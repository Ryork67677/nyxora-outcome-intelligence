# Production RAG v1 — final report

Portfolio artifact for the frozen SYSTEM-D-GUARD-BLEND release candidate.
Holdout executed once. No retuning. No second retrieval run. No live document
fetch. Weights unchanged after freeze.

**Honest claim (exact):** Production RAG v1 achieves 87.8% strict full-case
Recall@10 on a frozen 90-case unseen holdout using SYSTEM-D-GUARD-BLEND, with
0.883 evidence-span recall and 0.978 document recall.

This document does not claim statistical significance of the reranker, does not
claim a closed-book win (EXP-NULL never ran), and does not invent a SYSTEM-A
holdout score. SYSTEM-A top-100 on holdout is candidate generation for D only.

---

## 1. Architecture

Two-stage retrieval. Stage 1/2 naming follows the frozen systems in
`src/rag_v1/systems.py`. SYSTEM-D does not replace SYSTEM-A; it reranks A's
candidate pool.

```text
frozen corpus snapshot
        ↓
cs_v1_control chunks (14,209)
        ↓
 SYSTEM-A-GLOBAL candidate generation
   BM25 (simple TSVECTOR, k1=1.2, b=0.75)
   + all-MiniLM-L6-v2 bi-encoder (max_seq=512, exact cosine, no ANN)
   fused by RRF (rrf_k=60, pool_per_retriever=50, fused top-100)
        ↓
 cross-encoder ms-marco-MiniLM-L6-v2 (ONNX fp32, max_length=512)
        ↓
 SYSTEM-D-GUARD-BLEND
   0.7 * minmax(CE) + 0.3 * minmax(SYSTEM-A fused RRF)
   within-query minmax; degenerate → 0.5
   tie-break: blend desc, then A rank asc, then chunk_id asc
        ↓
 top_k=10
```

SYSTEM-D is a **score blend**, not the EXP-016 clamp. Clamp
(`protect_a_rank_max=3`, `clamp_floor=10`) was variant C
(SYSTEM-D-GUARD-CLAMP) and is not in the release.

Ground truth remains above the chunk layer: `(version_id, section_path,
char_start, char_end)`. Chunk IDs are diagnostic.

---

## 2. Corpus provenance

Restored by CORPUS-002 from a verified recovery tarball. No live fetch.

| | |
| --- | --- |
| snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| manifest hash | `452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17` |
| documents | **202** (anthropic 139, openai 63) |
| chunks | **14,209** `cs_v1_control` (anthropic 12,028, openai 2,181) |
| archive | `/home/user/corpus-recovery-snap689e3363-20260831T2118Z.tar.gz` |
| archive sha256 | `4387ae1d5144109adbde3f11f1fcb339c3773480f356f9804909cf3ad2051b33` |
| package | 203 of 203 checksums |
| working copy | `recovery/CORPUS-002/working-corpus` |
| parser | `v1.0` |
| chunking | max 3500 / min 200 chars; config hash `bbc874e4f27a7e6826d5106e33510942fd76cb28cf55b5c3333f014e2a6fd916` |
| gold anchors | 174/174 spans across 150 cases byte-exact vs restored corpus |
| live docs fetched | **false** (holdout results and CORPUS-002 both) |

Embeddings used at holdout: model `emb_e7d4183fd6eb878ae2fdf080efb6861e`,
fingerprint `bd95feaeacf98559`, 14,209/14,209 rows complete.

---

## 3. Experiment timeline (EXP-000 → EVAL-HOLDOUT-001)

Early work measured retrieval on a 20-case development seed. Later work froze
systems, expanded GOLD to 150, split 20/40/90, and evaluated D once on holdout.

