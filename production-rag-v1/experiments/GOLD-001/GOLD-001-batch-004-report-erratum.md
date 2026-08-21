# GOLD-001 — batch 004 report erratum

**Issued during batch-004 human-review preparation. The generation artifacts are not modified.**

## 1. The near-miss count was wrong

The batch-004 results PDF (`docs/reports/GOLD-001-batch-004-generation-results.pdf`,
§8) stated:

> three bridge pairs that passed every other check were rejected only by the
> entity-state rule

The correct number is **five**.

### Where the wrong number came from

It was not computed. It came from a manual probe run during generation, which
inspected the pairs surviving at an intermediate point in the composer's development
and counted four, one of which passed. That probe ran with the composer's per-run
limit and its `used` set in force, so a fact already consumed by an accepted pair was
unavailable to later ones, and the search stopped early. It also ran before the
entity-state rule existed, against a different filter stack.

`scripts/diagnose_b004_near_miss.py` now derives the set properly: it applies every
check in the composer's own order, skips only the rule under test, and does not
consume facts. That yields five pairs — the three the probe found
(`allowed_callers`, `max_tokens`, `tool_result`) plus `OpenAIChatCompletionsModel`
and `view_range`, which the probe's limits had hidden.

### What is *not* affected

The generation report's own numbers were computed from the run and are unchanged:

| figure | value | status |
| --- | --- | --- |
| bridge pairs tested | 559 | unchanged |
| passed the composition check | 1 | unchanged |
| rejected | 558 | unchanged |
| rejection reasons by bucket | 379 / 147 / 16 / 16 / 0 | unchanged |
| `unclassified` guard | 0 | unchanged |

`GOLD-001-batch-004-generation-report.{md,json}` never carried a near-miss count, so
neither file is corrected. The error existed only in prose I wrote for the PDF.

### The fix

`scripts/build_batch_004_pdf.py` no longer hardcodes the number. It reads
`BATCH-004-near-miss-multihop-review.json` and reports the count and the verdicts
from it, so the figure cannot drift from the diagnostic again. The PDF is a rendering
of the artifacts rather than a historical artifact itself, and it is rebuilt; this
erratum is the record of what it used to say.

## 2. What the corrected diagnostic found

All five near misses are **CORRECT_REJECTION**. The rule under test — span 2's
conditional must test the bridge entity's own state — is not too strict on this
evidence. Full reasoning per pair is in
`BATCH-004-near-miss-multihop-review.md`.

One finding is worth lifting out, because it is a gap in a check rather than a
judgement about a pair. The `max_tokens` pair failed because span 1 uses
`max_tokens` as a request parameter and span 2 uses `"max_tokens"` as a
`stop_reason` value. The bridge requirement — the entity must appear in both spans —
is a string test and cannot see equivocation. Nothing in the current composer can.
That belongs in batch 005's design, preregistered before it sees a candidate.

## 3. Scope

No candidate changed status because of this erratum. No batch-004 candidate was
added, removed or promoted. No retrieval was run; SYSTEM-A and SYSTEM-B remain frozen
and unexecuted; the holdout is not frozen. Confirmed holdout-eligible remains 53 from
batches 001–003.
