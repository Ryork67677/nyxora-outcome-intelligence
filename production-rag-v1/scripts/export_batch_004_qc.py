#!/usr/bin/env python3
"""GOLD-001: build the batch-004 owner QC packet.

Composes the generation artifact with the internal review's repairs and renders one
decision sheet per candidate: the final question, answer, claims, exact evidence and
critical strings, what the review found, what it repaired, and what the precheck says.

The packet exists so a person can decide. It therefore does not decide: the decisions
file it writes carries ``decision: null`` for every candidate, and a repaired candidate
also carries ``approves_evidence_hash: null``, so accepting a repair means quoting the
hash of the evidence being accepted rather than trusting that a repair happened.

Three separate states are kept apart throughout, because collapsing them is the failure
this whole pipeline is built to prevent:

* ``precheck_holdout_ready`` — structurally capable. A script decides this.
* ``human_verified`` — the project owner approved it. Only a person decides this.
* ``holdout_eligible`` — verified, plus deterministic claim support, valid evidence and
  no unresolved blocker.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

BATCH = Path("evals/review/gold_review_batch_004.json")
REPAIRS = Path("evals/review/gold_review_batch_004_repairs.json")
OPTIONS = ("APPROVE", "REJECT", "NEEDS_EDIT")


def compose(batch: dict, repairs: dict) -> list[dict]:
    """The record as it now stands: generated, then repaired where the review said so."""
    repaired = {r["candidate_id"]: r for r in repairs["records"]}
    out = []
    for record in batch["records"]:
        candidate_id = record["candidate_id"]
        final = repaired.get(candidate_id, record)
        review = repairs["review"][candidate_id]
        out.append({
            "record": final,
            "generated": record,
            "review": review,
            "was_repaired": candidate_id in repaired,
        })
    return out


def code_span(text: str) -> str:
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def render(packet: dict) -> str:
    entries = packet["candidates"]
    counts = packet["internal_review_status_counts"]
    lines = [
        "# GOLD-001 — batch 004 owner QC packet",
        "",
        (f"**{len(entries)} candidates · corpus snapshot "
         f"`{packet['corpus_snapshot']}` · prepared {packet['prepared_at']}**"),
        "",
        ("Nothing in this packet is gold and nothing is verified. Every candidate is "
         "`candidate_unverified`, and no script in this repository can change that: "
         "`human_verified` exists only where the project owner records an approval."),
        "",
        "## What the three states mean",
        "",
        "| state | who decides | what it means |",
        "| --- | --- | --- |",
        ("| `precheck_holdout_ready` | a script | the record is structurally capable — "
         "hashes match, critical strings are inside their own spans, no critical "
         "anaphora, no oversized anchor |"),
        ("| `human_verified` | the project owner | a person read the evidence and "
         "approved the case |"),
        ("| `holdout_eligible` | derived | `human_verified` **and** deterministic claim "
         "support **and** valid evidence **and** no unresolved blocker |"),
        "",
        ("15 of 15 candidates are `precheck_holdout_ready`. That is not an argument for "
         "approving them: the internal review below recommends one for rejection and "
         "repaired ten, and every one of those was precheck-ready before the review "
         "looked at it. A structural check cannot see that a question is broader than "
         "its evidence or that a rule applies only on one API surface."),
        "",
        "## Internal review outcome",
        "",
        "| status | candidates |",
        "| --- | --- |",
    ]
    for status, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {status} | {count} |")
    lines += [
        "",
        ("The review was done by the authoring model against the frozen evidence. It is "
         "an internal check, not a second opinion from an independent party, and it is "
         "certainly not verification. Where it repaired a candidate the original text "
         "and the original anchor are both preserved, so a disagreement is checkable."),
        "",
        "| id | provider | reasoning type | shape | internal status | repaired |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        record, review = entry["record"], entry["review"]
        lines.append(
            f"| `{record['candidate_id'][-2:]}` | {record['provider']} | "
            f"`{record['reasoning_type']}` | {record['evidence_shape']} | "
            f"{review['status']} | {'yes' if entry['was_repaired'] else 'no'} |")
    lines += ["", "---", ""]

    for entry in entries:
        record, review = entry["record"], entry["review"]
        generated = entry["generated"]
        spans = record["expected_evidence"]
        lines += [
            f"## {record['candidate_id']}",
            "",
            f"- **provider**: {record['provider']}",
            f"- **document**: {record['document_title']}",
            f"- **section**: {' › '.join(record['section_path'])}",
            (f"- **reasoning type**: `{record['reasoning_type']}`"
             + (f" (generated as `{generated['reasoning_type']}`)"
                if record["reasoning_type"] != generated["reasoning_type"] else "")),
            (f"- **evidence shape**: `{record['evidence_shape']}` · "
             f"**requires all evidence**: {record['requires_all_evidence']}"),
            f"- **internal review status**: **{review['status']}**",
            (f"- **precheck**: holdout-ready = {record['precheck_holdout_ready']}"
             + (f", failures: {record['precheck_failures']}"
                if record.get("precheck_failures") else "")),
            "",
            "### Final question",
            "",
            record["question"],
            "",
            "### Final answer",
            "",
            record["answer"],
            "",
            "### Final atomic claims",
            "",
        ]
        lines += [f"{i}. {c}" for i, c in enumerate(record["atomic_claims"], 1)]
        if record.get("composed_claim"):
            lines += ["", f"**Composed claim.** {record['composed_claim']}"]
        lines += ["", "### Exact evidence", ""]
        for span in spans:
            lines += [
                (f"**{span['evidence_id']}** · `{span['version_id']}` "
                 f"{span['char_start']}–{span['char_end']} "
                 f"({span['evidence_char_length']} chars) · "
                 f"{' › '.join(span['section_path'])}"),
                "", "```", span["evidence_text"], "```",
                ("**critical strings**: "
                 + ", ".join(code_span(s) for s in span["critical_strings"])),
                f"**evidence_hash**: `{span['evidence_hash']}`",
                "",
            ]
        lines += ["### Claim → evidence", ""]
        lines += [f"{i}. {m['claim'][:90]}{'…' if len(m['claim']) > 90 else ''} → "
                  f"`{m['evidence_id']}`"
                  for i, m in enumerate(record["claim_evidence_map"], 1)]
        lines += ["", "### Internal review", ""]
        if review["findings"]:
            lines += [f"- {f}" for f in review["findings"]]
        else:
            lines.append("- No finding. The candidate is as generated.")
        if entry["was_repaired"]:
            lines += ["", "### Repairs made", ""]
            for revision in record.get("anchor_revisions", []):
                if revision["action"] == "extend_boundary":
                    lines += [
                        f"- **{revision['evidence_id']} anchor extended** "
                        f"({revision['reason']})",
                        f"  - was {revision['old_char_start']}–"
                        f"{revision['old_char_end']}, hash "
                        f"`{revision['old_evidence_hash'][:16]}…`",
                        f"  - now {revision['new_char_start']}–"
                        f"{revision['new_char_end']}, hash "
                        f"`{revision['new_evidence_hash'][:16]}…`",
                    ]
                else:
                    lines += [
                        f"- **{revision['evidence_id']} scope span added** "
                        f"({revision['reason']})",
                        f"  - {revision['new_char_start']}–{revision['new_char_end']}, "
                        f"hash `{revision['new_evidence_hash'][:16]}…`",
                    ]
            for revision in record.get("revisions", []):
                before = revision["from"]
                after = revision["to"]
                lines += [
                    f"- **{revision['field']} rewritten** ({revision['reason']})",
                    f"  - was: {before if isinstance(before, str) else before}",
                    f"  - now: {after if isinstance(after, str) else after}",
                ]
        if record.get("precheck_flags"):
            lines += ["", "### Flags for your judgement", ""]
            lines += [f"- {flag}" for flag in record["precheck_flags"]]
        lines += [
            "",
            "### Your decision",
            "",
            "`APPROVE` · `REJECT` · `NEEDS_EDIT`",
            "",
        ]
        if entry["was_repaired"]:
            lines += [
                (f"This candidate was repaired. Approving it means approving the "
                 f"repaired evidence: record `approves_evidence_hash` = "
                 f"`{spans[0]['evidence_hash']}`"
                 + (" (and the other spans' hashes above)" if len(spans) > 1 else "")
                 + "."),
                "",
            ]
        if review["status"] == "REJECT_RECOMMENDED":
            lines += [
                ("The review recommends rejecting this candidate. That recommendation "
                 "is not a decision and does not bind you."),
                "",
            ]
        lines += ["---", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="evals/review")
    args = parser.parse_args()

    batch = json.loads(BATCH.read_text())
    repairs = json.loads(REPAIRS.read_text())
    if repairs["source_batch_sha256"] != batch["batch_sha256"]:
        raise SystemExit(
            "the repairs were computed against a different batch file — regenerate the "
            "review rather than composing records that never met")

    entries = compose(batch, repairs)
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    packet = {
        "batch": 4,
        "prepared_at": now,
        "corpus_snapshot": batch["corpus_snapshot"],
        "source_batch_sha256": batch["batch_sha256"],
        "repairs_file": str(REPAIRS),
        "candidates": entries,
        "internal_review_status_counts": dict(
            Counter(e["review"]["status"] for e in entries)),
        "repaired_candidates": sum(1 for e in entries if e["was_repaired"]),
        "precheck_holdout_ready": sum(
            1 for e in entries if e["record"]["precheck_holdout_ready"]),
        "human_verified": 0,
        "holdout_eligible": 0,
        "owner_options": list(OPTIONS),
        "note": ("A QC packet is a request for decisions, not a record of them. Nothing "
                 "here is verified, approved or eligible."),
        "retrieval_was_not_run": True,
        "systems_executed": [],
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "gold_batch_004_qc.json").write_text(
        json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "gold_batch_004_qc.md").write_text(render(packet), encoding="utf-8")

    decisions = {
        "batch": 4,
        "prepared_at": now,
        "source_batch_sha256": batch["batch_sha256"],
        "instructions": (
            "Record one decision per candidate. decision must be APPROVE, REJECT or "
            "NEEDS_EDIT — a null decision is an undecided candidate and the batch "
            "cannot close while one remains. For a repaired candidate, set "
            "approves_evidence_hash to the evidence_hash of each span you are "
            "approving; the importer refuses an approval that quotes the pre-repair "
            "hash, so a repair cannot be approved by someone who only saw the original."),
        "decided_by": None,
        "decisions": [
            {
                "candidate_id": entry["record"]["candidate_id"],
                "decision": None,
                "internal_review_status": entry["review"]["status"],
                "was_repaired": entry["was_repaired"],
                "approves_evidence_hash": (
                    [None] * len(entry["record"]["expected_evidence"])
                    if entry["was_repaired"] else None),
                "notes": None,
            }
            for entry in entries
        ],
    }
    (out_dir / "human_decisions_batch_004.json").write_text(
        json.dumps(decisions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"packet for {len(entries)} candidates: "
          f"{packet['internal_review_status_counts']}")
    print(f"  repaired: {packet['repaired_candidates']}  "
          f"precheck-ready: {packet['precheck_holdout_ready']}  "
          f"human_verified: {packet['human_verified']}")
    print(f"wrote {out_dir}/gold_batch_004_qc.md, .json and "
          "human_decisions_batch_004.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
