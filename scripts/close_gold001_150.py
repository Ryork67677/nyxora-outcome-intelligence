#!/usr/bin/env python3
"""Close GOLD-001 at 150, if the records support it, and say what 150 does not buy.

Every number here is read from the records at build time. Nothing is retyped, and the
build refuses rather than rendering a document that disagrees with the project state:
if a case is not eligible, if the counts do not add up, if a retrieval system has been
executed, or if the holdout has been frozen, there is no closure to write.

The document leads with what the size does not fix. 150 is the benchmark-size target and
that is all it is: the set is provider- and category-skewed, genuine multi-hop is still
n=1, the preregistered pilot sequence was not followed, and the frozen corpus is still
not reproduced. A closure that buried those would be the wrong document.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rag_v1.gold.eligibility import HOLDOUT_CONDITIONS, evaluate  # noqa: E402

STATUS = "experiments/GOLD-001/GOLD-001-eligibility-status.json"
ADMISSION = "experiments/GOLD-001/GOLD-001-HA-admission.json"
LIMITATION = "experiments/GOLD-001/GOLD-001-corpus-reproduction-limitation.json"
DEVIATION = "experiments/GOLD-001/GOLD-001-protocol-deviation-001.json"
TARGET_SIZE = 150


class Refused(SystemExit):
    """The closure was not written."""


def eligible_cases(status: dict) -> list[dict]:
    """Every eligible case, read from the file each group's eligibility comes from."""
    cases = []
    for group in status["batches"]:
        source = Path(group["eligibility_source"])
        payload = json.loads(source.read_text())
        records = payload.get("case_records") or payload.get("records") or []
        by_id = {r["candidate_id"]: r for r in records}
        for candidate_id in group["holdout_eligible_ids"]:
            case = by_id.get(candidate_id)
            if case is None:
                raise Refused(f"{candidate_id} is counted eligible in {source} but is "
                              "not in that file")
            cases.append(dict(case, _group=group["label"]))
    return cases


#: Batches 001 and 002 predate the reasoning-type and evidence-shape fields. Their cases
#: are counted under this label rather than under ``None``, so a reader can tell a real
#: category from a field that was never filled in.
UNRECORDED = "(not recorded in this batch's schema)"


