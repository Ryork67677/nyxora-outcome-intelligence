"""GOLD-001 batch 005: the checks that exist because batch 004 cost something.

Two of these are regressions in the strict sense. The ``max_tokens`` pair is the near
miss batch 004's diagnostic recorded — a request parameter in one span and a
``stop_reason`` value in the other — and it must never again read as a valid bridge. The
definition-bullet shape is the one batch 004's review rejected for taking its scope from
a heading, and batch 005 must not ship it again.

The rest guard the separations this project keeps re-learning: structural precheck is not
semantic approval, a generation self-review is not verification, and a category label is
earned by what the evidence says rather than by what would balance the batch.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rag_v1.gold.authoring import build_conditional, split_conditional
from rag_v1.gold.bridge_equivalence import (
    ENUM_VALUE,
    FIELD_NAME,
    REQUEST_PARAMETER,
    entity_role,
    namespace,
    same_semantic_entity,
)
from rag_v1.gold.mining_v5 import subject_identifier
from rag_v1.gold.multihop import (
    DEPENDENCY_PAIR_BUDGET,
    is_dependency_statement,
    state_implication,
)
from rag_v1.gold.normalisation import contains_claim_string

BATCH = Path("evals/review/gold_review_batch_005.json")
REPORT = Path("experiments/GOLD-001/GOLD-001-batch-005-generation-report.json")
CLOSED = {
    1: Path("evals/review/gold_review_batch_001.json"),
    2: Path("evals/review/gold_review_batch_002.json"),
    3: Path("evals/review/gold_review_batch_003.json"),
    4: Path("evals/review/gold_review_batch_004_final.json"),
}
CLOSURES = {
    1: Path("experiments/GOLD-001/GOLD-001-batch-001-closure.json"),
    2: Path("experiments/GOLD-001/GOLD-001-batch-002-closure.json"),
    3: Path("experiments/GOLD-001/GOLD-001-batch-003-closure.json"),
    4: Path("experiments/GOLD-001/GOLD-001-batch-004-closure.json"),
}
FROZEN_SYSTEMS = {
    "SYSTEM-A-GLOBAL":
        "9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38",
    "SYSTEM-B-DOC-C":
        "304c350940b83733df6043ae3a8abdcbcde33d16950730127aa9f1f39494388b",
}

#: The batch-004 near miss, verbatim from BATCH-004-near-miss-multihop-review.json.
MAX_TOKENS_SPAN_1 = {
    "evidence_text": ("* `budget_tokens` can exceed `max_tokens` here; the [budget "
                      "rules](https://example.invalid) explain this exception."),
    "section_path": ["Interleaved thinking in manual mode"],
    "document_title": "Extended thinking", "version_id": "ver_thinking"}
MAX_TOKENS_SPAN_2 = {
    "evidence_text": ('The loop exits on any other stop reason (`"end_turn"`, '
                      '`"max_tokens"`, `"stop_sequence"`, or `"refusal"`), which means '
                      "Claude has produced a final answer."),
    "section_path": ["The agentic loop (client tools)"],
    "document_title": "How tool use works", "version_id": "ver_tool_use"}
NEEDS_APPROVAL_SPAN_1 = {
    "evidence_text": ("Set `needs_approval` to `True` to always require approval or "
                      "provide an async function that decides per call."),
    "section_path": ["Human-in-the-loop", "Marking tools that need approval"],
    "document_title": "Human-in-the-loop", "version_id": "ver_hitl"}
NEEDS_APPROVAL_SPAN_2 = {
    "evidence_text": ("SDK tool approval interruptions are not supported: any function "
                      "tool whose `needs_approval` setting is not `False` is rejected "
                      "before the request is sent."),
    "section_path": ["Models", "Hosted multi-agent (experimental)",
                     "Local function tools"],
    "document_title": "Models", "version_id": "ver_models"}


def load(path: Path) -> dict:
    if not path.exists():
        pytest.skip(f"{path} has not been generated")
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def batch() -> dict:
    return load(BATCH)


# ---------------------------------------------------- semantic bridge equivalence


def test_max_tokens_equivocation_is_refused():
    """The batch-004 regression: same string, different concept, no chain."""
    verdict = same_semantic_entity("max_tokens", MAX_TOKENS_SPAN_1, MAX_TOKENS_SPAN_2)
    assert verdict["same_semantic_entity"] is False
    assert verdict["semantic_compatibility_check"] == "FAIL"
    assert verdict["bridge_entity_meaning_span_1"] == REQUEST_PARAMETER
    assert verdict["bridge_entity_meaning_span_2"] == ENUM_VALUE
    assert "two different things" in verdict["bridge_equivalence_reason"]


def test_a_genuine_bridge_still_passes():
    """The check must not be so strict that the one real chain fails it."""
    verdict = same_semantic_entity("needs_approval", NEEDS_APPROVAL_SPAN_1,
                                   NEEDS_APPROVAL_SPAN_2)
    assert verdict["same_semantic_entity"] is True
    assert verdict["semantic_compatibility_check"] == "PASS"
    assert verdict["bridge_entity_meaning_span_1"] == REQUEST_PARAMETER
    assert verdict["bridge_entity_meaning_span_2"] == REQUEST_PARAMETER


def test_request_parameter_and_enum_value_are_distinguished():
    assert entity_role("Set `max_tokens` to 1024 to cap the response.",
                       "max_tokens") == REQUEST_PARAMETER
    assert entity_role('The stop reason is one of `"max_tokens"` or `"end_turn"`.',
                       "max_tokens") == ENUM_VALUE
    assert entity_role("- `view_range`: An array of two integers.",
                       "view_range") == FIELD_NAME


def test_two_definitions_in_unrelated_areas_are_two_parameters():
    """§17: a tool parameter from two unrelated tools is not one entity."""
    first = {"evidence_text": "- `view_range`: An array of two integers to view.",
             "section_path": ["Text editor tool commands", "view"],
             "document_title": "Text editor tool", "version_id": "a"}
    second = {"evidence_text": "- `view_range`: The lines of the memory file to read.",
              "section_path": ["Memory tool commands", "view"],
              "document_title": "Memory tool", "version_id": "b"}
    verdict = same_semantic_entity("view_range", first, second)
    assert verdict["same_semantic_entity"] is False


def test_namespace_reads_the_documentation_area():
    space = namespace({"section_path": ["Human-in-the-loop", "Marking tools"],
                       "document_title": "Human-in-the-loop"})
    assert "human" in space and "loop" in space
    # Stopwords must not make every span look related to every other.
    assert "the" not in space and "api" not in space


# ------------------------------------------------- dependency-first composition


def test_a_dependency_statement_is_recognised():
    assert is_dependency_statement("Set `needs_approval` to `True` to require approval.")
    assert is_dependency_statement("`a` requires `b`.")
    assert not is_dependency_statement("The response contains a list of blocks.")


def test_state_implication_needs_the_entity_put_into_a_state():
    established = state_implication("needs_approval", NEEDS_APPROVAL_SPAN_1["evidence_text"])
    assert established["state_established"] is True
    assert "needs_approval" in established["state_evidence"]

    mentioned = state_implication(
        "needs_approval", "The interruptions list contains one entry per `needs_approval` tool.")
    assert mentioned["state_established"] is False
    assert mentioned["reason"]


def test_the_multi_hop_search_reports_its_budget_and_funnel(batch):
    search = batch["multi_hop_search"]
    assert search["budget"] == DEPENDENCY_PAIR_BUDGET
    funnel = search["funnel"]
    assert "dependency_pairs_considered" in funnel
    outcomes = sum(v for k, v in funnel.items() if k != "dependency_pairs_considered")
    assert outcomes <= funnel["dependency_pairs_considered"]
    assert search["exported_chains"] == batch["genuine_multi_hop"]


def test_multi_hop_candidates_carry_both_checks(batch):
    for record in batch["records"]:
        if record["reasoning_type"] != "genuine_multi_hop":
            continue
        assert record["multi_hop_composition_check"] == "PASS"
        assert record["semantic_compatibility_check"] == "PASS"
        assert record["same_semantic_entity"] is True
        assert record["requires_all_evidence"] is True
        assert len(record["expected_evidence"]) >= 2
        for field in ("bridge_entity", "bridge_relationship", "hop_1_claim",
                      "hop_2_claim", "composed_claim", "bridge_entity_text",
                      "bridge_entity_meaning_span_1", "bridge_entity_meaning_span_2",
                      "bridge_equivalence_reason"):
            assert record[field], field


# ------------------------------------------------------------- authoring quality


def test_the_question_subject_is_the_fact_subject():
    """"What is the limit on `request_too_large`?" — the limit is not on the error."""
    from rag_v1.gold.mining_v5 import CONSTRAINT_PATTERNS
    span = "* 413 - `request_too_large`: Request exceeds the maximum allowed bytes."
    assert subject_identifier(span, CONSTRAINT_PATTERNS,
                              ["request_too_large"]) is None
    span = "Request-level `allowed_domains` must be a subset of the organization list."
    assert subject_identifier(span, CONSTRAINT_PATTERNS,
                              ["allowed_domains"]) == "allowed_domains"


def test_a_conditional_split_never_cuts_through_a_literal():
    """A split inside a brace produced a question ending mid-JSON object."""
    text = ('When thinking is enabled without explicit `clear_thinking` configuration, '
            'the API defaults to `keep: {type: "thinking_turns", value: 1}`, which '
            'triggers this behavior.')
    split = split_conditional(text)
    if split is not None:
        _, clause, result = split
        for fragment in (clause, result):
            assert fragment.count("{") == fragment.count("}")
            assert fragment.count("`") % 2 == 0


def test_an_outcome_must_contain_a_verb():
    """"…returns X, not an error." must not yield "not an error" as the answer."""
    text = ("When a classifier declines a request, the Messages API returns "
            '`stop_reason: "refusal"` as a successful HTTP 200 response, not an error.')
    split = split_conditional(text)
    if split is not None:
        assert not split[2].lower().startswith("not ")


def test_a_wish_is_not_a_condition():
    fact = {"evidence_text": "If you want to change this, you can set an `input_filter`."}
    assert build_conditional(fact) is None


def test_generic_identifier_questions_do_not_reach_the_batch(batch):
    """§12 and batch 004's review: an identifier in a dozen APIs needs its scope."""
    import re
    generic = {"type", "name", "url", "path", "value", "data", "timezone", "headers"}
    for record in batch["records"]:
        subject = next(iter(re.findall(r"`([^`]+)`", record["question"])), None)
        if subject:
            assert subject.lower() not in generic, record["candidate_id"]


