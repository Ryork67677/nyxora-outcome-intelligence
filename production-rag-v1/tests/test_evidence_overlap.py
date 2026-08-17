from rag_v1.evals.retrieval_eval import score_evidence
from rag_v1.types import EvidenceRef, SearchHit


def test_evidence_scored_above_chunk_identity():
    ref = EvidenceRef(version_id="v1", section_path=["A"], char_start=100, char_end=150)
    hit = SearchHit(
        chunk_id="new_chunk_after_rechunk",
        version_id="v1",
        section_path=["A"],
        char_start=90,
        char_end=120,
        text="x",
        score=1.0,
        rank=1,
        retriever="test",
    )
    result = score_evidence([hit], [ref], "c", "exact_lookup", 10)
    assert result.recall == 1.0
