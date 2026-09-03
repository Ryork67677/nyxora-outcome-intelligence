#!/usr/bin/env python3
"""CORPUS-002: verify the restored corpus and write the restoration artifacts.

Every figure is read from the restored database, the recovery package and the closed
GOLD records at run time. The script refuses to declare success unless each gate in the
CORPUS-002 brief passes on its own evidence.

It does not run retrieval, does not embed, and does not touch the historical database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.config import settings
from rag_v1.corpus_oracle import MANIFEST_HASH, SNAPSHOT_ID
from rag_v1.db import connect
from rag_v1.gold.normalisation import contains_claim_string
from rag_v1.ids import config_hash
from rag_v1.parsing import PARSER_VERSION

ARCHIVE = Path("/home/user/corpus-recovery-snap689e3363-20260831T2118Z.tar.gz")
ARCHIVE_SHA = "4387ae1d5144109adbde3f11f1fcb339c3773480f356f9804909cf3ad2051b33"
PACKAGE = Path("/home/user/corpus002/extracted/"
               "corpus-recovery-export-20260831T2118Z-snap689e3363")
WORKING = Path("recovery/CORPUS-002/working-corpus")
OUT = Path("experiments/CORPUS-002")
CONTROL_SET = "cs_v1_control"
HISTORICAL_CHUNKS = {"total": 14209, "anthropic": 12028, "openai": 2181}

GOLD_SOURCES = {
    "001": "evals/gold/batch_001_v2/overlay.json",
    "002": "evals/review/gold_review_batch_002.json",
    "003": "evals/review/gold_review_batch_003.json",
    "004": "evals/review/gold_review_batch_004_final.json",
    "005": "evals/review/gold_review_batch_005_final.json",
    "006": "evals/review/gold_review_batch_006_final.json",
    "HA": "evals/review/gold_review_HA01_HA60_final.json",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def spans_of(record: dict) -> list[dict]:
    """GOLD anchors in either schema.

    Batches 004 onward carry ``expected_evidence`` as a list. Batches 001-003 predate
    that and keep a single anchor flat on the record. Reading only the list shape makes
    45 of the 150 cases look unanchored, which would understate the verification and
    misreport the benchmark.
    """
    listed = record.get("expected_evidence") or []
    if listed:
        return [dict(span, _shape="expected_evidence") for span in listed]
    if record.get("version_id") and record.get("char_start") is not None:
        return [{
            "_shape": "legacy_flat", "evidence_id": "E1",
            "version_id": record["version_id"], "char_start": record["char_start"],
            "char_end": record["char_end"], "evidence_text": record.get("evidence_text"),
            "evidence_hash": record.get("evidence_hash"),
            "critical_strings": record.get("critical_strings") or [],
        }]
    return []


def verify_package() -> dict:
    listing = (PACKAGE / "SHA256SUMS.txt").read_text().splitlines()
    ok = failed = 0
    for line in listing:
        if not line.strip():
            continue
        want, rel = line.split("  ", 1)
        path = PACKAGE / rel
        if path.exists() and sha256_file(path) == want:
            ok += 1
        else:
            failed += 1
    return {"entries": len(listing), "verified": ok, "failed": failed}


def verify_working_copy() -> dict:
    """The working files must still equal the package they were copied from."""
    ok = failed = 0
    mismatches = []
    for line in (PACKAGE / "SHA256SUMS.txt").read_text().splitlines():
        if not line.strip():
            continue
        want, rel = line.split("  ", 1)
        if rel.startswith("corpus/data/raw/"):
            target = WORKING / "data/raw" / rel[len("corpus/data/raw/"):]
        elif rel.startswith("corpus/data/manifests/"):
            target = WORKING / "data/manifests" / rel[len("corpus/data/manifests/"):]
        else:
            continue
        if target.exists() and sha256_file(target) == want:
            ok += 1
        else:
            failed += 1
            mismatches.append(str(target))
    return {"verified": ok, "failed": failed, "mismatches": mismatches}


def verify_documents() -> dict:
    provenance = json.loads((PACKAGE / "PROVENANCE.json").read_text())
    expected = {f["version_id"]: f for f in provenance["files"]}
    with connect() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT v.version_id, v.content_hash, s.provider, s.canonical_url,
                   v.captured_at
            FROM document_version v JOIN document_source s ON s.source_id = v.source_id
            WHERE v.status = 'current' ORDER BY v.version_id""")
        rows = cur.fetchall()
    mismatches, providers = [], {}
    for version_id, content_hash, provider, url, captured in rows:
        providers[provider] = providers.get(provider, 0) + 1
        want = expected.get(version_id)
        if want is None:
            mismatches.append({"version_id": version_id, "field": "version_id",
                               "detail": "restored row absent from PROVENANCE.json"})
            continue
        captured_text = (captured.strftime("%Y-%m-%dT%H:%M:%SZ")
                         if hasattr(captured, "strftime") else str(captured))
        for field, got, expect in (("content_hash", content_hash,
                                    want["content_sha256"]),
                                   ("provider", provider, want["provider"]),
                                   ("canonical_url", url, want["canonical_url"]),
                                   ("captured_at", captured_text, want["captured_at"])):
            if got != expect:
                mismatches.append({"version_id": version_id,
                                   "basename": want["basename"], "field": field,
                                   "restored": str(got), "expected": str(expect)})
    return {"restored": len(rows), "expected": len(expected),
            "by_provider": providers,
            "missing": sorted(set(expected) - {r[0] for r in rows}),
            "mismatches": mismatches}


