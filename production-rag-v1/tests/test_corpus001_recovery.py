"""CORPUS-001: the snapshot arithmetic, and the things a partial corpus must never do.

The frozen snapshot id is content-derived, which is what makes recovery checkable at all:
a restored corpus proves its identity by hashing to the same value, not by carrying the
right label. These tests pin that construction — including the two parameters recovered
from ``experiments/EXP-007/results.json`` and confirmed by reproduction — and pin the
refusals: a partial corpus cannot clear the gate, a live page cannot stand in for a
historical capture, and reaching 150 GOLD cases proves nothing about the 202 documents.

Nothing here fetches, restores, or runs retrieval.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from rag_v1.config import settings
from rag_v1.ids import config_hash, stable_id
from rag_v1.parsing import PARSER_VERSION

EXP = Path("experiments/GOLD-001")
INVENTORY = EXP / "CORPUS-001-local-artifact-inventory.json"
MANIFEST = EXP / "CORPUS-001-expected-202-manifest.json"
LEDGER = EXP / "CORPUS-001-recovery-ledger.json"
UNBUILDABLE = EXP / "CORPUS-001-unbuildable-identity-analysis.json"
LIMITATION = EXP / "GOLD-001-corpus-reproduction-limitation.json"
STATUS = EXP / "GOLD-001-eligibility-status.json"
HOST_SEARCH = EXP / "CORPUS-001-host-search.json"
ANTHROPIC_IDS = EXP / "CORPUS-001-known-anthropic-id-search.json"
PLAN = EXP / "CORPUS-001-anthropic-recovery-plan.json"
CHUNKING = {"max_chunk_chars": settings.max_chunk_chars,
            "min_chunk_chars": settings.min_chunk_chars}

SNAPSHOT_ID = "snap_689e336380a054d8039dc35b2c09cd0a"
MANIFEST_HASH = "452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17"
SNAPSHOT_NAME = "v1-openai-anthropic"
EXPECTED_DOCUMENTS = 202

#: Statuses the ledger may use. Anything else is a vague "done" by another name.
ALLOWED_STATUSES = {"EXACT_MATCH", "PARTIAL_METADATA", "HASH_MISMATCH", "MISSING_SOURCE",
                    "EXPECTED_HASH_UNKNOWN", "BLOCKED", "UNRECOVERABLE"}


def load(path: Path) -> dict:
    if not path.exists():
        pytest.skip(f"{path} is not present")
    return json.loads(path.read_text())


def chunking_hash() -> str:
    return config_hash({"max_chunk_chars": settings.max_chunk_chars,
                        "min_chunk_chars": settings.min_chunk_chars})


def digest(versions: list[tuple[str, str]], name: str = SNAPSHOT_NAME) -> str:
    """``create_snapshot``'s construction: ORDER BY version_id, then hash the pairs."""
    payload = [{"version_id": v, "content_hash": h} for v, h in sorted(versions)]
    return stable_id("snap", name, config_hash({"versions": payload}), PARSER_VERSION,
                     chunking_hash(), length=32)


def corpus(count: int = EXPECTED_DOCUMENTS) -> list[tuple[str, str]]:
    return [(f"ver_{i:032x}", f"{i:064x}") for i in range(count)]


# ------------------------------------------------ the recovered snapshot parameters

def test_the_recorded_manifest_hash_and_name_reproduce_the_frozen_snapshot_id():
    """The whole recovery of both parameters rests on this one equality."""
    reproduced = stable_id("snap", SNAPSHOT_NAME, MANIFEST_HASH, PARSER_VERSION,
                           chunking_hash(), length=32)

    assert reproduced == SNAPSHOT_ID


def test_the_manifest_hash_was_read_from_an_experiment_artifact_not_typed_in():
    results = json.loads(Path("experiments/EXP-007/results.json").read_text())

    assert results["corpus_manifest_hash"] == MANIFEST_HASH


@pytest.mark.parametrize("name", ["v1-seed", "v1", "production-rag-v1", "seed", ""])
def test_any_other_snapshot_name_gives_a_different_id(name):
    """Which is why the match confirms the name and the manifest hash together."""
    assert stable_id("snap", name, MANIFEST_HASH, PARSER_VERSION, chunking_hash(),
                     length=32) != SNAPSHOT_ID


