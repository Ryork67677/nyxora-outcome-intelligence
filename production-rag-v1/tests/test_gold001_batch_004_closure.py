"""GOLD-001 batch 004: the decisions, the eligibility gate, and the closure.

Batch 004 is the first batch whose repairs were kept out of the generation artifact, so
a decision attaches to a composed reviewed-state file rather than to the batch itself.
These tests check that the composition is honest — the generation artifact untouched,
both hashes recorded, approvals pinned to the post-repair evidence — and that the counts
in the closure and the project-wide status are the ones the records support.

The number these tests most exist to protect is the small one. One genuine multi-hop
case out of 559 tested bridge pairs is the batch's real finding, and it is the number
most easily inflated by a report that rounds it into "multi-hop coverage".
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rag_v1.gold.eligibility import evaluate

GENERATED = Path("evals/review/gold_review_batch_004.json")
REPAIRS = Path("evals/review/gold_review_batch_004_repairs.json")
FINAL = Path("evals/review/gold_review_batch_004_final.json")
DECISIONS = Path("evals/review/human_decisions_batch_004.json")
CLOSURE = Path("experiments/GOLD-001/GOLD-001-batch-004-closure.json")
STATUS = Path("experiments/GOLD-001/GOLD-001-eligibility-status.json")
NEAR_MISS = Path("experiments/GOLD-001/BATCH-004-near-miss-multihop-review.json")
VALIDATION = Path("evals/review/validate_golden_batch_004.json")
FROZEN_SYSTEMS = {
    "SYSTEM-A-GLOBAL":
        "9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38",
    "SYSTEM-B-DOC-C":
        "304c350940b83733df6043ae3a8abdcbcde33d16950730127aa9f1f39494388b",
}
#: What the owner decided. Written down so a later edit to the decisions file that
#: quietly flips an outcome fails here rather than passing.
EXPECTED_DECISIONS = {
    **{f"GOLD-B004-{n:02d}": "APPROVE" for n in
       (1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15)},
    "GOLD-B004-08": "REJECT",
}


def load(path: Path) -> dict:
    if not path.exists():
        pytest.skip(f"{path} has not been generated")
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def final() -> dict:
    return load(FINAL)


@pytest.fixture(scope="module")
def closure() -> dict:
    return load(CLOSURE)


@pytest.fixture(scope="module")
def decisions() -> dict:
    return load(DECISIONS)


# ------------------------------------------------------------------ decisions imported


def test_decisions_are_the_ones_the_owner_gave(decisions):
    recorded = {d["candidate_id"]: d["decision"] for d in decisions["decisions"]}
    assert recorded == EXPECTED_DECISIONS
    assert decisions["decided_by"] == "project_owner"
    assert decisions["reviewer"] == "project_owner"


def test_batch_reached_the_expected_state(final):
    assert final["status_counts"] == {"human_verified": 14, "human_rejected": 1}
    assert final["undecided_candidates"] == []
    assert final["human_reviewer"] == "project_owner"


def test_no_model_is_recorded_as_the_approver(final):
    models = {"claude", "chatgpt", "gpt", "gemini", "assistant", "ai", "llm", "model"}
    for record in final["records"]:
        for entry in record.get("human_decision_history", []):
            assert entry["reviewer"].strip().lower() not in models
        assert (record.get("human_reviewer") or "project_owner").lower() not in models


def test_approvals_pin_the_post_repair_evidence(final, decisions):
    """A repaired candidate can only be approved against the version the owner saw."""
    records = {r["candidate_id"]: r for r in final["records"]}
    repairs = load(REPAIRS)
    superseded = {
        r["candidate_id"]: {rev["old_evidence_hash"]
                            for rev in r.get("anchor_revisions", [])
                            if "old_evidence_hash" in rev}
        for r in repairs["records"]}
    for row in decisions["decisions"]:
        if row["decision"] != "APPROVE":
            continue
        record = records[row["candidate_id"]]
        current = [s["evidence_hash"] for s in record["expected_evidence"]]
        assert row["approves_evidence_hash"] == current, row["candidate_id"]
        stale = superseded.get(row["candidate_id"], set())
        assert not stale.intersection(row["approves_evidence_hash"]), (
            f"{row['candidate_id']} approves a pre-repair anchor")


def test_generation_artifact_survived_the_decisions(final):
    """§7: the original generation artifact stays immutable."""
    generated = load(GENERATED)
    for record in generated["records"]:
        assert record["verification_status"] == "candidate_unverified"
        assert "human_decision" not in record
        assert "anchor_revisions" not in record
    assert final["source_batch_sha256"] == generated["batch_sha256"]


def test_repair_history_survived_the_decisions(final):
    repaired = [r for r in final["records"] if r.get("anchor_revisions")]
    assert repaired, "the repair history is gone"
    for record in repaired:
        for revision in record["anchor_revisions"]:
            if revision["action"] != "extend_boundary":
                continue
            assert revision["old_evidence_text"]
            assert revision["old_evidence_hash"] != revision["new_evidence_hash"]


def test_rejected_candidate_is_preserved_not_deleted(final):
    rejected = [r for r in final["records"]
                if r["verification_status"] == "human_rejected"]
    assert [r["candidate_id"] for r in rejected] == ["GOLD-B004-08"]
    assert rejected[0]["human_decision_history"][-1]["notes"]
    assert rejected[0]["expected_evidence"], "the evidence was stripped"


# ---------------------------------------------------------------------- the overrides


def test_noncritical_findings_were_accepted_by_a_person_not_a_model(final):
    records = {r["candidate_id"]: r for r in final["records"]}
    overridden = {cid: r for cid, r in records.items()
                  if r.get("human_anaphora_override") or r.get("human_dependency_override")}
    assert set(overridden) == {"GOLD-B004-02", "GOLD-B004-05", "GOLD-B004-15"}
    for candidate_id, record in overridden.items():
        assert record["override_reviewer"] == "project_owner", candidate_id
        assert record.get("anaphora_status") or record.get("dependency_status")


def test_an_override_does_not_delete_the_finding(final):
    """§3: record the acceptance, keep the finding."""
    from rag_v1.gold.anaphora import evaluate_span
    record = next(r for r in final["records"] if r["candidate_id"] == "GOLD-B004-15")
    span = record["expected_evidence"][1]
    verdict = evaluate_span(span["evidence_text"], record)
    assert verdict["finding"], "the finding was erased by the override"
    assert verdict["human_anaphora_override"] is True
    assert verdict["blocking"] is False


def test_a_critical_finding_cannot_be_overridden():
    from rag_v1.gold.anaphora import CRITICAL, evaluate_span
    span = "If true, the request is rejected before it reaches the model."
    case = {"proposed_question": "What happens if true?",
            "proposed_answer": "It is rejected.", "proposed_atomic_claims": [],
            "critical_strings": [], "human_anaphora_override": True,
            "override_reviewer": "project_owner"}
    verdict = evaluate_span(span, case)
    assert verdict["status"] == CRITICAL
    assert verdict["blocking"] is True
    assert verdict["override_refused"]


# --------------------------------------------------------------------- the eligibility


def test_every_approved_case_passes_the_eligibility_gate(final):
    approved = [r for r in final["records"]
                if r["verification_status"] == "human_verified"]
    assert len(approved) == 14
    for record in approved:
        verdict = evaluate(record)
        assert verdict["holdout_eligible"], (record["candidate_id"], verdict["failures"])


def test_a_rejected_case_can_never_be_eligible(final):
    rejected = next(r for r in final["records"]
                    if r["verification_status"] == "human_rejected")
    verdict = evaluate(rejected)
    assert verdict["holdout_eligible"] is False
    assert any(f["condition"] == "human_verified" for f in verdict["failures"])


def test_multi_span_cases_declare_that_all_evidence_is_required(final):
    for record in final["records"]:
        if record["verification_status"] != "human_verified":
            continue
        if len(record["expected_evidence"]) > 1:
            assert record["requires_all_evidence"] is True, record["candidate_id"]


def test_multi_document_case_really_spans_two_documents(final):
    record = next(r for r in final["records"]
                  if r["reasoning_type"] == "genuine_multi_hop")
    versions = {s["version_id"] for s in record["expected_evidence"]}
    assert record["evidence_shape"] == "multi_document"
    assert len(versions) == 2
    assert record["requires_all_evidence"] is True
    assert record["multi_hop_composition_check"] == "PASS"
    assert record["verification_status"] == "human_verified"


def test_multi_document_claims_are_supported_by_their_own_spans(final):
    from rag_v1.gold.normalisation import contains_claim_string
    record = next(r for r in final["records"]
                  if r["reasoning_type"] == "genuine_multi_hop")
    for mapping in record["claim_evidence_map"]:
        span = next(s for s in record["expected_evidence"]
                    if s["evidence_id"] == mapping["evidence_id"])
        for string in mapping["critical_strings"]:
            assert contains_claim_string(span["evidence_text"], string)


def test_eligibility_gate_rejects_an_undeclared_multi_span_case():
    """The condition added for batch 004, exercised rather than assumed."""
    body = "The `x_flag` setting is required."
    case = {
        "candidate_id": "SYNTHETIC-1", "verification_status": "human_verified",
        "human_verified": True, "proposed_atomic_claims": ["`x_flag` is required."],
        "critical_strings": ["x_flag"], "requires_all_evidence": False,
        "expected_evidence": [
            {"evidence_id": "E1", "version_id": "v1", "evidence_text": body,
             "evidence_hash": hashlib.sha256(body.encode()).hexdigest(),
             "critical_strings": ["x_flag"]},
            {"evidence_id": "E2", "version_id": "v1", "evidence_text": body,
             "evidence_hash": hashlib.sha256(body.encode()).hexdigest(),
             "critical_strings": ["x_flag"]},
        ],
    }
    verdict = evaluate(case)
    assert verdict["holdout_eligible"] is False
    assert any(f["condition"] == "required_evidence_declared"
               for f in verdict["failures"])


def test_closed_batches_kept_their_eligibility(final):
    """The new condition must not retroactively disqualify batches 001–003."""
    status = load(STATUS)
    by_batch = {b["batch"]: b for b in status["batches"]}
    assert by_batch[1]["holdout_eligible"] == 16
    assert by_batch[2]["holdout_eligible"] == 17
    assert by_batch[3]["holdout_eligible"] == 20


# -------------------------------------------------------------------------- the closure


def test_closure_counts_match_the_records(closure, final):
    totals = closure["totals"]
    assert totals["candidates"] == len(final["records"]) == 15
    assert totals["human_verified"] == 14
    assert totals["human_rejected"] == 1
    assert totals["needs_human_review"] == 0
    assert totals["outstanding_decisions"] == 0
    assert closure["status_counts"] == final["status_counts"]
    assert len(closure["human_verified_ids"]) == totals["human_verified"]


def test_closure_hash_still_matches_the_records(closure, final):
    """A closed batch is not supposed to change; the hash is how that is checked."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_close_batch", Path("scripts/close_batch.py").resolve())
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    actual = module.candidate_digest(final["records"])
    assert actual == closure["closure_sha256"], "batch 004 changed after closure"
    assert actual == final["closure_sha256"]


