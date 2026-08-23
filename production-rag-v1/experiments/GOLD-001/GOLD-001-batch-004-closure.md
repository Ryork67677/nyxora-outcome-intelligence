# GOLD-001 — batch 004 closure

**Closed 2026-08-23T06:17:18Z by project_owner.** Every candidate reached an explicit human decision. Nothing is outstanding.

| | |
| --- | --- |
| candidates | 15 |
| `human_verified` | **14** |
| `human_rejected` | 1 |
| `needs_human_review` | 0 |
| outstanding decisions | 0 |
| acceptance rate | **93.3%** |

Acceptance rate is not a quality score. It is the share of *mined candidates* a person kept, and it says as much about how permissive the miner was as about how good the evidence is. With n=15 one candidate moves it 6.7 points.

## Rejected — kept, not deleted

| candidate | defects | reason |
| --- | --- | --- |
| `GOLD-B004-08` | — | Rejected: BENCHMARK_QUALITY / TAXONOMY_MISCLASSIFICATION. The facts are not disputed — ContentDeltaEvent carries type "content.delta" and ContentDoneEvent carries type "content.done" — but two discriminator constants are not meaningful disambiguation. Relabelling to exact_lookup would produce two trivial literal lookups of little benchmark value. Not salvaged to increase the candidate count. Preserved as an audit example. |

The record remains in the batch as a negative audit example. A rejection is evidence about the miner, and deleting it would discard the only record of what the miner got wrong.

## Repaired — anchors extended, originals preserved

| candidate | old span | new span | approved anchor |
| --- | --- | --- | --- |
| `GOLD-B004-04` | 48081–48225 | 47953–48225 | `8eb88b1c77cc…` |
| `GOLD-B004-06` | 16744–16843 | 16295–16843 | `b38e23b266e3…` |
| `GOLD-B004-09` | 6938–6997, 7362–7509 | 6627–6997, 7072–7509 | `53b4b866ce9f…` |
| `GOLD-B004-10` | 1979–2121 | 1827–2121 | `352fcab03e4b…` |
| `GOLD-B004-14` | — (scope span added) | 1576–1654 | `6ed28e39bdd7…` |
| `GOLD-B004-15` | 16756–16910 | 16313–16910 | `b0ef211a15b2…` |

Each repair grew the anchor outward to contain what its claims already depended on; the new span is a strict superset of the old, and both are retained in `anchor_revisions`. Each approval pins the post-repair hash, so the record shows which version the owner actually approved.

## Question-authoring revisions

9 of 15 candidates had their question, answer or claims re-authored during review. The miner's original wording is retained on every one of them as revision 1; nothing was overwritten.

**Claims actually checkable: 14 of 14 verified cases carry literal critical strings.** A case without literal critical strings passes the claim-in-evidence gate vacuously. This count, not the validator's green tick, is what says whether the claims were actually checked.

## Reasoning type and evidence shape

Reasoning types: {'error_behavior': 5, 'configuration_interaction': 3, 'exact_lookup': 3, 'lifecycle_compatibility_migration': 1, 'ambiguity_disambiguation': 2, 'genuine_multi_hop': 1}. Evidence shapes: {'single_span': 11, 'multi_span': 3, 'multi_document': 1}.

**Genuine multi-hop reasoning cases: 1**, against a generation target of 6–8.

Reasoning type and evidence shape are separate dimensions. A case needing two spans is multi_span; multi_hop is a reasoning type, and a case only earns it when the answer is derived from combining spans rather than being the spans' contents. This batch closed with 1. That is one observation, and it proves the benchmark infrastructure can represent a genuine multi-hop case; it does not mean the category is adequately sampled. The generation figure below is the finding to carry forward.

## What it cost to find one chain

The composer tested **559** bridge pairs. **1** passed the composition check; **558** were rejected.

| rejection reason | pairs |
| --- | --- |
| the spans were two unrelated lookups | 379 |
| no bridge relationship existed | 147 |
| span 1 alone answered the full question | 16 |
| span 2 alone answered the full question | 16 |
| the composed answer introduced unsupported inference | 0 |

This ratio is a result about the corpus and the authoring method, not a defect to be tuned away. In this corpus two facts that share an identifier are almost never two halves of an argument, and no candidate was regenerated to improve the number.

## Near-miss diagnostic

