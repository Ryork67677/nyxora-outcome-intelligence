#!/usr/bin/env python3
"""NATQ2-DIAG-001 stage 3: candidate ceiling, pool recall, and the failure taxonomy.

TRACE-ONLY. Reads the frozen span trace; runs nothing.

The ceiling is reported twice on purpose. The coordinator defined CANDIDATE_CASE_CEILING
as an EVERY-span oracle, which is the analogue of case_full_coverage@10. But the metric
SYSTEM-H actually failed is case_hit@10, an ANY-span metric, so the any-span ceiling is
the one that bounds the qualification decision. Reporting only the every-span figure
would understate the headroom against the floor that was missed; reporting only the
any-span figure would answer a question the coordinator did not ask. Both are labelled.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
D = REPO / "experiments/NATQ2-DIAG-001"
OUT = D / "NATQ2-DIAG-001-CEILING-TAXONOMY.json"
PASS_FLOOR, FAIL_FLOOR = 0.80, 0.65


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def classify(spans: list[dict]) -> tuple[str, list[str], str]:
    """One PRIMARY mechanism per failed case, from trace evidence only.

    A vs E cannot be separated by these traces: SYSTEM-A membership was never persisted
    apart from local BM25, so 'never entered the candidate system' and 'the gold document
    is not represented in candidates' are the same observation here. Cases where the gold
    document is entirely absent from the union pool are reported as E and the collapse is
    declared, rather than splitting the difference and implying a distinction the traces
    cannot support.
    """
    failed = [s for s in spans if not s["in_top10"]]
    hit = [s for s in spans if s["in_top10"]]
    mech = []
    for s in failed:
        if not s["gold_doc_in_pool"]:
            mech.append("E_DOCUMENT_DISCOVERY_FAILURE")
        elif not s["in_final_pre_ce_pool"]:
            mech.append("B_LOCALIZATION_FAILURE")
        else:
            mech.append("C_RERANKING_FAILURE")
    kinds = sorted(set(mech))
    if hit and failed:
        # Some required evidence landed, some did not. That is D by definition; the
        # mechanism behind the missing spans is carried as secondary.
        return "D_MULTI_SPAN_PARTIAL_FAILURE", kinds, "case_full_coverage@10 only"
    if len(kinds) > 1:
        return "F_MIXED", kinds, "multiple independent stages contribute"
    return kinds[0], [], "single mechanism across all failing spans"


def main() -> int:
    tr = json.loads((D / "NATQ2-DIAG-001-SPAN-TRACE.json").read_text())
    pops = json.loads((D / "NATQ2-DIAG-001-POPULATIONS.json").read_text())["populations"]
    by_case: dict[str, list[dict]] = {}
    for s in tr["spans"]:
        by_case.setdefault(s["case_id"], []).append(s)
    n_cases, n_spans = len(by_case), len(tr["spans"])

    ceiling_all = [c for c, ss in by_case.items() if all(s["in_final_pre_ce_pool"] for s in ss)]
    ceiling_any = [c for c, ss in by_case.items() if any(s["in_final_pre_ce_pool"] for s in ss)]
    span_ceiling = [s for s in tr["spans"] if s["in_final_pre_ce_pool"]]

    hit_cases = {c for c, ss in by_case.items() if any(s["in_top10"] for s in ss)}
    cov_cases = {c for c, ss in by_case.items() if all(s["in_top10"] for s in ss)}

    # Stage recall at the resolutions the traces support.
    doc_any = [c for c, ss in by_case.items() if any(s["gold_doc_in_pool"] for s in ss)]
    proj_spans = [s for s in tr["spans"] if s["via_projection"]]
    fused_spans = [s for s in tr["spans"] if s["via_fused_e_systemA_or_localbm25"]]
    proj_only = [s for s in tr["spans"] if s["via_projection"] and not s["via_fused_e_systemA_or_localbm25"]]

    tax, rows = Counter(), []
    for cid, ss in sorted(by_case.items()):
        failed = [s for s in ss if not s["in_top10"]]
        if not failed:
            continue
        primary, secondary, scope = classify(ss)
        pop = next(k for k, v in pops.items() if cid in v)
        tax[primary] += 1
        rows.append({
            "case_id": cid, "population": pop,
            "n_spans": len(ss), "n_failed_spans": len(failed),
            "case_hit_at_10": cid in hit_cases, "case_full_coverage_at_10": cid in cov_cases,
            "primary_mechanism": primary, "secondary_mechanisms": secondary,
            "affects": scope,
            "failing_spans": [{
                "span_index": s["span_index"],
                "gold_doc_in_pool": s["gold_doc_in_pool"],
                "covering_candidates_in_pool": s["n_covering_in_pool"],
                "best_ce_score_rank_in_pool": s["best_ce_score_rank_in_pool"],
                "final_blend_rank": "UNAVAILABLE_BEYOND_TOP10"} for s in failed]})

    # Reranker movement, at the only resolution the traces allow.
    in_pool = [s for s in tr["spans"] if s["in_final_pre_ce_pool"]]
    ranked_out = [s for s in in_pool if not s["in_top10"]]
    payload = {
        "record_id": "NATQ2-DIAG-001-CEILING-TAXONOMY",
        "trace_only": True, "systems_run": 0, "retrieval_performed": False,
        "reranking_performed": False, "ce_inference_performed": False,
        "source_span_trace_sha256": sha(D / "NATQ2-DIAG-001-SPAN-TRACE.json"),
        "source_populations_sha256": sha(D / "NATQ2-DIAG-001-POPULATIONS.json"),

        "candidate_ceiling": {
            "definition_used_for_CANDIDATE_CASE_CEILING":
                "every required gold span has at least one covering candidate in the final "
                "pre-rerank pool (the coordinator's definition; a full-coverage oracle)",
            "candidate_case_ceiling": f"{len(ceiling_all)}/{n_cases}",
            "candidate_case_ceiling_rate": round(len(ceiling_all) / n_cases, 4),
            "candidate_span_ceiling": f"{len(span_ceiling)}/{n_spans}",
            "candidate_span_ceiling_rate": round(len(span_ceiling) / n_spans, 4),
            "any_span_candidate_ceiling": f"{len(ceiling_any)}/{n_cases}",
            "any_span_candidate_ceiling_rate": round(len(ceiling_any) / n_cases, 4),
            "why_any_span_is_also_reported":
                "case_hit@10 is the metric that failed and it is an ANY-span metric, so the "
                "any-span ceiling is what bounds the qualification decision.",
            "is_not_system_performance": True},

        "headroom_against_the_floors": {
            "achieved_case_hit_at_10": round(len(hit_cases) / n_cases, 4),
            "any_span_candidate_ceiling_rate": round(len(ceiling_any) / n_cases, 4),
            "PASS_floor": PASS_FLOOR, "FAIL_floor": FAIL_FLOOR,
            "ceiling_clears_PASS_floor": len(ceiling_any) / n_cases >= PASS_FLOOR,
            "cases_between_achieved_and_ceiling": len(ceiling_any) - len(hit_cases),
            "cases_needed_to_reach_FAIL_floor": max(0, -(-int(FAIL_FLOOR * n_cases * 1000) // 1000) - len(hit_cases)),
            "cases_needed_to_reach_PASS_floor": int(round(PASS_FLOOR * n_cases)) - len(hit_cases)},

        "stage_recall": {
            "note": "Reported only at resolutions the stored traces support.",
            "gold_document_present_in_union_pool_cases": f"{len(doc_any)}/{n_cases}",
            "gold_document_present_in_union_pool_spans":
                f"{tr['totals']['gold_doc_present_in_union_pool']}/{n_spans}",
            "covering_candidate_in_union_pool_spans": f"{len(span_ceiling)}/{n_spans}",
            "covering_candidate_via_fused_e_spans": f"{len(fused_spans)}/{n_spans}",
            "covering_candidate_via_projection_spans": f"{len(proj_spans)}/{n_spans}",
            "spans_contributed_by_projection_alone": f"{len(proj_only)}/{n_spans}",
            "case_candidate_recall_at_SYSTEM_A_depth": "UNAVAILABLE — SYSTEM-A membership not persisted separately",
            "span_candidate_recall_at_SYSTEM_A_depth": "UNAVAILABLE — SYSTEM-A membership not persisted separately",
            "candidate_recall_after_local_bm25": "UNAVAILABLE — local BM25 membership not persisted separately",
            "candidate_recall_after_projection": f"{len(span_ceiling)}/{n_spans} (equals the full union pool; projection is the last additive stage)"},

        "reranker_movement": {
            "note": "Pre-CE RRF rank was not persisted, so per-span movement cannot be "
                    "computed. What the traces support is stated instead; nothing is inferred.",
            "pre_ce_rank_available": False,
            "final_blend_rank_available_beyond_top10": False,
            "spans_with_covering_candidate_in_pool": len(in_pool),
            "of_those_reached_top10": len(in_pool) - len(ranked_out),
            "of_those_ranked_out_of_top10": len(ranked_out),
            "ranked_out_rate": round(len(ranked_out) / len(in_pool), 4),
            "ranked_out_spans": [{
                "case_id": s["case_id"], "span_index": s["span_index"],
                "covering_candidates_in_pool": s["n_covering_in_pool"],
                "best_ce_score_rank_in_pool": s["best_ce_score_rank_in_pool"],
                "best_ce_score": s["best_ce_score"]} for s in ranked_out],
            "ce_score_rank_is_derived": "Ordering of stored CE scores, not a persisted rank. "
                                        "The final order is a blend, so this is diagnostic only."},

        "taxonomy": {
            "cases_with_at_least_one_failing_span": len(rows),
            "primary_mechanism_counts": dict(sorted(tax.items())),
            "A_vs_E_separable": False,
            "A_vs_E_note": "GLOBAL_CANDIDATE_FAILURE and DOCUMENT_DISCOVERY_FAILURE are not "
                           "separable from these traces; SYSTEM-A membership was not persisted "
                           "apart from local BM25. Cases whose gold document never appears in "
                           "the union pool are reported as E.",
            "cases": rows},
    }
    OUT.write_text(json.dumps(payload, indent=1) + "\n")

    cc = payload["candidate_ceiling"]
    hr = payload["headroom_against_the_floors"]
    rm = payload["reranker_movement"]
    print(f"CANDIDATE_CASE_CEILING (every span)  {cc['candidate_case_ceiling']}  ({cc['candidate_case_ceiling_rate']})")
    print(f"candidate span ceiling               {cc['candidate_span_ceiling']}  ({cc['candidate_span_ceiling_rate']})")
    print(f"any-span candidate ceiling           {cc['any_span_candidate_ceiling']}  ({cc['any_span_candidate_ceiling_rate']})")
    print(f"achieved case_hit@10                 {hr['achieved_case_hit_at_10']}")
    print(f"ceiling clears the 0.80 PASS floor   {hr['ceiling_clears_PASS_floor']}")
    print(f"cases between achieved and ceiling   {hr['cases_between_achieved_and_ceiling']}")
    print(f"\nin-pool spans ranked out of top10    {rm['of_those_ranked_out_of_top10']}/{rm['spans_with_covering_candidate_in_pool']}  ({rm['ranked_out_rate']})")
    print("\nprimary mechanism counts:")
    for k, v in payload["taxonomy"]["primary_mechanism_counts"].items():
        print(f"  {k:<36} {v}")
    print(f"\nceiling/taxonomy sha256 {sha(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
