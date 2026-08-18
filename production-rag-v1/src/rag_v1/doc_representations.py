"""EXP-014: document-level representations built from stored chunk vectors.

Why this exists
---------------
EXP-013 falsified the aggregation hypothesis: four rank-aggregation rules over chunk
rankings all landed on document recall@5 = 0.875 and 17/20 all-required-documents
routed. AN-001 showed why in one line — its document contributes a single chunk
anywhere in 300 BM25 results and the transformer never retrieves it at all, so no
function of those rankings can promote it, yet handed the document its evidence
ranks first.

That is an argument about the *input*, not the arithmetic. This module represents a
document directly instead of inferring it from how its chunks happened to compete.

What it is not
--------------
No new model, no training, no external call, no re-chunking, no new passage
embeddings. Every vector here is a deterministic function of embeddings this project
already stored, so a rebuild from the same snapshot reproduces identical vectors.

The four constructions are preregistered in
``experiments/EXP-014/preregistration.md`` and were fixed before any scored result
was observed.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

REPRESENTATION_VERSION = "1.0"

REPRESENTATIONS = {
    "DOC-A-MEAN": "arithmetic mean of the document's normalised chunk vectors",
    "DOC-B-CENTROID": "as A, after removing exact-duplicate chunk content by content hash",
    "DOC-C-SECTION": "mean within each section, then equal-weight mean of section vectors",
    "DOC-D-MULTIVECTOR": "per-section vectors kept separate; document scores at its best section",
}


def _l2(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=-1, keepdims=True)
    return matrix / np.clip(norms, 1e-12, None)


@dataclass
class DocumentIndex:
    """Document vectors plus the provenance needed to reproduce and audit them."""

    name: str
    version: str
    version_ids: list[str]
    matrix: np.ndarray                     # single-vector representations
    section_vectors: dict[str, np.ndarray] | None = None   # DOC-D only
    stats: dict | None = None

    def vector_hashes(self) -> dict[str, str]:
        return {
            v: hashlib.sha256(self.matrix[i].tobytes()).hexdigest()[:16]
            for i, v in enumerate(self.version_ids)
        }

    def score(self, query_vector: np.ndarray) -> dict[str, float]:
        """Cosine of every document against the query."""
        q = np.asarray(query_vector, dtype=np.float32)
        q = q / max(float(np.linalg.norm(q)), 1e-12)
        if self.section_vectors is None:
            sims = self.matrix @ q
            return dict(zip(self.version_ids, (float(s) for s in sims), strict=True))
        # DOC-D: a document is as relevant as its most relevant section. Compressing
        # a whole document into one centroid averages distinct topics together; this
        # keeps them separate and lets one strongly relevant section surface the
        # document.
        return {v: float((vectors @ q).max()) for v, vectors in self.section_vectors.items()}

    def ranking(self, query_vector: np.ndarray) -> list[tuple[str, int]]:
        """Documents ordered by score, with a deterministic tie-break on id."""
        scores = self.score(query_vector)
        ordered = sorted(scores, key=lambda v: (-scores[v], v))
        return [(v, rank) for rank, v in enumerate(ordered, start=1)]


def load_chunk_rows(model_id: str, chunk_set_id: str, snapshot_id: str) -> list[tuple]:
    """(version_id, section_path, content_hash, embedding) for one chunk set.

    Ordered by chunk_id so the construction is independent of database row order.
    """
    import json

    from rag_v1.db import connect

    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.version_id, c.section_path, c.content_hash, ce.embedding::text
            FROM chunk_embedding ce
            JOIN chunk c ON c.chunk_id = ce.chunk_id
            JOIN corpus_snapshot_version sv ON sv.version_id = c.version_id
            WHERE ce.model_id=%s AND c.chunk_set_id=%s AND sv.snapshot_id=%s
            ORDER BY c.chunk_id
            """,
            (model_id, chunk_set_id, snapshot_id),
        )
        return [(r[0], tuple(r[1]), r[2], np.array(json.loads(r[3]), dtype=np.float32))
                for r in cur.fetchall()]


