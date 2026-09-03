# EXP-018 development report

Timestamp: 2026-09-01T01:37:13Z (UTC). Split: gold150-v1/development n=20.
Validation not loaded. Holdout not loaded. SYSTEM-E is **not** a release freeze.
Holdout access log before/after: 235/235 bytes (sha 45b83a77f6f3… unchanged=True).
Original preregistration 2026-09-01T01:23:45Z kept. Amendment 2026-09-01T01:27:02Z (local BM25 only) is what ran. Amendment mtime precedes this results file.
Rematerialized D identity vs EXP-016 gold-span ranks: `True`. D strict 20/20.

## Honest gate

EXP-016 D is already 20/20 and 23/23 spans@10 on this split. Strict Recall@10 **cannot improve**. A tied 20/20 is not a retrieval win. ChatGPT's "proceed only if Recall@10 improves" clause is **UNMEETABLE_ON_AUTHORIZED_SPLIT**. Freeze-or-val is ChatGPT's decision.

## Metrics

| V | strict R@10 | span recall | spans@10 | MRR | doc recall | cand-ev recall (pool) | pool mean/max | latency ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 19/20 | 0.9500 | 22/23 | 0.8309 | 1.0000 | 1.0000 | 91.3/97 | 496.6 |
| D | 20/20 | 1.0000 | 23/23 | 0.8239 | 1.0000 | 1.0000 | 91.3/97 | 5759.7 |
| E | 20/20 | 1.0000 | 23/23 | 0.8269 | 1.0000 | 1.0000 | 185.2/243 | 19421.3 |

Primary (candidate evidence recall): D/A pool 23/23 = 1.0000; E union 23/23 = 1.0000.
Additive integrity: `True`. Rescues vs D: —; regressions vs D: —; net +0.
Rank-1 destruction vs D: 0; vs A: 0.
E mean latency 19421.3 ms vs rematerialized D 5759.7 ms (EXP-016 D recorded 5774.4 ms).

## Named-case traces

### HA-22

A full=True  D full=True  E full=True  parents=7  pool 91→196 (+105 new)  first-gold-pool A=2 E=2

| span | cover-chunk | A rank | D pool | E pool | D rank | E rank | in D pool | in E pool | new | top10 A/D/E |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| 0 | `chk_d6e10a755991e31ad9e3d2770f5142f2cd0f9040` | 2 | 2 | 2 | 6 | 8 | True | True | False | True/True/True |

### HA-24

A full=True  D full=True  E full=True  parents=6  pool 90→170 (+80 new)  first-gold-pool A=1 E=1

| span | cover-chunk | A rank | D pool | E pool | D rank | E rank | in D pool | in E pool | new | top10 A/D/E |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| 0 | `chk_300debbdfdd33f994da8367b173f4986666146c1` | 1 | 1 | 1 | 3 | 7 | True | True | False | True/True/True |

### GOLD-B005-11

A full=False  D full=True  E full=True  parents=6  pool 91→158 (+67 new)  first-gold-pool A=13 E=11

| span | cover-chunk | A rank | D pool | E pool | D rank | E rank | in D pool | in E pool | new | top10 A/D/E |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| 0 | `chk_99cafb680130e5c1110b94721443d9a70b07e3d0` | 13 | 13 | 11 | 5 | 2 | True | True | False | False/True/True |

## Decision

**QUALIFIES_FOR_VAL_CONSIDERATION + CEILING_ON_DEV**

- QUALIFIES_FOR_VAL_CONSIDERATION: `True`
- CEILING_ON_DEV: `True`
- MECHANISM_SUPPORTED: `False`
- REJECT_AT_DEV: `False`
- SYSTEM-E config hash: `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe`
- SYSTEM-E was **not** frozen as a v2 release. Validation was not run. Holdout was not run.
- Environment: PostgreSQL 16.15 (Debian 16.15-1.pgdg12+2) on x86_64-pc-linux-gnu / pgvector 0.8.6 (known drift vs 16.13 / 0.6.0).

