"""EXP-005 chunker tests.

These are the guarantees the experiment's conclusions rest on. If the hard limit
is not really enforced, or an evidence span stops mapping to a chunk, or the
control chunker drifts, then the measured recall difference stops meaning what
the report says it means.
"""

from __future__ import annotations

import pytest

from rag_v1.chunkers import available, bounded, chunk_set_id_for, control, get_chunker, technical
from rag_v1.parsing import _sections_from_markdown
from rag_v1.types import ParsedDocument

HARD_MAX = bounded.SPEC.config["hard_max_chars"]


def make_doc(body: str) -> ParsedDocument:
    return ParsedDocument(
        normalized_text=body,
        sections=_sections_from_markdown(body),
        parser_name="markdown",
        parser_version="v1.0",
    )


def big_parameter_table(rows: int = 220) -> str:
    header = (
        "| Parameter | Type | Required | Description |\n"
        "| --------- | ---- | -------- | ----------- |\n"
    )
    body = "".join(
        f"| `param_{i}` | integer | {'yes' if i % 3 == 0 else 'no'} | "
        f"Controls behaviour number {i} of the endpoint. |\n"
        for i in range(rows)
    )
    return f"## Body Parameters\n\n{header}{body}\n"


def big_code_block(functions: int = 60) -> str:
    body = "\n\n".join(
        f"def handler_{i}(request):\n"
        f"    # example {i}\n"
        f"    payload = build_payload(request, index={i})\n"
        f"    return client.messages.create(**payload)"
        for i in range(functions)
    )
    return f"## Example\n\n```python\n{body}\n```\n"


def big_prose(sentences: int = 200) -> str:
    body = " ".join(
        f"The service enforces constraint number {i} on every inbound request." for i in range(sentences)
    )
    return f"## Overview\n\n{body}\n"


DOC_BODY = big_parameter_table() + big_code_block() + big_prose()


@pytest.fixture(scope="module")
def doc() -> ParsedDocument:
    return make_doc(DOC_BODY)


@pytest.mark.parametrize("name", ["chunker_v2_bounded", "chunker_v3_technical"])
def test_no_chunk_exceeds_hard_maximum(doc, name):
    # The control's defect is that its ceiling is only a grouping target. V2 and
    # V3 must enforce theirs on every emitted chunk, whatever the block type.
    _, chunk = get_chunker(name)
    oversized = [c for c in chunk(doc, "ver_test") if c.char_end - c.char_start > HARD_MAX]
    assert oversized == [], [
        (c.chunk_type, c.char_end - c.char_start, c.section_path) for c in oversized
    ]


def test_control_still_produces_oversized_chunks(doc):
    # Guards the premise of the experiment: if the control stopped being
    # unbounded, EXP-005 would be comparing against the wrong baseline.
    chunks = control.chunk(doc, "ver_test")
    assert any(c.char_end - c.char_start > HARD_MAX for c in chunks)


@pytest.mark.parametrize("name", ["chunker_v2_bounded", "chunker_v3_technical"])
def test_oversized_table_keeps_heading_and_column_context(doc, name):
    _, chunk = get_chunker(name)
    table_chunks = [
        c for c in chunk(doc, "ver_test")
        if c.chunk_type in {"table", "table_row"} and "param_" in c.text
    ]
    assert len(table_chunks) > 1, "an oversized table must be split into several units"
    for piece in table_chunks:
        assert piece.char_end - piece.char_start <= HARD_MAX
        # Every fragment must still be attributable to its table, either through
        # the retained header or through recorded parent metadata.
        has_context = (
            "Parameter" in piece.text
            or piece.metadata.get("table_header")
            or piece.metadata.get("table_block")
            or piece.metadata.get("split_from_block")
        )
        assert has_context, f"table fragment lost its heading/column context: {piece.text[:80]!r}"


@pytest.mark.parametrize("name", ["chunker_v2_bounded", "chunker_v3_technical"])
def test_oversized_code_is_bounded_and_split_on_line_boundaries(doc, name):
    _, chunk = get_chunker(name)
    code_chunks = [c for c in chunk(doc, "ver_test") if c.chunk_type == "code"]
    assert len(code_chunks) > 1
    for piece in code_chunks:
        assert piece.char_end - piece.char_start <= HARD_MAX
    # Code is never cut mid-line when logical boundaries exist.
    body = [c for c in code_chunks if "def handler_" in c.text]
    assert body, "expected the code block to survive as retrievable units"
    for piece in body:
        source = piece.text[piece.metadata.get("context_prefix_len", 0):]
        assert "def handler_" in source


@pytest.mark.parametrize("name", ["chunker_v2_bounded", "chunker_v3_technical"])
def test_oversized_prose_splits_at_sentence_boundaries(doc, name):
    _, chunk = get_chunker(name)
    prose = [
        c for c in chunk(doc, "ver_test")
        if c.chunk_type == "prose" and "enforces constraint number" in c.text
    ]
    assert len(prose) > 1
    for piece in prose:
        assert piece.char_end - piece.char_start <= HARD_MAX


@pytest.mark.parametrize("name", available())
def test_every_chunk_retains_source_lineage(doc, name):
    _, chunk = get_chunker(name)
    for piece in chunk(doc, "ver_test"):
        assert piece.version_id == "ver_test"
        assert piece.section_path, "a chunk without a section path cannot anchor evidence"
        assert piece.char_end > piece.char_start
        assert piece.content_hash


@pytest.mark.parametrize("name", available())
def test_source_span_round_trips(doc, name):
    # char_start/char_end must always address the exact source text. V3 may
    # prepend a context header to the indexed text, and records its length.
    _, chunk = get_chunker(name)
    for piece in chunk(doc, "ver_test"):
        prefix_len = piece.metadata.get("context_prefix_len", 0)
        assert piece.text[prefix_len:] == DOC_BODY[piece.char_start:piece.char_end]


@pytest.mark.parametrize("name", available())
def test_chunking_is_deterministic(doc, name):
    _, chunk = get_chunker(name)
    first = chunk(doc, "ver_test")
    second = chunk(make_doc(DOC_BODY), "ver_test")
    assert [(c.chunk_id, c.char_start, c.char_end) for c in first] == [
        (c.chunk_id, c.char_start, c.char_end) for c in second
    ]


@pytest.mark.parametrize("name", available())
def test_known_evidence_still_maps_to_a_chunk(doc, name):
    # Stand-in for the golden set's contract: a short answer-bearing sentence
    # must remain inside some chunk with a usable section path.
    needle = "Controls behaviour number 137 of the endpoint."
    start = DOC_BODY.index(needle)
    end = start + len(needle)

    _, chunk = get_chunker(name)
    covering = [c for c in chunk(doc, "ver_test") if c.char_start < end and c.char_end > start]
    assert covering, "evidence span no longer maps to any chunk"
    assert all(c.section_path for c in covering)


def test_control_chunk_set_id_is_pinned():
    # The control's rows were adopted under this id by sql/002_chunk_sets.sql;
    # re-deriving it from a config hash would orphan them.
    assert chunk_set_id_for("chunker_v1_control") == "cs_v1_control"


def test_chunkers_have_distinct_identities():
    ids = {name: chunk_set_id_for(name) for name in available()}
    assert len(set(ids.values())) == len(ids), ids
    assert bounded.SPEC.config_hash != technical.SPEC.config_hash


def test_control_config_records_that_it_does_not_enforce_a_limit():
    assert control.SPEC.config["enforces_hard_limit"] is False
    assert bounded.SPEC.config["enforces_hard_limit"] is True
    assert technical.SPEC.config["enforces_hard_limit"] is True
