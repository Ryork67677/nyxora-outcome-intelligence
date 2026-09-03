#!/usr/bin/env python3
"""EXP-021B: section-stratified two-pass compression of SYSTEM-J W20 extras.

Preregistration MUST already be hashed. Candidate-generation / compression only.
Does not run CE, blend, coverage selector, MMR, or final top-10.
Does not open NATQ or V1 holdout.json. Does not overwrite SYSTEM-H/I/J/G/E.
Does not increase W/L/P. Does not include EXP-020A parent-balanced projection.
Does not change EXTRA_BUDGET after seeing results. One variant. One run.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import statistics
import sys
import time
from collections import Counter, defaultdict
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
from rag_v1.ids import config_hash  # noqa: E402
from rag_v1.systems import FROZEN_HASHES  # noqa: E402
from rag_v1.types import EvidenceRef, EvalCase, SearchHit  # noqa: E402

from local_bm25_batched import local_bm25_per_parent_batched  # noqa: E402
from projection_retrieval import PROJECTION_SET_ID  # noqa: E402
from run_exp017 import L, P, load_control_chunks  # noqa: E402
from run_exp018_development import env_fingerprint, span_in_hits  # noqa: E402
from system_e import (  # noqa: E402
    A_HASH,
    CHUNK_SET,
    HOLD_LOG_SHA_AT_PREREG,
    PARENT_N,
    SNAPSHOT,
    W,
    covering_chunk_ids,
    embedding_status,
    holdout_log_state,
)

OUT_DIR = ROOT / "experiments" / "RAG-V2" / "EXP-021B"
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
J_FILE = (
    ROOT
    / "experiments"
    / "RAG-V2"
    / "SYSTEM-J-LOCAL-W20-UNION"
    / "SYSTEM-J-LOCAL-W20-UNION.json"
)
K_FILE = (
    ROOT
    / "experiments"
    / "RAG-V2"
    / "SYSTEM-K-W20-SECTION-COMPRESS"
    / "SYSTEM-K-W20-SECTION-COMPRESS.json"
)
G_FILE = ROOT / "experiments" / "EXP-019A" / "SYSTEM-G-PROJECTION-PRIOR.json"
G_CE_D1 = ROOT / "experiments" / "PERF-003" / "SYSTEM-G-CE-D1.json"
E_L10_FILE = ROOT / "experiments" / "EXP-018B" / "SYSTEM-E-L10-WITHIN-DOC.json"
PREREG_JSON = OUT_DIR / "EXP-021B-preregistration.json"
PREREG_MD = OUT_DIR / "EXP-021B-preregistration.md"
STORED_POOLS = ROOT / "experiments" / "RAG-V2" / "EXP-021A" / "logs" / "EXP-021A-pools.jsonl"
EXP021A_REPORT = ROOT / "experiments" / "RAG-V2" / "EXP-021A" / "EXP-021A-REPORT.json"
NATQ_HOLD_LOG = ROOT / "evals" / "splits" / "natq-001" / "holdout-access.log.jsonl"
NATQ_HOLD_LOCK = ROOT / "evals" / "splits" / "natq-001" / "holdout.lock.json"
V1_HOLD_LOG = ROOT / "evals" / "splits" / "gold150-v1" / "holdout-access.log.jsonl"

PREREG_JSON_SHA = "f5cfb249f76e9fbb68230ae034bb9ccdab173354482caf71c8b3cc0d1893fb3e"
H_CONFIG_HASH = "7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a"
H_FILE_SHA = "7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475"
I_CONFIG_HASH = "9103a51eaaebcbc581df452279ea06c880abb7524053606428dfd77649d4b3d6"
I_FILE_SHA = "63a78f1d88876c3f55033dc13ce3e6bad1fe768ce5252d315f31652769a9fd19"
J_CONFIG_HASH = "b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787"
J_FILE_SHA = "70acac77f33dbe1f7fc0f2e9b81f8a995c7fd0e9f47bab662f03f12cdecc0fdd"
K_CONFIG_HASH = "eef589c085ea7e88fdc729d83021b311e2927310fc6368b54a87f374859bdec8"
K_FILE_SHA = "20d967e2f56fed88f617d1c18474abc86b9f984f32a30cc195f42d6fef03ad7e"
VAL_SHA = "a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6"
NATQ_LOG_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
V1_LOG_SHA = "45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3"
NATQ_LOCK_SHA = "03e0d5749e61e73e6b9582109a74a4a9672610b7bf794daf25f46999e5ad40b2"
G_FILE_SHA = "7f4ff6db09f32e55cac820cbc00d87ce2ae91886d444c3bad20ac3e04c7f0f61"
G_CE_D1_SHA = "cf0c985c5f7738e7fc5422039fd6940621d8dcd8f91de41abe3784ac53a6a7ec"
E_L10_SHA = "efbd3bc1cc73d3c342a607ef75135515d13680b31fd6058e8f1c13e80d13ed89"
PROJ_CFG_HASH = "7fd5034c9510a1e08ec76bd22b020703c586dd12e7c02659397df05c5c365a8e"
J_CG_MEAN_MS = 1301.0
EXTRA_BUDGET = 30
NAMED_J_RECOVERIES = (
    ("NATQ-C-004", 0),
    ("NATQ-C-005", 1),
    ("NATQ-C-044", 0),
    ("NATQ-C-044", 1),
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mean(xs: list[float], ndigits: int = 4) -> float:
    return round(statistics.mean(xs), ndigits) if xs else 0.0


def _median(xs: list[float], ndigits: int = 4) -> float:
    return round(statistics.median(xs), ndigits) if xs else 0.0


def _p95(xs: list[float], ndigits: int = 2) -> float:
    if not xs:
        return 0.0
    s = sorted(float(x) for x in xs)
    if len(s) == 1:
        return round(s[0], ndigits)
    k = (len(s) - 1) * 0.95
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return round(s[int(k)], ndigits)
    return round(s[f] * (c - k) + s[c] * (k - f), ndigits)


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


def canonical_section_key(section_path) -> str:
    sp = section_path if isinstance(section_path, list) else list(section_path)
    return json.dumps(sp, ensure_ascii=True, separators=(",", ":"))


def within_group_key(e: dict) -> tuple:
    return (-float(e["local_bm25_score"]), int(e["local_bm25_rank"]), e["chunk_id"])


def global_key(e: dict) -> tuple:
    return (
        -float(e["local_bm25_score"]),
        int(e["parent_rank"]),
        int(e["local_bm25_rank"]),
        e["version_id"],
        e["section_key"],
        e["chunk_id"],
    )


def compress_extras(extras: list[dict]) -> list[dict]:
    """Two-pass section-stratified compression. EXTRA_BUDGET=30. Max 2 per group."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for e in extras:
        groups[(e["version_id"], e["section_key"])].append(e)
    for items in groups.values():
        items.sort(key=within_group_key)

    pass1: list[dict] = []
    pass2: list[dict] = []
    for items in groups.values():
        if items:
            rec = dict(items[0])
            rec["pass"] = 1
            pass1.append(rec)
        if len(items) >= 2:
            rec = dict(items[1])
            rec["pass"] = 2
            pass2.append(rec)

    pass1.sort(key=global_key)
    pass2.sort(key=global_key)

    selected: list[dict] = []
    seen: set[str] = set()
    for rec in pass1:
        if len(selected) >= EXTRA_BUDGET:
            break
        if rec["chunk_id"] in seen:
            continue
        selected.append(rec)
        seen.add(rec["chunk_id"])
    if len(selected) < EXTRA_BUDGET:
        for rec in pass2:
            if len(selected) >= EXTRA_BUDGET:
                break
            if rec["chunk_id"] in seen:
                continue
            selected.append(rec)
            seen.add(rec["chunk_id"])

    if len(selected) > EXTRA_BUDGET:
        raise SystemExit("STOP: selected extras exceeded EXTRA_BUDGET")
    group_counts: Counter[tuple[str, str]] = Counter()
    for rec in selected:
        g = (rec["version_id"], rec["section_key"])
        group_counts[g] += 1
        if group_counts[g] > 2:
            raise SystemExit("STOP: third candidate taken from same (version_id, section_path)")
        if rec["pass"] not in (1, 2):
            raise SystemExit("STOP: selected extra missing pass")
    return selected


