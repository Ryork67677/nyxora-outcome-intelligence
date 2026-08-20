#!/usr/bin/env python3
"""GOLD-001: apply an independent review's revisions to a candidate batch.

Batch 001's review arrived as verdicts plus suggested text; this is the same step for
batch 002, driven from a spec file rather than a reviewer's JSON, and with one addition:
a review may also require an anchor to be extended.

The invariants are unchanged. Every text change is appended as a numbered revision with
its author and reason, never written over the original. Every anchor change is a numbered
``anchor_revisions`` entry recording both spans and both hashes, and the new span must be
a strict superset of the old — a span that moves elsewhere is a re-anchoring, and is
refused. Nothing here can produce ``human_verified``: a revised candidate lands at
``needs_human_review``, which is where a person picks it up.

Every critical string is checked against the span it is supposed to be inside. A claim
the validator cannot check is the defect this batch exists to avoid shipping.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.db import connect

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repair_evidence_boundary import check_superset, locate
from validate_golden import load_sources

#: Where a revised candidate lands. Revising is not approving.
STATUS_AFTER_REVISION = "needs_human_review"
CONTEXT_CHARS = 900


def apply_anchor(record: dict, spec: dict, text: str, now: str) -> dict:
    old = (record["char_start"], record["char_end"])
    new = locate(text, spec["locate_head"], spec["locate_tail"], *old)
    check_superset(text, new, old)

    new_text = text[new[0]:new[1]]
    revision = {
        "revision": len(record.get("anchor_revisions", [])) + 1,
        "reason": "evidence_boundary_completion",
        "old_char_start": old[0], "old_char_end": old[1],
        "old_evidence_hash": record["evidence_hash"],
        "old_evidence_text": record["evidence_text"],
        "new_char_start": new[0], "new_char_end": new[1],
        "new_evidence_hash": hashlib.sha256(new_text.encode("utf-8")).hexdigest(),
        "new_evidence_text": new_text,
        "characters_added_before": old[0] - new[0],
        "characters_added_after": new[1] - old[1],
        "what_changed": spec.get("what_changed", ""),
        "why_complete": spec.get("why_complete", ""),
        "size_warning": spec.get("size_warning"),
        "author": "claude", "directed_by": "independent_review", "timestamp": now,
    }
    record.setdefault("anchor_revisions", []).append(revision)
    record["char_start"], record["char_end"] = new
    record["evidence_text"] = new_text
    record["evidence_hash"] = revision["new_evidence_hash"]
    record["context_before"] = text[max(0, new[0] - CONTEXT_CHARS):new[0]]
    record["context_after"] = text[new[1]:new[1] + CONTEXT_CHARS]
    return revision


def apply_text(record: dict, repair: dict, reviewer: str, now: str) -> int:
    changed = 0
    for field, key in (("proposed_question", "question"),
                       ("proposed_answer", "answer"),
                       ("proposed_atomic_claims", "atomic_claims")):
        if repair[key] == record.get(field):
            continue
        record.setdefault("revisions", []).append({
            "revision": len(record.get("revisions", [])) + 1,
            "field": field, "from": record.get(field), "to": repair[key],
            "author": reviewer, "timestamp": now,
            "reason": repair["defect_class"],
        })
        record[field] = repair[key]
        changed += 1
    return changed


def unsupported_strings(record: dict) -> list[str]:
    span = record["evidence_text"].lower()
    return [s for s in record.get("critical_strings", []) if s.lower() not in span]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch")
    parser.add_argument("spec")
    parser.add_argument("--reviewer", default="independent_review")
    parser.add_argument("--report", default="evals/review/batch_002_revision_report.json")
    args = parser.parse_args()

    batch_path = Path(args.batch)
    batch = json.loads(batch_path.read_text())
    spec = json.loads(Path(args.spec).read_text())
    records = {r["candidate_id"]: r for r in batch["records"]}

    claimed = spec.get("source_batch_sha256")
    if claimed and batch.get("batch_sha256") and claimed != batch["batch_sha256"]:
        raise SystemExit(
            "batch hash mismatch — nothing was applied.\n"
            f"  batch on disk : {batch['batch_sha256']}\n"
            f"  spec claims   : {claimed}"
        )
    unknown = [r["candidate_id"] for r in spec["repairs"]
               if r["candidate_id"] not in records]
    if unknown:
        raise SystemExit(f"spec names candidates not in the batch: {unknown}")

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    with connect() as conn, conn.cursor() as cur:
        sources = load_sources(cur)

    applied = []
    for repair in spec["repairs"]:
        record = records[repair["candidate_id"]]
        anchor_revision = None
        if "anchor" in repair:
            source = sources.get(record["version_id"])
            if source is None:
                raise SystemExit(f"{record['candidate_id']}: version not in the snapshot")
            anchor_revision = apply_anchor(record, repair["anchor"], source["text"], now)

        changed = apply_text(record, repair, args.reviewer, now)
        record["critical_strings"] = repair["critical_strings"]
        record["review_defect_class"] = repair["defect_class"]
        record["verification_status"] = STATUS_AFTER_REVISION
        record["chatgpt_verified"] = False
        record["verification"] = {
            "reviewer": args.reviewer, "verdict": repair["verdict"], "reviewed_at": now,
            "question_supported": False,
            "answer_supported": False,
            "all_critical_claims_supported": False,
            "evidence_boundary_complete": "anchor" not in repair,
            "identifier_value_binding_correct": True,
            "natural_question": False,
            "verification_notes": repair["defect_note"],
        }
        applied.append({
            "candidate_id": record["candidate_id"],
            "defect_class": repair["defect_class"],
            "fields_revised": changed,
            "anchor_revision": anchor_revision,
            "unsupported_critical_strings": unsupported_strings(record),
        })

    failures = [a for a in applied if a["unsupported_critical_strings"]]
    if failures:
        print(f"{len(failures)} candidates have a critical string outside their span — "
              "nothing was written:")
        for failure in failures:
            print(f"   {failure['candidate_id']}: "
                  f"{failure['unsupported_critical_strings']}")
        return 1

    batch["review_applied_at"] = now
    batch["review_reviewer"] = args.reviewer
    batch["status_counts"] = dict(Counter(r["verification_status"] for r in batch["records"]))
    batch["review_defect_classes"] = dict(Counter(a["defect_class"] for a in applied))
    batch["verification_status"] = (
        f"reviewed by {args.reviewer} — every candidate is FIX_REQUIRED and revised; "
        "nothing in this file is gold"
    )
    batch_path.write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")

    report = {
        "batch": batch.get("batch"),
        "applied_at": now,
        "reviewer": args.reviewer,
        "source_batch_sha256": batch.get("batch_sha256"),
        "candidates": len(applied),
        "defect_classes": batch["review_defect_classes"],
        "anchor_revisions": sum(1 for a in applied if a["anchor_revision"]),
        "all_critical_strings_inside_their_span": True,
        "status_counts": batch["status_counts"],
        "nothing_is_gold": (
            "Every candidate is needs_human_review. Only an explicit owner APPROVE "
            "imported by scripts/import_human_decisions.py can produce human_verified."
        ),
        "applied": applied,
    }
    Path(args.report).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                                 encoding="utf-8")

    print(f"revised {len(applied)} candidates as {args.reviewer}")
    print("  defect classes:", report["defect_classes"])
    print(f"  anchor revisions: {report['anchor_revisions']}")
    print("  every critical string verified inside its own span")
    print(f"wrote {batch_path}")
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
