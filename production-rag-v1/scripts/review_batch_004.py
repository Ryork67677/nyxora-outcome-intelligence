#!/usr/bin/env python3
"""GOLD-001: apply the batch-004 internal source-integrity review.

The review itself lives in ``b004-review-decisions.json`` — the judgements, the findings
and the repairs, written against the frozen evidence. This script is the machinery that
checks them and records the result: it re-reads the corpus, verifies that every repaired
anchor is a strict outward growth of the one it replaces, recomputes hashes, re-runs the
precheck against the repaired record, and refuses to write anything if a repair would
make a case worse.

Two rules shape the output.

The generation artifact is never rewritten. ``gold_review_batch_004.json`` stays exactly
as generated, because a benchmark whose generation record is edited after review cannot
be audited. Repairs go to a separate file that names what changed, from what, to what,
and why.

Nothing here approves anything. Every candidate stays ``candidate_unverified``. A repair
is a proposal, and the owner accepts it by quoting the new evidence hash — the same gate
batches 001 and 003 used, and the reason a repaired case cannot be waved through on the
strength of the repair having been made.
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
from rag_v1.gold.mining import _section_for
from rag_v1.gold.normalisation import contains_claim_string
from rag_v1.parsing import _sections_from_markdown

BATCH = Path("evals/review/gold_review_batch_004.json")
DECISIONS = Path("experiments/GOLD-001/b004-review-decisions.json")
EVIDENCE_HARD_CAP = 1500
EVIDENCE_SOFT_CAP = 1000
STATUSES = ("READY_FOR_OWNER_REVIEW", "NEEDS_REPAIR", "REJECT_RECOMMENDED")


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

    Batch 001 established this: an anchor that moves rather than grows is a different
    claim wearing the same candidate id, and the reviewer who approved the first one
    never saw the second.
    """
    if new_start > old["char_start"] or new_end < old["char_end"]:
        raise SystemExit(
            f"repair to {old['evidence_id']} is not a superset: "
            f"{old['char_start']}–{old['char_end']} -> {new_start}–{new_end}. "
            "An anchor repair may only extend the span outward.")
    if (new_start, new_end) == (old["char_start"], old["char_end"]):
        raise SystemExit(f"repair to {old['evidence_id']} changes nothing")


def repair_spans(record: dict, decision: dict, sources: dict) -> list[dict]:
    """Rebuild the evidence list, recording each anchor revision."""
    spans = [dict(span) for span in record["expected_evidence"]]
    by_id = {span["evidence_id"]: span for span in spans}
    revisions: list[dict] = []

    for repair in decision.get("evidence_repairs", []):
        start, end = repair["new_char_start"], repair["new_char_end"]
        if repair.get("action") == "add_scope_span":
            version = repair["version_id"]
            source = sources[version]
            text = source["text"][start:end]
            added = {
                "evidence_id": repair["evidence_id"],
                "version_id": version,
                "section_path": _section_for(source["sections"], start),
                "char_start": start, "char_end": end,
                "evidence_text": text,
                "evidence_hash": sha(text),
                "evidence_char_length": end - start,
                "critical_strings": repair["critical_strings"],
            }
            spans.append(added)
            revisions.append({
                "evidence_id": repair["evidence_id"], "action": "add_scope_span",
                "new_char_start": start, "new_char_end": end,
                "new_evidence_text": text, "new_evidence_hash": added["evidence_hash"],
                "reason": repair["reason"],
            })
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
            "reason": repair["reason"],
        })
        old.update({
            "char_start": start, "char_end": end, "evidence_text": text,
            "evidence_hash": sha(text), "evidence_char_length": end - start,
            "section_path": _section_for(source["sections"], start),
        })

    spans.sort(key=lambda s: s["evidence_id"])
    for index, span in enumerate(spans, 1):
        span["evidence_id"] = f"E{index}"
    return spans, revisions


