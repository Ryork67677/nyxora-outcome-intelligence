# CORPUS-001 — local artifact inventory

*2026-08-31T03:55:16Z*. Read-only. Nothing was deleted, moved or rewritten.

Searched the repository for archives, database dumps, SQLite files, SQL exports, JSONL exports and the corpus data directories. **18 artifacts** were catalogued.

## The result in one line

**No corpus material was found.** `data/raw/` and `data/cache/` contain nothing but their `.gitkeep` files — they are gitignored, and the container was cloned fresh, so nothing local survived. No ZIP, no dump, no SQLite file, no normalized-text cache.

## Artifacts

| path | type | size | relevance | what it could hold |
| --- | --- | --- | --- | --- |
| `data/manifests/fetch-compliance.json` | corpus_data_dir | 1,260 | HIGH | data/raw and data/cache are where captures would live |
| `data/manifests/sources.example.yaml` | corpus_data_dir | 448 | HIGH | data/raw and data/cache are where captures would live |
| `data/manifests/v1-openai-anthropic.yaml` | corpus_data_dir | 110,498 | HIGH | data/raw and data/cache are where captures would live |
| `evals/development/v1.jsonl` | jsonl_export | 15,429 | LOW | GOLD candidate projections; no document normalized text |
| `evals/gold/batch_001_v2/projection.jsonl` | jsonl_export | 21,033 | LOW | GOLD candidate projections; no document normalized text |
| `evals/gold/batch_004_projection.jsonl` | jsonl_export | 22,339 | LOW | GOLD candidate projections; no document normalized text |
| `evals/gold/batch_005_projection.jsonl` | jsonl_export | 21,668 | LOW | GOLD candidate projections; no document normalized text |
| `evals/gold/batch_006_projection.jsonl` | jsonl_export | 11,945 | LOW | GOLD candidate projections; no document normalized text |
| `evals/golden/candidates.jsonl` | jsonl_export | 16,204 | LOW | GOLD candidate projections; no document normalized text |
| `evals/golden/v1.jsonl` | jsonl_export | 11,451 | LOW | GOLD candidate projections; no document normalized text |
| `evals/golden/v1.sample.jsonl` | jsonl_export | 652 | LOW | GOLD candidate projections; no document normalized text |
| `evals/review/batch_001_approved_projection.jsonl` | jsonl_export | 21,531 | LOW | GOLD candidate projections; no document normalized text |
| `evals/review/batch_002_approved_projection.jsonl` | jsonl_export | 21,974 | LOW | GOLD candidate projections; no document normalized text |
| `evals/review/batch_003_approved_projection.jsonl` | jsonl_export | 32,326 | LOW | GOLD candidate projections; no document normalized text |
| `sql/001_init.sql` | sql | 5,114 | MEDIUM | schema only; defines document_version and corpus_snapshot but carries no rows |
| `sql/002_chunk_sets.sql` | sql | 3,013 | MEDIUM | schema only; defines document_version and corpus_snapshot but carries no rows |
| `sql/003_search_text.sql` | sql | 2,121 | MEDIUM | schema only; defines document_version and corpus_snapshot but carries no rows |
| `sql/004_embedding_cache.sql` | sql | 1,233 | MEDIUM | schema only; defines document_version and corpus_snapshot but carries no rows |

## The database

Tables sought: `corpus_snapshot`, `corpus_snapshot_version`, `document`, `document_version`, `document_source`. sql/001_init.sql defines all of them; it carries no rows.

A PostgreSQL 16 cluster **does** exist at `/var/lib/postgresql/16/main`, found `down` and left `down`. Started read-only to enumerate: it holds `postgres`, `template0`, `template1` and nothing else (base OIDs on disk: 1, 4, 5 — the three defaults). only the three default databases; no project database, no document_version rows, no corpus_snapshot rows. Inspected read-only: no migration was run and no table was modified.

Docker: no docker daemon and no /var/lib/docker in this environment. Dumps found: 0.

**Verdict: the historical project database is not in this environment.**

## What did survive

2460 `ver_` references across 71 files — 89 distinct document identities the corpus itself no longer has to supply. Top sources:

| file | version ids |
| --- | --- |
| `experiments/EXP-012/results-n10.json` | 117 |
| `experiments/EXP-012/results.json` | 84 |
| `experiments/EXP-014/results.json` | 83 |
| `experiments/EXP-003/sweep/pool100-rrfk10.json` | 76 |
| `experiments/EXP-003/sweep/pool50-rrfk10.json` | 76 |
| `experiments/EXP-001/results.json` | 76 |
| `experiments/EXP-003/results-k10.json` | 75 |
| `experiments/EXP-003/sweep/pool10-rrfk20.json` | 75 |
| `experiments/EXP-003/sweep/pool20-rrfk20.json` | 75 |
| `experiments/EXP-003/sweep/pool10-rrfk10.json` | 75 |

