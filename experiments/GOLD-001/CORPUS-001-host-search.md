# CORPUS-001 — host search

*2026-08-31T06:25:21Z*

## The honest first result: the host is not reachable from here

This session runs in an isolated cloud VM (Claude Code remote execution), on a single root disk. The brief asks for a sweep of Windows user directories, WSL mounts, Desktop, Downloads, OneDrive, old repository copies and Docker volumes. None of them exist in this container.

| requested location | what it is | present here |
| --- | --- | --- |
| `/mnt/c/Users` | Windows user directories via a WSL mount | **no** |
| `/mnt/d` | second Windows drive | **no** |
| `/mnt/wsl` | WSL interop mount | **no** |
| `/media` | removable media | yes — present but empty — the stock mount point, not removable media |
| `/var/lib/docker` | Docker volumes | **no** |
| `/var/run/docker.sock` | Docker daemon | **no** |

**No Windows host, no WSL mount and no Docker daemon is reachable from this session. The gitignored data/raw captures were never in this container. A host-machine sweep has to be run on the host itself; its results can be brought back here as an artifact, which is how the earlier host evidence in this project arrived.**

This is not a new limitation: the host-side evidence already in this project's record was produced on the host and brought here as text, for exactly this reason.

## What was swept

Every accessible filesystem: `/mnt/user-data`, `/home/claude`, `/home/user`, `/root/.claude/uploads`, `/tmp`, `/var/tmp`.

**Archives, dumps, SQLite files matching the requested patterns: 0.**

| provenance anchor | files outside the repository |
| --- | --- |
| `snap_689e336380a054d8039dc35b2c09cd0a` | 220 |
| `452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e…` | 11 |
| `v1-openai-anthropic` | 49 |
| `corpus_snapshot_version` | 62 |
| `document_version` | 58 |
| `2026-08-17 04:46:19` | 35 |

Every hit resolves to this session's own working directories and logs — the packets built during GOLD-001 admission, the scratchpad, the session log. None is historical corpus material.

## Two identity oracles survived the corpus

| oracle | surviving | construction |
| --- | --- | --- |
| `version_id` | 166 | `stable_id("ver", src_id, content_hash)` |
| `chunk_id` | 803 | `stable_id("chk", version_id, section_path, char_start, char_end, content_hash(text))` |

The chunk oracle is the stronger of the two: it binds the document's version identity to its section structure, its character offsets and the chunk's own text at once, so a match cannot come from a document that merely hashes the same.

Neither can conjure a missing document. Both mean that a historical capture produced elsewhere can be **accepted or rejected here by arithmetic**, with no trust involved.

## The 14 OpenAI documents with unknown identity

Both oracles were run over all 63 reproduced OpenAI documents. 36 are confirmed at chunk level — version id, section path, offsets and chunk text together.

**14 → 14.** the 14 are exactly the OpenAI documents that never appeared in any logged retrieval result — neither their version_id nor any of their chunk ids survives. There is no further mapping to mine; the search is exhausted by evidence, not by effort.

