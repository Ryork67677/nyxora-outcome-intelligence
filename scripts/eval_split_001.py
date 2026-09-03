#!/usr/bin/env python3
"""EVAL-SPLIT-001: audit exposure, cluster facts, and freeze the 150-case split.

The split is built in one direction only: contamination decides first, fact clusters
decide next, the rare-case policy after that, and balance last. Nothing in this pipeline
can read a retrieval score, so the assignment cannot be — even accidentally — chosen for
the result it produces.

Run with --freeze to write the immutable split manifests and set the holdout lock.
Without it the script audits and reports but writes no split.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.corpus_oracle import SNAPSHOT_ID
from rag_v1.eval import clusters as fact_clusters
from rag_v1.eval.exposure import CONTAMINATED, UNEXPOSED, classify, spans_of
from rag_v1.eval.split import ALGORITHM_VERSION, SEED, SPLITS, assign

GOLD_SOURCES = {
    "001": "evals/gold/batch_001_v2/overlay.json",
    "002": "evals/review/gold_review_batch_002.json",
    "003": "evals/review/gold_review_batch_003.json",
    "004": "evals/review/gold_review_batch_004_final.json",
    "005": "evals/review/gold_review_batch_005_final.json",
    "006": "evals/review/gold_review_batch_006_final.json",
    "HA": "evals/review/gold_review_HA01_HA60_final.json",
}
HISTORICAL = "evals/development/v1.jsonl"
OUT = Path("experiments/EVAL-SPLIT-001")
SPLIT_DIR = Path("evals/splits/gold150-v1")
TARGETS = {"development": 20, "validation": 40, "holdout": 90}
#: §10. Categories with n <= 2 are sentinel cases, not statistics. An unexposed one is
#: most useful in the holdout, where it is at least a fresh observation.
RARE_CATEGORIES = ("genuine_multi_hop", "ambiguity_disambiguation")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_cases() -> list[dict]:
    cases = []
    for group, rel in GOLD_SOURCES.items():
        payload = json.loads(Path(rel).read_text())
        for record in (payload.get("records") or payload.get("case_records") or []):
            if (record.get("verification_status") == "human_verified"
                    or record.get("human_verified")):
                cases.append({"group": group, **record})
    return sorted(cases, key=lambda c: c["candidate_id"])


def load_historical() -> list[dict]:
    return [json.loads(line) for line in Path(HISTORICAL).read_text().splitlines()
            if line.strip()]


def audit(cases: list[dict], historical: list[dict]) -> list[dict]:
    ledger = []
    for case in cases:
        verdict = classify(case, historical)
        spans = spans_of(case)
        ledger.append({
            "candidate_id": case["candidate_id"],
            "provider": case.get("provider"),
            "group": case["group"],
            "reasoning_type": case.get("reasoning_type"),
            "reasoning_type_inferred": (None if case.get("reasoning_type")
                                        else "unlabeled_legacy"),
            "secondary_category": case.get("secondary_category"),
            "evidence_shape": case.get("evidence_shape") or "single_span",
            "span_count": len(spans),
            "version_ids": sorted({s["version_id"] for s in spans}),
            "source_documents": sorted({case.get("document_title")}
                                       - {None}) or [],
            "exposure_status": verdict["status"],
            "historical_matches": [m["case_id"] for m in verdict["matches"]],
            "matching_experiments": sorted({
                exp for m in verdict["matches"]
                for exp in m.get("experiments", [])}) or None,
            "criteria_hit": sorted({m["criterion"] for m in verdict["matches"]}),
            "question_text_match": any(m["criterion"] in ("A_exact_id",
                                                          "B_exact_question")
                                       for m in verdict["matches"]),
            "evidence_overlap": max(
                (m.get("overlap_chars", 0) for m in verdict["matches"]), default=0),
            "fact_overlap": max(
                (m.get("similarity", 0.0) for m in verdict["matches"]), default=0.0),
            "reason": verdict["reason"],
        })
    return ledger


def distributions(cases: list[dict], assignment: dict) -> dict:
    by_id = {c["candidate_id"]: c for c in cases}
    out: dict = {}
    for split in SPLITS:
        members = [cid for cid, s in assignment.items() if s == split]
        records = [by_id[m] for m in members]
        docs = Counter(r.get("document_title") for r in records)
        out[split] = {
            "count": len(members),
            "provider": dict(Counter(r.get("provider") for r in records)),
            "provider_pct": {k: round(100 * v / len(records), 1)
                             for k, v in Counter(r.get("provider")
                                                 for r in records).items()}
            if records else {},
            "reasoning_type": dict(Counter(
                r.get("reasoning_type") or "unlabeled_legacy" for r in records)),
            "secondary_category": dict(Counter(
                r.get("secondary_category") or "none" for r in records)),
            "group": dict(Counter(r["group"] for r in records)),
            "evidence_shape": dict(Counter(
                r.get("evidence_shape") or "single_span" for r in records)),
            "span_counts": dict(Counter(len(spans_of(r)) for r in records)),
            "multi_span_cases": sum(1 for r in records if len(spans_of(r)) > 1),
            "unique_source_documents": len(docs),
            "top_source_documents": docs.most_common(5),
            "max_cases_from_one_document": max(docs.values()) if docs else 0,
        }
    return out


def build(freeze: bool) -> dict:
    cases = load_cases()
    historical = load_historical()
    ledger = audit(cases, historical)
    by_status = Counter(row["exposure_status"] for row in ledger)
    contaminated = {row["candidate_id"] for row in ledger
                    if row["exposure_status"] in CONTAMINATED}

    cluster_result = fact_clusters.build(cases, spans_of)

    # §10 — rare categories. An unexposed sentinel goes to the holdout.
    rare = {}
    for category in RARE_CATEGORIES:
        members = [c["candidate_id"] for c in cases
                   if c.get("reasoning_type") == category]
        rare[category] = {
            "case_ids": members, "count": len(members),
            "exposed": [m for m in members if m in contaminated],
        }
    forced_holdout = {m for info in rare.values() for m in info["case_ids"]
                      if m not in contaminated and info["count"] <= 2}

    result = assign(cases, cluster_result["clusters"], contaminated, forced_holdout,
                    TARGETS)
    assignment = result["assignment"]

    # Every gate the brief names, checked on the produced assignment.
    holdout_ids = {c for c, s in assignment.items() if s == "holdout"}
    validation_ids = {c for c, s in assignment.items() if s == "validation"}
    status_of = {row["candidate_id"]: row["exposure_status"] for row in ledger}
    straddling = []
    for cluster in cluster_result["clusters"]:
        splits = {assignment[m] for m in cluster["members"]}
        if len(splits) > 1:
            straddling.append({"cluster_id": cluster["cluster_id"],
                               "members": cluster["members"],
                               "splits": sorted(splits)})
    gates = {
        "every_case_assigned_once": (len(assignment) == 150
                                     and sorted(assignment) == sorted(
                                         c["candidate_id"] for c in cases)),
        "no_contaminated_in_validation": not (validation_ids & contaminated),
        "no_contaminated_in_holdout": not (holdout_ids & contaminated),
        "validation_all_unexposed": all(status_of[c] == UNEXPOSED
                                        for c in validation_ids),
        "holdout_all_unexposed": all(status_of[c] == UNEXPOSED for c in holdout_ids),
        "no_cluster_straddles_a_split": not straddling,
        "snapshot_unchanged": SNAPSHOT_ID == "snap_689e336380a054d8039dc35b2c09cd0a",
    }

    payload = {
        "document": "EVAL-SPLIT-001 — contamination-aware freeze of the 150-case set",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "split_version": "gold150-v1",
        "algorithm_version": ALGORITHM_VERSION,
        "seed": SEED,
        "corpus_snapshot": SNAPSHOT_ID,
        "gold_version": "GOLD-001 (150 human_verified)",
        "targets": TARGETS,
        "historical_exposure": {
            "source": HISTORICAL,
            "cases": len(historical),
            "scored": sum(1 for h in historical if not h.get("expected_abstain")),
            "abstain_controls": sum(1 for h in historical
                                    if h.get("expected_abstain")),
            "case_ids": [h["case_id"] for h in historical],
            "note": ("Derived from the artifacts, not assumed: these are the only case "
                     "identifiers any EXP-000..EXP-014R result file references."),
        },
        "exposure_summary": dict(by_status),
        "contaminated_case_ids": sorted(contaminated),
        "counts": result["counts"],
        "assignment": assignment,
        "distributions": distributions(cases, assignment),
        "fact_clusters": {
            "total": len(cluster_result["clusters"]),
            "multi_member": len(cluster_result["multi_member_clusters"]),
            "cases_in_multi_member_clusters": sum(
                c["size"] for c in cluster_result["multi_member_clusters"]),
            "thresholds": cluster_result["thresholds"],
            "straddling_clusters": straddling,
        },
        "rare_categories": rare,
        "rare_category_placement": {
            m: assignment[m] for info in rare.values() for m in info["case_ids"]},
        "interventions": result["interventions"],
        "gates": gates,
        "generation_policy": {
            "authoring_model_exposure": (
                "Claude, ChatGPT, Grok and Codex participated in authoring and review "
                "of these cases. Retrieval configurations were not tuned on them, but "
                "answer generation must not be run inside an authoring conversation."),
            "required_runtime_rule": (
                "Answer generation must use fresh, stateless model calls. The "
                "generation input carries only the experiment-defined system prompt, "
                "the query and the retrieved context — nothing from any "
                "benchmark-authoring conversation, and no prior turn of one."),
        },
        "not_done": [
            ("No retrieval was run: no BM25, dense, RRF, DOC-C, routing, "
             "reranking or generation, and no rank or score was computed."),
            "No case was placed using system performance knowledge.",
            "No GOLD record was modified.",
            "The holdout was not run.",
        ],
    }
    payload["succeeded"] = all(gates.values())
    payload["exposure_ledger"] = ledger
    payload["clusters"] = cluster_result["clusters"]

    if freeze and payload["succeeded"]:
        SPLIT_DIR.mkdir(parents=True, exist_ok=True)
        hashes = {}
        for split in SPLITS:
            members = sorted(c for c, s in assignment.items() if s == split)
            body = {
                "split": split, "split_version": "gold150-v1", "seed": SEED,
                "algorithm_version": ALGORITHM_VERSION,
                "corpus_snapshot": SNAPSHOT_ID,
                "frozen_at": payload["generated_at"],
                "count": len(members), "case_ids": members,
                "exposure_statuses": {m: status_of[m] for m in members},
            }
            text = json.dumps(body, indent=2, ensure_ascii=False) + "\n"
            (SPLIT_DIR / f"{split}.json").write_text(text, encoding="utf-8")
            hashes[split] = sha256_text(text)
        payload["split_artifact_sha256"] = hashes
        payload["contamination_audit_sha256"] = sha256_text(
            json.dumps(ledger, sort_keys=True, ensure_ascii=False))
        payload["fact_cluster_sha256"] = sha256_text(
            json.dumps(cluster_result["clusters"], sort_keys=True, ensure_ascii=False))
        payload["holdout_frozen"] = True
        lock = {
            "holdout_frozen": True,
            "frozen_at": payload["generated_at"],
            "split_version": "gold150-v1",
            "holdout_sha256": hashes["holdout"],
            "holdout_count": len(holdout_ids),
            "corpus_snapshot": SNAPSHOT_ID,
            "rule": ("Holdout membership may not change because of system performance. "
                     "A failure found during engineering goes to the "
                     "challenge-candidate queue, never into or out of this set."),
            "erratum_policy": ("A holdout case later shown to be objectively invalid is "
                               "recorded as a benchmark erratum and retained. It is "
                               "never silently replaced."),
            "unlock_requires": "an explicit owner decision recorded as an erratum",
        }
        (SPLIT_DIR / "holdout.lock.json").write_text(
            json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        payload["holdout_lock"] = lock
    else:
        payload["holdout_frozen"] = False
    return payload


def render_ledger(payload: dict) -> str:
    rows = "\n".join(
        f"| `{r['candidate_id']}` | {r['group']} | {r['provider']} | "
        f"`{r['reasoning_type'] or 'null'}` | {r['evidence_shape']} | "
        f"**{r['exposure_status']}** | {', '.join(r['historical_matches']) or '—'} | "
        f"{r['reason'][:110]} |"
        for r in payload["exposure_ledger"])
    hist = payload["historical_exposure"]
    summary = "\n".join(f"| `{k}` | {v} |"
                        for k, v in sorted(payload["exposure_summary"].items()))
    return "\n".join([
        "# EVAL-SPLIT-001 — exposure ledger",
        "",
        (f"Every one of the {len(payload['exposure_ledger'])} approved cases, judged "
         f"against the {hist['cases']} historically exposed cases "
         f"({hist['scored']} scored + {hist['abstain_controls']} abstain controls)."),
        "",
        ("Those 22 are the complete exposure surface: they are the only case "
         "identifiers any EXP-000..EXP-014R result file references, derived by scanning "
         "the artifacts rather than taken from a description. The scored twenty appear "
         "in 19 experiments each."),
        "",
        "## Summary",
        "",
        "| exposure status | cases |",
        "| --- | --- |",
        summary,
        "",
        ("A case may enter validation or holdout only at `UNEXPOSED`. `UNKNOWN` counts "
         "as contaminated."),
        "",
        "## Criteria",
        "",
        "| | test | status assigned |",
        "| --- | --- | --- |",
        "| A | identical case identifier | EXPOSED_DIRECT |",
        "| B | identical normalised question | EXPOSED_DIRECT |",
        "| C | identical evidence anchor | EXPOSED_DIRECT |",
        "| D | any character overlap in the same document | EXPOSED_EVIDENCE_OVERLAP |",
        "| E | claim token overlap ≥ 0.80 | EXPOSED_FACT_PARAPHRASE |",
        "| F | question token overlap ≥ 0.70 | EXPOSED_FACT_PARAPHRASE |",
        "| G | any hop of a composed case exposed | inherits the hop's status |",
        "",
        "## Every case",
        "",
        ("| case | grp | provider | reasoning | shape | exposure | historical match | "
         "reason |"),
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        rows,
        "",
    ])


def render_report(payload: dict) -> str:
    dist = payload["distributions"]
    counts = payload["counts"]
    clusters = payload["fact_clusters"]
    gates = "\n".join(f"| {k.replace('_', ' ')} | {'PASS' if v else 'FAIL'} |"
                      for k, v in payload["gates"].items())

    def block(split: str) -> list[str]:
        d = dist[split]
        return [
            f"### {split} — {d['count']} cases",
            "",
            f"- provider: {d['provider']} ({d['provider_pct']}%)",
            f"- reasoning type: {d['reasoning_type']}",
            f"- evidence shape: {d['evidence_shape']}",
            f"- spans per case: {d['span_counts']}; multi-span: {d['multi_span_cases']}",
            f"- batch/group: {d['group']}",
            (f"- source documents: {d['unique_source_documents']} unique, "
             f"most concentrated holds {d['max_cases_from_one_document']} cases"),
            f"- top documents: {d['top_source_documents'][:3]}",
            "",
        ]

    overall_provider = Counter()
    for split in SPLITS:
        for provider, n in dist[split]["provider"].items():
            overall_provider[provider] += n
    return "\n".join([
        "# EVAL-SPLIT-001 — split report",
        "",
        (f"**{'FROZEN' if payload.get('holdout_frozen') else 'NOT FROZEN'}** — "
         f"generated {payload['generated_at']}, seed `{payload['seed']}`, "
         f"algorithm `{payload['algorithm_version']}`."),
        "",
        "## Gates",
        "",
        "| gate | result |",
        "| --- | --- |",
        gates,
        "",
        "## Counts",
        "",
        "| split | cases | target |",
        "| --- | --- | --- |",
        *[f"| {s} | {counts.get(s, 0)} | {payload['targets'][s]} |" for s in SPLITS],
        f"| **total** | **{sum(counts.values())}** | **150** |",
        "",
        "## Exposure",
        "",
        (f"{payload['exposure_summary']}. Contaminated cases: "
         f"{payload['contaminated_case_ids'] or 'none'} — all in development."),
        "",
        "## Distributions",
        "",
        *itertools.chain.from_iterable(block(s) for s in SPLITS),
        f"Overall provider mix: {dict(overall_provider)}.",
        "",
        "## Fact clusters",
        "",
        (f"{clusters['total']} clusters, of which {clusters['multi_member']} hold more "
         f"than one case, covering {clusters['cases_in_multi_member_clusters']} cases. "
         f"Clusters straddling a split boundary: "
         f"{len(clusters['straddling_clusters'])}."),
        "",
        f"Thresholds: {clusters['thresholds']}.",
        "",
        "## Rare categories",
        "",
        *[f"- `{k}`: {v['count']} case(s) {v['case_ids']}, exposed: "
          f"{v['exposed'] or 'none'} → placed in "
          f"{[payload['assignment'][c] for c in v['case_ids']]}"
          for k, v in payload["rare_categories"].items()],
        "",
        ("A category with two or fewer members is a sentinel, not a "
         "statistic. Neither supports an aggregate claim and neither should be "
         "reported as one."),
        "",
        "## Interventions",
        "",
        ("\n".join(f"- `{i.get('cluster_id')}`: {i['issue']} → {i['resolution']}"
                   for i in payload["interventions"]) or "None. Every cluster was "
         "placed by the deterministic rule without manual override."),
        "",
        "## Generation policy",
        "",
        f"**{payload['generation_policy']['required_runtime_rule']}**",
        "",
        payload["generation_policy"]["authoring_model_exposure"],
        "",
        "## Not done",
        "",
        "\n".join(f"- {item}" for item in payload["not_done"]),
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true",
                        help="write the split manifests and set the holdout lock")
    args = parser.parse_args()

    payload = build(freeze=args.freeze)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "EVAL-SPLIT-001-exposure-ledger.json").write_text(
        json.dumps({"historical_exposure": payload["historical_exposure"],
                    "summary": payload["exposure_summary"],
                    "ledger": payload["exposure_ledger"]}, indent=2,
                   ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "EVAL-SPLIT-001-exposure-ledger.md").write_text(render_ledger(payload),
                                                           encoding="utf-8")
    (OUT / "EVAL-SPLIT-001-fact-clusters.json").write_text(
        json.dumps({"thresholds": payload["fact_clusters"]["thresholds"],
                    "clusters": payload["clusters"]}, indent=2,
                   ensure_ascii=False) + "\n", encoding="utf-8")
    report = {k: v for k, v in payload.items()
              if k not in ("exposure_ledger", "clusters")}
    (OUT / "EVAL-SPLIT-001-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "EVAL-SPLIT-001-report.md").write_text(render_report(payload),
                                                  encoding="utf-8")
    if args.freeze and payload["succeeded"]:
        (OUT / "EVAL-SPLIT-001-manifest.json").write_text(
            json.dumps({
                "split_version": payload["split_version"],
                "created_at": payload["generated_at"],
                "seed": payload["seed"],
                "algorithm_version": payload["algorithm_version"],
                "corpus_snapshot": payload["corpus_snapshot"],
                "gold_version": payload["gold_version"],
                "counts": payload["counts"],
                "case_ids": {s: sorted(c for c, v in payload["assignment"].items()
                                       if v == s) for s in SPLITS},
                "distributions": payload["distributions"],
                "contamination_audit_sha256": payload["contamination_audit_sha256"],
                "fact_cluster_sha256": payload["fact_cluster_sha256"],
                "split_artifact_sha256": payload["split_artifact_sha256"],
                "holdout_frozen": True,
                "generation_policy": payload["generation_policy"],
            }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (OUT / "EVAL-SPLIT-001-manifest.md").write_text("\n".join([
            "# EVAL-SPLIT-001 — frozen split manifest",
            "",
            f"Split `{payload['split_version']}`, frozen {payload['generated_at']}.",
            "",
            "| | |",
            "| --- | --- |",
            f"| seed | `{payload['seed']}` |",
            f"| algorithm | `{payload['algorithm_version']}` |",
            f"| corpus snapshot | `{payload['corpus_snapshot']}` |",
            f"| gold version | {payload['gold_version']} |",
            *[f"| {s} | {payload['counts'].get(s, 0)} cases, sha256 "
              f"`{payload['split_artifact_sha256'][s][:16]}…` |" for s in SPLITS],
            f"| contamination audit | `{payload['contamination_audit_sha256'][:16]}…` |",
            f"| fact clusters | `{payload['fact_cluster_sha256'][:16]}…` |",
            f"| holdout frozen | **{payload['holdout_frozen']}** |",
            "",
            "## Holdout lock",
            "",
            payload["holdout_lock"]["rule"],
            "",
            payload["holdout_lock"]["erratum_policy"],
            "",
        ]), encoding="utf-8")

    for name, ok in payload["gates"].items():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print(f"\ncounts: {payload['counts']}")
    print(f"exposure: {payload['exposure_summary']}")
    print(f"EVAL-SPLIT-001 SUCCEEDED: {payload['succeeded']}")
    print(f"holdout_frozen: {payload.get('holdout_frozen')}")
    return 0 if payload["succeeded"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
