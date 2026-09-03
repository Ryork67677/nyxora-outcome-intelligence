# RAG-V1-CLOSURE-CHECKPOINT

Closure verification for Production RAG v1. Written 2026-09-01T01:12:54Z
(2026-08-31 21:12 ET) on the box work tree
`/workspace/rag-v1/repo/production-rag-v1`.

This checkpoint is documentation only. No retrieval, holdout, validation, or
embeddings were run. SYSTEM-D freeze JSON, weights, and CE artifacts were not
modified. No git commit.

**Overall: PASS** (7/7 verification items).

---

## Verification table

| # | item | result | size (bytes) | sha256 |
| --- | --- | --- | ---: | --- |
| 1 | `experiments/EVAL-HOLDOUT-001/PRODUCTION-RAG-V1-FINAL-REPORT.md` | **PASS** exists | 13364 | `32744c0a7e693936ac4b766441f0542d7fe920c4de117eacdc53776c8e5592f0` |
| 2 | `docs/reports/PRODUCTION-RAG-V1-FINAL-REPORT.md` | **PASS** exists; byte-identical to item 1 (`cmp` equal) | 13364 | `32744c0a7e693936ac4b766441f0542d7fe920c4de117eacdc53776c8e5592f0` |
| 3 | `experiments/EVAL-HOLDOUT-001/HOLDOUT-FAILURE-ANALYSIS-001.md` | **PASS** exists | 11731 | `1e7a4b79bcb5dc27163dec01a8b941d524eeb533a74211ce62e31ab15667c6d8` |
| 4 | `experiments/EVAL-HOLDOUT-001/EVAL-HOLDOUT-001-decision.md` | **PASS** exists | 1857 | `9c712bbf718c7a9b194c3d6c9561eef9a776f08207134cb395a80ef448621546` |
| 5 | `SYSTEM-D-RELEASE.json` + sidecar | **PASS** exists; sidecar hash matches file bytes | json 6062 / sidecar 88 | json `1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40` |
| 6 | `experiments/EXP-016/SYSTEM-D-GUARD.json` | **PASS** exists; config hash matches RELEASE | 2382 | `e9267f5581404e9885598979204c08762cd33f362703e526b20f4d3430c35a82` |
| 7 | `holdout.lock.json` + `holdout-access.log.jsonl` | **PASS** lock exists; log **235 bytes**, **1** JSONL entry, `holdout_runs=1` | lock 698 / log 235 | lock `fc9ac96082cbf0aa3df82df017e19af9f49eed5506c5c281858b3de405cde294` / log `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3` |

---

## Item notes

### 1–4. Reports and decision

Both final-report copies exist and are the same 13364 bytes / same sha256.
Failure analysis and the holdout decision file exist at the recorded hashes.
11 misses are classified (6 `CANDIDATE_GENERATION_FAILURE`, 5 `RERANKING_FAILURE`);
none were used to change retrieval.

### 5. SYSTEM-D-RELEASE sidecar

Sidecar path on disk is `experiments/EVAL-HOLDOUT-001/SYSTEM-D-RELEASE.sha256`
(not `SYSTEM-D-RELEASE.json.sha256`). Contents:

```text
1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40  SYSTEM-D-RELEASE.json
```

`sha256sum` of `SYSTEM-D-RELEASE.json` is exactly that digest. **Sidecar matches
file bytes.** JSON was not edited. Status remains `RELEASE_CANDIDATE_FROZEN`,
frozen_at `2026-09-01T00:48:30Z` (2026-08-31 20:48 ET).

### 6. Config hash (immutable RELEASE vs GUARD)

| | |
| --- | --- |
| expected | `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a` |
| `SYSTEM-D-RELEASE.json` `config_hash` | `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a` |
| `SYSTEM-D-GUARD.json` `config_hash` | `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a` |
| match | **PASS** |

RELEASE `config_hash_verified` is true. GUARD was not edited.

### 7. Holdout lock and access log

`evals/splits/gold150-v1/holdout.lock.json`: `holdout_frozen=true`,
`holdout_sha256=756a3a9bc74ce3e2dd3a7924c4048984a0ae5e74237bc8053e18b6fec202d914`,
n=90, frozen_at `2026-08-31T22:30:29Z`.

`evals/splits/gold150-v1/holdout-access.log.jsonl`: **235 bytes**, **1 line**
(one access entry at `2026-09-01T00:51:54Z` = 2026-08-31 20:51 ET, reason
EVAL-HOLDOUT-001 first and only holdout run, count=90).
`experiments/EVAL-HOLDOUT-001/EVAL-HOLDOUT-001-results.json` records
`holdout_runs=1`, `holdout_access_log_bytes_after=235`. No second access.

---

## Git / archive state

| | |
| --- | --- |
| `.git` in this tree | **absent** (git archive, not a clone) |
| HEAD | n/a |
| base commit (zip comment / recorded origin) | `5082123e8c406ab162349d23003b1173afd697ac` (`origin/claude/rag-v1-build-experiments-5yngul`) |
| archive file | `/workspace/rag-v1/rag-5082123.zip` |

**NEW local-only artifact dirs** (0 entries in the 5082123 archive; not on GitHub):

- `experiments/EXP-015`
- `experiments/EXP-016`
- `experiments/EVAL-VAL-002`
- `experiments/EVAL-HOLDOUT-001`

Do not describe these four directories, or this checkpoint/tag/roadmap, as
committed to `origin/claude/rag-v1-build-experiments-5yngul`.

Archive *does* contain EXP-014 and EVAL-VAL-001 / EVAL-SPLIT-001 (those are
in 5082123).

---

## SYSTEM-D files this write left byte-identical

Pre-write hashes (rechecked after this file was created; see tag):

| path | sha256 |
| --- | --- |
| `experiments/EVAL-HOLDOUT-001/SYSTEM-D-RELEASE.json` | `1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40` |
| `experiments/EVAL-HOLDOUT-001/SYSTEM-D-RELEASE.sha256` | `2b33fe9f0f184db40f23ea1f9c48e04d6525d567f08cc630b4add7b72df50bda` |
| `experiments/EXP-016/SYSTEM-D-GUARD.json` | `e9267f5581404e9885598979204c08762cd33f362703e526b20f4d3430c35a82` |

Weights, CE ONNX, and freeze JSON contents were not opened for write.

---

## Companion files written by this closure pass

- `experiments/EVAL-HOLDOUT-001/RAG-V1-FINAL-TAG.md`
- `experiments/EVAL-HOLDOUT-001/ROADMAP-RAG-V2.md` (planning only)
