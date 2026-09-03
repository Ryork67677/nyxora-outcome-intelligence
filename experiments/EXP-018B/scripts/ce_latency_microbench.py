#!/usr/bin/env python3
"""Isolated CE latency microbench. Synthetic queries + cs_v1_control passages.

Does not load gold150-v1 holdout or development, does not score V2-DEVSET-001,
does not write freeze files, does not change rankings.
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

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-015" / "scripts"))

from cross_encoder import (  # noqa: E402
    CE_ONNX,
    CE_SHA256,
    CrossEncoderReranker,
    MAX_LENGTH,
)
from rag_v1.db import connect  # noqa: E402

OUT_JSON = ROOT / "experiments" / "EXP-018B" / "ce-latency-microbench.json"
HOLD_LOG = ROOT / "evals" / "splits" / "gold150-v1" / "holdout-access.log.jsonl"
HOLD_SHA = "45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3"
N_PASSAGES = 104  # EXP-018B L=10 union mean
N_WARMUP = 1
N_TIMED = 3

SYNTH_QUERIES = [
    "How does the HTTP client apply retry backoff after a 429 response?",
    "Where is the default idle timeout configured for pooled database connections?",
    "What happens when a webhook signature fails validation during delivery?",
    "How are pagination cursors encoded for list endpoints that return partial pages?",
]


def hold_sha() -> tuple[int, str]:
    data = HOLD_LOG.read_bytes()
    return len(data), hashlib.sha256(data).hexdigest()


def load_passages(n: int) -> list[str]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT text
            FROM chunk
            WHERE chunk_set_id = 'cs_v1_control'
            ORDER BY chunk_id
            LIMIT %s
            """,
            (n + 50,),
        )
        rows = [r[0] for r in cur.fetchall() if r[0] and r[0].strip()]
    if len(rows) < n:
        raise SystemExit(f"not enough cs_v1_control passages: {len(rows)}")
    return rows[:n]


def logit_cmp(a: list[float], b: list[float]) -> dict:
    x = np.asarray(a, dtype=np.float64)
    y = np.asarray(b, dtype=np.float64)
    diff = np.abs(x - y)
    order_a = np.argsort(-x, kind="stable")
    order_b = np.argsort(-y, kind="stable")
    return {
        "n": int(x.size),
        "exact_equal": bool(np.array_equal(x, y)),
        "max_abs_diff": float(diff.max()) if x.size else 0.0,
        "mean_abs_diff": float(diff.mean()) if x.size else 0.0,
        "allclose_1e5": bool(np.allclose(x, y, rtol=1e-5, atol=1e-5)),
        "allclose_1e4": bool(np.allclose(x, y, rtol=1e-4, atol=1e-4)),
        "rank_identical": bool(np.array_equal(order_a, order_b)),
        "top10_identical": bool(np.array_equal(order_a[:10], order_b[:10])),
    }


def time_score(ce: CrossEncoderReranker, queries: list[str], passages: list[str],
               batch_size: int, warmup: int, timed: int) -> dict:
    for q in queries[:warmup]:
        ce.score_pairs(q, passages, batch_size=batch_size)
    xs = []
    last = None
    for q in queries[warmup:warmup + timed]:
        t0 = time.perf_counter()
        last = ce.score_pairs(q, passages, batch_size=batch_size)
        xs.append((time.perf_counter() - t0) * 1000)
    return {
        "ms_per_query": [round(v, 2) for v in xs],
        "ms_mean": round(statistics.mean(xs), 2) if xs else None,
        "ms_per_pair": round(statistics.mean(xs) / len(passages), 3) if xs else None,
        "n_passages": len(passages),
        "n_scores": len(last) if last is not None else 0,
    }


