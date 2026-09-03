# NATQ-001 STAGE 4 REPAIR

Classification: **EVIDENCE_BOUNDARY / STALE-METADATA REPAIR** (not BENCHMARK_REJECTION).

Claim method kept: `distinctive_identifier_token_v3` (restored into `/tmp/natq001/stage4_freeze.py` before the rerun). Critical-string method kept: exact substring OR markdown-unescape OR dotted-path components.

No questions rewritten. No SYSTEM-H. No retrieval. Split 40/60 membership unchanged. V1 holdout.json not opened.

## Per-ID

| ID | kind | what changed |
|---|---|---|
| NATQ-C-008 | span expansion | E1 expanded upward 29934→29741 so `failure_error_function` (parameter name + default/None semantics) is inside `evidence_text`. Claim/answer unchanged. |
| NATQ-C-022 | span expansion | E1 expanded downward 5599→5699 to include `3. By a file_id from the Files API`. Question/answer/claim unchanged. |
| NATQ-C-032 | span expansion | E2 expanded around `parallel_tool_calls=False,` (27607→27448) to include `from agents import Agent, ModelSettings` and `model_settings=ModelSettings(`. Question/answer unchanged. |
| NATQ-C-069 | span expansion | E1 expanded downward 66670→66987 to include adjacent `top_p: optional number` definition. Claim kept (comparison now anchored). |
| NATQ-C-087 | span expansion | E1 expanded upward 89501→88953 so field `stop_reason` and value `"refusal"` co-occur in `evidence_text`. |
| NATQ-C-131 | span expansion | E1 expanded upward 1295→1031 to include `completion = client.chat.completions.parse(...)`. Claim kept. |
| NATQ-C-167 | span expansion | E1 expanded upward 13567→13247 to include enclosing `ToolResultBlockParam` / `type: "tool_result"` together with content definition. |
| NATQ-C-179 | span expansion | E1 expanded downward 32618→32789 to include TextBlockParam `text`, `type`, `cache_control: optional`. Claim unchanged. |
| NATQ-C-189 | span expansion | E1 expanded downward 29711→29757 to include `mouse_move` in the basic-actions list. |
| NATQ-C-016 | STALE_CRITICAL_STRING_REPAIR | Round-2 packet: removed stale critical_string `role": "system"`. Replaced with `mid-conversation system message` (present in evidence). Kept `top-level \`system\` field` and `cannot be the first entry`. Question and Round-2 answer unchanged. Evidence not expanded. |

All new/expanded spans satisfy `normalized_text[char_start:char_end] == evidence_text` and `sha256(utf-8 evidence_text) == evidence_hash` against snapshot `snap_689e336380a054d8039dc35b2c09cd0a`.

Claim count remains 251 (no claim tightened).
