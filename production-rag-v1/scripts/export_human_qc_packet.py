#!/usr/bin/env python3
"""GOLD-001: render the human QC queue as something a person can actually review.

``select_human_qc.py`` decides *who* gets looked at; it emits candidate ids. This
renders those candidates with the source span, the surrounding context, and both
models' proposals side by side, so the reviewer judges the evidence rather than
trusting either model's summary of it.

The packet is deliberately read-only. Approval is recorded by editing the decision
file this writes alongside it, which keeps the human decision an explicit,
diffable act rather than a checkbox nobody can audit later.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DECISION_TEMPLATE = {
    "decision": "PENDING",
    "final_question": None,
    "final_answer": None,
    "final_atomic_claims": None,
    "reviewer_notes": "",
}
#: Only a person writes these. The importer can never produce them.
VALID_DECISIONS = ("APPROVE", "REJECT", "PENDING")


def revision_for(record: dict, field: str) -> dict | None:
    for revision in reversed(record.get("revisions", [])):
        if revision["field"] == field:
            return revision
    return None


def render(record: dict, reason: str) -> str:
    verification = record.get("verification", {})
    failed = [
        key for key, value in verification.items()
        if isinstance(value, bool) and value is False
    ]
    lines = [
        (f"### {record['candidate_id']} — "
         f"{verification.get('verdict', 'UNREVIEWED')} ({reason})"),
        "",
        f"- **status**: `{record['verification_status']}`",
        f"- **source**: {record['document_title']} — {' > '.join(record['section_path'])}",
        (f"- **anchor**: `{record['version_id']}` chars "
         f"{record['char_start']}–{record['char_end']}"),
        (f"- **evidence kind**: `{record['evidence_kind']}`, generator confidence "
         f"`{record['generator_confidence']}`"),
        f"- **checks that failed**: {', '.join(f'`{f}`' for f in failed) or 'none'}",
        "",
        "**Context before**",
        "",
        "```",
        record["context_before"].strip() or "(start of document)",
        "```",
        "",
        "**ANCHORED EVIDENCE — this is what the case is allowed to rest on**",
        "",
        "```",
        record["evidence_text"],
        "```",
        "",
        "**Context after**",
        "",
        "```",
        record["context_after"].strip() or "(end of document)",
        "```",
        "",
        "**Proposals**",
        "",
    ]

    for field, label in (("proposed_question", "Question"),
                         ("proposed_answer", "Answer"),
                         ("proposed_atomic_claims", "Atomic claims")):
        revision = revision_for(record, field)
        current = record.get(field)
        current_text = json.dumps(current, ensure_ascii=False) if isinstance(
            current, list) else str(current)
        if revision is None:
            lines.append(f"- **{label}** (generator, unchanged): {current_text}")
            continue
        original = revision["from"]
        original_text = json.dumps(original, ensure_ascii=False) if isinstance(
            original, list) else str(original)
        lines.append(f"- **{label}**")
        lines.append(f"  - generator: {original_text}")
        lines.append(f"  - reviewer ({revision['author']}): {current_text}")

    notes = verification.get("verification_notes", "").strip()
    if notes:
        lines += ["", f"**Reviewer notes**: {notes}"]
    if record.get("anchor_disputes"):
        lines += ["", "**Anchor disputes (reviewer's change was NOT applied)**", ""]
        lines += [f"- `{d['field']}`: proposed {d['reviewer_value']!r}, kept "
                  f"{d['kept_value']!r}" for d in record["anchor_disputes"]]

    lines += ["",
              ("**Decision**: record `APPROVE` or `REJECT` for "
               f"`{record['candidate_id']}` in the decisions file. Approving means "
               "you checked the anchored evidence yourself and it supports the final "
               "question, answer and every claim without needing the context blocks."),
              "", "---", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch")
    parser.add_argument("queue")
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    batch_path = Path(args.batch)
    batch = json.loads(batch_path.read_text())
    queue = json.loads(Path(args.queue).read_text())
    records = {r["candidate_id"]: r for r in batch["records"]}

    reasons: dict[str, str] = {}
    for candidate_id in queue["must_review"]:
        reasons[candidate_id] = "mandatory: disagreement, uncertainty or failure"
    for candidate_id in queue["qc_sample_of_dual_llm_pass"]:
        reasons[candidate_id] = "QC sample of agreed passes"

    missing = sorted(set(reasons) - set(records))
    if missing:
        raise SystemExit(f"queue references candidates not in the batch: {missing}")

    number = batch.get("batch", 0)
    out_dir = Path(args.out_dir) if args.out_dir else batch_path.parent
    ordered = sorted(reasons)

    body = [
        f"# GOLD-001 — human review packet, batch {number:03d}",
        "",
        (f"{len(ordered)} of {len(records)} candidates need a person: "
         f"{len(queue['must_review'])} mandatory "
         f"(ChatGPT disagreed, failed or was uncertain), plus "
         f"{len(queue['qc_sample_of_dual_llm_pass'])} drawn as a "
         f"{queue['sample_rate']:.0%} sample of the "
         f"{queue['dual_llm_pass_total']} cases both models passed (seed "
         f"{queue['seed']})."),
        "",
        ("Nothing in this packet is gold. A candidate becomes `human_verified` "
         "only when you record an `APPROVE` decision for it; no script can set that "
         "status."),
        "",
        ("Judge each case against the **anchored evidence** block alone. The "
         "context blocks are there to let you spot a bad anchor, not to answer the "
         "question — if you need them to answer it, the anchor is wrong and the case "
         "should be rejected or re-anchored."),
        "",
        "---",
        "",
    ]
    body += [render(records[cid], reasons[cid]) for cid in ordered]

    packet = out_dir / f"human_review_packet_batch_{number:03d}.md"
    packet.write_text("\n".join(body), encoding="utf-8")

    decisions_path = out_dir / f"human_decisions_batch_{number:03d}.json"
    if decisions_path.exists():
        print(f"kept existing {decisions_path} (decisions are never overwritten)")
    else:
        decisions_path.write_text(json.dumps({
            "batch": number,
            "source_batch_sha256": batch.get("batch_sha256"),
            "reviewer": None,
            "reviewed_at": None,
            "valid_decisions": list(VALID_DECISIONS),
            "decisions": {cid: dict(DECISION_TEMPLATE) for cid in ordered},
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {decisions_path}")

    print(f"wrote {packet} ({len(ordered)} candidates)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
