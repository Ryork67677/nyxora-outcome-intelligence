#!/usr/bin/env python3
"""EXP-017: single preregistered development run on V2-DEVSET-001 n=50.

Preregistration must already be hashed. Integrity fail-closed before scoring.
Does not open gold150-v1 holdout.json. Does not load validation. Does not
overwrite D/E freeze files or cs_v1_control. Does not start EXP-019. Does not
freeze a release. CrossEncoderReranker() defaults only (not fast=True).
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
sys.path.insert(0, str(ROOT / "experiments" / "EXP-018B" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cross_encoder import CE_NAME, CE_REVISION, CE_SHA256, CrossEncoderReranker  # noqa: E402
from rag_v1.db import connect  # noqa: E402
from rag_v1.embedders_transformer import TransformerEncoder  # noqa: E402
from rag_v1.evals.io import load_cases  # noqa: E402
from rag_v1.ids import content_hash  # noqa: E402
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

OUT_DIR = ROOT / "experiments" / "EXP-017"
GOLD_JSONL = ROOT / "evals" / "gold" / "v2-devset-001.jsonl"
SPLIT_PATH = ROOT / "evals" / "splits" / "v2-devset-001" / "development.json"
D_FREEZE = ROOT / "experiments" / "EXP-016" / "SYSTEM-D-GUARD.json"
D_RELEASE = ROOT / "experiments" / "EVAL-HOLDOUT-001" / "SYSTEM-D-RELEASE.json"
E_FILE = ROOT / "experiments" / "EXP-018" / "SYSTEM-E-WITHIN-DOC.json"
E_L10_FILE = ROOT / "experiments" / "EXP-018B" / "SYSTEM-E-L10-WITHIN-DOC.json"
PREREG_JSON = OUT_DIR / "EXP-017-preregistration.json"
PREREG_MD = OUT_DIR / "EXP-017-preregistration.md"
PREREG_JSON_SHA = "053a6bf14df088ca9e2283bc3e8dfb0769848a48c54c51a77fbe045795a80cc6"
GOLD_SHA = "cb687f3cc88b38d4beed7ad4bc829296a30518aaaf45cce0677ec568b1bf77e5"
SPLIT_SHA = "6b0c49c9040c215fde6134697c35a1f28458ba7d72ef012c0840feb7f9c3eb17"
FREEZE_SHA = "97ea6befbb4fd845f53da2aef20ba84cedaaf69c0f09e3ad90833b813fee2ad9"
E_FILE_SHA = "e228616beee1bcb13855c2eadee9fc20ec1fae3e54c77b28587114568c64d087"
D_GUARD_SHA = "e9267f5581404e9885598979204c08762cd33f362703e526b20f4d3430c35a82"
D_RELEASE_SHA = "1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40"
CHUNK_ID_AGG = "394a76b1569f0b46d4151442d5dba0fdf615beb2fc75355df743e0ea0979d93e"
SPAN_HASH = "44563cbb5abb4f9a6917b2398dca7b55df60d7359d368b9873b675c78937873b"
E_L10_HASH = "bae1c05b5c47c179dc5cd7972a14bd23d102a4d513b674667eb469e17cd85e89"
E_UNCAPPED_HASH = "7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe"
L = 10
P = 20
EL10_CAND = 44
EL10_N = 50


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mean(xs: list[float], ndigits: int = 1) -> float:
    return round(statistics.mean(xs), ndigits) if xs else 0.0


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


def metrics_from_cases(cases_map, name, cfg_hash, cand_flags, pool_sizes, latency_mean, extra=None):
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


def load_control_chunks() -> dict[str, dict]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT chunk_id, version_id, section_path, char_start, char_end, text
            FROM chunk WHERE chunk_set_id=%s
            """,
            (CHUNK_SET,),
        )
        out = {}
        for cid, vid, spath, cs, ce, text in cur.fetchall():
            out[cid] = {
                "chunk_id": cid,
                "version_id": vid,
                "section_path": list(spath),
                "char_start": cs,
                "char_end": ce,
                "text": text,
            }
    return out


