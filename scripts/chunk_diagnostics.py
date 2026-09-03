#!/usr/bin/env python3
"""Chunk-size distribution report per chunk set.

Run before retrieval evaluation. The point is to establish, independently of any
recall number, whether a chunker actually did what it claims: whether the hard
ceiling is enforced, where the size mass moved, and whether anything above the
limit remains. A chunker whose distribution did not change cannot explain a recall
change, and one that leaves chunks above its own limit has a bug, not a result.

    python scripts/chunk_diagnostics.py --out experiments/EXP-005/chunk-distribution.json
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from rag_v1.db import connect

# Exceptions the report is allowed to show above a chunker's hard limit. Empty:
# V2 and V3 are expected to have none, and any that appear must be enumerated.
ALLOWED_EXCEPTIONS: dict[str, str] = {}


def percentile(values: list[int], p: float) -> int:
    if not values:
        return 0
    return values[min(len(values) - 1, int(len(values) * p))]


def describe(cur, chunk_set_id: str) -> dict:
    cur.execute(
        """
        SELECT chunker_name, chunker_version, config_hash, config, parser_version
        FROM chunk_set WHERE chunk_set_id = %s
        """,
        (chunk_set_id,),
    )
    name, version, cfg_hash, config, parser_version = cur.fetchone()
    hard_max = config.get("hard_max_chars")

    cur.execute(
        "SELECT char_end - char_start FROM chunk WHERE chunk_set_id=%s ORDER BY 1",
        (chunk_set_id,),
    )
    lengths = [r[0] for r in cur.fetchall()]

    cur.execute(
        "SELECT chunk_type, count(*) FROM chunk WHERE chunk_set_id=%s GROUP BY 1 ORDER BY 2 DESC",
        (chunk_set_id,),
    )
    by_type = dict(cur.fetchall())

    cur.execute(
        """
        SELECT s.provider, count(*), round(avg(c.char_end - c.char_start))::int, max(c.char_end - c.char_start)
        FROM chunk c
        JOIN document_version v ON v.version_id = c.version_id
        JOIN document_source s ON s.source_id = v.source_id
        WHERE c.chunk_set_id=%s GROUP BY 1 ORDER BY 1
        """,
        (chunk_set_id,),
    )
    by_provider = {
        r[0]: {"chunks": r[1], "mean_chars": r[2], "max_chars": r[3]} for r in cur.fetchall()
    }

    cur.execute(
        "SELECT count(DISTINCT version_id), count(*)::float8 / NULLIF(count(DISTINCT version_id),0) FROM chunk WHERE chunk_set_id=%s",
        (chunk_set_id,),
    )
    documents, per_doc = cur.fetchone()

    cur.execute(
        """
        SELECT metadata->>'block_kind', count(*) FROM chunk
        WHERE chunk_set_id=%s AND metadata ? 'block_kind' GROUP BY 1 ORDER BY 2 DESC
        """,
        (chunk_set_id,),
    )
    by_block_kind = dict(cur.fetchall())

    over_limit: list[dict] = []
    if hard_max:
        cur.execute(
            """
            SELECT c.chunk_id, c.chunk_type, c.char_end - c.char_start, s.canonical_url, c.section_path
            FROM chunk c
            JOIN document_version v ON v.version_id = c.version_id
            JOIN document_source s ON s.source_id = v.source_id
            WHERE c.chunk_set_id=%s AND c.char_end - c.char_start > %s
            ORDER BY 3 DESC LIMIT 50
            """,
            (chunk_set_id, hard_max),
        )
        over_limit = [
            {
                "chunk_id": r[0], "chunk_type": r[1], "chars": r[2],
                "url": r[3], "section_path": r[4],
                "allowed_reason": ALLOWED_EXCEPTIONS.get(r[0]),
            }
            for r in cur.fetchall()
        ]

    return {
        "chunk_set_id": chunk_set_id,
        "chunker": name,
        "chunker_version": version,
        "config_hash": cfg_hash,
        "config": config,
        "parser_version": parser_version,
        "hard_max_chars": hard_max,
        "documents": documents,
        "total_chunks": len(lengths),
        "chunks_per_document": round(per_doc, 1) if per_doc else 0,
        "mean_chars": round(statistics.mean(lengths)) if lengths else 0,
        "median_chars": percentile(lengths, 0.50),
        "p75_chars": percentile(lengths, 0.75),
        "p90_chars": percentile(lengths, 0.90),
        "p95_chars": percentile(lengths, 0.95),
        "p99_chars": percentile(lengths, 0.99),
        "max_chars": lengths[-1] if lengths else 0,
        "over_1500": sum(1 for x in lengths if x > 1500),
        "over_2000": sum(1 for x in lengths if x > 2000),
        "over_3000": sum(1 for x in lengths if x > 3000),
        "over_hard_max": sum(1 for x in lengths if hard_max and x > hard_max),
        "unexplained_over_hard_max": sum(1 for e in over_limit if not e["allowed_reason"]),
        "over_hard_max_examples": over_limit,
        "by_chunk_type": by_type,
        "by_block_kind": by_block_kind,
        "by_provider": by_provider,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="experiments/EXP-005/chunk-distribution.json")
    args = parser.parse_args()

    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT chunk_set_id FROM chunk_set ORDER BY created_at")
        ids = [r[0] for r in cur.fetchall()]
        reports = [describe(cur, cid) for cid in ids]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"chunk_sets": reports}, indent=2, default=str) + "\n", encoding="utf-8")

    header = f"{'chunker':24s} {'chunks':>7s} {'mean':>6s} {'med':>6s} {'p90':>6s} {'p95':>6s} {'p99':>6s} {'max':>7s} {'>2000':>6s} {'>3000':>6s} {'>hard':>6s}"
    print(header)
    print("-" * len(header))
    for r in reports:
        print(
            f"{r['chunker']:24s} {r['total_chunks']:7d} {r['mean_chars']:6d} {r['median_chars']:6d} "
            f"{r['p90_chars']:6d} {r['p95_chars']:6d} {r['p99_chars']:6d} {r['max_chars']:7d} "
            f"{r['over_2000']:6d} {r['over_3000']:6d} "
            f"{(r['over_hard_max'] if r['hard_max_chars'] else 0):6d}"
        )
    print()
    for r in reports:
        print(f"{r['chunker']}: types={r['by_chunk_type']}")
        if r["by_block_kind"]:
            print(f"{'':>{0}}  block kinds={r['by_block_kind']}")
        if r["unexplained_over_hard_max"]:
            print(f"  !! {r['unexplained_over_hard_max']} UNEXPLAINED chunks above hard limit {r['hard_max_chars']}")
            for e in r["over_hard_max_examples"][:5]:
                print(f"     {e['chars']:6d} {e['chunk_type']:10s} {e['section_path']}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
