#!/usr/bin/env python3
"""Summarise the V1 experiment outputs into one comparable table.

Three things this produces that a per-experiment ``macro_recall`` does not:

* **Strict per-case scoring.** ``macro_recall`` averages span-level recall, so a
  two-span multi-hop case that finds one span contributes 0.5. A configuration
  can therefore post a higher headline number without answering one more
  question completely. ``cases_fully_recalled`` counts only cases where every
  expected span was retrieved.
* **Paired comparisons.** On 20 cases the interesting quantity is which specific
  questions moved, not the mean.
* **Document vs span recall.** When a span is missed, this records whether the
  correct *document* was in the top-k anyway. That separates "retrieval went to
  the wrong place" from "retrieval went to the right document and picked the
  wrong chunk", which are different bugs with different fixes.

Usage::

    python scripts/analyze_experiments.py --out experiments/summary.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag_v1.reporting import paired_compare

EXPERIMENTS = [
    ("EXP-000 lexical (BM25)", "experiments/EXP-000/results.json"),
    ("EXP-000 lexical (websearch AND, failed)", "experiments/EXP-000/results-websearch-and.json"),
    ("EXP-001 dense (LSA)", "experiments/EXP-001/results.json"),
    ("EXP-002 hybrid interleave", "experiments/EXP-002/results.json"),
    ("EXP-003 RRF rrf_k=10", "experiments/EXP-003/results-k10.json"),
    ("EXP-003 RRF rrf_k=20", "experiments/EXP-003/results-k20.json"),
    ("EXP-003 RRF rrf_k=60", "experiments/EXP-003/results-k60.json"),
]

COMPARISONS = [
    ("EXP-000 lexical", "EXP-001 dense", "experiments/EXP-000/results.json", "experiments/EXP-001/results.json"),
    ("EXP-000 lexical", "EXP-002 hybrid", "experiments/EXP-000/results.json", "experiments/EXP-002/results.json"),
    ("EXP-001 dense", "EXP-002 hybrid", "experiments/EXP-001/results.json", "experiments/EXP-002/results.json"),
    ("EXP-002 hybrid", "EXP-003 RRF k=60", "experiments/EXP-002/results.json", "experiments/EXP-003/results-k60.json"),
    ("EXP-000 lexical", "EXP-003 RRF k=60", "experiments/EXP-000/results.json", "experiments/EXP-003/results-k60.json"),
    (
        "EXP-000 lexical",
        "EXP-003 RRF k=60 pool=100",
        "experiments/EXP-000/results.json",
        "experiments/EXP-003/sweep/pool100-rrfk60.json",
    ),
]


def summarize(path: Path) -> dict | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    if not cases:
        return None

    total_spans = sum(c["expected_evidence_count"] for c in cases)
    found_spans = sum(c["evidence_found_count"] for c in cases)
    full = [c for c in cases if c["recall"] >= 1.0]

    # Of the spans that were missed, how often was the right document retrieved?
    missed = wrong_chunk_right_doc = 0
    for case in cases:
        hit_versions = {h["version_id"] for h in case.get("hits", [])}
        for ref in case.get("missed", []):
            missed += 1
            if ref["version_id"] in hit_versions:
                wrong_chunk_right_doc += 1

    by_category: dict[str, list[float]] = {}
    for case in cases:
        by_category.setdefault(case["category"], []).append(case["recall"])

    return {
        "cases": len(cases),
        "macro_span_recall": round(data.get("macro_recall") or 0.0, 4),
        "cases_fully_recalled": len(full),
        "cases_fully_recalled_pct": round(len(full) / len(cases), 4),
        "spans_found": found_spans,
        "spans_expected": total_spans,
        "span_recall": round(found_spans / total_spans, 4) if total_spans else None,
        "missed_spans": missed,
        "missed_spans_with_correct_document_retrieved": wrong_chunk_right_doc,
        "document_level_recall": round((total_spans - missed + wrong_chunk_right_doc) / total_spans, 4)
        if total_spans
        else None,
        "macro_recall_by_category": {
            cat: round(sum(v) / len(v), 4) for cat, v in sorted(by_category.items())
        },
        "per_case_recall": {c["case_id"]: c["recall"] for c in cases},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="experiments/summary.json")
    args = parser.parse_args()

    summaries = {}
    for label, path in EXPERIMENTS:
        result = summarize(Path(path))
        if result:
            summaries[label] = result

    comparisons = []
    for old_label, new_label, old_path, new_path in COMPARISONS:
        if Path(old_path).exists() and Path(new_path).exists():
            comparisons.append(
                {"from": old_label, "to": new_label, **paired_compare(Path(old_path), Path(new_path))}
            )

    sweep = {}
    for path in sorted(Path("experiments/EXP-003/sweep").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        cases = data.get("cases", [])
        sweep[path.stem] = {
            "macro_span_recall": round(data.get("macro_recall") or 0.0, 4),
            "cases_fully_recalled": sum(1 for c in cases if c["recall"] >= 1.0),
        }

    payload = {"experiments": summaries, "paired_comparisons": comparisons, "exp003_sweep": sweep}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"{'experiment':44s} {'macroR':>7s} {'full':>6s} {'spans':>9s} {'docR':>6s}")
    for label, s in summaries.items():
        print(
            f"{label:44s} {s['macro_span_recall']:7.3f} "
            f"{s['cases_fully_recalled']:3d}/{s['cases']:<2d} "
            f"{s['spans_found']:4d}/{s['spans_expected']:<4d} {s['document_level_recall']:6.3f}"
        )
    print()
    for comp in comparisons:
        print(
            f"{comp['from']:20s} -> {comp['to']:26s} "
            f"rescued={len(comp['rescued']):d} regressed={len(comp['regressed']):d} "
            f"net={comp['net_rescued']:+d}  {comp['rescued']} / {comp['regressed']}"
        )
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
