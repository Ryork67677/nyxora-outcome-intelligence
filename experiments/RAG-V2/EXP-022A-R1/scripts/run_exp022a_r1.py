#!/usr/bin/env python3
"""EXP-022A-R1: controlled frozen-CE replay over stored SYSTEM-J memberships.

Preregistration MUST already be hashed. ONE CE call per query on exact J_IDS
texts in stored order. Persist every raw CE logit before aggregate metrics.
Does not modify EXP-022A, SYSTEM-H/J/K, W/L/P, or CE. Does not test K.
Does not open holdout.json. Development replay, not independent validation.
"""
from __future__ import annotations

import hashlib
import json
import os
import statistics
import struct
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
sys.path.insert(0, str(ROOT / "experiments" / "EXP-019B" / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "RAG-V2" / "EXP-021A" / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "PERF-003" / "scripts"))

from rag_v1.ids import config_hash  # noqa: E402

from cross_encoder import CE_NAME, CE_ONNX, CE_REVISION, CE_SHA256, CE_TOKENIZER  # noqa: E402
from run_exp017 import load_control_chunks, score_system  # noqa: E402
from run_exp018_development import env_fingerprint, first_span_rank, span_in_hits, summarise  # noqa: E402
from run_exp019b import mcnemar_exact  # noqa: E402
from run_exp021a import hits_from_ids, load_validation  # noqa: E402
from system_e import (  # noqa: E402
    HOLD_LOG_SHA_AT_PREREG,
    TOP_K,
    covering_chunk_ids,
    embedding_status,
    holdout_log_state,
)
from v2_system_g_ce import make_v2_system_g_d1_reranker  # noqa: E402

OUT_DIR = ROOT / "experiments" / "RAG-V2" / "EXP-022A-R1"
VAL_JSONL = ROOT / "evals" / "splits" / "natq-001" / "validation.jsonl"
H_FILE = ROOT / "experiments" / "RAG-V2" / "SYSTEM-H-V2-DEV-CANDIDATE" / "SYSTEM-H-V2-DEV-CANDIDATE.json"
I_FILE = (
    ROOT / "experiments" / "RAG-V2" / "SYSTEM-I-PARENT-BALANCED-CANDIDATES" / "SYSTEM-I-PARENT-BALANCED-CANDIDATES.json"
)
J_FILE = ROOT / "experiments" / "RAG-V2" / "SYSTEM-J-LOCAL-W20-UNION" / "SYSTEM-J-LOCAL-W20-UNION.json"
K_FILE = ROOT / "experiments" / "RAG-V2" / "SYSTEM-K-W20-SECTION-COMPRESS" / "SYSTEM-K-W20-SECTION-COMPRESS.json"
G_FILE = ROOT / "experiments" / "EXP-019A" / "SYSTEM-G-PROJECTION-PRIOR.json"
G_CE_D1 = ROOT / "experiments" / "PERF-003" / "SYSTEM-G-CE-D1.json"
E_L10_FILE = ROOT / "experiments" / "EXP-018B" / "SYSTEM-E-L10-WITHIN-DOC.json"
PREREG_JSON = OUT_DIR / "EXP-022A-R1-preregistration.json"
PREREG_MD = OUT_DIR / "EXP-022A-R1-preregistration.md"
STORED_POOLS = ROOT / "experiments" / "RAG-V2" / "EXP-021A" / "logs" / "EXP-021A-pools.jsonl"
EXP021A_REPORT = ROOT / "experiments" / "RAG-V2" / "EXP-021A" / "EXP-021A-REPORT.json"
EXP022A_DIR = ROOT / "experiments" / "RAG-V2" / "EXP-022A"
NATQ_HOLD_LOG = ROOT / "evals" / "splits" / "natq-001" / "holdout-access.log.jsonl"
NATQ_HOLD_LOCK = ROOT / "evals" / "splits" / "natq-001" / "holdout.lock.json"
V1_HOLD_LOG = ROOT / "evals" / "splits" / "gold150-v1" / "holdout-access.log.jsonl"
POST_DIR = Path("/workspace/NATQ-001-post")
LOGITS_PATH = OUT_DIR / "logs" / "EXP-022A-R1-raw-ce-logits.jsonl"
LOGITS_SHA_PATH = OUT_DIR / "logs" / "EXP-022A-R1-raw-ce-logits.jsonl.sha256"

PREREG_JSON_SHA = "29be7cfc9f22c2e182016baa81f1e8bca5a9dfeae6e5e518594cab24f4d6ff48"
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
FROZEN_CE_SHA = "5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a"
TOKENIZER_JSON_SHA = "d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66"
NAMED_J_RECOVERIES = (
    ("NATQ-C-004", 0),
    ("NATQ-C-005", 1),
    ("NATQ-C-044", 0),
    ("NATQ-C-044", 1),
)
EXP022A_FROZEN_SHAS = {
    "EXP-022A-REPORT.json": "7653a849e2aafae25840df72d9597654efcd4b7a387f87a1ee5103e4040be793",
    "EXP-022A-REPORT.md": "011f752b1bafeb911acd914aec80ff7dc6a961cab63b3d9d2b0c9b40f36cbfed",
    "EXP-022A-preregistration.json": "ad7fba5a38d6fda06fdb42a94f0b78fdce008cfe978b1743224028bb2fd8e64b",
    "EXP-022A-preregistration.json.sha256": "c453f80e0e4d0a02e4dcaae59a113ac43719b0455534abfb2af5b0933bfaa3d2",
    "EXP-022A-preregistration.md": "acf68c6443e1a229812468a3795bbf3d9d69ef7f68253d9e23406a948baf62ea",
    "scripts/run_exp022a.py": "97e7155edde5fe3f24d50353abd0d6cc8f45e9ea74e239677fb898872b643e61",
    "logs/EXP-022A-h-logit-inventory.json": "53a6c8cb87bf82d6f80b2f3c0648064165ce7d5bbb76b0df1cbe1d2f6a0b3ba1",
}
EXPECTED_H = 4753
EXPECTED_J = 7485
EXPECTED_J_ONLY = 2732


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


