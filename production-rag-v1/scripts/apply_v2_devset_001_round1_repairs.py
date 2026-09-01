#!/usr/bin/env python3
"""Apply ChatGPT round-1 FIX_REQUIRED verdicts to V2-DEVSET-001.

Does not freeze, does not run retrieval, does not open holdout.json, does not
touch the 34 PASS cases, does not import PASS as gold, does not run D or E.
Status after fix is candidate_unverified_after_fix.
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from rag_v1.db import connect
from rag_v1.gold.anaphora import evaluate_span
from rag_v1.gold.mining import wellformed_problem
from rag_v1.gold.normalisation import contains_claim_string, has_markdown_link
from rag_v1.gold.questionform import evaluate as question_form
from rag_v1.gold import relations

SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"
CONTEXT_KEEP = 900
EVIDENCE_HARD_CAP = 1500
STATUS_AFTER = "candidate_unverified_after_fix"
ROOT = Path("/workspace/rag-v1/repo/production-rag-v1")
PACKET = ROOT / "evals/review/v2_devset_001_batch_001.json"
VERDICTS = ROOT / "experiments/RAG-V2/V2-DEVSET-001/chatgpt-verdicts-round1.json"
OUT_JSON = ROOT / "experiments/RAG-V2/V2-DEVSET-001/v2_devset_001_repairs_round1.json"
OUT_MD_EXP = ROOT / "experiments/RAG-V2/V2-DEVSET-001/v2_devset_001_repairs_round1.md"
OUT_MD_REVIEW = ROOT / "evals/review/v2_devset_001_repairs_round1.md"
OUT_DOWNLOADS = Path("/home/box/Downloads/v2_devset_001_repairs_round1.md")
STATUS = ROOT / "experiments/RAG-V2/V2-DEVSET-001-status.md"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def locate(text: str, head: str, tail: str, old_start: int, old_end: int) -> tuple[int, int]:
    start = text.rfind(head, 0, old_end)
    if start == -1:
        raise SystemExit(f"could not locate head {head!r} before offset {old_end}")
    index = text.find(tail, start)
    if index == -1:
        raise SystemExit(f"could not locate tail {tail!r} after offset {start}")
    return start, index + len(tail)


def check_superset(text: str, new: tuple[int, int], old: tuple[int, int]) -> None:
    if not (new[0] <= old[0] and new[1] >= old[1]):
        raise SystemExit(f"refusing: new span {new} does not contain old span {old}")
    if text[old[0]:old[1]] not in text[new[0]:new[1]]:
        raise SystemExit("refusing: original evidence text is not inside the new span")


def load_frozen(version_ids: list[str]) -> dict[str, str]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT v.version_id, v.normalized_text
            FROM document_version v
            JOIN corpus_snapshot_version sv ON sv.version_id = v.version_id
            WHERE sv.snapshot_id = %s AND v.version_id = ANY(%s)
            """,
            (SNAPSHOT, version_ids),
        )
        rows = cur.fetchall()
    texts = {vid: body for vid, body in rows}
    missing = set(version_ids) - set(texts)
    if missing:
        raise SystemExit(f"version_ids not in snapshot {SNAPSHOT}: {sorted(missing)}")
    return texts


def attach_triples(record: dict) -> None:
    evidence = record["evidence_text"]
    q_rel = record.get("question_relation")
    q_subj = record.get("question_subject")
    source = None
    if q_rel in relations.RELATION_PATTERNS:
        source = relations.derive_source_triple(evidence, q_rel, q_subj)
    if source is None:
        source = relations.derive_generic_triple(evidence, q_subj)
    if source is None:
        source = {
            "source_subject": None,
            "source_relation": None,
            "source_object": None,
            "source_sentence": None,
            "derivation": "not derivable from the evidence",
        }
    source.setdefault("derivation", "named relation")
    record["source_subject"] = source["source_subject"]
    record["source_relation"] = source["source_relation"]
    record["source_object"] = source["source_object"]
    record["source_sentence"] = source["source_sentence"]
    record["source_triple_derivation"] = source["derivation"]


# ChatGPT evidence_boundary_complete=false IDs (only these may grow the span).
EXPAND_IDS = {
    "V2D-06", "V2D-08", "V2D-18", "V2D-32", "V2D-33", "V2D-37", "V2D-38", "V2D-50",
}

