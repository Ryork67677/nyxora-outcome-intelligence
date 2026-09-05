#!/usr/bin/env python3
"""EVAL-NATQ2-H-002 — the single preregistered SYSTEM-H run on NATQ-002 validation (n=40).

This is a WRAPPER, not a system. Every retrieval stage below is the recovered SYSTEM-H
pipeline imported verbatim from the recovered worktree at origin/grok/v2-natq-20260903:
SYSTEM-A pool, parent selection, per-parent local BM25, RRF union, D1 cross-encoder,
the EXP-017 blend, projection RRF with canonical mapping, and the EXP-019A final blend.
Nothing here changes SYSTEM-H's behaviour; the config hash is asserted, not recomputed
from anything this file does.

Two things differ from the recovered NATQ-001 runner, and only two:

  input   the 40 NATQ-002 validation cases instead of NATQ-001's validation.jsonl.
  scoring natq2_scorer, the same module that reproduced the frozen BM25 comparator.
          The recovered runner's score_system requires section_path equality, which
          NATQ-002 gold evidence does not carry; using it here would silently measure a
          stricter metric than the 0.375 this run is compared against (METRIC-AUDIT-001).

--preflight stops before the first query. It consumes no run and produces no score.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

MAIN = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

E = MAIN / "experiments/EVAL-NATQ2-H-002"
SPLIT = MAIN / "evals/splits/natq-002"
BM = MAIN / "experiments/EVAL-NATQ-BM25-BASELINE-001"
PREREG = MAIN / "experiments/NATQ-002/EVAL-NATQ2-H-002-PREREGISTRATION.json"
MANIFEST = MAIN / "experiments/SYSTEM-H/SYSTEM-H-RUNTIME-MANIFEST.json"

H_CONFIG_HASH = "7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a"
DEPTH, BOOTSTRAP_N, BOOTSTRAP_SEED = 10, 10_000, 20260904


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def gate(wt: Path) -> dict:
    """Refuse to run unless every preregistered identity holds. Checked before any query."""
    pre = json.loads(PREREG.read_text())
    man = json.loads(MANIFEST.read_text())
    bs = pre["benchmark_and_split"]
    checks: list[tuple[str, object, object]] = [
        ("preregistration is the replacement", pre["record_id"], "EVAL-NATQ2-H-002"),
        ("runtime manifest sha", sha(MANIFEST), pre["system_under_test"]["runtime_manifest_sha256"]),
        ("manifest config hash", man["authoritative_system_h_config_hash"], H_CONFIG_HASH),
        ("prereg config hash", pre["system_under_test"]["authoritative_config_hash"], H_CONFIG_HASH),
        ("benchmark file sha", sha(MAIN / "experiments/NATQ-002/NATQ-002-ACCEPTED-100.json"),
         bs["benchmark_file_sha256"]),
        ("validation sha", sha(SPLIT / "validation.json"), bs["validation_sha256"]),
        ("reserve sha", sha(SPLIT / "reserve.json"), bs["reserve_sha256"]),
        ("reserve lock sha", sha(SPLIT / "reserve.lock.json"), bs["reserve_lock_sha256"]),
        ("reserve access log sha", sha(SPLIT / "reserve-access.log.jsonl"),
         bs["reserve_access_log_sha256"]),
        ("reserve access log bytes", (SPLIT / "reserve-access.log.jsonl").stat().st_size, 0),
        ("bm25 results sha", sha(BM / "EVAL-NATQ-BM25-BASELINE-001-RESULTS.json"),
         pre["bm25_comparator"]["results_sha256"]),
        ("bm25 case results sha", sha(BM / "EVAL-NATQ-BM25-BASELINE-001-CASE-RESULTS.json"),
         pre["bm25_comparator"]["case_results_sha256"]),
        ("bm25 ranked output sha", sha(BM / "logs/bm25-ranked-output.jsonl"),
         pre["bm25_comparator"]["ranked_output_sha256"]),
        ("scorer verified against bm25",
         json.loads((E / "EVAL-NATQ2-H-002-SCORER-VERIFICATION.json").read_text())["verified"], True),
    ]
    # Every score-determining source file must still match the recovered ref.
    for name, rec in man["code"].items():
        checks.append((f"code {name}", sha(wt / rec["path"]), rec["sha256"]))
    for name, rec in man["configs"].items():
        checks.append((f"config {name}", sha(wt / rec["path"]), rec["sha256"]))

    results = [{"check": c, "got": str(g)[:80], "want": str(w)[:80], "pass": g == w}
               for c, g, w in checks]
    failed = [r for r in results if not r["pass"]]
    if failed:
        for r in failed:
            print(f"GATE FAIL {r['check']}\n  got  {r['got']}\n  want {r['want']}", file=sys.stderr)
        raise SystemExit(f"refusing to run: {len(failed)} of {len(results)} identity gates failed")
    print(f"identity gate {len(results)}/{len(results)} passed")
    return {"checks": results, "passed": len(results), "total": len(results)}


def paired_bootstrap(h_stat: dict, b_stat: dict, case_ids: list[str]) -> dict:
    """Paired bootstrap over CASES, exactly as preregistered: 10,000 resamples, seed 20260904.

    Spans within a case are not independent, so the resampling unit is the case. The
    statistic is the span-weighted mean of per-case MRR, which reconstructs the partition
    micro-MRR when every case is present.
    """
    weights = {c: len(h_stat[c]["span_ranks"]) for c in case_ids}

    def micro(sample: list[str], stat: dict) -> float:
        num = sum(sum(1.0 / r for r in stat[c]["span_ranks"] if r) for c in sample)
        den = sum(weights[c] for c in sample)
        return num / den if den else 0.0

    obs = micro(case_ids, h_stat) - micro(case_ids, b_stat)
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(case_ids)
    deltas = []
    for _ in range(BOOTSTRAP_N):
        s = [case_ids[rng.randrange(n)] for _ in range(n)]
        deltas.append(micro(s, h_stat) - micro(s, b_stat))
    deltas.sort()
    lo = deltas[int(0.025 * (BOOTSTRAP_N - 1))]
    hi = deltas[int(round(0.975 * (BOOTSTRAP_N - 1)))]
    return {"observed_delta": round(obs, 6), "bootstrap_mean_delta": round(sum(deltas) / len(deltas), 6),
            "ci95_low": round(lo, 6), "ci95_high": round(hi, 6),
            "interval_excludes_zero": not (lo <= 0.0 <= hi),
            "resamples": BOOTSTRAP_N, "seed": BOOTSTRAP_SEED, "unit": "case"}


def decide(delta_mean: float, excludes_zero: bool, case_hit: float) -> tuple[str, dict]:
    """The EVAL-NATQ2-H-002 rule. FAIL gained the regression disjunct; PASS is unchanged."""
    p = excludes_zero and delta_mean > 0 and case_hit >= 0.80
    f = (not excludes_zero) or (excludes_zero and delta_mean < 0) or case_hit < 0.65
    verdict = "PASS" if p and not f else ("FAIL" if f and not p else
                                          ("OVERLAP" if p and f else "INCONCLUSIVE"))
    return verdict, {
        "PASS_clause": p, "FAIL_clause": f,
        "interval_excludes_zero": excludes_zero,
        "mean_delta_sign": "positive" if delta_mean > 0 else ("negative" if delta_mean < 0 else "zero"),
        "case_hit_at_10": case_hit,
        "PASS_floor": 0.80, "FAIL_floor": 0.65}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True, help="recovered worktree at origin/grok/v2-natq-20260903")
    ap.add_argument("--preflight", action="store_true", help="gate and wire-up only; no query, no score")
    a = ap.parse_args()
    wt = Path(a.worktree).resolve()

    g = gate(wt)
    if a.preflight:
        (E / "EVAL-NATQ2-H-002-PREFLIGHT.json").write_text(json.dumps(
            {"record_id": "EVAL-NATQ2-H-002-PREFLIGHT", "gate": g,
             "runs_consumed": 0, "scores_produced": False}, indent=1) + "\n")

    # SYSTEM-H lives in the recovered tree. Import it there, exactly as its own runner does.
    os.chdir(wt)
    for p in ("", "src", "experiments/EXP-015/scripts", "experiments/EXP-018/scripts",
              "experiments/EXP-018B/scripts", "experiments/EXP-017/scripts",
              "experiments/PERF-003/scripts", "experiments/EXP-019A/scripts"):
        sys.path.insert(0, str(wt / p) if p else str(wt))

    from rag_v1.embedders_transformer import TransformerEncoder
    from rag_v1.query_cache import CachedQueryEmbedder
    from rag_v1.types import SearchHit
    from local_bm25_batched import (additive_extras_ordered, cap_local_lists,
                                    local_bm25_per_parent_batched)
    from projection_retrieval import map_to_canonical_extras, projection_rrf
    from run_exp017 import L, P, apply_blend_exp017, load_control_chunks
    from run_exp019a import apply_blend_exp019a
    from system_e import (CHUNK_SET, PARENT_N, SNAPSHOT, TOP_K, TRANSFORMER_FINGERPRINT,
                          TRANSFORMER_MODEL, W, apply_blend, merge_union_rrf,
                          parent_version_ids, retrieve_system_a_pool)
    from v2_system_g_ce import make_v2_system_g_d1_reranker
    from cross_encoder import CE_SHA256
    from run_exp018_development import hit_as_row
    from natq2_scorer import DEPTH as SD, aggregate, case_micro_mrr, per_slice, score_case

    assert SD == DEPTH == TOP_K, "evaluation depth drifted"
    print(f"SYSTEM-H wired: snapshot={SNAPSHOT} chunk_set={CHUNK_SET} parents={PARENT_N} "
          f"W={W} L={L} P={P} depth={TOP_K}")

    encoder = TransformerEncoder(max_seq=512).load()
    if encoder.model_version != TRANSFORMER_FINGERPRINT:
        raise SystemExit(f"STOP: encoder fingerprint {encoder.model_version} != {TRANSFORMER_FINGERPRINT}")
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)
    ce = make_v2_system_g_d1_reranker()
    if ce.artifact_sha256 != CE_SHA256:
        raise SystemExit("STOP: CE onnx sha mismatch")
    if ce.pad != "batch" or ce.bucket_by_length is not True or ce.fast is not False or ce.threads != 4:
        raise SystemExit(f"STOP: D1 CE constructor drifted pad={ce.pad} bucket={ce.bucket_by_length} "
                         f"fast={ce.fast} threads={ce.threads}")
    chunks_by_id = load_control_chunks()
    if len(chunks_by_id) != 14209:
        raise SystemExit(f"STOP: control chunk cache {len(chunks_by_id)} != 14209")
    print(f"encoder fingerprint {encoder.model_version} · CE {ce.artifact_sha256[:16]}… · "
          f"{len(chunks_by_id)} control chunks")

    if a.preflight:
        print("\nPREFLIGHT OK — every component loaded and verified. No query issued, "
              "no run consumed, no score produced.")
        return 0

    cases = json.loads((SPLIT / "validation.json").read_text())["cases"]
    ranked_fh = (E / "logs/h-ranked-output.jsonl").open("w", encoding="utf-8")
    pools_fh = (E / "logs/h-pools.jsonl").open("w", encoding="utf-8")
    ce_fh = (E / "logs/h-ce-scores.jsonl").open("w", encoding="utf-8")

    per_case, lat, stage_lat = [], [], {k: [] for k in ("a_pool", "local_bm25", "ce", "projection", "blend")}
    started = datetime.now(UTC).isoformat()
    print(f"\nEVAL-NATQ2-H-002 retrieving SYSTEM-H once over {len(cases)} validation questions...")

    for case in cases:
        q = case["question"]
        t_case = time.perf_counter()

        t0 = time.perf_counter()
        a_pool = retrieve_system_a_pool(q, transformer)
        stage_lat["a_pool"].append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        parents = parent_version_ids(a_pool, PARENT_N)
        local = local_bm25_per_parent_batched(q, parents, W)
        a_ids = {h.chunk_id for h in a_pool}
        extras = additive_extras_ordered(local, a_ids)
        capped_local = cap_local_lists(local, a_ids, extras[:L])
        fused_e, _new_ids, a_ids = merge_union_rrf(a_pool, capped_local)
        c_e_ids = {h.chunk_id for h in fused_e}
        if not a_ids.issubset(c_e_ids):
            raise SystemExit(f"STOP: anti-drop A failed on {case['case_id']}")
        stage_lat["local_bm25"].append((time.perf_counter() - t0) * 1000)

        a_by_id = {h.chunk_id: h for h in a_pool}
        t0 = time.perf_counter()
        e_ce = ce.score_pairs(q, [h.text for h in fused_e], batch_size=16)
        ce_by_id = {h.chunk_id: float(s) for h, s in zip(fused_e, e_ce, strict=True)}
        lat_ce_e = (time.perf_counter() - t0) * 1000

        e_rows_in = [hit_as_row(h, a_rank=int(h.rank), a_score=float(h.score),
                                ce_score=float(ce_by_id[h.chunk_id]),
                                in_a_pool=h.chunk_id in a_ids,
                                origin="a_pool" if h.chunk_id in a_ids else "local_bm25",
                                system_a_rank=int(a_by_id[h.chunk_id].rank) if h.chunk_id in a_by_id else None,
                                system_a_score=float(a_by_id[h.chunk_id].score) if h.chunk_id in a_by_id else None)
                     for h in fused_e]
        e_rows = apply_blend(e_rows_in)
        for r in e_rows:
            r["e_rank"] = r["blend_rank"]

        t0 = time.perf_counter()
        fused_p = projection_rrf(q, TRANSFORMER_MODEL, transformer)
        mapped = map_to_canonical_extras(fused_p, c_e_ids, P)
        stage_lat["projection"].append((time.perf_counter() - t0) * 1000)

        extra_rows, extra_hits = [], []
        for cid in mapped["C_P"]:
            rec = chunks_by_id[cid]
            extra_rows.append({"chunk_id": rec["chunk_id"], "version_id": rec["version_id"],
                               "section_path": rec["section_path"], "char_start": rec["char_start"],
                               "char_end": rec["char_end"], "text": rec["text"],
                               "origin": "projection", "in_a_pool": False,
                               "projection_fused": mapped["C_P_scores"][cid]})
            extra_hits.append(SearchHit(chunk_id=rec["chunk_id"], version_id=rec["version_id"],
                                        section_path=rec["section_path"], char_start=rec["char_start"],
                                        char_end=rec["char_end"], text=rec["text"],
                                        score=mapped["C_P_scores"][cid], rank=0,
                                        retriever="projection_mapped"))

        t0 = time.perf_counter()
        if extra_rows:
            extra_ce = ce.score_pairs(q, [r["text"] for r in extra_rows], batch_size=16)
            for rec, s in zip(extra_rows, extra_ce, strict=True):
                ce_by_id[rec["chunk_id"]] = float(s)
        stage_lat["ce"].append(lat_ce_e + (time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        x_rows = apply_blend_exp017(e_rows, extra_rows, ce_by_id)
        if not c_e_ids.issubset({r["chunk_id"] for r in x_rows}):
            raise SystemExit(f"STOP: anti-drop E-L10 failed on {case['case_id']}")
        y_rows = apply_blend_exp019a(x_rows)
        stage_lat["blend"].append((time.perf_counter() - t0) * 1000)

        lat.append((time.perf_counter() - t_case) * 1000)

        # The final ranked list, in SYSTEM-H's own final order, capped at the fixed depth.
        ranked = sorted(y_rows, key=lambda r: r["exp019a_rank"])
        hits = [{"rank": int(r["exp019a_rank"]), "chunk_id": r["chunk_id"],
                 "version_id": r["version_id"], "char_start": r["char_start"],
                 "char_end": r["char_end"], "section_path": r.get("section_path"),
                 "origin": r.get("origin"), "ce_score": ce_by_id.get(r["chunk_id"])}
                for r in ranked if int(r["exp019a_rank"]) <= DEPTH]
        for h in hits:
            ranked_fh.write(json.dumps({"case_id": case["case_id"], **h}) + "\n")
        pools_fh.write(json.dumps({
            "case_id": case["case_id"], "a_pool": len(a_pool), "parents": len(parents),
            "local_extras_selected": len(extras[:L]), "fused_e": len(fused_e),
            "projection_extras": len(extra_rows), "union_scored": len(x_rows),
            "final_ranked": len(y_rows)}) + "\n")
        ce_fh.write(json.dumps({"case_id": case["case_id"],
                                "ce_scores": {k: round(v, 6) for k, v in ce_by_id.items()}}) + "\n")

        r = score_case(case, hits, DEPTH)
        r["latency_ms"] = round(lat[-1], 3)
        per_case.append(r)
        print(f"  {case['case_id']} hit={int(r['hit_at_10'])} cov={int(r['full_coverage_at_10'])} "
              f"ranks={r['span_ranks']} {r['latency_ms']:.0f}ms", flush=True)

    for fh in (ranked_fh, pools_fh, ce_fh):
        fh.close()
    finished = datetime.now(UTC).isoformat()

    metrics = aggregate(per_case)
    slat = sorted(lat)

    def pct(p):
        return round(slat[min(len(slat) - 1, int(round(p * (len(slat) - 1))))], 3)

    metrics["latency_p50_ms"], metrics["latency_p95_ms"] = pct(0.50), pct(0.95)

    bm_cases = json.loads((BM / "EVAL-NATQ-BM25-BASELINE-001-CASE-RESULTS.json").read_text())["cases"]
    b_stat = {c["case_id"]: c for c in bm_cases}
    h_stat = {c["case_id"]: c for c in per_case}
    ids = [c["case_id"] for c in per_case]
    boot = paired_bootstrap(h_stat, b_stat, ids)
    verdict, detail = decide(boot["bootstrap_mean_delta"], boot["interval_excludes_zero"],
                             metrics["case_hit_at_10"])

    bm_metrics = json.loads((BM / "EVAL-NATQ-BM25-BASELINE-001-RESULTS.json").read_text())["metrics"]
    payload = {
        "record_id": "EVAL-NATQ2-H-002-RESULTS",
        "system_id": "SYSTEM-H-V2-DEV-CANDIDATE",
        "authoritative_config_hash": H_CONFIG_HASH,
        "preregistration": "experiments/NATQ-002/EVAL-NATQ2-H-002-PREREGISTRATION.json",
        "preregistration_sha256": sha(PREREG),
        "partition_scored": "validation", "cases": len(per_case),
        "reserve_opened": False, "validation_runs_consumed": 1, "retries": 0,
        "started_utc": started, "finished_utc": finished,
        "evaluation_depth": DEPTH,
        "scorer": "experiments/EVAL-NATQ2-H-002/scripts/natq2_scorer.py",
        "scorer_sha256": sha(Path(__file__).resolve().parent / "natq2_scorer.py"),
        "scorer_shared_with_comparator": True,
        "identity_gate": {"passed": g["passed"], "total": g["total"]},
        "metrics": metrics,
        "per_slice": per_slice(per_case),
        "comparator": {"system_id": "SYSTEM-BM25-NATQ-CONTROL", "rerun": False,
                       "metrics": {k: bm_metrics[k] for k in metrics if k in bm_metrics}},
        "paired_test": boot,
        "decision": verdict,
        "decision_detail": detail,
        "stage_latency_mean_ms": {k: round(sum(v) / len(v), 2) for k, v in stage_lat.items() if v},
        "per_case_micro_mrr": {c: round(case_micro_mrr(h_stat[c]), 6) for c in ids},
        "artifacts": {
            "ranked_output": "experiments/EVAL-NATQ2-H-002/logs/h-ranked-output.jsonl",
            "pools": "experiments/EVAL-NATQ2-H-002/logs/h-pools.jsonl",
            "ce_scores": "experiments/EVAL-NATQ2-H-002/logs/h-ce-scores.jsonl"},
    }
    (E / "EVAL-NATQ2-H-002-RESULTS.json").write_text(json.dumps(payload, indent=1) + "\n")
    (E / "EVAL-NATQ2-H-002-CASE-RESULTS.json").write_text(json.dumps(
        {"record_id": "EVAL-NATQ2-H-002-CASE-RESULTS", "system_id": "SYSTEM-H-V2-DEV-CANDIDATE",
         "case_level_pass_fail_vector": {c["case_id"]: c["hit_at_10"] for c in per_case},
         "cases": per_case}, indent=1) + "\n")

    print(json.dumps({k: payload[k] for k in ("metrics", "paired_test", "decision", "decision_detail")},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
