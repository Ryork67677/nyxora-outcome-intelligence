"""Does the question ask the shape of thing the evidence actually says?

Two failures from batch 005, both of which a person caught and no machine did.

``GOLD-B005-08``'s evidence says manual extended thinking *is not supported on Claude
Sonnet 5*. The mined question was *"Where is ``budget_tokens`` supported?"* — a request
for a set of models, asked of a sentence that names one place it does not work. The
answer to the question is not in the evidence; the evidence answers a different
question.

``GOLD-B005-18``'s evidence says Undici-specific options *must be paired with* the
matching ``fetch`` implementation. The mined question was *"What must ``dispatcher``
be?"* — the copula truncated away the predicate, so the question asks for an identity
and the evidence gives a pairing requirement.

Both are the same mistake in different clothes: the question's *form* does not match the
evidence's *form*. This module tests for that directly, on the pair, rather than hoping
a category label catches it.
"""

from __future__ import annotations

import re

OK = "OK"
NEGATIVE_AS_POSITIVE = "NEGATIVE_AS_POSITIVE"
TRUNCATED_PREDICATE = "TRUNCATED_PREDICATE"

#: "Where is X supported?", "Which models support X?", "What supports X?" — a question
#: whose answer is a set of places something works.
_ASKS_FOR_COVERAGE = re.compile(
    r"^\s*(?:where\s+(?:is|are)\b.*\bsupported\b"
    r"|which\s+\w+s?\s+supports?\b"
    r"|what\s+supports?\b)",
    re.IGNORECASE)
#: "... is not supported on ...", "... is unsupported ...", "... does not support ..."
_STATES_NON_SUPPORT = re.compile(
    r"\b(?:is|are)\s+not\s+supported\b"
    r"|\bunsupported\b"
    r"|\bdoes\s+not\s+support\b"
    r"|\bno\s+longer\s+supported\b",
    re.IGNORECASE)
_STATES_SUPPORT = re.compile(
    r"\b(?<!not )supported\s+(?:on|in|by|for)\b|\bsupports\b", re.IGNORECASE)
#: "What must `X` be?" — a copula with nothing after it.
_BARE_COPULA = re.compile(
    r"^\s*what\s+must\s+(?:an?\s+|the\s+)?`?[^`?]+`?\s+be\s*\?\s*$", re.IGNORECASE)
#: The predicates a bare "must ... be?" swallows. Each needs its own preposition in the
#: question, because the preposition is the fact.
_PHRASAL_PREDICATE = re.compile(
    r"must\s+be\s+(?P<predicate>paired|combined|used|accompanied|matched|set|encoded|"
    r"passed|declared|escaped|prefixed|suffixed|wrapped)\s+"
    r"(?P<preposition>with|by|to|as|in|together with)\b",
    re.IGNORECASE)


def evaluate(question: str, evidence: str) -> dict:
    """Compare the question's form against the evidence's. ``OK`` means they match."""
    if _ASKS_FOR_COVERAGE.match(question) and _STATES_NON_SUPPORT.search(evidence):
        return {
            "status": NEGATIVE_AS_POSITIVE,
            "finding": (
                "the question asks where something is supported, and the evidence "
                "states where it is *not* — the evidence cannot answer a question about "
                "coverage, only about the one place it names"),
            "suggested_form": "Is <subject> supported on <the named place>?",
        }
    phrasal = _PHRASAL_PREDICATE.search(evidence)
    if phrasal and _BARE_COPULA.match(question):
        predicate = phrasal.group("predicate").lower()
        preposition = phrasal.group("preposition").lower()
        return {
            "status": TRUNCATED_PREDICATE,
            "finding": (
                f"the evidence says the subject must be {predicate} {preposition} "
                "something, and the question truncates that to \"must ... be?\" — which "
                "asks for an identity the evidence never gives"),
            "suggested_form": f"What must <subject> be {predicate} {preposition}?",
        }
    return {"status": OK, "finding": None, "suggested_form": None}


def asks_for_coverage(question: str) -> bool:
    return bool(_ASKS_FOR_COVERAGE.match(question))


def states_non_support(evidence: str) -> bool:
    return bool(_STATES_NON_SUPPORT.search(evidence))


def phrasal_predicate(evidence: str) -> tuple[str, str] | None:
    """The ``(predicate, preposition)`` a bare copula would swallow, if there is one."""
    match = _PHRASAL_PREDICATE.search(evidence)
    return (match.group("predicate").lower(),
            match.group("preposition").lower()) if match else None


__all__ = [
    "NEGATIVE_AS_POSITIVE",
    "OK",
    "TRUNCATED_PREDICATE",
    "asks_for_coverage",
    "evaluate",
    "phrasal_predicate",
    "states_non_support",
]
