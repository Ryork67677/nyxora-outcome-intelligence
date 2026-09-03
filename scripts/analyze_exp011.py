#!/usr/bin/env python3
"""EXP-011 attribution: which retriever does query rewriting actually damage?

The A-E cells fuse BM25 and the transformer, so they cannot say *which* retriever
the transformation hurt. This runs every (query view x retriever) alone.

The prediction worth testing is mechanistic: BM25 already discounts conversational
words through inverse document frequency, so removing them should change little
and can only lose the occasional useful term. The transformer, by contrast, is a
*sentence* encoder trained on natural sentence pairs — a bag of keywords is out of
distribution for it, so it should degrade much more.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from rag_v1.embedders_transformer import TransformerEncoder
from rag_v1.evals.io import load_cases
from rag_v1.query_cache import CachedQueryEmbedder
from rag_v1.query_views import build_views
from rag_v1.retrieval import dense_search, lexical_search
from rag_v1.types import EvidenceRef, SearchHit

CONTROL_SNAP = "snap_689e336380a054d8039dc35b2c09cd0a"
TRANSFORMER_MODEL = "emb_e7d4183fd6eb878ae2fdf080efb6861e"
MAX_SEQ = 512
PROBE_DEPTHS = (10, 20, 30, 50, 100, 300)
VIEWS = ("raw", "normalized", "structured")


def overlaps(hit: SearchHit, ref: EvidenceRef) -> bool:
    return (hit.version_id == ref.version_id and hit.section_path == ref.section_path
            and hit.char_start < ref.char_end and hit.char_end > ref.char_start)


def measure(cases, view_name: str, retriever: str, transformer, deep: int) -> dict:
    per_case, ranks = {}, []
    latency = []
    for case in cases:
        view = next(v for v in build_views(case.question, (view_name,)))
        t0 = time.time()
        hits = (lexical_search(view.text, CONTROL_SNAP, deep) if retriever == "bm25"
                else dense_search(view.text, CONTROL_SNAP, TRANSFORMER_MODEL, deep,
                                  embedder=transformer))
        latency.append((time.time() - t0) * 1000)
        spans = []
        for ref in case.expected_evidence:
            hit = next((h for h in hits if overlaps(h, ref)), None)
            spans.append({"rank": hit.rank if hit else None,
                          "within": {str(d): (hit is not None and hit.rank <= d)
                                     for d in PROBE_DEPTHS}})
            ranks.append(hit.rank if hit else None)
        found = sum(1 for s in spans if s["within"]["10"])
        per_case[case.case_id] = {
            "spans": spans,
            "recall": found / len(spans) if spans else 1.0,
            "fully_recalled": bool(spans) and found == len(spans),
        }
    all_spans = [s for c in per_case.values() for s in c["spans"]]
    got = [r for r in ranks if r is not None]
    return {
        "view": view_name, "retriever": retriever,
        "macro_span_recall": round(sum(c["recall"] for c in per_case.values()) / len(per_case), 4),
        "cases_fully_recalled": sum(1 for c in per_case.values() if c["fully_recalled"]),
        "spans_found_at_10": sum(1 for s in all_spans if s["within"]["10"]),
        "spans_total": len(all_spans),
        "mrr": round(sum(1 / s["rank"] for s in all_spans if s["rank"]) / len(all_spans), 4),
        "median_rank_when_found": statistics.median(got) if got else None,
        "spans_absent_from_top": {str(d): sum(1 for s in all_spans if not s["within"][str(d)])
                                  for d in PROBE_DEPTHS},
        "mean_query_ms": round(statistics.mean(latency), 1),
        "cases": per_case,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", default="evals/golden/v1.jsonl")
    parser.add_argument("--deep", type=int, default=300)
    parser.add_argument("--out", default="experiments/EXP-011/retriever-attribution.json")
    args = parser.parse_args()

    cases = [c for c in load_cases(Path(args.golden)) if c.expected_evidence]
    encoder = TransformerEncoder(max_seq=MAX_SEQ).load()
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)

    grid = {}
    for view in VIEWS:
        for retriever in ("bm25", "transformer"):
            grid[f"{retriever}({view})"] = measure(cases, view, retriever, transformer, args.deep)

    def delta(retriever: str, view: str) -> float:
        return round(grid[f"{retriever}({view})"]["macro_span_recall"]
                     - grid[f"{retriever}(raw)"]["macro_span_recall"], 4)

    attribution = {
        "note": "Change in macro span recall relative to the same retriever on the raw query.",
        "bm25": {v: delta("bm25", v) for v in VIEWS},
        "transformer": {v: delta("transformer", v) for v in VIEWS},
    }
    attribution["transformer_damage_vs_bm25"] = {
        v: round(attribution["transformer"][v] - attribution["bm25"][v], 4) for v in VIEWS
    }

    payload = {"experiment_id": "EXP-011", "grid": grid, "attribution": attribution,
               "query_embedding_cache": transformer.stats()}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"{'cell':26s} {'macroR':>7s} {'full':>6s} {'spans':>8s} {'MRR':>6s} {'a@300':>6s}")
    for key, r in grid.items():
        print(f"{key:26s} {r['macro_span_recall']:7.3f} {r['cases_fully_recalled']:3d}/20 "
              f"{r['spans_found_at_10']:3d}/{r['spans_total']:<4d} {r['mrr']:6.3f} "
              f"{r['spans_absent_from_top']['300']:6d}")
    print("\ndelta vs the same retriever on the raw query:")
    for retriever in ("bm25", "transformer"):
        print(f"  {retriever:12s} " + "  ".join(
            f"{v}={attribution[retriever][v]:+.3f}" for v in VIEWS))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
