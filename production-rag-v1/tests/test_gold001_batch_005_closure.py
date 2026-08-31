"""GOLD-001 batch 005: the owner's decisions, the eligibility gate, and the closure.

Batch 005 is the batch where the review earned its keep. Nineteen candidates were
`precheck_holdout_ready`, all nineteen; the source-integrity review then repaired seven
and recommended four for rejection, and the owner rejected exactly those four. These
tests exist to keep that separation visible — a structural pass is not a semantic one —
and to stop the numbers drifting into a report that flatters them.

The other number they protect is the small one. Batch 005 searched the corpus for
multi-hop chains a second way, dependency-first, and exported none: three pairs reached
the gates, one was a valid chain, and it was the chain batch 004 had already closed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rag_v1.gold.eligibility import HOLDOUT_CONDITIONS, evaluate

GENERATED = Path("evals/review/gold_review_batch_005.json")
REPAIRS = Path("evals/review/gold_review_batch_005_repairs.json")
FINAL = Path("evals/review/gold_review_batch_005_final.json")
DECISIONS = Path("evals/review/human_decisions_batch_005.json")
CLOSURE = Path("experiments/GOLD-001/GOLD-001-batch-005-closure.json")
STATUS = Path("experiments/GOLD-001/GOLD-001-eligibility-status.json")
VALIDATION = Path("evals/review/validate_golden_batch_005.json")
PREREG = Path("experiments/GOLD-001/GOLD-001-batch-006-preregistration-inputs.json")
FROZEN_SYSTEMS = {
    "SYSTEM-A-GLOBAL":
        "9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38",
    "SYSTEM-B-DOC-C":
        "304c350940b83733df6043ae3a8abdcbcde33d16950730127aa9f1f39494388b",
}
#: What the owner decided. Written down so an edit that quietly flips an outcome fails
#: here rather than passing.
EXPECTED_DECISIONS = {
    **{f"GOLD-B005-{n:02d}": "APPROVE" for n in
       (2, 3, 4, 5, 7, 8, 9, 11, 12, 14, 15, 16, 17, 18, 19)},
    **{f"GOLD-B005-{n:02d}": "REJECT" for n in (1, 6, 10, 13)},
}
CLOSED_BEFORE = {
    1: "evals/review/gold_review_batch_001.json",
    2: "evals/review/gold_review_batch_002.json",
    3: "evals/review/gold_review_batch_003.json",
    4: "evals/review/gold_review_batch_004_final.json",
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


# ----------------------------------------------------------------- decisions imported


def test_decisions_are_the_ones_the_owner_gave(decisions):
    recorded = {d["candidate_id"]: d["decision"] for d in decisions["decisions"]}
    assert recorded == EXPECTED_DECISIONS
    assert decisions["decided_by"] == "project_owner"


def test_batch_reached_the_expected_state(final):
    assert final["status_counts"] == {"human_verified": 15, "human_rejected": 4}
    assert final["undecided_candidates"] == []
    assert final["human_reviewer"] == "project_owner"


def test_no_model_is_recorded_as_the_approver(final):
    models = {"claude", "chatgpt", "gpt", "gemini", "assistant", "ai", "llm", "model"}
    for record in final["records"]:
        for entry in record.get("human_decision_history", []):
            assert entry["reviewer"].strip().lower() not in models
        assert (record.get("override_reviewer") or "project_owner").lower() not in models


def test_approvals_pin_the_post_repair_evidence(final, decisions):
    """A repaired candidate can only be approved against the version the owner saw."""
    records = {r["candidate_id"]: r for r in final["records"]}
    repairs = load(REPAIRS)
    superseded = {
        r["candidate_id"]: {rev["old_evidence_hash"]
                            for rev in r.get("anchor_revisions", [])
                            if "old_evidence_hash" in rev}
        for r in repairs["records"]}
    approved = [row for row in decisions["decisions"] if row["decision"] == "APPROVE"]
    assert approved
    for row in approved:
        record = records[row["candidate_id"]]
        current = [s["evidence_hash"] for s in record["expected_evidence"]]
        assert row["approves_evidence_hash"] == current, row["candidate_id"]
        stale = superseded.get(row["candidate_id"], set())
        assert not stale.intersection(row["approves_evidence_hash"]), (
            f"{row['candidate_id']} approves a pre-repair anchor")


def test_a_repaired_anchor_still_hashes_to_its_own_text(final):
    repaired = [r for r in final["records"] if r.get("anchor_revisions")]
    assert repaired, "the repair history is gone"
    for record in repaired:
        for span in record["expected_evidence"]:
            digest = hashlib.sha256(span["evidence_text"].encode()).hexdigest()
            assert span["evidence_hash"] == digest, record["candidate_id"]


def test_generation_artifact_survived_the_decisions(final):
    generated = load(GENERATED)
    for record in generated["records"]:
        assert record["verification_status"] == "candidate_unverified"
        assert "human_decision" not in record
        assert "anchor_revisions" not in record
    assert final["source_batch_sha256"] == generated["batch_sha256"]


def test_rejected_candidates_are_preserved_not_deleted(final):
    rejected = [r for r in final["records"]
                if r["verification_status"] == "human_rejected"]
    assert sorted(r["candidate_id"] for r in rejected) == [
        "GOLD-B005-01", "GOLD-B005-06", "GOLD-B005-10", "GOLD-B005-13"]
    for record in rejected:
        assert record["human_decision_history"][-1]["notes"]
        assert record["expected_evidence"], "the evidence was stripped"


def test_the_relation_direction_rejection_is_kept_as_evidence(final):
    """B005-10 reversed the documented relation, and that is worth keeping.

    The source says the experimental model rejects caller-supplied `betas` overrides.
    The generated question asked what `betas` overrides. The rejected record stays in
    the batch precisely so the direction check has a case to be measured against.
    """
    record = next(r for r in final["records"]
                  if r["candidate_id"] == "GOLD-B005-10")
    assert record["verification_status"] == "human_rejected"
    assert "RELATION_DIRECTION" in " ".join(record["internal_review_findings"])
    assert "rejects" in " ".join(
        span["evidence_text"] for span in record["expected_evidence"])


# ------------------------------------------------------------------------ the override


def test_a_noncritical_scope_finding_was_accepted_not_deleted(final):
    overridden = {r["candidate_id"]: r for r in final["records"]
                  if r.get("human_scope_override")}
    assert set(overridden) == {"GOLD-B005-03", "GOLD-B005-04"}
    for candidate_id, record in overridden.items():
        assert record["override_reviewer"] == "project_owner", candidate_id
        assert record["scope_status"] == "NONCRITICAL_SCOPE"
        assert record.get("internal_review_findings"), (
            f"{candidate_id} lost the finding the override accepted")


def test_the_closure_reports_every_override(closure, final):
    overridden = {r["candidate_id"] for r in final["records"]
                  if r.get("human_scope_override")
                  or r.get("human_anaphora_override")
                  or r.get("human_dependency_override")}
    reported = {o["candidate_id"] for o in closure["human_overrides"]}
    assert reported == overridden
    assert all(o["finding_retained"] for o in closure["human_overrides"])


# --------------------------------------------------------------------- the eligibility


def test_every_approved_case_passes_the_eligibility_gate(final):
    verified = [r for r in final["records"]
                if r["verification_status"] == "human_verified"]
    assert len(verified) == 15
    for record in verified:
        verdict = evaluate(record)
        assert verdict["holdout_eligible"], (
            f"{record['candidate_id']}: {verdict['failures']}")


def test_a_rejected_case_can_never_be_eligible(final):
    for record in final["records"]:
        if record["verification_status"] != "human_rejected":
            continue
        verdict = evaluate(record)
        assert not verdict["holdout_eligible"]
        assert "human_verified" in {f["condition"] for f in verdict["failures"]}


def test_eligibility_is_derived_at_closure_not_asserted(closure, final):
    verified = [r for r in final["records"]
                if r["verification_status"] == "human_verified"]
    recomputed = sorted(r["candidate_id"] for r in verified
                        if evaluate(r)["holdout_eligible"])
    assert closure["holdout_eligible_ids"] == recomputed
    assert closure["totals"]["holdout_eligible"] == len(recomputed)
    assert closure["not_holdout_eligible"] == []


def test_the_gate_checks_every_condition_it_names(final):
    record = next(r for r in final["records"]
                  if r["verification_status"] == "human_verified")
    assert set(evaluate(record)["conditions_checked"]) == set(HOLDOUT_CONDITIONS)


# -------------------------------------------------------------------------- the closure


def test_closure_counts_match_the_records(closure, final):
    records = final["records"]
    totals = closure["totals"]
    assert totals["candidates"] == len(records)
    assert totals["human_verified"] == sum(
        1 for r in records if r["verification_status"] == "human_verified")
    assert totals["human_rejected"] == sum(
        1 for r in records if r["verification_status"] == "human_rejected")
    assert totals["needs_human_review"] == 0
    assert totals["outstanding_decisions"] == 0
    assert totals["acceptance_rate"] == round(
        totals["human_verified"] / totals["candidates"], 4)


def test_closure_hash_still_covers_the_records(closure, final):
    payload = json.dumps(sorted(final["records"], key=lambda r: r["candidate_id"]),
                         sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert closure["closure_sha256"] == hashlib.sha256(
        payload.encode("utf-8")).hexdigest()
    assert final["closure_sha256"] == closure["closure_sha256"]


def test_closure_records_both_identities(closure, final):
    assert closure["source_batch_sha256"] == final["batch_sha256"]
    assert closure["generation_batch_sha256"] == final["source_batch_sha256"]


def test_closure_says_the_batch_came_back_short(closure):
    """§17: 30 was the target, 19 was the batch, and the gap is the finding."""
    shortfall = closure["generation_shortfall"]
    assert shortfall["target"] == 30
    assert shortfall["exported"] == 19
    assert shortfall["dropped_by_semantic_self_review"] == 27
    assert shortfall["entered_semantic_self_review"] == (
        shortfall["dropped_by_semantic_self_review"] + shortfall["exported"])
    document = Path("experiments/GOLD-001/GOLD-001-batch-005-closure.md").read_text()
    assert "Target 30, exported 19" in document


def test_closure_preserves_the_multi_hop_result(closure):
    """§18: three pairs, one valid chain, nothing new. Not rounded away."""
    search = closure["multi_hop_search"]
    assert search["funnel"]["dependency_pairs_considered"] == 3
    assert search["valid_chains"] == 1
    assert search["exported_chains"] == 0
    assert closure["reasoning_and_shape"]["genuine_multi_hop"] == 0


def test_multi_hop_coverage_is_not_overstated():
    document = Path("experiments/GOLD-001/GOLD-001-batch-005-closure.md").read_text()
    assert "0" in document
    for overstatement in ("strong multi-hop coverage", "multi-hop is covered",
                          "adequate multi-hop"):
        assert overstatement not in document.lower()


def test_closure_documents_the_precheck_limitation(closure):
    precheck = closure["precheck_limitation"]
    assert precheck["candidates"] == 19
    assert precheck["precheck_ready"] == 19
    assert precheck["repaired"] == 7
    assert precheck["reject_recommended"] == 4
    assert precheck["means"] == "structurally capable"
    assert "human approval" in precheck["does_not_mean"]


def test_closure_reports_the_breakdowns_the_brief_asked_for(closure, final):
    from collections import Counter

    verified = [r for r in final["records"]
                if r["verification_status"] == "human_verified"]
    shape = closure["reasoning_and_shape"]
    assert shape["by_reasoning_type_verified"] == dict(
        Counter(r["reasoning_type"] for r in verified))
    assert shape["by_evidence_shape_verified"] == dict(
        Counter(r["evidence_shape"] for r in verified))
    assert closure["by_provider"]["human_verified"] == dict(
        Counter(r["provider"] for r in verified))
    assert closure["by_provider"]["generated"] == dict(
        Counter(r["provider"] for r in final["records"]))


def test_validator_ran_on_the_projection(closure):
    validation = load(VALIDATION)
    assert validation["passed"] is True
    assert closure["validation"]["cases"] == validation["cases"] == 15
    assert closure["validation"]["failures"] == 0
    assert closure["validation"]["projection"] == validation["path"]


# ------------------------------------------------------- inputs for the next batch


def test_generator_defects_became_preregistration_inputs(final):
    prereg = load(PREREG)
    recorded = {d["defect"] for d in final["generator_defects_found"]}
    carried = {entry["defect"] for entry in prereg["inputs"]}
    assert recorded <= carried, "a recorded defect was dropped on the way to batch 006"
    assert {entry["id"] for entry in prereg["inputs"]} == {"A", "B", "C", "D"}
    for entry in prereg["inputs"]:
        assert entry["check"] and entry["verified_by"] and entry["source"]


def test_the_preregistration_inputs_did_not_patch_batch_005(final):
    prereg = load(PREREG)
    assert prereg["source_batch"]["closure_sha256"] == final["closure_sha256"]
    assert "not generated" in prereg["status"]


# ------------------------------------------------------------------------- invariants


def test_project_wide_counts_are_consistent(final):
    status = load(STATUS)
    combined = status["combined"]
    assert combined["human_verified"] == sum(
        b["human_verified"] for b in status["batches"])
    assert combined["holdout_eligible"] == sum(
        b["holdout_eligible"] for b in status["batches"])
    assert combined["human_rejected"] == sum(
        b["human_rejected"] for b in status["batches"])

    row = next(b for b in status["batches"] if b["batch"] == 5)
    assert row["human_verified"] == 15
    assert row["holdout_eligible"] == 15
    assert row["human_rejected"] == 4
    assert row["genuine_multi_hop"] == 0


def test_holdout_is_not_frozen():
    """The count reason expired when the set reached 150; the invariant did not.

    This used to assert the eligible count was under 100, which was the reason no split
    could be frozen at the time. The set has since grown past that, so the assertion is
    now about what has to stay true regardless: nothing is frozen, and the status says
    why in its own words rather than leaving it to be inferred.
    """
    status = load(STATUS)
    assert status["holdout_frozen"] is False
    assert status["reason_not_frozen"]


def test_closed_batches_are_untouched():
    """Closing batch 005 must not have moved a case in any earlier batch."""
    for number, path in CLOSED_BEFORE.items():
        batch = load(Path(path))
        closure = load(Path(
            f"experiments/GOLD-001/GOLD-001-batch-{number:03d}-closure.json"))
        payload = json.dumps(sorted(batch["records"], key=lambda r: r["candidate_id"]),
                             sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        assert closure["closure_sha256"] == hashlib.sha256(
            payload.encode("utf-8")).hexdigest(), f"batch {number:03d} changed"


def test_retrieval_was_not_run(final, closure):
    assert final["retrieval_was_not_run"] is True
    assert final["systems_executed"] == []
    assert closure["retrieval"]["retrieval_was_not_run"] is True
    assert closure["retrieval"]["systems_run_against_these_candidates"] == []
    for record in final["records"]:
        assert "retrieval_rank" not in record
        assert "retrieved_by" not in record


def test_frozen_systems_are_unchanged():
    from rag_v1.systems import FROZEN_HASHES

    assert FROZEN_HASHES == FROZEN_SYSTEMS
