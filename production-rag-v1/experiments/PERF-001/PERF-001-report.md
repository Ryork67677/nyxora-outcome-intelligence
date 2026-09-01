# PERF-001 — Read-only performance audit of local within-document BM25

**Status:** analysis only. No patch applied, no retrieval executed, no system modified.

## 0. Scope note — what this repository actually contains

The V2 handoff names `SYSTEM-D-GUARD-BLEND`, `SYSTEM-E-WITHIN-DOC`, `V2-DEVSET-001`
and `EXP-018`. **None of those artifacts exist in this repository.** `git log`
ends at `EXP-015`; `src/rag_v1/systems.py` freezes only `SYSTEM-A-GLOBAL` and
`SYSTEM-B-DOC-C`, and it sets `"reranker": None, "cross_encoder": None`. EXP-015
concluded `NO_PRETRAINED_CROSS_ENCODER_AVAILABLE`, so no cross-encoder is
implemented here at all.

What *is* here is the code SYSTEM-E is built out of:

* `src/rag_v1/retrieval.py` — `lexical_search()` and `_LEXICAL_SQL`, the BM25
  implementation, which already accepts a `version_ids` restriction.
* `src/rag_v1/hierarchical.py` — EXP-012 document routing.
* `scripts/run_exp012.py`, `scripts/run_exp014r.py` — the two-stage callers.

Every measurement below is taken against that code and against the live
`snap_689e336380a054d8039dc35b2c09cd0a` / `cs_v1_control` database
(14,209 chunks, 202 documents). The audit therefore describes the *mechanism*
SYSTEM-E inherits with certainty, and the numbers are real. Where a conclusion
depends on SYSTEM-E-specific code I cannot see, it is marked
**[UNVERIFIED — needs SYSTEM-E source]**.

### What was executed for this audit

* `EXPLAIN` **without** `ANALYZE` (plan and cost estimates; the query is not run).
* Catalog inspection (`\d`, `pg_class`, `pg_relation_size`).
* Corpus-statistic aggregates (`count`, `sum`, `avg` of chunk length) — no query,
  no ranking, no candidate, no score.
* Two pure-Python microbenchmarks (connection open/close; Pydantic copy).

No retrieval was run, no D or E run, no cap variant, no V2-DEVSET-001 case
scored, no V1 holdout touched, no file under `experiments/EXP-018*` created or
read, and nothing in `src/` modified.

---

## A. Bottleneck map with estimated relative cost

One call to `lexical_search(q, snap, k, version_ids=[one_parent])` — that is,
one parent's local BM25 — plans at **29,700 cost units** for a 4-term query.
Decomposed by CTE:

| Stage | What it computes | Plan cost | Share | Depends on the parent? | Depends on the query? |
|---|---|---|---|---|---|
| `corpus` CTE | `count(*)`, `avg(length(coalesce(search_text,text)))` over the **whole snapshot** | **29,041** | **~81%** at p50 terms | **No** | **No** |
| `weighted` LATERAL | per-term `df` over the **whole snapshot** | **626 × n_terms** | ~19% at p50 (11 terms → 6,882) | **No** | Yes (terms only) |
| scoring `SELECT` | BM25 sum over the parent's own chunks | **54** | **0.15%** | **Yes** | Yes |

Isolating the two halves of the `corpus` CTE makes the finding unambiguous:

```
count(*) only ..................... cost   536.85   Index Only Scan (no heap access)
count(*) + avg(length(...)) ....... cost 29,040.80   Bitmap Heap Scan, width=809
```

**`avg_len` alone costs 28,504 units — 96% of a single-parent local BM25 query.**

Why it is so expensive physically:

* `search_text IS NULL` for **all 14,209** `cs_v1_control` chunks, so
  `coalesce(search_text, text)` always resolves to `text`.
* `text` is the TOASTed column. The `chunk` TOAST relation is **142 MB**; the
  heap is **310 MB**; `shared_buffers` is **128 MB**. `length()` on a TOASTed
  value has no shortcut — it must read the whole chain.
