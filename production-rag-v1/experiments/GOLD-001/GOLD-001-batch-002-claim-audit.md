# GOLD-001 — batch 002 claim-support audit

An overlay, not an edit. No batch 001 record was modified, no closure hash was recomputed, and the closed batch still hashes to `69364f672e233fb3…`.

**17 SUPPORTED · 0 NEEDS_REVIEW · 0 UNSUPPORTED** across 17 approved cases and 19 atomic claims.

**17 of 17 are holdout-eligible today** — meaning their claims trace to their own span *and* they carry literal critical strings the validator can check. That second condition is what the closure artifact flagged, and it is the binding one.

## Method, and what it cannot tell you

This is a mechanical screen. For each approved claim it checks that every term the claim turns on — code identifiers, numbers, quoted values, product names — appears inside the approved span, and measures how much of the claim's content vocabulary the span carries.

A claim can pass every check here and still be a bad paraphrase; a claim can fail one and still be true. Nothing short of clean is called a verdict — it is called NEEDS_REVIEW and addressed to a person. Retrieval was not run.

## Results

| candidate | status | critical strings | min claim coverage | holdout-eligible |
| --- | --- | --- | --- | --- |
| `GOLD-B002-01` | SUPPORTED | yes | 67% | **yes** |
| `GOLD-B002-02` | SUPPORTED | yes | 80% | **yes** |
| `GOLD-B002-03` | SUPPORTED | yes | 62% | **yes** |
| `GOLD-B002-04` | SUPPORTED | yes | 56% | **yes** |
| `GOLD-B002-05` | SUPPORTED | yes | 60% | **yes** |
| `GOLD-B002-06` | SUPPORTED | yes | 60% | **yes** |
| `GOLD-B002-07` | SUPPORTED | yes | 56% | **yes** |
| `GOLD-B002-08` | SUPPORTED | yes | 50% | **yes** |
| `GOLD-B002-09` | SUPPORTED | yes | 60% | **yes** |
| `GOLD-B002-10` | SUPPORTED | yes | 100% | **yes** |
| `GOLD-B002-11` | SUPPORTED | yes | 89% | **yes** |
| `GOLD-B002-13` | SUPPORTED | yes | 100% | **yes** |
| `GOLD-B002-14` | SUPPORTED | yes | 58% | **yes** |
| `GOLD-B002-15` | SUPPORTED | yes | 100% | **yes** |
| `GOLD-B002-16` | SUPPORTED | yes | 88% | **yes** |
| `GOLD-B002-17` | SUPPORTED | yes | 67% | **yes** |
| `GOLD-B002-18` | SUPPORTED | yes | 90% | **yes** |

## Cases that are not clean

## Proposed v2 promotion

`PROPOSED — not applied, and no batch 001 record was modified`. It is returned for explicit approval and has not been written anywhere.

- claim repair needed: 0
- critical strings needed (claims otherwise fine): 0

A case in the second list is not wrong — its claims are traceable to its span. It simply carries no literal critical string, so the validator cannot check it, and a holdout built from it would be gated on nothing.

## Holdout

Not frozen, and this audit does not unblock it. SYSTEM-A and SYSTEM-B remain frozen and unexecuted.
