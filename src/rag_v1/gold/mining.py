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

# --- batch 002 preregistered miner changes ----------------------------------
#
# These four rules were written down after batch 001 was verified and BEFORE batch 002
# was generated, so they cannot be tuned to its outcome. They are not to be changed on
# the basis of batch 002 results.
#
#   1. Reject or extend anaphoric spans so the anchor contains its own antecedent. (D1)
#   2. Do not export a proposed relation label to the reviewer. (D2)
#   3. Reject normative-rule candidates drawn from fenced code or JSON literals. (D3)
#   4. Raise the share of structural candidates.

#: A span opening on one of these refers outside itself. Batch 001 shipped three.
_ANAPHORIC_OPENER = re.compile(
    r"^\W*(if\s+(?:true|false|so|not)|otherwise|instead|then|however|therefore|"
    r"it\b|they\b|this\s+(?:is|means|can|will|returns)|that\s+is|such\b|here\b|"
    r"there\b|both\b|each\s+of|any\s+of|all\s+of|either\b)",
    re.IGNORECASE)
#: Nouns whose scope decides what a claim is even about. "The model determines…" is
#: only checkable if the span says which model.
_SCOPE_NOUNS = (
    "model", "models", "endpoint", "endpoints", "parameter", "parameters", "method",
    "methods", "client", "clients", "tool", "tools", "guardrail", "guardrails",
    "setting", "settings", "field", "fields", "option", "options", "error", "errors",
)
#: A referring expression whose head noun must already be in the span.
_REFERRING = re.compile(
    r"\b(these|those|this|that|the)\s+(" + "|".join(_SCOPE_NOUNS) + r")\b",
    re.IGNORECASE)
#: Fenced code. A rule cannot be read out of a sample.
_CODE_FENCE = re.compile(r"^[ \t]*(?:```|~~~)", re.MULTILINE)
#: Assignments, JSON keys and bare closing brackets: the shape of an example.
_CODE_LINE = re.compile(
    r'''^\s*[\w.\[\]"']+\s*=\s*\S|^\s*[\]\})],?\s*$|^\s*"[\w_]+"\s*:'''
    r"|^\s*(?:raise|return|import|def|class)\s",
    re.MULTILINE)
#: How far a span may grow to find its own antecedent before it is dropped instead.
MAX_EXTENSION_SENTENCES = 3
#: A required/optional column cell that states the answer outright.
_REQUIRED_IN_CELL = re.compile(r"^(yes|no|required|optional)$", re.IGNORECASE)

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
    #: Literal strings that must appear inside the span. The golden validator only
    #: checks claims marked critical, so a candidate without these is not claim-checked.
    critical_strings: list[str] = field(default_factory=list)
    #: True when rule 1 grew the span backwards to capture its own antecedent.
    anchor_extended: bool = False

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


#: A numbered-list marker the sentence splitter leaves stranded on the end of a span.
_TRAILING_LIST_MARKER = re.compile(r"\s*\n\s*\d+\.\s*$")
#: Markdown links carry URLs that inflate a span's length without adding any prose.
_MARKDOWN_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)|\[([^\]]*)\]\[[^\]]*\]")
#: The least prose a span may carry once link URLs are discounted.
MIN_PROSE_CHARS = 55
#: A span opening on a bare backticked option followed by a comma is a list item.
_LIST_ITEM_FRAGMENT = re.compile(r"^`[^`]+`\s*,")


def prose_without_links(span: str) -> str:
    """The span with markdown link targets removed, so length means what it says.

    Without this a span like ``See [Route matching](https://…long…).`` clears a
    60-character minimum on URL alone and reaches a reviewer as evidence.
    """
    return _MARKDOWN_LINK.sub(lambda m: m.group(1) or m.group(2) or "", span)


def wellformed_problem(span: str) -> str | None:
    """Reject a span that is a fragment rather than a statement.

    This is not one of the four preregistered rules — it is a defect those rules
    exposed. Extending spans backwards (rule 1) made the sentence splitter's behaviour
    on numbered lists visible: it cuts items mid-clause and strands the next item's
    marker on the end, producing spans that start lowercase and end in "\n2.".
    """
    stripped = _TRAILING_LIST_MARKER.sub("", span).strip()
    if not stripped:
        return "empty after trimming a stranded list marker"
    if not stripped.endswith((".", "!", "?", ":")):
        return f"does not end a sentence: {stripped[-24:]!r}"
    first = stripped[0]
    if not (first.isupper() or first in "*-|`" or first.isdigit()):
        return f"starts mid-sentence: {stripped[:24]!r}"
    # "`required`, which requires the LLM to use a tool" — a list item whose subject is
    # an option named in the stem above it. The identifier reads like a subject but the
    # thing it is an option *of* is outside the span.
    if _LIST_ITEM_FRAGMENT.match(stripped):
        return f"is a list item whose stem is outside the span: {stripped[:32]!r}"
    if len(prose_without_links(stripped)) < MIN_PROSE_CHARS:
        return "too little prose once link URLs are discounted"
    return None


