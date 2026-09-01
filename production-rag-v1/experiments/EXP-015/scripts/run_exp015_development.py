#!/usr/bin/env python3
"""EXP-015 development qualification: SYSTEM-A vs SYSTEM-C on gold150-v1 development.

Does not load validation. Does not load holdout. Does not tune after seeing scores.
SYSTEM-C is a reorder of frozen SYSTEM-A fused candidates (pool 100, pool_per_retriever
50, rrf_k 60). Candidate generation is the project's lexical_search / dense_search /
rrf_fuse; BM25 and RRF are not reimplemented here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from cross_encoder import (  # noqa: E402
    CE_NAME,
    CE_ONNX,
    CE_REVISION,
    CE_SHA256,
    MAX_LENGTH,
    CrossEncoderReranker,
    rerank,
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
    SYSTEM_A_GLOBAL,
    TRANSFORMER_FINGERPRINT,
    TRANSFORMER_MODEL,
    system_config_hash,
)
from rag_v1.types import EvidenceRef, SearchHit  # noqa: E402

PROBE_DEPTHS = (10, 20, 30, 50, 100, 300)
TOP_K, RRF_POOL, RRF_K, CANDIDATE_POOL = 10, 50, 60, 100
HISTORICAL_EXPECTED = {
    "cases_fully_recalled": 15,
    "cases_total": 20,
    "macro_span_recall": 0.775,
    "spans_found_at_10": 17,
    "document_recall": 0.925,
    "mrr": 0.449,
}
A_HASH = "9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38"


def overlaps(hit: SearchHit, ref: EvidenceRef) -> bool:
    return (
        hit.version_id == ref.version_id
        and hit.section_path == ref.section_path
        and hit.char_start < ref.char_end
        and hit.char_end > ref.char_start
    )


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
                "within": {str(d): (hit is not None and hit.rank <= d) for d in PROBE_DEPTHS},
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


def retrieve_system_a_pool(query: str, embedder) -> list[SearchHit]:
    lexical = lexical_search(query, SNAPSHOT, RRF_POOL)
    dense = dense_search(
        query, SNAPSHOT, TRANSFORMER_MODEL, RRF_POOL, embedder=embedder
    )
    return rrf_fuse([lexical, dense], rrf_k=RRF_K, top_k=CANDIDATE_POOL)


def identity_ok(summary: dict) -> tuple[bool, list[str]]:
    mismatches = []
    if summary["cases_fully_recalled"] != HISTORICAL_EXPECTED["cases_fully_recalled"]:
        mismatches.append(
            f"strict {summary['cases_fully_recalled']}/{summary['cases_total']} "
            f"!= {HISTORICAL_EXPECTED['cases_fully_recalled']}/20"
        )
    if abs(summary["macro_span_recall"] - HISTORICAL_EXPECTED["macro_span_recall"]) > 1e-6:
        mismatches.append(
            f"macro_span_recall {summary['macro_span_recall']} != "
            f"{HISTORICAL_EXPECTED['macro_span_recall']}"
        )
    if abs(summary["mrr"] - HISTORICAL_EXPECTED["mrr"]) > 5e-4:
        mismatches.append(f"mrr {summary['mrr']} != {HISTORICAL_EXPECTED['mrr']}")
    if summary["spans_found_at_10"] != HISTORICAL_EXPECTED["spans_found_at_10"]:
        mismatches.append(
            f"spans_found_at_10 {summary['spans_found_at_10']} != "
            f"{HISTORICAL_EXPECTED['spans_found_at_10']}"
        )
    if abs(summary["document_recall"] - HISTORICAL_EXPECTED["document_recall"]) > 1e-6:
        mismatches.append(
            f"document_recall {summary['document_recall']} != "
            f"{HISTORICAL_EXPECTED['document_recall']}"
        )
    return not mismatches, mismatches


def apply_gates(system_a: dict, system_c: dict, per_case_compare: list[dict],
                repro: dict) -> dict:
    """Preregistered qualitative gates, operationalised before looking at C scores.

    These thresholds are the only reading of the preregistration's four bullets that
    can be applied without a validation sweep:
    - positive net rescues: C-only full@10 minus A-only full@10 > 0
    - no catastrophic regression pattern: regressions < 3 and no mass destruction of
      A rank-1 cases (more than one rank-1 A hit dropped out of C top-10)
    - enough pool headroom: at least one A-miss@10 whose gold spans all sit in the
      fused pool of 100 (perfect reranker could rescue a case)
    - reproducibility: encoder/A-hash/CE-hash/row-count/historical-A identity
    """
    rescues = [r["case_id"] for r in per_case_compare if r["c_full"] and not r["a_full"]]
    regressions = [r["case_id"] for r in per_case_compare if r["a_full"] and not r["c_full"]]
    net = len(rescues) - len(regressions)
    rank1_destroyed = [
        r["case_id"]
        for r in per_case_compare
        if r["a_full"]
        and not r["c_full"]
        and any(s.get("a_rank") == 1 for s in r["spans"])
    ]
    headroom_cases = [
        r["case_id"]
        for r in per_case_compare
        if (not r["a_full"]) and r["all_spans_in_pool"]
    ]
    ceiling = sum(1 for r in per_case_compare if r["pool_full_at_100"])
    a_strict = system_a["cases_fully_recalled"]
    c_strict = system_c["cases_fully_recalled"]

    g_net = net > 0
    g_cat = len(regressions) < 3 and len(rank1_destroyed) <= 1
    g_head = len(headroom_cases) >= 1 and ceiling > a_strict
    g_repro = bool(repro.get("passed"))
    passed = g_net and g_cat and g_head and g_repro
    return {
        "positive_net_rescues": {
            "pass": g_net,
            "net": net,
            "rescues": rescues,
            "regressions": regressions,
            "rule": "net = rescues - regressions > 0 on strict Recall@10",
        },
        "no_catastrophic_regression_pattern": {
            "pass": g_cat,
            "regressions": regressions,
            "rank1_destroyed": rank1_destroyed,
            "rule": (
                "fail if regressions >= 3 or more than one A rank-1 case is dropped "
                "from C top-10"
            ),
        },
        "enough_pool_headroom": {
            "pass": g_head,
            "a_strict": a_strict,
            "perfect_reranker_pool_100": ceiling,
            "headroom_cases": headroom_cases,
            "rule": (
                "at least one A-miss@10 with every gold span inside fused pool 100, "
                "so ceiling@100 > A@10"
            ),
        },
        "reproducibility_checks": {
            "pass": g_repro,
            "details": repro,
        },
        "passed": passed,
        "decision": "PROCEED_TO_VALIDATION" if passed else "RERANKER_REJECTED_AT_DEV",
        "a_strict": a_strict,
        "c_strict": c_strict,
        "note": "Gates applied once. No post-score retuning.",
    }


def holdout_log_bytes() -> int:
    path = Path("evals/splits/gold150-v1/holdout-access.log.jsonl")
    return path.stat().st_size if path.exists() else -1


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--development-jsonl",
        default="experiments/EXP-015/development.jsonl",
    )
    parser.add_argument(
        "--historical-jsonl",
        default="evals/development/v1.jsonl",
        help="Recorded 15/20 SYSTEM-A identity split (EXP-014R / EVAL-VAL-001), not gold150-v1",
    )
    parser.add_argument("--skip-historical-identity", action="store_true")
    parser.add_argument(
        "--out", default="experiments/EXP-015/EXP-015-development-results.json"
    )
    parser.add_argument(
        "--freeze-out", default="experiments/EXP-015/SYSTEM-C-RERANK.json"
    )
    args = parser.parse_args()

    started = time.time()
    a_hash = FROZEN_HASHES["SYSTEM-A-GLOBAL"]
    if a_hash != A_HASH:
        raise SystemExit(f"STOP: SYSTEM-A hash {a_hash} != {A_HASH}")

    emb = embedding_status()
    if not emb["complete"]:
        raise SystemExit(f"STOP: embeddings incomplete: {emb}")

    encoder = TransformerEncoder(max_seq=512).load()
    if encoder.model_version != TRANSFORMER_FINGERPRINT:
        raise SystemExit("STOP: live encoder fingerprint mismatch")
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)

    identity = {"ran": False, "passed": False}
    if not args.skip_historical_identity:
        hist_cases = [c for c in load_cases(Path(args.historical_jsonl)) if c.expected_evidence]
        hist_scored = {}
        for case in hist_cases:
            hits = retrieve_system_a_pool(case.question, transformer)
            hist_scored[case.case_id] = score_case(case, hits)
        hist_summary = summarise(hist_scored, "SYSTEM-A-GLOBAL", a_hash)
        ok, mismatches = identity_ok(hist_summary)
        identity = {
            "ran": True,
            "split": args.historical_jsonl,
            "note": (
                "EVAL-VAL-001 recorded development A=15/20 on this historical AN/OA "
                "split, not on gold150-v1 development.json. This is the encoder/"
                "SYSTEM-A identity check. gold150-v1 development is the EXP-015 split."
            ),
            "passed": ok,
            "mismatches": mismatches,
            "observed": {
                k: hist_summary[k]
                for k in (
                    "cases_fully_recalled",
                    "cases_total",
                    "macro_span_recall",
                    "spans_found_at_10",
                    "spans_total",
                    "document_recall",
                    "mrr",
                    "strict_recall_at_10",
                )
            },
            "expected": HISTORICAL_EXPECTED,
        }
        if not ok:
            payload = {
                "experiment_id": "EXP-015",
                "status": "STOPPED_SYSTEM_A_IDENTITY_FAILED",
                "identity_reproduction": identity,
                "embedding": emb,
                "holdout_access_log_bytes": holdout_log_bytes(),
                "holdout_loaded": False,
                "validation_loaded": False,
            }
            Path(args.out).write_text(
                json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
            )
            print("STOP: SYSTEM-A historical identity did not reproduce 15/20")
            print(json.dumps(identity, indent=2))
            return 2

    ce = CrossEncoderReranker()
    # Reproducibility: same pair twice.
    probe_q, probe_p = "What is BM25?", "BM25 is a lexical ranking function."
    s1 = ce.score_pairs(probe_q, [probe_p])[0]
    s2 = ce.score_pairs(probe_q, [probe_p])[0]
    ce_stable = s1 == s2

    cases = [c for c in load_cases(Path(args.development_jsonl)) if c.expected_evidence]
    if len(cases) != 20:
        raise SystemExit(f"expected 20 development cases, got {len(cases)}")

    a_cases, c_cases = {}, {}
    lat_a, lat_c, lat_ce = [], [], []
    compare = []

    for case in cases:
        q = case.question
        t0 = time.time()
        pool = retrieve_system_a_pool(q, transformer)
        lat_a.append((time.time() - t0) * 1000)
        a_cases[case.case_id] = score_case(case, pool)

        t0 = time.time()
        c_hits, ce_scores = rerank(pool, q, ce, top_k=len(pool))
        ce_ms = (time.time() - t0) * 1000
        lat_ce.append(ce_ms)
        lat_c.append(lat_a[-1] + ce_ms)
        # Score the full reranked pool so probe depths and MRR match SYSTEM-A's convention.
        c_cases[case.case_id] = score_case(case, c_hits)

        score_by_chunk = {h.chunk_id: sc for h, sc in zip(pool, ce_scores, strict=True)}
        c_rank_by_chunk = {h.chunk_id: h.rank for h in c_hits}
        span_rows = []
        for i, ref in enumerate(case.expected_evidence):
            a_hit = next((h for h in pool if overlaps(h, ref)), None)
            pool_rank = a_hit.rank if a_hit else None
            a_rank = pool_rank if pool_rank is not None and pool_rank <= TOP_K else None
            c_rank = c_rank_by_chunk.get(a_hit.chunk_id) if a_hit else None
            ce_score = score_by_chunk.get(a_hit.chunk_id) if a_hit else None
            span_rows.append(
                {
                    "span_index": i,
                    "a_rank": a_rank,
                    "pool_rank": pool_rank,
                    "c_rank": c_rank,
                    "c_in_top_10": c_rank is not None and c_rank <= TOP_K,
                    "ce_score": ce_score,
                    "chunk_id": a_hit.chunk_id if a_hit else None,
                }
            )
        all_in_pool = all(s["pool_rank"] is not None for s in span_rows)
        pool_full = bool(span_rows) and all(
            s["pool_rank"] is not None and s["pool_rank"] <= CANDIDATE_POOL for s in span_rows
        )
        compare.append(
            {
                "case_id": case.case_id,
                "a_full": a_cases[case.case_id]["fully_recalled"],
                "c_full": c_cases[case.case_id]["fully_recalled"],
                "a_recall": a_cases[case.case_id]["recall"],
                "c_recall": c_cases[case.case_id]["recall"],
                "pool_size": len(pool),
                "all_spans_in_pool": all_in_pool,
                "pool_full_at_100": pool_full,
                "spans": span_rows,
                "latency_ms": {
                    "system_a_retrieval": round(lat_a[-1], 2),
                    "cross_encoder": round(ce_ms, 2),
                    "system_c_total": round(lat_c[-1], 2),
                },
            }
        )

    system_a = summarise(a_cases, "SYSTEM-A-GLOBAL", a_hash)
    # SYSTEM-C hash is written at freeze time from the frozen config object.
    system_c_config = {
        "name": "SYSTEM-C-RERANK",
        "description": (
            "SYSTEM-A fused candidates (pool 100) reordered by pretrained "
            "cross-encoder/ms-marco-MiniLM-L6-v2; top 10. No new passages."
        ),
        "control": "SYSTEM-A-GLOBAL",
        "system_a_config_hash": a_hash,
        "snapshot": SNAPSHOT,
        "chunk_set": CHUNK_SET,
        "candidate_generation": {
            "lexical": SYSTEM_A_GLOBAL["stage_2"]["lexical"],
            "dense": SYSTEM_A_GLOBAL["stage_2"]["dense"],
            "fusion": {"method": "rrf", "rrf_k": RRF_K, "pool_per_retriever": RRF_POOL},
            "candidate_pool": CANDIDATE_POOL,
            "may_retrieve_new_passages": False,
        },
        "cross_encoder": {
            "name": CE_NAME,
            "revision": CE_REVISION,
            "artifact": str(CE_ONNX),
            "artifact_sha256": CE_SHA256,
            "runtime": "onnxruntime + HuggingFace tokenizers",
            "precision": "fp32",
            "max_length": MAX_LENGTH,
            "pair_formatting": "[CLS] query [SEP] passage [SEP]",
            "truncation": "longest_first",
            "scoring": "raw sequence-classification logit (Identity); higher=more relevant",
            "tie_break": "score desc, then SYSTEM-A fused rank asc, then chunk_id asc",
        },
        "top_k": TOP_K,
        "reranker": CE_NAME,
        "query": "raw user question, verbatim",
    }
    c_hash = config_hash(system_c_config)
    system_c = summarise(c_cases, "SYSTEM-C-RERANK", c_hash)

    repro = {
        "passed": True,
        "system_a_hash": a_hash,
        "system_a_hash_ok": a_hash == A_HASH,
        "encoder_fingerprint": encoder.model_version,
        "encoder_fingerprint_ok": encoder.model_version == TRANSFORMER_FINGERPRINT,
        "embedding": emb,
        "cross_encoder_sha256": ce.artifact_sha256,
        "cross_encoder_sha256_ok": ce.artifact_sha256 == CE_SHA256,
        "ce_pair_score_stable": ce_stable,
        "historical_identity": identity,
        "holdout_access_log_bytes": holdout_log_bytes(),
        "holdout_loaded": False,
        "validation_loaded": False,
    }
    repro["passed"] = (
        repro["system_a_hash_ok"]
        and repro["encoder_fingerprint_ok"]
        and emb["complete"]
        and repro["cross_encoder_sha256_ok"]
        and ce_stable
        and identity.get("passed", False)
        and holdout_log_bytes() == 0
    )

    gates = apply_gates(system_a, system_c, compare, repro)

    rescues = gates["positive_net_rescues"]["rescues"]
    regressions = gates["positive_net_rescues"]["regressions"]

    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:  # noqa: BLE001
        commit = None

    dep_fp = config_hash(
        {
            "system_a_hash": a_hash,
            "encoder_fingerprint": TRANSFORMER_FINGERPRINT,
            "encoder_model_id": TRANSFORMER_MODEL,
            "ce_name": CE_NAME,
            "ce_revision": CE_REVISION,
            "ce_sha256": CE_SHA256,
            "pool": CANDIDATE_POOL,
            "pool_per_retriever": RRF_POOL,
            "rrf_k": RRF_K,
            "top_k": TOP_K,
            "pair": "[CLS] query [SEP] passage [SEP]",
            "truncation": "longest_first/512",
            "tie_break": "score desc, A-rank asc, chunk_id asc",
            "scoring": "raw logit",
            "snapshot": SNAPSHOT,
            "chunk_set": CHUNK_SET,
        }
    )

    payload = {
        "experiment_id": "EXP-015",
        "phase": "development_qualification",
        "split": "gold150-v1/development",
        "split_path": "evals/splits/gold150-v1/development.json",
        "projection_path": args.development_jsonl,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "corpus_snapshot": SNAPSHOT,
        "chunk_set": CHUNK_SET,
        "system_a_config_hash": a_hash,
        "system_c_config_hash": c_hash,
        "tuned_after_seeing_scores": False,
        "validation_loaded": False,
        "holdout_loaded": False,
        "holdout_access_log_bytes": holdout_log_bytes(),
        "embedding": emb,
        "identity_reproduction": identity,
        "system_a": {k: v for k, v in system_a.items() if k != "cases"} | {"cases": system_a["cases"]},
        "system_c": {k: v for k, v in system_c.items() if k != "cases"} | {"cases": system_c["cases"]},
        "paired": {
            "rescues_C_over_A": rescues,
            "regressions_C_vs_A": regressions,
            "net_cases": len(rescues) - len(regressions),
            "both_correct": [
                r["case_id"] for r in compare if r["a_full"] and r["c_full"]
            ],
            "neither": [
                r["case_id"] for r in compare if (not r["a_full"]) and (not r["c_full"])
            ],
            "macro_span_recall_delta": round(
                system_c["macro_span_recall"] - system_a["macro_span_recall"], 4
            ),
        },
        "per_case": compare,
        "latency_ms": {
            "A_mean": round(statistics.mean(lat_a), 1) if lat_a else None,
            "C_mean": round(statistics.mean(lat_c), 1) if lat_c else None,
            "CE_mean": round(statistics.mean(lat_ce), 1) if lat_ce else None,
            "A_median": round(statistics.median(lat_a), 1) if lat_a else None,
            "C_median": round(statistics.median(lat_c), 1) if lat_c else None,
            "CE_median": round(statistics.median(lat_ce), 1) if lat_ce else None,
        },
        "gates": gates,
        "system_c_config": system_c_config,
        "dependency_fingerprint": dep_fp,
        "runtime_seconds": round(time.time() - started, 1),
        "frozen": False,
        "freeze_path": None,
    }

    if gates["passed"]:
        freeze = {
            "name": "SYSTEM-C-RERANK",
            "frozen_at": payload["timestamp"],
            "frozen_before_validation_load": True,
            "validation_loaded": False,
            "holdout_loaded": False,
            "config": system_c_config,
            "config_hash": c_hash,
            "dependency_fingerprint": dep_fp,
            "system_a_config_hash": a_hash,
            "snapshot": SNAPSHOT,
            "chunk_set": CHUNK_SET,
            "encoder": {
                "model_id": TRANSFORMER_MODEL,
                "fingerprint": TRANSFORMER_FINGERPRINT,
                "max_seq_length": 512,
            },
            "cross_encoder": system_c_config["cross_encoder"],
            "candidate_pool": CANDIDATE_POOL,
            "pool_per_retriever": RRF_POOL,
            "rrf_k": RRF_K,
            "top_k": TOP_K,
            "pair_formatting": "[CLS] query [SEP] passage [SEP]",
            "truncation": "max_length=512, longest_first",
            "tie_break": "score desc, then SYSTEM-A fused rank asc, then chunk_id asc",
            "scoring": "raw sequence-classification logit (Identity)",
            "development_metrics": {
                "strict_recall_at_10": system_c["strict_recall_at_10"],
                "macro_span_recall": system_c["macro_span_recall"],
                "mrr": system_c["mrr"],
                "document_recall": system_c["document_recall"],
            },
            "gates": {"passed": True, "decision": gates["decision"]},
            "note": (
                "Frozen after development qualification passed. Validation must not be "
                "loaded until this freeze file has been inspected."
            ),
        }
        freeze_path = Path(args.freeze_out)
        freeze_path.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
        payload["frozen"] = True
        payload["freeze_path"] = str(freeze_path)
    else:
        payload["reranker_rejected_at_dev"] = True
        payload["rejected_note"] = (
            "RERANKER_REJECTED-at-dev. SYSTEM-C is not frozen as a promoted system. "
            "Validation was not run."
        )
        Path(args.freeze_out).with_name("RERANKER_REJECTED-at-dev.json").write_text(
            json.dumps(
                {
                    "status": "RERANKER_REJECTED-at-dev",
                    "frozen": False,
                    "validation_loaded": False,
                    "gates": gates,
                    "timestamp": payload["timestamp"],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Drop full case dumps' hit text is already not stored; ranks only.
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    print(
        f"SYSTEM-A  {system_a['strict_recall_at_10']}  "
        f"spanR={system_a['macro_span_recall']:.3f} MRR={system_a['mrr']:.3f}"
    )
    print(
        f"SYSTEM-C  {system_c['strict_recall_at_10']}  "
        f"spanR={system_c['macro_span_recall']:.3f} MRR={system_c['mrr']:.3f}"
    )
    print(
        f"rescues {rescues}  regressions {regressions}  net "
        f"{len(rescues) - len(regressions):+d}"
    )
    print(f"gates {gates['decision']} passed={gates['passed']}")
    print(f"frozen={payload['frozen']}  holdout_log={holdout_log_bytes()} bytes")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
