#!/usr/bin/env python3
"""EXP-005 paired analysis: what moved, per question, and why.

Aggregate recall cannot distinguish "the chunker helped" from "the chunker helped
one question and hurt another". This script recomputes, for every configuration
and every expected evidence span:

* the rank at which the span first becomes retrievable (searched to ``--deep``,
  well past k, so a span that merely ranked too low is distinguishable from one
  that was never retrievable at all);
* the length of the chunk that carries the span, which is the quantity EXP-005
  is intervening on;
* the rank of the correct *document*, so document-level recall can be separated
  from span-level recall.

It then pairs each configuration against the V1 control per question and labels
every case rescued / regressed / unchanged, attaching the rank and length change
that explains it.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.db import connect
from rag_v1.evals.io import load_cases
from rag_v1.parsing import PARSER_VERSION
from rag_v1.retrieval import BM25_B, BM25_K1, lexical_search
from rag_v1.types import EvidenceRef, SearchHit

CONFIGS = [
    ("EXP-000_control", "snap_689e336380a054d8039dc35b2c09cd0a", "chunker_v1_control"),
    ("EXP-005A_bounded", "snap_95215379baa1d8460315986d9745dc0c", "chunker_v2_bounded"),
    ("EXP-005B_technical", "snap_766fa9940ec8b881f4e111076b13bf82", "chunker_v3_technical"),
]


def provenance() -> dict:
    """Everything needed to re-run this exact comparison later."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        dirty = bool(
            subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
        )
    except Exception:  # noqa: BLE001 - provenance is best-effort
        commit, dirty = None, None

    chunk_sets = {}
    with connect() as conn, conn.cursor() as cur:
        for _, snapshot_id, _ in CONFIGS:
            cur.execute(
                """
                SELECT cs.chunk_set_id, cs.chunker_name, cs.chunker_version, cs.config_hash,
                       cs.config, cs.parser_version, s.chunking_config_hash
                FROM corpus_snapshot s
                JOIN chunk_set cs ON cs.chunk_set_id = s.chunk_set_id
                WHERE s.snapshot_id = %s
                """,
                (snapshot_id,),
            )
            row = cur.fetchone()
            cur.execute("SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (row[0],))
            chunk_sets[snapshot_id] = {
                "chunk_set_id": row[0],
                "chunker_name": row[1],
                "chunker_version": row[2],
                "chunker_config_hash": row[3],
                "chunker_config": row[4],
                "parser_version": row[5],
                "snapshot_chunking_config_hash": row[6],
                "chunks": cur.fetchone()[0],
            }
    return {
        "git_commit": commit,
        "working_tree_dirty": dirty,
        "parser_version": PARSER_VERSION,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "chunk_sets": chunk_sets,
    }


def overlaps(hit: SearchHit, ref: EvidenceRef) -> bool:
    """The exact condition rag_v1.evals.retrieval_eval scores on."""
    return (
        hit.version_id == ref.version_id
        and hit.section_path == ref.section_path
        and hit.char_start < ref.char_end
        and hit.char_end > ref.char_start
    )


def probe(question: str, refs: list[EvidenceRef], snapshot_id: str, deep: int, k: int) -> dict:
    hits = lexical_search(question, snapshot_id, deep)
    spans = []
    for ref in refs:
        span_rank = None
        chunk_len = None
        chunk_id = None
        for hit in hits:
            if overlaps(hit, ref):
                span_rank = hit.rank
                chunk_len = hit.char_end - hit.char_start
                chunk_id = hit.chunk_id
                break
        doc_rank = next((h.rank for h in hits if h.version_id == ref.version_id), None)
        spans.append(
            {
                "section_path": ref.section_path,
                "span": [ref.char_start, ref.char_end],
                "span_len": ref.char_end - ref.char_start,
                "rank": span_rank,
                "within_k": span_rank is not None and span_rank <= k,
                "chunk_len": chunk_len,
                "chunk_id": chunk_id,
                "evidence_share_of_chunk": round((ref.char_end - ref.char_start) / chunk_len, 4)
                if chunk_len
                else None,
                "doc_rank": doc_rank,
                "doc_within_k": doc_rank is not None and doc_rank <= k,
            }
        )
    found = sum(1 for s in spans if s["within_k"])
    return {
        "spans": spans,
        "recall": found / len(spans) if spans else 1.0,
        "fully_recalled": found == len(spans) and bool(spans),
        "doc_recall": sum(1 for s in spans if s["doc_within_k"]) / len(spans) if spans else 1.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", default="evals/golden/v1.jsonl")
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--deep", type=int, default=300)
    parser.add_argument("--out", default="experiments/EXP-005/paired-analysis.json")
    args = parser.parse_args()

    cases = [c for c in load_cases(Path(args.golden)) if c.expected_evidence]
    started = time.time()

    results: dict[str, dict] = {}
    for label, snapshot_id, chunker in CONFIGS:
        per_case = {}
        for case in cases:
            per_case[case.case_id] = {
                "category": case.category,
                "question": case.question,
                **probe(case.question, case.expected_evidence, snapshot_id, args.deep, args.k),
            }
        recalls = [c["recall"] for c in per_case.values()]
        doc_recalls = [c["doc_recall"] for c in per_case.values()]
        by_category: dict[str, list[float]] = {}
        for c in per_case.values():
            by_category.setdefault(c["category"], []).append(c["recall"])
        results[label] = {
            "snapshot_id": snapshot_id,
            "chunker": chunker,
            "k": args.k,
            "macro_span_recall": round(sum(recalls) / len(recalls), 4),
            "cases_fully_recalled": sum(1 for c in per_case.values() if c["fully_recalled"]),
            "cases_total": len(per_case),
            "spans_found": sum(sum(1 for s in c["spans"] if s["within_k"]) for c in per_case.values()),
            "spans_total": sum(len(c["spans"]) for c in per_case.values()),
            "document_recall": round(sum(doc_recalls) / len(doc_recalls), 4),
            "recall_by_category": {
                cat: round(sum(v) / len(v), 4) for cat, v in sorted(by_category.items())
            },
            "cases": per_case,
        }

    control = results["EXP-000_control"]["cases"]
    comparisons = {}
    for label in ("EXP-005A_bounded", "EXP-005B_technical"):
        new = results[label]["cases"]
        buckets: dict[str, list[dict]] = {
            "rescued": [], "regressed": [], "unchanged_good": [], "unchanged_bad": [], "partial_change": []
        }
        for case_id, before in control.items():
            after = new[case_id]
            detail = {
                "case_id": case_id,
                "category": before["category"],
                "recall_before": before["recall"],
                "recall_after": after["recall"],
                "doc_recall_before": before["doc_recall"],
                "doc_recall_after": after["doc_recall"],
                "spans": [
                    {
                        "section_path": b["section_path"],
                        "span_len": b["span_len"],
                        "rank_before": b["rank"],
                        "rank_after": a["rank"],
                        "chunk_len_before": b["chunk_len"],
                        "chunk_len_after": a["chunk_len"],
                        "evidence_share_before": b["evidence_share_of_chunk"],
                        "evidence_share_after": a["evidence_share_of_chunk"],
                        "doc_rank_before": b["doc_rank"],
                        "doc_rank_after": a["doc_rank"],
                    }
                    for b, a in zip(before["spans"], after["spans"], strict=True)
                ],
            }
            if before["fully_recalled"] and not after["fully_recalled"]:
                buckets["regressed"].append(detail)
            elif not before["fully_recalled"] and after["fully_recalled"]:
                buckets["rescued"].append(detail)
            elif before["fully_recalled"]:
                buckets["unchanged_good"].append(detail)
            elif before["recall"] != after["recall"]:
                buckets["partial_change"].append(detail)
            else:
                buckets["unchanged_bad"].append(detail)
        comparisons[f"EXP-000_control -> {label}"] = {
            **{k: [d["case_id"] for d in v] for k, v in buckets.items()},
            "net_rescued": len(buckets["rescued"]) - len(buckets["regressed"]),
            "details": buckets,
        }

    payload = {
        "experiment": "EXP-005",
        "provenance": provenance(),
        "retrieval_config": {
            "retriever": "lexical_bm25",
            "bm25_k1": BM25_K1,
            "bm25_b": BM25_B,
            "top_k": args.k,
            "deep_probe_depth": args.deep,
            "golden_set": args.golden,
            "reranker": None,
            "query_rewriting": False,
        },
        "runtime_seconds": round(time.time() - started, 1),
        "errors": [],
        "configurations": results,
        "paired_comparisons": comparisons,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    print(f"{'configuration':22s} {'macroR':>7s} {'full':>7s} {'spans':>8s} {'docR':>7s}")
    for label, r in results.items():
        print(
            f"{label:22s} {r['macro_span_recall']:7.3f} {r['cases_fully_recalled']:3d}/{r['cases_total']:<3d} "
            f"{r['spans_found']:3d}/{r['spans_total']:<4d} {r['document_recall']:7.3f}"
        )
    print()
    for name, comp in comparisons.items():
        print(f"{name}: rescued={comp['rescued']} regressed={comp['regressed']} "
              f"partial={comp['partial_change']} net={comp['net_rescued']:+d}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
