# EVAL-HOLDOUT-001 — holdout of frozen SYSTEM-D-GUARD-BLEND

One-shot **SYSTEM-D-GUARD-BLEND** on gold150-v1 holdout, n=90. First and only holdout run.
No retuning. No second run. No answer-generation eval. SYSTEM-A was not evaluated as a
competing holdout system (A top-100 is D candidate generation only).

## Primary endpoint — strict full-case Recall@10

| system | fully recalled | of | percentage |
| --- | ---: | ---: | ---: |
| SYSTEM-D-GUARD-BLEND | **79** | 90 | 87.8% |

A case passes only when every required span is in the top 10.

## Secondary metrics

| metric | SYSTEM-D |
| --- | ---: |
| macro span recall@10 | 0.8833 |
| spans retrieved@10 | 92/104 |
| document recall | 0.9778 |
| MRR | 0.7055 |
| spans absent@10 | 12 |
| spans absent@20 | 9 |
| spans absent@50 | 8 |
| spans absent@100 | 7 |
| latency mean (ms) | 5640.3 |
| latency median (ms) | 5589.3 |

Candidate-pool coverage (not an A evaluation): 97/104 gold spans were present in the SYSTEM-A top-100 used as D's candidate generator.

## Setup (frozen before scoring)

- Split: `evals/splits/gold150-v1/holdout.json` n=90.
- `holdout_sha256` `756a3a9bc74ce3e2dd3a7924c4048984a0ae5e74237bc8053e18b6fec202d914` verified against `holdout.lock.json` **before scoring**.
- SYSTEM-D: `experiments/EVAL-HOLDOUT-001/SYSTEM-D-RELEASE.json` sha256 `1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40`.
- Implementation SYSTEM-D-GUARD-BLEND, config hash `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a` recomputed and matched freeze **before scoring**.
- Source freeze: `experiments/EXP-016/SYSTEM-D-GUARD.json` (same hash).
- Weights: 0.7 minmax CE + 0.3 minmax SYSTEM-A fused RRF, pool 100, tie-break blend desc / A rank / chunk_id.
- CE: `cross-encoder/ms-marco-MiniLM-L6-v2` rev `233902d25c440f23af6f7d6e94d2946bac0bee0a`, onnx sha256 `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`.
- Encoder fingerprint: `bd95feaeacf98559`.
- D scored **exactly once** on the 90 cases.
- Holdout access log: **235 bytes** after the run (0 before).
- Parameters were not changed after seeing any case.

## Failures (case IDs only; question text omitted)

11 / 90 not fully recalled@10: `GOLD-B001-02`, `GOLD-B001-09`, `GOLD-B002-06`, `GOLD-B003-04`, `GOLD-B005-07`, `GOLD-B006-02`, `HA-20`, `HA-21`, `HA-37`, `HA-43`, `HA-58`

## Provider

| value | cases | D strict | pct | span recall | doc recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| `openai` | 57 | 51/57 | 89.5% | 0.8947 | 0.9649 |
| `anthropic` | 33 | 28/33 | 84.8% | 0.8636 | 1.0 |

## Reasoning type

| value | cases | D strict | pct | span recall | doc recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| `exact_lookup` | 33 | 30/33 | 90.9% | 0.9091 | 0.9697 |
| `unlabeled_legacy` | 20 | 17/20 | 85.0% | 0.85 | 1.0 |
| `configuration_interaction` | 14 | 13/14 | 92.9% | 0.9286 | 0.9286 |
| `error_behavior` | 12 | 10/12 | 83.3% | 0.875 | 1.0 |
| `lifecycle_compatibility_migration` | 5 | 4/5 | 80.0% | 0.8 | 1.0 |
| `request_response` * | 3 | 2/3 | 66.7% | 0.6667 | 1.0 |
| `ambiguity_disambiguation` * | 1 | 1/1 | 100.0% | 1.0 | 1.0 |
| `genuine_multi_hop` * | 1 | 1/1 | 100.0% | 1.0 | 1.0 |
| `lifecycle` * | 1 | 1/1 | 100.0% | 1.0 | 1.0 |

## Evidence shape

| value | cases | D strict | pct | span recall | doc recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| `single_span` | 76 | 67/76 | 88.2% | 0.8816 | 0.9868 |
| `multi_span_same_fact` | 9 | 8/9 | 88.9% | 0.8889 | 0.8889 |
| `multi_span` | 4 | 3/4 | 75.0% | 0.875 | 1.0 |
| `multi_document` * | 1 | 1/1 | 100.0% | 1.0 | 1.0 |

`*` marks a category with three or fewer cases. Those rows are individual observations.

## What was not done

- No retuning, no weight search, no clamp swap (clamp was EXP-016 variant C, not D).
- No second retrieval system scored on holdout as an evaluation.
- No SYSTEM-A holdout score is reported.
- Development and validation were not loaded for scoring or cherry-picking.
- Answer generation was not run.
- Individual holdout failures were not debugged mid-run.

## Files

- `experiments/EVAL-HOLDOUT-001/EVAL-HOLDOUT-001-results.json`
- `experiments/EVAL-HOLDOUT-001/EVAL-HOLDOUT-001-per-case.json`
- `experiments/EVAL-HOLDOUT-001/EVAL-HOLDOUT-001-report.md`
- `experiments/EVAL-HOLDOUT-001/EVAL-HOLDOUT-001-environment.json`
- `evals/splits/gold150-v1/holdout-access.log.jsonl`
