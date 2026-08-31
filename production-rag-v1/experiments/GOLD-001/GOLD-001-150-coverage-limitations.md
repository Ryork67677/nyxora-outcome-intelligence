# GOLD-001 — coverage limitations at 150

As of 2026-08-31T03:39:01Z. Every figure is counted from the 150 eligible records.

The benchmark reached its size target. This document is the case against reading that as readiness.

## Provider distribution

| value | cases | share |
| --- | --- | --- |
| openai | 96 | 64% |
| anthropic | 54 | 36% |

A per-provider number from this set measures the larger provider's documentation and, for the smaller one, a sample too thin to separate a real difference from noise.

## Category distribution

| value | cases | share |
| --- | --- | --- |
| exact_lookup | 58 | 39% |
| (not recorded in this batch's schema) | 33 | 22% |
| configuration_interaction | 23 | 15% |
| error_behavior | 19 | 13% |
| lifecycle_compatibility_migration | 8 | 5% |
| request_response | 5 | 3% |
| lifecycle | 2 | 1% |
| ambiguity_disambiguation | 1 | 1% |
| genuine_multi_hop | 1 | 1% |

An unweighted score over these cases is close to a score over the largest category alone. Any per-category claim needs its own n reported beside it.

## Evidence shape

| value | cases | share |
| --- | --- | --- |
| single_span | 93 | 62% |
| (not recorded in this batch's schema) | 33 | 22% |
| multi_span_same_fact | 16 | 11% |
| multi_span | 7 | 5% |
| multi_document | 1 | 1% |

## Genuine multi-hop

**1 case: GOLD-B004-15.** Two independent searches of this corpus — bridge-pair and dependency-first — produced one composable chain between them. That is a property of the corpus, not a tuning failure, and it means this benchmark cannot answer a question about multi-hop retrieval no matter how large the total grows.

## Source-document concentration

The 150 eligible cases are anchored in 60 distinct document versions.

| document version | cases | share |
| --- | --- | --- |
| `ver_f15e1a531d680bb98179238f80355058` | 14 | 9% |
| `ver_ae3bfcc42c733c5051abda30f0f6db07` | 12 | 8% |
| `ver_1c77f33b04ffffa285ea7e61c2a89653` | 11 | 7% |
| `ver_ae909bf8b4bbbe1d1a11119447f7ac94` | 9 | 6% |
| `ver_f22fbd5c504fa28a4e70440337e4a495` | 8 | 5% |

The most-used single document supplies 14 cases (9%). A retrieval system that happens to chunk that document well will look better than it is.

## Ambiguity cases

**1**: GOLD-B004-09. At this count the set cannot measure whether a system declines to answer an under-specified question; it can only show that the category exists.

33 eligible cases carry no `reasoning_type` at all — batches 001 and 002 predate the field. They are counted separately above rather than folded into a category they were never assigned, and any per-category analysis has to decide what to do with them.

## Protocol deviation

ACCEPTED_PROTOCOL_DEVIATION — the preregistered 10-case NO_BUILDER-only pilot was not run before the 60-case derivative was authored. See `GOLD-001-protocol-deviation-001.md`. Those 60 cases are not that pilot.

## Corpus reproduction

Reproduction is incomplete; 139 Anthropic documents and 2482 unbuildable identities outstanding. Retrieval is RETRIEVAL_BLOCKED: reaching 150 admitted cases says nothing about whether the frozen corpus those cases point into can be reconstituted.
