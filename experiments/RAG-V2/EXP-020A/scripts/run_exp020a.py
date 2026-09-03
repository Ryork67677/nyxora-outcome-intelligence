#!/usr/bin/env python3
"""EXP-020A: parent-balanced candidate generation on frozen SYSTEM-H.

Preregistration MUST already be hashed. Candidate-generation only.
Does not run CE, blend, coverage selector, MMR, or final top-10.
Does not open NATQ or V1 holdout.json. Does not overwrite SYSTEM-H/G/E.
Does not run EXP-020B.
"""
from __future__ import annotations

import hashlib
import json
import os
import statistics
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-015" / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-018" / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-018B" / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-017" / "scripts"))

from rag_v1.db import connect  # noqa: E402
from rag_v1.embedders_transformer import TransformerEncoder  # noqa: E402
from rag_v1.ids import config_hash  # noqa: E402
from rag_v1.query_cache import CachedQueryEmbedder  # noqa: E402
from rag_v1.systems import FROZEN_HASHES  # noqa: E402
from rag_v1.types import EvidenceRef, EvalCase, SearchHit  # noqa: E402

from local_bm25_batched import (  # noqa: E402
    additive_extras_ordered,
    cap_local_lists,
    local_bm25_per_parent_batched,
)
from projection_retrieval import (  # noqa: E402
    PROJECTION_SET_ID,
    map_to_canonical_extras,
    projection_rrf,
)
from run_exp017 import L, P, load_control_chunks  # noqa: E402
from run_exp018_development import env_fingerprint, span_in_hits  # noqa: E402
from system_e import (  # noqa: E402
    A_HASH,
    CHUNK_SET,
    HOLD_LOG_SHA_AT_PREREG,
    PARENT_N,
    SNAPSHOT,
    TRANSFORMER_FINGERPRINT,
    TRANSFORMER_MODEL,
    W,
    covering_chunk_ids,
    embedding_status,
    holdout_log_state,
    merge_union_rrf,
    parent_version_ids,
    retrieve_system_a_pool,
)

OUT_DIR = ROOT / "experiments" / "RAG-V2" / "EXP-020A"
VAL_JSONL = ROOT / "evals" / "splits" / "natq-001" / "validation.jsonl"
VAL_JSON = ROOT / "evals" / "splits" / "natq-001" / "validation.json"
H_FILE = ROOT / "experiments" / "RAG-V2" / "SYSTEM-H-V2-DEV-CANDIDATE" / "SYSTEM-H-V2-DEV-CANDIDATE.json"
I_FILE = (
    ROOT
    / "experiments"
    / "RAG-V2"
    / "SYSTEM-I-PARENT-BALANCED-CANDIDATES"
    / "SYSTEM-I-PARENT-BALANCED-CANDIDATES.json"
)
G_FILE = ROOT / "experiments" / "EXP-019A" / "SYSTEM-G-PROJECTION-PRIOR.json"
G_CE_D1 = ROOT / "experiments" / "PERF-003" / "SYSTEM-G-CE-D1.json"
E_L10_FILE = ROOT / "experiments" / "EXP-018B" / "SYSTEM-E-L10-WITHIN-DOC.json"
PREREG_JSON = OUT_DIR / "EXP-020A-preregistration.json"
PREREG_MD = OUT_DIR / "EXP-020A-preregistration.md"
H_REPORT = ROOT / "experiments" / "RAG-V2" / "EVAL-NATQ-VAL-001" / "EVAL-NATQ-VAL-001-REPORT.json"
H_POOLS = ROOT / "experiments" / "RAG-V2" / "EVAL-NATQ-VAL-001" / "logs" / "EVAL-NATQ-VAL-001-pools.jsonl"
NATQ_HOLD_LOG = ROOT / "evals" / "splits" / "natq-001" / "holdout-access.log.jsonl"
NATQ_HOLD_LOCK = ROOT / "evals" / "splits" / "natq-001" / "holdout.lock.json"
V1_HOLD_LOG = ROOT / "evals" / "splits" / "gold150-v1" / "holdout-access.log.jsonl"

PREREG_JSON_SHA = "f0501380ff0a44526eb8b1646b90eb28129a4ba9f37a04521c85cc03399d8dfc"
H_CONFIG_HASH = "7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a"
H_FILE_SHA = "7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475"
I_CONFIG_HASH = "9103a51eaaebcbc581df452279ea06c880abb7524053606428dfd77649d4b3d6"
I_FILE_SHA = "63a78f1d88876c3f55033dc13ce3e6bad1fe768ce5252d315f31652769a9fd19"
VAL_SHA = "a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6"
NATQ_LOG_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
V1_LOG_SHA = "45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3"
NATQ_LOCK_SHA = "03e0d5749e61e73e6b9582109a74a4a9672610b7bf794daf25f46999e5ad40b2"
G_FILE_SHA = "7f4ff6db09f32e55cac820cbc00d87ce2ae91886d444c3bad20ac3e04c7f0f61"
G_CE_D1_SHA = "cf0c985c5f7738e7fc5422039fd6940621d8dcd8f91de41abe3784ac53a6a7ec"
E_L10_SHA = "efbd3bc1cc73d3c342a607ef75135515d13680b31fd6058e8f1c13e80d13ed89"
PROJ_CFG_HASH = "7fd5034c9510a1e08ec76bd22b020703c586dd12e7c02659397df05c5c365a8e"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mean(xs: list[float], ndigits: int = 4) -> float:
    return round(statistics.mean(xs), ndigits) if xs else 0.0


