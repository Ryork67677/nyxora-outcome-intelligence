"""chunker_v1_control — the V1 chunking, preserved exactly as shipped.

This module deliberately adds no behaviour. It wraps ``rag_v1.chunking.chunk_document``
unmodified so that EXP-000 through EXP-003 stay reproducible while EXP-005 measures
alternatives beside them. If this file ever starts changing chunk boundaries, the
V1 results stop being a control and the whole comparison is void.
"""

from __future__ import annotations

from rag_v1.chunkers.base import ChunkerSpec
from rag_v1.chunking import chunk_document
from rag_v1.types import ChunkRecord, ParsedDocument

SPEC = ChunkerSpec(
    name="chunker_v1_control",
    version="1.0",
    config={
        "max_chunk_chars": 3500,
        "min_chunk_chars": 200,
        # The defect EXP-005 exists to test: the ceiling is a grouping target
        # applied to runs of paragraphs, and a single oversized paragraph, table
        # or code fence bypasses it entirely.
        "enforces_hard_limit": False,
    },
)

# The V1 corpus was ingested before chunk sets existed and its rows were adopted
# under this fixed id by sql/002_chunk_sets.sql. Re-deriving it from the config
# hash would not match those rows, so the control's id is pinned.
CONTROL_CHUNK_SET_ID = "cs_v1_control"


def chunk(doc: ParsedDocument, version_id: str) -> list[ChunkRecord]:
    return chunk_document(
        doc,
        version_id,
        max_chars=SPEC.config["max_chunk_chars"],
        min_chars=SPEC.config["min_chunk_chars"],
    )
