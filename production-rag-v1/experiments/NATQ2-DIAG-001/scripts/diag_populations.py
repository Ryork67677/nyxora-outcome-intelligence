#!/usr/bin/env python3
"""NATQ2-DIAG-001 stage 1: build and freeze the four case populations.

Populations are hashed BEFORE any diagnostic inspection, so the sets cannot be adjusted
once the per-case detail is visible. Membership comes only from the two stored per-case
pass/fail vectors; nothing is recomputed and no system is run.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
H = REPO / "experiments/EVAL-NATQ2-H-002/EVAL-NATQ2-H-002-CASE-RESULTS.json"
B = REPO / "experiments/EVAL-NATQ-BM25-BASELINE-001/EVAL-NATQ-BM25-BASELINE-001-CASE-RESULTS.json"
OUT = REPO / "experiments/NATQ2-DIAG-001/NATQ2-DIAG-001-POPULATIONS.json"

PINNED = {
    H: "cc289dcbe10807330df8527d3f1313ce08a3c5e41e196e89a9239408ad0371ff",
    B: "061e475b5ed7df140919fd5ad60fb96d6ef31b0a64d39aac561fac31ee4a7054",
}
EXPECTED = {"H_RESCUES": 11, "H_REGRESSIONS": 3, "BOTH_HIT": 12, "BOTH_MISS": 14}
COORDINATOR_IDS = {
    "H_RESCUES": ["A23", "A24", "A28", "B25", "C11", "C29", "D19", "D23", "D29", "E17", "E22"],
    "H_REGRESSIONS": ["B09", "B28", "D27"],
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    for p, want in PINNED.items():
        if sha(p) != want:
            raise SystemExit(f"refusing to build populations: {p.name} hash changed")

    h = {c["case_id"]: c for c in json.loads(H.read_text())["cases"]}
    b = {c["case_id"]: c for c in json.loads(B.read_text())["cases"]}
    if set(h) != set(b):
        raise SystemExit("refusing: the two runs do not cover the same case set")

    pop = {"H_RESCUES": [], "H_REGRESSIONS": [], "BOTH_HIT": [], "BOTH_MISS": []}
    for cid in sorted(h):
        hh, bb = h[cid]["hit_at_10"], b[cid]["hit_at_10"]
        pop[("BOTH_HIT" if bb else "H_RESCUES") if hh else ("H_REGRESSIONS" if bb else "BOTH_MISS")].append(cid)

    counts = {k: len(v) for k, v in pop.items()}
    if counts != EXPECTED:
        raise SystemExit(f"refusing: population counts {counts} != coordinator's {EXPECTED}")
    for k, ids in COORDINATOR_IDS.items():
        if pop[k] != sorted(ids):
            raise SystemExit(f"refusing: {k} membership differs from the coordinator's list\n"
                             f"  derived {pop[k]}\n  given   {sorted(ids)}")
    if sum(counts.values()) != 40:
        raise SystemExit("refusing: populations do not partition the 40 cases")

    payload = {
        "record_id": "NATQ2-DIAG-001-POPULATIONS",
        "derived_from": {str(p.relative_to(REPO)): v for p, v in PINNED.items()},
        "systems_run": 0, "retrieval_performed": False, "ce_inference_performed": False,
        "partition_is_exact": True, "total": 40,
        "counts": counts,
        "matches_coordinator_expected_counts": True,
        "matches_coordinator_named_ids": True,
        "populations": pop,
        "definitions": {
            "H_RESCUES": "SYSTEM-H hit@10 true, BM25 hit@10 false",
            "H_REGRESSIONS": "SYSTEM-H hit@10 false, BM25 hit@10 true",
            "BOTH_HIT": "both hit@10 true",
            "BOTH_MISS": "both hit@10 false"},
    }
    OUT.write_text(json.dumps(payload, indent=1) + "\n")
    for k, v in pop.items():
        print(f"{k:<16} {len(v):>2}  {' '.join(v)}")
    print(f"\npopulations sha256 {sha(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
