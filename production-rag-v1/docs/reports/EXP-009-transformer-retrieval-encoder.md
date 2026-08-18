# EXP-009 — Does a contextual transformer retrieval encoder beat static vectors?

**Status: partially supported — the preregistered accuracy bar was not met, but a
clear causal mechanism was identified.**

## 1. The question

EXP-007 tested whether a pretrained embedding model could bridge the vocabulary
mismatch that BM25 cannot. It could not obtain a transformer, so it used
mean-pooled static FastText vectors and labelled the result honestly: an
order-insensitive bag of word vectors is a **weak instrument**, so its negative
result was weak evidence rather than a falsification. EXP-008 then showed that
shortening chunks made the static encoder *worse*, implicating the pooling rather
than the chunk size.

EXP-009 supplies the instrument EXP-007 lacked.

## 2. What changed in the environment

The EXP-007 conclusion — "no transformer is reachable" — was **re-tested, not
inherited**. Hugging Face and every embedding API are still blocked at the egress
proxy (`403` at CONNECT, confirmed by the proxy's own failure log). But PyPI and
an ONNX redistribution bucket are reachable, so a genuine transformer encoder is
obtainable after all. EXP-009 was therefore **not blocked**, and no FastText
fallback was used.

## 3. The encoder

`sentence-transformers/all-MiniLM-L6-v2` — a 6-layer BERT bi-encoder,
contrastively trained on ~1B sentence pairs explicitly for semantic search.
384 dimensions, fp32, unquantized (verified: zero quantization nodes in the ONNX
graph). Attention-masked mean pooling, L2 normalized, cosine distance, exact
search with no ANN index. No query or document prefix — the model is symmetric
and defines no task instruction, so inventing one would be tuning.

Selected and committed in `experiments/EXP-009/model-preregistration.md` **before
any retrieval result was observed** (commit `adc73ae`).

### Declared provenance limitation

Hugging Face is unreachable, so the bundle **cannot be checksummed against the
upstream publisher**. Provenance rests on a third-party redistribution. This is a
real weakness in the chain of custody and is reported as such. Two independent
checks were recorded instead:

* **Structural** — architecture, precision, graph shape and tokenizer vocabulary
  all match the published model exactly.
* **Behavioural** — on held-out sentence pairs the encoder separates paraphrases
  from unrelated sentences by **0.468** cosine, and scores a paraphrase pair with
  **no shared content words** at **0.603**. A random or plain-MLM BERT would not.
  This is the instrument validity check EXP-007 could never pass.

The encoder is also bitwise deterministic and batch-composition independent:
every sequence is padded to a fixed width, so a chunk's vector does not depend on
which other chunks shared its batch.

## 4. Design

Five cells, all on the frozen control chunks and the frozen snapshot. Only the
encoder differs between B and C.

| cell | configuration |
|---|---|
| A | BM25 on control chunks (frozen baseline) |
| B | static FastText dense (reproduces EXP-007B) |
| C | **transformer dense** (the intervention) |
| D | **BM25 + transformer RRF** (preregistered pool 50, `rrf_k` 60, `top_k` 10) |
| E | BM25 + FastText RRF (reproduces EXP-007C — D's real comparator) |

### Reproduction gate

All three frozen baselines reproduced exactly before any new result was read.

| cell | expected | actual | |
|---|---|---|---|
| A BM25 | 0.475 / 9-of-20 / 10-of-22 | 0.475 / 9-of-20 / 10-of-22 | PASS |
| B FastText | 0.425 / 8-of-20 / 9-of-22 / MRR 0.360 / absent@300 5 | identical | PASS |
| E BM25+FastText RRF | 0.600 / 11-of-20 / 13-of-22 | identical | PASS |

## 5. Results

| cell | macro recall | fully recalled | spans@10 | doc recall | MRR | absent@300 | ms |
|---|---|---|---|---|---|---|---|
| A BM25 | 0.475 | 9/20 | 10/22 | 0.825 | 0.280 | 1 | 894 |
| B FastText dense | 0.425 | 8/20 | 9/22 | 0.725 | 0.360 | **5** | 617 |
| C **transformer dense** | **0.500** | **10/20** | **11/22** | **0.925** | 0.346 | **1** | 169 |
| D **BM25 + transformer RRF** | **0.625** | **12/20** | **14/22** | **0.925** | **0.423** | 2 | 681 |
| E BM25 + FastText RRF | 0.600 | 11/20 | 13/22 | 0.825 | 0.326 | 2 | 638 |

## 6. Verdict against the preregistered criteria

The preregistration required **≥ 0.10 (two cases)** over FastText to call the
hypothesis supported.

| comparison | delta | preregistered reading |
|---|---|---|
| C vs B (transformer vs static) | **+0.075** (1.5 cases) | **below the bar** — not "supported" |
| D vs E (fused) | **+0.025** (1 case) | within noise at n=20 |

**The headline accuracy claim does not clear its own preregistered threshold.**
At n=20 one case is 5 percentage points; no significance is claimed and a
one-case difference is not reported as an improvement.

What *is* robust is **reachability**, which does not depend on the top-10 cutoff:

* spans absent from the top 300 fell from **5 to 1**
* document recall rose from **0.725 to 0.925**
* the transformer is also **3.6× faster** per query than the static encoder

## 7. The transformer is not strictly better — it is differently better

The preregistration flagged this exact check: *"a transformer that wins on
aggregate while losing all three FastText wins would indicate a different
mechanism, not a strictly better encoder."*

**All three were lost.**

| case | FastText rank | transformer rank |
|---|---|---|
| AN-002 | 1 | 77 |
| AN-007 | 2 | 22 |
| AN-012 | 1, absent | 27, 189 |

## 8. Mechanism: the 256-token window, not the architecture

The encoder's reference window is 256 WordPiece tokens. Measured against the
control chunks:

* **35.3%** of chunks are truncated (5,008 of 14,209)
* the encoder sees only **51.3%** of all corpus tokens
* the median truncated chunk is **745 tokens** — nearly three windows long

Splitting the case-level movement by truncation makes the mechanism unambiguous:

| group | evidence chunk tokens | truncated? |
|---|---|---|
| **lost** AN-002 / AN-007 / AN-012 | 850 / 850 / 850, 382 | **all truncated** |
| **rescued** AN-005 / AN-008 / OA-006 / OA-007 | 93 / 216 / 232, 34 / 171 | **none truncated** |
| rescued AN-011 | 382 | truncated, still improved 14 → 5 |

The transformer wins wherever it can see the whole chunk and loses wherever the
answer sits past token 256. This is a property of the deployment window, not of
the architecture — and it is the first mechanism in this project that explains
*both* directions of movement with one variable.

A sensitivity run at the model's 512-token positional limit was preregistered
precisely so this could be tested rather than argued.

## 9. AN-003 — first contact

AN-003 ("How many requests can a single Message Batches create request contain at
most?") has been unreachable at depth 300 for every retriever in this project.

| retriever | rank |
|---|---|
| BM25 | absent |
| FastText dense | absent |
| **transformer dense** | **91** |
| BM25 + transformer RRF | absent |

The transformer is the first retriever to locate it at all on the control chunks.
It is still far outside `top_k`, and **fusion loses it again** — RRF pools only 50
candidates and 91 falls outside the pool. Its evidence chunk is 803 tokens, so the
encoder saw under a third of it.

## 10. OA-004 — the tracked fusion regression

| cell | rank |
|---|---|
| A BM25 | **5** (recalled) |
| B FastText | 73 |
| C transformer | 56 |
| D BM25 + transformer RRF | 14 |
| E BM25 + FastText RRF | 17 |

BM25 alone answers OA-004; every dense and fused configuration loses it. Fusion
improves its rank over dense alone but still cannot recover what BM25 had. This
regression has now survived three experiments and is the clearest standing cost
of fusion.

## 11. Reranker decision gate (counts only — no reranker was built)

A reranker can only reorder what retrieval already returned; spans absent from the
pool are unreachable by any reranker.

| cell | 1–10 | 11–30 | 31–50 | 51–100 | 101–300 | absent@300 | ceiling if perfect @100 |
|---|---|---|---|---|---|---|---|
| A BM25 | 10 | 7 | 2 | 1 | 1 | 1 | 0.909 |
| B FastText | 9 | 4 | 0 | 2 | 2 | 5 | 0.682 |
| C transformer | 11 | 4 | 0 | 4 | 2 | 1 | 0.864 |
| **D BM25 + transformer RRF** | **14** | 2 | 2 | 2 | 0 | 2 | **0.909** |
| E BM25 + FastText RRF | 13 | 3 | 1 | 3 | 0 | 2 | 0.909 |

For D, **6 of 22 spans** sit between ranks 11 and 100 — recoverable in principle
by a perfect reranker, for a ceiling of 0.909 against the measured 0.636 span
recall. That is the size of the prize, and it is a *ceiling*, not a forecast: no
reranker is perfect. The two spans absent at 300 are unreachable regardless.

**No reranker was implemented.** This section is a count.

## 12. What this changes

The best measured configuration is now **D — BM25 + transformer dense RRF, both on
control chunks: 0.625 macro span recall, 12-of-20 fully recalled, MRR 0.423**,
against the previous best of 0.600 (EXP-007C). That is a **one-case** improvement
and is explicitly *not* claimed as a real gain at n=20.

The frozen baseline is **unchanged**: control chunking, no enrichment, BM25,
`top_k = 10`. Nothing here clears the bar to move it.

## 13. Honest summary

* The hypothesis as preregistered — a transformer beats static vectors on accuracy
  — **did not clear its own threshold** (+0.075 against a required +0.10).
* The transformer is **not uniformly better**: it lost every case FastText won.
* The genuine finding is **mechanistic**: retrieval quality here is gated by how
  much of a chunk the encoder can see. 35% of chunks are truncated and half the
  corpus tokens are invisible to the encoder.
* Reachability improvements (absent@300 5 → 1, doc recall 0.725 → 0.925) are large
  enough not to be n=20 noise, unlike the top-10 accuracy deltas.
* EXP-007's negative result is now **superseded, not confirmed**: it was measured
  with an instrument this experiment shows to be the weaker one.

## 14. What was deliberately not done

No reranker, no query rewriting or expansion, no stemming, no confidence
threshold, no scalar identifier boost, no change to the chunker, chunk size,
enrichment, BM25 parameters, golden questions, evidence anchors, or the
preregistered RRF parameters. No prior experiment's artifacts were modified.

## 15. Defect found and fixed during this experiment

The first truncation measurement reported **0% truncation** on a corpus whose
largest chunk is 6,857 tokens. Cause: `Tokenizer.from_file` restores the
tokenizer's own saved 128-token truncation, so the "untruncated" reference length
was itself truncated. The **stored vectors were never affected** — the encoding
tokenizer's explicit 256 override was always correct — but the reported coverage
figure was wrong, and it was the figure the mechanism in §8 rests on. Fixed, and
pinned by a regression test.

## 16. Reproducibility

Snapshot `snap_689e336380a054d8039dc35b2c09cd0a`, chunk set `cs_v1_control`
(14,209 chunks), transformer model `emb_5197b67ea29a78cce96e91054d01d1dd`
(fingerprint `57240b5e0b41c89e`), FastText model
`emb_c11d8d9184d2ebc1ac60801a6452b884`. `onnxruntime` 1.29.0, `tokenizers` 0.23.1.
Full per-case results, rank movements, watchlists and gate counts in
`experiments/EXP-009/results.json`. 101 tests pass; ruff clean.
