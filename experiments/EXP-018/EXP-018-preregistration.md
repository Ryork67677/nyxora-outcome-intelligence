# EXP-018 preregistration

Written **before** any EXP-018 retrieval, CE scoring, union pools, or
development result file. No SYSTEM-E scores exist at this timestamp.

Timestamp: **2026-09-01T01:23:45Z** (2026-08-31 21:23 ET).

ChatGPT approved this as v2 experiment 1 (2026-08-31 ~21:19 ET) after Grok
rejected EXP-017-chunking-first. This is a **new system**
`SYSTEM-E-WITHIN-DOC`, not an edit to frozen SYSTEM-D-GUARD-BLEND.

## 1. Hypothesis

Holdout analysis (historical, **not a tuning set**) classified 11 SYSTEM-D
misses with `CHUNKING_FAILURE=0`. Six were candidate-generation misses; five
were rerank misses. Document recall was 0.978; 9/11 gold documents were already
in D top-10. EXP-012 SYSTEM-B DOC-C **FAILED** because Stage-1 routing
**dropped** documents (val A 30/40 vs B 21/40).

**SYSTEM-E must be the opposite of DOC-C: additive union, never a document
gate.** Expanding candidate generation *inside* documents that frozen SYSTEM-A
already placed in fused top-10, then unioning those chunks with the original
SYSTEM-A pool of 100 (never dropping an A-pool chunk), then applying frozen D
blend (0.7 minmax CE + 0.3 minmax A) on the larger pool, can raise **candidate
evidence recall** (gold spans present in the candidate pool) without regressing
strict Recall@10 versus frozen SYSTEM-D.

Known ceiling risk, accepted now: EXP-016 SYSTEM-D is already 20/20 strict
Recall@10 and 23/23 spans@10 on this same development split, document recall
1.0. Candidate evidence recall at k=10 / pool-100 may already be 1.0. That is
a valid outcome (`CEILING_ON_DEV`). If so, development cannot measure the
holdout-motivated pool-miss hypothesis. Do **not** then load holdout or
validation. Do **not** retune knobs after seeing a ceiling.

## 2. Control — frozen SYSTEM-D-GUARD-BLEND

Read-only freeze files (must not be edited):

- `experiments/EXP-016/SYSTEM-D-GUARD.json` hash
  `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a`
- `experiments/EVAL-HOLDOUT-001/SYSTEM-D-RELEASE.json`

SYSTEM-A-GLOBAL hash
`9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38`.

Expected development (EXP-016 stored, not retuned): strict Recall@10 = 20/20,
macro span recall 1.0, spans@10 23/23, MRR 0.8239, document recall 1.0,
latency mean 5774.4 ms. Rematerialize D on development with the frozen config
and confirm 20/20, or prove identity against stored EXP-016 D ranks for
`gold150-v1/development`. Do not retune D. Do not edit 0.7/0.3, CE ONNX, A
hash, or D code paths in place.

## 3. SYSTEM-E-WITHIN-DOC — frozen knobs (do not change after scores)

1. Run frozen SYSTEM-A globally (BM25 Postgres FTS `simple` k1=1.2 b=0.75 +
   MiniLM cosine exact + RRF k=60, `pool_per_retriever=50`) over all
   `cs_v1_control` chunks. Raw query, no rewrite, no metadata filter.
2. Parent documents = unique `version_id`s among SYSTEM-A fused `top_k=10`.
   Frozen `parent_n=10`. Rationale written **now**: these are documents the
   global system already identified; expansion happens inside them. Do not
   pick `parent_n` from holdout.
3. Within-doc expansion: for each parent `version_id`, score **ALL**
   `cs_v1_control` chunks of that version using the **same full-corpus BM25
   and transformer scores** (do **not** recompute IDF inside the document;
   reuse `lexical_search`/`dense_search` `version_ids` restriction which keeps
   corpus n/df/avg_len unchanged). Fuse those within-doc lists with RRF k=60
   (within-document ranks, not global-among-parents ranks). Take top `W=20`
   chunks per parent (or all if fewer). Frozen `W=20`.
   Implementation note frozen now: scoring all parent versions in one
   filtered BM25/dense call and then re-ranking within each `version_id` is
   **identical** to per-parent calls, because a chunk's full-corpus BM25 and
   cosine do not depend on the candidate set. Equivalence is mechanical, not
   a knob.
4. **UNION** those expanded chunks with the original SYSTEM-A candidate pool
   of 100. Dedupe by `chunk_id`. **NEVER drop an A-pool-100 chunk**, even if
   its `version_id` is not a parent. This is the **anti-DOC-C rule**.
