"""The four things batch 006 did not persist, and could not be recovered without.

Batch 007's calibration pilot is blocked on a set that was *counted and thrown away*:
``removed["unbuildable"] += 1`` recorded 2482 facts reaching no builder and kept not one
of their identities. The corpus that could re-derive them is not in this environment, and
an exhaustive search found no copy of it. A number is not a record. Nothing here can
recover that set — this module exists so the next batch cannot lose it the same way.

Four safeguards, each answering a question the blocker asked and batch 006 could not:

``UnbuildableLog``
    *Which spans reached no builder?* Records the identity of every fact a builder
    declines, so the set survives the run that produced it.

``fingerprint`` / ``verify_fingerprint``
    *Is this corpus the frozen one?* The snapshot id is a hash over every version's
    content hash — the same construction ``rag_v1.snapshot.create_snapshot`` uses — so a
    restored corpus proves its identity by arithmetic rather than by the label somebody
    typed on the restore.

``verify_restored_corpus``
    *Did the restore land the same bytes?* Re-reads every closed span at its recorded
    offsets and re-hashes it. 137 spans across batches 003-006 carry an ``evidence_hash``
    over text that cannot have drifted, so a restore has 137 independent chances to fail
    honestly instead of one chance to look plausible.

``select_pilot_cases``
    *Why these ten?* Deterministic selection with the basis recorded per case, so the
    choice is auditable and re-running it cannot quietly return a different ten.

None of this authors anything, approves anything, or touches a closed batch.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable, Sequence
from typing import Any

from rag_v1.ids import config_hash, stable_id

#: Why a builder declined a fact. ``NO_BUILDER`` is the preregistered pilot input: no
#: builder could express the span. It is deliberately distinct from a semantic-gate
#: failure, which paraphrasing does not fix and which the pilot must not draw from.
NO_BUILDER = "NO_BUILDER"
SEMANTIC_GATE = "SEMANTIC_GATE"


def span_key(version_id: str, char_start: int, char_end: int) -> tuple[str, int, int]:
    """The identity of a span: which document version, and which characters of it."""
    return (str(version_id), int(char_start), int(char_end))


class UnbuildableLog:
    """Every fact that reached no builder, with enough identity to find it again.

    Batch 006 incremented a counter. The count was faithful and useless: it could not say
    *which* 2482, so the set could not be re-derived once the corpus went away. This
    records the span's version and offsets — which is what makes it findable in a
    restored corpus — alongside the text and the reason.

    Ordering is insertion order and duplicates collapse on span identity, so a log is
    comparable across runs: two runs over the same corpus produce the same manifest.
    """

    def __init__(self) -> None:
        self._entries: dict[tuple[str, int, int], dict] = {}

    def record(self, fact: dict, reason: str = NO_BUILDER) -> None:
        """Note that ``fact`` produced no candidate, and why."""
        key = span_key(fact["version_id"], fact["char_start"], fact["char_end"])
        if key in self._entries:
            return
        text = fact.get("evidence_text", "")
        self._entries[key] = {
            "version_id": key[0],
            "char_start": key[1],
            "char_end": key[2],
            "evidence_text": text,
            "evidence_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "evidence_char_length": key[2] - key[1],
            "reason": reason,
        }

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def entries(self) -> list[dict]:
        return list(self._entries.values())

    def of_reason(self, reason: str) -> list[dict]:
        return [e for e in self._entries.values() if e["reason"] == reason]

    def manifest(self, *, corpus_snapshot: str, batch: int) -> dict:
        """The record that makes this set re-derivable after the run ends."""
        entries = self.entries
        by_reason: dict[str, int] = {}
        for entry in entries:
            by_reason[entry["reason"]] = by_reason.get(entry["reason"], 0) + 1
        return {
            "corpus_snapshot": corpus_snapshot,
            "batch": batch,
            "total": len(entries),
            "by_reason": by_reason,
            "note": ("Identities, not a count. Batch 006 recorded only a count and its "
                     "unbuildable set could not be re-derived once the corpus was "
                     "unavailable."),
            "entries": entries,
        }


def chunking_config_from_settings() -> dict:
    """The chunking config in the shape the snapshot id is built from.

    The key names are part of the hash, so a caller writing ``{"max": ...}`` would
    compute a different fingerprint and conclude a good restore was bad. Building it in
    one place is cheaper than debugging that.
    """
    from rag_v1.config import settings
    return {"max_chunk_chars": settings.max_chunk_chars,
            "min_chunk_chars": settings.min_chunk_chars}


def fingerprint(versions: Iterable[tuple[str, str]], *, name: str,
                parser_version: str, chunking_config: dict) -> str:
    """The snapshot id a corpus of these versions must produce.

    ``versions`` is (version_id, content_hash) for every current document version, in the
    order the snapshot was built from — ``ORDER BY version_id``. This mirrors
    ``rag_v1.snapshot.create_snapshot`` exactly: change one document and the id changes,
    which is what makes it a fingerprint rather than a name.
    """
    manifest_payload = [{"version_id": v, "content_hash": h} for v, h in versions]
    manifest_hash = config_hash({"versions": manifest_payload})
    chunking_hash = config_hash(chunking_config)
    return stable_id("snap", name, manifest_hash, parser_version, chunking_hash,
                     length=32)


def verify_fingerprint(expected_snapshot_id: str, versions: Iterable[tuple[str, str]],
                       *, name: str, parser_version: str,
                       chunking_config: dict) -> dict:
    """Does this corpus hash to the snapshot it claims to be?

    A restore that cannot answer yes is not the frozen corpus, whatever the row in
    ``corpus_snapshot`` says — that row is a label, and a label is written by whoever did
    the restore.
    """
    computed = fingerprint(versions, name=name, parser_version=parser_version,
                           chunking_config=chunking_config)
    return {
        "expected": expected_snapshot_id,
        "computed": computed,
        "matches": computed == expected_snapshot_id,
        "documents": len(list(versions)) if isinstance(versions, (list, tuple)) else None,
    }


def verify_restored_corpus(records: Sequence[dict],
                           read_span: Callable[[str, int, int], str | None]) -> dict:
    """Re-read every closed span from a restored corpus and re-hash it.

    ``read_span(version_id, char_start, char_end)`` returns the restored text at those
    offsets, or ``None`` when that version is absent. Every span must reproduce its
    recorded ``evidence_hash``.

    A single mismatch means the restore is not the frozen corpus and nothing downstream
    may proceed: offsets that have shifted by one character still return text, and the
    text still reads plausibly, which is exactly why this is checked by hash and not by
    eye.
    """
    checked = matched = 0
    mismatches: list[dict] = []
    missing: list[dict] = []
    for record in records:
        for span in record.get("expected_evidence") or []:
            if "evidence_hash" not in span:
                continue
            checked += 1
            where = {"candidate_id": record.get("candidate_id"),
                     "version_id": span.get("version_id"),
                     "char_start": span.get("char_start"),
                     "char_end": span.get("char_end")}
            body = read_span(span["version_id"], span["char_start"], span["char_end"])
            if body is None:
                missing.append({**where, "reason": "version not present in the restore"})
                continue
            digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
            if digest == span["evidence_hash"]:
                matched += 1
            else:
                mismatches.append({**where, "expected_hash": span["evidence_hash"],
                                   "computed_hash": digest})
    return {
        "spans_checked": checked,
        "spans_matched": matched,
        "mismatches": mismatches,
        "missing": missing,
        "verified": checked > 0 and matched == checked,
    }


def select_pilot_cases(unbuildable: Sequence[dict], *, size: int = 10,
                       already_spent: Iterable[tuple[str, int, int]] = (),
                       reason: str = NO_BUILDER) -> dict:
    """Choose the pilot's cases deterministically, and say why each was chosen.

    Only spans that reached no builder are eligible: a span that failed a semantic gate
    failed for a reason paraphrasing does not fix, and the preregistration excludes it.
    Spans a closed batch already spent are excluded too.

    Selection is by sorted span identity rather than by corpus order, so the same input
    returns the same ten however the miners happened to enumerate them. A convenience
    sample that changes between runs is not a calibration.
    """
    spent = {span_key(*k) for k in already_spent}
    eligible = sorted(
        (e for e in unbuildable
         if e.get("reason") == reason
         and span_key(e["version_id"], e["char_start"], e["char_end"]) not in spent),
        key=lambda e: (e["version_id"], e["char_start"], e["char_end"]))
    chosen = eligible[:size]
    return {
        "requested": size,
        "eligible": len(eligible),
        "selected": len(chosen),
        "short": len(chosen) < size,
        "selection_rule": ("spans that reached no builder, excluding any span already "
                           "spent by a closed batch, ordered by (version_id, "
                           "char_start, char_end) and taken from the front"),
        "cases": [
            {**case, "selection_basis":
                f"reached no builder in the recorded run; not spent by any closed "
                f"batch; rank {index + 1} of {len(eligible)} eligible by span order"}
            for index, case in enumerate(chosen)],
    }


def pilot_thresholds_unmet(results: dict[str, Any]) -> list[str]:
    """Which of the four preregistered thresholds a pilot result fails.

    Present so no report can call a pilot passed without the numbers saying so. An empty
    list means every threshold is met; a pilot that was not run fails all four, because
    unmeasured is not met.
    """
    unmet = []
    sound = results.get("independently_judged_factually_sound")
    if not isinstance(sound, int) or sound < 8:
        unmet.append("independently_judged_factually_sound >= 8 of 10")
    for field in ("unsupported_claims", "relation_direction_reversals",
                  "scope_broadening"):
        value = results.get(field)
        if value != 0:
            unmet.append(f"{field} == 0")
    return unmet


__all__ = [
    "NO_BUILDER",
    "chunking_config_from_settings",
    "SEMANTIC_GATE",
    "UnbuildableLog",
    "fingerprint",
    "pilot_thresholds_unmet",
    "select_pilot_cases",
    "span_key",
    "verify_fingerprint",
    "verify_restored_corpus",
]
