# EXP-010 preregistration — recorded BEFORE building the chunker or running any cell

## 1. Hypothesis

If transformer retrieval quality is limited by truncation, then restructuring
retrieval units so a complete unit fits inside the encoder's 512-token window
should improve retrieval **relative to running the same transformer at 512 on the
existing control chunks** (EXP-009 cell B/C).

The experiment must be able to falsify this. Encoder alignment is **not** assumed
to help.

## 2. What is held fixed

Same encoder as EXP-009, with no substitution and no sweep:
`sentence-transformers/all-MiniLM-L6-v2`, ONNX fp32, bundle sha256
`913d7300ceae3b2dbc2c50d1de4baacab4be7b9380491c27fab7418616a16ec3`, attention-masked
mean pooling, L2 normalization, cosine, exact search, no ANN, no query/document
prefix, 512-token window.

Also frozen: the 22 evidence anchors, the 20 scored questions, BM25 `k1=1.2`
`b=0.75` on the `simple` configuration, `top_k=10`, probe depths 10/20/50/100/300,
and the preregistered RRF parameters (pool 50 per retriever, `rrf_k` 60, final
top_k 10). No enrichment, no reranker, no query rewriting or expansion.

## 3. Encoder token budget — measured, not assumed

Measured directly from the shipped tokenizer and model config rather than assumed:

| quantity | value | how it was determined |
|---|---|---|
| `max_position_embeddings` | 512 | `config.json` |
| `model_max_length` | 512 | `tokenizer_config.json` |
| special-token overhead | **2** | encoded `"alpha beta gamma"` with and without special tokens: 5 − 3 = 2 (`[CLS]` … `[SEP]`) |
| **usable payload** | **510** | 512 − 2 |
| target payload | **448** | conservative; see §4 |
| hard payload cap | **480** | 30 tokens of headroom below 510 |

Note: `tokenizer.json` ships its own saved truncation of **128**, which
`Tokenizer.from_file` restores. EXP-009 was bitten by this. The chunker and every
gate must therefore set truncation explicitly and never rely on the loaded default.

## 4. Why the target is high, not low

EXP-005 (chunk size × BM25) and EXP-008 (chunk size × dense) both failed by making
chunks generically shorter. EXP-008 specifically showed that splitting a long but
topically coherent unit **hurts** dense retrieval. Shortness is therefore not the
objective here.

The objective is: **the largest coherent unit that the encoder can see completely.**
A 448-token target sits near the top of the window rather than near the bottom, so
units are split only when they would otherwise be truncated.

## 5. Boundary priority (declared in advance)

section/subsection → paragraph → parameter/reference unit → list group →
table row group → code unit → sentence → hard token boundary (last resort only).

All limits are measured in the encoder's own WordPiece tokenization. Character
counts, whitespace word counts and other tokenizers are not used for any limit.

## 6. Carryover context at forced splits

Only where a semantic unit had to be split:

* continuation parts carry their section heading (one short line);
* table row groups after the first carry the table header and separator rows.

EXP-006 showed that broad repetitive prefixes (`Provider: Anthropic`) inflate
document frequency and damage BM25. Carryover here is therefore narrow, applied
only to forced continuations, and never to whole-unit chunks. The canonical
`chunk.text` is never mutated: carryover lives in `context_header` / `search_text`,
and `char_start`/`char_end` continue to denote the exact source span.

## 7. Cells

| cell | chunks | retriever | purpose |
|---|---|---|---|
| A | control | BM25 | reproduce frozen baseline (0.475 / 9-of-20 / 10-of-22) |
| B | control | transformer @512 | reproduce EXP-009 (≈0.575 / 11-of-20) |
| C | control | BM25 + transformer RRF | reproduce EXP-009 best (≈0.775 / 15-of-20 / 17-of-22) |
| D | **encoder-aligned** | transformer @512 | the isolated intervention |
| E | BM25 on **control** + transformer on **encoder-aligned** | RRF | mixed representation |

If A, B or C fails to reproduce, stop and diagnose before interpreting D or E.

## 8. Cross-representation fusion identity

In cell E the two retrievers return chunks from different chunk sets, so chunk_id
cannot be the deduplication key. Two candidates are the same evidence region when
they share `version_id` **and** `section_path` **and** their `[char_start, char_end)`
spans overlap. Fusion keeps the best (lowest) rank per retriever for a region, so a
region cannot be double-rewarded merely for existing in two representations. The
rule is deterministic and is recorded with the results.

## 9. Preregistered readings

n = 20 scored questions / 22 spans. One case = 5 percentage points. No significance
claims.

| outcome | reading |
|---|---|
| D > B by ≥ 2 cases (≥ 0.10) | encoder alignment supported as a retrieval-unit design principle |
| D within ±1 case of B | no measurable effect at this sample size |
| D < B | alignment **hurts**; truncation correlated with EXP-009 movement but was not causal |
| E > C with no or very limited regressions | different retrievers have earned different representations |
| D improves depth (absent/>100 → 15–50) without top-10 gain | retrieval is entering rerankable range; freeze and consider EXP-011 |

**Zero-regression watch.** EXP-009's fused cell achieved +6 cases over BM25 and +4
over EXP-007C with *zero* regressions. That property is now a quality
characteristic in its own right. If EXP-010 raises macro recall but introduces
losing cases relative to EXP-009, that will be reported prominently and EXP-010
will **not** be called an unconditional improvement.

Tracked individually regardless of aggregate: **AN-003**, **AN-002**, **AN-007**,
**OA-004**.

## 10. Promotion

The frozen production baseline stays control chunks / no enrichment / BM25 /
`top_k=10` unless EXP-010 outperforms the current strongest configuration
(0.775 / 15-of-20). Neither EXP-009 @512 nor EXP-010 is promoted automatically.

## 11. Not done in this experiment

No reranker. No encoder-window sweep (512 is fixed from EXP-009; the chunker's
conservative target is an ingestion constraint, not a retrieval hyperparameter).
No second transformer. No new golden questions. No BM25 tuning. No ANN. No
enrichment. Prior experiment artifacts and chunk sets are immutable.

---

# Addendum — chunker construction, recorded before the chunker was built

A literal reading of "build an encoder-aligned chunker" would re-chunk the corpus
from source with a ~448-token target. That would change **two** things at once
relative to cell B: how oversized units are split *and* how already-fitting units
are grouped. D vs B would then no longer isolate encoder alignment, which is the
whole point of the cell.

So the encoder-aligned chunk set is **derived from the control chunking**:

* a control chunk whose payload already fits the window is passed through
  **byte-identical** — same source span, same text, same content hash;
* a control chunk that exceeds the window is split at structural boundaries into
  pieces targeting **448** payload tokens, hard cap **480**.

This satisfies the design intent — *every normal retrieval unit is completely
visible to the encoder* — while changing exactly one thing: units the encoder
could not previously see whole. Units that already fitted are untouched, so any
movement in D is attributable to the truncation fix and not to re-grouping.

It also directly serves the §11 warning that shortness is not the objective, and
the §26 topical-coherence check: coherent units that already fitted cannot be
fragmented by this intervention, because they are not touched at all.

Consequence to expect in the diagnostics: the encoder-aligned set will have
**more** chunks than the control (oversized units become several), not fewer, and
its token distribution will be the control's with the >480 tail folded down.
