# EXP-021A — FULL LOCAL-W20 CANDIDATE EXPOSURE

**PREREGISTRATION. HASHED BEFORE EXAMINING NEW CANDIDATE RANKS/RESULTS.**

Written 2026-09-03T04:40:34Z UTC (2026-09-03T00:40:34-04:00 ET). ChatGPT-authorized EXP-021A after EXP-020A_SUPPORTED=false. Assignment: `/workspace/NATQ-001-post/EXP-021A-ASSIGNMENT.md`.

Machine-readable twin: `experiments/RAG-V2/EXP-021A/EXP-021A-preregistration.json` sha256 `da8a4b26f216049cdaa2efc5b17fc4ee904e576c95821132dc2ec985cd3bb10f`.

NATQ-001 validation n=40 is **DEVELOPMENT / MODEL-SELECTION DATA**. This is not independent validation. Locked holdout n=60 remains unseen. Do not open `evals/splits/natq-001/holdout.json` or `evals/splits/gold150-v1/holdout.json`.

One mechanism. One variant. One run. Candidate-generation only. No CE. No final ranking. No EXP-020B. Do not overwrite SYSTEM-H / SYSTEM-I / G / E. Do not increase W/L/P. Do not include EXP-020A parent-balanced projection top-1.

---

## Frozen parent (not modified)

| | |
| --- | --- |
| SYSTEM-H-V2-DEV-CANDIDATE config_hash | `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` |
| SYSTEM-H file SHA256 | `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475` |
| SYSTEM-I-PARENT-BALANCED-CANDIDATES config_hash (not modified) | `9103a51eaaebcbc581df452279ea06c880abb7524053606428dfd77649d4b3d6` |
| snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| projection | `ps_v2_ovl_win448_s224` n=18057 |
| validation.jsonl | sha256 `a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6` n=40 |

## New identity

| | |
| --- | --- |
| name | `SYSTEM-J-LOCAL-W20-UNION` |
| config_hash | `b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787` |
| identity file SHA256 | `70acac77f33dbe1f7fc0f2e9b81f8a995c7fd0e9f47bab662f03f12cdecc0fdd` |

## Mechanism (preregistered)

Use the exact SYSTEM-H parent set (`parent_version_ids`: unique `version_id`s among SYSTEM-A fused top-10 hits, PARENT_N=10 cap). Stored EVAL-NATQ-VAL-001 parent lists are reused after an identical recomputation check. Full SYSTEM-H union member ids were not serialized; recompute SYSTEM-H candidate generation only (no CE) identically and check stored C_P / e_pool_size / parents.

SYSTEM-H already computes up to W=20 local-BM25 canonical candidates inside every selected parent via `local_bm25_per_parent_batched` (cs_v1_control, full-corpus IDF, same tokenizer, W=20, `round(score,9) DESC` then `chunk_id ASC`). Full W=20 lists were not serialized in EVAL-NATQ-VAL-001 or EXP-020A (EXP-020A stored top-1 only), so they are recomputed with identical E-L10 semantics for SYSTEM-H selected parents only. Do not increase W.

After those existing parent-local W=20 lists are computed:

New pool = SYSTEM-H existing candidate union UNION all unique canonical chunk_ids from every selected parent's existing W=20 list.

Deduplicate by canonical chunk_id. Additive only. Never remove SYSTEM-H candidates. Exact superset or equal set vs SYSTEM-H for every query.

Keep E-L10 global L=10 intact. Keep frozen SYSTEM-H global P=20 projection lane unchanged. Do **not** include EXP-020A parent-balanced projection top-1.

## PRIMARY

candidate full-case Recall@pool. Baseline **34/40**.

## SECONDARY

- candidate gold-span micro recall, baseline **46/53**
- candidate recall by provider
- multi-span all-gold-in-pool ceiling
- mean / median / p95 pool size
- mean / median number of W20 additions after deduplication
- candidate-generation latency
- distribution of parent counts
- fraction of new union contributed by local W20
- exact superset check against SYSTEM-H
- pool growth (baseline mean, SYSTEM-J mean, absolute / percent / largest per-query increase, estimated CE pairs if full union were reranked; do **not** run CE)

## Gate (do not change after seeing results)

`EXP-021A_SUPPORTED` iff ALL:

1. candidate full-case recall >= 36/40
2. candidate span recall > 46/53
3. every original SYSTEM-H candidate remains present
4. no integrity/provenance failure

The gate remains the original engineering candidate threshold. Do not change it. Diagnostic expectation ~37/40 and 50/53 from exposed development ranks is **NOT** a gate and **NOT** an unseen-performance prediction. Report actuals independently. Do not reject support solely because pool grows; report growth clearly.

## Diagnostics (after aggregates only)

For the seven previously missing gold spans from NATQ-DIAG-001 (the complete set of SYSTEM-H union misses on this split): recovered yes/no; local BM25 rank; whether covering canonical entered SYSTEM-J; resulting candidate position if one is defined. Also inspect ALL 40 cases for newly recovered gold. Diagnostic only. No named-case handling.

## Holdout

Before and after: NATQ access log 0 bytes sha `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. V1 log 235 bytes sha `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`.

## STOP

Do not run final ranking. Do not run EXP-020B. Do not run CE. Do not run another variant. Return to coordinator ChatGPT.
