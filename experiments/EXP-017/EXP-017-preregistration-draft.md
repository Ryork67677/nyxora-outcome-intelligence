# EXP-017 — SEARCH-PROJECTION / EVIDENCE-PRESERVING RETRIEVAL

**PREREGISTRATION DRAFT — DESIGN ONLY. NOT AUTHORIZED TO RUN.**

Written 2026-09-01T03:49:47Z UTC (2026-08-31T23:50:00-04:00 ET). ChatGPT ordered design only after accepting EXP-018B L=10.

This draft does **not** implement retrieval, does **not** build the projection table, does **not** embed, and does **not** score V2-DEVSET-001. It does **not** open `gold150-v1/holdout.json` or load gold150-v1 development/validation. It does **not** modify SYSTEM-D, SYSTEM-E-WITHIN-DOC.json, CE/blend weights, or `cs_v1_control`.

Baseline development system: **SYSTEM-E-L10-WITHIN-DOC** config_hash `bae1c05b5c47c179dc5cd7972a14bd23d102a4d513b674667eb469e17cd85e89`.

---

## 0. Hypothesis

A separate **additive search representation** can improve candidate evidence coverage beyond SYSTEM-E-L10 while `cs_v1_control` remains the citation/evidence representation.

**SEARCH UNIT ≠ CITATION UNIT.**

- `cs_v1_control` stays immutable (14209 rows). Canonical `chunk.text` / `char_start` / `char_end` / `section_path` / `version_id` remain the citation identity.
- The new lane may **ADD** candidates. It must **never remove** an E-L10 candidate from the pool.
- Every projection maps deterministically back to `version_id`, `section_path`, canonical `char_start` / `char_end`, and therefore to covering `chunk_id`s.
- No new neural model. No CE/blend change. No rerank optimization (that is EXP-019). Cases that enter the pool but stay out of top-10 are EXP-019 headroom.

## 0.1 What this draft did and did not inspect

Allowed, and done: corpus-wide chunk-length, section-length, tiny/long units, adjacency, headings/`section_path`, overlap/boundary, storage/index implications. Read-only SQL against `snap_689e336380a054d8039dc35b2c09cd0a` / `cs_v1_control`. Prior EXP-005/006/009/010 **corpus** measurements (truncation rate, encoder token budget) — not their gold-case movement tables.

Forbidden, and not done: inspecting which V2-DEVSET-001 cases miss candidate retrieval; using the 11 V1 holdout failures to pick rules; loading gold labels to choose window sizes; running BM25/dense/CE against eval queries.

---

## 1. Exact projection construction algorithm

**Projection set id (proposed):** `ps_v2_ovl_win448_s224`.

**Tokenizer:** frozen SYSTEM-A MiniLM WordPiece (`sentence-transformers/all-MiniLM-L6-v2`, fingerprint `bd95feaeacf98559`), `add_special_tokens=False`. Do **not** trust the tokenizer.json default max length of 128 (EXP-010). Truncation is disabled while measuring offsets; windows are sliced in token space so each projection payload is ≤ 448 tokens.

**Per document version in the snapshot:**

1. Load `document_version.normalized_text` and all `cs_v1_control` chunks for that `version_id`, `ORDER BY ordinal ASC`.
2. Let `src_lo = min(char_start)`, `src_hi = max(char_end)`. Let `text = normalized_text[src_lo:src_hi]`.
3. Adjacent control chunks in this corpus have **zero character overlap** and inter-chunk gaps of **1–26 chars (median 2)** — stripped whitespace. Consecutive ordinals therefore form one canonical coverage envelope that is an exact source substring. (Do **not** group by `section_path` and take min/max: that envelope is not always contiguous.)
4. Encode `text` with offset mapping. Let `T` be the token count.
5. Window starts in token space:
   - if `T <= 448`: one start `0`, width `T`.
   - else starts `0, 224, 448, …` while `start + 448 < T`; then append a **right-aligned** final start `T - 448` if it is not already present.
   - each window is tokens `[start, min(start+448, T))`.
