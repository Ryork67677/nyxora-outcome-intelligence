"""EXP-014R tests: the systems must be frozen, the splits isolated, and the
evaluation set unable to ship a wrong answer key.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag_v1.systems import (
    FROZEN_HASHES,
    NOT_UNDER_TEST,
    STAGE_2,
    SYSTEM_A_GLOBAL,
    SYSTEM_B_DOC_C,
    system_config_hash,
)

DEV = Path("evals/development/v1.jsonl")
DEV_MANIFEST = Path("evals/development/manifest.json")
RESULTS = Path("experiments/EXP-014R/results-development.json")
ORIGINAL = Path("evals/golden/v1.jsonl")


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


@pytest.fixture(scope="module")
def results():
    if not RESULTS.exists():
        pytest.skip("EXP-014R results not built")
    return json.loads(RESULTS.read_text())


# -- frozen systems ----------------------------------------------------------

def test_system_hashes_are_stable():
    assert system_config_hash(SYSTEM_A_GLOBAL) == FROZEN_HASHES["SYSTEM-A-GLOBAL"]
    assert system_config_hash(SYSTEM_B_DOC_C) == FROZEN_HASHES["SYSTEM-B-DOC-C"]
    assert FROZEN_HASHES["SYSTEM-A-GLOBAL"] != FROZEN_HASHES["SYSTEM-B-DOC-C"]


def test_hash_ignores_recorded_metrics_but_not_configuration():
    """Metrics are outcomes, not settings; changing a setting must change the hash."""
    with_other_metrics = {**SYSTEM_B_DOC_C, "development_metrics": {"macro_span_recall": 0.0}}
    assert system_config_hash(with_other_metrics) == FROZEN_HASHES["SYSTEM-B-DOC-C"]
    retuned = {**SYSTEM_B_DOC_C,
               "stage_1": {**SYSTEM_B_DOC_C["stage_1"], "top_documents": 10}}
    assert system_config_hash(retuned) != FROZEN_HASHES["SYSTEM-B-DOC-C"]


def test_both_systems_share_one_frozen_stage_two():
    assert SYSTEM_A_GLOBAL["stage_2"] is STAGE_2
    assert SYSTEM_B_DOC_C["stage_2"] is STAGE_2
    assert STAGE_2["reranker"] is None and STAGE_2["cross_encoder"] is None
    assert STAGE_2["query_rewriting"] is False and STAGE_2["enrichment"] is None
    assert STAGE_2["top_k"] == 10 and STAGE_2["fusion"]["rrf_k"] == 60


def test_system_a_has_no_routing_stage():
    assert SYSTEM_A_GLOBAL["stage_1"] is None


def test_system_b_is_the_standalone_router_not_the_secondary_one():
    stage1 = SYSTEM_B_DOC_C["stage_1"]
    assert stage1["representation"] == "DOC-C-SECTION"
    assert stage1["top_documents"] == 5
    assert stage1["fusion_with_chunk_router"] is False
    assert stage1["fusion_with_bm25"] is False
    assert "19/20" in NOT_UNDER_TEST["reason"]


def test_run_used_the_frozen_configurations(results):
    assert results["system_a_config_hash"] == FROZEN_HASHES["SYSTEM-A-GLOBAL"]
    assert results["system_b_config_hash"] == FROZEN_HASHES["SYSTEM-B-DOC-C"]
    assert results["system_a"]["config_hash"] == FROZEN_HASHES["SYSTEM-A-GLOBAL"]
    assert results["system_b"]["config_hash"] == FROZEN_HASHES["SYSTEM-B-DOC-C"]


# -- split isolation and immutability ---------------------------------------

def test_development_cases_are_unchanged_from_the_original():
    """Only provenance metadata may be added; questions and evidence are frozen."""
    original = {c["case_id"]: c for c in load(ORIGINAL)}
    for case in load(DEV):
        source = original[case["case_id"]]
        assert case["question"] == source["question"]
        assert case["expected_evidence"] == source["expected_evidence"]
        assert case["expected_claims"] == source["expected_claims"]
        assert case["expected_abstain"] == source["expected_abstain"]


def test_development_split_is_labelled_and_hashed():
    manifest = json.loads(DEV_MANIFEST.read_text())
    assert manifest["split"] == "development"
    assert manifest["cases"] == len(load(DEV))
    assert len(manifest["manifest_sha256"]) == 64
    assert "no longer an unbiased holdout" in manifest["note"]
    for case in load(DEV):
        assert case["split"] == "development"
        assert case["human_verified"] is True


def test_split_manifest_hash_is_recorded_with_the_results(results):
    assert results["split"] == "development"
    assert len(results["split_manifest_sha256"]) == 64


# -- the validator must be able to block ------------------------------------

def test_validator_rejects_a_holdout_case_without_human_verification():
    from scripts_validate import validate_cases  # thin import shim below

    case = {"case_id": "X-1", "split": "holdout", "category": "exact_lookup",
            "provider": "openai", "question": "What is the default value of foo_bar?",
            "expected_claims": [{"text": "3", "critical": True}],
            "expected_evidence": [{"version_id": "v", "section_path": ["S"],
                                   "char_start": 0, "char_end": 10}],
            "expected_abstain": False, "verification": "source_anchored_automatic",
            "human_verified": False}
    sources = {"v": {"text": "value is 3", "provider": "openai"}}
    failures = validate_cases([case], sources, {"holdout"})
    assert any(f["check"] == "human_verified_required" for f in failures)


def test_validator_rejects_a_claim_absent_from_its_own_evidence():
    from scripts_validate import validate_cases

    case = {"case_id": "X-2", "split": "development", "category": "exact_lookup",
            "provider": "openai", "question": "What is the default value of foo_bar?",
            "expected_claims": [{"text": "MissingValue", "critical": True}],
            "expected_evidence": [{"version_id": "v", "section_path": ["S"],
                                   "char_start": 0, "char_end": 10}],
            "expected_abstain": False, "verification": "human_verified",
            "human_verified": True}
    sources = {"v": {"text": "value is 3", "provider": "openai"}}
    failures = validate_cases([case], sources, set())
    assert any(f["check"] == "claim_supported_by_evidence" for f in failures)


def test_validator_rejects_an_abstention_case_carrying_evidence():
    from scripts_validate import validate_cases

    case = {"case_id": "X-3", "split": "development", "category": "missing_info",
            "provider": "cross", "question": "How do I configure a thing that does not exist?",
            "expected_claims": [], "expected_abstain": True,
            "expected_evidence": [{"version_id": "v", "section_path": ["S"],
                                   "char_start": 0, "char_end": 5}],
            "verification": "absence_verified_against_snapshot", "human_verified": False}
    sources = {"v": {"text": "value is 3", "provider": "openai"}}
    failures = validate_cases([case], sources, set())
    assert any(f["check"] == "abstention_has_evidence" for f in failures)


def test_validator_detects_duplicate_questions():
    from scripts_validate import validate_cases

    base = {"split": "development", "category": "exact_lookup", "provider": "openai",
            "question": "What is the default value of foo_bar?",
            "expected_claims": [{"text": "3", "critical": True}],
            "expected_evidence": [{"version_id": "v", "section_path": ["S"],
                                   "char_start": 0, "char_end": 10}],
            "expected_abstain": False, "verification": "human_verified", "human_verified": True}
    sources = {"v": {"text": "value is 3", "provider": "openai"}}
    failures = validate_cases([{**base, "case_id": "X-4"}, {**base, "case_id": "X-5"}],
                              sources, set())
    assert any(f["check"] == "duplicate_question" for f in failures)


def test_the_recorded_data_defect_is_still_present_and_documented():
    """OA-002's claim is absent from its own span. Documented, deliberately unfixed."""

    defect_note = Path("experiments/EXP-014R/known-data-defects.md")
    assert defect_note.exists()
    text = defect_note.read_text()
    assert "OA-002" in text and "MaxTurnsExceeded" in text
    assert "NOT fixed" in text or "not been fixed" in text


