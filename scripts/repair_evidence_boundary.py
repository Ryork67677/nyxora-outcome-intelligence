#!/usr/bin/env python3
"""GOLD-001: complete an evidence boundary without destroying the original anchor.

An anchor is normally immutable. ``import_verification.py`` refuses to let a reviewer
move one, because silently re-anchoring would break the hash that makes the evidence
checkable. This script is the one authorised exception, and it is deliberately narrow:

* it only touches candidates the project owner marked ``NEEDS_EDIT``;
* the new span must be a **strict superset** of the old one, so the anchor can only grow
  outward to include what the claim already depended on — a span that moves elsewhere is
  a re-anchoring, and is refused;
* both anchors are kept. The old offsets, text and hash are recorded in a numbered
  ``anchor_revisions`` entry, alongside the reason, and nothing is overwritten;
* the repaired candidate goes back to ``needs_human_review``. Repairing a case does not
  approve it, and this script cannot produce ``human_verified``.

It then projects each repaired candidate into the golden-case schema and runs the real
validator over it, so the packet reports what the gate says rather than what the repair
hoped.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.db import connect

# The golden validator is a sibling script, not an installed module. Reusing it is the
# point: the packet must report what the real gate says, not a second implementation.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_golden import load_sources, validate

#: Only a candidate the owner sent back may be repaired. Anything else is out of scope.
REPAIRABLE_DECISION = "NEEDS_EDIT"
#: A repair returns the case to review. It never approves it.
STATUS_AFTER_REPAIR = "needs_human_review"
CONTEXT_CHARS = 900


def locate(text: str, head: str, tail: str, old_start: int, old_end: int) -> tuple[int, int]:
    start = text.rfind(head, 0, old_end)
    if start == -1:
        raise SystemExit(f"could not locate head {head!r} before offset {old_end}")
    index = text.find(tail, start)
    if index == -1:
        raise SystemExit(f"could not locate tail {tail!r} after offset {start}")
    return start, index + len(tail)


def check_superset(text: str, new: tuple[int, int], old: tuple[int, int]) -> None:
    if not (new[0] <= old[0] and new[1] >= old[1]):
        raise SystemExit(
            f"refusing: new span {new} does not contain old span {old}. A boundary "
            "completion may only grow the anchor outward."
        )
    if text[old[0]:old[1]] not in text[new[0]:new[1]]:
        raise SystemExit("refusing: the original evidence text is not inside the new span")


def apply_repair(record: dict, repair: dict, text: str, now: str) -> dict:
    decision = record.get("human_decision")
    if decision != REPAIRABLE_DECISION:
        raise SystemExit(
            f"refusing to repair {record['candidate_id']}: its human decision is "
            f"{decision!r}, not {REPAIRABLE_DECISION}"
        )

    old = (record["char_start"], record["char_end"])
    new = locate(text, repair["locate_head"], repair["locate_tail"], *old)
    check_superset(text, new, old)

    new_text = text[new[0]:new[1]]
    new_hash = hashlib.sha256(new_text.encode("utf-8")).hexdigest()
    if hashlib.sha256(record["evidence_text"].encode("utf-8")).hexdigest() != \
            record["evidence_hash"]:
        raise SystemExit(f"{record['candidate_id']}: stored evidence hash is already stale")

    revision = {
        "revision": len(record.get("anchor_revisions", [])) + 1,
        "reason": "evidence_boundary_completion",
        "old_char_start": old[0], "old_char_end": old[1],
        "old_evidence_hash": record["evidence_hash"],
        "old_evidence_text": record["evidence_text"],
        "new_char_start": new[0], "new_char_end": new[1],
        "new_evidence_hash": new_hash,
        "new_evidence_text": new_text,
        "characters_added_before": old[0] - new[0],
        "characters_added_after": new[1] - old[1],
        "author": "claude",
        "directed_by": "project_owner",
        "timestamp": now,
    }
    record.setdefault("anchor_revisions", []).append(revision)

    for field, key in (("proposed_question", "question"),
                       ("proposed_answer", "answer"),
                       ("proposed_atomic_claims", "atomic_claims")):
        if repair[key] == record.get(field):
            continue
        record.setdefault("revisions", []).append({
            "revision": len(record.get("revisions", [])) + 1,
            "field": field, "from": record.get(field), "to": repair[key],
            "author": "claude", "directed_by": "project_owner", "timestamp": now,
            "reason": "evidence_boundary_completion",
        })
        record[field] = repair[key]

    record["char_start"], record["char_end"] = new
    record["evidence_text"] = new_text
    record["evidence_hash"] = new_hash
    record["context_before"] = text[max(0, new[0] - CONTEXT_CHARS):new[0]]
    record["context_after"] = text[new[1]:new[1] + CONTEXT_CHARS]
    record["critical_strings"] = repair["critical_strings"]
    record["verification_status"] = STATUS_AFTER_REPAIR
    record["human_verified"] = False
    record["repaired_at"] = now
    record["awaiting"] = "explicit owner approval of the repaired version"
    return revision


def load_development_cases() -> list[dict]:
    """The existing development set, so a repaired question cannot silently duplicate one.

    These cases predate the status vocabulary and are only here to occupy question and
    evidence keys; failures attributed to them are filtered out by the caller.
    """
    path = Path("evals/development/v1.jsonl")
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def golden_projection(record: dict) -> dict:
    """Express the repaired candidate in the schema the golden validator checks."""
    return {
        "case_id": record["candidate_id"],
        "question": record["proposed_question"],
        "category": record.get("proposed_category") or "exact_lookup",
        "split": "validation",
        "provider": record["provider"],
        "verification": record["verification_status"],
        # A repaired case is not approved, so the human gate is not asserted here; the
        # caller runs with require_human=set() and the packet says so explicitly.
        "human_verified": record.get("human_verified", False),
        "expected_abstain": False,
        "evidence_text_sha256": record["evidence_hash"],
        # Critical claims are literal strings that must appear inside the span — the
        # convention the development set and the validator already use. Only the
        # repaired cases were authored that way; the approved candidates carry
        # sentence-form claims and appear here as context, so their claims are marked
        # non-critical rather than being failed against a convention they predate.
        "expected_claims": [{"text": s, "critical": True}
                            for s in record["critical_strings"]]
        if record.get("critical_strings")
        else [{"text": c, "critical": False}
              for c in record.get("proposed_atomic_claims", [])],
        "expected_evidence": [{
            "version_id": record["version_id"], "char_start": record["char_start"],
            "char_end": record["char_end"], "section_path": record["section_path"],
        }],
        "source_document_title": record["document_title"],
        "source_url": record["source_url"],
        "source_captured_at": record["captured_at"],
    }


def render_markdown(packet: dict) -> str:
    lines = [
        f"# GOLD-001 — batch {packet['batch']:03d} evidence-boundary repair review",
        "",
        (f"{len(packet['repairs'])} candidates were sent back with `NEEDS_EDIT`. Their "
         "anchors have been extended so that each exact span now contains everything its "
         "claims depend on. Nothing here is approved."),
        "",
        ("Every one of these remains `needs_human_review` until you approve the repaired "
         "version. This script cannot produce `human_verified`, and did not."),
        "",
        ("**The original anchors were not overwritten.** Each repair is a numbered "
         "`anchor_revisions` entry carrying the old offsets, text and hash beside the new "
         "ones. The new span is a strict superset of the old in all three cases — the "
         "script refuses anything else, because a span that moves elsewhere is a "
         "re-anchoring, not a boundary completion."),
        "",
        (f"Validator: **{packet['validator']['result']}** "
         f"({packet['validator']['checks_run']} cases checked, "
         f"{len(packet['validator']['failures'])} failures)."),
        "",
        "---",
        "",
    ]
    for item in packet["repairs"]:
        anchor = item["anchor_revision"]
        claims = "\n".join(f"  {i}. {c}" for i, c in enumerate(item["atomic_claims"], 1))
        lines += [
            f"## {item['candidate_id']}",
            "",
            f"**Q.** {item['question']}",
            "",
            f"**A.** {item['answer']}",
            "",
            "**Atomic claims**",
            claims,
            "",
            (f"**Repaired exact evidence** — `{item['version_id']}` "
             f"{anchor['new_char_start']}–{anchor['new_char_end']} "
             f"({anchor['new_char_end'] - anchor['new_char_start']} chars) · "
             f"`{anchor['new_evidence_hash'][:16]}…`"),
            "",
            "```",
            anchor["new_evidence_text"],
            "```",
            "",
            (f"**Old evidence** — {anchor['old_char_start']}–{anchor['old_char_end']} "
             f"({anchor['old_char_end'] - anchor['old_char_start']} chars) · "
             f"`{anchor['old_evidence_hash'][:16]}…`"),
            "",
            "```",
            anchor["old_evidence_text"],
            "```",
            "",
            (f"**What changed.** {item['what_changed']} "
             f"({anchor['characters_added_before']} characters added before the old "
             f"span, {anchor['characters_added_after']} after.) The old span is "
             "contained in the new one verbatim."),
            "",
            f"**Why the new anchor is complete.** {item['why_complete']}",
            "",
            f"**Validator result.** {item['validator']}",
            "",
            "**Decision needed:** `APPROVE` or `REJECT` the repaired version.",
            "",
            "---",
            "",
        ]
    lines += [
        "## What happens next",
        "",
        ("Record a decision for these three in a decisions file and import it with "
         "`scripts/import_human_decisions.py`. Until then batch 001 stands at 12 "
         "`human_verified`, 2 `human_rejected`, 3 `needs_human_review`, and is not "
         "closed."),
        "",
        ("`GOLD-B001-01` is not in this packet and never reached a human: it was the "
         "second agreed pass, and the deterministic QC sample drew `02`. It remains "
         "`dual_llm_pass`, which is not gold."),
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch")
    parser.add_argument("spec")
    parser.add_argument("--out-dir", default="evals/review")
    args = parser.parse_args()

    batch_path = Path(args.batch)
    batch = json.loads(batch_path.read_text())
    spec = json.loads(Path(args.spec).read_text())
    records = {r["candidate_id"]: r for r in batch["records"]}

    unknown = [r["candidate_id"] for r in spec["repairs"] if r["candidate_id"] not in records]
    if unknown:
        raise SystemExit(f"spec names candidates not in the batch: {unknown}")

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    with connect() as conn, conn.cursor() as cur:
        sources = load_sources(cur)

        repairs = []
        for repair in spec["repairs"]:
            record = records[repair["candidate_id"]]
            source = sources.get(record["version_id"])
            if source is None:
                raise SystemExit(f"{record['candidate_id']}: version not in the snapshot")
            revision = apply_repair(record, repair, source["text"], now)
            repairs.append({
                "candidate_id": record["candidate_id"],
                "version_id": record["version_id"],
                "section_path": record["section_path"],
                "question": record["proposed_question"],
                "answer": record["proposed_answer"],
                "atomic_claims": record["proposed_atomic_claims"],
                "critical_strings": record["critical_strings"],
                "anchor_revision": revision,
                "what_changed": repair["what_changed"],
                "why_complete": repair["why_complete"],
                "verification_status": record["verification_status"],
            })

    # Duplicate-question and duplicate-evidence are only meaningful against everything
    # else that already exists, so the repaired cases are validated at the end of a list
    # that also holds the approved candidates and the development set. A duplicate is
    # attributed to the later case, which is why the repaired three come last.
    repaired_ids = {r["candidate_id"] for r in repairs}
    context_cases = [c for c in load_development_cases() if c]
    context_cases += [golden_projection(r) for r in batch["records"]
                      if r["candidate_id"] not in repaired_ids
                      and r.get("verification_status") == "human_verified"]
    projections = [golden_projection(records[r["candidate_id"]]) for r in repairs]
    all_failures = validate(context_cases + projections, sources, require_human=set())
    failures = [f for f in all_failures if f["case_id"] in repaired_ids]
    by_case: dict[str, list[dict]] = {}
    for failure in failures:
        by_case.setdefault(failure["case_id"], []).append(failure)
    for item in repairs:
        problems = by_case.get(item["candidate_id"], [])
        item["validator"] = "PASS — all checks" if not problems else "FAIL: " + "; ".join(
            f"{p['check']} ({p['detail']})" for p in problems)

    packet = {
        "batch": batch.get("batch"),
        "generated_at": now,
        "source_batch_sha256": batch.get("batch_sha256"),
        "nothing_here_is_approved": (
            "Repaired candidates are needs_human_review. Only an explicit owner APPROVE "
            "imported by scripts/import_human_decisions.py can make one human_verified."
        ),
        "validator": {
            "result": "PASS" if not failures else "FAIL",
            "checks_run": len(projections),
            "failures": failures,
            "note": ("Run with the same validate() the golden sets use, over the "
                     "repaired cases plus the 12 approved candidates and the "
                     "development set, so duplicate question and duplicate evidence are "
                     "checked against everything that already exists. Failures "
                     "belonging to the context cases are filtered out."),
            "context_cases": len(context_cases),
        },
        "repairs": repairs,
    }

    out_dir = Path(args.out_dir)
    (out_dir / "gold_batch_001_repair_review.json").write_text(
        json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "gold_batch_001_repair_review.md").write_text(
        render_markdown(packet), encoding="utf-8")
    batch["boundary_repairs_applied_at"] = now
    batch_path.write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")

    print(f"repaired {len(repairs)} candidates; validator {packet['validator']['result']}")
    for item in repairs:
        anchor = item["anchor_revision"]
        print(f"  {item['candidate_id']}: "
              f"{anchor['old_char_start']}–{anchor['old_char_end']} -> "
              f"{anchor['new_char_start']}–{anchor['new_char_end']}  {item['validator']}")
    for failure in failures:
        print("   FAILURE", failure)
    print(f"wrote {out_dir}/gold_batch_001_repair_review.md")
    print(f"wrote {out_dir}/gold_batch_001_repair_review.json")
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
