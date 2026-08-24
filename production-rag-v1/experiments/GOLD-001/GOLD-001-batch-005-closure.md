# GOLD-001 — batch 005 closure

**Closed 2026-08-24T05:21:19Z by project_owner.** Every candidate reached an explicit human decision. Nothing is outstanding.

| | |
| --- | --- |
| candidates | 19 |
| `human_verified` | **15** |
| `human_rejected` | 4 |
| `needs_human_review` | 0 |
| outstanding decisions | 0 |
| `holdout_eligible` | **15** |
| acceptance rate | **79.0%** |

Acceptance rate is not a quality score. It is the share of *mined candidates* a person kept, and it says as much about how permissive the miner was as about how good the evidence is. With n=19 one candidate moves it 5.3 points.

`holdout_eligible` is the deterministic gate re-run at closure over the 15 verified records — human approval and machine checkability are separate states, and this one is derived, never asserted. Every verified case passes it.

## Rejected — kept, not deleted

| candidate | defects | reason |
| --- | --- | --- |
| `GOLD-B005-01` | NOT_AMBIGUITY, NOT_A_FIELD, SCOPE_IN_HEADING | Rejected: BENCHMARK_QUALITY / TAXONOMY_MISCLASSIFICATION / SCOPE_DEFECT. `invalid_tool_input` is the same semantic concept in both sources — the tool input is invalid — and the examples differ by tool (a malformed or non-HTTP(S) URL; a malformed or over-length regex) without creating meaningful disambiguation. The spans are bare definition bullets that rely on document and section scope outside themselves. Not salvaged as two exact lookups to preserve count. Preserved as an audit example. |
| `GOLD-B005-06` | NOT_A_LIFECYCLE_STATEMENT, UNANSWERABLE_AS_ASKED | Rejected: UNANSWERABLE_AS_ASKED / CATEGORY_MISCLASSIFICATION. The evidence is a schema description of what model IDs may appear in `fallbacks[i].model` and what an empty list means. It does not answer 'Where is fallbacks supported?', and it is not a lifecycle statement merely because the phrase 'not supported' appears in a schema description. The question is not to be rewritten into a different fact under this candidate ID. Preserved as an audit example. |
| `GOLD-B005-10` | RELATION_DIRECTION, SCOPE_IN_HEADING | Rejected: RELATION_DIRECTION / UNRECOVERABLE_SCOPE. The evidence says the experimental model rejects caller-supplied `betas` overrides; it does not say `betas` overrides anything, so the generated question reverses the documented relation. Rewriting around the true subject would require identifying the experimental model, whose identity is outside the exact evidence and cannot be recovered by a minimal valid expansion. Not salvaged. |
| `GOLD-B005-13` | ANAPHORA, DUPLICATE_RELATION | Rejected: DUPLICATE_RELATION / BENCHMARK_REDUNDANCY. The fact is supported — `S3FilesMountPattern` requires broad acknowledgement because `mount.s3files` uses ambient IAM authority — but it is the adjacent sibling of GOLD-B005-12 and tests the same relation: mount pattern requires broad acknowledgement because ambient cloud authority is discovered. GOLD-B005-12 is kept; benchmark capacity is not spent on an adjacent duplicate. Preserved for audit history. |

All rejected records remain in the batch as negative audit examples. A rejection is evidence about the miner, and deleting them would discard the only record of what the miner got wrong.

## Repaired — anchors extended, originals preserved

| candidate | old span | new span | approved anchor |
| --- | --- | --- | --- |
| `GOLD-B005-09` | 1609–1855 | 1523–1855 | `d4a15c400fe1…` |

Each repair grew the anchor outward to contain what its claims already depended on; the new span is a strict superset of the old, and both are retained in `anchor_revisions`. Each approval pins the post-repair hash, so the record shows which version the owner actually approved.

## Question-authoring revisions

7 of 19 candidates had their question, answer or claims re-authored during review. The miner's original wording is retained on every one of them as revision 1; nothing was overwritten.

**Claims actually checkable: 15 of 15 verified cases carry literal critical strings.** A case without literal critical strings passes the claim-in-evidence gate vacuously. This count, not the validator's green tick, is what says whether the claims were actually checked.

## Reasoning type and evidence shape

| dimension | all 19 records | verified only |
| --- | --- | --- |
| reasoning type | {'ambiguity_disambiguation': 1, 'configuration_interaction': 8, 'error_behavior': 4, 'exact_lookup': 2, 'lifecycle_compatibility_migration': 4} | {'configuration_interaction': 6, 'error_behavior': 4, 'exact_lookup': 2, 'lifecycle_compatibility_migration': 3} |
| evidence shape | {'multi_document': 1, 'single_span': 18} | {'single_span': 15} |
| provider | {'anthropic': 8, 'openai': 11} | {'anthropic': 6, 'openai': 9} |