# -- results integrity -------------------------------------------------------

def test_development_run_reproduces_exp014(results):
    a, b = results["system_a"], results["system_b"]
    assert a["macro_span_recall"] == 0.775
    assert a["cases_fully_recalled"] == 15 and a["spans_found_at_10"] == 17
    assert b["macro_span_recall"] == 0.875
    assert b["cases_fully_recalled"] == 17 and b["spans_found_at_10"] == 19
    assert results["paired"]["net_cases"] == 2
    assert results["paired"]["b_regressions_vs_a"] == []


def test_bootstrap_is_reproducible_with_a_fixed_seed(results):
    bootstrap = results["bootstrap"]
    assert bootstrap["seed"] == 20250818
    assert bootstrap["samples"] == 10000
    assert bootstrap["n_questions"] == results["system_a"]["cases_total"]
    low, high = bootstrap["macro_recall_delta"]["ci95"]
    assert low <= bootstrap["macro_recall_delta"]["point_estimate"] <= high


def test_bootstrap_resamples_questions_not_spans(results):
    """Spans within a question are not independent; the unit must be the question."""
    assert results["bootstrap"]["n_questions"] == 20
    assert results["system_a"]["spans_total"] == 22


def test_mcnemar_is_reported_as_supplementary(results):
    mcnemar = results["mcnemar"]
    assert mcnemar["discordant_pairs"] == mcnemar["b_only"] + mcnemar["a_only"]
    assert "supplementary" in mcnemar["note"]


def test_paired_quadrant_covers_every_case(results):
    quadrant = results["paired"]["quadrant"]
    total = sum(len(v) for v in quadrant.values())
    assert total == results["system_a"]["cases_total"]


def test_no_oracle_metrics_are_presented_as_deployable(results):
    assert "oracle" not in json.dumps(results["system_a"]).lower()
    assert "oracle" not in json.dumps(results["system_b"]).lower()
