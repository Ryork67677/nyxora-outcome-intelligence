# GOLD-001 batch 007 — E/F/G implemented, calibration pilot blocked

**FIXES IMPLEMENTED AND VERIFIED — PILOT NOT RUN — STOPPED FOR INDEPENDENT REVIEW**

*Written 2026-08-30T03:58:20Z against corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a`, commit `c65d5204901e`. Follows `GOLD-001-batch-007-preregistration.md` and `.json`.*

The three preregistered generator defects are implemented and verified against the real candidates that revealed them. **The calibration pilot was not run**: the frozen evidence it must draw from is not present in this environment, and no substitute for it is admissible. That is the headline, and section 4 is the whole of it.

## 1. State verified before anything was written

| | | |
| --- | --- | --- |
| human_verified | **90** | PASS |
| holdout_eligible | **90** | PASS |
| human_rejected | **9** | PASS |
| genuine multi-hop | 1 | PASS |
| closure sha256 | `7ff5596c755a01fc…` | recomputed, PASS |
| retrieval_was_not_run | true | PASS |
| systems_executed | `[]` | PASS |
| SYSTEM-A / SYSTEM-B | `9afcb5b7…` / `304c3509…` | frozen, unchanged |
| batch-007 candidate or pilot artifact | none | PASS |

The hash was recomputed from the nine closed records rather than read off the closure, so the state is checked, not quoted.

## 2. What was implemented

### E. cross-library duplicate facts are invisible to duplicate control

`src/rag_v1/gold/factidentity.py`

compares the normalised (subject, relation, object) triple in addition to text and offsets; flags, never drops; reports 'not_comparable' when no triple can be read

*Verified against the real GOLD-B005-11 / GOLD-B006-06 pair the owner caught.*

### F. compound single-span facts are labelled by their first verb

`src/rag_v1/gold/reasoningtype.py`

classifies from the whole sentence; lifecycle first whatever the verb; configuration_interaction requires an interaction verb, so one requirement naming two identifiers is a lookup

*Verified against all nine batch-006 candidates against the owner's labels.*

### G. questions inherit the breadth of their frame, not of their evidence

`src/rag_v1/gold/questionscope.py`

a scope qualifier in the evidence must appear in the question AND in the critical strings, else the candidate does not export; a comparative aside is not a scope

*Verified against the three rescoped candidates as generated and as approved.*

**E — the pair the owner caught is now visible.** GOLD-B005-11 (OpenAI Python library) and GOLD-B006-06 (TypeScript/JavaScript library) share no question text, no span offsets and no span text, which is why the old comparison could not see them. Both now normalise to the triple `('aws_bedrock_base_url', 'override', 'endpoint')` and the second is flagged. Batch 005 predates the triple fields, so its triple is derived from its frozen evidence — never from its question. Within batch 006 the check raises **0 false positives**.

**F — 9/9 agreement with the owner's labels**, including all 3 the owner had to relabel.

| id | generated | owner | whole-sentence | |
| --- | --- | --- | --- | --- |
| 01 | `configuration_interaction` | `exact_lookup` | `exact_lookup` | PASS **relabelled** |
| 02 | `error_behavior` | `error_behavior` | `error_behavior` | PASS |
| 03 | `exact_lookup` | `lifecycle_compatibility_migration` | `lifecycle_compatibility_migration` | PASS **relabelled** |
| 04 | `exact_lookup` | `exact_lookup` | `exact_lookup` | PASS |
| 05 | `exact_lookup` | `exact_lookup` | `exact_lookup` | PASS |
| 06 | `configuration_interaction` | `configuration_interaction` | `configuration_interaction` | PASS |
| 07 | `configuration_interaction` | `configuration_interaction` | `configuration_interaction` | PASS |
| 08 | `configuration_interaction` | `lifecycle_compatibility_migration` | `lifecycle_compatibility_migration` | PASS **relabelled** |
| 09 | `exact_lookup` | `exact_lookup` | `exact_lookup` | PASS |

**G — the three rescoped questions no longer export as generated.**

| id | as generated | as approved |
| --- | --- | --- |
| 02 | `SCOPE_MISSING_FROM_CRITICAL_STRINGS` — dropped | `SCOPED` — exports |
| 04 | `SCOPE_MISSING_FROM_QUESTION` — dropped | `SCOPED` — exports |
| 05 | `SCOPE_MISSING_FROM_QUESTION` — dropped | `SCOPED` — exports |

## 3. A finding the reviewer must decide

**G-STRICTER-THAN-BATCH-006 — `GOLD-B006-08`.** The preregistered rule requires the scope qualifier in the question AND in the critical strings. GOLD-B006-08 carries 'OpenAI Python SDK' in its question but not in its critical strings, and the owner approved it. Implemented as preregistered rather than loosened; recorded so the reviewer can decide whether batch 007 should hold to the stricter rule.

*recorded as a passing test, not tuned away.*

## 4. The calibration pilot was not run

**BLOCKED — the frozen evidence the pilot must draw from is not present in this environment**

The preregistration fixes the pilot's input exactly: *10 evidence spans that failed batch 006 ONLY because no builder could express them — NO_BUILDER / UNBUILDABLE.* That input cannot be obtained here, on four independent grounds.

1. **the NO_BUILDER/UNBUILDABLE set was counted, never persisted.** batch 006 recorded removed.unbuildable = 2482 as an integer; scripts/export_batch_006.py:733 increments the counter and returns, discarding the fact's identity. No artifact records which spans they were.

2. **the corpus text exists only in Postgres, and this container has no corpus.** load_docs() reads document_version.normalized_text joined to corpus_snapshot_version. The local cluster starts but holds only postgres/template0/template1 — there is no 'rag' database and no snapshot.

3. **the raw documents are not in the repository.** data/raw/ contains only .gitkeep and is gitignored by design; data/cache/ is empty.

4. **re-fetching would not reproduce the frozen snapshot.** data/manifests/v1-openai-anthropic.yaml lists 202 documents captured 2026-08-17 with no text and no content hashes. Re-fetching returns the documentation as it stands today, so offsets and evidence hashes would not match snap_689e336380a054d8039dc35b2c09cd0a, and the evidence would not be the frozen evidence.

No pilot case was authored. Authoring 10 cases against invented or re-fetched evidence would produce exactly what the preregistration exists to prevent — a benchmark testing what its author imagined rather than what the documentation says — and the pilot's four thresholds would measure nothing.

### The four thresholds, unmeasured

| criterion | threshold | measured |
| --- | --- | --- |
| independently judged factually sound | >= 8 of 10 | **not measured — pilot not run** |
| unsupported claims | 0 | **not measured — pilot not run** |
| relation direction reversals | 0 | **not measured — pilot not run** |
| scope broadening | 0 | **not measured — pilot not run** |

**To unblock:** Restore the corpus snapshot into Postgres (or restore data/raw/ and re-ingest), then re-run batch 006's miners to re-derive the spans that reach no builder and take the pilot's 10 from that set.

Until the pilot runs and is independently reviewed, the paraphrasing lane does not scale and no batch-007 candidate is authored. The preregistration is explicit that a failed or absent pilot means revising the contract and re-piloting — not proceeding.

## 5. Invariants

- `retrieval_was_not_run` is still true; `systems_executed` is still `[]`. No retrieval system was run at any point.
- Closed batches modified: **0**. Dataset records modified: **0**. Eligibility state modified: **false**.
- Validation and holdout were neither inspected nor modified.
- `human_verified` set by this work: **0**. Only the project owner may set it.
- Files added (4), modified (0):
  - `src/rag_v1/gold/factidentity.py` (new)
  - `src/rag_v1/gold/reasoningtype.py` (new)
  - `src/rag_v1/gold/questionscope.py` (new)
  - `tests/test_gold001_b007_fixes.py` (new)

**Next:** Independent review of the three fixes, and a decision on the G-STRICTER finding, before the corpus is restored and the pilot is run. The paraphrasing lane does not scale until the pilot passes.
