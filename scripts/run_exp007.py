#!/usr/bin/env python3
"""EXP-007 — pretrained semantic retrieval vs the frozen BM25 baseline.

Three configurations on the frozen control chunks, unenriched:

    EXP-007A_bm25_control     reproduce the frozen lexical baseline (fidelity gate)
    EXP-007B_pretrained_dense exact cosine search over pretrained embeddings
    EXP-007C_bm25_dense_rrf   RRF over the two, preregistered pool=50 / rrf_k=60

Everything is derived from one deep probe per (config, question) so the metrics at
k=10/20/50/100/300 are mutually consistent.
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
from rag_v1.parsing import PARSER_VERSION
from rag_v1.retrieval import BM25_B, BM25_K1, dense_search, lexical_search, query_terms, rrf_fuse
from rag_v1.types import EvidenceRef, SearchHit

SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"
CHUNK_SET = "cs_v1_control"
MODEL_ID = "emb_c11d8d9184d2ebc1ac60801a6452b884"
PROBE_DEPTHS = (10, 20, 50, 100, 300)

# Preregistered before any EXP-007C result was observed. Not tuned.
RRF_POOL = 50
RRF_K = 60
TOP_K = 10


def overlaps(hit: SearchHit, ref: EvidenceRef) -> bool:
    return (
        hit.version_id == ref.version_id
        and hit.section_path == ref.section_path
        and hit.char_start < ref.char_end
        and hit.char_end > ref.char_start
    )


def rank_of(hits: list[SearchHit], ref: EvidenceRef) -> tuple[int | None, SearchHit | None]:
    for hit in hits:
        if overlaps(hit, ref):
            return hit.rank, hit
    return None, None


def lexical_overlap(question: str, text: str) -> dict:
    terms = query_terms(question)
    low = (text or "").lower()
    present = [t for t in terms if t.lower() in low]
    return {
        "query_terms": len(terms),
        "terms_present_in_chunk": len(present),
        "overlap_fraction": round(len(present) / len(terms), 3) if terms else None,
        "present": present,
    }


def summarize(per_case: dict, latencies: list[float]) -> dict:
    spans = [s for c in per_case.values() for s in c["spans"]]
    found = [s["rank"] for s in spans if s["rank"] is not None]
    recalls = [c["recall"] for c in per_case.values()]
    docs = [c["doc_recall"] for c in per_case.values()]
    by_cat: dict[str, list[float]] = {}
    by_provider: dict[str, list[int]] = {}
    for c in per_case.values():
        by_cat.setdefault(c["category"], []).append(c["recall"])
    for c in per_case.values():
        prov = "anthropic" if c["case_id"].startswith("AN") else "openai"
        by_provider.setdefault(prov, []).append(c["recall"])
    return {
        "macro_span_recall": round(sum(recalls) / len(recalls), 4),
        "cases_fully_recalled": sum(1 for c in per_case.values() if c["fully_recalled"]),
        "cases_total": len(per_case),
        "spans_found_at_10": sum(1 for s in spans if s["within"]["10"]),
        "spans_total": len(spans),
        "document_recall": round(sum(docs) / len(docs), 4),
        "mrr": round(sum(1 / s["rank"] for s in spans if s["rank"]) / len(spans), 4),
        "mean_evidence_rank_when_found": round(statistics.mean(found), 2) if found else None,
        "median_evidence_rank_when_found": statistics.median(found) if found else None,
        "spans_absent_from_top": {str(d): sum(1 for s in spans if not s["within"][str(d)]) for d in PROBE_DEPTHS},
        "recall_by_category": {k: round(sum(v) / len(v), 4) for k, v in sorted(by_cat.items())},
        "recall_by_provider": {k: round(sum(v) / len(v), 4) for k, v in sorted(by_provider.items())},
        "mean_query_ms": round(statistics.mean(latencies), 1),
        "total_retrieval_seconds": round(sum(latencies) / 1000, 2),
    }


def run_config(cases, retrieve, deep: int) -> dict:
    per_case, latencies = {}, []
    with connect() as conn, conn.cursor() as cur:
        for case in cases:
            started = time.time()
            hits = retrieve(case.question, deep)
            latencies.append((time.time() - started) * 1000)
            spans = []
            for ref in case.expected_evidence:
                rank, hit = rank_of(hits, ref)
                doc_rank = next((h.rank for h in hits if h.version_id == ref.version_id), None)
                body = ""
                if hit:
                    cur.execute("SELECT text FROM chunk WHERE chunk_id=%s", (hit.chunk_id,))
                    row = cur.fetchone()
                    body = row[0] if row else ""
                spans.append({
                    "section_path": ref.section_path,
                    "span": [ref.char_start, ref.char_end],
                    "rank": rank,
                    "doc_rank": doc_rank,
                    "score": hit.score if hit else None,
                    "chunk_id": hit.chunk_id if hit else None,
                    "chunk_len": (hit.char_end - hit.char_start) if hit else None,
                    "lexical_overlap": lexical_overlap(case.question, body) if hit else None,
                    "within": {str(d): (rank is not None and rank <= d) for d in PROBE_DEPTHS},
                    "doc_within_10": doc_rank is not None and doc_rank <= 10,
                })
            found10 = sum(1 for s in spans if s["within"]["10"])
            per_case[case.case_id] = {
                "case_id": case.case_id,
                "category": case.category,
                "question": case.question,
                "spans": spans,
                "recall": found10 / len(spans) if spans else 1.0,
                "fully_recalled": bool(spans) and found10 == len(spans),
                "doc_recall": sum(1 for s in spans if s["doc_within_10"]) / len(spans) if spans else 1.0,
                "top_hits": [
                    {"rank": h.rank, "chunk_id": h.chunk_id, "score": round(h.score, 4),
                     "section_path": h.section_path}
                    for h in hits[:5]
                ],
            }
    return {"cases": per_case, **summarize(per_case, latencies)}


def classify(before: int | None, after: int | None, k: int = TOP_K) -> str:
    if before is None and after is None:
        return "both_absent"
    if before is None:
        return "newly_reachable" if after > k else ("strong_rescue" if after <= k else "rescue")
    if after is None:
        return "lost_entirely"
    if before > k >= after:
        return "strong_rescue" if (before - after >= 10 or after <= k // 2) else "boundary_rescue"
    if after > k >= before:
        return "strong_regression" if (after - before >= 10 or before <= k // 2) else "boundary_regression"
    if after < before:
        return "improved_no_cross"
    if after > before:
        return "worsened_no_cross"
    return "unchanged"


def pair(a_name: str, a: dict, b_name: str, b: dict) -> dict:
    buckets = {"rescued": [], "regressed": [], "unchanged_good": [], "unchanged_bad": [], "partial_change": []}
    details, quadrant = [], {"both_correct": [], "only_a": [], "only_b": [], "neither": []}
    movements: dict[str, int] = {}
    for cid, before in a["cases"].items():
        after = b["cases"][cid]
        if before["fully_recalled"] and after["fully_recalled"]:
            quadrant["both_correct"].append(cid)
        elif before["fully_recalled"]:
            quadrant["only_a"].append(cid)
        elif after["fully_recalled"]:
            quadrant["only_b"].append(cid)
        else:
            quadrant["neither"].append(cid)

        span_moves = []
        for sb, sa in zip(before["spans"], after["spans"], strict=True):
            move = classify(sb["rank"], sa["rank"])
            movements[move] = movements.get(move, 0) + 1
            span_moves.append({
                "section_path": sb["section_path"],
                "rank_before": sb["rank"], "rank_after": sa["rank"],
                "doc_rank_before": sb["doc_rank"], "doc_rank_after": sa["doc_rank"],
                "score_before": sb["score"], "score_after": sa["score"],
                "lexical_overlap_before": sb["lexical_overlap"],
                "lexical_overlap_after": sa["lexical_overlap"],
                "movement": move,
                "crossed_k10": (sb["rank"] is None or sb["rank"] > TOP_K) != (sa["rank"] is None or sa["rank"] > TOP_K),
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
        details.append({"case_id": cid, "category": before["category"],
                        "recall_before": before["recall"], "recall_after": after["recall"],
                        "spans": span_moves})
    return {
        "from": a_name, "to": b_name, **buckets,
        "net_rescued": len(buckets["rescued"]) - len(buckets["regressed"]),
        "macro_recall_delta": round(b["macro_span_recall"] - a["macro_span_recall"], 4),
        "quadrant": quadrant,
        "span_movement_counts": movements,
        "details": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", default="evals/golden/v1.jsonl")
    parser.add_argument("--deep", type=int, default=300)
    parser.add_argument("--out", default="experiments/EXP-007/results.json")
    args = parser.parse_args()

    cases = [c for c in load_cases(Path(args.golden)) if c.expected_evidence]
    started = time.time()

    def bm25(q, k):
        return lexical_search(q, SNAPSHOT, k)

    def dense(q, k):
        return dense_search(q, SNAPSHOT, MODEL_ID, k)

    def rrf(q, k):
        lex = lexical_search(q, SNAPSHOT, RRF_POOL)
        den = dense_search(q, SNAPSHOT, MODEL_ID, RRF_POOL)
        return rrf_fuse([lex, den], rrf_k=RRF_K, top_k=k)

    results = {
        "EXP-007A_bm25_control": run_config(cases, bm25, args.deep),
        "EXP-007B_pretrained_dense": run_config(cases, dense, args.deep),
        # RRF can only rank what the two pools contain: 2 x 50 candidates.
        "EXP-007C_bm25_dense_rrf": run_config(cases, rrf, 2 * RRF_POOL),
    }

    comparisons = {
        "BM25 -> dense": pair("EXP-007A_bm25_control", results["EXP-007A_bm25_control"],
                              "EXP-007B_pretrained_dense", results["EXP-007B_pretrained_dense"]),
        "BM25 -> RRF": pair("EXP-007A_bm25_control", results["EXP-007A_bm25_control"],
                            "EXP-007C_bm25_dense_rrf", results["EXP-007C_bm25_dense_rrf"]),
        "dense -> RRF": pair("EXP-007B_pretrained_dense", results["EXP-007B_pretrained_dense"],
                             "EXP-007C_bm25_dense_rrf", results["EXP-007C_bm25_dense_rrf"]),
    }

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                         stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        commit = None

    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT manifest_hash, chunking_config_hash, parser_version FROM corpus_snapshot WHERE snapshot_id=%s", (SNAPSHOT,))
        manifest_hash, chunking_hash, parser_v = cur.fetchone()
        cur.execute("SELECT chunker_name, chunker_version, config_hash FROM chunk_set WHERE chunk_set_id=%s", (CHUNK_SET,))
        chunker_name, chunker_version, chunker_cfg = cur.fetchone()

    from rag_v1.ids import config_hash

    payload = {
        "experiment_id": "EXP-007",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "corpus_snapshot_id": SNAPSHOT,
        "corpus_manifest_hash": manifest_hash,
        "chunker": {"name": chunker_name, "version": chunker_version,
                    "config_hash": chunker_cfg, "chunk_set_id": CHUNK_SET,
                    "enrichment": None},
        "chunk_config_hash": chunking_hash,
        "parser_version": parser_v or PARSER_VERSION,
        "embedding_model": {"model_id": MODEL_ID, **MODEL_CARD},
        "retrieval_config": {
            "top_k": TOP_K, "probe_depth": args.deep,
            "dense_search": "exact cosine (pgvector <=>, no ANN index)",
            "reranker": None, "query_rewriting": False, "query_expansion": False,
            "stemming": False, "synonyms": False,
        },
        "bm25_config": {"k1": BM25_K1, "b": BM25_B, "ts_config": "simple",
                        "tie_break": "round(score,9) desc, chunk_id asc"},
        "rrf_config": {"preregistered": True, "candidate_pool_per_retriever": RRF_POOL,
                       "rrf_k": RRF_K, "final_top_k": TOP_K, "tuned": False},
        "configurations": results,
        "paired_results": comparisons,
        "probe_depth_results": {k: v["spans_absent_from_top"] for k, v in results.items()},
        "runtime_seconds": round(time.time() - started, 1),
        "errors": [],
    }
    payload["config_hash"] = config_hash({
        "snapshot": SNAPSHOT, "chunk_set": CHUNK_SET, "model": MODEL_ID,
        "bm25": payload["bm25_config"], "rrf": payload["rrf_config"], "top_k": TOP_K,
    })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    print(f"{'config':28s} {'macroR':>7s} {'full':>7s} {'spans':>8s} {'docR':>7s} {'MRR':>6s} "
          f"{'a@10':>5s} {'a@20':>5s} {'a@50':>5s} {'a@100':>6s} {'a@300':>6s} {'ms':>7s}")
    for name, r in results.items():
        a = r["spans_absent_from_top"]
        print(f"{name:28s} {r['macro_span_recall']:7.3f} {r['cases_fully_recalled']:3d}/{r['cases_total']:<3d} "
              f"{r['spans_found_at_10']:3d}/{r['spans_total']:<4d} {r['document_recall']:7.3f} {r['mrr']:6.3f} "
              f"{a['10']:5d} {a['20']:5d} {a['50']:5d} {a['100']:6d} {a['300']:6d} {r['mean_query_ms']:7.1f}")
    print()
    for name, c in comparisons.items():
        print(f"{name:16s} d={c['macro_recall_delta']:+.3f} rescued={c['rescued']} "
              f"regressed={c['regressed']} partial={c['partial_change']} net={c['net_rescued']:+d}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
