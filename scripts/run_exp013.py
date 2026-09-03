#!/usr/bin/env python3
"""EXP-013 — does aggregating more chunk evidence route documents better?

EXP-012 isolated the bottleneck: given the correct document the same retrievers
reach 0.950 / 19-of-20, but the router puts every required document in the top 5
for only 17 of 20 questions. Its rule keeps a document's single best chunk and
discards the rest.

    A_MAX          best chunk only            (EXP-012 control)
    B_RANK_SUM     reciprocal-rank support
    C_TOPK_VOTE    breadth of support
    D_MAX_SUPPORT  both, fused in rank domain

Stage 2 is frozen: same raw query, same full-corpus BM25 and transformer scores
restricted to the routed documents, same passage RRF, same top 10. Only the
document ranking changes.
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
from rag_v1.hierarchical import chunk_counts_for_documents
from rag_v1.ids import config_hash
from rag_v1.parsing import PARSER_VERSION
from rag_v1.query_cache import CachedQueryEmbedder
from rag_v1.retrieval import BM25_B, BM25_K1, dense_search, lexical_search, rrf_fuse
from rag_v1.routers import (
    DOCUMENT_RRF_K,
    ROUTER_PARAMETERS,
    ROUTER_VERSION,
    route,
)
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
ROUTERS = ("A_MAX", "B_RANK_SUM", "C_TOPK_VOTE", "D_MAX_SUPPORT")

REPRO = {
    "GLOBAL_control": {"macro_span_recall": 0.775, "cases_fully_recalled": 15,
                       "spans_found_at_10": 17},
    "A_MAX": {"macro_span_recall": 0.725, "cases_fully_recalled": 14,
              "spans_found_at_10": 16},
    "ORACLE": {"macro_span_recall": 0.95, "cases_fully_recalled": 19,
               "spans_found_at_10": 21},
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


def score_case(case, hits: list[SearchHit], extra: dict) -> dict:
    spans = []
    for ref in case.expected_evidence:
        hit = next((h for h in hits if overlaps(h, ref)), None)
        doc_rank = next((h.rank for h in hits if h.version_id == ref.version_id), None)
        spans.append({
            "section_path": ref.section_path, "span": [ref.char_start, ref.char_end],
            "rank": hit.rank if hit else None, "doc_rank": doc_rank,
            "chunk_id": hit.chunk_id if hit else None,
            "within": {str(d): (hit is not None and hit.rank <= d) for d in PROBE_DEPTHS},
            "doc_within_10": doc_rank is not None and doc_rank <= TOP_K,
        })
    found = sum(1 for s in spans if s["within"]["10"])
    return {"case_id": case.case_id, "category": case.category, "question": case.question,
            "spans": spans,
            "recall": found / len(spans) if spans else 1.0,
            "fully_recalled": bool(spans) and found == len(spans),
            "doc_recall": sum(1 for s in spans if s["doc_within_10"]) / len(spans) if spans else 1.0,
            **extra}


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


def recall_at(order: list[str], expected: set[str], depths=(1, 3, 5, 10)) -> dict:
    return {str(d): round(len(expected & set(order[:d])) / len(expected), 4) if expected else 1.0
            for d in depths}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", default="evals/golden/v1.jsonl")
    parser.add_argument("--top-documents", type=int, default=TOP_DOCUMENTS)
    parser.add_argument("--deep", type=int, default=300)
    parser.add_argument("--out", default="experiments/EXP-013/results.json")
    parser.add_argument("--label", default="primary")
    args = parser.parse_args()

    cases = [c for c in load_cases(Path(args.golden)) if c.expected_evidence]
    started = time.time()
    encoder = TransformerEncoder(max_seq=MAX_SEQ).load()
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)
    n = args.top_documents

    def bm25(q, k, versions=None):
        return lexical_search(q, SNAP, k, version_ids=versions)

    def dense(q, k, versions=None):
        return dense_search(q, SNAP, MODEL, k, embedder=transformer, version_ids=versions)

    global_cases, oracle_cases = {}, {}
    router_cases = {r: {} for r in ROUTERS}
    lat = {"GLOBAL": [], "ORACLE": [], **{r: [] for r in ROUTERS}}
    routing_rows = {r: [] for r in ROUTERS}
    pool_sizes = {r: [] for r in ROUTERS}
    support_diag = {}

    for case in cases:
        q = case.question
        expected = {ref.version_id for ref in case.expected_evidence}

        g_lex = bm25(q, DOC_RANKING_DEPTH)
        g_den = dense(q, DOC_RANKING_DEPTH)

        t0 = time.time()
        g_hits = rrf_fuse([bm25(q, RRF_POOL), dense(q, RRF_POOL)], rrf_k=RRF_K, top_k=2 * RRF_POOL)
        lat["GLOBAL"].append((time.time() - t0) * 1000)
        global_cases[case.case_id] = score_case(case, g_hits, {})

        t0 = time.time()
        oracle_docs = sorted(expected)
        o_hits = rrf_fuse([bm25(q, RRF_POOL, oracle_docs), dense(q, RRF_POOL, oracle_docs)],
                          rrf_k=RRF_K, top_k=2 * RRF_POOL)
        lat["ORACLE"].append((time.time() - t0) * 1000)
        oracle_cases[case.case_id] = score_case(case, o_hits, {"oracle_documents": oracle_docs})

        # Support evidence for every expected document, independent of router.
        support_diag[case.case_id] = {
            "expected_documents": sorted(expected),
            "multi_hop": len(expected) > 1,
            "per_document": {
                doc: {
                    "best_bm25_chunk_rank": next((h.rank for h in g_lex if h.version_id == doc), None),
                    "best_transformer_chunk_rank": next((h.rank for h in g_den if h.version_id == doc), None),
                    "bm25_chunks_in_top": {str(d): sum(1 for h in g_lex if h.version_id == doc and h.rank <= d)
                                           for d in (10, 30, 50, 100)},
                    "transformer_chunks_in_top": {str(d): sum(1 for h in g_den if h.version_id == doc and h.rank <= d)
                                                  for d in (10, 30, 50, 100)},
                } for doc in sorted(expected)
            },
        }

        for name in ROUTERS:
            t0 = time.time()
            fused, per_retriever = route(name, g_lex, g_den)
            order = [e["version_id"] for e in fused]
            selected = order[:n]
            routing_ms = (time.time() - t0) * 1000

            t0 = time.time()
            hits = rrf_fuse([bm25(q, RRF_POOL, selected), dense(q, RRF_POOL, selected)],
                            rrf_k=RRF_K, top_k=2 * RRF_POOL)
            lat[name].append(routing_ms + (time.time() - t0) * 1000)

            counts = chunk_counts_for_documents(SNAP, CHUNK_SET, selected)
            pool_sizes[name].append(counts["chunks"])

            comp = {}
            for label, ranking in per_retriever.items():
                comp[label] = {
                    "recall": recall_at([v for v, _ in ranking], expected),
                    "all_routed": expected <= {v for v, _ in ranking[:n]},
                }
            routing_rows[name].append({
                "case_id": case.case_id,
                "expected_documents": sorted(expected),
                "multi_hop": len(expected) > 1,
                "fused_document_rank": {d: next((e["document_rank"] for e in fused
                                                 if e["version_id"] == d), None)
                                        for d in sorted(expected)},
                "all_expected_routed": expected <= set(selected),
                "partially_routed": bool(expected & set(selected)) and not expected <= set(selected),
                "selected_documents": selected,
                "recall_fused": recall_at(order, expected),
                "per_retriever": comp,
                "local_candidate_chunks": counts["chunks"],
            })
            router_cases[name][case.case_id] = score_case(case, hits, {
                "selected_documents": selected,
                "all_expected_routed": expected <= set(selected),
                "local_candidate_chunks": counts["chunks"],
            })

    configurations = {"GLOBAL_control": {"description": "global BM25 + transformer RRF (no routing)",
                                         "topology": "global", **summarise(global_cases, lat["GLOBAL"])}}
    for name in ROUTERS:
        configurations[name] = {
            "description": f"router {name} -> top {n} documents -> frozen Stage 2",
            "topology": "hierarchical", "router": name,
            **summarise(router_cases[name], lat[name]),
        }
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

    # Routing quality — the primary metric of EXP-013.
    routing_summary = {}
    for name in ROUTERS:
        rows = routing_rows[name]
        all_routed = [r["case_id"] for r in rows if r["all_expected_routed"]]
        missing = [r["case_id"] for r in rows if not r["all_expected_routed"]]
        partial = [r["case_id"] for r in rows if r["partially_routed"]]
        comp_labels = sorted(rows[0]["per_retriever"])
        component_all_routed = {
            label: sum(1 for r in rows if r["per_retriever"][label]["all_routed"])
            for label in comp_labels
        }
        best_component = max(component_all_routed.values())
        routing_summary[name] = {
            "mean_document_recall": {d: round(statistics.mean([r["recall_fused"][d] for r in rows]), 4)
                                     for d in ("1", "3", "5", "10")},
            "cases_all_expected_routed": len(all_routed),
            "cases_total": len(rows),
            "cases_missing_a_document": missing,
            "cases_partially_routed": partial,
            "stage1_ceiling": round(len(all_routed) / len(rows), 4),
            "component_all_routed": component_all_routed,
            "best_component_all_routed": best_component,
            "fused_all_routed": len(all_routed),
            "fusion_bonus_cases": len(all_routed) - best_component,
            "mean_local_pool": round(statistics.mean(pool_sizes[name]), 1),
            "mean_local_pool_fraction": round(statistics.mean(pool_sizes[name]) / GLOBAL_CHUNKS, 5),
            "multi_hop_cases": [r["case_id"] for r in rows if r["multi_hop"]],
            "multi_hop_all_routed": [r["case_id"] for r in rows if r["multi_hop"] and r["all_expected_routed"]],
        }

    comparisons = {}
    for name in ROUTERS:
        comparisons[f"GLOBAL->{name}"] = pair("GLOBAL_control", configurations["GLOBAL_control"],
                                              name, configurations[name])
        if name != "A_MAX":
            comparisons[f"A_MAX->{name}"] = pair("A_MAX", configurations["A_MAX"],
                                                 name, configurations[name])
    comparisons["GLOBAL->ORACLE (diagnostic)"] = pair(
        "GLOBAL_control", configurations["GLOBAL_control"], "ORACLE", oracle)

    oracle_gap = {name: round(oracle["macro_span_recall"] - cfg["macro_span_recall"], 4)
                  for name, cfg in configurations.items()}

    watch = {}
    for cid in ("AN-001", "AN-012", "OA-004", "AN-003"):
        watch[cid] = {
            "expected_documents": support_diag[cid]["expected_documents"],
            "support": support_diag[cid]["per_document"],
            "by_router": {
                name: {
                    "fused_document_rank": next(r["fused_document_rank"] for r in routing_rows[name]
                                                if r["case_id"] == cid),
                    "all_expected_routed": next(r["all_expected_routed"] for r in routing_rows[name]
                                                if r["case_id"] == cid),
                    "evidence_ranks": [s["rank"] for s in router_cases[name][cid]["spans"]],
                } for name in ROUTERS
            },
            "global_evidence_ranks": [s["rank"] for s in global_cases[cid]["spans"]],
            "oracle_evidence_ranks": [s["rank"] for s in oracle_cases[cid]["spans"]],
        }

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                         stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        commit = None

    payload = {
        "experiment_id": "EXP-013",
        "label": args.label,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "corpus_snapshot": SNAP, "chunk_set": CHUNK_SET,
        "query": "raw user question only",
        "router_version": ROUTER_VERSION,
        "router_parameters": ROUTER_PARAMETERS,
        "routers": list(ROUTERS),
        "top_documents": n,
        "document_ranking_depth": DOC_RANKING_DEPTH,
        "document_rrf_k": DOCUMENT_RRF_K,
        "passage_rrf_k": RRF_K, "candidate_pool": RRF_POOL, "top_k": TOP_K,
        "stage2": "FROZEN — identical to EXP-012: full-corpus BM25 + transformer cosine "
                  "restricted to routed documents, passage RRF, top 10",
        "bm25_config": {"k1": BM25_K1, "b": BM25_B, "ts_config": "simple",
                        "statistics": "full corpus — never recomputed inside routed documents"},
        "transformer_fingerprint": encoder.model_version,
        "embedding_model": {"model_id": MODEL, **TRANSFORMER_CARD, "max_seq_length": MAX_SEQ},
        "parser_version": PARSER_VERSION,
        "probe_depths": list(PROBE_DEPTHS),
        "retrieval_config": {"reranker": None, "cross_encoder": None, "query_rewriting": False,
                             "enrichment": None, "metadata_filtering": False, "ann_index": False},
        "reproduction_gate": repro,
        "configurations": configurations,
        "oracle_diagnostic": oracle,
        "routing_quality": routing_summary,
        "routing_per_case": routing_rows,
        "support_diagnostics": support_diag,
        "paired_comparison": comparisons,
        "oracle_gap": oracle_gap,
        "case_watchlist": watch,
        "reranker_decision_gate": {**{k: reranker_gate(v) for k, v in configurations.items()},
                                   "ORACLE": reranker_gate(oracle)},
        "latency_ms": {k: round(statistics.mean(v), 1) for k, v in lat.items() if v},
        "query_embedding_cache": transformer.stats(),
        "runtime_seconds": round(time.time() - started, 1),
        "errors": [],
    }
    payload["config_hash"] = config_hash({
        "routers": list(ROUTERS), "params": ROUTER_PARAMETERS, "top_documents": n,
        "depth": DOC_RANKING_DEPTH, "rrf_k": RRF_K, "pool": RRF_POOL, "model": MODEL,
        "bm25": payload["bm25_config"],
    })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    print("ROUTING QUALITY (primary metric)")
    print(f"{'router':16s} {'@1':>6s} {'@3':>6s} {'@5':>6s} {'@10':>6s} {'all-routed':>11s} "
          f"{'ceiling':>8s} {'bonus':>6s} {'pool':>7s}")
    for name in ROUTERS:
        r = routing_summary[name]
        m = r["mean_document_recall"]
        print(f"{name:16s} {m['1']:6.3f} {m['3']:6.3f} {m['5']:6.3f} {m['10']:6.3f} "
              f"{r['cases_all_expected_routed']:6d}/{r['cases_total']:<4d} {r['stage1_ceiling']:8.3f} "
              f"{r['fusion_bonus_cases']:+6d} {r['mean_local_pool']:7.0f}")
    print("\nEND-TO-END")
    print(f"{'cell':16s} {'macroR':>7s} {'full':>7s} {'spans':>8s} {'docR':>7s} {'MRR':>6s} "
          f"{'a@10':>5s} {'a@30':>5s} {'a@300':>6s} {'gap':>6s}")
    for key, r in list(configurations.items()) + [("ORACLE*", oracle)]:
        a = r["spans_absent_from_top"]
        gap = oracle_gap.get(key, 0.0)
        print(f"{key:16s} {r['macro_span_recall']:7.3f} {r['cases_fully_recalled']:3d}/{r['cases_total']:<3d} "
              f"{r['spans_found_at_10']:3d}/{r['spans_total']:<4d} {r['document_recall']:7.3f} "
              f"{r['mrr']:6.3f} {a['10']:5d} {a['30']:5d} {a['300']:6d} {gap:6.3f}")
    print("\nreproduction gates:")
    for key, g in repro.items():
        print(f"  {key:16s} {'PASS' if g['reproduced'] else 'FAIL'}")
        if not g["reproduced"]:
            for f, c in g["checks"].items():
                if not c["match"]:
                    print(f"      {f}: expected {c['expected']}, got {c['actual']}")
    print()
    for name, c in comparisons.items():
        print(f"{name:28s} d={c['macro_recall_delta']:+.3f} rescued={c['rescued']} "
              f"regressed={c['regressed']} net={c['net_rescued']:+d}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
