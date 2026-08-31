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
    """data/raw and data/cache must still hold nothing but their .gitkeep files."""
    for directory in (Path("data/raw"), Path("data/cache")):
        assert [p.name for p in directory.iterdir()] == [".gitkeep"], directory
