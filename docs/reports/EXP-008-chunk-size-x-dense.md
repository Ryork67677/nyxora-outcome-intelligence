# Production RAG — EXP-008 Chunk Size × Dense Retrieval

## 1. Executive result

**The interaction hypothesis was not supported. The chunk-length correlation observed
in EXP-007 was not causal.**

Bounded chunking did not improve dense retrieval — it made it slightly **worse**
(macro recall 0.425 → 0.400), collapsed MRR from 0.360 to **0.259**, and left deep
reachability unchanged at 5 spans absent@300. The paired result is 1 rescued, 1
regressed, **net 0**, and both movements are single-rank boundary crossings.

The interaction runs the *wrong way*: chunk size moved BM25 by **+0.025** and dense by
**−0.025**, an interaction of **−0.050**. If anything, shortening the retrieval unit
helps lexical retrieval marginally and hurts this dense retriever.

One genuine partial success: **AN-003's answer-bearing chunk entered the dense
candidate pool for the first time in the project's history** (absent@300 → rank 119)
once its chunk fell from 3,449 to 1,191 characters. But rank 119 is far outside both
`top_k` and any practical rerank window, and it was offset exactly by AN-004 being
**lost entirely** (rank 17 → absent@300).

Per the decision gate this is **Outcome C**: stop optimising chunk size.

Artifacts: `experiments/EXP-008/results.json`,
`experiments/EXP-008/intervention-fidelity.json`,
`experiments/EXP-008/embedding-build-bounded.json`.

---

## 2. Why EXP-008 exists

EXP-005 tested chunk size against BM25 and found nothing. EXP-007 then noticed that
dense reachability appeared to track chunk length. Those are different interactions,
and a correlation observed inside one configuration is not evidence of a causal
mechanism. EXP-008 isolates it.

## 3. What EXP-005 concluded

Max chunk size 16,096 → 1,999 characters; chunks over 2,000: 3,069 → 0. **Zero**
questions rescued; 8 span ranks improved, 9 worsened. Smaller chunks did not
materially improve BM25 — which says nothing about dense retrieval.

## 4. The EXP-007 observation being tested

Median answer-bearing chunk length when dense could reach the evidence: ~897
characters. When it could not: ~1,754. AN-003's evidence sat in a 3,449-character
chunk, and dense had ranked its *document* first while never surfacing the chunk.

## 5. Hypothesis (pre-registered)

> If long heterogeneous chunks dilute mean-pooled dense vectors, bounded V2 chunks
> should improve dense evidence reachability and top-10 span recall relative to
> control dense retrieval.

Supported only if C→D shows meaningful paired improvement — not merely a small rise
in an average.

---

## 6. The 2×2

| | control chunks | bounded chunks |
|---|---|---|
| **BM25** | **A** — frozen baseline | **B** — EXP-005 intervention |
| **dense** | **C** — EXP-007 configuration | **D** — the new cell |

V3 was excluded deliberately: it bundles contextual enrichment and table transforms
that would confound the result. No enrichment anywhere. Pooling, tokenization, metric,
query representation and `top_k` are unchanged from EXP-007.

## 7. Intervention fidelity

`scripts/verify_exp008_fidelity.py` gates the experiment and passes:

| check | result |
|---|---|
| same document versions | 202 / 202, zero divergence |
| chunk bodies are exact source substrings | control ✓, bounded ✓ |
| contextual headers / enriched search text | **0 rows in both** |
| V3 table-row transforms | **0 in both** |
| evidence spans mapped | **22/22 in both** |
| **token vocabulary** | **identical — 32,011 forms, zero bounded-only** |

That last row matters: because V2 is a re-partition of the same normalized text with
boundaries on whitespace, the two chunkings present *exactly the same tokens* to the
embedding model. The only thing that changed is where the boundaries fall.

What did change:

| | chunks | mean | median | p90 | max | >2,000 |
|---|---:|---:|---:|---:|---:|---:|
| control | 14,209 | 1,097 | 508 | 3,466 | 16,096 | 3,069 |
| bounded | 20,526 | 757 | 917 | 1,193 | **1,999** | **0** |

