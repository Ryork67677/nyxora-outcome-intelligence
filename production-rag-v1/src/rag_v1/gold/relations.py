"""A relation has a direction, and a question that reverses it asks something false.

The source says *the experimental model rejects caller-supplied ``betas`` overrides*.
``betas`` is the thing being rejected. A miner that matched "overrides" near ``betas``
wrote *"What does ``betas`` override?"* — a question the page never answers, anchored to
evidence that looks like it should. That was ``GOLD-B005-10``, and it reached an owner.

The defence here is to stop inferring the direction and start recording it. A candidate
carries a source triple, read out of its own evidence, and a question triple, recorded
by whichever builder wrote the question. Export compares them. Two failures are refused:
the question's subject is not the source's subject, and the question's subject and object
are the source's the other way round.

Nothing in this module guesses at meaning. It finds a relation verb in the evidence,
takes what is on each side of it, and compares strings. That is narrow on purpose — a
check that tries to be clever is a check nobody can predict, and an unpredictable gate is
one a generator learns to route around.
"""

from __future__ import annotations

import re

#: Relation name → the verb forms that state it, in the active voice.
RELATION_PATTERNS = {
    "overrides": r"\boverrid(?:e|es|ing|den)\b",
    "requires": r"\brequir(?:e|es|ing|ed)\b",
    "rejects": r"\breject(?:s|ed|ing)?\b",
    "disables": r"\b(?:disabl(?:e|es|ing|ed)|prevent(?:s|ed|ing)?|"
                r"suppress(?:es|ed|ing)?)\b",
    "ignores": r"\bignor(?:e|es|ing|ed)\b",
    "replaces": r"\b(?:replac(?:e|es|ing|ed)|supersed(?:e|es|ing|ed))\b",
    "determines": r"\b(?:determin(?:e|es|ing|ed)|controls?|selects?)\b",
    "changes": r"\b(?:chang(?:e|es|ing|ed)|affects?|alters?)\b",
    "takes_precedence_over": r"\btakes? precedence over\b",
    "must_be_paired_with": r"\bmust be (?:paired|combined|used) with\b",
    "is_not_supported_on": r"\b(?:is|are) not supported on\b",
    "supports": r"\bsupports?\b",
    "returns": r"\breturns?\b",
    "accepts": r"\baccepts?\b",
    # The predicate lane's relations, so its triples read as named rather than being
    # re-split generically — a generic split cut "defaults to" after "defaults".
    "defaults_to": r"\bdefaults? to\b",
    "raises": r"\braises?\b",
    "throws": r"\bthrows?\b",
    "emits": r"\bemits?\b",
    "is_rejected": r"\b(?:is|are) rejected\b",
    "stops_with": r"\bstops? with\b",
    "fails_with": r"\bfails? with\b",
    "counts_towards": r"\bcounts? towards?\b",
    "is_limited_to": r"\b(?:is|are) limited to\b",
    "may_not_exceed": r"\b(?:may not|cannot|must not) exceed\b",
    "expires_after": r"\bexpires? after\b",
    "must_match": r"\bmust match\b",
    "transitions_to": r"\btransitions? to\b",
    "is_deprecated": r"\b(?:is|are) deprecated\b",
    "is_ignored": r"\b(?:is|are) ignored\b",
}
#: Relations where swapping the two sides does not change what is said. Nothing else may
#: be reversed, and this set stays short deliberately.
SYMMETRIC_RELATIONS = frozenset({
    "must_be_paired_with", "conflicts_with", "is_mutually_exclusive_with",
})

AGREES = "AGREES"
REVERSED = "REVERSED"
SUBJECT_MISMATCH = "SUBJECT_MISMATCH"
NOT_CHECKABLE = "NOT_CHECKABLE"

_SENTENCE_SPLIT = re.compile(r"(?<![A-Z])\.\s+(?=[A-Z`*\-\d])")
_ARTICLES = re.compile(r"^(?:the|a|an|its|their|this|that|each|any|all)\s+",
                       re.IGNORECASE)
