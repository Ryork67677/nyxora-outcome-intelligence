#!/usr/bin/env python3
"""Embed the frozen control chunks with the preregistered EXP-009 transformer.

Storage reuses the repository's model-versioned embedding table; nothing is added
to the canonical chunk table and no existing model's vectors are touched. Vectors
are cached by (model_id, content_hash), so an unchanged chunk under an unchanged
encoder is never re-embedded.

    python scripts/build_transformer_embeddings.py --chunk-set cs_v1_control
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from psycopg.types.json import Jsonb

from rag_v1.db import connect
from rag_v1.embedders_transformer import MODEL_CARD, TransformerEncoder
from rag_v1.ids import content_hash, stable_id


def ensure_model_row(encoder: TransformerEncoder) -> str:
    model_id = stable_id(
        "emb", encoder.provider, encoder.model_name, encoder.model_version,
        encoder.dimension, length=32,
    )
    card = {**MODEL_CARD, "max_seq_length": encoder.max_seq}
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO embedding_model(model_id, provider, model_name, model_version,
                                        dimension, model_card)
            VALUES (%s,%s,%s,%s,%s,%s)
            ON CONFLICT (model_id) DO UPDATE SET model_card = EXCLUDED.model_card
            """,
            (model_id, encoder.provider, encoder.model_name, encoder.model_version,
             encoder.dimension, Jsonb(card)),
        )
        conn.commit()
    return model_id


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunk-set", default="cs_v1_control")
    parser.add_argument("--max-seq", type=int, default=256)
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--out", default="experiments/EXP-009/embedding-build.json")
    args = parser.parse_args()

    started = time.time()
    # Embeds coalesce(search_text, text): the representation the chunker intends to
    # be searched. Every chunk set before EXP-010 leaves search_text NULL, so this
    # is byte-identical to embedding text for them and the EXP-009 cells reproduce
    # exactly; only EXP-010's carryover chunks differ.
    encoder = TransformerEncoder(max_seq=args.max_seq).load()
    model_id = ensure_model_row(encoder)

    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT chunk_id, coalesce(search_text, text), content_hash
            FROM chunk WHERE chunk_set_id=%s ORDER BY chunk_id
            """,
            (args.chunk_set,),
        )
        rows = cur.fetchall()
        cur.execute(
            "SELECT chunk_id, content_hash FROM chunk_embedding WHERE model_id=%s", (model_id,)
        )
        cached = {cid: chash for cid, chash in cur.fetchall()}

        hits = misses = 0
        # Counted in Python, not SQL: chunk_embedding holds several models with
        # different dimensions, so a SQL-side vector comparison would compare a
        # 384-dim probe against 300-dim rows and fail (the EXP-008 defect).
        zero_vectors = 0
        embed_started = time.time()
        for start in range(0, len(rows), args.batch):
            batch = rows[start:start + args.batch]
            pending = [(cid, text, chash) for cid, text, chash in batch
                       if cached.get(cid) != chash]
            hits += len(batch) - len(pending)
            if not pending:
                continue
            vectors = encoder.embed_array([t for _c, t, _h in pending], batch_size=args.batch)
            zero_vectors += int(sum(1 for v in vectors if not v.any()))
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
                     chash, encoder.model_version),
                )
                misses += 1
            conn.commit()
            if (start // args.batch) % 25 == 0:
                done = start + len(batch)
                rate = done / max(time.time() - embed_started, 1e-9)
                print(f"  {done}/{len(rows)} chunks  {rate:.0f}/s", flush=True)
        embed_seconds = time.time() - embed_started

        cur.execute(
            "SELECT count(*), pg_size_pretty(sum(pg_column_size(embedding))::bigint) "
            "FROM chunk_embedding WHERE model_id=%s",
            (model_id,),
        )
        stored, size = cur.fetchone()

    lengths = [len(t) for _c, t, _h in rows]
    payload = {
        "chunk_set_id": args.chunk_set,
        "model_id": model_id,
        "model_card": {**MODEL_CARD, "max_seq_length": encoder.max_seq},
        "model_version_fingerprint": encoder.model_version,
        "chunks": len(rows),
        "embeddings_stored": stored,
        "cache_hits": hits,
        "cache_misses": misses,
        "all_zero_embeddings": zero_vectors,
        # The confound declared in the preregistration, measured rather than assumed.
        "truncation": encoder.truncation_stats(),
        "chunk_char_length": {
            "mean": round(statistics.mean(lengths), 1),
            "median": statistics.median(lengths),
            "max": max(lengths),
        },
        "storage_size": size,
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
