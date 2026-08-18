#!/usr/bin/env python3
"""EXP-006 — controlled 2x2 ablation of contextual enrichment vs chunk granularity.

EXP-005 falsified the chunk-size hypothesis but left a confound: its V3 chunker
both changed boundaries *and* prepended structural context to the indexed text, so
its gain could not be attributed. This decomposes that into a clean 2x2:

    A  control chunking, no enrichment      (must reproduce EXP-000)
    B  control chunking, + enrichment       (A -> B isolates enrichment)
    C  bounded chunking, no enrichment      (must reproduce EXP-005A)
    D  bounded chunking, + enrichment       (C -> D isolates enrichment again)

B and D are row-for-row copies of A and C with only ``search_text`` changed, so a
difference between them cannot be a chunking difference.

Everything is derived from a single deep probe per (config, question) so that
metrics at k=10/50/100/300 are consistent with one another.
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
from rag_v1.enrichment import STRUCTURAL_V1
from rag_v1.evals.io import load_cases
from rag_v1.parsing import PARSER_VERSION
from rag_v1.retrieval import (
    _LEXICAL_SQL,
    BM25_B,
    BM25_K1,
    lexical_search,
    query_terms,
    snapshot_chunk_set,
)
from rag_v1.types import EvidenceRef, SearchHit

CONFIGS = [
    ("EXP-006A", "snap_689e336380a054d8039dc35b2c09cd0a", "control chunking, no enrichment"),
    ("EXP-006B", "snap_635fe0ba0f0b5a5c8b6744571b43b438", "control chunking, structural enrichment"),
    ("EXP-006C", "snap_95215379baa1d8460315986d9745dc0c", "bounded chunking, no enrichment"),
    ("EXP-006D", "snap_d0dabae0a857ea27fd96bbdf8b989f1b", "bounded chunking, structural enrichment"),
]

# Exploratory only (EXP-006 section 20): which header fields matter. These were
# selected on the development set after the core 2x2 had already run, and are
# labelled exploratory everywhere they are reported.
EXPLORATORY_CONFIGS = [
    ("E1_section_only", "snap_0dbc9037dcf48aea6f95a70d47131934", "control chunking, section path only"),
    ("E2_document_section", "snap_e99ae08c8a3cdb848e916d1c9afdd71e", "control chunking, document title + section path"),
]

PROBE_DEPTHS = (10, 50, 100, 300)
GENERIC_HEADINGS = {
    "preamble", "overview", "introduction", "guide", "documentation", "information",
    "home", "getting started", "about", "next steps", "summary", "notes", "reference",
}


def overlaps(hit: SearchHit, ref: EvidenceRef) -> bool:
    """Exactly the condition rag_v1.evals.retrieval_eval scores on."""
    return (
        hit.version_id == ref.version_id
        and hit.section_path == ref.section_path
        and hit.char_start < ref.char_end
        and hit.char_end > ref.char_start
    )


def git_commit() -> tuple[str | None, bool | None]:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                         stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())
        return commit, dirty
    except Exception:  # noqa: BLE001 - provenance is best-effort
        return None, None


def query_plan_summary(snapshot_id: str, question: str) -> dict:
    """Confirm the GIN index is still chosen, per the EXP-005 planner regression."""
    params = {
        "terms": query_terms(question), "snapshot_id": snapshot_id,
        "chunk_set_id": snapshot_chunk_set(snapshot_id),
        "k": 10, "k1": BM25_K1, "b": BM25_B,
    }
    with connect() as conn, conn.cursor() as cur:
        cur.execute("EXPLAIN (ANALYZE, TIMING OFF) " + _LEXICAL_SQL, params)
        rows = [r[0] for r in cur.fetchall()]
    exec_line = next((r for r in rows if r.strip().startswith("Execution Time")), "")
    return {
        "gin_index_scans": sum(1 for r in rows if "idx_chunk_search_vector" in r),
        "uses_gin_index": any("idx_chunk_search_vector" in r for r in rows),
        "seq_scan_on_chunk": any("Seq Scan on chunk" in r for r in rows),
        "execution_time_ms": float(exec_line.split(":")[1].strip().split()[0]) if exec_line else None,
        "plan_lines": len(rows),
    }


def chunk_context(cur, chunk_set_id: str, chunk_id: str) -> dict:
    cur.execute(
        "SELECT text, search_text, context_header FROM chunk WHERE chunk_set_id=%s AND chunk_id=%s",
        (chunk_set_id, chunk_id),
    )
    row = cur.fetchone()
    if not row:
        return {}
    text, search_text, header = row
    return {"text": text, "search_text": search_text or text, "context_header": header or ""}


def term_df(cur, snapshot_id: str, chunk_set_id: str, term: str) -> int:
    cur.execute(
        """
        SELECT count(*) FROM chunk c
        JOIN corpus_snapshot_version sv ON sv.version_id=c.version_id
        WHERE sv.snapshot_id=%s AND c.chunk_set_id=%s
          AND c.search_vector @@ phraseto_tsquery('simple', %s)
        """,
        (snapshot_id, chunk_set_id, term),
    )
    return cur.fetchone()[0]


def probe_config(cases, snapshot_id: str, deep: int) -> dict:
    """One deep retrieval per question; all @k metrics derive from it."""
    chunk_set_id = snapshot_chunk_set(snapshot_id)
    per_case: dict[str, dict] = {}
    started = time.time()

    with connect() as conn, conn.cursor() as cur:
        for case in cases:
            q_started = time.time()
            hits = lexical_search(case.question, snapshot_id, deep)
            elapsed_ms = (time.time() - q_started) * 1000

            spans = []
            for ref in case.expected_evidence:
                rank = next((h.rank for h in hits if overlaps(h, ref)), None)
                doc_rank = next((h.rank for h in hits if h.version_id == ref.version_id), None)
                hit = next((h for h in hits if overlaps(h, ref)), None)
                ctx = chunk_context(cur, chunk_set_id, hit.chunk_id) if hit else {}
                spans.append({
                    "section_path": ref.section_path,
                    "span": [ref.char_start, ref.char_end],
                    "span_len": ref.char_end - ref.char_start,
                    "rank": rank,
                    "doc_rank": doc_rank,
                    "chunk_id": hit.chunk_id if hit else None,
                    "chunk_len": (hit.char_end - hit.char_start) if hit else None,
                    "search_text_len": len(ctx.get("search_text", "")) or None,
                    "context_header": ctx.get("context_header", ""),
                    "bm25_score": hit.score if hit else None,
                    "within": {str(d): (rank is not None and rank <= d) for d in PROBE_DEPTHS},
                    "doc_within_10": doc_rank is not None and doc_rank <= 10,
                })
            found10 = sum(1 for s in spans if s["within"]["10"])
            per_case[case.case_id] = {
                "category": case.category,
                "question": case.question,
                "spans": spans,
                "recall": found10 / len(spans) if spans else 1.0,
                "fully_recalled": bool(spans) and found10 == len(spans),
                "doc_recall": sum(1 for s in spans if s["doc_within_10"]) / len(spans) if spans else 1.0,
                "query_ms": round(elapsed_ms, 1),
            }

    all_spans = [s for c in per_case.values() for s in c["spans"]]
    found_ranks = [s["rank"] for s in all_spans if s["rank"] is not None]
    recalls = [c["recall"] for c in per_case.values()]
    doc_recalls = [c["doc_recall"] for c in per_case.values()]
    by_cat: dict[str, list[float]] = {}
    for c in per_case.values():
        by_cat.setdefault(c["category"], []).append(c["recall"])

    return {
        "snapshot_id": snapshot_id,
        "chunk_set_id": chunk_set_id,
        "top_k": 10,
        "probe_depth": deep,
        "macro_span_recall": round(sum(recalls) / len(recalls), 4),
        "cases_fully_recalled": sum(1 for c in per_case.values() if c["fully_recalled"]),
        "cases_total": len(per_case),
        "spans_retrieved_at_10": sum(1 for s in all_spans if s["within"]["10"]),
        "spans_total": len(all_spans),
        "document_recall": round(sum(doc_recalls) / len(doc_recalls), 4),
        "mean_evidence_rank_when_found": round(statistics.mean(found_ranks), 2) if found_ranks else None,
        "median_evidence_rank_when_found": statistics.median(found_ranks) if found_ranks else None,
        "mrr": round(sum(1 / s["rank"] for s in all_spans if s["rank"]) / len(all_spans), 4),
        "spans_absent_from_top": {
            str(d): sum(1 for s in all_spans if not s["within"][str(d)]) for d in PROBE_DEPTHS
        },
        "recall_by_category": {k: round(sum(v) / len(v), 4) for k, v in sorted(by_cat.items())},
        "retrieval_runtime_seconds": round(time.time() - started, 2),
        "mean_query_ms": round(statistics.mean([c["query_ms"] for c in per_case.values()]), 1),
        "cases": per_case,
    }


def classify_move(before: int | None, after: int | None, k: int = 10) -> str:
    """Distinguish a convincing movement from one that merely grazed the cutoff."""
    if before is None and after is None:
        return "unchanged_absent"
    if before is None:
        return "newly_retrievable"
    if after is None:
        return "lost_entirely"
    crossed_in = before > k >= after
    crossed_out = after > k >= before
    delta = before - after
    if crossed_in:
        return "strong_rescue" if (delta >= 10 or after <= k // 2) else "boundary_rescue"
    if crossed_out:
        return "strong_regression" if (-delta >= 10 or before <= k // 2) else "boundary_regression"
    if delta > 0:
        return "improved_no_cross"
    if delta < 0:
        return "worsened_no_cross"
    return "unchanged"


def enrichment_overlap(cur, snapshot_id: str, chunk_set_id: str, question: str, span: dict) -> dict:
    """Which query terms the body already had, and which enrichment introduced."""
    terms = query_terms(question)
    header = (span.get("context_header") or "").lower()
    chunk_text = ""
    if span.get("chunk_id"):
        ctx = chunk_context(cur, chunk_set_id, span["chunk_id"])
        chunk_text = (ctx.get("text") or "").lower()

    in_body, added_by_header, absent = [], [], []
    for term in terms:
        low = term.lower()
        if low in chunk_text:
            in_body.append(term)
        elif low in header:
            added_by_header.append(term)
        else:
            absent.append(term)

    dfs = {t: term_df(cur, snapshot_id, chunk_set_id, t) for t in terms}
    discriminative = sorted(dfs, key=lambda t: dfs[t])[:4]
    return {
        "query_terms": terms,
        "terms_in_body": in_body,
        "terms_added_by_enrichment": added_by_header,
        "terms_absent_everywhere": absent,
        "term_document_frequency": dfs,
        "most_discriminative_terms": discriminative,
        "enrichment_added_a_discriminative_term": any(t in added_by_header for t in discriminative),
    }


def section_path_quality(section_path: list[str]) -> dict:
    parts = [p.strip() for p in section_path if p.strip()]
    generic = [p for p in parts if p.lower() in GENERIC_HEADINGS]
    return {
        "section_path": parts,
        "depth": len(parts),
        "generic_components": generic,
        "all_generic": bool(parts) and len(generic) == len(parts),
        "verdict": "generic" if parts and len(generic) == len(parts) else "technical",
    }


def pair(results: dict, a: str, b: str) -> dict:
    before_cases, after_cases = results[a]["cases"], results[b]["cases"]
    buckets: dict[str, list[str]] = {
        "rescued": [], "regressed": [], "unchanged_good": [], "unchanged_bad": [], "partial_change": []
    }
    details = []
    for case_id, before in before_cases.items():
        after = after_cases[case_id]
        span_moves = []
        for sb, sa in zip(before["spans"], after["spans"], strict=True):
            span_moves.append({
                "section_path": sb["section_path"],
                "rank_before": sb["rank"], "rank_after": sa["rank"],
                "doc_rank_before": sb["doc_rank"], "doc_rank_after": sa["doc_rank"],
                "chunk_len_before": sb["chunk_len"], "chunk_len_after": sa["chunk_len"],
                "search_len_before": sb["search_text_len"], "search_len_after": sa["search_text_len"],
                "bm25_before": sb["bm25_score"], "bm25_after": sa["bm25_score"],
                "bm25_delta": round(sa["bm25_score"] - sb["bm25_score"], 4)
                if sb["bm25_score"] is not None and sa["bm25_score"] is not None else None,
                "context_header_after": sa["context_header"],
                "movement": classify_move(sb["rank"], sa["rank"]),
                "crossed_k10": (sb["rank"] is None or sb["rank"] > 10) != (sa["rank"] is None or sa["rank"] > 10),
                "section_path_quality": section_path_quality(sb["section_path"]),
            })
        if before["fully_recalled"] and not after["fully_recalled"]:
            buckets["regressed"].append(case_id)
        elif not before["fully_recalled"] and after["fully_recalled"]:
            buckets["rescued"].append(case_id)
        elif before["fully_recalled"]:
            buckets["unchanged_good"].append(case_id)
        elif before["recall"] != after["recall"]:
            buckets["partial_change"].append(case_id)
        else:
            buckets["unchanged_bad"].append(case_id)
        details.append({
            "case_id": case_id, "category": before["category"],
            "recall_before": before["recall"], "recall_after": after["recall"],
            "spans": span_moves,
        })

    movement_counts: dict[str, int] = {}
    for d in details:
        for s in d["spans"]:
            movement_counts[s["movement"]] = movement_counts.get(s["movement"], 0) + 1

    return {
        "from": a, "to": b,
        **buckets,
        "net_rescued": len(buckets["rescued"]) - len(buckets["regressed"]),
        "macro_recall_delta": round(results[b]["macro_span_recall"] - results[a]["macro_span_recall"], 4),
        "span_movement_counts": movement_counts,
        "details": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", default="evals/golden/v1.jsonl")
    parser.add_argument("--deep", type=int, default=300)
    parser.add_argument("--out", default="experiments/EXP-006/results.json")
    args = parser.parse_args()

    cases = [c for c in load_cases(Path(args.golden)) if c.expected_evidence]
    started = time.time()
    commit, dirty = git_commit()

    results, plans = {}, {}
    for label, snapshot_id, _desc in CONFIGS:
        results[label] = probe_config(cases, snapshot_id, args.deep)
        plans[label] = query_plan_summary(snapshot_id, cases[0].question)

    exploratory = {}
    for label, snapshot_id, _desc in EXPLORATORY_CONFIGS:
        results[label] = probe_config(cases, snapshot_id, args.deep)
        exploratory[label] = pair(results, "EXP-006A", label)

    comparisons = {
        "A->B enrichment on control chunking": pair(results, "EXP-006A", "EXP-006B"),
        "A->C chunk size without enrichment": pair(results, "EXP-006A", "EXP-006C"),
        "C->D enrichment on bounded chunking": pair(results, "EXP-006C", "EXP-006D"),
        "B->D chunk size with enrichment": pair(results, "EXP-006B", "EXP-006D"),
    }

    # Vocabulary-overlap and section-path diagnostics per span, per config.
    diagnostics = {}
    with connect() as conn, conn.cursor() as cur:
        for label, snapshot_id, _ in CONFIGS:
            chunk_set_id = results[label]["chunk_set_id"]
            per_case = {}
            for case_id, case in results[label]["cases"].items():
                per_case[case_id] = [
                    {
                        **enrichment_overlap(cur, snapshot_id, chunk_set_id, case["question"], span),
                        "rank": span["rank"],
                        "section_path_quality": section_path_quality(span["section_path"]),
                    }
                    for span in case["spans"]
                ]
            diagnostics[label] = per_case

    payload = {
        "experiment_id": "EXP-006",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "working_tree_dirty": dirty,
        "parser_version": PARSER_VERSION,
        "enrichment_config": STRUCTURAL_V1.as_dict(),
        "enrichment_config_hash": STRUCTURAL_V1.config_hash,
        "retrieval_config": {
            "retriever": "lexical_bm25", "top_k": 10, "probe_depth": args.deep,
            "reranker": None, "query_rewriting": False, "query_expansion": False,
            "dense": False, "rrf": False,
        },
        "bm25_config": {"k1": BM25_K1, "b": BM25_B, "ts_config": "simple",
                        "tie_break": "round(score,9) desc, chunk_id asc"},
        "top_k": 10,
        "configurations": {
            label: {"description": desc, **results[label], "query_plan_summary": plans[label]}
            for label, _snap, desc in CONFIGS
        },
        "paired_results": comparisons,
        "exploratory_field_ablation": {
            "note": (
                "Selected on the development set after the core 2x2 completed. "
                "Not a held-out result; reported to explain the df-inflation mechanism."
            ),
            "configurations": {
                label: {"description": desc, **{k: v for k, v in results[label].items() if k != "cases"}}
                for label, _s, desc in EXPLORATORY_CONFIGS
            },
            "paired_vs_A": exploratory,
        },
        "probe_depth_results": {
            label: results[label]["spans_absent_from_top"] for label, _s, _d in CONFIGS
        },
        "vocabulary_diagnostics": diagnostics,
        "runtime_seconds": round(time.time() - started, 1),
        "errors": [],
    }
    from rag_v1.ids import config_hash as _ch
    payload["config_hash"] = _ch({
        "configs": [c[1] for c in CONFIGS],
        "enrichment": STRUCTURAL_V1.as_dict(),
        "bm25": payload["bm25_config"],
        "top_k": 10,
        "golden": args.golden,
    })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    print(f"{'config':10s} {'macroR':>7s} {'full':>7s} {'spans':>8s} {'docR':>7s} {'MRR':>6s} "
          f"{'absent@10':>9s} {'@50':>4s} {'@100':>5s} {'@300':>5s} {'ms':>7s}")
    for label, _s, _d in CONFIGS:
        r = results[label]
        a = r["spans_absent_from_top"]
        print(f"{label:10s} {r['macro_span_recall']:7.3f} {r['cases_fully_recalled']:3d}/{r['cases_total']:<3d} "
              f"{r['spans_retrieved_at_10']:3d}/{r['spans_total']:<4d} {r['document_recall']:7.3f} "
              f"{r['mrr']:6.3f} {a['10']:9d} {a['50']:4d} {a['100']:5d} {a['300']:5d} {r['mean_query_ms']:7.1f}")
    print()
    print()
    for label, _s, desc in EXPLORATORY_CONFIGS:
        r = results[label]
        print(f"[exploratory] {label:22s} macro={r['macro_span_recall']:.3f} "
              f"full={r['cases_fully_recalled']}/{r['cases_total']}  ({desc})")
    print()
    for name, comp in comparisons.items():
        print(f"{name:38s} rescued={comp['rescued']} regressed={comp['regressed']} "
              f"partial={comp['partial_change']} net={comp['net_rescued']:+d} "
              f"dMacro={comp['macro_recall_delta']:+.3f}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
