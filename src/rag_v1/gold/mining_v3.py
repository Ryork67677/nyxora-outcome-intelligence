"""GOLD-001 batch 003: mine varied, complete candidates from normative prose.

Batches 001 and 002 established what makes evidence trustworthy. What they did not
produce is variety: batch 002 was 15 Anthropic to 3 OpenAI and its structural half came
from three question templates, so it would test one phrasing of one fact shape rather
than the corpus.

This module mines *sentence shapes* instead of table columns. Each pattern fires only on
a sentence whose structure already contains the question and the answer, and builds both
from the captured groups — the question is never invented and then justified. That is the
difference between this and the EXP-014R generator that had to be thrown away.

Every batch-001/002 safety rule still applies and is enforced here, not assumed:

* a span must resolve its own references or be dropped (``resolve_anaphora``);
* nothing normative is drawn from fenced code, JSON literals or example helpers;
* no inferred relation label reaches the reviewer — the pattern name is internal;
* no question depends on a table header outside its own row;
* spans have a size budget, because an anchor the size of a section makes retrieval
  easy for the wrong reason.

Candidates ship complete: question, answer, atomic claims and the critical strings that
make each claim machine-checkable. Batch 001 needed a metadata cleanup because none of
that existed at creation time.
"""

from __future__ import annotations

import hashlib
import re

from rag_v1.gold.mining import (
    _SENTENCE_SPLIT,
    _context,
    _section_for,
    clean,
    code_regions,
    identifiers_in,
    inside_code,
    looks_like_code,
    resolve_anaphora,
    wellformed_problem,
)
from rag_v1.gold.normalisation import contains_claim_string

SCHEMA_VERSION = "1.1"

#: Anchors above this get flagged for review; above the hard cap they are dropped.
EVIDENCE_SOFT_CAP = 1000
EVIDENCE_HARD_CAP = 1500
#: Shorter than this and a "sentence" is usually a fragment or a heading.
MIN_EVIDENCE_CHARS = 60

_TICK = re.compile(r"`([^`]+)`")
#: A backticked span is only a *subject* if it looks like an identifier. Without this
#: the miner reads `-Infinity` as the thing being configured rather than as a value.
_IDENTIFIER_LIKE = re.compile(r"^[A-Za-z_][\w.\[\]]*(?:[=:][^\s`]{1,40})?$")
#: How far into a sentence a subject may sit before it is probably an object instead.
SUBJECT_WINDOW = 70
#: Literal values that look like identifiers but never name a thing being configured.
#: Without this the miner asks "What does `None` disable?".
_LITERAL_VALUES = frozenset({
    "true", "false", "none", "null", "nil", "nan", "infinity", "-infinity", "undefined",
    "yes", "no", "0", "1",
})
#: Base forms, so the generated question is grammatical. ``verb.rstrip("s")`` turned
#: "takes precedence over" into "takes precedence ove".
_VERB_BASE = {
    "disables": "disable", "enables": "enable", "overrides": "override",
    "requires": "require", "replaces": "replace",
    "takes precedence over": "take precedence over",
}


def _is_subject(sentence: str, ticked: str) -> bool:
    position = sentence.find(f"`{ticked}`")
    return (0 <= position <= SUBJECT_WINDOW
            and bool(_IDENTIFIER_LIKE.match(ticked))
            and ticked.strip().lower() not in _LITERAL_VALUES)


def _is_clean_fragment(text: str) -> bool:
    """Reject a captured group that the pattern clearly cut in the wrong place."""
    return ("\n" not in text and text.count("`") % 2 == 0
            and ": " not in text and not text.endswith((" the", " a", " an")))


def _is_substantive(text: str) -> bool:
    """Enough of an answer to be worth asking about."""
    stripped = _strip_trailing(text)
    return len(stripped) >= 18 and (bool(_TICK.search(stripped))
                                    or len(stripped.split()) >= 3)


def _lower_first(text: str) -> str:
    return text[0].lower() + text[1:] if text else text


def _strip_trailing(text: str) -> str:
    return text.rstrip(" .:,;")


def _ticked(text: str) -> list[str]:
    return _TICK.findall(text)


