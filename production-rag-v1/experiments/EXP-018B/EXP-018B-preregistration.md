# EXP-018B preregistration

Written **2026-08-31T23:27:17-04:00** (2026-09-01T03:27:17Z UTC), **before** any EXP-018B Track 1
scoring of Track 2 and before any L-cap scores. ChatGPT approved this exact
revision at **2026-08-31T23:22:00-04:00** (~2026-08-31 23:22 ET). Protocol copy:
`experiments/EXP-018B/CHATGP-EXP-018B-protocol.txt` (verbatim from
`/workspace/reply-exp018b-critique.txt`).

This file freezes the Track 2 cross-parent extras ordering rule. That rule
will not change after scores.

## Dataset

Frozen **V2-DEVSET-001 n=50 only**.

- `evals/gold/v2-devset-001.jsonl` (sha256 `cb687f3cc88b38d4beed7ad4bc829296a30518aaaf45cce0677ec568b1bf77e5`)
- `evals/splits/v2-devset-001/development.json` (sha256 `6b0c49c9040c215fde6134697c35a1f28458ba7d72ef012c0840feb7f9c3eb17`)
- `experiments/RAG-V2/V2-DEVSET-001/V2-DEVSET-001-FREEZE.json` (sha256 `97ea6befbb4fd845f53da2aef20ba84cedaaf69c0f09e3ad90833b813fee2ad9`)

Do **not** load `evals/splits/gold150-v1/holdout.json` or `gold150-v1/development`.

Holdout access log at preregistration: **235 bytes**, sha256
`45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`. Must be
unchanged after the run.

## Frozen identities (do not change)

| id | hash |
| --- | --- |
| SYSTEM-D | `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a` |
| SYSTEM-E | `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe` |
| SYSTEM-A | `9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38` |
| snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| chunk_set | `cs_v1_control` (14209 chunks) |
| MiniLM ONNX fingerprint | `bd95feaeacf98559` |
| CE sha256 | `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a` |

Knobs inherited from frozen E (not retuned): W=20 per parent, parent_n=10
unique version_ids first-seen in A fused top-10 (typically 6–9, not always 10),
A pool 100, RRF k=60, blend 0.7 CE + 0.3 merge-RRF, anti-DOC-C (never drop A-pool).

## Do-nots

- No validation.
- No holdout.
- No SYSTEM-D edits (`SYSTEM-D-GUARD.json`, `SYSTEM-D-RELEASE.json` read-only).
- No CE / blend / RRF / SYSTEM-A / W / parent_n / A-pool-size changes.
- No EXP-017.
- No EXP-019.
- Do not freeze SYSTEM-E as a release system.
- Do not modify `SYSTEM-E-WITHIN-DOC.json`, `cs_v1_control`.
- Do not invent extra L values after seeing scores.
- Do not retune after scores.
- Do not re-embed. Do not restore corpus from scratch unless DB is empty.
- Do not git clone. Do not touch the user's Windows machine.
- Do not open holdout.json.
- Do not use the four known rescue IDs as a promotion/selection gate.

## Track 1 — score-preserving local BM25 optimization

**Goal:** remove redundant local-BM25 computation without changing SYSTEM-E
retrieval behavior.

Current E calls `lexical_search(query, SNAPSHOT, W, version_ids=[vid])` once
per parent. That re-runs `_LEXICAL_SQL` full-corpus IDF CTEs (n / avg_len / df)
independently ~6–10 times per query. Stored EXP-018 local BM25 mean: 6077.6 ms.

**Fast path (frozen):** one SQL call with `version_ids = all parents` (same
`_LEXICAL_SQL`, same full-corpus IDF, same BM25 k1=1.2 b=0.75, same snapshot,
same W=20). Then take top-W=20 per parent using the same ORDER BY as
`lexical_search`: `round(score::numeric, 9) DESC, chunk_id ASC`. Re-rank 1..W
inside each parent as current E does.

Do **not** reuse SYSTEM-A's global top-50 BM25 list. After `rrf_fuse`,
`SearchHit.score` is RRF and original BM25 is discarded. A's lexical is only
corpus-wide top-50; E's W=20 per parent routinely includes chunks never in
that 50. Overlap-only reuse would fail the equivalence gate.

Do not approximate. Do not change W, merge, fusion, CE, blend.

**EQUIVALENCE GATE** vs stored EXP-018 (`EXP-018-v2devset001-results.json` +
`EXP-018-v2devset001-pools.jsonl`), all 50 queries:

1. same local candidate identities (extras = union − A-pool-100 match stored
   `new_union_chunk_ids`; per-parent top-W sets implied by union + RRF)
2. same local candidate ordering (per parent) — stored E did not persist
   per-parent ordered lists; existing within-parent order is
   `round(BM25 score, 9) DESC, chunk_id ASC` from `_LEXICAL_SQL`. Track 1 uses
   that same key after the batched SQL. Empirical check: union membership +
   final ranks (RRF uses per-parent ranks 1..W, so order mismatches would
   move final ranks)
3. same union membership
4. same final reranked ordering/ranks (stored `e_top10` chunk_id sequence +
   gold `e_rank`)