# locate_head / locate_tail for expansions. Tails are unique suffixes of the new span.
EXPANSIONS = {
    "V2D-06": {
        "head": 'When a request with `speed: "fast"` succeeds',
        "tail": 'the `speed` field accurately shows `"standard"`.',
        "why": (
            "Extended forward to the Claude Opus 4.6 exception that qualifies the "
            "selected sentence (a speed=fast request can succeed while usage.speed "
            "is standard)."
        ),
    },
    "V2D-08": {
        "head": "  - `allowed_fallback_models: array of string or null`",
        "tail": "as `fallbacks[i].model` on the Messages API.",
        "why": (
            "Extended backwards to the Returns field name `allowed_fallback_models` "
            "so the description is bound to the identifier it defines."
        ),
    },
    "V2D-18": {
        "head": "Use `ModelStep.raise_error()` to fail one model call.",
        "tail": "must vary dynamically by attempt.",
        "why": (
            "Extended backwards to the sentence that names `ModelStep.raise_error`, "
            "so 'the Python helper' is identified inside the span."
        ),
    },
    "V2D-32": {
        "head": "* [OpenSSL](https://openssl-library.org/source/) 1.1.1 or later.",
        "tail": "the `openssl` binary must be on your `PATH`).",
        "why": (
            "Extended backwards to include the OpenSSL 1.1.1+ version requirement "
            "that sits in the same bullet as the Windows PATH/install statement."
        ),
    },
    "V2D-33": {
        "head": "You have 3 options:",
        "tail": "you pass in a starting agent and input.",
        "why": (
            "Extended backwards to the list that names `Runner.run`, "
            "`Runner.run_sync`, and `Runner.run_streamed`, resolving 'the three "
            "Runner methods above'."
        ),
    },
    "V2D-37": {
        "head": "The async client uses the exact same interface.",
        "tail": "will be read asynchronously automatically.",
        "why": (
            "Extended backwards to the sentence that scopes PathLike async "
            "file-reading to the async client."
        ),
    },
    "V2D-38": {
        "head": "**2. Have the model propose options before building.**",
        "tail": "it produces meaningfully different directions across runs.",
        "why": (
            "Extended backwards to the heading that names the approach "
            "('have the model propose options before building'), resolving "
            "'this approach'."
        ),
    },
    "V2D-50": {
        "head": (
            "If you want to switch to other models like `gpt-5.6-sol`, there are "
            "two ways to configure your agents."
        ),
        "tail": "the SDK applies default `ModelSettings`.",
        "why": (
            "Extended backwards to the default-model configuration path "
            "(`OPENAI_DEFAULT_MODEL` and `RunConfig`), resolving 'in this way'."
        ),
    },
}

