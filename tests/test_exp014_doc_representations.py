"""EXP-014 tests: document representations must be deterministic, correctly
normalised, blind to the evaluation set, and must not disturb Stage 2.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from rag_v1.doc_representations import (
    REPRESENTATION_VERSION,
    REPRESENTATIONS,
    build,
    chunk_vectors_are_normalised,
)

RESULTS = Path("experiments/EXP-014/results.json")
SNAP = "snap_689e336380a054d8039dc35b2c09cd0a"
CHUNK_SET = "cs_v1_control"
MODEL = "emb_e7d4183fd6eb878ae2fdf080efb6861e"
FINGERPRINT = "bd95feaeacf98559"


def unit(*values: float) -> np.ndarray:
    v = np.array(values, dtype=np.float32)
    return v / np.linalg.norm(v)


def rows_fixture() -> list[tuple]:
    """Two documents: one with a lopsided section, one balanced."""
    return [
        # docA: three chunks in section X (all identical content), one in section Y
        ("docA", ("X",), "hash-x", unit(1, 0, 0)),
        ("docA", ("X",), "hash-x", unit(1, 0, 0)),
        ("docA", ("X",), "hash-x", unit(1, 0, 0)),
        ("docA", ("Y",), "hash-y", unit(0, 1, 0)),
        # docB: one chunk per section
        ("docB", ("P",), "hash-p", unit(0, 0, 1)),
        ("docB", ("Q",), "hash-q", unit(0, 1, 1)),
    ]


@pytest.fixture(scope="module")
def payload():
    if not RESULTS.exists():
        pytest.skip("EXP-014 results not built")
    return json.loads(RESULTS.read_text())


# -- 1-3. construction determinism and duplicate handling --------------------

@pytest.mark.parametrize("name", sorted(REPRESENTATIONS))
def test_construction_is_deterministic(name):
    rows = rows_fixture()
    first, second = build(name, rows), build(name, rows)
    assert first.version_ids == second.version_ids
    assert np.array_equal(first.matrix, second.matrix)
    assert first.vector_hashes() == second.vector_hashes()


@pytest.mark.parametrize("name", sorted(REPRESENTATIONS))
def test_construction_is_independent_of_row_order(name):
    rows = rows_fixture()
    shuffled = list(reversed(rows))
    a, b = build(name, rows), build(name, shuffled)
    assert a.version_ids == b.version_ids
    assert np.allclose(a.matrix, b.matrix, atol=1e-6)


def test_doc_b_removes_exact_duplicate_chunk_content():
    rows = rows_fixture()
    index = build("DOC-B-CENTROID", rows)
    # docA has three byte-identical chunks in section X; two must be dropped.
    assert index.stats["duplicate_chunks_removed"] == 2


def test_doc_b_differs_from_doc_a_when_duplicates_exist():
    """If dedup changed nothing on this fixture the test would be vacuous."""
    rows = rows_fixture()
    a = build("DOC-A-MEAN", rows)
    b = build("DOC-B-CENTROID", rows)
    doc_a_index = a.version_ids.index("docA")
    assert not np.allclose(a.matrix[doc_a_index], b.matrix[doc_a_index], atol=1e-6)


# -- 4. equal section contribution -------------------------------------------

def test_doc_c_gives_every_section_one_vote():
    """docA's three identical X chunks must not outweigh its single Y chunk."""
    rows = rows_fixture()
    index = build("DOC-C-SECTION", rows)
    vector = index.matrix[index.version_ids.index("docA")]
    # X = (1,0,0), Y = (0,1,0); equal weight means the two components match.
    assert vector[0] == pytest.approx(vector[1], abs=1e-6)

    mean_index = build("DOC-A-MEAN", rows)
    mean_vector = mean_index.matrix[mean_index.version_ids.index("docA")]
    # The plain mean is dominated by the repeated section.
    assert mean_vector[0] > mean_vector[1]


def test_doc_c_is_unaffected_by_duplicate_chunks_within_a_section():
    rows = rows_fixture()
    without_dupes = [r for i, r in enumerate(rows) if i not in (1, 2)]
    a = build("DOC-C-SECTION", rows)
    b = build("DOC-C-SECTION", without_dupes)
    assert np.allclose(a.matrix, b.matrix, atol=1e-6)