5. same strict Recall@10, candidate Recall@100, span Recall@10, MRR, document
   recall

Any difference caused by the optimization → `SCORE_PRESERVING=false`.
**STOP. Do not run Track 2.** Write the mismatch report.

If true: record latency breakdown A/global, local BM25, CE, total, then
continue to Track 2.

Reference stored EXP-018 metrics (do not rerun old E unless a field is missing):

| | cand R@100 | strict R@10 | span R@10 | MRR | doc recall | pool | latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| D | 41/50 | 38/50 | 0.76 | 0.5650 | 0.90 | 94.1 | 5824 ms |
| E | 45/50 | 40/50 | 0.80 | 0.5969 | 0.92 | 176.8 | 16604 ms |

## Track 2 — additive per-query cap

Only if Track 1 passed. Use the Track 1 implementation.

**L means ADDITIVE LOCAL PASSAGES PER QUERY** after dedupe and excluding
A-pool-100. It does **not** mean per parent.

Test exactly `L = {10, 20, 40}`. No additional L after seeing results.

Per query:

1. generate current E local candidates (optimized, equivalent)
2. deduplicate by `chunk_id`
3. exclude passages already in A-pool-100
4. apply the FROZEN cross-parent ordering below
5. take the first L additive passages for the entire query
6. union with A-pool-100, merge RRF, frozen D blend/CE as in E

Local lists passed to merge RRF keep original within-parent BM25 ranks 1..W
and retain local hits that already sit in A-pool-100 (they are not additive
and do not count toward L; dropping them would change A-pool RRF
contributions). Each parent's local list is filtered to
`(in A-pool-100) ∪ (selected L extras for that parent)`.

### Frozen cross-parent ordering of additive extras

Inspected stored E / live `system_e.local_bm25_per_parent`: local
`SearchHit.score` is the **full-corpus-equivalent BM25** from
`lexical_search` (rank is overwritten 1..W; score is not RRF). Existing E
defines **no cross-parent ordering** — parents are independent.

Existing within-parent tie-break (found, not invented), from
`src/rag_v1/retrieval.py` `_LEXICAL_SQL`:

```
ORDER BY round(scored.score::numeric, 9) DESC, scored.chunk_id
```

**FROZEN NOW** for extras not in A-pool-100, after dedupe:

```
sort key = (round(local_BM25_score::numeric, 9) DESC, chunk_id ASC)
```

Python implementation: `Decimal(str(score)).quantize(Decimal('0.000000001'),
rounding=ROUND_HALF_UP)` then `(-quantized, chunk_id)`. Postgres `numeric`
ROUND is half-away-from-zero; BM25 scores are positive so this matches.

Do not change this key after scores. Do not invent a learned or query-tuned
fusion rule.

## Preregistered selection rule

Select the **smallest L** in `{10, 20, 40}` satisfying **both**:

1. candidate gold-span Recall@100 >= **44/50**
2. **zero** strict Recall@10 regressions versus SYSTEM-D

Do **not** require preservation of all four known EXP-018 rescue IDs.
Do **not** require a strict Recall@10 improvement over D.

If multiple caps qualify: select the smallest L.
If no cap qualifies: select **none**. EXP-018 remains MECHANISM_SUPPORTED
but the tested capped variants are not promoted.

**Provenance of >=44/50 (record explicitly):** this threshold was chosen
**after seeing EXP-018's development result of 45/50**. It is a
**development-stage criterion, not an independent validation threshold**.
It must not later be portrayed as an untouched criterion.

Do not retune after scores.

## Known rescue IDs — DIAGNOSTIC_ONLY

Not a selection gate.

| id | EXP-018 in D pool | E blend rank | E pool rank |
| --- | --- | ---: | ---: |
| V2D-11 | no | 34 | 63 |
| V2D-33 | no | 13 | 92 |
| V2D-34 | no | 44 | 40 |
| V2D-43 | no | 10 | 19 |

V2D-48 was already in D pool (D rank 11 → E rank 7); not a pool rescue.

Report per-L fate (in-pool? rank?) marked DIAGNOSTIC_ONLY.

## Metrics to report per L

PRIMARY: candidate gold-span Recall@100 (n/50).

SECONDARY: strict R@10, span R@10, MRR, document recall, rescues vs D,
regressions vs D, rank-1 destructions, mean additive count, mean union size,
A/global latency, local BM25 latency, CE latency, total latency.

## Interpretation constraints

Three of the four EXP-018 pool rescues remained below final top-10 at E
ranks ~13/34/44. Treat that only as evidence of future reranking headroom.
Do not modify SYSTEM-D. Do not change blend weights. Do not start EXP-019.

## Stop

Stop after Track-1 equivalence, Track-1 latency, three Track-2 cap results,
and the preregistered selection decision. No validation. No holdout. No
EXP-017. No EXP-019.

## Preregistration JSON hash

sha256 of `experiments/EXP-018B/EXP-018B-preregistration.json` (this file hashed after write, JSON bytes not mutated after hashing):

`c48068ec5dfa06683eaa2b0763508e9c7457d1ede2f23c3394c3c6bd6192ce8c`
