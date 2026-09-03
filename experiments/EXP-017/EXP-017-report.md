# EXP-017 — search-projection / evidence-preserving retrieval

Timestamp: 2026-09-01T04:29:28Z UTC. Dataset: V2-DEVSET-001 n=50 only. Prereg json sha256 `053a6bf14df088ca9e2283bc3e8dfb0769848a48c54c51a77fbe045795a80cc6`. Integrity **PASS**. Scored once. Not retuned.

gold150-v1 holdout.json not opened. Validation not loaded. SYSTEM-D / SYSTEM-E-WITHIN-DOC.json / SYSTEM-E-L10-WITHIN-DOC.json / cs_v1_control not overwritten. No third merge-RRF list. Projection-only A-channel = 0.0 (not minmax_degenerate=0.5). No extra windows/strides/P. No query rewrite. RELEASE=NOT_FROZEN.

Holdout access log: 235 bytes sha `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3` unchanged=True.

## Integrity

PASS. Projection set `ps_v2_ovl_win448_s224` cardinality **18057**. Table 66 MB; embedding table 37 MB; payload 27 MB.

Hash labeling (kept distinct):

- SYSTEM-E-WITHIN-DOC **config_hash** `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe`
- SYSTEM-E-WITHIN-DOC **file SHA256** `e228616beee1bcb13855c2eadee9fc20ec1fae3e54c77b28587114568c64d087`
- SYSTEM-E-L10-WITHIN-DOC **config_hash** `bae1c05b5c47c179dc5cd7972a14bd23d102a4d513b674667eb469e17cd85e89`

## PRIMARY

Candidate gold-span recall: **46/50** vs frozen E-L10 **44/50**. Strictly greater: `True`.

## SECONDARY

- strict R@10: 40/50 (E-L10 rematerialized 40/50)
- span R@10: 0.8 (E-L10 0.8)
- MRR: 0.597 (E-L10 0.5956)
- document recall: 0.92 (E-L10 0.92)
- rescues vs E-L10: —
- regressions vs E-L10: —
- rank-1 destructions: 0
- mean projection additions: 20
- mean final pool: 124.1 (E-L10 remat 104.1; frozen E-L10 104.1)
- latency ms: A 350.0 / local BM25 195.2 / projection 466.2 / CE 6899.6 / total 7914.3

## DIAGNOSTICS

- mean projection hits: 95.02
- mapping to multiple canonical chunks (sum over queries): 3882
- mean previously absent canonical chunks from mapping: 190.78
- gold in pool but below top-10: 6 (EXP-019 headroom; entered_via_projection listed in results JSON)

## Decision (preregistered, not retuned)

**MECHANISM_SUPPORTED**

MECHANISM_SUPPORTED iff candidate gold-span recall > 44/50 AND 0 strict R@10 regressions vs E-L10 AND 0 rank-1 destructions vs E-L10. Development-stage, not independent validation. Not a named-miss gate. No release freeze.

## Standing

No EXP-019. No validation. No holdout. No retune.