# --- patterns ---------------------------------------------------------------
#
# Each returns (category, question, answer, claims, critical_strings) or None. The
# pattern name never leaves this module: batch 001 showed that an inferred relation
# label is wrong often enough to be worse than no label, so the reviewer sees a question
# built from the sentence, not the miner's guess about what the sentence is.

def _p_conditional_result(sentence: str) -> tuple | None:
    """``If <condition>, <subject> returns/raises <result>.``"""
    match = re.match(
        r"^If (?P<cond>[^,]{12,180}), (?P<subject>[A-Za-z][^,]{0,60}?) "
        r"(?P<verb>returns|raises|rejects|responds with) (?P<result>[^.]{3,120})\.",
        sentence)
    if not match:
        return None
    cond = _strip_trailing(match.group("cond"))
    subject, verb, result = (match.group("subject"), match.group("verb"),
                             _strip_trailing(match.group("result")))
    if not (_is_clean_fragment(cond) and _is_clean_fragment(result)):
        return None
    if "\n" in subject or len(subject) > 40:
        return None  # the "subject" is the rest of an imperative sentence
    return (
        "error_behavior",
        f"What happens if {_lower_first(cond)}?",
        f"{subject.capitalize()} {verb} {result}.",
        [f"If {_lower_first(cond)}, {subject} {verb} {result}."],
        [c for c in (*_ticked(cond), *_ticked(result), result) if c],
    )


def _p_action_result(sentence: str) -> tuple | None:
    """``<Doing something> returns/raises <result>.`` — a gerund subject."""
    match = re.match(
        r"^(?P<action>[A-Z][a-z]+ing [^.]{12,160}?) "
        r"(?P<verb>returns|raises|is rejected with|produces) (?P<result>[^.]{3,120})\.",
        sentence)
    if not match:
        return None
    action = _strip_trailing(match.group("action"))
    verb, result = match.group("verb"), _strip_trailing(match.group("result"))
    if not (_is_clean_fragment(action) and _is_clean_fragment(result)):
        return None
    return (
        "error_behavior",
        f"What happens when {_lower_first(action)}?",
        f"It {verb} {result}.",
        [f"{action} {verb} {result}."],
        [c for c in (*_ticked(action), *_ticked(result), result) if c],
    )


def _p_must_value(sentence: str) -> tuple | None:
    """``<subject> must be set to <literal>.``

    The value must be a backticked or quoted literal. An earlier version accepted any
    trailing words and produced "What must `openssl` be set to? — on your.", which is
    what happens when a pattern is allowed to match prose it does not understand.
    """
    match = re.search(
        r"(?P<subject>`[^`]{2,60}`)[^.`]{0,60}? "
        r"must (?P<verb>be set to|start with|be|match|use)\s+(?:the value )?"
        r"(?P<value>`[^`]{1,60}`|\"[^\"]{1,60}\")(?=[\s.,;)]|$)",
        sentence)
    if not match:
        return None
    subject = match.group("subject")
    value = match.group("value")
    if not _is_subject(sentence, subject.strip("`")):
        return None
    if clean(subject).lower() == clean(value).lower():
        return None  # "What must `search_result` be? — `search_result`."
    verb = match.group("verb")
    return (
        "exact_constraint",
        f"What must {subject} {verb}?",
        f"{value}.",
        [f"{subject} must {verb} {value}."],
        [subject.strip("`"), value.strip("`\"")],
    )


def _p_interaction(sentence: str) -> tuple | None:
    """``When <config>, <consequence>.`` — one setting changing another's behaviour."""
    match = re.match(
        r"^(?:When|Once|If) (?P<cond>[^,]{12,160}? (?:is|are) "
        r"(?:set|enabled|disabled|present|used|configured)[^,]{0,60}), "
        r"(?P<effect>[^.]{12,180})\.",
        sentence)
    if not match:
        return None
    cond = _strip_trailing(match.group("cond"))
    effect = _strip_trailing(match.group("effect"))
    if not _ticked(cond) or not _is_substantive(effect):
        return None
    if not (_is_clean_fragment(cond) and _is_clean_fragment(effect)):
        return None
    return (
        "configuration_interaction",
        f"What happens when {_lower_first(cond)}?",
        f"{effect[0].upper()}{effect[1:]}.",
        [f"When {_lower_first(cond)}, {effect}."],
        [*_ticked(cond), *_ticked(effect)],
    )


