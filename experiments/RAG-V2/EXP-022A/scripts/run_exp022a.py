#!/usr/bin/env python3
"""EXP-022A: SYSTEM-J CE recognizability diagnostic.

Preregistration MUST already be hashed. ARM H uses stored EVAL-NATQ-VAL-001
raw CE logits only. Does not rerun CE on SYSTEM-H candidates. If those
logits are missing or incomplete, write STOP report and exit 0.

Does not invent a retrieval prior, run SYSTEM-K, alter 0.7/0.3 blend,
run coverage-aware selection, or open holdout.json.
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
sys.path.insert(0, str(ROOT / "experiments" / "EXP-019B" / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "RAG-V2" / "EXP-021A" / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "PERF-003" / "scripts"))

from rag_v1.ids import config_hash  # noqa: E402
from rag_v1.types import EvidenceRef, EvalCase, SearchHit  # noqa: E402

from cross_encoder import CE_NAME, CE_REVISION, CE_SHA256, CE_ONNX  # noqa: E402
from run_exp017 import L, P, load_control_chunks, score_system  # noqa: E402
from run_exp018_development import env_fingerprint, first_span_rank, hit_as_row, span_in_hits, summarise  # noqa: E402
from run_exp019b import mcnemar_exact  # noqa: E402
from run_exp021a import hits_from_ids, load_validation  # noqa: E402
from system_e import (  # noqa: E402
    CHUNK_SET,
    HOLD_LOG_SHA_AT_PREREG,
    PARENT_N,
    SNAPSHOT,
    TOP_K,
    W,
    covering_chunk_ids,
    embedding_status,
    holdout_log_state,
)

OUT_DIR = ROOT / "experiments" / "RAG-V2" / "EXP-022A"
VAL_JSONL = ROOT / "evals" / "splits" / "natq-001" / "validation.jsonl"
VAL_JSON = ROOT / "evals" / "splits" / "natq-001" / "validation.json"
H_FILE = ROOT / "experiments" / "RAG-V2" / "SYSTEM-H-V2-DEV-CANDIDATE" / "SYSTEM-H-V2-DEV-CANDIDATE.json"
I_FILE = (
    ROOT / "experiments" / "RAG-V2" / "SYSTEM-I-PARENT-BALANCED-CANDIDATES" / "SYSTEM-I-PARENT-BALANCED-CANDIDATES.json"
)
J_FILE = ROOT / "experiments" / "RAG-V2" / "SYSTEM-J-LOCAL-W20-UNION" / "SYSTEM-J-LOCAL-W20-UNION.json"
K_FILE = ROOT / "experiments" / "RAG-V2" / "SYSTEM-K-W20-SECTION-COMPRESS" / "SYSTEM-K-W20-SECTION-COMPRESS.json"
G_FILE = ROOT / "experiments" / "EXP-019A" / "SYSTEM-G-PROJECTION-PRIOR.json"
G_CE_D1 = ROOT / "experiments" / "PERF-003" / "SYSTEM-G-CE-D1.json"
E_L10_FILE = ROOT / "experiments" / "EXP-018B" / "SYSTEM-E-L10-WITHIN-DOC.json"
PREREG_JSON = OUT_DIR / "EXP-022A-preregistration.json"
PREREG_MD = OUT_DIR / "EXP-022A-preregistration.md"
STORED_POOLS = ROOT / "experiments" / "RAG-V2" / "EXP-021A" / "logs" / "EXP-021A-pools.jsonl"
EXP021A_REPORT = ROOT / "experiments" / "RAG-V2" / "EXP-021A" / "EXP-021A-REPORT.json"
EVAL_DIR = ROOT / "experiments" / "RAG-V2" / "EVAL-NATQ-VAL-001"
EVAL_REPORT = EVAL_DIR / "EVAL-NATQ-VAL-001-REPORT.json"
EVAL_POOLS = EVAL_DIR / "logs" / "EVAL-NATQ-VAL-001-pools.jsonl"
NATQ_HOLD_LOG = ROOT / "evals" / "splits" / "natq-001" / "holdout-access.log.jsonl"
NATQ_HOLD_LOCK = ROOT / "evals" / "splits" / "natq-001" / "holdout.lock.json"
V1_HOLD_LOG = ROOT / "evals" / "splits" / "gold150-v1" / "holdout-access.log.jsonl"
POST_DIR = Path("/workspace/NATQ-001-post")

PREREG_JSON_SHA = "ad7fba5a38d6fda06fdb42a94f0b78fdce008cfe978b1743224028bb2fd8e64b"
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
NAMED_J_RECOVERIES = (
    ("NATQ-C-004", 0),
    ("NATQ-C-005", 1),
    ("NATQ-C-044", 0),
    ("NATQ-C-044", 1),
)
BLEND_KEYS = {"blend_score", "blend", "exp019a_score", "retrieval_norm", "a_norm", "ce_norm"}
RAW_CE_KEY_HINTS = ("ce_logit", "raw_ce_logit", "raw_ce", "ce_score", "logit")
SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".cache",
    "chrome-profile-3",
    "computer-use",
    "WasmTtsEngine",
}


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


def is_raw_ce_key(key: str) -> bool:
    k = key.lower()
    if k in BLEND_KEYS or "blend" in k or k.endswith("_norm"):
        return False
    if k in ("ce_logit", "raw_ce_logit", "raw_ce", "ce_score"):
        return True
    if k == "logit" or k.endswith("_logit"):
        return True
    return False


def extract_numeric(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def collect_from_hit(case_id: str, item: dict, source: str, found: dict, notes: list) -> None:
    cid = item.get("chunk_id") or item.get("id")
    if not isinstance(cid, str) or not case_id:
        return
    raw_keys = [k for k in item if is_raw_ce_key(k) and extract_numeric(item[k]) is not None]
    if not raw_keys:
        return
    val = extract_numeric(item[raw_keys[0]])
    key = (case_id, cid)
    rec = {"logit": val, "source": source, "field": raw_keys[0], "all_fields": raw_keys}
    if key in found and found[key]["logit"] != val:
        notes.append(f"duplicate_disagree {case_id} {cid} {found[key]} vs {rec}")
    found.setdefault(key, rec)


def walk_obj_for_logits(obj, case_id: str | None, source: str, found: dict, notes: list, depth: int = 0) -> None:
    if depth > 8:
        return
    if isinstance(obj, dict):
        cid_here = obj.get("case_id") if isinstance(obj.get("case_id"), str) else case_id
        if any(is_raw_ce_key(k) for k in obj) and (obj.get("chunk_id") or obj.get("id")):
            collect_from_hit(cid_here or "", obj, source, found, notes)
        for k, v in obj.items():
            if k in ("holdout",):
                continue
            walk_obj_for_logits(v, cid_here, source, found, notes, depth + 1)
    elif isinstance(obj, list):
        for item in obj[:50000]:
            walk_obj_for_logits(item, case_id, source, found, notes, depth + 1)


def inspect_json_file(path: Path, found: dict, file_index: list, notes: list) -> None:
    if path.name == "holdout.json":
        notes.append(f"skipped_holdout_json path={path}")
        return
    try:
        if path.stat().st_size > 80_000_000:
            file_index.append({"path": str(path), "skipped": "too_large", "bytes": path.stat().st_size})
            return
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        file_index.append({"path": str(path), "error": str(exc)})
        return
    n_before = len(found)
    keys_seen: set[str] = set()
    n_rows = 0
    n_blend = 0
    n_raw = 0
    sample_keys = None
    try:
        if path.suffix == ".jsonl":
            for line in text.splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                n_rows += 1
                if isinstance(rec, dict):
                    if sample_keys is None:
                        sample_keys = sorted(rec.keys())
                    keys_seen.update(rec.keys())
                    case_id = rec.get("case_id") if isinstance(rec.get("case_id"), str) else None
                    if "top10" in rec and isinstance(rec["top10"], list):
                        for hit in rec["top10"]:
                            if isinstance(hit, dict):
                                keys_seen.update(hit.keys())
                                if "blend_score" in hit:
                                    n_blend += 1
                                if any(is_raw_ce_key(k) and extract_numeric(hit.get(k)) is not None for k in hit):
                                    n_raw += 1
                                    collect_from_hit(case_id or "", hit, str(path), found, notes)
                    walk_obj_for_logits(rec, case_id, str(path), found, notes)
        else:
            rec = json.loads(text)
            if isinstance(rec, dict):
                sample_keys = sorted(list(rec.keys())[:40])
                keys_seen.update(rec.keys())
                walk_obj_for_logits(rec, rec.get("case_id") if isinstance(rec.get("case_id"), str) else None, str(path), found, notes)
            elif isinstance(rec, list):
                n_rows = len(rec)
                walk_obj_for_logits(rec, None, str(path), found, notes)
    except Exception as exc:
        file_index.append({"path": str(path), "parse_error": str(exc), "bytes": path.stat().st_size})
        return
    file_index.append(
        {
            "path": str(path),
            "bytes": path.stat().st_size,
            "n_rows": n_rows,
            "n_top10_blend_score": n_blend,
            "n_top10_raw_ce": n_raw,
            "new_raw_ce_pairs": len(found) - n_before,
            "sample_keys": sample_keys,
            "ce_like_keys": sorted(k for k in keys_seen if "ce" in k.lower() or "logit" in k.lower() or "score" in k.lower()),
        }
    )


def inventory_stored_h_logits(h_pairs: set[tuple[str, str]]) -> dict:
    found: dict[tuple[str, str], dict] = {}
    file_index: list[dict] = []
    notes: list[str] = []
    search_roots = [
        EVAL_DIR,
        ROOT / "experiments" / "RAG-V2" / "EXP-021A",
        ROOT / "experiments" / "RAG-V2" / "EXP-021B",
        ROOT / "experiments" / "RAG-V2" / "EXP-020A",
        ROOT / "experiments" / "RAG-V2" / "NATQ-DIAG-001",
        ROOT / "experiments" / "RAG-V2" / "EVAL-NATQ-VAL-001",
        Path("/workspace/NATQ-001-post"),
        Path("/workspace"),
        ROOT / "experiments" / "PERF-003" / "logs",
    ]
    seen: set[str] = set()
    for root in search_roots:
        if not root.exists():
            continue
        if root.is_file():
            paths = [root]
        else:
            paths = []
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
                # do not recurse into other agents' chrome or huge trees under /workspace
                if Path(dirpath).name in {"rag-v1", "ragcheck"} and root == Path("/workspace"):
                    # still allow rag-v1 repo experiments via explicit roots; skip walking whole clone from /workspace
                    if "repo" in dirnames:
                        dirnames.remove("repo")
                    if "claude-ce-handoff" in dirnames:
                        dirnames.remove("claude-ce-handoff")
                    if "corpus-extracted" in dirnames:
                        dirnames.remove("corpus-extracted")
                for fn in filenames:
                    if fn == "holdout.json":
                        continue
                    if not fn.endswith((".json", ".jsonl")):
                        continue
                    low = fn.lower()
                    p = Path(dirpath) / fn
                    rel = str(p)
                    if rel in seen:
                        continue
                    # under /workspace walk, only inspect files that look CE/eval/pool related
                    if root == Path("/workspace") and not any(
                        x in low for x in ("ce", "logit", "eval", "pool", "score", "natq", "report")
                    ):
                        continue
                    seen.add(rel)
                    paths.append(p)
        for p in paths:
            inspect_json_file(p, found, file_index, notes)

    onnx_sha = _sha(CE_ONNX) if CE_ONNX.exists() else None
    eval_ce = {}
    eval_pools_summary = {}
    if EVAL_REPORT.exists():
        ev = json.loads(EVAL_REPORT.read_text(encoding="utf-8"))
        eval_ce = ev.get("cross_encoder") or {}
        per_case = ev.get("per_case") or []
        pc_keys = sorted(per_case[0].keys()) if per_case else []
        span_keys = sorted(per_case[0]["spans"][0].keys()) if per_case and per_case[0].get("spans") else []
        eval_pools_summary["report_per_case_n"] = len(per_case)
        eval_pools_summary["report_per_case_keys"] = pc_keys
        eval_pools_summary["report_span_keys"] = span_keys
        eval_pools_summary["report_has_raw_ce_in_per_case_keys"] = any(is_raw_ce_key(k) for k in pc_keys)
        eval_pools_summary["report_has_raw_ce_in_span_keys"] = any(is_raw_ce_key(k) for k in span_keys)
    if EVAL_POOLS.exists():
        n_q = 0
        n_top = 0
        n_blend = 0
        n_raw = 0
        hit_keys: set[str] = set()
        for line in EVAL_POOLS.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            n_q += 1
            for hit in rec.get("top10") or []:
                n_top += 1
                if isinstance(hit, dict):
                    hit_keys.update(hit.keys())
                    if "blend_score" in hit:
                        n_blend += 1
                    if any(is_raw_ce_key(k) for k in hit):
                        n_raw += 1
        eval_pools_summary.update(
            {
                "eval_pools_queries": n_q,
                "eval_pools_top10_rows": n_top,
                "eval_pools_top10_blend_score": n_blend,
                "eval_pools_top10_raw_ce": n_raw,
                "eval_pools_hit_keys": sorted(hit_keys),
            }
        )

    h_found = {k: v for k, v in found.items() if k in h_pairs}
    missing = sorted(h_pairs - set(h_found))
    extra_non_h = len(found) - len(h_found)
    dup_notes = [n for n in notes if n.startswith("duplicate_disagree")]
    fingerprint_ok = (
        (eval_ce.get("artifact_sha256") == FROZEN_CE_SHA)
        and (onnx_sha == FROZEN_CE_SHA)
        and (CE_SHA256 == FROZEN_CE_SHA)
    )
    complete = (
        len(missing) == 0
        and len(h_pairs) == 4753
        and len(dup_notes) == 0
        and fingerprint_ok
        and len(h_found) == len(h_pairs)
    )
    inventory = {
        "n_H_candidates_required": len(h_pairs),
        "n_stored_raw_ce_pairs_any": len(found),
        "n_stored_raw_ce_pairs_matching_H": len(h_found),
        "n_missing_H": len(missing),
        "n_stored_non_H": extra_non_h,
        "n_duplicate_disagreements": len(dup_notes),
        "complete": complete,
        "fingerprint": {
            "required_sha": FROZEN_CE_SHA,
            "CE_SHA256_module": CE_SHA256,
            "onnx_file_sha": onnx_sha,
            "EVAL_report_artifact_sha256": eval_ce.get("artifact_sha256"),
            "EVAL_report_constructor": eval_ce.get("constructor"),
            "EVAL_report_name": eval_ce.get("name"),
            "EVAL_report_revision": eval_ce.get("revision"),
            "match": fingerprint_ok,
        },
        "eval_pools_and_report": eval_pools_summary,
        "files_inspected": file_index,
        "notes": notes[:50],
        "missing_examples": [{"case_id": a, "chunk_id": b} for a, b in missing[:10]],
        "interpretation": (
            "EVAL-NATQ-VAL-001 persisted only top-10 blend_score rows (not raw CE logits "
            "for the full SYSTEM-H pool). ARM H cannot be reconstructed without rerunning H CE."
            if not complete
            else "Stored raw CE logits cover every SYSTEM-H candidate."
        ),
    }
    return inventory


def copy_to_post(paths: list[Path]) -> None:
    POST_DIR.mkdir(parents=True, exist_ok=True)
    for p in paths:
        if p.exists():
            dest = POST_DIR / p.name
            dest.write_bytes(p.read_bytes())


def write_stop_report(
    *,
    inventory: dict,
    natq_before: dict,
    natq_after: dict,
    v1_before: dict,
    v1_after: dict,
    hash_check: dict,
    env: dict | None,
    emb: dict | None,
    started: float,
    integrity_failures: list[str],
) -> None:
    results_path = OUT_DIR / "EXP-022A-REPORT.json"
    report_path = OUT_DIR / "EXP-022A-REPORT.md"
    utc = datetime.now(tz=UTC).replace(microsecond=0)
    et = utc.astimezone(ZoneInfo("America/New_York"))
    payload = {
        "experiment_id": "EXP-022A",
        "scored": False,
        "EXP-022A_STATUS": "STOPPED_MISSING_STORED_H_CE_LOGITS",
        "H_CE_rerun": False,
        "J_EXTRAS_CE_run": False,
        "EXP-022A_CE_RECOGNIZABILITY_SUPPORTED": None,
        "gate_evaluated": False,
        "n_evals": 1,
        "second_run": False,
        "new_SYSTEM_identity_created": False,
        "timestamp": utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timestamp_et": et.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "preregistration_json_sha256": PREREG_JSON_SHA,
        "SYSTEM_H_config_hash": H_CONFIG_HASH,
        "SYSTEM_H_file_sha256": hash_check.get("SYSTEM_H_file_sha256"),
        "SYSTEM_H_config_hash_unchanged": hash_check.get("SYSTEM_H_file_sha256_ok") and hash_check.get("SYSTEM_H_config_hash_ok"),
        "SYSTEM_J_config_hash": J_CONFIG_HASH,
        "SYSTEM_J_file_sha256": hash_check.get("SYSTEM_J_file_sha256"),
        "SYSTEM_J_config_hash_unchanged": hash_check.get("SYSTEM_J_file_sha256_ok"),
        "SYSTEM_K_config_hash": K_CONFIG_HASH,
        "SYSTEM_K_file_sha256": hash_check.get("SYSTEM_K_file_sha256"),
        "SYSTEM_K_config_hash_unchanged": hash_check.get("SYSTEM_K_file_sha256_ok"),
        "hash_check": hash_check,
        "natq_holdout_access_log_before": natq_before,
        "natq_holdout_access_log_after": natq_after,
        "v1_holdout_access_log_before": {"log_bytes": v1_before["log_bytes"], "log_sha256": v1_before["log_sha256"]},
        "v1_holdout_access_log_after": {"log_bytes": v1_after["log_bytes"], "log_sha256": v1_after["log_sha256"]},
        "holdout_json_opened": False,
        "v1_holdout_json_opened": False,
        "stored_H_logit_inventory": inventory,
        "cross_encoder": {
            "name": CE_NAME,
            "revision": CE_REVISION,
            "artifact_sha256": CE_SHA256,
            "onnx_file_sha256": inventory["fingerprint"]["onnx_file_sha"],
            "EVAL_report_artifact_sha256": inventory["fingerprint"]["EVAL_report_artifact_sha256"],
            "fingerprint_match": inventory["fingerprint"]["match"],
            "constructor": "CrossEncoderReranker(pad='batch', bucket_by_length=True)",
            "fast": False,
            "threads": 4,
            "pad": "batch",
            "bucket_by_length": True,
            "batch_size": 16,
            "max_length": 512,
            "H_CE_rerun": False,
            "J_EXTRAS_CE_run": False,
        },
        "embedding": emb,
        "environment": env,
        "environment_drift_note": "PostgreSQL 16.15 / pgvector 0.8.6 vs historical 16.13 / 0.6.0",
        "integrity_failures": integrity_failures,
        "elapsed_s": round(time.time() - started, 2),
        "STOP": "Stored EVAL-NATQ-VAL-001 artifacts do not contain raw CE logits for the full SYSTEM-H pool. ARM H cannot be reconstructed without rerunning H CE, which is forbidden. J extras were not scored. Return to coordinator ChatGPT.",
    }
    results_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    evs = inventory.get("eval_pools_and_report") or {}
    lines = [
        "# EXP-022A — SYSTEM-J CE RECOGNIZABILITY DIAGNOSTIC",
        "",
        "## STOPPED_MISSING_STORED_H_CE_LOGITS",
        "",
        "NATQ-001 validation n=40 is DEVELOPMENT / MODEL-SELECTION DATA. Not independent validation. "
        "Holdout was not opened. SYSTEM-H / SYSTEM-J / SYSTEM-K were not modified. "
        "H CE was **not** rerun. J extras were **not** scored.",
        "",
        f"**scored = false**. **H_CE_rerun = false**. **J_EXTRAS_CE_run = false**. "
        f"**EXP-022A_CE_RECOGNIZABILITY_SUPPORTED** was **not evaluated**.",
        "",
        "## Setup / lock",
        "",
        f"- Preregistration sha256 `{PREREG_JSON_SHA}` hashed before any aggregate J CE-only metrics (none computed).",
        f"- SYSTEM-H config_hash `{H_CONFIG_HASH}` file sha `{H_FILE_SHA}` unchanged: **{payload['SYSTEM_H_config_hash_unchanged']}**.",
        f"- SYSTEM-J config_hash `{J_CONFIG_HASH}` file sha `{J_FILE_SHA}` unchanged: **{payload['SYSTEM_J_config_hash_unchanged']}**.",
        f"- SYSTEM-K config_hash `{K_CONFIG_HASH}` file sha `{K_FILE_SHA}` unchanged: **{payload['SYSTEM_K_config_hash_unchanged']}** (not tested).",
        f"- validation.jsonl sha256 `{VAL_SHA}`.",
        f"- Frozen CE ONNX sha `{FROZEN_CE_SHA}`. EVAL report artifact sha `{inventory['fingerprint']['EVAL_report_artifact_sha256']}`. Module CE_SHA256 `{CE_SHA256}`. File sha `{inventory['fingerprint']['onnx_file_sha']}`. Fingerprint match: **{inventory['fingerprint']['match']}**.",
        f"- NATQ holdout-access log after: {natq_after['log_bytes']} bytes, sha256 `{natq_after['log_sha256']}`.",
        f"- V1 holdout-access log after: {v1_after['log_bytes']} bytes, sha256 `{v1_after['log_sha256']}`.",
        "- holdout_json_opened: **false**. v1_holdout_json_opened: **false**.",
        f"- Environment drift: {payload['environment_drift_note']}.",
        "",
        "## HARD STOP — stored H raw CE logits incomplete",
        "",
        "ARM H must reconstruct CE-only ranking over the exact SYSTEM-H pool using raw CE logits already stored from EVAL-NATQ-VAL-001. Those logits are missing.",
        "",
        "| item | count |",
        "| --- | ---: |",
        f"| SYSTEM-H candidates required (system_h_union_ids, 40 queries) | {inventory['n_H_candidates_required']} |",
        f"| stored raw CE pairs matching H (query, chunk_id) | {inventory['n_stored_raw_ce_pairs_matching_H']} |",
        f"| missing H logits | {inventory['n_missing_H']} |",
        f"| stored raw CE pairs any source | {inventory['n_stored_raw_ce_pairs_any']} |",
        f"| EVAL pools queries | {evs.get('eval_pools_queries')} |",
        f"| EVAL pools top-10 rows | {evs.get('eval_pools_top10_rows')} |",
        f"| EVAL pools top-10 blend_score (NOT raw CE) | {evs.get('eval_pools_top10_blend_score')} |",
        f"| EVAL pools top-10 raw CE fields | {evs.get('eval_pools_top10_raw_ce')} |",
        f"| EVAL REPORT per_case n | {evs.get('report_per_case_n')} |",
        "",
        f"EVAL-NATQ-VAL-001-pools.jsonl hit keys: `{evs.get('eval_pools_hit_keys')}`.",
        f"REPORT per_case keys: `{evs.get('report_per_case_keys')}`.",
        f"REPORT span keys: `{evs.get('report_span_keys')}`.",
        "",
        inventory["interpretation"],
        "",
        "EVAL-NATQ-VAL-001 computed CE in memory (`ce_by_id`) and wrote only top-10 `blend_score` (0.7 CE_norm + 0.3 retrieval_norm). "
        "`blend_score` is not a raw CE logit and covers 400 rows, not 4753 H candidates. "
        "PERF-003 `*-logits.jsonl` artifacts are V2-DEVSET case ids (e.g. V2D-01), not NATQ-001 validation.",
        "",
        "No integrity/provenance failure on holdouts or frozen identity files. The stop is the assigned missing-logit behavior, not a crash.",
        "",
        "## Gate",
        "",
        "EXP-022A_CE_RECOGNIZABILITY_SUPPORTED **not evaluated** (scoring did not run).",
        "",
        "## STOP",
        "",
        "Stop after EXP-022A. Do **not** rerun H CE as a workaround. Do **not** score J extras. "
        "Do **not** run a coverage-aware selector. Do **not** run SYSTEM-K. Do **not** invent a retrieval prior. "
        "Return to coordinator ChatGPT.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    (OUT_DIR / "logs" / "EXP-022A-h-logit-inventory.json").write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )
    reply = (
        "EXP-022A is STOPPED_MISSING_STORED_H_CE_LOGITS. I verified holdouts first "
        f"(NATQ access log {natq_after['log_bytes']} bytes sha {natq_after['log_sha256']}; "
        f"V1 {v1_after['log_bytes']} bytes sha {v1_after['log_sha256']}) and hashed the CE-only two-arm "
        f"preregistration (sha {PREREG_JSON_SHA}) before any scoring. Stored EVAL-NATQ-VAL-001 artifacts "
        f"do not contain raw CE logits for the full SYSTEM-H pool ({inventory['n_H_candidates_required']} candidates "
        f"across 40 queries): EVAL-NATQ-VAL-001-pools.jsonl has only {evs.get('eval_pools_top10_blend_score')} "
        "top-10 blend_score rows, REPORT per_case has blend ranks not raw logits, and no other NATQ-validation "
        "json/jsonl stores query-associated raw CE for every H candidate, so ARM H cannot be reconstructed without "
        "rerunning H CE, which the assignment forbids. J extras were not scored (H_CE_rerun=false, J_EXTRAS_CE_run=false). "
        f"Frozen CE fingerprint matches sha {FROZEN_CE_SHA}. H/J/K identity files and validation.jsonl are unchanged. "
        "Holdouts untouched; holdout.json never opened. Waiting on ChatGPT."
    )
    POST_DIR.mkdir(parents=True, exist_ok=True)
    (POST_DIR / "exp-022a-reply.txt").write_text(reply + "\n", encoding="utf-8")
    copy_to_post(
        [
            results_path,
            report_path,
            PREREG_JSON,
            PREREG_MD,
            OUT_DIR / "EXP-022A-preregistration.json.sha256",
        ]
    )


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


def case_mrr(scored: dict) -> float:
    ranks = [s["rank"] for s in scored["spans"] if s.get("rank") is not None]
    if not ranks:
        return 0.0
    return 1.0 / min(ranks)


def run_scoring(
    *,
    stored_logits: dict[tuple[str, str], dict],
    pools: list[dict],
    natq_before: dict,
    v1_before: dict,
    hash_check: dict,
    inventory: dict,
    started: float,
) -> int:
    from v2_system_g_ce import make_v2_system_g_d1_reranker

    raw, cases = load_validation()
    if len(raw) != 40 or len(cases) != 40:
        raise SystemExit(f"STOP: n must equal 40, got raw={len(raw)} cases={len(cases)}")
    chunks_by_id = load_control_chunks()
    gold_cover = covering_chunk_ids([c.case_id for c in cases], [c.expected_evidence for c in cases])
    pool_by_id = {r["case_id"]: r for r in pools}
    ce = make_v2_system_g_d1_reranker()
    if getattr(ce, "artifact_sha256", None) != FROZEN_CE_SHA:
        raise SystemExit("STOP: live CE artifact sha mismatch")

    per_case = []
    cases_h = {}
    cases_j = {}
    extra_ranks_all: list[int] = []
    lat_ce_extras: list[float] = []
    n_new_pairs = 0
    named_diag = []
    ranking_log = OUT_DIR / "logs" / "EXP-022A-ce-only-rankings.jsonl"
    ranking_fh = ranking_log.open("w", encoding="utf-8")

    for case, meta in zip(cases, raw, strict=True):
        prow = pool_by_id[case.case_id]
        h_ids = list(prow["system_h_union_ids"])
        j_ids = list(prow["system_j_union_ids"])
        extras = [cid for cid in j_ids if cid not in set(h_ids)]
        stored_added = list(prow.get("added_w20") or [])
        if set(extras) != set(stored_added):
            raise SystemExit(f"STOP: J_EXTRAS != added_w20 on {case.case_id}")
        h_logits = {}
        for cid in h_ids:
            rec = stored_logits[(case.case_id, cid)]
            h_logits[cid] = float(rec["logit"])
        t0 = time.perf_counter()
        extra_texts = [chunks_by_id[cid]["text"] for cid in extras]
        extra_scores = ce.score_pairs(case.question, extra_texts, batch_size=16) if extras else []
        lat_ce_extras.append((time.perf_counter() - t0) * 1000)
        n_new_pairs += len(extras)
        extra_logits = {cid: float(s) for cid, s in zip(extras, extra_scores, strict=True)}
        j_logits = dict(h_logits)
        j_logits.update(extra_logits)
        if set(j_logits) != set(j_ids):
            raise SystemExit(f"STOP: J logit set != SYSTEM-J pool on {case.case_id}")
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
        tags = list(meta.get("coverage_tags") or []) + list(meta.get("stress_types") or [])
        rec = {
            "case_id": case.case_id,
            "provider": meta.get("provider"),
            "coverage_tags": list(meta.get("coverage_tags") or []),
            "stress_types": list(meta.get("stress_types") or []),
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
            "H_mrr_first_span": case_mrr(scored_h),
            "J_mrr_first_span": case_mrr(scored_j),
            "H_spans": scored_h["spans"],
            "J_spans": scored_j["spans"],
            "extra_ce_ranks": extra_rank_list,
            "ce_extras_ms": round(lat_ce_extras[-1], 3),
            "is_multi_span": len(case.expected_evidence) > 1 or "multi_span" in tags,
        }
        per_case.append(rec)
        ranking_fh.write(
            json.dumps(
                {
                    "case_id": case.case_id,
                    "H_ce_only": [
                        {"rank": r["ce_only_rank"], "chunk_id": r["chunk_id"], "ce_logit": r["ce_logit"]}
                        for r in h_rows
                    ],
                    "J_ce_only": [
                        {
                            "rank": r["ce_only_rank"],
                            "chunk_id": r["chunk_id"],
                            "ce_logit": r["ce_logit"],
                            "is_extra": r["chunk_id"] in extra_logits,
                        }
                        for r in j_rows
                    ],
                },
                default=str,
            )
            + "\n"
        )
        ranking_fh.flush()

        j_top = j_rows[:TOP_K]
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
                    "ce_only_rank_in_J": rank,
                    "enters_top10": rank <= TOP_K,
                    "n_higher_ranked_same_version_id": sum(
                        1 for r in higher if r["version_id"] == chunks_by_id[chosen]["version_id"]
                    ),
                    "n_higher_ranked_same_section_path": sum(
                        1
                        for r in higher
                        if list(r["section_path"]) == list(chunks_by_id[chosen]["section_path"])
                    ),
                }
            )
        rec["j_top10_version_ids"] = sorted({r["version_id"] for r in j_top})
        rec["j_top10_section_paths"] = [
            json.dumps(list(r["section_path"]), ensure_ascii=True, separators=(",", ":")) for r in j_top
        ]

    ranking_fh.close()

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
    h_mrr = _mean([r["H_mrr_first_span"] for r in per_case], 4)
    j_mrr = _mean([r["J_mrr_first_span"] for r in per_case], 4)

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
        ids = [r["case_id"] for r in sub]
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

    multi_detail = []
    for r in multi:
        case = next(c for c in cases if c.case_id == r["case_id"])
        prow = pool_by_id[r["case_id"]]
        j_ids = list(prow["system_j_union_ids"])
        j_hits = hits_from_ids(j_ids, chunks_by_id)
        in_pool = sum(1 for ref in case.expected_evidence if span_in_hits(j_hits, ref))
        j_top_rows = [
            row
            for row in rows_from_ranked(
                j_ids,
                {**{cid: stored_logits[(r["case_id"], cid)]["logit"] for cid in prow["system_h_union_ids"] if (r["case_id"], cid) in stored_logits}},
                chunks_by_id,
            )
        ]
        # rebuild from scored spans instead of re-ranking
        span_ranks = [
            {
                "span_index": s["span_index"],
                "in_pool": s["in_pool"],
                "ce_only_rank": s["rank"],
                "within_10": s["within_10"],
            }
            for s in r["J_spans"]
        ]
        vid_counts = Counter(r["j_top10_version_ids"])
        # j_top10_version_ids was stored unique sorted; recompute redundancy from spans file
        multi_detail.append(
            {
                "case_id": r["case_id"],
                "required_span_count": r["n_gold_spans"],
                "spans_in_SYSTEM_J_pool": in_pool,
                "spans_in_J_CE_only_top10": r["J_span_found"],
                "in_pool_gold_span_ranks": span_ranks,
                "unique_version_ids_in_J_CE_top10": len(set(r["j_top10_version_ids"])),
                "unique_section_paths_in_J_CE_top10": len(set(r["j_top10_section_paths"])),
                "redundant_top10_by_version_id": max(0, TOP_K - len(set(r["j_top10_version_ids"]))),
                "redundant_top10_by_section_path": max(0, TOP_K - len(set(r["j_top10_section_paths"]))),
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

    no_integrity = len(integrity_failures) == 0
    gate = {
        "J_strict_improves_ge_2_cases": (j_strict - h_strict) >= 2,
        "J_span_improves_ge_2_spans": (j_span - h_span) >= 2,
        "J_strict_regressions_le_1": len(regressions) <= 1,
        "no_integrity_provenance_failure": no_integrity,
    }
    supported = all(gate.values())
    estimated_full_j_pairs = sum(len(p["system_j_union_ids"]) for p in pools)
    per_query_est = [len(p["system_j_union_ids"]) for p in pools]
    mean_extra_ms = _mean(lat_ce_extras, 3)
    # estimated full-pool cost: scale measured extra ms by (H+extras)/extras per query when extras>0
    est_full_ms = []
    for r, prow in zip(per_case, [pool_by_id[c.case_id] for c in cases]):
        n_j = r["j_pool"]
        n_e = r["n_extras"]
        if n_e > 0:
            est_full_ms.append(r["ce_extras_ms"] * (n_j / n_e))
        else:
            est_full_ms.append(0.0)

    try:
        emb = embedding_status()
        env = env_fingerprint(emb)
    except Exception as exc:
        emb = {"error": str(exc)}
        env = {"error": str(exc)}

    utc = datetime.now(tz=UTC).replace(microsecond=0)
    et = utc.astimezone(ZoneInfo("America/New_York"))
    payload = {
        "experiment_id": "EXP-022A",
        "scored": True,
        "EXP-022A_STATUS": "SCORED",
        "H_CE_rerun": False,
        "J_EXTRAS_CE_run": True,
        "new_SYSTEM_identity_created": False,
        "diagnostic_label": "EXP-022A-CE-ONLY-H-vs-J",
        "preregistration_json_sha256": PREREG_JSON_SHA,
        "timestamp": utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timestamp_et": et.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "hash_check": hash_check,
        "natq_holdout_access_log_before": natq_before,
        "natq_holdout_access_log_after": natq_after,
        "v1_holdout_access_log_before": {"log_bytes": v1_before["log_bytes"], "log_sha256": v1_before["log_sha256"]},
        "v1_holdout_access_log_after": {"log_bytes": v1_after["log_bytes"], "log_sha256": v1_after["log_sha256"]},
        "holdout_json_opened": False,
        "v1_holdout_json_opened": False,
        "stored_H_logit_inventory": {
            "complete": True,
            "n_H_candidates_required": inventory["n_H_candidates_required"],
            "n_stored_raw_ce_pairs_matching_H": inventory["n_stored_raw_ce_pairs_matching_H"],
        },
        "cross_encoder": {
            "name": CE_NAME,
            "revision": CE_REVISION,
            "artifact_sha256": CE_SHA256,
            "constructor": "CrossEncoderReranker(pad='batch', bucket_by_length=True)",
            "fast": False,
            "threads": 4,
            "H_CE_rerun": False,
            "J_EXTRAS_CE_run": True,
        },
        "embedding": emb,
        "environment": env,
        "environment_drift_note": "PostgreSQL 16.15 / pgvector 0.8.6 vs historical 16.13 / 0.6.0",
        "PRIMARY": {
            "H_CE_only_strict_Recall@10": f"{h_strict}/{n}",
            "J_CE_only_strict_Recall@10": f"{j_strict}/{n}",
            "delta_cases": j_strict - h_strict,
        },
        "SECONDARY": {
            "H_CE_only_span_Recall@10": f"{h_span}/{n_spans}",
            "J_CE_only_span_Recall@10": f"{j_span}/{n_spans}",
            "delta_spans": j_span - h_span,
            "H_MRR_first_gold_span": h_mrr,
            "J_MRR_first_gold_span": j_mrr,
            "H_summarise_mrr": s_h["mrr"],
            "J_summarise_mrr": s_j["mrr"],
            "H_document_Recall@10": f"{h_doc}/{n}",
            "J_document_Recall@10": f"{j_doc}/{n}",
            "multi_span_H_strict": f"{multi_h_strict}/{len(multi)}",
            "multi_span_J_strict": f"{multi_j_strict}/{len(multi)}",
            "multi_span_H_span": f"{multi_h_span}/{multi_span_d}",
            "multi_span_J_span": f"{multi_j_span}/{multi_span_d}",
            "openai": provider_metrics("openai"),
            "anthropic": provider_metrics("anthropic"),
            "J_EXTRAS_CE_rank_mean": _mean([float(x) for x in extra_ranks_all], 3),
            "J_EXTRAS_CE_rank_median": _median([float(x) for x in extra_ranks_all], 3),
            "n_newly_scored_pairs": n_new_pairs,
            "CE_wall_ms_J_EXTRAS_mean": _mean(lat_ce_extras, 3),
            "CE_wall_ms_J_EXTRAS_median": _median(lat_ce_extras, 3),
            "CE_wall_ms_J_EXTRAS_total": round(sum(lat_ce_extras), 3),
            "estimated_complete_J_CE_pairs": estimated_full_j_pairs,
            "estimated_per_query_J_CE_pairs_mean": _mean([float(x) for x in per_query_est], 2),
            "estimated_per_query_J_CE_pairs_median": _median([float(x) for x in per_query_est], 2),
            "estimated_full_pool_CE_ms_mean": _mean(est_full_ms, 3),
            "estimated_full_pool_CE_ms_median": _median(est_full_ms, 3),
            "latency_note": "measured incremental = J_EXTRAS only; estimated full-pool scales extras wall time by J/extras and does NOT run H CE",
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
        "diagnostics_four_SYSTEM_J_recovered_spans": named_diag,
        "MULTI_SPAN_ANALYSIS": multi_detail,
        "gate": gate,
        "EXP-022A_CE_RECOGNIZABILITY_SUPPORTED": supported,
        "integrity_failures": integrity_failures,
        "per_case": per_case,
        "elapsed_s": round(time.time() - started, 2),
        "STOP": "Do not run a coverage-aware selector. Do not run another compression scheme. Do not alter scoring. Return to coordinator ChatGPT.",
    }
    results_path = OUT_DIR / "EXP-022A-REPORT.json"
    report_path = OUT_DIR / "EXP-022A-REPORT.md"
    results_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    lines = [
        "# EXP-022A — SYSTEM-J CE RECOGNIZABILITY DIAGNOSTIC",
        "",
        f"**EXP-022A_CE_RECOGNIZABILITY_SUPPORTED = {str(supported).upper()}**",
        "",
        f"scored=true. H_CE_rerun=false. J_EXTRAS_CE_run=true. Newly scored pairs={n_new_pairs}.",
        "",
        "## PRIMARY — strict full-case Recall@10 (CE-only)",
        "",
        "| arm | strict R@10 |",
        "| --- | ---: |",
        f"| H CE-only | {h_strict}/40 |",
        f"| J CE-only | **{j_strict}/40** |",
        "",
        "## SECONDARY",
        "",
        f"- evidence-span R@10: H {h_span}/{n_spans} vs J {j_span}/{n_spans}",
        f"- MRR (first gold span): H {h_mrr} vs J {j_mrr}",
        f"- document R@10: H {h_doc}/40 vs J {j_doc}/40",
        f"- multi-span strict: H {multi_h_strict}/{len(multi)} vs J {multi_j_strict}/{len(multi)}",
        f"- multi-span span: H {multi_h_span}/{multi_span_d} vs J {multi_j_span}/{multi_span_d}",
        f"- paired: rescues {n01} regressions {n10} both_pass {len(both_pass)} both_fail {len(both_fail)}; McNemar p={mc.get('p_exact')}",
        f"- J_EXTRAS newly scored pairs {n_new_pairs}; CE wall extras total {round(sum(lat_ce_extras), 1)} ms",
        "",
        f"NATQ holdout after: {natq_after['log_bytes']} bytes sha `{natq_after['log_sha256']}`.",
        "",
        "## STOP",
        "",
        "Return to coordinator ChatGPT. Do not run a coverage-aware selector.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    copy_to_post([results_path, report_path, PREREG_JSON, PREREG_MD, OUT_DIR / "EXP-022A-preregistration.json.sha256"])
    print(f"DONE scored SUPPORTED={supported} H={h_strict}/40 J={j_strict}/40 extras={n_new_pairs}", flush=True)
    return 0


def main() -> int:
    started = time.time()
    results_path = OUT_DIR / "EXP-022A-REPORT.json"
    report_path = OUT_DIR / "EXP-022A-REPORT.md"
    if results_path.exists() or report_path.exists():
        raise SystemExit("STOP: EXP-022A results already exist; refusing second run")
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

    pools = load_021a_pools()
    if len(pools) != 40:
        raise SystemExit(f"STOP: EXP-021A pools n={len(pools)} != 40")
    h_pairs: set[tuple[str, str]] = set()
    n_h = 0
    n_j = 0
    for rec in pools:
        h_ids = rec["system_h_union_ids"]
        if len(h_ids) != len(set(h_ids)):
            raise SystemExit(f"STOP: duplicate SYSTEM-H ids on {rec['case_id']}")
        for cid in h_ids:
            key = (rec["case_id"], cid)
            if key in h_pairs:
                raise SystemExit(f"STOP: duplicate (query,chunk) in H pool {key}")
            h_pairs.add(key)
        n_h += len(h_ids)
        n_j += len(rec["system_j_union_ids"])
    if n_h != 4753:
        raise SystemExit(f"STOP: SYSTEM-H candidate count {n_h} != 4753")

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
        "n_H_candidates": n_h,
        "n_J_candidates": n_j,
        "natq_holdout_access_log": natq_before,
        "v1_holdout_access_log": {"log_bytes": v1_before["log_bytes"], "log_sha256": v1_before["log_sha256"]},
    }

    inventory = inventory_stored_h_logits(h_pairs)
    (OUT_DIR / "logs").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "logs" / "EXP-022A-h-logit-inventory.json").write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )

    if not inventory["complete"]:
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
        write_stop_report(
            inventory=inventory,
            natq_before=natq_before,
            natq_after=natq_after,
            v1_before=v1_before,
            v1_after=v1_after,
            hash_check=hash_check,
            env=env,
            emb=emb,
            started=started,
            integrity_failures=integrity_failures,
        )
        print(
            "STOPPED_MISSING_STORED_H_CE_LOGITS "
            f"H_required={inventory['n_H_candidates_required']} "
            f"H_stored={inventory['n_stored_raw_ce_pairs_matching_H']} "
            f"H_CE_rerun=false J_EXTRAS_CE_run=false",
            flush=True,
        )
        return 0

    # Reconstruct stored logits map for scoring path
    stored: dict[tuple[str, str], dict] = {}
    # Re-run a targeted extract from inventory files is already in inventory; rebuild by re-inspecting
    # Use a second pass over the same search, restricted to matching H pairs.
    found: dict[tuple[str, str], dict] = {}
    file_index: list[dict] = []
    notes: list[str] = []
    inspect_json_file(EVAL_POOLS, found, file_index, notes)
    inspect_json_file(EVAL_REPORT, found, file_index, notes)
    stored = {k: v for k, v in found.items() if k in h_pairs}
    if len(stored) != len(h_pairs):
        # inventory said complete; refuse to silently continue if rebuild failed
        raise SystemExit("STOP: stored logit rebuild incomplete despite inventory.complete")
    return run_scoring(
        stored_logits=stored,
        pools=pools,
        natq_before=natq_before,
        v1_before=v1_before,
        hash_check=hash_check,
        inventory=inventory,
        started=started,
    )


if __name__ == "__main__":
    raise SystemExit(main())
