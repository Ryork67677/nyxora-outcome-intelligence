"""GOLD-001 tests: the authoring workflow must not be able to manufacture gold."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag_v1.gold.mining import (
    Candidate,
    anaphora_problem,
    code_regions,
    identifiers_in,
    inside_code,
    looks_like_code,
    mine_explicit_statements,
    mine_table_parameters,
    mine_table_required,
    resolve_anaphora,
)

BATCH = Path("evals/review/gold_review_batch_001.json")
PROPOSAL = Path("experiments/GOLD-001/oa-002-development-v2-proposal.json")
DEV = Path("evals/development/v1.jsonl")


class FakeSection:
    def __init__(self, path, start, end):
        self.path, self.char_start, self.char_end = path, start, end


def make_doc(text: str) -> dict:
    return {"version_id": "ver_test", "text": text, "provider": "openai",
            "title": "Test Doc", "url": "https://example.invalid", "captured_at": "2026-01-01",
            "sections": [FakeSection(["Body"], 0, len(text))]}


@pytest.fixture(scope="module")
def batch():
    if not BATCH.exists():
        pytest.skip("review batch not generated")
    return json.loads(BATCH.read_text())


# -- nothing leaves the miner as gold ----------------------------------------

def test_every_mined_candidate_is_unverified():
    doc = make_doc("| `foo_bar` | no | Enabled by default. Defaults to `true` here. |\n")
    doc["text"] = "| a | b |\n| --- | --- |\n" + doc["text"]
    doc["sections"] = [FakeSection(["Body"], 0, len(doc["text"]))]
    for candidate in mine_table_parameters(doc):
        assert candidate.verification_status == "candidate_unverified"
        assert candidate.chatgpt_verified is None
        assert candidate.claude_proposed is True


def test_candidate_dataclass_defaults_are_not_verified():
    fields = Candidate.__dataclass_fields__
    assert fields["verification_status"].default == "candidate_unverified"
    assert fields["chatgpt_verified"].default is None


#: Statuses a batch may hold at any point before a person has approved anything.
#: ``human_verified`` and ``human_approved`` are deliberately absent.
PRE_HUMAN_STATUSES = {
    "candidate_unverified", "dual_llm_pass", "dual_llm_fail", "needs_human_review",
}


def test_nothing_is_gold_without_a_human_approve(batch):
    """The invariant that outlives the batch's own lifecycle.

    The batch starts entirely unverified, gains dual-LLM statuses, then gains human
    ones. Through all of it, exactly one thing must never happen: a record reaching
    ``human_verified`` without a person having recorded APPROVE for it.
    """
    assert batch["retrieval_was_not_run"] is True
    for record in batch["records"]:
        gold = record["verification_status"] == "human_verified"
        approvals = [h["decision"] for h in record.get("human_decision_history", [])]
        assert gold == (approvals[-1:] == ["APPROVE"]), record["candidate_id"]
        assert record.get("human_verified", False) == gold
        if not gold:
            assert record["verification_status"] in PRE_HUMAN_STATUSES | {
                "human_rejected", "needs_edit"}


def test_a_repaired_candidate_keeps_its_old_anchor_and_pins_what_was_approved(batch):
    repaired = [r for r in batch["records"] if r.get("anchor_revisions")]
    if not repaired:
        pytest.skip("no boundary repairs applied yet")
    for record in repaired:
        # The old anchor survives beside the new one, and the new one contains it.
        revision = record["anchor_revisions"][-1]
        assert revision["reason"] == "evidence_boundary_completion"
        assert revision["new_char_start"] <= revision["old_char_start"]
        assert revision["new_char_end"] >= revision["old_char_end"]
        assert revision["old_evidence_text"] in revision["new_evidence_text"]
        assert revision["old_evidence_hash"] != revision["new_evidence_hash"]
        assert record["evidence_hash"] == revision["new_evidence_hash"]

        # A repair alone never approves. If the case is gold, the approval must name
        # the repaired anchor — approving the span that was sent back is the mistake
        # this pin exists to make impossible.
        if record["verification_status"] == "human_verified":
            history = record["human_decision_history"][-1]
            assert history["decision"] == "APPROVE"
            assert history["approved_evidence_hash"] == revision["new_evidence_hash"]
            assert history["approved_anchor_revision"] == revision["revision"]
        else:
            assert record["verification_status"] in {"needs_edit", "needs_human_review"}
            assert record["human_verified"] is False


# -- binding is structural, not proximity ------------------------------------

def test_table_miner_binds_the_value_to_the_row_parameter():
    text = ("| name | required | description |\n| --- | --- | --- |\n"
            "| `retry_count` | no | Number of retries. Defaults to `5`. |\n")
    doc = make_doc(text)
    candidates = mine_table_parameters(doc)
    assert candidates, "expected a table-row candidate"
    c = candidates[0]
    assert "retry_count" in c.proposed_question
    assert c.proposed_answer == "5"
    assert c.generator_confidence == "high"
    assert "structural" in c.binding


def test_table_miner_does_not_bind_across_rows():
    """The EXP-014R failure mode: a value from one row attaching to another."""
    text = ("| name | required | description |\n| --- | --- | --- |\n"
            "| `alpha_flag` | no | Turns the thing on. |\n"
            "| `beta_count` | no | Defaults to `9`. |\n")
    doc = make_doc(text)
    by_name = {c.proposed_question: c.proposed_answer for c in mine_table_parameters(doc)}
    # alpha_flag states no default, so it must not acquire beta_count's 9.
    assert not any("alpha_flag" in q for q in by_name)
    assert by_name.get("What is the default value of beta_count?") == "9"


def test_prose_miner_flags_ambiguous_subjects_instead_of_guessing():
    # No unresolved reference here — this fixture is about ambiguity of subject, which
    # is a different defect from the anaphoric-span rule tested below.
    text = ("The `first_option` and `second_option` values must be configured before "
            "startup, and each one is required for the handshake to complete now. ")
    doc = make_doc(text)
    candidates = mine_explicit_statements(doc)
    assert candidates
    c = candidates[0]
    assert c.needs_human_interpretation is True
    assert "AMBIGUOUS" in c.binding
    assert c.generator_confidence == "low"


def test_prose_candidates_propose_no_claims():
    """Claim synthesis is what failed; prose candidates leave it to the reviewer."""
    text = ("A `ValidationError` is raised when the payload cannot be parsed by the "
            "server before any downstream processing takes place at all here. ")
    doc = make_doc(text)
    for candidate in mine_explicit_statements(doc):
        assert candidate.proposed_atomic_claims == []
        assert candidate.proposed_answer == ""
        assert candidate.needs_human_interpretation is True
        assert "REVIEWER TO WRITE" in candidate.proposed_question


def test_identifier_detection_rejects_common_words():
    found = identifiers_in("The parameter value for `max_tokens` must be an integer.")
    assert "max_tokens" in found
    assert "parameter" not in found and "value" not in found


# -- review packets carry what a reviewer needs ------------------------------

def test_every_candidate_carries_context_and_provenance(batch):
    for record in batch["records"]:
        assert record["evidence_text"].strip()
        assert len(record["evidence_hash"]) == 64
        assert record["context_before"] or record["char_start"] == 0
        assert record["context_after"] or record["char_end"] > 0
        for field in ("provider", "document_title", "version_id", "section_path",
                      "char_start", "char_end", "evidence_kind", "binding",
                      "generator_confidence", "generator_notes"):
            assert field in record, field


def test_evidence_hash_matches_the_packaged_text(batch):
    import hashlib

    for record in batch["records"]:
        expected = hashlib.sha256(record["evidence_text"].encode("utf-8")).hexdigest()
        assert record["evidence_hash"] == expected, record["candidate_id"]


def test_batch_is_size_limited_and_deduplicated(batch):
    records = batch["records"]
    assert 15 <= len(records) <= 20
    questions = [r["proposed_question"] for r in records]
    spans = [(r["version_id"], r["char_start"], r["char_end"]) for r in records]
    assert len(set(questions)) == len(questions)
    assert len(set(spans)) == len(spans)


def test_batch_covers_both_providers(batch):
    assert set(batch["by_provider"]) >= {"anthropic", "openai"}
    assert min(batch["by_provider"].values()) >= 1


# -- verification import -----------------------------------------------------

def _importer():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_import_verification",
        Path(__file__).resolve().parents[1] / "scripts" / "import_verification.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_chatgpt_pass_never_becomes_human_verified():
    mod = _importer()
    record = {"candidate_id": "X", "proposed_question": "q", "proposed_answer": "a",
              "proposed_atomic_claims": [], "verification_status": "candidate_unverified",
              "version_id": "v", "char_start": 0, "char_end": 1, "evidence_hash": "h",
              "evidence_text": "t", "section_path": ["S"]}
    mod.apply_review(record, {"candidate_id": "X", "verdict": "PASS"}, "chatgpt", "now")
    assert record["verification_status"] == "dual_llm_pass"
    assert record["chatgpt_verified"] is True
    assert record.get("human_verified") is not True
    assert "human_verified" not in mod.STATUS_FROM_VERDICT.values()


@pytest.mark.parametrize(("verdict", "status"), [
    ("PASS", "dual_llm_pass"), ("FAIL", "dual_llm_fail"),
    ("FIX_REQUIRED", "needs_human_review"), ("UNCERTAIN", "needs_human_review"),
])
def test_verdicts_map_to_the_declared_statuses(verdict, status):
    mod = _importer()
    assert mod.STATUS_FROM_VERDICT[verdict] == status


def test_edits_are_versioned_not_overwritten():
    mod = _importer()
    record = {"candidate_id": "X", "proposed_question": "old question",
              "proposed_answer": "a", "proposed_atomic_claims": [],
              "verification_status": "candidate_unverified", "version_id": "v",
              "char_start": 0, "char_end": 1, "evidence_hash": "h",
              "evidence_text": "t", "section_path": ["S"]}
    mod.apply_review(record, {"candidate_id": "X", "verdict": "FIX_REQUIRED",
                              "suggested_question": "new question",
                              "suggested_fix": "clearer wording"},
                     "chatgpt", "2026-01-01T00:00:00Z")
    assert record["proposed_question"] == "new question"
    revision = record["revisions"][0]
    assert revision["from"] == "old question" and revision["to"] == "new question"
    assert revision["author"] == "chatgpt" and revision["reason"] == "clearer wording"


def test_a_reviewer_cannot_silently_move_the_source_anchor():
    mod = _importer()
    record = {"candidate_id": "X", "proposed_question": "q", "proposed_answer": "a",
              "proposed_atomic_claims": [], "verification_status": "candidate_unverified",
              "version_id": "v", "char_start": 10, "char_end": 20, "evidence_hash": "h",
              "evidence_text": "t", "section_path": ["S"]}
    mod.apply_review(record, {"candidate_id": "X", "verdict": "PASS", "char_start": 999},
                     "chatgpt", "now")
    assert record["char_start"] == 10
    assert record["anchor_disputes"][0]["field"] == "char_start"


def test_unknown_candidate_ids_are_rejected():
    mod = _importer()
    problems = mod.validate_review({"candidate_id": "NOPE", "verdict": "PASS"}, {"X"})
    assert any("unknown candidate_id" in p for p in problems)


def test_invalid_verdicts_are_rejected():
    mod = _importer()
    problems = mod.validate_review({"candidate_id": "X", "verdict": "LGTM"}, {"X"})
    assert any("invalid verdict" in p for p in problems)


@pytest.mark.parametrize("key", ["reviews", "records", "results"])
def test_review_envelopes_are_accepted_whatever_the_verifier_called_the_list(key):
    mod = _importer()
    reviews = [{"candidate_id": "X", "verdict": "PASS"}]
    assert mod.extract_reviews({key: reviews}) == reviews
    assert mod.extract_reviews(reviews) == reviews


def test_an_envelope_with_no_review_list_is_refused_rather_than_iterated():
    mod = _importer()
    # ``raw.get("reviews", raw)`` would return the dict here and iterate its keys,
    # importing garbage. Refusing loudly is the point.
    with pytest.raises(SystemExit):
        mod.extract_reviews({"reviewer": "chatgpt", "reviewed_at": "now"})


def test_a_review_of_a_different_batch_is_refused():
    mod = _importer()
    batch = {"batch_sha256": "a" * 64}
    mod.check_batch_provenance({"source_batch_sha256": "a" * 64}, batch)  # matches
    with pytest.raises(SystemExit) as excinfo:
        mod.check_batch_provenance({"source_batch_sha256": "b" * 64}, batch)
    assert "mismatch" in str(excinfo.value)


# -- human QC sampling -------------------------------------------------------

def _qc():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_select_human_qc",
        Path(__file__).resolve().parents[1] / "scripts" / "select_human_qc.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_disagreement_reaches_a_human():
    mod = _qc()
    records = [{"candidate_id": f"C{i}", "verification_status": s} for i, s in enumerate(
        ["dual_llm_pass", "dual_llm_fail", "needs_human_review", "candidate_unverified"])]
    queue = mod.build_queue(records, 0.0, seed=1)
    assert set(queue["must_review"]) == {"C1", "C2", "C3"}


def test_qc_sample_is_deterministic_for_a_seed():
    mod = _qc()
    records = [{"candidate_id": f"C{i:02d}", "verification_status": "dual_llm_pass"}
               for i in range(20)]
    first = mod.build_queue(records, 0.15, seed=7)
    second = mod.build_queue(records, 0.15, seed=7)
    assert first["qc_sample_of_dual_llm_pass"] == second["qc_sample_of_dual_llm_pass"]
    assert len(first["qc_sample_of_dual_llm_pass"]) == 3


def test_agreed_passes_are_still_sampled():
    """Two models agreeing is correlated, so agreement alone must not close the queue."""
    mod = _qc()
    records = [{"candidate_id": f"C{i:02d}", "verification_status": "dual_llm_pass"}
               for i in range(10)]
    queue = mod.build_queue(records, 0.15, seed=3)
    assert queue["qc_sample_of_dual_llm_pass"]


# -- validator gates ---------------------------------------------------------

def test_holdout_requires_human_approval_not_a_dual_llm_pass():
    from scripts_validate import validate_cases

    case = {"case_id": "H-1", "split": "holdout", "category": "exact_lookup",
            "provider": "openai", "question": "What is the default value of foo_bar?",
            "expected_claims": [{"text": "3", "critical": True}],
            "expected_evidence": [{"version_id": "v", "section_path": ["S"],
                                   "char_start": 0, "char_end": 10}],
            "expected_abstain": False, "verification": "dual_llm_pass",
            "human_verified": False, "source_document_title": "T",
            "source_url": "u", "source_captured_at": "t"}
    sources = {"v": {"text": "value is 3", "provider": "openai"}}
    failures = validate_cases([case], sources, {"holdout"})
    assert any(f["check"] == "human_verified_required" for f in failures)


def test_holdout_requires_provenance():
    from scripts_validate import validate_cases

    case = {"case_id": "H-2", "split": "holdout", "category": "exact_lookup",
            "provider": "openai", "question": "What is the default value of foo_bar?",
            "expected_claims": [{"text": "3", "critical": True}],
            "expected_evidence": [{"version_id": "v", "section_path": ["S"],
                                   "char_start": 0, "char_end": 10}],
            "expected_abstain": False, "verification": "human_approved",
            "human_verified": True}
    sources = {"v": {"text": "value is 3", "provider": "openai"}}
    failures = validate_cases([case], sources, {"holdout"})
    assert any(f["check"] == "missing_provenance" for f in failures)


def test_multi_hop_needs_more_than_one_span():
    from scripts_validate import validate_cases

    case = {"case_id": "M-1", "split": "development", "category": "multi_hop",
            "provider": "openai", "question": "What is the default value of foo_bar?",
            "expected_claims": [{"text": "3", "critical": True}],
            "expected_evidence": [{"version_id": "v", "section_path": ["S"],
                                   "char_start": 0, "char_end": 10}],
            "expected_abstain": False, "verification": "human_verified",
            "human_verified": True}
    sources = {"v": {"text": "value is 3", "provider": "openai"}}
    failures = validate_cases([case], sources, set())
    assert any(f["check"] == "multi_hop_structure" for f in failures)


# -- OA-002 proposal ---------------------------------------------------------

def test_oa002_correction_is_proposed_not_applied():
    if not PROPOSAL.exists():
        pytest.skip("proposal not generated")
    proposal = json.loads(PROPOSAL.read_text())
    assert proposal["status"].startswith("PROPOSED")
    assert proposal["current_anchor"]["contains_claim"] is False
    assert proposal["proposed_anchor"]["contains_claim"] is True

    # development/v1 must still carry the original, uncorrected anchor.
    case = next(json.loads(line) for line in DEV.read_text().splitlines()
                if line.strip() and json.loads(line)["case_id"] == "OA-002")
    assert case["expected_evidence"][0]["char_start"] == proposal["current_anchor"]["char_start"]


def test_systems_remain_frozen():
    from rag_v1.systems import FROZEN_HASHES

    assert FROZEN_HASHES["SYSTEM-A-GLOBAL"].startswith("9afcb5b7c58ebacf")
    assert FROZEN_HASHES["SYSTEM-B-DOC-C"].startswith("304c350940b83733")


# -- human QC packet --------------------------------------------------------

def _packet_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_export_human_qc_packet",
        Path(__file__).resolve().parents[1] / "scripts" / "export_human_qc_packet.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _reviewed_record(**overrides):
    record = {
        "candidate_id": "GOLD-B001-99", "document_title": "Guardrails",
        "section_path": ["Guardrails", "Input guardrails"], "version_id": "ver_x",
        "char_start": 10, "char_end": 40, "evidence_hash": "h",
        "evidence_kind": "explicit_exception", "generator_confidence": "medium",
        "provider": "openai", "source_url": "https://example.invalid/doc",
        "captured_at": "2026-08-01T00:00:00Z",
        "context_before": "before", "context_after": "after",
        "evidence_text": "If true, an `Tripwire` exception is raised.",
        "proposed_question": "What is raised when `tripwire_triggered` is true?",
        "proposed_answer": "A `Tripwire` exception.",
        "proposed_atomic_claims": ["When `tripwire_triggered` is true, `Tripwire` is raised."],
        "verification_status": "needs_human_review",
        "verification": {"verdict": "FIX_REQUIRED", "evidence_boundary_complete": False,
                         "verification_notes": "anchor starts with a pronoun"},
        "revisions": [{"revision": 1, "field": "proposed_question",
                       "from": "[REVIEWER TO WRITE] \u2026", "to": "What is raised?",
                       "author": "chatgpt", "timestamp": "t", "reason": "r"}],
    }
    record.update(overrides)
    return record


def test_a_claim_resting_on_a_term_the_anchor_lacks_is_flagged_not_smoothed_over():
    mod = _packet_module()
    item = mod.build_item(_reviewed_record(), "mandatory")
    # `tripwire_triggered` is asserted by the claim but appears nowhere in the span,
    # and the section path does not supply it either. This is the OA-002 shape.
    assert item["anchor_gaps"]["unsupported_in_claims"] == ["tripwire_triggered"]
    assert item["group"] == "check_anchor"
    assert item["risk"] == "HIGH"


def test_a_term_the_section_path_supplies_is_weaker_evidence_not_a_gap():
    mod = _packet_module()
    record = _reviewed_record(
        section_path=["Guardrails", "tripwire_triggered handling"])
    item = mod.build_item(record, "mandatory")
    assert item["anchor_gaps"]["unsupported_in_claims"] == []
    assert item["anchor_gaps"]["covered_by_provenance_only"] == ["tripwire_triggered"]
    assert item["risk"] == "MEDIUM"


def test_example_code_evidence_is_classified_as_d3_not_d2():
    mod = _packet_module()
    code = _reviewed_record(
        evidence_text='  "required": ["location"]\n  }\n',
        verification={"verdict": "FIX_REQUIRED",
                      "identifier_value_binding_correct": False})
    prose = _reviewed_record(
        evidence_text="The runner loops until it reaches the limit.",
        verification={"verdict": "FIX_REQUIRED",
                      "identifier_value_binding_correct": False})
    assert [d["class"] for d in mod.build_item(code, "m")["defects"]] == ["D3"]
    assert [d["class"] for d in mod.build_item(prose, "m")["defects"]] == ["D2"]


def test_a_failed_case_is_presented_for_rejection_not_rescued():
    mod = _packet_module()
    item = mod.build_item(_reviewed_record(
        verification={"verdict": "FAIL", "verification_notes": "sample config"}), "m")
    assert item["group"] == "recommended_reject"
    assert "recommends rejection" in item["why_human_review_required"]


def test_packet_retains_the_original_proposal_and_the_anchor_as_mined():
    mod = _packet_module()
    item = mod.build_item(_reviewed_record(), "mandatory")
    audit = item["audit"]
    assert audit["claude_original_proposal"]["proposed_question"].startswith(
        "[REVIEWER TO WRITE]")
    assert audit["revisions"][0]["author"] == "chatgpt"
    assert audit["anchor_as_mined"] == audit["anchor_current"]
    assert audit["chatgpt_review"]["verdict"] == "FIX_REQUIRED"
    # The final version is what the human decides on, not a reconstruction job.
    assert item["final"]["question"] == "What is raised when `tripwire_triggered` is true?"


def test_packet_never_declares_a_case_verified_and_never_preselects_approve():
    mod = _packet_module()
    item = mod.build_item(_reviewed_record(), "mandatory")
    assert item["decision"] is None
    assert item["decision_options"] == ["APPROVE", "REJECT", "NEEDS_EDIT"]
    assert "human_verified" not in mod.render_item(item)


# -- human decision import --------------------------------------------------

def _decisions_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_import_human_decisions",
        Path(__file__).resolve().parents[1] / "scripts" / "import_human_decisions.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(("decision", "status"), [
    ("APPROVE", "human_verified"), ("REJECT", "human_rejected"),
    ("NEEDS_EDIT", "needs_edit"),
])
def test_decisions_map_to_the_declared_statuses(decision, status):
    mod = _decisions_module()
    record = _reviewed_record()
    mod.apply_decision(record, {"candidate_id": record["candidate_id"],
                                "decision": decision}, "project_owner", "now")
    assert record["verification_status"] == status
    assert record["human_verified"] is (decision == "APPROVE")
    assert (status in mod.GOLD_STATUSES) is (decision == "APPROVE")


def test_only_approve_reaches_gold():
    mod = _decisions_module()
    assert mod.GOLD_STATUSES == {"human_verified"}
    gold = {d for d, s in mod.STATUS_FROM_DECISION.items() if s in mod.GOLD_STATUSES}
    assert gold == {"APPROVE"}


def test_an_undecided_candidate_is_never_promoted():
    mod = _decisions_module()
    record = _reviewed_record()
    changed = mod.apply_decision(record, {"candidate_id": record["candidate_id"],
                                          "decision": None}, "project_owner", "now")
    assert changed is False
    assert record["verification_status"] == "needs_human_review"
    assert record.get("human_verified") is not True


def test_a_model_cannot_be_the_human_reviewer():
    mod = _decisions_module()
    problems = mod.validate([{"candidate_id": "X", "decision": "APPROVE"}], {"X"}, "chatgpt")
    assert any("is a model, not a person" in p for p in problems)
    assert mod.validate([{"candidate_id": "X", "decision": "APPROVE"}],
                        {"X"}, "project_owner") == []


def test_unknown_and_invalid_decisions_are_rejected():
    mod = _decisions_module()
    problems = mod.validate([{"candidate_id": "NOPE", "decision": "APPROVE"},
                             {"candidate_id": "X", "decision": "LGTM"}],
                            {"X"}, "project_owner")
    assert any("unknown candidate_id" in p for p in problems)
    assert any("invalid decision" in p for p in problems)


def test_a_decision_is_appended_so_a_re_review_does_not_erase_the_first():
    mod = _decisions_module()
    record = _reviewed_record()
    entry = {"candidate_id": record["candidate_id"], "decision": "NEEDS_EDIT",
             "notes": "extend the anchor"}
    mod.apply_decision(record, entry, "project_owner", "t1")
    mod.apply_decision(record, {**entry, "decision": "APPROVE", "notes": "fixed"},
                       "project_owner", "t2")
    assert [h["decision"] for h in record["human_decision_history"]] == [
        "NEEDS_EDIT", "APPROVE"]
    assert record["revisions"][0]["author"] == "chatgpt"  # untouched


def test_validation_report_blocks_an_approved_case_with_a_placeholder_question():
    mod = _decisions_module()
    import hashlib
    text = "If true, an `Tripwire` exception is raised."
    record = _reviewed_record(
        evidence_hash=hashlib.sha256(text.encode()).hexdigest(),
        proposed_question="[REVIEWER TO WRITE] something",
        verification_status="human_verified")
    report = mod.validation_report({"batch": 1, "records": [record]},
                                   "project_owner", "now")
    assert report["passed"] is False
    assert any("placeholder question" in f for f in report["gate_failures"])
    assert report["eligible_for_gold"] == ["GOLD-B001-99"]


def test_validation_report_catches_evidence_hash_drift():
    mod = _decisions_module()
    record = _reviewed_record(evidence_hash="not-the-real-hash",
                              verification_status="human_verified")
    report = mod.validation_report({"batch": 1, "records": [record]},
                                   "project_owner", "now")
    assert any("evidence hash drift" in f for f in report["gate_failures"])


# -- evidence-boundary repair ------------------------------------------------

def _repair_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_repair_evidence_boundary",
        Path(__file__).resolve().parents[1] / "scripts" / "repair_evidence_boundary.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOURCE = ("Input guardrails run in 3 steps. Finally we check `.tripwire_triggered`. "
          "If true, an exception is raised.")


def _repairable(**overrides):
    import hashlib
    old = SOURCE.index("If true")
    text = SOURCE[old:]
    record = {
        "candidate_id": "GOLD-B001-99", "version_id": "ver_x",
        "char_start": old, "char_end": len(SOURCE),
        "evidence_text": text,
        "evidence_hash": hashlib.sha256(text.encode()).hexdigest(),
        "section_path": ["Guardrails"], "document_title": "Guardrails",
        "provider": "openai", "source_url": "https://example.invalid",
        "captured_at": "2026-08-01T00:00:00Z", "evidence_kind": "explicit_exception",
        "generator_confidence": "medium", "context_before": "", "context_after": "",
        "proposed_question": "old question?", "proposed_answer": "old answer",
        "proposed_atomic_claims": ["old claim"],
        "verification_status": "needs_edit", "human_decision": "NEEDS_EDIT",
        "human_verified": False,
    }
    record.update(overrides)
    return record


REPAIR = {
    "candidate_id": "GOLD-B001-99",
    "locate_head": "Input guardrails run in 3 steps.",
    "locate_tail": "an exception is raised.",
    "question": "What happens when `.tripwire_triggered` is true?",
    "answer": "An exception is raised.",
    "atomic_claims": ["If `.tripwire_triggered` is true, an exception is raised."],
    "critical_strings": [".tripwire_triggered", "an exception is raised"],
}


def test_a_repair_grows_the_anchor_and_keeps_the_old_one():
    mod = _repair_module()
    record = _repairable()
    old_start, old_hash = record["char_start"], record["evidence_hash"]
    revision = mod.apply_repair(record, REPAIR, SOURCE, "2026-01-01T00:00:00Z")

    assert revision["old_char_start"] == old_start
    assert revision["old_evidence_hash"] == old_hash
    assert revision["new_char_start"] == 0
    assert revision["old_evidence_text"] in revision["new_evidence_text"]
    assert record["char_start"] == 0 and record["evidence_hash"] != old_hash
    # The repair sends the case back for review; it cannot approve it.
    assert record["verification_status"] == "needs_human_review"
    assert record["human_verified"] is False
    assert mod.STATUS_AFTER_REPAIR != "human_verified"


def test_a_repair_that_would_move_the_anchor_elsewhere_is_refused():
    mod = _repair_module()
    # A span that does not contain the original is a re-anchoring, not a completion.
    with pytest.raises(SystemExit) as excinfo:
        mod.check_superset(SOURCE, (0, 31), (SOURCE.index("If true"), len(SOURCE)))
    assert "does not contain old span" in str(excinfo.value)


def test_only_a_candidate_the_owner_sent_back_may_be_repaired():
    mod = _repair_module()
    for decision in ("APPROVE", "REJECT", None):
        record = _repairable(human_decision=decision)
        with pytest.raises(SystemExit) as excinfo:
            mod.apply_repair(record, REPAIR, SOURCE, "t")
        assert "not NEEDS_EDIT" in str(excinfo.value)


def test_the_rewritten_question_is_a_revision_not_an_overwrite():
    mod = _repair_module()
    record = _repairable()
    mod.apply_repair(record, REPAIR, SOURCE, "t")
    revision = next(r for r in record["revisions"] if r["field"] == "proposed_question")
    assert revision["from"] == "old question?"
    assert revision["reason"] == "evidence_boundary_completion"
    assert revision["directed_by"] == "project_owner"
    assert record["proposed_question"] == REPAIR["question"]


def test_every_critical_string_is_actually_inside_the_repaired_span():
    mod = _repair_module()
    record = _repairable()
    mod.apply_repair(record, REPAIR, SOURCE, "t")
    span = record["evidence_text"].lower()
    assert all(s.lower() in span for s in record["critical_strings"])


# -- approving a repaired case ----------------------------------------------

def _repaired_record():
    record = _reviewed_record(
        candidate_id="GOLD-B001-98",
        evidence_hash="new" + "0" * 61,
        human_decision="NEEDS_EDIT",
        anchor_revisions=[{
            "revision": 1, "reason": "evidence_boundary_completion",
            "old_char_start": 10, "old_char_end": 40, "old_evidence_hash": "old" + "0" * 61,
            "new_char_start": 0, "new_char_end": 40, "new_evidence_hash": "new" + "0" * 61,
        }])
    return record


def test_approving_a_repaired_case_must_name_the_revision_it_approves():
    mod = _decisions_module()
    record = _repaired_record()
    entry = {"candidate_id": record["candidate_id"], "decision": "APPROVE"}
    problems = mod.revision_problems(record, entry)
    assert any("must pin it with approves_evidence_hash" in p for p in problems)


def test_an_approval_of_the_pre_repair_anchor_is_refused():
    mod = _decisions_module()
    record = _repaired_record()
    # The owner reviewed the repair packet; approving the span that was sent back
    # would silently gold the version the repair existed to replace.
    problems = mod.revision_problems(record, {
        "candidate_id": record["candidate_id"], "decision": "APPROVE",
        "approves_evidence_hash": record["anchor_revisions"][0]["old_evidence_hash"]})
    assert any("BEFORE the repair" in p for p in problems)


def test_an_approval_pinned_to_the_current_anchor_is_accepted():
    mod = _decisions_module()
    record = _repaired_record()
    entry = {"candidate_id": record["candidate_id"], "decision": "APPROVE",
             "approves_evidence_hash": record["evidence_hash"],
             "approves_anchor_revision": 1}
    assert mod.revision_problems(record, entry) == []
    mod.apply_decision(record, entry, "project_owner", "now")
    assert record["verification_status"] == "human_verified"
    history = record["human_decision_history"][-1]
    assert history["approved_evidence_hash"] == record["evidence_hash"]
    assert history["approved_anchor_revision"] == 1
    # The repair history is not erased by the approval.
    assert record["anchor_revisions"][0]["old_evidence_hash"] == "old" + "0" * 61


def test_an_unrepaired_case_needs_no_pin():
    mod = _decisions_module()
    record = _reviewed_record()
    assert mod.revision_problems(
        record, {"candidate_id": record["candidate_id"], "decision": "APPROVE"}) == []


def test_projection_reports_which_cases_are_not_claim_checked():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_export_golden_projection",
        Path(__file__).resolve().parents[1] / "scripts" / "export_golden_projection.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    sentence = mod.project(_reviewed_record(), "validation")
    assert sentence["claims_are_critical"] is False
    assert all(c["critical"] is False for c in sentence["expected_claims"])

    verbatim = mod.project(
        _reviewed_record(critical_strings=["Tripwire"]), "validation")
    assert verbatim["claims_are_critical"] is True
    assert verbatim["expected_claims"] == [{"text": "Tripwire", "critical": True}]
    # A projection is not a split assignment.
    assert verbatim["split_is_placeholder"] is True


# -- closure -----------------------------------------------------------------

def _close_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_close_batch",
        Path(__file__).resolve().parents[1] / "scripts" / "close_batch.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CLOSURE = Path(__file__).resolve().parents[1] / "experiments" / "GOLD-001" / \
    "GOLD-001-batch-001-closure.json"


def test_a_closed_batch_has_not_been_edited_since_closure(batch):
    """The point of recording a closure hash is that someone checks it."""
    if not CLOSURE.exists() or "closure_sha256" not in batch:
        pytest.skip("batch 001 is not closed yet")
    mod = _close_module()
    closure = json.loads(CLOSURE.read_text())
    actual = mod.candidate_digest(batch["records"])
    assert actual == batch["closure_sha256"], "batch 001 changed after closure"
    assert actual == closure["closure_sha256"]


def test_closure_counts_match_the_batch_itself(batch):
    if not CLOSURE.exists():
        pytest.skip("batch 001 is not closed yet")
    closure = json.loads(CLOSURE.read_text())
    from collections import Counter
    statuses = Counter(r["verification_status"] for r in batch["records"])
    assert closure["totals"]["candidates"] == len(batch["records"])
    assert closure["totals"]["human_verified"] == statuses["human_verified"]
    assert closure["totals"]["human_rejected"] == statuses["human_rejected"]
    assert closure["totals"]["outstanding_decisions"] == 0
    # A closure may not claim a higher acceptance rate than the records support.
    expected = statuses["human_verified"] / len(batch["records"])
    assert closure["totals"]["acceptance_rate"] == round(expected, 4)


def test_closure_is_refused_while_a_decision_is_outstanding():
    mod = _close_module()
    records = [{"candidate_id": "X", "verification_status": "human_verified"},
               {"candidate_id": "Y", "verification_status": "dual_llm_pass"}]
    with pytest.raises(SystemExit) as excinfo:
        mod.build({"batch": 1, "records": records}, {"passed": True}, "now")
    assert "no final human decision" in str(excinfo.value)
    assert "Y" in str(excinfo.value)


def test_rejected_candidates_survive_closure(batch):
    if not CLOSURE.exists():
        pytest.skip("batch 001 is not closed yet")
    closure = json.loads(CLOSURE.read_text())
    rejected_ids = {r["candidate_id"] for r in closure["rejected"]}
    present = {r["candidate_id"] for r in batch["records"]}
    assert rejected_ids and rejected_ids <= present
    for entry in closure["rejected"]:
        assert entry["reason"].strip(), entry["candidate_id"]


def test_closure_does_not_claim_retrieval_was_run(batch):
    if not CLOSURE.exists():
        pytest.skip("batch 001 is not closed yet")
    closure = json.loads(CLOSURE.read_text())
    assert closure["retrieval"]["retrieval_was_not_run"] is True
    assert closure["retrieval"]["systems_run_against_these_candidates"] == []


# -- batch 002 preregistered miner rules -------------------------------------
#
# Each test names the batch-001 candidate whose defect the rule exists to prevent, so a
# later change to the rule has to argue with the evidence rather than with an opinion.

def test_rule1_resolves_the_gold_b001_04_shape():
    """"If true, an exception is raised" — the antecedent was outside the anchor."""
    text = ("Finally, we check if `.tripwire_triggered` is true. "
            "If true, an `InputGuardrailTripwireTriggered` exception is raised.")
    start = text.index("If true")
    assert anaphora_problem(text[start:]) is not None
    resolved = resolve_anaphora(text, start, len(text))
    assert resolved == (0, len(text))
    assert ".tripwire_triggered" in text[resolved[0]:resolved[1]]


def test_rule1_resolves_the_gold_b001_14_shape():
    """"any of these models" — the scope was outside the anchor."""
    text = ("Claude 4.6 and later models do not support prefilling. "
            "Sending a request to any of these models returns a 400 error.")
    start = text.index("Sending")
    assert "no antecedent" in anaphora_problem(text[start:])
    assert resolve_anaphora(text, start, len(text)) == (0, len(text))


def test_rule1_drops_a_span_whose_antecedent_does_not_exist():
    # Extension is bounded; a span that cannot be made self-contained is dropped, which
    # is a legitimate and preferable outcome to shipping an uncheckable candidate.
    text = "If true, an exception is raised."
    assert resolve_anaphora(text, 0, len(text)) is None


def test_rule1_leaves_a_self_contained_span_alone():
    text = "The `body` parameter must be the raw JSON string sent from the server."
    assert anaphora_problem(text) is None
    assert resolve_anaphora(text, 0, len(text)) == (0, len(text))


def test_rule2_no_relation_label_reaches_the_reviewer():
    """Batch 001's label was wrong on five of sixteen and steered the first reading."""
    text = ("A `ValidationError` is raised when the payload cannot be parsed by the "
            "server before any downstream processing takes place at all here. ")
    candidates = mine_explicit_statements(make_doc(text))
    assert candidates
    for candidate in candidates:
        assert candidate.evidence_kind == "prose_statement"
        exported = json.dumps(candidate.to_dict()).lower()
        for label in ("explicit_exception", "explicit_response", "explicit_constraint",
                      "explicit_required_optional", "explicit_deprecation"):
            assert label not in exported
        # The marker phrase that selected the sentence is not named either.
        assert "relationship stated" not in exported


