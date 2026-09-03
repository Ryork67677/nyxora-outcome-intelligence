# GOLD-001 — batch 006 preregistration inputs

**Recorded 2026-08-24T05:02:43Z. inputs only — batch 006 is not generated, designed or preregistered.**

Four things batch 005 established about the generator. They are recorded here rather than fixed in place: batch 005's generation artifact is a historical record, and a miner corrected retroactively would leave no evidence of what it got wrong. Each one is a check a future batch-006 preregistration has to carry, with the case that would verify it.

### A. the bare-definition-bullet rule only inspects single-span records

**Seen in** `GOLD-B005-01`. The generation self-review drops a candidate whose single span is a bare '- `field`: description' bullet, because its scope lives in the heading. B005-01 is two such bullets in a multi-span record, and the rule's `len(spans) == 1` guard let it through. Recorded rather than patched: batch 005's generation artifact is not being regenerated, and a fix belongs in batch 006's preregistration.

**Check batch 006 must carry.** Extend the bare-definition-bullet scope rule to every span of a multi-span record, not only records with exactly one span.

**Verified by.** A regression case built from GOLD-B005-01's two bullets: the rule must drop it.

Source: `evals/review/gold_review_batch_005_final.json:generator_defects_found`.

### B. markdown reference links survive into questions built from conditional sentences

**Seen in** `GOLD-B005-15`. The link stripper runs on the composed question, but a reference-style link whose label is itself backticked was not matched. Repaired here by hand; the pattern should be fixed before batch 006.

**Check batch 006 must carry.** Strip markdown reference links whose label is itself backticked, before a question is composed.

**Verified by.** A regression case using GOLD-B005-15's original question text: no bracket or link label may survive into the question.

Source: `evals/review/gold_review_batch_005_final.json:generator_defects_found`.

### C. prose mistaken for a section heading by the parser

**Seen in** `GOLD-B005-11`. section_path reads 'configured through AWS_REGION, AWS_DEFAULT_REGION, or your AWS profile.' No claim depends on it, and closed batches must not be touched, so this is recorded as a parser observation for a future audit.

**Check batch 006 must carry.** Audit the heading parser against the corpus snapshot and record how often ordinary prose is captured as a `section_path`. Do NOT fix historical parser output in place; closed batches keep what they have.

**Verified by.** A count from the snapshot, reported before batch 006 generation, plus a rule that a `section_path` ending in a sentence-final period is not used as scope.

Source: `evals/review/gold_review_batch_005_final.json:generator_defects_found`.

### D. subject–relation direction must remain explicitly checked

**Seen in** `GOLD-B005-10`. Rejected: RELATION_DIRECTION / UNRECOVERABLE_SCOPE. The evidence says the experimental model rejects caller-supplied `betas` overrides; it does not say `betas` overrides anything, so the generated question reverses the documented relation. Rewriting around the true subject would require identifying the experimental model, whose identity is outside the exact evidence and cannot be recovered by a minimal valid expansion. Not salvaged.

**Check batch 006 must carry.** Every generated question must be re-read against its span for relation direction: the question's subject must be the source's subject, not its object.

**Verified by.** The GOLD-B005-10 rejection is kept as the regression case — the source says the experimental model rejects caller-supplied `betas` overrides, and a question asking what `betas` overrides must not survive generation.

Source: `experiments/GOLD-001/GOLD-001-batch-005-closure.json:rejected`.

## Provenance

| | |
| --- | --- |
| source batch | 005 |
| closure sha256 | `ffbf9dda40ec1554d15ade41480d0927464fb2c35a2f4a08aaa9f6fb065df4c0` |
| reviewed-state sha256 | `c9077e4f1519a99a4b0723e3db3ed98b6f2b2a6069b8f4d84c9638ae3e99a279` |
| generation batch sha256 | `37bf3509a9205637588730760dc14bf2dcaed19e03e4ed6bcd4ba7580e501af3` |

## Not done

- No batch-006 generation was run.
- No miner was changed. These are inputs to a future preregistration, and a fix applied now would be a change nobody preregistered.
- Batch 005's generation artifact is unmodified; the defects are recorded against it, not patched into it.