def apply_decision(record: dict, decision: dict, sources: dict) -> dict:
    """Produce the repaired record. The input record is not modified."""
    repaired = json.loads(json.dumps(record))
    spans, revisions = repair_spans(record, decision, sources)
    repaired["expected_evidence"] = spans

    if "critical_strings_by_span" in decision:
        # The mapping is keyed on the evidence ids as the decision file names them,
        # which are the ids before any scope span renumbered them.
        original_ids = [s["evidence_id"] for s in record["expected_evidence"]]
        for position, span in enumerate(spans):
            key = (original_ids[position] if position < len(original_ids)
                   else span["evidence_id"])
            if key in decision["critical_strings_by_span"]:
                span["critical_strings"] = decision["critical_strings_by_span"][key]
    elif "critical_strings" in decision and len(spans) == 1:
        spans[0]["critical_strings"] = decision["critical_strings"]

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Every field a review may rewrite. Each rewrite becomes a numbered revision that
    # keeps the generator's original text, so a reviewer can see what the review changed
    # and disagree with it.
    for field, key in (("question", "question"), ("answer", "answer"),
                       ("atomic_claims", "atomic_claims"),
                       ("reasoning_type", "reasoning_type"),
                       ("composed_claim", "composed_claim"),
                       ("composed_answer", "composed_answer"),
                       ("bridge_relationship", "bridge_relationship"),
                       ("why_span_1_alone_is_insufficient",
                        "why_span_1_alone_is_insufficient"),
                       ("why_span_2_alone_is_insufficient",
                        "why_span_2_alone_is_insufficient")):
        if key not in decision or decision[key] == repaired.get(field):
            continue
        repaired.setdefault("revisions", []).append({
            "revision": len(repaired.get("revisions", [])) + 1,
            "field": field, "from": repaired.get(field), "to": decision[key],
            "author": "claude (internal authoring review)", "timestamp": now,
            "reason": decision.get("reason") or "internal source-integrity review",
        })
        repaired[field] = decision[key]
        # ``proposed_*`` is what the downstream QC and decision tooling reads.
        if field in ("question", "answer", "atomic_claims"):
            repaired[f"proposed_{field.replace('atomic_claims', 'atomic_claims')}"] = \
                decision[key]

    repaired["proposed_question"] = repaired["question"]
    repaired["proposed_answer"] = repaired["answer"]
    repaired["proposed_atomic_claims"] = repaired["atomic_claims"]
    repaired["section_path"] = spans[0]["section_path"]
    repaired["critical_strings"] = [s for span in spans for s in span["critical_strings"]]
    repaired["evidence_char_length"] = sum(s["evidence_char_length"] for s in spans)
    shape = "single_span" if len(spans) == 1 else repaired["evidence_shape"]
    if len(spans) > 1 and repaired["evidence_shape"] == "single_span":
        shape = "multi_span"
    repaired["evidence_shape"] = shape
    repaired["requires_all_evidence"] = len(spans) > 1
    if revisions:
        repaired["anchor_revisions"] = revisions
    repaired["claim_evidence_map"] = remap_claims(repaired)
    return repaired


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


def precheck(record: dict) -> tuple[list[str], list[str]]:
    """The batch-004 precheck, re-run against the repaired record.

    Returns blocking failures and non-blocking flags separately. §2B: an unresolved
    *critical* anaphora blocks, while an incidental noncritical one is for a person to
    accept or refuse — so it is surfaced in the packet rather than swallowed here.
    """
    failures: list[str] = []
    flags: list[str] = []
    for span in record["expected_evidence"]:
        if sha(span["evidence_text"]) != span["evidence_hash"]:
            failures.append(f"{span['evidence_id']}: hash does not match its text")
        if not (0 <= span["char_start"] < span["char_end"]):
            failures.append(f"{span['evidence_id']}: invalid span")
        if not span["critical_strings"]:
            failures.append(f"{span['evidence_id']}: no critical strings")
        stray = [s for s in span["critical_strings"]
                 if not contains_claim_string(span["evidence_text"], s)]
        if stray:
            failures.append(f"{span['evidence_id']}: strings outside this span: {stray}")
        verdict = evaluate_span(span["evidence_text"], record)
        if verdict["status"] == CRITICAL:
            failures.append(
                f"{span['evidence_id']}: critical anaphora — {verdict['finding']}")
        elif verdict["status"] == NONCRITICAL:
            flags.append(f"{span['evidence_id']}: noncritical anaphora — "
                         f"{verdict['finding']}. {verdict['why']}")
        if span["evidence_char_length"] > EVIDENCE_SOFT_CAP:
            flags.append(f"{span['evidence_id']}: {span['evidence_char_length']} "
                         f"characters, over the {EVIDENCE_SOFT_CAP} soft cap")
        if span["evidence_char_length"] > EVIDENCE_HARD_CAP:
            failures.append(f"{span['evidence_id']}: over the evidence cap")
    if not (record["question"] and record["answer"] and record["atomic_claims"]):
        failures.append("question, answer or claims missing")
    if not record["retrieval_was_not_run"]:
        failures.append("retrieval leakage")
    return failures, flags