def test_rule3_refuses_a_span_inside_a_fenced_block():
    """GOLD-B001-15: `required: ["location"]` read out of an example request body."""
    text = ('Some prose about tools that is long enough to be mined and then some.\n\n'
            '```json\n{\n  "required": ["location"],\n  "tool_choice": {"type": "any"}\n}\n```\n')
    regions = code_regions(text)
    fence = text.index("```json")
    assert regions and inside_code(regions, fence + 10, fence + 40)
    assert not inside_code(regions, 0, 20)
    assert mine_explicit_statements(make_doc(text)) == []


def test_rule3_refuses_a_span_that_is_shaped_like_code_without_a_fence():
    assert looks_like_code('  "required": ["location"]')
    assert looks_like_code("    raise ValueError('no')")
    assert not looks_like_code("The runner loops until Claude returns a message.")


def test_rule4_required_column_yields_a_complete_structural_proposal():
    text = ("| name | required | description |\n| --- | --- | --- |\n"
            "| `session_id` | yes | Identifies the session. |\n")
    candidates = mine_table_required(make_doc(text))
    assert candidates
    c = candidates[0]
    assert c.proposed_question == "Is the `session_id` parameter required?"
    assert c.proposed_answer == "Yes, it is required."
    assert c.proposed_atomic_claims == ["`session_id` is required."]
    assert c.generator_confidence == "high"
    assert c.needs_human_interpretation is False
    # Complete means claim-checkable: every critical string is inside the span.
    assert c.critical_strings
    assert all(s.lower() in c.evidence_text.lower() for s in c.critical_strings)


