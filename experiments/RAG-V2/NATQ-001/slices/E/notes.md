# NATQ-001 extra slice E notes

- Slice: NATQ-C-191 through NATQ-C-230 (40 extra candidates)
- Snapshot: `snap_689e336380a054d8039dc35b2c09cd0a`
- Schema: natq-001-v1
- Verifier: evidence-verifier extra slice E
- Timestamp (America/New_York): 2026-09-02 1:39 PM EDT start; write-up same afternoon

## Counts

- n_support: 16
- n_reject: 24
- n_total: 40

## SUPPORT ids

NATQ-C-191, NATQ-C-193, NATQ-C-199, NATQ-C-200, NATQ-C-201, NATQ-C-203, NATQ-C-205, NATQ-C-207, NATQ-C-209, NATQ-C-212, NATQ-C-217, NATQ-C-218, NATQ-C-219, NATQ-C-224, NATQ-C-225, NATQ-C-227

## Process

1. Loaded questions **unchanged** from `/workspace/natq001-authoring/NATQ-001-raw-questions-extra.jsonl`.
2. Wrote a batch ILIKE search for all 40 ids to `/tmp/natq001/hits-extra-E.json` (AND terms from the question; provider from intended_provider when openai/anthropic). No precomputed hits.json for extras.
3. If a hit snippet answered as written, expanded a tight contiguous span via `get_span`/`find_offset` on `document_version.normalized_text`.
4. If n==0 or snippets did not answer: **at most one** extra `search_chunks` (ILIKE). Still no → REJECT. Questions were not rewritten into corpus language.
5. Verified `evidence_text == normalized_text[char_start:char_end]` and sha256.
6. Rejected unsupported, stretched, or conflicting items. `genuine_ambiguity` kept only when the corpus itself presents it (NATQ-C-193).

## Isolation

- Did **not** run BM25, dense retrieval, or cross-encoder.
- Did **not** open `evals/gold`, `evals/splits`, `evals/review`, or `holdout.json`.
- Did **not** evaluate SYSTEM-H or touch SYSTEM-* files.
- Did **not** pick the final 100 or write gold.
- Did **not** modify slices A/B/C.
- `retrieval_was_not_run` is true on every SUPPORT packet.

## Extra-search used (one per unclear id)

Used when original n=0 or snippets did not answer. Extra n=0 still REJECT. Did not chain additional queries.

Extra ILIKE: 192, 193, 194, 196, 197, 198, 200, 202, 204, 205, 206, 207, 208, 210, 211, 213, 215, 216, 220, 221, 222, 223, 224, 225, 226, 228, 229, 230.

Original hits sufficient (no extra) for SUPPORT of: 191, 199, 201, 203, 209, 212, 217, 218, 219, 227.

200, 205, 207, 224, 225 used the extra search to locate the answering passage.

## Example SUPPORT (3)

- NATQ-C-191: "tool_choice none with thinking enabled, allowed or 400"
- NATQ-C-201: "agents sdk handoff input_filter — can I strip prior tool calls from the history I pass the next agent"
- NATQ-C-218: "agents sdk MCP, MCPServerStdio vs the streamable http one, which do I use for a remote server"

## Example REJECT reasons (3)

- NATQ-C-196: gzip / Content-Encoding original n=0 and extra n=0
- NATQ-C-208: Responses background=true / GET /responses/{id} extra n=0
- NATQ-C-223: silence_duration_ms original n=0 and extra n=0
