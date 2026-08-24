#!/usr/bin/env python3
"""GOLD-001: generate batch 004 — genuine multi-hop, ambiguity, and OpenAI coverage.

Batch 003 closed with zero genuine multi-hop cases. It had four labelled that way, and
the label was wrong: each drew on two spans, but the answer was the two spans' contents
rather than something that followed from combining them. Batch 004 exists to produce the
real thing, and to be honest about how often the corpus does not support it.

Three miners feed this batch:

* **bridge composition** — a condition fact and a consequence fact sharing an entity,
  put through a composition check that fails a pair whenever either span already
  answers the whole question. Failures are counted and reported, because how often the
  attempt fails is the measurement that matters here;
* **ambiguity** — a field name the corpus defines twice under different parent types,
  with genuinely different meanings. The question names the scope, since a question that
  withholds the scope needed to answer it is a trick rather than a test;
* **the batch-003 sentence patterns** for configuration interaction, error behaviour and
  lifecycle.

Every batch-001/002/003 protection still applies and is enforced rather than assumed.
Retrieval is never run, and no candidate is chosen, ordered or worded because of what any
system does with it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import UTC, datetime
from itertools import zip_longest
from pathlib import Path

from rag_v1.db import connect
from rag_v1.gold.ambiguity import find_ambiguous_fields
from rag_v1.gold.factmining import mine_bridge_facts
from rag_v1.gold.mining import _context, _section_for, anaphora_problem
from rag_v1.gold.mining_v3 import (
    EVIDENCE_HARD_CAP,
    EVIDENCE_SOFT_CAP,
    mine_definition_bullets,
    mine_prose,
    mine_row_facts,
)
from rag_v1.gold.multihop import PASS, find_bridges
from rag_v1.gold.normalisation import contains_claim_string
from rag_v1.parsing import _sections_from_markdown

SCHEMA_VERSION = "1.2"
SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"
PRIOR = (
    "evals/review/gold_review_batch_001.json",
    "evals/review/gold_review_batch_002.json",
    "evals/review/gold_review_batch_003.json",
)
DEVELOPMENT = "evals/development/v1.jsonl"
#: Historical failures that shaped the architecture. Retesting them would measure the
#: design against its own training, so their spans are excluded outright.
EXCLUDED_FAILURE_CASES = ("AN-001", "AN-003", "AN-012", "OA-004")

REASONING_TARGET = {
    "genuine_multi_hop": (6, 8),
    "configuration_interaction": (4, 5),
    "ambiguity_disambiguation": (3, 4),
    "error_behavior": (2, 3),
    "lifecycle_compatibility_migration": (2, 3),
    "exact_lookup": (0, 3),
}
PROVIDER_TARGET = {"openai": (10, 12), "anthropic": (8, 10)}
#: Reasoning types the miner's own categories map onto.
CATEGORY_TO_REASONING = {
    "exact_constraint": "exact_lookup",
    "error_behavior": "error_behavior",
    "configuration_interaction": "configuration_interaction",
    "lifecycle": "lifecycle_compatibility_migration",
}


def load_docs(cur) -> list[dict]:
    cur.execute(
        """
        SELECT v.version_id, v.normalized_text, s.provider, s.title, s.canonical_url,
               v.captured_at
        FROM document_version v
        JOIN document_source s ON s.source_id = v.source_id
        JOIN corpus_snapshot_version sv ON sv.version_id = v.version_id
        WHERE sv.snapshot_id = %s
        ORDER BY v.version_id
        """,
        (SNAPSHOT,),
    )
    return [{"version_id": r[0], "text": r[1], "provider": r[2], "title": r[3],
             "url": r[4], "captured_at": r[5]} for r in cur.fetchall()]


def normalise_question(question: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", question.lower()).split())


def prior_material() -> tuple[set[str], set[tuple], set[tuple]]:
    """Questions and spans already spent, plus the architecture-shaping failure spans."""
    questions: set[str] = set()
    spans: set[tuple] = set()
    excluded: set[tuple] = set()
    for path in PRIOR:
        for record in json.loads(Path(path).read_text())["records"]:
            questions.add(normalise_question(record["proposed_question"]))
            for span in (record.get("expected_evidence") or [record]):
                spans.add((span["version_id"], span["char_start"], span["char_end"]))
            for revision in record.get("anchor_revisions", []):
                for key in ("old_spans", "new_spans"):
                    for span in revision.get(key, []):
                        spans.add((record["version_id"], span["char_start"],
                                   span["char_end"]))
    development = Path(DEVELOPMENT)
    if development.exists():
        for line in development.read_text().splitlines():
            if not line.strip():
                continue
            case = json.loads(line)
            questions.add(normalise_question(case["question"]))
            for ref in case.get("expected_evidence", []):
                key = (ref.get("version_id"), ref.get("char_start"), ref.get("char_end"))
                spans.add(key)
                if case["case_id"] in EXCLUDED_FAILURE_CASES:
                    excluded.add(key)
    return questions, spans, excluded


def evidence_record(index: int, doc: dict, start: int, end: int,
                    critical: list[str]) -> dict:
    body = doc["text"][start:end]
    return {
        "evidence_id": f"E{index}",
        "version_id": doc["version_id"],
        "section_path": _section_for(doc["sections"], start),
        "char_start": start, "char_end": end,
        "evidence_text": body,
        "evidence_hash": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "evidence_char_length": end - start,
        "critical_strings": critical,
    }


def map_claims(claims: list[str], spans: list[dict]) -> list[dict]:
    """Say which span is supposed to support which claim.

    §19: for a multi-hop case the critical strings belong to their own span, and a
    reviewer must not be asked to find every string in every span. Recording the
    mapping is what makes that checkable rather than assumed.
    """
    out = []
    for index, claim in enumerate(claims):
        if len(claims) == len(spans):
            span = spans[index]
        else:
            span = next(
                (s for s in spans
                 if any(contains_claim_string(claim, t) for t in s["critical_strings"])),
                spans[0])
        out.append({"claim": claim, "evidence_id": span["evidence_id"],
                    "critical_strings": span["critical_strings"]})
    return out


def base_record(doc: dict, spans: list[dict], reasoning: str, question: str,
                answer: str, claims: list[str], confidence: str) -> dict:
    shape = "single_span" if len(spans) == 1 else "multi_span"
    first, last = spans[0], spans[-1]
    return {
        "candidate_id": "",
        "provider": doc["provider"],
        "document_title": doc["title"],
        "version_id": doc["version_id"],
        "source_url": doc.get("url"),
        "captured_at": str(doc.get("captured_at")),
        "reasoning_type": reasoning,
        "secondary_category": None,
        "evidence_shape": shape,
        "requires_all_evidence": shape != "single_span",
        "question": question,
        "answer": answer,
        "atomic_claims": claims,
        # §28 names the short forms; §18 names ``proposed_*``, which is also what the
        # batch-001..003 pipeline keys on (verification import, QC packet, decisions,
        # closure). Ship both rather than fork the tooling for one batch.
        "proposed_question": question,
        "proposed_answer": answer,
        "proposed_atomic_claims": claims,
        "expected_evidence": spans,
        "claim_evidence_map": map_claims(claims, spans),
        "section_path": spans[0]["section_path"],
        "critical_strings": [s for span in spans for s in span["critical_strings"]],
        "evidence_char_length": sum(s["evidence_char_length"] for s in spans),
        "context_before": _context(doc["text"], first["char_start"],
                                   first["char_end"])[0],
        "context_after": _context(doc["text"], last["char_start"], last["char_end"])[1],
        "candidate_type": "supported",
        "generator_confidence": confidence,
        "needs_human_interpretation": reasoning == "genuine_multi_hop",
        "verification_status": "candidate_unverified",
        "claude_proposed": True,
        "chatgpt_verified": None,
        "retrieval_was_not_run": True,
        "schema_version": SCHEMA_VERSION,
        "precheck_holdout_ready": False,
        "precheck_failures": [],
        "revisions": [],
    }


#: A backticked token that reads as a value rather than as the thing being configured.
_VALUE_LIKE = re.compile(r"^(?:True|False|None|null|\"[^\"]+\"|'[^']+'|-?\d[\w.]*|"
                         r"[A-Za-z_][\w.-]{0,30})$")


def compose_question(bridge: str, condition_text: str) -> str:
    """Write the hop's question from what span 1 actually says.

    §24: it has to sound like a developer asking, and it must not reveal that two spans
    are involved — "According to evidence span 1 and span 2" is a question about the
    benchmark rather than about the API.
    """
    for value in re.findall(r"`([^`]{1,30})`", condition_text):
        if value != bridge and _VALUE_LIKE.match(value) and value.lower() != bridge.lower():
            return f"If I set `{bridge}` to `{value}`, what happens?"
    return f"If I use `{bridge}` as the documentation describes, what happens as a result?"


def build_multi_hop(pair: dict, docs_by_version: dict) -> dict | None:
    first, second = pair["first"], pair["second"]
    bridge = pair["bridge_entity"]
    doc = docs_by_version[first["version_id"]]
    other = docs_by_version[second["version_id"]]

    spans = [
        evidence_record(1, doc, first["char_start"], first["char_end"],
                        first["critical_strings"]),
        evidence_record(2, other, second["char_start"], second["char_end"],
                        second["critical_strings"]),
    ]
    hop_1 = first["proposed_atomic_claims"][0]
    hop_2 = second["proposed_atomic_claims"][0]
    # The claims are the source's own sentences, so the composition joins them rather
    # than paraphrasing: a reworded claim is where batch 001 drifted from its evidence.
    composed = f"For `{bridge}`: {hop_1.rstrip('.')}. Consequently, {hop_2}"
    question = compose_question(bridge, first["evidence_text"])
    answer = f"{first['proposed_answer']} {second['proposed_answer']}"

    record = base_record(doc, spans, "genuine_multi_hop", question, answer,
                         [hop_1, hop_2], "medium")
    if first["version_id"] != second["version_id"]:
        record["evidence_shape"] = "multi_document"
        record["document_count"] = 2
    else:
        record["document_count"] = 1
    record.update({
        "bridge_entity": bridge,
        "bridge_relationship": ("span 1 states a requirement or constraint on the bridge "
                                "entity; span 2 states the behaviour that follows"),
        "hop_1_claim": hop_1,
        "hop_2_claim": hop_2,
        "composed_claim": composed,
        # §6 calls it composed_answer, §28 composed_claim. Same string, both keys.
        "composed_answer": composed,
        "why_span_1_alone_is_insufficient": pair["why_span_1_alone_is_insufficient"],
        "why_span_2_alone_is_insufficient": pair["why_span_2_alone_is_insufficient"],
        "multi_hop_composition_check": pair["multi_hop_composition_check"],
        "section_count": len({tuple(s["section_path"]) for s in spans}),
    })
    return record


def _sentence(text: str) -> str:
    """Close a description that the source left unpunctuated, so two of them can join."""
    text = text.strip()
    return text if text.endswith((".", "!", "?")) else text + "."


def build_ambiguity(doc: dict, finding: dict) -> dict | None:
    readings = finding["candidate_interpretations"]
    if len(readings) < 2:
        return None
    chosen, other = readings[0], readings[1]
    term = finding["ambiguous_term"]
    spans = [evidence_record(i, doc, r["char_start"], r["char_end"],
                             [term, r["meaning"][:60]])
             for i, r in enumerate((chosen, other), start=1)]
    question = (f"In a `{chosen['scope']}`, what does the `{term}` field contain, and "
                f"how does that differ from `{other['scope']}`?")
    # A colon rather than "is": the meanings are the source's own sentences, capital
    # letter and all, and "it is The partially parsed arguments object" reads as a
    # transcription error rather than as an answer.
    claims = [f"In `{reading['scope']}`, `{term}` is: {_sentence(reading['meaning'])}"
              for reading in (chosen, other)]
    answer = " ".join(claims)
    record = base_record(doc, spans, "ambiguity_disambiguation", question, answer,
                         claims, "medium")
    record.update({
        "ambiguous_term": term,
        "candidate_interpretations": [
            {"scope": r["scope"], "meaning": r["meaning"]} for r in readings],
        "required_scope_to_answer": finding["required_scope_to_answer"],
        "needs_human_interpretation": True,
    })
    return record


#: "If <clause>, <result>." — the sentence carries its own condition and its own
#: outcome, which is exactly the shape §14 asks for: both halves matter, and the exact
#: evidence contains every required condition.
_CONDITIONAL_OPENER = re.compile(r"^(?P<marker>If|When|Unless)\s+(?P<rest>.+)$")
#: A result that opens on one of these is a continuation of the condition, not the
#: outcome: splitting there produces "Reordered, filtered out, ..., the request returns
#: a 400" as the answer, which is not a sentence.
_NOT_A_RESULT_OPENER = frozenset({
    "which", "that", "where", "and", "or", "but", "so", "while", "whereas", "though",
    "although", "including", "unless", "then",
})
#: Words that make an outcome an *error* rather than a configuration effect.
_ERROR_WORDS = re.compile(
    r"\b(?:error|fails?|failure|rejected?|raises?|exception|invalid|4\d\d|5\d\d|"
    r"refus\w+|abort\w*|denied)\b", re.IGNORECASE)
#: §13's vocabulary. A conditional whose outcome is about support state is a lifecycle
#: case, and calling it a configuration interaction would hide it.
_LIFECYCLE_WORDS = re.compile(
    r"\b(?:deprecated|no longer supported|removed|retired|superseded|migrat\w+|"
    r"end[- ]of[- ]life|sunset\w*)\b", re.IGNORECASE)
#: A demonstrative determiner in the *question* — "if you exceed these limits" — names
#: nothing: the limits are in a table above the span, so the question cannot be answered
#: from its own evidence.
_DANGLING_REFERENCE = re.compile(r"\b(?:these|those|such)\s+(?!as\b)[a-z]{3,}",
                                 re.IGNORECASE)
_SENTENCE_BOUNDARY = re.compile(r"(?<![A-Z])\.\s+(?=[A-Z`])")
_MD_LINK = re.compile(r"\[([^\]]+)\]\((?:[^)]+)\)|\[([^\]]+)\]\[(?:[^\]]+)\]")


def plain(text: str) -> str:
    """Drop markdown link plumbing from prose meant to be read as a question.

    A question carrying a raw URL is not a question a developer would type (§24). This
    touches the question and the answer only: the evidence, the claims and the hashes
    keep the source's exact bytes, so nothing being checked is being rewritten.
    """
    return " ".join(_MD_LINK.sub(lambda m: m.group(1) or m.group(2), text).split())


def split_conditional(text: str) -> tuple[str, str, str] | None:
    """Split "If X, Y." into its condition and its outcome at the right comma.

    Splitting at the first comma broke every sentence whose condition contains a list:
    "If the message contains `thinking` blocks that were edited, reordered, filtered
    out, or reconstructed, the request returns 400" became the answer "Reordered,
    filtered out, ..., the request returns 400". The outcome starts at the *last* comma
    that leaves a well-formed result behind.
    """
    opener = _CONDITIONAL_OPENER.match(text)
    if opener is None:
        return None
    marker, rest = opener.group("marker"), opener.group("rest")
    best = None
    for match in re.finditer(r",\s+", rest):
        clause, result = rest[:match.start()].strip(), rest[match.end():].strip()
        if not (12 <= len(clause) <= 180 and 12 <= len(result) <= 240):
            continue
        if result.split()[0].lower().strip(",") in _NOT_A_RESULT_OPENER:
            continue
        # One sentence each side. A span can hold two sentences once the anaphora
        # resolver extends it backwards, and splitting across the boundary produced
        # "What happens if you don't need to process text as it arrives, the SDKs
        # provide a way to use streaming internally...?" — a question that swallowed
        # its own answer.
        if _SENTENCE_BOUNDARY.search(clause) or _SENTENCE_BOUNDARY.search(result):
            continue
        best = (marker, clause, result)
    return best


def build_conditional(fact: dict, doc: dict) -> dict | None:
    """A single-span case from a sentence that states its own condition and outcome.

    §10 and §14 both ask for reasoning where the condition and the result matter
    together, and the corpus states plenty of it in one sentence. Nothing is composed
    here and nothing is inferred: the question repeats the source's own condition, and
    the answer is the source's own outcome.
    """
    text = " ".join(fact["evidence_text"].split())
    split = split_conditional(text)
    if split is None:
        return None
    marker, clause, result = split
    if not result.endswith("."):
        return None
    if clause.lower().startswith(("true", "so", "not", "any of")):
        # "If true, ..." is the batch-001 defect: the condition names nothing.
        return None
    question = plain(f"What happens {marker.lower()} {clause}?")
    if _DANGLING_REFERENCE.search(question):
        return None
    answer = plain(result)
    answer = answer[0].upper() + answer[1:]
    reasoning = ("lifecycle_compatibility_migration" if _LIFECYCLE_WORDS.search(result)
                 else "error_behavior" if _ERROR_WORDS.search(result)
                 else "configuration_interaction")
    spans = [evidence_record(1, doc, fact["char_start"], fact["char_end"],
                             fact["critical_strings"])]
    record = base_record(doc, spans, reasoning, question, answer, [text],
                         fact["generator_confidence"])
    record["secondary_category"] = "conditional_behavior"
    return record


def build_single(candidate: dict, doc: dict) -> dict:
    reasoning = CATEGORY_TO_REASONING[candidate["proposed_category"]]
    spans = [evidence_record(1, doc, candidate["char_start"], candidate["char_end"],
                             candidate["critical_strings"])]
    return base_record(doc, spans, reasoning, candidate["proposed_question"],
                       candidate["proposed_answer"],
                       candidate["proposed_atomic_claims"],
                       candidate["generator_confidence"])


#: A demonstrative *determiner* in the answer — "takes precedence over these content
#: blocks" — points at a list the span does not contain, so the answer is unresolvable
#: from the evidence. A bare opening pronoun ("It returns 200", "This lets you filter")
#: refers back to the subject the question already named, and is not a defect: an
#: earlier version rejected four sound candidates for it.
_ANSWER_ANAPHORA = re.compile(r"\b(?:these|those|such)\s+(?!as\b)[a-z]{3,}",
                              re.IGNORECASE)
#: A question of the form "What does `X` ...?" asserts that ``X`` is the subject of the
#: fact. When the evidence has ``X`` as the object of a preposition — "Grouping by
#: `speed` requires the beta header" — that assertion is false and the question is
#: broader than its evidence.
_SUBJECT_QUESTION = re.compile(r"^What (?:does|is|must|are) (?:the )?`", re.IGNORECASE)
_PREPOSITIONS = frozenset({"by", "for", "in", "with", "on", "of", "to", "from", "into",
                           "across", "over", "under", "via", "through", "between"})


def question_scope_problem(record: dict) -> str | None:
    """Is the question's subject really the subject of its evidence?"""
    question = record["question"]
    if not _SUBJECT_QUESTION.match(question):
        return None
    subject = next(iter(re.findall(r"`([^`]+)`", question)), None)
    if subject is None:
        return None
    for span in record["expected_evidence"]:
        position = span["evidence_text"].find(f"`{subject}`")
        if position <= 0:
            continue
        preceding = span["evidence_text"][:position].strip().split()
        if preceding and preceding[-1].lower().strip(",;:") in _PREPOSITIONS:
            return (f"the question makes `{subject}` the subject, but the evidence has "
                    f"it after {preceding[-1]!r}")
    return None


