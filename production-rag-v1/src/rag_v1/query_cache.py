"""EXP-011: query-embedding cache.

Multi-view retrieval encodes several representations of every question, and the
same representation recurs across cells — the raw view is present in A, C and E,
and a normalized view sometimes collapses to the raw text. Re-encoding it each
time is pure waste and, worse, makes latency figures depend on cell ordering.

The cache is keyed on ``(query_text_hash, model_fingerprint)``. The fingerprint is
part of the key because a different encoder produces different vectors for the
same string; without it a cached vector could silently outlive the model that
made it.

It caches **query** vectors only. Document embeddings are untouched — EXP-011
freezes them by design.
"""

from __future__ import annotations

from collections.abc import Sequence

from rag_v1.ids import content_hash


class CachedQueryEmbedder:
    """Wraps an embedder, memoising query vectors for the life of the process."""

    def __init__(self, embedder, fingerprint: str | None = None):
        self._embedder = embedder
        self.fingerprint = fingerprint or getattr(embedder, "model_version", "unknown")
        self._cache: dict[tuple[str, str], list[float]] = {}
        self.hits = 0
        self.misses = 0

    @property
    def provider(self) -> str:
        return getattr(self._embedder, "provider", "unknown")

    @property
    def model_name(self) -> str:
        return getattr(self._embedder, "model_name", "unknown")

    def key(self, text: str) -> tuple[str, str]:
        return (content_hash(text), self.fingerprint)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        pending: list[tuple[int, str]] = []
        for index, text in enumerate(texts):
            cached = self._cache.get(self.key(text))
            if cached is None:
                pending.append((index, text))
                out.append([])
                self.misses += 1
            else:
                out.append(cached)
                self.hits += 1
        if pending:
            vectors = self._embedder.embed([t for _i, t in pending])
            for (index, text), vector in zip(pending, vectors, strict=True):
                self._cache[self.key(text)] = vector
                out[index] = vector
        return out

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {
            "query_embedding_cache_hits": self.hits,
            "query_embedding_cache_misses": self.misses,
            "query_embedding_cache_hit_rate": round(self.hits / total, 4) if total else None,
            "distinct_queries_cached": len(self._cache),
            "model_fingerprint": self.fingerprint,
        }


__all__ = ["CachedQueryEmbedder"]
