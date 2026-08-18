"""EXP-007 tests: pretrained embedding identity, caching, and experiment fidelity.

The EXP-007 conclusions rest on three claims that must be mechanically checked:
the embedder is pretrained and not fitted to this corpus, its cache invalidates on
a model change, and the frozen lexical control still reproduces.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag_v1.embedders_pretrained import (
    MODEL_CARD,
    PretrainedWordVectorEmbedder,
    lookup_forms,
    tokenize,
)

CONTROL_CHUNK_SET = "cs_v1_control"
MODEL_ID = "emb_c11d8d9184d2ebc1ac60801a6452b884"
RESULTS = Path("experiments/EXP-007/results.json")


# --------------------------------------------------------------------- encoder


def test_model_card_declares_it_is_not_corpus_fitted():
    # The whole point of EXP-007: the earlier LSA encoder was fitted on this corpus
    # and therefore could not test the vocabulary-mismatch hypothesis.
    assert MODEL_CARD["corpus_fitted"] is False
    assert MODEL_CARD["model_identifier"] == "fasttext-wiki-news-subwords-300"
    assert MODEL_CARD["dimension"] == 300
    assert MODEL_CARD["distance_metric"] == "cosine"


def test_model_version_changes_when_the_model_card_changes():
    # A different model must produce a different fingerprint, or stale vectors
    # would be silently reused across models.
    a = PretrainedWordVectorEmbedder()
    b = PretrainedWordVectorEmbedder()
    assert a.model_version == b.model_version

    original = MODEL_CARD["model_identifier"]
    try:
        MODEL_CARD["model_identifier"] = "some-other-model"
        changed = PretrainedWordVectorEmbedder()
        assert changed.model_version != a.model_version
    finally:
        MODEL_CARD["model_identifier"] = original


def test_tokenizer_keeps_identifiers_whole_then_decomposes():
    assert "request_too_large" in tokenize("the request_too_large error")
    assert lookup_forms("request_too_large")[0] == "request_too_large"
    assert "request" in lookup_forms("request_too_large")
    # A plain word has no decomposition.
    assert lookup_forms("messages") == ["messages"]


def test_tokenizer_drops_punctuation_only_tokens():
    assert tokenize("-- ... !!") == []


# ----------------------------------------------------------------- live corpus


@pytest.fixture(scope="module")
def cursor():
    psycopg = pytest.importorskip("psycopg")
    from rag_v1.db import connect

    try:
        with connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM chunk_embedding WHERE model_id=%s", (MODEL_ID,))
            if cur.fetchone()[0] == 0:
                pytest.skip("pretrained embeddings not built")
            yield cur
    except psycopg.OperationalError:
        pytest.skip("database unavailable")


def test_embedding_cache_is_keyed_by_content_and_model(cursor):
    cursor.execute(
        """
        SELECT count(*) FROM chunk_embedding ce
        JOIN chunk c ON c.chunk_id = ce.chunk_id
        WHERE ce.model_id=%s AND ce.content_hash IS DISTINCT FROM c.content_hash
        """,
        (MODEL_ID,),
    )
    assert cursor.fetchone()[0] == 0, "cached vector no longer matches its chunk's content hash"


def test_every_control_chunk_is_embedded_exactly_once(cursor):
    cursor.execute("SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (CONTROL_CHUNK_SET,))
    chunks = cursor.fetchone()[0]
    cursor.execute(
        """
        SELECT count(*) FROM chunk_embedding ce
        JOIN chunk c ON c.chunk_id = ce.chunk_id
        WHERE ce.model_id=%s AND c.chunk_set_id=%s
        """,
        (MODEL_ID, CONTROL_CHUNK_SET),
    )
    assert cursor.fetchone()[0] == chunks


def test_embeddings_cover_only_unenriched_control_chunks(cursor):
    # EXP-007 freezes the corpus representation: control chunker, no enrichment.
    cursor.execute(
        """
        SELECT count(*) FROM chunk_embedding ce
        JOIN chunk c ON c.chunk_id = ce.chunk_id
        WHERE ce.model_id=%s AND (c.chunk_set_id <> %s OR c.search_text IS NOT NULL)
        """,
        (MODEL_ID, CONTROL_CHUNK_SET),
    )
    assert cursor.fetchone()[0] == 0, "an enriched or non-control chunk was embedded"


def test_no_evaluation_question_text_is_stored_as_a_document(cursor):
    # Questions may influence which pretrained vectors are loaded, never what is
    # embedded as a document.
    questions = [
        json.loads(line)["question"]
        for line in Path("evals/golden/v1.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    cursor.execute(
        """
        SELECT count(*) FROM chunk_embedding ce
        JOIN chunk c ON c.chunk_id = ce.chunk_id
        WHERE ce.model_id=%s AND c.text = ANY(%s)
        """,
        (MODEL_ID, questions),
    )
    assert cursor.fetchone()[0] == 0


def test_dense_search_has_no_ann_index_so_it_is_exact(cursor):
    # EXP-007 measures embedding quality, not ANN index quality.
    cursor.execute(
        """
        SELECT count(*) FROM pg_indexes
        WHERE tablename='chunk_embedding' AND (indexdef ILIKE '%hnsw%' OR indexdef ILIKE '%ivfflat%')
        """
    )
    assert cursor.fetchone()[0] == 0


def test_dense_ranking_is_deterministic(cursor):
    from rag_v1.retrieval import dense_search

    snapshot = "snap_689e336380a054d8039dc35b2c09cd0a"
    question = "How many requests can a single Message Batches create request contain at most?"
    first = [h.chunk_id for h in dense_search(question, snapshot, MODEL_ID, 25)]
    second = [h.chunk_id for h in dense_search(question, snapshot, MODEL_ID, 25)]
    assert first == second


def test_rrf_ordering_is_deterministic():
    from rag_v1.retrieval import rrf_fuse
    from rag_v1.types import SearchHit

    def hit(cid, rank, retriever):
        return SearchHit(chunk_id=cid, version_id="v", section_path=["s"], char_start=0,
                         char_end=1, text=cid, score=1.0, rank=rank, retriever=retriever)

    lex = [hit(f"a{i}", i, "lexical") for i in range(1, 11)]
    den = [hit(f"a{i}", 11 - i, "dense") for i in range(1, 11)]
    first = [h.chunk_id for h in rrf_fuse([lex, den], rrf_k=60, top_k=10)]
    second = [h.chunk_id for h in rrf_fuse([lex, den], rrf_k=60, top_k=10)]
    assert first == second


# ------------------------------------------------------------------- artifacts


@pytest.mark.skipif(not RESULTS.exists(), reason="EXP-007 not run")
def test_experiment_artifact_has_the_required_reproducibility_fields():
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    for field in (
        "experiment_id", "timestamp", "git_commit", "corpus_snapshot_id",
        "corpus_manifest_hash", "chunker", "chunk_config_hash", "parser_version",
        "embedding_model", "retrieval_config", "bm25_config", "rrf_config",
        "configurations", "paired_results", "probe_depth_results",
        "runtime_seconds", "errors", "config_hash",
    ):
        assert field in data, f"missing artifact field: {field}"

    model = data["embedding_model"]
    for field in ("model_id", "provider", "model_identifier", "revision", "dimension",
                  "pooling", "normalization", "distance_metric"):
        assert field in model, f"missing model field: {field}"

    assert data["rrf_config"]["preregistered"] is True
    assert data["rrf_config"]["tuned"] is False
    assert data["retrieval_config"]["reranker"] is None
    assert data["retrieval_config"]["query_rewriting"] is False
    assert data["chunker"]["enrichment"] is None


@pytest.mark.skipif(not RESULTS.exists(), reason="EXP-007 not run")
def test_bm25_control_reproduces_the_frozen_baseline():
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    control = data["configurations"]["EXP-007A_bm25_control"]
    assert control["macro_span_recall"] == 0.475
    assert control["cases_fully_recalled"] == 9
    assert control["spans_found_at_10"] == 10
