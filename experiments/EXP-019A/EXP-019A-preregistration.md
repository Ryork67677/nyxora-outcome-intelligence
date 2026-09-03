# EXP-019A — PROJECTION-ONLY RETRIEVAL-CHANNEL RESCORE

**PREREGISTRATION. HASHED BEFORE ANY NEW FINAL RANKS.**

Written 2026-09-01T04:41:48Z UTC (2026-09-01T00:41:48-04:00 ET). ChatGPT-authorized EXP-019A. Protocol copy: `experiments/EXP-019A/CHATGP-EXP-019A-protocol.txt`.

Machine-readable twin: `experiments/EXP-019A/EXP-019A-preregistration.json` sha256 `f14001eff07b63c7916d7e27567d15ccd1e53b52918ae66f0d24ca37abb54cf3`.

This preregistration does **not** open `gold150-v1/holdout.json` or load validation. It does **not** modify SYSTEM-D, SYSTEM-E-WITHIN-DOC, SYSTEM-E-L10-WITHIN-DOC, `cs_v1_control`, or projection set `ps_v2_ovl_win448_s224`. It does **not** change candidate generation, CE model, CE logits, or 0.7/0.3 weights. No weight sweep. No extra variants after scores. No query rewrite. No release freeze.

Baseline: **SYSTEM-F-PROJECTION** (exact EXP-017 system) config_hash `83ba5f2e834ecdffbfe4fb554cf84860ad35cf7010e9764e5cdea9e38598f678` — strict R@10 **40/50**, cand R@100 **46/50**.

---

## Hypothesis

Replacing projection-only `a_norm = 0.0` with `minmax(projection-RRF)` over the P projection-only extras for that query improves ranking versus SYSTEM-F / EXP-017.

## ONE CHANGE ONLY

1. **E-L10 members:** keep existing E-L10 `a_norm` **exactly**. Do not renormalize them. Do not combine E-L10 and projection scores for them.
2. **Projection-only members:** take the stored projection-RRF fused score (EXP-017 `C_P_scores` / best covering projection fused). Minmax with the **same** `system_e.minmax_norm` used by the retrieval channel (`MINMAX_DEGENERATE=0.5` if `hi==lo`). Use that as the retrieval-channel value instead of 0.0.
3. **Minmax population (ambiguity resolved here, do not retune after scores):** minmax over the **P projection-only fused scores for that query**, not mixed with E-L10 `a` scores. Degenerate 0.5 if constant.
4. **No third RRF list. No candidate membership change.**
5. **Blend still** `0.7 * CE_norm + 0.3 * retrieval_norm`.
6. **CE_norm:** keep the stored EXP-017 CE minmax values **exactly** (do not re-minmax CE because `a_norm` changed).
7. **Tie-break unchanged:** blend DESC, E-L10 merge-RRF rank (projection-only after those with RRF ranks), chunk_id.

## PRIMARY

strict Recall@10. Baseline SYSTEM-F / EXP-017 = **40/50**.

## SECONDARY

cand R@100, span R@10, MRR, document recall, rescues vs frozen EXP-017, regressions vs frozen EXP-017, rank-1 destructions vs frozen EXP-017, rank movements, latency of rescoring.

## Identity gate

Candidate membership **MUST** be identical to EXP-017 so cand R@100 stays **46/50**. If not: implementation drift, **STOP**.

## Decision (preregistered, not retuned)

**RERANK_MECHANISM_SUPPORTED** iff:

1. strict R@10 **> 40/50**
2. **0** strict R@10 regressions vs frozen EXP-017
3. **0** rank-1 destructions vs frozen EXP-017
4. cand R@100 **exactly 46/50**

Else: **NOT_SUPPORTED**.

No named-case gate. **V2D-33** and **V2D-36** are **DIAGNOSTIC_ONLY**.

## Reuse / rematerialize

Prefer stored EXP-017 candidate pools, E-L10 retrieval scores, projection RRF scores, frozen CE logits. `EXP-017-results.json` `per_case` stores C_P lists, span ranks, pool sizes — it may **not** store CE logits / `a_norm` / projection RRF.

If those scores are not stored: rematerialize **ONCE** with the frozen EXP-017 code **ONLY** to recover them, then verify candidate identities match `EXP-017-results.json` per_case (C_P sets, pool sizes, `in_x_pool` / `x_rank` for gold). If membership drifts, STOP. After recovery, apply 019A scoring **in memory**; do **not** call CE again for the 019A ranks.

Verify hashes before scoring: this prereg json, SYSTEM-F config_hash, E-L10 `bae1c05b5c47c179dc5cd7972a14bd23d102a4d513b674667eb469e17cd85e89`, projection set `ps_v2_ovl_win448_s224` / `7fd5034c9510a1e08ec76bd22b020703c586dd12e7c02659397df05c5c365a8e`, holdout log 235 bytes `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`.

## Single eval

One rescore on V2-DEVSET-001 n=50. No second variant. Do not post to ChatGPT. RELEASE=NOT_FROZEN. VALIDATION=NOT_RUN. HOLDOUT=UNTOUCHED.

## Parent hashes

| identity | hash |
| --- | --- |
| SYSTEM-A | `9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38` |
| SYSTEM-D | `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a` |
| SYSTEM-E uncapped | `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe` |
| SYSTEM-E-L10 | `bae1c05b5c47c179dc5cd7972a14bd23d102a4d513b674667eb469e17cd85e89` |
| SYSTEM-F-PROJECTION config_hash | `83ba5f2e834ecdffbfe4fb554cf84860ad35cf7010e9764e5cdea9e38598f678` |
| SYSTEM-F-PROJECTION file SHA256 | `e68d8c7a5782420bfd63cc57882ce96eacd5d919ac6197d271b9e11e399c3ff5` |
| EXP-017 prereg | `053a6bf14df088ca9e2283bc3e8dfb0769848a48c54c51a77fbe045795a80cc6` |
| projection set | `ps_v2_ovl_win448_s224` |
| projection config_hash | `7fd5034c9510a1e08ec76bd22b020703c586dd12e7c02659397df05c5c365a8e` |
