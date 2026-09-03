# EXP-020A — PARENT-BALANCED WITHIN-DOCUMENT CANDIDATE GENERATION

**EXP-020A_SUPPORTED = FALSE**

Candidate-generation only on NATQ-001 validation n=40, now DEVELOPMENT / MODEL-SELECTION DATA. Not independent validation. Holdout was not opened. SYSTEM-H / G / E were not modified. CE and final ranking were not run. EXP-020B was not run.

## Setup

- Preregistration sha256 `f0501380ff0a44526eb8b1646b90eb28129a4ba9f37a04521c85cc03399d8dfc` hashed before examining new candidate ranks.
- SYSTEM-I-PARENT-BALANCED-CANDIDATES config_hash `9103a51eaaebcbc581df452279ea06c880abb7524053606428dfd77649d4b3d6` (file sha256 `63a78f1d88876c3f55033dc13ce3e6bad1fe768ce5252d315f31652769a9fd19`).
- Parent SYSTEM-H config_hash `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` unchanged after run: **True**.
- Split: `evals/splits/natq-001/validation.jsonl` n=40, sha256 `a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6`.
- Snapshot `snap_689e336380a054d8039dc35b2c09cd0a`. Projection `ps_v2_ovl_win448_s224` n=18057.
- Recomputed SYSTEM-H candidate generation matched stored parents, C_P, e_pool_size, union size, and in_pool flags.
- NATQ holdout-access log after: 0 bytes, sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- V1 holdout-access log after: 235 bytes, sha256 `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`.
- holdout_json_opened: **false**. v1_holdout_json_opened: **false**.

## PRIMARY — candidate full-case Recall@pool

| metric | SYSTEM-H baseline | SYSTEM-I |
| --- | ---: | ---: |
| candidate full-case Recall@pool | 34/40 | **34/40** |

## SECONDARY

| metric | SYSTEM-H baseline | SYSTEM-I |
| --- | ---: | ---: |
| candidate span micro | 46/53 | **46/53** |
| recovered CG cases | — | 0 |
| recovered missing spans | — | 0 |
| mean pool size | 118.83 | 120.3 |
| median pool size | 119.5 | 121.5 |
| mean added candidates | — | 1.475 |
| mean added BM25 / projection | — | 0.05 / 1.425 |
| candidate-gen latency mean ms | 1314.6 | 1314.0 (Δ -0.6) |
| parent-balanced selection mean ms | — | 0.2 |

### Lexical vs projection contribution (recovered spans)

| lane | recovered spans |
| --- | ---: |
| BM25 only | 0 |
| projection only | 0 |
| both | 0 |
| neither | 0 |

### Per-provider candidate recall

| provider | baseline case | SYSTEM-I case | baseline span | SYSTEM-I span |
| --- | ---: | ---: | ---: | ---: |
| openai | 15/18 | 15/18 | 20/23 | 20/23 |
| anthropic | 19/22 | 19/22 | 26/30 | 26/30 |

### Multi-span candidate ceiling

Subset n=12 (n_gold_spans>1 or tag multi_span). SYSTEM-H all-gold-in-pool **8/12**. SYSTEM-I **8/12**.

## Diagnostics — seven previously missing gold spans (after aggregates)

Identities are the complete set of SYSTEM-H union misses on this split (NATQ-DIAG-001). Diagnostic only. No named-case handling.

| case | span | recovered | by | new pool position | local-BM25 rank in parent |
| --- | ---: | --- | --- | ---: | --- |
| `NATQ-C-004` | 0 | False | neither (not recovered) | None | 18 |
| `NATQ-C-005` | 1 | False | neither (not recovered) | None | 13 |
| `NATQ-C-014` | 1 | False | neither (not recovered) | None | not in W=20 list |
| `NATQ-C-179` | 0 | False | neither (not recovered) | None | not in W=20 list |
| `NATQ-C-044` | 0 | False | neither (not recovered) | None | 11 |
| `NATQ-C-044` | 1 | False | neither (not recovered) | None | 5 |
| `NATQ-C-026` | 1 | False | neither (not recovered) | None | not in W=20 list |

Recoveries across ALL 40 cases: **0** span(s) in **0** case(s). SYSTEM-H missing span count was 7; still missing after SYSTEM-I: 7.

## Gate

| condition | result |
| --- | --- |
| candidate full-case recall >= 36/40 (34/40) | False |
| candidate span recall > 46/53 (46/53) | False |
| every original SYSTEM-H candidate remains present | True |
| no integrity/provenance failure | True |

**EXP-020A_SUPPORTED = FALSE**

## STOP

Stop after EXP-020A. Do **not** run final ranking. Do **not** run EXP-020B. Do **not** run CE. Do **not** open holdout.
