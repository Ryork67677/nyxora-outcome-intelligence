"""chunker_v2_bounded — structure-aware chunking with a ceiling that is real.

What changes relative to the control, and why
---------------------------------------------
The control has two distinct defects, and V2 addresses both:

1. **The ceiling is not enforced.** ``max_chunk_chars`` is only a grouping target
   for runs of paragraphs. A single oversized paragraph, markdown table or fenced
   code block is emitted whole, which is how a 12,341-character chunk exists under
   a 3,500-character budget. V2 enforces ``hard_max_chars`` on every emitted
   chunk, with type-appropriate splitting.

2. **The grouping target is too coarse for reference documentation.** The known
   failing case is a 57-character answer inside a 3,449-character chunk — already
   *under* the control's budget, so enforcement alone would not have rescued it.
   V2 groups to a smaller target so an answer-bearing sentence is a larger share
   of the chunk that carries it.

Because V2 changes both the ceiling and the target, it is **not** a single-variable
ablation of the control. It tests the chunking hypothesis as a whole, and the
report says so rather than attributing any movement to one parameter.

Where the sizes come from
-------------------------
Measured from the corpus itself, never from the golden set:

* atomic prose blocks: median 38, p95 242, p99 618 characters
* fenced code blocks:  median 465, p90 1,583, p95 2,379
* table runs:          median 98, p90 1,771, p95 2,704

``target_max_chars = 1200`` sits well above the 99th percentile of atomic prose,
so related short blocks still group together, while a substantive paragraph is
rarely diluted. ``hard_max_chars = 2000`` sits above the 90th percentile of both
code blocks and table runs, so the large majority of those stay intact and only
the tail is split.

Boundary priority: section, then paragraph or list group, then table row group,
then code logical unit, then sentence, and a hard split only as a last resort.
"""

from __future__ import annotations

from rag_v1.chunkers.base import (
    Block,
    ChunkerSpec,
    code_language,
    make_chunk,
    segment_blocks,
    split_code,
    split_prose,
    split_table,
    table_header,
)
from rag_v1.types import ChunkRecord, ParsedDocument

SPEC = ChunkerSpec(
    name="chunker_v2_bounded",
    version="2.0",
    config={
        "target_max_chars": 1200,
        "hard_max_chars": 2000,
        "min_merge_chars": 120,
        "enforces_hard_limit": True,
        "size_basis": "corpus block-size percentiles, not the golden set",
    },
)

TARGET = SPEC.config["target_max_chars"]
HARD_MAX = SPEC.config["hard_max_chars"]
MIN_MERGE = SPEC.config["min_merge_chars"]


def _bound_block(doc: ParsedDocument, block: Block) -> list[tuple[int, int]]:
    """Split one structural block so no piece exceeds the hard ceiling."""
    text = doc.normalized_text[block.start:block.end]
    if block.kind == "code":
        return split_code(text, block.start, HARD_MAX)
    if block.kind == "table":
        return split_table(text, block.start, HARD_MAX)
    return split_prose(text, block.start, HARD_MAX)


def chunk(doc: ParsedDocument, version_id: str, spec: ChunkerSpec = SPEC) -> list[ChunkRecord]:
    chunks: list[ChunkRecord] = []
    ordinal = 0

    for section in doc.sections:
        blocks = segment_blocks(
            doc.normalized_text[section.char_start:section.char_end], section.char_start
        )

        # Bound every block first, then group the small ones back up to target.
        units: list[tuple[str, int, int, dict]] = []
        for block in blocks:
            pieces = _bound_block(doc, block)
            multi = len(pieces) > 1
            header = ""
            if block.kind == "table" and multi:
                header = table_header(doc.normalized_text[block.start:block.end])
            for index, (start, end) in enumerate(pieces):
                meta: dict = {"block_kind": block.kind}
                if multi:
                    # Split pieces stay identifiable as parts of one source block.
                    meta |= {
                        "split_from_block": f"{block.start}:{block.end}",
                        "part_index": index,
                        "part_count": len(pieces),
                    }
                    if block.kind == "code":
                        meta["code_language"] = code_language(
                            doc.normalized_text[block.start:block.end]
                        )
                    if header:
                        meta["table_header"] = header
                units.append((block.kind, start, end, meta))

        for kind, start, end, meta in _group_small_units(units):
            record = make_chunk(
                spec=spec,
                doc=doc,
                version_id=version_id,
                section_path=section.path,
                chunk_type=kind,
                start=start,
                end=end,
                ordinal=ordinal,
                metadata=meta,
            )
            if record is not None:
                chunks.append(record)
                ordinal += 1

    return chunks


def _group_small_units(units: list[tuple[str, int, int, dict]]) -> list[tuple[str, int, int, dict]]:
    """Merge adjacent same-kind units up to the target, never past the ceiling.

    A split piece is never re-merged with anything: it only exists because its
    source block was already too large.
    """
    grouped: list[tuple[str, int, int, dict]] = []
    for kind, start, end, meta in units:
        if grouped and not meta.get("split_from_block"):
            p_kind, p_start, p_end, p_meta = grouped[-1]
            mergeable = (
                p_kind == kind
                and not p_meta.get("split_from_block")
                and end - p_start <= TARGET
                and end - p_start <= HARD_MAX
                and start >= p_end
                and (p_end - p_start < MIN_MERGE or end - start < MIN_MERGE or end - p_start <= TARGET)
            )
            if mergeable:
                grouped[-1] = (kind, p_start, end, p_meta)
                continue
        grouped.append((kind, start, end, meta))
    return grouped
