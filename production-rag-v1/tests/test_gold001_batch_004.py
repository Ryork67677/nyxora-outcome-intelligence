"""GOLD-001 batch 004: the multi-hop label has to be earned, not asserted.

Batch 003 shipped four candidates labelled ``multi_hop`` and kept none of them: each
drew on two spans, which made the label look earned, while the answer was the two spans'
contents rather than anything that followed from combining them. These tests exist so
that failure cannot recur silently — the composition check must reject the shapes that
fooled batch 003, and the batch on disk must satisfy every claim its report makes about
it.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rag_v1.gold.ambiguity import find_ambiguous_fields, scope_is_symbolic
from rag_v1.gold.factmining import mine_bridge_facts
from rag_v1.gold.multihop import (
    FAIL,
    PASS,
    about,
    composition_check,
    find_bridges,
    is_list_membership,
    plausible_bridge,
    self_contained,
    states_dependency,
)

BATCH = Path("evals/review/gold_review_batch_004.json")
REPORT = Path("experiments/GOLD-001/GOLD-001-batch-004-generation-report.json")
COVERAGE = Path("experiments/GOLD-001/GOLD-001-coverage-status-after-b004-generation.json")
FROZEN_SYSTEMS = {
    "SYSTEM-A-GLOBAL":
        "9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38",
    "SYSTEM-B-DOC-C":
        "304c350940b83733df6043ae3a8abdcbcde33d16950730127aa9f1f39494388b",
}

SPAN_REQUIREMENT = (
    "Set `needs_approval` to `True` to always require approval or provide an async "
    "function that decides per call.")
SPAN_CONSEQUENCE = (
    "SDK tool approval interruptions are not supported: any function tool whose "
    "`needs_approval` setting is not `False` is rejected before the request is sent.")


class FakeSection:
    def __init__(self, path, start, end):
        self.path, self.char_start, self.char_end = path, start, end


def make_doc(text: str, provider: str = "openai") -> dict:
    return {"version_id": "ver_test", "text": text, "provider": provider,
            "title": "Test Doc", "url": "https://example.invalid",
            "captured_at": "2026-01-01",
            "sections": [FakeSection(["Body"], 0, len(text))]}


@pytest.fixture(scope="module")
def batch() -> dict:
    if not BATCH.exists():
        pytest.skip(f"{BATCH} has not been generated")
    return json.loads(BATCH.read_text())


@pytest.fixture(scope="module")
def report() -> dict:
    if not REPORT.exists():
        pytest.skip(f"{REPORT} has not been generated")
    return json.loads(REPORT.read_text())


# --------------------------------------------------------------------------- composition


def test_true_multi_hop_composes():
    verdict = composition_check("needs_approval", SPAN_REQUIREMENT, SPAN_CONSEQUENCE,
                                ["needs_approval", "True"], ["rejected"])
    assert verdict["multi_hop_composition_check"] == PASS
    assert verdict["reasons"] == []


def test_fake_multi_hop_is_rejected_when_span_1_answers_alone():
    """Span 1 already carries hop 2's assertion, so a reader needs only span 1."""
    span_1 = ("Set `needs_approval` to `True`; any tool whose `needs_approval` is not "
              "`False` is rejected before the request is sent.")
    verdict = composition_check("needs_approval", span_1, SPAN_CONSEQUENCE,
                                ["needs_approval"], ["rejected"])
    assert verdict["multi_hop_composition_check"] == FAIL
    assert any("span 1 alone" in reason for reason in verdict["reasons"])


def test_fake_multi_hop_is_rejected_when_span_2_answers_alone():
    span_2 = SPAN_CONSEQUENCE + " Set `needs_approval` to `True` to require approval."
    verdict = composition_check("needs_approval", SPAN_REQUIREMENT, span_2,
                                ["needs_approval", "True"], ["rejected"])
    assert verdict["multi_hop_composition_check"] == FAIL
    assert any("span 2 alone" in reason for reason in verdict["reasons"])


def test_bridge_entity_must_appear_in_both_spans():
    verdict = composition_check("needs_approval", SPAN_REQUIREMENT,
                                "Tool calls are streamed as they arrive.",
                                ["needs_approval"], ["streamed"])
    assert verdict["multi_hop_composition_check"] == FAIL
    assert any("not in both spans" in reason for reason in verdict["reasons"])


def test_each_hop_must_be_carried_by_its_own_span():
    """A composed answer may not assert what neither span says."""
    verdict = composition_check("needs_approval", SPAN_REQUIREMENT, SPAN_CONSEQUENCE,
                                ["needs_approval", "retry_policy"], ["rejected"])
    assert verdict["multi_hop_composition_check"] == FAIL
    assert any("span 1 does not contain" in reason for reason in verdict["reasons"])


