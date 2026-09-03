from __future__ import annotations

import re

from rag_v1.ids import content_hash, stable_id
from rag_v1.types import ChunkRecord, ParsedDocument

_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
_TABLE_LINE_RE = re.compile(r"^.*\|.*$", re.MULTILINE)


def _split_prose_spans(text: str, abs_start: int, max_chars: int, min_chars: int):
    # Paragraph-aware, no fixed overlap. Stable offsets are retained into normalized_text.
    paras = list(re.finditer(r"\S(?:.*?)(?=\n\s*\n|\Z)", text, re.DOTALL))
    if not paras:
        return []

    groups: list[tuple[int, int]] = []
    g_start = paras[0].start()
    g_end = paras[0].end()
    for p in paras[1:]:
        proposed_end = p.end()
        if proposed_end - g_start > max_chars and g_end - g_start >= min_chars:
            groups.append((abs_start + g_start, abs_start + g_end))
            g_start = p.start()
        g_end = proposed_end
    groups.append((abs_start + g_start, abs_start + g_end))
    return groups


def chunk_document(doc: ParsedDocument, version_id: str, max_chars: int = 3500, min_chars: int = 200) -> list[ChunkRecord]:
    chunks: list[ChunkRecord] = []
    ordinal = 0

    for section in doc.sections:
        section_text = doc.normalized_text[section.char_start:section.char_end]
        cursor = 0
        code_matches = list(_CODE_RE.finditer(section_text))

        # `section` is bound as a default so the closure cannot pick up a later
        # loop iteration's section if this is ever called outside the iteration.
        def emit_span(start: int, end: int, chunk_type: str, section=section):
            nonlocal ordinal
            raw = doc.normalized_text[start:end]
            cleaned = raw.strip()
            if not cleaned:
                return
            # tighten span to stripped text while preserving global offsets
            left_trim = len(raw) - len(raw.lstrip())
            right_trim = len(raw) - len(raw.rstrip())
            s = start + left_trim
            e = end - right_trim
            text = doc.normalized_text[s:e]
            cid = stable_id("chk", version_id, section.path, s, e, content_hash(text), length=40)
            chunks.append(
                ChunkRecord(
                    chunk_id=cid,
                    version_id=version_id,
                    ordinal=ordinal,
                    section_path=section.path,
                    chunk_type=chunk_type,
                    char_start=s,
                    char_end=e,
                    text=text,
                    content_hash=content_hash(text),
                )
            )
            ordinal += 1

        for cm in code_matches:
            prose = section_text[cursor:cm.start()]
            abs_prose_start = section.char_start + cursor
            for s, e in _split_prose_spans(prose, abs_prose_start, max_chars, min_chars):
                ctype = "table" if _TABLE_LINE_RE.search(doc.normalized_text[s:e]) else "prose"
                emit_span(s, e, ctype)
            emit_span(section.char_start + cm.start(), section.char_start + cm.end(), "code")
            cursor = cm.end()

        prose = section_text[cursor:]
        abs_prose_start = section.char_start + cursor
        for s, e in _split_prose_spans(prose, abs_prose_start, max_chars, min_chars):
            ctype = "table" if _TABLE_LINE_RE.search(doc.normalized_text[s:e]) else "prose"
            emit_span(s, e, ctype)

    return chunks
