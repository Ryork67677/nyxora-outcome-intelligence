"""What operational fact does a candidate actually state? — batch 006 defect E.

Duplicate control compares normalised question text, span offsets and span text. Two
provider libraries documenting the same behaviour share none of those, so the same fact
enters the benchmark twice and the benchmark counts it as two. ``GOLD-B005-11`` (the
OpenAI Python library) and ``GOLD-B006-06`` (the TypeScript/JavaScript library) both say
that ``AWS_BEDROCK_BASE_URL`` overrides the region-derived Bedrock endpoint. Nothing in
the old comparison could see it, and the owner caught it by reading.

The identity of a fact is its **(subject, relation, object) triple**, normalised. Batch
006 records that triple on every candidate; batches 001-005 predate it, so a triple is
*derived from the frozen evidence* when a record does not carry one — from the evidence,
never from the question, because the evidence is the part that cannot drift.

**This flags. It never drops.** Two libraries genuinely differing in behaviour is a real
case and only a reviewer can tell that apart from a restatement, which is exactly the
judgement the preregistration reserves for a person. A checker that auto-dropped here
would silently delete real coverage to make a number look tidy.

Where a record carries no triple and none can be derived, it is reported as
``not_comparable`` rather than as clean. Saying "checked" of something never checked is
the failure this module exists to stop, and it would be an odd module that committed it.
"""

from __future__ import annotations

import re

from rag_v1.gold.normalisation import strip_markdown_links, unescape_markdown

#: Relation verbs that state an operational relation between two things, mapped to one
#: canonical form. Deliberately a closed set: a stemmer would fold unrelated verbs
#: together, and a fact's identity is not the place to guess. Longest first, so
#: "defaults to" is read before "default".
RELATION_FORMS: tuple[tuple[str, str], ...] = (
    (r"overrid(?:es|e|ing|den)", "override"),
    (r"defaults?\s+to|defaulting\s+to", "default_to"),
    (r"disabl(?:es|e|ing|ed)", "disable"),
    (r"enabl(?:es|e|ing|ed)", "enable"),
    (r"replac(?:es|e|ing|ed)(?:\s+by)?", "replace"),
    (r"supersed(?:es|e|ing|ed)", "supersede"),
    (r"requir(?:es|e|ing|ed)", "require"),
    (r"accepts?|accepting|accepted", "accept"),
    (r"rejects?|rejecting|rejected", "reject"),
    (r"returns?|returning|returned", "return"),
    (r"rais(?:es|e|ing|ed)", "raise"),
    (r"throws?|throwing|thrown", "throw"),
    (r"emits?|emitting|emitted", "emit"),
    (r"ignor(?:es|e|ing|ed)", "ignore"),
    (r"expires?\s+after|expiring\s+after", "expire_after"),
    (r"(?:is|are|was|were)\s+limited\s+to", "be_limited_to"),
    (r"counts?\s+towards?|counting\s+towards?", "count_towards"),
    (r"transitions?\s+to|transitioning\s+to", "transition_to"),
    (r"(?:is|are)\s+deprecated", "be_deprecated"),
    (r"must\s+match", "must_match"),
    (r"controls?|controlling|controlled", "control"),
    (r"sets?|setting", "set"),
)
_RELATION = re.compile(
    "|".join(f"(?P<r{i}>\\b{p}\\b)" for i, (p, _) in enumerate(RELATION_FORMS)),
    re.IGNORECASE)
_CANONICAL = {f"r{i}": canon for i, (_, canon) in enumerate(RELATION_FORMS)}

#: An identifier a reader would recognise as the thing being configured: a code span, an
#: ENV_VAR, or a dotted path. This is what a subject normally is in this corpus.
_IDENTIFIER = re.compile(
    r"`(?P<code>[^`]+)`"
    r"|\b(?P<env>[A-Z][A-Z0-9]{2,}(?:_[A-Z0-9]+)+)\b"
    r"|\b(?P<dotted>[a-z][\w]*(?:\.[a-z][\w]*)+)\b")

#: Determiners and bare qualifiers that carry no identity. Dropped from either end of a
#: term so "the derived endpoint" and "the endpoint" name the same thing.
_NOISE_WORDS = frozenset({
    "a", "an", "the", "its", "their", "this", "that", "these", "those", "derived",
    "regional", "default", "current", "given", "same", "documented", "configured",
    "resulting", "corresponding", "associated", "relevant", "specified",
})
_CODE_SPAN = re.compile(r"`[^`]*`")
_PUNCT = re.compile(r"[^\w\s.:/<>-]")
#: Punctuation that ends a phrase rather than belonging to a term. Stripped from the
#: head word, so a recorded object written "the endpoint." matches one written
#: "the endpoint" — dots inside a dotted path are kept, because those identify.
_TRAILING_PUNCT = re.compile(r"[.:;,]+$")
#: A call written as an identifier: ``bedrock(...)`` names ``bedrock``, and the argument
#: list is not part of the name.
_CALL_SUFFIX = re.compile(r"\s*\([^)]*\)\s*$")

#: Generic relations, which a sentence often carries alongside the one it is actually
#: about: "**set** `X` to **override** `Y`" is a fact about overriding. Ranked last so a
#: specific operational relation wins when both appear. Rank is not a fallback order —
#: every relation here is real — it is which of two true readings identifies the fact.
_WEAK_RELATIONS = frozenset({"set", "control", "require", "be_limited_to"})


