# EXP-016 development report

Timestamp: 2026-09-01T00:28:01Z
Split: gold150-v1/development n=20. Validation not loaded. Holdout not loaded.
Holdout access log: 0 bytes.
Preregistration existed before any EXP-016 scores.
Rematerialized pool/CE reproduced EXP-015: `True`.

## HA-24 diagnostic conclusion

YES. CE preferred a more general explanation over the exact answer: a generic Tools overview (CE logit 4.04, no ToolContext / tool_input) outranked the A-rank-1 gold sentence that states the `.tool_input` condition (CE logit 1.30 → CE rank 18).

See `experiments/EXP-016/EXP-016-HA24-diagnostic.md`.

## Metrics

| V | strict R@10 | span recall | MRR | rescues vs A | regressions vs A | net | rank-dest (A≤3 out of 10) | latency ms |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| A | 19/20 | 0.9500 | 0.8309 | — | — | +0 | 0 | 500.8 |
| B | 18/20 | 0.9000 | 0.8030 | ['GOLD-B005-11'] | ['HA-22', 'HA-24'] | -1 | 2 | 5780.2 |
| C | 20/20 | 1.0000 | 0.8072 | ['GOLD-B005-11'] | — | +1 | 0 | 5774.4 |
| D | 20/20 | 1.0000 | 0.8239 | ['GOLD-B005-11'] | — | +1 | 0 | 5774.4 |

A and B are re-reported from stored EXP-015 ranks. C and D use the same
rematerialized pool-100 and CE logits; only the fusion/guard differs.

## Named-case traces

### HA-22

A full=True  B full=False  C full=True  D full=True

| span | chunk | A rank | pool | CE score | CE rank | B rank | C rank | D rank | protected | clamped | all spans in top-10 A/B/C/D |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| 0 | `chk_d6e10a755991e31ad9e3d2770f5142f2cd0f9040` | 2 | 2 | 0.4937 | 21 | 21 | 10 | 6 | True | True | True/False/True/True |

### HA-24

A full=True  B full=False  C full=True  D full=True

| span | chunk | A rank | pool | CE score | CE rank | B rank | C rank | D rank | protected | clamped | all spans in top-10 A/B/C/D |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| 0 | `chk_300debbdfdd33f994da8367b173f4986666146c1` | 1 | 1 | 1.2992 | 18 | 18 | 10 | 3 | True | True | True/False/True/True |

### GOLD-B005-11

A full=False  B full=True  C full=True  D full=True

| span | chunk | A rank | pool | CE score | CE rank | B rank | C rank | D rank | protected | clamped | all spans in top-10 A/B/C/D |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| 0 | `chk_99cafb680130e5c1110b94721443d9a70b07e3d0` | 13 | 13 | 4.9393 | 1 | 1 | 1 | 5 | False | False | False/True/True/True |

## Decision

**SYSTEM_D_FROZEN** — SYSTEM_D_FROZEN_STOP_FOR_VALIDATION_APPROVAL

- C qualifies: `{'strict_ge_A': True, 'net_rescues_ge_0': True, 'no_new_rank1_destruction': True, 'qualifies': True}`
- D qualifies: `{'strict_ge_A': True, 'net_rescues_ge_0': True, 'no_new_rank1_destruction': True, 'qualifies': True}`
- SYSTEM-D frozen: `True` → `SYSTEM-D-GUARD.json`
- Validation was not run. Holdout was not run. No EXP-017.

