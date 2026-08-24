# GOLD-001 — batch 006 generation report

**9 candidates** from a mined pool of 1364, across 8 distinct documents. Nothing is verified; nothing is gold.

The target was 28 and the batch exported 9. The shortfall is reported, not padded: what was available after the gates below is what is here.

## The four preregistered fixes, applied before anything was authored

| | fix | implemented in | from |
| --- | --- | --- | --- |
| **A** | bare-definition-bullet scope applied to every span | `rag_v1.gold.scoping` | `GOLD-B005-01` |
| **B** | markdown links stripped from questions and answers | `rag_v1.gold.normalisation.strip_markdown_links` | `GOLD-B005-15` |
| **C** | heading parser audited; section_path not trusted for scope | `scripts/audit_heading_parser.py` | `GOLD-B005-11` |
| **D** | source and question triples recorded and compared | `rag_v1.gold.relations` | `GOLD-B005-10` |

Each was recorded in batch 005's closure as a preregistration input, and each has a regression test built from the candidate that motivated it (`tests/test_gold001_b006_fixes.py`). Batch 005's own artifacts are unchanged — the fixes are forward-looking, which is the point of recording them rather than patching.

## Starting state

Read from `experiments/GOLD-001/GOLD-001-eligibility-status.json` before generating: **82 human_verified**, **82 holdout_eligible**, 8 rejected, 1 genuine multi-hop, across 90 historical candidates. Holdout frozen: false.

## Composition

| | |
| --- | --- |
| provider | {'anthropic': 5, 'openai': 4} |
| documents by provider | {'anthropic': 4, 'openai': 4} |
| reasoning type | {'configuration_interaction': 4, 'error_behavior': 1, 'exact_lookup': 4} |
| evidence shape | {'single_span': 9} |
| confidence | {'medium': 8, 'high': 1} |
| distinct documents | 8 |
| genuine multi-hop | 0 |
| complete question / answer / claims | 9 / 9 / 9 of 9 |
| needing reviewer judgement | 0 of 9 |
| precheck holdout-ready | 9 of 9 |

**`precheck_holdout_ready` means: STRUCTURAL ONLY — not semantic correctness, not independent verification, not human approval, not holdout eligibility.**

### Reasoning types against target

| reasoning type | in batch | target | met | eligible available |
| --- | --- | --- | --- | --- |
| `error_behavior` | 1 | 5–6 | under | 1 |
| `configuration_interaction` | 4 | 6–7 | under | 4 |
| `exact_lookup` | 4 | 5–6 | under | 4 |
| `lifecycle_compatibility_migration` | 0 | 4–5 | under | 1 |
| `ambiguity_disambiguation` | 0 | 0–3 | yes | 0 |
| `comparison` | 0 | 0–2 | yes | 0 |
| `genuine_multi_hop` | 0 | 0–1 | yes | 0 |

### Providers against target

| provider | in batch | target | met | documents |
| --- | --- | --- | --- | --- |
| openai | 4 | 12–14 | under | 4 |
| anthropic | 5 | 12–14 | under | 4 |

## The self-review

50 candidates reached the semantic self-review: **10** were ready, **0** were repaired, **40** were dropped. This is authoring, not verification.

| gate that fired | candidates |
| --- | --- |
| `BARE_DEFINITION_SCOPE` | 12 |
| `NO_TRIPLE` | 9 |
| `GENERIC_IDENTIFIER` | 9 |
| `CATEGORY` | 5 |
| `QUESTION_SCOPE` | 2 |
| `QUESTION_FORM` | 1 |
| `SUBJECT_MISMATCH` | 1 |
| `CLAIM_SCOPE` | 1 |

### What was dropped and why

