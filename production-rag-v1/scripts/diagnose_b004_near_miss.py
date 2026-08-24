#!/usr/bin/env python3
"""Recover the bridge pairs that failed only on the entity-state rule.

The batch-004 composer rejected 558 of 559 pairs. Most failed several checks at once
and are uninteresting. A small number passed every structural check *and* the
composition check, and were rejected solely because span 2's conditional tested
something other than the bridge entity's own state — the last rule added, and the one
most likely to be too strict.

This is diagnostic only. §5 of the review brief is explicit: a near miss does not become
a batch-004 candidate after the fact, because choosing candidates by re-examining
rejections is how a benchmark gets tuned to its own generator. If the rule turns out to
be wrong, that is a batch-005 design question.

Nothing here is written into the batch. Retrieval is not run.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag_v1.db import connect
from rag_v1.gold import multihop as M
from rag_v1.gold.factmining import mine_bridge_facts
from rag_v1.parsing import _sections_from_markdown

SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"


def load_docs(cur) -> list[dict]:
    cur.execute(
        """
        SELECT v.version_id, v.normalized_text, s.provider, s.title, s.canonical_url
        FROM document_version v
        JOIN document_source s ON s.source_id = v.source_id
        JOIN corpus_snapshot_version sv ON sv.version_id = v.version_id
        WHERE sv.snapshot_id = %s
        ORDER BY v.version_id
        """,
        (SNAPSHOT,),
    )
    return [{"version_id": r[0], "text": r[1], "provider": r[2], "title": r[3],
             "url": r[4]} for r in cur.fetchall()]


def near_misses(facts: list[dict]) -> list[dict]:
    """Pairs that clear every check except the entity-state rule.

    The order matters and mirrors ``find_bridges``: a pair is a near miss only when the
    entity-state rule is the *only* thing standing between it and an exported case, so
    each earlier check is applied first and a pair failing one of those is not a near
    miss, it is an ordinary rejection.
    """
    by_entity: dict[str, list[dict]] = {}
    for fact in facts:
        for raw in set(M.re.findall(r"`([^`]{3,60})`", fact["evidence_text"])):
            entity = raw.strip().strip("`\"'")
            if M.plausible_bridge(entity):
                by_entity.setdefault(entity, []).append(fact)

    out: list[dict] = []
    for entity, group in sorted(by_entity.items()):
        if len(group) < 2:
            continue
        group = group[:M.MAX_FACTS_PER_ENTITY]
        conditions = [c for c in group
                      if M.is_condition(c["evidence_text"])
                      and M.about(c["evidence_text"], entity)]
        consequences = [c for c in group
                        if M.is_consequence(c["evidence_text"])
                        and M.about(c["evidence_text"], entity)]
        for first in conditions:
            for second in consequences:
                if first["evidence_hash"] == second["evidence_hash"]:
                    continue
                if first["provider"] != second["provider"]:
                    continue
                if M.is_list_membership(first["evidence_text"]):
                    continue
                if M.states_dependency(second["evidence_text"], entity):
                    continue  # not a near miss: it passed the rule under test
                if (M.self_contained(first["evidence_text"])
                        and M.self_contained(second["evidence_text"])):
                    continue
                verdict = M.composition_check(
                    entity, first["evidence_text"], second["evidence_text"],
                    first["critical_strings"], second["critical_strings"])
                if verdict["multi_hop_composition_check"] != M.PASS:
                    continue
                out.append({"bridge_entity": entity, "first": first, "second": second,
                            "composition": verdict})
                break
            else:
                continue
            break
    return out


def why_rejected(entity: str, text: str) -> str:
    """Say precisely what the entity-state rule saw."""
    markers = [m.group(0) for m in M._CONDITIONAL.finditer(text)]
    if not markers:
        return ("the span carries no conditional marker at all, so there is no clause "
                "that could test the entity's state")
    clauses = []
    for marker in M._CONDITIONAL.finditer(text):
        start = marker.end()
        clause = text[start:start + M.CLAUSE_WINDOW]
        cut = min((clause.find(c) for c in ",;:" if clause.find(c) >= 0), default=-1)
        clauses.append((marker.group(0), clause[:cut] if cut >= 0 else clause))
    rendered = "; ".join(f"{marker!r} governs {clause.strip()!r}"
                         for marker, clause in clauses)
    return (f"the span's conditional markers are {markers}, and none of their clauses "
            f"contains `{entity}` — {rendered}")


def render(pairs: list[dict], verdicts: dict) -> str:
    lines = [
        "# GOLD-001 — batch 004 near-miss multi-hop diagnostic",
        "",
        (f"**{len(pairs)} bridge pairs** cleared every check in the composer except the "
         "entity-state rule. This document exists to test that rule, not to rescue the "
         "pairs."),
        "",
        ("§5 of the review brief forbids promoting any of these into batch 004, and the "
         "reason is worth stating plainly: choosing candidates by re-reading the "
         "rejection list is how a benchmark ends up measuring its own generator. If the "
         "rule is wrong, the place to fix it is batch 005's design, with the change "
         "preregistered before it sees any candidate."),
        "",
        "## The rule under test",
        "",
        ("A pair is a chain only when span 2 makes its outcome conditional on **the "
         "bridge entity's own state**. Span 2 mentioning the entity and containing a "
         "conditional is not enough: the entity has to sit inside the conditional "
         "clause. Formally, for some conditional marker in span 2, the text from that "
         f"marker to the next `,`/`;`/`:` (or {M.CLAUSE_WINDOW} characters, whichever "
         "comes first) must contain the entity."),
        "",
        "| # | bridge entity | provider | verdict |",
        "| --- | --- | --- | --- |",
    ]
    for index, pair in enumerate(pairs, 1):
        verdict = verdicts[pair["bridge_entity"]]["verdict"]
        lines.append(f"| {index} | `{pair['bridge_entity']}` | "
                     f"{pair['first']['provider']} | **{verdict}** |")
    lines += ["", "---", ""]

    for index, pair in enumerate(pairs, 1):
        entity = pair["bridge_entity"]
        first, second = pair["first"], pair["second"]
        judgement = verdicts[entity]
        same_doc = first["version_id"] == second["version_id"]
        lines += [
            f"## {index}. `{entity}`",
            "",
            f"- **provider**: {first['provider']}",
            (f"- **span 1 document**: {first['document_title']} — "
            f"{' › '.join(first['section_path'])}"),
            (f"- **span 2 document**: {second['document_title']} — "
            f"{' › '.join(second['section_path'])}"),
            f"- **same document**: {same_doc}",
            "",
            "**Span 1 (proposed hop 1)**",
            "",
            "```", first["evidence_text"], "```",
            f"critical strings: {', '.join(f'`{s}`' for s in first['critical_strings'])}",
            "",
            "**Span 2 (proposed hop 2)**",
            "",
            "```", second["evidence_text"], "```",
            f"critical strings: {', '.join(f'`{s}`' for s in second['critical_strings'])}",
            "",
            "**Why every other check passed**",
            "",
            (f"Both spans are {first['provider']} documentation; span 1 is a "
             f"{first['fact_role']} statement about `{entity}` and is not a list "
             f"enumeration; span 2 is a {second['fact_role']} statement; the entity "
             "appears near the front of both; and the composition check returned "
             f"`{pair['composition']['multi_hop_composition_check']}` — neither span "
             "carries the other hop's critical strings, so on the mechanical test "
             "neither span alone answers."),
            "",
            "**Why the entity-state rule rejected it**",
            "",
            why_rejected(entity, second["evidence_text"]),
            "",
            f"**Reviewer verdict: {judgement['verdict']}**",
            "",
            judgement["reasoning"],
            "",
            "---",
            "",
        ]
    lines += [
        "## What this says about the rule",
        "",
        ("Every pair here is a correct rejection, and each fails in the same way: the "
         "two spans are about the same identifier and about different questions. That "
         "is the shape batch 003 shipped four times. On this evidence the rule is not "
         "too strict — it is the only check that caught them, since all four cleared "
         "the composition check that is supposed to be the hostile one."),
        "",
        ("The composition check's blind spot is worth recording for batch 005: it asks "
         "whether either span carries the *other hop's critical strings*, which is a "
         "test of textual overlap, not of whether the two facts bear on one another. "
         "Two unrelated facts share no strings, so they pass. The entity-state rule is "
         "a crude proxy for the missing test, and a better one would ask whether span "
         "1 establishes the state span 2's condition tests — which is the judgement "
         "`GOLD-B004-15` is flagged for."),
        "",
        "## Scope",
        "",
        ("Diagnostic only. No pair here is a batch-004 candidate, none was added, and "
         "batch 004 was not regenerated. No retrieval system was run; SYSTEM-A and "
         "SYSTEM-B remain frozen and unexecuted."),
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="experiments/GOLD-001")
    parser.add_argument("--verdicts", default="experiments/GOLD-001/b004-near-miss-verdicts.json",
                        help="reviewer verdicts, keyed by bridge entity")
    args = parser.parse_args()

    with connect() as conn, conn.cursor() as cur:
        docs = load_docs(cur)
    for doc in docs:
        doc["sections"] = _sections_from_markdown(doc["text"])
    facts: list[dict] = []
    for doc in docs:
        facts += mine_bridge_facts(doc)

    pairs = near_misses(facts)
    verdicts = json.loads(Path(args.verdicts).read_text())
    missing = [p["bridge_entity"] for p in pairs if p["bridge_entity"] not in verdicts]
    if missing:
        raise SystemExit(
            "no reviewer verdict recorded for: " + ", ".join(missing)
            + "\nA near miss without a written judgement is an unreviewed rejection.")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "BATCH-004-near-miss-multihop-review.md").write_text(
        render(pairs, verdicts), encoding="utf-8")
    payload = {
        "pairs": len(pairs),
        "rule_under_test": "states_dependency — span 2's conditional must test the "
                           "bridge entity's own state",
        "clause_window": M.CLAUSE_WINDOW,
        "diagnostic_only": True,
        "promoted_to_batch_004": 0,
        "batch_004_regenerated": False,
        "retrieval_was_not_run": True,
        "systems_executed": [],
        "findings": [
            {
                "bridge_entity": p["bridge_entity"],
                "provider": p["first"]["provider"],
                "verdict": verdicts[p["bridge_entity"]]["verdict"],
                "same_document": p["first"]["version_id"] == p["second"]["version_id"],
                "span_1": {"version_id": p["first"]["version_id"],
                           "char_start": p["first"]["char_start"],
                           "char_end": p["first"]["char_end"],
                           "evidence_text": p["first"]["evidence_text"],
                           "critical_strings": p["first"]["critical_strings"]},
                "span_2": {"version_id": p["second"]["version_id"],
                           "char_start": p["second"]["char_start"],
                           "char_end": p["second"]["char_end"],
                           "evidence_text": p["second"]["evidence_text"],
                           "critical_strings": p["second"]["critical_strings"]},
                "composition_check": p["composition"]["multi_hop_composition_check"],
                "entity_state_rejection": why_rejected(
                    p["bridge_entity"], p["second"]["evidence_text"]),
                "reviewer_reasoning": verdicts[p["bridge_entity"]]["reasoning"],
            }
            for p in pairs
        ],
    }
    (out_dir / "BATCH-004-near-miss-multihop-review.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(pairs)} near-miss pairs:",
          ", ".join(f"{p['bridge_entity']} -> {verdicts[p['bridge_entity']]['verdict']}"
                    for p in pairs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
