# GOLD-001 — batch 006 closure

**Closed 2026-08-25T06:50:29Z by project_owner.** Every candidate reached an explicit human decision. Nothing is outstanding.

| | |
| --- | --- |
| candidates | 9 |
| `human_verified` | **8** |
| `human_rejected` | 1 |
| `needs_human_review` | 0 |
| outstanding decisions | 0 |
| `holdout_eligible` | **8** |
| acceptance rate | **88.9%** |

Acceptance rate is not a quality score. It is the share of *mined candidates* a person kept, and it says as much about how permissive the miner was as about how good the evidence is. With n=9 one candidate moves it 11.1 points.

`holdout_eligible` is the deterministic gate re-run at closure over the 8 verified records — human approval and machine checkability are separate states, and this one is derived, never asserted. Every verified case passes it.

## Rejected — kept, not deleted

| candidate | defects | reason |
| --- | --- | --- |
| `GOLD-B006-06` | DUPLICATE_FACT | REJECT — DUPLICATE_FACT / BENCHMARK_REDUNDANCY. The fact is supported, but GOLD-B005-11 already carries substantially the same operational relation from the OpenAI Python library; this obtains it from the TypeScript/JavaScript library. Useful source corroboration, not enough independent benchmark information. Preserved as an audit example and NOT replaced. |

The record remains in the batch as a negative audit example. A rejection is evidence about the miner, and deleting it would discard the only record of what the miner got wrong.

## Repaired — anchors extended, originals preserved

| candidate | old span | new span | approved anchor |
| --- | --- | --- | --- |


Each repair grew the anchor outward to contain what its claims already depended on; the new span is a strict superset of the old, and both are retained in `anchor_revisions`. Each approval pins the post-repair hash, so the record shows which version the owner actually approved.

## Question-authoring revisions

6 of 9 candidates had their question, answer or claims re-authored during review. The miner's original wording is retained on every one of them as revision 1; nothing was overwritten.

**Claims actually checkable: 8 of 8 verified cases carry literal critical strings.** A case without literal critical strings passes the claim-in-evidence gate vacuously. This count, not the validator's green tick, is what says whether the claims were actually checked.

## Reasoning type and evidence shape

| dimension | all 9 records | verified only |
| --- | --- | --- |
| reasoning type | {'exact_lookup': 4, 'error_behavior': 1, 'lifecycle_compatibility_migration': 2, 'configuration_interaction': 2} | {'exact_lookup': 4, 'error_behavior': 1, 'lifecycle_compatibility_migration': 2, 'configuration_interaction': 1} |
| evidence shape | {'single_span': 9} | {'single_span': 8} |
| provider | {'anthropic': 5, 'openai': 4} | {'anthropic': 5, 'openai': 3} |

Both columns carry the labels the records hold at closure, so a category the review corrected reads as corrected here and not as the miner first guessed — the generation report is the record of what was mined. The left column is every candidate; the right is the mix that survived, and only the right one is coverage.

**Genuine multi-hop reasoning cases: 0**, against a generation target of 0–1.

Reasoning type and evidence shape are separate dimensions. A case needing two spans is multi_span; multi_hop is a reasoning type, and a case only earns it when the answer is derived from combining spans rather than being the spans' contents. The multi-span cases in this batch are useful multi-evidence retrieval tests and are not relabelled to close the gap; a later batch has to target genuine multi-hop reasoning directly.

## Target 28, exported 9

The generation target was **28**; the batch exported **9**.

**50** candidates reached the semantic self-review and **40** were dropped there, leaving 10. The drops were led by generic identifiers, claims wider than their span, and category labels the evidence did not support — not by anything the structural precheck could see.

| | |
| --- | --- |
| facts mined | 1361 |
| distinct evidence spans the miners reach | 773 |
| **of those, unspent by any closed batch** | **699** |

**The corpus is not exhausted — the authoring is.** 699 distinct evidence spans in the frozen snapshot have never been used by a closed batch. What blocked them was that no deterministic question template could express them without paraphrasing: the prose left in this corpus is long and multi-clause, while the builders need a single-clause statement they can template exactly. That is the finding batch 007's preregistration is written from, and it points at a change of authoring method rather than at a smaller corpus or a lower bar.

The shortfall is the review working, not a miner failing to reach a number. An earlier draft of this batch did reach 30 candidates; those candidates carried pervasive question-subject/fact-subject mismatches, the miners were corrected rather than the candidates patched, and the corrected run returned 9. Padding back to 28 would have meant keeping cases a reader could not check, so the count was the thing allowed to move.

## Multi-hop — no search was run

**This batch deliberately ran no multi-hop search.** §7: batch 004 tested 559 bridge pairs and found 1 chain; batch 005 searched dependency-first and found the same one. The corpus has been measured twice. No search was run here, and no multi-span case was relabelled to raise the count.

