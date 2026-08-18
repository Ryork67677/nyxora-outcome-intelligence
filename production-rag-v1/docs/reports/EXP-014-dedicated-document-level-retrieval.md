# EXP-014 — Dedicated Document-Level Retrieval

**Status: hypothesis supported — the first configuration in this project to beat the
global control.** `DOC-C-SECTION` reaches **0.875 / 17-of-20** end-to-end against the
global control's 0.775 / 15-of-20: **+2 cases rescued, zero regressions**. Document
routing improved from 17/20 to **18/20**, and to **19/20** in a secondary
configuration — which, notably, retrieves *worse*.

## 1. Executive result

### Document routing (primary metric: all required documents routed @5)

| configuration | @1 | @3 | @5 | @10 | routed@5 | missing@5 |
|---|---|---|---|---|---|---|
| chunk-derived router (EXP-013) | 0.525 | 0.675 | 0.875 | 0.925 | 17/20 | AN-001, AN-012, OA-004 |
| DOC-A-MEAN | 0.375 | 0.725 | 0.825 | **1.000** | 16/20 | AN-001, AN-003, AN-006, AN-012 |
| DOC-B-CENTROID | 0.375 | 0.725 | 0.825 | **1.000** | 16/20 | *(identical to A)* |
| **DOC-C-SECTION** | 0.550 | **0.875** | **0.925** | 0.950 | **18/20** | AN-001, AN-012 |
| DOC-D-MULTIVECTOR | 0.500 | 0.725 | 0.775 | 0.925 | 15/20 | AN-001, AN-003, AN-012, OA-002, OA-004 |
| DOC-C-SECTION + chunk | 0.600 | 0.825 | 0.925 | 0.925 | 18/20 | AN-001, AN-012 |
| *DOC-C-SECTION + chunk + BM25* (secondary) | *0.725* | *0.875* | ***0.950*** | *0.950* | ***19/20*** | *AN-001* |

### End-to-end (frozen Stage 2)

| cell | macro recall | full | spans@10 | doc R | MRR | absent@300 | oracle gap |
|---|---|---|---|---|---|---|---|
| GLOBAL control | 0.775 | 15/20 | 17/22 | 0.925 | 0.449 | 2 | 0.175 |
| DOC-A-MEAN | 0.825 | 16/20 | 18/22 | 0.825 | 0.464 | 4 | 0.125 |
| DOC-B-CENTROID | 0.825 | 16/20 | 18/22 | 0.825 | 0.464 | 4 | 0.125 |
| **DOC-C-SECTION** | **0.875** | **17/20** | **19/22** | 0.925 | **0.474** | 3 | **0.075** |
| DOC-D-MULTIVECTOR | 0.675 | 13/20 | 15/22 | 0.725 | 0.392 | 5 | 0.275 |
| DOC-C-SECTION + chunk | **0.875** | **17/20** | **19/22** | 0.925 | 0.464 | 3 | 0.075 |
| *DOC-C-SECTION + chunk + BM25* | *0.825* | *16/20* | *18/22* | *0.950* | *0.453* | *2* | *0.125* |
| **ORACLE** *(not deployable)* | 0.950 | 19/20 | 21/22 | 1.000 | 0.646 | 0 | 0.000 |

All three reproduction gates pass: GLOBAL 0.775 / 15-of-20, chunk-derived router
0.875 @5 with 17/20, ORACLE 0.950 / 19-of-20.

## 2. Why EXP-014 exists

EXP-012's oracle showed the passage layer is mostly fine — given the right document,
the same retrievers reach 0.950 / 19-of-20 with zero regressions. EXP-013 then
falsified rank aggregation: four rules over chunk rankings all landed on recall@5
0.875 and 17/20. AN-001 explained why — its document contributes one chunk in 300
and the transformer never retrieves it, so no function of those rankings can promote
it. **The limitation was the input, not the arithmetic.**

## 3. What changed, and what did not

Only document retrieval. Stage 2 is byte-identical to EXP-012/013: raw query,
full-corpus BM25 plus the existing transformer cosine restricted to selected
documents, passage RRF `k=60`, top 10, BM25 statistics never recomputed locally.
`top_documents = 5` throughout. Same chunks, same model (fingerprint
`bd95feaeacf98559`), same stored embeddings, same anchors and questions.

Every document vector is a deterministic function of embeddings already stored —
no new model, no training, no external call, no re-chunking. The stored chunk
vectors were verified unit-length (14,209 checked, all 1.000) before use.

## 4. The four representations

All defined in `experiments/EXP-014/preregistration.md` before any scored result.

