#!/usr/bin/env python3
"""EXP-018 development: SYSTEM-E-WITHIN-DOC (amended local-BM25) vs frozen D.

Preregistration + amendment written before any scores. Development n=20 only.
Does not load validation. Does not load holdout. Does not edit D freeze files.
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
    PROBE_DEPTHS,
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
    overlaps,
    parent_version_ids,
    retrieve_system_a_pool,
    system_e_config,
    system_e_hash,
)

OUT_DIR = ROOT / "experiments" / "EXP-018"
DEV_JSONL = ROOT / "experiments" / "EXP-015" / "development.jsonl"
EXP016_RESULTS = ROOT / "experiments" / "EXP-016" / "EXP-016-development-results.json"
NAMED = ("HA-22", "HA-24", "GOLD-B005-11")
D_FREEZE = ROOT / "experiments" / "EXP-016" / "SYSTEM-D-GUARD.json"
D_RELEASE = ROOT / "experiments" / "EVAL-HOLDOUT-001" / "SYSTEM-D-RELEASE.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dict_overlaps(row: dict, ref: EvidenceRef) -> bool:
    return (
        row["version_id"] == ref.version_id
        and list(row["section_path"]) == list(ref.section_path)
        and row["char_start"] < ref.char_end
        and row["char_end"] > ref.char_start
    )


def span_in_hits(hits: list[SearchHit] | list[dict], ref: EvidenceRef) -> bool:
    for h in hits:
        if isinstance(h, dict):
            if dict_overlaps(h, ref):
                return True
        elif overlaps(h, ref):
            return True
    return False


def first_span_rank(rows: list[dict], ref: EvidenceRef, rank_key: str) -> int | None:
    ranks = [r[rank_key] for r in rows if dict_overlaps(r, ref) and r.get(rank_key) is not None]
    return min(ranks) if ranks else None


def hit_as_row(hit: SearchHit, **extra) -> dict:
    row = {
        "chunk_id": hit.chunk_id,
        "version_id": hit.version_id,
        "section_path": list(hit.section_path),
        "char_start": hit.char_start,
        "char_end": hit.char_end,
        "text": hit.text,
    }
    row.update(extra)
    return row


def summarise(per_case: dict, system: str, config_hash_value: str) -> dict:
    all_spans = [s for c in per_case.values() for s in c["spans"]]
    recalls = [c["recall"] for c in per_case.values()]
    return {
        "system": system,
        "config_hash": config_hash_value,
        "macro_span_recall": round(sum(recalls) / len(recalls), 4) if recalls else 0.0,
        "cases_fully_recalled": sum(1 for c in per_case.values() if c["fully_recalled"]),
        "cases_total": len(per_case),
        "strict_recall_at_10": (
            f"{sum(1 for c in per_case.values() if c['fully_recalled'])}/{len(per_case)}"
        ),
        "spans_found_at_10": sum(1 for s in all_spans if s["within_10"]),
        "spans_total": len(all_spans),
        "document_recall": round(
            sum(c["doc_recall"] for c in per_case.values()) / len(per_case), 4
        )
        if per_case
        else 0.0,
        "mrr": round(
            sum((1 / s["rank"] for s in all_spans if s["rank"]), 0.0) / len(all_spans), 4
        )
        if all_spans
        else 0.0,
    }


def paired(control_full: dict, variant_full: dict) -> dict:
    rescues = [cid for cid, ok in variant_full.items() if ok and not control_full[cid]]
    regressions = [cid for cid, ok in variant_full.items() if control_full[cid] and not ok]
    return {
        "rescues": rescues,
        "regressions": regressions,
        "net": len(rescues) - len(regressions),
        "both_correct": [cid for cid, ok in variant_full.items() if ok and control_full[cid]],
        "neither": [cid for cid, ok in variant_full.items() if (not ok) and (not control_full[cid])],
    }


def env_fingerprint(emb: dict) -> dict:
    import platform

    deps = {}
    for name in ("numpy", "onnxruntime", "pgvector", "psycopg", "pydantic", "tokenizers"):
        try:
            mod = __import__(name)
            deps[name] = getattr(mod, "__version__", "unknown")
        except Exception:
            deps[name] = None
    return {
        "host": {
            "os": platform.platform(),
            "python": platform.python_version(),
            "executable": sys.executable,
        },
        "postgres_version": emb["postgres_version"],
        "pgvector_extversion": emb["pgvector_extversion"],
        "known_drift": emb["known_drift"],
        "dependencies": deps,
        "corpus_snapshot": SNAPSHOT,
        "chunk_set": CHUNK_SET,
        "transformer_model": TRANSFORMER_MODEL,
        "transformer_fingerprint": TRANSFORMER_FINGERPRINT,
    }


def main() -> int:
    started = time.time()
    pre_md = OUT_DIR / "EXP-018-preregistration.md"
    pre_json = OUT_DIR / "EXP-018-preregistration.json"
    amend_md = OUT_DIR / "EXP-018-preregistration-amendment.md"
    amend_json = OUT_DIR / "EXP-018-preregistration-amendment.json"
    results_path = OUT_DIR / "EXP-018-development-results.json"
    if not pre_md.exists() or not pre_json.exists():
        raise SystemExit("STOP: original preregistration missing")
    if not amend_md.exists() or not amend_json.exists():
        raise SystemExit("STOP: amendment missing; do not run the 01:23Z dense-within-doc design")
    if results_path.exists():
        raise SystemExit("STOP: results already exist; refusing to overwrite")
    if pre_md.stat().st_mtime > amend_md.stat().st_mtime:
        raise SystemExit("STOP: amendment is older than original prereg; clock/order broken")
    if amend_md.stat().st_mtime > time.time():
        raise SystemExit("STOP: amendment mtime in the future")

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

    emb = embedding_status()
    if not emb["complete"]:
        raise SystemExit(f"STOP: embeddings incomplete: {emb}")

    e_cfg = system_e_config()
    e_hash = system_e_hash()
    if e_hash == D_HASH or e_hash == A_HASH:
        raise SystemExit("STOP: SYSTEM-E hash collided with A or D")

    encoder = TransformerEncoder(max_seq=512).load()
    if encoder.model_version != TRANSFORMER_FINGERPRINT:
        raise SystemExit("STOP: live encoder fingerprint mismatch")
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)
    ce = CrossEncoderReranker()
    probe_q, probe_p = "What is BM25?", "BM25 is a lexical ranking function."
    ce_stable = ce.score_pairs(probe_q, [probe_p])[0] == ce.score_pairs(probe_q, [probe_p])[0]

    cases = [c for c in load_cases(DEV_JSONL) if c.expected_evidence]
    if len(cases) != 20:
        raise SystemExit(f"expected 20 development cases, got {len(cases)}")
    split_ids = json.loads((ROOT / "evals/splits/gold150-v1/development.json").read_text())[
        "case_ids"
    ]
    got_ids = [c.case_id for c in cases]
    if got_ids != split_ids:
        raise SystemExit(f"STOP: development.jsonl ids != development.json: {got_ids}")

    stored016 = json.loads(EXP016_RESULTS.read_text())
    if stored016.get("split") != "gold150-v1/development":
        raise SystemExit("STOP: EXP-016 results are not gold150-v1/development")
    stored_per = {row["case_id"]: row for row in stored016["per_case"]}
    stored_d = stored016["variants"]["D"]
    stored_a = stored016["variants"]["A"]

    gold_cover: dict[str, list[list[str]]] = {}
    for case in cases:
        gold_cover[case.case_id] = [covering_chunk_ids(ref) for ref in case.expected_evidence]

    lat_a, lat_local, lat_ce_d, lat_ce_e, lat_d_total, lat_e_total = [], [], [], [], [], []
    a_cases, d_cases, e_cases = {}, {}, {}
    a_full, d_full, e_full = {}, {}, {}
    per_case = []
    named_traces = {}
    compact_pools = []
    d_identity_mismatches = []
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
        e_by_id = {h.chunk_id: h for h in fused_e}

        # --- rematerialize D on A-pool-100 (frozen D formula) ---
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
        lat_d_total.append((time.time() - t_case) * 1000 - lat_local[-1])  # D does not pay local BM25

        # --- E: CE union, reuse A-pool logits ---
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

        # candidate evidence + scoring vs gold
        def score_system(rows: list[dict], rank_key: str, pool_for_evidence: list) -> dict:
            spans = []
            gold_docs = {ref.version_id for ref in case.expected_evidence}
            top_docs = {r["version_id"] for r in rows if r[rank_key] <= TOP_K}
            for i, ref in enumerate(case.expected_evidence):
                in_pool = span_in_hits(pool_for_evidence, ref)
                rank = first_span_rank(rows, ref, rank_key)
                pool_rank = first_span_rank(
                    pool_for_evidence
                    if pool_for_evidence and isinstance(pool_for_evidence[0], dict)
                    else [
                        {
                            "version_id": h.version_id,
                            "section_path": list(h.section_path),
                            "char_start": h.char_start,
                            "char_end": h.char_end,
                            "pool_rank": h.rank,
                        }
                        for h in pool_for_evidence
                    ],
                    ref,
                    "pool_rank" if not (pool_for_evidence and isinstance(pool_for_evidence[0], dict) and rank_key in pool_for_evidence[0]) else rank_key,
                )
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

        # rebuild pool-rank rows for A/E pools
        a_pool_rows = [
            hit_as_row(h, pool_rank=int(h.rank), a_rank=int(h.rank), a_score=float(h.score))
            for h in a_pool
        ]
        e_pool_rows = [
            hit_as_row(h, pool_rank=int(h.rank), a_rank=int(h.rank), a_score=float(h.score))
            for h in fused_e
        ]

        a_scored = score_system(
            [
                {**hit_as_row(h), "a_rank": int(h.rank)}
                for h in a_pool
            ],
            "a_rank",
            a_pool,
        )
        # fill pool_rank on A using A fused rank
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

        # EXP-016 identity on gold spans
        stored = stored_per[case.case_id]
        for i, sspan in enumerate(stored["spans"]):
            got_a = first_span_rank(d_rows_in, case.expected_evidence[i], "a_rank")
            got_d = first_span_rank(d_rows, case.expected_evidence[i], "d_rank")
            if got_a != sspan.get("a_rank"):
                d_identity_mismatches.append(
                    f"{case.case_id} span{i} A rank {got_a} != stored {sspan.get('a_rank')}"
                )
            if got_d != sspan.get("d_rank"):
                d_identity_mismatches.append(
                    f"{case.case_id} span{i} D rank {got_d} != stored {sspan.get('d_rank')}"
                )
            stored_ce = sspan.get("ce_score")
            got_ce = next(
                (r["ce_score"] for r in d_rows_in if r["chunk_id"] == sspan.get("chunk_id")),
                None,
            )
            if stored_ce is not None and got_ce is not None and abs(got_ce - stored_ce) > 1e-4:
                d_identity_mismatches.append(
                    f"{case.case_id} span{i} CE {got_ce} != stored {stored_ce}"
                )

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
                    "new_union_member": bool(
                        e_row and not e_row["in_a_pool"]
                    )
                    if e_row
                    else (not d_scored["spans"][i]["in_pool"] and e_scored["spans"][i]["in_pool"]),
                    "a_in_top_10": a_scored["spans"][i]["within_10"],
                    "d_in_top_10": d_scored["spans"][i]["within_10"],
                    "e_in_top_10": e_scored["spans"][i]["within_10"],
                }
            )

        destructions_e_vs_d = [
            s
            for s in span_rows
            if s["d_rank"] == 1 and not s["e_in_top_10"]
        ]
        destructions_e_vs_a = [
            s
            for s in span_rows
            if s["a_rank"] == 1 and not s["e_in_top_10"]
        ]

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
        if case.case_id in NAMED:
            named_traces[case.case_id] = rec

        # persist compact pool (no passage text)
        compact_pools.append(
            {
                "case_id": case.case_id,
                "parents": parents,
                "a_pool": [
                    {
                        "chunk_id": r["chunk_id"],
                        "version_id": r["version_id"],
                        "a_rank": r["a_rank"],
                        "a_score": r["a_score"],
                        "ce_score": r["ce_score"],
                        "d_rank": r["d_rank"],
                        "blend_score": r["blend_score"],
                    }
                    for r in d_rows
                ],
                "e_pool": [
                    {
                        "chunk_id": r["chunk_id"],
                        "version_id": r["version_id"],
                        "merge_rrf_rank": r["a_rank"],
                        "merge_rrf_score": r["a_score"],
                        "system_a_rank": r.get("system_a_rank"),
                        "in_a_pool": r["in_a_pool"],
                        "origin": r["origin"],
                        "ce_score": r["ce_score"],
                        "e_rank": r["e_rank"],
                        "blend_score": r["blend_score"],
                    }
                    for r in e_rows
                ],
                "new_union_chunk_ids": new_ids,
                "new_union_ce_logits": {
                    h.chunk_id: ce_by_id[h.chunk_id] for h in new_hits
                },
            }
        )
        print(
            f"{case.case_id} A={int(a_full[case.case_id])} D={int(d_full[case.case_id])} "
            f"E={int(e_full[case.case_id])} pool {len(a_pool)}->{len(fused_e)} "
            f"new={len(new_ids)} E_ms={lat_e_total[-1]:.0f}",
            flush=True,
        )

    hold_after = holdout_log_state()
    if hold_after != hold_before:
        raise SystemExit(f"STOP: holdout log changed during run {hold_before} -> {hold_after}")

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

    d_strict = system_d["cases_fully_recalled"]
    e_strict = system_e["cases_fully_recalled"]
    no_r_at_10_regression = e_strict >= d_strict
    cand_ge = cand_ev_e >= cand_ev_d - 1e-12
    d_pool_complete = cand_ev_d == 1.0
    d_is_20_20 = d_strict == 20 and system_d["spans_found_at_10"] == system_d["spans_total"]
    no_rank1 = len(rank1_vs_d) == 0

    ceiling = bool(d_pool_complete and d_is_20_20 and no_r_at_10_regression)
    qualifies = bool(additive_ok and no_r_at_10_regression and cand_ge and no_rank1)
    mechanism = bool(cand_ev_e > cand_ev_d + 1e-12)
    reject = bool((e_strict < d_strict) or (not additive_ok))

    labels = []
    if reject:
        labels.append("REJECT_AT_DEV")
    if qualifies:
        labels.append("QUALIFIES_FOR_VAL_CONSIDERATION")
    if ceiling:
        labels.append("CEILING_ON_DEV")
    if mechanism:
        labels.append("MECHANISM_SUPPORTED")
    if not labels:
        labels.append("NO_LABEL")

    d_identity_ok = len(d_identity_mismatches) == 0
    if system_d["cases_fully_recalled"] != 20:
        raise SystemExit(
            f"STOP: rematerialized D is {system_d['strict_recall_at_10']}, expected 20/20"
        )

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    latency = {
        "A_retrieval_mean": round(statistics.mean(lat_a), 1),
        "local_bm25_mean": round(statistics.mean(lat_local), 1),
        "CE_D_pool_mean": round(statistics.mean(lat_ce_d), 1),
        "CE_E_union_mean": round(statistics.mean(lat_ce_e), 1),
        "D_total_mean": round(statistics.mean(lat_d_total), 1),
        "E_total_mean": round(statistics.mean(lat_e_total), 1),
        "EXP016_D_mean_recorded": 5774.4,
    }

    differing = [
        rec["case_id"]
        for rec in per_case
        if rec["d_full"] != rec["e_full"]
        or any(s["d_rank"] != s["e_rank"] for s in rec["spans"])
        or rec["a_pool_size"] != rec["e_pool_size"]
        or rec["n_new_union_members"] > 0
        or rec["first_gold_pool_rank_A"] != rec["first_gold_pool_rank_E"]
    ]
    for cid in NAMED:
        if cid not in named_traces:
            named_traces[cid] = next(r for r in per_case if r["case_id"] == cid)
        if cid not in differing:
            # still trace named even if identical
            pass

    metrics_block = {
        "A": {
            "source": "rematerialized frozen SYSTEM-A on gold150-v1/development",
            "config_hash": A_HASH,
            **{k: system_a[k] for k in system_a if k not in ("system", "config_hash")},
            "candidate_evidence_recall": round(cand_ev_d, 4),
            "pool_size_mean": round(statistics.mean(pool_sizes_d), 2),
            "pool_size_max": max(pool_sizes_d),
            "latency_ms_mean": latency["A_retrieval_mean"],
            "stored_EXP016_strict": stored_a["strict_recall_at_10"],
        },
        "D": {
            "source": "rematerialized frozen SYSTEM-D-GUARD-BLEND on same A pools",
            "config_hash": D_HASH,
            **{k: system_d[k] for k in system_d if k not in ("system", "config_hash")},
            "candidate_evidence_recall": round(cand_ev_d, 4),
            "pool_size_mean": round(statistics.mean(pool_sizes_d), 2),
            "pool_size_max": max(pool_sizes_d),
            "latency_ms_mean": latency["D_total_mean"],
            "stored_EXP016_strict": stored_d["strict_recall_at_10"],
            "stored_EXP016_mrr": stored_d["mrr"],
            "identity_vs_EXP016_gold_spans": d_identity_ok,
        },
        "E": {
            "source": "SYSTEM-E-WITHIN-DOC amended local-BM25 union + merge RRF + frozen D blend",
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

    decision = {
        "labels": labels,
        "QUALIFIES_FOR_VAL_CONSIDERATION": qualifies,
        "CEILING_ON_DEV": ceiling,
        "MECHANISM_SUPPORTED": mechanism,
        "REJECT_AT_DEV": reject,
        "honest_gate": {
            "recall_at_10_cannot_improve_on_dev": True,
            "additive_integrity": additive_ok,
            "no_recall_at_10_regression": no_r_at_10_regression,
            "cand_ev_E_ge_D": cand_ge,
            "D_pool_already_complete": d_pool_complete,
            "tied_20_20": e_strict == 20 and d_strict == 20,
            "claimed_retrieval_win": False if (e_strict == d_strict) else e_strict > d_strict,
            "chatgpt_proceed_only_if_recall_improves": "UNMEETABLE_ON_AUTHORIZED_SPLIT",
        },
        "no_system_e_release_freeze": True,
        "validation_loaded": False,
        "holdout_loaded": False,
        "leave_freeze_or_val_to_chatgpt": True,
    }

    system_e_file = {
        "name": "SYSTEM-E-WITHIN-DOC",
        "status": "DEVELOPMENT_CONFIG_NOT_A_RELEASE_FREEZE",
        "release_freeze": False,
        "generated_at": timestamp,
        "config": e_cfg,
        "config_hash": e_hash,
        "system_a_config_hash": A_HASH,
        "system_d_config_hash": D_HASH,
        "snapshot": SNAPSHOT,
        "chunk_set": CHUNK_SET,
        "encoder": {
            "model_id": TRANSFORMER_MODEL,
            "fingerprint": TRANSFORMER_FINGERPRINT,
            "max_seq_length": 512,
        },
        "cross_encoder": {
            "name": CE_NAME,
            "revision": CE_REVISION,
            "artifact": str(CE_ONNX),
            "artifact_sha256": CE_SHA256,
            "runtime": "onnxruntime + HuggingFace tokenizers",
            "precision": "fp32",
            "max_length": MAX_LENGTH,
            "pair_formatting": "[CLS] query [SEP] passage [SEP]",
            "truncation": "longest_first",
            "scoring": "raw sequence-classification logit (Identity); higher=more relevant",
        },
        "blend": {
            "weights_CE": BLEND_CE,
            "weights_A_channel": BLEND_A,
            "A_channel": "merge-RRF on A-pool-100 UNION local BM25",
            "minmax_degenerate": 0.5,
        },
        "parent_n": PARENT_N,
        "W": W,
        "local_retrieval": "BM25_ONLY",
        "development_metrics": metrics_block["E"],
        "decision_labels": labels,
        "note": (
            "Config + hash only. Not a v2 release freeze. Validation and holdout "
            "were not run. Freeze-or-val is a ChatGPT decision."
        ),
    }
    (OUT_DIR / "SYSTEM-E-WITHIN-DOC.json").write_text(
        json.dumps(system_e_file, indent=2) + "\n", encoding="utf-8"
    )

    (OUT_DIR / "EXP-018-pools.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in compact_pools) + "\n",
        encoding="utf-8",
    )
    (OUT_DIR / "EXP-018-per-case.json").write_text(
        json.dumps(per_case, indent=2, default=str) + "\n", encoding="utf-8"
    )

    payload = {
        "experiment_id": "EXP-018",
        "phase": "development_qualification",
        "split": "gold150-v1/development",
        "split_path": "evals/splits/gold150-v1/development.json",
        "projection_path": str(DEV_JSONL.relative_to(ROOT)),
        "n": 20,
        "preregistration": [
            "experiments/EXP-018/EXP-018-preregistration.md",
            "experiments/EXP-018/EXP-018-preregistration.json",
            "experiments/EXP-018/EXP-018-preregistration-amendment.md",
            "experiments/EXP-018/EXP-018-preregistration-amendment.json",
        ],
        "charter": "experiments/RAG-V2/V2-RESEARCH-CHARTER.md",
        "timestamp": timestamp,
        "corpus_snapshot": SNAPSHOT,
        "chunk_set": CHUNK_SET,
        "system_a_config_hash": A_HASH,
        "system_d_config_hash": D_HASH,
        "system_e_config_hash": e_hash,
        "tuned_after_seeing_scores": False,
        "validation_loaded": False,
        "holdout_loaded": False,
        "holdout_access_log_before": hold_before,
        "holdout_access_log_after": hold_after,
        "holdout_log_unchanged": hold_after == hold_before,
        "embedding": emb,
        "environment": env_fingerprint(emb),
        "d_rematerialize_identity_vs_EXP016": {
            "passed": d_identity_ok,
            "mismatches": d_identity_mismatches,
            "rematerialized_strict_20_20": system_d["cases_fully_recalled"] == 20,
        },
        "metrics": metrics_block,
        "candidate_evidence_recall": {
            "D_A_pool": round(cand_ev_d, 4),
            "E_union_pool": round(cand_ev_e, 4),
            "spans_in_D_pool": f"{sum(cand_ev_d_flags)}/{n_spans}",
            "spans_in_E_pool": f"{sum(cand_ev_e_flags)}/{n_spans}",
            "primary": True,
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
        "named_case_traces": {k: named_traces[k] for k in NAMED},
        "differing_or_expanded_cases": differing,
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
        },
    }
    results_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    def row(letter, m, cand):
        return (
            f"| {letter} | {m['strict_recall_at_10']} | {m['macro_span_recall']:.4f} | "
            f"{m['spans_found_at_10']}/{m['spans_total']} | {m['mrr']:.4f} | "
            f"{m['document_recall']:.4f} | {cand:.4f} | {m['pool_size_mean']:.1f}/{m['pool_size_max']} | "
            f"{m['latency_ms_mean']} |"
        )

    report = []
    report.append("# EXP-018 development report")
    report.append("")
    report.append(f"Timestamp: {timestamp} (UTC). Split: gold150-v1/development n=20.")
    report.append("Validation not loaded. Holdout not loaded. SYSTEM-E is **not** a release freeze.")
    report.append(
        f"Holdout access log before/after: {hold_before['log_bytes']}/{hold_after['log_bytes']} bytes "
        f"(sha {hold_before['log_sha256'][:12]}… unchanged={hold_after == hold_before})."
    )
    report.append(
        "Original preregistration 2026-09-01T01:23:45Z kept. Amendment "
        "2026-09-01T01:27:02Z (local BM25 only) is what ran. Amendment mtime "
        "precedes this results file."
    )
    report.append(
        f"Rematerialized D identity vs EXP-016 gold-span ranks: `{d_identity_ok}`. "
        f"D strict {system_d['strict_recall_at_10']}."
    )
    report.append("")
    report.append("## Honest gate")
    report.append("")
    report.append(
        "EXP-016 D is already 20/20 and 23/23 spans@10 on this split. Strict Recall@10 "
        "**cannot improve**. A tied 20/20 is not a retrieval win. ChatGPT's "
        "\"proceed only if Recall@10 improves\" clause is **UNMEETABLE_ON_AUTHORIZED_SPLIT**. "
        "Freeze-or-val is ChatGPT's decision."
    )
    report.append("")
    report.append("## Metrics")
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
        f"Primary (candidate evidence recall): D/A pool {sum(cand_ev_d_flags)}/{n_spans} = "
        f"{cand_ev_d:.4f}; E union {sum(cand_ev_e_flags)}/{n_spans} = {cand_ev_e:.4f}."
    )
    report.append(
        f"Additive integrity: `{additive_ok}`. Rescues vs D: {pair_e_vs_d['rescues'] or '—'}; "
        f"regressions vs D: {pair_e_vs_d['regressions'] or '—'}; net {pair_e_vs_d['net']:+d}."
    )
    report.append(
        f"Rank-1 destruction vs D: {len(rank1_vs_d)}; vs A: {len(rank1_vs_a)}."
    )
    report.append(
        f"E mean latency {latency['E_total_mean']} ms vs rematerialized D "
        f"{latency['D_total_mean']} ms (EXP-016 D recorded 5774.4 ms)."
    )
    report.append("")
    report.append("## Named-case traces")
    report.append("")
    for cid in NAMED:
        rec = named_traces[cid]
        report.append(f"### {cid}")
        report.append("")
        report.append(
            f"A full={rec['a_full']}  D full={rec['d_full']}  E full={rec['e_full']}  "
            f"parents={rec['n_parents']}  pool {rec['a_pool_size']}→{rec['e_pool_size']} "
            f"(+{rec['n_new_union_members']} new)  first-gold-pool A={rec['first_gold_pool_rank_A']} "
            f"E={rec['first_gold_pool_rank_E']}"
        )
        report.append("")
        report.append(
            "| span | cover-chunk | A rank | D pool | E pool | D rank | E rank | "
            "in D pool | in E pool | new | top10 A/D/E |"
        )
        report.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |")
        for s in rec["spans"]:
            cover = s["covering_chunk_ids"][0] if s["covering_chunk_ids"] else None
            report.append(
                f"| {s['span_index']} | `{cover}` | {s['a_rank']} | {s['d_pool_rank']} | "
                f"{s['e_pool_rank']} | {s['d_rank']} | {s['e_rank']} | {s['in_d_pool']} | "
                f"{s['in_e_pool']} | {s['new_union_member']} | "
                f"{s['a_in_top_10']}/{s['d_in_top_10']}/{s['e_in_top_10']} |"
            )
        report.append("")
    if any(rec["case_id"] not in NAMED and rec["d_full"] != rec["e_full"] for rec in per_case):
        report.append("## Cases that differ on strict Recall@10")
        report.append("")
        for rec in per_case:
            if rec["case_id"] not in NAMED and rec["d_full"] != rec["e_full"]:
                report.append(
                    f"- `{rec['case_id']}` D={rec['d_full']} E={rec['e_full']} "
                    f"pool {rec['a_pool_size']}→{rec['e_pool_size']}"
                )
        report.append("")
    report.append("## Decision")
    report.append("")
    report.append("**" + " + ".join(labels) + "**")
    report.append("")
    report.append(f"- QUALIFIES_FOR_VAL_CONSIDERATION: `{qualifies}`")
    report.append(f"- CEILING_ON_DEV: `{ceiling}`")
    report.append(f"- MECHANISM_SUPPORTED: `{mechanism}`")
    report.append(f"- REJECT_AT_DEV: `{reject}`")
    report.append(f"- SYSTEM-E config hash: `{e_hash}`")
    report.append("- SYSTEM-E was **not** frozen as a v2 release. Validation was not run. Holdout was not run.")
    report.append(
        f"- Environment: {emb['postgres_version'].split(',')[0]} / pgvector {emb['pgvector_extversion']} "
        f"(known drift vs 16.13 / 0.6.0)."
    )
    report.append("")
    (OUT_DIR / "EXP-018-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print("labels", labels)
    print("D", system_d["strict_recall_at_10"], "cand", cand_ev_d)
    print("E", system_e["strict_recall_at_10"], "cand", cand_ev_e)
    print("additive", additive_ok, "identity", d_identity_ok)
    print("holdout", hold_before["log_bytes"], hold_after["log_bytes"])
    print("e_hash", e_hash)
    print("wrote", results_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
