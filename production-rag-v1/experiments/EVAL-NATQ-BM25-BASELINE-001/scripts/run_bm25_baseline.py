#!/usr/bin/env python3
"""EVAL-NATQ-BM25-BASELINE-001 — pure BM25 over cs_v1_control, NATQ-002 validation only.

This is SYSTEM-BM25-NATQ-CONTROL, not SYSTEM-H and not a substitute for it. It exists
to exercise the frozen split and the harness and to establish the preregistered local
comparator for a future SYSTEM-H paired run.

The reserve partition is never opened. The runner reads exactly one split file, and a
gate refuses to proceed if any pinned hash fails to reproduce or if the reserve access
log has grown.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
E = REPO / "experiments/EVAL-NATQ-BM25-BASELINE-001"
SPLIT = REPO / "evals/splits/natq-002"
DEPTH = 10


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def gate() -> dict:
    """Refuse to score unless every pinned input reproduces and the reserve is untouched."""
    pre = json.loads((E / "EVAL-NATQ-BM25-BASELINE-001-PREREGISTRATION.json").read_text())
    checks = {
        "benchmark_file": (sha(REPO / pre["data"]["benchmark_file"]), pre["data"]["benchmark_file_sha256"]),
        "validation": (sha(REPO / pre["data"]["validation_file"]), pre["data"]["validation_sha256"]),
        "reserve": (sha(REPO / pre["data"]["reserve_file"]), pre["data"]["reserve_sha256"]),
        "bm25_source": (sha(REPO / "src/rag_v1/retrieval.py"), pre["system_under_test"]["source_sha256"]),
    }
    for name, (got, want) in checks.items():
        if got != want:
            raise SystemExit(f"refusing to score: {name} hash changed\n  got  {got}\n  want {want}")
    log = SPLIT / "reserve-access.log.jsonl"
    if log.stat().st_size != 0:
        raise SystemExit("refusing to score: the reserve access log is not empty")
    return pre


def main() -> int:
    from rag_v1.retrieval import lexical_search

    pre = gate()
    val = json.loads((SPLIT / "validation.json").read_text())
    snap = pre["data"]["corpus_snapshot_id"]
    cases = val["cases"]

    ranked_path = E / "logs/bm25-ranked-output.jsonl"
    rows, per_case, lat = [], [], []
    for c in cases:
        t0 = time.perf_counter()
        hits = lexical_search(c["question"], snap, k=DEPTH)
        lat.append((time.perf_counter() - t0) * 1000.0)
        for h in hits:
            rows.append({"case_id": c["case_id"], "rank": h.rank, "chunk_id": h.chunk_id,
                         "version_id": h.version_id, "char_start": h.char_start,
                         "char_end": h.char_end, "score": h.score,
                         "section_path": h.section_path})
        # a gold span is hit when a returned chunk overlaps it in that span's own document
        span_ranks = []
        for e in c["evidence"]:
            r = next((h.rank for h in hits
                      if h.version_id == e["version_id"]
                      and h.char_start < e["char_end"] and h.char_end > e["char_start"]), None)
            span_ranks.append(r)
        hit_ranks = [r for r in span_ranks if r is not None]
        per_case.append({
            "case_id": c["case_id"], "slice": c["slice"], "provider": c["provider"],
            "n_gold_spans": len(c["evidence"]),
            "span_ranks": span_ranks,
            "hit_at_10": bool(hit_ranks),
            "full_coverage_at_10": all(r is not None for r in span_ranks),
            "hit_at_1": any(r == 1 for r in hit_ranks),
            "best_rank": min(hit_ranks) if hit_ranks else None,
            "latency_ms": round(lat[-1], 3)})

    ranked_path.write_text("".join(json.dumps(r) + "\n" for r in rows))

    n_cases, n_spans = len(cases), sum(c["n_gold_spans"] for c in per_case)
    all_ranks = [r for c in per_case for r in c["span_ranks"]]
    micro_mrr = sum(1.0 / r for r in all_ranks if r) / n_spans
    slat = sorted(lat)

    def pct(p: float) -> float:
        return round(slat[min(len(slat) - 1, int(round(p * (len(slat) - 1))))], 3)

    def agg(sub):
        if not sub:
            return None
        sr = [r for c in sub for r in c["span_ranks"]]
        return {"cases": len(sub), "gold_spans": len(sr),
                "case_hit_at_10": round(sum(c["hit_at_10"] for c in sub) / len(sub), 4),
                "case_full_coverage_at_10": round(sum(c["full_coverage_at_10"] for c in sub) / len(sub), 4),
                "span_recall_at_10": round(sum(1 for r in sr if r) / len(sr), 4),
                "case_hit_at_1": round(sum(c["hit_at_1"] for c in sub) / len(sub), 4),
                "micro_MRR": round(sum(1.0 / r for r in sr if r) / len(sr), 4)}

    metrics = {
        "evaluation_depth": DEPTH, "cases": n_cases, "gold_spans": n_spans,
        "micro_MRR": round(micro_mrr, 4),
        "case_hit_at_10": round(sum(c["hit_at_10"] for c in per_case) / n_cases, 4),
        "case_full_coverage_at_10": round(sum(c["full_coverage_at_10"] for c in per_case) / n_cases, 4),
        "span_recall_at_10": round(sum(1 for r in all_ranks if r) / n_spans, 4),
        "case_hit_at_1": round(sum(c["hit_at_1"] for c in per_case) / n_cases, 4),
        "latency_p50_ms": pct(0.50), "latency_p95_ms": pct(0.95),
        "per_slice": {s: agg([c for c in per_case if c["slice"] == s]) for s in "ABCDE"},
        "per_provider": {p: agg([c for c in per_case if c["provider"] == p])
                         for p in sorted({c["provider"] for c in per_case})},
    }
    cr = {"experiment_id": "EVAL-NATQ-BM25-BASELINE-001",
          "system_id": "SYSTEM-BM25-NATQ-CONTROL",
          "partition": "validation", "evaluation_depth": DEPTH,
          "case_level_pass_fail_vector": {c["case_id"]: c["hit_at_10"] for c in per_case},
          "cases": per_case}
    (E / "EVAL-NATQ-BM25-BASELINE-001-CASE-RESULTS.json").write_text(json.dumps(cr, indent=1))

    run = {"experiment_id": "EVAL-NATQ-BM25-BASELINE-001",
           "system_id": "SYSTEM-BM25-NATQ-CONTROL",
           "is_not_system_h": True, "system_h_runs_consumed": 0,
           "partition_scored": "validation", "reserve_opened": False,
           "preregistration_sha256": sha(E / "EVAL-NATQ-BM25-BASELINE-001-PREREGISTRATION.json"),
           "inputs": {k: v for k, v in pre["data"].items()},
           "system": pre["system_under_test"],
           "metrics": metrics,
           "artifacts": {
               "ranked_output": str(ranked_path.relative_to(REPO)),
               "ranked_output_sha256": sha(ranked_path),
               "ranked_output_rows": len(rows),
               "case_results": "experiments/EVAL-NATQ-BM25-BASELINE-001/EVAL-NATQ-BM25-BASELINE-001-CASE-RESULTS.json",
               "case_results_sha256": sha(E / "EVAL-NATQ-BM25-BASELINE-001-CASE-RESULTS.json"),
               "runner": "experiments/EVAL-NATQ-BM25-BASELINE-001/scripts/run_bm25_baseline.py",
               "runner_sha256": sha(Path(__file__))},
           "decision": None,
           "decision_note": "Control measurement. No pass/fail threshold applies to BM25."}
    (E / "EVAL-NATQ-BM25-BASELINE-001-RESULTS.json").write_text(json.dumps(run, indent=1))
    print(json.dumps(metrics, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
