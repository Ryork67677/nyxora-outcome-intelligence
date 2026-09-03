import hashlib

from rag_v1.evals.retrieval_eval import redact_hit
from rag_v1.types import SearchHit


def make_hit(text: str) -> dict:
    return SearchHit(
        chunk_id="c1",
        version_id="v1",
        section_path=["HTTP errors"],
        char_start=10,
        char_end=10 + len(text),
        text=text,
        score=1.5,
        rank=1,
        retriever="lexical",
    ).model_dump()


def test_provider_prose_is_not_published():
    # Published experiment results must not carry copied provider documentation.
    text = "413 - request_too_large: Request exceeds the maximum allowed number of bytes."
    redacted = redact_hit(make_hit(text))
    assert "text" not in redacted
    assert text not in str(redacted)


def test_anchor_fields_survive_redaction():
    # The analysis scores on these, so redaction must not cost us the evidence anchor.
    redacted = redact_hit(make_hit("some documentation prose"))
    for field in ("version_id", "section_path", "char_start", "char_end", "rank", "score"):
        assert field in redacted


def test_redacted_hit_still_identifies_the_chunk():
    text = "some documentation prose"
    redacted = redact_hit(make_hit(text))
    assert redacted["text_sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert redacted["text_len"] == len(text)