def normalise_term(text: str | None) -> str:
    """Reduce a subject or object to a comparable form, keeping what identifies it.

    Markdown plumbing and backticks go, case folds, determiners and bare qualifiers are
    stripped from both ends, and a trailing noun phrase is reduced to its head — English
    noun phrases are head-final, so "the derived `https://…` endpoint" and "the endpoint"
    both come back as ``endpoint``.
    """
    if not text:
        return ""
    out = unescape_markdown(strip_markdown_links(text))
    out = _CALL_SUFFIX.sub("", out.strip())
    out = out.replace("`", " ")
    out = _PUNCT.sub(" ", out).lower()
    words = [_TRAILING_PUNCT.sub("", w) for w in out.split()]
    words = [w for w in words if w]
    while words and words[0] in _NOISE_WORDS:
        words.pop(0)
    while words and words[-1] in _NOISE_WORDS:
        words.pop()
    if not words:
        return ""
    # A term that is a single identifier keeps all of it; a phrase reduces to its head.
    return words[0] if len(words) == 1 else words[-1]


def normalise_relation(text: str | None) -> str:
    """Map a relation verb to its canonical form, or "" when it names no relation."""
    if not text:
        return ""
    match = _RELATION.search(unescape_markdown(strip_markdown_links(text)))
    if not match:
        return ""
    return _CANONICAL[match.lastgroup]


def derive_triple(evidence_text: str) -> tuple[str, str, str] | None:
    """Read a (subject, relation, object) triple out of frozen evidence.

    The subject is the nearest identifier *before* the relation verb, which is where the
    subject of an English clause sits; the object is the phrase after it, reduced to its
    head. Returns ``None`` when the span states no operational relation — a great many
    spans do not, and inventing one for them is how a duplicate check starts producing
    false matches.
    """
    text = unescape_markdown(strip_markdown_links(evidence_text or ""))
    found: list[tuple[int, int, tuple[str, str, str]]] = []
    for match in _RELATION.finditer(text):
        before, after = text[:match.start()], text[match.end():]
        identifiers = [m.group("code") or m.group("env") or m.group("dotted")
                       for m in _IDENTIFIER.finditer(before)]
        if not identifiers:
            continue
        relation = _CANONICAL[match.lastgroup]
        # Code spans are masked before the phrase is cut, so a dot inside a URL or a
        # dotted path does not end the object early.
        masked = _CODE_SPAN.sub("   ", after)
        cut = re.split(r"[.;,]|\bor\b", masked, maxsplit=1)[0]
        subject, target = normalise_term(identifiers[-1]), normalise_term(cut)
        if subject and target:
            found.append((relation in _WEAK_RELATIONS, match.start(),
                          (subject, relation, target)))
    if not found:
        return None
    # Specific relations before generic ones, then leftmost — the first thing the
    # sentence actually asserts.
    return min(found)[2]


def triple(record: dict) -> tuple[str, str, str] | None:
    """The candidate's fact triple: the one it records, else one read from its evidence.

    A recorded triple wins, because a generator that named its own relation knew which
    clause it built from. Derivation is the fallback for the batches that predate the
    field.
    """
    subject = normalise_term(record.get("source_subject"))
    relation = normalise_relation(record.get("source_relation"))
    obj = normalise_term(record.get("source_object"))
    if subject and relation and obj:
        return subject, relation, obj
    for span in record.get("expected_evidence") or []:
        derived = derive_triple(span.get("evidence_text", ""))
        if derived:
            return derived
    return None


def duplicate_facts(candidates: list[dict], prior: list[dict]) -> list[dict]:
    """Flag candidates whose fact triple already appears in ``prior`` or in the batch.

    Every flag names both sides and the triple they share, so a reviewer can read the two
    spans and decide. Nothing is dropped here: see the module docstring.
    """
    seen: dict[tuple[str, str, str], list[dict]] = {}
    for record in prior:
        found = triple(record)
        if found:
            seen.setdefault(found, []).append(record)

    flags: list[dict] = []
    for record in candidates:
        found = triple(record)
        if found is None:
            flags.append({
                "candidate_id": record.get("candidate_id"),
                "status": "not_comparable",
                "reason": "no triple recorded and none derivable from the evidence",
            })
            continue
        matches = seen.get(found, [])
        if matches:
            flags.append({
                "candidate_id": record.get("candidate_id"),
                "status": "duplicate_fact",
                "triple": list(found),
                "also_stated_by": [m.get("candidate_id") for m in matches],
                "providers": sorted({str(m.get("provider")) for m in matches}
                                    | {str(record.get("provider"))}),
                "documents": sorted({str(m.get("document_title")) for m in matches}
                                    | {str(record.get("document_title"))}),
                "reason": ("the same (subject, relation, object) fact is already in the "
                           "benchmark from another document"),
                "action": "flag for review — a reviewer decides, this check never drops",
            })
        seen.setdefault(found, []).append(record)
    return flags


__all__ = [
    "RELATION_FORMS",
    "derive_triple",
    "duplicate_facts",
    "normalise_relation",
    "normalise_term",
    "triple",
]
