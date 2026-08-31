#!/usr/bin/env python3
"""Admit HA-01 … HA-60 from the 150-case review packet, or refuse and say why.

The packet of record is ``Production_RAG_v1_Full_150_Case_Review.pdf``. Its 60 drafts
carry full evidence identity, so nothing here is bound by the short ``HA-nn`` label: a
separate 64-case packet uses the same labels for different cases, and binding by number
would have attached owner approval to cases nobody reviewed. Every record is instead
re-derived from the frozen source — the span is re-sliced at its offsets, rehashed, and
its ``version_id`` recomputed through the content-derived chain — before it is eligible
to be admitted at all.

Two cases need work before they can be admitted, and both are handled explicitly:

``HA-15``
    The anaphora detector reports ``NONCRITICAL_ANAPHORA`` on a neighbouring "the model".
    The finding is **retained**, not deleted, and carries an explicit project-owner
    override. Nothing scored depends on resolving that phrase.

``HA-47``
    Its second span opened on "It" with the antecedent in the first span, which fails the
    independently self-contained-span rule. The two spans are replaced by the one
    contiguous span that carries both, recomputed from the frozen source. The old spans
    and their hashes are preserved in the revision history.

Approval is the project owner's and is recorded as theirs. This script imports a
decision; it does not make one. No retrieval is run and no closed batch is touched.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rag_v1.gold import anaphora  # noqa: E402
from rag_v1.gold.eligibility import HOLDOUT_CONDITIONS, evaluate  # noqa: E402
from rag_v1.ids import stable_id  # noqa: E402
from rag_v1.parsing import parse_file  # noqa: E402

PACKET_SHA256 = "bf6190fc53ee4ada6c948093d30e8fa7feac3dbf3300918ec75886d2a5a8f786"
PACKET_PAGES = 159
RECORDS_ATTACHMENT = "150-case-review-records.json"

#: Statements the packet has to make about itself before any record is read. The counts
#: are read from the embedded records instead of from prose; these are the claims that
#: only the prose can carry.
FRONT_MATTER_CLAIMS = {
    "part_b_is_the_codex_derivative_reviewed_by_grok":
        "reproduces exactly HA-01 through HA-60 from the Codex derivative reviewed by "
        "Grok Expert",
    "the_alternate_64_case_packet_is_excluded":
        "Those separate packet-local IDs are excluded to avoid double-counting",
    "the_drafts_are_not_yet_human_verified":
        "No human_verified or holdout_eligible flag was changed for the drafts",
    "no_retrieval_was_run":
        "No new approval, retrieval run, deployment, or benchmark admission was "
        "performed to create this PDF",
}

#: HA-47's repaired evidence: one contiguous span carrying the ``input_type`` antecedent
#: and all three non-effects. The hash is recomputed from the frozen source at run time
#: and compared against this; it is never copied in.
HA47 = {
    "case_id": "HA-47",
    "char_start": 4308,
    "char_end": 4916,
    "expected_sha256": "e894c94d831ccfd2678f4cd132b72b52e44770d07ebeaab6c51e96e0e312a203",
    "old_spans": [
        {"char_start": 4308, "char_end": 4378,
         "evidence_hash":
             "5e36f5ff857cdcd795d4e8133de6072b5a8e7588be44fc21516e24a5e97f5b34"},
        {"char_start": 4539, "char_end": 4916,
         "evidence_hash":
             "f4d4ee514ca2285d8cc67313a02b7cb7382d11cc3cedfd998733884d98321387"},
    ],
    "must_establish": {
        "subject_is_input_type": "`input_type` describes",
        "does_not_replace_the_next_agents_main_input":
            "It does not replace the next agent's main input",
        "does_not_choose_a_different_destination":
            "it does not choose a different destination",
        "handoff_still_transfers_to_the_wrapped_agent":
            "still transfers to the specific agent you wrapped",
    },
    "revision_reason": ["EVIDENCE_BOUNDARY_COMPLETION", "CRITICAL_ANAPHORA_REPAIR"],
}

HA15 = {"case_id": "HA-15", "expected_status": anaphora.NONCRITICAL,
        "expected_phrase": "the model"}


class Refused(SystemExit):
    """The admission stopped. Nothing was written."""


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_packet(pdf: Path) -> tuple[dict, str]:
    """Verify the packet's identity, then read its embedded records."""
    import pypdf

    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if digest != PACKET_SHA256:
        raise Refused(f"packet sha256 {digest} is not the packet of record")
    reader = pypdf.PdfReader(str(pdf))
    if len(reader.pages) != PACKET_PAGES:
        raise Refused(f"packet has {len(reader.pages)} pages, expected {PACKET_PAGES}")

    front = " ".join(" ".join((page.extract_text() or "").split())
                     for page in reader.pages[:4])
    for name, needle in FRONT_MATTER_CLAIMS.items():
        if needle not in front:
            raise Refused(f"the packet does not state {name!r}")

    blob = reader.attachments[RECORDS_ATTACHMENT]
    data = b"".join(blob) if isinstance(blob, list) else blob
    return json.loads(data), digest


