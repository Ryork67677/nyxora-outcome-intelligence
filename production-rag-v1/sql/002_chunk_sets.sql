-- EXP-005 migration: let several chunkings of the SAME document versions coexist.
--
-- Motivation
-- ----------
-- EXP-005 tests whether chunk granularity is the retrieval bottleneck. That test
-- is only valid if the V1 chunking stays byte-identical and re-runnable while new
-- chunkings are measured beside it. Before this migration the schema made that
-- impossible in two ways:
--
--   1. chunk had UNIQUE (version_id, ordinal), so a second chunking of the same
--      document version collided with the first.
--   2. Retrieval reached chunks via corpus_snapshot_version -> version_id, which
--      carries no notion of *which* chunking, so a query against a snapshot would
--      have returned chunks from every chunking of those versions at once.
--
-- The migration is purely additive for existing rows: everything already in the
-- database is adopted into the 'cs_v1_control' chunk set, so EXP-000 through
-- EXP-003 remain reproducible against snapshot snap_689e3363... unchanged.

BEGIN;

CREATE TABLE IF NOT EXISTS chunk_set (
    chunk_set_id TEXT PRIMARY KEY,
    chunker_name TEXT NOT NULL,
    chunker_version TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    parser_version TEXT NOT NULL,
    git_commit TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    notes TEXT,
    UNIQUE (chunker_name, chunker_version, config_hash)
);

-- Adopt the pre-existing chunks as the immutable control set. The config recorded
-- here is what src/rag_v1/chunking.py was actually run with for the V1 corpus.
INSERT INTO chunk_set (
    chunk_set_id, chunker_name, chunker_version, config_hash, config, parser_version, notes
) VALUES (
    'cs_v1_control',
    'chunker_v1_control',
    '1.0',
    'v1-control-as-shipped',
    '{"max_chunk_chars": 3500, "min_chunk_chars": 200, "enforces_hard_limit": false}'::jsonb,
    'v1.0',
    'Chunking as shipped in V1. Frozen: EXP-000..EXP-003 were measured against this set.'
) ON CONFLICT (chunk_set_id) DO NOTHING;

ALTER TABLE chunk ADD COLUMN IF NOT EXISTS chunk_set_id TEXT REFERENCES chunk_set(chunk_set_id);
UPDATE chunk SET chunk_set_id = 'cs_v1_control' WHERE chunk_set_id IS NULL;
ALTER TABLE chunk ALTER COLUMN chunk_set_id SET NOT NULL;

-- Ordinals are only unique within one chunking of one version.
ALTER TABLE chunk DROP CONSTRAINT IF EXISTS chunk_version_id_ordinal_key;
ALTER TABLE chunk DROP CONSTRAINT IF EXISTS chunk_set_version_ordinal_key;
ALTER TABLE chunk ADD CONSTRAINT chunk_set_version_ordinal_key
    UNIQUE (chunk_set_id, version_id, ordinal);

CREATE INDEX IF NOT EXISTS idx_chunk_set_version ON chunk(chunk_set_id, version_id);

-- A snapshot now pins BOTH the document versions and the chunking of them.
ALTER TABLE corpus_snapshot ADD COLUMN IF NOT EXISTS chunk_set_id TEXT REFERENCES chunk_set(chunk_set_id);
UPDATE corpus_snapshot SET chunk_set_id = 'cs_v1_control' WHERE chunk_set_id IS NULL;
ALTER TABLE corpus_snapshot ALTER COLUMN chunk_set_id SET NOT NULL;

COMMIT;
