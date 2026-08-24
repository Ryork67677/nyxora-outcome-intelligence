#!/usr/bin/env python3
"""GOLD-001: generate batch 006 — the final large coverage push.

Two things make this batch different from batch 005.

The first is that it carries the four fixes batch 005's closure preregistered, and they
run *before* anything is authored: the bare-definition-bullet rule now asks its question
of every span rather than only of single-span records; markdown reference links are
stripped from questions by a normaliser that handles all three link shapes; the heading
parser has been audited and ``section_path`` is no longer trusted for claim scope; and
every candidate carries a source triple and a question triple, compared before export,
so a question that reverses its source's relation cannot leave.

The second is that no multi-hop search runs. Batch 004 tested 559 identifier-sharing
pairs and found one chain; batch 005 searched dependency-first and found the same one.
Two searches, two methods, one composable structure — the corpus has been measured, and
spending this batch's effort measuring it a third time would buy nothing. A chain that
appears naturally is still admissible under the existing composition rules; none is
sought.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.db import connect
from rag_v1.gold import relations, scoping
from rag_v1.gold.ambiguity import find_ambiguous_fields
from rag_v1.gold.authoring import (
    DANGLING_REFERENCE,
    build_comparison,
    build_conditional,
    build_constraint,
    build_cross_component_ambiguity,
    build_interaction,
    build_lifecycle,
    build_predicate_fact,
    sentence,
)
from rag_v1.gold.mining_v3 import mine_definition_bullets, mine_prose, mine_row_facts
from rag_v1.gold.mining_v5 import (
    find_cross_component_ambiguity,
    mine_constraints,
    mine_interactions,
    mine_lifecycle,
)
from rag_v1.gold.normalisation import contains_claim_string, has_markdown_link
from rag_v1.gold.questionform import evaluate as question_form
from rag_v1.parsing import _sections_from_markdown

SCHEMA_VERSION = "1.3"
SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"
BATCH = 6
PRIOR = (
    "evals/review/gold_review_batch_001.json",
    "evals/review/gold_review_batch_002.json",
    "evals/review/gold_review_batch_003.json",
    "evals/review/gold_review_batch_004_final.json",
    "evals/review/gold_review_batch_005_final.json",
)
DEVELOPMENT = "evals/development/v1.jsonl"
ELIGIBILITY = "experiments/GOLD-001/GOLD-001-eligibility-status.json"
HEADING_AUDIT = "experiments/GOLD-001/GOLD-001-heading-parser-audit.json"
EXCLUDED_FAILURE_CASES = ("AN-001", "AN-003", "AN-012", "OA-004")

#: §1 and §8. Floors and ceilings on the mixture; ceilings are hard.
TARGET_SIZE = 28
MINIMUM_USEFUL = 20
REASONING_TARGET = {
    "error_behavior": (5, 6),
    "configuration_interaction": (6, 7),
    "exact_lookup": (5, 6),
    "lifecycle_compatibility_migration": (4, 5),
    "ambiguity_disambiguation": (0, 3),
    "comparison": (0, 2),
    "genuine_multi_hop": (0, 1),
}
PROVIDER_TARGET = {"openai": (12, 14), "anthropic": (12, 14)}
CATEGORY_TO_REASONING = {
    "exact_constraint": "exact_lookup",
    "error_behavior": "error_behavior",
    "configuration_interaction": "configuration_interaction",
    "lifecycle": "lifecycle_compatibility_migration",
}
EVIDENCE_SOFT_CAP = 1000
EVIDENCE_HARD_CAP = 1500
#: §6 wants twenty distinct documents out of twenty-eight candidates, so no page may
#: supply more than two. Batch 005 allowed three and came back with sixteen documents.
MAX_PER_DOCUMENT = 2
MAX_PER_QUESTION_OPENING = 6
#: §8's ambiguity and comparison categories are corpus-limited and their floors are
#: zero, so the batch fills from the categories that have material rather than padding
#: or forcing. Anything taken this way is marked and counted.
OVERFLOW_CAP = {"error_behavior": 3, "configuration_interaction": 3, "exact_lookup": 3,
                "lifecycle_compatibility_migration": 2}

#: §Fix D. The builders speak their own relation vocabulary; these are the ones the
#: direction check can read directly. Anything else falls back to a generic triple,
#: which is recorded as such rather than dressed up as a parse.
RELATION_MAP = {
    "takes_precedence": "takes_precedence_over",
    "overrides": "overrides",
    "disables": "disables",
    "requires": "requires",
    "ignored_under_condition": "ignores",
    "changes_behaviour": "changes",
    "must_be_paired_with": "must_be_paired_with",
    "must_be_combined_with": "must_be_paired_with",
    "must_be_used_with": "must_be_paired_with",
    "is_not_supported_on": "is_not_supported_on",
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


def verify_state() -> dict:
    """Read the project's state from the records before adding to it."""
    status = json.loads(Path(ELIGIBILITY).read_text())
    combined = status["combined"]
    if status["holdout_frozen"]:
        raise SystemExit("the holdout is frozen — batch 006 must not be generated into "
                         "a frozen evaluation")
    if not status["retrieval_was_not_run"] or status["systems_executed"]:
        raise SystemExit("the eligibility status records a retrieval run; stop and "
                         "diagnose before authoring more candidates")
    return {
        "human_verified": combined["human_verified"],
        "holdout_eligible": combined["holdout_eligible"],
        "human_rejected": combined["human_rejected"],
        "genuine_multi_hop": combined["genuine_multi_hop"],
        "candidates": combined["candidates"],
        "by_batch": [{k: b[k] for k in
                      ("batch", "human_verified", "holdout_eligible", "human_rejected",
                       "genuine_multi_hop")} for b in status["batches"]],
        "holdout_frozen": status["holdout_frozen"],
        "read_from": ELIGIBILITY,
    }


def verify_frozen_systems() -> dict:
    """§3: the retrieval systems are frozen, and this batch must not have moved them."""
    from rag_v1.systems import FROZEN_HASHES

    expected = {
        "SYSTEM-A-GLOBAL":
            "9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38",
        "SYSTEM-B-DOC-C":
            "304c350940b83733df6043ae3a8abdcbcde33d16950730127aa9f1f39494388b",
    }
    if dict(FROZEN_HASHES) != expected:
        raise SystemExit("a frozen system's config hash has changed; stop and diagnose")
    return expected


def suspicious_headings() -> set[str]:
    """Headings the audit judged to be prose. §Fix C: never used as claim scope."""
    path = Path(HEADING_AUDIT)
    if not path.exists():
        return set()
    report = json.loads(path.read_text())
    return {e["heading"] for e in report["examples"] if e["likely_prose"]}


