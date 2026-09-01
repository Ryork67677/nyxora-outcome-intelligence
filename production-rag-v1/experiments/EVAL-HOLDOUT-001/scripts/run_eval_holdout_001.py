#!/usr/bin/env python3
"""EVAL-HOLDOUT-001: one-shot holdout of frozen SYSTEM-D-GUARD-BLEND.

FIRST and ONLY holdout run. SYSTEM-D only. Does not retune. Does not change
weights, CE, pool, or blend after seeing any case. Does not debug individual
holdout failures mid-run. Does not run answer generation. Does not evaluate
SYSTEM-A as a competing holdout system (A top-100 is D candidate generation).

Does not load development or validation for scoring or cherry-picking.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EXP015_SCRIPTS = ROOT / "experiments" / "EXP-015" / "scripts"
if str(EXP015_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(EXP015_SCRIPTS))

from cross_encoder import (  # noqa: E402
    CE_NAME,
    CE_ONNX,
    CE_REVISION,
    CE_SHA256,
    MAX_LENGTH,
    CrossEncoderReranker,
)
from rag_v1.db import connect  # noqa: E402
from rag_v1.eval.exposure import spans_of  # noqa: E402
from rag_v1.eval.splits import load as load_split  # noqa: E402
from rag_v1.embedders_transformer import TransformerEncoder  # noqa: E402
from rag_v1.gold.mining import _section_for  # noqa: E402
from rag_v1.ids import config_hash  # noqa: E402
from rag_v1.parsing import _sections_from_markdown  # noqa: E402
from rag_v1.query_cache import CachedQueryEmbedder  # noqa: E402
from rag_v1.retrieval import dense_search, lexical_search, rrf_fuse  # noqa: E402
from rag_v1.systems import (  # noqa: E402
    CHUNK_SET,
    FROZEN_HASHES,
    SNAPSHOT,
    TRANSFORMER_FINGERPRINT,
    TRANSFORMER_MODEL,
)
from rag_v1.types import EvalCase, EvidenceRef, SearchHit  # noqa: E402

PROBE_DEPTHS = (10, 20, 30, 50, 100, 300)
TOP_K, RRF_POOL, RRF_K, CANDIDATE_POOL = 10, 50, 60, 100
A_HASH = "9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38"
EXPECTED_D_HASH = "d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a"
EXPECTED_RELEASE_SHA256 = "1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40"
EXPECTED_HOLDOUT_SHA256 = "756a3a9bc74ce3e2dd3a7924c4048984a0ae5e74237bc8053e18b6fec202d914"
BLEND_CE, BLEND_A = 0.7, 0.3
GOLD_SOURCES = {
    "001": "evals/gold/batch_001_v2/overlay.json",
    "002": "evals/review/gold_review_batch_002.json",
    "003": "evals/review/gold_review_batch_003.json",
    "004": "evals/review/gold_review_batch_004_final.json",
    "005": "evals/review/gold_review_batch_005_final.json",
    "006": "evals/review/gold_review_batch_006_final.json",
    "HA": "evals/review/gold_review_HA01_HA60_final.json",
}
CATEGORY_MAP = {
    "exact_lookup": "exact_lookup",
    "genuine_multi_hop": "multi_hop",
    "ambiguity_disambiguation": "ambiguous",
}
RELEASE = ROOT / "experiments" / "EVAL-HOLDOUT-001" / "SYSTEM-D-RELEASE.json"
MANIFEST = ROOT / "experiments" / "EVAL-HOLDOUT-001" / "EVAL-HOLDOUT-001-manifest.json"
SOURCE_FREEZE = ROOT / "experiments" / "EXP-016" / "SYSTEM-D-GUARD.json"
HOLDOUT_JSON = ROOT / "evals" / "splits" / "gold150-v1" / "holdout.json"
HOLDOUT_LOCK = ROOT / "evals" / "splits" / "gold150-v1" / "holdout.lock.json"
ACCESS_LOG = ROOT / "evals" / "splits" / "gold150-v1" / "holdout-access.log.jsonl"
OUT_DIR = ROOT / "experiments" / "EVAL-HOLDOUT-001"


def holdout_log_bytes() -> int:
    return ACCESS_LOG.stat().st_size if ACCESS_LOG.exists() else -1


def overlaps(hit: SearchHit, ref: EvidenceRef) -> bool:
    return (
        hit.version_id == ref.version_id
        and list(hit.section_path) == list(ref.section_path)
        and hit.char_start < ref.char_end
        and hit.char_end > ref.char_start
    )


def embedding_status() -> dict:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (CHUNK_SET,))
        chunks = cur.fetchone()[0]
        cur.execute(
            "SELECT count(*), min(model_fingerprint), max(model_fingerprint) "
            "FROM chunk_embedding WHERE model_id=%s",
            (TRANSFORMER_MODEL,),
        )
        n, fp_min, fp_max = cur.fetchone()
    return {
        "chunk_set": CHUNK_SET,
        "chunks": chunks,
        "embedding_rows": n,
        "model_id": TRANSFORMER_MODEL,
        "fingerprint_min": fp_min,
        "fingerprint_max": fp_max,
        "fingerprint_expected": TRANSFORMER_FINGERPRINT,
        "complete": n == chunks == 14209 and fp_min == fp_max == TRANSFORMER_FINGERPRINT,
    }


def retrieve_system_a_pool(query: str, embedder) -> list[SearchHit]:
    """Candidate generation for D. Not an A holdout evaluation."""
    lexical = lexical_search(query, SNAPSHOT, RRF_POOL)
    dense = dense_search(query, SNAPSHOT, TRANSFORMER_MODEL, RRF_POOL, embedder=embedder)
    return rrf_fuse([lexical, dense], rrf_k=RRF_K, top_k=CANDIDATE_POOL)


def minmax_norm(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5] * len(values)
    scale = hi - lo
    return [(v - lo) / scale for v in values]


def apply_blend(rows: list[dict]) -> list[dict]:
    """Frozen SYSTEM-D-GUARD-BLEND. Do not retune weights or tie-break."""
    ce_n = minmax_norm([r["ce_score"] for r in rows])
    a_n = minmax_norm([r["a_score"] for r in rows])
    blended = []
    for row, ce, a in zip(rows, ce_n, a_n, strict=True):
        item = dict(row)
        item["ce_norm"] = ce
        item["a_norm"] = a
        item["blend_score"] = BLEND_CE * ce + BLEND_A * a
        blended.append(item)
    blended.sort(key=lambda r: (-r["blend_score"], r["a_rank"], r["chunk_id"]))
    for i, row in enumerate(blended, start=1):
        row["d_rank"] = i
    return blended


def score_case(case, hits) -> dict:
    spans = []
    for ref in case.expected_evidence:
        hit = next((h for h in hits if overlaps(h, ref)), None)
        doc_rank = next((h.rank for h in hits if h.version_id == ref.version_id), None)
        spans.append(
            {
                "rank": hit.rank if hit else None,
                "doc_rank": doc_rank,
                "chunk_id": hit.chunk_id if hit else None,
                "within": {
                    str(d): (hit is not None and hit.rank <= d) for d in PROBE_DEPTHS
                },
                "doc_within_10": doc_rank is not None and doc_rank <= TOP_K,
            }
        )
    found = sum(1 for s in spans if s["within"]["10"])
    return {
        "case_id": case.case_id,
        "spans": spans,
        "recall": found / len(spans) if spans else 1.0,
        "fully_recalled": bool(spans) and found == len(spans),
        "doc_recall": (
            sum(1 for s in spans if s["doc_within_10"]) / len(spans) if spans else 1.0
        ),
    }


def hits_from_blend(rows: list[dict]) -> list[SearchHit]:
    hits = []
    for row in rows:
        hits.append(
            SearchHit(
                chunk_id=row["chunk_id"],
                version_id=row["version_id"],
                section_path=list(row["section_path"]),
                char_start=row["char_start"],
                char_end=row["char_end"],
                text="",
                score=float(row["blend_score"]),
                rank=int(row["d_rank"]),
                retriever="system_d_blend",
                metadata={
                    "ce_score": row["ce_score"],
                    "a_rank": row["a_rank"],
                    "a_score": row["a_score"],
                    "blend_score": row["blend_score"],
                },
            )
        )
    return hits


def summarise(per_case: dict, system: str, config_hash_value: str) -> dict:
    all_spans = [s for c in per_case.values() for s in c["spans"]]
    recalls = [c["recall"] for c in per_case.values()]
    return {
        "system": system,
        "config_hash": config_hash_value,
        "macro_span_recall": round(sum(recalls) / len(recalls), 4),
        "cases_fully_recalled": sum(1 for c in per_case.values() if c["fully_recalled"]),
        "cases_total": len(per_case),
        "strict_recall_at_10": (
            f"{sum(1 for c in per_case.values() if c['fully_recalled'])}/{len(per_case)}"
        ),
        "spans_found_at_10": sum(1 for s in all_spans if s["within"]["10"]),
        "spans_total": len(all_spans),
        "document_recall": round(
            sum(c["doc_recall"] for c in per_case.values()) / len(per_case), 4
        ),
        "mrr": round(
            sum(1 / s["rank"] for s in all_spans if s["rank"]) / len(all_spans), 4
        ),
        "spans_absent_from_top": {
            str(d): sum(1 for s in all_spans if not s["within"][str(d)])
            for d in PROBE_DEPTHS
        },
    }


def frozen_d_hash(a_hash: str) -> str:
    return config_hash(
        {
            "name": "SYSTEM-D-GUARD-BLEND",
            "control": a_hash,
            "pool": CANDIDATE_POOL,
            "weights": [BLEND_CE, BLEND_A],
            "minmax_degenerate": 0.5,
            "ce_sha256": CE_SHA256,
            "tie_break": "blend desc, A rank, chunk_id",
        }
    )


def load_gold_allowlist(allow: set[str]) -> dict[str, dict]:
    records: dict[str, dict] = {}
    for group, rel in GOLD_SOURCES.items():
        payload = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        for record in payload.get("records") or payload.get("case_records") or []:
            cid = record.get("candidate_id")
            if cid not in allow:
                continue
            if record.get("verification_status") == "human_verified" or record.get(
                "human_verified"
            ):
                records[cid] = {"group": group, **record}
    return records


def derived_sections() -> dict:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT version_id, normalized_text FROM document_version WHERE status='current'"
        )
        return {
            version: _sections_from_markdown(text) for version, text in cur.fetchall()
        }


def project_holdout_cases(case_ids: list[str]) -> tuple[list[EvalCase], list[dict], dict]:
    allow = set(case_ids)
    gold = load_gold_allowlist(allow)
    missing = sorted(allow - set(gold))
    if missing:
        raise SystemExit(f"STOP: holdout cases missing from gold sources: {missing}")
    extra = sorted(set(gold) - allow)
    if extra:
        raise SystemExit("STOP: non-holdout IDs leaked into projection")
    sections = derived_sections()
    cases: list[EvalCase] = []
    meta: list[dict] = []
    derived_count = 0
    derived_case_ids: list[str] = []
    skipped = []
    for case_id in case_ids:
        record = gold[case_id]
        spans = spans_of(record)
        refs = []
        derived_this = False
        for span in spans:
            source = next(
                (
                    s
                    for s in (record.get("expected_evidence") or [])
                    if s.get("char_start") == span["char_start"]
                    and s.get("version_id") == span["version_id"]
                ),
                record,
            )
            section = source.get("section_path") or (
                record.get("section_path")
                if not (record.get("expected_evidence") or [])
                else None
            )
            if not section:
                section = _section_for(sections[span["version_id"]], span["char_start"])
                derived_count += 1
                derived_this = True
            if not section:
                skipped.append({"case_id": case_id, "reason": "no section_path"})
                continue
            refs.append(
                EvidenceRef(
                    version_id=span["version_id"],
                    section_path=list(section),
                    char_start=span["char_start"],
                    char_end=span["char_end"],
                )
            )
        if derived_this:
            derived_case_ids.append(case_id)
        if not refs:
            skipped.append({"case_id": case_id, "reason": "no usable anchor"})
            continue
        reasoning = record.get("reasoning_type")
        notes = {
            "group": record["group"],
            "provider": record.get("provider"),
            "reasoning_type": reasoning,
            "secondary_category": record.get("secondary_category"),
            "evidence_shape": record.get("evidence_shape") or "single_span",
            "document_title": record.get("document_title"),
        }
        question = record.get("question") or record.get("proposed_question")
        if not question:
            skipped.append({"case_id": case_id, "reason": "no question"})
            continue
        cases.append(
            EvalCase(
                case_id=case_id,
                category=CATEGORY_MAP.get(reasoning, "normal"),
                question=question,
                expected_evidence=refs,
                expected_abstain=False,
            )
        )
        meta.append(
            {
                "case_id": case_id,
                "span_count": len(refs),
                "category": CATEGORY_MAP.get(reasoning, "normal"),
                **notes,
            }
        )
    if skipped:
        raise SystemExit(f"STOP: skipped holdout cases {skipped}")
    if len(cases) != 90:
        raise SystemExit(f"STOP: projected {len(cases)} != 90")
    proj_info = {
        "cases": len(cases),
        "spans": sum(len(c.expected_evidence) for c in cases),
        "section_path_derived_span_count": derived_count,
        "section_path_derived_case_ids": derived_case_ids,
        "note": (
            "section_path is derived from the frozen corpus parser only when the GOLD "
            "record has no stored section_path. A stored value always wins. Question "
            "text is held in memory for scoring and is not written to holdout artifacts."
        ),
    }
    return cases, meta, proj_info


def breakdown(meta_by_id: dict, d_cases: dict, field: str) -> dict:
    buckets: dict[str, list[str]] = defaultdict(list)
    for cid, info in meta_by_id.items():
        key = info.get(field)
        if key is None:
            key = "unlabeled_legacy" if field == "reasoning_type" else "unknown"
        buckets[str(key)].append(cid)
    out = {}
    for key, ids in sorted(buckets.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        full = sum(1 for cid in ids if d_cases[cid]["fully_recalled"])
        span_recalls = [d_cases[cid]["recall"] for cid in ids]
        doc_recalls = [d_cases[cid]["doc_recall"] for cid in ids]
        out[key] = {
            "cases": len(ids),
            "strict_fully_recalled": full,
            "strict_recall_at_10": f"{full}/{len(ids)}",
            "strict_pct": round(100 * full / len(ids), 1),
            "macro_span_recall": round(sum(span_recalls) / len(span_recalls), 4),
            "document_recall": round(sum(doc_recalls) / len(doc_recalls), 4),
            "small_n": len(ids) <= 3,
        }
    return out


def pip_deps() -> dict:
    freeze_pip = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    deps = {}
    wanted = {
        "numpy",
        "psycopg",
        "pgvector",
        "onnxruntime",
        "tokenizers",
        "scikit-learn",
        "pytest",
        "ruff",
        "pydantic",
    }
    for line in freeze_pip.splitlines():
        if "==" in line:
            name, ver = line.split("==", 1)
            if name.lower() in wanted:
                deps[name] = ver
    return deps


def git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        return out or None
    except Exception:
        return None


def verify_freeze_before_scoring() -> tuple[str, dict, dict]:
    if holdout_log_bytes() != 0:
        raise SystemExit(
            f"STOP: holdout access log is {holdout_log_bytes()} bytes before first run"
        )

    release_sha = hashlib.sha256(RELEASE.read_bytes()).hexdigest()
    if release_sha != EXPECTED_RELEASE_SHA256:
        raise SystemExit(
            f"STOP: SYSTEM-D-RELEASE.json sha256 {release_sha} != {EXPECTED_RELEASE_SHA256}"
        )

    freeze = json.loads(RELEASE.read_text(encoding="utf-8"))
    source = json.loads(SOURCE_FREEZE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    if freeze.get("implementation") != "SYSTEM-D-GUARD-BLEND":
        raise SystemExit(f"STOP: freeze implementation {freeze.get('implementation')}")
    if freeze.get("config_hash") != EXPECTED_D_HASH:
        raise SystemExit(
            f"STOP: freeze config_hash {freeze.get('config_hash')} != {EXPECTED_D_HASH}"
        )
    if source.get("config_hash") != EXPECTED_D_HASH:
        raise SystemExit("STOP: EXP-016 SYSTEM-D-GUARD.json hash mismatch")
    if manifest.get("config_hash") != EXPECTED_D_HASH:
        raise SystemExit("STOP: EVAL-HOLDOUT-001 manifest hash mismatch")
    if list(freeze.get("blend", {}).get("blend_weights") or freeze.get("guard", {}).get("blend_weights") or []) != [
        BLEND_CE,
        BLEND_A,
    ]:
        raise SystemExit("STOP: freeze blend weights changed")
    if freeze.get("candidate_pool") != CANDIDATE_POOL:
        raise SystemExit("STOP: freeze candidate_pool changed")
    if freeze.get("cross_encoder", {}).get("artifact_sha256") != CE_SHA256:
        raise SystemExit("STOP: freeze CE sha256 changed")
    if freeze.get("system_a_config_hash") != A_HASH:
        raise SystemExit("STOP: freeze SYSTEM-A hash changed")
    if freeze.get("holdout_executed"):
        raise SystemExit("STOP: freeze says holdout already executed")
    if source.get("guard", {}).get("blend_weights") != [BLEND_CE, BLEND_A]:
        raise SystemExit("STOP: source freeze blend weights changed")
    if source.get("candidate_pool") != CANDIDATE_POOL:
        raise SystemExit("STOP: source freeze candidate_pool changed")

    a_hash = FROZEN_HASHES["SYSTEM-A-GLOBAL"]
    if a_hash != A_HASH:
        raise SystemExit(f"STOP: live SYSTEM-A hash {a_hash} != {A_HASH}")

    d_hash = frozen_d_hash(a_hash)
    if d_hash != EXPECTED_D_HASH:
        raise SystemExit(
            f"STOP: recomputed SYSTEM-D config hash {d_hash} != freeze {EXPECTED_D_HASH}"
        )
    if d_hash != freeze["config_hash"]:
        raise SystemExit("STOP: recomputed hash does not match freeze file")

    onnx_digest = hashlib.sha256(CE_ONNX.read_bytes()).hexdigest()
    if onnx_digest != CE_SHA256:
        raise SystemExit(f"STOP: live CE onnx sha256 {onnx_digest} != {CE_SHA256}")

    holdout_text = HOLDOUT_JSON.read_text(encoding="utf-8")
    holdout_sha = hashlib.sha256(holdout_text.encode("utf-8")).hexdigest()
    if holdout_sha != EXPECTED_HOLDOUT_SHA256:
        raise SystemExit(
            f"STOP: holdout.json utf-8 sha256 {holdout_sha} != {EXPECTED_HOLDOUT_SHA256}"
        )
    lock = json.loads(HOLDOUT_LOCK.read_text(encoding="utf-8"))
    if lock.get("holdout_sha256") != EXPECTED_HOLDOUT_SHA256:
        raise SystemExit("STOP: holdout.lock.json hash mismatch")
    if lock.get("holdout_count") != 90:
        raise SystemExit("STOP: holdout.lock.json count != 90")

    print(f"SYSTEM-D config hash verified: {d_hash}")
    print(f"SYSTEM-D-RELEASE.json sha256 verified: {release_sha}")
    print(f"holdout.json utf-8 sha256 verified: {holdout_sha}")
    print("Proceeding to score frozen SYSTEM-D-GUARD-BLEND on holdout n=90 once.")
    return d_hash, freeze, manifest


def render_breakdown_table(title: str, data: dict) -> str:
    lines = [
        f"## {title}",
        "",
        "| value | cases | D strict | pct | span recall | doc recall |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, row in data.items():
        star = " *" if row["small_n"] else ""
        lines.append(
            f"| `{key}`{star} | {row['cases']} | {row['strict_recall_at_10']} | "
            f"{row['strict_pct']}% | {row['macro_span_recall']} | {row['document_recall']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    started = time.time()
    d_hash, freeze, manifest = verify_freeze_before_scoring()

    emb = embedding_status()
    if not emb["complete"]:
        raise SystemExit(f"STOP: embeddings incomplete: {emb}")

    # Official loader: appends holdout-access.log.jsonl and prints the warning.
    split = load_split(
        "holdout",
        allow_frozen_holdout=True,
        reason=(
            "EVAL-HOLDOUT-001 first and only holdout run of frozen "
            "SYSTEM-D-GUARD-BLEND; owner Russell and ChatGPT approved; "
            "one-shot D-only scoring of gold150-v1 n=90"
        ),
    )
    holdout_ids = list(split["case_ids"])
    if len(holdout_ids) != 90:
        raise SystemExit(f"STOP: holdout count {len(holdout_ids)} != 90")
    if split.get("count") != 90:
        raise SystemExit("STOP: holdout split count field != 90")
    log_bytes_after_load = holdout_log_bytes()
    if log_bytes_after_load <= 0:
        raise SystemExit("STOP: holdout access was not logged")

    # Do not load development or validation case records for scoring.
    cases, meta_list, proj_info = project_holdout_cases(holdout_ids)
    loaded_ids = [c.case_id for c in cases]
    if loaded_ids != holdout_ids:
        raise SystemExit("STOP: projected case order/ids != holdout.json")
    meta_by_id = {m["case_id"]: m for m in meta_list}

    encoder = TransformerEncoder(max_seq=512).load()
    if encoder.model_version != TRANSFORMER_FINGERPRINT:
        raise SystemExit(
            f"STOP: live encoder fingerprint {encoder.model_version} != {TRANSFORMER_FINGERPRINT}"
        )
    transformer = CachedQueryEmbedder(encoder, fingerprint=encoder.model_version)
    ce = CrossEncoderReranker()
    probe_q, probe_p = "What is BM25?", "BM25 is a lexical ranking function."
    ce_stable = ce.score_pairs(probe_q, [probe_p])[0] == ce.score_pairs(probe_q, [probe_p])[0]

    d_cases: dict[str, dict] = {}
    lat_a, lat_ce, lat_total = [], [], []
    per_case_rows = []
    n_gold_in_pool = 0
    n_gold_total = 0

    for idx, case in enumerate(cases, start=1):
        q = case.question
        t_all = time.time()
        t0 = time.time()
        pool = retrieve_system_a_pool(q, transformer)
        lat_a.append((time.time() - t0) * 1000)
        t0 = time.time()
        scores = ce.score_pairs(q, [h.text for h in pool])
        lat_ce.append((time.time() - t0) * 1000)

        rows = []
        for hit, score in zip(pool, scores, strict=True):
            rows.append(
                {
                    "chunk_id": hit.chunk_id,
                    "version_id": hit.version_id,
                    "section_path": list(hit.section_path),
                    "char_start": hit.char_start,
                    "char_end": hit.char_end,
                    "a_rank": hit.rank,
                    "a_score": float(hit.score),
                    "ce_score": float(score),
                }
            )
        d_rows = apply_blend(rows)
        d_by_chunk = {r["chunk_id"]: r for r in d_rows}
        d_hits = hits_from_blend(d_rows)
        scored = score_case(case, d_hits)
        d_cases[case.case_id] = scored
        lat_total.append((time.time() - t_all) * 1000)

        span_rows = []
        for i, ref in enumerate(case.expected_evidence):
            d_span = scored["spans"][i]
            cid = d_span["chunk_id"]
            a_hit = next((h for h in pool if overlaps(h, ref)), None)
            if cid is None and a_hit is not None:
                cid = a_hit.chunk_id
            row = d_by_chunk.get(cid) if cid else None
            in_pool = a_hit is not None
            n_gold_total += 1
            n_gold_in_pool += int(in_pool)
            span_rows.append(
                {
                    "span_index": i,
                    "chunk_id": cid,
                    "version_id": ref.version_id,
                    "section_path": list(ref.section_path),
                    "char_start": ref.char_start,
                    "char_end": ref.char_end,
                    "candidate_a_rank": a_hit.rank if a_hit else None,
                    "candidate_a_score": float(a_hit.score) if a_hit else None,
                    "ce_score": row["ce_score"] if row else None,
                    "blend_score": row["blend_score"] if row else None,
                    "d_rank": d_span["rank"],
                    "d_doc_rank": d_span["doc_rank"],
                    "d_in_top_10": d_span["within"]["10"],
                    "in_candidate_pool": in_pool,
                    "within": d_span["within"],
                }
            )

        rec = {
            "case_id": case.case_id,
            "fully_recalled": scored["fully_recalled"],
            "recall": scored["recall"],
            "doc_recall": scored["doc_recall"],
            "pool_size": len(pool),
            "all_spans_in_candidate_pool": all(s["in_candidate_pool"] for s in span_rows),
            "spans": span_rows,
            "latency_ms": {
                "system_a_retrieval_candidate_gen": round(lat_a[-1], 2),
                "cross_encoder": round(lat_ce[-1], 2),
                "total": round(lat_total[-1], 2),
            },
            "provider": meta_by_id[case.case_id].get("provider"),
            "reasoning_type": meta_by_id[case.case_id].get("reasoning_type"),
            "evidence_shape": meta_by_id[case.case_id].get("evidence_shape"),
            "group": meta_by_id[case.case_id].get("group"),
            "span_count": meta_by_id[case.case_id]["span_count"],
        }
        per_case_rows.append(rec)
        print(
            f"[{idx}/90] {case.case_id} D={int(scored['fully_recalled'])} "
            f"pool={len(pool)} ce_ms={lat_ce[-1]:.0f} total_ms={lat_total[-1]:.0f}",
            flush=True,
        )

    system_d = summarise(d_cases, "SYSTEM-D-GUARD-BLEND", d_hash)
    failed = [cid for cid, c in d_cases.items() if not c["fully_recalled"]]
    passed = [cid for cid, c in d_cases.items() if c["fully_recalled"]]

    by_provider = breakdown(meta_by_id, d_cases, "provider")
    by_reasoning = breakdown(meta_by_id, d_cases, "reasoning_type")
    by_shape = breakdown(meta_by_id, d_cases, "evidence_shape")
    by_group = breakdown(meta_by_id, d_cases, "group")

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    runtime = round(time.time() - started, 1)
    log_bytes_after = holdout_log_bytes()

    freeze_after = json.loads(RELEASE.read_text(encoding="utf-8"))
    if freeze_after != freeze:
        raise SystemExit("STOP: SYSTEM-D-RELEASE.json changed during the run")
    if freeze_after["config_hash"] != EXPECTED_D_HASH:
        raise SystemExit("STOP: freeze hash changed during the run")
    source_after = json.loads(SOURCE_FREEZE.read_text(encoding="utf-8"))
    if source_after.get("config_hash") != EXPECTED_D_HASH:
        raise SystemExit("STOP: EXP-016 freeze hash changed during the run")

    results = {
        "experiment_id": "EVAL-HOLDOUT-001",
        "phase": "holdout",
        "split": "gold150-v1/holdout",
        "split_path": "evals/splits/gold150-v1/holdout.json",
        "lock_path": "evals/splits/gold150-v1/holdout.lock.json",
        "timestamp": timestamp,
        "corpus_snapshot": SNAPSHOT,
        "chunk_set": CHUNK_SET,
        "system": "SYSTEM-D-GUARD-BLEND",
        "variant": "D",
        "implementation": "SYSTEM-D-GUARD-BLEND",
        "system_a_config_hash": A_HASH,
        "system_d_config_hash": d_hash,
        "system_d_config_hash_matched_freeze_before_scoring": True,
        "release_path": "experiments/EVAL-HOLDOUT-001/SYSTEM-D-RELEASE.json",
        "release_sha256": EXPECTED_RELEASE_SHA256,
        "source_freeze": "experiments/EXP-016/SYSTEM-D-GUARD.json",
        "freeze_untouched": True,
        "tuned_after_seeing_scores": False,
        "parameters_changed_after_any_case": False,
        "second_run": False,
        "answer_generation_run": False,
        "development_loaded_for_scoring": False,
        "validation_loaded_for_scoring": False,
        "holdout_loaded": True,
        "holdout_ids_enumerated": True,
        "holdout_question_text_loaded": True,
        "holdout_question_text_written_to_artifacts": False,
        "holdout_sha256": EXPECTED_HOLDOUT_SHA256,
        "holdout_sha256_verified": True,
        "holdout_count": 90,
        "holdout_access_log_bytes_before": 0,
        "holdout_access_log_bytes_after_load": log_bytes_after_load,
        "holdout_access_log_bytes_after": log_bytes_after,
        "holdout_runs": 1,
        "live_docs_fetched": False,
        "trained": False,
        "cases_scored": 90,
        "d_runs": 1,
        "embedding": emb,
        "projection": proj_info,
        "blend": {
            "weights_CE": BLEND_CE,
            "weights_SYSTEM_A": BLEND_A,
            "minmax_scope": "within each query pool",
            "minmax_degenerate": 0.5,
            "candidate_pool": CANDIDATE_POOL,
            "pool_per_retriever": RRF_POOL,
            "rrf_k": RRF_K,
            "top_k": TOP_K,
            "tie_break": "blended score desc, then SYSTEM-A fused rank asc, then chunk_id asc",
        },
        "system_a_on_holdout": {
            "evaluated_as_competing_system": False,
            "note": (
                "SYSTEM-A top-100 was retrieved only as candidate generation for D. "
                "No A holdout score is reported. No stored A holdout ranks existed."
            ),
            "gold_spans_in_candidate_pool": n_gold_in_pool,
            "gold_spans_total": n_gold_total,
        },
        "system_d": system_d,
        "failed_case_ids": failed,
        "passed_case_ids": passed,
        "breakdowns": {
            "provider": by_provider,
            "reasoning_type": by_reasoning,
            "evidence_shape": by_shape,
            "group": by_group,
        },
        "latency_ms": {
            "A_retrieval_candidate_gen_mean": round(statistics.mean(lat_a), 1),
            "CE_mean": round(statistics.mean(lat_ce), 1),
            "D_total_mean": round(statistics.mean(lat_total), 1),
            "A_retrieval_candidate_gen_median": round(statistics.median(lat_a), 1),
            "CE_median": round(statistics.median(lat_ce), 1),
            "D_total_median": round(statistics.median(lat_total), 1),
            "D_total_min": round(min(lat_total), 1),
            "D_total_max": round(max(lat_total), 1),
        },
        "cross_encoder": {
            "name": CE_NAME,
            "revision": CE_REVISION,
            "artifact_sha256": CE_SHA256,
            "pair_score_stable": ce_stable,
            "max_length": MAX_LENGTH,
        },
        "runtime_seconds": runtime,
        "protocol": {
            "one_shot_system_d_only": True,
            "no_tuning": True,
            "no_debugging_from_holdout_cases": True,
            "no_second_run": True,
            "no_answer_generation": True,
            "chatgpt_instruction": "run SYSTEM-D only",
        },
    }

    per_case_payload = {
        "experiment_id": "EVAL-HOLDOUT-001",
        "system": "SYSTEM-D-GUARD-BLEND",
        "n": 90,
        "question_text_included": False,
        "metadata": meta_by_id,
        "cases": {row["case_id"]: row for row in per_case_rows},
    }

    env = {
        "experiment_id": "EVAL-HOLDOUT-001",
        "timestamp": timestamp,
        "git_commit": git_commit(),
        "host": {
            "os": platform.platform(),
            "python": sys.version.split()[0],
            "executable": sys.executable,
        },
        "corpus_snapshot": SNAPSHOT,
        "chunk_set": CHUNK_SET,
        "transformer_model": TRANSFORMER_MODEL,
        "transformer_fingerprint": TRANSFORMER_FINGERPRINT,
        "system_a_hash": A_HASH,
        "system_d_hash": d_hash,
        "system_d_hash_matched_freeze": True,
        "release_sha256": EXPECTED_RELEASE_SHA256,
        "holdout_sha256": EXPECTED_HOLDOUT_SHA256,
        "holdout_sha256_verified": True,
        "cross_encoder": {
            "name": CE_NAME,
            "revision": CE_REVISION,
            "artifact_sha256": CE_SHA256,
        },
        "blend_weights": [BLEND_CE, BLEND_A],
        "candidate_pool": CANDIDATE_POOL,
        "dependencies": pip_deps(),
        "embedding": emb,
        "holdout_access_log_bytes": log_bytes_after,
        "holdout_runs": 1,
        "runtime_seconds": runtime,
        "latency_ms": results["latency_ms"],
        "d_runs": 1,
        "freeze_untouched": True,
        "python": sys.version.split()[0],
    }

    d_strict = system_d["cases_fully_recalled"]
    failed_list = ", ".join(f"`{cid}`" for cid in failed) if failed else "(none)"
    report = f"""# EVAL-HOLDOUT-001 — holdout of frozen SYSTEM-D-GUARD-BLEND

