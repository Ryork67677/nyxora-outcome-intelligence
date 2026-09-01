# EVAL-HOLDOUT-001 preregistration

Written after the SYSTEM-D release-candidate freeze and **before** any holdout
run. Holdout question text is not loaded. Holdout IDs are not enumerated.
`evals/splits/gold150-v1/holdout-access.log.jsonl` is 0 bytes.

## System under test

One-shot **SYSTEM-D-GUARD-BLEND** only, frozen in
`experiments/EVAL-HOLDOUT-001/SYSTEM-D-RELEASE.json`.

ChatGPT: run SYSTEM-D only.

SYSTEM-A was never run on holdout. This holdout measurement is D-only. Do not
invent A holdout numbers. No A rerun is required unless a later pairing analysis
needs stored A ranks (none exist on holdout).

## Rules (frozen now)

- No tuning.
- No debugging from holdout cases.
- No retrieval changes after this freeze.
- No weight search, no clamp swap (clamp was variant C, not D), no new
  passages, no encoder change.
- Score each holdout case exactly once.

## Endpoints

- **Primary:** strict Recall@10 (full-case).
- **Secondaries:** span recall, MRR, document recall, latency.

## Split

`gold150-v1` holdout, n=90, `holdout_sha256`
`756a3a9bc74ce3e2dd3a7924c4048984a0ae5e74237bc8053e18b6fec202d914`
from `evals/splits/gold150-v1/holdout.lock.json`.

## Status

`holdout_runs` = 0. Not yet executed.