| id | what was tested | outcome that survived |
| --- | --- | --- |
| EXP-NULL | closed-book generation | **blocked** (no provider). Retrieval is uncalibrated vs what the model already knows. |
| EXP-000 | BM25 lexical | first real baseline after FAIL-0001 (empty retrieval) |
| EXP-001 | dense LSA substitute | lost to lexical; no transformer yet |
| EXP-002 | hybrid interleave | worse than lexical (dilution) |
| EXP-003 | RRF | only pool-100 was a genuine +2 on n=20 |
| EXP-005 / 005A / 005B | rechunking | bounded chunks did not rescue questions |
| EXP-006 | enrichment ablation | not promoted |
| EXP-007 | pretrained static dense + RRF | BM25+dense RRF 11/20; still no transformer |
| EXP-008 | chunk size × dense | interaction hypothesis rejected |
| EXP-009 | MiniLM transformer @512 | BM25 + MiniLM RRF **15/20** — this became SYSTEM-A |
| EXP-010 | encoder-window chunking | no reason to leave control chunks |
| EXP-011 | query-side retrieval | not promoted over A |
| EXP-012 | hierarchical doc-passage | routing precursor |
| EXP-013 | document routing | routing can drop the source document |
| EXP-014 | dedicated document-level (DOC-C) | +2 on n=20 development; CI includes 0 |
| EXP-014R | replication + GOLD expansion | systems **frozen**; expansion not yet at 150 |
| GOLD-001 | 150 human-verified cases | size target hit; coverage still skewed |
| CORPUS-001 / 002 | recover frozen corpus | CORPUS-002 **SUCCEEDED**; 202 docs / 14,209 chunks |
| EVAL-SPLIT-001 | 20 / 40 / 90 freeze | holdout lock `2026-08-31T22:30:29Z` |
| EVAL-VAL-001 | A vs B (DOC-C) on val n=40 | **REPLICATION_REJECTS_B** |
| EXP-015 | pure CE SYSTEM-C on dev n=20 | **RERANKER_REJECTED_AT_DEV** |
| EXP-016 | CE+A blend (D) vs clamp (C) | D frozen (`SYSTEM-D-GUARD.json`) |
| EVAL-VAL-002 | frozen D vs recorded A on val | **RERANKER_SUPPORTED** (not significant) |
| EVAL-HOLDOUT-001 | one-shot D on holdout n=90 | **79/90** strict Recall@10; `holdout_runs=1` |

### Rejected hypotheses (do not revive in v1)

**DOC-C / SYSTEM-B — `REPLICATION_REJECTS_B`** (EVAL-VAL-001). Development
15/20 vs 17/20 (+2 / 0) did not replicate. Validation: A **30/40**, B
**21/40**, 2 rescues / 11 regressions, net −9. Bootstrap 95% CI on delta
`[-0.375, -0.075]`, McNemar p=0.0225. **12** of B's failures were
`DOCUMENT_ROUTING_FAILURE`: Stage-1 routing discarded a document that global
A ranked successfully. SYSTEM-A-GLOBAL
(`9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38`) remains
the retrieval control. SYSTEM-B-DOC-C
(`304c350940b83733df6043ae3a8abdcbcde33d16950730127aa9f1f39494388b`) is a
measured, rejected alternative.

**Pure CE SYSTEM-C — `RERANKER_REJECTED_AT_DEV`** (EXP-015). On gold150-v1
development, A 19/20 vs C 18/20. One rescue (`GOLD-B005-11`) against two
regressions (`HA-22`, `HA-24`), net −1. HA-24 was an A-rank-1 gold span
demoted to CE rank 18 (generic Tools overview outranked the exact
`.tool_input` sentence). Gates applied once; no post-score retuning. Pure CE
was not frozen.

EXP-016 then rematerialized the same pool/CE logits and tested a blend. D
qualified on development (20/20, net +1, 0 rank-1 destructions) and was
frozen **before** validation load.

---

## 4. Final system configuration

Source of truth: `experiments/EVAL-HOLDOUT-001/SYSTEM-D-RELEASE.json`
(status `RELEASE_CANDIDATE_FROZEN`, frozen `2026-09-01T00:48:30Z` =
2026-08-31 20:48 ET). File sha256
`1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40`.

