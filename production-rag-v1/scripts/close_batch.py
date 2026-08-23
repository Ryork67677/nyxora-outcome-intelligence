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
    # Batches 001–003 keep one anchor on the record; batch 004 keeps a list. Ask for
    # whichever exists rather than assuming the older shape.
    body = (record.get("anchor_revisions", [{}])[0].get("old_evidence_text")
            or record.get("evidence_text")
            or " \n".join(s["evidence_text"]
                          for s in record.get("expected_evidence", [])))
    code = re.search(r"^\s*[\w.\[\]\"']+\s*=\s*\S|^\s*[\]\})],?\s*$|^\s*\"[\w_]+\"\s*:|"
                     r"^\s*raise\s|^\s*return\s", body, re.MULTILINE)
    classes = []
    if verification.get("evidence_boundary_complete") is False:
        classes.append("D1")
    if verification.get("identifier_value_binding_correct") is False:
        classes.append("D3" if code else "D2")
    return classes


def _repair_summary(record: dict) -> dict:
    """Describe an anchor repair in either recorded shape.

    Batch 001 grew a single span and recorded ``old_char_start``/``old_evidence_hash``.
    Batch 003 records span *lists*, because a repair may split one anchor into two
    precise spans rather than growing it outward.
    """
    latest = record["anchor_revisions"][-1]
    if "evidence_id" in latest:
        # Batch 004: one entry per repaired span, naming the span and what was done to
        # it. A span may be extended or added, so "old" is absent for an addition.
        extended = [r for r in record["anchor_revisions"]
                    if r["action"] == "extend_boundary"]
        added = [r for r in record["anchor_revisions"]
                 if r["action"] == "add_scope_span"]
        return {
            "candidate_id": record["candidate_id"],
            "reason": "; ".join(sorted({r["reason"] for r in record["anchor_revisions"]})),
            "actions": dict(Counter(r["action"] for r in record["anchor_revisions"])),
            "old_spans": [[r["old_char_start"], r["old_char_end"]] for r in extended],
            "new_spans": [[r["new_char_start"], r["new_char_end"]]
                          for r in record["anchor_revisions"]],
            "old_evidence_hashes": [r["old_evidence_hash"] for r in extended],
            "new_evidence_hashes": [r["new_evidence_hash"]
                                    for r in record["anchor_revisions"]],
            "scope_spans_added": [r["evidence_id"] for r in added],
            "approval_pinned_to": record["human_decision_history"][-1].get(
                "approved_evidence_hash"),
        }
    if "old_spans" in latest:
        old_spans = [[s["char_start"], s["char_end"]] for s in latest["old_spans"]]
        new_spans = [[s["char_start"], s["char_end"]] for s in latest["new_spans"]]
        old_hashes = [s["evidence_hash"] for s in latest["old_spans"]]
        new_hashes = [s["evidence_hash"] for s in latest["new_spans"]]
    else:
        old_spans = [[latest["old_char_start"], latest["old_char_end"]]]
        new_spans = [[latest["new_char_start"], latest["new_char_end"]]]
        old_hashes = [latest["old_evidence_hash"]]
        new_hashes = [latest["new_evidence_hash"]]
    return {
        "candidate_id": record["candidate_id"],
        "reason": latest["reason"],
        "old_spans": old_spans, "new_spans": new_spans,
        "old_evidence_hashes": old_hashes, "new_evidence_hashes": new_hashes,
        "approval_pinned_to": record["human_decision_history"][-1].get(
            "approved_evidence_hash"),
    }


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
        # Where repairs were kept out of the generation artifact, the batch a
        # decision attached to is a composed reviewed-state file. Both identities
        # are recorded, so a closure can be traced to the text a person saw *and*
        # to the generation run it came from.
        "generation_batch_sha256": batch.get("source_batch_sha256"),
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
            # Batch 004 had no independent model pass; its rejection came from the
            # internal source-integrity review and the owner's decision.
            "independent_verdict": r.get("verification", {}).get("verdict"),
            "internal_review_status": r.get("internal_review_status"),
            "preserved_as": "negative audit example - the record is kept, not deleted",
        } for r in sorted(rejected, key=lambda r: r["candidate_id"])],
        "repaired": [_repair_summary(r) for r in
                     sorted(repaired, key=lambda r: r["candidate_id"])],
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
        "by_provider": {
            "generated": dict(Counter(r["provider"] for r in records)),
            "human_verified": dict(Counter(r["provider"] for r in verified)),
        },
        "human_overrides": [{
            "candidate_id": r["candidate_id"],
            "anaphora_status": r.get("anaphora_status"),
            "dependency_status": r.get("dependency_status"),
            "human_anaphora_override": r.get("human_anaphora_override"),
            "human_dependency_override": r.get("human_dependency_override"),
            "override_reviewer": r.get("override_reviewer"),
            "finding_retained": True,
        } for r in sorted(records, key=lambda r: r["candidate_id"])
            if r.get("human_anaphora_override") or r.get("human_dependency_override")],
        "reasoning_and_shape": {
            # Counted from the records that closed, not from the generation-time
            # totals: a rejected candidate is still in the generated mix and must not
            # be in the verified one.
            "by_reasoning_type": dict(Counter(r["reasoning_type"] for r in records
                                              if r.get("reasoning_type"))),
            "by_reasoning_type_verified": dict(
                Counter(r["reasoning_type"] for r in verified if r.get("reasoning_type"))
            ) or batch.get("by_reasoning_type", {}),
            "by_evidence_shape": dict(Counter(r["evidence_shape"] for r in records
                                              if r.get("evidence_shape"))),
            "by_evidence_shape_verified": dict(
                Counter(r["evidence_shape"] for r in verified if r.get("evidence_shape"))
            ) or batch.get("by_evidence_shape", {}),
            "genuine_multi_hop": sum(
                1 for r in verified if r.get("reasoning_type") == "genuine_multi_hop"
            ) if any(r.get("reasoning_type") for r in records)
            else batch.get("genuine_multi_hop"),
            "note": (
                "Reasoning type and evidence shape are separate dimensions. A case "
                "needing two spans is multi_span; multi_hop is a reasoning type, and a "
                "case only earns it when the answer is derived from combining spans "
                "rather than being the spans' contents."
            ),
        },
        "errata": batch.get("closure_errata", []),
        "multi_hop_rejection": batch.get("multi_hop_rejection"),
        "near_miss_diagnostic": batch.get("near_miss_diagnostic"),
        "reasoning_targets": batch.get("reasoning_targets"),
        "precheck_limitation": {
            "candidates": len(records),
            "precheck_ready": sum(1 for r in records
                                  if r.get("precheck_holdout_ready")),
            # The review repaired more candidates than it re-anchored: a question
            # rewrite is a repair too. Counting anchors here understated it.
            "repaired": sum(1 for r in records
                            if r.get("internal_review_status") == "NEEDS_REPAIR"),
            "anchor_repairs": len(repaired),
            "reject_recommended": sum(
                1 for r in records
                if r.get("internal_review_status") == "REJECT_RECOMMENDED"),
            "means": "structurally capable",
            "does_not_mean": ["semantic correctness", "human approval",
                              "holdout eligibility"],
        } if any(r.get("internal_review_status") for r in records) else None,
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
             "verified cases" + ("; the rest are not claim-checked."
                                 if with_critical < len(verified) else
                                 ", so every one of them is claim-checked.")),
            ("OA-002 remains a recorded defect in development/v1 with an unapplied "
             "development/v2 correction proposal."),
        ],
        "closure_sha256": candidate_digest(records),
    }


