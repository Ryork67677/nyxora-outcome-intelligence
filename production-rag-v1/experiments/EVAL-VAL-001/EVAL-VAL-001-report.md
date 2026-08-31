# EVAL-VAL-001 — validation replication of SYSTEM-A vs SYSTEM-B

## REPLICATION_REJECTS_B

On 40 independent, previously unseen cases **SYSTEM-B retrieved worse than SYSTEM-A**: 21/40 against 30/40 on strict full-case recall@10, with 2 rescues against 11 regressions (net -9).

**The DOC-C mechanism is contradicted rather than merely unhelpful: 12 of B's failures are cases where a required document never reached Stage 2. Stage-1 routing discards evidence that the global system ranks successfully.**

*This is a measurement, not a promotion. The classification is returned to the project owner; no system was promoted, demoted or changed by this task.*

## The historical result did not replicate

| | development (n=20, exposed) | validation (n=40, unseen) |
| --- | --- | --- |
| SYSTEM-A strict | 15/20 | 30/40 |
| SYSTEM-B strict | 17/20 | 21/40 |
| B rescues | 2 | 2 |
| B regressions | 0 | 11 |
| net | +2 | -9 |

The development figures were re-run this session and reproduced exactly, so the difference is not a harness change. Re-run this session against the same development split and every figure matched: 15/20, 17/20, +2 rescues (AN-006, AN-011), 0 regressions, macro 0.775 / 0.875, MRR 0.449 / 0.474.

## Primary endpoint — strict full-case recall@10

| system | fully recalled | of | percentage |
| --- | --- | --- | --- |
| SYSTEM-A-GLOBAL | **30** | 40 | 75.0% |
| SYSTEM-B-DOC-C | **21** | 40 | 52.5% |
| difference | -9 | | -22.5 pp |

A case passes only when every required span is in the top 10. Multi-span cases are never scored partially for this metric.

## Secondary metrics

| | SYSTEM-A | SYSTEM-B |
| --- | --- | --- |
| macro span recall@10 | 0.75 | 0.525 |
| spans retrieved | 33/47 | 24/47 |
| document recall | 0.975 | 0.675 |
| MRR | 0.5283 | 0.4022 |
| spans absent@10 | 14 | 23 |
| spans absent@30 | 6 | 14 |
| spans absent@50 | 5 | 13 |
| spans absent@100 | 4 | 12 |
| spans absent@300 | 4 | 12 |

**Document recall is the headline.** SYSTEM-A reaches 0.975 and SYSTEM-B only 0.675: the routed system is losing the source document itself, not merely ranking passages differently inside it.

## Paired analysis

- **B rescues (2)**: ['GOLD-B002-07', 'HA-44']
- **B regressions (11)**: ['GOLD-B001-01', 'GOLD-B001-10', 'GOLD-B002-01', 'GOLD-B003-08', 'GOLD-B003-15', 'GOLD-B004-04', 'GOLD-B005-09', 'GOLD-B005-15', 'GOLD-B005-17', 'GOLD-B005-19', 'HA-36']
- both pass: 19, both fail: 8
- net movement: **-9 cases**

### Causal trace for every movement

| case | movement | A ranks → B ranks | all docs routed@5 | attribution |
| --- | --- | --- | --- | --- |
| `GOLD-B001-01` | REGRESSION | [2] → [None] | False | caused by Stage-1 routing: a required document was not in the routed top 5, so Stage 2 could never retrieve its passage |
| `GOLD-B001-10` | REGRESSION | [1] → [None] | False | caused by Stage-1 routing: a required document was not in the routed top 5, so Stage 2 could never retrieve its passage |
| `GOLD-B002-01` | REGRESSION | [2] → [None] | False | caused by Stage-1 routing: a required document was not in the routed top 5, so Stage 2 could never retrieve its passage |
| `GOLD-B003-08` | REGRESSION | [4] → [None] | False | caused by Stage-1 routing: a required document was not in the routed top 5, so Stage 2 could never retrieve its passage |
| `GOLD-B003-15` | REGRESSION | [1] → [None] | False | caused by Stage-1 routing: a required document was not in the routed top 5, so Stage 2 could never retrieve its passage |
| `GOLD-B004-04` | REGRESSION | [9] → [None] | False | caused by Stage-1 routing: a required document was not in the routed top 5, so Stage 2 could never retrieve its passage |
| `GOLD-B005-09` | REGRESSION | [3] → [None] | False | caused by Stage-1 routing: a required document was not in the routed top 5, so Stage 2 could never retrieve its passage |
| `GOLD-B005-15` | REGRESSION | [2] → [None] | False | caused by Stage-1 routing: a required document was not in the routed top 5, so Stage 2 could never retrieve its passage |
| `GOLD-B005-17` | REGRESSION | [3] → [None] | False | caused by Stage-1 routing: a required document was not in the routed top 5, so Stage 2 could never retrieve its passage |
| `GOLD-B005-19` | REGRESSION | [1] → [None] | False | caused by Stage-1 routing: a required document was not in the routed top 5, so Stage 2 could never retrieve its passage |
| `HA-36` | REGRESSION | [6] → [None] | False | caused by Stage-1 routing: a required document was not in the routed top 5, so Stage 2 could never retrieve its passage |
| `GOLD-B002-07` | RESCUE | [24] → [9] | True | consistent with the DOC-C mechanism: every required document routed into the top 5 and the local passage rank improved |
| `HA-44` | RESCUE | [14] → [9] | True | consistent with the DOC-C mechanism: every required document routed into the top 5 and the local passage rank improved |

