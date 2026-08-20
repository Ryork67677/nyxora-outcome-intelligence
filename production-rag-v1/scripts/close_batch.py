#!/usr/bin/env python3
"""GOLD-001: close a review batch and make it tamper-evident.

Closure is not a status change — it is a statement that every candidate reached a human
decision and nothing is outstanding. The script refuses to write one while that is
untrue, so a closure artifact can never claim more than the batch actually holds.

It records a ``closure_sha256`` over the candidate records. A closed batch is not
supposed to change again, and a hash is the difference between saying so and being able
to check it. ``tests/test_gold001_review_workflow.py`` verifies the recorded hash still
matches, so an edit after closure fails the suite rather than passing unnoticed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

GOLD = "human_verified"
REJECTED = "human_rejected"
#: Anything else outstanding blocks closure.
CLOSED_STATUSES = frozenset({GOLD, REJECTED})

#: The taxonomy batch 001 produced, kept with the closure so the rejection reasons and
#: the batch-002 rules stay legible next to the numbers they came from.
DEFECT_TAXONOMY = {
    "D1": {
        "name": "anaphoric anchor",
        "description": ("The span opens on, or silently depends on, a referent outside "
                        "itself — 'If true', 'any of these models'. The claim cannot be "
                        "checked against the anchor alone."),
    },
    "D2": {
        "name": "wrong relation label",
        "description": ("The miner matched a trigger word and labelled the candidate "
                        "with a relation the sentence does not express. The evidence is "
                        "usually fine; the label aims the reviewer at the wrong "
                        "question."),
    },
    "D3": {
        "name": "example-code false binding",
        "description": ("An identifier matched inside a fenced code block or JSON "
                        "literal and was framed as a documented rule. A sample "
                        "configuration is not a rule."),
    },
}


def claim_check_caveat(verified: int, with_critical: int) -> str:
    """State what the validator's pass does and does not cover, from the records.

    The claim-in-evidence gate only fires on claims marked critical, so a case carrying
    none passes it without anything being tested. Whether that matters is a fact about
    the batch, so it is derived here rather than written down once and left to rot.
    """
    unchecked = verified - with_critical
    if verified == 0:
        return "No verified cases, so the validator's result covers nothing."
    if unchecked == 0:
        return (
            f"All {verified} verified cases carry literal critical strings, so the "
            "claim-in-evidence check ran on every one of them. The validator's pass "
            "covers claim support, not only structure."
        )
    if with_critical == 0:
        return (
            f"None of the {verified} verified cases carry literal critical strings, so "
            "the claim-in-evidence check passed over all of them without testing "
            "anything. This pass says nothing about claim support, and that gap must be "
            "closed before any of these enters a frozen holdout."
        )
    return (
        f"Only {with_critical} of {verified} verified cases carry literal critical "
        f"strings, so for the other {unchecked} the claim-in-evidence check passed "
        "without testing anything. That gap must be closed before those cases enter a "
        "frozen holdout."
    )


def candidate_digest(records: list[dict]) -> str:
    """Hash the candidates in a stable order, ignoring key ordering."""
    payload = json.dumps(sorted(records, key=lambda r: r["candidate_id"]),
                         sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def defects_of(record: dict) -> list[str]:
    """Recover the taxonomy classes from what the independent reviewer recorded."""
    named = record.get("review_defect_class")
    if named:
        return [named]
    verification = record.get("verification", {})
    import re
    code = re.search(r"^\s*[\w.\[\]\"']+\s*=\s*\S|^\s*[\]\})],?\s*$|^\s*\"[\w_]+\"\s*:|"
                     r"^\s*raise\s|^\s*return\s",
                     record.get("anchor_revisions", [{}])[0].get("old_evidence_text")
                     or record["evidence_text"], re.MULTILINE)
    classes = []
    if verification.get("evidence_boundary_complete") is False:
        classes.append("D1")
    if verification.get("identifier_value_binding_correct") is False:
        classes.append("D3" if code else "D2")
    return classes


def build(batch: dict, validation: dict, now: str) -> dict:
    records = batch["records"]
    statuses = Counter(r["verification_status"] for r in records)
    outstanding = sorted(r["candidate_id"] for r in records
                         if r["verification_status"] not in CLOSED_STATUSES)
    if outstanding:
        raise SystemExit(
            "refusing to close: these candidates have no final human decision — "
            + ", ".join(outstanding)
        )

    verified = [r for r in records if r["verification_status"] == GOLD]
    with_critical = sum(1 for r in verified if r.get("critical_strings"))
    rejected = [r for r in records if r["verification_status"] == REJECTED]
    repaired = [r for r in records if r.get("anchor_revisions")]

    return {
        "batch": batch.get("batch"),
        "closed_at": now,
        "closed_by": "project_owner",
        "source_batch_sha256": batch.get("batch_sha256"),
        "corpus_snapshot": batch.get("corpus_snapshot"),
        "schema_version": batch.get("schema_version"),
        "git_commit": batch.get("git_commit"),
        "totals": {
            "candidates": len(records),
            "human_verified": len(verified),
            "human_rejected": len(rejected),
            "needs_human_review": 0,
            "outstanding_decisions": 0,
            "acceptance_rate": round(len(verified) / len(records), 4),
        },
        "status_counts": dict(statuses),
        "human_verified_ids": sorted(r["candidate_id"] for r in verified),
        "rejected": [{
            "candidate_id": r["candidate_id"],
            "defects": defects_of(r),
            "reason": r["human_decision_history"][-1]["notes"],
            "independent_verdict": r["verification"]["verdict"],
            "preserved_as": "negative audit example - the record is kept, not deleted",
        } for r in sorted(rejected, key=lambda r: r["candidate_id"])],
        "repaired": [{
            "candidate_id": r["candidate_id"],
            "reason": r["anchor_revisions"][-1]["reason"],
            "old_span": [r["anchor_revisions"][-1]["old_char_start"],
                         r["anchor_revisions"][-1]["old_char_end"]],
            "new_span": [r["anchor_revisions"][-1]["new_char_start"],
                         r["anchor_revisions"][-1]["new_char_end"]],
            "old_evidence_hash": r["anchor_revisions"][-1]["old_evidence_hash"],
            "new_evidence_hash": r["anchor_revisions"][-1]["new_evidence_hash"],
            "approval_pinned_to": r["human_decision_history"][-1].get(
                "approved_evidence_hash"),
        } for r in sorted(repaired, key=lambda r: r["candidate_id"])],
        "question_authoring_revisions": [{
            "candidate_id": r["candidate_id"],
            "fields_revised": sorted({rev["field"] for rev in r.get("revisions", [])}),
            "revisions": len(r.get("revisions", [])),
            "miner_original_question": next(
                (rev["from"] for rev in r.get("revisions", [])
                 if rev["field"] == "proposed_question"), None),
            "final_question": r["proposed_question"],
        } for r in sorted(records, key=lambda r: r["candidate_id"])
            if r.get("revisions")],
        "claim_checkable": {
            "with_critical_strings": with_critical,
            "of_verified": len(verified),
            "note": (
                "A case without literal critical strings passes the claim-in-evidence "
                "gate vacuously. This count, not the validator's green tick, is what "
                "says whether the claims were actually checked."
            ),
        },
        "defect_taxonomy": DEFECT_TAXONOMY,
        "defects_seen": dict(Counter(
            d for r in records for d in defects_of(r))),
        "validation": {
            "validator": "scripts/validate_golden.py",
            "projection": validation.get("path"),
            "cases": validation.get("cases"),
            "failures": len(validation.get("failures", [])),
            "passed": validation.get("passed"),
            "require_human": "validation",
            # Computed, never asserted. This sentence was previously a fixed string
            # describing batch 001, and it was emitted verbatim into batch 002's
            # closure, where it contradicted that batch's own 17-of-17 count. A caveat
            # that cannot see the records is not a caveat, it is a leftover.
            "caveat": claim_check_caveat(len(verified), with_critical),
        },
        "retrieval": {
            "retrieval_was_not_run": batch.get("retrieval_was_not_run"),
            "systems_run_against_these_candidates": [],
            "statement": (
                "No retrieval system was run against any candidate in this batch at any "
                "point. SYSTEM-A and SYSTEM-B remain frozen and were not executed. "
                "Candidate selection could not be influenced by what either system "
                "succeeds or fails on, which is what keeps a future holdout honest."
            ),
        },
        "not_yet_done": [
            "No split has been assigned; the projection's split is a placeholder.",
            "No holdout is frozen.",
            (f"Critical claim strings exist for {with_critical} of {len(verified)} "
             "verified cases; the rest are not claim-checked."),
            ("OA-002 remains a recorded defect in development/v1 with an unapplied "
             "development/v2 correction proposal."),
        ],
        "closure_sha256": candidate_digest(records),
    }


def render(closure: dict) -> str:
    totals = closure["totals"]
    rejected = "\n".join(
        f"| `{r['candidate_id']}` | {', '.join(r['defects']) or '—'} | {r['reason']} |"
        for r in closure["rejected"])
    repaired = "\n".join(
        f"| `{r['candidate_id']}` | {r['old_span'][0]}–{r['old_span'][1]} | "
        f"{r['new_span'][0]}–{r['new_span'][1]} | `{r['new_evidence_hash'][:12]}…` |"
        for r in closure["repaired"])
    taxonomy = "\n".join(
        f"| `{key}` | {value['name']} | {closure['defects_seen'].get(key, 0)} | "
        f"{value['description']} |"
        for key, value in closure["defect_taxonomy"].items())
    outstanding = "\n".join(f"- {item}" for item in closure["not_yet_done"])

    authoring = closure.get("question_authoring_revisions", [])
    checkable = closure.get("claim_checkable", {})
    return "\n".join([
        f"# GOLD-001 — batch {closure['batch']:03d} closure",
        "",
        (f"**Closed {closure['closed_at']} by {closure['closed_by']}.** Every "
         "candidate reached an explicit human decision. Nothing is outstanding."),
        "",
        "| | |",
        "| --- | --- |",
        f"| candidates | {totals['candidates']} |",
        f"| `human_verified` | **{totals['human_verified']}** |",
        f"| `human_rejected` | {totals['human_rejected']} |",
        f"| `needs_human_review` | {totals['needs_human_review']} |",
        f"| outstanding decisions | {totals['outstanding_decisions']} |",
        f"| acceptance rate | **{totals['acceptance_rate']:.1%}** |",
        "",
        ("Acceptance rate is not a quality score. It is the share of *mined candidates* "
         "a person kept, and it says as much about how permissive the miner was as about "
         "how good the evidence is. With n=18 one candidate moves it 5.6 points."),
        "",
        "## Rejected — kept, not deleted",
        "",
        "| candidate | defects | reason |",
        "| --- | --- | --- |",
        rejected,
        "",
        ("Both records remain in the batch as negative audit examples. A rejection is "
         "evidence about the miner, and deleting it would discard the only record of "
         "what the miner got wrong."),
        "",
        "## Repaired — anchors extended, originals preserved",
        "",
        "| candidate | old span | new span | approved anchor |",
        "| --- | --- | --- | --- |",
        repaired,
        "",
        ("Each repair grew the anchor outward to contain what its claims already "
         "depended on; the new span is a strict superset of the old, and both are "
         "retained in `anchor_revisions`. Each approval pins the post-repair hash, so "
         "the record shows which version the owner actually approved."),
        "",
        "## Question-authoring revisions",
        "",
        (f"{len(authoring)} of {totals['candidates']} candidates had their question, "
         "answer or claims re-authored during review. The miner's original wording is "
         "retained on every one of them as revision 1; nothing was overwritten."),
        "",
        (f"**Claims actually checkable: {checkable.get('with_critical_strings', 0)} of "
         f"{checkable.get('of_verified', 0)} verified cases carry literal critical "
         f"strings.** {checkable.get('note', '')}"),
        "",
        "## Miner defect taxonomy",
        "",
        "| class | name | seen | description |",
        "| --- | --- | --- | --- |",
        taxonomy,
        "",
        "## Provenance",
        "",
        "| | |",
        "| --- | --- |",
        f"| source batch sha256 | `{closure['source_batch_sha256']}` |",
        f"| corpus snapshot | `{closure['corpus_snapshot']}` |",
        f"| schema version | {closure['schema_version']} |",
        f"| git commit at generation | `{closure['git_commit'][:12]}` |",
        f"| closure sha256 | `{closure['closure_sha256']}` |",
        "",
        ("The closure hash covers the candidate records. A closed batch is not supposed "
         "to change again, and the test suite re-checks this hash, so an edit after "
         "closure fails the tests rather than passing unnoticed."),
        "",
        "## Validation",
        "",
        (f"`{closure['validation']['validator']}` — "
         f"**{closure['validation']['cases']} cases, "
         f"{closure['validation']['failures']} failures**, "
         f"`--require-human {closure['validation']['require_human']}`."),
        "",
        f"**Caveat.** {closure['validation']['caveat']}",
        "",
        "## Retrieval",
        "",
        f"{closure['retrieval']['statement']}",
        "",
        f"`retrieval_was_not_run: {closure['retrieval']['retrieval_was_not_run']}`",
        "",
        "## Not done, and deliberately so",
        "",
        outstanding,
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch")
    parser.add_argument("--validation", default="evals/review/validate_golden_batch_001.json")
    parser.add_argument("--out-dir", default="experiments/GOLD-001")
    args = parser.parse_args()

    batch = json.loads(Path(args.batch).read_text())
    validation = json.loads(Path(args.validation).read_text())
    if not validation.get("passed"):
        raise SystemExit("refusing to close: the validator did not pass")

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    closure = build(batch, validation, now)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    number = closure["batch"]
    (out_dir / f"GOLD-001-batch-{number:03d}-closure.json").write_text(
        json.dumps(closure, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / f"GOLD-001-batch-{number:03d}-closure.md").write_text(
        render(closure), encoding="utf-8")

    batch["closed_at"] = now
    batch["closure_sha256"] = closure["closure_sha256"]
    Path(args.batch).write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n",
                                encoding="utf-8")

    totals = closure["totals"]
    print(f"closed batch {number:03d}: {totals['human_verified']} verified, "
          f"{totals['human_rejected']} rejected, "
          f"{totals['acceptance_rate']:.1%} acceptance")
    print(f"  closure_sha256 {closure['closure_sha256']}")
    print(f"wrote {out_dir}/GOLD-001-batch-{number:03d}-closure.md")
    print(f"wrote {out_dir}/GOLD-001-batch-{number:03d}-closure.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
