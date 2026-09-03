# EXP-020A — PARENT-BALANCED WITHIN-DOCUMENT CANDIDATE GENERATION

**PREREGISTRATION. HASHED BEFORE EXAMINING NEW CANDIDATE RANKS/RESULTS.**

Written 2026-09-03T04:26:51Z UTC (2026-09-03T00:26:51-04:00 ET). ChatGPT-authorized EXP-020A after NATQ-DIAG-001. Assignment: `/workspace/NATQ-001-post/EXP-020A-ASSIGNMENT.md`.

Machine-readable twin: `experiments/RAG-V2/EXP-020A/EXP-020A-preregistration.json` sha256 `f0501380ff0a44526eb8b1646b90eb28129a4ba9f37a04521c85cc03399d8dfc`.

NATQ-001 validation n=40 is **DEVELOPMENT / MODEL-SELECTION DATA**. This is not independent validation. Locked holdout n=60 remains unseen. Do not open `evals/splits/natq-001/holdout.json` or `evals/splits/gold150-v1/holdout.json`.

One mechanism. One variant. One run. Candidate-generation only. No CE. No final ranking. No EXP-020B. Do not overwrite SYSTEM-H / G / E.

---

## Frozen parent (not modified)

| | |
| --- | --- |
| SYSTEM-H-V2-DEV-CANDIDATE config_hash | `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` |
| SYSTEM-H file SHA256 | `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475` |
| snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| projection | `ps_v2_ovl_win448_s224` n=18057 |
| validation.jsonl | sha256 `a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6` n=40 |

## New identity

| | |
| --- | --- |
| name | `SYSTEM-I-PARENT-BALANCED-CANDIDATES` |
| config_hash | `9103a51eaaebcbc581df452279ea06c880abb7524053606428dfd77649d4b3d6` |
| identity file SHA256 | `63a78f1d88876c3f55033dc13ce3e6bad1fe768ce5252d315f31652769a9fd19` |

## Mechanism (preregistered)

Use the exact SYSTEM-H parent set (`parent_version_ids`: unique `version_id`s among SYSTEM-A fused top-10 hits, PARENT_N=10 cap). Stored EVAL-NATQ-VAL-001 parent lists are reused after an identical recomputation check. Full SYSTEM-H union member ids were not serialized; recompute SYSTEM-H candidate generation only (no CE) identically and check stored C_P / e_pool_size / parents.

For each parent:

**A. Lexical.** TOP 1 canonical from existing E-L10 local-BM25 lists (`local_bm25_per_parent_batched`, full-corpus IDF, same tokenizer, `round(score,9) DESC` then `chunk_id ASC`). Do not alter L=10.

**B. Projection.** Restrict existing globally scored `projection_rrf` hits to that parent. Apply exact `map_to_canonical_extras` unique-canonical ranking. Take k=1. Do not alter global P=20. Do not recompute parent-local RRF.

New pool = SYSTEM-H union UNION A UNION B, dedupe `chunk_id`. Never remove a SYSTEM-H candidate. Max <=20 extras before dedup.

### Projection multi-cover mapping (STOP-condition resolution)

Existing `map_to_canonical_extras` **can** emit multiple canonical chunks from one projection result: it writes every `covering_chunk_id` into a unique-canonical score table. Frozen set: **12687/18057** projections have `covering_n>1` (max 24).

The assignment said to STOP rather than invent a new rule. EXP-020A does **not** invent an overlap heuristic and does **not** emit all covers of a single top-1 projection. It reuses the existing unique-canonical ranking (`-best_fused`, then `chunk_id`) with **k=1 per parent**. That is the frozen mapping rule, not a new one.

## PRIMARY

candidate full-case Recall@pool. Baseline **34/40**.

## SECONDARY

- candidate gold-span micro recall, baseline **46/53**
- recovered candidate-generation cases
- recovered missing spans (all 40 cases)
- mean/median pool size
- mean added candidates
- lexical-vs-projection contribution
- per-provider candidate recall
- multi-span candidate ceiling
- candidate-generation latency

## Gate (do not lower after seeing results)

`EXP-020A_SUPPORTED` iff ALL:

1. candidate full-case recall >= 36/40
2. candidate span recall > 46/53
3. every original SYSTEM-H candidate remains present
4. no integrity/provenance failure

Report descriptively even if the gate fails.

## Diagnostics (after aggregates only)

For the seven previously missing gold spans from NATQ-DIAG-001 (the complete set of SYSTEM-H union misses on this split): recovered? BM25 / projection / both / neither; new pool position if meaningful. Diagnostic only. No named-case handling.

## Holdout

Before and after: NATQ access log 0 bytes sha `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. V1 log 235 bytes sha `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`.

## STOP

Do not run final ranking. Do not run EXP-020B. Do not run CE. Return to coordinator ChatGPT.