def test_closure_reports_one_multi_hop_and_says_what_it_cost(closure):
    assert closure["reasoning_and_shape"]["genuine_multi_hop"] == 1
    rejection = closure["multi_hop_rejection"]
    assert rejection["attempted_pairs"] == 559
    assert rejection["passed"] == 1
    assert rejection["rejected"] == 558
    assert sum(rejection["reasons"].values()) == rejection["rejected"]


def test_closure_carries_the_near_miss_diagnostic(closure):
    near = closure["near_miss_diagnostic"]
    diagnostic = load(NEAR_MISS)
    assert near["pairs"] == diagnostic["pairs"] == 5
    assert set(near["verdicts"].values()) == {"CORRECT_REJECTION"}
    assert near["promoted_to_batch_004"] == 0
    assert near["batch_004_regenerated"] is False


def test_closure_preserves_the_erratum(closure):
    errata = closure["errata"]
    assert errata, "the erratum was dropped from the closure"
    entry = next(e for e in errata if e["correction"] == "near-miss bridge-pair count")
    assert "3" in entry["was"]
    assert entry["is"] == "5 pairs"
    assert entry["affects_generation_figures"] is False


def test_closure_documents_the_precheck_limitation(closure):
    precheck = closure["precheck_limitation"]
    assert precheck["precheck_ready"] == precheck["candidates"] == 15
    assert precheck["repaired"] == 10
    assert precheck["reject_recommended"] == 1
    assert precheck["means"] == "structurally capable"
    assert set(precheck["does_not_mean"]) == {
        "semantic correctness", "human approval", "holdout eligibility"}


