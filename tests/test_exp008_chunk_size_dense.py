"""EXP-008 tests: the 2x2 is only an isolation of chunk size if nothing else moved.

Each test here pins one invariant the C -> D conclusion depends on.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

CONTROL_SET = "cs_v1_control"
BOUNDED_SET = "cs_2722bf8b72dcf3eb404336d7"
MODEL_ID = "emb_c11d8d9184d2ebc1ac60801a6452b884"
CONTROL_SNAP = "snap_689e336380a054d8039dc35b2c09cd0a"
BOUNDED_SNAP = "snap_95215379baa1d8460315986d9745dc0c"
RESULTS = Path("experiments/EXP-008/results.json")
HARD_MAX = 2000


@pytest.fixture(scope="module")
def cursor():
    psycopg = pytest.importorskip("psycopg")
    from rag_v1.db import connect

    try:
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM chunk_embedding ce JOIN chunk c ON c.chunk_id=ce.chunk_id "
                "WHERE ce.model_id=%s AND c.chunk_set_id=%s",
                (MODEL_ID, BOUNDED_SET),
            )
            if cur.fetchone()[0] == 0:
                pytest.skip("bounded embeddings not built")
            yield cur
    except psycopg.OperationalError:
        pytest.skip("database unavailable")


def _one(cursor, sql, params):
    cursor.execute(sql, params)
    return cursor.fetchone()[0]


def test_both_chunk_sets_use_the_same_embedding_model(cursor):
    # If the model differed, C -> D would confound representation with chunking.
    # The control set also still carries vectors from the superseded EXP-001 LSA
    # model; that is preserved history, so this pins the EXP-008 model specifically
    # rather than asserting only one model has ever existed.
    for chunk_set in (CONTROL_SET, BOUNDED_SET):
        fingerprints = _one(
            cursor,
            """
            SELECT count(DISTINCT ce.model_fingerprint) FROM chunk_embedding ce
            JOIN chunk c ON c.chunk_id=ce.chunk_id
            WHERE c.chunk_set_id=%s AND ce.model_id=%s
            """,
            (chunk_set, MODEL_ID),
        )
        assert fingerprints == 1, chunk_set

    cursor.execute(
        "SELECT model_name, dimension FROM embedding_model WHERE model_id=%s", (MODEL_ID,)
    )
    assert cursor.fetchone() == ("fasttext-wiki-news-subwords-300", 300)


def test_every_bounded_chunk_is_embedded(cursor):
    chunks = _one(cursor, "SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (BOUNDED_SET,))
    embedded = _one(
        cursor,
        "SELECT count(*) FROM chunk_embedding ce JOIN chunk c ON c.chunk_id=ce.chunk_id "
        "WHERE ce.model_id=%s AND c.chunk_set_id=%s",
        (MODEL_ID, BOUNDED_SET),
    )
    assert embedded == chunks


def test_no_enrichment_enters_the_embedded_text(cursor):
    # Dense text must be the canonical body. EXP-006 enrichment lives in search_text.
    for chunk_set in (CONTROL_SET, BOUNDED_SET):
        enriched = _one(
            cursor,
            """
            SELECT count(*) FROM chunk_embedding ce JOIN chunk c ON c.chunk_id=ce.chunk_id
            WHERE ce.model_id=%s AND c.chunk_set_id=%s
              AND (c.search_text IS NOT NULL OR c.context_header IS NOT NULL)
            """,
            (MODEL_ID, chunk_set),
        )
        assert enriched == 0, chunk_set


def test_bounded_chunks_obey_the_hard_limit(cursor):
    oversized = _one(
        cursor,
        "SELECT count(*) FROM chunk WHERE chunk_set_id=%s AND char_end-char_start > %s",
        (BOUNDED_SET, HARD_MAX),
    )
    assert oversized == 0


def test_same_evidence_spans_map_in_both_chunk_sets(cursor):
    from rag_v1.evals.io import load_cases

    cases = load_cases(Path("evals/golden/v1.jsonl"))
    refs = [r for c in cases for r in c.expected_evidence]
    for chunk_set in (CONTROL_SET, BOUNDED_SET):
        mapped = 0
        for ref in refs:
            cursor.execute(
                """
                SELECT count(*) FROM chunk WHERE chunk_set_id=%s AND version_id=%s
                  AND section_path=%s AND char_start<%s AND char_end>%s
                """,
                (chunk_set, ref.version_id, ref.section_path, ref.char_end, ref.char_start),
            )
            mapped += 1 if cursor.fetchone()[0] else 0
        assert mapped == len(refs), chunk_set


def test_embedding_cache_key_includes_content_hash_and_model_fingerprint(cursor):
    stale = _one(
        cursor,
        """
        SELECT count(*) FROM chunk_embedding ce JOIN chunk c ON c.chunk_id=ce.chunk_id
        WHERE ce.model_id=%s AND (ce.content_hash IS DISTINCT FROM c.content_hash
                                  OR ce.model_fingerprint IS NULL)
        """,
        (MODEL_ID,),
    )
    assert stale == 0


def test_no_evaluation_query_text_is_stored_as_a_document(cursor):
    questions = [
        json.loads(line)["question"]
        for line in Path("evals/golden/v1.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    leaked = _one(
        cursor,
        """
        SELECT count(*) FROM chunk_embedding ce JOIN chunk c ON c.chunk_id=ce.chunk_id
        WHERE ce.model_id=%s AND c.text = ANY(%s)
        """,
        (MODEL_ID, questions),
    )
    assert leaked == 0


def test_dense_ranking_is_deterministic_on_bounded_chunks(cursor):
    from rag_v1.retrieval import dense_search

    question = "How many requests can a single Message Batches create request contain at most?"
    first = [h.chunk_id for h in dense_search(question, BOUNDED_SNAP, MODEL_ID, 30)]
    second = [h.chunk_id for h in dense_search(question, BOUNDED_SNAP, MODEL_ID, 30)]
    assert first == second


def test_exact_search_only_no_ann_index(cursor):
    # Passing no parameters keeps psycopg from reading the LIKE wildcards as
    # placeholders ('%h' is not a valid one).
    cursor.execute(
        """
        SELECT count(*) FROM pg_indexes WHERE tablename='chunk_embedding'
          AND (indexdef ILIKE '%hnsw%' OR indexdef ILIKE '%ivfflat%')
        """
    )
    assert cursor.fetchone()[0] == 0


@pytest.mark.skipif(not RESULTS.exists(), reason="EXP-008 not run")
def test_cells_differ_only_in_intended_variables():
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    cells = data["configurations"]
    # Columns differ in chunk set; rows differ in retriever. Nothing else varies.
    assert cells["A_control_bm25"]["chunk_set_id"] == cells["C_control_dense"]["chunk_set_id"]
    assert cells["B_bounded_bm25"]["chunk_set_id"] == cells["D_bounded_dense"]["chunk_set_id"]
    assert cells["A_control_bm25"]["retriever"] == cells["B_bounded_bm25"]["retriever"] == "bm25"
    assert cells["C_control_dense"]["retriever"] == cells["D_bounded_dense"]["retriever"] == "dense"
    assert data["retrieval_config"]["enrichment"] is None
    assert data["retrieval_config"]["reranker"] is None
    assert data["retrieval_config"]["query_rewriting"] is False
    assert data["retrieval_config"]["stemming"] is False


@pytest.mark.skipif(not RESULTS.exists(), reason="EXP-008 not run")
def test_reproduction_gates_hold():
    cells = json.loads(RESULTS.read_text(encoding="utf-8"))["configurations"]
    # A reproduces the frozen BM25 baseline, B reproduces EXP-005A, C reproduces EXP-007B.
    assert cells["A_control_bm25"]["macro_span_recall"] == 0.475
    assert cells["A_control_bm25"]["cases_fully_recalled"] == 9
    assert cells["B_bounded_bm25"]["macro_span_recall"] == 0.500
    assert cells["C_control_dense"]["macro_span_recall"] == 0.425
    assert cells["C_control_dense"]["cases_fully_recalled"] == 8


@pytest.mark.skipif(not RESULTS.exists(), reason="EXP-008 not run")
def test_artifact_has_required_reproducibility_fields():
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    for field in ("experiment_id", "git_commit", "config_hash", "corpus_snapshots", "chunk_sets",
                  "embedding_model", "embedding_fingerprint", "distance_metric", "top_k",
                  "probe_depths", "configurations", "paired_comparison", "interaction_analysis",
                  "evidence_anchors", "runtime_seconds", "errors"):
        assert field in data, f"missing artifact field: {field}"
