"""Batch-005 miners: interactions, constraints, lifecycle, and cross-document scope.

Batch 004's coverage came almost entirely from one shape — a sentence carrying its own
condition and outcome — and its review then had to relabel two of those as
``error_behavior`` because a single conditional fact is not an interaction between
settings. These miners separate the shapes at generation instead, so a label is earned
by what the sentence says rather than corrected afterwards:

* **interactions** name two settings and state how one bears on the other. Requiring two
  identifiers is what makes ``configuration_interaction`` mean something;
* **constraints** state a hard limit or a required format — an exact lookup that a
  developer would actually hit;
* **lifecycle** states a support status: deprecated, removed, migrated;
* **cross-document scope** finds a field defined in two components with different
  meanings, which is the ambiguity §12 asks for and the one the single-document miner
  cannot see.

Every miner walks ``factmining.iter_guarded_spans``, so the evidence guards — fenced
code, code-shaped prose, anaphora resolution, fragment rejection, size caps — are the
same ones batches 003 and 004 used, and cannot drift per miner.
"""

from __future__ import annotations

import re
from collections import defaultdict

from rag_v1.gold.factmining import iter_guarded_spans, package_fact
from rag_v1.gold.normalisation import contains_claim_string

#: A relation between two named settings. Each pattern has to match a sentence that
#: mentions *both* sides, which is checked separately — the verb alone is not enough.
INTERACTION_PATTERNS = (
    (re.compile(r"\btakes precedence over\b", re.IGNORECASE), "takes_precedence"),
    (re.compile(r"\bis ignored (?:when|if|unless)\b", re.IGNORECASE), "ignored_under_condition"),
    (re.compile(r"\b(?:disables?|prevents?|suppresses?)\b", re.IGNORECASE), "disables"),
    (re.compile(r"\brequires?\b", re.IGNORECASE), "requires"),
    (re.compile(r"\boverrides?\b", re.IGNORECASE), "overrides"),
    (re.compile(r"\bcannot be (?:used|combined|set) (?:with|together)\b", re.IGNORECASE),
     "mutually_exclusive"),
    (re.compile(r"\bonly (?:applies|works|available) (?:when|if|with)\b", re.IGNORECASE),
     "conditional_availability"),
    # "when X is present" matched sentences whose subject was somewhere else entirely
    # — "How does `memory_stores` change behaviour when it is present?" answered with a
    # field definition. The relation is real but this pattern cannot find its subject,
    # so it is not mined rather than mined badly.

    (re.compile(r"\bfalls? back to\b", re.IGNORECASE), "fallback"),
    (re.compile(r"\bchanges? (?:the )?(?:behaviou?r|meaning|semantics) of\b", re.IGNORECASE),
     "changes_behaviour"),
)
#: A hard limit or a required format — the exact lookups §14 says must earn their place.
CONSTRAINT_PATTERNS = (
    (re.compile(r"\bmust be\b", re.IGNORECASE), "required_value"),
    (re.compile(r"\bmust (?:not|never)\b", re.IGNORECASE), "prohibited"),
    (re.compile(r"\bmaximum (?:of |is |allowed )?\b", re.IGNORECASE), "maximum"),
    (re.compile(r"\bcannot exceed\b", re.IGNORECASE), "maximum"),
    (re.compile(r"\bis limited to\b", re.IGNORECASE), "maximum"),
    (re.compile(r"\bup to \d", re.IGNORECASE), "maximum"),
    (re.compile(r"\bat (?:most|least) \d", re.IGNORECASE), "bound"),
    (re.compile(r"\bmust (?:match|conform|start with|end with|contain)\b", re.IGNORECASE),
     "required_format"),
)
#: §13's vocabulary. "version_conflict" is deliberately absent: the corpus has no
#: superseded-version chains, so nothing here can be one.
LIFECYCLE_PATTERNS = (
    (re.compile(r"\bis deprecated\b", re.IGNORECASE), "deprecation"),
    (re.compile(r"\bare deprecated\b", re.IGNORECASE), "deprecation"),
    (re.compile(r"\bno longer (?:supported|available|returned|accepted)\b", re.IGNORECASE),
     "deprecation"),
    (re.compile(r"\b(?:has been|was|is) removed\b", re.IGNORECASE), "removal"),
    (re.compile(r"\bmigrat(?:e|ing|ion)\b", re.IGNORECASE), "migration"),
    (re.compile(r"\bsupersed(?:es|ed)\b", re.IGNORECASE), "migration"),
    (re.compile(r"\breplaced by\b", re.IGNORECASE), "migration"),
    (re.compile(r"\bstill (?:functional|supported|works)\b", re.IGNORECASE), "compatibility"),
    (re.compile(r"\bnot supported (?:on|for|in)\b", re.IGNORECASE), "compatibility"),
)
#: ``-   `field`: Description.`` — the definition bullets the scope miner pairs.
_FIELD = re.compile(
    r"^[ \t]*[-*]\s+`(?P<name>[A-Za-z_][\w.]{2,40})`:\s+(?P<desc>[^\n]{20,220})$",
    re.MULTILINE)
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{2,}")
#: Two descriptions this similar are the same fact written twice, not two meanings.
MAX_MEANING_OVERLAP = 0.5
#: Below this a "difference" is two unrelated sentences that happen to share a field
#: name, which is a naming collision rather than an ambiguity a developer would hit.
MIN_MEANING_OVERLAP = 0.15
#: How many identifiers a sentence may name before it is a list rather than a relation.
MAX_IDENTIFIERS_IN_INTERACTION = 5