def precheck(record: dict) -> list[str]:
    failures: list[str] = []
    spans = record["expected_evidence"]
    for span in spans:
        if hashlib.sha256(
                span["evidence_text"].encode("utf-8")).hexdigest() != span["evidence_hash"]:
            failures.append(f"{span['evidence_id']}: hash does not match its text")
        if not (0 <= span["char_start"] < span["char_end"]):
            failures.append(f"{span['evidence_id']}: invalid span")
        if not span["critical_strings"]:
            failures.append(f"{span['evidence_id']}: no critical strings")
        # §19: a string belongs to its own span, and is checked there.
        outside = [s for s in span["critical_strings"]
                   if not contains_claim_string(span["evidence_text"], s)]
        if outside:
            failures.append(f"{span['evidence_id']}: strings outside this span: {outside}")
        problem = anaphora_problem(span["evidence_text"])
        if problem:
            failures.append(f"{span['evidence_id']}: unresolved anaphora — {problem}")
        if span["evidence_char_length"] > EVIDENCE_HARD_CAP:
            failures.append(f"{span['evidence_id']}: over the evidence cap")
    by_id = {s["evidence_id"]: s for s in spans}
    for mapping in record.get("claim_evidence_map", []):
        span = by_id.get(mapping["evidence_id"])
        if span is None:
            failures.append(f"claim maps to unknown span {mapping['evidence_id']}")
            continue
        stray = [t for t in mapping["critical_strings"]
                 if not contains_claim_string(span["evidence_text"], t)]
        if stray:
            failures.append(
                f"{mapping['evidence_id']}: claim-mapped strings not in that span: {stray}")
    if not record["question"] or not record["answer"] or not record["atomic_claims"]:
        failures.append("question, answer or claims missing")
    dangling = _ANSWER_ANAPHORA.search(record["answer"])
    if dangling:
        failures.append("the answer points outside its evidence: "
                        f"{dangling.group(0)!r}")
    scope_problem = question_scope_problem(record)
    if scope_problem:
        failures.append(scope_problem)
    if not record["retrieval_was_not_run"]:
        failures.append("retrieval leakage")
    if record["reasoning_type"] == "genuine_multi_hop":
        if len(spans) < 2:
            failures.append("multi-hop with fewer than two spans")
        if not record.get("requires_all_evidence"):
            failures.append("multi-hop without requires_all_evidence")
        if not record.get("bridge_entity"):
            failures.append("multi-hop without a bridge entity")
        if record.get("multi_hop_composition_check") != PASS:
            failures.append("multi-hop composition check did not pass")
    return failures


