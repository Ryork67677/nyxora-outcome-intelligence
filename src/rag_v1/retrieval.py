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


def snapshot_chunk_set(snapshot_id: str) -> str:
    """Resolve which chunking a snapshot pins.

    Since EXP-005 a snapshot fixes both the document versions and the chunking of
    them, so every chunk query has to be scoped to that chunk set. It is resolved
    once here, in Python, and passed down as a scalar. Expressing it instead as an
    extra join on ``corpus_snapshot`` gave the planner one more relation to
    reorder and it stopped using the GIN index on the outer scoring join — the
    same evaluation went from under a second to over a minute. A plain equality
    predicate keeps the query plan that produced the published EXP-000 numbers.
    """
    from rag_v1.db import connect

    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT chunk_set_id FROM corpus_snapshot WHERE snapshot_id=%s", (snapshot_id,))
        row = cur.fetchone()
    if not row:
        raise ValueError(f"Unknown snapshot: {snapshot_id}")
    return row[0]

_LEXICAL_SQL = """
WITH terms AS (
    SELECT DISTINCT t, phraseto_tsquery('simple', t) AS tq
    FROM unnest(%(terms)s::text[]) AS t
    WHERE phraseto_tsquery('simple', t)::text <> ''
),
corpus AS (
    SELECT count(*)::float8 AS n, avg(length(coalesce(c.search_text, c.text)))::float8 AS avg_len
    FROM chunk c
    JOIN corpus_snapshot_version sv ON sv.version_id = c.version_id
    WHERE sv.snapshot_id = %(snapshot_id)s
      AND c.chunk_set_id = %(chunk_set_id)s
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
          AND c.chunk_set_id = %(chunk_set_id)s
          AND c.search_vector @@ terms.tq
    ) AS stat
    WHERE stat.df > 0
)
SELECT * FROM (
    SELECT c.chunk_id, c.version_id, c.section_path, c.char_start, c.char_end, c.text,
           sum(
               w.idf * (%(k1)s + 1)
               / (1 + %(k1)s * (1 - %(b)s + %(b)s * length(coalesce(c.search_text, c.text)) / w.avg_len))
           ) AS score
    FROM chunk c
    JOIN corpus_snapshot_version sv ON sv.version_id = c.version_id
    JOIN weighted w ON c.search_vector @@ w.tq
    WHERE sv.snapshot_id = %(snapshot_id)s
      AND c.chunk_set_id = %(chunk_set_id)s
      -- EXP-012 restricts candidates to routed documents. The filter sits in the
      -- *scoring* select only: the corpus and weighted CTEs above still compute n,
      -- avg_len and df across the whole snapshot, so a term's IDF is identical to
      -- the global run. Restricting those CTEs instead would re-weight the lexicon
      -- inside the selected documents and confound topology with statistics.
      AND (%(version_ids)s::text[] IS NULL OR c.version_id = ANY(%(version_ids)s::text[]))
    GROUP BY c.chunk_id, c.version_id, c.section_path, c.char_start, c.char_end, c.text
) scored
-- Ties are common in BM25, and sum() accumulates in whatever order the plan
-- produces, so two chunks with mathematically equal scores could differ in the
-- last float bit and swap places between runs. Rounding before the sort makes
-- exact ties resolve on chunk_id instead, which keeps a re-run reproducible.
ORDER BY round(scored.score::numeric, 9) DESC, scored.chunk_id
LIMIT %(k)s
"""


def lexical_search(
    query: str, snapshot_id: str, k: int = 20, version_ids: list[str] | None = None
) -> list[SearchHit]:
    """BM25 over the snapshot, optionally restricted to selected documents.

    ``version_ids`` is optional and defaults to the whole snapshot, which is how
    every experiment through EXP-011 called this. When supplied (EXP-012), the
    restriction applies to candidate selection only — term statistics remain those
    of the full corpus, so a chunk's score is the same number it would have had in
    the global ranking.
    """
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
                "chunk_set_id": snapshot_chunk_set(snapshot_id),
                "k": k,
                "k1": BM25_K1,
                "b": BM25_B,
                "version_ids": version_ids,
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


