# EXP-017 — SEARCH-PROJECTION / EVIDENCE-PRESERVING RETRIEVAL

**PREREGISTRATION (AUTHORIZED). AMENDED FROM THE DESIGN DRAFT BEFORE ANY BUILD OR SCORE.**

Written 2026-09-01T04:02:32Z UTC (2026-09-01T00:02:32-04:00 ET). This file **amends** `experiments/EXP-017/EXP-017-preregistration-draft.md`; it does not rewrite the scientific design. ChatGPT authorized a single development run with four preregistration amendments. Machine-readable twin: `experiments/EXP-017/EXP-017-preregistration.json` (hashed before any projection build or V2-DEVSET-001 score).

This preregistration does **not** open `gold150-v1/holdout.json` or load gold150-v1 development/validation. It does **not** modify SYSTEM-D, SYSTEM-E-WITHIN-DOC.json, SYSTEM-E-L10-WITHIN-DOC.json, CE/blend weights, or `cs_v1_control`.

Baseline development system: **SYSTEM-E-L10-WITHIN-DOC** `config_hash` `bae1c05b5c47c179dc5cd7972a14bd23d102a4d513b674667eb469e17cd85e89`.

Uncapped parent SYSTEM-E-WITHIN-DOC (do not interchange these two numbers):

| label | value |
| --- | --- |
| SYSTEM-E-WITHIN-DOC **config_hash** | `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe` |
| SYSTEM-E-WITHIN-DOC **file SHA256** | `e228616beee1bcb13855c2eadee9fc20ec1fae3e54c77b28587114568c64d087` |

---

## ChatGPT amendments incorporated (do not retune)

### 1. Primary decision rule

Replace the draft numeric wording `candidate Recall@100 >=45/50` with:

> candidate gold-span recall MUST BE STRICTLY GREATER THAN the frozen SYSTEM-E-L10 baseline of 44/50.

Since n=50, the smallest observable qualifying result is 45/50. This is not an independent benchmark target. It is a development-stage requirement that the primary metric actually improve. It is **not** a named-miss gate.

**MECHANISM_SUPPORTED** iff:

1. candidate gold-span recall **> 44/50**
2. **zero** strict Recall@10 regressions vs SYSTEM-E-L10
3. **zero** rank-1 destructions vs SYSTEM-E-L10

Otherwise: **MECHANISM_NOT_SUPPORTED**.

Do not retune window, stride, P, retrieval parameters, or decision rule after scores.

### 2. No third RRF list — confirmed

The projection lane is a **CANDIDATE-GENERATION** lane only.

Do **NOT** introduce projection retrieval as a third merge-RRF list.

Existing SYSTEM-E-L10 A/local merge-RRF identities, scores and ranks must remain unchanged before CE.

Projection fused score is used only to:

- rank projection hits
- map them to canonical chunk_ids
- deduplicate
- order previously absent canonical candidates
- choose the additive P=20 extras

It must not alter E-L10 retrieval scores. There is **no** third merge-RRF list.

### 3. Projection-only A channel = 0.0 (not minmax_degenerate=0.5)

The draft proposed `minmax_degenerate=0.5` on the A channel for projection-only members. **Do not use 0.5.**

For canonical candidates newly introduced only by EXP-017:

**A-channel normalized score = 0.0**

Existing SYSTEM-E-L10 candidates retain their existing normalized retrieval-channel values **exactly**.

Do **not** recompute or renormalize the E-L10 retrieval channel merely because projection candidates were appended.

The frozen CE still scores the entire resulting candidate pool. CE minmax may be over the union because CE scores the full pool — **do not renormalize A**. Then apply the existing frozen 0.7 CE / 0.3 retrieval blend.

Purpose: EXP-017 tests candidate discovery. A projection-only candidate must not receive an artificial midpoint retrieval prior simply because it lacked an E-L10 score. If a newly recovered candidate enters the pool but remains below top-10, record it as reranking headroom for EXP-019.

### 4. Hash labeling

Keep config hashes separate from artifact byte SHA256 values. The values in the table above stay distinct. Do not overwrite any existing system artifact.

---

## 0. Hypothesis

A separate **additive search representation** can improve candidate evidence coverage beyond SYSTEM-E-L10 while `cs_v1_control` remains the citation/evidence representation.

**SEARCH UNIT ≠ CITATION UNIT.**

