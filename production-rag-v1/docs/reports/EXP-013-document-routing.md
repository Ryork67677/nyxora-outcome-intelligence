# EXP-013 — Document Routing

**Status: hypothesis falsified for rank aggregation; an exploratory signal found
elsewhere.** Not one of the three aggregation routers improved document recall@5.
All four routers — including the EXP-012 control — sit at **0.875 / 17-of-20**, an
identical Stage-1 ceiling of 0.850. But an exploratory **document-level embedding**
router reached **18/20** and recall@5 **0.900**, and ranked the one document no
chunk-derived router could find at **8 instead of 62**.

## 1. Executive result

### Routing quality — the primary metric

| router | @1 | @3 | @5 | @10 | all-routed | Stage-1 ceiling | fusion bonus | mean pool |
|---|---|---|---|---|---|---|---|---|
| A_MAX (EXP-012 control) | 0.525 | 0.800 | **0.875** | 0.950 | **17/20** | 0.850 | +0 | 900 |
| B_RANK_SUM | 0.475 | 0.825 | **0.875** | 0.900 | **17/20** | 0.850 | +0 | 1,745 |
| C_TOPK_VOTE | 0.475 | 0.825 | **0.875** | 0.925 | **17/20** | 0.850 | +0 | 1,446 |
| D_MAX_SUPPORT | **0.575** | **0.875** | **0.875** | 0.950 | **17/20** | 0.850 | +0 | 1,348 |
| *E_DOC_EMBED (exploratory, hybrid)* | *0.675* | *0.875* | ***0.900*** | *0.950* | ***18/20*** | *0.900* | — | — |

**No preregistered router improved recall@5 or all-required-document routing.**

### End-to-end

| cell | macro recall | full | spans@10 | doc R | MRR | absent@300 | oracle gap |
|---|---|---|---|---|---|---|---|
| GLOBAL control | **0.775** | 15/20 | 17/22 | 0.925 | 0.449 | 2 | 0.175 |
| A_MAX | 0.725 | 14/20 | 16/22 | 0.875 | 0.421 | 4 | 0.225 |
| B_RANK_SUM | 0.775 | 15/20 | 17/22 | 0.875 | 0.414 | 4 | 0.175 |
| C_TOPK_VOTE | 0.775 | 15/20 | 17/22 | 0.875 | 0.412 | 4 | 0.175 |
| D_MAX_SUPPORT | 0.775 | 15/20 | 17/22 | 0.875 | 0.402 | 4 | 0.175 |
| **ORACLE** *(not deployable)* | **0.950** | **19/20** | **21/22** | **1.000** | **0.646** | **0** | 0.000 |

Aggregation **repairs** the EXP-012 hierarchy regression — B, C and D each recover
to global parity — but **none exceeds global**. Hierarchy still never wins.

## 2. Reproduction gates

| gate | target | measured | verdict |
|---|---|---|---|
| GLOBAL control | 0.775 / 15-of-20 / 17-of-22 | exact | **PASS** |
| A_MAX (EXP-012 hierarchy) | 0.725 / 14-of-20 / 16-of-22 | exact | **PASS** |
| ORACLE | 0.950 / 19-of-20 / 21-of-22 | exact | **PASS** |

## 3. What was frozen

Stage 2 is untouched: raw query, full-corpus BM25 plus transformer cosine restricted
to the routed documents, passage RRF `k=60`, top 10. BM25 term statistics are never
recomputed inside routed documents. Corpus, versions, `cs_v1_control`, chunk text,
BM25 parameters, the transformer and its 512-token configuration and fingerprint
`bd95feaeacf98559`, the stored document embeddings, `top_k=10`, evidence anchors and
questions all unchanged. `top_documents = 5` for every primary comparison.

All routers work in the **rank domain**. BM25 and cosine scores are never combined
directly — a test asserts the module contains no such expression — because mixing
their scales, or normalising them against 20 questions and tuning a weight, would
fit the evaluation set rather than measure on it. `k=60`, support 5 and vote depth
50 were preregistered and not tuned.

## 4. The routers behave as designed — the corpus just doesn't care