def apply_blend_exp017(e_rows: list[dict], extra_rows: list[dict], ce_by_id: dict) -> list[dict]:
    """Keep E-L10 a_norm exactly. Projection-only a_norm=0.0. CE minmax over union."""
    e_ids = {r["chunk_id"] for r in e_rows}
    union: list[dict] = []
    for r in e_rows:
        item = dict(r)
        item["ce_score"] = float(ce_by_id[r["chunk_id"]])
        item["in_e_l10"] = True
        union.append(item)
    for r in extra_rows:
        if r["chunk_id"] in e_ids:
            continue
        item = dict(r)
        item["ce_score"] = float(ce_by_id[r["chunk_id"]])
        item["a_norm"] = 0.0
        item["a_rank"] = 10**9
        item["a_score"] = 0.0
        item["in_e_l10"] = False
        item["in_a_pool"] = False
        item["origin"] = "projection"
        union.append(item)
    ce_n = minmax_norm([r["ce_score"] for r in union])
    for row, ce in zip(union, ce_n, strict=True):
        row["ce_norm"] = ce
        row["blend_score"] = BLEND_CE * ce + BLEND_A * float(row["a_norm"])
    union.sort(key=lambda r: (-r["blend_score"], r["a_rank"], r["chunk_id"]))
    for i, row in enumerate(union, start=1):
        row["blend_rank"] = i
        row["exp017_rank"] = i
    return union


