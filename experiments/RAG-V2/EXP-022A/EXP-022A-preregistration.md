# EXP-022A — SYSTEM-J CE RECOGNIZABILITY DIAGNOSTIC

**PREREGISTRATION. HASHED BEFORE COMPUTING ANY AGGREGATE J CE-ONLY METRICS.**

Written 2026-09-03T05:13:27Z UTC (2026-09-03T01:13:27-04:00 ET). ChatGPT-authorized EXP-022A after EXP-021B_SUPPORTED=false. Assignment: `/workspace/NATQ-001-post/EXP-022A-ASSIGNMENT.md`. ChatGPT source: `/workspace/chatgpt-after-exp-021b.txt`.

Machine-readable twin: `experiments/RAG-V2/EXP-022A/EXP-022A-preregistration.json` sha256 `ad7fba5a38d6fda06fdb42a94f0b78fdce008cfe978b1743224028bb2fd8e64b`.

NATQ-001 validation n=40 is **DEVELOPMENT / MODEL-SELECTION DATA**. This is not independent validation. Locked holdout n=60 remains unseen. Do not open `evals/splits/natq-001/holdout.json` or `evals/splits/gold150-v1/holdout.json`.

One diagnostic. Two CE-only ranking arms. Do not invent a retrieval prior for W20 extras. Do not run SYSTEM-K. Do not run coverage-aware selection. Do not alter the SYSTEM-H 0.7/0.3 blend. Do not rerun CE on SYSTEM-H candidates. Do not create a new SYSTEM identity unless scoring actually runs.

---

## Frozen identities (not modified)

| | |
| --- | --- |
| SYSTEM-H-V2-DEV-CANDIDATE config_hash | `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` |
| SYSTEM-H file SHA256 | `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475` |
| SYSTEM-J-LOCAL-W20-UNION config_hash | `b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787` |
| SYSTEM-J file SHA256 | `70acac77f33dbe1f7fc0f2e9b81f8a995c7fd0e9f47bab662f03f12cdecc0fdd` |
| SYSTEM-K-W20-SECTION-COMPRESS config_hash (not tested) | `eef589c085ea7e88fdc729d83021b311e2927310fc6368b54a87f374859bdec8` |
| SYSTEM-K file SHA256 | `20d967e2f56fed88f617d1c18474abc86b9f984f32a30cc195f42d6fef03ad7e` |
| snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| chunk set | `cs_v1_control` |
| validation.jsonl | sha256 `a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6` n=40 |
| stored pools | `experiments/RAG-V2/EXP-021A/logs/EXP-021A-pools.jsonl` |
| frozen CE ONNX sha | `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a` |

Closed ceilings (not modified): SYSTEM-H 34/40 cases, 46/53 spans, mean pool 118.83; SYSTEM-J 37/40, 50/53, 187.12; SYSTEM-K 35/40, 48/53, 146.78. EXP-021A_SUPPORTED=true. EXP-021B_SUPPORTED=false.

## Question

Are the additional candidates recovered by SYSTEM-J recognizable as relevant by the frozen cross-encoder?

This is a **reranker recognizability diagnostic**, not a release architecture.

## Ranking (both arms)

raw frozen CE logit DESC, then deterministic canonical chunk_id ASC.

Do **not** combine CE with BM25, projection scores, a_norm, retrieval_norm, or the SYSTEM-H 0.7/0.3 blend. Raw CE logit is sufficient because per-query CE normalization is monotonic for ranking.

## ARM H — stored control

Reconstruct CE-only rankings over the exact SYSTEM-H candidate pool (`system_h_union_ids`, 4753 total across 40 queries) using raw CE logits **already stored** from EVAL-NATQ-VAL-001.

Do **not** rerun CE for SYSTEM-H candidates.

## ARM J — additive CE

`J_EXTRAS = SYSTEM-J set − SYSTEM-H set` per query (stored `added_w20` / EXP-021A-pools). Run the exact frozen CE (`CrossEncoderReranker(pad='batch', bucket_by_length=True)`, fast=False, threads=4, batch_size=16, max_length=512, longest_first, PERF-003 D1) **only** on J_EXTRAS texts. Combine stored H logits + new extra logits. CE-only rank the J pool. Do not score any candidate not in SYSTEM-J.

## HARD STOP (verify before scoring J)

Verify ALL of:

1. every SYSTEM-H candidate chunk_id has a stored RAW CE logit for that query
2. query/candidate association intact
3. CE model fingerprint matches frozen reranker sha `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`
4. no missing or duplicate logits

Search stored artifacts thoroughly (EVAL pools jsonl, EVAL REPORT per_case, any jsonl/json under EVAL-NATQ-VAL-001 and /workspace with ce_score/ce_logit for NATQ validation). `blend_score` is **not** a raw CE logit.

If stored full-pool raw H CE logits are missing or incomplete: **STOP**. Do not silently rerun H. Do not score J extras with CE. Write the STOP report. That is a successful completion of this task.

## PRIMARY

strict full-case Recall@10: H CE-only vs J CE-only. Report numerator/40.

## SECONDARY

evidence-span Recall@10; MRR (mean of 1/rank of first gold span, 0 if none); document Recall@10; multi-span strict Recall@10 and multi-span span Recall@10 (same 12-case definition as EXP-021A: n_gold_spans>1 or tag multi_span); OpenAI/Anthropic strict and span; added W20 candidate CE-rank distribution; CE latency for J_EXTRAS only; total newly scored pairs. Report raw numerators/denominators.

## PAIRED

Per case: H PASS/FAIL and J PASS/FAIL. Aggregate: J rescues over H, J regressions vs H, both pass, both fail. McNemar exact p diagnostic (n01=J success H fail, n10=J fail H success). No significance claim required.

## GATE (do not change after seeing results)

`EXP-022A_CE_RECOGNIZABILITY_SUPPORTED` iff ALL:

1. J CE-only strict R@10 improves over H CE-only by >= 2 cases
2. J CE-only span R@10 improves over H CE-only by >= 2 spans
3. J strict regressions vs H <= 1
4. no integrity/provenance failure

Mechanism gate, not release gate. Not evaluated if STOPPED_MISSING_STORED_H_CE_LOGITS.

## Diagnostics (after aggregates only)

Four SYSTEM-J recovered spans: NATQ-C-004 s0, NATQ-C-005 s1, NATQ-C-044 s0, NATQ-C-044 s1. For each: raw CE logit, CE-only rank in J, whether top10, n higher-ranked same version_id, n higher-ranked same section_path. Diagnostic only. No named-case rules.

Multi-span: required span count; spans in J pool; spans in J CE-only top10; CE-only rank of each in-pool gold span; unique version_ids / section_paths in J CE-only top10; redundant top10 count by version_id/section_path.

## Latency

Measured: n J_EXTRAS CE pairs, CE wall time for new pairs. Estimated: complete J CE workload (H stored pairs + extras; do not run H CE), mean/median estimated per-query J CE cost. Distinguish measured incremental vs estimated full-pool. No cross-machine architecture claim.

## Environment

Record current environment. Known drift remains: PostgreSQL 16.15 / pgvector 0.8.6 vs historical PostgreSQL 16.13 / pgvector 0.6.0.

## Holdout

Before and after: NATQ access log 0 bytes sha `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. V1 log 235 bytes sha `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`. Neither holdout.json may be opened.

## STOP

Return to coordinator ChatGPT. Do not run a coverage-aware selector. Do not run another compression scheme. Do not alter scoring. Do not silently rerun H CE.
