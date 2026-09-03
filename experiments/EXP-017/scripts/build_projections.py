#!/usr/bin/env python3
"""Build ps_v2_ovl_win448_s224 search projections. New tables only.

Does not write cs_v1_control chunk rows. Does not score. Does not open holdout.
Preregistration JSON must already exist and hash to the frozen value.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from psycopg.types.json import Jsonb  # noqa: E402

from rag_v1.db import connect  # noqa: E402
from rag_v1.embedders_transformer import TransformerEncoder, model_dir  # noqa: E402
from rag_v1.ids import config_hash, content_hash, stable_id  # noqa: E402
from rag_v1.systems import (  # noqa: E402
    CHUNK_SET,
    SNAPSHOT,
    TRANSFORMER_FINGERPRINT,
    TRANSFORMER_MODEL,
)

OUT_DIR = ROOT / "experiments" / "EXP-017"
PREREG_JSON = OUT_DIR / "EXP-017-preregistration.json"
PREREG_JSON_SHA = "053a6bf14df088ca9e2283bc3e8dfb0769848a48c54c51a77fbe045795a80cc6"
PROJECTION_SET_ID = "ps_v2_ovl_win448_s224"
WINDOW = 448
STRIDE = 224
BATCH = 64


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_offset_tokenizer():
    from tokenizers import Tokenizer

    path = model_dir() / "tokenizer.json"
    tok = Tokenizer.from_file(str(path))
    tok.no_truncation()
    tok.no_padding()
    return tok


def window_starts(n_tokens: int, window: int = WINDOW, stride: int = STRIDE) -> list[int]:
    if n_tokens <= 0:
        return []
    if n_tokens <= window:
        return [0]
    starts: list[int] = []
    start = 0
    while start + window < n_tokens:
        starts.append(start)
        start += stride
    last = n_tokens - window
    if last not in starts:
        starts.append(last)
    return starts


def token_span_to_chars(offsets: list[tuple[int, int]], start: int, end: int) -> tuple[int, int] | None:
    if start >= end:
        return None
    lo, _ = offsets[start]
    _, hi = offsets[end - 1]
    if hi <= lo:
        return None
    return lo, hi


def covering_chunks(chunks: list[dict], cs: int, ce: int) -> list[dict]:
    return [ch for ch in chunks if ch["char_start"] < ce and ch["char_end"] > cs]


def section_paths_of(covering: list[dict]) -> list[str]:
    seen: list[str] = []
    keys: set[tuple] = set()
    for ch in covering:
        key = tuple(ch["section_path"])
        if key in keys:
            continue
        keys.add(key)
        seen.append(json.dumps(list(ch["section_path"]), ensure_ascii=False, separators=(",", ":")))
    return seen


def projection_config() -> dict:
    return {
        "projection_set_id": PROJECTION_SET_ID,
        "derived_from_chunk_set_id": CHUNK_SET,
        "snapshot_id": SNAPSHOT,
        "tokenizer": "sentence-transformers/all-MiniLM-L6-v2",
        "tokenizer_fingerprint": TRANSFORMER_FINGERPRINT,
        "add_special_tokens": False,
        "do_not_trust_tokenizer_json_max_128": True,
        "window_tokens": WINDOW,
        "stride_tokens": STRIDE,
        "right_align_last_window": True,
        "exact_source_substrings": True,
        "no_heading_prefix": True,
        "covering": "overlap>=1 char, ordinal ASC",
    }


DDL = """
CREATE TABLE IF NOT EXISTS search_projection_set (
  projection_set_id TEXT PRIMARY KEY,
  derived_from_chunk_set_id TEXT NOT NULL,
  snapshot_id TEXT NOT NULL,
  tokenizer_fingerprint TEXT NOT NULL,
  window_tokens INT NOT NULL,
  stride_tokens INT NOT NULL,
  config JSONB NOT NULL,
  config_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS search_projection (
  projection_id TEXT PRIMARY KEY,
  projection_set_id TEXT NOT NULL REFERENCES search_projection_set(projection_set_id),
  version_id TEXT NOT NULL,
  ordinal INT NOT NULL,
  char_start INT NOT NULL,
  char_end INT NOT NULL,
  text TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  covering_chunk_ids TEXT[] NOT NULL,
  section_paths TEXT[] NOT NULL,
  search_vector TSVECTOR GENERATED ALWAYS AS (to_tsvector('simple', text)) STORED,
  UNIQUE(projection_set_id, version_id, ordinal),
  UNIQUE(projection_set_id, version_id, char_start, char_end),
  CHECK (char_end > char_start),
  CHECK (projection_id LIKE 'prj_%')
);

CREATE TABLE IF NOT EXISTS search_projection_embedding (
  projection_id TEXT NOT NULL REFERENCES search_projection(projection_id),
  model_id TEXT NOT NULL,
  embedding VECTOR,
  embedding_hash TEXT,
  content_hash TEXT,
  model_fingerprint TEXT,
  PRIMARY KEY(projection_id, model_id)
);
"""


def ensure_tables() -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(DDL)
        conn.commit()


def upsert_set_row(cfg: dict, cfg_hash: str) -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO search_projection_set(
              projection_set_id, derived_from_chunk_set_id, snapshot_id,
              tokenizer_fingerprint, window_tokens, stride_tokens, config, config_hash
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (projection_set_id) DO UPDATE SET
              derived_from_chunk_set_id = EXCLUDED.derived_from_chunk_set_id,
              snapshot_id = EXCLUDED.snapshot_id,
              tokenizer_fingerprint = EXCLUDED.tokenizer_fingerprint,
              window_tokens = EXCLUDED.window_tokens,
              stride_tokens = EXCLUDED.stride_tokens,
              config = EXCLUDED.config,
              config_hash = EXCLUDED.config_hash
            """,
            (
                PROJECTION_SET_ID,
                CHUNK_SET,
                SNAPSHOT,
                TRANSFORMER_FINGERPRINT,
                WINDOW,
                STRIDE,
                Jsonb(cfg),
                cfg_hash,
            ),
        )
        conn.commit()


