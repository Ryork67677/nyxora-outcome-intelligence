# GOLD-001 — batch 001 closure

**Closed 2026-08-20T06:21:04Z by project_owner.** Every candidate reached an explicit human decision. Nothing is outstanding.

| | |
| --- | --- |
| candidates | 18 |
| `human_verified` | **16** |
| `human_rejected` | 2 |
| `needs_human_review` | 0 |
| outstanding decisions | 0 |
| acceptance rate | **88.9%** |

Acceptance rate is not a quality score. It is the share of *mined candidates* a person kept, and it says as much about how permissive the miner was as about how good the evidence is. With n=18 one candidate moves it 5.6 points.

## Rejected — kept, not deleted

| candidate | defects | reason |
| --- | --- | --- |
| `GOLD-B001-15` | D3 | REJECT — code/example false binding. `required: ["location"]` belongs to the tool input schema in the example request and does not establish a general requirement on `tool_choice`. |
| `GOLD-B001-16` | D3 | REJECT — concerns the implementation behaviour of a local example helper function rather than an externally meaningful API or documentation fact. Stronger benchmark material is preferred. |

Both records remain in the batch as negative audit examples. A rejection is evidence about the miner, and deleting it would discard the only record of what the miner got wrong.

## Repaired — anchors extended, originals preserved

| candidate | old span | new span | approved anchor |
| --- | --- | --- | --- |
| `GOLD-B001-03` | 2410–2519 | 2223–2519 | `54f4b6a0802f…` |
| `GOLD-B001-04` | 1930–2119 | 1496–2119 | `f54443978632…` |
| `GOLD-B001-14` | 19189–19308 | 19054–19308 | `9e8be2c9734a…` |

Each repair grew the anchor outward to contain what its claims already depended on; the new span is a strict superset of the old, and both are retained in `anchor_revisions`. Each approval pins the post-repair hash, so the record shows which version the owner actually approved.

## Miner defect taxonomy

| class | name | seen | description |
| --- | --- | --- | --- |
| `D1` | anaphoric anchor | 3 | The span opens on, or silently depends on, a referent outside itself — 'If true', 'any of these models'. The claim cannot be checked against the anchor alone. |
| `D2` | wrong relation label | 4 | The miner matched a trigger word and labelled the candidate with a relation the sentence does not express. The evidence is usually fine; the label aims the reviewer at the wrong question. |
| `D3` | example-code false binding | 2 | An identifier matched inside a fenced code block or JSON literal and was framed as a documented rule. A sample configuration is not a rule. |

## Provenance

| | |
| --- | --- |
| source batch sha256 | `a3fe9242e33fb2dff8be78f4c5f1baffc8037066b09445a936a2e3dc9f11ea73` |
| corpus snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| schema version | 1.0 |
| git commit at generation | `67de5563f469` |
| closure sha256 | `d6f92e8d1a7e77eae760d8a866b0353603aeefaec3c2309817e64f19a3a39f97` |

The closure hash covers the candidate records. A closed batch is not supposed to change again, and the test suite re-checks this hash, so an edit after closure fails the tests rather than passing unnoticed.

## Validation

`scripts/validate_golden.py` — **16 cases, 0 failures**, `--require-human validation`.

**Caveat.** The claim-in-evidence check only fires on claims marked critical. Only the three repaired cases carry literal critical strings, so for the other 13 this pass says nothing about claim support. That gap must be closed before any of these enters a frozen holdout.

## Retrieval

No retrieval system was run against any candidate in this batch at any point. SYSTEM-A and SYSTEM-B remain frozen and were not executed. Candidate selection could not be influenced by what either system succeeds or fails on, which is what keeps a future holdout honest.

`retrieval_was_not_run: True`

## Not done, and deliberately so

- No split has been assigned; the projection's split is a placeholder.
- No holdout is frozen.
- Critical claim strings exist for 3 of 16 verified cases; the rest are not claim-checked.
- OA-002 remains a recorded defect in development/v1 with an unapplied development/v2 correction proposal.
