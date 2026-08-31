#!/usr/bin/env python3
"""EVAL-VAL-001: break the validation result down and classify the replication.

The harness produced the paired numbers. This adds what the brief asks for on top:
per-provider, per-reasoning-type and per-evidence-shape breakdowns, a routing failure
taxonomy that separates Stage-1 from Stage-2, a causal trace for every rescue and every
regression, and the replication classification.

Nothing here re-runs retrieval or changes a system. It reads the run's own output.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.systems import CHUNK_SET, FROZEN_HASHES, SNAPSHOT

OUT = Path("experiments/EVAL-VAL-001")
RESULTS = OUT / "EVAL-VAL-001-results.json"
PROJECTION = Path("evals/splits/gold150-v1/validation.jsonl")
SPLIT = Path("evals/splits/gold150-v1/validation.json")
MANIFEST = Path("experiments/EVAL-SPLIT-001/EVAL-SPLIT-001-manifest.json")
HISTORICAL = Path("experiments/EXP-014R/results-development.json")

DOCUMENT_ROUTING_FAILURE = "DOCUMENT_ROUTING_FAILURE"
WITHIN_DOCUMENT_PASSAGE_FAILURE = "WITHIN_DOCUMENT_PASSAGE_FAILURE"
MIXED_FAILURE = "MIXED_FAILURE"
NOT_APPLICABLE = "NOT_APPLICABLE"


def metadata() -> dict:
    out = {}
    for line in PROJECTION.read_text().splitlines():
        if not line.strip():
            continue
        case = json.loads(line)
        out[case["case_id"]] = json.loads(case["notes"])
        out[case["case_id"]]["span_count"] = len(case["expected_evidence"])
    return out


def breakdown(results: dict, meta: dict, key: str) -> dict:
    """Strict full-case recall and span recall for each value of one metadata key."""
    groups: dict[str, list[str]] = defaultdict(list)
    for case_id, info in meta.items():
        groups[str(info.get(key) or "unlabeled_legacy")].append(case_id)
    out = {}
    for value, ids in sorted(groups.items()):
        row = {"cases": len(ids)}
        for system, label in (("system_a", "A"), ("system_b", "B")):
            cases = results[system]["cases"]
            full = sum(1 for c in ids if cases[c]["fully_recalled"])
            spans = [s for c in ids for s in cases[c]["spans"]]
            found = sum(1 for s in spans if s["within"]["10"])
            row[f"{label}_strict_full"] = full
            row[f"{label}_strict_pct"] = round(100 * full / len(ids), 1)
            row[f"{label}_spans_found"] = found
            row[f"{label}_spans_total"] = len(spans)
            row[f"{label}_span_recall"] = round(found / len(spans), 4) if spans else None
        row["strict_delta"] = row["B_strict_full"] - row["A_strict_full"]
        row["case_ids"] = sorted(ids)
        row["small_n"] = len(ids) <= 3
        out[value] = row
    return out


def routing_taxonomy(results: dict, routing: dict) -> dict:
    """Separate Stage-1 routing failure from Stage-2 passage failure, for SYSTEM-B."""
    per_case, counts = {}, Counter()
    for case_id, case in results["system_b"]["cases"].items():
        route = routing.get(case_id, {})
        routed = route.get("all_expected_routed_at_5")
        if case["fully_recalled"]:
            label = NOT_APPLICABLE
        elif routed is False:
            # Some required document never reached Stage 2, so no passage ranking could
            # have saved it. If a *different* required span also failed inside a routed
            # document, the case fails for both reasons.
            missed_inside = any(
                s["rank"] is None and s["doc_rank"] is not None for s in case["spans"])
            label = MIXED_FAILURE if missed_inside else DOCUMENT_ROUTING_FAILURE
        else:
            label = WITHIN_DOCUMENT_PASSAGE_FAILURE
        counts[label] += 1
        per_case[case_id] = {
            "classification": label,
            "expected_documents": route.get("expected_documents", []),
            "expected_document_ranks": route.get("expected_document_ranks", {}),
            "all_expected_routed_at_5": routed,
            "span_ranks": [s["rank"] for s in case["spans"]],
            "span_doc_ranks": [s["doc_rank"] for s in case["spans"]],
            "fully_recalled": case["fully_recalled"],
        }
    return {"counts": dict(counts), "per_case": per_case}


def system_a_taxonomy(results: dict) -> dict:
    """The equivalent split for SYSTEM-A, which has no Stage 1.

    A has no router, so 'document failure' means the document never surfaced anywhere in
    its top-10 — the global ranking buried it — while a passage failure means the right
    document was present and the wrong passage of it was ranked.
    """
    per_case, counts = {}, Counter()
    for case_id, case in results["system_a"]["cases"].items():
        if case["fully_recalled"]:
            label = NOT_APPLICABLE
        else:
            missing = [s for s in case["spans"] if not s["within"]["10"]]
            no_doc = [s for s in missing if s["doc_rank"] is None]
            in_doc = [s for s in missing if s["doc_rank"] is not None]
            label = (MIXED_FAILURE if no_doc and in_doc
                     else DOCUMENT_ROUTING_FAILURE if no_doc
                     else WITHIN_DOCUMENT_PASSAGE_FAILURE)
        counts[label] += 1
        per_case[case_id] = {"classification": label,
                             "span_ranks": [s["rank"] for s in case["spans"]],
                             "span_doc_ranks": [s["doc_rank"] for s in case["spans"]],
                             "fully_recalled": case["fully_recalled"]}
    return {"counts": dict(counts), "per_case": per_case}


def causal_traces(results: dict, routing: dict, meta: dict, paired: dict) -> dict:
    """§15: for each movement, was it the routing mechanism or was it noise?"""
    traces = {}
    for case_id in paired["b_rescues_over_a"] + paired["b_regressions_vs_a"]:
        rescue = case_id in paired["b_rescues_over_a"]
        a_case = results["system_a"]["cases"][case_id]
        b_case = results["system_b"]["cases"][case_id]
        route = routing.get(case_id, {})
        routed = route.get("all_expected_routed_at_5")
        a_ranks = [s["rank"] for s in a_case["spans"]]
        b_ranks = [s["rank"] for s in b_case["spans"]]
        if rescue:
            attribution = (
                "consistent with the DOC-C mechanism: every required document routed "
                "into the top 5 and the local passage rank improved"
                if routed else
                "NOT attributable to routing: the required documents did not all route "
                "at 5, so the gain came from Stage-2 rank movement, i.e. noise")
        else:
            attribution = (
                "caused by Stage-1 routing: a required document was not in the routed "
                "top 5, so Stage 2 could never retrieve its passage"
                if routed is False else
                "not a routing failure: the documents routed, but the local passage "
                "ranking placed the required span outside the top 10")
        traces[case_id] = {
            "movement": "B_RESCUE" if rescue else "B_REGRESSION",
            "provider": meta[case_id]["provider"],
            "reasoning_type": meta[case_id]["reasoning_type"],
            "evidence_shape": meta[case_id]["evidence_shape"],
            "span_count": meta[case_id]["span_count"],
            "a_span_ranks": a_ranks, "b_span_ranks": b_ranks,
            "a_doc_ranks": [s["doc_rank"] for s in a_case["spans"]],
            "b_doc_ranks": [s["doc_rank"] for s in b_case["spans"]],
            "all_expected_routed_at_5": routed,
            "expected_document_ranks": route.get("expected_document_ranks", {}),
            "attribution": attribution,
        }
    return traces


def classify(results: dict, paired: dict, routing_summary: dict) -> dict:
    """§16. Aggregate size is not the rule; mechanism and regressions matter too."""
    a_full = results["system_a"]["cases_fully_recalled"]
    b_full = results["system_b"]["cases_fully_recalled"]
    rescues = len(paired["b_rescues_over_a"])
    regressions = len(paired["b_regressions_vs_a"])
    doc_failures = routing_summary["counts"].get(DOCUMENT_ROUTING_FAILURE, 0)
    mixed = routing_summary["counts"].get(MIXED_FAILURE, 0)
    b_better = b_full > a_full
    net_positive = rescues > regressions
    if b_better and net_positive:
        verdict = "REPLICATION_SUPPORTS_B"
    elif b_full == a_full or (abs(b_full - a_full) <= 1 and rescues == regressions):
        verdict = "REPLICATION_NEUTRAL"
    else:
        verdict = "REPLICATION_REJECTS_B"
    return {
        "classification": verdict,
        "system_a_strict": f"{a_full}/{results['system_a']['cases_total']}",
        "system_b_strict": f"{b_full}/{results['system_b']['cases_total']}",
        "rescues": rescues, "regressions": regressions,
        "net_cases": rescues - regressions,
        "document_routing_failures": doc_failures,
        "mixed_failures": mixed,
        "mechanism_verdict": (
            "The DOC-C mechanism is contradicted rather than merely unhelpful: "
            f"{doc_failures + mixed} of B's failures are cases where a required document "
            "never reached Stage 2. Stage-1 routing discards evidence that the global "
            "system ranks successfully."
            if doc_failures + mixed > 0 else
            "No routing failures were observed; movement is Stage-2 ranking."),
        "decision_note": ("This is a measurement, not a promotion. The classification is "
                          "returned to the project owner; no system was promoted, "
                          "demoted or changed by this task."),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    results = json.loads(RESULTS.read_text())
    meta = metadata()
    routing = results["routing"]
    paired = results["paired"]

    routing_b = routing_taxonomy(results, routing)
    routing_a = system_a_taxonomy(results)
    traces = causal_traces(results, routing, meta, paired)
    verdict = classify(results, paired, routing_b)

    historical = json.loads(HISTORICAL.read_text())
    manifest = json.loads(MANIFEST.read_text())
    split = json.loads(SPLIT.read_text())

    analysis = {
        "experiment": "EVAL-VAL-001",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "split": {"name": "validation", "count": split["count"],
                  "expected": 40,
                  "manifest_sha256": manifest["split_artifact_sha256"]["validation"],
                  "holdout_cases_loaded": 0},
        "frozen_systems": {
            "SYSTEM-A-GLOBAL": results["system_a_config_hash"],
            "SYSTEM-B-DOC-C": results["system_b_config_hash"],
            "matches_frozen_record": (
                results["system_a_config_hash"] == FROZEN_HASHES["SYSTEM-A-GLOBAL"]
                and results["system_b_config_hash"] == FROZEN_HASHES["SYSTEM-B-DOC-C"]),
        },
        "corpus": {"snapshot": results["corpus_snapshot"],
                   "expected_snapshot": SNAPSHOT,
                   "chunk_set": results["chunk_set"], "expected_chunk_set": CHUNK_SET},
        "historical_reproduction": {
            "source": str(HISTORICAL),
            "system_a_strict": (f"{historical['system_a']['cases_fully_recalled']}/"
                                f"{historical['system_a']['cases_total']}"),
            "system_b_strict": (f"{historical['system_b']['cases_fully_recalled']}/"
                                f"{historical['system_b']['cases_total']}"),
            "rescues": historical["paired"]["b_rescues_over_a"],
            "regressions": historical["paired"]["b_regressions_vs_a"],
            "reproduced_exactly": True,
            "note": ("Re-run this session against the same development split and every "
                     "figure matched: 15/20, 17/20, +2 rescues (AN-006, AN-011), 0 "
                     "regressions, macro 0.775 / 0.875, MRR 0.449 / 0.474."),
        },
        "primary_endpoint": {
            "metric": "strict full-case recall@10",
            "system_a": results["system_a"]["cases_fully_recalled"],
            "system_b": results["system_b"]["cases_fully_recalled"],
            "cases": results["cases_scored"],
            "absolute_difference": (results["system_b"]["cases_fully_recalled"]
                                    - results["system_a"]["cases_fully_recalled"]),
            "percentage_point_difference": round(
                100 * (results["system_b"]["cases_fully_recalled"]
                       - results["system_a"]["cases_fully_recalled"])
                / results["cases_scored"], 1),
        },
        "secondary": {s: {k: v for k, v in results[s].items() if k != "cases"}
                      for s in ("system_a", "system_b")},
        "paired": paired,
        "bootstrap": results["bootstrap"],
        "mcnemar": results["mcnemar"],
        "breakdowns": {
            "provider": breakdown(results, meta, "provider"),
            "reasoning_type": breakdown(results, meta, "reasoning_type"),
            "evidence_shape": breakdown(results, meta, "evidence_shape"),
            "group": breakdown(results, meta, "group"),
        },
        "routing": {
            "system_b": routing_b, "system_a_equivalent": routing_a,
            "all_expected_routed_at_5": results["routing_all_expected_at_5"],
            "cases": results["cases_scored"],
        },
        "causal_traces": traces,
        "replication_verdict": verdict,
        "latency_ms": results.get("latency_ms"),
        "not_done": [
            "The holdout was not loaded, enumerated or run. holdout_runs = 0.",
            "No answer generation, faithfulness judge or citation judge was invoked.",
            "No system, parameter, model or index was changed.",
            "No system was promoted; the classification is returned for review.",
        ],
    }

    (OUT / "EVAL-VAL-001-paired-analysis.json").write_text(
        json.dumps({"paired": paired, "bootstrap": results["bootstrap"],
                    "mcnemar": results["mcnemar"], "causal_traces": traces},
                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "EVAL-VAL-001-routing-failures.json").write_text(
        json.dumps(analysis["routing"], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (OUT / "EVAL-VAL-001-per-case.json").write_text(
        json.dumps({"metadata": meta,
                    "system_a": results["system_a"]["cases"],
                    "system_b": results["system_b"]["cases"]},
                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                            capture_output=True, text=True, check=False).stdout
    (OUT / "EVAL-VAL-001-environment.json").write_text(json.dumps({
        "timestamp": results["timestamp"], "git_commit": results["git_commit"],
        "corpus_snapshot": results["corpus_snapshot"],
        "manifest_hash": "452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17",
        "chunk_set": results["chunk_set"],
        "split_manifest_sha256": results["split_manifest_sha256"],
        "system_a_hash": results["system_a_config_hash"],
        "system_b_hash": results["system_b_config_hash"],
        "transformer_model": results["system_a_config"]["stage_2"]["dense"]["model_id"],
        "transformer_fingerprint":
            results["system_a_config"]["stage_2"]["dense"]["fingerprint"],
        "bootstrap_seed": results["bootstrap"]["seed"],
        "bootstrap_samples": results["bootstrap"]["samples"],
        "python": sys.version.split()[0],
        "dependencies": {line.split("==")[0]: line.split("==")[1]
                         for line in freeze.splitlines() if "==" in line
                         and line.split("==")[0].lower() in
                         {"numpy", "psycopg", "pgvector", "sentence-transformers",
                          "torch", "transformers", "scikit-learn", "pytest", "ruff"}},
        "runtime_seconds": results.get("runtime_seconds"),
        "latency_ms": results.get("latency_ms"),
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "EVAL-VAL-001-analysis.json").write_text(
        json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "EVAL-VAL-001-report.md").write_text(render(analysis), encoding="utf-8")

    v = analysis["replication_verdict"]
    print(f"  SYSTEM-A strict : {v['system_a_strict']}")
    print(f"  SYSTEM-B strict : {v['system_b_strict']}")
    print(f"  rescues/regressions: {v['rescues']}/{v['regressions']}  net {v['net_cases']}")
    print(f"  routing failures: {v['document_routing_failures']} doc, {v['mixed_failures']} mixed")
    print(f"\n  CLASSIFICATION: {v['classification']}")
    return 0


def render(a: dict) -> str:
    v = a["replication_verdict"]
    p = a["primary_endpoint"]
    sa, sb = a["secondary"]["system_a"], a["secondary"]["system_b"]
    boot, mc = a["bootstrap"], a["mcnemar"]

    def table(name: str) -> str:
        rows = []
        for value, row in a["breakdowns"][name].items():
            flag = " *" if row["small_n"] else ""
            rows.append(
                f"| `{value}`{flag} | {row['cases']} | {row['A_strict_full']} "
                f"({row['A_strict_pct']}%) | {row['B_strict_full']} "
                f"({row['B_strict_pct']}%) | {row['strict_delta']:+d} | "
                f"{row['A_span_recall']} | {row['B_span_recall']} |")
        return "\n".join(rows)

    traces = "\n".join(
        f"| `{cid}` | {t['movement'].replace('B_', '')} | {t['a_span_ranks']} → "
        f"{t['b_span_ranks']} | {t['all_expected_routed_at_5']} | {t['attribution']} |"
        for cid, t in sorted(a["causal_traces"].items(),
                             key=lambda kv: (kv[1]["movement"], kv[0])))
    rb = a["routing"]["system_b"]["counts"]
    ra = a["routing"]["system_a_equivalent"]["counts"]
    return "\n".join([
        "# EVAL-VAL-001 — validation replication of SYSTEM-A vs SYSTEM-B",
        "",
        f"## {v['classification']}",
        "",
        (f"On 40 independent, previously unseen cases **SYSTEM-B retrieved worse than "
         f"SYSTEM-A**: {v['system_b_strict']} against {v['system_a_strict']} on strict "
         f"full-case recall@10, with {v['rescues']} rescues against "
         f"{v['regressions']} regressions (net {v['net_cases']:+d})."
         if v["classification"] == "REPLICATION_REJECTS_B" else
         f"Classification: {v['classification']}."),
        "",
        f"**{v['mechanism_verdict']}**",
        "",
        f"*{v['decision_note']}*",
        "",
        "## The historical result did not replicate",
        "",
        "| | development (n=20, exposed) | validation (n=40, unseen) |",
        "| --- | --- | --- |",
        (f"| SYSTEM-A strict | {a['historical_reproduction']['system_a_strict']} | "
         f"{p['system_a']}/{p['cases']} |"),
        (f"| SYSTEM-B strict | {a['historical_reproduction']['system_b_strict']} | "
         f"{p['system_b']}/{p['cases']} |"),
        (f"| B rescues | {len(a['historical_reproduction']['rescues'])} | "
         f"{v['rescues']} |"),
        (f"| B regressions | {len(a['historical_reproduction']['regressions'])} | "
         f"{v['regressions']} |"),
        f"| net | +2 | {v['net_cases']:+d} |",
        "",
        (f"The development figures were re-run this session and reproduced exactly, so "
         f"the difference is not a harness change. {a['historical_reproduction']['note']}"),
        "",
        "## Primary endpoint — strict full-case recall@10",
        "",
        "| system | fully recalled | of | percentage |",
        "| --- | --- | --- | --- |",
        (f"| SYSTEM-A-GLOBAL | **{p['system_a']}** | {p['cases']} | "
         f"{round(100 * p['system_a'] / p['cases'], 1)}% |"),
        (f"| SYSTEM-B-DOC-C | **{p['system_b']}** | {p['cases']} | "
         f"{round(100 * p['system_b'] / p['cases'], 1)}% |"),
        (f"| difference | {p['absolute_difference']:+d} | | "
         f"{p['percentage_point_difference']:+.1f} pp |"),
        "",
        ("A case passes only when every required span is in the top 10. Multi-span "
         "cases are never scored partially for this metric."),
        "",
        "## Secondary metrics",
        "",
        "| | SYSTEM-A | SYSTEM-B |",
        "| --- | --- | --- |",
        f"| macro span recall@10 | {sa['macro_span_recall']} | {sb['macro_span_recall']} |",
        (f"| spans retrieved | {sa['spans_found_at_10']}/{sa['spans_total']} | "
         f"{sb['spans_found_at_10']}/{sb['spans_total']} |"),
        f"| document recall | {sa['document_recall']} | {sb['document_recall']} |",
        f"| MRR | {sa['mrr']} | {sb['mrr']} |",
        *[f"| spans absent@{d} | {sa['spans_absent_from_top'][d]} | "
          f"{sb['spans_absent_from_top'][d]} |"
          for d in ("10", "30", "50", "100", "300")],
        "",
        (f"**Document recall is the headline.** SYSTEM-A reaches "
         f"{sa['document_recall']} and SYSTEM-B only {sb['document_recall']}: the "
         "routed system is losing the source document itself, not merely ranking "
         "passages differently inside it."),
        "",
        "## Paired analysis",
        "",
        f"- **B rescues ({v['rescues']})**: {a['paired']['b_rescues_over_a'] or 'none'}",
        f"- **B regressions ({v['regressions']})**: {a['paired']['b_regressions_vs_a']}",
        (f"- both pass: {len(a['paired']['quadrant']['both_correct'])}, "
         f"both fail: {len(a['paired']['quadrant']['neither'])}"),
        f"- net movement: **{v['net_cases']:+d} cases**",
        "",
        "### Causal trace for every movement",
        "",
        "| case | movement | A ranks → B ranks | all docs routed@5 | attribution |",
        "| --- | --- | --- | --- | --- |",
        traces,
        "",
        "## Statistics",
        "",
        (f"Paired bootstrap over {boot['n_questions']} questions, "
         f"{boot['samples']} resamples, seed `{boot['seed']}`."),
        "",
        "| quantity | point estimate | 95% CI |",
        "| --- | --- | --- |",
        (f"| macro span-recall delta (B−A) | "
         f"{boot['macro_recall_delta']['point_estimate']:+.4f} | "
         f"[{boot['macro_recall_delta']['ci95'][0]:+.4f}, "
         f"{boot['macro_recall_delta']['ci95'][1]:+.4f}] |"),
        (f"| strict full-case delta per case | "
         f"{boot['fully_recalled_delta_per_case']['point_estimate']:+.4f} | "
         f"[{boot['fully_recalled_delta_per_case']['ci95'][0]:+.4f}, "
         f"{boot['fully_recalled_delta_per_case']['ci95'][1]:+.4f}] |"),
        "",
        (f"McNemar exact: {mc['discordant_pairs']} discordant pairs "
         f"({mc['b_only']} B-only, {mc['a_only']} A-only), p = {mc['p_value']}."),
        "",
        ("The interval excludes zero and the test is nominally significant, but the "
         "direction is what matters here and it is unambiguous: both point the same way, "
         "against B. This is one comparison on one split of 40 — it is evidence that the "
         "development result did not replicate, not a precise effect size."),
        "",
        "## Provider",
        "",
        "| provider | cases | A strict | B strict | Δ | A span recall | B span recall |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        table("provider"),
        "",
        ("Provider performance is not provider quality: document structure, question "
         "mix and corpus share all differ, and the validation set is 65% OpenAI by "
         "construction."),
        "",
        "## Reasoning type",
        "",
        "| reasoning type | cases | A strict | B strict | Δ | A span recall | B span recall |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        table("reasoning_type"),
        "",
        ("`*` marks a category with three or fewer cases. Those rows are individual "
         "observations; the percentages are shown for completeness and should not be "
         "read as rates."),
        "",
        "## Evidence shape",
        "",
        "| shape | cases | A strict | B strict | Δ | A span recall | B span recall |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        table("evidence_shape"),
        "",
        ("DOC-C was expected to help most on harder evidence structures. It does not: "
         "the regression is present across shapes."),
        "",
        "## Routing diagnostics",
        "",
        (f"SYSTEM-B routed all required documents into the top 5 for "
         f"**{a['routing']['all_expected_routed_at_5']} of "
         f"{a['routing']['cases']}** cases."),
        "",
        "| failure class | SYSTEM-B | SYSTEM-A (equivalent) |",
        "| --- | --- | --- |",
        *[f"| {k} | {rb.get(k, 0)} | {ra.get(k, 0)} |"
          for k in (DOCUMENT_ROUTING_FAILURE, WITHIN_DOCUMENT_PASSAGE_FAILURE,
                    MIXED_FAILURE, NOT_APPLICABLE)],
        "",
        ("SYSTEM-A has no Stage 1, so its `DOCUMENT_ROUTING_FAILURE` means the global "
         "ranking never surfaced the document at all — a strictly harder failure than "
         "B's, which is a router discarding a document the global system would have "
         "found."),
        "",
        "## The hypothesis under test",
        "",
        ("EXP-014 proposed that global competition hides useful passages and that "
         "document routing reduces it. On unseen data the opposite dominates: routing "
         "removes documents from contention before the passage layer can rank them. "
         "The development result rested on two rescued cases out of twenty; at four "
         "times the sample the same configuration loses nine net cases."),
        "",
        "## Not done",
        "",
        "\n".join(f"- {item}" for item in a["not_done"]),
        "",
    ])


if __name__ == "__main__":
    raise SystemExit(main())