def load_versions() -> list[tuple[str, str, list[dict]]]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT dv.version_id, dv.normalized_text
            FROM document_version dv
            JOIN corpus_snapshot_version sv ON sv.version_id = dv.version_id
            WHERE sv.snapshot_id = %s
            ORDER BY dv.version_id
            """,
            (SNAPSHOT,),
        )
        versions = [(r[0], r[1]) for r in cur.fetchall()]
        cur.execute(
            """
            SELECT version_id, chunk_id, ordinal, char_start, char_end, section_path, content_hash
            FROM chunk
            WHERE chunk_set_id = %s
            ORDER BY version_id, ordinal ASC
            """,
            (CHUNK_SET,),
        )
        by_vid: dict[str, list[dict]] = {vid: [] for vid, _ in versions}
        for vid, cid, ordinal, cs, ce, spath, chash in cur.fetchall():
            by_vid.setdefault(vid, []).append(
                {
                    "chunk_id": cid,
                    "ordinal": ordinal,
                    "char_start": cs,
                    "char_end": ce,
                    "section_path": list(spath),
                    "content_hash": chash,
                }
            )
    return [(vid, text, by_vid.get(vid, [])) for vid, text in versions]


def existing_projection_ids() -> set[str]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT projection_id FROM search_projection WHERE projection_set_id=%s",
            (PROJECTION_SET_ID,),
        )
        return {r[0] for r in cur.fetchall()}


def build_windows(tok, versions) -> tuple[list[tuple], dict]:
    rows: list[tuple] = []
    stats = {
        "n_versions": len(versions),
        "n_windows_considered": 0,
        "n_skipped_exact_single_canonical": 0,
        "n_skipped_duplicate_span": 0,
        "n_skipped_empty_span": 0,
        "n_projections": 0,
        "n_covering_empty": 0,
        "n_covering_multi": 0,
        "max_windows_in_one_doc": 0,
        "max_windows_version_id": None,
    }
    seen_ids: set[str] = set()
    t0 = time.time()
    for vi, (version_id, normalized, chunks) in enumerate(versions, start=1):
        if not chunks:
            continue
        src_lo = min(ch["char_start"] for ch in chunks)
        src_hi = max(ch["char_end"] for ch in chunks)
        text = normalized[src_lo:src_hi]
        enc = tok.encode(text, add_special_tokens=False)
        ids = enc.ids
        offsets = enc.offsets
        T = len(ids)
        starts = window_starts(T)
        ordinal = 0
        seen_spans: set[tuple[int, int]] = set()
        n_this = 0
        for st in starts:
            en = min(st + WINDOW, T)
            stats["n_windows_considered"] += 1
            span = token_span_to_chars(offsets, st, en)
            if span is None:
                stats["n_skipped_empty_span"] += 1
                continue
            local_start, local_end = span
            char_start = src_lo + local_start
            char_end = src_lo + local_end
            if char_end <= char_start:
                stats["n_skipped_empty_span"] += 1
                continue
            if (char_start, char_end) in seen_spans:
                stats["n_skipped_duplicate_span"] += 1
                continue
            payload = normalized[char_start:char_end]
            covering = covering_chunks(chunks, char_start, char_end)
            if (
                len(covering) == 1
                and covering[0]["char_start"] == char_start
                and covering[0]["char_end"] == char_end
            ):
                stats["n_skipped_exact_single_canonical"] += 1
                continue
            seen_spans.add((char_start, char_end))
            chash = content_hash(payload)
            pid = stable_id("prj", version_id, char_start, char_end, chash, length=40)
            if pid in seen_ids:
                stats["n_skipped_duplicate_span"] += 1
                continue
            seen_ids.add(pid)
            cover_ids = [ch["chunk_id"] for ch in covering]
            if not cover_ids:
                stats["n_covering_empty"] += 1
            if len(cover_ids) > 1:
                stats["n_covering_multi"] += 1
            rows.append(
                (
                    pid,
                    PROJECTION_SET_ID,
                    version_id,
                    ordinal,
                    char_start,
                    char_end,
                    payload,
                    chash,
                    cover_ids,
                    section_paths_of(covering),
                )
            )
            ordinal += 1
            n_this += 1
        stats["n_projections"] += n_this
        if n_this > (stats["max_windows_in_one_doc"] or 0):
            stats["max_windows_in_one_doc"] = n_this
            stats["max_windows_version_id"] = version_id
        if vi % 10 == 0 or n_this > 500:
            elapsed = time.time() - t0
            print(
                f"  windowed {vi}/{len(versions)} versions  "
                f"projections={stats['n_projections']}  last={n_this}  {elapsed:.1f}s",
                flush=True,
            )
    stats["window_seconds"] = round(time.time() - t0, 1)
    return rows, stats


def insert_projections(rows: list[tuple]) -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM search_projection_embedding pe "
            "USING search_projection sp "
            "WHERE pe.projection_id = sp.projection_id AND sp.projection_set_id=%s",
            (PROJECTION_SET_ID,),
        )
        cur.execute(
            "DELETE FROM search_projection WHERE projection_set_id=%s",
            (PROJECTION_SET_ID,),
        )
        sql = """
            INSERT INTO search_projection(
              projection_id, projection_set_id, version_id, ordinal,
              char_start, char_end, text, content_hash, covering_chunk_ids, section_paths
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        for start in range(0, len(rows), 200):
            cur.executemany(sql, rows[start:start + 200])
        cur.execute(
            "CREATE INDEX IF NOT EXISTS search_projection_search_vector_gin "
            "ON search_projection USING GIN (search_vector)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS search_projection_set_vid_idx "
            "ON search_projection (projection_set_id, version_id)"
        )
        conn.commit()


def embed_projections(encoder: TransformerEncoder, model_id: str) -> dict:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT projection_id, text, content_hash
            FROM search_projection
            WHERE projection_set_id=%s
            ORDER BY projection_id
            """,
            (PROJECTION_SET_ID,),
        )
        rows = cur.fetchall()
        cur.execute(
            """
            SELECT pe.projection_id, pe.content_hash
            FROM search_projection_embedding pe
            JOIN search_projection sp ON sp.projection_id = pe.projection_id
            WHERE pe.model_id=%s AND sp.projection_set_id=%s
            """,
            (model_id, PROJECTION_SET_ID),
        )
        cached = {cid: chash for cid, chash in cur.fetchall()}

    hits = misses = zero_vectors = 0
    embed_started = time.time()
    with connect() as conn, conn.cursor() as cur:
        for start in range(0, len(rows), BATCH):
            batch = rows[start:start + BATCH]
            pending = [(pid, text, chash) for pid, text, chash in batch if cached.get(pid) != chash]
            hits += len(batch) - len(pending)
            if pending:
                vectors = encoder.embed_array([t for _p, t, _h in pending], batch_size=BATCH)
                zero_vectors += int(sum(1 for v in vectors if not v.any()))
                for (pid, _text, chash), vec in zip(pending, vectors, strict=True):
                    cur.execute(
                        """
                        INSERT INTO search_projection_embedding(
                          projection_id, model_id, embedding, embedding_hash,
                          content_hash, model_fingerprint
                        ) VALUES (%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (projection_id, model_id) DO UPDATE SET
                          embedding = EXCLUDED.embedding,
                          embedding_hash = EXCLUDED.embedding_hash,
                          content_hash = EXCLUDED.content_hash,
                          model_fingerprint = EXCLUDED.model_fingerprint
                        """,
                        (
                            pid,
                            model_id,
                            vec.tolist(),
                            content_hash(vec.tobytes().hex()),
                            chash,
                            encoder.model_version,
                        ),
                    )
                    misses += 1
                conn.commit()
            done = start + len(batch)
            if (start // BATCH) % 10 == 0 or done == len(rows):
                rate = done / max(time.time() - embed_started, 1e-9)
                print(f"  embed {done}/{len(rows)}  {rate:.1f}/s  misses={misses}", flush=True)

        cur.execute(
            """
            SELECT count(*), pg_size_pretty(COALESCE(sum(pg_column_size(pe.embedding)),0)::bigint),
                   min(pe.model_fingerprint), max(pe.model_fingerprint)
            FROM search_projection_embedding pe
            JOIN search_projection sp ON sp.projection_id = pe.projection_id
            WHERE pe.model_id=%s AND sp.projection_set_id=%s
            """,
            (model_id, PROJECTION_SET_ID),
        )
        stored, size, fp_min, fp_max = cur.fetchone()
        cur.execute("ANALYZE search_projection")
        cur.execute("ANALYZE search_projection_embedding")
        conn.commit()

    return {
        "n_rows": len(rows),
        "embeddings_stored": stored,
        "cache_hits": hits,
        "cache_misses": misses,
        "all_zero_embeddings": zero_vectors,
        "storage_size": size,
        "fingerprint_min": fp_min,
        "fingerprint_max": fp_max,
        "embed_seconds": round(time.time() - embed_started, 1),
        "truncation": encoder.truncation_stats(),
    }


def main() -> int:
    started = time.time()
    if not PREREG_JSON.exists():
        raise SystemExit("STOP: preregistration JSON missing; do not build")
    got = _sha(PREREG_JSON)
    if got != PREREG_JSON_SHA:
        raise SystemExit(f"STOP: prereg json sha {got} != frozen {PREREG_JSON_SHA}")

    encoder = TransformerEncoder(max_seq=512).load()
    if encoder.model_version != TRANSFORMER_FINGERPRINT:
        raise SystemExit(
            f"STOP: encoder fingerprint {encoder.model_version} != {TRANSFORMER_FINGERPRINT}"
        )
    model_id = stable_id(
        "emb", encoder.provider, encoder.model_name, encoder.model_version,
        encoder.dimension, length=32,
    )
    if model_id != TRANSFORMER_MODEL:
        raise SystemExit(f"STOP: model_id {model_id} != {TRANSFORMER_MODEL}")

    cfg = projection_config()
    cfg_hash = config_hash(cfg)
    print("projection config_hash", cfg_hash, flush=True)
    ensure_tables()
    upsert_set_row(cfg, cfg_hash)

    tok = load_offset_tokenizer()
    # Prove tokenizer.json default 128 is disabled.
    probe = "alpha " * 200
    enc = tok.encode(probe, add_special_tokens=False)
    if len(enc.ids) <= 128:
        raise SystemExit(f"STOP: offset tokenizer still truncating: {len(enc.ids)} tokens")
    print(f"offset tokenizer ok: probe tokens={len(enc.ids)} (no 128 cap)", flush=True)

    versions = load_versions()
    print(f"loaded {len(versions)} versions", flush=True)
    rows, stats = build_windows(tok, versions)
    print(json.dumps(stats, indent=2), flush=True)
    insert_projections(rows)
    print(f"inserted {len(rows)} projections", flush=True)
    emb = embed_projections(encoder, model_id)
    print(json.dumps(emb, indent=2), flush=True)

    payload = {
        "experiment_id": "EXP-017",
        "projection_set_id": PROJECTION_SET_ID,
        "preregistration_json_sha256": PREREG_JSON_SHA,
        "projection_config_hash": cfg_hash,
        "model_id": model_id,
        "model_fingerprint": encoder.model_version,
        "window_stats": stats,
        "embedding": emb,
        "total_seconds": round(time.time() - started, 1),
    }
    out = OUT_DIR / "EXP-017-projection-build.json"
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    print("wrote", out, "total_s", payload["total_seconds"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
