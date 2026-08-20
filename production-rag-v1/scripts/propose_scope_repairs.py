#!/usr/bin/env python3
"""GOLD-001: propose — and only propose — scope repairs for closed cases.

Two batch-001 cases assert a scope their approved anchor does not contain. Both are
genuine defects rather than audit noise, and neither can be fixed by adding metadata, so
they are excluded from the v2 metadata overlay and handled here.

Nothing in this script writes to the closed batch or to the overlay. It computes each
proposed repair against the frozen source, runs the real validator over the result, and
writes a packet for the owner to accept or reject. Where a case has more than one honest
repair it shows both, because choosing between a larger anchor and a narrower claim is a
judgement about the benchmark, not a detail to settle quietly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.gold.eligibility import evaluate
from rag_v1.gold.normalisation import contains_claim_string

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_golden_projection import project
from repair_evidence_boundary import check_superset, locate
from validate_golden import load_sources, validate

PROPOSALS = {
    "GOLD-B001-13": [
        {
            "option": "A",
            "kind": "evidence_boundary_expansion",
            "recommended": True,
            "locate_head": "The API for accessing Claude on Google Cloud's Agent Platform",
            "locate_tail": "must be set to the value `vertex-2023-10-16`.",
            "question": None,
            "atomic_claims": [
                ("On Google Cloud's Agent Platform, `anthropic_version` is passed in "
                 "the request body rather than as a header."),
                "`anthropic_version` must be set to the value `vertex-2023-10-16`.",
            ],
            "critical_strings": [
                "Google Cloud's Agent Platform", "`anthropic_version`",
                "passed in the request body", "rather than as a header",
                "vertex-2023-10-16",
            ],
            "what_changed": (
                "Extended backwards to the sentence that names Google Cloud's Agent "
                "Platform as the subject of the two request-format differences."
            ),
            "why": (
                "The approved claim says \"On Google Cloud Agent Platform\" and the "
                "approved span does not contain that scope — the audit's UNSUPPORTED "
                "finding is correct. The extension also fixes something the audit did "
                "not look for: the approved span opens on \"Instead, it is specified "
                "in…\", an anaphoric reference to the previous bullet. Both defects "
                "close with the same extension."
            ),
        },
        {
            "option": "B",
            "kind": "claim_narrowing",
            "recommended": False,
            "locate_head": None,
            "locate_tail": None,
            "question": None,
            "atomic_claims": [
                ("On Agent Platform, `anthropic_version` is passed in the request "
                 "body (rather than as a header), and must be set to "
                 "`vertex-2023-10-16`."),
            ],
            "critical_strings": [
                "On Agent Platform", "`anthropic_version`",
                "passed in the request body", "rather than as a header",
                "vertex-2023-10-16",
            ],
            "what_changed": "The anchor does not move. The claim drops \"Google Cloud\".",
            "why": (
                "Smaller, and fully supported by the existing span. It is not "
                "recommended: the question still asks about Google Cloud, so a reader "
                "checking the anchor alone cannot confirm which Agent Platform is meant, "
                "and the span keeps its anaphoric opening. It trades a real fix for a "
                "smaller diff."
            ),
        },
    ],
    "GOLD-B001-17": [
        {
            "option": "A",
            "kind": "evidence_boundary_expansion",
            "recommended": True,
            "locate_head": "Common errors when using the Files API include:",
            "locate_tail": "and cannot be downloaded.",
            "question": None,
            "atomic_claims": [
                "A Files API `File not found` error uses HTTP 404.",
                ("It indicates that the specified `file_id` doesn't exist or the "
                 "caller doesn't have access to it."),
            ],
            "critical_strings": [
                "Common errors when using the Files API", "File not found (404)",
                "`file_id`", "doesn't exist or you don't have access to it",
            ],
            "what_changed": (
                "Extended backwards to the line that names the Files API as the scope of "
                "the error list. The span's end is unchanged."
            ),
            "why": (
                "The approved claim says \"Files API\", which appears only in the "
                "document title and section path. The extension puts the scope inside "
                "the anchor. The end is not trimmed: the repair path only ever grows an "
                "anchor outward, so that the new span provably contains the approved "
                "one. Two unrelated error bullets therefore stay in the span — a cost "
                "worth stating rather than hiding."
            ),
        },
    ],
}


def build(record: dict, proposal: dict, text: str) -> dict:
    old = (record["char_start"], record["char_end"])
    if proposal["locate_head"]:
        new = locate(text, proposal["locate_head"], proposal["locate_tail"], *old)
        check_superset(text, new, old)
    else:
        new = old
    new_text = text[new[0]:new[1]]
    new_hash = hashlib.sha256(new_text.encode("utf-8")).hexdigest()

    proposed = {
        **{k: record[k] for k in ("candidate_id", "provider", "document_title",
                                  "source_url", "section_path", "version_id",
                                  "proposed_answer", "proposed_category")},
        "captured_at": str(record["captured_at"]),
        "verification_status": record["verification_status"],
        "human_verified": record.get("human_verified", False),
        "proposed_question": proposal["question"] or record["proposed_question"],
        "proposed_atomic_claims": proposal["atomic_claims"],
        "critical_strings": proposal["critical_strings"],
        "char_start": new[0], "char_end": new[1],
        "evidence_text": new_text, "evidence_hash": new_hash,
    }
    outside = [s for s in proposal["critical_strings"]
               if not contains_claim_string(new_text, s)]
    return {
        "option": proposal["option"],
        "kind": proposal["kind"],
        "recommended": proposal["recommended"],
        "what_changed": proposal["what_changed"],
        "why": proposal["why"],
        "old_char_start": old[0], "old_char_end": old[1],
        "old_evidence_text": record["evidence_text"],
        "old_evidence_hash": record["evidence_hash"],
        "new_char_start": new[0], "new_char_end": new[1],
        "new_evidence_text": new_text,
        "new_evidence_hash": new_hash,
        "characters_added": (new[1] - new[0]) - (old[1] - old[0]),
        "anchor_moved": new != old,
        "proposed_question": proposed["proposed_question"],
        "proposed_answer": proposed["proposed_answer"],
        "proposed_atomic_claims": proposed["proposed_atomic_claims"],
        "critical_strings": proposal["critical_strings"],
        "critical_strings_outside_span": outside,
        "eligibility": evaluate(proposed),
        "_case": proposed,
    }


def code_span(text: str) -> str:
    """Markdown code span that survives text already containing backticks."""
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def render(packet: dict) -> str:
    lines = [
        "# GOLD-001 — batch 001 v2 scope repairs",
        "",
        ("Two cases, proposed and applied to nothing. Batch 001 v1 is unchanged and "
         f"still hashes to `{packet['v1_closure_sha256'][:16]}…`; the v2 metadata "
         "overlay deliberately excludes both of these because neither can be fixed by "
         "adding metadata."),
        "",
        ("Both were flagged by the mechanical claim audit and both flags are correct: "
         "each case asserts a scope its approved anchor does not contain. Neither is "
         "holdout-eligible until one of the options below is approved."),
        "",
        "---",
        "",
    ]
    for candidate_id, options in packet["repairs"].items():
        lines += [f"## {candidate_id}", "",
                  f"**Current question.** {options[0]['proposed_question']}", "",
                  f"**Current answer.** {options[0]['proposed_answer']}", "",
                  "**Current claims (as approved in v1)**", ""]
        lines += [f"  {i}. {c}" for i, c in
                  enumerate(packet["current_claims"][candidate_id], 1)]
        lines += ["", ("**Current exact evidence** — "
                   f"{options[0]['old_char_start']}–{options[0]['old_char_end']} · "
                   f"`{options[0]['old_evidence_hash'][:16]}…`"), "",
                  "```", options[0]["old_evidence_text"], "```", ""]
        for option in options:
            mark = " — **recommended**" if option["recommended"] else ""
            lines += [
                f"### Option {option['option']}: {option['kind']}{mark}", "",
                (f"**What changed.** {option['what_changed']} "
                 f"({option['characters_added']:+d} characters; anchor "
                 f"{'moved' if option['anchor_moved'] else 'unchanged'}.)"), "",
                f"**Why it is necessary.** {option['why']}", "",
                "**Proposed claims**", "",
            ]
            lines += [f"  {i}. {c}" for i, c in
                      enumerate(option["proposed_atomic_claims"], 1)]
            if option["anchor_moved"]:
                lines += ["", ("**Proposed exact evidence** — "
                           f"{option['new_char_start']}–{option['new_char_end']} · "
                           f"`{option['new_evidence_hash'][:16]}…`"), "",
                          "```", option["new_evidence_text"], "```"]
            else:
                lines += ["", ("**Exact evidence** — unchanged, hash still "
                           f"`{option['old_evidence_hash'][:16]}…`")]
            strings = ", ".join(code_span(s) for s in option["critical_strings"])
            lines += ["", f"**Critical strings.** {strings}", "",
                      ("*All verified inside the proposed span.*"
                       if not option["critical_strings_outside_span"]
                       else f"*OUTSIDE THE SPAN: {option['critical_strings_outside_span']}*"),
                      "", f"**Validator.** {option['validator']}", "",
                      ("**Holdout-eligible if approved.** "
                       + ("yes" if option["eligibility"]["holdout_eligible"]
                          else "no")),
                      "", "---", ""]
    lines += [
        "## Decision",
        "",
        ("Approve one option per case, or reject both. Nothing is applied until you do, "
         "and applying it creates a v2 record — batch 001 v1 stays closed and unchanged "
         "either way."),
        "",
        ("Until then the project stands at "
         f"**{packet['holdout_eligible_now']} holdout-eligible** cases, with these two "
         "pending."),
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch")
    parser.add_argument("--overlay", default="evals/gold/batch_001_v2/overlay.json")
    parser.add_argument("--out-dir", default="evals/gold/batch_001_v2")
    args = parser.parse_args()

    batch = json.loads(Path(args.batch).read_text())
    overlay = json.loads(Path(args.overlay).read_text())
    records = {r["candidate_id"]: r for r in batch["records"]}

    with connect_sources() as sources:
        repairs, cases_for_validation = {}, []
        for candidate_id, options in PROPOSALS.items():
            record = records[candidate_id]
            text = sources[record["version_id"]]["text"]
            built = []
            for proposal in options:
                item = build(record, proposal, text)
                case = item.pop("_case")
                case["case_id"] = f"{candidate_id}-option-{item['option']}"
                cases_for_validation.append((item, case))
                built.append(item)
            repairs[candidate_id] = built

        # Validated against the eligible v2 set, so a proposed repair cannot duplicate a
        # question or a span that is already in play.
        context = [project(c, "validation") for c in overlay["case_records"]]
        projections = []
        for item, case in cases_for_validation:
            projection = project(case, "validation")
            projection["case_id"] = case["case_id"]
            projections.append((item, projection))
        # One validator run per option. Options for the same case are mutually
        # exclusive, so validating them together would report each as a duplicate
        # question of the other — a artefact of the harness, not a defect in either.
        for item, projection in projections:
            problems = [f for f in validate(context + [projection], sources,
                                            require_human=set())
                        if f["case_id"] == projection["case_id"]]
            item["validator"] = ("PASS — all blocking checks" if not problems
                                 else "FAIL: " + "; ".join(
                                     f"{p['check']} ({p['detail']})" for p in problems))

    packet = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "PROPOSED — applied to nothing, awaiting explicit owner approval",
        "v1_closure_sha256": batch.get("closure_sha256"),
        "v1_unchanged": True,
        "holdout_eligible_now": overlay["holdout_eligible_count"],
        "current_claims": {cid: records[cid]["proposed_atomic_claims"]
                           for cid in PROPOSALS},
        "repairs": repairs,
        "retrieval_was_not_run": True,
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "gold_batch_001_v2_scope_repairs.json").write_text(
        json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "gold_batch_001_v2_scope_repairs.md").write_text(
        render(packet), encoding="utf-8")

    for candidate_id, options in repairs.items():
        for option in options:
            print(f"  {candidate_id} option {option['option']}: "
                  f"{option['characters_added']:+d} chars, {option['validator']}, "
                  f"eligible={option['eligibility']['holdout_eligible']}")
    print(f"wrote {out_dir}/gold_batch_001_v2_scope_repairs.md")
    return 0


class connect_sources:
    """Load the frozen sources once and hand them to the caller."""

    def __enter__(self):
        from rag_v1.db import connect
        with connect() as conn, conn.cursor() as cur:
            self._sources = load_sources(cur)
        return self._sources

    def __exit__(self, *exc):
        return False


if __name__ == "__main__":
    raise SystemExit(main())