def _p_disables_requires(sentence: str) -> tuple | None:
    """``<A> disables / requires / overrides <B>.``"""
    match = re.search(
        r"(?P<a>`[^`]{2,60}`)(?P<mid>[^.`]{0,60}?) "
        r"(?P<verb>disables|enables|overrides|requires|replaces|takes precedence over) "
        r"(?P<b>[^.]{3,120})\.",
        sentence)
    if not match:
        return None
    a, verb, b = match.group("a"), match.group("verb"), _strip_trailing(match.group("b"))
    if not _is_subject(sentence, a.strip("`")) or not _is_substantive(b):
        return None
    if not _is_clean_fragment(b):
        return None
    return (
        "configuration_interaction",
        f"What does {a} {_VERB_BASE[verb]}?",
        f"{b[0].upper()}{b[1:]}.",
        [f"{a} {verb} {b}."],
        [a.strip("`"), *_ticked(b)],
    )


def _p_lifecycle(sentence: str) -> tuple | None:
    """Deprecation, removal and compatibility stated in the current document.

    The subject must be a backticked identifier. Free proper-noun capture produced
    "Opus 4.6 and Sonnet 4.6 but" as a subject — a phrase cut mid-conjunction.
    """
    # ``[^.]`` stopped the tail at the decimal point in "Claude Opus 4.7", turning
    # "no longer supported on Claude Opus 4.7 or later models" into "on Claude Opus 4" —
    # a different and far broader claim than the source makes. The tail now runs to a
    # sentence-ending period (one not followed by a digit) instead.
    match = re.search(
        r"(?P<subject>`[^`]{2,60}`) (?:is|are|was|has been) "
        r"(?P<state>deprecated|no longer supported|removed|retired|unsupported)"
        r"(?P<rest>(?:[^.]|\.(?=\d)){0,160})\.(?!\d)",
        sentence)
    if not match:
        return None
    subject = match.group("subject")
    state = match.group("state")
    rest = _strip_trailing(match.group("rest"))
    tail = f" {rest}" if rest else ""
    tail = re.sub(r"\s+", " ", tail)
    return (
        "lifecycle",
        f"What is the documented status of {subject}?",
        f"It is {state}{tail}.",
        [f"{subject} is {state}{tail}."],
        [subject.strip("`"), state],
    )


#: A description cell that starts with one of these is a statement about the parameter,
#: so it can be read as a fact without borrowing meaning from a column heading.
_ROW_VERBS = (
    "controls", "sets", "enables", "disables", "determines", "specifies", "caps",
    "limits", "returns", "adds", "overrides", "selects", "restricts", "configures",
)


def _p_row_fact(row_cells: list[str]) -> tuple | None:
    """A table row read for what it *says*, never for what its header means.

    Batch 002's nine header-dependency defects came from asking "is this required?" — a
    question whose answer is a bare ``Yes`` whose meaning lives in a column heading
    outside the anchor. A description cell opening with a verb states a fact in its own
    words, so the row answers on its own.

    The first cell must be a backticked identifier. Without that the miner reads enum
    value tables as parameter tables and asks what the "`array` parameter" does.
    """
    if not row_cells[0].strip().startswith("`"):
        return None
    name = clean(row_cells[0])
    if not name or len(name) < 3 or not re.fullmatch(r"[a-z][a-zA-Z0-9_.]{2,40}", name):
        return None
    description = max((clean(c) for c in row_cells[1:]), key=len, default="")
    # Strip "See [x](url)" wherever it appears: a link is navigation, not a fact, and
    # it inflates both the answer and the claim with a URL.
    description = re.sub(r"\s*See \[[^\]]*\]\([^)]*\)\.?", "", description).strip()
    if not (25 <= len(description) <= 220):
        return None
    # Same rule as the definition bullets: a generic parameter name needs the row itself
    # to name something specific, or the question has a dozen answers in this corpus.
    if name.lower() in _GENERIC_OPTION_NAMES and not _ticked(description):
        return None
    first_word = description.split()[0].lower().rstrip(",")
    if first_word == "whether":
        sentence = _strip_trailing(description)
        return (
            "configuration_interaction",
            f"What does the `{name}` parameter control?",
            f"{sentence}.",
            [f"The `{name}` parameter controls {_lower_first(sentence)}."],
            [name, sentence[:60]],
        )
    if first_word not in _ROW_VERBS:
        return None
    sentence = _strip_trailing(description)
    return (
        "exact_constraint",
        f"What does the `{name}` parameter do?",
        f"{sentence}.",
        [f"The `{name}` parameter {_lower_first(sentence)}."],
        [name, sentence[:60]],
    )


