# EXP-011 — Controlled Query-Side Retrieval

**Status: hypothesis falsified — with an instructive twist.** Every query
transformation made the *system* worse, and **not one case was rescued in any
cell**. But the same transformations made each retriever **better in isolation**.
The hybrid's strength was never query quality; it was the two retrievers failing
on different questions, and "improving" the query destroyed that.

## 1. Executive result

| cell | query views | macro recall | fully recalled | Δ vs A | rescued | regressed |
|---|---|---|---|---|---|---|
| **A** raw (control) | 1 | **0.775** | **15/20** | — | — | — |
| B normalized | 1 | 0.700 | 13/20 | −0.075 | **0** | 2 |
| C raw + normalized | 2 | 0.750 | 14/20 | −0.025 | **0** | 1 |
| D structured | 1 | 0.300 | 5/20 | **−0.475** | **0** | 10 |
| E raw + normalized + structured | 3 | 0.700 | 13/20 | −0.075 | **0** | 2 |

Zero rescues across every cell and every case. The frozen control is the best
configuration measured.

## 2. Why EXP-011 exists

EXP-010 closed the document side: truncation was eliminated completely (23.22% of
chunks → 0%, token coverage 0.7610 → 1.0000) and retrieval moved Δ0.000. Its
decisive measurement was that **21 of 22 answers were already visible** to the
encoder. What remains is a ranking problem — the retriever reads the right text
and scores it below other text.

The query had been a raw user-question string since EXP-000. It was the one major
variable never tested.

## 3. What EXP-010 ruled out

Chunk boundaries, chunk size, encoder visibility, structural enrichment. Three
chunking interventions returned 0, −0.050 and 0.000. The document representation
is not where the remaining recall lives.

## 4. Frozen document and retrieval system

Corpus, versions, control chunks, chunk text, **stored document embeddings**
(`emb_e7d4183fd6eb878ae2fdf080efb6861e`, fingerprint `bd95feaeacf98559`), the
transformer and its tokenizer and 512-token window, BM25 `k1=1.2`/`b=0.75` on
`simple`, cosine, exact search with no ANN, RRF pool 50 / `rrf_k` 60 / `top_k` 10,
the evidence anchors and the 20 questions. **Only the query text differed.**

## 5. Hypothesis

> The remaining failures are partly caused by mismatch between natural user
> questions and the forms retrievers rank most effectively. A controlled query
> representation may improve retrieval while preserving the user's intent.

Preregistered in `experiments/EXP-011/preregistration.md` before any transform was
written, with `A ≈ E` declared in advance to mean *stop rewriting queries*.

## 6. Leakage controls

A transform receives only the raw question string. Enforced and tested:

* the module imports **only** `re` and `dataclasses` — no project import at all,
  so corpus or evaluation knowledge has no route in;
* its executable code contains no reference to `golden`, `evals`, `load_cases`,
  `expected_evidence`, `case_id`, `section_path`, `version_id` or `chunk_id`
  (checked on tokenized code, not prose);
* no golden question or multi-word evidence section path appears in the source;
* transforms are exercised on held-out probe strings, not only the 20 questions.

No per-question rules exist. Every rule is general English question scaffolding.

## 7. The two transformations

**`technical_normalized_query`** — subtractive. Removes conversational
scaffolding (interrogatives, auxiliaries, modals, articles, pronouns, politeness)
and applies a small fixed map of English limit phrasings (`at most` → `maximum`).
Protected and never altered: identifiers, anything containing a digit, back-quoted
spans, acronyms, and capitalised product names the user actually wrote.

**`structured_query`** — extracts entities, operations and the asked property
*from the question itself*, then renders them as one query. Nothing is inferred
that the user did not write.

Worked example (a held-out probe, not a golden question):

```
raw         : What is the default value of max_tokens in the Anthropic Messages API?
normalized  : default value max_tokens Anthropic Messages API
structured  : max_tokens Anthropic Messages API default value
```

## 8. Reproduction gate

| check | target | measured | verdict |
|---|---|---|---|
| macro span recall | 0.775 | 0.775 | **PASS** |
| cases fully recalled | 15/20 | 15/20 | **PASS** |
| spans@10 | 17/22 | 17/22 | **PASS** |

