# RAG v2 research charter

Written 2026-09-01T01:27:02Z (2026-08-31 21:27 ET). Planning and process rules only. This file does not
run retrieval, does not load holdout, does not load validation, and does not
edit v1 freeze artifacts.

v1 is closed. v2 is a new line of systems evaluated on development first.

## 1. Frozen v1 baseline

SYSTEM-D-GUARD-BLEND is the production RAG v1 retrieval system.

| | |
| --- | --- |
| system | SYSTEM-D-GUARD-BLEND (EXP-016 variant D; score blend, not clamp) |
| config hash | `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a` |
| SYSTEM-A (candidate generator) | `9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38` |
| holdout EVAL-HOLDOUT-001 | **79/90 (87.8%)** strict Recall@10 |
| holdout macro span recall@10 | **0.8833** (92/104) |
| holdout document recall | **0.9778** |
| holdout MRR | **0.7055** |
| holdout_runs | **1** (never a second run) |
| validation EVAL-VAL-002 | D 33/40 vs recorded A 30/40; 0 regressions |

v1 claim stays in `experiments/EVAL-HOLDOUT-001/RAG-V1-FINAL-TAG.md`.

## 2. Immutable v1 artifacts

Do not edit, overwrite, re-hash in place, or silently replace:

- `experiments/EVAL-HOLDOUT-001/SYSTEM-D-RELEASE.json` (and `.sha256`)
- `experiments/EXP-016/SYSTEM-D-GUARD.json`
- `cs_v1_control` (14,209 chunks; no new passages, no re-embed)
- GOLD-001 membership and gold offsets
- gold150-v1 holdout lock, holdout.json, holdout-access.log.jsonl
- EVAL-HOLDOUT-001 / PRODUCTION-RAG-V1 final reports, failure analysis, tag

Do not change 0.7/0.3, CE ONNX
`5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`, SYSTEM-A
hash, or D code paths in place. v2 work is **new named systems** and, if
authorized later, **new chunk sets**.

## 3. v2 hypothesis

Holdout residual is **not a document-retrieval problem**. Document recall is
already 0.9778; most misses are passage selection inside an already-found
document, plus a smaller candidate-generation miss set. `CHUNKING_FAILURE=0`
on the classified holdout misses.

v2 goal: **increase evidence availability and passage selection** without
breaking D precision.

- Evidence availability = gold spans present in the candidate pool (candidate
  evidence recall).
- Passage selection = frozen D-style rerank (CE + A blend) over a *larger
  additive pool*, or later a new robustness system (EXP-019), not a D edit.
- Do **not** revive SYSTEM-B / DOC-C document gates. EXP-012 failed because
  Stage-1 routing **dropped** documents. v2 expansion is union, never a gate.

The 11 holdout misses are historical classification, **not a tuning set**.
Do not choose knobs to recover them. Do not enumerate holdout IDs for
engineering.

## 4. Experiment order (frozen process)

1. **EXP-018** — additive within-document candidate expansion as
   SYSTEM-E-WITHIN-DOC on `cs_v1_control`. Development n=20 first.
2. **EXP-017** — evidence-preserving chunking (`cs_v2_*` additive set;
   `cs_v1_control` stays immutable). After 018 unless a later owner note
   reorders.
3. **EXP-019** — reranker robustness (new named system; do not retune frozen
   0.7/0.3 in place; do not swap the EXP-016 clamp into v1 D).

Latency work may run **in parallel** if and only if it is **score-preserving**
(same ranked lists, same hashes). Latency that changes scores is a new system
and needs its own preregistration.

## 5. Standing do-nots

1. **Never holdout for engineering.** `holdout_runs` stays 1. Do not load
   holdout question text. Do not enumerate holdout IDs to pick knobs. Do not
   open holdout to "make an experiment interesting" after a development
   ceiling.
2. **Never DOC-C gates.** No restrict-to-selected-docs candidate set. Local
   retrieval may add; it must not remove global SYSTEM-A candidates.
3. **Development first.** Validation only after a new freeze file exists and
   ChatGPT/owner approves. Never skip to holdout.
4. **No v1 mutation.** Freeze files, `cs_v1_control`, GOLD, holdout lock, CE
   ONNX, 0.7/0.3 stay read-only.
5. **No post-score knob search** on the same experiment.
6. **No live doc fetch.** Corpus identity remains
   `snap_689e336380a054d8039dc35b2c09cd0a`.
7. **Do not freeze a v2 release from development alone** without an explicit
   ChatGPT/owner decision.

## 6. Honest development ceiling

EXP-016 SYSTEM-D is already 20/20 strict Recall@10 and 23/23 spans@10 on
gold150-v1 development. Strict Recall@10 **cannot improve** on that split.
A tied 20/20 is **not** a retrieval win. If D's candidate pool already
contains every gold span, report `CEILING_ON_DEV` and stop. Do not then load
validation or holdout.
