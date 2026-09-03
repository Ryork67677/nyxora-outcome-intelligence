"""SYSTEM-E-WITHIN-DOC (amended): additive local-BM25 candidate expansion.

New v2 system. Not a D edit. Opposite of DOC-C: union, never a document gate.
Local lane is BM25 only (no within-doc dense). Knobs frozen in
EXP-018-preregistration-amendment.md before retrieval.
"""

from __future__ import annotations

from pathlib import Path

from rag_v1.db import connect
from rag_v1.ids import config_hash
from rag_v1.retrieval import dense_search, lexical_search, rrf_fuse, rrf_fuse_labelled
from rag_v1.systems import (
    CHUNK_SET,
    SNAPSHOT,
    TRANSFORMER_FINGERPRINT,
    TRANSFORMER_MODEL,
)
from rag_v1.types import EvidenceRef, SearchHit

ROOT = Path(__file__).resolve().parents[3]

A_HASH = "9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38"
D_HASH = "d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a"
CE_SHA256 = "5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a"
TOP_K = 10
RRF_POOL = 50
RRF_K = 60
CANDIDATE_POOL = 100
PARENT_N = 10
W = 20
BLEND_CE, BLEND_A = 0.7, 0.3
MINMAX_DEGENERATE = 0.5
PROBE_DEPTHS = (10, 20, 30, 50, 100, 300)

HOLDOUT_LOG = ROOT / "evals" / "splits" / "gold150-v1" / "holdout-access.log.jsonl"
HOLDOUT_LOCK = ROOT / "evals" / "splits" / "gold150-v1" / "holdout.lock.json"
HOLD_LOG_SHA_AT_PREREG = "45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3"
HOLD_LOCK_SHA = "fc9ac96082cbf0aa3df82df017e19af9f49eed5506c5c281858b3de405cde294"


def system_e_config() -> dict:
    return {
        "name": "SYSTEM-E-WITHIN-DOC",
        "control_system_a": A_HASH,
        "control_system_d": D_HASH,
        "parent_n": PARENT_N,
        "parent_source": (
            "TOP 10 unique version_ids from SYSTEM-A fused ranking "
            "(ChatGPT option B)"
        ),
        "local_retrieval": "BM25_ONLY",
        "within_doc_dense": False,
        "W": W,
        "union": (
            "A pool-100 UNION per-parent local BM25 top-W; "
            "dedupe chunk_id; never drop A-pool chunk"
        ),
        "merge_rrf": (
            "rrf_fuse_labelled k=60 over system_a + local_bm25:<version_id>; "
            "top_k=union size"
        ),
        "anti_doc_c": True,
        "idf": "full-corpus never recomputed inside document",
        "weights": [BLEND_CE, BLEND_A],
        "minmax_degenerate": MINMAX_DEGENERATE,
        "a_channel": "merge-RRF score/rank",
        "ce_sha256": CE_SHA256,
        "tie_break": "blend desc, merge-RRF rank, chunk_id",
        "snapshot": SNAPSHOT,
        "chunk_set": CHUNK_SET,
        "rrf_k": RRF_K,
        "pool_per_retriever": RRF_POOL,
        "top_k": TOP_K,
        "amendment": "experiments/EXP-018/EXP-018-preregistration-amendment.md",
    }


def system_e_hash() -> str:
    return config_hash(system_e_config())


def holdout_log_state() -> dict:
    import hashlib

    log_bytes = HOLDOUT_LOG.read_bytes() if HOLDOUT_LOG.exists() else b""
    lock_bytes = HOLDOUT_LOCK.read_bytes() if HOLDOUT_LOCK.exists() else b""
    return {
        "log_bytes": len(log_bytes),
        "log_sha256": hashlib.sha256(log_bytes).hexdigest() if HOLDOUT_LOG.exists() else None,
        "lock_bytes": len(lock_bytes),
        "lock_sha256": hashlib.sha256(lock_bytes).hexdigest() if HOLDOUT_LOCK.exists() else None,
        "lock_frozen": True,
    }


def embedding_status() -> dict:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT version()")
        pg = cur.fetchone()[0]
        cur.execute("SELECT extversion FROM pg_extension WHERE extname='vector'")
        pgv = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (CHUNK_SET,))
        chunks = cur.fetchone()[0]
        cur.execute(
            "SELECT count(*), min(model_fingerprint), max(model_fingerprint) "
            "FROM chunk_embedding WHERE model_id=%s",
            (TRANSFORMER_MODEL,),
        )
        n, fp_min, fp_max = cur.fetchone()
    return {
        "postgres_version": pg,
        "pgvector_extversion": pgv,
        "chunk_set": CHUNK_SET,
        "chunks": chunks,
        "embedding_rows": n,
        "model_id": TRANSFORMER_MODEL,
        "fingerprint_min": fp_min,
        "fingerprint_max": fp_max,
        "fingerprint_expected": TRANSFORMER_FINGERPRINT,
        "complete": n == chunks == 14209 and fp_min == fp_max == TRANSFORMER_FINGERPRINT,
        "known_drift": "Postgres 16.15 / pgvector 0.8.6 vs recorded 16.13 / 0.6.0",
    }


