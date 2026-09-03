# EVAL-NATQ-VAL-001 — SYSTEM-H NATURAL-QUERY VALIDATION

**PREREGISTRATION. HASHED BEFORE ANY SYSTEM-H RETRIEVAL ON NATQ VALIDATION.**

Written 2026-09-03T03:53:30Z UTC (2026-09-02T23:53:30-04:00 ET). ChatGPT-authorized EVAL-NATQ-VAL-001. Assignment: `/workspace/NATQ-001-post/EVAL-NATQ-VAL-001-ASSIGNMENT.md`.

Machine-readable twin: `experiments/RAG-V2/EVAL-NATQ-VAL-001/EVAL-NATQ-VAL-001-preregistration.json` sha256 `3d91f14acfa2cbc1c0368781ac0dd4783cc331677e6d0ecc425ed07b1abd1dd3`.

This is **exactly one** validation evaluation of frozen **SYSTEM-H-V2-DEV-CANDIDATE** against **NATQ-001 validation n=40**. Not a retune. Not a second run. Not a holdout. Not a release freeze. Do not modify SYSTEM-H. Do not overwrite SYSTEM-G or SYSTEM-G-CE-D1.

---

## Frozen system (identity only; not modified)

| | |
| --- | --- |
| name | `SYSTEM-H-V2-DEV-CANDIDATE` |
| config_hash | `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` |
| file SHA256 | `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475` |
| DEVELOPMENT_ARCHITECTURE_FROZEN | true |
| RELEASE_FROZEN | false |
| VALIDATION_RUN (before this experiment) | false |
| NEW_HOLDOUT_RUN | false |

Pipeline (reuse existing EXP-017 / EXP-019A / PERF-003 / EXP-018B code; do not rewrite architecture):

- global retrieval (SYSTEM-A BM25 + dense RRF, A pool 100)
- E-L10 within-document additive retrieval (`L=10`)
- projection lane `ps_v2_ovl_win448_s224`, `P=20` projection extras
- projection-aware retrieval prior (EXP-019A): E-L10 `a_norm` kept exactly; projection-only `retrieval_norm` = minmax(projection-RRF) over the P extras (degenerate 0.5); combined list not re-minmaxed
- frozen CE via `make_v2_system_g_d1_reranker()` = `CrossEncoderReranker(pad='batch', bucket_by_length=True)` (PERF-003 D1)
- blend **0.7 CE / 0.3 retrieval**
- PERF-003 D1 dynamic batch padding, `batch_size=16`, threads=4 / intra_op=4 / inter_op=1
- tie-break: blend DESC, E-L10 merge-RRF rank (projection-only `a_rank=10**9`), chunk_id ASC
- no query rewrite; no answer generation

## Frozen NATQ-001 (validation only)

| artifact | sha256 |
| --- | --- |
| validation.jsonl n=40 | `a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6` |
| gold 100 (recorded; file not loaded for this run) | `332384a4d59b8f21fb882247b8d35c0b69a188ae2d936458132c497d7333453e` |
| split.json | `332b833765c5c5cfff8ece26bff74bce74476c2ab6907353bf66a095bde6525b` |
| holdout.json (recorded; **file not opened**) | `6a7cf781c7538106605e8c85607405cd3dee2db37fdbb556aaadc913b3141dd3` |
| holdout.lock.json | `03e0d5749e61e73e6b9582109a74a4a9672610b7bf794daf25f46999e5ad40b2` |
| snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |

Load **ONLY** `evals/splits/natq-001/validation.jsonl`. n must equal 40.

NATQ holdout-access log **before** run: 0 bytes, sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

Historical V1 holdout-access log: 235 bytes, sha256 `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`.

## PRIMARY

strict full-case Recall@10: a case succeeds iff every gold evidence span overlaps a top-10 SYSTEM-H chunk (EXP-017 `fully_recalled`). Report n/40.

## SECONDARY

- candidate gold-span Recall@100: every gold span present in the SYSTEM-H candidate union; n/40
- evidence-span Recall@10: micro (spans in top-10) / (total gold spans); also macro; gate uses micro ≥ 0.80
- document Recall@10: every gold `version_id` appears in top-10 chunks; n/40
- MRR (EXP-018 span MRR)
- mean/median latency and per-stage if available
- provider breakdown (OpenAI vs Anthropic)
- major coverage/stress-tag breakdown
- exact-identifier / multi-span / natural-paraphrase subsets

Report raw numerators and denominators.

## ENGINEERING QUALIFICATION GATE

`VALIDATION_SUPPORTED` iff **ALL** are true (do not change after seeing results):

1. strict full-case Recall@10 ≥ 32/40
2. candidate gold-span Recall@100 ≥ 36/40
3. evidence-span Recall@10 ≥ 0.80
4. document Recall@10 ≥ 38/40
5. no benchmark-integrity failure
6. NATQ holdout remains untouched

This is an engineering advancement gate, **not** a claim of statistical significance.

Also report a 95% Clopper-Pearson binomial CI for strict Recall@10 as diagnostic context only.

## Failure analysis (no retune)

Classify every strict failure: candidate-generation vs ranking vs document-discovery vs evidence-granularity vs gold ambiguity (flag only; do not alter gold). Do not use failure identities to make a second run.

## STOP

Stop after EVAL-NATQ-VAL-001. Do **not** run holdout whether the gate passes or fails. No second validation run. No retune. No release freeze.