def _median(xs: list[float], ndigits: int = 4) -> float:
    return round(statistics.median(xs), ndigits) if xs else 0.0


def natq_holdout_log_state() -> dict:
    log_bytes = NATQ_HOLD_LOG.read_bytes() if NATQ_HOLD_LOG.exists() else b""
    lock_bytes = NATQ_HOLD_LOCK.read_bytes() if NATQ_HOLD_LOCK.exists() else b""
    return {
        "log_bytes": len(log_bytes),
        "log_sha256": hashlib.sha256(log_bytes).hexdigest() if NATQ_HOLD_LOG.exists() else None,
        "lock_bytes": len(lock_bytes),
        "lock_sha256": hashlib.sha256(lock_bytes).hexdigest() if NATQ_HOLD_LOCK.exists() else None,
        "holdout_json_opened": False,
    }


def verify_projection_set() -> dict:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT projection_set_id, config_hash, window_tokens, stride_tokens
            FROM search_projection_set WHERE projection_set_id=%s
            """,
            (PROJECTION_SET_ID,),
        )
        row = cur.fetchone()
        cur.execute(
            "SELECT count(*) FROM search_projection WHERE projection_set_id=%s",
            (PROJECTION_SET_ID,),
        )
        n = cur.fetchone()[0]
        cur.execute("SELECT snapshot_id FROM corpus_snapshot")
        snaps = [r[0] for r in cur.fetchall()]
        cur.execute(
            """
            SELECT count(*) FILTER (WHERE cardinality(covering_chunk_ids) > 1),
                   count(*) FILTER (WHERE cardinality(covering_chunk_ids) = 1),
                   max(cardinality(covering_chunk_ids))
            FROM search_projection WHERE projection_set_id=%s
            """,
            (PROJECTION_SET_ID,),
        )
        n_multi, n_single, max_n = cur.fetchone()
    if row is None:
        raise SystemExit("STOP: projection set missing")
    pid, cfg_hash, window, stride = row
    ok = (
        pid == PROJECTION_SET_ID
        and cfg_hash == PROJ_CFG_HASH
        and n == 18057
        and window == 448
        and stride == 224
        and SNAPSHOT in snaps
        and snaps == [SNAPSHOT]
    )
    return {
        "projection_set_id": pid,
        "config_hash": cfg_hash,
        "n": n,
        "window_tokens": window,
        "stride_tokens": stride,
        "snapshots": snaps,
        "snapshot_ok": snaps == [SNAPSHOT],
        "n_covering_gt_1": int(n_multi),
        "n_covering_eq_1": int(n_single),
        "max_covering_n": int(max_n),
        "ok": ok,
    }


def load_validation() -> tuple[list[dict], list[EvalCase]]:
    raw: list[dict] = []
    for line in VAL_JSONL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            raw.append(json.loads(line))
    cases: list[EvalCase] = []
    for row in raw:
        ev = [
            EvidenceRef(
                version_id=e["version_id"],
                section_path=list(e["section_path"]),
                char_start=int(e["char_start"]),
                char_end=int(e["char_end"]),
            )
            for e in row["expected_evidence"]
        ]
        cases.append(
            EvalCase(
                case_id=row["case_id"],
                category=row.get("category") or "normal",
                question=row["question"],
                expected_evidence=ev,
                expected_abstain=bool(row.get("expected_abstain")),
            )
        )
    return raw, cases


def tags_of(row: dict) -> list[str]:
    out: list[str] = []
    for key in ("coverage_tags", "stress_types"):
        for t in row.get(key) or []:
            if t not in out:
                out.append(t)
    return out


def hits_from_ids(ids: list[str], chunks_by_id: dict) -> list[SearchHit]:
    out: list[SearchHit] = []
    for i, cid in enumerate(ids, start=1):
        rec = chunks_by_id[cid]
        out.append(
            SearchHit(
                chunk_id=rec["chunk_id"],
                version_id=rec["version_id"],
                section_path=rec["section_path"],
                char_start=rec["char_start"],
                char_end=rec["char_end"],
                text=rec["text"],
                score=0.0,
                rank=i,
                retriever="union",
            )
        )
    return out


def parent_top1_projection(fused_p: list[SearchHit], parent_vid: str, chunks_by_id: dict) -> str | None:
    parent_hits = [h for h in fused_p if h.version_id == parent_vid]
    if not parent_hits:
        return None
    mapped = map_to_canonical_extras(parent_hits, set(), p=10**9)
    for cid in mapped["C_P"]:
        rec = chunks_by_id.get(cid)
        if rec is None:
            continue
        if rec["version_id"] == parent_vid:
            return cid
    return None


def lane_of_span(cover: list[str], bm25_ids: set[str], proj_ids: set[str]) -> str:
    in_b = any(c in bm25_ids for c in cover)
    in_p = any(c in proj_ids for c in cover)
    if in_b and in_p:
        return "both"
    if in_b:
        return "BM25"
    if in_p:
        return "projection"
    return "neither"


def main() -> int:
    started = time.time()
    results_path = OUT_DIR / "EXP-020A-REPORT.json"
    report_path = OUT_DIR / "EXP-020A-REPORT.md"
    pools_path = OUT_DIR / "logs" / "EXP-020A-pools.jsonl"
    if results_path.exists() or report_path.exists():
        raise SystemExit("STOP: EXP-020A results already exist; refusing second run")
    if not PREREG_JSON.exists() or not PREREG_MD.exists():
        raise SystemExit("STOP: preregistration missing; do not score")
    got_pre = _sha(PREREG_JSON)
    if got_pre != PREREG_JSON_SHA:
        raise SystemExit(f"STOP: prereg json sha {got_pre} != frozen {PREREG_JSON_SHA}")

    natq_before = natq_holdout_log_state()
    v1_before = holdout_log_state()
    if natq_before["log_bytes"] != 0 or natq_before["log_sha256"] != NATQ_LOG_SHA:
        raise SystemExit(f"STOP: NATQ holdout access log not empty before run: {natq_before}")
    if natq_before["lock_sha256"] != NATQ_LOCK_SHA:
        raise SystemExit(f"STOP: NATQ holdout lock sha drifted: {natq_before}")
    if v1_before["log_bytes"] != 235 or v1_before["log_sha256"] != V1_LOG_SHA:
        raise SystemExit(f"STOP: V1 holdout log drifted before run: {v1_before}")
    if v1_before["log_sha256"] != HOLD_LOG_SHA_AT_PREREG:
        raise SystemExit("STOP: V1 holdout log sha != recorded HOLD_LOG_SHA_AT_PREREG")

    val_sha = _sha(VAL_JSONL)
    if val_sha != VAL_SHA:
        raise SystemExit(f"STOP: validation sha {val_sha} != frozen {VAL_SHA}")
    h_sha = _sha(H_FILE)
    if h_sha != H_FILE_SHA:
        raise SystemExit(f"STOP: SYSTEM-H file sha {h_sha} != frozen {H_FILE_SHA}")
    h_obj = json.loads(H_FILE.read_text(encoding="utf-8"))
    if h_obj.get("config_hash") != H_CONFIG_HASH:
        raise SystemExit("STOP: SYSTEM-H config_hash mismatch")
    if config_hash(h_obj["config"]) != H_CONFIG_HASH:
        raise SystemExit("STOP: recomputed SYSTEM-H config_hash drifted")
    i_sha = _sha(I_FILE)
    if i_sha != I_FILE_SHA:
        raise SystemExit(f"STOP: SYSTEM-I file sha {i_sha} != frozen {I_FILE_SHA}")
    i_obj = json.loads(I_FILE.read_text(encoding="utf-8"))
    if i_obj.get("config_hash") != I_CONFIG_HASH:
        raise SystemExit("STOP: SYSTEM-I config_hash mismatch")
    if config_hash(i_obj["config"]) != I_CONFIG_HASH:
        raise SystemExit("STOP: recomputed SYSTEM-I config_hash drifted")
    if _sha(G_FILE) != G_FILE_SHA:
        raise SystemExit("STOP: SYSTEM-G file mutated")
    if _sha(G_CE_D1) != G_CE_D1_SHA:
        raise SystemExit("STOP: SYSTEM-G-CE-D1 file mutated")
    if _sha(E_L10_FILE) != E_L10_SHA:
        raise SystemExit("STOP: SYSTEM-E-L10 file mutated")
    if FROZEN_HASHES["SYSTEM-A-GLOBAL"] != A_HASH:
        raise SystemExit("STOP: SYSTEM-A hash mismatch")

    proj = verify_projection_set()
    if not proj["ok"]:
        raise SystemExit(f"STOP: projection/snapshot mismatch {proj}")

    emb = embedding_status()
    if not emb["complete"]:
        raise SystemExit(f"STOP: control embeddings incomplete: {emb}")

    raw, cases = load_validation()
    if len(raw) != 40 or len(cases) != 40:
        raise SystemExit(f"STOP: n must equal 40, got raw={len(raw)} cases={len(cases)}")
    split_ids = json.loads(VAL_JSON.read_text(encoding="utf-8"))["case_ids"]
    got_ids = [c.case_id for c in cases]
    if got_ids != split_ids:
        raise SystemExit("STOP: validation.jsonl order/ids != validation.json case_ids")
    if any(c.case_id != r["case_id"] for c, r in zip(cases, raw, strict=True)):
        raise SystemExit("STOP: raw/eval case_id misalignment")
    if any(not c.expected_evidence for c in cases):
        raise SystemExit("STOP: a validation case has empty expected_evidence")
    if any(r.get("split") != "validation" for r in raw):
        raise SystemExit("STOP: a loaded record is not split=validation")
    if any(r.get("snapshot") != SNAPSHOT for r in raw):
        raise SystemExit("STOP: a validation case snapshot mismatch")

    h_report = json.loads(H_REPORT.read_text(encoding="utf-8"))
    h_by_id = {r["case_id"]: r for r in h_report["per_case"]}
    stored_pools = {}
    for line in H_POOLS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            stored_pools[rec["case_id"]] = rec
    if set(h_by_id) != set(got_ids) or set(stored_pools) != set(got_ids):
        raise SystemExit("STOP: stored SYSTEM-H traces missing cases")

    encoder = TransformerEncoder(max_seq=512).load()
    if encoder.model_version != TRANSFORMER_FINGERPRINT:
        raise SystemExit("STOP: live encoder fingerprint mismatch")
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)

    gold_cover: dict[str, list[list[str]]] = {}
    for case in cases:
        gold_cover[case.case_id] = [covering_chunk_ids(ref) for ref in case.expected_evidence]

    chunks_by_id = load_control_chunks()
    if len(chunks_by_id) != 14209:
        raise SystemExit(f"STOP: control chunk cache {len(chunks_by_id)} != 14209")

    raw_by_id = {r["case_id"]: r for r in raw}
    per_case: list[dict] = []
    lat_total: list[float] = []
    lat_a: list[float] = []
    lat_local: list[float] = []
    lat_proj: list[float] = []
    lat_pb: list[float] = []
    integrity_failures: list[str] = []
    h_superset_ok_all = True
    pools_fh = pools_path.open("w", encoding="utf-8")

    print("EXP-020A candidate-generation only over 40 NATQ validation questions...", flush=True)

    for case in cases:
        q = case.question
        stored = h_by_id[case.case_id]
        stored_cp = list(stored_pools[case.case_id]["C_P"])
        stored_parents = list(stored["parents"])
        t_case = time.perf_counter()

        t0 = time.perf_counter()
        a_pool = retrieve_system_a_pool(q, transformer)
        lat_a.append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        parents = parent_version_ids(a_pool, PARENT_N)
        if parents != stored_parents:
            raise SystemExit(
                f"STOP: recomputed SYSTEM-H parents != stored on {case.case_id}: "
                f"{parents} vs {stored_parents}"
            )
        local = local_bm25_per_parent_batched(q, parents, W)
        a_ids = {h.chunk_id for h in a_pool}
        extras = additive_extras_ordered(local, a_ids)
        selected_extras = extras[:L]
        capped_local = cap_local_lists(local, a_ids, selected_extras)
        fused_e, new_ids, a_ids = merge_union_rrf(a_pool, capped_local)
        c_e_ids = {h.chunk_id for h in fused_e}
        if not a_ids.issubset(c_e_ids):
            raise SystemExit(f"STOP: anti-drop A failed on {case.case_id}")
        if len(fused_e) != stored["e_pool_size"]:
            raise SystemExit(
                f"STOP: recomputed e_pool_size {len(fused_e)} != stored {stored['e_pool_size']} "
                f"on {case.case_id}"
            )
        lat_local.append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        fused_p = projection_rrf(q, TRANSFORMER_MODEL, transformer)
        mapped = map_to_canonical_extras(fused_p, c_e_ids, P)
        c_p_ids = mapped["C_P"]
        if c_p_ids != stored_cp:
            raise SystemExit(
                f"STOP: recomputed C_P != stored C_P on {case.case_id}"
            )
        lat_proj.append((time.perf_counter() - t0) * 1000)

        h_union_ids: list[str] = []
        seen_h: set[str] = set()
        for h in fused_e:
            if h.chunk_id not in seen_h:
                h_union_ids.append(h.chunk_id)
                seen_h.add(h.chunk_id)
        for cid in c_p_ids:
            if cid not in seen_h:
                h_union_ids.append(cid)
                seen_h.add(cid)
        if len(h_union_ids) != stored["union_pool_size"]:
            raise SystemExit(
                f"STOP: recomputed H union {len(h_union_ids)} != stored "
                f"{stored['union_pool_size']} on {case.case_id}"
            )

        t0 = time.perf_counter()
        pb_bm25: list[str] = []
        pb_proj: list[str] = []
        local_rank_by_chunk: dict[str, dict] = {}
        for vid in parents:
            hits = local.get(vid) or []
            for h in hits:
                local_rank_by_chunk[h.chunk_id] = {
                    "parent": vid,
                    "local_bm25_rank": int(h.rank),
                    "local_bm25_score": float(h.score),
                }
            if hits:
                pb_bm25.append(hits[0].chunk_id)
            top_proj = parent_top1_projection(fused_p, vid, chunks_by_id)
            if top_proj is not None:
                pb_proj.append(top_proj)
        n_before_dedup = len(pb_bm25) + len(pb_proj)
        if n_before_dedup > 20:
            raise SystemExit(
                f"STOP: parent-balanced extras before dedup {n_before_dedup} > 20 on {case.case_id}"
            )
        added_bm25: list[str] = []
        added_proj: list[str] = []
        seen_i = set(h_union_ids)
        for cid in pb_bm25:
            if cid not in seen_i:
                added_bm25.append(cid)
                seen_i.add(cid)
        for cid in pb_proj:
            if cid not in seen_i:
                added_proj.append(cid)
                seen_i.add(cid)
        i_union_ids = list(h_union_ids) + added_bm25 + added_proj
        if not set(h_union_ids).issubset(set(i_union_ids)):
            h_superset_ok_all = False
            raise SystemExit(f"STOP: SYSTEM-H union not subset of SYSTEM-I on {case.case_id}")
        lat_pb.append((time.perf_counter() - t0) * 1000)

        h_hits = hits_from_ids(h_union_ids, chunks_by_id)
        i_hits = hits_from_ids(i_union_ids, chunks_by_id)
        pb_bm25_set = set(pb_bm25)
        pb_proj_set = set(pb_proj)
        pos = {cid: i + 1 for i, cid in enumerate(i_union_ids)}

        span_rows = []
        for i, ref in enumerate(case.expected_evidence):
            cover = gold_cover[case.case_id][i]
            in_h = span_in_hits(h_hits, ref)
            in_i = span_in_hits(i_hits, ref)
            covering_in_i = [c for c in cover if c in pos]
            pool_pos = min((pos[c] for c in covering_in_i), default=None)
            local_info = None
            for c in cover:
                if c in local_rank_by_chunk:
                    local_info = local_rank_by_chunk[c]
                    break
            recovered = bool(in_i) and not bool(in_h)
            rec_lane = lane_of_span(cover, pb_bm25_set, pb_proj_set) if recovered or (not in_h) else None
            span_rows.append(
                {
                    "span_index": i,
                    "covering_chunk_ids": cover,
                    "gold_version_id": ref.version_id,
                    "in_system_h_pool": bool(in_h),
                    "in_system_i_pool": bool(in_i),
                    "recovered": recovered,
                    "recovery_lane": rec_lane if (recovered or not in_h) else None,
                    "in_parent_balanced_bm25_top1": any(c in pb_bm25_set for c in cover),
                    "in_parent_balanced_projection_top1": any(c in pb_proj_set for c in cover),
                    "new_pool_position": pool_pos,
                    "local_bm25_within_parent": local_info,
                    "gold_in_parents": ref.version_id in set(parents),
                }
            )
            if stored["spans"][i]["in_pool"] != in_h:
                raise SystemExit(
                    f"STOP: recomputed SYSTEM-H in_pool != stored on {case.case_id} span {i}"
                )

        total_ms = (time.perf_counter() - t_case) * 1000
        lat_total.append(total_ms)
        meta = raw_by_id[case.case_id]
        rec = {
            "case_id": case.case_id,
            "provider": meta.get("provider"),
            "coverage_tags": list(meta.get("coverage_tags") or []),
            "stress_types": list(meta.get("stress_types") or []),
            "n_gold_spans": len(case.expected_evidence),
            "parents": parents,
            "n_parents": len(parents),
            "system_h_pool_size": len(h_union_ids),
            "system_i_pool_size": len(i_union_ids),
            "n_added": len(i_union_ids) - len(h_union_ids),
            "n_parent_balanced_bm25_before_dedup": len(pb_bm25),
            "n_parent_balanced_projection_before_dedup": len(pb_proj),
            "n_added_bm25": len(added_bm25),
            "n_added_projection": len(added_proj),
            "n_extras_before_dedup": n_before_dedup,
            "all_gold_in_h_pool": all(s["in_system_h_pool"] for s in span_rows),
            "all_gold_in_i_pool": all(s["in_system_i_pool"] for s in span_rows),
            "system_h_subset": True,
            "spans": span_rows,
            "parent_balanced_bm25_top1": pb_bm25,
            "parent_balanced_projection_top1": pb_proj,
            "added_bm25": added_bm25,
            "added_projection": added_proj,
            "latency_ms": {
                "total_candidate_generation": round(total_ms, 1),
                "system_a": round(lat_a[-1], 1),
                "e_l10": round(lat_local[-1], 1),
                "projection": round(lat_proj[-1], 1),
                "parent_balanced_selection": round(lat_pb[-1], 1),
                "stored_system_h_system_a": stored["latency_ms"]["system_a"],
                "stored_system_h_e_l10": stored["latency_ms"]["e_l10"],
                "stored_system_h_projection": stored["latency_ms"]["projection"],
            },
        }
        per_case.append(rec)
        dump = {
            "case_id": case.case_id,
            "parents": parents,
            "C_P": c_p_ids,
            "system_h_union_ids": h_union_ids,
            "system_i_union_ids": i_union_ids,
            "parent_balanced_bm25_top1": pb_bm25,
            "parent_balanced_projection_top1": pb_proj,
            "added_bm25": added_bm25,
            "added_projection": added_proj,
            "spans": span_rows,
        }
        pools_fh.write(json.dumps(dump, default=str) + "\n")
        pools_fh.flush()
        print(
            f"{case.case_id} H={int(rec['all_gold_in_h_pool'])} I={int(rec['all_gold_in_i_pool'])} "
            f"pool {len(h_union_ids)}->{len(i_union_ids)} "
            f"added_b={len(added_bm25)} added_p={len(added_proj)} "
            f"parents={len(parents)} ms={total_ms:.0f}",
            flush=True,
        )

    pools_fh.close()

    natq_after = natq_holdout_log_state()
    v1_after = holdout_log_state()
    if natq_after["log_bytes"] != 0 or natq_after["log_sha256"] != NATQ_LOG_SHA:
        integrity_failures.append("NATQ holdout access log changed")
    if v1_after["log_bytes"] != 235 or v1_after["log_sha256"] != V1_LOG_SHA:
        integrity_failures.append("V1 holdout access log changed")
    if _sha(H_FILE) != H_FILE_SHA:
        integrity_failures.append("SYSTEM-H file mutated")
    if config_hash(json.loads(H_FILE.read_text(encoding="utf-8"))["config"]) != H_CONFIG_HASH:
        integrity_failures.append("SYSTEM-H config_hash changed")
    if _sha(I_FILE) != I_FILE_SHA:
        integrity_failures.append("SYSTEM-I file mutated")
    if _sha(G_FILE) != G_FILE_SHA or _sha(G_CE_D1) != G_CE_D1_SHA:
        integrity_failures.append("SYSTEM-G or SYSTEM-G-CE-D1 mutated")
    if _sha(E_L10_FILE) != E_L10_SHA:
        integrity_failures.append("SYSTEM-E-L10 mutated")
    if _sha(VAL_JSONL) != VAL_SHA:
        integrity_failures.append("validation.jsonl mutated")
    if _sha(PREREG_JSON) != PREREG_JSON_SHA:
        integrity_failures.append("preregistration mutated after hash")

    n = 40
    n_spans = sum(len(r["spans"]) for r in per_case)
    case_h = sum(1 for r in per_case if r["all_gold_in_h_pool"])
    case_i = sum(1 for r in per_case if r["all_gold_in_i_pool"])
    span_h = sum(1 for r in per_case for s in r["spans"] if s["in_system_h_pool"])
    span_i = sum(1 for r in per_case for s in r["spans"] if s["in_system_i_pool"])
    recovered_cases = sum(
        1 for r in per_case if r["all_gold_in_i_pool"] and not r["all_gold_in_h_pool"]
    )
    recovered_spans = [
        {"case_id": r["case_id"], **s}
        for r in per_case
        for s in r["spans"]
        if s["recovered"]
    ]
    still_missing = [
        {"case_id": r["case_id"], **s}
        for r in per_case
        for s in r["spans"]
        if not s["in_system_i_pool"]
    ]
    missing_h = [
        {"case_id": r["case_id"], **s}
        for r in per_case
        for s in r["spans"]
        if not s["in_system_h_pool"]
    ]
    lane_counts = Counter(s["recovery_lane"] for s in recovered_spans)
    missing_h_lane = Counter(s["recovery_lane"] for s in missing_h)
    added_sizes = [r["n_added"] for r in per_case]
    h_sizes = [r["system_h_pool_size"] for r in per_case]
    i_sizes = [r["system_i_pool_size"] for r in per_case]
    parent_ns = [r["n_parents"] for r in per_case]

    stored_h_cg = [
        h_by_id[r["case_id"]]["latency_ms"]["system_a"]
        + h_by_id[r["case_id"]]["latency_ms"]["e_l10"]
        + h_by_id[r["case_id"]]["latency_ms"]["projection"]
        for r in per_case
    ]
    new_cg = [
        r["latency_ms"]["system_a"]
        + r["latency_ms"]["e_l10"]
        + r["latency_ms"]["projection"]
        + r["latency_ms"]["parent_balanced_selection"]
        for r in per_case
    ]

    def provider_metrics(provider: str) -> dict:
        sub = [r for r in per_case if r["provider"] == provider]
        ns = sum(len(r["spans"]) for r in sub)
        return {
            "n_cases": len(sub),
            "candidate_case": f"{sum(1 for r in sub if r['all_gold_in_i_pool'])}/{len(sub)}",
            "candidate_span": f"{sum(1 for r in sub for s in r['spans'] if s['in_system_i_pool'])}/{ns}",
            "baseline_case": f"{sum(1 for r in sub if r['all_gold_in_h_pool'])}/{len(sub)}",
            "baseline_span": f"{sum(1 for r in sub for s in r['spans'] if s['in_system_h_pool'])}/{ns}",
        }

    multi = [
        r
        for r in per_case
        if r["n_gold_spans"] > 1 or "multi_span" in (r["coverage_tags"] + r["stress_types"])
    ]
    multi_i = sum(1 for r in multi if r["all_gold_in_i_pool"])
    multi_h = sum(1 for r in multi if r["all_gold_in_h_pool"])

    every_h_present = h_superset_ok_all and all(r["system_h_subset"] for r in per_case)
    no_integrity = len(integrity_failures) == 0
    gate = {
        "candidate_full_case_ge_36_40": case_i >= 36,
        "candidate_span_gt_46_53": span_i > 46,
        "every_original_SYSTEM_H_candidate_remains_present": every_h_present,
        "no_integrity_provenance_failure": no_integrity,
    }
    supported = all(gate.values())

    # Diagnostics after aggregates: the 7 previously missing H spans (== missing_h)
    diag_seven = []
    for item in missing_h:
        diag_seven.append(
            {
                "case_id": item["case_id"],
                "span_index": item["span_index"],
                "covering_chunk_ids": item["covering_chunk_ids"],
                "recovered": item["recovered"],
                "recovered_by": item["recovery_lane"],
                "new_pool_position": item["new_pool_position"],
                "in_parent_balanced_bm25_top1": item["in_parent_balanced_bm25_top1"],
                "in_parent_balanced_projection_top1": item["in_parent_balanced_projection_top1"],
                "local_bm25_within_parent": item["local_bm25_within_parent"],
                "gold_in_parents": item["gold_in_parents"],
            }
        )

    payload = {
        "experiment_id": "EXP-020A",
        "scored": True,
        "n_evals": 1,
        "second_run": False,
        "retuned": False,
        "holdout_run": False,
        "release_frozen": False,
        "SYSTEM_H_modified": False,
        "CE_run": False,
        "final_ranking_run": False,
        "EXP-020B_run": False,
        "split": "natq-001/validation",
        "split_role": "DEVELOPMENT / MODEL-SELECTION DATA; not independent validation",
        "n": n,
        "n_gold_spans": n_spans,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timestamp_et": datetime.now(UTC).astimezone(ZoneInfo("America/New_York")).strftime(
            "%Y-%m-%dT%H:%M:%S%z"
        ),
        "preregistration_json_sha256": PREREG_JSON_SHA,
        "SYSTEM_I_config_hash": I_CONFIG_HASH,
        "SYSTEM_I_file_sha256": i_sha,
        "SYSTEM_H_config_hash": H_CONFIG_HASH,
        "SYSTEM_H_config_hash_unchanged": _sha(H_FILE) == H_FILE_SHA,
        "SYSTEM_H_file_sha256": _sha(H_FILE),
        "projection_set": proj,
        "natq_holdout_access_log_before": natq_before,
        "natq_holdout_access_log_after": natq_after,
        "v1_holdout_access_log_before": {
            "log_bytes": v1_before["log_bytes"],
            "log_sha256": v1_before["log_sha256"],
        },
        "v1_holdout_access_log_after": {
            "log_bytes": v1_after["log_bytes"],
            "log_sha256": v1_after["log_sha256"],
        },
        "holdout_json_opened": False,
        "v1_holdout_json_opened": False,
        "embedding": emb,
        "environment": env_fingerprint(emb),
        "baseline": {
            "candidate_full_case_Recall_at_pool": "34/40",
            "candidate_span_micro": "46/53",
            "recomputed_match": {
                "case": f"{case_h}/40",
                "span": f"{span_h}/{n_spans}",
                "matches_stored_34_40_46_53": case_h == 34 and span_h == 46 and n_spans == 53,
            },
        },
        "PRIMARY": {
            "candidate_full_case_Recall_at_pool": f"{case_i}/{n}",
            "n": case_i,
            "d": n,
            "baseline": "34/40",
            "delta_cases": case_i - 34,
        },
        "SECONDARY": {
            "candidate_span_micro": f"{span_i}/{n_spans}",
            "baseline_span": "46/53",
            "delta_spans": span_i - 46,
            "recovered_cases": recovered_cases,
            "recovered_spans_n": len(recovered_spans),
            "recovered_spans": recovered_spans,
            "still_missing_n": len(still_missing),
            "still_missing": still_missing,
            "pool_size_H_mean": _mean(h_sizes, 2),
            "pool_size_H_median": _median(h_sizes, 2),
            "pool_size_I_mean": _mean(i_sizes, 2),
            "pool_size_I_median": _median(i_sizes, 2),
            "mean_added": _mean(added_sizes, 3),
            "median_added": _median(added_sizes, 3),
            "mean_parents": _mean([float(x) for x in parent_ns], 2),
            "parent_n_distribution": dict(Counter(parent_ns)),
            "lexical_vs_projection_recovered_spans": dict(lane_counts),
            "lexical_vs_projection_of_the_7_missing_H_spans": dict(missing_h_lane),
            "mean_added_bm25": _mean([r["n_added_bm25"] for r in per_case], 3),
            "mean_added_projection": _mean([r["n_added_projection"] for r in per_case], 3),
            "mean_bm25_top1_before_dedup": _mean(
                [r["n_parent_balanced_bm25_before_dedup"] for r in per_case], 3
            ),
            "mean_projection_top1_before_dedup": _mean(
                [r["n_parent_balanced_projection_before_dedup"] for r in per_case], 3
            ),
            "per_provider": {
                "openai": provider_metrics("openai"),
                "anthropic": provider_metrics("anthropic"),
            },
            "multi_span_candidate_ceiling": {
                "n": len(multi),
                "SYSTEM_H": f"{multi_h}/{len(multi)}",
                "SYSTEM_I": f"{multi_i}/{len(multi)}",
            },
            "latency_ms": {
                "SYSTEM_I_candidate_generation_mean": _mean(new_cg, 1),
                "SYSTEM_I_candidate_generation_median": _median(new_cg, 1),
                "stored_SYSTEM_H_A_EL10_proj_mean": _mean(stored_h_cg, 1),
                "stored_SYSTEM_H_A_EL10_proj_median": _median(stored_h_cg, 1),
                "increase_mean_vs_stored_H": round(_mean(new_cg, 1) - _mean(stored_h_cg, 1), 1),
                "parent_balanced_selection_mean": _mean(lat_pb, 1),
                "parent_balanced_selection_median": _median(lat_pb, 1),
                "recomputed_system_a_mean": _mean(lat_a, 1),
                "recomputed_e_l10_mean": _mean(lat_local, 1),
                "recomputed_projection_mean": _mean(lat_proj, 1),
            },
        },
        "diagnostics_seven_previously_missing_gold_spans": diag_seven,
        "diagnostics_recoveries_all_40_cases": recovered_spans,
        "gate": gate,
        "EXP-020A_SUPPORTED": supported,
        "integrity_failures": integrity_failures,
        "per_case": per_case,
        "elapsed_s": round(time.time() - started, 2),
        "L": L,
        "P": P,
        "PARENT_N": PARENT_N,
        "W": W,
        "STOP": "Do not run final ranking. Do not run EXP-020B. Do not run CE.",
    }

    results_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n")

    def lane_cell(item: dict) -> str:
        if item["recovered"]:
            return str(item["recovered_by"])
        return str(item["recovered_by"] or "neither") + " (not recovered)"

    lines = [
        "# EXP-020A — PARENT-BALANCED WITHIN-DOCUMENT CANDIDATE GENERATION",
        "",
        f"**EXP-020A_SUPPORTED = {str(supported).upper()}**",
        "",
        "Candidate-generation only on NATQ-001 validation n=40, now DEVELOPMENT / MODEL-SELECTION DATA. "
        "Not independent validation. Holdout was not opened. SYSTEM-H / G / E were not modified. "
        "CE and final ranking were not run. EXP-020B was not run.",
        "",
        "## Setup",
        "",
        f"- Preregistration sha256 `{PREREG_JSON_SHA}` hashed before examining new candidate ranks.",
        f"- SYSTEM-I-PARENT-BALANCED-CANDIDATES config_hash `{I_CONFIG_HASH}` (file sha256 `{i_sha}`).",
        f"- Parent SYSTEM-H config_hash `{H_CONFIG_HASH}` unchanged after run: **{payload['SYSTEM_H_config_hash_unchanged']}**.",
        f"- Split: `evals/splits/natq-001/validation.jsonl` n=40, sha256 `{VAL_SHA}`.",
        f"- Snapshot `{SNAPSHOT}`. Projection `{PROJECTION_SET_ID}` n=18057.",
        f"- Recomputed SYSTEM-H candidate generation matched stored parents, C_P, e_pool_size, union size, and in_pool flags.",
        f"- NATQ holdout-access log after: {natq_after['log_bytes']} bytes, sha256 `{natq_after['log_sha256']}`.",
        f"- V1 holdout-access log after: {v1_after['log_bytes']} bytes, sha256 `{v1_after['log_sha256']}`.",
        "- holdout_json_opened: **false**. v1_holdout_json_opened: **false**.",
        "",
        "## PRIMARY — candidate full-case Recall@pool",
        "",
        "| metric | SYSTEM-H baseline | SYSTEM-I |",
        "| --- | ---: | ---: |",
        f"| candidate full-case Recall@pool | 34/40 | **{case_i}/40** |",
        "",
        "## SECONDARY",
        "",
        "| metric | SYSTEM-H baseline | SYSTEM-I |",
        "| --- | ---: | ---: |",
        f"| candidate span micro | 46/53 | **{span_i}/53** |",
        f"| recovered CG cases | — | {recovered_cases} |",
        f"| recovered missing spans | — | {len(recovered_spans)} |",
        f"| mean pool size | {_mean(h_sizes, 2)} | {_mean(i_sizes, 2)} |",
        f"| median pool size | {_median(h_sizes, 2)} | {_median(i_sizes, 2)} |",
        f"| mean added candidates | — | {_mean(added_sizes, 3)} |",
        f"| mean added BM25 / projection | — | {_mean([r['n_added_bm25'] for r in per_case], 3)} / {_mean([r['n_added_projection'] for r in per_case], 3)} |",
        f"| candidate-gen latency mean ms | {_mean(stored_h_cg, 1)} | {_mean(new_cg, 1)} (Δ {round(_mean(new_cg, 1) - _mean(stored_h_cg, 1), 1)}) |",
        f"| parent-balanced selection mean ms | — | {_mean(lat_pb, 1)} |",
        "",
        "### Lexical vs projection contribution (recovered spans)",
        "",
        "| lane | recovered spans |",
        "| --- | ---: |",
        f"| BM25 only | {lane_counts.get('BM25', 0)} |",
        f"| projection only | {lane_counts.get('projection', 0)} |",
        f"| both | {lane_counts.get('both', 0)} |",
        f"| neither | {lane_counts.get('neither', 0)} |",
        "",
        "### Per-provider candidate recall",
        "",
        "| provider | baseline case | SYSTEM-I case | baseline span | SYSTEM-I span |",
        "| --- | ---: | ---: | ---: | ---: |",
        f"| openai | {provider_metrics('openai')['baseline_case']} | {provider_metrics('openai')['candidate_case']} | {provider_metrics('openai')['baseline_span']} | {provider_metrics('openai')['candidate_span']} |",
        f"| anthropic | {provider_metrics('anthropic')['baseline_case']} | {provider_metrics('anthropic')['candidate_case']} | {provider_metrics('anthropic')['baseline_span']} | {provider_metrics('anthropic')['candidate_span']} |",
        "",
        "### Multi-span candidate ceiling",
        "",
        f"Subset n={len(multi)} (n_gold_spans>1 or tag multi_span). SYSTEM-H all-gold-in-pool **{multi_h}/{len(multi)}**. SYSTEM-I **{multi_i}/{len(multi)}**.",
        "",
        "## Diagnostics — seven previously missing gold spans (after aggregates)",
        "",
        "Identities are the complete set of SYSTEM-H union misses on this split (NATQ-DIAG-001). Diagnostic only. No named-case handling.",
        "",
        "| case | span | recovered | by | new pool position | local-BM25 rank in parent |",
        "| --- | ---: | --- | --- | ---: | --- |",
    ]
    for item in diag_seven:
        loc = item["local_bm25_within_parent"]
        loc_s = str(loc["local_bm25_rank"]) if loc else "not in W=20 list"
        lines.append(
            f"| `{item['case_id']}` | {item['span_index']} | {item['recovered']} | {lane_cell(item)} | "
            f"{item['new_pool_position']} | {loc_s} |"
        )
    lines += [
        "",
        f"Recoveries across ALL 40 cases: **{len(recovered_spans)}** span(s) in **{recovered_cases}** case(s). "
        f"SYSTEM-H missing span count was {len(missing_h)}; still missing after SYSTEM-I: {len(still_missing)}.",
        "",
        "## Gate",
        "",
        "| condition | result |",
        "| --- | --- |",
        f"| candidate full-case recall >= 36/40 ({case_i}/40) | {gate['candidate_full_case_ge_36_40']} |",
        f"| candidate span recall > 46/53 ({span_i}/53) | {gate['candidate_span_gt_46_53']} |",
        f"| every original SYSTEM-H candidate remains present | {gate['every_original_SYSTEM_H_candidate_remains_present']} |",
        f"| no integrity/provenance failure | {gate['no_integrity_provenance_failure']} |",
        "",
        f"**EXP-020A_SUPPORTED = {str(supported).upper()}**",
        "",
        "## STOP",
        "",
        "Stop after EXP-020A. Do **not** run final ranking. Do **not** run EXP-020B. Do **not** run CE. Do **not** open holdout.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"DONE case {case_i}/40 span {span_i}/{n_spans} recovered_cases={recovered_cases} "
        f"SUPPORTED={supported} elapsed={payload['elapsed_s']}s",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
