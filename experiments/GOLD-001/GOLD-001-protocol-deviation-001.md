# GOLD-001 - protocol deviation 001

**Disposition: `ACCEPTED_PROTOCOL_DEVIATION`**, decided by `project_owner`, recorded 2026-08-31T03:32:45Z.

## Planned

`GOLD-001-batch-007-preregistration.json` required a prospective 10-case NO_BUILDER-only calibration pilot, run and reviewed, before evidence-grounded paraphrasing was scaled to a 35-40 candidate batch.

## Actual

The pilot was never run. Sixty standalone drafts (HA-01 ... HA-60) were authored first, outside the preregistered sequence, and are now admitted.

**These 60 cases are not the preregistered pilot and may not be described as it, retrospectively or otherwise. The pilot remains unrun.**

## Why it matters

A prospective pilot is a commitment made before the data is seen. Its value is that the thresholds cannot be chosen to fit the result. Reviewing 60 cases afterwards, however carefully, cannot recover that property, and no amount of downstream checking converts a retrospective review into a preregistered one. What the mitigations below establish is that these particular cases are sound; what they do not establish is that the method was calibrated before it was used.

## Mitigations actually performed

Only figures verifiable from the packet, its embedded records, or this session's own re-derivation are listed. Each carries what it does not establish.

| mitigation | figure | verified from | limit |
| --- | --- | --- | --- |
| structural, integrity and review-lineage checks on the derivative | 1,576 / 1,576 passed | the packet's own front matter (page 3) | the packet states these are not proof of semantic correctness or full-corpus authenticity |
| deliberately corrupted negative controls | 8 detected | the packet's own front matter (page 3) | shows the checks can fail; not a semantic guarantee |
| Codex semantic review | a codex_review block on every one of the 60 records | the embedded 150-case-review-records.json | Codex authored the derivative; its review is not independent of it |
| Grok Expert independent semantic review | 60 reviewed, 60 PASS, 0 REVISE, 0 REJECT | the embedded grok-review-results.json | These are captured accessibility transcripts from the observed UI, not a signed provider API attestation. |
| ChatGPT independent semantic review | 58 PASS, 1 pass-with-noncritical-anaphora-override (HA-15), 1 fix-required-then-approve (HA-47), 0 semantic rejections | the supplied review file, bound to the records by case id plus exact question and answer | an independent review is a recommendation; it approves nothing |
| re-derivation of every record from the frozen source in this session | 60 records, 77 spans re-sliced at their offsets, rehashed, and version_ids recomputed through the content-derived chain | scripts/admit_ha01_ha60.py, run against the reproduced OpenAI corpus | certifies these 9 document versions, not the 202-document snapshot |
| project-owner decision | 60 approved, 0 rejected | evals/review/human_decisions_HA01_HA60.json | read as an input; no script produced it |
| deterministic eligibility gate | 60/60 holdout_eligible | rag_v1.gold.eligibility.evaluate, unmodified | metadata and evidence integrity; it does not read semantics |
| no retrieval leakage | retrieval_was_not_run true, systems_executed empty | GOLD-001-eligibility-status.json | none - this one is an invariant, and it holds |

Grok's own record states `official_admissions: 0`, `human_approval: False`, `semantic_blocking_findings: 0`. No reviewer approved anything.

## A declined suggestion the owner has now superseded

The packet records: _Grok suggested rewriting HA-47 E2 or merging E1/E2 if needed. Do not rewrite exact source evidence or merge across paragraph boundaries; neither suggestion was applied._

The owner has now directed exactly the outward expansion that note declined: HA-47's evidence is one contiguous slice 4308:4916 that crosses a paragraph break. This is recorded rather than passed over silently. It is not a rewrite and not a synthetic merge - the evidence is an exact contiguous slice of the frozen source, re-sliced and rehashed here - and no eligibility condition reads paragraph structure. The earlier note was a stricter house rule; the owner has replaced it for this case with a documented decision.

## Consequences

- The 60 cases may be admitted, and are.
- The project must never claim the preregistered pilot sequence was followed.
- The batch-007 preregistered pilot remains unrun and still applies to any future scaling of evidence-grounded paraphrasing.
- Any paper or report describing this benchmark must carry this deviation.

## What this deviation does not cover

- corpus reproduction, which remains incomplete and blocks retrieval
- category coverage, which is uneven and leaves genuine multi-hop at n=1

