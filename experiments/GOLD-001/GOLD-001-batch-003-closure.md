# GOLD-001 — batch 003 closure

**Closed 2026-08-21T00:02:09Z by project_owner.** Every candidate reached an explicit human decision. Nothing is outstanding.

| | |
| --- | --- |
| candidates | 20 |
| `human_verified` | **20** |
| `human_rejected` | 0 |
| `needs_human_review` | 0 |
| outstanding decisions | 0 |
| acceptance rate | **100.0%** |

Acceptance rate is not a quality score. It is the share of *mined candidates* a person kept, and it says as much about how permissive the miner was as about how good the evidence is. With n=18 one candidate moves it 5.6 points.

## Rejected — kept, not deleted

| candidate | defects | reason |
| --- | --- | --- |


Both records remain in the batch as negative audit examples. A rejection is evidence about the miner, and deleting it would discard the only record of what the miner got wrong.

## Repaired — anchors extended, originals preserved

| candidate | old span | new span | approved anchor |
| --- | --- | --- | --- |
| `GOLD-B003-04` | 92785–92898 | 88971–89112, 92785–92898 | `a147d3f035dd…` |
| `GOLD-B003-06` | 2207–2293 | 1820–2293 | `fbd40033fb7a…` |
| `GOLD-B003-16` | 5603–5672 | 5518–5672 | `e06211303ca4…` |
| `GOLD-B003-17` | 5944–6000 | 5741–6000 | `f3a7e4d49ba9…` |
| `GOLD-B003-19` | 15366–15450, 15451–15557 | 15267–15450, 15451–15557 | `9edfa438aab0…` |

Each repair grew the anchor outward to contain what its claims already depended on; the new span is a strict superset of the old, and both are retained in `anchor_revisions`. Each approval pins the post-repair hash, so the record shows which version the owner actually approved.

## Question-authoring revisions

9 of 20 candidates had their question, answer or claims re-authored during review. The miner's original wording is retained on every one of them as revision 1; nothing was overwritten.

**Claims actually checkable: 20 of 20 verified cases carry literal critical strings.** A case without literal critical strings passes the claim-in-evidence gate vacuously. This count, not the validator's green tick, is what says whether the claims were actually checked.

## Reasoning type and evidence shape

Reasoning types: {'configuration_interaction': 4, 'error_behavior': 4, 'exact_lookup': 10, 'lifecycle': 2}. Evidence shapes: {'single_span': 15, 'multi_span': 5}.

**Genuine multi-hop reasoning cases: 0**, against a generation target of three to four.

Reasoning type and evidence shape are separate dimensions. A case needing two spans is multi_span; multi_hop is a reasoning type, and a case only earns it when the answer is derived from combining spans rather than being the spans' contents. The multi-span cases in this batch are useful multi-evidence retrieval tests and are not relabelled to close the gap; a later batch has to target genuine multi-hop reasoning directly.

## Errata

- **E3** — The first GOLD-B003-04 final-case artifact printed `needs_human_review = 0` while its own prose said the case was awaiting review. Cause: a status-counting bug, not display or prose. `import_human_decisions` wrote `status_counts = {human_verified: 19, needs_edit: 1}`; `rewrite_b003_04.py` then moved the record to `needs_human_review` and refreshed `precheck_holdout_ready` but not `status_counts`, so the header claimed a status no record held. The true pre-approval state was 19 verified / 1 needing review / 0 rejected. Fixed twice over: the rewrite refreshes the counts, and the renderer now derives them from the records instead of trusting a header. The original artifact is preserved at gold_batch_003_final_case_review-original.md with its error intact, and a regression test asserts a pending case is counted.

## Miner defect taxonomy

| class | name | seen | description |
| --- | --- | --- | --- |
| `D1` | anaphoric anchor | 0 | The span opens on, or silently depends on, a referent outside itself — 'If true', 'any of these models'. The claim cannot be checked against the anchor alone. |
| `D2` | wrong relation label | 0 | The miner matched a trigger word and labelled the candidate with a relation the sentence does not express. The evidence is usually fine; the label aims the reviewer at the wrong question. |
| `D3` | example-code false binding | 0 | An identifier matched inside a fenced code block or JSON literal and was framed as a documented rule. A sample configuration is not a rule. |

## Provenance

| | |
| --- | --- |
| source batch sha256 | `89d2360d60df71aa88e4db217ea68c844fb8000ec7e09a01d4bcd5d6c0c2f7a9` |
| corpus snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| schema version | 1.1 |
| git commit at generation | `bf9c1a8bb937` |
| closure sha256 | `e186a2f30efd4cd610d718df6bddc07a76f205a42bbba3f0bf8945900a49270e` |

The closure hash covers the candidate records. A closed batch is not supposed to change again, and the test suite re-checks this hash, so an edit after closure fails the tests rather than passing unnoticed.

## Validation

`scripts/validate_golden.py` — **20 cases, 0 failures**, `--require-human validation`.

**Caveat.** All 20 verified cases carry literal critical strings, so the claim-in-evidence check ran on every one of them. The validator's pass covers claim support, not only structure.

## Retrieval

No retrieval system was run against any candidate in this batch at any point. SYSTEM-A and SYSTEM-B remain frozen and were not executed. Candidate selection could not be influenced by what either system succeeds or fails on, which is what keeps a future holdout honest.

`retrieval_was_not_run: True`

## Not done, and deliberately so

- No split has been assigned; the projection's split is a placeholder.
- No holdout is frozen.
- Critical claim strings exist for 20 of 20 verified cases; the rest are not claim-checked.
- OA-002 remains a recorded defect in development/v1 with an unapplied development/v2 correction proposal.