def _p_raises(sentence: str) -> tuple | None:
    """``<condition clause> raises `SomeError`.`` — the shape OpenAI's docs favour."""
    match = re.match(
        r"^(?P<cond>[A-Z][^.]{14,90}?) raises (?:an? )?(?P<err>`[A-Z]\w{3,40}`)"
        r"(?P<rest>[^.;]{0,60})\.",
        sentence)
    if not match:
        return None
    cond = _strip_trailing(match.group("cond"))
    err = match.group("err")
    rest = _strip_trailing(match.group("rest"))
    if not (_is_clean_fragment(cond) and _is_clean_fragment(rest)):
        return None
    tail = f" {rest}" if rest else ""
    return (
        "error_behavior",
        f"What exception does {_lower_first(cond)} raise?",
        f"{err}{tail}.",
        [f"{cond} raises {err}{tail}."],
        [err.strip("`"), *_ticked(cond)],
    )


def _p_emitted_when(sentence: str) -> tuple | None:
    """A named event or value emitted, sent or returned under a stated condition."""
    match = re.match(
        r"^(?P<subject>`[^`]{2,60}`) (?:is|are) "
        r"(?P<verb>emitted|sent|returned|raised|invoked|called|applied) "
        r"(?P<when>when|only when|if) (?P<cond>[^.]{12,160})\.",
        sentence)
    if not match:
        return None
    subject, verb = match.group("subject"), match.group("verb")
    cond = _strip_trailing(match.group("cond"))
    if not _is_clean_fragment(cond):
        return None
    return (
        "configuration_interaction",
        f"When is {subject} {verb}?",
        f"When {_lower_first(cond)}.",
        [f"{subject} is {verb} when {_lower_first(cond)}."],
        [subject.strip("`"), *_ticked(cond)],
    )


PROSE_PATTERNS = (
    _p_conditional_result, _p_action_result, _p_raises, _p_emitted_when,
    _p_must_value, _p_interaction, _p_disables_requires, _p_lifecycle,
)


def _package(doc: dict, start: int, end: int, built: tuple, kind: str,
             confidence: str) -> dict | None:
    text = doc["text"]
    evidence = text[start:end]
    category, question, answer, claims, criticals = built

    criticals = [c for c in dict.fromkeys(clean(c) for c in criticals if c and len(c) > 2)
                 if contains_claim_string(evidence, c)]
    if not criticals:
        return None

    before, after = _context(text, start, end)
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
        "evidence_text": evidence,
        "evidence_hash": hashlib.sha256(evidence.encode("utf-8")).hexdigest(),
        "evidence_char_length": end - start,
        "context_before": before,
        "context_after": after,
        "proposed_category": category,
        "proposed_question": question,
        "proposed_answer": answer,
        "proposed_atomic_claims": claims,
        "critical_strings": criticals,
        "evidence_kind": kind,
        "candidate_type": "supported",
        "generator_confidence": confidence,
        "needs_human_interpretation": False,
        "verification_status": "candidate_unverified",
        "claude_proposed": True,
        "chatgpt_verified": None,
        "retrieval_was_not_run": True,
        "schema_version": SCHEMA_VERSION,
        "revisions": [],
    }


def mine_prose(doc: dict, limit: int = 3) -> list[dict]:
    """Complete candidates from normative sentences, one pattern at a time."""
    text = doc["text"]
    fenced = code_regions(text)
    out: list[dict] = []
    seen: set[tuple[int, int]] = set()
    cursor = 0

    for piece in _SENTENCE_SPLIT.split(text):
        if len(out) >= limit:
            break
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
        if not identifiers_in(sentence):
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

        for pattern in PROSE_PATTERNS:
            built = pattern(span.strip())
            if built is None:
                continue
            packaged = _package(doc, start, end, built, "normative_statement",
                                "high" if end - start <= EVIDENCE_SOFT_CAP else "medium")
            if packaged is not None:
                seen.add((start, end))
                out.append(packaged)
            break
    return out