def test_no_bare_definition_bullet_survives(batch):
    """The shape batch 004's review rejected for taking its scope from a heading."""
    import re
    bare = re.compile(r"^[-*]\s+`[^`]+`\s*:")
    for record in batch["records"]:
        spans = record["expected_evidence"]
        if len(spans) != 1:
            continue
        text = spans[0]["evidence_text"].strip()
        if not bare.match(text):
            continue
        others = [s for s in record["critical_strings"] if f"`{s}`" in text]
        assert len(others) >= 2, (
            f"{record['candidate_id']} is a bare definition bullet with no scope")


def test_configuration_interaction_names_two_settings(batch):
    """§11: a single conditional fact is not an interaction between settings."""
    for record in batch["records"]:
        if record["reasoning_type"] != "configuration_interaction":
            continue
        evidence = " \n".join(s["evidence_text"] for s in record["expected_evidence"])
        named = [s for s in record["critical_strings"] if f"`{s}`" in evidence]
        assert len(named) >= 2, record["candidate_id"]


def test_ambiguity_cases_declare_two_readings(batch):
    for record in batch["records"]:
        if record["reasoning_type"] != "ambiguity_disambiguation":
            continue
        assert record["ambiguous_term"]
        readings = record["candidate_interpretations"]
        assert len(readings) >= 2
        assert len({r["meaning"] for r in readings}) >= 2
        assert record["required_scope_to_answer"]


