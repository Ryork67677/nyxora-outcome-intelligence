#!/usr/bin/env python3
"""NATQ2-DIAG-002 — replay SYSTEM-H candidate generation and reconstruct its ranking without CE.

This is a DEVELOPMENT TRACE RECONSTRUCTION on exposed NATQ-002 validation data. It is not
a SYSTEM-H validation run, not a retry, and does not increment
validation_runs_consumed, which stays at 1.

What is replayed: the deterministic candidate stages only — SYSTEM-A pool, parent
selection, per-parent local BM25, the labelled RRF union, and the projection channel.
Every implementation is imported verbatim from the recovered lineage at
origin/grok/v2-natq-20260903 and hash-pinned; nothing is reconstructed from prose.

What is NOT re-run: the cross-encoder. Every CE score is the persisted value from
EVAL-NATQ2-H-002, joined by (case_id, chunk_id). The join is required to be a bijection
against the replayed pool; anything less stops the run rather than approximating.

CE precision, stated up front because it bounds what "exact" can mean here: the per-case
CE map was persisted rounded to 6 decimals, while the 400 final top-10 rows carry full
float precision. Both are used — full precision wherever the ranked output supplies it,
6dp otherwise — and the residual blend-score deviation is measured and reported rather
than assumed negligible. Reproduction is judged on membership, the 400 top-10 rows, the
40-case vector and the aggregate metrics, all of which must match exactly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

MAIN = Path(__file__).resolve().parents[4]
E2 = MAIN / "experiments/EVAL-NATQ2-H-002"
OUT = MAIN / "experiments/RAG-V2/NATQ2-DIAG-002"
SPLIT = MAIN / "evals/splits/natq-002"
DEPTH = 10

PINNED_SOURCES = {
    E2 / "EVAL-NATQ2-H-002-RESULTS.json": "ce01aeee9bebd811b9a3ae1a2f58983ca607e3bb8f18096b232a0a2ddafff9ce",
    E2 / "EVAL-NATQ2-H-002-CASE-RESULTS.json": "cc289dcbe10807330df8527d3f1313ce08a3c5e41e196e89a9239408ad0371ff",
    E2 / "logs/h-ranked-output.jsonl": "545eae62ff555bdd5f70ab9f24136546ff5a239c82392e179db0b896ed5bb63a",
    E2 / "logs/h-ce-scores.jsonl": "a7be8e34b825d918a3a5fc2392fe083faae3679cbec01fb3406c439c693088ab",
    E2 / "logs/h-pools.jsonl": "5cfb7f4abb2d193b235a7f2f36d359aeeeb453564d73207cc7404729a0babf84",
    E2 / "scripts/natq2_scorer.py": "96447990b75f94e2f1e3daad1407eb1cdac53f7e4967ceb4ecdc4c0f8119b060",
    SPLIT / "validation.json": "6b7f3c90e2bfa58f244de6b2aff65e56ca3f50e2ed0886e83696aba8f5b47961",
}
H_CONFIG_HASH = "7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def gate(wt: Path) -> dict:
    for p, want in PINNED_SOURCES.items():
        if sha(p) != want:
            raise SystemExit(f"STOP: source {p.name} hash changed\n  got {sha(p)}\n  want {want}")
    log = SPLIT / "reserve-access.log.jsonl"
    if log.stat().st_size != 0:
        raise SystemExit("STOP: the reserve access log is not empty")
    lock = json.loads((SPLIT / "reserve.lock.json").read_text())
    if lock["reserve_frozen"] is not True or lock["reserve_count"] != 60:
        raise SystemExit("STOP: the reserve lock is not frozen at 60 cases")

    man = json.loads((MAIN / "experiments/SYSTEM-H/SYSTEM-H-RUNTIME-MANIFEST.json").read_text())
    if man["authoritative_system_h_config_hash"] != H_CONFIG_HASH:
        raise SystemExit("STOP: manifest config hash is not authoritative")
    impl = {}
    for group in ("code", "configs"):
        for name, rec in man[group].items():
            got = sha(wt / rec["path"])
            if got != rec["sha256"]:
                raise SystemExit(f"STOP: implementation {name} differs from the recovered ref")
            impl[f"{group}.{name}"] = {"path": rec["path"], "sha256": got}
    return {"sources": {str(p.relative_to(MAIN)): v for p, v in PINNED_SOURCES.items()},
            "implementations": impl, "implementation_count": len(impl),
            "recovered_from_ref": "origin/grok/v2-natq-20260903",
            "reserve_access_log_bytes": 0,
            "reserve_lock": {"reserve_frozen": True, "reserve_count": 60}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True)
    a = ap.parse_args()
    wt = Path(a.worktree).resolve()
    identity = gate(wt)
    print(f"gate ok — {identity['implementation_count']} pinned implementations, "
          f"{len(identity['sources'])} pinned sources")

    os.chdir(wt)
    for p in ("", "src", "experiments/EXP-015/scripts", "experiments/EXP-018/scripts",
              "experiments/EXP-018B/scripts", "experiments/EXP-017/scripts",
              "experiments/PERF-003/scripts", "experiments/EXP-019A/scripts"):
        sys.path.insert(0, str(wt / p) if p else str(wt))
    sys.path.insert(0, str(E2 / "scripts"))

    from rag_v1.embedders_transformer import TransformerEncoder
    from rag_v1.query_cache import CachedQueryEmbedder
    from local_bm25_batched import (additive_extras_ordered, cap_local_lists,
                                    local_bm25_per_parent_batched)
    from projection_retrieval import map_to_canonical_extras, projection_rrf
    from run_exp017 import L, P, apply_blend_exp017, load_control_chunks
    from run_exp018_development import hit_as_row
    from run_exp019a import apply_blend_exp019a
    from system_e import (PARENT_N, TRANSFORMER_FINGERPRINT, TRANSFORMER_MODEL, W,
                          apply_blend, merge_union_rrf, parent_version_ids,
                          retrieve_system_a_pool)
    from natq2_scorer import aggregate, score_case

    encoder = TransformerEncoder(max_seq=512).load()
    if encoder.model_version != TRANSFORMER_FINGERPRINT:
        raise SystemExit("STOP: encoder fingerprint mismatch")
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)
    chunks_by_id = load_control_chunks()
    if len(chunks_by_id) != 14209:
        raise SystemExit(f"STOP: control chunk cache {len(chunks_by_id)} != 14209")

    # Stored CE scores. 6dp map for the whole pool; full precision for the 400 top-10 rows.
    stored_ce = {}
    for line in (E2 / "logs/h-ce-scores.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            stored_ce[r["case_id"]] = dict(r["ce_scores"])
    stored_top: dict[str, dict[str, dict]] = {}
    for line in (E2 / "logs/h-ranked-output.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            stored_top.setdefault(r["case_id"], {})[r["chunk_id"]] = r
    precise = 0
    for cid, rows in stored_top.items():
        for ch, r in rows.items():
            if r.get("ce_score") is not None and ch in stored_ce[cid]:
                stored_ce[cid][ch] = float(r["ce_score"])
                precise += 1
    print(f"stored CE: {sum(len(v) for v in stored_ce.values())} scores, "
          f"{precise} restored to full precision from the ranked output")

    cases = json.loads((SPLIT / "validation.json").read_text())["cases"]
    stored_case = {c["case_id"]: c for c in
                   json.loads((E2 / "EVAL-NATQ2-H-002-CASE-RESULTS.json").read_text())["cases"]}
    stored_metrics = json.loads((E2 / "EVAL-NATQ2-H-002-RESULTS.json").read_text())["metrics"]

    cand_fh = (OUT / "NATQ2-DIAG-002-CANDIDATES.jsonl").open("w", encoding="utf-8")
    per_case, mismatches, blend_dev, stage_counts = [], [], [], []

    print(f"\nreplaying candidate generation over {len(cases)} validation queries (no CE)...")
    for case in cases:
        cid, q = case["case_id"], case["question"]

        a_pool = retrieve_system_a_pool(q, transformer)
        parents = parent_version_ids(a_pool, PARENT_N)
        local = local_bm25_per_parent_batched(q, parents, W)
        a_ids = {h.chunk_id for h in a_pool}
        extras = additive_extras_ordered(local, a_ids)
        selected_extras = extras[:L]
        capped_local = cap_local_lists(local, a_ids, selected_extras)
        fused_e, _new, a_ids = merge_union_rrf(a_pool, capped_local)
        c_e_ids = {h.chunk_id for h in fused_e}

        fused_p = projection_rrf(q, TRANSFORMER_MODEL, transformer)
        mapped = map_to_canonical_extras(fused_p, c_e_ids, P)

        # ---- per-stage membership, scores and ranks, recorded for every candidate ----
        a_by_id = {h.chunk_id: h for h in a_pool}
        local_by_id: dict[str, dict] = {}
        for vid, hits in local.items():
            for h in hits:
                prev = local_by_id.get(h.chunk_id)
                if prev is None or h.rank < prev["local_bm25_rank"]:
                    local_by_id[h.chunk_id] = {"local_bm25_parent": vid,
                                               "local_bm25_rank": int(h.rank),
                                               "local_bm25_score": float(h.score)}
        proj_rank = {c: i + 1 for i, c in enumerate(mapped["C_P"])}
        pre_ce = {h.chunk_id: {"pre_ce_retrieval_rank": int(h.rank),
                               "pre_ce_retrieval_score": float(h.score)} for h in fused_e}

        # ---- join the STORED CE scores; require an exact bijection ----
        pool_ids = [h.chunk_id for h in fused_e] + list(mapped["C_P"])
        if len(set(pool_ids)) != len(pool_ids):
            raise SystemExit(f"STOP: {cid} replayed pool contains a duplicate chunk_id")
        ce_map = stored_ce.get(cid)
        if ce_map is None:
            raise SystemExit(f"STOP: no persisted CE scores for {cid}")
        missing = [c for c in pool_ids if c not in ce_map]
        orphan = [c for c in ce_map if c not in set(pool_ids)]
        if missing or orphan:
            raise SystemExit(
                f"STOP: CE join is not a bijection on {cid} — "
                f"{len(missing)} replayed candidates lack a persisted score, "
                f"{len(orphan)} persisted scores match no replayed candidate")
        ce_by_id = {c: float(ce_map[c]) for c in pool_ids}
        ce_rank = {c: i + 1 for i, (c, _) in enumerate(
            sorted(ce_by_id.items(), key=lambda kv: (-kv[1], kv[0])))}

        # ---- reconstruct the frozen ranking from replayed retrieval + stored CE ----
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
        extra_rows = []
        for ch in mapped["C_P"]:
            rec = chunks_by_id[ch]
            extra_rows.append({"chunk_id": ch, "version_id": rec["version_id"],
                               "section_path": rec["section_path"], "char_start": rec["char_start"],
                               "char_end": rec["char_end"], "text": rec["text"],
                               "origin": "projection", "in_a_pool": False,
                               "projection_fused": mapped["C_P_scores"][ch]})
        x_rows = apply_blend_exp017(e_rows, extra_rows, ce_by_id)
        y_rows = apply_blend_exp019a(x_rows)

        ranked = sorted(y_rows, key=lambda r: r["exp019a_rank"])
        hits = [{"rank": int(r["exp019a_rank"]), "chunk_id": r["chunk_id"],
                 "version_id": r["version_id"], "char_start": r["char_start"],
                 "char_end": r["char_end"], "section_path": r.get("section_path"),
                 "origin": r.get("origin")} for r in ranked if int(r["exp019a_rank"]) <= DEPTH]

        # ---- compare against the frozen run ----
        st = stored_top.get(cid, {})
        for h in hits:
            s = st.get(h["chunk_id"])
            if s is None or s["rank"] != h["rank"]:
                mismatches.append({"case_id": cid, "chunk_id": h["chunk_id"],
                                   "replay_rank": h["rank"],
                                   "stored_rank": s["rank"] if s else None})
        if len(hits) != len(st):
            mismatches.append({"case_id": cid, "reason": "top10 row count differs",
                               "replay": len(hits), "stored": len(st)})

        by_id = {r["chunk_id"]: r for r in y_rows}
        for ch, s in st.items():
            r = by_id.get(ch)
            if r is not None and s.get("ce_score") is not None:
                blend_dev.append(abs(float(r["ce_score"]) - float(s["ce_score"])))

        for r in ranked:
            ch = r["chunk_id"]
            channels = []
            if ch in a_ids:
                channels.append("system_a")
            if ch in local_by_id:
                channels.append("local_bm25")
            if ch in proj_rank:
                channels.append("projection")
            cand_fh.write(json.dumps({
                "case_id": cid, "chunk_id": ch,
                "version_id": r["version_id"], "char_start": r["char_start"],
                "char_end": r["char_end"], "section_path": r.get("section_path"),
                "channels": channels, "origin": r.get("origin"),
                "in_system_a": ch in a_ids,
                "system_a_rank": int(a_by_id[ch].rank) if ch in a_by_id else None,
                "system_a_score": float(a_by_id[ch].score) if ch in a_by_id else None,
                "local_bm25_parent": local_by_id.get(ch, {}).get("local_bm25_parent"),
                "local_bm25_rank": local_by_id.get(ch, {}).get("local_bm25_rank"),
                "local_bm25_score": local_by_id.get(ch, {}).get("local_bm25_score"),
                "projection_rank": proj_rank.get(ch),
                "projection_score": mapped["C_P_scores"].get(ch),
                "in_fused_e": ch in c_e_ids,
                "pre_ce_retrieval_rank": pre_ce.get(ch, {}).get("pre_ce_retrieval_rank"),
                "pre_ce_retrieval_score": pre_ce.get(ch, {}).get("pre_ce_retrieval_score"),
                "ce_score": ce_by_id[ch], "ce_rank": ce_rank[ch],
                "retrieval_norm": r.get("retrieval_norm"), "ce_norm": r.get("ce_norm"),
                "blend_score_exp017": r.get("blend_score_exp017"),
                "exp017_rank": r.get("exp017_rank"),
                "final_blend_score": r["blend_score"],
                "final_rank": int(r["exp019a_rank"]),
                "in_final_top10": int(r["exp019a_rank"]) <= DEPTH}) + "\n")

        stage_counts.append({"case_id": cid, "system_a": len(a_pool), "parents": len(parents),
                             "local_candidates": sum(len(v) for v in local.values()),
                             "local_additive_available": len(extras),
                             "local_additive_selected": len(selected_extras),
                             "fused_e": len(fused_e), "projection_extras": len(mapped["C_P"]),
                             "union": len(y_rows)})
        r = score_case(case, hits, DEPTH)
        per_case.append(r)
        print(f"  {cid} pool={len(y_rows):>3} hit={int(r['hit_at_10'])} ranks={r['span_ranks']}", flush=True)

    cand_fh.close()
    metrics = aggregate(per_case)

    vec_mismatch = [c["case_id"] for c in per_case
                    if c["hit_at_10"] != stored_case[c["case_id"]]["hit_at_10"]]
    rank_mismatch = [c["case_id"] for c in per_case
                     if list(c["span_ranks"]) != list(stored_case[c["case_id"]]["span_ranks"])]
    metric_mismatch = {k: (metrics[k], stored_metrics[k]) for k in metrics
                       if k in stored_metrics and metrics[k] != stored_metrics[k]}

    exact = not mismatches and not vec_mismatch and not rank_mismatch and not metric_mismatch
    identity.update({
        "record_id": "NATQ2-DIAG-002-REPLAY-IDENTITY",
        "is_a_system_h_validation_run": False, "is_a_retry": False,
        "system_h_validation_runs_consumed": 1, "unused_validation_runs": 2,
        "ce_inference_performed": False,
        "ce_scores_source": "persisted EVAL-NATQ2-H-002 traces, joined by (case_id, chunk_id)",
        "ce_join_is_bijective_on_every_case": True,
        "ce_precision_note": ("The per-case CE map was persisted at 6dp; the 400 top-10 rows "
                              "carry full precision and were used where available."),
        "ce_full_precision_values_used": precise,
        "max_ce_roundtrip_deviation_on_top10": max(blend_dev) if blend_dev else 0.0,
        "reproduction": {
            "final_top10_row_mismatches": len(mismatches),
            "mismatch_detail": mismatches[:20],
            "case_hit_vector_mismatches": vec_mismatch,
            "per_case_span_rank_mismatches": rank_mismatch,
            "aggregate_metric_mismatches": metric_mismatch,
            "replayed_metrics": metrics,
            "stored_metrics": {k: stored_metrics[k] for k in metrics if k in stored_metrics},
            "EXACT": exact},
        "stage_counts": stage_counts,
    })
    (OUT / "NATQ2-DIAG-002-REPLAY-IDENTITY.json").write_text(json.dumps(identity, indent=1) + "\n")

    print("\n" + "=" * 62)
    print(f"top-10 row mismatches      {len(mismatches)}")
    print(f"case hit vector mismatches {len(vec_mismatch)}")
    print(f"span rank mismatches       {len(rank_mismatch)}")
    print(f"aggregate metric mismatch  {metric_mismatch or 'none'}")
    print(f"max CE roundtrip deviation {max(blend_dev) if blend_dev else 0.0:.3e}")
    print(f"REPLAY IDENTITY EXACT      {exact}")
    if not exact:
        print("\nSTOP: reconstruction is not exact. Reconstructed pre-CE traces must NOT be "
              "used for architectural decisions.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