def distribution(cases: list[dict], key: str) -> dict[str, int]:
    counts = Counter(str(c.get(key)) if c.get(key) is not None else UNRECORDED
                     for c in cases)
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="experiments/GOLD-001")
    args = parser.parse_args()

    status = json.loads(Path(STATUS).read_text())
    combined = status["combined"]

    # ---------------------------------------------------------------- build gates
    if status["retrieval_was_not_run"] is not True or status["systems_executed"]:
        raise Refused("a retrieval system has been executed; this closure would be wrong")
    if status["holdout_frozen"] is not False:
        raise Refused("the holdout is frozen; this closure describes an unfrozen state")

    cases = eligible_cases(status)
    if len(cases) != combined["holdout_eligible"]:
        raise Refused(f"{len(cases)} eligible cases read from the records, but the "
                      f"status says {combined['holdout_eligible']}")
    if combined["human_verified"] != combined["holdout_eligible"]:
        raise Refused(f"{combined['human_verified']} verified but "
                      f"{combined['holdout_eligible']} eligible; the closure would have "
                      "to explain a gap it does not describe")

    # Re-run the real predicate here rather than trusting the status file's counts.
    reverdict = {c["candidate_id"]: evaluate(c) for c in cases}
    ineligible = {cid: v["failures"] for cid, v in reverdict.items()
                  if not v["holdout_eligible"]}
    if ineligible:
        for cid, failures in sorted(ineligible.items()):
            for failure in failures:
                print(f"  INELIGIBLE {cid}: {failure['condition']} — {failure['detail']}")
        raise Refused(f"{len(ineligible)} case(s) do not pass the eligibility gate on "
                      "re-evaluation")
    if len({c["candidate_id"] for c in cases}) != len(cases):
        raise Refused("a candidate id appears twice across the groups")

    admission = json.loads(Path(ADMISSION).read_text())
    limitation = json.loads(Path(LIMITATION).read_text())
    deviation = json.loads(Path(DEVIATION).read_text()) if Path(DEVIATION).exists() else {}
    if not deviation:
        raise Refused(f"{DEVIATION} is missing; the closure may not omit the deviation")
    if limitation.get("CORPUS_REPRODUCTION_INCOMPLETE") is not True:
        raise Refused("the corpus limitation no longer says reproduction is incomplete")

    providers = distribution(cases, "provider")
    categories = distribution(cases, "reasoning_type")
    shapes = distribution(cases, "evidence_shape")
    multi_hop = [c["candidate_id"] for c in cases
                 if c.get("reasoning_type") == "genuine_multi_hop"]
    documents = Counter(str(c.get("version_id")) for c in cases)
    ambiguity = [c["candidate_id"] for c in cases
                 if str(c.get("reasoning_type", "")).startswith("ambiguity")
                 or c.get("candidate_type") == "ambiguous"]
    overrides = [c["candidate_id"] for c in cases if c.get("human_anaphora_override")]
    revised = [c["candidate_id"] for c in cases if c.get("revisions")]

    closure = {
        "closed_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "headline": (f"{combined['holdout_eligible']} cases is the achieved GOLD "
                     "benchmark-size target. It is a size, not coverage."),
        "target_size": TARGET_SIZE,
        "size_target_achieved": combined["holdout_eligible"] >= TARGET_SIZE,
        "counts": {
            "human_verified": combined["human_verified"],
            "holdout_eligible": combined["holdout_eligible"],
            "human_rejected": combined["human_rejected"],
            "genuine_multi_hop": combined["genuine_multi_hop"],
            "candidates_reviewed": combined["candidates"],
        },
        "counts_source": "derived from the group records via the eligibility predicate",
        "by_group": [{"group": g["label"], "human_verified": g["human_verified"],
                      "human_rejected": g["human_rejected"],
                      "holdout_eligible": g["holdout_eligible"],
                      "eligibility_source": g["eligibility_source"]}
                     for g in status["batches"]],
        "conditions_checked": list(HOLDOUT_CONDITIONS),
        "coverage": {
            "provider": providers,
            "reasoning_type": categories,
            "evidence_shape": shapes,
            "genuine_multi_hop_ids": multi_hop,
            "ambiguity_cases": len(ambiguity),
            "ambiguity_case_ids": ambiguity,
            "cases_with_no_recorded_reasoning_type":
                categories.get(UNRECORDED, 0),
            "distinct_source_documents": len(documents),
            "most_concentrated_document": documents.most_common(1)[0] if documents else None,
            "cases_from_the_top_document": documents.most_common(1)[0][1] if documents else 0,
        },
        "admission": {
            "packet": "Production_RAG_v1_Full_150_Case_Review.pdf",
            "packet_sha256": admission["packet_identity"]["packet_sha256"],
            "cases_admitted": admission["owner_decisions"]["approved"],
            "reviewer": admission["owner_decisions"]["reviewer"],
            "ha15_override": admission["ha15_override"],
            "ha47_repair": admission["ha47_repair"],
            "anaphora_overrides_in_the_set": overrides,
            "cases_carrying_a_revision": revised,
        },
        "limitations": {
            "provider_imbalance": (
                f"{max(providers.values())} of {len(cases)} eligible cases come from "
                f"one provider ({max(providers, key=providers.get)}). A per-provider "
                "result from this set is not a comparison between providers."),
            "category_imbalance": (
                f"the largest recorded category holds "
                f"{max(v for k, v in categories.items() if k != UNRECORDED)} of "
                f"{len(cases)} cases and the smallest holds "
                f"{min(v for k, v in categories.items() if k != UNRECORDED)}; "
                f"{categories.get(UNRECORDED, 0)} cases predate the field entirely. An "
                "unweighted score over this set is dominated by the largest category."),
            "genuine_multi_hop": (
                f"{combined['genuine_multi_hop']} case. One observation cannot support "
                "any claim about multi-hop performance, and 150 does not change that."),
            "protocol_deviation": deviation.get("disposition"),
            "corpus_reproduction": (
                "incomplete; "
                f"{limitation['outstanding']['anthropic_documents']} Anthropic documents "
                f"and {limitation['outstanding']['unbuildable_identities']} unbuildable "
                "identities outstanding"),
            "retrieval": limitation["effect"],
        },
        "holdout_frozen": False,
        "reason_not_frozen": status["reason_not_frozen"],
        "retrieval_was_not_run": True,
        "systems_executed": [],
        "alternate_packet": (
            "The separate Claude-authored 64-case packet is NOT_ADMITTED and contributed "
            "no case to this total. See GOLD-001-alternate-HA-packet-disposition.json."),
    }
    # The hash covers what the closure asserts, not when it was built. A digest that
    # changed on every rebuild would certify nothing; this one reproduces as long as the
    # counts, coverage, admission and limitations do.
    substantive = {k: v for k, v in closure.items()
                   if k not in ("closed_at", "closure_hash")}
    substantive["admission"] = {k: v for k, v in closure["admission"].items()}
    digest = hashlib.sha256(
        json.dumps(substantive, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False).encode()).hexdigest()[:16]
    closure["closure_hash"] = digest

    out_dir = Path(args.out_dir)
    (out_dir / "GOLD-001-150-case-closure.json").write_text(
        json.dumps(closure, indent=2, ensure_ascii=False) + "\n")
    (out_dir / "GOLD-001-150-case-closure.md").write_text(render_closure(closure))
    (out_dir / "GOLD-001-150-coverage-limitations.md").write_text(
        render_limitations(closure, cases, documents))
    print(f"closed at {closure['counts']['holdout_eligible']} eligible "
          f"({closure['counts']['human_verified']} verified), hash {digest}")
    print(f"wrote {out_dir}/GOLD-001-150-case-closure.md and "
          f"{out_dir}/GOLD-001-150-coverage-limitations.md")
    return 0


