from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

import numpy as np

from rag_v1.config import settings
from rag_v1.db import connect
from rag_v1.ids import content_hash, stable_id


class Embedder(ABC):
    provider: str
    model_name: str
    model_version: str

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class LocalSentenceTransformerEmbedder(Embedder):
    def __init__(self, model_name: str, model_version: str = "unversioned"):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError("Install local embeddings: pip install -e '.[local-embeddings]'") from exc
        self.provider = "local"
        self.model_name = model_name
        self.model_version = model_version
        self._model = SentenceTransformer(model_name)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        arr = self._model.encode(list(texts), normalize_embeddings=True)
        return np.asarray(arr, dtype=np.float32).tolist()


class OpenAIEmbedder(Embedder):
    def __init__(self, model_name: str, model_version: str = "api"):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install OpenAI support: pip install -e '.[openai]'") from exc
        self.provider = "openai"
        self.model_name = model_name
        self.model_version = model_version
        self._client = OpenAI(api_key=settings.openai_api_key)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self.model_name, input=list(texts))
        return [item.embedding for item in response.data]


def get_embedder() -> Embedder:
    provider = settings.embedding_provider.lower()
    if provider == "local":
        return LocalSentenceTransformerEmbedder(settings.embedding_model, settings.embedding_model_version)
    if provider == "openai":
        return OpenAIEmbedder(settings.embedding_model, settings.embedding_model_version)
    if provider == "pretrained":
        # EXP-007: genuinely pretrained vectors, no corpus fitting. Loaded once per
        # process from the filtered cache; see rag_v1.embedders_pretrained.
        from rag_v1.embedders_pretrained import get_pretrained_embedder

        return get_pretrained_embedder()
    if provider == "local-lsa":
        # Offline fallback used when neither Hugging Face nor the OpenAI embedding
        # endpoint is reachable. See rag_v1.embedders_lsa for what this does and
        # does not measure.
        from rag_v1.embedders_lsa import LocalLsaEmbedder

        if not settings.lsa_fit_snapshot_id:
            raise ValueError(
                "EMBEDDING_PROVIDER=local-lsa requires LSA_FIT_SNAPSHOT_ID so query and "
                "chunk vectors come from the same fitted model."
            )
        return LocalLsaEmbedder(
            fit_snapshot_id=settings.lsa_fit_snapshot_id,
            dimension=settings.lsa_dimension,
        )
    raise ValueError(f"Unsupported embedding provider: {provider}")


def ensure_model(embedder: Embedder, dimension: int) -> str:
    model_id = stable_id(
        "emb",
        embedder.provider,
        embedder.model_name,
        embedder.model_version,
        dimension,
        length=32,
    )
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO embedding_model(model_id, provider, model_name, model_version, dimension)
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (model_id) DO NOTHING
            """,
            (model_id, embedder.provider, embedder.model_name, embedder.model_version, dimension),
        )
        conn.commit()
    return model_id


def embed_snapshot(snapshot_id: str, batch_size: int = 32) -> tuple[str, int]:
    embedder = get_embedder()
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.chunk_id, c.text, c.content_hash
            FROM chunk c
            JOIN corpus_snapshot_version sv ON sv.version_id=c.version_id
            WHERE sv.snapshot_id=%s AND c.chunk_type <> 'table_row'
            ORDER BY c.chunk_id
            """,
            (snapshot_id,),
        )
        rows = cur.fetchall()
    if not rows:
        raise RuntimeError("No chunks found for snapshot")

    probe = embedder.embed([rows[0][1]])[0]
    model_id = ensure_model(embedder, len(probe))
    inserted = 0

    with connect() as conn, conn.cursor() as cur:
        for start in range(0, len(rows), batch_size):
            batch = rows[start:start + batch_size]
            cur.execute(
                "SELECT chunk_id FROM chunk_embedding WHERE model_id=%s AND chunk_id = ANY(%s)",
                (model_id, [r[0] for r in batch]),
            )
            cached = {r[0] for r in cur.fetchall()}
            missing = [r for r in batch if r[0] not in cached]
            if not missing:
                continue
            vectors = embedder.embed([r[1] for r in missing])
            for (chunk_id, _text, chash), vec in zip(missing, vectors, strict=True):
                cur.execute(
                    """
                    INSERT INTO chunk_embedding(chunk_id, model_id, embedding, embedding_hash)
                    VALUES (%s,%s,%s,%s)
                    ON CONFLICT (chunk_id, model_id) DO NOTHING
                    """,
                    (chunk_id, model_id, vec, content_hash(str(vec))),
                )
                inserted += 1
            conn.commit()
    return model_id, inserted
