#!/usr/bin/env python3
"""EXP-015 §1 and §8: record the validation decision, and bound what reranking could win.

The ceiling is computed from SYSTEM-A's already-stored candidate ranks. No retrieval is
re-run and no model is involved: a perfect reranker over a pool of P can only promote a
span that is already inside the top P, so the ceiling is arithmetic over the ranks the
validation run recorded.

This is what decides whether EXP-015 is worth running at all. A reranker cannot rescue
evidence that candidate generation never produced.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.systems import FROZEN_HASHES, SNAPSHOT

VAL = Path("experiments/EVAL-VAL-001")
OUT = Path("experiments/EXP-015")
POOLS = (30, 50, 100)
TOP_K = 10


def decision() -> dict:
    analysis = json.loads((VAL / "EVAL-VAL-001-analysis.json").read_text())
    verdict = analysis["replication_verdict"]
    return {
        "document": "EVAL-VAL-001 — project decision",
        "decided_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "SYSTEM_B_PROMOTION": "REJECTED",
        "SYSTEM_A_CONTROL": "RETAINED",
        "classification": verdict["classification"],
        "evidence": {
            "system_a_strict": verdict["system_a_strict"],
            "system_b_strict": verdict["system_b_strict"],
            "rescues": verdict["rescues"],
            "regressions": verdict["regressions"],
            "net_cases": verdict["net_cases"],
            "bootstrap_macro_delta": analysis["bootstrap"]["macro_recall_delta"],
            "mcnemar_p": analysis["mcnemar"]["p_value"],
            "document_routing_failures": verdict["document_routing_failures"],
            "cases": analysis["primary_endpoint"]["cases"],
        },
        "reason": (
            "DOC-C did not replicate on independent validation. Its Stage-1 routing "
            f"discarded a required document in "
            f"{verdict['document_routing_failures']} of "
            f"{analysis['primary_endpoint']['cases']} cases, and every one of the "
            f"{verdict['regressions']} regressions has the same signature: SYSTEM-A "
            "found the span at rank 1-9 and SYSTEM-B did not retrieve it at all."),
        "system_b_disposition": {
            "deleted": False,
            "status": "PRESERVED as a measured negative experiment",
            "config_hash": FROZEN_HASHES["SYSTEM-B-DOC-C"],
            "why_preserved": (
                "A rejected intervention with a clean causal explanation is a result. "
                "Deleting it would leave the project unable to say why routing was "
                "tried and what it cost."),
        },
        "system_a_disposition": {
            "status": "RETAINED as the retrieval control",
            "config_hash": FROZEN_HASHES["SYSTEM-A-GLOBAL"],
            "unchanged": True,
        },
        "holdout": {"runs": 0, "frozen": True, "count": 90, "membership_unchanged": True},
    }


def ceiling(results: dict) -> dict:
    """What a perfect reranker over each pool could achieve, and what it could not."""
    cases = results["system_a"]["cases"]
    out = {}
    for pool in POOLS:
        reachable_cases, reachable_spans = 0, 0
        unreachable_cases, unreachable_spans = [], 0
        total_spans = 0
        for case_id, case in cases.items():
            in_pool = []
            for span in case["spans"]:
                total_spans += 1
                rank = span["rank"]
                if rank is not None and rank <= pool:
                    in_pool.append(True)
                    reachable_spans += 1
                else:
                    in_pool.append(False)
                    unreachable_spans += 1
            if all(in_pool):
                reachable_cases += 1
            else:
                unreachable_cases.append({
                    "case_id": case_id,
                    "span_ranks": [s["rank"] for s in case["spans"]],
                    "reason": ("evidence absent from candidate generation entirely"
                               if any(s["rank"] is None for s in case["spans"])
                               else f"evidence ranked beyond pool {pool}"),
                })
        out[str(pool)] = {
            "pool": pool,
            "max_strict_full_case_recall": reachable_cases,
            "max_strict_pct": round(100 * reachable_cases / len(cases), 1),
            "max_span_recall_at_10": round(reachable_spans / total_spans, 4),
            "spans_reachable": reachable_spans,
            "spans_total": total_spans,
            "cases_unreachable": len(unreachable_cases),
            "spans_unreachable": unreachable_spans,
            "unreachable_detail": unreachable_cases,
        }
    return out


def main() -> int:
    results = json.loads((VAL / "EVAL-VAL-001-results.json").read_text())
    if results["system_a_config_hash"] != FROZEN_HASHES["SYSTEM-A-GLOBAL"]:
        raise SystemExit("refusing: the stored run did not use the frozen SYSTEM-A")
    if results["corpus_snapshot"] != SNAPSHOT:
        raise SystemExit("refusing: the stored run used a different corpus snapshot")

    OUT.mkdir(parents=True, exist_ok=True)
    record = decision()
    (VAL / "EVAL-VAL-001-decision.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (VAL / "EVAL-VAL-001-decision.md").write_text("\n".join([
        "# EVAL-VAL-001 — project decision",
        "",
        f"**`SYSTEM_B_PROMOTION = {record['SYSTEM_B_PROMOTION']}`**",
        "",
        f"**`SYSTEM_A_CONTROL = {record['SYSTEM_A_CONTROL']}`**",
        "",
        (f"Decided {record['decided_at']} on the EVAL-VAL-001 result "
         f"(`{record['classification']}`)."),
        "",
        "## Why",
        "",
        record["reason"],
        "",
        "| | SYSTEM-A | SYSTEM-B |",
        "| --- | --- | --- |",
        (f"| strict full-case recall@10 | {record['evidence']['system_a_strict']} | "
         f"{record['evidence']['system_b_strict']} |"),
        (f"| paired movement | — | {record['evidence']['rescues']} rescues, "
         f"{record['evidence']['regressions']} regressions, "
         f"net {record['evidence']['net_cases']:+d} |"),
        (f"| bootstrap macro delta | — | "
         f"{record['evidence']['bootstrap_macro_delta']['point_estimate']:+.3f} "
         f"95% CI [{record['evidence']['bootstrap_macro_delta']['ci95'][0]:+.3f}, "
         f"{record['evidence']['bootstrap_macro_delta']['ci95'][1]:+.3f}] |"),
        f"| McNemar exact p | — | {record['evidence']['mcnemar_p']} |",
        "",
        "## SYSTEM-B is preserved, not deleted",
        "",
        record["system_b_disposition"]["why_preserved"],
        "",
        (f"Its frozen configuration hash "
         f"`{FROZEN_HASHES['SYSTEM-B-DOC-C'][:16]}…` and every artifact of the run "
         "remain in the repository."),
        "",
        "## Holdout",
        "",
        (f"Untouched: {record['holdout']['count']} cases, "
         f"`holdout_runs = {record['holdout']['runs']}`, "
         f"`holdout_frozen = {str(record['holdout']['frozen']).lower()}`."),
        "",
    ]), encoding="utf-8")

    ceilings = ceiling(results)
    baseline = results["system_a"]["cases_fully_recalled"]
    payload = {
        "document": "EXP-015 — reranker ceiling analysis",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": ("Arithmetic over SYSTEM-A's stored candidate ranks. A perfect "
                   "reranker over a pool of P promotes any span already inside the top "
                   "P; it can do nothing for a span outside it. No retrieval was "
                   "re-run and no model was involved."),
        "baseline": {"system": "SYSTEM-A-GLOBAL", "strict_full_case": baseline,
                     "cases": results["cases_scored"],
                     "span_recall": results["system_a"]["macro_span_recall"],
                     "spans_found": results["system_a"]["spans_found_at_10"],
                     "spans_total": results["system_a"]["spans_total"]},
        "ceilings": ceilings,
        "headroom": {
            str(pool): ceilings[str(pool)]["max_strict_full_case_recall"] - baseline
            for pool in POOLS},
        "candidate_generation_limit": {
            "spans_never_retrieved": sum(
                1 for c in results["system_a"]["cases"].values()
                for s in c["spans"] if s["rank"] is None),
            "note": ("These spans are outside every pool. No reranker can reach them; "
                     "they are a candidate-generation problem, not a ranking one."),
        },
        "system_a_hash": results["system_a_config_hash"],
        "corpus_snapshot": results["corpus_snapshot"],
    }
    (OUT / "EXP-015-ceiling-analysis.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"SYSTEM-A baseline: {baseline}/{results['cases_scored']} strict, "
          f"span recall {results['system_a']['macro_span_recall']}")
    for pool in POOLS:
        c = ceilings[str(pool)]
        print(f"  pool {pool:3d}: ceiling {c['max_strict_full_case_recall']}/40 "
              f"({c['max_strict_pct']}%)  span {c['max_span_recall_at_10']}  "
              f"headroom +{c['max_strict_full_case_recall'] - baseline}  "
              f"unreachable cases {c['cases_unreachable']}")
    print(f"  spans never retrieved at any depth: "
          f"{payload['candidate_generation_limit']['spans_never_retrieved']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
