# EVAL-VAL-002 — validation of frozen SYSTEM-D-GUARD-BLEND

## RERANKER_SUPPORTED

D strictly beats recorded A on primary (33/40 vs 30/40, net +3) without catastrophic exact-match destruction (rank-1 destructions=0, A≤3-out-of-10=0).

This is a measurement of the already-frozen SYSTEM-D against recorded EVAL-VAL-001 SYSTEM-A. SYSTEM-D was not modified. Holdout was not loaded.

## Setup

- Split: `evals/splits/gold150-v1/validation.json` n=40. Projection `validation.jsonl`.
- SYSTEM-A: recorded EVAL-VAL-001, **30/40** strict Recall@10, macro span recall **0.75**, doc recall **0.975**, MRR **0.5283**. Not rerun as an evaluation. A top-100 was retrieved only as D candidate generation.
- SYSTEM-D: freeze `experiments/EXP-016/SYSTEM-D-GUARD.json`, implementation SYSTEM-D-GUARD-BLEND, config hash `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a` verified **before scoring**.
- Weights: 0.7 minmax CE + 0.3 minmax SYSTEM-A fused RRF, pool 100, tie-break blend desc / A rank / chunk_id.
- CE: `cross-encoder/ms-marco-MiniLM-L6-v2` rev `233902d25c440f23af6f7d6e94d2946bac0bee0a`, onnx sha256 `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`.
- Encoder fingerprint: `bd95feaeacf98559`.
- D scored **exactly once** on the 40 cases.
- Holdout access log: **0 bytes**. holdout_runs = **0**.

## Named-case audit (HA-22, HA-24, GOLD-B005-11)

These three were the EXP-015/016 development traces. They are **not** in the validation set.

- **HA-22**: development-only; not in validation; not looked up in holdout
- **HA-24**: development-only; not in validation; not looked up in holdout
- **GOLD-B005-11**: development-only; not in validation; not looked up in holdout

They were not looked up in holdout.

## Primary endpoint — strict full-case recall@10

| system | fully recalled | of | percentage |
| --- | ---: | ---: | ---: |
| SYSTEM-A-GLOBAL (recorded EVAL-VAL-001) | **30** | 40 | 75.0% |
| SYSTEM-D-GUARD-BLEND | **33** | 40 | 82.5% |
| difference (D−A) | +3 | | +7.5 pp |

## Secondary metrics

| | SYSTEM-A (recorded) | SYSTEM-D |
| --- | ---: | ---: |
| macro span recall@10 | 0.75 | 0.825 |
| spans retrieved | 33/47 | 36/47 |
| document recall | 0.975 | 1.0 |
| MRR | 0.5283 | 0.5887 |
| spans absent@10 | 14 | 11 |
| latency mean (ms) | (recorded A retrieval ~653) | 5680.2 |

Rematerialized A gold-span rank mismatches vs recorded: **0**. Rematerialized A strict (candidate-gen only, not a new eval): 30/40.

## Paired analysis vs recorded A

- **rescues (3)**: ['GOLD-B001-03', 'GOLD-B002-07', 'HA-44']
- **regressions (0)**: none
- both pass: 30, both fail: 7
- net: **+3**

### Statistics

Paired bootstrap over 40 questions, 10000 resamples, seed `20250818`, on the 40 paired strict 0/1 outcomes (D−A).

| quantity | point estimate | 95% CI |
| --- | ---: | --- |
| strict fully-recalled delta per case | 0.075 | [0.0, 0.175] |
| macro span-recall delta | 0.075 | [0.0, 0.175] |

McNemar exact (discordant strict outcomes): discordant=3, D-only=3, A-only=0, p=0.25.

Rank-1 gold destructions (A rank 1 out of D top 10): 0.
A-rank≤3 gold spans out of D top 10: 0.

## Rescues

| case | A ranks (stored) | D ranks | CE score(s) | id-overlap | guard triggered | all spans in D@10 | class |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GOLD-B001-03` | [11] | [8] | ['5.6233'] | [True] | False (blend) | True | OTHER |
| `GOLD-B002-07` | [24] | [7] | ['3.3295'] | [True] | False (blend) | True | OTHER |
| `HA-44` | [14] | [3] | ['3.4522'] | [True] | False (blend) | True | OTHER |

## Regressions

(none)

### Classification notes

Exact-match guard (EXP-016 clamp) did **not** trigger on any case: SYSTEM-D is the frozen score blend. Identifier overlap is diagnostic only.

- `GOLD-B001-03` RESCUE: **OTHER** — A 11→D 8 (CE 5.6233); identifier overlap `claude-fable-5`, `claude-mythos-5`, `thinking`. Blend lifted an A-miss into top 10. Not a failure-mode class.
- `GOLD-B002-07` RESCUE: **OTHER** — A 24→D 7 (CE 3.3295); identifier overlap `pause_after_compaction`. Same pattern.
- `HA-44` RESCUE: **OTHER** — A 14→D 3 (CE 3.4522); identifier overlap `RunConfig.handoff_input_filter`, `input_filter`. Same pattern.
- No regressions, so EXACT_IDENTIFIER_DEMOTION / VERSION_CONFUSION / SEMANTIC_MISREAD / TRUNCATION were not assigned.

## Decision

**RERANKER_SUPPORTED**

D strictly beats recorded A on primary (33/40 vs 30/40, net +3) without catastrophic exact-match destruction (rank-1 destructions=0, A≤3-out-of-10=0).

The 95% CI on the strict delta is [0.0, 0.175] and McNemar p=0.25. The label is **RERANKER_SUPPORTED** because D beats A on the primary (net +3 strict cases, 0 regressions, 0 rank-1 destructions), not because the paired test is significant. Do not read this as a significant win.

Holdout was not run. Stop after this report.

## Files

- `experiments/EVAL-VAL-002/EVAL-VAL-002-results.json`
- `experiments/EVAL-VAL-002/EVAL-VAL-002-paired-analysis.json`
- `experiments/EVAL-VAL-002/EVAL-VAL-002-regression-analysis.json`
- `experiments/EVAL-VAL-002/EVAL-VAL-002-environment.json`
- `experiments/EVAL-VAL-002/EVAL-VAL-002-report.md`
- `experiments/EXP-016/EXP-016-validation-results.json`
