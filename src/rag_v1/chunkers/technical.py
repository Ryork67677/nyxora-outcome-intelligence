"""chunker_v3_technical — V2's safety properties plus reference-document structure.

V3 keeps every guarantee V2 makes (real ceiling, structural boundaries, exact
source spans) and adds two things that only make sense for API reference material:

**Parameter entries become retrievable units.** Reference pages document each
parameter as an identifier line followed by its type and description. Under V2
those still group into a paragraph run, so a question about one parameter competes
with every sibling parameter in the same chunk. V3 emits a parameter entry as its
own unit and prepends a context header naming the endpoint and section, because a
bare ``max_tokens integer`` fragment is unretrievable and useless as evidence.

**Large tables gain row groups with their header.** A row group carries the table's
header rows as context, so a matched row still says what its columns mean. Groups
are kept to a few rows rather than one row each: hundreds of near-identical
single-row chunks would flood the index and, in a dense retriever, collapse into
indistinguishable vectors.

Context prefixes and the evidence contract
------------------------------------------
A prefix is prepended to the *indexed* text only. ``char_start``/``char_end``
continue to denote the exact source span, and ``metadata.context_prefix_len``
records the prefix length so the source text is recoverable as
``text[context_prefix_len:]``. Evidence scoring compares spans, never text, so
this cannot move the evaluation target — and the validator in
``scripts/validate_evidence_mapping.py`` checks the invariant explicitly.
"""

from __future__ import annotations

import re

from rag_v1.chunkers.base import (
    ChunkerSpec,
    code_language,
    make_chunk,
    segment_blocks,
    split_code,
    split_prose,
    split_table,
    table_header,
)
from rag_v1.chunkers.bounded import _group_small_units
from rag_v1.types import ChunkRecord, ParsedDocument

SPEC = ChunkerSpec(
    name="chunker_v3_technical",
    version="3.0",
    config={
        "target_max_chars": 1200,
        "hard_max_chars": 2000,
        "min_merge_chars": 120,
        "enforces_hard_limit": True,
        "parameter_entry_units": True,
        "table_row_group_size": 4,
        "context_header": True,
    },
)

TARGET = SPEC.config["target_max_chars"]
HARD_MAX = SPEC.config["hard_max_chars"]
ROW_GROUP = SPEC.config["table_row_group_size"]

# A parameter entry opens with a bare or backticked identifier, optionally
# followed by its type — the shape used across both providers' reference pages.
PARAM_ENTRY_RE = re.compile(
    r"^\s{0,4}(?:[-*]\s+)?`?(?P<name>[A-Za-z_][A-Za-z0-9_.\[\]]{2,})`?"
    r"(?:\s+(?P<type>string|integer|number|boolean|object|array|enum|null)\b.*)?$"
)


def _context_header(section_path: list[str], extra: str = "") -> str:
    trail = " > ".join(section_path)
    return f"[{trail}]{(' ' + extra) if extra else ''}"


def _parameter_spans(text: str, start: int) -> list[tuple[int, int, str]]:
    """Find parameter entries inside a prose block.

    An entry runs from its identifier line to the line before the next entry.
    Returns an empty list unless several entries are present, so ordinary prose
    that happens to begin with a word is never shredded.
    """
    lines = text.splitlines(keepends=True)
    starts: list[tuple[int, str]] = []
    offset = 0
    for line in lines:
        match = PARAM_ENTRY_RE.match(line.rstrip())
        if match and len(line.strip()) < 120:
            starts.append((offset, match.group("name")))
        offset += len(line)

    if len(starts) < 2:
        return []

    spans: list[tuple[int, int, str]] = []
    for index, (offset, name) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(text)
        if end - offset >= 20:
            spans.append((start + offset, start + end, name))
    return spans if len(spans) >= 2 else []