| reasoning type | gate | question |
| --- | --- | --- |
| exact_lookup | QUESTION_FORM | What must `openssl` be? |
| exact_lookup | BARE_DEFINITION_SCOPE | What does the `is_enabled` option control? |
| exact_lookup | NO_TRIPLE | What is the `nest_handoff_history` option? |
| configuration_interaction | CATEGORY | What does `created_at` require? |
| configuration_interaction | NO_TRIPLE | What happens if recent raw memories exceed `max_raw_memories_for_conso… |
| exact_lookup | BARE_DEFINITION_SCOPE | What is the `default_message` option? |
| exact_lookup | BARE_DEFINITION_SCOPE | What is the `encrypted_index` option? |
| exact_lookup | BARE_DEFINITION_SCOPE | What is the `request_too_large` option? |
| exact_lookup | BARE_DEFINITION_SCOPE | What is the `parsed` option? |
| exact_lookup | BARE_DEFINITION_SCOPE | What is the `arguments` option? |
| exact_lookup | BARE_DEFINITION_SCOPE | What is the `arguments_delta` option? |
| exact_lookup | BARE_DEFINITION_SCOPE | What is the `refusal` option? |
| exact_lookup | BARE_DEFINITION_SCOPE | What is the `refusal` option? |
| exact_lookup | BARE_DEFINITION_SCOPE | What is the `group_id` option? |
| exact_lookup | BARE_DEFINITION_SCOPE | What is the `insert_line` option? |
| lifecycle_compatibility_migration | NO_TRIPLE | What should I move to instead of `httpx`? |
| exact_lookup | BARE_DEFINITION_SCOPE | What is the `tool_use_id` option? |
| configuration_interaction | SUBJECT_MISMATCH | What happens when the memory tool is present in your request's `tools`… |
| exact_lookup | GENERIC_IDENTIFIER | What must `name` be? |
| exact_lookup | GENERIC_IDENTIFIER | What must `name` be? |
| exact_lookup | GENERIC_IDENTIFIER | What must `name` be? |
| configuration_interaction | QUESTION_SCOPE | What does `RunConfig.session_settings` override? |
| configuration_interaction | NO_TRIPLE | What happens when extended thinking is enabled without explicit `clear… |
| configuration_interaction | QUESTION_SCOPE | What does Grouping by `speed` require? |
| configuration_interaction | NO_TRIPLE | What does `speed` require? |
| configuration_interaction | NO_TRIPLE | What happens when the API receives a `compaction` block? |
| configuration_interaction | CLAIM_SCOPE | What does Because setting `max_retries` to `0` disable? |
| configuration_interaction | CATEGORY | What does Version 0.21.0 require? |
| configuration_interaction | CATEGORY | What does Setting `audio.input.turn_detection=None` explicitly disable… |
| configuration_interaction | NO_TRIPLE | What does `audio.input.turn_detection=None` disable? |

40 drops in total; the first 30 are listed. They are recorded rather than regenerated away: what the miner gets wrong is part of what this batch measures.

## Subject and relation triples

Every candidate carries both triples. How the source triple was read: {'named relation': 9}. A *named relation* is one this project has a directed pattern for, and is the stronger reading; a *generic predicate split* records the sentence's two halves around its verb and is weaker evidence about direction. Both are shown to the reviewer.

## Multi-hop

**No multi-hop search was run.** §7: batch 004 tested 559 bridge pairs and found 1 chain; batch 005 searched dependency-first and found the same one. The corpus has been measured twice. No search was run here, and no multi-span case was relabelled to raise the count. Exported chains: 0.

## Question openings

| opening | candidates |
| --- | --- |
| "what does claude…" | 3 |
| "what does creating…" | 1 |
| "what does `thinking.display`…" | 1 |
| "what does `aws_bedrock_base_url`…" | 1 |
| "what does setting…" | 1 |
| "what does the…" | 1 |
| "what does `runerrorhandlerresult.include_in_history`…" | 1 |

No opening is allowed past 6 candidates. A batch that measures one template measures the template.

## Evidence size

Across 9 spans: mean 169.9, median 181, min 62, max 345 characters. 0 over the 1000-character soft cap, none over the 1500 hard cap.

## Removed before export

| reason | count |
| --- | --- |
| unbuildable | 2482 |
| dropped by semantic review | 40 |
| duplicate evidence | 36 |
| duplicate question | 26 |
| short of target before overflow | 19 |
| duplicate evidence text | 5 |
| excluded known failure case | 1 |
| blocking anaphora | 1 |
| document concentration | 1 |
| not selected diversity | 1 |

## Retrieval

No retrieval system was run against any batch-006 candidate at any point. SYSTEM-A and SYSTEM-B remain frozen and were not executed; their config hashes were verified before generation began. No candidate was selected, ordered or worded because of what any system does with it, and no difficulty label in this batch derives from retrieval behaviour.