One-shot **SYSTEM-D-GUARD-BLEND** on gold150-v1 holdout, n=90. First and only holdout run.
No retuning. No second run. No answer-generation eval. SYSTEM-A was not evaluated as a
competing holdout system (A top-100 is D candidate generation only).

## Primary endpoint — strict full-case Recall@10

| system | fully recalled | of | percentage |
| --- | ---: | ---: | ---: |
| SYSTEM-D-GUARD-BLEND | **{d_strict}** | 90 | {round(100 * d_strict / 90, 1)}% |

A case passes only when every required span is in the top 10.

## Secondary metrics

| metric | SYSTEM-D |
| --- | ---: |
| macro span recall@10 | {system_d['macro_span_recall']} |
| spans retrieved@10 | {system_d['spans_found_at_10']}/{system_d['spans_total']} |
| document recall | {system_d['document_recall']} |
| MRR | {system_d['mrr']} |
| spans absent@10 | {system_d['spans_absent_from_top']['10']} |
| spans absent@20 | {system_d['spans_absent_from_top']['20']} |
| spans absent@50 | {system_d['spans_absent_from_top']['50']} |
| spans absent@100 | {system_d['spans_absent_from_top']['100']} |
| latency mean (ms) | {results['latency_ms']['D_total_mean']} |
| latency median (ms) | {results['latency_ms']['D_total_median']} |