5. Cross-encode the UNION pool with the frozen CE (same artifact/sha as D).
   Apply frozen D blend: `0.7 * minmax_norm(CE) + 0.3 * minmax_norm(A)` with
   the same tie-breaks as EXP-016 variant D (blend desc, SYSTEM-A fused rank
   asc, `chunk_id` asc). Min-max is within each query's **E union pool** (the
   natural application of D's formula to a larger pool). For union members
   **absent from SYSTEM-A fused top-100**: frozen `a_score=0.0` and
   `a_rank=1000000000` (strictly worse than any A-pool rank). This is not a
   weight search and not a D edit. Rematerialized D still min-maxes over the
   A pool of 100 only.
6. Emit `top_k=10`.
7. New config hash for SYSTEM-E. Do not overwrite D's hash.

BM25 IDF stays full-corpus. `cs_v1_control` stays immutable (no new passages).
No new embeddings except if a chunk somehow lacked a row — they should not
(14209/14209 confirmed before this file).

### Anti-DOC-C rule (frozen)

Never restrict the candidate set to selected documents. Never drop a
SYSTEM-A pool-100 chunk. Expansion is union, not a gate. Do **not** copy
`src/rag_v1/hierarchical.py`'s restrict-to-selected-docs pattern into E.

### Not tuned from the 11 holdout misses

`parent_n=10` and `W=20` are frozen in this file before retrieval. They are
**not** chosen to recover any holdout miss. Historical holdout analysis may
be read as motivation; the 11 miss IDs must not be enumerated for engineering
and must not set knobs.

## 4. Splits

**ONLY** `evals/splits/gold150-v1/development.json` (n=20), projection
`experiments/EXP-015/development.jsonl`.

- Do **not** load `validation.json` / `validation.jsonl`.
- Do **not** load holdout. Do **not** enumerate holdout IDs. Do **not** open
  `holdout.json`.
- `holdout.lock.json` remains frozen. `holdout-access.log.jsonl` bytes at
  preregistration = **235** (sha256
  `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`);
  must be unchanged after the run (no new holdout access). Historical
  EVAL-HOLDOUT-001 already wrote one line; EXP-018 must not grow it.

## 5. Metrics

Primary (ChatGPT): **candidate evidence recall** = fraction of gold spans
present in the candidate pool (D pool = A top-100; E pool = union). Also
report pool size mean/max.

Also compute:

- strict full-case Recall@10 (E vs D vs A)
- macro span recall, spans found@10 / total, MRR, document recall
- Additive integrity: every A-pool-100 `chunk_id` still in E pool (must be
  true for all 20 cases). Every D-found gold document still retrievable
  (document recall E >= D).
- Rescues / regressions vs D; rank-1 destruction events (gold span with D
  rank 1 dropped out of E top-10; also report A-rank-1 events)
- Latency mean vs D (~5774 ms on EXP-016 D)
- Named traces for any case that differs, plus GOLD-B005-11, HA-22, HA-24

## 6. Decision rule (frozen now; do not move the goalposts)

- **QUALIFIES_FOR_VAL_CONSIDERATION** if: strict Recall@10 >= D **AND** net
  rescues vs D >= 0 **AND** no new rank-1 destruction **AND** additive
  integrity holds.
- **MECHANISM_SUPPORTED** if candidate evidence recall_E > candidate
  evidence recall_D (more gold spans enter the pool).
- **CEILING_ON_DEV** if D already has candidate evidence recall = 1 **and**
  Recall@10 = 20/20 **and** E does not regress: still
  QUALIFIES_FOR_VAL_CONSIDERATION but do **not** claim a retrieval win.
  State that development cannot measure the holdout-motivated pool-miss
  hypothesis.
- **REJECT_AT_DEV** if E regresses vs D on strict Recall@10 **or** additive
  integrity fails (dropped an A-pool chunk or dropped a D-found document).

Do **NOT** freeze SYSTEM-E as a v2 release. Do **NOT** run validation. Do
**NOT** run holdout. Leave freeze-or-val as a ChatGPT decision.

## 7. Explicit do-nots

- no holdout (no question text, no ID enumeration, no second holdout run)
- no validation load
- no D edit (0.7/0.3, CE ONNX, A hash, D freeze files, D code paths)
- no knob search after scores (`parent_n`, `W`, blend weights stay frozen)
- no using the 11 holdout misses to choose knobs
- no copy of DOC-C document gate
- no new passages into `cs_v1_control`
- no re-embed of `cs_v1_control`
- no live OpenAI/Anthropic doc fetch
- no git clone / commit / push
- no touch of the user's Windows tree
- no SYSTEM-E release freeze

## 8. Environment (fingerprint; known drift)

Postgres 16.15 / pgvector 0.8.6 vs historically recorded 16.13 / 0.6.0.
Snapshot `snap_689e336380a054d8039dc35b2c09cd0a`, chunk set `cs_v1_control`
(14209 chunks), embeddings MiniLM ONNX fingerprint `bd95feaeacf98559` /
model_id `emb_e7d4183fd6eb878ae2fdf080efb6861e`. CE
`cross-encoder/ms-marco-MiniLM-L6-v2` rev
`233902d25c440f23af6f7d6e94d2946bac0bee0a`, onnx sha256
`5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`.