| name | construction | outcome |
|---|---|---|
| DOC-A-MEAN | mean of the document's normalised chunk vectors | 16/20 routed, 0.825 end-to-end |
| DOC-B-CENTROID | as A, after removing exact-duplicate chunk content | **identical to A on every metric** |
| **DOC-C-SECTION** | mean within each section, then **equal weight per section** | **18/20 routed, 0.875 end-to-end** |
| DOC-D-MULTIVECTOR | per-section vectors; document scores at its **best** section | 15/20 routed, 0.675 — worse than global |

## 5. What actually made the difference: one section, one vote

DOC-C differs from DOC-A by a single decision — sections contribute equally instead
of chunks contributing equally — and that decision is worth **two cases** of routing
and **one case** end-to-end.

The corpus explains it: documents average 29 sections but the largest has **1,445**.
Under a plain chunk mean, a document's vector is dominated by whichever section
happens to generate the most chunks. Equal section weighting removes that.

**DOC-B is the clean negative.** Removing 2,542 exact-duplicate chunks — 18% of the
corpus — changed **nothing**: identical routing, identical end-to-end, identical
MRR. Duplicate content was not distorting the centroid; uneven section size was.

**DOC-D is the clean failure.** Scoring a document at its best section is too
permissive: any document with one vaguely matching section scores highly, so
precision collapses (routing 15/20, document recall 0.725) and it is the only
representation that loses to the global control.

## 6. Better routing is not better retrieval

The single most important nuance in EXP-014:

| configuration | routed@5 | end-to-end |
|---|---|---|
| DOC-C-SECTION | 18/20 | **0.875 / 17-of-20** |
| DOC-C-SECTION + chunk + BM25 | **19/20** | 0.825 / 16-of-20 |

The configuration that routes **best** retrieves **worse**. Adding BM25 document
routing buys AN-012's second document (rank 8 → 5) but changes which five documents
the passage stage competes over, and the net is one case lost.

This is exactly the trap the promotion rule was written to catch: **document recall
is necessary but not sufficient**, and a router must be judged on what it converts.

## 7. AN-001 — improved, still unrouted

| ranking | AN-001 document rank |
|---|---|
| chunk-derived router | **never retrieved at all** |
| **DOC-A-MEAN** | **8** |
| DOC-C-SECTION | 13 |
| DOC-D-MULTIVECTOR | 74 |
| DOC-C-SECTION + chunk | 72 |
| DOC-C-SECTION + chunk + BM25 | 39 |

A document-level representation *can* see AN-001's document — DOC-A puts it at rank
8, where every chunk-derived router put it at 62–72 or nowhere. That confirms the
EXP-013 diagnosis directly.

But it is still outside the top 5, and **fusion actively destroys the gain**: adding
the chunk router, which ranks this document nowhere, pushes it back to 72. AN-001 is
the one case no EXP-014 configuration routes.

## 8. AN-012 — multi-hop, and now solvable

| ranking | document A | document B | both in top 5? |
|---|---|---|---|
| chunk-derived router | 2 | 30 | no |
| DOC-C-SECTION | **1** | 8 | no |
| DOC-C-SECTION + chunk + BM25 | 2 | **5** | **yes** |

The only configuration that routes AN-012 fully is the 19/20 secondary one — the
same configuration that retrieves worse overall.

## 9. Other movements

* **OA-004** (long-standing regression watch): chunk router 7 → DOC-C **3**. Routed,
  and **not** regressed by DOC-C standalone or DOC-C+chunk. It *is* lost by DOC-A+chunk
  and DOC-B+chunk, so the regression watch remains warranted.
* **AN-006**: chunk router 4 → DOC-C **2**, rescued end-to-end.
* **AN-008**: rank 1 in every representation — the case EXP-013's aggregating routers
  lost is safe here.
* **AN-011**: rescued by every DOC-A/B/C configuration.

## 10. Document-level complementarity — revised from EXP-013

EXP-013 concluded BM25 contributes **+0** cases at the document level. That was true
*of chunk-derived routing*. It is **not** true here: adding BM25 to DOC-C moves
routing from 18/20 to 19/20 and lifts recall@1 from 0.550 to 0.725.

The corrected statement: BM25 adds nothing to another chunk-derived ranking, but it
does add something to a document-level representation — they fail differently. It
still does not convert into end-to-end gain, so the recommendation stands that it
does not earn a place in Stage 1 yet.

Fusing DOC-C with the chunk router changes nothing end-to-end (0.875 either way) and
costs AN-001's visibility. **DOC-C standalone is the better system.**

## 11. Reranker gate

| cell | 1–10 | 11–30 | 31–50 | 51–100 | absent | c@30 | c@50 | c@100 |
|---|---|---|---|---|---|---|---|---|
| GLOBAL | 17 | 1 | 1 | 1 | 2 | 0.818 | 0.864 | 0.909 |
| DOC-C-SECTION | **19** | 0 | 0 | 0 | 3 | 0.864 | 0.864 | 0.864 |
| DOC-C + chunk + BM25 | 18 | 2 | 0 | 0 | 2 | **0.909** | 0.909 | 0.909 |
| ORACLE | 21 | 1 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |

