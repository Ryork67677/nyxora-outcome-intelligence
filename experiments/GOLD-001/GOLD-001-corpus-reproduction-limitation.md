# Corpus reproduction limitation — blocking for retrieval

*2026-08-31T03:57:17Z*

**`CORPUS_REPRODUCTION_INCOMPLETE = true`, `corpus_snapshot_reproduced = false`, `RETRIEVAL_BLOCKED = true`.** Frozen snapshot `snap_689e336380a054d8039dc35b2c09cd0a` is not reproduced.

## Two snapshot parameters recovered

- `name` = `v1-openai-anthropic`
- `manifest_hash` = `452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17`, from `experiments/EXP-007/results.json`

stable_id('snap', name, manifest_hash, PARSER_VERSION, chunking_hash) reproduces snap_689e336380a054d8039dc35b2c09cd0a; any other name gives a different value, so the match confirms both at once. The manifest hash covers only the 202 (version_id, content_hash) pairs, so it is a recovery target that isolates corpus content from the parser and chunking parameters.

## Reproduced

**63 OpenAI documents**, of which **49 verify against an identity recorded before the corpus was lost**. Each saved openai url is pinned to a full commit; re-fetched, re-parsed with the frozen parser, and 49 of the 63 version_ids match identities recorded in retrieval experiments and gold records before the corpus was lost.

## Outstanding

**139 Anthropic documents.** no historical capture exists in this environment; the archive host is unreachable through this session's proxy and live pages have drifted. 40 of the 139 now have a recovered expected version_id, so a candidate capture can be verified exactly rather than judged by eye.

A further 62 expected `version_id` values survive without a url attached; they still work as an oracle.

## Audit correction CORPUS-001-AC-001

> **Superseded:** "the original 2,482 unbuildable identities remain a corpus reproduction blocker"
>
> **Replaced with:** "The original 2,482 value counts failed Batch-006 authoring attempts and is not part of the corpus snapshot digest. It remains relevant only to exact authoring-pipeline reproduction."

The superseded wording is preserved here rather than rewritten out of the older reports. Those reports were accurate records of what the project believed when they were written; this correction is the audit trail, not a silent edit. Basis: `CORPUS-001-unbuildable-identity-analysis.md`.

## The 2,482 unbuildable identities are not a corpus blocker

Previously counted in this limitation as a corpus gap. NOT a corpus blocker. They are counts of authoring attempts inside batch 006's generator that produced no question — spans inside the 202 documents, not documents. They are required only to reproduce the GOLD authoring process (the batch-007 NO_BUILDER pilot). The count is of attempts, not distinct spans, so 2,482 is not even a count of identities.

See `CORPUS-001-unbuildable-identity-analysis.md`. **Effect: the corpus gate has one blocker, not two.**

## What blocks this gate

- 139 Anthropic documents with no recovered historical bytes
- 14 OpenAI documents that reproduce but whose frozen version_id was never recorded, so the reproduction cannot be checked

**Effect: `RETRIEVAL_BLOCKED`.** These must not run until it lifts: SYSTEM-A, SYSTEM-B, BM25, MiniLM, transformer retrieval, DOC-C, routing, reranking, answer generation.

**Unblocks when:**

- A. the original frozen corpus/database snapshot is shown to exist and to match its recorded manifest and hashes, or
- B. the intended snapshot is fully reconstructed and revalidated to snap_689e336380a054d8039dc35b2c09cd0a


## Host search

No Windows host, no WSL mount and no Docker daemon is reachable from this session. The gitignored data/raw captures were never in this container. A host-machine sweep has to be run on the host itself; its results can be brought back here as an artifact, which is how the earlier host evidence in this project arrived. See `CORPUS-001-host-search.md`.

## Identity oracles

166 `version_id` and 803 `chunk_id` values survived the corpus — a historical capture produced outside this session can be accepted or rejected here by arithmetic; 40 Anthropic documents can be verified individually and 16 of those also carry exact byte anchors.
