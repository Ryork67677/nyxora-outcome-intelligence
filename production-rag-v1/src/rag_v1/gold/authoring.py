"""Turn a mined fact into a candidate: a question, an answer, and checkable claims.

Each builder here writes the question from what its fact actually says, using only
identifiers the span contains. Nothing is paraphrased: an answer is the source's own
sentence with markdown link plumbing removed, and a claim is the sentence verbatim. That
is deliberate — batch 001's drift between claim and evidence came from rewording, and a
question template that needs to invent a word is a template that will eventually invent
a fact.

Question *shape* varies by what the fact is, which is also how §26's template-monotony
problem is avoided: a precedence rule and a size limit ask different questions because
they are different kinds of statement, not because a generator alternated phrasings.
"""

from __future__ import annotations

import re

from rag_v1.gold.normalisation import contains_claim_string

_MD_LINK = re.compile(r"\[([^\]]+)\]\((?:[^)]+)\)|\[([^\]]+)\]\[(?:[^\]]+)\]")
#: "If <clause>, <result>." Split at the last comma that leaves a well-formed outcome.
_CONDITIONAL_OPENER = re.compile(r"^(?P<marker>If|When|Unless)\s+(?P<rest>.+)$")
_NOT_A_RESULT_OPENER = frozenset({
    "which", "that", "where", "and", "or", "but", "so", "while", "whereas", "though",
    "although", "including", "unless", "then",
})
_SENTENCE_BOUNDARY = re.compile(r"(?<![A-Z])\.\s+(?=[A-Z`*\-\d])")
_ERROR_WORDS = re.compile(
    r"\b(?:error|fails?|failure|rejected?|raises?|exception|invalid|4\d\d|5\d\d|"
    r"refus\w+|abort\w*|denied|stop_reason)\b", re.IGNORECASE)
_LIFECYCLE_WORDS = re.compile(
    r"\b(?:deprecated|no longer supported|removed|retired|superseded|migrat\w+|"
    r"replaced by|still functional)\b", re.IGNORECASE)
#: A demonstrative determiner points outside the span; "such as" does not.
DANGLING_REFERENCE = re.compile(r"\b(?:these|those|such)\s+(?!as\b)[a-z]{3,}",
                                re.IGNORECASE)
#: "What happens if you want to change this?" — a wish is not a condition, and "this"
#: refers to a paragraph the span does not contain. Both shapes reached batch 005's
#: first draft.
_NOT_A_CONDITION = re.compile(
    r"^(?:you (?:want|need|wish|would like|just need|prefer)|"
    r"(?:we|i) (?:want|need)|this\b|that\b|it\b)", re.IGNORECASE)
_BARE_THIS = re.compile(r"\bthis\s*[?.]|\bthis\s+(?:one|value|setting|behaviou?r)\b",
                        re.IGNORECASE)
#: An outcome needs a verb. Participles and bare noun phrases are the tail of a longer
#: sentence, not the thing that happens.
_FINITE_VERB = re.compile(
    r"\b(?:is|are|was|were|has|have|will|can|may|must|does|do|returns?|raises?|fails?|"
    r"stops?|starts?|keeps?|removes?|adds?|sends?|applies|becomes?|throws?|uses?|"
    r"requires?|ignores?|disables?|enables?|continues?|resumes?|exits?|call|set|pass|"
    r"rerun|use|treat|expect)\b", re.IGNORECASE)
_NOT_AN_OUTCOME = re.compile(r"^(?:not\b|containing\b|including\b|such as\b|and\b|"
                             r"or\b|with\b|without\b)", re.IGNORECASE)
CLAUSE_MIN, CLAUSE_MAX = 12, 180
RESULT_MIN, RESULT_MAX = 12, 240


def _balanced(text: str) -> bool:
    """Does the fragment open and close every delimiter it contains?"""
    for opener, closer in (("{", "}"), ("[", "]"), ("(", ")")):
        if text.count(opener) != text.count(closer):
            return False
    return text.count("`") % 2 == 0 and text.count('"') % 2 == 0


def plain(text: str) -> str:
    """Drop markdown link plumbing from prose meant to be read as a question."""
    return " ".join(_MD_LINK.sub(lambda m: m.group(1) or m.group(2), text).split())


def sentence(text: str) -> str:
    text = " ".join(text.split()).strip()
    return text if text.endswith((".", "!", "?", ":")) else text + "."


