"""Batch 006's closure, and the batch-007 contract it preregisters.

Two things this file exists to hold: that the owner's decisions reached the record
intact, and that the paraphrasing contract batch 007 is about to run under cannot be
loosened without a test failing. The second matters more. Batch 007 is the first time
a model may author a question rather than fill a template, and the guardrails are only
real if something checks them.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rag_v1.gold import relations, scoping
from rag_v1.gold.eligibility import evaluate as eligibility
from rag_v1.gold.normalisation import contains_claim_string, has_markdown_link

FINAL = Path("evals/review/gold_review_batch_006_final.json")
GENERATION = Path("evals/review/gold_review_batch_006.json")
CLOSURE = Path("experiments/GOLD-001/GOLD-001-batch-006-closure.json")
PREREG = Path("experiments/GOLD-001/GOLD-001-batch-007-preregistration.json")
STATUS = Path("experiments/GOLD-001/GOLD-001-eligibility-status.json")
REVIEW = Path("experiments/GOLD-001/b006-review-decisions.json")
BATCH_005 = Path("evals/review/gold_review_batch_005_final.json")
CLOSED = {
    1: "evals/review/gold_review_batch_001.json",
    2: "evals/review/gold_review_batch_002.json",
    3: "evals/review/gold_review_batch_003.json",
    4: "evals/review/gold_review_batch_004_final.json",
    5: "evals/review/gold_review_batch_005_final.json",
    6: "evals/review/gold_review_batch_006_final.json",
}
FROZEN_SYSTEMS = {
    "SYSTEM-A-GLOBAL":
        "9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38",
    "SYSTEM-B-DOC-C":
        "304c350940b83733df6043ae3a8abdcbcde33d16950730127aa9f1f39494388b",
}


def load(path: Path) -> dict:
    if not path.exists():
        pytest.skip(f"{path} does not exist")
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def final() -> dict:
    return load(FINAL)


@pytest.fixture(scope="module")
def closure() -> dict:
    return load(CLOSURE)


@pytest.fixture(scope="module")
def prereg() -> dict:
    return load(PREREG)


def by_id(payload: dict) -> dict:
    return {r["candidate_id"]: r for r in payload["records"]}


# ------------------------------------------------------ the owner's decisions landed


def test_the_batch_closed_eight_and_one(closure):
    totals = closure["totals"]
    assert totals["human_verified"] == 8
    assert totals["human_rejected"] == 1
    assert totals["needs_human_review"] == 0
    assert totals["outstanding_decisions"] == 0
    assert totals["holdout_eligible"] == 8


def test_only_the_owner_decided(final):
    assert final["human_reviewer"] == "project_owner"
    for record in final["records"]:
        for entry in record.get("human_decision_history", []):
            assert entry["reviewer"] == "project_owner"
            assert "claude" not in entry["reviewer"].lower()
            assert entry["decision"] in ("APPROVE", "REJECT")


def test_the_rejected_case_is_kept_not_deleted(final, closure):
    rejected = by_id(final)["GOLD-B006-06"]
    assert rejected["verification_status"] == "human_rejected"
    assert rejected["expected_evidence"], "the evidence must survive rejection"
    entry = next(r for r in closure["rejected"]
                 if r["candidate_id"] == "GOLD-B006-06")
    assert "audit example" in entry["preserved_as"]
    assert "DUPLICATE_FACT" in entry["reason"]


def test_the_rejection_is_the_duplicate_of_b005_11(final):
    """§21: the reason for the rejection, checked against the case it duplicates."""
    b006 = by_id(final)["GOLD-B006-06"]
    b005 = by_id(load(BATCH_005))["GOLD-B005-11"]
    assert b005["verification_status"] == "human_verified", (
        "the duplicate only matters because the earlier case was approved")
    # Different libraries, different spans — which is exactly why span-based duplicate
    # control could not see it.
    assert b006["version_id"] != b005["version_id"]
    assert b006["expected_evidence"][0]["evidence_text"] != \
        b005["expected_evidence"][0]["evidence_text"]
    # Same operational relation, which is what makes it redundant.
    for record in (b006, b005):
        assert "AWS_BEDROCK_BASE_URL" in record["critical_strings"]
    assert "override" in b006["question"].lower()


def test_the_duplicate_defect_was_recorded_for_batch_007():
    defects = {d["id"]: d for d in load(REVIEW)["generator_defects_found"]}
    assert "E" in defects
    assert "GOLD-B006-06" in defects["E"]["from_case"]
    assert defects["E"]["preregistered_for"] == "batch 007"


# --------------------------------------------------- relabelling did not touch evidence


def test_taxonomy_relabelling_left_every_anchor_alone(final):
    """§21: a taxonomy change is a change of label, not of evidence."""
    generated = by_id(load(GENERATION))
    for candidate_id, record in by_id(final).items():
        before = generated[candidate_id]["expected_evidence"]
        after = record["expected_evidence"]
        assert len(before) == len(after), candidate_id
        for old, new in zip(before, after, strict=True):
            assert (old["char_start"], old["char_end"]) == \
                (new["char_start"], new["char_end"]), candidate_id
            assert old["evidence_text"] == new["evidence_text"], candidate_id
            assert old["evidence_hash"] == new["evidence_hash"], candidate_id


def test_the_relabelled_cases_actually_changed_label(final):
    generated = by_id(load(GENERATION))
    relabelled = {
        "GOLD-B006-01": "exact_lookup",
        "GOLD-B006-03": "lifecycle_compatibility_migration",
        "GOLD-B006-08": "lifecycle_compatibility_migration",
    }
    for candidate_id, expected in relabelled.items():
        assert generated[candidate_id]["reasoning_type"] != expected, candidate_id
        assert by_id(final)[candidate_id]["reasoning_type"] == expected, candidate_id


def test_no_relabelled_case_became_multi_hop(final):
    """The owner said twice: compound facts in one span are not multi-hop."""
    for record in final["records"]:
        if record["reasoning_type"] == "genuine_multi_hop":
            assert len(record["expected_evidence"]) >= 2, record["candidate_id"]
    assert not any(r["reasoning_type"] == "genuine_multi_hop"
                   for r in final["records"])


def test_every_revision_names_who_asked_for_it(final):
    for record in final["records"]:
        for revision in record.get("revisions", []):
            assert revision["author"], record["candidate_id"]
            assert revision["from"] != revision["to"], record["candidate_id"]


def test_owner_directed_revisions_are_attributed_to_the_owner(final):
    """Claude's own review and the owner's instructions are different acts."""
    owner_directed = {"GOLD-B006-01", "GOLD-B006-02", "GOLD-B006-03",
                      "GOLD-B006-04", "GOLD-B006-05", "GOLD-B006-08"}
    for candidate_id in owner_directed:
        authors = {rev["author"]
                   for rev in by_id(final)[candidate_id].get("revisions", [])}
        assert authors, candidate_id
        assert all("project_owner" in a for a in authors), (
            f"{candidate_id}: revisions attributed to {authors}")


# ------------------------------------------------------------ question scope (§21)


def test_a_rescoped_question_anchors_the_qualifier_it_asserts(final):
    """§21: model qualifiers in a question must be checkable against the evidence."""
    scoped = {
        "GOLD-B006-04": ["Claude Sonnet 5"],
        "GOLD-B006-05": ["claude-mythos-5", "claude-fable-5"],
        "GOLD-B006-02": ["Claude Opus 4.7"],
        "GOLD-B006-03": ["Claude Haiku 4.5"],
    }
    for candidate_id, qualifiers in scoped.items():
        record = by_id(final)[candidate_id]
        evidence = " \n".join(s["evidence_text"]
                              for s in record["expected_evidence"])
        for qualifier in qualifiers:
            assert qualifier in record["question"], f"{candidate_id}: {qualifier}"
            assert qualifier in record["critical_strings"], (
                f"{candidate_id}: {qualifier} is asserted but not anchored")
            assert contains_claim_string(evidence, qualifier), candidate_id


def test_every_critical_string_is_inside_its_own_span(final):
    for record in final["records"]:
        for span in record["expected_evidence"]:
            for value in span["critical_strings"]:
                assert contains_claim_string(span["evidence_text"], value), (
                    f"{record['candidate_id']}: {value!r}")


def test_the_existing_gates_still_hold_on_the_closed_records(final):
    for record in final["records"]:
        if record["verification_status"] != "human_verified":
            continue
        assert scoping.evaluate(record)["status"] == scoping.SCOPED, \
            record["candidate_id"]
        assert not has_markdown_link(record["question"]), record["candidate_id"]
        assert not has_markdown_link(record["answer"]), record["candidate_id"]
        assert relations.evaluate(record)["status"] != relations.REVERSED, \
            record["candidate_id"]


def test_the_eligibility_gate_is_rerun_not_asserted(final, closure):
    approved = [r for r in final["records"]
                if r["verification_status"] == "human_verified"]
    eligible = [r["candidate_id"] for r in approved
                if eligibility(r)["holdout_eligible"]]
    assert eligible == closure["holdout_eligible_ids"]
    assert len(eligible) == closure["totals"]["holdout_eligible"]


# ------------------------------------------------------------------ project state


def test_the_six_generation_batches_still_stand_at_ninety(closure):
    """Batch 006 carried the six generation batches to 90. Later admissions add to the
    project total; they must never change what those six hold."""
    status = load(STATUS)
    generation = [b for b in status["batches"] if isinstance(b["batch"], int)]

    assert sum(b["human_verified"] for b in generation) == 90
    assert sum(b["holdout_eligible"] for b in generation) == 90
    assert sum(b["human_rejected"] for b in generation) == 9
    assert any(b["batch"] == 6 for b in generation)


def test_the_closure_reports_the_shortfall_and_its_cause(closure):
    shortfall = closure["generation_shortfall"]
    assert shortfall["target"] == 28
    assert shortfall["exported"] == 9
    census = closure["corpus_census"]
    assert census["unspent_distinct_texts"] == 699
    assert "not a shortage of material" in census["note"]


def test_the_closure_reports_the_heading_audit(closure):
    audit = closure["heading_parser_audit"]
    assert audit["headings_parsed"] == 5857
    assert audit["likely_prose"] == 44
    assert round(audit["share"], 4) == 0.0075
    assert audit["nothing_was_rewritten"] is True


def test_the_closure_records_that_no_multi_hop_search_ran(closure):
    assert closure["multi_hop_search"]["ran"] is False
    assert closure["reasoning_and_shape"]["genuine_multi_hop"] == 0


def test_retrieval_was_not_run(final, closure):
    assert closure["retrieval"]["retrieval_was_not_run"] is True
    assert closure["retrieval"]["systems_run_against_these_candidates"] == []
    assert final["retrieval_was_not_run"] is True
    assert final["systems_executed"] == []
    for record in final["records"]:
        for leak in ("retrieval_rank", "bm25_score", "dense_score", "reranker_score"):
            assert leak not in record, record["candidate_id"]


def test_the_frozen_hashes_did_not_move():
    from rag_v1.systems import FROZEN_HASHES

    assert dict(FROZEN_HASHES) == FROZEN_SYSTEMS


def test_every_closed_batch_still_matches_its_closure_hash():
    for number, path in CLOSED.items():
        payload = load(Path(path))
        closed = load(Path(
            f"experiments/GOLD-001/GOLD-001-batch-{number:03d}-closure.json"))
        blob = json.dumps(sorted(payload["records"], key=lambda r: r["candidate_id"]),
                          sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        assert closed["closure_sha256"] == hashlib.sha256(
            blob.encode("utf-8")).hexdigest(), f"batch {number:03d} changed"


def test_the_generation_artifact_was_not_rewritten():
    """Repairs live beside the generation run, never inside it."""
    generation = load(GENERATION)
    assert generation["candidates"] == 9
    for record in generation["records"]:
        assert record["verification_status"] == "candidate_unverified", (
            "the generation artifact must not carry a decision")


# ------------------------------- the batch-007 contract, before it authors anything


def test_batch_007_is_only_preregistered(prereg):
    assert "PREREGISTERED" in prereg["status"]
    assert not Path("evals/review/gold_review_batch_007.json").exists()
    for item in ("No batch-007 candidate was generated.", "No pilot was run."):
        assert item in prereg["not_done_in_this_document"]


def test_the_paraphrase_line_is_stated_explicitly(prereg):
    line = prereg["strategy_change"]["the_line"]
    assert "WORDING" in line and "MEANING" in line
    assert "QUESTION" in line and "FACT" in line


def test_the_authoring_order_cannot_be_reversed(prereg):
    order = prereg["authoring_order"]
    assert order[0].startswith("frozen source evidence")
    assert "paraphrased" in order[-1]
    assert prereg["forbidden_order"] == (
        "invent question → search for supporting evidence")


def test_a_paraphrased_candidate_must_carry_its_literal_fact(prereg):
    """The reviewer has to be able to see the gap between fact and question."""
    required = prereg["required_fields_on_paraphrased_candidates"]
    for field in ("source_fact_literal", "source_subject", "source_relation",
                  "source_object", "paraphrase_used"):
        assert field in required


def test_every_entailment_check_is_present_and_drops_on_failure(prereg):
    checks = {c["id"]: c for c in prereg["entailment_self_check"]}
    assert set(checks) == set("ABCDEFG")
    assert prereg["on_any_failure"] == "DROP"
    for check in checks.values():
        assert check["fails_when"], check["id"]


def test_paraphrasing_cannot_broaden_scope_or_add_conditions(prereg):
    """§21: the two failure modes a naturalised question is most likely to introduce."""
    text = json.dumps(prereg["entailment_self_check"])
    assert "broaden" in text
    assert "new condition" in text
    assert "reverse the relation" in text
    assert "causal claim" in text


def test_the_answer_may_not_explain_beyond_the_source(prereg):
    conservatism = prereg["answer_conservatism"]
    assert conservatism["example_good_answer"] == conservatism["example_source"]
    assert "because" in conservatism["example_bad_answer"]


def test_no_existing_gate_was_dropped(prereg):
    gates = {g["gate"] for g in prereg["retained_gates"]}
    for required in ("bare definition scope", "critical anaphora",
                     "subject / relation direction", "duplicate detection",
                     "critical strings", "evidence hashes",
                     "scope self-containment", "evidence size",
                     "holdout eligibility"):
        assert required in gates, required


def test_the_pilot_gates_the_lane(prereg):
    pilot = prereg["calibration_pilot"]
    assert pilot["required_before_scaling"] is True
    assert pilot["size"] == 10
    assert pilot["independent_review_required"] is True
    criteria = pilot["success_criteria"]
    assert criteria["independently_judged_factually_sound"]["minimum"] == 8
    assert criteria["unsupported_claims"]["maximum"] == 0
    assert criteria["relation_direction_reversals"]["maximum"] == 0
    assert criteria["scope_broadening"]["maximum"] == 0
    assert "Do not scale" in pilot["if_it_fails"]
    assert "NO_BUILDER" in pilot["selection"]


def test_no_ai_may_set_human_verified(prereg):
    assert "Only the project owner" in prereg["who_may_set_human_verified"]
    assert "ChatGPT independent verification" in prereg["workflow_unchanged"]
    assert "project-owner approval" in prereg["workflow_unchanged"]


def test_the_preregistration_reads_state_rather_than_asserting_it(prereg):
    state = prereg["starting_state"]
    status = load(STATUS)
    # A starting state is historical. It must equal what the groups that existed when it
    # was written still sum to — the six generation batches — not the live project total,
    # which moves every time anything is admitted.
    generation = [b for b in status["batches"] if isinstance(b["batch"], int)]
    assert state["holdout_eligible"] == sum(b["holdout_eligible"] for b in generation)
    assert state["human_verified"] == sum(b["human_verified"] for b in generation)
    assert state["still_needed"] == 150 - state["holdout_eligible"]
    assert state["holdout_frozen"] is False
    assert state["retrieval_was_not_run"] is True


def test_the_projection_does_not_promise_the_target(prereg):
    projection = prereg["projection"]
    assert projection["project_target"] == 150
    assert "must not influence any individual approval" in projection["note"]
    # 35-40 candidates cannot close a 60-case gap; the document must not imply it can.
    assert projection["reaches_target_this_batch"] is False


def test_the_defects_batch_007_must_fix_first_are_recorded(prereg):
    defects = {d["id"] for d in prereg["generator_defects_to_fix_first"]}
    assert defects == {"E", "F", "G"}
    for defect in prereg["generator_defects_to_fix_first"]:
        assert defect["proposed_fix"], defect["id"]
        assert defect["seen_in"], defect["id"]
