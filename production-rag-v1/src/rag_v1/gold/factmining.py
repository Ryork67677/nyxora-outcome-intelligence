"""Mine the raw facts a bridge is built from.

The batch-003 miner emits *complete candidates*: a sentence that matches one of four
question templates, packaged with a question, an answer and atomic claims. That is the
right shape for a single-fact lookup and the wrong shape for a hop. A hop needs two
sentences that happen to talk about the same identifier — one stating a condition, one
stating what follows — and the template that would have turned either of them into a
standalone question is irrelevant to whether they compose.

Requiring a template match before a sentence could be considered for a bridge was why
the first batch-004 run found no pairs at all: the pool it searched was 58 sentences
across the whole corpus, and the two halves of a hop were almost never both in it.

So this module mines facts, not questions. Every guard the batch-003 miner applies to a
span still applies here — fenced code, code-looking prose, anaphora, fragment shapes,
size caps — because those protect the *evidence*, and the evidence is the part being
reused. What is dropped is only the requirement that the sentence be answerable on its
own, which is the very property a hop member is not supposed to have.

The batch-003 miner is not modified. Batch 003 is closed, and a change there would
change what a closed batch reproduces.
"""

from __future__ import annotations

import hashlib

from rag_v1.gold.mining import (
    _SENTENCE_SPLIT,
    _context,
    _section_for,
    code_regions,
    identifiers_in,
    inside_code,
    looks_like_code,
    resolve_anaphora,
    wellformed_problem,
)
from rag_v1.gold.mining_v3 import EVIDENCE_HARD_CAP, MIN_EVIDENCE_CHARS, SCHEMA_VERSION
from rag_v1.gold.multihop import is_condition, is_consequence
from rag_v1.gold.normalisation import contains_claim_string

#: A fact carries at most this many critical strings. The composition check asks whether
#: one span already contains all of the other hop's strings; a hop carrying eight strings
#: makes that test vacuous, because some of them are shared vocabulary.
MAX_CRITICAL_STRINGS = 3


def _claim(sentence: str) -> str:
    """The claim a fact asserts: the source sentence, trimmed, not paraphrased.

    A template would have to reword the sentence to fit, and rewording is where batch
    001 introduced claims its evidence did not support. The source's own words are
    checkable against the source by construction.
    """
    return " ".join(sentence.split()).rstrip()


def iter_guarded_spans(doc: dict, keep=None, limit: int = 400):
    """Walk a document's sentences, yielding only spans that clear every guard.

    Every miner needs the same sequence — split, reject fenced code and code-shaped
    prose, resolve anaphora backwards, reject fragments, hold the size caps, require a
    checkable identifier — and each one that reimplements it is a chance for the guards
    to drift apart. ``keep`` decides which *sentences* are of interest; the guards are
    not the caller's business.

    Yields ``(start, end, span_text, identifiers)`` for the resolved span.
    """
    text = doc["text"]
    fenced = code_regions(text)
    seen: set[tuple[int, int]] = set()
    cursor = 0
    yielded = 0

    for piece in _SENTENCE_SPLIT.split(text):
        if yielded >= limit:
            return
        start = text.find(piece, cursor)
        if start < 0:
            continue
        cursor = start + len(piece)
        end = start + len(piece)
        sentence = piece.strip()
        if not (MIN_EVIDENCE_CHARS <= len(sentence) <= 400):
            continue
        if sentence.startswith(("|", "#", "```", "---")):
            continue
        if inside_code(fenced, start, end) or looks_like_code(sentence):
            continue
        if keep is not None and not keep(sentence):
            continue

        identifiers = identifiers_in(sentence)
        if not identifiers:
            continue

        resolved = resolve_anaphora(text, start, end)
        if resolved is None:
            continue
        start, end = resolved
        span = text[start:end]
        if (inside_code(fenced, start, end) or looks_like_code(span)
                or wellformed_problem(span) is not None
                or not (MIN_EVIDENCE_CHARS <= end - start <= EVIDENCE_HARD_CAP)
                or (start, end) in seen):
            continue
        seen.add((start, end))
        yielded += 1
        yield start, end, span, identifiers


def package_fact(doc: dict, start: int, end: int, span: str, critical: list[str],
                 role: str, kind: str = "normative_statement") -> dict:
    """Wrap a guarded span with the provenance every candidate carries."""
    before, after = _context(doc["text"], start, end)
    return {
        "candidate_id": "",
        "provider": doc["provider"],
        "document_title": doc["title"],
        "version_id": doc["version_id"],
        "source_url": doc.get("url"),
        "captured_at": str(doc.get("captured_at")),
        "section_path": _section_for(doc["sections"], start),
        "char_start": start,
        "char_end": end,
        "evidence_text": span,
        "evidence_hash": hashlib.sha256(span.encode("utf-8")).hexdigest(),
        "evidence_char_length": end - start,
        "context_before": before,
        "context_after": after,
        "fact_role": role,
        "proposed_question": None,
        "proposed_answer": _claim(span),
        "proposed_atomic_claims": [_claim(span)],
        "critical_strings": critical,
        "evidence_kind": kind,
        "candidate_type": "supported",
        "generator_confidence": "medium",
        "retrieval_was_not_run": True,
        "schema_version": SCHEMA_VERSION,
    }


def mine_bridge_facts(doc: dict, limit: int = 400) -> list[dict]:
    """Condition and consequence sentences, packaged as reusable hop members."""
    out: list[dict] = []

    def keep(sentence: str) -> bool:
        return is_condition(sentence) or is_consequence(sentence)

    for start, end, span, identifiers in iter_guarded_spans(doc, keep, limit):
        critical = [i for i in identifiers if contains_claim_string(span, i)]
        if not critical:
            continue
        critical = critical[:MAX_CRITICAL_STRINGS]
        condition = is_condition(span)
        consequence = is_consequence(span)
        before, after = _context(doc["text"], start, end)
        out.append({
            "candidate_id": "",
            "provider": doc["provider"],
            "document_title": doc["title"],
            "version_id": doc["version_id"],
            "source_url": doc.get("url"),
            "captured_at": str(doc.get("captured_at")),
            "section_path": _section_for(doc["sections"], start),
            "char_start": start,
            "char_end": end,
            "evidence_text": span,
            "evidence_hash": hashlib.sha256(span.encode("utf-8")).hexdigest(),
            "evidence_char_length": end - start,
            "context_before": before,
            "context_after": after,
            "fact_role": ("condition_and_consequence" if condition and consequence
                          else "condition" if condition else "consequence"),
            # A hop member has no standalone question by design. These fields exist so a
            # fact can flow through the composer with the miner's own vocabulary; the
            # exported case's question is composed, never one of these.
            "proposed_question": None,
            "proposed_answer": _claim(span),
            "proposed_atomic_claims": [_claim(span)],
            "critical_strings": critical,
            "evidence_kind": "normative_statement",
            "candidate_type": "supported",
            "generator_confidence": "medium",
            "retrieval_was_not_run": True,
            "schema_version": SCHEMA_VERSION,
        })
    return out


__all__ = ["MAX_CRITICAL_STRINGS", "mine_bridge_facts"]