def _first_identifier(fact: dict) -> str | None:
    return fact["critical_strings"][0] if fact.get("critical_strings") else None


def split_conditional(text: str) -> tuple[str, str, str] | None:
    """Split "If X, Y." into condition and outcome at the right comma."""
    opener = _CONDITIONAL_OPENER.match(text)
    if opener is None:
        return None
    marker, rest = opener.group("marker"), opener.group("rest")
    best = None
    for match in re.finditer(r",\s+", rest):
        clause, result = rest[:match.start()].strip(), rest[match.end():].strip()
        if not (CLAUSE_MIN <= len(clause) <= CLAUSE_MAX):
            continue
        if not (RESULT_MIN <= len(result) <= RESULT_MAX):
            continue
        if result.split()[0].lower().strip(",") in _NOT_A_RESULT_OPENER:
            continue
        if _SENTENCE_BOUNDARY.search(clause) or _SENTENCE_BOUNDARY.search(result):
            continue
        # The outcome has to be a clause with something happening in it. Splitting at
        # the last comma of "When X declines, the API returns Y, not an error." left
        # "not an error." as the answer and put the answer inside the question.
        if not _FINITE_VERB.search(result):
            continue
        # A split inside a brace, bracket or quote cuts through a JSON literal and
        # produces a question ending mid-object.
        if not (_balanced(clause) and _balanced(result)):
            continue
        if _NOT_AN_OUTCOME.match(result):
            continue
        best = (marker, clause, result)
    return best


def build_conditional(fact: dict) -> dict | None:
    """A sentence that states its own condition and its own outcome."""
    text = " ".join(fact["evidence_text"].split())
    split = split_conditional(text)
    if split is None:
        return None
    marker, clause, result = split
    if not result.endswith("."):
        return None
    if clause.lower().startswith(("true", "so", "not", "any of")):
        return None
    # The condition has to be a state of the world, not a state of the reader, and it
    # has to name what it is about.
    if _NOT_A_CONDITION.match(clause.strip()):
        return None
    question = plain(f"What happens {marker.lower()} {clause}?")
    if DANGLING_REFERENCE.search(question) or _BARE_THIS.search(question):
        return None
    if not re.search(r"`[^`]+`", question):
        # A condition with no identifier in it cannot be checked against the evidence,
        # and reads as a paraphrase of the prose around it.
        return None
    answer = plain(result)
    reasoning = ("lifecycle_compatibility_migration" if _LIFECYCLE_WORDS.search(result)
                 else "error_behavior" if _ERROR_WORDS.search(result)
                 else "configuration_interaction")
    return {
        "reasoning_type": reasoning,
        "secondary_category": "conditional_behavior",
        "question": question,
        "answer": answer[0].upper() + answer[1:],
        "atomic_claims": [sentence(text)],
    }


#: One question shape per relation. A precedence rule and a fallback rule are different
#: questions because they are different statements.
_INTERACTION_QUESTIONS = {
    "takes_precedence": "If both {a} and {b} are supplied, which one applies?",
    "overrides": "What does {a} override?",
    "disables": "What does {a} turn off?",
    "requires": "What does {a} require?",
    "mutually_exclusive": "Can {a} and {b} be used together?",
    "ignored_under_condition": "When is {a} ignored?",
    "conditional_availability": "When is {a} available?",
    "fallback": "What does {a} fall back to?",
    "changes_behaviour": "What does {a} change the behaviour of?",
}


def build_interaction(fact: dict) -> dict | None:
    """A documented relation between two named settings."""
    identifiers = fact.get("interacting_identifiers") or fact["critical_strings"]
    if len(identifiers) < 2:
        return None
    template = _INTERACTION_QUESTIONS.get(fact["interaction_relation"])
    if template is None:
        return None
    text = " ".join(fact["evidence_text"].split())
    question = plain(template.format(a=f"`{identifiers[0]}`", b=f"`{identifiers[1]}`"))
    if DANGLING_REFERENCE.search(question):
        return None
    return {
        "reasoning_type": "configuration_interaction",
        "secondary_category": fact["interaction_relation"],
        "question": question,
        "answer": plain(text),
        "atomic_claims": [sentence(text)],
    }


_CONSTRAINT_QUESTIONS = {
    "maximum": "What is the documented limit on {a}?",
    "bound": "What bound does the documentation put on {a}?",
    "required_value": "What must {a} be?",
    "required_format": "What format must {a} use?",
    "prohibited": "What must {a} not do?",
}


