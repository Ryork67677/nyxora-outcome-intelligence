# GOLD-001 — batch 003 generation report

**20 candidates** mined from a pool of 42, across 17 distinct documents. Nothing is verified; nothing is gold.

## Composition

| | |
| --- | --- |
| provider | {'anthropic': 12, 'openai': 8} |
| documents by provider | {'anthropic': 10, 'openai': 7} |
| evidence kind | {'normative_statement': 10, 'parameter_table_row': 1, 'definition_bullet': 5, 'multi_span': 4} |
| confidence | {'high': 16, 'medium': 4} |
| complete proposals | 16 of 20 |
| precheck holdout-ready | 20 of 20 |

### Categories against target

| category | in batch | target |
| --- | --- | --- |
| `exact_constraint` | 6 | 4–5 |
| `error_behavior` | 4 | 3–4 |
| `multi_hop` | 4 | 3–4 |
| `configuration_interaction` | 4 | 2–3 |
| `lifecycle` | 2 | 2–3 |

## Evidence size

Mean 150.1, median 129, max 295 characters. 0 over the 1000-character soft cap, none over the 1500 hard cap.

Batch 002 rejected a candidate whose self-contained anchor needed 1,430 characters for one fact. Keeping spans small is not tidiness: an anchor the size of a section makes retrieval easy for the wrong reason.

## Removed before export

| reason | count |
| --- | --- |
| duplicate evidence | 2 |
| duplicate question | 5 |
| not selected diversity | 11 |

## Generation quality across batches

Generation and evidence metrics only. No retrieval was run against any candidate in any batch.

| metric | 001 (as generated) | 002 (as generated) | 003 |
| --- | --- | --- | --- |
| candidates | 18 | 18 | 20 |
| OpenAI share | 33% | 17% | 40% |
| distinct documents | 18 | 18 | 17 |
| distinct question forms | 2 | 3 | 9 |
| complete question+answer+claims | 2 | 9 | 20 |
| carrying critical strings | 3 | 18 | 20 |
| needing reviewer authoring | 16 | 9 | 4 |
| anaphoric spans | 4 | 0 | 1 |
| median evidence chars | 186 | 209 | 129 |
| max evidence chars | 623 | 1430 | 295 |

Batches 001 and 002 are measured **as generated** — the miner's original wording recovered from revision 1 — because their stored text is what review rewrote. Comparing batch 003's unreviewed proposals to a reviewed batch would credit batch 003 with a person's work.

## Retrieval

No retrieval system was run against any batch-003 candidate at any point. SYSTEM-A and SYSTEM-B remain frozen and were not executed. No candidate was selected, ordered or worded because of what any system does with it.