# -- 5. multi-vector scoring --------------------------------------------------

def test_doc_d_scores_a_document_at_its_best_section():
    rows = rows_fixture()
    index = build("DOC-D-MULTIVECTOR", rows)
    query = unit(0, 1, 0)  # matches docA's section Y exactly
    scores = index.score(query)
    assert scores["docA"] == pytest.approx(1.0, abs=1e-5)


def test_doc_d_keeps_one_vector_per_section():
    index = build("DOC-D-MULTIVECTOR", rows_fixture())
    assert index.section_vectors["docA"].shape[0] == 2   # sections X and Y
    assert index.section_vectors["docB"].shape[0] == 2   # sections P and Q
    assert index.stats["section_vectors_total"] == 4


def test_doc_d_ranking_is_deterministic():
    index = build("DOC-D-MULTIVECTOR", rows_fixture())
    query = unit(1, 1, 1)
    assert index.ranking(query) == index.ranking(query)


# -- 6. normalisation ---------------------------------------------------------

@pytest.mark.parametrize("name", sorted(REPRESENTATIONS))
def test_document_vectors_are_unit_length(name):
    index = build(name, rows_fixture())
    norms = np.linalg.norm(index.matrix, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)
    if index.section_vectors:
        for vectors in index.section_vectors.values():
            assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-5)


def test_stored_chunk_vectors_were_verified_unit_length(payload):
    check = payload["chunk_vector_normalisation"]
    assert check["all_unit_length"] is True
    assert check["chunks_checked"] == 14209


def test_normalisation_checker_detects_unnormalised_input():
    bad = [("d", ("S",), "h", np.array([3.0, 4.0], dtype=np.float32))]
    assert chunk_vectors_are_normalised(bad)["all_unit_length"] is False


# -- 7. no evaluation leakage -------------------------------------------------

def test_representation_module_cannot_see_the_evaluation_set():
    source = Path("src/rag_v1/doc_representations.py").read_text()
    for banned in ("golden", "evals", "load_cases", "expected_evidence", "case_id"):
        assert banned not in source, f"representation module references {banned!r}"


def test_representations_are_built_before_any_query_is_seen(payload):
    """Construction depends only on the corpus, so one index serves every query."""
    for name, stats in payload["representations"].items():
        assert stats["documents"] == 202, name
        assert stats["dimension"] == 384


def test_oracle_stays_out_of_deployable_configurations(payload):
    oracle = payload["oracle_diagnostic"]
    assert oracle["deployable"] is False
    assert oracle["uses_golden_document"] is True
    assert "NOT DEPLOYABLE" in oracle["description"]
    assert "ORACLE" not in payload["configurations"]
    for key, cfg in payload["configurations"].items():
        for case in cfg["cases"].values():
            assert "oracle_documents" not in case, f"{key} leaked oracle documents"


# -- 8. multi-hop accounting --------------------------------------------------

def test_multi_hop_cases_need_every_expected_document(payload):
    multi = [cid for cid, w in payload["case_watchlist"].items() if w["multi_hop"]]
    assert multi, "no multi-hop case found — the accounting test would be vacuous"
    for label, rows in payload["routing_per_case"].items():
        for row in rows:
            if row["case_id"] not in multi:
                continue
            for depth in ("1", "3", "5", "10"):
                # all_routed can only be true when recall is complete.
                assert row["all_routed"][depth] == (row["recall"][depth] == 1.0), label


def test_routing_summary_matches_the_per_case_rows(payload):
    for label, summary in payload["routing_quality"].items():
        if label == "chunk_derived_router":
            continue
        rows = payload["routing_per_case"][label]
        for depth in ("1", "3", "5", "10"):
            assert summary["all_expected_routed"][depth] == sum(
                1 for r in rows if r["all_routed"][depth])
        assert summary["stage1_ceiling_at_5"] == pytest.approx(
            summary["all_expected_routed"]["5"] / summary["cases_total"])


