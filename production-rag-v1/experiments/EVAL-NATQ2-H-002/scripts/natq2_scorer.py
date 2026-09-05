#!/usr/bin/env python3
"""The single NATQ-002 scorer. Both SYSTEM-H and the frozen BM25 comparator go through it.

METRIC-AUDIT-001 found that NATQ-001's strict_recall@10 and NATQ-002's case_hit@10 are
NOT_EQUIVALENT on two axes: strict requires ALL gold spans, and it additionally requires
section_path equality. Neither applies here. Scoring SYSTEM-H with the NATQ-001 helpers
would silently measure a stricter metric and make the comparison against the frozen
0.375 meaningless — so this module exists to make the two systems share one definition
by construction rather than by intention.

Definitions, from EVAL-NATQ2-H-002-PREREGISTRATION.json:
  span hit    a gold span is HIT at depth k if any chunk in the top k overlaps the span's
              [char_start, char_end) interval in the span's OWN version_id. section_path
              is not consulted; NATQ-002 gold evidence does not carry it.
  case_hit    ANY one gold span hit. Denominator: cases.
  full_cov    EVERY gold span hit. Denominator: cases.
  span_recall fraction of gold spans hit. Denominator: gold spans.
  micro-MRR   mean over ALL gold spans of 1/rank of the first chunk hitting that span;
              an unhit span contributes 0 rather than being dropped.
Duplicate covering chunks collapse to the best rank. Hits must arrive in rank order.
"""

from __future__ import annotations

DEPTH = 10


def span_hit_rank(hits, span, depth: int = DEPTH) -> int | None:
    """Best rank at which a chunk covers this span, or None within the depth.

    Deliberately does NOT compare section_path. See the module docstring.
    """
    best = None
    for h in hits:
        r = h["rank"]
        if r > depth:
            continue
        if (h["version_id"] == span["version_id"]
                and h["char_start"] < span["char_end"]
                and h["char_end"] > span["char_start"]):
            if best is None or r < best:
                best = r
    return best


def score_case(case: dict, hits: list[dict], depth: int = DEPTH) -> dict:
    ranks = [span_hit_rank(hits, sp, depth) for sp in case["evidence"]]
    found = [r for r in ranks if r is not None]
    return {
        "case_id": case["case_id"],
        "slice": case.get("slice"),
        "provider": case.get("provider"),
        "n_gold_spans": len(ranks),
        "span_ranks": ranks,
        "hit_at_10": bool(found),
        "full_coverage_at_10": bool(ranks) and all(r is not None for r in ranks),
        "hit_at_1": any(r == 1 for r in found),
        "best_rank": min(found) if found else None,
    }


def aggregate(per_case: list[dict]) -> dict:
    n = len(per_case)
    ranks = [r for c in per_case for r in c["span_ranks"]]
    n_spans = len(ranks)
    if n == 0 or n_spans == 0:
        raise ValueError("refusing to aggregate an empty partition")
    return {
        "cases": n,
        "gold_spans": n_spans,
        "micro_MRR": round(sum(1.0 / r for r in ranks if r) / n_spans, 4),
        "case_hit_at_10": round(sum(c["hit_at_10"] for c in per_case) / n, 4),
        "case_full_coverage_at_10": round(sum(c["full_coverage_at_10"] for c in per_case) / n, 4),
        "span_recall_at_10": round(sum(1 for r in ranks if r) / n_spans, 4),
        "case_hit_at_1": round(sum(c["hit_at_1"] for c in per_case) / n, 4),
    }


def per_slice(per_case: list[dict]) -> dict:
    out = {}
    for s in "ABCDE":
        sub = [c for c in per_case if c["slice"] == s]
        out[s] = aggregate(sub) if sub else None
    return out


def case_micro_mrr(case_result: dict) -> float:
    """Per-case mean reciprocal rank over that case's own spans.

    The paired bootstrap resamples CASES, so it needs a per-case statistic. Weighting by
    the case's span count reconstructs the partition micro-MRR exactly when every case is
    present, which is what makes this the right per-case unit rather than a macro average.
    """
    ranks = case_result["span_ranks"]
    return sum(1.0 / r for r in ranks if r) / len(ranks) if ranks else 0.0