# Minimal evidence-faithful rewrites. Answers stay inside the (possibly expanded) span.
REWRITES = {
    "V2D-03": {
        "question": "For org-wide queries, what do `created_at.*` filters require?",
        "answer": "`order_by=created_at`.",
        "atomic_claims": [
            "For org-wide queries, `created_at.*` filters require `order_by=created_at`.",
        ],
        "critical_strings": ["created_at.*", "order_by=created_at"],
        "question_subject": "`created_at.*` filters on org-wide queries",
        "question_relation": "requires",
        "question_object": "`order_by=created_at`",
        "what_changed": (
            "Rewrote the question so it asks about `created_at.*` filters on "
            "org-wide queries rather than what `created_at` itself requires. "
            "Narrowed the answer/claim to the created_at rule; did not mash in "
            "the separate `updated_at.*` rule. Span unchanged "
            "(ChatGPT evidence_boundary_complete=true; the full matching-sort-key "
            "sentence was already in the span)."
        ),
    },
    "V2D-05": {
        "question": "What does grouping by `speed` require?",
        "answer": "The `fast-mode-2026-02-01` beta header.",
        "atomic_claims": [
            "Grouping by `speed` requires the `fast-mode-2026-02-01` beta header.",
        ],
        "critical_strings": ["speed", "fast-mode-2026-02-01"],
        "question_subject": "grouping by `speed`",
        "question_relation": "requires",
        "question_object": "the `fast-mode-2026-02-01` beta header",
        "what_changed": (
            "Rewrote question and claim to preserve the grouping condition. "
            "Does not say that `speed` generally requires the beta header. "
            "Span unchanged."
        ),
    },
    "V2D-06": {
        "question": (
            "What is `usage.speed` when a request with `speed: \"fast\"` succeeds, "
            "including on Claude Opus 4.6?"
        ),
        "answer": (
            "It is `\"fast\"`. Claude Opus 4.6 is an exception: requesting fast mode "
            "can succeed while the `speed` field shows `\"standard\"`."
        ),
        "atomic_claims": [
            "When a request with `speed: \"fast\"` succeeds, `usage.speed` is `\"fast\"`.",
            (
                "If you are using Claude Opus 4.6 and request fast mode, it silently "
                "switches to standard speed and the `speed` field accurately shows "
                "`\"standard\"`."
            ),
        ],
        "critical_strings": ["usage.speed", "Claude Opus 4.6", "standard"],
        "question_subject": '`speed: "fast"`',
        "question_relation": None,
        "question_object": None,
        "what_changed": (
            "Included the Claude Opus 4.6 exception in the question, answer, and "
            "claims. Expanded the evidence boundary forward to that following "
            "exception (speed=fast can succeed while usage.speed is standard)."
        ),
    },
    "V2D-08": {
        "question": "What does `allowed_fallback_models` contain?",
        "answer": "Model IDs this model accepts as `fallbacks[i].model` on the Messages API.",
        "atomic_claims": [
            (
                "`allowed_fallback_models` contains model IDs this model accepts as "
                "`fallbacks[i].model` on the Messages API."
            ),
        ],
        "critical_strings": ["allowed_fallback_models", "fallbacks[i].model"],
        "question_subject": "`allowed_fallback_models`",
        "question_relation": None,
        "question_object": "model IDs this model accepts as `fallbacks[i].model` on the Messages API",
        "what_changed": (
            "Named the omitted field `allowed_fallback_models` in the question. "
            "Expanded the evidence boundary backwards to the field name."
        ),
    },
    "V2D-13": {
        "question": "What does the experimental model reject?",
        "answer": (
            "`reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` "
            "or `betas` overrides."
        ),
        "atomic_claims": [
            (
                "The experimental model rejects `reasoning.summary`, `max_tool_calls`, "
                "and caller-supplied `multi_agent` or `betas` overrides."
            ),
        ],
        "critical_strings": ["betas", "reasoning.summary", "max_tool_calls"],
        "question_subject": "the experimental model",
        "question_relation": "rejects",
        "question_object": (
            "`reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` "
            "or `betas` overrides"
        ),
        "what_changed": (
            "RELATION_DIRECTION fix: the question no longer asks what `betas` "
            "override. Subject is the experimental model; relation is rejects; "
            "object is the listed overrides. Span unchanged."
        ),
    },
    "V2D-18": {
        "question": "What does `ModelStep.raise_error` accept?",
        "answer": (
            "A fixed `ModelRetryAdvice` value; use a custom `Model` when retry advice "
            "itself must vary dynamically by attempt."
        ),
        "atomic_claims": [
            (
                "`ModelStep.raise_error` accepts a fixed `ModelRetryAdvice` value; "
                "use a custom `Model` when retry advice itself must vary dynamically "
                "by attempt."
            ),
        ],
        "critical_strings": ["ModelStep.raise_error", "ModelRetryAdvice"],
        "question_subject": "`ModelStep.raise_error`",
        "question_relation": "accepts",
        "question_object": "a fixed `ModelRetryAdvice` value",
        "what_changed": (
            "Replaced 'the Python helper' with `ModelStep.raise_error`. Expanded "
            "the evidence boundary backwards so the helper name is inside the span."
        ),
    },
    "V2D-19": {
        "question": "What argument does `files_from_dir` accept?",
        "answer": "A directory path.",
        "atomic_claims": [
            "The Python SDK `files_from_dir` helper accepts a directory path.",
        ],
        "critical_strings": ["files_from_dir"],
        "question_subject": "`files_from_dir`",
        "question_relation": "accepts",
        "question_object": "a directory path",
        "what_changed": (
            "Grammatical rewrite: the question now asks what argument "
            "`files_from_dir` accepts. Span unchanged."
        ),
    },
    "V2D-21": {
        "question": "What safeguard is recommended for large `view` command output?",
        "answer": (
            "Cap how many characters the `view` command returns, and let Claude page "
            "through the rest with `view_range`."
        ),
        "atomic_claims": [
            (
                "Consider capping how many characters the `view` command returns, "
                "and let Claude page through the rest with `view_range`."
            ),
        ],
        "critical_strings": ["view", "view_range"],
        "question_subject": "large `view` command output",
        "question_relation": None,
        "question_object": None,
        "what_changed": (
            "Rewrote the malformed question to ask what safeguard is recommended "
            "for large `view` output. Span unchanged."
        ),
    },
    "V2D-22": {
        "question": "What has already been appended by the time `next_message` returns?",
        "answer": "The assistant message and tool result for that turn.",
        "atomic_claims": [
            (
                "By the time `next_message` returns, the assistant message and tool "
                "result for that turn are already appended."
            ),
        ],
        "critical_strings": ["next_message"],
        "question_subject": "`next_message`",
        "question_relation": "returns",
        "question_object": None,
        "what_changed": (
            "Rewrote the malformed question to 'What has already been appended by "
            "the time `next_message` returns?'. Span unchanged."
        ),
    },
    "V2D-23": {
        "question": "What are credentialless `rclone` mounts limited to?",
        "answer": "S3, GCS, R2, and Azure Blob.",
        "atomic_claims": [
            "Credentialless `rclone` mounts are limited to S3, GCS, R2, and Azure Blob.",
        ],
        "critical_strings": ["rclone", "FuseMountPattern", "blobfuse2"],
        "question_subject": "credentialless `rclone` mounts",
        "question_relation": "is_limited_to",
        "question_object": "S3, GCS, R2, and Azure Blob",
        "what_changed": (
            "Grammar only: 'What are credentialless `rclone` mounts limited to?'. "
            "No factual change. Span unchanged."
        ),
    },
    "V2D-32": {
        "question": (
            "What OpenSSL version is required, and what is required of the `openssl` "
            "binary on Windows?"
        ),
        "answer": (
            "OpenSSL 1.1.1 or later. On Windows, install it separately (the `openssl` "
            "binary must be on your `PATH`)."
        ),
        "atomic_claims": [
            "OpenSSL 1.1.1 or later is required.",
            (
                "On Windows, install OpenSSL separately (the `openssl` binary must be "
                "on your `PATH`)."
            ),
        ],
        "critical_strings": ["OpenSSL", "1.1.1", "openssl", "PATH"],
        "question_subject": "OpenSSL",
        "question_relation": None,
        "question_object": None,
        "what_changed": (
            "Included the adjacent OpenSSL 1.1.1 or later version requirement and "
            "narrowed the Windows part to install/PATH. Expanded the evidence "
            "boundary backwards to the start of that bullet."
        ),
    },
    "V2D-33": {
        "question": (
            "What do you pass in when you call `Runner.run`, `Runner.run_sync`, or "
            "`Runner.run_streamed`?"
        ),
        "answer": "A starting agent and input.",
        "atomic_claims": [
            (
                "When you call `Runner.run`, `Runner.run_sync`, or `Runner.run_streamed`, "
                "you pass in a starting agent and input."
            ),
        ],
        "critical_strings": ["Runner.run", "Runner.run_sync", "Runner.run_streamed"],
        "question_subject": "`Runner.run` / `Runner.run_sync` / `Runner.run_streamed`",
        "question_relation": None,
        "question_object": "a starting agent and input",
        "what_changed": (
            "Replaced 'the three Runner methods above' with `Runner.run`, "
            "`Runner.run_sync`, and `Runner.run_streamed`. Expanded the evidence "
            "boundary backwards to the list that names those methods."
        ),
    },
    "V2D-37": {
        "question": "What happens if you pass a `PathLike` instance to the async client?",
        "answer": "The file contents will be read asynchronously automatically.",
        "atomic_claims": [
            (
                "If you pass a PathLike instance to the async client, the file "
                "contents will be read asynchronously automatically."
            ),
        ],
        "critical_strings": ["PathLike", "async client"],
        "question_subject": "`PathLike` on the async client",
        "question_relation": None,
        "question_object": None,
        "what_changed": (
            "Scoped PathLike async file-reading to the async client. Expanded "
            "the evidence boundary backwards to the sentence that names the async client."
        ),
    },
    "V2D-38": {
        "question": (
            "If you previously relied on `temperature` for design variety, what "
            "approach should you use?"
        ),
        "answer": (
            "Have the model propose options before building; it produces meaningfully "
            "different directions across runs."
        ),
        "atomic_claims": [
            (
                "If you previously relied on `temperature` for design variety, have "
                "the model propose options before building; it produces meaningfully "
                "different directions across runs."
            ),
        ],
        "critical_strings": ["temperature", "propose options before building"],
        "question_subject": "`temperature` for design variety",
        "question_relation": None,
        "question_object": "have the model propose options before building",
        "what_changed": (
            "Replaced 'this approach' with the explicit approach from the preceding "
            "heading: have the model propose options before building. Expanded the "
            "evidence boundary backwards to that heading."
        ),
    },
    "V2D-44": {
        "question": (
            "What setting should you add when a streaming Chat Completions provider "
            "requires an explicit usage request?"
        ),
        "answer": "`ModelSettings(include_usage=True)`.",
        "atomic_claims": [
            (
                "When a streaming Chat Completions provider requires an explicit usage "
                "request, also set `ModelSettings(include_usage=True)`."
            ),
        ],
        "critical_strings": ["include_usage"],
        "question_subject": "a streaming Chat Completions provider that requires an explicit usage request",
        "question_relation": None,
        "question_object": "`ModelSettings(include_usage=True)`",
        "what_changed": (
            "Rewrote the malformed question to ask what setting to add when a "
            "streaming Chat Completions provider requires an explicit usage request. "
            "Span unchanged."
        ),
    },
    "V2D-50": {
        "question": (
            "What happens when you use any GPT-5 model such as `gpt-5.6-sol` as the "
            "default model via `OPENAI_DEFAULT_MODEL` or `RunConfig`?"
        ),
        "answer": "The SDK applies default `ModelSettings`.",
        "atomic_claims": [
            (
                "When you use any GPT-5 model such as `gpt-5.6-sol` as the default "
                "model via `OPENAI_DEFAULT_MODEL` or `RunConfig`, the SDK applies "
                "default `ModelSettings`."
            ),
        ],
        "critical_strings": ["gpt-5.6-sol", "OPENAI_DEFAULT_MODEL", "RunConfig", "ModelSettings"],
        "question_subject": "any GPT-5 model such as `gpt-5.6-sol` used as the default via `OPENAI_DEFAULT_MODEL` or `RunConfig`",
        "question_relation": None,
        "question_object": "default `ModelSettings`",
        "what_changed": (
            "Replaced 'in this way' with the explicit default-model / `RunConfig` "
            "configuration path. Expanded the evidence boundary backwards to that path."
        ),
    },
}


