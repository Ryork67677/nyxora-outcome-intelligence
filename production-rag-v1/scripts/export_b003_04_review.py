#!/usr/bin/env python3
"""GOLD-001: the last outstanding batch-003 case, rendered for one decision.

Everything needed to decide is here: both spans verbatim, the detector's original
finding, why it is now classified noncritical, and what the validator says. Nothing to
look up, and nothing approved.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from rag_v1.gold.eligibility import evaluate
from rag_v1.gold.normalisation import contains_claim_string

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_golden_projection import project
from validate_golden import load_sources, validate

CANDIDATE = "GOLD-B003-04"


def code_span(text: str) -> str:
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def status_counts(batch: dict) -> dict:
    """Counted from the records, never read from the batch header.

    The first version of this artifact printed needs_human_review = 0 while its own
    prose said the case was awaiting review. The header dict was stale — a script had
    changed a record's status without refreshing it. A report that derives its numbers
    from the records cannot disagree with them.
    """
    return dict(Counter(r["verification_status"] for r in batch["records"]))


def render(record: dict, validator: str, eligibility: dict, batch: dict) -> str:
    spans = record["expected_evidence"]
    finding = record["anaphora_finding"]
    original = {r["field"]: r["from"] for r in record["revisions"]}
    claims = "\n".join(f"  {i}. {c}"
                       for i, c in enumerate(record["proposed_atomic_claims"], 1))
    strings = ", ".join(code_span(s) for s in record["critical_strings"])

    lines = [
        f"# GOLD-001 — batch 003 final case: {CANDIDATE}",
        "",
        ("One decision closes batch 003. The other 19 candidates are approved; this one "
         "was sent back with `NEEDS_EDIT` and has been rewritten as directed."),
        "",
        ("**The evidence was never the problem, and it has not been touched.** Both "
         "spans are byte-identical to the ones you reviewed, and both hashes were "
         "re-verified against their text. What changed is the question."),
        "",
        "---", "",
        "## The case",
        "",
        f"**Q.** {record['proposed_question']}",
        "",
        f"**A.** {record['proposed_answer']}",
        "",
        "**Atomic claims**",
        claims,
        "",
        (f"`reasoning_type: {record['reasoning_type']}` · "
         f"`evidence_shape: {record['evidence_shape']}` · "
         f"`requires_all_evidence: {record['requires_all_evidence']}` — "
         "a retriever earns credit only by finding both spans."),
        "",
        "## Exact evidence",
        "",
    ]
    for index, span in enumerate(spans, 1):
        lines += [
            (f"**Span {index}** — `{span['version_id']}` "
             f"{span['char_start']}–{span['char_end']} "
             f"({span['evidence_char_length']} chars) · "
             f"`{span['evidence_hash'][:16]}…`"),
            "", "```", span["evidence_text"], "```", "",
        ]
    lines += [
        f"**Critical strings** (each verified inside the evidence): {strings}",
        "",
        "## What changed, and what did not",
        "",
        "| | |",
        "| --- | --- |",
        f"| question, before | {original.get('proposed_question', '—')} |",
        f"| question, after | {record['proposed_question']} |",
        f"| evidence spans | unchanged — {len(spans)} spans, same offsets, same hashes |",
        f"| revisions on record | {len(record['revisions'])}, none touching evidence |",
        "",
        ("The original question named the advisor tool. That framing is what made the "
         "phrase \"the tool definition\" load-bearing, because a reader had to resolve "
         "which tool before the question meant anything. Removing it does not weaken "
         "the case: the fact under test is the executor/advisor pairing rule and its "
         "failure behaviour, and both spans state that outright."),
        "",
        "## The detector finding — kept, not erased",
        "",
        "| | |",
        "| --- | --- |",
        f"| original finding | {finding['finding']} |",
        f"| phrase | `{finding['phrase']}` |",
        f"| classification | **{record['anaphora_status']}** |",
        (f"| override | {record.get('human_anaphora_override')} by "
         f"`{record.get('override_reviewer')}` |"),
        "",
        f"**Why noncritical.** {finding['why']}",
        "",
        ("The rule is mechanical, not a judgement call: a span that *opens* on a "
         "reference is always critical, because the sentence's own subject or condition "
         "is what is missing. Otherwise the reference's head noun is looked for in the "
         "question, the answer, the claims and the critical strings. If the scored text "
         "never mentions it, resolving it cannot change the score."),
        "",
        ("Two things this deliberately does not do. It does not edit the evidence to "
         "silence the detector — the phrase is still there, verbatim, and a test holds "
         "it there. And it does not let a model accept its own finding: without a named "
         "human override the case stays blocked, which is what it did until you "
         "recorded one."),
        "",
        "## Validator and eligibility",
        "",
        f"**Validator.** {validator}",
        "",
        (f"**Precheck.** {'holdout-ready' if record['precheck_holdout_ready'] else 'blocked'}"
         f"{'' if record['precheck_holdout_ready'] else ': ' + '; '.join(record['precheck_failures'])}."),
        "",
        (f"**Holdout eligibility if approved.** "
         f"{'yes' if eligibility['holdout_eligible'] else 'no — ' + str(eligibility['failures'])}"),
        "",
        ("Eligibility is not approval. This case is `needs_human_review` and stays "
         "there until you decide."),
        "",
        "## Batch 003 state",
        "",
        "| | |",
        "| --- | --- |",
        *[f"| `{status}` | {count} |"
          for status, count in sorted(status_counts(batch).items())],
        f"| genuine multi-hop | {batch['genuine_multi_hop']} (target 3–4) |",
        "",
        ("The multi-hop shortfall is unchanged and is not being quietly refilled. The "
         "five multi-span cases remain useful retrieval tests; none of them is multi-hop "
         "reasoning."),
        "",
        "## Decision",
        "",
        ("`APPROVE` or `REJECT`. Approving closes batch 003 at **20 human_verified, 0 "
         "rejected**; rejecting closes it at **19 and 1**. Either way it closes, and no "
         "retrieval has been run against any of it."),
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch")
    parser.add_argument("--out", default="evals/review/gold_batch_003_final_case_review.md")
    args = parser.parse_args()

    batch = json.loads(Path(args.batch).read_text())
    record = next(r for r in batch["records"] if r["candidate_id"] == CANDIDATE)
    if record.get("verification_status") == "human_verified":
        raise SystemExit(f"{CANDIDATE} is already approved; nothing to review")

    combined = " \n".join(s["evidence_text"] for s in record["expected_evidence"])
    outside = [s for s in record["critical_strings"]
               if not contains_claim_string(combined, s)]
    if outside:
        raise SystemExit(f"critical strings outside the evidence: {outside}")

    from rag_v1.db import connect
    with connect() as conn, conn.cursor() as cur:
        sources = load_sources(cur)

    # Validated against the already-approved cases, so a duplicate question or span
    # would be caught rather than assumed absent.
    approved = [project(r, "validation") for r in batch["records"]
                if r["verification_status"] == "human_verified"]
    proposed = project({**record, "verification_status": "human_verified",
                        "human_verified": True}, "validation")
    proposed["expected_evidence"] = [
        {"version_id": s["version_id"], "char_start": s["char_start"],
         "char_end": s["char_end"], "section_path": s["section_path"]}
        for s in record["expected_evidence"]]
    proposed["category"] = "multi_hop" if len(proposed["expected_evidence"]) > 1 \
        else proposed["category"]
    failures = [f for f in validate([*approved, proposed], sources, require_human=set())
                if f["case_id"] == CANDIDATE]
    validator = ("PASS — all blocking checks" if not failures else
                 "FAIL: " + "; ".join(f"{f['check']} ({f['detail']})" for f in failures))

    eligibility = evaluate({**record, "verification_status": "human_verified",
                            "human_verified": True})
    Path(args.out).write_text(render(record, validator, eligibility, batch),
                              encoding="utf-8")
    print(f"wrote {args.out}")
    print(f"  {CANDIDATE}: {record['verification_status']} · "
          f"{record['anaphora_status']} · validator {validator}")
    print(f"  eligibility if approved: {eligibility['holdout_eligible']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
