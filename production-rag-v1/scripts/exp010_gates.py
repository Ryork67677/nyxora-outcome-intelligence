#!/usr/bin/env python3
"""EXP-010 ingestion gates: evidence preservation, truncation, chunk distribution.

Three things must hold before any retrieval number from EXP-010 means anything:

1. every one of the 22 expected evidence spans still maps to at least one
   retrieval unit, in **both** chunk sets, anchored on
   ``(version_id, section_path, char_start, char_end)`` and never on chunk ids;
2. **no** encoder-aligned chunk truncates when passed through the real encoding
   path — measured by actually tokenizing every chunk, not by trusting metadata;
3. the distribution comparison that says what the intervention did.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.chunkers.encoder_aligned import (
    ENCODER_ALIGNED_CHUNK_SET_ID,
    HARD_PAYLOAD_TOKENS,
    SPEC,
    encoder_budget,
    encoder_tokenizer,
)
from rag_v1.db import connect
from rag_v1.evals.io import load_cases

CONTROL_SET = "cs_v1_control"
WINDOW = 512


def _rows(cur, chunk_set: str) -> list[tuple]:
    cur.execute(
        """
        SELECT chunk_id, version_id, section_path, chunk_type, char_start, char_end,
               coalesce(search_text, text) AS encoded_text, metadata
        FROM chunk WHERE chunk_set_id=%s ORDER BY chunk_id
        """,
        (chunk_set,),
    )
    return cur.fetchall()


def distribution(rows: list[tuple], label: str) -> dict:
    tok = encoder_tokenizer()
    # encode_batch applies the model's post-processor, so ids already include
    # [CLS]/[SEP]. Adding an overhead here would double-count them.
    lengths = [len(e.ids) for e in tok.encode_batch([r[6] for r in rows])]

    def pct(p: float) -> int:
        ordered = sorted(lengths)
        return ordered[min(int(len(ordered) * p), len(ordered) - 1)]

    truncated = [n for n in lengths if n > WINDOW]
    visible = sum(min(n, WINDOW) for n in lengths)
    return {
        "chunk_set": label,
        "chunks": len(rows),
        "mean_encoded_tokens": round(statistics.mean(lengths), 1),
        "median_encoded_tokens": statistics.median(lengths),
        "p75": pct(0.75), "p90": pct(0.90), "p95": pct(0.95), "p99": pct(0.99),
        "max_encoded_tokens": max(lengths),
        "chunks_over_256": sum(1 for n in lengths if n > 256),
        "chunks_over_384": sum(1 for n in lengths if n > 384),
        "chunks_over_448": sum(1 for n in lengths if n > 448),
        "chunks_over_512": len(truncated),
        "percent_truncated_at_512": round(100 * len(truncated) / len(lengths), 4),
        "total_tokens": sum(lengths),
        "tokens_visible_to_encoder": visible,
        "corpus_token_coverage": round(visible / sum(lengths), 4),
        "chunks_by_type": dict(Counter(r[3] for r in rows)),
        "provider_distribution": dict(Counter(r[1].split(":")[0] if ":" in r[1] else "unknown" for r in rows)),
        "truncated_chunk_ids": [rows[i][0] for i, n in enumerate(lengths) if n > WINDOW][:50],
    }


def evidence_gate(cur, cases, chunk_set: str) -> dict:
    """Every expected span must land in at least one retrieval unit."""
    spans, missing = [], []
    for case in cases:
        for idx, ref in enumerate(case.expected_evidence):
            cur.execute(
                """
                SELECT chunk_id, char_start, char_end FROM chunk
                WHERE chunk_set_id=%s AND version_id=%s AND section_path=%s
                  AND char_start < %s AND char_end > %s
                ORDER BY char_end-char_start
                """,
                (chunk_set, ref.version_id, ref.section_path, ref.char_end, ref.char_start),
            )
            hits = cur.fetchall()
            entry = {
                "case_id": case.case_id, "span_index": idx,
                "section_path": ref.section_path, "span": [ref.char_start, ref.char_end],
                "mapped_chunks": len(hits),
                "smallest_chunk_id": hits[0][0] if hits else None,
                "fully_contained": any(c[1] <= ref.char_start and c[2] >= ref.char_end for c in hits),
            }
            spans.append(entry)
            if not hits:
                missing.append(entry)
    return {
        "chunk_set": chunk_set,
        "spans_total": len(spans),
        "spans_mapped": len(spans) - len(missing),
        "spans_fully_contained": sum(1 for s in spans if s["fully_contained"]),
        "missing": missing,
        "passed": not missing,
        "spans": spans,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", default="evals/golden/v1.jsonl")
    parser.add_argument("--out", default="experiments/EXP-010/ingestion-gates.json")
    args = parser.parse_args()

    cases = [c for c in load_cases(Path(args.golden)) if c.expected_evidence]
    failures: list[str] = []

    with connect() as conn, conn.cursor() as cur:
        control_rows = _rows(cur, CONTROL_SET)
        aligned_rows = _rows(cur, ENCODER_ALIGNED_CHUNK_SET_ID)
        dists = {
            "control": distribution(control_rows, CONTROL_SET),
            "encoder_aligned": distribution(aligned_rows, ENCODER_ALIGNED_CHUNK_SET_ID),
        }
        gates = {
            "control": evidence_gate(cur, cases, CONTROL_SET),
            "encoder_aligned": evidence_gate(cur, cases, ENCODER_ALIGNED_CHUNK_SET_ID),
        }

    for name, g in gates.items():
        if not g["passed"]:
            failures.append(f"{name}: {len(g['missing'])} expected evidence spans map to no chunk")
    if dists["encoder_aligned"]["chunks_over_512"]:
        failures.append(
            f"{dists['encoder_aligned']['chunks_over_512']} encoder-aligned chunks exceed the "
            f"{WINDOW}-token window; the set is not encoder-aligned"
        )

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                         stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        commit = None

    payload = {
        "experiment_id": "EXP-010",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "chunker": {"name": SPEC.name, "version": SPEC.version,
                    "config_hash": SPEC.config_hash, "config": SPEC.config},
        "encoder_budget": encoder_budget(),
        "hard_payload_tokens": HARD_PAYLOAD_TOKENS,
        "distribution": dists,
        "evidence_gate": gates,
        "failures": failures,
        "passed": not failures,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    for key, d in dists.items():
        print(f"{key:16s} chunks={d['chunks']:>6d} median={d['median_encoded_tokens']:>6g} "
              f"p95={d['p95']:>4d} max={d['max_encoded_tokens']:>5d} "
              f">512={d['chunks_over_512']:>5d} ({d['percent_truncated_at_512']:.2f}%) "
              f"coverage={d['corpus_token_coverage']:.4f}")
    for key, g in gates.items():
        print(f"{key:16s} evidence {g['spans_mapped']}/{g['spans_total']} mapped, "
              f"{g['spans_fully_contained']}/{g['spans_total']} fully contained -> "
              f"{'PASS' if g['passed'] else 'FAIL'}")
    print(f"\nwrote {out}")
    if failures:
        print("\nGATES FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
