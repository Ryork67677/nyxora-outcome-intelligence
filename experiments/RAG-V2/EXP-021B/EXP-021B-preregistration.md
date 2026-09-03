# EXP-021B — SECTION-STRATIFIED LOCAL-W20 COMPRESSION

**PREREGISTRATION. HASHED BEFORE COMPUTING ANY SYSTEM-K AGGREGATE CANDIDATE METRICS.**

Written 2026-09-03T04:58:28Z UTC (2026-09-03T00:58:28-04:00 ET). ChatGPT-authorized EXP-021B after EXP-021A_SUPPORTED=true. Assignment: `/workspace/NATQ-001-post/EXP-021B-ASSIGNMENT.md`.

Machine-readable twin: `experiments/RAG-V2/EXP-021B/EXP-021B-preregistration.json` sha256 `f5cfb249f76e9fbb68230ae034bb9ccdab173354482caf71c8b3cc0d1893fb3e`.

NATQ-001 validation n=40 is **DEVELOPMENT / MODEL-SELECTION DATA**. This is not independent validation. Locked holdout n=60 remains unseen. Do not open `evals/splits/natq-001/holdout.json` or `evals/splits/gold150-v1/holdout.json`.

One mechanism. One variant. One run. Candidate-generation / compression only. No CE. No final ranking. No blend. No coverage selector. No MMR. No answer generation. Do not overwrite SYSTEM-H / SYSTEM-I / SYSTEM-J / G / E. Do not increase W/L/P. Do not include EXP-020A parent-balanced projection. Do not change EXTRA_BUDGET after seeing results. Do not try another budget.

---

## Frozen parents (not modified)

| | |
| --- | --- |
| SYSTEM-H-V2-DEV-CANDIDATE config_hash | `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` |
| SYSTEM-H file SHA256 | `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475` |
| SYSTEM-J-LOCAL-W20-UNION config_hash | `b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787` |
| SYSTEM-J file SHA256 | `70acac77f33dbe1f7fc0f2e9b81f8a995c7fd0e9f47bab662f03f12cdecc0fdd` |
| SYSTEM-I-PARENT-BALANCED-CANDIDATES config_hash (not modified) | `9103a51eaaebcbc581df452279ea06c880abb7524053606428dfd77649d4b3d6` |
| snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| projection | `ps_v2_ovl_win448_s224` n=18057 |
| validation.jsonl | sha256 `a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6` n=40 |
| stored pools | `experiments/RAG-V2/EXP-021A/logs/EXP-021A-pools.jsonl` |

## New identity

| | |
| --- | --- |
| name | `SYSTEM-K-W20-SECTION-COMPRESS` |
| config_hash | `eef589c085ea7e88fdc729d83021b311e2927310fc6368b54a87f374859bdec8` |
| identity file SHA256 | `20d967e2f56fed88f617d1c18474abc86b9f984f32a30cc195f42d6fef03ad7e` |
| EXTRA_BUDGET | 30 |

## Mechanism (preregistered)

For each of 40 validation cases from stored EXP-021A-pools.jsonl:

- H = exact stored `system_h_union_ids` (list, preserve order)
- J = exact stored `system_j_union_ids`
- EXTRAS = J minus H as sets; process extras in stored `added_w20` order as the J-H list (must equal J-H)
- Parents = stored parents list; parent_rank is 1-based index in that list

Attach to every EXTRA (do not run a NEW retrieval model; do not increase W): parent `version_id`, parent rank used by SYSTEM-H, `section_path` from control chunks (`cs_v1_control`), parent-local BM25 raw score, parent-local BM25 rank, canonical `chunk_id`.

Score/rank association: recompute `local_bm25_per_parent_batched(query, parents, W=20)` with exact E-L10 semantics used in EXP-021A, ONLY to attach scores to already-known W20 ids. VERIFY that for every parent, `[h.chunk_id for h in hits]` EXACTLY equals stored `w20_by_parent[vid]`. If any mismatch, STOP. This is identity check of existing W20, not a new model.

