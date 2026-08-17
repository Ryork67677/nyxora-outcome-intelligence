from __future__ import annotations

import hashlib
import json
from pathlib import Path

from rag_v1.evals.io import load_cases, write_json
from rag_v1.retrieval import dense_search, interleave_hybrid, lexical_search, rrf_fuse
from rag_v1.types import EvidenceRef, RetrievalCaseResult, SearchHit


def _overlap(hit: SearchHit, ref: EvidenceRef) -> bool:
    return (
        hit.version_id == ref.version_id
        and hit.section_path == ref.section_path
        and hit.char_start < ref.char_end
        and hit.char_end > ref.char_start
    )


def score_evidence(hits: list[SearchHit], refs: list[EvidenceRef], case_id: str, category: str, k: int):
    found: list[EvidenceRef] = []
    missed: list[EvidenceRef] = []
    for ref in refs:
        if any(_overlap(h, ref) for h in hits[:k]):
            found.append(ref)
        else:
            missed.append(ref)
    denom = len(refs)
    recall = len(found) / denom if denom else 1.0
    return RetrievalCaseResult(
        case_id=case_id,
        category=category,
        k=k,
        expected_evidence_count=denom,
        evidence_found_count=len(found),
        recall=recall,
        found=found,
        missed=missed,
        hits=hits[:k],
    )


def redact_hit(hit: dict) -> dict:
    """Drop retrieved provider prose from a published result record.

    Experiment results have to be publishable, but a hit carries the chunk text
    verbatim and the corpus is copied provider documentation that this repository
    deliberately does not redistribute. Everything the analysis actually uses —
    version, section path, char span, rank, score, retriever attribution — is
    kept, plus a content hash and length so a redacted record can still be tied
    back to the exact chunk in a local database.

    Use ``--include-text`` to write an unredacted trace file for local debugging;
    that path is gitignored.
    """
    text = hit.pop("text", "") or ""
    hit["text_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    hit["text_len"] = len(text)
    return hit


def run_retrieval_eval(
    golden_path: Path,
    snapshot_id: str,
    mode: str,
    k: int,
    output_path: Path,
    model_id: str | None = None,
    lexical_k: int = 30,
    dense_k: int = 30,
    rrf_k: int = 60,
    include_text: bool = False,
):
    cases = load_cases(golden_path)
    results = []
    for case in cases:
        if case.expected_abstain and not case.expected_evidence:
            continue
        if mode == "lexical":
            hits = lexical_search(case.question, snapshot_id, k=max(k, lexical_k))
        elif mode == "dense":
            if not model_id:
                raise ValueError("--model-id is required for dense mode")
            hits = dense_search(case.question, snapshot_id, model_id, k=max(k, dense_k))
        elif mode in {"hybrid", "rrf"}:
            if not model_id:
                raise ValueError("--model-id is required for hybrid/rrf mode")
            lex = lexical_search(case.question, snapshot_id, k=lexical_k)
            den = dense_search(case.question, snapshot_id, model_id, k=dense_k)
            hits = interleave_hybrid(lex, den, k=k) if mode == "hybrid" else rrf_fuse([lex, den], rrf_k=rrf_k, top_k=k)
        else:
            raise ValueError(f"Unsupported mode: {mode}")
        results.append(score_evidence(hits, case.expected_evidence, case.case_id, case.category, k))

    recalls = [r.recall for r in results]
    full = [r for r in results if r.recall >= 1.0]
    cases = [r.model_dump() for r in results]

    if include_text:
        trace_path = output_path.with_name(output_path.stem + "-traces.jsonl")
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        trace_path.write_text(
            "\n".join(json.dumps(c, ensure_ascii=False, default=str) for c in cases) + "\n",
            encoding="utf-8",
        )
        cases = [r.model_dump() for r in results]

    for case in cases:
        case["hits"] = [redact_hit(h) for h in case["hits"]]

    payload = {
        "mode": mode,
        "snapshot_id": snapshot_id,
        "k": k,
        "model_id": model_id,
        "lexical_k": lexical_k if mode in {"lexical", "hybrid", "rrf"} else None,
        "dense_k": dense_k if mode in {"dense", "hybrid", "rrf"} else None,
        "rrf_k": rrf_k if mode == "rrf" else None,
        "macro_recall": sum(recalls) / len(recalls) if recalls else None,
        "cases_fully_recalled": len(full),
        "cases_total": len(results),
        "hit_text_redacted": True,
        "cases": cases,
    }
    write_json(output_path, payload)
    return payload