_TRAILING = re.compile(r"[\s.,;:)\]]+$")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT.split(" ".join(text.split())) if s.strip()]


def normalise(phrase: str | None) -> str:
    """Backticks, articles and surrounding punctuation carry no direction."""
    if not phrase:
        return ""
    out = phrase.replace("`", " ").strip()
    out = _TRAILING.sub("", out)
    out = _ARTICLES.sub("", out).strip()
    return " ".join(out.lower().split())


def identifiers(phrase: str) -> set[str]:
    """The identifier-shaped tokens in a phrase, which is what a question names."""
    return {t.lower() for t in re.findall(r"[A-Za-z_][\w.]{2,}", phrase or "")}


def derive_source_triple(evidence: str, relation: str,
                         subject_hint: str | None = None) -> dict | None:
    """Read ``subject relation object`` out of the evidence sentence that states it.

    ``subject_hint`` is the question's subject. A multi-sentence span can state the same
    relation twice about different things — one batch-006 candidate asked about
    ``AWS_BEDROCK_BASE_URL`` and matched "overrides" in a neighbouring sentence about
    ``AWS_REGION`` — so sentences naming the question's subject are read first, and only
    then the rest.

    Returns ``None`` when the evidence does not state the relation at all, which is
    itself a finding and is treated as one rather than as permission.
    """
    pattern = RELATION_PATTERNS.get(relation)
    if not pattern:
        return None
    lines = sentences(evidence)
    hint = normalise(subject_hint)
    if hint:
        about_the_subject = [line for line in lines if hint in normalise(line)]
        if not about_the_subject:
            return None
        # Only sentences about the question's subject may supply the triple. Falling
        # back to the others is how a candidate ends up with a relation read off a
        # neighbouring sentence about a different setting.
        lines = about_the_subject
    for line in lines:
        match = re.search(pattern, line, re.IGNORECASE)
        if not match:
            continue
        subject = last_conjunct(line[:match.start()].strip())
        obj = line[match.end():].strip()
        if not subject or not obj:
            continue
        return {
            "source_subject": subject,
            "source_relation": relation,
            "source_object": obj,
            "source_sentence": line,
        }
    return None


#: The verbs a documentation sentence uses to predicate something of a subject. Used
#: only when the candidate's relation is not one of the directed relations above — every
#: candidate has to carry a triple, and "no relation" is not a triple.
_PREDICATE = re.compile(
    r"\b(?:is|are|was|were|has|have|must|may|can|will|should|cannot|"
    r"defaults?|returns?|raises?|applies|accepts?|emits?|sends?|sets?|uses?|"
    r"contains?|includes?|maps?|counts?|expires?|resets?|fails?|becomes?)\b",
    re.IGNORECASE)


def derive_generic_triple(evidence: str, subject_hint: str | None) -> dict | None:
    """A subject-predicate-object read of the sentence the question is asked of.

    Not a parse. It finds the sentence that mentions the question's subject, splits it
    at the first predicate verb, and records the two halves. That is enough for the
    check this module performs — whether the question and the source put the same thing
    on the same side — and it is honest about being no more than that.
    """
    hint = normalise(subject_hint)
    for line in sentences(evidence):
        if hint and hint not in normalise(line):
            continue
        match = _PREDICATE.search(line)
        if not match or match.start() == 0:
            continue
        subject = last_conjunct(line[:match.start()].strip())
        obj = line[match.end():].strip()
        if not subject or not obj:
            continue
        return {
            "source_subject": subject,
            "source_relation": match.group(0).lower(),
            "source_object": obj,
            "source_sentence": line,
            "derivation": "generic predicate split",
        }
    return None


