# GOLD-001 — batch 004 generation report

**15 candidates** from a mined pool of 58, across 10 distinct documents. Nothing is verified; nothing is gold.

Batch 004 was commissioned to fix a specific hole: batch 003 closed with **zero** genuine multi-hop cases after four candidates carrying that label failed scrutiny. The composition check now runs before export rather than after review.

## Composition

| | |
| --- | --- |
| provider | {'anthropic': 7, 'openai': 8} |
| documents by provider | {'anthropic': 5, 'openai': 5} |
| versions by provider | {'anthropic': 5, 'openai': 6} |
| reasoning type | {'configuration_interaction': 5, 'error_behavior': 3, 'exact_lookup': 3, 'lifecycle_compatibility_migration': 1, 'ambiguity_disambiguation': 2, 'genuine_multi_hop': 1} |
| evidence shape | {'single_span': 12, 'multi_span': 2, 'multi_document': 1} |
| confidence | {'medium': 12, 'high': 3} |
| genuine multi-hop | 1 |
| multi-document | 1 |
| complete question+answer+claims | 15 of 15 |
| needing reviewer judgement | 3 of 15 |
| precheck holdout-ready | 15 of 15 |

### Reasoning types against target

| reasoning type | in batch | target | met | eligible candidates available |
| --- | --- | --- | --- | --- |
| `genuine_multi_hop` | 1 | 6–8 | NO | 1 |
| `configuration_interaction` | 5 | 4–5 | yes | 39 |
| `ambiguity_disambiguation` | 2 | 3–4 | NO | 2 |
| `error_behavior` | 3 | 2–3 | yes | 18 |
| `lifecycle_compatibility_migration` | 1 | 2–3 | NO | 1 |
| `exact_lookup` | 3 | 0–3 | yes | 16 |

The last column is the honest part. Where it is at or below the batch count, the corpus had nothing more to give under the checks in §6, §9 and §20 — the target was not missed by selection. Where it is far above, the ceiling stopped the batch, not the material.

### Providers against target

| provider | in batch | target | met |
| --- | --- | --- | --- |
| openai | 8 | 10–12 | NO |
| anthropic | 7 | 8–10 | NO |

A target that reads `NO` was not met, and was not made to read `yes` by relabelling a candidate or lowering the evidence standard. §3 of the brief puts quality above count, and a missed target is the honest report of what the frozen corpus supports.

## Evidence size

Across 18 spans: mean 141.4, median 144, max 330 characters. 0 over the 1000-character soft cap, none over the 1500 hard cap. Multi-hop cases are measured per span, not per case, because the size that matters is the size of each anchor.

## Removed before export

| reason | count |
| --- | --- |
| blocking anaphora | 1 |
| duplicate evidence | 25 |
| duplicate question | 24 |
| excluded known failure case | 1 |
| failed precheck | 4 |
| fake multi hop | 558 |
| not selected diversity | 62 |
| reasoning type ceiling | 62 |

## Fake multi-hop rejection

The composer tested 559 bridge pairs. 1 passed the composition check; 558 were rejected. That ratio is the finding: in this corpus, two facts sharing an identifier are almost never two halves of an argument.

| rejection reason | count |
| --- | --- |
| the spans were two unrelated lookups | 379 |
| no bridge relationship existed | 147 |
| span 1 alone answered the full question | 16 |
| span 2 alone answered the full question | 16 |
| the composed answer introduced unsupported inference | 0 |

Counted from each check's own reason string, not asserted. A pair is counted once, under the first reason it failed. `unclassified` is a guard: it should be 0, and a non-zero value means a check grew a reason the report does not know how to file.

### The same rejections by the check that made them

| check | pairs |
| --- | --- |
| span 2 states no condition on the bridge entity | 371 |
| span 1 enumerates values rather than stating a requirement about the bridge entity | 147 |
| span 1 alone already answers the whole question | 16 |
| span 2 alone already answers the whole question | 16 |
| the spans are two unrelated lookups | 8 |

This is the number batch 003 could not produce, because it had no check to fail. A rejection rate that looks bad is the measurement working: it says how often two facts that share an identifier are not actually a hop.

## Retrieval

No retrieval system was run against any batch-004 candidate at any point. SYSTEM-A and SYSTEM-B remain frozen and were not executed. No candidate was selected, ordered or worded because of what any system does with it, and no difficulty label in this batch derives from retrieval behaviour.