def erratum_line(entry: dict) -> str:
    """Render an erratum in either recorded shape.

    Batch 002 and 003 recorded ``id``/``summary``/``detail``. Batch 004 records what was
    corrected, what it said, and what it should have said, which is the more useful
    shape and the one to prefer.
    """
    if "correction" in entry:
        return (f"- **{entry['correction']}** — was \"{entry['was']}\"; is "
                f"**{entry['is']}**. {entry['why']} Recorded in "
                f"`{entry['recorded_in']}`. Generation figures affected: "
                f"{'yes' if entry.get('affects_generation_figures') else 'no'}.")
    return f"- **{entry.get('id')}** — {entry.get('summary')} {entry.get('detail')}"


def multi_hop_line(closure: dict) -> str:
    count = closure["reasoning_and_shape"]["genuine_multi_hop"]
    target = closure.get("reasoning_targets", {}).get("genuine_multi_hop")
    against = f", against a generation target of {target[0]}–{target[1]}" if target else ""
    return f"**Genuine multi-hop reasoning cases: {count}**{against}."


def multi_hop_tail(closure: dict) -> str:
    """The sentence that follows the taxonomy note depends on what the batch found."""
    count = closure["reasoning_and_shape"]["genuine_multi_hop"]
    if count:
        return (
            f" This batch closed with {count}. That is one observation, and it proves "
            "the benchmark infrastructure can represent a genuine multi-hop case; it "
            "does not mean the category is adequately sampled. The generation figure "
            "below is the finding to carry forward.")
    return (" The multi-span cases in this batch are useful multi-evidence retrieval "
            "tests and are not relabelled to close the gap; a later batch has to target "
            "genuine multi-hop reasoning directly.")


def multi_hop_rejection_section(closure: dict) -> list[str]:
    rejection = closure.get("multi_hop_rejection")
    if not rejection:
        return []
    rows = "\n".join(f"| {reason.replace('_', ' ')} | {count} |"
                      for reason, count in sorted(rejection["reasons"].items(),
                                                  key=lambda kv: -kv[1]))
    return [
        "## What it cost to find one chain",
        "",
        (f"The composer tested **{rejection['attempted_pairs']}** bridge pairs. "
         f"**{rejection['passed']}** passed the composition check; "
         f"**{rejection['rejected']}** were rejected."),
        "",
        "| rejection reason | pairs |",
        "| --- | --- |",
        rows,
        "",
        ("This ratio is a result about the corpus and the authoring method, not a "
         "defect to be tuned away. In this corpus two facts that share an identifier "
         "are almost never two halves of an argument, and no candidate was regenerated "
         "to improve the number."),
        "",
    ]


