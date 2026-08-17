# Production RAG — EXP-005 Re-Chunking Results

**Verdict up front: the chunk-granularity hypothesis is not supported.** Bounding chunk
size — the intervention the hypothesis actually names — rescued **zero** questions.
The gain that did appear came from a different mechanism (contextual enrichment), and
the single case that motivated the whole hypothesis is **still unretrievable** after
its evidence share of its chunk improved 2.9×.

Source of truth for every number below: `experiments/EXP-005/paired-analysis.json`,
`experiments/EXP-005/chunk-distribution.json`, `experiments/EXP-005/evidence-mapping.json`,
and the two results files under `experiments/EXP-005A_rechunk_bounded_bm25/` and
`experiments/EXP-005B_rechunk_technical_bm25/`.

---

## 1. Hypothesis

> If chunk granularity is the dominant retrieval bottleneck, improving structure-aware
> chunking should materially increase span-level retrieval recall while document-level
> recall remains approximately stable.

The prediction under test, from FAIL-0002: span recall (0.455–0.500) should move toward
the document-level ceiling (0.818), because 8 of the 12 spans lexical retrieval missed
had the correct *document* in the top 10.

Falsification condition, fixed before running: if span recall barely moves while the
chunk-size distribution demonstrably changes, granularity is not the bottleneck.

---

## 2. Experimental controls

Held constant across all three configurations:

| Held constant | Value |
|---|---|
| Raw corpus documents | unchanged; nothing re-fetched |
| Document versions | the same 202 `version_id`s |
| Golden questions | the same 20 retrieval-scored cases |
| Evidence spans | the same 22, unmodified |
| Evidence anchoring | `(version_id, section_path, char_start, char_end)` |
| Retriever | BM25, `k1=1.2`, `b=0.75`, unchanged |
| `top_k` | 10 |
| Query text | unchanged |
| Scoring implementation | `rag_v1.evals.retrieval_eval` unchanged |
| Provider distribution | 139 Anthropic / 63 OpenAI |

Not added: reranker, query rewriting, agent loop, BM25 retuning, larger `k`, RRF tuning.

Re-chunking reads each version's stored `normalized_text` and re-derives sections with
the same parser, so nothing upstream of chunking can move.

### Two changes were required to run this experiment at all

**A chunk-set dimension** (`sql/002_chunk_sets.sql`). The schema had
`UNIQUE (version_id, ordinal)` on `chunk`, and retrieval reached chunks through
`snapshot → version` with no notion of *which* chunking. A second chunking of the same
versions was therefore impossible to store and impossible to query in isolation. The
migration is additive: existing rows were adopted into `cs_v1_control` and a snapshot now
pins both its versions and its chunking.

**Control fidelity was verified, not assumed.** After the migration, EXP-000 was re-run:
macro recall 0.475, 9/20 fully recalled, and the results file is **byte-identical** to the
committed one.

That check surfaced a latent defect worth recording: scoping the query with an extra join
on `corpus_snapshot` made the planner abandon the GIN index and the evaluation went from
under a second to over a minute. Scoping instead with a scalar equality predicate restored
the original plan. A second, subtler issue also appeared — two chunks with *mathematically
equal* BM25 scores swapped rank because `sum()` accumulates in plan-dependent order, giving
a 3.55e-15 difference. Ordering now rounds before sorting so exact ties resolve on
`chunk_id`. Recall was never affected; 2 of 200 hit positions were.

---

## 3. Chunk-distribution comparison

| Chunker | chunks | mean | median | p90 | p95 | p99 | **max** | >2000 | >3000 | > own hard limit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `chunker_v1_control` | 14,209 | 1,097 | 508 | 3,466 | 3,485 | 3,500 | **16,096** | 3,069 | 2,543 | n/a — enforces none |
| `chunker_v2_bounded` | 20,526 | 757 | 917 | 1,193 | 1,247 | 1,879 | **1,999** | 0 | 0 | **0** |
| `chunker_v3_technical` | 20,516 | 764 | 907 | 1,192 | 1,200 | 1,837 | **1,999** | 0 | 0 | **0** |

Zero unexplained chunks above the hard limit in V2/V3, and no exceptions are claimed.

The control's true maximum is **16,096** characters. FAIL-0002 quoted 12,341, which was
the maximum over the *Anthropic* subset only; the global maximum is larger and sits on the
OpenAI side. The correction makes the control's defect worse, not milder.

Chunk types — V2: 15,900 prose / 4,239 code / 387 table. V3: 15,201 prose / 4,858 code /
281 table-row groups / 176 table, of which only **60** are parameter entries.

