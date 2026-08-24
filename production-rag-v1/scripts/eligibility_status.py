#!/usr/bin/env python3
"""GOLD-001: report how many cases exist, and how many a holdout could actually use.

Two numbers, kept apart because they answer different questions. ``human_verified`` is
how many cases a person approved. ``holdout_eligible`` is how many of those a machine can
still check — every condition in ``rag_v1.gold.eligibility`` holding right now.

Counts are read from the records. Where a batch has a v2 overlay the overlay is the
current state of those cases and the closed v1 batch stays the historical record; both
are reported so the difference is visible rather than assumed.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.gold.eligibility import HOLDOUT_CONDITIONS, evaluate

#: Batch, closed record, and the overlay that supersedes it for eligibility, if any.
SOURCES = (
    (1, "evals/review/gold_review_batch_001.json", "evals/gold/batch_001_v2/overlay.json"),
    (2, "evals/review/gold_review_batch_002.json", None),
    (3, "evals/review/gold_review_batch_003.json", None),
    # Batch 004 kept repairs out of its generation artifact, so its decided state is the
    # composed file the owner's decisions were imported into.
    (4, "evals/review/gold_review_batch_004_final.json", None),
    # Batch 005 followed the same composition: repairs live beside the generation
    # artifact, and the decided state is the composed file.
    (5, "evals/review/gold_review_batch_005_final.json", None),
)
#: What the project is aiming at. Reported so a count can be read against a target
#: instead of in a vacuum.
TARGET = {"validation": "30–40", "holdout": "70–100"}


def count(batch_path: str, overlay_path: str | None) -> dict:
    batch = json.loads(Path(batch_path).read_text())
    records = batch["records"]
    verified = [r for r in records if r["verification_status"] == "human_verified"]
    rejected = [r for r in records if r["verification_status"] == "human_rejected"]

    if overlay_path and Path(overlay_path).exists():
        overlay = json.loads(Path(overlay_path).read_text())
        cases = overlay["case_records"]
        source = overlay_path
    else:
        cases, overlay, source = verified, None, batch_path

    verdicts = {c["candidate_id"]: evaluate(c) for c in cases}
    eligible = sorted(cid for cid, v in verdicts.items() if v["holdout_eligible"])
    return {
        "batch": batch.get("batch"),
        "closed_record": batch_path,
        "eligibility_source": source,
        "closure_sha256": batch.get("closure_sha256"),
        "candidates": len(records),
        "human_verified": len(verified),
        "human_rejected": len(rejected),
        "holdout_eligible": len(eligible),
        "holdout_eligible_ids": eligible,
        "not_eligible": sorted({v["candidate_id"] for v in verdicts.values()}
                               - set(eligible)),
        # Reported per batch because the project-wide figure is the one that is easy to
        # overstate, and because a category with a single member should look like one.
        "genuine_multi_hop": sum(
            1 for c in cases
            if c.get("reasoning_type") == "genuine_multi_hop"
            and c["candidate_id"] in set(eligible)),
        "overlay_version": overlay["overlay"] if overlay else None,
    }


def multi_hop_section(status: dict) -> list[str]:
    """Say what the multi-hop number is, and refuse to let it sound like coverage."""
    count = status["combined"]["genuine_multi_hop"]
    total = status["combined"]["holdout_eligible"]
    tested = status.get("multi_hop_generation", {})
    lines = [
        "## Genuine multi-hop",
        "",
        (f"**{count} of {total} eligible cases** is a genuine multi-hop reasoning case."
         if count else
         "**No eligible case** is a genuine multi-hop reasoning case."),
        "",
    ]
    if count:
        lines += [
            ("That is one observation. It proves the benchmark infrastructure can "
             "represent a genuine multi-hop case — anchor it, check its composition, "
             "and carry it through review — and it does not mean the category is "
             "adequately sampled. A single case cannot support a claim about how any "
             "system handles multi-hop reasoning."),
            "",
        ]
    if tested:
        lines += [
            (f"Batch 004's composer tested **{tested['attempted_pairs']}** bridge pairs "
             f"and **{tested['passed']}** passed the composition check. That ratio is a "
             "finding about the corpus and the authoring method, not a defect that was "
             "tuned away: two facts sharing an identifier are almost never two halves "
             "of an argument."),
            "",
        ]
    second = status.get("multi_hop_dependency_first") or {}
    if second:
        funnel = second["funnel"]
        lines += [
            (f"Batch 005 searched the same corpus dependency-first instead — only "
             "sentences that state a dependency may open a chain — and reached the "
             f"composition gates with **{funnel['dependency_pairs_considered']}** "
             f"pairs. **{second['valid_chains']}** was a valid chain, and it is the "
             f"chain batch 004 already closed, so **{second['exported_chains']}** new "
             "unique chains were exported."),
            "",
            ("Two searches, two methods, one composable structure. That is a measured "
             "property of this frozen corpus, not a failure of either search, and it "
             "is the reason the multi-hop count above is 1 rather than a number a "
             "later batch can be expected to raise easily."),
            "",
        ]
    return lines


def render(status: dict) -> str:
    rows = "\n".join(
        f"| {b['batch']:03d} | {b['candidates']} | {b['human_verified']} | "
        f"{b['human_rejected']} | **{b['holdout_eligible']}** | "
        f"{b['genuine_multi_hop']} | {b['overlay_version'] or 'v1'} |"
        for b in status["batches"])
    combined = status["combined"]
    return "\n".join([
        "# GOLD-001 — eligibility status",
        "",
        f"As of {status['generated_at']}.",
        "",
        ("| batch | candidates | `human_verified` | `human_rejected` | "
         "`holdout_eligible` | genuine multi-hop | eligibility read from |"),
        "| --- | --- | --- | --- | --- | --- | --- |",
        rows,
        (f"| **all** | **{combined['candidates']}** | "
         f"**{combined['human_verified']}** | **{combined['human_rejected']}** | "
         f"**{combined['holdout_eligible']}** | "
         f"**{combined['genuine_multi_hop']}** | |"),
        "",
        *multi_hop_section(status),
        "## The two numbers are not the same question",
        "",
        ("`human_verified` counts approvals a person gave; it is historical and does "
         "not change. `holdout_eligible` counts cases a machine can still check: every "
         "one of "
         + ", ".join(f"`{condition}`" for condition in HOLDOUT_CONDITIONS)
         + " holding right now. The list is read from `rag_v1.gold.eligibility`, so a "
           "condition added to the gate appears here instead of being described from "
           "memory. A case can gain eligibility through added metadata without being "
           "re-approved, and lose it to corpus drift without the approval being "
           "wrong."),
        "",
        "## Against the target",
        "",
        (f"The project is aiming at roughly **{TARGET['validation']} validation** "
         f"cases and **{TARGET['holdout']} holdout** cases."),
        "",
        (f"**{combined['holdout_eligible']} eligible cases is not enough for both.** "
         "Splitting them would leave a holdout too small to measure with and a "
         "validation set too small to develop against, and every case spent on "
         "validation is a case the holdout will never see. No holdout is frozen, and "
         "none should be until the count supports the split."),
        "",
        "## Untouched",
        "",
        ("SYSTEM-A and SYSTEM-B remain frozen and have not been executed against any "
         "GOLD-001 candidate. No candidate-selection step has seen a retrieval outcome, "
         "which is the property that makes a future holdout worth having."),
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="experiments/GOLD-001")
    args = parser.parse_args()

    batches = [count(record, overlay) for _, record, overlay in SOURCES]
    combined = {
        key: sum(b[key] for b in batches)
        for key in ("candidates", "human_verified", "human_rejected",
                    "holdout_eligible", "genuine_multi_hop")
    }
    generation = Path("experiments/GOLD-001/GOLD-001-batch-004-generation-report.json")
    multi_hop_generation = (
        json.loads(generation.read_text())["multi_hop_rejection"]
        if generation.exists() else {})
    # Batch 005 searched the same corpus a different way. Both results belong here:
    # a project-wide multi-hop number that cites only the first search implies the
    # second one has not happened.
    dependency_first = Path(
        "experiments/GOLD-001/GOLD-001-batch-005-generation-report.json")
    multi_hop_dependency_first = (
        json.loads(dependency_first.read_text()).get("multi_hop_search", {})
        if dependency_first.exists() else {})
    status = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "batches": batches,
        "combined": combined,
        "target": TARGET,
        "multi_hop_generation": multi_hop_generation,
        "multi_hop_dependency_first": multi_hop_dependency_first,
        "holdout_frozen": False,
        "reason_not_frozen": (
            f"{combined['holdout_eligible']} eligible cases cannot support both a "
            f"{TARGET['validation']} validation split and a {TARGET['holdout']} holdout."
        ),
        "retrieval_was_not_run": True,
        "systems_executed": [],
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "GOLD-001-eligibility-status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "GOLD-001-eligibility-status.md").write_text(render(status), encoding="utf-8")

    for batch in batches:
        print(f"  batch {batch['batch']:03d}: {batch['human_verified']} verified, "
              f"{batch['human_rejected']} rejected, "
              f"{batch['holdout_eligible']} eligible "
              f"({batch['overlay_version'] or 'v1'})")
    print(f"  combined: {combined['human_verified']} verified, "
          f"{combined['holdout_eligible']} eligible")
    print(f"wrote {out_dir}/GOLD-001-eligibility-status.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
