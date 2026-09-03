# Production RAG — EXP-006 Contextual Enrichment Ablation

## 1. Executive result

**Contextual enrichment did not improve retrieval.** On the control chunking, adding a
structural header to the indexed text moved macro span recall by **exactly zero**
(0.475 → 0.475): it rescued one question and regressed another. V3's apparent +3 in
EXP-005 is therefore **not** reproducibly explained by section enrichment alone.

The measured reason is specific and was not anticipated: enrichment **inflates document
frequency**. Writing `Provider: anthropic` into all 12,028 Anthropic chunks took the term
"Anthropic" from df 3,289 to df 12,028, destroying its IDF. Across all 22 evidence spans,
enrichment supplied a query term to only **3**, and in **none** of those was it a
discriminative one.

Per the pre-registered decision criteria this is **Case 2**: do not freeze enrichment; the
next priority is the pretrained embedding experiment.

Artifacts: `experiments/EXP-006/results.json` (source of truth),
`experiments/EXP-006/evidence-mapping.json`.

---

## 2. Why EXP-006 was run

EXP-005 rejected the chunk-granularity hypothesis but left one variable confounded. Its V3
chunker changed boundaries *and* prepended structural context to the indexed text, and its
document recall rose to 0.900 when a pure chunking change should have left it flat. The
gain could not be attributed. EXP-006 decomposes it.

## 3. The EXP-005 finding being tested

Bounding chunk size cut the corpus maximum from 16,096 characters to 1,999 and eliminated
all 3,069 chunks over 2,000, yet rescued **zero** questions: 8 span ranks improved, 9
worsened, and no previously unreachable span became reachable. EXP-006 asks whether the
other half of V3 — the context header — is what actually helped.

## 4. Experimental controls

Held constant: the same 202 document versions, the same 20 scored questions and 22 evidence
spans, the same anchors `(version_id, section_path, char_start, char_end)`, the same BM25
implementation and parameters (`k1=1.2`, `b=0.75`, `simple` configuration), the same
`top_k=10`, the same tie-breaking, the same scoring code. No reranker, no query rewriting,
no query expansion, no synonyms, no dense retrieval, no RRF, no BM25 sweep.

**Enrichment is applied to the index only.** A migration (`sql/003_search_text.sql`)
separates the columns:

| column | meaning |
|---|---|
| `chunk.text` | canonical source body — never enriched, this is what a citation quotes |
| `chunk.context_header` | the structural header, or NULL |
| `chunk.search_text` | what is indexed; NULL means "index `text` verbatim" |

`search_vector` falls back through `coalesce(search_text, text)`, so every pre-existing row
keeps a byte-identical tsvector. BM25 document length now measures the indexed text, which
is identical to the old behaviour wherever `search_text` is NULL.

**Baseline reproducibility, verified before any code changed.** EXP-006A reproduces EXP-000
(0.475, 9/20) and EXP-006C reproduces EXP-005A (0.500, 9/20) with identical per-case recall
and identical hit ordering. Repeated runs are byte-identical. The only residual difference
against the committed EXP-000 artifact is last-bit float noise in the serialized `score`
field (~1e-14); recall and ordering are unaffected, and the older artifacts were left
untouched rather than regenerated.

**Query plan verified.** `EXPLAIN ANALYZE` confirms `idx_chunk_search_vector` is still used
(4 bitmap index scans); the one sequential scan is the corpus-average CTE, which has no
index to use. The EXP-005 planner regression has not returned.

**Evidence mapping validated.** All four configurations pass 22/22 spans with 0 offset
mismatches. A and B report identical evidence-share (0.133), as do C and D (0.154), which
is itself proof the boundaries are unchanged.

---

## 5. The 2×2

| | no enrichment | + structural enrichment |
|---|---|---|
| **control chunking** | **A** — `cs_v1_control` | **B** — boundaries copied from A |
| **bounded chunking** | **C** — `chunker_v2_bounded` | **D** — boundaries copied from C |

B and D are row-for-row copies of A and C: **0** boundary differences and **0** body
differences, verified in SQL and pinned by tests. Only `search_text` differs. A difference
between A and B therefore cannot be a chunking difference.

The header uses source-native fields only — nothing summarised or generated:

