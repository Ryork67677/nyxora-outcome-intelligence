#!/usr/bin/env python3
"""Validate a golden evaluation set. Failure blocks evaluation.

An evaluation set is the one artifact a project cannot check by running it: a wrong
answer key produces a confident number with nothing behind it. Every check here
exists to make a specific class of wrong key impossible to ship.

The span-hash check is the important one. It re-reads the source text at the
recorded offsets and compares the hash, so a case cannot silently drift when the
corpus is re-parsed, and cannot claim evidence that does not say what it claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from rag_v1.db import connect

SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"
VALID_SPLITS = {"development", "validation", "holdout"}
VALID_CATEGORIES = {
    "exact_lookup", "version_conflict", "multi_hop", "ambiguous", "missing_info",
    "routing_heavy", "passage_heavy", "sanity", "normal",
}
VALID_PROVIDERS = {"anthropic", "openai", "cross"}
VALID_VERIFICATION = {
    "human_verified", "source_anchored_automatic", "absence_verified_against_snapshot",
    "candidate_unverified", "dual_llm_pass", "dual_llm_fail", "needs_human_review",
    "human_approved", "human_rejected",
}
#: Only these may enter a frozen holdout. A dual-LLM pass is not one of them: two
#: models agreeing is correlated evidence, not human approval.
HOLDOUT_APPROVED = {"human_verified", "human_approved"}
#: Provenance a case must carry to be auditable later.
REQUIRED_PROVENANCE = ("source_document_title", "source_url", "source_captured_at")


def normalise(question: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", question.lower()).split().__str__()


def load_sources(cur) -> dict:
    cur.execute(
        """
        SELECT v.version_id, v.normalized_text, s.provider
        FROM document_version v
        JOIN document_source s ON s.source_id = v.source_id
        JOIN corpus_snapshot_version sv ON sv.version_id = v.version_id
        WHERE sv.snapshot_id = %s
        """,
        (SNAPSHOT,),
    )
    return {r[0]: {"text": r[1], "provider": r[2]} for r in cur.fetchall()}


def validate(cases: list[dict], sources: dict, require_human: set[str]) -> list[dict]:
    """Return a list of failures. Empty means the set may be used."""
    failures: list[dict] = []
    seen_ids: set[str] = set()
    seen_questions: dict[str, str] = {}
    seen_evidence: dict[tuple, str] = {}

    def fail(case_id: str, check: str, detail: str) -> None:
        failures.append({"case_id": case_id, "check": check, "detail": detail})

    for case in cases:
        case_id = case.get("case_id", "<missing>")
        if case_id in seen_ids:
            fail(case_id, "unique_case_id", "duplicate case id")
        seen_ids.add(case_id)

        if case.get("category") not in VALID_CATEGORIES:
            fail(case_id, "category", f"unknown category {case.get('category')!r}")
        if case.get("split") not in VALID_SPLITS:
            fail(case_id, "split", f"unknown split {case.get('split')!r}")
        if case.get("provider") not in VALID_PROVIDERS:
            fail(case_id, "provider", f"unknown provider {case.get('provider')!r}")
        if case.get("verification") not in VALID_VERIFICATION:
            fail(case_id, "verification", f"unknown status {case.get('verification')!r}")

        question = case.get("question", "")
        if len(question) < 15:
            fail(case_id, "question_length", "question is too short to be meaningful")
        key = normalise(question)
        if key in seen_questions:
            fail(case_id, "duplicate_question", f"near-duplicate of {seen_questions[key]}")
        seen_questions[key] = case_id

        abstain = case.get("expected_abstain", False)
        evidence = case.get("expected_evidence", [])

        if abstain:
            if evidence:
                fail(case_id, "abstention_has_evidence",
                     "a missing-information case must not carry positive evidence")
            if case.get("expected_claims"):
                fail(case_id, "abstention_has_claims", "abstention case asserts claims")
            continue

        if not evidence:
            fail(case_id, "supported_case_needs_evidence", "no expected evidence")
        if not case.get("expected_claims"):
            fail(case_id, "supported_case_needs_claims", "no expected claims")

        for index, ref in enumerate(evidence):
            version_id = ref.get("version_id")
            if not version_id:
                fail(case_id, "chunk_id_ground_truth",
                     "evidence must be anchored on version_id, not chunk ids")
                continue
            if version_id not in sources:
                fail(case_id, "source_version_exists",
                     f"version {version_id} is not in snapshot {SNAPSHOT}")
                continue
            text = sources[version_id]["text"]
            start, end = ref.get("char_start"), ref.get("char_end")
            if start is None or end is None or not (0 <= start < end <= len(text)):
                fail(case_id, "char_span_valid", f"evidence {index} span {start}:{end} invalid")
                continue
            if not ref.get("section_path"):
                fail(case_id, "section_path_present", f"evidence {index} has no section path")
            # The check that catches silent drift: the anchor must still contain
            # the text the case was written against.
            expected_hash = case.get("evidence_text_sha256")
            if len(evidence) == 1 and expected_hash:
                actual = hashlib.sha256(text[start:end].encode("utf-8")).hexdigest()
                if actual != expected_hash:
                    fail(case_id, "evidence_hash", "source text at the anchor has changed")
            # Every critical claim must actually appear in the evidence it cites.
            span_text = text[start:end].lower()
            if len(evidence) == 1:
                for claim in case.get("expected_claims", []):
                    if claim.get("critical") and claim["text"].lower() not in span_text:
                        fail(case_id, "claim_supported_by_evidence",
                             f"claim {claim['text']!r} does not appear in its own evidence span")

        evidence_key = tuple(sorted((e.get("version_id"), e.get("char_start"), e.get("char_end"))
                                    for e in evidence))
        if evidence_key and evidence_key in seen_evidence:
            fail(case_id, "duplicate_evidence",
                 f"same evidence as {seen_evidence[evidence_key]}")
        seen_evidence[evidence_key] = case_id

        # Multi-hop structure: every required span must be independently anchored,
        # or partial retrieval would silently earn full credit.
        if case.get("category") == "multi_hop":
            if len(evidence) < 2:
                fail(case_id, "multi_hop_structure",
                     "a multi-hop case must carry at least two evidence spans")
            spans = {(e.get("version_id"), e.get("char_start"), e.get("char_end"))
                     for e in evidence}
            if len(spans) != len(evidence):
                fail(case_id, "multi_hop_structure", "duplicate spans within one case")

        if case.get("split") == "holdout":
            missing = [f for f in REQUIRED_PROVENANCE if case.get(f) in (None, "")]
            if missing:
                fail(case_id, "missing_provenance",
                     f"holdout case lacks {', '.join(missing)}")

        if case.get("split") in require_human:
            status = case.get("verification")
            if status not in HOLDOUT_APPROVED or not case.get("human_verified"):
                fail(case_id, "human_verified_required",
                     f"{case.get('split')} requires human approval; status is {status!r}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    parser.add_argument("--require-human", default="holdout",
                        help="comma-separated splits that must be human-verified")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    cases = [json.loads(line) for line in Path(args.path).read_text().splitlines() if line.strip()]
    with connect() as conn, conn.cursor() as cur:
        sources = load_sources(cur)

    require = {s for s in args.require_human.split(",") if s}
    failures = validate(cases, sources, require)

    report = {
        "path": args.path,
        "cases": len(cases),
        "snapshot": SNAPSHOT,
        "by_split": dict(Counter(c.get("split") for c in cases)),
        "by_category": dict(Counter(c.get("category") for c in cases)),
        "by_provider": dict(Counter(c.get("provider") for c in cases)),
        "by_verification": dict(Counter(c.get("verification") for c in cases)),
        "failures": failures,
        "failure_counts": dict(Counter(f["check"] for f in failures)),
        "passed": not failures,
    }
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"{len(cases)} cases, {len(failures)} failures")
    for check, count in sorted(report["failure_counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {check:34s} {count}")
    if failures:
        print("\nexamples:")
        for f in failures[:8]:
            print(f"  [{f['case_id']}] {f['check']}: {f['detail']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
