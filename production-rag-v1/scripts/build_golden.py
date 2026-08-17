#!/usr/bin/env python3
"""Compile the V1 golden set from human-authored cases plus verified anchors.

Every question, expected claim and target document below was chosen by reading
the ingested source document. What this script automates is only the mechanical,
error-prone half: turning a human-verified literal quotation into the stable
``(version_id, section_path, char_start, char_end)`` anchor the evaluator scores
against, and failing loudly when a quotation is missing or ambiguous.

That split matters for the benchmark's validity:

* Anchors are never hand-typed, so a case cannot silently point at the wrong span.
* A locator that matches zero or multiple chunks aborts the build, so a case can
  never become ambiguous after a re-ingest or a chunking change.
* Anchors are resolved from the database, so re-running this after a corpus
  refresh regenerates coordinates instead of invalidating the benchmark.

Usage::

    python scripts/build_golden.py --snapshot SNAPSHOT_ID --out evals/golden/v1.jsonl
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

from rag_v1.db import connect


@dataclass(frozen=True)
class Locator:
    """A human-verified literal quotation inside one specific document."""

    url_suffix: str
    quote: str
    # Extend the anchor past the quotation when the answering sentence continues.
    extend: int = 0


@dataclass
class CaseSpec:
    case_id: str
    category: str
    question: str
    claims: list[dict] = field(default_factory=list)
    locators: list[Locator] = field(default_factory=list)
    expected_abstain: bool = False
    notes: str = ""


def claim(text: str, match_type: str = "contains", critical: bool = True, alternatives: list[str] | None = None) -> dict:
    return {
        "text": text,
        "match_type": match_type,
        "critical": critical,
        "alternatives": alternatives or [],
    }


CASES: list[CaseSpec] = [
    # ------------------------------------------------------------------ Anthropic
    CaseSpec(
        case_id="AN-001",
        category="exact_lookup",
        question="Which request header must every Claude API request send, and what value does the documentation give as the example?",
        claims=[claim("anthropic-version"), claim("2023-06-01")],
        locators=[Locator("/api/versioning", "you must send an `anthropic-version` request header", extend=60)],
        notes="Answer is in the page front matter description, not under a heading.",
    ),
    CaseSpec(
        case_id="AN-002",
        category="exact_lookup",
        question="Which HTTP status code does the Claude API return with the request_too_large error type?",
        claims=[claim("413")],
        locators=[Locator("/api/errors", "413 - `request_too_large`", extend=60)],
    ),
    CaseSpec(
        case_id="AN-003",
        category="exact_lookup",
        question="How many requests can a single Message Batches create request contain at most?",
        claims=[claim("100,000", alternatives=["100000"])],
        locators=[Locator("/api/messages/batches", "There is a limit of 100,000 messages in a single request.")],
    ),
    CaseSpec(
        case_id="AN-004",
        category="exact_lookup",
        question="How many blocks does the Claude prompt caching lookback window check per breakpoint?",
        claims=[claim("20")],
        locators=[Locator("/build-with-claude/prompt-caching", "The lookback window is 20 blocks.", extend=120)],
    ),
    CaseSpec(
        case_id="AN-005",
        category="exact_lookup",
        question="Which anthropic-beta header value enables context editing?",
        claims=[claim("context-management-2025-06-27")],
        locators=[Locator("/build-with-claude/context-editing", "use the beta header `context-management-2025-06-27`")],
    ),
    CaseSpec(
        case_id="AN-006",
        category="exact_lookup",
        question="Which beta header value enables the Claude code execution tool?",
        claims=[claim("code-execution-2025-05-22")],
        locators=[Locator("/agents-and-tools/tool-use/code-execution-tool", "`code-execution-2025-05-22`")],
    ),
    CaseSpec(
        case_id="AN-007",
        category="exact_lookup",
        question="What error type does the Claude API return with HTTP status 529?",
        claims=[claim("overloaded_error")],
        locators=[Locator("/api/errors", "529 - `overloaded_error`", extend=50)],
    ),
    CaseSpec(
        case_id="AN-008",
        category="normal",
        question="What does Anthropic guarantee to preserve for a given version of the Messages API?",
        claims=[claim("input parameters"), claim("output parameters")],
        locators=[Locator("/api/versioning", "For any given version with the Messages API, Anthropic preserves:", extend=70)],
    ),
    CaseSpec(
        case_id="AN-009",
        category="version_conflict",
        question="Can an organization still purchase a Priority Tier capacity commitment for the Claude API?",
        claims=[claim("no longer available for purchase")],
        locators=[Locator("/api/service-tiers", "Priority Tier capacity commitments are no longer available for purchase.")],
        notes="The service-tiers page still documents Priority Tier at length; only the warning block states it cannot be bought. Stale-context trap.",
    ),
    CaseSpec(
        case_id="AN-010",
        category="version_conflict",
        question="What is the current state of the claude-opus-4-1-20250805 model?",
        claims=[claim("Retired")],
        locators=[Locator("/about-claude/model-deprecations", "| claude-opus-4-1-20250805   | Retired", extend=60)],
        notes="Evidence lives in a markdown table row, which the chunker types as 'table'.",
    ),
    CaseSpec(
        case_id="AN-011",
        category="ambiguous",
        question="What is my rate limit on the Claude API?",
        claims=[claim("usage tier")],
        locators=[Locator("/api/rate-limits", "Limits are defined by **usage tier**.", extend=140)],
        notes="Deliberately under-specified. Correct behavior is to explain that the limit depends on usage tier, not to state one number.",
    ),
    CaseSpec(
        case_id="AN-012",
        category="multi_hop",
        question="If a Claude API request fails with HTTP 429, what error type comes back and what determines the limit that was hit?",
        claims=[claim("rate_limit_error"), claim("usage tier")],
        locators=[
            Locator("/api/errors", "429 - `rate_limit_error`", extend=40),
            Locator("/api/rate-limits", "Limits are defined by **usage tier**.", extend=140),
        ],
        notes="Requires evidence from two separate documents.",
    ),
    # --------------------------------------------------------------------- OpenAI
    CaseSpec(
        case_id="OA-001",
        category="exact_lookup",
        question="Which environment variable globally disables tracing in the OpenAI Agents SDK?",
        claims=[claim("OPENAI_AGENTS_DISABLE_TRACING")],
        locators=[Locator("docs/tracing.md", "OPENAI_AGENTS_DISABLE_TRACING=1", extend=10)],
    ),
    CaseSpec(
        case_id="OA-002",
        category="exact_lookup",
        question="Which exception does the OpenAI Agents SDK raise when a run exceeds the max_turns limit?",
        claims=[claim("MaxTurnsExceeded")],
        locators=[Locator("docs/running_agents.md", "This exception is raised when the agent's run exceeds the `max_turns` limit", extend=120)],
    ),
    CaseSpec(
        case_id="OA-003",
        category="exact_lookup",
        question="Which exception does the OpenAI Agents SDK runner raise when an input guardrail tripwire fires?",
        claims=[claim("InputGuardrailTripwireTriggered")],
        locators=[Locator("docs/guardrails.md", "The runner immediately raises an `InputGuardrailTripwireTriggered`", extend=90)],
    ),
    CaseSpec(
        case_id="OA-004",
        category="exact_lookup",
        question="How do you disable the agent turn limit entirely in the OpenAI Agents SDK runner?",
        claims=[claim("max_turns=None")],
        locators=[Locator("docs/running_agents.md", "Pass `max_turns=None` to disable this turn limit.")],
    ),
    CaseSpec(
        case_id="OA-005",
        category="exact_lookup",
        question="Which OpenAI Agents SDK function sets the OpenAI API key programmatically instead of using the environment variable?",
        claims=[claim("set_default_openai_key")],
        locators=[Locator("docs/config.md", "set_default_openai_key()][agents.set_default_openai_key] function to set the key", extend=10)],
    ),
    CaseSpec(
        case_id="OA-006",
        category="multi_hop",
        question="What are the two documented ways to globally disable tracing in the OpenAI Agents SDK — one by environment and one in code?",
        claims=[claim("OPENAI_AGENTS_DISABLE_TRACING"), claim("set_tracing_disabled")],
        locators=[
            Locator("docs/tracing.md", "OPENAI_AGENTS_DISABLE_TRACING=1", extend=10),
            Locator("docs/config.md", "You can also disable tracing entirely by using the", extend=110),
        ],
        notes="Requires evidence from two separate documents in the same repository.",
    ),
    CaseSpec(
        case_id="OA-007",
        category="normal",
        question="What problem does built-in session memory solve in the OpenAI Agents SDK?",
        claims=[claim("conversation history"), claim("to_input_list")],
        locators=[Locator("docs/sessions/index.md", "The Agents SDK provides built-in session memory", extend=200)],
    ),
    CaseSpec(
        case_id="OA-008",
        category="exact_lookup",
        question="Which model does the OpenAI Agents SDK use when an Agent does not specify one?",
        claims=[claim("gpt-5.6-luna")],
        locators=[Locator("docs/models/index.md", "does not specify a model, the Agents SDK uses", extend=90)],
        notes="Strong closed-book contrast: the value is release-specific and unlikely to be recalled without retrieval.",
    ),
    # ----------------------------------------------------------- abstain controls
    CaseSpec(
        case_id="MI-001",
        category="missing_info",
        question="What does the turbo_reasoning_level parameter do in the Claude Messages API?",
        expected_abstain=True,
        notes="No such parameter exists in the corpus. Control for confident fabrication; not retrieval-scored.",
    ),
    CaseSpec(
        case_id="MI-002",
        category="missing_info",
        question="How much does an enterprise support plan for the OpenAI Agents SDK cost per seat per month?",
        expected_abstain=True,
        notes="Pricing of that kind is absent from the corpus. Control for confident fabrication; not retrieval-scored.",
    ),
]


RESOLVE_SQL = """
SELECT c.version_id,
       c.section_path,
       c.char_start,
       c.chunk_type,
       s.canonical_url,
       position(%(quote)s in c.text) AS offset_in_chunk,
       length(c.text) AS chunk_len
