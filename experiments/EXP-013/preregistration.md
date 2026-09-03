# EXP-013 preregistration — recorded BEFORE any router was implemented

## 1. Hypothesis

Aggregating evidence across **multiple** highly ranked chunks will improve document
recall@5 relative to the current best-chunk routing rule, allowing hierarchical
passage retrieval to approach the oracle result without sacrificing existing
successful cases.

This must be falsifiable. No router is assumed to help, and the experiment is not
to be steered toward making aggregation succeed.

## 2. Why routing, and why now

EXP-012 ran the oracle-document diagnostic: given the correct document, the *same*
retrievers, scores and fusion reached **0.950 / 19-of-20**, document recall 1.000,
MRR 0.646, nothing absent at 300, and **zero regressions**. Passage scoring is
therefore mostly fine.

What failed was routing. The fused router achieves recall@5 of 0.875, and every
expected document is routed for only **17 of 20** cases — three questions lose
required evidence before Stage 2 begins. That is the measured bottleneck.

## 3. What the current rule discards

The existing router gives a document the rank of its **single highest-ranked
chunk**. A document supported by chunks at ranks 2, 7, 11 and 18 loses to one whose
only support is rank 1 and whose next chunks are at 150 and 270. All evidence
beyond the best chunk is thrown away. EXP-013 asks whether using it routes better.

## 4. Frozen — everything except document aggregation

Stage 2 is **completely frozen**: raw query, full-corpus BM25 chunk scores plus
transformer cosine scores restricted to routed documents, passage RRF `k=60`, top
10. BM25 term statistics are never recomputed inside routed documents. No passage
reranker, cross-encoder, local query rewriting, local IDF, passage enrichment or new
passage embeddings.

Also frozen: corpus, versions, `cs_v1_control` chunks, chunk text, raw query (no
rewriting — EXP-011 produced zero rescues), BM25 `k1=1.2`/`b=0.75`, the transformer
and its 512-token configuration and fingerprint `bd95feaeacf98559`, the stored
document embeddings, `top_k=10`, evidence anchors, golden questions, no ANN, no
generation.

**Routing width is fixed at `top_documents = 5`** for every primary comparison.
Sensitivity at N=3 and N=10 may follow only after the primary results are frozen,
labelled exploratory.

Document ranking is derived from a depth-300 chunk ranking, as in EXP-012.

## 5. The four routers — parameters fixed in advance

All routers work in the **rank domain**. BM25 scores and cosine scores live on
different scales; adding them, or normalising them against this 20-question set and
tuning weights, would fit the evaluation set rather than measure on it.

| router | rule |
|---|---|
| **A_MAX** (control) | document rank = its highest-ranked chunk. The EXP-012 rule. |
| **B_RANK_SUM** | `score = Σ 1/(60 + chunk_rank)` over the document's **top 5** supporting chunks. |
| **C_TOPK_VOTE** | each of the **top 50** chunks casts one vote for its document; order by votes ↓, then best supporting chunk rank ↑, then document id. |
| **D_MAX_SUPPORT** | derive a best-chunk list *and* a rank-sum support list per retriever, then fuse all four with RRF. |

`k = 60`, support count 5, and vote depth 50 are **preregistered and not tuned**.
Router D deliberately avoids a scalar blend such as `0.7·max + 0.3·support`, which
would introduce an arbitrary score-scale weight; everything stays in ranks.

For A, B and C the two retrievers produce independent document lists which are then
fused with RRF `k=60`. For D the four lists are fused together, giving BM25 and the
transformer equal total weight.

## 6. Optional exploratory router

`ROUTER_E_DOC_EMBED` may be run **only after A–D are frozen**, clearly labelled
exploratory: mean of the already-stored normalised chunk embeddings per document,
renormalised, ranked against the query. No re-chunking, no training. If it needs
substantial tuning it will be skipped rather than turned into a research project.

## 7. Primary metric — routing, measured before passage retrieval

Document recall@1/@3/@5/@10, and above all **cases with every required document
routed at top 5**. The current fused router achieves **17/20**; a router must
improve that. For multi-hop questions partial routing is not enough — all expected
documents must be present.

Stage-1 ceiling (maximum possible case recall if Stage 2 were perfect but routing
stayed as measured) is reported for every router.

## 8. End-to-end is still required

A router is not promoted on routing recall alone. Every router runs the full frozen
Stage 2, and paired movement is reported against **both**:

* the global control (0.775 / 15-of-20) — the system to beat;
* the EXP-012 hierarchy (0.725 / 14-of-20) — whether routing itself improved.

## 9. Complementarity is a required metric

Three separate changes in this project have improved components while degrading the
ensemble (EXP-011 normalization, EXP-012 hierarchy). So for every router: BM25
routing alone, transformer routing alone, best component, fused, and the **fusion
bonus** in all-documents-routed cases. A router that makes the two document
rankings agree may route worse after fusion even if each side improves.

## 10. Exclusion damage must be visible

Hierarchy has a failure mode global retrieval structurally cannot have: an excluded
document is unrecoverable. Every router reports which expected documents fall
outside top 5 and for which cases.

**OA-004** is tracked explicitly — it has repeatedly exposed ensemble regressions.

## 11. AN-003 is not a target

AN-003's document was already routed correctly at rank 3 in EXP-012, and its oracle
evidence rank was 29 inside its own 141-chunk document. It is a **within-document
passage-ranking defect**, not a routing defect. It is reported after Stage 2 but the
system will **not** be modified to target it, and it is not a success condition for
any router.

## 12. Preregistered readings

n = 20 / 22 spans. One case = 5 percentage points. No significance claims; paired
movement matters more than averages.

| outcome | reading |
|---|---|
| recall@5 > 0.875 **and** end-to-end above 0.775 / 15-of-20 | aggregation has earned its place; then compute reranker headroom |
| routing reaches 19–20/20 but end-to-end stalls | Stage 1 is fixed, Stage 2 ranking is the next bottleneck — the strongest case yet for a passage reranker |
| routing improves but complementarity collapses | do not promote; check whether aggregation made the two document rankings too similar (the EXP-011 failure) |
| no router improves recall@5 | chunk-ranking-derived routing is itself inadequate; the next step is a genuinely document-level representation, **not** more aggregation formulas |
| routing improves but hierarchy still loses to global | exclusion costs more than competition reduction gains; do not deploy hierarchy |

## 13. Promotion

The frozen production baseline stays BM25 / control chunks / `top_k=10`. The
strongest measured configuration remains the global hybrid at 0.775 / 15-of-20.
Oracle numbers are diagnostic headroom and are never presented as deployable. No
reranker is built in EXP-013; its ceiling is recomputed under the best router at the
end.
