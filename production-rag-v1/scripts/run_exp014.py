#!/usr/bin/env python3
"""EXP-014 — can representing a document directly route better than its chunks?

EXP-013 falsified rank aggregation: four rules over chunk rankings all reached
document recall@5 = 0.875 and 17/20 all-required-documents routed. AN-001 showed the
limitation is the input — its document contributes one chunk in 300 and the
transformer never retrieves it — so this experiment represents documents directly.

    DOC-A-MEAN          mean of the document's normalised chunk vectors
    DOC-B-CENTROID      as A, after removing exact-duplicate chunk content
    DOC-C-SECTION       equal weight per section, not per chunk
    DOC-D-MULTIVECTOR   per-section vectors; document scores at its best section

Every vector is a deterministic function of embeddings already stored. Stage 2 is
frozen exactly as EXP-012/013; only document retrieval changes.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from rag_v1.doc_representations import (
    REPRESENTATION_VERSION,
    REPRESENTATIONS,
    build,
    chunk_vectors_are_normalised,
    load_chunk_rows,
)
from rag_v1.embedders_transformer import MODEL_CARD as TRANSFORMER_CARD
from rag_v1.embedders_transformer import TransformerEncoder
from rag_v1.evals.io import load_cases
from rag_v1.hierarchical import chunk_counts_for_documents
from rag_v1.ids import config_hash
from rag_v1.query_cache import CachedQueryEmbedder
from rag_v1.retrieval import BM25_B, BM25_K1, dense_search, lexical_search, rrf_fuse
from rag_v1.routers import DOCUMENT_RRF_K, router_max, rrf_document_lists
from rag_v1.types import EvidenceRef, SearchHit

SNAP = "snap_689e336380a054d8039dc35b2c09cd0a"
CHUNK_SET = "cs_v1_control"
MODEL = "emb_e7d4183fd6eb878ae2fdf080efb6861e"
MAX_SEQ = 512
PROBE_DEPTHS = (10, 20, 30, 50, 100, 300)
TOP_K = 10
RRF_POOL, RRF_K = 50, 60
DOC_DEPTH = 300
TOP_DOCUMENTS = 5
DEPTHS = (1, 3, 5, 10)

REPRO = {"GLOBAL_control": {"macro_span_recall": 0.775, "cases_fully_recalled": 15,
                            "spans_found_at_10": 17},
         "ORACLE": {"macro_span_recall": 0.95, "cases_fully_recalled": 19,
                    "spans_found_at_10": 21}}


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
        "median_evidence_rank_when_found": statistics.median(found) if found else None,
        "spans_absent_from_top": {str(d): sum(1 for s in all_spans if not s["within"][str(d)])
                                  for d in PROBE_DEPTHS},
        "mean_query_ms": round(statistics.mean(latencies), 1) if latencies else None,
        "cases": per_case,
    }


def score_case(case, hits: list[SearchHit], extra: dict) -> dict:
    spans = []
    for ref in case.expected_evidence:
        hit = next((h for h in hits if overlaps(h, ref)), None)
        doc_rank = next((h.rank for h in hits if h.version_id == ref.version_id), None)
        spans.append({"section_path": ref.section_path, "span": [ref.char_start, ref.char_end],
                      "rank": hit.rank if hit else None, "doc_rank": doc_rank,
                      "within": {str(d): (hit is not None and hit.rank <= d) for d in PROBE_DEPTHS},
                      "doc_within_10": doc_rank is not None and doc_rank <= TOP_K})
    found = sum(1 for s in spans if s["within"]["10"])
    return {"case_id": case.case_id, "question": case.question, "spans": spans,
            "recall": found / len(spans) if spans else 1.0,
            "fully_recalled": bool(spans) and found == len(spans),
            "doc_recall": sum(1 for s in spans if s["doc_within_10"]) / len(spans) if spans else 1.0,
            **extra}


def routing_metrics(order: list[str], expected: set[str]) -> dict:
    return {
        "recall": {str(d): round(len(expected & set(order[:d])) / len(expected), 4)
                   for d in DEPTHS},
        "all_routed": {str(d): expected <= set(order[:d]) for d in DEPTHS},
        "ranks": {doc: (order.index(doc) + 1 if doc in order else None) for doc in sorted(expected)},
    }


def summarise_routing(rows: list[dict]) -> dict:
    return {
        "document_recall": {str(d): round(statistics.mean([r["recall"][str(d)] for r in rows]), 4)
                            for d in DEPTHS},
        "all_expected_routed": {str(d): sum(1 for r in rows if r["all_routed"][str(d)])
                                for d in DEPTHS},
        "cases_total": len(rows),
        "stage1_ceiling_at_5": round(sum(1 for r in rows if r["all_routed"]["5"]) / len(rows), 4),
        "cases_missing_at_5": [r["case_id"] for r in rows if not r["all_routed"]["5"]],
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
    return "improved_no_cross" if after < before else (
        "worsened_no_cross" if after > before else "unchanged")


def pair(a_label: str, a: dict, b_label: str, b: dict) -> dict:
    buckets = {"rescued": [], "regressed": [], "unchanged_good": [], "unchanged_bad": [],
               "partial_change": []}
    moves: dict[str, int] = {}
    for cid, before in a["cases"].items():
        after = b["cases"][cid]
        for sb, sa in zip(before["spans"], after["spans"], strict=True):
            mv = movement(sb["rank"], sa["rank"])
            moves[mv] = moves.get(mv, 0) + 1
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
            "zero_regression": not buckets["regressed"], "span_movement_counts": moves}


def reranker_gate(cell: dict) -> dict:
    bands = {"1-10": 0, "11-30": 0, "31-50": 0, "51-100": 0, "101-300": 0, "absent_at_300": 0}
    for case in cell["cases"].values():
        for span in case["spans"]:
            r = span["rank"]
            key = ("absent_at_300" if r is None else "1-10" if r <= 10 else "11-30" if r <= 30
                   else "31-50" if r <= 50 else "51-100" if r <= 100 else "101-300")
            bands[key] += 1
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
    parser.add_argument("--top-documents", type=int, default=TOP_DOCUMENTS)
    parser.add_argument("--out", default="experiments/EXP-014/results.json")
    args = parser.parse_args()

    cases = [c for c in load_cases(Path(args.golden)) if c.expected_evidence]
    started = time.time()
    encoder = TransformerEncoder(max_seq=MAX_SEQ).load()
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)
    n = args.top_documents

    t0 = time.time()
    rows = load_chunk_rows(MODEL, CHUNK_SET, SNAP)
    load_seconds = time.time() - t0
    normalisation = chunk_vectors_are_normalised(rows)

    indexes, build_stats = {}, {}
    for name in REPRESENTATIONS:
        t0 = time.time()
        index = build(name, rows)
        seconds = time.time() - t0
        vectors = (sum(v.shape[0] for v in index.section_vectors.values())
                   if index.section_vectors else index.matrix.shape[0])
        indexes[name] = index
        build_stats[name] = {
            "description": REPRESENTATIONS[name],
            "documents": len(index.version_ids),
            "vectors_stored": int(vectors),
            "dimension": int(index.matrix.shape[1]),
            "build_seconds": round(seconds, 3),
            "storage_bytes": int(vectors * index.matrix.shape[1] * 4),
            "construction_stats": index.stats or {},
            "vector_hash_sample": dict(list(index.vector_hashes().items())[:3]),
        }

    def bm25(q, k, versions=None):
        return lexical_search(q, SNAP, k, version_ids=versions)

    def dense(q, k, versions=None):
        return dense_search(q, SNAP, MODEL, k, embedder=transformer, version_ids=versions)

    routing_rows: dict[str, list[dict]] = {}
    end_to_end: dict[str, dict] = {}
    lat: dict[str, list[float]] = {}
    doc_latency: dict[str, list[float]] = {}
    global_cases, oracle_cases = {}, {}
    chunk_router_rows: list[dict] = []
    watch_rows: dict[str, dict] = {}

    for case in cases:
        q = case.question
        expected = {ref.version_id for ref in case.expected_evidence}
        qvec = np.asarray(transformer.embed([q])[0], dtype=np.float32)

        g_lex = bm25(q, DOC_DEPTH)
        g_den = dense(q, DOC_DEPTH)

        t0 = time.time()
        g_hits = rrf_fuse([bm25(q, RRF_POOL), dense(q, RRF_POOL)], rrf_k=RRF_K, top_k=2 * RRF_POOL)
        lat.setdefault("GLOBAL_control", []).append((time.time() - t0) * 1000)
        global_cases[case.case_id] = score_case(case, g_hits, {})

        oracle_docs = sorted(expected)
        t0 = time.time()
        o_hits = rrf_fuse([bm25(q, RRF_POOL, oracle_docs), dense(q, RRF_POOL, oracle_docs)],
                          rrf_k=RRF_K, top_k=2 * RRF_POOL)
        lat.setdefault("ORACLE", []).append((time.time() - t0) * 1000)
        oracle_cases[case.case_id] = score_case(case, o_hits, {"oracle_documents": oracle_docs})

        # The EXP-013 baseline router: transformer chunk ranking collapsed to documents.
        chunk_ranking = router_max(g_den)
        chunk_order = [v for v, _ in chunk_ranking]
        chunk_router_rows.append({"case_id": case.case_id, **routing_metrics(chunk_order, expected)})

        configs: dict[str, list[str]] = {}
        for name, index in indexes.items():
            t0 = time.time()
            ranking = index.ranking(qvec)
            doc_latency.setdefault(name, []).append((time.time() - t0) * 1000)
            order = [v for v, _ in ranking]
            configs[name] = order
            # Primary fusion: representation + the transformer chunk-derived router.
            fused = rrf_document_lists([(name, [(v, 1) for v in order]),
                                        ("transformer_chunk", chunk_ranking)], k=DOCUMENT_RRF_K)
            configs[f"{name}+chunk"] = [e["version_id"] for e in fused]
            # Secondary: adding BM25 document ranking.
            with_bm25 = rrf_document_lists([(name, [(v, 1) for v in order]),
                                            ("transformer_chunk", chunk_ranking),
                                            ("bm25_chunk", router_max(g_lex))], k=DOCUMENT_RRF_K)
            configs[f"{name}+chunk+bm25"] = [e["version_id"] for e in with_bm25]

        for label, order in configs.items():
            routing_rows.setdefault(label, []).append(
                {"case_id": case.case_id, **routing_metrics(order, expected)})

        # End to end for standalone, primary fusion, and — since one of them routes
        # 19/20 — the secondary BM25 fusion too. A routing configuration that good
        # cannot be left without an end-to-end number just because it is secondary.
        for label in [*REPRESENTATIONS, *[f"{k}+chunk" for k in REPRESENTATIONS],
                      *[f"{k}+chunk+bm25" for k in REPRESENTATIONS]]:
            selected = configs[label][:n]
            t0 = time.time()
            hits = rrf_fuse([bm25(q, RRF_POOL, selected), dense(q, RRF_POOL, selected)],
                            rrf_k=RRF_K, top_k=2 * RRF_POOL)
            lat.setdefault(label, []).append((time.time() - t0) * 1000)
            counts = chunk_counts_for_documents(SNAP, CHUNK_SET, selected)
            end_to_end.setdefault(label, {})[case.case_id] = score_case(case, hits, {
                "selected_documents": selected,
                "all_expected_routed": expected <= set(selected),
                "local_candidate_chunks": counts["chunks"],
            })

        watch_rows[case.case_id] = {
            "expected_documents": sorted(expected),
            "multi_hop": len(expected) > 1,
            "chunk_router_ranks": routing_metrics(chunk_order, expected)["ranks"],
            "by_representation": {label: routing_metrics(order, expected)["ranks"]
                                  for label, order in configs.items()},
        }

    configurations = {"GLOBAL_control": {"description": "global BM25 + transformer RRF",
                                         "topology": "global",
                                         **summarise(global_cases, lat["GLOBAL_control"])}}
    for label, per_case in end_to_end.items():
        configurations[label] = {"description": f"{label} -> top {n} documents -> frozen Stage 2",
                                 "topology": "hierarchical", **summarise(per_case, lat[label])}
    oracle = {"description": "ORACLE / DIAGNOSTIC / NOT DEPLOYABLE — golden document, frozen Stage 2",
              "deployable": False, "uses_golden_document": True,
              **summarise(oracle_cases, lat["ORACLE"])}

    repro = {}
    for key, targets in REPRO.items():
        got = oracle if key == "ORACLE" else configurations[key]
        checks = {f: {"expected": e, "actual": got[f],
                      "match": (round(got[f], 3) == e if isinstance(e, float) else got[f] == e)}
                  for f, e in targets.items()}
        repro[key] = {"checks": checks, "reproduced": all(c["match"] for c in checks.values())}
    chunk_summary = summarise_routing(chunk_router_rows)
    repro["chunk_derived_router"] = {
        "checks": {"document_recall_at_5": {"expected": 0.875,
                                            "actual": chunk_summary["document_recall"]["5"],
                                            "match": chunk_summary["document_recall"]["5"] == 0.875},
                   "all_routed_at_5": {"expected": 17,
                                       "actual": chunk_summary["all_expected_routed"]["5"],
                                       "match": chunk_summary["all_expected_routed"]["5"] == 17}},
    }
    repro["chunk_derived_router"]["reproduced"] = all(
        c["match"] for c in repro["chunk_derived_router"]["checks"].values())

    routing_summary = {"chunk_derived_router": chunk_summary}
    for label, rows_ in routing_rows.items():
        routing_summary[label] = summarise_routing(rows_)

    comparisons = {}
    for label in end_to_end:
        comparisons[f"GLOBAL->{label}"] = pair("GLOBAL_control", configurations["GLOBAL_control"],
                                               label, configurations[label])
    comparisons["GLOBAL->ORACLE (diagnostic)"] = pair(
        "GLOBAL_control", configurations["GLOBAL_control"], "ORACLE", oracle)

    oracle_gap = {k: round(oracle["macro_span_recall"] - v["macro_span_recall"], 4)
                  for k, v in configurations.items()}

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                         stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        commit = None

    payload = {
        "experiment_id": "EXP-014",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "corpus_snapshot": SNAP, "chunk_set": CHUNK_SET,
        "transformer_fingerprint": encoder.model_version,
        "embedding_model": {"model_id": MODEL, **TRANSFORMER_CARD, "max_seq_length": MAX_SEQ},
        "document_representation_version": REPRESENTATION_VERSION,
        "representations": build_stats,
        "chunk_vector_normalisation": normalisation,
        "chunk_vector_load_seconds": round(load_seconds, 2),
        "query": "raw user question only",
        "similarity_metric": "cosine",
        "top_documents": n,
        "document_rrf_k": DOCUMENT_RRF_K, "passage_rrf_k": RRF_K,
        "candidate_pool": RRF_POOL, "top_k": TOP_K,
        "document_ranking_depth": DOC_DEPTH,
        "stage2": "FROZEN — identical to EXP-012/013",
        "bm25_config": {"k1": BM25_K1, "b": BM25_B, "ts_config": "simple",
                        "statistics": "full corpus — never recomputed inside routed documents"},
        "retrieval_config": {"reranker": None, "cross_encoder": None, "query_rewriting": False,
                             "enrichment": None, "metadata_filtering": False, "ann_index": False},
        "reproduction_gate": repro,
        "routing_quality": routing_summary,
        "routing_per_case": routing_rows,
        "configurations": configurations,
        "oracle_diagnostic": oracle,
        "paired_comparison": comparisons,
        "oracle_gap": oracle_gap,
        "case_watchlist": watch_rows,
        "reranker_decision_gate": {**{k: reranker_gate(v) for k, v in configurations.items()},
                                   "ORACLE": reranker_gate(oracle)},
        "document_retrieval_latency_ms": {k: round(statistics.mean(v), 3)
                                          for k, v in doc_latency.items()},
        "latency_ms": {k: round(statistics.mean(v), 1) for k, v in lat.items() if v},
        "query_embedding_cache": transformer.stats(),
        "runtime_seconds": round(time.time() - started, 1),
        "errors": [],
    }
    payload["config_hash"] = config_hash({
        "representations": sorted(REPRESENTATIONS), "version": REPRESENTATION_VERSION,
        "top_documents": n, "doc_rrf_k": DOCUMENT_RRF_K, "rrf_k": RRF_K, "pool": RRF_POOL,
        "model": MODEL, "bm25": payload["bm25_config"],
    })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    print("STANDALONE + FUSED DOCUMENT ROUTING (primary metric = all-routed@5)")
    print(f"{'configuration':26s} {'@1':>6s} {'@3':>6s} {'@5':>6s} {'@10':>6s}  "
          f"{'routed@5':>9s} {'routed@10':>10s}  missing@5")
    for label in ["chunk_derived_router", *REPRESENTATIONS,
                  *[f"{k}+chunk" for k in REPRESENTATIONS],
                  *[f"{k}+chunk+bm25" for k in REPRESENTATIONS]]:
        r = routing_summary[label]
        d = r["document_recall"]
        print(f"{label:26s} {d['1']:6.3f} {d['3']:6.3f} {d['5']:6.3f} {d['10']:6.3f}  "
              f"{r['all_expected_routed']['5']:5d}/{r['cases_total']:<3d} "
              f"{r['all_expected_routed']['10']:6d}/{r['cases_total']:<3d}  "
              f"{','.join(r['cases_missing_at_5']) or '-'}")
    print("\nEND-TO-END")
    print(f"{'cell':26s} {'macroR':>7s} {'full':>7s} {'spans':>8s} {'docR':>7s} {'MRR':>6s} "
          f"{'a@300':>6s} {'gap':>6s}")
    for key, r in list(configurations.items()) + [("ORACLE*", oracle)]:
        print(f"{key:26s} {r['macro_span_recall']:7.3f} {r['cases_fully_recalled']:3d}/{r['cases_total']:<3d} "
              f"{r['spans_found_at_10']:3d}/{r['spans_total']:<4d} {r['document_recall']:7.3f} "
              f"{r['mrr']:6.3f} {r['spans_absent_from_top']['300']:6d} "
              f"{oracle_gap.get(key, 0.0):6.3f}")
    print("\nreproduction gates:")
    for key, g in repro.items():
        print(f"  {key:24s} {'PASS' if g['reproduced'] else 'FAIL'}")
    print()
    for name, c in comparisons.items():
        if c["rescued"] or c["regressed"] or "ORACLE" in name:
            print(f"{name:34s} d={c['macro_recall_delta']:+.3f} rescued={c['rescued']} "
                  f"regressed={c['regressed']} net={c['net_rescued']:+d}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
