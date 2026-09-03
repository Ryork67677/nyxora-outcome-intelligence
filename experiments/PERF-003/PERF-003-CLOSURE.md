# PERF-003 closure

Closed 2026-09-01T05:51:33Z UTC (2026-09-01T01:51:33-04:00 ET). ChatGPT accepted **PERF-003_SUPPORTED** ~01:48 ET 2026-09-01. SCORE-PRESERVING PERFORMANCE ENGINEERING ONLY. Did not re-run PERF-003. No holdout. No validation. No release freeze. SYSTEM-G / SYSTEM-G-CE-D1 / SYSTEM-F / SYSTEM-E / SYSTEM-D / `cs_v1_control` / projection set not overwritten.

## Status labels

| label | value |
| --- | --- |
| PERF-003 | **PERF-003_SUPPORTED** |
| ChatGPT accepted | **~01:48 ET 2026-09-01** |
| SYSTEM-G-PROJECTION-PRIOR | **not overwritten** |
| SYSTEM-G-CE-D1 | **not overwritten** |
| RELEASE | **NOT_FROZEN** |
| VALIDATION | **NOT_RUN** |
| HOLDOUT | **UNTOUCHED** |

PERF-003 = **PERF-003_SUPPORTED** (preregistered rule: complete equivalence gate passes AND measured CE latency improves on the same host). Engineering-performance decision only. Not a quality-system promotion.

## Protocol values (corroborated from PERF-003-report.md / PERF-003-results.json)

| item | value |
| --- | --- |
| Prereg SHA256 | `dc01713eafc56347a9eba0711d0947f13fccbc8ba784dfa034e22280ec23c880` |
| SYSTEM-G-PROJECTION-PRIOR config_hash | `563a7b790564fa1efb96257e988c4b1ccfab45146825d2a366b2fee0ca5d5790` |
| SYSTEM-G-CE-D1 config_hash | `6d108568f3131bad87d8617f5c2fb88ea14428e397d59ff54ff8e11cc4647b7d` |
| SYSTEM-G-CE-D1 file SHA256 (protocol) | `cf0c985c5f7738e7fc5422039fd6940621d8dcd8f91de41abe3784ac53a6a7ec` |
| SYSTEM-G-CE-D1 file SHA256 (`sha256sum` this close) | `cf0c985c5f7738e7fc5422039fd6940621d8dcd8f91de41abe3784ac53a6a7ec` |
| file SHA match | **True** |
| Equivalence | **6205/6205** raw CE logits bitwise identical, `max_abs_diff=0` |
| cand R@100 | 46/50 |
| strict R@10 | 41/50 |
| span | 0.82 |
| MRR | 0.6009 |
| document recall | 0.90 |

## Timing (this host only — do NOT present as cross-host)

CPU: Intel Xeon 8 cores. ORT 1.29.0 CPUExecutionProvider intra_op=4 inter_op=1.

| | old | D1 |
| --- | ---: | ---: |
| CE mean | 6791.2 ms | 2117.6 ms |
| SYSTEM-G total | 7802.6 ms | 3129.0 ms |

CE speedup **3.207x**. Corroboration from results.json: old CE 6791.1651 ms, D1 CE 2117.5741 ms, speedup 3.207, totals 7802.5651 / 3128.9741 ms.

## Follow-on

Development architecture freeze: `SYSTEM-H-V2-DEV-CANDIDATE` (identity freeze of the PERF-003 D1 V2 path; no ranking/quality change). **V2-DEVSET-001 is CLOSED for architecture changes.** Do not evaluate SYSTEM-H yet. **NATQ-001 is next.** Do not open V1 holdout.

`evals/splits/gold150-v1/holdout.json` was not opened.
