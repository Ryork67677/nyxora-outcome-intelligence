# EXP-010 — Encoder-Window-Aligned Chunking

**Status: hypothesis falsified.** Truncation was eliminated completely — 23.22% of
chunks truncated → **0%**, corpus token coverage 0.7610 → **1.0000** — and retrieval
did not move at all: **Δ0.000**, zero cases rescued, zero regressed, on both
primary comparisons. Encoder visibility correlated with the EXP-009 result but is
not the causal bottleneck.

## 1. Executive result

| comparison | before | after | delta | rescued | regressed |
|---|---|---|---|---|---|
| **B → D** transformer, control → encoder-aligned | 0.575 | 0.575 | **+0.000** | 0 | 0 |
| **C → E** fusion, control → mixed representation | 0.775 | 0.775 | **+0.000** | 0 | 0 |

The intervention did exactly what it was designed to do at the ingestion layer and
produced no retrieval change whatever. The frozen production baseline does not
move, and neither does the strongest measured configuration.

## 2. Why EXP-010 exists

EXP-009 measured the same transformer at two context windows and found retrieval
tracked how much of a retrieval unit the encoder could see: at 256 tokens 35.2% of
chunks were truncated and dense recall was 0.500; at 512 tokens 23.2% were
truncated and dense recall was 0.575, with fusion reaching 0.775. It concluded that
*context coverage*, not generic chunk length, was the variable worth testing next.

That was a correlation across two window settings, with one observation each.
EXP-010 holds the window fixed at 512 and changes the retrieval unit instead, so
the claim can be tested rather than repeated.

## 3. What EXP-009 established

| window | chunks truncated | corpus token coverage | dense recall | fused recall |
|---|---|---|---|---|
| 256 (reference primary) | 35.2% | 51.3% | 0.500 | 0.625 |
| 512 (preregistered sensitivity) | 23.2% | 76.1% | 0.575 | 0.775 |

## 4. Difference from previous chunking experiments

EXP-005 (chunk size × BM25) and EXP-008 (chunk size × dense) both shortened chunks
using corpus character heuristics; both failed, and EXP-008 showed that splitting a
long but topically coherent unit makes dense retrieval *worse*.

EXP-010 is not "smaller chunks" again. Every limit is measured in the encoder's own
WordPiece tokenization, and the objective is the **largest coherent unit the encoder
can consume whole** — not the smallest unit. Shortness was explicitly not the goal.

## 5. Hypothesis (preregistered)

> If transformer retrieval quality is limited by truncation, then restructuring
> retrieval units so a complete unit fits inside the 512-token window should improve
> retrieval relative to running the same transformer at 512 on the control chunks.

Preregistered readings included: *D within ±1 case of B* → no measurable effect;
*D < B* → alignment hurts. Recorded in `experiments/EXP-010/preregistration.md`
before the chunker was built.

## 6. Encoder and tokenizer constraints — measured, not assumed

| quantity | value | source |
|---|---|---|
| `max_position_embeddings` | 512 | `config.json` |
| special-token overhead | **2** | encoded a probe with and without specials: 5 − 3 |
| usable payload | **510** | 512 − 2 |
| target payload | 448 | conservative, near the top of the window |
| hard payload cap | 480 | headroom for carryover and packing error |

`tokenizer.json` ships its own saved truncation of **128**, which `from_file`
restores. Every measurement path here clears it explicitly.

## 7. Chunker design

`chunker_v4_encoder_aligned` is **derived from the control**, not rebuilt from
source. A control chunk whose payload already fits passes through with the same
source span and the same text; only an oversized chunk is split, at structural
boundaries in the declared priority order. This was decided and committed before
the build, so that D vs B isolates encoder alignment instead of confounding it with
re-grouping.

Carryover is narrow and only at forced splits: a continuation piece carries its
section heading, and a table row group carries the table header. EXP-006 showed
broad repetitive prefixes inflate document frequency, so nothing is prefixed to
whole-unit chunks. `chunk.text` is never mutated — carryover lives in
`search_text`/`context_header`, and `char_start`/`char_end` remain the exact source
span.

## 8. Intervention fidelity

| | control | encoder-aligned |
|---|---|---|
| chunks | 14,209 | 18,579 |
| median encoded tokens | 146 | 181 |
| p95 | 881 | 445 |
| max | 6,857 | **482** |
| chunks > 512 | 3,300 | **0** |
| corpus token coverage | 0.7610 | **1.0000** |

Same document versions, same parser, same evidence anchors, same encoder
fingerprint `bd95feaeacf98559`, same tokenizer, same exact cosine search, same
preregistered RRF parameters. No enrichment, no reranker, no query rewriting, no
ANN.

## 9. Truncation validation

Verified twice, independently:

* the gate script tokenized all 18,579 chunks: **0** exceed the window;
* the embedding build measured truncation through the encoder's own path while
  encoding: `texts_truncated: 0`, `token_coverage: 1.0`.

