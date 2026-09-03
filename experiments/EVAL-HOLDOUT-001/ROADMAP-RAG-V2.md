# ROADMAP-RAG-V2

Planning only. No experiment was run. No retrieval, holdout, validation,
embeddings, chunking, or weight search was executed while writing this file.
v1 retrieval stays frozen at SYSTEM-D-GUARD-BLEND.

Written 2026-09-01T01:12:54Z (2026-08-31 21:12 ET).

## Why a v2 line exists

Holdout (one shot, `holdout_runs=1`) measured 79/90 strict Recall@10.
Failure analysis classified 11 misses and stopped. The residual is not a
v1 bug-fix list:

- Pool ceiling 97/104 gold spans (84/90 cases) at SYSTEM-A top-100.
  Six cases never entered the pool (`CANDIDATE_GENERATION_FAILURE`).
- Five in-pool spans ranked out of D top 10 (`RERANKING_FAILURE`), including
  HA-58 (A rank 1 → D 19) and GOLD-B001-02 (A 5 → D 63, CE −10.34).
- Covering `cs_v1_control` chunks exist for all 11; two have contributing
  chunk-shape notes (oversized / undersized leftovers) under candidate
  generation, not `CHUNKING_FAILURE`.
- Document recall 0.9778 vs span 0.8833: most misses are passage selection
  inside an already-found document.

v2 work is **new systems and new chunk sets**, evaluated on development
first. It is not a patch to frozen D.

## Proposed experiments (not started)

### EXP-017 — evidence-preserving chunking

| | |
| --- | --- |
| new chunk set | `cs_v2_evidence_preserving` |
| control | `cs_v1_control` stays **immutable** (v1 release chunk set; 14,209 rows) |
| hypothesis | Span-aware / section-faithful chunks reduce pool misses and same-chunk CE conflict without moving gold offsets |
| split | **development first** (gold150-v1 n=20) |
| holdout | **do not load, do not run** |
| embeddings | new rows for `cs_v2_*` only if/when EXP-017 is actually authorized; never re-embed or rewrite `cs_v1_control` |
| promotion | freeze a v2 chunk config on development gates before any validation load |

Do not retarget chunk boundaries using the 11 holdout miss spans. Those
cases stay unseen for engineering.

### EXP-018 — candidate expansion

| | |
| --- | --- |
| hypothesis | Raising SYSTEM-A pool (depth per retriever and/or fused K) recovers spans that D never saw at pool 100 |
| control | frozen SYSTEM-A-GLOBAL hash `9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38` as the v1 generator; expansion is a **new** system, not an edit to D's freeze |
| split | development first |
| holdout | **do not run**; do not pick K from the six holdout pool-miss cases |
| coupling | may compose with EXP-017 (new chunks) or run on `cs_v1_control` as an isolated pool ablation |
| note | A ranks in the holdout per-case file are candidate-generator ranks from D's one run, not a SYSTEM-A holdout score. Do not invent one. |

### EXP-019 — reranker robustness

| | |
| --- | --- |
| hypothesis | CE overconfidence / generic-neighbour preference (HA-24 family; holdout HA-58 and GOLD-B001-02) can be reduced without the EXP-016 clamp and without retuning frozen 0.7/0.3 |
| in scope | robustness diagnostics on **development** (already-known HA-22/HA-24), alternative blend or calibration as a **new** named system, latency if CE stays in the loop |
| out of scope | editing SYSTEM-D-GUARD-BLEND; swapping clamp (`protect_a_rank_max=3`) into v1 D; changing CE ONNX `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a` in place |
| split | development first; validation only after a new freeze file exists |
| holdout | **do not run** |

## Explicit do-nots (ChatGPT / v1 freeze)

These are standing rules for v2 planning and for any later execution. This
document does not authorize breaking them.

1. **Do not change v1 retrieval.** No weight search on 0.7/0.3, no clamp
   swap into D, no encoder change, no CE revision swap, no new passages
   written into `cs_v1_control`.
2. **Do not mutate freeze files.** `SYSTEM-D-RELEASE.json`,
   `SYSTEM-D-RELEASE.sha256`, `SYSTEM-D-GUARD.json`, CE ONNX bytes, and
   holdout lock/log stay read-only.
3. **Do not run holdout.** `holdout_runs` stays 1. A second run is not
   confirmation. Do not enumerate holdout IDs or load holdout question
   text for v2 work.
4. **Do not debug retrieval from the 11 holdout misses.** They are
   classified, not a tuning set. Do not promote a v2 change because it
   would have fixed those cases.
5. **Do not revive rejected v1 systems.** SYSTEM-B / DOC-C is
   `REPLICATION_REJECTS_B`. Pure CE SYSTEM-C is `RERANKER_REJECTED_AT_DEV`.
6. **Do not invent a SYSTEM-A holdout number.** A was candidate generation
   for D only.
7. **Do not claim the validation delta is significant.** CI includes 0;
   McNemar p=0.25.
8. **Do not claim a closed-book win.** EXP-NULL never ran.
9. **Do not fetch live documents.** Corpus identity remains the CORPUS-002
   snapshot.
10. **Do not run EXP-017/018/019 in this closure pass.** This file is a
    plan. Execution needs a later owner decision and its own
    preregistration.
11. **Do not replace `cs_v1_control`.** v2 chunking is an additive set
    (`cs_v2_evidence_preserving`).
12. **Do not move GOLD membership or the holdout lock.** Errata stay
    errata; cases are not swapped because a system missed them.
13. **Do not treat local EXP-015/016/EVAL-VAL-002/EVAL-HOLDOUT-001 as
    GitHub history.** Base commit remains `5082123e8c406ab162349d23003b1173afd697ac`.
14. **Development first; no holdout for exploration.** Validation only
    after a new freeze. Never skip to holdout to "see if v2 worked."

## What may proceed without moving D's ranked list

- Answer-generation eval on already-retrieved v1 top-10 (if separately
  authorized), using fresh stateless calls only.
- Latency engineering that does not change scores.
- This v2 proposal and later preregistrations.

v1 claim and tag stay in `RAG-V1-FINAL-TAG.md`.
