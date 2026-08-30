# GOLD-001 batch 007 — E/F/G implemented, calibration pilot blocked

**FIXES IMPLEMENTED AND VERIFIED — CORPUS RECOVERY EXHAUSTED AND FAILED — SAFEGUARDS ADDED — PILOT NOT RUN — STOPPED FOR INDEPENDENT REVIEW**

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

### Independent automated-review recommendation

> **INDEPENDENT AUTOMATED-REVIEW RECOMMENDATION — NOT PROJECT-OWNER APPROVAL**

> A recommendation only. It does not approve, verify or close anything, does not set human_verified, and does not alter the preregistration. Only the project owner may approve, and the preregistration is amended only by the owner.

*Recorded 2026-08-30T04:04:55Z. Concerns finding G-STRICTER-THAN-BATCH-006.*

**R1. Keep Gate G exactly as preregistered for batch 007.**

The preregistered rule requires the scope qualifier in the question AND in the critical strings. The second condition is the one that has effect: a qualifier appearing only in the question is read by no check, which is how two of batch 006's three rescoped candidates passed with the qualifier absent from the critical strings entirely. Loosening the gate to match what batch 006 accepted would remove the part that does the work, and a rule relaxed after seeing which candidates it would drop is a rule fitted to the output — the precise failure preregistration exists to prevent.

**R2. Grandfather GOLD-B006-08 under the closed batch-006 standard. Do not rewrite it, do not relabel it, do not re-open it.**

GOLD-B006-08 was authored, reviewed and approved by the owner under the rule in force for batch 006, and batch 006 is closed and hash-covered. A closed batch is a historical artifact: the standing constraint is that it is never edited, and an erratum, audit or versioned overlay is the only admissible instrument. A stricter rule preregistered for batch 007 governs batch 007. Applying it backwards would rewrite an approved record to satisfy a rule that did not exist when the owner approved it, and would break the closure hash that covers it.

**Consequence accepted.** Gate G will drop batch-007 candidates that batch 006 would have accepted. That is the intended effect of the stricter rule, not a regression, and the drop count belongs in the batch-007 generation report so the cost is visible.

**What this changes in the code:** Nothing. Gate G is already implemented as preregistered.

**Status of the finding:** Still open for the project owner. The recommendation is recorded, not applied as a decision.

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

### Recovery search — every path, and what was in it

*2026-08-30T10:59:40Z.* **NO — exhausted; the snapshot is not present in any reachable location.**

Can the exact frozen corpus snapshot snap_689e336380a054d8039dc35b2c09cd0a, captured 2026-08-17T04:46:19Z, be recovered non-destructively from anything reachable in this session?