* So computing `avg_len` **detoasts and scans a working set roughly 3.5× larger
  than shared_buffers, from disk, every time it is computed.**

That is the ~8.3 s the handoff attributes to local BM25. It is not BM25. It is
one corpus-wide `avg(length())` being recomputed once per parent.

### Per-query arithmetic (10 parents, p50 = 11 distinct terms)

Term counts come from tokenizing the 53 existing V1 gold questions with
`query_terms()` (string tokenization only — no DB, no devset):
min 4, **p50 11**, p90 19, max 26.

| | plan cost / query | connections / query |
|---|---|---|
| Current: 10 independent `lexical_search()` calls | 10 × (29,041 + 6,882 + 54) = **359,760** | **20** |
| Query-level work hoisted, parents batched | 29,041 + 6,882 + 155 = **36,078** | 1 |
| \+ `avg_len` materialized | 537 + 6,882 + 155 = **7,574** | 1 |
| \+ `df` cache warm | ~155 | 1 |

**Cold speedup on the local stage: ~47×. Warm: bounded by the 155-unit scan.**

Connection overhead is separately measurable and separately real:
`connect()` + `register_vector()` + `close()` costs a **median 20.6 ms**
(n=12, min 18.5, max 40.1). Each `lexical_search()` opens **two** connections
(see §B3), so 10 parents = 20 connections ≈ **412 ms/query of pure setup**.

### Wall-clock projection

Reported `E − D = 16,604 − 5,824 = 10,780 ms` is the local stage. Decomposing
conservatively (not by scaling planner units, which are not milliseconds):

* connection churn 412 ms → 21 ms  (**−391 ms**)
* 10 repetitions of the corpus scan → 1 repetition (**−~9/10 of the remainder**)
* materializing `avg_len` removes the heap+TOAST read from that last repetition

**Projected E′ ≈ 6.2–6.6 s** against D's 5.82 s — an end-to-end **~2.5–2.7×**,
and **~13–25×** on the local stage alone. These are projections from plan costs
and microbenchmarks, not measurements of E; treat them as a target to verify,
not a result.

---

## B. Exact code locations and functions involved

### B1. `src/rag_v1/retrieval.py:70-124` — `_LEXICAL_SQL`

* **Lines 76-82** — `corpus` CTE. `count(*)` and `avg(length(coalesce(...)))`
  over the full snapshot. **Query-independent and parent-independent constant.
  Recomputed on every invocation.** This is bottleneck #1.
* **Lines 83-98** — `weighted` CTE. `CROSS JOIN LATERAL` computing `df` per term.
  **Query-dependent but parent-independent. Recomputed on every invocation.**
  Bottleneck #2.
* **Lines 99-116** — the scoring `SELECT`. Line 115 is the only place
  `version_ids` appears. This is the ~0.15% that is genuinely per-parent.
* **Line 122** — `ORDER BY round(scored.score::numeric, 9) DESC, scored.chunk_id`.
  This total order is the equivalence contract; §D preserves it exactly.
* **Lines 110-114** — the existing comment already states the invariant the
  optimization must not break: *"the corpus and weighted CTEs above still compute
  n, avg_len and df across the whole snapshot, so a term's IDF is identical to
  the global run."* The optimization keeps that promise; it only stops paying
  for it eleven times.

### B2. `src/rag_v1/retrieval.py:127-162` — `lexical_search()`

The function that SYSTEM-E must be calling once per parent to obtain W=20
per-parent hits, because a single call with all ten `version_ids` applies one
global `LIMIT k` across the union and cannot yield W per parent.
**[UNVERIFIED — needs SYSTEM-E source]** — but it is the only way to get
per-parent W out of this API as written, and `run_exp012.py:201` shows the
`version_ids` call shape.

### B3. `src/rag_v1/retrieval.py:142-154` — the nested-connection N+1

```python
with connect() as conn, conn.cursor() as cur:
    cur.execute(_LEXICAL_SQL, {
        ...
        "chunk_set_id": snapshot_chunk_set(snapshot_id),   # <-- opens a SECOND connection
```

