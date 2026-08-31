# GOLD-001 — eligibility status

As of 2026-08-31T03:37:38Z.

| batch | candidates | `human_verified` | `human_rejected` | `holdout_eligible` | genuine multi-hop | eligibility read from |
| --- | --- | --- | --- | --- | --- | --- |
| 001 | 18 | 16 | 2 | **16** | 0 | batch_001_v2 |
| 002 | 18 | 17 | 1 | **17** | 0 | v1 |
| 003 | 20 | 20 | 0 | **20** | 0 | v1 |
| 004 | 15 | 14 | 1 | **14** | 1 | v1 |
| 005 | 19 | 15 | 4 | **15** | 0 | v1 |
| 006 | 9 | 8 | 1 | **8** | 0 | v1 |
| HA-01–HA-60 | 60 | 60 | 0 | **60** | 0 | v1 |
| **all** | **159** | **150** | **9** | **150** | **1** | |

## Genuine multi-hop

**1 of 150 eligible cases** is a genuine multi-hop reasoning case.

That is one observation. It proves the benchmark infrastructure can represent a genuine multi-hop case — anchor it, check its composition, and carry it through review — and it does not mean the category is adequately sampled. A single case cannot support a claim about how any system handles multi-hop reasoning.

Batch 004's composer tested **559** bridge pairs and **1** passed the composition check. That ratio is a finding about the corpus and the authoring method, not a defect that was tuned away: two facts sharing an identifier are almost never two halves of an argument.

Batch 005 searched the same corpus dependency-first instead — only sentences that state a dependency may open a chain — and reached the composition gates with **3** pairs. **1** was a valid chain, and it is the chain batch 004 already closed, so **0** new unique chains were exported.

Two searches, two methods, one composable structure. That is a measured property of this frozen corpus, not a failure of either search, and it is the reason the multi-hop count above is 1 rather than a number a later batch can be expected to raise easily.

## The two numbers are not the same question

`human_verified` counts approvals a person gave; it is historical and does not change. `holdout_eligible` counts cases a machine can still check: every one of `human_verified`, `every_claim_has_a_deterministic_check`, `critical_strings_present_in_evidence`, `evidence_hash_valid`, `no_unresolved_scope_defect`, `required_evidence_declared` holding right now. The list is read from `rag_v1.gold.eligibility`, so a condition added to the gate appears here instead of being described from memory. A case can gain eligibility through added metadata without being re-approved, and lose it to corpus drift without the approval being wrong.

## Against the target

The project is aiming at roughly **30–40 validation** cases and **70–100 holdout** cases.

**150 eligible cases can support the 30–40 / 70–100 split by size, so size is no longer the reason. What is missing is a split policy: the set is provider- and category-skewed and holds 1 genuine multi-hop case, so an unweighted split would decide by accident which categories the holdout can measure. Freezing also stays blocked while corpus reproduction is incomplete.**

No holdout is frozen and `holdout_frozen` stays false.

## Untouched

SYSTEM-A and SYSTEM-B remain frozen and have not been executed against any GOLD-001 candidate. No candidate-selection step has seen a retrieval outcome, which is the property that makes a future holdout worth having.
