#!/usr/bin/env python3
"""EVAL-NATQ-VAL-001: one validation run of frozen SYSTEM-H on NATQ-001 n=40.

Preregistration MUST already be hashed. Loads ONLY validation.jsonl.
Does not open NATQ holdout.json or gold150-v1 holdout.json.
Does not modify SYSTEM-H / SYSTEM-G / SYSTEM-G-CE-D1.
Does not retune. Does not run a second time. Does not freeze a release.
Reuses EXP-017 / EXP-019A / PERF-003 D1 / EXP-018B code.
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
sys.path.insert(0, str(ROOT / "experiments" / "PERF-003" / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-019A" / "scripts"))

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
from run_exp017 import (  # noqa: E402
    L,
    P,
    apply_blend_exp017,
    load_control_chunks,
    score_system,
)
from run_exp018_development import (  # noqa: E402
    env_fingerprint,
    first_span_rank,
    hit_as_row,
    span_in_hits,
    summarise,
)
from run_exp019a import apply_blend_exp019a  # noqa: E402
from system_e import (  # noqa: E402
    A_HASH,
    BLEND_A,
    BLEND_CE,
    CHUNK_SET,
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
)
from v2_system_g_ce import make_v2_system_g_d1_reranker  # noqa: E402
from cross_encoder import CE_NAME, CE_REVISION, CE_SHA256  # noqa: E402

OUT_DIR = ROOT / "experiments" / "RAG-V2" / "EVAL-NATQ-VAL-001"
VAL_JSONL = ROOT / "evals" / "splits" / "natq-001" / "validation.jsonl"
VAL_JSON = ROOT / "evals" / "splits" / "natq-001" / "validation.json"
H_FILE = ROOT / "experiments" / "RAG-V2" / "SYSTEM-H-V2-DEV-CANDIDATE" / "SYSTEM-H-V2-DEV-CANDIDATE.json"
G_FILE = ROOT / "experiments" / "EXP-019A" / "SYSTEM-G-PROJECTION-PRIOR.json"
G_CE_D1 = ROOT / "experiments" / "PERF-003" / "SYSTEM-G-CE-D1.json"
PREREG_JSON = OUT_DIR / "EVAL-NATQ-VAL-001-preregistration.json"
PREREG_MD = OUT_DIR / "EVAL-NATQ-VAL-001-preregistration.md"
NATQ_HOLD_LOG = ROOT / "evals" / "splits" / "natq-001" / "holdout-access.log.jsonl"
NATQ_HOLD_LOCK = ROOT / "evals" / "splits" / "natq-001" / "holdout.lock.json"
V1_HOLD_LOG = ROOT / "evals" / "splits" / "gold150-v1" / "holdout-access.log.jsonl"

PREREG_JSON_SHA = "3d91f14acfa2cbc1c0368781ac0dd4783cc331677e6d0ecc425ed07b1abd1dd3"
H_CONFIG_HASH = "7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a"
H_FILE_SHA = "7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475"
VAL_SHA = "a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6"
NATQ_LOG_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
V1_LOG_SHA = "45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3"
NATQ_LOCK_SHA = "03e0d5749e61e73e6b9582109a74a4a9672610b7bf794daf25f46999e5ad40b2"
G_FILE_SHA = "7f4ff6db09f32e55cac820cbc00d87ce2ae91886d444c3bad20ac3e04c7f0f61"
G_CE_D1_SHA = "cf0c985c5f7738e7fc5422039fd6940621d8dcd8f91de41abe3784ac53a6a7ec"
G_HASH = "563a7b790564fa1efb96257e988c4b1ccfab45146825d2a366b2fee0ca5d5790"
G_CE_D1_HASH = "6d108568f3131bad87d8617f5c2fb88ea14428e397d59ff54ff8e11cc4647b7d"
PROJ_CFG_HASH = "7fd5034c9510a1e08ec76bd22b020703c586dd12e7c02659397df05c5c365a8e"
CLASS_PRIORITY = (
    "document-discovery",
    "candidate-generation",
    "evidence-granularity",
    "ranking",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mean(xs: list[float], ndigits: int = 1) -> float:
    return round(statistics.mean(xs), ndigits) if xs else 0.0


def _median(xs: list[float], ndigits: int = 1) -> float:
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


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    from scipy.stats import beta

    if n <= 0:
        return (0.0, 1.0)
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2.0, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))
    return (round(lo, 4), round(hi, 4))


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


def overlap_ignoring_section(version_id: str, char_start: int, char_end: int) -> list[str]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT chunk_id FROM chunk
            WHERE chunk_set_id=%s AND version_id=%s
              AND char_start < %s AND char_end > %s
            ORDER BY chunk_id
            """,
            (CHUNK_SET, version_id, char_end, char_start),
        )
        return [r[0] for r in cur.fetchall()]


