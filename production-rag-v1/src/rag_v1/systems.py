"""EXP-014R: the two systems under replication, frozen.

EXP-014 produced the first preregistered intervention to beat the global control
end-to-end (0.875 / 17-of-20 against 0.775 / 15-of-20, +2 rescued, 0 regressed).
But n = 20, one case is 5 percentage points, and six of the last seven experiments
turned on one or two cases. So the next question is not "what else can we change" —
it is "was that real".

Answering it requires the systems to stop moving. This module states both
configurations as data and hashes them, so a later run can prove it used the same
system rather than asserting it. Nothing here is tunable: if a field changes, the
hash changes, and any comparison across the change is invalid by construction.
"""

from __future__ import annotations

from rag_v1.ids import config_hash

SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"
CHUNK_SET = "cs_v1_control"
TRANSFORMER_MODEL = "emb_e7d4183fd6eb878ae2fdf080efb6861e"
TRANSFORMER_FINGERPRINT = "bd95feaeacf98559"
MAX_SEQ = 512

#: Shared by both systems — the passage layer EXP-012/013/014 never touched.
STAGE_2 = {
    "query": "raw user question, verbatim",
    "lexical": {"retriever": "bm25", "k1": 1.2, "b": 0.75, "ts_config": "simple",
                "statistics": "full corpus — never recomputed inside routed documents"},
    "dense": {"retriever": "transformer_cosine", "model_id": TRANSFORMER_MODEL,
              "fingerprint": TRANSFORMER_FINGERPRINT, "max_seq_length": MAX_SEQ,
              "exact_search": True, "ann_index": False},
    "fusion": {"method": "rrf", "rrf_k": 60, "pool_per_retriever": 50},
    "top_k": 10,
    "reranker": None, "cross_encoder": None, "query_rewriting": False,
    "enrichment": None, "metadata_filtering": False,
}

SYSTEM_A_GLOBAL = {
    "name": "SYSTEM-A-GLOBAL",
    "description": "global BM25 + transformer RRF over all control chunks",
    "stage_1": None,
    "stage_2": STAGE_2,
    "snapshot": SNAPSHOT,
    "chunk_set": CHUNK_SET,
    "development_metrics": {"macro_span_recall": 0.775, "cases_fully_recalled": 15,
                            "spans_found_at_10": 17, "document_recall": 0.925, "mrr": 0.449},
}

SYSTEM_B_DOC_C = {
    "name": "SYSTEM-B-DOC-C",
    "description": "DOC-C-SECTION document routing -> frozen Stage 2",
    "stage_1": {
        "representation": "DOC-C-SECTION",
        "representation_version": "1.0",
        "construction": [
            "group stored chunk embeddings by section_path",
            "mean the normalised chunk vectors within each section",
            "normalise each section vector",
            "give every section equal contribution",
            "mean the section vectors",
            "normalise the document vector",
        ],
        "source_embeddings": TRANSFORMER_MODEL,
        "similarity": "cosine",
        "top_documents": 5,
        "fusion_with_chunk_router": False,
        "fusion_with_bm25": False,
    },
    "stage_2": STAGE_2,
    "snapshot": SNAPSHOT,
    "chunk_set": CHUNK_SET,
    "development_metrics": {"macro_span_recall": 0.875, "cases_fully_recalled": 17,
                            "spans_found_at_10": 19, "document_recall": 0.925, "mrr": 0.474},
}

#: EXP-014's secondary router reached 19/20 document routing and retrieved *worse*
#: (0.825 / 16-of-20). It is recorded so the choice is auditable, and deliberately
#: not the system under replication: the configuration being tested is the one that
#: improved end-to-end retrieval, not the one with the better Stage-1 number.
NOT_UNDER_TEST = {
    "name": "DOC-C-SECTION+chunk+bm25",
    "reason": "routes 19/20 but retrieves 0.825 / 16-of-20 — better routing, worse retrieval",
    "excluded_by": "EXP-014R brief section 4",
}


def system_config_hash(system: dict) -> str:
    """Hash everything that could change a result, and nothing that cannot."""
    return config_hash({k: v for k, v in system.items() if k != "development_metrics"})


SYSTEMS = {"SYSTEM-A-GLOBAL": SYSTEM_A_GLOBAL, "SYSTEM-B-DOC-C": SYSTEM_B_DOC_C}

FROZEN_HASHES = {name: system_config_hash(system) for name, system in SYSTEMS.items()}


__all__ = [
    "CHUNK_SET", "FROZEN_HASHES", "MAX_SEQ", "NOT_UNDER_TEST", "SNAPSHOT", "STAGE_2",
    "SYSTEMS", "SYSTEM_A_GLOBAL", "SYSTEM_B_DOC_C", "TRANSFORMER_FINGERPRINT",
    "TRANSFORMER_MODEL", "system_config_hash",
]
