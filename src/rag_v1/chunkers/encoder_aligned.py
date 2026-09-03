"""chunker_v4_encoder_aligned — retrieval units sized in the encoder's own tokens.

Why this exists
---------------
EXP-009 measured the transformer at two context windows and found retrieval quality
moved with how much of a retrieval unit the encoder could actually see: at 256
tokens 35.2% of control chunks were truncated and recall was 0.500; at 512 tokens
23.2% were truncated and recall was 0.575, with the fused configuration reaching
0.775. The mechanism it proposed was *encoder visibility*, and EXP-010 exists to
test whether that relationship is causal.

What makes this different from V2/V3
------------------------------------
EXP-005 (chunk size x BM25) and EXP-008 (chunk size x dense) both shortened chunks
using corpus character heuristics, and both failed. EXP-008 specifically showed
that splitting a long but topically coherent unit makes dense retrieval *worse*.

So this chunker does not optimise for shortness, and it does not measure anything
in characters. Every limit is measured with the encoder's own WordPiece tokenizer,
and the objective is the largest coherent unit the encoder can consume whole.

Construction: derived from the control, not rebuilt
--------------------------------------------------
Re-chunking from source with a token target would change two things at once — how
oversized units are split *and* how already-fitting units are grouped — so a
comparison against the control transformer cell would no longer isolate encoder
alignment. Instead:

* a control chunk whose payload already fits the window is passed through with the
  **same source span and the same text**;
* only a control chunk that exceeds the window is split, at structural boundaries.

Units the encoder could already see whole are therefore untouched, and any
movement is attributable to the truncation fix. See
``experiments/EXP-010/preregistration.md``.

Budget
------
Measured from the shipped model and tokenizer rather than assumed: the model's
``max_position_embeddings`` is 512 and the special-token overhead is 2 (``[CLS]``
… ``[SEP]``), so the usable payload is 510. The target is 448 and the hard cap 480,
leaving headroom for carryover context and for the fact that per-atom token counts
are summed during packing and only then verified against a real encode.
"""

from __future__ import annotations

import re

from rag_v1.chunkers import control
from rag_v1.chunkers.base import (
    LIST_ITEM_RE,
    SENTENCE_END_RE,
    TABLE_SEPARATOR_RE,
    Block,
    ChunkerSpec,
    code_language,
    make_chunk,
    segment_blocks,
    table_header,
)
from rag_v1.types import ChunkRecord, ParsedDocument

ENCODER_WINDOW_TOKENS = 512
SPECIAL_TOKEN_OVERHEAD = 2  # measured, not assumed; see encoder_budget()
USABLE_PAYLOAD_TOKENS = ENCODER_WINDOW_TOKENS - SPECIAL_TOKEN_OVERHEAD
TARGET_PAYLOAD_TOKENS = 448
HARD_PAYLOAD_TOKENS = 480
#: A carried header may never consume more than this share of the budget.
MAX_CARRYOVER_TOKENS = 96

SPEC = ChunkerSpec(
    name="chunker_v4_encoder_aligned",
    version="4.0",
    config={
        "encoder": "sentence-transformers/all-MiniLM-L6-v2",
        "encoder_window_tokens": ENCODER_WINDOW_TOKENS,
        "special_token_overhead": SPECIAL_TOKEN_OVERHEAD,
        "usable_payload_tokens": USABLE_PAYLOAD_TOKENS,
        "target_payload_tokens": TARGET_PAYLOAD_TOKENS,
        "hard_payload_tokens": HARD_PAYLOAD_TOKENS,
        "max_carryover_tokens": MAX_CARRYOVER_TOKENS,
        "limits_measured_in": "encoder WordPiece tokens (not characters or words)",
        "derived_from": control.CONTROL_CHUNK_SET_ID,
        "fitting_chunks": "passed through unchanged",
        "carryover": "section heading on forced continuations; table header on later row groups",
    },
)

#: Pinned rather than derived from the config hash so the chunk set is addressable
#: by the name the experiment brief uses.
ENCODER_ALIGNED_CHUNK_SET_ID = "cs_v4_encoder_aligned"