The corrected control figures (23.22%, 0.7610) match EXP-009's independently
recorded numbers exactly, which is what confirms the measurement is right.

## 10. Chunk-distribution comparison

The aligned distribution is the control's with the >480 tail folded down: more
chunks (18,579 vs 14,209), a slightly higher median, and a hard ceiling at 482.
Nothing was made uniformly small — that was the point.

## 11. Reproduction gates

| cell | target | measured | verdict |
|---|---|---|---|
| A BM25 control | 0.475 / 9-of-20 / 10-of-22 | 0.475 / 9 / 10 | **PASS** |
| B transformer @512 control | 0.575 / 11-of-20 / 13-of-22 | 0.575 / 11 / 13 | **PASS** |
| C BM25 + transformer RRF | 0.775 / 15-of-20 / 17-of-22 | 0.775 / 15 / 17 | **PASS** |

## 12. Transformer B → D result

| cell | macro R | full | spans@10 | doc R | MRR | a@10 | a@50 | a@300 | ms |
|---|---|---|---|---|---|---|---|---|---|
| A BM25 control | 0.475 | 9/20 | 10/22 | 0.825 | 0.280 | 12 | 3 | 1 | 421 |
| B transformer control | 0.575 | 11/20 | 13/22 | 0.925 | 0.339 | 9 | 4 | 1 | 199 |
| **D transformer aligned** | **0.575** | **11/20** | **13/22** | **0.925** | 0.338 | 9 | 5 | 1 | 190 |

Identical on every headline metric. MRR moves by 0.001 and one span leaves the top
50.

## 13. Hybrid C → E result

| cell | macro R | full | spans@10 | doc R | MRR |
|---|---|---|---|---|---|
| C BM25 + transformer, both control | 0.775 | 15/20 | 17/22 | 0.925 | 0.449 |
| **E BM25 control + transformer aligned** | **0.775** | **15/20** | **17/22** | 0.875 | 0.460 |

Mixed representation buys nothing. MRR is marginally better (0.460 vs 0.449) and
document recall marginally worse (0.875 vs 0.925) — both well inside noise at
n=20. The cross-representation fusion machinery works, and has nothing to add.

## 14. Paired rescues and regressions

Zero rescued and zero regressed on both primary comparisons. But **12 of 22 spans
changed rank** — the movements simply never crossed the top-10 boundary:

| movement | spans |
|---|---|
| worsened (no crossing) | 9 |
| improved (no crossing) | 3 |
| unchanged | 9 |
| still unreachable | 1 |

Splitting those 12 by cause is what makes the result interpretable:

* **7 spans** sat in a chunk that was truncated, so their carrying chunk genuinely
  changed — and their **cosine changed**. 3 improved, 4 worsened.
* **5 spans** sat in chunks that already fitted and therefore passed through
  byte-identical — their **cosine is identical to six decimal places**. They moved
  only because *other* documents' chunks were resplit and the competition changed.

That second group is worth stating plainly: rank is relative, so an untouched chunk
still moves when the corpus around it is recut.

## 15. AN-003 deep dive

| cell | evidence rank | doc rank | chunk tokens | answer offset | answer visible | cosine |
|---|---|---|---|---|---|---|
| B transformer control | 299 | — | 801 | 118 | **yes** | 0.4048 |
| D transformer aligned | **193** | — | 442 | — | yes | 0.4482 |

AN-003 improved by 106 places and its cosine rose, which is the largest single
movement in the experiment — and it is still at rank 193, far outside any practical
candidate pool. Its answer was **already visible** in the control chunk at token
offset 118, so this is not a truncation rescue. AN-003 has now failed under BM25,
FastText, the transformer at two windows, and encoder-aligned chunking.

## 16. Truncation-driven cases — the decisive measurement

This is the finding that explains the null result.

Of the 22 evidence spans, 7 sat in a chunk that exceeded the window. But
**chunk-level truncation is not answer-level invisibility**:

| case | control chunk tokens | answer token offset | answer visible at 512? | rank B → D |
|---|---|---|---|---|
| AN-002 | 848 | 346 | yes | 18 → 26 |
| AN-003 | 801 | 118 | yes | 299 → 193 |
| AN-004 | 796 | 235 | yes | 2 → 3 |
| **AN-007** | 848 | **588** | **no** | **16 → 28** |
| AN-010 | 671 | 397 | yes | 49 → 127 |
| AN-012 | 848 | 407 | yes | 8 → 6 |
| OA-002 | 620 | 102 | yes | 7 → 2 |

**Only one answer out of 22 — AN-007 — was actually outside the visible window.**
The other 21 were already fully visible to the encoder. 23% of *chunks* were
truncated, but only 4.5% of *answers* were hidden, because answers sit near the top
of the sections that carry them.

There was therefore almost nothing left for encoder alignment to fix — and the one
case where the hypothesis made a direct prediction, **AN-007, got worse when its
answer was made visible** (16 → 28). That is the sharpest available refutation: the
single span the mechanism was supposed to rescue moved the wrong way.