def apply_one(orig: dict, verdict: dict, text: str, now: str, now_et: str) -> dict:
    cid = orig["candidate_id"]
    rec = copy.deepcopy(orig)
    rewrite = REWRITES[cid]
    old_start, old_end = orig["char_start"], orig["char_end"]
    old_text = orig["evidence_text"]
    old_hash = orig["evidence_hash"]
    if sha(old_text) != old_hash:
        raise SystemExit(f"{cid}: stored hash already stale vs stored text")
    if text[old_start:old_end] != old_text:
        raise SystemExit(f"{cid}: frozen corpus slice does not match stored evidence")
    if sha(text[old_start:old_end]) != old_hash:
        raise SystemExit(f"{cid}: frozen corpus hash mismatch")
    if rec["version_id"] != orig["version_id"]:
        raise SystemExit(f"{cid}: version_id mutated")

    if cid in EXPAND_IDS:
        if verdict.get("evidence_boundary_complete") is not False:
            raise SystemExit(f"{cid}: expansion planned but ChatGPT said boundary complete")
        spec = EXPANSIONS[cid]
        new_start, new_end = locate(text, spec["head"], spec["tail"], old_start, old_end)
        check_superset(text, (new_start, new_end), (old_start, old_end))
    else:
        if cid in EXPANSIONS:
            raise SystemExit(f"{cid}: expansion table vs EXPAND_IDS mismatch")
        new_start, new_end = old_start, old_end

    new_text = text[new_start:new_end]
    if len(new_text) > EVIDENCE_HARD_CAP:
        raise SystemExit(f"{cid}: new evidence {len(new_text)} exceeds hard cap {EVIDENCE_HARD_CAP}")
    new_hash = sha(new_text)
    if new_text != text[new_start:new_end]:
        raise SystemExit(f"{cid}: evidence_text not sliced from frozen corpus")

    for s in rewrite["critical_strings"]:
        if not contains_claim_string(new_text, s):
            raise SystemExit(f"{cid}: critical string {s!r} not in new evidence")
    # keep any old critical strings that are still present
    kept_old = [s for s in (orig.get("critical_strings") or []) if contains_claim_string(new_text, s)]
    critical = []
    for s in rewrite["critical_strings"] + kept_old:
        if s not in critical:
            critical.append(s)

    for claim in rewrite["atomic_claims"]:
        # claims may paraphrase; critical strings must still be inside evidence
        pass
    if has_markdown_link(rewrite["question"]):
        raise SystemExit(f"{cid}: markdown link in question")

    revision = {
        "revision": 1,
        "round": 1,
        "reason": "chatgpt_round1_FIX_REQUIRED",
        "chatgpt_reason": verdict.get("reason"),
        "evidence_boundary_complete": verdict.get("evidence_boundary_complete"),
        "old_question": orig["question"],
        "old_proposed_question": orig.get("proposed_question"),
        "old_answer": orig["answer"],
        "old_atomic_claims": orig.get("atomic_claims"),
        "old_char_start": old_start,
        "old_char_end": old_end,
        "old_evidence_text": old_text,
        "old_evidence_hash": old_hash,
        "old_question_subject": orig.get("question_subject"),
        "old_question_relation": orig.get("question_relation"),
        "old_question_object": orig.get("question_object"),
        "new_question": rewrite["question"],
        "new_answer": rewrite["answer"],
        "new_char_start": new_start,
        "new_char_end": new_end,
        "new_evidence_hash": new_hash,
        "span_expanded": (new_start, new_end) != (old_start, old_end),
        "characters_added_before": old_start - new_start,
        "characters_added_after": new_end - old_end,
        "author": "claude",
        "directed_by": "ChatGPT round-1 FIX_REQUIRED + owner apply",
        "timestamp": now,
        "timestamp_et": now_et,
        "what_changed": rewrite["what_changed"],
    }
    if cid in EXPANSIONS:
        revision["expansion_why"] = EXPANSIONS[cid]["why"]

    rec["revisions"] = [revision]
    rec["question"] = rewrite["question"]
    rec["proposed_question"] = rewrite["question"]
    rec["answer"] = rewrite["answer"]
    rec["proposed_answer"] = rewrite["answer"]
    rec["atomic_claims"] = list(rewrite["atomic_claims"])
    rec["proposed_atomic_claims"] = list(rewrite["atomic_claims"])
    rec["char_start"] = new_start
    rec["char_end"] = new_end
    rec["evidence_text"] = new_text
    rec["evidence_hash"] = new_hash
    rec["evidence_char_length"] = new_end - new_start
    rec["context_before"] = text[max(0, new_start - CONTEXT_KEEP):new_start]
    rec["context_after"] = text[new_end:new_end + CONTEXT_KEEP]
    rec["critical_strings"] = critical
    rec["question_subject"] = rewrite["question_subject"]
    rec["question_relation"] = rewrite["question_relation"]
    rec["question_object"] = rewrite["question_object"]
    rec["verification_status"] = STATUS_AFTER
    rec["chatgpt_verified"] = False
    rec["round1_verdict"] = "FIX_REQUIRED"
    rec["round1_reason"] = verdict.get("reason")
    rec["repaired_at"] = now
    rec["repaired_at_et"] = now_et
    rec["frozen"] = False
    rec["human_verified"] = False
    rec["version_id"] = orig["version_id"]
    rec["retrieval_was_not_run"] = True

    # expected_evidence
    ev = copy.deepcopy(orig["expected_evidence"][0])
    ev["version_id"] = orig["version_id"]
    ev["char_start"] = new_start
    ev["char_end"] = new_end
    ev["evidence_text"] = new_text
    ev["evidence_hash"] = new_hash
    ev["evidence_char_length"] = new_end - new_start
    ev["critical_strings"] = critical
    rec["expected_evidence"] = [ev]

    attach_triples(rec)

    notes = orig.get("generator_notes") or ""
    repair_note = f"round1 repair: {rewrite['what_changed']}"
    rec["generator_notes"] = (notes + " | " if notes else "") + repair_note
    return rec, revision


