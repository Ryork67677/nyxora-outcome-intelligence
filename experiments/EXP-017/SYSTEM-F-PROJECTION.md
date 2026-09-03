# SYSTEM-F-PROJECTION

Immutable **development-system** identity for the **exact EXP-017 system** (SYSTEM-E-L10 + additive search-projection P=20).

Written 2026-09-01T04:41:48Z UTC (2026-09-01T00:41:48-04:00 ET). ChatGPT-authorized EXP-019A STEP 0 close of EXP-017. No holdout. No validation. No release freeze.

| | |
| --- | --- |
| name | `SYSTEM-F-PROJECTION` |
| **config_hash** | `83ba5f2e834ecdffbfe4fb554cf84860ad35cf7010e9764e5cdea9e38598f678` |
| file SHA256 | `e68d8c7a5782420bfd63cc57882ce96eacd5d919ac6197d271b9e11e399c3ff5` |
| status | **DEVELOPMENT CANDIDATE** |
| release | **NOT_FROZEN** |
| validation | **NOT_RUN** / **NOT independently validated** |
| holdout | **UNTOUCHED** |

`config_hash` is `rag_v1.ids.config_hash` over the `config` object only. Observed metrics are **excluded** from the hashed dict (`observed_metrics_DEVELOPMENT_ONLY`). Keep config_hash distinct from file SHA256.

This file does **not** overwrite:

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
| EXP-017 prereg json sha256 | `053a6bf14df088ca9e2283bc3e8dfb0769848a48c54c51a77fbe045795a80cc6` |
| projection set id | `ps_v2_ovl_win448_s224` |
| projection config_hash | `7fd5034c9510a1e08ec76bd22b020703c586dd12e7c02659397df05c5c365a8e` |
| snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| chunk_set | `cs_v1_control` (14209 chunks) |
| CE sha256 | `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a` |
| MiniLM fingerprint | `bd95feaeacf98559` |

## Frozen knobs (hashed `config`)

- Exact EXP-017 system. Candidate generation = E-L10 C_E UNION projection-mapped C_P (P=20).
- Projection lane is **CANDIDATE-GENERATION only**. No third merge-RRF list.
- E-L10 members keep existing E-L10 `a_norm` **exactly**. Projection-only `a_norm = 0.0` (not `minmax_degenerate=0.5`).
- CE minmax over the union C. Blend 0.7 CE / 0.3 retrieval.
- Tie-break: blend DESC, E-L10 merge-RRF rank (projection-only after those with RRF ranks), chunk_id ASC.
- Query rewrite: false. CE constructor: `CrossEncoderReranker()` defaults (not `fast=True`).
- `parent_n=10`, `W=20`, `L=10`, `P=20`, RRF k=60, A pool 100, anti-DOC-C, anti-drop E-L10.

## Observed V2-DEVSET-001 metrics (DEVELOPMENT_ONLY)

Not independently validated. Not a release freeze. Source: EXP-017 single scored run.

| metric | SYSTEM-F / EXP-017 |
| --- | ---: |
| candidate gold-span Recall@100 | 46/50 |
| strict Recall@10 | 40/50 |
| span Recall@10 | 0.80 |
| MRR | 0.597 |
| document recall | 0.92 |
| mean union | 124.1 |
| mean projection additions | 20 |
| total latency | 7914.3 ms |
| strict regressions vs E-L10 | 0 |
| rank-1 destructions vs E-L10 | 0 |
| EXP-017 decision | MECHANISM_SUPPORTED |

## Do-nots

- Do not overwrite `SYSTEM-E-L10-WITHIN-DOC.json`, `SYSTEM-E-WITHIN-DOC.json`, SYSTEM-D, `cs_v1_control`, or `ps_v2_ovl_win448_s224`.
- Do not load gold150-v1 holdout.json or gold150-v1 development/validation.
- Do not treat this identity as a v2 release freeze.
- EXP-019A may rescore projection-only retrieval-channel values; that is a **new** experiment, not an edit of this identity.