def build_constraint(fact: dict) -> dict | None:
    """A hard limit or a required format."""
    subject = _first_identifier(fact)
    template = _CONSTRAINT_QUESTIONS.get(fact["constraint_kind"])
    if subject is None or template is None:
        return None
    text = " ".join(fact["evidence_text"].split())
    question = plain(template.format(a=f"`{subject}`"))
    return {
        "reasoning_type": "exact_lookup",
        "secondary_category": f"constraint_{fact['constraint_kind']}",
        "question": question,
        "answer": plain(text),
        "atomic_claims": [sentence(text)],
    }


_LIFECYCLE_QUESTIONS = {
    "deprecation": "Is {a} still supported?",
    "removal": "What happened to {a}?",
    "migration": "What should I move to instead of {a}?",
    "compatibility": "Where is {a} supported?",
}


def build_lifecycle(fact: dict) -> dict | None:
    """A support status: deprecated, removed, migrated, still compatible."""
    subject = _first_identifier(fact)
    template = _LIFECYCLE_QUESTIONS.get(fact["lifecycle_kind"])
    if subject is None or template is None:
        return None
    text = " ".join(fact["evidence_text"].split())
    question = plain(template.format(a=f"`{subject}`"))
    if DANGLING_REFERENCE.search(question):
        return None
    return {
        "reasoning_type": "lifecycle_compatibility_migration",
        "secondary_category": fact["lifecycle_kind"],
        "question": question,
        "answer": plain(text),
        "atomic_claims": [sentence(text)],
    }


def build_cross_component_ambiguity(finding: dict) -> dict | None:
    """The same field name meaning different things in two components."""
    first, second = finding["readings"]
    term = finding["ambiguous_term"]
    question = (f"In {first['document_title']}, what does the `{term}` field mean, and "
                f"how does that differ from {second['document_title']}?")
    claims = [f"In {reading['document_title']}, `{term}` is: "
              f"{sentence(reading['description'])}"
              for reading in (first, second)]
    return {
        "reasoning_type": "ambiguity_disambiguation",
        "secondary_category": "cross_component",
        "question": plain(question),
        "answer": plain(" ".join(claims)),
        "atomic_claims": claims,
        "ambiguous_term": term,
        "candidate_interpretations": [
            {"scope": reading["document_title"], "meaning": reading["description"]}
            for reading in (first, second)],
        "required_scope_to_answer": (
            f"Which component the `{term}` field belongs to. It is documented in "
            f"{first['document_title']} and in {second['document_title']} with "
            "different meanings, so the answer is undetermined until the component is "
            "named."),
        "needs_human_interpretation": True,
    }


def build_comparison(finding: dict) -> dict | None:
    """Two documented behaviours of one concept, asked as a difference."""
    first, second = finding["readings"]
    term = finding["ambiguous_term"]
    question = (f"How does `{term}` differ between {first['document_title']} and "
                f"{second['document_title']}?")
    claims = [f"In {reading['document_title']}, `{term}` is: "
              f"{sentence(reading['description'])}"
              for reading in (first, second)]
    return {
        "reasoning_type": "comparison",
        "secondary_category": "cross_component",
        "question": plain(question),
        "answer": plain(" ".join(claims)),
        "atomic_claims": claims,
        "needs_human_interpretation": True,
    }


def compose_multi_hop_question(bridge: str, condition_text: str) -> str:
    """Write the hop's question from what span 1 actually sets."""
    for value in re.findall(r"`([^`]{1,30})`", condition_text):
        if value != bridge and re.match(r"^(?:True|False|None|null|-?\d[\w.]*|"
                                        r"[A-Za-z_][\w.-]{0,30})$", value):
            return f"If I set `{bridge}` to `{value}`, what happens?"
    return f"If I use `{bridge}` as the documentation describes, what happens as a result?"


def strings_in(text: str, strings: list[str]) -> list[str]:
    return [s for s in strings if not contains_claim_string(text, s)]


__all__ = [
    "DANGLING_REFERENCE", "build_comparison", "build_conditional", "build_constraint",
    "build_cross_component_ambiguity", "build_interaction", "build_lifecycle",
    "compose_multi_hop_question", "plain", "sentence", "split_conditional",
    "strings_in",
]
