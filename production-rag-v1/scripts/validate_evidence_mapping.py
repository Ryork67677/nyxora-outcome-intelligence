#!/usr/bin/env python3
"""Fail loudly if re-chunking moved the evaluation target.

The golden set anchors evidence above the chunk layer as
``(version_id, section_path, char_start, char_end)`` precisely so that a new
chunking can be scored against unchanged ground truth. That guarantee is worth
nothing unless it is checked, because the failure mode is silent: a chunker that
drops a section, shifts an offset or renames a section path would simply score
lower, and the drop would be misread as evidence about chunk granularity.

Checks, per chunk set:

1. Every expected source version still exists and is still in the snapshot.
2. Every expected evidence span overlaps at least one chunk with the *same*
   section path — the exact condition the retrieval evaluator scores on.
3. Source character offsets still address the same text: the chunk's recorded
   span, read back out of ``normalized_text``, matches the chunk's stored text
   (allowing for a recorded V3 context prefix).
4. Section identity is still valid — no empty or null section paths.

Exit status is non-zero if any check fails, so this can gate an experiment run.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag_v1.db import connect
from rag_v1.evals.io import load_cases


def validate(snapshot_id: str, golden_path: Path) -> dict:
    cases = load_cases(golden_path)
    refs = [(c.case_id, ref) for c in cases for ref in c.expected_evidence]
    failures: list[dict] = []
    per_span: list[dict] = []

    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT chunk_set_id FROM corpus_snapshot WHERE snapshot_id=%s", (snapshot_id,))
        row = cur.fetchone()
        if not row:
            raise SystemExit(f"FAIL: unknown snapshot {snapshot_id}")
        chunk_set_id = row[0]

        for case_id, ref in refs:
            cur.execute(
                """
                SELECT count(*) FROM corpus_snapshot_version
                WHERE snapshot_id=%s AND version_id=%s
                """,
                (snapshot_id, ref.version_id),
            )
            if cur.fetchone()[0] == 0:
                failures.append(
                    {"case_id": case_id, "check": "version_present", "version_id": ref.version_id}
                )
                continue

            # The exact overlap condition used by rag_v1.evals.retrieval_eval.
            cur.execute(
                """
                SELECT chunk_id, char_start, char_end, chunk_type, char_end - char_start AS len
                FROM chunk
                WHERE chunk_set_id=%s AND version_id=%s AND section_path=%s
                  AND char_start < %s AND char_end > %s
                ORDER BY char_start
                """,
                (chunk_set_id, ref.version_id, ref.section_path, ref.char_end, ref.char_start),
            )
            matches = cur.fetchall()
            if not matches:
                failures.append(
                    {
                        "case_id": case_id,
                        "check": "span_maps_to_chunk",
                        "version_id": ref.version_id,
                        "section_path": ref.section_path,
                        "span": [ref.char_start, ref.char_end],
                    }
                )
                continue

            per_span.append(
                {
                    "case_id": case_id,
                    "section_path": ref.section_path,
                    "span": [ref.char_start, ref.char_end],
                    "span_len": ref.char_end - ref.char_start,
                    "containing_chunks": len(matches),
                    "smallest_containing_chunk_len": min(m[4] for m in matches),
                    "evidence_share_of_chunk": round(
                        (ref.char_end - ref.char_start) / min(m[4] for m in matches), 4
                    ),
                }
            )

        # Offsets must still address the same source text.
        cur.execute(
            """
            SELECT count(*) FROM chunk c
            JOIN document_version v ON v.version_id = c.version_id
            WHERE c.chunk_set_id=%s
              AND substring(v.normalized_text from c.char_start+1 for c.char_end-c.char_start)
                  <> substring(c.text from COALESCE((c.metadata->>'context_prefix_len')::int, 0) + 1)
            """,
            (chunk_set_id,),
        )
        offset_mismatches = cur.fetchone()[0]
        if offset_mismatches:
            failures.append({"check": "source_offsets_stable", "mismatched_chunks": offset_mismatches})

        cur.execute(
            "SELECT count(*) FROM chunk WHERE chunk_set_id=%s AND (section_path IS NULL OR array_length(section_path,1) IS NULL)",
            (chunk_set_id,),
        )
        bad_sections = cur.fetchone()[0]
        if bad_sections:
            failures.append({"check": "section_identity_valid", "chunks_without_section": bad_sections})

        cur.execute("SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (chunk_set_id,))
        total_chunks = cur.fetchone()[0]

    return {
        "snapshot_id": snapshot_id,
        "chunk_set_id": chunk_set_id,
        "total_chunks": total_chunks,
        "expected_spans": len(refs),
        "spans_mapped": len(per_span),
        "offset_mismatches": offset_mismatches,
        "passed": not failures,
        "failures": failures,
        "spans": per_span,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, action="append", dest="snapshots")
    parser.add_argument("--golden", default="evals/golden/v1.jsonl")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    reports = [validate(s, Path(args.golden)) for s in args.snapshots]
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"reports": reports}, indent=2) + "\n", encoding="utf-8")

    failed = False
    for report in reports:
        status = "PASS" if report["passed"] else "FAIL"
        shares = [s["evidence_share_of_chunk"] for s in report["spans"]]
        mean_share = sum(shares) / len(shares) if shares else 0.0
        print(
            f"[{status}] {report['chunk_set_id']:26s} "
            f"spans {report['spans_mapped']}/{report['expected_spans']}  "
            f"chunks {report['total_chunks']:6d}  "
            f"offset_mismatches {report['offset_mismatches']}  "
            f"mean evidence share of containing chunk {mean_share:.3f}"
        )
        for failure in report["failures"]:
            print(f"    {failure}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