**Embedding build (bounded):** same model, same fingerprint. 20,526 vectors, 40 MB,
21.0 s encode + 18.3 s model load, 0 cache hits / 20,526 misses on a clean rebuild,
token match rate **0.9627 — identical to control**. All-zero embeddings **117 → 128**;
on 44% more chunks that is a *fall* in rate from 0.82% to 0.62%.

---

## 8. A / B / C / D metrics

| cell | macro recall | fully recalled | spans@10 | doc recall | MRR | a@10 | a@20 | a@50 | a@100 | a@300 | ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **A** control + BM25 | 0.475 | 9/20 | 10/22 | 0.825 | 0.280 | 12 | 8 | 3 | 2 | **1** | 384 |
| **B** bounded + BM25 | 0.500 | 9/20 | 11/22 | 0.825 | 0.287 | 11 | 8 | 5 | 2 | **1** | 395 |
| **C** control + dense | 0.425 | 8/20 | 9/22 | 0.725 | **0.360** | 13 | 9 | 9 | 7 | **5** | 90 |
| **D** bounded + dense | **0.400** | 8/20 | 8/22 | **0.675** | **0.259** | 14 | 10 | 10 | 8 | **5** | 82 |

All three reproduction gates pass: **A** reproduces the frozen BM25 baseline
(0.475, 9/20), **B** reproduces EXP-005A (0.500, 9/20), **C** reproduces EXP-007B
(0.425, 8/20).

Mean / median evidence rank when found: **C 34.1 / 10, D 56.5 / 11** — when dense does find the evidence under bounded chunks, it finds it substantially deeper.

---

## 9. Interaction analysis

| retriever | control | bounded | Δ | fully recalled | absent@300 | MRR | net rescued |
|---|---:|---:|---:|---:|---:|---:|---:|
| BM25 | 0.475 | 0.500 | **+0.025** | 9 → 9 | 1 → 1 | 0.280 → 0.287 | 0 |
| dense | 0.425 | 0.400 | **−0.025** | 8 → 8 | 5 → 5 | 0.360 → **0.259** | 0 |

**Interaction (dense Δ − BM25 Δ) = −0.050.**

The hypothesis predicted a positive interaction: ≈0 for BM25, strongly positive for
dense. The measurement is ≈0 for BM25 and *negative* for dense. Neither retriever
gained a single fully-recalled case, and both kept their absent@300 count exactly.

---

## 10. Paired C → D

**1 rescued (OA-007), 1 regressed (OA-008), net 0**, plus one partial change (AN-012).

| quadrant | n | cases |
|---|---:|---|
| control dense correct / bounded dense correct | 7 | AN-002, AN-007, AN-009, OA-001, OA-002, OA-003, OA-005 |
| control dense correct / **bounded dense wrong** | 1 | OA-008 |
| **control dense wrong** / bounded dense correct | 1 | OA-007 |
| both wrong | 11 | |

Both movements are **fragile**: OA-007 moved rank 11 → 10 and OA-008 moved 10 → 11.
Neither is a substantive retrieval improvement; they are the same span sliding one
place across the cutoff in opposite directions.

Span-level movement across all 22 spans:

| movement | n |
|---|---:|
| worsened without crossing k | **6** |
| unchanged | 6 |
| still unreachable | 4 |
| newly reachable outside k | 1 (AN-003) |
| **lost entirely** | **1** (AN-004) |
| strong regression | 1 (AN-012) |
| improved without crossing k | 1 (OA-004) |
| boundary improvement / regression | 1 / 1 |

Six worsened against one improved, outside the cutoff. That is the signature behind
the MRR collapse.

---

## 11. AN-003 deep dive

| cell | evidence rank | doc rank | chunk len | cosine | @10 | @20 | @50 | @100 | @300 |
|---|---:|---:|---:|---:|---|---|---|---|---|
| A control + BM25 | — | 6 | — | — | no | no | no | no | **no** |
| B bounded + BM25 | — | 4 | — | — | no | no | no | no | **no** |
| C control + dense | — | 2 | — | — | no | no | no | no | **no** |
| **D bounded + dense** | **119** | 3 | 1,191 | 0.9214 | no | no | no | no | **yes** |

