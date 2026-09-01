# PERF-002 — cross-encoder score-preserving latency audit

**Read-only. No patch applied. No E-L10 validation, no freeze, no holdout.**

Source audited: `grok/ce-latency-handoff` @ **7661ac5**, inspected in a detached
worktree. CE artifact sha256 re-verified against the preregistered value:
`5d3e70fd…c1d4d4a` ✓. Model confirmed `BertForSequenceClassification`,
`logits [batch, 1]`, 6 layers / hidden 384 / 12 heads / FFN 1536 — MiniLM-**L6**,
settling H3 as the handoff states.

**Everything below was measured independently on this container** (4-core Xeon
@2.80 GHz, AVX-512+VNNI, onnxruntime 1.29.0, tokenizers 0.23.1 — the same
library versions as EXP-018B). Grok's audit was read *after* my own measurements
were taken, and is treated as a claim to check, not as input.

---

## Headline

Two results matter, and they point in opposite directions.

**1. Grok's bitwise-identity claim is correct.** I doubted it and I was wrong.
All ten levers tested — batch size, thread count, pad width, bucketing,
`fast=True` end-to-end — return **bit-identical logits**, including the extreme
case of width 24 versus width 512. So the equivalence criterion for this work is
**bitwise**, not a tolerance. §E is stronger than the brief assumed it could be.

**2. `fast=True` is the wrong bundle, and on a 4-core host it is a
regression.** It couples a machine-*independent* 2.07× win (length-bucketed
`pad="batch"`) with a machine-*dependent* choice (`threads=8`) that is a **0.68×
regression here**. Measured on this box, `fast=True` delivers 1.22× where
bucketing alone delivers 2.07×. **The two levers must be separated.**

---

## A. Exact CE code locations

| What | Location |
|---|---|
| CE class | `experiments/EXP-015/scripts/cross_encoder.py::CrossEncoderReranker` |
| Session + tokenizer construction | same file, `__init__` lines 37–89 |
| `SessionOptions` | lines 69–74 — `intra_op_num_threads=threads` (default 4), `inter_op_num_threads=1`, `providers=["CPUExecutionProvider"]`, graph opt left at ORT default `ORT_ENABLE_ALL` |
| Fixed 512 padding | lines 81–84 — `enable_padding(length=MAX_LENGTH)` |
| Truncation | line 77 — `enable_truncation(512, strategy="longest_first")` |
| Batch loop (the hot path) | lines 108–121, `_score_in_order` |
| ONNX call | line 119 — `self._session.run(None, feeds)` |
| Bucketing path | lines 98–106, `_score_bucketed` |
| Rerank + tie-break | lines 124–141 — `sort(key=(-score, a_rank, chunk_id))` |
| E-L10 construction | `experiments/EXP-018B/scripts/run_exp018b.py:341` — `ce = CrossEncoderReranker()`, **no kwargs** |
| CE call 1 (A-pool ≈94) | `run_exp018b.py:391` |
| CE call 2 (extras ≈10) | `run_exp018b.py:409` |
| L=10 CE estimate | `run_exp018b.py:697` |

### Answers to the ten inspection questions

1. **Session creation.** Created **once per process** (line 72), reused across
   all 50 queries. Measured construction cost **859 ms** (sha256 verify +
   `InferenceSession` + tokenizer load) — paid once, not per query. Tokenizer
   objects likewise reused. **Not a bottleneck. Grok is right; my H2 is dead.**
2. **Batching.** `batch_size=16`, ~7 `session.run` calls per query at union
   104.1. Not per-candidate. **My H1 is dead.**
3. **Tokenization.** Query *is* re-tokenized for every pair (`encode_batch`
   receives `(query, passage)` tuples). Measured cost: **1.03% of CE time.**
   No repeated tokenizer init. Padding: fixed 512. Truncation: `longest_first`
   512, correct.
4. **Tensor construction.** Three `np.array(..., dtype=np.int64)` per batch,
   contiguous, no dtype churn, no redundant copies. Measured: **0.09%.**
5. **ORT config.** intra 4 / inter 1 / CPU EP fp32 / `ORT_ENABLE_ALL`. Sane.
   The only lever here is thread count — see §D2.
