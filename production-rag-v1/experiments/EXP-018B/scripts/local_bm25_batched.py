"""Track 1: score-preserving batched local BM25 (one full-corpus IDF pass).

Current SYSTEM-E calls lexical_search once per parent, which re-runs
_LEXICAL_SQL corpus/weighted CTEs (n, avg_len, df) independently for every
parent. This module issues ONE lexical_search over the parent set, then takes
top-W=20 per parent with the same ORDER BY / BM25 formula / snapshot / W.

Does not reuse SYSTEM-A's global top-50 BM25 list (RRF overwrites score; local
W=20 includes chunks that never appear in A's 50).
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from rag_v1.retrieval import lexical_search
from rag_v1.systems import SNAPSHOT
from rag_v1.types import SearchHit

from system_e import W

# cs_v1_control size; LIMIT this high returns every matching parent-set chunk
# so per-parent top-W is a pure slice of the same ORDER BY as a per-parent call.
CORPUS_CHUNKS = 14209
QUANT9 = Decimal("0.000000001")


def lexical_tiebreak_score(score: float) -> Decimal:
    """Postgres numeric ROUND(..., 9) half-away-from-zero; BM25 scores are >0."""
    return Decimal(str(score)).quantize(QUANT9, rounding=ROUND_HALF_UP)


def cross_parent_extra_sort_key(hit: SearchHit) -> tuple:
    """FROZEN EXP-018B Track 2 key. Do not change after scores.

    Existing E has no cross-parent order. Within-parent order from _LEXICAL_SQL:
    ORDER BY round(scored.score::numeric, 9) DESC, scored.chunk_id
    Adopted for extras not in A-pool-100 after dedupe.
    """
    return (-lexical_tiebreak_score(hit.score), hit.chunk_id)


def local_bm25_per_parent_batched(
    query: str, parent_ids: list[str], w: int = W
) -> dict[str, list[SearchHit]]:
    """Top-W BM25 inside each parent. One SQL. Full-corpus IDF. No dense lane."""
    expanded: dict[str, list[SearchHit]] = {vid: [] for vid in parent_ids}
    if not parent_ids:
        return expanded
    hits = lexical_search(query, SNAPSHOT, CORPUS_CHUNKS, version_ids=list(parent_ids))
    for hit in hits:
        bucket = expanded.get(hit.version_id)
        if bucket is None or len(bucket) >= w:
            continue
        h = hit.model_copy(deep=True)
        h.rank = len(bucket) + 1
        bucket.append(h)
    return expanded


def additive_extras_ordered(
    local: dict[str, list[SearchHit]], a_ids: set[str]
) -> list[SearchHit]:
    """Dedupe local hits, drop A-pool-100, sort by frozen cross-parent key."""
    by_id: dict[str, SearchHit] = {}
    for hits in local.values():
        for h in hits:
            if h.chunk_id in a_ids:
                continue
            by_id.setdefault(h.chunk_id, h)
    extras = list(by_id.values())
    extras.sort(key=cross_parent_extra_sort_key)
    return extras


def cap_local_lists(
    local: dict[str, list[SearchHit]], a_ids: set[str], extras_l: list[SearchHit]
) -> dict[str, list[SearchHit]]:
    """Keep original per-parent ranks. Retain A-overlap local hits; add selected extras."""
    selected = {h.chunk_id for h in extras_l}
    capped: dict[str, list[SearchHit]] = {}
    for vid, hits in local.items():
        capped[vid] = [
            h for h in hits if h.chunk_id in a_ids or h.chunk_id in selected
        ]
    return capped


__all__ = [
    "CORPUS_CHUNKS",
    "additive_extras_ordered",
    "cap_local_lists",
    "cross_parent_extra_sort_key",
    "lexical_tiebreak_score",
    "local_bm25_per_parent_batched",
]