def code_regions(text: str) -> list[tuple[int, int]]:
    """Character ranges covered by fenced code blocks.

    Rule 3. A span inside a fence is a sample, and a sample configuration is not a
    documented rule — conflating the two is what produced batch 001's only outright
    FAIL and what made the EXP-014R generator unusable.
    """
    fences = [m.start() for m in _CODE_FENCE.finditer(text)]
    return [(fences[i], fences[i + 1]) for i in range(0, len(fences) - 1, 2)]


def inside_code(regions: list[tuple[int, int]], start: int, end: int) -> bool:
    return any(start < region_end and end > region_start
               for region_start, region_end in regions)


def looks_like_code(span: str) -> bool:
    return bool(_CODE_LINE.search(span))


def _previous_sentence_start(text: str, start: int) -> int | None:
    """Walk back one sentence from ``start``. None when there is nothing before it."""
    window = text[:start].rstrip()
    if not window:
        return None
    boundary = max(window.rfind(". "), window.rfind(".\n"), window.rfind("\n\n"),
                   window.rfind("? "), window.rfind("! "))
    if boundary == -1:
        return 0 if start > 0 else None
    candidate = boundary + 1
    while candidate < start and text[candidate] in " \n\t":
        candidate += 1
    return candidate if candidate < start else None


def anaphora_problem(span: str) -> str | None:
    """Name the reference the span cannot resolve on its own, or None if it can.

    Rule 1, made mechanical. Two shapes, both seen in batch 001:

    * the span *opens* on a reference — "If true, an exception is raised";
    * the span refers to a scope it never names — "any of these models".

    In the second case the test is whether the head noun already appears earlier in the
    span. "these models" is fine once the span also says which models.
    """
    stripped = span.lstrip()
    if _ANAPHORIC_OPENER.match(stripped):
        return f"opens on a reference: {stripped[:32]!r}"
    for match in _REFERRING.finditer(span):
        noun = match.group(2).lower()
        earlier = span[:match.start()].lower()
        if noun in earlier or noun.rstrip("s") in earlier:
            continue
        return f"refers to {match.group(0)!r} with no antecedent in the span"
    return None


