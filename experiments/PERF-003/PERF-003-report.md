# PERF-003 — V2 CROSS-ENCODER D1 DYNAMIC PADDING

Written 2026-09-01T01:38:07-0400 ET (2026-09-01T05:38:07Z UTC). ChatGPT-authorized PERF-003.
SCORE-PRESERVING PERFORMANCE ENGINEERING ONLY. Did not post to ChatGPT.

**Decision: `PERF-003_SUPPORTED`**

Prereg JSON sha256 `dc01713eafc56347a9eba0711d0947f13fccbc8ba784dfa034e22280ec23c880`.
SYSTEM-G config_hash `563a7b790564fa1efb96257e988c4b1ccfab45146825d2a366b2fee0ca5d5790` not overwritten.

## Equivalence gate

Pass: **True**

- `1_same_membership`: PASS
- `2_same_semantic_token_ids_before_padding`: PASS
- `3_same_truncation`: PASS
- `4_bitwise_identical_raw_ce_logits`: PASS
- `5_same_unpermuted_candidate_logit_association`: PASS
- `6_same_ce_norm`: PASS
- `7_same_blend_scores_bitwise`: PASS
- `8_same_final_rankings`: PASS
- `9_cand_R100_46_50`: PASS
- `10_strict_R10_41_50`: PASS
- `11_span_0_82`: PASS
- `12_mrr_0_6009`: PASS
- `13_doc_recall_0_90`: PASS
- `14_in_process_deterministic_repeat`: PASS
- `15_fresh_process_deterministic_repeat`: PASS
- `profiler_matches_class_score_pairs`: PASS
- `class_defaults_unchanged`: PASS
- `old_path_metrics_match_SYSTEM_G`: PASS
- `d1_path_metrics_match_SYSTEM_G`: PASS
- `no_fast_true`: PASS
- `threads_unchanged_4`: PASS

### Metrics (D1 path)

- cand R@100: 46/50 (require 46/50)
- strict R@10: 41/50 (require 41/50)
- span R@10: 0.82 (require 0.82)
- MRR: 0.6009 (require 0.6009)
- document recall: 0.9 (require 0.90)

Raw CE logits max abs diff old vs D1: 0.0
n_pairs: 6205; logit mismatches: 0

## Timing (this host only; do not compare ms to another host)

CPU: Intel(R) Xeon(R) Processor n=8
ORT 1.29.0 provider=CPUExecutionProvider intra_op=4 inter_op=1

| stage | old mean ms | old median ms | D1 mean ms | D1 median ms | speedup |
| --- | ---: | ---: | ---: | ---: | ---: |
| tokenization_ms | 21.9407 | 21.5752 | 20.0683 | 19.9178 | 1.0933 |
| bucketing_ms | 0.0 | 0.0 | 12.8995 | 12.6035 | 0.0 |
| numpy_prep_ms | 6.2338 | 6.1965 | 3.3224 | 3.281 | 1.8763 |
| onnx_ms | 6762.1719 | 6826.0565 | 2080.4706 | 2064.3397 | 3.2503 |
| unpermute_ms | 0.055 | 0.0516 | 0.0541 | 0.0514 | 1.0166 |
| ce_total_ms | 6791.1651 | 6857.5911 | 2117.5741 | 2102.4286 | 3.207 |

SYSTEM-G total old = stored non-CE 1011.4 + CE 6791.1651 = **7802.5651 ms**
SYSTEM-G total D1 = stored non-CE 1011.4 + CE 2117.5741 = **3128.9741 ms**
CE speedup ratio (old/new): **3.207**
CE latency improved: **True**

Stored non-CE 1011.4 ms is EXP-017 A+local+projection (EXP-019B G-NO-CE). Retrieval was not rerun.

## Artifact

- path: `experiments/PERF-003/SYSTEM-G-CE-D1.json`
- config_hash: `6d108568f3131bad87d8617f5c2fb88ea14428e397d59ff54ff8e11cc4647b7d`
- file sha256: `cf0c985c5f7738e7fc5422039fd6940621d8dcd8f91de41abe3784ac53a6a7ec`

## Provenance

- CE ONNX sha256: `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`
- tokenizer sha256: `d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66`
- cross_encoder.py sha256: `ad987d12747c28e75257d8d9a0a526d216052937cffe2268921f5278b51fac45`
- batch_size: 16
- old pad: fixed 512; D1 pad: batch; bucket: unpadded length then original index
- holdout log: 235 bytes sha `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3` unchanged=True

No validation. No holdout.json. No fast=True. No threads=8. No second variant.

## Metrics correction

The first metrics pass reconstructed blend with recovered-union `a_norm` for projection extras. Those compact rows still carry EXP-017 `a_norm=0.0` / `blend_rank` (SYSTEM-F), not SYSTEM-G. SYSTEM-G extras use `minmax(projection_fused)` (EXP-019A). Recomputed from stored logits with that formula; CE was not rerun. Old vs D1 logits remained bitwise identical (`max_abs_diff=0`, 6205/6205 pairs). After correction: strict R@10 41/50, span 0.82, MRR 0.6009, document recall 0.90, cand R@100 46/50.