def test_rule4_required_miner_does_not_bind_across_rows():
    text = ("| name | required | description |\n| --- | --- | --- |\n"
            "| `alpha_flag` | no | Optional switch. |\n"
            "| `beta_id` | yes | Needed always. |\n")
    answers = {c.proposed_question: c.proposed_answer
               for c in mine_table_required(make_doc(text))}
    assert answers["Is the `alpha_flag` parameter required?"] == "No, it is optional."
    assert answers["Is the `beta_id` parameter required?"] == "Yes, it is required."


def test_rule4_required_miner_ignores_a_table_with_no_required_column():
    text = ("| name | type | description |\n| --- | --- | --- |\n"
            "| `session_id` | string | Identifies the session. |\n")
    assert mine_table_required(make_doc(text)) == []


# -- batch 002 review revisions ----------------------------------------------

BATCH_002 = Path(__file__).resolve().parents[1] / "evals" / "review" / \
    "gold_review_batch_002.json"


@pytest.fixture
def batch2():
    if not BATCH_002.exists():
        pytest.skip("batch 002 has not been generated")
    return json.loads(BATCH_002.read_text())


def test_batch_002_reached_gold_only_through_a_human_approve(batch2):
    for record in batch2["records"]:
        # Every candidate was FIX_REQUIRED at the independent-review stage; none
        # reached approval carrying the proposal the miner exported.
        assert record["verification"]["verdict"] == "FIX_REQUIRED"
        gold = record["verification_status"] == "human_verified"
        approvals = [h["decision"] for h in record.get("human_decision_history", [])]
        assert gold == (approvals[-1:] == ["APPROVE"]), record["candidate_id"]
        assert record.get("human_verified", False) == gold
    assert batch2["retrieval_was_not_run"] is True


