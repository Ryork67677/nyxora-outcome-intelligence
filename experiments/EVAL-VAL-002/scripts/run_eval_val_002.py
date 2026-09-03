#!/usr/bin/env python3
"""EVAL-VAL-002: one-shot validation of frozen SYSTEM-D-GUARD-BLEND.

Validation set ONLY (gold150-v1/validation.json, n=40). Does not load holdout.
Does not enumerate holdout IDs. Does not fetch live docs. Does not train.
Does not change frozen SYSTEM-D. Compares D against ALREADY RECORDED SYSTEM-A
from EVAL-VAL-001. Retrieving SYSTEM-A pool-100 is candidate generation for D,
not a new A evaluation.
"""

from __future__ import annotations

import hashlib
import json
import platform
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from math import comb
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EXP015_SCRIPTS = ROOT / "experiments" / "EXP-015" / "scripts"
if str(EXP015_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(EXP015_SCRIPTS))
EXP016_SCRIPTS = ROOT / "experiments" / "EXP-016" / "scripts"
if str(EXP016_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(EXP016_SCRIPTS))

from cross_encoder import (  # noqa: E402
    CE_NAME,
    CE_ONNX,
    CE_REVISION,
    CE_SHA256,
    MAX_LENGTH,
    CrossEncoderReranker,
)
from identifier_matcher import (  # noqa: E402
    extract_identifiers,
    has_exact_identifier_overlap,
    overlapping_identifiers,
)
from rag_v1.embedders_transformer import TransformerEncoder  # noqa: E402
from rag_v1.evals.io import load_cases  # noqa: E402
from rag_v1.ids import config_hash  # noqa: E402
from rag_v1.query_cache import CachedQueryEmbedder  # noqa: E402
from rag_v1.retrieval import dense_search, lexical_search, rrf_fuse  # noqa: E402
from rag_v1.systems import (  # noqa: E402
    CHUNK_SET,
    FROZEN_HASHES,
    SNAPSHOT,
    TRANSFORMER_FINGERPRINT,
    TRANSFORMER_MODEL,
)
from rag_v1.types import EvidenceRef, SearchHit  # noqa: E402

PROBE_DEPTHS = (10, 20, 30, 50, 100, 300)
TOP_K, RRF_POOL, RRF_K, CANDIDATE_POOL = 10, 50, 60, 100
A_HASH = "9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38"
EXPECTED_D_HASH = "d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a"
BLEND_CE, BLEND_A = 0.7, 0.3
BOOTSTRAP_SEED, BOOTSTRAP_SAMPLES = 20250818, 10000
NAMED_DEV_ONLY = ("HA-22", "HA-24", "GOLD-B005-11")
VAL_JSONL = ROOT / "evals" / "splits" / "gold150-v1" / "validation.jsonl"
VAL_JSON = ROOT / "evals" / "splits" / "gold150-v1" / "validation.json"
DEV_JSON = ROOT / "evals" / "splits" / "gold150-v1" / "development.json"
FREEZE = ROOT / "experiments" / "EXP-016" / "SYSTEM-D-GUARD.json"
EVAL_VAL_001 = ROOT / "experiments" / "EVAL-VAL-001" / "EVAL-VAL-001-results.json"
OUT_DIR = ROOT / "experiments" / "EVAL-VAL-002"
EXP016_DIR = ROOT / "experiments" / "EXP-016"


def holdout_log_bytes() -> int:
    path = ROOT / "evals" / "splits" / "gold150-v1" / "holdout-access.log.jsonl"
    return path.stat().st_size if path.exists() else -1


def overlaps(hit: SearchHit, ref: EvidenceRef) -> bool:
    return (
        hit.version_id == ref.version_id
        and list(hit.section_path) == list(ref.section_path)
        and hit.char_start < ref.char_end
        and hit.char_end > ref.char_start
    )


def embedding_status() -> dict:
    from rag_v1.db import connect

    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (CHUNK_SET,))
        chunks = cur.fetchone()[0]
        cur.execute(
            "SELECT count(*), min(model_fingerprint), max(model_fingerprint) "
            "FROM chunk_embedding WHERE model_id=%s",
            (TRANSFORMER_MODEL,),
        )
        n, fp_min, fp_max = cur.fetchone()
    return {
        "chunk_set": CHUNK_SET,
        "chunks": chunks,
        "embedding_rows": n,
        "model_id": TRANSFORMER_MODEL,
        "fingerprint_min": fp_min,
        "fingerprint_max": fp_max,
        "fingerprint_expected": TRANSFORMER_FINGERPRINT,
        "complete": n == chunks == 14209 and fp_min == fp_max == TRANSFORMER_FINGERPRINT,
    }


def retrieve_system_a_pool(query: str, embedder) -> list[SearchHit]:
    lexical = lexical_search(query, SNAPSHOT, RRF_POOL)
    dense = dense_search(query, SNAPSHOT, TRANSFORMER_MODEL, RRF_POOL, embedder=embedder)
    return rrf_fuse([lexical, dense], rrf_k=RRF_K, top_k=CANDIDATE_POOL)


def minmax_norm(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5] * len(values)
    scale = hi - lo
    return [(v - lo) / scale for v in values]


def apply_blend(rows: list[dict]) -> list[dict]:
    """Frozen SYSTEM-D-GUARD-BLEND. Do not retune weights or tie-break."""
    ce_n = minmax_norm([r["ce_score"] for r in rows])
    a_n = minmax_norm([r["a_score"] for r in rows])
    blended = []
    for row, ce, a in zip(rows, ce_n, a_n, strict=True):
        item = dict(row)
        item["ce_norm"] = ce
        item["a_norm"] = a
        item["blend_score"] = BLEND_CE * ce + BLEND_A * a
        blended.append(item)
    blended.sort(key=lambda r: (-r["blend_score"], r["a_rank"], r["chunk_id"]))
    for i, row in enumerate(blended, start=1):
        row["d_rank"] = i
    return blended


