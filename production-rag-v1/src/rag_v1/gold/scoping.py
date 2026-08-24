"""Does a span say what its fact is about, without leaning on anything outside itself?

A documentation bullet like ``- `invalid_tool_input`: Invalid tool input`` is a complete
sentence and a useless piece of evidence. The field name is not unique — three tools in
this corpus define an ``invalid_tool_input`` — and what makes the bullet mean something
is the heading above it, which the span does not contain. A claim anchored there is
checkable against text that does not actually determine it.

Batch 005 shipped one of these as ``GOLD-B005-01``, and it got through because the rule
that catches the shape only looked at records with exactly one span. That record had
two, one from each of the two tools whose meanings it was supposedly distinguishing, and
neither named its owner. The fix is the obvious one and it is the whole point of this
module: **the question is asked of every span, independently.** A record is only as
scoped as its least scoped span.

Section paths and document titles are deliberately not consulted. They are metadata the
parser produced, not evidence a reader can check — and batch 005's own heading audit is
the reason to distrust them.
"""

from __future__ import annotations

import re

#: ``- `field`: description`` or ``* `field`: description``. The shape a reference table
#: renders as a row and a reader reads as "this field, of whatever this section is about".
_DEFINITION_BULLET = re.compile(r"^\s*[-*+]\s+`(?P<field>[^`]+)`\s*:\s*(?P<body>.*)$")
#: The same shape without backticks, which some pages use.
_PLAIN_BULLET = re.compile(r"^\s*[-*+]\s+(?P<field>[A-Za-z_][\w.]*)\s*:\s+(?P<body>.+)$")
#: A name that reads as a type, component, event or tool rather than as a field: two or
#: more capitalised words run together, or a dotted path, or a conventional suffix.
_OWNER_SHAPED = re.compile(
    r"^(?:[A-Z][a-z0-9]+){2,}$"
    r"|^[a-z][\w]*(?:\.[a-z][\w]*)+$"
    r"|(?:Event|Tool|Error|Exception|Response|Request|Object|Param|Params|Message|"
    r"Item|Delta|Client|Session|Runner|Model|Provider|Handler|Config)$")
#: Words that look like an owner but name the document's furniture, not a component.
_NOT_AN_OWNER = frozenset({
    "note", "warning", "example", "examples", "parameters", "fields", "properties",
    "response", "request", "returns", "arguments", "options", "see", "usage",
})

SCOPED = "SCOPED"
NEEDS_SCOPE = "NEEDS_SCOPE"


def _lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip()]


def definition_bullets(text: str) -> list[str]:
    """The field names this span defines as bullets, in order."""
    fields = []
    for line in _lines(text):
        match = _DEFINITION_BULLET.match(line) or _PLAIN_BULLET.match(line)
        if match:
            fields.append(match.group("field"))
    return fields


def is_only_definition_bullets(text: str) -> bool:
    """Is every non-empty line in this span a bare definition bullet?

    A span mixing a bullet with a sentence about what owns it is not this shape — the
    sentence is where the scope can live.
    """
    lines = _lines(text)
    if not lines:
        return False
    return all(_DEFINITION_BULLET.match(line) or _PLAIN_BULLET.match(line)
               for line in lines)


def owner_candidates(text: str, defined: set[str] | None = None) -> list[str]:
    """Names in this span that could identify what the defined fields belong to.

    A field name the span itself defines cannot be its own owner, so those are excluded:
    that is exactly the circularity that makes a bare bullet unscoped.
    """
    defined = {d.lower() for d in (defined or ())}
    seen: list[str] = []
    for token in re.findall(r"`([^`]+)`|\b([A-Za-z_][\w.]*)\b", text):
        name = (token[0] or token[1]).strip()
        # A call or subscript still names the thing it calls.
        name = re.sub(r"[(\[].*$", "", name).strip(" .,:;")
        if not name or name.lower() in defined or name.lower() in _NOT_AN_OWNER:
            continue
        if _OWNER_SHAPED.search(name) and name not in seen:
            seen.append(name)
    return seen


def evaluate_span(text: str) -> dict:
    """Can this span, alone, tell a reader what its fact is about?"""
    fields = definition_bullets(text)
    if not fields or not is_only_definition_bullets(text):
        return {"status": SCOPED, "definition_fields": fields, "owner": None,
                "finding": None}
    owners = owner_candidates(text, set(fields))
    if owners:
        return {"status": SCOPED, "definition_fields": fields, "owner": owners[0],
                "finding": None}
    return {
        "status": NEEDS_SCOPE,
        "definition_fields": fields,
        "owner": None,
        "finding": (
            "bare definition bullet"
            + ("s" if len(fields) > 1 else "")
            + " — the span defines "
            + ", ".join(f"`{f}`" for f in fields)
            + " without naming the object, component, event or tool that owns "
            + ("them" if len(fields) > 1 else "it")
            + "; the scope is in the heading, which is not evidence"),
    }


def evaluate(record: dict) -> dict:
    """Apply the span rule to every span of a record and report the worst case.

    ``spans`` in the returned dict is one verdict per span, in order, so a repair can be
    aimed at the span that needs it rather than at the record as a whole.
    """
    spans = record.get("expected_evidence") or []
    verdicts = [evaluate_span(span["evidence_text"]) for span in spans]
    unscoped = [(span["evidence_id"], verdict)
                for span, verdict in zip(spans, verdicts, strict=True)
                if verdict["status"] == NEEDS_SCOPE]
    return {
        "status": NEEDS_SCOPE if unscoped else SCOPED,
        "spans": [{"evidence_id": span["evidence_id"], **verdict}
                  for span, verdict in zip(spans, verdicts, strict=True)],
        "unscoped_spans": [evidence_id for evidence_id, _ in unscoped],
        "findings": [f"{evidence_id}: {verdict['finding']}"
                     for evidence_id, verdict in unscoped],
    }


__all__ = [
    "NEEDS_SCOPE",
    "SCOPED",
    "definition_bullets",
    "evaluate",
    "evaluate_span",
    "is_only_definition_bullets",
    "owner_candidates",
]