def test_every_batch_002_critical_string_is_inside_its_own_span(batch2):
    """The gap batch 001 closed with: a claim the validator cannot check."""
    from rag_v1.gold.normalisation import contains_claim_string

    for record in batch2["records"]:
        assert record["critical_strings"], record["candidate_id"]
        for string in record["critical_strings"]:
            assert contains_claim_string(record["evidence_text"], string), (
                record["candidate_id"], string)


def test_batch_002_revisions_preserve_the_miner_original(batch2):
    for record in batch2["records"]:
        first = next(r for r in record["revisions"]
                     if r["field"] == "proposed_question")
        # The exported question the miner wrote is still recoverable.
        assert first["from"] != record["proposed_question"]
        assert first["reason"] in {
            "MINER_QUESTION_HEADER_DEPENDENCY", "QUESTION_AUTHORING_REQUIRED",
            "MINER_EVIDENCE_DEFECT"}


def test_batch_002_anchor_extensions_are_supersets_and_keep_both_spans(batch2):
    repaired = [r for r in batch2["records"] if r.get("anchor_revisions")]
    assert {r["candidate_id"] for r in repaired} == {"GOLD-B002-12", "GOLD-B002-18"}
    for record in repaired:
        revision = record["anchor_revisions"][-1]
        assert revision["new_char_start"] <= revision["old_char_start"]
        assert revision["new_char_end"] >= revision["old_char_end"]
        assert revision["old_evidence_text"] in revision["new_evidence_text"]
        assert record["evidence_hash"] == revision["new_evidence_hash"]
        assert revision["old_evidence_hash"] != revision["new_evidence_hash"]


def test_the_defect_classes_the_review_named_are_preserved(batch2):
    classes = {r["candidate_id"]: r["review_defect_class"] for r in batch2["records"]}
    assert classes["GOLD-B002-12"] == "MINER_EVIDENCE_DEFECT"
    assert classes["GOLD-B002-18"] == "MINER_EVIDENCE_DEFECT"
    # The nine structural candidates are a third class, not folded into either of the
    # two the review named: their evidence is sound, but the miner's question was not.
    header = [c for c, k in classes.items() if k == "MINER_QUESTION_HEADER_DEPENDENCY"]
    assert len(header) == 9
    assert all(c <= "GOLD-B002-09" for c in header)


# -- claim-support audit -----------------------------------------------------

def _audit_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_audit_claim_support",
        Path(__file__).resolve().parents[1] / "scripts" / "audit_claim_support.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_claim_asserting_a_term_the_span_lacks_is_unsupported():
    mod = _audit_module()
    result = mod.audit_claim(
        "On Google Cloud Agent Platform, `anthropic_version` must be `vertex-2023-10-16`.",
        "On Agent Platform, `anthropic_version` must be set to `vertex-2023-10-16`.",
        provenance="Claude on Google Cloud")
    assert result["status"] == mod.UNSUPPORTED
    assert "Google Cloud Agent Platform" in result["terms_missing_from_span"]


