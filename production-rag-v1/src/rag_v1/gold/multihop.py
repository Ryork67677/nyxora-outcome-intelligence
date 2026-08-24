"""Genuine multi-hop: a bridge between two facts, not two facts side by side.

Batch 003 produced four candidates labelled ``multi_hop`` that were nothing of the kind.
Each drew on two spans, so the label looked earned, but the answer was the two spans'
contents — a reader who found either span learned one of the two facts and nothing
followed from combining them. That is a multi-span *retrieval* test.

A case is multi-hop when the answer exists in neither span. Span 1 establishes something
about a bridge entity; span 2 says what follows from that; the answer is the composition,
and a reader holding only one span cannot produce it.

The check here is mechanical, and it is deliberately hostile to its own output:

* the bridge entity must appear in **both** spans — that is what makes it a bridge;
* hop 1's evidence must be in span 1 and **not** wholly in span 2;
* hop 2's evidence must be in span 2 and **not** wholly in span 1;
* the composed answer must need content from both.

A pair failing any of these is recorded as a rejected multi-hop with its reason, because
how often the miner *tried* and failed is the number that says whether the corpus
supports this at all.
"""

from __future__ import annotations

import re
from collections import Counter

from rag_v1.gold.bridge_equivalence import same_semantic_entity
from rag_v1.gold.normalisation import contains_claim_string

PASS = "PASS"
FAIL = "FAIL"

#: A sentence that constrains, requires or scopes something — the first hop.
CONDITION_PATTERNS = (
    re.compile(r"\b(?:is |are )?(?:only )?(?:supported|available|permitted|allowed)\b"),
    re.compile(r"\brequires?\b"),
    re.compile(r"\bmust (?:be|use|match|start|contain|form)\b"),
    re.compile(r"\bis (?:deprecated|no longer supported|removed|retired)\b"),
    re.compile(r"\bonly (?:when|if|for|on)\b"),
    re.compile(r"\bapplies (?:only )?(?:to|when)\b"),
    re.compile(r"\btakes precedence over\b"),
    re.compile(r"\bdefaults? to\b"),
)
#: A sentence that states what then happens — the second hop.
CONSEQUENCE_PATTERNS = (
    re.compile(r"\breturns? (?:a |an )?\d{3}\b"),
    re.compile(r"\breturns? (?:a |an )?`?[A-Za-z_]"),
    re.compile(r"\braises?\b"),
    re.compile(r"\b(?:is|are) (?:rejected|ignored|dropped|discarded|skipped)\b"),
    re.compile(r"\bstops?\b|\bhalts?\b|\bterminates?\b"),
    re.compile(r"\b(?:disables?|enables?|overrides?|changes?|affects?)\b"),
    re.compile(r"\berror\b"),
    re.compile(r"\bfails?\b"),
)


def _matches(patterns, text: str) -> bool:
    lowered = text.lower()
    return any(p.search(lowered) for p in patterns)


def is_condition(text: str) -> bool:
    return _matches(CONDITION_PATTERNS, text)


def is_consequence(text: str) -> bool:
    return _matches(CONSEQUENCE_PATTERNS, text)


