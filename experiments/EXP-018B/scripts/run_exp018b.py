#!/usr/bin/env python3
"""EXP-018B: Track 1 batched local BM25 + Track 2 additive L in {10,20,40}.

Preregistration must exist before this scores. Does not load gold150-v1
holdout.json or gold150-v1/development. Does not mutate D/E freeze files or
cs_v1_control. Does not rerun run_exp018_v2devset001.py.
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
sys.path.insert(0, str(ROOT / "experiments" / "EXP-018" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cross_encoder import (  # noqa: E402
    CE_NAME,
    CE_REVISION,
    CE_SHA256,
    CrossEncoderReranker,
)
from rag_v1.embedders_transformer import TransformerEncoder  # noqa: E402
from rag_v1.evals.io import load_cases  # noqa: E402
from rag_v1.query_cache import CachedQueryEmbedder  # noqa: E402
from rag_v1.systems import FROZEN_HASHES  # noqa: E402
from rag_v1.types import SearchHit  # noqa: E402

from local_bm25_batched import (  # noqa: E402
    additive_extras_ordered,
    cap_local_lists,
    local_bm25_per_parent_batched,
)
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
    merge_union_rrf,
    parent_version_ids,
    retrieve_system_a_pool,
    system_e_config,
    system_e_hash,
)

OUT_DIR = ROOT / "experiments" / "EXP-018B"
GOLD_JSONL = ROOT / "evals" / "gold" / "v2-devset-001.jsonl"
SPLIT_PATH = ROOT / "evals" / "splits" / "v2-devset-001" / "development.json"
D_FREEZE = ROOT / "experiments" / "EXP-016" / "SYSTEM-D-GUARD.json"
D_RELEASE = ROOT / "experiments" / "EVAL-HOLDOUT-001" / "SYSTEM-D-RELEASE.json"
E_FILE = ROOT / "experiments" / "EXP-018" / "SYSTEM-E-WITHIN-DOC.json"
STORED_RESULTS = ROOT / "experiments" / "EXP-018" / "EXP-018-v2devset001-results.json"
STORED_POOLS = ROOT / "experiments" / "EXP-018" / "EXP-018-v2devset001-pools.jsonl"
PREREG_JSON = OUT_DIR / "EXP-018B-preregistration.json"
PREREG_MD = OUT_DIR / "EXP-018B-preregistration.md"
EXPECTED_E = "7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe"
D_GUARD_SHA_AT_FREEZE = "e9267f5581404e9885598979204c08762cd33f362703e526b20f4d3430c35a82"
D_RELEASE_SHA_AT_FREEZE = "1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40"
PREREG_JSON_SHA = "c48068ec5dfa06683eaa2b0763508e9c7457d1ede2f23c3394c3c6bd6192ce8c"
L_VALUES = (10, 20, 40)
DIAGNOSTIC_IDS = ("V2D-11", "V2D-33", "V2D-34", "V2D-43")
GOLD_SHA = "cb687f3cc88b38d4beed7ad4bc829296a30518aaaf45cce0677ec568b1bf77e5"
SPLIT_SHA = "6b0c49c9040c215fde6134697c35a1f28458ba7d72ef012c0840feb7f9c3eb17"
FREEZE_SHA = "97ea6befbb4fd845f53da2aef20ba84cedaaf69c0f09e3ad90833b813fee2ad9"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mean(xs: list[float]) -> float:
    return round(statistics.mean(xs), 1) if xs else 0.0


def score_system(case, rows: list[dict], rank_key: str, pool, gold_cover: dict) -> dict:
    spans = []
    gold_docs = {ref.version_id for ref in case.expected_evidence}
    top_docs = {r["version_id"] for r in rows if r[rank_key] <= TOP_K}
    for i, ref in enumerate(case.expected_evidence):
        in_pool = span_in_hits(pool, ref)
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


def metrics_from_cases(cases_map: dict, name: str, cfg_hash: str, cand_flags: list[bool],
                       pool_sizes: list[int], latency_mean: float, extra: dict | None = None) -> dict:
    s = summarise(cases_map, name, cfg_hash)
    n_spans = len(cand_flags)
    out = {
        "source": name,
        "config_hash": cfg_hash,
        **{k: s[k] for k in s if k not in ("system", "config_hash")},
        "candidate_evidence_recall": round((sum(cand_flags) / n_spans) if n_spans else 1.0, 4),
        "candidate_evidence_spans": f"{sum(cand_flags)}/{n_spans}",
        "candidate_evidence_n": sum(cand_flags),
        "candidate_evidence_d": n_spans,
        "pool_size_mean": round(statistics.mean(pool_sizes), 2) if pool_sizes else 0.0,
        "pool_size_max": max(pool_sizes) if pool_sizes else 0,
        "latency_ms_mean": latency_mean,
    }
    if extra:
        out.update(extra)
    return out


def blend_union(fused, a_ids, a_by_id, ce_by_id, rank_key: str) -> list[dict]:
    rows_in = []
    for hit in fused:
        origin = "a_pool" if hit.chunk_id in a_ids else "local_bm25"
        rows_in.append(
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
    rows = apply_blend(rows_in)
    for r in rows:
        r[rank_key] = r["blend_rank"]
    return rows


def compare_track1(per_case: list[dict], compact_pools: list[dict],
                   stored_results: dict, stored_pools: dict,
                   m_d: dict, m_e: dict) -> dict:
    mismatches: list[dict] = []
    n = len(per_case)
    union_ok = 0
    parents_ok = 0
    e_top10_ok = 0
    gold_rank_ok = 0
    local_order_proxy_ok = 0
    for rec, pool in zip(per_case, compact_pools, strict=True):
        cid = rec["case_id"]
        sp = stored_pools[cid]
        sr = next(x for x in stored_results["per_case"] if x["case_id"] == cid)
        issues = []
        if rec["parents"] != sp["parents"]:
            issues.append("parents")
        else:
            parents_ok += 1
        if set(pool["new_union_chunk_ids"]) != set(sp["new_union_chunk_ids"]):
            only_new = sorted(set(pool["new_union_chunk_ids"]) - set(sp["new_union_chunk_ids"]))
            only_old = sorted(set(sp["new_union_chunk_ids"]) - set(pool["new_union_chunk_ids"]))
            issues.append(
                f"union extras new={len(only_new)} missing={len(only_old)} "
                f"sample_new={only_new[:3]} sample_missing={only_old[:3]}"
            )
        else:
            union_ok += 1
        got_e = [r["chunk_id"] for r in pool["e_top10"]]
        exp_e = [r["chunk_id"] for r in sp["e_top10"]]
        if got_e != exp_e:
            issues.append(f"e_top10 got={got_e} expected={exp_e}")
        else:
            e_top10_ok += 1
        # gold span e_rank / in_pool
        for i, span in enumerate(rec["spans"]):
            sspan = sr["spans"][i]
            if span["e_rank"] != sspan["e_rank"] or span["in_e_pool"] != sspan["in_e_pool"]:
                issues.append(
                    f"gold span{i} e_rank {span['e_rank']} vs {sspan['e_rank']} "
                    f"in_e {span['in_e_pool']} vs {sspan['in_e_pool']}"
                )
            else:
                gold_rank_ok += 1
        if rec["n_new_union_members"] != sr["n_new_union_members"] or rec["e_pool_size"] != sr["e_pool_size"]:
            issues.append(
                f"pool size new={rec['n_new_union_members']}/{rec['e_pool_size']} "
                f"vs {sr['n_new_union_members']}/{sr['e_pool_size']}"
            )
        if rec["e_full"] != sr["e_full"] or rec["d_full"] != sr["d_full"]:
            issues.append(f"full D/E {rec['d_full']}/{rec['e_full']} vs {sr['d_full']}/{sr['e_full']}")
        # proxy for per-parent order: union extras + e_top10 both match
        if not issues:
            local_order_proxy_ok += 1
        if issues:
            mismatches.append({"case_id": cid, "issues": issues})

    def _metric_eq(a, b, key):
        return a.get(key) == b.get(key)

    stored_e = stored_results["metrics"]["E"]
    stored_d = stored_results["metrics"]["D"]
    metric_keys = [
        "strict_recall_at_10",
        "macro_span_recall",
        "mrr",
        "document_recall",
        "candidate_evidence_spans",
        "cases_fully_recalled",
        "spans_found_at_10",
    ]
    metric_mismatches = []
    for k in metric_keys:
        if m_e.get(k) != stored_e.get(k):
            metric_mismatches.append({"side": "E", "key": k, "got": m_e.get(k), "expected": stored_e.get(k)})
        if m_d.get(k) != stored_d.get(k):
            metric_mismatches.append({"side": "D", "key": k, "got": m_d.get(k), "expected": stored_d.get(k)})

    score_preserving = (not mismatches) and (not metric_mismatches)
    return {
        "SCORE_PRESERVING": score_preserving,
        "n": n,
        "union_membership_ok": union_ok,
        "parents_ok": parents_ok,
        "e_top10_ok": e_top10_ok,
        "gold_e_rank_ok": gold_rank_ok,
        "local_order_proxy_ok": local_order_proxy_ok,
        "local_order_note": (
            "stored EXP-018 did not persist per-parent ordered local lists; "
            "within-parent order is round(BM25,9) DESC, chunk_id ASC from _LEXICAL_SQL; "
            "batched path uses the same ORDER BY then first W per parent. "
            "Proxy: union extras identity + e_top10 (RRF consumes per-parent ranks)."
        ),
        "per_query_mismatches": mismatches,
        "metric_mismatches": metric_mismatches,
    }


def diagnostic_fate(case_id: str, scored: dict, rec_spans: list[dict]) -> dict:
    span0 = rec_spans[0] if rec_spans else {}
    return {
        "case_id": case_id,
        "DIAGNOSTIC_ONLY": True,
        "in_pool": bool(span0.get("in_e_pool") if "in_e_pool" in span0 else scored["spans"][0]["in_pool"]),
        "blend_rank": span0.get("e_rank", scored["spans"][0]["rank"]),
        "pool_rank": span0.get("e_pool_rank", scored["spans"][0]["pool_rank"]),
    }


def main() -> int:
    started = time.time()
    results_path = OUT_DIR / "EXP-018B-results.json"
    report_path = OUT_DIR / "EXP-018B-report.md"
    track1_json = OUT_DIR / "EXP-018B-track1-equivalence.json"
    track1_md = OUT_DIR / "EXP-018B-track1-equivalence.md"
    if results_path.exists() or track1_json.exists():
        raise SystemExit("STOP: EXP-018B results already exist; refusing to overwrite")
    if not PREREG_JSON.exists() or not PREREG_MD.exists():
        raise SystemExit("STOP: preregistration missing; do not score")
    got_pre = _sha(PREREG_JSON)
    if got_pre != PREREG_JSON_SHA:
        raise SystemExit(f"STOP: prereg json sha {got_pre} != frozen {PREREG_JSON_SHA}")

    hold_before = holdout_log_state()
    if hold_before["log_bytes"] != 235 or hold_before["log_sha256"] != HOLD_LOG_SHA_AT_PREREG:
        raise SystemExit(f"STOP: holdout log drifted before run: {hold_before}")
    if hold_before["lock_sha256"] != HOLD_LOCK_SHA:
        raise SystemExit(f"STOP: holdout lock sha drifted: {hold_before}")
    if _sha(GOLD_JSONL) != GOLD_SHA or _sha(SPLIT_PATH) != SPLIT_SHA:
        raise SystemExit("STOP: gold/split hash mismatch")
    freeze_path = ROOT / "experiments" / "RAG-V2" / "V2-DEVSET-001" / "V2-DEVSET-001-FREEZE.json"
    if _sha(freeze_path) != FREEZE_SHA:
        raise SystemExit("STOP: V2-DEVSET-001 freeze hash mismatch")

    a_hash = FROZEN_HASHES["SYSTEM-A-GLOBAL"]
    if a_hash != A_HASH:
        raise SystemExit(f"STOP: SYSTEM-A hash {a_hash} != {A_HASH}")
    if json.loads(D_FREEZE.read_text())["config_hash"] != D_HASH:
        raise SystemExit("STOP: SYSTEM-D-GUARD.json hash mismatch")
    if json.loads(D_RELEASE.read_text())["config_hash"] != D_HASH:
        raise SystemExit("STOP: SYSTEM-D-RELEASE.json hash mismatch")
    if _sha(D_FREEZE) != D_GUARD_SHA_AT_FREEZE or _sha(D_RELEASE) != D_RELEASE_SHA_AT_FREEZE:
        raise SystemExit("STOP: D freeze file bytes changed")
    e_file_sha_before = _sha(E_FILE)

    emb = embedding_status()
    if not emb["complete"]:
        raise SystemExit(f"STOP: embeddings incomplete: {emb}")

    e_cfg = system_e_config()
    e_hash = system_e_hash()
    if e_hash != EXPECTED_E:
        raise SystemExit(f"STOP: SYSTEM-E hash {e_hash} != frozen {EXPECTED_E}")
    if e_cfg["W"] != 20 or e_cfg["parent_n"] != 10 or e_cfg["weights"] != [0.7, 0.3]:
        raise SystemExit("STOP: E knobs drifted")

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
    if got_ids != split_ids or split_ids != [f"V2D-{i:02d}" for i in range(1, 51)]:
        raise SystemExit("STOP: split ids mismatch")

    gold_cover: dict[str, list[list[str]]] = {}
    for case in cases:
        gold_cover[case.case_id] = [covering_chunk_ids(ref) for ref in case.expected_evidence]

    stored_results = json.loads(STORED_RESULTS.read_text())
    stored_pools = {}
    for line in STORED_POOLS.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            stored_pools[row["case_id"]] = row

    lat_a, lat_local, lat_ce_d, lat_ce_e, lat_d_total, lat_e_total = [], [], [], [], [], []
    d_cases, e_cases = {}, {}
    d_full, e_full = {}, {}
    cand_ev_d_flags, cand_ev_e_flags = [], []
    pool_sizes_d, pool_sizes_e, new_member_counts = [], [], []
    per_case = []
    compact_pools = []
    cache = {}  # case_id -> retrieval artifacts for Track 2

    for case in cases:
        q = case.question
        t_case = time.time()
        t0 = time.time()
        a_pool = retrieve_system_a_pool(q, transformer)
        lat_a.append((time.time() - t0) * 1000)

        parents = parent_version_ids(a_pool, PARENT_N)
        t0 = time.time()
        local = local_bm25_per_parent_batched(q, parents, W)
        lat_local.append((time.time() - t0) * 1000)
        fused_e, new_ids, a_ids = merge_union_rrf(a_pool, local)
        if not a_ids.issubset({h.chunk_id for h in fused_e}):
            raise SystemExit(f"STOP: additive integrity failed on {case.case_id}")

        a_by_id = {h.chunk_id: h for h in a_pool}

        t0 = time.time()
        a_ce = ce.score_pairs(q, [h.text for h in a_pool])
        lat_ce_d.append((time.time() - t0) * 1000)
        d_rows_in = [
            hit_as_row(
                hit, a_rank=int(hit.rank), a_score=float(hit.score),
                ce_score=float(score), in_a_pool=True, origin="a_pool",
            )
            for hit, score in zip(a_pool, a_ce, strict=True)
        ]
        d_rows = apply_blend(d_rows_in)
        for r in d_rows:
            r["d_rank"] = r["blend_rank"]
        lat_d_total.append((time.time() - t_case) * 1000 - lat_local[-1])

        ce_by_id = {h.chunk_id: float(s) for h, s in zip(a_pool, a_ce, strict=True)}
        new_hits = [h for h in fused_e if h.chunk_id not in ce_by_id]
        t0 = time.time()
        if new_hits:
            new_scores = ce.score_pairs(q, [h.text for h in new_hits])
            for h, s in zip(new_hits, new_scores, strict=True):
                ce_by_id[h.chunk_id] = float(s)
        lat_ce_e.append(lat_ce_d[-1] + (time.time() - t0) * 1000)

        e_rows = blend_union(fused_e, a_ids, a_by_id, ce_by_id, "e_rank")
        lat_e_total.append((time.time() - t_case) * 1000)

        pool_sizes_d.append(len(a_pool))
        pool_sizes_e.append(len(fused_e))
        new_member_counts.append(len(new_ids))

        a_pool_rows = [
            hit_as_row(h, pool_rank=int(h.rank), a_rank=int(h.rank), a_score=float(h.score))
            for h in a_pool
        ]
        e_pool_rows = [
            hit_as_row(h, pool_rank=int(h.rank), a_rank=int(h.rank), a_score=float(h.score))
            for h in fused_e
        ]

        d_scored = score_system(case, d_rows, "d_rank", a_pool, gold_cover)
        for i, ref in enumerate(case.expected_evidence):
            d_scored["spans"][i]["pool_rank"] = first_span_rank(a_pool_rows, ref, "pool_rank")
            d_scored["spans"][i]["in_pool"] = span_in_hits(a_pool, ref)

        e_scored = score_system(case, e_rows, "e_rank", fused_e, gold_cover)
        for i, ref in enumerate(case.expected_evidence):
            e_scored["spans"][i]["pool_rank"] = first_span_rank(e_pool_rows, ref, "pool_rank")
            e_scored["spans"][i]["in_pool"] = span_in_hits(fused_e, ref)

        d_cases[case.case_id] = d_scored
        e_cases[case.case_id] = e_scored
        d_full[case.case_id] = d_scored["fully_recalled"]
        e_full[case.case_id] = e_scored["fully_recalled"]
        cand_ev_d_flags.extend(d_scored["cand_ev_span_flags"])
        cand_ev_e_flags.extend(e_scored["cand_ev_span_flags"])

        span_rows = []
        for i, ref in enumerate(case.expected_evidence):
            d_row = next((r for r in d_rows if dict_overlaps(r, ref)), None)
            e_row = next((r for r in e_rows if dict_overlaps(r, ref)), None)
            span_rows.append(
                {
                    "span_index": i,
                    "covering_chunk_ids": gold_cover[case.case_id][i],
                    "d_rank": d_scored["spans"][i]["rank"],
                    "e_rank": e_scored["spans"][i]["rank"],
                    "d_pool_rank": d_scored["spans"][i]["pool_rank"],
                    "e_pool_rank": e_scored["spans"][i]["pool_rank"],
                    "in_d_pool": d_scored["spans"][i]["in_pool"],
                    "in_e_pool": e_scored["spans"][i]["in_pool"],
                    "d_in_top_10": d_scored["spans"][i]["within_10"],
                    "e_in_top_10": e_scored["spans"][i]["within_10"],
                    "new_union_member": bool(e_row and not e_row["in_a_pool"])
                    if e_row
                    else (not d_scored["spans"][i]["in_pool"] and e_scored["spans"][i]["in_pool"]),
                }
            )
        destructions = [s for s in span_rows if s["d_rank"] == 1 and not s["e_in_top_10"]]
        rec = {
            "case_id": case.case_id,
            "d_full": d_full[case.case_id],
            "e_full": e_full[case.case_id],
            "parents": parents,
            "n_parents": len(parents),
            "a_pool_size": len(a_pool),
            "e_pool_size": len(fused_e),
            "n_new_union_members": len(new_ids),
            "additive_integrity": a_ids.issubset({h.chunk_id for h in fused_e}),
            "spans": span_rows,
            "rank1_destruction_vs_D": destructions,
            "local_per_parent": {
                vid: [h.chunk_id for h in hits] for vid, hits in local.items()
            },
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
                    for r in d_rows if r["d_rank"] <= TOP_K
                ],
                "e_top10": [
                    {"chunk_id": r["chunk_id"], "version_id": r["version_id"], "e_rank": r["e_rank"]}
                    for r in e_rows if r["e_rank"] <= TOP_K
                ],
            }
        )
        cache[case.case_id] = {
            "case": case,
            "a_pool": a_pool,
            "local": local,
            "a_ids": a_ids,
            "a_by_id": a_by_id,
            "ce_by_id": ce_by_id,
            "d_rows": d_rows,
            "d_scored": d_scored,
            "d_full": d_full[case.case_id],
            "lat_a": lat_a[-1],
            "lat_local": lat_local[-1],
            "lat_ce_d": lat_ce_d[-1],
            "lat_ce_e": lat_ce_e[-1],
            "n_new_e": len(new_ids),
        }
        print(
            f"{case.case_id} D={int(d_full[case.case_id])} E={int(e_full[case.case_id])} "
            f"pool {len(a_pool)}->{len(fused_e)} new={len(new_ids)} "
            f"local_ms={lat_local[-1]:.0f} E_ms={lat_e_total[-1]:.0f}",
            flush=True,
        )

    hold_mid = holdout_log_state()
    if hold_mid != hold_before:
        raise SystemExit(f"STOP: holdout log changed during Track 1 {hold_before} -> {hold_mid}")

    m_d = metrics_from_cases(
        d_cases, "rematerialized frozen SYSTEM-D-GUARD-BLEND on A-pool-100",
        D_HASH, cand_ev_d_flags, pool_sizes_d, _mean(lat_d_total),
    )
    m_e = metrics_from_cases(
        e_cases, "Track-1 batched-local SYSTEM-E-WITHIN-DOC",
        e_hash, cand_ev_e_flags, pool_sizes_e, _mean(lat_e_total),
        extra={"new_union_members_mean": round(statistics.mean(new_member_counts), 2)},
    )
    gate = compare_track1(per_case, compact_pools, stored_results, stored_pools, m_d, m_e)
    latency_t1 = {
        "A_retrieval_mean": _mean(lat_a),
        "local_bm25_mean": _mean(lat_local),
        "CE_D_pool_mean": _mean(lat_ce_d),
        "CE_E_union_mean": _mean(lat_ce_e),
        "D_total_mean": _mean(lat_d_total),
        "E_total_mean": _mean(lat_e_total),
        "stored_E_total_mean": 16604.3,
        "stored_local_bm25_mean": 6077.6,
    }
    track1_payload = {
        "experiment_id": "EXP-018B",
        "track": 1,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "SCORE_PRESERVING": gate["SCORE_PRESERVING"],
        "preregistration_json_sha256": PREREG_JSON_SHA,
        "system_e_config_hash": e_hash,
        "method": (
            "lexical_search once with version_ids=all parents, k=14209, then "
            "top-W=20 per parent (same _LEXICAL_SQL full-corpus IDF). "
            "Does not reuse SYSTEM-A global top-50 BM25."
        ),
        "equivalence": gate,
        "metrics_rematerialized": {"D": m_d, "E": m_e},
        "metrics_stored_EXP018": {
            "D": stored_results["metrics"]["D"],
            "E": stored_results["metrics"]["E"],
        },
        "latency_ms": latency_t1,
        "holdout_access_log_before": hold_before,
        "holdout_access_log_after_track1": hold_mid,
        "holdout_log_unchanged": hold_mid == hold_before,
        "n": 50,
    }
    track1_json.write_text(json.dumps(track1_payload, indent=2, default=str) + "\n", encoding="utf-8")

    t1_lines = [
        "# EXP-018B Track 1 — score-preserving local BM25",
        "",
        f"Timestamp: {track1_payload['timestamp']} UTC. "
        f"SCORE_PRESERVING=`{gate['SCORE_PRESERVING']}`.",
        "",
        f"Method: one `_LEXICAL_SQL` call per query with `version_ids=all parents`, "
        f"then top-W={W} per parent. Full-corpus IDF. Not A's top-50 BM25.",
        "",
        f"Union membership ok: {gate['union_membership_ok']}/50. "
        f"Parents ok: {gate['parents_ok']}/50. "
        f"e_top10 ok: {gate['e_top10_ok']}/50. "
        f"Gold e_rank ok: {gate['gold_e_rank_ok']}. "
        f"Local-order proxy ok: {gate['local_order_proxy_ok']}/50.",
        "",
        gate["local_order_note"],
        "",
        "## Metrics vs stored EXP-018",
        "",
        f"- D strict R@10 remat {m_d['strict_recall_at_10']} stored {stored_results['metrics']['D']['strict_recall_at_10']}",
        f"- E strict R@10 remat {m_e['strict_recall_at_10']} stored {stored_results['metrics']['E']['strict_recall_at_10']}",
        f"- D cand R@100 remat {m_d['candidate_evidence_spans']} stored {stored_results['metrics']['D']['candidate_evidence_spans']}",
        f"- E cand R@100 remat {m_e['candidate_evidence_spans']} stored {stored_results['metrics']['E']['candidate_evidence_spans']}",
        f"- E span R@10 remat {m_e['macro_span_recall']} stored {stored_results['metrics']['E']['macro_span_recall']}",
        f"- E MRR remat {m_e['mrr']} stored {stored_results['metrics']['E']['mrr']}",
        f"- E doc recall remat {m_e['document_recall']} stored {stored_results['metrics']['E']['document_recall']}",
        "",
        "## Latency",
        "",
        f"- A/global: {latency_t1['A_retrieval_mean']} ms (stored 357.5)",
        f"- local BM25: {latency_t1['local_bm25_mean']} ms (stored 6077.6)",
        f"- CE E union: {latency_t1['CE_E_union_mean']} ms (stored 10163.7)",
        f"- E total: {latency_t1['E_total_mean']} ms (stored 16604.3)",
        "",
    ]
    if gate["per_query_mismatches"] or gate["metric_mismatches"]:
        t1_lines.append("## Mismatches")
        t1_lines.append("")
        t1_lines.append(json.dumps({"per_query": gate["per_query_mismatches"][:20],
                                    "metrics": gate["metric_mismatches"]}, indent=2, default=str))
        t1_lines.append("")
        t1_lines.append("SCORE_PRESERVING=false. Track 2 not run.")
    else:
        t1_lines.append("No mismatches. Track 2 may run.")
    track1_md.write_text("\n".join(t1_lines) + "\n", encoding="utf-8")
    print("TRACK1 SCORE_PRESERVING", gate["SCORE_PRESERVING"], "local_ms", latency_t1["local_bm25_mean"], flush=True)

    track2 = None
    selected = None
    if not gate["SCORE_PRESERVING"]:
        hold_after = holdout_log_state()
        payload = {
            "experiment_id": "EXP-018B",
            "SCORE_PRESERVING": False,
            "track_2_run": False,
            "stop_reason": "Track 1 equivalence gate failed",
            "track1": track1_payload,
            "selected_L": None,
            "holdout_access_log_before": hold_before,
            "holdout_access_log_after": hold_after,
            "holdout_log_unchanged": hold_after == hold_before,
            "runtime_seconds": round(time.time() - started, 1),
        }
        results_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
        report_path.write_text(
            "# EXP-018B\n\nTrack 1 SCORE_PRESERVING=false. Track 2 not run. See "
            "EXP-018B-track1-equivalence.md.\n",
            encoding="utf-8",
        )
        print("STOP after Track 1 failure", flush=True)
        return 0

    # ---------- Track 2 ----------
    l_results = {}
    for L in L_VALUES:
        l_cases = {}
        l_full = {}
        cand_flags = []
        pool_sizes = []
        additive_counts = []
        ce_lat_est = []
        total_lat_est = []
        per_l = []
        diag = {}
        rank1 = []
        for case in cases:
            art = cache[case.case_id]
            a_pool = art["a_pool"]
            a_ids = art["a_ids"]
            extras = additive_extras_ordered(art["local"], a_ids)
            selected_extras = extras[:L]
            capped_local = cap_local_lists(art["local"], a_ids, selected_extras)
            fused, new_ids, _ = merge_union_rrf(a_pool, capped_local)
            missing_ce = [h for h in fused if h.chunk_id not in art["ce_by_id"]]
            if missing_ce:
                scores = ce.score_pairs(case.question, [h.text for h in missing_ce])
                for h, s in zip(missing_ce, scores, strict=True):
                    art["ce_by_id"][h.chunk_id] = float(s)
            rows = blend_union(fused, a_ids, art["a_by_id"], art["ce_by_id"], "e_rank")
            e_pool_rows = [
                hit_as_row(h, pool_rank=int(h.rank), a_rank=int(h.rank), a_score=float(h.score))
                for h in fused
            ]
            scored = score_system(case, rows, "e_rank", fused, gold_cover)
            for i, ref in enumerate(case.expected_evidence):
                scored["spans"][i]["pool_rank"] = first_span_rank(e_pool_rows, ref, "pool_rank")
                scored["spans"][i]["in_pool"] = span_in_hits(fused, ref)
            l_cases[case.case_id] = scored
            l_full[case.case_id] = scored["fully_recalled"]
            cand_flags.extend(scored["cand_ev_span_flags"])
            pool_sizes.append(len(fused))
            additive_counts.append(len(new_ids))
            n_new_e = max(art["n_new_e"], 1)
            ce_est = art["lat_ce_d"] + (art["lat_ce_e"] - art["lat_ce_d"]) * (len(new_ids) / n_new_e)
            ce_lat_est.append(ce_est)
            total_lat_est.append(art["lat_a"] + art["lat_local"] + ce_est)
            span_rows = []
            for i, ref in enumerate(case.expected_evidence):
                span_rows.append(
                    {
                        "span_index": i,
                        "d_rank": art["d_scored"]["spans"][i]["rank"],
                        "e_rank": scored["spans"][i]["rank"],
                        "e_pool_rank": scored["spans"][i]["pool_rank"],
                        "in_d_pool": art["d_scored"]["spans"][i]["in_pool"],
                        "in_e_pool": scored["spans"][i]["in_pool"],
                        "d_in_top_10": art["d_scored"]["spans"][i]["within_10"],
                        "e_in_top_10": scored["spans"][i]["within_10"],
                    }
                )
            destructions = [s for s in span_rows if s["d_rank"] == 1 and not s["e_in_top_10"]]
            rank1.extend({"case_id": case.case_id, **s} for s in destructions)
            per_l.append(
                {
                    "case_id": case.case_id,
                    "d_full": art["d_full"],
                    "e_full": scored["fully_recalled"],
                    "n_additive": len(new_ids),
                    "union_size": len(fused),
                    "n_extras_available": len(extras),
                    "spans": span_rows,
                }
            )
            if case.case_id in DIAGNOSTIC_IDS:
                covering = gold_cover[case.case_id][0]
                extra_pos = None
                for i, h in enumerate(extras):
                    if h.chunk_id in covering:
                        extra_pos = i  # 0-based among extras
                        break
                diag[case.case_id] = {
                    "DIAGNOSTIC_ONLY": True,
                    "in_pool": scored["spans"][0]["in_pool"],
                    "blend_rank": scored["spans"][0]["rank"],
                    "pool_rank": scored["spans"][0]["pool_rank"],
                    "additive_extra_index_0based": extra_pos,
                    "selected_by_L": extra_pos is not None and extra_pos < L,
                    "covering_chunk_ids": covering,
                }

        pair = paired(d_full, l_full)
        m = metrics_from_cases(
            l_cases, f"EXP-018B Track-2 L={L} additive cap",
            e_hash, cand_flags, pool_sizes, _mean(total_lat_est),
            extra={
                "new_union_members_mean": round(statistics.mean(additive_counts), 2),
                "additive_count_mean": round(statistics.mean(additive_counts), 2),
            },
        )
        cand_n = sum(cand_flags)
        cand_d = len(cand_flags)
        qualifies = (cand_n >= 44) and (len(pair["regressions"]) == 0)
        l_results[str(L)] = {
            "L": L,
            "L_means": "additive local passages per query after dedupe excluding A-pool-100",
            "primary": {
                "candidate_gold_span_recall_at_100": f"{cand_n}/{cand_d}",
                "n": cand_n,
                "d": cand_d,
            },
            "secondary": {
                "strict_recall_at_10": m["strict_recall_at_10"],
                "span_recall_at_10": m["macro_span_recall"],
                "mrr": m["mrr"],
                "document_recall": m["document_recall"],
                "rescues_vs_D": pair["rescues"],
                "regressions_vs_D": pair["regressions"],
                "rank1_destructions": rank1,
                "rank1_destruction_count": len(rank1),
                "mean_additive_count": round(statistics.mean(additive_counts), 2),
                "mean_union_size": round(statistics.mean(pool_sizes), 2),
                "A_global_latency_ms": latency_t1["A_retrieval_mean"],
                "local_BM25_latency_ms": latency_t1["local_bm25_mean"],
                "CE_latency_ms": _mean(ce_lat_est),
                "total_latency_ms": _mean(total_lat_est),
                "CE_latency_note": (
                    "CE scores reused from Track 1 (capped union is a subset). "
                    "CE latency estimated per query as CE_D + (CE_E-CE_D)*(n_additive_L/n_additive_E)."
                ),
            },
            "metrics": m,
            "qualifies": qualifies,
            "diagnostic_only": diag,
            "per_case": per_l,
            "paired_vs_D": pair,
        }
        print(
            f"L={L} cand={cand_n}/{cand_d} strict={m['strict_recall_at_10']} "
            f"reg={pair['regressions'] or '—'} rescue={pair['rescues'] or '—'} "
            f"qualifies={qualifies}",
            flush=True,
        )

    selected_L = None
    for L in L_VALUES:
        if l_results[str(L)]["qualifies"]:
            selected_L = L
            break
    selected = {
        "selected_L": selected_L,
        "rule": "smallest L in {10,20,40} with cand R@100 >= 44/50 AND 0 strict R@10 regressions vs D",
        "threshold_provenance": (
            ">=44/50 preregistered after seeing EXP-018 development 45/50; "
            "development-stage criterion, not independent validation"
        ),
        "do_not_require_rescue_ids": True,
        "do_not_require_R10_improvement_vs_D": True,
        "if_none": "none; EXP-018 remains MECHANISM_SUPPORTED; capped variants not promoted",
    }

    hold_after = holdout_log_state()
    if hold_after != hold_before:
        raise SystemExit(f"STOP: holdout log changed {hold_before} -> {hold_after}")
    if _sha(D_FREEZE) != D_GUARD_SHA_AT_FREEZE or _sha(D_RELEASE) != D_RELEASE_SHA_AT_FREEZE:
        raise SystemExit("STOP: D freeze files mutated")
    if _sha(E_FILE) != e_file_sha_before:
        raise SystemExit("STOP: SYSTEM-E-WITHIN-DOC.json mutated")

    payload = {
        "experiment_id": "EXP-018B",
        "phase": "track1_batched_local_bm25_plus_track2_additive_cap",
        "split": "v2-devset-001/development",
        "n": 50,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "preregistration_json_sha256": PREREG_JSON_SHA,
        "chatgpt_approved_revision_timestamp_et": "2026-08-31T23:22:00-04:00",
        "SCORE_PRESERVING": True,
        "track_2_run": True,
        "system_a_config_hash": A_HASH,
        "system_d_config_hash": D_HASH,
        "system_e_config_hash": e_hash,
        "L_values": list(L_VALUES),
        "tuned_after_seeing_scores": False,
        "validation_loaded": False,
        "holdout_loaded": False,
        "holdout_json_opened": False,
        "holdout_access_log_before": hold_before,
        "holdout_access_log_after": hold_after,
        "holdout_log_unchanged": True,
        "embedding": emb,
        "environment": env_fingerprint(emb),
        "cross_encoder": {
            "name": CE_NAME,
            "revision": CE_REVISION,
            "artifact_sha256": CE_SHA256,
            "pair_score_stable": ce_stable,
        },
        "track1": {
            "SCORE_PRESERVING": True,
            "latency_ms": latency_t1,
            "metrics_E": m_e,
            "metrics_D": m_d,
            "equivalence": {k: gate[k] for k in gate if k != "per_query_mismatches"},
        },
        "D_baseline": m_d,
        "E_uncapped_track1": m_e,
        "L": {str(L): {k: v for k, v in l_results[str(L)].items() if k != "per_case"} | {
            "n_cases": 50
        } for L in L_VALUES},
        "L_per_case": {str(L): l_results[str(L)]["per_case"] for L in L_VALUES},
        "selection": selected,
        "diagnostic_only_ids": list(DIAGNOSTIC_IDS),
        "freeze_files_untouched": {
            "SYSTEM-D-GUARD.json_sha256": _sha(D_FREEZE),
            "SYSTEM-D-RELEASE.json_sha256": _sha(D_RELEASE),
            "SYSTEM-E-WITHIN-DOC.json_sha256": _sha(E_FILE),
        },
        "runtime_seconds": round(time.time() - started, 1),
    }
    results_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    def row(label, m, cand, lat):
        return (
            f"| {label} | {m['strict_recall_at_10']} | {m['macro_span_recall']:.4f} | "
            f"{m['mrr']:.4f} | {m['document_recall']:.4f} | {cand} | "
            f"{m.get('pool_size_mean', 0):.1f} | {lat} |"
        )

    lines = [
        "# EXP-018B — within-document efficiency + score-preserving optimization",
        "",
        f"Timestamp: {payload['timestamp']} UTC. Dataset: V2-DEVSET-001 n=50 only. "
        f"ChatGPT approved revision 2026-08-31 23:22 ET. "
        f"Prereg json sha256 `{PREREG_JSON_SHA}`.",
        "",
        "gold150-v1 holdout.json not opened. gold150-v1/development not loaded. "
        "Validation not loaded. SYSTEM-D not edited. No extra L. No retune.",
        "",
        f"Holdout access log before/after: {hold_before['log_bytes']}/{hold_after['log_bytes']} bytes "
        f"(sha {hold_before['log_sha256']} unchanged={hold_after == hold_before}).",
        "",
        "## Track 1",
        "",
        f"**SCORE_PRESERVING = `{gate['SCORE_PRESERVING']}`**",
        "",
        f"Local BM25 mean {latency_t1['local_bm25_mean']} ms vs stored EXP-018 6077.6 ms. "
        f"E total {latency_t1['E_total_mean']} ms vs stored 16604.3 ms.",
        f"Union/e_top10/parents: {gate['union_membership_ok']}/50, {gate['e_top10_ok']}/50, {gate['parents_ok']}/50.",
        "",
        "## Track 2 caps",
        "",
        "| V | strict R@10 | span R@10 | MRR | doc recall | cand R@100 | union mean | total ms |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        row("D", m_d, m_d["candidate_evidence_spans"], latency_t1["D_total_mean"]),
        row("E uncapped (T1)", m_e, m_e["candidate_evidence_spans"], latency_t1["E_total_mean"]),
    ]
    for L in L_VALUES:
        r = l_results[str(L)]
        lines.append(row(
            f"L={L}",
            r["metrics"],
            r["primary"]["candidate_gold_span_recall_at_100"],
            r["secondary"]["total_latency_ms"],
        ))
    lines += ["", "## Per-L secondary + gate", ""]
    for L in L_VALUES:
        r = l_results[str(L)]
        sec = r["secondary"]
        lines.append(
            f"- **L={L}** cand {r['primary']['candidate_gold_span_recall_at_100']}; "
            f"strict {sec['strict_recall_at_10']}; span {sec['span_recall_at_10']}; "
            f"MRR {sec['mrr']}; doc {sec['document_recall']}; "
            f"rescues vs D {sec['rescues_vs_D'] or '—'}; "
            f"regressions vs D {sec['regressions_vs_D'] or '—'}; "
            f"rank-1 destructions {sec['rank1_destruction_count']}; "
            f"mean additive {sec['mean_additive_count']}; mean union {sec['mean_union_size']}; "
            f"A {sec['A_global_latency_ms']} / local {sec['local_BM25_latency_ms']} / "
            f"CE {sec['CE_latency_ms']} / total {sec['total_latency_ms']} ms; "
            f"qualifies=`{r['qualifies']}`."
        )
    lines += ["", "## Selection (preregistered, not retuned)", ""]
    if selected_L is None:
        lines.append("**selected L = none**. No tested cap has cand R@100 >= 44/50 AND 0 strict R@10 regressions vs D.")
        lines.append("EXP-018 remains MECHANISM_SUPPORTED. Capped variants are not promoted.")
    else:
        lines.append(f"**selected L = {selected_L}** (smallest L in {{10,20,40}} that qualifies).")
    lines.append("")
    lines.append("Threshold >=44/50 was preregistered after seeing EXP-018's 45/50; development-stage, not independent validation.")
    lines.append("Four rescue IDs were NOT used as a gate.")
    lines.append("")
    lines.append("## DIAGNOSTIC_ONLY rescue fates")
    lines.append("")
    lines.append("| id | L | in-pool | blend rank | pool rank | extra index (0-based) | selected by L |")
    lines.append("| --- | ---: | --- | ---: | ---: | ---: | --- |")
    for L in L_VALUES:
        for cid in DIAGNOSTIC_IDS:
            d = l_results[str(L)]["diagnostic_only"][cid]
            lines.append(
                f"| {cid} | {L} | {d['in_pool']} | {d['blend_rank']} | {d['pool_rank']} | "
                f"{d['additive_extra_index_0based']} | {d['selected_by_L']} |"
            )
    lines += [
        "",
        "## Hashes",
        "",
        f"- prereg json: `{PREREG_JSON_SHA}`",
        f"- holdout log: `{hold_before['log_sha256']}` (unchanged)",
        f"- SYSTEM-D-GUARD: `{_sha(D_FREEZE)}`",
        f"- SYSTEM-D-RELEASE: `{_sha(D_RELEASE)}`",
        f"- SYSTEM-E-WITHIN-DOC: `{_sha(E_FILE)}`",
        "",
        "No extra L. No EXP-017. No EXP-019. No holdout. No validation.",
        "",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("selected_L", selected_L, "wrote", results_path, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
