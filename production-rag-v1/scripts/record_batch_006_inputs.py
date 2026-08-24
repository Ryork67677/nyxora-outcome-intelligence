#!/usr/bin/env python3
"""GOLD-001: record what batch 005 learned as preregistration inputs for batch 006.

This writes no generator code and changes no batch. A defect found while reviewing a
batch is evidence about the miner, and the place for it is the *next* batch's
preregistration — patching the batch it was found in would destroy the evidence and
leave the miner unfixed.

Every entry is sourced: three come from ``generator_defects_found`` on the closed
batch-005 record, and the fourth from the rejection that motivated it. Nothing here is
retyped from prose.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

BATCH = Path("evals/review/gold_review_batch_005_final.json")
CLOSURE = Path("experiments/GOLD-001/GOLD-001-batch-005-closure.json")

#: The check each defect asks batch 006 to carry, and how it would be verified. Written
#: here because it is a decision about the next batch, not a fact about this one.
PROPOSED = {
    "the bare-definition-bullet rule only inspects single-span records": {
        "id": "A",
        "check": ("Extend the bare-definition-bullet scope rule to every span of a "
                  "multi-span record, not only records with exactly one span."),
        "verified_by": ("A regression case built from GOLD-B005-01's two bullets: the "
                        "rule must drop it."),
    },
    "markdown reference links survive into questions built from conditional sentences": {
        "id": "B",
        "check": ("Strip markdown reference links whose label is itself backticked, "
                  "before a question is composed."),
        "verified_by": ("A regression case using GOLD-B005-15's original question "
                        "text: no bracket or link label may survive into the "
                        "question."),
    },
    "prose mistaken for a section heading by the parser": {
        "id": "C",
        "check": ("Audit the heading parser against the corpus snapshot and record how "
                  "often ordinary prose is captured as a `section_path`. Do NOT fix "
                  "historical parser output in place; closed batches keep what they "
                  "have."),
        "verified_by": ("A count from the snapshot, reported before batch 006 "
                        "generation, plus a rule that a `section_path` ending in a "
                        "sentence-final period is not used as scope."),
    },
}

#: Defect D is not a generator bug the batch-005 run recorded — it is the check that
#: caught GOLD-B005-10 and must not be allowed to lapse. Sourced from that rejection.
DIRECTION = {
    "id": "D",
    "defect": "subject–relation direction must remain explicitly checked",
    "check": ("Every generated question must be re-read against its span for relation "
              "direction: the question's subject must be the source's subject, not its "
              "object."),
    "verified_by": ("The GOLD-B005-10 rejection is kept as the regression case — the "
                    "source says the experimental model rejects caller-supplied "
                    "`betas` overrides, and a question asking what `betas` overrides "
                    "must not survive generation."),
    "seen_in": "GOLD-B005-10",
}


def build(now: str) -> dict:
    batch = json.loads(BATCH.read_text())
    closure = json.loads(CLOSURE.read_text())
    recorded = batch["generator_defects_found"]

    unknown = [d["defect"] for d in recorded if d["defect"] not in PROPOSED]
    if unknown:
        raise SystemExit(
            "refusing to write: batch 005 recorded a defect this script has no "
            "proposed check for — " + "; ".join(unknown))

    rejected = {r["candidate_id"]: r for r in closure["rejected"]}
    if DIRECTION["seen_in"] not in rejected:
        raise SystemExit(
            f"refusing to write: {DIRECTION['seen_in']} is not a rejected candidate in "
            "the batch-005 closure, so defect D has no source")

    inputs = [{
        **PROPOSED[d["defect"]],
        "defect": d["defect"],
        "seen_in": d["seen_in"],
        "detail": d["detail"],
        "source": "evals/review/gold_review_batch_005_final.json:generator_defects_found",
    } for d in recorded]
    inputs.append({
        **DIRECTION,
        "detail": rejected[DIRECTION["seen_in"]]["reason"],
        "source": "experiments/GOLD-001/GOLD-001-batch-005-closure.json:rejected",
    })
    inputs.sort(key=lambda entry: entry["id"])

    return {
        "document": "GOLD-001 batch 006 preregistration inputs",
        "recorded_at": now,
        "recorded_by": "project_owner",
        "status": "inputs only — batch 006 is not generated, designed or preregistered",
        "source_batch": {
            "batch": closure["batch"],
            "closure_sha256": closure["closure_sha256"],
            "reviewed_state_sha256": closure["source_batch_sha256"],
            "generation_batch_sha256": closure["generation_batch_sha256"],
        },
        "inputs": inputs,
        "not_done": [
            "No batch-006 generation was run.",
            ("No miner was changed. These are inputs to a future preregistration, and a "
            "fix applied now would be a change nobody preregistered."),
            ("Batch 005's generation artifact is unmodified; the defects are recorded "
            "against it, not patched into it."),
        ],
    }


def render(doc: dict) -> str:
    rows = []
    for entry in doc["inputs"]:
        rows.extend([
            f"### {entry['id']}. {entry['defect']}",
            "",
            f"**Seen in** `{entry['seen_in']}`. {entry['detail']}",
            "",
            f"**Check batch 006 must carry.** {entry['check']}",
            "",
            f"**Verified by.** {entry['verified_by']}",
            "",
            f"Source: `{entry['source']}`.",
            "",
        ])
    source = doc["source_batch"]
    return "\n".join([
        "# GOLD-001 — batch 006 preregistration inputs",
        "",
        f"**Recorded {doc['recorded_at']}. {doc['status']}.**",
        "",
        ("Four things batch 005 established about the generator. They are recorded "
         "here rather than fixed in place: batch 005's generation artifact is a "
         "historical record, and a miner corrected retroactively would leave no "
         "evidence of what it got wrong. Each one is a check a future batch-006 "
         "preregistration has to carry, with the case that would verify it."),
        "",
        *rows,
        "## Provenance",
        "",
        "| | |",
        "| --- | --- |",
        f"| source batch | {source['batch']:03d} |",
        f"| closure sha256 | `{source['closure_sha256']}` |",
        f"| reviewed-state sha256 | `{source['reviewed_state_sha256']}` |",
        f"| generation batch sha256 | `{source['generation_batch_sha256']}` |",
        "",
        "## Not done",
        "",
        *[f"- {item}" for item in doc["not_done"]],
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="experiments/GOLD-001")
    args = parser.parse_args()

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    doc = build(now)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "GOLD-001-batch-006-preregistration-inputs.json").write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "GOLD-001-batch-006-preregistration-inputs.md").write_text(
        render(doc), encoding="utf-8")
    print(f"recorded {len(doc['inputs'])} preregistration inputs: "
          + ", ".join(e["id"] for e in doc["inputs"]))
    print(f"wrote {out}/GOLD-001-batch-006-preregistration-inputs.md")
    print(f"wrote {out}/GOLD-001-batch-006-preregistration-inputs.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
