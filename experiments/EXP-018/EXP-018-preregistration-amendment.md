# EXP-018 preregistration amendment

Written **2026-09-01T01:27:02Z** (2026-08-31 21:27 ET), **before** any EXP-018 results file exists.
Original preregistration `EXP-018-preregistration.md` /
`EXP-018-preregistration.json` (2026-09-01T01:23:45Z) is **kept** (it froze
BM25+dense within-doc expansion). This amendment supersedes that retrieval
design with ChatGPT's frozen answers. No scores have been computed. Knobs
below are frozen now and will not be retuned after scores.

ChatGPT's full v2 note landed before retrieval. Russell: get EXP-018 done;
do not wait for another ChatGPT review of this amendment.

## What changed vs the 01:23Z preregistration

| item | 01:23Z (kept on disk, not executed) | this amendment (what will run) |
| --- | --- | --- |
| local lanes | full-corpus BM25 **and** MiniLM cosine inside each parent, RRF k=60, top W=20 | **LOCAL BM25 ONLY** over that document's `cs_v1_control` passages; **no** within-doc dense/MiniLM lane |
| merge | union expanded chunks with A-pool-100, then D blend using original A scores (absent A-pool → a_score=0, a_rank=1e9) | A-pool-100 **UNION** local BM25 candidates → **deterministic RRF** → frozen D blend (0.7 CE + 0.3 A) on the union |
| parents | unique version_ids among A fused top_k=10, parent_n=10 | **confirmed ChatGPT option B**: TOP 10 unique version_ids from SYSTEM-A fused ranking. Not top 5. Not all pool-100 docs. |
| W | 20 | **still 20** (already written; do not retune after scores) |
| success gate | QUALIFIES if strict R@10 ≥ D and net rescues ≥ 0 and no rank-1 destruction and additive integrity; MECHANISM if cand-ev-recall_E > D | **honest gate** below (R@10 cannot improve on this split) |

IDF remains **full-corpus**. Do not recompute IDF inside the document.
`cs_v1_control` remains immutable. SYSTEM-D freeze files remain read-only.

## Frozen SYSTEM-E-WITHIN-DOC (amended)

1. Run frozen SYSTEM-A globally (BM25 Postgres FTS simple k1=1.2 b=0.75 +
   MiniLM cosine exact + RRF k=60, pool_per_retriever=50) over all
   `cs_v1_control` chunks. Raw query, no rewrite, no metadata filter.
   This produces the A candidate pool of 100 with fused ranks 1..N (N≤100).
2. **Which docs get local search (ChatGPT option B):** the TOP 10 unique
   `version_id`s among SYSTEM-A fused ranking, first-seen order in A fused
   top_k=10. Frozen `parent_n=10`. Not top 5. Not all pool documents.
   Rationale (unchanged): these are documents the global system already
   identified; expansion happens inside them. Not chosen from holdout.
3. **Local retrieval: BM25 only.** For each parent `version_id`, BM25-score
   that document's `cs_v1_control` passages with the **same full-corpus IDF**
   (`lexical_search(..., version_ids=[parent])` — corpus n/df/avg_len
   unchanged). Take top `W=20` (or all if fewer). **Do not** add a
   within-doc dense/MiniLM lane in this experiment.
4. **Merge (anti-DOC-C):**
   - Candidate set = A-pool-100 ∪ (union of per-parent local BM25 top-W).
     Dedupe by `chunk_id`. Local retrieval **can add**. It **cannot remove**
     a global A-pool-100 chunk, even if that chunk's `version_id` is not a
     parent.
   - Ranked lists for deterministic merge RRF (`rrf_k=60`, same frozen k as
     SYSTEM-A; not a new knob): labelled `system_a` = A fused pool-100 with
     its A ranks; labelled `local_bm25:<version_id>` = that parent's local
     BM25 top-W with within-document BM25 ranks 1..W.
   - Fuse with `rrf_fuse_labelled` over the **full union** (top_k = union
     size, so nobody is dropped before CE). A chunk in both A and local BM25
     receives both contributions (additive). A chunk only in A still
     participates (A-list contribution only).
   - Merge-RRF score/rank is the **A channel** for E's blend (the natural
     "0.3 A" on a larger additive pool). Rematerialized SYSTEM-D control
     still uses original SYSTEM-A fused scores on pool-100 only.
5. Cross-encode the UNION with the frozen CE (same ONNX/sha as D). Apply
   frozen D blend: `0.7 * minmax_norm(CE) + 0.3 * minmax_norm(merge-RRF)`
   within each query's union pool; degenerate channel → 0.5. Tie-break:
   blend desc, merge-RRF rank asc, `chunk_id` asc. Emit top_k=10.
6. New SYSTEM-E config hash from the **amended** config. Do not overwrite D.

## Metrics (ChatGPT)

**Primary:** candidate evidence recall = fraction of gold spans present in
the candidate pool (D/A pool = SYSTEM-A top-100; E pool = union).

**Secondary:** strict Recall@10, span recall, MRR, latency, rank of first
gold appearance in the pool (pool-rank, not post-rerank). Also document
recall, spans@10 / total, pool size mean/max, additive integrity, rescues /
regressions vs D, rank-1 destruction, named traces (GOLD-B005-11, HA-22,
HA-24, any case that differs).

## Honest gate (frozen now)

EXP-016 SYSTEM-D is already **20/20** strict Recall@10 and **23/23** spans@10
on this same development split. **Strict Recall@10 cannot improve on
development.**

Success on dev is **all** of:

(a) additive integrity (every A-pool-100 `chunk_id` still in E pool for all
    20 cases; no D-found gold document dropped);
(b) no Recall@10 regression vs D (E strict ≥ D strict, i.e. still 20/20);
(c) candidate evidence recall_E ≥ candidate evidence recall_D;
(d) report **CEILING_ON_DEV** if D's pool already contains all gold spans.

Do **NOT** claim a retrieval win on development if scores are tied at 20/20.
Do **NOT** then open holdout or validation.

Labels (apply; do not move goalposts):

- **QUALIFIES_FOR_VAL_CONSIDERATION** if (a)(b)(c) hold and there is no new
  rank-1 destruction (gold span with D rank 1 leaves E top-10).
- **MECHANISM_SUPPORTED** if candidate evidence recall_E **>** recall_D.
- **CEILING_ON_DEV** if D pool already has every gold span and Recall@10 is
  20/20 and E does not regress. Still QUALIFIES_FOR_VAL_CONSIDERATION if
  (a)(b)(c) hold. Development **cannot** measure the holdout-motivated
  pool-miss hypothesis.
- **REJECT_AT_DEV** if E regresses vs D on strict Recall@10 **or** additive
  integrity fails.

### ChatGPT "proceed only if Recall@10 improves" clause

Recorded as **unmeetable on the authorized split**: D is already 20/20, so
Recall@10 cannot strictly improve here. Freeze-or-val is **ChatGPT's
decision** after this development report. This experiment does **not** freeze
SYSTEM-E as a v2 release and does **not** run validation or holdout.

## Unchanged do-nots

No holdout, no validation, no D edit, no knob search after scores, no using
the 11 holdout misses to choose W / parent_n / blend weights, no DOC-C gate,
no new `cs_v1_control` passages, no re-embed, no live fetch, no git
clone/commit/push, no Windows tree.

Holdout access log at original preregistration: 235 bytes, sha256
`45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`. Must be
unchanged after the run.
