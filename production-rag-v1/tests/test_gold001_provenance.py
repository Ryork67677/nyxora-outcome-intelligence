"""The reproducibility safeguards batch 006 lacked, tested against the closed record.

Batch 007's pilot is blocked because batch 006 counted its unbuildable set instead of
recording it, and the corpus that could re-derive it is gone. These tests pin the four
safeguards that stop that recurring. Where a test can use a real closed span it does —
137 spans across batches 003-006 carry an ``evidence_hash`` over text that cannot have
drifted, and a verifier that cannot check those is not worth shipping.

Nothing here writes to a closed batch, runs retrieval, or touches validation or holdout.
"""

from __future__ import annotations

import glob
import hashlib
import json
from pathlib import Path

import pytest

from rag_v1.gold.provenance import (
    NO_BUILDER,
    chunking_config_from_settings,
    SEMANTIC_GATE,
    UnbuildableLog,
    fingerprint,
    pilot_thresholds_unmet,
    select_pilot_cases,
    verify_fingerprint,
    verify_restored_corpus,
)
from rag_v1.ids import config_hash, stable_id

SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"
CHUNKING = {"max_chunk_chars": 1800, "min_chunk_chars": 200}


@pytest.fixture(scope="module")
def closed_records() -> list[dict]:
    """Every closed candidate that carries an anchored, hashed span."""
    records = []
    for path in sorted(glob.glob("evals/review/gold_review_batch_00*_final.json")):
        records.extend(json.loads(Path(path).read_text())["records"])
    if not records:
        pytest.skip("no closed batches present")
    return records


def fake_corpus(records: list[dict]) -> dict[str, str]:
    """A corpus in which every closed span sits at exactly its recorded offsets.

    Built from the records themselves: this is a stand-in for a *correct* restore, which
    is what lets the verifier be tested without the frozen corpus. It is not corpus and
    is never used to author anything.
    """
    docs: dict[str, str] = {}
    for record in records:
        for span in record.get("expected_evidence") or []:
            version, start = span["version_id"], span["char_start"]
            text = span["evidence_text"]
            body = docs.setdefault(version, "")
            if len(body) < start:
                body += " " * (start - len(body))
            docs[version] = body[:start] + text + body[start + len(text):]
    return docs


def reader(docs: dict[str, str]):
    def read_span(version_id: str, start: int, end: int) -> str | None:
        if version_id not in docs:
            return None
        return docs[version_id][start:end]
    return read_span


# ------------------------------------------------------- 1. unbuildable span identities

def test_a_declined_fact_keeps_its_identity_not_just_a_count():
    log = UnbuildableLog()
    log.record({"version_id": "v1", "char_start": 10, "char_end": 24,
                "evidence_text": "a span of text"})

    entry = log.entries[0]
    assert (entry["version_id"], entry["char_start"], entry["char_end"]) == ("v1", 10, 24)
    assert entry["evidence_text"] == "a span of text"
    assert entry["reason"] == NO_BUILDER


def test_the_log_hashes_what_it_records_so_a_restore_can_be_checked_against_it():
    log = UnbuildableLog()
    log.record({"version_id": "v1", "char_start": 0, "char_end": 5,
                "evidence_text": "hello"})

    assert log.entries[0]["evidence_hash"] == hashlib.sha256(b"hello").hexdigest()


def test_the_same_span_recorded_twice_is_one_entry():
    log = UnbuildableLog()
    for _ in range(3):
        log.record({"version_id": "v1", "char_start": 0, "char_end": 5,
                    "evidence_text": "hello"})

    assert len(log) == 1


def test_a_semantic_gate_failure_is_distinguished_from_no_builder():
    """The pilot may draw only from NO_BUILDER: the distinction has to survive the run."""
    log = UnbuildableLog()
    log.record({"version_id": "v1", "char_start": 0, "char_end": 5,
                "evidence_text": "hello"}, reason=NO_BUILDER)
    log.record({"version_id": "v1", "char_start": 9, "char_end": 14,
                "evidence_text": "world"}, reason=SEMANTIC_GATE)

    assert len(log.of_reason(NO_BUILDER)) == 1
    assert len(log.of_reason(SEMANTIC_GATE)) == 1


