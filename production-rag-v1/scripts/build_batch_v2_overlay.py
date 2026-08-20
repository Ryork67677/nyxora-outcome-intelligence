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

from rag_v1.gold.eligibility import evaluate
from rag_v1.gold.normalisation import contains_claim_string

sys.path.insert(0, str(Path(__file__).resolve().parent))
from close_batch import candidate_digest
from export_golden_projection import project

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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch")
    parser.add_argument("--spec", default="evals/gold/batch_001_v2/metadata-spec.json")
    parser.add_argument("--out-dir", default="evals/gold/batch_001_v2")
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

    # Cases already carrying critical strings in v1 come along unchanged, so the overlay
    # is the complete eligible set rather than only the newly upgraded part.
    for candidate_id, record in sorted(records.items()):
        if candidate_id in spec["critical_strings"] or not record.get("critical_strings"):
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

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
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
        "carried_forward_unchanged": len(cases) - len(spec["critical_strings"]),
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

    print(f"built {spec['overlay']}: {len(cases)} cases "
          f"({len(spec['critical_strings'])} upgraded, "
          f"{len(cases) - len(spec['critical_strings'])} carried forward)")
    print(f"  holdout-eligible: {len(eligible)}")
    print(f"  pending scope repair: {', '.join(overlay['pending_scope_repair']) or '—'}")
    print("  v1 closure hash re-verified; v1 untouched")
    print(f"  status counts: {dict(Counter(c['verification_status'] for c in cases))}")
    print(f"wrote {out_dir}/overlay.json")
    print(f"wrote {out_dir}/projection.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
