# SYSTEM-J-LOCAL-W20-UNION

NEW development identity. Additive full local-W20 candidate exposure on frozen SYSTEM-H. Written 2026-09-03T04:40:34Z UTC (2026-09-03T00:40:34-04:00 ET). Does **not** overwrite SYSTEM-H / SYSTEM-I / SYSTEM-G / SYSTEM-E. Candidate-generation only. EXP-021A does not run CE or final ranking.

| | |
| --- | --- |
| name | `SYSTEM-J-LOCAL-W20-UNION` |
| **config_hash** | `b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787` |
| file SHA256 | `70acac77f33dbe1f7fc0f2e9b81f8a995c7fd0e9f47bab662f03f12cdecc0fdd` |
| parent SYSTEM-H config_hash | `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` |
| parent SYSTEM-H file SHA256 | `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475` |
| does not overwrite SYSTEM-I config_hash | `9103a51eaaebcbc581df452279ea06c880abb7524053606428dfd77649d4b3d6` |
| status | DEVELOPMENT |
| release | NOT_FROZEN |
| holdout | UNTOUCHED |

`config_hash` is `rag_v1.ids.config_hash` over the `config` object only.

## One change from SYSTEM-H

After the existing parent-local BM25 W=20 lists are computed for every exact SYSTEM-H parent (`parent_version_ids`, PARENT_N=10 cap) using exact E-L10 local-BM25 semantics:

ADD every unique canonical `chunk_id` from every selected parent's existing W=20 list to the candidate union.

New pool = SYSTEM-H existing candidate union UNION all existing parent-local W=20 canonical candidates, deduped by `chunk_id`. Never drop a SYSTEM-H candidate. Exact superset or equal set vs SYSTEM-H for every query. Additive only.

Does **not** include EXP-020A parent-balanced projection top-1. Existing E-L10 global L=10 remains intact. Frozen SYSTEM-H global P=20 projection lane remains exactly unchanged. Does not increase W. Does not run a different BM25 search.

Full W=20 lists were not serialized in EVAL-NATQ-VAL-001 or EXP-020A traces (EXP-020A stored top-1 only). EXP-021A recomputes the existing parent-local BM25 W=20 using exact E-L10 semantics for SYSTEM-H selected parents only.

## Frozen knobs unchanged

L=10, P=20, W=20, PARENT_N=10, SYSTEM-A, E-L10, projection set `ps_v2_ovl_win448_s224`, MiniLM, CE identity (unused in EXP-021A), blend 0.7/0.3 (unused in EXP-021A).

## Do-nots

Do not overwrite SYSTEM-H, SYSTEM-I, SYSTEM-G, SYSTEM-E, `cs_v1_control`, `ps_v2_ovl_win448_s224`. Do not open holdout. Do not run CE/final ranking in EXP-021A. Do not run EXP-020B. Do not increase W/L/P.
