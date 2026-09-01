# EXP-018B Track 1 — score-preserving local BM25

Timestamp: 2026-09-01T03:38:00Z UTC. SCORE_PRESERVING=`True`.

Method: one `_LEXICAL_SQL` call per query with `version_ids=all parents`, then top-W=20 per parent. Full-corpus IDF. Not A's top-50 BM25.

Union membership ok: 50/50. Parents ok: 50/50. e_top10 ok: 50/50. Gold e_rank ok: 50. Local-order proxy ok: 50/50.

stored EXP-018 did not persist per-parent ordered local lists; within-parent order is round(BM25,9) DESC, chunk_id ASC from _LEXICAL_SQL; batched path uses the same ORDER BY then first W per parent. Proxy: union extras identity + e_top10 (RRF consumes per-parent ranks).

## Metrics vs stored EXP-018

- D strict R@10 remat 38/50 stored 38/50
- E strict R@10 remat 40/50 stored 40/50
- D cand R@100 remat 41/50 stored 41/50
- E cand R@100 remat 45/50 stored 45/50
- E span R@10 remat 0.8 stored 0.8
- E MRR remat 0.5969 stored 0.5969
- E doc recall remat 0.92 stored 0.92

## Latency

- A/global: 358.5 ms (stored 357.5)
- local BM25: 192.4 ms (stored 6077.6)
- CE E union: 9913.6 ms (stored 10163.7)
- E total: 10469.4 ms (stored 16604.3)

No mismatches. Track 2 may run.