Candidate-pool coverage (not an A evaluation): {n_gold_in_pool}/{n_gold_total} gold spans were present in the SYSTEM-A top-100 used as D's candidate generator.

## Setup (frozen before scoring)

- Split: `evals/splits/gold150-v1/holdout.json` n=90.
- `holdout_sha256` `{EXPECTED_HOLDOUT_SHA256}` verified against `holdout.lock.json` **before scoring**.
- SYSTEM-D: `experiments/EVAL-HOLDOUT-001/SYSTEM-D-RELEASE.json` sha256 `{EXPECTED_RELEASE_SHA256}`.
- Implementation SYSTEM-D-GUARD-BLEND, config hash `{d_hash}` recomputed and matched freeze **before scoring**.
- Source freeze: `experiments/EXP-016/SYSTEM-D-GUARD.json` (same hash).
- Weights: 0.7 minmax CE + 0.3 minmax SYSTEM-A fused RRF, pool 100, tie-break blend desc / A rank / chunk_id.
- CE: `{CE_NAME}` rev `{CE_REVISION}`, onnx sha256 `{CE_SHA256}`.
- Encoder fingerprint: `{TRANSFORMER_FINGERPRINT}`.
- D scored **exactly once** on the 90 cases.
- Holdout access log: **{log_bytes_after} bytes** after the run (0 before).
- Parameters were not changed after seeing any case.

