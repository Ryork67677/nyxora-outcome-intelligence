#!/usr/bin/env python3
"""GOLD-001: apply an internal source-integrity review to a batch.

Batches 004 and 005 each got a bespoke copy of this machinery, which is one copy too
many: a fix to the superset check in one would not reach the other. This is the general
version, parameterised by batch number, and it is what later batches should use.

The review itself lives in a decisions file — the judgements, the findings, the repairs,
written against the frozen evidence. This script checks them and records the result: it
re-reads the corpus, verifies that every repaired anchor is a strict outward growth of
the one it replaces, recomputes hashes, re-runs the precheck against the repaired record,
and refuses to write anything if a repair would make a case worse.

Two rules shape the output. The generation artifact is never rewritten — repairs go to a
separate file naming what changed, from what, to what, and why. And nothing here approves
anything: every candidate stays ``candidate_unverified``, and the owner accepts a repair
by quoting the new evidence hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.db import connect
from rag_v1.gold.anaphora import CRITICAL, NONCRITICAL, evaluate_span
from rag_v1.gold.defects import line as defect_line
from rag_v1.gold.mining import _section_for
from rag_v1.gold.normalisation import contains_claim_string
from rag_v1.parsing import _sections_from_markdown

EVIDENCE_HARD_CAP = 1500
EVIDENCE_SOFT_CAP = 1000
STATUSES = ("READY_FOR_OWNER_REVIEW", "NEEDS_REPAIR", "REJECT_RECOMMENDED")
#: Fields a review may rewrite. Each rewrite becomes a numbered revision keeping the
#: original, so the review can be disagreed with.
REWRITABLE = (
    "question", "answer", "atomic_claims", "reasoning_type", "secondary_category",
    "composed_claim", "composed_answer", "bridge_relationship",
    "why_span_1_alone_is_insufficient", "why_span_2_alone_is_insufficient",
)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_sources(version_ids: set[str]) -> dict:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT version_id, normalized_text FROM document_version "
            "WHERE version_id = ANY(%s)", (sorted(version_ids),))
        rows = cur.fetchall()
    return {version: {"text": text, "sections": _sections_from_markdown(text)}
            for version, text in rows}


def check_superset(old: dict, new_start: int, new_end: int) -> None:
    """A repaired anchor may only grow outward.

    An anchor that moves rather than grows is a different claim wearing the same
    candidate id, and the reviewer who approved the first never saw the second.
    """
    if new_start > old["char_start"] or new_end < old["char_end"]:
        raise SystemExit(
            f"repair to {old['evidence_id']} is not a superset: "
            f"{old['char_start']}–{old['char_end']} -> {new_start}–{new_end}")
    if (new_start, new_end) == (old["char_start"], old["char_end"]):
        raise SystemExit(f"repair to {old['evidence_id']} changes nothing")


def repair_spans(record: dict, decision: dict, sources: dict) -> tuple[list, list]:
    spans = [dict(span) for span in record["expected_evidence"]]
    by_id = {span["evidence_id"]: span for span in spans}
    revisions: list[dict] = []

    for repair in decision.get("evidence_repairs", []):
        start, end = repair["new_char_start"], repair["new_char_end"]
        if repair.get("action") == "add_scope_span":
            version = repair["version_id"]
            source = sources[version]
            text = source["text"][start:end]
            spans.append({
                "evidence_id": repair["evidence_id"], "version_id": version,
                "section_path": _section_for(source["sections"], start),
                "char_start": start, "char_end": end, "evidence_text": text,
                "evidence_hash": sha(text), "evidence_char_length": end - start,
                "critical_strings": repair["critical_strings"],
            })
            revisions.append({
                "evidence_id": repair["evidence_id"], "action": "add_scope_span",
                "new_char_start": start, "new_char_end": end,
                "new_evidence_text": text, "new_evidence_hash": sha(text),
                "reason": repair["reason"]})
            continue

        old = by_id[repair["evidence_id"]]
        check_superset(old, start, end)
        source = sources[old["version_id"]]
        text = source["text"][start:end]
        if old["evidence_text"] not in text:
            raise SystemExit(
                f"{repair['evidence_id']}: the repaired span does not contain the "
                "original text — the offsets do not describe the same evidence")
        revisions.append({
            "evidence_id": old["evidence_id"], "action": "extend_boundary",
            "old_char_start": old["char_start"], "old_char_end": old["char_end"],
            "old_evidence_hash": old["evidence_hash"],
            "old_evidence_text": old["evidence_text"],
            "new_char_start": start, "new_char_end": end,
            "new_evidence_text": text, "new_evidence_hash": sha(text),
            "reason": repair["reason"]})
        old.update({
            "char_start": start, "char_end": end, "evidence_text": text,
            "evidence_hash": sha(text), "evidence_char_length": end - start,
            "section_path": _section_for(source["sections"], start)})

    spans.sort(key=lambda s: s["evidence_id"])
    for index, span in enumerate(spans, 1):
        span["evidence_id"] = f"E{index}"
    return spans, revisions


def remap_claims(record: dict) -> list[dict]:
    spans = record["expected_evidence"]
    out = []
    for index, claim in enumerate(record["atomic_claims"]):
        if len(record["atomic_claims"]) == len(spans):
            span = spans[index]
        else:
            span = next(
                (s for s in spans
                 if any(contains_claim_string(claim, t) for t in s["critical_strings"])),
                spans[0])
        out.append({"claim": claim, "evidence_id": span["evidence_id"],
                    "critical_strings": span["critical_strings"]})
    return out


def apply_decision(record: dict, decision: dict, sources: dict) -> dict:
    repaired = json.loads(json.dumps(record))
    spans, revisions = repair_spans(record, decision, sources)
    repaired["expected_evidence"] = spans

    if "critical_strings_by_span" in decision:
        original = [s["evidence_id"] for s in record["expected_evidence"]]
        for position, span in enumerate(spans):
            key = (original[position] if position < len(original)
                   else span["evidence_id"])
            if key in decision["critical_strings_by_span"]:
                span["critical_strings"] = decision["critical_strings_by_span"][key]
    elif "critical_strings" in decision and len(spans) == 1:
        spans[0]["critical_strings"] = decision["critical_strings"]

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    for field in REWRITABLE:
        if field not in decision or decision[field] == repaired.get(field):
            continue
        repaired.setdefault("revisions", []).append({
            "revision": len(repaired.get("revisions", [])) + 1,
            "field": field, "from": repaired.get(field), "to": decision[field],
            # Batch 006's revisions were dictated by the owner in their decision brief,
            # not proposed by Claude reading its own output. Those are different acts
            # and the record has to be able to tell them apart, so a decision may name
            # its author. Absent that, it is Claude's own review.
            "author": decision.get("revision_author",
                                   "claude (internal authoring review)"),
            "timestamp": now,
            "reason": decision.get("reason") or "internal source-integrity review"})
        repaired[field] = decision[field]

    repaired["proposed_question"] = repaired["question"]
    repaired["proposed_answer"] = repaired["answer"]
    repaired["proposed_atomic_claims"] = repaired["atomic_claims"]
    repaired["section_path"] = spans[0]["section_path"]
    repaired["critical_strings"] = [s for span in spans for s in span["critical_strings"]]
    repaired["evidence_char_length"] = sum(s["evidence_char_length"] for s in spans)
    if len(spans) > 1 and repaired["evidence_shape"] == "single_span":
        repaired["evidence_shape"] = (
            "multi_document" if len({s["version_id"] for s in spans}) > 1
            else "multi_span")
    repaired["requires_all_evidence"] = len(spans) > 1
    if revisions:
        repaired["anchor_revisions"] = revisions
    if "interaction" in decision:
        repaired["interaction"] = decision["interaction"]
    repaired["claim_evidence_map"] = remap_claims(repaired)
    return repaired


def precheck(record: dict) -> tuple[list[str], list[str]]:
    """Structural only. §2B: a critical anaphora blocks; a noncritical one is flagged."""
    failures: list[str] = []
    flags: list[str] = []
    for span in record["expected_evidence"]:
        body = span["evidence_text"]
        if sha(body) != span["evidence_hash"]:
            failures.append(f"{span['evidence_id']}: hash does not match its text")
        if not (0 <= span["char_start"] < span["char_end"]):
            failures.append(f"{span['evidence_id']}: invalid span")
        if not span["critical_strings"]:
            failures.append(f"{span['evidence_id']}: no critical strings")
        stray = [s for s in span["critical_strings"]
                 if not contains_claim_string(body, s)]
        if stray:
            failures.append(f"{span['evidence_id']}: strings outside this span: {stray}")
        verdict = evaluate_span(body, record)
        if verdict["status"] == CRITICAL:
            failures.append(
                f"{span['evidence_id']}: critical anaphora — {verdict['finding']}")
        elif verdict["status"] == NONCRITICAL:
            flags.append(f"{span['evidence_id']}: noncritical anaphora — "
                         f"{verdict['finding']}")
        if span["evidence_char_length"] > EVIDENCE_HARD_CAP:
            failures.append(f"{span['evidence_id']}: over the {EVIDENCE_HARD_CAP} cap")
        elif span["evidence_char_length"] > EVIDENCE_SOFT_CAP:
            flags.append(f"{span['evidence_id']}: {span['evidence_char_length']} chars, "
                         f"over the {EVIDENCE_SOFT_CAP} soft cap")
    if not (record["question"] and record["answer"] and record["atomic_claims"]):
        failures.append("question, answer or claims missing")
    if not record["retrieval_was_not_run"]:
        failures.append("retrieval leakage")
    return failures, flags


def _changed(record: dict | None) -> bool:
    return bool(record and (record.get("revisions") or record.get("anchor_revisions")))


def render_review(payload: dict, decisions_doc: dict) -> str:
    counts = payload["status_counts"]
    review = decisions_doc["candidates"]
    repaired = {r["candidate_id"]: r for r in payload["records"]}
    number = payload["batch"]

    rows = "\n".join(
        f"| `{cid}` | {d['status']} | "
        f"{'yes' if _changed(repaired.get(cid)) else 'no'} | "
        f"{len(d['findings'])} |" for cid, d in sorted(review.items()))
    lines = [
        f"# GOLD-001 — batch {number:03d} internal source-integrity review",
        "",
        (f"**{sum(counts.values())} candidates reviewed against the frozen evidence · "
         f"{payload['repaired_candidates']} repaired · reviewed "
         f"{payload['reviewed_at']}**"),
        "",
        ("This is an internal review by the authoring model. It is not independent "
         "verification, not a second opinion from another party, and it changes no "
         "candidate's status: all of them remain `candidate_unverified`."),
        "",
        "## Outcome",
        "",
        "| status | candidates |",
        "| --- | --- |",
        *(f"| {status} | {count} |"
          for status, count in sorted(counts.items(), key=lambda kv: -kv[1])),
        "",
        "| candidate | status | repaired | findings |",
        "| --- | --- | --- | --- |",
        rows,
        "",
        "## Findings by candidate",
        "",
    ]
    for candidate_id, decision in sorted(review.items()):
        lines += [f"### {candidate_id} — {decision['status']}", ""]
        lines += ([f"- {finding}" for finding in decision["findings"]]
                  or ["- No finding."])
        if "interaction" in decision:
            interaction = decision["interaction"]
            lines += ["", "**Interaction recorded**", "",
                      f"- A: {interaction['setting_or_state_A']}",
                      f"- B: {interaction['setting_or_state_B']}",
                      f"- relation: {interaction['documented_relation']}"]
        if _changed(repaired.get(candidate_id)):
            record = repaired[candidate_id]
            lines += ["", "**Repairs**", ""]
            for revision in record.get("anchor_revisions", []):
                if revision["action"] == "extend_boundary":
                    lines.append(
                        f"- `{revision['evidence_id']}` "
                        f"{revision['old_char_start']}–{revision['old_char_end']} → "
                        f"{revision['new_char_start']}–{revision['new_char_end']} "
                        f"({revision['reason']}); hash "
                        f"`{revision['old_evidence_hash'][:12]}…` → "
                        f"`{revision['new_evidence_hash'][:12]}…`")
                else:
                    lines.append(
                        f"- `{revision['evidence_id']}` scope span added at "
                        f"{revision['new_char_start']}–{revision['new_char_end']}")
            for revision in record.get("revisions", []):
                lines.append(f"- `{revision['field']}` rewritten")
        lines.append("")

    defects = decisions_doc.get("generator_defects_found") or []
    if defects:
        lines += ["## Generator defects found during review", "",
                  ("Recorded rather than patched. The generation artifact is not being "
                   "regenerated, so a fix belongs in the next batch's preregistration "
                   "where it can be declared before it sees a candidate."), ""]
        lines += [defect_line(d) for d in defects]
        lines.append("")

    lines += [
        "## What this review did not do",
        "",
        ("- It did not approve anything. `human_verified` requires an owner decision.\n"
         "- It did not rewrite the generation artifact; repairs live beside it with the "
         "original text and offsets preserved.\n"
         "- It did not regenerate the batch, add a candidate, or search for new "
         "multi-hop chains.\n"
         "- It did not run retrieval. SYSTEM-A and SYSTEM-B remain frozen and "
         "unexecuted, and the holdout is not frozen."),
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=int, required=True)
    parser.add_argument("--source", default=None)
    parser.add_argument("--decisions", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--report-dir", default="experiments/GOLD-001")
    args = parser.parse_args()

    number = args.batch
    source = Path(args.source or f"evals/review/gold_review_batch_{number:03d}.json")
    decisions_path = Path(
        args.decisions or f"experiments/GOLD-001/b{number:03d}-review-decisions.json")
    out = Path(args.out
               or f"evals/review/gold_review_batch_{number:03d}_repairs.json")

    batch = json.loads(source.read_text())
    decisions_doc = json.loads(decisions_path.read_text())
    decisions = decisions_doc["candidates"]
    records = {r["candidate_id"]: r for r in batch["records"]}

    missing = sorted(set(records) - set(decisions))
    unknown = sorted(set(decisions) - set(records))
    if missing or unknown:
        raise SystemExit(
            f"review does not match the batch — unreviewed: {missing}, "
            f"unknown: {unknown}")
    for candidate_id, decision in decisions.items():
        if decision["status"] not in STATUSES:
            raise SystemExit(f"{candidate_id}: unknown status {decision['status']!r}")

    versions = {span["version_id"] for r in batch["records"]
                for span in r["expected_evidence"]}
    versions |= {rep["version_id"] for d in decisions.values()
                 for rep in d.get("evidence_repairs", []) if "version_id" in rep}
    sources = load_sources(versions)

    repaired: dict[str, dict] = {}
    problems: list[str] = []
    for candidate_id, decision in decisions.items():
        if decision["status"] == "REJECT_RECOMMENDED":
            continue
        touches = any(key in decision for key in
                      ("evidence_repairs", "critical_strings", "revision_author",
                       "critical_strings_by_span", "interaction", *REWRITABLE))
        if not touches:
            continue
        candidate = apply_decision(records[candidate_id], decision, sources)
        failures, flags = precheck(candidate)
        if failures:
            problems += [f"[{candidate_id}] {f}" for f in failures]
        candidate["precheck_failures"] = failures
        candidate["precheck_flags"] = flags
        candidate["precheck_holdout_ready"] = not failures
        repaired[candidate_id] = candidate

    if problems:
        print(f"{len(problems)} repaired candidates fail their own precheck — "
              "nothing was written:")
        for problem in problems:
            print("  ", problem)
        return 1

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "batch": number,
        "reviewed_at": now,
        "reviewer": "claude (internal authoring review)",
        "source_batch": str(source),
        "source_batch_sha256": batch["batch_sha256"],
        "decisions_file": str(decisions_path),
        "note": ("Repairs proposed by an internal review. The generation artifact is "
                 "unchanged. No candidate is verified, approved or eligible; an owner "
                 "accepts a repair by quoting its new evidence hash."),
        "status_counts": dict(Counter(d["status"] for d in decisions.values())),
        # A record rewritten only to attach an interaction annotation is annotated,
        # not repaired. Counting it as a repair would overstate what the review changed.
        "repaired_candidates": sum(
            1 for r in repaired.values()
            if r.get("revisions") or r.get("anchor_revisions")),
        "annotated_candidates": sum(
            1 for r in repaired.values()
            if not (r.get("revisions") or r.get("anchor_revisions"))),
        "generator_defects_found": decisions_doc.get("generator_defects_found", []),
        "retrieval_was_not_run": True,
        "systems_executed": [],
        "records": [repaired[cid] for cid in sorted(repaired)],
        "review": decisions,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")

    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / f"GOLD-001-batch-{number:03d}-internal-review.md").write_text(
        render_review(payload, decisions_doc), encoding="utf-8")
    (report_dir / f"GOLD-001-batch-{number:03d}-internal-review.json").write_text(
        json.dumps({k: v for k, v in payload.items() if k != "records"},
                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"reviewed {len(decisions)} candidates: {payload['status_counts']}")
    print(f"  repaired: {len(repaired)}")
    for candidate_id in sorted(repaired):
        revisions = repaired[candidate_id].get("anchor_revisions", [])
        text = ", ".join(f"{r['evidence_id']} {r['action']}" for r in revisions)
        print(f"    {candidate_id}: {text or 'text only'}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
