#!/usr/bin/env python3
"""Attempt a quarantined rehydration of the frozen corpus, and certify it or reject it.

The frozen snapshot id is **content-derived**, and that is the whole basis for this
script. Reading ``rag_v1.ingest`` and ``rag_v1.snapshot``, the chain is:

    src_id_i      = stable_id("src", provider_i.lower(), canonical_url_i)
    content_hash_i= sha256(normalized_text_i)
    version_id_i  = stable_id("ver", src_id_i, content_hash_i)
    manifest_hash = sha256(json({"versions": [{version_id, content_hash} … ×202]}))
    snapshot_id   = stable_id("snap", name, manifest_hash, PARSER_VERSION, chunking_hash)

Nothing in it is random, sequential, or clock-derived. ``captured_at`` is stored on the
row but is *not* an input to any id. Every input except the document text is already
persisted: provider and canonical_url in the manifest, ``PARSER_VERSION`` in the parser,
the chunking budget in settings.

So ``snap_689e336380a054d8039dc35b2c09cd0a`` is a **complete authoritative digest over
all 202 normalized texts at once**. Reproducing it certifies the whole corpus
cryptographically — not by counts, not by the 137 sampled closed spans, both of which
this script computes only as diagnostics and neither of which it will ever accept as
proof.

**Fail-closed, and quarantined.** Fetched bytes are written only under a quarantine
directory outside the repository. Nothing is written to ``data/``, no database is
touched, and no restore happens unless the exact fingerprint reproduces. A partial match
is a failure: 201 of 202 documents identical is a different corpus, and the script says
so rather than calling it recovered.

No retrieval system is run. SYSTEM-A and SYSTEM-B are not executed.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rag_v1.gold.provenance import (  # noqa: E402
    FROZEN_CAPTURE_SHAPE,
    verify_corpus_shape,
    verify_restored_corpus,
)
from rag_v1.ids import config_hash, stable_id  # noqa: E402
from rag_v1.manifest import load_manifest  # noqa: E402
from rag_v1.parsing import PARSER_VERSION, parse_file  # noqa: E402

TARGET_SNAPSHOT = FROZEN_CAPTURE_SHAPE["snapshot_id"]
MANIFEST = REPO_ROOT / "data/manifests/v1-openai-anthropic.yaml"
#: The snapshot name is the one id input not persisted in any artifact. It is a free
#: parameter, not a weakness: a match is a 256-bit coincidence whichever name produced
#: it, so candidates are simply tried. The first is the CLI's default.
CANDIDATE_NAMES = ("v1-seed", "v1", "v1-openai-anthropic", "production-rag-v1", "seed")
USER_AGENT = "production-rag-v1 quarantined-rehydration-verifier (read-only)"


def chunking_config() -> dict:
    from rag_v1.config import settings
    return {"max_chunk_chars": settings.max_chunk_chars,
            "min_chunk_chars": settings.min_chunk_chars}


def snapshot_id_for(versions: list[tuple[str, str]], name: str) -> str:
    """Recompute the snapshot id exactly as ``create_snapshot`` would."""
    payload = [{"version_id": v, "content_hash": h} for v, h in versions]
    return stable_id("snap", name, config_hash({"versions": payload}), PARSER_VERSION,
                     config_hash(chunking_config()), length=32)


def closed_records() -> list[dict]:
    records: list[dict] = []
    for path in sorted(glob.glob(str(REPO_ROOT / "evals/review/gold_review_batch_00*_final.json"))):
        records.extend(json.loads(Path(path).read_text())["records"])
    return records


def fetch(url: str, timeout: int) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        return response.read()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quarantine", required=True,
                        help="directory for fetched bytes; must be outside the repository")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--limit", type=int, default=0,
                        help="fetch only the first N sources (a reachability probe; "
                             "certification always requires all 202)")
    parser.add_argument("--report", default="")
    args = parser.parse_args()

    quarantine = Path(args.quarantine).resolve()
    if quarantine == REPO_ROOT or REPO_ROOT in quarantine.parents:
        raise SystemExit("refusing to run: the quarantine directory must be outside the "
                         "repository, so fetched bytes can never be mistaken for corpus")
    quarantine.mkdir(parents=True, exist_ok=True)

    sources = load_manifest(MANIFEST).sources
    print(f"manifest: {len(sources)} sources; target {TARGET_SNAPSHOT}")
    if len(sources) != FROZEN_CAPTURE_SHAPE["documents"]:
        raise SystemExit(f"refusing to run: manifest has {len(sources)} sources, expected "
                         f"{FROZEN_CAPTURE_SHAPE['documents']}")

    selected = sources[:args.limit] if args.limit else sources
    fetched, failures = [], []
    for index, source in enumerate(selected, 1):
        url = source.metadata.get("fetched_from") or source.canonical_url
        target = quarantine / f"{index:04d}{Path(url).suffix or '.md'}"
        try:
            body = fetch(url, args.timeout)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
                OSError) as error:
            failures.append({"url": url, "error": str(error)[:200]})
            continue
        target.write_bytes(body)
        try:
            document = parse_file(target)
        except Exception as error:  # noqa: BLE001 - a parse failure is a fetch outcome
            failures.append({"url": url, "error": f"parse failed: {error}"[:200]})
            continue
        digest = hashlib.sha256(document.normalized_text.encode("utf-8")).hexdigest()
        src_id = stable_id("src", source.provider.lower(), source.canonical_url,
                           length=32)
        fetched.append({
            "canonical_url": source.canonical_url,
            "provider": source.provider,
            "version_id": stable_id("ver", src_id, digest, length=32),
            "content_hash": digest,
            "normalized_text": document.normalized_text,
        })
        if index % 25 == 0 or index == len(selected):
            print(f"  fetched {index}/{len(selected)} ({len(failures)} failed)")

    result = {
        "target_snapshot": TARGET_SNAPSHOT,
        "sources_in_manifest": len(sources),
        "attempted": len(selected),
        "fetched_ok": len(fetched),
        "fetch_failures": len(failures),
        "failure_examples": failures[:5],
        "certified": False,
        "verdict": "",
    }

    # Certification requires every document. A partial crawl is not a corpus, and this
    # is checked before anything else so a short crawl can never look like a near miss.
    if len(fetched) != FROZEN_CAPTURE_SHAPE["documents"]:
        result["verdict"] = (
            f"NOT CERTIFIED — {len(fetched)} of {FROZEN_CAPTURE_SHAPE['documents']} "
            "documents fetched and parsed. The snapshot id hashes all 202 together, so a "
            "partial crawl cannot be certified and is not recovered data.")
    else:
        versions = sorted((f["version_id"], f["content_hash"]) for f in fetched)
        computed = {name: snapshot_id_for(versions, name) for name in CANDIDATE_NAMES}
        match = next((n for n, s in computed.items() if s == TARGET_SNAPSHOT), None)
        result["computed_snapshot_ids"] = computed
        result["certified"] = match is not None
        result["verdict"] = (
            f"CERTIFIED — the rehydrated corpus reproduces {TARGET_SNAPSHOT} under "
            f"snapshot name {match!r}."
            if match else
            "NOT CERTIFIED — all 202 documents fetched, but none of the candidate "
            "snapshot names reproduces the frozen fingerprint. The live pages have "
            "drifted from the 2026-08-17 capture. This is not the frozen corpus.")

        # Diagnostics only. Recorded to show *how far* the crawl is, never to accept it.
        by_version = {f["version_id"]: f["normalized_text"] for f in fetched}
        result["diagnostics"] = {
            "shape": verify_corpus_shape(len(fetched)),
            "closed_spans": verify_restored_corpus(
                closed_records(),
                lambda v, s, e: (by_version[v][s:e] if v in by_version else None)),
            "note": ("Diagnostics never certify. Only the fingerprint does; these are "
                     "recorded so a failure can be read rather than guessed at."),
        }

    print("\n" + result["verdict"])
    if args.report:
        Path(args.report).write_text(json.dumps(
            {k: v for k, v in result.items() if k != "normalized_text"},
            indent=2, ensure_ascii=False) + "\n")
        print(f"report written to {args.report}")

    if not result["certified"]:
        shutil.rmtree(quarantine, ignore_errors=True)
        print(f"quarantine discarded: {quarantine}")
        print("state unchanged; nothing was restored and no project artifact was written.")
        return 1
    print("fingerprint reproduced. Restore may proceed through the existing verifier.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
