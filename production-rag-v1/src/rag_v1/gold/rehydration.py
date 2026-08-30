"""Turning saved URLs back into the exact bytes they named — safely, or not at all.

Two halves of the frozen corpus need two different treatments, and both have to end in
the same place: bytes whose provenance is recorded and whose identity is checked by hash
rather than by looking plausible.

**OpenAI (63 documents).** Every saved URL is a GitHub *blob* pinned to a full 40-hex
commit. A commit SHA is immutable — the same SHA names the same bytes forever — so these
are exactly re-fetchable. ``blob_to_raw`` rewrites the blob URL to its
``raw.githubusercontent.com`` form **without touching owner, repo, commit or path**, and
refuses anything that is not pinned to a full SHA. A branch or tag would be a moving
target: ``main`` today is not ``main`` on 2026-08-17, and accepting one would silently
substitute a different document.

**Anthropic (139 documents).** These are live documentation pages with no pinned form.
The only reproducible route to their 2026-08-17 state is a historical capture, and every
candidate must carry where it came from and when. ``HistoricalCandidate`` keeps that
provenance attached to the bytes, so a later reviewer can see which capture a document
came from rather than taking the corpus on trust.

Nothing here fetches, writes, or reconstructs text. These are the pure parts, kept
separate so they can be tested without the network.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

#: A full commit SHA. Nothing shorter is accepted: an abbreviated SHA can become
#: ambiguous as a repository grows, and a branch or tag name is not a fixed target at all.
IMMUTABLE_REF = re.compile(r"^[0-9a-f]{40}$")
_BLOB = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/blob/"
    r"(?P<ref>[^/]+)/(?P<path>.+)$")
RAW_HOST = "raw.githubusercontent.com"


class NotImmutable(ValueError):
    """The URL does not name a fixed set of bytes, so it must not be fetched."""


def is_immutable_ref(ref: str) -> bool:
    """Is this a full commit SHA, rather than a branch or tag?"""
    return bool(IMMUTABLE_REF.match(ref or ""))


def blob_to_raw(url: str) -> str:
    """Rewrite a pinned GitHub blob URL to its raw form, changing nothing else.

    Owner, repo, commit and path are carried across verbatim. Only the host and the
    ``/blob/`` segment differ, because that is the whole transformation: the same commit,
    served as bytes instead of as a rendered page.

    Raises :class:`NotImmutable` for anything not pinned to a full 40-hex SHA.
    """
    match = _BLOB.match(url or "")
    if not match:
        raise NotImmutable(f"not a GitHub blob URL: {url}")
    ref = match.group("ref")
    if not is_immutable_ref(ref):
        raise NotImmutable(
            f"ref {ref!r} is not a full commit SHA; a branch or tag is a moving target "
            "and would not reproduce the 2026-08-17 bytes")
    return (f"https://{RAW_HOST}/{match.group('owner')}/{match.group('repo')}/"
            f"{ref}/{match.group('path')}")


def commit_of(url: str) -> str | None:
    """The commit a blob or raw URL is pinned to, if it is pinned to one."""
    match = _BLOB.match(url or "")
    if match:
        return match.group("ref") if is_immutable_ref(match.group("ref")) else None
    parts = urlparse(url or "")
    if parts.netloc != RAW_HOST:
        return None
    segments = parts.path.strip("/").split("/")
    if len(segments) >= 3 and is_immutable_ref(segments[2]):
        return segments[2]
    return None


def redirect_is_safe(requested: str, final: str) -> bool:
    """Did the fetch land on the same immutable commit it asked for?

    A redirect that keeps the commit is harmless — the host may normalise a path. A
    redirect that drops or changes it has handed back a different document, which is the
    one thing this must never accept silently.
    """
    pinned = commit_of(requested)
    return bool(pinned) and commit_of(final) == pinned


@dataclass
class HistoricalCandidate:
    """One candidate representation of a document, with the provenance to justify it.

    ``source_kind`` says how it was obtained — a pinned repository, an official versioned
    asset, a read-only archive capture, or a current live page used only for comparison.
    ``captured_at`` is the capture's own timestamp, not the time it was downloaded here.
    """

    canonical_url: str
    provenance_url: str
    source_kind: str
    captured_at: str | None = None
    content_hash: str | None = None
    version_id: str | None = None
    notes: dict = field(default_factory=dict)

    #: Kinds that can reproduce a fixed past state. A live page cannot: it is only ever
    #: a comparison candidate, however closely it happens to match.
    REPRODUCIBLE = ("pinned_commit", "official_versioned_asset", "archive_capture")

    def is_reproducible(self) -> bool:
        return self.source_kind in self.REPRODUCIBLE

    def record(self) -> dict:
        """The provenance a reviewer needs, kept beside the bytes rather than implied."""
        return {
            "canonical_url": self.canonical_url,
            "provenance_url": self.provenance_url,
            "source_kind": self.source_kind,
            "captured_at": self.captured_at,
            "content_hash": self.content_hash,
            "version_id": self.version_id,
            "reproducible": self.is_reproducible(),
            **({"notes": self.notes} if self.notes else {}),
        }


__all__ = [
    "IMMUTABLE_REF",
    "RAW_HOST",
    "HistoricalCandidate",
    "NotImmutable",
    "blob_to_raw",
    "commit_of",
    "is_immutable_ref",
    "redirect_is_safe",
]