def build(name: str, rows: list[tuple]) -> DocumentIndex:
    """Build one preregistered representation from stored chunk vectors."""
    if name not in REPRESENTATIONS:
        raise ValueError(f"Unknown representation {name!r}. Available: {sorted(REPRESENTATIONS)}")

    by_doc: dict[str, list[tuple]] = {}
    for version_id, section_path, content_hash, vector in rows:
        by_doc.setdefault(version_id, []).append((section_path, content_hash, vector))

    version_ids = sorted(by_doc)
    duplicates_removed = 0
    section_counts: list[int] = []

    if name == "DOC-D-MULTIVECTOR":
        section_vectors: dict[str, np.ndarray] = {}
        for version_id in version_ids:
            sections: dict[tuple, list[np.ndarray]] = {}
            for section_path, _chash, vector in by_doc[version_id]:
                sections.setdefault(section_path, []).append(vector)
            stacked = np.vstack([_l2(np.mean(_l2(np.vstack(v)), axis=0)[None, :])
                                 for _k, v in sorted(sections.items())])
            section_vectors[version_id] = stacked.astype(np.float32)
            section_counts.append(len(sections))
        # The flat matrix is the DOC-C vector, kept so hashing and storage
        # accounting work uniformly; scoring uses the section vectors.
        matrix = np.vstack([_l2(np.mean(section_vectors[v], axis=0)[None, :])
                            for v in version_ids]).astype(np.float32)
        stats = {
            "section_vectors_total": int(sum(section_counts)),
            "mean_sections_per_document": round(float(np.mean(section_counts)), 2),
            "max_sections_per_document": int(max(section_counts)),
            "min_sections_per_document": int(min(section_counts)),
        }
        return DocumentIndex(name, REPRESENTATION_VERSION, version_ids, matrix,
                             section_vectors=section_vectors, stats=stats)

    vectors: list[np.ndarray] = []
    for version_id in version_ids:
        entries = by_doc[version_id]
        if name == "DOC-B-CENTROID":
            seen: set[str] = set()
            kept = []
            for section_path, content_hash, vector in entries:
                if content_hash in seen:
                    duplicates_removed += 1
                    continue
                seen.add(content_hash)
                kept.append((section_path, content_hash, vector))
            entries = kept
        if name == "DOC-C-SECTION":
            sections: dict[tuple, list[np.ndarray]] = {}
            for section_path, _chash, vector in entries:
                sections.setdefault(section_path, []).append(vector)
            section_counts.append(len(sections))
            # Each section contributes one normalised vector, so a section that
            # happens to produce many chunks cannot dominate the document.
            per_section = np.vstack([_l2(np.mean(_l2(np.vstack(v)), axis=0)[None, :])
                                     for _k, v in sorted(sections.items())])
            doc_vector = _l2(np.mean(per_section, axis=0)[None, :])[0]
        else:
            stacked = _l2(np.vstack([v for _s, _c, v in entries]))
            doc_vector = _l2(np.mean(stacked, axis=0)[None, :])[0]
        vectors.append(doc_vector)

    matrix = np.vstack(vectors).astype(np.float32)
    stats: dict = {}
    if name == "DOC-B-CENTROID":
        stats["duplicate_chunks_removed"] = duplicates_removed
    if name == "DOC-C-SECTION":
        stats |= {
            "mean_sections_per_document": round(float(np.mean(section_counts)), 2),
            "max_sections_per_document": int(max(section_counts)),
        }
    return DocumentIndex(name, REPRESENTATION_VERSION, version_ids, matrix, stats=stats)


def chunk_vectors_are_normalised(rows: list[tuple], tolerance: float = 1e-3) -> dict:
    """Confirm the stored chunk vectors are unit length, as DOC-A assumes."""
    norms = np.array([float(np.linalg.norm(v)) for _a, _b, _c, v in rows])
    return {
        "chunks_checked": int(norms.size),
        "min_norm": round(float(norms.min()), 6),
        "max_norm": round(float(norms.max()), 6),
        "all_unit_length": bool(np.all(np.abs(norms - 1.0) <= tolerance)),
    }


__all__ = [
    "REPRESENTATIONS", "REPRESENTATION_VERSION", "DocumentIndex", "build",
    "chunk_vectors_are_normalised", "load_chunk_rows",
]