def normalise_question(question: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", question.lower()).split())


def prior_material() -> tuple[set[str], set[tuple], set[tuple], set[str]]:
    """Everything already spent: questions, spans, excluded failures, and facts."""
    questions: set[str] = set()
    spans: set[tuple] = set()
    excluded: set[tuple] = set()
    texts: set[str] = set()
    for path in PRIOR:
        payload = json.loads(Path(path).read_text())
        for record in payload["records"]:
            for field in ("proposed_question", "question"):
                if record.get(field):
                    questions.add(normalise_question(record[field]))
            for span in (record.get("expected_evidence") or [record]):
                if span.get("version_id") is None:
                    continue
                spans.add((span["version_id"], span["char_start"], span["char_end"]))
                texts.add(" ".join(span.get("evidence_text", "").split()))
            for revision in record.get("anchor_revisions", []):
                for key in ("old_spans", "new_spans"):
                    for span in revision.get(key, []):
                        spans.add((record["version_id"], span["char_start"],
                                   span["char_end"]))
                if "old_char_start" in revision:
                    spans.add((record.get("version_id"), revision["old_char_start"],
                               revision["old_char_end"]))
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
    return questions, spans, excluded, texts


def evidence_record(index: int, doc: dict, start: int, end: int,
                    critical: list[str]) -> dict:
    from rag_v1.gold.mining import _section_for
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


def triples(built: dict, spans: list[dict]) -> dict:
    """§Fix D and §27: the source's triple and the question's, both on the record.

    The question triple comes from the builder, which knows what it made the subject.
    The source triple is read out of the evidence — by the directed-relation reader
    where the relation is one this project has named, and by a generic predicate split
    otherwise. Which one was used is recorded, because a generic split is weaker
    evidence about direction than a named relation and a reader should be able to tell.
    """
    evidence = " \n".join(s["evidence_text"] for s in spans)
    question_relation = built.get("question_relation")
    mapped = RELATION_MAP.get(question_relation, question_relation)
    source = None
    if mapped in relations.RELATION_PATTERNS:
        source = relations.derive_source_triple(evidence, mapped,
                                                built.get("question_subject"))
    if source is None:
        source = relations.derive_generic_triple(evidence, built.get("question_subject"))
    if source is None:
        source = {"source_subject": None, "source_relation": None,
                  "source_object": None, "source_sentence": None,
                  "derivation": "not derivable from the evidence"}
    source.setdefault("derivation", "named relation")
    return {
        "source_subject": source["source_subject"],
        "source_relation": source["source_relation"],
        "source_object": source["source_object"],
        "source_sentence": source["source_sentence"],
        "source_triple_derivation": source["derivation"],
        "question_subject": built.get("question_subject"),
        "question_relation": question_relation,
        "question_object": built.get("question_object"),
    }


def base_record(doc: dict, spans: list[dict], built: dict, confidence: str) -> dict:
    from rag_v1.gold.mining import _context
    shape = "single_span" if len(spans) == 1 else (
        "multi_document" if len({s["version_id"] for s in spans}) > 1 else "multi_span")
    first, last = spans[0], spans[-1]
    record = {
        "candidate_id": "",
        "provider": doc["provider"],
        "document_title": doc["title"],
        "version_id": doc["version_id"],
        "source_url": doc.get("url"),
        "captured_at": str(doc.get("captured_at")),
        "reasoning_type": built["reasoning_type"],
        "secondary_category": built.get("secondary_category"),
        "evidence_shape": shape,
        "requires_all_evidence": len(spans) > 1,
        "question": built["question"],
        "answer": built["answer"],
        "atomic_claims": built["atomic_claims"],
        "proposed_question": built["question"],
        "proposed_answer": built["answer"],
        "proposed_atomic_claims": built["atomic_claims"],
        **triples(built, spans),
        "expected_evidence": spans,
        "claim_evidence_map": map_claims(built["atomic_claims"], spans),
        "section_path": first["section_path"],
        "section_path_trusted_for_scope": False,
        "critical_strings": [s for span in spans for s in span["critical_strings"]],
        "evidence_char_length": sum(s["evidence_char_length"] for s in spans),
        "context_before": _context(doc["text"], first["char_start"],
                                   first["char_end"])[0],
        "context_after": _context(doc["text"], last["char_start"], last["char_end"])[1],
        "candidate_type": "supported",
        "generator_confidence": confidence,
        "needs_human_interpretation": built.get(
            "needs_human_interpretation",
            built["reasoning_type"] == "genuine_multi_hop"),
        "precheck_holdout_ready": False,
        "precheck_failures": [],
        "precheck_flags": [],
        "internal_semantic_review_status": None,
        "internal_review_findings": [],
        "generation_repairs": [],
        "verification_status": "candidate_unverified",
        "claude_proposed": True,
        "chatgpt_verified": None,
        "retrieval_was_not_run": True,
        "schema_version": SCHEMA_VERSION,
        "revisions": [],
    }
    for key in ("ambiguous_term", "candidate_interpretations",
                "required_scope_to_answer"):
        if key in built:
            record[key] = built[key]
    return record


def precheck(record: dict) -> tuple[list[str], list[str]]:
    """§23: structural only. Says the record is checkable, not that it is right."""
    from rag_v1.gold.anaphora import CRITICAL, NONCRITICAL, evaluate_span
    failures: list[str] = []
    flags: list[str] = []
    spans = record["expected_evidence"]
    for span in spans:
        body = span["evidence_text"]
        if hashlib.sha256(body.encode("utf-8")).hexdigest() != span["evidence_hash"]:
            failures.append(f"{span['evidence_id']}: hash does not match its text")
        if not (0 <= span["char_start"] < span["char_end"]):
            failures.append(f"{span['evidence_id']}: invalid span")
        if not span["critical_strings"]:
            failures.append(f"{span['evidence_id']}: no critical strings")
        stray = [s for s in span["critical_strings"]
                 if not contains_claim_string(body, s)]
        if stray:
            failures.append(f"{span['evidence_id']}: strings outside this span: {stray}")
        verdict = evaluate_span(body, record)
        if verdict["status"] == CRITICAL:
            failures.append(
                f"{span['evidence_id']}: critical anaphora — {verdict['finding']}")
        elif verdict["status"] == NONCRITICAL:
            flags.append(f"{span['evidence_id']}: noncritical anaphora — "
                         f"{verdict['finding']}")
        if span["evidence_char_length"] > EVIDENCE_HARD_CAP:
            failures.append(f"{span['evidence_id']}: over the {EVIDENCE_HARD_CAP} cap")
        elif span["evidence_char_length"] > EVIDENCE_SOFT_CAP:
            flags.append(f"{span['evidence_id']}: {span['evidence_char_length']} chars, "
                         f"over the {EVIDENCE_SOFT_CAP} soft cap")
    if not (record["question"] and record["answer"] and record["atomic_claims"]):
        failures.append("question, answer or claims missing")
    if "[REVIEWER TO WRITE]" in record["question"]:
        failures.append("placeholder question")
    # §Fix B: a string property, so it belongs in the structural pass.
    for field in ("question", "answer"):
        if has_markdown_link(record[field]):
            failures.append(f"markdown link plumbing survived into the {field}")
    if not record["retrieval_was_not_run"]:
        failures.append("retrieval leakage")
    if record["reasoning_type"] == "genuine_multi_hop":
        if len(spans) < 2:
            failures.append("multi-hop with fewer than two spans")
        if not record.get("requires_all_evidence"):
            failures.append("multi-hop without requires_all_evidence")
        if record.get("multi_hop_composition_check") != "PASS":
            failures.append("multi-hop composition check did not pass")
    return failures, flags


READY = "READY_FOR_INDEPENDENT_REVIEW"
REPAIR = "NEEDS_INTERNAL_REPAIR"
DROP = "DROP"
_GENERIC_IDENTIFIERS = frozenset({
    "type", "types", "name", "id", "url", "path", "content", "text", "value", "data",
    "model", "role", "status", "error", "message", "input", "output", "config",
    "options", "timeout", "timezone", "headers", "metadata", "context", "result",
})
_SUBJECT_QUESTION = re.compile(r"^(?:What|Which) (?:does|is|must|are|bound)\b",
                               re.IGNORECASE)
_PREPOSITIONS = frozenset({"by", "for", "in", "with", "on", "of", "to", "from", "into",
                           "across", "over", "under", "via", "through", "between"})
_COMPARATIVE = re.compile(r"\b(?:a different|another|the other)\b", re.IGNORECASE)
_CODE_SHAPED = re.compile(r"^\s*(?:[\w.\[\]\"']+\s*[=:]\s*\S|[\]\})],?\s*$|>>>|\$ )",
                          re.MULTILINE)
#: §16. A reader's wish is not a system state.
_READER_INTENT = re.compile(
    r"\b(?:you|we|i)\s+(?:want|wish|need|would like|prefer|intend|decide|choose)\b",
    re.IGNORECASE)
#: §9. "What type is X?" and "Is X optional?" are facts nobody operates on.
_LOW_VALUE_LOOKUP = re.compile(
    r"^(?:what type (?:is|does)|is\s+`[^`]+`\s+optional|"
    r"what is the (?:type|default type) of)\b", re.IGNORECASE)


def semantic_review(record: dict, suspicious: set[str]) -> tuple[str, list[str],
                                                                 list[dict]]:
    """§24: read each candidate against its own evidence before exporting it.

    Authoring self-review, not verification. It repairs what it can as a numbered
    revision that keeps the original, and drops what it cannot repair honestly.
    """
    findings: list[str] = []
    repairs: list[dict] = []
    spans = record["expected_evidence"]
    evidence = " \n".join(s["evidence_text"] for s in spans)

    subject = next(iter(re.findall(r"`([^`]+)`", record["question"])), None)
    if subject and subject.lower() in _GENERIC_IDENTIFIERS:
        findings.append(
            f"GENERIC_IDENTIFIER: `{subject}` names something that exists in many APIs, "
            "and the question does not say which one")
        return DROP, findings, repairs

    # §Fix A — asked of every span, which is the whole change.
    scope = scoping.evaluate(record)
    if scope["status"] == scoping.NEEDS_SCOPE:
        findings.append("BARE_DEFINITION_SCOPE: " + "; ".join(scope["findings"]))
        return DROP, findings, repairs

    # §Fix D — the relation has a direction and the record now states both sides of it.
    # §27 requires both triples on every exported candidate, so a record whose triple
    # cannot be read out of its own evidence does not leave. Dropping it here is the
    # honest outcome; exporting it with empty fields would be the schema lying.
    if not record.get("question_subject") or not record.get("source_subject"):
        findings.append(
            "NO_TRIPLE: the candidate cannot state its subject and relation from its "
            "own evidence, so the direction check has nothing to compare")
        return DROP, findings, repairs

    verdict = relations.evaluate(record)
    if verdict["status"] == relations.REVERSED:
        findings.append(f"RELATION_DIRECTION: {verdict['finding']}")
        return DROP, findings, repairs
    if verdict["status"] == relations.SUBJECT_MISMATCH:
        findings.append(f"SUBJECT_MISMATCH: {verdict['finding']}")
        return DROP, findings, repairs

    # §15 — the question's form has to match the evidence's.
    form = question_form(record["question"], evidence)
    if form["status"] != "OK":
        findings.append(f"{form['status']}: {form['finding']}")
        return DROP, findings, repairs

    if _READER_INTENT.search(record["question"]):
        findings.append("READER_INTENT: the question is conditioned on what a reader "
                        "wants rather than on a documented state")
        return DROP, findings, repairs

    if _LOW_VALUE_LOOKUP.match(record["question"]):
        findings.append("LOW_VALUE_LOOKUP: a type or optionality question with no "
                        "operational consequence")
        return DROP, findings, repairs

    # §Fix C — a claim may not lean on a heading the audit calls prose.
    for span in spans:
        if any(part in suspicious for part in span["section_path"]):
            findings.append(
                f"SUSPICIOUS_SECTION_PATH: {span['evidence_id']}'s section_path "
                "contains a heading the parser audit judged to be prose; the span has "
                "to carry its own scope")
            if not any(contains_claim_string(span["evidence_text"], s)
                       for s in span["critical_strings"]):
                return DROP, findings, repairs

    if subject and _SUBJECT_QUESTION.match(record["question"]):
        position = evidence.find(f"`{subject}`")
        if position > 0:
            preceding = evidence[:position].strip().split()
            if preceding and preceding[-1].lower().strip(",;:") in _PREPOSITIONS:
                findings.append(
                    f"QUESTION_SCOPE: the question makes `{subject}` the subject, but "
                    f"the evidence has it after {preceding[-1]!r}")
                return DROP, findings, repairs

    if DANGLING_REFERENCE.search(record["answer"]):
        findings.append("CLAIM_SCOPE: the answer points outside its evidence with a "
                        "demonstrative")
        return DROP, findings, repairs

    if _COMPARATIVE.search(record["question"]) and not _COMPARATIVE.search(evidence):
        findings.append("COMPARATIVE_ANAPHORA: the question compares against something "
                        "the evidence does not name")
        return DROP, findings, repairs

    if _CODE_SHAPED.search(evidence):
        findings.append("CODE_EXAMPLE: the evidence looks like a sample rather than a "
                        "statement of a rule")
        return DROP, findings, repairs

    # §11 — two things must actually interact.
    if record["reasoning_type"] == "configuration_interaction":
        named = [s for s in record["critical_strings"] if f"`{s}`" in evidence]
        if len(named) < 2:
            findings.append(
                "CATEGORY: labelled configuration_interaction but the evidence names "
                "fewer than two settings, and the question was written for a relation "
                "the evidence does not state")
            return DROP, findings, repairs

    # §12 — ambiguity needs two readings that actually differ.
    if record["reasoning_type"] == "ambiguity_disambiguation":
        readings = record.get("candidate_interpretations") or []
        if len(readings) < 2 or len({r["meaning"] for r in readings}) < 2:
            findings.append("NOT_AMBIGUITY: the readings do not differ")
            return DROP, findings, repairs

    # §13 — a schema description is not a lifecycle statement.
    if record["reasoning_type"] == "lifecycle_compatibility_migration":
        from rag_v1.gold.mining_v5 import LIFECYCLE_PATTERNS
        if not any(pattern.search(evidence) for pattern, _ in LIFECYCLE_PATTERNS):
            findings.append("NOT_A_LIFECYCLE_STATEMENT: the evidence does not describe "
                            "support status, deprecation or migration")
            return DROP, findings, repairs

    if len(record["question"]) < 25:
        findings.append("QUESTION_FORM: too short to carry its conditions")
        return DROP, findings, repairs

    return (REPAIR if repairs else READY), findings, repairs


def interleave_providers(pool: list[dict]) -> list[dict]:
    from itertools import zip_longest
    groups: dict[str, list[dict]] = {}
    for candidate in pool:
        groups.setdefault(candidate["provider"], []).append(candidate)
    ordered: list[dict] = []
    for row in zip_longest(*(groups[p] for p in sorted(groups))):
        ordered += [c for c in row if c is not None]
    return ordered


def question_opening(question: str) -> str:
    return " ".join(question.lower().split()[:3])


def select(pool: list[dict], size: int) -> tuple[list[dict], Counter]:
    """Fill the reasoning floors, then balance providers, then stop at the ceilings."""
    chosen: list[dict] = []
    reasons: Counter = Counter()
    counts: Counter = Counter()
    documents: Counter = Counter()
    openings: Counter = Counter()
    providers: Counter = Counter({p: 0 for p in PROVIDER_TARGET})
    blocked: dict[str, set[int]] = {}
    overflow_open = {"value": False}

    def note(reason: str, candidate: dict) -> None:
        if id(candidate) not in blocked.setdefault(reason, set()):
            blocked[reason].add(id(candidate))
            reasons[reason] += 1

    def admissible(candidate: dict) -> bool:
        _, ceiling = REASONING_TARGET.get(candidate["reasoning_type"], (0, size))
        if overflow_open["value"]:
            ceiling += OVERFLOW_CAP.get(candidate["reasoning_type"], 0)
        if counts[candidate["reasoning_type"]] >= ceiling:
            note("reasoning_type_ceiling", candidate)
            return False
        if documents[candidate["document_title"]] >= MAX_PER_DOCUMENT:
            note("document_concentration", candidate)
            return False
        _, provider_ceiling = PROVIDER_TARGET.get(candidate["provider"], (0, size))
        if providers[candidate["provider"]] >= provider_ceiling:
            note("provider_ceiling", candidate)
            return False
        if openings[question_opening(candidate["question"])] >= MAX_PER_QUESTION_OPENING:
            note("question_template_repetition", candidate)
            return False
        return True

    def take(predicate, quota: int) -> None:
        while len(chosen) < size and sum(1 for c in chosen if predicate(c)) < quota:
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
            pick["selected_by"] = "overflow" if overflow_open["value"] else "target"
            counts[pick["reasoning_type"]] += 1
            documents[pick["document_title"]] += 1
            providers[pick["provider"]] += 1
            openings[question_opening(pick["question"])] += 1

    for reasoning, (floor, _) in REASONING_TARGET.items():
        if floor:
            take(lambda c, k=reasoning: c["reasoning_type"] == k, floor)
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

    if len(chosen) < size:
        reasons["short_of_target_before_overflow"] = size - len(chosen)
        overflow_open["value"] = True
        take(lambda c: True, size)
    return chosen[:size], reasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=TARGET_SIZE)
    parser.add_argument("--out-dir", default="evals/review")
    parser.add_argument("--report-dir", default="experiments/GOLD-001")
    args = parser.parse_args()

    state = verify_state()
    frozen = verify_frozen_systems()
    suspicious = suspicious_headings()
    with connect() as conn, conn.cursor() as cur:
        docs = load_docs(cur)
    for doc in docs:
        doc["sections"] = _sections_from_markdown(doc["text"])
    docs_by_version = {d["version_id"]: d for d in docs}

    removed: Counter = Counter()
    questions, prior_spans, excluded, prior_texts = prior_material()

    def allowed(fact: dict) -> bool:
        version, start, end = fact["version_id"], fact["char_start"], fact["char_end"]
        if any(v == version and start < b_end and b_start < end
               for v, b_start, b_end in excluded):
            removed["excluded_known_failure_case"] += 1
            return False
        return True

    # ---- mining. One lane: §7 forbids another multi-hop search. -----------------
    from rag_v1.gold.factmining import mine_bridge_facts

    conditional_facts: list[dict] = []
    templated: list[dict] = []
    interactions: list[dict] = []
    constraints: list[dict] = []
    lifecycles: list[dict] = []
    single_doc_ambiguity: list[tuple] = []
    for doc in docs:
        conditional_facts += mine_bridge_facts(doc)
        templated += mine_prose(doc, limit=20)
        templated += mine_row_facts(doc, limit=10)
        templated += mine_definition_bullets(doc, limit=10)
        interactions += mine_interactions(doc, limit=60)
        constraints += mine_constraints(doc, limit=60)
        lifecycles += mine_lifecycle(doc, limit=50)
        for finding in find_ambiguous_fields(doc, limit=3):
            single_doc_ambiguity.append((doc, finding))
    cross_component = find_cross_component_ambiguity(docs, limit=16)
    mined = (len(conditional_facts) + len(templated) + len(interactions)
             + len(constraints) + len(lifecycles) + len(single_doc_ambiguity)
             + len(cross_component))

    # The census behind this batch's central claim: the corpus is not exhausted, the
    # authoring is. Counted here so a report reads it from the record rather than from
    # a number somebody typed into a document once.
    every_fact = (conditional_facts + templated + interactions + constraints
                  + lifecycles)
    distinct_texts = {" ".join(f["evidence_text"].split()) for f in every_fact}
    unspent_texts = {
        t for t in distinct_texts if t not in prior_texts} - {
        " ".join(f["evidence_text"].split()) for f in every_fact
        if (f["version_id"], f["char_start"], f["char_end"]) in prior_spans}
    census = {
        "facts_mined": len(every_fact),
        "distinct_evidence_texts": len(distinct_texts),
        "unspent_distinct_texts": len(unspent_texts),
        "note": ("Distinct evidence texts no closed batch has used. The shortfall in "
                 "this batch is not a shortage of material — it is a shortage of "
                 "builders that can turn this material into a question without "
                 "paraphrasing it."),
    }

    conditional_facts = [f for f in conditional_facts if allowed(f)]
    templated = [f for f in templated if allowed(f)]
    interactions = [f for f in interactions if allowed(f)]
    constraints = [f for f in constraints if allowed(f)]
    lifecycles = [f for f in lifecycles if allowed(f)]

    pool: list[dict] = []

    def add(fact: dict, built: dict | None, confidence: str = "medium") -> None:
        if built is None:
            removed["unbuildable"] += 1
            return
        doc = docs_by_version[fact["version_id"]]
        spans = [evidence_record(1, doc, fact["char_start"], fact["char_end"],
                                 fact["critical_strings"])]
        pool.append(base_record(doc, spans, built, confidence))

    for fact in conditional_facts:
        add(fact, build_conditional(fact))
    for fact in interactions:
        add(fact, build_interaction(fact), "high")
    for fact in constraints:
        add(fact, build_constraint(fact), "high")
    for fact in lifecycles:
        add(fact, build_lifecycle(fact))
    # §9/§10: the predicate lane. Batches 001-005 spent what the conditional and
    # template builders could reach; these are the plain statements left behind.
    claimed = {(f["version_id"], f["char_start"], f["char_end"])
               for f in interactions + constraints + lifecycles}
    for fact in conditional_facts:
        if (fact["version_id"], fact["char_start"], fact["char_end"]) in claimed:
            continue
        if build_conditional(fact) is not None:
            continue
        add(fact, build_predicate_fact(fact))

    for fact in templated:
        add(fact, {
            "reasoning_type": CATEGORY_TO_REASONING.get(
                fact["proposed_category"], "exact_lookup"),
            "secondary_category": fact.get("evidence_kind"),
            "question": fact["proposed_question"],
            "answer": fact["proposed_answer"],
            "atomic_claims": fact["proposed_atomic_claims"],
            "question_subject": (f"`{fact['critical_strings'][0]}`"
                                 if fact.get("critical_strings") else None),
            "question_relation": fact.get("evidence_kind"),
            "question_object": None,
        }, fact.get("generator_confidence", "medium"))

    for doc, finding in single_doc_ambiguity:
        readings = finding["candidate_interpretations"]
        if len(readings) < 2:
            continue
        chosen_reading, other = readings[0], readings[1]
        term = finding["ambiguous_term"]
        spans = [evidence_record(i, doc, r["char_start"], r["char_end"],
                                 [term, r["meaning"][:60]])
                 for i, r in enumerate((chosen_reading, other), start=1)]
        claims = [f"In `{r['scope']}`, `{term}` is: {sentence(r['meaning'])}"
                  for r in (chosen_reading, other)]
        built = {
            "reasoning_type": "ambiguity_disambiguation",
            "secondary_category": "same_document_scope",
            "question": (f"In a `{chosen_reading['scope']}`, what does the `{term}` "
                         f"field contain, and how does that differ from "
                         f"`{other['scope']}`?"),
            "answer": " ".join(claims),
            "atomic_claims": claims,
            "ambiguous_term": term,
            "candidate_interpretations": [
                {"scope": r["scope"], "meaning": r["meaning"]} for r in readings],
            "required_scope_to_answer": finding["required_scope_to_answer"],
            "needs_human_interpretation": True,
            "question_subject": f"`{term}`",
            "question_relation": "means_differently_by_scope",
            "question_object": f"`{chosen_reading['scope']}` vs `{other['scope']}`",
        }
        pool.append(base_record(doc, spans, built, "medium"))

    for index, finding in enumerate(cross_component):
        builder = (build_cross_component_ambiguity if index % 2 == 0
                   else build_comparison)
        built = builder(finding)
        if built is None:
            continue
        first, second = finding["readings"]
        built.setdefault("question_subject", f"`{finding['ambiguous_term']}`")
        built.setdefault("question_relation", "means_differently_by_component")
        built.setdefault("question_object", None)
        spans = [
            evidence_record(1, first["doc"], first["char_start"], first["char_end"],
                            [finding["ambiguous_term"]]),
            evidence_record(2, second["doc"], second["char_start"], second["char_end"],
                            [finding["ambiguous_term"]]),
        ]
        pool.append(base_record(first["doc"], spans, built, "medium"))

    # ---- duplicate control, precheck, self-review -------------------------------
    kept: list[dict] = []
    seen_questions: set[str] = set()
    seen_spans: set[tuple] = set()
    seen_texts: set[str] = set()
    seen_relations: set[tuple] = set()
    review_counts: Counter = Counter()
    dropped: list[dict] = []
    repaired: list[dict] = []
    gate_counts: Counter = Counter()

    for candidate in sorted(pool, key=lambda c: (
            c["version_id"], c["expected_evidence"][0]["char_start"])):
        key = normalise_question(candidate["question"])
        span_key = tuple(sorted((s["version_id"], s["char_start"], s["char_end"])
                                for s in candidate["expected_evidence"]))
        text_key = " \n".join(" ".join(s["evidence_text"].split())
                              for s in candidate["expected_evidence"])
        if key in questions or key in seen_questions:
            removed["duplicate_question"] += 1
            continue
        if any(k in prior_spans or k in seen_spans for k in span_key):
            removed["duplicate_evidence"] += 1
            continue
        if text_key in prior_texts or text_key in seen_texts:
            removed["duplicate_evidence_text"] += 1
            continue
        # §22: batch 005 established that two adjacent siblings stating the same
        # relation are one benchmark case, not two. The relation and the document are
        # the key; the identifier is what differs and is exactly what should not earn a
        # second candidate.
        relation_key = (candidate["version_id"], candidate["reasoning_type"],
                        candidate.get("question_relation"),
                        tuple(candidate["expected_evidence"][0]["section_path"]))
        if relation_key in seen_relations:
            removed["adjacent_sibling_relation"] += 1
            continue

        failures, flags = precheck(candidate)
        candidate["precheck_failures"] = failures
        candidate["precheck_flags"] = flags
        candidate["precheck_holdout_ready"] = not failures
        if failures:
            bucket = ("blocking_anaphora" if any("anaphora" in f for f in failures)
                      else "markdown_link_in_question"
                      if any("markdown link" in f for f in failures)
                      else "missing_critical_strings"
                      if any("critical strings" in f or "strings outside" in f
                             for f in failures)
                      else "failed_precheck")
            removed[bucket] += 1
            continue

        status, findings, repairs = semantic_review(candidate, suspicious)
        candidate["internal_semantic_review_status"] = status
        candidate["internal_review_findings"] = findings
        candidate["generation_repairs"] = repairs
        review_counts[status] += 1
        for finding in findings:
            gate_counts[finding.split(":", 1)[0]] += 1
        if status == DROP:
            removed["dropped_by_semantic_review"] += 1
            dropped.append({"question": candidate["question"],
                            "reasoning_type": candidate["reasoning_type"],
                            "provider": candidate["provider"],
                            "findings": findings})
            continue
        if repairs:
            repaired.append({"question": candidate["question"], "repairs": repairs})
            for number, repair in enumerate(repairs, 1):
                candidate["revisions"].append({
                    "revision": number, "field": repair["field"],
                    "from": repair["from"], "to": repair["to"],
                    "author": "claude (generation self-review)",
                    "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "reason": repair["reason"]})

        seen_questions.add(key)
        seen_spans.update(span_key)
        seen_texts.add(text_key)
        seen_relations.add(relation_key)
        kept.append(candidate)

    eligible_by_reasoning = dict(Counter(c["reasoning_type"] for c in kept))
    eligible_by_provider = dict(Counter(c["provider"] for c in kept))
    chosen, selection_reasons = select(interleave_providers(kept), args.size)
    removed.update(selection_reasons)
    removed["not_selected_diversity"] = len(kept) - len(chosen)

    for position, candidate in enumerate(sorted(
            chosen, key=lambda c: (c["provider"], c["reasoning_type"],
                                   c["document_title"])), start=1):
        candidate["candidate_id"] = f"GOLD-B006-{position:02d}"
    chosen.sort(key=lambda c: c["candidate_id"])

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                         stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        commit = None

    lengths = sorted(s["evidence_char_length"]
                     for c in chosen for s in c["expected_evidence"])
    payload = {
        "batch": BATCH,
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "corpus_snapshot": SNAPSHOT,
        "starting_state": state,
        "frozen_systems": frozen,
        "preregistered_fixes_applied": PREREGISTERED_FIXES,
        "candidate_pool_size": mined,
        "corpus_census": census,
        "candidates": len(chosen),
        "target_size": args.size,
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
        "multi_document": sum(1 for c in chosen
                              if c["evidence_shape"] == "multi_document"),
        "complete_questions": sum(1 for c in chosen if c["question"]),
        "complete_answers": sum(1 for c in chosen if c["answer"]),
        "complete_claims": sum(1 for c in chosen if c["atomic_claims"]),
        "needs_human_interpretation": sum(1 for c in chosen
                                          if c["needs_human_interpretation"]),
        "precheck_holdout_ready": sum(1 for c in chosen
                                      if c["precheck_holdout_ready"]),
        "precheck_means": "STRUCTURAL ONLY — not semantic correctness, not independent "
                          "verification, not human approval, not holdout eligibility",
        "internal_review": {
            "counts": dict(review_counts),
            "gate_counts": dict(gate_counts.most_common()),
            "repaired": repaired,
            "dropped": dropped,
            "note": ("A generation self-review, not independent verification and not "
                     "human approval. Every candidate here is candidate_unverified."),
        },
        "selected_by": dict(Counter(c.get("selected_by", "target") for c in chosen)),
        "overflow_cap": OVERFLOW_CAP,
        "question_openings": dict(Counter(question_opening(c["question"])
                                          for c in chosen).most_common()),
        "evidence_length": {
            "spans": len(lengths),
            "mean": round(sum(lengths) / len(lengths), 1) if lengths else 0,
            "median": lengths[len(lengths) // 2] if lengths else 0,
            "max": max(lengths) if lengths else 0,
            "min": min(lengths) if lengths else 0,
            "over_soft_cap": sum(1 for n in lengths if n > EVIDENCE_SOFT_CAP),
        },
        "removed": dict(removed),
        "eligible_pool": {"candidates": len(kept),
                          "by_reasoning_type": eligible_by_reasoning,
                          "by_provider": eligible_by_provider},
        "multi_hop_search": {
            "ran": False,
            "reason": ("§7: batch 004 tested 559 bridge pairs and found 1 chain; batch "
                       "005 searched dependency-first and found the same one. The "
                       "corpus has been measured twice. No search was run here, and no "
                       "multi-span case was relabelled to raise the count."),
            "exported_chains": sum(1 for c in chosen
                                   if c["reasoning_type"] == "genuine_multi_hop"),
        },
        "targets": {"reasoning_type": REASONING_TARGET, "provider": PROVIDER_TARGET,
                    "size": args.size, "minimum_useful": MINIMUM_USEFUL,
                    "unique_documents": 20},
        "source_triple_derivations": dict(Counter(
            c["source_triple_derivation"] for c in chosen)),
        "heading_audit": HEADING_AUDIT,
        "suspicious_headings_known": len(suspicious),
        "verification_status": "candidate_unverified — nothing in this file is gold",
        "retrieval_was_not_run": True,
        "systems_executed": [],
        "records": chosen,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"gold_review_batch_{BATCH:03d}.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    payload["batch_sha256"] = hashlib.sha256(json_path.read_bytes()).hexdigest()
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    (out_dir / f"gold_review_batch_{BATCH:03d}.md").write_text(
        render(payload), encoding="utf-8")
    write_reports(payload, Path(args.report_dir))

    print(f"pool {mined} mined -> {len(kept)} eligible -> batch {BATCH:03d} with "
          f"{len(chosen)}")
    print("  provider  :", payload["by_provider"])
    print("  reasoning :", payload["by_reasoning_type"])
    print("  shape     :", payload["by_evidence_shape"])
    print("  documents :", payload["unique_documents"], payload["documents_by_provider"])
    print("  evidence  : mean", payload["evidence_length"]["mean"],
          "median", payload["evidence_length"]["median"],
          "max", payload["evidence_length"]["max"])
    print("  review    :", payload["internal_review"]["counts"])
    print("  gates     :", payload["internal_review"]["gate_counts"])
    print("  triples   :", payload["source_triple_derivations"])
    print("  removed   :", payload["removed"])
    if len(chosen) < MINIMUM_USEFUL:
        print(f"  NOTE: {len(chosen)} is below the {MINIMUM_USEFUL} this batch was "
              "expected to be useful at. Reported, not padded.")
    return 0


#: §5. What was implemented before a candidate was authored, and the case each one
#: comes from. Recorded on the batch so the report cannot claim a fix it did not run.
PREREGISTERED_FIXES = [
    {"id": "A", "fix": "bare-definition-bullet scope applied to every span",
     "module": "rag_v1.gold.scoping", "from_case": "GOLD-B005-01"},
    {"id": "B", "fix": "markdown links stripped from questions and answers",
     "module": "rag_v1.gold.normalisation.strip_markdown_links",
     "from_case": "GOLD-B005-15"},
    {"id": "C", "fix": "heading parser audited; section_path not trusted for scope",
     "module": "scripts/audit_heading_parser.py", "from_case": "GOLD-B005-11"},
    {"id": "D", "fix": "source and question triples recorded and compared",
     "module": "rag_v1.gold.relations", "from_case": "GOLD-B005-10"},
]


def code_span(text: str) -> str:
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def render(payload: dict) -> str:
    lines: list[str] = [
        f"# Gold review batch {payload['batch']:03d}",
        "",
        (f"**{payload['candidates']} candidates · corpus snapshot "
         f"`{payload['corpus_snapshot']}` · generated {payload['generated_at']}**"),
        "",
        ("Nothing in this file is ground truth. Every candidate is "
         "`candidate_unverified`. The evidence is quoted verbatim from the frozen "
         "corpus and is authoritative for this review — **do not consult live "
         "documentation**, which may have changed since the snapshot."),
        "",
        ("Three things to know before reading. First, `precheck_holdout_ready` is "
         "**structural only**: batch 005 shipped 19 of 19 precheck-ready and its review "
         "still repaired seven and rejected four. Second, the "
         "`internal_semantic_review_status` on each candidate is a **generation** "
         "self-review — the author reading its own output — and is not verification. "
         "Third, `section_path` is metadata, not evidence: the heading parser audit "
         "found headings that are ordinary prose, so a claim's scope has to be inside "
         "the span."),
        "",
        (f"Provider {payload['by_provider']} · reasoning {payload['by_reasoning_type']} "
         f"· {payload['unique_documents']} distinct documents · median span "
         f"{payload['evidence_length']['median']} characters."),
        "",
        "| id | provider | reasoning type | shape | chars | question |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for record in payload["records"]:
        question = record["question"]
        short = question if len(question) <= 68 else question[:65] + "…"
        lines.append(f"| `{record['candidate_id'][-2:]}` | {record['provider']} | "
                     f"{record['reasoning_type']} | {record['evidence_shape']} | "
                     f"{record['evidence_char_length']} | {short} |")
    lines += ["", "---", ""]

    for record in payload["records"]:
        lines += [
            f"## {record['candidate_id']}",
            "",
            f"- **provider**: {record['provider']}",
            f"- **document**: {record['document_title']}",
            (f"- **section** (metadata, not scope): "
             f"{' › '.join(record['section_path'])}"),
            (f"- **reasoning type**: `{record['reasoning_type']}`"
             + (f" · **secondary**: `{record['secondary_category']}`"
                if record.get("secondary_category") else "")),
            (f"- **evidence shape**: `{record['evidence_shape']}` · "
             f"**requires all evidence**: {record['requires_all_evidence']}"),
            (f"- **generation self-review**: "
             f"{record['internal_semantic_review_status']} · "
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
        lines += [
            "",
            "**Subject and relation** — check the direction against the evidence below.",
            "",
            "| | subject | relation | object |",
            "| --- | --- | --- | --- |",
            (f"| source | {record['source_subject'] or '—'} | "
             f"`{record['source_relation'] or '—'}` | "
             f"{record['source_object'] or '—'} |"),
            (f"| question | {record['question_subject'] or '—'} | "
             f"`{record['question_relation'] or '—'}` | "
             f"{record['question_object'] or '—'} |"),
            "",
            f"*Source triple read by: {record['source_triple_derivation']}.*",
            "",
        ]
        if record.get("ambiguous_term"):
            lines += ["**Ambiguity**", "",
                      f"- **term**: {code_span(record['ambiguous_term'])}"]
            lines += [f"  - in `{r['scope']}`: {r['meaning']}"
                      for r in record["candidate_interpretations"]]
            lines += [(f"- **scope needed to answer**: "
                      f"{record['required_scope_to_answer']}"), ""]

        lines += ["**Exact evidence**", ""]
        for span in record["expected_evidence"]:
            lines += [
                (f"`{span['evidence_id']}` · `{span['version_id']}` "
                 f"{span['char_start']}–{span['char_end']} "
                 f"({span['evidence_char_length']} chars)"),
                "", "```", span["evidence_text"], "```",
                ("**critical strings**: "
                 + ", ".join(code_span(s) for s in span["critical_strings"])),
                "",
            ]
        lines += ["**Claim → evidence**", ""]
        lines += [f"  {i}. {m['claim'][:100]}{'…' if len(m['claim']) > 100 else ''} → "
                  f"`{m['evidence_id']}`"
                  for i, m in enumerate(record["claim_evidence_map"], 1)]
        if record.get("generation_repairs"):
            lines += ["", "**Generation repairs**", ""]
            lines += [f"  - `{r['field']}`: {r['from']} → {r['to']} ({r['reason']})"
                      for r in record["generation_repairs"]]
        if record.get("internal_review_findings"):
            lines += ["", "**Self-review findings kept on the record**", ""]
            lines += [f"  - {f}" for f in record["internal_review_findings"]]
        if record.get("precheck_flags"):
            lines += ["", "**Flags for the reviewer**", ""]
            lines += [f"  - {flag}" for flag in record["precheck_flags"]]
        lines += ["", ("<details><summary>surrounding context (review only — not part "
                       "of the gold evidence)</summary>"), "", "```",
                  f"…{record['context_before'][-400:].strip()}", "  ⟦EVIDENCE⟧",
                  f"{record['context_after'][:400].strip()}…", "```", "", "</details>",
                  "", "---", ""]
    return "\n".join(lines)


def check_consistency(payload: dict) -> None:
    """Refuse to write a report that disagrees with the batch it describes."""
    problems = []
    records = payload["records"]
    if sum(payload["by_reasoning_type"].values()) != len(records):
        problems.append("the reasoning-type counts do not sum to the candidate count")
    if sum(payload["by_provider"].values()) != len(records):
        problems.append("the provider counts do not sum to the candidate count")
    if payload["candidates"] != len(records):
        problems.append("the candidate count does not match the records")
    if any(r["verification_status"] != "candidate_unverified" for r in records):
        problems.append("a record claims a verification it does not have")
    if not payload["retrieval_was_not_run"] or payload["systems_executed"]:
        problems.append("the batch records a retrieval run")
    if payload["multi_hop_search"]["ran"]:
        problems.append("§7 forbids a multi-hop search in this batch")
    missing = [r["candidate_id"] for r in records
               if not r.get("question_subject") or not r.get("source_subject")]
    if missing:
        problems.append("§Fix D: these records carry no subject triple — "
                        + ", ".join(missing))
    unscoped = [r["candidate_id"] for r in records
                if scoping.evaluate(r)["status"] == scoping.NEEDS_SCOPE]
    if unscoped:
        problems.append("§Fix A: these records have a bare-bullet span — "
                        + ", ".join(unscoped))
    linked = [r["candidate_id"] for r in records if has_markdown_link(r["question"])]
    if linked:
        problems.append("§Fix B: markdown link plumbing in a question — "
                        + ", ".join(linked))
    if problems:
        raise SystemExit("refusing to write the batch:\n  " + "\n  ".join(problems))


def render_report(payload: dict) -> str:
    review = payload["internal_review"]
    removed = payload["removed"]
    targets = payload["targets"]["reasoning_type"]
    length = payload["evidence_length"]

    def target_rows() -> str:
        rows = []
        for reasoning, (floor, ceiling) in targets.items():
            got = payload["by_reasoning_type"].get(reasoning, 0)
            met = "yes" if floor <= got <= ceiling else ("over" if got > ceiling
                                                         else "under")
            rows.append(f"| `{reasoning}` | {got} | {floor}–{ceiling} | {met} | "
                        f"{payload['eligible_pool']['by_reasoning_type'].get(reasoning, 0)} |")
        return "\n".join(rows)

    def provider_rows() -> str:
        rows = []
        for provider, (floor, ceiling) in payload["targets"]["provider"].items():
            got = payload["by_provider"].get(provider, 0)
            met = "yes" if floor <= got <= ceiling else ("over" if got > ceiling
                                                         else "under")
            rows.append(f"| {provider} | {got} | {floor}–{ceiling} | {met} | "
                        f"{payload['documents_by_provider'].get(provider, 0)} |")
        return "\n".join(rows)

    gate_rows = "\n".join(f"| `{gate}` | {count} |"
                          for gate, count in review["gate_counts"].items())
    removed_rows = "\n".join(f"| {reason.replace('_', ' ')} | {count} |"
                             for reason, count in sorted(removed.items(),
                                                         key=lambda kv: -kv[1]))
    fix_rows = "\n".join(
        f"| **{f['id']}** | {f['fix']} | `{f['module']}` | `{f['from_case']}` |"
        for f in payload["preregistered_fixes_applied"])
    dropped_rows = "\n".join(
        f"| {d['reasoning_type']} | {d['findings'][0].split(':', 1)[0]} | "
        f"{d['question'][:70]}{'…' if len(d['question']) > 70 else ''} |"
        for d in review["dropped"][:30])
    state = payload["starting_state"]
    short = payload["candidates"] < payload["target_size"]

    return "\n".join([
        f"# GOLD-001 — batch {payload['batch']:03d} generation report",
        "",
        (f"**{payload['candidates']} candidates** from a mined pool of "
         f"{payload['candidate_pool_size']}, across {payload['unique_documents']} "
         "distinct documents. Nothing is verified; nothing is gold."),
        "",
        ((f"The target was {payload['target_size']} and the batch exported "
          f"{payload['candidates']}. "
          + ("The shortfall is reported, not padded: what was available after the "
             "gates below is what is here."
             if short else ""))
         if short else
         f"The target was {payload['target_size']} and the batch met it."),
        "",
        "## The four preregistered fixes, applied before anything was authored",
        "",
        "| | fix | implemented in | from |",
        "| --- | --- | --- | --- |",
        fix_rows,
        "",
        ("Each was recorded in batch 005's closure as a preregistration input, and each "
         "has a regression test built from the candidate that motivated it "
         "(`tests/test_gold001_b006_fixes.py`). Batch 005's own artifacts are "
         "unchanged — the fixes are forward-looking, which is the point of recording "
         "them rather than patching."),
        "",
        "## Starting state",
        "",
        (f"Read from `{state['read_from']}` before generating: "
         f"**{state['human_verified']} human_verified**, "
         f"**{state['holdout_eligible']} holdout_eligible**, "
         f"{state['human_rejected']} rejected, {state['genuine_multi_hop']} genuine "
         f"multi-hop, across {state['candidates']} historical candidates. Holdout "
         f"frozen: {str(state['holdout_frozen']).lower()}."),
        "",
        "## Composition",
        "",
        "| | |",
        "| --- | --- |",
        f"| provider | {payload['by_provider']} |",
        f"| documents by provider | {payload['documents_by_provider']} |",
        f"| reasoning type | {payload['by_reasoning_type']} |",
        f"| evidence shape | {payload['by_evidence_shape']} |",
        f"| confidence | {payload['by_confidence']} |",
        f"| distinct documents | {payload['unique_documents']} |",
        f"| genuine multi-hop | {payload['genuine_multi_hop']} |",
        (f"| complete question / answer / claims | "
         f"{payload['complete_questions']} / {payload['complete_answers']} / "
         f"{payload['complete_claims']} of {payload['candidates']} |"),
        (f"| needing reviewer judgement | {payload['needs_human_interpretation']} of "
         f"{payload['candidates']} |"),
        (f"| precheck holdout-ready | {payload['precheck_holdout_ready']} of "
         f"{payload['candidates']} |"),
        "",
        f"**`precheck_holdout_ready` means: {payload['precheck_means']}.**",
        "",
        "### Reasoning types against target",
        "",
        "| reasoning type | in batch | target | met | eligible available |",
        "| --- | --- | --- | --- | --- |",
        target_rows(),
        "",
        "### Providers against target",
        "",
        "| provider | in batch | target | met | documents |",
        "| --- | --- | --- | --- | --- |",
        provider_rows(),
        "",
        "## The self-review",
        "",
        (f"{sum(review['counts'].values())} candidates reached the semantic "
         f"self-review: **{review['counts'].get('READY_FOR_INDEPENDENT_REVIEW', 0)}** "
         f"were ready, **{review['counts'].get('NEEDS_INTERNAL_REPAIR', 0)}** were "
         f"repaired, **{review['counts'].get('DROP', 0)}** were dropped. This is "
         "authoring, not verification."),
        "",
        "| gate that fired | candidates |",
        "| --- | --- |",
        gate_rows or "| — | 0 |",
        "",
        "### What was dropped and why",
        "",
        "| reasoning type | gate | question |",
        "| --- | --- | --- |",
        dropped_rows or "| — | — | nothing was dropped |",
        "",
        (f"{len(review['dropped'])} drops in total"
         + (f"; the first {min(30, len(review['dropped']))} are listed."
            if len(review["dropped"]) > 30 else ".")
         + " They are recorded rather than regenerated away: what the miner gets wrong "
           "is part of what this batch measures."),
        "",
        "## Subject and relation triples",
        "",
        (f"Every candidate carries both triples. How the source triple was read: "
         f"{payload['source_triple_derivations']}. A *named relation* is one this "
         "project has a directed pattern for, and is the stronger reading; a *generic "
         "predicate split* records the sentence's two halves around its verb and is "
         "weaker evidence about direction. Both are shown to the reviewer."),
        "",
        "## Multi-hop",
        "",
        (f"**No multi-hop search was run.** {payload['multi_hop_search']['reason']} "
         f"Exported chains: {payload['multi_hop_search']['exported_chains']}."),
        "",
        "## Question openings",
        "",
        "| opening | candidates |",
        "| --- | --- |",
        "\n".join(f"| \"{opening}…\" | {count} |"
                  for opening, count in payload["question_openings"].items()),
        "",
        (f"No opening is allowed past {MAX_PER_QUESTION_OPENING} candidates. A batch "
         "that measures one template measures the template."),
        "",
        "## Evidence size",
        "",
        (f"Across {length['spans']} spans: mean {length['mean']}, median "
         f"{length['median']}, min {length['min']}, max {length['max']} characters. "
         f"{length['over_soft_cap']} over the {EVIDENCE_SOFT_CAP}-character soft cap, "
         f"none over the {EVIDENCE_HARD_CAP} hard cap."),
        "",
        "## Removed before export",
        "",
        "| reason | count |",
        "| --- | --- |",
        removed_rows,
        "",
        "## Retrieval",
        "",
        ("No retrieval system was run against any batch-006 candidate at any point. "
         "SYSTEM-A and SYSTEM-B remain frozen and were not executed; their config "
         "hashes were verified before generation began. No candidate was selected, "
         "ordered or worded because of what any system does with it, and no difficulty "
         "label in this batch derives from retrieval behaviour."),
        "",
    ])


def target_verdict(confirmed: int, exported: int, by_batch: list[dict]) -> list[str]:
    """Say whether this batch can reach 100, from the batch's own size.

    Written as a computation because the first draft of this section asserted "either
    crosses 100" — true for the 28 the batch was aiming at and false for the 9 it
    produced. A sentence that is only true at the number you hoped for is the failure
    mode this project keeps finding in its own reports.
    """
    rates = [b["human_verified"] / (b["human_verified"] + b["human_rejected"])
             for b in by_batch if b["human_verified"] + b["human_rejected"]]
    worst, best = min(rates), max(rates)
    low, high = confirmed + int(exported * worst), confirmed + exported
    shortfall = 100 - high
    lines = [
        (f"The project needs **≥100** confirmed holdout-eligible cases and holds "
         f"**{confirmed}**. Batch 006 exports **{exported}**. At the {worst:.0%} "
         f"acceptance rate of the weakest closed batch that would reach {low}; at "
         f"{best:.0%} it would reach {high}."),
        "",
    ]
    if shortfall > 0:
        lines += [
            (f"**Neither crosses 100.** Even if every batch-006 candidate were "
             f"approved, the project would be {shortfall} short. This batch does not "
             "get GOLD-001 to its minimum, and no approval decision should be taken as "
             "though it might — the gap has to close through another batch, a wider "
             "corpus, or a revised target, not through a lower bar here."),
            "",
        ]
    elif low < 100 <= high:
        lines += [
            ("**Whether it crosses 100 depends on the acceptance rate**, which is not "
             "something to manage toward. The bar does not move because the count is "
             "close."),
            "",
        ]
    else:
        lines += [
            ("Both ends of that range cross 100. That is not a reason to approve a "
             "candidate that should not be approved."),
            "",
        ]
    return lines


def render_coverage(payload: dict) -> str:
    state = payload["starting_state"]
    exported = payload["candidates"]
    confirmed = state["holdout_eligible"]
    return "\n".join([
        "# GOLD-001 — coverage status after batch 006 generation",
        "",
        (f"**Confirmed: {state['human_verified']} human_verified, "
         f"{state['holdout_eligible']} holdout_eligible, "
         f"{state['human_rejected']} rejected, {state['genuine_multi_hop']} genuine "
         "multi-hop.** Batch 006 adds nothing to those numbers yet."),
        "",
        f"Read from `{state['read_from']}`.",
        "",
        "## Confirmed — batches 001 to 005",
        "",
        "| batch | human_verified | holdout_eligible | rejected | genuine multi-hop |",
        "| --- | --- | --- | --- | --- |",
        "\n".join(f"| {b['batch']:03d} | {b['human_verified']} | "
                  f"{b['holdout_eligible']} | {b['human_rejected']} | "
                  f"{b['genuine_multi_hop']} |" for b in state["by_batch"]),
        (f"| **all** | **{state['human_verified']}** | "
         f"**{state['holdout_eligible']}** | **{state['human_rejected']}** | "
         f"**{state['genuine_multi_hop']}** |"),
        "",
        "## Projected — only if every batch-006 candidate were approved",
        "",
        "| | confirmed | if all of batch 006 were approved |",
        "| --- | --- | --- |",
        (f"| `human_verified` | {state['human_verified']} | "
         f"{state['human_verified'] + exported} |"),
        (f"| `holdout_eligible` | {state['holdout_eligible']} | "
         f"{state['holdout_eligible'] + exported} |"),
        f"| candidates | {state['candidates']} | {state['candidates'] + exported} |",
        "",
        ("**The right-hand column is not a result.** It is what the arithmetic would "
         "give if an independent review and an owner approved all "
         f"{exported} candidates, which has never happened: acceptance across the five "
         "closed batches has run between 79% and 100%. Nothing in batch 006 is "
         "`human_verified`, and no batch-006 candidate is counted as confirmed "
         "anywhere in this project's records."),
        "",
        "## Against the 100-case target",
        "",
        *target_verdict(confirmed, exported, state["by_batch"]),
        "## Not done",
        "",
        "- No holdout is frozen and no validation split is frozen.",
        "- No retrieval system has been run against any GOLD candidate.",
        "- Batch 006 has had no independent review; that is the next step.",
        "",
    ])


def write_reports(payload: dict, report_dir: Path) -> None:
    check_consistency(payload)
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / f"GOLD-001-batch-{payload['batch']:03d}-generation-report.json"
     ).write_text(json.dumps({k: v for k, v in payload.items() if k != "records"},
                             indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / f"GOLD-001-batch-{payload['batch']:03d}-generation-report.md"
     ).write_text(render_report(payload), encoding="utf-8")
    (report_dir / "GOLD-001-coverage-status-after-b006-generation.md").write_text(
        render_coverage(payload), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
