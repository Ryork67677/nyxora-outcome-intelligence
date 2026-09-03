"""Does the question carry the scope its evidence carries? — batch 006 defect G.

A frame asks what the frame is shaped to ask. "What does {s} default to?" asks for a
complete answer; the evidence gives one value, scoped to named models or surfaces:

    evidence   `thinking.display` defaults to `"omitted"` on `claude-mythos-5` and
               `claude-fable-5` …
    generated  What does `thinking.display` default to?

The question inherits the *frame's* breadth, not the *evidence's*. Answered as asked it
is wrong, because the default is not universal. Three of batch 006's nine needed
rescoping by the owner, and in two of them the scope qualifier was not in the critical
strings either — so the claim-in-evidence check could not have caught it: there was
nothing to check.

Hence two conditions, and the second is the one with teeth:

1. a scope qualifier in the evidence must appear in the **question**; and
2. it must appear in the **critical strings**, so something downstream verifies it.

A qualifier that no check reads is decoration. Requiring it in the critical strings is
what turns this from a style rule into a gate.

The preregistered behaviour is **drop, not flag**: "a question whose evidence is scoped
and whose wording is not, does not export."
"""

from __future__ import annotations

import re

from rag_v1.gold.normalisation import contains_claim_string

SCOPED = "SCOPED"
SCOPE_MISSING_FROM_QUESTION = "SCOPE_MISSING_FROM_QUESTION"
SCOPE_MISSING_FROM_CRITICAL_STRINGS = "SCOPE_MISSING_FROM_CRITICAL_STRINGS"
UNSCOPED_SOURCE = "UNSCOPED_SOURCE"

#: A named model, in the two shapes this corpus writes one: prose ("Claude Sonnet 5",
#: "Claude Haiku 4.5", "GPT-5") and API id ("claude-mythos-5", "gpt-5-mini").
_MODEL_NAMES = (
    re.compile(r"\bClaude\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+[\d.]+\b"),
    re.compile(r"\bClaude\s+[A-Z][a-z]+\s+(?:Preview|Latest)\b"),
    re.compile(r"\bGPT-[\w.]+\b"),
    re.compile(r"`(claude-[\w.-]+|gpt-[\w.-]+|o\d(?:-[\w.]+)?)`"),
)
#: A platform or surface the behaviour is scoped to. These are proper nouns in the
#: documentation and are what "on the Claude API and Claude Code" narrows a default to.
_SURFACES = re.compile(
    r"\b(?:Claude\s+(?:API|Code|Console|Agent\s+SDK)|Anthropic\s+API|"
    r"OpenAI\s+(?:Python|TypeScript|JavaScript|Node)?\s*(?:SDK|API|library)|"
    r"Agents?\s+SDK|Messages\s+API|Responses\s+API|Batch(?:es)?\s+API|"
    r"Amazon\s+Bedrock|Google\s+Vertex(?:\s+AI)?|Azure\s+OpenAI|Vertex\s+AI)\b")
#: A comparative aside names something the statement is *compared to*, not something it
#: is scoped to. "`thinking.display` defaults to `"omitted"` on `claude-mythos-5` and
#: `claude-fable-5`, **the same as on Claude Mythos Preview**" is scoped to the two ids;
#: the Preview is a comparison. Requiring the question to carry it would demand wording
#: about a model the fact is not about — the opposite of what this gate is for.
_COMPARATIVE_ASIDE = re.compile(
    r"(?:the\s+same\s+as|same\s+as|as\s+(?:it\s+does\s+)?on|just\s+as|like|unlike|"
    r"compared\s+(?:to|with)|in\s+contrast\s+(?:to|with)|whereas)\b[^.;]*",
    re.IGNORECASE)


def qualifiers(evidence_text: str) -> list[str]:
    """Every model or surface name the span uses to narrow what it says.

    A name that opens the sentence is its subject, not its scope — "Claude Sonnet 5
    defaults to `high` effort on the Claude API and Claude Code" is *about* Sonnet 5 and
    *scoped to* two surfaces. Both are returned: the owner's rescoping of
    ``GOLD-B006-04`` put the subject in the question too, and a question that drops the
    subject is at least as broad as one that drops the surface.
    """
    # A comparison is not a scope: drop those clauses before reading qualifiers out.
    text = _COMPARATIVE_ASIDE.sub(" ", evidence_text or "")
    found: list[str] = []
    for pattern in _MODEL_NAMES:
        for match in pattern.finditer(text):
            name = (match.group(1) if match.re.groups else match.group(0)).strip()
            if name and name not in found:
                found.append(name)
    for match in _SURFACES.finditer(text):
        name = " ".join(match.group(0).split())
        if name not in found:
            found.append(name)
    return found


def evaluate(record: dict) -> dict:
    """Is this candidate's question as narrow as the evidence it is anchored to?

    Returns a status and the qualifiers behind it. ``UNSCOPED_SOURCE`` means the evidence
    names no model or surface, so there is no scope to carry and nothing to enforce.
    """
    spans = record.get("expected_evidence") or []
    evidence = " ".join(s.get("evidence_text", "") for s in spans)
    question = record.get("question") or record.get("proposed_question") or ""
    critical: list[str] = []
    for span in spans:
        critical.extend(span.get("critical_strings") or [])
    critical.extend(record.get("critical_strings") or [])

    found = qualifiers(evidence)
    if not found:
        return {"candidate_id": record.get("candidate_id"), "status": UNSCOPED_SOURCE,
                "qualifiers": [], "missing_from_question": [],
                "missing_from_critical_strings": []}

    missing_question = [q for q in found if not contains_claim_string(question, q)]
    missing_critical = [
        q for q in found
        if not any(contains_claim_string(c, q) or contains_claim_string(q, c)
                   for c in critical)]

    if missing_question:
        status = SCOPE_MISSING_FROM_QUESTION
    elif missing_critical:
        status = SCOPE_MISSING_FROM_CRITICAL_STRINGS
    else:
        status = SCOPED
    return {
        "candidate_id": record.get("candidate_id"),
        "status": status,
        "qualifiers": found,
        "missing_from_question": missing_question,
        "missing_from_critical_strings": missing_critical,
    }


def exports(record: dict) -> bool:
    """The preregistered gate: a scoped source with an unscoped question does not export."""
    return evaluate(record)["status"] in (SCOPED, UNSCOPED_SOURCE)


__all__ = [
    "SCOPED",
    "SCOPE_MISSING_FROM_CRITICAL_STRINGS",
    "SCOPE_MISSING_FROM_QUESTION",
    "UNSCOPED_SOURCE",
    "evaluate",
    "exports",
    "qualifiers",
]