def checks(rec: dict, orig: dict, text: str, verdict: dict) -> list[str]:
    cid = rec["candidate_id"]
    warnings = []
    if rec["version_id"] != orig["version_id"]:
        raise SystemExit(f"{cid}: version_id changed")
    body = rec["evidence_text"]
    if body != text[rec["char_start"]:rec["char_end"]]:
        raise SystemExit(f"{cid}: evidence_text != frozen slice")
    if rec["evidence_hash"] != sha(body):
        raise SystemExit(f"{cid}: hash != sha256(frozen slice)")
    if rec["verification_status"] != STATUS_AFTER:
        raise SystemExit(f"{cid}: bad status {rec['verification_status']}")
    if rec.get("human_verified"):
        raise SystemExit(f"{cid}: must not be human_verified")
    if rec.get("frozen"):
        raise SystemExit(f"{cid}: must not be frozen")
    for s in rec["critical_strings"]:
        if not contains_claim_string(body, s):
            raise SystemExit(f"{cid}: critical {s!r} missing from evidence")
    wf = wellformed_problem(body)
    if wf:
        warnings.append(f"wellformed_problem: {wf}")
    qf = question_form(rec["question"], body)
    if qf.get("status") != "OK":
        warnings.append(f"questionform {qf['status']}: {qf.get('finding')}")
    ana = evaluate_span(body, rec)
    rec["anaphora_check"] = {
        "status": ana.get("status"),
        "blocking": ana.get("blocking"),
        "finding": ana.get("finding"),
        "phrase": ana.get("phrase"),
    }
    if ana.get("status") == "CRITICAL_ANAPHORA":
        warnings.append(f"CRITICAL anaphora: {ana.get('finding')}")
    if rec.get("question_relation") in relations.RELATION_PATTERNS:
        src = {
            "source_subject": rec.get("source_subject"),
            "source_relation": rec.get("source_relation") or rec.get("question_relation"),
            "source_object": rec.get("source_object"),
        }
        q = {
            "question_subject": rec.get("question_subject"),
            "question_object": rec.get("question_object"),
        }
        d = relations.direction(src, q)
        rec["relation_direction_check"] = d.get("status")
        if d.get("status") in {"REVERSED", "SUBJECT_MISMATCH"}:
            warnings.append(f"relation {d.get('status')}: {d.get('finding')}")
    if verdict.get("evidence_boundary_complete") is False:
        if rec["char_start"] == orig["char_start"] and rec["char_end"] == orig["char_end"]:
            warnings.append("ChatGPT said boundary incomplete but span was not expanded")
    else:
        if rec["char_start"] != orig["char_start"] or rec["char_end"] != orig["char_end"]:
            raise SystemExit(f"{cid}: expanded although ChatGPT said boundary complete")
    rec["repair_warnings"] = warnings
    return warnings