def load_021a_pools() -> list[dict]:
    rows = []
    for line in STORED_POOLS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def input_hash(case_id: str, chunk_id: str, query: str, text: str) -> str:
    payload = json.dumps(
        {"case_id": case_id, "chunk_id": chunk_id, "query": query, "text": text},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def query_sha256(query: str) -> str:
    return hashlib.sha256(query.encode("utf-8")).hexdigest()


def logit_hex(value: float) -> tuple[str, str]:
    f = float(value)
    return f.hex(), struct.pack(">d", f).hex()


def ce_only_order(ids: list[str], logits: dict[str, float]) -> list[str]:
    return sorted(ids, key=lambda cid: (-float(logits[cid]), cid))


def rows_from_ranked(ids: list[str], logits: dict[str, float], chunks_by_id: dict) -> list[dict]:
    ranked = ce_only_order(ids, logits)
    rows = []
    for i, cid in enumerate(ranked, start=1):
        rec = chunks_by_id[cid]
        rows.append(
            {
                "chunk_id": cid,
                "version_id": rec["version_id"],
                "section_path": list(rec["section_path"]),
                "char_start": rec["char_start"],
                "char_end": rec["char_end"],
                "text": rec["text"],
                "ce_logit": float(logits[cid]),
                "ce_only_rank": i,
            }
        )
    return rows


def is_multi_span(n_gold_spans: int, coverage_tags: list, stress_types: list) -> bool:
    tags = list(coverage_tags or []) + list(stress_types or [])
    return n_gold_spans > 1 or "multi_span" in tags


def copy_to_post(paths: list[Path]) -> None:
    POST_DIR.mkdir(parents=True, exist_ok=True)
    for p in paths:
        if p.exists():
            dest = POST_DIR / p.name
            dest.write_bytes(p.read_bytes())


def exp022a_unchanged() -> dict:
    out = {}
    ok = True
    for rel, expected in EXP022A_FROZEN_SHAS.items():
        path = EXP022A_DIR / rel
        got = _sha(path) if path.exists() else None
        match = got == expected
        ok = ok and match
        out[rel] = {"expected": expected, "got": got, "unchanged": match}
    return {"all_unchanged": ok, "files": out}


def verify_membership(pools: list[dict]) -> dict:
    if len(pools) != 40:
        raise SystemExit(f"STOP: EXP-021A pools n={len(pools)} != 40")
    h_pairs: set[tuple[str, str]] = set()
    j_pairs: set[tuple[str, str]] = set()
    n_h = n_j = n_jo = 0
    for rec in pools:
        h_ids = list(rec["system_h_union_ids"])
        j_ids = list(rec["system_j_union_ids"])
        if len(h_ids) != len(set(h_ids)):
            raise SystemExit(f"STOP: duplicate SYSTEM-H ids on {rec['case_id']}")
        if len(j_ids) != len(set(j_ids)):
            raise SystemExit(f"STOP: duplicate SYSTEM-J ids on {rec['case_id']}")
        h_set = set(h_ids)
        j_set = set(j_ids)
        if not h_set <= j_set:
            missing = sorted(h_set - j_set)
            raise SystemExit(f"STOP: H_IDS not subset of J_IDS on {rec['case_id']}: {missing[:5]}")
        extras = [cid for cid in j_ids if cid not in h_set]
        stored_added = list(rec.get("added_w20") or [])
        if set(extras) != set(stored_added):
            raise SystemExit(f"STOP: J-only != added_w20 on {rec['case_id']}")
        for cid in h_ids:
            key = (rec["case_id"], cid)
            if key in h_pairs:
                raise SystemExit(f"STOP: duplicate (query,chunk) in H pool {key}")
            h_pairs.add(key)
        for cid in j_ids:
            key = (rec["case_id"], cid)
            if key in j_pairs:
                raise SystemExit(f"STOP: duplicate (query,chunk) in J pool {key}")
            j_pairs.add(key)
        n_h += len(h_ids)
        n_j += len(j_ids)
        n_jo += len(extras)
    if n_h != EXPECTED_H or n_j != EXPECTED_J or n_jo != EXPECTED_J_ONLY:
        raise SystemExit(
            f"STOP: membership count mismatch H={n_h} J={n_j} J-only={n_jo} "
            f"expected {EXPECTED_H}/{EXPECTED_J}/{EXPECTED_J_ONLY}"
        )
    return {
        "n_queries": 40,
        "n_H_pairs": n_h,
        "n_J_pairs": n_j,
        "n_J_only_pairs": n_jo,
        "h_pairs": h_pairs,
        "j_pairs": j_pairs,
        "H_subset_J_every_query": True,
    }


def persistence_gate(
    *,
    h_pairs: set[tuple[str, str]],
    j_pairs: set[tuple[str, str]],
) -> dict:
    rows = []
    seen: dict[tuple[str, str], float] = {}
    dup_disagree = []
    for line in LOGITS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        key = (rec["case_id"], rec["chunk_id"])
        logit = float.fromhex(rec["raw_ce_logit_hex"]) if rec.get("raw_ce_logit_hex") else float(rec["raw_ce_logit"])
        if key in seen and seen[key] != logit:
            dup_disagree.append({"key": key, "a": seen[key], "b": logit})
        seen.setdefault(key, logit)
        rows.append(rec)
    unique = set(seen)
    h_member = {k for k in unique if k in h_pairs}
    j_member = {k for k in unique if k in j_pairs}
    j_only = j_member - h_pairs
    missing_j = sorted(j_pairs - unique)
    missing_h = sorted(h_pairs - unique)
    extra = sorted(unique - j_pairs)
    arm_h = sum(1 for r in rows if r.get("candidate_arm") == "H")
    arm_jo = sum(1 for r in rows if r.get("candidate_arm") == "J_ONLY")
    ok = (
        len(unique) == EXPECTED_J
        and len(j_member) == EXPECTED_J
        and len(h_member) == EXPECTED_H
        and len(j_only) == EXPECTED_J_ONLY
        and len(missing_j) == 0
        and len(missing_h) == 0
        and len(extra) == 0
        and len(dup_disagree) == 0
        and arm_h == EXPECTED_H
        and arm_jo == EXPECTED_J_ONLY
        and len(rows) == EXPECTED_J
    )
    jsonl_sha = _sha(LOGITS_PATH)
    LOGITS_SHA_PATH.write_text(jsonl_sha + "\n", encoding="utf-8")
    return {
        "ok": ok,
        "n_jsonl_rows": len(rows),
        "n_unique_pairs": len(unique),
        "n_H_member": len(h_member),
        "n_J_member": len(j_member),
        "n_J_only": len(j_only),
        "n_missing_J": len(missing_j),
        "n_missing_H": len(missing_h),
        "n_extra_non_J": len(extra),
        "n_duplicate_disagreements": len(dup_disagree),
        "arm_H_rows": arm_h,
        "arm_J_ONLY_rows": arm_jo,
        "zero_missing": len(missing_j) == 0 and len(missing_h) == 0,
        "zero_duplicate_disagreements": len(dup_disagree) == 0,
        "every_H_has_one_logit": len(missing_h) == 0 and len(h_member) == EXPECTED_H,
        "every_J_has_one_logit": len(missing_j) == 0 and len(j_member) == EXPECTED_J,
        "missing_j_examples": [{"case_id": a, "chunk_id": b} for a, b in missing_j[:10]],
        "duplicate_disagree_examples": dup_disagree[:10],
        "jsonl_sha256": jsonl_sha,
        "logits": seen,
    }


def write_stop_persistence(
    *,
    gate: dict,
    natq_before: dict,
    natq_after: dict,
    v1_before: dict,
    v1_after: dict,
    hash_check: dict,
    env: dict,
    emb: dict,
    started: float,
    integrity_failures: list[str],
    exp022a_check: dict,
    ce_info: dict | None,
) -> None:
    utc = datetime.now(tz=UTC).replace(microsecond=0)
    et = utc.astimezone(ZoneInfo("America/New_York"))
    payload = {
        "experiment_id": "EXP-022A-R1",
        "scored": False,
        "EXP-022A-R1_STATUS": "STOPPED_PERSISTENCE_GATE",
        "EXP-022A-R1_CE_RECOGNIZABILITY_SUPPORTED": None,
        "mechanism_metrics_computed": False,
        "preregistration_json_sha256": PREREG_JSON_SHA,
        "timestamp": utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timestamp_et": et.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "hash_check": hash_check,
        "persistence_gate": {k: v for k, v in gate.items() if k != "logits"},
        "cross_encoder": ce_info,
        "embedding": emb,
        "environment": env,
        "environment_drift_note": "PostgreSQL 16.15 / pgvector 0.8.6 vs historical 16.13 / 0.6.0",
        "natq_holdout_access_log_before": natq_before,
        "natq_holdout_access_log_after": natq_after,
        "v1_holdout_access_log_before": {"log_bytes": v1_before["log_bytes"], "log_sha256": v1_before["log_sha256"]},
        "v1_holdout_access_log_after": {"log_bytes": v1_after["log_bytes"], "log_sha256": v1_after["log_sha256"]},
        "holdout_json_opened": False,
        "v1_holdout_json_opened": False,
        "EXP-022A_files_unchanged": exp022a_check,
        "integrity_failures": integrity_failures,
        "elapsed_s": round(time.time() - started, 2),
        "STOP": "Persistence gate failed. Mechanism metrics were not computed. Return to coordinator ChatGPT.",
    }
    results_path = OUT_DIR / "EXP-022A-R1-REPORT.json"
    report_path = OUT_DIR / "EXP-022A-R1-REPORT.md"
    results_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    g = gate
    lines = [
        "# EXP-022A-R1 — CONTROLLED CE REPLAY + SYSTEM-J RECOGNIZABILITY",
        "",
        "## STOPPED_PERSISTENCE_GATE",
        "",
        "NATQ-001 validation n=40 is DEVELOPMENT / MODEL-SELECTION DATA. Not independent validation.",
        "Holdout was not opened. SYSTEM-H / SYSTEM-J / SYSTEM-K were not modified. Mechanism metrics were **not** computed.",
        "",
        f"**scored = false**. **EXP-022A-R1_CE_RECOGNIZABILITY_SUPPORTED** was **not evaluated**.",
        "",
        "## Persistence gate",
        "",
        "| item | count |",
        "| --- | ---: |",
        f"| JSONL rows | {g['n_jsonl_rows']} |",
        f"| unique (case_id, chunk_id) | {g['n_unique_pairs']} |",
        f"| H-member | {g['n_H_member']} |",
        f"| J-member | {g['n_J_member']} |",
        f"| J-only | {g['n_J_only']} |",
        f"| missing J | {g['n_missing_J']} |",
        f"| missing H | {g['n_missing_H']} |",
        f"| extra non-J | {g['n_extra_non_J']} |",
        f"| duplicate disagreements | {g['n_duplicate_disagreements']} |",
        "",
        f"JSONL sha256 `{g['jsonl_sha256']}`.",
        "",
        "## STOP",
        "",
        "Stop after EXP-022A-R1 persistence-gate failure. Do **not** compute mechanism metrics.",
        "Do **not** build a coverage-aware selector. Do **not** test SYSTEM-K. Return to coordinator ChatGPT.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    reply = (
        f"EXP-022A-R1 stopped on the persistence gate before any mechanism metrics. "
        f"Prereg sha {PREREG_JSON_SHA}. Raw-logit jsonl sha {g['jsonl_sha256']}. "
        f"Stored logits: {g['n_jsonl_rows']} rows, unique {g['n_unique_pairs']} "
        f"(H-member {g['n_H_member']}, J-only {g['n_J_only']}); missing J {g['n_missing_J']}, "
        f"missing H {g['n_missing_H']}, duplicate disagreements {g['n_duplicate_disagreements']}. "
        f"CE fingerprint {FROZEN_CE_SHA}. H/J strict/span/MRR/doc were not computed. "
        f"Paired rescues/regressions, provider, multi-span, four-span ranks, redundancy, and latency "
        f"aggregates were not computed. EXP-022A-R1_CE_RECOGNIZABILITY_SUPPORTED unevaluated. "
        f"Environment drift PostgreSQL 16.15 / pgvector 0.8.6 vs 16.13 / 0.6.0. "
        f"NATQ holdout after {natq_after['log_bytes']} bytes sha {natq_after['log_sha256']}. "
        f"V1 holdout after {v1_after['log_bytes']} bytes sha {v1_after['log_sha256']}. "
        "Did not build a selector, test K, modify W/L/P, change CE, or open holdout. STOP."
    )
    POST_DIR.mkdir(parents=True, exist_ok=True)
    (POST_DIR / "exp-022a-r1-reply.txt").write_text(reply + "\n", encoding="utf-8")
    copy_to_post(
        [
            results_path,
            report_path,
            PREREG_JSON,
            PREREG_MD,
            OUT_DIR / "EXP-022A-R1-preregistration.json.sha256",
            LOGITS_PATH,
            LOGITS_SHA_PATH,
            OUT_DIR / "scripts" / "run_exp022a_r1.py",
        ]
    )


def write_scored_report(payload: dict) -> None:
    results_path = OUT_DIR / "EXP-022A-R1-REPORT.json"
    report_path = OUT_DIR / "EXP-022A-R1-REPORT.md"
    results_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    p = payload
    prim = p["PRIMARY"]
    sec = p["SECONDARY"]
    paired = p["PAIRED"]
    gate = p["gate"]
    supported = p["EXP-022A-R1_CE_RECOGNIZABILITY_SUPPORTED"]
    lat = p["LATENCY"]
    named = p["diagnostics_four_SYSTEM_J_recovered_spans"]
    multi = p["MULTI_SPAN_ANALYSIS"]
    lines = [
        "# EXP-022A-R1 — CONTROLLED CE REPLAY + SYSTEM-J RECOGNIZABILITY",
        "",
        f"**EXP-022A-R1_CE_RECOGNIZABILITY_SUPPORTED = {str(supported).upper()}**",
        "",
        "NATQ-001 validation n=40 is DEVELOPMENT / MODEL-SELECTION DATA. Not independent validation. "
        "This is a development replay / diagnostic, not EVAL-NATQ-VAL-002. Holdout was not opened. "
        "SYSTEM-H / SYSTEM-J / SYSTEM-K were not modified. Original EXP-022A remains CLOSED unscored "
        "as STOPPED_MISSING_STORED_H_CE_LOGITS and was not rewritten.",
        "",
        f"scored=true. One CE call per query on exact stored J_IDS. Stored logits={p['persistence_gate']['n_jsonl_rows']}.",
        "",
        "## Setup / lock",
        "",
        f"- Preregistration sha256 `{p['preregistration_json_sha256']}` hashed before any raw CE logits.",
        f"- Raw-logit JSONL sha256 `{p['raw_logit_jsonl_sha256']}`.",
        f"- SYSTEM-H config_hash `{H_CONFIG_HASH}` file sha `{H_FILE_SHA}` unchanged: **{p['SYSTEM_H_file_unchanged']}**.",
        f"- SYSTEM-J config_hash `{J_CONFIG_HASH}` file sha `{J_FILE_SHA}` unchanged: **{p['SYSTEM_J_file_unchanged']}**.",
        f"- SYSTEM-K config_hash `{K_CONFIG_HASH}` file sha `{K_FILE_SHA}` unchanged: **{p['SYSTEM_K_file_unchanged']}** (not tested).",
        f"- validation.jsonl sha256 `{VAL_SHA}`.",
        f"- Frozen CE ONNX sha `{FROZEN_CE_SHA}`. Module CE_SHA256 `{CE_SHA256}`. Live artifact `{p['cross_encoder']['artifact_sha256']}`. Fingerprint match: **{p['cross_encoder']['fingerprint_match']}**.",
        f"- Constructor `{p['cross_encoder']['constructor']}`; fast={p['cross_encoder']['fast']}; threads={p['cross_encoder']['threads']}; batch_size=16; max_length=512; D1 bucket_by_length.",
        f"- Membership: H={EXPECTED_H}, J={EXPECTED_J}, J-only={EXPECTED_J_ONLY}; H subset J every query: **True**.",
        f"- Persistence gate: unique {p['persistence_gate']['n_unique_pairs']}, H-member {p['persistence_gate']['n_H_member']}, J-only {p['persistence_gate']['n_J_only']}, missing 0, duplicate disagreements 0.",
        f"- NATQ holdout-access log after: {p['natq_holdout_access_log_after']['log_bytes']} bytes, sha256 `{p['natq_holdout_access_log_after']['log_sha256']}`.",
        f"- V1 holdout-access log after: {p['v1_holdout_access_log_after']['log_bytes']} bytes, sha256 `{p['v1_holdout_access_log_after']['log_sha256']}`.",
        "- holdout_json_opened: **false**. v1_holdout_json_opened: **false**.",
        f"- Environment drift: {p['environment_drift_note']}.",
        f"- EXP-022A files unchanged: **{p['EXP-022A_files_unchanged']['all_unchanged']}**.",
        "",
        "## PRIMARY — strict full-case Recall@10 (CE-only)",
        "",
        "| arm | strict R@10 |",
        "| --- | ---: |",
        f"| H CE-only | {prim['H_CE_only_strict_Recall@10']} |",
        f"| J CE-only | **{prim['J_CE_only_strict_Recall@10']}** |",
        f"| delta cases | {prim['delta_cases']} |",
        "",
        "## SECONDARY",
        "",
        "| metric | H CE-only | J CE-only |",
        "| --- | ---: | ---: |",
        f"| evidence-span R@10 | {sec['H_CE_only_span_Recall@10']} | {sec['J_CE_only_span_Recall@10']} |",
        f"| MRR (summarise: mean 1/rank all gold spans) | {sec['H_summarise_mrr']} | {sec['J_summarise_mrr']} |",
        f"| document R@10 (all gold docs in top-10) | {sec['H_document_Recall@10']} | {sec['J_document_Recall@10']} |",
        f"| document recall mean | {sec['H_document_recall_mean']} | {sec['J_document_recall_mean']} |",
        f"| multi-span strict | {sec['multi_span_H_strict']} | {sec['multi_span_J_strict']} |",
        f"| multi-span span | {sec['multi_span_H_span']} | {sec['multi_span_J_span']} |",
        "",
        "### Provider",
        "",
        "| provider | n | H strict | J strict | H span | J span |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        f"| openai | {sec['openai']['n_cases']} | {sec['openai']['H_strict']} | {sec['openai']['J_strict']} | {sec['openai']['H_span']} | {sec['openai']['J_span']} |",
        f"| anthropic | {sec['anthropic']['n_cases']} | {sec['anthropic']['H_strict']} | {sec['anthropic']['J_strict']} | {sec['anthropic']['H_span']} | {sec['anthropic']['J_span']} |",
        "",
        "## PAIRED MOVEMENT",
        "",
        f"- J rescues over H: {paired['n_rescues']} {paired['J_rescues_over_H']}",
        f"- J regressions vs H: {paired['n_regressions']} {paired['J_regressions_vs_H']}",
        f"- both pass: {paired['n_both_pass']}",
        f"- both fail: {paired['n_both_fail']}",
        f"- McNemar exact p (diagnostic): n01={paired['mcnemar_exact'].get('n01')} n10={paired['mcnemar_exact'].get('n10')} p={paired['mcnemar_exact'].get('p_exact')}. No significance claim.",
        "",
        "## Diagnostics — four SYSTEM-J recovered spans (after aggregates)",
        "",
        "| case | span | raw CE logit | J CE-only rank | top10 | n higher same version_id | n higher same section_path |",
        "| --- | ---: | ---: | ---: | --- | ---: | ---: |",
    ]
    for d in named:
        lines.append(
            f"| `{d.get('case_id')}` | {d.get('span_index')} | {d.get('raw_ce_logit')} | {d.get('ce_only_rank_in_J')} | {d.get('enters_top10')} | {d.get('n_higher_ranked_same_version_id')} | {d.get('n_higher_ranked_same_section_path')} |"
        )
    lines += [
        "",
        "## MULTI-SPAN",
        "",
        "| case | required | in J pool | in J top10 | unique version_ids top10 | unique section_paths top10 | redundancy version | redundancy section |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for d in multi:
        lines.append(
            f"| `{d['case_id']}` | {d['required_span_count']} | {d['spans_in_SYSTEM_J_pool']} | {d['spans_in_J_CE_only_top10']} | {d['unique_version_ids_in_J_CE_top10']} | {d['unique_section_paths_in_J_CE_top10']} | {d['redundant_top10_by_version_id']} | {d['redundant_top10_by_section_path']} |"
        )
    lines += [
        "",
        "In-pool gold span CE-only ranks:",
        "",
    ]
    for d in multi:
        ranks = ", ".join(
            f"s{s['span_index']}={'in_pool rank '+str(s['ce_only_rank']) if s['in_pool'] else 'not in pool'}"
            for s in d["in_pool_gold_span_ranks"]
        )
        lines.append(f"- `{d['case_id']}`: {ranks}")
    lines += [
        "",
        "## LATENCY",
        "",
        f"- total CE wall time: {lat['total_CE_wall_s']} s ({lat['total_CE_wall_ms']} ms)",
        f"- mean per-query CE time: {lat['mean_per_query_CE_ms']} ms",
        f"- median per-query CE time: {lat['median_per_query_CE_ms']} ms",
        f"- H-pair count: {lat['H_pair_count']}",
        f"- J-only pair count: {lat['J_only_pair_count']}",
        f"- full J-pair count: {lat['full_J_pair_count']}",
        "- No cross-host architecture claim.",
        "",
        "## HARNESS FIX (NON-SCORING follow-up)",
        "",
        "EVAL-NATQ-VAL-001 did not persist full-pool raw CE logits. Future development/validation reranker executions must persist candidate membership, raw reranker logits, query/candidate association, model fingerprint, and input/config fingerprint. Historical EVAL-NATQ-VAL-001 artifacts were not modified. Historical logits were not fabricated.",
        "",
        "## Gate",
        "",
        "| condition | result |",
        "| --- | --- |",
        f"| J strict R@10 improves over H by >= 2 cases ({prim['delta_cases']}) | {gate['J_strict_improves_ge_2_cases']} |",
        f"| J span R@10 improves over H by >= 2 spans ({sec['delta_spans']}) | {gate['J_span_improves_ge_2_spans']} |",
        f"| J strict regressions vs H <= 1 ({paired['n_regressions']}) | {gate['J_strict_regressions_le_1']} |",
        f"| no integrity/provenance failure | {gate['no_integrity_provenance_failure']} |",
        "",
        f"**EXP-022A-R1_CE_RECOGNIZABILITY_SUPPORTED = {str(supported).upper()}**",
        "",
        "## STOP",
        "",
        "Return to coordinator ChatGPT. Did not build a coverage-aware selector, test SYSTEM-K, modify W/L/P, change CE, or open holdout.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")


def write_reply(payload: dict) -> None:
    p = payload
    prim = p["PRIMARY"]
    sec = p["SECONDARY"]
    paired = p["PAIRED"]
    lat = p["LATENCY"]
    named = p["diagnostics_four_SYSTEM_J_recovered_spans"]
    named_txt = "; ".join(
        f"{d.get('case_id')} s{d.get('span_index')} logit={d.get('raw_ce_logit')} rank={d.get('ce_only_rank_in_J')} top10={d.get('enters_top10')} same_ver={d.get('n_higher_ranked_same_version_id')} same_sec={d.get('n_higher_ranked_same_section_path')}"
        for d in named
    )
    multi = p["MULTI_SPAN_ANALYSIS"]
    red_v = [d["redundant_top10_by_version_id"] for d in multi]
    red_s = [d["redundant_top10_by_section_path"] for d in multi]
    reply = (
        f"EXP-022A-R1 is a scored development replay, not independent validation. "
        f"Prereg sha {p['preregistration_json_sha256']}. "
        f"Raw-logit jsonl sha {p['raw_logit_jsonl_sha256']}. "
        f"Stored logits {p['persistence_gate']['n_jsonl_rows']} unique {p['persistence_gate']['n_unique_pairs']} "
        f"(H-member {p['persistence_gate']['n_H_member']}, J-only {p['persistence_gate']['n_J_only']}); "
        f"zero missing, zero duplicate disagreements, every H and every J candidate has one logit. "
        f"CE fingerprint onnx {p['cross_encoder']['artifact_sha256']} revision {p['cross_encoder']['revision']} "
        f"constructor {p['cross_encoder']['constructor']}. "
        f"H CE-only strict {prim['H_CE_only_strict_Recall@10']}, span {sec['H_CE_only_span_Recall@10']}, "
        f"MRR {sec['H_summarise_mrr']}, doc {sec['H_document_Recall@10']}. "
        f"J CE-only strict {prim['J_CE_only_strict_Recall@10']}, span {sec['J_CE_only_span_Recall@10']}, "
        f"MRR {sec['J_summarise_mrr']}, doc {sec['J_document_Recall@10']}. "
        f"Paired: rescues {paired['n_rescues']} {paired['J_rescues_over_H']}, "
        f"regressions {paired['n_regressions']} {paired['J_regressions_vs_H']}, "
        f"both pass {paired['n_both_pass']}, both fail {paired['n_both_fail']}; "
        f"McNemar n01={paired['mcnemar_exact'].get('n01')} n10={paired['mcnemar_exact'].get('n10')} p={paired['mcnemar_exact'].get('p_exact')} (diagnostic only). "
        f"OpenAI H/J strict {sec['openai']['H_strict']}/{sec['openai']['J_strict']} span {sec['openai']['H_span']}/{sec['openai']['J_span']}; "
        f"Anthropic H/J strict {sec['anthropic']['H_strict']}/{sec['anthropic']['J_strict']} span {sec['anthropic']['H_span']}/{sec['anthropic']['J_span']}. "
        f"Multi-span (n={sec['multi_span_n']}) strict H/J {sec['multi_span_H_strict']}/{sec['multi_span_J_strict']} "
        f"span {sec['multi_span_H_span']}/{sec['multi_span_J_span']}. "
        f"Four recovered spans: {named_txt}. "
        f"Redundancy (top10 minus unique version/section) per multi-span case version {red_v} section {red_s}. "
        f"CE latency total {lat['total_CE_wall_s']}s mean {lat['mean_per_query_CE_ms']}ms median {lat['median_per_query_CE_ms']}ms; "
        f"H-pairs {lat['H_pair_count']} J-only {lat['J_only_pair_count']} full J {lat['full_J_pair_count']}. "
        f"EXP-022A-R1_CE_RECOGNIZABILITY_SUPPORTED={p['EXP-022A-R1_CE_RECOGNIZABILITY_SUPPORTED']}. "
        f"Environment: {p['environment_drift_note']}. "
        f"NATQ holdout {p['natq_holdout_access_log_after']['log_bytes']} bytes sha {p['natq_holdout_access_log_after']['log_sha256']}. "
        f"V1 holdout {p['v1_holdout_access_log_after']['log_bytes']} bytes sha {p['v1_holdout_access_log_after']['log_sha256']}. "
        f"EXP-022A files unchanged={p['EXP-022A_files_unchanged']['all_unchanged']}. "
        "Did not build a selector, test K, modify W/L/P, change CE, or open holdout. STOP."
    )
    POST_DIR.mkdir(parents=True, exist_ok=True)
    (POST_DIR / "exp-022a-r1-reply.txt").write_text(reply + "\n", encoding="utf-8")


def main() -> int:
    started = time.time()
    results_path = OUT_DIR / "EXP-022A-R1-REPORT.json"
    report_path = OUT_DIR / "EXP-022A-R1-REPORT.md"
    if results_path.exists() or report_path.exists():
        raise SystemExit("STOP: EXP-022A-R1 results already exist; refusing second run")
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
    j_sha = _sha(J_FILE)
    if j_sha != J_FILE_SHA:
        raise SystemExit(f"STOP: SYSTEM-J file sha {j_sha} != frozen {J_FILE_SHA}")
    j_obj = json.loads(J_FILE.read_text(encoding="utf-8"))
    if j_obj.get("config_hash") != J_CONFIG_HASH:
        raise SystemExit("STOP: SYSTEM-J config_hash mismatch")
    k_sha = _sha(K_FILE)
    if k_sha != K_FILE_SHA:
        raise SystemExit(f"STOP: SYSTEM-K file sha {k_sha} != frozen {K_FILE_SHA}")
    k_obj = json.loads(K_FILE.read_text(encoding="utf-8"))
    if k_obj.get("config_hash") != K_CONFIG_HASH:
        raise SystemExit("STOP: SYSTEM-K config_hash mismatch")
    if _sha(I_FILE) != I_FILE_SHA:
        raise SystemExit("STOP: SYSTEM-I file mutated")
    if _sha(G_FILE) != G_FILE_SHA:
        raise SystemExit("STOP: SYSTEM-G file mutated")
    if _sha(G_CE_D1) != G_CE_D1_SHA:
        raise SystemExit("STOP: SYSTEM-G-CE-D1 file mutated")
    if E_L10_FILE.exists() and _sha(E_L10_FILE) != E_L10_SHA:
        raise SystemExit("STOP: SYSTEM-E-L10 file mutated")
    exp022a_check = exp022a_unchanged()
    if not exp022a_check["all_unchanged"]:
        raise SystemExit(f"STOP: EXP-022A files drifted before run: {exp022a_check}")

    onnx_sha = _sha(CE_ONNX)
    if onnx_sha != FROZEN_CE_SHA or CE_SHA256 != FROZEN_CE_SHA:
        raise SystemExit(f"STOP: CE ONNX sha {onnx_sha} / module {CE_SHA256} != frozen {FROZEN_CE_SHA}")
    tok_sha = _sha(Path(CE_TOKENIZER))
    if tok_sha != TOKENIZER_JSON_SHA:
        raise SystemExit(f"STOP: tokenizer.json sha {tok_sha} != {TOKENIZER_JSON_SHA}")

    pools = load_021a_pools()
    membership = verify_membership(pools)
    h_pairs = membership["h_pairs"]
    j_pairs = membership["j_pairs"]

    hash_check = {
        "prereg_json_sha256": got_pre,
        "prereg_json_sha256_ok": got_pre == PREREG_JSON_SHA,
        "validation_sha256": val_sha,
        "validation_sha256_ok": val_sha == VAL_SHA,
        "SYSTEM_H_config_hash": h_obj["config_hash"],
        "SYSTEM_H_config_hash_ok": h_obj["config_hash"] == H_CONFIG_HASH,
        "SYSTEM_H_file_sha256": h_sha,
        "SYSTEM_H_file_sha256_ok": h_sha == H_FILE_SHA,
        "SYSTEM_J_file_sha256": j_sha,
        "SYSTEM_J_file_sha256_ok": j_sha == J_FILE_SHA,
        "SYSTEM_K_file_sha256": k_sha,
        "SYSTEM_K_file_sha256_ok": k_sha == K_FILE_SHA,
        "n_H_candidates": membership["n_H_pairs"],
        "n_J_candidates": membership["n_J_pairs"],
        "n_J_only": membership["n_J_only_pairs"],
        "natq_holdout_access_log": natq_before,
        "v1_holdout_access_log": {"log_bytes": v1_before["log_bytes"], "log_sha256": v1_before["log_sha256"]},
        "ce_onnx_sha256": onnx_sha,
        "tokenizer_json_sha256": tok_sha,
    }

    raw, cases = load_validation()
    if len(raw) != 40 or len(cases) != 40:
        raise SystemExit(f"STOP: n must equal 40, got raw={len(raw)} cases={len(cases)}")
    chunks_by_id = load_control_chunks()
    gold_cover = {case.case_id: [covering_chunk_ids(ref) for ref in case.expected_evidence] for case in cases}
    pool_by_id = {r["case_id"]: r for r in pools}
    meta_by_id = {r["case_id"]: r for r in raw}

    ce = make_v2_system_g_d1_reranker()
    if getattr(ce, "artifact_sha256", None) != FROZEN_CE_SHA:
        raise SystemExit("STOP: live CE artifact sha mismatch")
    if ce.fast or ce.threads != 4 or ce.pad != "batch" or not ce.bucket_by_length:
        raise SystemExit(f"STOP: CE constructor drift fast={ce.fast} threads={ce.threads} pad={ce.pad} bucket={ce.bucket_by_length}")

    ce_info = {
        "name": CE_NAME,
        "revision": CE_REVISION,
        "artifact_sha256": ce.artifact_sha256,
        "module_CE_SHA256": CE_SHA256,
        "onnx_file_sha256": onnx_sha,
        "fingerprint_match": ce.artifact_sha256 == FROZEN_CE_SHA == onnx_sha == CE_SHA256,
        "constructor": "CrossEncoderReranker(pad='batch', bucket_by_length=True)",
        "fast": False,
        "threads": 4,
        "pad": "batch",
        "bucket_by_length": True,
        "batch_size": 16,
        "max_length": 512,
        "truncation": "longest_first",
        "tokenizer_path": str(CE_TOKENIZER),
        "tokenizer_json_sha256": tok_sha,
    }

    (OUT_DIR / "logs").mkdir(parents=True, exist_ok=True)
    if LOGITS_PATH.exists():
        raise SystemExit("STOP: raw-ce-logits jsonl already exists; refusing to append a second run")

    tokenizer_identity = {
        "path": str(CE_TOKENIZER),
        "tokenizer_json_sha256": tok_sha,
    }

    lat_ce: list[float] = []
    scored_pair_count = 0
    with LOGITS_PATH.open("w", encoding="utf-8") as fh:
        for case in cases:
            prow = pool_by_id[case.case_id]
            h_ids = list(prow["system_h_union_ids"])
            j_ids = list(prow["system_j_union_ids"])
            h_set = set(h_ids)
            missing_text = [cid for cid in j_ids if cid not in chunks_by_id]
            if missing_text:
                raise SystemExit(f"STOP: missing control-chunk text for {case.case_id}: {missing_text[:5]}")
            texts = [chunks_by_id[cid]["text"] for cid in j_ids]
            q_sha = query_sha256(case.question)
            t0 = time.perf_counter()
            scores = ce.score_pairs(case.question, texts, batch_size=16)
            lat_ce.append((time.perf_counter() - t0) * 1000.0)
            if len(scores) != len(j_ids):
                raise SystemExit(f"STOP: CE returned {len(scores)} scores for {len(j_ids)} J ids on {case.case_id}")
            for stored_j_index, (cid, score) in enumerate(zip(j_ids, scores, strict=True)):
                logit = float(score)
                hx, be = logit_hex(logit)
                rec = {
                    "case_id": case.case_id,
                    "chunk_id": cid,
                    "candidate_arm": "H" if cid in h_set else "J_ONLY",
                    "raw_ce_logit": logit,
                    "raw_ce_logit_hex": hx,
                    "raw_ce_logit_be64_hex": be,
                    "input_hash": input_hash(case.case_id, cid, case.question, chunks_by_id[cid]["text"]),
                    "ce_artifact_sha": ce.artifact_sha256,
                    "tokenizer_identity": tokenizer_identity,
                    "max_length": 512,
                    "query_association": {
                        "case_id": case.case_id,
                        "query_sha256": q_sha,
                    },
                    "stored_j_index": stored_j_index,
                    "ce_name": CE_NAME,
                    "ce_revision": CE_REVISION,
                }
                fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
                fh.flush()
                scored_pair_count += 1
            print(
                f"CE {case.case_id} n={len(j_ids)} ms={lat_ce[-1]:.1f} cumulative_pairs={scored_pair_count}",
                flush=True,
            )

    if scored_pair_count != EXPECTED_J:
        raise SystemExit(f"STOP: scored_pair_count {scored_pair_count} != {EXPECTED_J}")

    gate = persistence_gate(h_pairs=h_pairs, j_pairs=j_pairs)
    if not gate["ok"]:
        try:
            emb = embedding_status()
            env = env_fingerprint(emb)
        except Exception as exc:
            emb = {"error": str(exc), "note": "postgres env fingerprint unavailable on STOP path"}
            env = {"error": str(exc), "known_drift": "PostgreSQL 16.15 / pgvector 0.8.6 vs historical 16.13 / 0.6.0"}
        natq_after = natq_holdout_log_state()
        v1_after = holdout_log_state()
        integrity_failures = []
        if natq_after["log_bytes"] != 0 or natq_after["log_sha256"] != NATQ_LOG_SHA:
            integrity_failures.append("NATQ holdout access log changed")
        if v1_after["log_bytes"] != 235 or v1_after["log_sha256"] != V1_LOG_SHA:
            integrity_failures.append("V1 holdout access log changed")
        if _sha(H_FILE) != H_FILE_SHA or _sha(J_FILE) != J_FILE_SHA or _sha(K_FILE) != K_FILE_SHA:
            integrity_failures.append("H/J/K identity file mutated")
        if _sha(VAL_JSONL) != VAL_SHA:
            integrity_failures.append("validation.jsonl mutated")
        if _sha(PREREG_JSON) != PREREG_JSON_SHA:
            integrity_failures.append("prereg json mutated")
        write_stop_persistence(
            gate=gate,
            natq_before=natq_before,
            natq_after=natq_after,
            v1_before=v1_before,
            v1_after=v1_after,
            hash_check=hash_check,
            env=env,
            emb=emb,
            started=started,
            integrity_failures=integrity_failures,
            exp022a_check=exp022a_unchanged(),
            ce_info=ce_info,
        )
        print("STOPPED_PERSISTENCE_GATE " + json.dumps({k: v for k, v in gate.items() if k != "logits"}), flush=True)
        return 0

    # Persistence passed. Rank from persisted logits (hex-exact). Then aggregates, then diagnostics.
    stored_logits: dict[tuple[str, str], float] = gate["logits"]
    per_case = []
    cases_h = {}
    cases_j = {}
    extra_ranks_all: list[int] = []

    for case in cases:
        prow = pool_by_id[case.case_id]
        meta = meta_by_id[case.case_id]
        h_ids = list(prow["system_h_union_ids"])
        j_ids = list(prow["system_j_union_ids"])
        h_set = set(h_ids)
        extras = [cid for cid in j_ids if cid not in h_set]
        h_logits = {cid: stored_logits[(case.case_id, cid)] for cid in h_ids}
        j_logits = {cid: stored_logits[(case.case_id, cid)] for cid in j_ids}
        h_rows = rows_from_ranked(h_ids, h_logits, chunks_by_id)
        j_rows = rows_from_ranked(j_ids, j_logits, chunks_by_id)
        h_hits = hits_from_ids(h_ids, chunks_by_id)
        j_hits = hits_from_ids(j_ids, chunks_by_id)
        scored_h = score_system(case, h_rows, "ce_only_rank", h_hits, gold_cover)
        scored_j = score_system(case, j_rows, "ce_only_rank", j_hits, gold_cover)
        cases_h[case.case_id] = scored_h
        cases_j[case.case_id] = scored_j
        j_rank = {r["chunk_id"]: r["ce_only_rank"] for r in j_rows}
        extra_rank_list = [j_rank[cid] for cid in extras]
        extra_ranks_all.extend(extra_rank_list)
        tags = list(meta.get("coverage_tags") or [])
        stress = list(meta.get("stress_types") or [])
        rec = {
            "case_id": case.case_id,
            "provider": meta.get("provider"),
            "coverage_tags": tags,
            "stress_types": stress,
            "n_gold_spans": len(case.expected_evidence),
            "h_pool": len(h_ids),
            "j_pool": len(j_ids),
            "n_extras": len(extras),
            "H_strict": bool(scored_h["fully_recalled"]),
            "J_strict": bool(scored_j["fully_recalled"]),
            "H_span_found": sum(1 for s in scored_h["spans"] if s["within_10"]),
            "J_span_found": sum(1 for s in scored_j["spans"] if s["within_10"]),
            "H_doc_recall": scored_h["doc_recall"],
            "J_doc_recall": scored_j["doc_recall"],
            "H_spans": scored_h["spans"],
            "J_spans": scored_j["spans"],
            "extra_ce_ranks": extra_rank_list,
            "is_multi_span": is_multi_span(len(case.expected_evidence), tags, stress),
            "j_top10_version_ids": [r["version_id"] for r in j_rows[:TOP_K]],
            "j_top10_section_paths": [
                json.dumps(list(r["section_path"]), ensure_ascii=True, separators=(",", ":")) for r in j_rows[:TOP_K]
            ],
        }
        per_case.append(rec)

    n = 40
    n_spans = sum(len(c.expected_evidence) for c in cases)
    s_h = summarise(cases_h, "SYSTEM-H-CE-ONLY", H_CONFIG_HASH)
    s_j = summarise(cases_j, "SYSTEM-J-CE-ONLY", J_CONFIG_HASH)
    h_strict = s_h["cases_fully_recalled"]
    j_strict = s_j["cases_fully_recalled"]
    h_span = s_h["spans_found_at_10"]
    j_span = s_j["spans_found_at_10"]
    h_doc = sum(1 for c in cases_h.values() if c["doc_recall"] == 1.0)
    j_doc = sum(1 for c in cases_j.values() if c["doc_recall"] == 1.0)

    h_pass = {r["case_id"]: r["H_strict"] for r in per_case}
    j_pass = {r["case_id"]: r["J_strict"] for r in per_case}
    rescues = [cid for cid, ok in j_pass.items() if ok and not h_pass[cid]]
    regressions = [cid for cid, ok in j_pass.items() if h_pass[cid] and not ok]
    both_pass = [cid for cid, ok in j_pass.items() if ok and h_pass[cid]]
    both_fail = [cid for cid, ok in j_pass.items() if (not ok) and (not h_pass[cid])]
    n01 = len(rescues)
    n10 = len(regressions)
    mc = mcnemar_exact(n01, n10)

    def provider_metrics(provider: str) -> dict:
        sub = [r for r in per_case if r["provider"] == provider]
        ns = sum(r["n_gold_spans"] for r in sub)
        return {
            "n_cases": len(sub),
            "H_strict": f"{sum(1 for r in sub if r['H_strict'])}/{len(sub)}",
            "J_strict": f"{sum(1 for r in sub if r['J_strict'])}/{len(sub)}",
            "H_span": f"{sum(r['H_span_found'] for r in sub)}/{ns}",
            "J_span": f"{sum(r['J_span_found'] for r in sub)}/{ns}",
        }

    multi = [r for r in per_case if r["is_multi_span"]]
    multi_h_strict = sum(1 for r in multi if r["H_strict"])
    multi_j_strict = sum(1 for r in multi if r["J_strict"])
    multi_h_span = sum(r["H_span_found"] for r in multi)
    multi_j_span = sum(r["J_span_found"] for r in multi)
    multi_span_d = sum(r["n_gold_spans"] for r in multi)

    # AFTER aggregates only: four recovered spans + multi-span diagnosis
    named_diag = []
    for rec in per_case:
        case = next(c for c in cases if c.case_id == rec["case_id"])
        prow = pool_by_id[case.case_id]
        j_ids = list(prow["system_j_union_ids"])
        j_logits = {cid: stored_logits[(case.case_id, cid)] for cid in j_ids}
        j_rows = rows_from_ranked(j_ids, j_logits, chunks_by_id)
        j_rank = {r["chunk_id"]: r["ce_only_rank"] for r in j_rows}
        for span_index in [i for cid, i in NAMED_J_RECOVERIES if cid == case.case_id]:
            cover = gold_cover[case.case_id][span_index]
            cover_in_j = [c for c in cover if c in j_rank]
            chosen = min(cover_in_j, key=lambda c: (j_rank[c], c)) if cover_in_j else None
            if chosen is None:
                named_diag.append({"case_id": case.case_id, "span_index": span_index, "in_j_pool": False})
                continue
            rank = j_rank[chosen]
            higher = [r for r in j_rows if r["ce_only_rank"] < rank]
            named_diag.append(
                {
                    "case_id": case.case_id,
                    "span_index": span_index,
                    "chunk_id": chosen,
                    "raw_ce_logit": j_logits[chosen],
                    "raw_ce_logit_hex": float(j_logits[chosen]).hex(),
                    "ce_only_rank_in_J": rank,
                    "enters_top10": rank <= TOP_K,
                    "n_higher_ranked_same_version_id": sum(
                        1 for r in higher if r["version_id"] == chunks_by_id[chosen]["version_id"]
                    ),
                    "n_higher_ranked_same_section_path": sum(
                        1 for r in higher if list(r["section_path"]) == list(chunks_by_id[chosen]["section_path"])
                    ),
                }
            )

    multi_detail = []
    for r in multi:
        case = next(c for c in cases if c.case_id == r["case_id"])
        prow = pool_by_id[r["case_id"]]
        j_ids = list(prow["system_j_union_ids"])
        j_hits = hits_from_ids(j_ids, chunks_by_id)
        in_pool = sum(1 for ref in case.expected_evidence if span_in_hits(j_hits, ref))
        span_ranks = [
            {
                "span_index": s["span_index"],
                "in_pool": s["in_pool"],
                "ce_only_rank": s["rank"],
                "within_10": s["within_10"],
            }
            for s in r["J_spans"]
        ]
        n_top = len(r["j_top10_version_ids"])
        n_vid = len(set(r["j_top10_version_ids"]))
        n_sec = len(set(r["j_top10_section_paths"]))
        multi_detail.append(
            {
                "case_id": r["case_id"],
                "required_span_count": r["n_gold_spans"],
                "spans_in_SYSTEM_J_pool": in_pool,
                "spans_in_J_CE_only_top10": r["J_span_found"],
                "in_pool_gold_span_ranks": span_ranks,
                "unique_version_ids_in_J_CE_top10": n_vid,
                "unique_section_paths_in_J_CE_top10": n_sec,
                "redundant_top10_by_version_id": max(0, n_top - n_vid),
                "redundant_top10_by_section_path": max(0, n_top - n_sec),
            }
        )

    natq_after = natq_holdout_log_state()
    v1_after = holdout_log_state()
    integrity_failures: list[str] = []
    if natq_after["log_bytes"] != 0 or natq_after["log_sha256"] != NATQ_LOG_SHA:
        integrity_failures.append("NATQ holdout access log changed")
    if v1_after["log_bytes"] != 235 or v1_after["log_sha256"] != V1_LOG_SHA:
        integrity_failures.append("V1 holdout access log changed")
    if _sha(H_FILE) != H_FILE_SHA:
        integrity_failures.append("SYSTEM-H file mutated")
    if _sha(J_FILE) != J_FILE_SHA:
        integrity_failures.append("SYSTEM-J file mutated")
    if _sha(K_FILE) != K_FILE_SHA:
        integrity_failures.append("SYSTEM-K file mutated")
    if _sha(VAL_JSONL) != VAL_SHA:
        integrity_failures.append("validation.jsonl mutated")
    if _sha(PREREG_JSON) != PREREG_JSON_SHA:
        integrity_failures.append("prereg json mutated")
    exp022a_after = exp022a_unchanged()
    if not exp022a_after["all_unchanged"]:
        integrity_failures.append("EXP-022A files rewritten")

    no_integrity = len(integrity_failures) == 0
    gate_eval = {
        "J_strict_improves_ge_2_cases": (j_strict - h_strict) >= 2,
        "J_span_improves_ge_2_spans": (j_span - h_span) >= 2,
        "J_strict_regressions_le_1": len(regressions) <= 1,
        "no_integrity_provenance_failure": no_integrity,
    }
    supported = all(gate_eval.values())

    try:
        emb = embedding_status()
        env = env_fingerprint(emb)
    except Exception as exc:
        emb = {"error": str(exc)}
        env = {"error": str(exc)}

    utc = datetime.now(tz=UTC).replace(microsecond=0)
    et = utc.astimezone(ZoneInfo("America/New_York"))
    payload = {
        "experiment_id": "EXP-022A-R1",
        "scored": True,
        "EXP-022A-R1_STATUS": "SCORED_DEVELOPMENT_REPLAY",
        "diagnostic_label": "EXP-022A-R1-CE-ONLY-H-vs-J",
        "not_independent_validation": True,
        "not_EVAL_NATQ_VAL_002": True,
        "original_EXP-022A_closed_as": "STOPPED_MISSING_STORED_H_CE_LOGITS",
        "original_EXP-022A_rewritten": False,
        "preregistration_json_sha256": PREREG_JSON_SHA,
        "raw_logit_jsonl_sha256": gate["jsonl_sha256"],
        "timestamp": utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timestamp_et": et.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "hash_check": hash_check,
        "SYSTEM_H_file_unchanged": _sha(H_FILE) == H_FILE_SHA,
        "SYSTEM_J_file_unchanged": _sha(J_FILE) == J_FILE_SHA,
        "SYSTEM_K_file_unchanged": _sha(K_FILE) == K_FILE_SHA,
        "natq_holdout_access_log_before": natq_before,
        "natq_holdout_access_log_after": natq_after,
        "v1_holdout_access_log_before": {"log_bytes": v1_before["log_bytes"], "log_sha256": v1_before["log_sha256"]},
        "v1_holdout_access_log_after": {"log_bytes": v1_after["log_bytes"], "log_sha256": v1_after["log_sha256"]},
        "holdout_json_opened": False,
        "v1_holdout_json_opened": False,
        "persistence_gate": {k: v for k, v in gate.items() if k != "logits"},
        "cross_encoder": ce_info,
        "embedding": emb,
        "environment": env,
        "environment_drift_note": "PostgreSQL 16.15 / pgvector 0.8.6 vs historical 16.13 / 0.6.0. CE replay used stored membership and does not depend on pgvector.",
        "PRIMARY": {
            "H_CE_only_strict_Recall@10": f"{h_strict}/{n}",
            "J_CE_only_strict_Recall@10": f"{j_strict}/{n}",
            "delta_cases": j_strict - h_strict,
        },
        "SECONDARY": {
            "H_CE_only_span_Recall@10": f"{h_span}/{n_spans}",
            "J_CE_only_span_Recall@10": f"{j_span}/{n_spans}",
            "delta_spans": j_span - h_span,
            "H_summarise_mrr": s_h["mrr"],
            "J_summarise_mrr": s_j["mrr"],
            "H_document_Recall@10": f"{h_doc}/{n}",
            "J_document_Recall@10": f"{j_doc}/{n}",
            "H_document_recall_mean": s_h["document_recall"],
            "J_document_recall_mean": s_j["document_recall"],
            "multi_span_n": len(multi),
            "multi_span_H_strict": f"{multi_h_strict}/{len(multi)}",
            "multi_span_J_strict": f"{multi_j_strict}/{len(multi)}",
            "multi_span_H_span": f"{multi_h_span}/{multi_span_d}",
            "multi_span_J_span": f"{multi_j_span}/{multi_span_d}",
            "openai": provider_metrics("openai"),
            "anthropic": provider_metrics("anthropic"),
        },
        "PAIRED": {
            "J_rescues_over_H": rescues,
            "J_regressions_vs_H": regressions,
            "both_pass": both_pass,
            "both_fail": both_fail,
            "n_rescues": n01,
            "n_regressions": n10,
            "n_both_pass": len(both_pass),
            "n_both_fail": len(both_fail),
            "mcnemar_exact": mc,
        },
        "LATENCY": {
            "total_CE_wall_ms": round(sum(lat_ce), 3),
            "total_CE_wall_s": round(sum(lat_ce) / 1000.0, 3),
            "mean_per_query_CE_ms": _mean(lat_ce, 3),
            "median_per_query_CE_ms": _median(lat_ce, 3),
            "per_query_CE_ms": [round(x, 3) for x in lat_ce],
            "H_pair_count": EXPECTED_H,
            "J_only_pair_count": EXPECTED_J_ONLY,
            "full_J_pair_count": EXPECTED_J,
            "no_cross_host_architecture_claim": True,
        },
        "diagnostics_four_SYSTEM_J_recovered_spans": named_diag,
        "MULTI_SPAN_ANALYSIS": multi_detail,
        "harness_fix_non_scoring_follow_up": {
            "defect": "EVAL-NATQ-VAL-001 did not persist full-pool raw CE logits",
            "requirement": "Future development/validation reranker executions must persist candidate membership, raw reranker logits, query/candidate association, model fingerprint, and input/config fingerprint",
            "historical_EVAL_NATQ_VAL_001_modified": False,
            "historical_logits_fabricated": False,
        },
        "gate": gate_eval,
        "EXP-022A-R1_CE_RECOGNIZABILITY_SUPPORTED": supported,
        "integrity_failures": integrity_failures,
        "EXP-022A_files_unchanged": exp022a_after,
        "first_span_rank_imported": first_span_rank.__name__,
        "per_case": per_case,
        "elapsed_s": round(time.time() - started, 2),
        "STOP": "Do not build a coverage-aware selector. Do not test SYSTEM-K. Do not modify W/L/P. Do not change CE. Do not open holdout. Return to coordinator ChatGPT.",
    }
    write_scored_report(payload)
    write_reply(payload)
    copy_to_post(
        [
            results_path,
            report_path,
            PREREG_JSON,
            PREREG_MD,
            OUT_DIR / "EXP-022A-R1-preregistration.json.sha256",
            LOGITS_PATH,
            LOGITS_SHA_PATH,
            OUT_DIR / "scripts" / "run_exp022a_r1.py",
        ]
    )
    print(
        f"DONE scored SUPPORTED={supported} H={h_strict}/40 J={j_strict}/40 "
        f"span H={h_span}/{n_spans} J={j_span}/{n_spans} pairs={EXPECTED_J} "
        f"jsonl_sha={gate['jsonl_sha256']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