| field | value |
| --- | --- |
| system | SYSTEM-D-GUARD-BLEND |
| variant | D |
| **config hash** | **`d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a`** |
| source freeze | `experiments/EXP-016/SYSTEM-D-GUARD.json` (same hash) |
| SYSTEM-A hash | `9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38` |
| snapshot / chunk set | `snap_689e336380a054d8039dc35b2c09cd0a` / `cs_v1_control` |
| encoder | MiniLM-L6-v2 `emb_e7d4183fd6eb878ae2fdf080efb6861e` fp `bd95feaeacf98559` @512 |
| CE | `cross-encoder/ms-marco-MiniLM-L6-v2` rev `233902d25c440f23af6f7d6e94d2946bac0bee0a` |
| CE artifact sha256 | `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a` |
| candidate pool | 100 (50 per retriever, RRF k=60) |
| blend | **0.7 CE / 0.3 SYSTEM-A**, within-query minmax, degenerate 0.5 |
| guard | score_blend; `protect_a_rank_max=null`; D does not clamp |
| top_k | 10 |
| split | gold150-v1 holdout n=90, sha256 `756a3a9bc74ce3e2dd3a7924c4048984a0ae5e74237bc8053e18b6fec202d914` |

Holdout protocol (from EVAL-HOLDOUT-001 results): D scored exactly once;
`freeze_untouched=true`; `parameters_changed_after_any_case=false`;
`second_run=false`; `answer_generation_run=false`; `holdout_runs=1`.

---

## 5. Scorecard

### Validation (EVAL-VAL-002) — frozen D vs recorded A, n=40

Measurement of already-frozen D against recorded EVAL-VAL-001 SYSTEM-A.
Holdout was not loaded. D scored once.

| | SYSTEM-A (recorded) | SYSTEM-D-GUARD-BLEND |
| --- | ---: | ---: |
| strict Recall@10 | **30/40** (75.0%) | **33/40** (82.5%) |
| macro span recall@10 | 0.75 | 0.825 |
| document recall | 0.975 | 1.0 |
| MRR | 0.5283 | 0.5887 |
| regressions | — | **0** |
| rescues | — | 3 (`GOLD-B001-03`, `GOLD-B002-07`, `HA-44`) |
| net | — | +3 |
| rank-1 gold destructions | — | 0 |
| A≤3 gold spans out of D top-10 | — | 0 |

Paired bootstrap (seed `20250818`, 10,000 resamples) on strict 0/1 outcomes:
delta **0.075**, 95% CI **[0.0, 0.175]**. McNemar exact: discordant=3,
D-only=3, A-only=0, **p=0.25**.

Decision: **RERANKER_SUPPORTED** because D beats A on the primary with 0
regressions and 0 rank-1 destructions — **not** because the paired test is
significant. Do not read this as a significant win.

### Holdout (EVAL-HOLDOUT-001) — SYSTEM-D only, n=90, holdout_runs=1

First and only holdout run. Timestamp `2026-09-01T01:00:22Z`
(2026-08-31 21:00 ET). Config hash recomputed and matched freeze **before**
scoring. SYSTEM-A was not evaluated as a competing holdout system.

| metric | SYSTEM-D-GUARD-BLEND |
| --- | ---: |
| **strict full-case Recall@10** | **79/90 (87.8%)** |
| macro span recall@10 | **0.8833** (92/104 spans) |
| document recall | **0.9778** |
| MRR | **0.7055** |
| spans absent@10 / @20 / @50 / @100 | 12 / 9 / 8 / 7 |
| latency mean / median | **5640.3 ms** / 5589.3 ms |
| A candidate-gen mean | 492.8 ms |
| CE mean | 5146.8 ms |
| holdout_runs | **1** |

Candidate-pool coverage (not an A evaluation): **97/104** gold spans were
present in the SYSTEM-A top-100 used as D's candidate generator.

11 / 90 not fully recalled@10:
`GOLD-B001-02`, `GOLD-B001-09`, `GOLD-B002-06`, `GOLD-B003-04`,
`GOLD-B005-07`, `GOLD-B006-02`, `HA-20`, `HA-21`, `HA-37`, `HA-43`,
`HA-58`. Classified in `HOLDOUT-FAILURE-ANALYSIS-001.md`. No debugging from
these cases was used to change retrieval.

