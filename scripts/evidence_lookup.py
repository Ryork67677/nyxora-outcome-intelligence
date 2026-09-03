#!/usr/bin/env python3
"""Resolve a literal corpus string to a stable evidence anchor.

Golden cases must be anchored to ``(version_id, section_path, char_start, char_end)``
rather than to a chunk id. Authoring those coordinates by hand is error prone, so
this helper takes a literal string that a human has already located in the source
document and prints the exact anchor plus the surrounding text for verification.

    python scripts/evidence_lookup.py "max_tokens is the maximum" --limit 3
    python scripts/evidence_lookup.py --url-like '%messages/create%' "temperature"

The span printed is the span of the matched literal inside ``normalized_text``,
and the ``section_path`` is taken from the chunk that contains it. Both are
verified against the database before printing, so a copy/paste of the emitted
JSON object is a checked anchor rather than a guess.
"""

from __future__ import annotations

import argparse
import json

from rag_v1.db import connect

SQL = """
SELECT c.version_id,
       c.section_path,
       c.char_start,
       c.char_end,
       c.chunk_type,
       s.provider,
       s.canonical_url,
       position(%(needle)s in c.text) AS offset_in_chunk,
       c.text
FROM chunk c
JOIN document_version v ON v.version_id = c.version_id
JOIN document_source s ON s.source_id = v.source_id
JOIN corpus_snapshot_version sv ON sv.version_id = c.version_id
WHERE sv.snapshot_id = %(snapshot)s
  AND c.text LIKE %(pattern)s
  AND (%(url_like)s IS NULL OR s.canonical_url LIKE %(url_like)s)
ORDER BY s.provider, s.canonical_url, c.ordinal
LIMIT %(limit)s
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("needle", help="literal string to locate in the corpus")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--url-like", default=None, help="optional SQL LIKE filter on canonical_url")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--context", type=int, default=160, help="characters of context to show")
    parser.add_argument("--span", type=int, default=0, help="anchor span length; 0 = length of needle")
    args = parser.parse_args()

    params = {
        "needle": args.needle,
        "pattern": f"%{args.needle}%",
        "snapshot": args.snapshot,
        "url_like": args.url_like,
        "limit": args.limit,
    }
    with connect() as conn, conn.cursor() as cur:
        cur.execute(SQL, params)
        rows = cur.fetchall()

    if not rows:
        print("no match")
        return 1

    for version_id, section_path, char_start, _char_end, chunk_type, provider, url, off, text in rows:
        # position() is 1-indexed; convert to a global 0-indexed offset.
        start = char_start + (off - 1)
        length = args.span or len(args.needle)
        anchor = {
            "version_id": version_id,
            "section_path": section_path,
            "char_start": start,
            "char_end": start + length,
        }
        print("=" * 100)
        print(f"{provider} | {url} | chunk_type={chunk_type}")
        print(json.dumps(anchor))
        lo = max(0, (off - 1) - args.context)
        hi = min(len(text), (off - 1) + length + args.context)
        print("--- context ---")
        print(text[lo:hi].replace("\n", "\n  "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
