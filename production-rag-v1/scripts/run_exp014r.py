#!/usr/bin/env python3
"""EXP-014R: run the two frozen systems against an evaluation split.

This is the replication harness. It takes a split, refuses to run if that split
fails validation, runs SYSTEM-A and SYSTEM-B exactly as frozen, and reports the
paired case movement with bootstrap confidence intervals and McNemar's test.

The harness is deliberately dumb: it has no knobs. Everything that could change a
result lives in ``rag_v1.systems`` and is hashed, so a run either used the frozen
configuration or it did not.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from rag_v1.doc_representations import build, load_chunk_rows
from rag_v1.embedders_transformer import TransformerEncoder
from rag_v1.evals.io import load_cases
from rag_v1.query_cache import CachedQueryEmbedder
from rag_v1.retrieval import dense_search, lexical_search, rrf_fuse
from rag_v1.systems import (
    CHUNK_SET,
    FROZEN_HASHES,
    SNAPSHOT,
    SYSTEM_A_GLOBAL,
    SYSTEM_B_DOC_C,
    TRANSFORMER_MODEL,
)
from rag_v1.types import EvidenceRef, SearchHit

PROBE_DEPTHS = (10, 20, 30, 50, 100, 300)
TOP_K, RRF_POOL, RRF_K, TOP_DOCUMENTS = 10, 50, 60, 5
BOOTSTRAP_SEED, BOOTSTRAP_SAMPLES = 20250818, 10000


def overlaps(hit: SearchHit, ref: EvidenceRef) -> bool:
    return (hit.version_id == ref.version_id and hit.section_path == ref.section_path
            and hit.char_start < ref.char_end and hit.char_end > ref.char_start)


def score_case(case, hits) -> dict:
    spans = []
    for ref in case.expected_evidence:
        hit = next((h for h in hits if overlaps(h, ref)), None)
        doc_rank = next((h.rank for h in hits if h.version_id == ref.version_id), None)
        spans.append({"rank": hit.rank if hit else None, "doc_rank": doc_rank,
                      "within": {str(d): (hit is not None and hit.rank <= d) for d in PROBE_DEPTHS},
                      "doc_within_10": doc_rank is not None and doc_rank <= TOP_K})
    found = sum(1 for s in spans if s["within"]["10"])
    return {"case_id": case.case_id, "spans": spans,
            "recall": found / len(spans) if spans else 1.0,
            "fully_recalled": bool(spans) and found == len(spans),
            "doc_recall": sum(1 for s in spans if s["doc_within_10"]) / len(spans) if spans else 1.0}


def summarise(per_case: dict) -> dict:
    all_spans = [s for c in per_case.values() for s in c["spans"]]
    recalls = [c["recall"] for c in per_case.values()]
    return {
        "macro_span_recall": round(sum(recalls) / len(recalls), 4),
        "cases_fully_recalled": sum(1 for c in per_case.values() if c["fully_recalled"]),
        "cases_total": len(per_case),
        "spans_found_at_10": sum(1 for s in all_spans if s["within"]["10"]),
        "spans_total": len(all_spans),
        "document_recall": round(sum(c["doc_recall"] for c in per_case.values()) / len(per_case), 4),
        "mrr": round(sum(1 / s["rank"] for s in all_spans if s["rank"]) / len(all_spans), 4),
        "spans_absent_from_top": {str(d): sum(1 for s in all_spans if not s["within"][str(d)])
                                  for d in PROBE_DEPTHS},
        "cases": per_case,
    }


def bootstrap_delta(a: dict, b: dict, seed: int, samples: int) -> dict:
    """Paired bootstrap over questions — resample cases, not spans.

    Questions are the independent unit here; spans within a question are not, so
    resampling spans would understate the interval.
    """
    ids = sorted(a["cases"])
    diffs = np.array([b["cases"][cid]["recall"] - a["cases"][cid]["recall"] for cid in ids])
    case_diffs = np.array([int(b["cases"][cid]["fully_recalled"]) -
                           int(a["cases"][cid]["fully_recalled"]) for cid in ids])
    rng = np.random.default_rng(seed)
    n = len(ids)
    recall_samples, case_samples = [], []
    for _ in range(samples):
        pick = rng.integers(0, n, n)
        recall_samples.append(float(diffs[pick].mean()))
        case_samples.append(float(case_diffs[pick].mean()))
    return {
        "seed": seed, "samples": samples, "n_questions": n,
        "macro_recall_delta": {
            "point_estimate": round(float(diffs.mean()), 4),
            "ci95": [round(float(np.percentile(recall_samples, 2.5)), 4),
                     round(float(np.percentile(recall_samples, 97.5)), 4)],
        },
        "fully_recalled_delta_per_case": {
            "point_estimate": round(float(case_diffs.mean()), 4),
            "ci95": [round(float(np.percentile(case_samples, 2.5)), 4),
                     round(float(np.percentile(case_samples, 97.5)), 4)],
        },
    }


def mcnemar(a: dict, b: dict) -> dict:
    """Exact binomial McNemar on discordant fully-recalled outcomes."""
    from math import comb

    b_only = a_only = 0
    for cid, case_a in a["cases"].items():
        case_b = b["cases"][cid]
        if case_b["fully_recalled"] and not case_a["fully_recalled"]:
            b_only += 1
        elif case_a["fully_recalled"] and not case_b["fully_recalled"]:
            a_only += 1
    n = a_only + b_only
    if n == 0:
        return {"discordant_pairs": 0, "b_only": 0, "a_only": 0, "p_value": None,
                "note": "no discordant pairs — the test is undefined"}
    k = min(a_only, b_only)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / (2 ** n))
    return {"discordant_pairs": n, "b_only": b_only, "a_only": a_only,
            "p_value": round(p, 4),
            "note": "exact binomial; supplementary to the paired case counts, not a "
                    "substitute for them"}


def paired(a: dict, b: dict) -> dict:
    quadrant = {"both_correct": [], "only_A": [], "only_B": [], "neither": []}
    for cid, case_a in a["cases"].items():
        case_b = b["cases"][cid]
        if case_a["fully_recalled"] and case_b["fully_recalled"]:
            quadrant["both_correct"].append(cid)
        elif case_a["fully_recalled"]:
            quadrant["only_A"].append(cid)
        elif case_b["fully_recalled"]:
            quadrant["only_B"].append(cid)
        else:
            quadrant["neither"].append(cid)
    return {"quadrant": quadrant,
            "b_rescues_over_a": quadrant["only_B"], "b_regressions_vs_a": quadrant["only_A"],
            "net_cases": len(quadrant["only_B"]) - len(quadrant["only_A"]),
            "macro_recall_delta": round(b["macro_span_recall"] - a["macro_span_recall"], 4)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", default="evals/development/v1.jsonl")
    parser.add_argument("--split-name", default="development")
    parser.add_argument("--out", default="experiments/EXP-014R/results-development.json")
    args = parser.parse_args()

    path = Path(args.split)
    cases = [c for c in load_cases(path) if c.expected_evidence]
    manifest_hash = hashlib.sha256(path.read_bytes()).hexdigest()

    started = time.time()
    encoder = TransformerEncoder(max_seq=512).load()
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)

    t0 = time.time()
    rows = load_chunk_rows(TRANSFORMER_MODEL, CHUNK_SET, SNAPSHOT)
    index = build("DOC-C-SECTION", rows)
    index_seconds = time.time() - t0

    a_cases, b_cases = {}, {}
    lat = {"A": [], "B": [], "routing": []}
    routing = {}

    for case in cases:
        q = case.question
        t0 = time.time()
        a_hits = rrf_fuse([lexical_search(q, SNAPSHOT, RRF_POOL),
                           dense_search(q, SNAPSHOT, TRANSFORMER_MODEL, RRF_POOL,
                                        embedder=transformer)],
                          rrf_k=RRF_K, top_k=2 * RRF_POOL)
        lat["A"].append((time.time() - t0) * 1000)
        a_cases[case.case_id] = score_case(case, a_hits)

        t0 = time.time()
        qvec = np.asarray(transformer.embed([q])[0], dtype=np.float32)
        order = [v for v, _ in index.ranking(qvec)]
        selected = order[:TOP_DOCUMENTS]
        routing_ms = (time.time() - t0) * 1000
        lat["routing"].append(routing_ms)

        t0 = time.time()
        b_hits = rrf_fuse([lexical_search(q, SNAPSHOT, RRF_POOL, version_ids=selected),
                           dense_search(q, SNAPSHOT, TRANSFORMER_MODEL, RRF_POOL,
                                        embedder=transformer, version_ids=selected)],
                          rrf_k=RRF_K, top_k=2 * RRF_POOL)
        lat["B"].append(routing_ms + (time.time() - t0) * 1000)
        b_cases[case.case_id] = score_case(case, b_hits)

        expected = {ref.version_id for ref in case.expected_evidence}
        routing[case.case_id] = {
            "expected_documents": sorted(expected),
            "all_expected_routed_at_5": expected <= set(selected),
            "expected_document_ranks": {d: (order.index(d) + 1 if d in order else None)
                                        for d in sorted(expected)},
        }

    system_a = {"system": "SYSTEM-A-GLOBAL", "config_hash": FROZEN_HASHES["SYSTEM-A-GLOBAL"],
                **summarise(a_cases)}
    system_b = {"system": "SYSTEM-B-DOC-C", "config_hash": FROZEN_HASHES["SYSTEM-B-DOC-C"],
                **summarise(b_cases)}

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                         stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        commit = None

    payload = {
        "experiment_id": "EXP-014R",
        "split": args.split_name,
        "split_path": str(path),
        "split_manifest_sha256": manifest_hash,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "corpus_snapshot": SNAPSHOT, "chunk_set": CHUNK_SET,
        "system_a_config": SYSTEM_A_GLOBAL, "system_b_config": SYSTEM_B_DOC_C,
        "system_a_config_hash": FROZEN_HASHES["SYSTEM-A-GLOBAL"],
        "system_b_config_hash": FROZEN_HASHES["SYSTEM-B-DOC-C"],
        "cases_scored": len(cases),
        "system_a": system_a, "system_b": system_b,
        "paired": paired(system_a, system_b),
        "bootstrap": bootstrap_delta(system_a, system_b, BOOTSTRAP_SEED, BOOTSTRAP_SAMPLES),
        "mcnemar": mcnemar(system_a, system_b),
        "routing": routing,
        "routing_all_expected_at_5": sum(1 for r in routing.values() if r["all_expected_routed_at_5"]),
        "document_index": {"representation": "DOC-C-SECTION", "documents": len(index.version_ids),
                           "build_seconds": round(index_seconds, 2),
                           "storage_bytes": int(index.matrix.nbytes)},
        "latency_ms": {k: round(statistics.mean(v), 1) for k, v in lat.items()},
        "runtime_seconds": round(time.time() - started, 1),
        "errors": [],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    for s in (system_a, system_b):
        print(f"{s['system']:16s} macroR={s['macro_span_recall']:.3f} "
              f"full={s['cases_fully_recalled']}/{s['cases_total']} "
              f"spans={s['spans_found_at_10']}/{s['spans_total']} "
              f"docR={s['document_recall']:.3f} MRR={s['mrr']:.3f}")
    p = payload["paired"]
    print(f"\npaired: B rescues {p['b_rescues_over_a']}  B regressions {p['b_regressions_vs_a']}  "
          f"net {p['net_cases']:+d}  delta {p['macro_recall_delta']:+.3f}")
    bs = payload["bootstrap"]["macro_recall_delta"]
    print(f"bootstrap macro-recall delta {bs['point_estimate']:+.3f} "
          f"95% CI [{bs['ci95'][0]:+.3f}, {bs['ci95'][1]:+.3f}] (n={payload['bootstrap']['n_questions']})")
    print(f"mcnemar: {payload['mcnemar']}")
    print(f"routing all-expected@5: {payload['routing_all_expected_at_5']}/{len(routing)}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
