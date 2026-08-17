CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS document_source (
    source_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    canonical_url TEXT NOT NULL,
    title TEXT NOT NULL,
    authority_class TEXT NOT NULL DEFAULT 'official_docs',
    authority_rank SMALLINT NOT NULL DEFAULT 100,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (provider, canonical_url)
);

CREATE TABLE IF NOT EXISTS document_version (
    version_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES document_source(source_id),
    content_hash TEXT NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('current','superseded','removed_from_source','quarantined_candidate')),
    parser_name TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    raw_path TEXT,
    char_count INTEGER NOT NULL,
    section_count INTEGER NOT NULL,
    supersedes_version_id TEXT REFERENCES document_version(version_id),
    validation JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (source_id, content_hash)
);

CREATE INDEX IF NOT EXISTS idx_document_version_source_status_captured
    ON document_version(source_id, status, captured_at DESC);

CREATE TABLE IF NOT EXISTS chunk (
    chunk_id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL REFERENCES document_version(version_id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    section_path TEXT[] NOT NULL,
    chunk_type TEXT NOT NULL CHECK (chunk_type IN ('prose','code','table','table_row')),
    char_start INTEGER NOT NULL,
    char_end INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    text TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    search_vector TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('simple', coalesce(text, ''))
    ) STORED,
    CHECK (char_end > char_start),
    UNIQUE (version_id, ordinal)
);

CREATE INDEX IF NOT EXISTS idx_chunk_search_vector
    ON chunk USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_chunk_version_type_ordinal
    ON chunk(version_id, chunk_type, ordinal);
CREATE INDEX IF NOT EXISTS idx_chunk_section_path
    ON chunk USING GIN(section_path);

CREATE TABLE IF NOT EXISTS chunk_link (
    parent_chunk_id TEXT NOT NULL REFERENCES chunk(chunk_id) ON DELETE CASCADE,
    child_chunk_id TEXT NOT NULL REFERENCES chunk(chunk_id) ON DELETE CASCADE,
    relation TEXT NOT NULL,
    PRIMARY KEY(parent_chunk_id, child_chunk_id, relation),
    CHECK (parent_chunk_id <> child_chunk_id)
);

CREATE TABLE IF NOT EXISTS embedding_model (
    model_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    dimension INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(provider, model_name, model_version, dimension)
);

-- Unconstrained vector dimension intentionally supports multiple embedding models.
-- For large corpora, create a partial expression HNSW index per active model/dimension.
CREATE TABLE IF NOT EXISTS chunk_embedding (
    chunk_id TEXT NOT NULL REFERENCES chunk(chunk_id) ON DELETE CASCADE,
    model_id TEXT NOT NULL REFERENCES embedding_model(model_id) ON DELETE CASCADE,
    embedding VECTOR NOT NULL,
    embedding_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY(chunk_id, model_id)
);
CREATE INDEX IF NOT EXISTS idx_chunk_embedding_model ON chunk_embedding(model_id);

CREATE TABLE IF NOT EXISTS corpus_snapshot (
    snapshot_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    manifest_hash TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    chunking_config_hash TEXT NOT NULL,
    git_commit TEXT,
    status TEXT NOT NULL DEFAULT 'frozen' CHECK (status IN ('frozen','live')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS corpus_snapshot_version (
    snapshot_id TEXT NOT NULL REFERENCES corpus_snapshot(snapshot_id) ON DELETE CASCADE,
    version_id TEXT NOT NULL REFERENCES document_version(version_id),
    PRIMARY KEY(snapshot_id, version_id)
);
CREATE INDEX IF NOT EXISTS idx_snapshot_version_version ON corpus_snapshot_version(version_id);

CREATE TABLE IF NOT EXISTS query_trace (
    trace_id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    experiment_id TEXT,
    snapshot_id TEXT REFERENCES corpus_snapshot(snapshot_id),
    query TEXT NOT NULL,
    query_hash TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    mode TEXT NOT NULL,
    stage_trace JSONB NOT NULL,
    total_latency_ms DOUBLE PRECISION,
    estimated_cost_usd NUMERIC(12,6),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_query_trace_exp ON query_trace(experiment_id, created_at DESC);

CREATE TABLE IF NOT EXISTS retrieval_cache (
    cache_key TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL,
    query_hash TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    result_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
