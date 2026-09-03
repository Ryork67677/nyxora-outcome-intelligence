#!/usr/bin/env python3
"""GOLD-001: rewrite GOLD-B003-04 so its incidental reference stops being load-bearing.

The evidence was never the problem. Two spans state the fact the benchmark wants: that
the executor and advisor models must form a valid pair, and that an invalid pair returns
a 400. What blocked the case was the phrase "the tool definition" sitting inside span 1,
which the anaphora detector reads as an unresolved reference — correctly, in the sense
that the span does not say which tool.

The owner's instruction is the right shape of fix: drop the advisor-tool framing from the
question so nothing being scored depends on resolving that phrase. The evidence is not
touched. Silencing a detector by editing the source it inspects would be the one move
that makes every future finding worthless.

The finding is not deleted either. It is classified NONCRITICAL against the rewritten
question, and it stays blocking until a named human records an override.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.gold.anaphora import CRITICAL, evaluate_span
from rag_v1.gold.normalisation import contains_claim_string

CANDIDATE = "GOLD-B003-04"
REWRITE = {
    "proposed_question": ("What happens when the executor model and advisor model do "
                          "not form a valid pair?"),
    "proposed_answer": ("The API returns a `400 invalid_request_error` naming the "
                        "unsupported combination."),
    "proposed_atomic_claims": [
        "The executor model and advisor model must form a valid pair.",
        ("Requesting an invalid pair returns a `400 invalid_request_error` naming "
         "the unsupported combination."),
    ],
    "critical_strings": [
        "executor model", "advisor model", "must form a valid pair",
        "invalid pair", "400 invalid_request_error",
        "naming the unsupported combination",
    ],
    "reasoning_type": "error_behavior",
    "evidence_shape": "multi_span",
    "requires_all_evidence": True,
}
REASON = (
    "The advisor-tool framing was removed from the question. Nothing scored — question, "
    "answer, claims or critical strings — now depends on resolving \"the tool "
    "definition\", so the detector's finding becomes noncritical. The evidence spans, "
    "their offsets and their hashes are unchanged."
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch")
    parser.add_argument("--reviewer", default="project_owner")
    parser.add_argument("--override", action="store_true",
                        help="record the owner's noncritical-anaphora override")
    args = parser.parse_args()

    batch_path = Path(args.batch)
    batch = json.loads(batch_path.read_text())
    record = next(r for r in batch["records"] if r["candidate_id"] == CANDIDATE)

    if record.get("human_decision") != "NEEDS_EDIT":
        raise SystemExit(
            f"refusing: {CANDIDATE}'s decision is {record.get('human_decision')!r}, not "
            "NEEDS_EDIT")

    before = [
        {"char_start": s["char_start"], "char_end": s["char_end"],
         "evidence_hash": s["evidence_hash"], "evidence_text": s["evidence_text"]}
        for s in record["expected_evidence"]
    ]
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    for field, value in REWRITE.items():
        if record.get(field) == value:
            continue
        record.setdefault("revisions", []).append({
            "revision": len(record.get("revisions", [])) + 1,
            "field": field, "from": record.get(field), "to": value,
            "author": "claude", "directed_by": args.reviewer, "timestamp": now,
            "reason": "QUESTION_SCOPE: remove framing the evidence cannot resolve",
        })
        record[field] = value

    # The evidence must be byte-identical to what was reviewed. This is the check that
    # makes "we did not edit the source to silence the detector" a fact rather than a
    # promise.
    after = [{"char_start": s["char_start"], "char_end": s["char_end"],
              "evidence_hash": s["evidence_hash"], "evidence_text": s["evidence_text"]}
             for s in record["expected_evidence"]]
    if before != after:
        raise SystemExit("refusing: the evidence changed during a wording-only rewrite")
    for span in record["expected_evidence"]:
        if hashlib.sha256(
                span["evidence_text"].encode("utf-8")).hexdigest() != span["evidence_hash"]:
            raise SystemExit("refusing: an evidence hash no longer matches its text")

    combined = " \n".join(s["evidence_text"] for s in record["expected_evidence"])
    outside = [s for s in record["critical_strings"]
               if not contains_claim_string(combined, s)]
    if outside:
        raise SystemExit(f"refusing: critical strings outside the evidence: {outside}")

    if args.override:
        record["human_anaphora_override"] = True
        record["override_reviewer"] = args.reviewer
        record["override_recorded_at"] = now

    verdicts = [evaluate_span(s["evidence_text"], record)
                for s in record["expected_evidence"]]
    finding = next((v for v in verdicts if v["finding"]), verdicts[0])
    record["anaphora_status"] = finding["status"]
    record["anaphora_finding"] = finding
    record["precheck_failures"] = [
        f"{v['status']}: {v['finding']}" for v in verdicts if v["blocking"]]
    record["precheck_holdout_ready"] = not record["precheck_failures"]
    record["verification_status"] = "needs_human_review"
    record["human_verified"] = False
    record["awaiting"] = "explicit owner approval of the rewritten version"
    record["rewrite_reason"] = REASON

    batch["records"] = [r if r["candidate_id"] != CANDIDATE else record
                        for r in batch["records"]]
    # Refresh the header aggregate. A stale count beside a changed record is the same
    # defect class as the report contradictions this batch already had to correct.
    batch["precheck_holdout_ready"] = sum(1 for r in batch["records"]
                                          if r["precheck_holdout_ready"])
    # And the status counts. Moving a record from needs_edit to needs_human_review
    # without refreshing these left the batch header claiming a status nothing had.
    batch["status_counts"] = dict(Counter(r["verification_status"]
                                          for r in batch["records"]))
    batch_path.write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")

    print(f"rewrote {CANDIDATE}: {len(record['revisions'])} revisions total")
    print(f"  anaphora     : {record['anaphora_status']} ({finding['phrase']!r})")
    print(f"  why          : {finding['why']}")
    print(f"  override     : {record.get('human_anaphora_override', False)} "
          f"by {record.get('override_reviewer')}")
    print(f"  precheck     : "
          f"{'ready' if record['precheck_holdout_ready'] else record['precheck_failures']}")
    print(f"  status       : {record['verification_status']}")
    print("  evidence     : unchanged, both hashes re-verified against their text")
    if record["anaphora_status"] == CRITICAL:
        print("  NOTE: a critical anaphora cannot be overridden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