Both columns carry the labels the records hold at closure, so a category the review corrected reads as corrected here and not as the miner first guessed — the generation report is the record of what was mined. The left column is every candidate; the right is the mix that survived, and only the right one is coverage.

**Genuine multi-hop reasoning cases: 0**, against a generation target of 0–6.

Reasoning type and evidence shape are separate dimensions. A case needing two spans is multi_span; multi_hop is a reasoning type, and a case only earns it when the answer is derived from combining spans rather than being the spans' contents. The multi-span cases in this batch are useful multi-evidence retrieval tests and are not relabelled to close the gap; a later batch has to target genuine multi-hop reasoning directly.

## Multi-hop search — dependency-first

Dependency-first: a chain may only open on a sentence that states a dependency and puts the entity in a state. **122** entities had a sentence that could open a chain; **3** dependency pairs reached the composition gates, within a budget of 1000.

| | |
| --- | --- |
| dependency pairs considered | 3 |
| failed span independence | 1 |
| failed semantic equivalence | 1 |
| valid chains | **1** |
| new unique chains exported | **0** |

| bridge entity | gate | why it was rejected |
| --- | --- | --- |
| `input_filter` | span independence | span 1 alone already answers the whole question — not multi-hop |
| `max_tokens` | semantic equivalence | `max_tokens` is a request parameter in span 1 and an enum value in span 2: the same string naming two different things, which is a coincidence rather than a chain |

The one valid chain is the chain batch 004 already closed, so this batch exported none. That is the finding, not a failure: searching a different way found the same single composable structure, which is evidence that the frozen corpus contains very little naturally composable multi-hop material — not that the search was run badly.

## Target 30, exported 19

The generation target was **30**; the batch exported **19**.

**46** candidates reached the semantic self-review and **27** were dropped there, leaving 19. The drops were led by generic identifiers, claims wider than their span, and category labels the evidence did not support — not by anything the structural precheck could see.

The shortfall is the review working, not a miner failing to reach a number. An earlier draft of this batch did reach 30 candidates; those candidates carried pervasive question-subject/fact-subject mismatches, the miners were corrected rather than the candidates patched, and the corrected run returned 19. Padding back to 30 would have meant keeping cases a reader could not check, so the count was the thing allowed to move.

## Human overrides

A noncritical finding blocks until a person accepts it. These were accepted, and none of them was deleted: the detector still reports every one, and a *critical* finding cannot be overridden at all.

| candidate | finding | accepted by | disposition |
| --- | --- | --- | --- |
| `GOLD-B005-03` | NONCRITICAL_SCOPE | project_owner | finding retained |
| `GOLD-B005-04` | NONCRITICAL_SCOPE | project_owner | finding retained |

## What `precheck_holdout_ready` does and does not mean

This batch produced 19 of 19 candidates `precheck_holdout_ready`. The source-integrity review that followed repaired 7 of them and recommended 4 for rejection.

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
| reviewed-state sha256 | `c9077e4f1519a99a4b0723e3db3ed98b6f2b2a6069b8f4d84c9638ae3e99a279` |
| generation batch sha256 | `37bf3509a9205637588730760dc14bf2dcaed19e03e4ed6bcd4ba7580e501af3` |
| corpus snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| schema version | 1.3 |
| git commit at generation | `f4c7d4e11a97` |
| closure sha256 | `ffbf9dda40ec1554d15ade41480d0927464fb2c35a2f4a08aaa9f6fb065df4c0` |

The closure hash covers the candidate records. A closed batch is not supposed to change again, and the test suite re-checks this hash, so an edit after closure fails the tests rather than passing unnoticed.

## Validation

`scripts/validate_golden.py` — **15 cases, 0 failures**, `--require-human validation`.

**Caveat.** All 15 verified cases carry literal critical strings, so the claim-in-evidence check ran on every one of them. The validator's pass covers claim support, not only structure.

## Retrieval

No retrieval system was run against any candidate in this batch at any point. SYSTEM-A and SYSTEM-B remain frozen and were not executed. Candidate selection could not be influenced by what either system succeeds or fails on, which is what keeps a future holdout honest.

`retrieval_was_not_run: True`

## Not done, and deliberately so

- No split has been assigned; the projection's split is a placeholder.
- No holdout is frozen.
- Critical claim strings exist for 15 of 15 verified cases, so every one of them is claim-checked.
- OA-002 remains a recorded defect in development/v1 with an unapplied development/v2 correction proposal.
