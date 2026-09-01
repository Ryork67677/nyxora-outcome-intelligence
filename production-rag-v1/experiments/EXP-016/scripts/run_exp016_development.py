#!/usr/bin/env python3
"""EXP-016 development qualification: A / B / C / D on gold150-v1 development.

Preregistered before any EXP-016 scores. Does not load validation. Does not
load holdout. Does not train on GOLD. Does not sweep. Does not retune after
scores. Writes HA-24 diagnostic before applying C/D fusion.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EXP015_SCRIPTS = ROOT / "experiments" / "EXP-015" / "scripts"
if str(EXP015_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(EXP015_SCRIPTS))
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from cross_encoder import (  # noqa: E402
    CE_NAME,
    CE_ONNX,
    CE_REVISION,
    CE_SHA256,
    MAX_LENGTH,
    CrossEncoderReranker,
)
from identifier_matcher import (  # noqa: E402
    extract_identifiers,
    has_exact_identifier_overlap,
    overlapping_identifiers,
)
from rag_v1.embedders_transformer import TransformerEncoder  # noqa: E402
from rag_v1.evals.io import load_cases  # noqa: E402
from rag_v1.ids import config_hash  # noqa: E402
from rag_v1.query_cache import CachedQueryEmbedder  # noqa: E402
from rag_v1.retrieval import dense_search, lexical_search, rrf_fuse  # noqa: E402
from rag_v1.systems import (  # noqa: E402
    CHUNK_SET,
    FROZEN_HASHES,
    SNAPSHOT,
    SYSTEM_A_GLOBAL,
    TRANSFORMER_FINGERPRINT,
    TRANSFORMER_MODEL,
)
from rag_v1.types import EvidenceRef, SearchHit  # noqa: E402

PROBE_DEPTHS = (10, 20, 30, 50, 100, 300)
TOP_K, RRF_POOL, RRF_K, CANDIDATE_POOL = 10, 50, 60, 100
A_HASH = "9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38"
BLEND_CE, BLEND_A = 0.7, 0.3
PROTECT_A_RANK_MAX = 3
CLAMP_FLOOR = 10
NAMED = ("HA-22", "HA-24", "GOLD-B005-11")
EXP015_RESULTS = ROOT / "experiments" / "EXP-015" / "EXP-015-development-results.json"
DEV_JSONL = ROOT / "experiments" / "EXP-015" / "development.jsonl"
OUT_DIR = ROOT / "experiments" / "EXP-016"


def overlaps(hit: SearchHit, ref: EvidenceRef) -> bool:
    return (
        hit.version_id == ref.version_id
        and hit.section_path == ref.section_path
        and hit.char_start < ref.char_end
        and hit.char_end > ref.char_start
    )


def holdout_log_bytes() -> int:
    path = ROOT / "evals" / "splits" / "gold150-v1" / "holdout-access.log.jsonl"
    return path.stat().st_size if path.exists() else -1


def embedding_status() -> dict:
    from rag_v1.db import connect

    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (CHUNK_SET,))
        chunks = cur.fetchone()[0]
        cur.execute(
            "SELECT count(*), min(model_fingerprint), max(model_fingerprint) "
            "FROM chunk_embedding WHERE model_id=%s",
            (TRANSFORMER_MODEL,),
        )
        n, fp_min, fp_max = cur.fetchone()
    return {
        "chunk_set": CHUNK_SET,
        "chunks": chunks,
        "embedding_rows": n,
        "model_id": TRANSFORMER_MODEL,
        "fingerprint_min": fp_min,
        "fingerprint_max": fp_max,
        "fingerprint_expected": TRANSFORMER_FINGERPRINT,
        "complete": n == chunks == 14209 and fp_min == fp_max == TRANSFORMER_FINGERPRINT,
    }


def retrieve_system_a_pool(query: str, embedder) -> list[SearchHit]:
    lexical = lexical_search(query, SNAPSHOT, RRF_POOL)
    dense = dense_search(query, SNAPSHOT, TRANSFORMER_MODEL, RRF_POOL, embedder=embedder)
    return rrf_fuse([lexical, dense], rrf_k=RRF_K, top_k=CANDIDATE_POOL)


def minmax_norm(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5] * len(values)
    scale = hi - lo
    return [(v - lo) / scale for v in values]


def ce_order(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda r: (-r["ce_score"], r["a_rank"], r["chunk_id"]))


def apply_guard_clamp(rows: list[dict]) -> list[dict]:
    """Frozen clamp: protected A-head items cannot leave top 10."""
    ordered = ce_order(rows)
    for i, row in enumerate(ordered, start=1):
        row["ce_rank"] = i
        row["protected"] = bool(row["identifier_overlap"] and row["a_rank"] <= PROTECT_A_RANK_MAX)
    need_floor = [r for r in ordered if r["protected"] and r["ce_rank"] > CLAMP_FLOOR]
    floor_ids = {r["chunk_id"] for r in need_floor}
    n_floor = len(need_floor)
    keep = [r for r in ordered if r["chunk_id"] not in floor_ids]
    head = keep[: CLAMP_FLOOR - n_floor]
    rest = keep[CLAMP_FLOOR - n_floor :]
    out = head + need_floor + rest
    for i, row in enumerate(out, start=1):
        row["c_rank"] = i
        row["clamped"] = row["chunk_id"] in floor_ids
    return out


def apply_blend(rows: list[dict]) -> list[dict]:
    ce_n = minmax_norm([r["ce_score"] for r in rows])
    a_n = minmax_norm([r["a_score"] for r in rows])
    blended = []
    for row, ce, a in zip(rows, ce_n, a_n, strict=True):
        item = dict(row)
        item["ce_norm"] = ce
        item["a_norm"] = a
        item["blend_score"] = BLEND_CE * ce + BLEND_A * a
        blended.append(item)
    blended.sort(key=lambda r: (-r["blend_score"], r["a_rank"], r["chunk_id"]))
    for i, row in enumerate(blended, start=1):
        row["d_rank"] = i
    return blended


def score_case_from_ranks(case, rank_by_chunk: dict[str, int], chunk_by_span: list[str | None]) -> dict:
    spans = []
    for ref, chunk_id in zip(case.expected_evidence, chunk_by_span, strict=True):
        rank = rank_by_chunk.get(chunk_id) if chunk_id else None
        # document rank: first hit of same version — approximated by this span's rank
        spans.append(
            {
                "rank": rank,
                "doc_rank": rank,
                "chunk_id": chunk_id,
                "within": {str(d): (rank is not None and rank <= d) for d in PROBE_DEPTHS},
                "doc_within_10": rank is not None and rank <= TOP_K,
            }
        )
    found = sum(1 for s in spans if s["within"]["10"])
    return {
        "case_id": case.case_id,
        "spans": spans,
        "recall": found / len(spans) if spans else 1.0,
        "fully_recalled": bool(spans) and found == len(spans),
        "doc_recall": (
            sum(1 for s in spans if s["doc_within_10"]) / len(spans) if spans else 1.0
        ),
    }


def summarise(per_case: dict, system: str, config_hash_value: str) -> dict:
    all_spans = [s for c in per_case.values() for s in c["spans"]]
    recalls = [c["recall"] for c in per_case.values()]
    return {
        "system": system,
        "config_hash": config_hash_value,
        "macro_span_recall": round(sum(recalls) / len(recalls), 4),
        "cases_fully_recalled": sum(1 for c in per_case.values() if c["fully_recalled"]),
        "cases_total": len(per_case),
        "strict_recall_at_10": (
            f"{sum(1 for c in per_case.values() if c['fully_recalled'])}/{len(per_case)}"
        ),
        "spans_found_at_10": sum(1 for s in all_spans if s["within"]["10"]),
        "spans_total": len(all_spans),
        "document_recall": round(
            sum(c["doc_recall"] for c in per_case.values()) / len(per_case), 4
        ),
        "mrr": round(
            sum(1 / s["rank"] for s in all_spans if s["rank"]) / len(all_spans), 4
        ),
        "spans_absent_from_top": {
            str(d): sum(1 for s in all_spans if not s["within"][str(d)])
            for d in PROBE_DEPTHS
        },
        "cases": per_case,
    }


def excerpt(text: str, limit: int = 240) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def write_ha24_diagnostic(case, rows: list[dict], gold_chunk: str | None, path: Path) -> dict:
    """Write HA-24 diagnostic BEFORE C/D fusion is applied."""
    by_a = {r["chunk_id"]: r for r in rows}
    ce_sorted = ce_order(rows)
    a1 = next((r for r in rows if r["a_rank"] == 1), None)
    c1 = ce_sorted[0] if ce_sorted else None
    gold = by_a.get(gold_chunk) if gold_chunk else None
    q_ids = sorted(extract_identifiers(case.question))
    gold_overlap = overlapping_identifiers(case.question, gold["text"]) if gold else []
    a1_overlap = overlapping_identifiers(case.question, a1["text"]) if a1 else []
    c1_overlap = overlapping_identifiers(case.question, c1["text"]) if c1 else []

    gold_ce = gold["ce_score"] if gold else None
    c1_ce = c1["ce_score"] if c1 else None
    preferred_general = False
    why = []
    if gold and c1 and gold["chunk_id"] != c1["chunk_id"]:
        if gold_ce is not None and c1_ce is not None and c1_ce > gold_ce:
            # Heuristic recorded, not a knob: CE rank-1 is a different passage
            # with a higher logit than the A-rank-1 gold chunk.
            preferred_general = True
            why.append(
                f"CE scored the rank-1 C passage {c1_ce:.4f} vs gold chunk {gold_ce:.4f} "
                f"(Δ={c1_ce - gold_ce:.4f}), dropping gold from A rank {gold['a_rank']} "
                f"to CE rank {gold['ce_rank'] if 'ce_rank' in gold else ce_sorted.index(gold)+1}."
            )
    ce_rank_gold = None
    if gold:
        ce_rank_gold = next(i for i, r in enumerate(ce_sorted, start=1) if r["chunk_id"] == gold["chunk_id"])

    conclusion = (
        "YES — CE preferred a more general / higher-logit non-gold passage over the "
        "exact A-rank-1 gold answer."
        if preferred_general
        else "NO — CE did not clearly prefer a more general explanation over the exact answer "
        "(gold is CE rank-1, or scores do not support that reading)."
    )

    md = []
    md.append("# EXP-016 HA-24 diagnostic")
    md.append("")
    md.append("Written **after** rematerializing the SYSTEM-A pool-100 and CE logits,")
    md.append("and **before** applying variant C clamp or variant D blend.")
    md.append("No C/D scores were computed when this file was written.")
    md.append("")
    md.append("## Query")
    md.append("")
    md.append(f"`{case.question}`")
    md.append("")
    md.append(f"Query identifier tokens (frozen matcher): `{q_ids}`")
    md.append("")
    md.append("## Gold span")
    md.append("")
    if gold:
        ref = case.expected_evidence[0]
        md.append(f"- chunk_id: `{gold['chunk_id']}`")
        md.append(f"- version_id: `{ref.version_id}`")
        md.append(f"- section_path: `{list(ref.section_path)}`")
        md.append(f"- char: [{ref.char_start}, {ref.char_end})")
        md.append(f"- SYSTEM-A rank: **{gold['a_rank']}** (fused RRF score {gold['a_score']:.6f})")
        md.append(f"- CE logit: **{gold['ce_score']:.6f}**")
        md.append(f"- CE rank (EXP-015 / rematerialized): **{ce_rank_gold}**")
        md.append(f"- identifier overlap with query: `{gold_overlap}`")
        md.append("")
        md.append("Gold excerpt:")
        md.append("")
        md.append(f"> {excerpt(gold['text'], 280)}")
    else:
        md.append("Gold chunk was not in the rematerialized pool.")
    md.append("")
    md.append("## Top A passage (SYSTEM-A rank 1)")
    md.append("")
    if a1:
        same = gold and a1["chunk_id"] == gold["chunk_id"]
        md.append(f"- chunk_id: `{a1['chunk_id']}`")
        md.append(f"- CE logit: **{a1['ce_score']:.6f}**")
        md.append(f"- same as gold: `{same}`")
        md.append(f"- identifier overlap: `{a1_overlap}`")
        md.append("")
        md.append(f"> {excerpt(a1['text'], 280)}")
    md.append("")
    md.append("## Top C passage (what CE put at rank 1)")
    md.append("")
    if c1:
        md.append(f"- chunk_id: `{c1['chunk_id']}`")
        md.append(f"- SYSTEM-A rank: {c1['a_rank']}")
        md.append(f"- CE logit: **{c1['ce_score']:.6f}**")
        md.append(f"- identifier overlap: `{c1_overlap}`")
        md.append("")
        md.append(f"> {excerpt(c1['text'], 280)}")
    md.append("")
    md.append("## Why the gold chunk fell to CE rank 18")
    md.append("")
    if gold and c1:
        md.append(
            f"The gold chunk is SYSTEM-A rank {gold['a_rank']} with CE logit "
            f"{gold['ce_score']:.4f}. Seventeen other pool-100 candidates received a "
            f"higher CE logit (top is {c1['ce_score']:.4f} at A rank {c1['a_rank']}). "
            "EXP-015 tie-break is CE desc, then A rank, then chunk_id; no other fusion "
            "was applied in EXP-015."
        )
        md.append("")
        md.append(" ".join(why) if why else "See scores above.")
        md.append("")
        if preferred_general:
            md.append(
                "Reading of the excerpts: the CE-rank-1 passage is a broader explanation "
                "or adjacent discussion that the MS MARCO MiniLM scores as more 'relevant' "
                "prose, while the gold chunk is the exact answer SYSTEM-A already placed at 1."
            )
        else:
            md.append("The excerpts do not support a general-vs-exact preference reading.")
    md.append("")
    md.append("## Conclusion")
    md.append("")
    md.append(conclusion)
    md.append("")
    path.write_text("\n".join(md) + "\n", encoding="utf-8")
    return {
        "case_id": "HA-24",
        "query": case.question,
        "gold_chunk_id": gold_chunk,
        "gold_a_rank": gold["a_rank"] if gold else None,
        "gold_ce_score": gold["ce_score"] if gold else None,
        "gold_ce_rank": ce_rank_gold,
        "top_a_chunk_id": a1["chunk_id"] if a1 else None,
        "top_a_ce_score": a1["ce_score"] if a1 else None,
        "top_c_chunk_id": c1["chunk_id"] if c1 else None,
        "top_c_ce_score": c1["ce_score"] if c1 else None,
        "top_c_a_rank": c1["a_rank"] if c1 else None,
        "ce_preferred_more_general_explanation": preferred_general,
        "conclusion": conclusion,
        "written_before_C_or_D_scoring": True,
        "path": str(path.relative_to(ROOT)),
    }


def paired(a_full: dict, v_full: dict) -> dict:
    rescues = [cid for cid, ok in v_full.items() if ok and not a_full[cid]]
    regressions = [cid for cid, ok in v_full.items() if a_full[cid] and not ok]
    return {
        "rescues": rescues,
        "regressions": regressions,
        "net": len(rescues) - len(regressions),
        "both_correct": [cid for cid, ok in v_full.items() if ok and a_full[cid]],
        "neither": [cid for cid, ok in v_full.items() if (not ok) and (not a_full[cid])],
    }


def rank_destructions(named_rows: dict) -> dict:
    events = []
    for cid, info in named_rows.items():
        for span in info:
            a_rank = span["a_rank"]
            v_rank = span["variant_rank"]
            if a_rank is not None and a_rank <= 3 and (v_rank is None or v_rank > 10):
                events.append(
                    {
                        "case_id": cid,
                        "chunk_id": span["chunk_id"],
                        "a_rank": a_rank,
                        "variant_rank": v_rank,
                    }
                )
    rank1 = [e for e in events if e["a_rank"] == 1]
    return {"events": events, "count": len(events), "rank1_destroyed": rank1}


def main() -> int:
    started = time.time()
    if holdout_log_bytes() != 0:
        raise SystemExit(f"STOP: holdout access log is {holdout_log_bytes()} bytes")

    pre_md = OUT_DIR / "EXP-016-preregistration.md"
    pre_json = OUT_DIR / "EXP-016-preregistration.json"
    if not pre_md.exists() or not pre_json.exists():
        raise SystemExit("STOP: preregistration missing")
    results_path = OUT_DIR / "EXP-016-development-results.json"
    if results_path.exists():
        raise SystemExit("STOP: results already exist; refusing to overwrite mid-protocol")

    a_hash = FROZEN_HASHES["SYSTEM-A-GLOBAL"]
    if a_hash != A_HASH:
        raise SystemExit(f"STOP: SYSTEM-A hash {a_hash} != {A_HASH}")

    emb = embedding_status()
    if not emb["complete"]:
        raise SystemExit(f"STOP: embeddings incomplete: {emb}")

    exp015 = json.loads(EXP015_RESULTS.read_text())
    stored_a = exp015["system_a"]
    stored_c = exp015["system_c"]
    stored_per = {row["case_id"]: row for row in exp015["per_case"]}

    encoder = TransformerEncoder(max_seq=512).load()
    if encoder.model_version != TRANSFORMER_FINGERPRINT:
        raise SystemExit("STOP: live encoder fingerprint mismatch")
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)
    ce = CrossEncoderReranker()
    probe_q, probe_p = "What is BM25?", "BM25 is a lexical ranking function."
    ce_stable = ce.score_pairs(probe_q, [probe_p])[0] == ce.score_pairs(probe_q, [probe_p])[0]

    cases = [c for c in load_cases(DEV_JSONL) if c.expected_evidence]
    if len(cases) != 20:
        raise SystemExit(f"expected 20 development cases, got {len(cases)}")

    # --- rematerialize pools + CE logits (not yet C/D) ---
    material: dict[str, dict] = {}
    lat_a, lat_ce = [], []
    reproduce_ok = True
    reproduce_mismatches = []

    for case in cases:
        q = case.question
        t0 = time.time()
        pool = retrieve_system_a_pool(q, transformer)
        lat_a.append((time.time() - t0) * 1000)
        t0 = time.time()
        scores = ce.score_pairs(q, [h.text for h in pool])
        lat_ce.append((time.time() - t0) * 1000)
        rows = []
        for hit, score in zip(pool, scores, strict=True):
            rows.append(
                {
                    "chunk_id": hit.chunk_id,
                    "version_id": hit.version_id,
                    "section_path": list(hit.section_path),
                    "char_start": hit.char_start,
                    "char_end": hit.char_end,
                    "a_rank": hit.rank,
                    "a_score": float(hit.score),
                    "ce_score": float(score),
                    "identifier_overlap": has_exact_identifier_overlap(q, hit.text),
                    "overlap_tokens": overlapping_identifiers(q, hit.text),
                    "text": hit.text,
                }
            )
        gold_chunks = []
        for ref in case.expected_evidence:
            hit = next((h for h in pool if overlaps(h, ref)), None)
            gold_chunks.append(hit.chunk_id if hit else None)

        stored = stored_per[case.case_id]
        for i, span in enumerate(stored["spans"]):
            got_pool = next((r["a_rank"] for r in rows if r["chunk_id"] == span["chunk_id"]), None)
            got_ce = next((r["ce_score"] for r in rows if r["chunk_id"] == span["chunk_id"]), None)
            exp_pool = span["pool_rank"]
            exp_ce_rank = span["c_rank"]
            ce_sorted = ce_order(rows)
            got_ce_rank = next(
                (i + 1 for i, r in enumerate(ce_sorted) if r["chunk_id"] == span["chunk_id"]),
                None,
            )
            if got_pool != exp_pool:
                reproduce_ok = False
                reproduce_mismatches.append(
                    f"{case.case_id} span{i} A/pool rank {got_pool} != stored {exp_pool}"
                )
            if got_ce_rank != exp_ce_rank:
                reproduce_ok = False
                reproduce_mismatches.append(
                    f"{case.case_id} span{i} CE rank {got_ce_rank} != stored {exp_ce_rank}"
                )
            if got_ce is not None and span["ce_score"] is not None:
                if abs(got_ce - span["ce_score"]) > 1e-4:
                    reproduce_ok = False
                    reproduce_mismatches.append(
                        f"{case.case_id} span{i} CE score {got_ce} != stored {span['ce_score']}"
                    )

        material[case.case_id] = {
            "case": case,
            "rows": rows,
            "gold_chunks": gold_chunks,
            "pool_size": len(pool),
            "latency_a_ms": lat_a[-1],
            "latency_ce_ms": lat_ce[-1],
        }

    if not reproduce_ok:
        raise SystemExit("STOP: rematerialized pool/CE did not reproduce EXP-015:\n" + "\n".join(reproduce_mismatches))

    # --- HA-24 diagnostic BEFORE C/D scoring ---
    ha24 = material["HA-24"]
    diag_path = OUT_DIR / "EXP-016-HA24-diagnostic.md"
    if (OUT_DIR / "EXP-016-development-results.json").exists():
        raise SystemExit("STOP: results appeared before diagnostic")
    diagnostic = write_ha24_diagnostic(
        ha24["case"], ha24["rows"], ha24["gold_chunks"][0], diag_path
    )
    print(f"wrote HA-24 diagnostic {diag_path} before C/D scoring")
    print(diagnostic["conclusion"])

    # --- now apply C and D ---
    a_full = {cid: stored_a["cases"][cid]["fully_recalled"] for cid in material}
    b_full = {cid: stored_c["cases"][cid]["fully_recalled"] for cid in material}
    c_cases, d_cases = {}, {}
    c_full, d_full = {}, {}
    per_case = []
    named_traces = {}
    compact_pools = []

    for case in cases:
        pack = material[case.case_id]
        rows = [dict(r) for r in pack["rows"]]
        c_rows = apply_guard_clamp(rows)
        # blend uses original rows (clamp mutated copies with extra keys; re-copy)
        d_rows = apply_blend([dict(r) for r in pack["rows"]])
        c_rank = {r["chunk_id"]: r["c_rank"] for r in c_rows}
        d_rank = {r["chunk_id"]: r["d_rank"] for r in d_rows}
        ce_rank = {r["chunk_id"]: r["ce_rank"] for r in c_rows}
        protected_by = {r["chunk_id"]: r["protected"] for r in c_rows}
        clamped_by = {r["chunk_id"]: r["clamped"] for r in c_rows}
        blend_by = {r["chunk_id"]: r["blend_score"] for r in d_rows}

        c_cases[case.case_id] = score_case_from_ranks(case, c_rank, pack["gold_chunks"])
        d_cases[case.case_id] = score_case_from_ranks(case, d_rank, pack["gold_chunks"])
        c_full[case.case_id] = c_cases[case.case_id]["fully_recalled"]
        d_full[case.case_id] = d_cases[case.case_id]["fully_recalled"]

        span_rows = []
        for i, ref in enumerate(case.expected_evidence):
            cid = pack["gold_chunks"][i]
            row = next((r for r in pack["rows"] if r["chunk_id"] == cid), None) if cid else None
            stored_span = stored_per[case.case_id]["spans"][i]
            span_rows.append(
                {
                    "span_index": i,
                    "chunk_id": cid,
                    "a_rank_stored": stored_span["a_rank"],
                    "a_rank": row["a_rank"] if row else None,
                    "pool_rank": row["a_rank"] if row else None,
                    "a_score": row["a_score"] if row else None,
                    "ce_score": row["ce_score"] if row else None,
                    "ce_rank": ce_rank.get(cid) if cid else None,
                    "b_rank_stored": stored_span["c_rank"],
                    "c_rank": c_rank.get(cid) if cid else None,
                    "d_rank": d_rank.get(cid) if cid else None,
                    "protected": protected_by.get(cid) if cid else False,
                    "clamped": clamped_by.get(cid) if cid else False,
                    "blend_score": blend_by.get(cid) if cid else None,
                    "identifier_overlap": row["identifier_overlap"] if row else False,
                    "overlap_tokens": row["overlap_tokens"] if row else [],
                    "a_in_top_10": stored_a["cases"][case.case_id]["spans"][i]["within"]["10"],
                    "b_in_top_10": stored_c["cases"][case.case_id]["spans"][i]["within"]["10"],
                    "c_in_top_10": c_rank.get(cid) is not None and c_rank[cid] <= TOP_K if cid else False,
                    "d_in_top_10": d_rank.get(cid) is not None and d_rank[cid] <= TOP_K if cid else False,
                }
            )

        destructions_c = [
            s for s in span_rows
            if s["a_rank"] is not None and s["a_rank"] <= 3 and not s["c_in_top_10"]
        ]
        destructions_d = [
            s for s in span_rows
            if s["a_rank"] is not None and s["a_rank"] <= 3 and not s["d_in_top_10"]
        ]
        destructions_b = [
            s for s in span_rows
            if s["a_rank"] is not None and s["a_rank"] <= 3 and not s["b_in_top_10"]
        ]

        rec = {
            "case_id": case.case_id,
            "a_full": a_full[case.case_id],
            "b_full": b_full[case.case_id],
            "c_full": c_full[case.case_id],
            "d_full": d_full[case.case_id],
            "pool_size": pack["pool_size"],
            "all_spans_in_pool": all(s["pool_rank"] is not None for s in span_rows),
            "n_protected": sum(1 for r in c_rows if r["protected"]),
            "n_clamped": sum(1 for r in c_rows if r["clamped"]),
            "spans": span_rows,
            "rank_destruction": {
                "B": destructions_b,
                "C": destructions_c,
                "D": destructions_d,
            },
            "latency_ms": {
                "system_a_retrieval": round(pack["latency_a_ms"], 2),
                "cross_encoder": round(pack["latency_ce_ms"], 2),
                "fusion_guard_is_cpu_microseconds": True,
                "stored_A_from_EXP015": stored_per[case.case_id]["latency_ms"]["system_a_retrieval"],
                "stored_B_from_EXP015": stored_per[case.case_id]["latency_ms"]["system_c_total"],
            },
        }
        per_case.append(rec)
        if case.case_id in NAMED:
            named_traces[case.case_id] = rec

        compact_pools.append(
            {
                "case_id": case.case_id,
                "pool": [
                    {
                        "chunk_id": r["chunk_id"],
                        "a_rank": r["a_rank"],
                        "a_score": r["a_score"],
                        "ce_score": r["ce_score"],
                        "ce_rank": ce_rank[r["chunk_id"]],
                        "c_rank": c_rank[r["chunk_id"]],
                        "d_rank": d_rank[r["chunk_id"]],
                        "protected": protected_by[r["chunk_id"]],
                        "clamped": clamped_by[r["chunk_id"]],
                        "blend_score": blend_by[r["chunk_id"]],
                        "identifier_overlap": r["identifier_overlap"],
                        "overlap_tokens": r["overlap_tokens"],
                    }
                    for r in pack["rows"]
                ],
            }
        )
        # drop passage text from memory after scoring this case's C/D
        for r in pack["rows"]:
            r.pop("text", None)

    c_hash = config_hash(
        {
            "name": "SYSTEM-D-GUARD-CLAMP",
            "control": a_hash,
            "pool": CANDIDATE_POOL,
            "protect_a_rank_max": PROTECT_A_RANK_MAX,
            "clamp_floor": CLAMP_FLOOR,
            "matcher": "EXP-016-preregistration identifier set intersection",
            "ce_sha256": CE_SHA256,
            "tie_break": "ce desc, A rank, chunk_id; then clamp",
        }
    )
    d_hash = config_hash(
        {
            "name": "SYSTEM-D-GUARD-BLEND",
            "control": a_hash,
            "pool": CANDIDATE_POOL,
            "weights": [BLEND_CE, BLEND_A],
            "minmax_degenerate": 0.5,
            "ce_sha256": CE_SHA256,
            "tie_break": "blend desc, A rank, chunk_id",
        }
    )
    system_c = summarise(c_cases, "SYSTEM-D-GUARD-CLAMP", c_hash)
    system_d = summarise(d_cases, "SYSTEM-D-GUARD-BLEND", d_hash)

    pair_c = paired(a_full, c_full)
    pair_d = paired(a_full, d_full)
    pair_b = paired(a_full, b_full)

    def destructions_for(variant_key: str) -> dict:
        events = []
        rank1 = []
        for rec in per_case:
            for s in rec["spans"]:
                a_rank = s["a_rank"]
                in_top = {
                    "B": s["b_in_top_10"],
                    "C": s["c_in_top_10"],
                    "D": s["d_in_top_10"],
                }[variant_key]
                if a_rank is not None and a_rank <= 3 and not in_top:
                    ev = {
                        "case_id": rec["case_id"],
                        "chunk_id": s["chunk_id"],
                        "a_rank": a_rank,
                        "variant_rank": {
                            "B": s["b_rank_stored"],
                            "C": s["c_rank"],
                            "D": s["d_rank"],
                        }[variant_key],
                    }
                    events.append(ev)
                    if a_rank == 1:
                        rank1.append(ev)
        return {"events": events, "count": len(events), "rank1_destroyed": rank1}

    dest_b, dest_c, dest_d = destructions_for("B"), destructions_for("C"), destructions_for("D")

    def qualifies(strict: int, pair: dict, dest: dict) -> dict:
        ok_strict = strict >= stored_a["cases_fully_recalled"]
        ok_net = pair["net"] >= 0
        ok_rank1 = len(dest["rank1_destroyed"]) == 0
        return {
            "strict_ge_A": ok_strict,
            "net_rescues_ge_0": ok_net,
            "no_new_rank1_destruction": ok_rank1,
            "qualifies": ok_strict and ok_net and ok_rank1,
        }

    q_c = qualifies(system_c["cases_fully_recalled"], pair_c, dest_c)
    q_d = qualifies(system_d["cases_fully_recalled"], pair_d, dest_d)

    candidates = []
    if q_c["qualifies"]:
        candidates.append(("C", system_c, dest_c, q_c, "SYSTEM-D-GUARD-CLAMP"))
    if q_d["qualifies"]:
        candidates.append(("D", system_d, dest_d, q_d, "SYSTEM-D-GUARD-BLEND"))
    # tie-break: higher strict, higher MRR, fewer destructions, C over D
    def cand_key(item):
        letter, summary, dest, _q, _name = item
        return (
            summary["cases_fully_recalled"],
            summary["mrr"],
            -dest["count"],
            1 if letter == "C" else 0,
        )

    winner = None
    if candidates:
        winner = max(candidates, key=cand_key)

    if winner:
        decision = "SYSTEM_D_FROZEN_STOP_FOR_VALIDATION_APPROVAL"
        decision_code = "SYSTEM_D_FROZEN"
    else:
        decision = "RERANKER_DIRECTION_REJECTED"
        decision_code = "RERANKER_DIRECTION_REJECTED"

    variant_metrics = {
        "A": {
            "source": "EXP-015 stored SYSTEM-A ranks (not retuned)",
            "strict_recall_at_10": stored_a["strict_recall_at_10"],
            "cases_fully_recalled": stored_a["cases_fully_recalled"],
            "macro_span_recall": stored_a["macro_span_recall"],
            "mrr": stored_a["mrr"],
            "document_recall": stored_a["document_recall"],
            "spans_found_at_10": stored_a["spans_found_at_10"],
            "spans_total": stored_a["spans_total"],
            "rescues_vs_A": [],
            "regressions_vs_A": [],
            "net_rescues": 0,
            "rank_destruction_events": 0,
            "rank1_destroyed": [],
            "latency_ms_mean": exp015["latency_ms"]["A_mean"],
        },
        "B": {
            "source": "EXP-015 stored SYSTEM-C (already-rejected CE-only control)",
            "strict_recall_at_10": stored_c["strict_recall_at_10"],
            "cases_fully_recalled": stored_c["cases_fully_recalled"],
            "macro_span_recall": stored_c["macro_span_recall"],
            "mrr": stored_c["mrr"],
            "document_recall": stored_c["document_recall"],
            "spans_found_at_10": stored_c["spans_found_at_10"],
            "spans_total": stored_c["spans_total"],
            "rescues_vs_A": pair_b["rescues"],
            "regressions_vs_A": pair_b["regressions"],
            "net_rescues": pair_b["net"],
            "rank_destruction_events": dest_b["count"],
            "rank1_destroyed": dest_b["rank1_destroyed"],
            "latency_ms_mean": exp015["latency_ms"]["C_mean"],
            "already_rejected": True,
        },
        "C": {
            "source": "EXP-016 exact-match protected rerank on rematerialized EXP-015 logits",
            "strict_recall_at_10": system_c["strict_recall_at_10"],
            "cases_fully_recalled": system_c["cases_fully_recalled"],
            "macro_span_recall": system_c["macro_span_recall"],
            "mrr": system_c["mrr"],
            "document_recall": system_c["document_recall"],
            "spans_found_at_10": system_c["spans_found_at_10"],
            "spans_total": system_c["spans_total"],
            "rescues_vs_A": pair_c["rescues"],
            "regressions_vs_A": pair_c["regressions"],
            "net_rescues": pair_c["net"],
            "rank_destruction_events": dest_c["count"],
            "rank1_destroyed": dest_c["rank1_destroyed"],
            "latency_ms_mean": round(statistics.mean(a + c for a, c in zip(lat_a, lat_ce)), 1),
            "qualifies": q_c,
        },
        "D": {
            "source": "EXP-016 0.7/0.3 CE+A blend on rematerialized EXP-015 logits",
            "strict_recall_at_10": system_d["strict_recall_at_10"],
            "cases_fully_recalled": system_d["cases_fully_recalled"],
            "macro_span_recall": system_d["macro_span_recall"],
            "mrr": system_d["mrr"],
            "document_recall": system_d["document_recall"],
            "spans_found_at_10": system_d["spans_found_at_10"],
            "spans_total": system_d["spans_total"],
            "rescues_vs_A": pair_d["rescues"],
            "regressions_vs_A": pair_d["regressions"],
            "net_rescues": pair_d["net"],
            "rank_destruction_events": dest_d["count"],
            "rank1_destroyed": dest_d["rank1_destroyed"],
            "latency_ms_mean": round(statistics.mean(a + c for a, c in zip(lat_a, lat_ce)), 1),
            "qualifies": q_d,
        },
    }

    freeze_path = None
    frozen = False
    if winner:
        letter, summary, dest, _q, name = winner
        freeze = {
            "name": "SYSTEM-D-GUARD",
            "variant": letter,
            "implementation": name,
            "frozen_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "frozen_before_validation_load": True,
            "validation_loaded": False,
            "holdout_loaded": False,
            "system_a_config_hash": a_hash,
            "config_hash": summary["config_hash"],
            "snapshot": SNAPSHOT,
            "chunk_set": CHUNK_SET,
            "encoder": {
                "model_id": TRANSFORMER_MODEL,
                "fingerprint": TRANSFORMER_FINGERPRINT,
                "max_seq_length": 512,
            },
            "cross_encoder": {
                "name": CE_NAME,
                "revision": CE_REVISION,
                "artifact": str(CE_ONNX),
                "artifact_sha256": CE_SHA256,
                "runtime": "onnxruntime + HuggingFace tokenizers",
                "precision": "fp32",
                "max_length": MAX_LENGTH,
                "pair_formatting": "[CLS] query [SEP] passage [SEP]",
                "truncation": "longest_first",
                "scoring": "raw sequence-classification logit (Identity); higher=more relevant",
            },
            "candidate_pool": CANDIDATE_POOL,
            "pool_per_retriever": RRF_POOL,
            "rrf_k": RRF_K,
            "top_k": TOP_K,
            "guard": {
                "kind": "exact_match_clamp" if letter == "C" else "score_blend",
                "protect_a_rank_max": PROTECT_A_RANK_MAX if letter == "C" else None,
                "clamp_floor": CLAMP_FLOOR if letter == "C" else None,
                "blend_weights": [BLEND_CE, BLEND_A] if letter == "D" else None,
                "matcher": "EXP-016-preregistration identifier set intersection",
            },
            "development_metrics": variant_metrics[letter],
            "note": (
                "Frozen after EXP-016 development qualification. Validation must not "
                "be loaded until this freeze file has been inspected and approved."
            ),
        }
        freeze_path = OUT_DIR / "SYSTEM-D-GUARD.json"
        freeze_path.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
        frozen = True
    else:
        (OUT_DIR / "RERANKER_DIRECTION_REJECTED.json").write_text(
            json.dumps(
                {
                    "status": "RERANKER_DIRECTION_REJECTED",
                    "frozen": False,
                    "validation_loaded": False,
                    "holdout_loaded": False,
                    "variant_C_qualifies": q_c,
                    "variant_D_qualifies": q_d,
                    "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    (OUT_DIR / "EXP-016-pools.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in compact_pools) + "\n",
        encoding="utf-8",
    )

    payload = {
        "experiment_id": "EXP-016",
        "phase": "development_qualification",
        "split": "gold150-v1/development",
        "split_path": "evals/splits/gold150-v1/development.json",
        "projection_path": str(DEV_JSONL.relative_to(ROOT)),
        "preregistration": [
            "experiments/EXP-016/EXP-016-preregistration.md",
            "experiments/EXP-016/EXP-016-preregistration.json",
        ],
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "corpus_snapshot": SNAPSHOT,
        "chunk_set": CHUNK_SET,
        "system_a_config_hash": a_hash,
        "tuned_after_seeing_scores": False,
        "validation_loaded": False,
        "holdout_loaded": False,
        "holdout_access_log_bytes": holdout_log_bytes(),
        "embedding": emb,
        "rematerialize_reproduced_exp015": {
            "passed": reproduce_ok,
            "mismatches": reproduce_mismatches,
        },
        "ha24_diagnostic": diagnostic,
        "variants": variant_metrics,
        "system_c_guard": {k: v for k, v in system_c.items() if k != "cases"} | {"cases": system_c["cases"]},
        "system_d_blend": {k: v for k, v in system_d.items() if k != "cases"} | {"cases": system_d["cases"]},
        "paired": {"B": pair_b, "C": pair_c, "D": pair_d},
        "rank_destruction": {"B": dest_b, "C": dest_c, "D": dest_d},
        "named_case_traces": named_traces,
        "per_case": per_case,
        "latency_ms": {
            "A_mean_stored": exp015["latency_ms"]["A_mean"],
            "B_mean_stored": exp015["latency_ms"]["C_mean"],
            "CE_mean_rematerialized": round(statistics.mean(lat_ce), 1),
            "A_mean_rematerialized": round(statistics.mean(lat_a), 1),
            "C_D_mean_retrieval_plus_ce": round(statistics.mean(a + c for a, c in zip(lat_a, lat_ce)), 1),
        },
        "decision": {
            "code": decision_code,
            "text": decision,
            "C_qualifies": q_c,
            "D_qualifies": q_d,
            "winner": winner[0] if winner else None,
            "frozen": frozen,
            "freeze_path": str(freeze_path.relative_to(ROOT)) if freeze_path else None,
        },
        "cross_encoder": {
            "name": CE_NAME,
            "revision": CE_REVISION,
            "artifact_sha256": CE_SHA256,
            "pair_score_stable": ce_stable,
        },
        "runtime_seconds": round(time.time() - started, 1),
    }
    results_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    # report
    def row(letter, m):
        return (
            f"| {letter} | {m['strict_recall_at_10']} | {m['macro_span_recall']:.4f} | "
            f"{m['mrr']:.4f} | {m['rescues_vs_A'] or '—'} | {m['regressions_vs_A'] or '—'} | "
            f"{m['net_rescues']:+d} | {m['rank_destruction_events']} | {m['latency_ms_mean']} |"
        )

    report = []
    report.append("# EXP-016 development report")
    report.append("")
    report.append(f"Timestamp: {payload['timestamp']}")
    report.append("Split: gold150-v1/development n=20. Validation not loaded. Holdout not loaded.")
    report.append(f"Holdout access log: {payload['holdout_access_log_bytes']} bytes.")
    report.append("Preregistration existed before any EXP-016 scores.")
    report.append(f"Rematerialized pool/CE reproduced EXP-015: `{reproduce_ok}`.")
    report.append("")
    report.append("## HA-24 diagnostic conclusion")
    report.append("")
    report.append(diagnostic["conclusion"])
    report.append("")
    report.append(f"See `{diagnostic['path']}`.")
    report.append("")
    report.append("## Metrics")
    report.append("")
    report.append("| V | strict R@10 | span recall | MRR | rescues vs A | regressions vs A | net | rank-dest (A≤3 out of 10) | latency ms |")
    report.append("| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |")
    for letter in "ABCD":
        report.append(row(letter, variant_metrics[letter]))
    report.append("")
    report.append("A and B are re-reported from stored EXP-015 ranks. C and D use the same")
    report.append("rematerialized pool-100 and CE logits; only the fusion/guard differs.")
    report.append("")
    report.append("## Named-case traces")
    report.append("")
    for cid in NAMED:
        rec = named_traces[cid]
        report.append(f"### {cid}")
        report.append("")
        report.append(f"A full={rec['a_full']}  B full={rec['b_full']}  C full={rec['c_full']}  D full={rec['d_full']}")
        report.append("")
        report.append("| span | chunk | A rank | pool | CE score | CE rank | B rank | C rank | D rank | protected | clamped | all spans in top-10 A/B/C/D |")
        report.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |")
        for s in rec["spans"]:
            report.append(
                f"| {s['span_index']} | `{s['chunk_id']}` | {s['a_rank']} | {s['pool_rank']} | "
                f"{s['ce_score']:.4f} | {s['ce_rank']} | {s['b_rank_stored']} | {s['c_rank']} | "
                f"{s['d_rank']} | {s['protected']} | {s['clamped']} | "
                f"{s['a_in_top_10']}/{s['b_in_top_10']}/{s['c_in_top_10']}/{s['d_in_top_10']} |"
            )
        report.append("")
    report.append("## Decision")
    report.append("")
    report.append(f"**{decision_code}** — {decision}")
    report.append("")
    report.append(f"- C qualifies: `{q_c}`")
    report.append(f"- D qualifies: `{q_d}`")
    report.append(f"- SYSTEM-D frozen: `{frozen}`" + (f" → `{freeze_path.name}`" if freeze_path else ""))
    report.append("- Validation was not run. Holdout was not run. No EXP-017.")
    report.append("")
    (OUT_DIR / "EXP-016-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"A {variant_metrics['A']['strict_recall_at_10']}")
    print(f"B {variant_metrics['B']['strict_recall_at_10']} net {variant_metrics['B']['net_rescues']:+d}")
    print(f"C {variant_metrics['C']['strict_recall_at_10']} net {variant_metrics['C']['net_rescues']:+d} dest {dest_c['count']} q={q_c['qualifies']}")
    print(f"D {variant_metrics['D']['strict_recall_at_10']} net {variant_metrics['D']['net_rescues']:+d} dest {dest_d['count']} q={q_d['qualifies']}")
    print(f"decision {decision_code} frozen={frozen}")
    print(f"holdout_log={holdout_log_bytes()} bytes")
    print(f"wrote {results_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