6. Convert token span → local char span via offset mapping (start of first token, end of last token). Convert to absolute source offsets: `char_start = src_lo + local_start`, `char_end = src_lo + local_end`.
7. `projection.text = normalized_text[char_start:char_end]` (exact source substring; never mutated, never heading-prepended).
8. `covering_chunk_ids` = control chunks of the same `version_id` whose `[char_start, char_end)` overlaps `[projection.char_start, projection.char_end)` by ≥ 1 character, ordered by `ordinal ASC`.
9. `section_path` stored on the projection = the `section_path` of covering chunks (one path if unique; otherwise the list of distinct paths in ordinal order). Citation mapping is via covering chunks, not via this field alone.
10. `projection_id = stable_id("prj", version_id, char_start, char_end, content_hash(text), length=40)`.
11. Drop duplicate `(version_id, char_start, char_end)` after right-align (deterministic: keep lowest `ordinal` assignment, which is insertion order).
12. Skip a window only if it is character-identical to **exactly one** covering canonical chunk **and** that chunk's source span equals the window span (redundant with A / E-L10). Character simulation found **3** such windows; expect a similarly tiny skip set in token space.

No heading prefix on `search_text` (EXP-006 showed broad repetitive prefixes inflate DF; EXP-010 restricted carryover to forced splits). Canonical `chunk.text` is never copied into `search_text` / `context_header` on `cs_v1_control`.

## 2. Type

**Overlapping canonical-coverage windows** (other / not a rechunk).

Not selected:

- **Contextualized canonical chunks** — 1:1 with 14209 control rows; prepends do not create a new localization unit for long-chunk tails or straddling cuts. EXP-006 already tested structural prefixes as index text.
- **Adjacent-chunk full bridges** — 14007 (or 8215 same-section) concats. Mean chunk 1097 chars, p90 3466; full concat routinely exceeds MiniLM 512 and truncates the very boundary the bridge exists to expose.
- **Section_path envelope windows** — `section_path` groups are not reliably contiguous (Beta `['Versions']`: 2 chunks, 1.53M char envelope, 20 chars of own text).

## 3. Exact size / overlap / context rules

| knob | value | source |
| --- | --- | --- |
| window payload | **448 tokens** | EXP-010 encoder target (usable 510 = 512−2 specials; hard 480; target 448). Measured from shipped tokenizer/model, not from eval labels. |
| stride / overlap | **224 tokens (50%)** | Structural default: any token span of length ≤ overlap is fully contained in some window. Not taken from gold span lengths. |
| right-align last window | yes | So the document tail is a full 448-token payload when `T > 448`. |
| context prefix | none | Search text = exact source substring. |
| inter-chunk whitespace | included | Envelope `normalized_text[src_lo:src_hi]` keeps the observed 1–26 char gaps. |
| code / table / prose | included equally | Type is a control property; no type-specific window rule. |

Character equivalents used **only** for the pre-build audit: 448×3.80 = 1702 chars, 224×3.80 = 851 chars, where 3.80 = EXP-009 control chars/token (4,097,597 tokens / 14,209 chunks / mean 1097.2 chars). Implementation tokenizes; it does not slice by 1702 characters.

## 4. How the rules were chosen (no eval-label outcomes)

Corpus facts (see `corpus-structure-audit.json`):