def verify_identity() -> dict:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT version_id, content_hash FROM document_version "
                    "WHERE status='current' ORDER BY version_id")
        payload = [{"version_id": v, "content_hash": h} for v, h in cur.fetchall()]
        cur.execute("SELECT snapshot_id, name, manifest_hash, parser_version, "
                    "chunking_config_hash FROM corpus_snapshot")
        snapshots = cur.fetchall()
    manifest = config_hash({"versions": payload})
    chunking = config_hash({"max_chunk_chars": settings.max_chunk_chars,
                            "min_chunk_chars": settings.min_chunk_chars})
    return {
        "manifest_hash_computed": manifest,
        "manifest_hash_expected": MANIFEST_HASH,
        "manifest_hash_match": manifest == MANIFEST_HASH,
        "snapshot_ids_in_db": [s[0] for s in snapshots],
        "snapshot_id_expected": SNAPSHOT_ID,
        "snapshot_id_match": any(s[0] == SNAPSHOT_ID for s in snapshots),
        "parser_version": PARSER_VERSION,
        "chunking": {"max_chunk_chars": settings.max_chunk_chars,
                     "min_chunk_chars": settings.min_chunk_chars,
                     "config_hash": chunking},
    }


def verify_chunks() -> dict:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT chunk_set_id, count(*) FROM chunk GROUP BY 1 ORDER BY 1")
        by_set = dict(cur.fetchall())
        cur.execute("""SELECT s.provider, count(*) FROM chunk c
                       JOIN document_version v ON v.version_id = c.version_id
                       JOIN document_source s ON s.source_id = v.source_id
                       WHERE c.chunk_set_id = %s GROUP BY 1 ORDER BY 1""",
                    (CONTROL_SET,))
        by_provider = dict(cur.fetchall())
    return {
        "by_chunk_set": by_set,
        "control_set": CONTROL_SET,
        "control_by_provider": by_provider,
        "control_total": sum(by_provider.values()),
        "historical_target": HISTORICAL_CHUNKS,
        "matches_historical": (
            sum(by_provider.values()) == HISTORICAL_CHUNKS["total"]
            and by_provider.get("anthropic") == HISTORICAL_CHUNKS["anthropic"]
            and by_provider.get("openai") == HISTORICAL_CHUNKS["openai"]),
        "note": (
            "Only the V1 control set is restored here. The historical database also "
            "holds seven later experimental chunk sets over the same source corpus; "
            "those are retrieval-configuration state, not corpus identity, and "
            "CORPUS-002 deliberately does not rebuild them."),
    }