**The intervention was real.** Mean chunk length fell 31%, the p90 fell from 3,466 to
1,193, and 3,069 chunks over 2,000 characters became none. Any claim that granularity did
not change is refuted by this table — which is what makes the recall result below
interpretable rather than inconclusive.

### Evidence mapping preserved

`scripts/validate_evidence_mapping.py` passes for all three chunk sets: 22/22 spans map to
a chunk with the same section path, 0 offset mismatches, 0 invalid section paths. Mean
evidence share of its containing chunk: control 0.133 → V2 0.154 → V3 0.116.

---

## 4. V1 baseline and EXP-005 results

| Configuration | macro span recall | fully recalled | spans | document recall |
|---|---:|---:|---:|---:|
| EXP-000 control (`chunker_v1_control`) | 0.475 | 9/20 | 10/22 | 0.825 |
| **EXP-005A** bounded (`chunker_v2_bounded`) | 0.500 | 9/20 | 11/22 | 0.825 |
| **EXP-005B** technical (`chunker_v3_technical`) | **0.650** | **12/20** | 14/22 | 0.900 |

By category:

| Category | control | V2 | V3 |
|---|---:|---:|---:|
| exact_lookup (13) | 0.538 | 0.538 | 0.615 |
| multi_hop (2) | 0.250 | 0.500 | 0.500 |
| normal (2) | 0.500 | 0.500 | 1.000 |
| version_conflict (2) | 0.500 | 0.500 | 1.000 |
| ambiguous (1) | 0.000 | 0.000 | 0.000 |

---

## 5. EXP-005A — bounded chunking rescued nothing

**Paired result: 0 rescued, 0 regressed, net 0.** One case (AN-012) changed partially,
recovering one of its two spans. The entire 0.475 → 0.500 macro movement is that single
half-case.

The span-level view is the more damning one. Across all 22 spans:

| | V2 bounded | V3 technical |
|---|---:|---:|
| rank improved | 8 | 10 |
| rank **worsened** | **9** | 6 |
| unchanged | 5 | 6 |
| newly retrievable (was unreachable) | **0** | **0** |
| lost entirely | 0 | 0 |

Bounding chunk size moved ranks roughly at random: 8 up, 9 down. And **not one span that
was previously unreachable became reachable** — in either configuration, at a probe depth
of 300. Every gain is reshuffling among spans that were already retrievable.

Document recall was unchanged at 0.825, exactly as the hypothesis predicted. But the
hypothesis predicted that *alongside* a span-recall rise, and the rise did not happen.

---

## 6. EXP-005B — technical chunking helped, for a different reason

**Paired result: 3 rescued (AN-004, AN-008, AN-010), 0 regressed, net +3.** Macro recall
0.650, 12/20 fully recalled.

This is a real improvement and it is not the hypothesis being confirmed. V3 changes two
things at once relative to V2:

1. Finer units for reference structure (table row groups, parameter entries).
2. **A context header prepended to the indexed text** of those units, naming the section
   path and, for tables, the column headers.

The second is contextual enrichment, not chunk granularity. It also explains why
**document recall rose to 0.900** — a movement the experimental design expected to stay
flat. Adding section-path terms to the indexed text makes documents easier to find, so V3
is not a clean chunking intervention and must not be reported as one.

The honest reading: V2 isolates granularity and shows it does nothing. V3 confounds
granularity with enrichment and shows a gain. The gain is therefore attributable to
enrichment, not to the hypothesis under test.

---

## 7. Paired question changes

| Case | Category | control | V2 | V3 | rank: control → V2 → V3 |
|---|---|---:|---:|---:|---|
| AN-001 | exact_lookup | 0.00 | 0.00 | 0.00 | 19 → 29 → 32 |
| AN-002 | exact_lookup | 0.00 | 0.00 | 0.00 | 27 → **172** → 171 |
| AN-003 | exact_lookup | 0.00 | 0.00 | 0.00 | — → — → — |
| AN-004 | exact_lookup | 0.00 | 0.00 | **1.00** | 12 → 11 → **10** |
| AN-005 | exact_lookup | 1.00 | 1.00 | 1.00 | 4 → 3 → 1 |
| AN-006 | exact_lookup | 0.00 | 0.00 | 0.00 | 29 → 36 → 32 |
| AN-007 | exact_lookup | 0.00 | 0.00 | 0.00 | 18 → 34 → 41 |
| AN-008 | normal | 0.00 | 0.00 | **1.00** | 12 → 11 → **9** |
| AN-009 | version_conflict | 1.00 | 1.00 | 1.00 | 1 → 1 → 1 |
| AN-010 | version_conflict | 0.00 | 0.00 | **1.00** | 49 → 62 → **1** |
| AN-011 | ambiguous | 0.00 | 0.00 | 0.00 | 54 → 153 → 139 |
| AN-012 | multi_hop | 0.00 | 0.50 | 0.50 | 47,117 → **6**,223 → 6,248 |
| OA-001…OA-008 | mixed | 7 of 8 full | 7 of 8 | 7 of 8 | unchanged; OA-006 stays partial in all three |

