#!/usr/bin/env python3
"""Reproduce the frozen BM25 comparator from its STORED ranked output, offline.

This is metric recomputation, not retrieval. Nothing queries the database and nothing
touches src/rag_v1/retrieval.py; the only input is the 400-row ranked-output log the
comparator already wrote, pinned by hash. If this fails to reproduce 0.375 and 0.1425
and the stored per-case vector exactly, the shared scorer is wrong and SYSTEM-H must not
be scored with it.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from natq2_scorer import DEPTH, aggregate, per_slice, score_case  # noqa: E402

BM = REPO / "experiments/EVAL-NATQ-BM25-BASELINE-001"
SPLIT = REPO / "evals/splits/natq-002"
OUT = REPO / "experiments/EVAL-NATQ2-H-002/EVAL-NATQ2-H-002-SCORER-VERIFICATION.json"

PINNED = {
    BM / "logs/bm25-ranked-output.jsonl": "1eb9ffe15e3974f195da6a3145da8f8952a203658e9ed11ec1d2ad678a61ba6a",
    BM / "EVAL-NATQ-BM25-BASELINE-001-RESULTS.json": "e2e7d70dcf42fa31edfc8690ddb26f15fd5dc67ed5a612c662480db0456b831b",
    BM / "EVAL-NATQ-BM25-BASELINE-001-CASE-RESULTS.json": "061e475b5ed7df140919fd5ad60fb96d6ef31b0a64d39aac561fac31ee4a7054",
    SPLIT / "validation.json": "6b7f3c90e2bfa58f244de6b2aff65e56ca3f50e2ed0886e83696aba8f5b47961",
}
EXPECT = {"case_hit_at_10": 0.375, "micro_MRR": 0.1425,
          "case_full_coverage_at_10": 0.325, "span_recall_at_10": 0.3333,
          "case_hit_at_1": 0.1}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    for p, want in PINNED.items():
        got = sha(p)
        if got != want:
            raise SystemExit(f"refusing to verify: {p.name} hash changed\n  got  {got}\n  want {want}")
    log = SPLIT / "reserve-access.log.jsonl"
    if log.stat().st_size != 0:
        raise SystemExit("refusing to verify: the reserve access log is not empty")

    val = json.loads((SPLIT / "validation.json").read_text())
    cases = val["cases"]
    rows = [json.loads(x) for x in
            (BM / "logs/bm25-ranked-output.jsonl").read_text().splitlines() if x.strip()]

    hits: dict[str, list[dict]] = {}
    for r in rows:
        hits.setdefault(r["case_id"], []).append(r)
    for cid in hits:
        hits[cid].sort(key=lambda h: h["rank"])

    per_case = [score_case(c, hits.get(c["case_id"], []), DEPTH) for c in cases]
    metrics = aggregate(per_case)

    stored_run = json.loads((BM / "EVAL-NATQ-BM25-BASELINE-001-RESULTS.json").read_text())
    stored_cases = json.loads((BM / "EVAL-NATQ-BM25-BASELINE-001-CASE-RESULTS.json").read_text())
    stored_vec = stored_cases["case_level_pass_fail_vector"]
    stored_metrics = stored_run["metrics"]

    metric_checks = [{"metric": k, "recomputed": metrics[k], "expected": v, "match": metrics[k] == v}
                     for k, v in EXPECT.items()]
    stored_checks = [{"metric": k, "recomputed": metrics[k], "stored": stored_metrics[k],
                      "match": metrics[k] == stored_metrics[k]}
                     for k in EXPECT if k in stored_metrics]

    ours = {c["case_id"]: c["hit_at_10"] for c in per_case}
    vec_mismatch = sorted(k for k in set(ours) | set(stored_vec) if ours.get(k) != stored_vec.get(k))

    # The stored per-case records also carry span_ranks. Compare every one of them, not
    # just the pass/fail rollup — a scorer can agree on the verdict and disagree on rank.
    stored_by_id = {c["case_id"]: c for c in stored_cases["cases"]}
    rank_mismatch = []
    for c in per_case:
        s = stored_by_id.get(c["case_id"])
        if s is None:
            rank_mismatch.append({"case_id": c["case_id"], "reason": "absent from stored case results"})
        elif list(s["span_ranks"]) != list(c["span_ranks"]):
            rank_mismatch.append({"case_id": c["case_id"], "stored": s["span_ranks"],
                                  "recomputed": c["span_ranks"]})

    ok = (all(m["match"] for m in metric_checks) and all(m["match"] for m in stored_checks)
          and not vec_mismatch and not rank_mismatch)

    payload = {
        "record_id": "EVAL-NATQ2-H-002-SCORER-VERIFICATION",
        "purpose": "Offline recomputation of the frozen BM25 comparator through the shared NATQ-002 scorer.",
        "bm25_retrieval_rerun": False,
        "database_queried": False,
        "input": "experiments/EVAL-NATQ-BM25-BASELINE-001/logs/bm25-ranked-output.jsonl (stored)",
        "input_rows": len(rows),
        "cases_scored": len(per_case),
        "evaluation_depth": DEPTH,
        "scorer": "experiments/EVAL-NATQ2-H-002/scripts/natq2_scorer.py",
        "scorer_sha256": sha(Path(__file__).resolve().parent / "natq2_scorer.py"),
        "pinned_inputs": {str(p.relative_to(REPO)): v for p, v in PINNED.items()},
        "recomputed_metrics": metrics,
        "recomputed_per_slice": per_slice(per_case),
        "checks_against_preregistered_values": metric_checks,
        "checks_against_stored_results_file": stored_checks,
        "per_case_pass_fail_vector_mismatches": vec_mismatch,
        "per_case_span_rank_mismatches": rank_mismatch,
        "verified": ok,
    }
    OUT.write_text(json.dumps(payload, indent=1) + "\n")

    for m in metric_checks:
        print(f"{'ok  ' if m['match'] else 'FAIL'} {m['metric']:<28} "
              f"recomputed={m['recomputed']} expected={m['expected']}")
    print(f"{'ok  ' if not vec_mismatch else 'FAIL'} per-case pass/fail vector    "
          f"{len(ours)} cases, {len(vec_mismatch)} mismatches")
    print(f"{'ok  ' if not rank_mismatch else 'FAIL'} per-case span ranks          "
          f"{len(rank_mismatch)} mismatches")
    print(f"\nVERIFIED={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