def verify_gold() -> dict:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT version_id, normalized_text FROM document_version "
                    "WHERE status='current'")
        text_by_version = dict(cur.fetchall())
    summary = {"cases": 0, "anchored_cases": 0, "unanchored_cases": 0,
               "spans_total": 0, "spans_verified": 0, "by_shape": {},
               "by_group": {}, "failures": []}
    per_case = []
    for group, rel in GOLD_SOURCES.items():
        payload = json.loads(Path(rel).read_text())
        for record in (payload.get("records") or payload.get("case_records") or []):
            if not (record.get("verification_status") == "human_verified"
                    or record.get("human_verified")):
                continue
            summary["cases"] += 1
            bucket = summary["by_group"].setdefault(
                group, {"cases": 0, "spans": 0, "verified": 0})
            bucket["cases"] += 1
            spans = spans_of(record)
            entry = {"candidate_id": record["candidate_id"], "group": group,
                     "spans": len(spans), "verified": 0, "failures": []}
            summary["anchored_cases" if spans else "unanchored_cases"] += 1
            for span in spans:
                summary["spans_total"] += 1
                bucket["spans"] += 1
                summary["by_shape"][span["_shape"]] = (
                    summary["by_shape"].get(span["_shape"], 0) + 1)
                text = text_by_version.get(span["version_id"])
                if text is None:
                    entry["failures"].append(
                        f"{span['evidence_id']}: version_id absent from corpus")
                    continue
                if not (0 <= span["char_start"] < span["char_end"] <= len(text)):
                    entry["failures"].append(
                        f"{span['evidence_id']}: offsets outside the document")
                    continue
                sliced = text[span["char_start"]:span["char_end"]]
                if span.get("evidence_text") is not None and \
                        sliced != span["evidence_text"]:
                    entry["failures"].append(
                        f"{span['evidence_id']}: evidence text differs")
                    continue
                stored = span.get("evidence_hash")
                if stored and hashlib.sha256(
                        sliced.encode("utf-8")).hexdigest() != stored:
                    entry["failures"].append(f"{span['evidence_id']}: hash differs")
                    continue
                stray = [s for s in (span.get("critical_strings") or [])
                         if not contains_claim_string(sliced, s)]
                if stray:
                    entry["failures"].append(
                        f"{span['evidence_id']}: critical strings absent {stray}")
                    continue
                entry["verified"] += 1
                summary["spans_verified"] += 1
                bucket["verified"] += 1
            if entry["failures"]:
                summary["failures"].append(entry)
            per_case.append(entry)
    return {"summary": summary, "per_case": per_case}


