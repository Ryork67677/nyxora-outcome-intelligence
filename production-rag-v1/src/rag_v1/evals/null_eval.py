from __future__ import annotations

import re
from pathlib import Path

from rag_v1.config import settings
from rag_v1.evals.io import load_cases, write_json
from rag_v1.generation import closed_book_answer


def _deterministic_claim_score(answer: str, claim) -> bool | None:
    candidates = [claim.text, *claim.alternatives]
    if claim.match_type == "human":
        return None
    if claim.match_type == "contains":
        ans = answer.casefold()
        return any(x.casefold() in ans for x in candidates)
    if claim.match_type == "exact":
        ans = " ".join(answer.casefold().split())
        return any(" ".join(x.casefold().split()) == ans for x in candidates)
    if claim.match_type == "regex":
        return any(re.search(x, answer, flags=re.IGNORECASE) is not None for x in candidates)
    return None


def run_null_eval(golden_path: Path, output_path: Path):
    """Run the closed-book control.

    A missing generation provider is recorded rather than raised. EXP-NULL is the
    control every later retrieval number is interpreted against, so "this control
    did not run, and here is exactly why" has to survive into the results file. An
    unrunnable control must never be silently downgraded into an absent file or,
    worse, into placeholder accuracy numbers that read like measurements.
    """
    cases = load_cases(golden_path)
    results = []
    blocked_reason: str | None = None

    for case in cases:
        if blocked_reason is None:
            try:
                generated = closed_book_answer(case.question)
            except Exception as exc:  # noqa: BLE001 - provider/credential/egress failures
                blocked_reason = f"{type(exc).__name__}: {exc}"
                generated = None
        else:
            generated = None

        if generated is None:
            results.append(
                {
                    "case_id": case.case_id,
                    "category": case.category,
                    "status": "not_run",
                    "answer": None,
                    "usage": {},
                    "claim_scores": [None for _ in case.expected_claims],
                    "deterministic_accuracy": None,
                    "needs_human_review": True,
                }
            )
            continue

        claim_scores = [_deterministic_claim_score(generated.text, c) for c in case.expected_claims]
        determinate = [x for x in claim_scores if x is not None]
        results.append(
            {
                "case_id": case.case_id,
                "category": case.category,
                "status": "answered",
                "answer": generated.text,
                "usage": generated.usage,
                "claim_scores": claim_scores,
                "deterministic_accuracy": (sum(determinate) / len(determinate)) if determinate else None,
                "needs_human_review": any(x is None for x in claim_scores) or case.expected_abstain,
            }
        )

    answered = [r for r in results if r["status"] == "answered"]
    scored = [r["deterministic_accuracy"] for r in answered if r["deterministic_accuracy"] is not None]
    payload = {
        "experiment": "EXP-NULL",
        "status": "blocked" if blocked_reason else "complete",
        "blocked_reason": blocked_reason,
        "generation_provider": settings.generation_provider,
        "generation_model": settings.generation_model,
        "cases_total": len(results),
        "cases_answered": len(answered),
        "macro_deterministic_accuracy": (sum(scored) / len(scored)) if scored else None,
        "cases": results,
    }
    write_json(output_path, payload)
    return payload
