# EXP-009 model selection — recorded BEFORE running the experiment

Written and committed before any EXP-009 retrieval result was observed, so the
choice of encoder cannot be a post-hoc selection of whichever model happened to win.

## 1. Preflight, re-measured (not assumed from EXP-007)

The EXP-007 and EXP-008 reports concluded that no transformer encoder was
obtainable. That conclusion was **re-tested rather than inherited**, because the
egress policy can change between sessions.

### Network egress, probed 2026-08-18

| host | result |
|---|---|
| `huggingface.co` | **blocked** — `CONNECT tunnel failed, response 403` |
| `cdn-lfs.huggingface.co` | **blocked** — 403 at CONNECT |
| `hf-mirror.com` | **blocked** — 403 at CONNECT |
| `api.openai.com` | **blocked** — 403 at CONNECT |
| `api.cohere.ai` / `api.cohere.com` | **blocked** — 403 at CONNECT |
| `api.voyageai.com` | **blocked** — 403 at CONNECT |
| `storage.googleapis.com` | **blocked** — 403 |
| `dl.fbaipublicfiles.com` | unreachable |
| `tfhub.dev`, `kaggle.com`, `sbert.net` | unreachable |
| `cdn.jsdelivr.net` | unreachable |
| `pypi.org`, `files.pythonhosted.org` | **reachable** (proxy `noProxy` direct) |
| `github.com` release assets, `raw.githubusercontent.com` | **reachable** (HTTP 206) |
| `chroma-onnx-models.s3.amazonaws.com` | **reachable** (HTTP 206) |

The proxy status endpoint independently confirms the denials as
`connect_rejected: gateway answered 403 to CONNECT (policy denial or upstream
failure)` for the Hugging Face and embedding-API hosts.

### Local state

| checked | result |
|---|---|
| installed packages | 50 packages; **no** `torch`, `transformers`, `sentence-transformers`, `onnxruntime` |
| `~/.cache/huggingface`, `/root/.cache/huggingface`, `~/.cache/torch` | do not exist |
| any `.safetensors` / `.onnx` / `pytorch_model.bin` on disk | none |
| repo model cache | only the EXP-007 FastText artifacts |
| credentials for an embedding API | none — no `OPENAI_*`, `HF_*`, `COHERE_*`, or `VOYAGE_*` variable is present |

No credential was fabricated, printed, or hardcoded. Only environment variable
*names* were listed; no value was read or emitted.

### What changed since EXP-007

Hugging Face is still blocked, but a **different distribution path is reachable**:
package indexes and object storage that redistribute pretrained weights outside
Hugging Face. `onnxruntime` and `tokenizers` install from PyPI, and a full
ONNX export of a sentence-transformer bi-encoder is retrievable from the Chroma
model bucket. EXP-009 is therefore **not blocked**, and no FastText fallback is
needed or permitted.

## 2. Selected model — one encoder, chosen before any result

| field | value |
|---|---|
| model identifier | `sentence-transformers/all-MiniLM-L6-v2` |
| distribution used | `https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz` |
| bundle sha256 | `913d7300ceae3b2dbc2c50d1de4baacab4be7b9380491c27fab7418616a16ec3` |
| `model.onnx` sha256 | `4f148ba8ae9c2c7fbee4af2b132db8d06c6a6545b47fc83bbb98c3d22b8393e6` |
| `tokenizer.json` sha256 | `da0e79933b9ed51798a3ae27893d3c5fa4a201126cef75586296df9b4d2c62a0` |
| architecture | `BertModel`, 6 layers, hidden 384, 12 heads, intermediate 1536, vocab 30,522 |
| parameters | ~22.7M |
| precision | **fp32, not quantized** — verified: zero `QuantizeLinear` / `DequantizeLinear` / `MatMulInteger` / `DynamicQuantizeLinear` nodes in the graph |
| graph inputs | `input_ids`, `attention_mask`, `token_type_ids` (int64) |
| graph output | `last_hidden_state` `[batch, seq, 384]` — pooling is performed by this repo, not baked in |
| dimensions | 384 |
| tokenizer | `BertTokenizer` WordPiece, `do_lower_case=true`, vocab 30,522 |
| pooling | attention-mask-weighted **mean** over `last_hidden_state` |
| normalization | L2 on the pooled vector |
| distance metric | cosine, **exact** search (no HNSW/IVFFlat index) |
| query prefix | **none** — this model is symmetric and defines no task instruction |
| document prefix | **none** |
| max sequence length | **256 WordPiece tokens** (the reference `sentence_bert_config.json` value for this model) |
| corpus fitted | **False** — weights are frozen, nothing is fitted to this corpus or these questions |
| library | `onnxruntime` 1.29.0, `tokenizers` 0.23.1 |