def test_the_manifest_carries_the_identities_batch_006_discarded():
    log = UnbuildableLog()
    for i in range(3):
        log.record({"version_id": "v1", "char_start": i * 10, "char_end": i * 10 + 4,
                    "evidence_text": f"tx{i:02d}"})

    manifest = log.manifest(corpus_snapshot=SNAPSHOT, batch=7)

    assert manifest["total"] == 3
    assert manifest["by_reason"] == {NO_BUILDER: 3}
    assert manifest["corpus_snapshot"] == SNAPSHOT
    assert len(manifest["entries"]) == 3


# ------------------------------------------------------------ 2. corpus fingerprint

def test_the_fingerprint_reproduces_the_snapshot_id_construction():
    """The same arithmetic rag_v1.snapshot.create_snapshot uses, without a database."""
    versions = [("v1", "h1"), ("v2", "h2")]

    expected = stable_id(
        "snap", "corpus",
        config_hash({"versions": [{"version_id": "v1", "content_hash": "h1"},
                                  {"version_id": "v2", "content_hash": "h2"}]}),
        "p1", config_hash(CHUNKING), length=32)

    assert fingerprint(versions, name="corpus", parser_version="p1",
                       chunking_config=CHUNKING) == expected


def test_the_chunking_config_helper_uses_the_keys_the_hash_is_built_from():
    """Wrong key names would compute a different id and fail a good restore."""
    assert set(chunking_config_from_settings()) == {"max_chunk_chars", "min_chunk_chars"}


def test_one_changed_document_changes_the_fingerprint():
    """The point of a fingerprint: a re-fetch cannot pass as the frozen corpus."""
    frozen = fingerprint([("v1", "h1"), ("v2", "h2")], name="c",
                         parser_version="p1", chunking_config=CHUNKING)
    refetched = fingerprint([("v1", "h1"), ("v2", "CHANGED")], name="c",
                            parser_version="p1", chunking_config=CHUNKING)

    assert frozen != refetched


def test_a_missing_document_changes_the_fingerprint():
    whole = fingerprint([("v1", "h1"), ("v2", "h2")], name="c",
                        parser_version="p1", chunking_config=CHUNKING)
    partial = fingerprint([("v1", "h1")], name="c", parser_version="p1",
                          chunking_config=CHUNKING)

    assert whole != partial


def test_verification_rejects_a_corpus_that_claims_an_id_it_does_not_hash_to():
    result = verify_fingerprint(SNAPSHOT, [("v1", "h1")], name="c",
                                parser_version="p1", chunking_config=CHUNKING)

    assert result["matches"] is False
    assert result["expected"] == SNAPSHOT
    assert result["computed"] != SNAPSHOT


def test_verification_accepts_the_corpus_that_does_hash_to_it():
    versions = [("v1", "h1"), ("v2", "h2")]
    claimed = fingerprint(versions, name="c", parser_version="p1",
                          chunking_config=CHUNKING)

    assert verify_fingerprint(claimed, versions, name="c", parser_version="p1",
                              chunking_config=CHUNKING)["matches"] is True


# --------------------------------------------------------------- 3. restore verifier

def test_every_closed_span_hashes_to_its_recorded_hash(closed_records):
    """The premise of the verifier, checked against the record itself."""
    checked = 0
    for record in closed_records:
        for span in record.get("expected_evidence") or []:
            if "evidence_hash" not in span:
                continue
            checked += 1
            assert (hashlib.sha256(span["evidence_text"].encode()).hexdigest()
                    == span["evidence_hash"])
    assert checked >= 9


def test_a_correct_restore_verifies(closed_records):
    docs = fake_corpus(closed_records)

    result = verify_restored_corpus(closed_records, reader(docs))

    assert result["verified"] is True
    assert result["spans_checked"] == result["spans_matched"] >= 9
    assert result["mismatches"] == [] and result["missing"] == []


def test_a_single_changed_character_fails_the_restore(closed_records):
    """Text that still reads plausibly is exactly what a hash is for."""
    docs = fake_corpus(closed_records)
    version = sorted(docs)[0]
    body = docs[version]
    index = next(i for i, c in enumerate(body) if c.strip())
    docs[version] = body[:index] + ("X" if body[index] != "X" else "Y") + body[index + 1:]

    result = verify_restored_corpus(closed_records, reader(docs))

    assert result["verified"] is False
    assert result["mismatches"]


