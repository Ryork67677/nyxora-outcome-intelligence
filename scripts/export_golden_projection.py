#!/usr/bin/env python3
"""GOLD-001: project the human-approved candidates into the golden-case schema.

A review batch and a golden set are different shapes. The batch carries a candidate:
proposals, verdicts, revisions, decisions. The golden set carries a case: a question, an
anchored span, and claims the validator can check. This writes the second from the first
so ``validate_golden.py`` can be run for real rather than approximated.

The projection is **not** a split. It asserts a placeholder ``split`` because the
validator requires one; assigning cases to validation or holdout is a separate decision
and is not made here.

One gap is reported rather than hidden. The golden convention is that a *critical* claim
is a literal string that must appear inside its own evidence span, and the validator only
checks claims marked critical. Candidates authored before that convention carry
sentence-form claims instead, so they are emitted as non-critical and are **not** claim-
checked. The script prints how many cases that applies to; treating a pass over them as
proof of claim support would be wrong.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

#: Only approved cases are projected. Nothing else is a candidate for a golden set.
PROJECTED_STATUS = "human_verified"
PLACEHOLDER_SPLIT = "validation"


def project(record: dict, split: str, batch: int = 1) -> dict:
    critical = record.get("critical_strings")
    spans = record.get("expected_evidence")
    claims = ([{"text": s, "critical": True} for s in critical] if critical
              else [{"text": c, "critical": False}
                    for c in record.get("proposed_atomic_claims", [])])
    return {
        "case_id": record["candidate_id"],
        "question": record["proposed_question"],
        "answer": record["proposed_answer"],
        # reasoning_type is authoritative once a review has set it; proposed_category
        # is the miner's pre-review guess.
        "category": (record.get("reasoning_type")
                     or record.get("proposed_category") or "exact_lookup"),
        "evidence_shape": record.get("evidence_shape"),
        "requires_all_evidence": record.get("requires_all_evidence"),
        "split": split,
        "split_is_placeholder": True,
        "provider": record["provider"],
        "verification": record["verification_status"],
        "human_verified": record.get("human_verified", False),
        "expected_abstain": False,
        # A multi-span case has no single anchor hash. The per-span hashes below are
        # the real check; the top-level one is a convenience the validator falls back
        # to, and inventing one for a multi-span case would give the fallback something
        # false to agree with.
        "evidence_text_sha256": (record.get("evidence_hash") if not spans
                                 else spans[0]["evidence_hash"] if len(spans) == 1
                                 else None),
        "expected_claims": claims,
        "claims_are_critical": bool(critical),
        # Every span, not just the first. A multi-span case projected as one span
        # silently drops the evidence its second claim rests on.
        "expected_evidence": [
            {"version_id": s["version_id"], "char_start": s["char_start"],
             "char_end": s["char_end"], "section_path": s["section_path"],
             "evidence_text_sha256": s.get("evidence_hash")}
            for s in (record.get("expected_evidence") or [{
                "version_id": record["version_id"],
                "char_start": record["char_start"],
                "char_end": record["char_end"],
                "section_path": record["section_path"],
                "evidence_hash": record["evidence_hash"]}])],
        "source_document_title": record["document_title"],
        "source_url": record["source_url"],
        "source_captured_at": str(record["captured_at"]),
        "provenance": {
            "batch": batch,
            "generator": "claude",
            "independent_reviewer": record.get("verification", {}).get("reviewer"),
            "independent_verdict": record.get("verification", {}).get("verdict"),
            "human_reviewer": record.get("human_reviewer"),
            "human_reviewed_at": record.get("human_reviewed_at"),
            "revisions": len(record.get("revisions", [])),
            "anchor_revisions": len(record.get("anchor_revisions", [])),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch")
    parser.add_argument("--out", default="evals/review/batch_001_approved_projection.jsonl")
    parser.add_argument("--split", default=PLACEHOLDER_SPLIT)
    parser.add_argument("--include", default=None,
                        help="comma-separated candidate ids to project regardless of status")
    args = parser.parse_args()

    batch = json.loads(Path(args.batch).read_text())
    extra = {c for c in (args.include or "").split(",") if c}
    number = batch.get("batch", 1)
    cases = [project(r, args.split, number) for r in batch["records"]
             if r.get("verification_status") == PROJECTED_STATUS
             or r["candidate_id"] in extra]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases),
                   encoding="utf-8")

    unchecked = [c["case_id"] for c in cases if not c["claims_are_critical"]]
    print(f"wrote {out} ({len(cases)} cases, split placeholder {args.split!r})")
    print(f"  claim-checked (critical strings authored): {len(cases) - len(unchecked)}")
    if unchecked:
        print(f"  NOT claim-checked ({len(unchecked)}): {', '.join(unchecked)}")
        print("  these carry sentence-form claims; a validator pass over them says "
              "nothing about claim support")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
