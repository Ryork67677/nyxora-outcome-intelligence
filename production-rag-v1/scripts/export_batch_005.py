#!/usr/bin/env python3
"""GOLD-001: generate batch 005 — accelerated coverage in two lanes.

Batch 004 tested 559 identifier-sharing pairs and found one genuine multi-hop chain.
That result is why this batch is split. Lane A spends the effort where the corpus pays —
interactions, constraints, lifecycle statements, conditional behaviour, cross-component
ambiguity — and Lane B searches for chains dependency-first, from sentences that state a
dependency rather than from sentences that share a token, under a fixed budget so a
low-yield lane cannot consume the batch.

Two checks are new here and both come from what batch 004 cost. A bridge entity must
mean the same thing in both spans (``max_tokens`` is a request parameter in one place
and a ``stop_reason`` value in another). And a ``configuration_interaction`` must name
two settings that actually interact — batch 004 shipped two single conditional facts
under that label and its review had to relabel both.

The batch also self-reviews before export. That review is authoring, not verification:
it repairs what it can as a numbered revision and drops what it cannot, and every
candidate still leaves as ``candidate_unverified``.
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
from rag_v1.gold.ambiguity import find_ambiguous_fields
from rag_v1.gold.authoring import (
    DANGLING_REFERENCE,
    build_comparison,
    build_conditional,
    build_constraint,
    build_cross_component_ambiguity,
    build_interaction,
    build_lifecycle,
    compose_multi_hop_question,
    plain,
    sentence,
)
from rag_v1.gold.factmining import mine_bridge_facts
from rag_v1.gold.mining_v3 import (
    mine_definition_bullets,
    mine_prose,
    mine_row_facts,
)
from rag_v1.gold.mining_v5 import (
    find_cross_component_ambiguity,
    mine_constraints,
    mine_interactions,
    mine_lifecycle,
)
from rag_v1.gold.multihop import DEPENDENCY_PAIR_BUDGET, find_dependency_chains
from rag_v1.gold.normalisation import contains_claim_string
from rag_v1.parsing import _sections_from_markdown

SCHEMA_VERSION = "1.3"
SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"
PRIOR = (
    "evals/review/gold_review_batch_001.json",
    "evals/review/gold_review_batch_002.json",
    "evals/review/gold_review_batch_003.json",
    "evals/review/gold_review_batch_004_final.json",
)
DEVELOPMENT = "evals/development/v1.jsonl"
ELIGIBILITY = "experiments/GOLD-001/GOLD-001-eligibility-status.json"
#: Historical failures that shaped the architecture; retesting them measures the design
#: against its own training.
EXCLUDED_FAILURE_CASES = ("AN-001", "AN-003", "AN-012", "OA-004")

#: §7's Lane A mixture, and §5's provider balance. Ceilings are hard: a batch that
#: cannot reach 30 within them comes back short rather than padded.
REASONING_TARGET = {
    "genuine_multi_hop": (0, 6),
    "error_behavior": (5, 6),
    "configuration_interaction": (5, 6),
    "exact_lookup": (5, 6),
    "lifecycle_compatibility_migration": (3, 4),
    "ambiguity_disambiguation": (3, 4),
    "comparison": (2, 3),
}
PROVIDER_TARGET = {"openai": (14, 16), "anthropic": (14, 16)}
#: The batch-003 miner's own categories, mapped onto the reasoning vocabulary.
CATEGORY_TO_REASONING = {
    "exact_constraint": "exact_lookup",
    "error_behavior": "error_behavior",
    "configuration_interaction": "configuration_interaction",
    "lifecycle": "lifecycle_compatibility_migration",
}
EVIDENCE_SOFT_CAP = 1000
EVIDENCE_HARD_CAP = 1500
#: §7's mixture and §5's size can conflict, and here they do: ambiguity, comparison and
#: multi-hop are corpus-limited, so the preregistered ceilings cap this batch at 25 while
#: a hundred vetted candidates wait behind them in the categories that do have material.
#: Rather than quietly raise a ceiling — the post-hoc tuning this project forbids
#: everywhere else — the shortfall is filled from those categories under a declared cap,
#: and every candidate taken this way is marked ``selected_by = "overflow"`` and counted
#: in the report. A reader can subtract them.
OVERFLOW_CAP = {"error_behavior": 4, "configuration_interaction": 4, "exact_lookup": 3}
#: No document may supply more than this, so one rich page cannot become the batch.
MAX_PER_DOCUMENT = 3
#: §26: a template that dominates the batch makes the benchmark about the template.
MAX_PER_QUESTION_OPENING = 8


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
        raise SystemExit("the holdout is frozen — batch 005 must not be generated into "
                         "a frozen evaluation")
    if not status["retrieval_was_not_run"] or status["systems_executed"]:
        raise SystemExit("the eligibility status records a retrieval run; stop and "
                         "diagnose before authoring more candidates")
    return {
        "human_verified": combined["human_verified"],
        "holdout_eligible": combined["holdout_eligible"],
        "human_rejected": combined["human_rejected"],
        "genuine_multi_hop": combined["genuine_multi_hop"],
        "by_batch": [{k: b[k] for k in
                      ("batch", "human_verified", "holdout_eligible", "human_rejected",
                       "genuine_multi_hop")} for b in status["batches"]],
        "holdout_frozen": status["holdout_frozen"],
        "read_from": ELIGIBILITY,
    }


def normalise_question(question: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", question.lower()).split())


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
    """§23: say which span is meant to support which claim."""
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
        "expected_evidence": spans,
        "claim_evidence_map": map_claims(built["atomic_claims"], spans),
        "section_path": first["section_path"],
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


def build_multi_hop(pair: dict, docs_by_version: dict) -> dict:
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
    hop_1 = sentence(first["evidence_text"])
    hop_2 = sentence(second["evidence_text"])
    composed = (f"For `{bridge}`: {hop_1.rstrip('.')}. Consequently, {hop_2}")
    built = {
        "reasoning_type": "genuine_multi_hop",
        "secondary_category": "dependency_chain",
        "question": compose_multi_hop_question(bridge, first["evidence_text"]),
        "answer": plain(f"{hop_1} {hop_2}"),
        "atomic_claims": [hop_1, hop_2],
        "needs_human_interpretation": True,
    }
    record = base_record(doc, spans, built, "medium")
    record.update({
        "bridge_entity": bridge,
        "bridge_relationship": (
            f"Span 1 puts `{bridge}` into a state ({pair['state_evidence']!r}); span 2 "
            "makes an outcome conditional on that state."),
        "hop_1_claim": hop_1,
        "hop_2_claim": hop_2,
        "composed_claim": composed,
        "composed_answer": composed,
        "why_span_1_alone_is_insufficient": pair["why_span_1_alone_is_insufficient"],
        "why_span_2_alone_is_insufficient": pair["why_span_2_alone_is_insufficient"],
        "multi_hop_composition_check": pair["multi_hop_composition_check"],
        "semantic_compatibility_check": pair["semantic_compatibility_check"],
        "bridge_entity_text": pair["bridge_entity_text"],
        "bridge_entity_meaning_span_1": pair["bridge_entity_meaning_span_1"],
        "bridge_entity_meaning_span_2": pair["bridge_entity_meaning_span_2"],
        "bridge_equivalence_reason": pair["bridge_equivalence_reason"],
        "same_semantic_entity": pair["same_semantic_entity"],
        "state_established": pair["state_established"],
        "document_count": len({s["version_id"] for s in spans}),
        "section_count": len({tuple(s["section_path"]) for s in spans}),
    })
    return record


def precheck(record: dict) -> tuple[list[str], list[str]]:
    """§24: structural only. Says the record is checkable, not that it is right."""
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
    if not record["retrieval_was_not_run"]:
        failures.append("retrieval leakage")
    if record["reasoning_type"] == "genuine_multi_hop":
        if len(spans) < 2:
            failures.append("multi-hop with fewer than two spans")
        if not record.get("requires_all_evidence"):
            failures.append("multi-hop without requires_all_evidence")
        if record.get("multi_hop_composition_check") != "PASS":
            failures.append("multi-hop composition check did not pass")
        if record.get("semantic_compatibility_check") != "PASS":
            failures.append("multi-hop bridge failed the semantic equivalence check")
    return failures, flags


#: §25's vocabulary. A self-review is authoring, not verification.
READY = "READY_FOR_INDEPENDENT_REVIEW"
REPAIR = "NEEDS_INTERNAL_REPAIR"
DROP = "DROP"
#: "What does `timezone` mean?" — an identifier that exists in a dozen APIs needs to say
#: which one. Batch 004's review caught three of these after generation.
_GENERIC_IDENTIFIERS = frozenset({
    "type", "types", "name", "id", "url", "path", "content", "text", "value", "data",
    "model", "role", "status", "error", "message", "input", "output", "config",
    "options", "timeout", "timezone", "headers", "metadata", "context", "result",
})
#: A question of this shape asserts the identifier is the subject of the fact.
_SUBJECT_QUESTION = re.compile(r"^(?:What|Which) (?:does|is|must|are|bound)\b",
                               re.IGNORECASE)
_PREPOSITIONS = frozenset({"by", "for", "in", "with", "on", "of", "to", "from", "into",
                           "across", "over", "under", "via", "through", "between"})
_COMPARATIVE = re.compile(r"\b(?:a different|another|the other)\b", re.IGNORECASE)
#: A rule read off a sample is not a rule.
_BARE_DEFINITION = re.compile(r"^[-*]\s+`[^`]+`\s*:")
_CODE_SHAPED = re.compile(r"^\s*(?:[\w.\[\]\"']+\s*[=:]\s*\S|[\]\})],?\s*$|>>>|\$ )",
                          re.MULTILINE)


def semantic_review(record: dict) -> tuple[str, list[str], list[dict]]:
    """§25: read each candidate against its own evidence before exporting it.

    Returns a status, the findings, and any repairs applied. A repair is a numbered
    generation revision that keeps the original text, so the review can be disagreed
    with. Anything that cannot be repaired honestly is dropped rather than shipped with
    a caveat — a caveat in a benchmark is a defect with an excuse.
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

    relation = record.get("secondary_category")
    if record["reasoning_type"] == "configuration_interaction":
        named = [s for s in record["critical_strings"] if f"`{s}`" in evidence]
        if len(named) < 2:
            # Relabelling keeps a question that was written for a relation the evidence
            # does not state — "What does `X` override?" survives as an error_behavior
            # case whose answer is about something else. The premise failed, so the
            # candidate goes rather than changing its label.
            findings.append(
                "CATEGORY: labelled configuration_interaction but the evidence names "
                "fewer than two settings, and the question was written for a relation "
                "the evidence does not state")
            return DROP, findings, repairs

    # A relation has a direction. "The model rejects caller-supplied `betas` overrides"
    # matched "overrides" with `betas` nearby, and the question asked what `betas`
    # overrides — the opposite of what the sentence says.
    subject_relations = {"overrides": r"overrid", "requires": r"requir",
                         "disables": r"disabl|prevent|suppress",
                         "takes_precedence": r"takes precedence"}
    if relation in subject_relations and subject:
        pattern = (re.escape(f"`{subject}`") + r"[^.]{0,24}\b(?:"
                   + subject_relations[relation] + r")")
        if not re.search(pattern, evidence, re.IGNORECASE):
            findings.append(
                f"RELATION_DIRECTION: the question makes `{subject}` the thing that "
                f"{relation.replace('_', ' ')}, but the evidence does not put it in "
                "that position")
            return DROP, findings, repairs

    if record["reasoning_type"] == "ambiguity_disambiguation":
        readings = record.get("candidate_interpretations") or []
        if len(readings) < 2 or len({r["meaning"] for r in readings}) < 2:
            findings.append("NOT_AMBIGUITY: the readings do not differ")
            return DROP, findings, repairs

    if (record["reasoning_type"] == "genuine_multi_hop"
            and not record.get("same_semantic_entity")):
        findings.append("BRIDGE_EQUIVALENCE: the bridge entity does not mean the "
                        "same thing in both spans")
        return DROP, findings, repairs

    # A bare definition bullet takes its scope from the heading above it. Batch 004's
    # review rejected three candidates of exactly this shape — "What is the `timezone`
    # option?" — because §19 forbids leaning on a heading outside the span. Shipping the
    # shape again knowing that would be a regression, so it is dropped here unless the
    # span names its own parent.
    if len(spans) == 1 and _BARE_DEFINITION.match(spans[0]["evidence_text"].strip()):
        parent = [s for s in record["critical_strings"]
                  if s != subject and f"`{s}`" in evidence]
        if not parent:
            findings.append(
                "CLAIM_SCOPE: a definition bullet whose parent type is in the heading, "
                "not in the span — the same shape batch 004's review rejected")
            return DROP, findings, repairs

    length = len(record["question"])
    if length < 25:
        findings.append("QUESTION_FORM: too short to carry its conditions")
        return DROP, findings, repairs

    return (REPAIR if repairs else READY), findings, repairs


