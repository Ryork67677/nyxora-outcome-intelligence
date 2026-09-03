"""Holdout eligibility — a separate state from human approval, and a stricter one.

The batch 001 claim audit exposed the gap this module closes. ``human_verified`` means a
person read the case and said yes. It does **not** mean a machine can check the case
later: 13 of 16 approved batch-001 cases carried no literal critical string, so the
claim-in-evidence gate passed over them without testing anything, and a holdout built
from them would have been gated on nothing.

The two states are deliberately independent:

``human_verified``
    A person approved this case. Historical, permanent, and never revoked by anything
    here — an approval that was honestly given stays given.

``holdout_eligible``
    Everything in ``HOLDOUT_CONDITIONS`` holds *right now*. Metadata can make a case
    eligible without re-approving it, and a corpus change can make it ineligible without
    calling the approval wrong.

Only ``holdout_eligible`` cases may enter a frozen holdout. Nothing here modifies a case
or downgrades an approval; it answers a question.
"""

from __future__ import annotations

import hashlib

from rag_v1.gold.normalisation import contains_claim_string

#: The conditions, in the order they are reported. Each maps to one check below.
HOLDOUT_CONDITIONS = (
    "human_verified",
    "every_claim_has_a_deterministic_check",
    "critical_strings_present_in_evidence",
    "evidence_hash_valid",
    "no_unresolved_scope_defect",
    "required_evidence_declared",
)


def evaluate(case: dict) -> dict:
    """Return the eligibility verdict for one case, with a reason per failed condition."""
    failures: list[dict] = []

    if case.get("verification_status") != "human_verified" or not case.get("human_verified"):
        failures.append({
            "condition": "human_verified",
            "detail": (f"status is {case.get('verification_status')!r}; only a case a "
                       "person approved may enter a holdout"),
        })

    claims = case.get("proposed_atomic_claims") or []
    strings = case.get("critical_strings") or []
    if not claims:
        failures.append({"condition": "every_claim_has_a_deterministic_check",
                         "detail": "the case asserts no atomic claims"})
    elif not strings:
        failures.append({
            "condition": "every_claim_has_a_deterministic_check",
            "detail": ("no critical strings, so the claim-in-evidence gate passes this "
                       "case without checking anything about its claims"),
        })

    # A multi-span case's evidence is all of its spans. Checking only the first would
    # call a case ineligible for a string its second span carries — and every batch-003
    # multi-span case keeps part of its claim in the second span.
    spans = case.get("expected_evidence")
    evidence = (" \n".join(s["evidence_text"] for s in spans) if spans
                else case.get("evidence_text", ""))
    missing = [s for s in strings if not contains_claim_string(evidence, s)]
    if missing:
        failures.append({
            "condition": "critical_strings_present_in_evidence",
            "detail": f"not inside the anchored span: {missing}",
        })

    # Each span's own hash must match its own text; a joined blob has no meaningful
    # hash, so multi-span cases are checked span by span.
    for span in (spans or [case]):
        recorded = span.get("evidence_hash")
        body = span.get("evidence_text", "")
        actual = hashlib.sha256(body.encode("utf-8")).hexdigest() if body else None
        if not recorded or recorded != actual:
            failures.append({
                "condition": "evidence_hash_valid",
                "detail": ("the stored hash does not match the stored evidence text"
                           + (f" (span at {span.get('char_start')})" if spans else "")),
            })

    scope = case.get("unresolved_scope_defect")
    if scope:
        failures.append({"condition": "no_unresolved_scope_defect", "detail": scope})

    # A case built from more than one span must say so. Without the flag a holdout
    # runner has no way to know that retrieving one span is a partial answer rather
    # than the answer, and a multi-hop case scored on one span is scored wrongly.
    if spans and len(spans) > 1:
        if not case.get("requires_all_evidence"):
            failures.append({
                "condition": "required_evidence_declared",
                "detail": (f"{len(spans)} spans but requires_all_evidence is not set, so "
                           "nothing records that a partial retrieval is a partial answer"),
            })
        # Per-span critical strings are the batch-004 convention. Batch 003 keeps one
        # list on the record, and that list is already checked against the joined
        # evidence above, so requiring the newer shape there would retroactively
        # disqualify closed cases for a convention that did not exist when a person
        # approved them. What is a defect in either convention is a *mixed* record: one
        # span carrying its own strings while another carries none is a span nothing
        # checks.
        declared = [s for s in spans if s.get("critical_strings")]
        if declared and len(declared) != len(spans):
            bare = [s.get("evidence_id") or s.get("char_start")
                    for s in spans if not s.get("critical_strings")]
            failures.append({
                "condition": "required_evidence_declared",
                "detail": (f"some spans declare their own critical strings and these do "
                           f"not, so nothing checks them: {bare}"),
            })
    if case.get("reasoning_type") == "genuine_multi_hop":
        if len(spans or []) < 2:
            failures.append({"condition": "required_evidence_declared",
                             "detail": "genuine_multi_hop with fewer than two spans"})
        if case.get("multi_hop_composition_check") != "PASS":
            failures.append({
                "condition": "required_evidence_declared",
                "detail": ("genuine_multi_hop without a passing composition check: "
                           f"{case.get('multi_hop_composition_check')!r}")})
        if case.get("evidence_shape") == "multi_document":
            documents = {s.get("version_id") for s in (spans or [])}
            if len(documents) < 2:
                failures.append({
                    "condition": "required_evidence_declared",
                    "detail": ("labelled multi_document but every span is in the same "
                               "document version")})

    return {
        "candidate_id": case.get("candidate_id"),
        "holdout_eligible": not failures,
        "conditions_checked": list(HOLDOUT_CONDITIONS),
        "failures": failures,
        "note": (
            "human_verified is unaffected by this result. Eligibility is a property of "
            "the case's current metadata, not a judgement on the person's approval."
        ),
    }


def eligible(cases: list[dict]) -> list[dict]:
    return [c for c in cases if evaluate(c)["holdout_eligible"]]


__all__ = ["HOLDOUT_CONDITIONS", "eligible", "evaluate"]
