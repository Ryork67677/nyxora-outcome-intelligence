# CORPUS-001 — recovery plan for the 139 missing Anthropic documents

*2026-08-31T06:25:21Z*

**139 documents.** They divide by one question: could a candidate be verified on its own, or only as part of the whole corpus?

## Group A — 40 documents with a known expected `version_id`

A candidate capture is accepted or rejected outright: normalize it with the frozen parser, hash it, derive stable_id("ver", src_id, content_hash) and require equality with the recorded identity.

16 of them also carry exact historical byte-slices from closed gold evidence, at known offsets — a candidate must reproduce those bytes at those offsets before it is even worth hashing.

## Group B — 99 documents with no recorded identity

no per-document oracle survives. A candidate can only be checked collectively: assemble all 202 (version_id, content_hash) pairs and require the manifest hash to match. That is all-or-nothing across the corpus.

## Candidate sources, in preference order

| source | exactly verifiable | status |
| --- | --- | --- |
| original local raw capture under data/raw/ | yes | not present in this environment; must be searched on the host |
| document_version rows from the original PostgreSQL database | yes | no project database found; the local cluster holds only the three default databases |
| an archived project ZIP containing data/raw | yes | the one archive lead in this project resolved to an early scaffold with no corpus |
| a timestamped web archive capture of the 2026-08-17 state | yes | archive hosts are not reachable through this session's proxy; a capture fetched elsewhere can be verified here |
| provider-owned historical sources with immutable refs | yes | this is what made the OpenAI half recoverable; the Anthropic docs have no pinned form |
| current live platform.claude.com pages | **no** | NOT a recovery path. Drift was already measured at 12 of 14 sampled documents. Useful only as a comparison lead, and only after historical recovery is exhausted. |

**What would close the gate.** historical bytes for all 139 documents. Group A can be verified one at a time; group B only in aggregate, through the manifest hash.

Nothing was fetched. Live `platform.claude.com` pages were not used as a recovery path and are not an acceptable substitute; drift was already measured at 12 of 14 sampled documents.