# ------------------------------------------------------------ separations kept apart


def test_structural_precheck_is_not_semantic_approval(batch):
    """§24: the two states are different, and the batch must say so."""
    for record in batch["records"]:
        assert record["precheck_holdout_ready"] is True
        assert record["precheck_failures"] == []
        assert record["verification_status"] == "candidate_unverified"
        assert record["internal_semantic_review_status"] in (
            "READY_FOR_INDEPENDENT_REVIEW", "NEEDS_INTERNAL_REPAIR")
    review = batch["internal_review"]
    assert "not independent verification" in review["note"]
    # The precheck passed candidates the semantic review then dropped; if it never
    # did, one of the two is not doing its job.
    assert review["counts"].get("DROP", 0) > 0


def test_the_self_review_is_not_recorded_as_verification(batch):
    for record in batch["records"]:
        assert record["chatgpt_verified"] is None
        assert record["claude_proposed"] is True
        assert "human" not in (record["internal_semantic_review_status"] or "").lower()


def test_generation_repairs_keep_the_original_value(batch):
    for record in batch["records"]:
        for repair in record["generation_repairs"]:
            assert repair["from"] != repair["to"]
            assert repair["reason"]
        for revision in record["revisions"]:
            assert revision["author"]
            assert revision["reason"]


# --------------------------------------------------------------- evidence contract


