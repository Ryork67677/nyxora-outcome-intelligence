# EVAL-NATQ-VAL-001 — SYSTEM-H NATURAL-QUERY VALIDATION

## VALIDATION_NOT_SUPPORTED

Frozen SYSTEM-H-V2-DEV-CANDIDATE scored **exactly once** on NATQ-001 validation n=40. Preregistration sha256 `3d91f14acfa2cbc1c0368781ac0dd4783cc331677e6d0ecc425ed07b1abd1dd3` hashed before any retrieval. Holdout was not opened. SYSTEM-H / SYSTEM-G / SYSTEM-G-CE-D1 were not modified. No retune. No second run. No release freeze.

## Setup

- Split: `evals/splits/natq-001/validation.jsonl` n=40, sha256 `a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6`.
- SYSTEM-H config_hash `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` (file sha256 `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475`), unchanged after run: **True**.
- Snapshot `snap_689e336380a054d8039dc35b2c09cd0a`. Projection `ps_v2_ovl_win448_s224` n=18057.
- CE: `cross-encoder/ms-marco-MiniLM-L6-v2` D1 `pad='batch', bucket_by_length=True`, batch_size=16, threads=4, onnx sha `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`.
- Blend 0.7 CE / 0.3 retrieval (EXP-019A projection-aware prior). L=10, P=20.
- NATQ holdout-access log after: 0 bytes, sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- V1 holdout-access log after: 235 bytes, sha256 `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`.
- holdout_json_opened: **false**. v1_holdout_json_opened: **false**.

## PRIMARY — strict full-case Recall@10

| metric | value |
| --- | ---: |
| strict Recall@10 | **20/40** (50.0%) |
| 95% Clopper-Pearson CI (diagnostic) | [0.338, 0.662] |

## SECONDARY

| metric | value |
| --- | ---: |
| candidate gold-span Recall@100 | **34/40** |
| candidate gold spans in union (span-level) | 46/53 |
| evidence-span Recall@10 (micro) | **0.5094** (27/53) |
| evidence-span Recall@10 (macro) | 0.5667 |
| document Recall@10 | **35/40** |
| document recall mean | 0.9 |
| MRR | 0.2952 |
| latency mean / median (ms) | 3752.1 / 3760.6 |
| SYSTEM-A mean (ms) | 438.3 |
| E-L10 mean (ms) | 218.3 |
| projection mean (ms) | 657.9 |
| CE mean / median (ms) | 2435.8 / 2492.1 |
| blend mean (ms) | 0.5324 |

### Provider

| provider | n | strict | cand R@100 | span R@10 | doc R@10 | MRR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | 18 | 11/18 | 15/18 | 14/23 (0.6087) | 17/18 | 0.3443 |
| anthropic | 22 | 9/22 | 19/22 | 13/30 (0.4333) | 18/22 | 0.2577 |

### Exact-identifier / multi-span / natural paraphrase

| subset | n | strict | cand R@100 | span R@10 | doc R@10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| exact_identifier_lookup | 17 | 9/17 | 15/17 | 11/21 (0.5238) | 15/17 |
| multi_span | 12 | 2/12 | 8/12 | 9/25 (0.36) | 10/12 |
| realistic_paraphrase | 5 | 4/5 | 4/5 | 5/7 (0.7143) | 5/5 |

### Coverage / stress-tag breakdown

| tag | n | strict | cand R@100 | span R@10 |
| --- | ---: | ---: | ---: | ---: |
| `exact_identifier_lookup` | 17 | 9/17 | 15/17 | 11/21 |
| `configuration_interaction` | 15 | 6/15 | 13/15 | 9/20 |
| `short_evidence` | 13 | 8/13 | 12/13 | 9/14 |
| `short_evidence_unit` | 11 | 7/11 | 10/11 | 8/12 |
| `same_document_passage_discrimination` | 9 | 5/9 | 7/9 | 6/11 |
| `error_behavior` | 7 | 4/7 | 7/7 | 5/8 |
| `realistic_paraphrase` | 5 | 4/5 | 4/5 | 5/7 |
| `long_document_localization` | 5 | 1/5 | 2/5 | 4/11 |
| `multi_span` | 5 | 1/5 | 4/5 | 3/9 |
| `version_model_discrimination` | 2 | 2/2 | 2/2 | 2/2 |
| `identifier_vs_semantic_distractor` | 2 | 2/2 | 2/2 | 2/2 |
| `lifecycle_migration` | 2 | 0/2 | 2/2 | 0/3 |
| `parameter_error_literal_lookup` | 1 | 1/1 | 1/1 | 1/1 |

