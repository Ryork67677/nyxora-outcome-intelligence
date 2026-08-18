#!/usr/bin/env python3
"""Does query normalization make the two retrievers agree with each other more?

EXP-011 found the individual retrievers improving under normalization while the
fusion of them got worse. If normalization pushes BM25 and the transformer toward
the same candidates, RRF has less disagreement left to exploit — this measures
that agreement directly.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from rag_v1.embedders_transformer import TransformerEncoder
from rag_v1.evals.io import load_cases
from rag_v1.query_cache import CachedQueryEmbedder
from rag_v1.query_views import build_views
from rag_v1.retrieval import dense_search, lexical_search

SNAP = "snap_689e336380a054d8039dc35b2c09cd0a"
MODEL = "emb_e7d4183fd6eb878ae2fdf080efb6861e"
POOL = 50

cases = [c for c in load_cases(Path("evals/golden/v1.jsonl")) if c.expected_evidence]
enc = TransformerEncoder(max_seq=512).load()
tx = CachedQueryEmbedder(enc, fingerprint=enc.model_version)

out = {}
for view in ("raw", "normalized", "structured"):
    jaccards, overlaps10 = [], []
    for case in cases:
        text = build_views(case.question, (view,))[0].text
        lex = {h.chunk_id for h in lexical_search(text, SNAP, POOL)}
        den = {h.chunk_id for h in dense_search(text, SNAP, MODEL, POOL, embedder=tx)}
        union = lex | den
        jaccards.append(len(lex & den) / len(union) if union else 0.0)
        lex10 = {h.chunk_id for h in lexical_search(text, SNAP, 10)}
        den10 = {h.chunk_id for h in dense_search(text, SNAP, MODEL, 10, embedder=tx)}
        overlaps10.append(len(lex10 & den10))
    out[view] = {
        "mean_jaccard_top50": round(statistics.mean(jaccards), 4),
        "mean_shared_chunks_top10": round(statistics.mean(overlaps10), 2),
    }
print(json.dumps(out, indent=2))
Path("experiments/EXP-011/complementarity.json").write_text(
    json.dumps({"note": "Agreement between BM25 and the transformer on the same query view. "
                        "Higher agreement means less for RRF to exploit.",
                "by_view": out}, indent=2) + "\n")
