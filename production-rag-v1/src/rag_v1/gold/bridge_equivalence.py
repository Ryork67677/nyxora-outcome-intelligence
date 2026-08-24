"""Does the same string mean the same thing in both spans?

Batch 004's composer required a bridge entity to appear in both spans, which is a string
test, and a string test cannot see equivocation. It paired these two:

    span 1: ``budget_tokens`` can exceed ``max_tokens`` here; the budget rules explain…
    span 2: The loop exits on any other stop reason (``"end_turn"``, ``"max_tokens"``, …)

``max_tokens`` in span 1 is a request parameter. ``"max_tokens"`` in span 2 is one of the
values ``stop_reason`` can take. They are different things that share a name, so there
was never an entity to chain through — and every other check passed the pair.

This module decides whether an entity plays the *same semantic role* in two spans. It is
deliberately coarse: it recognises a handful of roles a documented identifier can play
and refuses a pair whose roles differ, rather than trying to understand the sentence. A
coarse check that fires on the real failure is worth more than a subtle one that does
not, and a wrongly-refused pair costs a candidate while a wrongly-accepted one costs the
benchmark's credibility.

Namespace is checked alongside role. Two tools may each document a ``view_range``
parameter, and a chain through "``view_range``" that starts in the text editor tool and
ends in the memory tool is a chain through a coincidence.
"""

from __future__ import annotations

import re

#: The roles an identifier can play in a documentation sentence.
REQUEST_PARAMETER = "request_parameter"
ENUM_VALUE = "enum_value"
FIELD_NAME = "field_name"
CLASS_OR_TYPE = "class_or_type"
UNKNOWN = "unknown"

#: ``"max_tokens"`` — quoted inside the backticks, or backticked inside quotes. A string
#: literal in API documentation is a value, not the thing being configured.
_QUOTED = re.compile(r"""[`"']\s*["']([^"']+)["']\s*[`"']|["']([^"'`]+)["']""")
#: "one of", "such as", "the possible values are" — a list of literals.
_VALUE_CONTEXT = re.compile(
    r"\b(?:stop[_ ]reason|one of|any of|possible values?|allowed values?|"
    r"supported values?|such as|either|returns?|set to|equal to|value)\b",
    re.IGNORECASE)
#: "the `x` parameter", "pass `x`", "set `x`" — the thing being configured.
_PARAMETER_CONTEXT = re.compile(
    r"\b(?:parameter|argument|option|setting|flag|field|property|key|"
    r"pass(?:ing|es)?|set(?:ting|s)?|specify|provide|configure|include|omit|"
    r"defaults? to|requires?|accepts?)\b", re.IGNORECASE)
#: A dotted or CamelCase symbol is a type or a member of one.
_CLASS_LIKE = re.compile(r"^[A-Z][A-Za-z0-9]*(?:[A-Z][A-Za-z0-9]*)+$|^[a-z_]+(?:\.[a-z_]+)+$")
#: How much text either side of the occurrence counts as its context.
CONTEXT_WINDOW = 90
#: Words too common to distinguish one documentation area from another.
_NAMESPACE_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "of", "in", "on", "for", "with", "to", "api",
    "apis", "reference", "guide", "overview", "docs", "documentation", "tool",
    "tools", "use", "using", "usage", "response", "request", "parameters",
    "parameter", "options", "fields", "sdk",
})


def _occurrences(text: str, entity: str) -> list[int]:
    return [m.start() for m in re.finditer(re.escape(entity), text)]


