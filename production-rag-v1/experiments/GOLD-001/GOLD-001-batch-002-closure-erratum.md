# GOLD-001 — batch 002 closure erratum

**The closure report contained two statements that could not both be true. One was
wrong. The candidate records were not affected, and the closure hash is unchanged.**

## The contradiction

`GOLD-001-batch-002-closure.md` said, in its Question-authoring section:

> Claims actually checkable: **17 of 17** verified cases carry literal critical strings.

and then, in its Validation section:

> **Caveat.** The claim-in-evidence check only fires on claims marked critical. Only the
> **three repaired cases** carry literal critical strings, so for the other 13 this pass
> says nothing about claim support.

## Which is authoritative

The candidate records, not the prose. Inspecting the closed batch directly:

| | |
| --- | --- |
| `human_verified` cases | 17 |
| carrying critical strings | **17** |
| every critical string present in its raw evidence | yes, all 19 claims across 17 cases |
| independent re-audit | `GOLD-001-batch-002-claim-audit.md` |

**The 17-of-17 count is correct. The caveat was wrong.**

## Cause

The caveat was a fixed string in `scripts/close_batch.py`. It was written to describe
batch 001, where 3 of 16 cases carried critical strings, and the closure builder emitted
it verbatim for every batch afterwards. It never read the records it was describing.

This is worth naming precisely: the report did not miscount. It carried a sentence that
had stopped being about the batch it appeared in — and it sat directly beneath a computed
number that contradicted it.

## What was affected

| | |
| --- | --- |
| candidate records | **not affected** — no record was read or written by the caveat |
| closure hash | **unchanged** — `69364f672e233fb32685a7a0fe283cfa…` |
| validator result | unaffected — 17 cases, 0 failures |
| holdout eligibility | unaffected — computed from records, never from the report |

## Fix

`claim_check_caveat(verified, with_critical)` now derives the sentence from the counts,
with four cases: all checkable, none checkable, some checkable, and no verified cases at
all. A regression test asserts that a closure's caveat can never contradict its own
`claim_checkable` count — the specific failure that produced this erratum.

## What was not done

The historical `GOLD-001-batch-002-closure.md` is **not** silently rewritten. It is
regenerated alongside this erratum, and this erratum records what the original said, so
the correction is visible rather than disappeared.
