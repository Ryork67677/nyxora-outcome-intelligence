#!/usr/bin/env python3
"""Project gold150-v1 *development* cases into the EXP-014R harness JSONL shape.

Loads only ``evals/splits/gold150-v1/development.json``. Never opens holdout.json,
holdout.lock.json (except existence is irrelevant), the holdout access log, or
validation. Gold source files are scanned, but only records whose candidate_id is in
the development allowlist are retained; other IDs are discarded without being stored.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from rag_v1.db import connect
from rag_v1.eval.exposure import spans_of
from rag_v1.eval.splits import load_development
from rag_v1.gold.mining import _section_for
from rag_v1.parsing import _sections_from_markdown

GOLD_SOURCES = {
    "001": "evals/gold/batch_001_v2/overlay.json",
    "002": "evals/review/gold_review_batch_002.json",
    "003": "evals/review/gold_review_batch_003.json",
    "004": "evals/review/gold_review_batch_004_final.json",
    "005": "evals/review/gold_review_batch_005_final.json",
    "006": "evals/review/gold_review_batch_006_final.json",
    "HA": "evals/review/gold_review_HA01_HA60_final.json",
}
CATEGORY_MAP = {
    "exact_lookup": "exact_lookup",
    "genuine_multi_hop": "multi_hop",
    "ambiguity_disambiguation": "ambiguous",
}


def load_gold_allowlist(allow: set[str]) -> dict[str, dict]:
    """Keep only development IDs. Never accumulate any other identifier."""
    records: dict[str, dict] = {}
    for group, rel in GOLD_SOURCES.items():
        payload = json.loads(Path(rel).read_text())
        for record in (payload.get("records") or payload.get("case_records") or []):
            cid = record.get("candidate_id")
            if cid not in allow:
                continue
            if record.get("verification_status") == "human_verified" or record.get("human_verified"):
                records[cid] = {"group": group, **record}
    return records


def derived_sections() -> dict:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT version_id, normalized_text FROM document_version WHERE status='current'"
        )
        return {version: _sections_from_markdown(text) for version, text in cur.fetchall()}


def project(out_path: Path) -> dict:
    split = load_development()
    allow = set(split["case_ids"])
    if split["count"] != 20 or len(allow) != 20:
        raise SystemExit(f"expected 20 development cases, got {split['count']}")
    gold = load_gold_allowlist(allow)
    missing = sorted(allow - set(gold))
    if missing:
        raise SystemExit(f"development cases missing from gold sources: {missing}")
    extra = sorted(set(gold) - allow)
    if extra:
        raise SystemExit("internal error: non-development IDs leaked into projection")
    sections = derived_sections()
    lines, skipped, derived_count = [], [], 0
    for case_id in split["case_ids"]:
        record = gold[case_id]
        spans = spans_of(record)
        refs = []
        for span in spans:
            source = next(
                (
                    s
                    for s in (record.get("expected_evidence") or [])
                    if s.get("char_start") == span["char_start"]
                    and s.get("version_id") == span["version_id"]
                ),
                record,
            )
            section = source.get("section_path") or (
                record.get("section_path") if not (record.get("expected_evidence") or []) else None
            )
            if not section:
                section = _section_for(sections[span["version_id"]], span["char_start"])
                derived_count += 1
            if not section:
                skipped.append({"case_id": case_id, "reason": "no section_path"})
                continue
            refs.append(
                {
                    "version_id": span["version_id"],
                    "section_path": section,
                    "char_start": span["char_start"],
                    "char_end": span["char_end"],
                }
            )
        if not refs:
            skipped.append({"case_id": case_id, "reason": "no usable anchor"})
            continue
        reasoning = record.get("reasoning_type")
        lines.append(
            {
                "case_id": case_id,
                "category": CATEGORY_MAP.get(reasoning, "normal"),
                "question": record.get("question") or record.get("proposed_question"),
                "expected_evidence": refs,
                "expected_abstain": False,
                "notes": json.dumps(
                    {
                        "group": record["group"],
                        "provider": record.get("provider"),
                        "reasoning_type": reasoning,
                        "secondary_category": record.get("secondary_category"),
                        "evidence_shape": record.get("evidence_shape") or "single_span",
                        "document_title": record.get("document_title"),
                    }
                ),
            }
        )
    if skipped:
        raise SystemExit(f"refusing: skipped {skipped}")
    if len(lines) != 20:
        raise SystemExit(f"refusing: projected {len(lines)} != 20")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(line, ensure_ascii=False) for line in lines) + "\n"
    out_path.write_text(text, encoding="utf-8")
    return {
        "out": str(out_path),
        "cases": len(lines),
        "spans": sum(len(line["expected_evidence"]) for line in lines),
        "section_path_derived": derived_count,
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "holdout_loaded": False,
        "validation_loaded": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", default="experiments/EXP-015/development.jsonl"
    )
    args = parser.parse_args()
    payload = project(Path(args.out))
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
