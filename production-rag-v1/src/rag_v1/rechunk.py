"""Build a new chunk set over the document versions already in the database.

EXP-005 must isolate chunking, so nothing upstream of it may move: no re-fetch, no
re-parse from disk, no new document versions. This module reads each version's
stored ``normalized_text`` and re-derives its sections with the same parser used
at ingest, then applies the requested chunker. Raw provider files are not needed
and are never touched, which also means a re-chunk is reproducible from the
database alone.
"""

from __future__ import annotations

import subprocess
import time

from psycopg.types.json import Jsonb

from rag_v1.chunkers import chunk_set_id_for, get_chunker
from rag_v1.db import connect
from rag_v1.ids import config_hash, stable_id
from rag_v1.parsing import PARSER_VERSION, _sections_from_markdown
from rag_v1.types import ParsedDocument


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:  # noqa: BLE001 - provenance is best-effort
        return None


def _load_versions(cur, source_snapshot_id: str) -> list[tuple[str, str, str, str]]:
    cur.execute(
        """
        SELECT v.version_id, v.normalized_text, v.parser_name, v.parser_version
        FROM document_version v
        JOIN corpus_snapshot_version sv ON sv.version_id = v.version_id
        WHERE sv.snapshot_id = %s
        ORDER BY v.version_id
        """,
        (source_snapshot_id,),
    )
    return cur.fetchall()


