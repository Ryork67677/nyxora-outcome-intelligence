"""EXP-011: controlled query-side retrieval representations.

Why this exists
---------------
Ten experiments changed the *document* side. EXP-010 closed that line: truncation
was eliminated completely and retrieval moved by 0.000, and its decisive
measurement was that 21 of 22 expected answers were **already visible** to the
encoder. The remaining failures are ranking failures — the retriever reads the
right text and scores it below competing text.

The query has been a raw user-question string since EXP-000. This module builds
additional *views* of it.

Design rules this module enforces
--------------------------------
* **The raw query is never replaced.** Every function here returns an
  *additional* representation. Fusion decides what wins, so a bad transform costs
  ranking positions rather than the answer.
* **No knowledge of the evaluation set.** Every function is a pure function of the
  query string. Nothing here imports the eval package, reads the golden file, or
  contains a golden question, answer, section path or document name. Rules are
  general English question-scaffolding rules, not per-question rules.
* **Technical content is protected, never guessed.** Identifiers, numbers,
  versions, status codes and provider names the user actually wrote survive
  verbatim. Provider names are never *added* when the user did not write one.
* **Added terms carry provenance.** Anything a transform introduces is recorded
  with the rule that introduced it, so a reader can check that no fact leaked in.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

QUERY_TRANSFORM_VERSION = "1.0"

# A token keeps identifier punctuation so ``client.messages.create`` and
# ``max_tokens`` survive as single units.
_TOKEN_RE = re.compile(r"`[^`]+`|[A-Za-z0-9_./\-]+|[^\sA-Za-z0-9]")
_WORD_RE = re.compile(r"^[A-Za-z]+$")

#: Conversational scaffolding. General English question form — interrogatives,
#: auxiliaries, modals, articles, pronouns, politeness. Nothing domain-specific,
#: and nothing that could encode an answer.
FILLER = frozenset((
    "a", "an", "the", "this", "that", "these", "those", "i", "we", "you", "they", "it", "me",
    "us", "them", "my", "our", "your", "its", "their", "am", "is", "are", "was", "were", "be",
    "been", "being", "do", "does", "did", "done", "can", "could", "will", "would", "shall",
    "should", "may", "might", "must", "have", "has", "had", "please", "kindly", "just",
    "simply", "actually", "really", "there", "here", "what", "which", "who", "whom", "whose",
    "when", "where", "why", "how", "of", "to", "in", "on", "at", "for", "with", "by", "from",
    "as", "into", "about", "over", "under", "and", "or", "but", "if", "then", "than", "so",
    "such"
))

#: Register differences between how people ask and how reference documentation
#: states limits. General English, source-independent, and deliberately tiny.
#: Every application is recorded in ``added_terms`` with this rule's name.
PHRASE_ALIASES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("at", "most"), ("maximum",)),
    (("at", "maximum"), ("maximum",)),
    (("no", "more", "than"), ("maximum",)),
    (("up", "to"), ("maximum",)),
    (("at", "least"), ("minimum",)),
    (("no", "less", "than"), ("minimum",)),
    (("how", "many"), ("number",)),
    (("how", "much"), ("amount",)),
    (("how", "long"), ("duration",)),
    (("by", "default"), ("default",)),
)

#: General API vocabulary. Used only to *recognise* words already in the query.
OPERATION_WORDS = frozenset((
    "create", "list", "delete", "update", "get", "retrieve", "send", "receive", "cancel",
    "stream", "batch", "upload", "download", "count", "return", "set", "configure", "enable",
    "disable", "expire", "refresh", "poll", "submit"
))

#: Words that name the thing a question is asking about.
PROPERTY_WORDS = frozenset((
    "maximum", "minimum", "default", "limit", "size", "length", "count", "number", "amount",
    "duration", "rate", "timeout", "price", "cost", "version", "status", "code", "error",
    "format", "type", "value", "range"
))


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text)


def is_protected(token: str) -> bool:
    """Content that must survive every transform verbatim.

    Identifiers, anything carrying a digit, back-quoted spans, acronyms and
    capitalised product names. Protection is decided from the token's own shape,
    never from a list of corpus terms — a list would be a channel for corpus
    knowledge to enter the query.
    """
    if token.startswith("`") and token.endswith("`"):
        return True
    if any(ch.isdigit() for ch in token):
        return True
    if any(ch in token for ch in ("_", ".", "/", "-")) and any(c.isalnum() for c in token):
        return True
    if len(token) > 1 and token.isupper():
        return True
    if token[:1].isupper() and _WORD_RE.match(token):
        # A capitalised plain word is a product name unless it is ordinary
        # scaffolding capitalised by sentence position — "What", "How", "Can".
        # Product names never appear in FILLER, so this needs no position
        # information and behaves the same mid-sentence.
        return token.lower() not in FILLER
    return False


@dataclass
class QueryView:
    """One retrieval representation of a user question."""

    name: str
    text: str
    origin: str
    removed_terms: list[str] = field(default_factory=list)
    added_terms: list[dict] = field(default_factory=list)
    fields: dict = field(default_factory=dict)

    def stats(self, raw: str) -> dict:
        return {
            "view": self.name,
            "text": self.text,
            "origin": self.origin,
            "raw_token_count": len(_tokens(raw)),
            "view_token_count": len(_tokens(self.text)),
            "terms_removed": self.removed_terms,
            "terms_added": self.added_terms,
            "identifiers_preserved": identifiers(raw) <= identifiers(self.text),
            "numbers_preserved": numbers(raw) <= numbers(self.text),
            "fields": self.fields,
        }


def identifiers(text: str) -> set[str]:
    """Identifier-shaped tokens, used by the preservation checks and tests."""
    out = set()
    for token in _tokens(text):
        stripped = token.strip("`").strip(".,:;?!()[]{}")
        if not stripped or not any(c.isalnum() for c in stripped):
            continue
        if any(ch in stripped for ch in ("_", ".", "/")) or (
            len(stripped) > 1 and stripped.isupper()
        ):
            out.add(stripped)
    return out


def numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:[.,]\d+)*", text))


def raw_view(query: str) -> QueryView:
    """The user's question, untouched. Always present in every configuration."""
    return QueryView(name="raw", text=query, origin="user")


