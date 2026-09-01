#!/usr/bin/env python3
"""EXP-018 one-shot: frozen SYSTEM-D vs frozen SYSTEM-E on V2-DEVSET-001 n=50.

Does not load gold150-v1 holdout.json. Does not load gold150-v1/development.
Does not retune E. Does not mutate SYSTEM-D freeze files or cs_v1_control.
Does not overwrite EXP-018-development-results.json or SYSTEM-E-WITHIN-DOC.json.
"""

from __future__ import annotations

import hashlib
import json
import os
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-015" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cross_encoder import (  # noqa: E402
    CE_NAME,
    CE_ONNX,
    CE_REVISION,
    CE_SHA256,
    MAX_LENGTH,
    CrossEncoderReranker,
)
from rag_v1.embedders_transformer import TransformerEncoder  # noqa: E402
from rag_v1.evals.io import load_cases  # noqa: E402
from rag_v1.query_cache import CachedQueryEmbedder  # noqa: E402
from rag_v1.systems import FROZEN_HASHES  # noqa: E402
from rag_v1.types import EvidenceRef, SearchHit  # noqa: E402

from run_exp018_development import (  # noqa: E402
    dict_overlaps,
    env_fingerprint,
    first_span_rank,
    hit_as_row,
    paired,
    span_in_hits,
    summarise,
)
from system_e import (  # noqa: E402
    A_HASH,
    BLEND_A,
    BLEND_CE,
    CANDIDATE_POOL,
    CHUNK_SET,
    D_HASH,
    HOLD_LOCK_SHA,
    HOLD_LOG_SHA_AT_PREREG,
    PARENT_N,
    SNAPSHOT,
    TOP_K,
    TRANSFORMER_FINGERPRINT,
    TRANSFORMER_MODEL,
    W,
    apply_blend,
    covering_chunk_ids,
    embedding_status,
    holdout_log_state,
    local_bm25_per_parent,
    merge_union_rrf,
    parent_version_ids,
    retrieve_system_a_pool,
    system_e_config,
    system_e_hash,
)

OUT_DIR = ROOT / "experiments" / "EXP-018"
GOLD_JSONL = ROOT / "evals" / "gold" / "v2-devset-001.jsonl"
SPLIT_PATH = ROOT / "evals" / "splits" / "v2-devset-001" / "development.json"
D_FREEZE = ROOT / "experiments" / "EXP-016" / "SYSTEM-D-GUARD.json"
D_RELEASE = ROOT / "experiments" / "EVAL-HOLDOUT-001" / "SYSTEM-D-RELEASE.json"
E_FILE = ROOT / "experiments" / "EXP-018" / "SYSTEM-E-WITHIN-DOC.json"
EXPECTED_E = "7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe"
D_GUARD_SHA_AT_FREEZE = "e9267f5581404e9885598979204c08762cd33f362703e526b20f4d3430c35a82"
D_RELEASE_SHA_AT_FREEZE = "1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decide(cand_d: float, cand_e: float, d_strict: int, e_strict: int, d_spans10: int, e_spans10: int) -> dict:
    """Preregistered ChatGPT labels for this V2-DEVSET-001 comparison only."""
    cand_improved = cand_e > cand_d + 1e-12
    top10_improved = (e_strict > d_strict) or (e_spans10 > d_spans10)
    if not cand_improved:
        label = "REJECT_WITHIN_DOC_BM25"
    elif cand_improved and not top10_improved:
        label = "CANDIDATE_GAIN_RERANKING_LIMITED"
    else:
        label = "MECHANISM_SUPPORTED"
    return {
        "label": label,
        "MECHANISM_SUPPORTED": label == "MECHANISM_SUPPORTED",
        "CANDIDATE_GAIN_RERANKING_LIMITED": label == "CANDIDATE_GAIN_RERANKING_LIMITED",
        "REJECT_WITHIN_DOC_BM25": label == "REJECT_WITHIN_DOC_BM25",
        "candidate_recall_improved": cand_improved,
        "top10_improved": top10_improved,
        "rule": (
            "MECHANISM_SUPPORTED if E materially increases candidate evidence recall "
            "and top-10 also improves; CANDIDATE_GAIN_RERANKING_LIMITED if candidate "
            "recall improves but top-10 does not; REJECT_WITHIN_DOC_BM25 if candidate "
            "recall does not improve. Material = any increase in gold-span pool recall."
        ),
        "tuned_after_seeing_scores": False,
    }