def test_multi_span_is_not_multi_hop():
    """Two spans about one entity that never interact: the batch-003 shape exactly."""
    span_1 = "The `timezone` field takes an IANA timezone ID."
    span_2 = "When `timezone` is omitted, results are returned in UTC."
    verdict = composition_check("timezone", span_1, span_2,
                                ["IANA timezone ID"], ["UTC"])
    assert verdict["multi_hop_composition_check"] == PASS, (
        "the mechanical check alone cannot see this; the structural filters must")
    assert not states_dependency(span_1, "timezone")


# ------------------------------------------------------------------- structural filters


@pytest.mark.parametrize("entity", ["needs_approval", "max_tokens", "ContentDeltaEvent",
                                    "agents.tool.ComputerTool"])
def test_plausible_bridge_accepts_symbols(entity):
    assert plausible_bridge(entity)


@pytest.mark.parametrize("entity", ["False", "True", "error", "refusal", "string",
                                    "content", "json"])
def test_plausible_bridge_rejects_vocabulary(entity):
    assert not plausible_bridge(entity)


def test_dependency_must_be_on_the_bridge_entity():
    """The conditional has to test the entity, not merely sit in the same sentence."""
    unrelated = ("If you run at `xhigh` or `max` effort, raise `max_tokens` to at least "
                 "64k as a starting point.")
    assert not states_dependency(unrelated, "max_tokens")
    assert states_dependency(SPAN_CONSEQUENCE, "needs_approval")


def test_list_membership_is_not_a_requirement():
    assert is_list_membership(
        'The supported keys are `"max_turns"`, `"model_refusal"`, and '
        '`"invalid_final_output"`.')
    assert not is_list_membership(SPAN_REQUIREMENT)


def test_two_self_contained_sentences_are_parallel_facts():
    both = ("If Claude attempts more searches than allowed, the "
            "`web_search_tool_result` is an error with the `max_uses_exceeded` code.")
    assert self_contained(both)
    assert not self_contained(SPAN_REQUIREMENT)


def test_about_requires_the_entity_near_the_front():
    assert about(SPAN_REQUIREMENT, "needs_approval")
    assert not about("x" * 200 + " `needs_approval` matters here.", "needs_approval")


def test_find_bridges_rejects_cross_provider_pairs():
    facts = [
        {"evidence_text": SPAN_REQUIREMENT, "evidence_hash": "a" * 64,
         "critical_strings": ["needs_approval"], "provider": "openai",
         "version_id": "ver_a"},
        {"evidence_text": SPAN_CONSEQUENCE, "evidence_hash": "b" * 64,
         "critical_strings": ["rejected"], "provider": "anthropic",
         "version_id": "ver_b"},
    ]
    pairs, rejected = find_bridges(facts)
    assert pairs == []
    assert any("different providers" in r for entry in rejected
               for r in entry["reasons"])


def test_find_bridges_accepts_the_real_pair():
    facts = [
        {"evidence_text": SPAN_REQUIREMENT, "evidence_hash": "a" * 64,
         "critical_strings": ["needs_approval", "True"], "provider": "openai",
         "version_id": "ver_a"},
        {"evidence_text": SPAN_CONSEQUENCE, "evidence_hash": "b" * 64,
         "critical_strings": ["rejected"], "provider": "openai",
         "version_id": "ver_b"},
    ]
    pairs, _ = find_bridges(facts)
    assert len(pairs) == 1
    assert pairs[0]["bridge_entity"] == "needs_approval"
    assert pairs[0]["multi_hop_composition_check"] == PASS


# ------------------------------------------------------------------------ fact mining


def test_bridge_facts_carry_their_own_critical_strings():
    text = ("# Tools\n\n" + SPAN_REQUIREMENT + "\n\n" + SPAN_CONSEQUENCE + "\n")
    facts = mine_bridge_facts(make_doc(text))
    assert facts, "the miner found no condition or consequence sentences"
    for fact in facts:
        assert fact["critical_strings"]
        for string in fact["critical_strings"]:
            assert string in fact["evidence_text"]
        assert hashlib.sha256(
            fact["evidence_text"].encode("utf-8")).hexdigest() == fact["evidence_hash"]
        assert fact["proposed_question"] is None, (
            "a hop member has no standalone question; giving it one would let it leave "
            "the generator as a single-span case")
        assert fact["retrieval_was_not_run"] is True