`snapshot_chunk_set()` (lines 50-68) opens its own `connect()`. Because the dict
literal is evaluated *inside* the outer `with`, every `lexical_search()` holds
two concurrent connections. `dense_search()` (line 204) and
`exact_identifier_search()` (line 274) have the identical defect.

`snapshot_chunk_set()` result is a pure function of `snapshot_id` over an
append-only table and is never cached.

### B4. `src/rag_v1/db.py:9-16` — `connect()`

Opens a fresh `psycopg.connect()` per call and runs `register_vector(conn)`
(a catalog lookup for the `vector` type OID). **No pool exists anywhere in the
codebase.**

### B5. `src/rag_v1/hierarchical.py`

`collapse_to_documents()` (32-47) and `fuse_document_rankings()` (50-83) are
pure in-memory functions over ≤300 hits — microseconds. Not a bottleneck.
`chunk_counts_for_documents()` (118-134) opens another connection per call;
it is diagnostic, not part of the retrieval path.

Note that this module's docstring says local ranking *"reuses the full-corpus
scores — the candidate set shrinks, the numbers attached to each candidate do
not."* SYSTEM-E's "local BM25 within each parent" is the same contract, which is
what makes §C safe.

### B6. `src/rag_v1/retrieval.py:216-417` — fusion

`rrf_fuse`, `rrf_fuse_regions`, `rrf_fuse_labelled` all call
`model_copy(deep=True)` on hits carrying full chunk text. Measured: **10.6 µs**
deep vs **1.8 µs** shallow per hit. At E's mean pool of 176.8 candidates that is
**1.87 ms/query**. See §5 below — this is *not* worth touching.

---

## C. Proposed score-preserving optimization

Three changes, strictly ordered, each independently revertible.

### C1 — Hoist the query-level CTEs out of the per-parent loop (largest win, lowest risk)

Add a sibling function that takes **all** parents and returns **W per parent** in
**one** statement, using `ROW_NUMBER() OVER (PARTITION BY version_id ...)` with
the *same* ordering expression that `_LEXICAL_SQL` uses for its `ORDER BY`.

This is score-preserving by construction: the `corpus` and `weighted` CTEs are
character-for-character unchanged and still full-corpus, so every chunk receives
the identical `score`; the partitioned window applies the identical total order
`(round(score::numeric,9) DESC, chunk_id)` that the current per-parent `LIMIT`
applies. `LIMIT W` over a total order and `row_number() <= W` over the same total
order select the same set in the same sequence.

Cost: 10 identical query-level computations collapse to 1, and 10 candidate
scans (10 × 54 = 540) collapse to 1 batched scan (**measured plan cost 155**).

### C2 — Materialize `n` and `avg_len` per `(snapshot_id, chunk_set_id)`

These are constants of the frozen snapshot. **Bitwise equivalence verified:**

```
n                = 14209
sum(length(...)) = 15590038          -- exact bigint, order-independent
avg(length(...))::float8      = 1097.194594975016
(sum::numeric/n::numeric)::float8 = 1097.194594975016
float8send(a) = float8send(b)  =>  t          -- BITWISE IDENTICAL
```

Store the exact integer `sum` and `count`, not the float. Then `avg_len` is
recovered by an exact numeric division whose float8 image is provably the same
value. (Note also: `length()` returns `integer` and `avg(integer)` accumulates
in `numeric`, so the current value is *already* order-independent — caching it
cannot change it. There is no parallel-aggregation hazard here.)

Effect: `29,041 → 537`, and the 142 MB TOAST read disappears from the hot path.

### C3 — Cache `df` per `(snapshot_id, chunk_set_id, term)`

`df` depends only on the term and the frozen snapshot. A process-level dict —
mirroring the existing, already-accepted `CachedQueryEmbedder` pattern in
`src/rag_v1/query_cache.py` — removes 626 units per repeated term. Across a
50-case run, function words and shared identifiers repeat heavily.

Keep the cache **keyed on the tsquery text**, not the raw term, so two raw terms
that normalize to the same `phraseto_tsquery` share one entry and cannot diverge.

