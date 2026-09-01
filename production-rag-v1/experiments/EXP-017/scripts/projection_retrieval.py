"""Projection-lane BM25 + dense + labelled RRF. Candidate-generation only."""

from __future__ import annotations

from rag_v1.db import connect
from rag_v1.retrieval import BM25_B, BM25_K1, query_terms, rrf_fuse_labelled
from rag_v1.types import SearchHit

PROJECTION_SET_ID = "ps_v2_ovl_win448_s224"
POOL = 50
RRF_K = 60

_LEXICAL_SQL = """
WITH terms AS (
    SELECT DISTINCT t, phraseto_tsquery('simple', t) AS tq
    FROM unnest(%(terms)s::text[]) AS t
    WHERE phraseto_tsquery('simple', t)::text <> ''
),
corpus AS (
    SELECT count(*)::float8 AS n, avg(length(sp.text))::float8 AS avg_len
    FROM search_projection sp
    WHERE sp.projection_set_id = %(projection_set_id)s
),
weighted AS (
    SELECT terms.tq,
           ln(1 + (corpus.n - stat.df + 0.5) / (stat.df + 0.5)) AS idf,
           corpus.avg_len
    FROM terms
    CROSS JOIN corpus
    CROSS JOIN LATERAL (
        SELECT count(*)::float8 AS df
        FROM search_projection sp
        WHERE sp.projection_set_id = %(projection_set_id)s
          AND sp.search_vector @@ terms.tq
    ) AS stat
    WHERE stat.df > 0
)
SELECT * FROM (
    SELECT sp.projection_id, sp.version_id, sp.char_start, sp.char_end, sp.text,
           sp.covering_chunk_ids,
           sum(
               w.idf * (%(k1)s + 1)
               / (1 + %(k1)s * (1 - %(b)s + %(b)s * length(sp.text) / w.avg_len))
           ) AS score
    FROM search_projection sp
    JOIN weighted w ON sp.search_vector @@ w.tq
    WHERE sp.projection_set_id = %(projection_set_id)s
    GROUP BY sp.projection_id, sp.version_id, sp.char_start, sp.char_end, sp.text,
             sp.covering_chunk_ids
) scored
ORDER BY round(scored.score::numeric, 9) DESC, scored.projection_id
LIMIT %(k)s
"""


def _hit(row, rank: int, retriever: str) -> SearchHit:
    return SearchHit(
        chunk_id=row[0],
        version_id=row[1],
        section_path=[],
        char_start=row[2],
        char_end=row[3],
        text=row[4],
        score=float(row[6]),
        rank=rank,
        retriever=retriever,
        metadata={"covering_chunk_ids": list(row[5] or [])},
    )


def projection_bm25(query: str, k: int = POOL) -> list[SearchHit]:
    terms = query_terms(query)
    if not terms:
        return []
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            _LEXICAL_SQL,
            {
                "terms": terms,
                "projection_set_id": PROJECTION_SET_ID,
                "k": k,
                "k1": BM25_K1,
                "b": BM25_B,
            },
        )
        rows = cur.fetchall()
    return [_hit(r, i + 1, "projection_bm25") for i, r in enumerate(rows)]


def projection_dense(query: str, model_id: str, embedder, k: int = POOL) -> list[SearchHit]:
    qvec = embedder.embed([query])[0]
    sql = """
    SELECT * FROM (
        SELECT sp.projection_id, sp.version_id, sp.char_start, sp.char_end, sp.text,
               sp.covering_chunk_ids,
               1 - (pe.embedding <=> %s::vector) AS score,
               (pe.embedding <=> %s::vector) AS distance
        FROM search_projection_embedding pe
        JOIN search_projection sp ON sp.projection_id = pe.projection_id
        WHERE pe.model_id=%s AND sp.projection_set_id=%s
    ) scored
    ORDER BY round(scored.distance::numeric, 9) ASC, scored.projection_id
    LIMIT %s
    """
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, (qvec, qvec, model_id, PROJECTION_SET_ID, k))
        rows = cur.fetchall()
    return [_hit(r, i + 1, "projection_dense") for i, r in enumerate(rows)]


def projection_rrf(query: str, model_id: str, embedder) -> list[SearchHit]:
    bm25 = projection_bm25(query, POOL)
    dense = projection_dense(query, model_id, embedder, POOL)
    fused = rrf_fuse_labelled(
        [("projection_bm25", bm25), ("projection_dense", dense)],
        rrf_k=RRF_K,
        top_k=max(len({h.chunk_id for h in bm25} | {h.chunk_id for h in dense}), 1),
    )
    cover_by_pid = {}
    for h in bm25 + dense:
        cover_by_pid.setdefault(h.chunk_id, h.metadata.get("covering_chunk_ids", []))
    for h in fused:
        h.metadata["covering_chunk_ids"] = cover_by_pid.get(h.chunk_id, [])
    return fused


def map_to_canonical_extras(
    fused: list[SearchHit], c_e_ids: set[str], p: int = 20
) -> dict:
    best: dict[str, float] = {}
    n_multi = 0
    for hit in fused:
        covering = list(hit.metadata.get("covering_chunk_ids") or [])
        if len(covering) > 1:
            n_multi += 1
        score = float(hit.score)
        for cid in covering:
            prev = best.get(cid)
            if prev is None or score > prev:
                best[cid] = score
    absent = [cid for cid in best if cid not in c_e_ids]
    absent.sort(key=lambda cid: (-best[cid], cid))
    c_p = absent[:p]
    return {
        "n_projection_hits": len(fused),
        "n_mapping_to_multiple_canonical": n_multi,
        "n_unique_canonical_from_projections": len(best),
        "n_previously_absent": len(absent),
        "C_P": c_p,
        "C_P_scores": {cid: best[cid] for cid in c_p},
        "best_score_by_chunk": best,
    }
