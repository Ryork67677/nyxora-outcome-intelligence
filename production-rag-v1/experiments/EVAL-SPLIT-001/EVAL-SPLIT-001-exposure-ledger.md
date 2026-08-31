# EVAL-SPLIT-001 — exposure ledger

Every one of the 150 approved cases, judged against the 22 historically exposed cases (20 scored + 2 abstain controls).

Those 22 are the complete exposure surface: they are the only case identifiers any EXP-000..EXP-014R result file references, derived by scanning the artifacts rather than taken from a description. The scored twenty appear in 19 experiments each.

## Summary

| exposure status | cases |
| --- | --- |
| `EXPOSED_EVIDENCE_OVERLAP` | 1 |
| `UNEXPOSED` | 149 |

A case may enter validation or holdout only at `UNEXPOSED`. `UNKNOWN` counts as contaminated.

## Criteria

| | test | status assigned |
| --- | --- | --- |
| A | identical case identifier | EXPOSED_DIRECT |
| B | identical normalised question | EXPOSED_DIRECT |
| C | identical evidence anchor | EXPOSED_DIRECT |
| D | any character overlap in the same document | EXPOSED_EVIDENCE_OVERLAP |
| E | claim token overlap ≥ 0.80 | EXPOSED_FACT_PARAPHRASE |
| F | question token overlap ≥ 0.70 | EXPOSED_FACT_PARAPHRASE |
| G | any hop of a composed case exposed | inherits the hop's status |

## Every case

| case | grp | provider | reasoning | shape | exposure | historical match | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GOLD-B001-01` | 001 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B001-02` | 001 | openai | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B001-03` | 001 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B001-04` | 001 | openai | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B001-05` | 001 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B001-06` | 001 | openai | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B001-07` | 001 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B001-08` | 001 | openai | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B001-09` | 001 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B001-10` | 001 | openai | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B001-11` | 001 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B001-12` | 001 | openai | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B001-13` | 001 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B001-14` | 001 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B001-17` | 001 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B001-18` | 001 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-01` | 002 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-02` | 002 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-03` | 002 | openai | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-04` | 002 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-05` | 002 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-06` | 002 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-07` | 002 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-08` | 002 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-09` | 002 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-10` | 002 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-11` | 002 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-13` | 002 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-14` | 002 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-15` | 002 | openai | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-16` | 002 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-17` | 002 | openai | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B002-18` | 002 | anthropic | `null` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-01` | 003 | anthropic | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-02` | 003 | anthropic | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-03` | 003 | anthropic | `error_behavior` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-04` | 003 | anthropic | `error_behavior` | multi_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-05` | 003 | anthropic | `error_behavior` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-06` | 003 | anthropic | `error_behavior` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-07` | 003 | anthropic | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-08` | 003 | anthropic | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-09` | 003 | anthropic | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-10` | 003 | anthropic | `lifecycle` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-11` | 003 | anthropic | `lifecycle` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-12` | 003 | anthropic | `exact_lookup` | multi_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-13` | 003 | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-14` | 003 | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-15` | 003 | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-16` | 003 | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-17` | 003 | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-18` | 003 | openai | `exact_lookup` | multi_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-19` | 003 | openai | `exact_lookup` | multi_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B003-20` | 003 | openai | `exact_lookup` | multi_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B004-01` | 004 | anthropic | `error_behavior` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B004-02` | 004 | anthropic | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B004-03` | 004 | anthropic | `error_behavior` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B004-04` | 004 | anthropic | `error_behavior` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B004-05` | 004 | anthropic | `error_behavior` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B004-06` | 004 | anthropic | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B004-07` | 004 | anthropic | `lifecycle_compatibility_migration` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B004-09` | 004 | openai | `ambiguity_disambiguation` | multi_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B004-10` | 004 | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B004-11` | 004 | openai | `error_behavior` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B004-12` | 004 | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B004-13` | 004 | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B004-14` | 004 | openai | `exact_lookup` | multi_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B004-15` | 004 | openai | `genuine_multi_hop` | multi_document | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B005-02` | 005 | anthropic | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B005-03` | 005 | anthropic | `error_behavior` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B005-04` | 005 | anthropic | `error_behavior` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B005-05` | 005 | anthropic | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B005-07` | 005 | anthropic | `lifecycle_compatibility_migration` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B005-08` | 005 | anthropic | `lifecycle_compatibility_migration` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B005-09` | 005 | openai | `error_behavior` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B005-11` | 005 | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B005-12` | 005 | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B005-14` | 005 | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B005-15` | 005 | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B005-16` | 005 | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B005-17` | 005 | openai | `error_behavior` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B005-18` | 005 | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B005-19` | 005 | openai | `lifecycle_compatibility_migration` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B006-01` | 006 | anthropic | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B006-02` | 006 | anthropic | `error_behavior` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B006-03` | 006 | anthropic | `lifecycle_compatibility_migration` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B006-04` | 006 | anthropic | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B006-05` | 006 | anthropic | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B006-07` | 006 | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B006-08` | 006 | openai | `lifecycle_compatibility_migration` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `GOLD-B006-09` | 006 | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-01` | HA | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-02` | HA | openai | `lifecycle_compatibility_migration` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-03` | HA | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-04` | HA | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-05` | HA | openai | `error_behavior` | multi_span_same_fact | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-06` | HA | openai | `lifecycle_compatibility_migration` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-07` | HA | openai | `exact_lookup` | multi_span_same_fact | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-08` | HA | openai | `error_behavior` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-09` | HA | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-10` | HA | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-11` | HA | openai | `error_behavior` | single_span | **EXPOSED_EVIDENCE_OVERLAP** | OA-003 | OA-003 via D_evidence_overlap: 14 characters shared in ver_f22fbd5c504fa28a4e70440337e4a495 (7367-7497 vs 7225 |
| `HA-12` | HA | openai | `error_behavior` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-13` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-14` | HA | openai | `error_behavior` | multi_span_same_fact | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-15` | HA | openai | `request_response` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-16` | HA | openai | `configuration_interaction` | multi_span_same_fact | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-17` | HA | openai | `request_response` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-18` | HA | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-19` | HA | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-20` | HA | openai | `configuration_interaction` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-21` | HA | openai | `request_response` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-22` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-23` | HA | openai | `request_response` | multi_span_same_fact | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-24` | HA | openai | `request_response` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-25` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-26` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-27` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-28` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-29` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-30` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-31` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-32` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-33` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-34` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-35` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-36` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-37` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-38` | HA | openai | `exact_lookup` | multi_span_same_fact | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-39` | HA | openai | `exact_lookup` | multi_span_same_fact | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-40` | HA | openai | `exact_lookup` | multi_span_same_fact | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-41` | HA | openai | `exact_lookup` | multi_span_same_fact | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-42` | HA | openai | `exact_lookup` | multi_span_same_fact | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-43` | HA | openai | `exact_lookup` | multi_span_same_fact | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-44` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-45` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-46` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-47` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-48` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-49` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-50` | HA | openai | `exact_lookup` | multi_span_same_fact | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-51` | HA | openai | `exact_lookup` | multi_span_same_fact | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-52` | HA | openai | `exact_lookup` | multi_span_same_fact | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-53` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-54` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-55` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-56` | HA | openai | `exact_lookup` | multi_span_same_fact | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-57` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-58` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-59` | HA | openai | `exact_lookup` | multi_span_same_fact | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
| `HA-60` | HA | openai | `exact_lookup` | single_span | **UNEXPOSED** | — | no historical case shares this question, its anchor, an overlapping anchor, or its claim |
