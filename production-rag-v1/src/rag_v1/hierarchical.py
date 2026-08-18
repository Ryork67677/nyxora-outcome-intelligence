"""EXP-012: two-stage document -> passage retrieval.

Why this exists
---------------
AN-003 has shown the same shape in every configuration since EXP-007: the correct
document ranks 2nd-6th while the answer chunk is absent from the top 300. EXP-010
established the answer is *visible* to the encoder, and EXP-011 that query
rewriting rescues zero cases. One remaining explanation is competition: the right
passage is ranked against ~14,209 chunks, nearly all from irrelevant documents.

This module removes that competition and lets the measurement decide.

What it deliberately does not change
------------------------------------
No new scorer. Document ranks are *derived from* the existing BM25 and transformer
chunk rankings, and local passage ranking reuses the **full-corpus** scores — the
candidate set shrinks, the numbers attached to each candidate do not. Restricting
BM25's term statistics to the selected documents would re-weight the lexicon and
confound topology with statistics, so it is not done here (see
``experiments/EXP-012/preregistration.md``).
"""

from __future__ import annotations

from collections import defaultdict

from rag_v1.types import SearchHit

DOCUMENT_RRF_K = 60


def collapse_to_documents(hits: list[SearchHit]) -> list[tuple[str, int]]:
    """Collapse a chunk ranking into a document ranking.

    A document's rank is the position of its **highest-ranked chunk**, and each
    document votes exactly once. Counting every chunk would let a document with
    many mediocre passages outrank one holding a single excellent passage, which
    is the opposite of what routing should do.

    Ties are impossible here (chunk ranks are unique), but the sort is still made
    total on ``version_id`` so the order cannot depend on input ordering.
    """
    best: dict[str, int] = {}
    for hit in hits:
        if hit.version_id not in best or hit.rank < best[hit.version_id]:
            best[hit.version_id] = hit.rank
    return sorted(best.items(), key=lambda kv: (kv[1], kv[0]))


def fuse_document_rankings(
    named_rankings: list[tuple[str, list[tuple[str, int]]]], rrf_k: int = DOCUMENT_RRF_K
) -> list[dict]:
    """RRF over document rankings from independent retrievers.

    Each entry is ``(label, [(version_id, chunk_rank), ...])``. Documents are
    scored on their *document* position in each list, not on the chunk rank that
    produced it, so a retriever that needed 40 chunks to reach its third document
    contributes the same as one that reached its third document at chunk 5.
    """
    scores: dict[str, float] = defaultdict(float)
    contributions: dict[str, dict[str, float]] = defaultdict(dict)
    positions: dict[str, dict[str, int]] = defaultdict(dict)

    for label, ranking in named_rankings:
        for position, (version_id, chunk_rank) in enumerate(ranking, start=1):
            contribution = 1.0 / (rrf_k + position)
            scores[version_id] += contribution
            contributions[version_id][label] = contribution
            positions[version_id][label] = position
            positions[version_id][f"{label}_best_chunk_rank"] = chunk_rank

    ordered = sorted(scores, key=lambda v: (-scores[v], v))
    return [
        {
            "version_id": version_id,
            "document_rank": rank,
            "score": scores[version_id],
            "contributions": contributions[version_id],
            "source_positions": positions[version_id],
            "contributing_sources": sorted(contributions[version_id]),
        }
        for rank, version_id in enumerate(ordered, start=1)
    ]


def document_rank_of(ranking: list[tuple[str, int]], version_id: str) -> int | None:
    for position, (candidate, _chunk_rank) in enumerate(ranking, start=1):
        if candidate == version_id:
            return position
    return None


def fused_rank_of(fused: list[dict], version_id: str) -> int | None:
    for entry in fused:
        if entry["version_id"] == version_id:
            return entry["document_rank"]
    return None


def routing_recall(rankings: list[tuple[str, int]] | list[dict], expected: set[str],
                   depths: tuple[int, ...] = (1, 3, 5, 10)) -> dict:
    """Fraction of expected documents present in the top-N routed set.

    This is the ceiling on everything downstream: a document that is not routed
    cannot have its passages retrieved by any Stage-2 ranking.
    """
    if rankings and isinstance(rankings[0], dict):
        order = [r["version_id"] for r in rankings]
    else:
        order = [v for v, _ in rankings]
    out = {}
    for depth in depths:
        selected = set(order[:depth])
        out[str(depth)] = round(len(expected & selected) / len(expected), 4) if expected else 1.0
    return out


def chunk_counts_for_documents(snapshot_id: str, chunk_set_id: str,
                               version_ids: list[str]) -> dict:
    """How much competition the routing actually removed."""
    from rag_v1.db import connect

    if not version_ids:
        return {"documents": 0, "chunks": 0}
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*) FROM chunk c
            JOIN corpus_snapshot_version sv ON sv.version_id = c.version_id
            WHERE sv.snapshot_id=%s AND c.chunk_set_id=%s AND c.version_id = ANY(%s)
            """,
            (snapshot_id, chunk_set_id, version_ids),
        )
        return {"documents": len(version_ids), "chunks": cur.fetchone()[0]}


__all__ = [
    "DOCUMENT_RRF_K", "chunk_counts_for_documents", "collapse_to_documents",
    "document_rank_of", "fuse_document_rankings", "fused_rank_of", "routing_recall",
]