def test_an_offset_shifted_by_one_fails_the_restore(closed_records):
    """A restore whose offsets moved still returns text; the hash is what catches it."""
    docs = fake_corpus(closed_records)

    def shifted(version_id, start, end):
        if version_id not in docs:
            return None
        return docs[version_id][start + 1:end + 1]

    result = verify_restored_corpus(closed_records, shifted)

    assert result["verified"] is False


def test_a_missing_document_is_reported_not_skipped(closed_records):
    result = verify_restored_corpus(closed_records, lambda *_: None)

    assert result["verified"] is False
    assert len(result["missing"]) == result["spans_checked"]


# ------------------------------------------------------- 4. deterministic pilot selection

def make_unbuildable(count: int, reason: str = NO_BUILDER) -> list[dict]:
    return [{"version_id": f"v{i % 3}", "char_start": i * 100, "char_end": i * 100 + 40,
             "evidence_text": f"span {i}", "reason": reason} for i in range(count)]


def test_selection_is_deterministic():
    pool = make_unbuildable(30)
    shuffled = list(reversed(pool))

    first = select_pilot_cases(pool)
    second = select_pilot_cases(shuffled)

    assert [(c["version_id"], c["char_start"]) for c in first["cases"]] == \
           [(c["version_id"], c["char_start"]) for c in second["cases"]]


def test_selection_takes_the_preregistered_ten():
    result = select_pilot_cases(make_unbuildable(30))

    assert result["selected"] == 10 and result["short"] is False
    assert len(result["cases"]) == 10


def test_a_semantic_gate_failure_is_never_selected():
    """Preregistered: those failed for reasons paraphrasing does not fix."""
    pool = make_unbuildable(5) + make_unbuildable(20, reason=SEMANTIC_GATE)

    result = select_pilot_cases(pool)

    assert result["eligible"] == 5
    assert all(c["reason"] == NO_BUILDER for c in result["cases"])


def test_a_span_already_spent_by_a_closed_batch_is_excluded():
    pool = make_unbuildable(12)
    spent = [(pool[0]["version_id"], pool[0]["char_start"], pool[0]["char_end"])]

    result = select_pilot_cases(pool, already_spent=spent)

    assert result["eligible"] == 11
    assert all((c["version_id"], c["char_start"]) !=
               (pool[0]["version_id"], pool[0]["char_start"]) for c in result["cases"])


def test_every_selected_case_records_why_it_was_selected():
    result = select_pilot_cases(make_unbuildable(15))

    assert all(c["selection_basis"] for c in result["cases"])
    assert "not spent by any closed batch" in result["cases"][0]["selection_basis"]


def test_a_short_pool_is_reported_short_rather_than_padded():
    result = select_pilot_cases(make_unbuildable(4))

    assert result["selected"] == 4 and result["short"] is True


# ------------------------------------------------------------------ threshold guard

def test_an_unrun_pilot_fails_all_four_thresholds():
    """Unmeasured is not met. No report may call this a pass."""
    assert len(pilot_thresholds_unmet({})) == 4


def test_a_passing_pilot_meets_all_four():
    assert pilot_thresholds_unmet({
        "independently_judged_factually_sound": 9,
        "unsupported_claims": 0,
        "relation_direction_reversals": 0,
        "scope_broadening": 0,
    }) == []


def test_one_unsupported_claim_fails_the_pilot():
    unmet = pilot_thresholds_unmet({
        "independently_judged_factually_sound": 10,
        "unsupported_claims": 1,
        "relation_direction_reversals": 0,
        "scope_broadening": 0,
    })

    assert unmet == ["unsupported_claims == 0"]


def test_seven_of_ten_sound_fails_the_pilot():
    unmet = pilot_thresholds_unmet({
        "independently_judged_factually_sound": 7,
        "unsupported_claims": 0,
        "relation_direction_reversals": 0,
        "scope_broadening": 0,
    })

    assert unmet == ["independently_judged_factually_sound >= 8 of 10"]