## 17. Topical-coherence regressions

Five already-fitting spans lost rank (AN-005 8→10, AN-006 185→258, AN-012#1
123→141, OA-003 2→3, OA-004 24→26). Their embeddings are **bit-identical** to the
control, so this is not fragmentation of their own context — it is competition from
resplit neighbours.

The EXP-008 fragmentation failure therefore did **not** repeat, which is a direct
consequence of the pass-through design: units that already fitted were never
touched.

## 18. AN-002 and AN-007

Both worsened: AN-002 18 → 26, AN-007 16 → 28. Neither was inside the top 10 under
the transformer in the first place, so no case changed state, but both moved in the
wrong direction. AN-007 matters most, for the reason in §16.

## 19. OA-004 regression watch

OA-004 moved 24 → 26 under D — outside the top 10 in both, so the EXP-009 fusion
rescue is not undone. Under the fused cells it is unchanged between C and E. It is
still not solved.

Note the A→D comparison does list OA-004 and OA-008 as regressions against BM25,
exactly as A→C did in EXP-009. That is the dense-vs-lexical trade-off, not
something EXP-010 introduced.

## 20. Candidate-depth distribution

| cell | 1–10 | 11–30 | 31–50 | 51–100 | 101–300 | absent |
|---|---|---|---|---|---|---|
| A BM25 | 10 | 7 | 2 | 1 | 1 | 1 |
| B transformer control | 13 | 4 | 1 | 0 | 3 | 1 |
| D transformer aligned | 13 | 4 | 0 | 0 | 4 | 1 |
| C fused control | 17 | 1 | 1 | 1 | 0 | 2 |
| E fused mixed | 17 | 1 | 1 | 1 | 0 | 2 |

## 21. Reranker decision gate — counts only, no reranker was built

Perfect-reranker ceiling, by candidate pool:

| cell | pool 30 | pool 50 | pool 100 |
|---|---|---|---|
| A BM25 | 0.773 | 0.864 | 0.909 |
| B transformer control | 0.773 | 0.818 | 0.818 |
| **D transformer aligned** | 0.773 | **0.773** | **0.773** |
| C fused control | 0.818 | 0.864 | 0.909 |
| E fused mixed | 0.818 | 0.864 | 0.909 |

Alignment did not improve rerankable headroom; at pools 50 and 100 it slightly
**reduced** it, by pushing one span from the 31–50 band out past 100. The fused
cells are unchanged at 0.909.

A reranker would still be working against a ceiling of 0.909 with the fused
retriever already delivering 0.775 — roughly 3 spans of headroom across 20
questions. That is not yet a compelling case.

## 22. EXP-NULL status

**BLOCKED.** `api.anthropic.com` is now reachable but answers `401` without a key;
`api.openai.com` remains blocked at the egress proxy (no HTTP response). The only
related environment variable present is `ANTHROPIC_BASE_URL`, which carries no key.
The session's own harness credentials are not a project credential and were not
used. No credential was fabricated, printed, or inferred. EXP-010 was not delayed
for it.

## 23. Limitations

* n = 20 questions / 22 spans. One case is 5 percentage points. No significance is
  claimed and no result here generalises beyond this corpus.
* A Δ0.000 with 12 spans moving is a *null at the decision boundary*, not proof of
  no effect. A different top-k, or a larger question set, could separate B and D.
* The answer-offset measurement counts tokens from the start of the carrying chunk
  to the start of the evidence span; an answer that begins inside the window but
  extends past it is counted as visible.
* Only one encoder was tested. A model with a longer window, or one more sensitive
  to position, could behave differently.
* The 512 window itself was inherited from EXP-009 and deliberately not swept.

## 24. Did encoder alignment earn promotion?

**No.** The frozen production baseline stays: control chunks, no enrichment, BM25,
`top_k=10`. The strongest measured configuration remains **BM25 + transformer @512
RRF, both on control chunks — 0.775 / 15-of-20**, and EXP-010 gives no reason to
prefer the aligned representation over it.

The aligned chunk set costs 31% more chunks, 48 MB more vectors and a longer
embedding build, and returns nothing. Keeping two chunk representations in
production would be complexity bought with no measured benefit.

## 25. What the measurements justify next

1. **Stop treating truncation as the bottleneck.** It is fixed, completely, and it
   bought nothing. Three chunking interventions (EXP-005, EXP-008, EXP-010) have now
   returned 0, −0.050 and 0.000. **Chunking is not where the remaining recall is.**
2. **The real gap is ranking, not visibility.** 21 of 22 answers were already
   visible to the encoder and 9 still sit outside the top 10. The encoder sees the
   right text and scores it below other text.
3. **Investigate the query side, which has never been touched.** Every experiment so
   far has modified the document representation. The query has been a raw
   user-question string since EXP-000.
4. **A reranker is still not justified** — ceiling 0.909 against 0.775 delivered.
5. **AN-003 needs a failure report, not another chunker.** It has now defeated five
   distinct retrieval configurations, and its answer was visible every time.
