# EXP-012 — Hierarchical Document → Passage Retrieval

**Status: the intervention failed; the diagnostic succeeded.** Hierarchical
retrieval never beat the global control at any routing width. But the
oracle-document diagnostic reached **0.950 / 19-of-20 with zero regressions and
nothing absent at 300** — so global competition *is* causal, and the binding
constraint is **document routing**, not passage scoring.

## 1. Executive result

| cell | topology | macro recall | full | spans@10 | doc R | MRR | absent@300 |
|---|---|---|---|---|---|---|---|
| **A** global raw hybrid (control) | global | **0.775** | 15/20 | 17/22 | 0.925 | 0.449 | 2 |
| B BM25 routing → BM25 local | hierarchical | 0.575 | 11/20 | 12/22 | 0.750 | 0.282 | 7 |
| C transformer routing → tx local | hierarchical | 0.675 | 13/20 | 15/22 | 0.875 | 0.346 | 4 |
| **D** fused routing → fused local | hierarchical | 0.725 | 14/20 | 16/22 | 0.875 | 0.421 | 4 |
| **ORACLE** golden doc → fused local | *diagnostic* | **0.950** | **19/20** | **21/22** | **1.000** | **0.646** | **0** |

`ORACLE / DIAGNOSTIC / NOT DEPLOYABLE` — it reads the golden expected document and
is excluded from every production metric.

**A → D: −0.050, zero rescued, one regressed (OA-004).**
**A → ORACLE: +0.175, four rescued (AN-001, AN-006, AN-011, AN-012), zero regressed.**

## 2. Why EXP-012 exists

AN-003 has shown the same shape since EXP-007: correct document at rank 2–6, answer
chunk absent from the top 300. EXP-010 established that 21 of 22 answers are
visible to the encoder; EXP-011 that query rewriting rescues zero cases. The
remaining candidate explanation was competition — the right passage ranked against
~14,209 chunks, nearly all from irrelevant documents.

## 3. What EXP-011 ruled out

Query-side transformation. Four configurations, **zero rescues**. It also showed
the fused system's value is retriever *disagreement*: the raw fusion bonus was +4
cases over the best single component, and "improving" both retrievers collapsed it
to +1 while making the system worse. EXP-012 therefore reports component and fused
behaviour separately throughout.

## 4. Design and what was frozen

Raw query only. Control chunks only. BM25 `k1=1.2`/`b=0.75` on `simple`,
`all-MiniLM-L6-v2` @512 (fingerprint `bd95feaeacf98559`), stored document
embeddings reused unchanged, cosine, exact search, no ANN, `rrf_k` 60 for both
stages, `top_k` 10. No enrichment, no reranker, no cross-encoder, no LLM, no
metadata filtering, no new chunking.

**Stage 1** collapses each retriever's chunk ranking by `version_id` — a document
ranks at the position of its highest-ranked chunk, and votes exactly once — then
fuses the two document lists with RRF. **Stage 2** restricts candidates to the
routed documents and ranks them by their **full-corpus** scores.

### The scoring constraint that makes this interpretable

BM25's term statistics are **not** recomputed inside the routed documents. The
restriction sits in the scoring select only; the `corpus` and `weighted` CTEs still
compute `n`, `avg_len` and `df` across the whole snapshot. Verified directly: a
chunk's restricted score is bit-identical to its global score. Without this, the
experiment would have confounded topology with lexical re-weighting.

Two planner tests guard the FAIL-0001 regression — the GIN index is still used both
with and without the document restriction.

## 5. Leakage controls

The routing module imports nothing from the eval package and references no golden
symbol. Tests assert the deployable cells carry no oracle document field and that
`ORACLE` is not among the configurations. The golden expected document is used in
exactly one place, and that place is labelled non-deployable in the artifact
itself.

## 6. Reproduction gate

Cell A reproduced the control exactly — **0.775 / 15-of-20 / 17-of-22: PASS**.

## 7. Document-routing quality — the ceiling on everything

Mean routing recall over the 20 cases:

| ranking | @1 | @3 | @5 | @10 |
|---|---|---|---|---|
| BM25 documents | 0.475 | 0.675 | 0.750 | 0.875 |
| transformer documents | 0.525 | 0.675 | 0.875 | 0.925 |
| **fused documents** | 0.525 | 0.800 | **0.875** | 0.950 |

At the preregistered `top_documents = 5`, **all** expected documents are routed for
only **17 of 20** cases. AN-001, AN-012 and OA-004 each lose a document before
Stage 2 begins.

**Stage-1 ceiling: 0.850.** Even a perfect passage ranker could not exceed 17/20
under this routing. D achieved 14/20, so it does not even reach its own ceiling.

## 8. Why hierarchy lost

D is worse than A on every headline metric, and the loss decomposes cleanly:

* **Routing drops documents.** Three cases lose an expected document outright — an
  error the global system cannot make, because it never excludes anything.
* **Complementarity degrades.** The hierarchical fusion bonus is **+1 case**
  (best component 13 → fused 14), against **+4** for the global fusion. This is the
  third time this project has seen a change erode the disagreement RRF feeds on.
* **Rerankable headroom shrinks.** Perfect-reranker ceiling falls from
  0.909 (A, pool 100) to **0.818** (D, flat across pools 30/50/100).

Local pools average **900 chunks — 6.34% of the corpus** — so competition really
was removed. It simply did not help.

## 9. The oracle: passage ranking is nearly fine

With perfect document routing, the same retrievers, the same scores and the same
fusion reach **0.950 / 19-of-20 / 21-of-22**, document recall **1.000**, MRR
**0.646**, and **nothing absent at 300**. Candidate bands: 21 spans in 1–10, one in
11–30, zero beyond.