def test_the_manifest_recorded_the_parameters_it_verified():
    manifest = load(MANIFEST)

    assert manifest["name"] == SNAPSHOT_NAME
    assert manifest["manifest_hash"] == MANIFEST_HASH
    assert manifest["snapshot_id"] == SNAPSHOT_ID


# --------------------------------------------------------- the digest is determinate

def test_the_digest_is_deterministic():
    assert digest(corpus()) == digest(corpus())


def test_the_digest_does_not_depend_on_input_ordering():
    """``create_snapshot`` reads ORDER BY version_id, so a shuffle must not matter."""
    versions = corpus()
    shuffled = versions[100:] + versions[:100]

    assert digest(shuffled) == digest(versions)


def test_one_changed_content_hash_changes_the_digest():
    versions = corpus()
    changed = versions[:-1] + [(versions[-1][0], "f" * 64)]

    assert digest(changed) != digest(versions)


def test_a_missing_document_changes_the_digest():
    assert digest(corpus(EXPECTED_DOCUMENTS - 1)) != digest(corpus())


def test_a_duplicate_version_id_is_not_the_same_corpus():
    versions = corpus()
    duplicated = versions[:-1] + [versions[0]]

    assert digest(duplicated) != digest(versions)


def test_the_parser_version_and_chunking_config_are_digest_inputs():
    versions = corpus()
    other = stable_id("snap", SNAPSHOT_NAME,
                      config_hash({"versions": [{"version_id": v, "content_hash": h}
                                                for v, h in sorted(versions)]}),
                      "v9.9", chunking_hash(), length=32)

    assert other != digest(versions)


def test_synthetic_input_never_reproduces_the_frozen_snapshot():
    """A verifier a made-up corpus could satisfy would certify nothing."""
    assert digest(corpus()) != SNAPSHOT_ID


# ------------------------------------------------------ version-id determinism

def test_the_version_id_is_derived_from_the_document_text():
    src_id = stable_id("src", "anthropic", "https://example.invalid/doc", length=32)

    first = stable_id("ver", src_id, "a" * 64, length=32)

    assert first == stable_id("ver", src_id, "a" * 64, length=32)
    assert first != stable_id("ver", src_id, "b" * 64, length=32)


def test_the_source_id_is_derived_from_provider_and_canonical_url():
    assert stable_id("src", "openai", "https://x/y", length=32) != stable_id(
        "src", "anthropic", "https://x/y", length=32)


def test_captured_at_is_not_an_input_to_any_id():
    """A re-fetch is not doomed by the clock."""
    source = Path("src/rag_v1/ingest.py").read_text()
    line = next(x for x in source.splitlines() if "version_id = stable_id" in x)

    assert "captured_at" not in line
    assert "uuid" not in source.lower()


def test_every_reproduced_document_rederives_its_own_version_id():
    workspace = Path("recovery/CORPUS-001/recovered-openai-63.json")
    if not workspace.exists():
        pytest.skip("the recovery workspace has not been built")
    for document in json.loads(workspace.read_text())["recovered_documents"]:
        derived = stable_id("ver", document["source_id"], document["content_hash"],
                            length=32)

        assert derived == document["version_id"], document["source_url"]


# ------------------------------------------------------------- the manifest and ledger

def test_the_expected_manifest_holds_exactly_202_entries():
    entries = load(MANIFEST)["entries"]

    assert len(entries) == EXPECTED_DOCUMENTS
    assert {e["provider"] for e in entries} == {"openai", "anthropic"}


def test_no_expected_entry_is_duplicated():
    entries = load(MANIFEST)["entries"]

    assert len({e["source_url"] for e in entries}) == EXPECTED_DOCUMENTS
    assert len({e["source_id"] for e in entries}) == EXPECTED_DOCUMENTS


def test_no_known_expected_version_id_is_claimed_twice():
    known = [e["expected_version_id"] for e in load(MANIFEST)["entries"]
             if e["expected_version_id"] != "UNKNOWN"]

    assert len(known) == len(set(known))


