# PERF-003 — V2 CROSS-ENCODER DYNAMIC-PADDING IMPLEMENTATION (D1)

**PREREGISTRATION. HASHED BEFORE ANY CE SCORING.**

Written 2026-09-01T05:12:05Z UTC (2026-09-01T01:12:05-04:00 ET). ChatGPT-authorized PERF-003. Protocol copy: `experiments/PERF-003/CHATGP-PERF-003-protocol.txt` sha256 `431e5f8721cb80a485e263bb95176e4298dc1059a75d21a4002f7b514c70834a`.

Machine-readable twin: `experiments/PERF-003/PERF-003-preregistration.json` sha256 `dc01713eafc56347a9eba0711d0947f13fccbc8ba784dfa034e22280ec23c880`.

This is **SCORE-PRESERVING PERFORMANCE ENGINEERING ONLY**. Not a retrieval experiment. Not a ranking-semantics change. Not a quality promotion. Do not change any retrieval-quality system label.

This preregistration does **not** open `gold150-v1/holdout.json` or load validation. It does **not** overwrite SYSTEM-G-PROJECTION-PRIOR (config_hash `563a7b790564fa1efb96257e988c4b1ccfab45146825d2a366b2fee0ca5d5790`, file SHA256 `7f4ff6db09f32e55cac820cbc00d87ce2ae91886d444c3bad20ac3e04c7f0f61`). It does **not** change CrossEncoderReranker global class defaults (V1/val/holdout share them). It does **not** use `fast=True`, does **not** set `threads=8`, does **not** change `batch_size` to 1, does **not** merge extra optimizations, does **not** change CE model/tokenizer/blend/RRF/candidate generation. One D1 variant only. No thread/batch sweep. No second perf variant.

Baseline: **SYSTEM-G-PROJECTION-PRIOR** config_hash `563a7b790564fa1efb96257e988c4b1ccfab45146825d2a366b2fee0ca5d5790` — strict R@10 **41/50**, cand R@100 **46/50**, span 0.82, MRR 0.6009, document recall 0.90. Constructor: `CrossEncoderReranker()` DEFAULTS.

---

## Purpose

Make the same CE produce exactly the same logits/ranks faster on the V2 SYSTEM-G development path by enabling **D1 only**:

- deterministic length bucketing
- pad each batch to that batch's max seq length (`pad="batch"`)
- preserve max sequence length 512
- preserve tokenizer/truncation semantics
- leave ORT thread configuration unchanged (default intra_op=4, inter_op=1, CPUExecutionProvider)
- unpermute logits back to original candidate order
- same ONNX sha `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`

## Implementation (preregistered)

Class: `experiments/EXP-015/scripts/cross_encoder.py` already has optional `pad="batch"` and `bucket_by_length`. **Defaults stay** `pad="fixed"` length 512, `threads=4`, `bucket_by_length=False`, `fast=False`.

V2 path constructs:

```python
CrossEncoderReranker(pad="batch", bucket_by_length=True)
```

WITHOUT `fast=True` and WITHOUT changing threads.

Frozen bucket rule (already in `_score_bucketed`): sort by unpadded token length then original index. If a V2 wrapper is added, default kwargs are not edited.

Candidate pools: reuse `experiments/EXP-019A/EXP-019A-recovered-union.jsonl` texts + CE pairs. **Do not rerun retrieval.** Passage texts loaded from `cs_v1_control` by recovered `chunk_id`.

## BLOCKING EQUIVALENCE GATE

Paired old-path (defaults) vs D1 path on identical real SYSTEM-G candidate pools. Require ALL:

1. same membership
2. same semantic token IDs before padding
3. same truncation
4. bitwise-identical raw CE logits every pair
5. same unpermuted candidate/logit association
6. same CE_norm
7. same blend scores bitwise if achievable
8. same final rankings
9. cand R@100 exactly 46/50
10. strict R@10 exactly 41/50
11. span 0.82
12. MRR 0.6009
13. doc recall 0.90
14. in-process deterministic repeat
15. fresh-process deterministic repeat

If ANY fail: **STOP**, PERF-003=`FAILED_EQUIVALENCE`, do not tune.

## Timing (only if gate passes)

Same host. Stages: tokenization, bucketing, numpy prep, ONNX, unpermute, CE total, full SYSTEM-G total (stored non-CE stages A+local+projection **1011.4 ms** + measured CE). Report mean, median if available, speedup ratio. Do not compare ms to another host.

## Artifact

NEW `experiments/PERF-003/SYSTEM-G-CE-D1.json` with its own hash. Do not overwrite SYSTEM-G.

## Decision

`PERF-003_SUPPORTED` iff complete equivalence gate passes **AND** measured CE latency improves on this host. Else fail. Engineering-performance only.

## Holdout

holdout-access.log.jsonl 235 bytes sha256 `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`. Do not open holdout.json.

## Stop

Stop after equivalence result, measured latency result, new artifact/hash, PERF-003_SUPPORTED or FAILED. No validation. No holdout. No thread sweep. No batch-size sweep. No additional performance variant. Do not post to ChatGPT.