def fence(text: str) -> str:
    return "```\n" + text + "\n```"


def render_experiments_md(payload: dict) -> str:
    lines = [
        "# V2-DEVSET-001 round-1 repairs (16 FIX_REQUIRED)",
        "",
        (
            f"Written {payload['generated_at']} ({payload['generated_at_et']}). "
            "**Nothing is gold. Nothing is frozen.** Status of every repaired record: "
            f"`{STATUS_AFTER}`."
        ),
        "",
        (
            "ChatGPT round-1: PASS 34, FIX_REQUIRED 16, FAIL 0. The 34 PASS cases "
            "were **not** imported as frozen gold and are **not** in this file. "
            "Holdout.json was not opened. Retrieval was not run. SYSTEM-D / SYSTEM-E "
            "were not run. Live docs were not fetched. `version_id` is unchanged on "
            "every case. Spans were expanded only where ChatGPT set "
            "`evidence_boundary_complete=false`. Evidence hashes were recomputed from "
            f"frozen corpus snapshot `{SNAPSHOT}`."
        ),
        "",
        f"- source packet: `{payload['source_packet']}`",
        f"- verdicts: `{payload['verdicts_file']}`",
        f"- n repaired: **{payload['n_repaired']}**",
        f"- PASS untouched (not imported as gold): {len(payload['pass_ids_not_imported_as_gold'])}",
        "",
        "## The 16 new questions",
        "",
    ]
    for rec in payload["records"]:
        lines.append(f"- **{rec['candidate_id']}**: {rec['question']}")
    lines += ["", "---", ""]
    for rec in payload["records"]:
        rev = rec["revisions"][0]
        lines += [
            f"## {rec['candidate_id']}",
            "",
            f"**Document.** {rec['provider']} · {rec['document_title']}",
            "",
            f"**ChatGPT reason.** {rev['chatgpt_reason']}",
            "",
            f"**Before Q.** {rev['old_question']}",
            "",
            f"**After Q.** {rec['question']}",
            "",
            f"**Before A.** {rev['old_answer']}",
            "",
            f"**After A.** {rec['answer']}",
            "",
            "**After claims**",
            "",
        ]
        for i, c in enumerate(rec["atomic_claims"], 1):
            lines.append(f"{i}. {c}")
        lines += [
            "",
            (
                f"**After evidence** — `{rec['version_id']}` "
                f"{rec['char_start']}–{rec['char_end']} "
                f"({rec['evidence_char_length']} chars) · `{rec['evidence_hash']}`"
            ),
            "",
            fence(rec["evidence_text"]),
            "",
            (
                f"**Before evidence** — {rev['old_char_start']}–{rev['old_char_end']} "
                f"({rev['old_char_end'] - rev['old_char_start']} chars) · "
                f"`{rev['old_evidence_hash']}`"
            ),
            "",
            fence(rev["old_evidence_text"]),
            "",
            (
                f"**Span.** {'expanded' if rev['span_expanded'] else 'unchanged'} "
                f"(+{rev['characters_added_before']} before, "
                f"+{rev['characters_added_after']} after). "
                f"`version_id` kept `{rec['version_id']}`."
            ),
            "",
            f"**What changed.** {rev['what_changed']}",
            "",
            f"**Status.** `{rec['verification_status']}` — not gold, not frozen.",
            "",
            "---",
            "",
        ]
    return "\n".join(lines)