def test_missing_hashes_are_marked_unknown_rather_than_inferred():
    entries = load(MANIFEST)["entries"]

    assert all(e["expected_raw_content_hash"] == "UNKNOWN" for e in entries)
    assert any(e["expected_version_id"] == "UNKNOWN" for e in entries)


def test_the_ledger_has_one_row_per_expected_document():
    rows = load(LEDGER)["rows"]

    assert len(rows) == EXPECTED_DOCUMENTS
    assert [r["index"] for r in rows] == list(range(1, EXPECTED_DOCUMENTS + 1))


def test_every_ledger_status_is_one_of_the_allowed_values():
    for row in load(LEDGER)["rows"]:
        assert row["status"] in ALLOWED_STATUSES, row["source_url"]


def test_a_row_that_is_not_an_exact_match_says_why_and_what_would_fix_it():
    for row in load(LEDGER)["rows"]:
        if row["status"] != "EXACT_MATCH":
            assert row["failure_reason"], row["source_url"]
            assert row["next_recovery_path"], row["source_url"]


def test_a_recovered_hash_never_overwrites_an_expected_hash():
    """The expected column is evidence; the recovered column is a candidate."""
    for row in load(LEDGER)["rows"]:
        if row["status"] == "HASH_MISMATCH":
            assert row["recovered_hashes"]["version_id"] != row["expected_version_id"]


def test_every_missing_document_is_anthropic_and_no_live_page_was_substituted():
    rows = [r for r in load(LEDGER)["rows"] if r["status"] == "MISSING_SOURCE"]

    assert rows, "the ledger should still be recording missing documents"
    for row in rows:
        assert row["provider"] == "anthropic"
        assert row["recovered_artifact"] is None
        assert "live page is not an acceptable substitute" in row["failure_reason"]


# ------------------------------------------- a partial corpus clears nothing

def test_the_snapshot_digest_is_not_reproduced():
    digest_state = load(LEDGER)["metrics"]["snapshot_digest"]

    assert digest_state["reproduced"] is False
    assert digest_state["target"] == SNAPSHOT_ID


def test_a_partial_corpus_cannot_set_corpus_snapshot_reproduced():
    limitation = load(LIMITATION)
    metrics = load(LEDGER)["metrics"]

    assert metrics["exactly_recovered"] < EXPECTED_DOCUMENTS
    assert limitation["corpus_snapshot_reproduced"] is False
    assert limitation["CORPUS_REPRODUCTION_INCOMPLETE"] is True


def test_a_partial_corpus_cannot_clear_retrieval_blocked():
    limitation = load(LIMITATION)

    assert limitation["RETRIEVAL_BLOCKED"] is True
    assert limitation["effect"] == "RETRIEVAL_BLOCKED"
    assert limitation["blocking_this_gate"]


def test_gold_evidence_recovery_is_not_corpus_recovery():
    """150 admitted cases rest on 9 document versions. The corpus is 202."""
    metrics = load(LEDGER)["metrics"]

    assert metrics["documents_whose_bytes_reproduce"] < EXPECTED_DOCUMENTS
    assert metrics["missing"] > 0


# -------------------------------------------------------- the unbuildable set

def test_the_2482_are_classified_and_are_not_a_corpus_blocker():
    analysis = load(UNBUILDABLE)
    classification = analysis["classification"]

    assert classification["A_needed_to_reproduce_the_corpus_snapshot"] is False
    assert classification["B_needed_to_reproduce_the_gold_authoring_process"] is True


def test_the_2482_are_not_documents():
    analysis = load(UNBUILDABLE)

    assert "documents" in analysis["what_the_objects_are"]["not"]
    assert analysis["where_the_number_comes_from"]["value"] == 2482


def test_the_count_is_attempts_and_the_record_says_so():
    analysis = load(UNBUILDABLE)

    finding = analysis["the_count_is_attempts_not_distinct_spans"]
    assert "not distinct facts" in finding["finding"]
    assert "counts attempts" in finding["corroboration"]
    assert analysis["where_the_number_comes_from"]["file"] == "scripts/export_batch_006.py"


