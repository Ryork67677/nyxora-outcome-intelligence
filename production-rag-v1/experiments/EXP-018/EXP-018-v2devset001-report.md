# EXP-018 V2-DEVSET-001 D vs E

Timestamp: 2026-09-01T03:09:59Z (UTC). Split: v2-devset-001/development n=50. One comparison of frozen SYSTEM-D vs frozen SYSTEM-E. E knobs not retuned.
gold150-v1 holdout.json not opened. gold150-v1/development not loaded. Validation not loaded.
Holdout access log before/after: 235/235 bytes (sha 45b83a77f6f3… unchanged=True).
SYSTEM-D `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a`. SYSTEM-E `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe`. Snapshot `snap_689e336380a054d8039dc35b2c09cd0a`. chunk_set `cs_v1_control`.

## Primary metric — candidate gold-span Recall@100

D/A pool 41/50 = 0.8200; E union 45/50 = 0.9000.
Candidate-pool rescues vs D: ['V2D-11', 'V2D-33', 'V2D-34', 'V2D-43']; only-in-D (should be empty if additive): —.

## Secondary

| V | strict R@10 | span recall | spans@10 | MRR | doc recall | cand-ev recall (pool) | pool mean/max | latency ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 32/50 | 0.6400 | 32/50 | 0.4762 | 0.8800 | 0.8200 | 94.1/100 | 357.5 |
| D | 38/50 | 0.7600 | 38/50 | 0.5650 | 0.9000 | 0.8200 | 94.1/100 | 5823.6 |
| E | 40/50 | 0.8000 | 40/50 | 0.5969 | 0.9200 | 0.9000 | 176.8/269 | 16604.3 |

Additive integrity: `True`. Rescues vs D (strict R@10): ['V2D-43', 'V2D-48']; regressions vs D: —; net +2.
Rank-1 destruction vs D: 0; vs A: 0.
E mean latency 16604.3 ms vs rematerialized D 5823.6 ms.

## Differing cases

- `V2D-11` D_full=False E_full=False inD=False inE=True D_rank=None E_rank=34 pool 94→231
- `V2D-33` D_full=False E_full=False inD=False inE=True D_rank=None E_rank=13 pool 84→194
- `V2D-34` D_full=False E_full=False inD=False inE=True D_rank=None E_rank=44 pool 97→240
- `V2D-43` D_full=False E_full=True inD=False inE=True D_rank=None E_rank=10 pool 96→145
- `V2D-48` D_full=False E_full=True inD=True inE=True D_rank=11 E_rank=7 pool 90→183

## Decision (preregistered, not retuned)

**MECHANISM_SUPPORTED**

- MECHANISM_SUPPORTED: `True`
- CANDIDATE_GAIN_RERANKING_LIMITED: `False`
- REJECT_WITHIN_DOC_BM25: `False`
- candidate_recall_improved: `True`
- top10_improved: `True`
- tuned_after_seeing_scores: `False`
- SYSTEM-E config hash (unchanged): `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe`
- SYSTEM-D-GUARD.json / SYSTEM-D-RELEASE.json / SYSTEM-E-WITHIN-DOC.json bytes unchanged.
- Environment: PostgreSQL 16.15 (Debian 16.15-1.pgdg12+2) on x86_64-pc-linux-gnu / pgvector 0.8.6.