**5** bridge pairs cleared every check except the rule under test — states_dependency — span 2's conditional must test the bridge entity's own state. Reviewer verdicts: 5 CORRECT_REJECTION.

| bridge entity | verdict |
| --- | --- |
| `OpenAIChatCompletionsModel` | CORRECT_REJECTION |
| `allowed_callers` | CORRECT_REJECTION |
| `max_tokens` | CORRECT_REJECTION |
| `tool_result` | CORRECT_REJECTION |
| `view_range` | CORRECT_REJECTION |

Diagnostic only: 0 promoted into the batch, batch regenerated: false. Full reasoning in `experiments/GOLD-001/BATCH-004-near-miss-multihop-review.md`.

## Human overrides

A noncritical finding blocks until a person accepts it. These were accepted, and none of them was deleted: the detector still reports every one, and a *critical* finding cannot be overridden at all.

| candidate | finding | accepted by | disposition |
| --- | --- | --- | --- |
| `GOLD-B004-02` | NONCRITICAL_ANAPHORA | project_owner | finding retained |
| `GOLD-B004-05` | NONCRITICAL_DEPENDENCY | project_owner | finding retained |
| `GOLD-B004-15` | NONCRITICAL_ANAPHORA | project_owner | finding retained |

## What `precheck_holdout_ready` does and does not mean

This batch produced 15 of 15 candidates `precheck_holdout_ready`. The source-integrity review that followed repaired 10 of them and recommended 1 for rejection.

That is not a precheck failure. The precheck is deliberately structural: it verifies hashes, offsets, string containment, anaphora and anchor size. It means **structurally capable** — not semantic correctness, not human approval, and not holdout eligibility. The review is what showed why the separation has to be maintained rather than assumed.

## Errata

- **near-miss bridge-pair count** — was "3 pairs rejected only by the entity-state rule"; is **5 pairs**. The 3 came from a manual probe run mid-development, with the composer's per-run limit and used-fact set in force and before the entity-state rule existed. scripts/diagnose_b004_near_miss.py derives the set properly, and the PDF builder now reads the count from it rather than hardcoding one. Recorded in `experiments/GOLD-001/GOLD-001-batch-004-report-erratum.md`. Generation figures affected: no.

## Miner defect taxonomy

| class | name | seen | description |
| --- | --- | --- | --- |
| `D1` | anaphoric anchor | 0 | The span opens on, or silently depends on, a referent outside itself — 'If true', 'any of these models'. The claim cannot be checked against the anchor alone. |
| `D2` | wrong relation label | 0 | The miner matched a trigger word and labelled the candidate with a relation the sentence does not express. The evidence is usually fine; the label aims the reviewer at the wrong question. |
| `D3` | example-code false binding | 0 | An identifier matched inside a fenced code block or JSON literal and was framed as a documented rule. A sample configuration is not a rule. |

## Provenance

| | |
| --- | --- |
| reviewed-state sha256 | `1ce046829660332c073d41101d74415efd569ab6e2a5059c793a10d001bed712` |
| generation batch sha256 | `e7c6d58c3c21b9ece940ae9665cba96ada35c887558803bba1797aaa142b93f9` |
| corpus snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| schema version | 1.2 |
| git commit at generation | `2daaa9e62566` |
| closure sha256 | `57269018d21a2b1f72b607b419ce5f9c02789ff98e6699ca0c58ea65811c8908` |

The closure hash covers the candidate records. A closed batch is not supposed to change again, and the test suite re-checks this hash, so an edit after closure fails the tests rather than passing unnoticed.

## Validation

`scripts/validate_golden.py` — **14 cases, 0 failures**, `--require-human validation`.

**Caveat.** All 14 verified cases carry literal critical strings, so the claim-in-evidence check ran on every one of them. The validator's pass covers claim support, not only structure.

## Retrieval

No retrieval system was run against any candidate in this batch at any point. SYSTEM-A and SYSTEM-B remain frozen and were not executed. Candidate selection could not be influenced by what either system succeeds or fails on, which is what keeps a future holdout honest.

`retrieval_was_not_run: True`

## Not done, and deliberately so

- No split has been assigned; the projection's split is a placeholder.
- No holdout is frozen.
- Critical claim strings exist for 14 of 14 verified cases, so every one of them is claim-checked.
- OA-002 remains a recorded defect in development/v1 with an unapplied development/v2 correction proposal.
