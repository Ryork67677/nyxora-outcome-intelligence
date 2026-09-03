# EXP-019B — CROSS-ENCODER NECESSITY ABLATION

**PREREGISTRATION. HASHED BEFORE ANY NO-CE RANKS.**

Written 2026-09-01T04:59:09Z UTC (2026-09-01T00:59:09-04:00 ET). ChatGPT-authorized EXP-019B. Protocol copy: `experiments/EXP-019B/CHATGP-EXP-019B-protocol.txt`.

Machine-readable twin: `experiments/EXP-019B/EXP-019B-preregistration.json` sha256 `eb542d641b60ba907cca321ca6943682257f7088da2028816d04144365dd2c74`.

This is an **ablation**, not a promotion experiment. Bootstrap seed **20260901** and McNemar+bootstrap 10000 are recorded here **before** computing no-CE ranks.

This preregistration does **not** open `gold150-v1/holdout.json` or load validation. It does **not** overwrite SYSTEM-F (config_hash `83ba5f2e834ecdffbfe4fb554cf84860ad35cf7010e9764e5cdea9e38598f678`, file SHA256 `e68d8c7a5782420bfd63cc57882ce96eacd5d919ac6197d271b9e11e399c3ff5`). It does **not** modify SYSTEM-D, SYSTEM-E-WITHIN-DOC, SYSTEM-E-L10-WITHIN-DOC, `cs_v1_control`, or projection set `ps_v2_ovl_win448_s224`. It does **not** change candidate generation, projections, E-L10, CE model, or weights. One no-CE variant only. No PERF-003. No second reranker. No release freeze.

Baseline: **SYSTEM-G-PROJECTION-PRIOR** (exact EXP-019A scoring) config_hash `563a7b790564fa1efb96257e988c4b1ccfab45146825d2a366b2fee0ca5d5790` — strict R@10 **41/50**, cand R@100 **46/50**, span 0.82, MRR 0.6009, document recall 0.90.

---

## Purpose

Determine whether the frozen cross-encoder materially improves final ranking on the CURRENT V2 candidate-generation architecture.

Candidate membership must remain identical to SYSTEM-G. Candidate Recall@100 must remain exactly **46/50**. If membership or candidate recall changes: **STOP** for implementation drift.

## G-NO-CE (one variant)

Use the exact SYSTEM-G candidate pool for every query (prefer `EXP-019A-recovered-union.jsonl` + `EXP-019A-results.json`). Do not rerun CE unless identity verification requires it.

1. **E-L10 members:** keep their exact current `retrieval_norm` (E-L10 `a_norm`, minmaxed on the E-L10 pool).
2. **Projection-only members:** keep the exact normalized projection-RRF `retrieval_norm` used by EXP-019A (minmaxed on the P extras).
3. **Do NOT re-minmax the combined list.** Mixing those two scales on one list is inherited from G, not a new normalization. Re-minmaxing the combined list would be a new normalization and is forbidden.
4. **Remove CE from ranking.** Rank by `retrieval_norm DESC`, then existing EXP-017/019A tie-break: `a_rank` (E-L10 merge-RRF rank; projection-only `a_rank=10**9`) then `chunk_id`. On exact `retrieval_norm` ties, E-L10 members rank before projection-only extras. Do not invent a new tie-break.
5. No new RRF, blend, normalization, query-specific rules, or named-case handling.

## PRIMARY DIAGNOSTIC

Paired strict Recall@10: SYSTEM-G (CE) vs SYSTEM-G-NO-CE.

Delta (preregistered): per-case `(1 if G strict R@10 else 0) - (1 if G-NO-CE strict R@10 else 0)`. Positive means CE helps.

## SECONDARY

strict R@10, cand R@100, span R@10, MRR, document recall, CE-only rescues, NO-CE rescues, regressions each direction, rank-1 destructions, exact gold rank movements, candidate-pool identity, latency with CE, latency with CE skipped.