### Explicitly NOT proposed

* Restricting the `corpus`/`weighted` CTEs to the routed documents. That is the
  cheapest-looking change on the page and it **changes every score**. It is
  already forbidden by `hierarchical.py`'s docstring and
  `retrieval.py:110-114`.
* Deriving local candidates from A's materialized pool — see §8 and §G1.
* Any change to `BM25_K1`, `BM25_B`, `rrf_k`, the 0.7/0.3 blend, or the CE.

---

## D. Patch-style diff (NOT APPLIED)

Written to `experiments/PERF-001/PERF-001-proposed.patch`. Summary of the
new SQL — note that the `terms`, `corpus` and `weighted` CTEs are copied
**verbatim** from `_LEXICAL_SQL` so a diff can prove they are unchanged:

```sql
-- ... terms / corpus / weighted CTEs: BYTE-IDENTICAL to _LEXICAL_SQL lines 71-98
scored AS (
    SELECT c.chunk_id, c.version_id, c.section_path, c.char_start, c.char_end, c.text,
           sum( w.idf * (%(k1)s + 1)
                / (1 + %(k1)s * (1 - %(b)s + %(b)s
                    * length(coalesce(c.search_text, c.text)) / w.avg_len)) ) AS score
    FROM chunk c
    JOIN corpus_snapshot_version sv ON sv.version_id = c.version_id
    JOIN weighted w ON c.search_vector @@ w.tq
    WHERE sv.snapshot_id = %(snapshot_id)s
      AND c.chunk_set_id = %(chunk_set_id)s
      AND c.version_id = ANY(%(version_ids)s::text[])   -- ALL parents, one pass
    GROUP BY c.chunk_id, c.version_id, c.section_path, c.char_start, c.char_end, c.text
),
ranked AS (
    SELECT scored.*,
           row_number() OVER (
               PARTITION BY scored.version_id
               -- identical to _LEXICAL_SQL's ORDER BY, line 122
               ORDER BY round(scored.score::numeric, 9) DESC, scored.chunk_id
           ) AS local_rank
    FROM scored
)
SELECT chunk_id, version_id, section_path, char_start, char_end, text, score, local_rank
FROM ranked
WHERE local_rank <= %(w)s
ORDER BY version_id, local_rank;
```

Python side (`src/rag_v1/retrieval.py`), sketch:

```python
_CHUNK_SET_CACHE: dict[str, str] = {}

def snapshot_chunk_set(snapshot_id: str, conn=None) -> str:
    """Cached, and able to reuse a caller's connection.

    The mapping is a property of a frozen, append-only snapshot row, so a
    process-level cache cannot go stale within a run.
    """
    if snapshot_id in _CHUNK_SET_CACHE:
        return _CHUNK_SET_CACHE[snapshot_id]
    ...  # existing body, using `conn` when supplied

def local_lexical_search_batch(
    query: str, snapshot_id: str, version_ids: list[str], w: int
) -> dict[str, list[SearchHit]]:
    """Top-`w` BM25 hits *within each* parent, in one statement.

    Equivalent to calling ``lexical_search(query, snapshot_id, w, [v])`` once
    per ``v`` — same scores, same candidates, same order — but the full-corpus
    term statistics are computed once instead of ``len(version_ids)`` times.
    """
    terms = query_terms(query)
    if not terms or not version_ids:
        return {v: [] for v in version_ids}
    with connect() as conn, conn.cursor() as cur:
        chunk_set_id = snapshot_chunk_set(snapshot_id, conn)     # no 2nd connection
        cur.execute(_LOCAL_BATCH_SQL, {...})
        rows = cur.fetchall()
    out: dict[str, list[SearchHit]] = {v: [] for v in version_ids}
    for r in rows:
        out[r[1]].append(SearchHit(..., rank=r[7], retriever="lexical"))
    return out
```

`rank` is set from `local_rank`, reproducing the 1..W numbering the per-parent
`LIMIT` produced. Parents with no matching chunk yield `[]`, exactly as the
current `LIMIT` path does.

