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

from rag_v1.gold.normalisation import contains_claim_string, strip_markdown_links
from rag_v1.gold.questionform import phrasal_predicate, states_non_support

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
#: §17. A comma between two sibling literals is a list separator, not a clause boundary.
#: "When a `ComputerTool` is present, `tool_choice="computer"`, `"computer_use"`, and
#: `"computer_use_preview"` are all accepted" split at the *second* comma, leaving the
#: condition ending mid-enumeration and the outcome opening on the tail of a list. Each
#: half is separately balanced, so the delimiter check could not see it.
_ENUMERATION_TAIL = re.compile(
    r"""^(?:`[^`]*`|"[^"]*"|'[^']*')\s*,?\s*(?:and|or)\b""")
_ENDS_IN_LITERAL = re.compile(r"""(?:`[^`]*`|"[^"]*"|'[^']*')\s*$""")

CLAUSE_MIN, CLAUSE_MAX = 12, 180
RESULT_MIN, RESULT_MAX = 12, 240


def _balanced(text: str) -> bool:
    """Does the fragment open and close every delimiter it contains?"""
    for opener, closer in (("{", "}"), ("[", "]"), ("(", ")")):
        if text.count(opener) != text.count(closer):
            return False
    return text.count("`") % 2 == 0 and text.count('"') % 2 == 0


def plain(text: str) -> str:
    """Drop markdown link plumbing from prose meant to be read as a question.

    §Fix B: the shared stripper handles inline, full-reference and collapsed links, and
    keeps a code-span label intact. Evidence is never passed through here.
    """
    return " ".join(strip_markdown_links(text).split())


def sentence(text: str) -> str:
    text = " ".join(text.split()).strip()
    return text if text.endswith((".", "!", "?", ":")) else text + "."


#: "... is not supported on Claude Sonnet 5 and returns a 400 error." The place is what
#: comes after the preposition and before the sentence continues into something else.
_NON_SUPPORT_TARGET = re.compile(
    r"(?:is|are)\s+not\s+supported\s+(?:on|in|for|by)\s+"
    r"(?P<target>.+?)(?=\s+(?:and|or|but)\b|\s*[.,;]|$)", re.IGNORECASE)


def non_support_target(text: str) -> str | None:
    """Where the evidence says something is *not* supported, if it names a place.

    The link is stripped before the sentence is cut, because the pattern stops at the
    first full stop and a URL is full of them: one batch-006 draft asked *"Is
    ``fallbacks`` supported on the [Message Batches API](https://platform?"*. A target
    that still carries link punctuation after stripping is not a place name, and no
    question is built from it.
    """
    match = _NON_SUPPORT_TARGET.search(strip_markdown_links(text))
    if not match:
        return None
    target = match.group("target").strip(" .,;:")
    if not target or re.search(r"[\[\]()<>]|https?:", target):
        return None
    return target


