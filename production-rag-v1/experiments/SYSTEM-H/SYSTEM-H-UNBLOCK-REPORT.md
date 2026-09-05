# SYSTEM-H — unblock report

**Status:** `CANNOT_EXECUTE_MISSING_SCORE_DETERMINING_ARTIFACTS`
**Validation runs consumed:** 0 · **Validation scored:** false · **Reserve accessed:** false
**SUPPORTED:** `null` — not `false`. This is an execution and provenance blocker, **not a measured negative result.**

## What is actually blocking

SYSTEM-H-V2-DEV-CANDIDATE is an architecture *record*, not runnable code. Four things are missing, and
one of them cannot be fixed by copying files.

| # | Item | Classification |
|---|------|----------------|
| 1 | Executable SYSTEM-H runner | MISSING_LOCAL · NEEDS_TRANSFER |
| 2 | SYSTEM-H configuration record | **AVAILABLE_LOCAL** |
| 3 | SYSTEM-A-GLOBAL implementation (stage 1) | MISSING_LOCAL · NEEDS_TRANSFER |
| 4 | SYSTEM-G / EXP-019A score-determining artifacts | **PROVENANCE_GAP** · MISSING_LOCAL · NEEDS_TRANSFER |
| 5 | Projection index `ps_v2_ovl_win448_s224` | MISSING_LOCAL · NEEDS_TRANSFER |
| 6 | CE model + tokenizer at the pinned revision | MISSING_LOCAL · NEEDS_TRANSFER |
| 7 | Candidate-generation implementation hashes | MISSING_LOCAL · NEEDS_TRANSFER |
| 8 | Performance path (PERF-003 D1) | MISSING_LOCAL · NEEDS_TRANSFER · not score-determining |
| 9 | Everything needed to recompute `score_determining_hash` | **PROVENANCE_GAP** |

No item needs a CUDA host. SYSTEM-H is CPU-executable in principle — it is provenance, not hardware,
that blocks it.

## Item 4 is the one that matters

Items 1, 3, 5, 6 and 7 are transfer problems. Someone copies files, we verify hashes, we run.

Item 4 is different. The EXP-019A retrieval prior is **score-determining**, and EXP-019A's original
artifacts are absent from every fetched ref — `PROVENANCE-GAP-001` records them as known only through
relayed conversation values. Its behaviour *is* described in the SYSTEM-H record in enough detail to
re-implement: piecewise channel assignment, `P=20` projection-only extras, min-max within that
population, degenerate `0.5`, E-L10 `retrieval_norm` preserved, no third RRF.

That description is exactly the trap. A re-implementation would run and produce numbers, and those
numbers would be **unverifiable against the thing they claim to reproduce**, because the thing does not
exist. The preregistration makes a run valid only if `score_determining_hash` equals
`3fade96a9b3597861b0788c15d0e456a52fa92f6907749a2661960e54bf7b2e5` at run time, and that hash covers
fields that would be invented rather than reproduced.

So the answer to "can we just rebuild it?" is: we can build *something*, and it must not be called
SYSTEM-H.

## Verification note on the local CE artifact

`data/cache/models/exp009/onnx/model.onnx` exists on this host. It is **not** verified to be
`cross-encoder/ms-marco-MiniLM-L6-v2` at revision `233902d25c440f23af6f7d6e94d2946bac0bee0a`. Before any
use it must be checked against the recorded `artifact_sha256`
`5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`. `huggingface.co` is unreachable from
here (`CONNECT tunnel failed, response 403`) and `torch`/`transformers` are absent, so it cannot be
re-fetched locally either.

## The two legitimate paths

**PATH A — original execution environment.** Run the frozen preregistration on the machine that already
has the executable SYSTEM-H and all score-determining artifacts. Verify the pinned hashes before scoring.
This is the cheapest path and the one to prefer.

**PATH B — verified artifact transfer.** Move the runner, the projection index and the score-determining
implementation here; verify each against its original recorded hash; reproduce `score_determining_hash`;
then score. Path B still fails at item 4 unless EXP-019A's originals are recovered.

**There is no PATH C.** A reconstruction from the written description is a different system. If one is
ever built it takes a new identity — `SYSTEM-P-H-RECONSTRUCTED` or another approved name — and inherits
none of SYSTEM-H's identity, config hash, frozen claims or preregistration. It was not built in this task.

## What is unaffected

The benchmark, the split and the preregistration are all intact and independently re-verified: the ten
frozen hashes reproduce, the split was re-derived from the frozen benchmark plus its recorded salt and
reproduced both partition hashes exactly, the reserve lock holds, and the reserve access log is still
zero bytes. The SYSTEM-H preregistration remains unconsumed at zero runs.