---

## E. Complexity before / after

Let `P` = parents (10), `T` = distinct query terms (p50 11), `N` = snapshot
chunks (14,209), `M` = mean chunks per routed parent (measured: mean 70.3,
median 27.0, max 2,351), `Q` = queries in the run (50).

| | before | after C1 | after C1+C2+C3 |
|---|---|---|---|
| full-corpus heap+TOAST scans | `P` per query = **10** | 1 | **0** (materialized) |
| full-corpus `df` index scans | `P·T` = **110** | `T` = 11 | ≤ `T`, amortized → ~0 warm |
| candidate scans | `P` scans of `M` | 1 scan of `P·M` | 1 scan of `P·M` |
| DB round trips | `2P` = **20** | **1** | **1** |
| DB connections | `2P` = **20** | **1** | **1** |
| plan cost / query | **359,760** | 36,078 | **7,574** cold / ~155 warm |
| over `Q=50` queries | 17.99 M | 1.80 M | 0.38 M cold |

Asymptotically: `O(P·(N + T·N + M))` → `O(N + T·N + P·M)` → `O(T·N + P·M)` →
`O(P·M)` warm. The `P` factor is removed from the dominant term entirely.

---

## F. Equivalence-test checklist

An optimization is score-preserving only if **all ten** pass. Nos. 1–5 are the
blocking gate; C1 alone must pass all of them before C2/C3 are attempted.

1. **Per-parent candidate identity.** For every query in the equivalence corpus
   and every parent, `[h.chunk_id for h in new[v]] == [h.chunk_id for h in
   lexical_search(q, snap, W, [v])]` — as an **ordered list**, not a set.
2. **Bitwise score identity.** `struct.pack('<d', new.score) == struct.pack('<d',
   old.score)` for every hit. Not `math.isclose`, not `round(…, 9)` — the raw
   float8 bits. A tolerance test would hide exactly the IDF drift this audit
   exists to prevent.
3. **Rank identity.** `new[v][i].rank == i + 1` and equal to the old rank, so the
   RRF contribution `1/(k + rank)` is unchanged downstream.
4. **`avg_len` and `n` bitwise.** `float8send(cached_avg_len) =
   float8send(recomputed_avg_len)` and `cached_n = recomputed_n`, asserted in SQL
   against the live snapshot. Already verified once above for `cs_v1_control`:
   `n=14209`, `sum=15590038`, `avg_len=1097.194594975016`, `bitwise = t`.
5. **`df` bitwise per term.** For every term in the equivalence corpus,
   `cached_df = recomputed_df` exactly, and cache keys are tsquery text so two
   raw terms normalizing together cannot split.
6. **Union membership identity.** The set *and* the multiplicity of new local
   members added to the A pool is unchanged, and `mean new union members` still
   reports **82.7/query**.
7. **Final ranking identity.** The post-RRF, post-blend, post-CE top-10 is an
   identical ordered list of chunk ids for every case.
8. **Metric identity.** Candidate `Recall@100 = 45/50`, strict `Recall@10 =
   40/50`, span recall `.80`, `MRR = .5969`, document recall `.92` — reproduced
   **exactly**, not within tolerance.
9. **Empty and degenerate parents.** A parent with zero matching chunks returns
   `[]`; a parent with fewer than W matches returns all of them; the single
   1-chunk document and the 2,351-chunk document both behave as before.
10. **Determinism across repeat runs.** The same call twice in one process and
    once in a fresh process yields byte-identical JSON. This also guards the
    tie-break at `retrieval.py:122`, which exists precisely because BM25 ties
    are common.

Practical note: run 1–5 on **V1 development questions**, not on V2-DEVSET-001.
Equivalence is a property of the code, not of the benchmark, so it does not need
— and should not spend — devset exposure. Only test 8 requires the devset, and
it is a reproduction check, not a measurement.

---

## G. Risks that an "optimization" would subtly change scores or ranking

**G1 — Deriving local hits from A's already-materialized pool. HIGH; would
destroy the mechanism.** See §8. This is the most attractive-looking and most
dangerous idea available.