# -------------------------------------------------------------------------- ambiguity


@pytest.mark.parametrize("scope", ["ContentDeltaEvent", "tool_result",
                                   "agents.run.RunConfig"])
def test_symbolic_scopes_are_scopes(scope):
    assert scope_is_symbolic(scope)


@pytest.mark.parametrize("scope", ["FAQ", "Limitations", "create", "Overview"])
def test_prose_headings_are_not_scopes(scope):
    assert not scope_is_symbolic(scope)


def test_ambiguity_needs_two_different_meanings():
    same = ("#### ContentDeltaEvent\n\n- `parsed`: The parsed content of the event.\n\n"
            "#### ContentDoneEvent\n\n- `parsed`: The parsed content of the event.\n")
    assert find_ambiguous_fields(make_doc(same)) == []

    differing = ("#### ContentDeltaEvent\n\n- `parsed`: The partially decoded fragment "
                 "so far.\n\n#### ContentDoneEvent\n\n- `parsed`: The complete "
                 "validated model instance.\n")
    findings = find_ambiguous_fields(make_doc(differing))
    assert [f["ambiguous_term"] for f in findings] == ["parsed"]
    assert len(findings[0]["candidate_interpretations"]) == 2
    assert findings[0]["required_scope_to_answer"]


# ------------------------------------------------------------- the batch on disk


def test_batch_claims_nothing_is_gold(batch):
    assert batch["retrieval_was_not_run"] is True
    assert batch["systems_executed"] == []
    for record in batch["records"]:
        assert record["verification_status"] == "candidate_unverified"
        assert record["chatgpt_verified"] is None
        assert record["claude_proposed"] is True
        assert record["retrieval_was_not_run"] is True


def test_no_retrieval_labels_leaked_into_the_batch(batch):
    """§23: nothing may be called hard before anything has been run against it."""
    forbidden = ("routing_heavy", "passage_heavy", "hard_for_bm25", "hard_for_doc-c",
                 "rank", "recall@", "ndcg")
    blob = json.dumps(batch["records"]).lower()
    for label in forbidden:
        assert label not in blob, f"{label!r} is an outcome-based label"


def test_every_span_hashes_to_its_own_text(batch):
    for record in batch["records"]:
        for span in record["expected_evidence"]:
            digest = hashlib.sha256(span["evidence_text"].encode("utf-8")).hexdigest()
            assert digest == span["evidence_hash"], record["candidate_id"]
            assert span["evidence_char_length"] == span["char_end"] - span["char_start"]


def test_critical_strings_belong_to_their_own_span(batch):
    """§19: a string is checked in its span, not in every span."""
    for record in batch["records"]:
        for span in record["expected_evidence"]:
            assert span["critical_strings"], record["candidate_id"]
            for string in span["critical_strings"]:
                assert string in span["evidence_text"], (
                    f"{record['candidate_id']} {span['evidence_id']}: {string!r}")


def test_claims_map_to_evidence(batch):
    for record in batch["records"]:
        ids = {span["evidence_id"] for span in record["expected_evidence"]}
        assert record["claim_evidence_map"], record["candidate_id"]
        assert len(record["claim_evidence_map"]) == len(record["atomic_claims"])
        for mapping in record["claim_evidence_map"]:
            assert mapping["evidence_id"] in ids


def test_multi_hop_records_carry_every_required_field(batch):
    for record in batch["records"]:
        if record["reasoning_type"] != "genuine_multi_hop":
            continue
        assert len(record["expected_evidence"]) >= 2
        assert record["requires_all_evidence"] is True
        assert record["evidence_shape"] in ("multi_span", "multi_document")
        assert record["multi_hop_composition_check"] == PASS
        for field in ("bridge_entity", "bridge_relationship", "hop_1_claim",
                      "hop_2_claim", "composed_claim", "composed_answer",
                      "why_span_1_alone_is_insufficient",
                      "why_span_2_alone_is_insufficient"):
            assert record[field], f"{record['candidate_id']} is missing {field}"
        assert record["needs_human_interpretation"] is True


def test_multi_hop_spans_are_independently_insufficient(batch):
    for record in batch["records"]:
        if record["reasoning_type"] != "genuine_multi_hop":
            continue
        first, second = record["expected_evidence"][:2]
        verdict = composition_check(
            record["bridge_entity"], first["evidence_text"], second["evidence_text"],
            first["critical_strings"], second["critical_strings"])
        assert verdict["multi_hop_composition_check"] == PASS, verdict["reasons"]