def render_review(payload: dict, decisions_doc: dict) -> str:
    counts = payload["status_counts"]
    review = decisions_doc["candidates"]
    repaired = {r["candidate_id"]: r for r in payload["records"]}
    semantic = decisions_doc["multi_hop_semantic_review"]

    rows = "\n".join(
        f"| `{cid}` | {d['status']} | {'yes' if cid in repaired else 'no'} | "
        f"{len(d['findings'])} |"
        for cid, d in sorted(review.items()))
    questions = "\n\n".join(
        f"**{q['id']}. {q['question']}**\n\n*{q['answer']}*\n\n{q['reasoning']}"
        for q in semantic["questions"])

    lines = [
        "# GOLD-001 — batch 004 internal source-integrity review",
        "",
        (f"**{sum(counts.values())} candidates reviewed against the frozen evidence · "
         f"{payload['repaired_candidates']} repaired · reviewed {payload['reviewed_at']}**"),
        "",
        ("This is an internal review by the authoring model. It is not human "
         "verification, not an independent second opinion, and it changes no "
         "candidate's status: all 15 remain `candidate_unverified`, and the confirmed "
         "holdout-eligible count is still 53 from batches 001–003."),
        "",
        "## Outcome",
        "",
        "| status | candidates |",
        "| --- | --- |",
        *(f"| {status} | {count} |"
          for status, count in sorted(counts.items(), key=lambda kv: -kv[1])),
        "",
        ("All 15 candidates were `precheck_holdout_ready` before this review, and all 15 "
         "still are. That is the point worth taking from the table: the structural "
         "precheck passed a candidate whose rule applies only on one experimental API "
         "surface, three questions broader than their evidence, four anchors whose scope "
         "lived in a section heading, and two critical strings that were 60-character "
         "truncations of a markdown link. A precheck cannot read."),
        "",
        "| candidate | status | repaired | findings |",
        "| --- | --- | --- | --- |",
        rows,
        "",
        "## The multi-hop case, reviewed semantically",
        "",
        semantic["note"],
        "",
        questions,
        "",
        f"**Verdict: {semantic['verdict']}.** Preserved: "
        + ", ".join(f"`{k}` = `{v}`" for k, v in semantic["labels_preserved"].items())
        + ".",
        "",
        "### What the mechanical check still cannot see",
        "",
        semantic["what_the_mechanical_check_still_cannot_see"],
        "",
        "## Findings by candidate",
        "",
    ]
    for candidate_id, decision in sorted(review.items()):
        lines += [f"### {candidate_id} — {decision['status']}", ""]
        if decision["findings"]:
            lines += [f"- {finding}" for finding in decision["findings"]]
        else:
            lines.append("- No finding.")
        if candidate_id in repaired:
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
                        f"{revision['new_char_start']}–{revision['new_char_end']} "
                        f"({revision['reason']}); hash "
                        f"`{revision['new_evidence_hash'][:12]}…`")
            for revision in record.get("revisions", []):
                lines.append(f"- `{revision['field']}` rewritten")
        lines.append("")

    lines += [
        "## What this review did not do",
        "",
        ("- It did not approve anything. `human_verified` requires an owner decision, "
         "and the decisions file ships with every decision `null`.\n"
         "- It did not rewrite the generation artifact. "
         "`gold_review_batch_004.json` is unchanged; repairs live in "
         "`gold_review_batch_004_repairs.json` with the original text and offsets "
         "preserved.\n"
         "- It did not regenerate the batch, add a candidate, or promote a near-miss "
         "bridge pair.\n"
         "- It did not run retrieval. SYSTEM-A and SYSTEM-B remain frozen and "
         "unexecuted, and the holdout is not frozen."),
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="evals/review/gold_review_batch_004_repairs.json")
    parser.add_argument("--report-dir", default="experiments/GOLD-001")
    args = parser.parse_args()

    batch = json.loads(BATCH.read_text())
    decisions = json.loads(DECISIONS.read_text())["candidates"]
    records = {r["candidate_id"]: r for r in batch["records"]}

    missing = sorted(set(records) - set(decisions))
    unknown = sorted(set(decisions) - set(records))
    if missing or unknown:
        raise SystemExit(
            f"review does not match the batch — unreviewed: {missing}, unknown: {unknown}")
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
                      ("evidence_repairs", "question", "answer", "atomic_claims",
                       "critical_strings", "critical_strings_by_span",
                       "reasoning_type", "composed_claim", "composed_answer",
                       "bridge_relationship", "why_span_1_alone_is_insufficient",
                       "why_span_2_alone_is_insufficient"))
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
        "batch": 4,
        "reviewed_at": now,
        "reviewer": "claude (internal authoring review)",
        "source_batch": str(BATCH),
        "source_batch_sha256": batch["batch_sha256"],
        "decisions_file": str(DECISIONS),
        "note": ("Repairs proposed by an internal review. The generation artifact is "
                 "unchanged. No candidate is verified, approved or eligible; an owner "
                 "accepts a repair by quoting its new evidence hash."),
        "status_counts": dict(Counter(d["status"] for d in decisions.values())),
        "repaired_candidates": len(repaired),
        "retrieval_was_not_run": True,
        "systems_executed": [],
        "records": [repaired[cid] for cid in sorted(repaired)],
        "review": decisions,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")

    decisions_doc = json.loads(DECISIONS.read_text())
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "GOLD-001-batch-004-internal-review.md").write_text(
        render_review(payload, decisions_doc), encoding="utf-8")
    (report_dir / "GOLD-001-batch-004-internal-review.json").write_text(
        json.dumps({
            "batch": 4,
            "reviewed_at": payload["reviewed_at"],
            "reviewer": payload["reviewer"],
            "status_counts": payload["status_counts"],
            "repaired_candidates": payload["repaired_candidates"],
            "human_verified": 0,
            "holdout_eligible": 0,
            "precheck_holdout_ready_before_review": 15,
            "precheck_holdout_ready_after_repairs": sum(
                1 for r in payload["records"] if r["precheck_holdout_ready"]),
            "multi_hop_semantic_review": decisions_doc["multi_hop_semantic_review"],
            "candidates": decisions_doc["candidates"],
            "retrieval_was_not_run": True,
            "systems_executed": [],
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

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
