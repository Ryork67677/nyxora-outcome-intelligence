# Claude handoff: score-preserving CE latency (SYSTEM-E-L10)

Written 2026-08-31 23:58 ET. Pack assembled from the box work tree
`/workspace/rag-v1/repo/production-rag-v1` (not a git checkout). Frozen
Windows production checkout must stay at `claude/rag-v1-build-experiments-5yngul`
**e65912a**. Do not edit that checkout. Do not open `holdout.json`.

Claude owns the official CE latency track. This pack is the V2 source + CE
model dir + call site + EXP-018B timers + V2-DEVSET-001 hashes. Grok's
parallel audit is included as optional context only (not a freeze).

## DROP PERF-002 from the frozen checkout

Claude wrote `experiments/PERF-002/PERF-002-report.md` on a checkout they
were told **not** to modify. **Drop that file** from the frozen Windows
checkout (`C:\Users\yorkr\Documents\Codex\2026-08-29\can-you-look-at-rag-project\rag-review\production-rag-v1`).
Do not commit PERF-002. Do not treat it as part of this track. At pack time
that path was **not** present on the frozen tree (HEAD e65912a, clean); if
it reappears, delete it. This handoff branch also does **not** contain PERF-002.

## Constraints (hard)

- Score-preserving only. Same ONNX, same tokenizer, same truncation
  (`longest_first` 512), same raw sequence-classification logit.
- No model swap, distillation, quantization, or int8 ONNX.
- No blend-weight change, ranking change, candidate-set / L / W / parent_n change.
- No holdout. Do not open `evals/splits/gold150-v1/holdout.json`.
- No source edits on the frozen Windows checkout (HEAD e65912a).
- E-L10 MUST keep `CrossEncoderReranker()` **defaults** until ChatGPT
  authorizes a score-preserving switch. Optional `fast=` / `pad=` kwargs
  on the class are a Grok audit experiment, not a freeze change.
- Do not add timers to the frozen E-L10 path. Reuse EXP-018B keys below.
- Do not treat `experiments/EXP-018B/CE-LATENCY-AUDIT.md` (or the
  microbench JSONs) as a freeze.

---

## 1. V2 source tree with CE path

Remote: `https://github.com/Ryork67677/nyxora-outcome-intelligence.git`

Claude can already fetch `origin/claude/rag-v1-build-experiments-5yngul`.
This pack is also published as branch **`grok/ce-latency-handoff`** (see
§GitHub below). If git push is unavailable, add this folder as a local repo:

- Windows extract (NEW folder, not inside the frozen repo):
  `C:\Users\yorkr\Documents\Codex\2026-08-29\claude-ce-handoff`
- Tarball: `C:\Users\yorkr\Documents\Codex\2026-08-29\claude-ce-handoff.tar.gz`
- Optional git worktree used to publish the branch (does not move frozen HEAD):
  `C:\Users\yorkr\Documents\Codex\2026-08-29\nyxora-ce-latency-wt`

Box source of the copies: `/workspace/rag-v1/repo/production-rag-v1`.

## 2. CE model dir (ONNX + config.json + tokenizer)

Path (repo-relative):

```
experiments/EXP-015/models/cross-encoder-ms-marco-MiniLM-L6-v2/233902d25c440f23af6f7d6e94d2946bac0bee0a/
```

| file | role |
| --- | --- |
| `onnx/model.onnx` (~87 MB, 91011230 bytes) | ONNX weights |
| `config.json` | architecture (settles H3 by itself) |
| `tokenizer.json` | HF tokenizers file used at runtime |
| `tokenizer_config.json` | tokenizer config |
| `special_tokens_map.json` | special tokens |
| `vocab.txt` | WordPiece vocab |

- ONNX sha256: `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`
- HF revision: `233902d25c440f23af6f7d6e94d2946bac0bee0a`
- Runtime name in `cross_encoder.py`: `cross-encoder/ms-marco-MiniLM-L6-v2`

### H3 (config.json alone)

`config.json` `_name_or_path` is `cross-encoder/ms-marco-MiniLM-L-12-v2`
but `num_hidden_layers` is **6**. This is **L6**, not L12. That mismatch
is the H3 settlement: the artifact is MiniLM-L6-v2 (6 layers, hidden 384,
Identity activation). Do not swap in L-12.

