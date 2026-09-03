"""EXP-013 tests: routing conclusions only hold if the routers are deterministic,
Stage 2 is untouched, and the oracle stays out of the deployable metrics.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag_v1.routers import (
    DOCUMENT_RRF_K,
    RANK_SUM_K,
    RANK_SUM_SUPPORT_CHUNKS,
    ROUTER_PARAMETERS,
    VOTE_DEPTH,
    route,
    router_max,
    router_max_support,
    router_rank_sum,
    router_topk_vote,
    rrf_document_lists,
)
from rag_v1.types import SearchHit

RESULTS = Path("experiments/EXP-013/results.json")
SNAP = "snap_689e336380a054d8039dc35b2c09cd0a"
CHUNK_SET = "cs_v1_control"
MODEL = "emb_e7d4183fd6eb878ae2fdf080efb6861e"
FINGERPRINT = "bd95feaeacf98559"
ROUTERS = ("A_MAX", "B_RANK_SUM", "C_TOPK_VOTE", "D_MAX_SUPPORT")


def h(chunk_id, version_id, rank, retriever="lexical"):
    return SearchHit(chunk_id=chunk_id, version_id=version_id, section_path=["S"],
                     char_start=0, char_end=9, text="t", score=1.0, rank=rank,
                     retriever=retriever)


@pytest.fixture(scope="module")
def payload():
    if not RESULTS.exists():
        pytest.skip("EXP-013 results not built")
    return json.loads(RESULTS.read_text())


# -- 1. best-chunk control ---------------------------------------------------

def test_router_a_reproduces_the_best_chunk_rule():
    hits = [h("b1", "B", 1), h("a1", "A", 2), h("a2", "A", 7), h("b2", "B", 150)]
    assert router_max(hits) == [("B", 1), ("A", 2)]


def test_router_a_matches_the_exp012_collapse_function():
    from rag_v1.hierarchical import collapse_to_documents

    hits = [h("b1", "B", 1), h("a1", "A", 2), h("a2", "A", 7), h("c1", "C", 3)]
    assert router_max(hits) == collapse_to_documents(hits)


# -- 2/3/4. aggregation determinism ------------------------------------------

def test_rank_sum_rewards_broad_support_over_a_single_best_chunk():
    """The motivating example: A has four good chunks, B owns rank 1 and nothing else."""
    hits = [h("b1", "B", 1), h("a1", "A", 2), h("a2", "A", 7), h("a3", "A", 11),
            h("a4", "A", 18), h("b2", "B", 150), h("b3", "B", 270)]
    assert router_max(hits)[0][0] == "B"
    assert router_rank_sum(hits)[0][0] == "A"
    assert router_topk_vote(hits)[0][0] == "A"


def test_rank_sum_counts_only_the_top_supporting_chunks():
    """Chunks beyond the cap contribute nothing, so document length is bounded.

    Note what this does *not* claim: the cap does not make two excellent chunks beat
    five mediocre ones. Rank-sum deliberately rewards breadth, and that is visible in
    the measured result — its routed pools are nearly twice the size of the
    best-chunk router's. The cap bounds how far that goes, no more.
    """
    truncated = [h(f"l{i}", "LONG", i) for i in range(20, 20 + RANK_SUM_SUPPORT_CHUNKS)]
    padded = truncated + [h(f"x{i}", "LONG", i) for i in range(100, 140)]
    assert router_rank_sum(truncated) == router_rank_sum(padded)


def test_rank_sum_prefers_breadth_which_is_the_whole_point():
    few_excellent = [h("s1", "SHORT", 1), h("s2", "SHORT", 2)]
    many_good = [h(f"l{i}", "LONG", i) for i in range(20, 25)]
    assert router_max(few_excellent + many_good)[0][0] == "SHORT"
    assert router_rank_sum(few_excellent + many_good)[0][0] == "LONG"


@pytest.mark.parametrize("fn", [router_max, router_rank_sum, router_topk_vote])
def test_router_output_is_deterministic_and_order_independent(fn):
    hits = [h("a1", "A", 3), h("b1", "B", 1), h("a2", "A", 5), h("c1", "C", 2)]
    assert fn(hits) == fn(list(reversed(hits)))
    assert fn(hits) == fn(hits)


def test_ties_are_broken_deterministically_not_by_input_order():
    """Two documents with identical support must order by best chunk then id."""
    hits = [h("x1", "zeta", 4), h("y1", "alpha", 4)]
    assert [v for v, _ in router_rank_sum(hits)] == ["alpha", "zeta"]
    assert [v for v, _ in router_topk_vote(hits)] == ["alpha", "zeta"]


def test_vote_router_ignores_chunks_below_the_vote_depth():
    inside = [h(f"a{i}", "A", i) for i in range(1, VOTE_DEPTH + 1)]
    outside = [h(f"b{i}", "B", i) for i in range(VOTE_DEPTH + 1, VOTE_DEPTH + 60)]
    ranking = router_topk_vote(inside + outside)
    assert ranking[0][0] == "A"
    # B has more chunks overall but none inside the depth, so it scores zero votes.
    assert [v for v, _ in ranking] == ["A", "B"]


def test_max_support_fuses_four_rank_domain_lists():
    lex = [h("a1", "A", 1), h("b1", "B", 2)]
    den = [h("b2", "B", 1), h("a2", "A", 2)]
    fused = router_max_support(lex, den)
    assert {e["version_id"] for e in fused} == {"A", "B"}
    sources = set(fused[0]["contributing_sources"])
    assert sources == {"bm25_max", "bm25_support", "transformer_max", "transformer_support"}


def test_max_support_never_combines_raw_scores():
    """Score-scale mixing is the failure mode this router exists to avoid."""
    source = Path("src/rag_v1/routers.py").read_text()
    for banned in ("hit.score +", "score +=  hit.score", "bm25_score", "cosine_score"):
        assert banned not in source


# -- 5. one document, one entry ----------------------------------------------

@pytest.mark.parametrize("fn", [router_max, router_rank_sum, router_topk_vote])
def test_a_document_appears_exactly_once_in_the_output(fn):
    hits = [h(f"a{i}", "A", i) for i in range(1, 30)] + [h("b1", "B", 40)]
    ranking = fn(hits)
    versions = [v for v, _ in ranking]
    assert len(versions) == len(set(versions)) == 2


def test_document_rrf_emits_each_document_once():
    lists = [("x", [("A", 1), ("B", 2)]), ("y", [("A", 3), ("B", 1)])]
    fused = rrf_document_lists(lists, k=DOCUMENT_RRF_K)
    ids = [e["version_id"] for e in fused]
    assert ids == sorted(set(ids), key=ids.index)
    assert len(ids) == 2
    assert [e["document_rank"] for e in fused] == [1, 2]


def test_route_returns_fused_ranking_and_its_components():
    lex = [h("a1", "A", 1)]
    den = [h("b1", "B", 1)]
    for name in ROUTERS:
        fused, per_retriever = route(name, lex, den)
        assert {e["version_id"] for e in fused} == {"A", "B"}
        assert "bm25" in per_retriever and "transformer" in per_retriever


def test_unknown_router_is_rejected():
    with pytest.raises(ValueError, match="Unknown router"):
        route("E_MADE_UP", [], [])


# -- 6. no golden leakage ----------------------------------------------------

def test_router_module_cannot_see_the_evaluation_set():
    source = Path("src/rag_v1/routers.py").read_text()
    for banned in ("golden", "evals", "load_cases", "expected_evidence", "case_id"):
        assert banned not in source, f"router module references {banned!r}"


def test_deployable_configurations_carry_no_oracle_document(payload):
    for key, cfg in payload["configurations"].items():
        for case in cfg["cases"].values():
            assert "oracle_documents" not in case, f"{key} leaked oracle documents"


def test_oracle_is_excluded_from_deployable_metrics(payload):
    oracle = payload["oracle_diagnostic"]
    assert oracle["deployable"] is False
    assert oracle["uses_golden_document"] is True
    assert "NOT DEPLOYABLE" in oracle["description"]
    assert "ORACLE" not in payload["configurations"]


# -- 7/8. Stage 2 and corpus statistics frozen -------------------------------

def test_stage2_is_declared_frozen(payload):
    assert "FROZEN" in payload["stage2"]
    assert payload["passage_rrf_k"] == 60
    assert payload["candidate_pool"] == 50
    assert payload["top_k"] == 10
    cfg = payload["retrieval_config"]
    assert cfg["reranker"] is None and cfg["cross_encoder"] is None
    assert cfg["query_rewriting"] is False and cfg["enrichment"] is None
    assert cfg["metadata_filtering"] is False and cfg["ann_index"] is False
    assert payload["query"] == "raw user question only"


def test_full_corpus_bm25_statistics_are_unchanged(payload):
    assert payload["bm25_config"]["k1"] == 1.2
    assert payload["bm25_config"]["b"] == 0.75
    assert "full corpus" in payload["bm25_config"]["statistics"]


def test_transformer_fingerprint_and_chunk_set_unchanged(payload):
    assert payload["transformer_fingerprint"] == FINGERPRINT
    assert payload["embedding_model"]["model_id"] == MODEL
    assert payload["chunk_set"] == CHUNK_SET
    assert payload["corpus_snapshot"] == SNAP


# -- 9. frozen routing width and parameters ----------------------------------

def test_primary_run_uses_top_five_documents(payload):
    assert payload["top_documents"] == 5
    for row in payload["routing_per_case"].values():
        for case in row:
            assert len(case["selected_documents"]) <= 5


def test_router_parameters_are_the_preregistered_ones(payload):
    params = payload["router_parameters"]
    assert params["rank_sum_k"] == RANK_SUM_K == 60
    assert params["rank_sum_support_chunks"] == RANK_SUM_SUPPORT_CHUNKS == 5
    assert params["vote_depth"] == VOTE_DEPTH == 50
    assert params["document_rrf_k"] == DOCUMENT_RRF_K == 60
    assert params["tuned_against_eval_set"] is False
    assert ROUTER_PARAMETERS == params


def test_config_hash_is_present_and_stable(payload):
    assert isinstance(payload["config_hash"], str) and len(payload["config_hash"]) >= 16


# -- 10. multi-hop accounting ------------------------------------------------

def test_multi_hop_cases_require_every_expected_document(payload):
    for name, rows in payload["routing_per_case"].items():
        for case in rows:
            if len(case["expected_documents"]) > 1:
                assert case["multi_hop"] is True
                routed = set(case["selected_documents"])
                expected = set(case["expected_documents"])
                assert case["all_expected_routed"] == (expected <= routed), name
                if case["partially_routed"]:
                    assert not case["all_expected_routed"]


def test_routing_quality_counts_agree_with_the_per_case_rows(payload):
    for name, summary in payload["routing_quality"].items():
        rows = payload["routing_per_case"][name]
        assert summary["cases_all_expected_routed"] == sum(1 for r in rows if r["all_expected_routed"])
        assert summary["stage1_ceiling"] == pytest.approx(
            summary["cases_all_expected_routed"] / summary["cases_total"])


# -- 11. complementarity -----------------------------------------------------

def test_fusion_bonus_is_reported_for_every_router(payload):
    for summary in payload["routing_quality"].values():
        assert summary["best_component_all_routed"] == max(summary["component_all_routed"].values())
        assert summary["fusion_bonus_cases"] == (
            summary["fused_all_routed"] - summary["best_component_all_routed"])


# -- 12. reproduction --------------------------------------------------------

def test_all_reproduction_gates_pass(payload):
    failed = {k: v["checks"] for k, v in payload["reproduction_gate"].items() if not v["reproduced"]}
    assert not failed, f"reproduction gates failed: {failed}"


def test_global_control_and_exp012_hierarchy_reproduce(payload):
    control = payload["configurations"]["GLOBAL_control"]
    assert control["macro_span_recall"] == 0.775
    assert control["cases_fully_recalled"] == 15
    assert control["spans_found_at_10"] == 17

    a_max = payload["configurations"]["A_MAX"]
    assert a_max["macro_span_recall"] == 0.725
    assert a_max["cases_fully_recalled"] == 14

    oracle = payload["oracle_diagnostic"]
    assert oracle["macro_span_recall"] == 0.95
    assert oracle["cases_fully_recalled"] == 19


def test_every_router_ran_end_to_end(payload):
    for name in ROUTERS:
        cfg = payload["configurations"][name]
        assert cfg["cases_total"] == 20
        assert cfg["spans_total"] == 22
        assert cfg["router"] == name
