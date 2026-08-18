#!/usr/bin/env python3
"""EXP-011 — is the raw query formulation part of the remaining bottleneck?

EXP-010 established that 21 of 22 expected answers are already visible to the
encoder, so what is left is a ranking problem. Every experiment so far changed the
document side; the query has been a raw user-question string since EXP-000.

    A  raw                                    (frozen control, must reproduce 0.775)
    B  normalized                             diagnostic
    C  raw + normalized                       multi-view, original preserved
    D  structured                             diagnostic
    E  raw + normalized + structured          the primary comparison

Every cell runs its views through BM25 and the transformer and fuses the resulting
lists with the preregistered RRF. The document side is frozen: same chunks, same
stored vectors, same model, same window, same BM25 parameters, same pool/rrf_k/top_k.
Only the query text differs.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.embedders_transformer import MODEL_CARD as TRANSFORMER_CARD
from rag_v1.embedders_transformer import TransformerEncoder
from rag_v1.evals.io import load_cases
from rag_v1.ids import config_hash
from rag_v1.parsing import PARSER_VERSION
from rag_v1.query_cache import CachedQueryEmbedder
from rag_v1.query_views import QUERY_TRANSFORM_VERSION, build_views
from rag_v1.retrieval import BM25_B, BM25_K1, dense_search, lexical_search, rrf_fuse_labelled
from rag_v1.types import EvidenceRef, SearchHit

CONTROL_SNAP = "snap_689e336380a054d8039dc35b2c09cd0a"
CONTROL_SET = "cs_v1_control"
TRANSFORMER_MODEL = "emb_e7d4183fd6eb878ae2fdf080efb6861e"
MAX_SEQ = 512
PROBE_DEPTHS = (10, 20, 30, 50, 100, 300)
TOP_K = 10
RRF_POOL, RRF_K = 50, 60

CELLS = {
    "A_raw_query_control": ("raw",),
    "B_normalized_query": ("normalized",),
    "C_raw_plus_normalized": ("raw", "normalized"),
    "D_structured_query": ("structured",),
    "E_three_view": ("raw", "normalized", "structured"),
}

# From the committed EXP-009 512 / EXP-010 artifacts.
REPRO_TARGET = {"macro_span_recall": 0.775, "cases_fully_recalled": 15, "spans_found_at_10": 17}


def overlaps(hit: SearchHit, ref: EvidenceRef) -> bool:
    return (hit.version_id == ref.version_id and hit.section_path == ref.section_path
            and hit.char_start < ref.char_end and hit.char_end > ref.char_start)


def summarise(per_case: dict, latencies: dict) -> dict:
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
        "latency_ms": {k: round(statistics.mean(v), 1) for k, v in latencies.items() if v},
        "cases": per_case,
    }


def run_cell(cases, views: tuple[str, ...], transformer, deep: int) -> dict:
    per_case: dict = {}
    latencies = {"bm25": [], "transformer": [], "fusion": [], "total": []}
    calls_per_query: list[int] = []

    for case in cases:
        built = build_views(case.question, views)
        # Identical view text produces an identical ranked list; fusing it twice
        # would double-reward it for no retrieval reason. Deduplicate on text and
        # record which views collapsed.
        by_text: dict[str, list[str]] = {}
        for view in built:
            by_text.setdefault(view.text, []).append(view.name)

        started = time.time()
        labelled: list[tuple[str, list[SearchHit]]] = []
        bm25_ms = tx_ms = 0.0
        for text, names in by_text.items():
            label = "+".join(names)
            t0 = time.time()
            lex = lexical_search(text, CONTROL_SNAP, RRF_POOL)
            bm25_ms += (time.time() - t0) * 1000
            t0 = time.time()
            den = dense_search(text, CONTROL_SNAP, TRANSFORMER_MODEL, RRF_POOL,
                               embedder=transformer)
            tx_ms += (time.time() - t0) * 1000
            labelled.append((f"bm25({label})", lex))
            labelled.append((f"transformer({label})", den))

        t0 = time.time()
        hits = rrf_fuse_labelled(labelled, rrf_k=RRF_K, top_k=deep)
        fusion_ms = (time.time() - t0) * 1000
        total_ms = (time.time() - started) * 1000

        latencies["bm25"].append(bm25_ms)
        latencies["transformer"].append(tx_ms)
        latencies["fusion"].append(fusion_ms)
        latencies["total"].append(total_ms)
        calls_per_query.append(len(labelled))

        spans = []
        for ref in case.expected_evidence:
            hit = next((h for h in hits if overlaps(h, ref)), None)
            doc_rank = next((h.rank for h in hits if h.version_id == ref.version_id), None)
            spans.append({
                "section_path": ref.section_path, "span": [ref.char_start, ref.char_end],
                "rank": hit.rank if hit else None, "doc_rank": doc_rank,
                "chunk_id": hit.chunk_id if hit else None,
                "score": round(hit.score, 6) if hit else None,
                "within": {str(d): (hit is not None and hit.rank <= d) for d in PROBE_DEPTHS},
                "doc_within_10": doc_rank is not None and doc_rank <= TOP_K,
                # Which view actually surfaced the answer.
                "provenance": hit.metadata.get("source_ranks") if hit else None,
            })
        n_found = sum(1 for s in spans if s["within"]["10"])
        per_case[case.case_id] = {
            "case_id": case.case_id, "category": case.category, "question": case.question,
            "views": {v.name: v.stats(case.question) for v in built},
            "view_texts": {v.name: v.text for v in built},
            "deduplicated_views": {t: n for t, n in by_text.items() if len(n) > 1},
            "retrieval_calls": len(labelled),
            "spans": spans,
            "recall": n_found / len(spans) if spans else 1.0,
            "fully_recalled": bool(spans) and n_found == len(spans),
            "doc_recall": sum(1 for s in spans if s["doc_within_10"]) / len(spans) if spans else 1.0,
        }

    out = summarise(per_case, latencies)
    out["query_views"] = list(views)
    out["mean_retrieval_calls_per_query"] = round(statistics.mean(calls_per_query), 2)
    return out


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
    moves: dict[str, int] = {}
    rows = []
    for cid, before in a["cases"].items():
        after = b["cases"][cid]
        for idx, (sb, sa) in enumerate(zip(before["spans"], after["spans"], strict=True)):
            mv = movement(sb["rank"], sa["rank"])
            moves[mv] = moves.get(mv, 0) + 1
            rows.append({"case_id": cid, "span_index": idx,
                         "rank_before": sb["rank"], "rank_after": sa["rank"],
                         "doc_rank_before": sb["doc_rank"], "doc_rank_after": sa["doc_rank"],
                         "provenance_after": sa["provenance"], "movement": mv})
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
            "zero_regression": not buckets["regressed"],
            "span_movement_counts": moves, "span_rows": rows}


def reranker_gate(cell: dict) -> dict:
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
    ceilings = {}
    for pool in (30, 50, 100):
        inside = bands["1-10"] + bands["11-30"]
        if pool >= 50:
            inside += bands["31-50"]
        if pool >= 100:
            inside += bands["51-100"]
        ceilings[str(pool)] = round(inside / total, 4)
    return {"bands": bands, "spans_total": total,
            "perfect_reranker_ceiling_at_pool": ceilings,
            "note": "A reranker can only reorder what retrieval already returned."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", default="evals/golden/v1.jsonl")
    parser.add_argument("--deep", type=int, default=300)
    parser.add_argument("--out", default="experiments/EXP-011/results.json")
    args = parser.parse_args()

    cases = [c for c in load_cases(Path(args.golden)) if c.expected_evidence]
    started = time.time()
    encoder = TransformerEncoder(max_seq=MAX_SEQ).load()
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)

    results = {}
    for key, views in CELLS.items():
        results[key] = {"description": f"query views: {', '.join(views)}",
                        "chunk_set": CONTROL_SET, **run_cell(cases, views, transformer, args.deep)}

    got = results["A_raw_query_control"]
    repro_checks = {
        field: {"expected": expected, "actual": got[field],
                "match": (round(got[field], 3) == expected if isinstance(expected, float)
                          else got[field] == expected)}
        for field, expected in REPRO_TARGET.items()
    }
    repro = {"A_raw_query_control": {"checks": repro_checks,
                                     "reproduced": all(c["match"] for c in repro_checks.values())}}

    base = results["A_raw_query_control"]
    comparisons = {f"A->{k[0]} {k}": pair("A_raw_query_control", base, k, v)
                   for k, v in results.items() if k != "A_raw_query_control"}

    # Work multiplier against the raw-query control.
    base_calls = base["mean_retrieval_calls_per_query"]
    cost = {k: {"retrieval_calls_per_query": v["mean_retrieval_calls_per_query"],
                "work_multiplier_vs_A": round(v["mean_retrieval_calls_per_query"] / base_calls, 2),
                "latency_ms": v["latency_ms"],
                "latency_multiplier_vs_A": round(
                    v["latency_ms"]["total"] / base["latency_ms"]["total"], 2)}
            for k, v in results.items()}

    an003 = {k: {"views": v["cases"]["AN-003"]["view_texts"],
                 "spans": v["cases"]["AN-003"]["spans"]} for k, v in results.items()}

    unresolved = sorted({cid for cid, c in base["cases"].items() if not c["fully_recalled"]})
    persistent = {cid: {k: {"ranks": [s["rank"] for s in v["cases"][cid]["spans"]],
                            "doc_ranks": [s["doc_rank"] for s in v["cases"][cid]["spans"]],
                            "fully_recalled": v["cases"][cid]["fully_recalled"]}
                        for k, v in results.items()} for cid in unresolved}

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                         stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        commit = None

    payload = {
        "experiment_id": "EXP-011",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "corpus_snapshot": CONTROL_SNAP,
        "chunk_set": CONTROL_SET,
        "retrievers": ["bm25", "transformer_dense"],
        "embedding_model": {"model_id": TRANSFORMER_MODEL, **TRANSFORMER_CARD,
                            "max_seq_length": MAX_SEQ},
        "transformer_fingerprint": encoder.model_version,
        "query_transform_version": QUERY_TRANSFORM_VERSION,
        "document_side": "FROZEN — chunks, text, embeddings and model reused from EXP-009/EXP-010",
        "parser_version": PARSER_VERSION,
        "top_k": TOP_K,
        "probe_depths": list(PROBE_DEPTHS),
        "candidate_pool": RRF_POOL,
        "rrf_k": RRF_K,
        "bm25_config": {"k1": BM25_K1, "b": BM25_B, "ts_config": "simple"},
        "retrieval_config": {"reranker": None, "llm_query_rewriting": False,
                             "metadata_filtering": False, "stemming": False,
                             "enrichment": None, "ann_index": False},
        "fusion": "RRF over labelled lists; every view participates equally, no weights",
        "reproduction_gate": repro,
        "configurations": results,
        "paired_comparison": comparisons,
        "cost": cost,
        "query_embedding_cache": transformer.stats(),
        "an003_deep_dive": an003,
        "persistent_failures": persistent,
        "reranker_decision_gate": {k: reranker_gate(v) for k, v in results.items()},
        "runtime_seconds": round(time.time() - started, 1),
        "errors": [],
    }
    payload["config_hash"] = config_hash({
        "cells": {k: list(v) for k, v in CELLS.items()}, "model": TRANSFORMER_MODEL,
        "window": MAX_SEQ, "top_k": TOP_K, "pool": RRF_POOL, "rrf_k": RRF_K,
        "transform": QUERY_TRANSFORM_VERSION, "bm25": payload["bm25_config"],
    })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    print(f"{'cell':26s} {'macroR':>7s} {'full':>7s} {'spans':>8s} {'docR':>7s} {'MRR':>6s} "
          f"{'a@10':>5s} {'a@30':>5s} {'a@100':>6s} {'calls':>6s} {'ms':>8s}")
    for key, r in results.items():
        a = r["spans_absent_from_top"]
        print(f"{key:26s} {r['macro_span_recall']:7.3f} {r['cases_fully_recalled']:3d}/{r['cases_total']:<3d} "
              f"{r['spans_found_at_10']:3d}/{r['spans_total']:<4d} {r['document_recall']:7.3f} "
              f"{r['mrr']:6.3f} {a['10']:5d} {a['30']:5d} {a['100']:6d} "
              f"{r['mean_retrieval_calls_per_query']:6.1f} {r['latency_ms']['total']:8.1f}")
    print(f"\nreproduction gate A: {'PASS' if repro['A_raw_query_control']['reproduced'] else 'FAIL'}")
    if not repro["A_raw_query_control"]["reproduced"]:
        for f, c in repro_checks.items():
            if not c["match"]:
                print(f"   {f}: expected {c['expected']}, got {c['actual']}")
    print()
    for name, c in comparisons.items():
        flag = " ZERO-REGRESSION" if c["zero_regression"] and c["rescued"] else ""
        print(f"{name:34s} d={c['macro_recall_delta']:+.3f} rescued={c['rescued']} "
              f"regressed={c['regressed']} net={c['net_rescued']:+d}{flag}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