```
"_name_or_path": "cross-encoder/ms-marco-MiniLM-L-12-v2"
"num_hidden_layers": 6
"hidden_size": 384
"sbert_ce_default_activation_function": "torch.nn.modules.linear.Identity"
```

If GitHub rejects `model.onnx` for size, take ONNX from this tarball or
from HF revision `233902d25c440f23af6f7d6e94d2946bac0bee0a`. `config.json`
in the pack is enough for H3 either way.

## 3. Call site + SessionOptions / provider config

**Call site:** `experiments/EXP-015/scripts/cross_encoder.py`

Class: `CrossEncoderReranker`. EXP-018B constructs it with **no kwargs**:

```python
ce = CrossEncoderReranker()   # experiments/EXP-018B/scripts/run_exp018b.py
```

### SessionOptions (defaults)

```python
options = ort.SessionOptions()
options.intra_op_num_threads = threads   # default threads=4
options.inter_op_num_threads = 1
self._session = ort.InferenceSession(
    str(CE_ONNX), options, providers=["CPUExecutionProvider"]
)
```

- `intra_op_num_threads=threads` (default **4**)
- `inter_op_num_threads=1`
- provider: `["CPUExecutionProvider"]` only (fp32)
- graph opt: ORT default `ORT_ENABLE_ALL` (not overridden)
- pad **fixed 512**: `enable_padding(length=MAX_LENGTH)` with `MAX_LENGTH=512`
- `batch_size=16` (`score_pairs(..., batch_size: int = 16)`)
- tokenizer: `enable_truncation(max_length=512, strategy="longest_first")`
- pair format: BERT `[CLS] query [SEP] passage [SEP]`
- score: raw sequence-classification logit (Identity activation)
- session is created **once per process**, reused across queries

### Optional kwargs — NOT a freeze; E-L10 must keep defaults

`cross_encoder.py` currently has optional `fast=` / `pad=` / `bucket_by_length`
kwargs (Grok audit experiment). They do not change callers that construct
`CrossEncoderReranker()`.

| constructor | meaning |
| --- | --- |
| `CrossEncoderReranker()` | **required E-L10 path**: pad=fixed 512, threads=4, input order |
| `CrossEncoderReranker(fast=True)` | opt-in: threads=8, pad="batch", bucket_by_length=True |

**E-L10 MUST use `CrossEncoderReranker()` defaults.** Do not flip `fast=True`
on the default E-L10 scoring path until ChatGPT authorizes a score-preserving
switch. Those kwargs are not a freeze change.

## 4. EXP-018B existing latency timers

**Do not add timers to the frozen E-L10 path.** Reuse the per-query
`latency_ms` keys already written by
`experiments/EXP-018B/scripts/run_exp018b.py`.

Per-query dict (one per case):

```python
"latency_ms": {
    "system_a_retrieval": ...,   # lat_a
    "local_bm25": ...,           # lat_local
    "cross_encoder_D_pool": ..., # lat_ce_d   (CE on A-pool)
    "cross_encoder_E_union": ...,# lat_ce_e   (CE D-pool + extras)
    "D_total": ...,
    "E_total": ...,
}
```

Timer placement (same file, Track 1 loop):

- `system_a_retrieval`: `retrieve_system_a_pool`
- `local_bm25`: `local_bm25_per_parent_batched` (`experiments/EXP-018B/scripts/local_bm25_batched.py`)
- `cross_encoder_D_pool`: `ce.score_pairs` on A-pool (~94)
- `cross_encoder_E_union`: D-pool time + second `score_pairs` on new extras
- `D_total`: case elapsed minus local BM25
- `E_total`: full case elapsed

Track-1 means in `experiments/EXP-018B/EXP-018B-results.json`:

| key | ms |
| --- | ---: |
| A_retrieval_mean | 358.5 |
| local_bm25_mean | 192.4 |
| CE_D_pool_mean | 5354.9 |
| CE_E_union_mean | 9913.6 |
| D_total_mean | 5717.4 |
| E_total_mean | 10469.4 |

Stored E-L10 (Track-2 L=10 secondary, n=50, V2-DEVSET-001 development):

| piece | ms |
| --- | ---: |
| CE (`CE_latency_ms`) | **5903.9** |
| A/global | 358.5 |
| local BM25 | 192.4 |
| **E-L10 total** | **6454.8** |

