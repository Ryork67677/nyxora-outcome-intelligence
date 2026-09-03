# HOLDOUT-FAILURE-ANALYSIS-001

Understand-only classification of the 11 EVAL-HOLDOUT-001 misses.
No code fixes. No retuning. No second retrieval run. Ranks and CE scores
are taken from `EVAL-HOLDOUT-001-per-case.json`. Covering-chunk existence
was checked by reading `cs_v1_control` in the restored database (char-span
overlap on the gold `version_id`), not by reloading holdout through the
harness.

Question text is omitted. Evidence is identified by case ID, section_path,
and char offsets already in the per-case file.

Candidate-pool coverage (holdout report): **97/104** gold spans in the
SYSTEM-A top-100 used as D's candidate generator. The seven pool-absent
spans are exactly the gold spans under the six
`CANDIDATE_GENERATION_FAILURE` cases below.

Primary label is **exactly one** per case:

- `CANDIDATE_GENERATION_FAILURE` — gold span never entered A pool 100
- `RERANKING_FAILURE` — in the pool, outside D top 10
- `CHUNKING_FAILURE` — no covering chunk in `cs_v1_control`
- `METADATA_VERSION_ISSUE` — version / section metadata mismatch
- `GOLD_AMBIGUITY` — the required span is not a well-posed key

---

## Counts

| primary label | n | cases |
| --- | ---: | --- |
| CANDIDATE_GENERATION_FAILURE | **6** | GOLD-B001-09, GOLD-B002-06, GOLD-B003-04, GOLD-B006-02, HA-37, HA-43 |
| RERANKING_FAILURE | **5** | GOLD-B001-02, GOLD-B005-07, HA-20, HA-21, HA-58 |
| CHUNKING_FAILURE | **0** | — |
| METADATA_VERSION_ISSUE | **0** | — |
| GOLD_AMBIGUITY | **0** | — |
| **total** | **11** | |

Every missed span has a covering `cs_v1_control` chunk with matching
`section_path`. None of the 11 are a hole in the chunker, a wrong
`version_id`, or an ambiguous gold key. Two candidate-generation misses
have contributing chunk-shape notes (oversized / undersized leftovers);
those do not change the primary label.

---

## RERANKING_FAILURE (5)

Gold chunk was in the SYSTEM-A pool. Blend placed it outside top 10.

### GOLD-B001-02 — RERANKING_FAILURE

| | |
| --- | --- |
| provider / shape | openai, single_span, unlabeled (batch 001) |
| document | Agents · `['Agents', 'Basic configuration']` 3571:3725 |
| covering chunk | `chk_4473c14a44b77dd08fbe8d5e4585c5164760330f` (in pool) |
| **A rank / D rank / CE** | **5 / 63 / −10.3379** |
| blend | 0.1959 |
| doc recall | 1.0 (D doc rank 1) |
| within | absent@50; present@100 |

A-pool rank 5 is inside top 10; D rank 63 is not. CE logit **−10.34** is
the most negative gold score among the 11 misses. Pattern matches the
EXP-016 HA-24 diagnostic (CE prefers a generic neighbour over the exact
span), now on holdout. Blend 0.3 A was not enough to keep an A-rank-5
span inside 10.

### GOLD-B005-07 — RERANKING_FAILURE

| | |
| --- | --- |
| provider / type | anthropic, `lifecycle_compatibility_migration` / deprecation |
| document | Context editing · `['Client-side compaction (SDK)']` 75250:75380 |
| covering chunk | `chk_4e24ec5e67a63aa6cb59ee01cb795a91510f09d9` |
| **A rank / D rank / CE** | **51 / 14 / +1.3797** |
| blend | 0.5688 |
| doc recall | 1.0 (D doc rank 1) |
| within | absent@10; present@20 |

CE *helped* (51→14) but not enough. Headroom existed inside the pool;
the blend stopped at rank 14. Not a pool miss.

### HA-20 — RERANKING_FAILURE

| | |
| --- | --- |
| provider / type | openai, `configuration_interaction` |
| document | Human-in-the-loop · `['Human-in-the-loop', 'How the approval flow works']` 4886:5194 |
| covering chunk | `chk_91b59aa08660b93d3aa57ac22f7367bb361d3794` (3296:5703) |
| **A rank / D rank / CE** | **21 / 15 / +2.6582** |
| blend | 0.7199 |
| doc recall | **0.0** (D doc rank 15) |
| within | absent@10; present@20 |

