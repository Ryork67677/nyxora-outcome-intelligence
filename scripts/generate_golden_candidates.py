#!/usr/bin/env python3
"""EXP-014R: generate source-anchored candidate evaluation questions.

Why this exists
---------------
EXP-014 produced the first intervention to beat the global control, but on 20
questions where one case is 5 percentage points. The binding constraint is now the
evaluation set, not the retrieval architecture.

How a candidate is made
-----------------------
Evidence first, question second — never the reverse. For each document version the
generator finds sentences that state a *checkable fact* (a default, a limit, a
status code), records that sentence's exact character span, and only then writes a
question the span answers. A question is therefore anchored to real source text by
construction, and the anchor is verified by hashing the span.

What this is NOT
----------------
These candidates are **machine-generated and source-verified**, not human-verified.
Every case carries ``verification: "source_anchored_automatic"`` and
``human_verified: false``. The EXP-014R brief requires human verification for
holdout inclusion; that cannot be satisfied in an unattended session, and marking
these as human-verified would fabricate exactly the provenance the rule exists to
guarantee. The limitation is recorded in the manifest and the report.

A limit-extraction pattern was written and then **removed**: it bound a number to
whichever identifier appeared first in the same sentence, which produced confident
but wrong pairings ("maximum value allowed for rbac_group_id -> 100" where the 100
governed something else). An unreliable extractor is worse than a smaller set.

Question phrasing is deliberately *not* copied from the evidence sentence — a
question built from the answer's own wording would be trivially retrievable by
either system and would measure nothing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from rag_v1.db import connect
from rag_v1.parsing import _sections_from_markdown

SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"

# --- fact patterns -----------------------------------------------------------
# A first pass over these documents produced unusable questions — "the ptimized
# condition", "What value does parameter take" — and, worse, factually wrong claims
# where a loose status-code pattern paired an unrelated number with a nearby word.
# The patterns below are therefore deliberately narrow, and every emitted case must
# additionally survive `fact_is_sound` below. Precision matters far more than yield:
# a question the corpus does not actually answer makes the whole benchmark worthless.

#: An identifier must *look* like an API parameter — snake_case, or back-quoted.
IDENTIFIER = r"(?:`([A-Za-z][A-Za-z0-9_.]{2,40})`|\b([a-z][a-z0-9]*(?:_[a-z0-9]+){1,4})\b)"

DEFAULT_RE = re.compile(
    IDENTIFIER + r"[^\n]{0,30}?(?:defaults?\s+to|default\s+is|default:)\s+`?([^\s,.;:)\]]{1,20})`?",
    re.IGNORECASE)

#: A limit must be bound to a named identifier in the same sentence, otherwise the
#: question has no sensible subject ("the upper limit on active").
LIMIT_RE = re.compile(
    r"(?:maximum|max\.?|up\s+to|limit\s+of|at\s+most|no\s+more\s+than)\s+"
    r"`?([\d][\d,]{0,12})`?", re.IGNORECASE)

#: Words that are never a parameter name, however they are punctuated.
NOT_IDENTIFIERS = frozenset(["parameter", "parameters", "api", "apis", "value", "values", "default", "defaults", "request", "requests", "response", "responses", "example", "examples", "note", "notes", "model", "models", "field", "fields", "option", "options", "header", "headers", "method", "methods", "object", "objects", "string", "number", "boolean", "integer", "array", "type", "types"])

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z`\[])|\n")

#: Identifiers a developer might plausibly ask about that the corpus does not
#: document. Absence is verified against the snapshot before a case is emitted.
ABSENT_CANDIDATES = [
    ("max_retries_per_minute", "a per-minute retry ceiling"),
    ("response_compression", "response payload compression"),
    ("streaming_checkpoint_id", "resuming an interrupted stream"),
    ("prompt_cache_eviction_policy", "how cached prompts are evicted"),
    ("batch_priority_tier", "prioritising one batch over another"),
    ("token_refund_on_error", "refunding tokens when a request errors"),
    ("regional_data_residency_pin", "pinning requests to one region"),
    ("per_key_spend_alert", "spend alerts on an individual API key"),
]


def sentence_span(text: str, position: int) -> tuple[int, int]:
    """The sentence containing ``position``, as absolute offsets."""
    start = max(text.rfind("\n", 0, position), 0)
    for match in SENTENCE_SPLIT.finditer(text, max(0, position - 400), position):
        start = max(start, match.end())
    end = len(text)
    for match in SENTENCE_SPLIT.finditer(text, position, min(len(text), position + 400)):
        end = match.start()
        break
    while start < len(text) and text[start] in " \t\n":
        start += 1
    return start, min(end, len(text))


def section_for(sections, offset: int) -> list[str] | None:
    """The innermost section whose span contains ``offset``."""
    best = None
    for section in sections:
        inside = section.char_start <= offset < section.char_end
        smaller = best is None or (section.char_end - section.char_start) <= (
            best.char_end - best.char_start)
        if inside and smaller:
            best = section
    return list(best.path) if best else None


def clean(value: str) -> str:
    return value.strip().strip("`*_,.;:()[]").strip()


def load_versions(cur) -> list[dict]:
    cur.execute(
        """
        SELECT v.version_id, v.normalized_text, s.provider, s.title, s.canonical_url,
               v.captured_at
        FROM document_version v
        JOIN document_source s ON s.source_id = v.source_id
        JOIN corpus_snapshot_version sv ON sv.version_id = v.version_id
        WHERE sv.snapshot_id = %s
        ORDER BY v.version_id
        """,
        (SNAPSHOT,),
    )
    return [{"version_id": r[0], "text": r[1], "provider": r[2], "title": r[3],
             "url": r[4], "captured_at": str(r[5])} for r in cur.fetchall()]


def make_case(case_id, category, provider, question, claims, doc, span, notes):
    start, end = span
    evidence_text = doc["text"][start:end]
    return {
        "case_id": case_id,
        "split": None,
        "category": category,
        "provider": provider,
        "question": question,
        "expected_claims": [{"text": c, "match_type": "contains", "critical": True,
                             "alternatives": []} for c in claims],
        "expected_evidence": [{
            "version_id": doc["version_id"],
            "section_path": section_for(doc["sections"], start) or ["Preamble"],
            "char_start": start, "char_end": end,
        }],
        "expected_abstain": False,
        "source_document_title": doc["title"],
        "source_url": doc["url"],
        "source_captured_at": doc["captured_at"],
        "evidence_text_sha256": hashlib.sha256(evidence_text.encode("utf-8")).hexdigest(),
        "evidence_char_length": end - start,
        "verification": "source_anchored_automatic",
        "human_verified": False,
        "notes": notes,
    }


#: A default value is a literal, not an English word. "approved defaults to the ..."
#: produced a case whose expected answer was "the"; this is what stops that.
VALUE_RE = re.compile(r"""^(?:true|false|null|none|-?\d+(?:\.\d+)?|"[^"]{1,20}"|'[^']{1,20}'|`?[a-z][a-z0-9_.\-]{1,24}`?)$""",
                      re.IGNORECASE)