def tokenize_and_infer_split(ce: CrossEncoderReranker, query: str, passages: list[str],
                             batch_size: int) -> dict:
    tok_ms = 0.0
    infer_ms = 0.0
    pack_ms = 0.0
    n_batches = 0
    seq_lens = []
    for start in range(0, len(passages), batch_size):
        batch = passages[start:start + batch_size]
        t0 = time.perf_counter()
        encodings = ce._tokenizer.encode_batch([(query, p) for p in batch])
        tok_ms += (time.perf_counter() - t0) * 1000
        t1 = time.perf_counter()
        ids = np.array([e.ids for e in encodings], dtype=np.int64)
        mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
        types = np.array([e.type_ids for e in encodings], dtype=np.int64)
        feeds = {"input_ids": ids, "attention_mask": mask, "token_type_ids": types}
        pack_ms += (time.perf_counter() - t1) * 1000
        t2 = time.perf_counter()
        ce._session.run(None, feeds)
        infer_ms += (time.perf_counter() - t2) * 1000
        n_batches += 1
        for e in encodings:
            seq_lens.append(int(sum(e.attention_mask)))
    return {
        "tokenize_ms": round(tok_ms, 2),
        "pack_numpy_ms": round(pack_ms, 2),
        "infer_ms": round(infer_ms, 2),
        "n_batches": n_batches,
        "seq_len_mean": round(statistics.mean(seq_lens), 1),
        "seq_len_max": max(seq_lens),
        "seq_len_min": min(seq_lens),
        "frac_at_512": round(sum(1 for s in seq_lens if s >= 512) / len(seq_lens), 3),
        "pad_width": int(np.array([e.ids for e in encodings]).shape[1]) if encodings else None,
    }


