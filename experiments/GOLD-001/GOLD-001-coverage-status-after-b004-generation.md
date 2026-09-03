# GOLD-001 — coverage status after batch 004 generation

**Confirmed eligible today: 53.** Batch 004 adds 15 *candidates*, which are not eligible and not verified. The projection below is what coverage **would** be if every batch-004 candidate were later approved — no batch has ever approved every candidate, so treat it as a ceiling, not a forecast.

## Confirmed — batches 001–003 (human-approved, closed)

| batch | human_verified | holdout_eligible | rejected | genuine multi-hop |
| --- | --- | --- | --- | --- |
| 1 | 16 | 16 | 2 | 0 |
| 2 | 17 | 17 | 1 | 0 |
| 3 | 20 | 20 | 0 | 0 |
| **total** | **53** | **53** | **3** | **0** |

Read from `experiments/GOLD-001/GOLD-001-eligibility-status.json` and the closed batch records it names. Holdout frozen: **False**.

## Reasoning-type coverage

| reasoning type | confirmed (001–003) | batch 004 candidates | projected |
| --- | --- | --- | --- |
| `ambiguity_disambiguation` | 0 | 2 | 2 |
| `configuration_interaction` | 4 | 5 | 9 |
| `error_behavior` | 4 | 3 | 7 |
| `exact_lookup` | 43 | 3 | 46 |
| `genuine_multi_hop` | 0 | 1 | 1 |
| `lifecycle` | 2 | 0 | 2 |
| `lifecycle_compatibility_migration` | 0 | 1 | 1 |

Batches 001 and 002 are reported under `exact_lookup`, the label they were authored with: the reasoning-type/evidence-shape split arrived in batch 003, and relabelling closed batches to make the table look richer would be inventing coverage that was never reviewed. `lifecycle` and `lifecycle_compatibility_migration` are the same category under batch 003's name and batch 004's; they are listed separately for the same reason.

## Provider coverage

| provider | confirmed (001–003) | batch 004 candidates | projected |
| --- | --- | --- | --- |
| anthropic | 36 | 7 | 43 |
| openai | 17 | 8 | 25 |

## The gap batch 004 is aimed at

Genuine multi-hop in the confirmed set is **0**. Batch 004 proposes 1, with 1 drawing on more than one document. Whether that number survives review is the point of the batch; batch 003 proposed four and kept none.

## What this report does not say

- no batch-004 candidate is eligible, verified, or gold;
- no retrieval system was run against any candidate in any batch;
- the holdout is not frozen, and this report does not freeze it.
