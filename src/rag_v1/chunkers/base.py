"""Shared chunker machinery: identity, structural segmentation, bounded splitting.

Every chunker carries an explicit name, version and config hash so that a chunk
set in the database is traceable to the exact code and settings that produced it,
and so two chunkings can never be silently conflated.

The segmentation here is deliberately structural rather than character-counting.
Documentation has real boundaries — fenced code, table runs, paragraphs — and the
EXP-005 hypothesis is that respecting them while enforcing a genuine size ceiling
is what makes answer-bearing sentences retrievable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from rag_v1.ids import config_hash, content_hash, stable_id
from rag_v1.types import ChunkRecord, ParsedDocument

CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
TABLE_LINE_RE = re.compile(r"^\s*\|.*$|^[^\n]*\|[^\n]*\|[^\n]*$")
# A table separator row: | --- | :--- | ---: |
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?[\s:\-|]+\|[\s:\-|]*$")
SENTENCE_END_RE = re.compile(r"(?<=[.!?:;])\s+(?=[A-Z`\-*\d])")
# Lines that begin a new logical unit inside a code block.
CODE_BOUNDARY_RE = re.compile(
    r"^\s*(?:@|def |class |async def |function |export |const |let |var |public |private |"
    r"curl |import |from |#\s|//\s|/\*)"
)
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")


@dataclass(frozen=True)
class Block:
    """A structural unit of a section, with absolute offsets into normalized_text."""

    kind: str  # "prose" | "code" | "table"
    start: int
    end: int


@dataclass
class ChunkerSpec:
    """Identity and configuration of a chunking strategy."""

    name: str
    version: str
    config: dict = field(default_factory=dict)

    @property
    def config_hash(self) -> str:
        return config_hash({"name": self.name, "version": self.version, **self.config})

    @property
    def chunk_set_id(self) -> str:
        return stable_id("cs", self.name, self.version, self.config_hash, length=24)


def segment_blocks(text: str, abs_start: int) -> list[Block]:
    """Split a section into fenced code, table runs and prose paragraphs.

    Offsets returned are absolute into ``normalized_text`` so evidence spans stay
    comparable across chunkers.
    """
    blocks: list[Block] = []
    cursor = 0
    for match in CODE_FENCE_RE.finditer(text):
        if match.start() > cursor:
            blocks.extend(_segment_non_code(text[cursor:match.start()], abs_start + cursor))
        blocks.append(Block("code", abs_start + match.start(), abs_start + match.end()))
        cursor = match.end()
    if cursor < len(text):
        blocks.extend(_segment_non_code(text[cursor:], abs_start + cursor))
    return [b for b in blocks if text[b.start - abs_start:b.end - abs_start].strip()]


def _segment_non_code(text: str, abs_start: int) -> list[Block]:
    """Separate contiguous table runs from prose paragraphs."""
    blocks: list[Block] = []
    offset = 0
    run_start: int | None = None
    lines = text.splitlines(keepends=True)

    def flush_prose(chunk_text: str, start: int) -> None:
        for para in re.finditer(r"\S(?:.*?)(?=\n\s*\n|\Z)", chunk_text, re.DOTALL):
            blocks.append(Block("prose", start + para.start(), start + para.end()))

    pending_prose_start = 0
    for line in lines:
        is_table = "|" in line and line.count("|") >= 2
        if is_table and run_start is None:
            if offset > pending_prose_start:
                flush_prose(text[pending_prose_start:offset], abs_start + pending_prose_start)
            run_start = offset
        elif not is_table and run_start is not None:
            blocks.append(Block("table", abs_start + run_start, abs_start + offset))
            run_start = None
            pending_prose_start = offset
        offset += len(line)

    if run_start is not None:
        blocks.append(Block("table", abs_start + run_start, abs_start + offset))
    elif offset > pending_prose_start:
        flush_prose(text[pending_prose_start:offset], abs_start + pending_prose_start)
    return blocks


def _split_points_by_lines(text: str, start: int, hard_max: int, boundary_re: re.Pattern | None) -> list[tuple[int, int]]:
    """Group whole lines into spans no longer than ``hard_max``.

    Preferred break points are lines matching ``boundary_re``; a group is only
    broken mid-run when it would otherwise exceed the ceiling.
    """
    spans: list[tuple[int, int]] = []
    offset = 0
    group_start = 0
    for line in text.splitlines(keepends=True):
        line_end = offset + len(line)
        too_long = line_end - group_start > hard_max
        at_boundary = bool(boundary_re and boundary_re.match(line)) and offset > group_start
        if too_long and offset > group_start or at_boundary and line_end - group_start > hard_max * 0.6:
            spans.append((start + group_start, start + offset))
            group_start = offset
        offset = line_end
    if offset > group_start:
        spans.append((start + group_start, start + offset))
    return spans


def _hard_split(text: str, start: int, hard_max: int) -> list[tuple[int, int]]:
    """Last-resort split of a single unbreakable run, preferring whitespace."""
    spans: list[tuple[int, int]] = []
    pos = 0
    while pos < len(text):
        end = min(pos + hard_max, len(text))
        if end < len(text):
            window = text.rfind(" ", pos + int(hard_max * 0.5), end)
            if window > pos:
                end = window
        spans.append((start + pos, start + end))
        pos = end
    return spans


def split_prose(text: str, start: int, hard_max: int) -> list[tuple[int, int]]:
    """Bound an oversized prose block: list items, then sentences, then hard."""
    if len(text) <= hard_max:
        return [(start, start + len(text))]

    if any(LIST_ITEM_RE.match(ln) for ln in text.splitlines()):
        spans = _split_points_by_lines(text, start, hard_max, LIST_ITEM_RE)
        if all(e - s <= hard_max for s, e in spans):
            return spans

    # Accumulate sentences, closing a group at the last sentence end that keeps it
    # under the ceiling.
    spans: list[tuple[int, int]] = []
    group_start = 0
    last_break = 0
    for match in SENTENCE_END_RE.finditer(text):
        if match.start() - group_start > hard_max and last_break > group_start:
            spans.append((start + group_start, start + last_break))
            group_start = last_break
        last_break = match.end()
    spans.append((start + group_start, start + len(text)))

    bounded: list[tuple[int, int]] = []
    for s, e in spans:
        if e - s > hard_max:
            bounded.extend(_hard_split(text[s - start:e - start], s, hard_max))
        else:
            bounded.append((s, e))
    return bounded


def table_header(text: str) -> str:
    """Return the header lines of a markdown table run, if it has one."""
    lines = text.splitlines()
    for idx, line in enumerate(lines[:3]):
        if TABLE_SEPARATOR_RE.match(line) and idx > 0:
            return "\n".join(lines[: idx + 1])
    return ""


def split_table(text: str, start: int, hard_max: int) -> list[tuple[int, int]]:
    """Bound an oversized table run at whole-row boundaries."""
    if len(text) <= hard_max:
        return [(start, start + len(text))]
    return _split_points_by_lines(text, start, hard_max, None)


def split_code(text: str, start: int, hard_max: int) -> list[tuple[int, int]]:
    """Bound an oversized code block at logical boundaries, never mid-line."""
    if len(text) <= hard_max:
        return [(start, start + len(text))]
    spans = _split_points_by_lines(text, start, hard_max, CODE_BOUNDARY_RE)
    bounded: list[tuple[int, int]] = []
    for s, e in spans:
        if e - s > hard_max:
            # A single line longer than the ceiling (minified payload, long URL).
            bounded.extend(_hard_split(text[s - start:e - start], s, hard_max))
        else:
            bounded.append((s, e))
    return bounded


def code_language(text: str) -> str:
    first = text.splitlines()[0] if text else ""
    return first.removeprefix("```").strip() or "unknown"


def make_chunk(
    *,
    spec: ChunkerSpec,
    doc: ParsedDocument,
    version_id: str,
    section_path: list[str],
    chunk_type: str,
    start: int,
    end: int,
    ordinal: int,
    metadata: dict | None = None,
    context_prefix: str = "",
) -> ChunkRecord | None:
    """Build one chunk, tightening the span to its stripped text.

    ``char_start``/``char_end`` always denote the exact source span. When a
    ``context_prefix`` is supplied (V3 only) it is prepended to the indexed text
    and its length recorded in metadata, so the source span remains recoverable as
    ``text[context_prefix_len:]``.
    """
    raw = doc.normalized_text[start:end]
    if not raw.strip():
        return None
    s = start + (len(raw) - len(raw.lstrip()))
    e = end - (len(raw) - len(raw.rstrip()))
    source_text = doc.normalized_text[s:e]
    text = f"{context_prefix}\n{source_text}" if context_prefix else source_text

    meta = dict(metadata or {})
    meta["chunker"] = spec.name
    meta["source_len"] = len(source_text)
    if context_prefix:
        meta["context_prefix_len"] = len(context_prefix) + 1

    return ChunkRecord(
        chunk_id=stable_id(
            "chk", spec.chunk_set_id, version_id, section_path, s, e, content_hash(text), length=40
        ),
        version_id=version_id,
        ordinal=ordinal,
        section_path=section_path,
        chunk_type=chunk_type,
        char_start=s,
        char_end=e,
        text=text,
        content_hash=content_hash(text),
        metadata=meta,
    )
