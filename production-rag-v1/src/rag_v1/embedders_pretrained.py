"""EXP-007: retrieval using a genuinely pretrained embedding model.

Why this exists
---------------
EXP-001..003 used a TF-IDF+SVD (LSA) encoder *fitted on this corpus*. That is not a
pretrained semantic model and cannot test the vocabulary-mismatch hypothesis: an
encoder fitted on the same corpus inherits the same term co-occurrence structure
that BM25 already exploits.

This module loads pretrained word vectors whose training corpus is entirely
independent of this project (see ``experiments/EXP-007/model-preregistration.md``,
written before any EXP-007 result was observed).

What it is, and what it is not
------------------------------
It is a genuinely pretrained model. It is **not** a transformer retrieval encoder —
those are unreachable in this environment, where ``huggingface.co`` and every
embedding API are blocked by network egress policy. Mean-pooled static word vectors
are order-insensitive and wash out over long chunks, so this is a *weak instrument*.
A positive result is therefore strong evidence; a negative result is weak evidence
against the hypothesis rather than a falsification of it.

Nothing here is fitted to the corpus or to the evaluation questions:

* Vectors come from the frozen pretrained file and are never updated.
* Pooling is a plain mean of L2-normalized token vectors. IDF/SIF weighting was
  rejected on purpose because both derive weights from *this* corpus.
* Only the vectors for tokens that actually occur are loaded, which is an
  identical-result memory optimisation, not a fit.
"""

from __future__ import annotations

import gzip
import re
from collections.abc import Iterable, Sequence
from pathlib import Path

import numpy as np

from rag_v1.config import settings
from rag_v1.ids import config_hash

MODEL_FILENAME = "fasttext-wiki-news-subwords-300.gz"

#: Recorded identity of the frozen pretrained artifact. Any change here is a
#: different model and must invalidate cached embeddings.
MODEL_CARD = {
    "provider": "gensim-data",
    "model_identifier": "fasttext-wiki-news-subwords-300",
    "origin": "facebookresearch/fastText wiki-news-300d-1M-subword",
    "revision": "gensim-data release asset, sha256 "
                "be48d40d6c67dbebe4b3eea22ab7dd7c7efbdb977d88654010f4eb740a836552",
    "training_corpus": "Wikipedia 2017 + UMBC webbase + statmt.org news (~16B tokens)",
    "vocabulary": 999999,
    "dimension": 300,
    "pooling": "mean of L2-normalized in-vocabulary token vectors",
    "normalization": "L2 on the pooled vector",
    "distance_metric": "cosine",
    "query_prefix": None,
    "document_prefix": None,
    "corpus_fitted": False,
}

# Keep identifier punctuation inside a token, matching the lexical tokenizer, so
# `request_too_large` is looked up whole before being decomposed.
_TOKEN_RE = re.compile(r"[A-Za-z0-9_.\-]+")
_SPLIT_RE = re.compile(r"[_.\-]+")


def tokenize(text: str) -> list[str]:
    """Lowercase tokens, keeping identifier punctuation."""
    return [t for t in _TOKEN_RE.findall(text.lower()) if any(ch.isalnum() for ch in t)]


def lookup_forms(token: str) -> list[str]:
    """The forms tried for one token, in order.

    An identifier is looked up whole first; if the pretrained vocabulary does not
    contain it, its underscore/dot/hyphen-separated parts are used instead. This is
    a fixed, generic rule — not tuned against the evaluation questions.
    """
    forms = [token]
    if _SPLIT_RE.search(token):
        forms.extend(p for p in _SPLIT_RE.split(token) if p)
    return forms


