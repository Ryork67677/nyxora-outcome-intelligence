# SYSTEM-I-PARENT-BALANCED-CANDIDATES

NEW development identity. Additive parent-balanced within-document candidate generation on frozen SYSTEM-H. Written 2026-09-03T04:26:51Z UTC (2026-09-03T00:26:51-04:00 ET). Does **not** overwrite SYSTEM-H / SYSTEM-G / SYSTEM-E. Candidate-generation only. EXP-020A does not run CE or final ranking.

| | |
| --- | --- |
| name | `SYSTEM-I-PARENT-BALANCED-CANDIDATES` |
| **config_hash** | `9103a51eaaebcbc581df452279ea06c880abb7524053606428dfd77649d4b3d6` |
| file SHA256 | `63a78f1d88876c3f55033dc13ce3e6bad1fe768ce5252d315f31652769a9fd19` |
| parent SYSTEM-H config_hash | `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` |
| parent SYSTEM-H file SHA256 | `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475` |
| status | DEVELOPMENT |
| release | NOT_FROZEN |
| holdout | UNTOUCHED |

`config_hash` is `rag_v1.ids.config_hash` over the `config` object only.

## One change from SYSTEM-H

For each exact SYSTEM-H parent `version_id` (existing `parent_version_ids`, PARENT_N=10 cap):

- TOP 1 canonical local-BM25 candidate using exact E-L10 local-BM25 semantics (do not alter L=10).
- TOP 1 unique canonical from existing EXP-017 `map_to_canonical_extras` ranking over globally scored `projection_rrf` hits restricted to that parent (do not alter global P=20).

New pool = SYSTEM-H union UNION those contributions, deduped by `chunk_id`. Never drop a SYSTEM-H candidate. Max <=20 extras before dedup.

## Multi-cover mapping (not a new rule)

Existing `map_to_canonical_extras` assigns each projection's fused score to **every** `covering_chunk_id`, then ranks unique canonicals by `(-best_fused, chunk_id)`. Frozen projection set `ps_v2_ovl_win448_s224`: 12687/18057 windows have `covering_n>1` (max 24). EXP-020A takes that existing unique-canonical ranking with k=1 per parent. It does not emit all covers of one projection, and it does not invent an overlap heuristic.

## Frozen knobs unchanged

L=10, P=20, W=20, PARENT_N=10, SYSTEM-A, E-L10, projection set, MiniLM, CE identity (unused in EXP-020A), blend 0.7/0.3 (unused in EXP-020A).

## Do-nots

Do not overwrite SYSTEM-H, SYSTEM-G, SYSTEM-E, `cs_v1_control`, `ps_v2_ovl_win448_s224`. Do not open holdout. Do not run EXP-020B. Do not run CE/final ranking in EXP-020A.