def score_case(case, hits) -> dict:
    spans = []
    for ref in case.expected_evidence:
        hit = next((h for h in hits if overlaps(h, ref)), None)
        doc_rank = next((h.rank for h in hits if h.version_id == ref.version_id), None)
        spans.append(
            {
                "rank": hit.rank if hit else None,
                "doc_rank": doc_rank,
                "chunk_id": hit.chunk_id if hit else None,
                "within": {
                    str(d): (hit is not None and hit.rank <= d) for d in PROBE_DEPTHS
                },
                "doc_within_10": doc_rank is not None and doc_rank <= TOP_K,
            }
        )
    found = sum(1 for s in spans if s["within"]["10"])
    return {
        "case_id": case.case_id,
        "spans": spans,
        "recall": found / len(spans) if spans else 1.0,
        "fully_recalled": bool(spans) and found == len(spans),
        "doc_recall": (
            sum(1 for s in spans if s["doc_within_10"]) / len(spans) if spans else 1.0
        ),
    }


def hits_from_blend(rows: list[dict]) -> list[SearchHit]:
    hits = []
    for row in rows:
        hits.append(
            SearchHit(
                chunk_id=row["chunk_id"],
                version_id=row["version_id"],
                section_path=list(row["section_path"]),
                char_start=row["char_start"],
                char_end=row["char_end"],
                text=row.get("text") or "",
                score=float(row["blend_score"]),
                rank=int(row["d_rank"]),
                retriever="system_d_blend",
                metadata={
                    "ce_score": row["ce_score"],
                    "a_rank": row["a_rank"],
                    "a_score": row["a_score"],
                    "blend_score": row["blend_score"],
                },
            )
        )
    return hits


def summarise(per_case: dict, system: str, config_hash_value: str) -> dict:
    all_spans = [s for c in per_case.values() for s in c["spans"]]
    recalls = [c["recall"] for c in per_case.values()]
    return {
        "system": system,
        "config_hash": config_hash_value,
        "macro_span_recall": round(sum(recalls) / len(recalls), 4),
        "cases_fully_recalled": sum(1 for c in per_case.values() if c["fully_recalled"]),
        "cases_total": len(per_case),
        "strict_recall_at_10": (
            f"{sum(1 for c in per_case.values() if c['fully_recalled'])}/{len(per_case)}"
        ),
        "spans_found_at_10": sum(1 for s in all_spans if s["within"]["10"]),
        "spans_total": len(all_spans),
        "document_recall": round(
            sum(c["doc_recall"] for c in per_case.values()) / len(per_case), 4
        ),
        "mrr": round(
            sum(1 / s["rank"] for s in all_spans if s["rank"]) / len(all_spans), 4
        ),
        "spans_absent_from_top": {
            str(d): sum(1 for s in all_spans if not s["within"][str(d)])
            for d in PROBE_DEPTHS
        },
        "cases": per_case,
    }


def bootstrap_strict(a_full: dict, d_full: dict, a_recall: dict, d_recall: dict) -> dict:
    ids = sorted(a_full)
    diffs = np.array([d_recall[cid] - a_recall[cid] for cid in ids])
    case_diffs = np.array([int(d_full[cid]) - int(a_full[cid]) for cid in ids])
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    n = len(ids)
    recall_samples, case_samples = [], []
    for _ in range(BOOTSTRAP_SAMPLES):
        pick = rng.integers(0, n, n)
        recall_samples.append(float(diffs[pick].mean()))
        case_samples.append(float(case_diffs[pick].mean()))
    return {
        "seed": BOOTSTRAP_SEED,
        "samples": BOOTSTRAP_SAMPLES,
        "n_questions": n,
        "unit": "paired cases (questions), not spans",
        "macro_recall_delta": {
            "point_estimate": round(float(diffs.mean()), 4),
            "ci95": [
                round(float(np.percentile(recall_samples, 2.5)), 4),
                round(float(np.percentile(recall_samples, 97.5)), 4),
            ],
        },
        "fully_recalled_delta_per_case": {
            "point_estimate": round(float(case_diffs.mean()), 4),
            "ci95": [
                round(float(np.percentile(case_samples, 2.5)), 4),
                round(float(np.percentile(case_samples, 97.5)), 4),
            ],
            "note": "paired bootstrap on the 40 paired strict 0/1 outcomes (D−A)",
        },
    }


def mcnemar(a_full: dict, d_full: dict) -> dict:
    d_only = a_only = 0
    for cid, a_ok in a_full.items():
        d_ok = d_full[cid]
        if d_ok and not a_ok:
            d_only += 1
        elif a_ok and not d_ok:
            a_only += 1
    n = a_only + d_only
    if n == 0:
        return {
            "discordant_pairs": 0,
            "d_only": 0,
            "a_only": 0,
            "p_value": None,
            "note": "no discordant pairs — the test is undefined",
        }
    k = min(a_only, d_only)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / (2 ** n))
    return {
        "discordant_pairs": n,
        "d_only": d_only,
        "a_only": a_only,
        "p_value": round(p, 4),
        "note": "exact binomial McNemar on discordant strict fully-recalled outcomes",
    }