def test_a_term_supplied_only_by_provenance_needs_review_not_a_verdict():
    mod = _audit_module()
    result = mod.audit_claim(
        "A Files API `File not found` error uses HTTP 404.",
        "**File not found (404):** The specified `file_id` doesn't exist.",
        provenance="Files API > Error handling")
    assert result["status"] == mod.NEEDS_REVIEW
    assert result["terms_only_in_provenance"] == ["Files API"]


def test_a_claim_whose_terms_are_all_in_the_span_is_supported():
    mod = _audit_module()
    result = mod.audit_claim(
        "`enable_zoom` defaults to `false`.",
        "| `enable_zoom` | No | Enable zoom action. Default: `false` |",
        provenance="Computer use tool")
    assert result["status"] == mod.SUPPORTED


def test_the_audit_is_an_overlay_and_never_edits_the_closed_batch(batch):
    audit = Path(__file__).resolve().parents[1] / "experiments" / "GOLD-001" / \
        "GOLD-001-batch-001-claim-audit.json"
    if not audit.exists() or "closure_sha256" not in batch:
        pytest.skip("audit or closure not present")
    mod = _close_module()
    overlay = json.loads(audit.read_text())
    # The overlay records the hash it audited, and the batch still hashes to it.
    assert overlay["closure_sha256"] == batch["closure_sha256"]
    assert mod.candidate_digest(batch["records"]) == batch["closure_sha256"]
    assert overlay["proposed_v2"]["status"].startswith("PROPOSED")
    assert overlay["retrieval_was_not_run"] is True


def test_holdout_eligibility_requires_both_support_and_a_checkable_claim():
    mod = _audit_module()
    import hashlib

    evidence = "`alpha` defaults to `5`."
    record = {
        "candidate_id": "X", "evidence_text": evidence,
        "evidence_hash": hashlib.sha256(evidence.encode()).hexdigest(),
        "verification_status": "human_verified", "human_verified": True,
        "document_title": "Doc", "section_path": ["S"],
        "proposed_question": "q", "proposed_answer": "a",
        "proposed_atomic_claims": ["`alpha` defaults to `5`."],
    }
    without = mod.audit_case(record)
    assert without["status"] == mod.SUPPORTED
    # Supported claims are not enough: with no critical strings the validator checks
    # nothing, so a holdout built on it would be gated on nothing.
    assert without["holdout_eligible"] is False
    with_strings = mod.audit_case({**record, "critical_strings": ["alpha", "5"]})
    assert with_strings["holdout_eligible"] is True


# -- markdown-escape normalisation -------------------------------------------
#
# GOLD-B002-02's row writes the scheme as `https\://`, escaping the colon so the
# renderer does not linkify it, while the claim writes `https://`. Failing that check
# on a backslash the renderer would drop is a defect in the checker.

def test_a_markdown_escape_does_not_defeat_a_critical_string():
    from rag_v1.gold.normalisation import contains_claim_string

    row = r"| `url` | string | Yes | The URL of the MCP server. Must start with https\://. |"
    assert contains_claim_string(row, "Must start with https://")
    assert contains_claim_string(row, r"Must start with https\://")


def test_normalisation_undoes_escapes_and_nothing_else():
    from rag_v1.gold.normalisation import normalise_for_comparison, unescape_markdown

    assert unescape_markdown(r"a\.b\:c\*d") == "a.b:c*d"
    # A backslash before a non-escapable character is not a Markdown escape, so it stays.
    assert unescape_markdown(r"a\qb") == r"a\qb"
    # No case folding, no whitespace collapsing, no quote or dash substitution — each
    # would let a claim match evidence that does not say it.
    for text in ("Two  spaces", "MiXeD CaSe", "en–dash", "“curly”"):
        assert normalise_for_comparison(text) == text


def test_normalisation_cannot_make_a_false_claim_match():
    from rag_v1.gold.normalisation import contains_claim_string

    assert not contains_claim_string("The default is 5.", "The default is 6")
    assert not contains_claim_string("must start with http://", "must start with https://")


def test_evidence_is_stored_and_hashed_raw_not_normalised(batch2):
    """Normalisation is for comparison only; the hash must stay on the source form."""
    import hashlib

    record = next(r for r in batch2["records"] if r["candidate_id"] == "GOLD-B002-02")
    assert r"https\://" in record["evidence_text"], "raw escape must survive in storage"
    assert hashlib.sha256(
        record["evidence_text"].encode("utf-8")).hexdigest() == record["evidence_hash"]


# -- holdout eligibility is not human approval -------------------------------

def _eligible_case(**overrides):
    import hashlib

    evidence = "| `alpha` | No | Default: `5` |"
    case = {
        "candidate_id": "X", "verification_status": "human_verified",
        "human_verified": True, "evidence_text": evidence,
        "evidence_hash": hashlib.sha256(evidence.encode()).hexdigest(),
        "proposed_atomic_claims": ["`alpha` defaults to `5`."],
        "critical_strings": ["`alpha`", "Default: `5`"],
    }
    case.update(overrides)
    return case


def test_the_two_states_are_independent():
    from rag_v1.gold.eligibility import evaluate

    # Approved but not checkable: still human_verified, not holdout-eligible.
    approved_only = _eligible_case(critical_strings=[])
    verdict = evaluate(approved_only)
    assert verdict["holdout_eligible"] is False
    assert approved_only["verification_status"] == "human_verified"
    assert approved_only["human_verified"] is True, "eligibility must not revoke approval"

    # Checkable but not approved: eligibility cannot substitute for a person.
    unapproved = _eligible_case(verification_status="needs_human_review",
                                human_verified=False)
    assert evaluate(unapproved)["holdout_eligible"] is False
    assert any(f["condition"] == "human_verified"
               for f in evaluate(unapproved)["failures"])


def test_every_holdout_condition_can_block_on_its_own():
    from rag_v1.gold.eligibility import HOLDOUT_CONDITIONS, evaluate

    assert evaluate(_eligible_case())["holdout_eligible"] is True
    blockers = {
        "human_verified": {"human_verified": False},
        "every_claim_has_a_deterministic_check": {"critical_strings": []},
        "critical_strings_present_in_evidence": {"critical_strings": ["not in the span"]},
        "evidence_hash_valid": {"evidence_hash": "0" * 64},
        "no_unresolved_scope_defect": {"unresolved_scope_defect": "claim scope outside span"},
    }
    assert set(blockers) == set(HOLDOUT_CONDITIONS)
    for condition, override in blockers.items():
        verdict = evaluate(_eligible_case(**override))
        assert verdict["holdout_eligible"] is False, condition
        assert any(f["condition"] == condition for f in verdict["failures"]), condition


def test_only_eligible_cases_are_offered_to_a_holdout():
    from rag_v1.gold.eligibility import eligible

    cases = [_eligible_case(candidate_id="A"),
             _eligible_case(candidate_id="B", critical_strings=[])]
    assert [c["candidate_id"] for c in eligible(cases)] == ["A"]


# -- batch 001 v2 overlay ----------------------------------------------------

V2 = Path(__file__).resolve().parents[1] / "evals" / "gold" / "batch_001_v2"


@pytest.fixture
def overlay():
    path = V2 / "overlay.json"
    if not path.exists():
        pytest.skip("the v2 overlay has not been built")
    return json.loads(path.read_text())


def test_a_metadata_upgrade_changes_no_v1_content(overlay, batch):
    """Metadata-only cases must be byte-identical to v1 apart from critical strings.

    Scope repairs are excluded: those legitimately move the span, and are held to a
    different contract by the scope-repair test below.
    """
    v1 = {r["candidate_id"]: r for r in batch["records"]}
    repaired = set(overlay["scope_repairs"])
    checked = 0
    for case in overlay["case_records"]:
        if case["candidate_id"] in repaired:
            continue
        original = v1[case["candidate_id"]]
        for field in ("proposed_question", "proposed_answer", "proposed_atomic_claims",
                      "char_start", "char_end", "version_id", "evidence_hash",
                      "evidence_text"):
            assert case[field] == original[field], (case["candidate_id"], field)
        checked += 1
    assert checked == len(overlay["case_records"]) - len(repaired)


def test_the_overlay_records_the_v1_closure_hash_and_v1_still_matches(overlay, batch):
    mod = _close_module()
    assert overlay["v1_closure_sha256"] == batch["closure_sha256"]
    assert mod.candidate_digest(batch["records"]) == batch["closure_sha256"]


def test_every_overlay_critical_string_is_inside_its_own_span(overlay):
    from rag_v1.gold.normalisation import contains_claim_string

    for case in overlay["case_records"]:
        assert case["critical_strings"], case["candidate_id"]
        for string in case["critical_strings"]:
            assert contains_claim_string(case["evidence_text"], string), (
                case["candidate_id"], string)


def test_the_scope_defect_cases_entered_v2_only_through_an_approved_repair(overlay):
    present = {c["candidate_id"] for c in overlay["case_records"]}
    assert {"GOLD-B001-13", "GOLD-B001-17"} <= present
    assert overlay["pending_scope_repair"] == []
    for candidate_id in ("GOLD-B001-13", "GOLD-B001-17"):
        case = next(c for c in overlay["case_records"]
                    if c["candidate_id"] == candidate_id)
        # Present because a person approved a specific span, not because a script
        # decided the case looked fixed.
        assert case["v2_approval"]["decision"] == "APPROVE"
        assert case["v2_approval"]["approved_evidence_hash"] == case["evidence_hash"]
        assert case["v1_evidence_hash"] != case["evidence_hash"]
    # The count claimed must be the count computed, not a number in prose.
    assert overlay["holdout_eligible_count"] == len(overlay["holdout_eligible"])
    assert overlay["holdout_eligible_count"] == len(overlay["case_records"])


def test_the_scope_repairs_are_proposed_and_applied_to_nothing(batch):
    path = V2 / "gold_batch_001_v2_scope_repairs.json"
    if not path.exists():
        pytest.skip("the scope-repair packet has not been built")
    packet = json.loads(path.read_text())
    assert packet["status"].startswith("PROPOSED")
    assert packet["v1_closure_sha256"] == batch["closure_sha256"]
    v1 = {r["candidate_id"]: r for r in batch["records"]}
    for candidate_id, options in packet["repairs"].items():
        # v1 still holds the pre-repair anchor and no critical strings.
        assert v1[candidate_id]["char_start"] == options[0]["old_char_start"]
        assert not v1[candidate_id].get("critical_strings")
        assert any(o["recommended"] for o in options)


# -- closure reports may not contradict themselves ---------------------------
#
# Batch 002's closure said "17 of 17 verified cases carry literal critical strings" and,
# two sections later, "only the three repaired cases carry literal critical strings".
# The second was a fixed string describing batch 001 that the builder emitted verbatim
# into every batch afterwards. See GOLD-001-batch-002-closure-erratum.md.

