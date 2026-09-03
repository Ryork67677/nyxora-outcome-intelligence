# Production RAG v1 Scope

This repository deliberately stops before reranking/agentic retry. V1 exists to produce trustworthy measurements, not to maximize architecture surface area.

## Validity corrections incorporated before implementation

1. **EXP-NULL closed-book control** comes before retrieval experiments.
2. **Ground-truth evidence is anchored above the chunk layer** as `(version_id, section_path, char_span)`; chunk IDs are diagnostic only.
3. **Small-n results use paired per-case comparisons**, not claims based only on category averages.
4. **No scalar exact-identifier boost.** If tested, exact identifiers become a third ranked list in RRF (EXP-003B).
5. PostgreSQL FTS uses a generated `TSVECTOR` and a GIN index with the `simple` configuration.
6. Retry/reranker are out of V1; future retry must preserve and fuse first-attempt candidates.
7. Embeddings are cached by `(chunk_id, model_id)` and model metadata is first-class.
8. Deterministic evaluation is preferred where possible; LLM judges are reserved for semantic cases.
9. Raw provider snapshots remain gitignored. The public repo contains manifests, hashes, and fetch/ingest logic—not copied docs.
10. Live corpora and immutable evaluation snapshots are separate concepts.

## Experiment order

- `EXP-NULL`: no retrieval; measures what the generation model already knows.
- `EXP-000`: PostgreSQL lexical retrieval baseline.
- `EXP-001`: dense retrieval baseline.
- `EXP-002`: transparent lexical/dense interleave.
- `EXP-003`: pure RRF; test `rrf_k` values rather than assuming one.
- `EXP-003B` (optional): exact-identifier third ranked list.
- `EXP-004+`: only after V1 produces real failure data.

## V1 definition of done

- Seed corpus ingested and snapshotted immutably.
- 20 human-verified evaluation cases with stable evidence spans.
- EXP-NULL through EXP-003 run on the same snapshot.
- Per-case traces retained.
- Paired rescue/regression analysis published.
- At least one real failure is diagnosed and fixed or explicitly left unresolved.