def excerpt(text: str, limit: int = 220) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def classify_movement(
    movement: str,
    query: str,
    span_rows: list[dict],
    d_top: dict | None,
    truncated_gold: bool,
) -> tuple[str, str]:
    """One label for a rescue or regression. Conservative; do not stretch."""
    q_ids = extract_identifiers(query)
    gold_overlap = any(s.get("identifier_overlap") for s in span_rows)
    overlap_tokens = sorted({t for s in span_rows for t in (s.get("overlap_tokens") or [])})
    versionish = [t for t in q_ids if any(c.isdigit() for c in t)]
    gold_versions = {s["version_id"] for s in span_rows if s.get("version_id")}
    demoted_id = []
    for s in span_rows:
        a_r = s.get("a_rank_stored")
        d_r = s.get("d_rank")
        if s.get("identifier_overlap") and a_r is not None and a_r <= 10:
            if d_r is None or d_r > 10:
                demoted_id.append(s)
        if s.get("identifier_overlap") and a_r is not None and a_r <= 3:
            if d_r is None or d_r > 10:
                demoted_id.append(s)

    d_top_version = d_top["version_id"] if d_top else None
    different_version = (
        d_top is not None
        and gold_versions
        and d_top_version not in gold_versions
    )

    if movement == "REGRESSION" and demoted_id:
        return (
            "EXACT_IDENTIFIER_DEMOTION",
            "Gold span had exact identifier overlap with the query and was in SYSTEM-A "
            f"top 10 (tokens={overlap_tokens}); blend placed it outside top 10.",
        )
    if movement == "REGRESSION" and different_version and versionish:
        return (
            "VERSION_CONFUSION",
            f"Query carries version-like identifier tokens {versionish}; D rank-1 is a "
            f"different version_id ({d_top_version}) than gold {sorted(gold_versions)}.",
        )
    if movement == "REGRESSION" and truncated_gold:
        return (
            "TRUNCATION",
            "Gold query+passage pair exceeded CE max_length=512 (longest_first); "
            "truncation is a plausible contributor to the demotion.",
        )
    if movement == "REGRESSION":
        gold_ce = [s.get("ce_score") for s in span_rows if s.get("ce_score") is not None]
        top_ce = d_top["ce_score"] if d_top else None
        if gold_ce and top_ce is not None and top_ce > max(gold_ce):
            return (
                "SEMANTIC_MISREAD",
                f"CE scored a non-gold pool candidate higher ({top_ce:.4f}) than the gold "
                f"span ({max(gold_ce):.4f}); blend followed that preference. No exact-"
                "identifier demotion of an A-top-10 gold span.",
            )
        return (
            "OTHER",
            "D lost a recorded-A pass without a clear exact-identifier, version, or "
            "truncation signature.",
        )

    # RESCUE
    if gold_overlap:
        return (
            "SEMANTIC_MISREAD",
            "Rescue: identifier overlap existed and CE/blend lifted the gold span into "
            f"top 10 (overlap_tokens={overlap_tokens}). Label is mechanism-of-gain, not "
            "a misread of a pass.",
        )
    gold_ce = [s.get("ce_score") for s in span_rows if s.get("ce_score") is not None]
    if gold_ce:
        return (
            "SEMANTIC_MISREAD",
            "Rescue: CE scored the gold span highly enough that 0.7 CE + 0.3 A blend "
            f"moved it into top 10 (gold CE={max(gold_ce):.4f}).",
        )
    return ("OTHER", "Rescue without a stored CE score on the gold span.")


def decide(net: int, d_strict: int, a_strict: int, dest_rank1: list, dest_head: list) -> dict:
    """Exactly one of RERANKER_SUPPORTED / RERANKER_NEUTRAL / RERANKER_REJECTED."""
    catastrophic = len(dest_rank1) > 0 or len(dest_head) >= 3
    if d_strict > a_strict and net > 0 and not catastrophic:
        label = "RERANKER_SUPPORTED"
        reason = (
            f"D strictly beats recorded A on primary ({d_strict}/40 vs {a_strict}/40, "
            f"net {net:+d}) without catastrophic exact-match destruction "
            f"(rank-1 destructions={len(dest_rank1)}, A≤3-out-of-10={len(dest_head)})."
        )
    elif d_strict < a_strict or (catastrophic and net <= 0):
        label = "RERANKER_REJECTED"
        reason = (
            f"D is worse on strict ({d_strict}/40 vs recorded A {a_strict}/40, net {net:+d})"
            if d_strict < a_strict
            else (
                f"D does not beat A and shows exact-match destruction as a pattern "
                f"(rank-1 destructions={len(dest_rank1)}, A≤3-out-of-10={len(dest_head)})."
            )
        )
    else:
        label = "RERANKER_NEUTRAL"
        reason = (
            f"Equal strict ({d_strict}/40 = {a_strict}/40) with mixed mechanism "
            f"(net {net:+d}; rank-1 destructions={len(dest_rank1)})."
            if d_strict == a_strict
            else (
                f"D {d_strict}/40 vs A {a_strict}/40 net {net:+d} is not a clean support "
                f"or reject under the suggested mapping "
                f"(rank-1 destructions={len(dest_rank1)})."
            )
        )
    return {"label": label, "reason": reason}


def frozen_d_hash(a_hash: str) -> str:
    return config_hash(
        {
            "name": "SYSTEM-D-GUARD-BLEND",
            "control": a_hash,
            "pool": CANDIDATE_POOL,
            "weights": [BLEND_CE, BLEND_A],
            "minmax_degenerate": 0.5,
            "ce_sha256": CE_SHA256,
            "tie_break": "blend desc, A rank, chunk_id",
        }
    )


