# NATQ-001 slice B notes

**Slice:** NATQ-C-051 through NATQ-C-100 inclusive (50 ids)
**Verifier:** evidence verifier (ILIKE / get_span only)
**Snapshot:** `snap_689e336380a054d8039dc35b2c09cd0a`
**Written:** 2026-09-02 (America/New_York)

## Counts

- n_total: 50
- n_support: 18
- n_reject: 32

## SUPPORT ids

- NATQ-C-053: anthropic streaming event names, content_block_delta or just delta
- NATQ-C-056: can I stream anthropic thinking tokens separately from the visible answer
- NATQ-C-057: what happens if I set stream true and also submit via the batch api
- NATQ-C-058: openai realtime, ws from a python backend or webrtc from the browser
- NATQ-C-060: agents sdk stream events — is there a RunItemStreamEvent for messages vs tools
- NATQ-C-061: claude streaming, do I still need to handle ping events
- NATQ-C-065: anthropic temperature default, 1 or 0
- NATQ-C-069: claude top_k, still supported or only top_p now
- NATQ-C-071: anthropic thinking budget_tokens vs max_tokens, can the budget be larger than max
- NATQ-C-076: anthropic structured outputs — is it an output_format field or still the tool-hack
- NATQ-C-080: anthropic overloaded_error vs rate_limit_error, same backoff?
- NATQ-C-083: anthropic request too large, is it 413 or a 400
- NATQ-C-087: claude refusal, is stop_reason refusal or just end_turn with a decline
- NATQ-C-088: expired api key vs invalid, both 401?
- NATQ-C-090: tool_use_id mismatch when I return a tool_result, what error does claude give
- NATQ-C-092: agents sdk ModelBehaviorError vs UserError, when do I see each
- NATQ-C-093: claude 529 retry?
- NATQ-C-100: anthropic messages batches, did the path change from /v1/messages/batches

## Isolation / process

- Did **not** evaluate SYSTEM-H.
- Did **not** run BM25, dense retrieval, or cross-encoder.
- Did **not** open `evals/gold`, `evals/splits`, `evals/review`, or `holdout.json`.
- Did **not** pick the final 100 or write gold.
- Did **not** touch SYSTEM-* files.
- Used precomputed `/tmp/natq001/hits.json` first.
- At most **one** extra `search_chunks` (ILIKE AND) per id when hits were empty or non-answering.
- SUPPORT spans verified: `evidence_text == normalized_text[char_start:char_end]` and sha256.
- Answers taken only from quoted evidence; questions were not rewritten.
- `retrieval_was_not_run=true` on every SUPPORT packet.
- `verification_status=PENDING_CHATGPT_REVIEW`, `chatgpt_verified=null`.

## Extra-search usage (n==0 or original snippets did not answer)

One extra ILIKE search was used for: 051, 052, 054, 055, 057, 059, 062, 063, 064, 066, 067, 068, 072, 073, 074, 075, 077, 078, 079, 080, 081, 082, 083, 084, 085, 086, 089, 091, 092, 094, 095, 096, 097, 098, 099.

Original hits were sufficient (no extra search) for SUPPORT of: 053, 056, 058, 060, 061, 065, 069, 071, 076, 087, 088, 090, 100.

057, 080, 083, 092 used the extra search to locate the answering passage (batch FAQ / errors page / exceptions list). 093 used original hits on the errors page (same doc as 080 extra).

## REJECT reasons (summary)

Unsupported identifier/param (no corpus hit): 066, 067, 068, 072, 073, 074, 075, 077, 081, 082, 084, 089, 091, 094.
Wrong-passage / does not answer as written: 051, 052, 054, 055, 059, 062, 063, 064, 070, 078, 079, 085, 086, 095, 096, 097, 098, 099.
