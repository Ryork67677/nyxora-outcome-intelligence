#!/usr/bin/env python3
"""Embed the frozen control chunks with the preregistered pretrained model.

Storage uses the repository's existing model-versioned embedding table; nothing is
added to the canonical chunk table. Vectors are cached by (model_id, content_hash),
so an unchanged chunk under an unchanged model is never re-embedded.

    python scripts/build_pretrained_embeddings.py --chunk-set cs_v1_control
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from psycopg.types.json import Jsonb

from rag_v1.db import connect
from rag_v1.embedders_pretrained import (
    MODEL_CARD,
    PretrainedWordVectorEmbedder,
    corpus_vocabulary,
)
from rag_v1.evals.io import load_cases
from rag_v1.ids import content_hash, stable_id


def ensure_model_row(embedder: PretrainedWordVectorEmbedder) -> str:
    model_id = stable_id(
        "emb", embedder.provider, embedder.model_name, embedder.model_version,
        embedder.dimension, length=32,
    )
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO embedding_model(model_id, provider, model_name, model_version,
                                        dimension, model_card)
            VALUES (%s,%s,%s,%s,%s,%s)
            ON CONFLICT (model_id) DO UPDATE SET model_card = EXCLUDED.model_card
            """,
            (model_id, embedder.provider, embedder.model_name, embedder.model_version,
             embedder.dimension, Jsonb(MODEL_CARD)),
        )
        conn.commit()
    return model_id


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunk-set", default="cs_v1_control")
    parser.add_argument("--golden", default="evals/golden/v1.jsonl")
    parser.add_argument("--batch", type=int, default=512)
    parser.add_argument("--out", default="experiments/EXP-007/embedding-build.json")
    args = parser.parse_args()

    started = time.time()

    # The evaluation questions contribute only to *which* pretrained vectors are
    # loaded into memory, never to any vector's value and never to a document
    # embedding. Restricting the load is an exact optimisation.
    questions = [c.question for c in load_cases(Path(args.golden))]
    vocab_started = time.time()
    vocab = corpus_vocabulary(args.chunk_set, extra_texts=questions)
    vocab_seconds = time.time() - vocab_started

    embedder = PretrainedWordVectorEmbedder(vocabulary=vocab)
    load_started = time.time()
    embedder.load()
    load_seconds = time.time() - load_started

    model_id = ensure_model_row(embedder)

    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT chunk_id, text, content_hash FROM chunk WHERE chunk_set_id=%s ORDER BY chunk_id",
            (args.chunk_set,),
        )
        rows = cur.fetchall()

        cur.execute(
            "SELECT chunk_id, content_hash FROM chunk_embedding WHERE model_id=%s", (model_id,)
        )
        cached = {cid: chash for cid, chash in cur.fetchall()}

        hits = misses = zero_vectors = 0
        embed_started = time.time()
        for start in range(0, len(rows), args.batch):
            batch = rows[start:start + args.batch]
            pending = []
            for chunk_id, text, chash in batch:
                if cached.get(chunk_id) == chash:
                    hits += 1
                    continue
                pending.append((chunk_id, text, chash))
            if not pending:
                continue
            vectors = [embedder.embed_one(t) for _cid, t, _h in pending]
            zero_vectors += sum(1 for v in vectors if not v.any())
            for (chunk_id, _text, chash), vec in zip(pending, vectors, strict=True):
                cur.execute(
                    """
                    INSERT INTO chunk_embedding(chunk_id, model_id, embedding, embedding_hash,
                                                content_hash, model_fingerprint)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (chunk_id, model_id) DO UPDATE SET
                      embedding = EXCLUDED.embedding,
                      embedding_hash = EXCLUDED.embedding_hash,
                      content_hash = EXCLUDED.content_hash,
                      model_fingerprint = EXCLUDED.model_fingerprint
                    """,
                    (chunk_id, model_id, vec.tolist(), content_hash(vec.tobytes().hex()),
                     chash, embedder.model_version),
                )
                misses += 1
            conn.commit()
        embed_seconds = time.time() - embed_started

        cur.execute(
            "SELECT count(*), pg_size_pretty(sum(pg_column_size(embedding))::bigint) FROM chunk_embedding WHERE model_id=%s",
            (model_id,),
        )
        stored, size = cur.fetchone()

        # Counted while encoding: a chunk with no in-vocabulary token yields an
        # all-zero vector and can never be retrieved by cosine similarity.
        all_zero = zero_vectors

    payload = {
        "chunk_set_id": args.chunk_set,
        "model_id": model_id,
        "model_card": MODEL_CARD,
        "model_version_fingerprint": embedder.model_version,
        "chunks": len(rows),
        "embeddings_stored": stored,
        "cache_hits": hits,
        "cache_misses": misses,
        "cache_hit_rate": round(hits / len(rows), 4) if rows else None,
        "all_zero_embeddings": all_zero,
        "vocabulary_forms_requested": len(vocab),
        "pretrained_vectors_loaded": embedder.loaded_vectors,
        "token_coverage": embedder.coverage(),
        "storage_size": size,
        "vocabulary_seconds": round(vocab_seconds, 1),
        "model_load_seconds": round(load_seconds, 1),
        "embed_seconds": round(embed_seconds, 1),
        "total_seconds": round(time.time() - started, 1),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "model_card"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