def classify_failure(case, scored, a_pool, parents, gold_cover) -> dict:
    a_vids = {h.version_id for h in a_pool}
    parent_set = set(parents)
    span_classes: list[str] = []
    details: list[dict] = []
    gold_ambiguity_flags: list[dict] = []
    for i, span in enumerate(scored["spans"]):
        ref = case.expected_evidence[i]
        covering = gold_cover[case.case_id][i]
        rec = {
            "span_index": i,
            "in_pool": bool(span["in_pool"]),
            "within_10": bool(span["within_10"]),
            "rank": span["rank"],
            "covering_n": len(covering),
            "gold_version_id": ref.version_id,
            "gold_in_a_pool_docs": ref.version_id in a_vids,
            "gold_in_parents": ref.version_id in parent_set,
        }
        if span["within_10"]:
            rec["class"] = "ok"
            details.append(rec)
            continue
        if not covering:
            other = overlap_ignoring_section(ref.version_id, ref.char_start, ref.char_end)
            rec["overlap_ignoring_section_n"] = len(other)
            if other:
                klass = "evidence-granularity"
            else:
                klass = "evidence-granularity"
                gold_ambiguity_flags.append(
                    {
                        "case_id": case.case_id,
                        "span_index": i,
                        "reason": "no cs_v1_control chunk overlaps gold span even ignoring section_path",
                    }
                )
            rec["class"] = klass
            span_classes.append(klass)
            details.append(rec)
            continue
        if not span["in_pool"]:
            if ref.version_id not in a_vids:
                klass = "document-discovery"
            else:
                klass = "candidate-generation"
            rec["class"] = klass
            span_classes.append(klass)
            details.append(rec)
            continue
        rec["class"] = "ranking"
        span_classes.append("ranking")
        details.append(rec)
    primary = None
    for cand in CLASS_PRIORITY:
        if cand in span_classes:
            primary = cand
            break
    return {
        "primary": primary,
        "span_classes": span_classes,
        "spans": details,
        "gold_ambiguity_flags": gold_ambiguity_flags,
    }


def subset_ids(raw: list[dict], pred) -> list[str]:
    return [r["case_id"] for r in raw if pred(r)]


def metrics_for_ids(ids: list[str], cases_map: dict) -> dict:
    sub = {cid: cases_map[cid] for cid in ids if cid in cases_map}
    if not sub:
        return {"n_cases": 0}
    s = summarise(sub, "subset", H_CONFIG_HASH)
    all_spans = [sp for c in sub.values() for sp in c["spans"]]
    cand_n = sum(1 for sp in all_spans if sp["in_pool"])
    cases_all_in_pool = sum(1 for c in sub.values() if all(sp["in_pool"] for sp in c["spans"]))
    docs_ok = sum(1 for c in sub.values() if c["doc_recall"] == 1.0)
    n = len(sub)
    n_spans = len(all_spans)
    return {
        "n_cases": n,
        "strict": f"{s['cases_fully_recalled']}/{n}",
        "strict_n": s["cases_fully_recalled"],
        "candidate_gold_span_recall_at_100": f"{cases_all_in_pool}/{n}",
        "candidate_gold_span_n": cases_all_in_pool,
        "evidence_span_recall_at_10_micro": round((s["spans_found_at_10"] / n_spans) if n_spans else 1.0, 4),
        "evidence_span_found": f"{s['spans_found_at_10']}/{n_spans}",
        "macro_span_recall": s["macro_span_recall"],
        "document_recall_at_10": f"{docs_ok}/{n}",
        "document_recall_n": docs_ok,
        "document_recall_mean": s["document_recall"],
        "mrr": s["mrr"],
        "candidate_span_flags": f"{cand_n}/{n_spans}",
    }