- `cs_v1_control` stays immutable (14209 rows). Canonical `chunk.text` / `char_start` / `char_end` / `section_path` / `version_id` remain the citation identity.
- The new lane may **ADD** candidates. It must **never remove** an E-L10 candidate from the pool.
- Every projection maps deterministically back to `version_id`, `section_path`, canonical `char_start` / `char_end`, and therefore to covering `chunk_id`s.
- No new neural model. No CE/blend-weight change. No rerank optimization (that is EXP-019). Cases that enter the pool but stay out of top-10 are EXP-019 headroom.

## 0.1 What this experiment did and did not inspect

Allowed, and done at design time: corpus-wide chunk-length, section-length, tiny/long units, adjacency, headings/`section_path`, overlap/boundary, storage/index implications. Read-only SQL against `snap_689e336380a054d8039dc35b2c09cd0a` / `cs_v1_control`. Prior EXP-005/006/009/010 **corpus** measurements (truncation rate, encoder token budget) — not their gold-case movement tables.

Forbidden, and not done: inspecting which V2-DEVSET-001 cases miss candidate retrieval; using the 11 V1 holdout failures to pick rules; loading gold labels to choose window sizes; running BM25/dense/CE against eval queries to choose knobs.

---

## 1. Exact projection construction algorithm

**Projection set id:** `ps_v2_ovl_win448_s224`.

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

No heading prefix on search text (EXP-006 showed broad repetitive prefixes inflate DF; EXP-010 restricted carryover to forced splits). Canonical `chunk.text` is never copied into `search_text` / `context_header` on `cs_v1_control`.

---

## 2. Type

**Overlapping canonical-coverage windows** (other / not a rechunk).

Not selected (unchanged from draft):

- **Contextualized canonical chunks** — 1:1 with 14209 control rows; prepends do not create a new localization unit for long-chunk tails or straddling cuts. EXP-006 already tested structural prefixes as index text.
- **Adjacent-chunk full bridges** — 14007 (or 8215 same-section) concats. Mean chunk 1097 chars, p90 3466; full concat routinely exceeds MiniLM 512 and truncates the very boundary the bridge exists to expose.
- **Section_path envelope windows** — `section_path` groups are not reliably contiguous (Beta `['Versions']`: 2 chunks, 1.53M char envelope, 20 chars of own text).

---

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

---

## 4. How the rules were chosen (no eval-label outcomes)

Unchanged from the draft / `corpus-structure-audit.json`:

1. **No overlap in the citation layer.** 14007 adjacent ordinal pairs, **0 character overlaps**, 13965 gaps of 1–26 chars (median 2).
2. **Encoder localization.** EXP-009 MiniLM@512 truncated **3300/14209 = 23.22%** of control chunks; token coverage 0.761.
3. **Tiny units.** 3927 chunks < 200 chars (27.6%).
4. **Section_path is universal but not a contiguous span.** Envelope-by-path is unsafe.
5. **Replacement rechunking already failed as a research line.** EXP-017 **adds** a search representation and keeps `cs_v1_control` as citation units.
6. Window 448 / stride 224 come from the **encoder budget** and a 50% overlap default, not from gold-span histograms and not from V2D miss identities.

---

## 5. Mapping from every projection back to canonical source

Each projection stores `version_id`, `char_start`, `char_end` (absolute offsets into `normalized_text`), `text = normalized_text[char_start:char_end]`, `covering_chunk_ids[]` (frozen at build; overlap ≥ 1 char, ordinal order), `section_paths[]` copied from those chunks.

Citation / evidence identity is **always** a covering `cs_v1_control` `chunk_id`. A projection is never a citation.

At retrieval time a projection hit expands to **all** covering canonical `chunk_id`s. Dedupe follows (§6).

---

## 6. Deduplication behavior

1. Projections unique on `(version_id, char_start, char_end)`.
2. After mapping, candidate identity is canonical `chunk_id`.
3. Union with E-L10 is by `chunk_id`.
4. A canonical chunk already in the E-L10 pool is **kept** with its E-L10 scores; a projection hit on it does **not** replace or drop it.
5. New `chunk_id`s (not in E-L10) are ranked by best projection-lane fused score, then `chunk_id ASC`, and capped to **P=20**.

---

## 7. Retrieval method for the new lane

Same frozen retrievers as SYSTEM-A, **on the projection set**, not on `cs_v1_control`:

