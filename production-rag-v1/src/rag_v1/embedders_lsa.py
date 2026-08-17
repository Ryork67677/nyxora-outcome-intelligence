"""Offline dense embedder: TF-IDF followed by truncated SVD (latent semantic analysis).

Why this exists
---------------
The configured V1 dense baseline is a sentence-transformer checkpoint pulled from
Hugging Face, and the OpenAI embedding endpoint is the documented alternative. In
the environment this corpus was built in, neither host is reachable — the network
egress allowlist rejects ``huggingface.co`` and ``api.openai.com`` outright, and
no generation or embedding credential is present. Running EXP-001 through EXP-003
with no dense retriever at all would have left the fusion experiments unmeasurable.

This embedder is therefore a *substitute*, not an equivalent. LSA captures term
co-occurrence structure, so it does generalize past exact token overlap, but it
has no pretrained semantic knowledge and no subword handling. Every dense, hybrid
and RRF number produced with it should be read as a **lower bound** on what a
neural embedding model would achieve, and none of them supports a conclusion of
the form "dense retrieval does not help on this corpus".

Properties that keep it honest as a benchmark component:

* Deterministic. A fixed seed and a fixed fit corpus give identical vectors.
* Fit only on chunk text from the corpus snapshot. Golden-set questions are never
  part of the fit, so there is no evaluation leakage.
* Identified like any other model. The fit corpus and hyperparameters are hashed
  into ``model_version``, so vectors from different fits can never be silently
  mixed inside ``chunk_embedding``.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from rag_v1.config import settings
from rag_v1.ids import config_hash


class LocalLsaEmbedder:
    """TF-IDF + SVD embedder fitted on one corpus snapshot and cached on disk."""

    def __init__(
        self,
        fit_snapshot_id: str,
        dimension: int = 384,
        min_df: int = 2,
        max_df: float = 0.5,
        seed: int = 0,
    ):
        self.provider = "local-lsa"
        self.model_name = f"tfidf-svd-{dimension}"
        self.fit_snapshot_id = fit_snapshot_id
        self.dimension = dimension
        self.min_df = min_df
        self.max_df = max_df
        self.seed = seed

        import sklearn

        self._config = {
            "kind": "tfidf-svd",
            "fit_snapshot_id": fit_snapshot_id,
            "dimension": dimension,
            "min_df": min_df,
            "max_df": max_df,
            "seed": seed,
            "sklearn": sklearn.__version__,
        }
        # A different fit corpus or hyperparameter set is a different model, and
        # embedding identity in the schema is (chunk_id, model_id).
        self.model_version = config_hash(self._config)[:16]
        self._pipeline = None

    @property
    def _cache_path(self) -> Path:
        return Path(settings.data_dir) / "cache" / "embedders" / f"lsa-{self.model_version}.joblib"

    def _fit_texts(self) -> list[str]:
        from rag_v1.db import connect

        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.text
                FROM chunk c
                JOIN corpus_snapshot_version sv ON sv.version_id = c.version_id
                WHERE sv.snapshot_id = %s
                ORDER BY c.chunk_id
                """,
                (self.fit_snapshot_id,),
            )
            return [row[0] for row in cur.fetchall()]

    def _build(self):
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import Normalizer

        vectorizer = TfidfVectorizer(
            lowercase=True,
            # Keep identifier punctuation inside a token so `request_too_large`
            # and `max_turns` stay single features instead of being shredded.
            token_pattern=r"(?u)\b[\w.\-]+\b",
            min_df=self.min_df,
            max_df=self.max_df,
            sublinear_tf=True,
            strip_accents="unicode",
        )
        svd = TruncatedSVD(n_components=self.dimension, random_state=self.seed)
        return make_pipeline(vectorizer, svd, Normalizer(copy=False))

    def _ensure_fitted(self):
        if self._pipeline is not None:
            return
        import joblib

        cache = self._cache_path
        if cache.exists():
            self._pipeline = joblib.load(cache)
            return

        texts = self._fit_texts()
        if not texts:
            raise RuntimeError(f"No chunks to fit on for snapshot {self.fit_snapshot_id}")
        n_features_cap = min(self.dimension, max(2, len(texts) - 1))
        if n_features_cap != self.dimension:
            raise RuntimeError(
                f"Corpus too small to fit {self.dimension} components ({len(texts)} chunks)"
            )
        pipeline = self._build()
        pipeline.fit(texts)
        cache.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(pipeline, cache)
        self._pipeline = pipeline

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self._ensure_fitted()
        vectors = self._pipeline.transform(list(texts))
        return np.asarray(vectors, dtype=np.float32).tolist()

    def explained_variance(self) -> float:
        self._ensure_fitted()
        return float(self._pipeline.named_steps["truncatedsvd"].explained_variance_ratio_.sum())
