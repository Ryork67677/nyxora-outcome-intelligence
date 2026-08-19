"""GOLD-001 tests: the authoring workflow must not be able to manufacture gold."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag_v1.gold.mining import (
    Candidate,
    identifiers_in,
    mine_explicit_statements,
    mine_table_parameters,
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


def test_batch_declares_nothing_is_gold(batch):
    # The banner survives import: review changes the status, never the disclaimer.
    assert "nothing in this file is gold" in batch["verification_status"]
    assert batch["retrieval_was_not_run"] is True
    for record in batch["records"]:
        assert record["verification_status"] in PRE_HUMAN_STATUSES
        assert record.get("human_verified") is not True


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
    text = ("The `first_option` and `second_option` settings must be configured before "
            "the client starts, and each one is required for the handshake to complete. ")
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


# -- human review packet -----------------------------------------------------

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
        "candidate_id": "GOLD-B001-99", "document_title": "Doc",
        "section_path": ["A", "B"], "version_id": "ver_x",
        "char_start": 10, "char_end": 40, "evidence_kind": "explicit_exception",
        "generator_confidence": "medium", "context_before": "before",
        "context_after": "after", "evidence_text": "the anchored sentence",
        "proposed_question": "new question?", "proposed_answer": "new answer",
        "proposed_atomic_claims": ["a claim"],
        "verification_status": "needs_human_review",
        "verification": {"verdict": "FIX_REQUIRED", "evidence_boundary_complete": False,
                         "verification_notes": "anchor starts with a pronoun"},
        "revisions": [{"revision": 1, "field": "proposed_question",
                       "from": "[REVIEWER TO WRITE] …", "to": "new question?",
                       "author": "chatgpt", "timestamp": "t", "reason": "r"}],
    }
    record.update(overrides)
    return record


def test_packet_shows_the_generator_proposal_next_to_the_reviewer_edit():
    mod = _packet_module()
    rendered = mod.render(_reviewed_record(), "mandatory")
    # A reviewer who only sees the final text cannot tell that a model wrote it.
    assert "[REVIEWER TO WRITE]" in rendered
    assert "generator:" in rendered and "reviewer (chatgpt):" in rendered
    assert "the anchored sentence" in rendered
    assert "`evidence_boundary_complete`" in rendered


def test_packet_never_declares_a_case_verified():
    mod = _packet_module()
    rendered = mod.render(_reviewed_record(), "mandatory")
    assert "human_verified" not in rendered
    assert "APPROVE" in rendered
    assert "APPROVE" in mod.VALID_DECISIONS
    assert mod.DECISION_TEMPLATE["decision"] == "PENDING"


def test_packet_reports_anchor_disputes_as_rejected():
    mod = _packet_module()
    record = _reviewed_record(anchor_disputes=[{
        "field": "char_start", "reviewer_value": 999, "kept_value": 10,
        "author": "chatgpt", "timestamp": "t"}])
    rendered = mod.render(record, "mandatory")
    assert "was NOT applied" in rendered
    assert "char_start" in rendered
