#!/usr/bin/env python3
"""NATQ2-DIAG-002 stage 2 — the diagnostics the reconstructed pre-CE traces now support.

Reads only the replay artifacts. Runs nothing, scores nothing, tunes nothing. Every
number here is a mechanism measurement on a CLOSED result; none of it is a system result
and none of it is evidence for reserve.

Refuses to run unless the replay reproduced EVAL-NATQ2-H-002 exactly, because a
non-exact reconstruction must not be used for architectural decisions.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

MAIN = Path(__file__).resolve().parents[4]
OUT = MAIN / "experiments/RAG-V2/NATQ2-DIAG-002"
SPLIT = MAIN / "evals/splits/natq-002"
D1 = MAIN / "experiments/NATQ2-DIAG-001"
BM = MAIN / "experiments/EVAL-NATQ-BM25-BASELINE-001"
DEPTH = 10


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def covers(c: dict, sp: dict) -> bool:
    return (c["version_id"] == sp["version_id"]
            and c["char_start"] < sp["char_end"] and c["char_end"] > sp["char_start"])


def bucket(r: int | None) -> str:
    if r is None:
        return "not_in_pre_ce_ordering"
    for t in (3, 5, 10, 20):
        if r <= t:
            return f"<={t}"
    return ">20"


def channel_class(c: dict) -> str:
    ch = set(c["channels"])
    if ch == {"system_a"}:
        return "SYSTEM_A_ONLY"
    if ch == {"local_bm25"}:
        return "LOCAL_BM25_ONLY"
    if ch == {"system_a", "local_bm25"}:
        return "BOTH_A_AND_LOCAL"
    if ch == {"projection"}:
        return "PROJECTION_ONLY"
    if "projection" in ch:
        return "MULTIPLE_INCLUDING_PROJECTION"
    return "OTHER"


def main() -> int:
    ident = json.loads((OUT / "NATQ2-DIAG-002-REPLAY-IDENTITY.json").read_text())
    if not ident["reproduction"]["EXACT"]:
        raise SystemExit("STOP: the replay is not exact; reconstructed traces must not be used "
                         "for architectural decisions")

    cands = defaultdict(list)
    for line in (OUT / "NATQ2-DIAG-002-CANDIDATES.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            cands[r["case_id"]].append(r)
    cases = json.loads((SPLIT / "validation.json").read_text())["cases"]
    bm_case = {c["case_id"]: c for c in json.loads(
        (BM / "EVAL-NATQ-BM25-BASELINE-001-CASE-RESULTS.json").read_text())["cases"]}
    bm_rank: dict[str, list[dict]] = defaultdict(list)
    for line in (BM / "logs/bm25-ranked-output.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            bm_rank[r["case_id"]].append(r)

    # ---------- every gold span, against the reconstructed stages ----------
    spans, per_case = [], {}
    for case in cases:
        cid = case["case_id"]
        pool = cands[cid]
        by_id = {c["chunk_id"]: c for c in pool}
        pool_versions = {c["version_id"] for c in pool}
        a_versions = {c["version_id"] for c in pool if c["in_system_a"]}
        parent_versions = {c["local_bm25_parent"] for c in pool if c["local_bm25_parent"]}
        rows = []
        for i, sp in enumerate(case["evidence"]):
            cov = [c for c in pool if covers(c, sp)]
            best = min(cov, key=lambda c: c["final_rank"]) if cov else None
            pre = [c["pre_ce_retrieval_rank"] for c in cov if c["pre_ce_retrieval_rank"]]
            same_doc = [c for c in pool if c["version_id"] == sp["version_id"]]
            rows.append({
                "case_id": cid, "span_index": i, "version_id": sp["version_id"],
                "in_pool": bool(cov),
                "covering_chunk_ids": [c["chunk_id"] for c in cov],
                "covering_chunk_id": best["chunk_id"] if best else None,
                "origin": best["origin"] if best else None,
                "channels": best["channels"] if best else None,
                "channel_class": channel_class(best) if best else None,
                "system_a_rank": best["system_a_rank"] if best else None,
                "local_bm25_rank": best["local_bm25_rank"] if best else None,
                "local_bm25_parent": best["local_bm25_parent"] if best else None,
                "projection_rank": best["projection_rank"] if best else None,
                "pre_ce_retrieval_rank": min(pre) if pre else None,
                "pre_ce_retrieval_score": best["pre_ce_retrieval_score"] if best else None,
                "ce_score": best["ce_score"] if best else None,
                "ce_rank": best["ce_rank"] if best else None,
                "final_blend_rank": best["final_rank"] if best else None,
                "in_final_top10": bool(best) and best["final_rank"] <= DEPTH,
                "pre_ce_top10": bool(pre) and min(pre) <= DEPTH,
                # localization detail, only meaningful when the span never made the pool
                "gold_doc_in_pool": sp["version_id"] in pool_versions,
                "gold_doc_in_system_a": sp["version_id"] in a_versions,
                "gold_doc_in_local_parents": sp["version_id"] in parent_versions,
                "nearest_same_document_final_rank":
                    min((c["final_rank"] for c in same_doc), default=None),
                "nearest_same_document_pre_ce_rank":
                    min((c["pre_ce_retrieval_rank"] for c in same_doc
                         if c["pre_ce_retrieval_rank"]), default=None),
                "same_document_candidates_in_pool": len(same_doc),
                "projection_window_covered_gold": any(
                    c["projection_rank"] and covers(c, sp) for c in pool),
            })
        spans.extend(rows)
        per_case[cid] = {
            "pre_ce_top10_hit": any(r["pre_ce_top10"] for r in rows),
            "final_top10_hit": any(r["in_final_top10"] for r in rows),
            "spans": rows, "by_id": by_id}

    in_pool = [s for s in spans if s["in_pool"]]
    top10 = [s for s in spans if s["in_final_top10"]]
    ranked_out = [s for s in in_pool if not s["in_final_top10"]]
    absent = [s for s in spans if not s["in_pool"]]

    # ---------- retrieval protection ----------
    rtfo = [s for s in ranked_out if s["pre_ce_top10"]]
    rtfo_cases = sorted({s["case_id"] for s in rtfo})

    # ---------- retrieval-only vs H, paired ----------
    paired = Counter()
    paired_ids = defaultdict(list)
    for cid, v in per_case.items():
        k = (("retrieval_hit" if v["pre_ce_top10_hit"] else "retrieval_miss") + "/"
             + ("H_hit" if v["final_top10_hit"] else "H_miss"))
        paired[k] += 1
        paired_ids[k].append(cid)

    # ---------- BM25 regressions ----------
    regressions = {}
    for cid in ("B09", "B28", "D27"):
        case = next(c for c in cases if c["case_id"] == cid)
        det = []
        for i, sp in enumerate(case["evidence"]):
            s = next(x for x in per_case[cid]["spans"] if x["span_index"] == i)
            bgold = next((h["rank"] for h in sorted(bm_rank[cid], key=lambda h: h["rank"])
                          if covers(h, sp)), None)
            det.append({"span_index": i, "bm25_gold_rank": bgold,
                        "system_h_global_candidate_rank": s["system_a_rank"],
                        "local_bm25_rank": s["local_bm25_rank"],
                        "projection_rank": s["projection_rank"],
                        "pre_ce_retrieval_rank": s["pre_ce_retrieval_rank"],
                        "ce_score": s["ce_score"], "ce_rank": s["ce_rank"],
                        "final_blend_rank": s["final_blend_rank"]})
        pre = [d["pre_ce_retrieval_rank"] for d in det if d["pre_ce_retrieval_rank"]]
        if pre and min(pre) <= DEPTH:
            klass = "RETRIEVAL_ALREADY_CORRECT_CE_DESTROYED"
        elif pre:
            klass = "RETRIEVAL_AND_CE_BOTH_WEAK"
        else:
            klass = "OTHER"
        regressions[cid] = {"classification": klass,
                            "bm25_case_hit_at_10": bm_case[cid]["hit_at_10"], "spans": det}

    # ---------- projection ----------
    proj_all = [c for cs in cands.values() for c in cs if c["projection_rank"]]
    proj_top10 = [c for c in proj_all if c["in_final_top10"]]
    proj_cases = {c["case_id"] for c in proj_top10}
    displaced = []
    for cid, cs in cands.items():
        occupied = sorted((c for c in cs if c["projection_rank"] and c["in_final_top10"]),
                          key=lambda c: c["final_rank"])
        nxt = sorted((c for c in cs if not c["in_final_top10"]), key=lambda c: c["final_rank"])
        for k, slot in enumerate(occupied):
            n = nxt[k] if k < len(nxt) else None
            displaced.append({
                "case_id": cid, "projection_slot_final_rank": slot["final_rank"],
                "projection_chunk_id": slot["chunk_id"],
                "next_non_projection_chunk_id": n["chunk_id"] if n else None,
                "next_final_rank": n["final_rank"] if n else None,
                "next_origin": n["origin"] if n else None,
                "next_covers_a_gold_span": bool(n) and any(
                    covers(n, sp) for sp in next(c for c in cases if c["case_id"] == cid)["evidence"])})

    payload = {
        "record_id": "NATQ2-DIAG-002-AGGREGATE",
        "diagnostic_only": True, "is_a_system_result": False,
        "systems_evaluated": 0, "ce_inference_performed": False,
        "system_h_validation_runs_consumed": 1, "unused_validation_runs": 2,
        "replay_exact": True,
        "replay_identity_sha256": sha(OUT / "NATQ2-DIAG-002-REPLAY-IDENTITY.json"),

        "stage_membership": {
            "note": "means over the 40 validation queries, from the replay",
            **{k: round(sum(s[k] for s in ident["stage_counts"]) / 40, 2)
               for k in ("system_a", "parents", "local_candidates", "local_additive_available",
                         "local_additive_selected", "fused_e", "projection_extras", "union")},
            "total_candidates_recorded": sum(s["union"] for s in ident["stage_counts"])},

        "gold_span_funnel": {
            "gold_spans": len(spans),
            "covering_candidate_in_pool": len(in_pool),
            "reached_final_top10": len(top10),
            "in_pool_ranked_out": len(ranked_out),
            "no_covering_candidate": len(absent)},

        "pre_ce_rank_distribution": {
            "ranked_out_12": dict(Counter(bucket(s["pre_ce_retrieval_rank"]) for s in ranked_out)),
            "all_in_pool_44": dict(Counter(bucket(s["pre_ce_retrieval_rank"]) for s in in_pool)),
            "final_top10_32": dict(Counter(bucket(s["pre_ce_retrieval_rank"]) for s in top10))},

        "RETRIEVAL_TOP10_TO_FINAL_OUT": {
            "definition": "gold spans already inside the top 10 of the frozen pre-CE retrieval "
                          "ordering that the CE/blend stage pushed outside the final top 10",
            "spans": f"{len(rtfo)}/57", "spans_n": len(rtfo),
            "cases": f"{len(rtfo_cases)}/40", "cases_n": len(rtfo_cases),
            "case_ids": rtfo_cases,
            "detail": [{"case_id": s["case_id"], "span_index": s["span_index"],
                        "pre_ce_retrieval_rank": s["pre_ce_retrieval_rank"],
                        "ce_rank": s["ce_rank"], "ce_score": s["ce_score"],
                        "final_blend_rank": s["final_blend_rank"]} for s in rtfo],
            "is_not_a_system_result": True},

        "retrieval_only_vs_H": {
            "note": "RETRIEVAL_ONLY_TOP10_HIT is an internal mechanism diagnostic. It is NOT a "
                    "qualified system and must never be reported as one.",
            "populations": dict(paired), "case_ids": dict(paired_ids),
            "retrieval_only_case_hit_at_10_diagnostic":
                f"{sum(1 for v in per_case.values() if v['pre_ce_top10_hit'])}/40"},

        "bm25_regressions": regressions,

        "projection": {
            "total_projection_candidates": len(proj_all),
            "gold_spans_covered_by_projection": sum(1 for s in in_pool
                                                    if s["projection_rank"] is not None),
            "projection_candidates_entering_final_top10": len(proj_top10),
            "queries_with_at_least_one_projection_top10": len(proj_cases),
            "mean_projection_top10_slots_per_query": round(len(proj_top10) / 40, 3),
            "displaced_slots": displaced,
            "next_candidate_covers_gold_count": sum(1 for d in displaced if d["next_covers_a_gold_span"]),
            "no_removal_was_simulated": True,
            "no_claim_that_removal_improves_metrics": True},

        "channel_contribution": {
            "in_pool_44": dict(Counter(s["channel_class"] for s in in_pool)),
            "final_top10_32": dict(Counter(s["channel_class"] for s in top10)),
            "ranked_out_12": dict(Counter(s["channel_class"] for s in ranked_out))},

        "localization_failures": {
            "spans": len(absent),
            "gold_doc_in_system_a": sum(1 for s in absent if s["gold_doc_in_system_a"]),
            "gold_doc_in_local_parents": sum(1 for s in absent if s["gold_doc_in_local_parents"]),
            "gold_doc_absent_from_pool_entirely": sum(1 for s in absent if not s["gold_doc_in_pool"]),
            "projection_window_covered_gold": sum(1 for s in absent if s["projection_window_covered_gold"]),
            "detail": [{k: s[k] for k in (
                "case_id", "span_index", "gold_doc_in_pool", "gold_doc_in_system_a",
                "gold_doc_in_local_parents", "same_document_candidates_in_pool",
                "nearest_same_document_final_rank", "nearest_same_document_pre_ce_rank",
                "projection_window_covered_gold")} for s in absent]},

        "candidate_ceiling_confirmation": {
            "any_span_candidate_ceiling":
                f"{sum(1 for v in per_case.values() if any(s['in_pool'] for s in v['spans']))}/40",
            "every_span_candidate_ceiling":
                f"{sum(1 for v in per_case.values() if all(s['in_pool'] for s in v['spans']))}/40",
            "candidate_span_ceiling": f"{len(in_pool)}/57",
            "matches_NATQ2_DIAG_001": None},
    }
    cc = payload["candidate_ceiling_confirmation"]
    cc["matches_NATQ2_DIAG_001"] = (cc["any_span_candidate_ceiling"] == "33/40"
                                    and cc["every_span_candidate_ceiling"] == "31/40"
                                    and cc["candidate_span_ceiling"] == "44/57")

    (OUT / "NATQ2-DIAG-002-GOLD-SPANS.json").write_text(json.dumps(
        {"record_id": "NATQ2-DIAG-002-GOLD-SPANS", "gold_spans": len(spans),
         "IN_POOL_RANKED_OUT": [s for s in ranked_out], "all_spans": spans}, indent=1) + "\n")
    (OUT / "NATQ2-DIAG-002-AGGREGATE.json").write_text(json.dumps(payload, indent=1) + "\n")

    p = payload
    print(f"funnel  spans {p['gold_span_funnel']['gold_spans']} | in pool "
          f"{p['gold_span_funnel']['covering_candidate_in_pool']} | top10 "
          f"{p['gold_span_funnel']['reached_final_top10']} | ranked out "
          f"{p['gold_span_funnel']['in_pool_ranked_out']}")
    print(f"pre-CE rank of the 12 ranked out : {p['pre_ce_rank_distribution']['ranked_out_12']}")
    print(f"pre-CE rank of all 44 in pool    : {p['pre_ce_rank_distribution']['all_in_pool_44']}")
    print(f"RETRIEVAL_TOP10_TO_FINAL_OUT     : {p['RETRIEVAL_TOP10_TO_FINAL_OUT']['spans']} spans, "
          f"{p['RETRIEVAL_TOP10_TO_FINAL_OUT']['cases']} cases")
    print(f"retrieval-only vs H              : {p['retrieval_only_vs_H']['populations']}")
    print(f"regressions                      : "
          f"{ {k: v['classification'] for k, v in regressions.items()} }")
    print(f"channel (in pool 44)             : {p['channel_contribution']['in_pool_44']}")
    print(f"ceiling matches DIAG-001         : {cc['matches_NATQ2_DIAG_001']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