@pytest.mark.parametrize(("verified", "with_critical"), [
    (17, 17), (16, 3), (5, 0), (1, 1), (0, 0), (40, 39),
])
def test_the_claim_check_caveat_never_contradicts_its_own_count(verified, with_critical):
    mod = _close_module()
    caveat = mod.claim_check_caveat(verified, with_critical)
    unchecked = verified - with_critical

    if verified and unchecked == 0:
        # It must not claim anything is unchecked when nothing is.
        assert "says nothing about claim support" not in caveat
        assert "without testing anything" not in caveat
        assert str(verified) in caveat
    elif verified:
        # It must name the real shortfall, not a remembered one.
        assert str(with_critical) in caveat or "None of" in caveat
        assert str(unchecked) in caveat or with_critical == 0


def test_the_caveat_is_derived_from_the_records_not_stored_prose():
    mod = _close_module()
    # The same builder, given different batches, must produce different caveats.
    assert mod.claim_check_caveat(17, 17) != mod.claim_check_caveat(16, 3)


def test_batch_002_closure_agrees_with_its_own_records(batch2):
    from rag_v1.gold.normalisation import contains_claim_string

    closure = Path(__file__).resolve().parents[1] / "experiments" / "GOLD-001" / \
        "GOLD-001-batch-002-closure.json"
    if not closure.exists():
        pytest.skip("batch 002 is not closed")
    report = json.loads(closure.read_text())
    verified = [r for r in batch2["records"]
                if r["verification_status"] == "human_verified"]
    with_critical = [r for r in verified if r.get("critical_strings")]

    assert report["claim_checkable"]["of_verified"] == len(verified)
    assert report["claim_checkable"]["with_critical_strings"] == len(with_critical)
    # And the records back the number up, string by string.
    for record in with_critical:
        for string in record["critical_strings"]:
            assert contains_claim_string(record["evidence_text"], string)


# -- batch 001 v2 scope repairs applied --------------------------------------

def test_the_approved_scope_repairs_are_in_v2_and_not_in_v1(overlay, batch):
    repairs = overlay["scope_repairs"]
    assert set(repairs) == {"GOLD-B001-13", "GOLD-B001-17"}
    v1 = {r["candidate_id"]: r for r in batch["records"]}
    for candidate_id, repair in repairs.items():
        # v1 keeps the pre-repair anchor, hash and absence of critical strings.
        assert v1[candidate_id]["char_start"] == repair["v1_span"][0]
        assert v1[candidate_id]["evidence_hash"] == repair["v1_evidence_hash"]
        assert not v1[candidate_id].get("critical_strings")
        # v2 grew the anchor outward and both approvals are recorded.
        assert repair["v2_span"][0] <= repair["v1_span"][0]
        assert repair["v2_span"][1] >= repair["v1_span"][1]
        assert repair["characters_added"] > 0
        assert repair["v1_approval"]["decision"] == "APPROVE"
        assert repair["v2_approval"]["decision"] == "APPROVE"
        assert repair["v2_approval"]["reviewer"] == "project_owner"
        assert repair["v2_evidence_hash"] != repair["v1_evidence_hash"]


def test_a_scope_repair_whose_hash_does_not_match_the_approval_is_refused():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_build_batch_v2_overlay",
        Path(__file__).resolve().parents[1] / "scripts" / "build_batch_v2_overlay.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    import hashlib
    text = "Scope sentence here. The fact under test is stated plainly."
    old_start = text.index("The fact")
    v1 = {
        "candidate_id": "X", "char_start": old_start, "char_end": len(text),
        "evidence_text": text[old_start:],
        "evidence_hash": hashlib.sha256(text[old_start:].encode()).hexdigest(),
        "proposed_question": "q?", "proposed_answer": "a",
        "proposed_atomic_claims": ["c"], "section_path": ["S"], "provider": "anthropic",
        "document_title": "D", "source_url": "u", "captured_at": "t",
        "verification_status": "human_verified", "human_verified": True,
        "version_id": "v", "proposed_category": "exact_lookup",
    }
    approval = {
        "option": "A", "kind": "evidence_boundary_expansion",
        "char_start": 0, "char_end": len(text),
        "expected_hash_prefix": "0" * 16,  # the owner approved a different span
        "atomic_claims": ["c"], "critical_strings": ["Scope sentence"], "reason": "r",
    }
    with pytest.raises(SystemExit) as excinfo:
        mod.build_scope_repair(v1, approval, text, "now")
    assert "approved a different span" in str(excinfo.value)


# -- project-wide eligibility ------------------------------------------------

def test_the_eligibility_status_counts_match_the_records():
    status_path = Path(__file__).resolve().parents[1] / "experiments" / "GOLD-001" / \
        "GOLD-001-eligibility-status.json"
    if not status_path.exists():
        pytest.skip("the status report has not been generated")
    status = json.loads(status_path.read_text())
    combined = status["combined"]
    for key in ("candidates", "human_verified", "human_rejected", "holdout_eligible"):
        assert combined[key] == sum(b[key] for b in status["batches"]), key
    # A status report may never announce a frozen holdout on its own.
    assert status["holdout_frozen"] is False
    assert status["retrieval_was_not_run"] is True
    assert status["systems_executed"] == []


# -- batch 003 miner ---------------------------------------------------------

BATCH_003 = Path(__file__).resolve().parents[1] / "evals" / "review" / \
    "gold_review_batch_003.json"


@pytest.fixture
def batch3():
    if not BATCH_003.exists():
        pytest.skip("batch 003 has not been generated")
    return json.loads(BATCH_003.read_text())


def _v3():
    from rag_v1.gold import mining_v3

    return mining_v3


def _doc(text: str, provider: str = "anthropic") -> dict:
    return {"text": text, "provider": provider, "title": "Doc", "version_id": "ver_x",
            "url": "https://example.invalid", "captured_at": "2026-08-01",
            "sections": []}


def test_batch_003_ships_complete_and_unverified(batch3):
    from rag_v1.gold.normalisation import contains_claim_string

    assert batch3["retrieval_was_not_run"] is True
    assert batch3["systems_executed"] == []
    for record in batch3["records"]:
        # The status moves through the lifecycle; the invariant that does not move is
        # that gold requires an APPROVE a person recorded.
        approvals = [h["decision"] for h in record.get("human_decision_history", [])]
        gold = record["verification_status"] == "human_verified"
        assert gold == (approvals[-1:] == ["APPROVE"]), record["candidate_id"]
        assert record.get("human_verified", False) == gold
        assert record["claude_proposed"] is True
        assert record["retrieval_was_not_run"] is True
        assert record["proposed_question"] and record["proposed_answer"]
        assert record["proposed_atomic_claims"] and record["critical_strings"]
        assert "[REVIEWER TO WRITE]" not in record["proposed_question"]
        spans = record.get("expected_evidence") or [record]
        combined = " \n".join(s["evidence_text"] for s in spans)
        for string in record["critical_strings"]:
            assert contains_claim_string(combined, string), (
                record["candidate_id"], string)


def test_batch_003_evidence_hashes_and_lengths_are_honest(batch3):
    import hashlib

    for record in batch3["records"]:
        for span in record.get("expected_evidence") or [record]:
            assert hashlib.sha256(
                span["evidence_text"].encode()).hexdigest() == span["evidence_hash"]
            assert span["evidence_char_length"] == len(span["evidence_text"])
            assert span["char_end"] - span["char_start"] == len(span["evidence_text"])
        assert record["evidence_char_length"] <= _v3().EVIDENCE_HARD_CAP


def test_batch_003_never_reuses_an_earlier_question_or_span(batch3):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_export_batch_003",
        Path(__file__).resolve().parents[1] / "scripts" / "export_batch_003.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    questions, spans, _ = mod.prior_material()
    seen_questions, seen_spans = set(), set()
    for record in batch3["records"]:
        key = mod.normalise_question(record["proposed_question"])
        span = tuple(sorted(
            (s["version_id"], s["char_start"], s["char_end"])
            for s in (record.get("expected_evidence") or [record])))
        assert key not in questions, record["candidate_id"]
        assert span not in spans, record["candidate_id"]
        assert key not in seen_questions and span not in seen_spans
        seen_questions.add(key)
        seen_spans.add(span)


def test_batch_003_multi_span_cases_carry_independently_anchored_spans(batch3):
    multi = [r for r in batch3["records"]
             if len(r.get("expected_evidence") or [1]) > 1]
    assert multi, "the batch contains multi-span cases"
    for record in multi:
        spans = record["expected_evidence"]
        assert len(spans) >= 2
        # Distinct spans, so partial retrieval cannot earn full credit.
        assert len({(s["version_id"], s["char_start"], s["char_end"])
                    for s in spans}) == len(spans)
        assert len(record["proposed_atomic_claims"]) >= 2
        assert record["proposed_question"].count("?") == 1


def test_batch_003_reports_the_composition_it_actually_has(batch3):
    from collections import Counter

    assert batch3["by_provider"] == dict(
        Counter(r["provider"] for r in batch3["records"]))
    assert batch3["by_category"] == dict(
        Counter(r["proposed_category"] for r in batch3["records"]))
    if "by_reasoning_type" in batch3:
        assert batch3["by_reasoning_type"] == dict(
            Counter(r["reasoning_type"] for r in batch3["records"]))
        assert batch3["by_evidence_shape"] == dict(
            Counter(r["evidence_shape"] for r in batch3["records"]))
        assert batch3["precheck_holdout_ready"] == sum(
            1 for r in batch3["records"] if r["precheck_holdout_ready"])
    assert batch3["unique_documents"] == len(
        {r["document_title"] for r in batch3["records"]})
    assert batch3["candidates"] == len(batch3["records"])
    lengths = [r["evidence_char_length"] for r in batch3["records"]]
    assert batch3["evidence_length"]["max"] == max(lengths)


# -- the batch-001/002 lessons, still enforced -------------------------------

def test_v3_drops_a_span_that_cannot_resolve_its_own_reference():
    """Batch 001's D1. The antecedent is absent, so the candidate must not ship."""
    text = ("If true, the API returns a 400 `invalid_request_error` for the request "
            "and stops processing it immediately.")
    assert _v3().mine_prose(_doc(text)) == []


def test_v3_keeps_a_span_that_carries_its_own_condition():
    text = ("If the `stream` parameter is omitted, the API returns a 400 "
            "`invalid_request_error` naming the missing field.")
    mined = _v3().mine_prose(_doc(text))
    assert mined, "a self-contained conditional should mine"
    assert "stream" in mined[0]["proposed_question"]
    assert mined[0]["proposed_category"] == "error_behavior"


def test_v3_refuses_normative_claims_from_example_code():
    """Batch 001's D3, and the EXP-014R failure before it."""
    text = ('Some prose about tool configuration that runs long enough to mine.\n\n'
            '```json\n{\n  "required": ["location"],\n'
            '  "tool_choice": {"type": "any"}\n}\n```\n')
    assert _v3().mine_prose(_doc(text)) == []