1. **No overlap in the citation layer.** 14007 adjacent ordinal pairs, **0 character overlaps**, 13965 gaps of 1–26 chars (median 2). Control chunker (`chunking.py`) is paragraph-aware with no fixed overlap. A gold span that sits on a cut cannot be a single search unit today.
2. **Encoder localization.** EXP-009 MiniLM@512 truncated **3300/14209 = 23.22%** of control chunks; token coverage 0.761. Long-chunk tails are invisible to dense retrieval. 3332 chunks are ≥1700 chars; 150 are ≥3500; max 16096.
3. **Tiny units.** 3927 chunks < 200 chars (27.6%) despite a 200-char grouping minimum — leftovers, short code fences, etc. A 448-token window groups several tiny neighbours.
4. **Section_path is universal but not a contiguous span.** 5933 groups, all nonempty paths, depth 1–5, 3553 distinct leaf headings. Envelope-by-path is unsafe (non-contiguous parent headings).
5. **Replacement rechunking already failed as a research line.** EXP-005 (size×BM25) and EXP-008 (size×dense) shortened chunks using corpus percentiles and did not beat control as a *replacement*. EXP-017 therefore **adds** a search representation and keeps `cs_v1_control` as citation units.
6. Window 448 / stride 224 come from the **encoder budget** and a 50% overlap default, not from gold-span histograms and not from V2D miss identities.

## 5. Mapping from every projection back to canonical source

Each projection stores:

- `version_id`
- `char_start`, `char_end` (absolute offsets into `normalized_text`)
- `text = normalized_text[char_start:char_end]`
- `covering_chunk_ids[]` (frozen at build; overlap ≥ 1 char, ordinal order)
- `section_paths[]` copied from those chunks