#: A sentence that points somewhere else states nothing. "See [X]. To override…" is a
#: navigation aid, and a question built on it tests whether the reader can follow a link.
_NAVIGATIONAL = re.compile(r"^\s*(?:see|for (?:more|details|the full)|learn more|refer to|"
                           r"read (?:more|the))\b", re.IGNORECASE)
#: A lead-in to a list leaves its content outside the span.
_LIST_LEAD_IN = re.compile(r":\s*$|\n\s*[-*]\s")
#: A markdown table row is not a sentence. Its cells depend on a header outside the
#: span, which is exactly what rule 2D forbids relying on.
_TABLE_ROW = re.compile(r"\|\s*\S.*\|")
#: "…tool_reference blocks (up to 5 by default). 6." — a stranded ordinal means the
#: sentence splitter cut through a numbered list.
_STRANDED_ORDINAL = re.compile(r"(?:^|\s)\d{1,2}\.\s*$|^\s*\d{1,2}\.\s")
#: A literal is a value, not a thing that requires, overrides or disables anything.
#: "What does `None` turn off?" asks a question about a keyword.
_LITERAL_SUBJECT = re.compile(r"^(?:True|False|None|null|nil|\d[\w.]*|-\d.*)$",
                              re.IGNORECASE)
#: An error code is what you get, not a thing with a limit or a required value.
_ERROR_CODE = re.compile(r"error|_too_large|not_found|denied|invalid_|unauthorized|"
                         r"exceeded|forbidden", re.IGNORECASE)
#: Generic words that name a hundred different things across two SDKs. A field called
#: `url` in two documents is a naming collision, not an ambiguity worth testing.
_GENERIC_FIELD_NAMES = frozenset({
    "url", "urls", "headers", "header", "name", "names", "id", "ids", "type", "types",
    "value", "values", "data", "content", "text", "path", "paths", "key", "keys",
    "status", "state", "result", "results", "error", "errors", "message", "messages",
    "input", "output", "config", "options", "params", "args", "kwargs", "context",
    "metadata", "timeout", "model", "role", "size", "count", "index", "items",
})


def _usable(span: str) -> bool:
    """Guards shared by every v5 miner beyond the evidence-level ones."""
    return not (_NAVIGATIONAL.match(span) or _LIST_LEAD_IN.search(span)
                or _TABLE_ROW.search(span) or _STRANDED_ORDINAL.search(span))


#: How far the subject may sit from the verb it governs. Beyond this the identifier is
#: somewhere else in the sentence and the question would put words in its mouth.
SUBJECT_GAP = 16


