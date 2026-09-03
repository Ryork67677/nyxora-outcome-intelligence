# GOLD-001 — batch 001 v2 closure

**This does not replace the batch 001 v1 closure.** v1 stays closed at 16 `human_verified` and 2 `human_rejected`, and still hashes to `d6f92e8d1a7e77ea…`, which the builder re-verifies before writing anything here.

| | |
| --- | --- |
| cases in v2 | **16** |
| metadata upgraded | 11 |
| scope repaired | 2 |
| carried forward unchanged | 3 |
| `human_verified` | 16 |
| `holdout_eligible` | **16** |
| pending scope repair | 0 |
| validator | **16 cases, 0 failures** |

## Scope repairs applied

| case | v1 span | v2 span | Δ | v1 hash | v2 hash |
| --- | --- | --- | --- | --- | --- |
| `GOLD-B001-13` | 519–725 | 248–725 | +271 | `39c03eda7465…` | `f9057cf3281d…` |
| `GOLD-B001-17` | 29836–30171 | 29787–30171 | +49 | `83e5abb14c44…` | `8089c9eb8563…` |

Both were approved by the project owner as option A, evidence-boundary expansion. Each v2 record carries its v1 span, v1 text, v1 hash, v1 claims and v1 approval beside the new ones, so the promotion reads in one place. The builder refuses to write if the approved span does not hash to the value the approval names — an approval of a different span is not an approval of this one.

## Eligibility

All five conditions in `rag_v1.gold.eligibility` hold for every case: human approval, a deterministic check for every claim, critical strings present in the evidence, a valid evidence hash, and no unresolved scope defect.

Every case here was human_verified in v1 and still is. Eligibility is a separate state; gaining it required no new approval and losing it would not revoke one.

## Not done

- No holdout is frozen. The project has too few cases for a validation split and a genuinely unseen holdout both.
- No retrieval was run, and SYSTEM-A and SYSTEM-B remain frozen and unexecuted.
- Batch 001 v1 is unchanged and stays the historical record.
