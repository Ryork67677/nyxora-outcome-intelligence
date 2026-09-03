# EXP-018B closure

Closed 2026-09-01T03:49:47Z UTC (2026-08-31T23:50:00-04:00 ET). ChatGPT accepted preregistered L=10 and ordered DESIGN ONLY for EXP-017. No retrieval rerun. No V2-DEVSET-001 rescoring. Holdout untouched.

## Status labels (ChatGPT)

| label | value |
| --- | --- |
| EXP-018 | **MECHANISM_SUPPORTED** |
| TRACK1 | **SCORE_PRESERVING** |
| TRACK2 | **L10_SELECTED** |
| SYSTEM-E-L10 | **DEVELOPMENT CANDIDATE** |
| RELEASE | **NOT_FROZEN** |
| VALIDATION | **NOT_RUN** |
| HOLDOUT | **UNTOUCHED** |

## Selected development identity

`SYSTEM-E-L10-WITHIN-DOC` config_hash `bae1c05b5c47c179dc5cd7972a14bd23d102a4d513b674667eb469e17cd85e89`.

New files:

- `experiments/EXP-018B/SYSTEM-E-L10-WITHIN-DOC.json`
- `experiments/EXP-018B/SYSTEM-E-L10-WITHIN-DOC.md`

Uncapped parent `experiments/EXP-018/SYSTEM-E-WITHIN-DOC.json` was **not** overwritten (bytes sha256 `e228616beee1bcb13855c2eadee9fc20ec1fae3e54c77b28587114568c64d087`, config_hash `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe`).

## Integrity at closure

| artifact | bytes | sha256 | unchanged |
| --- | ---: | --- | --- |
| SYSTEM-E-WITHIN-DOC.json | 3595 | `e228616beee1bcb13855c2eadee9fc20ec1fae3e54c77b28587114568c64d087` | True |
| SYSTEM-D-GUARD.json | 2382 | `e9267f5581404e9885598979204c08762cd33f362703e526b20f4d3430c35a82` | True |
| SYSTEM-D-RELEASE.json | 6062 | `1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40` | True |
| holdout-access.log.jsonl | 235 | `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3` | True |

`evals/splits/gold150-v1/holdout.json` was not opened.

## Next (not started here)

EXP-017 preregistration draft is design-only. Do not implement the projection index, do not embed, do not score until ChatGPT/owner authorizes.
