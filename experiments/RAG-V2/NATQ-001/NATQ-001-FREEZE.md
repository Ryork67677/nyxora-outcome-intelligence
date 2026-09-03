# NATQ-001 STAGE 4 FREEZE

**Frozen at:** 2026-09-03T03:34:20Z (ET 2026-09-02T23:34:20-0400)
**Snapshot:** `snap_689e336380a054d8039dc35b2c09cd0a`
**Repo:** `evals/gold/natq-001.jsonl` + `evals/splits/natq-001/`

## Flags

| flag | value |
|---|---|
| NATQ_001_FROZEN | true |
| NATQ_VALIDATION_COUNT | 40 |
| NATQ_HOLDOUT_COUNT | 60 |
| SYSTEM_H_SCORED | false |
| VALIDATION_RUN | false |
| HOLDOUT_RUN | false |
| RELEASE_FROZEN | false |
| chatgpt_coordinator_verified | true |
| human_verified | false |
| SYSTEM-H config_hash (identity only, not scored) | `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` |

## Integrity (all 100, blocking, passed)

- questions match original authoring JSONL byte-for-byte
- every expected_evidence span: `document_version.normalized_text[char_start:char_end] == evidence_text`
- every `evidence_hash == sha256(utf-8 evidence_text)`
- every `version_id` in snapshot `snap_689e336380a054d8039dc35b2c09cd0a` via `corpus_snapshot_version`
- atomic claims: distinctive_identifier_token_v3: concatenate all expected_evidence.evidence_text; markdown-unescape (backslash-escaped punctuation unescaped; strip backtick characters). From each atomic claim extract: (a) backtick-quoted spans; (b) identifiers containing '_' or a digit; (c) dotted identifiers like foo.bar; (d) CamelCase with an INTERNAL capital ([a-z][A-Z]). Skip ellipsis and abbreviations e.g./i.e./etc. Each extracted token must appear as a casefold substring in unescaped evidence. Dotted identifiers pass if the full string appears OR every component appears. Light inflection: if token missing, accept stem stripping trailing s/es/ed/ing (stem len>=4).
- claims checked: 251/251 pass
- critical_strings present (exact OR markdown-unescape OR dotted components)
- no duplicate candidate IDs
- exactly 100 cases
- snapshot id exact
- spans checked: 122

## Split

- validation 40 / holdout 60 frozen from proposed-split.json (membership unchanged)
- cluster count: 63
- no cluster straddles validation and holdout

## Isolation

- SYSTEM-H was **not** run / not scored
- BM25 / dense / CE / retrieval was **not** run
- gold150-v1 holdout.json was **not** opened
- gold150-v1 holdout-access.log.jsonl: 235 bytes, sha256 `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3` (confirmed True)
- NATQ holdout-access.log.jsonl: 0 bytes (empty)

## Hashes

See `NATQ-001-hashes.json`.

| artifact | sha256 |
|---|---|
| gold 100 | `332384a4d59b8f21fb882247b8d35c0b69a188ae2d936458132c497d7333453e` |
| validation 40 jsonl | `a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6` |
| holdout 60 | `6a7cf781c7538106605e8c85607405cd3dee2db37fdbb556aaadc913b3141dd3` |
| split.json | `332b833765c5c5cfff8ece26bff74bce74476c2ab6907353bf66a095bde6525b` |
| cluster manifest | `bac1a01466200c6fdb15a82ab190ae4711b15755e94fb7ba4e5c1c320f8bf626` |
| freeze record | `616fc4604925f5cfebaf8bcd76cc7c2c681b78b7c495ba354d1af11969dd41a5` |
| holdout.lock.json | `03e0d5749e61e73e6b9582109a74a4a9672610b7bf794daf25f46999e5ad40b2` |
| NATQ holdout-access.log.jsonl | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (0 bytes) |

## STOP

Do not run SYSTEM-H. Validation n=40 is the next authorized experiment, not this stage.