def technical_normalized_query(query: str) -> QueryView:
    """Strip conversational scaffolding, keep every technical signal.

    Subtractive by default: the only additions come from ``PHRASE_ALIASES``, a
    fixed list of general English limit/quantity phrasings, and each application is
    recorded. Protected tokens are never removed or rewritten.
    """
    tokens = _tokens(query)
    lowered = [t.lower().strip(".,:;?!") for t in tokens]

    kept: list[str] = []
    removed: list[str] = []
    added: list[dict] = []
    index = 0
    while index < len(tokens):
        matched = False
        for phrase, replacement in PHRASE_ALIASES:
            end = index + len(phrase)
            if tuple(lowered[index:end]) == phrase and not any(
                is_protected(t) for t in tokens[index:end]
            ):
                kept.extend(replacement)
                removed.extend(tokens[index:end])
                added.append({
                    "terms": list(replacement),
                    "rule": "PHRASE_ALIASES",
                    "from": " ".join(tokens[index:end]),
                })
                index = end
                matched = True
                break
        if matched:
            continue

        token = tokens[index]
        bare = token.strip(".,:;?!")
        if is_protected(token):
            kept.append(bare)
        elif not any(c.isalnum() for c in token):
            removed.append(token)  # punctuation
        elif bare.lower() in FILLER:
            removed.append(token)
        else:
            kept.append(bare)
        index += 1

    text = " ".join(k for k in kept if k).strip()
    # A transform that empties the query is worse than no transform.
    if not text:
        text = query.strip()
        added.append({"terms": [], "rule": "EMPTY_FALLBACK", "from": query})
    return QueryView(name="normalized", text=text, origin="technical_normalized_query",
                     removed_terms=removed, added_terms=added)


