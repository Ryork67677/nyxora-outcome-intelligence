# EVAL-HOLDOUT-001 decision

**Holdout complete.** SYSTEM-D-GUARD-BLEND is the Production RAG v1
retrieval release candidate. **No further retrieval changes in v1.**

Recorded `2026-09-01T01:00:22Z` (2026-08-31 21:00 ET) after the one-shot
holdout of the already-frozen release
(`experiments/EVAL-HOLDOUT-001/SYSTEM-D-RELEASE.json`, config hash
`d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a`).

## Measurement this decision rests on

| | |
| --- | --- |
| split | gold150-v1 holdout, n=90, previously unseen |
| `holdout_runs` | **1** (first and only) |
| system | SYSTEM-D-GUARD-BLEND (not retuned, not reclamped) |
| strict Recall@10 | **79/90 (87.8%)** |
| span recall / doc recall / MRR | 0.8833 / 0.9778 / 0.7055 |
| latency mean | 5640.3 ms |
| prior validation | D 33/40 vs A 30/40, 0 regressions, CI [0.0, 0.175], p=0.25, `RERANKER_SUPPORTED` |

## What is frozen

- Retrieval configuration, blend weights (0.7 / 0.3), candidate pool 100,
  encoder, cross-encoder revision, chunk set `cs_v1_control`, snapshot
  `snap_689e336380a054d8039dc35b2c09cd0a`.
- SYSTEM-A remains the candidate generator, not a competing holdout system.
- SYSTEM-B (`REPLICATION_REJECTS_B`) and pure CE SYSTEM-C
  (`RERANKER_REJECTED_AT_DEV`) stay rejected.
- Holdout membership and this one-shot result stay as recorded. Misses are
  classified in `HOLDOUT-FAILURE-ANALYSIS-001.md` for understanding only.

## What this is not

- Not a second holdout run.
- Not a weight search, clamp swap, or encoder change.
- Not a SYSTEM-A holdout evaluation.
- Not a claim that the validation delta is statistically significant.
- Not permission to debug retrieval from the 11 holdout misses.

## Rule for v1

After this decision, no retrieval changes in v1. Answer-generation eval,
latency engineering, or a v2 proposal may proceed without moving D's
ranked list.