**G2 — Restricting the `corpus`/`weighted` CTEs to routed documents. HIGH.**
It looks like the same optimization as C1 and is the opposite of it. `n` would
fall from 14,209 to ~703, `avg_len` would shift, and every `idf` would change.
Every score changes. Guarded by test 4/5 and by the comments already in the file.

**G3 — Caching `avg_len` as a float rather than as `(sum, count)`. LOW but
real.** Round-tripping the float through JSON, a config file, or a `numeric`
column can lose the last bit. Store the exact integers; derive the float. Test 4.

**G4 — Window-function ordering drift. MEDIUM if the expression is retyped.**
`ORDER BY score DESC` inside the window is *not* the same as
`ORDER BY round(score::numeric, 9) DESC, chunk_id`. Ties are common and the
rounding is what makes them resolve on `chunk_id`. Copy the expression
character-for-character; test 1 catches it.

**G5 — `LIMIT` vs `row_number()` at the boundary. LOW.** Identical only because
the ordering key is total. It is total here (`chunk_id` is the PK). If anyone
ever drops the `chunk_id` tie-break, the two diverge silently at rank W.

**G6 — Batching changes the plan for the candidate scan. LOW, verified.**
`ANY(ARRAY[10 parents])` plans as a `Bitmap Heap Scan` (cost 155.28) where a
single parent plans as an `Index Scan` (cost 54.08). Different node, same rows,
same scores — the scan shape cannot alter arithmetic. Test 2 covers it.

**G7 — `search_text IS NULL` for all of `cs_v1_control`. LOW, but do not
exploit it.** It is true today (verified: 14,209 of 14,209), which means
`coalesce(search_text, text) ≡ text`. Simplifying the expression on that basis
would break silently on any enriched chunk set. Keep the `coalesce`.

**G8 — Connection reuse changing transaction visibility. LOW.** Passing one
connection where two were used changes snapshot isolation semantics in
principle. The corpus is frozen and read-only, so in practice nothing can
differ; test 10 covers it.

**G9 — Batching changes float accumulation order inside `sum()`. LOW-MEDIUM,
must be checked not argued.** `sum(float8)` accumulates in scan order, and C1
changes the scan. Per-chunk this is a sum over matched terms only (typically
2–5 values), so reordering is unlikely to move a bit — but "unlikely" is not
"proven". Test 2 is the proof, and it is why test 2 must be bitwise. If it ever
fails, the fix is to accumulate in `numeric` in both the old and new paths,
which is exact and order-independent.

---

## H. Recommended implementation order

Do these strictly in sequence. Each step ends at a green equivalence gate, and
no step begins until the previous one is green.

1. **Cache `snapshot_chunk_set()` and thread the connection through.**
   Removes the nested second connection in `lexical_search`, `dense_search` and
   `exact_identifier_search`. ~50% of connection overhead, zero SQL change, zero
   score risk. Gate: tests 1–3, 10.
2. **C1 — the batched per-parent window query.** The single largest win
   (**~10×** on the local stage) and the one whose equivalence argument is
   purely structural. Gate: **the full checklist, tests 1–10.** Freeze here and
   record the equivalence artifact; this alone may satisfy Track 1.
3. **C2 — materialize `(n, sum_len)` per `(snapshot_id, chunk_set_id)`.** Ship
   as `sql/005_bm25_corpus_stats.sql`, following the existing `sql/00N_*.sql`
   convention, with a `CHECK`-style verification query in the migration itself.
   A further **~5×** on what remains. Gate: test 4 first, then 1–10.
4. **C3 — the `df` cache.** Smallest win, and the only one with cross-query
   state, so it goes last where a failure is easiest to attribute. Gate: test 5
   first, then 1–10.
5. **Only then, Track 2 (`L = 10/20/40`).** Track 2 changes *which* candidates
   survive; steps 1–4 must be proven not to. Running them together would make an
   equivalence failure and a cap effect indistinguishable.

