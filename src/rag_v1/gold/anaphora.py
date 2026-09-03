"""Is an unresolved reference in the evidence actually load-bearing?

``anaphora_problem`` answers a narrow question: does this span contain a reference it
cannot resolve? That is the right check for an anchor, and it is deliberately
conservative — it has flagged "The error category", "These minimums" and "the tool
definition", none of which are anaphors in the sense that matters.

Being conservative is only safe if the conservative answer stays visible. So findings are
never erased; they are classified:

``CRITICAL``
    Resolving the reference changes the subject, the condition, the answer or a claim.
    The case cannot be scored without it. Blocking, always.

``NONCRITICAL``
    The phrase sits inside otherwise self-contained evidence and nothing being scored
    depends on which thing it refers to. A warning — and still blocking until a person
    says otherwise, because a machine deciding its own findings are unimportant is how
    a gate stops meaning anything.

The test is mechanical: a span that *opens* on a reference is always critical, because
the sentence's subject or condition is the missing part. Otherwise the reference's head
noun is looked for in the question, the answer, the claims and the critical strings —
the text that is actually scored. If the scored text never mentions it, resolving it
cannot change the score.
"""

from __future__ import annotations

import re

from rag_v1.gold.mining import _ANAPHORIC_OPENER, _REFERRING, anaphora_problem

CRITICAL = "CRITICAL_ANAPHORA"
NONCRITICAL = "NONCRITICAL_ANAPHORA"
NONE = "NO_ANAPHORA"


def scored_text(candidate: dict) -> str:
    """Everything a score depends on: the question, answer, claims, critical strings."""
    parts = [
        candidate.get("proposed_question", ""),
        candidate.get("proposed_answer", ""),
        *candidate.get("proposed_atomic_claims", []),
        *candidate.get("critical_strings", []),
    ]
    return " \n".join(str(p) for p in parts)


def classify(span: str, candidate: dict) -> dict:
    """Classify the span's anaphora finding against what the candidate actually scores."""
    problem = anaphora_problem(span)
    if problem is None:
        return {"status": NONE, "finding": None, "phrase": None, "blocking": False}

    stripped = span.lstrip()
    if _ANAPHORIC_OPENER.match(stripped):
        return {
            "status": CRITICAL, "finding": problem,
            "phrase": stripped[:40],
            "blocking": True,
            "why": ("The span opens on the reference, so the sentence's own subject or "
                    "condition is the part that is missing."),
        }

    scored = scored_text(candidate).lower()
    for match in _REFERRING.finditer(span):
        noun = match.group(2).lower()
        earlier = span[:match.start()].lower()
        if noun in earlier or noun.rstrip("s") in earlier:
            continue
        depends = bool(re.search(rf"\b{re.escape(noun)}s?\b", scored))
        return {
            "status": CRITICAL if depends else NONCRITICAL,
            "finding": problem,
            "phrase": match.group(0),
            "blocking": depends,
            "why": (
                f"The scored question, answer, claims or critical strings mention "
                f"{noun!r}, so which one is meant changes the answer."
                if depends else
                f"Nothing scored mentions {noun!r}: the question, answer, claims and "
                "critical strings are all satisfied without resolving it."
            ),
        }
    return {"status": NONE, "finding": problem, "phrase": None, "blocking": False}


def evaluate_span(span: str, candidate: dict) -> dict:
    """Classify, then apply any recorded human override.

    An override never deletes the finding and never makes a critical one harmless. It
    records that a person looked at a noncritical finding and accepted it.
    """
    verdict = classify(span, candidate)
    override = candidate.get("human_anaphora_override")
    reviewer = candidate.get("override_reviewer")
    verdict["human_anaphora_override"] = bool(override)
    verdict["override_reviewer"] = reviewer

    if not override:
        # Until a person accepts it, even a noncritical finding blocks: a generator
        # deciding its own findings do not matter is not a gate.
        verdict["blocking"] = verdict["status"] in (CRITICAL, NONCRITICAL)
        return verdict
    if verdict["status"] == CRITICAL:
        verdict["override_refused"] = (
            "A critical anaphora cannot be overridden: the scored text depends on the "
            "reference, so accepting it would score a case nobody can check."
        )
        verdict["blocking"] = True
        return verdict
    if not reviewer or reviewer.strip().lower() in {"claude", "chatgpt", "gpt", "model"}:
        verdict["override_refused"] = (
            "An override must name a human reviewer; a model cannot accept its own "
            "finding."
        )
        verdict["blocking"] = True
        return verdict
    verdict["blocking"] = False
    return verdict


__all__ = ["CRITICAL", "NONCRITICAL", "NONE", "classify", "evaluate_span", "scored_text"]