6. **Sequence lengths.** Measured on 400 `cs_v1_control` passages: mean
   **237.8**, p50 **172**, p90 512, **26.2% already at 512**. **53.6% of all
   token slots under fixed-512 padding are PAD.** (Independently reproduces
   Grok's mean 237 / 26.3%.) Length-bucketed batching is **exactly**
   score-preserving — verified bitwise, §E.
7. **Query-side caching.** Nothing worth caching: total tokenization is 1.03%,
   so a perfect query-token cache saves **<1%**.
8. **Candidate-side caching.** Same ceiling. Pair tokenization depends on the
   query, so per-passage caching cannot be reused across queries without
   changing pair construction. **Not a lever.**
9. **Execution provider.** `CPUExecutionProvider`, fp32, and it *is* being used
   efficiently in the sense that 98.87% of CE time is inside the ORT kernels.
   The inefficiency is not the provider — it is *what is being fed to it*.
10. **Parallelism.** `inter_op=1`, intra-op only. Safe parallel execution is
    possible and bitwise-safe (verified), but is a pure function of the host's
    real core count — see §G2.

---

## B. Measured latency decomposition

104 pairs (E-L10 mean union 104.1), one query, warmed, this container:

| Component | BASELINE pad=512 b16 t4 | share | BUCKETED pad=batch b16 t4 | share |
|---|---:|---:|---:|---:|
| pre-pass tokenize (bucketing only) | 0.0 ms | 0.00% | 49.8 ms | 0.89% |
| tokenize | 94.3 ms | 1.03% | 104.1 ms | 1.87% |
| numpy pack | 8.6 ms | 0.09% | 5.9 ms | 0.11% |
| **ONNX inference** | **9087.0 ms** | **98.87%** | **5408.3 ms** | **97.12%** |
| postprocess / unpermute | 0.4 ms | 0.00% | 0.4 ms | 0.01% |
| batching / loop overhead | 0.2 ms | 0.00% | 0.2 ms | 0.00% |
| **total** | **9190 ms** | | **5569 ms** | |

Batch widths — baseline `[512 ×7]`; bucketed `[34, 86, 168, 310, 512, 512, 512]`.
(Grok measured `[33, 85, 164, 309, 512, 512, 512]`; the small offset is my
19-token query vs theirs. Independent reproduction.)

Session construction **859 ms, once per process** — excluded from per-query cost,
correctly.

> **This box is ~1.55× slower than the EXP-018B box** (my 8638 ms baseline vs
> their 5571 ms for the same 104-pair pad-512 pass). Absolute milliseconds here
> are **not** comparable to EXP-018B's. **Ratios are.** Every projection in §H
> is built from ratios only.

---

## C. Dominant bottleneck

**ONNX inference on padding.** 98.87% of CE time is inside `session.run`, and
**53.6% of the tokens fed to it are `[PAD]`**. Attention is O(n²) in width, so a
172-token pair padded to 512 costs roughly 3× the FFN work and ~9× the attention
work of the same pair at its true width.

Everything the brief asked me to look at in items 3, 4, 7 and 8 —
tokenization, tensor construction, query-side caching, candidate-side caching —
sums to **1.12% of CE time**. Perfect elimination of *all of it* would save
about 100 ms of 5904 ms. **These are not levers, and this is a finding, not an
omission.** Grok reached the same conclusion; I confirm it with a direct
decomposition.

One structural note: the E-L10 CE figure of **5903.9 ms is an estimate, not a
measurement** (`run_exp018b.py:697` interpolates
`CE_D + (CE_E − CE_D)·(n_additive_L / n_additive_E)`). The interpolation is
reasonable and I am not disputing it, but every projection downstream inherits
its error, including §H.

---

## D. Score-preserving optimizations, ranked

Measured on 104 pairs, this container, all **bitwise identical** to
`CrossEncoderReranker()`:

| # | Change | ms | speedup | bitwise | machine-dependent? |
|---|---|---:|---:|:---:|:---:|
| — | baseline `CrossEncoderReranker()` | 8638 | 1.00× | — | — |
| **D1** | `pad="batch", bucket_by_length=True`, **threads unchanged** | **4168** | **2.07×** | ✅ | **no** |
| D1b | same, `batch_size=1` | 3681 | 2.35× | ✅ | probably |
| D3 | one `score_pairs` on the union instead of 94+10 | — | see below | ✅ | no |
| D2 | `threads=8` alone | 12686 | **0.68×** | ✅ | **YES** |
| — | `fast=True` (bundles D1 + threads=8) | 7096 | 1.22× | ✅ | **YES** |
| — | `pad="batch"` unsorted | 8161 | 1.06× | ✅ | no |

**D1 — length-bucketed `pad="batch"`. Ship this one.** 2.07× here; Grok's own
numbers imply ~2.16× on their box (deriving bucketing alone from their
5571 / 3728 / 1729 triple). The agreement across two different CPUs is what
makes it safe to project. Machine-independent, bitwise, biggest single win.

**D3 — merge the two CE calls.** `run_exp018b.py` scores the A-pool (≈94) and
the extras (≈10) in separate `score_pairs` calls, so bucketing currently sorts
94 and 10 *separately* and the 10-extras call gets almost no benefit. Merging
lets D1 bucket all 104 together. Bitwise-safe because batch composition provably
does not affect logits (§E, rows 1–3). Grok estimates ~250 ms standalone; its
real value is that it **raises D1's ceiling**. Call-site change only.

**D1b — `batch_size=1` with bucketing** gave a further 14% here (2.35× vs
2.07×), because every pair then gets its exact width instead of its bucket's
width. Grok did not test this combination. Worth one measurement on the target
box before adopting; the gain may be an artifact of this box's cache size.

**D2 — `threads=8`. Do not ship as part of a bundle.** On this 4-core host it is
a **32% regression**. On Grok's host it was a 1.49× gain. It is not wrong — it
is *a function of the deployment machine's real core count*, and it must be set
to match that machine, measured there, not inherited from a flag name.

**Explicitly not worth pursuing** (each bounded above by the §B decomposition):
query-token caching, passage-token caching, IO binding, `pad_to_multiple_of`,
larger batches. And out of scope by constraint: int8/quantization, model swap,
distillation.

---

## E. Equivalence-test plan

**Bitwise identity is achievable.** Measured, 10/10 configurations, `max|Δ| =
0.000e+00` on exact bit patterns (`struct.pack("<d", x)`, so −0.0 would show as
a difference and NaN would be visible), ranks identical in every case:

| Configuration vs `CrossEncoderReranker()` | bitwise | ranks |
|---|:---:|:---:|
| batch 1 / 16 / 32 | ✅✅✅ | same |
| threads 1 / 4 / 8 | ✅✅✅ | same |
| `pad="batch"` unsorted | ✅ | same |
| `pad="batch"` bucketed, b16 and b1 | ✅✅ | same |
| `fast=True` end-to-end | ✅ | same |
| **width 24 vs width 512** (8 shortest pairs) | ✅ | same |

**Why it holds** — worth stating, because it is the reason this is safe and not
luck. `attention_mask` sets padded positions to exactly `0.0` after softmax, and
adding exact zeros to a float accumulation in sequence order changes nothing.
MLAS parallelizes GEMM over M/N tiles rather than splitting the K reduction, so
each output element's summation order is fixed regardless of thread count or
batch shape. Neither padding nor threading perturbs a single bit.

**Because logits are bit-identical, ranks are identical by construction** — the
`(-score, a_rank, chunk_id)` tie-break at `cross_encoder.py:128` is never even
exercised differently. That removes the entire class of near-tie reordering
risk that a tolerance-based criterion would have left open.

### The gate to run before flipping anything

1. **Bitwise logit identity**, exact bit patterns, on ≥104 real E-L10 candidate
   pairs — not `math.isclose`, not `np.allclose`.
2. **Ordered candidate identity** per query after un-permutation.
3. **Final rank identity** for the top-10 after blend.
4. **Metric identity, exact**: candidate R@100 = 44/50, strict R@10 = 40/50,
   span R@10 = .8000, MRR = .5956, doc recall = .9200, union mean 104.1.
5. **Determinism**: identical twice in-process and once in a fresh process.
6. **Run the gate on the deployment host**, not only on the dev box — see G1.

Note the honest limitation, which Grok also flagged: **EXP-018B stores no CE
logits**, so there is no stored-logit replay gate. Gate 1 must be run as a
paired A/B in one process. Gates 4's metrics come from the stored results and
can be compared without re-running retrieval only if the CE change is proven
bitwise first — which is exactly why gate 1 comes first.

---

## F. Proposed changes (NOT APPLIED)

The code for D1 **already exists** on the branch as opt-in kwargs. So the
proposal is mostly about *how it is enabled*, plus one call-site change.

**F1 — do not use `fast=True`.** Split the bundle:

```python
# experiments/EXP-018B/scripts/run_exp018b.py:341  (when authorized)
- ce = CrossEncoderReranker()
+ ce = CrossEncoderReranker(pad="batch", bucket_by_length=True)   # D1: 2.07x, bitwise
+ # threads deliberately left at the default; set it from the host's real core
+ # count, measured on that host. threads=8 is a 0.68x REGRESSION on 4 cores.
```

**F2 — merge the two CE calls so D1 can bucket all 104 together** (`run_exp018b.py`
391 / 409). Score `fused_e` once, then read both `d_rows` and `e_rows` out of the
one `ce_by_id` map, instead of scoring `a_pool` and then `new_hits`:

```python
- a_ce = ce.score_pairs(q, [h.text for h in a_pool])
- ...
- new_scores = ce.score_pairs(q, [h.text for h in new_hits])
+ all_hits = a_pool + [h for h in fused_e if h.chunk_id not in {x.chunk_id for x in a_pool}]
+ all_scores = ce.score_pairs(q, [h.text for h in all_hits])
+ ce_by_id = {h.chunk_id: float(s) for h, s in zip(all_hits, all_scores, strict=True)}
```
This changes the two `latency_ms` keys' meaning, so it needs a separate timer
decision — flagged, not decided here.

**F3 — a guard worth adding to the class.** `pad="fixed"` with
`bucket_by_length=True` pays the extra tokenization pass (49.8 ms) for zero
benefit, since every width is 512 anyway. Either warn or make bucketing imply
`pad="batch"`.

---

## G. Risks

**G1 — bitwise identity is a property of *this ORT build on this CPU class*,
not a theorem.** It held on two independent machines (mine, AVX-512; Grok's),
same ORT 1.29.0. A different ORT version, a different `providers` list, or a CPU
without AVX-512 could select different kernels. **Mitigation: re-run the §E gate
on the deployment host.** This is the single most important residual risk, and
it is cheap to close.

**G2 — `threads` is machine-dependent and `fast=True` hides that.** Measured
0.68× on 4 cores, 1.49× on Grok's 8. The `EXP-018B-results.json` `environment`
block records OS, Python and library versions but **not core count**, so no
stored artifact substantiates "8-core". Anyone reading `fast=True` as "the fast
option" will ship a regression on a smaller host.

**G3 — D1's benefit depends on the length distribution and will shrink as
candidates get longer.** 26.2% of pairs are already at 512 and can never be
bucketed cheaper. If V2 chunking changes, re-measure; the gain is not a constant.

**G4 — bucketing reorders work but not results.** `_score_bucketed` un-permutes
via `order`, verified bitwise. The residual risk is a future edit breaking the
un-permutation silently — gate 2 (ordered candidate identity) is what catches
it, and it must stay in the suite.

**G5 — 5903.9 ms is interpolated, not measured** (§C). §H's absolute figures
inherit that.

**G6 — my absolute milliseconds are not EXP-018B's.** This box is ~1.55×
slower. Only ratios transfer.

---

## H. Expected realistic latency range

Ratios only, applied to the stored E-L10 figures (A 358.5 + local BM25 192.4 +
CE 5903.9 = 6454.8 ms). **These are projections to verify, not results.**

| Scenario | CE ms | E-L10 total | note |
|---|---:|---:|---|
| current | 5903.9 | 6454.8 | stored |
| **D1 alone** (bucketing, threads unchanged) | **≈2810** | **≈3360** | 2.07–2.16× measured on two boxes; **machine-independent** |
| D1 + D3 (merged call) | ≈2600 | ≈3150 | D3 raises D1's ceiling |
| D1 + D3 + threads matched to a true 8-core host | ≈1750–1850 | ≈2300–2400 | agrees with Grok's ≈2380 |
| `fast=True` on a **4-core** host | ≈4840 | ≈5390 | the trap — barely better than today |

**The defensible headline is D1 alone: CE ≈5904 → ≈2810 ms, E-L10 ≈6455 →
≈3360 ms, a ~1.9× end-to-end improvement with bit-identical logits and ranks,
independent of the deployment machine.** Anything beyond that is real but must
be earned by measuring the target host's core count, not by setting a flag.

---

## Constraints observed

No patch applied. E-L10 not validated, not frozen, still constructs
`CrossEncoderReranker()` with defaults. Holdout not opened. SYSTEM-D unchanged.
CE model, tokenizer, truncation and scoring semantics unchanged. Blend weights
and RRF unchanged. EXP-017 and EXP-019 not run. V2-DEVSET-001 **not scored** —
all microbenchmarks used `cs_v1_control` passages with a synthetic query, which
is the same isolation Grok used. No timers added to the frozen E-L10 path. No
file on `grok/ce-latency-handoff` modified; it was inspected in a detached
worktree. The frozen Windows checkout (e65912a, 2026-08-25) is untouched and
unreachable from here.

**Stop for ChatGPT / Grok review.**