def main() -> int:
    hold_before = hold_sha()
    if hold_before != (235, HOLD_SHA):
        raise SystemExit(f"STOP: holdout log drifted before bench: {hold_before}")

    digest = hashlib.sha256(CE_ONNX.read_bytes()).hexdigest()
    if digest != CE_SHA256:
        raise SystemExit("STOP: CE sha mismatch")

    passages = load_passages(N_PASSAGES)
    extra = load_passages(N_PASSAGES + 50)[-50:]  # unused extra for two-call split
    a_pool = passages[:94]
    extras = passages[94:104]
    queries = SYNTH_QUERIES
    assert len(queries) >= N_WARMUP + N_TIMED

    session_ms = []
    t0 = time.perf_counter()
    baseline = CrossEncoderReranker(threads=4)
    session_ms.append((time.perf_counter() - t0) * 1000)
    t0 = time.perf_counter()
    _ = CrossEncoderReranker(threads=4)
    session_ms.append((time.perf_counter() - t0) * 1000)

    # length stats with unpadded tokenizer clone
    from tokenizers import Tokenizer
    from cross_encoder import CE_TOKENIZER
    tok = Tokenizer.from_file(str(CE_TOKENIZER))
    tok.enable_truncation(max_length=MAX_LENGTH, strategy="longest_first")
    q0 = queries[0]
    raw = tok.encode_batch([(q0, p) for p in passages])
    raw_lens = [len(e.ids) for e in raw]
    length_stats = {
        "n": len(raw_lens),
        "mean": round(statistics.mean(raw_lens), 1),
        "p50": int(np.percentile(raw_lens, 50)),
        "p90": int(np.percentile(raw_lens, 90)),
        "max": max(raw_lens),
        "min": min(raw_lens),
        "frac_ge_512": round(sum(1 for x in raw_lens if x >= 512) / len(raw_lens), 3),
        "query_chars": len(q0),
        "passage_chars_mean": round(statistics.mean(len(p) for p in passages), 1),
    }

    configs = [
        {"name": "baseline_fixed_b16_t4", "threads": 4, "pad": "fixed", "batch_size": 16, "reuse": "baseline"},
        {"name": "fixed_b1_t4", "threads": 4, "pad": "fixed", "batch_size": 1, "reuse": "baseline"},
        {"name": "fixed_b32_t4", "threads": 4, "pad": "fixed", "batch_size": 32, "reuse": "baseline"},
        {"name": "fixed_b16_t8", "threads": 8, "pad": "fixed", "batch_size": 16, "reuse": None},
        {"name": "batchpad_b16_t4", "threads": 4, "pad": "batch", "batch_size": 16, "reuse": None},
        {"name": "batchpad_b32_t8", "threads": 8, "pad": "batch", "batch_size": 32, "reuse": None},
        {"name": "batchpad_mod8_b32_t8", "threads": 8, "pad": "batch", "pad_to_multiple_of": 8,
         "batch_size": 32, "reuse": None},
        {"name": "batchpad_b64_t8", "threads": 8, "pad": "batch", "batch_size": 64, "reuse": None},
    ]

    sessions: dict[str, CrossEncoderReranker] = {"baseline": baseline}
    timed = {}
    for cfg in configs:
        if cfg["reuse"] and cfg["reuse"] in sessions:
            ce = sessions[cfg["reuse"]]
        else:
            kw = {"threads": cfg["threads"], "pad": cfg["pad"]}
            if cfg.get("pad_to_multiple_of"):
                kw["pad_to_multiple_of"] = cfg["pad_to_multiple_of"]
            t0 = time.perf_counter()
            ce = CrossEncoderReranker(**kw)
            cfg["session_create_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            sessions[cfg["name"]] = ce
        timed[cfg["name"]] = {
            **cfg,
            **time_score(ce, queries, passages, cfg["batch_size"], N_WARMUP, N_TIMED),
        }
        print(cfg["name"], timed[cfg["name"]]["ms_mean"], "ms", flush=True)

    # tokenize vs infer on baseline and best-looking batch pad
    split_fixed = tokenize_and_infer_split(baseline, queries[0], passages, 16)
    ce_batch = sessions.get("batchpad_b32_t8") or CrossEncoderReranker(threads=8, pad="batch")
    split_batch = tokenize_and_infer_split(ce_batch, queries[0], passages, 32)

    # identity vs production baseline (threads=4, pad=fixed, batch=16)
    ident_q = queries[0]
    ident_p = passages[:32]
    gold = baseline.score_pairs(ident_q, ident_p, batch_size=16)
    identity = {
        "n_pairs": len(ident_p),
        "query": ident_q,
        "note": "synthetic query + first 32 cs_v1_control passages; not V2-DEVSET-001",
    }
    identity["self_repeat_same_session"] = logit_cmp(
        gold, baseline.score_pairs(ident_q, ident_p, batch_size=16)
    )
    identity["fixed_batch1_vs_batch16"] = logit_cmp(
        gold, baseline.score_pairs(ident_q, ident_p, batch_size=1)
    )
    identity["fixed_batch32_vs_batch16"] = logit_cmp(
        gold, baseline.score_pairs(ident_q, ident_p, batch_size=32)
    )
    ce_t8 = sessions.get("fixed_b16_t8")
    if ce_t8 is None:
        ce_t8 = CrossEncoderReranker(threads=8, pad="fixed")
    identity["fixed_t8_vs_t4"] = logit_cmp(
        gold, ce_t8.score_pairs(ident_q, ident_p, batch_size=16)
    )
    ce_bp = sessions.get("batchpad_b16_t4")
    if ce_bp is None:
        ce_bp = CrossEncoderReranker(threads=4, pad="batch")
    identity["batchpad_t4_b16_vs_fixed"] = logit_cmp(
        gold, ce_bp.score_pairs(ident_q, ident_p, batch_size=16)
    )
    identity["batchpad_t8_b32_vs_fixed"] = logit_cmp(
        gold, ce_batch.score_pairs(ident_q, ident_p, batch_size=32)
    )

    # two-call (A-pool then extras) vs one union call, production pad
    t0 = time.perf_counter()
    s_a = baseline.score_pairs(ident_q, a_pool, batch_size=16)
    s_x = baseline.score_pairs(ident_q, extras, batch_size=16)
    two_ms = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter()
    s_u = baseline.score_pairs(ident_q, a_pool + extras, batch_size=16)
    one_ms = (time.perf_counter() - t0) * 1000
    two_call = {
        "two_call_ms": round(two_ms, 2),
        "one_call_ms": round(one_ms, 2),
        "identity": logit_cmp(s_a + s_x, s_u),
        "n_a": len(a_pool),
        "n_extra": len(extras),
    }

    hold_after = hold_sha()
    payload = {
        "experiment_id": "EXP-018B",
        "artifact": "ce-latency-microbench",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cpu_count": os.cpu_count(),
        "ce_sha256": digest,
        "n_passages": N_PASSAGES,
        "queries": SYNTH_QUERIES,
        "session_create_ms": [round(x, 1) for x in session_ms],
        "length_stats": length_stats,
        "timed": timed,
        "split_fixed_b16": split_fixed,
        "split_batchpad_b32": split_batch,
        "identity": identity,
        "two_call_vs_one": two_call,
        "holdout_log_before": {"bytes": hold_before[0], "sha256": hold_before[1]},
        "holdout_log_after": {"bytes": hold_after[0], "sha256": hold_after[1]},
        "holdout_log_unchanged": hold_after == hold_before == (235, HOLD_SHA),
        "v2_devset_scored": False,
        "holdout_opened": False,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT_JSON, flush=True)
    if hold_after != (235, HOLD_SHA):
        raise SystemExit("STOP: holdout log changed during bench")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
