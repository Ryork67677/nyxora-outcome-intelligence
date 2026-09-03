"""EXP-012 tests: hierarchy is only interpretable if routing is deterministic, the
scorers are untouched, and the oracle stays quarantined from the deployable cells.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag_v1.hierarchical import (
    DOCUMENT_RRF_K,
    collapse_to_documents,
    document_rank_of,
    fuse_document_rankings,
    routing_recall,
)
from rag_v1.types import SearchHit

RESULTS = Path("experiments/EXP-012/results.json")
SNAP = "snap_689e336380a054d8039dc35b2c09cd0a"
CHUNK_SET = "cs_v1_control"
MODEL = "emb_e7d4183fd6eb878ae2fdf080efb6861e"
FINGERPRINT = "bd95feaeacf98559"


def hit(chunk_id, version_id, rank, retriever="lexical"):
    return SearchHit(chunk_id=chunk_id, version_id=version_id, section_path=["S"],
                     char_start=0, char_end=10, text="t", score=1.0, rank=rank,
                     retriever=retriever)


@pytest.fixture(scope="module")
def payload():
    if not RESULTS.exists():
        pytest.skip("EXP-012 results not built")
    return json.loads(RESULTS.read_text())


# -- 1/3. document collapse --------------------------------------------------

def test_document_collapse_uses_the_highest_ranked_chunk():
    hits = [hit("c1", "docA", 1), hit("c2", "docA", 2), hit("c3", "docB", 3),
            hit("c4", "docC", 4)]
    assert collapse_to_documents(hits) == [("docA", 1), ("docB", 3), ("docC", 4)]


def test_a_document_is_never_counted_more_than_once():
    """Many mediocre chunks must not outvote one excellent chunk."""
    hits = [hit("c1", "docB", 1)] + [hit(f"a{i}", "docA", i) for i in range(2, 40)]
    collapsed = collapse_to_documents(hits)
    assert [v for v, _ in collapsed] == ["docB", "docA"]
    assert len(collapsed) == 2
    assert sum(1 for v, _ in collapsed if v == "docA") == 1


def test_document_collapse_is_deterministic_and_order_independent():
    hits = [hit("c3", "docB", 3), hit("c1", "docA", 1), hit("c2", "docA", 2)]
    assert collapse_to_documents(hits) == collapse_to_documents(list(reversed(hits)))


# -- 2. document RRF ---------------------------------------------------------

def test_document_rrf_is_deterministic():
    lists = [("bm25", [("a", 1), ("b", 5)]), ("transformer", [("b", 1), ("c", 2)])]
    first = fuse_document_rankings(lists, rrf_k=DOCUMENT_RRF_K)
    second = fuse_document_rankings(lists, rrf_k=DOCUMENT_RRF_K)
    assert [(e["version_id"], e["document_rank"], round(e["score"], 12)) for e in first] == \
           [(e["version_id"], e["document_rank"], round(e["score"], 12)) for e in second]


def test_document_rrf_scores_on_document_position_not_chunk_rank():
    """A retriever needing 40 chunks to reach its 2nd document still votes 2nd."""
    cheap = [("bm25", [("a", 1), ("b", 2)])]
    costly = [("bm25", [("a", 1), ("b", 400)])]
    assert (fuse_document_rankings(cheap)[1]["score"]
            == pytest.approx(fuse_document_rankings(costly)[1]["score"]))


def test_document_rrf_records_provenance():
    lists = [("bm25", [("a", 3)]), ("transformer", [("a", 7)])]
    entry = fuse_document_rankings(lists)[0]
    assert entry["contributing_sources"] == ["bm25", "transformer"]
    assert entry["source_positions"]["bm25_best_chunk_rank"] == 3
    assert entry["source_positions"]["transformer_best_chunk_rank"] == 7


def test_routing_recall_counts_expected_documents():
    ranking = [("a", 1), ("b", 2), ("c", 3)]
    assert routing_recall(ranking, {"a"}, depths=(1, 3))["1"] == 1.0
    assert routing_recall(ranking, {"c"}, depths=(1, 3))["1"] == 0.0
    assert routing_recall(ranking, {"a", "c"}, depths=(1, 3))["3"] == 1.0
    assert document_rank_of(ranking, "b") == 2
    assert document_rank_of(ranking, "zzz") is None


# -- 4. routing reproducibility ----------------------------------------------

def test_top_n_routing_is_reproducible(payload):
    for row in payload["routing"]["per_case"]:
        assert len(row["selected_documents"]) <= payload["top_documents"]
        assert len(set(row["selected_documents"])) == len(row["selected_documents"])


# -- 5. leakage --------------------------------------------------------------

def test_primary_routing_never_reads_golden_document_identifiers():
    """Only the oracle cell may use expected documents."""
    source = Path("src/rag_v1/hierarchical.py").read_text()
    for banned in ("expected_evidence", "load_cases", "golden", "evals"):
        assert banned not in source, f"routing module references {banned!r}"


def test_oracle_is_declared_non_deployable_and_excluded_from_configurations(payload):
    oracle = payload["oracle_diagnostic"]
    assert oracle["deployable"] is False
    assert oracle["uses_golden_document"] is True
    assert "ORACLE" in oracle["description"]
    assert "NOT DEPLOYABLE" in oracle["description"]
    # It must not be one of the deployable cells.
    assert "ORACLE" not in payload["configurations"]
    for key in payload["configurations"]:
        assert "oracle" not in key.lower()


def test_deployable_cells_carry_no_oracle_document_field(payload):
    for key, cfg in payload["configurations"].items():
        for case in cfg["cases"].values():
            assert "oracle_documents" not in case, f"{key} leaked oracle documents"


# -- 6. local candidate membership -------------------------------------------

def test_local_candidates_belong_only_to_selected_documents(payload):
    psycopg = pytest.importorskip("psycopg")
    from rag_v1.db import connect

    cases = payload["configurations"]["D_fused_hierarchical"]["cases"]
    try:
        with connect() as conn, conn.cursor() as cur:
            for case in list(cases.values())[:6]:
                selected = set(case["selected_documents"])
                ids = [s["chunk_id"] for s in case["spans"] if s["chunk_id"]]
                if not ids:
                    continue
                cur.execute("SELECT DISTINCT version_id FROM chunk WHERE chunk_id = ANY(%s)", (ids,))
                for (version_id,) in cur.fetchall():
                    assert version_id in selected, (
                        f"{case['case_id']} returned a chunk from an unrouted document"
                    )
    except psycopg.OperationalError:
        pytest.skip("database unavailable")


# -- 7. corpus statistics retained -------------------------------------------

def test_restricting_documents_does_not_change_bm25_scores():
    """The whole design rests on this: topology changes, statistics do not."""
    psycopg = pytest.importorskip("psycopg")
    from rag_v1.retrieval import lexical_search

    query = "What is the maximum number of requests in a batch?"
    try:
        global_hits = lexical_search(query, SNAP, 30)
    except psycopg.OperationalError:
        pytest.skip("database unavailable")
    if not global_hits:
        pytest.skip("no lexical hits")

    target = global_hits[0].version_id
    restricted = lexical_search(query, SNAP, 30, version_ids=[target])
    by_id = {h.chunk_id: h.score for h in restricted}
    compared = 0
    for hit_ in global_hits:
        if hit_.version_id == target and hit_.chunk_id in by_id:
            assert by_id[hit_.chunk_id] == hit_.score, (
                f"{hit_.chunk_id} scored differently once documents were restricted"
            )
            compared += 1
    assert compared > 0, "no overlapping chunk to compare"


def test_local_idf_is_not_recomputed_in_the_declared_config(payload):
    assert "full corpus" in payload["bm25_config"]["statistics"]
    assert payload["bm25_config"]["k1"] == 1.2
    assert payload["bm25_config"]["b"] == 0.75


# -- 8. determinism of the whole pipeline ------------------------------------

def test_selected_documents_are_a_prefix_of_the_fused_document_ranking(payload):
    for row in payload["routing"]["per_case"]:
        for version_id, rank in row["fused_document_rank"].items():
            if rank is not None and rank <= payload["top_documents"]:
                assert version_id in row["selected_documents"]


# -- 9. evidence anchoring ---------------------------------------------------

def test_evidence_is_still_anchored_on_source_spans(payload):
    for cfg in payload["configurations"].values():
        for case in cfg["cases"].values():
            for span in case["spans"]:
                assert "section_path" in span
                assert isinstance(span["span"], list) and len(span["span"]) == 2


def test_span_totals_are_unchanged(payload):
    for cfg in payload["configurations"].values():
        assert cfg["spans_total"] == 22
        assert cfg["cases_total"] == 20


# -- 10. complementarity tracing ---------------------------------------------

def test_fusion_bonus_is_reported_for_the_hierarchical_topology(payload):
    bonus = payload["fusion_bonus"]["hierarchical"]
    assert bonus["best_component"] == max(bonus["bm25_alone"], bonus["transformer_alone"])
    assert bonus["fusion_bonus_cases"] == bonus["fused"] - bonus["best_component"]


# -- 12. reproduction --------------------------------------------------------

def test_exp012a_reproduces_the_global_control(payload):
    gate = payload["reproduction_gate"]["A_global_raw_hybrid"]
    assert gate["reproduced"], gate["checks"]
    cfg = payload["configurations"]["A_global_raw_hybrid"]
    assert cfg["macro_span_recall"] == 0.775
    assert cfg["cases_fully_recalled"] == 15
    assert cfg["spans_found_at_10"] == 17


def test_frozen_configuration_is_declared(payload):
    assert payload["chunk_set"] == CHUNK_SET
    assert payload["corpus_snapshot"] == SNAP
    assert payload["transformer_fingerprint"] == FINGERPRINT
    assert payload["embedding_model"]["model_id"] == MODEL
    assert payload["document_rrf_k"] == 60 and payload["passage_rrf_k"] == 60
    assert payload["top_k"] == 10 and payload["candidate_pool"] == 50
    cfg = payload["retrieval_config"]
    assert cfg["reranker"] is None and cfg["cross_encoder"] is None
    assert cfg["query_rewriting"] is False and cfg["enrichment"] is None
    assert cfg["metadata_filtering"] is False and cfg["ann_index"] is False
    assert "raw user question" in payload["query"]


def test_stage1_ceiling_is_reported_and_consistent(payload):
    stage1 = payload["routing"]["stage1_ceiling"]
    assert stage1["cases_total"] == 20
    assert stage1["max_possible_recall_if_stage2_were_perfect"] == pytest.approx(
        stage1["cases_with_all_expected_documents_routed"] / stage1["cases_total"]
    )
    assert len(stage1["cases_with_a_document_outside_top_n"]) == (
        stage1["cases_total"] - stage1["cases_with_all_expected_documents_routed"]
    )


def test_every_persistent_failure_is_classified(payload):
    valid = {"DOCUMENT_ROUTING_FAILURE", "GLOBAL_COMPETITION_FAILURE",
             "WITHIN_DOCUMENT_PASSAGE_RANKING_FAILURE", "MIXED_OR_UNCLEAR"}
    control = payload["configurations"]["A_global_raw_hybrid"]["cases"]
    failing = {cid for cid, c in control.items() if not c["fully_recalled"]}
    assert set(payload["failure_taxonomy"]) == failing
    for entry in payload["failure_taxonomy"].values():
        assert entry["classification"] in valid