STOP_VALUES = frozenset(["the", "a", "an", "it", "its", "this", "that", "they", "them", "and", "or", "but", "of", "to", "in", "on", "for", "with"])


def value_is_literal(value: str) -> bool:
    bare = value.strip("`\"'")
    return bool(VALUE_RE.match(value)) and bare.lower() not in STOP_VALUES


def fact_is_sound(identifier: str, value: str, span_text: str) -> bool:
    """Reject anything we cannot verify from the span itself.

    Both the identifier and the claimed value must appear verbatim inside the
    recorded evidence, so a case can never assert a fact its own anchor does not
    contain. This is the check that would have caught the first pass's invented
    status codes.
    """
    if not identifier or not value:
        return False
    if identifier.lower() in NOT_IDENTIFIERS or len(identifier) < 3:
        return False
    if identifier.lower() == value.lower():
        return False
    if not any(ch.isalnum() for ch in value) or not value_is_literal(value):
        return False
    return identifier.lower() in span_text.lower() and value.lower() in span_text.lower()


def pick_identifier(match: re.Match) -> str:
    return clean(match.group(1) or match.group(2) or "")


def generate(docs: list[dict], per_doc_cap: int = 2) -> list[dict]:
    cases: list[dict] = []
    counters: Counter = Counter()
    seen_facts: set[tuple] = set()

    for doc in docs:
        text = doc["text"]
        emitted = 0
        provider = doc["provider"]
        prefix = "OA" if provider == "openai" else "AN"

        # --- defaults ---------------------------------------------------------
        for match in DEFAULT_RE.finditer(text):
            if emitted >= per_doc_cap:
                break
            identifier = pick_identifier(match)
            value = clean(match.group(3))
            start, end = sentence_span(text, match.start())
            span_text = text[start:end]
            if not (25 <= end - start <= 600) or not fact_is_sound(identifier, value, span_text):
                continue
            key = ("default", identifier.lower(), value.lower())
            if key in seen_facts:
                continue
            seen_facts.add(key)
            counters[prefix] += 1
            cases.append(make_case(
                f"{prefix}-DEFAULT-{counters[prefix]:03d}", "exact_lookup", provider,
                f"What is the default value of {identifier}?", [value], doc, (start, end),
                f"Default for {identifier} stated in {doc['title']}."))
            emitted += 1

    return cases