def main() -> int:
    started = time.time()
    if holdout_log_bytes() != 0:
        raise SystemExit(f"STOP: holdout access log is {holdout_log_bytes()} bytes")

    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if freeze.get("implementation") != "SYSTEM-D-GUARD-BLEND":
        raise SystemExit(f"STOP: freeze implementation {freeze.get('implementation')}")
    if freeze.get("config_hash") != EXPECTED_D_HASH:
        raise SystemExit(
            f"STOP: freeze config_hash {freeze.get('config_hash')} != {EXPECTED_D_HASH}"
        )
    if list(freeze.get("guard", {}).get("blend_weights") or []) != [BLEND_CE, BLEND_A]:
        raise SystemExit("STOP: freeze blend weights changed")
    if freeze.get("candidate_pool") != CANDIDATE_POOL:
        raise SystemExit("STOP: freeze candidate_pool changed")
    if freeze.get("cross_encoder", {}).get("artifact_sha256") != CE_SHA256:
        raise SystemExit("STOP: freeze CE sha256 changed")
    if freeze.get("system_a_config_hash") != A_HASH:
        raise SystemExit("STOP: freeze SYSTEM-A hash changed")

    a_hash = FROZEN_HASHES["SYSTEM-A-GLOBAL"]
    if a_hash != A_HASH:
        raise SystemExit(f"STOP: live SYSTEM-A hash {a_hash} != {A_HASH}")

    d_hash = frozen_d_hash(a_hash)
    if d_hash != EXPECTED_D_HASH:
        raise SystemExit(
            f"STOP: recomputed SYSTEM-D config hash {d_hash} != freeze {EXPECTED_D_HASH}"
        )
    if d_hash != freeze["config_hash"]:
        raise SystemExit("STOP: recomputed hash does not match freeze file")

    print(f"SYSTEM-D config hash verified: {d_hash}")
    print("Proceeding to score frozen SYSTEM-D-GUARD-BLEND on validation n=40 once.")

    onnx_digest = hashlib.sha256(CE_ONNX.read_bytes()).hexdigest()
    if onnx_digest != CE_SHA256:
        raise SystemExit(f"STOP: live CE onnx sha256 {onnx_digest} != {CE_SHA256}")

    emb = embedding_status()
    if not emb["complete"]:
        raise SystemExit(f"STOP: embeddings incomplete: {emb}")

    recorded = json.loads(EVAL_VAL_001.read_text(encoding="utf-8"))
    stored_a = recorded["system_a"]
    if stored_a["cases_fully_recalled"] != 30 or stored_a["cases_total"] != 40:
        raise SystemExit("STOP: recorded SYSTEM-A is not 30/40")
    if abs(stored_a["macro_span_recall"] - 0.75) > 1e-9:
        raise SystemExit("STOP: recorded SYSTEM-A macro span recall is not 0.75")
    if abs(stored_a["document_recall"] - 0.975) > 1e-9:
        raise SystemExit("STOP: recorded SYSTEM-A document recall is not 0.975")
    if abs(stored_a["mrr"] - 0.5283) > 1e-9:
        raise SystemExit("STOP: recorded SYSTEM-A MRR is not 0.5283")
    if recorded["system_a_config_hash"] != A_HASH:
        raise SystemExit("STOP: EVAL-VAL-001 SYSTEM-A hash mismatch")

    val_manifest = json.loads(VAL_JSON.read_text(encoding="utf-8"))
    val_ids = list(val_manifest["case_ids"])
    if len(val_ids) != 40:
        raise SystemExit(f"STOP: validation.json count {len(val_ids)} != 40")

    dev_ids = set(json.loads(DEV_JSON.read_text(encoding="utf-8"))["case_ids"])
    named_audit = {}
    for cid in NAMED_DEV_ONLY:
        in_val = cid in val_ids
        in_dev = cid in dev_ids
        named_audit[cid] = {
            "in_validation": in_val,
            "in_development": in_dev,
            "looked_up_in_holdout": False,
            "status": (
                "development-only; not in validation; not looked up in holdout"
                if (in_dev and not in_val)
                else ("IN VALIDATION" if in_val else "not in validation.json case_ids")
            ),
        }
    if any(named_audit[c]["in_validation"] for c in NAMED_DEV_ONLY):
        # still allowed; just note. Instruction: if development-only, say so.
        pass

    cases = [c for c in load_cases(VAL_JSONL) if c.expected_evidence]
    if len(cases) != 40:
        raise SystemExit(f"STOP: expected 40 validation cases, got {len(cases)}")
    loaded_ids = [c.case_id for c in cases]
    if loaded_ids != val_ids:
        raise SystemExit("STOP: validation.jsonl case order/ids != validation.json")

    encoder = TransformerEncoder(max_seq=512).load()
    if encoder.model_version != TRANSFORMER_FINGERPRINT:
        raise SystemExit(
            f"STOP: live encoder fingerprint {encoder.model_version} != {TRANSFORMER_FINGERPRINT}"
        )
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)
    ce = CrossEncoderReranker()
    probe_q, probe_p = "What is BM25?", "BM25 is a lexical ranking function."
    ce_stable = ce.score_pairs(probe_q, [probe_p])[0] == ce.score_pairs(probe_q, [probe_p])[0]

    d_cases = {}
    remat_a_cases = {}
    lat_a, lat_ce, lat_total = [], [], []
    per_case = []
    compact_pools = []
    a_rank_mismatches = []
    movement_details = []

    for case in cases:
        q = case.question
        t_all = time.time()
        t0 = time.time()
        pool = retrieve_system_a_pool(q, transformer)
        lat_a.append((time.time() - t0) * 1000)
        t0 = time.time()
        scores = ce.score_pairs(q, [h.text for h in pool])
        lat_ce.append((time.time() - t0) * 1000)

        rows = []
        for hit, score in zip(pool, scores, strict=True):
            rows.append(
                {
                    "chunk_id": hit.chunk_id,
                    "version_id": hit.version_id,
                    "section_path": list(hit.section_path),
                    "char_start": hit.char_start,
                    "char_end": hit.char_end,
                    "a_rank": hit.rank,
                    "a_score": float(hit.score),
                    "ce_score": float(score),
                    "identifier_overlap": has_exact_identifier_overlap(q, hit.text),
                    "overlap_tokens": overlapping_identifiers(q, hit.text),
                    "text": hit.text,
                    "ce_pair_truncated": False,
                }
            )

        # truncation flag via CE tokenizer (read-only diagnostic; not a knob)
        encodings = ce._tokenizer.encode_batch([(q, r["text"]) for r in rows])
        for row, enc in zip(rows, encodings, strict=True):
            # overflowing tokens exist if longest_first truncated
            overflowing = getattr(enc, "overflowing", None)
            n_overflow = 0
            if overflowing:
                n_overflow = len(overflowing) if not isinstance(overflowing, int) else overflowing
            row["ce_pair_truncated"] = bool(n_overflow) or (len(enc.ids) >= MAX_LENGTH and (
                getattr(enc, "n_truncated_tokens", 0) or False
            ))
            row["ce_n_tokens_unpadded"] = int(sum(enc.attention_mask))

        d_rows = apply_blend([dict(r) for r in rows])
        d_rank = {r["chunk_id"]: r["d_rank"] for r in d_rows}
        blend_by = {r["chunk_id"]: r["blend_score"] for r in d_rows}
        ce_order = sorted(rows, key=lambda r: (-r["ce_score"], r["a_rank"], r["chunk_id"]))
        ce_rank = {r["chunk_id"]: i for i, r in enumerate(ce_order, start=1)}
        by_id = {r["chunk_id"]: r for r in rows}

        remat_a_cases[case.case_id] = score_case(case, pool)
        d_hits = hits_from_blend(d_rows)
        d_cases[case.case_id] = score_case(case, d_hits)
        lat_total.append((time.time() - t_all) * 1000)

        stored_spans = stored_a["cases"][case.case_id]["spans"]
        remat_spans = remat_a_cases[case.case_id]["spans"]
        for i, (st, rm) in enumerate(zip(stored_spans, remat_spans, strict=True)):
            if st["rank"] != rm["rank"]:
                a_rank_mismatches.append(
                    {
                        "case_id": case.case_id,
                        "span_index": i,
                        "stored_a_rank": st["rank"],
                        "rematerialized_a_rank": rm["rank"],
                    }
                )

        span_rows = []
        gold_truncated = False
        for i, ref in enumerate(case.expected_evidence):
            d_span = d_cases[case.case_id]["spans"][i]
            cid = d_span["chunk_id"]
            # if not in D ranking, try overlap against pool
            if cid is None:
                hit = next((h for h in pool if overlaps(h, ref)), None)
                cid = hit.chunk_id if hit else None
            row = by_id.get(cid) if cid else None
            stored_span = stored_spans[i]
            truncated = bool(row["ce_pair_truncated"]) if row else False
            if truncated:
                gold_truncated = True
            span_rows.append(
                {
                    "span_index": i,
                    "chunk_id": cid,
                    "version_id": ref.version_id,
                    "section_path": list(ref.section_path),
                    "a_rank_stored": stored_span["rank"],
                    "a_doc_rank_stored": stored_span.get("doc_rank"),
                    "a_rank_rematerialized": remat_spans[i]["rank"],
                    "a_rank": row["a_rank"] if row else remat_spans[i]["rank"],
                    "a_score": row["a_score"] if row else None,
                    "ce_score": row["ce_score"] if row else None,
                    "ce_rank": ce_rank.get(cid) if cid else None,
                    "d_rank": d_rank.get(cid) if cid else d_span["rank"],
                    "d_doc_rank": d_span["doc_rank"],
                    "blend_score": blend_by.get(cid) if cid else None,
                    "identifier_overlap": row["identifier_overlap"] if row else False,
                    "overlap_tokens": row["overlap_tokens"] if row else [],
                    "exact_match_guard_triggered": False,
                    "exact_match_guard_note": (
                        "SYSTEM-D is score_blend; the EXP-016 clamp/guard is not applied. "
                        "identifier_overlap is recorded only as a diagnostic."
                    ),
                    "would_have_been_clamp_protected": bool(
                        row
                        and row["identifier_overlap"]
                        and row["a_rank"] <= 3
                    )
                    if row
                    else False,
                    "ce_pair_truncated": truncated,
                    "a_in_top_10_stored": bool(stored_span["within"]["10"]),
                    "d_in_top_10": d_span["within"]["10"],
                    "excerpt": excerpt(row["text"]) if row else None,
                }
            )

        a_full_stored = stored_a["cases"][case.case_id]["fully_recalled"]
        d_full = d_cases[case.case_id]["fully_recalled"]
        rec = {
            "case_id": case.case_id,
            "a_full_recorded": a_full_stored,
            "a_full_rematerialized": remat_a_cases[case.case_id]["fully_recalled"],
            "d_full": d_full,
            "pool_size": len(pool),
            "all_spans_in_pool": all(s["a_rank"] is not None for s in span_rows),
            "spans": span_rows,
            "n_identifier_overlap_in_pool": sum(1 for r in rows if r["identifier_overlap"]),
            "latency_ms": {
                "system_a_retrieval": round(lat_a[-1], 2),
                "cross_encoder": round(lat_ce[-1], 2),
                "total": round(lat_total[-1], 2),
            },
        }
        per_case.append(rec)

        d_top_row = d_rows[0] if d_rows else None
        d_top = (
            {
                "chunk_id": d_top_row["chunk_id"],
                "version_id": d_top_row["version_id"],
                "a_rank": d_top_row["a_rank"],
                "ce_score": d_top_row["ce_score"],
                "blend_score": d_top_row["blend_score"],
                "identifier_overlap": d_top_row["identifier_overlap"],
                "excerpt": excerpt(d_top_row["text"]),
            }
            if d_top_row
            else None
        )
        if a_full_stored != d_full:
            movement = "RESCUE" if (d_full and not a_full_stored) else "REGRESSION"
            label, why = classify_movement(movement, q, span_rows, d_top, gold_truncated)
            movement_details.append(
                {
                    "case_id": case.case_id,
                    "movement": movement,
                    "classification": label,
                    "why": why,
                    "query": q,
                    "a_full_recorded": a_full_stored,
                    "d_full": d_full,
                    "spans": span_rows,
                    "d_rank1": d_top,
                    "gold_ce_pair_truncated": gold_truncated,
                    "all_required_spans_in_d_top_10": d_full,
                }
            )

        compact_pools.append(
            {
                "case_id": case.case_id,
                "pool": [
                    {
                        "chunk_id": r["chunk_id"],
                        "a_rank": r["a_rank"],
                        "a_score": r["a_score"],
                        "ce_score": r["ce_score"],
                        "ce_rank": ce_rank[r["chunk_id"]],
                        "d_rank": d_rank[r["chunk_id"]],
                        "blend_score": blend_by[r["chunk_id"]],
                        "identifier_overlap": r["identifier_overlap"],
                        "overlap_tokens": r["overlap_tokens"],
                    }
                    for r in rows
                ],
            }
        )
        for r in rows:
            r.pop("text", None)

        print(
            f"{case.case_id} A_rec={int(a_full_stored)} D={int(d_full)} "
            f"pool={len(pool)} ce_ms={lat_ce[-1]:.0f}",
            flush=True,
        )

    if holdout_log_bytes() != 0:
        raise SystemExit(
            f"STOP: holdout access log grew to {holdout_log_bytes()} bytes during run"
        )

    system_d = summarise(d_cases, "SYSTEM-D-GUARD-BLEND", d_hash)

    a_full = {cid: stored_a["cases"][cid]["fully_recalled"] for cid in d_cases}
    d_full_map = {cid: d_cases[cid]["fully_recalled"] for cid in d_cases}
    a_recall = {cid: stored_a["cases"][cid]["recall"] for cid in d_cases}
    d_recall = {cid: d_cases[cid]["recall"] for cid in d_cases}

    rescues = [cid for cid, ok in d_full_map.items() if ok and not a_full[cid]]
    regressions = [cid for cid, ok in d_full_map.items() if a_full[cid] and not ok]
    both_pass = [cid for cid, ok in d_full_map.items() if ok and a_full[cid]]
    both_fail = [cid for cid, ok in d_full_map.items() if (not ok) and (not a_full[cid])]
    net = len(rescues) - len(regressions)

    dest_head = []
    dest_rank1 = []
    for rec in per_case:
        for s in rec["spans"]:
            a_rank = s["a_rank_stored"]
            if a_rank is not None and a_rank <= 3 and not s["d_in_top_10"]:
                ev = {
                    "case_id": rec["case_id"],
                    "chunk_id": s["chunk_id"],
                    "a_rank": a_rank,
                    "d_rank": s["d_rank"],
                    "identifier_overlap": s["identifier_overlap"],
                }
                dest_head.append(ev)
                if a_rank == 1:
                    dest_rank1.append(ev)

    boot = bootstrap_strict(a_full, d_full_map, a_recall, d_recall)
    mc = mcnemar(a_full, d_full_map)
    decision = decide(net, system_d["cases_fully_recalled"], 30, dest_rank1, dest_head)

    remat_a_strict = sum(1 for c in remat_a_cases.values() if c["fully_recalled"])

    meta = {}
    for line in VAL_JSONL.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        notes = json.loads(obj["notes"]) if obj.get("notes") else {}
        meta[obj["case_id"]] = {
            **notes,
            "span_count": len(obj["expected_evidence"]),
            "category": obj.get("category"),
        }

    results = {
        "experiment_id": "EVAL-VAL-002",
        "phase": "validation",
        "split": "gold150-v1/validation",
        "split_path": "evals/splits/gold150-v1/validation.json",
        "projection_path": "evals/splits/gold150-v1/validation.jsonl",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "corpus_snapshot": SNAPSHOT,
        "chunk_set": CHUNK_SET,
        "system_a_config_hash": a_hash,
        "system_d_config_hash": d_hash,
        "system_d_config_hash_matched_freeze_before_scoring": True,
        "freeze_path": "experiments/EXP-016/SYSTEM-D-GUARD.json",
        "freeze_untouched": True,
        "tuned_after_seeing_scores": False,
        "validation_loaded": True,
        "holdout_loaded": False,
        "holdout_ids_enumerated": False,
        "holdout_question_text_loaded": False,
        "holdout_access_log_bytes": holdout_log_bytes(),
        "holdout_runs": 0,
        "live_docs_fetched": False,
        "trained": False,
        "cases_scored": 40,
        "d_runs": 1,
        "embedding": emb,
        "recorded_system_a": {
            "source": "experiments/EVAL-VAL-001/EVAL-VAL-001-results.json",
            "not_a_new_A_evaluation": True,
            "strict_recall_at_10": "30/40",
            "cases_fully_recalled": 30,
            "macro_span_recall": 0.75,
            "document_recall": 0.975,
            "mrr": 0.5283,
            "spans_found_at_10": stored_a["spans_found_at_10"],
            "spans_total": stored_a["spans_total"],
        },
        "rematerialized_A_for_D_candidates_only": {
            "note": (
                "SYSTEM-A top-100 was retrieved on the 40 val cases as candidate "
                "generation for D, not as a new A evaluation. Primary comparison is "
                "against recorded EVAL-VAL-001 A metrics and per-case ranks."
            ),
            "gold_span_rank_mismatches_vs_recorded": a_rank_mismatches,
            "mismatch_count": len(a_rank_mismatches),
            "rematerialized_strict_fully_recalled": remat_a_strict,
        },
        "system_d": system_d,
        "latency_ms": {
            "A_retrieval_mean": round(statistics.mean(lat_a), 1),
            "CE_mean": round(statistics.mean(lat_ce), 1),
            "D_total_mean": round(statistics.mean(lat_total), 1),
            "A_retrieval_median": round(statistics.median(lat_a), 1),
            "CE_median": round(statistics.median(lat_ce), 1),
            "D_total_median": round(statistics.median(lat_total), 1),
        },
        "named_case_audit": named_audit,
        "cross_encoder": {
            "name": CE_NAME,
            "revision": CE_REVISION,
            "artifact_sha256": CE_SHA256,
            "pair_score_stable": ce_stable,
            "max_length": MAX_LENGTH,
        },
        "decision": decision,
        "runtime_seconds": round(time.time() - started, 1),
        "per_case": per_case,
    }

    paired = {
        "rescues": rescues,
        "regressions": regressions,
        "net": net,
        "both_pass": both_pass,
        "both_fail": both_fail,
        "n_rescues": len(rescues),
        "n_regressions": len(regressions),
        "n_both_pass": len(both_pass),
        "n_both_fail": len(both_fail),
        "recorded_A_strict": "30/40",
        "D_strict": system_d["strict_recall_at_10"],
        "delta_strict_cases": system_d["cases_fully_recalled"] - 30,
        "bootstrap": boot,
        "mcnemar": mc,
        "rank_destruction": {
            "a_rank_le_3_out_of_top_10": dest_head,
            "rank1_destroyed": dest_rank1,
            "count_head": len(dest_head),
            "count_rank1": len(dest_rank1),
        },
        "decision": decision,
    }

    regression_analysis = {
        "note": (
            "Every rescue and every regression vs recorded EVAL-VAL-001 SYSTEM-A. "
            "exact_match_guard_triggered is False for all: SYSTEM-D is the frozen "
            "0.7/0.3 score blend, not the clamp. identifier_overlap is the EXP-016 "
            "matcher diagnostic."
        ),
        "rescues": [m for m in movement_details if m["movement"] == "RESCUE"],
        "regressions": [m for m in movement_details if m["movement"] == "REGRESSION"],
        "classification_counts": {},
        "named_dev_only_audit": named_audit,
    }
    counts = {}
    for m in movement_details:
        counts[m["classification"]] = counts.get(m["classification"], 0) + 1
    regression_analysis["classification_counts"] = counts

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results_path = OUT_DIR / "EVAL-VAL-002-results.json"
    paired_path = OUT_DIR / "EVAL-VAL-002-paired-analysis.json"
    regr_path = OUT_DIR / "EVAL-VAL-002-regression-analysis.json"
    report_path = OUT_DIR / "EVAL-VAL-002-report.md"
    env_path = OUT_DIR / "EVAL-VAL-002-environment.json"
    pools_path = OUT_DIR / "EVAL-VAL-002-pools.jsonl"
    exp016_copy = EXP016_DIR / "EXP-016-validation-results.json"

    results_path.write_text(json.dumps(results, indent=2, default=str) + "\n", encoding="utf-8")
    paired_path.write_text(json.dumps(paired, indent=2, default=str) + "\n", encoding="utf-8")
    regr_path.write_text(
        json.dumps(regression_analysis, indent=2, default=str) + "\n", encoding="utf-8"
    )
    pools_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in compact_pools) + "\n",
        encoding="utf-8",
    )

    # compact copy for EXP-016 without the full per_case dump duplicated
    exp016_payload = {
        k: v for k, v in results.items() if k != "per_case"
    }
    exp016_payload["per_case_path"] = "experiments/EVAL-VAL-002/EVAL-VAL-002-results.json"
    exp016_payload["paired"] = paired
    exp016_copy.write_text(
        json.dumps(exp016_payload, indent=2, default=str) + "\n", encoding="utf-8"
    )

    freeze_after = json.loads(FREEZE.read_text(encoding="utf-8"))
    if freeze_after != freeze:
        raise SystemExit("STOP: SYSTEM-D freeze file changed during the run")
    if freeze_after["config_hash"] != EXPECTED_D_HASH:
        raise SystemExit("STOP: freeze hash changed during the run")

    # environment fingerprint
    freeze_pip = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    deps = {}
    for line in freeze_pip.splitlines():
        if "==" in line:
            name, ver = line.split("==", 1)
            if name.lower() in {
                "numpy",
                "psycopg",
                "pgvector",
                "onnxruntime",
                "tokenizers",
                "scikit-learn",
                "pytest",
                "ruff",
                "pydantic",
            }:
                deps[name] = ver
    try:
        git_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip() or None
    except Exception:
        git_commit = None

    env = {
        "experiment_id": "EVAL-VAL-002",
        "timestamp": results["timestamp"],
        "git_commit": git_commit,
        "host": {
            "os": platform.platform(),
            "python": sys.version.split()[0],
            "executable": sys.executable,
        },
        "corpus_snapshot": SNAPSHOT,
        "chunk_set": CHUNK_SET,
        "transformer_model": TRANSFORMER_MODEL,
        "transformer_fingerprint": TRANSFORMER_FINGERPRINT,
        "system_a_hash": a_hash,
        "system_d_hash": d_hash,
        "system_d_hash_matched_freeze": True,
        "cross_encoder": {
            "name": CE_NAME,
            "revision": CE_REVISION,
            "artifact_sha256": CE_SHA256,
        },
        "blend_weights": [BLEND_CE, BLEND_A],
        "candidate_pool": CANDIDATE_POOL,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_samples": BOOTSTRAP_SAMPLES,
        "dependencies": deps,
        "embedding": emb,
        "holdout_access_log_bytes": holdout_log_bytes(),
        "holdout_runs": 0,
        "runtime_seconds": results["runtime_seconds"],
        "latency_ms": results["latency_ms"],
        "d_runs": 1,
        "freeze_untouched": True,
    }
    env_path.write_text(json.dumps(env, indent=2) + "\n", encoding="utf-8")

    # report
    def movement_table(items: list[dict]) -> str:
        if not items:
            return "(none)"
        lines = [
            "| case | A ranks (stored) | D ranks | CE score(s) | id-overlap | guard triggered | all spans in D@10 | class |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for m in items:
            a_ranks = [s["a_rank_stored"] for s in m["spans"]]
            d_ranks = [s["d_rank"] for s in m["spans"]]
            ce_s = [
                f"{s['ce_score']:.4f}" if s["ce_score"] is not None else "None"
                for s in m["spans"]
            ]
            overlap = [bool(s["identifier_overlap"]) for s in m["spans"]]
            lines.append(
                f"| `{m['case_id']}` | {a_ranks} | {d_ranks} | {ce_s} | {overlap} | "
                f"False (blend) | {m['all_required_spans_in_d_top_10']} | "
                f"{m['classification']} |"
            )
        return "\n".join(lines)

    named_lines = []
    for cid, info in named_audit.items():
        named_lines.append(f"- **{cid}**: {info['status']}")

    d_strict = system_d["cases_fully_recalled"]
    report = f"""# EVAL-VAL-002 — validation of frozen SYSTEM-D-GUARD-BLEND

## {decision['label']}

{decision['reason']}

This is a measurement of the already-frozen SYSTEM-D against recorded EVAL-VAL-001 SYSTEM-A. SYSTEM-D was not modified. Holdout was not loaded.

## Setup

- Split: `evals/splits/gold150-v1/validation.json` n=40. Projection `validation.jsonl`.
- SYSTEM-A: recorded EVAL-VAL-001, **30/40** strict Recall@10, macro span recall **0.75**, doc recall **0.975**, MRR **0.5283**. Not rerun as an evaluation. A top-100 was retrieved only as D candidate generation.
- SYSTEM-D: freeze `experiments/EXP-016/SYSTEM-D-GUARD.json`, implementation SYSTEM-D-GUARD-BLEND, config hash `{d_hash}` verified **before scoring**.
- Weights: 0.7 minmax CE + 0.3 minmax SYSTEM-A fused RRF, pool 100, tie-break blend desc / A rank / chunk_id.
- CE: `{CE_NAME}` rev `{CE_REVISION}`, onnx sha256 `{CE_SHA256}`.
- Encoder fingerprint: `{TRANSFORMER_FINGERPRINT}`.
- D scored **exactly once** on the 40 cases.
- Holdout access log: **{holdout_log_bytes()} bytes**. holdout_runs = **0**.

## Named-case audit (HA-22, HA-24, GOLD-B005-11)

These three were the EXP-015/016 development traces. They are **not** in the validation set.

{chr(10).join(named_lines)}

They were not looked up in holdout.

## Primary endpoint — strict full-case recall@10

| system | fully recalled | of | percentage |
| --- | ---: | ---: | ---: |
| SYSTEM-A-GLOBAL (recorded EVAL-VAL-001) | **30** | 40 | 75.0% |
| SYSTEM-D-GUARD-BLEND | **{d_strict}** | 40 | {round(100 * d_strict / 40, 1)}% |
| difference (D−A) | {d_strict - 30:+d} | | {round(100 * (d_strict - 30) / 40, 1):+.1f} pp |

## Secondary metrics

| | SYSTEM-A (recorded) | SYSTEM-D |
| --- | ---: | ---: |
| macro span recall@10 | 0.75 | {system_d['macro_span_recall']} |
| spans retrieved | {stored_a['spans_found_at_10']}/{stored_a['spans_total']} | {system_d['spans_found_at_10']}/{system_d['spans_total']} |
| document recall | 0.975 | {system_d['document_recall']} |
| MRR | 0.5283 | {system_d['mrr']} |
| spans absent@10 | {stored_a['spans_absent_from_top']['10']} | {system_d['spans_absent_from_top']['10']} |
| latency mean (ms) | (recorded A retrieval ~653) | {results['latency_ms']['D_total_mean']} |

Rematerialized A gold-span rank mismatches vs recorded: **{len(a_rank_mismatches)}**. Rematerialized A strict (candidate-gen only, not a new eval): {remat_a_strict}/40.

## Paired analysis vs recorded A

- **rescues ({len(rescues)})**: {rescues or 'none'}
- **regressions ({len(regressions)})**: {regressions or 'none'}
- both pass: {len(both_pass)}, both fail: {len(both_fail)}
- net: **{net:+d}**

### Statistics

Paired bootstrap over 40 questions, 10000 resamples, seed `20250818`, on the 40 paired strict 0/1 outcomes (D−A).

| quantity | point estimate | 95% CI |
| --- | ---: | --- |
| strict fully-recalled delta per case | {boot['fully_recalled_delta_per_case']['point_estimate']} | {boot['fully_recalled_delta_per_case']['ci95']} |
| macro span-recall delta | {boot['macro_recall_delta']['point_estimate']} | {boot['macro_recall_delta']['ci95']} |

McNemar exact (discordant strict outcomes): discordant={mc['discordant_pairs']}, D-only={mc['d_only']}, A-only={mc['a_only']}, p={mc['p_value']}.

Rank-1 gold destructions (A rank 1 out of D top 10): {len(dest_rank1)}.
A-rank≤3 gold spans out of D top 10: {len(dest_head)}.

## Rescues

{movement_table([m for m in movement_details if m['movement']=='RESCUE'])}

## Regressions

{movement_table([m for m in movement_details if m['movement']=='REGRESSION'])}

### Classification notes

Exact-match guard (EXP-016 clamp) did **not** trigger on any case: SYSTEM-D is the frozen score blend. Identifier overlap is diagnostic only.

{chr(10).join(f"- `{m['case_id']}` {m['movement']}: **{m['classification']}** — {m['why']}" for m in movement_details) or "- none"}

## Decision

**{decision['label']}**

{decision['reason']}

Holdout was not run. Stop after this report.

## Files

- `experiments/EVAL-VAL-002/EVAL-VAL-002-results.json`
- `experiments/EVAL-VAL-002/EVAL-VAL-002-paired-analysis.json`
- `experiments/EVAL-VAL-002/EVAL-VAL-002-regression-analysis.json`
- `experiments/EVAL-VAL-002/EVAL-VAL-002-environment.json`
- `experiments/EVAL-VAL-002/EVAL-VAL-002-report.md`
- `experiments/EXP-016/EXP-016-validation-results.json`
"""
    report_path.write_text(report, encoding="utf-8")

    print()
    print(f"D strict {system_d['strict_recall_at_10']} delta {d_strict - 30:+d}")
    print(f"rescues {rescues} regressions {regressions} net {net:+d}")
    print(f"bootstrap strict CI {boot['fully_recalled_delta_per_case']['ci95']}")
    print(f"McNemar p={mc['p_value']} discordant={mc['discordant_pairs']}")
    print(f"decision {decision['label']}")
    print(f"holdout_log={holdout_log_bytes()} bytes")
    print(f"named {named_audit}")
    print(f"wrote {results_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
