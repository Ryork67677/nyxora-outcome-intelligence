#!/usr/bin/env python3
"""GOLD-001: generate batch 003 — provider balance and question-type diversity.

Batch 002 fixed evidence integrity and, in doing so, narrowed: 15 Anthropic to 3 OpenAI,
and a structural half drawn from three question templates. A benchmark built that way
measures one phrasing of one fact shape.

Batch 003 keeps every batch-001/002 safety rule and changes what selection optimises.
Candidates are mined from sentence and definition shapes rather than table columns, they
ship complete — question, answer, atomic claims, critical strings — and selection
balances provider and category instead of taking whatever the confidence order offers.

Retrieval is never run. No candidate is chosen, ordered or worded because of what any
system does with it; that is the property that makes a future holdout worth having.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.db import connect
from rag_v1.gold.mining_v3 import (
    EVIDENCE_HARD_CAP,
    EVIDENCE_SOFT_CAP,
    SCHEMA_VERSION,
    compose_multi_hop,
    mine_definition_bullets,
    mine_prose,
    mine_row_facts,
)
from rag_v1.gold.normalisation import contains_claim_string
from rag_v1.parsing import _sections_from_markdown

SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"
#: Earlier work whose questions and spans batch 003 must not re-use.
PRIOR = (
    "evals/review/gold_review_batch_001.json",
    "evals/review/gold_review_batch_002.json",
)
DEVELOPMENT = "evals/development/v1.jsonl"
#: Roughly what the batch is aiming at. Deviating is allowed; faking it is not.
PROVIDER_TARGET = {"openai": (8, 10), "anthropic": (8, 10)}
CATEGORY_TARGET = {
    "exact_constraint": (4, 5),
    "error_behavior": (3, 4),
    "multi_hop": (3, 4),
    "configuration_interaction": (2, 3),
    "lifecycle": (2, 3),
}


def load_docs(cur) -> list[dict]:
    cur.execute(
        """
        SELECT v.version_id, v.normalized_text, s.provider, s.title, s.canonical_url,
               v.captured_at
        FROM document_version v
        JOIN document_source s ON s.source_id = v.source_id
        JOIN corpus_snapshot_version sv ON sv.version_id = v.version_id
        WHERE sv.snapshot_id = %s
        ORDER BY v.version_id
        """,
        (SNAPSHOT,),
    )
    return [{"version_id": r[0], "text": r[1], "provider": r[2], "title": r[3],
             "url": r[4], "captured_at": r[5]} for r in cur.fetchall()]


def normalise_question(question: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", question.lower()).split())


def prior_material() -> tuple[set[str], set[tuple], set[str]]:
    """Questions, spans and facts already spent, so batch 003 brings new information."""
    questions: set[str] = set()
    spans: set[tuple] = set()
    identifiers: set[str] = set()
    for path in PRIOR:
        for record in json.loads(Path(path).read_text())["records"]:
            questions.add(normalise_question(record["proposed_question"]))
            spans.add((record["version_id"], record["char_start"], record["char_end"]))
            spans.add(((record["version_id"], record["char_start"],
                        record["char_end"]),))
            for revision in record.get("anchor_revisions", []):
                spans.add(((record["version_id"], revision["old_char_start"],
                            revision["old_char_end"]),))
            identifiers.update(re.findall(r"`([^`]+)`", record["proposed_question"]))
    development = Path(DEVELOPMENT)
    if development.exists():
        for line in development.read_text().splitlines():
            if line.strip():
                case = json.loads(line)
                questions.add(normalise_question(case["question"]))
                spans.add(tuple(sorted(
                    (ref.get("version_id"), ref.get("char_start"), ref.get("char_end"))
                    for ref in case.get("expected_evidence", []))))
    return questions, spans, identifiers


def precheck(candidate: dict) -> list[str]:
    """Can this candidate ever become holdout-eligible? Not whether it should be."""
    failures = []
    spans = candidate.get("expected_evidence") or [candidate]
    for span in spans:
        text = span["evidence_text"]
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != span["evidence_hash"]:
            failures.append("evidence hash does not match the evidence text")
        if not (0 <= span["char_start"] < span["char_end"]):
            failures.append("invalid character span")
    if not candidate.get("version_id"):
        failures.append("no version_id")
    if not candidate.get("proposed_atomic_claims"):
        failures.append("no atomic claims")
    if not candidate.get("critical_strings"):
        failures.append("no critical strings")
    combined = " \n".join(s["evidence_text"] for s in spans)
    outside = [s for s in candidate.get("critical_strings", [])
               if not contains_claim_string(combined, s)]
    if outside:
        failures.append(f"critical strings outside the evidence: {outside}")
    if candidate["evidence_char_length"] > EVIDENCE_HARD_CAP:
        failures.append(f"evidence over the {EVIDENCE_HARD_CAP}-character cap")
    if candidate.get("chunk_id") is not None:
        failures.append("chunk id used as ground truth")
    if not candidate.get("retrieval_was_not_run"):
        failures.append("retrieval leakage: candidate does not assert retrieval_was_not_run")
    return failures


def select(pool: list[dict], size: int) -> tuple[list[dict], Counter]:
    """Fill provider and category floors first, then the remainder by document spread.

    Batch 002 ordered by confidence and ended up 15-to-3, because the mechanism that
    produced the most confident candidates was also the one concentrated in one
    provider's docs. Floors first is the fix.
    """
    chosen: list[dict] = []
    reasons: Counter = Counter()
    seen_documents: Counter = Counter()

    def take(predicate, quota: int) -> None:
        for candidate in pool:
            if len(chosen) >= size or sum(1 for c in chosen if predicate(c)) >= quota:
                break
            if candidate in chosen or not predicate(candidate):
                continue
            # One large page should not supply the batch.
            if seen_documents[candidate["document_title"]] >= 2:
                reasons["document_concentration"] += 1
                continue
            chosen.append(candidate)
            seen_documents[candidate["document_title"]] += 1

    for category, (floor, _) in CATEGORY_TARGET.items():
        take(lambda c, k=category: c["proposed_category"] == k, floor)
    for provider, (floor, _) in PROVIDER_TARGET.items():
        take(lambda c, p=provider: c["provider"] == p, floor)

    # Fill the remainder round-robin across categories rather than in pool order. A
    # plain fill takes whatever the miner produced most of, which is how batch 002's
    # structural half became three question templates.
    ceilings = {k: v[1] for k, v in CATEGORY_TARGET.items()}
    for step in range(1, 6):
        for category in CATEGORY_TARGET:
            take(lambda c, k=category: c["proposed_category"] == k,
                 min(ceilings[category] + step - 1, size))
        if len(chosen) >= size:
            break
    take(lambda c: True, size)
    return chosen[:size], reasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=20)
    parser.add_argument("--out-dir", default="evals/review")
    parser.add_argument("--report-dir", default="experiments/GOLD-001")
    args = parser.parse_args()

    with connect() as conn, conn.cursor() as cur:
        docs = load_docs(cur)
    for doc in docs:
        doc["sections"] = _sections_from_markdown(doc["text"])

    pool: list[dict] = []
    for doc in docs:
        pool += mine_prose(doc, limit=4)
        pool += mine_row_facts(doc, limit=2)
        pool += mine_definition_bullets(doc, limit=2)
    mined = len(pool)

    # Compose multi-hop cases first, then drop the singletons they consumed: shipping
    # both a composite and its own members would put the same fact in the batch twice.
    composites = compose_multi_hop(pool, limit=4)
    consumed = {span["evidence_hash"]
                for composite in composites
                for span in composite["expected_evidence"]}
    pool = [c for c in pool if c["evidence_hash"] not in consumed] + composites

    removed: Counter = Counter()
    questions, spans, _prior_identifiers = prior_material()
    kept: list[dict] = []
    seen_questions: set[str] = set()
    seen_spans: set[tuple] = set()
    for candidate in sorted(pool, key=lambda c: (c["version_id"], c["char_start"])):
        key = normalise_question(candidate["proposed_question"])
        # A multi-span candidate is keyed on all of its spans, so it does not collide
        # with a single-span candidate that happens to start in the same place.
        span = tuple(sorted(
            (s["version_id"], s["char_start"], s["char_end"])
            for s in (candidate.get("expected_evidence") or [candidate])))
        if key in questions or key in seen_questions:
            removed["duplicate_question"] += 1
            continue
        if span in spans or span in seen_spans:
            removed["duplicate_evidence"] += 1
            continue
        if candidate["evidence_char_length"] > EVIDENCE_HARD_CAP:
            removed["oversized_evidence"] += 1
            continue
        failures = precheck(candidate)
        if failures:
            removed["failed_precheck"] += 1
            continue
        candidate["precheck_holdout_ready"] = True
        candidate["precheck_failures"] = []
        seen_questions.add(key)
        seen_spans.add(span)
        kept.append(candidate)

    chosen, selection_reasons = select(kept, args.size)
    removed.update(selection_reasons)
    removed["not_selected_diversity"] = len(kept) - len(chosen)

    for position, candidate in enumerate(sorted(
            chosen, key=lambda c: (c["provider"], c["proposed_category"],
                                   c["document_title"])), start=1):
        candidate["candidate_id"] = f"GOLD-B003-{position:02d}"
    chosen.sort(key=lambda c: c["candidate_id"])

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                         stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        commit = None

    lengths = sorted(c["evidence_char_length"] for c in chosen)
    payload = {
        "batch": 3,
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "corpus_snapshot": SNAPSHOT,
        "candidate_pool_size": mined,
        "candidates": len(chosen),
        "by_provider": dict(Counter(c["provider"] for c in chosen)),
        "by_category": dict(Counter(c["proposed_category"] for c in chosen)),
        "by_evidence_kind": dict(Counter(c["evidence_kind"] for c in chosen)),
        "by_confidence": dict(Counter(c["generator_confidence"] for c in chosen)),
        "unique_documents": len({c["document_title"] for c in chosen}),
        "documents_by_provider": {
            provider: len({c["document_title"] for c in chosen
                           if c["provider"] == provider})
            for provider in sorted({c["provider"] for c in chosen})},
        "needs_human_interpretation": sum(1 for c in chosen
                                          if c["needs_human_interpretation"]),
        "precheck_holdout_ready": sum(1 for c in chosen
                                      if c["precheck_holdout_ready"]),
        "evidence_length": {
            "mean": round(sum(lengths) / len(lengths), 1) if lengths else 0,
            "median": lengths[len(lengths) // 2] if lengths else 0,
            "max": max(lengths) if lengths else 0,
            "over_soft_cap": sum(1 for n in lengths if n > EVIDENCE_SOFT_CAP),
        },
        "removed": dict(removed),
        "verification_status": "candidate_unverified — nothing in this file is gold",
        "retrieval_was_not_run": True,
        "systems_executed": [],
        "records": chosen,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "gold_review_batch_003.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    payload["batch_sha256"] = hashlib.sha256(json_path.read_bytes()).hexdigest()
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")

    (out_dir / "gold_review_batch_003.md").write_text(render(payload), encoding="utf-8")
    write_report(payload, Path(args.report_dir))

    print(f"pool {mined} mined -> {len(kept)} eligible -> batch 003 with {len(chosen)}")
    print("  provider  :", payload["by_provider"])
    print("  category  :", payload["by_category"])
    print("  documents :", payload["unique_documents"],
          payload["documents_by_provider"])
    print("  evidence  : mean", payload["evidence_length"]["mean"],
          "median", payload["evidence_length"]["median"],
          "max", payload["evidence_length"]["max"])
    print("  removed   :", payload["removed"])
    return 0


def code_span(text: str) -> str:
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def render(payload: dict) -> str:
    lines: list[str] = [
        "# Gold review batch 003",
        "",
        (f"**{payload['candidates']} candidates · corpus snapshot "
         f"`{payload['corpus_snapshot']}` · generated {payload['generated_at']}**"),
        "",
        ("Nothing in this file is ground truth. Every candidate is "
         "`candidate_unverified`. The evidence is quoted verbatim from the frozen "
         "corpus and is authoritative for this review — **do not consult live "
         "documentation**, which may have changed since the snapshot."),
        "",
        ("Unlike batches 001 and 002, these ship complete: question, answer, atomic "
         "claims and the critical strings that make each claim machine-checkable. Judge "
         "the proposal against the evidence; where you disagree, say what the evidence "
         "does support."),
        "",
        (f"Provider {payload['by_provider']} · "
         f"{payload['unique_documents']} distinct documents · "
         f"median evidence {payload['evidence_length']['median']} characters."),
        "",
        "| id | provider | category | chars | question |",
        "| --- | --- | --- | --- | --- |",
    ]
    for record in payload["records"]:
        question = record["proposed_question"]
        short = question if len(question) <= 78 else question[:75] + "…"
        lines.append(f"| `{record['candidate_id'][-2:]}` | {record['provider']} | "
                     f"{record['proposed_category']} | "
                     f"{record['evidence_char_length']} | {short} |")
    lines += ["", "---", ""]

    for record in payload["records"]:
        spans = record.get("expected_evidence") or [record]
        lines += [
            f"## {record['candidate_id']}",
            "",
            f"- **provider**: {record['provider']}",
            f"- **document**: {record['document_title']}",
            f"- **section**: {' › '.join(record['section_path'])}",
            (f"- **category**: `{record['proposed_category']}` · "
             f"**evidence kind**: `{record['evidence_kind']}`"),
            (f"- **confidence**: {record['generator_confidence']} · "
             f"**precheck holdout-ready**: {record['precheck_holdout_ready']}"),
            "",
            f"**Q.** {record['proposed_question']}",
            "",
            f"**A.** {record['proposed_answer']}",
            "",
            "**Atomic claims**",
            "",
        ]
        lines += [f"  {i}. {c}" for i, c in
                  enumerate(record["proposed_atomic_claims"], 1)]
        lines += ["", "**Exact evidence**", ""]
        for index, span in enumerate(spans, 1):
            label = f" (span {index} of {len(spans)})" if len(spans) > 1 else ""
            lines += [
                (f"`{span['version_id']}` {span['char_start']}–{span['char_end']} "
                 f"({span['evidence_char_length']} chars){label}"),
                "", "```", span["evidence_text"], "```", "",
            ]
        strings = ", ".join(code_span(s) for s in record["critical_strings"])
        lines += [f"**Critical strings** (each verified inside the evidence): {strings}",
                  ""]
        if record.get("multi_hop_note"):
            lines += [f"*{record['multi_hop_note']}*", ""]
        lines += [("<details><summary>surrounding context (review only — not part "
                   "of the gold evidence)</summary>"), "", "```",
                  f"…{record['context_before'][-400:].strip()}", "  ⟦EVIDENCE⟧",
                  f"{record['context_after'][:400].strip()}…", "```", "", "</details>",
                  "", "---", ""]
    return "\n".join(lines)


def as_generated(record: dict) -> dict:
    """Recover what a miner emitted, before review rewrote it.

    Batches 001 and 002 hold post-review text. Comparing that to batch 003's
    freshly-mined proposals would compare a reviewed batch to an unreviewed one and
    flatter batch 003 for work a person did.
    """
    out = dict(record)
    for field in ("proposed_question", "proposed_answer", "proposed_atomic_claims"):
        first = next((r for r in record.get("revisions", []) if r["field"] == field),
                     None)
        if first is not None:
            out[field] = first["from"]
    return out


def compare_generations(payload: dict) -> dict:
    """Generation-quality metrics only. Retrieval is not compared, and was not run."""
    from rag_v1.gold.mining import anaphora_problem

    def measure(records: list[dict], label: str) -> dict:
        lengths = sorted(r.get("evidence_char_length",
                               r["char_end"] - r["char_start"]) for r in records)
        boundary = sum(1 for r in records
                       if r.get("evidence_kind") != "parameter_table_row"
                       and anaphora_problem(r["evidence_text"]) is not None)
        return {
            "batch": label,
            "candidates": len(records),
            "providers": dict(Counter(r["provider"] for r in records)),
            "openai_share": round(
                sum(1 for r in records if r["provider"] == "openai") / len(records), 3),
            "unique_documents": len({r["document_title"] for r in records}),
            "distinct_question_forms": len({
                " ".join(r["proposed_question"].split("`")[0].split()[:4])
                for r in records}),
            "complete_question_answer_claims": sum(
                1 for r in records
                if r["proposed_answer"] and r["proposed_atomic_claims"]),
            "with_critical_strings": sum(1 for r in records
                                         if r.get("critical_strings")),
            "needs_human_interpretation": sum(
                1 for r in records if r.get("needs_human_interpretation")),
            "anaphoric_spans": boundary,
            "evidence_median": lengths[len(lengths) // 2] if lengths else 0,
            "evidence_max": max(lengths) if lengths else 0,
        }

    out = []
    for number, path in ((1, PRIOR[0]), (2, PRIOR[1])):
        records = [as_generated(r)
                   for r in json.loads(Path(path).read_text())["records"]]
        out.append(measure(records, f"00{number} (as generated)"))
    out.append(measure(payload["records"], "003"))
    return {"note": ("Generation and evidence metrics only. No retrieval was run "
                     "against any candidate in any batch."),
            "batches": out}


def render_report(report: dict) -> str:
    comparison = report["comparison"]
    header = ("| metric | " + " | ".join(b["batch"] for b in comparison["batches"])
              + " |")
    divider = "| --- " * (len(comparison["batches"]) + 1) + "|"
    rows = []
    for key, label in (("candidates", "candidates"),
                       ("openai_share", "OpenAI share"),
                       ("unique_documents", "distinct documents"),
                       ("distinct_question_forms", "distinct question forms"),
                       ("complete_question_answer_claims",
                        "complete question+answer+claims"),
                       ("with_critical_strings", "carrying critical strings"),
                       ("needs_human_interpretation", "needing reviewer authoring"),
                       ("anaphoric_spans", "anaphoric spans"),
                       ("evidence_median", "median evidence chars"),
                       ("evidence_max", "max evidence chars")):
        values = " | ".join(
            f"{b[key]:.0%}" if key == "openai_share" else str(b[key])
            for b in comparison["batches"])
        rows.append(f"| {label} | {values} |")
    removed = "\n".join(f"| {reason.replace('_', ' ')} | {count} |"
                         for reason, count in sorted(report["removed"].items()))
    targets = report["targets"]
    category_rows = "\n".join(
        f"| `{name}` | {report['by_category'].get(name, 0)} | {low}–{high} |"
        for name, (low, high) in targets["category"].items())
    return "\n".join([
        "# GOLD-001 — batch 003 generation report",
        "",
        (f"**{report['total_candidates']} candidates** mined from a pool of "
         f"{report['candidate_pool_size']}, across "
         f"{report['unique_documents']} distinct documents. Nothing is verified; "
         "nothing is gold."),
        "",
        "## Composition",
        "",
        "| | |",
        "| --- | --- |",
        f"| provider | {report['by_provider']} |",
        f"| documents by provider | {report['documents_by_provider']} |",
        f"| evidence kind | {report['by_evidence_kind']} |",
        f"| confidence | {report['by_confidence']} |",
        (f"| complete question+answer+claims | "
         f"{report['complete_question_answer_claims']} of "
         f"{report['total_candidates']} |"),
        (f"| needing reviewer judgement (`needs_human_interpretation`) | "
         f"{report['needs_human_interpretation']} of "
         f"{report['total_candidates']} |"),
        (f"| precheck holdout-ready | {report['precheck_holdout_ready']} of "
         f"{report['total_candidates']} |"),
        "",
        "### Categories against target",
        "",
        "| category | in batch | target |",
        "| --- | --- | --- |",
        category_rows,
        "",
        "## Evidence size",
        "",
        (f"Mean {report['evidence_length']['mean']}, median "
         f"{report['evidence_length']['median']}, max "
         f"{report['evidence_length']['max']} characters. "
         f"{report['evidence_length']['over_soft_cap']} over the "
         f"{EVIDENCE_SOFT_CAP}-character soft cap, none over the "
         f"{EVIDENCE_HARD_CAP} hard cap."),
        "",
        ("Batch 002 rejected a candidate whose self-contained anchor needed 1,430 "
         "characters for one fact. Keeping spans small is not tidiness: an anchor the "
         "size of a section makes retrieval easy for the wrong reason."),
        "",
        "## Removed before export",
        "",
        "| reason | count |",
        "| --- | --- |",
        removed,
        "",
        "## Generation quality across batches",
        "",
        comparison["note"],
        "",
        header,
        divider,
        *rows,
        "",
        ("Batches 001 and 002 are measured **as generated** — the miner's original "
         "wording recovered from revision 1 — because their stored text is what review "
         "rewrote. Comparing batch 003's unreviewed proposals to a reviewed batch would "
         "credit batch 003 with a person's work."),
        "",
        "## Retrieval",
        "",
        ("No retrieval system was run against any batch-003 candidate at any point. "
         "SYSTEM-A and SYSTEM-B remain frozen and were not executed. No candidate was "
         "selected, ordered or worded because of what any system does with it."),
        "",
    ])


def check_report_consistency(report: dict) -> None:
    """Refuse to write a report that contradicts itself.

    The first batch-003 report claimed 20 of 20 precheck-ready while also counting one
    anaphoric span, and used "complete proposals" for two different quantities in two
    tables. Both were report-generation defects, not record defects — and both were
    only caught by a person reading two tables against each other. This makes the
    generator do it.
    """
    problems = []
    batch = next((b for b in report["comparison"]["batches"] if b["batch"] == "003"),
                 None)
    if batch is None:
        problems.append("the comparison has no batch 003 row")
    else:
        if batch["complete_question_answer_claims"] != \
                report["complete_question_answer_claims"]:
            problems.append(
                "complete_question_answer_claims differs between the composition and "
                f"comparison tables: {report['complete_question_answer_claims']} vs "
                f"{batch['complete_question_answer_claims']}")
        if batch["needs_human_interpretation"] != report["needs_human_interpretation"]:
            problems.append("needs_human_interpretation differs between tables")
        if batch["anaphoric_spans"] and \
                report["precheck_holdout_ready"] == report["total_candidates"]:
            problems.append(
                f"{batch['anaphoric_spans']} anaphoric span(s) counted while claiming "
                "every candidate is precheck holdout-ready — an unresolved anaphora "
                "must block the precheck")
    if problems:
        raise SystemExit("refusing to write a self-contradicting report:\n  "
                         + "\n  ".join(problems))


def write_report(payload: dict, report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "batch": 3,
        "generated_at": payload["generated_at"],
        "batch_sha256": payload["batch_sha256"],
        "total_candidates": payload["candidates"],
        "candidate_pool_size": payload["candidate_pool_size"],
        "by_provider": payload["by_provider"],
        "documents_by_provider": payload["documents_by_provider"],
        "unique_documents": payload["unique_documents"],
        "by_category": payload["by_category"],
        "by_evidence_kind": payload["by_evidence_kind"],
        "by_confidence": payload["by_confidence"],
        "needs_human_interpretation": payload["needs_human_interpretation"],
        "precheck_holdout_ready": payload["precheck_holdout_ready"],
        "evidence_length": payload["evidence_length"],
        "removed": payload["removed"],
        "retrieval_was_not_run": True,
        "systems_executed": [],
        "targets": {"provider": PROVIDER_TARGET, "category": CATEGORY_TARGET},
    }
    report["complete_question_answer_claims"] = sum(
        1 for r in payload["records"]
        if r["proposed_answer"] and r["proposed_atomic_claims"])
    report["comparison"] = compare_generations(payload)
    check_report_consistency(report)
    (report_dir / "GOLD-001-batch-003-generation-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "GOLD-001-batch-003-generation-report.md").write_text(
        render_report(report), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