def near_miss_section(closure: dict) -> list[str]:
    near = closure.get("near_miss_diagnostic")
    if not near:
        return []
    verdicts = Counter(near["verdicts"].values())
    rows = "\n".join(f"| `{entity}` | {verdict} |"
                      for entity, verdict in sorted(near["verdicts"].items()))
    return [
        "## Near-miss diagnostic",
        "",
        (f"**{near['pairs']}** bridge pairs cleared every check except the rule under "
         f"test — {near['rule_under_test']}. Reviewer verdicts: "
         + ", ".join(f"{count} {verdict}" for verdict, count in verdicts.most_common())
         + "."),
        "",
        "| bridge entity | verdict |",
        "| --- | --- |",
        rows,
        "",
        (f"Diagnostic only: {near['promoted_to_batch_004']} promoted into the batch, "
         f"batch regenerated: {str(near['batch_004_regenerated']).lower()}. Full "
         f"reasoning in `{near['document']}`."),
        "",
    ]


def overrides_section(closure: dict) -> list[str]:
    overrides = closure.get("human_overrides")
    if not overrides:
        return []
    rows = "\n".join(
        f"| `{o['candidate_id']}` | "
        f"{o.get('anaphora_status') or o.get('dependency_status')} | "
        f"{o['override_reviewer']} | finding retained |"
        for o in overrides)
    return [
        "## Human overrides",
        "",
        ("A noncritical finding blocks until a person accepts it. These were accepted, "
         "and none of them was deleted: the detector still reports every one, and a "
         "*critical* finding cannot be overridden at all."),
        "",
        "| candidate | finding | accepted by | disposition |",
        "| --- | --- | --- | --- |",
        rows,
        "",
    ]


def precheck_section(closure: dict) -> list[str]:
    precheck = closure.get("precheck_limitation")
    if not precheck:
        return []
    return [
        "## What `precheck_holdout_ready` does and does not mean",
        "",
        (f"This batch produced {precheck['precheck_ready']} of "
         f"{precheck['candidates']} candidates `precheck_holdout_ready`. The "
         f"source-integrity review that followed repaired {precheck['repaired']} of "
         f"them and recommended {precheck['reject_recommended']} for rejection."),
        "",
        ("That is not a precheck failure. The precheck is deliberately structural: it "
         "verifies hashes, offsets, string containment, anaphora and anchor size. It "
         "means **structurally capable** — not semantic correctness, not human "
         "approval, and not holdout eligibility. The review is what showed why the "
         "separation has to be maintained rather than assumed."),
        "",
    ]


def render(closure: dict) -> str:
    totals = closure["totals"]
    rejected = "\n".join(
        f"| `{r['candidate_id']}` | {', '.join(r['defects']) or '—'} | {r['reason']} |"
        for r in closure["rejected"])
    def spans(entries: list) -> str:
        return ", ".join(f"{a}–{b}" for a, b in entries)

    repaired = "\n".join(
        f"| `{r['candidate_id']}` | "
        f"{spans(r['old_spans']) or '— (scope span added)'} | "
        f"{spans(r['new_spans'])} | `{r['new_evidence_hashes'][0][:12]}…` |"
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
         "a person kept, and it says as much about how permissive the miner was as "
         f"about how good the evidence is. With n={totals['candidates']} one candidate "
         f"moves it {100 / totals['candidates']:.1f} points."),
        "",
        "## Rejected — kept, not deleted",
        "",
        "| candidate | defects | reason |",
        "| --- | --- | --- |",
        rejected,
        "",
        ((f"{'Both records remain' if len(closure['rejected']) == 2 else 'All rejected records remain'} "
          "in the batch as negative audit examples. A rejection is evidence about the "
          "miner, and deleting them would discard the only record of what the miner "
          "got wrong.") if len(closure["rejected"]) != 1 else
         ("The record remains in the batch as a negative audit example. A rejection is "
          "evidence about the miner, and deleting it would discard the only record of "
          "what the miner got wrong.")),
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
        "## Reasoning type and evidence shape",
        "",
        (f"Reasoning types: {closure['reasoning_and_shape']['by_reasoning_type']}. "
         f"Evidence shapes: {closure['reasoning_and_shape']['by_evidence_shape']}."),
        "",
        multi_hop_line(closure),
        "",
        (closure["reasoning_and_shape"]["note"] + multi_hop_tail(closure)),
        "",
        *multi_hop_rejection_section(closure),
        *near_miss_section(closure),
        *overrides_section(closure),
        *precheck_section(closure),
        *(["## Errata", ""] + [erratum_line(e) for e in closure["errata"]] + [""]
          if closure["errata"] else []),
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
        f"| reviewed-state sha256 | `{closure['source_batch_sha256']}` |",
        *([f"| generation batch sha256 | "
           f"`{closure['generation_batch_sha256']}` |"]
          if closure.get("generation_batch_sha256") else []),
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
