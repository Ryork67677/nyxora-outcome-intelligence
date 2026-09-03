# EVAL-VAL-001 decision

**REPLICATION_REJECTS_B.** SYSTEM-B must not be promoted. SYSTEM-A remains the retrieval control.

Recorded at git commit `5082123e8c406ab162349d23003b1173afd697ac` (archive `5082123`). This document classifies the already-measured validation replication; it does not rewrite `EVAL-VAL-001-report.md` and it does not change any system.

## Measurement this decision rests on

On the frozen gold150-v1 validation split (n=40, previously unseen):

| | strict full-case recall@10 |
| --- | ---: |
| SYSTEM-A-GLOBAL | **30/40** (75.0%) |
| SYSTEM-B-DOC-C | **21/40** (52.5%) |
| delta (B−A) | **-0.225** (−9 cases) |

Paired movement: **2 rescues / 11 regressions** (net −9). Bootstrap 95% CI on the per-case delta: **[-0.375, -0.075]** (seed `20250818`, 10000 resamples). McNemar exact: 13 discordant pairs (2 B-only, 11 A-only), **p = 0.0225**.

**12** of B's failures are `DOCUMENT_ROUTING_FAILURE`: a required document never reached Stage 2. Stage-1 routing discards evidence that the global system ranks successfully.

The development result (15/20 vs 17/20, +2 / 0) did not replicate. SYSTEM-B is not eligible for promotion. SYSTEM-A-GLOBAL (`9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38`) remains the frozen retrieval control. SYSTEM-B-DOC-C (`304c350940b83733df6043ae3a8abdcbcde33d16950730127aa9f1f39494388b`) stays a measured, rejected alternative.

## What this is not

- Not a holdout run. holdout_runs = 0.
- Not a change to BM25, MiniLM, RRF, chunking, or SYSTEM-A.
- Not a rewrite of the EVAL-VAL-001 report.