CE lifted 21→15; still outside 10. Same covering chunk as HA-21. Document
itself is outside D top 10.

### HA-21 — RERANKING_FAILURE

| | |
| --- | --- |
| provider / type | openai, `request_response` |
| document | Human-in-the-loop · same section as HA-20, chars 5538:5703 |
| covering chunk | **same** `chk_91b59aa08660…` as HA-20 |
| **A rank / D rank / CE** | **14 / 29 / −2.5937** |
| blend | 0.5572 |
| doc recall | 1.0 (D doc rank 7 — a *different* chunk of this version) |
| within | absent@20; present@30 |

Same physical chunk as HA-20. CE moved them in **opposite** directions
(+2.66 vs −2.59). A 14→D 29 is a demotion. Another chunk from the gold
document reached D rank 7, so document recall passes while the required
span does not.

### HA-58 — RERANKING_FAILURE

| | |
| --- | --- |
| provider / type | openai, `exact_lookup` |
| document | Models · `['Models', 'Runner-managed retries', 'Safety boundaries']` 36894:37138 |
| covering chunk | `chk_6e8c2ae3d10d25fb47d647b925de69b5abe8115f` |
| **A rank / D rank / CE** | **1 / 19 / −3.5081** |
| blend | 0.6700 |
| doc recall | 1.0 (D doc rank 5) |
| within | absent@10; present@20 |

**A-rank-1 gold span dropped out of D top 10.** EVAL-VAL-002 recorded 0
rank-1 destructions on n=40. That protection did not hold on this holdout
case. 0.3 A-weight was insufficient against CE −3.51. This is the holdout
instance of the HA-24 failure mode that caused pure CE to be rejected.

---

## CANDIDATE_GENERATION_FAILURE (6)

Gold span has a covering chunk. That chunk was not in the SYSTEM-A
top-100, so CE/blend never saw it. D cannot recover what A did not
propose.

### GOLD-B001-09 — CANDIDATE_GENERATION_FAILURE

| | |
| --- | --- |
| provider / shape | anthropic, single_span, unlabeled |
| document | Tool runner (SDK) · `['Iterating over the tool runner']` 19885:20004 |
| covering chunk | `chk_34c2359de238…` 19507:20173 (666 chars, path match) |
| **A rank / D rank / CE** | **null / null / null** |
| in_candidate_pool | false; absent@100 |
| doc recall | 1.0 (D doc rank **2**) |

Right document in D top 10; the gold chunk of that document never entered
the pool. 15 chunks share this section_path; only the covering one matters,
and A did not retrieve it.

### GOLD-B002-06 — CANDIDATE_GENERATION_FAILURE

| | |
| --- | --- |
| provider / shape | anthropic, single_span, unlabeled |
| document | Advisor tool · `['Tool parameters']` 13205:13710 |
| covering chunk | `chk_f480c9247d61…` 10149:14216 (**4067 chars**) |
| **A rank / D rank / CE** | **null / null / null** |
| in_candidate_pool | false; absent@100 |
| doc recall | 1.0 (D doc rank **1**) |

Right document is D rank 1; gold span never in pool. Contributing shape
note (not a label change): covering chunk is 4067 characters, above
control `max_chunk_chars=3500`. That is a known FAIL-0002-style unit
(right document, unreachable passage). Primary label remains candidate
generation: a covering chunk exists and was not proposed.

### GOLD-B003-04 — CANDIDATE_GENERATION_FAILURE

Multi-span (`error_behavior`). Span 0 succeeded; span 1 never entered the
pool, so the case fails strict full-case Recall@10.

| span | section | chars | A | D | CE | in pool |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 0 | `['Model compatibility']` | 88971:89112 | **1** | **1** | **+5.8239** | true |
| 1 | `['Model compatibility']` | 92785:92898 | null | null | null | **false** |

Covering chunk for span 1: `chk_9c1a85ba8694…` 92785:92898 (**113 chars**),
path match. Sibling span 0 in the same section is D rank 1. Contributing
shape note: 113 chars is below `min_chunk_chars=200` — a leftover stub
after the middle chunk 89330:92783. Primary label remains candidate
generation: the stub exists as a chunk and was not in pool 100. Not
`GOLD_AMBIGUITY`: both spans are required `multi_span` evidence.

### GOLD-B006-02 — CANDIDATE_GENERATION_FAILURE