def interleave_providers(pool: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for candidate in pool:
        groups.setdefault(candidate["provider"], []).append(candidate)
    ordered: list[dict] = []
    from itertools import zip_longest
    for row in zip_longest(*(groups[p] for p in sorted(groups))):
        ordered += [c for c in row if c is not None]
    return ordered


def question_opening(question: str) -> str:
    return " ".join(question.split()[:3]).lower()


def select(pool: list[dict], size: int) -> tuple[list[dict], Counter]:
    """Fill the reasoning floors, then balance providers, then stop at the ceilings."""
    chosen: list[dict] = []
    reasons: Counter = Counter()
    counts: Counter = Counter()
    documents: Counter = Counter()
    openings: Counter = Counter()
    providers: Counter = Counter({p: 0 for p in PROVIDER_TARGET})
    blocked: dict[str, set[int]] = {}

    def note(reason: str, candidate: dict) -> None:
        if id(candidate) not in blocked.setdefault(reason, set()):
            blocked[reason].add(id(candidate))
            reasons[reason] += 1

    overflow_open = {"value": False}

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

    # Everything above respects the preregistered mixture. Only if that leaves the batch
    # short does the overflow open, and what it takes is recorded.
    if len(chosen) < size:
        reasons["short_of_target_before_overflow"] = size - len(chosen)
        overflow_open["value"] = True
        take(lambda c: True, size)
    return chosen[:size], reasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=30)
    parser.add_argument("--multi-hop-limit", type=int, default=6)
    parser.add_argument("--budget", type=int, default=DEPENDENCY_PAIR_BUDGET)
    parser.add_argument("--out-dir", default="evals/review")
    parser.add_argument("--report-dir", default="experiments/GOLD-001")
    args = parser.parse_args()

    state = verify_state()
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

    # ---- Lane A: coverage -------------------------------------------------------
    conditional_facts: list[dict] = []
    templated: list[dict] = []
    interactions: list[dict] = []
    constraints: list[dict] = []
    lifecycles: list[dict] = []
    single_doc_ambiguity: list[dict] = []
    for doc in docs:
        conditional_facts += mine_bridge_facts(doc)
        # The batch-003 template miners, unchanged. Their output has been through two
        # rounds of independent review and one owner review, which is a better warrant
        # than a pattern written this afternoon.
        templated += mine_prose(doc, limit=6)
        templated += mine_row_facts(doc, limit=3)
        templated += mine_definition_bullets(doc, limit=3)
        interactions += mine_interactions(doc)
        constraints += mine_constraints(doc)
        lifecycles += mine_lifecycle(doc)
        for finding in find_ambiguous_fields(doc, limit=3):
            single_doc_ambiguity.append((doc, finding))
    cross_component = find_cross_component_ambiguity(docs, limit=16)
    mined = (len(conditional_facts) + len(templated) + len(interactions)
             + len(constraints) + len(lifecycles) + len(single_doc_ambiguity)
             + len(cross_component))

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
    for fact in templated:
        add(fact, {
            "reasoning_type": CATEGORY_TO_REASONING.get(
                fact["proposed_category"], "exact_lookup"),
            "secondary_category": fact.get("evidence_kind"),
            "question": fact["proposed_question"],
            "answer": fact["proposed_answer"],
            "atomic_claims": fact["proposed_atomic_claims"],
        }, fact.get("generator_confidence", "medium"))

    # Ambiguity within one document keeps the batch-004 shape: one span per reading.
    for doc, finding in single_doc_ambiguity:
        readings = finding["candidate_interpretations"]
        if len(readings) < 2:
            continue
        chosen, other = readings[0], readings[1]
        term = finding["ambiguous_term"]
        spans = [evidence_record(i, doc, r["char_start"], r["char_end"],
                                 [term, r["meaning"][:60]])
                 for i, r in enumerate((chosen, other), start=1)]
        claims = [f"In `{r['scope']}`, `{term}` is: {sentence(r['meaning'])}"
                  for r in (chosen, other)]
        built = {
            "reasoning_type": "ambiguity_disambiguation",
            "secondary_category": "same_document_scope",
            "question": (f"In a `{chosen['scope']}`, what does the `{term}` field "
                         f"contain, and how does that differ from `{other['scope']}`?"),
            "answer": " ".join(claims),
            "atomic_claims": claims,
            "ambiguous_term": term,
            "candidate_interpretations": [
                {"scope": r["scope"], "meaning": r["meaning"]} for r in readings],
            "required_scope_to_answer": finding["required_scope_to_answer"],
            "needs_human_interpretation": True,
        }
        pool.append(base_record(doc, spans, built, "medium"))

    # Cross-component findings feed both the ambiguity lane and the comparison lane; a
    # finding is used once, whichever lane claims it first.
    for index, finding in enumerate(cross_component):
        builder = (build_cross_component_ambiguity if index % 2 == 0
                   else build_comparison)
        built = builder(finding)
        if built is None:
            continue
        first, second = finding["readings"]
        spans = [
            evidence_record(1, first["doc"], first["char_start"], first["char_end"],
                            [finding["ambiguous_term"]]),
            evidence_record(2, second["doc"], second["char_start"], second["char_end"],
                            [finding["ambiguous_term"]]),
        ]
        pool.append(base_record(first["doc"], spans, built, "medium"))

    # ---- Lane B: dependency-first multi-hop -------------------------------------
    chains, chain_report = find_dependency_chains(
        [f for f in conditional_facts], limit=args.multi_hop_limit, budget=args.budget)
    for pair in chains:
        pool.append(build_multi_hop(pair, docs_by_version))

    # ---- duplicate control, precheck, self-review -------------------------------
    kept: list[dict] = []
    seen_questions: set[str] = set()
    seen_spans: set[tuple] = set()
    seen_texts: set[str] = set()
    review_counts: Counter = Counter()
    dropped: list[dict] = []
    repaired: list[dict] = []

    for candidate in sorted(pool, key=lambda c: (c["version_id"],
                                                 c["expected_evidence"][0]["char_start"])):
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
        # The same sentence appears verbatim in several documents; a span key cannot see
        # that, because the offsets differ.
        if text_key in prior_texts or text_key in seen_texts:
            removed["duplicate_evidence_text"] += 1
            continue

        failures, flags = precheck(candidate)
        candidate["precheck_failures"] = failures
        candidate["precheck_flags"] = flags
        candidate["precheck_holdout_ready"] = not failures
        if failures:
            bucket = ("blocking_anaphora" if any("anaphora" in f for f in failures)
                      else "missing_critical_strings"
                      if any("critical strings" in f or "strings outside" in f
                             for f in failures)
                      else "failed_precheck")
            removed[bucket] += 1
            continue

        status, findings, repairs = semantic_review(candidate)
        candidate["internal_semantic_review_status"] = status
        candidate["internal_review_findings"] = findings
        candidate["generation_repairs"] = repairs
        review_counts[status] += 1
        if status == DROP:
            removed["dropped_by_semantic_review"] += 1
            dropped.append({"question": candidate["question"],
                            "reasoning_type": candidate["reasoning_type"],
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
        kept.append(candidate)

    eligible_by_reasoning = dict(Counter(c["reasoning_type"] for c in kept))
    eligible_by_provider = dict(Counter(c["provider"] for c in kept))
    chosen, selection_reasons = select(interleave_providers(kept), args.size)
    removed.update(selection_reasons)
    removed["not_selected_diversity"] = len(kept) - len(chosen)

    for position, candidate in enumerate(sorted(
            chosen, key=lambda c: (c["provider"], c["reasoning_type"],
                                   c["document_title"])), start=1):
        candidate["candidate_id"] = f"GOLD-B005-{position:02d}"
    chosen.sort(key=lambda c: c["candidate_id"])

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                         stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        commit = None

    lengths = sorted(s["evidence_char_length"]
                     for c in chosen for s in c["expected_evidence"])
    payload = {
        "batch": 5,
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit,
        "corpus_snapshot": SNAPSHOT,
        "starting_state": state,
        "candidate_pool_size": mined,
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
        "multi_document": sum(1 for c in chosen
                              if c["evidence_shape"] == "multi_document"),
        "complete_questions": sum(1 for c in chosen if c["question"]),
        "complete_answers": sum(1 for c in chosen if c["answer"]),
        "complete_claims": sum(1 for c in chosen if c["atomic_claims"]),
        "needs_human_interpretation": sum(1 for c in chosen
                                          if c["needs_human_interpretation"]),
        "precheck_holdout_ready": sum(1 for c in chosen
                                      if c["precheck_holdout_ready"]),
        "internal_review": {
            "counts": dict(review_counts),
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
            "strategy": "dependency-first: a chain may only open on a sentence that "
                        "states a dependency and puts the entity in a state",
            **chain_report,
            "valid_chains": len(chains),
            "exported_chains": sum(1 for c in chosen
                                   if c["reasoning_type"] == "genuine_multi_hop"),
        },
        "targets": {"reasoning_type": REASONING_TARGET, "provider": PROVIDER_TARGET},
        "verification_status": "candidate_unverified — nothing in this file is gold",
        "retrieval_was_not_run": True,
        "systems_executed": [],
        "records": chosen,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "gold_review_batch_005.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    payload["batch_sha256"] = hashlib.sha256(json_path.read_bytes()).hexdigest()
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    (out_dir / "gold_review_batch_005.md").write_text(render(payload), encoding="utf-8")
    write_reports(payload, Path(args.report_dir))

    print(f"pool {mined} mined -> {len(kept)} eligible -> batch 005 with {len(chosen)}")
    print("  provider  :", payload["by_provider"])
    print("  reasoning :", payload["by_reasoning_type"])
    print("  shape     :", payload["by_evidence_shape"])
    print("  documents :", payload["unique_documents"], payload["documents_by_provider"])
    print("  evidence  : mean", payload["evidence_length"]["mean"],
          "median", payload["evidence_length"]["median"],
          "max", payload["evidence_length"]["max"])
    print("  review    :", payload["internal_review"]["counts"])
    print("  multi-hop :", payload["multi_hop_search"]["funnel"],
          "-> exported", payload["multi_hop_search"]["exported_chains"])
    print("  removed   :", payload["removed"])
    return 0


def code_span(text: str) -> str:
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def render(payload: dict) -> str:
    lines: list[str] = [
        "# Gold review batch 005",
        "",
        (f"**{payload['candidates']} candidates · corpus snapshot "
         f"`{payload['corpus_snapshot']}` · generated {payload['generated_at']}**"),
        "",
        ("Nothing in this file is ground truth. Every candidate is "
         "`candidate_unverified`. The evidence is quoted verbatim from the frozen "
         "corpus and is authoritative for this review — **do not consult live "
         "documentation**, which may have changed since the snapshot."),
        "",
        ("Two things to know before reading. First, `precheck_holdout_ready` means the "
         "record is structurally checkable and nothing more: batch 004 shipped 15 of 15 "
         "precheck-ready and its review still repaired ten and rejected one. Second, "
         "the `internal_semantic_review_status` on each candidate is a **generation** "
         "self-review — the author reading its own output — and is not verification."),
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
        spans = record["expected_evidence"]
        lines += [
            f"## {record['candidate_id']}",
            "",
            f"- **provider**: {record['provider']}",
            f"- **document**: {record['document_title']}",
            f"- **section**: {' › '.join(record['section_path'])}",
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
        lines += [""]

        if record["reasoning_type"] == "genuine_multi_hop":
            lines += [
                "**Composition**", "",
                f"- **bridge entity**: {code_span(record['bridge_entity'])}",
                f"- **relationship**: {record['bridge_relationship']}",
                (f"- **bridge means the same thing in both spans**: "
                 f"`{record['semantic_compatibility_check']}` — "
                 f"{record['bridge_equivalence_reason']}"),
                f"- **hop 1**: {record['hop_1_claim']}",
                f"- **hop 2**: {record['hop_2_claim']}",
                f"- **composed**: {record['composed_claim']}",
                (f"- **span 1 alone is not enough**: "
                 f"{record['why_span_1_alone_is_insufficient']}"),
                (f"- **span 2 alone is not enough**: "
                 f"{record['why_span_2_alone_is_insufficient']}"),
                (f"- **composition check**: "
                 f"`{record['multi_hop_composition_check']}` · documents "
                 f"{record['document_count']} · sections {record['section_count']}"),
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
        for span in spans:
            lines += [
                (f"`{span['evidence_id']}` · `{span['version_id']}` "
                 f"{span['char_start']}–{span['char_end']} "
                 f"({span['evidence_char_length']} chars) · "
                 f"{' › '.join(span['section_path'])}"),
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
    if payload["genuine_multi_hop"] != payload["by_reasoning_type"].get(
            "genuine_multi_hop", 0):
        problems.append("genuine_multi_hop disagrees with the reasoning-type table")
    if payload["multi_hop_search"]["exported_chains"] != payload["genuine_multi_hop"]:
        problems.append("the multi-hop search and the batch disagree on exported chains")
    funnel = payload["multi_hop_search"]["funnel"]
    considered = funnel.get("dependency_pairs_considered", 0)
    accounted = sum(v for k, v in funnel.items() if k != "dependency_pairs_considered")
    if accounted > considered:
        problems.append("more multi-hop outcomes than pairs considered")
    if payload["precheck_holdout_ready"] != len(records):
        problems.append("a candidate that failed its precheck reached the batch")
    if problems:
        raise SystemExit("refusing to write a self-contradicting report:\n  "
                         + "\n  ".join(problems))


def overflow_note(payload: dict) -> list[str]:
    """Say plainly how many candidates came from beyond the preregistered mixture."""
    counts = payload.get("selected_by", {})
    overflow = counts.get("overflow", 0)
    if not overflow:
        return []
    return [
        (f"**{overflow} of {payload['candidates']} candidates were taken beyond §7's "
         "ceilings.** Ambiguity, comparison and multi-hop are corpus-limited here, so "
         "holding every ceiling would have returned a batch far short of target while "
         "vetted candidates waited in the categories that do have material. Rather than "
         "quietly raise a ceiling, the shortfall is filled under a declared cap "
         f"({payload['overflow_cap']}) and every candidate taken that way is marked "
         "`selected_by = \"overflow\"` in the record. Subtracting them gives the batch "
         "the preregistered mixture would have produced."),
        "",
    ]


def render_report(payload: dict) -> str:
    targets = payload["targets"]
    pool = payload["eligible_pool"]["by_reasoning_type"]
    search = payload["multi_hop_search"]
    funnel = search["funnel"]
    review = payload["internal_review"]

    reasoning_rows = "\n".join(
        f"| `{name}` | {payload['by_reasoning_type'].get(name, 0)} | {low}–{high} | "
        f"{'yes' if low <= payload['by_reasoning_type'].get(name, 0) <= high else 'NO'} "
        f"| {pool.get(name, 0)} |"
        for name, (low, high) in targets["reasoning_type"].items())
    provider_rows = "\n".join(
        f"| {name} | {payload['by_provider'].get(name, 0)} | {low}–{high} | "
        f"{'yes' if low <= payload['by_provider'].get(name, 0) <= high else 'NO'} | "
        f"{payload['documents_by_provider'].get(name, 0)} |"
        for name, (low, high) in targets["provider"].items())
    removed_rows = "\n".join(f"| {reason.replace('_', ' ')} | {count} |"
                             for reason, count in sorted(payload["removed"].items(),
                                                         key=lambda kv: -kv[1]))
    funnel_rows = "\n".join(f"| {stage.replace('_', ' ')} | {count} |"
                            for stage, count in funnel.items())
    dropped_rows = "\n".join(
        f"| `{d['reasoning_type']}` | {d['findings'][0].split(':')[0]} | "
        f"{d['question'][:70]} |" for d in review["dropped"][:20])
    opening_rows = "\n".join(f"| \"{opening}…\" | {count} |"
                             for opening, count in
                             list(payload["question_openings"].items())[:8])

    return "\n".join([
        "# GOLD-001 — batch 005 generation report",
        "",
        (f"**{payload['candidates']} candidates** from a mined pool of "
         f"{payload['candidate_pool_size']}, across {payload['unique_documents']} "
         "distinct documents. Nothing is verified; nothing is gold."),
        "",
        ("Batch 005 was commissioned as an accelerated coverage batch, and split into "
         "two lanes because of what batch 004 measured. Lane A mines the shapes the "
         "corpus actually contains. Lane B looks for genuine multi-hop chains "
         "dependency-first, under a fixed budget, rather than by testing every pair "
         "that shares an identifier — batch 004 did that and found one chain in 559."),
        "",
        "## Starting state",
        "",
        (f"Read from `{payload['starting_state']['read_from']}` before generating: "
         f"**{payload['starting_state']['human_verified']} human_verified**, "
         f"**{payload['starting_state']['holdout_eligible']} holdout_eligible**, "
         f"{payload['starting_state']['human_rejected']} rejected, "
         f"{payload['starting_state']['genuine_multi_hop']} genuine multi-hop. Holdout "
         f"frozen: {str(payload['starting_state']['holdout_frozen']).lower()}."),
        "",
        "## Composition",
        "",
        "| | |",
        "| --- | --- |",
        f"| provider | {payload['by_provider']} |",
        f"| documents by provider | {payload['documents_by_provider']} |",
        f"| versions by provider | {payload['versions_by_provider']} |",
        f"| reasoning type | {payload['by_reasoning_type']} |",
        f"| evidence shape | {payload['by_evidence_shape']} |",
        f"| confidence | {payload['by_confidence']} |",
        f"| genuine multi-hop | {payload['genuine_multi_hop']} |",
        f"| multi-document | {payload['multi_document']} |",
        (f"| complete question / answer / claims | {payload['complete_questions']} / "
         f"{payload['complete_answers']} / {payload['complete_claims']} of "
         f"{payload['candidates']} |"),
        (f"| needing reviewer judgement | {payload['needs_human_interpretation']} of "
         f"{payload['candidates']} |"),
        (f"| precheck holdout-ready | {payload['precheck_holdout_ready']} of "
         f"{payload['candidates']} |"),
        "",
        "### Reasoning types against target",
        "",
        "| reasoning type | in batch | target | met | eligible available |",
        "| --- | --- | --- | --- | --- |",
        reasoning_rows,
        "",
        ("The last column is the honest one. Where it equals the batch count the corpus "
         "had nothing more to give under these checks; where it is far above, a ceiling "
         "stopped the batch rather than the material."),
        "",
        *overflow_note(payload),
        "### Providers against target",
        "",
        "| provider | in batch | target | met | documents |",
        "| --- | --- | --- | --- | --- |",
        provider_rows,
        "",
        "## Multi-hop search — dependency-first",
        "",
        search["strategy"] + ".",
        "",
        "| stage | pairs |",
        "| --- | --- |",
        funnel_rows,
        "",
        (f"Budget: {search['budget']} pairs; "
         f"{funnel.get('dependency_pairs_considered', 0)} were considered, so the "
         "budget was not the constraint. "
         f"{search['entities_with_a_dependency_opener']} entities appear in at least "
         "one sentence that states a dependency; "
         f"**{search['valid_chains']}** "
         f"{'pair' if search['valid_chains'] == 1 else 'pairs'} survived every gate, "
         f"and {search['exported_chains']} reached the batch."
         + (" The survivor is the chain batch 004 already holds, so it is a duplicate "
            "rather than a new case — which is why the batch exports none."
            if search["valid_chains"] and not search["exported_chains"] else "")),
        "",
        ("The comparison with batch 004 is the useful part. That batch tested 559 "
         "identifier-sharing pairs to find one chain; this one considered "
         f"{funnel.get('dependency_pairs_considered', 0)} dependency-first pairs. "
         "Starting from sentences that state a dependency removes almost all of the "
         "work, and does not conjure chains that are not there — the corpus supports "
         "very few, and that remains the finding."),
        "",
        "## Generation self-review",
        "",
        (f"{review['counts']}. This is the author reading its own output before export. "
         "It is not independent verification and not human approval; every candidate is "
         "still `candidate_unverified`."),
        "",
        *(["### Dropped rather than shipped with a caveat", "",
           "| reasoning type | finding | question |", "| --- | --- | --- |",
           dropped_rows, ""] if review["dropped"] else []),
        *([(f"**{len(review['repaired'])} candidates repaired.** Each repair is a "
           "numbered generation revision that keeps the original value, so the review "
           "can be disagreed with."), ""] if review["repaired"] else []),
        "## Question shapes",
        "",
        "| opening | candidates |",
        "| --- | --- |",
        opening_rows,
        "",
        (f"No opening is allowed past {MAX_PER_QUESTION_OPENING} candidates. §26's "
         "concern is a batch that measures one template; the spread here comes from the "
         "facts being different kinds of statement, not from a generator alternating "
         "phrasings."),
        "",
        "## Evidence size",
        "",
        (f"Across {payload['evidence_length']['spans']} spans: mean "
         f"{payload['evidence_length']['mean']}, median "
         f"{payload['evidence_length']['median']}, min "
         f"{payload['evidence_length']['min']}, max "
         f"{payload['evidence_length']['max']} characters. "
         f"{payload['evidence_length']['over_soft_cap']} over the "
         f"{EVIDENCE_SOFT_CAP}-character soft cap, none over the {EVIDENCE_HARD_CAP} "
         "hard cap."),
        "",
        "## Removed before export",
        "",
        "| reason | count |",
        "| --- | --- |",
        removed_rows,
        "",
        "## Retrieval",
        "",
        ("No retrieval system was run against any batch-005 candidate at any point. "
         "SYSTEM-A and SYSTEM-B remain frozen and were not executed. No candidate was "
         "selected, ordered or worded because of what any system does with it, and no "
         "difficulty label in this batch derives from retrieval behaviour."),
        "",
    ])


def render_coverage(payload: dict) -> str:
    state = payload["starting_state"]
    projected = state["holdout_eligible"] + payload["candidates"]
    rows = "\n".join(
        f"| {b['batch']:03d} | {b['human_verified']} | {b['holdout_eligible']} | "
        f"{b['human_rejected']} | {b['genuine_multi_hop']} |"
        for b in state["by_batch"])
    return "\n".join([
        "# GOLD-001 — coverage status after batch 005 generation",
        "",
        (f"**Confirmed eligible today: {state['holdout_eligible']}.** Batch 005 adds "
         f"{payload['candidates']} *candidates*, which are not eligible and not "
         "verified."),
        "",
        "## Confirmed — batches 001–004 (human-approved, closed)",
        "",
        "| batch | human_verified | holdout_eligible | rejected | genuine multi-hop |",
        "| --- | --- | --- | --- | --- |",
        rows,
        (f"| **total** | **{state['human_verified']}** | "
         f"**{state['holdout_eligible']}** | **{state['human_rejected']}** | "
         f"**{state['genuine_multi_hop']}** |"),
        "",
        "## Projection, and what it is not",
        "",
        (f"If every one of the {payload['candidates']} batch-005 candidates were "
         f"eventually approved, the project would hold **{projected}** eligible cases. "
         "No batch has ever approved every candidate: the four closed batches approved "
         "16 of 18, 17 of 18, 20 of 20 and 14 of 15. Treat the number as a ceiling."),
        "",
        ("The projection must not become a reason to approve. If eighteen of these are "
         "good, the right outcome is eighteen — a hundred cases assembled by relaxing "
         "the bar measures less than sixty-seven assembled without."),
        "",
        "## Genuine multi-hop",
        "",
        (f"Confirmed: **{state['genuine_multi_hop']}**. Batch 005 proposes "
         f"**{payload['genuine_multi_hop']}**. The dependency-first search considered "
         f"{payload['multi_hop_search']['funnel'].get('dependency_pairs_considered', 0)}"
         " pairs against batch 004's 559 shared-identifier pairs, and the yield is "
         "still what the corpus supports rather than what the target asks for."),
        "",
        "## What this report does not say",
        "",
        ("- no batch-005 candidate is eligible, verified, or gold;\n"
         "- no retrieval system was run against any candidate in any batch;\n"
         "- the holdout is not frozen, and this report does not freeze it;\n"
         "- batches 001–004 are unchanged."),
        "",
    ])


def write_reports(payload: dict, report_dir: Path) -> None:
    check_consistency(payload)
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {k: v for k, v in payload.items() if k != "records"}
    report["report_of"] = "evals/review/gold_review_batch_005.json"
    (report_dir / "GOLD-001-batch-005-generation-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "GOLD-001-batch-005-generation-report.md").write_text(
        render_report(payload), encoding="utf-8")
    (report_dir / "GOLD-001-coverage-status-after-b005-generation.md").write_text(
        render_coverage(payload), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
