# EXP-017 corpus-structure audit

Label-independent. No gold labels, no V2D miss inspection, no holdout.json, no eval-query retrieval.

Snapshot `snap_689e336380a054d8039dc35b2c09cd0a`, chunk_set `cs_v1_control`, n_chunks **14209**, n_versions **202**.

Machine-readable: `experiments/EXP-017/corpus-structure-audit.json`.

## Control chunker

Paragraph-aware, **no fixed overlap**, grouping target 3500 chars, min 200, **no hard limit**. `search_text` and `context_header` are NULL on all 14209 control rows (canonical `chunk.text` is what would be cited).

## Chunk lengths (chars)

| | |
| --- | ---: |
| min / p10 / p25 / median | 1 / 39 / 175 / 508 |
| p75 / p90 / p95 / p99 / max | 1517 / 3466 / 3485 / 3500 / 16096 |
| mean | 1097.19 |
| <200 chars | 3927 (27.6%) |
| ≥3500 chars | 150 |
| MiniLM@512 truncated (EXP-009, label-independent) | 3300 / 14209 = 23.22%; token coverage 0.761 |

Types: prose 9488, code 4432, table 289. Every chunk has a nonempty `section_path` (depth 1–5).

## Sections and adjacency

5933 `(version_id, section_path)` groups; **4057** are single-chunk. **section_path groups are not always contiguous source spans** (Beta `['Versions']`: 2 chunks, 1.53M char envelope, 20 chars of text). Do not window section envelopes.

Adjacent ordinal pairs: **14007**. Same-section 8215, cross-section 5792. **0 overlaps**, 42 abuts, 13965 gaps of 1–26 chars (median 2) — stripped whitespace. So the control passage layer has a cut at every chunk boundary.

## Why these window numbers (no eval labels)

EXP-010 measured MiniLM usable payload 510 tokens, target 448, hard 480 from the shipped tokenizer/model — not from gold spans. EXP-009 measured 4,097,597 WordPiece tokens on the 14,209 control chunks (mean 1097.2 chars) → 3.80 chars/token. Half-window stride (224 tokens / 50% overlap) is a structural Nyquist default so any token span shorter than the overlap is fully contained in some window.

Character simulation of that rule over concatenated control chunk text: **18221** projections (1.28× 14209). Two large Anthropic docs (Compliance API, Beta) dominate the tail (max 5587 windows in one doc). Exact cardinality is produced at tokenizer build time.

Integrity hashes of `cs_v1_control` recorded in the JSON (`n=14209`, span_hash `44563cbb5abb4f9a6917b2398dca7b55df60d7359d368b9873b675c78937873b`).
