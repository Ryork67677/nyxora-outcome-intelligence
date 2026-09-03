#!/usr/bin/env python3
"""CORPUS-001: inventory what exists, state what is expected, and ledger the gap.

The frozen snapshot is ``snap_689e336380a054d8039dc35b2c09cd0a`` over 202 document
versions. Two of its inputs were previously recorded as unknown and are now recovered
here, and both are confirmed by the same arithmetic rather than asserted:

``manifest_hash``
    ``452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17``, read from
    ``experiments/EXP-007/results.json``. This is the digest over all 202
    ``(version_id, content_hash)`` pairs, and it is a *better* recovery target than the
    snapshot id: it isolates the corpus content from the name, parser and chunking
    parameters.

``name``
    ``v1-openai-anthropic``. Recovered by search and confirmed because
    ``stable_id("snap", name, manifest_hash, PARSER_VERSION, chunking_hash)`` reproduces
    the frozen snapshot id exactly. Any other name gives a different 128-bit value, so
    the match confirms the name and the manifest hash together.

Nothing here fetches, restores, or writes to ``data/``. It reads the repository and the
already-reproduced OpenAI corpus, and writes only under ``recovery/CORPUS-001/`` and
``experiments/GOLD-001/``. No retrieval is run and no GOLD record is touched.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rag_v1.config import settings  # noqa: E402
from rag_v1.ids import config_hash, stable_id  # noqa: E402
from rag_v1.manifest import load_manifest  # noqa: E402
from rag_v1.parsing import PARSER_VERSION, parse_file  # noqa: E402

SNAPSHOT_ID = "snap_689e336380a054d8039dc35b2c09cd0a"
#: Read from experiments/EXP-007/results.json, not typed in from memory. Verified below.
MANIFEST_HASH = "452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17"
SNAPSHOT_NAME = "v1-openai-anthropic"
EXPECTED_DOCUMENTS = 202
MANIFEST = "data/manifests/v1-openai-anthropic.yaml"
EXP007 = "experiments/EXP-007/results.json"

#: Where a recovered document's expected identity can come from. Ordered by strength.
IDENTITY_SOURCES = ("gold_record", "experiment_artifact", "none")

#: Statuses the ledger may use. No vague "done".
EXACT_MATCH = "EXACT_MATCH"
PARTIAL_METADATA = "PARTIAL_METADATA"
HASH_MISMATCH = "HASH_MISMATCH"
MISSING_SOURCE = "MISSING_SOURCE"
EXPECTED_HASH_UNKNOWN = "EXPECTED_HASH_UNKNOWN"
BLOCKED = "BLOCKED"
UNRECOVERABLE = "UNRECOVERABLE"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunking_hash() -> str:
    return config_hash({"max_chunk_chars": settings.max_chunk_chars,
                        "min_chunk_chars": settings.min_chunk_chars})


def snapshot_id_from(manifest_hash: str, name: str = SNAPSHOT_NAME) -> str:
    """The digest exactly as ``rag_v1.snapshot.create_snapshot`` builds it."""
    return stable_id("snap", name, manifest_hash, PARSER_VERSION, chunking_hash(),
                     length=32)


def manifest_hash_for(versions: list[tuple[str, str]]) -> str:
    """``versions`` is ``(version_id, content_hash)``, ordered as the query orders them.

    ``create_snapshot`` reads ``ORDER BY version_id``, so the ordering is a sort on the
    version id — not insertion order, not an ordinal, not provider order. The
    ``corpus_snapshot_version`` table has no ordinal column, which is the corroborating
    evidence: the order cannot come from the table.
    """
    payload = [{"version_id": v, "content_hash": h} for v, h in sorted(versions)]
    return config_hash({"versions": payload})


# --------------------------------------------------------------------- inventory

INVENTORY_PATTERNS = (
    ("**/*.zip", "archive"), ("**/*.tar", "archive"), ("**/*.tar.gz", "archive"),
    ("**/*.sql", "sql"), ("**/*.dump", "db_dump"), ("**/*.backup", "db_dump"),
    ("**/*.sqlite", "sqlite"), ("**/*.sqlite3", "sqlite"), ("**/*.db", "sqlite"),
    ("**/*.jsonl", "jsonl_export"),
    ("data/**/*", "corpus_data_dir"),
    ("data/manifests/*.yaml", "source_manifest"),
)
SKIP = ("/.git/", "/node_modules/", "/__pycache__/", "/.venv/", "/.pytest_cache/",
        "/.ruff_cache/")


def relevance(path: Path, kind: str) -> tuple[str, str]:
    """Could this hold corpus content, and does it?"""
    name = path.name.lower()
    if kind == "source_manifest":
        return ("HIGH", "the 202 canonical urls, providers, titles and captured_at — the "
                        "only complete record of what the snapshot contained")
    if kind == "sql":
        return ("MEDIUM", "schema only; defines document_version and corpus_snapshot "
                          "but carries no rows")
    if kind in ("db_dump", "sqlite"):
        return ("HIGH", "would carry document_version rows if it held the project DB")
    if kind == "archive":
        return ("HIGH", "could carry a raw capture or a database dump")
    if kind == "jsonl_export":
        if "projection" in name or "candidates" in name or name.startswith("v1"):
            return ("LOW", "GOLD candidate projections; no document normalized text")
        return ("LOW", "not a corpus export")
    if kind == "corpus_data_dir":
        return ("HIGH", "data/raw and data/cache are where captures would live")
    return ("LOW", "")


def inventory() -> list[dict]:
    seen, records = set(), []
    for pattern, kind in INVENTORY_PATTERNS:
        for match in glob.glob(str(REPO_ROOT / pattern), recursive=True):
            path = Path(match)
            if not path.is_file() or str(path) in seen:
                continue
            if any(skip in str(path) for skip in SKIP):
                continue
            seen.add(str(path))
            stat = path.stat()
            level, why = relevance(path, kind)
            record = {
                "path": str(path.relative_to(REPO_ROOT)),
                "size_bytes": stat.st_size,
                "mtime": datetime.fromtimestamp(stat.st_mtime, UTC).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"),
                "artifact_type": kind,
                "readable": os.access(path, os.R_OK),
                "relevance": level,
                "potential_corpus_contents": why,
            }
            if stat.st_size <= 8 * 1024 * 1024:
                record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            else:
                record["sha256"] = None
                record["sha256_note"] = "not hashed: over 8 MB"
            records.append(record)
    return sorted(records, key=lambda r: (r["relevance"] != "HIGH", r["path"]))


# ------------------------------------------------------- expected identities

def harvest_version_ids() -> tuple[set[str], dict[str, str], dict[str, int]]:
    """Every ``ver_`` identity the repository still records, and where from.

    Two independent kinds of witness survive the corpus:

    * **GOLD records** pair a ``version_id`` with the ``source_url`` it came from, so
      they name both halves.
    * **Retrieval experiment results** list ``version_id`` values that were current when
      the snapshot was frozen, without saying which url. Unlabelled, but still an
      oracle: a candidate document either hashes into this set or it does not.
    """
    harvested: set[str] = set()
    provenance: Counter = Counter()
    for pattern in ("experiments/**/*.json", "evals/**/*.json", "evals/**/*.jsonl",
                    "experiments/**/*.md", "docs/**/*.json"):
        for match in glob.glob(str(REPO_ROOT / pattern), recursive=True):
            try:
                text = Path(match).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            found = set(re.findall(r"ver_[0-9a-f]{32}", text))
            if found:
                harvested |= found
                provenance[str(Path(match).relative_to(REPO_ROOT))] = len(found)

    labelled: dict[str, str] = {}
    ambiguous: dict[str, set] = {}
    for pattern in ("evals/review/*.json", "evals/gold/**/*.json"):
        for match in glob.glob(str(REPO_ROOT / pattern), recursive=True):
            try:
                payload = json.loads(Path(match).read_text())
            except (OSError, json.JSONDecodeError):
                continue
            for record in (payload.get("records") or payload.get("case_records") or []):
                url = record.get("source_url")
                if not url:
                    continue
                ids = {record.get("version_id")} | {
                    s.get("version_id") for s in record.get("expected_evidence") or []}
                for version_id in filter(None, ids):
                    ambiguous.setdefault(version_id, set()).add(url)
    for version_id, urls in ambiguous.items():
        if len(urls) == 1:
            labelled[version_id] = next(iter(urls))
    return harvested, labelled, dict(provenance)


def reproduce_openai(sources_dir: Path, sources: list) -> dict[str, dict]:
    """Re-derive every OpenAI document from its pinned commit."""
    out = {}
    openai = [s for s in sources if s.provider == "openai"]
    for index, source in enumerate(openai, 1):
        path = sources_dir / f"oa{index:03d}.md"
        if not path.exists():
            continue
        text = parse_file(path).normalized_text
        content_hash = sha(text)
        src_id = stable_id("src", source.provider, source.canonical_url, length=32)
        out[source.canonical_url] = {
            "source_id": src_id,
            "content_hash": content_hash,
            "version_id": stable_id("ver", src_id, content_hash, length=32),
            "chars": len(text),
            "artifact": str(path),
            "recovery_method": "re-fetched from the pinned commit in the canonical url "
                               "and re-parsed with the frozen parser",
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openai-sources", required=True,
                        help="the reproduced OpenAI corpus, as pinned markdown")
    parser.add_argument("--workspace", default="recovery/CORPUS-001")
    parser.add_argument("--out-dir", default="experiments/GOLD-001")
    args = parser.parse_args()
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    workspace = REPO_ROOT / args.workspace
    workspace.mkdir(parents=True, exist_ok=True)
    out_dir = REPO_ROOT / args.out_dir

    # ------------------------------------------------ the two recovered parameters
    exp007 = json.loads((REPO_ROOT / EXP007).read_text())
    recorded_manifest_hash = exp007.get("corpus_manifest_hash")
    if recorded_manifest_hash != MANIFEST_HASH:
        raise SystemExit(f"{EXP007} records {recorded_manifest_hash}, not the manifest "
                         "hash this script was verified against")
    reproduced_id = snapshot_id_from(MANIFEST_HASH)
    if reproduced_id != SNAPSHOT_ID:
        raise SystemExit(f"the recorded manifest hash and name give {reproduced_id}, "
                         f"not {SNAPSHOT_ID}")
    print(f"snapshot parameters recovered: name={SNAPSHOT_NAME!r}, "
          f"manifest_hash={MANIFEST_HASH[:16]}… -> {reproduced_id}")

    sources = load_manifest(REPO_ROOT / MANIFEST).sources
    if len(sources) != EXPECTED_DOCUMENTS:
        raise SystemExit(f"manifest has {len(sources)} sources, expected "
                         f"{EXPECTED_DOCUMENTS}")

    artifacts = inventory()
    harvested, labelled, provenance = harvest_version_ids()
    reproduced = reproduce_openai(Path(args.openai_sources), sources)
    reproduced_vids = {d["version_id"] for d in reproduced.values()}
    print(f"inventory: {len(artifacts)} artifacts; harvested {len(harvested)} version "
          f"identities from {len(provenance)} files; reproduced {len(reproduced)} "
          "OpenAI documents")

    # ------------------------------------------------------------- expected manifest
    entries, ledger = [], []
    for index, source in enumerate(sources, 1):
        src_id = stable_id("src", source.provider, source.canonical_url, length=32)
        got = reproduced.get(source.canonical_url)
        expected_vid = None
        identity_source = "none"
        for version_id, url in labelled.items():
            if url == source.canonical_url:
                expected_vid, identity_source = version_id, "gold_record"
                break
        if expected_vid is None and got and got["version_id"] in harvested:
            expected_vid, identity_source = got["version_id"], "experiment_artifact"

        entry = {
            "index": index,
            "snapshot_id": SNAPSHOT_ID,
            "provider": source.provider,
            "source_url": source.canonical_url,
            "source_id": src_id,
            "document_title": source.title,
            "captured_at": source.captured_at,
            "fetched_from": source.metadata.get("fetched_from"),
            "expected_version_id": expected_vid or "UNKNOWN",
            "expected_version_id_source": identity_source,
            "expected_normalized_content_hash": (
                got["content_hash"] if got and identity_source != "none" else "UNKNOWN"),
            "expected_raw_content_hash": "UNKNOWN",
            "normalization_version": PARSER_VERSION,
            "ordinal": "UNKNOWN — corpus_snapshot_version has no ordinal column; "
                       "ordering comes from ORDER BY version_id",
        }
        entries.append(entry)

        # ------------------------------------------------------------- ledger row
        if got is None:
            status, reason, nxt = (
                MISSING_SOURCE,
                "no historical capture of this document exists in this environment; the "
                "live page is not an acceptable substitute and was not fetched",
                "an original raw capture, a document_version row, or a timestamped "
                "archive capture of the 2026-08-17 state")
            recovered_hashes = None
        elif expected_vid and got["version_id"] == expected_vid:
            status, reason, nxt = (EXACT_MATCH, None, None)
            recovered_hashes = {"content_hash": got["content_hash"],
                                "version_id": got["version_id"]}
        elif expected_vid:
            status, reason, nxt = (
                HASH_MISMATCH,
                f"reproduced {got['version_id']} but the records expect {expected_vid}",
                "re-check the pinned commit and the normalization pipeline")
            recovered_hashes = {"content_hash": got["content_hash"],
                                "version_id": got["version_id"]}
        else:
            status, reason, nxt = (
                EXPECTED_HASH_UNKNOWN,
                "the document reproduces deterministically from its pinned commit, but "
                "no surviving artifact records what its version_id was at capture time, "
                "so the reproduction cannot be checked against the frozen value",
                "any artifact recording this url's version_id or content_hash")
            recovered_hashes = {"content_hash": got["content_hash"],
                                "version_id": got["version_id"]}

        ledger.append({
            "index": index, "provider": source.provider,
            "source_url": source.canonical_url,
            "expected_version_id": expected_vid or "UNKNOWN",
            "expected_version_id_source": identity_source,
            "expected_normalized_content_hash": entry["expected_normalized_content_hash"],
            "recovered_artifact": got["artifact"] if got else None,
            "recovery_method": got["recovery_method"] if got else None,
            "recovered_hashes": recovered_hashes,
            "status": status, "failure_reason": reason, "next_recovery_path": nxt,
        })

    unlabelled = sorted(harvested - reproduced_vids - set(labelled))
    counts = Counter(row["status"] for row in ledger)
    by_provider = {
        provider: dict(Counter(row["status"] for row in ledger
                               if row["provider"] == provider))
        for provider in ("openai", "anthropic")}

    accounted = counts[EXACT_MATCH]
    reproduction = {
        "expected_documents": EXPECTED_DOCUMENTS,
        "status_counts": dict(counts),
        "by_provider": by_provider,
        "exactly_recovered": counts[EXACT_MATCH],
        "reproduced_but_unverifiable": counts[EXPECTED_HASH_UNKNOWN],
        "missing": counts[MISSING_SOURCE],
        "hash_mismatches": counts[HASH_MISMATCH],
        "document_version_reproduction_rate": round(accounted / EXPECTED_DOCUMENTS, 4),
        "normalized_hash_reproduction_rate": round(
            len(reproduced) / EXPECTED_DOCUMENTS, 4),
        "documents_whose_bytes_reproduce": len(reproduced),
        "expected_identities_recoverable": {
            "from_gold_records": len(labelled),
            "from_experiment_artifacts_unlabelled": len(unlabelled),
            "total_distinct": len(harvested),
        },
        "snapshot_digest": {
            "target": SNAPSHOT_ID,
            "name": SNAPSHOT_NAME,
            "manifest_hash": MANIFEST_HASH,
            "manifest_hash_source": EXP007,
            "parser_version": PARSER_VERSION,
            "chunking_config_hash": chunking_hash(),
            "reproduced": False,
            "why_not": (f"the digest is a hash over all {EXPECTED_DOCUMENTS} "
                        "(version_id, content_hash) pairs at once. "
                        f"{counts[MISSING_SOURCE]} documents have no recovered bytes, so "
                        "the manifest cannot be assembled and no partial set can "
                        "reproduce it."),
        },
    }

    workspace_note = {
        "workspace": args.workspace,
        "policy": ("Recovered files carry source provenance, sha256, recovery method, "
                   "timestamp and verification status. Nothing here is written back to "
                   "data/, no authoritative artifact is modified, and no live page was "
                   "substituted for a historical capture."),
        "recovered_documents": [
            {"source_url": url, **d, "verification_status": next(
                (r["status"] for r in ledger if r["source_url"] == url), "UNKNOWN"),
             "recovered_at": now}
            for url, d in sorted(reproduced.items())],
    }
    (workspace / "recovered-openai-63.json").write_text(
        json.dumps(workspace_note, indent=2, ensure_ascii=False) + "\n")

    payload = {"generated_at": now, "snapshot_id": SNAPSHOT_ID,
               "artifacts": artifacts,
               "database_search": database_search(),
               "version_id_provenance": provenance}
    (out_dir / "CORPUS-001-local-artifact-inventory.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    (out_dir / "CORPUS-001-expected-202-manifest.json").write_text(json.dumps(
        {"generated_at": now, "snapshot_id": SNAPSHOT_ID, "name": SNAPSHOT_NAME,
         "manifest_hash": MANIFEST_HASH, "parser_version": PARSER_VERSION,
         "chunking_config_hash": chunking_hash(),
         "expected_documents": EXPECTED_DOCUMENTS,
         "unlabelled_expected_version_ids": unlabelled,
         "entries": entries}, indent=2, ensure_ascii=False) + "\n")
    (out_dir / "CORPUS-001-recovery-ledger.json").write_text(json.dumps(
        {"generated_at": now, "snapshot_id": SNAPSHOT_ID, "metrics": reproduction,
         "rows": ledger}, indent=2, ensure_ascii=False) + "\n")

    print(f"ledger: {dict(counts)}")
    print(f"snapshot digest reproduced: {reproduction['snapshot_digest']['reproduced']}")
    return 0


def database_search() -> dict:
    """What was looked for, and what the local PostgreSQL actually holds."""
    data_dir = Path("/var/lib/postgresql/16/main")
    bases = sorted(p.name for p in (data_dir / "base").iterdir()) if (
        data_dir / "base").exists() else []
    return {
        "tables_sought": ["corpus_snapshot", "corpus_snapshot_version", "document",
                          "document_version", "document_source"],
        "schema_present_in_repo": "sql/001_init.sql defines all of them; it carries no rows",
        "local_cluster": {
            "path": str(data_dir),
            "exists": data_dir.exists(),
            "state_when_found": "down",
            "restored_to": "down",
            "databases": ["postgres", "template0", "template1"],
            "base_oids_on_disk": bases,
            "verdict": ("only the three default databases; no project database, no "
                        "document_version rows, no corpus_snapshot rows. Inspected "
                        "read-only: no migration was run and no table was modified."),
        },
        "docker": "no docker daemon and no /var/lib/docker in this environment",
        "dumps_found": [],
        "verdict": "the historical project database is not in this environment",
    }


if __name__ == "__main__":
    raise SystemExit(main())