def interleave_providers(pool: list[dict]) -> list[dict]:
    """Alternate providers in the order the selector walks.

    The selector fills reasoning-type floors first. Walking a provider-sorted pool meant
    the ceilings were spent on whichever provider came first alphabetically, and the
    batch came back 10 OpenAI to 4 Anthropic for no reason but ordering.
    """
    groups: dict[str, list[dict]] = {}
    for candidate in pool:
        groups.setdefault(candidate["provider"], []).append(candidate)
    ordered: list[dict] = []
    for row in zip_longest(*(groups[p] for p in sorted(groups))):
        ordered += [c for c in row if c is not None]
    return ordered


def select(pool: list[dict], size: int) -> tuple[list[dict], Counter]:
    """Fill the reasoning-type floors first, then the provider floors, then stop.

    The ceilings are hard. An earlier version applied them only in the pass that used
    them, so the provider pass — which asks only "is this OpenAI?" — filled the batch to
    20 with eight exact lookups against a ceiling of three. Reaching 20 that way is
    padding: §3 asks for fewer candidates rather than weaker ones, so a batch that
    cannot reach 20 within the ceilings comes back short.
    """
    chosen: list[dict] = []
    reasons: Counter = Counter()
    counts: Counter = Counter()
    documents: Counter = Counter()
    providers: Counter = Counter({p: 0 for p in PROVIDER_TARGET})
    blocked: dict[str, set[int]] = {}

    def note(reason: str, candidate: dict) -> None:
        # Count candidates, not attempts: the same candidate is offered to several
        # passes, and counting each look would inflate the removal table.
        if id(candidate) not in blocked.setdefault(reason, set()):
            blocked[reason].add(id(candidate))
            reasons[reason] += 1

    def admissible(candidate: dict) -> bool:
        _, ceiling = REASONING_TARGET.get(candidate["reasoning_type"], (0, size))
        if counts[candidate["reasoning_type"]] >= ceiling:
            note("reasoning_type_ceiling", candidate)
            return False
        if documents[candidate["document_title"]] >= 3:
            note("document_concentration", candidate)
            return False
        _, provider_ceiling = PROVIDER_TARGET.get(candidate["provider"], (0, size))
        if providers[candidate["provider"]] >= provider_ceiling:
            note("provider_ceiling", candidate)
            return False
        return True

    def take(predicate, quota: int) -> None:
        """Fill one quota, always spending it on the provider that is furthest behind.

        Interleaving the pool before selection was not enough: each pass walks the whole
        list looking for one reasoning type, so a type whose Anthropic material happens
        to sit late in the pool still went entirely to OpenAI. The balance has to be
        decided per pick, not per ordering.
        """
        while (len(chosen) < size
               and sum(1 for c in chosen if predicate(c)) < quota):
            order = sorted(PROVIDER_TARGET, key=lambda p: providers[p])
            pick = None
            for provider in [*order, None]:
                for candidate in pool:
                    if candidate in chosen or not predicate(candidate):
                        continue
                    if provider is not None and candidate["provider"] != provider:
                        continue
                    if not admissible(candidate):
                        continue
                    pick = candidate
                    break
                if pick is not None:
                    break
            if pick is None:
                return
            chosen.append(pick)
            counts[pick["reasoning_type"]] += 1
            documents[pick["document_title"]] += 1
            providers[pick["provider"]] += 1

    for reasoning, (floor, _) in REASONING_TARGET.items():
        if floor:
            take(lambda c, k=reasoning: c["reasoning_type"] == k, floor)
    # Provider floors, one pick at a time to whichever provider is furthest behind.
    # Running them as two whole-quota passes let the first provider take every seat the
    # reasoning ceilings had left, and the second got what was underneath: nothing.
    while len(chosen) < size:
        provider = min(PROVIDER_TARGET, key=lambda p: providers[p])
        if providers[provider] >= PROVIDER_TARGET[provider][0]:
            break
        before = len(chosen)
        take(lambda c, p=provider: c["provider"] == p, providers[provider] + 1)
        if len(chosen) == before:
            break
    for reasoning, (_, ceiling) in REASONING_TARGET.items():
        take(lambda c, k=reasoning: c["reasoning_type"] == k, ceiling)
    take(lambda c: True, size)
    return chosen[:size], reasons


