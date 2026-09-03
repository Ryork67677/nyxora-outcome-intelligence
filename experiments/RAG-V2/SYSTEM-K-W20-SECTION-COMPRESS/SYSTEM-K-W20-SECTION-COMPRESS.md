# SYSTEM-K-W20-SECTION-COMPRESS

NEW development identity. Frozen SYSTEM-H candidate pool PLUS a deterministic two-pass section-stratified compressed subset of SYSTEM-J W20-only extras (`EXTRA_BUDGET=30`). Written 2026-09-03T04:57:46Z UTC (2026-09-03T00:57:46-04:00 ET). Does **not** overwrite SYSTEM-H / SYSTEM-I / SYSTEM-J / SYSTEM-G / SYSTEM-E. Candidate-generation / compression only. EXP-021B does not run CE or final ranking.

| | |
| --- | --- |
| name | `SYSTEM-K-W20-SECTION-COMPRESS` |
| **config_hash** | `eef589c085ea7e88fdc729d83021b311e2927310fc6368b54a87f374859bdec8` |
| file SHA256 | `20d967e2f56fed88f617d1c18474abc86b9f984f32a30cc195f42d6fef03ad7e` |
| parent SYSTEM-H config_hash | `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` |
| parent SYSTEM-H file SHA256 | `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475` |
| parent SYSTEM-J config_hash | `b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787` |
| parent SYSTEM-J file SHA256 | `70acac77f33dbe1f7fc0f2e9b81f8a995c7fd0e9f47bab662f03f12cdecc0fdd` |
| does not overwrite SYSTEM-I config_hash | `9103a51eaaebcbc581df452279ea06c880abb7524053606428dfd77649d4b3d6` |
| status | DEVELOPMENT |
| DEVELOPMENT_ARCHITECTURE_FROZEN | false |
| RELEASE_FROZEN | false |
| extra_budget | 30 |
| holdout | UNTOUCHED |

`config_hash` is `rag_v1.ids.config_hash` over the `config` object only.

## One change from SYSTEM-J

Keep every frozen SYSTEM-H candidate (never removed; preserve H order). Compress SYSTEM-J's W20-only extras (`J minus H`, processed in stored `added_w20` order) with a two-pass section-stratified algorithm:

- `EXTRA_BUDGET = 30` extras/query maximum.
- Group extras by `(version_id, section_path)` from `cs_v1_control`. Canonical section key is `json.dumps(section_path, ensure_ascii=True, separators=(',', ':'))`.
- Within each group order by local BM25 raw score DESC, local BM25 rank ASC, canonical `chunk_id` ASC.
- Pass 1 (section coverage): take the best candidate from every group; rank those representatives globally by local BM25 raw score DESC, parent rank ASC, local BM25 rank ASC, `version_id` ASC, section_path ASC (canonical JSON string), canonical `chunk_id` ASC; add until budget exhausted.
- Pass 2 (limited same-section depth): if budget remains, take the second-best from each group with the same global keys; add until 30; never take a third from a section.

Therefore: max two W20-only additions per `(version_id, section_path)` AND max 30 total W20-only additions/query. No learned weights. No MMR lambda. No tuning.

SYSTEM-K pool = H (all) then selected extras in selection order (Pass 1 then Pass 2). Dedup by `chunk_id`. Exact SYSTEM-H superset on every query.

Does **not** include EXP-020A parent-balanced projection top-1. Does not increase W/L/P. Does not re-run SYSTEM-A or projection for the K pool itself. Local BM25 W=20 recompute is score-association + identity check of stored `w20_by_parent` only.

## Frozen knobs unchanged

L=10, P=20, W=20, PARENT_N=10, SYSTEM-A, E-L10, projection set `ps_v2_ovl_win448_s224`, MiniLM, CE identity (unused in EXP-021B), blend 0.7/0.3 (unused in EXP-021B). Inherited SYSTEM-J `local_w20_union = true`.

## Do-nots

Do not overwrite SYSTEM-H, SYSTEM-I, SYSTEM-J, SYSTEM-G, SYSTEM-E, `cs_v1_control`, `ps_v2_ovl_win448_s224`. Do not open holdout. Do not run CE/final ranking in EXP-021B. Do not increase W/L/P. Do not change EXTRA_BUDGET after seeing results. Do not freeze as a release.
