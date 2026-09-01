# SYSTEM-E-L10-WITHIN-DOC

Immutable **development-system** identity for the EXP-018B-selected L=10 within-document cap.

Written 2026-09-01T03:49:47Z UTC (2026-08-31T23:50:00-04:00 ET). Russell overnight / ChatGPT accepted L=10 and ordered DESIGN ONLY for EXP-017.

| | |
| --- | --- |
| name | `SYSTEM-E-L10-WITHIN-DOC` |
| **config_hash** | `bae1c05b5c47c179dc5cd7972a14bd23d102a4d513b674667eb469e17cd85e89` |
| status | **DEVELOPMENT CANDIDATE** |
| release | **NOT_FROZEN** |
| validation | **NOT_RUN** / **NOT independently validated** |
| holdout | **UNTOUCHED** |

This file does **not** overwrite `experiments/EXP-018/SYSTEM-E-WITHIN-DOC.json` (uncapped parent). That file must remain `e228616beee1bcb13855c2eadee9fc20ec1fae3e54c77b28587114568c64d087` / config_hash `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe`.

## Parent / provenance

| identity | hash |
| --- | --- |
| SYSTEM-A | `9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38` |
| SYSTEM-D | `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a` |
| SYSTEM-E uncapped parent | `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe` |
| EXP-018B prereg json sha256 | `c48068ec5dfa06683eaa2b0763508e9c7457d1ede2f23c3394c3c6bd6192ce8c` |
| snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| chunk_set | `cs_v1_control` (14209 chunks) |
| CE sha256 | `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a` |
| MiniLM fingerprint | `bd95feaeacf98559` |

## Frozen knobs (hashed `config`)

- `parent_n=10` unique `version_id`s from A fused top-10 (ChatGPT option B).
- `W=20` per parent still used to **generate** extras, then cap to `L=10`.
- `L=10` means **additive local passages per query** after dedupe excluding A-pool-100. Not per parent.
- Cross-parent extras order (frozen in EXP-018B prereg): `round(local BM25, 9) DESC`, then `chunk_id ASC`.
- Track 1 batched IDF (`experiments/EXP-018B/scripts/local_bm25_batched.py`) is the score-preserving implementation; scoring semantics identical to per-parent `lexical_search`.
- Blend 0.7/0.3, RRF k=60, A pool 100, anti-DOC-C (never drop an A-pool chunk).
- Local retrieval BM25 only (no within-doc dense). Full-corpus IDF, never recomputed inside a document.

`config_hash` is `rag_v1.ids.config_hash` over the `config` object only. Observed metrics are **excluded** from the hashed dict.

## Observed V2-DEVSET-001 metrics (DEVELOPMENT_ONLY)

Not independently validated. Not a release freeze.

| metric | E-L10 |
| --- | ---: |
| candidate gold-span Recall@100 | 44/50 |
| strict Recall@10 | 40/50 |
| span Recall@10 | 0.80 |
| MRR | 0.5956 |
| document recall | 0.92 |
| mean union | 104.1 |
| total latency | 6454.8 ms |
| strict regressions vs D | 0 |
| rank-1 destructions | 0 |

Selection rule was preregistered in EXP-018B: smallest L in {10,20,40} with candidate Recall@100 ≥ 44/50 and zero strict Recall@10 regressions vs D. Threshold ≥44/50 was a development-stage criterion after EXP-018's 45/50; it is **not** an independent validation threshold.

## Do-nots

- Do not overwrite `SYSTEM-E-WITHIN-DOC.json`.
- Do not edit SYSTEM-D (`SYSTEM-D-GUARD.json`, `SYSTEM-D-RELEASE.json`).
- Do not change CE/blend weights.
- Do not load gold150-v1 holdout.json or gold150-v1 development/validation.
- Do not treat this identity as a v2 release freeze.
