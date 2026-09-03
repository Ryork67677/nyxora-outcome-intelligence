# EXP-021B — SECTION-STRATIFIED LOCAL-W20 COMPRESSION

**EXP-021B_SUPPORTED = FALSE**

Candidate-generation / compression only on NATQ-001 validation n=40, DEVELOPMENT / MODEL-SELECTION DATA. Not independent validation. Holdout was not opened. SYSTEM-H / SYSTEM-I / SYSTEM-J / G / E were not modified. CE and final ranking were not run. W/L/P were not increased. EXTRA_BUDGET=30 was not changed after results. EXP-020A parent-balanced projection was not included.

## Setup

- Preregistration sha256 `f5cfb249f76e9fbb68230ae034bb9ccdab173354482caf71c8b3cc0d1893fb3e` hashed before computing SYSTEM-K aggregate candidate metrics.
- SYSTEM-K-W20-SECTION-COMPRESS config_hash `eef589c085ea7e88fdc729d83021b311e2927310fc6368b54a87f374859bdec8` (file sha256 `20d967e2f56fed88f617d1c18474abc86b9f984f32a30cc195f42d6fef03ad7e`).
- Parent SYSTEM-H config_hash `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` unchanged after run: **True**.
- Parent SYSTEM-J config_hash `b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787` unchanged after run: **True**.
- SYSTEM-I config_hash `9103a51eaaebcbc581df452279ea06c880abb7524053606428dfd77649d4b3d6` unchanged after run: **True**.
- Split: `evals/splits/natq-001/validation.jsonl` n=40, sha256 `a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6`.
- Snapshot `snap_689e336380a054d8039dc35b2c09cd0a`. Projection `ps_v2_ovl_win448_s224` n=18057.
- Used stored EXP-021A H/J ids. BM25 W=20 recomputed only to attach scores and verify identity with stored w20_by_parent.
- Two-pass section-stratified compression, EXTRA_BUDGET=30, max 2 extras per (version_id, section_path), never drop H.
- NATQ holdout-access log after: 0 bytes, sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- V1 holdout-access log after: 235 bytes, sha256 `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`.
- holdout_json_opened: **false**. v1_holdout_json_opened: **false**.
- Environment drift: PostgreSQL 16.15 / pgvector 0.8.6 vs historical 16.13 / 0.6.0.

## PRIMARY — candidate full-case Recall@pool

| metric | SYSTEM-H | SYSTEM-J | SYSTEM-K |
| --- | ---: | ---: | ---: |
| candidate full-case Recall@pool | 34/40 | 37/40 | **35/40** |

## SECONDARY

| metric | SYSTEM-H | SYSTEM-J | SYSTEM-K |
| --- | ---: | ---: | ---: |
| candidate span micro | 46/53 | 50/53 | **48/53** |
| mean pool size | 118.83 | 187.12 | 146.78 |
| median pool size | 119.5 | 186.0 | 149.0 |
| p95 pool size | 127.1 | 249.35 | 156.05 |
| mean / median additions | — | 68.3 / 66.0 | 27.95 / 30.0 |
| compression ratio mean_K/mean_J | — | — | 0.784416 |
| compression saved 1 - ratio | — | — | 0.215584 |
| exact superset vs SYSTEM-H | — | True | True |
| candidate-gen latency mean ms | — | 1301.0 | 1301.1 (J cg + compression) |
| compression selection mean / median ms | — | — | 0.118 / 0.108 |
| W20 score-association recompute mean ms | — | — | 213.6 |

### Pool / CE-pair estimate

| | |
| --- | ---: |
| baseline SYSTEM-H mean pool | 118.83 |
| SYSTEM-J mean pool | 187.12 |
| SYSTEM-K mean pool | 146.78 |
| estimated CE pairs SYSTEM-K | 5871 |
| estimated CE pairs SYSTEM-J | 7485 |
| estimated CE pairs SYSTEM-H | 4753 |

CE was **not** run. The CE-pair estimate is `sum(pool_size)` over 40 queries.

### Per-provider candidate recall

| provider | H case | J case | K case | H span | J span | K span |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | 15/18 | 17/18 | 16/18 | 20/23 | 22/23 | 21/23 |
| anthropic | 19/22 | 20/22 | 19/22 | 26/30 | 28/30 | 27/30 |

### Multi-span candidate ceiling

Subset n=12 (n_gold_spans>1 or tag multi_span). SYSTEM-H **8/12**. SYSTEM-J **10/12**. SYSTEM-K **8/12**.

## Diagnostics — four SYSTEM-J recovered spans (after aggregates)

Diagnostic only. No named-case handling. Identities are the four spans SYSTEM-J recovered over SYSTEM-H.

| case | span | retained by K | group section_path | local-BM25 rank | pass | K position |
| --- | ---: | --- | --- | ---: | --- | ---: |
| `NATQ-C-004` | 0 | True | `['Wrap with encryption and TTL', 'Operational patterns', 'Memory persistence']` | 18 | 1 | 150 |
| `NATQ-C-005` | 1 | False | `['Human-in-the-loop', 'Marking tools that need approval']` | 13 | none | None |
| `NATQ-C-044` | 0 | False | `['Tool versions']` | 11 | none | None |
| `NATQ-C-044` | 1 | True | `['How it works']` | 5 | 1 | 123 |

Newly lost gold spans vs SYSTEM-J: **2**. Newly retained gold spans vs SYSTEM-J: **0**.

Lost vs J:
- `NATQ-C-005` s1 covering=['chk_5451da95f9f8e826733d725bcd4366a236272733']
- `NATQ-C-044` s0 covering=['chk_d6c502d2d4b45c2db0abc29c2c98d6171600a157']

## Gate

| condition | result |
| --- | --- |
| candidate full-case recall >= 36/40 (35/40) | False |
| candidate span recall >= 49/53 (48/53) | False |
| mean candidate pool <= 150 (146.78) | True |
| every original SYSTEM-H candidate remains present | True |
| no integrity/provenance failure | True |

**EXP-021B_SUPPORTED = FALSE**

## Interpretation

EXP-021B did not pass the preregistered gate. Do not change EXTRA_BUDGET after seeing results. Do not try another budget in this experiment. Return to coordinator ChatGPT.

## STOP

Stop after EXP-021B. Do **not** run CE. Do **not** run final ranking. Do **not** try another budget. Do **not** alter EXTRA_BUDGET=30. Do **not** open holdout. Return to coordinator ChatGPT.
