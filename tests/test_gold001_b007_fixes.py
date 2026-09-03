"""The three generator defects batch 006's closure preregistered for batch 007: E, F, G.

Every case here is a real batch-005 or batch-006 candidate, read from the closed record.
That is the same discipline as `test_gold001_b006_fixes.py` and for the same reason: each
of these rules exists because a rule written from an imagined example missed the real
thing. GOLD-B006-01's credential requirement really did read as two settings interacting,
and no invented sentence would have shown that.

Batches 005 and 006 are closed historical artifacts. Nothing here writes to either, and
nothing here sets `human_verified` — these tests read the owner's decisions as ground
truth for what the classifier should have said.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag_v1.gold import questionscope, reasoningtype
from rag_v1.gold.factidentity import (
    derive_triple,
    duplicate_facts,
    normalise_relation,
    normalise_term,
    triple,
)

BATCH_005 = Path("evals/review/gold_review_batch_005_final.json")
BATCH_006 = Path("evals/review/gold_review_batch_006_final.json")
BATCH_006_GENERATED = Path("evals/review/gold_review_batch_006.json")


def _records(path: Path) -> dict:
    if not path.exists():
        pytest.skip(f"{path} is not present")
    return {r["candidate_id"]: r for r in json.loads(path.read_text())["records"]}


@pytest.fixture(scope="module")
def batch_005() -> dict:
    return _records(BATCH_005)


@pytest.fixture(scope="module")
def batch_006() -> dict:
    return _records(BATCH_006)


@pytest.fixture(scope="module")
def generated_006() -> dict:
    return _records(BATCH_006_GENERATED)


# --------------------------------------------------------------- defect E: fact identity

def test_the_cross_library_duplicate_the_owner_caught_is_now_visible(
        batch_005, batch_006):
    """GOLD-B005-11 and GOLD-B006-06: one fact, two SDKs, no shared text or offsets."""
    python_sdk, typescript_sdk = batch_005["GOLD-B005-11"], batch_006["GOLD-B006-06"]

    flags = duplicate_facts([typescript_sdk], [python_sdk])

    assert len(flags) == 1
    assert flags[0]["candidate_id"] == "GOLD-B006-06"
    assert flags[0]["status"] == "duplicate_fact"
    assert flags[0]["also_stated_by"] == ["GOLD-B005-11"]
    assert flags[0]["triple"] == ["aws_bedrock_base_url", "override", "endpoint"]


def test_the_duplicate_pair_shares_no_text_offsets_or_question(batch_005, batch_006):
    """The premise of defect E: the old comparison had nothing to compare."""
    python_sdk, typescript_sdk = batch_005["GOLD-B005-11"], batch_006["GOLD-B006-06"]
    a, b = python_sdk["expected_evidence"][0], typescript_sdk["expected_evidence"][0]

    assert python_sdk["question"] != typescript_sdk["question"]
    assert a["evidence_text"] != b["evidence_text"]
    assert (a["version_id"], a["char_start"]) != (b["version_id"], b["char_start"])


def test_a_triple_is_derived_when_a_record_predates_the_field(batch_005):
    """Batch 005 recorded no triple, so the check reads one out of the frozen evidence."""
    python_sdk = batch_005["GOLD-B005-11"]

    assert "source_subject" not in python_sdk
    assert triple(python_sdk) == ("aws_bedrock_base_url", "override", "endpoint")


def test_a_recorded_triple_is_preferred_over_a_derived_one(batch_006):
    typescript_sdk = batch_006["GOLD-B006-06"]

    assert typescript_sdk["source_relation"] == "overrides"
    assert triple(typescript_sdk) == ("aws_bedrock_base_url", "override", "endpoint")


def test_distinct_facts_are_not_flagged_as_duplicates(batch_006):
    """Nine candidates from one batch: only the pair the owner found may collide."""
    records = [batch_006[cid] for cid in sorted(batch_006)]

    flagged = [f for f in duplicate_facts(records, []) if f["status"] == "duplicate_fact"]

    assert flagged == []


def test_an_uncomparable_record_is_reported_not_silently_passed():
    """A span stating no operational relation is 'not_comparable', never 'clean'."""
    flags = duplicate_facts([{"candidate_id": "X", "expected_evidence": [
        {"evidence_text": "A paragraph of prose with no operational relation at all."}]}],
        [])

    assert flags[0]["status"] == "not_comparable"


def test_the_same_fact_written_two_ways_normalises_the_same():
    long_form = derive_triple(
        "Set `AWS_BEDROCK_BASE_URL` to override the derived "
        "`https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint.")
    short_form = derive_triple("`AWS_BEDROCK_BASE_URL` can override the endpoint.")

    assert long_form == short_form == ("aws_bedrock_base_url", "override", "endpoint")


def test_normalisation_keeps_what_identifies_and_drops_what_does_not():
    assert normalise_term("`AWS_BEDROCK_BASE_URL`") == "aws_bedrock_base_url"
    assert normalise_term("the endpoint.") == normalise_term("the derived endpoint")
    assert normalise_relation("overrides") == normalise_relation("override") == "override"
    assert normalise_relation("a sentence with no relation verb") == ""


# ------------------------------------------------------------- defect F: reasoning type

@pytest.mark.parametrize("candidate_id", [
    "GOLD-B006-01", "GOLD-B006-02", "GOLD-B006-03", "GOLD-B006-04", "GOLD-B006-05",
    "GOLD-B006-06", "GOLD-B006-07", "GOLD-B006-08", "GOLD-B006-09",
])
def test_whole_sentence_classification_agrees_with_the_owner(batch_006, candidate_id):
    """The owner's label is the ground truth the frame-derived label failed to match."""
    record = batch_006[candidate_id]

    assert reasoningtype.evaluate(record)["derived"] == record["reasoning_type"]