def test_closure_records_the_overrides(closure):
    overrides = {o["candidate_id"] for o in closure["human_overrides"]}
    assert overrides == {"GOLD-B004-02", "GOLD-B004-05", "GOLD-B004-15"}
    for override in closure["human_overrides"]:
        assert override["override_reviewer"] == "project_owner"
        assert override["finding_retained"] is True


def test_closure_records_both_identities(closure):
    generated = load(GENERATED)
    assert closure["generation_batch_sha256"] == generated["batch_sha256"]
    assert closure["source_batch_sha256"] != closure["generation_batch_sha256"]


def test_validator_ran_on_the_projection(closure):
    validation = load(VALIDATION)
    assert validation["passed"] is True
    assert validation["cases"] == closure["totals"]["human_verified"] == 14
    assert closure["validation"]["cases"] == 14
    assert closure["validation"]["failures"] == 0


# ------------------------------------------------------------------- project-wide state


def test_project_wide_counts_are_consistent():
    status = load(STATUS)
    combined = status["combined"]
    assert combined["human_verified"] == 67
    assert combined["holdout_eligible"] == 67
    assert combined["human_rejected"] == 4
    assert combined["genuine_multi_hop"] == 1
    assert sum(b["human_verified"] for b in status["batches"]) == 67
    assert sum(b["holdout_eligible"] for b in status["batches"]) == 67
    for batch in status["batches"]:
        assert len(batch["holdout_eligible_ids"]) == batch["holdout_eligible"]