def run_integrity(hold_before: dict) -> dict:
    checks: list[dict] = []

    def add(name: str, ok: bool, observed, expected=None, detail=None):
        rec = {"name": name, "ok": bool(ok), "observed": observed}
        if expected is not None:
            rec["expected"] = expected
        if detail is not None:
            rec["detail"] = detail
        checks.append(rec)
        return ok

    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (CHUNK_SET,))
        n = cur.fetchone()[0]
        add("control_n", n == 14209, n, 14209)

        cur.execute(
            """
            SELECT encode(sha256(convert_to(string_agg(chunk_id, '' ORDER BY chunk_id), 'UTF8')), 'hex')
            FROM chunk WHERE chunk_set_id=%s
            """,
            (CHUNK_SET,),
        )
        agg = cur.fetchone()[0]
        add("chunk_id_agg_sha256", agg == CHUNK_ID_AGG, agg, CHUNK_ID_AGG)

        cur.execute(
            """
            SELECT encode(sha256(convert_to(string_agg(
                chunk_id || ':' || content_hash || ':' || char_start::text || ':' || char_end::text,
                E'\\n' ORDER BY chunk_id), 'UTF8')), 'hex')
            FROM chunk WHERE chunk_set_id=%s
            """,
            (CHUNK_SET,),
        )
        span = cur.fetchone()[0]
        add("span_hash_sha256", span == SPAN_HASH, span, SPAN_HASH)

        cur.execute(
            """
            SELECT count(*) FILTER (WHERE search_text IS NULL) AS st_null,
                   count(*) FILTER (WHERE context_header IS NULL) AS ch_null,
                   count(*)
            FROM chunk WHERE chunk_set_id=%s
            """,
            (CHUNK_SET,),
        )
        st_null, ch_null, n2 = cur.fetchone()
        add(
            "search_text_and_context_header_null",
            st_null == 14209 and ch_null == 14209 and n2 == 14209,
            {"search_text_null": st_null, "context_header_null": ch_null, "n": n2},
            {"search_text_null": 14209, "context_header_null": 14209, "n": 14209},
        )

        cur.execute(
            """
            SELECT count(*), min(ce.model_fingerprint), max(ce.model_fingerprint)
            FROM chunk_embedding ce
            JOIN chunk c ON c.chunk_id = ce.chunk_id
            WHERE c.chunk_set_id=%s AND ce.model_id=%s
            """,
            (CHUNK_SET, TRANSFORMER_MODEL),
        )
        n_emb, fp_min, fp_max = cur.fetchone()
        add(
            "minilm_control_embeddings",
            n_emb == 14209 and fp_min == fp_max == TRANSFORMER_FINGERPRINT,
            {"n": n_emb, "fp_min": fp_min, "fp_max": fp_max},
            {"n": 14209, "fp": TRANSFORMER_FINGERPRINT},
        )

        file_checks = {
            "SYSTEM-E-WITHIN-DOC.json": (E_FILE, E_FILE_SHA),
            "SYSTEM-D-GUARD.json": (D_FREEZE, D_GUARD_SHA),
            "SYSTEM-D-RELEASE.json": (D_RELEASE, D_RELEASE_SHA),
            "holdout-access.log.jsonl": (
                ROOT / "evals" / "splits" / "gold150-v1" / "holdout-access.log.jsonl",
                HOLD_LOG_SHA_AT_PREREG,
            ),
        }
        file_obs = {}
        files_ok = True
        for label, (path, expected) in file_checks.items():
            got = _sha(path)
            nbytes = path.stat().st_size
            rec = {"path": str(path.relative_to(ROOT)), "bytes": nbytes, "sha256": got, "expected": expected}
            file_obs[label] = rec
            if got != expected:
                files_ok = False
            if label == "holdout-access.log.jsonl" and nbytes != 235:
                files_ok = False
        add("frozen_file_bytes", files_ok, file_obs)

        cur.execute(
            "SELECT count(*) FROM search_projection WHERE projection_set_id=%s",
            (PROJECTION_SET_ID,),
        )
        n_proj = cur.fetchone()[0]
        cur.execute(
            """
            SELECT count(*) FROM (
              SELECT unnest(covering_chunk_ids) AS cid
              FROM search_projection WHERE projection_set_id=%s
            ) x
            LEFT JOIN chunk c ON c.chunk_id = x.cid AND c.chunk_set_id=%s
            WHERE c.chunk_id IS NULL
            """,
            (PROJECTION_SET_ID, CHUNK_SET),
        )
        n_bad_cover = cur.fetchone()[0]
        add(
            "covering_chunk_ids_all_control",
            n_bad_cover == 0 and n_proj > 0,
            {"n_projections": n_proj, "n_unknown_covering_ids": n_bad_cover},
        )

        cur.execute(
            """
            SELECT count(*) FROM search_projection sp
            JOIN document_version dv ON dv.version_id = sp.version_id
            WHERE sp.projection_set_id=%s
              AND (
                sp.text IS DISTINCT FROM substring(dv.normalized_text FROM sp.char_start+1 FOR (sp.char_end-sp.char_start))
                OR sp.content_hash IS DISTINCT FROM encode(sha256(convert_to(sp.text,'UTF8')), 'hex')
              )
            """,
            (PROJECTION_SET_ID,),
        )
        n_text_mismatch = cur.fetchone()[0]
        add(
            "projection_text_is_exact_source_substring",
            n_text_mismatch == 0 and n_proj > 0,
            {"n_mismatched": n_text_mismatch, "n_projections": n_proj},
        )

        cur.execute(
            """
            SELECT count(*) FILTER (WHERE projection_id NOT LIKE 'prj_%%') AS bad_prefix,
                   count(*) FILTER (WHERE projection_id LIKE 'chk_%%') AS chk_prefix
            FROM search_projection WHERE projection_set_id=%s
            """,
            (PROJECTION_SET_ID,),
        )
        bad_prefix, chk_prefix = cur.fetchone()
        cur.execute(
            """
            SELECT count(*) FROM search_projection sp
            JOIN chunk c ON c.chunk_id = sp.projection_id
            WHERE sp.projection_set_id=%s
            """,
            (PROJECTION_SET_ID,),
        )
        n_collide = cur.fetchone()[0]
        add(
            "projection_id_prefix_prj_no_chk_collision",
            bad_prefix == 0 and chk_prefix == 0 and n_collide == 0 and n_proj > 0,
            {"bad_prefix": bad_prefix, "chk_prefix": chk_prefix, "id_collisions_with_chunk": n_collide, "n": n_proj},
        )

        cur.execute(
            """
            SELECT count(*), min(pe.model_fingerprint), max(pe.model_fingerprint)
            FROM search_projection_embedding pe
            JOIN search_projection sp ON sp.projection_id = pe.projection_id
            WHERE pe.model_id=%s AND sp.projection_set_id=%s
            """,
            (TRANSFORMER_MODEL, PROJECTION_SET_ID),
        )
        n_pemb, pmin, pmax = cur.fetchone()
        add(
            "projection_embeddings_complete",
            n_pemb == n_proj and n_proj > 0 and pmin == pmax == TRANSFORMER_FINGERPRINT,
            {"n": n_pemb, "n_projections": n_proj, "fp_min": pmin, "fp_max": pmax},
            {"n": n_proj, "fp": TRANSFORMER_FINGERPRINT},
        )

        cur.execute(
            """
            SELECT pg_size_pretty(pg_total_relation_size('search_projection')),
                   pg_size_pretty(pg_total_relation_size('search_projection_embedding')),
                   pg_size_pretty(COALESCE(sum(pg_column_size(pe.embedding)),0)::bigint)
            FROM search_projection_embedding pe
            JOIN search_projection sp ON sp.projection_id = pe.projection_id
            WHERE pe.model_id=%s AND sp.projection_set_id=%s
            """,
            (TRANSFORMER_MODEL, PROJECTION_SET_ID),
        )
        proj_tbl, emb_tbl, emb_payload = cur.fetchone()

        cur.execute(
            "SELECT count(*) FROM chunk WHERE chunk_set_id=%s",
            (CHUNK_SET,),
        )
        n_after = cur.fetchone()[0]
        add("control_n_unchanged_after_projection_build", n_after == 14209, n_after, 14209)

    holdout_json_path = ROOT / "evals" / "splits" / "gold150-v1" / "holdout.json"
    add(
        "holdout_json_not_opened_and_log_unchanged",
        hold_before["log_bytes"] == 235
        and hold_before["log_sha256"] == HOLD_LOG_SHA_AT_PREREG
        and hold_before["lock_sha256"] == HOLD_LOCK_SHA
        and holdout_json_path.exists(),
        {
            "log_bytes": hold_before["log_bytes"],
            "log_sha256": hold_before["log_sha256"],
            "lock_sha256": hold_before["lock_sha256"],
            "holdout_json_exists_but_not_loaded": True,
            "validation_loaded": False,
            "gold150_v1_development_loaded": False,
        },
        {"log_bytes": 235, "log_sha256": HOLD_LOG_SHA_AT_PREREG},
    )

    passed = all(c["ok"] for c in checks)
    return {
        "pass": passed,
        "n_checks": len(checks),
        "n_failed": sum(1 for c in checks if not c["ok"]),
        "checks": checks,
        "projection_cardinality": n_proj,
        "projection_table_size": proj_tbl,
        "projection_embedding_table_size": emb_tbl,
        "projection_embedding_payload": emb_payload,
        "holdout_access_log": hold_before,
    }


