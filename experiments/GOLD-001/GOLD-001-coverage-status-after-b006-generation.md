# GOLD-001 — coverage status after batch 006 generation

**Confirmed: 82 human_verified, 82 holdout_eligible, 8 rejected, 1 genuine multi-hop.** Batch 006 adds nothing to those numbers yet.

Read from `experiments/GOLD-001/GOLD-001-eligibility-status.json`.

## Confirmed — batches 001 to 005

| batch | human_verified | holdout_eligible | rejected | genuine multi-hop |
| --- | --- | --- | --- | --- |
| 001 | 16 | 16 | 2 | 0 |
| 002 | 17 | 17 | 1 | 0 |
| 003 | 20 | 20 | 0 | 0 |
| 004 | 14 | 14 | 1 | 1 |
| 005 | 15 | 15 | 4 | 0 |
| **all** | **82** | **82** | **8** | **1** |

## Projected — only if every batch-006 candidate were approved

| | confirmed | if all of batch 006 were approved |
| --- | --- | --- |
| `human_verified` | 82 | 91 |
| `holdout_eligible` | 82 | 91 |
| candidates | 90 | 99 |

**The right-hand column is not a result.** It is what the arithmetic would give if an independent review and an owner approved all 9 candidates, which has never happened: acceptance across the five closed batches has run between 79% and 100%. Nothing in batch 006 is `human_verified`, and no batch-006 candidate is counted as confirmed anywhere in this project's records.

## Against the 100-case target

The project needs **≥100** confirmed holdout-eligible cases and holds **82**. Batch 006 exports **9**. At the 79% acceptance rate of the weakest closed batch that would reach 89; at 100% it would reach 91.

**Neither crosses 100.** Even if every batch-006 candidate were approved, the project would be 9 short. This batch does not get GOLD-001 to its minimum, and no approval decision should be taken as though it might — the gap has to close through another batch, a wider corpus, or a revised target, not through a lower bar here.

## Not done

- No holdout is frozen and no validation split is frozen.
- No retrieval system has been run against any GOLD candidate.
- Batch 006 has had no independent review; that is the next step.