## 9–13. Cell results

| cell | macro R | full | spans@10 | doc R | MRR | a@10 | a@30 | a@300 | calls/query |
|---|---|---|---|---|---|---|---|---|---|
| A raw | 0.775 | 15/20 | 17/22 | 0.925 | 0.449 | 5 | 4 | 2 | 2 |
| B normalized | 0.700 | 13/20 | 15/22 | 0.900 | 0.371 | 7 | 4 | 2 | 2 |
| C raw + normalized | 0.750 | 14/20 | 16/22 | 0.950 | 0.405 | 6 | 4 | 2 | 4 |
| D structured | 0.300 | 5/20 | 7/22 | 0.725 | 0.092 | 15 | 11 | 8 | 2 |
| E three-view | 0.700 | 13/20 | 15/22 | 0.950 | 0.319 | 7 | 4 | **1** | 6 |

The structured view is not a marginal loss — it is a collapse. Reducing a question
to extracted concepts discards most of what the retrievers were using.

## 14. Paired rescues and regressions

| comparison | Δ | rescued | regressed | net |
|---|---|---|---|---|
| A → B | −0.075 | none | AN-002, OA-006 | −2 |
| A → C | −0.025 | none | OA-006 | −1 |
| A → D | −0.475 | none | AN-002, AN-004, AN-005, OA-001, OA-002, OA-003, OA-004, OA-005, OA-006, OA-008 | −10 |
| A → E | −0.075 | none | OA-002, OA-006 | −2 |

**No cell rescued a single case.** That is a stronger result than the aggregate
deltas: there is no subset of questions for which query rewriting helped.

## 15. The twist — the retrievers individually got *better*

Running each view through each retriever alone tells a different story:

| retriever | raw | normalized | Δ | structured | Δ |
|---|---|---|---|---|---|
| BM25 | 0.475 (9/20) | **0.575 (11/20)** | **+0.100** | 0.125 (2/20) | −0.350 |
| transformer | 0.575 (11/20) | **0.625 (12/20)** | **+0.050** | 0.300 (5/20) | −0.275 |

Normalization improved **both** retrievers on their own — BM25 by two cases and
the transformer by one. Yet fusing the two improved retrievers produced a *worse*
system than fusing the two unimproved ones.

## 16. Mechanism: the fusion bonus collapsed

The direct measurement:

| query view | BM25 alone | transformer alone | best component | fused | **fusion bonus** |
|---|---|---|---|---|---|
| raw | 9/20 | 11/20 | 11 | **15** | **+4 cases** |
| normalized | 11/20 | 12/20 | 12 | 13 | **+1 case** |
| structured | 2/20 | 5/20 | 5 | 5 | **+0 cases** |

RRF adds value in proportion to how much the two retrievers still *disagree*
usefully. On the raw query the fusion is worth four cases beyond its best
component. Normalizing pushed both retrievers toward the same evidence and the
bonus fell to one — more than cancelling the individual gains.

A supporting proxy points the same way but only weakly, and is reported as such:
mean Jaccard overlap between the two retrievers' top-50 rose from **0.134** (raw)
to **0.154** (normalized) to **0.187** (structured), while shared chunks in the
top 10 stayed flat (2.5 → 2.4). The fusion-bonus table is the solid evidence; the
overlap statistic is directionally consistent, not decisive.

## 17. The design rule earned its place

The preregistration forbade ever replacing the user's query. That rule is what
kept the damage bounded:

* B (normalized alone) − 2 cases
* C (raw **+** normalized) − 1 case

Keeping the original query halved the loss. And E, which adds the structured view
on top, is worse than C — a third view is not free even when the original is
retained.

## 18. Query-view contribution

Every fused hit records which `retriever(view)` list contributed it and at what
rank. In E, six lists participate equally with no weighting — weights chosen after
seeing which cases improved would be fitted to a 20-case set, not measured on it.
The query-embedding cache served 63.1% of requests (101 hits / 59 misses across
all cells).

## 19. Cost

| cell | retrieval calls/query | work multiplier |
|---|---|---|
| A | 2 | 1× |
| C | 4 | 2× |
| E | 6 | **3×** |