def overlaps(hit: SearchHit, ref: EvidenceRef) -> bool:
    return (
        hit.version_id == ref.version_id
        and list(hit.section_path) == list(ref.section_path)
        and hit.char_start < ref.char_end
        and hit.char_end > ref.char_start
    )


def covering_chunk_ids(ref: EvidenceRef) -> list[str]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT chunk_id FROM chunk
            WHERE chunk_set_id=%s AND version_id=%s
              AND section_path=%s
              AND char_start < %s AND char_end > %s
            ORDER BY chunk_id
            """,
            (CHUNK_SET, ref.version_id, list(ref.section_path), ref.char_end, ref.char_start),
        )
        return [r[0] for r in cur.fetchall()]


def retrieve_system_a_pool(query: str, embedder) -> list[SearchHit]:
    lexical = lexical_search(query, SNAPSHOT, RRF_POOL)
    dense = dense_search(query, SNAPSHOT, TRANSFORMER_MODEL, RRF_POOL, embedder=embedder)
    return rrf_fuse([lexical, dense], rrf_k=RRF_K, top_k=CANDIDATE_POOL)


def parent_version_ids(a_pool: list[SearchHit], parent_n: int = PARENT_N) -> list[str]:
    """ChatGPT option B: TOP 10 unique version_ids from SYSTEM-A fused ranking."""
    out: list[str] = []
    seen: set[str] = set()
    for hit in a_pool[:TOP_K]:
        if hit.version_id not in seen:
            seen.add(hit.version_id)
            out.append(hit.version_id)
            if len(out) >= parent_n:
                break
    return out


def local_bm25_per_parent(query: str, parent_ids: list[str]) -> dict[str, list[SearchHit]]:
    """Top-W BM25 inside each parent document. Full-corpus IDF. No dense lane."""
    expanded: dict[str, list[SearchHit]] = {}
    for vid in parent_ids:
        hits = lexical_search(query, SNAPSHOT, W, version_ids=[vid])
        ranked: list[SearchHit] = []
        for i, hit in enumerate(hits, start=1):
            h = hit.model_copy(deep=True)
            h.rank = i
            ranked.append(h)
        expanded[vid] = ranked
    return expanded


def merge_union_rrf(
    a_pool: list[SearchHit], local: dict[str, list[SearchHit]]
) -> tuple[list[SearchHit], list[str], set[str]]:
    """A-pool-100 UNION local BM25, then labelled RRF over the full union.

    Never drops an A-pool chunk. Returns (fused_union, new_chunk_ids, a_pool_ids).
    """
    a_ids = {h.chunk_id for h in a_pool}
    local_ids: set[str] = set()
    labelled: list[tuple[str, list[SearchHit]]] = [("system_a", a_pool)]
    for vid, hits in local.items():
        labelled.append((f"local_bm25:{vid}", hits))
        local_ids.update(h.chunk_id for h in hits)
    union_ids = a_ids | local_ids
    new_ids = sorted(union_ids - a_ids)
    fused = rrf_fuse_labelled(labelled, rrf_k=RRF_K, top_k=max(len(union_ids), 1))
    fused_ids = {h.chunk_id for h in fused}
    missing_a = a_ids - fused_ids
    if missing_a:
        raise RuntimeError(
            f"anti-DOC-C violation: merge RRF dropped A-pool chunks {sorted(missing_a)[:5]}"
        )
    return fused, new_ids, a_ids


def minmax_norm(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [MINMAX_DEGENERATE] * len(values)
    scale = hi - lo
    return [(v - lo) / scale for v in values]


def apply_blend(rows: list[dict]) -> list[dict]:
    """Frozen EXP-016 D formula on whatever pool is passed. Does not edit D."""
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
        row["blend_rank"] = i
    return blended


__all__ = [
    "A_HASH",
    "BLEND_A",
    "BLEND_CE",
    "CANDIDATE_POOL",
    "CE_SHA256",
    "CHUNK_SET",
    "D_HASH",
    "HOLD_LOCK_SHA",
    "HOLD_LOG_SHA_AT_PREREG",
    "PARENT_N",
    "PROBE_DEPTHS",
    "ROOT",
    "RRF_K",
    "RRF_POOL",
    "SNAPSHOT",
    "TOP_K",
    "TRANSFORMER_FINGERPRINT",
    "TRANSFORMER_MODEL",
    "W",
    "apply_blend",
    "covering_chunk_ids",
    "embedding_status",
    "holdout_log_state",
    "local_bm25_per_parent",
    "merge_union_rrf",
    "minmax_norm",
    "overlaps",
    "parent_version_ids",
    "retrieve_system_a_pool",
    "system_e_config",
    "system_e_hash",
]