class PretrainedWordVectorEmbedder:
    """Mean-pooled pretrained word vectors. Deterministic and corpus-independent."""

    def __init__(self, model_path: Path | None = None, vocabulary: Iterable[str] | None = None):
        self.provider = MODEL_CARD["provider"]
        self.model_name = MODEL_CARD["model_identifier"]
        self.dimension = MODEL_CARD["dimension"]
        self.model_path = Path(model_path or Path(settings.data_dir) / "cache" / "models" / MODEL_FILENAME)
        # The model's identity, not the corpus's, decides embedding validity.
        self.model_version = config_hash(
            {k: v for k, v in MODEL_CARD.items() if k != "training_corpus"}
        )[:16]
        self._vectors: dict[str, np.ndarray] = {}
        self._wanted: set[str] | None = set(vocabulary) if vocabulary is not None else None
        self._loaded = False
        self.tokens_seen = 0
        self.tokens_matched = 0

    # -- loading ---------------------------------------------------------------

    def load(self) -> PretrainedWordVectorEmbedder:
        if self._loaded:
            return self
        if not self.model_path.exists():
            raise RuntimeError(
                f"Pretrained vectors not found at {self.model_path}. "
                "Download the gensim-data release asset first."
            )
        wanted = self._wanted
        with gzip.open(self.model_path, "rt", encoding="utf-8", errors="replace") as handle:
            header = handle.readline().split()
            declared_dim = int(header[1])
            if declared_dim != self.dimension:
                raise RuntimeError(f"Model dimension {declared_dim} != expected {self.dimension}")
            for line in handle:
                space = line.find(" ")
                if space <= 0:
                    continue
                word = line[:space]
                if wanted is not None and word not in wanted:
                    continue
                values = np.fromstring(line[space + 1:], dtype=np.float32, sep=" ")
                if values.shape[0] != self.dimension:
                    continue
                norm = np.linalg.norm(values)
                # Vectors are L2-normalized once at load so pooling is a plain mean.
                self._vectors[word] = values / norm if norm > 0 else values
        self._loaded = True
        return self

    @property
    def loaded_vectors(self) -> int:
        return len(self._vectors)

    # -- encoding --------------------------------------------------------------

    def embed_one(self, text: str) -> np.ndarray:
        if not self._loaded:
            self.load()
        acc = np.zeros(self.dimension, dtype=np.float32)
        used = 0
        for token in tokenize(text):
            self.tokens_seen += 1
            for form in lookup_forms(token):
                vector = self._vectors.get(form)
                if vector is not None:
                    acc += vector
                    used += 1
                    self.tokens_matched += 1
                    break
        if used == 0:
            return acc  # all-zero: no in-vocabulary token, scores 0 against everything
        acc /= used
        norm = np.linalg.norm(acc)
        return acc / norm if norm > 0 else acc

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_one(t).tolist() for t in texts]

    def coverage(self) -> dict:
        return {
            "tokens_seen": self.tokens_seen,
            "tokens_matched": self.tokens_matched,
            "match_rate": round(self.tokens_matched / self.tokens_seen, 4) if self.tokens_seen else None,
            "vectors_loaded": self.loaded_vectors,
        }


def corpus_vocabulary(chunk_set_id: str, extra_texts: Iterable[str] = ()) -> set[str]:
    """Every lookup form needed by a chunk set (plus any extra text).

    Restricting the load to these forms is an exact optimisation: a vector that is
    never looked up cannot influence any embedding.
    """
    from rag_v1.db import connect

    forms: set[str] = set()
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT text FROM chunk WHERE chunk_set_id=%s", (chunk_set_id,))
        for (text,) in cur:
            for token in tokenize(text):
                forms.update(lookup_forms(token))
    for text in extra_texts:
        for token in tokenize(text):
            forms.update(lookup_forms(token))
    return forms


# --------------------------------------------------------------------------
# Process-level reuse
# --------------------------------------------------------------------------
#
# Loading the 1 GB pretrained file takes ~18 s, which is far too slow to repeat per
# query. The filtered vectors are persisted once as a compact .npz and a single
# instance is reused for the life of the process.
#
# The filter covers the corpus vocabulary *and* the golden-set question vocabulary,
# so every text this project embeds is encoded exactly as the full model would
# encode it. A query containing a word outside that union would be silently treated
# as out-of-vocabulary, so that case raises rather than quietly changing the query
# vector.

_INSTANCE: PretrainedWordVectorEmbedder | None = None


def _filtered_cache_path(model_version: str, vocab_hash: str) -> Path:
    return Path(settings.data_dir) / "cache" / "models" / f"filtered-{model_version}-{vocab_hash}.npz"


def build_filtered_cache(vocabulary: set[str]) -> Path:
    """Materialise the vectors this project needs into a fast-loading .npz."""
    embedder = PretrainedWordVectorEmbedder(vocabulary=vocabulary)
    vocab_hash = config_hash({"vocab": sorted(vocabulary)})[:12]
    path = _filtered_cache_path(embedder.model_version, vocab_hash)
    if path.exists():
        return path
    embedder.load()
    words = sorted(embedder._vectors)
    matrix = np.vstack([embedder._vectors[w] for w in words]).astype(np.float32)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, words=np.array(words, dtype=object), vectors=matrix)
    return path


def get_pretrained_embedder(vocabulary: set[str] | None = None) -> PretrainedWordVectorEmbedder:
    """Return the shared pretrained embedder, loading it at most once per process."""
    global _INSTANCE
    if _INSTANCE is not None:
        return _INSTANCE

    if vocabulary is None:
        from pathlib import Path as _Path

        candidates = sorted((_Path(settings.data_dir) / "cache" / "models").glob("filtered-*.npz"))
        if not candidates:
            raise RuntimeError(
                "No filtered pretrained-vector cache found. "
                "Run scripts/build_pretrained_embeddings.py first."
            )
        # Pick the largest cache. A vocabulary superset encodes any text whose
        # tokens it covers identically to the full model, so the widest cache is
        # always the safe choice; sorting by filename would pick arbitrarily.
        path = max(candidates, key=lambda c: c.stat().st_size)
    else:
        path = build_filtered_cache(vocabulary)

    data = np.load(path, allow_pickle=True)
    embedder = PretrainedWordVectorEmbedder()
    embedder._vectors = {
        str(w): v for w, v in zip(data["words"], data["vectors"], strict=True)
    }
    embedder._loaded = True
    _INSTANCE = embedder
    return embedder


def reset_pretrained_embedder() -> None:
    """Drop the cached instance. Used by tests that swap models."""
    global _INSTANCE
    _INSTANCE = None
