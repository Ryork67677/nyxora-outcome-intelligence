#!/usr/bin/env python3
"""GOLD-001: mine candidate evidence and export a review batch.

Produces a batch of 15-20 candidates as machine-readable JSON and human-readable
Markdown. Nothing here is gold: every candidate leaves as ``candidate_unverified``
and carries the surrounding source text a reviewer needs to judge it.

Retrieval is never run. Candidate selection must not be influenced by what either
system succeeds or fails on, which is what keeps the eventual holdout honest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.db import connect
from rag_v1.gold.mining import (
    CANDIDATE_SCHEMA_VERSION,
    mine_explicit_statements,
    mine_table_parameters,
)
from rag_v1.parsing import _sections_from_markdown

SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"


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
             "url": r[4], "captured_at": str(r[5])} for r in cur.fetchall()]


def dedupe(candidates: list) -> list:
    """Drop repeated questions, repeated claims and re-used evidence.

    The point of a larger set is more independent evidence, not a bigger n.
    """
    seen_q: set[str] = set()
    seen_claim: set[str] = set()
    seen_span: set[tuple] = set()
    out = []
    for c in candidates:
        q = " ".join(c.proposed_question.lower().split())
        claim = " ".join(" ".join(c.proposed_atomic_claims).lower().split())
        span = (c.version_id, c.char_start, c.char_end)
        if q in seen_q or span in seen_span or (claim and claim in seen_claim):
            continue
        seen_q.add(q)
        seen_span.add(span)
        if claim:
            seen_claim.add(claim)
        out.append(c)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--size", type=int, default=18)
    parser.add_argument("--seed", type=int, default=20250819)
    parser.add_argument("--out-dir", default="evals/review")
    args = parser.parse_args()

    with connect() as conn, conn.cursor() as cur:
        docs = load_docs(cur)
    for doc in docs:
        doc["sections"] = _sections_from_markdown(doc["text"])

    pool = []
    for doc in docs:
        pool.extend(mine_table_parameters(doc, limit=2))
        pool.extend(mine_explicit_statements(doc, limit=1))
    pool = dedupe(pool)

    # Deterministic, provider-balanced selection. The corpus is 139 Anthropic to 63
    # OpenAI; letting that ratio pick the batch would starve OpenAI coverage.
    rng = random.Random(args.seed + args.batch)
    by_provider: dict[str, list] = {}
    for c in pool:
        by_provider.setdefault(c.provider, []).append(c)
    for group in by_provider.values():
        group.sort(key=lambda c: (c.version_id, c.char_start))
        rng.shuffle(group)

    # Prefer high-confidence table rows, then fill with review-flagged prose.
    selected: list = []
    providers = sorted(by_provider)
    for confidence in ("high", "medium", "low"):
        index = 0
        while len(selected) < args.size:
            added = False
            for provider in providers:
                group = by_provider[provider]
                picks = [c for c in group if c.generator_confidence == confidence
                         and c not in selected]
                if index < len(picks) and len(selected) < args.size:
                    selected.append(picks[index])
                    added = True
            if not added:
                break
            index += 1

    for position, candidate in enumerate(selected, start=1):
        candidate.candidate_id = f"GOLD-B{args.batch:03d}-{position:02d}"

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"gold_review_batch_{args.batch:03d}"

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                         stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        commit = None

    records = [c.to_dict() for c in selected]
    payload = {
        "batch": args.batch,
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "corpus_snapshot": SNAPSHOT,
        "selection_seed": args.seed + args.batch,
        "candidate_pool_size": len(pool),
        "candidates": len(records),
        "by_provider": dict(Counter(c["provider"] for c in records)),
        "by_evidence_kind": dict(Counter(c["evidence_kind"] for c in records)),
        "by_confidence": dict(Counter(c["generator_confidence"] for c in records)),
        "needs_human_interpretation": sum(1 for c in records if c["needs_human_interpretation"]),
        "verification_status": "candidate_unverified — nothing in this file is gold",
        "retrieval_was_not_run": True,
        "records": records,
    }
    json_path = out_dir / f"{stem}.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    payload["batch_sha256"] = hashlib.sha256(json_path.read_bytes()).hexdigest()
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")

    # --- readable packet ---------------------------------------------------
    lines = [
        f"# Gold review batch {args.batch:03d}", "",
        (f"**{len(records)} candidates · corpus snapshot `{SNAPSHOT}` · "
         f"generated {payload['generated_at']}**"), "",
        ("Nothing in this file is ground truth. Every candidate is "
         "`candidate_unverified`. The evidence below is quoted verbatim from the "
         "frozen corpus and is authoritative for this review — **do not consult live "
         "documentation**, which may have changed since the snapshot."), "",
        ("For each candidate, judge the *proposed* question, answer and claims "
         "against the evidence and its surrounding context, and return the verdict "
         "schema in `docs/GOLD-REVIEW-PROCEDURE.md`."), "",
        "---", "",
    ]
    for c in records:
        lines += [
            f"## {c['candidate_id']}", "",
            f"- **provider**: {c['provider']}",
            f"- **document**: {c['document_title']}",
            f"- **section**: {' › '.join(c['section_path'])}",
            f"- **source span**: `{c['version_id']}` chars {c['char_start']}–{c['char_end']}",
            f"- **evidence kind**: `{c['evidence_kind']}`",
            f"- **binding**: {c['binding']}",
            f"- **generator confidence**: {c['generator_confidence']}",
            f"- **needs human interpretation**: {c['needs_human_interpretation']}", "",
            "**Proposed question** (a suggestion, not gold)", "",
            f"> {c['proposed_question']}", "",
            f"**Proposed answer**: {c['proposed_answer'] or '_none — reviewer to write_'}", "",
            "**Proposed atomic claims**: " + (
                ", ".join(f"`{x}`" for x in c["proposed_atomic_claims"]) or "_none_"), "",
            f"**Generator notes**: {c['generator_notes']}", "",
            "### Evidence (verbatim, authoritative)", "", "```",
            c["evidence_text"], "```", "",
            "<details><summary>Context before</summary>", "", "```",
            c["context_before"][-900:], "```", "", "</details>", "",
            "<details><summary>Context after</summary>", "", "```",
            c["context_after"][:900], "```", "", "</details>", "", "---", "",
        ]
    md_path = out_dir / f"{stem}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"pool {len(pool)} candidates -> batch {args.batch:03d} with {len(records)}")
    print("  by provider   :", payload["by_provider"])
    print("  by kind       :", payload["by_evidence_kind"])
    print("  by confidence :", payload["by_confidence"])
    print("  needs review  :", payload["needs_human_interpretation"])
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
