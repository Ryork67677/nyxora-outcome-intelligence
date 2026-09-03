# RAG-V1-FINAL-TAG

Production RAG v1 retrieval freeze tag. Written 2026-09-01T01:12:54Z
(2026-08-31 21:12 ET). Documentation only — not a git tag (this tree has no
`.git`).

## Identity

| | |
| --- | --- |
| base git commit | `5082123e8c406ab162349d23003b1173afd697ac` |
| recorded branch | `origin/claude/rag-v1-build-experiments-5yngul` |
| tree | git archive of that commit **plus** local-only experiment artifacts (EXP-015, EXP-016, EVAL-VAL-002, EVAL-HOLDOUT-001). Those four dirs are **not** on GitHub. |
| system | SYSTEM-D-GUARD-BLEND (variant D; score blend, not clamp) |
| release file | `experiments/EVAL-HOLDOUT-001/SYSTEM-D-RELEASE.json` |
| SYSTEM-D release sha256 | `1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40` |
| config hash | `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a` |
| source freeze | `experiments/EXP-016/SYSTEM-D-GUARD.json` (same config hash) |
| SYSTEM-A hash (candidate generator) | `9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38` |

## Corpus / GOLD / split

| | |
| --- | --- |
| corpus snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| corpus manifest | `452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17` |
| chunk set | `cs_v1_control` (14,209 chunks; immutable for v1) |
| GOLD closure hash | `32b59f774d3efa31` (`experiments/GOLD-001/GOLD-001-150-case-closure.json`) |
| split | `gold150-v1` (dev 20 / val 40 / holdout 90) |
| holdout_sha256 (lock / split artifact) | `756a3a9bc74ce3e2dd3a7924c4048984a0ae5e74237bc8053e18b6fec202d914` |
| `EVAL-SPLIT-001-manifest.json` sha256 | `d63d854b33d5a8a2c8adda62333e86ad54666d7cf186247923f5f09d124de098` (9410 bytes; `experiments/EVAL-SPLIT-001/EVAL-SPLIT-001-manifest.json`) |

## Encoder / cross-encoder

| | |
| --- | --- |
| encoder fingerprint | `bd95feaeacf98559` |
| encoder model_id | `emb_e7d4183fd6eb878ae2fdf080efb6861e` |
| CE | `cross-encoder/ms-marco-MiniLM-L6-v2` rev `233902d25c440f23af6f7d6e94d2946bac0bee0a` |
| CE ONNX sha256 | `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a` |
| blend | 0.7 CE / 0.3 SYSTEM-A; within-query minmax; degenerate 0.5 |
| pool | 100 (50 per retriever, RRF k=60); top_k=10 |

## Final metrics (already recorded; not re-run)

| | |
| --- | --- |
| validation EVAL-VAL-002 | D **33/40** vs recorded A **30/40**; 0 regressions; CI [0.0, 0.175]; McNemar p=0.25; `RERANKER_SUPPORTED` (net-positive mapping, **not** significance) |
| holdout EVAL-HOLDOUT-001 | D **79/90 (87.8%)** |
| holdout macro span recall@10 | **0.8833** (92/104) |
| holdout document recall | **0.9778** |
| holdout MRR | **0.7055** |
| holdout_runs | **1** |

## Honest claim

Production RAG v1 achieves 87.8% strict full-case Recall@10 on a frozen
90-case unseen holdout using SYSTEM-D-GUARD-BLEND, with 0.883
evidence-span recall and 0.978 document recall.

This does not claim statistical significance of the reranker, does not claim
a closed-book win (EXP-NULL never ran), and does not invent a SYSTEM-A
holdout score.

## Freeze note

**v1 retrieval is frozen.** Blend weights, encoder, CE ONNX, candidate pool,
chunk set `cs_v1_control`, and snapshot do not change in v1.

**11 misses classified, not fixed.** Cases:
`GOLD-B001-02`, `GOLD-B001-09`, `GOLD-B002-06`, `GOLD-B003-04`,
`GOLD-B005-07`, `GOLD-B006-02`, `HA-20`, `HA-21`, `HA-37`, `HA-43`,
`HA-58`. Classification is in `HOLDOUT-FAILURE-ANALYSIS-001.md`
(6 candidate-generation, 5 reranking). They are a diagnostic record, not a
tuning set. No retrieval change is proposed from them.

Path: `experiments/EVAL-HOLDOUT-001/RAG-V1-FINAL-TAG.md`
