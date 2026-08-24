"""The four fixes batch 005's closure preregistered for batch 006, plus two form rules.

Every case here is a real batch-005 candidate. That matters more than coverage: a
regression test written from an invented example tests the rule the author had in mind,
and these rules exist because the author's rule missed the real thing. The fixtures are
read from the closed batch-005 record, so if a test and the record ever disagree it is
the test that is wrong.

Batch 005 is a closed historical artifact. Nothing here writes to it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag_v1.gold import relations, scoping
from rag_v1.gold.authoring import split_conditional
from rag_v1.gold.normalisation import has_markdown_link, strip_markdown_links
from rag_v1.gold.questionform import (
    NEGATIVE_AS_POSITIVE,
    OK,
    TRUNCATED_PREDICATE,
)
from rag_v1.gold.questionform import evaluate as question_form

BATCH_005 = Path("evals/review/gold_review_batch_005_final.json")
AUDIT = Path("experiments/GOLD-001/GOLD-001-heading-parser-audit.json")


@pytest.fixture(scope="module")
def batch_005() -> dict:
    if not BATCH_005.exists():
        pytest.skip("batch 005 has not been closed")
    return {r["candidate_id"]: r for r in json.loads(BATCH_005.read_text())["records"]}


def evidence_of(record: dict) -> str:
    return " \n".join(s["evidence_text"] for s in record["expected_evidence"])


# ------------------------------------------- Fix A: bare bullets, in every span


def test_b005_01_is_caught_in_both_of_its_spans(batch_005):
    """The defect: the old rule only looked at records with exactly one span.

    ``GOLD-B005-01`` had two, one bare definition bullet from each of two different
    tools, and neither named the tool. The record passed because ``len(spans) == 1``
    was false.
    """
    record = batch_005["GOLD-B005-01"]
    assert len(record["expected_evidence"]) == 2, "the fixture is not the multi-span one"
    verdict = scoping.evaluate(record)
    assert verdict["status"] == scoping.NEEDS_SCOPE
    assert verdict["unscoped_spans"] == ["E1", "E2"], (
        "every span must be asked the question, not only the first")
    assert all("invalid_tool_input" in f for f in verdict["findings"])


def test_the_old_single_span_shortcut_would_have_missed_it(batch_005):
    """State the defect as a test, so a future refactor cannot quietly restore it."""
    record = batch_005["GOLD-B005-01"]
    single_span_only = len(record["expected_evidence"]) == 1
    assert not single_span_only
    assert scoping.evaluate(record)["status"] == scoping.NEEDS_SCOPE


def test_a_span_that_names_its_owner_is_scoped():
    text = ("`FunctionToolCallArgumentsDoneEvent` is emitted once per call.\n"
            "- `parsed_arguments`: the fully parsed arguments object")
    assert scoping.evaluate_span(text)["status"] == scoping.SCOPED


def test_a_bullet_whose_owner_is_only_in_the_heading_is_not():
    verdict = scoping.evaluate_span("- `parsed_arguments`: the fully parsed arguments")
    assert verdict["status"] == scoping.NEEDS_SCOPE
    assert verdict["definition_fields"] == ["parsed_arguments"]


def test_prose_evidence_is_not_a_definition_bullet(batch_005):
    """The rule must not fire on ordinary sentences, or it eats the whole batch."""
    for candidate_id in ("GOLD-B005-10", "GOLD-B005-18", "GOLD-B005-12"):
        record = batch_005[candidate_id]
        assert scoping.evaluate(record)["status"] == scoping.SCOPED, candidate_id


def test_a_field_cannot_be_its_own_owner():
    """The circularity that makes a bare bullet unscoped, stated directly."""
    assert scoping.owner_candidates("- `SomeEvent`: a thing", {"someevent"}) == []


# ------------------------------------ Fix B: markdown reference links in questions


def test_b005_15_question_loses_its_link_plumbing(batch_005):
    record = batch_005["GOLD-B005-15"]
    mined = next(r["from"] for r in record["revisions"] if r["field"] == "question")
    assert "[`ComputerTool`][agents.tool.ComputerTool]" in mined, (
        "the fixture no longer contains the defect it was chosen for")
    assert has_markdown_link(mined)
    cleaned = strip_markdown_links(mined)
    assert cleaned == "What happens when a `ComputerTool` is present?"
    assert "[" not in cleaned and "]" not in cleaned


def test_the_visible_identifier_survives_every_link_shape():
    for text, expected in (
        ("a [`ComputerTool`][agents.tool.ComputerTool] is present",
         "a `ComputerTool` is present"),
        ("see [the guide](https://example.com/a_(b)) first", "see the guide first"),
        ("use [`Runner.run`][] to start", "use `Runner.run` to start"),
        ("![diagram](img.png) shows it", "diagram shows it"),
    ):
        assert strip_markdown_links(text) == expected


def test_text_without_a_link_is_returned_unchanged():
    plain = "What must an Undici-specific option like `dispatcher` be paired with?"
    assert strip_markdown_links(plain) == plain
    assert not has_markdown_link(plain)


def test_evidence_is_never_rewritten(batch_005):
    """Fix B is for authoring. Evidence is anchored by offset and hashed as written."""
    record = batch_005["GOLD-B005-15"]
    span = record["expected_evidence"][0]
    assert "[`ComputerTool`][agents.tool.ComputerTool]" in span["evidence_text"], (
        "the stored evidence must still be the source's own text")


# ------------------------------------------------- Fix C: the heading parser audit


def test_the_audit_flags_the_heading_that_motivated_it():
    if not AUDIT.exists():
        pytest.skip("the heading audit has not been generated")
    report = json.loads(AUDIT.read_text())
    headings = [e["heading"] for e in report["examples"]]
    assert any("configured through AWS_REGION" in h for h in headings), (
        "GOLD-B005-11's section_path is the case this audit exists for")


def test_the_audit_did_not_change_anything():
    if not AUDIT.exists():
        pytest.skip("the heading audit has not been generated")
    report = json.loads(AUDIT.read_text())
    assert report["actions_taken"] == []
    assert any("No heading was rewritten" in n for n in report["not_done"])


def test_b005_11_keeps_its_recorded_section_path(batch_005):
    """A closed record keeps what it has. The audit is a document, not a migration."""
    record = batch_005["GOLD-B005-11"]
    assert record["expected_evidence"][0]["section_path"] == [
        "configured through AWS_REGION, AWS_DEFAULT_REGION, or your AWS profile."]


def test_an_identifier_heading_is_not_prose():
    """``max_tokens`` is a fine heading. The first draft of the audit disagreed."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_audit", Path("scripts/audit_heading_parser.py").resolve())
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for label in ("max\\_tokens", "end\\_turn", "claude.ai", "stop_sequence"):
        assert not module.likely_prose(module.suspicions(label)), label
    prose = "configured through AWS_REGION, AWS_DEFAULT_REGION, or your AWS profile."
    assert module.likely_prose(module.suspicions(prose))