FROM chunk c
JOIN document_version v ON v.version_id = c.version_id
JOIN document_source s ON s.source_id = v.source_id
JOIN corpus_snapshot_version sv ON sv.version_id = c.version_id
WHERE sv.snapshot_id = %(snapshot)s
  AND s.canonical_url LIKE %(url_pattern)s
  AND c.text LIKE %(quote_pattern)s
ORDER BY c.ordinal
"""

VERIFY_SQL = """
SELECT substring(v.normalized_text from %(start)s + 1 for %(length)s)
FROM document_version v WHERE v.version_id = %(version_id)s
"""


def resolve(cur, snapshot: str, locator: Locator) -> dict:
    cur.execute(
        RESOLVE_SQL,
        {
            "snapshot": snapshot,
            "quote": locator.quote,
            "quote_pattern": f"%{locator.quote}%",
            "url_pattern": f"%{locator.url_suffix}",
        },
    )
    rows = cur.fetchall()
    if not rows:
        raise SystemExit(f"NO MATCH for {locator.url_suffix!r} quote={locator.quote!r}")
    if len(rows) > 1:
        urls = {r[4] for r in rows}
        raise SystemExit(
            f"AMBIGUOUS ({len(rows)} chunks across {len(urls)} docs) for "
            f"{locator.url_suffix!r} quote={locator.quote!r}"
        )

    version_id, section_path, char_start, chunk_type, url, offset, chunk_len = rows[0]
    start = char_start + (offset - 1)
    end = start + len(locator.quote) + locator.extend
    # Never let an extended anchor run past the chunk that produced it.
    end = min(end, char_start + chunk_len)

    cur.execute(VERIFY_SQL, {"start": start, "length": end - start, "version_id": version_id})
    materialized = cur.fetchone()[0]
    if locator.quote not in materialized:
        raise SystemExit(f"VERIFY FAILED for {locator.quote!r}: anchor text does not contain the quotation")

    return {
        "anchor": {
            "version_id": version_id,
            "section_path": section_path,
            "char_start": start,
            "char_end": end,
        },
        "audit": {
            "canonical_url": url,
            "chunk_type": chunk_type,
            "section_path": section_path,
            "quote": locator.quote,
            "anchor_text": materialized,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--out", default="evals/golden/v1.jsonl")
    parser.add_argument("--audit", default="evals/golden/v1.anchors.json")
    args = parser.parse_args()

    out_path = Path(args.out)
    audit_path = Path(args.audit)
    records: list[dict] = []
    audit: list[dict] = []

    with connect() as conn, conn.cursor() as cur:
        for spec in CASES:
            evidence = []
            for locator in spec.locators:
                resolved = resolve(cur, args.snapshot, locator)
                evidence.append(resolved["anchor"])
                audit.append({"case_id": spec.case_id, **resolved["audit"]})

            records.append(
                {
                    "case_id": spec.case_id,
                    "category": spec.category,
                    "question": spec.question,
                    "expected_claims": spec.claims,
                    "expected_evidence": evidence,
                    "expected_abstain": spec.expected_abstain,
                    "notes": spec.notes or None,
                }
            )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8"
    )
    audit_path.write_text(json.dumps({"snapshot_id": args.snapshot, "anchors": audit}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    scored = sum(1 for r in records if r["expected_evidence"])
    print(
        json.dumps(
            {
                "cases": len(records),
                "retrieval_scored_cases": scored,
                "abstain_only_cases": len(records) - scored,
                "evidence_spans": sum(len(r["expected_evidence"]) for r in records),
                "out": str(out_path),
                "audit": str(audit_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