def render_closure(c: dict) -> str:
    counts, cov, lim = c["counts"], c["coverage"], c["limitations"]
    groups = "\n".join(
        f"| {g['group']} | {g['human_verified']} | {g['human_rejected']} | "
        f"**{g['holdout_eligible']}** |" for g in c["by_group"])
    return "\n".join([
        "# GOLD-001 — closure at 150",
        "",
        f"Closed {c['closed_at']} · closure hash `{c['closure_hash']}`",
        "",
        f"**{counts['holdout_eligible']} cases is the achieved GOLD benchmark-size "
        "target.** That is a size. It is not coverage, and the rest of this document is "
        "what the size does not buy.",
        "",
        "## The counts",
        "",
        "| | count |",
        "| --- | --- |",
        f"| `human_verified` | **{counts['human_verified']}** |",
        f"| `holdout_eligible` | **{counts['holdout_eligible']}** |",
        f"| `human_rejected` | {counts['human_rejected']} |",
        f"| genuine multi-hop | {counts['genuine_multi_hop']} |",
        f"| candidates reviewed | {counts['candidates_reviewed']} |",
        "",
        "Derived from the group records through `rag_v1.gold.eligibility`, not asserted. "
        "Conditions checked: " + ", ".join(f"`{x}`" for x in c["conditions_checked"]) + ".",
        "",
        "| group | `human_verified` | `human_rejected` | `holdout_eligible` |",
        "| --- | --- | --- | --- |",
        groups,
        "",
        "## What 150 does not mean",
        "",
        f"- **Provider imbalance.** {lim['provider_imbalance']}",
        f"- **Category imbalance.** {lim['category_imbalance']}",
        f"- **Genuine multi-hop is n={counts['genuine_multi_hop']}.** {lim['genuine_multi_hop']}",
        f"- **The preregistered pilot sequence was not followed.** {lim['protocol_deviation']} "
        "— see `GOLD-001-protocol-deviation-001.md`. The 60 admitted cases are not that "
        "pilot and must never be described as it.",
        f"- **Corpus reproduction is {lim['corpus_reproduction']}.** Reaching 150 does "
        "not certify the frozen corpus.",
        f"- **Retrieval remains {lim['retrieval']}.** No system may be run against these "
        "cases until the corpus gate clears.",
        "",
        "## Coverage, as measured",
        "",
        "| dimension | distribution |",
        "| --- | --- |",
        f"| provider | {fmt(cov['provider'])} |",
        f"| reasoning type | {fmt(cov['reasoning_type'])} |",
        f"| evidence shape | {fmt(cov['evidence_shape'])} |",
        f"| distinct source documents | {cov['distinct_source_documents']} |",
        f"| cases from the single most-used document | {cov['cases_from_the_top_document']} |",
        f"| ambiguity cases | {cov['ambiguity_cases']} |",
        "",
        "## The 60 admitted cases",
        "",
        f"Admitted from `{c['admission']['packet']}` "
        f"(sha256 `{c['admission']['packet_sha256']}`), bound by evidence identity rather "
        f"than by the short HA label, on the decision of `{c['admission']['reviewer']}`. "
        f"{c['alternate_packet']}",
        "",
        f"- **HA-15** carries `{c['admission']['ha15_override']['anaphora_status']}` with "
        "the detector's finding retained — "
        f"_{c['admission']['ha15_override']['finding_retained']}_ — and an explicit "
        f"`{c['admission']['ha15_override']['override_reviewer']}` override.",
        f"- **HA-47** was repaired to one contiguous span "
        f"{c['admission']['ha47_repair']['to']['char_start']}:"
        f"{c['admission']['ha47_repair']['to']['char_end']} "
        f"(`{c['admission']['ha47_repair']['to']['evidence_hash']}`), recomputed from the "
        "frozen source. Reason: "
        + ", ".join(f"`{r}`" for r in c["admission"]["ha47_repair"]["reason"]) + ". The "
        "pre-repair spans and hashes are kept in the record's revision history; a "
        "paragraph break is present and, read from the predicate, does not block "
        "eligibility.",
        "",
        "## Splits are not frozen",
        "",
        f"`holdout_frozen` is **false**. {c['reason_not_frozen']}",
        "",
        "## Untouched",
        "",
        "SYSTEM-A and SYSTEM-B remain frozen and unexecuted. `retrieval_was_not_run` is "
        "true and `systems_executed` is empty. No candidate selection has seen a "
        "retrieval outcome, which is the property that makes a future holdout worth "
        "having.",
        "",
    ])


