# EXP-011 preregistration — recorded BEFORE any query transform was written

## 1. Hypothesis

The remaining retrieval failures are partly caused by mismatch between natural
user questions and the forms lexical and semantic retrievers rank most
effectively. A controlled query representation may improve retrieval while
preserving the user's original intent.

EXP-011 must be able to falsify this. Query formulation is **not** assumed to help.

## 2. Why the query side, and why now

Every experiment so far changed the *document* representation. EXP-010 closed that
line decisively: truncation was eliminated completely (23.22% of chunks → 0%,
corpus token coverage 0.7610 → 1.0000) and retrieval moved by **Δ0.000**, with
zero rescued and zero regressed. Its decisive measurement was that **21 of 22
expected answers were already visible** to the encoder.

So the remaining failures are ranking failures, not visibility failures: the
retriever reads the right text and scores it below competing text. The query has
been a raw user-question string since EXP-000 and is the one major variable never
tested.

## 3. Frozen — the entire document and retrieval stack

Corpus, document versions, control chunk boundaries, chunk text, enrichment
(none), table and code handling, BM25 `k1=1.2` / `b=0.75` on the `simple`
configuration, the transformer model and weights and tokenizer, the 512-token
window, **the stored document embeddings**, embedding normalization, cosine
metric, exact dense search (no ANN), RRF pool 50 / `rrf_k` 60 / `top_k` 10, the
evidence anchors, and the golden questions.

**Only the query embedding may differ**, and only because the query text differs.
Document vectors are reused byte-for-byte from the EXP-009/EXP-010 control @512
build (`emb_e7d4183fd6eb878ae2fdf080efb6861e`, fingerprint `bd95feaeacf98559`).

## 4. Design rule: the original query is never replaced

The raw user question always remains one retrieval representation. A transformed
query is only ever an **additional view**, never a substitute. Every multi-view
cell fuses independent ranked lists rather than concatenating query text.

This is a safety property, not a performance choice: it bounds the damage a bad
transformation can do.

## 5. Leakage controls

A query transform receives **only the raw question string** and general rules. It
never receives, and must not be able to derive:

expected answer · expected evidence · evidence section path · expected document ·
retrieval result labels · golden annotations · whether the baseline succeeded.

Concretely enforced:

* the transform module imports nothing from the eval package and is a pure
  function of the query string;
* a test asserts the module's source contains no reference to the golden set;
* a test asserts no golden question or evidence string is hardcoded in it;
* transforms are applied to arbitrary held-out strings in tests, not only to the
  20 questions.

**No per-question rules.** If a transformation only works because it was written
after looking at a specific golden question, it is invalid.

## 6. Query representations (maximum three)

| view | kind | description |
|---|---|---|
| `raw` | none | the user's question, unchanged |
| `normalized` | deterministic | conversational scaffolding removed, identifiers/numbers/providers preserved exactly |
| `structured` | deterministic | retrieval concepts extracted (entity, operation, asked property) and rendered as one query |

Budget is capped at **3 views per user query**. This experiment tests alignment,
not brute-force query multiplication.

## 7. Preservation guarantees (tested)

Never altered or dropped by any transform:

* exact technical identifiers — `max_tokens`, `max_output_tokens`, `top_p`,
  `tool_choice`, `client.messages.create`;
* numbers, versions, HTTP status codes, dates, limits;
* provider and product names the user actually wrote.

Provider names are **never added** when the user did not mention one. No metadata
filtering is used: provider recognition may shape an extra query view, but every
corpus candidate stays searchable.

## 8. Cells

| cell | query views | purpose |
|---|---|---|
| A | raw | frozen control; must reproduce 0.775 / 15-of-20 / 17-of-22 |
| B | normalized | diagnostic — is conversational form costing us? |
| C | raw + normalized | multi-view, original preserved |
| D | structured | diagnostic |
| E | raw + normalized + structured | **the primary comparison** |

Each view runs independently through BM25 and the transformer, then all lists are
fused with the preregistered RRF. All lists participate equally; no weight is
assigned to any view. Inventing per-view weights after seeing which cases improve
would be fitting to a 20-case set.

If A fails to reproduce, stop and diagnose before interpreting anything else.

## 9. Preregistered readings

n = 20 / 22 spans. One case = 5 percentage points. No significance claims.

| outcome | reading |
|---|---|
| E exceeds 0.775 by ≥ 2 cases with no regressions | query formulation has earned a place |
| B alone improves substantially | conversational form was the noise; prefer the simple transform |
| views regress alone but fusion helps | complementarity — keep original + alternates, never substitute |
| A ≈ E | **query formulation is not the bottleneck; stop rewriting queries** |
| top-10 flat but absent evidence moves into 11–100 | candidate recall improved; recompute the reranker ceiling |

**Regression watch.** The control already recalls 15 of 20 fully. A transformation
that rescues failures while breaking existing successes is not an improvement.
Rescued/regressed/net against A is reported for every cell, and zero-regression
results are called out separately.

Tracked individually: **AN-003** (the canonical query-side diagnostic — it has now
resisted BM25, FastText, the transformer at 256 and 512, bounded chunking,
encoder-aligned chunking and enrichment, with its evidence visible every time),
plus every case not fully recalled by the 0.775 control.

If a transform moves AN-003 from rank 193 into the top 20, the report must explain
*which* mechanism did it — terminology alignment, identifier emphasis, filler
removal, changed semantic representation, or fusion complementarity — not merely
state the new rank.

## 10. Cost

More views mean more retrieval work. Every cell reports retrieval calls per
question, BM25 / transformer / fusion latency, and the work multiplier against A.
A one-case gain bought with several times the retrieval work is not automatically
worth promoting.

## 11. Not done in this experiment

No reranker. No LLM query rewriting as a primary cell (EXP-011F would be
exploratory only, after A–E are frozen, and only with a project-authorized
credential — the host harness's own credential is not one). No metadata filtering.
No document-side change of any kind. No new golden questions. No retuning of the
0.775 control.

## 12. Promotion

The frozen production baseline stays BM25 / control chunks / `top_k=10`. The
strongest measured configuration remains BM25 + transformer @512 RRF at
0.775 / 15-of-20. EXP-011 must beat it on paired case movement, not on a single
aggregate metric, before anything changes.
