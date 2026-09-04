#!/usr/bin/env python3
"""NATQ-002 Stage 3: evidence locator and packet validator.

Deliberately not retrieval. No BM25, no dense vectors, no cross-encoder, no
ranking that could feed a candidate set — a verifier reading the frozen corpus
by eye, only faster. Offsets are into ``document_version.normalized_text``, the
same source-offset discipline GOLD-001 used, so a packet can be replayed exactly.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

SNAP = "snap_689e336380a054d8039dc35b2c09cd0a"
CS = "cs_v1_control"
_STOPWORDS = """the a an and or of to in for on with is are do does did how what when where why
which can i my me you your it its if that this these those be been was were will would should
could there here they them their our we us not no yes get got getting use used using want need
about into from at as by but so than then just only also more most some any all every each
other same such own too very don ve ll re am he she his her him actually really thing things
one two way ways make makes made even still keep keeps stop stops give gives take takes"""
STOP = frozenset(_STOPWORDS.split())


def load():
    from rag_v1.db import connect
    with connect() as c, c.cursor() as cur:
        cur.execute("""SELECT sv.version_id, dv.normalized_text, ds.provider, ds.title,
                              ds.canonical_url, dv.content_hash
            FROM corpus_snapshot_version sv
            JOIN document_version dv ON dv.version_id = sv.version_id
            JOIN document_source ds ON ds.source_id = dv.source_id
            WHERE sv.snapshot_id = %s""", (SNAP,))
        docs = {r[0]: {"text": r[1], "provider": r[2], "title": r[3], "url": r[4],
                       "content_hash": r[5]} for r in cur.fetchall()}
        cur.execute("""SELECT c.version_id, c.chunk_id, c.char_start, c.char_end, c.section_path
            FROM chunk c JOIN corpus_snapshot_version sv ON sv.version_id = c.version_id
            WHERE sv.snapshot_id = %s AND c.chunk_set_id = %s
            ORDER BY c.version_id, c.ordinal""", (SNAP, CS))
        chunks = cur.fetchall()
    return docs, chunks


def tokens(q: str) -> list[str]:
    t = re.findall(r"[a-zA-Z_][a-zA-Z0-9_.\-]*", q.lower())
    return [x for x in dict.fromkeys(t) if len(x) > 2 and x not in STOP]


def locate(q: str, docs, chunks, top_docs=3, per_doc=2, width=520):
    """Chunks whose text carries the most of the question's vocabulary."""
    T = tokens(q)
    scored = []
    for vid, cid, cs, ce, sp in chunks:
        body = docs[vid]["text"][cs:ce].lower()
        n = sum(1 for t in T if t in body)
        if n:
            scored.append((n, vid, cid, cs, ce, sp))
    scored.sort(key=lambda r: (-r[0], r[1], r[3]))
    out, seen = [], {}
    for n, vid, cid, cs, ce, sp in scored:
        if len(seen) >= top_docs and vid not in seen:
            continue
        if seen.get(vid, 0) >= per_doc:
            continue
        seen[vid] = seen.get(vid, 0) + 1
        out.append({"version_id": vid, "chunk_id": cid, "char_start": cs, "char_end": ce,
                    "section_path": sp, "tokens_hit": n, "of": len(T),
                    "provider": docs[vid]["provider"], "title": docs[vid]["title"],
                    "excerpt": docs[vid]["text"][cs:min(ce, cs + width)]})
    return out


def validate(packets: list[dict], docs) -> list[dict]:
    """Deterministic integrity checks. Every one is mechanical; none is a judgement."""
    results = []
    for p in packets:
        f = []
        if p.get("support_status") == "REJECT":
            if not p.get("rejection_reason"):
                f.append("rejected without a reason")
            results.append({"case": p["case"], "verdict": "REJECT",
                            "rejection_reason": p.get("rejection_reason"), "failures": f})
            continue
        vid = p.get("version_id")
        if vid not in docs:
            results.append({"case": p["case"], "verdict": "FIX_REQUIRED",
                            "failures": [f"unknown version_id {vid}"]})
            continue
        # A span may name its own version_id; a cross-document case needs that.
        # Anything that omits it is anchored in the packet's document.
        span_vids = []
        for i, sp in enumerate(p.get("evidence", [])):
            svid = sp.get("version_id", vid)
            if svid not in docs:
                f.append(f"span {i}: unknown version_id {svid}")
                continue
            span_vids.append(svid)
            got = docs[svid]["text"][sp["char_start"]:sp["char_end"]]
            if got != sp["quote"]:
                f.append(f"span {i}: offsets do not reproduce the quote "
                         f"(got {len(got)} chars, quote {len(sp['quote'])})")
        if not p.get("evidence"):
            f.append("no evidence spans")
        joined = " ".join(sp["quote"] for sp in p.get("evidence", []))
        for s in p.get("critical_strings", []):
            if s not in joined:
                f.append(f"critical string absent from evidence: {s!r}")
        if not p.get("atomic_claims"):
            f.append("no atomic claims")
        # Provider must describe where the evidence actually lives. A case whose
        # spans cross providers has to say so rather than claim one of them.
        provs = sorted({docs[v]["provider"] for v in span_vids})
        if len(provs) > 1:
            if p.get("provider") != "cross-provider":
                f.append(f"evidence spans providers {provs}; provider must be 'cross-provider'")
            if sorted(p.get("providers", [])) != provs:
                f.append(f"providers field {p.get('providers')} != evidence providers {provs}")
        elif provs and p.get("provider") != provs[0]:
            f.append(f"provider {p.get('provider')} != source {provs[0]}")
        results.append({"case": p["case"], "verdict": "PASS" if not f else "FIX_REQUIRED",
                        "failures": f})
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--locate", help="JSON file of {case,q} to locate evidence for")
    ap.add_argument("--validate", help="JSON file of packets to validate")
    ap.add_argument("--probe", nargs="+", help="literal strings to find in the frozen corpus")
    ap.add_argument("--ctx", type=int, default=260)
    ap.add_argument("--slice", default=None)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--count", type=int, default=25)
    ap.add_argument("--out")
    a = ap.parse_args()
    docs, chunks = load()
    if a.probe:
        for needle in a.probe:
            print(f"\n### {needle!r}")
            hits = 0
            for vid, d in sorted(docs.items()):
                start = 0
                while (i := d["text"].find(needle, start)) != -1 and hits < 6:
                    lo, hi = max(0, i - a.ctx // 2), min(len(d["text"]), i + len(needle) + a.ctx)
                    print(f"  [{d['provider']}] {d['title'][:52]} v={vid[:14]} @{i}")
                    print("     …" + d["text"][lo:hi].replace(chr(10), " | ") + "…")
                    hits += 1
                    start = i + len(needle)
                if hits >= 6:
                    break
            if not hits:
                print("  (absent from the frozen corpus)")
        raise SystemExit(0)
    if a.validate:
        res = validate(json.loads(Path(a.validate).read_text()), docs)
        print(json.dumps(res, indent=1))
    else:
        rows = json.loads(Path(a.locate).read_text())
        if a.slice:
            rows = [r for r in rows if r.get("slice") == a.slice]
        rows = rows[a.start:a.start + a.count]
        out = [{"case": r["case"], "q": r["q"], "intent": r.get("intent"),
                "candidates": locate(r["q"], docs, chunks)} for r in rows]
        Path(a.out).write_text(json.dumps(out, indent=1))
        print(f"located evidence candidates for {len(out)} questions -> {a.out}")