def render_limitations(c: dict, cases: list[dict], documents: Counter) -> str:
    cov = c["coverage"]
    top = documents.most_common(5)
    total = len(cases)
    return "\n".join([
        "# GOLD-001 — coverage limitations at 150",
        "",
        f"As of {c['closed_at']}. Every figure is counted from the "
        f"{total} eligible records.",
        "",
        "The benchmark reached its size target. This document is the case against "
        "reading that as readiness.",
        "",
        "## Provider distribution",
        "",
        table(cov["provider"], total),
        "",
        "A per-provider number from this set measures the larger provider's "
        "documentation and, for the smaller one, a sample too thin to separate a real "
        "difference from noise.",
        "",
        "## Category distribution",
        "",
        table(cov["reasoning_type"], total),
        "",
        "An unweighted score over these cases is close to a score over the largest "
        "category alone. Any per-category claim needs its own n reported beside it.",
        "",
        "## Evidence shape",
        "",
        table(cov["evidence_shape"], total),
        "",
        "## Genuine multi-hop",
        "",
        f"**{c['counts']['genuine_multi_hop']} case"
        f"{'s' if c['counts']['genuine_multi_hop'] != 1 else ''}"
        f"{': ' + ', '.join(cov['genuine_multi_hop_ids']) if cov['genuine_multi_hop_ids'] else ''}.** "
        "Two independent searches of this corpus — bridge-pair and dependency-first — "
        "produced one composable chain between them. That is a property of the corpus, "
        "not a tuning failure, and it means this benchmark cannot answer a question "
        "about multi-hop retrieval no matter how large the total grows.",
        "",
        "## Source-document concentration",
        "",
        f"The {total} eligible cases are anchored in "
        f"{cov['distinct_source_documents']} distinct document versions.",
        "",
        "| document version | cases | share |",
        "| --- | --- | --- |",
        "\n".join(f"| `{v}` | {n} | {n / total:.0%} |" for v, n in top),
        "",
        f"The most-used single document supplies {cov['cases_from_the_top_document']} "
        f"cases ({cov['cases_from_the_top_document'] / total:.0%}). A retrieval system "
        "that happens to chunk that document well will look better than it is.",
        "",
        "## Ambiguity cases",
        "",
        f"**{cov['ambiguity_cases']}**"
        + (f": {', '.join(cov['ambiguity_case_ids'])}." if cov["ambiguity_case_ids"]
           else ".")
        + " At this count the set cannot measure whether a system declines to answer an "
        "under-specified question; it can only show that the category exists.",
        "",
        f"{cov['cases_with_no_recorded_reasoning_type']} eligible cases carry no "
        "`reasoning_type` at all — batches 001 and 002 predate the field. They are "
        "counted separately above rather than folded into a category they were never "
        "assigned, and any per-category analysis has to decide what to do with them.",
        "",
        "## Protocol deviation",
        "",
        f"{c['limitations']['protocol_deviation']} — the preregistered 10-case "
        "NO_BUILDER-only pilot was not run before the 60-case derivative was authored. "
        "See `GOLD-001-protocol-deviation-001.md`. Those 60 cases are not that pilot.",
        "",
        "## Corpus reproduction",
        "",
        f"Reproduction is {c['limitations']['corpus_reproduction']}. Retrieval is "
        f"{c['limitations']['retrieval']}: reaching 150 admitted cases says nothing "
        "about whether the frozen corpus those cases point into can be reconstituted.",
        "",
    ])


def fmt(dist: dict[str, int]) -> str:
    return ", ".join(f"{k} {v}" for k, v in dist.items())


def table(dist: dict[str, int], total: int) -> str:
    rows = "\n".join(f"| {k} | {v} | {v / total:.0%} |" for k, v in dist.items())
    return "\n".join(["| value | cases | share |", "| --- | --- | --- |", rows])


if __name__ == "__main__":
    raise SystemExit(main())
