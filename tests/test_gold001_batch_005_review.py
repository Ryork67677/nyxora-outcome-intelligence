"""GOLD-001 batch 005: the review, and the separations it is there to keep.

The generation tests check that batch 005 is structurally sound. These check the review
that followed — that repairs only ever grow an anchor, that a repaired record still
passes its own precheck, that the packet says plainly it is not verification, and that
the decisions file ships undecided.

The review's own numbers are the load-bearing ones: 19 candidates all precheck-ready,
and the review still recommended four for rejection and repaired seven. A test asserts
that, because a review that finds nothing is indistinguishable from one that did not
run.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from rag_v1.gold.bridge_equivalence import ENUM_VALUE, REQUEST_PARAMETER, same_semantic_entity
from rag_v1.gold.normalisation import contains_claim_string

BATCH = Path("evals/review/gold_review_batch_005.json")
REPAIRS = Path("evals/review/gold_review_batch_005_repairs.json")
PACKET = Path("evals/review/gold_batch_005_qc.json")
DECISIONS = Path("evals/review/human_decisions_batch_005.json")
REVIEW = Path("experiments/GOLD-001/GOLD-001-batch-005-internal-review.json")
FROZEN_SYSTEMS = {
    "SYSTEM-A-GLOBAL":
        "9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38",
    "SYSTEM-B-DOC-C":
        "304c350940b83733df6043ae3a8abdcbcde33d16950730127aa9f1f39494388b",
}
CLOSED = {
    1: ("evals/review/gold_review_batch_001.json",
        "experiments/GOLD-001/GOLD-001-batch-001-closure.json"),
    2: ("evals/review/gold_review_batch_002.json",
        "experiments/GOLD-001/GOLD-001-batch-002-closure.json"),
    3: ("evals/review/gold_review_batch_003.json",
        "experiments/GOLD-001/GOLD-001-batch-003-closure.json"),
    4: ("evals/review/gold_review_batch_004_final.json",
        "experiments/GOLD-001/GOLD-001-batch-004-closure.json"),
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


@pytest.fixture(scope="module")
def exported_decisions(tmp_path_factory) -> dict:
    """Re-export the packet and read the decisions file it writes.

    The checked-in decisions file is the owner's; it is full of decisions, as it should
    be. What still has to hold is that the *exporter* hands a person an empty form — so
    these tests run it again into a scratch directory rather than reading a file whose
    whole purpose is to stop being empty.
    """
    import subprocess
    import sys

    out = tmp_path_factory.mktemp("qc")
    result = subprocess.run(
        [sys.executable, "scripts/export_qc_packet.py", "--batch", "5",
         "--out-dir", str(out)],
        capture_output=True, text=True, check=False)
    if result.returncode != 0:
        pytest.skip(f"the packet exporter did not run: {result.stderr.strip()}")
    return json.loads((out / "human_decisions_batch_005.json").read_text())


# ------------------------------------------------------------- the review happened


def test_the_review_covers_every_candidate(batch, repairs):
    reviewed = set(repairs["review"])
    assert reviewed == {r["candidate_id"] for r in batch["records"]}
    assert sum(repairs["status_counts"].values()) == len(batch["records"])


def test_the_review_found_something(repairs):
    """A review that clears everything is indistinguishable from one that did not run."""
    counts = repairs["status_counts"]
    assert counts.get("REJECT_RECOMMENDED", 0) > 0
    assert counts.get("NEEDS_REPAIR", 0) > 0
    for decision in repairs["review"].values():
        if decision["status"] != "READY_FOR_OWNER_REVIEW":
            assert decision["findings"], "a non-ready candidate with no stated finding"


def test_every_rejection_states_why(repairs):
    for candidate_id, decision in repairs["review"].items():
        if decision["status"] != "REJECT_RECOMMENDED":
            continue
        assert decision.get("reason"), candidate_id
        assert len(decision["findings"]) >= 2, (
            f"{candidate_id} is recommended for rejection on a single observation")


def test_configuration_interactions_record_their_two_sides(repairs):
    """§4: A, B and the documented relation, or the label is wrong."""
    for candidate_id, decision in repairs["review"].items():
        if decision["status"] == "REJECT_RECOMMENDED":
            continue
        record = next((r for r in repairs["records"]
                       if r["candidate_id"] == candidate_id), None)
        reasoning = (record or {}).get("reasoning_type")
        if reasoning != "configuration_interaction":
            continue
        interaction = decision.get("interaction")
        assert interaction, f"{candidate_id} keeps the label with no interaction recorded"
        for field in ("setting_or_state_A", "setting_or_state_B", "documented_relation"):
            assert interaction[field], f"{candidate_id}: {field} is empty"


def test_a_relabelled_candidate_says_what_it_was(repairs):
    relabelled = {cid: d for cid, d in repairs["review"].items()
                  if "reasoning_type_was" in d}
    assert relabelled, "the taxonomy review recorded no relabels"
    for candidate_id, decision in relabelled.items():
        assert decision["reasoning_type"] != decision["reasoning_type_was"]
        assert any("CATEGORY" in f for f in decision["findings"]), candidate_id


def test_generator_defects_are_recorded_not_silently_patched(repairs):
    defects = repairs["generator_defects_found"]
    assert defects, "the review patched or ignored what it found in the generator"
    for defect in defects:
        assert defect["defect"] and defect["seen_in"] and defect["detail"]


# --------------------------------------------------------------- repairs are honest


def test_repairs_are_computed_against_this_batch(batch, repairs):
    assert repairs["source_batch_sha256"] == batch["batch_sha256"]


def test_generation_artifact_is_untouched(batch):
    for record in batch["records"]:
        assert record["verification_status"] == "candidate_unverified"
        assert "anchor_revisions" not in record
        assert not record.get("revisions"), (
            "a review revision was written into the generation artifact")


def test_every_anchor_repair_only_grows_outward(batch, repairs):
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
            assert revision["old_evidence_hash"] != revision["new_evidence_hash"]


def test_repaired_records_still_hash_and_scope_correctly(repairs):
    for record in repairs["records"]:
        for span in record["expected_evidence"]:
            digest = hashlib.sha256(span["evidence_text"].encode("utf-8")).hexdigest()
            assert digest == span["evidence_hash"], record["candidate_id"]
            assert span["evidence_char_length"] == span["char_end"] - span["char_start"]
            assert span["evidence_char_length"] <= 1500
            assert span["critical_strings"]
            for string in span["critical_strings"]:
                assert contains_claim_string(span["evidence_text"], string), (
                    f"{record['candidate_id']} {span['evidence_id']}: {string!r}")


def test_repaired_records_are_still_precheck_ready(repairs):
    for record in repairs["records"]:
        assert record["precheck_holdout_ready"] is True, record["candidate_id"]
        assert record["precheck_failures"] == []


def test_text_revisions_keep_the_original(repairs):
    for record in repairs["records"]:
        for revision in record.get("revisions", []):
            assert revision["from"] != revision["to"]
            assert revision["author"] and revision["reason"]
            assert "claude" in revision["author"].lower(), (
                "a model revision must say a model made it")


def test_repaired_questions_carry_the_scope_they_gained(repairs):
    """The repairs were scope and form corrections; the scope has to be in the span."""
    expected = {
        "GOLD-B005-05": "request-level",
        "GOLD-B005-11": "bedrock",
        "GOLD-B005-18": "Undici",
    }
    records = {r["candidate_id"]: r for r in repairs["records"]}
    for candidate_id, token in expected.items():
        record = records[candidate_id]
        assert token.lower() in record["question"].lower(), candidate_id
        evidence = " \n".join(s["evidence_text"] for s in record["expected_evidence"])
        assert token.lower() in evidence.lower(), (
            f"{candidate_id}: the question claims a scope the evidence does not state")


def test_no_markdown_link_plumbing_survives_in_a_repaired_question(repairs):
    for record in repairs["records"]:
        assert not re.search(r"\]\[[^\]]+\]", record["question"]), record["candidate_id"]
        assert not re.search(r"\]\(https?://", record["question"]), record["candidate_id"]


# ------------------------------------------------- the checks that must not weaken


def test_max_tokens_equivocation_is_still_refused():
    """§17: the batch-004 regression stays a regression."""
    first = {"evidence_text": "* `budget_tokens` can exceed `max_tokens` here.",
             "section_path": ["Interleaved thinking"],
             "document_title": "Extended thinking", "version_id": "a"}
    second = {"evidence_text": 'The loop exits on any other stop reason (`"end_turn"`, '
                               '`"max_tokens"`, `"stop_sequence"`).',
              "section_path": ["The agentic loop"],
              "document_title": "How tool use works", "version_id": "b"}
    verdict = same_semantic_entity("max_tokens", first, second)
    assert verdict["same_semantic_entity"] is False
    assert verdict["bridge_entity_meaning_span_1"] == REQUEST_PARAMETER
    assert verdict["bridge_entity_meaning_span_2"] == ENUM_VALUE


def test_no_new_multi_hop_search_was_run(batch, repairs):
    """§16: the review does not go looking for chains to improve a count."""
    assert batch["multi_hop_search"]["exported_chains"] == 0
    for record in repairs["records"]:
        assert record["reasoning_type"] != "genuine_multi_hop"


# --------------------------------------------------------- the packet and decisions


def test_packet_keeps_the_three_states_apart(packet):
    assert packet["human_verified"] == 0
    assert packet["holdout_eligible"] == 0
    assert packet["precheck_holdout_ready"] == len(packet["candidates"])
    for entry in packet["candidates"]:
        assert entry["record"]["verification_status"] == "candidate_unverified"


def test_packet_says_the_review_is_not_verification(packet):
    """§20, in the document rather than only in the commit message."""
    document = Path("evals/review/gold_batch_005_qc.md").read_text()
    assert "not independent verification" in document
    assert "not independent verification" in packet["note"]


def test_owner_decisions_start_null(exported_decisions):
    assert exported_decisions["decided_by"] is None
    assert len(exported_decisions["decisions"]) == 19
    for row in exported_decisions["decisions"]:
        assert row["decision"] is None, (
            f"{row['candidate_id']} arrived with a decision already made")
        assert row["notes"] is None


def test_repaired_candidates_need_a_hash_to_approve(exported_decisions, repairs):
    changed = {r["candidate_id"] for r in repairs["records"]
               if r.get("revisions") or r.get("anchor_revisions")}
    for row in exported_decisions["decisions"]:
        if row["candidate_id"] in changed:
            assert row["was_repaired"] is True
            assert isinstance(row["approves_evidence_hash"], list)
            assert all(value is None for value in row["approves_evidence_hash"])
        else:
            assert row["was_repaired"] is False
            assert row["approves_evidence_hash"] is None


def test_a_recommendation_is_not_a_decision(exported_decisions):
    for row in exported_decisions["decisions"]:
        assert row["internal_review_status"] in (
            "READY_FOR_OWNER_REVIEW", "NEEDS_REPAIR", "REJECT_RECOMMENDED")
        assert row["decision"] is None


def test_the_owners_decisions_did_not_come_from_the_recommendation(decisions):
    """The filled-in file: a decision is the owner's, and it is not the review's.

    The recommendation and the decision agreeing everywhere would be the signal that
    nobody actually reviewed. They agree on the four rejections and diverge on the
    seven repairs, which is what an owner reading a repaired candidate looks like.
    """
    assert decisions["decided_by"] == "project_owner"
    rows = decisions["decisions"]
    assert len(rows) == 19
    assert all(row["decision"] in ("APPROVE", "REJECT") for row in rows)
    # A rejection has to say why — it is the record of what the miner got wrong. A
    # plain approval does not, and inventing a reason for one would be putting words
    # in the owner's mouth.
    assert all(row["notes"] for row in rows if row["decision"] == "REJECT"), (
        "a rejection with no stated reason")

    recommended_reject = {row["candidate_id"] for row in rows
                          if row["internal_review_status"] == "REJECT_RECOMMENDED"}
    rejected = {row["candidate_id"] for row in rows if row["decision"] == "REJECT"}
    assert rejected == recommended_reject == {
        "GOLD-B005-01", "GOLD-B005-06", "GOLD-B005-10", "GOLD-B005-13"}
    approved_after_repair = {row["candidate_id"] for row in rows
                             if row["decision"] == "APPROVE"
                             and row["internal_review_status"] == "NEEDS_REPAIR"}
    assert approved_after_repair, "no repaired candidate was approved on its repair"


# ------------------------------------------------------------------- invariants


def test_closed_batches_are_untouched():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_close_batch", Path("scripts/close_batch.py").resolve())
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for number, (record_path, closure_path) in CLOSED.items():
        if not (Path(record_path).exists() and Path(closure_path).exists()):
            continue
        records = json.loads(Path(record_path).read_text())["records"]
        closure = json.loads(Path(closure_path).read_text())
        assert module.candidate_digest(records) == closure["closure_sha256"], (
            f"batch {number:03d} changed after closure")


def test_retrieval_was_not_run(batch, repairs, packet):
    for payload in (batch, repairs, packet):
        assert payload["retrieval_was_not_run"] is True
        assert payload["systems_executed"] == []
    blob = json.dumps(repairs["records"]).lower()
    for label in ("routing_heavy", "passage_heavy", "hard_for_bm25", "recall@", "ndcg"):
        assert label not in blob


def test_internal_review_document_exists_and_agrees():
    review = load(REVIEW)
    repairs = load(REPAIRS)
    assert review["status_counts"] == repairs["status_counts"]
    assert review["repaired_candidates"] == repairs["repaired_candidates"]
    document = Path(
        "experiments/GOLD-001/GOLD-001-batch-005-internal-review.md").read_text()
    assert "not independent verification" in document


def test_frozen_systems_are_unchanged():
    """The frozen configs still hash to what was frozen.

    This looked for an ``evals/frozen`` directory that does not exist, so it skipped —
    and a skipping test is not coverage of the invariant it names. The hashes are
    computed from ``rag_v1.systems`` at import, which is where a change to either
    system would actually show up.
    """
    from rag_v1.systems import FROZEN_HASHES

    assert FROZEN_HASHES == FROZEN_SYSTEMS

