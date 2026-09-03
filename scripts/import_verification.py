#!/usr/bin/env python3
"""GOLD-001: import independent verification results into candidate records.

Reads a verifier's output for a review batch and updates the candidates. It never
overwrites a proposal: any change to a question, answer or claim is appended as a
numbered revision with its author, timestamp and reason, so the authoring of ground
truth is itself auditable.

A ChatGPT PASS does **not** make a case ``human_verified``. It makes it
``dual_llm_pass``, which is a different and weaker thing, and the distinction is
enforced here rather than left to discipline.

The import also refuses to run when the verifier's ``source_batch_sha256`` does not
match the hash recorded in the batch: a review of a different batch than the one on
disk would silently attach verdicts to the wrong evidence.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

VALID_VERDICTS = {"PASS", "FAIL", "FIX_REQUIRED", "UNCERTAIN"}
BOOLEAN_FIELDS = (
    "question_supported", "answer_supported", "all_critical_claims_supported",
    "evidence_boundary_complete", "identifier_value_binding_correct", "natural_question",
)
#: A verdict alone never yields human approval — only a person can grant that.
STATUS_FROM_VERDICT = {
    "PASS": "dual_llm_pass",
    "FAIL": "dual_llm_fail",
    "FIX_REQUIRED": "needs_human_review",
    "UNCERTAIN": "needs_human_review",
}


#: Verifier outputs have arrived under several top-level keys. Accept the shapes we
#: have actually seen rather than requiring the reviewer to reformat by hand.
REVIEW_LIST_KEYS = ("reviews", "records", "results")


def extract_reviews(raw: object) -> list[dict]:
    """Pull the review list out of whatever envelope the verifier wrapped it in."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in REVIEW_LIST_KEYS:
            value = raw.get(key)
            if isinstance(value, list):
                return value
        raise SystemExit(
            f"review file has no review list; expected one of {REVIEW_LIST_KEYS} "
            f"or a bare list, got keys {sorted(raw)}"
        )
    raise SystemExit(f"review file must be a list or object, got {type(raw).__name__}")


def check_batch_provenance(raw: object, batch: dict) -> None:
    """Refuse to import verdicts produced against a different batch file."""
    if not isinstance(raw, dict):
        print("  warning: review file carries no source_batch_sha256 — provenance unchecked")
        return
    claimed = raw.get("source_batch_sha256")
    recorded = batch.get("batch_sha256")
    if claimed is None:
        print("  warning: review file carries no source_batch_sha256 — provenance unchecked")
        return
    if recorded is None:
        print("  warning: batch file carries no batch_sha256 — provenance unchecked")
        return
    if claimed != recorded:
        raise SystemExit(
            "batch hash mismatch — nothing was imported.\n"
            f"  batch on disk : {recorded}\n"
            f"  review claims : {claimed}"
        )
    print(f"  provenance ok: reviewed batch_sha256 {recorded[:16]}\u2026")


def validate_review(review: dict, known: set[str]) -> list[str]:
    problems = []
    candidate_id = review.get("candidate_id")
    if candidate_id not in known:
        problems.append(f"unknown candidate_id {candidate_id!r}")
    if review.get("verdict") not in VALID_VERDICTS:
        problems.append(f"invalid verdict {review.get('verdict')!r}")
    for field in BOOLEAN_FIELDS:
        if field in review and not isinstance(review[field], bool):
            problems.append(f"{field} must be boolean, got {review[field]!r}")
    return problems


def apply_review(record: dict, review: dict, reviewer: str, now: str) -> None:
    verdict = review["verdict"]
    record["chatgpt_verified"] = verdict == "PASS"
    record["verification_status"] = STATUS_FROM_VERDICT[verdict]
    record["verification"] = {
        "reviewer": reviewer, "verdict": verdict, "reviewed_at": now,
        **{f: review[f] for f in BOOLEAN_FIELDS if f in review},
        "verification_notes": review.get("verification_notes", ""),
    }

    # Any edit becomes a revision; the original proposal is never destroyed.
    for field, key in (("proposed_question", "suggested_question"),
                       ("proposed_answer", "suggested_answer"),
                       ("proposed_atomic_claims", "suggested_claims")):
        suggested = review.get(key)
        if suggested is None or suggested == record.get(field):
            continue
        record.setdefault("revisions", []).append({
            "revision": len(record.get("revisions", [])) + 1,
            "field": field,
            "from": record.get(field),
            "to": suggested,
            "author": reviewer,
            "timestamp": now,
            "reason": review.get("suggested_fix") or review.get("verification_notes", ""),
        })
        record[field] = suggested

    # The source anchor is not the reviewer's to change. A verifier who believes the
    # span is wrong should say so; silently re-anchoring would break the hash that
    # makes the evidence checkable.
    for immutable in ("version_id", "char_start", "char_end", "evidence_hash",
                      "evidence_text", "section_path"):
        if immutable in review and review[immutable] != record[immutable]:
            record.setdefault("anchor_disputes", []).append({
                "field": immutable, "reviewer_value": review[immutable],
                "kept_value": record[immutable], "author": reviewer, "timestamp": now,
            })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", help="path to gold_review_batch_NNN.json")
    parser.add_argument(
        "reviews",
        help="verifier output: a JSON list, or an object with a "
             "'reviews'/'records'/'results' list",
    )
    parser.add_argument("--reviewer", default="chatgpt")
    parser.add_argument("--out", default=None, help="defaults to updating the batch in place")
    args = parser.parse_args()

    batch_path = Path(args.batch)
    batch = json.loads(batch_path.read_text())
    raw = json.loads(Path(args.reviews).read_text())
    reviews = extract_reviews(raw)
    check_batch_provenance(raw, batch)

    records = {r["candidate_id"]: r for r in batch["records"]}
    problems: list[str] = []
    for review in reviews:
        problems.extend(f"[{review.get('candidate_id')}] {p}"
                        for p in validate_review(review, set(records)))
    if problems:
        print(f"{len(problems)} problems — nothing was imported:")
        for problem in problems[:20]:
            print("  ", problem)
        return 1

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    for review in reviews:
        apply_review(records[review["candidate_id"]], review, args.reviewer, now)

    reviewed = {r["candidate_id"] for r in reviews}
    batch["verification_imported_at"] = now
    batch["verification_reviewer"] = args.reviewer
    batch["reviewed_candidates"] = len(reviewed)
    batch["unreviewed_candidates"] = sorted(set(records) - reviewed)
    batch["status_counts"] = dict(Counter(r["verification_status"] for r in batch["records"]))
    # The batch-level banner has to move too, or it keeps claiming an unreviewed state
    # after review. What must not change is the part that says nothing here is gold.
    batch["verification_status"] = (
        f"dual_llm_reviewed by {args.reviewer} — nothing in this file is gold; "
        "every case still requires human approval"
    )

    out = Path(args.out) if args.out else batch_path
    out.write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"imported {len(reviewed)} reviews from {args.reviewer}")
    print("  status counts:", batch["status_counts"])
    if batch["unreviewed_candidates"]:
        print("  still unreviewed:", ", ".join(batch["unreviewed_candidates"]))
    print("  note: a PASS yields dual_llm_pass, never human_verified")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
