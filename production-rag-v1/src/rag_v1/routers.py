"""EXP-013: document routers — how chunk evidence becomes a document ranking.

Why this exists
---------------
EXP-012's oracle diagnostic showed the passage layer is mostly fine: given the
correct document, the same retrievers and the same fusion reach 0.950 / 19-of-20
with zero regressions. What failed was routing — every required document reaches
the top 5 for only 17 of 20 questions, and an excluded document is unrecoverable.

The router EXP-012 used gives a document the rank of its **single highest-ranked
chunk** and discards everything else. A document supported at ranks 2, 7, 11 and 18
loses to one whose only support is rank 1 and whose next chunks sit at 150 and 270.
This module implements that rule as a control and three alternatives that use the
discarded evidence.

Everything stays in the rank domain
-----------------------------------
BM25 scores and cosine similarities are on different scales. Adding them, or
normalising them against 20 questions and then tuning a weight, would fit the
evaluation set rather than measure on it. So every router consumes *ranks* and
emits *ranks*, and cross-retriever combination is always RRF.

All parameters here are preregistered (``experiments/EXP-013/preregistration.md``)
and were fixed before any routing result was observed.
"""

from __future__ import annotations

from collections import defaultdict

from rag_v1.types import SearchHit

#: Preregistered, not tuned.
RANK_SUM_K = 60
RANK_SUM_SUPPORT_CHUNKS = 5
VOTE_DEPTH = 50
DOCUMENT_RRF_K = 60


def _supporting_ranks(hits: list[SearchHit]) -> dict[str, list[int]]:
    """Every chunk rank each document contributed, ascending."""
    support: dict[str, list[int]] = defaultdict(list)
    for hit in hits:
        support[hit.version_id].append(hit.rank)
    for ranks in support.values():
        ranks.sort()
    return support


def _order(scored: dict[str, float], support: dict[str, list[int]]) -> list[tuple[str, int]]:
    """Total ordering: score desc, then best supporting chunk, then document id.

    The tie-breaks make the result independent of dictionary and input ordering,
    which is what lets a re-run reproduce a routing decision exactly.
    """
    ordered = sorted(scored, key=lambda v: (-scored[v], support[v][0], v))
    return [(version_id, support[version_id][0]) for version_id in ordered]


def router_max(hits: list[SearchHit]) -> list[tuple[str, int]]:
    """ROUTER_A_MAX — a document ranks at its highest-ranked chunk (EXP-012 rule)."""
    support = _supporting_ranks(hits)
    # Negated so the shared ordering helper (score descending) puts the best
    # chunk first without a second code path.
    scored = {v: -float(ranks[0]) for v, ranks in support.items()}
    return _order(scored, support)


def router_rank_sum(hits: list[SearchHit], k: int = RANK_SUM_K,
                    support_chunks: int = RANK_SUM_SUPPORT_CHUNKS) -> list[tuple[str, int]]:
    """ROUTER_B_RANK_SUM — reciprocal-rank support from a document's best chunks.

    ``score = sum(1 / (k + rank))`` over the document's top ``support_chunks``
    chunks. Capping the support count stops a long document from out-scoring a
    short one purely by having more chunks in the list.
    """
    support = _supporting_ranks(hits)
    scored = {v: sum(1.0 / (k + r) for r in ranks[:support_chunks])
              for v, ranks in support.items()}
    return _order(scored, support)


def router_topk_vote(hits: list[SearchHit], depth: int = VOTE_DEPTH) -> list[tuple[str, int]]:
    """ROUTER_C_TOPK_VOTE — one vote per chunk inside the top ``depth``.

    Deliberately coarse: it ignores *where* in the top 50 a chunk sits, so it
    measures breadth of support rather than strength. Ties fall back to the best
    supporting chunk, which is Router A's signal.
    """
    considered = [h for h in hits if h.rank <= depth]
    support = _supporting_ranks(hits)
    votes: dict[str, float] = defaultdict(float)
    for hit in considered:
        votes[hit.version_id] += 1.0
    # Documents with no chunk inside the vote depth still need an ordering.
    for version_id in support:
        votes.setdefault(version_id, 0.0)
    return _order(votes, support)