## Statistics (diagnostic, not a gate)

- Exact McNemar test on strict discordant cases (two-sided exact binomial of n01 vs n10 under p=0.5). n01 = G success & NO-CE fail (CE-only); n10 = G fail & NO-CE success (NO-CE-only).
- Paired bootstrap of strict Recall@10 delta. **10,000** resamples. Seed **20260901** (`numpy.random.Generator(numpy.random.PCG64(20260901))`). Percentile 95% CI (2.5th, 97.5th).
- Do not use statistical significance as a tuning gate.

## Latency

- **With CE:** stored EXP-017 per-query totals (identity-equivalent pools). Do not rerun CE.
- **With CE skipped:** retrieval stages only (A + local BM25 + projection) from stored EXP-017 per-query stage times. **Not** the 0.2 ms blend time.

## Classification (descriptive only; not a promotion gate)

After scores, classify as one of:

- CE materially contributes
- CE contribution appears marginal
- NO-CE outperforms
- inconclusive on n=50

Support with paired outcomes, effect size, latency difference, and uncertainty. **Do NOT automatically promote or delete CE based on a one-case difference.** This development split has already been used for architecture research. A final architecture decision must eventually be confirmed using fresh questions.

## Grok methodology check (recorded; protocol unchanged)

1. G-NO-CE is a valid ablation of SYSTEM-G (remove CE, keep G's `retrieval_norm` exactly). It is **NOT** a valid CE-vs-retrieval-only system comparison.
2. Hidden two-population minmax: E-L10 `retrieval_norm` minmaxed on the E-L10 pool; projection-only `retrieval_norm` minmaxed on the P extras. Do **NOT** re-minmax the combined list.
3. Tie-break `a_rank=10**9` for extras means E-L10 wins exact `retrieval_norm` ties. Record it; do not invent a new tie-break.
4. No gold-label leakage into no-CE ranks; membership is projection-RRF not CE. Same n=50 already used: ablation not promotion, as ChatGPT said.
5. Do not add a second no-CE variant. Classify descriptively.

## Single eval

One ablation on V2-DEVSET-001 n=50. No second variant. Do not post to ChatGPT. RELEASE=NOT_FROZEN. VALIDATION=NOT_RUN. HOLDOUT=UNTOUCHED. Do not run PERF-003.

## Parent hashes

| identity | hash |
| --- | --- |
| SYSTEM-A | `9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38` |
| SYSTEM-D | `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a` |
| SYSTEM-E uncapped | `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe` |
| SYSTEM-E-L10 | `bae1c05b5c47c179dc5cd7972a14bd23d102a4d513b674667eb469e17cd85e89` |
| SYSTEM-F-PROJECTION config_hash | `83ba5f2e834ecdffbfe4fb554cf84860ad35cf7010e9764e5cdea9e38598f678` |
| SYSTEM-F-PROJECTION file SHA256 | `e68d8c7a5782420bfd63cc57882ce96eacd5d919ac6197d271b9e11e399c3ff5` |
| SYSTEM-G-PROJECTION-PRIOR config_hash | `563a7b790564fa1efb96257e988c4b1ccfab45146825d2a366b2fee0ca5d5790` |
| SYSTEM-G-PROJECTION-PRIOR file SHA256 | `7f4ff6db09f32e55cac820cbc00d87ce2ae91886d444c3bad20ac3e04c7f0f61` |
| EXP-017 prereg | `053a6bf14df088ca9e2283bc3e8dfb0769848a48c54c51a77fbe045795a80cc6` |
| EXP-019A prereg | `f14001eff07b63c7916d7e27567d15ccd1e53b52918ae66f0d24ca37abb54cf3` |
| projection set | `ps_v2_ovl_win448_s224` |
| projection config_hash | `7fd5034c9510a1e08ec76bd22b020703c586dd12e7c02659397df05c5c365a8e` |
| holdout-access.log.jsonl | `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3` (235 bytes) |