## Failure taxonomy (strict misses; no retune)

| class | n |
| --- | ---: |
| candidate-generation | 6 |
| ranking | 14 |

### Strict failures

| case | provider | primary | span classes | ranks | in_pool | tags |
| --- | --- | --- | --- | --- | --- | --- |
| `NATQ-C-201` | openai | ranking | ['ranking'] | [3, 14] | [True, True] | configuration_interaction,long_document_localization |
| `NATQ-C-002` | openai | ranking | ['ranking'] | [65] | [True] | same_document_passage_discrimination,short_evidence |
| `NATQ-C-004` | openai | candidate-generation | ['candidate-generation'] | [None] | [False] | configuration_interaction,short_evidence |
| `NATQ-C-005` | openai | candidate-generation | ['ranking', 'candidate-generation'] | [11, None] | [True, False] | realistic_paraphrase,long_document_localization |
| `NATQ-C-008` | openai | ranking | ['ranking'] | [13] | [True] | error_behavior,short_evidence |
| `NATQ-C-014` | openai | candidate-generation | ['ranking', 'candidate-generation'] | [27, None] | [True, False] | configuration_interaction,multi_span |
| `NATQ-C-179` | anthropic | candidate-generation | ['candidate-generation'] | [None] | [False] | same_document_passage_discrimination,exact_identifier_lookup |
| `NATQ-C-017` | anthropic | ranking | ['ranking'] | [48, 2] | [True, True] | configuration_interaction,multi_span |
| `NATQ-C-023` | anthropic | ranking | ['ranking', 'ranking'] | [17, 43] | [True, True] | configuration_interaction,multi_span |
| `NATQ-C-155` | anthropic | ranking | ['ranking'] | [32] | [True] | configuration_interaction,short_evidence |
| `NATQ-C-071` | anthropic | ranking | ['ranking'] | [91] | [True] | configuration_interaction,error_behavior |
| `NATQ-C-021` | anthropic | ranking | ['ranking'] | [13] | [True] | exact_identifier_lookup,short_evidence |
| `NATQ-C-044` | anthropic | candidate-generation | ['candidate-generation', 'candidate-generation'] | [None, None, 3] | [False, False, True] | exact_identifier_lookup,long_document_localization |
| `NATQ-C-160` | anthropic | ranking | ['ranking', 'ranking'] | [98, 23] | [True, True] | lifecycle_migration,exact_identifier_lookup |
| `NATQ-C-025` | anthropic | ranking | ['ranking'] | [21] | [True] | exact_identifier_lookup,lifecycle_migration |
| `NATQ-C-026` | anthropic | candidate-generation | ['candidate-generation', 'ranking'] | [2, None, 77] | [True, False, True] | same_document_passage_discrimination,long_document_localization |
| `NATQ-C-029` | anthropic | ranking | ['ranking'] | [19] | [True] | exact_identifier_lookup,same_document_passage_discrimination |
| `NATQ-C-030` | anthropic | ranking | ['ranking'] | [51, 6] | [True, True] | error_behavior,multi_span |
| `NATQ-C-032` | openai | ranking | ['ranking'] | [1, 15] | [True, True] | exact_identifier_lookup,configuration_interaction |
| `NATQ-C-033` | anthropic | ranking | ['ranking'] | [14] | [True] | exact_identifier_lookup,configuration_interaction |

### Gold-ambiguity flags

None flagged. Gold was not altered.


## Gate

| condition | result |
| --- | --- |
| strict ≥ 32/40 (20/40) | False |
| candidate gold-span R@100 ≥ 36/40 (34/40) | False |
| evidence-span R@10 ≥ 0.80 (0.5094 = 27/53) | False |
| document R@10 ≥ 38/40 (35/40) | False |
| no benchmark-integrity failure | True |
| NATQ holdout untouched | True |

**VALIDATION_SUPPORTED = FALSE**

## STOP

Stop after EVAL-NATQ-VAL-001. Do **not** run holdout. No second validation run. No retune. No release freeze.