def _after_phrasal(text: str, predicate: str, preposition: str) -> str | None:
    """What the phrasal predicate points at — the object a bare copula would lose."""
    match = re.search(
        re.escape(f"must be {predicate} {preposition}") + r"\s+(?P<object>[^.;]+)",
        text, re.IGNORECASE)
    return match.group("object").strip(" .,;:") if match else None


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
        # A literal on each side of the comma, with the outcome continuing into "and"
        # or "or": that comma separates list items, and splitting there cuts an
        # enumeration in half.
        if _ENDS_IN_LITERAL.search(clause) and _ENUMERATION_TAIL.match(result):
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
        # §Fix D: the builder knows which identifier it made the subject. Recording it
        # here is the only place that knowledge is not a guess.
        "question_subject": f"`{identifiers[0]}`",
        "question_relation": fact["interaction_relation"],
        "question_object": f"`{identifiers[1]}`",
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
    relation = f"constraint_{fact['constraint_kind']}"
    obj = None
    # §15: "What must `dispatcher` be?" asked of "must be paired with the matching
    # `fetch` implementation" truncates the predicate away and asks for an identity the
    # evidence never gives. When the evidence has a phrasal predicate, the question has
    # to carry it — that was GOLD-B005-18.
    if fact["constraint_kind"] == "required_value":
        phrasal = phrasal_predicate(text)
        if phrasal:
            predicate, preposition = phrasal
            question = plain(f"What must `{subject}` be {predicate} {preposition}?")
            relation = f"must_be_{predicate}_{preposition}"
            obj = _after_phrasal(text, predicate, preposition)
        else:
            question = plain(template.format(a=f"`{subject}`"))
    else:
        question = plain(template.format(a=f"`{subject}`"))
    return {
        "reasoning_type": "exact_lookup",
        "secondary_category": f"constraint_{fact['constraint_kind']}",
        "question": question,
        "answer": plain(text),
        "atomic_claims": [sentence(text)],
        "question_subject": f"`{subject}`",
        "question_relation": relation,
        "question_object": obj,
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
    relation = fact["lifecycle_kind"]
    obj = None
    # §15: evidence that names one place something does *not* work cannot answer "where
    # is it supported?". Ask the question the sentence answers — that was GOLD-B005-08.
    if fact["lifecycle_kind"] == "compatibility" and states_non_support(text):
        target = non_support_target(text)
        if target is None:
            return None
        question = plain(f"Is `{subject}` supported on {target}?")
        relation = "is_not_supported_on"
        obj = target
    else:
        question = plain(template.format(a=f"`{subject}`"))
    if DANGLING_REFERENCE.search(question):
        return None
    return {
        "reasoning_type": "lifecycle_compatibility_migration",
        "secondary_category": fact["lifecycle_kind"],
        "question": question,
        "answer": plain(text),
        "atomic_claims": [sentence(text)],
        "question_subject": f"`{subject}`",
        "question_relation": relation,
        "question_object": obj,
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


#: §9 and §10. One frame per predicate the corpus actually uses, each producing a
#: question out of the sentence's own subject plus a frame word. Nothing is paraphrased:
#: if the frame does not fit the sentence, no candidate is built.
#:
#: These exist because batches 001-005 spent everything the conditional and template
#: miners could reach. 698 distinct unspent spans remained in the snapshot and no
#: builder could turn any of them into a question — the shortage was in the authoring,
#: not in the corpus.
PREDICATE_FRAMES = (
    (r"\breturns\b", "What does {s} return?", "error_behavior", "returns"),
    (r"\braises\b", "What does {s} raise?", "error_behavior", "raises"),
    (r"\bthrows\b", "What does {s} throw?", "error_behavior", "throws"),
    (r"\brejects\b", "What does {s} reject?", "error_behavior", "rejects"),
    (r"\b(?:is|are)\s+rejected\b", "What happens to {s}?", "error_behavior",
     "is_rejected"),
    (r"\bstops?\s+with\b", "What does {s} stop with?", "error_behavior", "stops_with"),
    (r"\bfails?\s+with\b", "What does {s} fail with?", "error_behavior", "fails_with"),
    (r"\bemits\b", "What does {s} emit?", "error_behavior", "emits"),
    (r"\bdefaults\s+to\b", "What does {s} default to?", "exact_lookup", "defaults_to"),
    (r"\bcounts?\s+towards?\b", "What does {s} count towards?", "exact_lookup",
     "counts_towards"),
    (r"\b(?:is|are)\s+limited\s+to\b", "What is {s} limited to?", "exact_lookup",
     "is_limited_to"),
    (r"\b(?:may\s+not|cannot|must\s+not)\s+exceed\b",
     "What is the documented maximum for {s}?", "exact_lookup", "may_not_exceed"),
    (r"\bexpires\s+after\b", "How long does {s} last?", "exact_lookup",
     "expires_after"),
    (r"\baccepts\b", "What does {s} accept?", "exact_lookup", "accepts"),
    (r"\bmust\s+match\b", "What must {s} match?", "exact_lookup", "must_match"),
    (r"\btransitions\s+to\b", "What does {s} transition to?",
     "lifecycle_compatibility_migration", "transitions_to"),
    (r"\b(?:is|are)\s+deprecated\b", "What is the support status of {s}?",
     "lifecycle_compatibility_migration", "is_deprecated"),
    (r"\b(?:is|are)\s+not\s+supported\s+(?:on|in)\b",
     "Is {s} supported on {o}?", "lifecycle_compatibility_migration",
     "is_not_supported_on"),
    (r"\b(?:is|are)\s+ignored\b", "When is {s} ignored?", "configuration_interaction",
     "is_ignored"),
    (r"\bdisables\b", "What does {s} disable?", "configuration_interaction",
     "disables"),
    (r"\brequires\b", "What does {s} require?", "configuration_interaction",
     "requires"),
)
#: A subject the reader cannot resolve inside the span, or that is not a subject at all.
_PRONOUN_SUBJECT = re.compile(
    r"^(?:this|that|these|those|it|they|there|here|such|and|or|but|both|also|however|"
    r"the (?:following|above|previous|latter|former))\b", re.IGNORECASE)
#: Another finite verb before the frame verb means the frame verb is not the main one.
_SUBJECT_VERB = re.compile(
    r"\b(?:is|are|was|were|has|have|will|can|may|must|does|do|returns|raises|accepts|"
    r"sets|sends|uses|makes|gives|adds|allows|requires|stops|starts|becomes|contains|"
    r"includes|supports|emits|counts|applies|treats|reads|writes|calls|takes|runs|"
    r"executes|loops|records|resolves|matches|carries|means)\b", re.IGNORECASE)
_TRAILING_ADVERB = re.compile(
    r"\s+(?:always|never|only|still|then|also|automatically|currently|typically|"
    r"generally|normally|already|simply|just|therefore|instead)$", re.IGNORECASE)
_SUBJECT_ENDS_PREP = re.compile(
    r"\b(?:of|for|with|without|to|in|on|by|from|at|as|than)$", re.IGNORECASE)
#: The subject has to name something. A backticked identifier, a CamelCase or dotted
#: name, or a proper-noun phrase like "Claude Sonnet 5".
_SUBJECT_NAMES_SOMETHING = re.compile(
    r"`[^`]+`|\b(?:[A-Z][a-z0-9]+){2,}\b|\b[a-z][\w]*(?:\.[a-z][\w]*)+\b")
_PROPER_PHRASE = re.compile(r"\b[A-Z][A-Za-z0-9]+(?:\s+[A-Z0-9][A-Za-z0-9.]*)+")
#: "What does the response return?" is a question about nothing in particular.
_GENERIC_SUBJECT = re.compile(
    r"^(?:the\s+|a\s+|an\s+)?(?:api|response|responses|request|requests|default|"
    r"defaults|runner|user|users|client|server|model|models|system|application|"
    r"method|function|call|value|values|result|results|output|input|data|error|"
    r"errors|claude|field|fields|object|type|parameter|option|setting)$", re.IGNORECASE)
#: A bare value, not a thing that can be the subject of a rule.
_LITERAL_ONLY = re.compile(
    r"^(?:setting\s+)?`?(?:-?\d+(?:\.\d+)?|true|false|null|none|nil|\"[^\"]*\"|"
    r"[a-z]{1,8})`?$", re.IGNORECASE)
#: Frames that place the subject at the start of the question, where a leading article
#: must keep its capital. Everywhere else it lands mid-sentence and must not.
_SUBJECT_LEADS = re.compile(r"^\{s\}|^Is \{s\}")

SUBJECT_MAX_CHARS, SUBJECT_MAX_WORDS = 72, 10


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_BOUNDARY.split(" ".join(text.split()))
            if s.strip()]


def usable_subject(subject: str) -> bool:
    """Can a reader tell what this question is about, from the subject alone?"""
    if not subject or len(subject) > SUBJECT_MAX_CHARS:
        return False
    if len(subject.split()) > SUBJECT_MAX_WORDS:
        return False
    if re.search(r"[,:;()\[\]{}]", subject):
        return False
    if _PRONOUN_SUBJECT.match(subject) or _SUBJECT_VERB.search(subject):
        return False
    if _SUBJECT_ENDS_PREP.search(subject) or _GENERIC_SUBJECT.match(subject):
        return False
    if " and " in subject or " or " in subject:
        return False
    if _LITERAL_ONLY.match(subject.strip()):
        return False
    return bool(_SUBJECT_NAMES_SOMETHING.search(subject)
                or _PROPER_PHRASE.search(subject))


def build_predicate_fact(fact: dict) -> dict | None:
    """A plain statement of the form *subject predicate object*.

    The question is the sentence's own subject inside a frame chosen by its verb, so
    every word in it except the frame comes from the source. A sentence whose subject a
    reader could not resolve — a pronoun, a run-on clause, a generic noun — produces no
    candidate rather than a vague one.
    """
    critical = [c for c in (fact.get("critical_strings") or []) if c]
    for raw in _sentences(fact["evidence_text"]):
        line = raw if raw.endswith(".") else raw + "."
        if line.startswith(("-", "*", "#", ">", "|")):
            continue
        if critical and not any(contains_claim_string(line, c) for c in critical):
            continue
        for pattern, frame, reasoning, relation in PREDICATE_FRAMES:
            match = re.search(pattern, line, re.IGNORECASE)
            if not match or match.start() < 4:
                continue
            subject = _TRAILING_ADVERB.sub("", line[:match.start()].strip()).strip()
            obj = line[match.end():].strip(" .")
            if not usable_subject(subject) or len(obj) < 4:
                continue
            # "... requires `name` and `description` fields with specific validation
            # rules:" — a colon means the content is the list that follows, outside
            # this span. The claim would be incomplete.
            if obj.rstrip().endswith(":"):
                continue
            placed = subject
            if not _SUBJECT_LEADS.match(frame) and re.match(
                    r"^(?:The|A|An|Each|Every|Both|Any)\s", placed):
                placed = placed[0].lower() + placed[1:]
            target = non_support_target(line) if "{o}" in frame else None
            if "{o}" in frame and not target:
                continue
            question = plain(frame.format(s=placed, o=target)
                             if target else frame.format(s=placed))
            if DANGLING_REFERENCE.search(question) or _BARE_THIS.search(question):
                continue
            answer = plain(line)
            return {
                "reasoning_type": reasoning,
                "secondary_category": relation,
                "question": question,
                "answer": answer,
                "atomic_claims": [sentence(line)],
                "question_subject": subject,
                "question_relation": relation,
                "question_object": obj,
            }
    return None
