# SYSTEM-H-V2-DEV-CANDIDATE

**Status: NOT FROZEN. `config_hash` withheld. 9 unresolved fields.**

File SHA256 of `SYSTEM-H-V2-DEV-CANDIDATE.json`:
`e6adf1e14eaa9de76f5b2647088a75ec71cb612119a9ac1fa49f5da09368adef`

## Why this is not frozen

The brief asks SYSTEM-H to "represent exactly" SYSTEM-G's candidate generation.
**SYSTEM-G's configuration is not reachable from this session.** Verified against
every branch on the remote:

| checked | result |
|---|---|
| `grok/v2-dev` @ `b044b41` | 0 files matching SYSTEM-G, PERF-003, EXP-019, `ps_v2_ovl` |
| `grok/ce-latency-handoff` @ `7661ac5` | same |
| `main`, `claude/rag-v1-build-experiments-5yngul` | same |
| content grep for `563a7b79…` and `6d108568…` | neither config hash appears anywhere |

Nine fields are consequently unresolved:

1. `candidate_generation.stage_2_local.parent_n`
2. `candidate_generation.stage_2_local.W_per_parent`
3. `candidate_generation.stage_3_projection.projection_model`
4. `candidate_generation.stage_3_projection.projection_chunk_set_id`
5. `candidate_generation.stage_3_projection.projection_index_hash`
6. `candidate_generation.retrieval_prior.parameters`
7. `candidate_generation.retrieval_prior.prior_form`
8. `reranking.normalization`
9. `reranking.tie_breaks`

## Why a hash was withheld rather than computed

A config hash is worth something only because it changes when any field changes.
Hashing a specification that contains placeholders would mint an
authoritative-looking identity for an architecture nobody is running — and when
the nine fields were later filled in, the hash would change, making **every
comparison across that correction silently invalid**. `systems.py` states the
same rule: *"if a field changes, the hash changes, and any comparison across the
change is invalid by construction."*

So the file records what is known, names what is not, and withholds the identity
until it is real. `DEVELOPMENT_ARCHITECTURE_FROZEN=false` is a statement of fact,
not a refusal.

## What is resolved

* **SYSTEM-A-GLOBAL** — hash `9afcb5b7…78ee0b38`, read from `src/rag_v1/systems.py`.
* **The cross-encoder** — `cross-encoder/ms-marco-MiniLM-L6-v2`, revision
  `233902d2…`, artifact sha256 `5d3e70fd…c1d4d4a`, **re-verified byte-for-byte in
  this session** against the copy on `grok/ce-latency-handoff`.
* **The performance path** — PERF-003 D1: `pad="batch"`, `bucket_by_length=True`,
  `batch_size=16`, threads unchanged, `fast=True` **not** used. This matches
  PERF-002's recommendation exactly: ship bucketing, leave threads as a separate
  per-host decision.
* **L=10**, P=20, no third RRF, 0.7/0.3 blend — as stated in the brief.

## To freeze in one step

Supply `SYSTEM-G-PROJECTION-PRIOR.json` (or push the branch carrying it) and the
EXP-019A prior parameters. The nine fields fill in, the hash is computed over a
complete specification, and the status flags flip together.