On the brief's motivating example (document A supported at ranks 2, 7, 11, 18;
document B owning rank 1 then 150 and 270), A_MAX picks B while B_RANK_SUM and
C_TOPK_VOTE pick A. The aggregation works exactly as intended. It simply does not
change which documents reach the top 5 on this corpus.

Where aggregation *does* help is shallow depth: D_MAX_SUPPORT improves recall@1
from 0.525 to **0.575** and recall@3 from 0.800 to **0.875**. By depth 5 every
router has converged.

## 5. The trade: one case rescued, one case lost

Against the EXP-012 hierarchy, B, C and D each score **net +1**: they rescue
**OA-004** and **AN-011**, and lose **AN-008**.

**OA-004 is the aggregation success story.** Its document has 5 BM25 chunks and 3
transformer chunks inside the top 30 — broad support that A_MAX discarded. Document
rank moves **6 → 2**, it routes, and its evidence lands at rank 2–4. This is exactly
the mechanism the hypothesis predicted.

**AN-008 is the cost.** It routed under A_MAX and falls out under all three
aggregating routers — the same breadth preference that promotes OA-004 demotes it.

Against the global control the exchange nets to zero: rescued AN-011, regressed
AN-008, **Δ0.000**.

## 6. Why the ceiling never moves

Every router leaves **17 of 20** cases with all required documents routed, so the
Stage-1 ceiling is **0.850** for all four. The three failures are not the same three
in every router, but the count is:

| router | cases missing a document |
|---|---|
| A_MAX | AN-001, AN-012, OA-004 |
| B_RANK_SUM / C_TOPK_VOTE / D_MAX_SUPPORT | AN-001, AN-008, AN-012 |

**AN-001 and AN-012 defeat every router.**

## 7. AN-001 — the case that explains the result

| signal | value |
|---|---|
| best BM25 chunk rank | 19 |
| **best transformer chunk rank** | **absent from the top 300** |
| BM25 chunks in top 10 / 30 / 50 / 100 | 0 / 1 / 1 / 1 |
| transformer chunks in top 100 | 0 |
| document rank, all four routers | 62 – 72 |
| oracle evidence rank | **1** |

Its document contributes **one** chunk anywhere in 300, and the transformer never
retrieves it at all. There is nothing for an aggregation rule to aggregate. Yet with
the document handed over, its evidence ranks **first**.

This is why no aggregation formula could work: the routers all consume the same
chunk lists, and for AN-001 those lists contain almost no signal. **The limitation
is the input, not the arithmetic.**

## 8. AN-012 — multi-hop, and only ever half-routed

Two expected documents. One is easy (transformer chunk rank 2). The other has best
BM25 rank 6 but transformer rank 63, and lands at document rank 9–13 — just outside
the top 5 under every router. AN-012 is **partially routed** in all four, which for a
multi-hop question is the same as failing.

## 9. Complementarity — document-level fusion is doing no work

| router | BM25 alone | transformer alone | best component | fused | bonus |
|---|---|---|---|---|---|
| A_MAX | 15/20 | **17/20** | 17 | 17 | **+0** |
| B_RANK_SUM | 16/20 | **17/20** | 17 | 17 | **+0** |
| C_TOPK_VOTE | 16/20 | **17/20** | 17 | 17 | **+0** |
| D_MAX_SUPPORT | 15/20 | **17/20** | 17 | 17 | **+0** |

The transformer's document ranking alone already achieves 17/20; BM25 adds nothing
at the document level, and fusion adds nothing over the better component. This is a
different picture from passage retrieval, where the raw fusion bonus is +4 cases.
**Retriever complementarity is a passage-level phenomenon here, not a document-level
one.**

## 10. Exploratory — a document-level representation

Run only after A–D were frozen, and **labelled exploratory**: the mean of each
document's already-stored normalised chunk vectors, renormalised, ranked by cosine.
No re-chunking, no training, no tuning.

| variant | @1 | @3 | @5 | @10 | all-routed |
|---|---|---|---|---|---|
| document embedding alone | 0.375 | 0.725 | 0.825 | **1.000** | 16/20 |
| **fused with chunk routing** | **0.675** | **0.875** | **0.900** | 0.950 | **18/20** |