def dense_search(
    query: str, snapshot_id: str, model_id: str, k: int = 20, embedder=None,
    version_ids: list[str] | None = None,
) -> list[SearchHit]:
    """Exact cosine search. No ANN index exists, so this is a full scan by design.

    ``embedder`` is optional and defaults to the configured one, which is how every
    experiment through EXP-008 called this. EXP-009 compares two dense encoders in
    a single process, and each one must embed the query with the same weights that
    embedded the chunks — a query vector from the wrong encoder would silently
    produce meaningless similarities rather than an error.
    """
    from rag_v1.db import connect

    if embedder is None:
        from rag_v1.embeddings import get_embedder

        embedder = get_embedder()
    qvec = embedder.embed([query])[0]
    # Cosine ties are common here — the corpus repeats identical documentation text
    # across pages, and EXP-007 found four chunks tied at 0.941729 for one query.
    # Without a tie-break the plan decides their order and a re-run reorders them,
    # exactly the reproducibility defect fixed for BM25 in EXP-005. Rounding the
    # distance before sorting makes exact ties resolve on chunk_id.
    sql = """
    SELECT * FROM (
        SELECT c.chunk_id, c.version_id, c.section_path, c.char_start, c.char_end, c.text,
               1 - (ce.embedding <=> %s::vector) AS score,
               (ce.embedding <=> %s::vector) AS distance
        FROM chunk_embedding ce
        JOIN chunk c ON c.chunk_id=ce.chunk_id
        JOIN corpus_snapshot_version sv ON sv.version_id=c.version_id
        WHERE ce.model_id=%s AND sv.snapshot_id=%s AND c.chunk_set_id=%s
          AND (%s::text[] IS NULL OR c.version_id = ANY(%s::text[]))
    ) scored
    ORDER BY round(scored.distance::numeric, 9) ASC, scored.chunk_id
    LIMIT %s
    """
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, (qvec, qvec, model_id, snapshot_id, snapshot_chunk_set(snapshot_id),
                          version_ids, version_ids, k))
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
    WHERE sv.snapshot_id=%s AND c.chunk_set_id=%s AND c.text LIKE %s
    ORDER BY c.version_id DESC, c.ordinal
    LIMIT %s
    """
    pattern = f"%{token}%"
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, (pattern, snapshot_id, snapshot_chunk_set(snapshot_id), pattern, k))
        rows = cur.fetchall()
    return [
        SearchHit(
            chunk_id=r[0], version_id=r[1], section_path=r[2], char_start=r[3], char_end=r[4],
            text=r[5], score=float(r[6]), rank=i + 1, retriever="exact_identifier",
            metadata={"identifier": token},
        )
        for i, r in enumerate(rows)
    ]


def evidence_region_key(hit: SearchHit) -> tuple:
    """The identity a candidate is deduplicated on across chunk representations."""
    return (hit.version_id, tuple(hit.section_path))


def rrf_fuse_regions(
    ranked_lists: list[list[SearchHit]], rrf_k: int = 60, top_k: int = 20
) -> list[SearchHit]:
    """RRF across retrievers that may return *different chunk representations*.

    EXP-010 fuses BM25 over the control chunks with the transformer over the
    encoder-aligned chunks. The two sets cut the same documents differently, so
    chunk_id cannot be the deduplication key: the same passage appears under two
    ids and would be scored twice, inflating the fused result for no retrieval
    reason.

    Two candidates are the same **evidence region** when they share a document
    version and a section path and their ``[char_start, char_end)`` spans overlap.
    Overlapping candidates are merged into one contiguous region, and a region
    receives **one** contribution per retriever, taken at that retriever's best
    (lowest) rank for the region. A region therefore cannot be rewarded twice
    merely for existing in two representations.

    The emitted span is the union of the merged members. Because members are merged
    only when they overlap, the union is contiguous and every point in it lies in
    some member — so "the union overlaps the evidence" is exactly equivalent to
    "some retrieved member overlaps the evidence". It does not make a hit easier to
    score than in a single-representation cell.

    When every list comes from the same chunk set — as in the reproduction cells —
    chunks do not overlap each other, so no merging occurs and this reduces exactly
    to :func:`rrf_fuse`.
    """
    # Collect candidates per (version, section), then merge overlapping spans.
    buckets: dict[tuple, list[SearchHit]] = defaultdict(list)
    for ranked in ranked_lists:
        for hit in ranked:
            buckets[evidence_region_key(hit)].append(hit)

    regions: list[dict] = []
    for key, hits in buckets.items():
        for hit in sorted(hits, key=lambda h: (h.char_start, h.char_end)):
            if regions and regions[-1]["key"] == key and hit.char_start < regions[-1]["end"]:
                regions[-1]["end"] = max(regions[-1]["end"], hit.char_end)
                regions[-1]["members"].append(hit)
            else:
                regions.append({"key": key, "start": hit.char_start, "end": hit.char_end,
                                "members": [hit]})

    scored: list[tuple[float, str, dict, dict]] = []
    for region in regions:
        best_by_retriever: dict[str, SearchHit] = {}
        for hit in region["members"]:
            current = best_by_retriever.get(hit.retriever)
            if current is None or hit.rank < current.rank:
                best_by_retriever[hit.retriever] = hit
        contributions = {r: 1.0 / (rrf_k + h.rank) for r, h in best_by_retriever.items()}
        exemplar = min(best_by_retriever.values(), key=lambda h: (h.rank, h.chunk_id))
        scored.append((sum(contributions.values()), exemplar.chunk_id, region, {
            "rrf_contributions": contributions,
            "member_chunk_ids": sorted({h.chunk_id for h in region["members"]}),
            "merged_members": len(region["members"]),
            "region_span": [region["start"], region["end"]],
            "exemplar_chunk_id": exemplar.chunk_id,
        }))

    scored.sort(key=lambda row: (-row[0], row[1]))
    out: list[SearchHit] = []
    for rank, (score, _cid, region, meta) in enumerate(scored[:top_k], start=1):
        exemplar = min(region["members"], key=lambda h: (h.rank, h.chunk_id))
        hit = exemplar.model_copy(deep=True)
        hit.char_start, hit.char_end = region["start"], region["end"]
        hit.score, hit.rank, hit.retriever = score, rank, "rrf_regions"
        hit.metadata = {**hit.metadata, **meta}
        out.append(hit)
    return out


def rrf_fuse_labelled(
    labelled_lists: list[tuple[str, list[SearchHit]]], rrf_k: int = 60, top_k: int = 20
) -> list[SearchHit]:
    """RRF across lists that differ by *query representation* as well as retriever.

    EXP-011 runs several views of one question — raw, normalized, structured —
    through both retrievers, producing up to six ranked lists over the same chunk
    set. :func:`rrf_fuse` keys contributions on ``hit.retriever``, which cannot
    separate BM25-on-raw from BM25-on-normalized: the second list would overwrite
    the first and the fusion would silently lose a view.

    Each list is therefore labelled explicitly, and every label contributes once
    per candidate. Provenance is recorded on the fused hit so any final position
    can be traced back to the view and retriever that produced it, and to the rank
    it held there.

    Every list participates equally. No weight is assigned to any view — with 20
    questions, weights chosen after seeing which cases improve would be fitted to
    the evaluation set rather than measured on it.
    """
    scores: dict[str, float] = defaultdict(float)
    exemplars: dict[str, SearchHit] = {}
    contributions: dict[str, dict[str, float]] = defaultdict(dict)
    source_ranks: dict[str, dict[str, int]] = defaultdict(dict)

    for label, ranked in labelled_lists:
        best_rank: dict[str, int] = {}
        for hit in ranked:
            # One list may not reward the same chunk twice.
            if hit.chunk_id not in best_rank or hit.rank < best_rank[hit.chunk_id]:
                best_rank[hit.chunk_id] = hit.rank
                exemplars.setdefault(hit.chunk_id, hit)
        for chunk_id, rank in best_rank.items():
            contribution = 1.0 / (rrf_k + rank)
            scores[chunk_id] += contribution
            contributions[chunk_id][label] = contribution
            source_ranks[chunk_id][label] = rank

    ordered = sorted(scores, key=lambda cid: (-scores[cid], cid))[:top_k]
    out: list[SearchHit] = []
    for rank, chunk_id in enumerate(ordered, start=1):
        hit = exemplars[chunk_id].model_copy(deep=True)
        hit.score = scores[chunk_id]
        hit.rank = rank
        hit.retriever = "rrf_views"
        hit.metadata = {
            **hit.metadata,
            "rrf_contributions": contributions[chunk_id],
            "source_ranks": source_ranks[chunk_id],
            "contributing_sources": sorted(contributions[chunk_id]),
            "source_count": len(contributions[chunk_id]),
        }
        out.append(hit)
    return out
