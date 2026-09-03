#!/usr/bin/env python3
"""GOLD-001: compose the record set an owner's decisions attach to.

From batch 004 onward, repairs are kept out of the generation artifact, so the state a
decision applies to lives in two files: the batch as generated, and the repairs the
source-integrity review proposed. The QC packet showed the owner their composition. This
writes that composition down as one file, so a decision has a single thing to attach to.

Neither input is modified. The composed file records both hashes — the generation batch
it came from and the QC packet whose contents the owner saw — so an approval can be
traced back to the exact text that was in front of a person.

Batch 004 has its own copy of this (``compose_batch_004_final.py``), left in place as a
historical artifact. New batches use this one.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=int, required=True)
    parser.add_argument("--source", default=None)
    parser.add_argument("--repairs", default=None)
    parser.add_argument("--packet", default=None)
    parser.add_argument("--generation-report", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    number = args.batch
    source = Path(args.source or f"evals/review/gold_review_batch_{number:03d}.json")
    repairs_path = Path(
        args.repairs or f"evals/review/gold_review_batch_{number:03d}_repairs.json")
    packet_path = Path(args.packet or f"evals/review/gold_batch_{number:03d}_qc.json")
    report_path = Path(
        args.generation_report
        or f"experiments/GOLD-001/GOLD-001-batch-{number:03d}-generation-report.json")
    out = Path(args.out
               or f"evals/review/gold_review_batch_{number:03d}_final.json")

    batch = json.loads(source.read_text())
    repairs = json.loads(repairs_path.read_text())
    packet = json.loads(packet_path.read_text())
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    if repairs["source_batch_sha256"] != batch["batch_sha256"]:
        raise SystemExit("the repairs were computed against a different batch file")
    if packet["source_batch_sha256"] != batch["batch_sha256"]:
        raise SystemExit("the QC packet was composed from a different batch file")

    repaired = {r["candidate_id"]: r for r in repairs["records"]}
    records = []
    for record in batch["records"]:
        candidate_id = record["candidate_id"]
        final = json.loads(json.dumps(repaired.get(candidate_id, record)))
        review = repairs["review"][candidate_id]
        final["internal_review_status"] = review["status"]
        final["internal_review_findings"] = review["findings"]
        final["was_repaired"] = bool(
            final.get("revisions") or final.get("anchor_revisions"))
        final.setdefault("precheck_flags", [])
        records.append(final)

    composed = {
        "batch": number,
        "state": "reviewed_pending_owner_decision",
        "schema_version": batch["schema_version"],
        "composed_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "corpus_snapshot": batch["corpus_snapshot"],
        "git_commit": batch.get("git_commit"),
        "source_batch": str(source),
        "source_batch_sha256": batch["batch_sha256"],
        "repairs_file": str(repairs_path),
        "qc_packet_prepared_at": packet["prepared_at"],
        "note": ("The generation artifact and the repairs file are both unchanged. This "
                 "is their composition — the text the owner reviewed — and the file a "
                 "decision attaches to."),
        "candidates": len(records),
        "repaired_candidates": sum(1 for r in records if r["was_repaired"]),
        "internal_review_status_counts": dict(
            Counter(r["internal_review_status"] for r in records)),
        "status_counts": dict(Counter(r["verification_status"] for r in records)),
        "human_verified": 0,
        "holdout_eligible": 0,
        "generation_target": report.get("targets", {}).get("size", 30),
        "generation_exported": batch["candidates"],
        "multi_hop_search": batch.get("multi_hop_search"),
        # Batch 006's central finding: the corpus is not exhausted, the authoring is.
        # Carried so a closure states it from the census rather than from prose.
        "corpus_census": batch.get("corpus_census"),
        "heading_audit": batch.get("heading_audit"),
        # Carried so a closure can report counts against what generation aimed
        # at, without reaching back into the generation artifact.
        "reasoning_targets": batch.get("targets", {}).get("reasoning_type"),
        "internal_review": batch.get("internal_review"),
        "generator_defects_found": repairs.get("generator_defects_found", []),
        "closure_errata": [],
        "retrieval_was_not_run": True,
        "systems_executed": [],
        "records": records,
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(composed, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    composed["batch_sha256"] = hashlib.sha256(out.read_bytes()).hexdigest()
    out.write_text(json.dumps(composed, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")

    print(f"composed {len(records)} records "
          f"({composed['repaired_candidates']} repaired) -> {out}")
    print("  review:", composed["internal_review_status_counts"])
    print("  batch_sha256:", composed["batch_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
