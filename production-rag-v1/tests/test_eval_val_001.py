"""EVAL-VAL-001: the validation run used the frozen systems and never touched the holdout.

The result rejects SYSTEM-B, which makes these tests more important rather than less: a
negative finding is only worth acting on if the run that produced it was the frozen
configuration, on the frozen corpus, against the frozen validation split, with the
holdout untouched.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rag_v1.eval.splits import FrozenHoldoutError, load
from rag_v1.systems import CHUNK_SET, FROZEN_HASHES, SNAPSHOT

OUT = Path("experiments/EVAL-VAL-001")
RESULTS = OUT / "EVAL-VAL-001-results.json"
ANALYSIS = OUT / "EVAL-VAL-001-analysis.json"
ROUTING = OUT / "EVAL-VAL-001-routing-failures.json"
PER_CASE = OUT / "EVAL-VAL-001-per-case.json"
ENVIRONMENT = OUT / "EVAL-VAL-001-environment.json"
SPLIT_DIR = Path("evals/splits/gold150-v1")
MANIFEST = Path("experiments/EVAL-SPLIT-001/EVAL-SPLIT-001-manifest.json")
MANIFEST_HASH = "452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17"


def read(path: Path) -> dict:
    if not path.exists():
        pytest.skip(f"{path} has not been generated")
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def results() -> dict:
    return read(RESULTS)


@pytest.fixture(scope="module")
def analysis() -> dict:
    return read(ANALYSIS)


# ------------------------------------------------------------------ frozen systems


def test_system_a_hash_is_unchanged(results):
    assert results["system_a_config_hash"] == FROZEN_HASHES["SYSTEM-A-GLOBAL"]
    assert results["system_a_config_hash"].startswith("9afcb5b7c58ebacf")


def test_system_b_hash_is_unchanged(results):
    assert results["system_b_config_hash"] == FROZEN_HASHES["SYSTEM-B-DOC-C"]
    assert results["system_b_config_hash"].startswith("304c350940b83733")


def test_the_run_used_the_frozen_corpus(results):
    assert results["corpus_snapshot"] == SNAPSHOT
    assert results["chunk_set"] == CHUNK_SET
    assert read(ENVIRONMENT)["manifest_hash"] == MANIFEST_HASH


def test_no_tuning_knob_moved(results):
    """Every Stage-2 value the brief forbids changing, checked against the record."""
    stage2 = results["system_a_config"]["stage_2"]
    assert stage2["fusion"]["rrf_k"] == 60
    assert stage2["fusion"]["pool_per_retriever"] == 50
    assert stage2["top_k"] == 10
    assert stage2["lexical"]["k1"] == 1.2
    assert stage2["lexical"]["b"] == 0.75
    assert stage2["reranker"] is None
    assert stage2["query_rewriting"] is False
    assert stage2["metadata_filtering"] is False
    assert results["system_b_config"]["stage_1"]["top_documents"] == 5
    # Both systems must share one Stage 2, or the comparison is not about routing.
    assert results["system_b_config"]["stage_2"] == stage2


# ---------------------------------------------------------------- the validation split


def test_exactly_forty_validation_cases_were_scored(results):
    assert results["cases_scored"] == 40
    assert results["system_a"]["cases_total"] == 40
    assert results["system_b"]["cases_total"] == 40


def test_the_split_matches_the_frozen_manifest_hash():
    manifest = read(MANIFEST)
    text = (SPLIT_DIR / "validation.json").read_text()
    assert hashlib.sha256(text.encode()).hexdigest() == (
        manifest["split_artifact_sha256"]["validation"])


def test_only_validation_case_ids_were_scored(results):
    validation = set(json.loads(
        (SPLIT_DIR / "validation.json").read_text())["case_ids"])
    scored = set(results["system_a"]["cases"])
    assert scored == validation


def test_zero_holdout_cases_were_loaded(results):
    holdout = set(json.loads((SPLIT_DIR / "holdout.json").read_text())["case_ids"])
    scored = set(results["system_a"]["cases"]) | set(results["system_b"]["cases"])
    assert not (scored & holdout), sorted(scored & holdout)
    assert read(ANALYSIS)["split"]["holdout_cases_loaded"] == 0


def test_no_holdout_id_appears_anywhere_in_the_experiment_output():
    """§4: holdout identifiers must not be printed into this experiment at all."""
    holdout = json.loads((SPLIT_DIR / "holdout.json").read_text())["case_ids"]
    for artifact in (RESULTS, ANALYSIS, ROUTING, PER_CASE, ENVIRONMENT,
                     OUT / "EVAL-VAL-001-paired-analysis.json",
                     OUT / "EVAL-VAL-001-report.md"):
        if not artifact.exists():
            continue
        text = artifact.read_text()
        leaked = [c for c in holdout if c in text]
        assert not leaked, f"{artifact.name} leaks holdout ids: {leaked[:5]}"


def test_the_holdout_is_still_frozen_and_unrun():
    lock = json.loads((SPLIT_DIR / "holdout.lock.json").read_text())
    assert lock["holdout_frozen"] is True
    assert lock["holdout_count"] == 90
    with pytest.raises(FrozenHoldoutError):
        load("holdout")


# ------------------------------------------------------------------------- scoring


def test_strict_multi_span_scoring_requires_every_span(results):
    """A multi-span case may not pass on partial evidence."""
    for system in ("system_a", "system_b"):
        for case_id, case in results[system]["cases"].items():
            found = sum(1 for s in case["spans"] if s["within"]["10"])
            assert case["fully_recalled"] == (found == len(case["spans"])), case_id
    multi = [c for c in results["system_a"]["cases"].values() if len(c["spans"]) > 1]
    assert multi, "no multi-span case in validation — the check is vacuous"


def test_span_totals_are_consistent(results):
    for system in ("system_a", "system_b"):
        spans = [s for c in results[system]["cases"].values() for s in c["spans"]]
        assert results[system]["spans_total"] == len(spans) == 47
        assert results[system]["spans_found_at_10"] == sum(
            1 for s in spans if s["within"]["10"])


def test_the_primary_endpoint_matches_the_per_case_records(results, analysis):
    for system, key in (("system_a", "system_a"), ("system_b", "system_b")):
        full = sum(1 for c in results[system]["cases"].values() if c["fully_recalled"])
        assert results[system]["cases_fully_recalled"] == full
        assert analysis["primary_endpoint"][key] == full


# --------------------------------------------------------------- paired and statistics


def test_the_paired_quadrants_partition_the_split(results):
    quadrant = results["paired"]["quadrant"]
    total = sum(len(v) for v in quadrant.values())
    assert total == 40
    seen = [c for v in quadrant.values() for c in v]
    assert len(set(seen)) == 40


def test_rescues_and_regressions_agree_with_the_per_case_records(results):
    a, b = results["system_a"]["cases"], results["system_b"]["cases"]
    rescues = sorted(c for c in a if b[c]["fully_recalled"]
                     and not a[c]["fully_recalled"])
    regressions = sorted(c for c in a if a[c]["fully_recalled"]
                         and not b[c]["fully_recalled"])
    assert sorted(results["paired"]["b_rescues_over_a"]) == rescues
    assert sorted(results["paired"]["b_regressions_vs_a"]) == regressions


def test_the_bootstrap_is_deterministic_and_paired(results):
    boot = results["bootstrap"]
    assert boot["samples"] == 10000
    assert boot["n_questions"] == 40, "bootstrap must resample questions, not spans"
    assert isinstance(boot["seed"], int)
    low, high = boot["macro_recall_delta"]["ci95"]
    assert low <= boot["macro_recall_delta"]["point_estimate"] <= high


def test_mcnemar_counts_match_the_paired_movement(results):
    mc, paired = results["mcnemar"], results["paired"]
    assert mc["b_only"] == len(paired["b_rescues_over_a"])
    assert mc["a_only"] == len(paired["b_regressions_vs_a"])
    assert mc["discordant_pairs"] == mc["b_only"] + mc["a_only"]


# ------------------------------------------------------------- routing classification


def test_routing_classification_is_deterministic_and_total(analysis):
    routing = read(ROUTING)
    per_case = routing["system_b"]["per_case"]
    assert len(per_case) == 40
    valid = {"DOCUMENT_ROUTING_FAILURE", "WITHIN_DOCUMENT_PASSAGE_FAILURE",
             "MIXED_FAILURE", "NOT_APPLICABLE"}
    assert {c["classification"] for c in per_case.values()} <= valid
    assert sum(routing["system_b"]["counts"].values()) == 40


def test_a_passing_case_is_never_classified_as_a_failure(analysis):
    for system in ("system_b", "system_a_equivalent"):
        for case_id, case in read(ROUTING)[system]["per_case"].items():
            if case["fully_recalled"]:
                assert case["classification"] == "NOT_APPLICABLE", case_id


def test_every_regression_has_a_causal_trace(results, analysis):
    traces = analysis["causal_traces"]
    for case_id in (results["paired"]["b_rescues_over_a"]
                    + results["paired"]["b_regressions_vs_a"]):
        assert case_id in traces, case_id
        assert traces[case_id]["attribution"]


# ------------------------------------------------------------------- no generation


def test_no_generation_model_was_invoked(analysis):
    """Look for generation *output*, not for the sentence saying there was none.

    The first version of this test scanned the whole document for the word
    "faithfulness" and matched its own disclaimer — a check that fails when the claim is
    true is worse than no check.
    """
    results = read(RESULTS)
    for system in ("system_a", "system_b"):
        for case in results[system]["cases"].values():
            assert set(case) <= {"case_id", "spans", "recall", "fully_recalled",
                                 "doc_recall"}, case["case_id"]
    forbidden = ("answer_correctness", "faithfulness_score", "citation_judge",
                 "generated_answer", "completion_tokens", "prompt_tokens",
                 "generation_model")
    for key in forbidden:
        assert key not in results, key
        assert key not in analysis, key
    assert "generation_provider" not in json.dumps(results["system_a_config"])
    assert any("generation" in item for item in analysis["not_done"])


def test_no_system_was_promoted(analysis):
    verdict = analysis["replication_verdict"]
    assert verdict["classification"] in ("REPLICATION_SUPPORTS_B",
                                         "REPLICATION_NEUTRAL",
                                         "REPLICATION_REJECTS_B")
    assert "no system was promoted" in verdict["decision_note"].lower()


# ------------------------------------------------------------------- the conclusion


def test_the_classification_follows_from_the_measurements(analysis):
    verdict = analysis["replication_verdict"]
    a = analysis["primary_endpoint"]["system_a"]
    b = analysis["primary_endpoint"]["system_b"]
    if verdict["classification"] == "REPLICATION_REJECTS_B":
        assert b < a or verdict["regressions"] > verdict["rescues"]
    if verdict["classification"] == "REPLICATION_SUPPORTS_B":
        assert b > a and verdict["rescues"] > verdict["regressions"]


def test_the_historical_reproduction_is_recorded(analysis):
    historical = analysis["historical_reproduction"]
    assert historical["system_a_strict"] == "15/20"
    assert historical["system_b_strict"] == "17/20"
    assert historical["reproduced_exactly"] is True
