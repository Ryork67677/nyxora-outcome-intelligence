# EVAL-SPLIT-001 — split report

**FROZEN** — generated 2026-08-31T22:30:29Z, seed `689336380`, algorithm `eval-split-001/v1`.

## Gates

| gate | result |
| --- | --- |
| every case assigned once | PASS |
| no contaminated in validation | PASS |
| no contaminated in holdout | PASS |
| validation all unexposed | PASS |
| holdout all unexposed | PASS |
| no cluster straddles a split | PASS |
| snapshot unchanged | PASS |

## Counts

| split | cases | target |
| --- | --- | --- |
| development | 20 | 20 |
| validation | 40 | 40 |
| holdout | 90 | 90 |
| **total** | **150** | **150** |

## Exposure

{'UNEXPOSED': 149, 'EXPOSED_EVIDENCE_OVERLAP': 1}. Contaminated cases: ['HA-11'] — all in development.

## Distributions

### development — 20 cases

- provider: {'openai': 13, 'anthropic': 7} ({'openai': 65.0, 'anthropic': 35.0}%)
- reasoning type: {'error_behavior': 2, 'unlabeled_legacy': 4, 'exact_lookup': 9, 'configuration_interaction': 3, 'lifecycle_compatibility_migration': 1, 'request_response': 1}
- evidence shape: {'single_span': 17, 'multi_span_same_fact': 2, 'multi_span': 1}
- spans per case: {1: 17, 2: 3}; multi-span: 3
- batch/group: {'HA': 8, '001': 2, '002': 2, '003': 3, '004': 2, '005': 2, '006': 1}
- source documents: 15 unique, most concentrated holds 3 cases
- top documents: [('Human-in-the-loop', 3), ('Guardrails', 2), ('Claude on Google Cloud', 2)]

### validation — 40 cases

- provider: {'openai': 26, 'anthropic': 14} ({'openai': 65.0, 'anthropic': 35.0}%)
- reasoning type: {'exact_lookup': 16, 'request_response': 1, 'unlabeled_legacy': 9, 'configuration_interaction': 6, 'lifecycle': 1, 'error_behavior': 5, 'lifecycle_compatibility_migration': 2}
- evidence shape: {'multi_span_same_fact': 5, 'single_span': 33, 'multi_span': 2}
- spans per case: {2: 7, 1: 33}; multi-span: 7
- batch/group: {'HA': 16, '001': 4, '002': 5, '003': 5, '004': 4, '005': 4, '006': 2}
- source documents: 26 unique, most concentrated holds 5 cases
- top documents: [('Handoffs', 5), ('Realtime transport', 4), ('Configuration', 4)]

### holdout — 90 cases

- provider: {'openai': 57, 'anthropic': 33} ({'openai': 63.3, 'anthropic': 36.7}%)
- reasoning type: {'ambiguity_disambiguation': 1, 'genuine_multi_hop': 1, 'configuration_interaction': 14, 'request_response': 3, 'exact_lookup': 33, 'unlabeled_legacy': 20, 'error_behavior': 12, 'lifecycle': 1, 'lifecycle_compatibility_migration': 5}
- evidence shape: {'multi_span': 4, 'multi_document': 1, 'multi_span_same_fact': 9, 'single_span': 76}
- spans per case: {2: 14, 1: 76}; multi-span: 14
- batch/group: {'004': 8, 'HA': 36, '002': 10, '003': 12, '001': 10, '005': 9, '006': 5}
- source documents: 44 unique, most concentrated holds 10 cases
- top documents: [('Configuration', 10), ('Human-in-the-loop', 7), ('Models', 6)]

Overall provider mix: {'openai': 96, 'anthropic': 54}.

## Fact clusters

137 clusters, of which 10 hold more than one case, covering 23 cases. Clusters straddling a split boundary: 0.

Thresholds: {'overlap_chars': 40, 'claim_jaccard': 0.8, 'question_jaccard': 0.75}.

## Rare categories

- `genuine_multi_hop`: 1 case(s) ['GOLD-B004-15'], exposed: none → placed in ['holdout']
- `ambiguity_disambiguation`: 1 case(s) ['GOLD-B004-09'], exposed: none → placed in ['holdout']

A category with two or fewer members is a sentinel, not a statistic. Neither supports an aggregate claim and neither should be reported as one.

## Interventions

None. Every cluster was placed by the deterministic rule without manual override.

## Generation policy

**Answer generation must use fresh, stateless model calls. The generation input carries only the experiment-defined system prompt, the query and the retrieved context — nothing from any benchmark-authoring conversation, and no prior turn of one.**

Claude, ChatGPT, Grok and Codex participated in authoring and review of these cases. Retrieval configurations were not tuned on them, but answer generation must not be run inside an authoring conversation.

## Not done

- No retrieval was run: no BM25, dense, RRF, DOC-C, routing, reranking or generation, and no rank or score was computed.
- No case was placed using system performance knowledge.
- No GOLD record was modified.
- The holdout was not run.