def overlapping(key: tuple, blocked: set[tuple]) -> bool:
    """§22: does this span touch one of the four architecture-shaping failure cases?"""
    version, start, end = key
    return any(v == version and start < b_end and b_start < end
               for v, b_start, b_end in blocked)


#: §30's five reasons, in the order a pair is tested against them. The first matching
#: phrase wins, so a pair is counted once even when it fails several ways.
_REJECTION_BUCKETS = (
    ("span 1 alone already answers", "span_1_alone_answered_the_full_question"),
    ("span 2 alone already answers", "span_2_alone_answered_the_full_question"),
    ("different providers", "the_spans_were_two_unrelated_lookups"),
    ("states no condition on the bridge entity",
     "the_spans_were_two_unrelated_lookups"),
    ("both spans are self-contained", "the_spans_were_two_unrelated_lookups"),
    ("enumerates values rather than", "no_bridge_relationship_existed"),
    ("is not in both spans", "no_bridge_relationship_existed"),
    ("which span 1 does not contain",
     "the_composed_answer_introduced_unsupported_inference"),
    ("which span 2 does not contain",
     "the_composed_answer_introduced_unsupported_inference"),
)


def rejection_summary(rejected: list[dict], accepted: int) -> dict:
    """§30: why the miner's multi-hop attempts failed, counted from the real reasons.

    Batch 003 shipped four multi-hop labels and could not say how many it had rejected,
    because it rejected none — there was no check to fail. The counts here come from the
    checks' own strings, so the table cannot drift from what actually happened.
    """
    buckets = Counter({label: 0 for _, label in _REJECTION_BUCKETS})
    verbatim: Counter = Counter()
    unmatched = 0
    for entry in rejected:
        reason = entry["reasons"][0]
        # Trim at the em dash or colon that introduces the explanation, not at a fixed
        # width: a table row reading "…a requirement about the b" looks like a bug.
        verbatim[reason.split(" — ")[0].split(":")[0].strip()] += 1
        label = next((label for phrase, label in _REJECTION_BUCKETS if phrase in reason),
                     None)
        if label is None:
            unmatched += 1
            continue
        buckets[label] += 1
    return {
        "attempted_pairs": len(rejected) + accepted,
        "passed": accepted,
        "rejected": len(rejected),
        "reasons": dict(buckets),
        "unclassified": unmatched,
        "by_check": dict(verbatim.most_common()),
        "note": ("Counted from each check's own reason string, not asserted. A pair is "
                 "counted once, under the first reason it failed. `unclassified` is a "
                 "guard: it should be 0, and a non-zero value means a check grew a "
                 "reason the report does not know how to file."),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=20)
    parser.add_argument("--out-dir", default="evals/review")
    parser.add_argument("--report-dir", default="experiments/GOLD-001")
    args = parser.parse_args()

    with connect() as conn, conn.cursor() as cur:
        docs = load_docs(cur)
    for doc in docs:
        doc["sections"] = _sections_from_markdown(doc["text"])
    docs_by_version = {d["version_id"]: d for d in docs}

    mined: list[dict] = []
    facts: list[dict] = []
    ambiguities: list[dict] = []
    for doc in docs:
        facts += mine_bridge_facts(doc)
        # Deliberately wide. Batch 003's miner limits were tuned for a batch of
        # single-fact lookups; a bridge needs two facts that happen to share an entity,
        # and a narrow pool simply never contains the pair.
        mined += mine_prose(doc, limit=60)
        mined += mine_row_facts(doc, limit=20)
        mined += mine_definition_bullets(doc, limit=20)
        for finding in find_ambiguous_fields(doc, limit=4):
            record = build_ambiguity(doc, finding)
            if record is not None:
                ambiguities.append(record)
    pool_size = len(mined)

    removed: Counter = Counter()
    questions, spans_seen, excluded = prior_material()

    # §22 first: a span that overlaps AN-001/AN-003/AN-012/OA-004 never reaches the
    # composer, so it cannot arrive inside a multi-hop pair through the back door.
    def allowed(candidate: dict) -> bool:
        key = (candidate["version_id"], candidate["char_start"], candidate["char_end"])
        if overlapping(key, excluded):
            removed["excluded_known_failure_case"] += 1
            return False
        return True

    mined = [c for c in mined if allowed(c)]
    facts = [c for c in facts if allowed(c)]

    pairs, rejected_pairs = find_bridges(facts, limit=10)
    multi_hop: list[dict] = []
    consumed: set[tuple] = set()
    for pair in pairs:
        record = build_multi_hop(pair, docs_by_version)
        if record is None:
            removed["fake_multi_hop"] += 1
            continue
        multi_hop.append(record)
        consumed.update((s["version_id"], s["char_start"], s["char_end"])
                        for s in record["expected_evidence"])
    removed["fake_multi_hop"] += len(rejected_pairs)

    # A fact only ever leaves this script inside a composed case. Facts are mined
    # without a standalone question by design — §15 authors the question from the
    # reasoning structure, and a hop member has none of its own.
    singles = [build_single(c, docs_by_version[c["version_id"]])
               for c in mined
               if (c["version_id"], c["char_start"], c["char_end"]) not in consumed]

    # Facts that were not composed into a hop are still evidence. A sentence carrying
    # its own condition and outcome is a complete reasoning case on one span, and
    # discarding it because the bridge search had no use for it would throw away the
    # material §10 and §14 ask for.
    conditionals = []
    for fact in facts:
        if (fact["version_id"], fact["char_start"], fact["char_end"]) in consumed:
            continue
        record = build_conditional(fact, docs_by_version[fact["version_id"]])
        if record is not None:
            conditionals.append(record)

    pool = multi_hop + ambiguities + conditionals + singles

    kept: list[dict] = []
    seen_questions: set[str] = set()
    seen_spans: set[tuple] = set()
    for candidate in sorted(pool, key=lambda c: (c["version_id"],
                                                 c["expected_evidence"][0]["char_start"])):
        key = normalise_question(candidate["question"])
        span_key = tuple(sorted((s["version_id"], s["char_start"], s["char_end"])
                                for s in candidate["expected_evidence"]))
        if key in questions or key in seen_questions:
            removed["duplicate_question"] += 1
            continue
        if any(k in spans_seen or k in seen_spans for k in span_key):
            removed["duplicate_evidence"] += 1
            continue
        if candidate["evidence_char_length"] > EVIDENCE_HARD_CAP:
            removed["oversized_evidence"] += 1
            continue
        failures = precheck(candidate)
        if failures:
            bucket = ("blocking_anaphora" if any("anaphora" in f for f in failures)
                      else "missing_critical_strings"
                      if any("critical strings" in f or "strings outside" in f
                             for f in failures)
                      else "failed_precheck")
            removed[bucket] += 1
            continue
        candidate["precheck_holdout_ready"] = True
        candidate["precheck_failures"] = []
        seen_questions.add(key)
        seen_spans.update(span_key)
        kept.append(candidate)

    eligible_by_reasoning = dict(Counter(c["reasoning_type"] for c in kept))
    eligible_by_provider = dict(Counter(c["provider"] for c in kept))
    chosen, selection_reasons = select(interleave_providers(kept), args.size)
    removed.update(selection_reasons)
    removed["not_selected_diversity"] = len(kept) - len(chosen)

    for position, candidate in enumerate(sorted(
            chosen, key=lambda c: (c["provider"], c["reasoning_type"],
                                   c["document_title"])), start=1):
        candidate["candidate_id"] = f"GOLD-B004-{position:02d}"
    chosen.sort(key=lambda c: c["candidate_id"])

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                         stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        commit = None

    lengths = sorted(s["evidence_char_length"]
                     for c in chosen for s in c["expected_evidence"])
    payload = {
        "batch": 4,
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "corpus_snapshot": SNAPSHOT,
        "candidate_pool_size": pool_size,
        "candidates": len(chosen),
        "by_provider": dict(Counter(c["provider"] for c in chosen)),
        "by_reasoning_type": dict(Counter(c["reasoning_type"] for c in chosen)),
        "by_evidence_shape": dict(Counter(c["evidence_shape"] for c in chosen)),
        "by_confidence": dict(Counter(c["generator_confidence"] for c in chosen)),
        "unique_documents": len({c["document_title"] for c in chosen}),
        "documents_by_provider": {
            provider: len({c["document_title"] for c in chosen
                           if c["provider"] == provider})
            for provider in sorted({c["provider"] for c in chosen})},
        "versions_by_provider": {
            provider: len({v for c in chosen if c["provider"] == provider
                           for v in {s["version_id"] for s in c["expected_evidence"]}})
            for provider in sorted({c["provider"] for c in chosen})},
        "genuine_multi_hop": sum(1 for c in chosen
                                 if c["reasoning_type"] == "genuine_multi_hop"),
        "multi_document": sum(1 for c in chosen if c.get("document_count", 1) > 1),
        "needs_human_interpretation": sum(1 for c in chosen
                                          if c["needs_human_interpretation"]),
        "precheck_holdout_ready": sum(1 for c in chosen
                                      if c["precheck_holdout_ready"]),
        "evidence_length": {
            "spans": len(lengths),
            "mean": round(sum(lengths) / len(lengths), 1) if lengths else 0,
            "median": lengths[len(lengths) // 2] if lengths else 0,
            "max": max(lengths) if lengths else 0,
            "over_soft_cap": sum(1 for n in lengths if n > EVIDENCE_SOFT_CAP),
        },
        "removed": dict(removed),
        "eligible_pool": {"by_reasoning_type": eligible_by_reasoning,
                          "by_provider": eligible_by_provider,
                          "candidates": len(kept)},
        "multi_hop_rejection": rejection_summary(rejected_pairs, len(multi_hop)),
        "verification_status": "candidate_unverified — nothing in this file is gold",
        "retrieval_was_not_run": True,
        "systems_executed": [],
        "records": chosen,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "gold_review_batch_004.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    payload["batch_sha256"] = hashlib.sha256(json_path.read_bytes()).hexdigest()
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    (out_dir / "gold_review_batch_004.md").write_text(render(payload), encoding="utf-8")
    write_report(payload, Path(args.report_dir))

    print(f"pool {pool_size} mined -> {len(kept)} eligible -> batch 004 with {len(chosen)}")
    print("  provider  :", payload["by_provider"])
    print("  reasoning :", payload["by_reasoning_type"])
    print("  shape     :", payload["by_evidence_shape"])
    print("  documents :", payload["unique_documents"], payload["documents_by_provider"])
    print("  evidence  : mean", payload["evidence_length"]["mean"],
          "median", payload["evidence_length"]["median"],
          "max", payload["evidence_length"]["max"])
    print("  removed   :", payload["removed"])
    print("  multi-hop rejections:", payload["multi_hop_rejection"]["reasons"])
    return 0


def code_span(text: str) -> str:
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def render(payload: dict) -> str:
    lines: list[str] = [
        "# Gold review batch 004",
        "",
        (f"**{payload['candidates']} candidates · corpus snapshot "
         f"`{payload['corpus_snapshot']}` · generated {payload['generated_at']}**"),
        "",
        ("Nothing in this file is ground truth. Every candidate is "
         "`candidate_unverified`. The evidence is quoted verbatim from the frozen "
         "corpus and is authoritative for this review — **do not consult live "
         "documentation**, which may have changed since the snapshot."),
        "",
        ("Batch 003 closed with zero genuine multi-hop cases: four were labelled that "
         "way and none survived scrutiny. This batch separates `reasoning_type` from "
         "`evidence_shape` and puts every multi-hop candidate through a composition "
         "check that fails the pair whenever one span already answers the question. "
         "Where you think a `genuine_multi_hop` case is really a two-span lookup, say "
         "so — that is the judgement this batch most needs."),
        "",
        (f"Provider {payload['by_provider']} · "
         f"reasoning {payload['by_reasoning_type']} · "
         f"{payload['unique_documents']} distinct documents · "
         f"median span {payload['evidence_length']['median']} characters."),
        "",
        "| id | provider | reasoning type | shape | chars | question |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for record in payload["records"]:
        question = record["question"]
        short = question if len(question) <= 70 else question[:67] + "…"
        lines.append(f"| `{record['candidate_id'][-2:]}` | {record['provider']} | "
                     f"{record['reasoning_type']} | {record['evidence_shape']} | "
                     f"{record['evidence_char_length']} | {short} |")
    lines += ["", "---", ""]

    for record in payload["records"]:
        spans = record["expected_evidence"]
        lines += [
            f"## {record['candidate_id']}",
            "",
            f"- **provider**: {record['provider']}",
            f"- **document**: {record['document_title']}",
            f"- **section**: {' › '.join(record['section_path'])}",
            (f"- **reasoning type**: `{record['reasoning_type']}` · "
             f"**evidence shape**: `{record['evidence_shape']}` · "
             f"**requires all evidence**: {record['requires_all_evidence']}"),
            (f"- **confidence**: {record['generator_confidence']} · "
             f"**precheck holdout-ready**: {record['precheck_holdout_ready']}"),
            "",
            f"**Q.** {record['question']}",
            "",
            f"**A.** {record['answer']}",
            "",
            "**Atomic claims**",
            "",
        ]
        lines += [f"  {i}. {c}" for i, c in enumerate(record["atomic_claims"], 1)]
        lines += [""]

        if record["reasoning_type"] == "genuine_multi_hop":
            lines += [
                "**Composition**",
                "",
                f"- **bridge entity**: {code_span(record['bridge_entity'])}",
                f"- **relationship**: {record['bridge_relationship']}",
                f"- **hop 1**: {record['hop_1_claim']}",
                f"- **hop 2**: {record['hop_2_claim']}",
                f"- **composed**: {record['composed_claim']}",
                (f"- **span 1 alone is not enough**: "
                f"{record['why_span_1_alone_is_insufficient']}"),
                (f"- **span 2 alone is not enough**: "
                f"{record['why_span_2_alone_is_insufficient']}"),
                (f"- **composition check**: "
                 f"`{record['multi_hop_composition_check']}` · "
                 f"documents {record['document_count']} · "
                 f"sections {record['section_count']}"),
                "",
            ]
        if record["reasoning_type"] == "ambiguity_disambiguation":
            lines += ["**Ambiguity**", "",
                      f"- **term**: {code_span(record['ambiguous_term'])}"]
            lines += [f"  - in `{r['scope']}`: {r['meaning']}"
                      for r in record["candidate_interpretations"]]
            lines += [f"- **scope needed to answer**: {record['required_scope_to_answer']}",
                      ""]

        lines += ["**Exact evidence**", ""]
        for index, span in enumerate(spans, 1):
            label = f" (span {index} of {len(spans)})" if len(spans) > 1 else ""
            lines += [
                (f"`{span['evidence_id']}` · `{span['version_id']}` "
                 f"{span['char_start']}–{span['char_end']} "
                 f"({span['evidence_char_length']} chars){label} · "
                 f"{' › '.join(span['section_path'])}"),
                "", "```", span["evidence_text"], "```",
                ("**critical strings**: "
                 + ", ".join(code_span(s) for s in span["critical_strings"])),
                "",
            ]
        lines += ["**Claim → evidence**", ""]
        lines += [f"  {i}. {m['claim']} → `{m['evidence_id']}`"
                  for i, m in enumerate(record["claim_evidence_map"], 1)]
        lines += ["", ("<details><summary>surrounding context (review only — not part "
                       "of the gold evidence)</summary>"), "", "```",
                  f"…{record['context_before'][-400:].strip()}", "  ⟦EVIDENCE⟧",
                  f"{record['context_after'][:400].strip()}…", "```", "", "</details>",
                  "", "---", ""]
    return "\n".join(lines)


ELIGIBILITY = "experiments/GOLD-001/GOLD-001-eligibility-status.json"


def confirmed_coverage() -> dict:
    """What batches 001–003 actually hold, read from the eligibility artifact.

    Prose summaries are not a source here. The eligible ids come from the eligibility
    status, and the reasoning labels from the closed batch records those ids name.
    """
    status = json.loads(Path(ELIGIBILITY).read_text())
    batches = []
    combined_reasoning: Counter = Counter()
    combined_provider: Counter = Counter()
    for entry in status["batches"]:
        records = {r["candidate_id"]: r
                   for r in json.loads(Path(entry["closed_record"]).read_text())["records"]}
        eligible = [records[i] for i in entry["holdout_eligible_ids"] if i in records]
        # Batches 001 and 002 predate the reasoning-type split; their stored label is
        # ``proposed_category``. Reporting that verbatim is more honest than back-filling
        # a dimension those batches were never authored against.
        reasoning = Counter(r.get("reasoning_type") or r.get("proposed_category")
                            for r in eligible)
        provider = Counter(r["provider"] for r in eligible)
        combined_reasoning.update(reasoning)
        combined_provider.update(provider)
        batches.append({
            "batch": entry["batch"],
            "human_verified": entry["human_verified"],
            "holdout_eligible": entry["holdout_eligible"],
            "human_rejected": entry["human_rejected"],
            "by_reasoning_type": dict(reasoning),
            "by_provider": dict(provider),
            "genuine_multi_hop": sum(1 for r in eligible
                                     if r.get("reasoning_type") == "genuine_multi_hop"),
        })
    return {
        "source": ELIGIBILITY,
        "batches": batches,
        "combined": status["combined"],
        "by_reasoning_type": dict(combined_reasoning),
        "by_provider": dict(combined_provider),
        "genuine_multi_hop": sum(b["genuine_multi_hop"] for b in batches),
        "holdout_frozen": status["holdout_frozen"],
    }


def render_coverage(coverage: dict, payload: dict) -> str:
    confirmed = coverage["combined"]
    projected_reasoning = Counter(coverage["by_reasoning_type"])
    projected_reasoning.update(payload["by_reasoning_type"])
    projected_provider = Counter(coverage["by_provider"])
    projected_provider.update(payload["by_provider"])
    rows = "\n".join(
        f"| `{name}` | {coverage['by_reasoning_type'].get(name, 0)} | "
        f"{payload['by_reasoning_type'].get(name, 0)} | {projected_reasoning[name]} |"
        for name in sorted(projected_reasoning))
    provider_rows = "\n".join(
        f"| {name} | {coverage['by_provider'].get(name, 0)} | "
        f"{payload['by_provider'].get(name, 0)} | {projected_provider[name]} |"
        for name in sorted(projected_provider))
    batch_rows = "\n".join(
        f"| {b['batch']} | {b['human_verified']} | {b['holdout_eligible']} | "
        f"{b['human_rejected']} | {b['genuine_multi_hop']} |"
        for b in coverage["batches"])
    return "\n".join([
        "# GOLD-001 — coverage status after batch 004 generation",
        "",
        (f"**Confirmed eligible today: {confirmed['holdout_eligible']}.** "
         f"Batch 004 adds {payload['candidates']} *candidates*, which are not eligible "
         "and not verified. The projection below is what coverage **would** be if every "
         "batch-004 candidate were later approved — no batch has ever approved every "
         "candidate, so treat it as a ceiling, not a forecast."),
        "",
        "## Confirmed — batches 001–003 (human-approved, closed)",
        "",
        "| batch | human_verified | holdout_eligible | rejected | genuine multi-hop |",
        "| --- | --- | --- | --- | --- |",
        batch_rows,
        (f"| **total** | **{confirmed['human_verified']}** | "
         f"**{confirmed['holdout_eligible']}** | "
         f"**{confirmed['human_rejected']}** | "
         f"**{coverage['genuine_multi_hop']}** |"),
        "",
        (f"Read from `{coverage['source']}` and the closed batch records it names. "
         f"Holdout frozen: **{coverage['holdout_frozen']}**."),
        "",
        "## Reasoning-type coverage",
        "",
        "| reasoning type | confirmed (001–003) | batch 004 candidates | projected |",
        "| --- | --- | --- | --- |",
        rows,
        "",
        ("Batches 001 and 002 are reported under `exact_lookup`, the label they were "
         "authored with: the reasoning-type/evidence-shape split arrived in batch 003, "
         "and relabelling closed batches to make the table look richer would be "
         "inventing coverage that was never reviewed. `lifecycle` and "
         "`lifecycle_compatibility_migration` are the same category under batch 003's "
         "name and batch 004's; they are listed separately for the same reason."),
        "",
        "## Provider coverage",
        "",
        "| provider | confirmed (001–003) | batch 004 candidates | projected |",
        "| --- | --- | --- | --- |",
        provider_rows,
        "",
        "## The gap batch 004 is aimed at",
        "",
        (f"Genuine multi-hop in the confirmed set is "
         f"**{coverage['genuine_multi_hop']}**. Batch 004 proposes "
         f"{payload['genuine_multi_hop']}, with {payload['multi_document']} drawing on "
         "more than one document. Whether that number survives review is the point of "
         "the batch; batch 003 proposed four and kept none."),
        "",
        "## What this report does not say",
        "",
        ("- no batch-004 candidate is eligible, verified, or gold;\n"
         "- no retrieval system was run against any candidate in any batch;\n"
         "- the holdout is not frozen, and this report does not freeze it."),
        "",
    ])


def render_report(report: dict) -> str:
    targets = report["targets"]
    pool = report["eligible_pool"]["by_reasoning_type"]
    reasoning_rows = "\n".join(
        f"| `{name}` | {report['by_reasoning_type'].get(name, 0)} | {low}–{high} | "
        f"{'yes' if low <= report['by_reasoning_type'].get(name, 0) <= high else 'NO'} | "
        f"{pool.get(name, 0)} |"
        for name, (low, high) in targets["reasoning_type"].items())
    provider_rows = "\n".join(
        f"| {name} | {report['by_provider'].get(name, 0)} | {low}–{high} | "
        f"{'yes' if low <= report['by_provider'].get(name, 0) <= high else 'NO'} |"
        for name, (low, high) in targets["provider"].items())
    removed_rows = "\n".join(f"| {reason.replace('_', ' ')} | {count} |"
                             for reason, count in sorted(report["removed"].items()))
    rejection = report["multi_hop_rejection"]
    rejection_rows = "\n".join(
        f"| {reason.replace('_', ' ')} | {count} |"
        for reason, count in sorted(rejection["reasons"].items(),
                                    key=lambda item: -item[1]))
    check_rows = "\n".join(f"| {check} | {count} |"
                           for check, count in rejection["by_check"].items())
    return "\n".join([
        "# GOLD-001 — batch 004 generation report",
        "",
        (f"**{report['total_candidates']} candidates** from a mined pool of "
         f"{report['candidate_pool_size']}, across {report['unique_documents']} "
         "distinct documents. Nothing is verified; nothing is gold."),
        "",
        ("Batch 004 was commissioned to fix a specific hole: batch 003 closed with "
         "**zero** genuine multi-hop cases after four candidates carrying that label "
         "failed scrutiny. The composition check now runs before export rather than "
         "after review."),
        "",
        "## Composition",
        "",
        "| | |",
        "| --- | --- |",
        f"| provider | {report['by_provider']} |",
        f"| documents by provider | {report['documents_by_provider']} |",
        f"| versions by provider | {report['versions_by_provider']} |",
        f"| reasoning type | {report['by_reasoning_type']} |",
        f"| evidence shape | {report['by_evidence_shape']} |",
        f"| confidence | {report['by_confidence']} |",
        f"| genuine multi-hop | {report['genuine_multi_hop']} |",
        f"| multi-document | {report['multi_document']} |",
        (f"| complete question+answer+claims | "
         f"{report['complete_question_answer_claims']} of "
         f"{report['total_candidates']} |"),
        (f"| needing reviewer judgement | {report['needs_human_interpretation']} of "
         f"{report['total_candidates']} |"),
        (f"| precheck holdout-ready | {report['precheck_holdout_ready']} of "
         f"{report['total_candidates']} |"),
        "",
        "### Reasoning types against target",
        "",
        "| reasoning type | in batch | target | met | eligible candidates available |",
        "| --- | --- | --- | --- | --- |",
        reasoning_rows,
        "",
        ("The last column is the honest part. Where it is at or below the batch count, "
         "the corpus had nothing more to give under the checks in §6, §9 and §20 — the "
         "target was not missed by selection. Where it is far above, the ceiling stopped "
         "the batch, not the material."),
        "",
        "### Providers against target",
        "",
        "| provider | in batch | target | met |",
        "| --- | --- | --- | --- |",
        provider_rows,
        "",
        ("A target that reads `NO` was not met, and was not made to read `yes` by "
         "relabelling a candidate or lowering the evidence standard. §3 of the brief "
         "puts quality above count, and a missed target is the honest report of what "
         "the frozen corpus supports."),
        "",
        "## Evidence size",
        "",
        (f"Across {report['evidence_length']['spans']} spans: mean "
         f"{report['evidence_length']['mean']}, median "
         f"{report['evidence_length']['median']}, max "
         f"{report['evidence_length']['max']} characters. "
         f"{report['evidence_length']['over_soft_cap']} over the "
         f"{EVIDENCE_SOFT_CAP}-character soft cap, none over the "
         f"{EVIDENCE_HARD_CAP} hard cap. Multi-hop cases are measured per span, not "
         "per case, because the size that matters is the size of each anchor."),
        "",
        "## Removed before export",
        "",
        "| reason | count |",
        "| --- | --- |",
        removed_rows,
        "",
        "## Fake multi-hop rejection",
        "",
        (f"The composer tested {rejection['attempted_pairs']} bridge pairs. "
         f"{rejection['passed']} passed the composition check; "
         f"{rejection['rejected']} were rejected. That ratio is the finding: in this "
         "corpus, two facts sharing an "
         "identifier are almost never two halves of an argument."),
        "",
        "| rejection reason | count |",
        "| --- | --- |",
        rejection_rows,
        "",
        rejection["note"],
        "",
        "### The same rejections by the check that made them",
        "",
        "| check | pairs |",
        "| --- | --- |",
        check_rows,
        "",
        ("This is the number batch 003 could not produce, because it had no check to "
         "fail. A rejection rate that looks bad is the measurement working: it says how "
         "often two facts that share an identifier are not actually a hop."),
        "",
        "## Retrieval",
        "",
        ("No retrieval system was run against any batch-004 candidate at any point. "
         "SYSTEM-A and SYSTEM-B remain frozen and were not executed. No candidate was "
         "selected, ordered or worded because of what any system does with it, and no "
         "difficulty label in this batch derives from retrieval behaviour."),
        "",
    ])


def check_report_consistency(report: dict) -> None:
    """Refuse to write a report that contradicts itself.

    Batch 003's first report claimed every candidate precheck-ready while also counting
    an anaphoric span, and used one label for two different quantities. Both were report
    defects caught by a person reading two tables against each other. The generator does
    it here instead.
    """
    problems = []
    if report["genuine_multi_hop"] != report["by_reasoning_type"].get(
            "genuine_multi_hop", 0):
        problems.append("genuine_multi_hop disagrees with the reasoning-type table")
    if report["precheck_holdout_ready"] > report["total_candidates"]:
        problems.append("more precheck-ready candidates than candidates")
    if report["complete_question_answer_claims"] > report["total_candidates"]:
        problems.append("more complete proposals than candidates")
    if sum(report["by_reasoning_type"].values()) != report["total_candidates"]:
        problems.append("the reasoning-type counts do not sum to the candidate count")
    if sum(report["by_evidence_shape"].values()) != report["total_candidates"]:
        problems.append("the evidence-shape counts do not sum to the candidate count")
    if report["multi_document"] > report["by_evidence_shape"].get("multi_document", 0) \
            + report["by_evidence_shape"].get("multi_span", 0):
        problems.append("more multi-document cases than multi-span ones")
    if problems:
        raise SystemExit("refusing to write a self-contradicting report:\n  "
                         + "\n  ".join(problems))


def write_report(payload: dict, report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "batch": 4,
        "generated_at": payload["generated_at"],
        "batch_sha256": payload["batch_sha256"],
        "total_candidates": payload["candidates"],
        "candidate_pool_size": payload["candidate_pool_size"],
        "by_provider": payload["by_provider"],
        "documents_by_provider": payload["documents_by_provider"],
        "versions_by_provider": payload["versions_by_provider"],
        "unique_documents": payload["unique_documents"],
        "by_reasoning_type": payload["by_reasoning_type"],
        "by_evidence_shape": payload["by_evidence_shape"],
        "by_confidence": payload["by_confidence"],
        "genuine_multi_hop": payload["genuine_multi_hop"],
        "multi_document": payload["multi_document"],
        "needs_human_interpretation": payload["needs_human_interpretation"],
        "precheck_holdout_ready": payload["precheck_holdout_ready"],
        "evidence_length": payload["evidence_length"],
        "removed": payload["removed"],
        "eligible_pool": payload["eligible_pool"],
        "multi_hop_rejection": payload["multi_hop_rejection"],
        "complete_question_answer_claims": sum(
            1 for r in payload["records"] if r["answer"] and r["atomic_claims"]),
        "retrieval_was_not_run": True,
        "systems_executed": [],
        "targets": {"provider": PROVIDER_TARGET, "reasoning_type": REASONING_TARGET},
    }
    check_report_consistency(report)
    (report_dir / "GOLD-001-batch-004-generation-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "GOLD-001-batch-004-generation-report.md").write_text(
        render_report(report), encoding="utf-8")

    coverage = confirmed_coverage()
    (report_dir / "GOLD-001-coverage-status-after-b004-generation.json").write_text(
        json.dumps({"confirmed": coverage,
                    "batch_004_candidates": {
                        "candidates": payload["candidates"],
                        "by_reasoning_type": payload["by_reasoning_type"],
                        "by_provider": payload["by_provider"],
                        "holdout_eligible": 0,
                        "human_verified": 0}},
                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "GOLD-001-coverage-status-after-b004-generation.md").write_text(
        render_coverage(coverage, payload), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
