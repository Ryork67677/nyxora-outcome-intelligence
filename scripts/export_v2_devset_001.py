#!/usr/bin/env python3
"""V2-DEVSET-001: mine candidate evidence for a new v2 development set.

PREREGISTERED in experiments/RAG-V2/V2-DEVSET-001-preregistration.md BEFORE this
script ran. Nothing here is gold. Every record leaves as candidate_unverified.

Retrieval is never run. Holdout.json is never opened. Live docs are never fetched.
SYSTEM-E hash is not changed. Cases are not frozen.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import re
import shutil
import signal
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from rag_v1.db import connect
from rag_v1.gold import relations, scoping
from rag_v1.gold.anaphora import CRITICAL, evaluate_span
from rag_v1.gold.authoring import (
    DANGLING_REFERENCE,
    build_conditional,
    build_constraint,
    build_interaction,
    build_lifecycle,
    build_predicate_fact,
    plain,
    sentence,
)
from rag_v1.gold.factmining import iter_guarded_spans, package_fact
from rag_v1.gold.mining import (
    _context,
    _section_for,
    code_regions,
    identifiers_in,
    inside_code,
    looks_like_code,
    mine_table_parameters,
    mine_table_required,
    mine_table_types,
    wellformed_problem,
)
from rag_v1.gold.mining_v3 import (
    EVIDENCE_HARD_CAP,
    EVIDENCE_SOFT_CAP,
    compose_multi_hop,
    mine_definition_bullets,
    mine_prose,
    mine_row_facts,
)
from rag_v1.gold.mining_v5 import mine_constraints, mine_interactions, mine_lifecycle
from rag_v1.gold.normalisation import contains_claim_string, has_markdown_link
from rag_v1.gold.questionform import evaluate as question_form
from rag_v1.parsing import _sections_from_markdown

SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"
BATCH = 101
ID_PREFIX = "V2D-"
SCHEMA_VERSION = "v2-devset-001/1.0"
SEED = 20260901
TARGET_SIZE = 60
MIN_PACKET = 50
STOP_AT_POOL = 60
DOC_TIMEOUT_S = 45
CONTEXT_KEEP = 900
PROGRESS_PATH = Path("experiments/RAG-V2/V2-DEVSET-001/mine-progress-pass2.jsonl")
KEEP_PATH = Path("evals/review/v2_devset_001_batch_001.json")
ADVISOR_VID = "ver_b8b18cda9b875d51a2ce979a1bf4e909"
E_HASH = "7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe"

HOLDOUT_MISS_TEMPLATE_IDS = frozenset({
    "GOLD-B001-02", "GOLD-B001-09", "GOLD-B002-06", "GOLD-B003-04",
    "GOLD-B005-07", "GOLD-B006-02", "HA-20", "HA-21", "HA-37", "HA-43", "HA-58",
})

REVIEW_BATCHES = (
    "evals/review/gold_review_batch_001.json",
    "evals/review/gold_review_batch_002.json",
    "evals/review/gold_review_batch_003.json",
    "evals/review/gold_review_batch_004_final.json",
    "evals/review/gold_review_batch_005_final.json",
    "evals/review/gold_review_batch_006_final.json",
    "evals/review/gold_review_HA01_HA60_final.json",
)
GOLD_JSONL = (
    "evals/gold/batch_004_projection.jsonl",
    "evals/gold/batch_005_projection.jsonl",
    "evals/gold/batch_006_projection.jsonl",
    "evals/gold/batch_001_v2/projection.jsonl",
    "evals/golden/v1.jsonl",
    "evals/development/v1.jsonl",
)

CATEGORY_TO_REASONING = {
    "exact_constraint": "exact_lookup",
    "exact_lookup": "exact_lookup",
    "error_behavior": "error_behavior",
    "configuration_interaction": "configuration_interaction",
    "lifecycle": "lifecycle_compatibility_migration",
    "lifecycle_compatibility_migration": "lifecycle_compatibility_migration",
    "multi_hop": "multi_span_same_document",
}

GENERIC_IDENTIFIERS = frozenset({
    "type", "types", "name", "id", "url", "path", "content", "text", "value", "data",
    "model", "role", "status", "error", "message", "input", "output", "config",
    "options", "timeout", "timezone", "headers", "metadata", "context", "result",
    "params", "args", "kwargs", "state",
})

MODEL_RE = re.compile(
    r"\b(?:gpt-[\w.-]+|o[1-4](?:-[\w.-]+)?|claude[- ][\w.-]*|"
    r"Claude\s+(?:Opus|Sonnet|Haiku)\s+[\d.]+|"
    r"Sonnet\s+[\d.]+|Opus\s+[\d.]+|Haiku\s+[\d.]+|"
    r"text-embedding[\w.-]*|chatgpt[\w.-]*|davinci[\w.-]*|whisper[\w.-]*)\b",
    re.IGNORECASE,
)
ERROR_RE = re.compile(
    r"\b(?:error|exception|raises?|throws?|invalid_|not_found|unauthorized|"
    r"forbidden|denied|4\d\d|5\d\d|stop_reason)\b",
    re.IGNORECASE,
)
VERSION_RE = re.compile(
    r"\b(?:v\d+(?:\.\d+)+|api[- ]version|model[- ]version|"
    r"\b\d+\.\d+(?:\.\d+)?\b)\b",
    re.IGNORECASE,
)
SNAKE_RE = re.compile(r"`[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+`")
ERROR_KEEP = re.compile(
    r"\b(?:raises?|throws?|error|exception|invalid_|not_found|status.?code|"
    r"HTTP\s*[45]\d\d)\b",
    re.IGNORECASE,
)
READER_INTENT = re.compile(
    r"\b(?:you|we|i)\s+(?:want|wish|need|would like|prefer|intend|decide|choose)\b",
    re.IGNORECASE,
)
LOW_VALUE = re.compile(
    r"^(?:what type (?:is|does)|is\s+`[^`]+`\s+optional|"
    r"what is the (?:type|default type) of)\b",
    re.IGNORECASE,
)
CODE_SHAPED = re.compile(
    r"^\s*(?:[\w.\[\]\"']+\s*[=:]\s*\S|[\]\})],?\s*$|>>>|\$ )",
    re.MULTILINE,
)

STRESS_FLOORS = {
    "short_evidence_unit": 8,
    "long_technical_section": 6,
    "parameter_error_literal_lookup": 10,
    "version_model_discrimination": 6,
    "identifier_vs_semantic_distractor": 8,
    "lexical_query_shape": 8,
    "paraphrase_query_shape": 6,
    "multi_span_same_document": 4,
    "correct_document_difficult_passage": 6,
}

MAX_PER_DOCUMENT = 3
MAX_PER_OPENING = 6
PROVIDER_TARGET = {"openai": (28, 40), "anthropic": (28, 42)}


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
             "url": r[4], "captured_at": str(r[5])} for r in cur.fetchall()]


def normalise_question(question: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", (question or "").lower()).split())


def load_gold001_ids() -> set[str]:
    eligibility = json.loads(
        Path("experiments/GOLD-001/GOLD-001-eligibility-status.json").read_text())
    ids: set[str] = set()
    for batch in eligibility["batches"]:
        ids.update(batch.get("holdout_eligible_ids") or [])
    for split_name in ("development.json", "validation.json"):
        payload = json.loads(
            Path("evals/splits/gold150-v1", split_name).read_text())
        ids.update(payload["case_ids"])
    if len(ids) != 150:
        raise SystemExit(f"expected 150 GOLD-001 IDs, got {len(ids)}")
    return ids


def _ingest_record(record: dict, gold_ids: set[str], questions: set[str],
                   spans: set[tuple], texts: set[str], seen_ids: set[str],
                   collisions: Counter) -> None:
    cid = record.get("candidate_id") or record.get("case_id")
    if cid and gold_ids and cid not in gold_ids and not str(cid).startswith(
            ("AN-", "OA-")):
        # Review batches mix rejected candidates. Skip non-admitted GOLD/HA ids.
        if str(cid).startswith(("GOLD-", "HA-")):
            collisions["skipped_non_admitted_id"] += 1
            return
    if cid:
        seen_ids.add(cid)
    for field in ("proposed_question", "question", "generated_question"):
        if record.get(field):
            questions.add(normalise_question(record[field]))
    evidence_lists = record.get("expected_evidence")
    if evidence_lists:
        for span in evidence_lists:
            if span.get("version_id") is None:
                continue
            spans.add((span["version_id"], span["char_start"], span["char_end"]))
            texts.add(" ".join((span.get("evidence_text") or "").split()))
    elif record.get("version_id") is not None and record.get("char_start") is not None:
        spans.add((record["version_id"], record["char_start"], record["char_end"]))
        texts.add(" ".join((record.get("evidence_text") or "").split()))
    for revision in record.get("anchor_revisions") or []:
        if "old_char_start" in revision:
            spans.add((record.get("version_id"), revision["old_char_start"],
                       revision["old_char_end"]))
        for key in ("old_spans", "new_spans"):
            for span in revision.get(key) or []:
                vid = span.get("version_id") or record.get("version_id")
                spans.add((vid, span["char_start"], span["char_end"]))


def load_admitted_material(gold_ids: set[str]) -> tuple[set[str], set[tuple], set[str],
                                                        set[str], Counter]:
    questions: set[str] = set()
    spans: set[tuple] = set()
    texts: set[str] = set()
    seen_ids: set[str] = set()
    collisions = Counter()
    for path in REVIEW_BATCHES:
        payload = json.loads(Path(path).read_text())
        records = payload.get("records") or []
        for record in records:
            cid = record.get("candidate_id") or record.get("case_id")
            # Filter mixed files by the 150-ID list.
            if cid and cid.startswith(("GOLD-", "HA-")) and cid not in gold_ids:
                collisions["skipped_non_admitted_id"] += 1
                continue
            _ingest_record(record, gold_ids, questions, spans, texts, seen_ids,
                           collisions)
    for path in GOLD_JSONL:
        p = Path(path)
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            case = json.loads(line)
            cid = case.get("case_id") or case.get("candidate_id")
            if cid and cid.startswith(("GOLD-", "HA-")) and cid not in gold_ids:
                collisions["skipped_non_admitted_id"] += 1
                continue
            _ingest_record(case, gold_ids, questions, spans, texts, seen_ids,
                           collisions)
    return questions, spans, texts, seen_ids, collisions


def evidence_spans_of(record: dict) -> list[dict]:
    if record.get("expected_evidence"):
        return record["expected_evidence"]
    return [{
        "evidence_id": "E1",
        "version_id": record["version_id"],
        "section_path": record.get("section_path") or ["Preamble"],
        "char_start": record["char_start"],
        "char_end": record["char_end"],
        "evidence_text": record["evidence_text"],
        "evidence_hash": record["evidence_hash"],
        "evidence_char_length": record.get("evidence_char_length")
        or (record["char_end"] - record["char_start"]),
        "critical_strings": record.get("critical_strings") or [],
    }]


def attach_triples(record: dict) -> dict:
    spans = evidence_spans_of(record)
    evidence = " \n".join(s["evidence_text"] for s in spans)
    q_rel = record.get("question_relation")
    q_subj = record.get("question_subject")
    if not q_subj:
        ticks = re.findall(r"`([^`]+)`", record.get("proposed_question") or "")
        q_subj = f"`{ticks[0]}`" if ticks else None
        record["question_subject"] = q_subj
    source = None
    if q_rel in relations.RELATION_PATTERNS:
        source = relations.derive_source_triple(evidence, q_rel, q_subj)
    if source is None:
        source = relations.derive_generic_triple(evidence, q_subj)
    if source is None:
        source = {"source_subject": None, "source_relation": None,
                  "source_object": None, "source_sentence": None,
                  "derivation": "not derivable from the evidence"}
    source.setdefault("derivation", "named relation")
    record["source_subject"] = source["source_subject"]
    record["source_relation"] = source["source_relation"]
    record["source_object"] = source["source_object"]
    record["source_sentence"] = source["source_sentence"]
    record["source_triple_derivation"] = source["derivation"]
    if "question_object" not in record:
        record["question_object"] = None
    if "question_relation" not in record:
        record["question_relation"] = source.get("source_relation")
    return record


def finalise_record(doc: dict, built: dict, fact: dict, kind: str,
                    confidence: str) -> dict | None:
    start, end = fact["char_start"], fact["char_end"]
    body = fact["evidence_text"]
    critical = [c for c in (fact.get("critical_strings") or [])
                if contains_claim_string(body, c)]
    if not critical:
        ticks = re.findall(r"`([^`]+)`", built["question"])
        critical = [t for t in ticks if contains_claim_string(body, t)]
    if not critical:
        return None
    span = {
        "evidence_id": "E1",
        "version_id": doc["version_id"],
        "section_path": _section_for(doc["sections"], start),
        "char_start": start, "char_end": end,
        "evidence_text": body,
        "evidence_hash": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "evidence_char_length": end - start,
        "critical_strings": critical[:4],
    }
    before, after = _context(doc["text"], start, end)
    record = {
        "candidate_id": "",
        "provider": doc["provider"],
        "document_title": doc["title"],
        "version_id": doc["version_id"],
        "source_url": doc.get("url"),
        "captured_at": str(doc.get("captured_at")),
        "section_path": span["section_path"],
        "char_start": start,
        "char_end": end,
        "evidence_text": body,
        "evidence_hash": span["evidence_hash"],
        "evidence_char_length": end - start,
        "context_before": before[-CONTEXT_KEEP:],
        "context_after": after[:CONTEXT_KEEP],
        "expected_evidence": [span],
        "proposed_category": built["reasoning_type"],
        "reasoning_type": built["reasoning_type"],
        "secondary_category": built.get("secondary_category"),
        "proposed_question": built["question"],
        "proposed_answer": built["answer"],
        "proposed_atomic_claims": built["atomic_claims"],
        "question": built["question"],
        "answer": built["answer"],
        "atomic_claims": built["atomic_claims"],
        "critical_strings": critical[:4],
        "evidence_kind": kind,
        "binding": fact.get("binding") or "structural-or-subject-window",
        "evidence_shape": "single_span",
        "requires_all_evidence": False,
        "generator_confidence": confidence,
        "generator_notes": fact.get("generator_notes") or "",
        "needs_human_interpretation": bool(built.get("needs_human_interpretation")),
        "candidate_type": "supported",
        "verification_status": "candidate_unverified",
        "claude_proposed": True,
        "chatgpt_verified": None,
        "retrieval_was_not_run": True,
        "schema_version": SCHEMA_VERSION,
        "question_subject": built.get("question_subject"),
        "question_relation": built.get("question_relation"),
        "question_object": built.get("question_object"),
        "revisions": [],
        "stress_types": [],
    }
    attach_triples(record)
    return record


def from_templated(raw: dict) -> dict | None:
    q = raw.get("proposed_question") or raw.get("question")
    a = raw.get("proposed_answer") or raw.get("answer")
    claims = raw.get("proposed_atomic_claims") or raw.get("atomic_claims") or []
    if not q or not a or not claims:
        return None
    if raw.get("expected_evidence"):
        spans = []
        for i, s in enumerate(raw["expected_evidence"], start=1):
            body = s["evidence_text"]
            spans.append({
                "evidence_id": f"E{i}",
                "version_id": s["version_id"],
                "section_path": s.get("section_path") or ["Preamble"],
                "char_start": s["char_start"],
                "char_end": s["char_end"],
                "evidence_text": body,
                "evidence_hash": s.get("evidence_hash")
                or hashlib.sha256(body.encode("utf-8")).hexdigest(),
                "evidence_char_length": s.get("evidence_char_length")
                or (s["char_end"] - s["char_start"]),
                "critical_strings": s.get("critical_strings")
                or raw.get("critical_strings") or [],
            })
        first, last = spans[0], spans[-1]
        shape = ("multi_span" if len(spans) > 1 else "single_span")
        cat = raw.get("proposed_category") or raw.get("reasoning_type") or "exact_lookup"
        record = {
            **{k: raw.get(k) for k in (
                "provider", "document_title", "version_id", "source_url",
                "captured_at", "section_path", "generator_confidence",
                "needs_human_interpretation", "critical_strings")},
            "candidate_id": "",
            "char_start": first["char_start"],
            "char_end": last["char_end"] if first["version_id"] == last["version_id"]
            else first["char_end"],
            "evidence_text": first["evidence_text"] if len(spans) == 1
            else "\n\n".join(s["evidence_text"] for s in spans),
            "evidence_hash": first["evidence_hash"] if len(spans) == 1
            else hashlib.sha256(
                "\n\n".join(s["evidence_text"] for s in spans).encode()).hexdigest(),
            "evidence_char_length": sum(s["evidence_char_length"] for s in spans),
            "context_before": (raw.get("context_before") or "")[-CONTEXT_KEEP:],
            "context_after": (raw.get("context_after") or "")[:CONTEXT_KEEP],
            "expected_evidence": spans,
            "proposed_category": cat,
            "reasoning_type": CATEGORY_TO_REASONING.get(cat, cat),
            "proposed_question": q,
            "proposed_answer": a,
            "proposed_atomic_claims": claims,
            "question": q,
            "answer": a,
            "atomic_claims": claims,
            "evidence_kind": raw.get("evidence_kind") or "normative_statement",
            "binding": raw.get("binding") or "template-captured-groups",
            "evidence_shape": shape,
            "requires_all_evidence": len(spans) > 1,
            "candidate_type": "supported",
            "verification_status": "candidate_unverified",
            "claude_proposed": True,
            "chatgpt_verified": None,
            "retrieval_was_not_run": True,
            "schema_version": SCHEMA_VERSION,
            "generator_notes": raw.get("multi_hop_note") or raw.get("generator_notes") or "",
            "revisions": [],
            "stress_types": [],
            "question_subject": raw.get("question_subject"),
            "question_relation": raw.get("question_relation"),
            "question_object": raw.get("question_object"),
        }
        attach_triples(record)
        return record
    if raw.get("char_start") is None:
        return None
    cat = raw.get("proposed_category") or "exact_lookup"
    body = raw["evidence_text"]
    critical = [c for c in (raw.get("critical_strings") or [])
                if contains_claim_string(body, c)]
    if not critical:
        return None
    span = {
        "evidence_id": "E1",
        "version_id": raw["version_id"],
        "section_path": raw.get("section_path") or ["Preamble"],
        "char_start": raw["char_start"],
        "char_end": raw["char_end"],
        "evidence_text": body,
        "evidence_hash": raw.get("evidence_hash")
        or hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "evidence_char_length": raw["char_end"] - raw["char_start"],
        "critical_strings": critical,
    }
    record = {
        "candidate_id": "",
        "provider": raw["provider"],
        "document_title": raw["document_title"],
        "version_id": raw["version_id"],
        "source_url": raw.get("source_url") or raw.get("url"),
        "captured_at": str(raw.get("captured_at")),
        "section_path": span["section_path"],
        "char_start": raw["char_start"],
        "char_end": raw["char_end"],
        "evidence_text": body,
        "evidence_hash": span["evidence_hash"],
        "evidence_char_length": span["evidence_char_length"],
        "context_before": (raw.get("context_before") or "")[-CONTEXT_KEEP:],
        "context_after": (raw.get("context_after") or "")[:CONTEXT_KEEP],
        "expected_evidence": [span],
        "proposed_category": cat,
        "reasoning_type": CATEGORY_TO_REASONING.get(cat, cat),
        "proposed_question": q,
        "proposed_answer": a,
        "proposed_atomic_claims": claims,
        "question": q,
        "answer": a,
        "atomic_claims": claims,
        "critical_strings": critical,
        "evidence_kind": raw.get("evidence_kind") or "normative_statement",
        "binding": raw.get("binding") or "template-captured-groups",
        "evidence_shape": "single_span",
        "requires_all_evidence": False,
        "generator_confidence": raw.get("generator_confidence") or "medium",
        "generator_notes": raw.get("generator_notes") or "",
        "needs_human_interpretation": bool(raw.get("needs_human_interpretation")),
        "candidate_type": "supported",
        "verification_status": "candidate_unverified",
        "claude_proposed": True,
        "chatgpt_verified": None,
        "retrieval_was_not_run": True,
        "schema_version": SCHEMA_VERSION,
        "revisions": [],
        "stress_types": [],
        "question_subject": raw.get("question_subject"),
        "question_relation": raw.get("question_relation"),
        "question_object": raw.get("question_object"),
    }
    attach_triples(record)
    return record


def from_candidate_obj(c) -> dict | None:
    raw = c.to_dict() if hasattr(c, "to_dict") else dict(c)
    if not raw.get("proposed_question") or not raw.get("proposed_answer"):
        return None
    if "[REVIEWER TO WRITE]" in (raw.get("proposed_question") or ""):
        return None
    if not raw.get("proposed_atomic_claims"):
        return None
    return from_templated(raw)


def mine_long_paragraphs(doc: dict, limit: int = 10) -> list[dict]:
    text = doc["text"]
    fenced = code_regions(text)
    out: list[dict] = []
    offset = 0
    for piece in re.split(r"\n{2,}", text):
        if len(out) >= limit:
            break
        start = text.find(piece, offset)
        if start < 0:
            continue
        offset = start + len(piece)
        span = piece.strip()
        if not (400 <= len(span) <= EVIDENCE_HARD_CAP):
            continue
        end = start + len(piece)
        # trim to stripped span offsets
        leading = piece[:piece.find(span)] if span in piece else ""
        start = start + len(leading)
        end = start + len(span)
        if inside_code(fenced, start, end) or looks_like_code(span):
            continue
        if span.startswith(("#", "|", "```", "---", ">")):
            continue
        if CODE_SHAPED.search(span):
            continue
        if wellformed_problem(span) is not None:
            continue
        ids = identifiers_in(span)
        if not ids:
            continue
        critical = [i for i in ids if contains_claim_string(span, i)][:3]
        if not critical:
            continue
        fact = package_fact(doc, start, end, span, critical, "long_section",
                            "long_technical_section")
        built = build_predicate_fact(fact) or build_conditional(fact)
        if built is None:
            continue
        rec = finalise_record(doc, built, fact, "long_technical_section", "medium")
        if rec:
            out.append(rec)
    return out


def mine_short_and_error(doc: dict, limit: int = 20) -> list[dict]:
    out: list[dict] = []

    def keep(sentence: str) -> bool:
        if not (60 <= len(sentence) <= 220):
            return False
        return bool(ERROR_KEEP.search(sentence) or identifiers_in(sentence))

    for start, end, span, identifiers in iter_guarded_spans(doc, keep, limit):
        critical = [i for i in identifiers if contains_claim_string(span, i)][:3]
        if not critical:
            continue
        role = "error_literal" if ERROR_KEEP.search(span) else "short_unit"
        fact = package_fact(doc, start, end, span, critical, role,
                            "error_statement" if role == "error_literal"
                            else "short_normative")
        built = build_predicate_fact(fact) or build_conditional(fact)
        if built is None:
            continue
        rec = finalise_record(doc, built, fact, fact["evidence_kind"], "medium")
        if rec:
            out.append(rec)
    return out


def tag_stress(record: dict, doc_len: int) -> list[str]:
    tags: list[str] = []
    spans = evidence_spans_of(record)
    length = sum(s["evidence_char_length"] for s in spans)
    start = min(s["char_start"] for s in spans)
    q = record.get("proposed_question") or ""
    evidence = " ".join(s["evidence_text"] for s in spans)
    ticks = re.findall(r"`[^`]+`", q)
    if length <= 180:
        tags.append("short_evidence_unit")
    if length >= 400:
        tags.append("long_technical_section")
    if doc_len >= 4000 and start > max(800, int(0.25 * doc_len)):
        tags.append("correct_document_difficult_passage")
    if MODEL_RE.search(evidence) or MODEL_RE.search(q) or VERSION_RE.search(evidence):
        tags.append("version_model_discrimination")
    kind = record.get("evidence_kind") or ""
    if (kind in {"parameter_table_row", "definition_bullet", "constraint_statement",
                 "error_statement"}
            or ERROR_RE.search(evidence) or ERROR_RE.search(q)):
        tags.append("parameter_error_literal_lookup")
    if len(spans) > 1 and len({s["version_id"] for s in spans}) == 1:
        tags.append("multi_span_same_document")
    if ticks or SNAKE_RE.search(q):
        tags.append("identifier_vs_semantic_distractor")
    if len(ticks) >= 2 or SNAKE_RE.search(q) or ERROR_RE.search(q):
        tags.append("lexical_query_shape")
    if len(ticks) <= 1 and re.search(r"\bwhat happens (?:if|when)\b", q, re.I):
        tags.append("paraphrase_query_shape")
    elif len(ticks) == 0 and len(q.split()) >= 8:
        tags.append("paraphrase_query_shape")
    record["stress_types"] = list(dict.fromkeys(tags))
    return record["stress_types"]


def gates(record: dict, dropped: Counter) -> bool:
    q = record.get("proposed_question") or ""
    a = record.get("proposed_answer") or ""
    claims = record.get("proposed_atomic_claims") or []
    spans = evidence_spans_of(record)
    evidence = " \n".join(s["evidence_text"] for s in spans)

    if not q or not a or not claims:
        dropped["missing_qac"] += 1
        return False
    if "[REVIEWER TO WRITE]" in q:
        dropped["placeholder"] += 1
        return False
    if has_markdown_link(q) or has_markdown_link(a):
        dropped["markdown_junk"] += 1
        return False
    if DANGLING_REFERENCE.search(q) or DANGLING_REFERENCE.search(a):
        dropped["dangling_reference"] += 1
        return False
    if READER_INTENT.search(q):
        dropped["reader_intent"] += 1
        return False
    if LOW_VALUE.match(q):
        record["needs_human_interpretation"] = True
        record["generator_notes"] = (
            (record.get("generator_notes") or "") + " FLAG_LOW_VALUE").strip()
        dropped["low_value_flagged"] += 1
    if len(q) < 18:
        dropped["question_too_short"] += 1
        return False
    subject = next(iter(re.findall(r"`([^`]+)`", q)), None)
    ticks = re.findall(r"`([^`]+)`", q)
    if (subject and subject.lower() in GENERIC_IDENTIFIERS
            and not any(x.lower() not in GENERIC_IDENTIFIERS for x in ticks[1:])):
        dropped["generic_identifier"] += 1
        return False
    total = sum(s["evidence_char_length"] for s in spans)
    if total > EVIDENCE_HARD_CAP and len(spans) == 1:
        dropped["oversize"] += 1
        return False
    for span in spans:
        body = span["evidence_text"]
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if digest != span["evidence_hash"]:
            dropped["hash_mismatch"] += 1
            return False
        crit = span.get("critical_strings") or record.get("critical_strings") or []
        if not crit:
            dropped["no_critical_strings"] += 1
            return False
        stray = [s for s in crit if not contains_claim_string(body, s)]
        if stray and len(spans) == 1:
            dropped["critical_outside_span"] += 1
            return False
        if CODE_SHAPED.search(body):
            dropped["code_example"] += 1
            return False
        verdict = evaluate_span(body, record)
        if verdict["status"] == CRITICAL:
            dropped["critical_anaphora"] += 1
            return False
    scope = scoping.evaluate(record)
    if scope["status"] == scoping.NEEDS_SCOPE:
        dropped["bare_definition_scope"] += 1
        return False
    form = question_form(q, evidence)
    if form["status"] != "OK":
        dropped[f"question_form_{form['status']}"] += 1
        return False
    if record.get("source_subject") and record.get("question_subject"):
        rel = relations.evaluate(record)
        if rel["status"] == relations.REVERSED:
            dropped["relation_reversed"] += 1
            return False
        if rel["status"] == relations.SUBJECT_MISMATCH:
            record["needs_human_interpretation"] = True
            record["generator_notes"] = (
                (record.get("generator_notes") or "")
                + " FLAG_SUBJECT_MISMATCH").strip()
            dropped["subject_mismatch_flagged"] += 1
    if record.get("reasoning_type") == "configuration_interaction":
        named = [s for s in record.get("critical_strings") or [] if f"`{s}`" in evidence]
        ticks = re.findall(r"`([^`]+)`", evidence)
        if len(named) < 2 and len(ticks) < 2:
            record["reasoning_type"] = "exact_lookup"
            record["proposed_category"] = "exact_lookup"
            record["needs_human_interpretation"] = True
            dropped["interaction_relabelled_exact_lookup"] += 1
    record["expected_evidence"] = spans
    return True


def index_spans(spans: set[tuple]) -> dict:
    by_vid: dict = defaultdict(list)
    for vid, start, end in spans:
        by_vid[vid].append((start, end))
    return by_vid


def collides(record: dict, questions: set[str], spans: set[tuple], texts: set[str],
             spans_by_vid: dict, dropped: Counter) -> bool:
    """Exact question or exact version_id+char span only. Not overlap, not claim-text."""
    qn = normalise_question(record["proposed_question"])
    if qn in questions:
        dropped["exact_question"] += 1
        return True
    for span in evidence_spans_of(record):
        key = (span["version_id"], span["char_start"], span["char_end"])
        if key in spans:
            dropped["exact_span"] += 1
            return True
    return False


def select(pool: list[dict], size: int, rng: random.Random) -> list[dict]:
    by_provider: dict[str, list] = defaultdict(list)
    for c in pool:
        by_provider[c["provider"]].append(c)
    for group in by_provider.values():
        group.sort(key=lambda c: (c["version_id"], c["char_start"]))
        rng.shuffle(group)

    chosen: list[dict] = []
    documents: Counter = Counter()
    openings: Counter = Counter()
    providers: Counter = Counter()
    stress_counts: Counter = Counter()
    used_q: set[str] = set()
    used_span: set[tuple] = set()

    def opening(q: str) -> str:
        return " ".join(q.lower().split()[:3])

    def admissible(c: dict) -> bool:
        if c in chosen:
            return False
        qn = normalise_question(c["proposed_question"])
        if qn in used_q:
            return False
        for span in evidence_spans_of(c):
            key = (span["version_id"], span["char_start"], span["char_end"])
            if key in used_span:
                return False
        if documents[c["version_id"]] >= MAX_PER_DOCUMENT:
            return False
        if openings[opening(c["proposed_question"])] >= MAX_PER_OPENING:
            return False
        ceiling = PROVIDER_TARGET.get(c["provider"], (0, size))[1]
        if providers[c["provider"]] >= ceiling:
            return False
        return True

    def take(pred, quota: int) -> None:
        while sum(1 for c in chosen if pred(c)) < quota and len(chosen) < size:
            pick = None
            order = sorted(PROVIDER_TARGET, key=lambda p: providers[p])
            for provider in [*order, None]:
                for c in pool:
                    if not pred(c) or not admissible(c):
                        continue
                    if provider is not None and c["provider"] != provider:
                        continue
                    pick = c
                    break
                if pick is not None:
                    break
            if pick is None:
                return
            chosen.append(pick)
            documents[pick["version_id"]] += 1
            providers[pick["provider"]] += 1
            openings[opening(pick["proposed_question"])] += 1
            used_q.add(normalise_question(pick["proposed_question"]))
            for span in evidence_spans_of(pick):
                used_span.add((span["version_id"], span["char_start"], span["char_end"]))
            for tag in pick.get("stress_types") or []:
                stress_counts[tag] += 1

    for tag, floor in STRESS_FLOORS.items():
        take(lambda c, t=tag: t in (c.get("stress_types") or []), floor)

    # Prefer a second fact from a document already chosen (passage discrimination).
    represented = {c["version_id"] for c in chosen}
    take(lambda c: c["version_id"] in represented
         and "multi_span_same_document" not in (c.get("stress_types") or []), 8)

    while len(chosen) < size:
        before = len(chosen)
        take(lambda c: True, size)
        if len(chosen) == before:
            break

    # Tag same-document passage discrimination after selection.
    by_ver: dict[str, list] = defaultdict(list)
    for c in chosen:
        by_ver[c["version_id"]].append(c)
    for group in by_ver.values():
        if len(group) < 2:
            continue
        sections = {" › ".join(c.get("section_path") or []) for c in group}
        starts = {c["char_start"] for c in group}
        if len(starts) < 2:
            continue
        for c in group:
            if "same_document_passage_discrimination" not in c["stress_types"]:
                c["stress_types"].append("same_document_passage_discrimination")
    return chosen[:size]


def render_md(payload: dict) -> str:
    lines = [
        "# V2-DEVSET-001 review packet (batch 101)",
        "",
        (f"**{payload['candidates']} candidates · corpus snapshot `{SNAPSHOT}` · "
         f"generated {payload['generated_at']} ({payload['generated_at_et']})**"),
        "",
        ("Nothing in this file is ground truth. Every candidate is "
         "`candidate_unverified`. The evidence below is quoted verbatim from the "
         "frozen corpus and is authoritative for this review — **do not consult live "
         "documentation**, which may have changed since the snapshot."),
        "",
        ("For each candidate, judge the *proposed* question, answer and claims "
         "against the evidence and its surrounding context only. Return one record "
         "per candidate with verdict `PASS | FAIL | FIX_REQUIRED | UNCERTAIN` and "
         "the GOLD review fields in `docs/GOLD-REVIEW-PROCEDURE.md`."),
        "",
        ("ID prefix `V2D-`. This is a v2 **development** candidate set, not frozen "
         "gold, not gold150-v1 holdout, and not gold150-v1 validation."),
        "",
        "---",
        "",
    ]
    for c in payload["records"]:
        spans = c["expected_evidence"]
        path = " › ".join(c.get("section_path") or [])
        lines += [
            f"## {c['candidate_id']}",
            "",
            f"- **provider**: {c['provider']}",
            f"- **document**: {c['document_title']}",
            f"- **section**: {path}",
            f"- **source span**: `{c['version_id']}` chars {c['char_start']}–{c['char_end']}",
            f"- **evidence kind**: `{c['evidence_kind']}`",
            f"- **evidence shape**: `{c.get('evidence_shape')}`",
            f"- **reasoning type**: `{c.get('reasoning_type')}`",
            f"- **stress types**: {', '.join(c.get('stress_types') or []) or '_none_'}",
            f"- **binding**: {c.get('binding')}",
            f"- **generator confidence**: {c.get('generator_confidence')}",
            f"- **needs human interpretation**: {c.get('needs_human_interpretation')}",
            f"- **verification status**: `{c['verification_status']}`",
            "",
            "**Proposed question** (a suggestion, not gold)",
            "",
            f"> {c['proposed_question']}",
            "",
            f"**Proposed answer**: {c['proposed_answer']}",
            "",
            "**Proposed atomic claims**: " + "; ".join(
                f"`{x}`" if len(x) < 80 else x for x in c["proposed_atomic_claims"]),
            "",
            f"**Critical strings**: {', '.join(c.get('critical_strings') or [])}",
            "",
            f"**Generator notes**: {c.get('generator_notes') or '_none_'}",
            "",
        ]
        for span in spans:
            lines += [
                f"### Evidence {span['evidence_id']} (verbatim, authoritative)",
                "",
                f"`{span['version_id']}` chars {span['char_start']}–{span['char_end']} "
                f"· hash `{span['evidence_hash'][:16]}…`",
                "",
                "```",
                span["evidence_text"],
                "```",
                "",
            ]
        lines += [
            "<details><summary>Context before</summary>",
            "",
            "```",
            (c.get("context_before") or "")[-CONTEXT_KEEP:],
            "```",
            "",
            "</details>",
            "",
            "<details><summary>Context after</summary>",
            "",
            "```",
            (c.get("context_after") or "")[:CONTEXT_KEEP],
            "```",
            "",
            "</details>",
            "",
            "---",
            "",
        ]
    return "\n".join(lines)


def main() -> int:
    root = Path(".")
    prereg = root / "experiments/RAG-V2/V2-DEVSET-001-preregistration.md"
    if not prereg.exists():
        raise SystemExit("preregistration missing; refuse to mine")

    gold_ids = load_gold001_ids()
    prior_q, prior_spans, prior_texts, prior_seen, ingest_counts = (
        load_admitted_material(gold_ids))
    spans_by_vid = index_spans(prior_spans)
    print(f"GOLD-001 ids {len(gold_ids)} questions {len(prior_q)} spans {len(prior_spans)}",
          flush=True)

    generated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    generated_et = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")  # overwritten below
    # US Eastern display
    from zoneinfo import ZoneInfo
    generated_et = datetime.now(ZoneInfo("America/New_York")).strftime(
        "%Y-%m-%d %H:%M ET")

    with connect() as conn, conn.cursor() as cur:
        docs = load_docs(cur)
    doc_len = {d["version_id"]: len(d["text"]) for d in docs}

    # Round-robin providers so an early stop still mixes OpenAI/Anthropic.
    by_provider: dict[str, list] = defaultdict(list)
    for d in docs:
        by_provider[d["provider"]].append(d)
    ordered_docs: list[dict] = []
    buckets = [by_provider[p] for p in sorted(by_provider)]
    while any(buckets):
        for bucket in buckets:
            if bucket:
                ordered_docs.append(bucket.pop(0))

    class DocTimeout(Exception):
        pass

    def _alarm(signum, frame):
        raise DocTimeout()

    signal.signal(signal.SIGALRM, _alarm)

    dropped = Counter()
    pool: list[dict] = []
    raw_mined = 0
    skipped_docs: list[dict] = []
    docs_mined = 0

    def accept(rec: dict | None) -> None:
        nonlocal raw_mined
        if rec is None:
            dropped["unauthorable"] += 1
            return
        raw_mined += 1
        if not gates(rec, dropped):
            return
        if collides(rec, prior_q, prior_spans, prior_texts, spans_by_vid, dropped):
            return
        tag_stress(rec, doc_len.get(rec["version_id"], 0))
        pool.append(rec)

    def log_progress(i: int, doc: dict, elapsed: float, status: str) -> None:
        rec = {
            "i": i,
            "n_docs": len(ordered_docs),
            "version_id": doc["version_id"],
            "provider": doc["provider"],
            "title": doc["title"],
            "elapsed_s": round(elapsed, 3),
            "status": status,
            "pool": len(pool),
            "raw_mined": raw_mined,
            "dropped": sum(dropped.values()),
            "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with PROGRESS_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(
            f"  doc {i}/{len(ordered_docs)} {status} {elapsed:.1f}s "
            f"pool {len(pool)} provider {doc['provider']}",
            flush=True,
        )

    kept: list[dict] = []
    if KEEP_PATH.exists():
        prev = json.loads(KEEP_PATH.read_text())
        kept = list(prev.get("records") or [])
        keep_copy = Path("experiments/RAG-V2/V2-DEVSET-001/pass1-15.json")
        keep_copy.parent.mkdir(parents=True, exist_ok=True)
        if not keep_copy.exists():
            keep_copy.write_text(KEEP_PATH.read_text(), encoding="utf-8")
        for rec in kept:
            pool.append(rec)
            qn = normalise_question(rec.get("proposed_question") or rec.get("question") or "")
            if qn:
                prior_q.add(qn)
            for span in evidence_spans_of(rec):
                prior_spans.add((span["version_id"], span["char_start"], span["char_end"]))
        print(f"pass2 keep {len(kept)} gated from pass1", flush=True)

    templated: list[dict] = []
    facts_ix: list[dict] = []
    facts_c: list[dict] = []
    facts_l: list[dict] = []
    PROGRESS_PATH.write_text("", encoding="utf-8")
    print(f"mining {len(ordered_docs)} documents (timeout {DOC_TIMEOUT_S}s/doc; "
          f"stop at pool {STOP_AT_POOL}; pass2 GOLD-ish limits)", flush=True)

    for i, doc in enumerate(ordered_docs, start=1):
        if len(pool) >= STOP_AT_POOL:
            print(f"early stop at pool {len(pool)} after {docs_mined} docs", flush=True)
            break
        t0 = time.monotonic()
        status = "ok"
        signal.alarm(DOC_TIMEOUT_S)
        try:
            doc["sections"] = _sections_from_markdown(doc["text"])

            def timed_out() -> bool:
                return (time.monotonic() - t0) >= DOC_TIMEOUT_S

            advisor = doc["version_id"] == ADVISOR_VID
            for c in mine_table_parameters(doc, limit=4):
                accept(from_candidate_obj(c))
            if timed_out():
                raise DocTimeout()
            for c in mine_table_required(doc, limit=3):
                accept(from_candidate_obj(c))
            for c in mine_table_types(doc, limit=3):
                accept(from_candidate_obj(c))
            if timed_out():
                raise DocTimeout()
            if advisor:
                for rec in mine_short_and_error(doc, limit=8):
                    accept(rec)
                docs_mined += 1
                status = "advisor_narrow"
                continue
            for raw in mine_prose(doc, limit=20):
                templated.append(raw)
                accept(from_templated(raw))
            if timed_out():
                raise DocTimeout()
            for raw in mine_row_facts(doc, limit=10):
                templated.append(raw)
                accept(from_templated(raw))
            for raw in mine_definition_bullets(doc, limit=10):
                templated.append(raw)
                accept(from_templated(raw))
            if timed_out():
                raise DocTimeout()
            for fact in mine_interactions(doc, limit=40):
                facts_ix.append(fact)
                built = build_interaction(fact)
                if built:
                    accept(finalise_record(doc, built, fact, "configuration_interaction",
                                           "high"))
                else:
                    dropped["interaction_unbuilt"] += 1
            if timed_out():
                raise DocTimeout()
            for fact in mine_constraints(doc, limit=40):
                facts_c.append(fact)
                built = build_constraint(fact)
                if built:
                    accept(finalise_record(doc, built, fact, "constraint_statement",
                                           "high"))
                else:
                    dropped["constraint_unbuilt"] += 1
            if timed_out():
                raise DocTimeout()
            for fact in mine_lifecycle(doc, limit=30):
                facts_l.append(fact)
                built = build_lifecycle(fact)
                if built:
                    accept(finalise_record(doc, built, fact, "lifecycle_statement",
                                           "medium"))
                else:
                    dropped["lifecycle_unbuilt"] += 1
            if timed_out():
                raise DocTimeout()
            for rec in mine_long_paragraphs(doc, limit=8):
                accept(rec)
            if timed_out():
                raise DocTimeout()
            for rec in mine_short_and_error(doc, limit=16):
                accept(rec)
            docs_mined += 1
        except DocTimeout:
            status = "skipped_timeout"
            dropped["doc_timeout"] += 1
            skipped_docs.append({
                "version_id": doc["version_id"],
                "provider": doc["provider"],
                "title": doc["title"],
            })
        finally:
            signal.alarm(0)
            log_progress(i, doc, time.monotonic() - t0, status)

    print(f"skip compose_multi_hop (pass1 timed out); pool {len(pool)}", flush=True)

    # Intra-pool question/span dedupe.
    seen_q: set[str] = set()
    seen_span: set[tuple] = set()
    unique: list[dict] = []
    for rec in pool:
        qn = normalise_question(rec["proposed_question"])
        keys = [(s["version_id"], s["char_start"], s["char_end"])
                for s in evidence_spans_of(rec)]
        if qn in seen_q or any(k in seen_span for k in keys):
            dropped["intra_pool_dupe"] += 1
            continue
        seen_q.add(qn)
        seen_span.update(keys)
        unique.append(rec)
    pool = unique

    rng = random.Random(SEED)
    kept_ids = {r.get("candidate_id") for r in kept if r.get("candidate_id")}
    kept_span_keys = set()
    for r in kept:
        for s in evidence_spans_of(r):
            kept_span_keys.add((s["version_id"], s["char_start"], s["char_end"]))
    newcomers = []
    for rec in pool:
        if rec.get("candidate_id") in kept_ids:
            continue
        keys = [(s["version_id"], s["char_start"], s["char_end"])
                for s in evidence_spans_of(rec)]
        if any(k in kept_span_keys for k in keys):
            continue
        newcomers.append(rec)
    extra_n = max(0, TARGET_SIZE - len(kept))
    selected_new = select(newcomers, extra_n, rng) if newcomers and extra_n else []
    if len(kept) + len(selected_new) < MIN_PACKET and newcomers:
        need = MIN_PACKET - len(kept)
        seen = {id(c) for c in selected_new}
        for rec in newcomers:
            if id(rec) in seen:
                continue
            selected_new.append(rec)
            if len(selected_new) >= need:
                break
        print("selection floors undershot; filling from gated newcomers")
    selected = list(kept) + selected_new
    if len(selected) < MIN_PACKET:
        print(f"WARNING: only {len(selected)} gated candidates (need {MIN_PACKET})")
    print(f"select keep {len(kept)} + new {len(selected_new)} = {len(selected)}", flush=True)

    n = 1
    used = {r.get("candidate_id") for r in kept if r.get("candidate_id")}
    while f"{ID_PREFIX}{n:02d}" in used:
        n += 1
    for rec in selected:
        rec["verification_status"] = "candidate_unverified"
        rec["retrieval_was_not_run"] = True
        rec["chatgpt_verified"] = None
        rec["claude_proposed"] = True
        if rec.get("candidate_id") in kept_ids:
            continue
        rec["candidate_id"] = f"{ID_PREFIX}{n:02d}"
        n += 1

    out_dir = Path("evals/review")
    copy_dir = Path("experiments/RAG-V2/V2-DEVSET-001")
    out_dir.mkdir(parents=True, exist_ok=True)
    copy_dir.mkdir(parents=True, exist_ok=True)

    records = selected
    payload = {
        "task": "V2-DEVSET-001",
        "batch": BATCH,
        "id_prefix": ID_PREFIX,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "generated_at_et": generated_et,
        "corpus_snapshot": SNAPSHOT,
        "selection_seed": SEED,
        "preregistration": "experiments/RAG-V2/V2-DEVSET-001-preregistration.md",
        "system_e_config_hash": E_HASH,
        "system_e_hash_unchanged": True,
        "candidate_pool_size": len(pool),
        "raw_mined_authored": raw_mined,
        "candidates": len(records),
        "by_provider": dict(Counter(c["provider"] for c in records)),
        "by_evidence_kind": dict(Counter(c["evidence_kind"] for c in records)),
        "by_reasoning_type": dict(Counter(c.get("reasoning_type") for c in records)),
        "by_stress_type": dict(Counter(
            t for c in records for t in (c.get("stress_types") or []))),
        "by_confidence": dict(Counter(c.get("generator_confidence") for c in records)),
        "gold001_ids_excluded": sorted(gold_ids),
        "gold001_id_count": len(gold_ids),
        "gold001_admitted_questions_loaded": len(prior_q),
        "gold001_admitted_spans_loaded": len(prior_spans),
        "gold001_ids_seen_in_sources": sorted(prior_seen),
        "collisions_dropped": dict(dropped),
        "ingest_notes": dict(ingest_counts),
        "docs_attempted": docs_mined + len(skipped_docs),
        "docs_completed": docs_mined,
        "docs_skipped_timeout": skipped_docs,
        "mine_progress": str(PROGRESS_PATH),
        "holdout_json_opened": False,
        "holdout_miss_ids_used_as_templates": False,
        "holdout_miss_template_ids_excluded": sorted(HOLDOUT_MISS_TEMPLATE_IDS),
        "retrieval_was_not_run": True,
        "systems_executed": [],
        "live_docs_fetched": False,
        "verification_status": "candidate_unverified — nothing in this file is gold",
        "v1_exposed_regression_40_note": (
            "gold150-v1 validation is conceptually V1-EXPOSED-REGRESSION-40; "
            "split files were not renamed or moved."
        ),
        "next_step": "independent ChatGPT verification, then Russell human QC, then freeze",
        "records": records,
    }
    json_path = out_dir / "v2_devset_001_batch_001.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    payload["batch_sha256"] = hashlib.sha256(json_path.read_bytes()).hexdigest()
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")

    md_path = out_dir / "v2_devset_001_batch_001.md"
    md_path.write_text(render_md(payload), encoding="utf-8")

    shutil.copy2(json_path, copy_dir / "v2_devset_001_batch_001.json")
    shutil.copy2(md_path, copy_dir / "v2_devset_001_batch_001.md")

    print(f"raw_mined_authored {raw_mined}")
    print(f"pool after gates+dedupe {len(pool)}")
    print(f"selected {len(records)}")
    print("by_provider", payload["by_provider"])
    print("by_stress", payload["by_stress_type"])
    print("dropped", dict(dropped))
    print("wrote", json_path)
    print("wrote", md_path)
    print("md_bytes", md_path.stat().st_size)
    print("json_bytes", json_path.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