def composition_check(bridge: str, span_1: str, span_2: str,
                      hop_1_strings: list[str], hop_2_strings: list[str]) -> dict:
    """Decide whether two spans genuinely compose, and say why when they do not."""
    reasons: list[str] = []

    in_1 = contains_claim_string(span_1, bridge)
    in_2 = contains_claim_string(span_2, bridge)
    if not (in_1 and in_2):
        reasons.append(
            f"the bridge entity {bridge!r} is not in both spans "
            f"(span 1: {in_1}, span 2: {in_2}); without a shared entity there is no hop")

    hop_1_here = [s for s in hop_1_strings if contains_claim_string(span_1, s)]
    hop_2_there = [s for s in hop_2_strings if contains_claim_string(span_2, s)]
    if len(hop_1_here) != len(hop_1_strings):
        missing = [s for s in hop_1_strings if s not in hop_1_here]
        reasons.append(f"hop 1 asserts {missing}, which span 1 does not contain")
    if len(hop_2_there) != len(hop_2_strings):
        missing = [s for s in hop_2_strings if s not in hop_2_there]
        reasons.append(f"hop 2 asserts {missing}, which span 2 does not contain")

    # The heart of it: if either span already carries the whole answer, a reader needs
    # only that span, and the case is a lookup wearing a multi-hop label.
    if hop_2_strings and all(contains_claim_string(span_1, s) for s in hop_2_strings):
        reasons.append("span 1 alone already answers the whole question — not multi-hop")
    if hop_1_strings and all(contains_claim_string(span_2, s) for s in hop_1_strings):
        reasons.append("span 2 alone already answers the whole question — not multi-hop")

    return {
        "multi_hop_composition_check": FAIL if reasons else PASS,
        "reasons": reasons,
        "why_span_1_alone_is_insufficient": (
            f"Span 1 establishes the condition on {bridge}, but does not state "
            f"{hop_2_strings[0] if hop_2_strings else 'the consequence'}."),
        "why_span_2_alone_is_insufficient": (
            f"Span 2 states what follows, but does not establish that it applies to "
            f"{bridge}."),
    }


#: An entity has to look like a specific API symbol for a hop through it to mean
#: anything. The first batch-004 attempt bridged on ``False``, ``refusal`` and
#: ``error``: two sentences that both mention ``False`` are not two halves of an
#: argument, they are two sentences that both mention ``False``.
_SYMBOL = re.compile(r"^[A-Za-z_][\w.]{3,}$")
_NOT_A_BRIDGE = frozenset({
    "true", "false", "none", "null", "nil", "nan", "undefined", "yes", "no",
    "string", "number", "boolean", "integer", "array", "object", "float",
    "error", "errors", "refusal", "request", "response", "result", "results",
    "input", "output", "value", "values", "default", "message", "messages",
    "content", "text", "json", "http", "https", "python", "typescript", "javascript",
})
#: How far into a span the entity may sit and still be what the sentence is *about*.
SUBJECT_WINDOW = 120
#: How many candidate facts one entity may contribute before the search stops looking
#: at it. This is a cost bound, not a quality rule: an early attempt rejected any entity
#: documented in more than three files, which threw away ``max_tokens`` and
#: ``tool_result`` — specific API symbols that happen to be documented in many places,
#: and the only entities in this corpus that actually produced a passing hop.
MAX_FACTS_PER_ENTITY = 80


#: A consequence span earns its place by making its outcome *conditional*. Without a
#: conditional the sentence is a second description of the same thing, and the pair is
#: two lookups about one identifier rather than a chain.
_CONDITIONAL = re.compile(
    r"\b(?:if|when|unless|whenever|whose|once|otherwise|provided that|as long as)\b",
    re.IGNORECASE)
#: "The supported keys are `a`, `b`, and `c`." — membership in a list is not a
#: requirement about any one member, so it cannot be the first half of a hop.
_LIST_MEMBERSHIP = re.compile(
    r"^\s*(?:the\s+)?(?:supported|valid|allowed|available|possible|accepted)\s+\w+\s+"
    r"(?:are|include)\b", re.IGNORECASE)
_TICKED = re.compile(r"`[^`]+`")


def is_list_membership(text: str) -> bool:
    """Does this span merely enumerate values rather than constrain one?"""
    if _LIST_MEMBERSHIP.match(text):
        return True
    return len(_TICKED.findall(text)) >= 3 and ", " in text


#: How far past a conditional marker its clause is taken to run when no punctuation
#: closes it sooner.
CLAUSE_WINDOW = 70