def _table_row_groups(text: str, start: int) -> list[tuple[int, int]]:
    """Group table body rows into small runs, skipping the header rows."""
    header = table_header(text)
    body_offset = len(header) + 1 if header else 0
    lines = text[body_offset:].splitlines(keepends=True)

    groups: list[tuple[int, int]] = []
    offset = body_offset
    group_start = body_offset
    rows = 0
    for line in lines:
        offset += len(line)
        rows += 1
        if rows >= ROW_GROUP or offset - group_start > TARGET:
            groups.append((start + group_start, start + offset))
            group_start = offset
            rows = 0
    if offset > group_start:
        groups.append((start + group_start, start + offset))
    return groups


def chunk(doc: ParsedDocument, version_id: str, spec: ChunkerSpec = SPEC) -> list[ChunkRecord]:
    chunks: list[ChunkRecord] = []
    ordinal = 0

    for section in doc.sections:
        section_text = doc.normalized_text[section.char_start:section.char_end]
        blocks = segment_blocks(section_text, section.char_start)
        emitted: list[tuple[str, int, int, dict, str]] = []

        for block in blocks:
            block_text = doc.normalized_text[block.start:block.end]

            if block.kind == "prose":
                params = _parameter_spans(block_text, block.start)
                if params:
                    for p_start, p_end, name in params:
                        for s, e in split_prose(
                            doc.normalized_text[p_start:p_end], p_start, HARD_MAX
                        ):
                            emitted.append(
                                (
                                    "prose",
                                    s,
                                    e,
                                    {"block_kind": "parameter_entry", "parameter": name},
                                    _context_header(section.path, f"parameter `{name}`"),
                                )
                            )
                    continue
                for s, e in split_prose(block_text, block.start, HARD_MAX):
                    emitted.append(("prose", s, e, {"block_kind": "prose"}, ""))

            elif block.kind == "table":
                header = table_header(block_text)
                if len(block_text) > TARGET:
                    for s, e in _table_row_groups(block_text, block.start):
                        for bs, be in split_table(doc.normalized_text[s:e], s, HARD_MAX):
                            emitted.append(
                                (
                                    "table_row",
                                    bs,
                                    be,
                                    {
                                        "block_kind": "table_row_group",
                                        "table_block": f"{block.start}:{block.end}",
                                        "table_header": header,
                                    },
                                    _context_header(section.path, header.replace("\n", " ")),
                                )
                            )
                else:
                    for s, e in split_table(block_text, block.start, HARD_MAX):
                        emitted.append(("table", s, e, {"block_kind": "table"}, ""))

            else:
                pieces = split_code(block_text, block.start, HARD_MAX)
                language = code_language(block_text)
                for index, (s, e) in enumerate(pieces):
                    meta = {"block_kind": "code", "code_language": language}
                    if len(pieces) > 1:
                        meta |= {
                            "split_from_block": f"{block.start}:{block.end}",
                            "part_index": index,
                            "part_count": len(pieces),
                        }
                    # A code example is a sibling of its section's prose, and is
                    # kept separately retrievable rather than merged into it.
                    emitted.append(("code", s, e, meta, _context_header(section.path, f"{language} example")))

        # Units without a context header are ordinary prose/table blocks and are
        # still grouped up to target as in V2; context-carrying units are already
        # deliberately sized and are never merged. The two streams are recombined
        # in document order so ordinals follow the source.
        plain = [(k, s, e, m) for k, s, e, m, ctx in emitted if not ctx]
        final: list[tuple[str, int, int, dict, str]] = [
            (k, s, e, m, "") for k, s, e, m in _group_small_units(plain)
        ]
        final += [(k, s, e, m, ctx) for k, s, e, m, ctx in emitted if ctx]
        final.sort(key=lambda u: (u[1], u[2]))

        for kind, s, e, meta, ctx in final:
            record = make_chunk(
                spec=spec,
                doc=doc,
                version_id=version_id,
                section_path=section.path,
                chunk_type=kind,
                start=s,
                end=e,
                ordinal=ordinal,
                metadata=meta,
                context_prefix=ctx,
            )
            if record is not None:
                chunks.append(record)
                ordinal += 1

    return chunks