def build_chunk_set(chunker_name: str, source_snapshot_id: str, replace: bool = False) -> dict:
    """Chunk every version of ``source_snapshot_id`` with ``chunker_name``."""
    spec, chunk_fn = get_chunker(chunker_name)
    chunk_set_id = chunk_set_id_for(chunker_name)
    started = time.time()

    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO chunk_set(chunk_set_id, chunker_name, chunker_version, config_hash,
                                  config, parser_version, git_commit, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (chunk_set_id) DO NOTHING
            """,
            (
                chunk_set_id, spec.name, spec.version, spec.config_hash,
                Jsonb(spec.config), PARSER_VERSION, _git_commit(),
                f"Built from {source_snapshot_id} by rag_v1.rechunk",
            ),
        )

        cur.execute("SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (chunk_set_id,))
        existing = cur.fetchone()[0]
        if existing and not replace:
            raise RuntimeError(
                f"Chunk set {chunk_set_id} already holds {existing} chunks. "
                "Pass replace=True to rebuild it."
            )
        if existing:
            cur.execute("DELETE FROM chunk WHERE chunk_set_id=%s", (chunk_set_id,))

        versions = _load_versions(cur, source_snapshot_id)
        if not versions:
            raise RuntimeError(f"No versions found for snapshot {source_snapshot_id}")

        total_chunks = 0
        links: list[tuple[str, str, str]] = []
        for version_id, normalized_text, parser_name, parser_version in versions:
            doc = ParsedDocument(
                normalized_text=normalized_text,
                sections=_sections_from_markdown(normalized_text),
                parser_name=parser_name,
                parser_version=parser_version,
            )
            records = chunk_fn(doc, version_id)
            if not records:
                raise RuntimeError(f"{chunker_name} produced no chunks for {version_id}")

            by_source_block: dict[str, str] = {}
            for record in records:
                cur.execute(
                    """
                    INSERT INTO chunk(chunk_id, chunk_set_id, version_id, ordinal, section_path,
                                      chunk_type, char_start, char_end, content_hash, text, metadata)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (chunk_id) DO NOTHING
                    """,
                    (
                        record.chunk_id, chunk_set_id, record.version_id, record.ordinal,
                        record.section_path, record.chunk_type, record.char_start, record.char_end,
                        record.content_hash, record.text, Jsonb(record.metadata),
                    ),
                )
                # Pieces of one oversized source block point back at the first
                # piece, so a fragment can be traced to the unit it came from.
                origin = record.metadata.get("split_from_block") or record.metadata.get("table_block")
                if origin:
                    parent = by_source_block.setdefault(f"{version_id}:{origin}", record.chunk_id)
                    if parent != record.chunk_id:
                        links.append((parent, record.chunk_id, "split_sibling"))
            total_chunks += len(records)

        for parent, child, relation in links:
            cur.execute(
                """
                INSERT INTO chunk_link(parent_chunk_id, child_chunk_id, relation)
                VALUES (%s,%s,%s) ON CONFLICT DO NOTHING
                """,
                (parent, child, relation),
            )
        conn.commit()

    return {
        "chunk_set_id": chunk_set_id,
        "chunker": spec.name,
        "chunker_version": spec.version,
        "config_hash": spec.config_hash,
        "versions": len(versions),
        "chunks": total_chunks,
        "split_sibling_links": len(links),
        "runtime_seconds": round(time.time() - started, 2),
    }


def create_snapshot_for_chunk_set(name: str, chunk_set_id: str, source_snapshot_id: str) -> str:
    """Freeze a snapshot over the same versions but a different chunking."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT v.version_id, v.content_hash
            FROM document_version v
            JOIN corpus_snapshot_version sv ON sv.version_id = v.version_id
            WHERE sv.snapshot_id = %s
            ORDER BY v.version_id
            """,
            (source_snapshot_id,),
        )
        rows = cur.fetchall()
        if not rows:
            raise RuntimeError(f"No versions for snapshot {source_snapshot_id}")

        cur.execute(
            """
            SELECT chunker_name, chunker_version, config_hash, config, enrichment_config
            FROM chunk_set WHERE chunk_set_id=%s
            """,
            (chunk_set_id,),
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError(f"Unknown chunk set {chunk_set_id}")
        chunker_name, chunker_version, cfg_hash, cfg, enrichment_cfg = row

        manifest_hash = config_hash({"versions": [{"version_id": r[0], "content_hash": r[1]} for r in rows]})
        # The enrichment config and the chunk set itself are part of the snapshot's
        # identity. Without them an enriched set would hash as the same "chunking"
        # as the plain set it was copied from, and two different indexes would
        # collide on one snapshot id.
        chunking_hash = config_hash(
            {
                "chunker": chunker_name,
                "version": chunker_version,
                "config": cfg,
                "enrichment": enrichment_cfg or {},
                "chunk_set_id": chunk_set_id,
            }
        )
        snapshot_id = stable_id("snap", name, manifest_hash, PARSER_VERSION, chunking_hash, length=32)

        cur.execute(
            """
            INSERT INTO corpus_snapshot(snapshot_id, name, manifest_hash, parser_version,
                                        chunking_config_hash, git_commit, chunk_set_id, metadata)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (snapshot_id) DO NOTHING
            """,
            (
                snapshot_id, name, manifest_hash, PARSER_VERSION, chunking_hash,
                _git_commit(), chunk_set_id,
                Jsonb({
                    "created_by": "rag_v1.rechunk",
                    "chunker": chunker_name,
                    "chunker_version": chunker_version,
                    "chunker_config_hash": cfg_hash,
                    "derived_from_snapshot": source_snapshot_id,
                }),
            ),
        )
        for version_id, _ in rows:
            cur.execute(
                "INSERT INTO corpus_snapshot_version(snapshot_id, version_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                (snapshot_id, version_id),
            )
        conn.commit()
    return snapshot_id


def build_enriched_chunk_set(
    source_chunk_set_id: str,
    enrichment_config=None,
    replace: bool = False,
) -> dict:
    """Clone a chunk set, changing only the indexed text.

    Chunk boundaries, section paths, character spans and canonical bodies are
    copied verbatim from ``source_chunk_set_id``. The only difference is
    ``search_text``, which carries the structural header. That is what makes the
    EXP-006 A→B and C→D comparisons a clean ablation of enrichment: any recall
    difference cannot be a chunking difference, because the chunking is identical
    row for row.
    """
    from rag_v1.enrichment import STRUCTURAL_V1, EnrichmentStats, build_context_header, enrich

    config = enrichment_config or STRUCTURAL_V1
    started = time.time()

    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT chunker_name, chunker_version, config_hash, config, parser_version
            FROM chunk_set WHERE chunk_set_id=%s
            """,
            (source_chunk_set_id,),
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError(f"Unknown source chunk set {source_chunk_set_id}")
        chunker_name, chunker_version, chunker_cfg_hash, chunker_cfg, parser_version = row

        target_id = stable_id(
            "cs", source_chunk_set_id, "enriched", config.name, config.config_hash, length=24
        )
        # chunk_set is UNIQUE on (chunker_name, chunker_version, config_hash). An
        # enriched clone shares its chunker with the set it was copied from, so the
        # enrichment has to be folded into the config hash — the indexed text is
        # part of what makes this a distinct chunk set.
        combined_cfg_hash = config_hash(
            {"chunker_config_hash": chunker_cfg_hash, "enrichment": config.as_dict()}
        )

        cur.execute(
            """
            INSERT INTO chunk_set(chunk_set_id, chunker_name, chunker_version, config_hash, config,
                                  parser_version, git_commit, notes, enrichment_config,
                                  derived_from_chunk_set_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (chunk_set_id) DO NOTHING
            """,
            (
                target_id, chunker_name, chunker_version, combined_cfg_hash, Jsonb(chunker_cfg),
                parser_version, _git_commit(),
                f"Boundaries copied from {source_chunk_set_id}; only search_text differs.",
                Jsonb(config.as_dict()), source_chunk_set_id,
            ),
        )

        cur.execute("SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (target_id,))
        existing = cur.fetchone()[0]
        if existing and not replace:
            raise RuntimeError(f"{target_id} already holds {existing} chunks; pass replace=True")
        if existing:
            cur.execute("DELETE FROM chunk WHERE chunk_set_id=%s", (target_id,))

        cur.execute(
            """
            SELECT c.chunk_id, c.version_id, c.ordinal, c.section_path, c.chunk_type,
                   c.char_start, c.char_end, c.content_hash, c.text, c.metadata,
                   s.provider, s.title
            FROM chunk c
            JOIN document_version v ON v.version_id = c.version_id
            JOIN document_source s ON s.source_id = v.source_id
            WHERE c.chunk_set_id = %s
            ORDER BY c.version_id, c.ordinal
            """,
            (source_chunk_set_id,),
        )
        rows = cur.fetchall()
        if not rows:
            raise RuntimeError(f"Source chunk set {source_chunk_set_id} is empty")

        stats = EnrichmentStats()
        for (
            src_chunk_id, version_id, ordinal, section_path, chunk_type,
            char_start, char_end, content_hash_value, text, metadata, provider, title,
        ) in rows:
            header = build_context_header(provider, title, list(section_path), config)
            stats.observe(header)
            search_text = enrich(text, header)
            new_id = stable_id("chk", target_id, src_chunk_id, length=40)
            meta = dict(metadata or {})
            meta |= {
                "enriched": bool(header),
                "enrichment": config.name,
                "source_chunk_id": src_chunk_id,
            }
            cur.execute(
                """
                INSERT INTO chunk(chunk_id, chunk_set_id, version_id, ordinal, section_path,
                                  chunk_type, char_start, char_end, content_hash, text,
                                  search_text, context_header, metadata)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (chunk_id) DO NOTHING
                """,
                (
                    new_id, target_id, version_id, ordinal, section_path, chunk_type,
                    char_start, char_end, content_hash_value, text,
                    search_text, header or None, Jsonb(meta),
                ),
            )
        conn.commit()

    return {
        "chunk_set_id": target_id,
        "derived_from": source_chunk_set_id,
        "enrichment": config.as_dict(),
        "enrichment_config_hash": config.config_hash,
        "chunks": len(rows),
        "enrichment_stats": stats.as_dict(),
        "runtime_seconds": round(time.time() - started, 2),
    }
