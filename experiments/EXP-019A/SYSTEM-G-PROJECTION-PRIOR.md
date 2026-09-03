# SYSTEM-G-PROJECTION-PRIOR

Immutable **development-system** identity for the **exact EXP-019A scoring system** (SYSTEM-F + projection-only retrieval-channel = minmax(projection-RRF) over P extras).

Written 2026-09-01T04:59:09Z UTC (2026-09-01T00:59:09-04:00 ET). ChatGPT-authorized EXP-019B STEP 0 close of EXP-019A. No holdout. No validation. No release freeze. **Does not overwrite SYSTEM-F.**

| | |
| --- | --- |
| name | `SYSTEM-G-PROJECTION-PRIOR` |
| **config_hash** | `563a7b790564fa1efb96257e988c4b1ccfab45146825d2a366b2fee0ca5d5790` |
| file SHA256 | `7f4ff6db09f32e55cac820cbc00d87ce2ae91886d444c3bad20ac3e04c7f0f61` |
| status | **DEVELOPMENT** |
| release | **NOT_FROZEN** |
| validation | **NOT_RUN** / **NOT independently validated** |
| holdout | **UNTOUCHED** |

`config_hash` is `rag_v1.ids.config_hash` over the `config` object only. Observed metrics are **excluded** from the hashed dict (`observed_metrics_DEVELOPMENT_ONLY`). Keep config_hash distinct from file SHA256.

This file does **not** overwrite:

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
| EXP-017 prereg json sha256 | `053a6bf14df088ca9e2283bc3e8dfb0769848a48c54c51a77fbe045795a80cc6` |
| EXP-019A prereg json sha256 | `f14001eff07b63c7916d7e27567d15ccd1e53b52918ae66f0d24ca37abb54cf3` |
| projection set id | `ps_v2_ovl_win448_s224` |
| projection config_hash | `7fd5034c9510a1e08ec76bd22b020703c586dd12e7c02659397df05c5c365a8e` |
| snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| chunk_set | `cs_v1_control` (14209 chunks) |
| CE sha256 | `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a` |
| MiniLM fingerprint | `bd95feaeacf98559` |

## Frozen knobs (hashed `config`)

- Exact EXP-019A scoring. Candidate generation identical to SYSTEM-F (E-L10 C_E UNION projection-mapped C_P, P=20).
- Projection lane is **CANDIDATE-GENERATION only**. No third merge-RRF list.
- E-L10 members keep existing E-L10 `a_norm` **exactly** (minmaxed on the E-L10 pool).
- Projection-only `retrieval_norm` = `minmax(projection-RRF)` over the P extras for that query (degenerate 0.5). This two-population minmax is inherited from EXP-019A; the combined list is **not** re-minmaxed.
- CE minmax over the union C, kept exactly from EXP-017. Blend 0.7 CE / 0.3 retrieval.
- Tie-break: blend DESC, E-L10 merge-RRF rank (projection-only `a_rank=10**9`), chunk_id ASC. On exact retrieval_norm ties, E-L10 members therefore rank before projection-only extras.
- Query rewrite: false. CE constructor: `CrossEncoderReranker()` defaults (not `fast=True`).
- `parent_n=10`, `W=20`, `L=10`, `P=20`, RRF k=60, A pool 100, anti-DOC-C, anti-drop E-L10.

## Observed V2-DEVSET-001 metrics (DEVELOPMENT_ONLY)

Not independently validated. Not a release freeze. Source: EXP-019A single scored run.

| metric | SYSTEM-G / EXP-019A |
| --- | ---: |
| candidate gold-span Recall@100 | 46/50 |
| strict Recall@10 | 41/50 |
| span Recall@10 | 0.82 |
| MRR | 0.6009 |
| document recall | 0.90 |
| mean union | 124.1 |
| mean projection additions | 20 |
| strict rescues vs SYSTEM-F | 1 (V2D-33) |
| strict regressions vs SYSTEM-F | 0 |
| rank-1 destructions vs SYSTEM-F | 0 |
| EXP-019A decision | RERANK_MECHANISM_SUPPORTED |

## Do-nots

- Do not overwrite `SYSTEM-F-PROJECTION.json`, `SYSTEM-E-L10-WITHIN-DOC.json`, `SYSTEM-E-WITHIN-DOC.json`, SYSTEM-D, `cs_v1_control`, or `ps_v2_ovl_win448_s224`.
- Do not load gold150-v1 holdout.json or gold150-v1 development/validation.
- Do not treat this identity as a v2 release freeze.
- EXP-019B G-NO-CE is an **ablation** of this identity (CE contribution removed; G retrieval_norm kept exactly). It is **not** a new system identity and **not** a promotion experiment.