## Statistics

Paired bootstrap over 40 questions, 10000 resamples, seed `20250818`.

| quantity | point estimate | 95% CI |
| --- | --- | --- |
| macro span-recall delta (B−A) | -0.2250 | [-0.3750, -0.0750] |
| strict full-case delta per case | -0.2250 | [-0.3750, -0.0750] |

McNemar exact: 13 discordant pairs (2 B-only, 11 A-only), p = 0.0225.

The interval excludes zero and the test is nominally significant, but the direction is what matters here and it is unambiguous: both point the same way, against B. This is one comparison on one split of 40 — it is evidence that the development result did not replicate, not a precise effect size.

## Provider

| provider | cases | A strict | B strict | Δ | A span recall | B span recall |
| --- | --- | --- | --- | --- | --- | --- |
| `anthropic` | 14 | 10 (71.4%) | 7 (50.0%) | -3 | 0.7143 | 0.5 |
| `openai` | 26 | 20 (76.9%) | 14 (53.8%) | -6 | 0.697 | 0.5152 |

Provider performance is not provider quality: document structure, question mix and corpus share all differ, and the validation set is 65% OpenAI by construction.

## Reasoning type

| reasoning type | cases | A strict | B strict | Δ | A span recall | B span recall |
| --- | --- | --- | --- | --- | --- | --- |
| `configuration_interaction` | 6 | 6 (100.0%) | 5 (83.3%) | -1 | 1.0 | 0.8333 |
| `error_behavior` | 5 | 5 (100.0%) | 2 (40.0%) | -3 | 1.0 | 0.4 |
| `exact_lookup` | 16 | 10 (62.5%) | 8 (50.0%) | -2 | 0.5652 | 0.4783 |
| `lifecycle` * | 1 | 1 (100.0%) | 1 (100.0%) | +0 | 1.0 | 1.0 |
| `lifecycle_compatibility_migration` * | 2 | 1 (50.0%) | 0 (0.0%) | -1 | 0.5 | 0.0 |
| `request_response` * | 1 | 1 (100.0%) | 1 (100.0%) | +0 | 1.0 | 1.0 |
| `unlabeled_legacy` | 9 | 6 (66.7%) | 4 (44.4%) | -2 | 0.6667 | 0.4444 |

`*` marks a category with three or fewer cases. Those rows are individual observations; the percentages are shown for completeness and should not be read as rates.

## Evidence shape

| shape | cases | A strict | B strict | Δ | A span recall | B span recall |
| --- | --- | --- | --- | --- | --- | --- |
| `multi_span` * | 2 | 2 (100.0%) | 2 (100.0%) | +0 | 1.0 | 1.0 |
| `multi_span_same_fact` | 5 | 1 (20.0%) | 1 (20.0%) | +0 | 0.2 | 0.2 |
| `single_span` | 33 | 27 (81.8%) | 18 (54.5%) | -9 | 0.8182 | 0.5455 |

DOC-C was expected to help most on harder evidence structures. It does not: the regression is present across shapes.

## Routing diagnostics

SYSTEM-B routed all required documents into the top 5 for **28 of 40** cases.

| failure class | SYSTEM-B | SYSTEM-A (equivalent) |
| --- | --- | --- |
| DOCUMENT_ROUTING_FAILURE | 12 | 0 |
| WITHIN_DOCUMENT_PASSAGE_FAILURE | 7 | 10 |
| MIXED_FAILURE | 0 | 0 |
| NOT_APPLICABLE | 21 | 30 |

SYSTEM-A has no Stage 1, so its `DOCUMENT_ROUTING_FAILURE` means the global ranking never surfaced the document at all — a strictly harder failure than B's, which is a router discarding a document the global system would have found.

## The hypothesis under test

EXP-014 proposed that global competition hides useful passages and that document routing reduces it. On unseen data the opposite dominates: routing removes documents from contention before the passage layer can rank them. The development result rested on two rescued cases out of twenty; at four times the sample the same configuration loses nine net cases.

## Not done

- The holdout was not loaded, enumerated or run. holdout_runs = 0.
- No answer generation, faithfulness judge or citation judge was invoked.
- No system, parameter, model or index was changed.
- No system was promoted; the classification is returned for review.