#: "The region can also come from `AWS_REGION` or `AWS_DEFAULT_REGION`, and
#: `AWS_BEDROCK_BASE_URL` can override the endpoint." The subject of *override* is the
#: last conjunct, not the whole prefix. Reporting the prefix is not wrong, but it makes
#: the reviewer's triple table say less than it could.
_LAST_CONJUNCT = re.compile(r".*,\s+(?:and|or|but)\s+", re.DOTALL)
#: A modal between the subject and the verb belongs with the verb, not the subject.
_TRAILING_MODAL = re.compile(r"\s+(?:can|may|will|must|should|does|do|is|are)$",
                             re.IGNORECASE)


def last_conjunct(prefix: str) -> str:
    """The nearest noun phrase to the verb, when the prefix is a coordinated clause."""
    trimmed = _LAST_CONJUNCT.sub("", prefix).strip()
    trimmed = _TRAILING_MODAL.sub("", trimmed).strip()
    return trimmed or prefix.strip()


def direction(source: dict, question: dict) -> dict:
    """Does the question ask the relation the way the source states it?

    ``REVERSED`` is the ``GOLD-B005-10`` failure: the question's subject is named in the
    source's object and its object is named in the source's subject.
    ``SUBJECT_MISMATCH`` is the weaker form — the question's subject simply is not what
    the source's sentence is about.
    """
    relation = source.get("source_relation")
    if not relation or not source.get("source_subject"):
        return {"status": NOT_CHECKABLE,
                "finding": "the evidence does not state this relation in a form the "
                           "direction check can read"}

    q_subject = normalise(question.get("question_subject"))
    q_object = normalise(question.get("question_object"))
    s_subject_ids = identifiers(source["source_subject"])
    s_object_ids = identifiers(source["source_object"])
    q_subject_ids = identifiers(q_subject)
    q_object_ids = identifiers(q_object)

    subject_matches = bool(q_subject_ids & s_subject_ids) or (
        q_subject and q_subject in normalise(source["source_subject"]))
    subject_is_the_object = bool(q_subject_ids & s_object_ids)
    object_is_the_subject = bool(q_object_ids & s_subject_ids)

    if subject_is_the_object and object_is_the_subject and not subject_matches:
        if relation in SYMMETRIC_RELATIONS:
            return {"status": AGREES,
                    "finding": f"`{relation}` is symmetric, so either side may lead"}
        return {
            "status": REVERSED,
            "finding": (
                f"the source says {source['source_subject'].strip()!r} "
                f"{relation.replace('_', ' ')} {source['source_object'].strip()!r}; "
                f"the question asks it the other way round"),
        }
    if not subject_matches:
        if subject_is_the_object:
            return {
                "status": SUBJECT_MISMATCH,
                "finding": (
                    f"the question's subject {q_subject!r} is what the source's "
                    f"sentence {relation.replace('_', ' ')}, not what does the "
                    f"{relation.replace('_', ' ')}"),
            }
        return {
            "status": SUBJECT_MISMATCH,
            "finding": (f"the question's subject {q_subject!r} is not the subject of "
                        f"the source sentence {source['source_sentence']!r}"),
        }
    return {"status": AGREES, "finding": None}


def evaluate(record: dict) -> dict:
    """The whole check for one candidate, from the triples the record carries."""
    source = {k: record.get(k) for k in
              ("source_subject", "source_relation", "source_object", "source_sentence")}
    question = {k: record.get(k) for k in
                ("question_subject", "question_relation", "question_object")}
    verdict = direction(source, question)
    return {"source": source, "question": question, **verdict}


__all__ = [
    "AGREES",
    "NOT_CHECKABLE",
    "RELATION_PATTERNS",
    "REVERSED",
    "SUBJECT_MISMATCH",
    "SYMMETRIC_RELATIONS",
    "derive_generic_triple",
    "derive_source_triple",
    "direction",
    "evaluate",
    "identifiers",
    "last_conjunct",
    "normalise",
    "sentences",
]
