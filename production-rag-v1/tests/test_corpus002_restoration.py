"""CORPUS-002: the restored corpus is the frozen corpus, and nothing else moved.

These tests read the restoration artifacts rather than the live database, so they pass
in any environment that has the report — including CI, where the isolated restoration
database does not exist. Where a check needs the database it is skipped explicitly
rather than silently weakened.

Nothing here runs retrieval, and one test exists purely to keep it that way.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPORT = Path("experiments/CORPUS-002/CORPUS-002-restoration-report.json")
DOCS = Path("experiments/CORPUS-002/CORPUS-002-document-verification.json")
ANCHORS = Path("experiments/CORPUS-002/CORPUS-002-gold-anchor-verification.json")
FINGERPRINT = Path("experiments/CORPUS-002/CORPUS-002-environment-fingerprint.json")

ARCHIVE_SHA = "4387ae1d5144109adbde3f11f1fcb339c3773480f356f9804909cf3ad2051b33"
MANIFEST_HASH = "452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17"
SNAPSHOT_ID = "snap_689e336380a054d8039dc35b2c09cd0a"
GOLD_SOURCES = {
    "001": "evals/gold/batch_001_v2/overlay.json",
    "002": "evals/review/gold_review_batch_002.json",
    "003": "evals/review/gold_review_batch_003.json",
    "004": "evals/review/gold_review_batch_004_final.json",
    "005": "evals/review/gold_review_batch_005_final.json",
    "006": "evals/review/gold_review_batch_006_final.json",
    "HA": "evals/review/gold_review_HA01_HA60_final.json",
}


def load(path: Path) -> dict:
    if not path.exists():
        pytest.skip(f"{path} has not been generated")
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def report() -> dict:
    return load(REPORT)


# ------------------------------------------------------------------ archive and package


def test_the_archive_hash_is_the_one_the_owner_recorded(report):
    assert report["archive"]["expected"] == ARCHIVE_SHA
    assert report["archive"]["match"] is True
    assert report["archive"]["sha256"] == ARCHIVE_SHA


def test_every_package_checksum_passed(report):
    package = report["package_integrity"]
    assert package["entries"] == 203
    assert package["verified"] == 203
    assert package["failed"] == 0


def test_the_working_copy_still_equals_the_package(report):
    """§4: a working copy that has drifted from the package is not the corpus."""
    assert report["working_copy"]["failed"] == 0
    assert report["working_copy"]["mismatches"] == []
    assert report["working_copy"]["verified"] == 203


# ------------------------------------------------------------------------- documents


def test_all_202_documents_restored_with_the_right_split(report):
    documents = report["documents"]
    assert documents["restored"] == 202
    assert documents["expected"] == 202
    assert documents["by_provider"] == {"anthropic": 139, "openai": 63}
    assert documents["missing"] == []


def test_no_document_identity_mismatched(report):
    """§9 wants mismatches individually, so the list must be empty, not merely short."""
    assert report["documents"]["mismatches"] == []


def test_the_document_verification_artifact_agrees_with_the_report(report):
    assert load(DOCS) == report["documents"]


# ------------------------------------------------------------- corpus identity oracles


def test_the_manifest_hash_reproduces_exactly(report):
    identity = report["identity"]
    assert identity["manifest_hash_expected"] == MANIFEST_HASH
    assert identity["manifest_hash_computed"] == MANIFEST_HASH
    assert identity["manifest_hash_match"] is True


def test_the_snapshot_id_reproduces_exactly(report):
    identity = report["identity"]
    assert identity["snapshot_id_expected"] == SNAPSHOT_ID
    assert SNAPSHOT_ID in identity["snapshot_ids_in_db"]
    assert identity["snapshot_id_match"] is True


def test_the_snapshot_was_not_replaced_by_a_lookalike(report):
    """§11: a different id created and called equivalent is the failure mode."""
    assert report["identity"]["snapshot_ids_in_db"] == [SNAPSHOT_ID]


def test_the_chunking_parameters_come_from_source(report):
    from rag_v1.config import settings

    chunking = report["identity"]["chunking"]
    assert chunking["max_chunk_chars"] == settings.max_chunk_chars == 3500
    assert chunking["min_chunk_chars"] == settings.min_chunk_chars == 200


def test_version_id_derivation_is_deterministic():
    from rag_v1.corpus_oracle import version_id_for

    first = version_id_for("anthropic", "https://example.test/a", "body text")
    second = version_id_for("anthropic", "https://example.test/a", "body text")
    assert first == second
    assert first != version_id_for("anthropic", "https://example.test/a", "other")
    assert first != version_id_for("openai", "https://example.test/a", "body text")


def test_the_normalizer_is_deterministic():
    from rag_v1.corpus_oracle import content_hash_of

    text = "# Title\n\nA paragraph with `code` and a number 42.\n"
    assert content_hash_of(text) == content_hash_of(text)
    assert content_hash_of(text) == hashlib.sha256(text.encode()).hexdigest()


def test_the_manifest_hash_is_order_independent():
    """A corpus assembled in a different order is the same corpus."""
    from rag_v1.corpus_oracle import manifest_hash_for

    pairs = [("ver_b", "hash_b"), ("ver_a", "hash_a"), ("ver_c", "hash_c")]
    assert manifest_hash_for(pairs) == manifest_hash_for(sorted(pairs, reverse=True))


# ---------------------------------------------------------------------------- chunks


def test_the_v1_control_chunks_match_the_historical_metrics(report):
    chunks = report["chunks"]
    assert chunks["control_set"] == "cs_v1_control"
    assert chunks["control_by_provider"] == {"anthropic": 12028, "openai": 2181}
    assert chunks["control_total"] == 14209
    assert chunks["matches_historical"] is True


def test_only_the_control_chunk_set_was_restored(report):
    """§13: experimental chunk sets are retrieval configuration, not corpus identity."""
    assert list(report["chunks"]["by_chunk_set"]) == ["cs_v1_control"]


# ------------------------------------------------------------------- GOLD evidence


def test_every_gold_case_carries_an_anchor(report):
    summary = report["gold_anchors"]["summary"]
    assert summary["cases"] == 150
    assert summary["unanchored_cases"] == 0
    assert summary["anchored_cases"] == 150


def test_every_gold_anchor_reproduces_against_the_restored_corpus(report):
    summary = report["gold_anchors"]["summary"]
    assert summary["spans_total"] > 0
    assert summary["spans_verified"] == summary["spans_total"]
    assert summary["failures"] == []


def test_both_anchor_schemas_were_checked(report):
    """Reading only `expected_evidence` leaves 45 of the 150 cases unverified."""
    shapes = report["gold_anchors"]["summary"]["by_shape"]
    assert shapes.get("legacy_flat", 0) > 0, "the flat batch-001..003 shape was skipped"
    assert shapes.get("expected_evidence", 0) > 0


def test_ha47_repaired_span_and_ha15_source_still_verify(report):
    per_case = {c["candidate_id"]: c for c in report["gold_anchors"]["per_case"]}
    for candidate in ("HA-15", "HA-47"):
        entry = next((v for k, v in per_case.items() if k.startswith(candidate)), None)
        assert entry is not None, f"{candidate} is not in the verification"
        assert entry["failures"] == []
        assert entry["verified"] == entry["spans"] > 0


def test_gold_records_were_not_modified_to_fit_the_corpus():
    """§5: the corpus is restored to the benchmark, never the benchmark to the corpus."""
    import subprocess

    # The GOLD records specifically, not all of evals/: later phases legitimately add
    # new files there (EVAL-SPLIT-001 writes evals/splits/), and a test that treats any
    # new sibling as a modified benchmark cries wolf.
    changed = subprocess.run(
        ["git", "status", "--porcelain", "evals/gold/", "evals/review/",
         "experiments/GOLD-001/"],
        capture_output=True, text=True, check=True).stdout.strip()
    assert changed == "", f"GOLD material has uncommitted edits:\n{changed}"


def test_the_gold_case_count_is_still_150():
    total = 0
    for rel in GOLD_SOURCES.values():
        path = Path(rel)
        if not path.exists():
            pytest.skip(f"{rel} absent")
        payload = json.loads(path.read_text())
        records = payload.get("records") or payload.get("case_records") or []
        total += sum(1 for r in records
                     if r.get("verification_status") == "human_verified"
                     or r.get("human_verified"))
    assert total == 150


# ------------------------------------------------------------- no retrieval, no fetch


def test_no_retrieval_was_executed(report):
    counts = report["environment"]["retrieval_tables_row_counts"]
    assert counts, "the fingerprint recorded no retrieval-table counts"
    assert all(value == 0 for value in counts.values()), counts
    assert report["gates"]["no_retrieval_ran"] is True


def test_no_embeddings_were_built(report):
    assert report["environment"]["retrieval_tables_row_counts"]["chunk_embedding"] == 0


def test_the_project_retrieval_flag_is_still_true():
    status = load(Path("experiments/GOLD-001/GOLD-001-eligibility-status.json"))
    assert status["retrieval_was_not_run"] is True
    assert status["systems_executed"] == []
    assert status["holdout_frozen"] is False


def test_the_restoration_used_no_network_source(report):
    """Every byte came from the verified package, and the report says which one."""
    assert report["archive"]["match"] is True
    assert report["working_copy"]["failed"] == 0
    assert any("network" in item for item in report["not_done"])


def test_the_restoration_database_is_not_the_historical_one(report):
    """§7: the historical database must not be overwritten."""
    assert report["environment"]["restoration_database"] == "corpus002_restore"
    assert report["environment"]["restoration_database"] != "rag"


# ------------------------------------------------------------------------ the verdict


def test_all_gates_pass_and_the_flags_follow_from_them(report):
    assert all(report["gates"].values()), report["gates"]
    assert report["corpus_002_succeeded"] is True
    flags = report["flags"]
    assert flags["corpus_snapshot_reproduced"] is True
    assert flags["CORPUS_REPRODUCTION_INCOMPLETE"] is False
    assert flags["RETRIEVAL_BLOCKED_BY_CORPUS"] is False


def test_the_split_block_is_not_cleared(report):
    """§16: CORPUS-002 clears the corpus block only."""
    assert "UNCHANGED" in report["flags"]["holdout_split_block"]


def test_the_fingerprint_records_the_migration_order(report):
    fingerprint = load(FINGERPRINT)
    assert fingerprint == report["environment"]
    order = fingerprint["sql_applied_in_order"]
    assert order.index("sql/001_init.sql") < order.index("sql/002_chunk_sets.sql")
    assert "(ingest 202 documents)" in order
    assert order.index("(ingest 202 documents)") < order.index("sql/002_chunk_sets.sql")


def test_the_anchor_artifact_agrees_with_the_report(report):
    assert load(ANCHORS) == report["gold_anchors"]