The anchor chunk fell from **3,449 → 1,191** characters, and for the first time in
any experiment the answer-bearing chunk itself became retrievable.

**This is §17 "partial support", and only barely.** Rank 119 is outside `top_k` by an
order of magnitude and outside any candidate pool a reranker would plausibly consume.
It does not change recall at any measured depth ≤ 100. And it was paid for exactly:
AN-004's evidence went from rank 17 to **absent@300**, so the corpus-wide absent@300
count stayed at 5.

## 12. AN-002 and AN-007 — what shorter chunks did to dense's wins

EXP-007's two dense rescues both lived in the same 3,327-character `HTTP errors`
chunk, a topically homogeneous list of status codes.

| case | A bm25/control | B bm25/bounded | C dense/control | D dense/bounded |
|---|---:|---:|---:|---:|
| AN-002 | 27 | 172 | **1** | 6 |
| AN-007 | 18 | 34 | **2** | 6 |
| AN-012 | 47 | 6 | **1** | **140** |

Both rescues survive into the top 10, but both degrade (1 → 6, 2 → 6). AN-012's dense
rank collapses from **1 to 140**.

This is the mechanism the aggregate numbers hide. Mean pooling rewards **topical
coherence**, not shortness. A long chunk that is uniformly about one topic produces a
strong, clean vector; splitting it fragments that signal across several weaker
vectors. Chunk length in EXP-007 was a *proxy* for heterogeneity, not the cause —
long chunks in this corpus are sometimes coherent (`HTTP errors`) and sometimes not
(`Body Parameters`). Uniform shortening helps the heterogeneous minority slightly and
damages the coherent majority.

The correlation itself survives bounded chunking, which confirms it is not something
shortening can fix: in D, median chunk length is **883** for reachable evidence and
**1,167** for unreachable — still ~1.3×, on a corpus where nothing exceeds 1,999.

## 13. Strong rescues

There were none. The only positive movements are AN-003 entering the pool at rank 119,
OA-004 improving 73 → 47 (both still far outside `top_k`), and OA-007's one-place
boundary crossing.

## 14. Regressions

* **AN-012, rank 1 → 140** — strong regression. Its evidence shares the `HTTP errors`
  chunk that splitting fragmented.
* **AN-004, rank 17 → absent@300** — lost entirely. Its chunk fell 3,439 → 1,167 and
  the evidence stopped being reachable at any depth.
* **AN-002 1→6, AN-007 2→6, AN-006 63→169, AN-001 242→267, AN-008 123→147, AN-011 14→16.**
* **OA-008, rank 10 → 11** — boundary regression, the mirror image of OA-007's rescue.

## 15. Reachability by depth

| cell | @10 | @20 | @50 | @100 | @300 |
|---|---:|---:|---:|---:|---:|
| A control + BM25 | 12 | 8 | 3 | 2 | 1 |
| B bounded + BM25 | 11 | 8 | 5 | 2 | 1 |
| C control + dense | 13 | 9 | 9 | 7 | 5 |
| D bounded + dense | 14 | 10 | 10 | 8 | 5 |

Bounded chunking made dense *worse at every depth except 300*, where it is unchanged.
There is no depth at which the intervention improved candidate recall.

## 16. Optional fusion — EXP-008E (exploratory)

The §24 precondition ("if bounded dense improves semantic retrieval") was **not met**,
so this is reported purely as exploratory. Preregistered EXP-007 settings, untuned:
pool 50 per retriever, `rrf_k = 60`, `top_k = 10`; BM25 on control chunks fused with
dense on bounded chunks.

| configuration | macro recall | fully recalled | doc recall | MRR | absent@300 |
|---|---:|---:|---:|---:|---:|
| A — BM25 control alone | 0.475 | 9/20 | 0.825 | 0.280 | 1 |
| **E — BM25 control + bounded dense** | **0.475** | **9/20** | 0.775 | 0.278 | 2 |
| *(EXP-007C — BM25 control + **control** dense)* | *0.600* | *11/20* | *0.825* | *0.326* | *2* |

