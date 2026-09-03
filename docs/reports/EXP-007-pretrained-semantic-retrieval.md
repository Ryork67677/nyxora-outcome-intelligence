# Production RAG — EXP-007 Pretrained Semantic Retrieval

## 1. Executive result

**The vocabulary-mismatch hypothesis was not supported, but hybrid retrieval earned
promotion on the measurements.**

A genuinely pretrained embedding model was obtained and tested. Standalone it is
**worse** than BM25 (0.425 vs 0.475 macro recall) and much worse at deep
reachability — 5 evidence spans unreachable at depth 300 against BM25's 1. It
rescued two questions and regressed three.

Crucially, **neither rescue was a vocabulary-mismatch rescue.** Both rescued spans
already contained ≥92% of their query terms; dense retrieval corrected a BM25
*ranking* failure, not a lexical *coverage* failure. And **AN-003 — the canonical
vocabulary-mismatch case this experiment exists for — was not rescued**, remaining
absent at depth 300.

The unexpected result is fusion. **BM25 + dense RRF reaches 0.600 macro recall and
11/20 fully recalled** — the best measured configuration in the project's history —
because the two retrievers fail on different questions. That is complementarity
(decision-gate Outcome C), not a validation of the semantic hypothesis.

Artifacts: `experiments/EXP-007/results.json`,
`experiments/EXP-007/semantic-contribution.json`,
`experiments/EXP-007/model-preregistration.md`,
`experiments/EXP-007/embedding-build.json`.

---

## 2. Why semantic retrieval was tested

Two architectural hypotheses had already been diagnosed, tested by controlled
intervention, and falsified. The surviving explanation was that BM25 cannot retrieve
evidence which shares no useful lexical terms with the query. EXP-007 tests it.

## 3. Prior hypotheses that were falsified

| Hypothesis | Intervention | Result |
|---|---|---|
| Oversized chunks hide evidence (EXP-005) | max chunk 16,096 → 1,999 chars; 3,069 over-2,000 chunks → 0 | **0 questions rescued**; 8 span ranks up, 9 down |
| Missing structural context (EXP-006) | 2×2 with identical boundaries and bodies | **Δ0.000** macro recall; 1 rescued, 1 regressed |

## 4. The surviving hypothesis

> Some retrieval failures are caused by lexical vocabulary mismatch that BM25 cannot
> bridge, and a genuinely pretrained semantic embedding model may recover evidence
> that lexical retrieval cannot reach.

---

## 5. Model selected, and why

Selection was recorded in `experiments/EXP-007/model-preregistration.md` **before any
EXP-007 result was observed**, so it cannot be a post-hoc pick.

| field | value |
|---|---|
| provider | `gensim-data` GitHub release asset |
| identifier | `fasttext-wiki-news-subwords-300` |
| origin | facebookresearch/fastText, wiki-news-300d-1M-subword |
| revision | sha256 `be48d40d…a836552` |
| training corpus | Wikipedia 2017 + UMBC webbase + statmt.org news (~16B tokens) |
| vocabulary / dimension | 999,999 / 300 |
| pooling | mean of L2-normalized in-vocabulary token vectors |
| normalization / metric | L2 / cosine |
| query & document prefix | none (this model defines no task instruction) |

Chosen a priori because it is trained with **subword information**, which directly
addresses the plural/singular failure mode named in the brief. The model confirms
this: `cos(request, requests) = 0.827` — exactly the bridge the unstemmed lexical
configuration cannot make.

### Why not a transformer retrieval encoder

Measured, not assumed: `huggingface.co` returns `CONNECT tunnel failed, response
403`; `api.openai.com`, `api.voyageai.com` and `api.cohere.com` are equally blocked;
no embedding credential exists. GitHub release assets and PyPI *are* reachable, which
is how a pretrained model was obtained at all. Falling back to corpus-fitted
TF-IDF+SVD was explicitly forbidden and was not done.

### Instrument strength — this qualifies every negative result below

This is a genuinely pretrained model but a **static word-embedding** one, not a
transformer retrieval encoder. Mean-pooled static vectors are order-insensitive and
wash out over long chunks. The asymmetry matters:

* A **positive** result would be strong evidence — a weak instrument finding signal
  is convincing.
* The **negative** result obtained is **weak** evidence against the hypothesis. It
  shows this *class* of embedding cannot bridge the gap, not that a transformer
  could not. **The vocabulary-mismatch hypothesis is unsupported, not falsified.**

---

## 6. Experimental controls

Frozen: the 202 document versions, the control chunker, **no enrichment**, canonical
raw chunk bodies, the same 20 scored questions and 22 evidence spans, the same
anchors `(version_id, section_path, char_start, char_end)`, the same BM25
implementation and parameters, `top_k = 10`.

