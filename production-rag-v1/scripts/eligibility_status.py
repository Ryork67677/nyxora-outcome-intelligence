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

from rag_v1.gold.eligibility import evaluate

#: Batch, closed record, and the overlay that supersedes it for eligibility, if any.
SOURCES = (
    (1, "evals/review/gold_review_batch_001.json", "evals/gold/batch_001_v2/overlay.json"),
    (2, "evals/review/gold_review_batch_002.json", None),
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
        "overlay_version": overlay["overlay"] if overlay else None,
    }


def render(status: dict) -> str:
    rows = "\n".join(
        f"| {b['batch']:03d} | {b['candidates']} | {b['human_verified']} | "
        f"{b['human_rejected']} | **{b['holdout_eligible']}** | "
        f"{b['overlay_version'] or 'v1'} |"
        for b in status["batches"])
    combined = status["combined"]
    return "\n".join([
        "# GOLD-001 — eligibility status",
        "",
        f"As of {status['generated_at']}.",
        "",
        "| batch | candidates | `human_verified` | `human_rejected` | `holdout_eligible` | eligibility read from |",
        "| --- | --- | --- | --- | --- | --- |",
        rows,
        (f"| **all** | **{combined['candidates']}** | "
         f"**{combined['human_verified']}** | **{combined['human_rejected']}** | "
         f"**{combined['holdout_eligible']}** | |"),
        "",
        "## The two numbers are not the same question",
        "",
        ("`human_verified` counts approvals a person gave; it is historical and does not "
         "change. `holdout_eligible` counts cases a machine can still check — human "
         "approval, a deterministic check for every claim, critical strings present in "
         "the evidence, a valid evidence hash, and no unresolved scope defect, all "
         "holding now. A case can gain eligibility through added metadata without being "
         "re-approved, and lose it to corpus drift without the approval being wrong."),
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
        for key in ("candidates", "human_verified", "human_rejected", "holdout_eligible")
    }
    status = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "batches": batches,
        "combined": combined,
        "target": TARGET,
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