CE is 91.5% of E-L10 wall time. Union mean at L=10 is 104.1.
CE L=10 note in results: estimated per query as
`CE_D + (CE_E-CE_D)*(n_additive_L/n_additive_E)` (capped union is a subset;
CE scores reused from Track 1).

## 5. V2-DEVSET-001 + split hashes (metric-identity / §6 only)

Use these for metric-identity only. Do not retune. Do not open holdout.

| artifact | path | sha256 |
| --- | --- | --- |
| freeze json | `experiments/RAG-V2/V2-DEVSET-001/V2-DEVSET-001-FREEZE.json` | `97ea6befbb4fd845f53da2aef20ba84cedaaf69c0f09e3ad90833b813fee2ad9` |
| gold jsonl | `evals/gold/v2-devset-001.jsonl` | `cb687f3cc88b38d4beed7ad4bc829296a30518aaaf45cce0677ec568b1bf77e5` |
| split | `evals/splits/v2-devset-001/development.json` | `6b0c49c9040c215fde6134697c35a1f28458ba7d72ef012c0840feb7f9c3eb17` |

Also packed: `experiments/RAG-V2/V2-DEVSET-001/V2-DEVSET-001-FREEZE.manifest.json`
(same three hashes under `sha256`). n=50, split ids `V2D-01`..`V2D-50`.
`holdout_json_opened: false`. `retrieval_was_not_run: true`.

---

## Optional context: Grok CE latency audit (not a freeze)

Claude owns the official CE track. Grok already ran a **score-preserving**
isolated microbench. Include for context; do not treat as freeze or as
authorization to flip `fast=True` on E-L10.

Packed:

- `experiments/EXP-018B/CE-LATENCY-AUDIT.md`
- `experiments/EXP-018B/CE-LATENCY-AUDIT.json`
- `experiments/EXP-018B/ce-latency-microbench.json`
- `experiments/EXP-018B/ce-latency-microbench-followup.json`

Headline: **pad-512 is the bottleneck**, not session create, not tokenize
(~2%), not batch-size-1. Session is already reused. Unsorted `pad=batch`
does not help because almost every batch of 16 contains a 512-token pair.
Length-bucketed pad-to-batch + 8 threads was ~1729 ms vs ~5571 ms baseline
on 104 synthetic `cs_v1_control` pairs (`max_abs_diff = 0` vs pad-512 on
that synthetic set). V2-DEVSET-001 was **not** re-scored.

`CrossEncoderReranker()` defaults are **unchanged**. Optional `fast=True`
exists but E-L10 must keep defaults until ChatGPT authorizes a
score-preserving switch.

## Pack layout

```
CLAUDE-HANDOFF.md
experiments/EXP-015/scripts/cross_encoder.py
experiments/EXP-015/models/cross-encoder-ms-marco-MiniLM-L6-v2/233902d25c440f23af6f7d6e94d2946bac0bee0a/
  config.json
  tokenizer.json
  tokenizer_config.json
  special_tokens_map.json
  vocab.txt
  onnx/model.onnx
experiments/EXP-018B/scripts/run_exp018b.py
experiments/EXP-018B/scripts/local_bm25_batched.py
experiments/EXP-018B/EXP-018B-results.json
experiments/EXP-018B/CE-LATENCY-AUDIT.md
experiments/EXP-018B/CE-LATENCY-AUDIT.json
experiments/EXP-018B/ce-latency-microbench.json
experiments/EXP-018B/ce-latency-microbench-followup.json
evals/gold/v2-devset-001.jsonl
evals/splits/v2-devset-001/development.json
experiments/RAG-V2/V2-DEVSET-001/V2-DEVSET-001-FREEZE.json
experiments/RAG-V2/V2-DEVSET-001/V2-DEVSET-001-FREEZE.manifest.json
```

## GitHub

Intended branch: `grok/ce-latency-handoff` on
`https://github.com/Ryork67677/nyxora-outcome-intelligence.git`

Created from a **separate git worktree** of
`origin/claude/rag-v1-build-experiments-5yngul` so the frozen Windows
checkout HEAD stays at e65912a. No force-push. No PERF-002 commit.
If `model.onnx` is rejected for size, the branch ships everything except
ONNX; take ONNX from the tarball or HF revision
`233902d25c440f23af6f7d6e94d2946bac0bee0a`.