Citation / evidence identity is **always** a covering `cs_v1_control` `chunk_id` (and that chunk's `version_id`, `section_path`, `char_start`, `char_end`). A projection is never a citation.

At retrieval time a projection hit expands to **all** covering canonical `chunk_id`s (needed for boundary recovery). Dedupe follows (§6).

## 6. Deduplication behavior

1. Projections unique on `(version_id, char_start, char_end)`.
2. After mapping, candidate identity is canonical `chunk_id`.
3. Union with E-L10 is by `chunk_id`.
4. A canonical chunk already in the E-L10 pool is **kept** with its E-L10 scores; a projection hit on it does **not** replace or drop it.
5. New `chunk_id`s (not in E-L10) are ranked by best projection-lane fused score, then `chunk_id ASC`, and capped to **P=20** (§8).

## 7. Retrieval method for the new lane

Same frozen retrievers as SYSTEM-A, **on the projection set**, not on `cs_v1_control`:

- BM25: k1=1.2, b=0.75, `simple` tsconfig, full **projection-set** IDF (the search corpus for this lane), tie-break `round(score::numeric, 9) DESC, projection_id ASC`.
- Dense: MiniLM `emb_e7d4183fd6eb878ae2fdf080efb6861e` fingerprint `bd95feaeacf98559`, max_seq 512, cosine, **exact** search, no ANN.
- Fusion: labelled RRF, k=60, `pool_per_retriever=50` (same as A). Lists: `projection_bm25`, `projection_dense`.
- Query text: raw user question, verbatim. No rewrite, no expansion.

Do **not** reuse SYSTEM-A's canonical-chunk BM25/dense lists (different search units, different IDF, different embeddings).

## 8. Candidate budget

| stage | budget |
| --- | --- |
| projection BM25 | 50 |
| projection dense | 50 |
| projection RRF fused pool | up to 100 projection hits |
| mapped canonical extras after excluding E-L10 | cap **P=20** |

**P=20** is preregistered from computational budget, not from miss identities: it matches E's per-parent generation depth `W=20`; CE on E-L10 is ~56.7 ms per union member (5903.9 ms / 104.1); P=20 ⇒ ~+1.13 s CE plus ~+0.36 s retrieval. Not retuned after scores. Not a promotion threshold.

## 9. Merge behavior with SYSTEM-E-L10

Architecture:

```
SYSTEM-A global lane (pool 100)
        +
E-L10 within-document lane (L=10 extras, W=20 generate, batched IDF)
        +
EXP-017 projection lane (map → canonical chunk_ids, additive P=20)
        ↓
union by chunk_id  (never drop E-L10)
        ↓
frozen D CE + 0.7/0.3 blend
```

Steps:

1. Materialize E-L10 pool `C_E` exactly as SYSTEM-E-L10-WITHIN-DOC (A-100 ∪ L=10 extras, two-list merge-RRF). **Do not change that merge-RRF.**
2. Run the projection lane. Map hits → covering `chunk_id`s.
3. `C_new = unique chunk_ids not in C_E`, ordered by best projection fused score DESC, `chunk_id ASC`. Take `C_P = C_new[:20]`.
4. Final pool `C = C_E ∪ C_P`.
5. **Do not add a third RRF list.** Adding `projection` into merge-RRF would change A-channel ranks of E-L10 members (rerank optimization; EXP-019). `C_P`-only members have no A/local RRF score and use existing `minmax_degenerate=0.5` on the A channel.
6. Frozen CE artifact `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`, blend 0.7/0.3, `top_k=10`.

## 10. Deterministic tie-breaking

- Projection BM25: `round(score numeric 9) DESC, projection_id ASC`.
- Projection dense: cosine DESC, `projection_id ASC`.
- Projection RRF: standard labelled RRF k=60; ties `projection_id ASC`.
- Additive extras `C_P`: best projection fused score DESC, `chunk_id ASC`.
- Final blend (unchanged E-L10 rule, with one specified hole for `C_P`-only): blend DESC, then E-L10 merge-RRF rank (members not in E-L10 RRF sort after those that are), then `chunk_id ASC`.

## 11. Storage / index format

**New tables**, not new `chunk` rows. Projections must not be citeable as `chunk_id`.

```
search_projection_set(
  projection_set_id TEXT PK,   -- ps_v2_ovl_win448_s224
  derived_from_chunk_set_id TEXT,  -- cs_v1_control
  snapshot_id TEXT,
  tokenizer_fingerprint TEXT,
  window_tokens INT, stride_tokens INT,
  config JSONB, config_hash TEXT
)

search_projection(
  projection_id TEXT PK,            -- prj_…
  projection_set_id TEXT,
  version_id TEXT,
  ordinal INT,
  char_start INT, char_end INT,
  text TEXT,
  content_hash TEXT,
  covering_chunk_ids TEXT[],
  section_paths TEXT[],
  search_vector TSVECTOR GENERATED ALWAYS AS (to_tsvector('simple', text)) STORED,
  UNIQUE(projection_set_id, version_id, ordinal),
  CHECK (char_end > char_start)
)

search_projection_embedding(
  projection_id TEXT,
  model_id TEXT,
  embedding VECTOR,
  embedding_hash TEXT,
  content_hash TEXT,
  model_fingerprint TEXT,
  PRIMARY KEY(projection_id, model_id)
)
```

GIN on `search_vector`. Exact pgvector scan, no HNSW required for this experiment (A is exact). `chunk` / `chunk_embedding` for `cs_v1_control` are **not written**.

## 12. Expected computational cost

Character simulation (tokenizer build will replace these counts):

| | |
| --- | ---: |
| control chunks | 14209 |
| estimated projections | **18221** (1.28×) |
| extra MiniLM embed time | ~1605 s (~27 min) vs EXP-009's 1251 s / 14209 |
| extra embedding storage | ~26.9 MB (control payload 21 MB) |
| extra BM25 index | tsvectors over 18221 windows; chunk table today 37 MB — same order |
| two-doc tail | Compliance API ~5587 windows, Beta ~3670 (51% of windows from 2/202 docs) |

Query latency vs E-L10 **6454.8 ms** (A 358.5 + local BM25 192.4 + CE 5903.9):

| extra | estimate |
| --- | ---: |
| projection BM25+dense | ~358–500 ms (1.28× rows vs A; A was 358.5 ms) |
| CE on +P=20 | ~1134 ms |
| **total** | **~7.9–8.1 s** |

Not measured. CE remains the dominant term (Claude's parallel score-preserving CE track is orthogonal).

## 13. Integrity tests (no canonical evidence mutation)

Before and after any later authorized build, all of the following must hold. **Fail-closed: if any fail, do not score.**

1. `SELECT count(*) FROM chunk WHERE chunk_set_id='cs_v1_control'` = **14209**.
2. Aggregate identity `chunk_id_agg_sha256` = `394a76b1569f0b46d4151442d5dba0fdf615beb2fc75355df743e0ea0979d93e`.
3. Span identity sha256 of `chunk_id:content_hash:char_start:char_end` ordered by `chunk_id` = `44563cbb5abb4f9a6917b2398dca7b55df60d7359d368b9873b675c78937873b`.
4. `search_text` IS NULL and `context_header` IS NULL for all 14209 control rows.
5. MiniLM `chunk_embedding` rows for control = 14209, fingerprint min=max=`bd95feaeacf98559`.
6. File bytes unchanged:
   - `experiments/EXP-018/SYSTEM-E-WITHIN-DOC.json` `e228616beee1bcb13855c2eadee9fc20ec1fae3e54c77b28587114568c64d087`
   - `experiments/EXP-016/SYSTEM-D-GUARD.json` `e9267f5581404e9885598979204c08762cd33f362703e526b20f4d3430c35a82`
   - `experiments/EVAL-HOLDOUT-001/SYSTEM-D-RELEASE.json` `1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40`
   - `evals/splits/gold150-v1/holdout-access.log.jsonl` 235 bytes `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`
7. No row in `search_projection.covering_chunk_ids` that is not a `cs_v1_control` `chunk_id`.
8. For every projection: `text = document_version.normalized_text[char_start:char_end]` and `content_hash` matches.
9. Projection ids use prefix `prj_`; they never collide with `chk_`.
10. `holdout.json` not opened; gold150-v1 development/validation not loaded.

## 14. Exact experiment metrics (when later authorized)

Dataset: frozen **V2-DEVSET-001 n=50 only**. Do not load validation. Do not open holdout.

**Primary:** candidate gold-span Recall@100. Baseline SYSTEM-E-L10 = **44/50**.

**Secondaries (ChatGPT list, recorded, not used to retune windows):**

- strict Recall@10
- span Recall@10
- MRR
- document recall
- candidate additions (mean `|C_P|`, mean union vs 104.1)
- rescues / regressions vs E-L10 (strict R@10 paired)
- rank-1 destructions vs E-L10
- mean pool size
- latency (A / local BM25 / projection lane / CE / total)

Do **not** create a promotion threshold from the identities of the six current candidate misses. Those identities were not inspected to choose window/stride/P.

### Proposed development decision rule (not independent validation)

After the single preregistered run:

- **MECHANISM_SUPPORTED** iff
  - primary candidate gold-span Recall@100 **≥ 45/50** (strictly above the frozen E-L10 development baseline 44/50; +1/50 is the smallest observable improvement on n=50), **and**
  - **0** strict Recall@10 regressions versus E-L10, **and**
  - **0** rank-1 destructions versus E-L10.
- Else **MECHANISM_NOT_SUPPORTED**. Do not mint a new system identity. Do not retune window/stride/P on the same split.
- Do **not** require named miss recoveries.
- Do **not** require strict Recall@10 to improve (pool-but-not-top-10 is EXP-019).
- **RELEASE = NOT_FROZEN.** **VALIDATION = NOT_RUN.** **HOLDOUT = UNTOUCHED.**

≥45/50 is a development-stage comparison to the E-L10 baseline, **not** a threshold fitted to which six cases currently fail.

---

## Standing do-nots for any later execution

- Do not implement until ChatGPT/owner authorizes this draft (or a revision).
- Do not change 0.7/0.3, CE ONNX, SYSTEM-A hash, SYSTEM-D, SYSTEM-E-WITHIN-DOC.json, L/W/parent_n.
- Do not start EXP-019 in this experiment.
- Do not freeze a v2 release from development alone.

## Artifacts written with this draft

- `experiments/EXP-017/EXP-017-preregistration-draft.md` (this file)
- `experiments/EXP-017/corpus-structure-audit.json`
- `experiments/EXP-017/corpus-structure-audit.md`