def write_integrity(payload: dict) -> None:
    path = OUT_DIR / "EXP-017-integrity.json"
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def main() -> int:
    started = time.time()
    results_path = OUT_DIR / "EXP-017-results.json"
    report_path = OUT_DIR / "EXP-017-report.md"
    integrity_path = OUT_DIR / "EXP-017-integrity.json"
    if results_path.exists():
        raise SystemExit("STOP: EXP-017 results already exist; refusing to overwrite")
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

    emb = embedding_status()
    if not emb["complete"]:
        raise SystemExit(f"STOP: control embeddings incomplete: {emb}")

    print("running integrity checks...", flush=True)
    integrity = run_integrity(hold_before)
    integrity["timestamp"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    integrity["preregistration_json_sha256"] = PREREG_JSON_SHA
    integrity["SYSTEM-E-WITHIN-DOC_config_hash"] = E_UNCAPPED_HASH
    integrity["SYSTEM-E-WITHIN-DOC_file_sha256"] = E_FILE_SHA
    integrity["SYSTEM-E-L10-WITHIN-DOC_config_hash"] = E_L10_HASH
    write_integrity(integrity)
    print("INTEGRITY", "PASS" if integrity["pass"] else "FAIL", "n_proj", integrity["projection_cardinality"], flush=True)

    if not integrity["pass"]:
        failed = [c for c in integrity["checks"] if not c["ok"]]
        payload = {
            "experiment_id": "EXP-017",
            "scored": False,
            "stop_reason": "integrity fail-closed",
            "integrity_pass": False,
            "failed_checks": failed,
            "preregistration_json_sha256": PREREG_JSON_SHA,
            "holdout_access_log": hold_before,
            "holdout_json_opened": False,
            "validation_loaded": False,
        }
        results_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
        report_path.write_text(
            "# EXP-017\n\nINTEGRITY FAIL. Scoring not run. See EXP-017-integrity.json.\n\n"
            + json.dumps(failed, indent=2, default=str)
            + "\n",
            encoding="utf-8",
        )
        print("STOP after integrity failure", flush=True)
        return 2

    encoder = TransformerEncoder(max_seq=512).load()
    if encoder.model_version != TRANSFORMER_FINGERPRINT:
        raise SystemExit("STOP: live encoder fingerprint mismatch")
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)
    ce = CrossEncoderReranker()  # defaults; not fast=True
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

    lat_a, lat_local, lat_proj, lat_ce, lat_total = [], [], [], [], []
    e_cases, x_cases = {}, {}
    e_full, x_full = {}, {}
    cand_e, cand_x = [], []
    pool_e, pool_x, add_counts = [], [], []
    per_case = []
    rank1 = []
    diag_hits, diag_multi, diag_absent, diag_below10 = [], [], [], []

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

        t0 = time.time()
        fused_p = projection_rrf(q, TRANSFORMER_MODEL, transformer)
        mapped = map_to_canonical_extras(fused_p, c_e_ids, P)
        c_p_ids = mapped["C_P"]
        lat_proj.append((time.time() - t0) * 1000)

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
        lat_ce.append(lat_ce_e + (time.time() - t0) * 1000)

        x_rows = apply_blend_exp017(e_rows, extra_rows, ce_by_id)
        x_ids = {r["chunk_id"] for r in x_rows}
        if not c_e_ids.issubset(x_ids):
            raise SystemExit(f"STOP: anti-drop E-L10 failed on {case.case_id}")

        union_hits: list[SearchHit] = list(fused_e) + extra_hits
        lat_total.append((time.time() - t_case) * 1000)

        e_pool_rows = [
            hit_as_row(h, pool_rank=int(h.rank), a_rank=int(h.rank), a_score=float(h.score))
            for h in fused_e
        ]
        x_pool_rows = []
        for i, h in enumerate(fused_e, start=1):
            x_pool_rows.append(
                hit_as_row(h, pool_rank=i, a_rank=int(h.rank), a_score=float(h.score))
            )
        for i, h in enumerate(extra_hits, start=len(fused_e) + 1):
            x_pool_rows.append(
                hit_as_row(h, pool_rank=i, a_rank=10**9, a_score=0.0)
            )

        e_scored = score_system(case, e_rows, "e_rank", fused_e, gold_cover)
        for i, ref in enumerate(case.expected_evidence):
            e_scored["spans"][i]["pool_rank"] = first_span_rank(e_pool_rows, ref, "pool_rank")
            e_scored["spans"][i]["in_pool"] = span_in_hits(fused_e, ref)

        x_scored = score_system(case, x_rows, "exp017_rank", union_hits, gold_cover)
        for i, ref in enumerate(case.expected_evidence):
            x_scored["spans"][i]["pool_rank"] = first_span_rank(x_pool_rows, ref, "pool_rank")
            x_scored["spans"][i]["in_pool"] = span_in_hits(union_hits, ref)

        e_cases[case.case_id] = e_scored
        x_cases[case.case_id] = x_scored
        e_full[case.case_id] = e_scored["fully_recalled"]
        x_full[case.case_id] = x_scored["fully_recalled"]
        cand_e.extend(e_scored["cand_ev_span_flags"])
        cand_x.extend(x_scored["cand_ev_span_flags"])
        pool_e.append(len(fused_e))
        pool_x.append(len(x_rows))
        add_counts.append(len(c_p_ids))
        diag_hits.append(mapped["n_projection_hits"])
        diag_multi.append(mapped["n_mapping_to_multiple_canonical"])
        diag_absent.append(mapped["n_previously_absent"])

        gold_below = []
        destructions = []
        span_rows = []
        for i, ref in enumerate(case.expected_evidence):
            s = {
                "span_index": i,
                "covering_chunk_ids": gold_cover[case.case_id][i],
                "e_rank": e_scored["spans"][i]["rank"],
                "x_rank": x_scored["spans"][i]["rank"],
                "e_pool_rank": e_scored["spans"][i]["pool_rank"],
                "x_pool_rank": x_scored["spans"][i]["pool_rank"],
                "in_e_pool": e_scored["spans"][i]["in_pool"],
                "in_x_pool": x_scored["spans"][i]["in_pool"],
                "e_in_top_10": e_scored["spans"][i]["within_10"],
                "x_in_top_10": x_scored["spans"][i]["within_10"],
                "entered_via_projection": (not e_scored["spans"][i]["in_pool"]) and x_scored["spans"][i]["in_pool"],
            }
            span_rows.append(s)
            if s["in_x_pool"] and not s["x_in_top_10"]:
                gold_below.append(s)
            if s["e_rank"] == 1 and not s["x_in_top_10"]:
                destructions.append(s)
                rank1.append({"case_id": case.case_id, **s})
        if gold_below:
            diag_below10.append({"case_id": case.case_id, "spans": gold_below})

        rec = {
            "case_id": case.case_id,
            "e_full": e_full[case.case_id],
            "x_full": x_full[case.case_id],
            "parents": parents,
            "a_pool_size": len(a_pool),
            "e_pool_size": len(fused_e),
            "x_pool_size": len(x_rows),
            "n_projection_additions": len(c_p_ids),
            "n_el10_new_union": len(new_ids),
            "anti_drop_el10": c_e_ids.issubset(x_ids),
            "n_projection_hits": mapped["n_projection_hits"],
            "n_mapping_to_multiple_canonical": mapped["n_mapping_to_multiple_canonical"],
            "n_previously_absent": mapped["n_previously_absent"],
            "C_P": c_p_ids,
            "spans": span_rows,
            "rank1_destruction_vs_EL10": destructions,
            "latency_ms": {
                "system_a_retrieval": round(lat_a[-1], 2),
                "local_bm25": round(lat_local[-1], 2),
                "projection_lane": round(lat_proj[-1], 2),
                "cross_encoder": round(lat_ce[-1], 2),
                "total": round(lat_total[-1], 2),
            },
        }
        per_case.append(rec)
        print(
            f"{case.case_id} E={int(e_full[case.case_id])} X={int(x_full[case.case_id])} "
            f"candE={int(e_scored['cand_ev_span_flags'][0]) if e_scored['cand_ev_span_flags'] else 0} "
            f"candX={int(x_scored['cand_ev_span_flags'][0]) if x_scored['cand_ev_span_flags'] else 0} "
            f"pool {len(fused_e)}->{len(x_rows)} P={len(c_p_ids)} "
            f"proj_ms={lat_proj[-1]:.0f} CE_ms={lat_ce[-1]:.0f} tot={lat_total[-1]:.0f}",
            flush=True,
        )

    hold_after = holdout_log_state()
    if hold_after != hold_before:
        raise SystemExit(f"STOP: holdout log changed {hold_before} -> {hold_after}")
    if _sha(D_FREEZE) != D_GUARD_SHA or _sha(D_RELEASE) != D_RELEASE_SHA:
        raise SystemExit("STOP: D freeze files mutated")
    if _sha(E_FILE) != E_FILE_SHA:
        raise SystemExit("STOP: SYSTEM-E-WITHIN-DOC.json mutated")
    if _sha(E_L10_FILE) != e_l10_sha_before:
        raise SystemExit("STOP: SYSTEM-E-L10-WITHIN-DOC.json mutated")

    m_e = metrics_from_cases(
        e_cases, "rematerialized SYSTEM-E-L10-WITHIN-DOC",
        E_L10_HASH, cand_e, pool_e, _mean(lat_a) + _mean(lat_local) + _mean(lat_ce),
    )
    m_x = metrics_from_cases(
        x_cases, "EXP-017 projection additive P=20 on E-L10",
        None, cand_x, pool_x, _mean(lat_total),
        extra={"new_projection_members_mean": round(statistics.mean(add_counts), 2)},
    )
    pair = paired(e_full, x_full)
    cand_n = sum(cand_x)
    cand_d = len(cand_x)
    cand_str = f"{cand_n}/{cand_d}"
    regressions = pair["regressions"]
    n_rank1 = len(rank1)
    mechanism = (
        cand_n > EL10_CAND
        and len(regressions) == 0
        and n_rank1 == 0
    )
    decision = "MECHANISM_SUPPORTED" if mechanism else "MECHANISM_NOT_SUPPORTED"

    gold_in_pool_below = []
    for rec in per_case:
        for s in rec["spans"]:
            if s["in_x_pool"] and not s["x_in_top_10"]:
                gold_in_pool_below.append(
                    {
                        "case_id": rec["case_id"],
                        "span_index": s["span_index"],
                        "x_rank": s["x_rank"],
                        "entered_via_projection": s["entered_via_projection"],
                    }
                )

    payload = {
        "experiment_id": "EXP-017",
        "scored": True,
        "split": "v2-devset-001/development",
        "n": 50,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timestamp_et": datetime.now(UTC).astimezone(__import__("zoneinfo").ZoneInfo("America/New_York")).strftime("%Y-%m-%dT%H:%M:%S%z"),
        "preregistration_json_sha256": PREREG_JSON_SHA,
        "integrity_pass": True,
        "projection_set_id": PROJECTION_SET_ID,
        "projection_count": integrity["projection_cardinality"],
        "P": P,
        "L": L,
        "tuned_after_seeing_scores": False,
        "validation_loaded": False,
        "holdout_loaded": False,
        "holdout_json_opened": False,
        "RELEASE": "NOT_FROZEN",
        "hash_labeling": {
            "SYSTEM-E-WITHIN-DOC_config_hash": E_UNCAPPED_HASH,
            "SYSTEM-E-WITHIN-DOC_file_sha256": E_FILE_SHA,
            "SYSTEM-E-L10-WITHIN-DOC_config_hash": E_L10_HASH,
            "note": "config_hash and file SHA256 kept distinct",
        },
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
        },
        "PRIMARY": {
            "candidate_gold_span_recall_at_100": cand_str,
            "n": cand_n,
            "d": cand_d,
            "baseline_EL10": f"{EL10_CAND}/{EL10_N}",
            "strictly_greater_than_44_50": cand_n > EL10_CAND,
        },
        "SECONDARY": {
            "strict_recall_at_10": m_x["strict_recall_at_10"],
            "span_recall_at_10": m_x["macro_span_recall"],
            "mrr": m_x["mrr"],
            "document_recall": m_x["document_recall"],
            "rescues_vs_EL10": pair["rescues"],
            "regressions_vs_EL10": regressions,
            "rank1_destructions": rank1,
            "rank1_destruction_count": n_rank1,
            "mean_projection_additions": round(statistics.mean(add_counts), 2),
            "mean_final_candidate_pool": round(statistics.mean(pool_x), 2),
            "A_global_latency_ms": _mean(lat_a),
            "local_BM25_latency_ms": _mean(lat_local),
            "projection_lane_latency_ms": _mean(lat_proj),
            "CE_latency_ms": _mean(lat_ce),
            "total_latency_ms": _mean(lat_total),
        },
        "DIAGNOSTICS": {
            "mean_projection_hits": round(statistics.mean(diag_hits), 2) if diag_hits else 0,
            "mean_mapping_to_multiple_canonical": round(statistics.mean(diag_multi), 2) if diag_multi else 0,
            "sum_mapping_to_multiple_canonical": int(sum(diag_multi)),
            "mean_previously_absent_canonical": round(statistics.mean(diag_absent), 2) if diag_absent else 0,
            "gold_in_pool_below_top10": gold_in_pool_below,
            "n_gold_in_pool_below_top10": len(gold_in_pool_below),
            "projection_cardinality": integrity["projection_cardinality"],
            "projection_table_size": integrity["projection_table_size"],
            "projection_embedding_table_size": integrity["projection_embedding_table_size"],
            "projection_embedding_payload": integrity["projection_embedding_payload"],
            "integrity_hashes": {
                "chunk_id_agg_sha256": CHUNK_ID_AGG,
                "span_hash_sha256": SPAN_HASH,
                "holdout_log_sha256": HOLD_LOG_SHA_AT_PREREG,
                "SYSTEM-E-WITHIN-DOC_file_sha256": E_FILE_SHA,
                "SYSTEM-E-WITHIN-DOC_config_hash": E_UNCAPPED_HASH,
                "preregistration_json_sha256": PREREG_JSON_SHA,
            },
        },
        "EL10_rematerialized": m_e,
        "EXP017_metrics": m_x,
        "decision": decision,
        "decision_rule": {
            "MECHANISM_SUPPORTED_iff": [
                "candidate gold-span recall > 44/50",
                "0 strict R@10 regressions vs E-L10",
                "0 rank-1 destructions vs E-L10",
            ],
            "development_stage_not_independent_validation": True,
            "not_a_named_miss_gate": True,
        },
        "freeze_files_untouched": {
            "SYSTEM-D-GUARD.json_sha256": _sha(D_FREEZE),
            "SYSTEM-D-RELEASE.json_sha256": _sha(D_RELEASE),
            "SYSTEM-E-WITHIN-DOC.json_sha256": _sha(E_FILE),
            "SYSTEM-E-L10-WITHIN-DOC.json_sha256": _sha(E_L10_FILE),
        },
        "per_case": per_case,
        "runtime_seconds": round(time.time() - started, 1),
    }
    results_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    lines = [
        "# EXP-017 — search-projection / evidence-preserving retrieval",
        "",
        f"Timestamp: {payload['timestamp']} UTC. Dataset: V2-DEVSET-001 n=50 only. "
        f"Prereg json sha256 `{PREREG_JSON_SHA}`. Integrity **PASS**. Scored once. Not retuned.",
        "",
        "gold150-v1 holdout.json not opened. Validation not loaded. "
        "SYSTEM-D / SYSTEM-E-WITHIN-DOC.json / SYSTEM-E-L10-WITHIN-DOC.json / cs_v1_control not overwritten. "
        "No third merge-RRF list. Projection-only A-channel = 0.0 (not minmax_degenerate=0.5). "
        "No extra windows/strides/P. No query rewrite. RELEASE=NOT_FROZEN.",
        "",
        f"Holdout access log: {hold_before['log_bytes']} bytes sha `{hold_before['log_sha256']}` unchanged={hold_after == hold_before}.",
        "",
        "## Integrity",
        "",
        f"PASS. Projection set `{PROJECTION_SET_ID}` cardinality **{integrity['projection_cardinality']}**. "
        f"Table {integrity['projection_table_size']}; embedding table {integrity['projection_embedding_table_size']}; "
        f"payload {integrity['projection_embedding_payload']}.",
        "",
        "Hash labeling (kept distinct):",
        "",
        f"- SYSTEM-E-WITHIN-DOC **config_hash** `{E_UNCAPPED_HASH}`",
        f"- SYSTEM-E-WITHIN-DOC **file SHA256** `{E_FILE_SHA}`",
        f"- SYSTEM-E-L10-WITHIN-DOC **config_hash** `{E_L10_HASH}`",
        "",
        "## PRIMARY",
        "",
        f"Candidate gold-span recall: **{cand_str}** vs frozen E-L10 **44/50**. "
        f"Strictly greater: `{cand_n > EL10_CAND}`.",
        "",
        "## SECONDARY",
        "",
        f"- strict R@10: {m_x['strict_recall_at_10']} (E-L10 rematerialized {m_e['strict_recall_at_10']})",
        f"- span R@10: {m_x['macro_span_recall']} (E-L10 {m_e['macro_span_recall']})",
        f"- MRR: {m_x['mrr']} (E-L10 {m_e['mrr']})",
        f"- document recall: {m_x['document_recall']} (E-L10 {m_e['document_recall']})",
        f"- rescues vs E-L10: {pair['rescues'] or '—'}",
        f"- regressions vs E-L10: {regressions or '—'}",
        f"- rank-1 destructions: {n_rank1}",
        f"- mean projection additions: {payload['SECONDARY']['mean_projection_additions']}",
        f"- mean final pool: {payload['SECONDARY']['mean_final_candidate_pool']} (E-L10 remat {m_e['pool_size_mean']}; frozen E-L10 104.1)",
        f"- latency ms: A {payload['SECONDARY']['A_global_latency_ms']} / local BM25 {payload['SECONDARY']['local_BM25_latency_ms']} / "
        f"projection {payload['SECONDARY']['projection_lane_latency_ms']} / CE {payload['SECONDARY']['CE_latency_ms']} / "
        f"total {payload['SECONDARY']['total_latency_ms']}",
        "",
        "## DIAGNOSTICS",
        "",
        f"- mean projection hits: {payload['DIAGNOSTICS']['mean_projection_hits']}",
        f"- mapping to multiple canonical chunks (sum over queries): {payload['DIAGNOSTICS']['sum_mapping_to_multiple_canonical']}",
        f"- mean previously absent canonical chunks from mapping: {payload['DIAGNOSTICS']['mean_previously_absent_canonical']}",
        f"- gold in pool but below top-10: {payload['DIAGNOSTICS']['n_gold_in_pool_below_top10']} "
        f"(EXP-019 headroom; entered_via_projection listed in results JSON)",
        "",
        "## Decision (preregistered, not retuned)",
        "",
        f"**{decision}**",
        "",
        "MECHANISM_SUPPORTED iff candidate gold-span recall > 44/50 AND 0 strict R@10 regressions vs E-L10 AND 0 rank-1 destructions vs E-L10. "
        "Development-stage, not independent validation. Not a named-miss gate. No release freeze.",
        "",
        "## Standing",
        "",
        "No EXP-019. No validation. No holdout. No retune.",
        "",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("decision", decision, "cand", cand_str, "wrote", results_path, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
