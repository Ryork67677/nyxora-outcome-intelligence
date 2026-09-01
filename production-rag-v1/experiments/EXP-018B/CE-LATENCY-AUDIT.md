# EXP-018B CE latency audit (score-preserving)

Written **2026-08-31 23:00 ET** (2026-09-01T04:00:00Z). Track: production RAG SYSTEM-E-L10.
Does **not** run EXP-017, does **not** open holdout, does **not** change ranking, model,
blend weights, or candidate sets. Default E-L10 path still constructs `CrossEncoderReranker()`.

## Current CE ms/query

Stored EXP-018B L=10 (n=50, V2-DEVSET-001 development):

| piece | ms |
| --- | ---: |
| **CE** | **5903.9** |
| A/global | 358.5 |
| local BM25 | 192.4 |
| **E-L10 total** | **6454.8** |

CE is 91.5% of E-L10 wall time. D CE was 5354.9 ms on pool 94.1. Union mean at L=10 is 104.1.

## Current call pattern

Single implementation: `experiments/EXP-015/scripts/cross_encoder.py::CrossEncoderReranker`.
Callers (all `CrossEncoderReranker()`, default kwargs): EXP-015, EXP-016, EXP-018,
EXP-018B, EVAL-VAL-002, EVAL-HOLDOUT-001.

| question | answer |
| --- | --- |
| Session created per query? | **No.** One `InferenceSession` per process (~290–350 ms). Reused for all 50 queries. |
| Batch size 1? | **No.** `score_pairs(..., batch_size=16)`. |
| CPU threads / intra-op? | **`intra_op_num_threads=4`** on an 8-core Xeon. `inter_op_num_threads=1`. Sequential ORT execution. `CPUExecutionProvider`, fp32. Graph opt already `ORT_ENABLE_ALL`. |
| Tokenize every pair from scratch? | **Yes.** HuggingFace `tokenizers.encode_batch([(query, p)…])` on every call. Query is re-tokenized per pair. No passage-encoding cache. |
| Padding? | **Always 512.** `enable_padding(length=512)` even when the unpadded pair is 22–250 tokens. |
| Tensor prep? | numpy int64 `input_ids` / `attention_mask` / `token_type_ids` per batch. No IO binding. |
| How E-L10 invokes CE | Track 1: `score_pairs` on A-pool (~94) then a second call on new extras. Track 2 L=10 CE ms is estimated from those two timings. |

Pair format (verified): `[CLS] query [SEP] passage [SEP]`, `longest_first` at 512, raw sequence-classification logit.

## Measured bottlenecks

Isolated microbench: **synthetic queries** + **104 `cs_v1_control` passages** (`ORDER BY chunk_id`).
Not eval labels. V2-DEVSET-001 was **not** re-scored. Artifacts:
`ce-latency-microbench.json`, `ce-latency-microbench-followup.json`.

Unpadded pair length on that 104-set: mean **251**, p50 **181**, **30.8% already 512**.
On 400 control chunks: mean 237, **26.3% at 512**.

Split of one pad-512 batch-16 pass: tokenize **131 ms**, numpy pack **14 ms**, ORT infer the rest.
Tokenization is not the bottleneck. Session reuse is already correct.

Timed ms / query (104 pairs):

| config | ms |
| --- | ---: |
| baseline pad-512, batch 16, 4 threads (current) | 5571 |
| pad-512, batch 1, 4 threads | 5092 |
| pad-512, batch 16, **8 threads** | 3728 |
| pad=batch **unsorted**, batch 16, 4 threads | 5600 (no win) |
| **length-bucketed pad=batch, batch 16, 8 threads** | **1729** |
| two CE calls (94+10) vs one union call, pad-512 | 5781 vs 5529 |

Unsorted `pad=batch` fails because almost every batch of 16 contains a 512-token pair, so the
batch width stays 512. Sorting by unpadded length yields widths
`[33, 85, 164, 309, 512, 512, 512]` — four cheap batches plus three full-width ones.

## Proposed changes (highest confidence, score-preserving)

Default E-L10 path is **unchanged**. Opt-in lives on `CrossEncoderReranker`.

### 1. `CrossEncoderReranker(fast=True)` — length-bucket + pad-to-batch + 8 threads

Estimated E-L10 CE: **5903.9 × (1729 / 5571) ≈ 1832 ms**. Savings **≈ 4070 ms**.
Estimated E-L10 total **≈ 2380 ms**.

Same ONNX, same tokenizer, same truncation, same raw logit. Output scores are
unpermuted back to input order.

### 2. `CrossEncoderReranker(threads=8)` only

Estimated CE **≈ 3950 ms**. Savings **≈ 1950 ms**. Use if bucket-pad is declined.
Bit-identical on this CPU / ORT 1.29.0.

### 3. One `score_pairs` on the L=10 union instead of A-pool then extras

≈ **250 ms** alone. Bit-identical. Needed so (1) can bucket the full 104-set rather than
two groups. Call-site change only; do not do this inside the default E-L10 runner until
the flag is intentionally flipped.

Not recommended as the next lever: query-token cache (tokenize is ~2%), IO binding,
`pad_to_multiple_of`, batch 64 (regressions / noise), int8, model swap.

## SCORE_PRESERVING

**Verified: exact logit identity (`max_abs_diff = 0`, ranks identical)** on synthetic
`cs_v1_control` pairs for: batch 1/16/32, threads 4 vs 8, short-sequence pad-width 143 vs 512,
length-bucketed pad-batch vs pad-512 (104 pairs), two-call vs one-call, and
`CrossEncoderReranker()` vs `CrossEncoderReranker(fast=True)` on 32 pairs.

V2-DEVSET-001 was **not** re-scored. EXP-018B artifacts do not store CE logits, so there
is no stored-logit gate to replay. Isolated synthetic identity is the gate used here.

## Implemented behind a flag

`experiments/EXP-015/scripts/cross_encoder.py`:

```python
CrossEncoderReranker()              # E-L10 default: pad-512, 4 threads, input order
CrossEncoderReranker(fast=True)     # opt-in: threads=8, pad="batch", bucket_by_length=True
```

`run_exp018b.py` still uses the default constructor. Ranking / blend / L / model unchanged.

## Do-nots

- No model replacement, distillation, or quantized ONNX.
- No blend-weight change, no ranking change, no candidate-set / L / W / parent_n change.
- No EXP-017. No holdout. No overwrite of `SYSTEM-E-WITHIN-DOC.json` or D freeze files.
- Do not turn `fast=True` on the default E-L10 scoring path without an explicit gate.

## Safety hashes (untouched)

- holdout access log: 235 bytes, sha256 `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`
- SYSTEM-E-WITHIN-DOC.json: `e228616beee1bcb13855c2eadee9fc20ec1fae3e54c77b28587114568c64d087`
- SYSTEM-D-GUARD.json: `e9267f5581404e9885598979204c08762cd33f362703e526b20f4d3430c35a82`
- SYSTEM-D-RELEASE.json: `1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40`