Two readings, and they differ:

* **DOC-C-SECTION leaves nothing for a reranker.** 19 of 22 spans are already in the
  top 10 and the remaining 3 are absent at 300 — its ceiling is flat at 0.864 across
  every pool. A reranker cannot reorder what was never retrieved.
* **DOC-C + chunk + BM25 reaches 0.909 at pool 30**, which the global control only
  reaches at pool 100. Evidence sits shallower there.

Neither justifies building a reranker now: the best system's headroom is 3 absent
spans, which is a *retrieval* problem, not a reordering one.

## 12. Cost

| representation | vectors | storage | build | retrieval latency |
|---|---|---|---|---|
| DOC-A / B / C | 202 | 310 KB | 0.04–0.20 s | 0.18–0.35 ms |
| DOC-D | 5,933 | 9.1 MB | 0.17 s | 2.13 ms |

Loading the 14,209 stored chunk vectors takes 1.8 s once. Document-level retrieval
is essentially free at this corpus size — the whole index is smaller than a single
document's chunk embeddings.

## 13. Residual failure taxonomy — after DOC-C-SECTION

| case | classification |
|---|---|
| AN-001 | **DOCUMENT REPRESENTATION FAILURE** — best rank 8 (DOC-A), 13 (DOC-C), outside top 5 |
| AN-012 | **MULTI-HOP ROUTING FAILURE** — second document at rank 8 |
| AN-003 | **WITHIN-DOCUMENT PASSAGE RANKING FAILURE** — routed at rank 5, oracle evidence rank 29 |

Three residual failures, three distinct mechanisms. None is a passage-conversion
failure: every correctly routed document converted.

## 14. AN-003 — unchanged and untargeted, as declared

Routed correctly by every representation (rank 3–7). Its evidence remains the known
within-document defect from EXP-012 — oracle rank 29 inside its own 141-chunk
document. Nothing here was tuned around it.

## 15. Limitations

* n = 20 / 22 spans; one case is 5 percentage points. **No significance claims** —
  DOC-C's +2 cases over global is a two-case difference on twenty questions.
* Four representations were preregistered and run once each. No variant was selected
  after seeing scored results.
* DOC-C's advantage rests on one design decision (equal section weight). It is
  well-motivated by the 1,445-section outlier but is a single corpus's evidence.
* The oracle remains an upper bound with a perfect router, not a deployable system.
* **EXP-NULL remains BLOCKED** — no project generation credential, so there is still
  no measured no-retrieval floor beneath any of these numbers.

## 16. Did document representation solve routing?

**Partly, and it did something better: it converted.**

Routing improved from 17/20 to 18/20 standalone and 19/20 with BM25 — short of the
20/20 that would make routing a solved problem. But for the first time an
intervention **beat the global control end-to-end**: 0.875 / 17-of-20 against 0.775
/ 15-of-20, with **zero regressions**, closing the oracle gap from 0.175 to 0.075.

The EXP-013 diagnosis is confirmed: a document-level representation retrieves
documents that chunk-derived routing cannot see. AN-001 moving from *never retrieved*
to rank 8 is that claim in one number.

## 17. Promotion assessment

The preregistered bar was: routed@5 ≥ 19/20 **and** end-to-end > 0.775 **and**
limited/no regressions.

DOC-C-SECTION meets two of three — end-to-end 0.875 / 17-of-20 with zero
regressions — but routes 18/20, not 19/20. The configuration that does route 19/20
retrieves worse. **So the formal bar is not met, and I am not promoting it.**

It is nonetheless the strongest candidate this project has produced, and the first
to beat the frozen control on paired case movement.

## 18. What the measurements justify next

1. **Replicate DOC-C-SECTION before promoting anything.** A +2-case result at n=20
   needs confirmation, ideally on held-out questions rather than this development set.
2. **Attack AN-001 as a representation problem.** It is now the single
   document-routing failure, its document is visible at rank 8 to a plain mean, and
   fusion is what buries it. Understanding why DOC-A ranks it 8 and DOC-C ranks it 13
   is a concrete, bounded question.
3. **Do not add BM25 to Stage 1 yet.** It improves routing and costs retrieval —
   complexity that does not convert.
4. **A reranker is still not justified.** The best system's residual is 3 spans absent
   at 300; that is retrieval headroom, not reordering headroom.
5. **The golden set is now the binding constraint on inference.** Six of the last
   seven experiments turned on one or two cases. Expanding it would buy more than any
   further retrieval change.