Two things stand out:

* **Alone it reaches recall@10 of 1.000** — every expected document is within its
  top 10, which no chunk-derived ranking achieves.
* **AN-001's document moves from rank 62 to rank 8.** The case that defeated every
  aggregation rule is visible to a document-level representation.

The fused variant is the first configuration in EXP-013 to exceed 17/20, reaching
**18/20** by routing AN-012's second document (rank 9 → 5) — though it loses OA-004
(rank 2 → 6).

**This is one exploratory run at n=20 and it is not a result.** A single case is 5
percentage points, and the same fusion that gains AN-012 gives back OA-004. It is a
direction with measured support, not a finding.

## 11. AN-003 — unchanged, as expected

Routed correctly by every router (document rank 3–4) and its evidence remains
absent@300, exactly as EXP-012 predicted. AN-003 is a within-document
passage-ranking defect, its document was never the problem, and nothing here was
modified to target it. Its oracle rank is still 29 inside its own 141-chunk document.

## 12. Reranker gate

| cell | 1–10 | 11–30 | 31–50 | 51–100 | 101–300 | absent | c@30 | c@50 | c@100 |
|---|---|---|---|---|---|---|---|---|---|
| GLOBAL | 17 | 1 | 1 | 1 | 0 | 2 | 0.818 | 0.864 | 0.909 |
| best router (D) | 17 | 1 | 0 | 0 | 0 | 4 | 0.818 | 0.818 | 0.818 |
| **ORACLE** | **21** | **1** | 0 | 0 | 0 | **0** | **1.000** | **1.000** | **1.000** |

Routing improvements did not raise the reranker ceiling. Under the best router it is
**0.818**, still *below* the global control's 0.909 — hierarchy's exclusions remove
candidates a reranker could otherwise have reordered. Only oracle routing reaches
1.000, and it does so at a pool of just 30.

## 13. Limitations

* n = 20 / 22 spans; one case is 5 percentage points. No significance claims.
* Three aggregation rules were tested, not the space of aggregation. Their agreement
  at recall@5 is suggestive, not exhaustive.
* Router E is exploratory, unreplicated, and its gain is a single case bought at the
  cost of another.
* Mean-pooled document vectors are the crudest possible document representation;
  they were chosen because they need no tuning, not because they are good.
* The oracle is an upper bound with a perfect router — it shows headroom exists, not
  that it is reachable.
* **EXP-NULL remains BLOCKED**: no project generation credential, so there is still
  no measured no-retrieval floor.

## 14. Did better document aggregation solve routing?

**No.** Three aggregation rules, all preregistered, all landing on exactly the same
recall@5 and the same 17/20. The Stage-1 ceiling did not move by a single case.

This is preregistered **Outcome D**: chunk-ranking-derived routing is itself
inadequate. AN-001 shows why in one line — its document appears once in 300 BM25
chunks and never in the transformer's list. No function of those lists can rank it
into the top 5.

The honest reading: **the routers were not the problem, the input was.**

## 15. What the measurements justify next

1. **Stop inventing aggregation formulas.** Three rules, one ceiling. Outcome D was
   preregistered for exactly this and should be honoured.
2. **A document-level retrieval representation is the justified next experiment.**
   The exploratory router already reaches recall@10 = 1.000 alone and moves AN-001
   from rank 62 to 8. That is the first signal in EXP-013 that isn't flat — and it
   deserves a proper preregistered experiment, not promotion off one run.
3. **Do not deploy hierarchy.** No router beat the global control at any point, and
   hierarchy still *lowers* the reranker ceiling (0.818 vs 0.909).
4. **A reranker remains premature.** Behind current routing its ceiling is worse
   than global's. The oracle's 1.000-at-pool-30 says a reranker becomes attractive
   only once routing is close to perfect — routing first, reranking second.
5. **Complementarity is passage-level, not document-level.** BM25 contributes
   nothing to document routing here; a future document retriever should be evaluated
   on whether it adds anything the transformer does not already have.