def resolve_anaphora(text: str, start: int, end: int) -> tuple[int, int] | None:
    """Grow the span backwards until it resolves its own references, or give up.

    Returns the resolved span, or None when the candidate should be dropped. Dropping
    is a legitimate outcome: batch 001 shipped three spans that could not be checked
    against themselves, and a candidate nobody can verify is worse than no candidate.
    """
    if anaphora_problem(text[start:end]) is None:
        return start, end
    for _ in range(MAX_EXTENSION_SENTENCES):
        previous = _previous_sentence_start(text, start)
        if previous is None:
            return None
        start = previous
        if anaphora_problem(text[start:end]) is None:
            return start, end
    return None


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

    Requires an explicit marker phrase *and* at least one candidate identifier. The
    reviewer still writes the question and the claims: auto-phrasing them is what
    produced unnatural gold in EXP-014R, and batch 001 gave no evidence that changed.

    Three batch-002 rules apply here. The span must resolve its own references or be
    dropped (rule 1); the marker that selected the sentence is **not** exported, because
    it was wrong on five of sixteen batch-001 candidates and steered the reviewer's first
    reading (rule 2); and a span drawn from fenced code or shaped like code is refused
    outright (rule 3).
    """
    text = doc["text"]
    fenced = code_regions(text)
    out: list[Candidate] = []
    seen_spans: set[tuple[int, int]] = set()
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
        if not any(phrase in lowered for phrase, _ in EXPLICIT_MARKERS):
            continue
        names = identifiers_in(sentence)
        if not names:
            continue

        end = start + len(piece)
        # Rule 3, before anything else: never build a rule out of a sample.
        if inside_code(fenced, start, end) or looks_like_code(text[start:end]):
            continue
        # Rule 1: resolve the span's own references, or drop the candidate.
        resolved = resolve_anaphora(text, start, end)
        if resolved is None:
            continue
        start, end = resolved
        if inside_code(fenced, start, end) or looks_like_code(text[start:end]):
            continue
        # Trim a stranded list marker off the end rather than shipping it.
        trailing = _TRAILING_LIST_MARKER.search(text[start:end])
        if trailing:
            end = start + trailing.start()
        if wellformed_problem(text[start:end]) is not None:
            continue
        if (start, end) in seen_spans:
            continue
        seen_spans.add((start, end))

        evidence = text[start:end]
        before, after = _context(text, start, end)
        names = identifiers_in(evidence) or names
        ambiguous = len(names) > 1
        out.append(Candidate(
            candidate_id="",
            provider=doc["provider"], document_title=doc["title"],
            version_id=doc["version_id"], source_url=doc.get("url"),
            captured_at=doc.get("captured_at"),
            section_path=_section_for(doc["sections"], start),
            char_start=start, char_end=end, evidence_text=evidence,
            evidence_hash=hashlib.sha256(evidence.encode("utf-8")).hexdigest(),
            context_before=before, context_after=after,
            proposed_category="exact_lookup",
            # A placeholder prompt, not a question, and deliberately without the marker
            # that selected the sentence. Rule 2: the label was wrong often enough to be
            # worse than no label.
            proposed_question=(
                "[REVIEWER TO WRITE] A question answerable from the evidence below, "
                f"which mentions {', '.join(f'`{n}`' for n in names[:3])}."),
            proposed_atomic_claims=[],
            proposed_answer="",
            # Rule 2: one neutral kind for all prose. The relation is the reviewer's to
            # determine from the sentence, not the miner's to assert.
            evidence_kind="prose_statement",
            binding=("single identifier in the span" if not ambiguous
                     else f"AMBIGUOUS: {len(names)} identifiers present "
                          f"({', '.join(names[:4])})"),
            generator_confidence="medium" if not ambiguous else "low",
            generator_notes=(
                "The reviewer writes the question and the atomic claims from the "
                "evidence; no relation is proposed. The span was checked to resolve its "
                "own references and is not drawn from example code. "
                + ("More than one identifier appears, so the subject is not "
                   "machine-determinable." if ambiguous else "")),
            needs_human_interpretation=True,
            anchor_extended=evidence != piece.strip(),
        ))
    return out


#: Column headers whose cell states a fact about the row's parameter outright.
_TYPE_VALUES = re.compile(
    r"^(string|number|integer|boolean|bool|object|array|float|enum|"
    r"array of strings|array of objects)$", re.IGNORECASE)


def _column_rows(text: str, headers: tuple[str, ...], fenced: list[tuple[int, int]]):
    """Walk parameter tables that carry one of ``headers``, yielding (name, cell, span).

    Shared by the requiredness and type miners so both bind the same way: the parameter
    is the row's first cell and the fact is another cell of the *same row*.
    """
    offset = 0
    header_seen = False
    column: int | None = None
    for line in text.splitlines(keepends=True):
        line_start = offset
        offset += len(line)
        stripped = line.rstrip("\n")
        if _SEPARATOR.match(stripped):
            header_seen = True
            continue
        match = _TABLE_ROW.match(stripped)
        if not match:
            header_seen = False
            column = None
            continue
        cells = [c.strip() for c in match.group("cells").split("|")]
        if not header_seen:
            lowered = [clean(c).lower() for c in cells]
            column = next((i for i, c in enumerate(lowered) if c in headers), None)
            continue
        if column is None or column >= len(cells) or len(cells) < 2:
            continue
        name = clean(cells[0])
        if not name or name.lower() in NOT_IDENTIFIERS or len(name) < 3:
            continue
        if not (("_" in name) or re.fullmatch(r"[a-z][a-zA-Z0-9_.]{2,40}", name)):
            continue
        start = line_start + (len(line) - len(line.lstrip()))
        end = line_start + len(stripped)
        if inside_code(fenced, start, end):
            continue
        yield name, clean(cells[column]), start, end


def mine_table_types(doc: dict, limit: int = 3) -> list[Candidate]:
    """Structural: a parameter's type, read from its own row.

    Rule 4 again, and for a second reason beyond volume. A batch whose structural half
    is one question template repeated is not twelve independent facts, it is one fact
    twelve times over, and it would test a retriever's handling of one phrasing rather
    than of the corpus. Mining a second column shape keeps the structural share honest.
    """
    text = doc["text"]
    fenced = code_regions(text)
    out: list[Candidate] = []
    for name, cell, start, end in _column_rows(text, ("type", "type?"), fenced):
        if len(out) >= limit:
            break
        if not _TYPE_VALUES.fullmatch(cell):
            continue
        evidence = text[start:end]
        before, after = _context(text, start, end)
        out.append(Candidate(
            candidate_id="",
            provider=doc["provider"], document_title=doc["title"],
            version_id=doc["version_id"], source_url=doc.get("url"),
            captured_at=doc.get("captured_at"),
            section_path=_section_for(doc["sections"], start),
            char_start=start, char_end=end, evidence_text=evidence,
            evidence_hash=hashlib.sha256(evidence.encode("utf-8")).hexdigest(),
            context_before=before, context_after=after,
            proposed_category="exact_lookup",
            proposed_question=f"What type does the `{name}` parameter take?",
            proposed_atomic_claims=[f"`{name}` is of type {cell}."],
            proposed_answer=f"`{cell}`",
            evidence_kind="parameter_table_row",
            binding=("structural: parameter is the row's first cell, type is another "
                     "cell of the same row"),
            generator_confidence="high",
            generator_notes=(
                "Row-scoped association. Reviewer should confirm the table is a "
                "parameter table and that the column header means the parameter's own "
                "type rather than, say, a return type."),
            critical_strings=[name, cell],
        ))
    return out


def mine_table_required(doc: dict, limit: int = 3) -> list[Candidate]:
    """Structural: whether a parameter is required, read from its own row.

    Rule 4 asks for a larger share of structural candidates, and this is the honest way
    to get it — a required/optional column states the answer outright in the same row as
    the parameter, so the candidate ships complete rather than as a packet for the
    reviewer to author. It is the same row-scoped binding as the default-value miner and
    the same reason: batch 001's two structural candidates were the only two that needed
    no re-authoring at all.
    """
    text = doc["text"]
    fenced = code_regions(text)
    out: list[Candidate] = []
    offset = 0
    header_seen = False
    required_column: int | None = None

    for line in text.splitlines(keepends=True):
        line_start = offset
        offset += len(line)
        if len(out) >= limit:
            break
        stripped = line.rstrip("\n")
        match = _TABLE_ROW.match(stripped)
        if _SEPARATOR.match(stripped):
            header_seen = True
            continue
        if not match:
            header_seen = False
            required_column = None
            continue
        cells = [c.strip() for c in match.group("cells").split("|")]
        if not header_seen:
            # A header row: remember which column states requiredness, if any.
            lowered = [clean(c).lower() for c in cells]
            required_column = next(
                (i for i, c in enumerate(lowered) if c in ("required", "required?")), None)
            continue
        if required_column is None or required_column >= len(cells) or len(cells) < 2:
            continue

        name = clean(cells[0])
        if not name or name.lower() in NOT_IDENTIFIERS or len(name) < 3:
            continue
        if not (("_" in name) or re.fullmatch(r"[a-z][a-zA-Z0-9_.]{2,40}", name)):
            continue
        state = clean(cells[required_column])
        if not _REQUIRED_IN_CELL.fullmatch(state):
            continue

        start = line_start + (len(line) - len(line.lstrip()))
        end = line_start + len(stripped)
        if inside_code(fenced, start, end):
            continue
        evidence = text[start:end]
        before, after = _context(text, start, end)
        is_required = state.lower() in ("yes", "required")
        answer = "Yes, it is required." if is_required else "No, it is optional."
        out.append(Candidate(
            candidate_id="",
            provider=doc["provider"], document_title=doc["title"],
            version_id=doc["version_id"], source_url=doc.get("url"),
            captured_at=doc.get("captured_at"),
            section_path=_section_for(doc["sections"], start),
            char_start=start, char_end=end, evidence_text=evidence,
            evidence_hash=hashlib.sha256(evidence.encode("utf-8")).hexdigest(),
            context_before=before, context_after=after,
            proposed_category="exact_lookup",
            proposed_question=f"Is the `{name}` parameter required?",
            proposed_atomic_claims=[
                f"`{name}` is {'required' if is_required else 'optional'}."],
            proposed_answer=answer,
            evidence_kind="parameter_table_row",
            binding=("structural: parameter is the row's first cell, requiredness is "
                     f"column {required_column} of the same row"),
            generator_confidence="high",
            generator_notes=(
                "Row-scoped association, so the state cannot belong to a different "
                "parameter. Reviewer should confirm the table is a parameter table and "
                "that the column header means what it appears to mean."),
            critical_strings=[name, state],
        ))
    return out


__all__ = [
    "CANDIDATE_SCHEMA_VERSION",
    "CONTEXT_AFTER",
    "CONTEXT_BEFORE",
    "EXPLICIT_MARKERS",
    "MAX_EXTENSION_SENTENCES",
    "MIN_PROSE_CHARS",
    "NOT_IDENTIFIERS",
    "Candidate",
    "anaphora_problem",
    "clean",
    "code_regions",
    "identifiers_in",
    "inside_code",
    "looks_like_code",
    "mine_explicit_statements",
    "mine_table_parameters",
    "mine_table_required",
    "mine_table_types",
    "prose_without_links",
    "resolve_anaphora",
    "wellformed_problem",
]
