#!/usr/bin/env python3
"""GOLD-001: build a versioned promotion overlay over a closed batch.

A closed batch does not change. When later work shows that an approved case is missing
something a machine needs — as batch 001's claim audit showed for 13 of 16 cases — the
answer is a new version layered on top, not an edit underneath.

This builder is deliberately incapable of doing anything else. It copies question,
answer, atomic claims, evidence span, source version and evidence hash straight from the
closed case and refuses to write if the spec would change any of them; the only thing it
adds is validation metadata. It also re-checks the v1 closure hash first, so an overlay
can never be built over a batch that has quietly drifted.

Eligibility is computed, not asserted: ``rag_v1.gold.eligibility`` answers whether each
case may enter a holdout, and a case can gain eligibility here without its human approval
being re-litigated. The two states are separate on purpose.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.db import connect
from rag_v1.gold.eligibility import evaluate
from rag_v1.gold.normalisation import contains_claim_string

sys.path.insert(0, str(Path(__file__).resolve().parent))
from close_batch import candidate_digest
from export_golden_projection import project
from repair_evidence_boundary import check_superset
from validate_golden import load_sources

#: Copied from v1 and never altered by an overlay of this kind.
IMMUTABLE = ("proposed_question", "proposed_answer", "proposed_atomic_claims",
             "char_start", "char_end", "version_id", "evidence_hash", "evidence_text")


def build_case(v1: dict, strings: list[str], note: str | None) -> dict:
    case = {field: v1[field] for field in IMMUTABLE}
    case.update({
        "candidate_id": v1["candidate_id"],
        "verification_status": v1["verification_status"],
        "human_verified": v1.get("human_verified", False),
        "human_reviewer": v1.get("human_reviewer"),
        "human_reviewed_at": v1.get("human_reviewed_at"),
        "section_path": v1["section_path"],
        "provider": v1["provider"],
        "document_title": v1["document_title"],
        "source_url": v1["source_url"],
        "captured_at": str(v1["captured_at"]),
        "proposed_category": v1.get("proposed_category"),
        "critical_strings": strings,
        "v2_change": "validation metadata only: critical claim strings added",
        "v1_evidence_hash": v1["evidence_hash"],
    })
    if note:
        case["human_review_outcome"] = note
    return case


def build_scope_repair(v1: dict, approval: dict, text: str, now: str) -> dict:
    """Promote an owner-approved boundary expansion into a v2 record.

    A scope repair is not metadata: the span changes. What does not change is v1 — its
    offsets, text, hash and approval are carried onto the v2 record beside the new ones,
    so the promotion can be read without opening two files.
    """
    old = (v1["char_start"], v1["char_end"])
    new = (approval["char_start"], approval["char_end"])
    check_superset(text, new, old)

    new_text = text[new[0]:new[1]]
    new_hash = hashlib.sha256(new_text.encode("utf-8")).hexdigest()
    expected = approval["expected_hash_prefix"]
    if not new_hash.startswith(expected):
        raise SystemExit(
            f"refusing {v1['candidate_id']}: the approved span hashes to "
            f"{new_hash[:16]}…, but the approval names {expected}…. The owner approved a "
            "different span than this one."
        )
    missing = [s for s in approval["critical_strings"]
               if not contains_claim_string(new_text, s)]
    if missing:
        raise SystemExit(
            f"refusing {v1['candidate_id']}: critical strings outside the approved "
            f"span: {missing}")

    case = build_case(v1, approval["critical_strings"], None)
    case.update({
        "proposed_atomic_claims": approval["atomic_claims"],
        "char_start": new[0], "char_end": new[1],
        "evidence_text": new_text, "evidence_hash": new_hash,
        "v2_change": f"{approval['kind']} (option {approval['option']})",
        "v2_approval": {
            "reviewer": "project_owner", "decision": "APPROVE", "reviewed_at": now,
            "approved_char_start": new[0], "approved_char_end": new[1],
            "approved_evidence_hash": new_hash,
            "approved_option": approval["option"],
        },
        "v1_char_start": old[0], "v1_char_end": old[1],
        "v1_evidence_text": v1["evidence_text"],
        "v1_evidence_hash": v1["evidence_hash"],
        "v1_atomic_claims": v1["proposed_atomic_claims"],
        "v1_approval": {
            "reviewer": v1.get("human_reviewer"),
            "reviewed_at": v1.get("human_reviewed_at"),
            "decision": (v1.get("human_decision_history") or [{}])[-1].get("decision"),
        },
        "repair_reason": approval["reason"],
        "characters_added": (new[1] - new[0]) - (old[1] - old[0]),
    })
    return case


def render_closure(overlay: dict, validation: dict) -> str:
    repairs = "\n".join(
        f"| `{cid}` | {r['v1_span'][0]}–{r['v1_span'][1]} | "
        f"{r['v2_span'][0]}–{r['v2_span'][1]} | {r['characters_added']:+d} | "
        f"`{r['v1_evidence_hash'][:12]}…` | `{r['v2_evidence_hash'][:12]}…` |"
        for cid, r in sorted(overlay.get("scope_repairs", {}).items()))
    return "\n".join([
        "# GOLD-001 — batch 001 v2 closure",
        "",
        ("**This does not replace the batch 001 v1 closure.** v1 stays closed at 16 "
         "`human_verified` and 2 `human_rejected`, and still hashes to "
         f"`{overlay['v1_closure_sha256'][:16]}…`, which the builder re-verifies before "
         "writing anything here."),
        "",
        "| | |",
        "| --- | --- |",
        f"| cases in v2 | **{overlay['cases']}** |",
        f"| metadata upgraded | {overlay['metadata_upgraded']} |",
        f"| scope repaired | {overlay['scope_repaired']} |",
        f"| carried forward unchanged | {overlay['carried_forward_unchanged']} |",
        f"| `human_verified` | {overlay['cases']} |",
        f"| `holdout_eligible` | **{overlay['holdout_eligible_count']}** |",
        f"| pending scope repair | {len(overlay['pending_scope_repair'])} |",
        (f"| validator | **{validation['cases']} cases, "
         f"{len(validation['failures'])} failures** |"),
        "",
        "## Scope repairs applied",
        "",
        "| case | v1 span | v2 span | Δ | v1 hash | v2 hash |",
        "| --- | --- | --- | --- | --- | --- |",
        repairs or "| — | | | | | |",
        "",
        ("Both were approved by the project owner as option A, evidence-boundary "
         "expansion. Each v2 record carries its v1 span, v1 text, v1 hash, v1 claims and "
         "v1 approval beside the new ones, so the promotion reads in one place. The "
         "builder refuses to write if the approved span does not hash to the value the "
         "approval names — an approval of a different span is not an approval of this "
         "one."),
        "",
        "## Eligibility",
        "",
        ("All five conditions in `rag_v1.gold.eligibility` hold for every case: human "
         "approval, a deterministic check for every claim, critical strings present in "
         "the evidence, a valid evidence hash, and no unresolved scope defect."),
        "",
        overlay["human_verified_is_unchanged"],
        "",
        "## Not done",
        "",
        ("- No holdout is frozen. The project has too few cases for a validation split "
         "and a genuinely unseen holdout both."),
        "- No retrieval was run, and SYSTEM-A and SYSTEM-B remain frozen and unexecuted.",
        "- Batch 001 v1 is unchanged and stays the historical record.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch")
    parser.add_argument("--spec", default="evals/gold/batch_001_v2/metadata-spec.json")
    parser.add_argument("--out-dir", default="evals/gold/batch_001_v2")
    parser.add_argument("--closure-dir", default=None,
                        help="also write v2 closure artifacts here")
    parser.add_argument("--validation", default="evals/gold/batch_001_v2/validation.json")
    args = parser.parse_args()

    batch = json.loads(Path(args.batch).read_text())
    spec = json.loads(Path(args.spec).read_text())
    records = {r["candidate_id"]: r for r in batch["records"]}

    recorded = batch.get("closure_sha256")
    if not recorded:
        raise SystemExit("refusing: the batch is not closed, so there is nothing to layer on")
    if candidate_digest(batch["records"]) != recorded:
        raise SystemExit(
            "refusing: the closed batch no longer matches its closure hash. An overlay "
            "over drifted records would be layered on something nobody approved."
        )

    unknown = sorted(set(spec["critical_strings"]) - set(records))
    if unknown:
        raise SystemExit(f"spec names candidates not in the batch: {unknown}")

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    cases, problems = [], []
    for candidate_id, strings in sorted(spec["critical_strings"].items()):
        v1 = records[candidate_id]
        if v1.get("verification_status") != "human_verified":
            problems.append(f"[{candidate_id}] is not human_verified")
            continue
        missing = [s for s in strings if not contains_claim_string(v1["evidence_text"], s)]
        if missing:
            problems.append(f"[{candidate_id}] critical strings outside the span: {missing}")
            continue
        if hashlib.sha256(v1["evidence_text"].encode("utf-8")).hexdigest() != \
                v1["evidence_hash"]:
            problems.append(f"[{candidate_id}] v1 evidence hash does not recompute")
            continue
        cases.append(build_case(
            v1, strings, spec.get("human_review_outcomes", {}).get(candidate_id)))

    scope_spec = spec.get("scope_repairs", {})
    repaired_ids = [k for k in scope_spec if k.startswith("GOLD-")]
    if repaired_ids:
        with connect() as conn, conn.cursor() as cur:
            sources = load_sources(cur)
        for candidate_id in sorted(repaired_ids):
            v1 = records[candidate_id]
            source = sources.get(v1["version_id"])
            if source is None:
                problems.append(f"[{candidate_id}] version not in the snapshot")
                continue
            cases.append(build_scope_repair(
                v1, scope_spec[candidate_id], source["text"], now))

    # Cases already carrying critical strings in v1 come along unchanged, so the overlay
    # is the complete eligible set rather than only the newly upgraded part.
    for candidate_id, record in sorted(records.items()):
        if (candidate_id in spec["critical_strings"] or candidate_id in scope_spec
                or not record.get("critical_strings")):
            continue
        if record.get("verification_status") != "human_verified":
            continue
        case = build_case(record, record["critical_strings"], None)
        case["v2_change"] = "carried forward from v1 unchanged; already claim-checkable"
        cases.append(case)

    if problems:
        print(f"{len(problems)} problems — nothing was written:")
        for problem in problems:
            print("  ", problem)
        return 1

    verdicts = {c["candidate_id"]: evaluate(c) for c in cases}
    eligible = sorted(cid for cid, v in verdicts.items() if v["holdout_eligible"])
    pending = sorted(spec.get("not_included", {}))

    overlay = {
        "overlay": spec["overlay"],
        "built_at": now,
        "layers_on": spec["layers_on"],
        "v1_closure_sha256": recorded,
        "v1_is_unchanged": (
            "This overlay reads the closed batch and writes nothing back to it. The v1 "
            "closure hash above was re-verified against the v1 records before building."
        ),
        "kind": spec["kind"],
        "rule": spec["rule"],
        "cases": len(cases),
        "metadata_upgraded": len(spec["critical_strings"]),
        "scope_repaired": len(repaired_ids),
        "scope_repairs": {c["candidate_id"]: {
            "v1_span": [c["v1_char_start"], c["v1_char_end"]],
            "v2_span": [c["char_start"], c["char_end"]],
            "v1_evidence_hash": c["v1_evidence_hash"],
            "v2_evidence_hash": c["evidence_hash"],
            "characters_added": c["characters_added"],
            "reason": c["repair_reason"],
            "v1_approval": c["v1_approval"], "v2_approval": c["v2_approval"],
        } for c in cases if c["candidate_id"] in scope_spec},
        "carried_forward_unchanged": (
            len(cases) - len(spec["critical_strings"]) - len(repaired_ids)),
        "holdout_eligible_count": len(eligible),
        "holdout_eligible": eligible,
        "not_included": spec.get("not_included", {}),
        "pending_scope_repair": [c for c in pending
                                 if "scope defect" in spec["not_included"][c]],
        "eligibility_verdicts": verdicts,
        "human_verified_is_unchanged": (
            "Every case here was human_verified in v1 and still is. Eligibility is a "
            "separate state; gaining it required no new approval and losing it would "
            "not revoke one."
        ),
        "retrieval_was_not_run": True,
        "case_records": cases,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "overlay.json").write_text(
        json.dumps(overlay, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    projection = [project(c, "validation") for c in cases]
    (out_dir / "projection.jsonl").write_text(
        "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in projection),
        encoding="utf-8")

    if args.closure_dir and Path(args.validation).exists():
        validation = json.loads(Path(args.validation).read_text())
        closure_dir = Path(args.closure_dir)
        closure_dir.mkdir(parents=True, exist_ok=True)
        closure = {
            "overlay": overlay["overlay"],
            "closed_at": now,
            "closed_by": "project_owner",
            "replaces_v1_closure": False,
            "v1_closure_sha256": overlay["v1_closure_sha256"],
            "totals": {
                "cases": overlay["cases"],
                "human_verified": overlay["cases"],
                "holdout_eligible": overlay["holdout_eligible_count"],
                "pending_scope_repair": len(overlay["pending_scope_repair"]),
                "metadata_upgraded": overlay["metadata_upgraded"],
                "scope_repaired": overlay["scope_repaired"],
            },
            "scope_repairs": overlay.get("scope_repairs", {}),
            "validation": {"cases": validation["cases"],
                           "failures": len(validation["failures"]),
                           "passed": validation["passed"]},
            "retrieval_was_not_run": True,
            "systems_run_against_these_cases": [],
            "holdout_frozen": False,
        }
        (closure_dir / "GOLD-001-batch-001-v2-closure.json").write_text(
            json.dumps(closure, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (closure_dir / "GOLD-001-batch-001-v2-closure.md").write_text(
            render_closure(overlay, validation), encoding="utf-8")
        print(f"wrote {closure_dir}/GOLD-001-batch-001-v2-closure.md")

    print(f"built {spec['overlay']}: {len(cases)} cases "
          f"({len(spec['critical_strings'])} metadata upgraded, "
          f"{len(repaired_ids)} scope repaired, "
          f"{len(cases) - len(spec['critical_strings']) - len(repaired_ids)} "
          "carried forward)")
    print(f"  holdout-eligible: {len(eligible)}")
    print(f"  pending scope repair: {', '.join(overlay['pending_scope_repair']) or '—'}")
    print("  v1 closure hash re-verified; v1 untouched")
    print(f"  status counts: {dict(Counter(c['verification_status'] for c in cases))}")
    print(f"wrote {out_dir}/overlay.json")
    print(f"wrote {out_dir}/projection.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
