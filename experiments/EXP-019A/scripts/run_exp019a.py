#!/usr/bin/env python3
"""EXP-019A: one preregistered rescore of SYSTEM-F / EXP-017.

ONE CHANGE: projection-only a_norm = minmax(projection-RRF) over P extras
for that query (degenerate 0.5 if constant). E-L10 a_norm and EXP-017 CE
minmax kept exactly. Blend 0.7/0.3. No CE recall for 019A ranks.

Does not open gold150-v1 holdout.json. Does not load validation. Does not
modify D/E/E-L10/cs_v1_control/ps_v2_ovl_win448_s224. Does not freeze a
release. Does not change candidate generation, CE model, CE logits, or
weights. No weight sweep. No extra variants. No query rewrite.
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
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-015" / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-018" / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-018B" / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-017" / "scripts"))

from cross_encoder import CE_NAME, CE_REVISION, CE_SHA256, CrossEncoderReranker  # noqa: E402
from rag_v1.db import connect  # noqa: E402
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
from projection_retrieval import (  # noqa: E402
    PROJECTION_SET_ID,
    map_to_canonical_extras,
    projection_rrf,
)
from run_exp017 import (  # noqa: E402
    L,
    P,
    apply_blend_exp017,
    load_control_chunks,
    metrics_from_cases,
    score_system,
)
from run_exp018_development import (  # noqa: E402
    env_fingerprint,
    first_span_rank,
    hit_as_row,
    paired,
    span_in_hits,
)
from system_e import (  # noqa: E402
    A_HASH,
    BLEND_A,
    BLEND_CE,
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
    minmax_norm,
    parent_version_ids,
    retrieve_system_a_pool,
)

OUT_DIR = ROOT / "experiments" / "EXP-019A"
GOLD_JSONL = ROOT / "evals" / "gold" / "v2-devset-001.jsonl"
SPLIT_PATH = ROOT / "evals" / "splits" / "v2-devset-001" / "development.json"
D_FREEZE = ROOT / "experiments" / "EXP-016" / "SYSTEM-D-GUARD.json"
D_RELEASE = ROOT / "experiments" / "EVAL-HOLDOUT-001" / "SYSTEM-D-RELEASE.json"
E_FILE = ROOT / "experiments" / "EXP-018" / "SYSTEM-E-WITHIN-DOC.json"
E_L10_FILE = ROOT / "experiments" / "EXP-018B" / "SYSTEM-E-L10-WITHIN-DOC.json"
F_FILE = ROOT / "experiments" / "EXP-017" / "SYSTEM-F-PROJECTION.json"
EXP017_RESULTS = ROOT / "experiments" / "EXP-017" / "EXP-017-results.json"
PREREG_JSON = OUT_DIR / "EXP-019A-preregistration.json"
PREREG_MD = OUT_DIR / "EXP-019A-preregistration.md"

PREREG_JSON_SHA = "f14001eff07b63c7916d7e27567d15ccd1e53b52918ae66f0d24ca37abb54cf3"
F_CONFIG_HASH = "83ba5f2e834ecdffbfe4fb554cf84860ad35cf7010e9764e5cdea9e38598f678"
EXP017_PREREG_SHA = "053a6bf14df088ca9e2283bc3e8dfb0769848a48c54c51a77fbe045795a80cc6"
GOLD_SHA = "cb687f3cc88b38d4beed7ad4bc829296a30518aaaf45cce0677ec568b1bf77e5"
SPLIT_SHA = "6b0c49c9040c215fde6134697c35a1f28458ba7d72ef012c0840feb7f9c3eb17"
FREEZE_SHA = "97ea6befbb4fd845f53da2aef20ba84cedaaf69c0f09e3ad90833b813fee2ad9"
E_FILE_SHA = "e228616beee1bcb13855c2eadee9fc20ec1fae3e54c77b28587114568c64d087"
D_GUARD_SHA = "e9267f5581404e9885598979204c08762cd33f362703e526b20f4d3430c35a82"
D_RELEASE_SHA = "1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40"
E_L10_HASH = "bae1c05b5c47c179dc5cd7972a14bd23d102a4d513b674667eb469e17cd85e89"
E_UNCAPPED_HASH = "7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe"
E_L10_FILE_SHA = "efbd3bc1cc73d3c342a607ef75135515d13680b31fd6058e8f1c13e80d13ed89"
PROJ_CFG_HASH = "7fd5034c9510a1e08ec76bd22b020703c586dd12e7c02659397df05c5c365a8e"
BASELINE_STRICT = 40
BASELINE_CAND = 46
BASELINE_N = 50

MEMBER_KEEP = (
    "chunk_id",
    "version_id",
    "section_path",
    "char_start",
    "char_end",
    "in_e_l10",
    "in_a_pool",
    "origin",
    "a_rank",
    "a_score",
    "a_norm",
    "ce_score",
    "ce_norm",
    "blend_score",
    "blend_rank",
    "e_rank",
    "exp017_rank",
    "projection_fused",
    "system_a_rank",
    "system_a_score",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mean(xs: list[float], ndigits: int = 1) -> float:
    return round(statistics.mean(xs), ndigits) if xs else 0.0


def compact_row(row: dict) -> dict:
    out = {}
    for k in MEMBER_KEEP:
        if k in row:
            v = row[k]
            if k in ("a_rank", "blend_rank", "e_rank", "exp017_rank") and v is not None:
                out[k] = int(v)
            elif k in ("a_score", "a_norm", "ce_score", "ce_norm", "blend_score", "projection_fused", "system_a_score"):
                out[k] = float(v) if v is not None else None
            else:
                out[k] = v
    return out


def inspect_stored_logits(exp017: dict) -> dict:
    pc = exp017["per_case"]
    keys = sorted({k for rec in pc for k in rec.keys()})
    span_keys = sorted({k for rec in pc for s in rec.get("spans", []) for k in s.keys()})
    forbidden = ("ce_score", "ce_logit", "ce_norm", "a_norm", "projection_fused", "projection_rrf", "blend_score")
    found_in_case = [k for k in forbidden if k in keys]
    found_in_span = [k for k in forbidden if k in span_keys]
    stored = bool(found_in_case or found_in_span)
    return {
        "per_case_keys": keys,
        "span_keys": span_keys,
        "logits_a_norm_proj_rrf_present_in_per_case": stored,
        "found_forbidden_case_keys": found_in_case,
        "found_forbidden_span_keys": found_in_span,
        "must_rematerialize": not stored,
    }


def apply_blend_exp019a(x_rows: list[dict]) -> list[dict]:
    """Keep E-L10 a_norm and EXP-017 ce_norm exactly. Projection-only a_norm = minmax(proj RRF)."""
    e_rows = [r for r in x_rows if r.get("in_e_l10")]
    extras = [r for r in x_rows if not r.get("in_e_l10")]
    proj_scores = [float(r["projection_fused"]) for r in extras]
    proj_norms = minmax_norm(proj_scores)
    out: list[dict] = []
    for r in e_rows:
        item = dict(r)
        item["a_norm_exp017"] = float(item["a_norm"])
        item["retrieval_norm"] = float(item["a_norm"])
        item["ce_norm_exp017"] = float(item["ce_norm"])
        item["blend_score_exp017"] = float(item["blend_score"])
        item["blend_score"] = BLEND_CE * float(item["ce_norm"]) + BLEND_A * float(item["retrieval_norm"])
        out.append(item)
    for r, pn in zip(extras, proj_norms, strict=True):
        item = dict(r)
        item["a_norm_exp017"] = float(item.get("a_norm", 0.0))
        item["a_norm"] = float(pn)
        item["retrieval_norm"] = float(pn)
        item["ce_norm_exp017"] = float(item["ce_norm"])
        item["blend_score_exp017"] = float(item["blend_score"])
        item["blend_score"] = BLEND_CE * float(item["ce_norm"]) + BLEND_A * float(item["retrieval_norm"])
        out.append(item)
    out.sort(key=lambda r: (-r["blend_score"], r["a_rank"], r["chunk_id"]))
    for i, row in enumerate(out, start=1):
        row["blend_rank"] = i
        row["exp019a_rank"] = i
    return out


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
    if row is None:
        raise SystemExit("STOP: projection set missing")
    pid, cfg_hash, window, stride = row
    ok = (
        pid == PROJECTION_SET_ID
        and cfg_hash == PROJ_CFG_HASH
        and n == 18057
        and window == 448
        and stride == 224
    )
    return {
        "projection_set_id": pid,
        "config_hash": cfg_hash,
        "n": n,
        "window_tokens": window,
        "stride_tokens": stride,
        "ok": ok,
    }


def write_stop(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def main() -> int:
    started = time.time()
    results_path = OUT_DIR / "EXP-019A-results.json"
    report_path = OUT_DIR / "EXP-019A-report.md"
    identity_path = OUT_DIR / "EXP-019A-pool-identity.json"
    recovered_path = OUT_DIR / "EXP-019A-recovered-union.jsonl"
    if results_path.exists():
        raise SystemExit("STOP: EXP-019A results already exist; refusing to overwrite")
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
    if FROZEN_HASHES["SYSTEM-A-GLOBAL"] != A_HASH:
        raise SystemExit("STOP: SYSTEM-A hash mismatch")
    if json.loads(D_FREEZE.read_text())["config_hash"] != D_HASH:
        raise SystemExit("STOP: SYSTEM-D-GUARD.json config_hash mismatch")
    if json.loads(D_RELEASE.read_text())["config_hash"] != D_HASH:
        raise SystemExit("STOP: SYSTEM-D-RELEASE.json config_hash mismatch")
    if _sha(D_FREEZE) != D_GUARD_SHA or _sha(D_RELEASE) != D_RELEASE_SHA:
        raise SystemExit("STOP: D freeze file bytes changed")
    if _sha(E_FILE) != E_FILE_SHA:
        raise SystemExit("STOP: SYSTEM-E-WITHIN-DOC.json file SHA256 changed")
    e_l10_sha_before = _sha(E_L10_FILE)
    e_l10_obj = json.loads(E_L10_FILE.read_text())
    if e_l10_obj["config_hash"] != E_L10_HASH:
        raise SystemExit("STOP: SYSTEM-E-L10 config_hash mismatch")
    if e_l10_sha_before != E_L10_FILE_SHA:
        raise SystemExit("STOP: SYSTEM-E-L10 file SHA256 mismatch")
    f_obj = json.loads(F_FILE.read_text())
    if f_obj["config_hash"] != F_CONFIG_HASH:
        raise SystemExit("STOP: SYSTEM-F-PROJECTION config_hash mismatch")
    if f_obj["config_hash"] != json.loads(PREREG_JSON.read_text())["SYSTEM-F-PROJECTION_config_hash"]:
        raise SystemExit("STOP: prereg SYSTEM-F hash mismatch")

    proj = verify_projection_set()
    if not proj["ok"]:
        raise SystemExit(f"STOP: projection set mismatch {proj}")

    exp017 = json.loads(EXP017_RESULTS.read_text())
    if exp017.get("preregistration_json_sha256") != EXP017_PREREG_SHA:
        raise SystemExit("STOP: EXP-017 results prereg sha mismatch")
    stored_pc = {rec["case_id"]: rec for rec in exp017["per_case"]}
    stored_inspect = inspect_stored_logits(exp017)
    print("stored_logits", stored_inspect["logits_a_norm_proj_rrf_present_in_per_case"],
          "must_rematerialize", stored_inspect["must_rematerialize"], flush=True)

    hash_check = {
        "prereg_json_sha256": got_pre,
        "prereg_json_sha256_ok": got_pre == PREREG_JSON_SHA,
        "SYSTEM-F-PROJECTION_config_hash": f_obj["config_hash"],
        "SYSTEM-F-PROJECTION_config_hash_ok": f_obj["config_hash"] == F_CONFIG_HASH,
        "SYSTEM-E-L10-WITHIN-DOC_config_hash": e_l10_obj["config_hash"],
        "SYSTEM-E-L10-WITHIN-DOC_config_hash_ok": e_l10_obj["config_hash"] == E_L10_HASH,
        "projection_set": proj,
        "holdout_access_log": hold_before,
        "holdout_log_ok": hold_before["log_bytes"] == 235 and hold_before["log_sha256"] == HOLD_LOG_SHA_AT_PREREG,
        "EXP-017_prereg_json_sha256": EXP017_PREREG_SHA,
    }
    if not all(
        [
            hash_check["prereg_json_sha256_ok"],
            hash_check["SYSTEM-F-PROJECTION_config_hash_ok"],
            hash_check["SYSTEM-E-L10-WITHIN-DOC_config_hash_ok"],
            hash_check["projection_set"]["ok"],
            hash_check["holdout_log_ok"],
        ]
    ):
        raise SystemExit(f"STOP: pre-score hash verification failed {hash_check}")

    if not stored_inspect["must_rematerialize"]:
        raise SystemExit("STOP: unexpected stored logits; protocol prefers stored, but this runner rematerializes only when absent")

    emb = embedding_status()
    if not emb["complete"]:
        raise SystemExit(f"STOP: control embeddings incomplete: {emb}")

    encoder = TransformerEncoder(max_seq=512).load()
    if encoder.model_version != TRANSFORMER_FINGERPRINT:
        raise SystemExit("STOP: live encoder fingerprint mismatch")
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)
    ce = CrossEncoderReranker()  # defaults; not fast=True; used ONLY to recover EXP-017 logits
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

    chunks_by_id = load_control_chunks()
    if len(chunks_by_id) != 14209:
        raise SystemExit(f"STOP: control chunk cache {len(chunks_by_id)} != 14209")

    identity_mismatches: list[dict] = []
    recovered_fh = recovered_path.open("w", encoding="utf-8")
    remat_x_cases = {}
    y_cases = {}
    remat_x_full = {}
    y_full = {}
    stored_x_full = {}
    cand_x = []
    cand_y = []
    pool_x, pool_y = [], []
    per_case = []
    rank1 = []
    rank_movements = []
    rescored_ms: list[float] = []
    remat_ce_ms: list[float] = []

    print("rematerializing EXP-017 scores with frozen code (CE once, for recovery only)...", flush=True)

    for case in cases:
        stored = stored_pc[case.case_id]
        q = case.question
        t_case = time.time()
        a_pool = retrieve_system_a_pool(q, transformer)
        parents = parent_version_ids(a_pool, PARENT_N)
        local = local_bm25_per_parent_batched(q, parents, W)
        a_ids = {h.chunk_id for h in a_pool}
        extras = additive_extras_ordered(local, a_ids)
        selected_extras = extras[:L]
        capped_local = cap_local_lists(local, a_ids, selected_extras)
        fused_e, new_ids, a_ids = merge_union_rrf(a_pool, capped_local)
        c_e_ids = {h.chunk_id for h in fused_e}
        if not a_ids.issubset(c_e_ids):
            raise SystemExit(f"STOP: anti-drop A failed on {case.case_id}")

        a_by_id = {h.chunk_id: h for h in a_pool}
        t0 = time.time()
        e_ce = ce.score_pairs(q, [h.text for h in fused_e])
        ce_by_id = {h.chunk_id: float(s) for h, s in zip(fused_e, e_ce, strict=True)}
        lat_ce_e = (time.time() - t0) * 1000

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

        fused_p = projection_rrf(q, TRANSFORMER_MODEL, transformer)
        mapped = map_to_canonical_extras(fused_p, c_e_ids, P)
        c_p_ids = mapped["C_P"]

        extra_rows = []
        extra_hits: list[SearchHit] = []
        for cid in c_p_ids:
            rec = chunks_by_id[cid]
            extra_rows.append(
                {
                    "chunk_id": rec["chunk_id"],
                    "version_id": rec["version_id"],
                    "section_path": rec["section_path"],
                    "char_start": rec["char_start"],
                    "char_end": rec["char_end"],
                    "text": rec["text"],
                    "origin": "projection",
                    "in_a_pool": False,
                    "projection_fused": mapped["C_P_scores"][cid],
                }
            )
            extra_hits.append(
                SearchHit(
                    chunk_id=rec["chunk_id"],
                    version_id=rec["version_id"],
                    section_path=rec["section_path"],
                    char_start=rec["char_start"],
                    char_end=rec["char_end"],
                    text=rec["text"],
                    score=mapped["C_P_scores"][cid],
                    rank=0,
                    retriever="projection_mapped",
                )
            )

        t0 = time.time()
        if extra_rows:
            extra_ce = ce.score_pairs(q, [r["text"] for r in extra_rows])
            for rec, s in zip(extra_rows, extra_ce, strict=True):
                ce_by_id[rec["chunk_id"]] = float(s)
        remat_ce_ms.append(lat_ce_e + (time.time() - t0) * 1000)

        x_rows = apply_blend_exp017(e_rows, extra_rows, ce_by_id)
        x_ids = {r["chunk_id"] for r in x_rows}
        if not c_e_ids.issubset(x_ids):
            raise SystemExit(f"STOP: anti-drop E-L10 failed on {case.case_id}")

        union_hits: list[SearchHit] = list(fused_e) + extra_hits
        x_pool_rows = []
        for i, h in enumerate(fused_e, start=1):
            x_pool_rows.append(hit_as_row(h, pool_rank=i, a_rank=int(h.rank), a_score=float(h.score)))
        for i, h in enumerate(extra_hits, start=len(fused_e) + 1):
            x_pool_rows.append(hit_as_row(h, pool_rank=i, a_rank=10**9, a_score=0.0))

        x_scored = score_system(case, x_rows, "exp017_rank", union_hits, gold_cover)
        for i, ref in enumerate(case.expected_evidence):
            x_scored["spans"][i]["pool_rank"] = first_span_rank(x_pool_rows, ref, "pool_rank")
            x_scored["spans"][i]["in_pool"] = span_in_hits(union_hits, ref)

        # Identity vs frozen EXP-017
        stored_cp = list(stored["C_P"])
        mm = {
            "case_id": case.case_id,
            "C_P_set_match": set(c_p_ids) == set(stored_cp),
            "C_P_list_match": c_p_ids == stored_cp,
            "e_pool_size_match": len(fused_e) == stored["e_pool_size"],
            "x_pool_size_match": len(x_rows) == stored["x_pool_size"],
            "gold": [],
        }
        for i, s in enumerate(x_scored["spans"]):
            st = stored["spans"][i]
            rec_g = {
                "span_index": i,
                "in_x_pool_match": bool(s["in_pool"]) == bool(st["in_x_pool"]),
                "x_rank_match": s["rank"] == st["x_rank"],
                "remat_in_x_pool": bool(s["in_pool"]),
                "stored_in_x_pool": bool(st["in_x_pool"]),
                "remat_x_rank": s["rank"],
                "stored_x_rank": st["x_rank"],
            }
            mm["gold"].append(rec_g)
        gold_ok = all(g["in_x_pool_match"] and g["x_rank_match"] for g in mm["gold"])
        membership_ok = mm["C_P_set_match"] and mm["e_pool_size_match"] and mm["x_pool_size_match"] and all(
            g["in_x_pool_match"] for g in mm["gold"]
        )
        mm["membership_ok"] = membership_ok
        mm["gold_x_rank_ok"] = gold_ok
        mm["identity_ok"] = membership_ok and mm["C_P_list_match"] and gold_ok
        if not mm["identity_ok"]:
            identity_mismatches.append(mm)

        dump = {
            "case_id": case.case_id,
            "C_P": c_p_ids,
            "C_P_scores": mapped["C_P_scores"],
            "e_pool_size": len(fused_e),
            "x_pool_size": len(x_rows),
            "members": [compact_row(r) for r in x_rows],
            "identity": mm,
            "recovery_seconds": round(time.time() - t_case, 3),
        }
        recovered_fh.write(json.dumps(dump, default=str) + "\n")
        recovered_fh.flush()

        print(
            f"{case.case_id} remat identity_ok={mm['identity_ok']} "
            f"C_P_set={mm['C_P_set_match']} list={mm['C_P_list_match']} "
            f"pools {len(fused_e)}/{len(x_rows)} gold_rank_ok={gold_ok} "
            f"CE_ms={remat_ce_ms[-1]:.0f}",
            flush=True,
        )

        t_rescore = time.time()
        y_rows = apply_blend_exp019a(x_rows)
        rescored_ms.append((time.time() - t_rescore) * 1000)

        y_scored = score_system(case, y_rows, "exp019a_rank", union_hits, gold_cover)
        for i, ref in enumerate(case.expected_evidence):
            y_scored["spans"][i]["pool_rank"] = first_span_rank(x_pool_rows, ref, "pool_rank")
            y_scored["spans"][i]["in_pool"] = span_in_hits(union_hits, ref)

        remat_x_cases[case.case_id] = x_scored
        y_cases[case.case_id] = y_scored
        remat_x_full[case.case_id] = x_scored["fully_recalled"]
        y_full[case.case_id] = y_scored["fully_recalled"]
        stored_x_full[case.case_id] = bool(stored["x_full"])
        cand_x.extend(x_scored["cand_ev_span_flags"])
        cand_y.extend(y_scored["cand_ev_span_flags"])
        pool_x.append(len(x_rows))
        pool_y.append(len(y_rows))

        destructions = []
        span_rows = []
        y_by_id = {r["chunk_id"]: r for r in y_rows}
        for i, ref in enumerate(case.expected_evidence):
            st = stored["spans"][i]
            s = {
                "span_index": i,
                "covering_chunk_ids": gold_cover[case.case_id][i],
                "exp017_rank": st["x_rank"],
                "exp019a_rank": y_scored["spans"][i]["rank"],
                "remat_exp017_rank": x_scored["spans"][i]["rank"],
                "in_exp017_pool": st["in_x_pool"],
                "in_019a_pool": y_scored["spans"][i]["in_pool"],
                "exp017_in_top_10": st["x_in_top_10"],
                "exp019a_in_top_10": y_scored["spans"][i]["within_10"],
                "entered_via_projection": st["entered_via_projection"],
            }
            if s["exp017_rank"] is not None and s["exp019a_rank"] is not None:
                s["rank_delta"] = int(s["exp017_rank"]) - int(s["exp019a_rank"])  # positive = improved
            else:
                s["rank_delta"] = None
            gold_cids = gold_cover[case.case_id][i]
            gold_member = None
            for cid in gold_cids:
                if cid in y_by_id:
                    gold_member = y_by_id[cid]
                    break
            if gold_member is not None:
                s["gold_chunk_id"] = gold_member["chunk_id"]
                s["in_e_l10"] = bool(gold_member.get("in_e_l10"))
                s["ce_norm"] = gold_member.get("ce_norm")
                s["retrieval_norm"] = gold_member.get("retrieval_norm")
                s["a_norm_exp017"] = gold_member.get("a_norm_exp017")
                s["blend_score_exp017"] = gold_member.get("blend_score_exp017")
                s["blend_score_019a"] = gold_member.get("blend_score")
                s["projection_fused"] = gold_member.get("projection_fused")
            span_rows.append(s)
            rank_movements.append({"case_id": case.case_id, **s})
            if st["x_rank"] == 1 and not y_scored["spans"][i]["within_10"]:
                destructions.append(s)
                rank1.append({"case_id": case.case_id, **s})

        per_case.append(
            {
                "case_id": case.case_id,
                "exp017_full": stored["x_full"],
                "exp019a_full": y_full[case.case_id],
                "e_pool_size": stored["e_pool_size"],
                "x_pool_size": stored["x_pool_size"],
                "y_pool_size": len(y_rows),
                "n_projection_additions": len(c_p_ids),
                "C_P": c_p_ids,
                "identity_ok": mm["identity_ok"],
                "spans": span_rows,
                "rank1_destruction_vs_EXP017": destructions,
                "rescoring_ms": round(rescored_ms[-1], 4),
            }
        )

    recovered_fh.close()

    hold_after = holdout_log_state()
    if hold_after != hold_before:
        raise SystemExit(f"STOP: holdout log changed {hold_before} -> {hold_after}")
    if _sha(D_FREEZE) != D_GUARD_SHA or _sha(D_RELEASE) != D_RELEASE_SHA:
        raise SystemExit("STOP: D freeze files mutated")
    if _sha(E_FILE) != E_FILE_SHA:
        raise SystemExit("STOP: SYSTEM-E-WITHIN-DOC.json mutated")
    if _sha(E_L10_FILE) != e_l10_sha_before:
        raise SystemExit("STOP: SYSTEM-E-L10-WITHIN-DOC.json mutated")
    if _sha(F_FILE) != hashlib.sha256(F_FILE.read_bytes()).hexdigest():
        pass  # tautology; keep F path read-only by never writing it

    n_id_fail = len(identity_mismatches)
    identity_payload = {
        "pool_identity_equivalent": n_id_fail == 0,
        "n_cases": 50,
        "n_mismatches": n_id_fail,
        "mismatches": identity_mismatches,
        "stored_artifact_inspect": stored_inspect,
        "recovery_method": "rematerialize_once_frozen_EXP-017_code",
        "ce_called_for_019a_ranks": False,
        "ce_called_for_recovery_only": True,
    }
    identity_path.write_text(json.dumps(identity_payload, indent=2, default=str) + "\n", encoding="utf-8")

    if n_id_fail:
        payload = {
            "experiment_id": "EXP-019A",
            "scored": False,
            "stop_reason": "implementation drift: rematerialized candidate identity != EXP-017-results.json",
            "n_mismatches": n_id_fail,
            "mismatches": identity_mismatches,
            "preregistration_json_sha256": PREREG_JSON_SHA,
            "SYSTEM-F-PROJECTION_config_hash": F_CONFIG_HASH,
            "holdout_json_opened": False,
            "validation_loaded": False,
            "hash_check": hash_check,
            "stored_artifact_inspect": stored_inspect,
        }
        write_stop(results_path, payload)
        report_path.write_text(
            "# EXP-019A\n\nSTOP: rematerialized candidate identity drifted vs EXP-017-results.json. "
            "019A ranks not accepted. See EXP-019A-pool-identity.json.\n",
            encoding="utf-8",
        )
        print("STOP identity drift", n_id_fail, flush=True)
        return 2

    # Decision vs frozen EXP-017 (stored x_full / x_rank), membership confirmed identical
    pair = paired(stored_x_full, y_full)
    m_y = metrics_from_cases(
        y_cases,
        "EXP-019A projection-only minmax(projection-RRF) a_norm",
        None,
        cand_y,
        pool_y,
        _mean(rescored_ms, 4),
    )
    cand_n = sum(cand_y)
    cand_d = len(cand_y)
    cand_str = f"{cand_n}/{cand_d}"
    regressions = pair["regressions"]
    rescues = pair["rescues"]
    n_rank1 = len(rank1)
    y_strict_n = sum(1 for ok in y_full.values() if ok)
    supported = (
        y_strict_n > BASELINE_STRICT
        and len(regressions) == 0
        and n_rank1 == 0
        and cand_n == BASELINE_CAND
        and cand_d == BASELINE_N
    )
    decision = "RERANK_MECHANISM_SUPPORTED" if supported else "NOT_SUPPORTED"

    diag_ids = ("V2D-33", "V2D-36")
    diagnostics_named = {}
    for cid in diag_ids:
        rec = next(r for r in per_case if r["case_id"] == cid)
        diagnostics_named[cid] = {
            "label": "DIAGNOSTIC_ONLY",
            "not_a_gate": True,
            "spans": rec["spans"],
            "exp017_full": rec["exp017_full"],
            "exp019a_full": rec["exp019a_full"],
        }

    improved = [m for m in rank_movements if m["rank_delta"] is not None and m["rank_delta"] > 0]
    worsened = [m for m in rank_movements if m["rank_delta"] is not None and m["rank_delta"] < 0]
    unchanged = [m for m in rank_movements if m["rank_delta"] == 0]
    still_none = [m for m in rank_movements if m["rank_delta"] is None]

    payload = {
        "experiment_id": "EXP-019A",
        "scored": True,
        "split": "v2-devset-001/development",
        "n": 50,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timestamp_et": datetime.now(UTC).astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%dT%H:%M:%S%z"),
        "preregistration_json_sha256": PREREG_JSON_SHA,
        "SYSTEM-F-PROJECTION_config_hash": F_CONFIG_HASH,
        "one_change": "projection-only a_norm = minmax(projection-RRF over P extras); E-L10 a_norm and EXP-017 CE minmax kept exactly; blend 0.7/0.3",
        "tuned_after_seeing_scores": False,
        "n_evals": 1,
        "second_variant": False,
        "validation_loaded": False,
        "holdout_loaded": False,
        "holdout_json_opened": False,
        "RELEASE": "NOT_FROZEN",
        "ce_called_for_019a_ranks": False,
        "recovery": {
            "stored_logits_a_norm_proj_rrf_existed": False,
            "method": "rematerialize_once_frozen_EXP-017_code",
            "identity_equivalent": True,
            "mean_recovery_ce_ms": _mean(remat_ce_ms),
        },
        "hash_check": hash_check,
        "holdout_access_log_before": hold_before,
        "holdout_access_log_after": hold_after,
        "holdout_log_unchanged": True,
        "embedding": emb,
        "environment": env_fingerprint(emb),
        "cross_encoder": {
            "name": CE_NAME,
            "revision": CE_REVISION,
            "artifact_sha256": CE_SHA256,
            "constructor": "CrossEncoderReranker() defaults",
            "fast": False,
            "pair_score_stable": ce_stable,
            "used_for": "EXP-017 logit recovery only; not recalled for 019A ranks",
        },
        "PRIMARY": {
            "strict_recall_at_10": m_y["strict_recall_at_10"],
            "n": y_strict_n,
            "d": 50,
            "baseline_SYSTEM_F_EXP017": f"{BASELINE_STRICT}/{BASELINE_N}",
            "strictly_greater_than_40_50": y_strict_n > BASELINE_STRICT,
        },
        "SECONDARY": {
            "candidate_gold_span_recall_at_100": cand_str,
            "span_recall_at_10": m_y["macro_span_recall"],
            "mrr": m_y["mrr"],
            "document_recall": m_y["document_recall"],
            "rescues_vs_EXP017": rescues,
            "regressions_vs_EXP017": regressions,
            "rank1_destructions": rank1,
            "rank1_destruction_count": n_rank1,
            "rank_movements": rank_movements,
            "rank_movements_summary": {
                "n_improved": len(improved),
                "n_worsened": len(worsened),
                "n_unchanged": len(unchanged),
                "n_still_absent": len(still_none),
                "mean_delta_among_ranked": (
                    round(statistics.mean([m["rank_delta"] for m in rank_movements if m["rank_delta"] is not None]), 2)
                    if any(m["rank_delta"] is not None for m in rank_movements)
                    else None
                ),
            },
            "rescoring_latency_ms_mean": _mean(rescored_ms, 4),
            "rescoring_latency_ms_sum": round(sum(rescored_ms), 4),
            "mean_final_candidate_pool": round(statistics.mean(pool_y), 2),
        },
        "DIAGNOSTICS": {
            "V2D-33": diagnostics_named["V2D-33"],
            "V2D-36": diagnostics_named["V2D-36"],
            "label": "DIAGNOSTIC_ONLY",
            "not_a_named_case_gate": True,
        },
        "pool_identity_equivalent": True,
        "EXP019A_metrics": m_y,
        "decision": decision,
        "decision_rule": {
            "RERANK_MECHANISM_SUPPORTED_iff": [
                "strict R@10 > 40/50",
                "0 strict R@10 regressions vs frozen EXP-017",
                "0 rank-1 destructions vs frozen EXP-017",
                "cand R@100 exactly 46/50",
            ],
            "otherwise": "NOT_SUPPORTED",
            "no_named_case_gate": True,
            "V2D-33_V2D-36": "DIAGNOSTIC_ONLY",
            "development_stage_not_independent_validation": True,
        },
        "freeze_files_untouched": {
            "SYSTEM-D-GUARD.json_sha256": _sha(D_FREEZE),
            "SYSTEM-D-RELEASE.json_sha256": _sha(D_RELEASE),
            "SYSTEM-E-WITHIN-DOC.json_sha256": _sha(E_FILE),
            "SYSTEM-E-L10-WITHIN-DOC.json_sha256": _sha(E_L10_FILE),
            "SYSTEM-F-PROJECTION.json_sha256": _sha(F_FILE),
        },
        "per_case": per_case,
        "runtime_seconds": round(time.time() - started, 1),
    }
    results_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    d33 = diagnostics_named["V2D-33"]["spans"][0]
    d36 = diagnostics_named["V2D-36"]["spans"][0]
    lines = [
        "# EXP-019A — projection-only retrieval-channel rescore",
        "",
        f"Timestamp: {payload['timestamp']} UTC. Dataset: V2-DEVSET-001 n=50 only. "
        f"Prereg json sha256 `{PREREG_JSON_SHA}`. SYSTEM-F-PROJECTION config_hash `{F_CONFIG_HASH}`. "
        f"Scored once. Not retuned. No second variant.",
        "",
        "gold150-v1 holdout.json not opened. Validation not loaded. "
        "SYSTEM-D / SYSTEM-E-WITHIN-DOC.json / SYSTEM-E-L10-WITHIN-DOC.json / cs_v1_control / "
        f"`{PROJECTION_SET_ID}` not modified. No third merge-RRF list. No candidate membership change. "
        "CE logits not recalled for 019A ranks. Blend 0.7/0.3 unchanged. No weight sweep. "
        "No query rewrite. RELEASE=NOT_FROZEN.",
        "",
        f"Holdout access log: {hold_before['log_bytes']} bytes sha `{hold_before['log_sha256']}` unchanged={hold_after == hold_before}.",
        "",
        "## Recovery",
        "",
        "EXP-017-results.json per_case does **not** store CE logits / a_norm / projection RRF. "
        "Rematerialized **once** with frozen EXP-017 code only. Candidate identities verified "
        "against EXP-017-results.json (C_P sets/lists, pool sizes, gold in_x_pool / x_rank). "
        f"**pool identity-equivalent = True**. Then 019A scoring applied in memory (CE not called again).",
        "",
        f"Mean rematerialization CE ms (recovery only): {payload['recovery']['mean_recovery_ce_ms']}.",
        "",
        "## ONE CHANGE",
        "",
        "E-L10 members: existing E-L10 a_norm kept exactly. Projection-only members: "
        "`minmax_norm` over the P projection-only fused scores for that query "
        "(degenerate 0.5 if constant) replaces a_norm=0.0. CE_norm kept exactly from EXP-017 union minmax. "
        "Blend 0.7*CE_norm + 0.3*retrieval_norm. Tie-break unchanged.",
        "",
        "## PRIMARY",
        "",
        f"strict R@10: **{m_y['strict_recall_at_10']}** vs SYSTEM-F / EXP-017 **40/50**. "
        f"Strictly greater: `{y_strict_n > BASELINE_STRICT}`.",
        "",
        "## SECONDARY",
        "",
        f"- cand R@100: {cand_str} (must 46/50; identity-equivalent `{cand_n == 46}`)",
        f"- span R@10: {m_y['macro_span_recall']} (EXP-017 0.80)",
        f"- MRR: {m_y['mrr']} (EXP-017 0.597)",
        f"- document recall: {m_y['document_recall']} (EXP-017 0.92)",
        f"- rescues vs EXP-017: {rescues or '—'}",
        f"- regressions vs EXP-017: {regressions or '—'}",
        f"- rank-1 destructions vs EXP-017: {n_rank1}",
        f"- rank movements: improved {len(improved)}, worsened {len(worsened)}, unchanged {len(unchanged)}, still absent {len(still_none)}; "
        f"mean delta (positive=improved) {payload['SECONDARY']['rank_movements_summary']['mean_delta_among_ranked']}",
        f"- rescoring latency: mean {payload['SECONDARY']['rescoring_latency_ms_mean']} ms / sum {payload['SECONDARY']['rescoring_latency_ms_sum']} ms "
        f"(019A blend only; recovery CE not included)",
        f"- mean pool: {payload['SECONDARY']['mean_final_candidate_pool']} (EXP-017 124.1)",
        "",
        "## DIAGNOSTICS (not a gate)",
        "",
        f"- V2D-33: EXP-017 rank {d33['exp017_rank']} → 019A rank {d33['exp019a_rank']} "
        f"(delta {d33['rank_delta']}); in_top_10 {d33['exp017_in_top_10']} → {d33['exp019a_in_top_10']}; "
        f"entered_via_projection={d33['entered_via_projection']}; retrieval_norm={d33.get('retrieval_norm')}; "
        f"ce_norm={d33.get('ce_norm')}",
        f"- V2D-36: EXP-017 rank {d36['exp017_rank']} → 019A rank {d36['exp019a_rank']} "
        f"(delta {d36['rank_delta']}); in_top_10 {d36['exp017_in_top_10']} → {d36['exp019a_in_top_10']}; "
        f"entered_via_projection={d36['entered_via_projection']}; retrieval_norm={d36.get('retrieval_norm')}; "
        f"ce_norm={d36.get('ce_norm')}",
        "",
        "## Decision (preregistered, not retuned)",
        "",
        f"**{decision}**",
        "",
        "RERANK_MECHANISM_SUPPORTED iff strict R@10 > 40/50 AND 0 strict R@10 regressions vs frozen EXP-017 "
        "AND 0 rank-1 destructions vs frozen EXP-017 AND cand R@100 exactly 46/50. "
        "Else NOT_SUPPORTED. Development-stage, not independent validation. Not a named-miss gate. No release freeze.",
        "",
        "## Standing",
        "",
        "No validation. No holdout. No retune. SYSTEM-F identity not edited. No release freeze.",
        "",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("decision", decision, "strict", m_y["strict_recall_at_10"], "cand", cand_str, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
