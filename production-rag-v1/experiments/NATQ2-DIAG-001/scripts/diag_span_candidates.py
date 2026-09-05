#!/usr/bin/env python3
"""NATQ2-DIAG-001 stage 2: trace every gold span through the stages the traces support.

TRACE-ONLY. Nothing is retrieved, reranked, or CE-scored. The only external read is the
frozen chunk table, used to resolve a stored chunk_id into the (version_id, char_start,
char_end) it already had at index time — that is trace resolution, not retrieval.

What the stored traces do and do not support, established before any classification:

  available   final pre-CE union pool membership. h-ce-scores.jsonl holds one CE score per
              scored candidate, so its key set IS the union pool. Verified per case:
              len(ce_scores) == union_scored == fused_e + projection_extras == final_ranked.
  available   the projection stage in isolation. ce_by_id was populated in fused_e order and
              then extended with projection extras, and JSON preserves that insertion order,
              so the trailing projection_extras keys are exactly the projection candidates.
              The count identity above is what makes this a derivation rather than a guess:
              had the two stages overlapped, union_scored would be less than their sum.
  available   CE score for every pool member, and a CE-score ordering derived from them.
  available   final top-10 rank, and its origin label (a_pool / local_bm25 / projection).
  UNAVAILABLE SYSTEM-A membership separately from local BM25 membership. merge_union_rrf
              returns one fused list and only its SIZE was persisted, so a candidate inside
              fused_e cannot be attributed to one stage or the other unless it reached the
              top 10 and carries an origin label.
  UNAVAILABLE pre-CE (RRF) rank, and final blend rank for anything outside the top 10. Only
              counts were written for the former and only ten rows for the latter.

Nothing below infers a stage result the traces do not carry.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
E = REPO / "experiments/EVAL-NATQ2-H-002"
OUT = REPO / "experiments/NATQ2-DIAG-001/NATQ2-DIAG-001-SPAN-TRACE.json"
DEPTH = 10

PINNED = {
    E / "logs/h-ranked-output.jsonl": "545eae62ff555bdd5f70ab9f24136546ff5a239c82392e179db0b896ed5bb63a",
    E / "EVAL-NATQ2-H-002-CASE-RESULTS.json": "cc289dcbe10807330df8527d3f1313ce08a3c5e41e196e89a9239408ad0371ff",
    REPO / "evals/splits/natq-002/validation.json":
        "6b7f3c90e2bfa58f244de6b2aff65e56ca3f50e2ed0886e83696aba8f5b47961",
}
CHUNK_SET = "cs_v1_control"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def covers(c: dict, sp: dict) -> bool:
    """The NATQ-002 predicate, unchanged: same version_id, intervals intersect."""
    return (c["version_id"] == sp["version_id"]
            and c["char_start"] < sp["char_end"] and c["char_end"] > sp["char_start"])


def main() -> int:
    for p, want in PINNED.items():
        if sha(p) != want:
            raise SystemExit(f"refusing to analyse: {p.name} hash changed")

    cases = json.loads((REPO / "evals/splits/natq-002/validation.json").read_text())["cases"]
    pools = {json.loads(x)["case_id"]: json.loads(x) for x in (E / "logs/h-pools.jsonl").read_text().splitlines() if x.strip()}
    ce = {}
    for x in (E / "logs/h-ce-scores.jsonl").read_text().splitlines():
        if x.strip():
            r = json.loads(x)
            ce[r["case_id"]] = r["ce_scores"]
    ranked: dict[str, list[dict]] = {}
    for x in (E / "logs/h-ranked-output.jsonl").read_text().splitlines():
        if x.strip():
            r = json.loads(x)
            ranked.setdefault(r["case_id"], []).append(r)

    # The identity that licenses the stage split. Re-asserted here, not assumed.
    for cid, p in pools.items():
        if not (len(ce[cid]) == p["union_scored"] == p["fused_e"] + p["projection_extras"]):
            raise SystemExit(f"refusing: pool identity fails on {cid}; the stage split is not derivable")

    # Resolve stored chunk_ids against the frozen chunk table. No retrieval.
    all_ids = sorted({k for m in ce.values() for k in m})
    from rag_v1.db import connect
    meta: dict[str, dict] = {}
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT chunk_id, version_id, char_start, char_end, section_path "
                    "FROM chunk WHERE chunk_set_id=%s AND chunk_id = ANY(%s)", (CHUNK_SET, all_ids))
        for cid_, vid, a, b, spath in cur.fetchall():
            meta[cid_] = {"version_id": vid, "char_start": a, "char_end": b, "section_path": spath}
    missing = [i for i in all_ids if i not in meta]
    if missing:
        raise SystemExit(f"refusing: {len(missing)} pool chunk_ids absent from {CHUNK_SET}")

    rows = []
    for case in cases:
        cid = case["case_id"]
        pool_ids = list(ce[cid])
        n_fused = pools[cid]["fused_e"]
        fused_ids, proj_ids = set(pool_ids[:n_fused]), set(pool_ids[n_fused:])
        pool_meta = [dict(meta[i], chunk_id=i) for i in pool_ids]
        pool_versions = {m["version_id"] for m in pool_meta}
        # CE-score ordering over the pool, derived from stored scores only.
        ce_order = {k: i + 1 for i, (k, _) in enumerate(
            sorted(ce[cid].items(), key=lambda kv: (-kv[1], kv[0])))}
        top = {r["chunk_id"]: r for r in ranked.get(cid, [])}

        for i, sp in enumerate(case["evidence"]):
            cov = [m["chunk_id"] for m in pool_meta if covers(m, sp)]
            cov_top = [c for c in cov if c in top]
            best_final = min((top[c]["rank"] for c in cov_top), default=None)
            best_ce = min((ce_order[c] for c in cov), default=None)
            rows.append({
                "case_id": cid, "span_index": i,
                "version_id": sp["version_id"],
                "gold_doc_in_pool": sp["version_id"] in pool_versions,
                "covering_chunk_ids_in_pool": cov,
                "n_covering_in_pool": len(cov),
                "in_final_pre_ce_pool": bool(cov),
                "via_projection": any(c in proj_ids for c in cov),
                "via_fused_e_systemA_or_localbm25": any(c in fused_ids for c in cov),
                "present_in_global_pool": "UNAVAILABLE_STAGE_MEMBERSHIP_NOT_PERSISTED",
                "present_via_local_bm25": "UNAVAILABLE_STAGE_MEMBERSHIP_NOT_PERSISTED",
                "best_pre_ce_rank": "UNAVAILABLE_RRF_RANK_NOT_PERSISTED",
                "best_ce_score_rank_in_pool": best_ce,
                "best_ce_score": max((ce[cid][c] for c in cov), default=None),
                "final_blend_rank": best_final,
                "final_blend_rank_note": None if best_final else "UNAVAILABLE_BEYOND_TOP10",
                "in_top10": best_final is not None,
                "top10_origin": top[min(cov_top, key=lambda c: top[c]["rank"])]["origin"] if cov_top else None,
            })

    n = len(rows)
    hit = [r for r in rows if r["in_top10"]]
    in_pool = [r for r in rows if r["in_final_pre_ce_pool"]]
    doc_in_pool = [r for r in rows if r["gold_doc_in_pool"]]
    payload = {
        "record_id": "NATQ2-DIAG-001-SPAN-TRACE",
        "trace_only": True, "retrieval_performed": False, "reranking_performed": False,
        "ce_inference_performed": False, "parameters_changed": False,
        "external_reads": [f"frozen chunk table {CHUNK_SET}: chunk_id -> version_id, char offsets"],
        "evaluation_depth": DEPTH,
        "gold_spans": n,
        "stage_availability": {
            "system_a_global_pool": "UNAVAILABLE — membership not persisted separately from local BM25",
            "local_bm25_additive": "UNAVAILABLE — membership not persisted separately from SYSTEM-A",
            "fused_e_systemA_plus_localbm25": "AVAILABLE (merged, not attributable within)",
            "projection_candidates": "AVAILABLE (trailing projection_extras keys, count-identity verified)",
            "final_pre_ce_union_pool": "AVAILABLE",
            "post_ce_ordering": "AVAILABLE as a CE-score ordering derived from stored scores",
            "pre_ce_rrf_rank": "UNAVAILABLE — only pool sizes were persisted",
            "final_blend_rank": "AVAILABLE for top 10 only; beyond that only 'rank > 10' is known",
            "final_top10": "AVAILABLE with origin labels"},
        "totals": {
            "spans": n,
            "gold_doc_present_in_union_pool": len(doc_in_pool),
            "covering_candidate_in_union_pool": len(in_pool),
            "reached_top10": len(hit),
            "in_pool_but_not_top10": len(in_pool) - len(hit),
            "no_covering_candidate_in_pool": n - len(in_pool),
            "gold_doc_absent_from_pool": n - len(doc_in_pool)},
        "spans": rows,
    }
    OUT.write_text(json.dumps(payload, indent=1) + "\n")
    t = payload["totals"]
    print(f"gold spans                          {t['spans']}")
    print(f"gold document present in pool       {t['gold_doc_present_in_union_pool']}")
    print(f"covering candidate in union pool    {t['covering_candidate_in_union_pool']}")
    print(f"reached final top 10                {t['reached_top10']}")
    print(f"in pool but ranked out              {t['in_pool_but_not_top10']}")
    print(f"no covering candidate at all        {t['no_covering_candidate_in_pool']}")
    print(f"gold document never in pool         {t['gold_doc_absent_from_pool']}")
    print(f"\nspan trace sha256 {sha(OUT)}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(REPO / "src"))
    raise SystemExit(main())
