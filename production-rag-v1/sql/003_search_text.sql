-- EXP-006 migration: separate what is *displayed* from what is *searched*.
--
-- Motivation
-- ----------
-- EXP-006 tests whether prepending structural context to the indexed text helps
-- BM25, independently of chunk size. Doing that by editing `chunk.text` — as the
-- V3 chunker did in EXP-005 — is wrong for two reasons: the canonical body is
-- what a citation quotes back to the user, and mutating it turns synthesised
-- metadata into apparent source content.
--
-- After this migration:
--   * chunk.text            canonical source body. Never enriched. Unchanged.
--   * chunk.context_header  the structural header, or NULL when not enriched.
--   * chunk.search_text     what is indexed. NULL means "index text verbatim".
--
-- search_vector falls back through coalesce(search_text, text), so every
-- pre-existing row keeps a byte-identical tsvector and EXP-000..EXP-005 stay
-- reproducible. Nothing has to be rewritten to adopt the new columns.

BEGIN;

ALTER TABLE chunk ADD COLUMN IF NOT EXISTS search_text TEXT;
ALTER TABLE chunk ADD COLUMN IF NOT EXISTS context_header TEXT;

COMMENT ON COLUMN chunk.text IS 'Canonical source body. Never enriched; this is what a citation quotes.';
COMMENT ON COLUMN chunk.search_text IS 'Text actually indexed. NULL means index chunk.text verbatim.';
COMMENT ON COLUMN chunk.context_header IS 'Structural header prepended in search_text, or NULL when not enriched.';

-- The generated column must be dropped and rebuilt to change its expression.
DROP INDEX IF EXISTS idx_chunk_search_vector;
ALTER TABLE chunk DROP COLUMN IF EXISTS search_vector;
ALTER TABLE chunk ADD COLUMN search_vector TSVECTOR
    GENERATED ALWAYS AS (to_tsvector('simple', coalesce(search_text, text, ''))) STORED;
CREATE INDEX idx_chunk_search_vector ON chunk USING GIN(search_vector);

-- Records which enrichment produced a chunk set, so B/D are self-describing.
ALTER TABLE chunk_set ADD COLUMN IF NOT EXISTS enrichment_config JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE chunk_set ADD COLUMN IF NOT EXISTS derived_from_chunk_set_id TEXT REFERENCES chunk_set(chunk_set_id);

COMMIT;
