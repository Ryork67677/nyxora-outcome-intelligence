# EXP-015 interruption reconciliation

**STATE A — NOT STARTED.**

The local Windows checkout was stale at `e65912a`. It is not the work surface. The authoritative ref is `origin/claude/rag-v1-build-experiments-5yngul` at `5082123e8c406ab162349d23003b1173afd697ac` (`5082123`). This session unpacks that git archive on the Linux box and does not clone GitHub or touch the user worktree.

## What 5082123 contains

- No `experiments/EXP-015/` directory.
- No SYSTEM-C files. `src/rag_v1/systems.py` defines SYSTEM-A-GLOBAL and SYSTEM-B-DOC-C only.

EXP-015 therefore starts here, from a clean ref, not from a resumed in-progress run.

## Holdout lock

| | |
| --- | --- |
| frozen | **True** (`2026-08-31T22:30:29Z`) |
| holdout_count | **90** |
| lock sha256 | `756a3a9bc74ce3e2dd3a7924c4048984a0ae5e74237bc8053e18b6fec202d914` |
| matches EVAL-SPLIT-001 split_artifact_sha256.holdout | **True** |
| access log | `evals/splits/gold150-v1/holdout-access.log.jsonl` **0 bytes** |
| holdout_runs | **0** |

Holdout membership is frozen. This session does not load holdout question text, enumerate holdout IDs, or run holdout.

## Hashes intact

| object | value |
| --- | --- |
| SYSTEM-A-GLOBAL | `9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38` |
| SYSTEM-B-DOC-C | `304c350940b83733df6043ae3a8abdcbcde33d16950730127aa9f1f39494388b` |
| snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| manifest hash | `452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17` |
| reranker / cross_encoder | `None` / `None` |
| rrf_k / pool_per_retriever / top_k | 60 / 50 / 10 |

Recomputed `FROZEN_HASHES` from `systems.py` at this unpack match the recorded EVAL-VAL-001 / handoff values.
