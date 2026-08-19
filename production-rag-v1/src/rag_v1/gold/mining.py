"""GOLD-001: candidate evidence discovery.

The generator's job changed
---------------------------
EXP-014R tried to synthesise gold — "X defaults to Y" inferred from nearby tokens —
and it produced confident wrong answers: `tool_choice -> True`, `effort` given two
contradictory values, numbers bound to whichever identifier happened to sit nearest.
Only 12 of a target 100 survived, several still wrong.

Span *discovery* was the part that worked. So this module discovers and packages
evidence for review. It proposes a question and claims, but those are **suggestions
to a reviewer**, never ground truth, and every candidate leaves here as
``candidate_unverified``.

Binding must be structural, not proximity
-----------------------------------------
The EXP-014R failure was always the same shape: a value was attached to an
identifier because they were close together in the text. So the highest-confidence
miner here reads **markdown table rows**, where the parameter is the row's first
cell and its description is another cell of the same row — the association is a
property of the document's structure, not a guess about word order.

The prose miner is deliberately far stricter than EXP-014R's: it requires an
explicit relationship phrase *and* exactly one candidate identifier in the sentence.
Anything with two possible subjects is emitted with
``needs_human_interpretation = true`` rather than silently resolved.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field

CANDIDATE_SCHEMA_VERSION = "1.0"

CONTEXT_BEFORE = 900
CONTEXT_AFTER = 900

_TABLE_ROW = re.compile(r"^\s*\|(?P<cells>.+)\|\s*$")
_SEPARATOR = re.compile(r"^\s*\|?[\s:\-|]+\|[\s:\-|]*$")
_IDENTIFIER = re.compile(r"`([A-Za-z][A-Za-z0-9_.\[\]]{2,48})`|\b([a-z][a-z0-9]*(?:_[a-z0-9]+){1,4})\b")
_DEFAULT_IN_CELL = re.compile(
    r"(?:defaults?\s+to|default\s+is|default:)\s*`?([^\s,.;)\]|]{1,32})`?", re.IGNORECASE)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z`\[])|\n{2,}")

#: Relationship phrases that state something outright rather than implying it.
EXPLICIT_MARKERS = (
    ("required", "explicit_required_optional"),
    ("is optional", "explicit_required_optional"),
    ("deprecated", "explicit_deprecation"),
    ("no longer supported", "explicit_deprecation"),
    ("raises", "explicit_exception"),
    ("is raised", "explicit_exception"),
    ("returns a", "explicit_response"),
    ("will return", "explicit_response"),
    ("must be", "explicit_constraint"),
    ("cannot be", "explicit_constraint"),
)

#: Never a parameter name, whatever the punctuation.
NOT_IDENTIFIERS = frozenset((
    "parameter", "parameters", "api", "apis", "value", "values", "default", "defaults",
    "request", "requests", "response", "responses", "example", "examples", "note", "notes",
    "model", "models", "field", "fields", "option", "options", "header", "headers",
    "method", "methods", "object", "objects", "string", "number", "boolean", "integer",
    "array", "type", "types", "this", "that", "these", "those", "it", "its", "use",
    "using", "see", "also", "can", "may", "will"
))


@dataclass
class Candidate:
    """One packaged review candidate. Never gold on creation."""

    candidate_id: str
    provider: str
    document_title: str
    version_id: str
    source_url: str | None
    captured_at: str | None
    section_path: list[str]
    char_start: int
    char_end: int
    evidence_text: str
    evidence_hash: str
    context_before: str
    context_after: str
    proposed_category: str
    proposed_question: str
    proposed_atomic_claims: list[str]
    proposed_answer: str
    evidence_kind: str
    binding: str
    generator_confidence: str
    generator_notes: str
    needs_human_interpretation: bool = False
    candidate_type: str = "supported"
    verification_status: str = "candidate_unverified"
    claude_proposed: bool = True
    chatgpt_verified: bool | None = None
    schema_version: str = CANDIDATE_SCHEMA_VERSION
    revisions: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def clean(value: str) -> str:
    return value.strip().strip("`*_,.;:()[]|").strip()


def identifiers_in(text: str) -> list[str]:
    found = []
    for match in _IDENTIFIER.finditer(text):
        name = clean(match.group(1) or match.group(2) or "")
        if name and name.lower() not in NOT_IDENTIFIERS and len(name) >= 3:
            found.append(name)
    # Preserve order, drop repeats.
    return list(dict.fromkeys(found))


def _context(text: str, start: int, end: int) -> tuple[str, str]:
    """Enough surrounding source for a reviewer to judge meaning, not one sentence."""
    return text[max(0, start - CONTEXT_BEFORE):start], text[end:end + CONTEXT_AFTER]


def _section_for(sections, offset: int) -> list[str]:
    best = None
    for section in sections:
        inside = section.char_start <= offset < section.char_end
        smaller = best is None or (section.char_end - section.char_start) <= (
            best.char_end - best.char_start)
        if inside and smaller:
            best = section
    return list(best.path) if best else ["Preamble"]


def mine_table_parameters(doc: dict, limit: int = 3) -> list[Candidate]:
    """Highest-confidence source: a parameter table row.

    The parameter is the row's first cell and the default is stated in another cell
    of the *same row*, so the association is structural. This is the miner that
    exists because proximity-based extraction failed.
    """
    text = doc["text"]
    out: list[Candidate] = []
    offset = 0
    header_seen = False

    for line in text.splitlines(keepends=True):
        line_start = offset
        offset += len(line)
        if len(out) >= limit:
            break
        stripped = line.rstrip("\n")
        if _SEPARATOR.match(stripped):
            header_seen = True
            continue
        match = _TABLE_ROW.match(stripped)
        if not match or not header_seen:
            continue
        cells = [c.strip() for c in match.group("cells").split("|")]
        if len(cells) < 2:
            continue
        name = clean(cells[0])
        if not name or name.lower() in NOT_IDENTIFIERS or len(name) < 3:
            continue
        if not (("_" in name) or name.startswith("`") or re.fullmatch(r"[a-z][a-zA-Z0-9_.]{2,40}", name)):
            continue
        row_rest = " ".join(cells[1:])
        default = _DEFAULT_IN_CELL.search(row_rest)
        if not default:
            continue
        value = clean(default.group(1))
        if not value or value.lower() == name.lower():
            continue

        start = line_start + (len(line) - len(line.lstrip()))
        end = line_start + len(stripped)
        evidence = text[start:end]
        before, after = _context(text, start, end)
        out.append(Candidate(
            candidate_id="",  # assigned by the batch exporter
            provider=doc["provider"], document_title=doc["title"],
            version_id=doc["version_id"], source_url=doc.get("url"),
            captured_at=doc.get("captured_at"),
            section_path=_section_for(doc["sections"], start),
            char_start=start, char_end=end, evidence_text=evidence,
            evidence_hash=hashlib.sha256(evidence.encode("utf-8")).hexdigest(),
            context_before=before, context_after=after,
            proposed_category="exact_lookup",
            proposed_question=f"What is the default value of {name}?",
            proposed_atomic_claims=[f"{name} defaults to {value}"],
            proposed_answer=value,
            evidence_kind="parameter_table_row",
            binding="structural: parameter is the row's first cell, default stated in the same row",
            generator_confidence="high",
            generator_notes=(
                "Row-scoped association, so the value cannot belong to a different "
                "parameter. Reviewer should still confirm the row is a parameter table "
                "and not a comparison or pricing table."),
        ))
    return out


def mine_explicit_statements(doc: dict, limit: int = 2) -> list[Candidate]:
    """Prose sentences that state a relationship outright.

    Requires an explicit marker phrase *and* exactly one candidate identifier. Where
    more than one identifier is present the sentence is still packaged, but flagged
    ``needs_human_interpretation`` — that ambiguity is precisely what produced wrong
    answers when it was resolved automatically.
    """
    text = doc["text"]
    out: list[Candidate] = []
    cursor = 0
    for piece in _SENTENCE_SPLIT.split(text):
        start = text.find(piece, cursor)
        if start < 0:
            continue
        cursor = start + len(piece)
        if len(out) >= limit:
            break
        sentence = piece.strip()
        if not (60 <= len(sentence) <= 400) or sentence.startswith(("|", "#", "```")):
            continue
        lowered = sentence.lower()
        marker = next(((phrase, kind) for phrase, kind in EXPLICIT_MARKERS if phrase in lowered), None)
        if not marker:
            continue
        names = identifiers_in(sentence)
        if not names:
            continue

        end = start + len(piece)
        evidence = text[start:end]
        before, after = _context(text, start, end)
        ambiguous = len(names) > 1
        phrase, kind = marker
        out.append(Candidate(
            candidate_id="",
            provider=doc["provider"], document_title=doc["title"],
            version_id=doc["version_id"], source_url=doc.get("url"),
            captured_at=doc.get("captured_at"),
            section_path=_section_for(doc["sections"], start),
            char_start=start, char_end=end, evidence_text=evidence,
            evidence_hash=hashlib.sha256(evidence.encode("utf-8")).hexdigest(),
            context_before=before, context_after=after,
            proposed_category="exact_lookup" if kind != "explicit_deprecation" else "deprecation",
            # A placeholder prompt, not a question. The claims are empty and the
            # reviewer writes both — auto-phrasing a question here is what produced
            # unnatural gold in EXP-014R.
            proposed_question=(
                f"[REVIEWER TO WRITE] A question about {names[0]} in "
                f"{doc['title']}, answerable from the evidence below "
                f"(relationship stated: {phrase!r})."),
            proposed_atomic_claims=[],
            proposed_answer="",
            evidence_kind=kind,
            binding=("single identifier in the sentence" if not ambiguous
                     else f"AMBIGUOUS: {len(names)} identifiers present ({', '.join(names[:4])})"),
            generator_confidence="medium" if not ambiguous else "low",
            generator_notes=(
                f"Matched explicit marker {phrase!r}. No claim is proposed: the reviewer "
                "should write the question and the atomic claims from the evidence. "
                + ("More than one identifier appears, so the subject is not "
                   "machine-determinable." if ambiguous else "")),
            needs_human_interpretation=True,
        ))
    return out


__all__ = [
    "CANDIDATE_SCHEMA_VERSION", "CONTEXT_AFTER", "CONTEXT_BEFORE", "EXPLICIT_MARKERS",
    "NOT_IDENTIFIERS", "Candidate", "clean", "identifiers_in", "mine_explicit_statements",
    "mine_table_parameters",
]
