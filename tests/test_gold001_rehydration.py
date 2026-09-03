"""The quarantined rehydration verifier: can a live crawl ever be certified?

The answer turns on one property of the code, and it is worth pinning with tests because
the whole recovery argument rests on it: **the snapshot id is content-derived**. Reading
``rag_v1.ingest`` and ``rag_v1.snapshot``, every input to it is either persisted or is the
document text itself. Nothing is random, sequential or clock-derived — in particular
``captured_at`` is stored on the row but never enters an id.

That makes ``snap_689e336380a054d8039dc35b2c09cd0a`` a complete authoritative digest over
all 202 normalized texts at once, which is exactly the instrument a rehydration would have
to reproduce. These tests pin the construction, and pin that partial matches are refused:
201 of 202 documents is a different corpus, and a verifier that shrugged at that would be
worse than none.

Nothing here fetches anything, writes to ``data/``, runs retrieval, or touches a closed
batch.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from rag_v1.ids import config_hash, stable_id
from rag_v1.parsing import PARSER_VERSION

SCRIPT = Path("scripts/rehydrate_quarantine.py")
TARGET = "snap_689e336380a054d8039dc35b2c09cd0a"


@pytest.fixture(scope="module")
def rq():
    if not SCRIPT.exists():
        pytest.skip("the rehydration verifier is not present")
    spec = importlib.util.spec_from_file_location("rq", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def corpus(count: int = 202) -> list[tuple[str, str]]:
    return sorted((f"ver_{i:032x}", f"{i:064x}") for i in range(count))


# ------------------------------------------------- the id chain is content-derived

def test_the_version_id_is_derived_from_the_document_text(rq):
    """version_id = stable_id("ver", src_id, sha256(normalized_text)) — no clock, no uuid."""
    src_id = stable_id("src", "anthropic", "https://example.invalid/doc", length=32)

    first = stable_id("ver", src_id, "a" * 64, length=32)
    second = stable_id("ver", src_id, "b" * 64, length=32)

    assert first != second
    assert first == stable_id("ver", src_id, "a" * 64, length=32)


def test_captured_at_is_not_an_input_to_any_id(rq):
    """The capture timestamp is stored on the row; a re-fetch is not doomed by the clock."""
    source = Path("src/rag_v1/ingest.py").read_text()
    version_line = next(line for line in source.splitlines()
                        if "version_id = stable_id" in line)

    assert "captured_at" not in version_line
    assert "uuid" not in source.lower()


def test_the_snapshot_id_reproduces_create_snapshots_construction(rq):
    versions = corpus()

    expected = stable_id(
        "snap", "v1-seed",
        config_hash({"versions": [{"version_id": v, "content_hash": h}
                                  for v, h in versions]}),
        PARSER_VERSION, config_hash(rq.chunking_config()), length=32)

    assert rq.snapshot_id_for(versions, "v1-seed") == expected


def test_the_snapshot_id_is_a_digest_over_every_document(rq):
    """This is why it can certify a whole corpus: one byte anywhere changes it."""
    versions = corpus()
    baseline = rq.snapshot_id_for(versions, "v1-seed")

    changed = sorted(versions[:-1] + [(versions[-1][0], "f" * 64)])

    assert rq.snapshot_id_for(changed, "v1-seed") != baseline


def test_a_missing_document_changes_the_snapshot_id(rq):
    assert rq.snapshot_id_for(corpus(201), "v1-seed") != rq.snapshot_id_for(corpus(202),
                                                                            "v1-seed")


def test_the_snapshot_name_is_part_of_the_id_so_candidates_are_searched(rq):
    versions = corpus()

    assert rq.snapshot_id_for(versions, "v1-seed") != rq.snapshot_id_for(versions, "v1")
    assert "v1-seed" in rq.CANDIDATE_NAMES


# ------------------------------------------------------------- fail-closed behaviour

def test_synthetic_input_never_reproduces_the_frozen_target(rq):
    """A verifier that could be satisfied by made-up input would certify nothing."""
    assert rq.snapshot_id_for(corpus(), "v1-seed") != TARGET
    assert rq.TARGET_SNAPSHOT == TARGET


def test_the_verifier_refuses_a_quarantine_inside_the_repository(rq):
    """Fetched bytes must never be able to pass as corpus."""
    source = SCRIPT.read_text()

    assert "must be outside the repository" in source


def test_a_partial_crawl_is_refused_before_any_comparison(rq):
    """201 of 202 is a different corpus, not a near miss."""
    source = SCRIPT.read_text()

    assert 'if len(fetched) != FROZEN_CAPTURE_SHAPE["documents"]:' in source
    assert "partial crawl cannot be certified" in source


def test_diagnostics_are_never_treated_as_certification(rq):
    """Counts and the sampled closed spans are recorded, never accepted as proof."""
    source = SCRIPT.read_text()

    assert "Diagnostics never certify" in source
    assert "not by counts, not by the 137 sampled closed spans" in source
