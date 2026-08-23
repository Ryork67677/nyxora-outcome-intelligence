#!/usr/bin/env python3
"""GOLD-001: compose the batch-004 record set the owner actually reviewed.

Batch 004 kept its repairs out of the generation artifact, so the state a decision
applies to lives in two files: ``gold_review_batch_004.json`` as generated, and
``gold_review_batch_004_repairs.json`` for the ten candidates the source-integrity
review repaired. The QC packet showed the owner the composition of the two. This writes
that composition down as one file, so a decision has a single thing to attach to.

Neither input is modified. The composed file records both hashes — the generation batch
it came from and the QC packet whose contents the owner saw — so an approval can be
traced back to the exact text that was in front of a person.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

BATCH = Path("evals/review/gold_review_batch_004.json")
GENERATION = Path("experiments/GOLD-001/GOLD-001-batch-004-generation-report.json")
NEAR_MISS = Path("experiments/GOLD-001/BATCH-004-near-miss-multihop-review.json")
REPAIRS = Path("evals/review/gold_review_batch_004_repairs.json")
PACKET = Path("evals/review/gold_batch_004_qc.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="evals/review/gold_review_batch_004_final.json")
    args = parser.parse_args()

    batch = json.loads(BATCH.read_text())
    repairs = json.loads(REPAIRS.read_text())
    packet = json.loads(PACKET.read_text())
    generation = json.loads(GENERATION.read_text())
    near_miss = json.loads(NEAR_MISS.read_text())
    if repairs["source_batch_sha256"] != batch["batch_sha256"]:
        raise SystemExit("the repairs were computed against a different batch file")
    if packet["source_batch_sha256"] != batch["batch_sha256"]:
        raise SystemExit("the QC packet was composed from a different batch file")

    repaired = {r["candidate_id"]: r for r in repairs["records"]}
    records = []
    for record in batch["records"]:
        final = json.loads(json.dumps(repaired.get(record["candidate_id"], record)))
        final["internal_review_status"] = repairs["review"][record["candidate_id"]]["status"]
        final["internal_review_findings"] = \
            repairs["review"][record["candidate_id"]]["findings"]
        final["was_repaired"] = record["candidate_id"] in repaired
        final.setdefault("precheck_flags", [])
        records.append(final)

    composed = {
        "batch": 4,
        "state": "reviewed_pending_owner_decision",
        "schema_version": batch["schema_version"],
        "composed_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "corpus_snapshot": batch["corpus_snapshot"],
        "source_batch": str(BATCH),
        "source_batch_sha256": batch["batch_sha256"],
        "repairs_file": str(REPAIRS),
        "qc_packet_prepared_at": packet["prepared_at"],
        "note": ("The generation artifact and the repairs file are both unchanged. This "
                 "is their composition — the text the owner reviewed — and the file a "
                 "decision attaches to."),
        "git_commit": batch.get("git_commit"),
        "candidates": len(records),
        "repaired_candidates": sum(1 for r in records if r["was_repaired"]),
        # Carried through so the closure states the generation result rather than
        # re-deriving it, and so the erratum travels with the record it corrects.
        "multi_hop_rejection": generation["multi_hop_rejection"],
        "reasoning_targets": generation["targets"]["reasoning_type"],
        "near_miss_diagnostic": {
            "pairs": near_miss["pairs"],
            "rule_under_test": near_miss["rule_under_test"],
            "verdicts": {f["bridge_entity"]: f["verdict"]
                         for f in near_miss["findings"]},
            "promoted_to_batch_004": near_miss["promoted_to_batch_004"],
            "batch_004_regenerated": near_miss["batch_004_regenerated"],
            "document": "experiments/GOLD-001/BATCH-004-near-miss-multihop-review.md",
        },
        "closure_errata": [{
            "correction": "near-miss bridge-pair count",
            "was": "3 pairs rejected only by the entity-state rule",
            "is": f"{near_miss['pairs']} pairs",
            "why": ("The 3 came from a manual probe run mid-development, with the "
                    "composer's per-run limit and used-fact set in force and before "
                    "the entity-state rule existed. "
                    "scripts/diagnose_b004_near_miss.py derives the set properly, and "
                    "the PDF builder now reads the count from it rather than "
                    "hardcoding one."),
            "recorded_in": "experiments/GOLD-001/GOLD-001-batch-004-report-erratum.md",
            "affects_generation_figures": False,
        }],
        "internal_review_status_counts": dict(
            Counter(r["internal_review_status"] for r in records)),
        "status_counts": dict(Counter(r["verification_status"] for r in records)),
        "human_verified": 0,
        "holdout_eligible": 0,
        "retrieval_was_not_run": True,
        "systems_executed": [],
        "records": records,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(composed, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    composed["batch_sha256"] = hashlib.sha256(out.read_bytes()).hexdigest()
    out.write_text(json.dumps(composed, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")

    print(f"composed {len(records)} records "
          f"({composed['repaired_candidates']} repaired) -> {out}")
    print("  review:", composed["internal_review_status_counts"])
    print("  status:", composed["status_counts"])
    print("  batch_sha256:", composed["batch_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