AN-004 and AN-008 were rescued by rank movements of **one and three positions** across the
k=10 boundary (12→10, 12→9). On a 20-case set those are not robust wins; they are two
questions that happened to sit on the threshold.

---

## 8. Major rescue — AN-010 (rank 49 → 1)

**Query:** "What is the current state of the `claude-opus-4-1-20250805` model?"
**Expected evidence:** `['Model status']`, span 5671–5769, in the model-deprecations page.

| Config | chunk carrying the evidence | length | rank |
|---|---|---:|---:|
| control | `## Model status` heading + a Note + the entire status table | 2,317 | 49 |
| V2 bounded | the whole table run | 1,871 | **62** (worse) |
| V3 technical | a 4-row group, `table_row`, with a 223-char context prefix | 415 | **1** |

The V3 chunk's indexed text begins:

```
[Model status] | API model name | Current state | Deprecated | Tentative retirement date |
```

**Why it changed.** Query terms are `current`, `state`, `model`, `claude-opus-4-1-20250805`.
In the control, the identifier sits in a 2,317-character chunk whose BM25 length
normalization dilutes it. V2 shrank the chunk to 1,871 and the rank got *worse*, because
splitting removed the surrounding `Model status` prose that carried `state` and `model`.
V3 restored exactly those terms as an explicit header while keeping the unit at 415
characters — so the row now matches `current`, `state` and the identifier simultaneously.

The mechanism is the header, not the size. V2 proves it: same corpus, smaller chunk, worse
rank.

---

## 9. Regression — AN-002 (rank 27 → 172)

**Query:** "Which HTTP status code does the Claude API return with the `request_too_large`
error type?"
**Expected evidence:** `['HTTP errors']`, span 1636–1721, in the API errors page.

| Config | chunk length | query terms present | rank |
|---|---:|---:|---:|
| control | 3,327 | **12 of 13** | 27 |
| V2 bounded | 1,121 | **7 of 13** | **172** |
| V3 technical | 1,121 | 7 of 13 | 171 |

**Why it changed.** The control's oversized chunk was accidentally *helping*: because it
concatenated the entire HTTP-error list, it contained almost every query term at once, and
BM25 rewards that co-occurrence. Splitting it to 1,121 characters cut term coverage nearly
in half — `status`, `code`, `does`, `return`, `type` all fell into neighbouring chunks —
and the rank collapsed by 145 positions.

This is the fragmentation cost, and it is the direct counterweight to the hypothesis.
Making chunks smaller does not only concentrate the answer; it also strips the
co-occurring context that a bag-of-words retriever scores on. AN-007 (18 → 41) and AN-011
(54 → 139) fail the same way. No case regressed *below the k=10 line* only because these
three were already failing there.

---

## 10. Persistent failure — AN-003, the case that motivated the hypothesis

**Query:** "How many requests can a single Message Batches create request contain at most?"
**Expected evidence:** the 57-character sentence *"There is a limit of 100,000 messages in
a single request."*

| Config | containing chunk | evidence share | rank (probe depth 300) |
|---|---:|---:|---:|
| control | 3,449 chars | 1.65% | **not retrieved** |
| V2 bounded | 1,191 chars | 4.79% | **not retrieved** |
| V3 technical | 1,188 chars | 4.80% | **not retrieved** |

Granularity improved by **2.9×** on exactly the quantity FAIL-0002 named, and the outcome
did not change at all.

**Why.** Term-by-term, against the V2 chunk that carries the evidence:

| Query term | corpus df | present in the chunk? |
|---|---:|---|
| `contain` | 111 | **no** |
| `Batches` | 286 | **no** |
| `most` | 516 | **no** |
| `many` | 561 | **no** |
| `requests` | 1,218 | **no** (only the singular `request` appears) |
| `single`, `Message`, `create`, `request`, `can`, `at` | 689–3,860 | yes |

Every discriminative, low-df term in the question is **absent** from the chunk that holds
the answer. The terms that do match are the common ones. No chunking strategy can fix
this, because the failure is vocabulary mismatch between question and evidence — including
a plural/singular mismatch that the deliberately unstemmed `simple` text-search
configuration cannot bridge.

**Next experiment if this remains unsolved:** this is precisely the failure a pretrained
semantic embedding model exists to solve. It is *not* an argument for a reranker — a
reranker only reorders what retrieval already found, and this chunk is absent from the top
300.

---

## 11. Was the hypothesis supported?

