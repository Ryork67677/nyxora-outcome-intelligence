# GOLD-001 — eligibility status

As of 2026-08-23T06:18:13Z.

| batch | candidates | `human_verified` | `human_rejected` | `holdout_eligible` | genuine multi-hop | eligibility read from |
| --- | --- | --- | --- | --- | --- | --- |
| 001 | 18 | 16 | 2 | **16** | 0 | batch_001_v2 |
| 002 | 18 | 17 | 1 | **17** | 0 | v1 |
| 003 | 20 | 20 | 0 | **20** | 0 | v1 |
| 004 | 15 | 14 | 1 | **14** | 1 | v1 |
| **all** | **71** | **67** | **4** | **67** | **1** | |

## Genuine multi-hop

**1 of 67 eligible cases** is a genuine multi-hop reasoning case.

That is one observation. It proves the benchmark infrastructure can represent a genuine multi-hop case — anchor it, check its composition, and carry it through review — and it does not mean the category is adequately sampled. A single case cannot support a claim about how any system handles multi-hop reasoning.

Batch 004's composer tested **559** bridge pairs and **1** passed the composition check. That ratio is a finding about the corpus and the authoring method, not a defect that was tuned away: two facts sharing an identifier are almost never two halves of an argument.

## The two numbers are not the same question

`human_verified` counts approvals a person gave; it is historical and does not change. `holdout_eligible` counts cases a machine can still check — human approval, a deterministic check for every claim, critical strings present in the evidence, a valid evidence hash, and no unresolved scope defect, all holding now. A case can gain eligibility through added metadata without being re-approved, and lose it to corpus drift without the approval being wrong.

## Against the target

The project is aiming at roughly **30–40 validation** cases and **70–100 holdout** cases.

**67 eligible cases is not enough for both.** Splitting them would leave a holdout too small to measure with and a validation set too small to develop against, and every case spent on validation is a case the holdout will never see. No holdout is frozen, and none should be until the count supports the split.

## Untouched

SYSTEM-A and SYSTEM-B remain frozen and have not been executed against any GOLD-001 candidate. No candidate-selection step has seen a retrieval outcome, which is the property that makes a future holdout worth having.
