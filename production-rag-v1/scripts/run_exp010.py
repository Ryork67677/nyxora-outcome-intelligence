#!/usr/bin/env python3
"""EXP-010 — does chunking to fit the encoder window preserve the EXP-009 gains?

EXP-009 found retrieval quality moved with how much of a retrieval unit the encoder
could see. That was a correlation across two window settings. EXP-010 tests whether
it is causal by holding the window fixed at 512 and changing the retrieval unit
instead, so that every unit fits.

    A  BM25 on control chunks                       (frozen baseline, must reproduce)
    B  transformer @512 on control chunks           (must reproduce EXP-009)
    C  BM25 + transformer RRF, both on control      (must reproduce EXP-009's best)
    D  transformer @512 on ENCODER-ALIGNED chunks   (the isolated intervention)
    E  BM25 on control + transformer on aligned     (mixed representation)

B -> D isolates encoder-aware chunking. C -> E asks whether it improves the
strongest configuration measured so far. Nothing else moves: same encoder, same
fingerprint, same tokenizer, same pooling, same exact cosine search, same
preregistered RRF parameters, no enrichment, no reranker, no query rewriting.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.chunkers.encoder_aligned import SPEC as ALIGNED_SPEC
from rag_v1.chunkers.encoder_aligned import encoder_budget
from rag_v1.embedders_transformer import MODEL_CARD as TRANSFORMER_CARD
from rag_v1.embedders_transformer import TransformerEncoder
from rag_v1.evals.io import load_cases
from rag_v1.ids import config_hash
from rag_v1.parsing import PARSER_VERSION
from rag_v1.retrieval import (
    BM25_B,
    BM25_K1,
    dense_search,
    lexical_search,
    rrf_fuse,
    rrf_fuse_regions,
)
from rag_v1.types import EvidenceRef, SearchHit

CONTROL_SNAP = "snap_689e336380a054d8039dc35b2c09cd0a"
CONTROL_SET = "cs_v1_control"
ALIGNED_SNAP = "snap_1ad94e790cec69f85f58fb0b916a4b6b"
ALIGNED_SET = "cs_v4_encoder_aligned"
# Same encoder identity for both chunk sets: the model_id derives from the model
# card and window, not from what it was pointed at. Vectors are separated by
# chunk_set, not by model, which is what makes B and D comparable at all.
TRANSFORMER_MODEL = "emb_e7d4183fd6eb878ae2fdf080efb6861e"
MAX_SEQ = 512
PROBE_DEPTHS = (10, 20, 50, 100, 300)
TOP_K = 10
RRF_POOL, RRF_K = 50, 60

# Taken from the committed EXP-009 512 artifact. A mismatch means something under
# the experiment moved and D/E cannot be interpreted.
REPRO_TARGETS = {
    "A_bm25_control": {"macro_span_recall": 0.475, "cases_fully_recalled": 9,
                       "spans_found_at_10": 10},
    "B_transformer_control": {"macro_span_recall": 0.575, "cases_fully_recalled": 11,
                              "spans_found_at_10": 13},
    "C_bm25_transformer_control_rrf": {"macro_span_recall": 0.775, "cases_fully_recalled": 15,
                                       "spans_found_at_10": 17},
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
                         "chunk_len_before": sb["chunk_len"], "chunk_len_after": sa["chunk_len"],
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
    """Where the answer actually sits. Counts only — no reranker is built."""
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
    total = sum(bands.values())
    at = {}
    for pool in (30, 50, 100):
        inside = bands["1-10"] + bands["11-30"]
        if pool >= 50:
            inside += bands["31-50"]
        if pool >= 100:
            inside += bands["51-100"]
        at[str(pool)] = round(inside / total, 4)
    return {"bands": bands, "spans_total": total,
            "perfect_reranker_ceiling_at_pool": at,
            "note": "A reranker can only reorder what retrieval already returned. "
                    "Spans absent at the pool depth are unreachable by any reranker."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", default="evals/golden/v1.jsonl")
    parser.add_argument("--deep", type=int, default=300)
    parser.add_argument("--out", default="experiments/EXP-010/results.json")
    args = parser.parse_args()

    cases = [c for c in load_cases(Path(args.golden)) if c.expected_evidence]
    started = time.time()
    transformer = TransformerEncoder(max_seq=MAX_SEQ).load()

    def bm25(q, k):
        return lexical_search(q, CONTROL_SNAP, k)

    def tx_control(q, k):
        return dense_search(q, CONTROL_SNAP, TRANSFORMER_MODEL, k, embedder=transformer)

    def tx_aligned(q, k):
        return dense_search(q, ALIGNED_SNAP, TRANSFORMER_MODEL, k, embedder=transformer)

    def rrf_same(q, k):
        # Both retrievers over the control chunks: plain RRF, exactly as EXP-009.
        return rrf_fuse([bm25(q, RRF_POOL), tx_control(q, RRF_POOL)], rrf_k=RRF_K, top_k=k)

    def rrf_mixed(q, k):
        # Different chunk representations: dedup on evidence region, not chunk id.
        return rrf_fuse_regions([bm25(q, RRF_POOL), tx_aligned(q, RRF_POOL)],
                                rrf_k=RRF_K, top_k=k)

    results = {
        "A_bm25_control": {"description": "BM25 on control chunks (frozen baseline)",
                           "chunk_set": CONTROL_SET, "retriever": "bm25",
                           **run_cell(cases, bm25, args.deep)},
        "B_transformer_control": {"description": "transformer @512 on control chunks",
                                  "chunk_set": CONTROL_SET, "retriever": "dense_transformer",
                                  **run_cell(cases, tx_control, args.deep)},
        "C_bm25_transformer_control_rrf": {"description": "BM25 + transformer RRF, both control",
                                           "chunk_set": CONTROL_SET, "retriever": "rrf",
                                           **run_cell(cases, rrf_same, 2 * RRF_POOL)},
        "D_transformer_aligned": {"description": "transformer @512 on encoder-aligned chunks",
                                  "chunk_set": ALIGNED_SET, "retriever": "dense_transformer",
                                  **run_cell(cases, tx_aligned, args.deep)},
        "E_bm25_control_plus_aligned_rrf": {
            "description": "BM25 on control + transformer on encoder-aligned, region RRF",
            "chunk_set": f"{CONTROL_SET} (bm25) + {ALIGNED_SET} (dense)", "retriever": "rrf_regions",
            **run_cell(cases, rrf_mixed, 2 * RRF_POOL)},
    }

    repro = {}
    for key, targets in REPRO_TARGETS.items():
        got = results[key]
        checks = {}
        for field, expected in targets.items():
            actual = got[field]
            match = (round(actual, len(str(expected).split(".")[-1])) == expected
                     if isinstance(expected, float) else actual == expected)
            checks[field] = {"expected": expected, "actual": actual, "match": match}
        repro[key] = {"checks": checks, "reproduced": all(c["match"] for c in checks.values())}

    comparisons = {
        "B->D encoder alignment (the hypothesis)": pair(
            "B_transformer_control", results["B_transformer_control"],
            "D_transformer_aligned", results["D_transformer_aligned"]),
        "C->E mixed-representation fusion": pair(
            "C_bm25_transformer_control_rrf", results["C_bm25_transformer_control_rrf"],
            "E_bm25_control_plus_aligned_rrf", results["E_bm25_control_plus_aligned_rrf"]),
        "A->D BM25 vs aligned transformer": pair(
            "A_bm25_control", results["A_bm25_control"],
            "D_transformer_aligned", results["D_transformer_aligned"]),
        "A->E BM25 vs mixed fusion": pair(
            "A_bm25_control", results["A_bm25_control"],
            "E_bm25_control_plus_aligned_rrf", results["E_bm25_control_plus_aligned_rrf"]),
    }

    watch = {
        "fasttext_wins_still_contested": ["AN-002", "AN-007", "AN-012"],
        "fusion_regression_watch": ["OA-004"],
        "hardest_case": ["AN-003"],
    }
    case_watch = {}
    for group, ids in watch.items():
        case_watch[group] = {
            cid: {key: {"recall": r["cases"][cid]["recall"],
                        "fully_recalled": r["cases"][cid]["fully_recalled"],
                        "ranks": [s["rank"] for s in r["cases"][cid]["spans"]],
                        "doc_ranks": [s["doc_rank"] for s in r["cases"][cid]["spans"]],
                        "chunk_lens": [s["chunk_len"] for s in r["cases"][cid]["spans"]]}
                  for key, r in results.items()}
            for cid in ids
        }

    an003 = {key: r["cases"]["AN-003"] for key, r in results.items()}

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                         stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        commit = None

    payload = {
        "experiment_id": "EXP-010",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "corpus_snapshots": {"control": CONTROL_SNAP, "encoder_aligned": ALIGNED_SNAP},
        "chunk_sets": {"control": CONTROL_SET, "encoder_aligned": ALIGNED_SET},
        "chunker": {"name": ALIGNED_SPEC.name, "version": ALIGNED_SPEC.version,
                    "config_hash": ALIGNED_SPEC.config_hash, "config": ALIGNED_SPEC.config},
        "encoder_budget": encoder_budget(),
        "encoder_window": MAX_SEQ,
        "embedding_model": {"model_id": TRANSFORMER_MODEL, **TRANSFORMER_CARD,
                            "max_seq_length": MAX_SEQ},
        "model_fingerprint": transformer.model_version,
        "tokenizer_fingerprint": TRANSFORMER_CARD["tokenizer_sha256"],
        "distance_metric": "cosine (exact, no ANN index)",
        "parser_version": PARSER_VERSION,
        "top_k": TOP_K,
        "probe_depths": list(PROBE_DEPTHS),
        "candidate_pool": RRF_POOL,
        "rrf_k": RRF_K,
        "bm25_config": {"k1": BM25_K1, "b": BM25_B, "ts_config": "simple"},
        "retrieval_config": {"reranker": None, "query_rewriting": False, "query_expansion": False,
                             "stemming": False, "enrichment": None, "ann_index": False,
                             "pooling": TRANSFORMER_CARD["pooling"]},
        "fusion_identity_rule": (
            "Same evidence region = same version_id AND same section_path AND overlapping "
            "[char_start, char_end). One RRF contribution per retriever per region, taken at "
            "that retriever's best rank. Reduces to plain RRF when both lists come from one "
            "chunk set, because chunks within a set do not overlap."
        ),
        "reproduction_gate": repro,
        "configurations": results,
        "paired_comparison": comparisons,
        "case_watchlist": case_watch,
        "an003_deep_dive": an003,
        "reranker_decision_gate": {k: reranker_gate(v) for k, v in results.items()},
        "runtime_seconds": round(time.time() - started, 1),
        "errors": [],
    }
    payload["config_hash"] = config_hash({
        "cells": sorted(results), "model": TRANSFORMER_MODEL, "window": MAX_SEQ,
        "top_k": TOP_K, "pool": RRF_POOL, "rrf_k": RRF_K, "bm25": payload["bm25_config"],
        "chunker": ALIGNED_SPEC.config_hash,
    })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    print(f"{'cell':38s} {'macroR':>7s} {'full':>7s} {'spans':>8s} {'docR':>7s} {'MRR':>6s} "
          f"{'a@10':>5s} {'a@50':>5s} {'a@300':>6s} {'ms':>8s}")
    for key, r in results.items():
        a = r["spans_absent_from_top"]
        print(f"{key:38s} {r['macro_span_recall']:7.3f} {r['cases_fully_recalled']:3d}/{r['cases_total']:<3d} "
              f"{r['spans_found_at_10']:3d}/{r['spans_total']:<4d} {r['document_recall']:7.3f} "
              f"{r['mrr']:6.3f} {a['10']:5d} {a['50']:5d} {a['300']:6d} {r['mean_query_ms']:8.1f}")
    print("\nreproduction gate:")
    for key, g in repro.items():
        print(f"  {key:38s} {'PASS' if g['reproduced'] else 'FAIL'}")
        if not g["reproduced"]:
            for f, c in g["checks"].items():
                if not c["match"]:
                    print(f"      {f}: expected {c['expected']}, got {c['actual']}")
    print()
    for name, c in comparisons.items():
        print(f"{name:44s} d={c['macro_recall_delta']:+.3f} rescued={c['rescued']} "
              f"regressed={c['regressed']} net={c['net_rescued']:+d}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
