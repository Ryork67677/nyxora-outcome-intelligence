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

## The EXP-017 a_norm field — RESOLVED, freeze kept

EXP-017's preregistration set projection-only `a_norm = 0.0` with
`do_not_use_minmax_degenerate_0_5_on_A_for_projection_only: true`. **EXP-019A
formally superseded that field**; the 0.0 rule is now characterised as historical
SYSTEM-F behaviour.

EXP-019A's authorised change: projection-only members get min-max over that
query's P projection-only fused scores, degenerate/constant → 0.5, while E-L10
members keep their existing `a_norm` exactly. No third RRF, no membership change,
blend stays 0.7/0.3. Reported result 41/50 strict R@10 against EXP-017's 40/50,
candidate R@100 46/50 unchanged, span .82, MRR .6009, doc recall .90, **zero
regressions and zero rank-1 destructions**. EXP-019A prereg SHA256
`f14001ef…b54cf3`. PERF-003 then reconstructed SYSTEM-G under the same rule and
reproduced all five metrics with 6205/6205 CE logits bitwise identical.

**Effect on this freeze: none.** The value frozen here was already minmax/0.5 —
the EXP-019A behaviour, not the EXP-017 one. Twelve content checks confirm it:

`projection-only norm = min-max over P` · `degenerate = 0.5` ·
`a_norm is not 0.0` · `E-L10 a_norm unchanged` · `blend 0.7/0.3` ·
`no third RRF` · `P=20` · `ps_v2_ovl_win448_s224` · `CE D1 dynamic padding` ·
`batch_size 16` · `threads unchanged` · `fast=False` — **all PASS**, and both
hashes recompute from the file.

`config_hash` is therefore **unchanged at `026a302b…`**. Recording the resolution
touched only the provenance block, which is not part of the hashed
configuration, so `file_sha256` moved from `d5199332…` to `ecbc35e7…` while the
architecture identity did not.

One limitation, stated for the record: `EXP-019A-report.md` and
`PERF-003-report.md` are not present on any ref reachable from this session. The
resolution is accepted on the coordinator's authority and recorded as such
(`verified_here: false`), not independently reproduced.

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
