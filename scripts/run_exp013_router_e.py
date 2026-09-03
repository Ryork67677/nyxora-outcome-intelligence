#!/usr/bin/env python3
"""EXP-013 Router E — EXPLORATORY document-level transformer representation.

Routers A-D all derive document rankings from a *chunk* ranking. They reached the
same routing recall@5 (0.875, 17/20), which is preregistered Outcome D: rank
aggregation over chunk lists is itself inadequate, and the next thing worth testing
is a genuinely document-level representation.

This is that test, and nothing more. It is **EXPLORATORY** — run only after A-D were
frozen, and it does not replace the preregistered result.

Method, fixed in advance: mean of the already-stored normalised chunk embeddings per
document, renormalised, ranked against the query by cosine. No re-chunking, no
training, no tuning. If it needed tuning to work it would be a research project, not
a measurement.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import numpy as np

from rag_v1.db import connect
from rag_v1.embedders_transformer import TransformerEncoder
from rag_v1.evals.io import load_cases
from rag_v1.query_cache import CachedQueryEmbedder
from rag_v1.retrieval import dense_search, lexical_search
from rag_v1.routers import DOCUMENT_RRF_K, route, rrf_document_lists

SNAP = "snap_689e336380a054d8039dc35b2c09cd0a"
CHUNK_SET = "cs_v1_control"
MODEL = "emb_e7d4183fd6eb878ae2fdf080efb6861e"
DOC_RANKING_DEPTH = 300
TOP_DOCUMENTS = 5


def document_vectors() -> tuple[list[str], np.ndarray]:
    """Mean of each document's stored chunk vectors, renormalised."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.version_id, avg(ce.embedding)::text
            FROM chunk_embedding ce
            JOIN chunk c ON c.chunk_id = ce.chunk_id
            JOIN corpus_snapshot_version sv ON sv.version_id = c.version_id
            WHERE ce.model_id=%s AND c.chunk_set_id=%s AND sv.snapshot_id=%s
            GROUP BY c.version_id ORDER BY c.version_id
            """,
            (MODEL, CHUNK_SET, SNAP),
        )
        rows = cur.fetchall()
    ids = [r[0] for r in rows]
    matrix = np.array([json.loads(r[1]) for r in rows], dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return ids, matrix / np.clip(norms, 1e-12, None)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", default="evals/golden/v1.jsonl")
    parser.add_argument("--top-documents", type=int, default=TOP_DOCUMENTS)
    parser.add_argument("--out", default="experiments/EXP-013/router-e-exploratory.json")
    args = parser.parse_args()

    cases = [c for c in load_cases(Path(args.golden)) if c.expected_evidence]
    encoder = TransformerEncoder(max_seq=512).load()
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)

    started = time.time()
    ids, doc_matrix = document_vectors()
    build_seconds = time.time() - started

    n = args.top_documents
    rows = []
    for case in cases:
        expected = {ref.version_id for ref in case.expected_evidence}
        qvec = np.asarray(transformer.embed([case.question])[0], dtype=np.float32)
        qvec = qvec / max(float(np.linalg.norm(qvec)), 1e-12)
        sims = doc_matrix @ qvec
        # Deterministic total order: similarity desc, then document id.
        order = [ids[i] for i in sorted(range(len(ids)), key=lambda i: (-float(sims[i]), ids[i]))]

        # Fused with the existing chunk-derived routing, in the rank domain.
        g_lex = lexical_search(case.question, SNAP, DOC_RANKING_DEPTH)
        g_den = dense_search(case.question, SNAP, MODEL, DOC_RANKING_DEPTH, embedder=transformer)
        _fused_d, per_retriever = route("D_MAX_SUPPORT", g_lex, g_den)
        doc_embed_ranking = [(v, 1) for v in order]
        hybrid = rrf_document_lists(
            [("doc_embedding", doc_embed_ranking),
             ("bm25_max", per_retriever["bm25"]),
             ("transformer_max", per_retriever["transformer"])],
            k=DOCUMENT_RRF_K)
        hybrid_order = [e["version_id"] for e in hybrid]

        rows.append({
            "case_id": case.case_id,
            "expected_documents": sorted(expected),
            "doc_embedding_rank": {d: (order.index(d) + 1 if d in order else None)
                                   for d in sorted(expected)},
            "doc_embedding_all_routed": expected <= set(order[:n]),
            "hybrid_rank": {d: (hybrid_order.index(d) + 1 if d in hybrid_order else None)
                            for d in sorted(expected)},
            "hybrid_all_routed": expected <= set(hybrid_order[:n]),
            "recall_doc_embedding": {str(d): round(len(expected & set(order[:d])) / len(expected), 4)
                                     for d in (1, 3, 5, 10)},
            "recall_hybrid": {str(d): round(len(expected & set(hybrid_order[:d])) / len(expected), 4)
                              for d in (1, 3, 5, 10)},
        })

    summary = {
        "status": "EXPLORATORY — run after routers A-D were frozen; does not replace them",
        "method": "mean of stored normalised chunk embeddings per document, renormalised, cosine",
        "documents": len(ids),
        "dimension": int(doc_matrix.shape[1]),
        "build_seconds": round(build_seconds, 2),
        "top_documents": n,
        "doc_embedding_only": {
            "mean_document_recall": {d: round(statistics.mean([r["recall_doc_embedding"][d] for r in rows]), 4)
                                     for d in ("1", "3", "5", "10")},
            "cases_all_expected_routed": sum(1 for r in rows if r["doc_embedding_all_routed"]),
            "cases_missing": [r["case_id"] for r in rows if not r["doc_embedding_all_routed"]],
        },
        "hybrid_with_chunk_routing": {
            "mean_document_recall": {d: round(statistics.mean([r["recall_hybrid"][d] for r in rows]), 4)
                                     for d in ("1", "3", "5", "10")},
            "cases_all_expected_routed": sum(1 for r in rows if r["hybrid_all_routed"]),
            "cases_missing": [r["case_id"] for r in rows if not r["hybrid_all_routed"]],
        },
        "per_case": rows,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    for key in ("doc_embedding_only", "hybrid_with_chunk_routing"):
        s = summary[key]
        m = s["mean_document_recall"]
        print(f"{key:26s} @1={m['1']:.3f} @3={m['3']:.3f} @5={m['5']:.3f} @10={m['10']:.3f} "
              f"all-routed={s['cases_all_expected_routed']}/20 missing={s['cases_missing']}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
