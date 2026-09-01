"""EXP-015: the decision is recorded, the ceiling is sound, and nothing was faked.

EXP-015 is blocked at model acquisition, which makes one test more important than all
the others: that no substitute reranker was quietly introduced and no promotion verdict
was invented. The rest hold the parts that did complete — the validation decision and
the candidate-pool ceiling.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag_v1.eval.splits import FrozenHoldoutError, load
from rag_v1.systems import CHUNK_SET, FROZEN_HASHES, SNAPSHOT, SYSTEMS

EXP = Path("experiments/EXP-015")
VAL = Path("experiments/EVAL-VAL-001")
SPLIT_DIR = Path("evals/splits/gold150-v1")
MANIFEST_HASH = "452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17"


def read(path: Path) -> dict:
    if not path.exists():
        pytest.skip(f"{path} has not been generated")
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def ceiling() -> dict:
    return read(EXP / "EXP-015-ceiling-analysis.json")


@pytest.fixture(scope="module")
def prereg() -> dict:
    return read(EXP / "EXP-015-preregistration.json")


@pytest.fixture(scope="module")
def acquisition() -> dict:
    return read(EXP / "EXP-015-acquisition-survey.json")


# ------------------------------------------------------------- §1 the decision record


def test_the_validation_decision_is_recorded():
    decision = read(VAL / "EVAL-VAL-001-decision.json")
    assert decision["SYSTEM_B_PROMOTION"] == "REJECTED"
    assert decision["SYSTEM_A_CONTROL"] == "RETAINED"
    assert decision["classification"] == "REPLICATION_REJECTS_B"


def test_system_b_is_preserved_not_deleted():
    decision = read(VAL / "EVAL-VAL-001-decision.json")
    assert decision["system_b_disposition"]["deleted"] is False
    assert "PRESERVED" in decision["system_b_disposition"]["status"]
    # The configuration must still exist in code, not merely in prose.
    assert "SYSTEM-B-DOC-C" in SYSTEMS
    assert (decision["system_b_disposition"]["config_hash"]
            == FROZEN_HASHES["SYSTEM-B-DOC-C"])
    assert (VAL / "EVAL-VAL-001-results.json").exists(), "the run artifact was deleted"


def test_the_decision_cites_the_measurements_it_rests_on():
    evidence = read(VAL / "EVAL-VAL-001-decision.json")["evidence"]
    assert evidence["system_a_strict"] == "30/40"
    assert evidence["system_b_strict"] == "21/40"
    assert evidence["regressions"] > evidence["rescues"]
    assert evidence["net_cases"] == -9


# --------------------------------------------------------------- frozen systems, corpus


def test_system_a_hash_is_unchanged(ceiling):
    assert ceiling["system_a_hash"] == FROZEN_HASHES["SYSTEM-A-GLOBAL"]
    assert FROZEN_HASHES["SYSTEM-A-GLOBAL"].startswith("9afcb5b7c58ebacf")


def test_system_b_hash_is_unchanged():
    assert FROZEN_HASHES["SYSTEM-B-DOC-C"].startswith("304c350940b83733")


def test_the_corpus_is_unchanged(ceiling, prereg):
    assert ceiling["corpus_snapshot"] == SNAPSHOT
    assert prereg["corpus"]["snapshot"] == SNAPSHOT
    assert prereg["corpus"]["manifest_hash"] == MANIFEST_HASH
    assert prereg["corpus"]["chunk_set"] == CHUNK_SET
    assert prereg["corpus"]["control_chunks"] == 14209
    assert prereg["corpus"]["anthropic"] == 12028
    assert prereg["corpus"]["openai"] == 2181


# ------------------------------------------------------------------ §8 the ceiling


def test_the_ceiling_used_stored_ranks_and_ran_no_retrieval(ceiling):
    assert "No retrieval was re-run" in ceiling["method"]
    assert "no model was involved" in ceiling["method"]


def test_the_ceiling_is_monotonic_in_pool_size(ceiling):
    """A larger pool can only ever reach more, never less."""
    values = [ceiling["ceilings"][k]["max_strict_full_case_recall"]
              for k in ("30", "50", "100")]
    assert values == sorted(values)
    spans = [ceiling["ceilings"][k]["max_span_recall_at_10"]
             for k in ("30", "50", "100")]
    assert spans == sorted(spans)


def test_the_ceiling_never_exceeds_the_case_count(ceiling):
    for key in ("30", "50", "100"):
        entry = ceiling["ceilings"][key]
        assert entry["max_strict_full_case_recall"] <= 40
        assert 0.0 <= entry["max_span_recall_at_10"] <= 1.0
        assert entry["spans_reachable"] + entry["spans_unreachable"] == entry["spans_total"]


def test_the_ceiling_is_above_the_baseline_so_the_experiment_is_justified(ceiling):
    baseline = ceiling["baseline"]["strict_full_case"]
    assert baseline == 30
    assert ceiling["ceilings"]["100"]["max_strict_full_case_recall"] > baseline
    assert ceiling["headroom"]["100"] > 0


def test_the_ceiling_does_not_overclaim(ceiling):
    """§9: a reranker cannot rescue evidence absent from its pool, and the record says so."""
    limit = ceiling["candidate_generation_limit"]
    assert limit["spans_never_retrieved"] > 0
    assert "No reranker can reach them" in limit["note"]
    assert ceiling["ceilings"]["100"]["max_strict_full_case_recall"] < 40


def test_the_ceiling_matches_the_stored_validation_ranks(ceiling):
    """Recompute the pool-100 ceiling from the run rather than trusting the artifact."""
    results = read(VAL / "EVAL-VAL-001-results.json")
    reachable = 0
    for case in results["system_a"]["cases"].values():
        if all(s["rank"] is not None and s["rank"] <= 100 for s in case["spans"]):
            reachable += 1
    assert reachable == ceiling["ceilings"]["100"]["max_strict_full_case_recall"]


# ----------------------------------------------------- §7 §10-§14 the preregistration


def test_the_candidate_pool_is_frozen_at_100(prereg):
    assert prereg["candidate_pool"]["size"] == 100
    assert prereg["candidate_pool"]["frozen_before_selection"] is True
    assert "not swept" in prereg["candidate_pool"]["sweeping_forbidden"]


def test_the_preregistration_forbids_gold_training(prereg):
    forbidden = prereg["model_policy"]["must_not_be"]
    for rule in ("trained on GOLD", "fine-tuned on GOLD"):
        assert any(rule in item for item in forbidden), rule
    assert any("synthetic labels" in item for item in forbidden)
    assert any("selected on validation performance" in item for item in forbidden)


def test_qualification_happens_on_development_only(prereg):
    assert prereg["model_policy"]["selection_split"] == "development (20 cases) only"
    assert prereg["qualification_rule"]["split"] == "development"
    assert prereg["validation_protocol"]["runs"] == "exactly one, after the freeze"


def test_the_experimental_system_may_not_change_retrieval(prereg):
    may_not = prereg["experimental_system"]["may_not"]
    for rule in ("invent candidates", "change the query", "change BM25",
                 "change dense retrieval", "change RRF"):
        assert any(rule in item for item in may_not), rule


def test_the_preregistration_was_written_before_selection(prereg):
    assert "before any reranker was selected" in prereg["status"]
    assert prereg["ceiling_analysis"]["computed_before_model_selection"] is True


def test_the_split_counts_are_what_the_experiment_assumes():
    assert load("development")["count"] == 20
    assert load("validation")["count"] == 40


# ------------------------------------------------------- §11 the acquisition blocker


def test_the_acquisition_survey_reached_a_recorded_conclusion(acquisition):
    assert acquisition["conclusion"] == "NO_PRETRAINED_CROSS_ENCODER_AVAILABLE"
    assert acquisition["local_inventory"]["cross_encoder_present"] is False
    assert len(acquisition["hosts"]) >= 5


def test_the_survey_distinguishes_a_block_from_an_absent_object(acquisition):
    """The S3 host is reachable and simply has no cross-encoder; that is not a block."""
    s3 = next(h for h in acquisition["hosts"] if "s3.amazonaws.com" in h["host"])
    assert "REACHABLE" in s3["verdict"]
    hf = next(h for h in acquisition["hosts"] if h["host"] == "huggingface.co")
    assert "BLOCKED" in hf["verdict"]


def test_no_substitute_reranker_was_used(acquisition):
    """The failure mode this whole experiment could have had."""
    assert "No substitute was used" in acquisition["what_was_not_done_instead"]
    assert not (EXP / "SYSTEM-C-RERANK.json").exists(), (
        "a SYSTEM-C config exists but no reranker was obtainable")
    for artifact in ("EXP-015-development-results.json",
                     "EXP-015-validation-results.json",
                     "EXP-015-paired-analysis.json"):
        assert not (EXP / artifact).exists(), (
            f"{artifact} exists but no reranker was ever run")


def test_no_promotion_verdict_was_invented():
    report = (EXP / "EXP-015-report.md").read_text()
    for verdict in ("RERANKER_SUPPORTED", "RERANKER_NEUTRAL", "RERANKER_REJECTED"):
        # The names may be explained, but none may be asserted as this run's result.
        assert f"Classification: {verdict}" not in report
        assert f"**{verdict}**" not in report
    assert "No `RERANKER_SUPPORTED`" in report


# ----------------------------------------------------------- §2 §22 the holdout


def test_the_holdout_was_not_run(prereg):
    assert prereg["holdout"]["runs"] == 0
    assert prereg["holdout"]["frozen"] is True
    assert prereg["holdout"]["count"] == 90
    lock = json.loads((SPLIT_DIR / "holdout.lock.json").read_text())
    assert lock["holdout_frozen"] is True
    assert lock["holdout_count"] == 90


def test_the_holdout_still_refuses_to_load():
    with pytest.raises(FrozenHoldoutError):
        load("holdout")


def test_no_holdout_id_appears_in_any_exp015_artifact():
    holdout = json.loads((SPLIT_DIR / "holdout.json").read_text())["case_ids"]
    for artifact in EXP.glob("*"):
        text = artifact.read_text()
        leaked = [c for c in holdout if c in text]
        assert not leaked, f"{artifact.name} leaks holdout ids: {leaked[:5]}"
    for artifact in (VAL / "EVAL-VAL-001-decision.md",
                     VAL / "EVAL-VAL-001-decision.json"):
        text = artifact.read_text()
        assert not [c for c in holdout if c in text], artifact.name


def test_the_holdout_access_log_is_empty():
    log = SPLIT_DIR / "holdout-access.log.jsonl"
    if not log.exists():
        return
    assert log.read_text().strip() == "", "the holdout was accessed"


# --------------------------------------------------------------- no generation


def test_no_answer_generation_occurred():
    for artifact in EXP.glob("*.json"):
        payload = json.loads(artifact.read_text())
        text = json.dumps(payload)
        for marker in ("generated_answer", "completion_tokens", "faithfulness_score",
                       "answer_correctness"):
            assert marker not in text, f"{artifact.name}: {marker}"
