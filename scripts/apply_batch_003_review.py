#!/usr/bin/env python3
"""GOLD-001: apply the independent review of batch 003.

Three kinds of correction land here, kept apart because they mean different things
about the miner:

* **wording** — the anchor was right and the generated question or claim was not;
* **evidence boundary** — the anchor did not carry the scope its claim depends on;
* **taxonomy** — the case is fine and its recorded reasoning type was wrong.

The last one matters more than it sounds. Four candidates were labelled ``multi_hop``
because they draw on two spans, but the answer is the two facts rather than a third
derived from them. That is a multi-span *retrieval* test, not multi-hop *reasoning*, and
recording the difference is the point of splitting ``reasoning_type`` from
``evidence_shape``. After this correction batch 003 contains **zero** genuine multi-hop
cases against a target of three to four, and no replacements are hunted for: the batch
has already been independently reviewed, and topping it up afterwards would make the
review meaningless.

Nothing is overwritten. Every text change is a numbered revision, every anchor change
records both spans and both hashes, and no candidate leaves here approved.
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
from rag_v1.gold.mining import anaphora_problem
from rag_v1.gold.mining_v3 import EVIDENCE_HARD_CAP, EVIDENCE_SOFT_CAP
from rag_v1.gold.normalisation import contains_claim_string

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repair_evidence_boundary import locate
from validate_golden import load_sources

STATUS_AFTER_REVISION = "needs_human_review"
CONTEXT_CHARS = 900
#: Reasoning types the project recognises. ``genuine_multi_hop`` is deliberately not a
#: synonym for a case that merely needs two spans.
REASONING_TYPES = (
    "exact_lookup", "error_behavior", "configuration_interaction", "lifecycle",
    "genuine_multi_hop", "ambiguity", "abstention",
)
EVIDENCE_SHAPES = ("single_span", "multi_span", "multi_document")
#: The category the miner recorded maps onto a reasoning type; the shape is separate.
CATEGORY_TO_REASONING = {
    "exact_constraint": "exact_lookup",
    "error_behavior": "error_behavior",
    "configuration_interaction": "configuration_interaction",
    "lifecycle": "lifecycle",
    "multi_hop": "exact_lookup",
}


def span_record(text: str, start: int, end: int, version_id: str,
                section_path: list[str]) -> dict:
    body = text[start:end]
    return {
        "version_id": version_id, "char_start": start, "char_end": end,
        "section_path": section_path, "evidence_text": body,
        "evidence_hash": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "evidence_char_length": len(body),
    }


def build_spans(record: dict, anchor: dict, text: str) -> list[dict]:
    existing = record.get("expected_evidence") or [{
        "version_id": record["version_id"], "char_start": record["char_start"],
        "char_end": record["char_end"], "section_path": record["section_path"],
        "evidence_text": record["evidence_text"],
        "evidence_hash": record["evidence_hash"],
        "evidence_char_length": record["evidence_char_length"]}]

    if anchor["kind"] == "extend":
        start, end = locate(text, anchor["locate_head"], anchor["locate_tail"],
                            record["char_start"], record["char_end"])
        if start > record["char_start"] or end < record["char_end"]:
            raise SystemExit(
                f"refusing {record['candidate_id']}: the repaired span does not contain "
                "the reviewed one. An anchor repair may only grow outward.")
        return [span_record(text, start, end, record["version_id"],
                            record["section_path"])]

    spans = []
    for wanted in anchor["spans"]:
        if wanted.get("keep_existing"):
            spans.append(existing[0])
        elif "keep_index" in wanted:
            spans.append(existing[wanted["keep_index"]])
        else:
            start, end = locate(text, wanted["locate_head"], wanted["locate_tail"],
                                len(text), len(text))
            spans.append(span_record(text, start, end, record["version_id"],
                                     record["section_path"]))
    return sorted(spans, key=lambda s: s["char_start"])


def revise_text(record: dict, spec: dict, reviewer: str, now: str) -> int:
    changed = 0
    for field, key in (("proposed_question", "question"),
                       ("proposed_answer", "answer"),
                       ("proposed_atomic_claims", "atomic_claims"),
                       ("critical_strings", "critical_strings")):
        if key not in spec or spec[key] == record.get(field):
            continue
        record.setdefault("revisions", []).append({
            "revision": len(record.get("revisions", [])) + 1,
            "field": field, "from": record.get(field), "to": spec[key],
            "author": reviewer, "timestamp": now,
            "reason": ", ".join(spec.get("defect_classes", [])) or "review",
        })
        record[field] = spec[key]
        changed += 1
    return changed


def apply_taxonomy(record: dict, reasoning: str, shape: str, now: str,
                   reviewer: str) -> None:
    before = (record.get("reasoning_type"), record.get("evidence_shape"))
    if before != (reasoning, shape) and any(before):
        record.setdefault("revisions", []).append({
            "revision": len(record.get("revisions", [])) + 1,
            "field": "reasoning_type/evidence_shape", "from": list(before),
            "to": [reasoning, shape], "author": reviewer, "timestamp": now,
            "reason": "CATEGORY_MISCLASSIFICATION",
        })
    record["reasoning_type"] = reasoning
    record["evidence_shape"] = shape
    record["requires_all_evidence"] = shape != "single_span"
    if record.get("proposed_category") == "multi_hop":
        record["proposed_category"] = reasoning
        record["not_genuine_multi_hop"] = (
            "Two independent facts from two spans. The answer is the two facts, not a "
            "third derived from them, so this is a multi-span retrieval test and does "
            "not count toward the genuine multi-hop target.")


def audit(record: dict) -> dict:
    """Deterministic checks that must agree with precheck_holdout_ready."""
    spans = record.get("expected_evidence") or [record]
    failures = []
    for span in spans:
        if hashlib.sha256(
                span["evidence_text"].encode("utf-8")).hexdigest() != span["evidence_hash"]:
            failures.append("evidence hash does not match its text")
        # Applied to every evidence kind. An exemption for rows and bullets was drafted
        # and removed: no row or bullet in this batch trips the check, so the exemption
        # bought nothing and would have weakened the gate for a future batch.
        problem = anaphora_problem(span["evidence_text"])
        if problem:
            failures.append(f"unresolved anaphora: {problem}")
    combined = " \n".join(s["evidence_text"] for s in spans)
    outside = [s for s in record.get("critical_strings", [])
               if not contains_claim_string(combined, s)]
    if outside:
        failures.append(f"critical strings outside the evidence: {outside}")
    if not record.get("proposed_atomic_claims"):
        failures.append("no atomic claims")
    total = sum(s["evidence_char_length"] for s in spans)
    if total > EVIDENCE_HARD_CAP:
        failures.append(f"evidence over the {EVIDENCE_HARD_CAP}-character cap")
    if not record.get("retrieval_was_not_run"):
        failures.append("retrieval leakage")
    return {"failures": failures, "evidence_char_length": total,
            "over_soft_cap": total > EVIDENCE_SOFT_CAP}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch")
    parser.add_argument("spec")
    parser.add_argument("--reviewer", default="independent_review")
    parser.add_argument("--report", default="evals/review/batch_003_revision_report.json")
    args = parser.parse_args()

    batch_path = Path(args.batch)
    batch = json.loads(batch_path.read_text())
    spec = json.loads(Path(args.spec).read_text())
    records = {r["candidate_id"]: r for r in batch["records"]}

    claimed = spec.get("source_batch_sha256")
    if claimed and batch.get("batch_sha256") and claimed != batch["batch_sha256"]:
        raise SystemExit("batch hash mismatch — nothing was applied")

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    with connect() as conn, conn.cursor() as cur:
        sources = load_sources(cur)

    applied = []
    for candidate_id, record in sorted(records.items()):
        revision = spec["revisions"].get(candidate_id)
        taxonomy = spec["taxonomy_only"].get(candidate_id)
        anchor_change = None

        if revision and "anchor" in revision:
            text = sources[record["version_id"]]["text"]
            before = [{"char_start": s["char_start"], "char_end": s["char_end"],
                       "evidence_hash": s["evidence_hash"]}
                      for s in (record.get("expected_evidence") or [record])]
            spans = build_spans(record, revision["anchor"], text)
            anchor_change = {
                "revision": len(record.get("anchor_revisions", [])) + 1,
                "reason": revision["anchor"]["reason"],
                "why": revision["anchor"]["why"],
                "old_spans": before,
                "new_spans": [{"char_start": s["char_start"], "char_end": s["char_end"],
                               "evidence_hash": s["evidence_hash"],
                               "evidence_char_length": s["evidence_char_length"]}
                              for s in spans],
                "author": "claude", "directed_by": args.reviewer, "timestamp": now,
            }
            record.setdefault("anchor_revisions", []).append(anchor_change)
            record["expected_evidence"] = spans
            primary = spans[0]
            record.update({
                "char_start": primary["char_start"], "char_end": primary["char_end"],
                "evidence_text": primary["evidence_text"],
                "evidence_hash": primary["evidence_hash"],
                "evidence_char_length": sum(s["evidence_char_length"] for s in spans),
                "context_before": text[max(0, primary["char_start"] - CONTEXT_CHARS):
                                       primary["char_start"]],
                "context_after": text[spans[-1]["char_end"]:
                                      spans[-1]["char_end"] + CONTEXT_CHARS],
            })

        changed = revise_text(record, revision, args.reviewer, now) if revision else 0

        source = revision or taxonomy or {}
        reasoning = source.get("reasoning_type") or CATEGORY_TO_REASONING[
            record["proposed_category"]]
        shape = source.get("evidence_shape") or (
            "multi_span" if len(record.get("expected_evidence") or [1]) > 1
            else "single_span")
        if reasoning not in REASONING_TYPES or shape not in EVIDENCE_SHAPES:
            raise SystemExit(f"{candidate_id}: unknown taxonomy {reasoning}/{shape}")
        apply_taxonomy(record, reasoning, shape, now, args.reviewer)

        result = audit(record)
        record["precheck_holdout_ready"] = not result["failures"]
        record["precheck_failures"] = result["failures"]
        record["evidence_over_soft_cap"] = result["over_soft_cap"]
        if revision or taxonomy:
            record["verification_status"] = STATUS_AFTER_REVISION
            record["review_defect_classes"] = source.get("defect_classes", [
                "CATEGORY_MISCLASSIFICATION"])
            record["review_reason"] = source.get("reason", spec["taxonomy_note"])
            record["verification"] = {
                "reviewer": args.reviewer, "verdict": "FIX_REQUIRED", "reviewed_at": now,
                "verification_notes": record["review_reason"],
            }
        else:
            record["review_defect_classes"] = []
            record["verification"] = {
                "reviewer": args.reviewer, "verdict": "PASS", "reviewed_at": now,
                "verification_notes": "Clean as written; no revision required.",
            }
            record["verification_status"] = STATUS_AFTER_REVISION

        applied.append({
            "candidate_id": candidate_id,
            "outcome": ("clean" if not (revision or taxonomy)
                        else "revised"),
            "defect_classes": record["review_defect_classes"],
            "fields_revised": changed,
            "anchor_revision": anchor_change,
            "reasoning_type": record["reasoning_type"],
            "evidence_shape": record["evidence_shape"],
            "requires_all_evidence": record["requires_all_evidence"],
            "precheck_holdout_ready": record["precheck_holdout_ready"],
            "precheck_failures": record["precheck_failures"],
        })

    batch["review_applied_at"] = now
    batch["review_reviewer"] = args.reviewer
    batch["status_counts"] = dict(Counter(r["verification_status"] for r in batch["records"]))
    # Recompute the header aggregates. A stale generation-time count sitting beside
    # revised records is the same class of defect as the report contradictions this
    # review is correcting.
    lengths = sorted(r["evidence_char_length"] for r in batch["records"])
    batch["evidence_length"] = {
        "mean": round(sum(lengths) / len(lengths), 1),
        "median": lengths[len(lengths) // 2],
        "max": lengths[-1],
        "over_soft_cap": sum(1 for n in lengths if n > EVIDENCE_SOFT_CAP),
    }
    batch["by_category"] = dict(Counter(r["proposed_category"] for r in batch["records"]))
    batch["by_evidence_kind"] = dict(Counter(r["evidence_kind"] for r in batch["records"]))
    batch["by_reasoning_type"] = dict(Counter(r["reasoning_type"] for r in batch["records"]))
    batch["by_evidence_shape"] = dict(Counter(r["evidence_shape"] for r in batch["records"]))
    batch["genuine_multi_hop"] = sum(1 for r in batch["records"]
                                     if r["reasoning_type"] == "genuine_multi_hop")
    batch["precheck_holdout_ready"] = sum(1 for r in batch["records"]
                                          if r["precheck_holdout_ready"])
    batch["verification_status"] = (
        f"reviewed by {args.reviewer} — revised where required; nothing here is gold")
    batch_path.write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")

    report = {
        "batch": 3, "applied_at": now, "reviewer": args.reviewer,
        "source_batch_sha256": batch.get("batch_sha256"),
        "outcomes": dict(Counter(a["outcome"] for a in applied)),
        "defect_classes": dict(Counter(
            d for a in applied for d in a["defect_classes"])),
        "anchor_revisions": [a["candidate_id"] for a in applied if a["anchor_revision"]],
        "by_reasoning_type": batch["by_reasoning_type"],
        "by_evidence_shape": batch["by_evidence_shape"],
        "genuine_multi_hop": batch["genuine_multi_hop"],
        "genuine_multi_hop_target": "3–4",
        "genuine_multi_hop_note": spec["taxonomy_note"],
        "precheck_holdout_ready": batch["precheck_holdout_ready"],
        "precheck_blocked": [a["candidate_id"] for a in applied
                             if not a["precheck_holdout_ready"]],
        "retrieval_was_not_run": True,
        "applied": applied,
    }
    Path(args.report).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                                 encoding="utf-8")

    print(f"applied review to {len(applied)} candidates")
    print("  outcomes         :", report["outcomes"])
    print("  defect classes   :", report["defect_classes"])
    print("  anchor revisions :", ", ".join(report["anchor_revisions"]) or "—")
    print("  reasoning types  :", report["by_reasoning_type"])
    print("  evidence shapes  :", report["by_evidence_shape"])
    print(f"  genuine multi-hop: {report['genuine_multi_hop']} "
          f"(target {report['genuine_multi_hop_target']})")
    print(f"  precheck ready   : {report['precheck_holdout_ready']} of {len(applied)}")
    for entry in applied:
        if not entry["precheck_holdout_ready"]:
            print(f"    {entry['candidate_id']}: {entry['precheck_failures']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
