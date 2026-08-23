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
#: Overrides a decision may carry. Each records that a person looked at a finding and
#: accepted it; none of them deletes the finding.
OVERRIDE_FIELDS = ("human_anaphora_override", "override_reviewer", "anaphora_status",
                   "human_dependency_override", "dependency_status")


def spans(record: dict) -> list[dict]:
    """The record's evidence, whichever shape the batch uses.

    Batches 001–003 carry one anchor on the record itself. Batch 004 carries a list in
    ``expected_evidence``, because a case may need two precise spans rather than one
    wide one. Everything downstream should ask this rather than reaching for
    ``record["evidence_hash"]``, which only exists in the older shape.
    """
    return record.get("expected_evidence") or [record]


def current_hashes(record: dict) -> list[str]:
    return [span["evidence_hash"] for span in spans(record)]


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

    # A pin may be one hash or, for a multi-span case, one per span in evidence order.
    claimed = entry.get("approves_evidence_hash")
    claimed_list = ([claimed] if isinstance(claimed, str)
                    else list(claimed) if claimed is not None else None)
    actual = current_hashes(record)

    if not revisions:
        # No repair: a pin is optional, but if given it must be right.
        if claimed_list is not None and claimed_list != actual:
            problems.append(
                f"[{candidate_id}] approves_evidence_hash does not match the anchor: "
                f"{[h[:16] for h in claimed_list]} vs {[h[:16] for h in actual]}"
            )
        return problems

    if claimed_list is None:
        problems.append(
            f"[{candidate_id}] has a repaired anchor; an APPROVE must pin it with "
            f"approves_evidence_hash (current: {actual})")
        return problems
    if len(claimed_list) != len(actual):
        problems.append(
            f"[{candidate_id}] approves {len(claimed_list)} evidence hashes, but the "
            f"candidate has {len(actual)} spans")
    elif claimed_list != actual:
        problems.append(
            f"[{candidate_id}] approves_evidence_hash does not match the current "
            f"anchor: {[h[:16] for h in claimed_list]} vs {[h[:16] for h in actual]}"
        )

    # Anchor revisions come in three shapes: a single grown span (batch 001), a list of
    # spans where a repair split one anchor into two (batch 003), and a per-span entry
    # naming the evidence it repaired (batch 004).
    superseded: set[str] = set()
    for revision in revisions:
        if "old_evidence_hash" in revision:
            superseded.add(revision["old_evidence_hash"])
        superseded.update(s["evidence_hash"] for s in revision.get("old_spans", []))
    overlap = superseded.intersection(claimed_list)
    if overlap:
        problems.append(
            f"[{candidate_id}] the approval names the anchor as it was BEFORE the "
            "repair; that version was sent back, not approved"
        )

    claimed_revision = entry.get("approves_anchor_revision")
    latest = revisions[-1]
    if claimed_revision is not None and claimed_revision != latest.get("revision"):
        problems.append(
            f"[{candidate_id}] approves anchor revision {claimed_revision}, but the "
            f"latest is {latest.get('revision')}"
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
        # Batch 004's revisions are per-span and carry no ordinal, so pin what is
        # actually there: which spans were repaired, and the hashes now approved.
        latest = record["anchor_revisions"][-1]
        history["approved_anchor_revision"] = latest.get("revision")
        history["approved_anchor_spans"] = [
            {"evidence_id": r["evidence_id"], "action": r["action"],
             "new_evidence_hash": r["new_evidence_hash"]}
            for r in record["anchor_revisions"] if "evidence_id" in r]
    # An override is part of the decision: it records that a person saw a finding and
    # accepted it. The finding itself is never deleted — anaphora.evaluate_span still
    # reports it, and still refuses to let a *critical* one be overridden at all.
    overrides = {k: entry[k] for k in OVERRIDE_FIELDS if k in entry}
    if overrides:
        if entry.get("human_anaphora_override") or entry.get("human_dependency_override"):
            named = entry.get("override_reviewer") or reviewer
            if named.strip().lower() in MODEL_REVIEWERS:
                raise SystemExit(
                    f"[{record['candidate_id']}] override_reviewer {named!r} is a model; "
                    "a model cannot accept a finding on a person's behalf")
            overrides.setdefault("override_reviewer", reviewer)
        record.update(overrides)
        history["overrides"] = overrides

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
        for span in spans(record):
            actual = hashlib.sha256(span["evidence_text"].encode("utf-8")).hexdigest()
            if actual != span["evidence_hash"]:
                failures.append(
                    f"[{record['candidate_id']}] {span.get('evidence_id', 'E1')} "
                    "evidence hash drift")
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
    # A decision file pins the batch the owner reviewed. Where repairs were kept out of
    # the generation artifact, that batch is a composed reviewed-state file, which
    # records the generation hash it was built from — so either identity satisfies the
    # pin, and a decision file naming some *other* batch is still refused.
    accepted = {h for h in (batch.get("batch_sha256"), batch.get("source_batch_sha256"))
                if h}
    if claimed and accepted and claimed not in accepted:
        raise SystemExit(
            "batch hash mismatch — nothing was imported.\n"
            f"  batch on disk    : {sorted(accepted)}\n"
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