def main() -> int:
    started = time.time()
    results_path = OUT_DIR / "EVAL-NATQ-VAL-001-REPORT.json"
    report_path = OUT_DIR / "EVAL-NATQ-VAL-001-REPORT.md"
    pools_path = OUT_DIR / "logs" / "EVAL-NATQ-VAL-001-pools.jsonl"
    if results_path.exists() or report_path.exists():
        raise SystemExit("STOP: EVAL-NATQ-VAL-001 results already exist; refusing to overwrite / second run")
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
    recomputed = config_hash(h_obj["config"])
    if recomputed != H_CONFIG_HASH:
        raise SystemExit(f"STOP: recomputed SYSTEM-H config_hash {recomputed} != frozen")
    if h_obj.get("DEVELOPMENT_ARCHITECTURE_FROZEN") is not True:
        raise SystemExit("STOP: SYSTEM-H DEVELOPMENT_ARCHITECTURE_FROZEN is not true")
    if h_obj.get("RELEASE_FROZEN") is not False:
        raise SystemExit("STOP: SYSTEM-H RELEASE_FROZEN drifted")
    if _sha(G_FILE) != G_FILE_SHA:
        raise SystemExit("STOP: SYSTEM-G file mutated")
    if _sha(G_CE_D1) != G_CE_D1_SHA:
        raise SystemExit("STOP: SYSTEM-G-CE-D1 file mutated")
    g_obj = json.loads(G_FILE.read_text(encoding="utf-8"))
    d1_obj = json.loads(G_CE_D1.read_text(encoding="utf-8"))
    if g_obj.get("config_hash") != G_HASH:
        raise SystemExit("STOP: SYSTEM-G config_hash mismatch")
    if d1_obj.get("config_hash") != G_CE_D1_HASH:
        raise SystemExit("STOP: SYSTEM-G-CE-D1 config_hash mismatch")
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

    hash_check = {
        "prereg_json_sha256": got_pre,
        "prereg_json_sha256_ok": got_pre == PREREG_JSON_SHA,
        "validation_sha256": val_sha,
        "validation_sha256_ok": val_sha == VAL_SHA,
        "SYSTEM_H_config_hash": h_obj["config_hash"],
        "SYSTEM_H_config_hash_recomputed": recomputed,
        "SYSTEM_H_config_hash_ok": recomputed == H_CONFIG_HASH == h_obj["config_hash"],
        "SYSTEM_H_file_sha256": h_sha,
        "SYSTEM_H_file_sha256_ok": h_sha == H_FILE_SHA,
        "SYSTEM_G_file_sha256_ok": _sha(G_FILE) == G_FILE_SHA,
        "SYSTEM_G_CE_D1_file_sha256_ok": _sha(G_CE_D1) == G_CE_D1_SHA,
        "projection_set": proj,
        "natq_holdout_access_log": natq_before,
        "v1_holdout_access_log": {
            "log_bytes": v1_before["log_bytes"],
            "log_sha256": v1_before["log_sha256"],
        },
        "n": 40,
        "snapshot": SNAPSHOT,
        "snapshot_ok": proj["snapshot_ok"],
    }
    if not all(
        [
            hash_check["prereg_json_sha256_ok"],
            hash_check["validation_sha256_ok"],
            hash_check["SYSTEM_H_config_hash_ok"],
            hash_check["SYSTEM_H_file_sha256_ok"],
            hash_check["projection_set"]["ok"],
            natq_before["log_bytes"] == 0,
        ]
    ):
        raise SystemExit(f"STOP: pre-retrieval verification failed {hash_check}")

    encoder = TransformerEncoder(max_seq=512).load()
    if encoder.model_version != TRANSFORMER_FINGERPRINT:
        raise SystemExit("STOP: live encoder fingerprint mismatch")
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)
    ce = make_v2_system_g_d1_reranker()
    probe_q, probe_p = "What is BM25?", "BM25 is a lexical ranking function."
    ce_stable = ce.score_pairs(probe_q, [probe_p], batch_size=16)[0] == ce.score_pairs(
        probe_q, [probe_p], batch_size=16
    )[0]
    if ce.pad != "batch" or ce.bucket_by_length is not True or ce.fast is not False or ce.threads != 4:
        raise SystemExit(f"STOP: D1 CE constructor drifted pad={ce.pad} bucket={ce.bucket_by_length} fast={ce.fast} threads={ce.threads}")
    if ce.artifact_sha256 != CE_SHA256:
        raise SystemExit("STOP: CE onnx sha mismatch")

    gold_cover: dict[str, list[list[str]]] = {}
    for case in cases:
        gold_cover[case.case_id] = [covering_chunk_ids(ref) for ref in case.expected_evidence]

    chunks_by_id = load_control_chunks()
    if len(chunks_by_id) != 14209:
        raise SystemExit(f"STOP: control chunk cache {len(chunks_by_id)} != 14209")

    raw_by_id = {r["case_id"]: r for r in raw}
    cases_map: dict[str, dict] = {}
    per_case: list[dict] = []
    lat_total: list[float] = []
    lat_a: list[float] = []
    lat_local: list[float] = []
    lat_proj: list[float] = []
    lat_ce: list[float] = []
    lat_blend: list[float] = []
    integrity_failures: list[str] = []
    pools_fh = pools_path.open("w", encoding="utf-8")

    print("EVAL-NATQ-VAL-001 retrieving SYSTEM-H once over 40 validation questions...", flush=True)

    for case in cases:
        q = case.question
        t_case = time.perf_counter()
        t0 = time.perf_counter()
        a_pool = retrieve_system_a_pool(q, transformer)
        lat_a.append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
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
        lat_local.append((time.perf_counter() - t0) * 1000)

        a_by_id = {h.chunk_id: h for h in a_pool}
        t0 = time.perf_counter()
        e_ce = ce.score_pairs(q, [h.text for h in fused_e], batch_size=16)
        ce_by_id = {h.chunk_id: float(s) for h, s in zip(fused_e, e_ce, strict=True)}
        lat_ce_e = (time.perf_counter() - t0) * 1000

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

        t0 = time.perf_counter()
        fused_p = projection_rrf(q, TRANSFORMER_MODEL, transformer)
        mapped = map_to_canonical_extras(fused_p, c_e_ids, P)
        c_p_ids = mapped["C_P"]
        lat_proj.append((time.perf_counter() - t0) * 1000)

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

        t0 = time.perf_counter()
        if extra_rows:
            extra_ce = ce.score_pairs(q, [r["text"] for r in extra_rows], batch_size=16)
            for rec, s in zip(extra_rows, extra_ce, strict=True):
                ce_by_id[rec["chunk_id"]] = float(s)
        lat_ce.append(lat_ce_e + (time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        x_rows = apply_blend_exp017(e_rows, extra_rows, ce_by_id)
        x_ids = {r["chunk_id"] for r in x_rows}
        if not c_e_ids.issubset(x_ids):
            raise SystemExit(f"STOP: anti-drop E-L10 failed on {case.case_id}")
        y_rows = apply_blend_exp019a(x_rows)
        lat_blend.append((time.perf_counter() - t0) * 1000)

        union_hits: list[SearchHit] = list(fused_e) + extra_hits
        x_pool_rows = []
        for i, h in enumerate(fused_e, start=1):
            x_pool_rows.append(hit_as_row(h, pool_rank=i, a_rank=int(h.rank), a_score=float(h.score)))
        for i, h in enumerate(extra_hits, start=len(fused_e) + 1):
            x_pool_rows.append(hit_as_row(h, pool_rank=i, a_rank=10**9, a_score=0.0))

        scored = score_system(case, y_rows, "exp019a_rank", union_hits, gold_cover)
        for i, ref in enumerate(case.expected_evidence):
            scored["spans"][i]["pool_rank"] = first_span_rank(x_pool_rows, ref, "pool_rank")
            scored["spans"][i]["in_pool"] = span_in_hits(union_hits, ref)
            gold_cids = gold_cover[case.case_id][i]
            origin = None
            in_e = None
            for cid in gold_cids:
                hit_row = next((r for r in y_rows if r["chunk_id"] == cid), None)
                if hit_row is not None:
                    origin = hit_row.get("origin")
                    in_e = bool(hit_row.get("in_e_l10"))
                    break
            scored["spans"][i]["gold_origin"] = origin
            scored["spans"][i]["gold_in_e_l10"] = in_e

        failure = None
        if not scored["fully_recalled"]:
            failure = classify_failure(case, scored, a_pool, parents, gold_cover)

        total_ms = (time.perf_counter() - t_case) * 1000
        lat_total.append(total_ms)
        meta = raw_by_id[case.case_id]
        rec = {
            "case_id": case.case_id,
            "provider": meta.get("provider"),
            "coverage_tags": list(meta.get("coverage_tags") or []),
            "stress_types": list(meta.get("stress_types") or []),
            "n_gold_spans": len(case.expected_evidence),
            "requires_all_evidence": bool(meta.get("requires_all_evidence")),
            "fully_recalled": scored["fully_recalled"],
            "recall": scored["recall"],
            "doc_recall": scored["doc_recall"],
            "all_gold_spans_in_pool": all(s["in_pool"] for s in scored["spans"]),
            "e_pool_size": len(fused_e),
            "union_pool_size": len(y_rows),
            "n_projection_additions": len(c_p_ids),
            "parents": parents,
            "spans": scored["spans"],
            "failure": failure,
            "latency_ms": {
                "total": round(total_ms, 1),
                "system_a": round(lat_a[-1], 1),
                "e_l10": round(lat_local[-1], 1),
                "projection": round(lat_proj[-1], 1),
                "ce": round(lat_ce[-1], 1),
                "blend": round(lat_blend[-1], 1),
            },
        }
        per_case.append(rec)
        cases_map[case.case_id] = scored
        dump = {
            "case_id": case.case_id,
            "C_P": c_p_ids,
            "e_pool_size": len(fused_e),
            "union_pool_size": len(y_rows),
            "fully_recalled": scored["fully_recalled"],
            "spans": scored["spans"],
            "top10": [
                {
                    "rank": r["exp019a_rank"],
                    "chunk_id": r["chunk_id"],
                    "version_id": r["version_id"],
                    "origin": r.get("origin"),
                    "blend_score": r.get("blend_score"),
                }
                for r in y_rows
                if r["exp019a_rank"] <= TOP_K
            ],
        }
        pools_fh.write(json.dumps(dump, default=str) + "\n")
        pools_fh.flush()
        print(
            f"{case.case_id} full={int(scored['fully_recalled'])} "
            f"spans={sum(1 for s in scored['spans'] if s['within_10'])}/{len(scored['spans'])} "
            f"pool={int(all(s['in_pool'] for s in scored['spans']))} "
            f"doc={scored['doc_recall']:.2f} "
            f"ms={total_ms:.0f} CE={lat_ce[-1]:.0f}",
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
    if _sha(G_FILE) != G_FILE_SHA or _sha(G_CE_D1) != G_CE_D1_SHA:
        integrity_failures.append("SYSTEM-G or SYSTEM-G-CE-D1 mutated")
    if _sha(VAL_JSONL) != VAL_SHA:
        integrity_failures.append("validation.jsonl mutated")

    s = summarise(cases_map, "SYSTEM-H-V2-DEV-CANDIDATE", H_CONFIG_HASH)
    n = 40
    strict_n = s["cases_fully_recalled"]
    all_spans = [sp for c in cases_map.values() for sp in c["spans"]]
    n_spans = len(all_spans)
    span_found = s["spans_found_at_10"]
    span_micro = (span_found / n_spans) if n_spans else 1.0
    cand_case_n = sum(1 for c in cases_map.values() if all(sp["in_pool"] for sp in c["spans"]))
    cand_span_n = sum(1 for sp in all_spans if sp["in_pool"])
    doc_case_n = sum(1 for c in cases_map.values() if c["doc_recall"] == 1.0)
    ci_lo, ci_hi = clopper_pearson(strict_n, n)

    failures = [r for r in per_case if not r["fully_recalled"]]
    taxonomy = Counter((r["failure"] or {}).get("primary") for r in failures)
    gold_amb = [flag for r in per_case if r.get("failure") for flag in (r["failure"] or {}).get("gold_ambiguity_flags") or []]

    gate = {
        "strict_ge_32_40": strict_n >= 32,
        "candidate_ge_36_40": cand_case_n >= 36,
        "span_ge_0_80": span_micro >= 0.80,
        "document_ge_38_40": doc_case_n >= 38,
        "no_benchmark_integrity_failure": len(integrity_failures) == 0,
        "natq_holdout_untouched": natq_after["log_bytes"] == 0 and natq_after["log_sha256"] == NATQ_LOG_SHA,
    }
    validation_supported = all(gate.values())

    openai_ids = subset_ids(raw, lambda r: r.get("provider") == "openai")
    anth_ids = subset_ids(raw, lambda r: r.get("provider") == "anthropic")
    exact_ids = subset_ids(
        raw,
        lambda r: "exact_identifier_lookup" in tags_of(r),
    )
    multi_ids = subset_ids(
        raw,
        lambda r: len(r.get("expected_evidence") or []) > 1 or "multi_span" in tags_of(r),
    )
    para_ids = subset_ids(
        raw,
        lambda r: "realistic_paraphrase" in tags_of(r),
    )
    tag_counter = Counter()
    for r in raw:
        for t in tags_of(r):
            tag_counter[t] += 1
    tag_breakdown = {}
    for tag, _cnt in tag_counter.most_common():
        ids = subset_ids(raw, lambda r, t=tag: t in tags_of(r))
        tag_breakdown[tag] = metrics_for_ids(ids, cases_map)

    payload = {
        "experiment_id": "EVAL-NATQ-VAL-001",
        "scored": True,
        "n_evals": 1,
        "second_run": False,
        "retuned": False,
        "holdout_run": False,
        "release_frozen": False,
        "SYSTEM_H_modified": False,
        "split": "natq-001/validation",
        "n": n,
        "n_gold_spans": n_spans,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timestamp_et": datetime.now(UTC).astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%dT%H:%M:%S%z"),
        "preregistration_json_sha256": PREREG_JSON_SHA,
        "SYSTEM_H_config_hash": H_CONFIG_HASH,
        "SYSTEM_H_config_hash_unchanged": _sha(H_FILE) == H_FILE_SHA and config_hash(json.loads(H_FILE.read_text())["config"]) == H_CONFIG_HASH,
        "SYSTEM_H_file_sha256": _sha(H_FILE),
        "hash_check": hash_check,
        "natq_holdout_access_log_before": natq_before,
        "natq_holdout_access_log_after": natq_after,
        "v1_holdout_access_log_before": {"log_bytes": v1_before["log_bytes"], "log_sha256": v1_before["log_sha256"]},
        "v1_holdout_access_log_after": {"log_bytes": v1_after["log_bytes"], "log_sha256": v1_after["log_sha256"]},
        "holdout_json_opened": False,
        "v1_holdout_json_opened": False,
        "embedding": emb,
        "environment": env_fingerprint(emb),
        "cross_encoder": {
            "name": CE_NAME,
            "revision": CE_REVISION,
            "artifact_sha256": CE_SHA256,
            "constructor": "CrossEncoderReranker(pad='batch', bucket_by_length=True)",
            "fast": False,
            "threads": 4,
            "pad": "batch",
            "bucket_by_length": True,
            "batch_size": 16,
            "pair_score_stable": ce_stable,
        },
        "PRIMARY": {
            "strict_recall_at_10": f"{strict_n}/{n}",
            "n": strict_n,
            "d": n,
            "percentage": round(100.0 * strict_n / n, 1),
            "binomial_ci_95_clopper_pearson": [ci_lo, ci_hi],
        },
        "SECONDARY": {
            "candidate_gold_span_recall_at_100": f"{cand_case_n}/{n}",
            "candidate_gold_span_n": cand_case_n,
            "candidate_gold_span_d": n,
            "candidate_span_flags": f"{cand_span_n}/{n_spans}",
            "evidence_span_recall_at_10": round(span_micro, 4),
            "evidence_span_found": f"{span_found}/{n_spans}",
            "macro_span_recall": s["macro_span_recall"],
            "document_recall_at_10": f"{doc_case_n}/{n}",
            "document_recall_n": doc_case_n,
            "document_recall_mean": s["document_recall"],
            "mrr": s["mrr"],
            "latency_ms": {
                "total_mean": _mean(lat_total),
                "total_median": _median(lat_total),
                "system_a_mean": _mean(lat_a),
                "e_l10_mean": _mean(lat_local),
                "projection_mean": _mean(lat_proj),
                "ce_mean": _mean(lat_ce),
                "ce_median": _median(lat_ce),
                "blend_mean": _mean(lat_blend, 4),
            },
            "provider": {
                "openai": metrics_for_ids(openai_ids, cases_map),
                "anthropic": metrics_for_ids(anth_ids, cases_map),
            },
            "exact_identifier_cases": metrics_for_ids(exact_ids, cases_map),
            "multi_span_cases": metrics_for_ids(multi_ids, cases_map),
            "natural_paraphrase_cases": metrics_for_ids(para_ids, cases_map),
            "coverage_stress_tag_breakdown": tag_breakdown,
        },
        "gate": gate,
        "VALIDATION_SUPPORTED": validation_supported,
        "integrity_failures": integrity_failures,
        "failure_taxonomy_counts": dict(taxonomy),
        "failures": failures,
        "gold_ambiguity_flags": gold_amb,
        "per_case": per_case,
        "elapsed_s": round(time.time() - started, 1),
        "BLEND_CE": BLEND_CE,
        "BLEND_A": BLEND_A,
        "L": L,
        "P": P,
        "PARENT_N": PARENT_N,
        "W": W,
        "projection_set_id": PROJECTION_SET_ID,
        "STOP": "Do not run holdout. No second validation run. No retune. No release freeze.",
    }
    results_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    decision = "VALIDATION_SUPPORTED" if validation_supported else "VALIDATION_NOT_SUPPORTED"
    lines = [
        "# EVAL-NATQ-VAL-001 — SYSTEM-H NATURAL-QUERY VALIDATION",
        "",
        f"## {decision}",
        "",
        f"Frozen SYSTEM-H-V2-DEV-CANDIDATE scored **exactly once** on NATQ-001 validation n=40. "
        f"Preregistration sha256 `{PREREG_JSON_SHA}` hashed before any retrieval. "
        f"Holdout was not opened. SYSTEM-H / SYSTEM-G / SYSTEM-G-CE-D1 were not modified. No retune. No second run. No release freeze.",
        "",
        "## Setup",
        "",
        f"- Split: `evals/splits/natq-001/validation.jsonl` n=40, sha256 `{VAL_SHA}`.",
        f"- SYSTEM-H config_hash `{H_CONFIG_HASH}` (file sha256 `{H_FILE_SHA}`), unchanged after run: **{payload['SYSTEM_H_config_hash_unchanged']}**.",
        f"- Snapshot `{SNAPSHOT}`. Projection `{PROJECTION_SET_ID}` n=18057.",
        f"- CE: `{CE_NAME}` D1 `pad='batch', bucket_by_length=True`, batch_size=16, threads=4, onnx sha `{CE_SHA256}`.",
        f"- Blend 0.7 CE / 0.3 retrieval (EXP-019A projection-aware prior). L=10, P=20.",
        f"- NATQ holdout-access log after: {natq_after['log_bytes']} bytes, sha256 `{natq_after['log_sha256']}`.",
        f"- V1 holdout-access log after: {v1_after['log_bytes']} bytes, sha256 `{v1_after['log_sha256']}`.",
        f"- holdout_json_opened: **false**. v1_holdout_json_opened: **false**.",
        "",
        "## PRIMARY — strict full-case Recall@10",
        "",
        f"| metric | value |",
        f"| --- | ---: |",
        f"| strict Recall@10 | **{strict_n}/40** ({payload['PRIMARY']['percentage']}%) |",
        f"| 95% Clopper-Pearson CI (diagnostic) | [{ci_lo}, {ci_hi}] |",
        "",
        "## SECONDARY",
        "",
        f"| metric | value |",
        f"| --- | ---: |",
        f"| candidate gold-span Recall@100 | **{cand_case_n}/40** |",
        f"| candidate gold spans in union (span-level) | {cand_span_n}/{n_spans} |",
        f"| evidence-span Recall@10 (micro) | **{span_micro:.4f}** ({span_found}/{n_spans}) |",
        f"| evidence-span Recall@10 (macro) | {s['macro_span_recall']} |",
        f"| document Recall@10 | **{doc_case_n}/40** |",
        f"| document recall mean | {s['document_recall']} |",
        f"| MRR | {s['mrr']} |",
        f"| latency mean / median (ms) | {_mean(lat_total)} / {_median(lat_total)} |",
        f"| SYSTEM-A mean (ms) | {_mean(lat_a)} |",
        f"| E-L10 mean (ms) | {_mean(lat_local)} |",
        f"| projection mean (ms) | {_mean(lat_proj)} |",
        f"| CE mean / median (ms) | {_mean(lat_ce)} / {_median(lat_ce)} |",
        f"| blend mean (ms) | {_mean(lat_blend, 4)} |",
        "",
        "### Provider",
        "",
        f"| provider | n | strict | cand R@100 | span R@10 | doc R@10 | MRR |",
        f"| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, ids in (("openai", openai_ids), ("anthropic", anth_ids)):
        m = metrics_for_ids(ids, cases_map)
        lines.append(
            f"| {name} | {m['n_cases']} | {m['strict']} | {m['candidate_gold_span_recall_at_100']} | "
            f"{m['evidence_span_found']} ({m['evidence_span_recall_at_10_micro']}) | {m['document_recall_at_10']} | {m['mrr']} |"
        )
    lines += [
        "",
        "### Exact-identifier / multi-span / natural paraphrase",
        "",
        f"| subset | n | strict | cand R@100 | span R@10 | doc R@10 |",
        f"| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, ids in (
        ("exact_identifier_lookup", exact_ids),
        ("multi_span", multi_ids),
        ("realistic_paraphrase", para_ids),
    ):
        m = metrics_for_ids(ids, cases_map)
        lines.append(
            f"| {label} | {m['n_cases']} | {m['strict']} | {m['candidate_gold_span_recall_at_100']} | "
            f"{m['evidence_span_found']} ({m['evidence_span_recall_at_10_micro']}) | {m['document_recall_at_10']} |"
        )
    lines += ["", "### Coverage / stress-tag breakdown", "", "| tag | n | strict | cand R@100 | span R@10 |", "| --- | ---: | ---: | ---: | ---: |"]
    for tag, m in tag_breakdown.items():
        lines.append(
            f"| `{tag}` | {m['n_cases']} | {m['strict']} | {m['candidate_gold_span_recall_at_100']} | {m['evidence_span_found']} |"
        )
    lines += [
        "",
        "## Failure taxonomy (strict misses; no retune)",
        "",
        f"| class | n |",
        f"| --- | ---: |",
    ]
    for klass in list(CLASS_PRIORITY) + [None]:
        if taxonomy.get(klass):
            lines.append(f"| {klass} | {taxonomy[klass]} |")
    if not failures:
        lines.append("| (none) | 0 |")
    lines += ["", "### Strict failures"]
    if not failures:
        lines.append("")
        lines.append("None.")
    else:
        lines += ["", "| case | provider | primary | span classes | ranks | in_pool | tags |", "| --- | --- | --- | --- | --- | --- | --- |"]
        for r in failures:
            f = r["failure"] or {}
            ranks = [s.get("rank") for s in r["spans"]]
            pools = [s.get("in_pool") for s in r["spans"]]
            tags = ",".join(r.get("coverage_tags") or [])
            lines.append(
                f"| `{r['case_id']}` | {r.get('provider')} | {f.get('primary')} | "
                f"{f.get('span_classes')} | {ranks} | {pools} | {tags} |"
            )
    if gold_amb:
        lines += ["", "### Gold-ambiguity flags (do not alter gold)", ""]
        for flag in gold_amb:
            lines.append(f"- `{flag}`")
    else:
        lines += ["", "### Gold-ambiguity flags", "", "None flagged. Gold was not altered.", ""]
    lines += [
        "",
        "## Gate",
        "",
        f"| condition | result |",
        f"| --- | --- |",
        f"| strict ≥ 32/40 ({strict_n}/40) | {gate['strict_ge_32_40']} |",
        f"| candidate gold-span R@100 ≥ 36/40 ({cand_case_n}/40) | {gate['candidate_ge_36_40']} |",
        f"| evidence-span R@10 ≥ 0.80 ({span_micro:.4f} = {span_found}/{n_spans}) | {gate['span_ge_0_80']} |",
        f"| document R@10 ≥ 38/40 ({doc_case_n}/40) | {gate['document_ge_38_40']} |",
        f"| no benchmark-integrity failure | {gate['no_benchmark_integrity_failure']} |",
        f"| NATQ holdout untouched | {gate['natq_holdout_untouched']} |",
        "",
        f"**VALIDATION_SUPPORTED = {str(validation_supported).upper()}**",
        "",
        "## STOP",
        "",
        "Stop after EVAL-NATQ-VAL-001. Do **not** run holdout. No second validation run. No retune. No release freeze.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(decision, f"{strict_n}/40", "cand", f"{cand_case_n}/40", "span", f"{span_found}/{n_spans}", "doc", f"{doc_case_n}/40", flush=True)
    print("wrote", results_path, report_path, flush=True)
    return 0 if not integrity_failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