def main() -> int:
    started = time.time()
    results_path = OUT_DIR / "EXP-021B-REPORT.json"
    report_path = OUT_DIR / "EXP-021B-REPORT.md"
    pools_path = OUT_DIR / "logs" / "EXP-021B-pools.jsonl"
    if results_path.exists() or report_path.exists():
        raise SystemExit("STOP: EXP-021B results already exist; refusing second run")
    if not PREREG_JSON.exists() or not PREREG_MD.exists():
        raise SystemExit("STOP: preregistration missing; do not score")
    got_pre = _sha(PREREG_JSON)
    if got_pre != PREREG_JSON_SHA:
        raise SystemExit(f"STOP: prereg json sha {got_pre} != frozen {PREREG_JSON_SHA}")
    sha_sidecar = (OUT_DIR / "EXP-021B-preregistration.json.sha256").read_text(encoding="utf-8").strip()
    if sha_sidecar != PREREG_JSON_SHA:
        raise SystemExit("STOP: prereg sha256 sidecar drifted")

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
    j_sha = _sha(J_FILE)
    if j_sha != J_FILE_SHA:
        raise SystemExit(f"STOP: SYSTEM-J file sha {j_sha} != frozen {J_FILE_SHA}")
    j_obj = json.loads(J_FILE.read_text(encoding="utf-8"))
    if j_obj.get("config_hash") != J_CONFIG_HASH:
        raise SystemExit("STOP: SYSTEM-J config_hash mismatch")
    if config_hash(j_obj["config"]) != J_CONFIG_HASH:
        raise SystemExit("STOP: recomputed SYSTEM-J config_hash drifted")
    k_sha = _sha(K_FILE)
    if k_sha != K_FILE_SHA:
        raise SystemExit(f"STOP: SYSTEM-K file sha {k_sha} != frozen {K_FILE_SHA}")
    k_obj = json.loads(K_FILE.read_text(encoding="utf-8"))
    if k_obj.get("config_hash") != K_CONFIG_HASH:
        raise SystemExit("STOP: SYSTEM-K config_hash mismatch")
    if config_hash(k_obj["config"]) != K_CONFIG_HASH:
        raise SystemExit("STOP: recomputed SYSTEM-K config_hash drifted")
    if k_obj["config"].get("extra_budget") != EXTRA_BUDGET:
        raise SystemExit("STOP: EXTRA_BUDGET drifted")
    if _sha(G_FILE) != G_FILE_SHA:
        raise SystemExit("STOP: SYSTEM-G file mutated")
    if _sha(G_CE_D1) != G_CE_D1_SHA:
        raise SystemExit("STOP: SYSTEM-G-CE-D1 file mutated")
    if _sha(E_L10_FILE) != E_L10_SHA:
        raise SystemExit("STOP: SYSTEM-E-L10 file mutated")
    if FROZEN_HASHES["SYSTEM-A-GLOBAL"] != A_HASH:
        raise SystemExit("STOP: SYSTEM-A hash mismatch")
    if W != 20 or L != 10 or P != 20 or PARENT_N != 10:
        raise SystemExit(f"STOP: frozen knobs drifted W={W} L={L} P={P} PARENT_N={PARENT_N}")

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

    stored_pools: dict[str, dict] = {}
    for line in STORED_POOLS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            stored_pools[rec["case_id"]] = rec
    if set(stored_pools) != set(got_ids):
        raise SystemExit("STOP: stored EXP-021A pools missing cases")

    exp021a = json.loads(EXP021A_REPORT.read_text(encoding="utf-8"))
    j_lat_by_id = {}
    for r in exp021a["per_case"]:
        lm = r["latency_ms"]
        j_lat_by_id[r["case_id"]] = (
            lm["system_a"] + lm["e_l10"] + lm["projection"] + lm["w20_union"]
        )

    chunks_by_id = load_control_chunks()
    if len(chunks_by_id) != 14209:
        raise SystemExit(f"STOP: control chunk cache {len(chunks_by_id)} != 14209")

    gold_cover: dict[str, list[list[str]]] = {}
    for case in cases:
        gold_cover[case.case_id] = [covering_chunk_ids(ref) for ref in case.expected_evidence]

    raw_by_id = {r["case_id"]: r for r in raw}
    per_case: list[dict] = []
    lat_compress: list[float] = []
    lat_bm25: list[float] = []
    integrity_failures: list[str] = []
    h_superset_ok_all = True
    pools_path.parent.mkdir(parents=True, exist_ok=True)
    pools_fh = pools_path.open("w", encoding="utf-8")

    print("EXP-021B candidate compression only over 40 NATQ validation questions...", flush=True)

    for case in cases:
        stored = stored_pools[case.case_id]
        h_union_ids = list(stored["system_h_union_ids"])
        j_union_ids = list(stored["system_j_union_ids"])
        added_w20 = list(stored["added_w20"])
        parents = list(stored["parents"])
        w20_by_parent = stored["w20_by_parent"]
        h_set = set(h_union_ids)
        j_set = set(j_union_ids)
        if set(added_w20) != (j_set - h_set):
            raise SystemExit(f"STOP: added_w20 != J-H on {case.case_id}")
        if j_union_ids != h_union_ids + added_w20:
            raise SystemExit(f"STOP: J != H + added_w20 order on {case.case_id}")
        if not h_set.issubset(j_set):
            raise SystemExit(f"STOP: H not subset of J on {case.case_id}")

        t0 = time.perf_counter()
        local = local_bm25_per_parent_batched(case.question, parents, W)
        for vid in parents:
            hits = local.get(vid) or []
            got_ids_w20 = [h.chunk_id for h in hits]
            stored_ids = list(w20_by_parent[vid])
            if got_ids_w20 != stored_ids:
                raise SystemExit(
                    f"STOP: recomputed W20 != stored w20_by_parent on {case.case_id} parent {vid}"
                )
        bm25_ms = (time.perf_counter() - t0) * 1000
        lat_bm25.append(bm25_ms)

        first_parent: dict[str, dict] = {}
        for parent_rank, vid in enumerate(parents, start=1):
            hits = local.get(vid) or []
            for h in hits:
                if h.chunk_id not in first_parent:
                    first_parent[h.chunk_id] = {
                        "version_id": vid,
                        "parent_rank": parent_rank,
                        "local_bm25_score": float(h.score),
                        "local_bm25_rank": int(h.rank),
                    }

        extras_meta: list[dict] = []
        for cid in added_w20:
            if cid not in first_parent:
                raise SystemExit(f"STOP: extra {cid} not in any parent W20 on {case.case_id}")
            info = first_parent[cid]
            rec = chunks_by_id[cid]
            if rec["version_id"] != info["version_id"]:
                raise SystemExit(
                    f"STOP: chunk.version_id {rec['version_id']} != associated parent "
                    f"{info['version_id']} on {case.case_id} extra {cid}"
                )
            sk = canonical_section_key(rec["section_path"])
            extras_meta.append(
                {
                    "chunk_id": cid,
                    "version_id": info["version_id"],
                    "parent_rank": info["parent_rank"],
                    "section_path": list(rec["section_path"]),
                    "section_key": sk,
                    "local_bm25_score": info["local_bm25_score"],
                    "local_bm25_rank": info["local_bm25_rank"],
                    "group": [info["version_id"], sk],
                }
            )

        t0 = time.perf_counter()
        selected = compress_extras(extras_meta)
        compress_ms = (time.perf_counter() - t0) * 1000
        lat_compress.append(compress_ms)

        selected_ids = [e["chunk_id"] for e in selected]
        if len(selected_ids) != len(set(selected_ids)):
            raise SystemExit(f"STOP: selected extras have duplicates on {case.case_id}")
        if len(selected_ids) > EXTRA_BUDGET:
            raise SystemExit(f"STOP: selected extras > EXTRA_BUDGET on {case.case_id}")
        if any(cid in h_set for cid in selected_ids):
            raise SystemExit(f"STOP: selected extra already in H on {case.case_id}")

        k_union_ids = list(h_union_ids)
        seen_k = set(h_union_ids)
        for cid in selected_ids:
            if cid not in seen_k:
                k_union_ids.append(cid)
                seen_k.add(cid)
        if not set(h_union_ids).issubset(set(k_union_ids)):
            h_superset_ok_all = False
            raise SystemExit(f"STOP: SYSTEM-H not subset of SYSTEM-K on {case.case_id}")
        if len(k_union_ids) != len(set(k_union_ids)):
            raise SystemExit(f"STOP: SYSTEM-K union has duplicates on {case.case_id}")
        if not set(k_union_ids).issubset(j_set):
            raise SystemExit(f"STOP: SYSTEM-K not subset of SYSTEM-J on {case.case_id}")

        extra_by_id = {e["chunk_id"]: e for e in extras_meta}
        selected_pass = {e["chunk_id"]: e["pass"] for e in selected}
        k_pos = {cid: i + 1 for i, cid in enumerate(k_union_ids)}
        extras_out = []
        for e in extras_meta:
            cid = e["chunk_id"]
            p = selected_pass.get(cid)
            extras_out.append(
                {
                    **e,
                    "pass": p,
                    "selected": cid in selected_pass,
                    "compressed_position": k_pos.get(cid) if cid in selected_pass else None,
                }
            )

        h_hits = hits_from_ids(h_union_ids, chunks_by_id)
        j_hits = hits_from_ids(j_union_ids, chunks_by_id)
        k_hits = hits_from_ids(k_union_ids, chunks_by_id)
        stored_spans = stored["spans"]

        span_rows = []
        for i, ref in enumerate(case.expected_evidence):
            cover = gold_cover[case.case_id][i]
            in_h = span_in_hits(h_hits, ref)
            in_j = span_in_hits(j_hits, ref)
            in_k = span_in_hits(k_hits, ref)
            stored_in_h = bool(stored_spans[i]["in_system_h_pool"])
            stored_in_j = bool(stored_spans[i]["in_system_j_pool"])
            if stored_in_h != in_h:
                raise SystemExit(
                    f"STOP: recomputed SYSTEM-H in_pool != stored on {case.case_id} span {i}"
                )
            if stored_in_j != in_j:
                raise SystemExit(
                    f"STOP: recomputed SYSTEM-J in_pool != stored on {case.case_id} span {i}"
                )
            covering_in_k = [c for c in cover if c in k_pos]
            pool_pos = min((k_pos[c] for c in covering_in_k), default=None)
            extra_info = None
            for c in cover:
                if c in extra_by_id:
                    extra_info = extra_by_id[c]
                    break
            span_rows.append(
                {
                    "span_index": i,
                    "covering_chunk_ids": cover,
                    "gold_version_id": ref.version_id,
                    "in_system_h_pool": bool(in_h),
                    "in_system_j_pool": bool(in_j),
                    "in_system_k_pool": bool(in_k),
                    "lost_vs_j": bool(in_j) and not bool(in_k),
                    "retained_vs_j": bool(in_j) and bool(in_k),
                    "new_vs_j": bool(in_k) and not bool(in_j),
                    "compressed_candidate_position": pool_pos,
                    "extra_meta": (
                        {
                            "chunk_id": extra_info["chunk_id"],
                            "version_id": extra_info["version_id"],
                            "parent_rank": extra_info["parent_rank"],
                            "section_path": extra_info["section_path"],
                            "section_key": extra_info["section_key"],
                            "local_bm25_score": extra_info["local_bm25_score"],
                            "local_bm25_rank": extra_info["local_bm25_rank"],
                            "pass": selected_pass.get(extra_info["chunk_id"]),
                            "compressed_position": k_pos.get(extra_info["chunk_id"])
                            if extra_info["chunk_id"] in selected_pass
                            else None,
                        }
                        if extra_info
                        else None
                    ),
                    "gold_in_parents": ref.version_id in set(parents),
                }
            )

        meta = raw_by_id[case.case_id]
        inherited_j_cg = float(j_lat_by_id[case.case_id])
        rec = {
            "case_id": case.case_id,
            "provider": meta.get("provider"),
            "coverage_tags": list(meta.get("coverage_tags") or []),
            "stress_types": list(meta.get("stress_types") or []),
            "n_gold_spans": len(case.expected_evidence),
            "parents": parents,
            "n_parents": len(parents),
            "system_h_pool_size": len(h_union_ids),
            "system_j_pool_size": len(j_union_ids),
            "system_k_pool_size": len(k_union_ids),
            "n_j_extras": len(added_w20),
            "n_k_additions": len(selected_ids),
            "n_groups": len({(e["version_id"], e["section_key"]) for e in extras_meta}),
            "n_pass1_selected": sum(1 for e in selected if e["pass"] == 1),
            "n_pass2_selected": sum(1 for e in selected if e["pass"] == 2),
            "exact_h_subset": True,
            "all_gold_in_h_pool": all(s["in_system_h_pool"] for s in span_rows),
            "all_gold_in_j_pool": all(s["in_system_j_pool"] for s in span_rows),
            "all_gold_in_k_pool": all(s["in_system_k_pool"] for s in span_rows),
            "system_h_subset": True,
            "spans": span_rows,
            "selected_extras": selected_ids,
            "latency_ms": {
                "compression_selection": round(compress_ms, 3),
                "w20_score_association_recompute": round(bm25_ms, 1),
                "inherited_system_j_candidate_generation": round(inherited_j_cg, 1),
                "system_k_candidate_generation": round(inherited_j_cg + compress_ms, 1),
            },
        }
        per_case.append(rec)
        dump = {
            "case_id": case.case_id,
            "parents": parents,
            "system_h_union_ids": h_union_ids,
            "system_j_union_ids": j_union_ids,
            "system_k_union_ids": k_union_ids,
            "added_w20": added_w20,
            "selected_extras": selected_ids,
            "extras": extras_out,
            "spans": span_rows,
        }
        pools_fh.write(json.dumps(dump, default=str) + "\n")
        pools_fh.flush()
        print(
            f"{case.case_id} H={int(rec['all_gold_in_h_pool'])} J={int(rec['all_gold_in_j_pool'])} "
            f"K={int(rec['all_gold_in_k_pool'])} pool {len(h_union_ids)}/{len(j_union_ids)}/{len(k_union_ids)} "
            f"added={len(selected_ids)} compress_ms={compress_ms:.2f}",
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
    if config_hash(json.loads(I_FILE.read_text(encoding="utf-8"))["config"]) != I_CONFIG_HASH:
        integrity_failures.append("SYSTEM-I config_hash changed")
    if _sha(J_FILE) != J_FILE_SHA:
        integrity_failures.append("SYSTEM-J file mutated")
    if config_hash(json.loads(J_FILE.read_text(encoding="utf-8"))["config"]) != J_CONFIG_HASH:
        integrity_failures.append("SYSTEM-J config_hash changed")
    if _sha(K_FILE) != K_FILE_SHA:
        integrity_failures.append("SYSTEM-K file mutated")
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
    case_j = sum(1 for r in per_case if r["all_gold_in_j_pool"])
    case_k = sum(1 for r in per_case if r["all_gold_in_k_pool"])
    span_h = sum(1 for r in per_case for s in r["spans"] if s["in_system_h_pool"])
    span_j = sum(1 for r in per_case for s in r["spans"] if s["in_system_j_pool"])
    span_k = sum(1 for r in per_case for s in r["spans"] if s["in_system_k_pool"])
    h_sizes = [r["system_h_pool_size"] for r in per_case]
    j_sizes = [r["system_j_pool_size"] for r in per_case]
    k_sizes = [r["system_k_pool_size"] for r in per_case]
    added_sizes = [r["n_k_additions"] for r in per_case]
    mean_h = _mean(h_sizes, 2)
    mean_j = _mean(j_sizes, 2)
    mean_k = _mean(k_sizes, 2)
    compression_ratio = round(mean_k / mean_j, 6) if mean_j else None
    compression_saved = round(1.0 - (mean_k / mean_j), 6) if mean_j else None

    def provider_metrics(provider: str) -> dict:
        sub = [r for r in per_case if r["provider"] == provider]
        ns = sum(len(r["spans"]) for r in sub)
        return {
            "n_cases": len(sub),
            "candidate_case_K": f"{sum(1 for r in sub if r['all_gold_in_k_pool'])}/{len(sub)}",
            "candidate_span_K": f"{sum(1 for r in sub for s in r['spans'] if s['in_system_k_pool'])}/{ns}",
            "candidate_case_J": f"{sum(1 for r in sub if r['all_gold_in_j_pool'])}/{len(sub)}",
            "candidate_span_J": f"{sum(1 for r in sub for s in r['spans'] if s['in_system_j_pool'])}/{ns}",
            "baseline_case_H": f"{sum(1 for r in sub if r['all_gold_in_h_pool'])}/{len(sub)}",
            "baseline_span_H": f"{sum(1 for r in sub for s in r['spans'] if s['in_system_h_pool'])}/{ns}",
        }

    multi = [
        r
        for r in per_case
        if r["n_gold_spans"] > 1 or "multi_span" in (r["coverage_tags"] + r["stress_types"])
    ]
    multi_h = sum(1 for r in multi if r["all_gold_in_h_pool"])
    multi_j = sum(1 for r in multi if r["all_gold_in_j_pool"])
    multi_k = sum(1 for r in multi if r["all_gold_in_k_pool"])

    every_h_present = h_superset_ok_all and all(r["system_h_subset"] for r in per_case)
    no_integrity = len(integrity_failures) == 0
    gate = {
        "candidate_full_case_ge_36_40": case_k >= 36,
        "candidate_span_ge_49_53": span_k >= 49,
        "mean_candidate_pool_le_150": mean_k <= 150,
        "every_original_SYSTEM_H_candidate_remains_present": every_h_present,
        "no_integrity_provenance_failure": no_integrity,
    }
    supported = all(gate.values())

    # Diagnostics ONLY AFTER aggregate metrics are calculated.
    lost_vs_j = [
        {"case_id": r["case_id"], **s}
        for r in per_case
        for s in r["spans"]
        if s["lost_vs_j"]
    ]
    new_vs_j = [
        {"case_id": r["case_id"], **s}
        for r in per_case
        for s in r["spans"]
        if s["new_vs_j"]
    ]
    named_diag = []
    by_id = {r["case_id"]: r for r in per_case}
    for cid, sidx in NAMED_J_RECOVERIES:
        rec = by_id[cid]
        span = rec["spans"][sidx]
        em = span.get("extra_meta")
        named_diag.append(
            {
                "case_id": cid,
                "span_index": sidx,
                "retained_by_SYSTEM_K": bool(span["in_system_k_pool"]),
                "in_system_j_pool": bool(span["in_system_j_pool"]),
                "group_section_path": em["section_path"] if em else None,
                "group_version_id": em["version_id"] if em else None,
                "local_bm25_rank": em["local_bm25_rank"] if em else None,
                "local_bm25_score": em["local_bm25_score"] if em else None,
                "compression_pass": em["pass"] if em else None,
                "compressed_candidate_position": (
                    em["compressed_position"] if em else span["compressed_candidate_position"]
                ),
                "covering_chunk_ids": span["covering_chunk_ids"],
            }
        )

    k_cg = [r["latency_ms"]["system_k_candidate_generation"] for r in per_case]
    estimated_ce_pairs = int(sum(k_sizes))
    estimated_ce_pairs_j = int(sum(j_sizes))
    estimated_ce_pairs_h = int(sum(h_sizes))

    payload = {
        "experiment_id": "EXP-021B",
        "scored": True,
        "n_evals": 1,
        "second_run": False,
        "retuned": False,
        "holdout_run": False,
        "release_frozen": False,
        "SYSTEM_H_modified": False,
        "SYSTEM_I_modified": False,
        "SYSTEM_J_modified": False,
        "CE_run": False,
        "final_ranking_run": False,
        "EXTRA_BUDGET": EXTRA_BUDGET,
        "EXTRA_BUDGET_changed_after_results": False,
        "split": "natq-001/validation",
        "split_role": "DEVELOPMENT / MODEL-SELECTION DATA; not independent validation",
        "n": n,
        "n_gold_spans": n_spans,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timestamp_et": datetime.now(UTC).astimezone(ZoneInfo("America/New_York")).strftime(
            "%Y-%m-%dT%H:%M:%S%z"
        ),
        "preregistration_json_sha256": PREREG_JSON_SHA,
        "SYSTEM_K_config_hash": K_CONFIG_HASH,
        "SYSTEM_K_file_sha256": k_sha,
        "SYSTEM_J_config_hash": J_CONFIG_HASH,
        "SYSTEM_J_file_sha256": j_sha,
        "SYSTEM_H_config_hash": H_CONFIG_HASH,
        "SYSTEM_H_config_hash_unchanged": _sha(H_FILE) == H_FILE_SHA,
        "SYSTEM_H_file_sha256": _sha(H_FILE),
        "SYSTEM_I_config_hash": I_CONFIG_HASH,
        "SYSTEM_I_config_hash_unchanged": _sha(I_FILE) == I_FILE_SHA,
        "SYSTEM_J_config_hash_unchanged": _sha(J_FILE) == J_FILE_SHA,
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
        "environment_drift_note": "PostgreSQL 16.15 / pgvector 0.8.6 vs historical 16.13 / 0.6.0",
        "baseline": {
            "SYSTEM_H": {
                "candidate_full_case_Recall_at_pool": "34/40",
                "candidate_span_micro": "46/53",
                "mean_pool": 118.83,
                "recomputed_match": {
                    "case": f"{case_h}/40",
                    "span": f"{span_h}/{n_spans}",
                    "mean_pool": mean_h,
                    "matches_stored": case_h == 34 and span_h == 46 and n_spans == 53 and mean_h == 118.83,
                },
            },
            "SYSTEM_J": {
                "candidate_full_case_Recall_at_pool": "37/40",
                "candidate_span_micro": "50/53",
                "mean_pool": 187.12,
                "recomputed_match": {
                    "case": f"{case_j}/40",
                    "span": f"{span_j}/{n_spans}",
                    "mean_pool": mean_j,
                    "matches_stored": case_j == 37 and span_j == 50 and n_spans == 53 and mean_j == 187.12,
                },
            },
        },
        "PRIMARY": {
            "candidate_full_case_Recall_at_pool": f"{case_k}/{n}",
            "n": case_k,
            "d": n,
            "baseline_H": "34/40",
            "baseline_J": "37/40",
            "delta_cases_vs_H": case_k - 34,
            "delta_cases_vs_J": case_k - 37,
        },
        "SECONDARY": {
            "candidate_span_micro": f"{span_k}/{n_spans}",
            "baseline_span_H": "46/53",
            "baseline_span_J": "50/53",
            "delta_spans_vs_H": span_k - 46,
            "delta_spans_vs_J": span_k - 50,
            "pool_size_H_mean": mean_h,
            "pool_size_H_median": _median(h_sizes, 2),
            "pool_size_H_p95": _p95(h_sizes, 2),
            "pool_size_J_mean": mean_j,
            "pool_size_J_median": _median(j_sizes, 2),
            "pool_size_J_p95": _p95(j_sizes, 2),
            "pool_size_K_mean": mean_k,
            "pool_size_K_median": _median(k_sizes, 2),
            "pool_size_K_p95": _p95(k_sizes, 2),
            "mean_added": _mean(added_sizes, 3),
            "median_added": _median(added_sizes, 3),
            "p95_added": _p95(added_sizes, 2),
            "compression_ratio_vs_J_mean_K_over_mean_J": compression_ratio,
            "compression_saved_1_minus_ratio": compression_saved,
            "exact_superset_check": {
                "every_query_SYSTEM_K_contains_every_SYSTEM_H_candidate": every_h_present,
                "n_queries_checked": n,
            },
            "pool_growth": {
                "baseline_SYSTEM_H_mean_pool": mean_h,
                "SYSTEM_J_mean_pool": mean_j,
                "SYSTEM_K_mean_pool": mean_k,
                "estimated_CE_pairs_SYSTEM_K": estimated_ce_pairs,
                "estimated_CE_pairs_SYSTEM_J": estimated_ce_pairs_j,
                "estimated_CE_pairs_SYSTEM_H": estimated_ce_pairs_h,
                "CE_was_not_run": True,
            },
            "per_provider": {
                "openai": provider_metrics("openai"),
                "anthropic": provider_metrics("anthropic"),
            },
            "multi_span_candidate_ceiling": {
                "n": len(multi),
                "SYSTEM_H": f"{multi_h}/{len(multi)}",
                "SYSTEM_J": f"{multi_j}/{len(multi)}",
                "SYSTEM_K": f"{multi_k}/{len(multi)}",
            },
            "latency_ms": {
                "compression_selection_mean": _mean(lat_compress, 3),
                "compression_selection_median": _median(lat_compress, 3),
                "inherited_SYSTEM_J_candidate_generation_mean": J_CG_MEAN_MS,
                "SYSTEM_K_candidate_generation_mean": _mean(k_cg, 1),
                "SYSTEM_K_candidate_generation_median": _median(k_cg, 1),
                "w20_score_association_recompute_mean": _mean(lat_bm25, 1),
                "w20_score_association_recompute_median": _median(lat_bm25, 1),
                "note": "SYSTEM-K candidate-gen = inherited J cg + compression; A/projection were not re-run for K",
            },
        },
        "diagnostics_four_SYSTEM_J_recovered_spans": named_diag,
        "diagnostics_newly_lost_vs_SYSTEM_J": lost_vs_j,
        "diagnostics_newly_retained_vs_SYSTEM_J": new_vs_j,
        "gate": gate,
        "EXP-021B_SUPPORTED": supported,
        "integrity_failures": integrity_failures,
        "per_case": per_case,
        "elapsed_s": round(time.time() - started, 2),
        "L": L,
        "P": P,
        "PARENT_N": PARENT_N,
        "W": W,
        "STOP": "Do not run CE. Do not run final ranking. Do not try another budget. Do not alter EXTRA_BUDGET=30.",
    }

    results_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n")

    def pass_cell(item: dict) -> str:
        p = item.get("compression_pass")
        if p is None:
            return "none"
        return str(p)

    lines = [
        "# EXP-021B — SECTION-STRATIFIED LOCAL-W20 COMPRESSION",
        "",
        f"**EXP-021B_SUPPORTED = {str(supported).upper()}**",
        "",
        "Candidate-generation / compression only on NATQ-001 validation n=40, DEVELOPMENT / MODEL-SELECTION DATA. "
        "Not independent validation. Holdout was not opened. SYSTEM-H / SYSTEM-I / SYSTEM-J / G / E were not modified. "
        "CE and final ranking were not run. W/L/P were not increased. EXTRA_BUDGET=30 was not changed after results. "
        "EXP-020A parent-balanced projection was not included.",
        "",
        "## Setup",
        "",
        f"- Preregistration sha256 `{PREREG_JSON_SHA}` hashed before computing SYSTEM-K aggregate candidate metrics.",
        f"- SYSTEM-K-W20-SECTION-COMPRESS config_hash `{K_CONFIG_HASH}` (file sha256 `{k_sha}`).",
        f"- Parent SYSTEM-H config_hash `{H_CONFIG_HASH}` unchanged after run: **{payload['SYSTEM_H_config_hash_unchanged']}**.",
        f"- Parent SYSTEM-J config_hash `{J_CONFIG_HASH}` unchanged after run: **{payload['SYSTEM_J_config_hash_unchanged']}**.",
        f"- SYSTEM-I config_hash `{I_CONFIG_HASH}` unchanged after run: **{payload['SYSTEM_I_config_hash_unchanged']}**.",
        f"- Split: `evals/splits/natq-001/validation.jsonl` n=40, sha256 `{VAL_SHA}`.",
        f"- Snapshot `{SNAPSHOT}`. Projection `{PROJECTION_SET_ID}` n=18057.",
        "- Used stored EXP-021A H/J ids. BM25 W=20 recomputed only to attach scores and verify identity with stored w20_by_parent.",
        "- Two-pass section-stratified compression, EXTRA_BUDGET=30, max 2 extras per (version_id, section_path), never drop H.",
        f"- NATQ holdout-access log after: {natq_after['log_bytes']} bytes, sha256 `{natq_after['log_sha256']}`.",
        f"- V1 holdout-access log after: {v1_after['log_bytes']} bytes, sha256 `{v1_after['log_sha256']}`.",
        "- holdout_json_opened: **false**. v1_holdout_json_opened: **false**.",
        f"- Environment drift: {payload['environment_drift_note']}.",
        "",
        "## PRIMARY — candidate full-case Recall@pool",
        "",
        "| metric | SYSTEM-H | SYSTEM-J | SYSTEM-K |",
        "| --- | ---: | ---: | ---: |",
        f"| candidate full-case Recall@pool | 34/40 | 37/40 | **{case_k}/40** |",
        "",
        "## SECONDARY",
        "",
        "| metric | SYSTEM-H | SYSTEM-J | SYSTEM-K |",
        "| --- | ---: | ---: | ---: |",
        f"| candidate span micro | 46/53 | 50/53 | **{span_k}/53** |",
        f"| mean pool size | {mean_h} | {mean_j} | {mean_k} |",
        f"| median pool size | {_median(h_sizes, 2)} | {_median(j_sizes, 2)} | {_median(k_sizes, 2)} |",
        f"| p95 pool size | {_p95(h_sizes, 2)} | {_p95(j_sizes, 2)} | {_p95(k_sizes, 2)} |",
        f"| mean / median additions | — | 68.3 / 66.0 | {_mean(added_sizes, 3)} / {_median(added_sizes, 3)} |",
        f"| compression ratio mean_K/mean_J | — | — | {compression_ratio} |",
        f"| compression saved 1 - ratio | — | — | {compression_saved} |",
        f"| exact superset vs SYSTEM-H | — | True | {every_h_present} |",
        f"| candidate-gen latency mean ms | — | {J_CG_MEAN_MS} | {_mean(k_cg, 1)} (J cg + compression) |",
        f"| compression selection mean / median ms | — | — | {_mean(lat_compress, 3)} / {_median(lat_compress, 3)} |",
        f"| W20 score-association recompute mean ms | — | — | {_mean(lat_bm25, 1)} |",
        "",
        "### Pool / CE-pair estimate",
        "",
        "| | |",
        "| --- | ---: |",
        f"| baseline SYSTEM-H mean pool | {mean_h} |",
        f"| SYSTEM-J mean pool | {mean_j} |",
        f"| SYSTEM-K mean pool | {mean_k} |",
        f"| estimated CE pairs SYSTEM-K | {estimated_ce_pairs} |",
        f"| estimated CE pairs SYSTEM-J | {estimated_ce_pairs_j} |",
        f"| estimated CE pairs SYSTEM-H | {estimated_ce_pairs_h} |",
        "",
        "CE was **not** run. The CE-pair estimate is `sum(pool_size)` over 40 queries.",
        "",
        "### Per-provider candidate recall",
        "",
        "| provider | H case | J case | K case | H span | J span | K span |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| openai | {provider_metrics('openai')['baseline_case_H']} | {provider_metrics('openai')['candidate_case_J']} | {provider_metrics('openai')['candidate_case_K']} | {provider_metrics('openai')['baseline_span_H']} | {provider_metrics('openai')['candidate_span_J']} | {provider_metrics('openai')['candidate_span_K']} |",
        f"| anthropic | {provider_metrics('anthropic')['baseline_case_H']} | {provider_metrics('anthropic')['candidate_case_J']} | {provider_metrics('anthropic')['candidate_case_K']} | {provider_metrics('anthropic')['baseline_span_H']} | {provider_metrics('anthropic')['candidate_span_J']} | {provider_metrics('anthropic')['candidate_span_K']} |",
        "",
        "### Multi-span candidate ceiling",
        "",
        f"Subset n={len(multi)} (n_gold_spans>1 or tag multi_span). SYSTEM-H **{multi_h}/{len(multi)}**. SYSTEM-J **{multi_j}/{len(multi)}**. SYSTEM-K **{multi_k}/{len(multi)}**.",
        "",
        "## Diagnostics — four SYSTEM-J recovered spans (after aggregates)",
        "",
        "Diagnostic only. No named-case handling. Identities are the four spans SYSTEM-J recovered over SYSTEM-H.",
        "",
        "| case | span | retained by K | group section_path | local-BM25 rank | pass | K position |",
        "| --- | ---: | --- | --- | ---: | --- | ---: |",
    ]
    for item in named_diag:
        lines.append(
            f"| `{item['case_id']}` | {item['span_index']} | {item['retained_by_SYSTEM_K']} | "
            f"`{item['group_section_path']}` | {item['local_bm25_rank']} | {pass_cell(item)} | "
            f"{item['compressed_candidate_position']} |"
        )
    lines += [
        "",
        f"Newly lost gold spans vs SYSTEM-J: **{len(lost_vs_j)}**. Newly retained gold spans vs SYSTEM-J: **{len(new_vs_j)}**.",
        "",
    ]
    if lost_vs_j:
        lines.append("Lost vs J:")
        for item in lost_vs_j:
            lines.append(
                f"- `{item['case_id']}` s{item['span_index']} covering={item['covering_chunk_ids']}"
            )
        lines.append("")
    if new_vs_j:
        lines.append("Newly retained vs J:")
        for item in new_vs_j:
            lines.append(f"- `{item['case_id']}` s{item['span_index']}")
        lines.append("")
    lines += [
        "## Gate",
        "",
        "| condition | result |",
        "| --- | --- |",
        f"| candidate full-case recall >= 36/40 ({case_k}/40) | {gate['candidate_full_case_ge_36_40']} |",
        f"| candidate span recall >= 49/53 ({span_k}/53) | {gate['candidate_span_ge_49_53']} |",
        f"| mean candidate pool <= 150 ({mean_k}) | {gate['mean_candidate_pool_le_150']} |",
        f"| every original SYSTEM-H candidate remains present | {gate['every_original_SYSTEM_H_candidate_remains_present']} |",
        f"| no integrity/provenance failure | {gate['no_integrity_provenance_failure']} |",
        "",
        f"**EXP-021B_SUPPORTED = {str(supported).upper()}**",
        "",
        "## Interpretation",
        "",
    ]
    if supported:
        lines += [
            "Section-stratified two-pass compression of SYSTEM-J W20-only extras preserved the preregistered "
            "candidate-recall floor while returning mean pool size to the SYSTEM-H engineering band (<=150).",
            "",
            "Do **not** conclude the compressed pool is release-ready. Do not run CE or final ranking in this experiment. "
            "Do not change EXTRA_BUDGET after these results.",
            "",
        ]
    else:
        lines += [
            "EXP-021B did not pass the preregistered gate. Do not change EXTRA_BUDGET after seeing results. "
            "Do not try another budget in this experiment. Return to coordinator ChatGPT.",
            "",
        ]
    lines += [
        "## STOP",
        "",
        "Stop after EXP-021B. Do **not** run CE. Do **not** run final ranking. Do **not** try another budget. "
        "Do **not** alter EXTRA_BUDGET=30. Do **not** open holdout. Return to coordinator ChatGPT.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"DONE case {case_k}/40 span {span_k}/{n_spans} mean_pool={mean_k} "
        f"SUPPORTED={supported} elapsed={payload['elapsed_s']}s",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