## Failures (case IDs only; question text omitted)

{len(failed)} / 90 not fully recalled@10: {failed_list}

{render_breakdown_table("Provider", by_provider)}
{render_breakdown_table("Reasoning type", by_reasoning)}
{render_breakdown_table("Evidence shape", by_shape)}
`*` marks a category with three or fewer cases. Those rows are individual observations.

## What was not done

- No retuning, no weight search, no clamp swap (clamp was EXP-016 variant C, not D).
- No second retrieval system scored on holdout as an evaluation.
- No SYSTEM-A holdout score is reported.
- Development and validation were not loaded for scoring or cherry-picking.
- Answer generation was not run.
- Individual holdout failures were not debugged mid-run.

## Files

- `experiments/EVAL-HOLDOUT-001/EVAL-HOLDOUT-001-results.json`
- `experiments/EVAL-HOLDOUT-001/EVAL-HOLDOUT-001-per-case.json`
- `experiments/EVAL-HOLDOUT-001/EVAL-HOLDOUT-001-report.md`
- `experiments/EVAL-HOLDOUT-001/EVAL-HOLDOUT-001-environment.json`
- `evals/splits/gold150-v1/holdout-access.log.jsonl`
"""

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results_path = OUT_DIR / "EVAL-HOLDOUT-001-results.json"
    per_case_path = OUT_DIR / "EVAL-HOLDOUT-001-per-case.json"
    report_path = OUT_DIR / "EVAL-HOLDOUT-001-report.md"
    env_path = OUT_DIR / "EVAL-HOLDOUT-001-environment.json"

    results_path.write_text(json.dumps(results, indent=2, default=str) + "\n", encoding="utf-8")
    per_case_path.write_text(
        json.dumps(per_case_payload, indent=2, default=str) + "\n", encoding="utf-8"
    )
    report_path.write_text(report, encoding="utf-8")
    env_path.write_text(json.dumps(env, indent=2, default=str) + "\n", encoding="utf-8")

    print()
    print(f"D strict {system_d['strict_recall_at_10']}")
    print(f"span recall {system_d['macro_span_recall']}")
    print(f"MRR {system_d['mrr']}")
    print(f"doc recall {system_d['document_recall']}")
    print(f"latency mean {results['latency_ms']['D_total_mean']} ms")
    print(f"holdout_log={log_bytes_after} bytes")
    print(f"freeze_hash={d_hash}")
    print(f"wrote {results_path}")
    print(f"wrote {per_case_path}")
    print(f"wrote {report_path}")
    print(f"wrote {env_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