**Optional, measure before adopting:** a stored generated column
`search_len int GENERATED ALWAYS AS (length(coalesce(search_text, text))) STORED`
plus `CREATE INDEX ON chunk (chunk_set_id, version_id) INCLUDE (search_len)`
would let `avg_len` come from an index-only scan without any cache at all. It is
a *schema* change to a frozen corpus DB, and although it cannot alter chunk
content or any hash (`search_vector` is already such a column, so there is
precedent), C2 achieves the same effect with no DDL. Prefer C2; keep this on the
shelf.

**Do not do without a separate authorization:** connection pooling. It is a
genuine ~20 ms × N win, it touches every experiment's timing path, and it should
not ride along inside a Track-1 equivalence change.

---

## Answers to the ten numbered questions

**1. Which query-level BM25 calculations are recomputed for every parent?**
All of them. The `corpus` CTE (`n`, `avg_len`) and the `weighted` CTE
(per-term `df`, hence every `idf`) are recomputed in full on every
`lexical_search()` invocation. Together they are **99.85%** of a single-parent
call's plan cost. Only the ~54-unit scoring scan is genuinely per-parent.

**2. Which full-corpus IDF values / CTEs already exist in SYSTEM-A and can be
reused?** All of them, and *reuse is mathematically required, not merely
permitted*: `retrieval.py:110-114` and `hierarchical.py`'s docstring both state
that local scoring uses full-corpus statistics. SYSTEM-A's global BM25 call for
the same query computes the identical `n`, `avg_len` and per-term `idf`. Those
three are the reuse surface. **SYSTEM-A's ranked hit list is *not* part of it**
— see 8.

**3. Can reuse be mathematically identical?** Yes, and for `avg_len` it is
already **proven bitwise** on the live snapshot (`float8send` equality, §C2).
`df` is an exact integer count. `idf` is a pure function of `n` and `df`. The
per-chunk score is a pure function of `idf`, `avg_len`, `k1`, `b` and the
chunk's own length. Nothing in the chain depends on how many times it was
evaluated or on which parents were in scope.

**4. Database / Python N+1 behavior?** Three, in descending order:
 (a) **the per-parent query loop** — `P` executions of a query whose cost is
 99.85% parent-independent;
 (b) **the nested connection** — `snapshot_chunk_set()` opens a second
 `connect()` inside `lexical_search`'s own `with` block
 (`retrieval.py:142-154`; same in `dense_search:204`,
 `exact_identifier_search:274`), so `P` parents cost `2P` connections at a
 measured 20.6 ms each ≈ **412 ms/query**;
 (c) **no connection pool exists** — `db.py:9-16` opens and closes a raw
 `psycopg.connect()` every time, plus a `register_vector()` catalog lookup.

**5. Candidate materialization / deduplication overhead?** **Measured and
negligible — do not optimize it.** `model_copy(deep=True)` on hits carrying full
chunk text costs 10.6 µs vs 1.8 µs shallow; at E's 176.8-candidate mean pool
that is **1.87 ms/query, ~0.02% of E's 16.6 s**. The `rrf_fuse_regions` bucket
and merge is `O(n log n)` over ≤300 hits. The one *database*-side materialization
cost worth noting is that the scoring `SELECT` carries `c.text` through its
`GROUP BY` and sort (`width=946`); for `P·M ≈ 700` rows that is moderate and C1
does not make it worse. Reporting this as a non-finding is deliberate: it is the
kind of thing that looks expensive in a profile and is not.

**6. CE batching overhead from the enlarged union?** **Cannot be audited — no
cross-encoder exists in this repository.** `systems.py:35` sets
`"cross_encoder": None`, and EXP-015 concluded
`NO_PRETRAINED_CROSS_ENCODER_AVAILABLE`. What can be said from the reported
numbers alone: the pool grows **94.1 → 176.8** (+88%), so if CE cost is linear
in pool size the CE contribution to the 10,780 ms local-stage delta scales by
~1.88×. Whether that is 200 ms or 8,000 ms depends entirely on the CE's batch
size, sequence length and backend, none of which are visible here. **This is the
one question I cannot answer, and it should be answered with a real profile of
the SYSTEM-E CE stage rather than estimated.** If it turns out CE dominates,
Track 1 as scoped (BM25 optimization) will not reach the latency target and
Track 2's caps become the operative lever — worth knowing before Track 1 starts.