```
Provider: anthropic
Document: Message Batches
Section: Batches > Create a Message Batch > Body Parameters
<canonical chunk body>
```

Mean header length 101 characters; 5,923 distinct headers across 14,209 chunks.

---

## 6. Aggregate metrics

| config | macro recall | fully recalled | spans @10 | doc recall | MRR | absent@10 | @50 | @100 | @300 | mean query ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **A** control, plain | 0.475 | 9/20 | 10/22 | 0.825 | 0.280 | 12 | 3 | 2 | 1 | 418 |
| **B** control, enriched | 0.475 | 9/20 | 10/22 | 0.875 | 0.282 | 12 | 3 | 2 | 1 | 513 |
| **C** bounded, plain | 0.500 | 9/20 | 11/22 | 0.825 | 0.287 | 11 | 5 | 4 | 1 | 446 |
| **D** bounded, enriched | 0.550 | 10/20 | 12/22 | 0.850 | 0.279 | 10 | 3 | 2 | **0** | 586 |

MRR is flat across all four (0.279–0.287). Enrichment costs roughly 20–30% query latency
for the longer indexed text.

---

## 7. Paired comparisons

| comparison | Δ macro | rescued | regressed | net | span movements |
|---|---:|---|---|---:|---|
| **A → B** enrichment, control chunking | **+0.000** | AN-004 | AN-005 | **0** | 7 improved, 5 worsened, 7 unchanged, 1 boundary rescue, 1 strong regression |
| **A → C** chunk size, no enrichment | +0.025 | — | — | 0 | 7 improved, 9 worsened, 1 strong rescue |
| **C → D** enrichment, bounded chunking | +0.050 | AN-004, AN-007 | AN-005 | **+1** | 6 improved, 7 worsened, 2 strong rescues, 1 strong regression |
| **B → D** chunk size, with enrichment | +0.075 | AN-007 | — | +1 | 6 improved, 10 worsened, 1 strong rescue, 1 boundary rescue |

**A → B is the headline and it is a wash.** One rescue, one regression, zero net change in
macro recall.

---

## 8. AN-003 deep dive

**Query:** "How many requests can a single Message Batches create request contain at most?"
**Evidence:** *"There is a limit of 100,000 messages in a single request."*

| config | rank | in top 300? | chunk chars | search_text chars | doc rank |
|---|---:|---|---:|---:|---:|
| A control, plain | — | **no** | — | — | 6 |
| B control, enriched | — | **no** | — | — | 9 |
| C bounded, plain | — | **no** | — | — | 4 |
| **D** bounded, enriched | **74** | **yes** | 1,191 | 1,289 | 12 |

**Enrichment did build a lexical bridge — but not nearly enough.** For the first time
across every experiment, AN-003's evidence becomes reachable at all: rank 74 under D. The
header supplied one query term the body lacked:

```
Provider: anthropic
Document: Batches
Section: Batches > Create a Message Batch > Body Parameters
```

`Batches` was absent from the body and is present in the header. But it is not a
discriminative term — and enrichment itself made it less so, taking its df from 283 to
1,203 by writing the document title into every chunk of that document.

The terms that would actually identify this evidence remain absent everywhere:

| query term | df | present anywhere in the chunk? |
|---|---:|---|
| `contain` | 111 | **no** |
| `most` | 533 | **no** |
| `many` | 564 | **no** |
| `requests` | 1,320 | **no** — only the singular `request` appears |
| `single`, `Message`, `create`, `request`, `can`, `at` | 711–3,967 | yes |

**Answer to the question posed: no.** Section-path enrichment does not create enough of a
lexical bridge to make AN-003 retrievable. It moved from unreachable to rank 74, which is
still a failure at k=10 and would remain one at k=50. AN-003 is a vocabulary-mismatch
failure and remains the canonical test case for the pretrained-embedding experiment.

---

## 9. Vocabulary-overlap analysis — why enrichment nets to zero

Two measurements explain the entire result.

**Enrichment almost never supplies a query term.** Across all 22 evidence spans, the header
contributed a query term to **3** of them (OA-002, OA-003, OA-006 — all the term `OpenAI`),
and in **0** cases was the contributed term one of the four most discriminative terms of
its query.