If a chunk appears in multiple parent W20 lists, associate the extra with the FIRST parent in SYSTEM-H parent order that listed it (same first-seen as EXP-021A `added_w20`). Group `version_id` is that parent. Confirm `chunk.version_id == that parent` (STOP if not).

GROUP EXTRAS by `(version_id, section_path)`. Canonical section key: `json.dumps(section_path if already list else list(section_path), ensure_ascii=True, separators=(',', ':'))`.

Within each group order by: (1) local BM25 raw score DESC (2) local BM25 rank ASC (3) canonical chunk_id ASC.

**PASS 1 — SECTION COVERAGE:** Take the best candidate from every group. Rank those group representatives globally by: (1) local BM25 raw score DESC (2) parent rank ASC (3) local BM25 rank ASC (4) version_id ASC (5) section_path ASC (canonical JSON string) (6) canonical chunk_id ASC. Add until EXTRA_BUDGET=30 exhausted or none remain.

**PASS 2 — LIMITED SAME-SECTION DEPTH:** If budget remains, take the second-best candidate, if any, from each group. Order with the EXACT same global deterministic keys as Pass 1. Add until EXTRA_BUDGET=30 reached. Do NOT take a third candidate from a section.

Therefore: max two W20-only additions per `(version_id, section_path)` AND max 30 total W20-only additions/query. No learned weights. No MMR lambda. No tuning.

SYSTEM-K pool = H (all, never removed, preserve H order) then selected extras in selection order (Pass 1 then Pass 2). Dedup by chunk_id. Assert set(H) ⊆ set(K) for every query. Assert len(selected extras) ≤ 30. Assert no third from same group.

Do NOT re-run SYSTEM-A or projection for the K pool itself. Use stored H/J ids. BM25 recompute is score-association + identity check only.

## PRIMARY

candidate full-case Recall@pool. Baseline SYSTEM-H **34/40**. Baseline SYSTEM-J **37/40**.

## SECONDARY

- candidate span Recall@pool, H **46/53**, J **50/53**
- multi-span all-gold-in-pool (same 12-case definition as EXP-021A: n_gold_spans>1 or tag multi_span)
- OpenAI and Anthropic candidate recall (case and span)
- mean / median / p95 pool size
- mean / median additions (K extras selected)
- compression ratio vs SYSTEM-J (mean_K / mean_J and 1 - that)
- candidate-generation latency (compression selection; inherited J cg 1301.0 ms; K = J cg + compression; W20 score-association recompute separately; estimated CE pairs = sum(pool_size); CE was NOT run)
- exact SYSTEM-H superset check

## Gate (do not change after seeing results)

`EXP-021B_SUPPORTED` iff ALL:

1. candidate full-case Recall@pool >= 36/40
2. candidate span Recall@pool >= 49/53
3. mean candidate pool <= 150
4. SYSTEM-K contains every SYSTEM-H candidate on every query
5. no benchmark-integrity or provenance failure

Do NOT change these thresholds after seeing results. Do NOT change EXTRA_BUDGET after seeing results. Do NOT try another budget.

## Diagnostics (after aggregates only)

Four SYSTEM-J recovered spans: NATQ-C-004 s0, NATQ-C-005 s1, NATQ-C-044 s0, NATQ-C-044 s1.

For each: retained by SYSTEM-K yes/no; group section_path; local BM25 rank; compression pass selected in (1/2/none); compressed candidate position.

Diagnostic only. No named-case rule. Also report all newly lost or newly retained gold spans across all 40 vs SYSTEM-J (K vs J membership). Do NOT increase W or chase NATQ-C-014 s1, NATQ-C-179 s0, NATQ-C-026 s1.

## Environment

Record environment again. Known current drift: PostgreSQL 16.15 / pgvector 0.8.6 versus historical PostgreSQL 16.13 / pgvector 0.6.0. The reconstructed candidate baseline has remained exact so far, but preserve this as an explicit reproducibility note. Do not silently treat environments as identical.

## Holdout

Before and after: NATQ access log 0 bytes sha `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. V1 log 235 bytes sha `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`. Neither holdout.json may be opened.

## STOP

Do not run CE. Do not run final ranking. Do not try another budget. Do not alter the 30-candidate budget after results. Return to coordinator ChatGPT.