def frozen_texts(sources: Path) -> dict[str, str]:
    """The reproduced OpenAI corpus, keyed by the content hash of its normalized text."""
    return {sha(parse_file(path).normalized_text): parse_file(path).normalized_text
            for path in sorted(sources.glob("*.md"))}


def verify_against_source(record: dict, texts: dict[str, str]) -> list[str]:
    """Re-derive the record from the frozen source. Returns the reasons it does not."""
    failures = []
    text = texts.get(record["content_hash"])
    if text is None:
        return [f"{record['candidate_id']}: source document is not reproducible"]

    src_id = stable_id("src", record["provider"], record["source_url"], length=32)
    if stable_id("ver", src_id, record["content_hash"], length=32) != record["version_id"]:
        failures.append(f"{record['candidate_id']}: version_id does not re-derive from "
                        "provider, canonical url and content hash")
    for span in record["expected_evidence"]:
        where = f"{record['candidate_id']} {span['evidence_id']}"
        sliced = text[span["char_start"]:span["char_end"]]
        if sliced != span["evidence_text"]:
            failures.append(f"{where}: offsets do not re-slice to the stored evidence")
            continue
        if sha(sliced) != span["evidence_hash"]:
            failures.append(f"{where}: hash recomputed from source disagrees")
        if span["version_id"] != record["version_id"]:
            failures.append(f"{where}: span version_id differs from the record's")
        if span["char_end"] - span["char_start"] != len(span["evidence_text"]):
            failures.append(f"{where}: char length disagrees with the evidence text")
        for string in span.get("critical_strings") or []:
            if string.lower() not in sliced.lower():
                failures.append(f"{where}: critical string {string!r} is not in this span")
    return failures


def opens_on_a_reference(span_text: str, record: dict) -> bool:
    """The independently self-contained-span rule, applied to one span on its own."""
    return anaphora.evaluate_span(span_text, record)["status"] == anaphora.CRITICAL


def repair_ha47(record: dict, texts: dict[str, str]) -> dict:
    """Replace the two spans with the one contiguous span that carries the antecedent."""
    text = texts[record["content_hash"]]
    body = text[HA47["char_start"]:HA47["char_end"]]
    digest = sha(body)
    if digest != HA47["expected_sha256"]:
        raise Refused(f"HA-47 repaired span hashes to {digest}, not the verified value")

    old = record["expected_evidence"]
    if [{"char_start": s["char_start"], "char_end": s["char_end"],
         "evidence_hash": s["evidence_hash"]} for s in old] != HA47["old_spans"]:
        raise Refused("HA-47's stored spans are not the ones the repair was verified for")
    for name, needle in HA47["must_establish"].items():
        if needle not in body:
            raise Refused(f"HA-47 repaired span does not establish {name!r}")

    union: list[str] = []
    for span in old:
        for string in span.get("critical_strings") or []:
            if string not in union:
                union.append(string)

    repaired = copy.deepcopy(record)
    repaired["expected_evidence"] = [{
        "evidence_id": "E1",
        "version_id": record["version_id"],
        "review_section_path": old[0].get("review_section_path"),
        "legacy_section_path": old[0].get("legacy_section_path"),
        "char_start": HA47["char_start"], "char_end": HA47["char_end"],
        "evidence_text": body, "evidence_hash": digest,
        "evidence_char_length": len(body),
        "critical_strings": union,
    }]
    repaired["critical_strings"] = union
    repaired["evidence_shape"] = "single_span"
    repaired["paragraph_break_present"] = "\n\n" in body.strip()
    # Read from the predicate rather than asserted: no holdout condition looks at
    # paragraph structure, so a paragraph break cannot block eligibility. This is not a
    # waiver — it is what the specification already says.
    repaired["paragraph_break_eligibility_blocking"] = any(
        "paragraph" in condition for condition in HOLDOUT_CONDITIONS)
    repaired.setdefault("revisions", []).append({
        "reason": HA47["revision_reason"],
        "revised_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "revised_by": "project_owner",
        "note": ("The second span opened on 'It' with its antecedent in the first span, "
                 "which fails the independently self-contained-span rule. The two spans "
                 "are replaced by the one contiguous span that carries both. The "
                 "question, answer and claims are unchanged."),
        "from": [{"evidence_id": s["evidence_id"], "char_start": s["char_start"],
                  "char_end": s["char_end"], "evidence_hash": s["evidence_hash"],
                  "evidence_char_length": s["evidence_char_length"],
                  "critical_strings": s.get("critical_strings"),
                  "evidence_text": s["evidence_text"]} for s in old],
        "to": {"evidence_id": "E1", "char_start": HA47["char_start"],
               "char_end": HA47["char_end"], "evidence_hash": digest,
               "evidence_char_length": len(body), "critical_strings": union},
        "establishes": list(HA47["must_establish"]),
        "paragraph_break_present": repaired["paragraph_break_present"],
        "eligibility_blocking": repaired["paragraph_break_eligibility_blocking"],
    })
    return repaired