A perfect reranker over a pool of just **30** would reach **1.000**.

This is the decisive measurement of EXP-012. Global competition was genuinely
suppressing answer-bearing passages — remove it completely and four cases are
rescued with no regressions at all. What fails is our ability to *route*, not our
ability to rank passages once routed.

## 10. AN-003 — the exception, and now precisely characterised

| stage | value |
|---|---|
| BM25 document rank | 3 |
| transformer document rank | 5 |
| **fused document rank** | **3 — routed correctly into the top 5** |
| chunks in the top-5 pool | **3,125** |
| global evidence rank | absent@300 |
| BM25 hierarchical | absent@300 |
| transformer hierarchical | absent@300 |
| fused hierarchical | absent@300 |
| chunks in its own document | 141 |
| **oracle evidence rank** | **29** |

AN-003's document is routed correctly, yet hierarchy does not help it — because
the top-5 pool still holds 3,125 chunks, 22% of the corpus. Only when competition
is cut to its own 141-chunk document does the evidence appear at all, and even then
at **rank 29**, outside the top 10.

**AN-003 is the one case the oracle does not rescue.** It is a genuine
within-document passage-ranking failure: searching a single small document, the
correct passage still ranks 29th. That is exactly the preregistered Outcome C, and
it now applies to precisely one case rather than to the system.

## 11. Failure taxonomy

Every case the control does not fully recall:

| case | classification |
|---|---|
| AN-001 | **DOCUMENT ROUTING FAILURE** — expected document outside top 5 |
| AN-012 | **DOCUMENT ROUTING FAILURE** |
| AN-003 | **WITHIN-DOCUMENT PASSAGE RANKING FAILURE** — oracle rank 29 |
| AN-006 | MIXED / UNCLEAR — oracle rescues it, hierarchy does not |
| AN-011 | MIXED / UNCLEAR — rescued by C, lost again in D |

Three of the five remaining failures are routing problems, one is a passage-scoring
problem, and OA-004 additionally loses a document at N=5 despite being recalled by
the control.

## 12. Regression: OA-004

The one case D loses relative to A. Its expected document falls outside the routed
top 5, so its evidence is unreachable regardless of local ranking. This is the
characteristic hierarchical failure — an error of *exclusion* that the global
system structurally cannot make.

## 13. Exploratory sensitivity — N = 3 and N = 10

Run only after the primary result was frozen. **Labelled exploratory; the primary
result is `top_documents = 5`.**

| routing width | D macro recall | D full | all docs routed | local pool |
|---|---|---|---|---|
| N = 3 | 0.750 | 15/20 | 16/20 | — |
| **N = 5 (primary)** | **0.725** | **14/20** | **17/20** | 900 (6.3%) |
| N = 10 | **0.775** | **15/20** | 19/20 | 1,701 (12.0%) |

Hierarchy **converges to the global control** as routing widens: at N = 10 it
matches A exactly (0.775 / 15-of-20 / 17-of-22). It never exceeds it at any width.
The N=3 vs N=5 difference is one case — noise at this sample size, and not a reason
to prefer N=3.

This is the clearest statement of the result: **the best hierarchical system is the
one that stops being hierarchical.**

## 14. Cost

Hierarchy is not free. It adds a deep global retrieval (depth 300) to build
document rankings, a collapse-and-fuse stage, then a second round of ranking —
roughly double the retrieval work of the global control, for a worse result.

## 15. Limitations

* n = 20 / 22 spans; one case is 5 percentage points. No significance claims.
* The oracle is an upper bound with a perfect router; no achievable router is
  implied by it. It says the *headroom* exists, not that it is reachable.
* Routing quality was measured for one collapse rule (highest-ranked chunk, one
  vote per document). Other rules — score aggregation, top-k voting, document-level
  embeddings — are untested and could route better.
* Document ranking was derived from a depth-300 chunk ranking; deeper lists might
  route differently.
* AN-003's oracle rank of 29 is a single case.

## 16. Was global competition causal?

**Yes — and that is the surprise.** Every previous mechanism this project proposed
turned out not to be causal: chunk size (×3), enrichment, encoder visibility, query
formulation. This one is. Removing cross-document competition entirely takes the
system from 0.775 to 0.950 with zero regressions.

But **the intervention still failed**, because achievable routing is not good
enough to realise it. The fused router puts all expected documents in the top 5 for
only 17 of 20 cases, and every document it drops is a case lost outright.

The honest summary: *global competition is a real bottleneck; document → passage
retrieval as built is not the way to remove it.*

## 17. What the measurements justify next

1. **Work on document routing, not passage ranking.** The oracle says passage
   ranking is already worth 19/20. Routing recall @5 of 0.875 is the constraint, and
   it is a genuinely different problem from everything tried so far.
2. **Do not deploy hierarchy at any N.** It never beats global and it introduces an
   exclusion failure mode that global retrieval cannot have.
3. **A reranker is now justified for the first time — but only behind good
   routing.** With perfect routing, a perfect reranker over a pool of 30 reaches
   1.000. Behind current routing the ceiling is 0.818, *worse* than global's 0.909.
   Sequence matters: routing first, reranking second.
4. **AN-003 is now a single, precisely characterised defect** — within-document
   passage ranking in a 141-chunk document — and deserves a failure report rather
   than another system-wide experiment.
5. **Keep measuring the fusion bonus.** Three separate changes have now improved
   components while degrading the ensemble.
6. **EXP-NULL remains BLOCKED** — still no measured no-retrieval floor.