def states_dependency(text: str, entity: str) -> bool:
    """Does this span make an outcome conditional on **the entity's own state**?

    Requiring only that a conditional appear somewhere in the span was not enough. Three
    of the four pairs that survived every other check failed here:

    * "If you run at ``xhigh`` or ``max`` effort, raise ``max_tokens`` to at least 64k" —
      the condition tests the effort level, and ``max_tokens`` is merely the thing being
      adjusted in the outcome;
    * "When Claude calls your custom search tool, return a standard ``tool_result``" —
      the condition tests who is calling;
    * "...causes the request to fail with a ``400 invalid_request_error`` whose message
      contains ``Circular $ref detected``" — the ``whose`` governs the error message.

    In each the entity appears, a conditional appears, and they have nothing to do with
    each other, so span 1 establishes nothing the condition needs. The entity has to sit
    inside the conditional clause for the pair to be a chain rather than a coincidence.
    """
    lowered = entity.lower()
    for marker in _CONDITIONAL.finditer(text):
        start = marker.end()
        clause = text[start:start + CLAUSE_WINDOW]
        cut = min((clause.find(c) for c in ",;:" if clause.find(c) >= 0), default=-1)
        if cut >= 0:
            clause = clause[:cut]
        if lowered in clause.lower():
            return True
    return False


def self_contained(text: str) -> bool:
    """A sentence that carries both its condition and its outcome answers alone.

    Two of these paired together is the batch-003 failure exactly: each span is already
    a complete case, so the "hop" adds nothing a reader could not get from either half.
    """
    return is_condition(text) and is_consequence(text)


def plausible_bridge(entity: str) -> bool:
    """Is this a specific enough symbol to carry a dependency?"""
    lowered = entity.lower()
    if lowered in _NOT_A_BRIDGE or not _SYMBOL.match(entity):
        return False
    # A lone lowercase English-looking word is usually vocabulary. A symbol earns its
    # place by looking like one: snake_case, dotted, or camelCase.
    return "_" in entity or "." in entity or any(c.isupper() for c in entity[1:])


def about(span: str, entity: str) -> bool:
    """Is the span *about* the entity, rather than merely mentioning it in passing?"""
    lowered, needle = span.lower(), entity.lower()
    position = lowered.find(needle)
    return 0 <= position <= SUBJECT_WINDOW


def find_bridges(candidates: list[dict], limit: int = 12) -> tuple[list[dict], list[dict]]:
    """Pair a condition fact with a consequence fact that shares a bridge entity.

    Returns (pairs, rejected). Rejections are returned rather than dropped: batch 003's
    lesson is that the number of *attempted* multi-hop cases that fail the composition
    check is itself a benchmark-quality signal.
    """
    by_entity: dict[str, list[dict]] = {}
    for candidate in candidates:
        for entity in set(re.findall(r"`([^`]{3,60})`", candidate["evidence_text"])):
            entity = entity.strip().strip("`\"'")
            if not plausible_bridge(entity):
                continue
            by_entity.setdefault(entity, []).append(candidate)

    pairs: list[dict] = []
    rejected: list[dict] = []
    used: set[str] = set()

    for entity, group in sorted(by_entity.items()):
        if len(pairs) >= limit or len(group) < 2:
            continue
        group = group[:MAX_FACTS_PER_ENTITY]
        conditions = [c for c in group
                      if is_condition(c["evidence_text"])
                      and about(c["evidence_text"], entity)]
        consequences = [c for c in group
                        if is_consequence(c["evidence_text"])
                        and about(c["evidence_text"], entity)]
        for first in conditions:
            for second in consequences:
                if first["evidence_hash"] == second["evidence_hash"]:
                    continue
                if {first["evidence_hash"], second["evidence_hash"]} & used:
                    continue
                # Structural rejections, before the composition check. A hop across
                # providers is not a dependency: OpenAI's docs do not state
                # consequences for Anthropic's settings, and cross-provider material
                # belongs in a comparison case rather than a requirement chain.
                reason = None
                if first["provider"] != second["provider"]:
                    reason = ("the spans are two unrelated lookups: they sit in "
                              "different providers' documentation and neither "
                              "constrains the other")
                elif is_list_membership(first["evidence_text"]):
                    reason = ("span 1 enumerates values rather than stating a "
                              "requirement about the bridge entity — no bridge "
                              "relationship")
                elif not states_dependency(second["evidence_text"], entity):
                    reason = ("span 2 states no condition on the bridge entity: the two "
                              "spans are unrelated lookups that share an identifier")
                elif (self_contained(first["evidence_text"])
                      and self_contained(second["evidence_text"])):
                    reason = ("both spans are self-contained condition-and-outcome "
                              "statements: two parallel lookups, not one chain")
                if reason is not None:
                    rejected.append({
                        "bridge_entity": entity,
                        "candidates": [first["evidence_hash"][:8],
                                       second["evidence_hash"][:8]],
                        "reasons": [reason],
                    })
                    continue
                hop_1 = first["critical_strings"]
                hop_2 = second["critical_strings"]
                verdict = composition_check(entity, first["evidence_text"],
                                            second["evidence_text"], hop_1, hop_2)
                record = {
                    "bridge_entity": entity,
                    "first": first, "second": second,
                    **verdict,
                }
                if verdict["multi_hop_composition_check"] == FAIL:
                    rejected.append({
                        "bridge_entity": entity,
                        "candidates": [first["candidate_id"] or first["evidence_hash"][:8],
                                       second["candidate_id"] or second["evidence_hash"][:8]],
                        "reasons": verdict["reasons"],
                    })
                    continue
                used.update({first["evidence_hash"], second["evidence_hash"]})
                pairs.append(record)
                break
            if len(pairs) >= limit:
                break
    return pairs, rejected


