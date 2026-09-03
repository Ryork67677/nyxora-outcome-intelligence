# NATQ-001 ROUND 2 report

Generated 2026-09-02 14:13 EDT (2026-09-02T18:13:16Z).

## OUTPUT FIRST

| item | value |
|---|---|
| snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| n_round2_ids | 16 |
| n_replaced | **0** |
| replacements from 12 held-out SUPPORT | none |
| tightened (answer/claims only) | 6 |
| evidence-added (and/or expanded span) | 10 |
| REJECT among the 16 | 0 |
| proposed coordinator re-review | 16 |
| 84 PASS packets | **untouched** (candidates.jsonl not rewritten) |
| split changes | **none** (no replacements; cluster membership unchanged) |
| freeze | **not done** |
| SYSTEM-H evaluated | **no** |
| BM25 / dense / CE / retrieval | **not run** |
| V1 holdout.json opened | **no** |

## Per-id action

| ID | action | notes |
|---|---|---|
| NATQ-C-002 | tightened | Removed 'Agent holds config; Runner is what actually invokes the model.' Kept the supported Runner-loop-calls-LLM answer. Evidence span unchanged. |
| NATQ-C-005 | evidence-added | Kept needs_approval=True. Added E2 showing the exact @tool(needs_approval=True) decorator example. |
| NATQ-C-014 | evidence-added | Kept 'agents as tools'. Added E2 with spanish_agent.as_tool(...) / french_agent.as_tool(...). |
| NATQ-C-016 | tightened | Removed the unsupported model-scope qualifier 'On some newer models'. Evidence span unchanged. |
| NATQ-C-026 | evidence-added | Removed 'not a tool'. Added E3: 'When citations are enabled, responses include multiple text blocks with citations.' |
| NATQ-C-030 | evidence-added | Added E2 from handling-stop-reasons: client tool_use is continued with tool_result blocks, not as-is resume. |
| NATQ-C-044 | evidence-added | Question asks bash AND text editor. Added frozen text-editor E3 rather than reject/replace. |
| NATQ-C-047 | evidence-added | Added direct hosted-vs-FunctionTool evidence. Did not infer; did not replace. |
| NATQ-C-120 | tightened | Dropped Claude-style cache_control absence claim. Kept prompt_cache_options implicit/explicit and 30m TTL. |
| NATQ-C-127 | tightened | Removed 'Server-side compaction is a different, primary strategy; this page is fine-grained clearing.' Claims already matched the tool-result-clearing evidence. |
| NATQ-C-154 | evidence-added | Kept web_search_20260209 as current type. Added E2 anchoring web_search_20250305 in the same Messages schema. |
| NATQ-C-160 | evidence-added | Added general Files API document-source evidence (E2) rather than scoping the answer to beta-only. |
| NATQ-C-163 | evidence-added | Added frozen SSE span with event: content_block_delta plus input_json_delta/partial_json. |
| NATQ-C-193 | tightened | Removed 'there is no unsuffixed anthropic-organization / anthropic-workspace'. Evidence spans unchanged. |
| NATQ-C-219 | tightened | Removed process-default / per-Runner-constructor claim. Evidence span unchanged. |
| NATQ-C-172 | evidence-added | Expanded E1 through the Note that names Claude Haiku 4.5. Corrected answer: Haiku 4.5 supports computer use with computer-use-2025-01-24, not 'haiku is absent'. |

## C-172 resolution

UNCERTAIN resolved from frozen `Computer use tool` (`ver_d9ba3ab0d872dd86047c7ed6dc783235`), not inferred. The Compatibility supported-models list for `computer-use-2025-11-24` is opus/sonnet IDs. The immediately following Note states that **Claude Haiku 4.5** (with Sonnet 4.5, Opus 4.1, Sonnet 4, Opus 4) uses the earlier beta header `computer-use-2025-01-24` instead of `computer-use-2025-11-24`. Answer corrected: Haiku 4.5 **does** support computer use, via the earlier header. Evidence E1 expanded through `</Note>` so the packet is self-contained.

## Replacements

None. ChatGPT preferred not replacing automatically. C-044 gained text-editor evidence; C-047 gained hosted-vs-FunctionTool evidence. Neither was rejected.

## Counts for the 16

| | n |
|---|---|
| repaired in place | 16 |
| REJECT | 0 |
| replaced from held-out SUPPORT | 0 |
| still needing coordinator verdict | 16 |

Coordinator Round-1 on the original 100: **84 PASS · 15 FIX_REQUIRED · 1 UNCERTAIN · 0 FAIL**.

After Round 2, the 84 PASS remain PASS (untouched). The 16 are resubmitted for coordinator review; this report does **not** self-assign PASS.

## Split

PROPOSED / NOT_FROZEN. No cluster membership changes. No freeze.

## Isolation confirmations

- Did **not** freeze NATQ-001.
- Did **not** run SYSTEM-H or score any candidate.
- Did **not** run BM25, dense retrieval, or cross-encoder.
- Did **not** open `evals/splits/gold150-v1/holdout.json`.
- Did **not** rewrite any of the 16 questions.
- Did **not** modify `NATQ-001-candidates.jsonl` (84 PASS remain byte-for-byte).
- Evidence checks used `get_span` on frozen `normalized_text` only (DSN corpus002_restore).
- Every new/changed span: `evidence_text == normalized_text[char_start:char_end]` and sha256 match.

## Outputs

All under `experiments/RAG-V2/NATQ-001/round2/`:

1. `NATQ-001-round2-packets.jsonl`
2. `NATQ-001-round2-diff.md`
3. `NATQ-001-round2-review.md`
4. `NATQ-001-round2-report.md` (this file)
5. `NATQ-001-round2-hashes.json`

## STOP

Do **not** freeze. Do **not** post to ChatGPT from this agent. Do **not** evaluate SYSTEM-H.
Send the Round-2 packet to coordinator ChatGPT for review of these 16 only.
