#!/usr/bin/env python3
"""EXP-009 — does a contextual transformer retrieval encoder beat static vectors?

EXP-007 tested the vocabulary-mismatch hypothesis with mean-pooled FastText and
reported the result as weak evidence, because an order-insensitive bag of word
vectors is a weak instrument. This experiment supplies a real one: a transformer
bi-encoder trained for semantic search.

    A  BM25 on control chunks            (frozen baseline, must reproduce EXP-007A)
    B  FastText dense on control chunks  (must reproduce EXP-007B)
    C  transformer dense on control chunks               (the intervention)
    D  BM25 + transformer RRF            (preregistered pool 50, rrf_k 60, top_k 10)
    E  BM25 + FastText RRF               (reproduces EXP-007C, D's real comparator)

Only the encoder differs between B and C: same chunks, same snapshot, same exact
cosine search, same pooling family, same absence of prefixes, same top_k.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.embedders_pretrained import MODEL_CARD as FASTTEXT_CARD
from rag_v1.embedders_pretrained import get_pretrained_embedder
from rag_v1.embedders_transformer import MODEL_CARD as TRANSFORMER_CARD
from rag_v1.embedders_transformer import TransformerEncoder
from rag_v1.evals.io import load_cases
from rag_v1.ids import config_hash
from rag_v1.parsing import PARSER_VERSION
from rag_v1.retrieval import BM25_B, BM25_K1, dense_search, lexical_search, rrf_fuse
from rag_v1.types import EvidenceRef, SearchHit

CONTROL_SNAP = "snap_689e336380a054d8039dc35b2c09cd0a"
CONTROL_SET = "cs_v1_control"
FASTTEXT_MODEL = "emb_c11d8d9184d2ebc1ac60801a6452b884"
TRANSFORMER_MODEL = "emb_5197b67ea29a78cce96e91054d01d1dd"
PROBE_DEPTHS = (10, 20, 50, 100, 300)
TOP_K = 10
RRF_POOL, RRF_K = 50, 60

# Reproduction targets, taken from the committed EXP-007 artifact. A mismatch means
# something under the experiment moved and the comparison is void.
REPRO_TARGETS = {
    "A_bm25_control": {"macro_span_recall": 0.475, "cases_fully_recalled": 9, "spans_found_at_10": 10},
    "B_fasttext_control": {"macro_span_recall": 0.425, "cases_fully_recalled": 8,
                           "spans_found_at_10": 9, "mrr": 0.36, "absent_at_300": 5},
    "E_bm25_fasttext_rrf": {"macro_span_recall": 0.6, "cases_fully_recalled": 11,
                            "spans_found_at_10": 13},
}


def overlaps(hit: SearchHit, ref: EvidenceRef) -> bool:
    return (hit.version_id == ref.version_id and hit.section_path == ref.section_path
            and hit.char_start < ref.char_end and hit.char_end > ref.char_start)


def summarise(per_case: dict, latencies: list[float]) -> dict:
    all_spans = [s for c in per_case.values() for s in c["spans"]]
    found = [s["rank"] for s in all_spans if s["rank"] is not None]
    recalls = [c["recall"] for c in per_case.values()]
    return {
        "macro_span_recall": round(sum(recalls) / len(recalls), 4),
        "cases_fully_recalled": sum(1 for c in per_case.values() if c["fully_recalled"]),
        "cases_total": len(per_case),
        "spans_found_at_10": sum(1 for s in all_spans if s["within"]["10"]),
        "spans_total": len(all_spans),
        "document_recall": round(sum(c["doc_recall"] for c in per_case.values()) / len(per_case), 4),
        "mrr": round(sum(1 / s["rank"] for s in all_spans if s["rank"]) / len(all_spans), 4),
        "mean_evidence_rank_when_found": round(statistics.mean(found), 2) if found else None,
        "median_evidence_rank_when_found": statistics.median(found) if found else None,
        "spans_absent_from_top": {str(d): sum(1 for s in all_spans if not s["within"][str(d)])
                                  for d in PROBE_DEPTHS},
        "mean_query_ms": round(statistics.mean(latencies), 1),
        "cases": per_case,
    }


def run_cell(cases, search, deep: int) -> dict:
    per_case, latencies = {}, []
    for case in cases:
        started = time.time()
        hits = search(case.question, deep)
        latencies.append((time.time() - started) * 1000)
        spans = []
        for ref in case.expected_evidence:
            hit = next((h for h in hits if overlaps(h, ref)), None)
            doc_rank = next((h.rank for h in hits if h.version_id == ref.version_id), None)
            spans.append({
                "section_path": ref.section_path, "span": [ref.char_start, ref.char_end],
                "rank": hit.rank if hit else None, "doc_rank": doc_rank,
                "chunk_id": hit.chunk_id if hit else None,
                "chunk_len": (hit.char_end - hit.char_start) if hit else None,
                "similarity": round(hit.score, 6) if hit else None,
                "within": {str(d): (hit is not None and hit.rank <= d) for d in PROBE_DEPTHS},
                "doc_within_10": doc_rank is not None and doc_rank <= TOP_K,
            })
        n_found = sum(1 for s in spans if s["within"]["10"])
        per_case[case.case_id] = {
            "case_id": case.case_id, "category": case.category, "question": case.question,
            "spans": spans,
            "recall": n_found / len(spans) if spans else 1.0,
            "fully_recalled": bool(spans) and n_found == len(spans),
            "doc_recall": sum(1 for s in spans if s["doc_within_10"]) / len(spans) if spans else 1.0,
        }
    return summarise(per_case, latencies)


def movement(before: int | None, after: int | None) -> str:
    if before is None and after is None:
        return "still_unreachable"
    if before is None:
        return "strong_improvement" if after <= TOP_K else "newly_reachable_outside_k"
    if after is None:
        return "lost_entirely"
    if before > TOP_K >= after:
        return "strong_improvement"
    if after > TOP_K >= before:
        return "strong_regression"
    if after < before:
        return "improved_no_cross"
    if after > before:
        return "worsened_no_cross"
    return "unchanged"


def pair(a_label: str, a: dict, b_label: str, b: dict) -> dict:
    buckets = {"rescued": [], "regressed": [], "unchanged_good": [], "unchanged_bad": [],
               "partial_change": []}
    quadrant = {"both_correct": [], "only_before": [], "only_after": [], "neither": []}
    moves: dict[str, int] = {}
    rows = []
    for cid, before in a["cases"].items():
        after = b["cases"][cid]
        if before["fully_recalled"] and after["fully_recalled"]:
            quadrant["both_correct"].append(cid)
        elif before["fully_recalled"]:
            quadrant["only_before"].append(cid)
        elif after["fully_recalled"]:
            quadrant["only_after"].append(cid)
        else:
            quadrant["neither"].append(cid)
        for idx, (sb, sa) in enumerate(zip(before["spans"], after["spans"], strict=True)):
            mv = movement(sb["rank"], sa["rank"])
            moves[mv] = moves.get(mv, 0) + 1
            rows.append({"case_id": cid, "span_index": idx, "category": before["category"],
                         "section_path": sb["section_path"],
                         "rank_before": sb["rank"], "rank_after": sa["rank"],
                         "similarity_before": sb["similarity"], "similarity_after": sa["similarity"],
                         "doc_rank_before": sb["doc_rank"], "doc_rank_after": sa["doc_rank"],
                         "movement": mv})
        if before["fully_recalled"] and not after["fully_recalled"]:
            buckets["regressed"].append(cid)
        elif not before["fully_recalled"] and after["fully_recalled"]:
            buckets["rescued"].append(cid)
        elif before["fully_recalled"]:
            buckets["unchanged_good"].append(cid)
        elif before["recall"] != after["recall"]:
            buckets["partial_change"].append(cid)
        else:
            buckets["unchanged_bad"].append(cid)
    return {"from": a_label, "to": b_label, **buckets,
            "net_rescued": len(buckets["rescued"]) - len(buckets["regressed"]),
            "macro_recall_delta": round(b["macro_span_recall"] - a["macro_span_recall"], 4),
            "quadrant": quadrant, "span_movement_counts": moves, "span_rows": rows}


def reranker_gate(cell: dict) -> dict:
    """Count where the answer actually sits. Counts only - no reranker is built."""
    bands = {"1-10": 0, "11-30": 0, "31-50": 0, "51-100": 0, "101-300": 0, "absent_at_300": 0}
    for case in cell["cases"].values():
        for span in case["spans"]:
            r = span["rank"]
            if r is None:
                bands["absent_at_300"] += 1
            elif r <= 10:
                bands["1-10"] += 1
            elif r <= 30:
                bands["11-30"] += 1
            elif r <= 50:
                bands["31-50"] += 1
            elif r <= 100:
                bands["51-100"] += 1
            else:
                bands["101-300"] += 1
    reachable = bands["11-30"] + bands["31-50"] + bands["51-100"]
    total = sum(bands.values())
    return {"bands": bands, "spans_total": total,
            "recoverable_by_a_perfect_reranker_over_100": reachable,
            "ceiling_if_reranker_were_perfect_at_100": round((bands["1-10"] + reachable) / total, 4),
            "note": "A reranker can only reorder what retrieval already returned. "
                    "Spans absent at the pool depth are unreachable by any reranker."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", default="evals/golden/v1.jsonl")
    parser.add_argument("--deep", type=int, default=300)
    parser.add_argument("--max-seq", type=int, default=256)
    parser.add_argument("--transformer-model", default=TRANSFORMER_MODEL)
    parser.add_argument("--out", default="experiments/EXP-009/results.json")
    args = parser.parse_args()

    cases = [c for c in load_cases(Path(args.golden)) if c.expected_evidence]
    started = time.time()

    fasttext = get_pretrained_embedder()
    transformer = TransformerEncoder(max_seq=args.max_seq).load()

    def bm25(q, k):
        return lexical_search(q, CONTROL_SNAP, k)

    def ft_dense(q, k):
        return dense_search(q, CONTROL_SNAP, FASTTEXT_MODEL, k, embedder=fasttext)

    def tx_dense(q, k):
        return dense_search(q, CONTROL_SNAP, args.transformer_model, k, embedder=transformer)

    def rrf(dense_fn):
        def search(q, k):
            return rrf_fuse([bm25(q, RRF_POOL), dense_fn(q, RRF_POOL)], rrf_k=RRF_K, top_k=k)
        return search

    results = {
        "A_bm25_control": {"description": "BM25 on control chunks (frozen baseline)",
                           "retriever": "bm25", **run_cell(cases, bm25, args.deep)},
        "B_fasttext_control": {"description": "static FastText dense on control chunks",
                               "retriever": "dense_fasttext", **run_cell(cases, ft_dense, args.deep)},
        "C_transformer_control": {"description": "transformer dense on control chunks",
                                  "retriever": "dense_transformer", **run_cell(cases, tx_dense, args.deep)},
        "D_bm25_transformer_rrf": {"description": "BM25 + transformer RRF",
                                   "retriever": "rrf", **run_cell(cases, rrf(tx_dense), 2 * RRF_POOL)},
        "E_bm25_fasttext_rrf": {"description": "BM25 + FastText RRF (reproduces EXP-007C)",
                                "retriever": "rrf", **run_cell(cases, rrf(ft_dense), 2 * RRF_POOL)},
    }

    # Reproduction gate: the baselines must land exactly where EXP-007 left them.
    repro = {}
    for key, targets in REPRO_TARGETS.items():
        got = results[key]
        checks = {}
        for field, expected in targets.items():
            actual = (got["spans_absent_from_top"]["300"] if field == "absent_at_300"
                      else got[field])
            # EXP-007 stored MRR to 4 decimals (0.3599); the brief quotes it to 3
            # (0.360). Compare floats at the precision the target was written to,
            # or an exact reproduction reads as a failure.
            match = (round(actual, len(str(expected).split(".")[-1])) == expected
                     if isinstance(expected, float) else actual == expected)
            checks[field] = {"expected": expected, "actual": actual, "match": match}
        repro[key] = {"checks": checks, "reproduced": all(c["match"] for c in checks.values())}

    comparisons = {
        "B->C static vs transformer (the hypothesis)": pair(
            "B_fasttext_control", results["B_fasttext_control"],
            "C_transformer_control", results["C_transformer_control"]),
        "A->C BM25 vs transformer": pair(
            "A_bm25_control", results["A_bm25_control"],
            "C_transformer_control", results["C_transformer_control"]),
        "E->D fusion: FastText vs transformer": pair(
            "E_bm25_fasttext_rrf", results["E_bm25_fasttext_rrf"],
            "D_bm25_transformer_rrf", results["D_bm25_transformer_rrf"]),
        "A->D BM25 vs fused transformer": pair(
            "A_bm25_control", results["A_bm25_control"],
            "D_bm25_transformer_rrf", results["D_bm25_transformer_rrf"]),
    }

    # Cases with a prior history worth checking individually.
    watch = {
        "fasttext_wins_in_exp007": ["AN-002", "AN-007", "AN-012"],
        "known_failures": ["AN-001", "AN-003", "AN-004", "AN-006", "AN-008",
                           "AN-010", "AN-011", "AN-012", "OA-006"],
        "fusion_regression_watch": ["OA-004"],
    }
    case_watch = {}
    for group, ids in watch.items():
        case_watch[group] = {}
        for cid in ids:
            if cid not in results["A_bm25_control"]["cases"]:
                continue
            case_watch[group][cid] = {
                cell: {"recall": results[cell]["cases"][cid]["recall"],
                       "fully_recalled": results[cell]["cases"][cid]["fully_recalled"],
                       "ranks": [s["rank"] for s in results[cell]["cases"][cid]["spans"]]}
                for cell in results
            }

    an003 = {
        cell: {"question": results[cell]["cases"]["AN-003"]["question"],
               "spans": results[cell]["cases"]["AN-003"]["spans"]}
        for cell in results if "AN-003" in results[cell]["cases"]
    }

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                         stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        commit = None

    payload = {
        "experiment_id": "EXP-009",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "corpus_snapshot_id": CONTROL_SNAP,
        "chunk_set_id": CONTROL_SET,
        "parser_version": PARSER_VERSION,
        "encoders": {
            "fasttext": {"model_id": FASTTEXT_MODEL, **FASTTEXT_CARD},
            "transformer": {"model_id": args.transformer_model,
                            **TRANSFORMER_CARD, "max_seq_length": args.max_seq,
                            "fingerprint": transformer.model_version,
                            "library": "onnxruntime 1.29.0, tokenizers 0.23.1"},
        },
        "distance_metric": "cosine (exact, no ANN index)",
        "top_k": TOP_K,
        "probe_depths": list(PROBE_DEPTHS),
        "bm25_config": {"k1": BM25_K1, "b": BM25_B, "ts_config": "simple"},
        "rrf_config": {"pool": RRF_POOL, "rrf_k": RRF_K, "top_k": TOP_K,
                       "preregistered_from": "EXP-007", "tuned": False},
        "retrieval_config": {"reranker": None, "query_rewriting": False,
                             "query_expansion": False, "stemming": False,
                             "enrichment": None, "chunker": "v1_control (frozen)"},
        "reproduction_gate": repro,
        "configurations": results,
        "paired_comparison": comparisons,
        "case_watchlist": case_watch,
        "an003_deep_dive": an003,
        "reranker_decision_gate": {cell: reranker_gate(results[cell]) for cell in results},
        "runtime_seconds": round(time.time() - started, 1),
        "errors": [],
    }
    payload["config_hash"] = config_hash({
        "cells": sorted(results), "transformer": args.transformer_model,
        "fasttext": FASTTEXT_MODEL, "top_k": TOP_K, "max_seq": args.max_seq,
        "bm25": payload["bm25_config"], "rrf": payload["rrf_config"],
    })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    print(f"{'cell':28s} {'macroR':>7s} {'full':>8s} {'spans':>8s} {'docR':>6s} {'MRR':>6s} "
          f"{'a@10':>5s} {'a@50':>5s} {'a@300':>6s} {'ms':>8s}")
    for key, r in results.items():
        a = r["spans_absent_from_top"]
        print(f"{key:28s} {r['macro_span_recall']:7.3f} {r['cases_fully_recalled']:3d}/{r['cases_total']:<4d} "
              f"{r['spans_found_at_10']:3d}/{r['spans_total']:<4d} {r['document_recall']:6.3f} "
              f"{r['mrr']:6.3f} {a['10']:5d} {a['50']:5d} {a['300']:6d} {r['mean_query_ms']:8.1f}")
    print("\nreproduction gate:")
    for key, r in repro.items():
        bad = [f"{f}: expected {c['expected']} got {c['actual']}"
               for f, c in r["checks"].items() if not c["match"]]
        print(f"  {key:28s} {'PASS' if r['reproduced'] else 'FAIL — ' + '; '.join(bad)}")
    print()
    for name, c in comparisons.items():
        print(f"{name:44s} d={c['macro_recall_delta']:+.3f} rescued={c['rescued']} "
              f"regressed={c['regressed']} net={c['net_rescued']:+d}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
