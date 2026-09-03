# GOLD-001 — batch 002 closure

**Closed 2026-08-20T18:27:35Z by project_owner.** Every candidate reached an explicit human decision. Nothing is outstanding.

| | |
| --- | --- |
| candidates | 18 |
| `human_verified` | **17** |
| `human_rejected` | 1 |
| `needs_human_review` | 0 |
| outstanding decisions | 0 |
| acceptance rate | **94.4%** |

Acceptance rate is not a quality score. It is the share of *mined candidates* a person kept, and it says as much about how permissive the miner was as about how good the evidence is. With n=18 one candidate moves it 5.6 points.

## Rejected — kept, not deleted

| candidate | defects | reason |
| --- | --- | --- |
| `GOLD-B002-12` | MINER_EVIDENCE_DEFECT | REJECT — OVERSIZED_EVIDENCE_ANCHOR / EVIDENCE_PRECISION_COST. The documentation is correct and the fact is real. Making the anchor self-contained required expanding it from ~70 to ~1,430 characters, taking in the complete per-model cache-length list. That evidence unit is disproportionate to the fact under test and would make retrieval artificially easier. Preserved for audit history; no further automatic salvage attempted in batch 002. A future candidate may test this fact from a naturally smaller self-contained span. |

Both records remain in the batch as negative audit examples. A rejection is evidence about the miner, and deleting it would discard the only record of what the miner got wrong.

## Repaired — anchors extended, originals preserved

| candidate | old span | new span | approved anchor |
| --- | --- | --- | --- |
| `GOLD-B002-12` | 31104–31174 | 29744–31174 | `6cc24e6e6b65…` |
| `GOLD-B002-18` | 25565–25931 | 25347–25931 | `0d3851e614b9…` |

Each repair grew the anchor outward to contain what its claims already depended on; the new span is a strict superset of the old, and both are retained in `anchor_revisions`. Each approval pins the post-repair hash, so the record shows which version the owner actually approved.

## Question-authoring revisions

18 of 18 candidates had their question, answer or claims re-authored during review. The miner's original wording is retained on every one of them as revision 1; nothing was overwritten.

**Claims actually checkable: 17 of 17 verified cases carry literal critical strings.** A case without literal critical strings passes the claim-in-evidence gate vacuously. This count, not the validator's green tick, is what says whether the claims were actually checked.

## Miner defect taxonomy

| class | name | seen | description |
| --- | --- | --- | --- |
| `D1` | anaphoric anchor | 0 | The span opens on, or silently depends on, a referent outside itself — 'If true', 'any of these models'. The claim cannot be checked against the anchor alone. |
| `D2` | wrong relation label | 0 | The miner matched a trigger word and labelled the candidate with a relation the sentence does not express. The evidence is usually fine; the label aims the reviewer at the wrong question. |
| `D3` | example-code false binding | 0 | An identifier matched inside a fenced code block or JSON literal and was framed as a documented rule. A sample configuration is not a rule. |

## Provenance

| | |
| --- | --- |
| source batch sha256 | `b108d925a09c539de26cb2f7a3e8b96a0fbf3462d0c0f6b95e1a86e82df07736` |
| corpus snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| schema version | 1.0 |
| git commit at generation | `f5214aeed262` |
| closure sha256 | `69364f672e233fb32685a7a0fe283cfaec7c864816e9a3db7759d9bb7a132965` |

The closure hash covers the candidate records. A closed batch is not supposed to change again, and the test suite re-checks this hash, so an edit after closure fails the tests rather than passing unnoticed.

## Validation

`scripts/validate_golden.py` — **17 cases, 0 failures**, `--require-human validation`.

**Caveat.** All 17 verified cases carry literal critical strings, so the claim-in-evidence check ran on every one of them. The validator's pass covers claim support, not only structure.

## Retrieval

No retrieval system was run against any candidate in this batch at any point. SYSTEM-A and SYSTEM-B remain frozen and were not executed. Candidate selection could not be influenced by what either system succeeds or fails on, which is what keeps a future holdout honest.

`retrieval_was_not_run: True`

## Not done, and deliberately so

- No split has been assigned; the projection's split is a placeholder.
- No holdout is frozen.
- Critical claim strings exist for 17 of 17 verified cases; the rest are not claim-checked.
- OA-002 remains a recorded defect in development/v1 with an unapplied development/v2 correction proposal.
