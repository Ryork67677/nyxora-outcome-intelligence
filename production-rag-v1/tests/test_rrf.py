from rag_v1.retrieval import rrf_fuse
from rag_v1.types import SearchHit


def hit(cid, rank, retriever):
    return SearchHit(
        chunk_id=cid,
        version_id="v",
        section_path=["s"],
        char_start=0,
        char_end=1,
        text=cid,
        score=1.0,
        rank=rank,
        retriever=retriever,
    )


def test_rrf_rewards_cross_list_support():
    a = [hit("x", 1, "lexical"), hit("y", 2, "lexical")]
    b = [hit("y", 1, "dense"), hit("z", 2, "dense")]
    fused = rrf_fuse([a, b], rrf_k=10, top_k=3)
    assert fused[0].chunk_id == "y"
