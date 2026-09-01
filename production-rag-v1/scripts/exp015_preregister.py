#!/usr/bin/env python3
"""EXP-015: preregister the reranker contract, and record the model-acquisition result.

The preregistration is written before any reranker has been chosen or run — which is the
order the brief requires and the only order in which a preregistration means anything.
It fixes the candidate pool, the qualification rule, the freeze procedure and the
promotion criteria so that none of them can be chosen after seeing a number.

The acquisition survey is recorded in the same document because it determines whether
the experiment can proceed at all, and because a blocked experiment that is documented is
worth more than one that is quietly replaced with something easier.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.systems import CHUNK_SET, FROZEN_HASHES, SNAPSHOT, SYSTEM_A_GLOBAL

OUT = Path("experiments/EXP-015")
MANIFEST_HASH = "452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17"
POOL = 100
SEED = 20250818
BOOTSTRAP_SAMPLES = 10000

#: §11. Every host that could serve a pretrained cross-encoder, and what it answered.
#: Recorded verbatim so the conclusion can be rechecked rather than believed.
ACQUISITION_SURVEY = [
    {"host": "huggingface.co", "result": "CONNECT 403",
     "verdict": "BLOCKED by egress policy",
     "evidence": "proxy status lists huggingface.co:443 under recentRelayFailures as "
                 "connect_rejected / gateway answered 403 to CONNECT"},
    {"host": "cdn.jsdelivr.net", "result": "CONNECT 403",
     "verdict": "BLOCKED by egress policy",
     "evidence": "same proxy failure record"},
    {"host": "github.com / objects.githubusercontent.com", "result": "400 / 403",
     "verdict": "release assets not retrievable"},
    {"host": "chroma-onnx-models.s3.amazonaws.com", "result": "200 for the EXP-009 "
     "bi-encoder bundle; 403 for every cross-encoder key tried",
     "verdict": "REACHABLE but hosts no cross-encoder",
     "evidence": "all-MiniLM-L6-v2/onnx.tar.gz returns 200, so the host is not blocked; "
                 "ms-marco-MiniLM-L-6-v2 and bge-reranker keys return 403 (no such key)"},
    {"host": "storage.googleapis.com/qdrant-fastembed", "result": "403 for concrete "
     "reranker objects", "verdict": "not retrievable"},
    {"host": "pypi.org / files.pythonhosted.org", "result": "200",
     "verdict": "REACHABLE — but no PyPI wheel bundles cross-encoder weights; "
                "flashrank and fastembed both resolve their weights from "
                "huggingface.co, which is blocked"},
]


def preregistration() -> dict:
    return {
        "document": "EXP-015 — cross-encoder reranking of SYSTEM-A: preregistration",
        "written_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "PREREGISTERED — written before any reranker was selected or run",
        "hypothesis": (
            "SYSTEM-A's validation failures are dominated by "
            "WITHIN_DOCUMENT_PASSAGE_FAILURE, not by document routing: document recall "
            "is 0.975 while span recall is 0.750. If that gap is a ranking problem, a "
            "pretrained cross-encoder reranking SYSTEM-A's own candidates should close "
            "part of it without changing retrieval."),
        "control": {
            "system": "SYSTEM-A-GLOBAL",
            "config_hash": FROZEN_HASHES["SYSTEM-A-GLOBAL"],
            "unchanged": True,
            "validation_baseline": {"strict_full_case": 30, "cases": 40,
                                    "macro_span_recall": 0.750,
                                    "document_recall": 0.975, "mrr": 0.5283},
        },
        "experimental_system": {
            "name": "SYSTEM-C-RERANK",
            "pipeline": ["SYSTEM-A candidate retrieval (unchanged)",
                         "cross-encoder rerank of those candidates only",
                         "take top 10"],
            "may": ["reorder candidates SYSTEM-A already retrieved"],
            "may_not": ["invent candidates", "run another retrieval method",
                        "change the query", "change chunks", "change BM25",
                        "change dense retrieval", "change RRF", "change the corpus"],
        },
        "candidate_pool": {
            "size": POOL,
            "rationale": (
                "Validation diagnostics place missed SYSTEM-A evidence at ranks 11, 12, "
                "14, 14, 22, 23, 24, 25, 31 and 73. A pool of 10 cannot test reranking "
                "at all, and 100 covers every observed rank while remaining below the "
                "point where top-k becomes the metric."),
            "frozen_before_selection": True,
            "sweeping_forbidden": "The pool is not swept on validation.",
        },
        "model_policy": {
            "must_be": ["genuinely pretrained for relevance or ranking",
                        "zero-shot for this experiment",
                        "reproducible from a pinned artifact"],
            "must_not_be": ["trained on GOLD", "fine-tuned on GOLD",
                            "fitted to GOLD answers or thresholds",
                            "trained on synthetic labels derived from GOLD",
                            "selected on validation performance"],
            "selection_split": "development (20 cases) only",
        },
        "qualification_rule": {
            "split": "development",
            "primary": "strict full-case recall@10",
            "proceed_to_validation_only_if": [
                "positive net rescues on development",
                "no catastrophic regression pattern",
                "measured candidate headroom exists",
                "implementation and reproducibility checks pass"],
            "case_by_case_tuning": "forbidden",
        },
        "freeze_before_validation": [
            "complete SYSTEM-C config and its hash", "reranker model fingerprint",
            "candidate pool", "input formatting", "truncation policy",
            "score transformation", "tie-breaking", "top-k", "dependency fingerprint"],
        "validation_protocol": {
            "split": "validation (40 cases, the same set EVAL-VAL-001 used)",
            "runs": "exactly one, after the freeze",
            "baseline": "the stored SYSTEM-A result; SYSTEM-A is not re-run",
            "statistics": {"paired_bootstrap_resamples": BOOTSTRAP_SAMPLES,
                           "seed": SEED, "ci": "95%",
                           "tests": [("paired bootstrap on strict delta and macro "
                                      "span recall delta"), "McNemar exact"]},
        },
        "promotion_rule": {
            "RERANKER_SUPPORTED": ["C strict recall > A", "positive net rescues",
                                   "no critical gate meaningfully regresses",
                                   "gains attributable to reranking"],
            "RERANKER_NEUTRAL": ["difference small or mixed"],
            "RERANKER_REJECTED": ["C worse", "regressions outweigh rescues",
                                  "substantial exact-match damage"],
            "note": ("No promotion happens in this experiment; the classification "
                     "is returned to the owner."),
        },
        "corpus": {"snapshot": SNAPSHOT, "manifest_hash": MANIFEST_HASH,
                   "chunk_set": CHUNK_SET, "control_chunks": 14209,
                   "anthropic": 12028, "openai": 2181},
        "holdout": {"runs": 0, "frozen": True, "count": 90,
                    "rule": "not loaded, not enumerated, not run — in this experiment "
                            "or any part of it"},
        "validation_set_usage": (
            "EVAL-VAL-001 opened the 40 validation cases for system comparison and "
            "failure analysis. EXP-015 may use them once more, for this preregistered "
            "one-shot frozen comparison, and for nothing iterative. Every final claim "
            "must still come from the untouched 90-case holdout."),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    prereg = preregistration()
    ceiling = json.loads((OUT / "EXP-015-ceiling-analysis.json").read_text())
    prereg["ceiling_analysis"] = {
        "computed_before_model_selection": True,
        "headroom": ceiling["headroom"],
        "pool_100_ceiling": ceiling["ceilings"]["100"]["max_strict_full_case_recall"],
        "baseline": ceiling["baseline"]["strict_full_case"],
        "note": ("Computed from stored candidate ranks only. It establishes that "
                 "reranking has enough headroom to be worth testing, before any model "
                 "was inventoried."),
    }
    acquisition = {
        "document": "EXP-015 — reranker acquisition survey",
        "surveyed_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "requirement": "a genuinely pretrained cross-encoder, runnable offline",
        "local_inventory": {
            "cached_models": [("data/cache/models/exp009/onnx (all-MiniLM-L6-v2 "
                               "bi-encoder, used by SYSTEM-A)"),
                              "data/cache/models/fasttext-wiki-news-subwords-300.gz",
                              "data/cache/embedders/lsa-*.joblib"],
            "cross_encoder_present": False,
            "runtime_available": "onnxruntime 1.29.0",
            "torch_or_transformers_installed": False,
        },
        "hosts": ACQUISITION_SURVEY,
        "conclusion": "NO_PRETRAINED_CROSS_ENCODER_AVAILABLE",
        "consequence": (
            "EXP-015 cannot proceed past model selection. Sections 13 through 20 — "
            "development qualification, the SYSTEM-C freeze, the one-shot validation, "
            "the regression audit and the promotion classification — are not "
            "executable and were not attempted."),
        "what_was_not_done_instead": (
            "No substitute was used. A hand-written lexical or heuristic rescorer is "
            "not a pretrained cross-encoder, and tuning one against the development "
            "set would be the GOLD fitting section 12 forbids. Reporting the blocker "
            "is the correct outcome, not a workaround."),
        "unblocking_options": [
            "Allow huggingface.co through the egress policy for this environment.",
            ("Side-load a cross-encoder ONNX bundle (for example "
             "cross-encoder/ms-marco-MiniLM-L-6-v2) into data/cache/models/ the way "
             "the EXP-009 bi-encoder bundle was supplied."),
            ("Publish the bundle to a reachable object store; "
             "chroma-onnx-models.s3.amazonaws.com is reachable and already serves "
             "the project's bi-encoder."),
        ],
    }
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                            capture_output=True, text=True, check=False).stdout
    environment = {
        "experiment": "EXP-015",
        "generated_at": prereg["written_at"],
        "corpus_snapshot": SNAPSHOT,
        "manifest_hash": MANIFEST_HASH,
        "chunk_set": CHUNK_SET,
        "system_a_hash": FROZEN_HASHES["SYSTEM-A-GLOBAL"],
        "system_b_hash": FROZEN_HASHES["SYSTEM-B-DOC-C"],
        "system_a_config": SYSTEM_A_GLOBAL,
        "bootstrap_seed": SEED,
        "python": sys.version.split()[0],
        "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                     text=True, check=False).stdout.strip(),
        "dependencies": {line.split("==")[0]: line.split("==")[1]
                         for line in freeze.splitlines() if "==" in line
                         and line.split("==")[0].lower() in
                         {"numpy", "psycopg", "pgvector", "onnxruntime", "tokenizers",
                          "pytest", "ruff"}},
        "acquisition": acquisition,
    }
    (OUT / "EXP-015-preregistration.json").write_text(
        json.dumps(prereg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "EXP-015-acquisition-survey.json").write_text(
        json.dumps(acquisition, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "EXP-015-environment.json").write_text(
        json.dumps(environment, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote preregistration, acquisition survey and environment record")
    print(f"  acquisition conclusion: {acquisition['conclusion']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
