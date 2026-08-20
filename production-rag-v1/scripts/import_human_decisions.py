#!/usr/bin/env python3
"""GOLD-001: import the project owner's decisions — the only path to ``human_verified``.

This is the one script in the pipeline that can promote a candidate to gold, and it can
only do so from a decision a person wrote down. Nothing infers approval: a missing
decision leaves the candidate out of gold, and a model's PASS never reaches this file.

Everything else is preserved. Revisions, the generator's original proposal, the
reviewer's verdict and the source anchor are all left exactly as they are; a decision is
recorded alongside them, never on top of them.

Run it only once decisions have actually been supplied::

    python scripts/import_human_decisions.py \\
      evals/review/gold_review_batch_001.json \\
      evals/review/human_decisions_batch_001.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

#: The whole point of the pipeline lives in this mapping. Only APPROVE produces gold.
STATUS_FROM_DECISION = {
    "APPROVE": "human_verified",
    "REJECT": "human_rejected",
    "NEEDS_EDIT": "needs_edit",
}
VALID_DECISIONS = frozenset(STATUS_FROM_DECISION)
#: Statuses that may enter a holdout. NEEDS_EDIT and an absent decision are both out.
GOLD_STATUSES = frozenset({"human_verified"})
#: A decision file naming a model as its reviewer is not a human decision, whatever it
#: says in the file. Refusing this is the difference between the safeguard being real
#: and being a comment.
MODEL_REVIEWERS = frozenset({
    "chatgpt", "gpt", "gpt-4", "gpt-5", "claude", "claude-code", "gemini", "llama",
    "assistant", "ai", "llm", "model",
})
REQUIRED_PROVENANCE = ("document_title", "source_url", "captured_at")


def revision_problems(record: dict, entry: dict) -> list[str]:
    """A repaired case may only be approved against the revision the owner saw.

    Once an anchor has been extended, "APPROVE" is ambiguous unless it names a version:
    the same candidate id now has two spans with two hashes. An approval that does not
    pin the current one is refused rather than guessed at.
    """
    if entry.get("decision") != "APPROVE":
        return []

    candidate_id = record["candidate_id"]
    revisions = record.get("anchor_revisions") or []
    problems = []

    # An approval may pin the number of text revisions it saw. On an unrepaired
    # candidate this is what distinguishes "I approved the generator's original" from
    # "I approved something a model rewrote".
    claimed_count = entry.get("approves_revision_count")
    if claimed_count is not None and claimed_count != len(record.get("revisions", [])):
        problems.append(
            f"[{candidate_id}] approves {claimed_count} revisions, but the candidate "
            f"carries {len(record.get('revisions', []))}"
        )

    claimed_hash = entry.get("approves_evidence_hash")
    if not revisions:
        # No repair: a pin is optional, but if given it must be right.
        if claimed_hash is not None and claimed_hash != record["evidence_hash"]:
            problems.append(
                f"[{candidate_id}] approves_evidence_hash {claimed_hash[:16]}… does not "
                f"match the anchor {record['evidence_hash'][:16]}…"
            )
        return problems

    latest = revisions[-1]
    if claimed_hash is None:
        problems.append(
            f"[{candidate_id}] has a repaired anchor; an APPROVE must pin it "
            f"with approves_evidence_hash (current: {record['evidence_hash']})")
        return problems
    if claimed_hash != record["evidence_hash"]:
        problems.append(
            f"[{candidate_id}] approves_evidence_hash {claimed_hash[:16]}… does not "
            f"match the current anchor {record['evidence_hash'][:16]}…"
        )
    # Anchor revisions come in two shapes: a single grown span (batch 001) and a list
    # of spans, because a repair may split one anchor into two precise ones (batch 003).
    superseded = ({latest["old_evidence_hash"]} if "old_evidence_hash" in latest
                  else {s["evidence_hash"] for s in latest.get("old_spans", [])})
    if claimed_hash in superseded:
        problems.append(
            f"[{candidate_id}] the approval names the anchor as it was BEFORE the "
            "repair; that version was sent back, not approved"
        )

    claimed_revision = entry.get("approves_anchor_revision")
    if claimed_revision is not None and claimed_revision != latest["revision"]:
        problems.append(
            f"[{candidate_id}] approves anchor revision {claimed_revision}, but the "
            f"latest is {latest['revision']}"
        )
    return problems


def validate(decisions: list[dict], known: set[str], reviewer: str,
             records: dict | None = None) -> list[str]:
    problems: list[str] = []
    if reviewer.strip().lower() in MODEL_REVIEWERS:
        problems.append(
            f"reviewer {reviewer!r} is a model, not a person — a model verdict is "
            "dual_llm_pass and can never be human_verified"
        )
    seen: set[str] = set()
    for entry in decisions:
        candidate_id = entry.get("candidate_id")
        if candidate_id not in known:
            problems.append(f"unknown candidate_id {candidate_id!r}")
            continue
        if candidate_id in seen:
            problems.append(f"duplicate decision for {candidate_id}")
        seen.add(candidate_id)
        decision = entry.get("decision")
        if decision is not None and decision not in VALID_DECISIONS:
            problems.append(
                f"[{candidate_id}] invalid decision {decision!r}; "
                f"allowed: {', '.join(sorted(VALID_DECISIONS))}"
            )
        if records is not None:
            problems.extend(revision_problems(records[candidate_id], entry))
    return problems


def apply_decision(record: dict, entry: dict, reviewer: str, now: str) -> bool:
    """Record one decision. Returns True if the candidate's status changed."""
    decision = entry.get("decision")
    if decision is None:
        record.setdefault("human_decision", None)
        return False

    # Appended, never overwritten — a re-review is a second entry, not a rewrite.
    history = {
        "decision": decision, "reviewer": reviewer, "decided_at": now,
        "notes": entry.get("notes", ""),
    }
    # Pin what was approved, so a later reader can tell which span the owner saw.
    if entry.get("approves_evidence_hash"):
        history["approved_evidence_hash"] = entry["approves_evidence_hash"]
    if record.get("anchor_revisions"):
        history["approved_anchor_revision"] = record["anchor_revisions"][-1]["revision"]
    record.setdefault("human_decision_history", []).append(history)
    record["human_decision"] = decision
    record["verification_status"] = STATUS_FROM_DECISION[decision]
    record["human_verified"] = decision == "APPROVE"
    record["human_reviewed_at"] = now
    record["human_reviewer"] = reviewer
    return True