@pytest.mark.parametrize("candidate_id,was,now", [
    ("GOLD-B006-01", "configuration_interaction", "exact_lookup"),
    ("GOLD-B006-03", "exact_lookup", "lifecycle_compatibility_migration"),
    ("GOLD-B006-08", "configuration_interaction", "lifecycle_compatibility_migration"),
])
def test_each_relabelled_case_is_now_classified_correctly(
        batch_006, generated_006, candidate_id, was, now):
    """The three the owner had to relabel — the defect, case by case."""
    assert generated_006[candidate_id]["reasoning_type"] == was
    assert batch_006[candidate_id]["reasoning_type"] == now

    assert reasoningtype.classify(
        batch_006[candidate_id]["expected_evidence"][0]["evidence_text"]) == now


def test_a_compatibility_statement_is_lifecycle_whatever_its_verb():
    """GOLD-B006-03 matched `accepts` and was read as a lookup."""
    assert reasoningtype.classify(
        "Claude Haiku 4.5 accepts the `code_execution_20260120` tool type, but "
        "programmatic tool calling isn't available on it.") == reasoningtype.LIFECYCLE


def test_one_requirement_naming_two_identifiers_is_not_an_interaction():
    """GOLD-B006-01: `admin` and `developer` are two roles in one rule, not two settings."""
    assert reasoningtype.classify(
        "Creating an `admin`-role service account requires an interactive credential — "
        "a workload may only create `developer`-role service accounts."
    ) == reasoningtype.EXACT_LOOKUP


def test_two_settings_bearing_on_each_other_is_an_interaction():
    assert reasoningtype.classify(
        "The region can also come from `AWS_REGION` or `AWS_DEFAULT_REGION`, and "
        "`AWS_BEDROCK_BASE_URL` can override the endpoint."
    ) == reasoningtype.CONFIGURATION_INTERACTION


def test_a_model_name_carrying_a_number_is_not_a_version_statement():
    """"Claude Sonnet 5" is scope, not lifecycle — or every span becomes lifecycle."""
    assert reasoningtype.classify(
        "Claude Sonnet 5 defaults to `high` effort on the Claude API and Claude Code."
    ) == reasoningtype.EXACT_LOOKUP


def test_a_trailing_instruction_does_not_outrank_the_sentences_assertion():
    """GOLD-B006-05 states a default and then says how to change it."""
    assert reasoningtype.classify(
        '`thinking.display` defaults to `"omitted"` on `claude-mythos-5` and '
        '`claude-fable-5`; set `display: "summarized"` to receive readable summaries.'
    ) == reasoningtype.EXACT_LOOKUP


# --------------------------------------------------------------- defect G: question scope

@pytest.mark.parametrize("candidate_id", ["GOLD-B006-02", "GOLD-B006-04", "GOLD-B006-05"])
def test_the_three_rescoped_questions_would_not_have_exported(
        generated_006, candidate_id):
    """As generated, each inherited its frame's breadth. The gate drops all three."""
    assert questionscope.exports(generated_006[candidate_id]) is False


def test_a_dropped_scope_qualifier_is_named(generated_006):
    """GOLD-B006-05's question dropped both model ids the default is scoped to."""
    result = questionscope.evaluate(generated_006["GOLD-B006-05"])

    assert result["status"] == questionscope.SCOPE_MISSING_FROM_QUESTION
    assert result["missing_from_question"] == ["claude-mythos-5", "claude-fable-5"]


def test_a_qualifier_no_check_reads_is_not_enough(generated_006):
    """GOLD-B006-02 named the model in its question but not in its critical strings."""
    result = questionscope.evaluate(generated_006["GOLD-B006-02"])

    assert result["missing_from_question"] == []
    assert result["status"] == questionscope.SCOPE_MISSING_FROM_CRITICAL_STRINGS


@pytest.mark.parametrize("candidate_id", ["GOLD-B006-02", "GOLD-B006-04", "GOLD-B006-05"])
def test_the_owners_rescoped_versions_pass_the_gate(batch_006, candidate_id):
    """The owner's repair is what the gate is asking for, so it must accept it."""
    assert questionscope.evaluate(batch_006[candidate_id])["status"] == questionscope.SCOPED


def test_a_comparison_is_not_a_scope():
    """"the same as on Claude Mythos Preview" compares; it does not narrow."""
    found = questionscope.qualifiers(
        '`thinking.display` defaults to `"omitted"` on `claude-mythos-5` and '
        '`claude-fable-5`, the same as on Claude Mythos Preview.')

    assert found == ["claude-mythos-5", "claude-fable-5"]


def test_an_unscoped_source_is_not_forced_to_invent_scope(batch_006):
    """GOLD-B006-07 names no model or surface, so there is nothing to carry."""
    assert questionscope.evaluate(
        batch_006["GOLD-B006-07"])["status"] == questionscope.UNSCOPED_SOURCE


def test_the_gate_is_stricter_than_batch_006_was_held_to(batch_006):
    """GOLD-B006-08 carries its scope in the question but not in the critical strings.

    The owner approved it under the old rule; the preregistered rule requires both. This
    is recorded as a test rather than tuned away, because the divergence is a finding for
    the reviewer: applied to batch 007, this gate will drop candidates batch 006 accepted.
    """
    result = questionscope.evaluate(batch_006["GOLD-B006-08"])

    assert result["missing_from_question"] == []
    assert result["status"] == questionscope.SCOPE_MISSING_FROM_CRITICAL_STRINGS
    assert result["missing_from_critical_strings"] == ["OpenAI Python SDK"]
