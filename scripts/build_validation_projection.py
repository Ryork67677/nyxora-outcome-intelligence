#!/usr/bin/env python3
"""Materialise the 40 frozen validation cases in the shape the EXP-014R harness reads.

The frozen split stores case identifiers; the records themselves live in the closed GOLD
files in two anchor schemas. This script joins the two without touching either, and
writes a projection the replication harness can consume unmodified.

It refuses to run if the split hash does not match the frozen manifest, and it never
opens the holdout — the loader it uses raises on a frozen holdout unless explicitly
overridden, and this script does not override it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from rag_v1.db import connect
from rag_v1.eval.exposure import spans_of
from rag_v1.eval.splits import load
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
MANIFEST = Path("experiments/EVAL-SPLIT-001/EVAL-SPLIT-001-manifest.json")
#: The harness's Category literal predates the modern reasoning vocabulary. This maps
#: onto it for schema validity only — the true reasoning_type is carried in `notes` and
#: is what every breakdown in the report is computed from. Nothing about a case changes.
CATEGORY_MAP = {
    "exact_lookup": "exact_lookup",
    "genuine_multi_hop": "multi_hop",
    "ambiguity_disambiguation": "ambiguous",
}


def load_gold() -> dict[str, dict]:
    records = {}
    for group, rel in GOLD_SOURCES.items():
        payload = json.loads(Path(rel).read_text())
        for record in (payload.get("records") or payload.get("case_records") or []):
            if (record.get("verification_status") == "human_verified"
                    or record.get("human_verified")):
                records[record["candidate_id"]] = {"group": group, **record}
    return records


def derived_sections() -> dict:
    """Section paths recomputed from the frozen corpus with the frozen parser.

    Sixteen HA records carry an anchor but no ``section_path``; the harness's overlap
    test needs one. The field is a deterministic function of (version_id, char_start)
    under parser v1.0, and derivation reproduces 97 of the 98 stored values elsewhere in
    the benchmark, so recovering it is reconstruction rather than invention. The single
    disagreement (GOLD-B003-06) is recorded in the report; it is in the holdout and does
    not affect this run.

    A stored value always wins. Nothing is written back to any GOLD record.
    """
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT version_id, normalized_text FROM document_version "
                    "WHERE status='current'")
        return {version: _sections_from_markdown(text)
                for version, text in cur.fetchall()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="evals/splits/gold150-v1/validation.jsonl")
    args = parser.parse_args()

    split = load("validation")
    manifest = json.loads(MANIFEST.read_text())
    stored = Path("evals/splits/gold150-v1/validation.json").read_text()
    digest = hashlib.sha256(stored.encode()).hexdigest()
    if digest != manifest["split_artifact_sha256"]["validation"]:
        raise SystemExit("refusing to build: the validation split file does not match "
                         "the frozen manifest hash")
    if split["count"] != 40 or len(split["case_ids"]) != 40:
        raise SystemExit(f"refusing to build: expected 40 cases, got {split['count']}")

    holdout_ids = set(json.loads(
        Path("evals/splits/gold150-v1/holdout.json").read_text())["case_ids"])
    if set(split["case_ids"]) & holdout_ids:
        raise SystemExit("refusing to build: a holdout case appears in validation")

    gold = load_gold()
    sections = derived_sections()
    lines, skipped, derived_count = [], [], 0
    for case_id in split["case_ids"]:
        record = gold[case_id]
        spans = spans_of(record)
        refs = []
        for span in spans:
            source = next((s for s in (record.get("expected_evidence") or [])
                           if s.get("char_start") == span["char_start"]
                           and s.get("version_id") == span["version_id"]), record)
            section = source.get("section_path") or (
                record.get("section_path") if not (record.get("expected_evidence") or [])
                else None)
            if not section:
                section = _section_for(sections[span["version_id"]],
                                       span["char_start"])
                derived_count += 1
            if not section:
                skipped.append({"case_id": case_id, "reason": "no section_path"})
                continue
            refs.append({"version_id": span["version_id"],
                         "section_path": section,
                         "char_start": span["char_start"],
                         "char_end": span["char_end"]})
        if not refs:
            skipped.append({"case_id": case_id, "reason": "no usable anchor"})
            continue
        reasoning = record.get("reasoning_type")
        lines.append({
            "case_id": case_id,
            "category": CATEGORY_MAP.get(reasoning, "normal"),
            "question": record.get("question") or record.get("proposed_question"),
            "expected_evidence": refs,
            "expected_abstain": False,
            "notes": json.dumps({
                "group": record["group"], "provider": record.get("provider"),
                "reasoning_type": reasoning,
                "secondary_category": record.get("secondary_category"),
                "evidence_shape": record.get("evidence_shape") or "single_span",
                "document_title": record.get("document_title"),
            }),
        })

    out = Path(args.out)
    out.write_text("\n".join(json.dumps(line, ensure_ascii=False) for line in lines)
                   + "\n", encoding="utf-8")
    print(f"wrote {out}")
    print(f"  cases      : {len(lines)} (split says {split['count']})")
    print(f"  spans      : {sum(len(line['expected_evidence']) for line in lines)}")
    print(f"  section_path derived from the corpus: {derived_count}")
    print(f"  skipped    : {len(skipped)} {skipped or ''}")
    print(f"  holdout ids in output: "
          f"{len({line['case_id'] for line in lines} & holdout_ids)}")
    if len(lines) != 40:
        raise SystemExit("refusing: not every validation case was projected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