def render_review_md(payload: dict) -> str:
    lines = [
        "# V2-DEVSET-001 round-1 repair review (16 FIX_REQUIRED only)",
        "",
        (
            f"**16 repaired candidates · corpus snapshot `{SNAPSHOT}` · "
            f"generated {payload['generated_at']} ({payload['generated_at_et']})**"
        ),
        "",
        (
            "This packet is **only** the 16 cases ChatGPT marked `FIX_REQUIRED` in "
            "round 1. The 34 PASS cases are **not** in this file and must **not** be "
            "imported as frozen gold."
        ),
        "",
        (
            "Every candidate here is `candidate_unverified_after_fix`. Nothing is "
            "ground truth. The evidence is quoted verbatim from the frozen corpus "
            "and is authoritative for this review — **do not consult live "
            "documentation**, which may have changed since the snapshot."
        ),
        "",
        (
            "Judge the *repaired* question, answer and claims against the evidence "
            "and its surrounding context only. Return one record per candidate with "
            "verdict `PASS | FAIL | FIX_REQUIRED | UNCERTAIN` and the GOLD review "
            "fields in `docs/GOLD-REVIEW-PROCEDURE.md`."
        ),
        "",
        (
            "Spans were expanded only where round 1 set `evidence_boundary_complete="
            "false`. Hashes were recomputed from the frozen snapshot. `version_id` "
            "is unchanged. Old question/span are in each case's repair history."
        ),
        "",
        "---",
        "",
    ]
    for rec in payload["records"]:
        rev = rec["revisions"][0]
        path = " › ".join(rec.get("section_path") or [])
        lines += [
            f"## {rec['candidate_id']}",
            "",
            f"- **provider**: {rec['provider']}",
            f"- **document**: {rec['document_title']}",
            f"- **section**: {path}",
            f"- **source span**: `{rec['version_id']}` chars {rec['char_start']}–{rec['char_end']}",
            f"- **evidence kind**: `{rec['evidence_kind']}`",
            f"- **evidence shape**: `{rec.get('evidence_shape')}`",
            f"- **reasoning type**: `{rec.get('reasoning_type')}`",
            f"- **stress types**: {', '.join(rec.get('stress_types') or []) or '_none_'}",
            f"- **binding**: {rec.get('binding')}",
            f"- **verification status**: `{rec['verification_status']}`",
            f"- **round-1 verdict**: FIX_REQUIRED",
            f"- **span expanded this round**: {str(rev['span_expanded']).lower()}",
            "",
            "**Repaired question** (a suggestion, not gold)",
            "",
            f"> {rec['question']}",
            "",
            f"**Repaired answer**: {rec['answer']}",
            "",
            "**Repaired atomic claims**:",
            "",
        ]
        for i, c in enumerate(rec["atomic_claims"], 1):
            lines.append(f"{i}. {c}")
        lines += [
            "",
            f"**Critical strings**: {', '.join(rec.get('critical_strings') or [])}",
            "",
            f"**What changed.** {rev['what_changed']}",
            "",
            f"**Round-1 ChatGPT reason.** {rev['chatgpt_reason']}",
            "",
        ]
        for span in rec["expected_evidence"]:
            lines += [
                f"### Evidence {span['evidence_id']} (verbatim, authoritative)",
                "",
                f"`{span['version_id']}` chars {span['char_start']}–{span['char_end']} "
                f"· hash `{span['evidence_hash']}`",
                "",
                fence(span["evidence_text"]),
                "",
            ]
        lines += [
            "<details><summary>Context before</summary>",
            "",
            fence((rec.get("context_before") or "")[-CONTEXT_KEEP:]),
            "",
            "</details>",
            "",
            "<details><summary>Context after</summary>",
            "",
            fence((rec.get("context_after") or "")[:CONTEXT_KEEP]),
            "",
            "</details>",
            "",
            "<details><summary>Repair history (old question / old span)</summary>",
            "",
            f"**Old question.** {rev['old_question']}",
            "",
            f"**Old answer.** {rev['old_answer']}",
            "",
            (
                f"**Old evidence** — `{rec['version_id']}` "
                f"{rev['old_char_start']}–{rev['old_char_end']} · "
                f"`{rev['old_evidence_hash']}`"
            ),
            "",
            fence(rev["old_evidence_text"]),
            "",
            "</details>",
            "",
            "---",
            "",
        ]
    return "\n".join(lines)


