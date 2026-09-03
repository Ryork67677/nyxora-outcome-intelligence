"""Blob-to-raw immutability, and provenance on every historical candidate.

The OpenAI half of the corpus is re-fetchable because each saved URL is pinned to a full
commit SHA. That is only true if the rewrite preserves the pin — an off-by-one in owner,
repo, commit or path silently fetches a different document, and a branch name fetches
whatever is there today. These tests pin the rewrite and pin the refusals.

The Anthropic half has no pinned form, so every candidate must carry where it came from
and when. A live page is never reproducible evidence of a past state, however close it
looks, and that distinction is tested rather than left to a comment.

Nothing here fetches anything or touches a closed batch.
"""

from __future__ import annotations

import pytest

from rag_v1.gold.rehydration import (
    HistoricalCandidate,
    NotImmutable,
    blob_to_raw,
    commit_of,
    is_immutable_ref,
    redirect_is_safe,
)

COMMIT = "39327d7c5d04c120bf47f1ee9696c078e1f55441"
BLOB = (f"https://github.com/openai/openai-agents-python/blob/{COMMIT}/docs/agents.md")
RAW = (f"https://raw.githubusercontent.com/openai/openai-agents-python/{COMMIT}/"
       "docs/agents.md")


# ------------------------------------------------------------ blob → raw immutability

def test_a_pinned_blob_rewrites_to_raw_preserving_every_component():
    assert blob_to_raw(BLOB) == RAW


def test_the_rewrite_changes_only_the_host_and_the_blob_segment():
    """Owner, repo, commit and path must survive verbatim."""
    rewritten = blob_to_raw(BLOB)

    assert "openai/openai-agents-python" in rewritten
    assert COMMIT in rewritten
    assert rewritten.endswith("/docs/agents.md")
    assert "/blob/" not in rewritten


@pytest.mark.parametrize("path", [
    "docs/agents.md",
    "docs/ref/tool.md",
    "examples/basic/hello world.md",
    "docs/models/litellm.md",
])
def test_paths_with_any_shape_survive_the_rewrite(path):
    assert blob_to_raw(
        f"https://github.com/o/r/blob/{COMMIT}/{path}").endswith(f"/{path}")


@pytest.mark.parametrize("ref", ["main", "master", "v1.2.3", "HEAD", "39327d7", ""])
def test_a_ref_that_is_not_a_full_commit_is_refused(ref):
    """A branch head is a moving target: main today is not main on 2026-08-17."""
    with pytest.raises(NotImmutable):
        blob_to_raw(f"https://github.com/o/r/blob/{ref}/docs/a.md")


def test_a_non_github_url_is_refused():
    with pytest.raises(NotImmutable):
        blob_to_raw("https://platform.claude.com/docs/en/about-claude/glossary.md")


def test_an_abbreviated_sha_is_not_immutable_enough():
    assert is_immutable_ref(COMMIT) is True
    assert is_immutable_ref(COMMIT[:7]) is False


def test_the_commit_is_readable_from_both_url_forms():
    assert commit_of(BLOB) == commit_of(RAW) == COMMIT


def test_a_branch_url_has_no_commit():
    assert commit_of("https://github.com/o/r/blob/main/docs/a.md") is None


# ------------------------------------------------------------------ redirect safety

def test_a_redirect_that_keeps_the_commit_is_safe():
    moved = (f"https://raw.githubusercontent.com/openai/openai-agents-python/{COMMIT}/"
             "docs/agents.md?token=x")

    assert redirect_is_safe(BLOB, moved) is True


def test_a_redirect_to_a_branch_head_is_refused():
    """The failure this guards: the pin quietly replaced by whatever is current."""
    to_head = "https://raw.githubusercontent.com/openai/openai-agents-python/main/docs/agents.md"

    assert redirect_is_safe(BLOB, to_head) is False


def test_a_redirect_to_a_different_commit_is_refused():
    other = "b" * 40
    elsewhere = f"https://raw.githubusercontent.com/openai/openai-agents-python/{other}/docs/agents.md"

    assert redirect_is_safe(BLOB, elsewhere) is False


def test_an_unpinned_request_is_never_safe():
    assert redirect_is_safe("https://github.com/o/r/blob/main/a.md", RAW) is False


# --------------------------------------------------------- historical candidate provenance

def test_a_candidate_carries_where_it_came_from_and_when():
    candidate = HistoricalCandidate(
        canonical_url="https://platform.claude.com/docs/en/about-claude/glossary",
        provenance_url="https://web.archive.org/web/20260817000000/https://example",
        source_kind="archive_capture",
        captured_at="2026-08-17T04:46:19Z")

    record = candidate.record()

    assert record["provenance_url"].startswith("https://web.archive.org/")
    assert record["captured_at"] == "2026-08-17T04:46:19Z"
    assert record["reproducible"] is True


@pytest.mark.parametrize("kind", ["pinned_commit", "official_versioned_asset",
                                  "archive_capture"])
def test_reproducible_kinds_are_marked_reproducible(kind):
    assert HistoricalCandidate("u", "p", kind).is_reproducible() is True


def test_a_live_page_is_never_reproducible_evidence_of_a_past_state():
    """However closely it matches, a live fetch is a comparison candidate only."""
    live = HistoricalCandidate("u", "https://platform.claude.com/x.md", "live_fetch")

    assert live.is_reproducible() is False
    assert live.record()["reproducible"] is False


def test_provenance_survives_into_the_record_even_when_hashes_are_absent():
    record = HistoricalCandidate("u", "p", "archive_capture").record()

    assert set(record) >= {"canonical_url", "provenance_url", "source_kind",
                           "captured_at", "content_hash", "version_id", "reproducible"}
