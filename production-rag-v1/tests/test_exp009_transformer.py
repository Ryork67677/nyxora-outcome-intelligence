"""EXP-009 tests: the B -> C comparison is only an encoder swap if nothing else moved.

Each test pins one invariant the conclusion depends on. Several exist because an
earlier version of this module got the invariant wrong: the truncation accounting
silently reported 0% truncation on a corpus whose largest chunk is 6,857 tokens,
because ``Tokenizer.from_file`` restores the tokenizer's own saved 128-token limit.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

CONTROL_SET = "cs_v1_control"
CONTROL_SNAP = "snap_689e336380a054d8039dc35b2c09cd0a"
TRANSFORMER_MODEL = "emb_5197b67ea29a78cce96e91054d01d1dd"
FASTTEXT_MODEL = "emb_c11d8d9184d2ebc1ac60801a6452b884"
RESULTS = Path("experiments/EXP-009/results.json")
VERIFICATION = Path("experiments/EXP-009/encoder-verification.json")


@pytest.fixture(scope="module")
def encoder():
    pytest.importorskip("onnxruntime")
    pytest.importorskip("tokenizers")
    from rag_v1.embedders_transformer import TransformerEncoder, model_dir

    if not (model_dir() / "model.onnx").exists():
        pytest.skip("EXP-009 transformer bundle not present")
    return TransformerEncoder().load()


@pytest.fixture(scope="module")
def results():
    if not RESULTS.exists():
        pytest.skip("EXP-009 has not been run")
    return json.loads(RESULTS.read_text())


@pytest.fixture(scope="module")
def cursor():
    pytest.importorskip("psycopg")
    from rag_v1.db import connect

    try:
        with connect() as conn, conn.cursor() as cur:
            yield cur
    except Exception:  # noqa: BLE001
        pytest.skip("database unavailable")


# -- the encoder itself ----------------------------------------------------


def test_model_card_declares_a_pretrained_uncfitted_transformer():
    from rag_v1.embedders_transformer import MODEL_CARD

    assert MODEL_CARD["corpus_fitted"] is False
    assert MODEL_CARD["contextual"] is True
    assert MODEL_CARD["dimension"] == 384
    # The provenance weakness must stay visible in the artifact, not be quietly dropped.
    assert MODEL_CARD["provenance_verified_against_publisher"] is False


def test_no_query_or_document_prefix_is_applied():
    """This model is symmetric. Inventing an instruction prefix would be tuning."""
    from rag_v1.embedders_transformer import MODEL_CARD

    assert MODEL_CARD["query_prefix"] is None
    assert MODEL_CARD["document_prefix"] is None


def test_vectors_are_l2_normalized(encoder):
    vecs = encoder.embed_array(["a rate limit error", "batch size limits"], batch_size=2)
    assert np.allclose(np.linalg.norm(vecs, axis=1), 1.0, atol=1e-5)


def test_encoding_is_deterministic_across_calls(encoder):
    probe = "How many requests can a batch contain?"
    assert np.array_equal(encoder.embed_array([probe])[0], encoder.embed_array([probe])[0])


def test_vector_does_not_depend_on_batch_mates(encoder):
    """Fixed-width padding exists so a chunk's vector is independent of its batch."""
    probe = "The rate limit error returns a 429 status code."
    alone = encoder.embed_array([probe], batch_size=1)[0]
    with_mates = encoder.embed_array(["filler", probe, "other text entirely"], batch_size=8)[1]
    assert np.array_equal(alone, with_mates)


def test_pooling_ignores_padding(encoder):
    """A masked mean must not average the [PAD] positions into the vector."""
    short = encoder.embed_array(["batch limit"], batch_size=1)[0]
    # If padding leaked into the mean, a short text's vector would be dominated by
    # ~250 identical pad vectors and every short text would look alike.
    other = encoder.embed_array(["completely unrelated subject matter"], batch_size=1)[0]
    assert float(short @ other) < 0.9


