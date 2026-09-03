# CORPUS-002 — restoration of the verified frozen corpus

**SUCCEEDED** — generated 2026-08-31T23:53:16Z.

The frozen corpus was restored from the verified recovery archive into a fresh isolated database, and its identity was recomputed rather than asserted. No retrieval was run.

## Gates

| gate | result |
| --- | --- |
| archive hash matches | PASS |
| package 203 of 203 | PASS |
| working copy matches package | PASS |
| documents 202 | PASS |
| provider counts | PASS |
| document identities verify | PASS |
| manifest hash exact | PASS |
| snapshot id exact | PASS |
| all gold anchors validate | PASS |
| no retrieval ran | PASS |

## Archive and package

| | |
| --- | --- |
| archive | `/home/user/corpus-recovery-snap689e3363-20260831T2118Z.tar.gz` |
| archive sha256 | `4387ae1d5144109adbde3f11f1fcb339c3773480f356f9804909cf3ad2051b33` |
| matches required | True |
| package checksums | 203 verified, 0 failed |
| working copy | 203 files match the package, 0 mismatched |
| working copy path | `recovery/CORPUS-002/working-corpus` |

## Documents

**202 of 202** document versions restored — {'anthropic': 139, 'openai': 63}. Missing: 0. Field mismatches: 0.

Each restored row was compared against `PROVENANCE.json` on `content_hash`, `provider`, `canonical_url` and `captured_at` individually.

## Corpus identity

| | |
| --- | --- |
| manifest hash computed | `452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17` |
| manifest hash expected | `452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17` |
| **exact match** | **True** |
| snapshot id in database | `snap_689e336380a054d8039dc35b2c09cd0a` |
| snapshot id expected | `snap_689e336380a054d8039dc35b2c09cd0a` |
| **exact match** | **True** |
| parser version | `v1.0` |
| chunking | max_chunk_chars=3500, min_chunk_chars=200 |
| chunking config hash | `bbc874e4f27a7e6826d5106e33510942fd76cb28cf55b5c3333f014e2a6fd916` |

The chunking values were read from `src/rag_v1/config.py`, not from a report. The snapshot id binds the manifest hash, the parser version and the chunking hash together, so all three had to be right for it to reproduce.

## Chunks

`cs_v1_control`: **14209** chunks — {'anthropic': 12028, 'openai': 2181}. Historical target: {'total': 14209, 'anthropic': 12028, 'openai': 2181}. Match: **True**.

Only the V1 control set is restored here. The historical database also holds seven later experimental chunk sets over the same source corpus; those are retrieval-configuration state, not corpus identity, and CORPUS-002 deliberately does not rebuild them.

## GOLD evidence anchors

**174 of 174** evidence spans across **150** human-verified cases reproduce byte-exactly against the restored corpus. Cases with no anchor at all: 0.

| group | cases | spans | verified |
| --- | --- | --- | --- |
| 001 | 16 | 16 | 16 |
| 002 | 17 | 17 | 17 |
| 003 | 20 | 25 | 25 |
| 004 | 14 | 17 | 17 |
| 005 | 15 | 15 | 15 |
| 006 | 8 | 8 | 8 |
| HA | 60 | 76 | 76 |

Anchor shapes: {'legacy_flat': 45, 'expected_evidence': 129}. Batches 001-003 store a single anchor flat on the record; batches 004 onward use an `expected_evidence` list. Both are checked — reading only the list shape would have left 45 of the 150 cases unverified while reporting success.

This is a source-integrity check. No query was run, nothing was ranked, and no retrieval system was executed.

## Environment

| | |
| --- | --- |
| restoration database | `corpus002_restore` |
| postgresql | PostgreSQL 16.15 (Debian 16.15-1.pgdg12+2) on x86_64-pc-linux-gnu |
| pgvector | 0.8.6 |
| python | 3.11.15 |
| parser version | `v1.0` |
| git commit | `` |
| retrieval tables | {'chunk_embedding': 0, 'query_trace': 0, 'retrieval_cache': 0, 'embedding_model': 0} |

**Migration order.** V1 was ingested before chunk sets existed; sql/002_chunk_sets.sql adopts those rows into cs_v1_control. Applying 002 before ingesting fails on a NOT NULL chunk_set_id, so the historical order is reproduced deliberately.

## Flags

- `CORPUS_REPRODUCTION_INCOMPLETE` = `False`
- `corpus_snapshot_reproduced` = `True`
- `RETRIEVAL_BLOCKED_BY_CORPUS` = `False`
- `holdout_split_block` = `UNCHANGED — CORPUS-002 does not clear it`

These flags describe corpus state only. The GOLD-001 150-case closure is a closed artifact and was not edited; its recorded corpus_reproduction limitation is superseded by this document rather than rewritten in place.

## Not done

- No retrieval was run: no BM25, dense, RRF, DOC-C, routing, reranking or generation, and no ranks or scores were produced.
- No embeddings were built; chunk_embedding is empty.
- The holdout and the validation split remain unfrozen.
- The historical database was read but never written.
- No GOLD record was modified.
- No document was fetched from any network source.
