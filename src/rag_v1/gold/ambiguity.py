"""Ambiguity that the corpus actually contains, not ambiguity invented to be hard.

``parsed`` is a field on ``ContentDeltaEvent`` and on ``ContentDoneEvent``, and it means
something different on each. A developer who asks "what does `parsed` contain?" has a
real question with two real answers, and answering it requires knowing which event type
is meant. That is worth testing.

An ambiguity case is only mined where the corpus itself supplies both readings: the same
field name defined under two different parent scopes, each with its own anchored span.
The question names the scope, because §11's contract is that if scope is needed to
answer, the evidence must establish it — a question that withholds the scope is a trick,
not a benchmark.
"""

from __future__ import annotations

import re

from rag_v1.gold.mining import code_regions, inside_code

#: ``-   `field`: Description.`` under a ``#### ParentType`` heading.
#: ``#### ContentDeltaEvent`` and ``#### `ContentDeltaEvent` `` are the same heading as
#: far as scope goes; requiring the bare form missed every doc that backticks its type
#: headings, which is most of the SDK reference pages.
_HEADING = re.compile(r"^#{2,5}\s+`?(?P<name>[A-Za-z_][\w.]{2,60})`?\s*$", re.MULTILINE)
_FIELD = re.compile(
    r"^[ \t]*[-*]\s+`(?P<name>[A-Za-z_][\w.]{1,40})`:\s+(?P<desc>[^\n]{15,220})$",
    re.MULTILINE)
MIN_INTERPRETATIONS = 2
#: Above this content-word overlap two "different" meanings are the same fact reworded.
#: "The title of the cited source" and "The title of the source page" are not an
#: ambiguity a developer could be confused by.
MAX_MEANING_OVERLAP = 0.6
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{2,}")


def _overlap(first: str, second: str) -> float:
    left = {w.lower() for w in _WORD.findall(first)}
    right = {w.lower() for w in _WORD.findall(second)}
    if not left or not right:
        return 1.0
    return len(left & right) / min(len(left), len(right))


def _meanings_differ(descriptions: list[str]) -> bool:
    return all(_overlap(a, b) <= MAX_MEANING_OVERLAP
               for i, a in enumerate(descriptions) for b in descriptions[i + 1:])


#: A scope is only a scope if it names a *type*. The first batch-004 run produced "In a
#: `FAQ`, what does `cache_read_input_tokens` contain, and how does that differ from
#: `Limitations`?" — the headings were prose sections of one page, so the two readings
#: were the same field described twice, and the question was unanswerable nonsense.
_SYMBOLIC_SCOPE = re.compile(r"^[A-Za-z_][\w.]{2,60}$")


def scope_is_symbolic(name: str) -> bool:
    """Does this heading name a type, rather than a section of prose?

    A type name announces itself: ``ContentDeltaEvent`` (internal capital),
    ``tool_result`` (underscore), ``agents.tool.ComputerTool`` (dotted). "FAQ",
    "Limitations" and "create" do not, and a field defined under two prose headings is a
    documentation repetition rather than a scoped meaning.
    """
    if not _SYMBOLIC_SCOPE.match(name):
        return False
    # "FAQ" and "HTTP" satisfy the internal-capital test by being all capitals. An
    # acronym heading is prose, not a type.
    if name.isupper():
        return False
    return "_" in name or "." in name or any(c.isupper() for c in name[1:])


def _scope_for(headings: list[tuple[int, str]], offset: int) -> tuple[int, str] | None:
    found = None
    for start, name in headings:
        if start < offset:
            found = (start, name)
        else:
            break
    return found


def find_ambiguous_fields(doc: dict, limit: int = 3) -> list[dict]:
    """Field names defined more than once, under different parent scopes."""
    text = doc["text"]
    fenced = code_regions(text)
    headings = [(m.start(), m.group("name")) for m in _HEADING.finditer(text)]

    by_name: dict[str, list[dict]] = {}
    for match in _FIELD.finditer(text):
        start, end = match.start(), match.end()
        if inside_code(fenced, start, end):
            continue
        scope = _scope_for(headings, start)
        if scope is None or not scope_is_symbolic(scope[1]):
            continue
        by_name.setdefault(match.group("name"), []).append({
            "scope": scope[1],
            "scope_offset": scope[0],
            "char_start": start,
            "char_end": end,
            "description": match.group("desc").strip(),
        })

    out: list[dict] = []
    for name, definitions in sorted(by_name.items()):
        if len(out) >= limit:
            break
        scopes = {d["scope"]: d for d in definitions}
        if len(scopes) < MIN_INTERPRETATIONS:
            continue
        # Two definitions that say the same thing are a repetition, not an ambiguity —
        # whether they are byte-identical or merely reworded.
        descriptions = [d["description"] for d in scopes.values()]
        if len(set(descriptions)) < MIN_INTERPRETATIONS:
            continue
        if not _meanings_differ(descriptions):
            continue
        out.append({
            "ambiguous_term": name,
            "candidate_interpretations": [
                {"scope": scope, "meaning": definition["description"],
                 "char_start": definition["char_start"],
                 "char_end": definition["char_end"]}
                for scope, definition in sorted(scopes.items())],
            "required_scope_to_answer": (
                f"Which parent type the `{name}` field belongs to. The corpus defines it "
                f"under {', '.join(sorted(scopes))} with different meanings, so the "
                "answer is undetermined until the scope is named."),
        })
    return out


__all__ = ["MAX_MEANING_OVERLAP", "MIN_INTERPRETATIONS", "find_ambiguous_fields",
           "scope_is_symbolic"]