**Question A — did span recall move materially toward the 0.818 document ceiling?**
Partially, and not by the mechanism under test. V2 (granularity alone): 0.475 → 0.500,
entirely one half-case. V3 (granularity + enrichment): 0.650. Attributing V3's gain to
granularity is not supportable when V2 isolates granularity and shows nothing.

**Question B — did document recall remain stable?** For V2 yes (0.825, unchanged), which
is the control the design wanted. For V3 no: 0.825 → 0.900, because context headers add
section-path terms to the index. V3 is therefore not a pure chunking intervention.

**Question C — did previously oversized answer-containing units become retrievable?**
**No.** Zero spans moved from unreachable to reachable in either configuration. AN-003 —
the specific 1.7%-of-chunk case that motivated EXP-005 — remains unretrieved at depth 300
despite a 2.9× improvement in evidence share.

**Question D — did smaller chunks introduce regressions through fragmentation?** **Yes,
substantially.** Under V2, 9 of 22 spans ranked *worse* against 8 better. AN-002 fell 145
places when query-term coverage in its chunk dropped from 12/13 to 7/13.

**Question E — does V3 outperform V2 enough to justify its complexity?** Yes on the
numbers: +3 rescued cases, 0 regressed, +0.150 macro recall, at the cost of ~200 lines and
a context-prefix contract. But the justification is for *contextual enrichment*, which V3
happens to bundle, not for its parameter-entry logic — only 60 parameter-entry chunks were
produced across 202 documents, and no rescued case depended on one.

**Overall: the chunk-granularity hypothesis as stated is rejected.** Chunk size was the
diagnosed cause; the intervention that changes chunk size and nothing else changes nothing.

---

## 12. Limitations

1. **V2 is not a single-variable ablation.** It changes both the grouping target
   (3,500 → 1,200) and hard-limit enforcement. Both were chosen from corpus block-size
   percentiles, never from the golden set. Since V2's result is null, the confound does not
   rescue the hypothesis — but a stricter design would vary one at a time.
2. **V3 confounds granularity with enrichment,** as stated above. Separating them is the
   obvious follow-up: run V2 with context headers and nothing else.
3. **n = 20 is development scale.** Nothing here is statistically significant. Two of the
   three V3 rescues turned on rank movements of 1–3 positions across the k boundary.
   Paired per-case movement is reported precisely because the averages cannot carry weight.
4. **EXP-NULL still has not run.** No generation credential and the provider host is
   egress-blocked, so retrieval lift over the model's own prior knowledge remains unknown.
   EXP-005 does not address this.
5. **Dense retrieval remains unmeasured in any real sense.** EXP-001/002/003 used an
   offline TF-IDF+SVD substitute. Nothing here supports "BM25 beats dense retrieval" — only
   "BM25 outperformed the available offline LSA substitute on this corpus and evaluation."
   EXP-005 is BM25-only and does not revisit it.
6. **Corpus skew persists:** 139 Anthropic documents to 63 OpenAI.
7. **The `simple` text-search configuration does not stem.** This protects identifiers and
   is deliberate, but AN-003 shows it also costs plural/singular matches. That trade-off is
   now measured rather than assumed.
8. **The EXP-003 pool=100 RRF result remains eval-set-tuned** and is not a held-out number.

---

## 13. What the data justifies building next

Per the decision gate:

**Span recall barely changed under the isolated intervention, so the chunking hypothesis is
weakened.** The gate says: investigate whether ranking inside correct documents is the
actual issue, and only then is a second-stage retriever justified.

The evidence says the bottleneck is **lexical matching**, not chunk size:

1. **A real pretrained embedding model — highest value.** AN-003 fails on pure vocabulary
   mismatch (`contain`, `Batches`, `requests` absent from the evidence chunk). This is the
   canonical case for semantic retrieval, and the current LSA substitute cannot answer it.
   Blocked only on network egress.
2. **Separate enrichment from granularity.** Run V2 + context headers alone. If it
   reproduces most of V3's +3, adopt enrichment and drop V3's parameter-entry machinery.
3. **Revisit the unstemmed `simple` configuration** as a third ranked list rather than a
   replacement, so identifier precision is kept while plural/singular matching is recovered.

**Not justified by this data:** a reranker (cannot rescue evidence absent from the top
300), a larger `k` (inflates the metric without improving retrieval), or a confidence
threshold (no calibration failure was observed).

**Baseline decision.** V3 is the better chunker on measured recall with no case
regressions, but it is not frozen as the new baseline, because its gain is attributable to
a mechanism the experiment did not isolate. `chunker_v1_control` remains the published
baseline for EXP-000…EXP-003, all three chunk sets remain queryable side by side, and the
enrichment ablation in (2) should decide the baseline rather than this result.
