#!/usr/bin/env python3
"""CORPUS-001: what this environment could be searched for, and what it holds.

The recovery brief asks for a read-only sweep of the *host* machine — Windows user
directories, WSL mounts, Desktop and Downloads, old repository copies, Docker volumes.
This session cannot do that, and the honest first output of this script is which
filesystems actually exist here. It is an isolated cloud VM with a single root disk:
there is no ``/mnt/c``, no ``/mnt/wsl``, no Windows host, no Docker daemon. The
gitignored ``data/raw/`` captures the brief is looking for were never in this container
and cannot be reached from it.

What *can* be done here is done: every accessible filesystem is swept for the project's
provenance anchors, and two oracles are run over the material that did survive.

``version_id``
    ``stable_id("ver", src_id, content_hash)``. 152 of these survive in retrieval
    experiment results and GOLD records.

``chunk_id``
    ``stable_id("chk", version_id, section_path, char_start, char_end, content_hash(text))``
    — a *stronger* oracle, because it binds the document identity to its section
    structure, its offsets and its chunk text at once. 803 survive.

Neither can conjure a missing document. Both mean that if a historical Anthropic capture
is ever produced, it can be accepted or rejected by arithmetic rather than by eye.

Nothing here fetches a live page, restores anything, or runs retrieval.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rag_v1.chunking import chunk_document  # noqa: E402
from rag_v1.config import settings  # noqa: E402
from rag_v1.ids import stable_id  # noqa: E402
from rag_v1.manifest import load_manifest  # noqa: E402
from rag_v1.parsing import parse_file  # noqa: E402

MANIFEST = "data/manifests/v1-openai-anthropic.yaml"
EXPECTED = "experiments/GOLD-001/CORPUS-001-expected-202-manifest.json"
LEDGER = "experiments/GOLD-001/CORPUS-001-recovery-ledger.json"

#: The host locations the brief asks for. Recorded with whether they exist here, so the
#: gap is a fact in the record rather than a claim in a sentence.
HOST_TARGETS = (
    ("/mnt/c/Users", "Windows user directories via a WSL mount"),
    ("/mnt/d", "second Windows drive"),
    ("/mnt/wsl", "WSL interop mount"),
    ("/media", "removable media"),
    ("/var/lib/docker", "Docker volumes"),
    ("/var/run/docker.sock", "Docker daemon"),
)
#: Filesystems that do exist here and were swept.
LOCAL_ROOTS = ("/mnt/user-data", "/home/claude", "/home/user", "/root/.claude/uploads",
               "/tmp", "/var/tmp")
ANCHORS = ("snap_689e336380a054d8039dc35b2c09cd0a",
           "452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17",
           "v1-openai-anthropic", "corpus_snapshot_version", "document_version",
           "2026-08-17 04:46:19")
ARCHIVE_GLOBS = ("*production*rag*.zip", "production_rag_v1.zip", "rag-v1*.zip",
                 "*corpus*.zip", "*rag*backup*.zip", "*.dump", "*.pgdump", "*.backup",
                 "*.sqlite", "*.sqlite3")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def host_reachability() -> dict:
    """Which of the requested host locations exist in this environment."""
    checked = [{"path": path, "description": what, "exists": Path(path).exists()}
               for path, what in HOST_TARGETS]
    try:
        filesystems = subprocess.run(["df", "-PT"], capture_output=True, text=True,
                                     timeout=20).stdout.strip().splitlines()[1:]
    except (OSError, subprocess.SubprocessError):
        filesystems = []
    return {
        "environment": "isolated cloud VM (Claude Code remote execution)",
        "container": Path("/container_info.json").read_text().strip()
        if Path("/container_info.json").exists() else None,
        "host_locations_requested": checked,
        "host_locations_present": [c["path"] for c in checked if c["exists"]],
        "filesystems": [line.split() for line in filesystems],
        "verdict": (
            "No Windows host, no WSL mount and no Docker daemon is reachable from this "
            "session. The gitignored data/raw captures were never in this container. A "
            "host-machine sweep has to be run on the host itself; its results can be "
            "brought back here as an artifact, which is how the earlier host evidence "
            "in this project arrived."),
    }


def sweep(roots: tuple[str, ...]) -> dict:
    """Everything accessible, swept for archives, dumps and provenance anchors."""
    archives = []
    for root in roots:
        if not Path(root).exists():
            continue
        for pattern in ARCHIVE_GLOBS:
            for match in glob.glob(f"{root}/**/{pattern}", recursive=True):
                path = Path(match)
                if not path.is_file():
                    continue
                stat = path.stat()
                archives.append({
                    "path": str(path), "size_bytes": stat.st_size,
                    "mtime": datetime.fromtimestamp(stat.st_mtime, UTC).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()
                    if stat.st_size <= 64 * 1024 * 1024 else None,
                })

    anchors = {}
    for anchor in ANCHORS:
        hits = []
        for root in roots:
            if not Path(root).exists():
                continue
            try:
                found = subprocess.run(["grep", "-rl", anchor, root],
                                       capture_output=True, text=True, timeout=40)
                hits.extend(line for line in found.stdout.splitlines() if line)
            except (OSError, subprocess.SubprocessError):
                continue
        anchors[anchor] = {
            "hits_outside_the_repository": len(hits),
            "directories": sorted({str(Path(h).parent) for h in hits})[:12],
        }
    return {"roots_swept": [r for r in roots if Path(r).exists()],
            "archives_found": archives, "anchor_hits": anchors}


def oracles(openai_sources: Path) -> dict:
    """Harvest the two identity oracles, and run the chunk oracle over the OpenAI half."""
    version_ids, chunk_ids, files = set(), set(), 0
    for pattern in ("experiments/**/*.json", "experiments/**/*.md", "evals/**/*.json",
                    "evals/**/*.jsonl", "docs/**/*.json"):
        for match in glob.glob(str(REPO_ROOT / pattern), recursive=True):
            try:
                text = Path(match).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            found_v = set(re.findall(r"ver_[0-9a-f]{32}", text))
            found_c = set(re.findall(r"chk_[0-9a-f]{40}", text))
            if found_v or found_c:
                files += 1
            version_ids |= found_v
            chunk_ids |= found_c

    sources = [s for s in load_manifest(REPO_ROOT / MANIFEST).sources
               if s.provider == "openai"]
    by_url = {}
    for index, source in enumerate(sources, 1):
        path = openai_sources / f"oa{index:03d}.md"
        if not path.exists():
            continue
        document = parse_file(path)
        src_id = stable_id("src", source.provider, source.canonical_url, length=32)
        version_id = stable_id("ver", src_id, sha(document.normalized_text), length=32)
        chunks = {c.chunk_id for c in chunk_document(
            document, version_id, settings.max_chunk_chars, settings.min_chunk_chars)}
        by_url[source.canonical_url] = {
            "version_id": version_id,
            "version_id_confirmed": version_id in version_ids,
            "chunks": len(chunks),
            "chunks_confirmed": len(chunks & chunk_ids),
            "chunk_id_confirmed": bool(chunks & chunk_ids),
        }
    return {
        "surviving_version_ids": len(version_ids),
        "surviving_chunk_ids": len(chunk_ids),
        "artifact_files_carrying_identities": files,
        "chunk_id_construction": ('stable_id("chk", version_id, section_path, '
                                  "char_start, char_end, content_hash(text))"),
        "why_chunk_id_is_stronger": (
            "it binds the document's version identity to its section structure, its "
            "character offsets and the chunk's own text at once, so a match cannot come "
            "from a document that merely hashes the same"),
        "openai": by_url,
    }


def anthropic_id_search(expected: dict) -> dict:
    """The 40 known Anthropic identities: where they appear, and what they anchor."""
    known = [e for e in expected["entries"]
             if e["provider"] == "anthropic" and e["expected_version_id"] != "UNKNOWN"]
    wanted = {e["expected_version_id"] for e in known}

    locations, carries_text = defaultdict(list), set()
    for pattern in ("experiments/**/*.json", "experiments/**/*.md", "evals/**/*.json",
                    "evals/**/*.jsonl", "docs/**/*.json", "*.md"):
        for match in glob.glob(str(REPO_ROOT / pattern), recursive=True):
            try:
                text = Path(match).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            relative = str(Path(match).relative_to(REPO_ROOT))
            for version_id in wanted & set(re.findall(r"ver_[0-9a-f]{32}", text)):
                locations[version_id].append(relative)
                if '"normalized_text"' in text:
                    carries_text.add(version_id)

    # Verified historical bytes: closed GOLD evidence spans are exact slices of the
    # historical normalized text at known offsets. They cannot rebuild a document, but a
    # candidate capture has to reproduce them byte for byte at those offsets.
    spans = defaultdict(list)
    by_url = {e["source_url"]: e for e in expected["entries"]}
    for pattern in ("evals/review/*.json", "evals/gold/**/*.json"):
        for match in glob.glob(str(REPO_ROOT / pattern), recursive=True):
            try:
                payload = json.loads(Path(match).read_text())
            except (OSError, json.JSONDecodeError):
                continue
            for record in (payload.get("records") or payload.get("case_records") or []):
                url = record.get("source_url")
                if not url or by_url.get(url, {}).get("provider") != "anthropic":
                    continue
                for span in record.get("expected_evidence") or []:
                    if span.get("evidence_text") and span.get("char_start") is not None:
                        spans[url].append({"char_start": span["char_start"],
                                           "char_end": span["char_end"],
                                           "evidence_hash": span["evidence_hash"]})

    anchored = {}
    for url, found in spans.items():
        merged: list[list[int]] = []
        for span in sorted(found, key=lambda s: s["char_start"]):
            if merged and span["char_start"] <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], span["char_end"])
            else:
                merged.append([span["char_start"], span["char_end"]])
        anchored[url] = {
            "expected_version_id": by_url[url]["expected_version_id"],
            "distinct_spans": len({(s["char_start"], s["char_end"]) for s in found}),
            "verified_historical_bytes": sum(b - a for a, b in merged),
            "highest_verified_offset": max(b for _, b in merged),
            "spans": sorted(found, key=lambda s: s["char_start"]),
        }

    return {
        "known_anthropic_identities": len(known),
        "found_somewhere_in_the_repository": len(locations),
        "whose_location_carries_normalized_text": len(carries_text),
        "finding": ("every one of the known identities is recorded, and not one "
                    "recording carries the document body. GOLD records keep evidence "
                    "spans, never the normalized text they were cut from."),
        "documents_with_verified_historical_bytes": len(anchored),
        "total_verified_historical_bytes": sum(
            a["verified_historical_bytes"] for a in anchored.values()),
        "entries": [{**{k: e[k] for k in ("index", "source_url", "document_title",
                                          "expected_version_id",
                                          "expected_version_id_source")},
                     "recorded_in": sorted(set(locations.get(
                         e["expected_version_id"], []))),
                     "byte_anchors": anchored.get(e["source_url"])}
                    for e in known],
    }


def recovery_plan(expected: dict, ledger: dict, id_search: dict) -> dict:
    """The 139, split by whether a candidate could be verified exactly."""
    missing = [r for r in ledger["rows"] if r["status"] == "MISSING_SOURCE"]
    by_url = {e["source_url"]: e for e in expected["entries"]}
    anchored = {e["source_url"]: e["byte_anchors"] for e in id_search["entries"]
                if e.get("byte_anchors")}

    group_a = [r["source_url"] for r in missing
               if by_url[r["source_url"]]["expected_version_id"] != "UNKNOWN"]
    group_b = [r["source_url"] for r in missing
               if by_url[r["source_url"]]["expected_version_id"] == "UNKNOWN"]
    return {
        "total_missing": len(missing),
        "group_A_expected_version_id_known": {
            "count": len(group_a),
            "verification": ("a candidate capture is accepted or rejected outright: "
                             "normalize it with the frozen parser, hash it, derive "
                             'stable_id("ver", src_id, content_hash) and require '
                             "equality with the recorded identity"),
            "additional_anchor": (
                f"{len(anchored)} of them also carry exact historical byte-slices from "
                "closed GOLD evidence, at known offsets — a candidate must reproduce "
                "those bytes at those offsets before it is even worth hashing"),
            "urls": sorted(group_a),
        },
        "group_B_expected_version_id_unknown": {
            "count": len(group_b),
            "verification": ("no per-document oracle survives. A candidate can only be "
                             "checked collectively: assemble all 202 (version_id, "
                             "content_hash) pairs and require the manifest hash to "
                             "match. That is all-or-nothing across the corpus."),
            "urls": sorted(group_b),
        },
        "candidate_sources_in_preference_order": [
            {"source": "original local raw capture under data/raw/",
             "verifiable_exactly": True,
             "status": "not present in this environment; must be searched on the host"},
            {"source": "document_version rows from the original PostgreSQL database",
             "verifiable_exactly": True,
             "status": "no project database found; the local cluster holds only the "
                       "three default databases"},
            {"source": "an archived project ZIP containing data/raw",
             "verifiable_exactly": True,
             "status": "the one archive lead in this project resolved to an early "
                       "scaffold with no corpus"},
            {"source": "a timestamped web archive capture of the 2026-08-17 state",
             "verifiable_exactly": True,
             "status": "archive hosts are not reachable through this session's proxy; "
                       "a capture fetched elsewhere can be verified here"},
            {"source": "provider-owned historical sources with immutable refs",
             "verifiable_exactly": True,
             "status": "this is what made the OpenAI half recoverable; the Anthropic "
                       "docs have no pinned form"},
            {"source": "current live platform.claude.com pages",
             "verifiable_exactly": False,
             "status": "NOT a recovery path. Drift was already measured at 12 of 14 "
                       "sampled documents. Useful only as a comparison lead, and only "
                       "after historical recovery is exhausted."},
        ],
        "what_would_close_the_gate": (
            f"historical bytes for all {len(missing)} documents. Group A can be verified "
            "one at a time; group B only in aggregate, through the manifest hash."),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openai-sources", required=True)
    parser.add_argument("--out-dir", default="experiments/GOLD-001")
    args = parser.parse_args()
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    out_dir = REPO_ROOT / args.out_dir

    expected = json.loads((REPO_ROOT / EXPECTED).read_text())
    ledger = json.loads((REPO_ROOT / LEDGER).read_text())

    host = host_reachability()
    swept = sweep(LOCAL_ROOTS)
    oracle = oracles(Path(args.openai_sources))
    id_search = anthropic_id_search(expected)
    plan = recovery_plan(expected, ledger, id_search)

    unknown = [r["source_url"] for r in ledger["rows"]
               if r["status"] == "EXPECTED_HASH_UNKNOWN"]
    still_unknown = [url for url in unknown
                     if not oracle["openai"].get(url, {}).get("chunk_id_confirmed")]
    openai_status = {
        "expected_hash_unknown_before": len(unknown),
        "confirmed_by_chunk_id_oracle": len(unknown) - len(still_unknown),
        "still_unknown": len(still_unknown),
        "still_unknown_urls": sorted(still_unknown),
        "documents_confirmed_by_chunk_id_overall": sum(
            1 for d in oracle["openai"].values() if d["chunk_id_confirmed"]),
        "finding": ("the 14 are exactly the OpenAI documents that never appeared in any "
                    "logged retrieval result — neither their version_id nor any of "
                    "their chunk ids survives. There is no further mapping to mine; "
                    "the search is exhausted by evidence, not by effort."),
    }

    (out_dir / "CORPUS-001-host-search.json").write_text(json.dumps(
        {"generated_at": now, "host_reachability": host, "accessible_sweep": swept,
         "identity_oracles": {k: v for k, v in oracle.items() if k != "openai"},
         "openai_unknown_identity_status": openai_status},
        indent=2, ensure_ascii=False) + "\n")
    (out_dir / "CORPUS-001-known-anthropic-id-search.json").write_text(
        json.dumps({"generated_at": now, **id_search}, indent=2,
                   ensure_ascii=False) + "\n")
    (out_dir / "CORPUS-001-anthropic-recovery-plan.json").write_text(
        json.dumps({"generated_at": now, **plan}, indent=2, ensure_ascii=False) + "\n")

    print(f"host locations requested: {len(host['host_locations_requested'])}, "
          f"present: {len(host['host_locations_present'])}")
    print(f"accessible roots swept: {len(swept['roots_swept'])}; "
          f"archives found: {len(swept['archives_found'])}")
    print(f"oracles: {oracle['surviving_version_ids']} version ids, "
          f"{oracle['surviving_chunk_ids']} chunk ids")
    print(f"OpenAI unknown identities: {openai_status['expected_hash_unknown_before']} -> "
          f"{openai_status['still_unknown']}")
    print(f"Anthropic known identities located: "
          f"{id_search['found_somewhere_in_the_repository']}/"
          f"{id_search['known_anthropic_identities']}; carrying document text: "
          f"{id_search['whose_location_carries_normalized_text']}")
    print(f"recovery plan: group A {plan['group_A_expected_version_id_known']['count']}, "
          f"group B {plan['group_B_expected_version_id_unknown']['count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