def rrf_document_lists(named: list[tuple[str, list[tuple[str, int]]]],
                       k: int = DOCUMENT_RRF_K) -> list[dict]:
    """RRF over document rankings, scoring on document position not chunk rank."""
    scores: dict[str, float] = defaultdict(float)
    contributions: dict[str, dict[str, float]] = defaultdict(dict)
    positions: dict[str, dict[str, int]] = defaultdict(dict)
    best_chunk: dict[str, int] = {}

    for label, ranking in named:
        for position, (version_id, chunk_rank) in enumerate(ranking, start=1):
            contribution = 1.0 / (k + position)
            scores[version_id] += contribution
            contributions[version_id][label] = contribution
            positions[version_id][label] = position
            if version_id not in best_chunk or chunk_rank < best_chunk[version_id]:
                best_chunk[version_id] = chunk_rank

    ordered = sorted(scores, key=lambda v: (-scores[v], best_chunk[v], v))
    return [
        {"version_id": v, "document_rank": rank, "score": scores[v],
         "contributions": contributions[v], "source_positions": positions[v],
         "best_supporting_chunk_rank": best_chunk[v],
         "contributing_sources": sorted(contributions[v])}
        for rank, v in enumerate(ordered, start=1)
    ]


def router_max_support(lex: list[SearchHit], den: list[SearchHit],
                       k: int = DOCUMENT_RRF_K) -> list[dict]:
    """ROUTER_D_MAX_SUPPORT — keep the strong single-chunk signal *and* breadth.

    Four ranked document lists are fused: a best-chunk list and a rank-sum support
    list for each retriever. Expressing the combination as RRF over ranks avoids
    inventing a scalar weight between "has one excellent chunk" and "has several
    good ones", which would be a tuned constant with no principled value.
    """
    return rrf_document_lists([
        ("bm25_max", router_max(lex)),
        ("bm25_support", router_rank_sum(lex)),
        ("transformer_max", router_max(den)),
        ("transformer_support", router_rank_sum(den)),
    ], k=k)


#: name -> (per-retriever ranking function, description)
SINGLE_RETRIEVER_ROUTERS = {
    "A_MAX": (router_max, "document ranks at its highest-ranked chunk (EXP-012 control)"),
    "B_RANK_SUM": (router_rank_sum,
                   f"sum of 1/({RANK_SUM_K}+rank) over the top {RANK_SUM_SUPPORT_CHUNKS} chunks"),
    "C_TOPK_VOTE": (router_topk_vote, f"one vote per chunk inside the top {VOTE_DEPTH}"),
}

ROUTER_VERSION = "1.0"

ROUTER_PARAMETERS = {
    "rank_sum_k": RANK_SUM_K,
    "rank_sum_support_chunks": RANK_SUM_SUPPORT_CHUNKS,
    "vote_depth": VOTE_DEPTH,
    "document_rrf_k": DOCUMENT_RRF_K,
    "domain": "ranks only — BM25 and cosine scores are never combined directly",
    "tuned_against_eval_set": False,
}


def route(name: str, lex: list[SearchHit], den: list[SearchHit]) -> tuple[
        list[dict], dict[str, list[tuple[str, int]]]]:
    """Return the fused document ranking and the per-retriever rankings behind it."""
    if name == "D_MAX_SUPPORT":
        per_retriever = {"bm25": router_max(lex), "transformer": router_max(den),
                         "bm25_support": router_rank_sum(lex),
                         "transformer_support": router_rank_sum(den)}
        return router_max_support(lex, den), per_retriever
    if name not in SINGLE_RETRIEVER_ROUTERS:
        raise ValueError(f"Unknown router {name!r}. Available: "
                         f"{sorted([*SINGLE_RETRIEVER_ROUTERS, 'D_MAX_SUPPORT'])}")
    fn, _desc = SINGLE_RETRIEVER_ROUTERS[name]
    lex_docs, den_docs = fn(lex), fn(den)
    fused = rrf_document_lists([("bm25", lex_docs), ("transformer", den_docs)])
    return fused, {"bm25": lex_docs, "transformer": den_docs}


__all__ = [
    "DOCUMENT_RRF_K", "RANK_SUM_K", "RANK_SUM_SUPPORT_CHUNKS", "ROUTER_PARAMETERS",
    "ROUTER_VERSION", "SINGLE_RETRIEVER_ROUTERS", "VOTE_DEPTH", "route",
    "router_max", "router_max_support", "router_rank_sum", "router_topk_vote",
    "rrf_document_lists",
]
