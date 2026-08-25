#!/usr/bin/env python3
"""GOLD-001: preregister the batch-007 authoring contract, before any candidate exists.

Batch 006 exported nine against a target of twenty-eight and its census said why: 699
distinct evidence spans in the frozen snapshot are unspent, and no deterministic
template could turn them into a question without paraphrasing. The corpus is not the
constraint. The authoring is.

Batch 007 answers that with **controlled evidence-grounded paraphrasing** — a model may
author the question, but never the fact. This document fixes the contract for that
before a single candidate is generated, which is the whole point of preregistering: a
rule written after seeing the output is a rule fitted to the output.

Every number here is read from the closed record — the eligibility status, batch 006's
closure, its census, its review's defect list. Nothing is typed in.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.gold.defects import normalise_all

STATUS = "experiments/GOLD-001/GOLD-001-eligibility-status.json"
CLOSURE = "experiments/GOLD-001/GOLD-001-batch-006-closure.json"
REVIEW = "experiments/GOLD-001/b006-review-decisions.json"
BATCH_006 = "evals/review/gold_review_batch_006_final.json"

#: §17. Quality remains the gate: a lane that yields 25 strong cases returns 25.
TARGET_RANGE = (35, 40)
#: §12. The project target the owner set in this brief.
PROJECT_TARGET = 150
#: §18-§19. The pilot that has to pass before the lane may scale.
PILOT_SIZE = 10
PILOT_CRITERIA = {
    "independently_judged_factually_sound": {"minimum": 8, "of": PILOT_SIZE},
    "unsupported_claims": {"maximum": 0},
    "relation_direction_reversals": {"maximum": 0},
    "scope_broadening": {"maximum": 0},
    "wording_cleanup_needed": {"acceptable": True,
                               "note": "cosmetic repair does not count against the "
                                       "criterion"},
}

#: §13. The entailment self-check, verbatim from the brief. Any failure drops the
#: candidate — there is no "flag and continue" branch, deliberately.
ENTAILMENT_CHECKS = [
    {"id": "A", "question": "Does the exact evidence support the complete answer?",
     "fails_when": "any part of the answer is not derivable from the anchored spans"},
    {"id": "B", "question": "Does every atomic claim map to literal evidence?",
     "fails_when": "a claim has no span whose text supports it"},
    {"id": "C", "question": "Did the question introduce any new condition?",
     "fails_when": "the question adds an 'if', 'when' or 'unless' the source lacks"},
    {"id": "D", "question": "Did it broaden model/provider/platform scope?",
     "fails_when": "the source names a model, provider, platform or surface and the "
                   "question drops or generalises it"},
    {"id": "E", "question": "Did it reverse the relation?",
     "fails_when": "the question's subject is the source's object and vice versa, and "
                   "the relation is not symmetric"},
    {"id": "F", "question": "Did it introduce a causal claim absent from the source?",
     "fails_when": "the answer explains why, and the source only says what"},
    {"id": "G", "question": "Could the answer be verified using only the exact "
                            "evidence?",
     "fails_when": "verifying it needs the surrounding document, a heading, or outside "
                   "knowledge"},
]

#: §14. The order is the safeguard. Reversing it — question first, then hunt for
#: evidence — is how a benchmark ends up testing what the author imagined.
AUTHORING_ORDER = [
    "frozen source evidence selected",
    "literal source fact extracted",
    "subject / relation / object recorded",
    "atomic claims anchored",
    "only then the natural question is paraphrased",
]
FORBIDDEN_ORDER = "invent question → search for supporting evidence"

#: §13. Recorded on every paraphrased candidate, so a reviewer can see the literal fact
#: beside the authored question and disagree with the gap between them.
REQUIRED_FIELDS = [
    "source_fact_literal", "source_subject", "source_relation", "source_object",
    "generated_question", "generated_answer", "generated_atomic_claims",
    "paraphrase_used",
]

#: §20. Controlled paraphrasing is an additional authoring method, not a weaker
#: pipeline. Each of these already exists and each still runs.
RETAINED_GATES = [
    ("bare definition scope", "rag_v1.gold.scoping", "every span, independently"),
    ("critical anaphora", "rag_v1.gold.anaphora", "blocks; noncritical flags"),
    ("subject / relation direction", "rag_v1.gold.relations",
     "REVERSED and SUBJECT_MISMATCH both drop"),
    ("question form matches evidence form", "rag_v1.gold.questionform",
     "negative-as-positive and truncated predicates drop"),
    ("duplicate detection", "scripts/export_batch_007.py",
     "question text, span offsets, span text — and now the relation triple"),
    ("critical strings", "rag_v1.gold.normalisation",
     "every one must be literally inside its own span"),
    ("evidence hashes", "scripts/export_batch_007.py",
     "each span hashes to its own text"),
    ("scope self-containment", "rag_v1.gold.scoping",
     "section_path is never claim scope"),
    ("example-code restriction", "scripts/export_batch_007.py",
     "a sample configuration is not a rule"),
    ("evidence size", "scripts/export_batch_007.py",
     "<500 preferred, 1000 soft cap, 1500 hard cap"),
    ("provider / model scope", "scripts/export_batch_007.py",
     "a scoped source needs a scoped question"),
    ("holdout eligibility", "rag_v1.gold.eligibility",
     "deterministic, run after owner approval"),
]

#: §16. Unchanged, and restated because a new authoring method is exactly when it would
#: be convenient to forget.
WORKFLOW = [
    "frozen evidence",
    "Claude authoring",
    "Claude internal semantic self-review",
    "ChatGPT independent verification",
    "project-owner approval",
    "holdout eligibility",
]


def read_state() -> dict:
    status = json.loads(Path(STATUS).read_text())
    closure = json.loads(Path(CLOSURE).read_text())
    review = json.loads(Path(REVIEW).read_text())
    batch = json.loads(Path(BATCH_006).read_text())
    combined = status["combined"]
    eligible = combined["holdout_eligible"]
    return {
        "read_from": [STATUS, CLOSURE, REVIEW, BATCH_006],
        "human_verified": combined["human_verified"],
        "holdout_eligible": eligible,
        "human_rejected": combined["human_rejected"],
        "genuine_multi_hop": combined["genuine_multi_hop"],
        "candidates": combined["candidates"],
        "holdout_frozen": status["holdout_frozen"],
        "retrieval_was_not_run": status["retrieval_was_not_run"],
        "project_target": PROJECT_TARGET,
        "still_needed": max(PROJECT_TARGET - eligible, 0),
        "batch_006": {
            "target": closure["generation_shortfall"]["target"],
            "exported": closure["generation_shortfall"]["exported"],
            "approved": closure["totals"]["human_verified"],
            "rejected": closure["totals"]["human_rejected"],
            "holdout_eligible": closure["totals"]["holdout_eligible"],
            "acceptance_rate": closure["totals"]["acceptance_rate"],
            "closure_sha256": closure["closure_sha256"],
        },
        "corpus_census": closure["corpus_census"],
        "unbuildable_at_generation": batch.get("removed", {}).get("unbuildable"),
        "defects_from_review": normalise_all(review.get("generator_defects_found")),
        "acceptance_rates": {
            f"{b['batch']:03d}": round(
                b["human_verified"] / (b["human_verified"] + b["human_rejected"]), 4)
            for b in status["batches"]
            if b["human_verified"] + b["human_rejected"]},
    }


def projection(state: dict) -> dict:
    """What batch 007 would and would not achieve, at the observed acceptance rates."""
    eligible = state["holdout_eligible"]
    low_target, high_target = TARGET_RANGE
    rates = list(state["acceptance_rates"].values())
    worst, best = min(rates), max(rates)
    return {
        "confirmed_now": eligible,
        "project_target": PROJECT_TARGET,
        "still_needed": state["still_needed"],
        "batch_007_target": f"{low_target}-{high_target}",
        "if_low_target_at_worst_rate": eligible + int(low_target * worst),
        "if_high_target_at_best_rate": eligible + int(high_target * best),
        "reaches_target_this_batch": eligible + int(high_target * best) >= PROJECT_TARGET,
        "note": (
            "A projection, not a plan. It is recorded so nobody has to compute it "
            "during review, and it must not influence any individual approval. If "
            "controlled paraphrasing yields only 25 strong cases, batch 007 returns 25."
        ),
    }


def build() -> dict:
    state = read_state()
    return {
        "document": "GOLD-001 batch 007 preregistration",
        "status": "PREREGISTERED — no batch-007 candidate has been generated",
        "written_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "corpus_snapshot": "snap_689e336380a054d8039dc35b2c09cd0a",
        "starting_state": state,
        "projection": projection(state),
        "strategy_change": {
            "name": "controlled evidence-grounded question paraphrasing",
            "what_changes": "how a question is authored",
            "what_does_not_change": [
                "the evidence, which stays frozen and exact",
                "the ground truth, which is still read out of the source",
                "every existing safety gate",
                "the requirement for independent verification and owner approval",
            ],
            "why": (
                f"Batch 006 exported {state['batch_006']['exported']} against a target "
                f"of {state['batch_006']['target']}. "
                f"{state['corpus_census']['unspent_distinct_texts']} distinct evidence "
                "spans are unspent and "
                f"{state['unbuildable_at_generation']} mined facts reached no builder. "
                "Deterministic templates cannot express the long multi-clause prose "
                "that remains, and refusing any paraphrase is what keeps those facts "
                "out of the benchmark."),
            "the_line": (
                "The authoring model may change WORDING. It may not change MEANING. It "
                "authors the QUESTION; it never invents the FACT."),
        },
        "authoring_order": AUTHORING_ORDER,
        "forbidden_order": FORBIDDEN_ORDER,
        "required_fields_on_paraphrased_candidates": REQUIRED_FIELDS,
        "entailment_self_check": ENTAILMENT_CHECKS,
        "on_any_failure": "DROP",
        "answer_conservatism": {
            "rule": ("The question may be naturalised more aggressively than the "
                     "answer. Prefer answers close to the source wording."),
            "example_source": "A overrides B",
            "example_good_answer": "A overrides B",
            "example_bad_answer": "A overrides B because this improves reliability",
            "why_bad": ("The reason is not in the source. An answer that explains is an "
                        "answer that asserts something the evidence cannot check."),
        },
        "batch_007_target": {
            "range": list(TARGET_RANGE),
            "floor_is_not_a_quota": (
                "Quality remains the gate. If controlled paraphrasing yields only 25 "
                "strong cases, return 25. Do not pad."),
        },
        "calibration_pilot": {
            "required_before_scaling": True,
            "size": PILOT_SIZE,
            "selection": (
                "10 evidence spans that failed batch 006 ONLY because no builder could "
                "express them — NO_BUILDER / UNBUILDABLE. Not spans that failed a "
                "semantic gate: those failed for reasons paraphrasing does not fix."),
            "run": "the new controlled paraphraser, then every semantic check",
            "independent_review_required": True,
            "success_criteria": PILOT_CRITERIA,
            "if_it_fails": (
                "Do not scale the paraphrasing lane. Revise the authoring contract "
                "first and re-pilot."),
            "retrieval": "no retrieval is run on the pilot",
        },
        "retained_gates": [
            {"gate": name, "implemented_in": module, "behaviour": behaviour}
            for name, module, behaviour in RETAINED_GATES],
        "workflow_unchanged": WORKFLOW,
        "who_may_set_human_verified": (
            "Only the project owner. No AI may set human_verified, and controlled "
            "paraphrasing does not make Claude authoritative about anything."),
        "generator_defects_to_fix_first": state["defects_from_review"],
        "invariants": {
            "retrieval_was_not_run": True,
            "systems_executed": [],
            "holdout_frozen": False,
            "validation_frozen": False,
            "closed_batches_immutable": [1, 2, 3, 4, 5, 6],
            "corpus_snapshot_unchanged": True,
        },
        "not_done_in_this_document": [
            "No batch-007 candidate was generated.",
            "No pilot was run.",
            "No paraphraser was implemented.",
            "No retrieval was run.",
            "Nothing was frozen.",
        ],
    }


def render(doc: dict) -> str:
    state = doc["starting_state"]
    proj = doc["projection"]
    census = state["corpus_census"]
    b6 = state["batch_006"]

    checks = "\n".join(f"| **{c['id']}** | {c['question']} | {c['fails_when']} |"
                       for c in doc["entailment_self_check"])
    gates = "\n".join(f"| {g['gate']} | `{g['implemented_in']}` | {g['behaviour']} |"
                      for g in doc["retained_gates"])
    defects = "\n".join(
        f"| **{d['id']}** | {d['defect']} | `{d['seen_in']}` |"
        for d in doc["generator_defects_to_fix_first"])
    order = "\n".join(f"{i}. {step}" for i, step in enumerate(doc["authoring_order"], 1))
    rates = " · ".join(f"{b} {r:.0%}" for b, r in state["acceptance_rates"].items())

    return "\n".join([
        "# GOLD-001 — batch 007 preregistration",
        "",
        "**Controlled evidence-grounded question paraphrasing.**",
        "",
        (f"*{doc['status']}. Written {doc['written_at']} against corpus snapshot "
         f"`{doc['corpus_snapshot']}`.*"),
        "",
        ("This document fixes the authoring contract for batch 007 **before any "
         "candidate exists**. That is the point of preregistering: a rule written after "
         "seeing the output is a rule fitted to the output. Every figure below is read "
         "from the closed record."),
        "",
        "## Why the method is changing",
        "",
        (f"Batch 006 was commissioned at **{b6['target']}** candidates and exported "
         f"**{b6['exported']}**. Its census is why:"),
        "",
        "| | |",
        "| --- | --- |",
        f"| facts mined | {census['facts_mined']} |",
        (
    f"| distinct evidence spans the miners reach | "
            f"{census['distinct_evidence_texts']} |"
        ),
        (
    f"| **unspent by any closed batch** | "
            f"**{census['unspent_distinct_texts']}** |"
        ),
        (
    f"| mined facts that reached no builder | "
            f"{state['unbuildable_at_generation']} |"
        ),
        "",
        (f"**The corpus is not exhausted. The authoring is.** "
         f"{census['unspent_distinct_texts']} distinct spans have never been used, and "
         "deterministic templates cannot express them: what remains in this snapshot is "
         "long, multi-clause prose, and a template that fits it is a template that "
         "invents wording. Refusing all paraphrase is precisely what keeps those facts "
         "out of the benchmark."),
        "",
        "## The line this batch draws",
        "",
        f"> {doc['strategy_change']['the_line']}",
        "",
        ("This is an **authoring** change. The evidence stays frozen and exact, the "
         "ground truth is still read out of the source, and every existing gate still "
         "runs. What changes is that a model may write the question when a template "
         "cannot."),
        "",
        "### The order is the safeguard",
        "",
        order,
        "",
        (
    f"**Never:** {doc['forbidden_order']}. Inventing a question and then hunting "
            "for evidence to support it is how a benchmark ends up testing what its author "
            "imagined rather than what the documentation says."
        ),
        "",
        "### Recorded on every paraphrased candidate",
        "",
        "\n".join(f"- `{field}`" for field in
                  doc["required_fields_on_paraphrased_candidates"]),
        "",
        ("The literal source fact sits on the record beside the authored question, so a "
         "reviewer can see the gap between them and disagree with it."),
        "",
        "## The entailment self-check",
        "",
        "| | check | it fails when |",
        "| --- | --- | --- |",
        checks,
        "",
        (
    f"**Any failure: {doc['on_any_failure']}.** There is no flag-and-continue "
            "branch, deliberately — a caveat in a benchmark is a defect with an excuse."
        ),
        "",
        "## Answer conservatism",
        "",
        doc["answer_conservatism"]["rule"],
        "",
        (
    f"Source says *{doc['answer_conservatism']['example_source']}* →️ answer "
            f"*{doc['answer_conservatism']['example_good_answer']}*, **not** "
            f"*{doc['answer_conservatism']['example_bad_answer']}*. "
            f"{doc['answer_conservatism']['why_bad']}"
        ),
        "",
        "## Calibration pilot — required before the lane scales",
        "",
        (f"**{doc['calibration_pilot']['size']} spans**, selected as: "
         f"{doc['calibration_pilot']['selection']}"),
        "",
        "| criterion | threshold |",
        "| --- | --- |",
        (
    f"| independently judged factually sound | ≥ "
            f"{PILOT_CRITERIA['independently_judged_factually_sound']['minimum']} of "
            f"{PILOT_SIZE} |"
        ),
        "| unsupported claims | 0 |",
        "| relation-direction reversals | 0 |",
        "| scope broadening | 0 |",
        "| wording cleanup needed | acceptable, does not count against the criterion |",
        "",
        f"**If it fails:** {doc['calibration_pilot']['if_it_fails']}",
        "",
        (
    f"The pilot is independently reviewed before the lane may scale, and "
            f"{doc['calibration_pilot']['retrieval']}."
        ),
        "",
        "## Every existing gate still runs",
        "",
        "| gate | implemented in | behaviour |",
        "| --- | --- | --- |",
        gates,
        "",
        ("Controlled paraphrasing is an **additional authoring method, not a weaker "
         "pipeline**."),
        "",
        "## Generator defects to fix before batch 007 authors anything",
        "",
        "| | defect | seen in |",
        "| --- | --- | --- |",
        defects,
        "",
        "\n\n".join(
            f"**{d['id']}. {d['defect']}** — {d['detail']}\n\n*Proposed fix:* "
            f"{d['proposed_fix']}"
            for d in doc["generator_defects_to_fix_first"] if d.get("proposed_fix")),
        "",
        "## Where the project stands",
        "",
        "| | |",
        "| --- | --- |",
        f"| human_verified | **{state['human_verified']}** |",
        f"| holdout_eligible | **{state['holdout_eligible']}** |",
        f"| rejected | {state['human_rejected']} |",
        f"| genuine multi-hop | {state['genuine_multi_hop']} |",
        f"| project target | **{PROJECT_TARGET}** |",
        f"| still needed | **{state['still_needed']}** |",
        "",
        (f"Batch 007 targets **{proj['batch_007_target']}** candidates. At the observed "
         f"acceptance rates ({rates}), that lands between "
         f"**{proj['if_low_target_at_worst_rate']}** and "
         f"**{proj['if_high_target_at_best_rate']}** eligible cases — "
         + ("enough to reach the target in one batch."
            if proj["reaches_target_this_batch"] else
            f"short of {PROJECT_TARGET}, so more than one batch will be needed.")),
        "",
        f"*{proj['note']}*",
        "",
        "## Who may set `human_verified`",
        "",
        doc["who_may_set_human_verified"],
        "",
        "Workflow, unchanged: " + " → ".join(f"**{step}**" for step in
                                             doc["workflow_unchanged"]) + ".",
        "",
        "## Not done in this document",
        "",
        "\n".join(f"- {item}" for item in doc["not_done_in_this_document"]),
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="experiments/GOLD-001")
    args = parser.parse_args()

    doc = build()
    state = doc["starting_state"]
    if state["holdout_frozen"] or not state["retrieval_was_not_run"]:
        raise SystemExit("refusing to preregister: the project state is not what a "
                         "preregistration assumes — stop and diagnose")
    if not doc["generator_defects_to_fix_first"]:
        raise SystemExit("refusing to preregister: batch 006's review recorded defects "
                         "and none were read")

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "GOLD-001-batch-007-preregistration.json").write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "GOLD-001-batch-007-preregistration.md").write_text(render(doc),
                                                               encoding="utf-8")
    print(f"preregistered batch 007: target {doc['projection']['batch_007_target']}, "
          f"pilot {PILOT_SIZE}, project target {PROJECT_TARGET}")
    print(f"  holdout_eligible now {state['holdout_eligible']}, "
          f"still needed {state['still_needed']}")
    print(f"  defects to fix first: "
          f"{[d['id'] for d in doc['generator_defects_to_fix_first']]}")
    print(f"wrote {out}/GOLD-001-batch-007-preregistration.md")
    print(f"wrote {out}/GOLD-001-batch-007-preregistration.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
