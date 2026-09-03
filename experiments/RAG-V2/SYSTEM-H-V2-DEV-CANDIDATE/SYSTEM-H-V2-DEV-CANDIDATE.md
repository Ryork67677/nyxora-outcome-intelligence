# SYSTEM-H-V2-DEV-CANDIDATE

Immutable **DEVELOPMENT architecture** identity freeze of exactly **SYSTEM-G candidate generation + EXP-019A projection-aware prior + PERF-003 D1 CE path**.

Written 2026-09-01T05:51:33Z UTC (2026-09-01T01:51:33-04:00 ET). ChatGPT-accepted PERF-003_SUPPORTED ~01:48 ET 2026-09-01. No holdout. No validation. **NOT a release freeze.** **Does not overwrite SYSTEM-G or SYSTEM-G-CE-D1.**

| | |
| --- | --- |
| name | `SYSTEM-H-V2-DEV-CANDIDATE` |
| **config_hash** | `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` |
| file SHA256 | `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475` |
| status | **DEVELOPMENT** / **DEVELOPMENT_ARCHITECTURE_FROZEN** |
| release | **NOT_FROZEN** (`RELEASE_FROZEN=false`) |
| validation | **NOT_RUN** / **NOT independently validated** |
| holdout | **UNTOUCHED** (`NEW_HOLDOUT_RUN=false`) |
| V2-DEVSET-001 | **CLOSED for architecture changes** |

`config_hash` is `rag_v1.ids.config_hash` over the `config` object only. Observed metrics are **excluded** from the hashed dict (`observed_metrics_DEVELOPMENT_ONLY`). Keep config_hash distinct from file SHA256.

Hashed `config` starts from `SYSTEM-G-CE-D1.json`'s `config`, then `name=SYSTEM-H-V2-DEV-CANDIDATE`, `parent_system_g_ce_d1=6d108568f3131bad87d8617f5c2fb88ea14428e397d59ff54ff8e11cc4647b7d`, and `one_change_from_G_CE_D1` = identity freeze of the PERF-003 D1 V2 path as the development architecture candidate; no ranking/quality change.

This file does **not** overwrite:

- `experiments/EXP-019A/SYSTEM-G-PROJECTION-PRIOR.json` (config_hash `563a7b790564fa1efb96257e988c4b1ccfab45146825d2a366b2fee0ca5d5790`, file SHA256 `7f4ff6db09f32e55cac820cbc00d87ce2ae91886d444c3bad20ac3e04c7f0f61`)
- `experiments/PERF-003/SYSTEM-G-CE-D1.json` (config_hash `6d108568f3131bad87d8617f5c2fb88ea14428e397d59ff54ff8e11cc4647b7d`, file SHA256 `cf0c985c5f7738e7fc5422039fd6940621d8dcd8f91de41abe3784ac53a6a7ec`; protocol expected `cf0c985c5f7738e7fc5422039fd6940621d8dcd8f91de41abe3784ac53a6a7ec`; match=True)
- `experiments/EXP-017/SYSTEM-F-PROJECTION.json` (config_hash `83ba5f2e834ecdffbfe4fb554cf84860ad35cf7010e9764e5cdea9e38598f678`, file SHA256 `e68d8c7a5782420bfd63cc57882ce96eacd5d919ac6197d271b9e11e399c3ff5`)
- `experiments/EXP-018B/SYSTEM-E-L10-WITHIN-DOC.json` (config_hash `bae1c05b5c47c179dc5cd7972a14bd23d102a4d513b674667eb469e17cd85e89`, file SHA256 `efbd3bc1cc73d3c342a607ef75135515d13680b31fd6058e8f1c13e80d13ed89`)
- `experiments/EXP-018/SYSTEM-E-WITHIN-DOC.json` (config_hash `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe`, file SHA256 `e228616beee1bcb13855c2eadee9fc20ec1fae3e54c77b28587114568c64d087`)
- SYSTEM-D (`SYSTEM-D-GUARD.json` / `SYSTEM-D-RELEASE.json`)
- `cs_v1_control`
- projection set `ps_v2_ovl_win448_s224` (n=18057, config_hash `7fd5034c9510a1e08ec76bd22b020703c586dd12e7c02659397df05c5c365a8e`)

## Parent / provenance