def test_the_limitation_no_longer_counts_them_as_a_corpus_gap():
    limitation = load(LIMITATION)

    assert "unbuildable_identities" not in limitation["outstanding"]
    assert limitation["unbuildable_identities_reclassified"]["effect_on_this_gate"]


# ----------------------------------------------------- GOLD and retrieval untouched

def test_gold_remains_at_150_and_unchanged():
    combined = load(STATUS)["combined"]

    assert combined["human_verified"] == 150
    assert combined["holdout_eligible"] == 150
    assert combined["human_rejected"] == 9
    assert combined["genuine_multi_hop"] == 1


def test_the_ha47_repair_and_ha15_override_survive_corpus_work():
    records = {r["candidate_id"]: r for r in json.loads(
        Path("evals/review/gold_review_HA01_HA60_final.json").read_text())["records"]}

    assert records["HA-15"]["human_anaphora_override"] is True
    assert records["HA-15"]["anaphora_finding"]
    span = records["HA-47"]["expected_evidence"][0]
    assert span["evidence_hash"] == (
        "e894c94d831ccfd2678f4cd132b72b52e44770d07ebeaab6c51e96e0e312a203")


def test_gold_evidence_hashes_still_recompute():
    """Corpus recovery must adapt to GOLD, never the other way round."""
    records = json.loads(
        Path("evals/review/gold_review_HA01_HA60_final.json").read_text())["records"]
    for record in records:
        for span in record["expected_evidence"]:
            assert hashlib.sha256(span["evidence_text"].encode()).hexdigest() == (
                span["evidence_hash"]), record["candidate_id"]


def test_no_retrieval_was_run_and_no_split_frozen():
    status = load(STATUS)

    assert status["retrieval_was_not_run"] is True
    assert status["systems_executed"] == []
    assert status["holdout_frozen"] is False


def test_the_local_database_was_inspected_read_only_and_left_as_found():
    cluster = load(INVENTORY)["database_search"]["local_cluster"]

    assert cluster["state_when_found"] == cluster["restored_to"] == "down"
    assert "no migration was run" in cluster["verdict"]
    assert "document_version" not in cluster["databases"]


def test_no_corpus_data_was_written_into_the_repository():
    """Nothing but the .gitkeep files may be *tracked* under data/raw and data/cache.

    The check is against git, not against the filesystem. Both directories are
    gitignored precisely so a working copy can hold a fetched corpus — that is how the
    pipeline runs at all — and asserting the directory is empty on disk fails in every
    environment that has actually done the work, while saying nothing about what was
    committed. What must never happen is corpus data entering the repository, and that
    is a question only git can answer.
    """
    tracked = subprocess.run(
        ["git", "ls-files", "data/raw", "data/cache"],
        capture_output=True, text=True, check=True).stdout.split()
    assert sorted(tracked) == ["data/cache/.gitkeep", "data/raw/.gitkeep"], tracked


# ---------------------------------------------------- the manifest-hash final oracle

def test_the_oracle_refuses_a_partial_corpus():
    from rag_v1.corpus_oracle import verify_corpus

    verdict = verify_corpus(corpus(201), CHUNKING)

    assert not verdict
    assert "partial corpus cannot be certified" in verdict.reason


def test_the_oracle_refuses_a_duplicate_version_id():
    from rag_v1.corpus_oracle import verify_corpus

    versions = corpus()
    verdict = verify_corpus(versions[:-1] + [versions[0]], CHUNKING)

    assert not verdict
    assert "more than once" in verdict.reason


def test_the_oracle_refuses_a_plausible_but_wrong_corpus():
    """202 well-formed documents that are not the frozen ones must still fail."""
    from rag_v1.corpus_oracle import verify_corpus

    verdict = verify_corpus(corpus(), CHUNKING)

    assert not verdict
    assert "manifest hash does not match" in verdict.reason
    assert verdict.manifest_hash != MANIFEST_HASH


def test_the_oracle_separates_a_content_failure_from_a_parameter_failure():
    """A matching manifest hash with a wrong parameter is a different diagnosis."""
    from rag_v1.corpus_oracle import snapshot_id_for

    assert snapshot_id_for(MANIFEST_HASH, CHUNKING) == SNAPSHOT_ID
    assert snapshot_id_for(MANIFEST_HASH, {"max_chunk_chars": 4000,
                                           "min_chunk_chars": 200}) != SNAPSHOT_ID


