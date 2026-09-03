# EXP-016 preregistration

Written **before** any EXP-016 scores. No fusion/guard ranks, no development
result file, no SYSTEM-D freeze.

## 1. Hypothesis

EXP-015 rejected CE-only reranking at development (`RERANKER_REJECTED_AT_DEV`,
A 19/20 vs C 18/20). The CE rescued GOLD-B005-11 (A pool 13 → C 1) but destroyed
exact-match head items: HA-22 (A 2 → C 21) and HA-24 (A 1 → C 18).

A frozen exact-match **guard** (variant C) or a frozen CE/A **score blend**
(variant D), applied to the **same** SYSTEM-A pool of 100 and the **same** CE
logits as EXP-015, can raise or hold strict Recall@10 versus SYSTEM-A without
destroying exact-match head items.

No training on GOLD. No new passages. No BM25 / MiniLM / RRF / chunking / query
/ normalization / provider-hint / pool / CE-weight change. No sweep.

## 2. Control — Variant A (frozen SYSTEM-A)

SYSTEM-A-GLOBAL config hash `9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38`.

Expected development strict Recall@10 = 19/20 from EXP-015. **Re-report from
stored A ranks. Do not retune. Do not treat a rematerialized A run as a new
baseline.**

Must not change: BM25 (Postgres FTS `simple`), MiniLM ONNX encoder fingerprint
`bd95feaeacf98559`, RRF `rrf_k=60`, `pool_per_retriever=50`, chunking
`cs_v1_control`, raw query, normalization, provider hints, candidate generation.
`reranker=null`, `cross_encoder=null`, `top_k=10`.

## 3. Already-rejected control — Variant B (CE-only SYSTEM-C)

SYSTEM-C as measured in EXP-015: 18/20, rescue GOLD-B005-11, regressions HA-22
and HA-24. SYSTEM-C is **not frozen**. Record B as the already-rejected CE-only
control. Do not rerun CE-only scoring unless needed to attach traces after
rematerializing the unpersisted pool-100 lists.

Tie-break (EXP-015, frozen): CE logit desc, then SYSTEM-A fused rank asc, then
`chunk_id` asc.

## 4. Variant C — exact-match protected reranking (frozen now)

Same A candidate pool 100. Same CE logits. No new knobs.

**Protection rule (frozen now; do not tune after seeing scores):**

If a candidate has **exact identifier overlap** with the query **and** its
SYSTEM-A fused rank is `<= 3`, then it **cannot be placed worse than rank 10**
after rerank (clamp). Remaining candidates stay in EXP-015 CE order.

### Identifier matcher (frozen)

Project term-handling exists (`rag_v1.query_views.identifiers`,
`query_views.is_protected`, `query_views._TOKEN_RE`, and
`retrieval.exact_identifier_search`'s `_` / `.` / `-` token test). The matcher
is those identifier extractors **restricted to identifier-shaped tokens**, not
bare capitalized product words (`Claude`) which `is_protected` would keep.

Extract a set of identifier tokens from a string as the union of:

1. Inner text of quoted / backtick spans: `` `...` ``, `"..."`, `'...'`, kept if
   the inner span contains an alphanumeric character.
2. `rag_v1.query_views.identifiers(text)` (snake / dotted / slash / ALL-CAPS).
3. Tokens from `query_views._TOKEN_RE` (after stripping wrapping backticks and
   `.,:;?!()[]{}`) that match **any** of:
   - CamelCase / camelCase: `[A-Za-z]*[a-z][A-Z][A-Za-z0-9]*`
   - snake_case: `[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+`
   - dotted API: `[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z0-9_.]+`
   - screaming / error / code: `[A-Z0-9_]{3,}`
   - version-like: `v?\d+(\.\d+)*[A-Za-z0-9._-]*` (must contain a digit)
   - hyphenated code / error string: `[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+` of length ≥ 5

**Overlap:** non-empty intersection of the query identifier-token set and the
candidate identifier-token set. Comparison is exact string equality
(case-sensitive). No fuzzy match, no extra terms, no corpus list.

Bare capitalized words and ordinary English are **not** identifiers.

### Clamp algorithm (frozen)

1. Order the pool by EXP-015 CE tie-break → CE ranks.
2. `need_floor` = protected candidates whose CE rank is `> 10`.
3. Let `n = |need_floor|`. Take the first `10 - n` items of the CE order that
   are not in `need_floor`. Append `need_floor` in CE order. Append the rest in
   CE order.
4. Re-number ranks 1…pool.

This puts every protected A-head item at rank ≤ 10 and disturbs CE order as
little as possible. At most three items can be protected (A rank ≤ 3), so
`n ≤ 3` and `10 - n ≥ 7`.

## 5. Variant D — score blend (frozen now)

Same A candidate pool 100. Same CE logits. **No weight search.**

```
final_score = 0.7 * minmax_norm(CE) + 0.3 * minmax_norm(SYSTEM-A fused RRF score)
```

Min-max is computed **within each query's pool** (the fused 100, or fewer if
RRF returned fewer). If `max == min` on a channel, every value on that channel
is `0.5` (well-defined; no NaN).

