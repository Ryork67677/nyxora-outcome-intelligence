# EXP-015 preregistration

Written **before** any cross-encoder download and **before** any scored EXP-015 run.

## 1. Hypothesis

A pretrained zero-shot relevance cross-encoder, applied only as a reorder of frozen SYSTEM-A candidates, can raise strict Recall@10 versus SYSTEM-A without changing candidate generation.

No training on GOLD. No new passages. No BM25 / MiniLM / RRF / chunking / query / normalization / provider-hint change.

## 2. Control — frozen SYSTEM-A

SYSTEM-A-GLOBAL config hash `9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38`.

Must not change: BM25 (Postgres FTS `simple`), MiniLM ONNX encoder, RRF `rrf_k=60`, `pool_per_retriever=50`, chunking, raw query, normalization, provider hints, candidate generation. `reranker=null`, `cross_encoder=null`, `top_k=10`.

SYSTEM-B is **not** the control. EVAL-VAL-001 classified `REPLICATION_REJECTS_B`.

## 3. Experimental — SYSTEM-C

SYSTEM-A candidates → pretrained cross-encoder reorder only → top 10. May not retrieve new passages.

## 4. Candidate pool = 100 (frozen now)

Handoff-preregistered. No prior EXP-015 pool exists. The only preregistered candidate-generation pool is `pool_per_retriever=50`.

Justified from the already-computed SYSTEM-A validation ceilings (recomputed in `EXP-015-ceiling-analysis.json`; not from a pool sweep):

| pool | perfect-reranker case-pass |
| --- | ---: |
| 10 (measured) | 30/40 |
| 30 | 35/40 |
| 50 | 36/40 |
| **100** | **37/40** |
| 300 | 37/40 |

+7 vs measured 30/40, +2 vs pool 30, +1 vs pool 50, 3 cases unreachable (span absent at 300). **Do not read this as "100 looked best in a sweep". There is no sweep.** Pool 100 is frozen now.

Actual rerank still requires a retrieval rerun to materialize candidates (artifacts store ranks, not lists). Probe depth 300. SYSTEM-A max stored rank 73.

## 5. Model — selected by rule, not by validation score

Selection rule, applied after inventory and without using validation scores:

> smallest widely-used MS MARCO MiniLM cross-encoder that is available and reproducible, else BGE reranker base, else stop

Inventory (this box, 2026-08-31): Hugging Face Hub reachable; no local weight cache; `cross-encoder/ms-marco-MiniLM-L6-v2` Hub API 200; hyphenated `...MiniLM-L-6-v2` 307-redirects to `L6-v2`; `BAAI/bge-reranker-base` also reachable (unused fallback).

**Selected:** `cross-encoder/ms-marco-MiniLM-L6-v2`

| field | value |
| --- | --- |
| source | Hugging Face Hub |
| revision | `233902d25c440f23af6f7d6e94d2946bac0bee0a` |
| artifact | `onnx/model.onnx` (fp32, not quantized) |
| advertised sha256 | `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a` (HEAD `x-linked-etag`; verify after download) |
| tokenizer | BertTokenizer WordPiece, `do_lower_case=true`, vocab 30522 |
| max length | 512 |
| precision | fp32 |
| runtime | onnxruntime + HuggingFace tokenizers (not the Python sentence-transformers CrossEncoder class) |
| architecture | BertForSequenceClassification, 6 layers, hidden 384, 12 heads, ~22.7M |

BGE reranker base is recorded and not used.

## 6. Pair formatting, truncation, scoring, tie-break

- Pair: `[CLS] query [SEP] passage [SEP]`
- Truncation: `max_length=512`, longest_first over the concatenated pair
- Score: raw sequence-classification logit (Identity activation). Higher = more relevant. No sigmoid, no temperature, no training.
- Tie-break: score descending, then original SYSTEM-A fused rank ascending, then `chunk_id` ascending
- Output: top 10 after reorder

## 7. Development qualification (20-case development only)

Split: `evals/splits/gold150-v1/development.json` (n=20). Not the EXP-014R AN/OA set. Compare A vs C.

- Primary: strict Recall@10
- Secondary: span recall, MRR, rescues, regressions, latency
- Proceed to validation only if: positive net rescues, no catastrophic regression pattern, enough pool headroom, reproducibility checks pass

## 8. Freeze SYSTEM-C before loading validation

Freeze model, revision, verified artifact hash, pool 100, pair formatting, truncation, tie-break, scoring, top-k, dependency fingerprint **before** loading the 40 validation cases.

## 9. One-shot validation, then classify

Same 40 gold150-v1 validation cases as EVAL-VAL-001. Classify `RERANKER_SUPPORTED` / `NEUTRAL` / `REJECTED`.

**NEVER run holdout.** holdout_count 90, frozen, access log must remain 0 bytes.

## 10. Post-preregistration download (not a selection change)

After this file existed on disk, `onnx/model.onnx` was downloaded at the preregistered revision. SHA-256 verified as `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a` (matches the advertised Hub etag). Graph loads in onnxruntime 1.29.0 with outputs `logits [batch,1]`. No GOLD scoring.
