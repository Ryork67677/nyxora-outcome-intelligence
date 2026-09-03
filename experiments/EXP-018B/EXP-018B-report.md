# EXP-018B — within-document efficiency + score-preserving optimization

Timestamp: 2026-09-01T03:38:00Z UTC. Dataset: V2-DEVSET-001 n=50 only. ChatGPT approved revision 2026-08-31 23:22 ET. Prereg json sha256 `c48068ec5dfa06683eaa2b0763508e9c7457d1ede2f23c3394c3c6bd6192ce8c`.

gold150-v1 holdout.json not opened. gold150-v1/development not loaded. Validation not loaded. SYSTEM-D not edited. No extra L. No retune.

Holdout access log before/after: 235/235 bytes (sha 45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3 unchanged=True).

## Track 1

**SCORE_PRESERVING = `True`**

Local BM25 mean 192.4 ms vs stored EXP-018 6077.6 ms. E total 10469.4 ms vs stored 16604.3 ms.
Union/e_top10/parents: 50/50, 50/50, 50/50.

## Track 2 caps

| V | strict R@10 | span R@10 | MRR | doc recall | cand R@100 | union mean | total ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| D | 38/50 | 0.7600 | 0.5650 | 0.9000 | 41/50 | 94.1 | 5717.4 |
| E uncapped (T1) | 40/50 | 0.8000 | 0.5969 | 0.9200 | 45/50 | 176.8 | 10469.4 |
| L=10 | 40/50 | 0.8000 | 0.5956 | 0.9200 | 44/50 | 104.1 | 6454.8 |
| L=20 | 40/50 | 0.8000 | 0.5972 | 0.9200 | 45/50 | 114.0 | 7000.6 |
| L=40 | 40/50 | 0.8000 | 0.5971 | 0.9200 | 45/50 | 132.9 | 8038.5 |

## Per-L secondary + gate

- **L=10** cand 44/50; strict 40/50; span 0.8; MRR 0.5956; doc 0.92; rescues vs D ['V2D-43', 'V2D-48']; regressions vs D —; rank-1 destructions 0; mean additive 10; mean union 104.1; A 358.5 / local 192.4 / CE 5903.9 / total 6454.8 ms; qualifies=`True`.
- **L=20** cand 45/50; strict 40/50; span 0.8; MRR 0.5972; doc 0.92; rescues vs D ['V2D-43', 'V2D-48']; regressions vs D —; rank-1 destructions 0; mean additive 19.94; mean union 114.04; A 358.5 / local 192.4 / CE 6449.8 / total 7000.6 ms; qualifies=`True`.
- **L=40** cand 45/50; strict 40/50; span 0.8; MRR 0.5971; doc 0.92; rescues vs D ['V2D-43', 'V2D-48']; regressions vs D —; rank-1 destructions 0; mean additive 38.82; mean union 132.92; A 358.5 / local 192.4 / CE 7487.6 / total 8038.5 ms; qualifies=`True`.

## Selection (preregistered, not retuned)

**selected L = 10** (smallest L in {10,20,40} that qualifies).

Threshold >=44/50 was preregistered after seeing EXP-018's 45/50; development-stage, not independent validation.
Four rescue IDs were NOT used as a gate.

## DIAGNOSTIC_ONLY rescue fates

| id | L | in-pool | blend rank | pool rank | extra index (0-based) | selected by L |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| V2D-11 | 10 | True | 31 | 28 | 9 | True |
| V2D-33 | 10 | False | None | None | 16 | False |
| V2D-34 | 10 | True | 39 | 24 | 0 | True |
| V2D-43 | 10 | True | 10 | 18 | 3 | True |
| V2D-11 | 20 | True | 32 | 36 | 9 | True |
| V2D-33 | 20 | True | 12 | 51 | 16 | True |
| V2D-34 | 20 | True | 41 | 31 | 0 | True |
| V2D-43 | 20 | True | 10 | 19 | 3 | True |
| V2D-11 | 40 | True | 34 | 49 | 9 | True |
| V2D-33 | 40 | True | 12 | 63 | 16 | True |
| V2D-34 | 40 | True | 41 | 37 | 0 | True |
| V2D-43 | 40 | True | 10 | 19 | 3 | True |

## Hashes

- prereg json: `c48068ec5dfa06683eaa2b0763508e9c7457d1ede2f23c3394c3c6bd6192ce8c`
- holdout log: `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3` (unchanged)
- SYSTEM-D-GUARD: `e9267f5581404e9885598979204c08762cd33f362703e526b20f4d3430c35a82`
- SYSTEM-D-RELEASE: `1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40`
- SYSTEM-E-WITHIN-DOC: `e228616beee1bcb13855c2eadee9fc20ec1fae3e54c77b28587114568c64d087`

No extra L. No EXP-017. No EXP-019. No holdout. No validation.

