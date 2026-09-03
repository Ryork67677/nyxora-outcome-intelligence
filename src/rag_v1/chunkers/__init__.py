"""Chunker registry.

Every chunking strategy is addressable by name and carries its own version and
config hash, so a chunk set in the database always names the code that built it.
"""

from __future__ import annotations

from collections.abc import Callable

from rag_v1.chunkers import bounded, control, encoder_aligned, technical
from rag_v1.chunkers.base import ChunkerSpec
from rag_v1.types import ChunkRecord, ParsedDocument

Chunker = Callable[[ParsedDocument, str], list[ChunkRecord]]

_REGISTRY: dict[str, tuple[ChunkerSpec, Chunker]] = {
    control.SPEC.name: (control.SPEC, control.chunk),
    bounded.SPEC.name: (bounded.SPEC, bounded.chunk),
    technical.SPEC.name: (technical.SPEC, technical.chunk),
    encoder_aligned.SPEC.name: (encoder_aligned.SPEC, encoder_aligned.chunk),
}


def available() -> list[str]:
    return sorted(_REGISTRY)


def get_chunker(name: str) -> tuple[ChunkerSpec, Chunker]:
    if name not in _REGISTRY:
        raise ValueError(f"Unknown chunker {name!r}. Available: {', '.join(available())}")
    return _REGISTRY[name]


def chunk_set_id_for(name: str) -> str:
    """The chunk set a chunker writes into.

    The control's id is pinned to the value its pre-existing rows were adopted
    under by the migration; everything else derives from its config hash.
    """
    spec, _ = get_chunker(name)
    if name == control.SPEC.name:
        return control.CONTROL_CHUNK_SET_ID
    if name == encoder_aligned.SPEC.name:
        return encoder_aligned.ENCODER_ALIGNED_CHUNK_SET_ID
    return spec.chunk_set_id


__all__ = ["ChunkerSpec", "available", "chunk_set_id_for", "get_chunker"]
