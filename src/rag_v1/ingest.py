from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from psycopg.types.json import Jsonb

from rag_v1.chunking import chunk_document
from rag_v1.config import settings
from rag_v1.db import connect
from rag_v1.ids import content_hash, stable_id
from rag_v1.manifest import load_manifest
from rag_v1.parsing import parse_file


def ingest_manifest(manifest_path: Path) -> list[str]:
    manifest = load_manifest(manifest_path)
    version_ids: list[str] = []

    with connect() as conn, conn.cursor() as cur:
        for src in manifest.sources:
            doc = parse_file(src.local_path)
            src_id = stable_id("src", src.provider.lower(), src.canonical_url, length=32)
            v_hash = content_hash(doc.normalized_text)
            version_id = stable_id("ver", src_id, v_hash, length=32)
            captured_at = (
                datetime.fromisoformat(src.captured_at)
                if src.captured_at
                else datetime.now(UTC)
            )

            cur.execute(
                """
                INSERT INTO document_source(source_id, provider, canonical_url, title, authority_class, authority_rank)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (source_id) DO UPDATE SET
                  title=EXCLUDED.title,
                  authority_class=EXCLUDED.authority_class,
                  authority_rank=EXCLUDED.authority_rank
                """,
                (src_id, src.provider, src.canonical_url, src.title, src.authority_class, src.authority_rank),
            )

            cur.execute("SELECT version_id FROM document_version WHERE source_id=%s AND content_hash=%s", (src_id, v_hash))
            existing = cur.fetchone()
            if existing:
                version_ids.append(existing[0])
                continue

            # Mark previous current version superseded, while retaining it.
            cur.execute(
                "SELECT version_id FROM document_version WHERE source_id=%s AND status='current' ORDER BY captured_at DESC LIMIT 1",
                (src_id,),
            )
            prev = cur.fetchone()
            prev_id = prev[0] if prev else None
            if prev_id:
                cur.execute("UPDATE document_version SET status='superseded' WHERE version_id=%s", (prev_id,))

            validation = {"status": "pass", "checks": ["non_empty", "parsed", "chunkable"]}
            cur.execute(
                """
                INSERT INTO document_version(
                  version_id, source_id, content_hash, captured_at, status,
                  parser_name, parser_version, normalized_text, raw_path,
                  char_count, section_count, supersedes_version_id, validation, metadata
                ) VALUES (%s,%s,%s,%s,'current',%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    version_id, src_id, v_hash, captured_at,
                    doc.parser_name, doc.parser_version, doc.normalized_text, str(src.local_path),
                    len(doc.normalized_text), len(doc.sections), prev_id, Jsonb(validation), Jsonb(src.metadata),
                ),
            )

            chunks = chunk_document(
                doc,
                version_id,
                max_chars=settings.max_chunk_chars,
                min_chars=settings.min_chunk_chars,
            )
            if not chunks:
                raise RuntimeError(f"Parser produced no chunks for {src.local_path}")

            for c in chunks:
                cur.execute(
                    """
                    INSERT INTO chunk(
                      chunk_id, version_id, ordinal, section_path, chunk_type,
                      char_start, char_end, content_hash, text, metadata
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        c.chunk_id, c.version_id, c.ordinal, c.section_path, c.chunk_type,
                        c.char_start, c.char_end, c.content_hash, c.text, Jsonb(c.metadata),
                    ),
                )
            version_ids.append(version_id)

        conn.commit()
    return version_ids