Not added: reranker, query rewriting, query expansion, synonyms, stemming, new
chunker, new metadata scheme, table-row splitting.

**Exact search, not ANN.** No HNSW or IVFFlat index exists on `chunk_embedding`;
`EXPLAIN ANALYZE` confirms a full scan at ~33 ms/query over 14,209 vectors. EXP-007
measures embedding quality, not index quality.

**Embedding storage** uses the existing model-versioned table, cached by
`(model_id, content_hash)`. Build: 14,209 chunks, 16 MB, 96.3% token coverage,
17.8 s model load + 14.9 s embed. 117 chunks (0.8%) produced all-zero vectors —
no in-vocabulary token, mostly pure-symbol code — and can never be retrieved by dense.

### A reproducibility defect found and fixed

A determinism test written for this phase **failed**: dense ranking was not
reproducible. Four chunks tied at cosine 0.941729 (the corpus repeats identical
documentation text across pages) and `ORDER BY embedding <=> q` let the plan decide
their order. This is the same class of defect fixed for BM25 in EXP-005; the distance
is now rounded before sorting so exact ties resolve on `chunk_id`. Verified stable
across three runs. Results are unchanged by the fix.

---

## 7. EXP-007A — BM25 reproduction gate

| metric | frozen baseline | EXP-007A |
|---|---:|---:|
| macro span recall | 0.475 | **0.475** |
| fully recalled | 9/20 | **9/20** |
| spans @10 | 10/22 | **10/22** |
| document recall | 0.825 | **0.825** |

Per-case recall **and hit ordering** are identical to the committed EXP-000 artifact.
Gate passed; EXP-000 artifacts untouched.

---

## 8. Dense results

| configuration | macro recall | fully recalled | spans@10 | doc recall | MRR | absent@10 | @20 | @50 | @100 | @300 | ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **A** BM25 control | 0.475 | 9/20 | 10/22 | 0.825 | 0.280 | 12 | 8 | 3 | 2 | **1** | 381 |
| **B** pretrained dense | **0.425** | 8/20 | 9/22 | **0.725** | **0.360** | 13 | 9 | 9 | 7 | **5** | 62 |
| **C** BM25+dense RRF | **0.600** | **11/20** | **13/22** | 0.825 | 0.326 | **9** | 8 | 5 | 2 | 2 | 413 |

By category, dense **ties** BM25 on `exact_lookup` (0.538 both), ties on `multi_hop`
(0.250) and `version_conflict` (0.500), and is **worse** on `normal` (0.000 vs 0.500).
Both score 0.000 on the single `ambiguous` case. By provider, dense is better on
Anthropic (0.292 vs 0.167) and clearly worse on OpenAI (0.625 vs 0.938). RRF lifts
`exact_lookup` to 0.692 and Anthropic to 0.458. **These groups contain 1–13 questions
each; no statistical claim is made from any of them.**

Two things stand out. Dense has the **highest MRR (0.360)** despite the lowest macro
recall — when it finds evidence it ranks it very high, often rank 1–2. And its deep
reachability is **much worse**: 5 spans unreachable at depth 300 versus BM25's 1.

---

## 9. BM25 vs dense — paired comparison

**Net −1: 2 rescued, 3 regressed, Δ macro −0.050.**

| quadrant | cases |
|---|---|
| BM25 correct / dense correct | AN-009, OA-001, OA-002, OA-003, OA-005, OA-008 (6) |
| BM25 correct / **dense wrong** | AN-005, OA-004, OA-007 (3) |
| **BM25 wrong** / dense correct | AN-002, AN-007 (2) |
| both wrong | AN-001, AN-003, AN-004, AN-006, AN-008, AN-010, AN-011, AN-012, OA-006 (9) |

Per-span rank, BM25 → dense → RRF:

| case | BM25 | dense | RRF | | case | BM25 | dense | RRF |
|---|---:|---:|---:|---|---|---:|---:|---:|
| AN-001 | 19 | 242 | 39 | | AN-011 | 54 | 14 | 29 |
| AN-002 | 27 | **1** | 2 | | AN-012 | 47,117 | 1,— | 2,— |
| AN-003 | — | — | — | | OA-001 | 4 | 1 | 2 |
| AN-004 | 12 | 17 | **4** | | OA-002 | 2 | 1 | 2 |
| AN-005 | 4 | **—** | 8 | | OA-003 | 6 | 1 | 3 |
| AN-006 | 29 | 63 | 56 | | OA-004 | 5 | **73** | 17 |
| AN-007 | 18 | **2** | 4 | | OA-005 | 3 | 1 | 1 |
| AN-008 | 12 | 123 | 25 | | OA-006 | 1,29 | 18,— | 2,55 |
| AN-009 | 1 | 1 | 1 | | OA-007 | 1 | 11 | 2 |
| AN-010 | 49 | — | 97 | | OA-008 | 1 | 10 | 1 |

