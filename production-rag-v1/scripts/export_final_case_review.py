#!/usr/bin/env python3
"""GOLD-001: render the one candidate that never reached a human.

``GOLD-B001-01`` passed independent verification without a rewrite, but the deterministic
QC sample drew its sibling, so no person has ever looked at it. It is ``dual_llm_pass``,
which is not gold, and it is the only thing keeping batch 001 open.

The packet is built so the decision needs no research: the exact span, the surrounding
table it sits in, the full provenance, the reviewer's verdict and reasoning, and a real
validator result on the case as it would enter a golden set.

Critical strings are **proposed** here, not stored. The candidate is not approved, so
nothing is written back to the batch; approving it is what makes them real.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rag_v1.db import connect

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_golden_projection import project
from validate_golden import load_sources, validate

CONTEXT_CHARS = 700


def code(text: str) -> str:
    """Markdown code span that survives a string containing backticks."""
    if "`" not in text:
        return f"`{text}`"
    return f"`` {text} ``"
#: Proposed literal claim strings. Each must appear inside the span, which the validator
#: is what actually confirms.
PROPOSED_CRITICAL = {
    "GOLD-B001-01": ["enable_zoom", "Default: `false`"],
}


def render(record: dict, context: dict, verdict_checks: list[str], validator: str,
           critical: list[str]) -> str:
    verification = record["verification"]
    claims = "\n".join(f"  {i}. {c}"
                       for i, c in enumerate(record["proposed_atomic_claims"], 1))
    checks = "\n".join(f"| `{name}` | {'yes' if value else 'NO'} |"
                       for name, value in verdict_checks)
    return "\n".join([
        f"# GOLD-001 — batch 001 final case: {record['candidate_id']}",
        "",
        ("One decision closes batch 001. This candidate passed independent verification "
         "without a single rewrite, but the deterministic QC sample drew its sibling "
         "`GOLD-B001-02` instead, so no person has ever looked at it. It is "
         f"`{record['verification_status']}` — two models agreeing, which is not gold."),
        "",
        "Everything needed to decide is below. Nothing to look up.",
        "",
        "---",
        "",
        "## The case",
        "",
        f"**Q.** {record['proposed_question']}",
        "",
        f"**A.** {record['proposed_answer']}",
        "",
        "**Atomic claim**",
        claims,
        "",
        "## Exact evidence",
        "",
        (f"`{record['version_id']}` chars {record['char_start']}–{record['char_end']} "
         f"({record['char_end'] - record['char_start']} chars) · "
         f"`{record['evidence_hash'][:16]}…`"),
        "",
        "```",
        record["evidence_text"],
        "```",
        "",
        ("The row binds structurally, not by proximity: the parameter is the row's first "
         "cell and the default is stated in that same row. That is the mechanism the "
         "table miner was built on, and it is the one mechanism in batch 001 that "
         "produced candidates needing no re-authoring."),
        "",
        "<details><summary>the table this row sits in</summary>",
        "",
        "```",
        f"…{context['before'].strip()}",
        "  ⟦THE ANCHORED ROW⟧",
        f"{context['after'].strip()}…",
        "```",
        "",
        "</details>",
        "",
        "## Source",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| document | {record['document_title']} |",
        f"| section | {' > '.join(record['section_path'])} |",
        f"| provider | {record['provider']} |",
        f"| url | {record['source_url']} |",
        f"| captured | {record['captured_at']} |",
        f"| version | `{record['version_id']}` |",
        f"| evidence kind | `{record['evidence_kind']}` |",
        f"| generator confidence | `{record['generator_confidence']}` |",
        "",
        "## Independent review",
        "",
        (f"**Verdict: {verification['verdict']}** "
         f"(reviewer `{verification['reviewer']}`, {verification['reviewed_at']})"),
        "",
        "| check | passed |",
        "| --- | --- |",
        checks,
        "",
        f"> {verification['verification_notes']}",
        "",
        ("The generator proposed this question and answer directly — there are "
         f"{len(record.get('revisions', []))} revisions on this candidate, because the "
         "reviewer changed nothing."),
        "",
        "## Validator",
        "",
        f"**{validator}**",
        "",
        ("Run through the same `validate_golden.py` the golden sets use, on this case "
         "projected into the golden-case schema, alongside the 15 already-approved "
         "cases so duplicate question and duplicate evidence are checked against them."),
        "",
        ("Critical claim strings proposed for this case: "
         + ", ".join(code(s) for s in critical) + ". These are the literal strings the "
         "validator requires to appear inside the span; they are proposed, not stored, "
         "and become real only on approval."),
        "",
        "## Decision",
        "",
        ("`APPROVE` or `REJECT`. Approving closes batch 001 at **16 human_verified, "
         "2 human_rejected**; rejecting closes it at **15 and 3**. Either way it closes."),
        "",
        ("Record it in a decisions file and import with "
         "`scripts/import_human_decisions.py`. Nothing else in batch 001 is outstanding."),
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch")
    parser.add_argument("--candidate", default="GOLD-B001-01")
    parser.add_argument("--out", default="evals/review/gold_batch_001_final_case_review.md")
    args = parser.parse_args()

    batch = json.loads(Path(args.batch).read_text())
    records = {r["candidate_id"]: r for r in batch["records"]}
    record = records.get(args.candidate)
    if record is None:
        raise SystemExit(f"{args.candidate} is not in this batch")
    if record.get("human_decision") is not None:
        raise SystemExit(f"{args.candidate} already has a human decision; nothing to review")

    critical = PROPOSED_CRITICAL[args.candidate]
    proposed = dict(record, critical_strings=critical,
                    verification_status="human_verified", human_verified=True)

    with connect() as conn, conn.cursor() as cur:
        sources = load_sources(cur)
    text = sources[record["version_id"]]["text"]
    context = {
        "before": text[max(0, record["char_start"] - CONTEXT_CHARS):record["char_start"]],
        "after": text[record["char_end"]:record["char_end"] + CONTEXT_CHARS],
    }

    # The already-approved cases go first so a duplicate is attributed to this candidate.
    approved = [project(r, "validation") for r in batch["records"]
                if r.get("verification_status") == "human_verified"]
    case = project(proposed, "validation")
    failures = [f for f in validate([*approved, case], sources, require_human=set())
                if f["case_id"] == args.candidate]
    validator = ("PASS — all blocking checks" if not failures else
                 "FAIL: " + "; ".join(f"{f['check']} ({f['detail']})" for f in failures))

    checks = [(k, v) for k, v in record["verification"].items() if isinstance(v, bool)]
    Path(args.out).write_text(
        render(record, context, checks, validator, critical), encoding="utf-8")

    print(f"wrote {args.out}")
    print(f"  {args.candidate}: {record['verification_status']}, validator {validator}")
    print(f"  checked against {len(approved)} approved cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