Tie-break (frozen): blended score desc, then SYSTEM-A fused rank asc, then
`chunk_id` asc.

Weights `0.7 / 0.3` are frozen. Do not search.

## 6. Candidate reuse

Prefer stored EXP-015 pool-100 lists + CE logits so the only change is the
fusion/guard. Those lists were **not** persisted (EXP-015 stored gold-span ranks
and gold-span CE scores only). Therefore rematerialize SYSTEM-A top 100 on
**development only** (`evals/splits/gold150-v1/development.json`, n=20,
projection `experiments/EXP-015/development.jsonl`) and score with the same CE
(`cross-encoder/ms-marco-MiniLM-L6-v2` revision
`233902d25c440f23af6f7d6e94d2946bac0bee0a`, ONNX sha256
`5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`).

Do **not** load `validation.json`. Do **not** load holdout. Do **not**
enumerate holdout IDs. Do **not** fetch live docs. Do **not** train on GOLD.
Do **not** sweep.

Rematerialized gold-span A ranks and CE ranks must reproduce EXP-015
(`HA-22` 2→21, `HA-24` 1→18, `GOLD-B005-11` 13→1). Variant A/B metrics are
taken from the stored EXP-015 summaries, not from a new baseline.

## 7. HA-24 diagnostic (before scoring C/D)

After rematerializing the HA-24 pool and CE logits, and **before** applying the
C clamp or D blend, write `experiments/EXP-016/EXP-016-HA24-diagnostic.md`:
query, gold span, top A passage (rank 1) + CE score, top C passage (CE rank 1)
+ CE score, gold-chunk CE score and why it fell to 18. Question: did CE prefer
a more general explanation over the exact answer? Short excerpts only.

## 8. Development qualification (20-case development only)

Split: `evals/splits/gold150-v1/development.json` (n=20). Compare A, B, C, D.

Primary: strict Recall@10.

Secondary: span recall, MRR, rescues vs A, regressions vs A, latency,
rank-destruction events (A rank ≤ 3 dropped out of top 10).

Required per-case traces on HA-22, HA-24, GOLD-B005-11 under every variant:
A rank, pool rank, CE score, guarded/blended rank, whether all required spans
are in top 10.

## 9. Decision rule (frozen now)

A guarded/blended variant (C or D) **qualifies** if and only if all of:

- strict Recall@10 ≥ A's 19/20
- net rescues vs A ≥ 0 (rescues − regressions)
- no **new** rank-1 destruction: no case whose gold span had A rank 1 is
  dropped out of that variant's top 10

If at least one qualifies, freeze the qualifying variant with highest strict
Recall@10; ties broken by higher MRR, then fewer rank-destruction events, then
C over D. Write `experiments/EXP-016/SYSTEM-D-GUARD.json`. **STOP for
validation approval. Do not run validation.**

If neither qualifies: `RERANKER_DIRECTION_REJECTED`. Do not freeze SYSTEM-D.

No post-score retuning. No EXP-017 in this pass.

## 10. Holdout

**NEVER run holdout.** Never load holdout question text. Never enumerate
holdout IDs. `holdout-access.log.jsonl` must remain 0 bytes.