def test_the_oracle_is_order_independent():
    from rag_v1.corpus_oracle import manifest_hash_for

    versions = corpus()

    assert manifest_hash_for(versions[100:] + versions[:100]) == manifest_hash_for(
        versions)


def test_a_document_with_no_recorded_identity_cannot_be_verified_alone():
    from rag_v1.corpus_oracle import verify_document

    result = verify_document("anthropic", "https://example.invalid/x", "text", "UNKNOWN")

    assert result["status"] == "EXPECTED_HASH_UNKNOWN"
    assert "collectively" in result["detail"]


def test_a_document_is_matched_by_derivation_not_by_assertion():
    from rag_v1.corpus_oracle import verify_document, version_id_for

    url, text = "https://example.invalid/x", "hello"
    expected = version_id_for("anthropic", url, text)

    assert verify_document("anthropic", url, text, expected)["status"] == "EXACT_MATCH"
    assert verify_document("anthropic", url, "other", expected)["status"] == (
        "HASH_MISMATCH")


def test_byte_anchors_refute_a_candidate_before_hashing():
    from rag_v1.corpus_oracle import verify_byte_anchors

    text = "the quick brown fox"
    anchor = [{"char_start": 4, "char_end": 9,
               "evidence_hash": hashlib.sha256(b"quick").hexdigest()}]

    assert verify_byte_anchors(text, anchor)[0]["matches"] is True
    assert verify_byte_anchors("the slow brown fox", anchor)[0]["matches"] is False


# --------------------------------------------------- host search and the correction

def test_the_host_was_not_reachable_and_the_record_says_so():
    host = load(HOST_SEARCH)["host_reachability"]
    present = [c for c in host["host_locations_requested"] if c["exists"]]

    assert all(c.get("empty") for c in present), "a non-empty host mount would be a lead"
    assert "No Windows host" in host["verdict"]


def test_no_archive_or_dump_was_found_in_the_accessible_filesystems():
    assert load(HOST_SEARCH)["accessible_sweep"]["archives_found"] == []


def test_the_14_unknown_openai_identities_were_tested_against_both_oracles():
    status = load(HOST_SEARCH)["openai_unknown_identity_status"]

    assert status["expected_hash_unknown_before"] == 14
    assert status["still_unknown"] == 14
    assert status["documents_confirmed_by_chunk_id_overall"] > 0
    assert "exhausted by evidence" in status["finding"]


def test_the_40_known_anthropic_identities_carry_no_document_body():
    search = load(ANTHROPIC_IDS)

    assert search["known_anthropic_identities"] == 40
    assert search["found_somewhere_in_the_repository"] == 40
    assert search["whose_location_carries_normalized_text"] == 0
    assert search["total_verified_historical_bytes"] > 0


def test_the_recovery_plan_splits_the_139_by_what_can_be_verified():
    plan = load(PLAN)
    group_a = plan["group_A_expected_version_id_known"]
    group_b = plan["group_B_expected_version_id_unknown"]

    assert group_a["count"] + group_b["count"] == plan["total_missing"] == 139
    assert group_a["count"] == 40


def test_the_plan_never_offers_live_pages_as_a_recovery_path():
    live = next(c for c in load(PLAN)["candidate_sources_in_preference_order"]
                if "live" in c["source"])

    assert live["verifiable_exactly"] is False
    assert "NOT a recovery path" in live["status"]


def test_the_audit_correction_preserves_the_superseded_wording():
    """The old reports were accurate when written; this is a trail, not a silent edit."""
    correction = load(LIMITATION)["audit_corrections"][0]

    assert "2,482 unbuildable identities remain a corpus" in (
        correction["superseded_statement"])
    assert "not part of the corpus snapshot digest" in correction["replacement_statement"]
    assert "silent edit" in correction["handling"]


def test_the_corpus_blocker_is_now_only_the_missing_anthropic_captures():
    limitation = load(LIMITATION)

    assert limitation["the_corpus_blocker"] == "139 missing Anthropic document captures"
    assert limitation["RETRIEVAL_BLOCKED"] is True