| identity | hash |
| --- | --- |
| SYSTEM-A | `9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38` |
| SYSTEM-D | `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a` |
| SYSTEM-E uncapped parent | `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe` |
| SYSTEM-E-L10-WITHIN-DOC | `bae1c05b5c47c179dc5cd7972a14bd23d102a4d513b674667eb469e17cd85e89` |
| SYSTEM-F-PROJECTION | `83ba5f2e834ecdffbfe4fb554cf84860ad35cf7010e9764e5cdea9e38598f678` |
| SYSTEM-F-PROJECTION file SHA256 | `e68d8c7a5782420bfd63cc57882ce96eacd5d919ac6197d271b9e11e399c3ff5` |
| SYSTEM-G-PROJECTION-PRIOR | `563a7b790564fa1efb96257e988c4b1ccfab45146825d2a366b2fee0ca5d5790` |
| SYSTEM-G-PROJECTION-PRIOR file SHA256 | `7f4ff6db09f32e55cac820cbc00d87ce2ae91886d444c3bad20ac3e04c7f0f61` |
| SYSTEM-G-CE-D1 | `6d108568f3131bad87d8617f5c2fb88ea14428e397d59ff54ff8e11cc4647b7d` |
| SYSTEM-G-CE-D1 file SHA256 | `cf0c985c5f7738e7fc5422039fd6940621d8dcd8f91de41abe3784ac53a6a7ec` |
| EXP-017 prereg json sha256 | `053a6bf14df088ca9e2283bc3e8dfb0769848a48c54c51a77fbe045795a80cc6` |
| EXP-019A prereg json sha256 | `f14001eff07b63c7916d7e27567d15ccd1e53b52918ae66f0d24ca37abb54cf3` |
| PERF-003 prereg json sha256 | `dc01713eafc56347a9eba0711d0947f13fccbc8ba784dfa034e22280ec23c880` |
| projection set id | `ps_v2_ovl_win448_s224` |
| projection config_hash | `7fd5034c9510a1e08ec76bd22b020703c586dd12e7c02659397df05c5c365a8e` |
| snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| chunk_set | `cs_v1_control` (14209 chunks) |
| CE sha256 | `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a` |
| MiniLM fingerprint | `bd95feaeacf98559` |

## Frozen knobs (hashed `config`)

- Exact SYSTEM-G candidate generation: A pool-100 + E-L10 (`L=10`) extras UNION projection-mapped `C_P` (`P=20`). Projection set `ps_v2_ovl_win448_s224`.
- Projection lane is **CANDIDATE-GENERATION only**. No third merge-RRF list.
- EXP-019A projection-aware prior: E-L10 members keep existing E-L10 `a_norm` **exactly**; projection-only `retrieval_norm` = `minmax(projection-RRF)` over the P extras (degenerate 0.5). Combined list is **not** re-minmaxed. Blend **0.7 CE / 0.3 retrieval**.
- PERF-003 D1 CE path: `CrossEncoderReranker(pad='batch', bucket_by_length=True)`; `fast=False`; `threads=4`; `intra_op=4`; `inter_op=1`; `batch_size=16`. Not class-default `pad='fixed'`.
- CE constructor / ONNX sha `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`. Snapshot `snap_689e336380a054d8039dc35b2c09cd0a`. Chunk set `cs_v1_control`.
- Tie-break: blend DESC, E-L10 merge-RRF rank (projection-only `a_rank=10**9`), chunk_id ASC.
- Query rewrite: false. `parent_n=10`, `W=20`, `L=10`, `P=20`, RRF k=60, A pool 100, anti-DOC-C, anti-drop E-L10.
- `one_change_from_G_CE_D1`: identity freeze of the PERF-003 D1 V2 path as the development architecture candidate; no ranking/quality change.

## Observed V2-DEVSET-001 metrics (DEVELOPMENT_ONLY)

Not independently validated. Not a release freeze. **Not a new SYSTEM-H run.** Source: PERF-003 D1 CE on frozen SYSTEM-G pools (equivalence vs old SYSTEM-G CE path).

| metric | SYSTEM-H / PERF-003 D1 (DEVELOPMENT_ONLY) |
| --- | ---: |
| candidate gold-span Recall@100 | 46/50 |
| strict Recall@10 | 41/50 |
| span Recall@10 | 0.82 |
| MRR | 0.6009 |
| document recall | 0.90 |
| raw CE logits identical | 6205/6205, max_abs_diff=0 |
| PERF-003 decision | PERF-003_SUPPORTED |

## Do-nots

- Do not overwrite `SYSTEM-G-PROJECTION-PRIOR.json`, `SYSTEM-G-CE-D1.json`, `SYSTEM-F-PROJECTION.json`, `SYSTEM-E-L10-WITHIN-DOC.json`, `SYSTEM-E-WITHIN-DOC.json`, SYSTEM-D, `cs_v1_control`, or `ps_v2_ovl_win448_s224`.
- **Stop using V2-DEVSET-001 for architecture changes.** V2-DEVSET-001 is CLOSED for architecture changes.
- **Do not evaluate SYSTEM-H yet.**
- **NATQ-001 is next.** Do not author NATQ questions in this freeze.
- Do not load gold150-v1 `holdout.json` or gold150-v1 development/validation. Do not open V1 holdout.
- Do not treat this identity as a v2 release freeze.
