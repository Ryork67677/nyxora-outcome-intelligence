# EXP-012 preregistration — recorded BEFORE the hierarchical retriever was built

## 1. Hypothesis

If global chunk competition is suppressing answer-bearing passages inside
already-correct documents, then a two-stage **document → passage** retrieval
topology should improve passage recall **without changing the underlying
retrievers**.

This must be falsifiable. Hierarchy is not assumed to help, and the experiment is
not to be steered toward making it succeed.

## 2. Why this diagnosis

Across EXP-011, AN-003 showed the same pattern in every configuration: the correct
document ranked **2nd–6th**, while the answer chunk was **absent from the top
300**. EXP-010 had already established that 21 of 22 answers are *visible* to the
encoder, and EXP-011 that query rewriting rescues **zero** cases.

So the system knows which document is relevant and fails to rank the right chunk
inside it. One candidate explanation is that the correct passage is competing
against ~14,209 chunks, most from irrelevant documents. EXP-012 removes that
competition and measures what happens.

## 3. Frozen — everything except retrieval topology

Raw query only (EXP-011 rescued 0 cases with transformed queries, so combining the
two would confound attribution). Control chunks `cs_v1_control` only. BM25
`k1=1.2` / `b=0.75` on `simple`. `all-MiniLM-L6-v2` @512, fingerprint
`bd95feaeacf98559`, stored document embeddings reused unchanged. Cosine, exact
search, no ANN. `rrf_k` 60. `top_k` 10. Evidence anchors and questions unchanged.

No enrichment, no reranker, no cross-encoder, no LLM, no metadata filtering, no
new chunking, no query rewriting.

## 4. Scoring constraint — corpus statistics must not move

The intervention is candidate **topology**, not lexical statistics. So local
ranking reuses the **full-corpus** scores:

1. compute normal full-corpus BM25 scores;
2. compute normal full-corpus transformer cosine scores;
3. derive document rankings from those;
4. restrict candidates to the selected documents;
5. re-rank those candidates by their **existing full-corpus** scores;
6. fuse locally with RRF.

BM25 IDF is **not** recomputed inside the selected documents. Doing so would
change term statistics and confound topology with lexical re-weighting. A
local-IDF variant, if ever tested, is exploratory and must be labelled as such.

## 5. Stage 1 — document ranking

Each retriever's full chunk ranking is collapsed by `version_id`: a document's
rank is the position of its **highest-ranked chunk**. A document appearing many
times in the chunk list gets **one** document vote, not many — otherwise a
document with many mediocre chunks would outrank one with a single excellent
chunk, which is the opposite of what routing should do.

The two document lists are fused with RRF at `rrf_k = 60`.

## 6. Routing budget — preregistered at 5

`top_documents = 5` for the primary experiment. It is a fixed engineering
compromise between keeping relevant documents and shrinking the candidate space,
chosen **before** any hierarchical result was observed and specifically **not**
because it rescues AN-003.

Sensitivity runs at 3 and 10 may follow **after** the primary result is frozen and
must be labelled exploratory. The primary result is not to be replaced by whichever
N scores best.

Five also guards the multi-hop cases: some questions need evidence from more than
one document, so Stage 1 must return several documents rather than assume one.

## 7. Cells

| cell | Stage 1 | Stage 2 | role |
|---|---|---|---|
| A | none (global) | BM25 + transformer RRF | control; must reproduce 0.775 / 15-of-20 / 17-of-22 |
| B | BM25 doc ranking | BM25 local | diagnostic — does hierarchy help lexical alone? |
| C | transformer doc ranking | transformer local | diagnostic — is global competition hurting the dense side? |
| D | fused doc ranking | BM25 + transformer local RRF | **primary intervention** |
| ORACLE | golden expected document | BM25 + transformer local RRF | **diagnostic only, not deployable** |

If A fails to reproduce, stop and diagnose before interpreting anything else.

## 8. The oracle diagnostic and its containment

`EXP-012-ORACLE-DOC` is the one place the golden expected document may be used. It
answers the question the primary cells cannot: *does passage ranking stay broken
even when routing is perfect?*

* Global absent@300 → hierarchical top-10/30 → oracle good ⇒ global competition
  was genuinely suppressing the passage.
* Global absent@300 → hierarchical poor → **oracle still poor** ⇒ the failure is
  true **within-document passage scoring**, and hierarchy cannot fix it.

That distinction determines the next experiment, so the oracle is a primary
deliverable — but it is **ORACLE / DIAGNOSTIC / NOT DEPLOYABLE**, excluded from
every production metric, and enforced by tests that the primary cells cannot read
golden document identifiers.

## 9. Measurement order

Document-routing recall@1/3/5/10 is reported **before** Stage 2 runs, for the BM25,
transformer and fused document rankings. If the correct document is not routed,
no passage ranking can recover its evidence, so routing recall is the ceiling on
everything downstream.

## 10. Complementarity must stay measured

EXP-011 showed the fused system's value comes from useful disagreement: the raw
fusion bonus was **+4 cases** over the best single component, and normalization
collapsed it to +1 while *improving* both components. So EXP-012 reports component
and fused behaviour separately throughout, and computes the hierarchical fusion
bonus against the global one. A change that improves both retrievers can still
degrade the ensemble.

## 11. Preregistered readings

n = 20 / 22 spans. One case = 5 percentage points. No significance claims.

| outcome | reading |
|---|---|
| D rescues several cases with limited/no regressions | global competition is a real bottleneck; hierarchy earns further work |
| AN-003 routed correctly and its evidence moves into the top 10–30 | AN-003 was primarily a global-competition problem |
| document rank ≤ 5 but oracle passage rank still poor | **within-document passage ranking** is the real problem; hierarchy cannot fix it |
| D regresses | check whether documents were routed out, or local competition changed complementarity, or multi-hop cases lost a needed document |
| A ≈ D | global competition is not the bottleneck; stop changing retrieval topology |

**Regression watch.** The control fully recalls 15 of 20. Aggregate gains that hide
losing cases are not improvements; every regression is reported with its routing
status and local ranks.

## 12. Failure taxonomy — a primary deliverable

Every case not fully recalled by the control is classified:

* **DOCUMENT ROUTING FAILURE** — expected document outside top 5;
* **GLOBAL COMPETITION FAILURE** — correct document routed and hierarchy strongly
  rescues the evidence;
* **WITHIN-DOCUMENT PASSAGE RANKING FAILURE** — even oracle-document search ranks
  the evidence poorly;
* **MIXED / UNCLEAR**.

## 13. Cost

Hierarchy is not free: it adds a document-collapse and fusion stage and a second
round of ranking. Retrieval calls, local pool sizes (mean/median/min/max against
the 14,209 global chunks), and per-stage latency are all reported.

## 14. Promotion

The frozen production baseline stays BM25 / control chunks / `top_k=10`. The
strongest measured configuration remains the global raw-query hybrid at
0.775 / 15-of-20. Hierarchy must win on paired case movement, not on one aggregate
number, and must not be promoted merely because the canonical case improves.