def override_ha15(record: dict) -> dict:
    """Retain the detector's finding and record the owner's explicit override."""
    joined = " \n".join(s["evidence_text"] for s in record["expected_evidence"])
    verdict = anaphora.evaluate_span(joined, record)
    if verdict["status"] != HA15["expected_status"]:
        raise Refused(f"HA-15 anaphora status is {verdict['status']}, expected "
                      f"{HA15['expected_status']}; an override is only valid for a "
                      "noncritical finding")
    if verdict["phrase"] != HA15["expected_phrase"]:
        raise Refused(f"HA-15 flags {verdict['phrase']!r}, not {HA15['expected_phrase']!r}")

    out = copy.deepcopy(record)
    out["anaphora_status"] = verdict["status"]
    out["anaphora_finding"] = verdict["finding"]          # retained, never deleted
    out["anaphora_phrase"] = verdict["phrase"]
    out["human_anaphora_override"] = True
    out["override_reviewer"] = "project_owner"
    out["override_rationale"] = (
        "The scored fact — that the returned handoff JSON is validated locally in the "
        "SDK — does not require resolving the neighbouring reference to 'the model'. "
        "The detector's finding is retained.")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True)
    parser.add_argument("--sources", required=True,
                        help="the reproduced OpenAI corpus, as pinned markdown")
    parser.add_argument("--chatgpt-review", required=True)
    parser.add_argument("--out", default="evals/review/gold_review_HA01_HA60_final.json")
    parser.add_argument("--decisions",
                        default="evals/review/human_decisions_HA01_HA60.json",
                        help="the owner's decision file; read, never written")
    parser.add_argument("--report",
                        default="experiments/GOLD-001/GOLD-001-HA-admission.json")
    args = parser.parse_args()

    packet, packet_sha = load_packet(Path(args.packet))
    selected = packet["selected_cases"]
    historical = [c for c in selected if not c["id"].startswith("HA-")]
    drafts = [c for c in selected if c["id"].startswith("HA-")]

    identity = {
        "packet_sha256": packet_sha,
        "pages": PACKET_PAGES,
        "historical_approved_cases": len(historical),
        "draft_cases": len(drafts),
        "draft_ids_are_HA_01_through_HA_60_exactly_once":
            sorted(c["id"] for c in drafts) == sorted(f"HA-{i:02d}" for i in range(1, 61)),
        "packet_counts_block": packet["counts"],
        "packet_declares_no_new_approval": packet.get("no_new_approval"),
        "front_matter_claims_confirmed": sorted(FRONT_MATTER_CLAIMS),
    }
    if len(historical) != 90 or len(drafts) != 60:
        raise Refused(f"packet holds {len(historical)} historical and {len(drafts)} "
                      "drafts, expected 90 and 60")
    if not identity["draft_ids_are_HA_01_through_HA_60_exactly_once"]:
        raise Refused("the draft ids are not exactly HA-01 … HA-60")
    if any(c["approved"] for c in drafts):
        raise Refused("a draft is already marked approved in the packet")
    print(f"packet verified: {len(historical)} historical + {len(drafts)} drafts, "
          f"{PACKET_PAGES} pages, sha256 {packet_sha[:16]}…")

    texts = frozen_texts(Path(args.sources))
    records = {c["id"]: c["record"] for c in drafts}

    failures: list[str] = []
    for case_id in sorted(records):
        failures.extend(verify_against_source(records[case_id], texts))
    if failures:
        for failure in failures:
            print(f"  SOURCE FAILURE {failure}")
        raise Refused(f"{len(failures)} record(s) do not re-derive from the frozen source")
    spans = sum(len(r["expected_evidence"]) for r in records.values())
    print(f"source verification: {len(records)} records, {spans} spans re-sliced and "
          "rehashed from the pinned corpus")

    # ------------------------------------------------------------ the two open findings
    records["HA-47"] = repair_ha47(records["HA-47"], texts)
    print(f"HA-47 repaired: one span {HA47['char_start']}:{HA47['char_end']}, "
          f"sha256 {records['HA-47']['expected_evidence'][0]['evidence_hash'][:16]}…")
    records["HA-15"] = override_ha15(records["HA-15"])
    print("HA-15 override recorded, finding retained: "
          f"{records['HA-15']['anaphora_finding']}")

    # Every span of a multi-span record must stand on its own: none may open on a
    # reference whose antecedent lives in a different span. This is the rule HA-47 failed.
    not_self_contained = [
        f"{cid} {s['evidence_id']}"
        for cid, r in records.items()
        for s in r["expected_evidence"]
        if len(r["expected_evidence"]) > 1 and opens_on_a_reference(s["evidence_text"], r)]
    if not_self_contained:
        raise Refused("spans that are not independently self-contained: "
                      + ", ".join(not_self_contained))
    checked_spans = sum(len(r["expected_evidence"]) for r in records.values())
    print(f"self-contained-span rule: all {checked_spans} spans pass")

    # ------------------------------------------------------------ bind the review
    review = json.loads(Path(args.chatgpt_review).read_text())
    verdicts = {r["case_id"]: r for r in review["records"]}
    if sorted(verdicts) != sorted(records):
        raise Refused("the review does not cover exactly the packet's 60 cases")

    def plain(value: str) -> str:
        return " ".join(value.replace("`", "").split())

    unbound = [cid for cid, r in records.items()
               if plain(verdicts[cid]["question"]) != plain(r["question"])
               or plain(verdicts[cid]["answer"]) != plain(r["answer"])]
    if unbound:
        raise Refused("review verdicts do not bind to the authoritative records by "
                      f"question and answer: {unbound}")
    rejected = [cid for cid, v in verdicts.items()
                if v["chatgpt_independent_verdict"] not in
                ("PASS", "PASS_WITH_NONCRITICAL_ANAPHORA_OVERRIDE",
                 "FIX_REQUIRED_THEN_APPROVE")]
    if rejected:
        raise Refused(f"the review rejects {rejected}; they cannot be admitted")
    for case_id, record in records.items():
        record["chatgpt_review"] = {
            "verdict": verdicts[case_id]["chatgpt_independent_verdict"],
            "review_note": verdicts[case_id]["review_note"],
            "reviewer": "ChatGPT",
            "bound_by": "case id plus exact question and answer",
            "confers_no_approval": True}
    print(f"review bound to all {len(records)} records by question, answer and case id")

    # ------------------------------------------------------------ the owner's decision
    # Read, never produced. No script may create human_verified: the decision has to
    # already exist as the owner's, and this only imports it. A decision file that does
    # not cover exactly these 60 cases, or that names the wrong packet, refuses.
    decisions = json.loads(Path(args.decisions).read_text())
    if decisions.get("packet_sha256") != packet_sha:
        raise Refused("the decision file names a different packet than the one verified")
    if decisions.get("reviewer") != "project_owner":
        raise Refused(f"decisions are attributed to {decisions.get('reviewer')!r}; only "
                      "the project owner can approve a case")
    approved = set(decisions.get("approved") or [])
    refused_ids = set(decisions.get("rejected") or [])
    if approved & refused_ids:
        raise Refused("a case is both approved and rejected in the decision file")
    undecided = set(records) - approved - refused_ids
    if undecided:
        raise Refused(f"no owner decision for {sorted(undecided)}")
    if approved - set(records):
        raise Refused(f"the decision file approves cases the packet does not hold: "
                      f"{sorted(approved - set(records))}")
    for case_id in sorted(refused_ids):
        records.pop(case_id, None)
    print(f"owner decisions imported: {len(approved)} approved, {len(refused_ids)} "
          f"rejected, reviewer {decisions['reviewer']}")

    decided_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    for record in records.values():
        record["verification_status"] = "human_verified"
        record["human_verified"] = True
        record["reviewer"] = "project_owner"
        record["reviewed_at"] = decided_at
        record["admitted_from"] = {
            "packet": "Production_RAG_v1_Full_150_Case_Review.pdf",
            "packet_sha256": packet_sha,
            "bound_by": "evidence identity, not the short HA label",
            "decision_file": args.decisions}
        record["non_official"] = False
        record["retrieval_was_not_run"] = True

    # ------------------------------------------------------------ the real gate
    verdict_by_id = {cid: evaluate(r) for cid, r in records.items()}
    ineligible = {cid: v["failures"] for cid, v in verdict_by_id.items()
                  if not v["holdout_eligible"]}
    for case_id, record in records.items():
        record["holdout_eligible"] = verdict_by_id[case_id]["holdout_eligible"]
    eligible = sum(1 for v in verdict_by_id.values() if v["holdout_eligible"])
    print(f"eligibility: {eligible}/{len(records)} holdout_eligible")
    if ineligible:
        for case_id, reasons in sorted(ineligible.items()):
            for reason in reasons:
                print(f"  INELIGIBLE {case_id}: {reason['condition']} — {reason['detail']}")
        raise Refused(f"{len(ineligible)} case(s) failed the eligibility gate; "
                      "nothing was written")

    ordered = [records[f"HA-{i:02d}"] for i in range(1, 61)]
    Path(args.out).write_text(json.dumps({
        "batch": "HA-01–HA-60",
        "group": "HA",
        "source_packet": "Production_RAG_v1_Full_150_Case_Review.pdf",
        "source_packet_sha256": packet_sha,
        "admitted_at": decided_at,
        "reviewer": "project_owner",
        "binding": "evidence identity (version_id, offsets, evidence hash), not the "
                   "short HA label",
        "not_the_alternate_packet": (
            "These are the packet-of-record's HA-01 … HA-60. The separate "
            "Claude-authored 64-case packet is NOT_ADMITTED and none of its candidates "
            "appears here."),
        "records": ordered,
    }, indent=2, ensure_ascii=False) + "\n")

    report = {
        "generated_at": decided_at,
        "packet_identity": identity,
        "source_verification": {"records": len(records), "spans": spans,
                                "failures": [], "corpus": str(args.sources)},
        "chatgpt_review": {"bound": True, "records": len(verdicts),
                           "counts": review["counts"],
                           "binding": "case_id plus exact question and answer against "
                                      "the authoritative record"},
        "ha15_override": {
            "anaphora_status": records["HA-15"]["anaphora_status"],
            "finding_retained": records["HA-15"]["anaphora_finding"],
            "human_anaphora_override": True, "override_reviewer": "project_owner"},
        "ha47_repair": {
            "from": HA47["old_spans"],
            "to": {"char_start": HA47["char_start"], "char_end": HA47["char_end"],
                   "evidence_char_length":
                       records["HA-47"]["expected_evidence"][0]["evidence_char_length"],
                   "evidence_hash":
                       records["HA-47"]["expected_evidence"][0]["evidence_hash"]},
            "reason": HA47["revision_reason"],
            "establishes": list(HA47["must_establish"]),
            "paragraph_break_present": records["HA-47"]["paragraph_break_present"],
            "eligibility_blocking":
                records["HA-47"]["paragraph_break_eligibility_blocking"]},
        "owner_decisions": {"approved": len(approved), "rejected": len(refused_ids),
                            "reviewer": decisions["reviewer"],
                            "decision_file": args.decisions,
                            "conditional": decisions.get("conditional", {})},
        "eligibility": {"evaluated": len(records), "holdout_eligible": eligible,
                        "ineligible": ineligible},
        "retrieval_was_not_run": True,
        "systems_executed": [],
    }
    Path(args.report).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {args.out}, {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