def update_status(payload: dict) -> None:
    extra = f"""

## Round-1 ChatGPT verdicts applied (not a freeze)

Written {payload['generated_at']} ({payload['generated_at_et']}).

| | |
| --- | --- |
| round-1 PASS | **34** — **not** imported as frozen gold; **not** changed |
| round-1 FIX_REQUIRED | **16** — repaired; status `{STATUS_AFTER}` |
| round-1 FAIL | **0** |
| frozen | **false** |
| retrieval run | **false** |
| holdout.json opened | **false** |
| SYSTEM-D / SYSTEM-E | **not run** |
| live docs fetched | **false** |

Repairs: `experiments/RAG-V2/V2-DEVSET-001/v2_devset_001_repairs_round1.json` + `.md`. ChatGPT-ready review of the 16 only: `evals/review/v2_devset_001_repairs_round1.md` (copied to `/home/box/Downloads/v2_devset_001_repairs_round1.md`). Original 50-case packet at `evals/review/v2_devset_001_batch_001.json` is unchanged (the 34 PASS questions/spans are byte-identical).

The 16 new questions:

"""
    for rec in payload["records"]:
        extra += f"- `{rec['candidate_id']}` {rec['question']}\n"
    extra += """
Next step: independent ChatGPT review of the **16 repairs**, then Russell human QC, **then** freeze. Do not run SYSTEM-D or SYSTEM-E. Do not start EXP-017.
"""
    original = STATUS.read_text()
    if "## Round-1 ChatGPT verdicts applied" in original:
        # replace from that heading to EOF
        head = original.split("## Round-1 ChatGPT verdicts applied")[0].rstrip() + "\n"
        STATUS.write_text(head + extra)
    else:
        STATUS.write_text(original.rstrip() + extra)


def main() -> int:
    now_dt = datetime.now(ZoneInfo("UTC"))
    now = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    now_et = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M ET")

    packet = json.loads(PACKET.read_text())
    verdicts = json.loads(VERDICTS.read_text())
    vmap = {r["candidate_id"]: r for r in verdicts["records"]}
    fix_ids = list(verdicts["fix_ids"])
    pass_ids = list(verdicts["pass_ids"])
    if set(fix_ids) != set(REWRITES):
        raise SystemExit(f"rewrite table mismatch: {set(fix_ids) ^ set(REWRITES)}")
    if len(pass_ids) != 34 or len(fix_ids) != 16:
        raise SystemExit(f"unexpected counts PASS={len(pass_ids)} FIX={len(fix_ids)}")

    orig_by_id = {r["candidate_id"]: r for r in packet["records"]}
    for pid in pass_ids:
        if orig_by_id[pid]["verification_status"] != "candidate_unverified":
            raise SystemExit(f"PASS {pid} has unexpected status")

    texts = load_frozen(sorted({orig_by_id[i]["version_id"] for i in fix_ids}))

    repaired = []
    all_warnings = {}
    for cid in fix_ids:
        orig = orig_by_id[cid]
        verdict = vmap[cid]
        if verdict["verdict"] != "FIX_REQUIRED":
            raise SystemExit(f"{cid} not FIX_REQUIRED")
        rec, _rev = apply_one(orig, verdict, texts[orig["version_id"]], now, now_et)
        warns = checks(rec, orig, texts[orig["version_id"]], verdict)
        all_warnings[cid] = warns
        repaired.append(rec)
        print(f"{cid}: span {orig['char_start']}-{orig['char_end']} -> "
              f"{rec['char_start']}-{rec['char_end']} ({rec['evidence_char_length']} chars) "
              f"expanded={rec['revisions'][0]['span_expanded']} warnings={warns}")

    payload = {
        "task": "V2-DEVSET-001",
        "round": 1,
        "schema_version": "v2-devset-001/1.0",
        "generated_at": now,
        "generated_at_et": now_et,
        "corpus_snapshot": SNAPSHOT,
        "source_packet": "evals/review/v2_devset_001_batch_001.json",
        "verdicts_file": "experiments/RAG-V2/V2-DEVSET-001/chatgpt-verdicts-round1.json",
        "n_repaired": 16,
        "n_pass_untouched": 34,
        "n_fail": 0,
        "fix_ids": fix_ids,
        "pass_ids_not_imported_as_gold": pass_ids,
        "status_after_fix": STATUS_AFTER,
        "frozen": False,
        "holdout_json_opened": False,
        "retrieval_was_not_run": True,
        "systems_executed": [],
        "live_docs_fetched": False,
        "pass_imported_as_frozen_gold": False,
        "original_packet_mutated": False,
        "repair_warnings": all_warnings,
        "records": repaired,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    OUT_MD_EXP.write_text(render_experiments_md(payload))
    review_md = render_review_md(payload)
    OUT_MD_REVIEW.write_text(review_md)
    OUT_DOWNLOADS.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(OUT_MD_REVIEW, OUT_DOWNLOADS)
    update_status(payload)

    print("wrote", OUT_JSON, OUT_JSON.stat().st_size)
    print("wrote", OUT_MD_EXP, OUT_MD_EXP.stat().st_size)
    print("wrote", OUT_MD_REVIEW, OUT_MD_REVIEW.stat().st_size)
    print("copied", OUT_DOWNLOADS, OUT_DOWNLOADS.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
