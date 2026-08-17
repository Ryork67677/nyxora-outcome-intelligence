from pathlib import Path

from rag_v1.chunking import chunk_document
from rag_v1.parsing import parse_file


def test_chunk_ids_and_spans_are_stable():
    path = Path(__file__).parent / "fixtures/docs/widget_v2.md"
    doc = parse_file(path)
    a = chunk_document(doc, "ver_test", max_chars=500, min_chars=20)
    b = chunk_document(doc, "ver_test", max_chars=500, min_chars=20)
    assert [x.chunk_id for x in a] == [x.chunk_id for x in b]
    for c in a:
        assert doc.normalized_text[c.char_start:c.char_end] == c.text
