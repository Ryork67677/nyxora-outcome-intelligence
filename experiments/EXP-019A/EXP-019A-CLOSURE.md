# EXP-019A closure

Closed 2026-09-01T04:59:09Z UTC (2026-09-01T00:59:09-04:00 ET). ChatGPT-authorized EXP-019B STEP 0. No holdout. No validation. No release freeze. Projection set `ps_v2_ovl_win448_s224` not modified. SYSTEM-F / SYSTEM-D / SYSTEM-E-WITHIN-DOC / SYSTEM-E-L10-WITHIN-DOC / `cs_v1_control` not overwritten.

## Status labels

| label | value |
| --- | --- |
| EXP-019A | **RERANK_MECHANISM_SUPPORTED** |
| SYSTEM-G-PROJECTION-PRIOR | **DEVELOPMENT** |
| RELEASE | **NOT_FROZEN** |
| VALIDATION | **NOT_RUN** |
| HOLDOUT | **UNTOUCHED** |

EXP-019A = **RERANK_MECHANISM_SUPPORTED** (preregistered rule: strict R@10 41/50 > 40/50 AND 0 strict R@10 regressions vs frozen EXP-017/SYSTEM-F AND 0 rank-1 destructions vs SYSTEM-F AND cand R@100 exactly 46/50). Development-stage, not independent validation.

Observed on frozen V2-DEVSET-001 n=50: strict 41/50, cand 46/50, span 0.82, MRR 0.6009, document recall 0.90, 1 rescue V2D-33, 0 regressions, 0 rank-1 destructions.

## Selected development identity

`SYSTEM-G-PROJECTION-PRIOR` config_hash `563a7b790564fa1efb96257e988c4b1ccfab45146825d2a366b2fee0ca5d5790` (file SHA256 `7f4ff6db09f32e55cac820cbc00d87ce2ae91886d444c3bad20ac3e04c7f0f61`). Exact EXP-019A scoring system. **Does not overwrite SYSTEM-F-PROJECTION** (config_hash `83ba5f2e834ecdffbfe4fb554cf84860ad35cf7010e9764e5cdea9e38598f678`, file SHA256 `e68d8c7a5782420bfd63cc57882ce96eacd5d919ac6197d271b9e11e399c3ff5`).

New files:

- `experiments/EXP-019A/SYSTEM-G-PROJECTION-PRIOR.json`
- `experiments/EXP-019A/SYSTEM-G-PROJECTION-PRIOR.md`

Parents recorded: SYSTEM-F `83ba5f2e834ecdffbfe4fb554cf84860ad35cf7010e9764e5cdea9e38598f678`; SYSTEM-E-L10 `bae1c05b5c47c179dc5cd7972a14bd23d102a4d513b674667eb469e17cd85e89`; EXP-019A prereg `f14001eff07b63c7916d7e27567d15ccd1e53b52918ae66f0d24ca37abb54cf3`; SYSTEM-A `9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38`; SYSTEM-D `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a`; SYSTEM-E uncapped `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe`; EXP-017 prereg `053a6bf14df088ca9e2283bc3e8dfb0769848a48c54c51a77fbe045795a80cc6`; projection set `ps_v2_ovl_win448_s224` config_hash `7fd5034c9510a1e08ec76bd22b020703c586dd12e7c02659397df05c5c365a8e` n=18057.

## Integrity at closure

| artifact | bytes | sha256 | unchanged |
| --- | ---: | --- | --- |
| SYSTEM-F-PROJECTION.json | 8874 | `e68d8c7a5782420bfd63cc57882ce96eacd5d919ac6197d271b9e11e399c3ff5` | True |
| SYSTEM-E-L10-WITHIN-DOC.json | 7030 | `efbd3bc1cc73d3c342a607ef75135515d13680b31fd6058e8f1c13e80d13ed89` | True |
| SYSTEM-E-WITHIN-DOC.json | 3595 | `e228616beee1bcb13855c2eadee9fc20ec1fae3e54c77b28587114568c64d087` | True |
| SYSTEM-D-GUARD.json | 2382 | `e9267f5581404e9885598979204c08762cd33f362703e526b20f4d3430c35a82` | True |
| SYSTEM-D-RELEASE.json | 6062 | `1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40` | True |
| holdout-access.log.jsonl | 235 | `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3` | True |

`evals/splits/gold150-v1/holdout.json` was not opened. Validation was not loaded.

## Standing

EXP-019B is a **CE-necessity ablation** of SYSTEM-G (G vs G-NO-CE), not a promotion experiment and not a new system identity. It must not edit this identity. Do not freeze a release from this closure. Do not run PERF-003. Do not validate. Do not open holdout. Do not start another reranker variant.
