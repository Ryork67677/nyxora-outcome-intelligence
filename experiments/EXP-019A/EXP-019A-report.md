# EXP-019A — projection-only retrieval-channel rescore

Timestamp: 2026-09-01T04:50:38Z UTC. Dataset: V2-DEVSET-001 n=50 only. Prereg json sha256 `f14001eff07b63c7916d7e27567d15ccd1e53b52918ae66f0d24ca37abb54cf3`. SYSTEM-F-PROJECTION config_hash `83ba5f2e834ecdffbfe4fb554cf84860ad35cf7010e9764e5cdea9e38598f678`. Scored once. Not retuned. No second variant.

gold150-v1 holdout.json not opened. Validation not loaded. SYSTEM-D / SYSTEM-E-WITHIN-DOC.json / SYSTEM-E-L10-WITHIN-DOC.json / cs_v1_control / `ps_v2_ovl_win448_s224` not modified. No third merge-RRF list. No candidate membership change. CE logits not recalled for 019A ranks. Blend 0.7/0.3 unchanged. No weight sweep. No query rewrite. RELEASE=NOT_FROZEN.

Holdout access log: 235 bytes sha `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3` unchanged=True.

## Recovery

EXP-017-results.json per_case does **not** store CE logits / a_norm / projection RRF. Rematerialized **once** with frozen EXP-017 code only. Candidate identities verified against EXP-017-results.json (C_P sets/lists, pool sizes, gold in_x_pool / x_rank). **pool identity-equivalent = True**. Then 019A scoring applied in memory (CE not called again).

Mean rematerialization CE ms (recovery only): 7032.8.

## ONE CHANGE

E-L10 members: existing E-L10 a_norm kept exactly. Projection-only members: `minmax_norm` over the P projection-only fused scores for that query (degenerate 0.5 if constant) replaces a_norm=0.0. CE_norm kept exactly from EXP-017 union minmax. Blend 0.7*CE_norm + 0.3*retrieval_norm. Tie-break unchanged.

## PRIMARY

strict R@10: **41/50** vs SYSTEM-F / EXP-017 **40/50**. Strictly greater: `True`.

## SECONDARY

- cand R@100: 46/50 (must 46/50; identity-equivalent `True`)
- span R@10: 0.82 (EXP-017 0.80)
- MRR: 0.6009 (EXP-017 0.597)
- document recall: 0.9 (EXP-017 0.92)
- rescues vs EXP-017: ['V2D-33']
- regressions vs EXP-017: —
- rank-1 destructions vs EXP-017: 0
- rank movements: improved 2, worsened 4, unchanged 40, still absent 4; mean delta (positive=improved) 0.39
- rescoring latency: mean 0.2018 ms / sum 10.0899 ms (019A blend only; recovery CE not included)
- mean pool: 124.1 (EXP-017 124.1)

## DIAGNOSTICS (not a gate)

- V2D-33: EXP-017 rank 23 → 019A rank 4 (delta 19); in_top_10 False → True; entered_via_projection=True; retrieval_norm=1.0; ce_norm=0.9233853803453715
- V2D-36: EXP-017 rank 40 → 019A rank 31 (delta 9); in_top_10 False → False; entered_via_projection=True; retrieval_norm=0.4841269841269824; ce_norm=0.5012522838058954

## Decision (preregistered, not retuned)

**RERANK_MECHANISM_SUPPORTED**

RERANK_MECHANISM_SUPPORTED iff strict R@10 > 40/50 AND 0 strict R@10 regressions vs frozen EXP-017 AND 0 rank-1 destructions vs frozen EXP-017 AND cand R@100 exactly 46/50. Else NOT_SUPPORTED. Development-stage, not independent validation. Not a named-miss gate. No release freeze.

## Standing

No validation. No holdout. No retune. SYSTEM-F identity not edited. No release freeze.

