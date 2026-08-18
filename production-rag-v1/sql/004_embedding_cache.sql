-- EXP-007: make the embedding cache key explicit.
--
-- chunk_embedding was keyed by (chunk_id, model_id). chunk_id already derives from
-- the chunk's content hash, so that was correct in practice, but the cache key was
-- implicit. Recording content_hash and the model fingerprint directly makes the
-- invalidation rule visible and testable: an unchanged chunk under an unchanged
-- model is never re-embedded, and either one changing forces a rebuild.

BEGIN;

ALTER TABLE chunk_embedding ADD COLUMN IF NOT EXISTS content_hash TEXT;
ALTER TABLE chunk_embedding ADD COLUMN IF NOT EXISTS model_fingerprint TEXT;

UPDATE chunk_embedding ce
SET content_hash = c.content_hash
FROM chunk c
WHERE c.chunk_id = ce.chunk_id AND ce.content_hash IS NULL;

CREATE INDEX IF NOT EXISTS idx_chunk_embedding_cache
    ON chunk_embedding(model_id, content_hash);

ALTER TABLE embedding_model ADD COLUMN IF NOT EXISTS model_card JSONB NOT NULL DEFAULT '{}'::jsonb;

COMMENT ON COLUMN chunk_embedding.content_hash IS
  'Hash of the chunk body that was embedded. With model_id this is the cache key.';
COMMENT ON COLUMN chunk_embedding.model_fingerprint IS
  'Embedding model version fingerprint; a change invalidates the cached vector.';

COMMIT;