E costs three times the retrieval work to lose two cases. **Wall-clock latency is
not comparable across cells here** — A ran first and absorbed cold-cache and
warm-up costs, which is why it shows the highest total despite the fewest calls.
The call count is the honest cost measure.

## 20. AN-003

| cell | evidence rank | document rank |
|---|---|---|
| A raw | absent@300 | 3 |
| B normalized | absent@300 | 6 |
| C raw + normalized | absent@300 | 4 |
| D structured | absent@300 | 3 |
| E three-view | absent@300 | **2** |

AN-003 was not moved by any query representation. The pattern is now unmistakable:
the **right document ranks 2nd–6th in every configuration**, while the chunk
carrying the answer never enters the top 300. This is not a query-formulation
failure and not a visibility failure — it is a within-document chunk-ranking
failure, and it has now survived nine experiments.

(In the fused cells "absent" is bounded by the 50-candidate pool per list, so it is
not directly comparable with EXP-010's rank 193 from an unfused dense run.)

## 21. Candidate depth and the reranker gate

| cell | 1–10 | 11–30 | 31–50 | 51–100 | 101–300 | absent | ceil@30 | ceil@50 | ceil@100 |
|---|---|---|---|---|---|---|---|---|---|
| A raw | 17 | 1 | 1 | 1 | 0 | 2 | 0.818 | 0.864 | **0.909** |
| C raw + normalized | 16 | 2 | 2 | 0 | 0 | 2 | 0.818 | 0.909 | 0.909 |
| E three-view | 15 | 3 | 1 | 1 | 1 | **1** | 0.818 | 0.864 | 0.909 |

Query expansion did **not** raise the perfect-reranker ceiling: it is 0.909 at
pool 100 for A, C and E alike. E does pull one span out of "absent" into the
101–300 band — real but not ceiling-changing.

So a reranker would still be chasing 0.909 against 0.775 already delivered:
roughly three spans across 20 questions, and it would have to be perfect to get
them.

## 22. EXP-NULL

**BLOCKED**, unchanged. `api.anthropic.com` is reachable but answers 401 without a
key; `api.openai.com` is blocked at the egress proxy. No project generation
credential exists. The host harness's own credential is not a project credential
and was not used. EXP-011 was not delayed for it.

**EXP-011F (LLM query rewriting) was not run** — it requires a project-authorized
generation model, and none is available.

## 23. Limitations

* n = 20 / 22 spans; one case is 5 percentage points. No significance claims.
* Two deterministic transforms were tested, not the space of query rewriting. An
  LLM rewriter that preserves sentence form might behave differently — though the
  mechanism found here predicts it would also erode complementarity if it made
  both retrievers agree.
* The fusion-bonus measurement is a case count at n=20; ±1 case is noise, but the
  +4 → +1 → +0 progression is monotone across three independent views.
* Latency figures are confounded by cell ordering (§19).
* All results are for this corpus, this encoder and this question set.

## 24. Was query formulation a real bottleneck?

**No — not in the way the hypothesis proposed.** Rewriting the query cannot rescue
a single case, and the raw question is already the best input to the *hybrid*.

But the finding is more specific than "queries are fine". Query form **does**
change individual retriever quality, materially — BM25 gained two cases from
filler removal alone. What it cannot do is improve the system, because this
system's performance comes from retriever disagreement rather than from either
retriever's absolute quality. **Optimising the components made the ensemble
worse.**

That is a result about ensembles, not about queries, and it was only visible
because the components were measured separately from the fusion.

## 25. What the evidence justifies next

1. **Stop rewriting queries.** Preregistered Outcome D. Zero rescues in four
   configurations is not a near miss.
2. **Treat complementarity as the quantity to protect.** Any future change should
   report the fusion bonus, not just aggregate recall — a change that improves both
   retrievers can still degrade the system.
3. **The remaining failure is within-document chunk ranking.** AN-003 is the clean
   case: right document at rank 2, answer chunk never in the top 300. That is the
   next thing to investigate, and it is not a chunking, visibility or query problem.
4. **A reranker is still not justified** on ceiling grounds (0.909 vs 0.775
   delivered) — and EXP-011 did not move that ceiling.
5. **EXP-NULL remains the most valuable unblocked experiment.** Without it there is
   still no measured no-retrieval floor beneath any of these numbers.
