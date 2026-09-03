#!/usr/bin/env python3
"""EXP-008 — does chunk size interact with dense retrieval?

EXP-005 tested chunk size against BM25 and found no benefit. EXP-007 then observed
that dense reachability tracked chunk length. Those are different interactions, and
only a 2x2 can separate a main effect from an interaction:

    A  control chunks + BM25      (frozen baseline)
    B  bounded chunks + BM25      (EXP-005 intervention, reproduced)
    C  control chunks + dense     (EXP-007 configuration, reproduced)
    D  bounded chunks + dense     (the new cell)

The comparison of interest is C -> D against A -> B. Only the retrieval unit differs
between the columns; the embedding model, pooling, tokenization, metric and query
representation are byte-identical across C and D.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.db import connect
from rag_v1.embedders_pretrained import MODEL_CARD
from rag_v1.evals.io import load_cases
from rag_v1.ids import config_hash
from rag_v1.parsing import PARSER_VERSION
from rag_v1.retrieval import BM25_B, BM25_K1, dense_search, lexical_search, rrf_fuse
from rag_v1.types import EvidenceRef, SearchHit

CONTROL_SNAP = "snap_689e336380a054d8039dc35b2c09cd0a"
BOUNDED_SNAP = "snap_95215379baa1d8460315986d9745dc0c"
CONTROL_SET = "cs_v1_control"
BOUNDED_SET = "cs_2722bf8b72dcf3eb404336d7"
MODEL_ID = "emb_c11d8d9184d2ebc1ac60801a6452b884"
PROBE_DEPTHS = (10, 20, 50, 100, 300)
TOP_K = 10
RRF_POOL, RRF_K = 50, 60

CELLS = [
    ("A_control_bm25", "control chunks + BM25", CONTROL_SNAP, CONTROL_SET, "bm25"),
    ("B_bounded_bm25", "bounded chunks + BM25", BOUNDED_SNAP, BOUNDED_SET, "bm25"),
    ("C_control_dense", "control chunks + pretrained dense", CONTROL_SNAP, CONTROL_SET, "dense"),
    ("D_bounded_dense", "bounded chunks + pretrained dense", BOUNDED_SNAP, BOUNDED_SET, "dense"),
]


def overlaps(hit: SearchHit, ref: EvidenceRef) -> bool:
    return (
        hit.version_id == ref.version_id
        and hit.section_path == ref.section_path
        and hit.char_start < ref.char_end
        and hit.char_end > ref.char_start
    )


def probe(cases, snapshot: str, mode: str, deep: int) -> dict:
    per_case, latencies = {}, []
    for case in cases:
        started = time.time()
        hits = (lexical_search(case.question, snapshot, deep) if mode == "bm25"
                else dense_search(case.question, snapshot, MODEL_ID, deep))
        latencies.append((time.time() - started) * 1000)
        spans = []
        for ref in case.expected_evidence:
            hit = next((h for h in hits if overlaps(h, ref)), None)
            doc_rank = next((h.rank for h in hits if h.version_id == ref.version_id), None)
            spans.append({
                "section_path": ref.section_path,
                "span": [ref.char_start, ref.char_end],
                "rank": hit.rank if hit else None,
                "doc_rank": doc_rank,
                "chunk_id": hit.chunk_id if hit else None,
                "chunk_len": (hit.char_end - hit.char_start) if hit else None,
                "similarity": round(hit.score, 6) if hit else None,
                "within": {str(d): (hit is not None and hit.rank <= d) for d in PROBE_DEPTHS},
                "doc_within_10": doc_rank is not None and doc_rank <= TOP_K,
            })
        found = sum(1 for s in spans if s["within"]["10"])
        per_case[case.case_id] = {
            "case_id": case.case_id, "category": case.category, "question": case.question,
            "spans": spans,
            "recall": found / len(spans) if spans else 1.0,
            "fully_recalled": bool(spans) and found == len(spans),
            "doc_recall": sum(1 for s in spans if s["doc_within_10"]) / len(spans) if spans else 1.0,
        }

    all_spans = [s for c in per_case.values() for s in c["spans"]]
    found_ranks = [s["rank"] for s in all_spans if s["rank"] is not None]
    recalls = [c["recall"] for c in per_case.values()]
    docs = [c["doc_recall"] for c in per_case.values()]

    # The quantity EXP-007 flagged: is reachability related to chunk length?
    reachable = [s["chunk_len"] for s in all_spans if s["within"]["300"] and s["chunk_len"]]
    return {
        "macro_span_recall": round(sum(recalls) / len(recalls), 4),
        "cases_fully_recalled": sum(1 for c in per_case.values() if c["fully_recalled"]),
        "cases_total": len(per_case),
        "spans_found_at_10": sum(1 for s in all_spans if s["within"]["10"]),
        "spans_total": len(all_spans),
        "document_recall": round(sum(docs) / len(docs), 4),
        "mrr": round(sum(1 / s["rank"] for s in all_spans if s["rank"]) / len(all_spans), 4),
        "mean_evidence_rank_when_found": round(statistics.mean(found_ranks), 2) if found_ranks else None,
        "median_evidence_rank_when_found": statistics.median(found_ranks) if found_ranks else None,
        "spans_absent_from_top": {str(d): sum(1 for s in all_spans if not s["within"][str(d)]) for d in PROBE_DEPTHS},
        "median_chunk_len_reachable_at_300": statistics.median(reachable) if reachable else None,
        "mean_query_ms": round(statistics.mean(latencies), 1),
        "cases": per_case,
    }


def movement(before: int | None, after: int | None) -> str:
    if before is None and after is None:
        return "still_unreachable"
    if before is None:
        return "strong_improvement" if after <= TOP_K else "newly_reachable_outside_k"
    if after is None:
        return "lost_entirely"
    if before > TOP_K >= after:
        return "strong_improvement" if (before - after >= 10 or after <= TOP_K // 2) else "boundary_improvement"
    if after > TOP_K >= before:
        return "strong_regression" if (after - before >= 10 or before <= TOP_K // 2) else "boundary_regression"
    if after < before:
        return "improved_no_cross"
    if after > before:
        return "worsened_no_cross"
    return "unchanged"


def pair(a_label: str, a: dict, b_label: str, b: dict, anchors: dict) -> dict:
    buckets = {"rescued": [], "regressed": [], "unchanged_good": [], "unchanged_bad": [], "partial_change": []}
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
            anchor = anchors.get((cid, idx), {})
            rows.append({
                "case_id": cid, "span_index": idx, "category": before["category"],
                "section_path": sb["section_path"],
                "control_chunk_id": anchor.get("control_chunk_id"),
                "bounded_chunk_id": anchor.get("bounded_chunk_id"),
                "control_chunk_len": anchor.get("control_chunk_len"),
                "bounded_chunk_len": anchor.get("bounded_chunk_len"),
                "rank_before": sb["rank"], "rank_after": sa["rank"],
                "similarity_before": sb["similarity"], "similarity_after": sa["similarity"],
                "doc_rank_before": sb["doc_rank"], "doc_rank_after": sa["doc_rank"],
                "movement": mv,
            })
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
    return {
        "from": a_label, "to": b_label, **buckets,
        "net_rescued": len(buckets["rescued"]) - len(buckets["regressed"]),
        "macro_recall_delta": round(b["macro_span_recall"] - a["macro_span_recall"], 4),
        "quadrant": quadrant, "span_movement_counts": moves, "span_rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", default="evals/golden/v1.jsonl")
    parser.add_argument("--deep", type=int, default=300)
    parser.add_argument("--out", default="experiments/EXP-008/results.json")
    parser.add_argument("--with-rrf", action="store_true", help="also run exploratory EXP-008E")
    args = parser.parse_args()

    cases = [c for c in load_cases(Path(args.golden)) if c.expected_evidence]
    started = time.time()

    # Evidence-anchor chunk identity in both chunkings, for the rank-movement table.
    anchors: dict[tuple[str, int], dict] = {}
    with connect() as conn, conn.cursor() as cur:
        for case in cases:
            for idx, ref in enumerate(case.expected_evidence):
                entry = {}
                for label, chunk_set in (("control", CONTROL_SET), ("bounded", BOUNDED_SET)):
                    cur.execute(
                        """
                        SELECT chunk_id, char_end-char_start FROM chunk
                        WHERE chunk_set_id=%s AND version_id=%s AND section_path=%s
                          AND char_start<%s AND char_end>%s
                        ORDER BY char_end-char_start LIMIT 1
                        """,
                        (chunk_set, ref.version_id, ref.section_path, ref.char_end, ref.char_start),
                    )
                    row = cur.fetchone()
                    entry[f"{label}_chunk_id"] = row[0] if row else None
                    entry[f"{label}_chunk_len"] = row[1] if row else None
                anchors[(case.case_id, idx)] = entry

    results = {}
    for key, desc, snapshot, chunk_set, mode in CELLS:
        results[key] = {"description": desc, "snapshot_id": snapshot,
                        "chunk_set_id": chunk_set, "retriever": mode,
                        **probe(cases, snapshot, mode, args.deep)}

    # Chunk length of the answer-bearing unit, split by dense reachability.
    for key in ("C_control_dense", "D_bounded_dense"):
        chunk_key = "control_chunk_len" if key.startswith("C") else "bounded_chunk_len"
        reach, unreach = [], []
        for cid, c in results[key]["cases"].items():
            for idx, s in enumerate(c["spans"]):
                length = anchors[(cid, idx)][chunk_key]
                (reach if s["within"]["300"] else unreach).append(length)
        results[key]["evidence_chunk_length_by_reachability"] = {
            "median_reachable": statistics.median(reach) if reach else None,
            "median_unreachable": statistics.median(unreach) if unreach else None,
            "n_reachable": len(reach), "n_unreachable": len(unreach),
            "unreachable_lengths": sorted(unreach),
        }

    comparisons = {
        "A->B chunk size under BM25": pair("A_control_bm25", results["A_control_bm25"],
                                           "B_bounded_bm25", results["B_bounded_bm25"], anchors),
        "C->D chunk size under dense": pair("C_control_dense", results["C_control_dense"],
                                            "D_bounded_dense", results["D_bounded_dense"], anchors),
    }

    interaction = {
        "note": "A main effect would move both rows equally; an interaction moves them differently.",
        "table": {
            "BM25": {
                "control": results["A_control_bm25"]["macro_span_recall"],
                "bounded": results["B_bounded_bm25"]["macro_span_recall"],
                "delta": round(results["B_bounded_bm25"]["macro_span_recall"] - results["A_control_bm25"]["macro_span_recall"], 4),
                "fully_recalled": [results["A_control_bm25"]["cases_fully_recalled"], results["B_bounded_bm25"]["cases_fully_recalled"]],
                "absent_at_300": [results["A_control_bm25"]["spans_absent_from_top"]["300"], results["B_bounded_bm25"]["spans_absent_from_top"]["300"]],
                "mrr": [results["A_control_bm25"]["mrr"], results["B_bounded_bm25"]["mrr"]],
                "net_rescued": comparisons["A->B chunk size under BM25"]["net_rescued"],
            },
            "dense": {
                "control": results["C_control_dense"]["macro_span_recall"],
                "bounded": results["D_bounded_dense"]["macro_span_recall"],
                "delta": round(results["D_bounded_dense"]["macro_span_recall"] - results["C_control_dense"]["macro_span_recall"], 4),
                "fully_recalled": [results["C_control_dense"]["cases_fully_recalled"], results["D_bounded_dense"]["cases_fully_recalled"]],
                "absent_at_300": [results["C_control_dense"]["spans_absent_from_top"]["300"], results["D_bounded_dense"]["spans_absent_from_top"]["300"]],
                "mrr": [results["C_control_dense"]["mrr"], results["D_bounded_dense"]["mrr"]],
                "net_rescued": comparisons["C->D chunk size under dense"]["net_rescued"],
            },
        },
    }
    interaction["interaction_delta"] = round(
        interaction["table"]["dense"]["delta"] - interaction["table"]["BM25"]["delta"], 4
    )

    if args.with_rrf:
        def fused(q, k):
            lex = lexical_search(q, CONTROL_SNAP, RRF_POOL)
            den = dense_search(q, BOUNDED_SNAP, MODEL_ID, RRF_POOL)
            return rrf_fuse([lex, den], rrf_k=RRF_K, top_k=k)

        per_case, latencies = {}, []
        for case in cases:
            t = time.time()
            hits = fused(case.question, 2 * RRF_POOL)
            latencies.append((time.time() - t) * 1000)
            spans = []
            for ref in case.expected_evidence:
                hit = next((h for h in hits if overlaps(h, ref)), None)
                doc_rank = next((h.rank for h in hits if h.version_id == ref.version_id), None)
                spans.append({"section_path": ref.section_path, "rank": hit.rank if hit else None,
                              "doc_rank": doc_rank, "chunk_len": (hit.char_end - hit.char_start) if hit else None,
                              "similarity": round(hit.score, 6) if hit else None,
                              "within": {str(d): (hit is not None and hit.rank <= d) for d in PROBE_DEPTHS},
                              "doc_within_10": doc_rank is not None and doc_rank <= TOP_K})
            found = sum(1 for s in spans if s["within"]["10"])
            per_case[case.case_id] = {"case_id": case.case_id, "category": case.category,
                                      "question": case.question, "spans": spans,
                                      "recall": found / len(spans) if spans else 1.0,
                                      "fully_recalled": bool(spans) and found == len(spans),
                                      "doc_recall": sum(1 for s in spans if s["doc_within_10"]) / len(spans) if spans else 1.0}
        all_spans = [s for c in per_case.values() for s in c["spans"]]
        recalls = [c["recall"] for c in per_case.values()]
        results["E_bm25control_plus_boundeddense_rrf"] = {
            "description": "EXPLORATORY — BM25 on control chunks fused with dense on bounded chunks",
            "exploratory": True,
            "rrf_config": {"pool": RRF_POOL, "rrf_k": RRF_K, "top_k": TOP_K,
                           "preregistered_from": "EXP-007", "tuned": False},
            "macro_span_recall": round(sum(recalls) / len(recalls), 4),
            "cases_fully_recalled": sum(1 for c in per_case.values() if c["fully_recalled"]),
            "cases_total": len(per_case),
            "spans_found_at_10": sum(1 for s in all_spans if s["within"]["10"]),
            "spans_total": len(all_spans),
            "document_recall": round(sum(c["doc_recall"] for c in per_case.values()) / len(per_case), 4),
            "mrr": round(sum(1 / s["rank"] for s in all_spans if s["rank"]) / len(all_spans), 4),
            "spans_absent_from_top": {str(d): sum(1 for s in all_spans if not s["within"][str(d)]) for d in PROBE_DEPTHS},
            "mean_query_ms": round(statistics.mean(latencies), 1),
            "cases": per_case,
        }
        comparisons["A->E fusion vs BM25 control"] = pair(
            "A_control_bm25", results["A_control_bm25"],
            "E_bm25control_plus_boundeddense_rrf", results["E_bm25control_plus_boundeddense_rrf"], anchors)

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        commit = None

    payload = {
        "experiment_id": "EXP-008",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "corpus_snapshots": {"control": CONTROL_SNAP, "bounded": BOUNDED_SNAP},
        "chunk_sets": {"control": CONTROL_SET, "bounded": BOUNDED_SET},
        "embedding_model": {"model_id": MODEL_ID, **MODEL_CARD},
        "embedding_fingerprint": MODEL_CARD["revision"],
        "distance_metric": "cosine (exact, no ANN index)",
        "parser_version": PARSER_VERSION,
        "top_k": TOP_K,
        "probe_depths": list(PROBE_DEPTHS),
        "bm25_config": {"k1": BM25_K1, "b": BM25_B, "ts_config": "simple"},
        "retrieval_config": {"reranker": None, "query_rewriting": False, "query_expansion": False,
                             "stemming": False, "enrichment": None, "pooling": MODEL_CARD["pooling"]},
        "configurations": results,
        "paired_comparison": comparisons,
        "interaction_analysis": interaction,
        "evidence_anchors": {f"{k[0]}#{k[1]}": v for k, v in anchors.items()},
        "runtime_seconds": round(time.time() - started, 1),
        "errors": [],
    }
    payload["config_hash"] = config_hash({
        "cells": [(c[0], c[2], c[3], c[4]) for c in CELLS],
        "model": MODEL_ID, "top_k": TOP_K, "bm25": payload["bm25_config"],
    })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    print(f"{'cell':40s} {'macroR':>7s} {'full':>7s} {'spans':>8s} {'docR':>7s} {'MRR':>6s} "
          f"{'a@10':>5s} {'a@50':>5s} {'a@300':>6s} {'ms':>7s}")
    for key, r in results.items():
        a = r["spans_absent_from_top"]
        print(f"{key:40s} {r['macro_span_recall']:7.3f} {r['cases_fully_recalled']:3d}/{r['cases_total']:<3d} "
              f"{r['spans_found_at_10']:3d}/{r['spans_total']:<4d} {r['document_recall']:7.3f} {r['mrr']:6.3f} "
              f"{a['10']:5d} {a['50']:5d} {a['300']:6d} {r['mean_query_ms']:7.1f}")
    print()
    for name, c in comparisons.items():
        print(f"{name:32s} d={c['macro_recall_delta']:+.3f} rescued={c['rescued']} "
              f"regressed={c['regressed']} partial={c['partial_change']} net={c['net_rescued']:+d}")
    print(f"\ninteraction: BM25 delta={interaction['table']['BM25']['delta']:+.3f}  "
          f"dense delta={interaction['table']['dense']['delta']:+.3f}  "
          f"interaction={interaction['interaction_delta']:+.3f}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