def subject_identifier(span: str, patterns, identifiers: list[str]) -> str | None:
    """The identifier the matched statement is *about*.

    Taking the first identifier in the span produced questions like "What is the
    documented limit on `request_too_large`?" — the limit is on the request, and
    `request_too_large` is the error you get for exceeding it. The subject has to be the
    identifier immediately governing the verb that matched, or there is no honest
    question to ask.
    """
    for pattern, _ in patterns:
        match = pattern.search(span)
        if match is None:
            continue
        before = span[:match.start()]
        best = None
        for identifier in identifiers:
            for occurrence in re.finditer(re.escape(identifier), before):
                gap = before[occurrence.end():]
                if len(gap) > SUBJECT_GAP or "," in gap or ";" in gap:
                    continue
                best = identifier
        if best is not None:
            return best
    return None


def _overlap(first: str, second: str) -> float:
    left = {w.lower() for w in _WORD.findall(first)}
    right = {w.lower() for w in _WORD.findall(second)}
    if not left or not right:
        return 1.0
    return len(left & right) / min(len(left), len(right))


def _matched(patterns, sentence: str):
    for pattern, label in patterns:
        if pattern.search(sentence):
            return label
    return None


def mine_interactions(doc: dict, limit: int = 40) -> list[dict]:
    """Sentences where one named setting bears on another named setting.

    The two-identifier requirement is the whole point. "If a tool requires approval,
    the stream finishes" is one conditional fact about one thing; "``structuredContent``
    takes precedence over these content blocks" names both sides of a relation. Batch
    004 shipped the first shape as ``configuration_interaction`` twice and the review
    had to relabel both.
    """
    out: list[dict] = []
    for start, end, span, identifiers in iter_guarded_spans(
            doc, lambda s: _matched(INTERACTION_PATTERNS, s) is not None, limit):
        if not _usable(span):
            continue
        relation = _matched(INTERACTION_PATTERNS, span)
        present = [i for i in identifiers if contains_claim_string(span, i)]
        if not (2 <= len(present) <= MAX_IDENTIFIERS_IN_INTERACTION):
            continue
        subject = subject_identifier(span, INTERACTION_PATTERNS, present)
        if subject is None or _LITERAL_SUBJECT.match(subject):
            continue
        present = [subject] + [i for i in present if i != subject]
        fact = package_fact(doc, start, end, span, present[:3], "interaction",
                            "configuration_interaction")
        fact["interaction_relation"] = relation
        fact["interacting_identifiers"] = present[:3]
        out.append(fact)
    return out


def mine_constraints(doc: dict, limit: int = 40) -> list[dict]:
    """Hard limits and required formats."""
    out: list[dict] = []
    for start, end, span, identifiers in iter_guarded_spans(
            doc, lambda s: _matched(CONSTRAINT_PATTERNS, s) is not None, limit):
        if not _usable(span):
            continue
        kind = _matched(CONSTRAINT_PATTERNS, span)
        present = [i for i in identifiers if contains_claim_string(span, i)]
        subject = subject_identifier(span, CONSTRAINT_PATTERNS, present)
        if subject is None or _ERROR_CODE.search(subject) or _LITERAL_SUBJECT.match(subject):
            continue
        present = [subject] + [i for i in present if i != subject]
        # A limit is only worth asking about when the span says what the limit *is*.
        if kind in ("maximum", "bound") and not re.search(r"\d", span):
            continue
        fact = package_fact(doc, start, end, span, present[:3], "constraint",
                            "constraint_statement")
        fact["constraint_kind"] = kind
        out.append(fact)
    return out


#: "`compaction_control` parameter is deprecated" — the thing being deprecated has to be
#: the grammatical subject. "a null `current_seat_tier` means the seat was removed"
#: matches "removed" and is about a seat assignment, not a lifecycle.
_DEPRECATION_SUBJECT = re.compile(
    r"`[^`]{2,60}`(?:\s+\w+){0,2}\s+(?:is|are|has been|have been|was|were|will be)\s+"
    r"(?:deprecated|removed|retired|superseded|replaced|no longer)", re.IGNORECASE)
#: Migration and compatibility sentences are phrased too variously for a subject rule,
#: so they keep the weaker requirement: some named artefact in the sentence.
_NAMED_ARTEFACT = re.compile(
    r"`[^`]{2,60}`|\b(?:Claude|GPT|Opus|Sonnet|Haiku)\b", re.IGNORECASE)


def _lifecycle_subject(span: str, kind: str) -> bool:
    """Is the support statement about a named artefact, as its subject?"""
    if kind in ("deprecation", "removal"):
        return bool(_DEPRECATION_SUBJECT.search(span))
    return bool(_NAMED_ARTEFACT.search(span))