- BM25: k1=1.2, b=0.75, `simple` tsconfig, full **projection-set** IDF, tie-break `round(score::numeric, 9) DESC, projection_id ASC`.
- Dense: MiniLM `emb_e7d4183fd6eb878ae2fdf080efb6861e` fingerprint `bd95feaeacf98559`, max_seq 512, cosine, **exact** search, no ANN.
- Fusion: labelled RRF, k=60, `pool_per_retriever=50`. Lists: `projection_bm25`, `projection_dense`. This fusion is **internal to the projection lane**. It is not added to E-L10 merge-RRF.
- Query text: raw user question, verbatim. No rewrite, no expansion.

Do **not** reuse SYSTEM-A's canonical-chunk BM25/dense lists (different search units, different IDF, different embeddings).

---

## 8. Candidate budget

| stage | budget |
| --- | --- |
| projection BM25 | 50 |
| projection dense | 50 |
| projection RRF fused pool | up to 100 projection hits |
| mapped canonical extras after excluding E-L10 | cap **P=20** |

**P=20** is preregistered from computational budget, not from miss identities: it matches E's per-parent generation depth `W=20`. Not retuned after scores. Not a promotion threshold. No extra windows/strides/P.

---

## 9. Merge behavior with SYSTEM-E-L10 (amended)

Architecture:

```
SYSTEM-A global lane (pool 100)
        +
E-L10 within-document lane (L=10 extras, W=20 generate, batched IDF)
        → two-list merge-RRF  =  C_E   (UNCHANGED)
        +
EXP-017 projection lane (map → canonical chunk_ids, additive P=20)
        ↓
union by chunk_id  (never drop E-L10)  =  C = C_E ∪ C_P
        ↓
frozen D CE on entire C
        ↓
blend: a_norm kept exactly from E-L10 for C_E members;
       a_norm = 0.0 for C_P-only;
       ce_norm minmax over C;
       0.7 CE / 0.3 A
```

Steps:

1. Materialize E-L10 pool `C_E` exactly as SYSTEM-E-L10-WITHIN-DOC (A-100 ∪ L=10 extras, two-list merge-RRF, EXP-018B Track-1 batched IDF). **Do not change that merge-RRF.**
2. Run the projection lane. Map hits → covering `chunk_id`s.
3. `C_new = unique chunk_ids not in C_E`, ordered by best projection fused score DESC, `chunk_id ASC`. Take `C_P = C_new[:20]`.
4. Final pool `C = C_E ∪ C_P`. Never drop `C_E`.
5. **Do not add a third RRF list.** `C_P`-only members have no A/local RRF score and receive **A-channel normalized score = 0.0** (not `minmax_degenerate=0.5`). E-L10 `a_norm` values computed on `C_E` are kept exactly; they are not recomputed over the appended union.
6. Frozen CE artifact `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a` scores the entire pool `C`. CE minmax is over `C`. Blend 0.7/0.3, `top_k=10`. Constructor: `CrossEncoderReranker()` defaults (`fast=True` is forbidden).

---

## 10. Deterministic tie-breaking

- Projection BM25: `round(score numeric 9) DESC, projection_id ASC`.
- Projection dense: cosine DESC, `projection_id ASC`.
- Projection RRF: standard labelled RRF k=60; ties `projection_id ASC`.
- Additive extras `C_P`: best projection fused score DESC, `chunk_id ASC`.
- Final blend: blend DESC, then E-L10 merge-RRF rank (members not in E-L10 RRF sort after those that are), then `chunk_id ASC`.

---

## 11. Storage / index format

**New tables**, not new `chunk` rows. Projections must not be citeable as `chunk_id`. Prefix `prj_`. Never write `cs_v1_control` chunk rows.

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

GIN on `search_vector`. Exact pgvector scan, no HNSW. `chunk` / `chunk_embedding` for `cs_v1_control` are **not written**.

---

## 12. Expected computational cost