**Fusion collapsed to the baseline: net 0, Δ0.000.** EXP-007's fusion reached 0.600
because control dense contributed genuinely complementary rankings; degrading dense
destroyed that complementarity entirely. This is strong indirect confirmation that
bounded chunking hurt the dense retriever.

On the §25 question: the prior fusion regression **did improve** — OA-004 was BM25
rank 5, RRF rank 17 in EXP-007; here it is rank **9**, back inside `top_k`. That is
the one thing bounded dense bought in fusion, and it did not survive into the average.

---

## 17. Was the interaction hypothesis supported?

**No.** Three independent lines of evidence:

1. **Direction.** Dense Δ is −0.025, not positive. The interaction term is −0.050.
2. **Paired movement.** Net 0, with both movements single-rank boundary crossings, and
   six spans worsening against one improving away from the cutoff.
3. **Ranking quality.** MRR fell 0.360 → 0.259, the largest single-cell degradation in
   the experiment.

The one supportive datum — AN-003 becoming reachable at rank 119 — is real and worth
recording, but it is a rank-119 result offset by an outright loss, and it does not
move recall at any depth ≤ 100.

**The EXP-007 chunk-length correlation was not causal.** The operative variable is
topical homogeneity of the retrieval unit, which chunk length only proxies.

---

## 18. Limitations

1. **n = 20.** One case is five percentage points of macro recall. Every movement here
   is 1–2 cases. No significance is claimed and none of this shows one retriever is
   generally superior.
2. **One dense model, and a weak one.** Static word vectors with mean pooling, because
   every transformer host remains egress-blocked. Mean pooling is very likely part of
   why coherence matters so much; a transformer encoder with proper attention might
   not degrade the same way under splitting. **This result constrains mean-pooled
   static embeddings, not dense retrieval in general.**
3. **One bounded configuration.** V2's target 1,200 / hard cap 2,000 was chosen in
   EXP-005 from corpus block-size percentiles. A different size might behave
   differently; no sweep was run, deliberately.
4. **EXP-008E is exploratory** and its precondition was not met.
5. **EXP-NULL still has not run** — no generation credential, host egress-blocked.
6. **Corpus skew persists:** 139 Anthropic documents to 63 OpenAI.

---

## 19. Updated project state

| # | hypothesis | verdict |
|---|---|---|
| 1 | Oversized chunks hide evidence (BM25) | **falsified** — 0 rescued |
| 2 | Missing structural context | **falsified** — Δ0.000 |
| 3 | Lexical vocabulary mismatch | **unsupported** — no vocabulary rescue |
| 4 | Chunk size interacts with dense retrieval | **not supported** — interaction −0.050 |

Four hypotheses, four negative results, each from a controlled intervention. What the
project has actually learned is narrower and more useful than any of them: **the best
measured configuration remains BM25 on control chunks fused with dense on control
chunks (EXP-007C, 0.600 / 11-of-20)**, and both retrievers work better on the original
chunking than on the bounded one.

## 20. What the measurements justify next

1. **Stop optimising chunk size.** Two controlled interventions, on two different
   retrievers, both null. The decision gate says so explicitly.
2. **A transformer retrieval encoder remains the highest-value experiment**, unchanged
   from EXP-007 and still blocked only on network egress. EXP-008 sharpens the reason:
   mean pooling is now implicated directly, and a transformer encoder is precisely the
   intervention that removes it.
3. **Test topical homogeneity, not length, if chunking is revisited at all.** The data
   says coherence is the operative variable. That would be a genuinely new hypothesis —
   but it should wait behind (2).
4. **Still not a reranker.** AN-003 is at rank 119 in the single cell where it is
   reachable at all, and absent at 300 in the other three. The Outcome-B condition —
   evidence routinely landing at rank 15–100 — is not what the data shows.

### Promotion decision

**The frozen baseline does not change: control chunking, no enrichment, BM25,
`top_k = 10`.** Bounded chunking is not promoted for dense retrieval; it is measurably
worse. The EXP-007 hybrid remains the leading promotion candidate, and EXP-008 has now
shown it must be built on **control** chunks for both retrievers.