__all__ = [
    "CONDITION_PATTERNS", "CONSEQUENCE_PATTERNS", "FAIL", "PASS", "composition_check",
    "find_bridges", "is_condition", "is_consequence",
]


#: §15's dependency vocabulary. A chain starts from a sentence that *states a
#: dependency*, not from two sentences that happen to share an identifier — batch 004
#: searched 559 shared-identifier pairs for one chain, and the yield is the reason this
#: search runs the other way round.
DEPENDENCY_MARKERS = (
    re.compile(r"\brequires?\b"), re.compile(r"\bonly if\b"),
    re.compile(r"\bif\b.*\bthen\b"), re.compile(r"\btakes precedence\b"),
    re.compile(r"\bmust\b"), re.compile(r"\bunsupported when\b"),
    re.compile(r"\bdepends on\b"), re.compile(r"\bavailable only\b"),
    re.compile(r"\bapplies (?:only )?when\b"), re.compile(r"\bresults? in\b"),
    re.compile(r"\bcauses?\b"), re.compile(r"\bfalls? back to\b"),
    re.compile(r"\bset\b.*\bto\b"), re.compile(r"\bis (?:deprecated|required)\b"),
    re.compile(r"\bwhen\b.*\bis (?:present|set|omitted|enabled|disabled)\b"),
)
#: Span 1 has to *put the entity in a state*, not merely mention it. §16: span 1
#: establishes fact/state A, span 2 establishes the rule A → B.
_STATE_ASSIGNMENT = (
    r"set\s+`?{e}`?\s+to", r"`?{e}`?\s+(?:is|are|must be|defaults? to)\s",
    r"(?:pass|provide|include|add|adding|specify|use|using)\s+`?{e}`?",
    r"`?{e}`?\s+requires?\s", r"`?{e}`?\s+(?:is|are)\s+(?:deprecated|required|optional)",
    r"with\s+`?{e}`?\s+(?:set|enabled|present)",
)
#: §18: a deterministic ceiling on the search, so a low-yield lane cannot eat the batch.
DEPENDENCY_PAIR_BUDGET = 1000


def is_dependency_statement(text: str) -> bool:
    """Does this sentence state a dependency at all?"""
    lowered = text.lower()
    return any(marker.search(lowered) for marker in DEPENDENCY_MARKERS)


def state_implication(entity: str, span_1: str) -> dict:
    """Does span 1 put the bridge entity into a state span 2 could test?

    A span that merely mentions the entity establishes nothing for the second hop to
    consume. This looks for the entity being set, required, passed, or declared to be
    something — the "fact/state A" half of §16's definition.
    """
    escaped = re.escape(entity)
    for pattern in _STATE_ASSIGNMENT:
        match = re.search(pattern.format(e=escaped), span_1, re.IGNORECASE)
        if match:
            return {"state_established": True, "state_evidence": match.group(0).strip()}
    return {
        "state_established": False,
        "state_evidence": None,
        "reason": (f"span 1 mentions `{entity}` without putting it in a state — nothing "
                   "for span 2's condition to be true of"),
    }