_TOKENIZER = None


def encoder_tokenizer():
    """The encoder's own tokenizer, with its shipped truncation cleared.

    ``tokenizer.json`` carries a saved truncation of 128 which ``from_file``
    restores. Counting lengths through that would silently cap every measurement
    at 128 tokens — the defect EXP-009 hit — so truncation and padding are cleared
    explicitly here and never left at their loaded defaults.
    """
    global _TOKENIZER
    if _TOKENIZER is None:
        from tokenizers import Tokenizer

        from rag_v1.embedders_transformer import model_dir

        tok = Tokenizer.from_file(str(model_dir() / "tokenizer.json"))
        tok.no_truncation()
        tok.no_padding()
        _TOKENIZER = tok
    return _TOKENIZER


def payload_tokens(text: str) -> int:
    """Token count excluding special tokens — what has to fit in the payload."""
    return len(encoder_tokenizer().encode(text, add_special_tokens=False).ids)


def encoded_tokens(text: str) -> int:
    """Token count as the encoder will actually see it, special tokens included."""
    return len(encoder_tokenizer().encode(text, add_special_tokens=True).ids)


def encoder_budget() -> dict:
    """Derive the usable payload from the tokenizer and model, not from assumption."""
    import json

    from rag_v1.embedders_transformer import model_dir

    probe = "alpha beta gamma"
    overhead = encoded_tokens(probe) - payload_tokens(probe)
    cfg = json.loads((model_dir() / "config.json").read_text())
    window = int(cfg["max_position_embeddings"])
    return {
        "max_position_embeddings": window,
        "special_token_overhead_measured": overhead,
        "usable_payload_tokens": window - overhead,
        "target_payload_tokens": TARGET_PAYLOAD_TOKENS,
        "hard_payload_tokens": HARD_PAYLOAD_TOKENS,
        "probe": probe,
    }


# --------------------------------------------------------------------------
# Splitting an oversized unit
# --------------------------------------------------------------------------

def _atoms(text: str, abs_start: int, kind: str) -> list[tuple[int, int]]:
    """The finest boundaries this block may be cut on, in source order.

    Code and tables are cut only at whole lines, so a row keeps its columns and a
    statement is never severed. Prose is cut at list items when it is a list and at
    sentence ends otherwise.
    """
    if kind in ("code", "table"):
        spans, offset = [], 0
        for line in text.splitlines(keepends=True):
            spans.append((abs_start + offset, abs_start + offset + len(line)))
            offset += len(line)
        return spans or [(abs_start, abs_start + len(text))]

    if any(LIST_ITEM_RE.match(ln) for ln in text.splitlines()):
        spans, offset, group_start = [], 0, 0
        for line in text.splitlines(keepends=True):
            if LIST_ITEM_RE.match(line) and offset > group_start:
                spans.append((abs_start + group_start, abs_start + offset))
                group_start = offset
            offset += len(line)
        if offset > group_start:
            spans.append((abs_start + group_start, abs_start + offset))
        return spans

    spans, cursor = [], 0
    for match in SENTENCE_END_RE.finditer(text):
        spans.append((abs_start + cursor, abs_start + match.end()))
        cursor = match.end()
    if cursor < len(text):
        spans.append((abs_start + cursor, abs_start + len(text)))
    return spans or [(abs_start, abs_start + len(text))]


def _hard_split_tokens(text: str, abs_start: int, budget: int) -> list[tuple[int, int]]:
    """Last resort for a single atom that alone exceeds the budget.

    Cuts on whitespace so a word is never split into fragments the tokenizer would
    then encode differently from the source.
    """
    spans, pos = [], 0
    while pos < len(text):
        lo, hi = pos + 1, len(text)
        best = None
        while lo <= hi:  # widest prefix that still fits, by bisection on characters
            mid = (lo + hi) // 2
            cut = text.rfind(" ", pos + 1, mid) if mid < len(text) else len(text)
            cut = cut if cut > pos else mid
            if payload_tokens(text[pos:cut]) <= budget:
                best, lo = cut, mid + 1
            else:
                hi = mid - 1
        end = best if best and best > pos else min(pos + 200, len(text))
        spans.append((abs_start + pos, abs_start + end))
        pos = end
    return spans


