# EXP-022A — SYSTEM-J CE RECOGNIZABILITY DIAGNOSTIC

## STOPPED_MISSING_STORED_H_CE_LOGITS

NATQ-001 validation n=40 is DEVELOPMENT / MODEL-SELECTION DATA. Not independent validation. Holdout was not opened. SYSTEM-H / SYSTEM-J / SYSTEM-K were not modified. H CE was **not** rerun. J extras were **not** scored.

**scored = false**. **H_CE_rerun = false**. **J_EXTRAS_CE_run = false**. **EXP-022A_CE_RECOGNIZABILITY_SUPPORTED** was **not evaluated**.

## Setup / lock

- Preregistration sha256 `ad7fba5a38d6fda06fdb42a94f0b78fdce008cfe978b1743224028bb2fd8e64b` hashed before any aggregate J CE-only metrics (none computed).
- SYSTEM-H config_hash `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` file sha `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475` unchanged: **True**.
- SYSTEM-J config_hash `b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787` file sha `70acac77f33dbe1f7fc0f2e9b81f8a995c7fd0e9f47bab662f03f12cdecc0fdd` unchanged: **True**.
- SYSTEM-K config_hash `eef589c085ea7e88fdc729d83021b311e2927310fc6368b54a87f374859bdec8` file sha `20d967e2f56fed88f617d1c18474abc86b9f984f32a30cc195f42d6fef03ad7e` unchanged: **True** (not tested).
- validation.jsonl sha256 `a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6`.
- Frozen CE ONNX sha `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`. EVAL report artifact sha `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`. Module CE_SHA256 `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`. File sha `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`. Fingerprint match: **True**.
- NATQ holdout-access log after: 0 bytes, sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- V1 holdout-access log after: 235 bytes, sha256 `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`.
- holdout_json_opened: **false**. v1_holdout_json_opened: **false**.
- Environment drift: PostgreSQL 16.15 / pgvector 0.8.6 vs historical 16.13 / 0.6.0.

## HARD STOP — stored H raw CE logits incomplete

ARM H must reconstruct CE-only ranking over the exact SYSTEM-H pool using raw CE logits already stored from EVAL-NATQ-VAL-001. Those logits are missing.

| item | count |
| --- | ---: |
| SYSTEM-H candidates required (system_h_union_ids, 40 queries) | 4753 |
| stored raw CE pairs matching H (query, chunk_id) | 0 |
| missing H logits | 4753 |
| stored raw CE pairs any source | 0 |
| EVAL pools queries | 40 |
| EVAL pools top-10 rows | 400 |
| EVAL pools top-10 blend_score (NOT raw CE) | 400 |
| EVAL pools top-10 raw CE fields | 0 |
| EVAL REPORT per_case n | 40 |

EVAL-NATQ-VAL-001-pools.jsonl hit keys: `['blend_score', 'chunk_id', 'origin', 'rank', 'version_id']`.
REPORT per_case keys: `['all_gold_spans_in_pool', 'case_id', 'coverage_tags', 'doc_recall', 'e_pool_size', 'failure', 'fully_recalled', 'latency_ms', 'n_gold_spans', 'n_projection_additions', 'parents', 'provider', 'recall', 'requires_all_evidence', 'spans', 'stress_types', 'union_pool_size']`.
REPORT span keys: `['covering_chunk_ids', 'doc_in_top_10', 'gold_in_e_l10', 'gold_origin', 'in_pool', 'pool_rank', 'rank', 'span_index', 'within_10']`.

EVAL-NATQ-VAL-001 persisted only top-10 blend_score rows (not raw CE logits for the full SYSTEM-H pool). ARM H cannot be reconstructed without rerunning H CE.

EVAL-NATQ-VAL-001 computed CE in memory (`ce_by_id`) and wrote only top-10 `blend_score` (0.7 CE_norm + 0.3 retrieval_norm). `blend_score` is not a raw CE logit and covers 400 rows, not 4753 H candidates. PERF-003 `*-logits.jsonl` artifacts are V2-DEVSET case ids (e.g. V2D-01), not NATQ-001 validation.

No integrity/provenance failure on holdouts or frozen identity files. The stop is the assigned missing-logit behavior, not a crash.

## Gate

EXP-022A_CE_RECOGNIZABILITY_SUPPORTED **not evaluated** (scoring did not run).

## STOP

Stop after EXP-022A. Do **not** rerun H CE as a workaround. Do **not** score J extras. Do **not** run a coverage-aware selector. Do **not** run SYSTEM-K. Do **not** invent a retrieval prior. Return to coordinator ChatGPT.