def fingerprint() -> dict:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT current_database(), version()")
        database, server = cur.fetchone()
        cur.execute("SELECT extversion FROM pg_extension WHERE extname='vector'")
        row = cur.fetchone()
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' "
                    "ORDER BY 1")
        tables = [r[0] for r in cur.fetchall()]
        cur.execute("""SELECT 'chunk_embedding', count(*) FROM chunk_embedding
                       UNION ALL SELECT 'query_trace', count(*) FROM query_trace
                       UNION ALL SELECT 'retrieval_cache', count(*) FROM retrieval_cache
                       UNION ALL SELECT 'embedding_model', count(*) FROM embedding_model
                    """)
        retrieval_tables = dict(cur.fetchall())
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                            capture_output=True, text=True, check=False).stdout
    pinned = {line.split("==")[0]: line.split("==")[1]
              for line in freeze.splitlines() if "==" in line
              and line.split("==")[0].lower() in
              {"psycopg", "pgvector", "pyyaml", "pydantic", "pydantic-settings",
               "numpy", "scikit-learn", "pytest", "ruff"}}
    return {
        "restoration_database": database,
        "postgresql": server.split(",")[0],
        "pgvector": row[0] if row else None,
        "sql_applied_in_order": ["sql/001_init.sql", "(ingest 202 documents)",
                                 "(create_snapshot)", "sql/002_chunk_sets.sql",
                                 "sql/003_search_text.sql", "sql/004_embedding_cache.sql"],
        "sql_order_note": (
            "V1 was ingested before chunk sets existed; sql/002_chunk_sets.sql adopts "
            "those rows into cs_v1_control. Applying 002 before ingesting fails on a "
            "NOT NULL chunk_set_id, so the historical order is reproduced deliberately."),
        "tables": tables,
        "retrieval_tables_row_counts": retrieval_tables,
        "python": sys.version.split()[0],
        "dependencies": pinned,
        "parser_version": PARSER_VERSION,
        "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                     text=True, check=False).stdout.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(OUT))
    args = parser.parse_args()

    if not settings.database_url.endswith("/corpus002_restore"):
        raise SystemExit("refusing to run: DATABASE_URL must point at the isolated "
                         f"restoration database, got {settings.database_url!r}")

    archive_sha = sha256_file(ARCHIVE) if ARCHIVE.exists() else None
    result = {
        "document": "CORPUS-002 — restoration of the verified frozen corpus",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "archive": {"path": str(ARCHIVE), "sha256": archive_sha,
                    "expected": ARCHIVE_SHA, "match": archive_sha == ARCHIVE_SHA},
        "package_integrity": verify_package(),
        "working_copy": {"path": str(WORKING), **verify_working_copy()},
        "documents": verify_documents(),
        "identity": verify_identity(),
        "chunks": verify_chunks(),
        "gold_anchors": verify_gold(),
        "environment": fingerprint(),
    }

    documents, identity = result["documents"], result["identity"]
    gold = result["gold_anchors"]["summary"]
    gates = {
        "archive_hash_matches": result["archive"]["match"],
        "package_203_of_203": (result["package_integrity"]["verified"] == 203
                               and result["package_integrity"]["failed"] == 0),
        "working_copy_matches_package": result["working_copy"]["failed"] == 0,
        "documents_202": documents["restored"] == 202 and not documents["missing"],
        "provider_counts": documents["by_provider"] == {"anthropic": 139, "openai": 63},
        "document_identities_verify": not documents["mismatches"],
        "manifest_hash_exact": identity["manifest_hash_match"],
        "snapshot_id_exact": identity["snapshot_id_match"],
        "all_gold_anchors_validate": (gold["spans_total"] == gold["spans_verified"]
                                      and gold["unanchored_cases"] == 0
                                      and gold["cases"] == 150),
        "no_retrieval_ran": all(
            v == 0 for v in
            result["environment"]["retrieval_tables_row_counts"].values()),
    }
    result["gates"] = gates
    result["corpus_002_succeeded"] = all(gates.values())
    result["flags"] = {
        "CORPUS_REPRODUCTION_INCOMPLETE": not result["corpus_002_succeeded"],
        "corpus_snapshot_reproduced": result["corpus_002_succeeded"],
        "RETRIEVAL_BLOCKED_BY_CORPUS": not result["corpus_002_succeeded"],
        "holdout_split_block": "UNCHANGED — CORPUS-002 does not clear it",
        "note": (
            "These flags describe corpus state only. The GOLD-001 150-case closure is "
            "a closed artifact and was not edited; its recorded corpus_reproduction "
            "limitation is superseded by this document rather than rewritten in "
            "place."),
    }
    result["not_done"] = [
        ("No retrieval was run: no BM25, dense, RRF, DOC-C, routing, reranking or "
         "generation, and no ranks or scores were produced."),
        "No embeddings were built; chunk_embedding is empty.",
        "The holdout and the validation split remain unfrozen.",
        "The historical database was read but never written.",
        "No GOLD record was modified.",
        "No document was fetched from any network source.",
    ]

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "CORPUS-002-restoration-report.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "CORPUS-002-document-verification.json").write_text(
        json.dumps(result["documents"], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (out_dir / "CORPUS-002-gold-anchor-verification.json").write_text(
        json.dumps(result["gold_anchors"], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (out_dir / "CORPUS-002-environment-fingerprint.json").write_text(
        json.dumps(result["environment"], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (out_dir / "CORPUS-002-restoration-report.md").write_text(render(result),
                                                              encoding="utf-8")

    for name, passed in gates.items():
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")
    print(f"\nCORPUS-002 SUCCEEDED: {result['corpus_002_succeeded']}")
    return 0 if result["corpus_002_succeeded"] else 1


def render(r: dict) -> str:
    d, i, c = r["documents"], r["identity"], r["chunks"]
    g = r["gold_anchors"]["summary"]
    e = r["environment"]
    gate_rows = "\n".join(f"| {k.replace('_', ' ')} | {'PASS' if v else 'FAIL'} |"
                          for k, v in r["gates"].items())
    group_rows = "\n".join(
        f"| {k} | {v['cases']} | {v['spans']} | {v['verified']} |"
        for k, v in sorted(g["by_group"].items()))
    return "\n".join([
        "# CORPUS-002 — restoration of the verified frozen corpus",
        "",
        (f"**{'SUCCEEDED' if r['corpus_002_succeeded'] else 'FAILED'}** — "
         f"generated {r['generated_at']}."),
        "",
        ("The frozen corpus was restored from the verified recovery archive into a "
         "fresh isolated database, and its identity was recomputed rather than "
         "asserted. No retrieval was run."),
        "",
        "## Gates",
        "",
        "| gate | result |",
        "| --- | --- |",
        gate_rows,
        "",
        "## Archive and package",
        "",
        "| | |",
        "| --- | --- |",
        f"| archive | `{r['archive']['path']}` |",
        f"| archive sha256 | `{r['archive']['sha256']}` |",
        f"| matches required | {r['archive']['match']} |",
        (f"| package checksums | {r['package_integrity']['verified']} verified, "
         f"{r['package_integrity']['failed']} failed |"),
        (f"| working copy | {r['working_copy']['verified']} files match the package, "
         f"{r['working_copy']['failed']} mismatched |"),
        f"| working copy path | `{r['working_copy']['path']}` |",
        "",
        "## Documents",
        "",
        (f"**{d['restored']} of {d['expected']}** document versions restored — "
         f"{d['by_provider']}. Missing: {len(d['missing'])}. "
         f"Field mismatches: {len(d['mismatches'])}."),
        "",
        ("Each restored row was compared against `PROVENANCE.json` on "
         "`content_hash`, `provider`, `canonical_url` and `captured_at` "
         "individually."),
        "",
        "## Corpus identity",
        "",
        "| | |",
        "| --- | --- |",
        f"| manifest hash computed | `{i['manifest_hash_computed']}` |",
        f"| manifest hash expected | `{i['manifest_hash_expected']}` |",
        f"| **exact match** | **{i['manifest_hash_match']}** |",
        f"| snapshot id in database | `{', '.join(i['snapshot_ids_in_db'])}` |",
        f"| snapshot id expected | `{i['snapshot_id_expected']}` |",
        f"| **exact match** | **{i['snapshot_id_match']}** |",
        f"| parser version | `{i['parser_version']}` |",
        (f"| chunking | max_chunk_chars={i['chunking']['max_chunk_chars']}, "
         f"min_chunk_chars={i['chunking']['min_chunk_chars']} |"),
        f"| chunking config hash | `{i['chunking']['config_hash']}` |",
        "",
        ("The chunking values were read from `src/rag_v1/config.py`, not from a report. "
         "The snapshot id binds the manifest hash, the parser version and the chunking "
         "hash together, so all three had to be right for it to reproduce."),
        "",
        "## Chunks",
        "",
        (f"`{c['control_set']}`: **{c['control_total']}** chunks — "
         f"{c['control_by_provider']}. Historical target: {c['historical_target']}. "
         f"Match: **{c['matches_historical']}**."),
        "",
        c["note"],
        "",
        "## GOLD evidence anchors",
        "",
        (f"**{g['spans_verified']} of {g['spans_total']}** evidence spans across "
         f"**{g['cases']}** human-verified cases reproduce byte-exactly against the "
         f"restored corpus. Cases with no anchor at all: {g['unanchored_cases']}."),
        "",
        "| group | cases | spans | verified |",
        "| --- | --- | --- | --- |",
        group_rows,
        "",
        (f"Anchor shapes: {g['by_shape']}. Batches 001-003 store a single anchor flat "
         "on the record; batches 004 onward use an `expected_evidence` list. Both are "
         "checked — reading only the list shape would have left 45 of the 150 cases "
         "unverified while reporting success."),
        "",
        ("This is a source-integrity check. No query was run, nothing was ranked, and "
         "no retrieval system was executed."),
        "",
        "## Environment",
        "",
        "| | |",
        "| --- | --- |",
        f"| restoration database | `{e['restoration_database']}` |",
        f"| postgresql | {e['postgresql']} |",
        f"| pgvector | {e['pgvector']} |",
        f"| python | {e['python']} |",
        f"| parser version | `{e['parser_version']}` |",
        f"| git commit | `{e['git_commit'][:12]}` |",
        f"| retrieval tables | {e['retrieval_tables_row_counts']} |",
        "",
        f"**Migration order.** {e['sql_order_note']}",
        "",
        "## Flags",
        "",
        "\n".join(f"- `{k}` = `{v}`" for k, v in r["flags"].items() if k != "note"),
        "",
        r["flags"]["note"],
        "",
        "## Not done",
        "",
        "\n".join(f"- {item}" for item in r["not_done"]),
        "",
    ])


if __name__ == "__main__":
    raise SystemExit(main())