def test_v3_asks_a_row_about_what_the_row_says_not_what_a_header_means():
    """Batch 002's header dependency: a bare Yes/No answers nothing on its own."""
    text = ("| name | required | description |\n| --- | --- | --- |\n"
            "| `retry_budget` | yes | Controls how many times a failed call is retried. |\n")
    mined = _v3().mine_row_facts(_doc(text))
    assert mined
    question = mined[0]["proposed_question"]
    assert "required" not in question.lower()
    assert "retry_budget" in question
    # The answer is stated inside the row, so the anchor supports it alone.
    assert "retried" in mined[0]["proposed_answer"]


def test_v3_will_not_ask_about_a_generic_identifier_it_cannot_scope():
    """"What is the `path` option?" has a dozen answers in this corpus."""
    generic = "-   `path`: The path to the file or directory to view now.\n"
    specific = "-   `path`: The path passed to the `TextEditorTool` constructor now.\n"
    assert _v3().mine_definition_bullets(_doc(generic)) == []
    assert _v3().mine_definition_bullets(_doc(specific))


def test_v3_rejects_a_value_literal_mistaken_for_a_subject():
    text = ("Setting `audio.turn_detection` to `None` disables automatic turn "
            "detection for the session entirely.")
    for candidate in _v3().mine_prose(_doc(text)):
        assert "`None`" not in candidate["proposed_question"]


def test_v3_enforces_the_evidence_size_budget():
    v3 = _v3()
    assert v3.EVIDENCE_SOFT_CAP < v3.EVIDENCE_HARD_CAP
    long_condition = "the request body contains a field that is not recognised, " * 30
    text = f"If {long_condition}the API returns a 400 error."
    assert _v3().mine_prose(_doc(text)) == []


def test_v3_precheck_names_what_would_block_eligibility():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_export_batch_003",
        Path(__file__).resolve().parents[1] / "scripts" / "export_batch_003.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    import hashlib
    evidence = "The `limit` parameter caps results at 100 per page."
    good = {
        "version_id": "v", "char_start": 0, "char_end": len(evidence),
        "evidence_text": evidence,
        "evidence_hash": hashlib.sha256(evidence.encode()).hexdigest(),
        "evidence_char_length": len(evidence),
        "proposed_atomic_claims": ["`limit` caps results at 100 per page."],
        "critical_strings": ["`limit`", "100 per page"],
        "retrieval_was_not_run": True,
    }
    assert mod.precheck(good) == []
    assert any("critical strings outside" in f
               for f in mod.precheck({**good, "critical_strings": ["not present"]}))
    assert any("no atomic claims" in f
               for f in mod.precheck({**good, "proposed_atomic_claims": []}))
    assert any("retrieval leakage" in f
               for f in mod.precheck({**good, "retrieval_was_not_run": False}))
    assert any("hash does not match" in f
               for f in mod.precheck({**good, "evidence_hash": "0" * 64}))


def test_the_frozen_systems_are_untouched_by_batch_003():
    from rag_v1.systems import FROZEN_HASHES

    assert FROZEN_HASHES["SYSTEM-A-GLOBAL"] == (
        "9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38")
    assert FROZEN_HASHES["SYSTEM-B-DOC-C"] == (
        "304c350940b83733df6043ae3a8abdcbcde33d16950730127aa9f1f39494388b")


# -- batch 003 independent review --------------------------------------------

def _apply3():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_apply_batch_003_review",
        Path(__file__).resolve().parents[1] / "scripts" / "apply_batch_003_review.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _export3():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_export_batch_003",
        Path(__file__).resolve().parents[1] / "scripts" / "export_batch_003.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _reviewed_case(**overrides):
    import hashlib

    evidence = "The `limit` parameter caps results at 100 per page."
    case = {
        "candidate_id": "X", "evidence_kind": "normative_statement",
        "evidence_text": evidence, "evidence_char_length": len(evidence),
        "evidence_hash": hashlib.sha256(evidence.encode()).hexdigest(),
        "char_start": 0, "char_end": len(evidence), "version_id": "v",
        "section_path": ["S"],
        "proposed_atomic_claims": ["`limit` caps results at 100 per page."],
        "critical_strings": ["`limit`", "100 per page"],
        "retrieval_was_not_run": True,
    }
    case.update(overrides)
    return case


def test_an_unresolved_anaphora_blocks_the_precheck():
    """The contradiction the report erratum records: 20/20 ready with 1 anaphoric span."""
    import hashlib

    mod = _apply3()
    assert mod.audit(_reviewed_case())["failures"] == []

    evidence = "If true, the API returns a 400 error and stops processing the request."
    blocked = _reviewed_case(
        evidence_text=evidence, evidence_char_length=len(evidence),
        evidence_hash=hashlib.sha256(evidence.encode()).hexdigest(),
        proposed_atomic_claims=["The API returns a 400 error."],
        critical_strings=["400 error"])
    failures = mod.audit(blocked)["failures"]
    assert any("unresolved anaphora" in f for f in failures)


def test_the_anaphora_check_covers_every_evidence_kind():
    """An exemption by evidence kind would quietly weaken the gate for later batches."""
    import inspect

    source = inspect.getsource(_apply3().audit)
    assert "parameter_table_row" not in source
    assert "definition_bullet" not in source


def test_multi_span_is_not_multi_hop(batch3):
    multi_span = [r for r in batch3["records"]
                  if r.get("evidence_shape") == "multi_span"]
    assert multi_span
    for record in multi_span:
        assert record["reasoning_type"] != "genuine_multi_hop", record["candidate_id"]
        assert record["requires_all_evidence"] is True
    # The four the generator mislabelled carry the correction on the record itself, so
    # a later reader cannot mistake a multi-span retrieval test for multi-hop reasoning.
    reclassified = [r for r in batch3["records"] if r.get("not_genuine_multi_hop")]
    assert {r["candidate_id"] for r in reclassified} == {
        "GOLD-B003-12", "GOLD-B003-18", "GOLD-B003-19", "GOLD-B003-20"}
    assert batch3["genuine_multi_hop"] == 0
    # The shortfall against the 3–4 target is recorded, not quietly refilled.
    assert batch3["by_reasoning_type"].get("genuine_multi_hop", 0) == 0


def test_reasoning_type_and_evidence_shape_are_independent_dimensions(batch3):
    mod = _apply3()
    shapes = {r["evidence_shape"] for r in batch3["records"]}
    reasonings = {r["reasoning_type"] for r in batch3["records"]}
    assert shapes <= set(mod.EVIDENCE_SHAPES)
    assert reasonings <= set(mod.REASONING_TYPES)
    # Both single- and multi-span cases exist under the same reasoning type, which is
    # what makes the two dimensions independent rather than one relabelled.
    lookups = [r for r in batch3["records"] if r["reasoning_type"] == "exact_lookup"]
    assert {r["evidence_shape"] for r in lookups} == {"single_span", "multi_span"}
    assert "multi_hop" not in mod.EVIDENCE_SHAPES


def test_model_scope_is_inside_the_anchor_where_the_claim_asserts_it(batch3):
    """B003-06 and B003-10: a claim naming a model needs the anchor to name it too."""
    from rag_v1.gold.normalisation import contains_claim_string

    for candidate_id in ("GOLD-B003-06", "GOLD-B003-10", "GOLD-B003-11"):
        record = next(r for r in batch3["records"]
                      if r["candidate_id"] == candidate_id)
        combined = " \n".join(s["evidence_text"]
                              for s in (record.get("expected_evidence") or [record]))
        for string in record["critical_strings"]:
            assert contains_claim_string(combined, string), (candidate_id, string)


def test_b003_11_says_what_the_source_says():
    """The worst defect in batch 003: "Claude Opus 4" for "Claude Opus 4.7 or later"."""
    from rag_v1.gold.mining_v3 import _p_lifecycle

    sentence = ('`thinking: {type: "enabled"}` is no longer supported on Claude Opus '
                "4.7 or later models and returns a 400 error.")
    built = _p_lifecycle(sentence)
    assert "Claude Opus 4.7 or later models" in built[2]
    assert not built[2].endswith("Claude Opus 4.")


def test_conditional_claims_keep_their_condition(batch3):
    for candidate_id, condition in (("GOLD-B003-13", "If both are provided"),
                                    ("GOLD-B003-14", "Without explicit authentication")):
        record = next(r for r in batch3["records"]
                      if r["candidate_id"] == candidate_id)
        claims = " ".join(record["proposed_atomic_claims"])
        assert condition.lower() in claims.lower(), candidate_id
        assert condition in record["critical_strings"]


def test_event_field_cases_name_their_event_type(batch3):
    for candidate_id, event in (("GOLD-B003-16", "ChunkEvent"),
                                ("GOLD-B003-17", "ContentDeltaEvent")):
        record = next(r for r in batch3["records"]
                      if r["candidate_id"] == candidate_id)
        assert event in record["proposed_question"]
        assert event in record["evidence_text"], candidate_id
    # `parsed` means something different on ContentDoneEvent; the anchor must not
    # silently include it as if it were the same field.
    seventeen = next(r for r in batch3["records"]
                     if r["candidate_id"] == "GOLD-B003-17")
    assert "ContentDoneEvent" not in seventeen["evidence_text"]


def test_batch_003_review_preserves_every_original_proposal(batch3):
    revised = [r for r in batch3["records"] if r.get("revisions")]
    assert revised
    for record in revised:
        for revision in record["revisions"]:
            assert revision["from"] != revision["to"]
            assert revision["author"] and revision["reason"]
        for anchor in record.get("anchor_revisions", []):
            assert anchor["old_spans"] and anchor["new_spans"]
            assert anchor["old_spans"] != anchor["new_spans"]


def test_a_self_contradicting_report_is_refused():
    mod = _export3()
    consistent = {
        "total_candidates": 20, "precheck_holdout_ready": 19,
        "complete_question_answer_claims": 20, "needs_human_interpretation": 4,
        "comparison": {"batches": [{"batch": "003",
                                    "complete_question_answer_claims": 20,
                                    "needs_human_interpretation": 4,
                                    "anaphoric_spans": 1}]},
    }
    mod.check_report_consistency(consistent)

    # The exact shape the original batch-003 report shipped with.
    with pytest.raises(SystemExit) as excinfo:
        mod.check_report_consistency({**consistent, "precheck_holdout_ready": 20})
    assert "must block the precheck" in str(excinfo.value)

    with pytest.raises(SystemExit):
        mod.check_report_consistency({
            **consistent, "complete_question_answer_claims": 16})


def test_the_erratum_preserves_the_original_report():
    root = Path(__file__).resolve().parents[1] / "experiments" / "GOLD-001"
    original = root / "GOLD-001-batch-003-generation-report-original.json"
    erratum = root / "GOLD-001-batch-003-report-erratum.json"
    if not erratum.exists():
        pytest.skip("erratum not written")
    assert original.exists(), "the original report must be kept as historical output"
    body = json.loads(erratum.read_text())
    assert body["candidate_records_affected"] is False
    assert {e["id"] for e in body["errata"]} == {"E1", "E2"}
    # The original still carries the numbers the erratum corrects.
    assert json.loads(original.read_text())["precheck_holdout_ready"] == 20