def find_dependency_chains(facts: list[dict], limit: int = 8,
                           budget: int = DEPENDENCY_PAIR_BUDGET) -> tuple[list, dict]:
    """Dependency-first multi-hop search, with a funnel report.

    The order is the point. Batch 004 took every pair of facts sharing a plausible
    identifier and asked whether it composed; 558 of 559 did not. Here a pair is only
    considered when span 1 already states a dependency and puts the entity in a state,
    and span 2 makes an outcome conditional on that entity. The funnel counts what each
    gate removed, so the next batch can see which gate is doing the work.
    """
    by_entity: dict[str, list[dict]] = {}
    for fact in facts:
        for raw in set(re.findall(r"`([^`]{3,60})`", fact["evidence_text"])):
            entity = raw.strip().strip("`\"'")
            if plausible_bridge(entity):
                by_entity.setdefault(entity, []).append(fact)

    funnel = Counter()
    pairs: list[dict] = []
    rejected: list[dict] = []
    used: set[str] = set()

    for entity, group in sorted(by_entity.items()):
        if len(pairs) >= limit or funnel["dependency_pairs_considered"] >= budget:
            break
        group = group[:MAX_FACTS_PER_ENTITY]
        # Lane B starts here: only spans that state a dependency and put the entity in
        # a state may open a chain.
        openers = [f for f in group
                   if is_dependency_statement(f["evidence_text"])
                   and about(f["evidence_text"], entity)
                   and state_implication(entity, f["evidence_text"])["state_established"]]
        consumers = [f for f in group
                     if is_consequence(f["evidence_text"])
                     and states_dependency(f["evidence_text"], entity)]
        if not openers or not consumers:
            continue

        for first in openers:
            for second in consumers:
                if funnel["dependency_pairs_considered"] >= budget:
                    break
                if first["evidence_hash"] == second["evidence_hash"]:
                    continue
                if {first["evidence_hash"], second["evidence_hash"]} & used:
                    continue
                funnel["dependency_pairs_considered"] += 1

                equivalence = same_semantic_entity(entity, first, second)
                if not equivalence["same_semantic_entity"]:
                    funnel["failed_semantic_equivalence"] += 1
                    rejected.append({"bridge_entity": entity, "gate": "semantic_equivalence",
                                     "reason": equivalence["bridge_equivalence_reason"]})
                    continue
                if is_list_membership(first["evidence_text"]):
                    funnel["failed_state_implication"] += 1
                    rejected.append({"bridge_entity": entity, "gate": "state_implication",
                                     "reason": "span 1 enumerates values rather than "
                                               "putting the entity in a state"})
                    continue
                if (self_contained(first["evidence_text"])
                        and self_contained(second["evidence_text"])):
                    funnel["failed_span_independence"] += 1
                    rejected.append({"bridge_entity": entity, "gate": "span_independence",
                                     "reason": "both spans carry their own condition and "
                                               "outcome: two parallel lookups"})
                    continue
                verdict = composition_check(
                    entity, first["evidence_text"], second["evidence_text"],
                    first["critical_strings"], second["critical_strings"])
                if verdict["multi_hop_composition_check"] != PASS:
                    funnel["failed_span_independence"] += 1
                    rejected.append({"bridge_entity": entity, "gate": "span_independence",
                                     "reason": "; ".join(verdict["reasons"])})
                    continue

                state = state_implication(entity, first["evidence_text"])
                funnel["passed"] += 1
                used |= {first["evidence_hash"], second["evidence_hash"]}
                pairs.append({
                    "bridge_entity": entity, "first": first, "second": second,
                    **verdict, **equivalence, **state,
                })
                break
            else:
                continue
            break

    return pairs, {"funnel": dict(funnel), "budget": budget,
                   "rejected": rejected,
                   "entities_with_a_dependency_opener": sum(
                       1 for entity, group in by_entity.items()
                       if any(is_dependency_statement(f["evidence_text"]) for f in group))}
