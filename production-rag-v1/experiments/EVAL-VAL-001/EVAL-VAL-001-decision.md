# EVAL-VAL-001 — project decision

**`SYSTEM_B_PROMOTION = REJECTED`**

**`SYSTEM_A_CONTROL = RETAINED`**

Decided 2026-08-31T23:01:41Z on the EVAL-VAL-001 result (`REPLICATION_REJECTS_B`).

## Why

DOC-C did not replicate on independent validation. Its Stage-1 routing discarded a required document in 12 of 40 cases, and every one of the 11 regressions has the same signature: SYSTEM-A found the span at rank 1-9 and SYSTEM-B did not retrieve it at all.

| | SYSTEM-A | SYSTEM-B |
| --- | --- | --- |
| strict full-case recall@10 | 30/40 | 21/40 |
| paired movement | — | 2 rescues, 11 regressions, net -9 |
| bootstrap macro delta | — | -0.225 95% CI [-0.375, -0.075] |
| McNemar exact p | — | 0.0225 |

## SYSTEM-B is preserved, not deleted

A rejected intervention with a clean causal explanation is a result. Deleting it would leave the project unable to say why routing was tried and what it cost.

Its frozen configuration hash `304c350940b83733…` and every artifact of the run remain in the repository.

## Holdout

Untouched: 90 cases, `holdout_runs = 0`, `holdout_frozen = true`.
