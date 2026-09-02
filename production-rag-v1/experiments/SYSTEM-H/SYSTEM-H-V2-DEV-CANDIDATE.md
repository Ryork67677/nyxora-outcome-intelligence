# SYSTEM-H-V2-DEV-CANDIDATE — frozen

```
config_hash             026a302b56c18e50f3af1d6b7baba8d744da2c8b951eba9ac1e137d5cec9c491
score_determining_hash  3fade96a9b3597861b0788c15d0e456a52fa92f6907749a2661960e54bf7b2e5
file_sha256             d5199332c2f89d579a009ea77a984f9e2853f8e70fb21268106a7f4563771bf0
```

```
DEVELOPMENT_ARCHITECTURE_FROZEN = true
RELEASE_FROZEN                  = false
VALIDATION_RUN                  = false
NEW_HOLDOUT_RUN                 = false
```

Computed with `rag_v1.ids.config_hash`, the project's own canonical hasher —
verified in the same run to reproduce `SYSTEM-A-GLOBAL`'s frozen identity
`9afcb5b7…78ee0b38` exactly, so this hash is comparable in kind to the existing
frozen systems. Nothing was overwritten: SYSTEM-A, B, D, E, E-L10 and both
SYSTEM-G artifacts are untouched.

## Two hashes, and which one to use

`config_hash` covers every configured field **including** the PERF-003 D1
performance path. That follows the precedent in `systems.py`, whose `STAGE_2`
already carries `exact_search` and `ann_index` — performance characteristics that
sit inside the identity. **This is the identity of the build.**

`score_determining_hash` excludes `performance_path` alone. PERF-003 proved that
path bitwise score-preserving (6205/6205 logits, `max_abs_diff = 0`), so two
systems differing only there must produce identical rankings. Use this one to ask
*"are these two runs comparable?"*; use `config_hash` to ask *"is this the same
build?"*.

## What was independently verified

The supplied values were checked against `EXP-017-preregistration.json` on
`grok/v2-dev` — a document written before any of these scores existed. Sixteen
fields agree exactly:

`projection_set_id` · `window_tokens 448` · `stride_tokens 224` ·
`overlap_fraction 0.5` · `model_id emb_e7d4183f…` · `fingerprint bd95feaeacf98559` ·
`max_seq 512` · `bm25_pool 50` · `dense_pool 50` · `rrf_k 60` · `P 20` ·
`chunk_set cs_v1_control` · no third RRF · E-L10 retrieval scores unaltered ·
CE min-max may be over the union · do not renormalize A.

Three could not be verified here and are recorded as supplied: `parent_n = 10`,
`W_per_parent = 20`, and `projection_index_hash` — which appears on no reachable
branch.

## One discrepancy the coordinator must resolve

**Not blocking, and the freeze proceeded — but it must be confirmed.**

EXP-017's preregistration contains this amendment:

```json
"projection_only_a_channel_normalized_score": 0.0,
"do_not_use_minmax_degenerate_0_5_on_A_for_projection_only": true
```

The value frozen here is the opposite: projection-only candidates receive
**min-max-normalized projection-RRF scores within the P=20 extras, degenerate
0.5**.

These are probably reconcilable. The EXP-017 amendment constrains the **A
channel**, and EXP-019A's entire contribution is a *projection-aware retrieval
prior* — which is precisely the change from "projection-only gets 0.0" to
"projection-only gets a normalized projection score." On that reading EXP-019A
supersedes the amendment by design, and the prereg text is simply older.

**But I cannot see EXP-019A, so I cannot confirm it.** If EXP-019A did not
formally amend that preregistered field, this freeze rests on an unrecorded
change to a preregistration, and `config_hash` above should be revoked and
recomputed. That is a one-line check for whoever holds the EXP-019A records, and
it should happen before SYSTEM-H is scored on anything.

## Resolved configuration

| | |
|---|---|
| global | SYSTEM-A-GLOBAL `9afcb5b7…`, A_pool 100 |
| local | E-L10 within-document BM25, parent_n 10, W 20/parent, **L=10 per query**, full-corpus term statistics |
| projection | `ps_v2_ovl_win448_s224`, win 448 / stride 224 / overlap 0.5, MiniLM-L6 `emb_e7d4183f…`, BM25 pool 50 + dense pool 50, RRF k=60, **P=20 extras**, candidate-generation lane only |
| prior | EXP-019A piecewise channel substitution — E-L10 candidates keep their exact `retrieval_norm`; projection-only extras get min-max projection-RRF within the P=20 set. No third RRF, no union-wide renormalization |
| rerank | frozen CE `5d3e70fd…`, CE min-max over the union (degenerate 0.5), blend **0.7·CE + 0.3·retrieval** |
| ties | blended DESC → E-L10 merge-RRF rank ASC (projection-only `a_rank = 1e9`) → `chunk_id` ASC |
| perf | PERF-003 D1: `pad="batch"`, length bucketing, `batch_size=16`, threads unchanged, **no `fast=True`** |

The performance path matches PERF-002's recommendation exactly: ship the
machine-independent bucketing, leave threads as a separate per-host decision.
