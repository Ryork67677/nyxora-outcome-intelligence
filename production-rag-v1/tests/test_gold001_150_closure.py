"""The 150-case admission: what it rests on, and what it must never quietly become.

Two HA packets exist in this project and they share the ``HA-nn`` namespace. Only one of
them is the packet of record. The invariants here are mostly about that: an approval must
bind to evidence, not to a label; the alternate packet must stay out; the count must be
derived; and the things 150 does *not* fix — the unrun pilot, the unreproduced corpus,
n=1 multi-hop — must still be on the record afterwards.

Nothing here runs retrieval or edits a closed batch.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rag_v1.gold import anaphora
from rag_v1.gold.eligibility import evaluate
from rag_v1.ids import stable_id

EXP = Path("experiments/GOLD-001")
STATUS = EXP / "GOLD-001-eligibility-status.json"
CLOSURE = EXP / "GOLD-001-150-case-closure.json"
ADMISSION = EXP / "GOLD-001-HA-admission.json"
DEVIATION = EXP / "GOLD-001-protocol-deviation-001.json"
LIMITATION = EXP / "GOLD-001-corpus-reproduction-limitation.json"
DISPOSITION = EXP / "GOLD-001-alternate-HA-packet-disposition.json"
HA_RECORDS = Path("evals/review/gold_review_HA01_HA60_final.json")
DECISIONS = Path("evals/review/human_decisions_HA01_HA60.json")

PACKET_SHA = "bf6190fc53ee4ada6c948093d30e8fa7feac3dbf3300918ec75886d2a5a8f786"
#: HA-47's admitted evidence, and the two pre-repair spans that are not it.
HA47_REPAIRED_SHA = "e894c94d831ccfd2678f4cd132b72b52e44770d07ebeaab6c51e96e0e312a203"
HA47_OLD_SHAS = {
    "5e36f5ff857cdcd795d4e8133de6072b5a8e7588be44fc21516e24a5e97f5b34",
    "f4d4ee514ca2285d8cc67313a02b7cb7382d11cc3cedfd998733884d98321387",
}


def load(path: Path) -> dict:
    if not path.exists():
        pytest.skip(f"{path} is not present")
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def ha_records() -> dict:
    payload = load(HA_RECORDS)
    return {r["candidate_id"]: r for r in payload["records"]}


# ------------------------------------------------------------ packet identity

def test_the_admitted_records_name_the_packet_of_record():
    payload = load(HA_RECORDS)

    assert payload["source_packet"] == "Production_RAG_v1_Full_150_Case_Review.pdf"
    assert payload["source_packet_sha256"] == PACKET_SHA


def test_every_admitted_record_carries_the_packet_it_came_from(ha_records):
    for candidate_id, record in ha_records.items():
        assert record["admitted_from"]["packet_sha256"] == PACKET_SHA, candidate_id
        assert "not the short HA label" in record["admitted_from"]["bound_by"]


def test_the_admitted_set_is_exactly_ha01_through_ha60(ha_records):
    assert sorted(ha_records) == sorted(f"HA-{i:02d}" for i in range(1, 61))


def test_the_alternate_64_case_packet_is_still_excluded():
    disposition = load(DISPOSITION)

    assert "NOT_ADMITTED" in disposition["status"]
    assert "NOT_THE_PACKET_OF_RECORD" in disposition["status"]
    assert "PRESERVED_FOR_AUDIT" in disposition["status"]


def test_the_alternate_packet_contributed_no_case():
    """Its records are unreviewed drafts; none of them may appear in the admitted set."""
    assert load(DISPOSITION)["records_are_unchanged"]["human_verified"] == 0
    assert "NOT_ADMITTED" in load(HA_RECORDS)["not_the_alternate_packet"]


# ------------------------------------------------- approval binds to evidence, not labels

def test_the_owner_decision_is_an_input_not_something_a_script_produced():
    decisions = load(DECISIONS)

    assert decisions["reviewer"] == "project_owner"
    assert decisions["packet_sha256"] == PACKET_SHA
    assert len(decisions["approved"]) == 60
    assert decisions["rejected"] == []


def test_approval_is_not_attributed_to_any_reviewer_model():
    decisions = load(DECISIONS)

    assert "approval is the project owner's" in decisions["attribution"]
    for name in ("Codex", "Grok", "ChatGPT"):
        assert name in decisions["attribution"]


def test_a_review_verdict_confers_no_approval(ha_records):
    for candidate_id, record in ha_records.items():
        assert record["chatgpt_review"]["confers_no_approval"] is True, candidate_id
        assert record["reviewer"] == "project_owner", candidate_id


def test_every_record_binds_by_evidence_identity(ha_records):
    """version_id must re-derive from provider, canonical url and content hash."""
    for candidate_id, record in ha_records.items():
        src_id = stable_id("src", record["provider"], record["source_url"], length=32)
        derived = stable_id("ver", src_id, record["content_hash"], length=32)

        assert derived == record["version_id"], candidate_id


def test_every_span_hash_recomputes_from_its_stored_text(ha_records):
    for candidate_id, record in ha_records.items():
        for span in record["expected_evidence"]:
            digest = hashlib.sha256(span["evidence_text"].encode()).hexdigest()

            assert digest == span["evidence_hash"], f"{candidate_id} {span['evidence_id']}"
            assert span["char_end"] - span["char_start"] == len(span["evidence_text"])


# ------------------------------------------------------------------ HA-15 and HA-47

def test_ha15_keeps_its_finding_and_carries_an_explicit_owner_override(ha_records):
    record = ha_records["HA-15"]

    assert record["anaphora_status"] == anaphora.NONCRITICAL
    assert record["anaphora_finding"], "the detector's finding must not be deleted"
    assert "the model" in record["anaphora_phrase"]
    assert record["human_anaphora_override"] is True
    assert record["override_reviewer"] == "project_owner"


def test_a_critical_anaphora_is_never_overridden(ha_records):
    """The override exists for a noncritical finding. A critical one blocks."""
    for candidate_id, record in ha_records.items():
        joined = " \n".join(s["evidence_text"] for s in record["expected_evidence"])

        assert anaphora.evaluate_span(joined, record)["status"] != anaphora.CRITICAL, (
            candidate_id)


def test_ha47_was_admitted_on_the_repaired_span(ha_records):
    spans = ha_records["HA-47"]["expected_evidence"]

    assert len(spans) == 1
    assert spans[0]["char_start"] == 4308
    assert spans[0]["char_end"] == 4916
    assert spans[0]["evidence_hash"] == HA47_REPAIRED_SHA
    assert spans[0]["evidence_char_length"] == 608


def test_the_pre_repair_ha47_evidence_is_not_the_admitted_evidence(ha_records):
    """The old spans survive in the revision history and nowhere else."""
    record = ha_records["HA-47"]
    admitted = {s["evidence_hash"] for s in record["expected_evidence"]}

    assert not (admitted & HA47_OLD_SHAS)
    revision = record["revisions"][0]
    assert {s["evidence_hash"] for s in revision["from"]} == HA47_OLD_SHAS
    assert revision["to"]["evidence_hash"] == HA47_REPAIRED_SHA


def test_the_ha47_repair_records_why_it_happened(ha_records):
    revision = ha_records["HA-47"]["revisions"][0]

    assert "EVIDENCE_BOUNDARY_COMPLETION" in revision["reason"]
    assert "CRITICAL_ANAPHORA_REPAIR" in revision["reason"]
    assert revision["revised_by"] == "project_owner"


def test_the_repaired_span_establishes_every_required_clause(ha_records):
    body = ha_records["HA-47"]["expected_evidence"][0]["evidence_text"]

    assert body.startswith("`input_type` describes")
    assert "It does not replace the next agent's main input" in body
    assert "it does not choose a different destination" in body
    assert "still transfers to the specific agent you wrapped" in body


def test_a_paragraph_break_is_recorded_and_does_not_block(ha_records):
    """Read from the predicate. Not a waiver — the condition simply does not exist."""
    from rag_v1.gold.eligibility import HOLDOUT_CONDITIONS
    record = ha_records["HA-47"]

    assert record["paragraph_break_present"] is True
    assert record["paragraph_break_eligibility_blocking"] is False
    assert not any("paragraph" in condition for condition in HOLDOUT_CONDITIONS)


# ------------------------------------------------------------ the count is derived

def test_every_admitted_record_passes_the_real_eligibility_predicate(ha_records):
    for candidate_id, record in ha_records.items():
        verdict = evaluate(record)

        assert verdict["holdout_eligible"], (candidate_id, verdict["failures"])


def test_the_final_count_is_derived_from_the_groups():
    status = load(STATUS)
    combined = status["combined"]

    for key in ("human_verified", "human_rejected", "holdout_eligible",
                "genuine_multi_hop"):
        assert combined[key] == sum(b[key] for b in status["batches"]), key


def test_the_closure_agrees_with_the_eligibility_status():
    closure, status = load(CLOSURE), load(STATUS)

    for key in ("human_verified", "holdout_eligible", "human_rejected",
                "genuine_multi_hop"):
        assert closure["counts"][key] == status["combined"][key], key


def test_the_set_reached_150_and_the_historical_rejections_are_unchanged():
    combined = load(STATUS)["combined"]

    assert combined["human_verified"] == 150
    assert combined["holdout_eligible"] == 150
    assert combined["human_rejected"] == 9
    assert combined["genuine_multi_hop"] == 1


def test_ninety_of_the_hundred_and_fifty_are_the_historical_cases():
    groups = {b["label"]: b for b in load(STATUS)["batches"]}
    historical = sum(v["holdout_eligible"] for k, v in groups.items()
                     if k != "HA-01–HA-60")

    assert historical == 90
    assert groups["HA-01–HA-60"]["holdout_eligible"] == 60


# ------------------------------------------------- what 150 does not fix, still recorded

def test_the_protocol_deviation_is_accepted_and_never_claims_the_pilot_ran():
    deviation = load(DEVIATION)

    assert deviation["disposition"] == "ACCEPTED_PROTOCOL_DEVIATION"
    assert "pilot remains unrun" in deviation["actual"]["the_claim_that_must_never_be_made"]
    assert any("never claim the preregistered pilot sequence was followed" in c
               for c in deviation["consequences"])


def test_every_mitigation_figure_carries_what_it_does_not_establish():
    for mitigation in load(DEVIATION)["mitigations_actually_performed"]:
        assert mitigation["limit"], mitigation["mitigation"]
        assert mitigation["verified_from"], mitigation["mitigation"]


def test_no_reviewer_is_recorded_as_having_admitted_anything():
    grok = next(m for m in load(DEVIATION)["mitigations_actually_performed"]
                if "Grok" in m["mitigation"])

    assert grok["explicitly_recorded"]["official_admissions"] == 0
    assert grok["explicitly_recorded"]["human_approval"] is False


def test_corpus_reproduction_still_blocks_retrieval():
    limitation = load(LIMITATION)

    assert limitation["CORPUS_REPRODUCTION_INCOMPLETE"] is True
    assert limitation["effect"] == "RETRIEVAL_BLOCKED"
    assert load(CLOSURE)["limitations"]["retrieval"] == "RETRIEVAL_BLOCKED"


def test_reaching_150_did_not_close_the_corpus_gate():
    limitation = load(LIMITATION)

    assert limitation["outstanding"]["anthropic_documents"] == 139
    assert limitation["corpus_snapshot_reproduced"] is False


def test_the_closure_leads_with_size_not_coverage():
    closure = load(CLOSURE)

    assert "not coverage" in closure["headline"]
    assert closure["counts"]["genuine_multi_hop"] == 1
    for key in ("provider_imbalance", "category_imbalance", "genuine_multi_hop",
                "protocol_deviation", "corpus_reproduction", "retrieval"):
        assert closure["limitations"][key], key


def test_cases_with_no_recorded_category_are_not_folded_into_one():
    coverage = load(CLOSURE)["coverage"]

    assert coverage["cases_with_no_recorded_reasoning_type"] > 0
    assert "None" not in coverage["reasoning_type"]


# --------------------------------------------------------------- retrieval and splits

def test_no_retrieval_was_run_and_no_system_executed():
    status, closure = load(STATUS), load(CLOSURE)

    assert status["retrieval_was_not_run"] is True
    assert status["systems_executed"] == []
    assert closure["retrieval_was_not_run"] is True
    assert closure["systems_executed"] == []
    assert load(ADMISSION)["retrieval_was_not_run"] is True


def test_the_holdout_is_not_frozen_and_says_why():
    status, closure = load(STATUS), load(CLOSURE)

    assert status["holdout_frozen"] is False
    assert closure["holdout_frozen"] is False
    assert closure["reason_not_frozen"] == status["reason_not_frozen"]


def test_the_reason_not_frozen_is_no_longer_the_stale_count_reason():
    """150 does support the split by size; the reason had to change with the count."""
    reason = load(STATUS)["reason_not_frozen"]

    assert "cannot support both" not in reason
    assert "split policy" in reason
