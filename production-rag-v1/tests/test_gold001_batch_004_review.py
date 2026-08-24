"""GOLD-001 batch 004: the review must not be able to manufacture approval.

The batch-004 generation tests check that the batch is structurally sound. These check
the review that followed it — that repairs only ever grow an anchor, that a repaired
record still passes its own precheck, that the packet keeps `precheck_holdout_ready`,
`human_verified` and `holdout_eligible` apart, and that the decisions file ships
undecided.

The load-bearing fact behind all of it: all 15 candidates were precheck-ready before the
review, and the review still found a candidate to reject, ten to repair, and a rule that
applies only on one experimental API surface. A structural check passing is not evidence
that a case is sound.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rag_v1.gold.multihop import PASS, composition_check
from rag_v1.gold.normalisation import contains_claim_string

BATCH = Path("evals/review/gold_review_batch_004.json")
REPAIRS = Path("evals/review/gold_review_batch_004_repairs.json")
PACKET = Path("evals/review/gold_batch_004_qc.json")
DECISIONS = Path("evals/review/human_decisions_batch_004.json")
REVIEW = Path("experiments/GOLD-001/GOLD-001-batch-004-internal-review.json")
NEAR_MISS = Path("experiments/GOLD-001/BATCH-004-near-miss-multihop-review.json")
FROZEN_SYSTEMS = {
    "SYSTEM-A-GLOBAL":
        "9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38",
    "SYSTEM-B-DOC-C":
        "304c350940b83733df6043ae3a8abdcbcde33d16950730127aa9f1f39494388b",
}


def load(path: Path) -> dict:
    if not path.exists():
        pytest.skip(f"{path} has not been generated")
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def batch() -> dict:
    return load(BATCH)


@pytest.fixture(scope="module")
def repairs() -> dict:
    return load(REPAIRS)


@pytest.fixture(scope="module")
def packet() -> dict:
    return load(PACKET)


@pytest.fixture(scope="module")
def decisions() -> dict:
    return load(DECISIONS)


# ------------------------------------------------------- repairs are auditable repairs


def test_repairs_are_computed_against_this_batch(batch, repairs):
    assert repairs["source_batch_sha256"] == batch["batch_sha256"]


def test_generation_artifact_is_untouched_by_the_review(batch):
    """§12: candidate data and generation history stay auditable."""
    for record in batch["records"]:
        assert record["verification_status"] == "candidate_unverified"
        assert "anchor_revisions" not in record, (
            "a repair was written into the generation artifact; repairs belong in "
            "gold_review_batch_004_repairs.json")


def test_every_anchor_repair_only_grows_outward(batch, repairs):
    """The strict-superset invariant. An anchor that moves is a different claim."""
    generated = {r["candidate_id"]: r for r in batch["records"]}
    for record in repairs["records"]:
        original = {s["evidence_id"]: s
                    for s in generated[record["candidate_id"]]["expected_evidence"]}
        for revision in record.get("anchor_revisions", []):
            if revision["action"] != "extend_boundary":
                continue
            old = original[revision["evidence_id"]]
            assert revision["old_char_start"] == old["char_start"]
            assert revision["old_char_end"] == old["char_end"]
            assert revision["new_char_start"] <= revision["old_char_start"]
            assert revision["new_char_end"] >= revision["old_char_end"]
            assert revision["old_evidence_text"] in revision["new_evidence_text"]


def test_repairs_preserve_the_pre_repair_hash(batch, repairs):
    """An owner must be able to see exactly what they are no longer approving."""
    for record in repairs["records"]:
        for revision in record.get("anchor_revisions", []):
            if revision["action"] != "extend_boundary":
                continue
            assert revision["old_evidence_hash"] != revision["new_evidence_hash"]
            assert hashlib.sha256(
                revision["new_evidence_text"].encode("utf-8")
            ).hexdigest() == revision["new_evidence_hash"]


def test_text_rewrites_keep_the_generated_wording(batch, repairs):
    generated = {r["candidate_id"]: r for r in batch["records"]}
    for record in repairs["records"]:
        for revision in record.get("revisions", []):
            source = generated[record["candidate_id"]]
            if revision["field"] in source:
                assert revision["from"] == source[revision["field"]] or any(
                    r["field"] == revision["field"] and r["revision"] < revision["revision"]
                    for r in record["revisions"])
            assert revision["author"], "a revision must name who made it"
            assert revision["reason"], "a revision must say why"


def test_repaired_records_still_hash_and_scope_correctly(repairs):
    for record in repairs["records"]:
        for span in record["expected_evidence"]:
            digest = hashlib.sha256(span["evidence_text"].encode("utf-8")).hexdigest()
            assert digest == span["evidence_hash"], record["candidate_id"]
            assert span["evidence_char_length"] == span["char_end"] - span["char_start"]
            assert span["critical_strings"]
            for string in span["critical_strings"]:
                assert contains_claim_string(span["evidence_text"], string), (
                    f"{record['candidate_id']} {span['evidence_id']}: {string!r}")


def test_generic_identifier_questions_carry_their_scope(repairs):
    """§6: `timezone` and `input_filter` exist in more than one API."""
    scoped = {
        "GOLD-B004-06": "user_location",
        "GOLD-B004-13": "handoff",
        "GOLD-B004-14": "handoff()",
    }
    records = {r["candidate_id"]: r for r in repairs["records"]}
    for candidate_id, scope in scoped.items():
        record = records[candidate_id]
        assert scope in record["question"], (
            f"{candidate_id} names an identifier without saying what it belongs to")
        # The scope must be in the evidence too, not only asserted in the question.
        assert any(scope.rstrip("()") in span["evidence_text"]
                   for span in record["expected_evidence"]), (
            f"{candidate_id}: the question's scope is not established by any span")


def test_no_critical_string_is_a_truncation(repairs):
    """Two critical strings were 60-character cuts through a markdown link."""
    for record in repairs["records"]:
        for span in record["expected_evidence"]:
            for string in span["critical_strings"]:
                assert not string.endswith(("List_of", "When set, th")), string
                opens = string.count("[") + string.count("(")
                closes = string.count("]") + string.count(")")
                if "](" in string:
                    assert opens == closes, f"unbalanced markdown link: {string!r}"


def test_multi_span_records_require_all_their_evidence(repairs):
    for record in repairs["records"]:
        multi = len(record["expected_evidence"]) > 1
        assert record["requires_all_evidence"] is multi, record["candidate_id"]
        assert (record["evidence_shape"] == "single_span") is not multi


def test_claim_map_covers_every_claim(repairs):
    for record in repairs["records"]:
        ids = {s["evidence_id"] for s in record["expected_evidence"]}
        assert len(record["claim_evidence_map"]) == len(record["atomic_claims"])
        for mapping in record["claim_evidence_map"]:
            assert mapping["evidence_id"] in ids


# ------------------------------------------------------------------ the multi-hop case


def test_multi_hop_still_composes_after_repair(repairs):
    record = next((r for r in repairs["records"]
                   if r["reasoning_type"] == "genuine_multi_hop"), None)
    if record is None:
        pytest.skip("no genuine_multi_hop candidate was repaired")
    first, second = record["expected_evidence"][:2]
    verdict = composition_check(
        record["bridge_entity"], first["evidence_text"], second["evidence_text"],
        first["critical_strings"], second["critical_strings"])
    assert verdict["multi_hop_composition_check"] == PASS, verdict["reasons"]
    assert record["requires_all_evidence"] is True
    assert record["needs_human_interpretation"] is True


def test_multi_hop_scope_lives_in_the_evidence_not_a_heading(repairs):
    """§2D: a case may not lean on a section heading outside its spans.

    The generated candidate's rejection rule applies on the hosted multi-agent surface
    only, and said so only in its section path. If the question claims a scope, some
    span has to establish it.
    """
    record = next((r for r in repairs["records"]
                   if r["reasoning_type"] == "genuine_multi_hop"), None)
    if record is None:
        pytest.skip("no genuine_multi_hop candidate was repaired")
    assert "hosted agents" in record["question"]
    assert any("hosted agents" in span["evidence_text"]
               for span in record["expected_evidence"])


def test_multi_hop_state_implication_is_recorded(repairs):
    record = next((r for r in repairs["records"]
                   if r["reasoning_type"] == "genuine_multi_hop"), None)
    if record is None:
        pytest.skip("no genuine_multi_hop candidate was repaired")
    for field in ("bridge_entity", "bridge_relationship", "hop_1_claim", "hop_2_claim",
                  "composed_claim", "composed_answer",
                  "why_span_1_alone_is_insufficient",
                  "why_span_2_alone_is_insufficient"):
        assert record[field], field
    # The chain runs through the value: True is one of the values that is not False.
    assert "True" in record["expected_evidence"][0]["critical_strings"]
    assert "False" in record["expected_evidence"][1]["critical_strings"]


def test_semantic_review_answers_every_question():
    review = load(REVIEW)
    semantic = review["multi_hop_semantic_review"]
    assert [q["id"] for q in semantic["questions"]] == ["A", "B", "C", "D", "E", "F"]
    for question in semantic["questions"]:
        assert question["answer"] and question["reasoning"]


# --------------------------------------------------------------- ambiguity vs lookups


def test_ambiguity_cases_declare_their_readings(repairs, batch):
    records = {r["candidate_id"]: r for r in batch["records"]}
    records.update({r["candidate_id"]: r for r in repairs["records"]})
    for record in records.values():
        if record["reasoning_type"] != "ambiguity_disambiguation":
            continue
        assert record["ambiguous_term"]
        assert len(record["candidate_interpretations"]) >= 2
        assert record["required_scope_to_answer"]
        readings = {r["meaning"] for r in record["candidate_interpretations"]}
        assert len(readings) >= 2, (
            f"{record['candidate_id']}: the readings are identical, so nothing needs "
            "disambiguating")


def test_two_independent_lookups_are_not_kept_as_ambiguity(repairs):
    """§7: a discriminator constant per event type is a lookup, not an ambiguity."""
    review = repairs["review"]
    assert review["GOLD-B004-08"]["status"] == "REJECT_RECOMMENDED"
    assert any("NOT_AMBIGUITY" in finding
               for finding in review["GOLD-B004-08"]["findings"])


def test_configuration_interaction_labels_were_checked(repairs):
    """§8: a single conditional fact is not an interaction between settings."""
    review = repairs["review"]
    relabelled = {cid: d for cid, d in review.items() if "reasoning_type_was" in d}
    assert relabelled, "the taxonomy review recorded no relabels at all"
    for candidate_id, decision in relabelled.items():
        assert decision["reasoning_type"] != decision["reasoning_type_was"], candidate_id
        assert any("CATEGORY" in finding for finding in decision["findings"]), (
            f"{candidate_id} was relabelled without a recorded reason")


# ------------------------------------------------------------- the packet and decisions


def test_packet_keeps_the_three_states_apart(packet):
    """The packet is a request for decisions and records none of its own."""
    assert packet["human_verified"] == 0
    assert packet["holdout_eligible"] == 0
    assert packet["precheck_holdout_ready"] == len(packet["candidates"])
    for entry in packet["candidates"]:
        assert entry["record"]["verification_status"] == "candidate_unverified"


def test_every_candidate_has_exactly_one_decision_slot(decisions):
    """The packet ships undecided; once decided, every candidate is accounted for.

    This test asserted that every decision was ``null``, which was right while the
    packet was waiting for a person and wrong the moment one answered. What has to hold
    either way is that there is one slot per candidate, no duplicates, and no decision
    outside the allowed set — a filled-in file must not smuggle in a candidate the
    packet never showed.
    """
    rows = decisions["decisions"]
    assert len(rows) == 15
    assert len({r["candidate_id"] for r in rows}) == 15
    for row in rows:
        assert row["decision"] in (None, "APPROVE", "REJECT", "NEEDS_EDIT")
    if decisions["decided_by"] is None:
        assert all(r["decision"] is None for r in rows), (
            "decisions were recorded without naming who made them")


def test_repaired_candidates_require_a_hash_to_approve(decisions, repairs):
    """A repaired candidate carries a hash slot per span, empty until it is approved."""
    repaired = {r["candidate_id"]: r for r in repairs["records"]}
    for row in decisions["decisions"]:
        pinned = row["approves_evidence_hash"]
        if row["candidate_id"] not in repaired:
            assert row["was_repaired"] is False
            continue
        assert row["was_repaired"] is True
        assert isinstance(pinned, list)
        spans = repaired[row["candidate_id"]]["expected_evidence"]
        assert len(pinned) == len(spans)
        if row["decision"] == "APPROVE":
            assert pinned == [s["evidence_hash"] for s in spans], row["candidate_id"]
        elif row["decision"] is None:
            assert all(value is None for value in pinned)


def test_internal_review_status_is_not_a_decision(decisions):
    """A recommendation must not be readable as an approval, or as a veto.

    The status field sits next to the decision field in the same row, and the risk is
    that one is read as the other. It is not: a NEEDS_REPAIR candidate can be approved
    once repaired, and a REJECT_RECOMMENDED one can be approved over the
    recommendation. Only the ``decision`` field decides anything, and only a person
    fills it in.
    """
    for row in decisions["decisions"]:
        assert row["internal_review_status"] in (
            "READY_FOR_OWNER_REVIEW", "NEEDS_REPAIR", "REJECT_RECOMMENDED")
    statuses = {r["candidate_id"]: r["internal_review_status"]
                for r in decisions["decisions"]}
    outcomes = {r["candidate_id"]: r["decision"] for r in decisions["decisions"]}
    if all(value is None for value in outcomes.values()):
        return
    repaired_and_approved = [cid for cid, status in statuses.items()
                             if status == "NEEDS_REPAIR" and outcomes[cid] == "APPROVE"]
    assert repaired_and_approved, (
        "no NEEDS_REPAIR candidate was approved, which would mean the recommendation "
        "was being read as a verdict")


# ------------------------------------------------------------------------- invariants


def test_retrieval_was_not_run_anywhere(batch, repairs, packet):
    for payload in (batch, repairs, packet):
        assert payload["retrieval_was_not_run"] is True
        assert payload["systems_executed"] == []
    for record in repairs["records"]:
        assert record["retrieval_was_not_run"] is True
    blob = json.dumps(repairs["records"]).lower()
    for label in ("routing_heavy", "passage_heavy", "hard_for_bm25", "recall@", "ndcg"):
        assert label not in blob


def test_near_miss_diagnostic_is_diagnostic_only(batch):
    near_miss = load(NEAR_MISS)
    assert near_miss["diagnostic_only"] is True
    assert near_miss["promoted_to_batch_004"] == 0
    assert near_miss["batch_004_regenerated"] is False
    generated = {(s["version_id"], s["char_start"], s["char_end"])
                 for r in batch["records"] for s in r["expected_evidence"]}
    for finding in near_miss["findings"]:
        assert finding["verdict"] in (
            "CORRECT_REJECTION", "POSSIBLE_CHECK_FALSE_NEGATIVE", "UNCERTAIN")
        assert finding["reviewer_reasoning"]
        for span in (finding["span_1"], finding["span_2"]):
            key = (span["version_id"], span["char_start"], span["char_end"])
            assert key not in generated, (
                "a near-miss span reached the batch — §5 forbids promoting one")


def test_frozen_systems_are_unchanged():
    """The frozen configs still hash to what was frozen.

    This looked for an ``evals/frozen`` directory that does not exist, so it skipped —
    and a skipping test is not coverage of the invariant it names. The hashes are
    computed from ``rag_v1.systems`` at import, which is where a change to either
    system would actually show up.
    """
    from rag_v1.systems import FROZEN_HASHES

    assert FROZEN_HASHES == FROZEN_SYSTEMS