# ------------------------------------------------- Fix D: subject/relation direction


def test_b005_10_is_a_reversal(batch_005):
    record = batch_005["GOLD-B005-10"]
    evidence = evidence_of(record)
    source = relations.derive_source_triple(evidence, "rejects")
    assert source is not None
    assert "experimental model" in source["source_subject"]
    assert "betas" in source["source_object"]

    as_generated = {"question_subject": "`betas`", "question_relation": "overrides",
                    "question_object": "the experimental model"}
    verdict = relations.direction(source, as_generated)
    assert verdict["status"] == relations.REVERSED
    assert record["question"] == "What does `betas` override?", (
        "the fixture is no longer the question that was actually generated")


def test_asking_the_relation_the_right_way_round_agrees(batch_005):
    evidence = evidence_of(batch_005["GOLD-B005-10"])
    source = relations.derive_source_triple(evidence, "rejects")
    verdict = relations.direction(source, {
        "question_subject": "the experimental model",
        "question_relation": "rejects",
        "question_object": "caller-supplied `betas` overrides"})
    assert verdict["status"] == relations.AGREES


def test_a_subject_the_sentence_is_not_about_is_a_mismatch():
    source = relations.derive_source_triple(
        "`temperature` overrides the sampler default.", "overrides")
    verdict = relations.direction(source, {
        "question_subject": "`top_p`", "question_relation": "overrides",
        "question_object": "something else"})
    assert verdict["status"] == relations.SUBJECT_MISMATCH


