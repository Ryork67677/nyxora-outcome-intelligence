"""Accept or reject a candidate corpus by arithmetic, never by inspection.

The frozen corpus is gone from this environment, but three things about it survived, and
together they let a candidate produced anywhere be checked here with no trust involved:

``MANIFEST_HASH``
    ``452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17`` — the digest
    over all 202 ``(version_id, content_hash)`` pairs, recorded in
    ``experiments/EXP-007/results.json``. This is the final oracle. It isolates corpus
    *content* from the snapshot name, the parser version and the chunking budget, so a
    corpus can be checked without those being right too.

surviving ``version_id`` values
    A per-document oracle. 40 of the 139 missing Anthropic documents have one, so a
    candidate for those is decided one at a time.

surviving ``chunk_id`` values
    A stronger per-document oracle:
    ``stable_id("chk", version_id, section_path, char_start, char_end, hash(text))``
    binds identity to section structure, offsets and chunk text at once.

The order matters and is enforced. A set of individually plausible documents can still be
the wrong corpus: only the manifest hash decides that, and it decides all-or-nothing.
Nothing here fetches, restores, or writes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from rag_v1.ids import config_hash, stable_id
from rag_v1.parsing import PARSER_VERSION

SNAPSHOT_ID = "snap_689e336380a054d8039dc35b2c09cd0a"
MANIFEST_HASH = "452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17"
SNAPSHOT_NAME = "v1-openai-anthropic"
EXPECTED_DOCUMENTS = 202


def content_hash_of(normalized_text: str) -> str:
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


def source_id_for(provider: str, canonical_url: str) -> str:
    return stable_id("src", provider.lower(), canonical_url, length=32)


def version_id_for(provider: str, canonical_url: str, normalized_text: str) -> str:
    """The identity a document has, derived from what it says and where it came from."""
    return stable_id("ver", source_id_for(provider, canonical_url),
                     content_hash_of(normalized_text), length=32)


def manifest_hash_for(versions: list[tuple[str, str]]) -> str:
    """``create_snapshot``'s manifest digest over ``(version_id, content_hash)`` pairs.

    ``create_snapshot`` reads ``ORDER BY version_id``, so the ordering is a sort on the
    version id. It is applied here rather than trusted from the caller: a candidate
    assembled in a different order is the same corpus and must hash the same.
    """
    payload = [{"version_id": v, "content_hash": h} for v, h in sorted(versions)]
    return config_hash({"versions": payload})


def snapshot_id_for(manifest_hash: str, chunking: dict,
                    name: str = SNAPSHOT_NAME) -> str:
    return stable_id("snap", name, manifest_hash, PARSER_VERSION,
                     config_hash(chunking), length=32)


@dataclass(frozen=True)
class Verdict:
    """Why a candidate corpus was accepted or refused. ``reproduced`` is the only pass."""

    reproduced: bool
    reason: str
    documents: int
    manifest_hash: str | None = None
    snapshot_id: str | None = None

    def __bool__(self) -> bool:
        return self.reproduced


def verify_corpus(versions: list[tuple[str, str]], chunking: dict) -> Verdict:
    """Does this candidate reproduce the frozen corpus? Fail-closed, in order.

    ``versions`` is every document's ``(version_id, content_hash)``. The checks run
    cheapest-first and each is fatal, because a later check passing cannot excuse an
    earlier one failing:

    1. the corpus must have all 202 documents — a partial crawl is a different corpus,
       not a near miss;
    2. no version id may repeat — 201 documents and a duplicate is not 202;
    3. the manifest hash must match, which is the content decision;
    4. the snapshot id must match, which additionally pins the name, parser and chunking.
    """
    if len(versions) != EXPECTED_DOCUMENTS:
        return Verdict(False, f"{len(versions)} documents, expected "
                              f"{EXPECTED_DOCUMENTS}: a partial corpus cannot be "
                              "certified and is not recovered data", len(versions))
    identities = [v for v, _ in versions]
    if len(set(identities)) != len(identities):
        return Verdict(False, "a version_id appears more than once, so this is not 202 "
                              "distinct documents", len(versions))

    manifest = manifest_hash_for(versions)
    if manifest != MANIFEST_HASH:
        return Verdict(False, "the manifest hash does not match. Every document may look "
                              "individually plausible and this still be the wrong "
                              "corpus — the manifest hash is what decides, and it "
                              "decides all-or-nothing", len(versions), manifest)

    snapshot = snapshot_id_for(manifest, chunking)
    if snapshot != SNAPSHOT_ID:
        return Verdict(False, "the manifest hash matches but the snapshot id does not, "
                              "so the corpus content is right and a parameter is wrong: "
                              "the snapshot name, the parser version or the chunking "
                              "budget", len(versions), manifest, snapshot)
    return Verdict(True, "the candidate reproduces the frozen corpus", len(versions),
                   manifest, snapshot)


def verify_document(provider: str, canonical_url: str, normalized_text: str,
                    expected_version_id: str | None) -> dict:
    """One candidate document against its recorded identity, where one survives."""
    derived = version_id_for(provider, canonical_url, normalized_text)
    if not expected_version_id or expected_version_id == "UNKNOWN":
        return {"status": "EXPECTED_HASH_UNKNOWN", "version_id": derived,
                "detail": "no recorded identity survives for this document, so a "
                          "candidate cannot be checked on its own; it can only be "
                          "checked collectively through the manifest hash"}
    if derived == expected_version_id:
        return {"status": "EXACT_MATCH", "version_id": derived,
                "detail": "the candidate reproduces the recorded identity"}
    return {"status": "HASH_MISMATCH", "version_id": derived,
            "detail": f"derived {derived}, but the records expect {expected_version_id}"}


def verify_byte_anchors(normalized_text: str, anchors: list[dict]) -> list[dict]:
    """Closed GOLD evidence spans are exact slices of the historical text.

    They cannot rebuild a document — the gaps between them are gone — but a candidate
    that does not reproduce them at their recorded offsets is refuted before it is worth
    hashing.
    """
    results = []
    for anchor in anchors:
        start, end = anchor["char_start"], anchor["char_end"]
        sliced = normalized_text[start:end]
        results.append({
            "char_start": start, "char_end": end,
            "matches": hashlib.sha256(sliced.encode("utf-8")).hexdigest()
            == anchor["evidence_hash"],
            "recovered_length": len(sliced),
        })
    return results


__all__ = [
    "EXPECTED_DOCUMENTS",
    "MANIFEST_HASH",
    "SNAPSHOT_ID",
    "SNAPSHOT_NAME",
    "Verdict",
    "content_hash_of",
    "manifest_hash_for",
    "snapshot_id_for",
    "source_id_for",
    "verify_byte_anchors",
    "verify_corpus",
    "verify_document",
    "version_id_for",
]
