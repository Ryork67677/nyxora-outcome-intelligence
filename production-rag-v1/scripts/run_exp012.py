#!/usr/bin/env python3
"""EXP-012 — does removing cross-document competition fix passage ranking?

The diagnosis under test: the system identifies the right document but ranks the
right passage below chunks from thousands of other documents.

    A       global raw hybrid                   (control, must reproduce 0.775)
    B       BM25 routing -> BM25 local          diagnostic
    C       transformer routing -> tx local     diagnostic
    D       fused routing -> fused local        the primary intervention
    ORACLE  golden document -> fused local      DIAGNOSTIC ONLY, NOT DEPLOYABLE

Nothing about the scorers changes. Document ranks are derived from the existing
chunk rankings, and local ranking reuses full-corpus scores — only the candidate
set shrinks.
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
from rag_v1.hierarchical import (
    DOCUMENT_RRF_K,
    chunk_counts_for_documents,
    collapse_to_documents,
    document_rank_of,
    fuse_document_rankings,
    fused_rank_of,
    routing_recall,
)
from rag_v1.ids import config_hash
from rag_v1.parsing import PARSER_VERSION
from rag_v1.query_cache import CachedQueryEmbedder
from rag_v1.retrieval import BM25_B, BM25_K1, dense_search, lexical_search, rrf_fuse
from rag_v1.types import EvidenceRef, SearchHit

SNAP = "snap_689e336380a054d8039dc35b2c09cd0a"
CHUNK_SET = "cs_v1_control"
MODEL = "emb_e7d4183fd6eb878ae2fdf080efb6861e"
MAX_SEQ = 512
PROBE_DEPTHS = (10, 20, 30, 50, 100, 300)
TOP_K = 10
RRF_POOL, RRF_K = 50, 60
DOC_RANKING_DEPTH = 300
TOP_DOCUMENTS = 5
GLOBAL_CHUNKS = 14209

REPRO_TARGET = {"macro_span_recall": 0.775, "cases_fully_recalled": 15, "spans_found_at_10": 17}


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


def score_case(case, hits: list[SearchHit], extra: dict) -> dict:
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
        })
    found = sum(1 for s in spans if s["within"]["10"])
    return {
        "case_id": case.case_id, "category": case.category, "question": case.question,
        "spans": spans,
        "recall": found / len(spans) if spans else 1.0,
        "fully_recalled": bool(spans) and found == len(spans),
        "doc_recall": sum(1 for s in spans if s["doc_within_10"]) / len(spans) if spans else 1.0,
        **extra,
    }


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
            rows.append({"case_id": cid, "span_index": idx, "rank_before": sb["rank"],
                         "rank_after": sa["rank"], "movement": mv})
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
    return {"bands": bands, "spans_total": total, "perfect_reranker_ceiling_at_pool": ceilings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", default="evals/golden/v1.jsonl")
    parser.add_argument("--deep", type=int, default=300)
    parser.add_argument("--top-documents", type=int, default=TOP_DOCUMENTS)
    parser.add_argument("--out", default="experiments/EXP-012/results.json")
    parser.add_argument("--label", default="primary")
    args = parser.parse_args()

    cases = [c for c in load_cases(Path(args.golden)) if c.expected_evidence]
    started = time.time()
    encoder = TransformerEncoder(max_seq=MAX_SEQ).load()
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)

    def bm25(q, k, versions=None):
        return lexical_search(q, SNAP, k, version_ids=versions)

    def dense(q, k, versions=None):
        return dense_search(q, SNAP, MODEL, k, embedder=transformer, version_ids=versions)

    a_cases, b_cases, c_cases, d_cases, o_cases = {}, {}, {}, {}, {}
    lat = {"A": [], "B": [], "C": [], "D": [], "ORACLE": []}
    routing_rows = []
    pool_sizes = []
    stage_timing = {"global": [], "routing": [], "local": []}

    for case in cases:
        q = case.question
        expected_docs = {ref.version_id for ref in case.expected_evidence}

        # ---- global stage (shared by the control and by routing) -------------
        t0 = time.time()
        g_lex_deep = bm25(q, DOC_RANKING_DEPTH)
        g_den_deep = dense(q, DOC_RANKING_DEPTH)
        stage_timing["global"].append((time.time() - t0) * 1000)

        # ---- A: global control ----------------------------------------------
        t0 = time.time()
        a_hits = rrf_fuse([bm25(q, RRF_POOL), dense(q, RRF_POOL)], rrf_k=RRF_K, top_k=2 * RRF_POOL)
        lat["A"].append((time.time() - t0) * 1000)
        a_cases[case.case_id] = score_case(case, a_hits, {})

        # ---- Stage 1: document rankings --------------------------------------
        t0 = time.time()
        lex_docs = collapse_to_documents(g_lex_deep)
        den_docs = collapse_to_documents(g_den_deep)
        fused_docs = fuse_document_rankings(
            [("bm25", lex_docs), ("transformer", den_docs)], rrf_k=DOCUMENT_RRF_K)
        stage_timing["routing"].append((time.time() - t0) * 1000)

        n = args.top_documents
        top_lex = [v for v, _ in lex_docs[:n]]
        top_den = [v for v, _ in den_docs[:n]]
        top_fused = [e["version_id"] for e in fused_docs[:n]]

        counts = chunk_counts_for_documents(SNAP, CHUNK_SET, top_fused)
        pool_sizes.append(counts["chunks"])

        routing_rows.append({
            "case_id": case.case_id,
            "expected_documents": sorted(expected_docs),
            "expected_document_count": len(expected_docs),
            "bm25_document_rank": {d: document_rank_of(lex_docs, d) for d in sorted(expected_docs)},
            "transformer_document_rank": {d: document_rank_of(den_docs, d) for d in sorted(expected_docs)},
            "fused_document_rank": {d: fused_rank_of(fused_docs, d) for d in sorted(expected_docs)},
            "all_expected_in_top_n": expected_docs <= set(top_fused),
            "selected_documents": top_fused,
            "local_candidate_chunks": counts["chunks"],
            "recall_bm25": routing_recall(lex_docs, expected_docs),
            "recall_transformer": routing_recall(den_docs, expected_docs),
            "recall_fused": routing_recall(fused_docs, expected_docs),
        })

        # ---- Stage 2: local passage retrieval --------------------------------
        t0 = time.time()
        b_hits = bm25(q, 2 * RRF_POOL, top_lex)
        c_hits = dense(q, 2 * RRF_POOL, top_den)
        d_hits = rrf_fuse([bm25(q, RRF_POOL, top_fused), dense(q, RRF_POOL, top_fused)],
                          rrf_k=RRF_K, top_k=2 * RRF_POOL)
        stage_timing["local"].append((time.time() - t0) * 1000)
        lat["B"].append(0.0)
        lat["C"].append(0.0)
        lat["D"].append(stage_timing["global"][-1] + stage_timing["routing"][-1]
                        + stage_timing["local"][-1])

        b_cases[case.case_id] = score_case(case, b_hits, {"selected_documents": top_lex})
        c_cases[case.case_id] = score_case(case, c_hits, {"selected_documents": top_den})
        d_cases[case.case_id] = score_case(case, d_hits, {
            "selected_documents": top_fused,
            "local_candidate_chunks": counts["chunks"],
            "all_expected_documents_routed": expected_docs <= set(top_fused),
        })

        # ---- ORACLE (diagnostic only, uses golden document identity) ---------
        t0 = time.time()
        oracle_docs = sorted(expected_docs)
        o_hits = rrf_fuse([bm25(q, RRF_POOL, oracle_docs), dense(q, RRF_POOL, oracle_docs)],
                          rrf_k=RRF_K, top_k=2 * RRF_POOL)
        lat["ORACLE"].append((time.time() - t0) * 1000)
        o_counts = chunk_counts_for_documents(SNAP, CHUNK_SET, oracle_docs)
        o_cases[case.case_id] = score_case(case, o_hits, {
            "oracle_documents": oracle_docs,
            "oracle_candidate_chunks": o_counts["chunks"],
        })

    results = {
        "A_global_raw_hybrid": {"description": "global BM25 + transformer RRF (control)",
                                "topology": "global", **summarise(a_cases, lat["A"])},
        "B_bm25_hierarchical": {"description": "BM25 routing -> BM25 local passages",
                                "topology": "hierarchical", **summarise(b_cases, lat["B"])},
        "C_transformer_hierarchical": {"description": "transformer routing -> transformer local",
                                       "topology": "hierarchical", **summarise(c_cases, lat["C"])},
        "D_fused_hierarchical": {"description": "fused routing -> fused local passages",
                                 "topology": "hierarchical", **summarise(d_cases, lat["D"])},
    }
    oracle = {"description": "ORACLE / DIAGNOSTIC / NOT DEPLOYABLE — golden document, fused local",
              "deployable": False, "uses_golden_document": True,
              **summarise(o_cases, lat["ORACLE"])}

    got = results["A_global_raw_hybrid"]
    checks = {f: {"expected": e, "actual": got[f],
                  "match": (round(got[f], 3) == e if isinstance(e, float) else got[f] == e)}
              for f, e in REPRO_TARGET.items()}
    repro = {"A_global_raw_hybrid": {"checks": checks,
                                     "reproduced": all(c["match"] for c in checks.values())}}

    comparisons = {f"A->{k}": pair("A_global_raw_hybrid", results["A_global_raw_hybrid"], k, v)
                   for k, v in results.items() if k != "A_global_raw_hybrid"}
    comparisons["A->ORACLE (diagnostic)"] = pair(
        "A_global_raw_hybrid", results["A_global_raw_hybrid"], "ORACLE", oracle)

    # Fusion bonus: global versus hierarchical.
    fusion_bonus = {
        "global": {"bm25_alone": None, "transformer_alone": None,
                   "note": "measured in EXP-011: 9 and 11 alone, 15 fused, bonus +4"},
        "hierarchical": {
            "bm25_alone": results["B_bm25_hierarchical"]["cases_fully_recalled"],
            "transformer_alone": results["C_transformer_hierarchical"]["cases_fully_recalled"],
            "best_component": max(results["B_bm25_hierarchical"]["cases_fully_recalled"],
                                  results["C_transformer_hierarchical"]["cases_fully_recalled"]),
            "fused": results["D_fused_hierarchical"]["cases_fully_recalled"],
        },
    }
    fusion_bonus["hierarchical"]["fusion_bonus_cases"] = (
        fusion_bonus["hierarchical"]["fused"] - fusion_bonus["hierarchical"]["best_component"])

    # Stage-1 ceiling.
    routed_all = [r for r in routing_rows if r["all_expected_in_top_n"]]
    outside = [r["case_id"] for r in routing_rows if not r["all_expected_in_top_n"]]
    stage1 = {
        "top_documents": args.top_documents,
        "cases_with_all_expected_documents_routed": len(routed_all),
        "cases_total": len(routing_rows),
        "cases_with_a_document_outside_top_n": outside,
        "max_possible_recall_if_stage2_were_perfect": round(len(routed_all) / len(routing_rows), 4),
        "mean_routing_recall": {
            method: {d: round(statistics.mean([r[f"recall_{method}"][d] for r in routing_rows]), 4)
                     for d in ("1", "3", "5", "10")}
            for method in ("bm25", "transformer", "fused")
        },
    }

    # Failure taxonomy for every case the control does not fully recall.
    taxonomy = {}
    for cid, a_case in a_cases.items():
        if a_case["fully_recalled"]:
            continue
        route = next(r for r in routing_rows if r["case_id"] == cid)
        d_case, o_case = d_cases[cid], o_cases[cid]
        oracle_ranks = [s["rank"] for s in o_case["spans"]]
        hier_ranks = [s["rank"] for s in d_case["spans"]]
        global_ranks = [s["rank"] for s in a_case["spans"]]
        oracle_good = all(r is not None and r <= TOP_K for r in oracle_ranks)
        if not route["all_expected_in_top_n"]:
            label = "DOCUMENT_ROUTING_FAILURE"
        elif d_case["fully_recalled"]:
            label = "GLOBAL_COMPETITION_FAILURE"
        elif not oracle_good:
            label = "WITHIN_DOCUMENT_PASSAGE_RANKING_FAILURE"
        else:
            label = "MIXED_OR_UNCLEAR"
        taxonomy[cid] = {
            "classification": label,
            "expected_document_fused_rank": route["fused_document_rank"],
            "all_expected_documents_routed": route["all_expected_in_top_n"],
            "global_evidence_ranks": global_ranks,
            "hierarchical_evidence_ranks": hier_ranks,
            "oracle_evidence_ranks": oracle_ranks,
            "local_candidate_chunks": route["local_candidate_chunks"],
        }

    an003 = {
        "routing": next(r for r in routing_rows if r["case_id"] == "AN-003"),
        "global": a_cases["AN-003"], "bm25_hierarchical": b_cases["AN-003"],
        "transformer_hierarchical": c_cases["AN-003"], "fused_hierarchical": d_cases["AN-003"],
        "oracle": o_cases["AN-003"],
    }

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                         stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        commit = None

    payload = {
        "experiment_id": "EXP-012",
        "label": args.label,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "corpus_snapshot": SNAP,
        "chunk_set": CHUNK_SET,
        "query": "raw user question only (EXP-011 rescued 0 cases with transformed queries)",
        "bm25_config": {"k1": BM25_K1, "b": BM25_B, "ts_config": "simple",
                        "statistics": "full corpus — never recomputed inside routed documents"},
        "transformer_fingerprint": encoder.model_version,
        "embedding_model": {"model_id": MODEL, **TRANSFORMER_CARD, "max_seq_length": MAX_SEQ},
        "document_ranking_method": "collapse chunk ranking by version_id, one vote per document "
                                   "at its highest-ranked chunk",
        "document_ranking_depth": DOC_RANKING_DEPTH,
        "document_rrf_k": DOCUMENT_RRF_K,
        "top_documents": args.top_documents,
        "passage_rrf_k": RRF_K,
        "candidate_pool": RRF_POOL,
        "top_k": TOP_K,
        "probe_depths": list(PROBE_DEPTHS),
        "parser_version": PARSER_VERSION,
        "retrieval_config": {"reranker": None, "cross_encoder": None, "query_rewriting": False,
                             "enrichment": None, "metadata_filtering": False, "ann_index": False},
        "reproduction_gate": repro,
        "configurations": results,
        "oracle_diagnostic": oracle,
        "paired_comparison": comparisons,
        "fusion_bonus": fusion_bonus,
        "routing": {"per_case": routing_rows, "stage1_ceiling": stage1},
        "failure_taxonomy": taxonomy,
        "an003_deep_dive": an003,
        "reranker_decision_gate": {**{k: reranker_gate(v) for k, v in results.items()},
                                   "ORACLE": reranker_gate(oracle)},
        "local_pool_size": {
            "global_chunks": GLOBAL_CHUNKS,
            "mean": round(statistics.mean(pool_sizes), 1),
            "median": statistics.median(pool_sizes),
            "min": min(pool_sizes), "max": max(pool_sizes),
            "mean_fraction_of_corpus": round(statistics.mean(pool_sizes) / GLOBAL_CHUNKS, 5),
        },
        "stage_latency_ms": {k: round(statistics.mean(v), 1) for k, v in stage_timing.items()},
        "query_embedding_cache": transformer.stats(),
        "runtime_seconds": round(time.time() - started, 1),
        "errors": [],
    }
    payload["config_hash"] = config_hash({
        "top_documents": args.top_documents, "doc_rrf_k": DOCUMENT_RRF_K, "rrf_k": RRF_K,
        "pool": RRF_POOL, "top_k": TOP_K, "model": MODEL, "depth": DOC_RANKING_DEPTH,
        "bm25": payload["bm25_config"],
    })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    print(f"{'cell':30s} {'macroR':>7s} {'full':>7s} {'spans':>8s} {'docR':>7s} {'MRR':>6s} "
          f"{'a@10':>5s} {'a@30':>5s} {'a@300':>6s}")
    for key, r in list(results.items()) + [("ORACLE (not deployable)", oracle)]:
        a = r["spans_absent_from_top"]
        print(f"{key:30s} {r['macro_span_recall']:7.3f} {r['cases_fully_recalled']:3d}/{r['cases_total']:<3d} "
              f"{r['spans_found_at_10']:3d}/{r['spans_total']:<4d} {r['document_recall']:7.3f} "
              f"{r['mrr']:6.3f} {a['10']:5d} {a['30']:5d} {a['300']:6d}")
    print(f"\nreproduction gate A: {'PASS' if repro['A_global_raw_hybrid']['reproduced'] else 'FAIL'}")
    print("\nrouting recall (mean over cases):")
    for method, rec in stage1["mean_routing_recall"].items():
        print(f"  {method:12s} @1={rec['1']:.3f} @3={rec['3']:.3f} @5={rec['5']:.3f} @10={rec['10']:.3f}")
    print(f"  all expected docs routed into top {args.top_documents}: "
          f"{stage1['cases_with_all_expected_documents_routed']}/{stage1['cases_total']}"
          f"  (missing: {stage1['cases_with_a_document_outside_top_n'] or 'none'})")
    print(f"\nlocal pool: mean {payload['local_pool_size']['mean']:.0f} chunks "
          f"({payload['local_pool_size']['mean_fraction_of_corpus'] * 100:.2f}% of {GLOBAL_CHUNKS})")
    print()
    for name, c in comparisons.items():
        print(f"{name:28s} d={c['macro_recall_delta']:+.3f} rescued={c['rescued']} "
              f"regressed={c['regressed']} net={c['net_rescued']:+d}")
    print("\nfailure taxonomy:")
    for cid, t in sorted(taxonomy.items()):
        print(f"  {cid:8s} {t['classification']}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
