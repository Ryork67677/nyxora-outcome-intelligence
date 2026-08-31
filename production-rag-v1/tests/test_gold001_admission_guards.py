"""Guards on the 150-case admission: the ones that can be tested without the packet.

Two HA packets exist in this project and they share the ``HA-nn`` namespace while holding
different cases. That is the whole hazard: an import addressed to HA-01 … HA-60 looks
like it would land correctly on a 64-case packet whose first 24 cases really are the same
facts, and would silently attach owner approval to 36 cases nobody reviewed.

So the invariants here are about identity and about not claiming more than was
established: a short id is not an identity, the alternate packet is not admitted, the
final count is derived rather than asserted, and the corpus limitation still blocks
retrieval. Nothing here runs retrieval or touches a closed batch.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

EXP = Path("experiments/GOLD-001")
STATUS = EXP / "GOLD-001-eligibility-status.json"
DISPOSITION = EXP / "GOLD-001-alternate-HA-packet-disposition.json"
BLOCKED = EXP / "GOLD-001-150-admission-blocked-002.json"
LIMITATION = EXP / "GOLD-001-corpus-reproduction-limitation.json"
REVIEW = EXP / "GOLD-001-independent-review-chatgpt-HA01-HA60.json"

#: The repaired HA-47 span, verified against the frozen ``docs/handoffs.md`` at its
#: pinned commit. Pinned here so a later edit to the record cannot quietly move it.
HA47_REPAIRED_SHA = "e894c94d831ccfd2678f4cd132b72b52e44770d07ebeaab6c51e96e0e312a203"
HA47_OLD_E1_SHA = "5e36f5ff857cdcd795d4e8133de6072b5a8e7588be44fc21516e24a5e97f5b34"
HA47_OLD_E2_SHA = "f4d4ee514ca2285d8cc67313a02b7cb7382d11cc3cedfd998733884d98321387"


def load(path: Path) -> dict:
    if not path.exists():
        pytest.skip(f"{path} is not present")
    return json.loads(path.read_text())


# --------------------------------------------------------- the two packets are not one

def test_the_alternate_64_case_packet_is_not_the_packet_of_record():
    disposition = load(DISPOSITION)

    assert "NOT_ADMITTED" in disposition["status"]
    assert "NOT_THE_PACKET_OF_RECORD" in disposition["status"]
    assert "PRESERVED_FOR_AUDIT" in disposition["status"]


def test_the_alternate_packet_holds_no_approval():
    unchanged = load(DISPOSITION)["records_are_unchanged"]

    assert unchanged["human_verified"] == 0
    assert unchanged["holdout_eligible"] == 0
    assert unchanged["verification_status"] == ["unreviewed"]


def test_the_namespace_collision_is_recorded_rather_than_resolved_by_renumbering():
    """The fix is never to renumber one packet onto the other."""
    disposition = load(DISPOSITION)
    collision = disposition["namespace_collision"]

    assert collision["evidence"], "the collision must be evidenced, not asserted"
    assert collision["consequence"].startswith("No candidate")
    assert "no owner decision addressed to HA-01" in collision["consequence"]
    assert "renumber" not in json.dumps(collision).lower()


# ------------------------------------------------- a short id is not an identity

def test_an_import_needs_evidence_identity_not_a_short_ha_number():
    binding = load(BLOCKED)["step_3_evidence_identity_binding"]

    for field in ("version_id", "char_start", "char_end", "evidence_hash"):
        assert field in binding["required"]
        assert field in binding["missing"]


def test_the_supplied_review_is_stored_unbound():
    review = load(REVIEW)

    assert review["binding_status"] == "UNBOUND"
    assert review["confers_no_approval"]


def test_the_stored_review_counts_are_recomputed_and_agree():
    review = load(REVIEW)
    records = review["review"]["records"]

    recomputed = {"PASS": 0, "PASS_WITH_NONCRITICAL_ANAPHORA_OVERRIDE": 0,
                  "FIX_REQUIRED_THEN_APPROVE": 0}
    for record in records:
        recomputed[record["chatgpt_independent_verdict"]] += 1

    assert len(records) == 60
    assert [r["case_id"] for r in records] == [f"HA-{i:02d}" for i in range(1, 61)]
    assert recomputed["PASS"] == 58
    assert recomputed["PASS_WITH_NONCRITICAL_ANAPHORA_OVERRIDE"] == 1
    assert recomputed["FIX_REQUIRED_THEN_APPROVE"] == 1


def test_ha15_carries_an_override_verdict_and_ha47_a_fix_verdict():
    records = {r["case_id"]: r for r in load(REVIEW)["review"]["records"]}

    assert records["HA-15"]["chatgpt_independent_verdict"] == (
        "PASS_WITH_NONCRITICAL_ANAPHORA_OVERRIDE")
    assert records["HA-47"]["chatgpt_independent_verdict"] == "FIX_REQUIRED_THEN_APPROVE"


# ----------------------------------------------------------- the HA-47 repair values

def test_the_repaired_ha47_hash_is_the_verified_frozen_source_hash():
    repair = load(BLOCKED)["step_6_ha47_repair_revalidated"]

    assert repair["repaired"]["sha256"] == HA47_REPAIRED_SHA
    assert repair["old_E1"]["sha256"] == HA47_OLD_E1_SHA
    assert repair["old_E2"]["sha256"] == HA47_OLD_E2_SHA
    assert repair["repaired"]["span"] == "4308:4916"


def test_the_repair_is_recorded_as_applied_to_nothing():
    """It belongs to a record this environment does not hold."""
    repair = load(BLOCKED)["step_6_ha47_repair_revalidated"]

    assert repair["applied_to"] is None


def test_a_paragraph_break_is_not_an_eligibility_condition():
    """Read from the predicate, not waived."""
    from rag_v1.gold.eligibility import HOLDOUT_CONDITIONS

    assert not any("paragraph" in condition for condition in HOLDOUT_CONDITIONS)
    assert load(BLOCKED)["step_7_paragraph_break_rule"]["resolution"] == (
        "paragraph_break_present = true, eligibility_blocking = false")


# ------------------------------------------------------------- nothing was claimed

def test_the_final_count_is_derived_from_the_authoritative_record():
    status = json.loads(STATUS.read_text())
    combined = status["combined"]

    assert combined["human_verified"] == combined["candidates"] - combined["human_rejected"]
    assert combined["holdout_eligible"] <= combined["human_verified"]


def test_the_only_group_added_to_the_historical_90_is_the_packet_of_record():
    """Attempt 002 blocked because 60 approvals had no records to bind to. When they
    arrived, exactly one group joined the six historical batches — and not the
    alternate packet."""
    status = json.loads(STATUS.read_text())
    groups = {b["label"]: b for b in status["batches"]}
    historical = sum(v["holdout_eligible"] for k, v in groups.items()
                     if k != "HA-01–HA-60")

    assert historical == 90
    assert status["combined"]["human_rejected"] == 9
    assert status["combined"]["genuine_multi_hop"] == 1
    assert json.loads(
        Path("evals/review/gold_review_HA01_HA60_final.json").read_text()
    )["source_packet_sha256"] == (
        "bf6190fc53ee4ada6c948093d30e8fa7feac3dbf3300918ec75886d2a5a8f786")


def test_the_blocked_record_is_kept_and_marked_superseded():
    """It stays as the history of attempt 002 rather than being rewritten."""
    blocked = load(BLOCKED)

    assert blocked["disposition"].startswith("STOPPED")
    assert blocked["superseded_by"]["artifacts"]
    assert "not the project's current state" in blocked["superseded_by"]["note"]


def test_the_protocol_deviation_names_the_packet_whose_admission_it_excuses():
    """The reason it could not be written during attempt 002: it needs its packet."""
    deviation = load(EXP / "GOLD-001-protocol-deviation-001.json")
    grok = next(m for m in deviation["mitigations_actually_performed"]
                if "Grok" in m["mitigation"])

    assert "GOLD-001-protocol-deviation-001.{json,md}" in load(BLOCKED)["not_written"]
    assert grok["verified_from"] == "the embedded grok-review-results.json"


# ------------------------------------------------------- retrieval stays blocked

def test_corpus_reproduction_is_incomplete_and_blocks_retrieval():
    limitation = load(LIMITATION)

    assert limitation["CORPUS_REPRODUCTION_INCOMPLETE"] is True
    assert limitation["effect"] == "RETRIEVAL_BLOCKED"
    assert limitation["outstanding"]["anthropic_documents"] == 139


def test_recovering_evidence_excerpts_does_not_reproduce_the_corpus():
    limitation = load(LIMITATION)

    assert "does not reproduce the corpus" in limitation[
        "why_partial_recovery_does_not_close_this"]


@pytest.mark.parametrize("system", ["SYSTEM-A", "SYSTEM-B", "BM25", "MiniLM", "DOC-C",
                                    "reranking", "answer generation"])
def test_every_retrieval_system_is_named_as_blocked(system):
    assert system in load(LIMITATION)["systems_that_must_not_run_until_then"]


def test_retrieval_was_not_run_and_no_split_is_frozen():
    status = json.loads(STATUS.read_text())

    assert status["retrieval_was_not_run"] is True
    assert status["holdout_frozen"] is False


def test_the_blocked_record_reports_no_systems_executed():
    assert load(BLOCKED)["authoritative_state_unchanged"]["systems_executed"] == []


# ------------------------------------------------------- historical state untouched

def test_the_nine_historical_rejections_remain_rejected():
    status = json.loads(STATUS.read_text())

    assert status["combined"]["human_rejected"] == 9


def test_the_stored_review_records_its_own_provenance_hash():
    review = load(REVIEW)

    assert len(review["source_sha256"]) == 64
    assert int(review["source_sha256"], 16) >= 0
