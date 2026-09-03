# CORPUS-001 — 202-row recovery ledger

*2026-08-31T03:55:16Z*

## Metrics

| | count |
| --- | --- |
| expected documents | 202 |
| **`EXACT_MATCH`** — bytes reproduce *and* match a recorded identity | **49** |
| `EXPECTED_HASH_UNKNOWN` — bytes reproduce, no recorded identity to check against | 14 |
| `HASH_MISMATCH` | 0 |
| `MISSING_SOURCE` | 139 |

| provider | statuses |
| --- | --- |
| openai | `EXACT_MATCH` 49, `EXPECTED_HASH_UNKNOWN` 14 |
| anthropic | `MISSING_SOURCE` 139 |

- exact document-version reproduction rate: **24.3%** (49/202)
- normalized-hash reproduction rate (bytes reproduce, verified or not): **31.2%** (63/202)
- snapshot digest status: **NOT REPRODUCED**

> the digest is a hash over all 202 (version_id, content_hash) pairs at once. 139 documents have no recovered bytes, so the manifest cannot be assembled and no partial set can reproduce it.

## Rows

Full rows are in `CORPUS-001-recovery-ledger.json`. Summary by status:

| status | documents | meaning |
| --- | --- | --- |
| `MISSING_SOURCE` | 139 | no historical capture exists here; the live page is not an acceptable substitute and was not fetched |
| `EXACT_MATCH` | 49 | re-fetched from its pinned commit, re-parsed with the frozen parser, and its version_id matches an identity recorded before the corpus was lost |
| `EXPECTED_HASH_UNKNOWN` | 14 | reproduces deterministically, but nothing surviving records what its version_id was, so the reproduction cannot be checked |

Every `MISSING_SOURCE` row is Anthropic and carries the same next recovery path: an original raw capture, a `document_version` row, or a timestamped archive capture of the 2026-08-17 state. 40 of the 139 now have a recovered expected `version_id`, so a candidate capture for those can be verified exactly rather than judged by eye.


## A second oracle, and what it settled

`chunk_id` = `stable_id("chk", version_id, section_path, char_start, char_end, content_hash(text))`. **803** of these survived in experiment artifacts. Running the frozen chunker over every reproduced OpenAI document confirms **36** of them at chunk level — version id, section path, offsets and chunk text together, which is a stronger statement than a version-id match alone.

It reduced `EXPECTED_HASH_UNKNOWN` by **0**. The 14 are exactly the openai documents that never appeared in any logged retrieval result — neither their version_id nor any of their chunk ids survives. there is no further mapping to mine; the search is exhausted by evidence, not by effort.

## The 139, split by what could verify them

- **40** have a recorded `version_id`: a candidate capture is accepted or rejected on its own.
- **99** have none: a candidate can only be checked collectively, through the manifest hash.

See `CORPUS-001-anthropic-recovery-plan.md`.
