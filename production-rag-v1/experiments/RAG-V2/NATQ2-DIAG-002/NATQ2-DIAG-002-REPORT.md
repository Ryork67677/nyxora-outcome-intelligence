# NATQ2-DIAG-002 — SYSTEM-H pre-CE trace reconstruction

**Diagnostic only.** NATQ-002 validation is exposed development data. SYSTEM-H validation
remains **CLOSED as FAIL**. This task did not evaluate a system, did not run the
cross-encoder, and did not consume a validation run: `validation_runs_consumed` stays **1**,
**2** remain unused. The reserve was not opened.

## Replay identity

The deterministic candidate stages were replayed for all 40 validation queries using
19 hash-pinned implementations recovered from
`origin/grok/v2-natq-20260903`. Every CE score is the persisted EVAL-NATQ2-H-002 value, joined by
`(case_id, chunk_id)`; the join was required to be a bijection on every case and was.

| Reproduction check | Result |
| --- | --- |
| Final top-10 rows (400) | **0 mismatches** |
| Case hit vector (40) | **0 mismatches** |
| Per-case span ranks | **0 mismatches** |
| Aggregate metrics | **identical** |
| **REPLAY IDENTITY EXACT** | **True** |

The per-case CE map was persisted at 6 decimals while the 400 top-10 rows carry full
precision; both were used, full precision where available. The final ranking reproduced
exactly regardless, which is what establishes that the rounding never flipped an ordering at
the depth-10 boundary.

## The headline correction

NATQ2-DIAG-001 located the loss in the ranking stage and named the cross-encoder. That is
still where the 12 spans die — but the reconstructed pre-CE ordering shows **retrieval was
weak on them too**, so retrieval ordering offers almost no protection to build on.

**Only 3 of the 12 ranked-out gold spans were inside the pre-CE retrieval top 10.**
Nine of twelve sat at pre-CE rank **> 20**, as deep as 68.

| pre-CE retrieval rank | 12 ranked out | all 44 in pool | 32 that reached top 10 |
| --- | ---: | ---: | ---: |
| ≤ 3 | 0 | 17 | 17 |
| ≤ 5 | 2 | 5 | 3 |
| ≤ 10 | 1 | 9 | 8 |
| ≤ 20 | 0 | 2 | 2 |
| > 20 | 9 | 11 | 2 |

**RETRIEVAL_TOP10_TO_FINAL_OUT = 3/57 spans, 3/40 cases** (B28, D27, E06).
All three finished at final rank 11, 11 and 14 — just outside. This is a mechanism
measurement, not a system result.

## IN_POOL_RANKED_OUT — all 12

| case | span | covering chunk | origin | A rank | local rank | proj | pre-CE | CE score | CE rank | final |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A07 | 1 | `chk_1a2b0bc35a74…` | a_pool | 32 | — | — | **56** | -2.116 | 63 | 68 |
| A30 | 0 | `chk_600fe1685960…` | a_pool | 40 | — | — | **56** | -2.268 | 18 | 31 |
| B09 | 0 | `chk_c489a281149a…` | a_pool | 11 | — | — | **26** | -6.37 | 20 | 20 |
| B09 | 1 | `chk_c489a281149a…` | a_pool | 11 | — | — | **26** | -6.37 | 20 | 20 |
| B22 | 0 | `chk_e8cbc2bb2f22…` | a_pool | 47 | — | — | **68** | -7.578 | 50 | 65 |
| B28 | 0 | `chk_d09b6e55e4ac…` | a_pool | 4 | 1 | — | **4** | -4.518 | 17 | 11 |
| C03 | 0 | `chk_203715961057…` | a_pool | 38 | — | — | **59** | -2.389 | 31 | 44 |
| C09 | 0 | `chk_b110a90dc7e7…` | a_pool | 11 | — | — | **25** | 0.096 | 19 | 20 |
| D03 | 0 | `chk_0412b3a3e3c2…` | a_pool | 80 | 7 | — | **22** | -4.226 | 17 | 19 |
| D08 | 0 | `chk_e43a73ae33d3…` | a_pool | 14 | — | — | **46** | -3.351 | 7 | 15 |
| D27 | 0 | `chk_5692cd732889…` | a_pool | 4 | 1 | — | **4** | -3.378 | 32 | 11 |
| E06 | 0 | `chk_6504a1c6f15f…` | a_pool | 7 | 9 | — | **10** | -2.796 | 30 | 14 |

## Retrieval-only vs SYSTEM-H, paired

`RETRIEVAL_ONLY_TOP10_HIT` is an internal mechanism diagnostic. **It is not a qualified
system** and must never be reported as one.

| | H hit | H miss |
| --- | ---: | ---: |
| **retrieval hit** | 21 | 3 |
| **retrieval miss** | 2 | 14 |

Retrieval-only diagnostic rate 24/40
against SYSTEM-H's closed 23/40. The CE/blend stage trades 3 cases away (B28, D27, E06) and
buys 2 back (C11, D29). Near-parity on this metric does not make the retrieval ordering a
system, and does not license reporting 24/40 as a result.

## BM25 regression cases

| case | classification |
| --- | --- |
| B09 | **RETRIEVAL_AND_CE_BOTH_WEAK** |
| B28 | **RETRIEVAL_ALREADY_CORRECT_CE_DESTROYED** |
| D27 | **RETRIEVAL_ALREADY_CORRECT_CE_DESTROYED** |

B09's gold span sat at SYSTEM-A rank 11 and pre-CE rank 26 with a CE score of −6.37 — both
stages were weak. B28 and D27 both had pre-CE rank 4 and were pushed to final rank 11 by CE
ranks of 17 and 32.

## Channel contribution

