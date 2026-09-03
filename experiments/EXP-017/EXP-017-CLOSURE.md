# EXP-017 closure

Closed 2026-09-01T04:41:48Z UTC (2026-09-01T00:41:48-04:00 ET). ChatGPT-authorized EXP-019A STEP 0. No holdout. No validation. No release freeze. Projection set `ps_v2_ovl_win448_s224` not modified. SYSTEM-D / SYSTEM-E-WITHIN-DOC / SYSTEM-E-L10-WITHIN-DOC / `cs_v1_control` not overwritten.

## Status labels

| label | value |
| --- | --- |
| EXP-017 | **MECHANISM_SUPPORTED** |
| SYSTEM-F-PROJECTION | **DEVELOPMENT CANDIDATE** |
| RELEASE | **NOT_FROZEN** |
| VALIDATION | **NOT_RUN** |
| HOLDOUT | **UNTOUCHED** |

EXP-017 = **MECHANISM_SUPPORTED** (preregistered rule: candidate gold-span recall 46/50 > 44/50 AND 0 strict R@10 regressions vs E-L10 AND 0 rank-1 destructions vs E-L10). Development-stage, not independent validation.

## Selected development identity

`SYSTEM-F-PROJECTION` config_hash `83ba5f2e834ecdffbfe4fb554cf84860ad35cf7010e9764e5cdea9e38598f678` (file SHA256 `e68d8c7a5782420bfd63cc57882ce96eacd5d919ac6197d271b9e11e399c3ff5`). Exact EXP-017 system.

New files:

- `experiments/EXP-017/SYSTEM-F-PROJECTION.json`
- `experiments/EXP-017/SYSTEM-F-PROJECTION.md`

Parents recorded: SYSTEM-A `9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38`; SYSTEM-D `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a`; SYSTEM-E uncapped `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe`; SYSTEM-E-L10 `bae1c05b5c47c179dc5cd7972a14bd23d102a4d513b674667eb469e17cd85e89`; EXP-017 prereg `053a6bf14df088ca9e2283bc3e8dfb0769848a48c54c51a77fbe045795a80cc6`; projection set `ps_v2_ovl_win448_s224` config_hash `7fd5034c9510a1e08ec76bd22b020703c586dd12e7c02659397df05c5c365a8e` n=18057.

## Integrity at closure

| artifact | bytes | sha256 | unchanged |
| --- | ---: | --- | --- |
| SYSTEM-E-WITHIN-DOC.json | 3595 | `e228616beee1bcb13855c2eadee9fc20ec1fae3e54c77b28587114568c64d087` | True |
| SYSTEM-E-L10-WITHIN-DOC.json | 7030 | `efbd3bc1cc73d3c342a607ef75135515d13680b31fd6058e8f1c13e80d13ed89` | True |
| SYSTEM-D-GUARD.json | 2382 | `e9267f5581404e9885598979204c08762cd33f362703e526b20f4d3430c35a82` | True |
| SYSTEM-D-RELEASE.json | 6062 | `1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40` | True |
| holdout-access.log.jsonl | 235 | `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3` | True |

`evals/splits/gold150-v1/holdout.json` was not opened. Validation was not loaded.

## Standing

EXP-019A is a **new** preregistered rescoring experiment (projection-only a_norm 0.0 → minmax(projection-RRF)). It must not edit this identity. Do not freeze a release from this closure.
