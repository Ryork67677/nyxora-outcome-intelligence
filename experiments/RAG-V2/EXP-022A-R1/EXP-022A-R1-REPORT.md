# EXP-022A-R1 — CONTROLLED CE REPLAY + SYSTEM-J RECOGNIZABILITY

**EXP-022A-R1_CE_RECOGNIZABILITY_SUPPORTED = FALSE**

NATQ-001 validation n=40 is DEVELOPMENT / MODEL-SELECTION DATA. Not independent validation. This is a development replay / diagnostic, not EVAL-NATQ-VAL-002. Holdout was not opened. SYSTEM-H / SYSTEM-J / SYSTEM-K were not modified. Original EXP-022A remains CLOSED unscored as STOPPED_MISSING_STORED_H_CE_LOGITS and was not rewritten.

scored=true. One CE call per query on exact stored J_IDS. Stored logits=7485.

## Setup / lock

- Preregistration sha256 `29be7cfc9f22c2e182016baa81f1e8bca5a9dfeae6e5e518594cab24f4d6ff48` hashed before any raw CE logits.
- Raw-logit JSONL sha256 `abd00619d538a5a497c36cf588b9d4eeed760ca343aaf1925ce466b3619c677c`.
- SYSTEM-H config_hash `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` file sha `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475` unchanged: **True**.
- SYSTEM-J config_hash `b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787` file sha `70acac77f33dbe1f7fc0f2e9b81f8a995c7fd0e9f47bab662f03f12cdecc0fdd` unchanged: **True**.
- SYSTEM-K config_hash `eef589c085ea7e88fdc729d83021b311e2927310fc6368b54a87f374859bdec8` file sha `20d967e2f56fed88f617d1c18474abc86b9f984f32a30cc195f42d6fef03ad7e` unchanged: **True** (not tested).
- validation.jsonl sha256 `a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6`.
- Frozen CE ONNX sha `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`. Module CE_SHA256 `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`. Live artifact `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`. Fingerprint match: **True**.
- Constructor `CrossEncoderReranker(pad='batch', bucket_by_length=True)`; fast=False; threads=4; batch_size=16; max_length=512; D1 bucket_by_length.
- Membership: H=4753, J=7485, J-only=2732; H subset J every query: **True**.
- Persistence gate: unique 7485, H-member 4753, J-only 2732, missing 0, duplicate disagreements 0.
- NATQ holdout-access log after: 0 bytes, sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- V1 holdout-access log after: 235 bytes, sha256 `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`.
- holdout_json_opened: **false**. v1_holdout_json_opened: **false**.
- Environment drift: PostgreSQL 16.15 / pgvector 0.8.6 vs historical 16.13 / 0.6.0. CE replay used stored membership and does not depend on pgvector..
- EXP-022A files unchanged: **True**.

## PRIMARY — strict full-case Recall@10 (CE-only)

| arm | strict R@10 |
| --- | ---: |
| H CE-only | 19/40 |
| J CE-only | **19/40** |
| delta cases | 0 |

## SECONDARY

| metric | H CE-only | J CE-only |
| --- | ---: | ---: |
| evidence-span R@10 | 26/53 | 26/53 |
| MRR (summarise: mean 1/rank all gold spans) | 0.2873 | 0.2864 |
| document R@10 (all gold docs in top-10) | 35/40 | 35/40 |
| document recall mean | 0.9 | 0.9 |
| multi-span strict | 1/12 | 1/12 |
| multi-span span | 8/25 | 8/25 |

### Provider

| provider | n | H strict | J strict | H span | J span |
| --- | ---: | ---: | ---: | ---: | ---: |
| openai | 18 | 11/18 | 11/18 | 14/23 | 14/23 |
| anthropic | 22 | 8/22 | 8/22 | 12/30 | 12/30 |

## PAIRED MOVEMENT

- J rescues over H: 0 []
- J regressions vs H: 0 []
- both pass: 19
- both fail: 21
- McNemar exact p (diagnostic): n01=0 n10=0 p=1.0. No significance claim.

## Diagnostics — four SYSTEM-J recovered spans (after aggregates)