def mine_row_facts(doc: dict, limit: int = 2) -> list[dict]:
    """Parameter rows, asked about what the row itself states."""
    from rag_v1.gold.mining import _SEPARATOR, _TABLE_ROW

    text = doc["text"]
    fenced = code_regions(text)
    out: list[dict] = []
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
        if not match:
            header_seen = False
            continue
        if not header_seen:
            continue
        cells = [c.strip() for c in match.group("cells").split("|")]
        if len(cells) < 2:
            continue
        built = _p_row_fact(cells)
        if built is None:
            continue
        start = line_start + (len(line) - len(line.lstrip()))
        end = line_start + len(stripped)
        if inside_code(fenced, start, end) or end - start > EVIDENCE_HARD_CAP:
            continue
        packaged = _package(doc, start, end, built, "parameter_table_row", "high")
        if packaged is not None:
            out.append(packaged)
    return out


#: ``-   `name`: Description.`` — the definition-list shape both SDK doc sets use for
#: options that never appear in a table. Mining it is what makes OpenAI coverage
#: possible without lowering the bar: their docs favour this over parameter tables.
_DEFINITION_BULLET = re.compile(
    r"^[ \t]*[-*]\s+`(?P<name>[A-Za-z_][\w.]{2,40})`:\s+(?P<desc>[A-Z][^\n]{24,240})$",
    re.MULTILINE)
#: Openers that decide which question the description can answer grammatically.
_DESCRIPTIVE_OPENERS = ("this", "the", "a", "an", "optional", "override", "by")
#: Option names common enough that a bare question about them is ambiguous across the
#: corpus. Kept only when the description carries an identifier that pins the context —
#: "What is the `url` option?" is not a question a gold set can answer.
_GENERIC_OPTION_NAMES = frozenset({
    "agent", "url", "kind", "chunk", "snapshot", "history", "name", "type", "id",
    "data", "input", "output", "model", "tools", "text", "value", "result", "content",
    "error", "message", "response", "request", "config", "options", "params", "state",
    "description", "path", "delta", "enabled", "command", "query", "prompt", "role",
    "source", "target", "timeout", "limit", "size", "format", "mode", "status",
})


def mine_definition_bullets(doc: dict, limit: int = 2) -> list[dict]:
    """Option definitions written as bullets rather than table rows.

    Same contract as the row miner and for the same reason: the bullet names the option
    and describes it in one line, so nothing is borrowed from a heading elsewhere. The
    claim mirrors the source's own ``name: description`` form rather than paraphrasing
    it into a sentence the source never wrote.
    """
    text = doc["text"]
    fenced = code_regions(text)
    out: list[dict] = []

    for match in _DEFINITION_BULLET.finditer(text):
        if len(out) >= limit:
            break
        start, end = match.start(), match.end()
        if inside_code(fenced, start, end) or looks_like_code(match.group("desc")):
            continue
        name = match.group("name")
        description = re.sub(r"\s*See \[[^\]]*\]\([^)]*\)\.?", "",
                             match.group("desc"))
        description = re.sub(r"\s*See below[^.]*\.\s*$", "", description).strip()
        if not (40 <= len(description) <= 220):
            continue
        # A generic name is only usable when the description itself names something
        # specific. "What is the `path` option?" has a dozen answers in this corpus, and
        # qualifying it by section would put the scope outside the anchor — which is
        # exactly the table-header defect batch 002 was built to stop repeating.
        if name.lower() in _GENERIC_OPTION_NAMES and not _ticked(description):
            continue
        opener = description.split()[0].lower().rstrip(",")
        if opener in _ROW_VERBS:
            question = f"What does the `{name}` option do?"
        elif opener == "whether":
            question = f"What does the `{name}` option control?"
        elif opener in _DESCRIPTIVE_OPENERS:
            question = f"What is the `{name}` option?"
        else:
            continue
        sentence = _strip_trailing(description)
        built = (
            "exact_constraint", question, f"{sentence}.",
            [f"`{name}`: {sentence}."],
            [name, sentence[:60]],
        )
        packaged = _package(doc, start, end, built, "definition_bullet", "high")
        if packaged is not None:
            out.append(packaged)
    return out


_OPTION_QUESTION = re.compile(r"^What is the `(?P<name>[^`]+)` option\?$")