def test_every_span_hashes_to_its_own_text(batch):
    for record in batch["records"]:
        for span in record["expected_evidence"]:
            digest = hashlib.sha256(span["evidence_text"].encode("utf-8")).hexdigest()
            assert digest == span["evidence_hash"], record["candidate_id"]
            assert span["evidence_char_length"] == span["char_end"] - span["char_start"]
            assert span["evidence_char_length"] <= 1500


def test_critical_strings_belong_to_their_own_span(batch):
    """§23: a string is checked in its span, not in the union of them."""
    for record in batch["records"]:
        for span in record["expected_evidence"]:
            assert span["critical_strings"], record["candidate_id"]
            for string in span["critical_strings"]:
                assert contains_claim_string(span["evidence_text"], string), (
                    f"{record['candidate_id']} {span['evidence_id']}: {string!r}")


def test_claims_map_to_spans(batch):
    for record in batch["records"]:
        ids = {s["evidence_id"] for s in record["expected_evidence"]}
        assert len(record["claim_evidence_map"]) == len(record["atomic_claims"])
        for mapping in record["claim_evidence_map"]:
            assert mapping["evidence_id"] in ids


def test_no_candidate_reuses_closed_evidence(batch):
    """§26: a fact already spent is not new coverage."""
    spent = set()
    for path in CLOSED.values():
        if not path.exists():
            continue
        for record in json.loads(path.read_text())["records"]:
            for span in (record.get("expected_evidence") or [record]):
                if span.get("version_id"):
                    spent.add((span["version_id"], span["char_start"],
                               span["char_end"]))
    for record in batch["records"]:
        for span in record["expected_evidence"]:
            key = (span["version_id"], span["char_start"], span["char_end"])
            assert key not in spent, f"{record['candidate_id']} reuses spent evidence"


# ------------------------------------------------------------------- invariants


def test_closed_batches_are_untouched():
    """§4: batches 001–004 are historical artifacts."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_close_batch", Path("scripts/close_batch.py").resolve())
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for number, path in CLOSED.items():
        closure_path = CLOSURES[number]
        if not (path.exists() and closure_path.exists()):
            continue
        records = json.loads(path.read_text())["records"]
        closure = json.loads(closure_path.read_text())
        assert module.candidate_digest(records) == closure["closure_sha256"], (
            f"batch {number:03d} changed after closure")


def test_retrieval_was_not_run(batch):
    assert batch["retrieval_was_not_run"] is True
    assert batch["systems_executed"] == []
    for record in batch["records"]:
        assert record["retrieval_was_not_run"] is True
    blob = json.dumps(batch["records"]).lower()
    for label in ("routing_heavy", "passage_heavy", "hard_for_bm25", "recall@", "ndcg"):
        assert label not in blob


def test_starting_state_was_read_from_the_records(batch):
    """What the project held *before* this batch, checked against batches 001-004.

    This used to compare the recorded starting state against the live status document,
    which was the same number only until batch 005 itself closed. A starting state is
    historical: it must equal what the batches that existed at the time still sum to,
    and it must keep naming the document it was read from.
    """
    state = batch["starting_state"]
    status = load(Path(state["read_from"]))
    earlier = [b for b in status["batches"] if b["batch"] < batch["batch"]]
    assert earlier, "the status document lists no batch before this one"
    assert state["human_verified"] == sum(b["human_verified"] for b in earlier)
    assert state["holdout_eligible"] == sum(b["holdout_eligible"] for b in earlier)
    assert state["holdout_frozen"] is False
    assert status["holdout_frozen"] is False

    per_batch = {b["batch"]: b for b in state["by_batch"]}
    for row in earlier:
        recorded = per_batch[row["batch"]]
        assert recorded["human_verified"] == row["human_verified"]
        assert recorded["holdout_eligible"] == row["holdout_eligible"]


def test_report_agrees_with_the_batch(batch):
    report = load(REPORT)
    assert report["candidates"] == len(batch["records"])
    assert report["by_reasoning_type"] == batch["by_reasoning_type"]
    assert report["by_provider"] == batch["by_provider"]
    assert report["genuine_multi_hop"] == batch["genuine_multi_hop"]


def test_frozen_systems_are_unchanged():
    """The frozen configs still hash to what was frozen.

    This looked for an ``evals/frozen`` directory that does not exist, so it skipped —
    and a skipping test is not coverage of the invariant it names. The hashes are
    computed from ``rag_v1.systems`` at import, which is where a change to either
    system would actually show up.
    """
    from rag_v1.systems import FROZEN_HASHES

    assert FROZEN_HASHES == FROZEN_SYSTEMS