def main() -> int:
    started = time.time()
    results_path = OUT_DIR / "EXP-018-v2devset001-results.json"
    report_path = OUT_DIR / "EXP-018-v2devset001-report.md"
    if results_path.exists():
        raise SystemExit("STOP: v2devset001 results already exist; refusing to overwrite")

    hold_before = holdout_log_state()
    if hold_before["log_bytes"] != 235 or hold_before["log_sha256"] != HOLD_LOG_SHA_AT_PREREG:
        raise SystemExit(f"STOP: holdout log drifted before run: {hold_before}")
    if hold_before["lock_sha256"] != HOLD_LOCK_SHA:
        raise SystemExit(f"STOP: holdout lock sha drifted: {hold_before}")

    a_hash = FROZEN_HASHES["SYSTEM-A-GLOBAL"]
    if a_hash != A_HASH:
        raise SystemExit(f"STOP: SYSTEM-A hash {a_hash} != {A_HASH}")
    d_freeze = json.loads(D_FREEZE.read_text())
    if d_freeze["config_hash"] != D_HASH:
        raise SystemExit("STOP: SYSTEM-D-GUARD.json hash mismatch")
    d_release = json.loads(D_RELEASE.read_text())
    if d_release["config_hash"] != D_HASH:
        raise SystemExit("STOP: SYSTEM-D-RELEASE.json hash mismatch")
    if _sha(D_FREEZE) != D_GUARD_SHA_AT_FREEZE:
        raise SystemExit("STOP: SYSTEM-D-GUARD.json bytes changed")
    if _sha(D_RELEASE) != D_RELEASE_SHA_AT_FREEZE:
        raise SystemExit("STOP: SYSTEM-D-RELEASE.json bytes changed")
    e_file_sha_before = _sha(E_FILE)

    emb = embedding_status()
    if not emb["complete"]:
        raise SystemExit(f"STOP: embeddings incomplete: {emb}")

    e_cfg = system_e_config()
    e_hash = system_e_hash()
    if e_hash != EXPECTED_E:
        raise SystemExit(f"STOP: SYSTEM-E hash {e_hash} != frozen {EXPECTED_E}")
    if e_cfg["W"] != 20 or e_cfg["parent_n"] != 10 or e_cfg["local_retrieval"] != "BM25_ONLY":
        raise SystemExit("STOP: E knobs drifted")
    if e_cfg["weights"] != [0.7, 0.3]:
        raise SystemExit("STOP: E blend weights drifted")

    encoder = TransformerEncoder(max_seq=512).load()
    if encoder.model_version != TRANSFORMER_FINGERPRINT:
        raise SystemExit("STOP: live encoder fingerprint mismatch")
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)
    ce = CrossEncoderReranker()
    probe_q, probe_p = "What is BM25?", "BM25 is a lexical ranking function."
    ce_stable = ce.score_pairs(probe_q, [probe_p])[0] == ce.score_pairs(probe_q, [probe_p])[0]

    cases = [c for c in load_cases(GOLD_JSONL) if c.expected_evidence]
    if len(cases) != 50:
        raise SystemExit(f"expected 50 v2-devset-001 cases, got {len(cases)}")
    split_ids = json.loads(SPLIT_PATH.read_text())["case_ids"]
    got_ids = [c.case_id for c in cases]
    if got_ids != split_ids:
        raise SystemExit(f"STOP: gold jsonl ids != development.json: {got_ids}")
    if split_ids != [f"V2D-{i:02d}" for i in range(1, 51)]:
        raise SystemExit("STOP: split ids are not V2D-01..50")

    gold_cover: dict[str, list[list[str]]] = {}
    for case in cases:
        gold_cover[case.case_id] = [covering_chunk_ids(ref) for ref in case.expected_evidence]

    lat_a, lat_local, lat_ce_d, lat_ce_e, lat_d_total, lat_e_total = [], [], [], [], [], []
    a_cases, d_cases, e_cases = {}, {}, {}
    a_full, d_full, e_full = {}, {}, {}
    per_case = []
    compact_pools = []
    additive_failures = []
    cand_ev_d_flags = []
    cand_ev_e_flags = []
    pool_sizes_e = []
    pool_sizes_d = []
    new_member_counts = []

    for case in cases:
        q = case.question
        t_case = time.time()
        t0 = time.time()
        a_pool = retrieve_system_a_pool(q, transformer)
        lat_a.append((time.time() - t0) * 1000)

        parents = parent_version_ids(a_pool, PARENT_N)
        t0 = time.time()
        local = local_bm25_per_parent(q, parents)
        lat_local.append((time.time() - t0) * 1000)
        fused_e, new_ids, a_ids = merge_union_rrf(a_pool, local)
        if not a_ids.issubset({h.chunk_id for h in fused_e}):
            additive_failures.append(case.case_id)
            raise SystemExit(f"STOP: additive integrity failed on {case.case_id}")

        a_by_id = {h.chunk_id: h for h in a_pool}

        t0 = time.time()
        a_texts = [h.text for h in a_pool]
        a_ce = ce.score_pairs(q, a_texts)
        lat_ce_d.append((time.time() - t0) * 1000)
        d_rows_in = []
        for hit, score in zip(a_pool, a_ce, strict=True):
            d_rows_in.append(
                hit_as_row(
                    hit,
                    a_rank=int(hit.rank),
                    a_score=float(hit.score),
                    ce_score=float(score),
                    in_a_pool=True,
                    origin="a_pool",
                )
            )
        d_rows = apply_blend(d_rows_in)
        for r in d_rows:
            r["d_rank"] = r["blend_rank"]
        lat_d_total.append((time.time() - t_case) * 1000 - lat_local[-1])

        ce_by_id = {h.chunk_id: s for h, s in zip(a_pool, a_ce, strict=True)}
        new_hits = [h for h in fused_e if h.chunk_id not in ce_by_id]
        t0 = time.time()
        if new_hits:
            new_scores = ce.score_pairs(q, [h.text for h in new_hits])
            for h, s in zip(new_hits, new_scores, strict=True):
                ce_by_id[h.chunk_id] = float(s)
        lat_ce_e.append(lat_ce_d[-1] + (time.time() - t0) * 1000)

        e_rows_in = []
        for hit in fused_e:
            origin = "a_pool" if hit.chunk_id in a_ids else "local_bm25"
            e_rows_in.append(
                hit_as_row(
                    hit,
                    a_rank=int(hit.rank),
                    a_score=float(hit.score),
                    ce_score=float(ce_by_id[hit.chunk_id]),
                    in_a_pool=hit.chunk_id in a_ids,
                    origin=origin,
                    system_a_rank=int(a_by_id[hit.chunk_id].rank) if hit.chunk_id in a_by_id else None,
                    system_a_score=float(a_by_id[hit.chunk_id].score) if hit.chunk_id in a_by_id else None,
                )
            )
        e_rows = apply_blend(e_rows_in)
        for r in e_rows:
            r["e_rank"] = r["blend_rank"]
        lat_e_total.append((time.time() - t_case) * 1000)

        pool_sizes_d.append(len(a_pool))
        pool_sizes_e.append(len(fused_e))
        new_member_counts.append(len(new_ids))

        def score_system(rows: list[dict], rank_key: str, pool_for_evidence: list) -> dict:
            spans = []
            gold_docs = {ref.version_id for ref in case.expected_evidence}
            top_docs = {r["version_id"] for r in rows if r[rank_key] <= TOP_K}
            for i, ref in enumerate(case.expected_evidence):
                in_pool = span_in_hits(pool_for_evidence, ref)
                rank = first_span_rank(rows, ref, rank_key)
                spans.append(
                    {
                        "span_index": i,
                        "covering_chunk_ids": gold_cover[case.case_id][i],
                        "in_pool": in_pool,
                        "rank": rank,
                        "within_10": rank is not None and rank <= TOP_K,
                        "doc_in_top_10": ref.version_id in top_docs,
                        "pool_rank": None,
                    }
                )
            found = sum(1 for s in spans if s["within_10"])
            return {
                "case_id": case.case_id,
                "spans": spans,
                "recall": found / len(spans) if spans else 1.0,
                "fully_recalled": bool(spans) and found == len(spans),
                "doc_recall": (len(gold_docs & top_docs) / len(gold_docs)) if gold_docs else 1.0,
                "gold_docs_in_top_10": sorted(gold_docs & top_docs),
                "gold_docs": sorted(gold_docs),
                "cand_ev_span_flags": [s["in_pool"] for s in spans],
            }

        a_pool_rows = [
            hit_as_row(h, pool_rank=int(h.rank), a_rank=int(h.rank), a_score=float(h.score))
            for h in a_pool
        ]
        e_pool_rows = [
            hit_as_row(h, pool_rank=int(h.rank), a_rank=int(h.rank), a_score=float(h.score))
            for h in fused_e
        ]

        a_scored = score_system(
            [{**hit_as_row(h), "a_rank": int(h.rank)} for h in a_pool],
            "a_rank",
            a_pool,
        )
        for i, ref in enumerate(case.expected_evidence):
            a_scored["spans"][i]["pool_rank"] = first_span_rank(a_pool_rows, ref, "pool_rank")
            a_scored["spans"][i]["in_pool"] = span_in_hits(a_pool, ref)

        d_scored = score_system(d_rows, "d_rank", a_pool)
        for i, ref in enumerate(case.expected_evidence):
            d_scored["spans"][i]["pool_rank"] = first_span_rank(a_pool_rows, ref, "pool_rank")
            d_scored["spans"][i]["in_pool"] = span_in_hits(a_pool, ref)

        e_scored = score_system(e_rows, "e_rank", fused_e)
        for i, ref in enumerate(case.expected_evidence):
            e_scored["spans"][i]["pool_rank"] = first_span_rank(e_pool_rows, ref, "pool_rank")
            e_scored["spans"][i]["in_pool"] = span_in_hits(fused_e, ref)

        a_cases[case.case_id] = a_scored
        d_cases[case.case_id] = d_scored
        e_cases[case.case_id] = e_scored
        a_full[case.case_id] = a_scored["fully_recalled"]
        d_full[case.case_id] = d_scored["fully_recalled"]
        e_full[case.case_id] = e_scored["fully_recalled"]
        cand_ev_d_flags.extend(d_scored["cand_ev_span_flags"])
        cand_ev_e_flags.extend(e_scored["cand_ev_span_flags"])

        first_gold_pool_a = min(
            (s["pool_rank"] for s in a_scored["spans"] if s["pool_rank"] is not None),
            default=None,
        )
        first_gold_pool_e = min(
            (s["pool_rank"] for s in e_scored["spans"] if s["pool_rank"] is not None),
            default=None,
        )
        d_top_docs = set(d_scored["gold_docs_in_top_10"])
        e_top_docs = set(e_scored["gold_docs_in_top_10"])
        dropped_docs = sorted(d_top_docs - e_top_docs)

        span_rows = []
        for i, ref in enumerate(case.expected_evidence):
            d_row = next((r for r in d_rows if dict_overlaps(r, ref)), None)
            e_row = next((r for r in e_rows if dict_overlaps(r, ref)), None)
            span_rows.append(
                {
                    "span_index": i,
                    "covering_chunk_ids": gold_cover[case.case_id][i],
                    "a_rank": a_scored["spans"][i]["rank"],
                    "d_rank": d_scored["spans"][i]["rank"],
                    "e_rank": e_scored["spans"][i]["rank"],
                    "d_pool_rank": d_scored["spans"][i]["pool_rank"],
                    "e_pool_rank": e_scored["spans"][i]["pool_rank"],
                    "in_d_pool": d_scored["spans"][i]["in_pool"],
                    "in_e_pool": e_scored["spans"][i]["in_pool"],
                    "ce_score_d": d_row["ce_score"] if d_row else None,
                    "ce_score_e": e_row["ce_score"] if e_row else None,
                    "blend_d": d_row["blend_score"] if d_row else None,
                    "blend_e": e_row["blend_score"] if e_row else None,
                    "new_union_member": bool(e_row and not e_row["in_a_pool"])
                    if e_row
                    else (not d_scored["spans"][i]["in_pool"] and e_scored["spans"][i]["in_pool"]),
                    "a_in_top_10": a_scored["spans"][i]["within_10"],
                    "d_in_top_10": d_scored["spans"][i]["within_10"],
                    "e_in_top_10": e_scored["spans"][i]["within_10"],
                }
            )

        destructions_e_vs_d = [s for s in span_rows if s["d_rank"] == 1 and not s["e_in_top_10"]]
        destructions_e_vs_a = [s for s in span_rows if s["a_rank"] == 1 and not s["e_in_top_10"]]

        rec = {
            "case_id": case.case_id,
            "a_full": a_full[case.case_id],
            "d_full": d_full[case.case_id],
            "e_full": e_full[case.case_id],
            "parents": parents,
            "n_parents": len(parents),
            "a_pool_size": len(a_pool),
            "e_pool_size": len(fused_e),
            "n_new_union_members": len(new_ids),
            "additive_integrity": a_ids.issubset({h.chunk_id for h in fused_e}),
            "dropped_d_gold_docs": dropped_docs,
            "first_gold_pool_rank_A": first_gold_pool_a,
            "first_gold_pool_rank_E": first_gold_pool_e,
            "spans": span_rows,
            "rank1_destruction_vs_D": destructions_e_vs_d,
            "rank1_destruction_vs_A": destructions_e_vs_a,
            "latency_ms": {
                "system_a_retrieval": round(lat_a[-1], 2),
                "local_bm25": round(lat_local[-1], 2),
                "cross_encoder_D_pool": round(lat_ce_d[-1], 2),
                "cross_encoder_E_union": round(lat_ce_e[-1], 2),
                "D_total": round(lat_d_total[-1], 2),
                "E_total": round(lat_e_total[-1], 2),
            },
        }
        per_case.append(rec)
        compact_pools.append(
            {
                "case_id": case.case_id,
                "parents": parents,
                "a_pool_size": len(a_pool),
                "e_pool_size": len(fused_e),
                "new_union_chunk_ids": new_ids,
                "d_top10": [
                    {"chunk_id": r["chunk_id"], "version_id": r["version_id"], "d_rank": r["d_rank"]}
                    for r in d_rows
                    if r["d_rank"] <= TOP_K
                ],
                "e_top10": [
                    {"chunk_id": r["chunk_id"], "version_id": r["version_id"], "e_rank": r["e_rank"]}
                    for r in e_rows
                    if r["e_rank"] <= TOP_K
                ],
            }
        )
        print(
            f"{case.case_id} A={int(a_full[case.case_id])} D={int(d_full[case.case_id])} "
            f"E={int(e_full[case.case_id])} pool {len(a_pool)}->{len(fused_e)} "
            f"new={len(new_ids)} inD={int(d_scored['spans'][0]['in_pool'])} "
            f"inE={int(e_scored['spans'][0]['in_pool'])} E_ms={lat_e_total[-1]:.0f}",
            flush=True,
        )

    hold_after = holdout_log_state()
    if hold_after != hold_before:
        raise SystemExit(f"STOP: holdout log changed during run {hold_before} -> {hold_after}")
    if _sha(D_FREEZE) != D_GUARD_SHA_AT_FREEZE or _sha(D_RELEASE) != D_RELEASE_SHA_AT_FREEZE:
        raise SystemExit("STOP: D freeze files mutated during run")
    if _sha(E_FILE) != e_file_sha_before:
        raise SystemExit("STOP: SYSTEM-E-WITHIN-DOC.json mutated during run")

    system_a = summarise(a_cases, "SYSTEM-A-GLOBAL", A_HASH)
    system_d = summarise(d_cases, "SYSTEM-D-GUARD-BLEND", D_HASH)
    system_e = summarise(e_cases, "SYSTEM-E-WITHIN-DOC", e_hash)

    n_spans = len(cand_ev_d_flags)
    cand_ev_d = (sum(cand_ev_d_flags) / n_spans) if n_spans else 1.0
    cand_ev_e = (sum(cand_ev_e_flags) / n_spans) if n_spans else 1.0
    pair_e_vs_d = paired(d_full, e_full)
    pair_d_vs_a = paired(a_full, d_full)
    rank1_vs_d = [s for rec in per_case for s in rec["rank1_destruction_vs_D"]]
    rank1_vs_a = [s for rec in per_case for s in rec["rank1_destruction_vs_A"]]
    additive_ok = all(rec["additive_integrity"] for rec in per_case) and not any(
        rec["dropped_d_gold_docs"] for rec in per_case
    )

    decision = decide(
        cand_ev_d,
        cand_ev_e,
        system_d["cases_fully_recalled"],
        system_e["cases_fully_recalled"],
        system_d["spans_found_at_10"],
        system_e["spans_found_at_10"],
    )

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    latency = {
        "A_retrieval_mean": round(statistics.mean(lat_a), 1),
        "local_bm25_mean": round(statistics.mean(lat_local), 1),
        "CE_D_pool_mean": round(statistics.mean(lat_ce_d), 1),
        "CE_E_union_mean": round(statistics.mean(lat_ce_e), 1),
        "D_total_mean": round(statistics.mean(lat_d_total), 1),
        "E_total_mean": round(statistics.mean(lat_e_total), 1),
    }

    metrics_block = {
        "A": {
            "source": "rematerialized frozen SYSTEM-A on v2-devset-001/development",
            "config_hash": A_HASH,
            **{k: system_a[k] for k in system_a if k not in ("system", "config_hash")},
            "candidate_evidence_recall": round(cand_ev_d, 4),
            "candidate_evidence_spans": f"{sum(cand_ev_d_flags)}/{n_spans}",
            "pool_size_mean": round(statistics.mean(pool_sizes_d), 2),
            "pool_size_max": max(pool_sizes_d),
            "latency_ms_mean": latency["A_retrieval_mean"],
        },
        "D": {
            "source": "rematerialized frozen SYSTEM-D-GUARD-BLEND on A-pool-100",
            "config_hash": D_HASH,
            **{k: system_d[k] for k in system_d if k not in ("system", "config_hash")},
            "candidate_evidence_recall": round(cand_ev_d, 4),
            "candidate_evidence_spans": f"{sum(cand_ev_d_flags)}/{n_spans}",
            "pool_size_mean": round(statistics.mean(pool_sizes_d), 2),
            "pool_size_max": max(pool_sizes_d),
            "latency_ms_mean": latency["D_total_mean"],
        },
        "E": {
            "source": "frozen SYSTEM-E-WITHIN-DOC local-BM25 union + merge RRF + frozen D blend",
            "config_hash": e_hash,
            **{k: system_e[k] for k in system_e if k not in ("system", "config_hash")},
            "candidate_evidence_recall": round(cand_ev_e, 4),
            "candidate_evidence_spans": f"{sum(cand_ev_e_flags)}/{n_spans}",
            "pool_size_mean": round(statistics.mean(pool_sizes_e), 2),
            "pool_size_max": max(pool_sizes_e),
            "new_union_members_mean": round(statistics.mean(new_member_counts), 2),
            "latency_ms_mean": latency["E_total_mean"],
        },
    }

    candidate_rescues = [
        rec["case_id"]
        for rec in per_case
        if any(s["in_e_pool"] and not s["in_d_pool"] for s in rec["spans"])
    ]
    candidate_only_d = [
        rec["case_id"]
        for rec in per_case
        if any(s["in_d_pool"] and not s["in_e_pool"] for s in rec["spans"])
    ]

    payload = {
        "experiment_id": "EXP-018",
        "phase": "v2-devset-001_frozen_D_vs_E",
        "split": "v2-devset-001/development",
        "split_path": "evals/splits/v2-devset-001/development.json",
        "gold_path": "evals/gold/v2-devset-001.jsonl",
        "n": 50,
        "freeze": "experiments/RAG-V2/V2-DEVSET-001/V2-DEVSET-001-FREEZE.json",
        "timestamp": timestamp,
        "corpus_snapshot": SNAPSHOT,
        "chunk_set": CHUNK_SET,
        "system_a_config_hash": A_HASH,
        "system_d_config_hash": D_HASH,
        "system_e_config_hash": e_hash,
        "tuned_after_seeing_scores": False,
        "e_knobs_changed": False,
        "validation_loaded": False,
        "holdout_loaded": False,
        "holdout_json_opened": False,
        "holdout_access_log_before": hold_before,
        "holdout_access_log_after": hold_after,
        "holdout_log_unchanged": hold_after == hold_before,
        "embedding": emb,
        "environment": env_fingerprint(emb),
        "metrics": metrics_block,
        "candidate_evidence_recall": {
            "D_A_pool": round(cand_ev_d, 4),
            "E_union_pool": round(cand_ev_e, 4),
            "spans_in_D_pool": f"{sum(cand_ev_d_flags)}/{n_spans}",
            "spans_in_E_pool": f"{sum(cand_ev_e_flags)}/{n_spans}",
            "primary": True,
            "candidate_pool_rescues_vs_D": candidate_rescues,
            "candidate_pool_only_in_D": candidate_only_d,
        },
        "additive_integrity": {
            "passed": additive_ok,
            "failures": additive_failures,
            "dropped_d_gold_docs": {
                rec["case_id"]: rec["dropped_d_gold_docs"]
                for rec in per_case
                if rec["dropped_d_gold_docs"]
            },
        },
        "paired_E_vs_D": pair_e_vs_d,
        "paired_D_vs_A": pair_d_vs_a,
        "rank1_destruction_vs_D": rank1_vs_d,
        "rank1_destruction_vs_A": rank1_vs_a,
        "per_case": per_case,
        "latency_ms": latency,
        "decision": decision,
        "cross_encoder": {
            "name": CE_NAME,
            "revision": CE_REVISION,
            "artifact_sha256": CE_SHA256,
            "pair_score_stable": ce_stable,
        },
        "runtime_seconds": round(time.time() - started, 1),
        "freeze_files_untouched": {
            "SYSTEM-D-GUARD.json_sha256": _sha(D_FREEZE),
            "SYSTEM-D-RELEASE.json_sha256": _sha(D_RELEASE),
            "SYSTEM-E-WITHIN-DOC.json_sha256": _sha(E_FILE),
        },
    }
    results_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    (OUT_DIR / "EXP-018-v2devset001-pools.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in compact_pools) + "\n",
        encoding="utf-8",
    )

    def row(letter, m, cand):
        return (
            f"| {letter} | {m['strict_recall_at_10']} | {m['macro_span_recall']:.4f} | "
            f"{m['spans_found_at_10']}/{m['spans_total']} | {m['mrr']:.4f} | "
            f"{m['document_recall']:.4f} | {cand:.4f} | {m['pool_size_mean']:.1f}/{m['pool_size_max']} | "
            f"{m['latency_ms_mean']} |"
        )

    report = []
    report.append("# EXP-018 V2-DEVSET-001 D vs E")
    report.append("")
    report.append(
        f"Timestamp: {timestamp} (UTC). Split: v2-devset-001/development n=50. "
        "One comparison of frozen SYSTEM-D vs frozen SYSTEM-E. E knobs not retuned."
    )
    report.append("gold150-v1 holdout.json not opened. gold150-v1/development not loaded. Validation not loaded.")
    report.append(
        f"Holdout access log before/after: {hold_before['log_bytes']}/{hold_after['log_bytes']} bytes "
        f"(sha {hold_before['log_sha256'][:12]}… unchanged={hold_after == hold_before})."
    )
    report.append(
        f"SYSTEM-D `{D_HASH}`. SYSTEM-E `{e_hash}`. Snapshot `{SNAPSHOT}`. chunk_set `cs_v1_control`."
    )
    report.append("")
    report.append("## Primary metric — candidate gold-span Recall@100")
    report.append("")
    report.append(
        f"D/A pool {sum(cand_ev_d_flags)}/{n_spans} = {cand_ev_d:.4f}; "
        f"E union {sum(cand_ev_e_flags)}/{n_spans} = {cand_ev_e:.4f}."
    )
    report.append(
        f"Candidate-pool rescues vs D: {candidate_rescues or '—'}; "
        f"only-in-D (should be empty if additive): {candidate_only_d or '—'}."
    )
    report.append("")
    report.append("## Secondary")
    report.append("")
    report.append(
        "| V | strict R@10 | span recall | spans@10 | MRR | doc recall | "
        "cand-ev recall (pool) | pool mean/max | latency ms |"
    )
    report.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    report.append(row("A", metrics_block["A"], cand_ev_d))
    report.append(row("D", metrics_block["D"], cand_ev_d))
    report.append(row("E", metrics_block["E"], cand_ev_e))
    report.append("")
    report.append(
        f"Additive integrity: `{additive_ok}`. Rescues vs D (strict R@10): "
        f"{pair_e_vs_d['rescues'] or '—'}; regressions vs D: {pair_e_vs_d['regressions'] or '—'}; "
        f"net {pair_e_vs_d['net']:+d}."
    )
    report.append(
        f"Rank-1 destruction vs D: {len(rank1_vs_d)}; vs A: {len(rank1_vs_a)}."
    )
    report.append(
        f"E mean latency {latency['E_total_mean']} ms vs rematerialized D {latency['D_total_mean']} ms."
    )
    report.append("")
    if pair_e_vs_d["rescues"] or pair_e_vs_d["regressions"] or candidate_rescues:
        report.append("## Differing cases")
        report.append("")
        for rec in per_case:
            if rec["d_full"] != rec["e_full"] or any(
                s["in_d_pool"] != s["in_e_pool"] for s in rec["spans"]
            ):
                report.append(
                    f"- `{rec['case_id']}` D_full={rec['d_full']} E_full={rec['e_full']} "
                    f"inD={rec['spans'][0]['in_d_pool']} inE={rec['spans'][0]['in_e_pool']} "
                    f"D_rank={rec['spans'][0]['d_rank']} E_rank={rec['spans'][0]['e_rank']} "
                    f"pool {rec['a_pool_size']}→{rec['e_pool_size']}"
                )
        report.append("")
    report.append("## Decision (preregistered, not retuned)")
    report.append("")
    report.append(f"**{decision['label']}**")
    report.append("")
    report.append(f"- MECHANISM_SUPPORTED: `{decision['MECHANISM_SUPPORTED']}`")
    report.append(f"- CANDIDATE_GAIN_RERANKING_LIMITED: `{decision['CANDIDATE_GAIN_RERANKING_LIMITED']}`")
    report.append(f"- REJECT_WITHIN_DOC_BM25: `{decision['REJECT_WITHIN_DOC_BM25']}`")
    report.append(f"- candidate_recall_improved: `{decision['candidate_recall_improved']}`")
    report.append(f"- top10_improved: `{decision['top10_improved']}`")
    report.append("- tuned_after_seeing_scores: `False`")
    report.append(f"- SYSTEM-E config hash (unchanged): `{e_hash}`")
    report.append("- SYSTEM-D-GUARD.json / SYSTEM-D-RELEASE.json / SYSTEM-E-WITHIN-DOC.json bytes unchanged.")
    report.append(
        f"- Environment: {emb['postgres_version'].split(',')[0]} / pgvector {emb['pgvector_extversion']}."
    )
    report.append("")
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    print("decision", decision["label"])
    print("D", system_d["strict_recall_at_10"], "cand", f"{sum(cand_ev_d_flags)}/{n_spans}", cand_ev_d)
    print("E", system_e["strict_recall_at_10"], "cand", f"{sum(cand_ev_e_flags)}/{n_spans}", cand_ev_e)
    print("holdout", hold_before["log_bytes"], hold_after["log_bytes"])
    print("e_hash", e_hash)
    print("wrote", results_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