def _compose_question(first: dict, second: dict, label: str) -> str:
    """Join two anchored facts into one question a developer would actually ask.

    Concatenating the member questions produces "what is the `type` option?, and what
    is the `country` option??" — two questions glued together, with the punctuation to
    prove it. Where both members are option definitions the pair has a natural joint
    form; otherwise the two clauses are joined once, with one question mark.
    """
    first_option = _OPTION_QUESTION.match(first["proposed_question"])
    second_option = _OPTION_QUESTION.match(second["proposed_question"])
    if first_option and second_option:
        return (f"What do the `{first_option.group('name')}` and "
                f"`{second_option.group('name')}` options specify in {label}?")
    left = _strip_trailing(first["proposed_question"]).rstrip("?")
    right = _lower_first(_strip_trailing(second["proposed_question"]).rstrip("?"))
    return f"{left}, and {right}?"


def compose_multi_hop(candidates: list[dict], limit: int = 3) -> list[dict]:
    """Pair two anchored facts about the same identifier into one question.

    Both spans stay independently anchored and both claims stay attached to the span
    that carries them, so partial retrieval cannot earn full credit. Nothing is inferred
    across the pair: the question asks for both facts, it does not ask the reader to
    derive a third.
    """
    def keys(candidate: dict) -> list[tuple]:
        # A shared identifier is the strongest link; a shared section is the weaker one
        # that still means the two facts are about the same feature.
        shared = [(candidate["version_id"], "id", i)
                  for i in _ticked(candidate["proposed_question"])]
        if candidate["section_path"]:
            shared.append((candidate["version_id"], "section",
                           " > ".join(candidate["section_path"])))
        return shared

    grouped: dict[tuple, list[dict]] = {}
    for candidate in candidates:
        for key in keys(candidate):
            grouped.setdefault(key, []).append(candidate)

    out: list[dict] = []
    used: set[str] = set()
    for key, group in sorted(grouped.items()):
        if len(out) >= limit or len(group) < 2:
            continue
        pair = None
        for first in group:
            for second in group:
                if first is second or first["evidence_hash"] == second["evidence_hash"]:
                    continue
                # Two spans asking the same thing are one fact twice over, not a
                # multi-hop case. This is the check that keeps the category honest.
                if first["proposed_question"] == second["proposed_question"]:
                    continue
                if {first["evidence_hash"], second["evidence_hash"]} & used:
                    continue
                pair = (first, second)
                break
            if pair:
                break
        if pair is None:
            continue
        first, second = pair
        used.update({first["evidence_hash"], second["evidence_hash"]})
        label = key[2] if key[1] == "id" else first["section_path"][-1]
        combined_length = first["evidence_char_length"] + second["evidence_char_length"]
        out.append({
            **first,
            "candidate_id": "",
            "proposed_category": "multi_hop",
            "evidence_kind": "multi_span",
            "linked_by": key[1],
            "proposed_question": _compose_question(first, second, label),
            "proposed_answer": f"{first['proposed_answer']} {second['proposed_answer']}",
            "proposed_atomic_claims": (first["proposed_atomic_claims"]
                                       + second["proposed_atomic_claims"]),
            "critical_strings": list(dict.fromkeys(
                first["critical_strings"] + second["critical_strings"])),
            "expected_evidence": [
                {"version_id": c["version_id"], "char_start": c["char_start"],
                 "char_end": c["char_end"], "section_path": c["section_path"],
                 "evidence_text": c["evidence_text"],
                 "evidence_hash": c["evidence_hash"],
                 "evidence_char_length": c["evidence_char_length"]}
                for c in (first, second)],
            "evidence_char_length": combined_length,
            "generator_confidence": "medium",
            "needs_human_interpretation": True,
            "multi_hop_note": (
                "Two independently anchored spans. A retriever earns credit only by "
                "finding both, and each claim is checked against the span it came from. "
                "The question asks for both facts; it does not ask the reader to derive "
                "a third, because the source does not state one."),
        })
    return out


__all__ = [
    "EVIDENCE_HARD_CAP", "EVIDENCE_SOFT_CAP", "MIN_EVIDENCE_CHARS", "SCHEMA_VERSION",
    "compose_multi_hop", "mine_definition_bullets", "mine_prose", "mine_row_facts",
]
