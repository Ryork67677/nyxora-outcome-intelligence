#!/usr/bin/env python3
"""EXP-010 supplementary analysis: was the movement actually about truncation?

The headline B->D delta cannot distinguish "encoder alignment worked" from "chunks
moved and some got luckier". This splits the evidence spans by whether the control
chunk carrying them was truncated at 512, and asks the two questions separately:

* **truncation-driven cases** — the control chunk did not fit. Did alignment rescue
  them, improve their rank, or leave them where they were?
* **already-fitting cases** — the control chunk fitted whole, so alignment had
  nothing to fix. If those got *worse*, the intervention fragmented topical context
  it should have left alone, which is the EXP-008 failure repeating.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag_v1.chunkers.encoder_aligned import payload_tokens
from rag_v1.db import connect

CONTROL_SET = "cs_v1_control"
ALIGNED_SET = "cs_v4_encoder_aligned"
WINDOW = 512


def carrying_chunks(cur, chunk_set: str, version_id: str, section_path: list, span: list) -> list:
    cur.execute(
        """
        SELECT chunk_id, char_start, char_end, coalesce(search_text, text)
        FROM chunk
        WHERE chunk_set_id=%s AND version_id=%s AND section_path=%s
          AND char_start < %s AND char_end > %s
        ORDER BY char_start
        """,
        (chunk_set, version_id, section_path, span[1], span[0]),
    )
    return cur.fetchall()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="experiments/EXP-010/results.json")
    parser.add_argument("--golden", default="evals/golden/v1.jsonl")
    parser.add_argument("--out", default="experiments/EXP-010/truncation-analysis.json")
    args = parser.parse_args()

    payload = json.loads(Path(args.results).read_text())
    cfg = payload["configurations"]
    b, d = cfg["B_transformer_control"]["cases"], cfg["D_transformer_aligned"]["cases"]
    c, e = cfg["C_bm25_transformer_control_rrf"]["cases"], cfg["E_bm25_control_plus_aligned_rrf"]["cases"]

    from rag_v1.evals.io import load_cases

    cases = [x for x in load_cases(Path(args.golden)) if x.expected_evidence]

    rows = []
    with connect() as conn, conn.cursor() as cur:
        for case in cases:
            for idx, ref in enumerate(case.expected_evidence):
                span = [ref.char_start, ref.char_end]
                ctrl = carrying_chunks(cur, CONTROL_SET, ref.version_id, ref.section_path, span)
                algn = carrying_chunks(cur, ALIGNED_SET, ref.version_id, ref.section_path, span)

                ctrl_tokens = [payload_tokens(r[3]) for r in ctrl]
                algn_tokens = [payload_tokens(r[3]) for r in algn]
                # Was the answer itself pushed past the window in the control?
                offset_in_chunk = None
                answer_visible_in_control = None
                if ctrl:
                    host = ctrl[0]
                    prefix = host[3][: max(ref.char_start - host[1], 0)]
                    offset_in_chunk = payload_tokens(prefix)
                    answer_visible_in_control = offset_in_chunk + 2 < WINDOW

                rows.append({
                    "case_id": case.case_id, "span_index": idx,
                    "section_path": ref.section_path, "span": span,
                    "control_chunks": len(ctrl),
                    "control_payload_tokens": ctrl_tokens,
                    "control_truncated": any(t + 2 > WINDOW for t in ctrl_tokens),
                    "answer_token_offset_in_control_chunk": offset_in_chunk,
                    "answer_visible_in_control_window": answer_visible_in_control,
                    "aligned_chunks": len(algn),
                    "aligned_payload_tokens": algn_tokens,
                    "aligned_truncated": any(t + 2 > WINDOW for t in algn_tokens),
                    "evidence_split_across_aligned_chunks": len(algn) > 1,
                    "rank_B_control": b[case.case_id]["spans"][idx]["rank"],
                    "rank_D_aligned": d[case.case_id]["spans"][idx]["rank"],
                    "cosine_B": b[case.case_id]["spans"][idx]["similarity"],
                    "cosine_D": d[case.case_id]["spans"][idx]["similarity"],
                    "rank_C_fused": c[case.case_id]["spans"][idx]["rank"],
                    "rank_E_fused": e[case.case_id]["spans"][idx]["rank"],
                })

    def bucket(row: dict) -> str:
        rb, rd = row["rank_B_control"], row["rank_D_aligned"]
        if rb is None and rd is None:
            return "still_unreachable"
        if rb is None:
            return "newly_reachable"
        if rd is None:
            return "lost_entirely"
        if rd < rb:
            return "improved"
        if rd > rb:
            return "worsened"
        return "unchanged"

    for row in rows:
        row["movement"] = bucket(row)

    truncated = [r for r in rows if r["control_truncated"]]
    fitting = [r for r in rows if not r["control_truncated"]]

    def tally(group: list) -> dict:
        out: dict[str, int] = {}
        for r in group:
            out[r["movement"]] = out.get(r["movement"], 0) + 1
        return out

    result = {
        "experiment_id": "EXP-010",
        "window": WINDOW,
        "question": "Did alignment help where truncation actually was, and leave the rest alone?",
        "truncation_driven": {
            "spans": len(truncated),
            "movement": tally(truncated),
            "detail": truncated,
        },
        "already_fitting": {
            "spans": len(fitting),
            "movement": tally(fitting),
            "note": "Alignment had nothing to fix here. Any 'worsened' row is fragmentation "
                    "of context that already fitted — the EXP-008 failure mode.",
            "detail": fitting,
        },
        "evidence_now_split_across_chunks": [
            {"case_id": r["case_id"], "span_index": r["span_index"],
             "aligned_chunks": r["aligned_chunks"], "movement": r["movement"],
             "rank_B_control": r["rank_B_control"], "rank_D_aligned": r["rank_D_aligned"]}
            for r in rows if r["evidence_split_across_aligned_chunks"]
        ],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(f"truncation-driven spans: {len(truncated):2d}  {tally(truncated)}")
    print(f"already-fitting spans:   {len(fitting):2d}  {tally(fitting)}")
    print(f"evidence now split across aligned chunks: {len(result['evidence_now_split_across_chunks'])}")
    for r in result["evidence_now_split_across_chunks"]:
        print(f"   {r['case_id']}#{r['span_index']}: {r['aligned_chunks']} chunks, "
              f"rank {r['rank_B_control']} -> {r['rank_D_aligned']} ({r['movement']})")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