def decompose_query(query: str) -> dict:
    """Extract retrieval concepts that are *present in the question*.

    This is a query representation, not an answer. Nothing is inferred that the
    user did not write: entities come from the question's own capitalised spans and
    identifiers, operations and properties are recognised only if their word
    already appears, and the asked-property fallback comes from the interrogative
    the user used.
    """
    tokens = [t for t in _tokens(query) if any(c.isalnum() for c in t)]
    bare = [t.strip(".,:;?!") for t in tokens]
    lowered = [t.lower() for t in bare]

    # Entities: runs of capitalised words, plus identifier-shaped tokens. The
    # first word of a sentence is capitalised by grammar, not by being a name, so
    # a single leading capitalised word is not treated as an entity on its own.
    entities: list[str] = []
    run: list[str] = []
    for position, token in enumerate(bare):
        if is_protected(token) and not token[:1].isdigit():
            if position == 0 and _WORD_RE.match(token) and not token.isupper():
                continue
            run.append(token)
        else:
            if run:
                entities.append(" ".join(run))
                run = []
    if run:
        entities.append(" ".join(run))

    operations = [t for t in lowered if t in OPERATION_WORDS]
    properties = [t for t in lowered if t in PROPERTY_WORDS]

    # If the question named no property word, take one from the interrogative
    # form itself — still only from what the user wrote.
    if not properties:
        for phrase, replacement in PHRASE_ALIASES:
            end = len(phrase)
            for start in range(len(lowered) - end + 1):
                if tuple(lowered[start:start + end]) == phrase:
                    properties.extend(replacement)
                    break
            if properties:
                break

    return {
        "entities": entities,
        "operations": sorted(set(operations)),
        "asked_property": sorted(set(properties)),
        "identifiers": sorted(identifiers(query)),
        "numbers": sorted(numbers(query)),
    }


def structured_query(query: str) -> QueryView:
    """Render the extracted concepts as one additional retrieval query."""
    parts = decompose_query(query)
    pieces: list[str] = []
    pieces.extend(parts["entities"])
    # An identifier already inside an entity run would otherwise be repeated.
    entity_words = {w.lower() for e in parts["entities"] for w in e.split()}
    pieces.extend(i for i in parts["identifiers"] if i.lower() not in entity_words)
    pieces.extend(parts["operations"])
    pieces.extend(parts["asked_property"])
    pieces.extend(parts["numbers"])

    seen: set[str] = set()
    ordered: list[str] = []
    for piece in pieces:
        if piece and piece.lower() not in seen:
            seen.add(piece.lower())
            ordered.append(piece)

    text = " ".join(ordered).strip()
    added = [{"terms": parts["asked_property"], "rule": "decompose_query.asked_property",
              "from": query}] if parts["asked_property"] else []
    if not text:
        # Nothing recognisable: fall back to the normalized view rather than
        # emitting an empty query, and say so.
        fallback = technical_normalized_query(query)
        return QueryView(name="structured", text=fallback.text, origin="structured_fallback_normalized",
                         added_terms=added, fields=parts)
    return QueryView(name="structured", text=text, origin="structured_query",
                     added_terms=added, fields=parts)


def build_views(query: str, views: tuple[str, ...] = ("raw", "normalized", "structured")) -> list[QueryView]:
    """Build the requested representations. ``raw`` is always available."""
    builders = {
        "raw": raw_view,
        "normalized": technical_normalized_query,
        "structured": structured_query,
    }
    unknown = set(views) - set(builders)
    if unknown:
        raise ValueError(f"Unknown query view(s): {sorted(unknown)}")
    return [builders[name](query) for name in views]


__all__ = [
    "FILLER", "OPERATION_WORDS", "PHRASE_ALIASES", "PROPERTY_WORDS",
    "QUERY_TRANSFORM_VERSION", "QueryView", "build_views", "decompose_query",
    "identifiers", "is_protected", "numbers", "raw_view", "structured_query",
    "technical_normalized_query",
]