| case | span | raw CE logit | J CE-only rank | top10 | n higher same version_id | n higher same section_path |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| `NATQ-C-004` | 0 | -6.049786567687988 | 80 | False | 14 | 0 |
| `NATQ-C-005` | 1 | -0.35656341910362244 | 42 | False | 7 | 2 |
| `NATQ-C-044` | 0 | -1.5396829843521118 | 46 | False | 6 | 0 |
| `NATQ-C-044` | 1 | -6.526081085205078 | 111 | False | 14 | 1 |

## MULTI-SPAN

| case | required | in J pool | in J top10 | unique version_ids top10 | unique section_paths top10 | redundancy version | redundancy section |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `NATQ-C-201` | 2 | 2 | 1 | 4 | 10 | 6 | 0 |
| `NATQ-C-005` | 2 | 2 | 0 | 8 | 10 | 2 | 0 |
| `NATQ-C-012` | 2 | 2 | 1 | 6 | 10 | 4 | 0 |
| `NATQ-C-014` | 2 | 1 | 0 | 6 | 10 | 4 | 0 |
| `NATQ-C-017` | 2 | 2 | 1 | 7 | 10 | 3 | 0 |
| `NATQ-C-023` | 2 | 2 | 0 | 6 | 10 | 4 | 0 |
| `NATQ-C-044` | 3 | 3 | 1 | 7 | 10 | 3 | 0 |
| `NATQ-C-160` | 2 | 2 | 0 | 4 | 8 | 6 | 2 |
| `NATQ-C-026` | 3 | 2 | 1 | 7 | 10 | 3 | 0 |
| `NATQ-C-170` | 1 | 1 | 1 | 5 | 8 | 5 | 2 |
| `NATQ-C-030` | 2 | 2 | 1 | 7 | 9 | 3 | 1 |
| `NATQ-C-032` | 2 | 2 | 1 | 7 | 10 | 3 | 0 |

In-pool gold span CE-only ranks:

- `NATQ-C-201`: s0=in_pool rank 2, s1=in_pool rank 13
- `NATQ-C-005`: s0=in_pool rank 20, s1=in_pool rank 42
- `NATQ-C-012`: s0=in_pool rank 12, s1=in_pool rank 5
- `NATQ-C-014`: s0=in_pool rank 27, s1=not in pool
- `NATQ-C-017`: s0=in_pool rank 119, s1=in_pool rank 2
- `NATQ-C-023`: s0=in_pool rank 18, s1=in_pool rank 41
- `NATQ-C-044`: s0=in_pool rank 46, s1=in_pool rank 111, s2=in_pool rank 2
- `NATQ-C-160`: s0=in_pool rank 114, s1=in_pool rank 59
- `NATQ-C-026`: s0=in_pool rank 2, s1=not in pool, s2=in_pool rank 108
- `NATQ-C-170`: s0=in_pool rank 2
- `NATQ-C-030`: s0=in_pool rank 27, s1=in_pool rank 6
- `NATQ-C-032`: s0=in_pool rank 1, s1=in_pool rank 50

## LATENCY

- total CE wall time: 123.978 s (123978.183 ms)
- mean per-query CE time: 3099.455 ms
- median per-query CE time: 2926.858 ms
- H-pair count: 4753
- J-only pair count: 2732
- full J-pair count: 7485
- No cross-host architecture claim.

## HARNESS FIX (NON-SCORING follow-up)

EVAL-NATQ-VAL-001 did not persist full-pool raw CE logits. Future development/validation reranker executions must persist candidate membership, raw reranker logits, query/candidate association, model fingerprint, and input/config fingerprint. Historical EVAL-NATQ-VAL-001 artifacts were not modified. Historical logits were not fabricated.

## Gate

| condition | result |
| --- | --- |
| J strict R@10 improves over H by >= 2 cases (0) | False |
| J span R@10 improves over H by >= 2 spans (0) | False |
| J strict regressions vs H <= 1 (0) | True |
| no integrity/provenance failure | True |

**EXP-022A-R1_CE_RECOGNIZABILITY_SUPPORTED = FALSE**

## STOP

Return to coordinator ChatGPT. Did not build a coverage-aware selector, test SYSTEM-K, modify W/L/P, change CE, or open holdout.