Provider: openai 51/57 (89.5%), anthropic 28/33 (84.8%). Exact-lookup
30/33 (90.9%) vs unlabeled-legacy 17/20 (85.0%). Single-span 67/76
(88.2%). Categories with n≤3 are individual observations, not rates.

---

## 6. Limitations (read before quoting the claim)

1. **n=40 validation is not significant.** CI `[0.0, 0.175]` includes 0;
   McNemar p=0.25. `RERANKER_SUPPORTED` is a net-positive mapping, not a
   significance claim.
2. **CE is ~11× latency.** Holdout mean: A candidate-gen 493 ms, CE 5,147 ms,
   D total 5,640 ms (~11.4× A retrieval). Development EXP-015: A 501 ms vs
   C 5,780 ms. This is a CPU ONNX fp32 cross-encoder over 100 passages.
3. **11 holdout misses remain.** 79/90 is not a solved retrieval problem.
   Six misses never entered the A pool; five were in-pool and ranked out of
   top 10, including an A-rank-1 span. See the failure analysis.
4. **GOLD is exact-lookup heavy.** Of 150 eligible cases, 58 (39%) are
   `exact_lookup`; 33 (22%) predate `reasoning_type`. Holdout inherits this:
   33/90 exact-lookup. An unweighted score is close to a score on the
   largest category. Genuine multi-hop is n=1 in the whole benchmark.
5. **HA drafts history.** HA-01–HA-60 entered as 60 drafts in the
   150-case review packet (Codex derivative reviewed by Grok;
   `ACCEPTED_PROTOCOL_DEVIATION` on the preregistered 10-case pilot). They
   were later owner-admitted and are `human_verified`. They are not the
   excluded 64-case packet. HA cases use derived `section_path` when the
   GOLD record has none stored (45 holdout spans).
6. **pgvector 0.8.6 vs recorded 0.6.0.** Restoration used
   `pgvector/pgvector:pg16` (PostgreSQL 16.15 vs recorded 16.13). Corpus
   identity still reproduced (snapshot, manifest, 202 docs, 14,209 chunks,
   174/174 gold anchors). Python package `pgvector==0.5.0` is the client,
   not the extension. Drift is recorded in EXP-015-environment.json.
7. **Local Windows checkout was stale** at `e65912a` and is not the work
   surface (EXP-015 interruption reconciliation). Authoritative engineering
   ran on the Linux box from archive `5082123`. Do not treat a stale
   Windows tree as the release tree.
8. **EXP-NULL never ran.** Nothing here shows retrieval beats closed-book
   generation.
9. **No SYSTEM-A holdout number.** Inventing one would violate the
   one-shot D-only protocol. A ranks quoted in the failure analysis are
   candidate-pool ranks stored during D's run, not an A evaluation.
10. **Single holdout run.** `holdout_runs=1` is the design. A second run
    would not be an independent confirmation.

---

## 7. What v1 does not change from here

SYSTEM-D-GUARD-BLEND is the v1 retrieval release candidate. No further
retrieval changes in v1: no weight search, no clamp swap, no encoder
change, no new passages, no SYSTEM-B revival, no pure-CE revival. See
`EVAL-HOLDOUT-001-decision.md`.

---

## Files

- `experiments/EVAL-HOLDOUT-001/SYSTEM-D-RELEASE.json`
- `experiments/EVAL-HOLDOUT-001/EVAL-HOLDOUT-001-results.json`
- `experiments/EVAL-HOLDOUT-001/EVAL-HOLDOUT-001-per-case.json`
- `experiments/EVAL-HOLDOUT-001/EVAL-HOLDOUT-001-report.md`
- `experiments/EVAL-HOLDOUT-001/HOLDOUT-FAILURE-ANALYSIS-001.md`
- `experiments/EVAL-HOLDOUT-001/EVAL-HOLDOUT-001-decision.md`
- `experiments/EVAL-VAL-002/EVAL-VAL-002-report.md`
- `experiments/EVAL-VAL-001/EVAL-VAL-001-decision.md`
- `experiments/EXP-015/RERANKER_REJECTED-at-dev.json`
- `experiments/CORPUS-002/CORPUS-002-restoration-report.md`
