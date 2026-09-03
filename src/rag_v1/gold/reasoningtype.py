"""What kind of statement is this span? — batch 006 defect F.

The predicate lane takes its reasoning type from the frame of the first verb it matches.
A verb is a poor witness to what a sentence is about. "Claude Haiku 4.5 **accepts** the
`code_execution_20260120` … tool types, but … aren't available on it" matched ``accepts``
and was labelled ``exact_lookup``; it is a compatibility statement. The owner relabelled
three of nine exported candidates and the evidence was right in every case — the taxonomy
was not.

So classify from the **whole sentence**, in the order the preregistration fixes:

1. A span naming a support status, a version or a migration is a lifecycle case
   *whatever its verb*.
2. An error outcome — a rejection, a raise, a status code — is error behaviour.
3. ``configuration_interaction`` requires **two settings that bear on each other**, or a
   setting whose value changes a behaviour. One requirement that happens to mention two
   identifiers is not an interaction: that was ``GOLD-B006-01``, where a credential
   requirement naming `admin` and `developer` roles read as two settings interacting.
4. Otherwise the span states a value, and the question is a lookup.

Order is the whole design. Lifecycle first is not a tie-break; it is the preregistered
rule, because a compatibility sentence almost always also contains a lookup verb, and
reading it as a lookup is precisely how ``GOLD-B006-03`` was mislabelled.

This decides a *label*. It never moves an anchor, rewrites evidence, or changes what a
question asks — batch 006's relabelling left every anchor untouched and so does this.
"""

from __future__ import annotations

import re

EXACT_LOOKUP = "exact_lookup"
ERROR_BEHAVIOR = "error_behavior"
CONFIGURATION_INTERACTION = "configuration_interaction"
LIFECYCLE = "lifecycle_compatibility_migration"

#: Support status, migration and compatibility language. A span carrying any of these is
#: a lifecycle case whatever else it says. "available"/"supported" are matched only in
#: the negative, because "available on the Claude API" is a plain scope statement.
_LIFECYCLE_MARKERS = re.compile(
    r"\b(?:deprecat\w+|no\s+longer\s+(?:supported|available)|retired|sunset|"
    r"end[-\s]of[-\s]life|supersed\w+|migrat\w+|legacy|backward[s]?[-\s]compatib\w+|"
    r"compatibility|still\s+functional|replaced\s+by|removed\s+in|"
    r"(?:aren['’]?t|are\s+not|isn['’]?t|is\s+not|not)\s+(?:yet\s+)?(?:available|supported)|"
    r"unavailable|unsupported|newer\s+versions?|older\s+versions?|"
    r"upgrade\s+to|downgrade)\b",
    re.IGNORECASE)
#: A dated artifact version — ``code_execution_20260120``. A model name carrying a
#: number ("Claude Sonnet 5") is deliberately not this: naming a model is scope, not a
#: statement about versions, and treating it as lifecycle would relabel every span in
#: the corpus.
_DATED_VERSION = re.compile(r"\b\w+_20\d{6}\b")

#: An error outcome. A status code counts; so does an explicit rejection or raise.
_ERROR_MARKERS = re.compile(
    r"\b(?:rejects?|rejected|raises?|raised|throws?|thrown|fails?\s+with|failure|"
    r"errors?|exception|invalid|refus\w+|denied|[45]\d{2}\s*(?:error|status)?|"
    r"stop_reason)\b",
    re.IGNORECASE)

#: Verbs by which one setting bears on another, or on a behaviour.
_INTERACTION_VERBS = re.compile(
    r"\b(?:overrid\w+|disabl\w+|enabl\w+|ignor\w+|takes?\s+precedence|"
    r"conflicts?\s+with|suppress\w+|forces?|prevents?|turns?\s+(?:on|off)|"
    r"has\s+no\s+effect|is\s+ignored)\b",
    re.IGNORECASE)
#: A requirement. Present so it can be *excluded*: "X requires Y" states one rule, and
#: the identifiers in it are not settings acting on each other (``GOLD-B006-01``).
_REQUIREMENT = re.compile(r"\b(?:requires?|required|must\s+(?:be|have|provide))\b",
                          re.IGNORECASE)
_IDENTIFIER = re.compile(r"`[^`]+`|\b[A-Z][A-Z0-9]{2,}(?:_[A-Z0-9]+)+\b")


def _settings_in(text: str) -> int:
    """How many distinct identifiers the span names."""
    return len({m.group(0).strip("`").lower() for m in _IDENTIFIER.finditer(text)})


def classify(evidence_text: str) -> str:
    """The reasoning type this span states, read from the whole sentence."""
    text = evidence_text or ""

    if _LIFECYCLE_MARKERS.search(text) or _DATED_VERSION.search(text):
        return LIFECYCLE
    if _ERROR_MARKERS.search(text):
        return ERROR_BEHAVIOR
    # An interaction needs a verb by which one thing acts on another. An assignment
    # alone is not enough: "`thinking.display` defaults to `"omitted"` … ; set
    # `display: "summarized"` to receive readable summaries" states a default and then
    # tells you how to change it, and reading the trailing instruction as the fact is
    # how ``GOLD-B006-05`` came out as an interaction. The sentence's assertion is the
    # default, so a value statement stays a lookup.
    if _INTERACTION_VERBS.search(text):
        # A requirement naming two identifiers is not two settings interacting.
        if _REQUIREMENT.search(text) and _settings_in(text) < 2:
            return EXACT_LOOKUP
        return CONFIGURATION_INTERACTION
    return EXACT_LOOKUP


def evaluate(record: dict) -> dict:
    """Compare a record's recorded label to the one its evidence supports.

    ``agrees`` false is not an error — it is the finding. The generator's frame-derived
    label and the whole-sentence reading disagreed on three of batch 006's nine, and the
    owner sided with the sentence every time.
    """
    spans = record.get("expected_evidence") or []
    text = " ".join(s.get("evidence_text", "") for s in spans)
    derived = classify(text)
    recorded = record.get("reasoning_type")
    return {
        "candidate_id": record.get("candidate_id"),
        "recorded": recorded,
        "derived": derived,
        "agrees": recorded == derived,
    }


__all__ = [
    "CONFIGURATION_INTERACTION",
    "ERROR_BEHAVIOR",
    "EXACT_LOOKUP",
    "LIFECYCLE",
    "classify",
    "evaluate",
]