def test_batch_003_still_asserts_no_retrieval_and_frozen_systems(batch3):
    from rag_v1.systems import FROZEN_HASHES

    assert batch3["retrieval_was_not_run"] is True
    assert batch3["systems_executed"] == []
    for record in batch3["records"]:
        assert record["retrieval_was_not_run"] is True
        assert record.get("retrieval_rank") is None
    assert FROZEN_HASHES["SYSTEM-A-GLOBAL"].startswith("9afcb5b7c58ebacf")
    assert FROZEN_HASHES["SYSTEM-B-DOC-C"].startswith("304c350940b83733")


# -- critical vs noncritical anaphora ----------------------------------------
#
# The detector is deliberately conservative and has flagged phrases that are not
# anaphors at all. Classifying its findings is only safe while the conservative answer
# stays visible, so nothing here deletes a finding — it decides whether the finding is
# load-bearing, and a noncritical one still blocks until a person accepts it.

def _anaphora():
    from rag_v1.gold import anaphora

    return anaphora


def test_A_an_unresolved_condition_the_claim_needs_stays_blocking():
    mod = _anaphora()
    candidate = {
        "proposed_question": "What happens if the guardrail's tripwire is true?",
        "proposed_answer": "The API returns a 400 error.",
        "proposed_atomic_claims": ["If the tripwire is true, the API returns a 400 error."],
        "critical_strings": ["400 error"],
    }
    verdict = mod.evaluate_span("If true, the API returns a 400 error.", candidate)
    assert verdict["status"] == mod.CRITICAL
    assert verdict["blocking"] is True


def test_B_an_unresolved_model_group_the_claim_needs_stays_blocking():
    mod = _anaphora()
    candidate = {
        "proposed_question": "What happens on these models?",
        "proposed_answer": "They return a 400 error.",
        "proposed_atomic_claims": ["These models return a 400 error."],
        "critical_strings": ["400 error"],
    }
    verdict = mod.evaluate_span("These models return a 400 error.", candidate)
    assert verdict["status"] == mod.CRITICAL
    assert verdict["blocking"] is True


def test_C_an_incidental_phrase_is_noncritical_only_when_nothing_scored_needs_it():
    mod = _anaphora()
    span = ("The executor model (the top-level `model` field) and the advisor model "
            "(the `model` field inside the tool definition) must form a valid pair.")

    scoped_away = {
        "proposed_question": ("What happens when the executor model and advisor model "
                              "do not form a valid pair?"),
        "proposed_answer": "The API returns a `400 invalid_request_error`.",
        "proposed_atomic_claims": [
            "The executor model and advisor model must form a valid pair."],
        "critical_strings": ["executor model", "advisor model", "must form a valid pair"],
    }
    assert mod.classify(span, scoped_away)["status"] == mod.NONCRITICAL

    # The same span, with a question that does depend on which tool: critical again.
    depends = {**scoped_away,
               "proposed_question": "Which tool definition holds the advisor `model`?",
               "critical_strings": ["tool definition"]}
    assert mod.classify(span, depends)["status"] == mod.CRITICAL


def test_D_a_noncritical_finding_blocks_until_a_named_human_accepts_it():
    mod = _anaphora()
    span = ("The executor model (the top-level `model` field) and the advisor model "
            "(the `model` field inside the tool definition) must form a valid pair.")
    base = {
        "proposed_question": ("What happens when the executor model and advisor model "
                              "do not form a valid pair?"),
        "proposed_answer": "The API returns a `400 invalid_request_error`.",
        "proposed_atomic_claims": [
            "The executor model and advisor model must form a valid pair."],
        "critical_strings": ["executor model", "advisor model"],
    }
    assert mod.evaluate_span(span, base)["blocking"] is True

    with_owner = mod.evaluate_span(
        span, {**base, "human_anaphora_override": True,
               "override_reviewer": "project_owner"})
    assert with_owner["blocking"] is False
    assert with_owner["status"] == mod.NONCRITICAL, "the finding is not erased"
    assert with_owner["finding"], "the original detector text is retained"

    # A model cannot accept its own finding.
    by_model = mod.evaluate_span(
        span, {**base, "human_anaphora_override": True, "override_reviewer": "claude"})
    assert by_model["blocking"] is True
    assert "must name a human reviewer" in by_model["override_refused"]


def test_D2_a_critical_finding_cannot_be_overridden_at_all():
    mod = _anaphora()
    candidate = {
        "proposed_atomic_claims": ["These models return a 400 error."],
        "critical_strings": ["400 error"],
        "human_anaphora_override": True, "override_reviewer": "project_owner",
    }
    verdict = mod.evaluate_span("These models return a 400 error.", candidate)
    assert verdict["blocking"] is True
    assert "cannot be overridden" in verdict["override_refused"]


def test_E_the_raw_evidence_is_never_edited_to_silence_the_detector(batch3):
    """B003-04 was repaired by rewriting the question, not by touching the source."""
    import hashlib

    record = next(r for r in batch3["records"]
                  if r["candidate_id"] == "GOLD-B003-04")
    spans = record["expected_evidence"]
    assert len(spans) == 2
    for span in spans:
        assert hashlib.sha256(
            span["evidence_text"].encode()).hexdigest() == span["evidence_hash"]
    # The phrase the detector objected to is still in the evidence, verbatim.
    assert "the tool definition" in spans[0]["evidence_text"]
    assert record["anaphora_status"] == "NONCRITICAL_ANAPHORA"
    assert record["anaphora_finding"]["finding"], "the finding is recorded, not erased"
    # No revision ever touched an evidence field.
    for revision in record["revisions"]:
        assert revision["field"] not in {"evidence_text", "evidence_hash",
                                         "expected_evidence", "char_start", "char_end"}


def test_b003_04_kept_everything_the_repair_and_approval_depend_on(batch3):
    record = next(r for r in batch3["records"]
                  if r["candidate_id"] == "GOLD-B003-04")
    # NEEDS_EDIT then APPROVE: both decisions survive, in order.
    decisions = [h["decision"] for h in record["human_decision_history"]]
    assert decisions == ["NEEDS_EDIT", "APPROVE"]
    gold = record["verification_status"] == "human_verified"
    assert gold == (decisions[-1] == "APPROVE")
    assert record["human_verified"] is gold
    assert record["reasoning_type"] == "error_behavior"
    assert record["evidence_shape"] == "multi_span"
    assert record["requires_all_evidence"] is True
    assert "advisor tool" not in record["proposed_question"]
    assert record["precheck_holdout_ready"] is True
    assert record["human_anaphora_override"] is True
    assert record["override_reviewer"] == "project_owner"


def test_batch_003_after_the_owner_decisions(batch3):
    from collections import Counter

    statuses = Counter(r["verification_status"] for r in batch3["records"])
    assert statuses["human_verified"] == 20
    assert statuses.get("needs_human_review", 0) == 0
    assert statuses.get("human_rejected", 0) == 0
    assert batch3["genuine_multi_hop"] == 0, "the corrected finding is preserved"
    for record in batch3["records"]:
        assert record["retrieval_was_not_run"] is True
        if record["verification_status"] == "human_verified":
            history = record["human_decision_history"][-1]
            assert history["decision"] == "APPROVE"
            assert history["approved_evidence_hash"] == record["evidence_hash"]


# -- state counts must come from the records ---------------------------------
#
# The first B003-04 review artifact printed `needs_human_review = 0` while its own prose
# said the case was awaiting review. The cause was neither display nor prose: a script
# moved a record from `needs_edit` to `needs_human_review` and refreshed
# `precheck_holdout_ready` but not `status_counts`, so the batch header claimed a status
# nothing had. The lesson is that a report must derive its numbers from the records.

def test_a_candidate_pending_final_review_is_counted_as_needing_review():
    import importlib.util
    from collections import Counter

    spec = importlib.util.spec_from_file_location(
        "_export_b003_04_review",
        Path(__file__).resolve().parents[1] / "scripts" / "export_b003_04_review.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # A batch whose stored header is stale in exactly the way the artifact was.
    batch = {
        "status_counts": {"human_verified": 19, "needs_edit": 1},
        "records": [{"verification_status": "human_verified"} for _ in range(19)]
                   + [{"verification_status": "needs_human_review"}],
    }
    counted = mod.status_counts(batch)
    assert counted["needs_human_review"] == 1, "the pending case must be counted"
    assert counted != batch["status_counts"], "and the stale header must not be trusted"
    assert counted == dict(Counter(r["verification_status"] for r in batch["records"]))


def test_every_batch_header_count_agrees_with_its_records(batch, batch2, batch3):
    """No batch may carry an aggregate its own records contradict."""
    from collections import Counter

    for name, payload in (("001", batch), ("002", batch2), ("003", batch3)):
        recomputed = dict(Counter(r["verification_status"] for r in payload["records"]))
        assert payload["status_counts"] == recomputed, name
        if "precheck_holdout_ready" in payload:
            assert payload["precheck_holdout_ready"] == sum(
                1 for r in payload["records"] if r["precheck_holdout_ready"]), name


def test_the_original_review_artifact_is_preserved_with_its_error():
    original = (Path(__file__).resolve().parents[1] / "evals" / "review"
                / "gold_batch_003_final_case_review-original.md")
    if not original.exists():
        pytest.skip("the original artifact is not present")
    body = original.read_text()
    # Kept as shipped, wrong count and all — the correction is recorded, not hidden.
    assert "| `needs_human_review` | 0 |" in body


def test_a_multi_span_case_is_claim_checked_at_all():
    """Checking only the first span skipped the gate entirely for multi-span cases."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_validate_golden",
        Path(__file__).resolve().parents[1] / "scripts" / "validate_golden.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    text = "First span says alpha. Filler in between. Second span says beta."
    sources = {"v": {"text": text, "provider": "anthropic"}}
    case = {
        "case_id": "M", "question": "What do the two spans say together?",
        "category": "multi_hop", "split": "validation", "provider": "anthropic",
        "verification": "human_verified", "human_verified": True,
        "expected_abstain": False,
        "expected_claims": [{"text": "alpha", "critical": True},
                            {"text": "beta", "critical": True}],
        "expected_evidence": [
            {"version_id": "v", "char_start": 0, "char_end": 21, "section_path": ["S"]},
            {"version_id": "v", "char_start": 41, "char_end": 64, "section_path": ["S"]},
        ],
    }
    assert mod.validate([case], sources, require_human=set()) == []

    # A claim in neither span must now fail rather than pass unchecked.
    unsupported = {**case, "expected_claims": [{"text": "gamma", "critical": True}]}
    failures = mod.validate([unsupported], sources, require_human=set())
    assert any(f["check"] == "claim_supported_by_evidence" for f in failures)