Unchanged estimates from the draft (character simulation; tokenizer build replaces counts): estimated projections **18221** (1.28×); extra MiniLM embed ~27 min; query total ~7.9–8.1 s vs E-L10 6454.8 ms. CE remains the dominant term (Claude's parallel score-preserving CE track is orthogonal). Not retuned.

---

## 13. Integrity tests (fail-closed: if any fail, do not score)

1. `SELECT count(*) FROM chunk WHERE chunk_set_id='cs_v1_control'` = **14209**.
2. Aggregate identity `chunk_id_agg_sha256` = `394a76b1569f0b46d4151442d5dba0fdf615beb2fc75355df743e0ea0979d93e`.
3. Span identity sha256 of `chunk_id:content_hash:char_start:char_end` ordered by `chunk_id` = `44563cbb5abb4f9a6917b2398dca7b55df60d7359d368b9873b675c78937873b`.
4. `search_text` IS NULL and `context_header` IS NULL for all 14209 control rows.
5. MiniLM `chunk_embedding` rows for control = 14209, fingerprint min=max=`bd95feaeacf98559`.
6. File bytes unchanged:
   - `experiments/EXP-018/SYSTEM-E-WITHIN-DOC.json` `e228616beee1bcb13855c2eadee9fc20ec1fae3e54c77b28587114568c64d087` (this is a **file SHA256**, not a config_hash)
   - `experiments/EXP-016/SYSTEM-D-GUARD.json` `e9267f5581404e9885598979204c08762cd33f362703e526b20f4d3430c35a82`
   - `experiments/EVAL-HOLDOUT-001/SYSTEM-D-RELEASE.json` `1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40`
   - `evals/splits/gold150-v1/holdout-access.log.jsonl` 235 bytes `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`
7. No row in `search_projection.covering_chunk_ids` that is not a `cs_v1_control` `chunk_id`.
8. For every projection: `text = document_version.normalized_text[char_start:char_end]` and `content_hash` matches.
9. Projection ids use prefix `prj_`; they never collide with `chk_`.
10. `holdout.json` not opened; gold150-v1 development/validation not loaded.

---

## 14. Exact experiment metrics (single authorized development run)

Dataset: frozen **V2-DEVSET-001 n=50 only**. Do not load validation. Do not open holdout.

**Primary:** candidate gold-span Recall@100. Baseline SYSTEM-E-L10 = **44/50**.

**Secondaries (recorded, not used to retune windows):**

- strict Recall@10
- span Recall@10
- MRR
- document recall
- candidate additions (mean `|C_P|`, mean union vs 104.1)
- rescues / regressions vs E-L10 (strict R@10 paired)
- rank-1 destructions vs E-L10
- mean pool size
- latency (A / local BM25 / projection lane / CE / total)

**Diagnostics:** n projection hits; n mapping to multiple canonical chunks; n previously absent canonical chunks; gold in pool but below top-10; projection cardinality/storage; integrity hashes.

### Development decision rule (not independent validation)

After the single preregistered run:

- **MECHANISM_SUPPORTED** iff
  - primary candidate gold-span recall **> 44/50** (strictly above the frozen E-L10 development baseline 44/50; at n=50 the smallest observable qualifying result is 45/50), **and**
  - **0** strict Recall@10 regressions versus E-L10, **and**
  - **0** rank-1 destructions versus E-L10.
- Else **MECHANISM_NOT_SUPPORTED**. Do not mint a new system identity. Do not retune window/stride/P on the same split.
- Do **not** require named miss recoveries.
- Do **not** require strict Recall@10 to improve (pool-but-not-top-10 is EXP-019).
- **RELEASE = NOT_FROZEN.** **VALIDATION = NOT_RUN.** **HOLDOUT = UNTOUCHED.**

> 44/50 is a development-stage comparison to the E-L10 baseline, **not** a threshold fitted to which six cases currently fail.

---

## Standing do-nots

- Do not change 0.7/0.3, CE ONNX, SYSTEM-A hash, SYSTEM-D, SYSTEM-E-WITHIN-DOC.json, SYSTEM-E-L10-WITHIN-DOC.json, L/W/parent_n.
- Do not start EXP-019 in this experiment.
- Do not freeze a v2 release from development alone.
- Do not overwrite `cs_v1_control` rows.
- One eval only. No extra windows/strides/P. No query rewrite. No retune.

## Artifacts

- `experiments/EXP-017/EXP-017-preregistration-draft.md` (design draft; kept)
- `experiments/EXP-017/corpus-structure-audit.json` / `.md` (kept)
- `experiments/EXP-017/EXP-017-preregistration.md` (this file)
- `experiments/EXP-017/EXP-017-preregistration.json` (hashed before scoring)
- After integrity: `experiments/EXP-017/EXP-017-integrity.json`
- After the single eval: `experiments/EXP-017/EXP-017-results.json`, `experiments/EXP-017/EXP-017-report.md`

## Preregistration JSON hash (computed after write, before any build/score)

`sha256(experiments/EXP-017/EXP-017-preregistration.json)` = `053a6bf14df088ca9e2283bc3e8dfb0769848a48c54c51a77fbe045795a80cc6`