def test_multi_hop_coverage_is_not_overstated():
    """§11: one observation is one observation."""
    status = load(STATUS)
    assert status["combined"]["genuine_multi_hop"] == 1
    document = Path("experiments/GOLD-001/GOLD-001-eligibility-status.md").read_text()
    assert "does not mean the category is adequately sampled" in document
    assert "559" in document, "the cost of finding one chain is not reported"


def test_holdout_is_not_frozen():
    status = load(STATUS)
    assert status["holdout_frozen"] is False
    assert status["reason_not_frozen"]


def test_retrieval_was_not_run(final, closure):
    assert final["retrieval_was_not_run"] is True
    assert final["systems_executed"] == []
    assert closure["retrieval"]["retrieval_was_not_run"] is True
    assert closure["retrieval"]["systems_run_against_these_candidates"] == []
    status = load(STATUS)
    assert status["retrieval_was_not_run"] is True
    assert status["systems_executed"] == []
    blob = json.dumps(final["records"]).lower()
    for label in ("routing_heavy", "passage_heavy", "hard_for_bm25", "recall@", "ndcg"):
        assert label not in blob


def test_frozen_systems_are_unchanged():
    frozen = Path("evals/frozen")
    if not frozen.exists():
        pytest.skip("no frozen system directory")
    seen = {}
    for path in sorted(frozen.glob("*.json")):
        payload = json.loads(path.read_text())
        name = payload.get("system_id") or payload.get("name")
        digest = payload.get("config_sha256") or payload.get("config_hash")
        if name in FROZEN_SYSTEMS and digest:
            seen[name] = digest
    if not seen:
        pytest.skip("frozen system hashes are recorded elsewhere")
    for name, digest in seen.items():
        assert digest == FROZEN_SYSTEMS[name], f"{name} changed"