# -- 9. deterministic document RRF -------------------------------------------

def test_document_rrf_is_deterministic_and_emits_each_document_once():
    from rag_v1.routers import rrf_document_lists

    lists = [("doc", [("A", 1), ("B", 1)]), ("chunk", [("B", 3), ("A", 7)])]
    first = rrf_document_lists(lists, k=60)
    second = rrf_document_lists(lists, k=60)
    assert [(e["version_id"], e["document_rank"]) for e in first] == \
           [(e["version_id"], e["document_rank"]) for e in second]
    ids = [e["version_id"] for e in first]
    assert len(ids) == len(set(ids)) == 2


# -- 10-12. frozen system ----------------------------------------------------

def test_stage2_and_query_are_declared_frozen(payload):
    assert "FROZEN" in payload["stage2"]
    assert payload["query"] == "raw user question only"
    assert payload["passage_rrf_k"] == 60 and payload["candidate_pool"] == 50
    assert payload["top_k"] == 10 and payload["top_documents"] == 5
    cfg = payload["retrieval_config"]
    assert cfg["reranker"] is None and cfg["cross_encoder"] is None
    assert cfg["query_rewriting"] is False and cfg["enrichment"] is None
    assert cfg["metadata_filtering"] is False and cfg["ann_index"] is False


def test_bm25_statistics_unchanged(payload):
    assert payload["bm25_config"]["k1"] == 1.2 and payload["bm25_config"]["b"] == 0.75
    assert "full corpus" in payload["bm25_config"]["statistics"]


def test_transformer_fingerprint_and_inputs_unchanged(payload):
    assert payload["transformer_fingerprint"] == FINGERPRINT
    assert payload["embedding_model"]["model_id"] == MODEL
    assert payload["chunk_set"] == CHUNK_SET
    assert payload["corpus_snapshot"] == SNAP
    assert payload["similarity_metric"] == "cosine"


def test_no_new_embedding_model_was_introduced():
    source = Path("src/rag_v1/doc_representations.py").read_text()
    for banned in ("TransformerEncoder", "sentence_transformers", "requests", "urllib", "http"):
        assert banned not in source, f"representation module reaches for {banned!r}"


# -- 13. reproduction ---------------------------------------------------------

def test_all_reproduction_gates_pass(payload):
    failed = {k: v["checks"] for k, v in payload["reproduction_gate"].items()
              if not v["reproduced"]}
    assert not failed, f"reproduction gates failed: {failed}"


def test_global_control_and_oracle_reproduce(payload):
    control = payload["configurations"]["GLOBAL_control"]
    assert control["macro_span_recall"] == 0.775
    assert control["cases_fully_recalled"] == 15
    assert control["spans_found_at_10"] == 17
    oracle = payload["oracle_diagnostic"]
    assert oracle["macro_span_recall"] == 0.95
    assert oracle["cases_fully_recalled"] == 19


def test_chunk_derived_router_reproduces_exp013(payload):
    gate = payload["reproduction_gate"]["chunk_derived_router"]
    assert gate["checks"]["document_recall_at_5"]["actual"] == 0.875
    assert gate["checks"]["all_routed_at_5"]["actual"] == 17


# -- 14/15. config hashing and caching ---------------------------------------

def test_config_hash_and_version_are_recorded(payload):
    assert isinstance(payload["config_hash"], str) and len(payload["config_hash"]) >= 16
    assert payload["document_representation_version"] == REPRESENTATION_VERSION


def test_every_representation_records_reproducible_provenance(payload):
    for name, stats in payload["representations"].items():
        assert name in REPRESENTATIONS
        assert stats["vectors_stored"] >= 202
        assert stats["storage_bytes"] > 0
        assert stats["build_seconds"] >= 0
        assert stats["vector_hash_sample"], name


def test_query_embeddings_are_cached_across_representations(payload):
    cache = payload["query_embedding_cache"]
    assert cache["model_fingerprint"] == FINGERPRINT
    # One embedding per distinct question, reused by every representation.
    assert cache["query_embedding_cache_hits"] > 0