def test_multi_span_records_require_all_their_evidence(batch):
    for record in batch["records"]:
        multi = len(record["expected_evidence"]) > 1
        assert record["requires_all_evidence"] is multi, record["candidate_id"]
        assert (record["evidence_shape"] == "single_span") is not multi


def test_multi_document_shape_matches_the_spans(batch):
    for record in batch["records"]:
        versions = {span["version_id"] for span in record["expected_evidence"]}
        if record["evidence_shape"] == "multi_document":
            assert len(versions) > 1, record["candidate_id"]
            assert record["document_count"] == len(versions)


def test_ambiguity_records_carry_their_metadata(batch):
    for record in batch["records"]:
        if record["reasoning_type"] != "ambiguity_disambiguation":
            continue
        assert record["ambiguous_term"]
        assert len(record["candidate_interpretations"]) >= 2
        assert record["required_scope_to_answer"]
        # §11: the question names the scope, or it is a trick rather than a test.
        assert record["candidate_interpretations"][0]["scope"] in record["question"]


def test_evidence_sizes_stay_within_the_thresholds(batch):
    for record in batch["records"]:
        for span in record["expected_evidence"]:
            assert span["evidence_char_length"] <= 1500, record["candidate_id"]


def test_precheck_state_is_recorded_for_every_candidate(batch):
    for record in batch["records"]:
        assert record["precheck_holdout_ready"] is True
        assert record["precheck_failures"] == []
        # A precheck is not an approval, and must not read like one.
        assert record["verification_status"] == "candidate_unverified"


def test_known_failure_cases_are_not_retested(batch):
    """§22: AN-001, AN-003, AN-012 and OA-004 shaped the architecture."""
    excluded = {"AN-001", "AN-003", "AN-012", "OA-004"}
    development = Path("evals/development/v1.jsonl")
    if not development.exists():
        pytest.skip("no development set on disk")
    spans = set()
    for line in development.read_text().splitlines():
        if not line.strip():
            continue
        case = json.loads(line)
        if case["case_id"] not in excluded:
            continue
        for ref in case.get("expected_evidence", []):
            spans.add((ref.get("version_id"), ref.get("char_start"),
                       ref.get("char_end")))
    for record in batch["records"]:
        for span in record["expected_evidence"]:
            for version, start, end in spans:
                if span["version_id"] != version:
                    continue
                assert not (span["char_start"] < end and start < span["char_end"]), (
                    f"{record['candidate_id']} overlaps an excluded failure case")


# ------------------------------------------------------------------------- the report


def test_report_counts_match_the_batch(batch, report):
    assert report["total_candidates"] == len(batch["records"])
    assert report["genuine_multi_hop"] == sum(
        1 for r in batch["records"] if r["reasoning_type"] == "genuine_multi_hop")
    assert sum(report["by_reasoning_type"].values()) == len(batch["records"])
    assert sum(report["by_provider"].values()) == len(batch["records"])
    assert report["batch_sha256"] == batch["batch_sha256"]


def test_provider_reporting_is_derived_from_records(batch, report):
    for provider, count in report["by_provider"].items():
        assert count == sum(1 for r in batch["records"] if r["provider"] == provider)
    for provider, documents in report["documents_by_provider"].items():
        assert documents == len({r["document_title"] for r in batch["records"]
                                 if r["provider"] == provider})


def test_rejection_report_is_complete_and_classified(report):
    rejection = report["multi_hop_rejection"]
    assert rejection["unclassified"] == 0, (
        "a check grew a reason the report cannot file")
    assert sum(rejection["reasons"].values()) == rejection["rejected"]
    assert rejection["attempted_pairs"] == rejection["rejected"] + rejection["passed"]
    assert rejection["passed"] == report["genuine_multi_hop"]


def test_coverage_report_counts_no_candidate_as_eligible():
    if not COVERAGE.exists():
        pytest.skip(f"{COVERAGE} has not been generated")
    coverage = json.loads(COVERAGE.read_text())
    assert coverage["batch_004_candidates"]["holdout_eligible"] == 0
    assert coverage["batch_004_candidates"]["human_verified"] == 0
    assert coverage["confirmed"]["holdout_frozen"] is False


def test_frozen_systems_are_unchanged():
    """The frozen configs still hash to what was frozen.

    This looked for an ``evals/frozen`` directory that does not exist, so it skipped —
    and a skipping test is not coverage of the invariant it names. The hashes are
    computed from ``rag_v1.systems`` at import, which is where a change to either
    system would actually show up.
    """
    from rag_v1.systems import FROZEN_HASHES

    assert FROZEN_HASHES == FROZEN_SYSTEMS