def entity_role(text: str, entity: str) -> str:
    """How the span uses the entity: a parameter, a value, a field, or a type."""
    positions = _occurrences(text, entity)
    if not positions:
        return UNKNOWN

    for position in positions:
        window_start = max(0, position - CONTEXT_WINDOW)
        before = text[window_start:position]
        after = text[position + len(entity):position + len(entity) + CONTEXT_WINDOW]

        # A quoted literal is a value wherever it appears. Checked first because the
        # surrounding sentence often *also* looks like parameter prose.
        quoted = any(entity in (m.group(1) or m.group(2) or "")
                     for m in _QUOTED.finditer(text[window_start:position + len(entity) + 4]))
        if quoted:
            return ENUM_VALUE
        if _VALUE_CONTEXT.search(before[-40:]) and not _PARAMETER_CONTEXT.search(before[-40:]):
            return ENUM_VALUE
        if _CLASS_LIKE.match(entity):
            return CLASS_OR_TYPE
        if _PARAMETER_CONTEXT.search(before) or _PARAMETER_CONTEXT.search(after):
            return REQUEST_PARAMETER
        # "- `field`: description" is a field definition.
        if re.search(r"[-*]\s+`?" + re.escape(entity) + r"`?\s*:", text):
            return FIELD_NAME
        # A bare backticked identifier with no quoting and no defining colon is the
        # thing itself. Leaving it UNKNOWN made the ``max_tokens`` equivocation read as
        # "could not tell" when the point is that one span means the parameter.
        if re.search(r"`\s*" + re.escape(entity) + r"\s*`", text):
            return REQUEST_PARAMETER
    return UNKNOWN


def namespace(span: dict) -> set[str]:
    """The documentation area a span sits in, as a bag of significant words."""
    words = set()
    for part in [*(span.get("section_path") or []), span.get("document_title") or ""]:
        for word in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", str(part)):
            lowered = word.lower()
            if lowered not in _NAMESPACE_STOPWORDS:
                words.add(lowered)
    return words


def same_semantic_entity(entity: str, first: dict, second: dict) -> dict:
    """Decide whether a bridge entity means the same thing in both spans.

    Returns the §17 record: the roles found, whether they match, and why.
    """
    role_1 = entity_role(first["evidence_text"], entity)
    role_2 = entity_role(second["evidence_text"], entity)
    space_1, space_2 = namespace(first), namespace(second)
    shared = space_1 & space_2
    same_document = first.get("version_id") == second.get("version_id")

    reasons: list[str] = []
    if UNKNOWN in (role_1, role_2):
        reasons.append(
            f"the role of `{entity}` could not be read in "
            + ("span 1" if role_1 == UNKNOWN else "span 2")
            + " — an entity whose part of speech is unclear is not a safe bridge")
    elif role_1 != role_2:
        reasons.append(
            f"`{entity}` is a {role_1.replace('_', ' ')} in span 1 and "
            f"{'an' if role_2[0] in 'aeiou' else 'a'} {role_2.replace('_', ' ')} in "
            "span 2: the same string naming two different "
            "things, which is a coincidence rather than a chain")
    # Namespace is only decisive for the shape it was written for: two *definitions* of
    # a field with the same name, in different documents, with nothing in common. That
    # is `view_range` documented by both the text editor tool and the memory tool. It
    # must not fire on a legitimate cross-document chain — one span setting a value and
    # another stating what follows — which is what a genuine hop across two pages of one
    # SDK looks like, so for any other pair the shared namespace is advisory only.
    elif role_1 == role_2 == FIELD_NAME and not same_document:
        # Two *definitions* of a field in two documents are two parameters, whatever
        # heading words they happen to share — "view" and "commands" appear in both the
        # text editor tool and the memory tool, and neither defines the other's field.
        # A chain never runs between two definitions in any case: a definition
        # establishes no state for a second hop to consume.
        reasons.append(
            f"both spans merely define `{entity}`, in different documents "
            f"({sorted(space_1)[:3]} vs {sorted(space_2)[:3]}), so these are two "
            "parameters that share a name rather than one entity")

    return {
        "bridge_entity_text": entity,
        "bridge_entity_meaning_span_1": role_1,
        "bridge_entity_meaning_span_2": role_2,
        "same_semantic_entity": not reasons,
        "semantic_compatibility_check": "PASS" if not reasons else "FAIL",
        "bridge_equivalence_reason": (
            "; ".join(reasons) if reasons else
            f"`{entity}` is a {role_1.replace('_', ' ')} in both spans"
            + (", in the same document" if same_document
               else f", sharing the documentation area {sorted(shared)[:4]}" if shared
               else ", in different documents with no shared heading vocabulary — "
                    "worth a reviewer's attention, but the role matches")),
        "shared_namespace": sorted(shared),
        "same_document": same_document,
    }


__all__ = [
    "CLASS_OR_TYPE", "CONTEXT_WINDOW", "ENUM_VALUE", "FIELD_NAME", "REQUEST_PARAMETER",
    "UNKNOWN", "entity_role", "namespace", "same_semantic_entity",
]