| population | BOTH_A_AND_LOCAL | SYSTEM_A_ONLY | LOCAL_BM25_ONLY | PROJECTION_ONLY |
| --- | ---: | ---: | ---: | ---: |
| in pool (44) | 35 | 9 | 0 | 0 |
| final top 10 (32) | 31 | 1 | 0 | 0 |
| ranked out (12) | 4 | 8 | 0 | 0 |

Corroboration across both retrieval channels tracks survival closely: 31 of the 32 surviving
gold spans were found by SYSTEM-A **and** local BM25, while 8 of the 12 ranked-out spans were
SYSTEM-A only. Local BM25 currently contributes an average of
10.0 additive candidates out of
99.2 available (L = 10).

## Projection

| quantity | value |
| --- | ---: |
| total projection candidates | 800 |
| gold spans covered by projection | **0** |
| projection candidates entering final top 10 | 12 |
| queries with ≥ 1 projection top-10 candidate | 8 |
| mean projection top-10 slots per query | 0.3 |
| displaced slots whose next candidate covers gold | **0** |

| case | projection slot | next non-projection | its final rank | covers gold |
| --- | ---: | --- | ---: | --- |
| A12 | 8 | a_pool | 11 | False |
| A23 | 10 | a_pool | 11 | False |
| B14 | 1 | a_pool | 11 | False |
| B14 | 7 | a_pool | 12 | False |
| B14 | 10 | a_pool | 13 | False |
| C01 | 8 | a_pool | 11 | False |
| C03 | 8 | a_pool | 11 | False |
| C03 | 10 | local_bm25 | 12 | False |
| C10 | 8 | a_pool | 11 | False |
| C10 | 10 | local_bm25 | 12 | False |
| C16 | 2 | a_pool | 11 | False |
| D19 | 8 | a_pool | 11 | False |

For every one of the 12 projection-occupied slots, the next non-projection candidate in frozen
final score order covers **no** gold span. Projection is therefore **inert** on gold recall
here, not actively harmful. No removal was simulated and no claim is made that removing it
improves any metric.

## Localization failures — the 13 spans with no covering candidate

| case | span | doc in pool | doc in SYSTEM-A | doc in local parents | same-doc candidates | nearest final | nearest pre-CE | projection covered |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| A12 | 0 | True | True | True | 6 | 13 | 10 | False |
| A12 | 1 | True | True | True | 6 | 13 | 10 | False |
| A12 | 2 | True | True | True | 6 | 13 | 10 | False |
| A30 | 1 | True | True | False | 1 | 31 | 56 | False |
| B18 | 0 | True | True | False | 4 | 40 | 48 | False |
| B19 | 0 | True | True | True | 7 | 2 | 2 | False |
| B19 | 1 | True | True | True | 7 | 2 | 2 | False |
| C01 | 0 | True | True | False | 2 | 57 | 66 | False |
| C01 | 1 | True | True | False | 2 | 57 | 66 | False |
| C03 | 1 | False | False | False | 0 | None | None | False |
| C05 | 0 | True | True | False | 1 | 101 | 91 | False |
| E01 | 0 | True | True | True | 38 | 1 | 5 | False |
| E27 | 0 | True | True | False | 3 | 45 | 44 | False |

**Document discovery is close to solved; within-document localization is not.**
12 of 13 had the gold document in SYSTEM-A and only
1 was absent from the pool entirely. Only
6 of 13 had that document among the local-BM25 parents, so the
localization stage was not even pointed at the right document for the other seven. E01 is the
clearest case: 38 candidates from the gold document are in the pool, the nearest sits at final
rank 1, and none of them covers the gold span. B19 is the same shape at rank 2. Projection
windows covered the gold chunk in 0 of 13.

## Candidate ceiling confirmation

| ceiling | DIAG-002 | DIAG-001 | agrees |
| --- | --- | --- | --- |
| any-span | 33/40 | 33/40 | ✓ |
| every-span | 31/40 | 31/40 | ✓ |
| span | 44/57 | 44/57 | ✓ |

## Architecture recommendation — exactly one

### **B. NEW RERANKER MODEL**

The evidence is in the pool (44/57) but the frozen retrieval ordering offers no useful
protection to build a guard on: only 3 of the 12 ranked-out spans were in the pre-CE top 10,
and 9 were beyond rank 20. That is the decision rule's condition for B, and it rules out A.

**Why not A (retrieval-protected reranker).** A guard keyed on the existing retrieval ordering
can rescue at most the 3 RETRIEVAL_TOP10_TO_FINAL_OUT cases, taking case_hit@10 from 23/40 to
26/40 = 0.65 — exactly the FAIL floor, still far below the 0.80 PASS floor. A retrieval signal
that ranks 9 of 12 misses beyond position 20 is not a signal worth protecting.

**Why not C (candidate-generation first).** Ranking still has room: 23/40 achieved against a
33/40 any-span ceiling is 10 cases, and the floor needs 9. Candidate generation is not yet the
binding constraint, though it is close to becoming one.

**Why not D (mixed).** One mechanism does dominate — the reranker misorders evidence it
already holds, on 12 spans across 10 cases.

**The qualification caveat stands and is not softened by this recommendation.** The any-span
ceiling is 33/40 = 0.825 against a 32/40 = 0.80 floor: **one case of oracle margin**. A perfect
reranker reaches 0.825 and a single benchmark case away from that is a failure. A ranking fix
alone is therefore **not** sufficient evidence for reserve, and this analysis does not claim
otherwise. The localization evidence above says where the ceiling work would go — parent
selection for the localization stage, which currently reaches the gold document for only 6 of
the 13 missing spans.

No parameter search was performed. No guard K was tested, no blend weight changed, no
projection removed, no retriever run, no candidate pool altered.