| | |
| --- | --- |
| provider / type | anthropic, `error_behavior` / rejects |
| document | Migration guide · `['Opus migration', 'What changed']` 55306:55378 |
| covering chunk | `chk_5a1780d2daca…` 53051:56420 (3369 chars) |
| **A rank / D rank / CE** | **null / null / null** |
| in_candidate_pool | false; absent@100 |
| doc recall | 1.0 (D doc rank 7) |

Gold document is inside D top 10; gold chunk is not in the pool.

### HA-37 — CANDIDATE_GENERATION_FAILURE

| | |
| --- | --- |
| provider / type | openai, `exact_lookup` |
| document | Context management · `['Context management', 'Local context', 'What \`RunContextWrapper\` exposes']` 2417:2541 |
| covering chunk | `chk_6753df2fcba4…` 2105:3674 (1569 chars, path match) |
| **A rank / D rank / CE** | **null / null / null** |
| in_candidate_pool | false; absent@100 |
| doc recall | 1.0 (D doc rank 10) |
| section_path | derived (HA; no stored path on the GOLD record) |

Derived path still matches the chunk `section_path`, so this is not a
metadata miss. Document barely inside top 10; gold chunk never proposed.

### HA-43 — CANDIDATE_GENERATION_FAILURE

`multi_span_same_fact`, both spans uncovered by the **same** chunk, both
absent from the pool.

| span | chars | A / D / CE | in pool |
| ---: | --- | --- | --- |
| 0 | 5215:5371 | null / null / null | false |
| 1 | 5646:5723 | null / null / null | false |

| | |
| --- | --- |
| provider / type | openai, `exact_lookup` |
| document | Realtime transport · `['Realtime transport', 'Custom endpoints and attach points']` |
| covering chunk | `chk_7430419e910e…` 5176:5847 (671 chars) covers **both** spans |
| doc recall | **0.0** (D doc rank 12) |
| section_path | derived (HA) |

Only miss whose gold document is also outside D top 10 among the
candidate-generation set (HA-20 is the reranking analogue). Path matches
the covering chunk; not `METADATA_VERSION_ISSUE`.

---

## Labels not used (and why)

**CHUNKING_FAILURE (0).** Every missed gold span overlaps exactly one
`cs_v1_control` chunk with identical `section_path`. CORPUS-002 already
verified 174/174 gold anchors byte-exact against source text. Undersized
(GOLD-B003-04 span 1, 113 chars) and oversized (GOLD-B002-06, 4067 chars)
units are contributing observations under candidate generation, not
absent chunks.

**METADATA_VERSION_ISSUE (0).** All 11 `version_id`s resolve to a current
document version with a covering chunk. Derived HA `section_path`s that
missed (HA-37, HA-43) still equal the chunk path.

**GOLD_AMBIGUITY (0).** Each miss has a deterministic required span (or
two required spans) that D did not place in top 10. No case failed because
two equally valid answers were keyed.

---

## Cross-cutting observations (not fixes)

1. **Pool ceiling is 97/104 spans, 84/90 cases if a perfect reranker
   reordered the pool.** Six cases are unreachable to D at pool 100.
   Strict holdout 79/90 with five rerank misses implies D converted
   79 of the 84 pool-complete cases (and none of the six pool-incomplete
   ones). GOLD-B003-04 is pool-incomplete despite span 0 at D rank 1.
2. **Rank-1 protection did not generalize.** Validation: 0 A-rank-1
   destructions. Holdout: HA-58 A 1 → D 19. GOLD-B001-02 is the same
   family at A 5 → D 63 with CE −10.34. The 0.7/0.3 blend that qualified
   on development by saving HA-22/HA-24 did not save HA-58.
3. **Same-chunk, opposite CE (HA-20 / HA-21).** One 2407-char Human-in-
   the-loop chunk is gold for two holdout questions. CE +2.66 vs −2.59
   on that same passage. Document concentration in GOLD (Human-in-the-loop
   is 7 holdout cases) makes this visible.
4. **Document recall 0.9778 vs span 0.8833.** Nine of eleven misses still
   retrieve the gold document in D top 10. The residual is passage
   selection inside an already-found document — the FAIL-0002 shape, now
   measured on holdout rather than on 20 development cases.
5. **A ranks here are not a SYSTEM-A holdout score.** They are the fused
   ranks inside D's candidate generator, stored on this one D run.

No retrieval change is proposed. These 11 cases are a diagnostic record
for v1, not a tuning set.
