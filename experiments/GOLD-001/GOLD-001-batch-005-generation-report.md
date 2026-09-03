# GOLD-001 — batch 005 generation report

**19 candidates** from a mined pool of 1354, across 16 distinct documents. Nothing is verified; nothing is gold.

Batch 005 was commissioned as an accelerated coverage batch, and split into two lanes because of what batch 004 measured. Lane A mines the shapes the corpus actually contains. Lane B looks for genuine multi-hop chains dependency-first, under a fixed budget, rather than by testing every pair that shares an identifier — batch 004 did that and found one chain in 559.

## Starting state

Read from `experiments/GOLD-001/GOLD-001-eligibility-status.json` before generating: **67 human_verified**, **67 holdout_eligible**, 4 rejected, 1 genuine multi-hop. Holdout frozen: false.

## Composition

| | |
| --- | --- |
| provider | {'anthropic': 8, 'openai': 11} |
| documents by provider | {'anthropic': 7, 'openai': 9} |
| versions by provider | {'anthropic': 8, 'openai': 9} |
| reasoning type | {'ambiguity_disambiguation': 1, 'configuration_interaction': 9, 'error_behavior': 3, 'exact_lookup': 2, 'lifecycle_compatibility_migration': 4} |
| evidence shape | {'multi_document': 1, 'single_span': 18} |
| confidence | {'medium': 10, 'high': 9} |
| genuine multi-hop | 0 |
| multi-document | 1 |
| complete question / answer / claims | 19 / 19 / 19 of 19 |
| needing reviewer judgement | 1 of 19 |
| precheck holdout-ready | 19 of 19 |

### Reasoning types against target

| reasoning type | in batch | target | met | eligible available |
| --- | --- | --- | --- | --- |
| `genuine_multi_hop` | 0 | 0–6 | yes | 0 |
| `error_behavior` | 3 | 5–6 | NO | 3 |
| `configuration_interaction` | 9 | 5–6 | NO | 9 |
| `exact_lookup` | 2 | 5–6 | NO | 2 |
| `lifecycle_compatibility_migration` | 4 | 3–4 | yes | 4 |
| `ambiguity_disambiguation` | 1 | 3–4 | NO | 1 |
| `comparison` | 0 | 2–3 | NO | 0 |

The last column is the honest one. Where it equals the batch count the corpus had nothing more to give under these checks; where it is far above, a ceiling stopped the batch rather than the material.

**3 of 19 candidates were taken beyond §7's ceilings.** Ambiguity, comparison and multi-hop are corpus-limited here, so holding every ceiling would have returned a batch far short of target while vetted candidates waited in the categories that do have material. Rather than quietly raise a ceiling, the shortfall is filled under a declared cap ({'error_behavior': 4, 'configuration_interaction': 4, 'exact_lookup': 3}) and every candidate taken that way is marked `selected_by = "overflow"` in the record. Subtracting them gives the batch the preregistered mixture would have produced.

### Providers against target

| provider | in batch | target | met | documents |
| --- | --- | --- | --- | --- |
| openai | 11 | 14–16 | NO | 9 |
| anthropic | 8 | 14–16 | NO | 7 |

## Multi-hop search — dependency-first

dependency-first: a chain may only open on a sentence that states a dependency and puts the entity in a state.

| stage | pairs |
| --- | --- |
| dependency pairs considered | 3 |
| failed span independence | 1 |
| failed semantic equivalence | 1 |
| passed | 1 |

Budget: 1000 pairs; 3 were considered, so the budget was not the constraint. 122 entities appear in at least one sentence that states a dependency; **1** pair survived every gate, and 0 reached the batch. The survivor is the chain batch 004 already holds, so it is a duplicate rather than a new case — which is why the batch exports none.

The comparison with batch 004 is the useful part. That batch tested 559 identifier-sharing pairs to find one chain; this one considered 3 dependency-first pairs. Starting from sentences that state a dependency removes almost all of the work, and does not conjure chains that are not there — the corpus supports very few, and that remains the finding.

## Generation self-review

{'DROP': 27, 'READY_FOR_INDEPENDENT_REVIEW': 19}. This is the author reading its own output before export. It is not independent verification and not human approval; every candidate is still `candidate_unverified`.

### Dropped rather than shipped with a caveat

| reasoning type | finding | question |
| --- | --- | --- |
| `exact_lookup` | QUESTION_FORM | What must `openssl` be? |
| `configuration_interaction` | CATEGORY | What does `created_at` require? |
| `configuration_interaction` | CATEGORY | What happens if recent raw memories exceed `max_raw_memories_for_conso |
| `exact_lookup` | CLAIM_SCOPE | What is the `default_message` option? |
| `exact_lookup` | CLAIM_SCOPE | What is the `parsed` option? |
| `exact_lookup` | CLAIM_SCOPE | What is the `group_id` option? |
| `exact_lookup` | CLAIM_SCOPE | What is the `insert_line` option? |
| `lifecycle_compatibility_migration` | CLAIM_SCOPE | What should I move to instead of `httpx`? |
| `exact_lookup` | CLAIM_SCOPE | What is the `tool_use_id` option? |
| `configuration_interaction` | CATEGORY | What happens when the memory tool is present in your request's `tools` |
| `exact_lookup` | GENERIC_IDENTIFIER | What must `name` be? |
| `exact_lookup` | GENERIC_IDENTIFIER | What must `name` be? |
| `exact_lookup` | GENERIC_IDENTIFIER | What must `name` be? |
| `configuration_interaction` | QUESTION_SCOPE | What does `RunConfig.session_settings` override? |
| `configuration_interaction` | CATEGORY | What happens when extended thinking is enabled without explicit `clear |
| `configuration_interaction` | QUESTION_SCOPE | What does `speed` require? |
| `configuration_interaction` | CATEGORY | What happens when the API receives a `compaction` block? |
| `configuration_interaction` | CATEGORY | What does `audio.input.turn_detection=None` disable? |
| `error_behavior` | GENERIC_IDENTIFIER | What happens if the precondition fails but the stored state already ex |
| `error_behavior` | GENERIC_IDENTIFIER | What happens if the precondition fails but the stored state already ex |

## Question shapes

| opening | candidates |
| --- | --- |
| "what happens when…" | 4 |
| "what happens if…" | 3 |
| "in web fetch…" | 1 |
| "what must `allowed_domains`…" | 1 |
| "where is `fallbacks`…" | 1 |
| "is `compaction_control` still…" | 1 |
| "where is `budget_tokens`…" | 1 |
| "what does `betas`…" | 1 |

No opening is allowed past 8 candidates. §26's concern is a batch that measures one template; the spread here comes from the facts being different kinds of statement, not from a generator alternating phrasings.

## Evidence size

Across 20 spans: mean 141.8, median 133, min 70, max 277 characters. 0 over the 1000-character soft cap, none over the 1500 hard cap.

## Removed before export

| reason | count |
| --- | --- |
| unbuildable | 1260 |
| dropped by semantic review | 27 |
| duplicate evidence | 26 |
| duplicate question | 18 |
| short of target before overflow | 14 |
| duplicate evidence text | 3 |
| reasoning type ceiling | 3 |
| excluded known failure case | 1 |
| blocking anaphora | 1 |
| not selected diversity | 0 |

## Retrieval

No retrieval system was run against any batch-005 candidate at any point. SYSTEM-A and SYSTEM-B remain frozen and were not executed. No candidate was selected, ordered or worded because of what any system does with it, and no difficulty label in this batch derives from retrieval behaviour.