def mine_lifecycle(doc: dict, limit: int = 30) -> list[dict]:
    """Support status: deprecated, removed, migrated, still-compatible."""
    out: list[dict] = []
    for start, end, span, identifiers in iter_guarded_spans(
            doc, lambda s: _matched(LIFECYCLE_PATTERNS, s) is not None, limit):
        if not _usable(span):
            continue
        kind = _matched(LIFECYCLE_PATTERNS, span)
        present = [i for i in identifiers if contains_claim_string(span, i)]
        if not present:
            continue
        # The lifecycle verb has to be about a named thing. "the seat was removed"
        # matches "removed" and is not a deprecation; batch 003 learned the same lesson
        # about its own lifecycle pattern.
        if not _lifecycle_subject(span, kind):
            continue
        subject = subject_identifier(span, LIFECYCLE_PATTERNS, present)
        if subject is None:
            continue
        present = [subject] + [i for i in present if i != subject]
        fact = package_fact(doc, start, end, span, present[:3], "lifecycle",
                            "lifecycle_statement")
        fact["lifecycle_kind"] = kind
        out.append(fact)
    return out


def field_definitions(doc: dict) -> dict[str, list[dict]]:
    """Every ``- `field`: description`` bullet in a document, by field name."""
    text = doc["text"]
    found: dict[str, list[dict]] = defaultdict(list)
    for match in _FIELD.finditer(text):
        found[match.group("name")].append({
            "name": match.group("name"),
            "description": match.group("desc").strip(),
            "char_start": match.start(),
            "char_end": match.end(),
            "version_id": doc["version_id"],
            "document_title": doc["title"],
            "provider": doc["provider"],
            "source_url": doc.get("url"),
            "captured_at": str(doc.get("captured_at")),
            "doc": doc,
        })
    return found


def find_cross_component_ambiguity(docs: list[dict], limit: int = 12) -> list[dict]:
    """The same field name meaning different things in two different components.

    §12's second shape. The single-document miner can only see a field defined twice
    under two headings of one page; this sees ``input_filter`` in the Agents SDK and
    ``input_filter`` somewhere else entirely, which is the confusion a developer
    searching by field name actually walks into.

    Two definitions must differ enough to be two meanings and overlap enough to be about
    the same kind of thing — a field name shared by genuinely unrelated subsystems is a
    naming collision, and asking which one is meant tests nothing.
    """
    by_name: dict[str, list[dict]] = defaultdict(list)
    for doc in docs:
        for name, definitions in field_definitions(doc).items():
            # One definition per document: a field defined twice on one page is the
            # single-document ambiguity case, handled elsewhere.
            if len(definitions) == 1:
                by_name[name].append(definitions[0])

    out: list[dict] = []
    for name, definitions in sorted(by_name.items()):
        if len(out) >= limit or len(definitions) < 2:
            continue
        if name.lower() in _GENERIC_FIELD_NAMES:
            continue
        for index, first in enumerate(definitions):
            for second in definitions[index + 1:]:
                if first["version_id"] == second["version_id"]:
                    continue
                overlap = _overlap(first["description"], second["description"])
                if not (MIN_MEANING_OVERLAP <= overlap <= MAX_MEANING_OVERLAP):
                    continue
                # Length and distinct content, not just a different overlap score.
                # "Report how much audio the user has actually heard" and "Report actual
                # playback progress" score as different and say the same thing.
                if min(len(first["description"]), len(second["description"])) < 40:
                    continue
                left = {w.lower() for w in _WORD.findall(first["description"])}
                right = {w.lower() for w in _WORD.findall(second["description"])}
                if min(len(left - right), len(right - left)) < 3:
                    continue
                out.append({
                    "ambiguous_term": name,
                    "readings": [first, second],
                    "meaning_overlap": round(overlap, 3),
                })
                break
            else:
                continue
            break
    return out


__all__ = [
    "CONSTRAINT_PATTERNS", "INTERACTION_PATTERNS", "LIFECYCLE_PATTERNS",
    "MAX_MEANING_OVERLAP", "MIN_MEANING_OVERLAP", "field_definitions",
    "find_cross_component_ambiguity", "mine_constraints", "mine_interactions",
    "mine_lifecycle",
]