def validation_report(batch: dict, reviewer: str, now: str) -> dict:
    """Re-derive what is true about the batch after the decisions land.

    The gates here are the ones a human decision cannot substitute for: an approval says
    the case is *right*, not that its bytes still match the corpus.
    """
    approved = [r for r in batch["records"]
                if r.get("verification_status") in GOLD_STATUSES]
    failures: list[str] = []
    for record in approved:
        actual = hashlib.sha256(record["evidence_text"].encode("utf-8")).hexdigest()
        if actual != record["evidence_hash"]:
            failures.append(f"[{record['candidate_id']}] evidence hash drift")
        if not record["proposed_question"].strip():
            failures.append(f"[{record['candidate_id']}] approved with an empty question")
        if not record["proposed_answer"].strip():
            failures.append(f"[{record['candidate_id']}] approved with an empty answer")
        if not record["proposed_atomic_claims"]:
            failures.append(f"[{record['candidate_id']}] approved with no atomic claims")
        if "[REVIEWER TO WRITE]" in record["proposed_question"]:
            failures.append(f"[{record['candidate_id']}] approved with a placeholder question")
        missing = [f for f in REQUIRED_PROVENANCE if not record.get(f)]
        if missing:
            failures.append(f"[{record['candidate_id']}] missing provenance: {missing}")

    return {
        "batch": batch.get("batch"),
        "source_batch_sha256": batch.get("batch_sha256"),
        "generated_at": now,
        "reviewer": reviewer,
        "status_counts": dict(Counter(r["verification_status"] for r in batch["records"])),
        "decision_counts": dict(Counter(
            r.get("human_decision") or "no_decision" for r in batch["records"])),
        "eligible_for_gold": sorted(r["candidate_id"] for r in approved),
        "eligible_for_gold_count": len(approved),
        "gate_failures": failures,
        "passed": not failures,
        "note": (
            "Eligible for gold means human_verified. NEEDS_EDIT and undecided candidates "
            "are deliberately excluded. This report checks integrity, not correctness — "
            "correctness is what the human decision is for."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", help="path to gold_review_batch_NNN.json")
    parser.add_argument("decisions", help="path to human_decisions_batch_NNN.json")
    parser.add_argument("--reviewer", default=None,
                        help="defaults to the reviewer named in the decisions file")
    parser.add_argument("--report", default=None)
    parser.add_argument("--out", default=None, help="defaults to updating the batch in place")
    args = parser.parse_args()

    batch_path = Path(args.batch)
    batch = json.loads(batch_path.read_text())
    supplied = json.loads(Path(args.decisions).read_text())
    entries = supplied["decisions"] if isinstance(supplied, dict) else supplied
    reviewer = args.reviewer or (
        supplied.get("reviewer") if isinstance(supplied, dict) else None) or "project_owner"

    claimed = supplied.get("source_batch_sha256") if isinstance(supplied, dict) else None
    if claimed and batch.get("batch_sha256") and claimed != batch["batch_sha256"]:
        raise SystemExit(
            "batch hash mismatch — nothing was imported.\n"
            f"  batch on disk    : {batch['batch_sha256']}\n"
            f"  decisions claim  : {claimed}"
        )

    records = {r["candidate_id"]: r for r in batch["records"]}
    problems = validate(entries, set(records), reviewer, records)
    if problems:
        print(f"{len(problems)} problems — nothing was imported:")
        for problem in problems[:20]:
            print("  ", problem)
        return 1

    decided = [e for e in entries if e.get("decision") is not None]
    if not decided:
        print("no decisions supplied yet — nothing to import")
        print(f"  fill in {args.decisions} with APPROVE / REJECT / NEEDS_EDIT and re-run")
        return 1

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    changed = sum(apply_decision(records[e["candidate_id"]], e, reviewer, now)
                  for e in entries)

    batch["human_decisions_imported_at"] = now
    batch["human_reviewer"] = reviewer
    batch["status_counts"] = dict(Counter(r["verification_status"] for r in batch["records"]))
    batch["undecided_candidates"] = sorted(
        cid for cid, r in records.items() if r.get("human_decision") is None)
    batch["verification_status"] = (
        f"human_reviewed by {reviewer} — approved cases are gold; every other case, "
        "including NEEDS_EDIT and undecided, is not"
    )

    report = validation_report(batch, reviewer, now)
    out = Path(args.out) if args.out else batch_path
    out.write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_path = Path(args.report) if args.report else out.with_name(
        f"validation_report_batch_{batch.get('batch', 0):03d}.json")
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")

    print(f"imported {changed} decisions from {reviewer}")
    print("  status counts:", batch["status_counts"])
    print(f"  eligible for gold: {report['eligible_for_gold_count']}")
    if batch["undecided_candidates"]:
        print("  still undecided:", ", ".join(batch["undecided_candidates"]))
    if report["gate_failures"]:
        print(f"  {len(report['gate_failures'])} GATE FAILURES:")
        for failure in report["gate_failures"][:20]:
            print("   ", failure)
    print(f"wrote {out}")
    print(f"wrote {report_path}")
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