Genuine multi-hop cases exported by this batch: **0**. No multi-span case was relabelled as multi-hop to raise the count, and the project's multi-hop total is unchanged by this batch.

## Heading parser audit

**44 of 5857 parsed headings (0.75%)** read as ordinary prose rather than as a label, across 15 of 202 documents. 82 were suspicious on at least one rule.

44 of 5857 parsed headings (0.75%), in 15 of 202 documents. That is isolated. It does not justify a parser experiment on its own, and the batch-006 rule — never trust section_path for scope — is the cheaper fix.

**Nothing was rewritten.** No heading was changed, no document was reparsed into storage, and no existing evidence anchor moved — a closed case approved against a bad `section_path` was approved against its *evidence*, and the path is metadata beside it. What changed is a rule: `section_path` is not trusted for claim scope, and a candidate's exact evidence must carry the scope its claim needs.

## Target 28, exported 9

The generation target was **28**; the batch exported **9**.

**50** candidates reached the semantic self-review and **40** were dropped there, leaving 10. The drops were led by generic identifiers, claims wider than their span, and category labels the evidence did not support — not by anything the structural precheck could see.

| | |
| --- | --- |
| facts mined | 1361 |
| distinct evidence spans the miners reach | 773 |
| **of those, unspent by any closed batch** | **699** |

**The corpus is not exhausted — the authoring is.** 699 distinct evidence spans in the frozen snapshot have never been used by a closed batch. What blocked them was that no deterministic question template could express them without paraphrasing: the prose left in this corpus is long and multi-clause, while the builders need a single-clause statement they can template exactly. That is the finding batch 007's preregistration is written from, and it points at a change of authoring method rather than at a smaller corpus or a lower bar.

The shortfall is the review working, not a miner failing to reach a number. An earlier draft of this batch did reach 30 candidates; those candidates carried pervasive question-subject/fact-subject mismatches, the miners were corrected rather than the candidates patched, and the corrected run returned 9. Padding back to 28 would have meant keeping cases a reader could not check, so the count was the thing allowed to move.

## What `precheck_holdout_ready` does and does not mean

This batch produced 9 of 9 candidates `precheck_holdout_ready`. The source-integrity review that followed repaired 6 of them and recommended 1 for rejection.

That is not a precheck failure. The precheck is deliberately structural: it verifies hashes, offsets, string containment, anaphora and anchor size. It means **structurally capable** — not semantic correctness, not human approval, and not holdout eligibility. The review is what showed why the separation has to be maintained rather than assumed.

## Miner defect taxonomy

| class | name | seen | description |
| --- | --- | --- | --- |
| `D1` | anaphoric anchor | 0 | The span opens on, or silently depends on, a referent outside itself — 'If true', 'any of these models'. The claim cannot be checked against the anchor alone. |
| `D2` | wrong relation label | 0 | The miner matched a trigger word and labelled the candidate with a relation the sentence does not express. The evidence is usually fine; the label aims the reviewer at the wrong question. |
| `D3` | example-code false binding | 0 | An identifier matched inside a fenced code block or JSON literal and was framed as a documented rule. A sample configuration is not a rule. |

## Provenance

| | |
| --- | --- |
| reviewed-state sha256 | `0c47fc891053f8c475ad89aa2dd085b2905ffbf0efa9eb1b641135ae4fd08f0e` |
| generation batch sha256 | `7a061b0beb37770338471ab0cd3517ea7d9c8e4e52c5aaf54e6094df81f145dc` |
| corpus snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| schema version | 1.3 |
| git commit at generation | `6f0588d62aab` |
| closure sha256 | `7ff5596c755a01fc57cf59b04cafdb77bd86a9f97f49cfdb58ff1782e07f68a2` |

The closure hash covers the candidate records. A closed batch is not supposed to change again, and the test suite re-checks this hash, so an edit after closure fails the tests rather than passing unnoticed.

## Validation

`scripts/validate_golden.py` — **8 cases, 0 failures**, `--require-human validation`.

**Caveat.** All 8 verified cases carry literal critical strings, so the claim-in-evidence check ran on every one of them. The validator's pass covers claim support, not only structure.

## Retrieval

No retrieval system was run against any candidate in this batch at any point. SYSTEM-A and SYSTEM-B remain frozen and were not executed. Candidate selection could not be influenced by what either system succeeds or fails on, which is what keeps a future holdout honest.

`retrieval_was_not_run: True`

## Not done, and deliberately so

- No split has been assigned; the projection's split is a placeholder.
- No holdout is frozen.
- Critical claim strings exist for 8 of 8 verified cases, so every one of them is claim-checked.
- OA-002 remains a recorded defect in development/v1 with an unapplied development/v2 correction proposal.
