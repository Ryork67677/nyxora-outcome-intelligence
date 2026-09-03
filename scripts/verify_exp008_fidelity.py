#!/usr/bin/env python3
"""EXP-008 fidelity gate: prove that only the retrieval unit changed.

The C -> D comparison is only an isolation of chunk size if the two chunk sets
differ in boundaries and nothing else. This checks that mechanically and writes a
machine-readable record of what is identical and what changed.

Exits non-zero if any invariant fails, so it can gate the experiment.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from rag_v1.db import connect
from rag_v1.evals.io import load_cases

CONTROL = "cs_v1_control"
BOUNDED = "cs_2722bf8b72dcf3eb404336d7"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", default="evals/golden/v1.jsonl")
    parser.add_argument("--out", default="experiments/EXP-008/intervention-fidelity.json")
    args = parser.parse_args()

    failures: list[dict] = []
    report: dict = {"control_chunk_set": CONTROL, "bounded_chunk_set": BOUNDED}

    with connect() as conn, conn.cursor() as cur:
        # --- identical upstream -------------------------------------------------
        cur.execute(
            """
            SELECT
              (SELECT count(DISTINCT version_id) FROM chunk WHERE chunk_set_id=%s),
              (SELECT count(DISTINCT version_id) FROM chunk WHERE chunk_set_id=%s),
              (SELECT count(*) FROM (
                  SELECT version_id FROM chunk WHERE chunk_set_id=%s
                  EXCEPT SELECT version_id FROM chunk WHERE chunk_set_id=%s) x)
            """,
            (CONTROL, BOUNDED, CONTROL, BOUNDED),
        )
        ctrl_versions, bounded_versions, version_diff = cur.fetchone()
        report["same_document_versions"] = {
            "control_versions": ctrl_versions,
            "bounded_versions": bounded_versions,
            "versions_only_in_control": version_diff,
        }
        if ctrl_versions != bounded_versions or version_diff:
            failures.append({"check": "same_document_versions"})

        # Both chunkings read the same stored normalized_text, so the parser source
        # is identical by construction; verify no chunk escapes its version's text.
        for label, chunk_set in (("control", CONTROL), ("bounded", BOUNDED)):
            cur.execute(
                """
                SELECT count(*) FROM chunk c JOIN document_version v ON v.version_id=c.version_id
                WHERE c.chunk_set_id=%s
                  AND substring(v.normalized_text from c.char_start+1 for c.char_end-c.char_start) <> c.text
                """,
                (chunk_set,),
            )
            mismatches = cur.fetchone()[0]
            report[f"{label}_body_is_exact_source_substring"] = mismatches == 0
            if mismatches:
                failures.append({"check": "body_is_exact_source_substring", "chunk_set": chunk_set})

        # --- no enrichment, no V3 transformations -------------------------------
        for label, chunk_set in (("control", CONTROL), ("bounded", BOUNDED)):
            cur.execute(
                """
                SELECT
                  count(*) FILTER (WHERE search_text IS NOT NULL),
                  count(*) FILTER (WHERE context_header IS NOT NULL),
                  count(*) FILTER (WHERE metadata ? 'context_prefix_len'),
                  count(*) FILTER (WHERE chunk_type = 'table_row'),
                  count(*) FILTER (WHERE metadata ? 'enrichment')
                FROM chunk WHERE chunk_set_id=%s
                """,
                (chunk_set,),
            )
            st, ch, cp, tr, en = cur.fetchone()
            report[f"{label}_no_enrichment"] = {
                "search_text_rows": st, "context_header_rows": ch,
                "context_prefix_rows": cp, "table_row_chunks": tr, "enrichment_metadata_rows": en,
            }
            if any((st, ch, cp, tr, en)):
                failures.append({"check": "no_enrichment_or_v3_transforms", "chunk_set": chunk_set})

        # --- evidence anchors map in both ---------------------------------------
        cases = load_cases(Path(args.golden))
        refs = [(c.case_id, r) for c in cases for r in c.expected_evidence]
        anchor_rows = []
        for case_id, ref in refs:
            row = {"case_id": case_id, "section_path": ref.section_path,
                   "span": [ref.char_start, ref.char_end]}
            for label, chunk_set in (("control", CONTROL), ("bounded", BOUNDED)):
                cur.execute(
                    """
                    SELECT chunk_id, char_end-char_start FROM chunk
                    WHERE chunk_set_id=%s AND version_id=%s AND section_path=%s
                      AND char_start < %s AND char_end > %s
                    ORDER BY char_end-char_start LIMIT 1
                    """,
                    (chunk_set, ref.version_id, ref.section_path, ref.char_end, ref.char_start),
                )
                found = cur.fetchone()
                row[f"{label}_chunk_id"] = found[0] if found else None
                row[f"{label}_chunk_len"] = found[1] if found else None
                if not found:
                    failures.append({"check": "evidence_span_maps", "case_id": case_id,
                                     "chunk_set": chunk_set})
            anchor_rows.append(row)
        report["evidence_anchors"] = anchor_rows
        report["evidence_spans_mapped"] = {
            "control": sum(1 for r in anchor_rows if r["control_chunk_id"]),
            "bounded": sum(1 for r in anchor_rows if r["bounded_chunk_id"]),
            "expected": len(refs),
        }

        # --- what actually changed ---------------------------------------------
        changed = {}
        for label, chunk_set in (("control", CONTROL), ("bounded", BOUNDED)):
            cur.execute(
                "SELECT char_end-char_start FROM chunk WHERE chunk_set_id=%s ORDER BY 1", (chunk_set,)
            )
            lengths = [r[0] for r in cur.fetchall()]
            def q(p, lengths=lengths):
                return lengths[min(len(lengths) - 1, int(len(lengths) * p))]
            changed[label] = {
                "chunks": len(lengths), "mean": round(statistics.mean(lengths)),
                "median": q(0.5), "p90": q(0.9), "p99": q(0.99), "max": lengths[-1],
                "over_2000": sum(1 for x in lengths if x > 2000),
            }
        report["intended_change_retrieval_unit"] = changed

    report["passed"] = not failures
    report["failures"] = failures

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")

    print(f"same document versions           : {report['same_document_versions']}")
    print(f"bodies are exact source substrings: control={report['control_body_is_exact_source_substring']} "
          f"bounded={report['bounded_body_is_exact_source_substring']}")
    print(f"no enrichment (control)          : {report['control_no_enrichment']}")
    print(f"no enrichment (bounded)          : {report['bounded_no_enrichment']}")
    print(f"evidence spans mapped            : {report['evidence_spans_mapped']}")
    print(f"retrieval unit changed           : {json.dumps(report['intended_change_retrieval_unit'])}")
    print(f"\nGATE: {'PASS' if report['passed'] else 'FAIL'}")
    for f in failures:
        print("   ", f)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