**7. Safe query-level caching opportunities?** Three, all keyed on frozen
inputs: `(snapshot_id) → chunk_set_id`; `(snapshot_id, chunk_set_id) → (n,
sum_len)` stored as exact integers; `(snapshot_id, chunk_set_id, tsquery_text) →
df`. All three are pure functions of an immutable snapshot. The codebase already
accepts this pattern for query embeddings (`query_cache.py`), including its
fingerprint-in-the-key discipline — mirror it by putting `snapshot_id` and
`chunk_set_id` in every key so a cached statistic cannot outlive its corpus.

**8. Can local scores be derived from already-materialized A BM25 results?**
**Scores: yes. Candidates: no — and doing so would destroy the mechanism
EXP-018 supported.** A chunk's local score *is* its global score, identically,
by construction. But A returns a globally-ranked top-`k`, and a chunk ranked
500th globally can be 3rd within its parent. Selecting each parent's top-W from
A's pool silently truncates to whatever A already found — which is precisely the
set SYSTEM-E exists to go beyond. It would eliminate most of the **82.7 new
union members/query** and would very likely un-rescue **V2D-11, V2D-33, V2D-34
and V2D-43**, the four pool rescues. The result would still be internally
consistent and would still pass a naive "scores match" test. It is the single
most dangerous optimization on this list, and equivalence test 1 (ordered
per-parent candidate identity) is what catches it.

**9. Indexes or database changes that reduce runtime without altering scores?**
In order of value:
 (i) a `bm25_corpus_stats(snapshot_id, chunk_set_id, n, sum_len)` table (C2) —
 removes a 142 MB TOAST + 310 MB heap read from the hot path;
 (ii) optionally a `bm25_term_df(snapshot_id, chunk_set_id, tsquery_text, df)`
 table if the df cache should survive across processes;
 (iii) optionally a stored `search_len` generated column plus a covering index,
 which makes `avg_len` index-only with no cache — but it is DDL on a frozen
 corpus and C2 gets there without it.
 Existing indexes are already adequate for the parent-restricted scan:
 `idx_chunk_set_version` and `idx_chunk_search_vector` are both used
 (`BitmapAnd` in the df subplan, `Index Scan` in the candidate scan). **No new
 index is needed for C1.** Also worth noting: `shared_buffers = 128 MB` against a
 310 MB heap is why the repeated scan is so punishing — raising it would mask the
 problem without fixing it, and would change nothing about scores. Fix the
 repetition, not the buffer.

**10. Exact deterministic equivalence checks required?** The ten in §F, with
these three non-negotiable properties: comparisons on **float8 bits**, not
tolerances; **ordered lists**, not sets; and **exact metric reproduction**, not
"within noise". Plus the discipline point — run the equivalence gate on V1
development questions, so proving the code correct costs zero V2-DEVSET-001
exposure.

---

## Bottom line

The local stage does **~0.15%** local work. `avg(length(coalesce(search_text,
text)))` over all 14,209 chunks — a constant of the frozen snapshot that depends
on neither the query nor the parent — is **96%** of a single-parent local BM25
query, and SYSTEM-E pays it once per parent, reading a 142 MB TOAST relation
through a 128 MB buffer cache each time.

Track 1's goal is reachable without touching a single scoring expression. The
`corpus` and `weighted` CTEs stay byte-identical and stay full-corpus; they are
simply computed once per query instead of once per parent, and the ten
per-parent `LIMIT` queries become one partitioned window. Everything that
determines a score is unchanged, which is what makes exact equivalence provable
rather than merely likely.

The two things to watch: the tempting shortcut in question 8 would pass a
careless test while deleting the mechanism, and the CE contribution (question 6)
is unmeasurable from here and could be large enough to change what Track 1 can
deliver.
