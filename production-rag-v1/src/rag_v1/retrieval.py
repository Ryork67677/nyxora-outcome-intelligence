from __future__ import annotations

import re
from collections import defaultdict

from rag_v1.types import SearchHit

_TERM_RE = re.compile(r"[A-Za-z0-9_.\-]+")


def query_terms(query: str) -> list[str]:
    """Split a natural-language question into tsquery terms.

    Identifier punctuation (``_``, ``.``, ``-``) is kept inside a term so that
    ``request_too_large`` survives as one term. Postgres still splits it into
    adjacent lexemes, but ``phraseto_tsquery`` turns those back into a phrase
    match, which preserves identifier precision without a scalar boost.
    """
    # A term must be longer than one character and carry at least one
    # alphanumeric character; "--" and "..." are punctuation, not search terms.
    terms = [t for t in _TERM_RE.findall(query) if len(t) > 1 and any(ch.isalnum() for ch in t)]
    # Preserve first-occurrence order while removing duplicates.
    return list(dict.fromkeys(terms))


# Lexical scoring is BM25 over the existing generated TSVECTOR and GIN index.
#
# Two measured failures drove this (see docs/failure-reports/FAIL-0001.md):
#
# 1. ``websearch_to_tsquery`` ANDs every token, so a 16-token question required
#    all 16 tokens inside one chunk and returned nothing at all — recall 0.000.
# 2. OR-ing the terms and ranking with ``ts_rank_cd`` recovered some cases but
#    still scored badly, because ts_rank has no inverse document frequency. A
#    chunk matching five ubiquitous words ("the", "api", "code") outranked the
#    chunk containing the one rare identifier the question was actually about.
#
# BM25 fixes exactly that: a term's weight falls as its document frequency
# rises, so ``request_too_large`` (df 59) dominates ``type`` (df 5494) without
# anything resembling a scalar identifier boost. Term frequency is treated as
# binary presence per chunk, which is what the TSVECTOR match gives us cheaply;
# the length normalization term is retained so long reference tables stop
# outranking short precise statements purely by size.
#
# k1/b are the standard BM25 defaults. They were not swept against the golden
# set, so they are not a value fitted to these 20 questions.
BM25_K1 = 1.2
BM25_B = 0.75

_LEXICAL_SQL = """
WITH terms AS (
    SELECT DISTINCT t, phraseto_tsquery('simple', t) AS tq
    FROM unnest(%(terms)s::text[]) AS t
    WHERE phraseto_tsquery('simple', t)::text <> ''
),
corpus AS (
    SELECT count(*)::float8 AS n, avg(length(c.text))::float8 AS avg_len
    FROM chunk c
    JOIN corpus_snapshot_version sv ON sv.version_id = c.version_id
    WHERE sv.snapshot_id = %(snapshot_id)s
),
weighted AS (
    SELECT terms.tq,
           ln(1 + (corpus.n - stat.df + 0.5) / (stat.df + 0.5)) AS idf,
           corpus.avg_len
    FROM terms
    CROSS JOIN corpus
    CROSS JOIN LATERAL (
        SELECT count(*)::float8 AS df
        FROM chunk c
        JOIN corpus_snapshot_version sv ON sv.version_id = c.version_id
        WHERE sv.snapshot_id = %(snapshot_id)s
          AND c.search_vector @@ terms.tq
    ) AS stat
    WHERE stat.df > 0
)
SELECT c.chunk_id, c.version_id, c.section_path, c.char_start, c.char_end, c.text,
       sum(
           w.idf * (%(k1)s + 1)
           / (1 + %(k1)s * (1 - %(b)s + %(b)s * length(c.text) / w.avg_len))
       ) AS score
FROM chunk c
JOIN corpus_snapshot_version sv ON sv.version_id = c.version_id
JOIN weighted w ON c.search_vector @@ w.tq
WHERE sv.snapshot_id = %(snapshot_id)s
GROUP BY c.chunk_id, c.version_id, c.section_path, c.char_start, c.char_end, c.text
ORDER BY score DESC, c.chunk_id
LIMIT %(k)s
"""


def lexical_search(query: str, snapshot_id: str, k: int = 20) -> list[SearchHit]:
    from rag_v1.db import connect
    terms = query_terms(query)
    if not terms:
        return []
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            _LEXICAL_SQL,
            {
                "terms": terms,
                "snapshot_id": snapshot_id,
                "k": k,
                "k1": BM25_K1,
                "b": BM25_B,
            },
        )
        rows = cur.fetchall()
    return [
        SearchHit(
            chunk_id=r[0], version_id=r[1], section_path=r[2], char_start=r[3], char_end=r[4],
            text=r[5], score=float(r[6]), rank=i + 1, retriever="lexical",
        )
        for i, r in enumerate(rows)
    ]