---

## 10. Semantic contribution — what dense actually bought

This is the most important finding in EXP-007, and it is negative for the hypothesis.

| rescued case | BM25 → dense | lexical overlap of the evidence chunk | mechanism |
|---|---|---:|---|
| AN-002 | 27 → **1** | **12/13 (0.923)** | topical coherence, not a vocabulary gap |
| AN-007 | 18 → **2** | **11/12 (0.917)** | topical coherence, not a vocabulary gap |

Mean lexical overlap of dense-rescued spans: **0.920**. The query terms were *already
present*. Both spans live in the same 3,327-character `HTTP errors` chunk — a
topically homogeneous list of HTTP status codes. BM25 ranked it 27th and 18th because
its length normalization penalises a long chunk; dense matched the chunk's overall
topic to the query's topic and put it at rank 1 and 2.

**So dense fixed a BM25 length-normalization failure, not a vocabulary failure.** No
rescue in EXP-007 is attributable to bridging missing vocabulary.

Regressions, classified:

| case | BM25 → dense | overlap | mechanism |
|---|---|---:|---|
| AN-005 | 4 → **absent@300** | 3/7 (0.429) | exact-identifier lookup — the answer *is* the literal `context-management-2025-06-27`; static vectors carry no useful representation for such a token, and a 325-char chunk gives no topical signal either |
| OA-004 | 5 → 73 | 11/14 (0.786) | pooled-vector dilution — terms present, but a 1,251-char loop description does not resemble the query's phrasing |
| OA-007 | 1 → 11 | 8/12 (0.667) | boundary regression — a top-ranked lexical hit pushed just outside `top_k` |

---

## 11. AN-003 deep dive — the canonical case

**Query:** "How many requests can a single Message Batches create request contain at
most?" **Evidence:** *"There is a limit of 100,000 messages in a single request."*

| retriever | evidence rank | doc rank | @10 | @20 | @50 | @100 | @300 |
|---|---:|---:|---|---|---|---|---|
| BM25 | — | 6 | no | no | no | no | **no** |
| **dense** | **—** | **1** | no | no | no | no | **no** |
| RRF | — | 1 | no | no | no | no | no |

**Outcome: failure.** Pretrained embeddings did not solve the canonical
vocabulary-mismatch case.

But the trace shows *why*, and it is not what the hypothesis predicted. Dense placed
the correct **document at rank 1** (BM25: rank 6), and its top five hits were all
`Create a Message Batch` chunks at cosine **0.9417**:

```
r1 sim=0.9417 len=436  ['Batches', 'Create a Message Batch']
r2 sim=0.9417 len=436  ['Create a Message Batch']
r3 sim=0.9417 len=436  ['Batches', 'Create a Message Batch']
r4 sim=0.9417 len=436  ['Batches', 'Create a Message Batch']
r5 sim=0.9401 len=620  ['Message Batches API', 'How to use the Message Batches API']
TARGET       len=3449  ['Batches', 'Create a Message Batch', 'Body Parameters']
```

**The model did semantically associate the query with the right material.** It failed
to surface the answer-bearing chunk because that chunk is 3,449 characters of
heterogeneous parameter documentation, and its mean-pooled vector is dominated by
parameters unrelated to the question.

The evidence never entered a rerankable range under any configuration, so **a
reranker could not rescue AN-003.**

### A new, testable observation

Chunk length predicts dense reachability in a way it did not predict BM25
reachability:

| dense outcome | n | median chunk length |
|---|---:|---:|
| reachable @300 | 17 | 897 chars |
| **unreachable** | 5 | **1,754 chars** (tail: 2,317 and 3,449) |

EXP-005 showed chunk size did **not** matter for BM25. This suggests it **does**
matter for dense retrieval. That is a new hypothesis generated by EXP-007, not a
conclusion of it — and note AN-002/AN-007 are a counterexample to a naive length rule
(3,327 chars, ranked 1 and 2), so the operative variable is more likely *topical
homogeneity* than raw length.

---

## 12. RRF results and whether fusion earned promotion

Preregistered before any EXP-007C result: candidate pool **50** per retriever,
`rrf_k = 60`, final `top_k = 10`. Not tuned; no sweep was run.

