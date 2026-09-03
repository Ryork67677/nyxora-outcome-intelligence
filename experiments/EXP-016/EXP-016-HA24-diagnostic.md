# EXP-016 HA-24 diagnostic

Written **after** rematerializing the SYSTEM-A pool-100 and CE logits,
and **before** applying variant C clamp or variant D blend.
No C/D scores were computed when this file was first written.

Excerpts below were expanded after the run (still from the same two chunks)
because the original 280-character head of the gold chunk stopped at
`tool_arguments` and omitted the `.tool_input` sentence.

## Query

`In the OpenAI Agents SDK for Python, under what condition can `ToolContext` also expose `.tool_input`?`

Query identifier tokens (frozen matcher): `['.tool_input', 'OpenAI', 'SDK', 'ToolContext', 'tool_input']`

## Gold span

- chunk_id: `chk_300debbdfdd33f994da8367b173f4986666146c1`
- version_id: `ver_fef74b4dda29e84a533c3e83f753effd`
- section_path: `['Context management', 'Local context', 'Advanced: \`ToolContext\`']`
- char: [7021, 7167)
- SYSTEM-A rank: **1** (fused RRF score 0.031778)
- CE logit: **1.299236**
- CE rank (EXP-015 / rematerialized): **18**
- identifier overlap with query: `['.tool_input', 'ToolContext', 'tool_input']`

Gold excerpt (exact-answer sentence, not the whole chunk):

> Use `ToolContext` when you need tool-level metadata during execution. For general context sharing between agents and tools, `RunContextWrapper` remains sufficient. Because `ToolContext` extends `RunContextWrapper`, it can also expose `.tool_input` when a nested `Agent.as_tool()` run supplied structured input.

## Top A passage (SYSTEM-A rank 1)

- chunk_id: `chk_300debbdfdd33f994da8367b173f4986666146c1`
- CE logit: **1.299236**
- same as gold: `True`
- identifier overlap: `['.tool_input', 'ToolContext', 'tool_input']`

Same excerpt as gold (A rank 1 **is** the gold chunk).

## Top C passage (what CE put at rank 1)

- chunk_id: `chk_c24c1a9df2502d944a1be63f49b7fa265f343d11`
- SYSTEM-A rank: 2
- CE logit: **4.036510**
- identifier overlap: `['OpenAI', 'SDK']` (no `ToolContext`, no `tool_input`)
- section: `['Tools']`

> # Tools Tools let agents take actions: things like fetching data, running code, calling external APIs, and even using a computer. The SDK supports five categories: Hosted OpenAI tools; local/runtime execution tools; FunctionTool; agents as tools; experimental Codex tool.

This passage never mentions `ToolContext` or `.tool_input`.

## Why the gold chunk fell to CE rank 18

The gold chunk is SYSTEM-A rank 1 with CE logit 1.2992. Seventeen other
pool-100 candidates received a higher CE logit (top is 4.0365 at A rank 2).
EXP-015 tie-break is CE desc, then A rank, then chunk_id; no other fusion
was applied in EXP-015.

CE scored the general Tools overview 4.0365 vs the exact-answer gold chunk
1.2992 (Δ=2.7373), dropping gold from A rank 1 to CE rank 18.

## Conclusion

**YES.** CE preferred a more general explanation over the exact answer.

The query asks a precise condition (`ToolContext` exposing `.tool_input`).
SYSTEM-A already had that sentence at rank 1. The cross-encoder promoted an
adjacent, generic "what are tools" overview (A rank 2, no `ToolContext`, no
`.tool_input`) to CE rank 1 with a much higher logit, and buried the exact
match at 18. That is the rank-1 destruction EXP-015 recorded for HA-24.