**Enrichment destroys the IDF of the terms it adds.** A constant field repeated across every
chunk of a document or provider is, by construction, non-discriminative:

| term | df in A | df in B | change |
|---|---:|---:|---|
| `Anthropic` | 3,289 | 12,028 | **+266%** |
| `OpenAI` | 366 | 2,185 | **+497%** |
| `beta` | 1,405 | 2,933 | +109% |
| `editing` | 66 | 211 | +220% |
| `API` | 3,347 | 4,629 | +38% |

98 distinct query terms shifted document frequency. BM25 weights a term by
`ln(1 + (N−df+0.5)/(df+0.5))`, so tripling a term's df is a direct attack on the signal that
made it useful. Enrichment adds a handful of weak matches while diluting terms that were
already working.

---

## 10. Strong rescues

**AN-007 (C → D): rank 34 → 6, BM25 +4.20.** Section `HTTP errors`. A genuine, large
movement — 28 positions, landing well inside k. This is the most convincing single result in
EXP-006, and it appears only in combination with bounded chunking.

**AN-004 (C → D): rank 11 → 3, BM25 +6.55.** Section
`Explicit cache breakpoints > Structuring your prompt > How automatic prefix checking works`
— a genuinely technical, specific path. Strong under bounded chunking.

## 11. Fragile rescues

**AN-004 (A → B): rank 12 → 7 — boundary rescue, and its BM25 score went *down*
(17.57 → 17.39).** It crossed the k=10 line by five places while scoring slightly worse in
absolute terms; competitors simply lost more. This is exactly the kind of movement EXP-005
flagged and should not be described as a success. It is the *only* rescue in the A → B
comparison, which is the comparison that isolates enrichment.

## 12. Regressions

**AN-005 (A → B): rank 4 → 18. Strong regression, BM25 −2.08.** It regresses again under
D (3 → 13, −2.18). The mechanism is measured, not guessed: the query is "Which
`anthropic-beta` header value enables context editing?" and its most discriminative term
`editing` had df 66 in A. Writing `Section: … Context editing` into every chunk of that
document tripled it to 211. The evidence chunk's IDF advantage on its single best term
collapsed, and it fell 14 places.

This is the cost side of enrichment, and it is systematic rather than incidental: the more
distinctive a document's title or section heading, the more damage repeating it across every
one of that document's chunks does to that term's discriminative power.

Overall span movement under A → B: 7 improved, 5 worsened, 7 unchanged, 1 absent throughout.

---

## 13. Query-plan and reproducibility validation

* `idx_chunk_search_vector` is used in all four configurations — 4 bitmap index scans per
  query. The single `Seq Scan on chunk` is the corpus-average CTE.
* Mean query time 418–586 ms; enrichment costs 20–30%.
* Repeated identical runs produce byte-identical output; pinned by
  `test_retrieval_ordering_is_deterministic`.
* Score rounding before sorting is retained, so BM25 ties resolve on `chunk_id`.
* EXP-000 through EXP-005 artifacts are untouched.

---

## 14. Was contextual enrichment the real source of V3's gain?

**No — not on its own, and not reproducibly.**

V3 rescued AN-004, AN-008 and AN-010 in EXP-005. EXP-006 shows:

* Enrichment alone (A → B) rescues **AN-004 only**, by a fragile five-place boundary
  crossing with a *lower* BM25 score — and simultaneously loses AN-005.
* Enrichment on bounded chunking (C → D) rescues AN-004 and AN-007. It does **not** rescue
  AN-008 or AN-010.

AN-010 was V3's largest win (rank 49 → 1) and no EXP-006 configuration reproduces it. That
rescue must have come from V3's table row-group splitting — emitting a 415-character row
group carrying its own column headers — rather than from the section-path header. V3's gain
decomposes into a *table-structure* effect that EXP-006 did not test, plus an enrichment
effect that is a wash.

---

## 15. Updated root-cause hypothesis

Two hypotheses have now been tested and neither survives as the dominant explanation:

1. **Oversized chunks hide evidence** — falsified by EXP-005 (0 rescued).
2. **Missing structural lexical context** — falsified by EXP-006 A → B (net 0, Δ0.000).