def test_truncation_accounting_uses_an_untruncated_tokenizer(encoder):
    """Regression test for the defect that reported 0% truncation on this corpus."""
    long_text = "rate limit error handling " * 900
    assert encoder._untruncated_length(long_text) > encoder.max_seq * 4


def test_max_seq_is_part_of_the_model_identity():
    """The same weights at 256 and 512 are two encoders and must not share a cache."""
    from rag_v1.embedders_transformer import TransformerEncoder

    assert TransformerEncoder(max_seq=256).model_version != TransformerEncoder(max_seq=512).model_version


def test_encoder_verification_passed():
    if not VERIFICATION.exists():
        pytest.skip("encoder verification has not been run")
    payload = json.loads(VERIFICATION.read_text())
    assert payload["passed"], payload["failures"]
    # The decisive check: a paraphrase with no shared content words must score high,
    # or this encoder cannot test the vocabulary-mismatch hypothesis at all.
    assert payload["behavioural"]["zero_overlap_pair_cosine"] > 0.4
    assert payload["behavioural"]["separation"] > 0.2


# -- the experiment --------------------------------------------------------


def test_frozen_baselines_reproduced(results):
    """A moved baseline voids the comparison, so this gate is not advisory."""
    for cell, gate in results["reproduction_gate"].items():
        assert gate["reproduced"], (cell, gate["checks"])


def test_transformer_embeddings_cover_exactly_the_control_chunks(cursor):
    cursor.execute(
        "SELECT count(*) FROM chunk_embedding ce JOIN chunk c ON c.chunk_id=ce.chunk_id "
        "WHERE ce.model_id=%s AND c.chunk_set_id<>%s",
        (TRANSFORMER_MODEL, CONTROL_SET),
    )
    assert cursor.fetchone()[0] == 0, "transformer embedded a chunk set it should not have"
    cursor.execute(
        "SELECT count(*) FROM chunk_embedding WHERE model_id=%s", (TRANSFORMER_MODEL,)
    )
    assert cursor.fetchone()[0] == 14209


def test_both_dense_cells_ran_on_the_same_chunks(results):
    """B and C differ in encoder only — same snapshot, same chunk set, same top_k."""
    assert results["chunk_set_id"] == CONTROL_SET
    assert results["corpus_snapshot_id"] == CONTROL_SNAP
    assert results["configurations"]["B_fasttext_control"]["retriever"] == "dense_fasttext"
    assert results["configurations"]["C_transformer_control"]["retriever"] == "dense_transformer"


def test_search_is_exact_with_no_ann_index(cursor):
    cursor.execute(
        "SELECT indexdef FROM pg_indexes WHERE tablename='chunk_embedding'"
    )
    defs = " ".join(row[0].lower() for row in cursor.fetchall())
    assert "hnsw" not in defs and "ivfflat" not in defs


def test_no_reranker_or_query_rewriting_was_introduced(results):
    cfg = results["retrieval_config"]
    assert cfg["reranker"] is None
    assert cfg["query_rewriting"] is False
    assert cfg["query_expansion"] is False
    assert cfg["stemming"] is False
    assert cfg["enrichment"] is None


def test_rrf_parameters_are_the_preregistered_ones(results):
    rrf = results["rrf_config"]
    assert (rrf["pool"], rrf["rrf_k"], rrf["top_k"]) == (50, 60, 10)
    assert rrf["tuned"] is False


def test_prior_experiment_artifacts_were_not_modified():
    """EXP-009 must not rewrite the record of an earlier experiment."""
    for path in ("experiments/EXP-007/results.json", "experiments/EXP-008/results.json"):
        payload = json.loads(Path(path).read_text())
        assert payload["experiment_id"] in ("EXP-007", "EXP-008")
    exp007 = json.loads(Path("experiments/EXP-007/results.json").read_text())
    assert exp007["configurations"]["EXP-007C_bm25_dense_rrf"]["macro_span_recall"] == 0.6
