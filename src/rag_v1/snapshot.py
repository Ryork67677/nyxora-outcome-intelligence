from __future__ import annotations

import subprocess

from psycopg.types.json import Jsonb

from rag_v1.config import settings
from rag_v1.db import connect
from rag_v1.ids import config_hash, stable_id
from rag_v1.parsing import PARSER_VERSION


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001 - provenance is best-effort; a snapshot must still be creatable outside a git checkout
        return None


def create_snapshot(name: str) -> str:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT version_id, content_hash FROM document_version WHERE status='current' ORDER BY version_id"
        )
        rows = cur.fetchall()
        if not rows:
            raise RuntimeError("No current document versions. Ingest a corpus first.")

        manifest_payload = [{"version_id": r[0], "content_hash": r[1]} for r in rows]
        manifest_hash = config_hash({"versions": manifest_payload})
        chunking_hash = config_hash(
            {"max_chunk_chars": settings.max_chunk_chars, "min_chunk_chars": settings.min_chunk_chars}
        )
        snapshot_id = stable_id("snap", name, manifest_hash, PARSER_VERSION, chunking_hash, length=32)

        cur.execute(
            """
            INSERT INTO corpus_snapshot(snapshot_id, name, manifest_hash, parser_version, chunking_config_hash, git_commit, metadata)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (snapshot_id) DO NOTHING
            """,
            (snapshot_id, name, manifest_hash, PARSER_VERSION, chunking_hash, _git_commit(), Jsonb({"created_by": "ragv1"})),
        )
        for version_id, _ in rows:
            cur.execute(
                "INSERT INTO corpus_snapshot_version(snapshot_id, version_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                (snapshot_id, version_id),
            )
        conn.commit()
    return snapshot_id