def generate_abstention(docs: list[dict]) -> list[dict]:
    """Questions the frozen corpus does not answer. Absence is verified, not assumed."""
    corpus = "\n".join(d["text"].lower() for d in docs)
    cases = []
    for index, (identifier, description) in enumerate(ABSENT_CANDIDATES, start=1):
        if identifier.lower() in corpus:
            continue  # the corpus does document it after all — not an abstention case
        cases.append({
            "case_id": f"XX-ABSTAIN-{index:03d}",
            "split": None,
            "category": "missing_info",
            "provider": "cross",
            "question": f"How do I configure {identifier} to control {description}?",
            "expected_claims": [],
            "expected_evidence": [],
            "expected_abstain": True,
            "source_document_title": None, "source_url": None, "source_captured_at": None,
            "evidence_text_sha256": None, "evidence_char_length": None,
            "verification": "absence_verified_against_snapshot",
            "human_verified": False,
            "notes": f"'{identifier}' does not appear anywhere in the frozen snapshot. "
                     "Correct behaviour is abstention.",
        })
    return cases


def generate_multi_hop(cases: list[dict], docs: list[dict]) -> list[dict]:
    """Pair two facts from the same document but different sections.

    Both spans are required, so partial retrieval must not earn full credit.
    """
    by_doc: dict[str, list[dict]] = {}
    for case in cases:
        if case["expected_evidence"]:
            by_doc.setdefault(case["expected_evidence"][0]["version_id"], []).append(case)
    titles = {d["version_id"]: d["title"] for d in docs}

    out = []
    index = 0
    for version_id, group in by_doc.items():
        if len(group) < 2:
            continue
        first, second = group[0], group[1]
        if first["expected_evidence"][0]["section_path"] == second["expected_evidence"][0]["section_path"]:
            continue
        index += 1
        prefix = "OA" if first["provider"] == "openai" else "AN"
        out.append({
            "case_id": f"{prefix}-MULTI-{index:03d}",
            "split": None,
            "category": "multi_hop",
            "provider": first["provider"],
            "question": (f"In the {titles[version_id]} documentation, {first['question'][0].lower()}"
                         f"{first['question'][1:].rstrip('?')}, and {second['question'][0].lower()}"
                         f"{second['question'][1:]}"),
            "expected_claims": first["expected_claims"] + second["expected_claims"],
            "expected_evidence": first["expected_evidence"] + second["expected_evidence"],
            "expected_abstain": False,
            "source_document_title": titles[version_id],
            "source_url": first["source_url"], "source_captured_at": first["source_captured_at"],
            "evidence_text_sha256": None,
            "evidence_char_length": None,
            "verification": "source_anchored_automatic",
            "human_verified": False,
            "notes": "Two facts from different sections of one document; both spans required.",
        })
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="evals/golden/candidates.jsonl")
    parser.add_argument("--per-doc", type=int, default=2)
    parser.add_argument("--multi-hop", type=int, default=18)
    args = parser.parse_args()

    with connect() as conn, conn.cursor() as cur:
        docs = load_versions(cur)
    for doc in docs:
        doc["sections"] = _sections_from_markdown(doc["text"])

    cases = generate(docs, per_doc_cap=args.per_doc)
    cases += generate_multi_hop(cases, docs)[: args.multi_hop]
    cases += generate_abstention(docs)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cases) + "\n",
                   encoding="utf-8")

    print(f"generated {len(cases)} candidates -> {out}")
    print("by category:", dict(Counter(c["category"] for c in cases)))
    print("by provider:", dict(Counter(c["provider"] for c in cases)))
    print("verification:", dict(Counter(c["verification"] for c in cases)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