def _pack(atoms: list[tuple[int, int]], text_of, budget: int) -> list[list[tuple[int, int]]]:
    """Greedily group atoms into the largest runs that fit the budget.

    Per-atom counts are summed while packing because measuring every candidate
    group would be far slower, but WordPiece is not perfectly additive across a
    join: six chunks in the first build came out 1-2 tokens over the cap that way.
    So each closed group is verified against the contiguous text that will actually
    be stored, and atoms are pushed back until it genuinely fits.
    """
    groups: list[list[tuple[int, int]]] = []

    def close(group: list[tuple[int, int]]) -> list[tuple[int, int]]:
        """Emit ``group``, returning any atoms that had to be deferred."""
        deferred: list[tuple[int, int]] = []
        while len(group) > 1 and payload_tokens(text_of((group[0][0], group[-1][1]))) > budget:
            deferred.insert(0, group.pop())
        if group:
            groups.append(group)
        return deferred

    current: list[tuple[int, int]] = []
    current_tokens = 0
    pending = list(atoms)
    while pending:
        span = pending.pop(0)
        tokens = payload_tokens(text_of(span))
        if tokens > budget:
            if current:
                pending = close(current) + pending
                current, current_tokens = [], 0
                continue
            for piece in _hard_split_tokens(text_of(span), span[0], budget):
                groups.append([piece])
            continue
        if current and current_tokens + tokens > budget:
            deferred = close(current)
            current, current_tokens = [], 0
            pending = deferred + [span] + pending
            continue
        current.append(span)
        current_tokens += tokens
    if current:
        close(current)
    return groups


def _compact_header(header: str) -> str:
    """Shrink a carried table header to the part that carries meaning.

    Markdown tables in this corpus are whitespace-padded to align columns, and the
    separator row is nothing but dashes and colons. Carried verbatim, one header
    measured 1,053 tokens and was pinned onto a 64-character row — the carryover
    dwarfed the content it was supposed to contextualise. Column *names* are what
    make a detached row interpretable, so runs of padding are collapsed and the
    separator row is dropped. No word of the source is changed.
    """
    lines = []
    for line in header.splitlines():
        if TABLE_SEPARATOR_RE.match(line):
            continue
        collapsed = re.sub(r"[ \t]{2,}", " ", line).strip()
        if collapsed:
            lines.append(collapsed)
    return "\n".join(lines)


def _runs(blocks: list) -> list[dict]:
    """Group adjacent blocks that may share a chunk.

    Consecutive prose paragraphs are one run, so packing can merge them back up to
    the budget. A table or a code fence always starts its own run: merging a row
    group with surrounding prose would break the header carryover and blur what the
    unit is.
    """
    runs: list[dict] = []
    for block in blocks:
        if runs and block.kind == "prose" and runs[-1]["kind"] == "prose":
            runs[-1]["blocks"].append(block)
        else:
            runs.append({"kind": block.kind, "blocks": [block]})
    return runs


