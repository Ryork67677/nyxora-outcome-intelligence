# EXP-021A — FULL LOCAL-W20 CANDIDATE EXPOSURE

**EXP-021A_SUPPORTED = TRUE**

Candidate-generation only on NATQ-001 validation n=40, now DEVELOPMENT / MODEL-SELECTION DATA. Not independent validation. Holdout was not opened. SYSTEM-H / SYSTEM-I / G / E were not modified. CE and final ranking were not run. EXP-020B was not run. W/L/P were not increased. EXP-020A parent-balanced projection was not included.

## Setup

- Preregistration sha256 `da8a4b26f216049cdaa2efc5b17fc4ee904e576c95821132dc2ec985cd3bb10f` hashed before examining new candidate ranks.
- SYSTEM-J-LOCAL-W20-UNION config_hash `b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787` (file sha256 `70acac77f33dbe1f7fc0f2e9b81f8a995c7fd0e9f47bab662f03f12cdecc0fdd`).
- Parent SYSTEM-H config_hash `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` unchanged after run: **True**.
- SYSTEM-I config_hash `9103a51eaaebcbc581df452279ea06c880abb7524053606428dfd77649d4b3d6` unchanged after run: **True**.
- Split: `evals/splits/natq-001/validation.jsonl` n=40, sha256 `a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6`.
- Snapshot `snap_689e336380a054d8039dc35b2c09cd0a`. Projection `ps_v2_ovl_win448_s224` n=18057.
- Recomputed SYSTEM-H candidate generation matched stored parents, C_P, e_pool_size, union size, and in_pool flags.
- Parent-local BM25 W=20 lists recomputed with exact E-L10 semantics (not serialized in stored traces; EXP-020A stored top-1 only).
- NATQ holdout-access log after: 0 bytes, sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- V1 holdout-access log after: 235 bytes, sha256 `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`.
- holdout_json_opened: **false**. v1_holdout_json_opened: **false**.

## PRIMARY — candidate full-case Recall@pool

| metric | SYSTEM-H baseline | SYSTEM-J |
| --- | ---: | ---: |
| candidate full-case Recall@pool | 34/40 | **37/40** |

## SECONDARY

| metric | SYSTEM-H baseline | SYSTEM-J |
| --- | ---: | ---: |
| candidate span micro | 46/53 | **50/53** |
| recovered CG cases | — | 3 |
| recovered missing spans | — | 4 |
| mean pool size | 118.83 | 187.12 |
| median pool size | 119.5 | 186.0 |
| p95 pool size | 127.1 | 249.35 |
| mean / median W20 additions after dedup | — | 68.3 / 66.0 |
| mean fraction of union from local W20 (incl. overlap) | — | 0.5743 |
| mean fraction of union that is W20-only additions | — | 0.3446 |
| exact superset vs SYSTEM-H | — | True |
| candidate-gen latency mean ms | 1314.6 | 1301.0 (Δ -13.6) |
| W20-union selection mean ms | — | 0.2 |

### Pool growth

| | |
| --- | ---: |
| baseline SYSTEM-H mean pool | 118.83 |
| SYSTEM-J mean pool | 187.12 |
| absolute increase | 68.29 |
| percentage increase | 57.47% |
| largest per-query increase | 139 |
| estimated CE pairs if full union reranked | 7485 |
| estimated CE pairs SYSTEM-H baseline | 4753 |
| estimated CE pairs increase | 2732 |

CE was **not** run. The CE-pair estimate is `sum(pool_size)` over 40 queries.

### Per-provider candidate recall

| provider | baseline case | SYSTEM-J case | baseline span | SYSTEM-J span |
| --- | ---: | ---: | ---: | ---: |
| openai | 15/18 | 17/18 | 20/23 | 22/23 |
| anthropic | 19/22 | 20/22 | 26/30 | 28/30 |

### Multi-span candidate ceiling

Subset n=12 (n_gold_spans>1 or tag multi_span). SYSTEM-H all-gold-in-pool **8/12**. SYSTEM-J **10/12**.

### Parent-count distribution

`{3: 2, 4: 7, 5: 8, 6: 8, 7: 5, 8: 6, 9: 4}` (mean 6.03).

## Diagnostics — seven previously missing gold spans (after aggregates)

Identities are the complete set of SYSTEM-H union misses on this split (NATQ-DIAG-001). Diagnostic only. No named-case handling.

| case | span | recovered | local-BM25 rank | covering canonical entered SYSTEM-J | candidate position |
| --- | ---: | --- | ---: | --- | ---: |
| `NATQ-C-004` | 0 | True | 18 | True | 139 |
| `NATQ-C-005` | 1 | True | 13 | True | 126 |
| `NATQ-C-014` | 1 | False | not in W=20 list | False | None |
| `NATQ-C-179` | 0 | False | not in W=20 list | False | None |
| `NATQ-C-044` | 0 | True | 11 | True | 146 |
| `NATQ-C-044` | 1 | True | 5 | True | 140 |
| `NATQ-C-026` | 1 | False | not in W=20 list | False | None |

Recoveries across ALL 40 cases: **4** span(s) in **3** case(s). SYSTEM-H missing span count was 7; still missing after SYSTEM-J: 3.

## Gate

| condition | result |
| --- | --- |
| candidate full-case recall >= 36/40 (37/40) | True |
| candidate span recall > 46/53 (50/53) | True |
| every original SYSTEM-H candidate remains present | True |
| no integrity/provenance failure | True |

**EXP-021A_SUPPORTED = TRUE**

## Interpretation

Existing parent-local BM25 has useful recall that the current global candidate promotion discards.

Do **not** conclude the resulting full pool is release-ready. The next experiment should separately address efficient / coverage-aware compression and final top-10 selection before running CE.

## STOP

Stop after EXP-021A. Do **not** run final ranking. Do **not** run EXP-020B. Do **not** run CE. Do **not** open holdout. Do **not** run another variant.
