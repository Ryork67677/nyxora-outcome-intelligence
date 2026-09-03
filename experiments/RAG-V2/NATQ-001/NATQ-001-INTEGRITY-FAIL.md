# NATQ-001 INTEGRITY FAIL

Stage 4 freeze **aborted**. No freeze artifacts written (no gold, no split freeze, no NATQ holdout lock).

**Generated:** 2026-09-02T18:27:16Z (ET 2026-09-02T14:27:16-0400)
**Snapshot:** `snap_689e336380a054d8039dc35b2c09cd0a`

## What passed

| check | result |
|---|---|
| exactly 100 cases (84 unchanged + 16 Round-2) | PASS |
| no duplicate candidate IDs | PASS |
| snapshot id exact `snap_689e336380a054d8039dc35b2c09cd0a` | PASS |
| questions match original authoring JSONL byte-for-byte | PASS |
| every evidence span `normalized_text[char_start:char_end]==evidence_text` | PASS (122 spans, 49 version_ids, all in snapshot) |
| every evidence_hash == sha256(utf-8 evidence_text) | PASS |
| every version_id in corpus_snapshot_version for this snapshot | PASS |
| proposed split 40/60, each id once, no overlap | PASS |
| no cluster straddles validation/holdout | PASS (63 clusters) |
| SYSTEM-H not run | PASS |
| V1 holdout.json not opened | PASS |
| V1 holdout-access.log.jsonl | 235 bytes, `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3` |

## What failed (blocking)

### Atomic claims: 9 claim(s) on 9 case(s)

**Method:**

`distinctive_identifier_token_v3: concatenate all expected_evidence.evidence_text; markdown-unescape (backslash-escaped punctuation unescaped; strip backtick characters). From each atomic claim extract: (a) backtick-quoted spans; (b) identifiers containing '_' or a digit; (c) dotted identifiers like foo.bar; (d) CamelCase with an INTERNAL capital ([a-z][A-Z]). Skip ellipsis and abbreviations e.g./i.e./etc. Each extracted token must appear as a casefold substring in unescaped evidence. Dotted identifiers pass if the full string appears OR every component appears. Light inflection: if token missing, accept stem stripping trailing s/es/ed/ing (stem len>=4).`

Checked 251 claims; 242 pass; **9 fail**.

| id | Round-2 | missing distinctive token(s) | claim |
|---|---|---|---|
| NATQ-C-008 | no | `ident:failure_error_function` | Default failure_error_function runs default_tool_error_function which tells the LLM an error occurred. |
| NATQ-C-022 | no | `ident:file_id` | PDFs are provided as a URL, as a base64-encoded PDF in document content blocks, or by file_id. |
| NATQ-C-032 | no | `ident:ModelSettings` | Example sets parallel_tool_calls=False on ModelSettings. |
| NATQ-C-069 | no | `backtick:top_p, ident:top_p` | `top_k` is recommended for advanced use cases only, not removed in favor of `top_p` only. |
| NATQ-C-087 | no | `backtick:stop_reason, ident:stop_reason` | `stop_reason` can be `"refusal"`. |
| NATQ-C-131 | no | `dotted:chat.completions.parse` | chat.completions.parse() returns a completion whose message may have parsed content or a refusal. |
| NATQ-C-167 | no | `ident:tool_result` | tool_result content is optional string or array of TextBlockParam or ImageBlockParam (and others). |
| NATQ-C-179 | no | `ident:cache_control` | The array form is TextBlockParam blocks (text/type, optional cache_control). |
| NATQ-C-189 | no | `ident:mouse_move` | Basic actions include screenshot, left_click, type, key, and mouse_move. |

These identifiers do not appear in the case `evidence_text` even after markdown unescape. They may exist in `context_before` or `section_path`, which this check does not count.

### Critical strings: 1 miss(es) on 1 case(s)

**Method:** exact substring in concatenated evidence_text, else markdown-unescape, else dotted-path components.

| id | Round-2 | string |
|---|---|---|
| NATQ-C-016 | yes | `role": "system"` |

## Failing IDs

- claims: NATQ-C-008, NATQ-C-022, NATQ-C-032, NATQ-C-069, NATQ-C-087, NATQ-C-131, NATQ-C-167, NATQ-C-179, NATQ-C-189
- critical_strings: NATQ-C-016

## Isolation (still holds)

- Did not freeze NATQ-001.
- Did not run SYSTEM-H / BM25 / dense / CE.
- Did not open `evals/splits/gold150-v1/holdout.json`.
- Did not reshuffle the split.
- Did not modify question wording.

## Next

Coordinator must repair the failing claims/critical_strings (or authorize a different recorded token method) before Stage 4 freeze can proceed.
