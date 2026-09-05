#!/usr/bin/env python3
"""Demonstrate, on synthetic fixtures, that NATQ-001 strict_recall@10 and NATQ-002
case_hit@10 are different functions of the same retrieval.

No database, no corpus, no benchmark case, no protected partition. Every fixture below
is hand-constructed so the divergence is a property of the two definitions rather than
of any particular dataset. The two scorers are transcribed from the authoritative
sources named in METRIC-AUDIT-001.json and are re-derived here only so the difference
can be exhibited; nothing here is used to compute or restate a real score.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "METRIC-AUDIT-001-PROBE-OUTPUT.json"
DEPTH = 10


def natq001_span_hit(hit: dict, span: dict) -> bool:
    """EXP-018/scripts/system_e.py::overlaps and run_exp018_development.py::dict_overlaps.

    Requires section_path equality on top of document identity and character overlap.
    """
    return (hit["version_id"] == span["version_id"]
            and list(hit["section_path"]) == list(span["section_path"])
            and hit["char_start"] < span["char_end"]
            and hit["char_end"] > span["char_start"])


def natq002_span_hit(hit: dict, span: dict) -> bool:
    """EVAL-NATQ-BM25-BASELINE-001/scripts/run_bm25_baseline.py, inner next(...).

    Document identity and character overlap only. section_path is not consulted, and
    NATQ-002 gold evidence does not carry the field.
    """
    return (hit["version_id"] == span["version_id"]
            and hit["char_start"] < span["char_end"]
            and hit["char_end"] > span["char_start"])


def first_rank(hits: list[dict], span: dict, pred) -> int | None:
    """Both implementations collapse duplicate covering chunks to the best rank.

    NATQ-001 takes min() over matching rows (run_exp018_development.py::first_span_rank);
    NATQ-002 takes next() over a rank-ordered hit list (lexical_search returns rows
    ordered by round(score,9) DESC, chunk_id ASC and numbers them 1..k). Same value.
    """
    ranks = [h["rank"] for h in hits if pred(h, span) and h["rank"] <= DEPTH]
    return min(ranks) if ranks else None


def score(case: dict) -> dict:
    s001 = [first_rank(case["hits"], sp, natq001_span_hit) for sp in case["spans"]]
    s002 = [first_rank(case["hits"], sp, natq002_span_hit) for sp in case["spans"]]
    return {
        "case": case["name"],
        "why": case["why"],
        "n_spans": len(case["spans"]),
        "natq001_span_ranks": s001,
        "natq002_span_ranks": s002,
        # strict_recall@10 counts a case only when EVERY span is within depth
        "natq001_strict_case_pass": bool(s001) and all(r is not None for r in s001),
        # case_hit@10 counts a case when ANY span is within depth
        "natq002_case_hit_pass": any(r is not None for r in s002),
        # the NATQ-002 metric that does use ALL-spans aggregation
        "natq002_case_full_coverage_pass": bool(s002) and all(r is not None for r in s002),
    }


def h(rank, vid, sp, a, b):
    return {"rank": rank, "version_id": vid, "section_path": sp, "char_start": a, "char_end": b}


def sp(vid, path, a, b):
    return {"version_id": vid, "section_path": path, "char_start": a, "char_end": b}


CASES = [
    {"name": "SYN-1 multi-span, one span found",
     "why": "Aggregation differs: ANY-span passes, ALL-spans fails.",
     "spans": [sp("v1", ["Guide", "Auth"], 100, 200), sp("v1", ["Guide", "Limits"], 900, 980)],
     "hits": [h(3, "v1", ["Guide", "Auth"], 80, 260)]},
    {"name": "SYN-2 single span, chunk filed under a different section_path",
     "why": "Match predicate differs: NATQ-001 requires section_path equality, NATQ-002 does not.",
     "spans": [sp("v1", ["Guide", "Auth"], 100, 200)],
     "hits": [h(2, "v1", ["Guide", "Auth", "Keys"], 90, 250)]},
    {"name": "SYN-3 single span, exact section_path, overlapping chunk",
     "why": "Control: the two definitions agree when the case is single-span and the paths match.",
     "spans": [sp("v1", ["Guide", "Auth"], 100, 200)],
     "hits": [h(1, "v1", ["Guide", "Auth"], 50, 300)]},
    {"name": "SYN-4 covering chunk returned below the evaluation depth",
     "why": "Control: depth 10 is enforced identically by both.",
     "spans": [sp("v1", ["Guide", "Auth"], 100, 200)],
     "hits": [h(11, "v1", ["Guide", "Auth"], 90, 250)]},
    {"name": "SYN-5 two duplicate covering chunks at ranks 3 and 7",
     "why": "Control: duplicates collapse to the best rank in both; no double counting.",
     "spans": [sp("v1", ["Guide", "Auth"], 100, 200)],
     "hits": [h(3, "v1", ["Guide", "Auth"], 90, 150), h(7, "v1", ["Guide", "Auth"], 140, 260)]},
    {"name": "SYN-6 cross-document case, only the first document's span found",
     "why": "Multi-document aggregation: each span resolves in its own version_id under both.",
     "spans": [sp("v1", ["A"], 10, 40), sp("v2", ["B"], 10, 40)],
     "hits": [h(4, "v1", ["A"], 5, 50)]},
    {"name": "SYN-7 one-character overlap at the span boundary",
     "why": "Both predicates are half-open interval intersection, so a single shared character hits.",
     "spans": [sp("v1", ["A"], 100, 200)],
     "hits": [h(5, "v1", ["A"], 199, 400)]},
]


def main() -> int:
    rows = [score(c) for c in CASES]
    diverge = [r for r in rows
               if r["natq001_strict_case_pass"] != r["natq002_case_hit_pass"]]
    agg_only = [r for r in rows
                if r["natq001_strict_case_pass"] != r["natq002_case_full_coverage_pass"]]
    payload = {
        "record_id": "METRIC-AUDIT-001-PROBE",
        "purpose": "Exhibit the divergence between NATQ-001 strict_recall@10 and "
                   "NATQ-002 case_hit@10 on synthetic fixtures.",
        "uses_real_benchmark_data": False,
        "uses_database": False,
        "protected_partitions_opened": [],
        "evaluation_depth": DEPTH,
        "cases": rows,
        "cases_where_strict_and_case_hit_disagree": [r["case"] for r in diverge],
        "cases_where_strict_and_full_coverage_disagree": [r["case"] for r in agg_only],
        "conclusion": {
            "aggregation": "strict_recall@10 is an ALL-spans metric; case_hit@10 is an "
                           "ANY-span metric. SYN-1 and SYN-6 separate them.",
            "match_predicate": "strict_recall@10 additionally requires section_path "
                               "equality. SYN-2 separates them.",
            "nearest_natq002_analogue_of_strict": "case_full_coverage@10 matches the "
                                                  "aggregation but still not the predicate; "
                                                  "SYN-2 remains a disagreement.",
        },
    }
    OUT.write_text(json.dumps(payload, indent=1) + "\n")
    for r in rows:
        print(f"{r['case']:<58} strict={int(r['natq001_strict_case_pass'])} "
              f"case_hit={int(r['natq002_case_hit_pass'])} "
              f"full_cov={int(r['natq002_case_full_coverage_pass'])}")
    print(f"\ndisagree (strict vs case_hit):      {[r['case'].split()[0] for r in diverge]}")
    print(f"disagree (strict vs full_coverage): {[r['case'].split()[0] for r in agg_only]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