def dense_search(query: str, snapshot_id: str, model_id: str, k: int = 20) -> list[SearchHit]:
    from rag_v1.db import connect
    from rag_v1.embeddings import get_embedder

    embedder = get_embedder()
    qvec = embedder.embed([query])[0]
    sql = """
    SELECT c.chunk_id, c.version_id, c.section_path, c.char_start, c.char_end, c.text,
           1 - (ce.embedding <=> %s::vector) AS score
    FROM chunk_embedding ce
    JOIN chunk c ON c.chunk_id=ce.chunk_id
    JOIN corpus_snapshot_version sv ON sv.version_id=c.version_id
    WHERE ce.model_id=%s AND sv.snapshot_id=%s
    ORDER BY ce.embedding <=> %s::vector
    LIMIT %s
    """
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, (qvec, model_id, snapshot_id, qvec, k))
        rows = cur.fetchall()
    return [
        SearchHit(
            chunk_id=r[0], version_id=r[1], section_path=r[2], char_start=r[3], char_end=r[4],
            text=r[5], score=float(r[6]), rank=i + 1, retriever="dense",
        )
        for i, r in enumerate(rows)
    ]


def interleave_hybrid(lexical: list[SearchHit], dense: list[SearchHit], k: int = 20) -> list[SearchHit]:
    out: list[SearchHit] = []
    seen: set[str] = set()
    for i in range(max(len(lexical), len(dense))):
        for source in (lexical, dense):
            if i < len(source) and source[i].chunk_id not in seen:
                hit = source[i].model_copy(deep=True)
                hit.retriever = "hybrid_interleave"
                hit.rank = len(out) + 1
                out.append(hit)
                seen.add(hit.chunk_id)
                if len(out) >= k:
                    return out
    return out


def rrf_fuse(ranked_lists: list[list[SearchHit]], rrf_k: int = 60, top_k: int = 20) -> list[SearchHit]:
    scores: dict[str, float] = defaultdict(float)
    exemplars: dict[str, SearchHit] = {}
    contributions: dict[str, dict[str, float]] = defaultdict(dict)

    for ranked in ranked_lists:
        for hit in ranked:
            contribution = 1.0 / (rrf_k + hit.rank)
            scores[hit.chunk_id] += contribution
            exemplars.setdefault(hit.chunk_id, hit)
            contributions[hit.chunk_id][hit.retriever] = contribution

    ordered = sorted(scores, key=lambda cid: (-scores[cid], cid))[:top_k]
    out: list[SearchHit] = []
    for rank, cid in enumerate(ordered, start=1):
        h = exemplars[cid].model_copy(deep=True)
        h.score = scores[cid]
        h.rank = rank
        h.retriever = "rrf"
        h.metadata["rrf_contributions"] = contributions[cid]
        out.append(h)
    return out


def exact_identifier_search(query: str, snapshot_id: str, k: int = 20) -> list[SearchHit]:
    from rag_v1.db import connect
    # EXP-003B hypothesis: identifiers are a third ranked list, never a scalar boost.
    tokens = [t for t in query.replace("`", " ").split() if ("_" in t or "." in t or "-" in t)]
    if not tokens:
        return []
    token = max(tokens, key=len).strip(".,:;()[]{}")
    sql = """
    SELECT c.chunk_id, c.version_id, c.section_path, c.char_start, c.char_end, c.text,
           CASE WHEN c.text LIKE %s THEN 1.0 ELSE 0.0 END AS score
    FROM chunk c
    JOIN corpus_snapshot_version sv ON sv.version_id=c.version_id
    WHERE sv.snapshot_id=%s AND c.text LIKE %s
    ORDER BY c.version_id DESC, c.ordinal
    LIMIT %s
    """
    pattern = f"%{token}%"
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, (pattern, snapshot_id, pattern, k))
        rows = cur.fetchall()
    return [
        SearchHit(
            chunk_id=r[0], version_id=r[1], section_path=r[2], char_start=r[3], char_end=r[4],
            text=r[5], score=float(r[6]), rank=i + 1, retriever="exact_identifier",
            metadata={"identifier": token},
        )
        for i, r in enumerate(rows)
    ]
