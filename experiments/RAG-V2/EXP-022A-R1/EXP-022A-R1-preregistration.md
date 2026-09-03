# EXP-022A-R1 — CONTROLLED CE REPLAY + SYSTEM-J RECOGNIZABILITY

**PREREGISTRATION. HASHED BEFORE ANY RAW CE LOGITS ARE GENERATED.**

Written 2026-09-03T05:26:25Z UTC (2026-09-03T01:26:25-04:00 ET). ChatGPT-authorized EXP-022A-R1 after EXP-022A STOPPED_MISSING_STORED_H_CE_LOGITS. Assignment: `/workspace/NATQ-001-post/EXP-022A-R1-ASSIGNMENT.md`. ChatGPT source: `/workspace/chatgpt-after-exp-022a.txt`.

Machine-readable twin: `experiments/RAG-V2/EXP-022A-R1/EXP-022A-R1-preregistration.json` sha256 `29be7cfc9f22c2e182016baa81f1e8bca5a9dfeae6e5e518594cab24f4d6ff48`.

NATQ-001 validation n=40 is **DEVELOPMENT / MODEL-SELECTION DATA**. This is a **development replay / diagnostic**, not independent validation, not EVAL-NATQ-VAL-002, not a second validation claim, not a release evaluation, not a holdout evaluation. Locked holdout n=60 remains unseen. Do not open `evals/splits/natq-001/holdout.json` or `evals/splits/gold150-v1/holdout.json`.

Original EXP-022A is **CLOSED** as `STOPPED_MISSING_STORED_H_CE_LOGITS`. It produced no CE scoring and no mechanism result. `EXP-022A_CE_RECOGNIZABILITY_SUPPORTED` remains **unevaluated**. Do **not** modify or rewrite EXP-022A.

One controlled CE replay. Score frozen CE once over exact stored SYSTEM-J candidate memberships (which include H). Persist every raw CE logit. Then CE-only rank ARM H (H subset) vs ARM J (full J). Ranking: raw CE logit DESC, canonical chunk_id ASC.

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
| frozen CE revision | `233902d25c440f23af6f7d6e94d2946bac0bee0a` |

Exact stored membership counts (STOP if mismatch): H pairs **4753**, J pairs **7485**, J-only **2732**. H_IDS ⊆ J_IDS every query.

Closed ceilings (not modified): SYSTEM-H 34/40 cases, 46/53 spans, mean pool 118.83; SYSTEM-J 37/40, 50/53, 187.12; SYSTEM-K 35/40, 48/53, 146.78 (K not tested). EXP-021A_SUPPORTED=true. EXP-021B_SUPPORTED=false. EXP-022A closed unscored.

## Question

Are the additional candidates recovered by SYSTEM-J recognizable as relevant by the frozen cross-encoder when both arms are ranked CE-only from **one shared CE pass** over exact stored J memberships?

This is a **reranker recognizability diagnostic / development replay**, not a release architecture.

## Ranking (both arms)

raw frozen CE logit DESC, then deterministic canonical chunk_id ASC.

Do **not** combine CE with BM25, projection scores, a_norm, retrieval_norm, MMR, section/diversity bonuses, or the SYSTEM-H 0.7/0.3 blend.

## ONE CE call per query

For each of 40 queries, ONE CE call on the exact J_IDS texts (stored order), batch_size=16, D1 bucketing (`CrossEncoderReranker(pad='batch', bucket_by_length=True)`, fast=False, threads=4, max_length=512, longest_first). Do **not** score H and extras as two separate CE passes (that would change length-bucket batches). Persist every pair immediately to `logs/EXP-022A-R1-raw-ce-logits.jsonl`.

## Persistence gate (before aggregate metrics)

Verify exactly 7485 unique (case_id, chunk_id) J pairs, 4753 H-member, 2732 J-only, zero missing, zero duplicate disagreements, every H and every J candidate has one logit. Hash the completed jsonl. If this gate fails: **STOP WITHOUT computing mechanism metrics**.

## PRIMARY

strict full-case Recall@10: H CE-only vs J CE-only. Report numerator/40.

## SECONDARY

evidence-span Recall@10 numerator/53; MRR (summarise definition: mean 1/rank over all gold spans, 0 if rank missing); document Recall@10; multi-span strict Recall@10 and multi-span span Recall@10 (same 12-case definition as EXP-021A: n_gold_spans>1 or tag multi_span); OpenAI/Anthropic strict and span.

## PAIRED

J rescues over H, J regressions vs H, both pass, both fail. McNemar exact p diagnostic (n01=J success H fail, n10=J fail H success). No significance claim required.

## GATE (do not change after seeing results)

`EXP-022A-R1_CE_RECOGNIZABILITY_SUPPORTED` iff ALL:

1. J CE-only strict R@10 improves over H CE-only by >= 2 cases
2. J CE-only span R@10 improves over H CE-only by >= 2 spans
3. J strict regressions vs H <= 1
4. no integrity/provenance failure

Preserve the original unobserved EXP-022A gate. Mechanism gate, not release gate.

## Diagnostics (after aggregates only)

Four SYSTEM-J recovered spans: NATQ-C-004 s0, NATQ-C-005 s1, NATQ-C-044 s0, NATQ-C-044 s1. For each: raw CE logit, J CE-only rank, whether top10, n higher-ranked same version_id, n higher-ranked same section_path. Diagnostic only. No named-case rules.

Multi-span: required span count; n in J pool; n in J CE-only top10; CE-only ranks of every in-pool gold span; unique version_ids / section_paths in top10; redundancy count (top10 minus unique version; top10 minus unique section).

## Latency

total CE wall time; mean/median per-query CE time; H-pair count; J-only pair count; full J-pair count. No cross-host architecture claim.

## Harness fix (NON-SCORING follow-up)

EVAL-NATQ-VAL-001 did not persist full-pool raw CE logits. Future development/validation reranker runs must persist candidate membership, raw logits, query/candidate association, model fingerprint, and input/config fingerprint. Do not modify historical EVAL-NATQ-VAL-001 artifacts. Do not fabricate historical logits.

## Environment

Record current environment. Known drift remains: PostgreSQL 16.15 / pgvector 0.8.6 vs historical PostgreSQL 16.13 / pgvector 0.6.0. CE replay uses stored membership so should not depend on pgvector; still record drift.

## Holdout

Before and after: NATQ access log 0 bytes sha `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. V1 log 235 bytes sha `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`. Neither holdout.json may be opened.

## STOP

Return to coordinator ChatGPT. Do not build a coverage-aware selector. Do not test SYSTEM-K. Do not modify W/L/P. Do not change CE. Do not open holdout.
