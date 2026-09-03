# EXP-019B — cross-encoder necessity ablation (G vs G-NO-CE)

Timestamp: 2026-09-01T05:01:30Z UTC (2026-09-01T01:01:30-04:00 ET). Dataset: V2-DEVSET-001 n=50 only. Prereg json sha256 `eb542d641b60ba907cca321ca6943682257f7088da2028816d04144365dd2c74` (hashed **before** no-CE ranks; seed **20260901**). SYSTEM-G-PROJECTION-PRIOR config_hash `563a7b790564fa1efb96257e988c4b1ccfab45146825d2a366b2fee0ca5d5790`. SYSTEM-F-PROJECTION untouched config_hash `83ba5f2e834ecdffbfe4fb554cf84860ad35cf7010e9764e5cdea9e38598f678` file sha `e68d8c7a5782420bfd63cc57882ce96eacd5d919ac6197d271b9e11e399c3ff5`. One ablation. Not retuned. No second no-CE variant. **Ablation, not promotion.**

gold150-v1 holdout.json not opened. Validation not loaded. SYSTEM-F / SYSTEM-D / SYSTEM-E-WITHIN-DOC.json / SYSTEM-E-L10-WITHIN-DOC.json / cs_v1_control / `ps_v2_ovl_win448_s224` not modified. Candidate generation / projections / E-L10 / CE model / weights unchanged. CE not rerun. Combined retrieval_norm list **not** re-minmaxed. No PERF-003. RELEASE=NOT_FROZEN.

Holdout access log: 235 bytes sha `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3` unchanged=True.

## Grok methodology review (recorded; ranking unchanged)

1. **G-NO-CE is a valid ablation of SYSTEM-G** (remove CE, keep G's `retrieval_norm` exactly). It is **not** a valid CE-vs-retrieval-only *system* comparison: the retrieval channel is G's two-population minmax mix, not a freshly designed retrieval-only ranker.
2. **Hidden two-population minmax:** E-L10 `retrieval_norm` was minmaxed on the E-L10 pool; projection-only `retrieval_norm` was minmaxed on the P extras. Those two scales are mixed on one list because G already did that. This run does **not** re-minmax the combined list.
3. **Tie-break:** after `retrieval_norm` DESC, existing EXP-017/019A order: `a_rank` then `chunk_id`. Projection-only `a_rank=10**9` (1e9), so **E-L10 wins exact `retrieval_norm` ties.** Not a new tie-break.
4. **No gold-label leakage** into no-CE ranks. Candidate membership is the EXP-017/019A projection-RRF union, not CE. Same n=50 already used for architecture research: ablation not promotion, as ChatGPT said.
5. **No second no-CE variant.** Classification is descriptive. Significance is diagnostic, not a gate.

## Method

Prefer stored `experiments/EXP-019A/EXP-019A-recovered-union.jsonl` + `EXP-019A-results.json`. Reconstruct G via frozen EXP-019A scoring (E-L10 keep `a_norm`; projection-only `minmax(projection-RRF)` over P extras). Verify gold ranks and `retrieval_norm` against EXP-019A. Then rank the **same** rows by `retrieval_norm DESC`, `a_rank ASC`, `chunk_id ASC`. No new RRF/blend/normalization. CE skipped latency = stored EXP-017 A + local BM25 + projection (not the 0.2 ms blend).

Pool identity-equivalent = **True**. cand R@100 stayed **46/50**. Reconstructed G strict R@10 = **41/50**.

## PRIMARY DIAGNOSTIC

paired strict R@10: **SYSTEM-G 41/50** vs **G-NO-CE 33/50** (delta G−NO-CE = **+8 cases**).

## SECONDARY

- cand R@100: 46/50 both (identity-equivalent True)
- span R@10: G 0.82 / NO-CE 0.66
- MRR: G 0.6009 / NO-CE 0.4567
- document recall: G 0.90 / NO-CE 0.84
- CE-only rescues (G yes, NO-CE no): V2D-05, V2D-08, V2D-13, V2D-17, V2D-19, V2D-28, V2D-43, V2D-48 (all eight are E-L10 members)
- NO-CE-only rescues (NO-CE yes, G no): none
- rank-1 destructions vs G: 1 (V2D-13: G rank 1 → NO-CE rank 28)
- gold rank movements (`g_rank - noce_rank`; negative = G better): G-better 20, NO-CE-better 7, unchanged 19, still absent 4; mean −5.43
- V2D-33 (EXP-019A projection rescue) stays rank 4 without CE (`retrieval_norm=1.0`)
- latency with CE (EXP-017 stored total): mean **7914.3 ms**
- latency CE skipped (A + local BM25 + projection only): mean **1011.4 ms**
- mean pool: 124.1

## Statistics (diagnostic, not a gate)

- Exact McNemar on strict discordants: n01 (CE-only) = 8, n10 (NO-CE-only) = 0, p_exact = **0.0078125**
- Paired bootstrap of strict R@10 delta (G − NO-CE), seed **20260901**, 10000 resamples: mean **0.158904**, 95% percentile CI **[0.06, 0.26]** (excludes 0)
- Observed delta: 0.16 (+8/50)

## Classification (descriptive only)

**CE materially contributes** — as an ablation of SYSTEM-G, not as a CE-vs-retrieval-only system claim.

Removing CE from G drops strict R@10 41/50 → 33/50, span 0.82 → 0.66, MRR 0.6009 → 0.4567, with 8–0 discordants, McNemar exact p=0.0078125, and bootstrap CI excluding 0. All eight losses are E-L10 golds that CE had lifted despite middling `retrieval_norm`. Latency falls from 7914.3 ms to 1011.4 ms when CE is skipped.

This does **not** say CE beats a well-designed retrieval-only ranker (Grok item 1). It says G's frozen CE term is doing real ranking work on this n=50 split relative to G's own inherited two-population `retrieval_norm`. Do **not** promote. Do **not** delete CE from this split alone. A final architecture decision must eventually be confirmed using fresh questions.

## Standing

No validation. No holdout. No PERF-003. No second no-CE variant. No retune. SYSTEM-F identity not edited. SYSTEM-G is DEVELOPMENT / NOT_FROZEN. No release freeze. Do not post to ChatGPT from this run.

## File paths

- `experiments/EXP-019A/SYSTEM-G-PROJECTION-PRIOR.json`
- `experiments/EXP-019A/SYSTEM-G-PROJECTION-PRIOR.md`
- `experiments/EXP-019A/EXP-019A-CLOSURE.md`
- `experiments/EXP-019B/CHATGP-EXP-019B-protocol.txt`
- `experiments/EXP-019B/EXP-019B-preregistration.json` (sha `eb542d641b60ba907cca321ca6943682257f7088da2028816d04144365dd2c74`)
- `experiments/EXP-019B/EXP-019B-preregistration.md`
- `experiments/EXP-019B/EXP-019B-results.json`
- `experiments/EXP-019B/EXP-019B-report.md`
- `experiments/EXP-019B/scripts/run_exp019b.py`
