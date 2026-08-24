#!/usr/bin/env python3
"""GOLD-001 Fix C: how often does the heading parser capture ordinary prose?

``GOLD-B005-11`` carries a ``section_path`` of *"configured through AWS_REGION,
AWS_DEFAULT_REGION, or your AWS profile."* — a sentence, not a heading. The parser takes
any line matching ``#{1,6} text`` as a heading, and a Markdown page that wraps a long
sentence onto a line beginning with ``#`` gets one.

This audit counts the shape across the frozen corpus snapshot and says whether it looks
isolated or systematic. It is diagnostic only. No heading is rewritten, no document is
reparsed into storage, and no existing evidence anchor moves — a candidate approved
against a bad ``section_path`` was approved against its *evidence*, and the path is
metadata beside it.

What it changes for batch 006 is a rule, not a record: ``section_path`` is never trusted
for claim scope. The exact evidence has to carry its own.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.db import connect
from rag_v1.parsing import _HEADING_RE

SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"

#: A heading is a label. These are the ways a captured line stops being one.
#: Each is reported separately, because "long" and "is a sentence" are different
#: complaints and a reader should be able to disagree with one and not the other.
_ENDS_SENTENCE = re.compile(r"[a-z0-9)`\"']\.\s*$")
_STARTS_LOWER = re.compile(r"^[a-z]")
_LIST_PROSE = re.compile(r",\s+(?:or|and)\s+")
_TRAILING_PUNCT = re.compile(r"[,;:]\s*$")
#: A version heading legitimately ends in a period-ish token; so does "v1.2".
_VERSION_LIKE = re.compile(r"^v?\d+(?:\.\d+)+\s*$")
#: ``max_tokens``, ``end\_turn``, ``claude.ai`` — a single identifier is a perfectly
#: good heading and starts lower case because the identifier does. Flagging these as
#: prose was the first draft of this audit, and it tripled the count with labels.
_IDENTIFIER_LIKE = re.compile(r"^`?[A-Za-z_][\w\\.\-]*(?:\(\))?`?$")
LONG_HEADING_WORDS = 12


def suspicions(title: str) -> list[str]:
    """Every reason this line does not read as a heading. Empty means it does."""
    found = []
    if _VERSION_LIKE.match(title):
        return found
    if _ENDS_SENTENCE.search(title):
        found.append("ends in a sentence-final period")
    if _STARTS_LOWER.match(title) and not _IDENTIFIER_LIKE.match(title):
        found.append("starts lowercase")
    if len(title.split()) > LONG_HEADING_WORDS:
        found.append(f"longer than {LONG_HEADING_WORDS} words")
    if _LIST_PROSE.search(title):
        found.append("contains a comma-separated 'or'/'and' list")
    if _TRAILING_PUNCT.search(title):
        found.append("ends in a comma, semicolon or colon")
    return found


def likely_prose(reasons: list[str]) -> bool:
    """The strong signal: it reads as a sentence, not merely as a long label.

    A long heading is common and harmless. A line that ends in a full stop, or begins in
    lower case, is a fragment of a paragraph that happened to start with a ``#``.
    """
    return any(r in ("ends in a sentence-final period", "starts lowercase")
               for r in reasons)


def load_docs(cur) -> list[dict]:
    cur.execute(
        """
        SELECT v.version_id, v.normalized_text, s.provider, s.title
        FROM document_version v
        JOIN document_source s ON s.source_id = v.source_id
        JOIN corpus_snapshot_version sv ON sv.version_id = v.version_id
        WHERE sv.snapshot_id = %s
        ORDER BY v.version_id
        """,
        (SNAPSHOT,),
    )
    return [{"version_id": r[0], "text": r[1], "provider": r[2], "title": r[3]}
            for r in cur.fetchall()]


def audit(docs: list[dict]) -> dict:
    total = 0
    suspicious: list[dict] = []
    per_document: Counter = Counter()
    prose_documents: set[str] = set()
    reason_counts: Counter = Counter()

    for doc in docs:
        for match in _HEADING_RE.finditer(doc["text"]):
            total += 1
            title = match.group(2).strip()
            reasons = suspicions(title)
            if not reasons:
                continue
            prose = likely_prose(reasons)
            per_document[doc["version_id"]] += 1
            for reason in reasons:
                reason_counts[reason] += 1
            if prose:
                prose_documents.add(doc["version_id"])
            suspicious.append({
                "version_id": doc["version_id"],
                "provider": doc["provider"],
                "document_title": doc["title"],
                "level": len(match.group(1)),
                "heading": title,
                "char_start": match.start(),
                "reasons": reasons,
                "likely_prose": prose,
            })

    prose = [s for s in suspicious if s["likely_prose"]]
    share = len(prose) / total if total else 0.0
    return {
        "audit": "GOLD-001 heading parser",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "snapshot": SNAPSHOT,
        "parser": "rag_v1.parsing._HEADING_RE",
        "documents": len(docs),
        "headings_parsed": total,
        "suspicious_headings": len(suspicious),
        "likely_prose": len(prose),
        "likely_prose_share": round(share, 4),
        "documents_with_prose_headings": len(prose_documents),
        "documents_affected_ids": sorted(prose_documents),
        "reason_counts": dict(reason_counts.most_common()),
        "per_document_suspicious": dict(per_document.most_common()),
        "examples": sorted(prose, key=lambda e: (-len(e["reasons"]),
                                                -len(e["heading"])))[:25],
        "verdict": verdict(len(prose), total, len(prose_documents), len(docs)),
        "actions_taken": [],
        "not_done": [
            "No heading was rewritten and no document was reparsed into storage.",
            "No existing evidence anchor moved; closed batches are unchanged.",
            "GOLD-B005-11 keeps its recorded section_path — it is a closed record.",
        ],
        "rule_for_batch_006": (
            "section_path is not trusted for claim scope. A candidate's exact evidence "
            "must contain the scope its claim needs, and a candidate whose scope would "
            "depend on a suspicious heading is repaired or dropped."
        ),
    }


def verdict(prose: int, total: int, documents: int, all_documents: int) -> dict:
    """Isolated, or systematic enough to justify a parser experiment later?"""
    share = prose / total if total else 0.0
    doc_share = documents / all_documents if all_documents else 0.0
    if prose == 0:
        finding = ("The parser produced no prose-shaped heading anywhere in the "
                   "snapshot. GOLD-B005-11 is not reproduced by this rule set, which "
                   "means the audit's heuristics miss it rather than that it did not "
                   "happen — worth a second look before concluding the defect is rare.")
        systematic = False
    elif share < 0.01 and doc_share < 0.15:
        finding = (f"{prose} of {total} parsed headings ({share:.2%}), in {documents} "
                   f"of {all_documents} documents. That is isolated. It does not "
                   "justify a parser experiment on its own, and the batch-006 rule — "
                   "never trust section_path for scope — is the cheaper fix.")
        systematic = False
    else:
        finding = (f"{prose} of {total} parsed headings ({share:.2%}), in {documents} "
                   f"of {all_documents} documents. That is systematic enough to justify "
                   "a parser experiment after GOLD-001 completes: a heading rule that "
                   "requires a short label, rejects sentence-final punctuation, or "
                   "reads the surrounding block structure would remove most of it.")
        systematic = True
    return {"systematic": systematic, "finding": finding,
            "recommended_next_step": (
                "A parser experiment AFTER GOLD-001 is complete. Not now: changing the "
                "parser changes section_path for every stored document, and the corpus "
                "snapshot is frozen for the duration of this evaluation.")}


def render(report: dict) -> str:
    examples = "\n".join(
        f"| `{e['version_id'][:12]}…` | {e['level']} | {e['heading'][:96]} | "
        f"{'; '.join(e['reasons'])} |"
        for e in report["examples"])
    reasons = "\n".join(f"| {reason} | {count} |"
                        for reason, count in report["reason_counts"].items())
    return "\n".join([
        "# GOLD-001 — heading parser audit",
        "",
        (f"**{report['likely_prose']} of {report['headings_parsed']} parsed headings "
         f"({report['likely_prose_share']:.2%}) read as prose rather than as a label**, "
         f"across {report['documents_with_prose_headings']} of {report['documents']} "
         "documents in the frozen snapshot."),
        "",
        f"{report['verdict']['finding']}",
        "",
        "## What was counted",
        "",
        "| | |",
        "| --- | --- |",
        f"| snapshot | `{report['snapshot']}` |",
        f"| parser | `{report['parser']}` |",
        f"| documents | {report['documents']} |",
        f"| headings parsed | {report['headings_parsed']} |",
        f"| suspicious on any rule | {report['suspicious_headings']} |",
        f"| **likely prose** | **{report['likely_prose']}** |",
        f"| documents affected | {report['documents_with_prose_headings']} |",
        "",
        ("A heading is a label. *Suspicious* means it broke one of the rules below; "
         "*likely prose* is the strong subset — it ends in a sentence-final period or "
         "begins in lower case, which a label does not do. A merely long heading is "
         "common and harmless, and is counted separately for that reason."),
        "",
        "| why it was flagged | headings |",
        "| --- | --- |",
        reasons or "| — | 0 |",
        "",
        "## Examples",
        "",
        "| version | level | heading | why |",
        "| --- | --- | --- | --- |",
        examples or "| — | — | none found | — |",
        "",
        "## What this changes",
        "",
        f"**For batch 006.** {report['rule_for_batch_006']}",
        "",
        f"**Later.** {report['verdict']['recommended_next_step']}",
        "",
        "## What was not done",
        "",
        *[f"- {item}" for item in report["not_done"]],
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="experiments/GOLD-001")
    args = parser.parse_args()

    with connect() as conn, conn.cursor() as cur:
        docs = load_docs(cur)
    if not docs:
        raise SystemExit(f"no documents in snapshot {SNAPSHOT}")

    report = audit(docs)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "GOLD-001-heading-parser-audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "GOLD-001-heading-parser-audit.md").write_text(render(report),
                                                          encoding="utf-8")
    print(f"{report['headings_parsed']} headings in {report['documents']} documents; "
          f"{report['suspicious_headings']} suspicious, "
          f"{report['likely_prose']} likely prose "
          f"({report['likely_prose_share']:.2%}) in "
          f"{report['documents_with_prose_headings']} documents")
    print(f"systematic: {report['verdict']['systematic']}")
    print(f"wrote {out}/GOLD-001-heading-parser-audit.md")
    print(f"wrote {out}/GOLD-001-heading-parser-audit.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
