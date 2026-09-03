#!/usr/bin/env python3
"""PERF-003: D1 on V2 SYSTEM-G development path. Score-preserving only.

Preregistration MUST already be hashed. Does not open gold150-v1 holdout.json.
Does not load validation. Does not overwrite SYSTEM-G. Does not use fast=True.
Does not change CrossEncoderReranker default kwargs. Does not rerun retrieval.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-015" / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-018" / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "PERF-003" / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-017" / "scripts"))

from tokenizers import Tokenizer  # noqa: E402

from cross_encoder import (  # noqa: E402
    CE_NAME,
    CE_ONNX,
    CE_REVISION,
    CE_SHA256,
    CE_TOKENIZER,
    MAX_LENGTH,
    CrossEncoderReranker,
)
from rag_v1.evals.io import load_cases  # noqa: E402
from rag_v1.ids import config_hash  # noqa: E402

from run_exp017 import load_control_chunks  # noqa: E402
from system_e import (  # noqa: E402
    BLEND_A,
    BLEND_CE,
    HOLD_LOCK_SHA,
    HOLD_LOG_SHA_AT_PREREG,
    MINMAX_DEGENERATE,
    TOP_K,
    covering_chunk_ids,
    embedding_status,
    holdout_log_state,
    minmax_norm,
)
from v2_system_g_ce import make_v2_system_g_d1_reranker  # noqa: E402

OUT_DIR = ROOT / "experiments" / "PERF-003"
GOLD_JSONL = ROOT / "evals" / "gold" / "v2-devset-001.jsonl"
SPLIT_PATH = ROOT / "evals" / "splits" / "v2-devset-001" / "development.json"
G_FILE = ROOT / "experiments" / "EXP-019A" / "SYSTEM-G-PROJECTION-PRIOR.json"
RECOVERED = ROOT / "experiments" / "EXP-019A" / "EXP-019A-recovered-union.jsonl"
PREREG_JSON = OUT_DIR / "PERF-003-preregistration.json"
PREREG_MD = OUT_DIR / "PERF-003-preregistration.md"
FRESH_LOGITS = OUT_DIR / "logs" / "PERF-003-fresh-logits.jsonl"
MAIN_LOGITS = OUT_DIR / "logs" / "PERF-003-main-logits.jsonl"

PREREG_JSON_SHA = "dc01713eafc56347a9eba0711d0947f13fccbc8ba784dfa034e22280ec23c880"
G_CONFIG_HASH = "563a7b790564fa1efb96257e988c4b1ccfab45146825d2a366b2fee0ca5d5790"
G_FILE_SHA = "7f4ff6db09f32e55cac820cbc00d87ce2ae91886d444c3bad20ac3e04c7f0f61"
GOLD_SHA = "cb687f3cc88b38d4beed7ad4bc829296a30518aaaf45cce0677ec568b1bf77e5"
SPLIT_SHA = "6b0c49c9040c215fde6134697c35a1f28458ba7d72ef012c0840feb7f9c3eb17"
CE_ONNX_SHA = "5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a"
STORED_NON_CE_MS = 1011.4
BATCH_SIZE = 16
HOLD_LOG_EXPECTED = "45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32_equal(a, b) -> bool:
    x = np.asarray(a, dtype=np.float32).reshape(-1)
    y = np.asarray(b, dtype=np.float32).reshape(-1)
    return x.shape == y.shape and bool(np.array_equal(x.view(np.uint32), y.view(np.uint32)))


def f64_equal(a, b) -> bool:
    x = np.asarray(a, dtype=np.float64).reshape(-1)
    y = np.asarray(b, dtype=np.float64).reshape(-1)
    return x.shape == y.shape and bool(np.array_equal(x.view(np.uint64), y.view(np.uint64)))


def f32_hex(arr) -> str:
    return np.asarray(arr, dtype=np.float32).reshape(-1).tobytes().hex()


def hex_to_f32(h: str) -> np.ndarray:
    return np.frombuffer(bytes.fromhex(h), dtype=np.float32)


def make_raw_tokenizer():
    raw = Tokenizer.from_file(str(CE_TOKENIZER))
    raw.enable_truncation(max_length=MAX_LENGTH, strategy="longest_first")
    return raw


def semantic_ids_from_encodings(encodings) -> list[list[int]]:
    out = []
    for e in encodings:
        ids = list(e.ids)
        mask = list(e.attention_mask)
        out.append([i for i, m in zip(ids, mask) if m])
    return out


def semantic_ids_raw(raw_tok, query: str, passages: list[str]) -> list[list[int]]:
    enc = raw_tok.encode_batch([(query, p) for p in passages])
    return [list(e.ids) for e in enc]


def score_profiled(ce: CrossEncoderReranker, query: str, passages: list[str], batch_size: int = BATCH_SIZE) -> dict:
    """Mirror CrossEncoderReranker.score_pairs with stage timers and float32 logits."""
    t_all = time.perf_counter()
    tok_ms = 0.0
    bucket_ms = 0.0
    numpy_ms = 0.0
    onnx_ms = 0.0
    unperm_ms = 0.0
    n = len(passages)
    if not passages:
        return {
            "scores": [],
            "logits_f32": np.array([], dtype=np.float32),
            "order": [],
            "batch_widths": [],
            "timing": {
                "tokenization_ms": 0.0,
                "bucketing_ms": 0.0,
                "numpy_prep_ms": 0.0,
                "onnx_ms": 0.0,
                "unpermute_ms": 0.0,
                "ce_total_ms": 0.0,
            },
        }

    if ce.bucket_by_length:
        t0 = time.perf_counter()
        raw = ce._raw_tokenizer.encode_batch([(query, p) for p in passages])
        order = sorted(range(n), key=lambda i: (len(raw[i].ids), i))
        work = [passages[i] for i in order]
        bucket_ms += (time.perf_counter() - t0) * 1000
    else:
        order = list(range(n))
        work = passages

    scores_work: list[float] = []
    logit_parts: list[np.ndarray] = []
    batch_widths: list[int] = []
    for start in range(0, len(work), batch_size):
        batch = work[start : start + batch_size]
        t0 = time.perf_counter()
        encodings = ce._tokenizer.encode_batch([(query, p) for p in batch])
        tok_ms += (time.perf_counter() - t0) * 1000
        t1 = time.perf_counter()
        ids = np.array([e.ids for e in encodings], dtype=np.int64)
        mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
        types = np.array([e.type_ids for e in encodings], dtype=np.int64)
        feeds = {"input_ids": ids, "attention_mask": mask}
        if "token_type_ids" in ce._input_names:
            feeds["token_type_ids"] = types
        numpy_ms += (time.perf_counter() - t1) * 1000
        batch_widths.append(int(ids.shape[1]))
        t2 = time.perf_counter()
        logits = ce._session.run(None, feeds)[0]
        onnx_ms += (time.perf_counter() - t2) * 1000
        flat = np.asarray(logits, dtype=np.float32).reshape(-1)
        logit_parts.append(flat.copy())
        scores_work.extend(float(v) for v in flat)

    t3 = time.perf_counter()
    raw_np = np.concatenate(logit_parts) if logit_parts else np.array([], dtype=np.float32)
    out_scores = [0.0] * n
    out_np = np.empty(n, dtype=np.float32)
    for new_i, orig_i in enumerate(order):
        out_scores[orig_i] = scores_work[new_i]
        out_np[orig_i] = raw_np[new_i]
    unperm_ms += (time.perf_counter() - t3) * 1000
    total_ms = (time.perf_counter() - t_all) * 1000
    return {
        "scores": out_scores,
        "logits_f32": out_np,
        "order": order,
        "batch_widths": batch_widths,
        "timing": {
            "tokenization_ms": round(tok_ms, 4),
            "bucketing_ms": round(bucket_ms, 4),
            "numpy_prep_ms": round(numpy_ms, 4),
            "onnx_ms": round(onnx_ms, 4),
            "unpermute_ms": round(unperm_ms, 4),
            "ce_total_ms": round(total_ms, 4),
        },
    }


def apply_system_g_blend(members: list[dict], ce_by_id: dict[str, float]) -> list[dict]:
    """SYSTEM-G / EXP-019A blend. Recovered extras still carry EXP-017 a_norm=0.0;
    projection-only retrieval_norm is minmax(projection_fused) over P extras.
    E-L10 a_norm is kept. CE minmax is over the live union logits.
    """
    scores = [float(ce_by_id[m["chunk_id"]]) for m in members]
    norms = minmax_norm(scores)
    e_rows: list[dict] = []
    extras: list[dict] = []
    for m, sc, cn in zip(members, scores, norms, strict=True):
        item = dict(m)
        item["ce_score"] = sc
        item["ce_norm"] = cn
        if item.get("in_e_l10"):
            e_rows.append(item)
        else:
            extras.append(item)
    proj_norms = minmax_norm([float(r["projection_fused"]) for r in extras])
    out: list[dict] = []
    for r in e_rows:
        r["retrieval_norm"] = float(r["a_norm"])
        r["blend_score"] = BLEND_CE * float(r["ce_norm"]) + BLEND_A * float(r["retrieval_norm"])
        out.append(r)
    for r, pn in zip(extras, proj_norms, strict=True):
        r["a_norm"] = float(pn)
        r["retrieval_norm"] = float(pn)
        r["blend_score"] = BLEND_CE * float(r["ce_norm"]) + BLEND_A * float(r["retrieval_norm"])
        out.append(r)
    out.sort(key=lambda r: (-r["blend_score"], r["a_rank"], r["chunk_id"]))
    for i, r in enumerate(out, start=1):
        r["blend_rank"] = i
    return out


def dict_overlaps(row: dict, ref) -> bool:
    return (
        row["version_id"] == ref.version_id
        and list(row["section_path"]) == list(ref.section_path)
        and row["char_start"] < ref.char_end
        and row["char_end"] > ref.char_start
    )


def span_in_hits(hits, ref) -> bool:
    for h in hits:
        if dict_overlaps(h, ref):
            return True
    return False


def first_span_rank(rows: list[dict], ref, rank_key: str):
    ranks = [r[rank_key] for r in rows if dict_overlaps(r, ref) and r.get(rank_key) is not None]
    return min(ranks) if ranks else None


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
            }
        )
    found = sum(1 for s in spans if s["within_10"])
    return {
        "case_id": case.case_id,
        "spans": spans,
        "recall": found / len(spans) if spans else 1.0,
        "fully_recalled": bool(spans) and found == len(spans),
        "doc_recall": (len(gold_docs & top_docs) / len(gold_docs)) if gold_docs else 1.0,
        "cand_ev_span_flags": [s["in_pool"] for s in spans],
    }


def summarise(per_case: dict) -> dict:
    all_spans = [s for c in per_case.values() for s in c["spans"]]
    recalls = [c["recall"] for c in per_case.values()]
    cand_flags = [flag for c in per_case.values() for flag in c["cand_ev_span_flags"]]
    return {
        "macro_span_recall": round(sum(recalls) / len(recalls), 4) if recalls else 0.0,
        "cases_fully_recalled": sum(1 for c in per_case.values() if c["fully_recalled"]),
        "cases_total": len(per_case),
        "strict_recall_at_10": f"{sum(1 for c in per_case.values() if c['fully_recalled'])}/{len(per_case)}",
        "spans_found_at_10": sum(1 for s in all_spans if s["within_10"]),
        "spans_total": len(all_spans),
        "document_recall": round(sum(c["doc_recall"] for c in per_case.values()) / len(per_case), 4)
        if per_case
        else 0.0,
        "mrr": round(
            sum((1 / s["rank"] for s in all_spans if s["rank"]), 0.0) / len(all_spans),
            4,
        )
        if all_spans
        else 0.0,
        "candidate_evidence_spans": f"{sum(cand_flags)}/{len(cand_flags)}",
        "candidate_evidence_n": sum(cand_flags),
        "candidate_evidence_d": len(cand_flags),
    }


def stage_stats(rows: list[dict], key: str) -> dict:
    xs = [r[key] for r in rows]
    return {
        "mean": round(statistics.mean(xs), 4) if xs else None,
        "median": round(statistics.median(xs), 4) if xs else None,
        "n": len(xs),
    }


def assert_class_defaults_frozen() -> dict:
    sig = inspect.signature(CrossEncoderReranker.__init__)
    params = sig.parameters
    observed = {
        "threads": params["threads"].default,
        "pad": params["pad"].default,
        "pad_to_multiple_of": params["pad_to_multiple_of"].default,
        "bucket_by_length": params["bucket_by_length"].default,
        "fast": params["fast"].default,
    }
    expected = {
        "threads": 4,
        "pad": "fixed",
        "pad_to_multiple_of": None,
        "bucket_by_length": False,
        "fast": False,
    }
    if observed != expected:
        raise SystemExit(f"STOP: CrossEncoderReranker defaults changed: {observed}")
    return observed


def cpu_provenance() -> dict:
    model = "unknown"
    flags = None
    try:
        txt = Path("/proc/cpuinfo").read_text(encoding="utf-8")
        for line in txt.splitlines():
            if line.lower().startswith("model name") and model == "unknown":
                model = line.split(":", 1)[1].strip()
            if line.lower().startswith("flags") and flags is None:
                flags = line.split(":", 1)[1].strip()[:200]
    except OSError:
        pass
    return {
        "model": model,
        "cpu_count": os.cpu_count(),
        "family_model_note": "Intel family 6 model 207, 8 cores, KVM; lscpu Model name=Intel(R) Xeon(R) Processor",
    }


def load_recovered() -> list[dict]:
    rows = []
    with RECOVERED.open(encoding="utf-8") as fh:
        for line in fh:
            rows.append(json.loads(line))
    if len(rows) != 50:
        raise SystemExit(f"STOP: recovered union n={len(rows)} != 50")
    return rows


def load_workload(chunks_by_id: dict, recovered: list[dict], cases_by_id: dict) -> list[dict]:
    out = []
    for rec in recovered:
        cid = rec["case_id"]
        case = cases_by_id[cid]
        members = rec["members"]
        texts = []
        for m in members:
            ch = chunks_by_id.get(m["chunk_id"])
            if ch is None or not ch.get("text"):
                raise SystemExit(f"STOP: missing text for {cid} {m['chunk_id']}")
            texts.append(ch["text"])
        out.append(
            {
                "case_id": cid,
                "query": case.question,
                "members": members,
                "texts": texts,
                "chunk_ids": [m["chunk_id"] for m in members],
            }
        )
    return out


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def score_workload(ce_old, ce_new, workload, raw_tok, repeat: bool) -> dict:
    per = []
    tok_ok = True
    trunc_ok = True
    logits_ok = True
    assoc_ok = True
    inproc_old_ok = True
    inproc_new_ok = True
    profiler_ok = True
    n_pairs = 0
    n_logit_mismatch = 0
    max_abs = 0.0

    probe_q, probe_p = "What is BM25?", ["BM25 is a lexical ranking function."]
    probe_old = ce_old.score_pairs(probe_q, probe_p)
    probe_new = ce_new.score_pairs(probe_q, probe_p)
    probe_old2 = ce_old.score_pairs(probe_q, probe_p)
    probe_new2 = ce_new.score_pairs(probe_q, probe_p)
    if probe_old[0] != probe_old2[0] or probe_new[0] != probe_new2[0]:
        inproc_old_ok = inproc_new_ok = False
    p_old = score_profiled(ce_old, probe_q, probe_p)
    p_new = score_profiled(ce_new, probe_q, probe_p)
    if p_old["scores"][0] != probe_old[0] or p_new["scores"][0] != probe_new[0]:
        profiler_ok = False

    for i, w in enumerate(workload, start=1):
        q = w["query"]
        texts = w["texts"]
        ids = w["chunk_ids"]
        n_pairs += len(texts)

        sem_raw = semantic_ids_raw(raw_tok, q, texts)
        enc_old = ce_old._tokenizer.encode_batch([(q, p) for p in texts])
        enc_new = ce_new._tokenizer.encode_batch([(q, p) for p in texts])
        sem_old = semantic_ids_from_encodings(enc_old)
        sem_new = semantic_ids_from_encodings(enc_new)
        if sem_raw != sem_old or sem_raw != sem_new:
            tok_ok = False
        if any(len(a) != len(b) or (len(a) > MAX_LENGTH) for a, b in zip(sem_raw, sem_old)):
            trunc_ok = False
        if any(len(s) > MAX_LENGTH for s in sem_raw):
            trunc_ok = False
        # truncation identical: same semantic ids already implies same truncated sequence

        old1 = score_profiled(ce_old, q, texts)
        new1 = score_profiled(ce_new, q, texts)
        if i == 1:
            cls_old = ce_old.score_pairs(q, texts, batch_size=BATCH_SIZE)
            cls_new = ce_new.score_pairs(q, texts, batch_size=BATCH_SIZE)
            if cls_old != old1["scores"] or cls_new != new1["scores"]:
                profiler_ok = False

        if not f32_equal(old1["logits_f32"], new1["logits_f32"]):
            logits_ok = False
            n_logit_mismatch += int(
                np.sum(
                    np.asarray(old1["logits_f32"]).view(np.uint32)
                    != np.asarray(new1["logits_f32"]).view(np.uint32)
                )
            )
        if old1["logits_f32"].size:
            max_abs = max(
                max_abs,
                float(np.max(np.abs(old1["logits_f32"].astype(np.float64) - new1["logits_f32"].astype(np.float64)))),
            )
        if [ids[j] for j in range(len(ids))] != ids:
            assoc_ok = False
        # unpermuted association: scores[j] belongs to texts[j]/ids[j]
        if len(old1["scores"]) != len(ids) or len(new1["scores"]) != len(ids):
            assoc_ok = False

        old2 = new2 = None
        if repeat:
            old2 = score_profiled(ce_old, q, texts)
            new2 = score_profiled(ce_new, q, texts)
            if not f32_equal(old1["logits_f32"], old2["logits_f32"]):
                inproc_old_ok = False
            if not f32_equal(new1["logits_f32"], new2["logits_f32"]):
                inproc_new_ok = False

        per.append(
            {
                "case_id": w["case_id"],
                "n": len(texts),
                "chunk_ids": ids,
                "old_logits_hex": f32_hex(old1["logits_f32"]),
                "new_logits_hex": f32_hex(new1["logits_f32"]),
                "old_scores": old1["scores"],
                "new_scores": new1["scores"],
                "old_timing": old1["timing"],
                "new_timing": new1["timing"],
                "old_batch_widths": old1["batch_widths"],
                "new_batch_widths": new1["batch_widths"],
                "semantic_ids_match": sem_raw == sem_old == sem_new,
                "n_truncated_512": sum(1 for s in sem_raw if len(s) >= MAX_LENGTH),
                "unpadded_len_mean": float(np.mean([len(s) for s in sem_raw])) if sem_raw else 0.0,
            }
        )
        print(
            f"{w['case_id']} n={len(texts)} old_ce={old1['timing']['ce_total_ms']:.1f}ms "
            f"new_ce={new1['timing']['ce_total_ms']:.1f}ms "
            f"logits_eq={f32_equal(old1['logits_f32'], new1['logits_f32'])} "
            f"widths_new={new1['batch_widths']}",
            flush=True,
        )

    return {
        "per": per,
        "tok_ok": tok_ok,
        "trunc_ok": trunc_ok,
        "logits_ok": logits_ok,
        "assoc_ok": assoc_ok,
        "inproc_old_ok": inproc_old_ok,
        "inproc_new_ok": inproc_new_ok,
        "profiler_ok": profiler_ok,
        "n_pairs": n_pairs,
        "n_logit_mismatch": n_logit_mismatch,
        "max_abs_diff": max_abs,
        "probe": {"old": probe_old, "new": probe_new},
    }


def blend_and_metrics(workload, per, cases_by_id, gold_cover):
    membership_ok = True
    ce_norm_ok = True
    blend_ok = True
    rank_ok = True
    old_cases = {}
    new_cases = {}
    cand_flags_old = []
    details = []
    for w, p in zip(workload, per, strict=True):
        members = w["members"]
        ids = w["chunk_ids"]
        if set(ids) != {m["chunk_id"] for m in members} or ids != [m["chunk_id"] for m in members]:
            membership_ok = False
        old_map = {cid: sc for cid, sc in zip(ids, p["old_scores"], strict=True)}
        new_map = {cid: sc for cid, sc in zip(ids, p["new_scores"], strict=True)}
        old_rows = apply_system_g_blend(members, old_map)
        new_rows = apply_system_g_blend(members, new_map)
        old_by = {r["chunk_id"]: r for r in old_rows}
        new_by = {r["chunk_id"]: r for r in new_rows}
        for cid in ids:
            if not f64_equal(old_by[cid]["ce_norm"], new_by[cid]["ce_norm"]):
                ce_norm_ok = False
            if not f64_equal(old_by[cid]["blend_score"], new_by[cid]["blend_score"]):
                blend_ok = False
        old_rank = [r["chunk_id"] for r in old_rows]
        new_rank = [r["chunk_id"] for r in new_rows]
        if old_rank != new_rank:
            rank_ok = False
        case = cases_by_id[w["case_id"]]
        old_sc = score_system(case, old_rows, "blend_rank", old_rows, gold_cover)
        new_sc = score_system(case, new_rows, "blend_rank", new_rows, gold_cover)
        old_cases[w["case_id"]] = old_sc
        new_cases[w["case_id"]] = new_sc
        cand_flags_old.extend(old_sc["cand_ev_span_flags"])
        details.append(
            {
                "case_id": w["case_id"],
                "rank_identical": old_rank == new_rank,
                "old_top10": old_rank[:10],
                "new_top10": new_rank[:10],
                "old_strict": old_sc["fully_recalled"],
                "new_strict": new_sc["fully_recalled"],
            }
        )
    old_m = summarise(old_cases)
    new_m = summarise(new_cases)
    return {
        "membership_ok": membership_ok,
        "ce_norm_ok": ce_norm_ok,
        "blend_ok": blend_ok,
        "rank_ok": rank_ok,
        "old_metrics": old_m,
        "new_metrics": new_m,
        "details": details,
    }


def build_d1_artifact(g_obj: dict, d1_hash: str, metrics: dict, provenance: dict) -> dict:
    cfg = dict(g_obj["config"])
    cfg["name"] = "SYSTEM-G-CE-D1"
    cfg["parent_system_g"] = G_CONFIG_HASH
    cfg["ce_constructor"] = "CrossEncoderReranker(pad='batch', bucket_by_length=True)  # D1; not fast=True; threads default 4"
    cfg["ce_padding"] = "batch"
    cfg["ce_bucket_by_length"] = True
    cfg["ce_bucket_rule"] = "sort by unpadded token length then original index; unpermute logits to original order"
    cfg["ce_fast"] = False
    cfg["ce_threads"] = 4
    cfg["ce_intra_op_num_threads"] = 4
    cfg["ce_inter_op_num_threads"] = 1
    cfg["one_change_from_G"] = "D1 CE padding/bucketing only; ranking semantics identical to SYSTEM-G"
    cfg_h = config_hash(cfg)
    art = {
        "name": "SYSTEM-G-CE-D1",
        "status": "DEVELOPMENT",
        "kind": "engineering_performance_artifact",
        "release_freeze": False,
        "independently_validated": False,
        "validation_run": False,
        "holdout_run": False,
        "NOT_FROZEN": True,
        "NOT_independently_validated": True,
        "parent_SYSTEM_G_config_hash": G_CONFIG_HASH,
        "does_not_overwrite_SYSTEM_G": True,
        "quality_system_label_unchanged": True,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_at_et": datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%dT%H:%M:%S%z"),
        "config": cfg,
        "config_hash": cfg_h,
        "cross_encoder": {
            "name": CE_NAME,
            "revision": CE_REVISION,
            "artifact": str(CE_ONNX),
            "artifact_sha256": CE_ONNX_SHA,
            "constructor": "CrossEncoderReranker(pad='batch', bucket_by_length=True)",
            "fast": False,
            "threads": 4,
            "intra_op_num_threads": 4,
            "inter_op_num_threads": 1,
            "pad": "batch",
            "bucket_by_length": True,
            "bucket_rule": "sort by unpadded token length then original index",
            "max_length": 512,
            "truncation": "longest_first",
            "batch_size": 16,
            "provider": "CPUExecutionProvider",
        },
        "observed_metrics_DEVELOPMENT_ONLY": metrics,
        "provenance": provenance,
        "note": "Score-preserving D1 performance variant of SYSTEM-G. Not a quality-system promotion. Does not overwrite SYSTEM-G-PROJECTION-PRIOR.",
    }
    return art


def write_report(path: Path, payload: dict) -> None:
    eq = payload["equivalence"]
    dec = payload["decision"]
    tim = payload.get("timing") or {}
    lines = [
        "# PERF-003 — V2 CROSS-ENCODER D1 DYNAMIC PADDING",
        "",
        f"Written {payload['timestamp_et']} ET ({payload['timestamp']} UTC). ChatGPT-authorized PERF-003.",
        "SCORE-PRESERVING PERFORMANCE ENGINEERING ONLY. Did not post to ChatGPT.",
        "",
        f"**Decision: `{dec}`**",
        "",
        f"Prereg JSON sha256 `{payload['preregistration_json_sha256']}`.",
        f"SYSTEM-G config_hash `{G_CONFIG_HASH}` not overwritten.",
        "",
        "## Equivalence gate",
        "",
        f"Pass: **{eq['pass']}**",
        "",
    ]
    for k, v in eq["checks"].items():
        mark = "PASS" if v else "FAIL"
        lines.append(f"- `{k}`: {mark}")
    lines += [
        "",
        "### Metrics (D1 path)",
        "",
        f"- cand R@100: {eq['new_metrics']['candidate_evidence_spans']} (require 46/50)",
        f"- strict R@10: {eq['new_metrics']['strict_recall_at_10']} (require 41/50)",
        f"- span R@10: {eq['new_metrics']['macro_span_recall']} (require 0.82)",
        f"- MRR: {eq['new_metrics']['mrr']} (require 0.6009)",
        f"- document recall: {eq['new_metrics']['document_recall']} (require 0.90)",
        "",
        f"Raw CE logits max abs diff old vs D1: {eq['max_abs_diff']}",
        f"n_pairs: {eq['n_pairs']}; logit mismatches: {eq['n_logit_mismatch']}",
        "",
    ]
    if tim:
        lines += [
            "## Timing (this host only; do not compare ms to another host)",
            "",
            f"CPU: {payload['provenance']['cpu']['model']} n={payload['provenance']['cpu']['cpu_count']}",
            f"ORT {payload['provenance']['ort_version']} provider={payload['provenance']['provider']} intra_op=4 inter_op=1",
            "",
            "| stage | old mean ms | old median ms | D1 mean ms | D1 median ms | speedup |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
        for stage in (
            "tokenization_ms",
            "bucketing_ms",
            "numpy_prep_ms",
            "onnx_ms",
            "unpermute_ms",
            "ce_total_ms",
        ):
            o = tim["old"][stage]
            n = tim["new"][stage]
            sp = round(o["mean"] / n["mean"], 4) if n["mean"] else None
            lines.append(
                f"| {stage} | {o['mean']} | {o['median']} | {n['mean']} | {n['median']} | {sp} |"
            )
        lines += [
            "",
            f"SYSTEM-G total old = stored non-CE 1011.4 + CE {tim['old']['ce_total_ms']['mean']} = **{tim['system_g_total_old_ms']} ms**",
            f"SYSTEM-G total D1 = stored non-CE 1011.4 + CE {tim['new']['ce_total_ms']['mean']} = **{tim['system_g_total_new_ms']} ms**",
            f"CE speedup ratio (old/new): **{tim['ce_speedup']}**",
            f"CE latency improved: **{tim['ce_improved']}**",
            "",
            "Stored non-CE 1011.4 ms is EXP-017 A+local+projection (EXP-019B G-NO-CE). Retrieval was not rerun.",
            "",
        ]
    art = payload.get("artifact")
    if art:
        lines += [
            "## Artifact",
            "",
            f"- path: `{art['path']}`",
            f"- config_hash: `{art['config_hash']}`",
            f"- file sha256: `{art['file_sha256']}`",
            "",
        ]
    lines += [
        "## Provenance",
        "",
        f"- CE ONNX sha256: `{payload['provenance']['ce_sha256']}`",
        f"- tokenizer sha256: `{payload['provenance']['tokenizer_sha256']}`",
        f"- cross_encoder.py sha256: `{payload['provenance']['cross_encoder_py_sha256']}`",
        f"- batch_size: {BATCH_SIZE}",
        f"- old pad: fixed 512; D1 pad: batch; bucket: unpadded length then original index",
        f"- holdout log: {payload['holdout_access_log_after']['log_bytes']} bytes sha `{payload['holdout_access_log_after']['log_sha256']}` unchanged={payload['holdout_log_unchanged']}",
        "",
        "No validation. No holdout.json. No fast=True. No threads=8. No second variant.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_fresh(out_path: Path) -> int:
    got_pre = _sha(PREREG_JSON)
    if got_pre != PREREG_JSON_SHA:
        raise SystemExit(f"STOP: prereg json sha {got_pre} != {PREREG_JSON_SHA}")
    hold = holdout_log_state()
    if hold["log_bytes"] != 235 or hold["log_sha256"] != HOLD_LOG_EXPECTED:
        raise SystemExit(f"STOP: holdout log drifted: {hold}")
    cases = [c for c in load_cases(GOLD_JSONL) if c.expected_evidence]
    cases_by_id = {c.case_id: c for c in cases}
    chunks_by_id = load_control_chunks()
    recovered = load_recovered()
    workload = load_workload(chunks_by_id, recovered, cases_by_id)
    ce_old = CrossEncoderReranker()
    ce_new = make_v2_system_g_d1_reranker()
    raw_tok = make_raw_tokenizer()
    scored = score_workload(ce_old, ce_new, workload, raw_tok, repeat=False)
    with out_path.open("w", encoding="utf-8") as fh:
        for p in scored["per"]:
            fh.write(
                json.dumps(
                    {
                        "case_id": p["case_id"],
                        "n": p["n"],
                        "chunk_ids": p["chunk_ids"],
                        "old_logits_hex": p["old_logits_hex"],
                        "new_logits_hex": p["new_logits_hex"],
                    }
                )
                + "\n"
            )
    print("wrote", out_path, flush=True)
    hold2 = holdout_log_state()
    if hold2["log_sha256"] != HOLD_LOG_EXPECTED:
        raise SystemExit("STOP: holdout log changed during fresh process")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh-out", type=Path, default=None)
    args = ap.parse_args()
    if args.fresh_out is not None:
        return run_fresh(args.fresh_out)

    started = time.time()
    results_path = OUT_DIR / "PERF-003-results.json"
    report_path = OUT_DIR / "PERF-003-report.md"
    artifact_path = OUT_DIR / "SYSTEM-G-CE-D1.json"
    if results_path.exists():
        raise SystemExit("STOP: PERF-003 results already exist; refusing to overwrite")
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
    g_obj = json.loads(G_FILE.read_text(encoding="utf-8"))
    if g_obj["config_hash"] != G_CONFIG_HASH:
        raise SystemExit("STOP: SYSTEM-G config_hash mismatch")
    if _sha(G_FILE) != G_FILE_SHA:
        raise SystemExit("STOP: SYSTEM-G file bytes changed; refusing to continue")
    digest = hashlib.sha256(CE_ONNX.read_bytes()).hexdigest()
    if digest != CE_ONNX_SHA:
        raise SystemExit(f"STOP: CE sha {digest} != {CE_ONNX_SHA}")

    defaults = assert_class_defaults_frozen()
    emb = embedding_status()

    cases = [c for c in load_cases(GOLD_JSONL) if c.expected_evidence]
    if len(cases) != 50:
        raise SystemExit(f"expected 50 cases, got {len(cases)}")
    split_ids = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))["case_ids"]
    if [c.case_id for c in cases] != split_ids:
        raise SystemExit("STOP: split ids mismatch")
    cases_by_id = {c.case_id: c for c in cases}
    gold_cover = {c.case_id: [covering_chunk_ids(ref) for ref in c.expected_evidence] for c in cases}

    chunks_by_id = load_control_chunks()
    recovered = load_recovered()
    workload = load_workload(chunks_by_id, recovered, cases_by_id)

    import onnxruntime as ort

    print("constructing old=CrossEncoderReranker() and D1 wrapper...", flush=True)
    ce_old = CrossEncoderReranker()
    ce_new = make_v2_system_g_d1_reranker()
    if ce_old.fast or ce_old.pad != "fixed" or ce_old.bucket_by_length or ce_old.threads != 4:
        raise SystemExit(f"STOP: old path not defaults: pad={ce_old.pad} fast={ce_old.fast} bucket={ce_old.bucket_by_length} t={ce_old.threads}")
    if ce_new.fast or ce_new.pad != "batch" or not ce_new.bucket_by_length or ce_new.threads != 4:
        raise SystemExit(f"STOP: D1 path wrong: pad={ce_new.pad} fast={ce_new.fast} bucket={ce_new.bucket_by_length} t={ce_new.threads}")
    if ce_old._session.get_providers()[0] != "CPUExecutionProvider":
        raise SystemExit("STOP: unexpected execution provider")

    raw_tok = make_raw_tokenizer()
    print("scoring old vs D1 on 50 SYSTEM-G pools (no retrieval)...", flush=True)
    scored = score_workload(ce_old, ce_new, workload, raw_tok, repeat=True)
    MAIN_LOGITS.parent.mkdir(parents=True, exist_ok=True)
    with MAIN_LOGITS.open("w", encoding="utf-8") as fh:
        for p in scored["per"]:
            fh.write(
                json.dumps(
                    {
                        "case_id": p["case_id"],
                        "n": p["n"],
                        "chunk_ids": p["chunk_ids"],
                        "old_logits_hex": p["old_logits_hex"],
                        "new_logits_hex": p["new_logits_hex"],
                    }
                )
                + "\n"
            )

    print("fresh-process repeat...", flush=True)
    FRESH_LOGITS.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--fresh-out", str(FRESH_LOGITS)],
        cwd=str(ROOT),
        capture_output=False,
        check=False,
    )
    fresh_ok = proc.returncode == 0 and FRESH_LOGITS.exists()
    fresh_old_ok = True
    fresh_new_ok = True
    if fresh_ok:
        main_map = {p["case_id"]: p for p in scored["per"]}
        with FRESH_LOGITS.open(encoding="utf-8") as fh:
            n_fresh = 0
            for line in fh:
                rec = json.loads(line)
                n_fresh += 1
                m = main_map[rec["case_id"]]
                if rec["chunk_ids"] != m["chunk_ids"]:
                    fresh_ok = False
                    fresh_old_ok = False
                    fresh_new_ok = False
                if rec["old_logits_hex"] != m["old_logits_hex"]:
                    fresh_old_ok = False
                    fresh_ok = False
                if rec["new_logits_hex"] != m["new_logits_hex"]:
                    fresh_new_ok = False
                    fresh_ok = False
        if n_fresh != 50:
            fresh_ok = False
    else:
        fresh_old_ok = False
        fresh_new_ok = False

    bm = blend_and_metrics(workload, scored["per"], cases_by_id, gold_cover)
    nm = bm["new_metrics"]
    metrics_ok = (
        nm["candidate_evidence_spans"] == "46/50"
        and nm["strict_recall_at_10"] == "41/50"
        and nm["macro_span_recall"] == 0.82
        and nm["mrr"] == 0.6009
        and nm["document_recall"] == 0.9
    )
    oldm = bm["old_metrics"]
    old_metrics_ok = (
        oldm["candidate_evidence_spans"] == "46/50"
        and oldm["strict_recall_at_10"] == "41/50"
        and oldm["macro_span_recall"] == 0.82
        and oldm["mrr"] == 0.6009
        and oldm["document_recall"] == 0.9
    )

    checks = {
        "1_same_membership": bm["membership_ok"],
        "2_same_semantic_token_ids_before_padding": scored["tok_ok"],
        "3_same_truncation": scored["trunc_ok"] and scored["tok_ok"],
        "4_bitwise_identical_raw_ce_logits": scored["logits_ok"],
        "5_same_unpermuted_candidate_logit_association": scored["assoc_ok"] and scored["logits_ok"],
        "6_same_ce_norm": bm["ce_norm_ok"],
        "7_same_blend_scores_bitwise": bm["blend_ok"],
        "8_same_final_rankings": bm["rank_ok"],
        "9_cand_R100_46_50": nm["candidate_evidence_spans"] == "46/50" and oldm["candidate_evidence_spans"] == "46/50",
        "10_strict_R10_41_50": nm["strict_recall_at_10"] == "41/50" and oldm["strict_recall_at_10"] == "41/50",
        "11_span_0_82": nm["macro_span_recall"] == 0.82 and oldm["macro_span_recall"] == 0.82,
        "12_mrr_0_6009": nm["mrr"] == 0.6009 and oldm["mrr"] == 0.6009,
        "13_doc_recall_0_90": nm["document_recall"] == 0.9 and oldm["document_recall"] == 0.9,
        "14_in_process_deterministic_repeat": scored["inproc_old_ok"] and scored["inproc_new_ok"],
        "15_fresh_process_deterministic_repeat": fresh_ok and fresh_old_ok and fresh_new_ok,
        "profiler_matches_class_score_pairs": scored["profiler_ok"],
        "class_defaults_unchanged": True,
        "old_path_metrics_match_SYSTEM_G": old_metrics_ok,
        "d1_path_metrics_match_SYSTEM_G": metrics_ok,
        "no_fast_true": (not ce_old.fast) and (not ce_new.fast),
        "threads_unchanged_4": ce_old.threads == 4 and ce_new.threads == 4,
    }
    eq_pass = all(checks.values())

    timing = None
    ce_improved = False
    if eq_pass:
        old_t = [p["old_timing"] for p in scored["per"]]
        new_t = [p["new_timing"] for p in scored["per"]]
        timing = {
            "old": {k: stage_stats(old_t, k) for k in old_t[0]},
            "new": {k: stage_stats(new_t, k) for k in new_t[0]},
            "note": "Per-query means/medians on this host over n=50 SYSTEM-G pools. Do not compare ms to another host.",
            "stored_non_ce_ms": STORED_NON_CE_MS,
            "batch_size": BATCH_SIZE,
        }
        old_ce = timing["old"]["ce_total_ms"]["mean"]
        new_ce = timing["new"]["ce_total_ms"]["mean"]
        timing["ce_speedup"] = round(old_ce / new_ce, 4) if new_ce else None
        timing["ce_improved"] = bool(new_ce < old_ce)
        timing["system_g_total_old_ms"] = round(STORED_NON_CE_MS + old_ce, 4)
        timing["system_g_total_new_ms"] = round(STORED_NON_CE_MS + new_ce, 4)
        ce_improved = timing["ce_improved"]
    else:
        # still record times as diagnostic; decision will be FAILED_EQUIVALENCE
        old_t = [p["old_timing"] for p in scored["per"]]
        new_t = [p["new_timing"] for p in scored["per"]]
        timing = {
            "recorded_despite_equivalence_failure_diagnostic_only": True,
            "old": {k: stage_stats(old_t, k) for k in old_t[0]},
            "new": {k: stage_stats(new_t, k) for k in new_t[0]},
            "stored_non_ce_ms": STORED_NON_CE_MS,
        }
        old_ce = timing["old"]["ce_total_ms"]["mean"]
        new_ce = timing["new"]["ce_total_ms"]["mean"]
        timing["ce_speedup"] = round(old_ce / new_ce, 4) if new_ce else None
        timing["ce_improved"] = bool(new_ce < old_ce)
        timing["system_g_total_old_ms"] = round(STORED_NON_CE_MS + old_ce, 4)
        timing["system_g_total_new_ms"] = round(STORED_NON_CE_MS + new_ce, 4)
        ce_improved = False  # do not support if equivalence failed

    if eq_pass and ce_improved:
        decision = "PERF-003_SUPPORTED"
    elif not eq_pass:
        decision = "FAILED_EQUIVALENCE"
    else:
        decision = "FAILED_NO_CE_LATENCY_IMPROVEMENT"

    provenance = {
        "cpu": cpu_provenance(),
        "ort_version": ort.__version__,
        "provider": "CPUExecutionProvider",
        "intra_op_num_threads": 4,
        "inter_op_num_threads": 1,
        "ce_sha256": digest,
        "tokenizer_path": str(CE_TOKENIZER),
        "tokenizer_sha256": hashlib.sha256(CE_TOKENIZER.read_bytes()).hexdigest(),
        "batch_size": BATCH_SIZE,
        "old_padding_mode": "fixed length 512",
        "new_padding_mode": "batch (pad to batch max seq length, max_length 512)",
        "bucketing_rule": "sort by unpadded token length then original index; unpermute to original order",
        "cross_encoder_py_sha256": _sha(ROOT / "experiments" / "EXP-015" / "scripts" / "cross_encoder.py"),
        "v2_wrapper_sha256": _sha(ROOT / "experiments" / "PERF-003" / "scripts" / "v2_system_g_ce.py"),
        "runner_sha256": _sha(Path(__file__).resolve()),
        "class_defaults": defaults,
        "git": None,
        "embedding": emb,
    }

    artifact_info = None
    if eq_pass:
        art = build_d1_artifact(
            g_obj,
            "",
            {
                "label": "DEVELOPMENT_ONLY",
                "not_independently_validated": True,
                "source": "PERF-003 D1 path on frozen SYSTEM-G pools",
                **nm,
            },
            provenance,
        )
        if artifact_path.exists():
            raise SystemExit("STOP: SYSTEM-G-CE-D1.json already exists")
        write_json(artifact_path, art)
        artifact_info = {
            "path": str(artifact_path.relative_to(ROOT)),
            "config_hash": art["config_hash"],
            "file_sha256": _sha(artifact_path),
        }
        # confirm SYSTEM-G untouched
        if _sha(G_FILE) != G_FILE_SHA:
            raise SystemExit("STOP: SYSTEM-G was modified; this is forbidden")

    hold_after = holdout_log_state()
    payload = {
        "experiment_id": "PERF-003",
        "scored": True,
        "engineering_performance_only": True,
        "split": "v2-devset-001/development",
        "n": 50,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timestamp_et": datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%dT%H:%M:%S%z"),
        "preregistration_json_sha256": got_pre,
        "SYSTEM-G-PROJECTION-PRIOR_config_hash": G_CONFIG_HASH,
        "SYSTEM-G-PROJECTION-PRIOR_file_sha256": G_FILE_SHA,
        "SYSTEM-G_overwritten": False,
        "one_change": "V2 SYSTEM-G development path constructs CrossEncoderReranker(pad='batch', bucket_by_length=True); class defaults unchanged; no fast=True; threads=4",
        "n_perf_variants": 1,
        "tuned_after_seeing_scores": False,
        "n_evals": 1,
        "second_variant": False,
        "fast_true": False,
        "threads_8": False,
        "batch_size_changed_to_1": False,
        "validation_loaded": False,
        "holdout_loaded": False,
        "holdout_json_opened": False,
        "RELEASE": "NOT_FROZEN",
        "decision": decision,
        "equivalence": {
            "pass": eq_pass,
            "checks": checks,
            "n_pairs": scored["n_pairs"],
            "n_logit_mismatch": scored["n_logit_mismatch"],
            "max_abs_diff": scored["max_abs_diff"],
            "old_metrics": oldm,
            "new_metrics": nm,
            "fresh_old_ok": fresh_old_ok,
            "fresh_new_ok": fresh_new_ok,
            "fresh_returncode": proc.returncode,
        },
        "timing": timing,
        "artifact": artifact_info,
        "provenance": provenance,
        "holdout_access_log_before": hold_before,
        "holdout_access_log_after": hold_after,
        "holdout_log_unchanged": hold_after["log_sha256"] == hold_before["log_sha256"] == HOLD_LOG_EXPECTED,
        "per_query_timing": [
            {
                "case_id": p["case_id"],
                "n": p["n"],
                "old": p["old_timing"],
                "new": p["new_timing"],
                "new_batch_widths": p["new_batch_widths"],
                "old_batch_widths": p["old_batch_widths"],
            }
            for p in scored["per"]
        ],
        "runtime_seconds": round(time.time() - started, 1),
    }
    write_json(results_path, payload)
    write_report(report_path, payload)
    print("decision", decision, "eq", eq_pass, "artifact", artifact_info, flush=True)
    if hold_after["log_sha256"] != HOLD_LOG_EXPECTED:
        raise SystemExit("STOP: holdout log changed during PERF-003")
    if _sha(G_FILE) != G_FILE_SHA:
        raise SystemExit("STOP: SYSTEM-G modified")
    return 0 if eq_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
