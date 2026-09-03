# GOLD-001 — closure at 150

Closed 2026-08-31T03:39:01Z · closure hash `32b59f774d3efa31`

**150 cases is the achieved GOLD benchmark-size target.** That is a size. It is not coverage, and the rest of this document is what the size does not buy.

## The counts

| | count |
| --- | --- |
| `human_verified` | **150** |
| `holdout_eligible` | **150** |
| `human_rejected` | 9 |
| genuine multi-hop | 1 |
| candidates reviewed | 159 |

Derived from the group records through `rag_v1.gold.eligibility`, not asserted. Conditions checked: `human_verified`, `every_claim_has_a_deterministic_check`, `critical_strings_present_in_evidence`, `evidence_hash_valid`, `no_unresolved_scope_defect`, `required_evidence_declared`.

| group | `human_verified` | `human_rejected` | `holdout_eligible` |
| --- | --- | --- | --- |
| 001 | 16 | 2 | **16** |
| 002 | 17 | 1 | **17** |
| 003 | 20 | 0 | **20** |
| 004 | 14 | 1 | **14** |
| 005 | 15 | 4 | **15** |
| 006 | 8 | 1 | **8** |
| HA-01–HA-60 | 60 | 0 | **60** |

## What 150 does not mean

- **Provider imbalance.** 96 of 150 eligible cases come from one provider (openai). A per-provider result from this set is not a comparison between providers.
- **Category imbalance.** the largest recorded category holds 58 of 150 cases and the smallest holds 1; 33 cases predate the field entirely. An unweighted score over this set is dominated by the largest category.
- **Genuine multi-hop is n=1.** 1 case. One observation cannot support any claim about multi-hop performance, and 150 does not change that.
- **The preregistered pilot sequence was not followed.** ACCEPTED_PROTOCOL_DEVIATION — see `GOLD-001-protocol-deviation-001.md`. The 60 admitted cases are not that pilot and must never be described as it.
- **Corpus reproduction is incomplete; 139 Anthropic documents and 2482 unbuildable identities outstanding.** Reaching 150 does not certify the frozen corpus.
- **Retrieval remains RETRIEVAL_BLOCKED.** No system may be run against these cases until the corpus gate clears.

## Coverage, as measured

| dimension | distribution |
| --- | --- |
| provider | openai 96, anthropic 54 |
| reasoning type | exact_lookup 58, (not recorded in this batch's schema) 33, configuration_interaction 23, error_behavior 19, lifecycle_compatibility_migration 8, request_response 5, lifecycle 2, ambiguity_disambiguation 1, genuine_multi_hop 1 |
| evidence shape | single_span 93, (not recorded in this batch's schema) 33, multi_span_same_fact 16, multi_span 7, multi_document 1 |
| distinct source documents | 60 |
| cases from the single most-used document | 14 |
| ambiguity cases | 1 |

## The 60 admitted cases

Admitted from `Production_RAG_v1_Full_150_Case_Review.pdf` (sha256 `bf6190fc53ee4ada6c948093d30e8fa7feac3dbf3300918ec75886d2a5a8f786`), bound by evidence identity rather than by the short HA label, on the decision of `project_owner`. The separate Claude-authored 64-case packet is NOT_ADMITTED and contributed no case to this total. See GOLD-001-alternate-HA-packet-disposition.json.

- **HA-15** carries `NONCRITICAL_ANAPHORA` with the detector's finding retained — _refers to 'the model' with no antecedent in the span_ — and an explicit `project_owner` override.
- **HA-47** was repaired to one contiguous span 4308:4916 (`e894c94d831ccfd2678f4cd132b72b52e44770d07ebeaab6c51e96e0e312a203`), recomputed from the frozen source. Reason: `EVIDENCE_BOUNDARY_COMPLETION`, `CRITICAL_ANAPHORA_REPAIR`. The pre-repair spans and hashes are kept in the record's revision history; a paragraph break is present and, read from the predicate, does not block eligibility.

## Splits are not frozen

`holdout_frozen` is **false**. 150 eligible cases can support the 30–40 / 70–100 split by size, so size is no longer the reason. What is missing is a split policy: the set is provider- and category-skewed and holds 1 genuine multi-hop case, so an unweighted split would decide by accident which categories the holdout can measure. Freezing also stays blocked while corpus reproduction is incomplete.

## Untouched

SYSTEM-A and SYSTEM-B remain frozen and unexecuted. `retrieval_was_not_run` is true and `systems_executed` is empty. No candidate selection has seen a retrieval outcome, which is the property that makes a future holdout worth having.
