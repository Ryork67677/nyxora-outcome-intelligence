# EXP-014 preregistration — all four representations defined BEFORE scored evaluation

## 1. Hypothesis

A dedicated document-level semantic representation will improve **shallow** document
routing relative to chunk-derived routing, because it represents the document as a
whole rather than depending on individual chunks being globally competitive.

This must be falsifiable. No representation is assumed to help.

## 2. Why this, and why now

EXP-012's oracle showed the passage layer is mostly fine — given the correct
document, the same retrievers reach 0.950 / 19-of-20 with zero regressions.
EXP-013 then falsified the aggregation hypothesis: four rank-aggregation rules
(MAX, RANK_SUM, TOPK_VOTE, MAX_SUPPORT) all landed on **document recall@5 = 0.875**
and **17/20** all-required-documents routed, an identical Stage-1 ceiling of 0.850.

**AN-001 explains why.** Its document contributes one chunk anywhere in 300 BM25
results and the transformer never retrieves it at all, so it sits at document rank
62–72 under every router — yet handed the document, its evidence ranks 1. There is
nothing for an aggregation formula to aggregate. The limitation is the input.

An exploratory mean-document-vector probe (run after EXP-013's routers were frozen)
reached recall@10 = 1.000, 18/20 fused, and moved AN-001 from rank 62 to 8. It was
unreplicated and is **not promoted**. EXP-014 tests that direction properly.

## 3. Primary success metric

**All required documents routed @5.** Chunk-derived routing achieves 17/20; the
exploratory probe reached 18/20; a result worth taking seriously is **19/20 or
20/20**. Recall@1/@3/@5/@10 is also reported.

For multi-hop questions **every** expected document must be present — partial
routing counts as failure for the case.

## 4. The four representations — defined completely, in advance

All are built from the **already-stored** transformer chunk embeddings
(`emb_e7d4183fd6eb878ae2fdf080efb6861e`, fingerprint `bd95feaeacf98559`) over
`cs_v1_control`. No external API, no new model, no retraining, no new passage
embeddings.

| name | construction |
|---|---|
| **DOC-A-MEAN** | arithmetic mean of the document's normalised chunk vectors, then L2 normalise. |
| **DOC-B-CENTROID** | deduplicate exact-duplicate chunk content by `content_hash`, then mean of the survivors, then L2 normalise. |
| **DOC-C-SECTION** | mean chunk vectors within each `section_path`, normalise each section vector, then mean the section vectors with **equal weight per section**, then normalise. One section = one vote. |
| **DOC-D-MULTIVECTOR** | keep the per-section vectors from DOC-C separately; a document's score is the **maximum** cosine over its section vectors. |

No weighting, no clustering, no thresholds, no sweeps, no learned parameters.
Similarity is cosine against the raw query vector, using the same MiniLM query
configuration as passage retrieval.

## 5. Preregistration discipline

The definitions above are final. During EXP-014 I will **not**: change weights after
seeing failures, alter section grouping to rescue AN-001, pick mean-vs-max per
question, tune against the 20 scored cases, or iterate formulas until one reaches
20/20. Any variant conceived after seeing scored results will be labelled
**EXPLORATORY / DEVELOPMENT-SET SELECTED** and excluded from the preregistered
conclusion.

## 6. Query representation

**Raw user query only.** No normalization, no structured query, no LLM rewrite —
EXP-011 rescued zero cases with transformed queries and degraded the hybrid.

## 7. Stage 2 is frozen

After Stage 1 selects documents: raw query, full-corpus BM25 chunk scores plus the
existing transformer chunk cosine scores restricted to the selected documents,
passage RRF `k=60`, final top 10. BM25 IDF is never recomputed inside the selected
documents. No passage-embedding change, no chunking change, no enrichment, no
cross-encoder, no second semantic model, no reranker.

Routing width is frozen at **`top_documents = 5`** for all primary comparisons.
Diagnostics are reported at @1/@3/@5/@10, but N=10 will not be promoted merely
because recall rises with width — the objective is *shallow* high-recall routing.

## 8. Fusion plan

EXP-013 showed BM25 contributes **+0** routed cases at the document level and
document-level fusion added nothing over the better component, so BM25 does not
automatically belong in Stage 1.

* **Standalone** — each representation alone (reported first).
* **Primary fusion** — each representation **+ the transformer chunk-derived
  document ranking**, RRF `k=60`, no weights, no sweep. This is the primary fusion
  test because the exploratory signal suggested the two may be complementary.
* **Secondary** — adding BM25 document ranking, run only after the primary fusion
  results are immutable and labelled SECONDARY. If it contributes no routed cases,
  the recommendation will be to leave it out. Complexity must earn its place.

Scores are never added across retrievers; combination is RRF over ranks only.

## 9. Promotion requirements

A router is **not** promoted on document recall alone. A strong candidate should
satisfy all of:

* all required documents routed @5 **≥ 19/20**;
* end-to-end **> 0.775 / 15-of-20**;
* acceptable or zero regressions.

The oracle proves headroom exists; a real router has to convert it.

## 10. Preregistered readings

n = 20 / 22 spans. One case = 5 percentage points. No significance claims.

| outcome | reading |
|---|---|
| ≥19/20 @5 **and** end-to-end above 0.775 | dedicated document retrieval is supported |
| ≥19/20 @5 but end-to-end stays 0.775 | routing improved, Stage 2 failed to convert it — the bottleneck moved |
| recall@10 improves but @5 does not | document semantics improve reachability, not shallow routing; do not deploy hierarchy |
| all representations remain 17/20 | simple aggregation of existing chunk embeddings is insufficient; a genuinely document-trained retrieval model becomes justified |
| AN-001 rescued but an established success lost | the tradeoff moved, not a clean improvement — analyse complementarity before promotion |

## 11. Tracked cases

**AN-001** (canonical routing failure), **AN-012** (multi-hop, needs both
documents), **OA-004** (repeated ensemble-regression exposure), **AN-008** (lost by
EXP-013's aggregating routers), plus every case whose routing classification changes.

**AN-003 is out of scope.** It is already routed correctly; EXP-012 showed 141
chunks in its document and an oracle evidence rank of 29. It is a within-document
passage-ranking defect. It will be tracked and **not** tuned around.

## 12. Not done in this experiment

No reranker (EXP-013 showed its ceiling behind current routing is worse than
global's). No generation. No ANN. No corpus, chunk, query or passage-scorer change
of any kind.
