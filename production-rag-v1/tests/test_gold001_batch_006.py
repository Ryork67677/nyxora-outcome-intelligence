"""GOLD-001 batch 006: what the generator produced, and what it refused to produce.

Batch 006 came back at nine against a target of twenty-eight. These tests exist to keep
that number honest in both directions — that nothing was padded in to reach a count, and
that nothing was dropped by a gate that is not doing real work. The gate counts are
asserted against the records, because a report that says a fix ran is worth nothing
next to a record that shows what it caught.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rag_v1.gold import relations, scoping
from rag_v1.gold.normalisation import contains_claim_string, has_markdown_link
from rag_v1.gold.questionform import OK
from rag_v1.gold.questionform import evaluate as question_form

BATCH = Path("evals/review/gold_review_batch_006.json")
REPORT = Path("experiments/GOLD-001/GOLD-001-batch-006-generation-report.json")
COVERAGE = Path(
    "experiments/GOLD-001/GOLD-001-coverage-status-after-b006-generation.md")
AUDIT = Path("experiments/GOLD-001/GOLD-001-heading-parser-audit.json")
STATUS = Path("experiments/GOLD-001/GOLD-001-eligibility-status.json")
CLOSED = {
    1: "evals/review/gold_review_batch_001.json",
    2: "evals/review/gold_review_batch_002.json",
    3: "evals/review/gold_review_batch_003.json",
    4: "evals/review/gold_review_batch_004_final.json",
    5: "evals/review/gold_review_batch_005_final.json",
}
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


def evidence_of(record: dict) -> str:
    return " \n".join(s["evidence_text"] for s in record["expected_evidence"])


# ---------------------------------------------------------------- nothing is gold


def test_nothing_in_the_batch_claims_verification(batch):
    for record in batch["records"]:
        assert record["verification_status"] == "candidate_unverified"
        assert record["claude_proposed"] is True
        assert record["chatgpt_verified"] is None
        assert record["internal_semantic_review_status"] != "human_verified"


def test_the_self_review_is_labelled_as_authoring(batch):
    note = batch["internal_review"]["note"]
    assert "not independent verification" in note
    assert "not human approval" in note


def test_precheck_is_labelled_structural_only(batch):
    assert "STRUCTURAL ONLY" in batch["precheck_means"]
    for word in ("semantic correctness", "human approval", "holdout eligibility"):
        assert word in batch["precheck_means"]


# ------------------------------------------------- §27: every field on every record


def test_every_record_carries_both_triples(batch):
    for record in batch["records"]:
        for field in ("source_subject", "source_relation", "source_object",
                      "question_subject", "question_relation"):
            assert record.get(field), f"{record['candidate_id']} has no {field}"


def test_every_record_carries_its_provenance(batch):
    for record in batch["records"]:
        for field in ("provider", "document_title", "version_id", "source_url",
                      "captured_at", "reasoning_type", "evidence_shape",
                      "requires_all_evidence", "question", "answer", "atomic_claims",
                      "generator_confidence", "precheck_holdout_ready"):
            assert field in record, f"{record['candidate_id']} has no {field}"


def test_every_span_hashes_to_its_own_text(batch):
    for record in batch["records"]:
        for span in record["expected_evidence"]:
            digest = hashlib.sha256(span["evidence_text"].encode()).hexdigest()
            assert span["evidence_hash"] == digest, record["candidate_id"]
            assert span["evidence_char_length"] == (
                span["char_end"] - span["char_start"])


def test_critical_strings_are_inside_their_own_span(batch):
    for record in batch["records"]:
        for span in record["expected_evidence"]:
            assert span["critical_strings"], record["candidate_id"]
            for value in span["critical_strings"]:
                assert contains_claim_string(span["evidence_text"], value), (
                    f"{record['candidate_id']}: {value!r} is not in "
                    f"{span['evidence_id']}")


# --------------------------------------------------- the four fixes, on the output


def test_no_exported_span_is_a_bare_definition_bullet(batch):
    """§Fix A, checked on the batch rather than on the module."""
    for record in batch["records"]:
        verdict = scoping.evaluate(record)
        assert verdict["status"] == scoping.SCOPED, (
            f"{record['candidate_id']}: {verdict['findings']}")


def test_the_scope_gate_actually_caught_something(batch):
    """A gate that never fires is indistinguishable from a gate that is not wired in."""
    assert batch["internal_review"]["gate_counts"].get("BARE_DEFINITION_SCOPE", 0) > 0


def test_no_markdown_link_survives_into_a_question_or_answer(batch):
    """§Fix B."""
    for record in batch["records"]:
        assert not has_markdown_link(record["question"]), record["candidate_id"]
        assert not has_markdown_link(record["answer"]), record["candidate_id"]


def test_section_path_is_marked_untrusted(batch):
    """§Fix C: the record says so, so a later reader cannot assume otherwise."""
    for record in batch["records"]:
        assert record["section_path_trusted_for_scope"] is False
    assert batch["heading_audit"].endswith("GOLD-001-heading-parser-audit.json")


def test_no_exported_claim_leans_on_a_prose_heading(batch):
    audit = load(AUDIT)
    prose = {e["heading"] for e in audit["examples"] if e["likely_prose"]}
    for record in batch["records"]:
        for span in record["expected_evidence"]:
            leaning = [p for p in span["section_path"] if p in prose]
            if not leaning:
                continue
            # Allowed only when the span carries its own scope, which is the rule.
            assert any(contains_claim_string(span["evidence_text"], s)
                       for s in span["critical_strings"]), record["candidate_id"]


def test_no_exported_question_reverses_its_source(batch):
    """§Fix D."""
    for record in batch["records"]:
        verdict = relations.evaluate(record)
        assert verdict["status"] != relations.REVERSED, (
            f"{record['candidate_id']}: {verdict['finding']}")
        assert verdict["status"] != relations.SUBJECT_MISMATCH, (
            f"{record['candidate_id']}: {verdict['finding']}")


def test_the_question_subject_appears_in_the_source_sentence(batch):
    """§14, stated as a property of the export rather than of the gate."""
    for record in batch["records"]:
        subject = relations.identifiers(record["question_subject"])
        sentence = relations.identifiers(record["source_sentence"] or "")
        if not subject:
            continue
        assert subject & sentence, (
            f"{record['candidate_id']}: the question's subject "
            f"{record['question_subject']!r} is not in the source sentence")


def test_question_form_matches_evidence_form(batch):
    """§15."""
    for record in batch["records"]:
        verdict = question_form(record["question"], evidence_of(record))
        assert verdict["status"] == OK, (
            f"{record['candidate_id']}: {verdict['finding']}")


# ------------------------------------------------------------- §7: no multi-hop search


def test_no_multi_hop_search_was_run(batch):
    search = batch["multi_hop_search"]
    assert search["ran"] is False
    assert "559" in search["reason"] and "dependency-first" in search["reason"]
    assert search["exported_chains"] == batch["genuine_multi_hop"]


def test_no_multi_span_case_was_relabelled_as_multi_hop(batch):
    for record in batch["records"]:
        if record["reasoning_type"] != "genuine_multi_hop":
            continue
        assert len(record["expected_evidence"]) >= 2
        assert record["multi_hop_composition_check"] == "PASS"


# ------------------------------------------------- the count, and how it was reached


def test_the_batch_is_not_padded_to_a_number(batch):
    """Every candidate cleared the precheck and the self-review. None was waved through."""
    for record in batch["records"]:
        assert record["precheck_holdout_ready"] is True, record["candidate_id"]
        assert record["precheck_failures"] == []
        assert record["internal_semantic_review_status"] in (
            "READY_FOR_INDEPENDENT_REVIEW", "NEEDS_INTERNAL_REPAIR")


def test_the_shortfall_is_recorded_not_hidden(batch):
    assert batch["candidates"] < batch["target_size"], (
        "this test encodes a shortfall the batch no longer has — update it")
    report = load(REPORT)
    assert report["candidates"] == batch["candidates"]
    text = Path(
        "experiments/GOLD-001/GOLD-001-batch-006-generation-report.md").read_text()
    assert f"The target was {batch['target_size']}" in text
    assert "not padded" in text


def test_every_drop_states_a_reason(batch):
    for entry in batch["internal_review"]["dropped"]:
        assert entry["findings"], entry["question"]
        assert entry["reasoning_type"]


def test_the_coverage_projection_does_not_claim_the_target(batch):
    if not COVERAGE.exists():
        pytest.skip("coverage status has not been generated")
    text = COVERAGE.read_text()
    status = load(STATUS)
    confirmed = status["combined"]["holdout_eligible"]
    best = confirmed + batch["candidates"]
    assert str(confirmed) in text
    if best < 100:
        assert "Neither crosses 100" in text, (
            "the projection must say plainly that this batch cannot reach the target")


def test_batch_006_is_not_counted_as_confirmed(batch):
    status = load(STATUS)
    assert all(b["batch"] != 6 for b in status["batches"])
    assert status["combined"]["human_verified"] == 82


# ---------------------------------------------------------------------- invariants


def test_no_evidence_is_reused_from_a_closed_batch(batch):
    spent: set[tuple] = set()
    texts: set[str] = set()
    for path in CLOSED.values():
        for record in load(Path(path))["records"]:
            for span in (record.get("expected_evidence") or [record]):
                if span.get("version_id") is None:
                    continue
                spent.add((span["version_id"], span["char_start"], span["char_end"]))
                texts.add(" ".join(span.get("evidence_text", "").split()))
    for record in batch["records"]:
        for span in record["expected_evidence"]:
            key = (span["version_id"], span["char_start"], span["char_end"])
            assert key not in spent, f"{record['candidate_id']} reuses a spent span"
            assert " ".join(span["evidence_text"].split()) not in texts, (
                f"{record['candidate_id']} reuses spent evidence text")


def test_closed_batches_are_untouched():
    for number, path in CLOSED.items():
        payload = load(Path(path))
        closure = load(Path(
            f"experiments/GOLD-001/GOLD-001-batch-{number:03d}-closure.json"))
        blob = json.dumps(sorted(payload["records"], key=lambda r: r["candidate_id"]),
                          sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        assert closure["closure_sha256"] == hashlib.sha256(
            blob.encode("utf-8")).hexdigest(), f"batch {number:03d} changed"


def test_retrieval_was_not_run(batch):
    assert batch["retrieval_was_not_run"] is True
    assert batch["systems_executed"] == []
    for record in batch["records"]:
        assert record["retrieval_was_not_run"] is True
        for leak in ("retrieval_rank", "retrieved_by", "bm25_score", "dense_score",
                     "reranker_score", "difficulty_from_retrieval"):
            assert leak not in record, f"{record['candidate_id']} carries {leak}"


def test_the_batch_records_the_frozen_hashes_it_checked(batch):
    from rag_v1.systems import FROZEN_HASHES

    assert batch["frozen_systems"] == FROZEN_SYSTEMS
    assert dict(FROZEN_HASHES) == FROZEN_SYSTEMS


def test_the_corpus_snapshot_did_not_change(batch):
    assert batch["corpus_snapshot"] == "snap_689e336380a054d8039dc35b2c09cd0a"
    for number, path in CLOSED.items():
        assert load(Path(path))["corpus_snapshot"] == batch["corpus_snapshot"], number


def test_report_agrees_with_the_batch(batch):
    report = load(REPORT)
    assert report["candidates"] == len(batch["records"])
    assert report["by_reasoning_type"] == batch["by_reasoning_type"]
    assert report["by_provider"] == batch["by_provider"]
    assert report["genuine_multi_hop"] == batch["genuine_multi_hop"]
    assert report["precheck_holdout_ready"] == batch["precheck_holdout_ready"]
    assert "records" not in report
