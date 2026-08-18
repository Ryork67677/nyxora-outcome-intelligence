# Production RAG + Evaluation Harness — V1

A deliberately small, measurable RAG baseline for technical documentation. V1 is designed to answer one question before adding complexity:

> **Does retrieval add measurable value over what the generation model already knows, and which retrieval method actually helps?**

## Why V1 is intentionally small

The project begins with a closed-book control and four retrieval experiments. Reranking, agentic retry, live crawling, dynamic confidence thresholds, dashboards, and framework orchestration are intentionally deferred until measurements justify them.

**[Jump to measured results](#results).** They include a baseline that scored 0.000, a dense retriever that lost to lexical on 5 of 20 questions, and an RRF configuration that regressed a question lexical answered correctly.

## Architecture

```text
local versioned docs
        ↓
structure-aware parser
        ↓
stable evidence spans
        ↓
PostgreSQL + pgvector
   ↙             ↘
lexical           dense
   ↘             ↙
  hybrid / RRF
        ↓
retrieval eval
```

Evaluation ground truth is anchored to:

```text
(version_id, section_path, char_start, char_end)
```

—not chunk IDs—so future chunking experiments do not invalidate the benchmark.

## Experiments

| Experiment | Purpose |
|---|---|
| EXP-NULL | Closed-book generation, zero retrieval |
| EXP-000 | PostgreSQL lexical baseline |
| EXP-001 | Dense retrieval baseline |
| EXP-002 | Simple lexical+dense interleave |
| EXP-003 | Pure Reciprocal Rank Fusion |
| EXP-003B | Optional exact-identifier third-list RRF hypothesis |

## Quick start

```bash
cp .env.example .env
docker compose up -d
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e '.[dev,openai,local-embeddings]'
pytest -q
```

Ingest the included synthetic fixture:

```bash
ragv1 ingest data/manifests/sources.example.yaml
ragv1 snapshot-create v1-seed
```

For the real project, replace the synthetic manifest with local snapshots of the focused OpenAI + Anthropic corpus. **Do not commit copied provider documentation to a public repository.** Verify provider terms and robots rules before automated fetching.

### Building the real corpus

```bash
python scripts/fetch_corpus.py            # writes data/raw/ (gitignored) + the manifest
ragv1 ingest data/manifests/v1-openai-anthropic.yaml
ragv1 snapshot-create v1-openai-anthropic
```

`scripts/fetch_corpus.py` fetches 202 documents and is the only thing in this repository that talks to a provider. What it does about compliance, so the claim is auditable rather than asserted:

- Parses and enforces `robots.txt` per host with `urllib.robotparser` **before** any document request, using a descriptive User-Agent and a 0.7 s delay between requests. Every decision is recorded to `data/manifests/fetch-compliance.json`.
- Anthropic documentation comes from `platform.claude.com` over HTTPS. Its `robots.txt` disallows only `/api/`; the documentation lives under `/docs/en/`, which is allowed.
- OpenAI documentation comes from OpenAI's own public repositories (`openai-agents-python` MIT, `openai-python` and `openai-node` Apache-2.0, `openai-cookbook` MIT), cloned and **pinned to an exact commit** so a version is reproducible and cannot silently mutate.
- Raw documents land in `data/raw/` and are gitignored. The repository keeps the manifest, the compliance record, hashes and the fetch logic — not the documents.

The manifest preserves provider, canonical URL, captured time, authority class and raw path for every document, which is what `ragv1 ingest` reads.

## Golden-set workflow

Start with ~20 manually verified cases. A case should point to source evidence above the chunk layer:

```json
{
  "case_id": "OA-001",
  "category": "exact_lookup",
  "question": "...",
  "expected_claims": [
    {"text": "expected value", "match_type": "contains", "critical": true}
  ],
  "expected_evidence": [
    {
      "version_id": "ver_...",
      "section_path": ["Responses API", "Parameters"],
      "char_start": 1200,
      "char_end": 1320
    }
  ],
  "expected_abstain": false
}
```

Validate:

```bash
ragv1 validate-golden evals/golden/v1.jsonl
```

### How the shipped golden set was authored

Questions, expected claims and target documents in `scripts/build_golden.py` were chosen by reading the ingested source documents. The script automates only the error-prone half — turning a human-verified literal quotation into the anchor the evaluator scores against:

```bash
python scripts/evidence_lookup.py "There is a limit of 100,000 messages" --snapshot SNAPSHOT_ID
python scripts/build_golden.py --snapshot SNAPSHOT_ID --out evals/golden/v1.jsonl
```

That split is what keeps the benchmark valid. Anchors are never hand-typed, so a case cannot silently point at the wrong span; a locator matching zero or several chunks **aborts the build**, so a case cannot quietly become ambiguous after a re-ingest; and every anchor is re-read from the database and checked to still contain its quotation. `evals/golden/v1.anchors.json` records the audit trail — canonical URL, section path, chunk type and materialized anchor text for all 22 spans.

The shipped set is 22 cases: 20 with expected evidence (retrieval-scored) plus 2 abstain-only `missing_info` controls, which the retrieval evaluator skips by design and which exist to catch confident fabrication in EXP-NULL. Categories: 13 `exact_lookup`, 2 `multi_hop`, 2 `version_conflict`, 2 `normal`, 1 `ambiguous`, 2 `missing_info`.

## EXP-NULL

Requires `OPENAI_API_KEY`. The V1 adapter uses the OpenAI Responses API and reads generated text from `response.output_text`.

```bash
ragv1 eval-null evals/golden/v1.jsonl experiments/EXP-NULL/results.json
```

Any question the model already answers correctly with zero retrieval is important context when interpreting later RAG accuracy.

If no generation provider is reachable, the run records `status: "blocked"` with the provider error and per-case `status: "not_run"` rather than raising or emitting placeholder accuracies. **This control did not run in the published results** — see [Limitations](#limitations--read-before-quoting-any-number-above).

## EXP-000 — lexical

```bash
ragv1 eval-retrieval \
  evals/golden/v1.jsonl SNAPSHOT_ID lexical \
  experiments/EXP-000/results.json --k 10
```

The lexical baseline uses a generated `TSVECTOR` with a GIN index under the `simple` configuration. The `simple` config is deliberate because technical identifiers can be damaged by natural-language stemming.

Scoring is BM25 over that index. The originally shipped `websearch_to_tsquery` ANDs every token and retrieved **nothing at all** on this corpus; each query term is now OR-ed as a `phraseto_tsquery` — which keeps `request_too_large` matching as an adjacent phrase — and weighted by inverse document frequency. See [FAIL-0001](docs/failure-reports/FAIL-0001.md). This is not a scalar identifier boost: no rule mentions identifiers, they simply tend to be the rarest terms in a query.

## EXP-001 — dense

Default local embedding model is configurable. Embeddings live in a separate versioned table and are cached by chunk/model identity.

Three providers are available via `EMBEDDING_PROVIDER`: `local` (sentence-transformers), `openai`, and `local-lsa` — an offline TF-IDF+SVD embedder fitted on the corpus snapshot itself, for environments where neither model host is reachable. `local-lsa` additionally requires `LSA_FIT_SNAPSHOT_ID` so query and chunk vectors come from the same fitted model; the fit corpus is hashed into the model version, so vectors from different fits cannot be mixed. It is a substitute with no pretrained semantic knowledge — see `src/rag_v1/embedders_lsa.py` and the limitations section.

```bash
ragv1 embed SNAPSHOT_ID
ragv1 eval-retrieval \
  evals/golden/v1.jsonl SNAPSHOT_ID dense \
  experiments/EXP-001/results.json \
  --k 10 --model-id EMBEDDING_MODEL_ID
```

## EXP-002 — hybrid interleave

```bash
ragv1 eval-retrieval \
  evals/golden/v1.jsonl SNAPSHOT_ID hybrid \
  experiments/EXP-002/results.json \
  --k 10 --model-id EMBEDDING_MODEL_ID
```

Interleave is intentionally unsophisticated. It provides a transparent hybrid checkpoint before RRF.

## EXP-003 — RRF

Do not assume `rrf_k=60` is optimal. Test it.

```bash
for RRF_K in 10 20 60; do
  ragv1 eval-retrieval \
    evals/golden/v1.jsonl SNAPSHOT_ID rrf \
    experiments/EXP-003/results-k${RRF_K}.json \
    --k 10 --model-id EMBEDDING_MODEL_ID --rrf-k ${RRF_K}
done
```

Also inspect candidate-size curves at K = 10/20/50/100 before freezing a candidate-pool decision:

```bash
for POOL in 10 20 50 100; do for RRF_K in 10 20 60; do
  ragv1 eval-retrieval evals/golden/v1.jsonl SNAPSHOT_ID rrf \
    experiments/EXP-003/sweep/pool${POOL}-rrfk${RRF_K}.json \
    --k 10 --model-id EMBEDDING_MODEL_ID --rrf-k ${RRF_K} \
    --lexical-k ${POOL} --dense-k ${POOL}
done; done
```

That advice paid off here: `rrf_k` made no difference at all until the candidate pool reached 50, and the shipped default pool of 30 would have hidden the best configuration. See [Results](#results).

## Paired comparisons

Small evaluation sets should be analyzed per question rather than by headline averages alone:

```bash
ragv1 compare experiments/EXP-001/results.json experiments/EXP-002/results.json
```

Output includes:

- previously wrong → now correct (`rescued`)
- previously correct → now wrong (`regressed`)
- unchanged-good
- unchanged-bad

`scripts/analyze_experiments.py` runs every pairing at once and adds two things a headline average cannot show: `cases_fully_recalled` (strict — every expected span retrieved, so a partially-answered multi-hop case gets no credit) and document-level recall (was the correct *document* in the top k even though the wrong chunk came back?). That second number is what separates "retrieval went to the wrong place" from "retrieval went to the right document and picked the wrong chunk" — two different bugs with two different fixes.

```bash
python scripts/analyze_experiments.py --out experiments/summary.json
```

## Results

Every number below was produced by `scripts/run_v1_baselines.sh` against one immutable snapshot and one unchanged golden set. Regenerate the table with `python scripts/analyze_experiments.py`; the machine-readable form is `experiments/summary.json`.

### Run identity

| | |
|---|---|
| Corpus snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| Corpus | 202 documents / 14,209 chunks — Anthropic 139 docs (12,028 chunks), OpenAI 63 docs (2,181 chunks) |
| Manifest | `data/manifests/v1-openai-anthropic.yaml`, captured 2026-08-17 |
| Golden set | `evals/golden/v1.jsonl` — 22 cases: 20 retrieval-scored + 2 abstain-only controls, 22 evidence spans |
| Parser / chunking | `markdown v1.0`, `MAX_CHUNK_CHARS=3500`, `MIN_CHUNK_CHARS=200` |
| Embedding model | `emb_205f51a2d4db0273e121527cb5c6ff83` — offline TF-IDF+SVD, 384 dims, 57.2% explained variance |
| Retrieval k | 10 for every experiment |

### Headline

`macro recall` averages per-case span recall, so a 2-span multi-hop case that finds 1 span scores 0.5. `cases fully recalled` is the strict count — every expected span retrieved. `doc recall` credits a span when the correct *document* was in the top 10 even if the wrong chunk came back.

| Experiment | macro recall | cases fully recalled | spans found | doc recall |
|---|---:|---:|---:|---:|
| EXP-NULL closed-book | **not run** | — | — | — |
| EXP-000 lexical — *as shipped* | 0.000 | 0/20 | 0/22 | 0.000 |
| EXP-000 lexical — BM25 (fixed) | 0.475 | 9/20 | 10/22 | 0.818 |
| EXP-001 dense (LSA) | 0.300 | 5/20 | 7/22 | 0.773 |
| EXP-002 hybrid interleave | 0.450 | 8/20 | 10/22 | 0.818 |
| EXP-003 RRF `rrf_k=10` | 0.500 | 9/20 | 11/22 | 0.818 |
| EXP-003 RRF `rrf_k=20` | 0.500 | 9/20 | 11/22 | 0.818 |
| EXP-003 RRF `rrf_k=60` | 0.500 | 9/20 | 11/22 | 0.818 |
| EXP-003 RRF `rrf_k=60`, pool 100 | **0.600** | **11/20** | 13/22 | 0.818 |

### Paired per-case comparisons

Averages on 20 cases hide everything that matters. These are the questions that actually moved.

| From → To | rescued | regressed | net | which |
|---|---:|---:|---:|---|
| lexical → dense | 1 | 5 | **−4** | +AN-011 / −AN-005, OA-001, OA-002, OA-003, OA-004 |
| lexical → hybrid interleave | 0 | 1 | **−1** | — / −OA-003 |
| dense → hybrid interleave | 4 | 1 | +3 | +AN-005, OA-001, OA-002, OA-004 / −AN-011 |
| hybrid → RRF `rrf_k=60` | 2 | 1 | +1 | +AN-004, OA-003 / −OA-004 |
| lexical → RRF `rrf_k=60` | 1 | 1 | **0** | +AN-004 / −OA-004 |
| lexical → RRF `rrf_k=60` pool 100 | 3 | 1 | +2 | +AN-004, AN-006, AN-008 / −OA-004 |

### The uncomfortable findings

**The shipped lexical baseline retrieved nothing.** `websearch_to_tsquery` ANDs every token, so a 16-word question required all 16 tokens in one chunk. Zero hits on all 20 cases — `macro_recall = 0.000`. Diagnosis and fix in [FAIL-0001](docs/failure-reports/FAIL-0001.md); the failing run is preserved at `experiments/EXP-000/results-websearch-and.json`.

**Lexical beats dense, and it is not close.** BM25 0.475 vs LSA 0.300. Switching from lexical to dense regressed 5 of 20 questions and rescued 1. Read this with the caveat below — the dense retriever is a substitute, not a real embedding model.

**Hybrid interleave is worse than lexical alone.** 0.450 vs 0.475, net −1 case. Naively alternating between a strong and a weak ranked list dilutes the strong one. Interleave was included as a transparent checkpoint before RRF, and it earned its place by failing.

**RRF's headline gain over lexical is partial credit, not a real win.** RRF `rrf_k=60` at the default pool posts 0.500 vs lexical 0.475, but per-case it is 1 rescued / 1 regressed — a wash. The entire macro-recall difference is one extra span on a two-span multi-hop case. Only at pool 100 does RRF become a genuine +2.

**RRF actively regressed a question lexical got right.** OA-004's evidence sits at lexical rank 5 and dense rank 61. Fusion averaged the two into rank 13 — outside k=10. Fusing a strong list with a weak one costs real answers.

**`rrf_k` barely matters; candidate pool size does.** At pool 10–30, all three `rrf_k` values give identical results. `rrf_k` only separates at pool ≥ 50. The full grid is in `experiments/EXP-003/sweep/`:

| pool \ `rrf_k` | 10 | 20 | 60 |
|---|---:|---:|---:|
| 10 | 0.450 | 0.450 | 0.450 |
| 20 | 0.500 | 0.500 | 0.500 |
| 50 | 0.500 | 0.550 | **0.600** |
| 100 | 0.450 | 0.550 | **0.600** |

The common advice to default to `rrf_k=60` happens to hold here, but only once the candidate pool is large enough for it to mean anything. Freezing the pool at the shipped default of 30 would have hidden the best configuration entirely.

**Every configuration is stuck at the same ceiling.** Document-level recall is 0.818 for lexical, interleave and RRF alike, against span recall of 0.455–0.500. Of the 12 spans lexical missed, 8 had the correct document in the top 10. Fusion is reordering chunks inside an already-correct document set, not finding new documents. That is a chunking failure, diagnosed in [FAIL-0002](docs/failure-reports/FAIL-0002.md) and deliberately left unfixed in V1.

**Ambiguous questions fail across the board.** AN-011 ("What is my rate limit?") is recalled by dense (1.00) and missed by lexical, interleave and RRF (0.00). One case is not a finding, but it is the only category where dense wins outright.

### EXP-005 — re-chunking (the hypothesis above, tested)

FAIL-0002 concluded that chunk granularity was the ceiling and predicted that re-chunking
would move span recall toward document recall. That was measured. Full write-up:
**[EXP-005-rechunking.md](docs/reports/EXP-005-rechunking.md)**.

| Configuration | macro span recall | fully recalled | doc recall | rescued / regressed vs control |
|---|---:|---:|---:|---|
| EXP-000 control (`chunker_v1_control`) | 0.475 | 9/20 | 0.825 | — |
| EXP-005A bounded (`chunker_v2_bounded`) | 0.500 | 9/20 | 0.825 | **0 / 0** |
| EXP-005B technical (`chunker_v3_technical`) | 0.650 | 12/20 | 0.900 | **3 / 0** |

**The granularity hypothesis was rejected.** V2 enforces a real ceiling — the corpus
maximum falls from 16,096 characters to 1,999 and 3,069 over-2,000 chunks become none — and
it rescued **nothing**. Across all 22 spans it improved 8 ranks and worsened 9, and **not
one span** that was previously unreachable became reachable.

The motivating case is the clearest evidence. AN-003's answer went from 1.65% to 4.79% of
its chunk and is still not retrieved at depth 300, because every low-df term in the
question (`contain` df 111, `Batches` df 286, `requests` df 1,218) is absent from the chunk
holding the answer. That is vocabulary mismatch, which no chunker can fix.

V2 also showed a real cost: AN-002 fell from rank 27 to 172 because splitting its chunk cut
query-term coverage from 12/13 to 7/13. The control's oversized chunks were accidentally
*helping* a bag-of-words retriever by aggregating co-occurring terms.

EXP-005B's +3 is real but is **not** the hypothesis being confirmed: V3 also prepends a
section-path context header to the indexed text, which is why its document recall rose to
0.900 when the design expected it to stay flat. The gain is attributable to contextual
enrichment, not to chunk size. `chunker_v1_control` therefore remains the published
baseline, and the next experiment is to isolate enrichment from granularity.

All three chunkings coexist in the database as separate chunk sets, and EXP-000 re-runs
byte-identically against the control set.

### EXP-006 — contextual enrichment ablation (decomposing EXP-005's V3)

EXP-005's V3 changed boundaries *and* prepended structural context to the indexed text, so
its +3 could not be attributed. EXP-006 decomposes it as a 2×2. Full write-up:
**[EXP-006-enrichment-ablation.md](docs/reports/EXP-006-enrichment-ablation.md)**.

| | no enrichment | + structural enrichment |
|---|---|---|
| **control chunking** | **A** — 0.475, 9/20 | **B** — 0.475, 9/20 |
| **bounded chunking** | **C** — 0.500, 9/20 | **D** — 0.550, 10/20 |

**Contextual enrichment did not improve retrieval.** A → B — the comparison that isolates
enrichment — moved macro recall by **exactly zero**, rescuing one question (AN-004, a fragile
12→7 crossing whose BM25 score actually *fell*) and regressing another (AN-005, 4→18).

The mechanism is measured: enrichment **inflates document frequency**. Writing
`Provider: anthropic` into all 12,028 Anthropic chunks took that term from df 3,289 to
12,028, destroying its IDF. Across 22 evidence spans, enrichment supplied a query term to
only **3**, and in **none** of those was it a discriminative one. AN-005 regressed because
its best term `editing` went from df 66 to 211.

B and D are row-for-row copies of A and C — 0 boundary differences, 0 body differences — so
an A→B difference cannot be a chunking difference. The canonical chunk body is never
mutated; the header lives in a separate `search_text` column, because a citation must quote
real source text.

AN-003 became reachable for the first time (rank 74 under D, previously absent at depth 300)
but is still nowhere near k=10. Its discriminative terms — `contain` (df 111), `most`,
`many`, and `requests`, which never matches the body's singular `request` — appear nowhere
in the chunk that answers it.

**Two hypotheses have now been tested with controlled interventions and neither survives:**
oversized chunks (EXP-005, zero rescued) and missing structural context (EXP-006, Δ0.000).
The surviving diagnosis is that BM25 cannot bridge the vocabulary gap between how a question
is phrased and how the documentation states the answer. The next justified experiment is a
real pretrained embedding model, with AN-003 as its canonical test case. Enrichment is
**not** frozen and the baseline remains control chunking, unenriched.

### Limitations — read before quoting any number above

1. **EXP-NULL did not run.** The closed-book control needs a generation credential and reachable provider host; this environment has neither (`experiments/EXP-NULL/results.json` records `status: "blocked"` with the exact error). **Nothing here shows that retrieval beats what the model already knows** — that was the primary question V1 was built to answer, and it remains unanswered. Every retrieval number below is uncalibrated against the closed-book floor.
2. **The dense retriever is a substitute.** `huggingface.co` and `api.openai.com` are both blocked by this environment's network egress allowlist, so neither the configured sentence-transformer nor the OpenAI embedding endpoint could be used. EXP-001/002/003 use an offline TF-IDF+SVD (LSA) embedder fitted on the corpus itself. LSA has no pretrained semantic knowledge and no subword handling. **All dense, hybrid and RRF numbers are lower bounds**, and "lexical beats dense" is a statement about *this* embedder, not about dense retrieval. Re-running with a real embedding model is the single highest-value next step.
3. **n = 20 is not a holdout.** Nothing here is statistically significant. One case is 5 percentage points of macro recall. The paired comparisons are more trustworthy than the averages, which is why they are given per question.
4. **The corpus is provider-skewed.** 139 Anthropic docs to 63 OpenAI docs, because OpenAI's documentation hosts are egress-blocked and only OpenAI's public GitHub repositories were reachable. At EXP-000 lexical fully recalls 7 of 8 OpenAI cases (the eighth, OA-006, partially) but only 2 of 12 Anthropic cases. The split tracks document size and structure — Anthropic's API reference pages average 1,207-character chunks against OpenAI's 491 — not provider quality.
5. **BM25 `k1`/`b` were not tuned.** Standard defaults (1.2 / 0.75), deliberately not swept against the golden set. The `rrf_k` and candidate-pool grids *were* swept on these same 20 cases, so the pool-100 configuration is selected on the evaluation set and is optimistic.
6. **The golden set is single-author.** "Human-verified" here means every anchor was read against the source document and mechanically verified to contain the quoted claim (`evals/golden/v1.anchors.json`), not that multiple annotators agreed.
7. **Retrieved text is redacted from published results.** Results files carry evidence anchors, ranks, scores and a sha256 of each hit, but not the chunk text, because the corpus is copied provider documentation. Use `--include-text` for local traces; those are gitignored.

### What V1 has not earned the right to add

A reranker cannot rescue AN-003 — the correct chunk is absent from the top 200 candidates entirely. A larger `k` would inflate the metric without improving retrieval. A confidence threshold addresses a calibration problem the data does not show. The next experiment justified by evidence is re-chunking (EXP-004), and because ground truth is anchored to `(version_id, section_path, char_span)` rather than `chunk_id`, it can run against the same 22 unchanged spans.

## Citation / answer demo

After dense embeddings exist:

```bash
ragv1 answer "your question" SNAPSHOT_ID EMBEDDING_MODEL_ID
```

The generator is instructed to answer only from retrieved evidence and cite source labels `[S1]`, `[S2]`, etc. This command is a demo path; retrieval experiments remain the V1 source of truth.

## Data and reproducibility

The repo stores metadata, hashes, configs, and source manifests. Raw documentation snapshots are gitignored. Corpus snapshots are immutable database manifests of exact document versions.

When you publish an experiment, record:

- git commit
- corpus snapshot ID
- parser version
- chunking config hash
- embedding model ID/version
- experiment config
- per-question results

All of that is captured for the published run: the snapshot row carries the git commit, parser version and chunking config hash; each results file carries the snapshot ID, mode, k, candidate pool sizes, `rrf_k` and embedding model ID; and `experiments/summary.json` holds per-question recall for every configuration. The corpus itself is reproducible from `data/manifests/v1-openai-anthropic.yaml` — Anthropic entries by canonical URL and captured time, OpenAI entries by repository and pinned commit SHA.

Published results are redacted at write time: `redact_hit` replaces each hit's chunk text with a sha256 and a length, so a results file is a reviewable record of anchors, ranks and scores without redistributing provider documentation. `--include-text` writes an unredacted `*-traces.jsonl` beside it for local debugging; that path is gitignored.

## Verification

```bash
pytest -q        # 12 passed
ruff check .     # All checks passed!
```

Beyond the shipped tests, corpus health was checked directly before any experiment ran: all 202 document versions ingested with status `current`, and all 14,209 chunk spans round-trip byte-exactly against `normalized_text` (0 mismatches). That check is what makes `(version_id, section_path, char_span)` trustworthy as ground truth. Re-ingesting the same manifest is idempotent — it creates no duplicate versions.

## What V1 does not claim

- It does not claim a reranker is useful yet.
- It does not claim a specific candidate-pool size is optimal.
- It does not use a scalar exact-identifier boost.
- It does not use an LLM judge where deterministic scoring is possible.
- It does not claim a 20-case seed is a statistically strong holdout.

Those become experiments only after the baseline produces real failures.

The baseline has now produced two, both written up:

- [FAIL-0001](docs/failure-reports/FAIL-0001.md) — the lexical baseline retrieved nothing at all. Diagnosed and fixed; 0.000 → 0.475.
- [FAIL-0002](docs/failure-reports/FAIL-0002.md) — retrieval reaches the right document and returns the wrong chunk. Diagnosed as chunk granularity, then **tested and largely refuted** in [EXP-005](docs/reports/EXP-005-rechunking.md): bounding chunk size rescued zero questions. The report is left standing with its outcome recorded, because a prediction that turned out wrong is part of the record.

And one claim V1 set out to make and could not: **it does not claim retrieval beats closed-book generation**, because EXP-NULL never ran. That is the honest headline.