| path searched | method | result |
| --- | --- | --- |
| git history — all refs, all commits | git log --all --diff-filter=A over data/raw/*; git rev-list --all with ls-tree for every path ever present; search of every added path for dump/archive/backup extensions | Only data/raw/.gitkeep was ever tracked (added in 185bc3a). No database dump, archive or corpus file has ever been committed on any branch. |
| tracked repository artifacts | scanned every evals/, experiments/ and docs/ JSON and JSONL for document or chunk body text | The largest carrier, experiments/EXP-011/results.json, holds 9858 characters of query-result snippets across 0 identifiable version ids. Closed records reference offsets up to character 2711869, so the corpus is at least ~2.7M characters: the artifacts hold under 0.4% of it, with no version ids and no offsets into normalized_text. Reconstruction is impossible and would in any case be the prohibited hand-reconstruction. |
| prior-session artifacts, manifests, logs and reports | searched the whole filesystem for any file naming the snapshot id | The only file outside the repository naming snap_689e336380a054d8039dc35b2c09cd0a is this session's own transcript at /root/.claude/projects/. No prior-session artifact carries corpus text. |
| database dump or backup locations named by project documentation | grep across all Markdown, Python, YAML and the Makefile for pg_dump, pg_restore, backup, .dump and restore instructions | The project documentation names no backup or dump location anywhere. There is no documented restore path; the corpus was only ever produced by scripts/fetch_corpus.py into gitignored data/raw/ and ingested from there. |
| Docker volumes (docker-compose.yml declares rag_pgdata) | inspected /var/lib/docker/volumes and the Docker daemon | /var/lib/docker/volumes does not exist and no Docker daemon is running. The rag_pgdata volume has never existed in this container. |
| PostgreSQL data directories | pg_lsclusters; started the 16/main cluster; enumerated databases, user tables and WAL | One cluster, initdb'd 2026-03-31 at image build. It holds only postgres, template0 and template1, zero user tables, and a single WAL segment 000000010000000000000001 — it has never held project data. A second finding: the pgvector extension is not available in this cluster at all (0 rows in pg_available_extensions, no extension files on disk), so the expected schema cannot even be created here, let alone populated, because sql/001_init.sql requires the VECTOR type. |
| persistent Claude workspace and mounted volumes | findmnt for non-overlay mounts; listed /home/user, /mnt/user-data, /mnt/attach, /srv, /root/.claude/backups and /root/.claude/projects | All empty of corpus. /mnt/user-data/working, /mnt/attach and /srv are empty directories; /root/.claude/backups holds only Claude configuration backups. |
| filesystem-wide archive sweep | find / -xdev for *.dump, *.pgdump, *.sql.gz, *.tar, *.tar.gz, *.tgz, *.bak and *backup* over 100KB, excluding system and package directories | No candidate found. No provider documentation exists anywhere outside the repository. |

**Constraints observed.**

- No current live URL was fetched.
- No toy or fixture data was used or accepted as corpus.
- SYSTEM-A and SYSTEM-B were not run.
- Validation and holdout were not inspected.
- Fingerprint proof was required before any corpus would have been accepted; none was offered because none was found.

### The precise remaining external artifact

One of two artifacts, neither of which exists in this environment. Both must reproduce the frozen fingerprint; nothing else is admissible.

**Option A — A PostgreSQL dump of the `rag` database as it stood on or after 2026-08-17.**

- document_source rows for all 202 documents
- document_version rows carrying normalized_text and content_hash
- corpus_snapshot and corpus_snapshot_version rows for snap_689e336380a054d8039dc35b2c09cd0a
- *Produced by:* pg_dump of the machine that ran batches 001-006

**Option B — The 202 raw Markdown files that were under data/raw/, as captured 2026-08-17T04:46:19Z.**

- the files at the local_path values in data/manifests/v1-openai-anthropic.yaml
- byte-identical to the capture, since content_hash is taken over the ingested text
- *Produced by:* the gitignored data/raw/ tree on the machine that ran scripts/fetch_corpus.py
- *Note:* Re-running fetch_corpus.py today does NOT produce this: it fetches current documentation.

**Environment prerequisite.** The target PostgreSQL must have the pgvector extension available. This container does not, so sql/001_init.sql cannot create the schema here even given the data.

**Acceptance test.** scripts/rederive_unbuildable.py refuses unless the restored corpus hashes to snap_689e336380a054d8039dc35b2c09cd0a, every closed span re-hashes at its recorded offsets, and the re-derived unbuildable count reproduces 2482. Passing all three is the proof; a snapshot row saying so is not.

### Recovery checklist

*The ordered, precise steps that unblock the calibration pilot. Nothing here has been performed; the pilot remains not run.*

**Hard prohibitions.**

- Do NOT substitute the current live contents of the manifest URLs. The documentation has moved on from the capture date, so offsets and evidence hashes would not match the frozen snapshot and the evidence would not be the frozen evidence.
- Do NOT substitute toy, synthetic or fixture data. tests/fixtures/docs/widget_v2.md is a synthetic document for unit tests and is not corpus.
- Do NOT reconstruct spans by hand from quotations in closed batch records.
- Do NOT run any retrieval system at any step; SYSTEM-A and SYSTEM-B stay frozen.

**Step 1 — Restore the exact frozen source-corpus snapshot into the expected PostgreSQL schema.**

Create the `rag` database and role and apply sql/001_init.sql, sql/002_chunk_sets.sql, sql/003_search_text.sql and sql/004_embedding_cache.sql, then restore the corpus from a backup of the snapshot — or restore data/raw/ (gitignored, 202 documents) and re-ingest it. The snapshot must be the one captured 2026-08-17T04:46:19Z, not a re-fetch.

- *Expected:* document_source, document_version and corpus_snapshot_version populated; snapshot_id snap_689e336380a054d8039dc35b2c09cd0a present.
- *Done when:* scripts/export_batch_006.py's load_docs() returns 202 documents.

**Step 2 — Verify the restored corpus is the frozen one, by fingerprint, before using it.**

Identity is not the snapshot id — that is a label anyone can write. Re-read each closed batch-006 span from the restored corpus at its recorded (version_id, char_start, char_end) and re-hash it; every evidence_hash must reproduce exactly. Batch 006's nine records give nine independent checks against text that cannot have drifted, and batches 001-005 give more. Also confirm rag_v1.systems.FROZEN_HASHES still equals SYSTEM-A 9afcb5b7… and SYSTEM-B 304c3509….

- *Expected:* every re-hash matches its recorded evidence_hash; document count 202.
- *Done when:* zero hash mismatches. A single mismatch means the restored corpus is not the frozen snapshot — stop, do not proceed to step 3.

**Step 3 — Deterministically re-derive the batch-006 NO_BUILDER / UNBUILDABLE span set.**

The set was counted, never persisted: scripts/export_batch_006.py:733 increments removed['unbuildable'] and returns, discarding the fact. Re-run batch 006's miners against the restored snapshot at the same commit and record, for each fact where the builder returns None, its (version_id, char_start, char_end, evidence_text) rather than only a count. Do not change any builder while doing this: the set is defined by the builders as they were.

- *Expected:* the recorded count reproduces exactly: 2482 unbuildable facts.
- *Done when:* the re-derived count equals 2482. A different count means the derivation is not reproducing batch 006's conditions — diagnose before selecting anything.

**Step 4 — Select the preregistered 10 pilot cases from that set, and only from it.**

Take 10 spans that failed batch 006 ONLY because no builder could express them. Exclude any span that failed a semantic gate — those failed for reasons paraphrasing does not fix — and exclude any span already spent by a closed batch. Record the selection basis for each so the choice is auditable and not a convenience sample.

- *Expected:* 10 spans, each traceable to the step-3 set.
- *Done when:* each of the 10 carries its version_id, offsets and selection basis.

**Step 5 — Run the calibration pilot and measure the four preregistered thresholds.**

Author in the preregistered order — frozen evidence, literal source fact, subject/relation/object, atomic claims, and only then the paraphrased question — never the forbidden order. Record all eight required fields on every case. Run the A-G entailment self-check, where any failure is a DROP with no flag-and-continue branch, then every retained gate including the new E, F and G. No retrieval is run on the pilot.

- *Expected:* factually sound >= 8 of 10; unsupported claims 0; relation-direction reversals 0; scope broadening 0. Wording cleanup does not count against the criterion.
- *Done when:* the pilot is independently reviewed against those four thresholds. If it fails, do not scale the lane: revise the authoring contract and re-pilot.

Until the pilot runs and is independently reviewed, the paraphrasing lane does not scale and no batch-007 candidate is authored. The preregistration is explicit that a failed or absent pilot means revising the contract and re-piloting — not proceeding.

## 5. Reproducibility safeguards added

The blocker is not only that the corpus is missing. It is that batch 006 recorded a count instead of identities, so even a restored corpus needs a re-derivation step that batch 006 made necessary. These safeguards mean a future batch does not repeat that.

Implemented in `src/rag_v1/gold/provenance.py`, tested in `tests/test_gold001_provenance.py`.

| | need | provides | verified by |
| --- | --- | --- | --- |
| **S1** | future generation persists the unbuildable-span identities | UnbuildableLog records (version_id, char_start, char_end, evidence_text, evidence_hash, reason) for every fact a builder declines, and writes a manifest. NO_BUILDER is kept distinct from SEMANTIC_GATE, because the pilot may draw only from the former. | identity is kept not just counted; the same span twice is one entry; the two reasons stay distinguishable; the manifest carries the entries |
| **S2** | corpus snapshot fingerprint | fingerprint() reproduces the snapshot-id construction of rag_v1.snapshot.create_snapshot without a database, and verify_fingerprint() answers whether a corpus hashes to the id it claims. chunking_config_from_settings() builds the hashed config so a caller cannot silently mis-key it. | construction matches rag_v1.ids primitives exactly; one changed content hash changes the id; a missing document changes the id; a corpus claiming an id it does not hash to is rejected |
| **S3** | restore verifier | verify_restored_corpus() re-reads every closed span at its recorded offsets and re-hashes it against evidence_hash, reporting mismatches and missing versions rather than a bare boolean. | all 137 closed spans across batches 003-006 satisfy sha256(evidence_text) == evidence_hash; a correct restore verifies; a single changed character fails; an offset shifted by one fails; a missing document is reported, not skipped |
| **S4** | deterministic pilot-selection manifest | select_pilot_cases() orders by span identity and records a selection basis per case, so the same input returns the same ten. Semantic-gate failures and spans already spent by a closed batch are excluded; a short pool is reported short rather than padded. | selection is order-independent; takes the preregistered ten; never selects a semantic-gate failure; excludes spent spans; records why each was chosen; reports a short pool |
| **S5** | a guard so no report can call an unrun pilot passed | pilot_thresholds_unmet() returns which of the four preregistered thresholds a result fails. An absent result fails all four, because unmeasured is not met. | an unrun pilot fails all four; a passing pilot meets all four; one unsupported claim fails; seven of ten sound fails |

**Harness — `scripts/rederive_unbuildable.py`.** Recovers the identities batch 006 discarded, by re-running batch 006's own miners and builders imported unmodified. The unbuildable set is defined by those builders as they were, so re-deriving it with a changed builder would answer a different question.

*scripts/export_batch_006.py is imported, never edited. Editing it would break the very re-derivation the recovery checklist depends on.*

It refuses unless:

- the corpus is reachable
- it hashes to the frozen snapshot id
- every closed span re-reads and re-hashes correctly
- the re-derived count reproduces the count batch 006 recorded

Run in this environment it refuses at the first check and writes nothing, both with PostgreSQL stopped and with it running but empty.

## 6. Invariants

- `retrieval_was_not_run` is still true; `systems_executed` is still `[]`. No retrieval system was run at any point.
- Closed batches modified: **0**. Dataset records modified: **0**. Eligibility state modified: **false**.
- Validation and holdout were neither inspected nor modified.
- `human_verified` set by this work: **0**. Only the project owner may set it.
- Files added (7), modified (0):
  - `src/rag_v1/gold/factidentity.py` (new)
  - `src/rag_v1/gold/reasoningtype.py` (new)
  - `src/rag_v1/gold/questionscope.py` (new)
  - `tests/test_gold001_b007_fixes.py` (new)
  - `src/rag_v1/gold/provenance.py` (new)
  - `tests/test_gold001_provenance.py` (new)
  - `scripts/rederive_unbuildable.py` (new)

**Next:** The calibration pilot cannot run until the external artifact named in recovery_search.remaining_external_artifact_required is supplied: a PostgreSQL dump of the corpus, or the 202 raw files captured 2026-08-17, restored into a PostgreSQL that has pgvector. Then work the recovery checklist in order — scripts/rederive_unbuildable.py enforces steps 1 to 3 and refuses on any failure. The G-STRICTER finding remains open for the project owner; the recorded recommendation is not owner approval. The paraphrasing lane does not scale until the pilot passes and is independently reviewed.