Why this model: it is a genuine **contextual pretrained transformer retrieval
encoder** — a bi-encoder contrastively trained on ~1B sentence pairs explicitly
for semantic search, which is precisely the instrument EXP-007 lacked. It was
selected because it is the only such encoder reachable from this environment,
not because of any measured retrieval score.

## 3. Declared provenance limitation

The canonical Hugging Face repository is unreachable, so the bundle's checksum
**cannot be verified against the upstream publisher**. Provenance rests on a
third-party redistribution. Two independent structural checks are recorded
instead, and both are reported whatever they show:

1. `config.json` carries `_name_or_path: sentence-transformers/all-MiniLM-L6-v2`
   and matches the published architecture exactly.
2. A behavioural instrument check on held-out sentence pairs (below), run before
   any golden-set evaluation, confirming the weights behave like a trained
   sentence-similarity encoder rather than an untrained or plain-MLM BERT.

This is a real weakness in the chain of custody and is reported as such.

## 4. Declared confound: sequence truncation

Control chunks are long (max 16,096 characters). At 256 WordPiece tokens
(~1,000 characters) most control chunks will be **truncated**, so the encoder
will not see all of the text BM25 indexes. This is a property of the model as
published, not a defect introduced here.

* **Primary configuration** is the reference one: `max_seq_length = 256`.
* A **preregistered sensitivity run** at `max_seq_length = 512` (the model's
  positional limit) will also be reported. It is declared here, in advance,
  precisely so it cannot become post-hoc tuning; it does **not** redefine the
  primary result.
* Truncation coverage (fraction of chunk characters actually seen) will be
  measured and reported, including for the specific evidence spans.

## 5. Preregistered predictions and falsification criteria

The hypothesis under test: *a contextual pretrained transformer retrieval encoder
outperforms the static mean-pooled FastText retriever on the frozen control chunks.*

| outcome | reading |
|---|---|
| EXP-009C macro span recall > 0.425 (FastText) by ≥ 2 cases (≥ 0.10) | hypothesis supported |
| EXP-009C within ±1 case of 0.425 | no measurable difference at n=20 |
| EXP-009C < 0.425 | hypothesis **falsified** for this corpus and question set |
| EXP-009D ≤ EXP-007C (0.600, 11/20) | the transformer adds nothing over the FastText fusion already in hand |

n = 20 questions / 22 evidence spans. One case is worth 5 percentage points. No
significance claim will be made at this sample size, and a difference of one case
will not be reported as an improvement.

Additional falsification checks, declared in advance:

* AN-003, unreachable at depth 300 for BM25 and for FastText, is the single
  hardest case. If the transformer also fails it, the vocabulary-mismatch story
  is not a pooling artifact.
* The three cases FastText won (AN-002, AN-007, AN-012) will be checked
  individually; a transformer that wins on aggregate while losing all three would
  indicate a different mechanism, not a strictly better encoder.
* OA-004 regressed under EXP-007 fusion and is tracked explicitly.

## 6. Frozen — not to be changed by this experiment

Chunker, chunk size, enrichment, BM25 `k1`/`b`, `simple` (unstemmed) text-search
configuration, query rewriting/expansion, golden questions, evidence anchors, and
the RRF parameters preregistered in EXP-007 (pool 50, `rrf_k` 60, `top_k` 10).
No reranker will be implemented. The reranker decision gate produces counts only.
