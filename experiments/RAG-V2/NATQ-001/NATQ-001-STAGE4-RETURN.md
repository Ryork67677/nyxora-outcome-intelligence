# NATQ-001 STAGE 4 RETURN

Coordinator freeze hashes and confirmations. SYSTEM-H was not run.

1. **final gold SHA256** `332384a4d59b8f21fb882247b8d35c0b69a188ae2d936458132c497d7333453e`
   - `evals/gold/natq-001.jsonl`
   - `experiments/RAG-V2/NATQ-001/NATQ-001-GOLD.jsonl` (same bytes)
2. **validation SHA256** `a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6`
   - `evals/splits/natq-001/validation.jsonl` (40 rows)
3. **holdout SHA256** `6a7cf781c7538106605e8c85607405cd3dee2db37fdbb556aaadc913b3141dd3`
   - `evals/splits/natq-001/holdout.json` (60 gold rows; hashed from write buffer, not re-read)
4. **split-manifest SHA256** `332b833765c5c5cfff8ece26bff74bce74476c2ab6907353bf66a095bde6525b`
   - `evals/splits/natq-001/split.json`
5. **cluster-manifest SHA256** `bac1a01466200c6fdb15a82ab190ae4711b15755e94fb7ba4e5c1c320f8bf626`
   - `experiments/RAG-V2/NATQ-001/NATQ-001-cluster-manifest.json`
6. **freeze-record SHA256** `616fc4604925f5cfebaf8bcd76cc7c2c681b78b7c495ba354d1af11969dd41a5`
   - `experiments/RAG-V2/NATQ-001/NATQ-001-FREEZE.json`
7. **holdout-lock SHA256** `03e0d5749e61e73e6b9582109a74a4a9672610b7bf794daf25f46999e5ad40b2`
   - `evals/splits/natq-001/holdout.lock.json`
8. **NATQ holdout-access-log** size **0 bytes**, sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
   - `evals/splits/natq-001/holdout-access.log.jsonl` (empty)
9. **confirmation all 100 evidence checks passed:** yes. n_cases=100, n_spans=122, n_claims=251 all pass distinctive_identifier_token_v3. snapshot `snap_689e336380a054d8039dc35b2c09cd0a`. questions byte-for-byte vs authoring JSONL. versions in `corpus_snapshot_version`. critical_strings 100% pass. no duplicate IDs.
10. **provider distribution:** {"openai": 40, "anthropic": 60}
11. **cluster count:** 63
12. **confirmation no cluster straddles split:** yes (0 straddles)
13. **confirmation SYSTEM-H was not run:** yes. SYSTEM_H_SCORED=false, VALIDATION_RUN=false, HOLDOUT_RUN=false. config_hash identity only `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a`.
14. **confirmation historical V1 holdout remains untouched:** yes. `holdout.json` not opened. access log 235 bytes sha256 `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3` (expected `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`).

Flags: NATQ_001_FROZEN=true, NATQ_VALIDATION_COUNT=40, NATQ_HOLDOUT_COUNT=60, RELEASE_FROZEN=false, chatgpt_coordinator_verified=true, human_verified=false.