The surviving hypothesis is the one AN-003 has pointed at from the beginning:
**BM25 cannot bridge the vocabulary gap between how a question is phrased and how the
documentation states the answer.** The evidence:

* AN-003's discriminative terms (`contain`, `most`, `many`) appear nowhere in the chunk that
  answers it, at any chunk size, with or without enrichment.
* `requests` never matches `request` — the `simple` configuration does not stem, a
  deliberate choice that protects identifiers and costs plural/singular matching.
* Enrichment can only add terms that already exist in the document's structure. It cannot
  add the words a user actually used.

The distinction EXP-006 was built to make — *structural lexical context missing* versus
*BM25 fundamentally cannot bridge the semantic gap* — resolves to the second.

---

## 16. Limitations

1. **n = 20 is development scale.** One case is 5 points of macro recall. Every result here
   is a 1–2 case movement. Nothing is statistically significant; the paired per-case tables
   are the trustworthy part.
2. **The exploratory field ablation was selected on the development set** and is not a
   held-out result. See section 17.
3. **EXP-006 does not test V3's table row-group mechanism**, which is now the leading
   explanation for V3's AN-010 rescue. That remains unattributed.
4. **EXP-NULL still has not run** — no generation credential and the provider host is
   egress-blocked, so retrieval lift over the model's own knowledge is still unknown.
5. **Dense retrieval has not been disproven.** The earlier dense numbers used an offline
   TF-IDF + SVD substitute, not a pretrained semantic embedding model. Nothing in this
   repository supports "BM25 beats dense retrieval".
6. **Corpus skew persists:** 139 Anthropic documents to 63 OpenAI.
7. **Section paths are mostly meaningful** — 19 of 22 evidence spans sit under technical
   paths such as `Explicit cache breakpoints > Structuring your prompt > How automatic
   prefix checking works`. The 3 generic ones are all `Preamble`, the parser's label for
   front matter. So the null result is *not* explained by useless headings; the headings are
   good and enrichment still did not help.

---

## 17. Exploratory: which header fields matter

Run after the core 2×2 completed, motivated by the df-inflation mechanism above. **Selected
on the development set — not a held-out result.** Control chunking throughout.

| variant | header fields | macro recall | fully recalled | `Anthropic` df | `editing` df |
|---|---|---:|---:|---:|---:|
| A | none | 0.475 | 9/20 | 3,289 | 66 |
| **E1** | section path only | **0.525** | **10/20** | 3,298 | 70 |
| E2 | document + section | 0.475 | 9/20 | 3,298 | 211 |
| B | provider + document + section | 0.475 | 9/20 | 12,028 | 211 |

The ordering matches the mechanism exactly: the more constant the field, the more df
inflation and the worse the result. `Provider:` is pure noise — one of two values across the
whole corpus — and `Document:` repeats a title across every chunk of its document. Only the
section path, which actually varies chunk to chunk, carries information.

E1 is the only variant that improves on the baseline, by **one case**. That is a
development-set observation of a single-question movement, and it does not license adopting
enrichment.

---

## 18. What experiment is justified next

**Real pretrained dense retrieval.** Both lexical hypotheses have now been tested and
rejected with controlled interventions. The remaining diagnosis — vocabulary mismatch —
is precisely what a pretrained semantic embedding model addresses, and AN-003 is its
canonical test case: an answer whose discriminative query terms appear nowhere in the text
that answers it. Blocked only on network egress to a model host.

**Secondary, cheap, and justified by this data:**

* **Test V3's table row-group mechanism in isolation.** It is the only unexplained rescue
  left (AN-010, rank 49 → 1) and EXP-006 did not cover it.
* **Add stemming as a third ranked list**, not as a replacement. `requests` failing to match
  `request` is now a measured cost of the `simple` configuration rather than a theoretical
  one; keeping the unstemmed list preserves identifier precision.

**Still not justified:**

* **A reranker.** AN-003 does not appear within probe depth 300 in three of four
  configurations, and at rank 74 in the fourth. A reranker reorders candidates; it cannot
  retrieve evidence that retrieval never found.
* **Freezing enrichment.** A → B is Δ0.000 with one fragile rescue and one strong
  regression. Complexity has to earn its place, and this did not.

**Baseline decision: unchanged.** `chunker_v1_control` with no enrichment remains the
published baseline.