def test_a_symmetric_relation_may_be_asked_from_either_side(batch_005):
    evidence = evidence_of(batch_005["GOLD-B005-18"])
    source = relations.derive_source_triple(evidence, "must_be_paired_with")
    assert source is not None
    verdict = relations.direction(source, {
        "question_subject": "`fetch`", "question_relation": "must_be_paired_with",
        "question_object": "`dispatcher`"})
    assert verdict["status"] == relations.AGREES
    assert "symmetric" in verdict["finding"]


def test_an_unstated_relation_is_not_checkable_rather_than_passing():
    source = relations.derive_source_triple("`retries` defaults to 2.", "overrides")
    assert source is None
    verdict = relations.direction({"source_subject": None, "source_relation": None},
                                  {"question_subject": "`retries`"})
    assert verdict["status"] == relations.NOT_CHECKABLE


# ------------------------------------------- question form must match evidence form


def test_b005_08_asks_for_coverage_of_a_negative(batch_005):
    record = batch_005["GOLD-B005-08"]
    mined = next(r["from"] for r in record["revisions"] if r["field"] == "question")
    assert mined == "Where is `budget_tokens` supported?"
    verdict = question_form(mined, evidence_of(record))
    assert verdict["status"] == NEGATIVE_AS_POSITIVE
    # And the question the review replaced it with passes.
    assert question_form(record["question"], evidence_of(record))["status"] == OK


def test_b005_18_truncates_its_predicate(batch_005):
    record = batch_005["GOLD-B005-18"]
    mined = next(r["from"] for r in record["revisions"] if r["field"] == "question")
    assert mined == "What must `dispatcher` be?"
    verdict = question_form(mined, evidence_of(record))
    assert verdict["status"] == TRUNCATED_PREDICATE
    assert "paired with" in verdict["suggested_form"]
    assert question_form(record["question"], evidence_of(record))["status"] == OK


def test_a_positive_support_statement_may_be_asked_positively():
    assert question_form(
        "Where is `budget_tokens` supported?",
        "`budget_tokens` is supported on Claude Opus 4 and Claude Sonnet 4.",
    )["status"] == OK


# --------------------------------------------------- literal split protection (§17)


def test_a_conditional_is_not_split_through_an_enumeration(batch_005):
    """The comma inside a list of enum literals is a separator, not a clause boundary."""
    record = batch_005["GOLD-B005-15"]
    text = " ".join(record["expected_evidence"][0]["evidence_text"].split())
    marker, clause, result = split_conditional(text)
    assert marker == "When"
    assert clause == "a [`ComputerTool`][agents.tool.ComputerTool] is present"
    assert result.startswith('`tool_choice="computer"`'), (
        "the outcome must keep the whole enumeration, not open on its tail")


def test_an_ordinary_two_literal_conditional_still_splits():
    assert split_conditional(
        "If `tool_choice` is set to `auto`, `parallel_tool_calls` is ignored by the "
        "router.") == ("If", "`tool_choice` is set to `auto`",
                       "`parallel_tool_calls` is ignored by the router.")


def test_a_split_never_leaves_an_unbalanced_delimiter():
    for text in (
        'When `thinking: {type: "enabled"}` is set, the request is rejected outright.',
        "If the value is `{a: 1, b: 2}`, the parser raises a `ValueError` immediately.",
    ):
        split = split_conditional(text)
        if split is None:
            continue
        _, clause, result = split
        for fragment in (clause, result):
            assert fragment.count("`") % 2 == 0
            assert fragment.count("{") == fragment.count("}")
            assert fragment.count('"') % 2 == 0
