# GOLD-001 — eligibility status

As of 2026-08-20T20:43:02Z.

| batch | candidates | `human_verified` | `human_rejected` | `holdout_eligible` | eligibility read from |
| --- | --- | --- | --- | --- | --- |
| 001 | 18 | 16 | 2 | **16** | batch_001_v2 |
| 002 | 18 | 17 | 1 | **17** | v1 |
| **all** | **36** | **33** | **3** | **33** | |

## The two numbers are not the same question

`human_verified` counts approvals a person gave; it is historical and does not change. `holdout_eligible` counts cases a machine can still check — human approval, a deterministic check for every claim, critical strings present in the evidence, a valid evidence hash, and no unresolved scope defect, all holding now. A case can gain eligibility through added metadata without being re-approved, and lose it to corpus drift without the approval being wrong.

## Against the target

The project is aiming at roughly **30–40 validation** cases and **70–100 holdout** cases.

**33 eligible cases is not enough for both.** Splitting them would leave a holdout too small to measure with and a validation set too small to develop against, and every case spent on validation is a case the holdout will never see. No holdout is frozen, and none should be until the count supports the split.

## Untouched

SYSTEM-A and SYSTEM-B remain frozen and have not been executed against any GOLD-001 candidate. No candidate-selection step has seen a retrieval outcome, which is the property that makes a future holdout worth having.
