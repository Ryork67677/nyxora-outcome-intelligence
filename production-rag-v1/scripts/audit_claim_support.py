#!/usr/bin/env python3
"""GOLD-001: audit whether a closed batch's approved claims are actually checkable.

Batch 001 closed with a passing validator run, and its own closure artifact says why
that is not enough: the claim-in-evidence gate only fires on claims marked *critical*,
and only 3 of the 16 approved cases carry any. For the other 13 the pass was silent
about the thing that matters most.

This audits them without touching them. The closed batch is read-only here — no record
is modified, no closure hash is recomputed — and the findings land in a separate overlay
keyed by candidate id and approved evidence hash, so a reader can always tell which
version of a case was audited.

**What this can and cannot establish.** It is a mechanical screen, not a semantic proof.
It checks whether the terms a claim turns on — code identifiers, numbers, quoted values,
product names — appear inside the approved span, and how much of the claim's content
vocabulary the span carries. A claim can pass every check here and still be a bad
paraphrase, and a claim can fail one and still be true. That is why the outcome for
anything short of clean is NEEDS_REVIEW, addressed to a person, rather than a verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.gold.eligibility import evaluate
from rag_v1.gold.mining import anaphora_problem
from rag_v1.gold.normalisation import (
    contains_claim_string,
    normalise_for_comparison,
)

#: Below this, a claim's vocabulary is worth a second look — but only where no critical
#: string checks the claim already. See ``audit_claim``.
COVERAGE_THRESHOLD = 0.6
#: Bumped when the audit's rules change, so two audits are never silently compared.
AUDIT_RULE_VERSION = 2

SUPPORTED = "SUPPORTED"
NEEDS_REVIEW = "NEEDS_REVIEW"
UNSUPPORTED = "UNSUPPORTED"

TICK = re.compile(r"`([^`]+)`")
NUMBER = re.compile(r"\b\d[\d,._]*\b")
PROPER = re.compile(
    r"\b(?:Claude|GPT|OpenAI|Anthropic|Google Cloud|Agent Platform|Responses API|"
    r"Files API)(?:[ -][A-Z0-9][\w.]*)*"
)
#: Words that carry no checkable content, so their absence from a span means nothing.
STOPWORDS = frozenset((
    "a", "all", "also", "an", "and", "any", "are", "as", "at", "be", "been", "but",
    "by", "can", "cannot", "could", "do", "does", "each", "every", "for", "from",
    "has", "have", "if", "in", "into", "is", "it", "its", "may", "must", "no", "not",
    "of", "on", "one", "only", "or", "other", "per", "same", "set", "should", "so",
    "such", "than", "that", "the", "their", "them", "then", "there", "these", "this",
    "those", "to", "use", "used", "uses", "using", "was", "were", "what", "when",
    "where", "which", "who", "will", "with", "would", "yes", "you", "your",
))


def terms(text: str) -> set[str]:
    return set(TICK.findall(text)) | set(NUMBER.findall(text)) | set(PROPER.findall(text))


#: Suffixes stripped before comparing vocabulary. "Setting … restarts" and "Set … to
#: restart" are the same words; counting them as different made five well-supported
#: batch-002 claims look like paraphrases.
_SUFFIXES = ("ing", "ed", "es", "s")


def stem(word: str) -> str:
    for suffix in _SUFFIXES:
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def content_words(text: str) -> set[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_.-]{2,}", text.lower())
    return {stem(w) for w in words if w not in STOPWORDS}


def audit_claim(claim: str, span: str, provenance: str,
                has_deterministic_check: bool = False) -> dict:
    missing, provenance_only = [], []
    for term in sorted(terms(claim)):
        if contains_claim_string(span, term):
            continue
        (provenance_only if contains_claim_string(provenance, term)
         else missing).append(term)

    words = content_words(claim)
    span_words = content_words(normalise_for_comparison(span))
    covered = words & span_words
    coverage = len(covered) / len(words) if words else 1.0

    if missing:
        status = UNSUPPORTED
        reason = ("the claim asserts " + ", ".join(f"`{t}`" for t in missing) +
                  ", which the approved span does not contain")
    elif provenance_only:
        status = NEEDS_REVIEW
        reason = ("the claim asserts " + ", ".join(f"`{t}`" for t in provenance_only) +
                  ", which appears in the document title or section path but not in the "
                  "span itself")
    elif coverage < COVERAGE_THRESHOLD and not has_deterministic_check:
        # Blocking only where nothing else checks the claim. Coverage is a proxy for
        # "is this a paraphrase the span does not carry", and it is a poor one: a claim
        # naming its own subject ("the routine-trigger `text` field") scores low while
        # asserting nothing the span lacks.
        status = NEEDS_REVIEW
        reason = (f"only {coverage:.0%} of the claim's content words appear in the span, "
                  "and the case carries no critical strings, so nothing else checks it")
    elif coverage < COVERAGE_THRESHOLD:
        status = SUPPORTED
        reason = (f"every asserted term is inside the span; content-word coverage is "
                  f"{coverage:.0%}, which is advisory here because the case's critical "
                  "strings provide the deterministic check")
    else:
        status = SUPPORTED
        reason = (f"every asserted term is inside the span and {coverage:.0%} of the "
                  "claim's content words appear there")
    return {
        "claim": claim, "status": status, "reason": reason,
        "terms_missing_from_span": missing,
        "terms_only_in_provenance": provenance_only,
        "content_word_coverage": round(coverage, 3),
        "content_words_absent": sorted(words - span_words),
    }


def audit_case(record: dict) -> dict:
    span = record["evidence_text"]
    provenance = f"{record['document_title']} {' > '.join(record['section_path'])}"
    strings = record.get("critical_strings", [])
    claims = [audit_claim(c, span, provenance, has_deterministic_check=bool(strings))
              for c in record["proposed_atomic_claims"]]
    statuses = {c["status"] for c in claims}
    if UNSUPPORTED in statuses:
        overall = UNSUPPORTED
    elif NEEDS_REVIEW in statuses or not claims:
        overall = NEEDS_REVIEW
    else:
        overall = SUPPORTED

    history = record.get("human_decision_history", [{}])[-1]
    outside = [s for s in strings if not contains_claim_string(span, s)]
    # Two different questions, and only the first can block eligibility:
    #
    #   * does a *claim* depend on something the span does not contain?  (scope gap)
    #   * does the span contain anaphoric phrasing anywhere?             (advisory)
    #
    # Treating the second as a defect misreads three v2 cases. GOLD-B001-03's span says
    # "The model determines…" with the two models named in its own first line, just as
    # identifiers rather than the word "model"; GOLD-B001-05's "the model's context
    # window" is generic and its span says "on every model"; GOLD-B001-12's span opens on
    # an unrelated sentence its claim never uses. None of their claims rest on an
    # unresolved reference, so the phrasing is recorded as an advisory rather than
    # failing a case whose claims are fully anchored.
    anaphoric = anaphora_problem(span) if record.get(
        "evidence_kind") != "parameter_table_row" else None
    scope_gaps = [t for c in claims for t in c["terms_missing_from_span"]]
    verdict = evaluate({**record, "unresolved_scope_defect":
                        f"claim asserts {scope_gaps}" if scope_gaps else None})
    return {
        "candidate_id": record["candidate_id"],
        "status": overall,
        "human_verified": record.get("human_verified", False),
        "approved_revision": len(record.get("anchor_revisions", [])),
        "atomic_claims": record["proposed_atomic_claims"],
        "critical_strings": strings,
        "critical_string_count": len(strings),
        "each_critical_string_present_in_raw_evidence": not outside,
        "critical_strings_outside_evidence": outside,
        "all_atomic_claims_have_deterministic_check": bool(claims) and bool(strings),
        "evidence_hash_valid": (
            hashlib.sha256(span.encode("utf-8")).hexdigest() == record["evidence_hash"]),
        "scope_self_contained": not scope_gaps,
        # A boundary defect is a claim resting on something outside its span. Anaphoric
        # phrasing no claim depends on is reported separately, not as a defect.
        "boundary_defect": bool(scope_gaps),
        "boundary_defect_detail": (f"claims assert {scope_gaps}, absent from the span"
                                   if scope_gaps else None),
        "anaphoric_span_advisory": anaphoric,
        "holdout_eligible_verdict": verdict,
        "notes": (
            "Comparison uses documented Markdown-escape normalisation only; the stored "
            "evidence and its hash are the raw source form."
        ),
        "approved_evidence_hash": record["evidence_hash"],
        "approved_evidence_hash_recomputes": (
            hashlib.sha256(span.encode("utf-8")).hexdigest() == record["evidence_hash"]),
        "approval_pinned_hash": history.get("approved_evidence_hash"),
        "approved_question": record["proposed_question"],
        "approved_answer": record["proposed_answer"],
        "approved_atomic_claims": record["proposed_atomic_claims"],
        "has_critical_strings": bool(strings),
        "evidence_boundary_dependency": [
            t for c in claims for t in c["terms_missing_from_span"] +
            c["terms_only_in_provenance"]],
        "claims": claims,
        "holdout_eligible": overall == SUPPORTED and verdict["holdout_eligible"],
    }


def proposed_v2(cases: list[dict]) -> dict:
    """What a v2 promotion would have to fix, proposed and deliberately not applied."""
    needs = [c for c in cases if c["status"] != SUPPORTED]
    no_criticals = [c for c in cases if c["status"] == SUPPORTED
                    and not c["has_critical_strings"]]
    return {
        "status": "PROPOSED — not applied, and no batch 001 record was modified",
        "requires": "explicit project-owner approval before anything is written",
        "cases_needing_claim_repair": [{
            "candidate_id": c["candidate_id"],
            "status": c["status"],
            "why": [claim["reason"] for claim in c["claims"]
                    if claim["status"] != SUPPORTED],
        } for c in needs],
        "cases_needing_critical_strings_only": [c["candidate_id"] for c in no_criticals],
        "note": (
            "A case in the second list is not wrong — its claims are traceable to its "
            "span. It simply carries no literal critical string, so the validator "
            "cannot check it, and a holdout built from it would be gated on nothing."
        ),
    }


def render(overlay: dict) -> str:
    counts = overlay["status_counts"]
    rows = "\n".join(
        f"| `{c['candidate_id']}` | {c['status']} | "
        f"{'yes' if c['has_critical_strings'] else 'no'} | "
        f"{min((claim['content_word_coverage'] for claim in c['claims']), default=1):.0%} | "
        f"{'**yes**' if c['holdout_eligible'] else 'no'} |"
        for c in overlay["cases"])
    detail = []
    for case in overlay["cases"]:
        if case["status"] == SUPPORTED and case["has_critical_strings"]:
            continue
        detail += [f"### {case['candidate_id']} — {case['status']}", ""]
        for claim in case["claims"]:
            detail += [f"- *{claim['status']}* — {claim['claim']}", f"  - {claim['reason']}"]
        if not case["has_critical_strings"]:
            detail += [("- no critical claim strings, so `validate_golden.py` does not "
                        "check this case's claims at all")]
        detail += [""]

    return "\n".join([
        f"# GOLD-001 — batch {overlay['batch']:03d} claim-support audit",
        "",
        ("An overlay, not an edit. No batch 001 record was modified, no closure hash was "
         f"recomputed, and the closed batch still hashes to "
         f"`{overlay['closure_sha256'][:16]}…`."),
        "",
        (f"**{counts.get(SUPPORTED, 0)} SUPPORTED · {counts.get(NEEDS_REVIEW, 0)} "
         f"NEEDS_REVIEW · {counts.get(UNSUPPORTED, 0)} UNSUPPORTED** across "
         f"{overlay['cases_audited']} approved cases and "
         f"{overlay['claims_audited']} atomic claims."),
        "",
        (f"**{overlay['holdout_eligible_count']} of {overlay['cases_audited']} are "
         "holdout-eligible today** — meaning their claims trace to their own span *and* "
         "they carry literal critical strings the validator can check. That second "
         "condition is what the closure artifact flagged, and it is the binding one."),
        "",
        "## Method, and what it cannot tell you",
        "",
        ("This is a mechanical screen. For each approved claim it checks that every term "
         "the claim turns on — code identifiers, numbers, quoted values, product names — "
         "appears inside the approved span, and measures how much of the claim's content "
         "vocabulary the span carries."),
        "",
        ("A claim can pass every check here and still be a bad paraphrase; a claim can "
         "fail one and still be true. Nothing short of clean is called a verdict — it is "
         "called NEEDS_REVIEW and addressed to a person. Retrieval was not run."),
        "",
        "## Results",
        "",
        "| candidate | status | critical strings | min claim coverage | holdout-eligible |",
        "| --- | --- | --- | --- | --- |",
        rows,
        "",
        "## Cases that are not clean",
        "",
        *detail,
        "## Proposed v2 promotion",
        "",
        ("`" + overlay["proposed_v2"]["status"] + "`. It is returned for explicit "
         "approval and has not been written anywhere."),
        "",
        f"- claim repair needed: {len(overlay['proposed_v2']['cases_needing_claim_repair'])}",
        (f"- critical strings needed (claims otherwise fine): "
         f"{len(overlay['proposed_v2']['cases_needing_critical_strings_only'])}"),
        "",
        overlay["proposed_v2"]["note"],
        "",
        "## Holdout",
        "",
        ("Not frozen, and this audit does not unblock it. SYSTEM-A and SYSTEM-B remain "
         "frozen and unexecuted."),
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch")
    parser.add_argument("--out-dir", default="experiments/GOLD-001")
    args = parser.parse_args()

    batch = json.loads(Path(args.batch).read_text())
    approved = [r for r in batch["records"]
                if r.get("verification_status") == "human_verified"]
    if not approved:
        raise SystemExit("no human_verified cases to audit")

    cases = [audit_case(r) for r in sorted(approved, key=lambda r: r["candidate_id"])]
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    overlay = {
        "batch": batch.get("batch"),
        "audited_at": now,
        "auditor": "claude",
        "audit_rule_version": AUDIT_RULE_VERSION,
        "rule_change": (
            "Version 2: content-word coverage is blocking only where the case carries no "
            "critical strings. Where it does, the critical strings are the deterministic "
            "check and coverage is advisory. Vocabulary is also compared with light "
            "suffix stripping, so 'setting/set' and 'restarts/restart' count as the same "
            "word. Version 1 blocked on coverage regardless, which flagged five "
            "well-supported batch-002 claims as possible paraphrases. A boundary defect "
            "is now a claim resting on something outside its span; anaphoric phrasing no "
            "claim depends on is an advisory and does not block."
        ),
        "anaphoric_span_advisories": sorted(
            c["candidate_id"] for c in cases if c["anaphoric_span_advisory"]),
        "is_an_overlay": (
            "This file describes the closed batch; it does not change it. No record was "
            "modified and the closure hash was not recomputed."
        ),
        "source_batch_sha256": batch.get("batch_sha256"),
        "closure_sha256": batch.get("closure_sha256"),
        "cases_audited": len(cases),
        "claims_audited": sum(len(c["claims"]) for c in cases),
        "status_counts": dict(Counter(c["status"] for c in cases)),
        "holdout_eligible_count": sum(1 for c in cases if c["holdout_eligible"]),
        "holdout_eligible": [c["candidate_id"] for c in cases if c["holdout_eligible"]],
        "retrieval_was_not_run": True,
        "method": (
            "Mechanical screen: every code identifier, number, quoted value and product "
            "name asserted by a claim must appear inside the approved span, plus a "
            "content-word coverage measure. Not a semantic proof."
        ),
        "cases": cases,
    }
    overlay["proposed_v2"] = proposed_v2(cases)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    number = overlay["batch"]
    (out_dir / f"GOLD-001-batch-{number:03d}-claim-audit.json").write_text(
        json.dumps(overlay, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / f"GOLD-001-batch-{number:03d}-claim-audit.md").write_text(
        render(overlay), encoding="utf-8")

    print(f"audited {len(cases)} approved cases, "
          f"{overlay['claims_audited']} claims: {overlay['status_counts']}")
    print(f"  holdout-eligible today: {overlay['holdout_eligible_count']}")
    print(f"wrote {out_dir}/GOLD-001-batch-{number:03d}-claim-audit.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
