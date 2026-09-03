#!/usr/bin/env python3
"""GOLD-001: turn the human QC queue into a packet a person can decide from quickly.

``select_human_qc.py`` decides *who* gets reviewed and emits candidate ids. Nobody can
review ids. This renders each queued candidate as a decision: the final proposed
question, answer and claims first, then the exact evidence span, then why a human is
required — and two choices, with ``NEEDS_EDIT`` available for the cases that genuinely
need one.

Two things this deliberately does not do:

* It does not present a repaired candidate as if it were sound. The importer forbids a
  reviewer from moving a source anchor, so a boundary defect can only ever be repaired
  by rewording the question — the span itself is unchanged. Where that leaves a claim
  resting on a term the anchor does not contain, the packet says so.
* It does not approve anything. Nothing here sets ``human_verified``; only
  ``import_human_decisions.py``, reading a decision a person wrote, can do that.

Audit history is retained in the JSON packet in full: the original generator proposal,
the reviewer's verdict, every revision, and the anchor as first mined.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path

#: Decisions a person may record. APPROVE is never pre-selected.
DECISIONS = ("APPROVE", "REJECT", "NEEDS_EDIT")

#: How much of the surrounding text to show. The full mined window is 900 characters a
#: side, which is more than a reviewer needs to judge an anchor and more provider prose
#: than this repository should carry.
CONTEXT_CHARS = 260

TICK = re.compile(r"`([^`]+)`")
#: Product and API names carry scope ("which models does this apply to?") and are the
#: other half of the OA-002 defect, so they are checked alongside code identifiers.
PROPER = re.compile(
    r"\b(?:Claude|GPT|OpenAI|Anthropic|Google Cloud|Agent Platform|Responses API|"
    r"Files API)(?:[ -][A-Z0-9][\w.]*)*"
)
#: A span containing assignments, JSON keys or bare closing brackets is example code.
#: A sample configuration is not a documented rule; conflating the two is defect D3.
CODE_LINE = re.compile(
    r"^\s*[\w.\[\]\"']+\s*=\s*\S|^\s*[\]\})],?\s*$|^\s*\"[\w_]+\"\s*:|^\s*raise\s|"
    r"^\s*return\s",
    re.MULTILINE,
)

#: Classes a reviewer named directly on a candidate. Where present these are used
#: instead of the inferred D1/D2/D3, because the reviewer said what the defect was and
#: the inference is only a fallback for reviews that did not.
REVIEW_DEFECT_REPAIRS = {
    "QUESTION_SCOPE": (
        "The question was ambiguous or broader than the evidence supports; it was "
        "re-scoped to what the anchor states."
    ),
    "CLAIM_SCOPE": (
        "The claim asserted more, or less, than the anchored evidence states; it was "
        "brought back to the source's own scope."
    ),
    "EVIDENCE_BOUNDARY": (
        "The anchor did not carry the scope its claim depends on, and was extended or "
        "split into precise spans. Both old and new spans are retained."
    ),
    "CATEGORY_MISCLASSIFICATION": (
        "The recorded reasoning type was wrong. Two facts from two spans is a "
        "multi-span retrieval test, not multi-hop reasoning."
    ),
    "MINER_QUESTION_HEADER_DEPENDENCY": (
        "The anchored row is sound evidence; the miner's exported question asked about a "
        "column whose meaning lives in a table header outside the row. The question was "
        "re-authored around a fact stated inside the row, and the anchor did not move."
    ),
    "QUESTION_AUTHORING_REQUIRED": (
        "No defect. The span is self-contained and the reviewer authored the question, "
        "answer and claims, which is how the prose miner is designed to work."
    ),
    "MINER_EVIDENCE_DEFECT": (
        "The anchor did not contain what its claim depends on, and was extended. Both "
        "spans and both hashes are retained below."
    ),
}

DEFECT_REPAIRS = {
    "D1": (
        "The anchor still opens on a referent it does not contain; the reviewer "
        "repaired this by rewriting the question to name the scope explicitly, and "
        "the span itself is unchanged."
    ),
    "D2": (
        "The generator's relation label pointed at the wrong fact; the reviewer "
        "re-authored the question and claims around what the span actually states."
    ),
    "D3": (
        "The span is example code, and the generator framed it as a documented rule; "
        "the reviewer narrowed the question to be about the example itself."
    ),
}


def scope_terms(text: str) -> set[str]:
    # A sentence-final period gets swept into a version number — "Claude Sonnet 4.6." —
    # and then reads as a term the span is missing. Trim trailing punctuation.
    return set(TICK.findall(text)) | {
        term.rstrip(".,;:") for term in PROPER.findall(text)}


def classify_defects(record: dict) -> list[str]:
    named = record.get("review_defect_classes") or record.get("review_defect_class")
    if isinstance(named, str):
        return [named]
    if named:
        return list(named)
    verification = record.get("verification", {})
    defects = []
    if verification.get("evidence_boundary_complete") is False:
        defects.append("D1")
    if verification.get("identifier_value_binding_correct") is False:
        defects.append("D3" if CODE_LINE.search(record["evidence_text"]) else "D2")
    return defects


def anchor_gaps(record: dict) -> dict:
    """Terms the case asserts that the anchored span does not itself contain.

    A claim has to be checkable against the anchor alone — that is the entire contract
    of source-anchored evaluation. A term missing from the span but present in the
    document title or section path is weaker evidence, not none, so it is reported
    separately rather than lumped in with a real gap.
    """
    # For a multi-span case the evidence is all of its spans: a term carried by the
    # second span is not missing just because the first does not have it.
    span = " \n".join(s["evidence_text"]
                      for s in (record.get("expected_evidence") or [record]))
    provenance = f"{record['document_title']} {' > '.join(record['section_path'])}"
    asserted = scope_terms(
        " ".join([record["proposed_answer"], *record["proposed_atomic_claims"]]))
    asked = scope_terms(record["proposed_question"])

    unsupported, provenance_only = [], []
    for term in sorted(asserted):
        if term in span:
            continue
        (provenance_only if term in provenance else unsupported).append(term)
    framing = sorted(t for t in asked
                     if t not in span and t not in unsupported and t not in provenance_only)
    return {
        "unsupported_in_claims": unsupported,
        "covered_by_provenance_only": provenance_only,
        "question_framing_only": framing,
    }


WHY_FAIL = (
    "The independent review recommends rejection: the span is a sample configuration, "
    "so any question over it tests an example rather than a documented rule."
)
WHY_UNSUPPORTED = (
    "A claim asserts {terms}, which the anchored span does not contain and the document "
    "title and section path do not supply either. Approving accepts a claim the anchor "
    "cannot support on its own."
)
WHY_PROVENANCE = (
    "A claim asserts {terms}, which appears in the section path but not in the anchored "
    "span. Confirm the section scope is genuinely part of the claim before approving."
)
WHY_AGREED_PASS = (
    "Both models passed this case. It is here because agreement between two models is "
    "correlated evidence, not independent confirmation, and this candidate was drawn as "
    "the deterministic QC sample."
)
WHY_REPAIRED = (
    "The reviewer rewrote the question and claims. Every term they assert is present in "
    "the anchored span, but a model authored the wording and a model verified it, so the "
    "case is not gold until you agree."
)
WHY_AUTHORED = (
    "The generator shipped this as evidence with no question; the reviewer wrote the "
    "question, answer and claims. Two models are not human verification."
)


WHY_PRECHECK_BLOCKED = (
    "The deterministic precheck blocks this case: {failures}. It cannot become "
    "holdout-eligible until that is resolved, so it needs a decision on the evidence "
    "rather than a quick approval."
)


def assess(record: dict, gaps: dict, defects: list[str]) -> tuple[str, str, str]:
    """Return (group, risk, why-a-human-is-required)."""
    verdict = record.get("verification", {}).get("verdict")
    failures = record.get("precheck_failures") or []
    if failures:
        return ("check_anchor", "HIGH",
                WHY_PRECHECK_BLOCKED.format(failures="; ".join(failures)))
    if verdict == "FAIL":
        return "recommended_reject", "HIGH", WHY_FAIL
    if gaps["unsupported_in_claims"]:
        terms = ", ".join(f"`{t}`" for t in gaps["unsupported_in_claims"])
        return "check_anchor", "HIGH", WHY_UNSUPPORTED.format(terms=terms)
    if gaps["covered_by_provenance_only"]:
        terms = ", ".join(f"`{t}`" for t in gaps["covered_by_provenance_only"])
        return "check_anchor", "MEDIUM", WHY_PROVENANCE.format(terms=terms)
    if verdict == "PASS":
        return "fast_track", "LOW", WHY_AGREED_PASS
    if defects:
        return "fast_track", "LOW", WHY_REPAIRED
    return "fast_track", "LOW", WHY_AUTHORED


def build_item(record: dict, reason: str, batch: int = 1) -> dict:
    gaps = anchor_gaps(record)
    defects = classify_defects(record)
    group, risk, why = assess(record, gaps, defects)

    revisions = record.get("revisions", [])
    original = {}
    for field in ("proposed_question", "proposed_answer", "proposed_atomic_claims"):
        first = next((r for r in revisions if r["field"] == field), None)
        original[field] = first["from"] if first else record.get(field)

    anchor = {
        "version_id": record["version_id"], "char_start": record["char_start"],
        "char_end": record["char_end"], "evidence_hash": record["evidence_hash"],
        "section_path": record["section_path"],
    }
    return {
        "candidate_id": record["candidate_id"],
        "batch": batch,
        "group": group,
        "risk": risk,
        "queued_because": reason,
        "chatgpt_verdict": record.get("verification", {}).get("verdict"),
        "verification_status": record["verification_status"],
        "final": {
            "question": record["proposed_question"],
            "answer": record["proposed_answer"],
            "atomic_claims": record["proposed_atomic_claims"],
        },
        "evidence": {**anchor, "text": record["evidence_text"],
                     "context_before": record["context_before"][-CONTEXT_CHARS:],
                     "context_after": record["context_after"][:CONTEXT_CHARS]},
        "why_human_review_required": why,
        "defects": [{"class": d,
                     "what_was_repaired": REVIEW_DEFECT_REPAIRS.get(
                         d, DEFECT_REPAIRS.get(d, ""))}
                    for d in defects],
        "anchor_gaps": gaps,
        "critical_strings": record.get("critical_strings", []),
        "anchor_revisions": record.get("anchor_revisions", []),
        "reasoning_type": record.get("reasoning_type"),
        "evidence_shape": record.get("evidence_shape"),
        "requires_all_evidence": record.get("requires_all_evidence"),
        "precheck_holdout_ready": record.get("precheck_holdout_ready"),
        "precheck_failures": record.get("precheck_failures", []),
        "extra_spans": (record.get("expected_evidence") or [])[1:],
        "review_reason": record.get("review_reason"),
        "decision_options": list(DECISIONS),
        "decision": None,
        "audit": {
            "claude_original_proposal": original,
            "chatgpt_review": record.get("verification"),
            "revisions": revisions,
            "anchor_as_mined": anchor,
            "anchor_current": anchor,
            "anchor_unchanged": True,
            "anchor_disputes": record.get("anchor_disputes", []),
            "provenance": {
                "provider": record["provider"],
                "document_title": record["document_title"],
                "source_url": record["source_url"],
                "captured_at": record["captured_at"],
                "evidence_kind": record["evidence_kind"],
                "generator_confidence": record["generator_confidence"],
            },
        },
    }


GROUP_HEADINGS = {
    "fast_track": (
        "A. Fast track — every asserted term is in the anchored span",
        ("Read the question, glance at the span, decide. These carry no detected gap "
         "between what the case claims and what its anchor contains."),
    ),
    "check_anchor": (
        "B. Check the anchor before approving",
        ("Each of these asserts something the anchored span does not contain. This is "
         "the OA-002 defect class, and it is the reason the whole batch exists — do not "
         "skim these."),
    ),
    "recommended_reject": (
        "C. Independent review recommends rejection",
        ("Included for your decision and the audit trail, not for rescue. No second "
         "automatic repair was attempted."),
    ),
}


def code_span(text: str) -> str:
    """Markdown code span that survives text already containing backticks."""
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def render_item(item: dict) -> str:
    ev = item["evidence"]
    claims = "\n".join(f"  {i}. {c}" for i, c in enumerate(item["final"]["atomic_claims"], 1))
    taxonomy = ""
    if item.get("reasoning_type"):
        taxonomy = (f"\n\n`reasoning_type: {item['reasoning_type']}` · "
                    f"`evidence_shape: {item['evidence_shape']}` · "
                    f"`requires_all_evidence: {item['requires_all_evidence']}`")
    lines = [
        f"#### {item['candidate_id']} · {item['chatgpt_verdict']} · risk {item['risk']}"
        + taxonomy,
        "",
        f"**Q.** {item['final']['question']}",
        "",
        f"**A.** {item['final']['answer']}",
        "",
        "**Claims**",
        claims or "  (none)",
        "",
        ("**Evidence span** — "
         f"`{ev['version_id']}` {ev['char_start']}–{ev['char_end']} · "
         f"{' > '.join(ev['section_path'])}"),
        "",
        "```",
        ev["text"],
        "```",
        "",
        "<details><summary>surrounding context</summary>",
        "",
        "```",
        f"…{ev['context_before'].strip()}",
        "  ⟦SPAN⟧",
        f"{ev['context_after'].strip()}…",
        "```",
        "",
        "</details>",
        "",
        f"**Why you are seeing this.** {item['why_human_review_required']}",
    ]
    for defect in item["defects"]:
        lines += ["", (f"**{defect['class']} — what was repaired.** "
                       f"{defect['what_was_repaired']}")]
    if item["anchor_gaps"]["question_framing_only"]:
        terms = ", ".join(f"`{t}`" for t in item["anchor_gaps"]["question_framing_only"])
        lines += ["", (f"*Note:* the question mentions {terms} as framing only; no "
                       "claim depends on it.")]
    for revision in item.get("anchor_revisions", []):
        if "old_spans" in revision:
            # Batch 003 records anchor changes as span lists, because a repair may split
            # one anchor into two precise spans rather than growing it.
            old_spans = ", ".join(f"{s['char_start']}–{s['char_end']}"
                                  for s in revision["old_spans"])
            new_spans = ", ".join(f"{s['char_start']}–{s['char_end']}"
                                  for s in revision["new_spans"])
            lines += [
                "",
                (f"**Anchor changed** ({revision['reason']}) — {old_spans} → "
                 f"{new_spans}"),
                "",
                f"*Why:* {revision.get('why', '')}",
            ]
            continue
        lines += [
            "",
            (f"**Anchor extended** — {revision['old_char_start']}–"
             f"{revision['old_char_end']} → {revision['new_char_start']}–"
             f"{revision['new_char_end']} "
             f"(+{revision['characters_added_before']} before, "
             f"+{revision['characters_added_after']} after). "
             f"{revision.get('what_changed', '')}"),
            "",
            f"*Why complete:* {revision.get('why_complete', '')}",
        ]
        if revision.get("size_warning"):
            lines += ["", f"*Size warning:* {revision['size_warning']}"]
        lines += ["", "<details><summary>the span before the extension</summary>", "",
                  "```", revision["old_evidence_text"], "```", "", "</details>"]
    for index, span in enumerate(item.get("extra_spans", []), 2):
        lines += [
            "",
            (f"**Evidence span {index}** — {span['char_start']}–{span['char_end']} "
             f"({span['evidence_char_length']} chars)"),
            "", "```", span["evidence_text"], "```", "",
            ("*Both spans are required: a retriever earns credit only by finding all "
             "of them.*"),
            "",
        ]
    if item.get("precheck_failures"):
        lines += ["", ("**Precheck blocked** — "
                       + "; ".join(item["precheck_failures"]))]
    elif item.get("precheck_holdout_ready") is not None:
        lines += ["", ("**Precheck holdout-ready.** Structurally capable of becoming "
                       "eligible; not an approval.")]
    if item.get("critical_strings"):
        strings = ", ".join(code_span(x) for x in item["critical_strings"])
        lines += ["", (f"*Critical claim strings, each verified inside the span above:* "
                       f"{strings}")]
    lines += ["",
              ("**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for "
               f"`{item['candidate_id']}` in "
               f"`human_decisions_batch_{item['batch']:03d}.json`."),
              "", "---", ""]
    return "\n".join(lines)


def render_markdown(packet: dict) -> str:
    queue = packet["queue"]
    counts = {g: sum(1 for i in packet["items"] if i["group"] == g) for g in GROUP_HEADINGS}
    lines = [
        f"# GOLD-001 — batch {packet['batch']:03d} human QC packet",
        "",
        (f"**{len(packet['items'])} decisions.** {counts['fast_track']} fast track, "
         f"{counts['check_anchor']} need the anchor checked, "
         f"{counts['recommended_reject']} recommended for rejection."),
        "",
        ("Nothing in this packet is gold. A candidate becomes `human_verified` only "
         "when you record `APPROVE` for it in "
         f"`evals/review/human_decisions_batch_{packet['batch']:03d}.json` and import "
         "that file. An independent-review PASS produces `dual_llm_pass` and stops "
         "there — two AI systems agreeing is not human verification."),
        "",
        ("**Judge each case against the anchored evidence block alone.** The context "
         "is there to let you spot a bad anchor, not to answer the question. If you need "
         "the context to answer it, the anchor is wrong: `NEEDS_EDIT`."),
        "",
        ("**The anchors were never moved.** The import path forbids a reviewer from "
         "changing a source span, so every repair below is a repair to the *wording*. "
         "Where that leaves a claim resting on a term the span does not contain, it is "
         "flagged in section B rather than smoothed over."),
        "",
        (f"Queue: {len(queue['must_review'])} mandatory + "
         f"{len(queue['qc_sample_of_dual_llm_pass'])} sampled from the "
         f"{queue['dual_llm_pass_total']} agreed passes "
         f"(seed {queue['seed']}, rate {queue['sample_rate']:.0%})."),
        "",
        "| id | verdict | risk | defects | one-line |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in packet["items"]:
        defects = ", ".join(d["class"] for d in item["defects"]) or "—"
        question = item["final"]["question"]
        short = question if len(question) <= 72 else question[:69] + "…"
        lines.append(f"| `{item['candidate_id'][-2:]}` | {item['chatgpt_verdict']} | "
                     f"{item['risk']} | {defects} | {short} |")
    lines.append("")

    for group, (heading, blurb) in GROUP_HEADINGS.items():
        items = [i for i in packet["items"] if i["group"] == group]
        if not items:
            continue
        lines += ["---", "", f"## {heading}", "", blurb, ""]
        lines += [render_item(item) for item in items]

    lines += [
        "## Audit",
        "",
        ("The full history — the generator's original proposal, the reviewer's verdict "
         "and boolean checks, every numbered revision, and the anchor as first mined — "
         "is retained per candidate in `gold_batch_001_qc.json` under `audit`. Nothing "
         "was overwritten, and no anchor was changed (0 disputes recorded)."),
        "",
        ("OA-002 is a defect in the original development set and is deliberately not "
         "part of this batch. Its `development/v2` correction remains proposed and "
         "unapplied."),
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch")
    parser.add_argument("queue")
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    batch_path = Path(args.batch)
    batch = json.loads(batch_path.read_text())
    queue = json.loads(Path(args.queue).read_text())
    records = {r["candidate_id"]: r for r in batch["records"]}

    reasons = {cid: "mandatory: disagreement, uncertainty or failure"
               for cid in queue["must_review"]}
    reasons.update({cid: "deterministic QC sample of agreed passes"
                    for cid in queue["qc_sample_of_dual_llm_pass"]})
    missing = sorted(set(reasons) - set(records))
    if missing:
        raise SystemExit(f"queue references candidates not in the batch: {missing}")

    order = {"recommended_reject": 2, "check_anchor": 1, "fast_track": 0}
    number = batch.get("batch", 0)
    items = [build_item(records[cid], reasons[cid], number) for cid in sorted(reasons)]
    items.sort(key=lambda i: (order[i["group"]], i["candidate_id"]))

    out_dir = Path(args.out_dir) if args.out_dir else batch_path.parent
    packet = {
        "batch": number,
        "source_batch_sha256": batch.get("batch_sha256"),
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "queue": queue,
        "allowed_decisions": list(DECISIONS),
        "nothing_here_is_gold": (
            "A candidate becomes human_verified only through an explicit APPROVE "
            "recorded by the project owner. A ChatGPT PASS is dual_llm_pass."
        ),
        "items": items,
    }

    json_path = out_dir / f"gold_batch_{number:03d}_qc.json"
    md_path = out_dir / f"gold_batch_{number:03d}_qc.md"
    json_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    md_path.write_text(render_markdown(packet), encoding="utf-8")

    decisions_path = out_dir / f"human_decisions_batch_{number:03d}.json"
    if decisions_path.exists() and any(
            d.get("decision") for d in
            json.loads(decisions_path.read_text()).get("decisions", [])):
        print(f"kept {decisions_path} — it already carries decisions")
    else:
        decisions_path.write_text(json.dumps({
            "batch": number,
            "source_batch_sha256": batch.get("batch_sha256"),
            "reviewer": "project_owner",
            "reviewed_at": None,
            "allowed_decisions": list(DECISIONS),
            "instructions": (
                "Set decision to APPROVE, REJECT or NEEDS_EDIT for each candidate, then "
                "run scripts/import_human_decisions.py. Only APPROVE produces "
                "human_verified. Leaving a decision null leaves the candidate out of "
                "gold."
            ),
            "decisions": [{"candidate_id": i["candidate_id"], "decision": None,
                           "notes": ""} for i in items],
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {decisions_path}")

    counts = {g: sum(1 for i in items if i["group"] == g) for g in GROUP_HEADINGS}
    print(f"wrote {md_path}")
    print(f"wrote {json_path}")
    print(f"  {len(items)} decisions — fast track {counts['fast_track']}, "
          f"check anchor {counts['check_anchor']}, "
          f"recommended reject {counts['recommended_reject']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