| comparison | Δ macro | rescued | regressed | net |
|---|---:|---|---|---:|
| BM25 → RRF | **+0.125** | AN-002, AN-004, AN-007 | OA-004 | **+2** |
| dense → RRF | **+0.175** | AN-004, AN-005, OA-007 | — | **+3** |

RRF at **0.600 / 11-of-20** is the best configuration measured in this project. It
beats both parents, and it restores what each one broke: AN-005 (dense lost it
entirely) returns at rank 8, OA-007 returns at rank 2.

**The fusion regression the brief warned about did occur.** OA-004: BM25 rank 5,
dense rank 73, **RRF rank 17** — outside `top_k`. A good lexical result was dragged
out of the top 10 by a weak dense rank, exactly the EXP-003 failure pattern. It is one
case, and it is reported rather than absorbed into the average.

RRF also inherits dense's deep-reachability loss: 2 spans absent@300 versus BM25's 1.

---

## 13. EXP-NULL — still blocked

Retried on this environment. Still fails: no generation credential
(`OpenAIError: Missing credentials`) and the provider host is egress-blocked. The
results file records `status: "blocked"` with the exact error and per-case
`status: "not_run"`. **Retrieval remains uncalibrated against what the model already
knows.** No closed-book/RAG quadrant classification is possible.

---

## 14. Limitations

1. **The instrument is weak.** Static word vectors, not a transformer retrieval
   encoder, because every transformer host is egress-blocked. The negative result is
   weak evidence against the hypothesis; a transformer might still bridge AN-003.
2. **n = 20.** One case is **five percentage points** of macro recall. Every movement
   here is 1–3 cases. No statistical significance is claimed, and nothing here shows
   "dense beats BM25" or "BM25 beats dense" in general — only how they behaved on
   these 20 questions.
3. **Mean pooling is a crude sentence representation** and is order-insensitive.
   Some dense failures are attributable to pooling rather than to the vectors.
4. **117 chunks (0.8%) have all-zero embeddings** and are unreachable by dense.
5. **EXP-NULL never ran**, so retrieval lift over model prior knowledge is unknown.
6. **Corpus skew persists:** 139 Anthropic documents to 63 OpenAI.
7. **No parameter was swept.** BM25 `k1`/`b` and the RRF configuration are fixed
   values; if any sweep is run later it must be labelled development-set tuned.

---

## 15. Updated root-cause conclusion

Three hypotheses have now been tested by controlled intervention:

| # | hypothesis | verdict |
|---|---|---|
| 1 | Oversized chunks hide evidence | **falsified** (0 rescued) |
| 2 | Missing structural context | **falsified** (Δ0.000) |
| 3 | Lexical vocabulary mismatch | **unsupported** — no rescue was a vocabulary rescue, and the canonical case failed |

What EXP-007 *did* establish is different from what it set out to test: **BM25 and
dense retrieval fail on disjoint questions.** BM25 is stronger on exact identifiers
and deep reachability; dense is stronger when a whole chunk is topically coherent and
BM25's length normalization buries it. Fusing them is worth more than either.

The residual failures now look less like a vocabulary problem and more like a
**retrieval-unit problem**: AN-003's evidence is a 57-character sentence inside a
3,449-character heterogeneous chunk, and *both* retrievers fail on it for their own
reasons — BM25 because the discriminative terms are absent, dense because the pooled
vector is diluted. EXP-005 tested chunk size against BM25 alone and found nothing;
it has never been tested against dense retrieval.

---

## 16. What the measurements justify next

1. **Bounded chunking × dense retrieval.** The single strongest lead. EXP-005 already
   built and validated the bounded chunk set; EXP-007 shows dense reachability tracks
   chunk size. This is a cheap 2×2 against an existing artifact, and it directly
   targets AN-003.
2. **A transformer retrieval encoder, if egress ever permits.** The hypothesis is
   unsupported, not falsified, and the instrument is the reason. AN-003 stays the
   canonical test case.
3. **Do not add a reranker.** AN-003 is absent at depth 300 under every configuration
   including fusion; a reranker reorders candidates and cannot retrieve what
   retrieval never found. The Outcome-B condition that would justify one — evidence
   routinely present at rank 15–100 but not top 10 — is not what the data shows.

### Promotion decision

**The frozen production baseline does not change: control chunking, no enrichment,
BM25, `top_k = 10`.**

RRF is the best-measured configuration (0.600, 11/20, +2 net over BM25) and is a
genuine candidate — but it is a **+2-case movement on a 20-case development set**,
it carries a real regression (OA-004 falls out of the top 10), and it doubles query
latency. That is not enough evidence to change a production baseline. The honest
status is: **hybrid retrieval is the leading candidate for promotion, pending a
larger evaluation set.** No component is promoted for being standard RAG architecture.
