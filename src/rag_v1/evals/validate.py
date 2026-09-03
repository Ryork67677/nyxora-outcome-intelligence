from __future__ import annotations

from collections import Counter
from pathlib import Path

from rag_v1.evals.io import load_cases


def validate_golden(path: Path) -> dict:
    cases = load_cases(path)
    ids = [c.case_id for c in cases]
    dupes = [k for k, v in Counter(ids).items() if v > 1]
    if dupes:
        raise ValueError(f"Duplicate case_id values: {dupes}")
    for case in cases:
        if not case.expected_abstain and not case.expected_claims and not case.expected_evidence:
            raise ValueError(f"{case.case_id}: needs expected claims/evidence or expected_abstain=true")
    return {
        "cases": len(cases),
        "categories": dict(Counter(c.category for c in cases)),
        "abstain_cases": sum(1 for c in cases if c.expected_abstain),
    }