def _split_oversized(doc: ParsedDocument, start: int, end: int, section_path: list[str]) -> list[dict]:
    """Split one oversized control chunk into window-fitting pieces."""
    whole = doc.normalized_text[start:end]
    blocks = segment_blocks(whole, start)
    if not blocks:
        blocks = [Block("prose", start, end)]

    heading = section_path[-1] if section_path else ""
    pieces: list[dict] = []

    for run in _runs(blocks):
        first = run["blocks"][0]
        btext = doc.normalized_text[first.start:first.end]
        header = _compact_header(table_header(btext)) if run["kind"] == "table" else ""
        # A carryover only earns its place if it leaves most of the budget for
        # content. Anything larger is dropped rather than allowed to squeeze the
        # payload, because a floor on the budget is exactly how a chunk ends up
        # over the window.
        if header and payload_tokens(header) > MAX_CARRYOVER_TOKENS:
            header = ""
        candidate = header or heading
        reserve = payload_tokens(candidate) + 1 if candidate else 0
        if reserve > MAX_CARRYOVER_TOKENS:
            candidate, reserve = "", 0
        budget = TARGET_PAYLOAD_TOKENS - reserve

        atoms: list[tuple[int, int]] = []
        for block in run["blocks"]:
            atoms.extend(_atoms(doc.normalized_text[block.start:block.end], block.start, block.kind))

        groups = _pack(atoms, lambda s: doc.normalized_text[s[0]:s[1]], budget)
        multi = len(groups) > 1
        origin = f"{run['blocks'][0].start}:{run['blocks'][-1].end}"

        for index, group in enumerate(groups):
            g_start, g_end = group[0][0], group[-1][1]
            meta: dict = {"block_kind": run["kind"], "encoder_aligned_split": True}
            carry = ""
            if multi:
                meta |= {"split_from_block": origin, "part_index": index, "part_count": len(groups)}
                if run["kind"] == "code":
                    meta["code_language"] = code_language(btext)
                if index > 0 and candidate:
                    # Narrow, source-grounded carryover only — never a broad
                    # repetitive prefix, which EXP-006 showed inflates df.
                    carry = candidate
                    meta["table_header_carried" if header else "section_heading_carried"] = True
            pieces.append({"start": g_start, "end": g_end, "kind": run["kind"],
                           "meta": meta, "carryover": carry})
    return pieces


# --------------------------------------------------------------------------

def chunk(doc: ParsedDocument, version_id: str, spec: ChunkerSpec = SPEC) -> list[ChunkRecord]:
    records: list[ChunkRecord] = []
    ordinal = 0

    for base in control.chunk(doc, version_id):
        tokens = payload_tokens(base.text)
        if tokens <= HARD_PAYLOAD_TOKENS:
            record = make_chunk(
                spec=spec, doc=doc, version_id=version_id, section_path=base.section_path,
                chunk_type=base.chunk_type, start=base.char_start, end=base.char_end,
                ordinal=ordinal,
                metadata={**base.metadata, "encoder_payload_tokens": tokens,
                          "encoder_aligned_split": False,
                          "control_chunk_id": base.chunk_id},
            )
            if record is not None:
                records.append(record)
                ordinal += 1
            continue

        for piece in _split_oversized(doc, base.char_start, base.char_end, base.section_path):
            record = make_chunk(
                spec=spec, doc=doc, version_id=version_id, section_path=base.section_path,
                chunk_type=piece["kind"] if piece["kind"] in ("code", "table") else base.chunk_type,
                start=piece["start"], end=piece["end"], ordinal=ordinal,
                metadata={**piece["meta"], "control_chunk_id": base.chunk_id,
                          "control_payload_tokens": tokens},
            )
            if record is None:
                continue
            carry = piece["carryover"]
            if carry:
                # Last line of defence: the representation that will actually be
                # embedded is measured here, and a carryover that would push it
                # past the window is dropped rather than shipped. Packing reserves
                # budget for the carryover, so this should never fire — it exists
                # so that "encoder-aligned" is a checked property, not a claim.
                composed = f"{carry}\n{record.text}"
                if encoded_tokens(composed) <= ENCODER_WINDOW_TOKENS:
                    record.context_header = carry
                    record.search_text = composed
                else:
                    record.metadata["carryover_dropped_to_fit_window"] = True
            record.metadata["encoder_payload_tokens"] = payload_tokens(
                record.search_text or record.text
            )
            records.append(record)
            ordinal += 1

    return records


__all__ = [
    "ENCODER_ALIGNED_CHUNK_SET_ID", "HARD_PAYLOAD_TOKENS", "SPEC", "TARGET_PAYLOAD_TOKENS",
    "chunk", "encoded_tokens", "encoder_budget", "encoder_tokenizer", "payload_tokens",
]
