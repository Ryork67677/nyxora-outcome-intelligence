# Gold review batch 004

**15 candidates · corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · generated 2026-08-21T05:18:49Z**

Nothing in this file is ground truth. Every candidate is `candidate_unverified`. The evidence is quoted verbatim from the frozen corpus and is authoritative for this review — **do not consult live documentation**, which may have changed since the snapshot.

Batch 003 closed with zero genuine multi-hop cases: four were labelled that way and none survived scrutiny. This batch separates `reasoning_type` from `evidence_shape` and puts every multi-hop candidate through a composition check that fails the pair whenever one span already answers the question. Where you think a `genuine_multi_hop` case is really a two-span lookup, say so — that is the judgement this batch most needs.

Provider {'anthropic': 7, 'openai': 8} · reasoning {'configuration_interaction': 5, 'error_behavior': 3, 'exact_lookup': 3, 'lifecycle_compatibility_migration': 1, 'ambiguity_disambiguation': 2, 'genuine_multi_hop': 1} · 10 distinct documents · median span 144 characters.

| id | provider | reasoning type | shape | chars | question |
| --- | --- | --- | --- | --- | --- |
| `01` | anthropic | configuration_interaction | single_span | 209 | What happens when using server tools? |
| `02` | anthropic | configuration_interaction | single_span | 180 | What happens if Claude calls web search and one of your client tool… |
| `03` | anthropic | error_behavior | single_span | 232 | What happens if the most recent assistant message contains `thinkin… |
| `04` | anthropic | error_behavior | single_span | 144 | What happens if generation then reaches the context window limit? |
| `05` | anthropic | error_behavior | single_span | 128 | What happens if Claude attempts more searches than allowed? |
| `06` | anthropic | exact_lookup | single_span | 99 | What is the `timezone` option? |
| `07` | anthropic | lifecycle_compatibility_migration | single_span | 156 | What happens if you need a hard ceiling on thinking costs? |
| `08` | openai | ambiguity_disambiguation | multi_span | 53 | In a `ContentDeltaEvent`, what does the `type` field contain, and h… |
| `09` | openai | ambiguity_disambiguation | multi_span | 206 | In a `FunctionToolCallArgumentsDeltaEvent`, what does the `parsed_a… |
| `10` | openai | configuration_interaction | single_span | 142 | What happens if you pass a different `RealtimeModel`? |
| `11` | openai | configuration_interaction | single_span | 185 | What happens if a tool requires approval? |
| `12` | openai | configuration_interaction | single_span | 330 | What happens if you are manually continuing from `result.to_input_l… |
| `13` | openai | exact_lookup | single_span | 121 | What is the `input_type` option? |
| `14` | openai | exact_lookup | single_span | 98 | What is the `input_filter` option? |
| `15` | openai | genuine_multi_hop | multi_document | 263 | If I set `needs_approval` to `True`, what happens? |

---

## GOLD-B004-01

- **provider**: anthropic
- **document**: Stop reasons and fallback
- **section**: Best practices for handling stop reasons › Implement retry logic for pause\_turn
- **reasoning type**: `configuration_interaction` · **evidence shape**: `single_span` · **requires all evidence**: False
- **confidence**: medium · **precheck holdout-ready**: True

**Q.** What happens when using server tools?

**A.** The API may return `pause_turn` if the server-side sampling loop reaches its iteration limit (default 10).

**Atomic claims**

  1. When using [server tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/server-tools), the API may return `pause_turn` if the server-side sampling loop reaches its iteration limit (default 10).

**Exact evidence**

`E1` · `ver_4d14aec24504f4b8f6f28938b84587dc` 80272–80481 (209 chars) · Best practices for handling stop reasons › Implement retry logic for pause\_turn

```
When using [server tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/server-tools), the API may return `pause_turn` if the server-side sampling loop reaches its iteration limit (default 10).
```
**critical strings**: `pause_turn`

**Claim → evidence**

  1. When using [server tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/server-tools), the API may return `pause_turn` if the server-side sampling loop reaches its iteration limit (default 10). → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…}&.text

    if [:max_tokens, :model_context_window_exceeded].include?(response.stop_reason)
      note = if response.stop_reason == :max_tokens
        "[Response truncated due to max_tokens limit]"
      else
        "[Response truncated due to context window limit]"
      end
      return "#{text}\n\n#{note}"
    end
    text
  end
  ```
</CodeGroup>

### Implement retry logic for pause\_turn
  ⟦EVIDENCE⟧
Handle this by continuing the conversation:

<CodeGroup exclude="shell">
  ```python Python
  def handle_server_tool_conversation(client, user_query, tools, max_continuations=5):
      """
      Handle server tool conversations that may require multiple continuations.

      The server runs a sampling loop when executing server tools. If the loop
      reaches its iteration limit, the API returns…
```

</details>

---

## GOLD-B004-02

- **provider**: anthropic
- **document**: Web search tool
- **section**: Response › `pause_turn` stop reason
- **reasoning type**: `configuration_interaction` · **evidence shape**: `single_span` · **requires all evidence**: False
- **confidence**: medium · **precheck holdout-ready**: True

**Q.** What happens if Claude calls web search and one of your client tools in the same group of parallel tool calls?

**A.** The API returns `stop_reason: "tool_use"` instead and does not run the search yet.

**Atomic claims**

  1. If Claude calls web search and one of your client tools in the same group of parallel tool calls, the API returns `stop_reason: "tool_use"` instead and does not run the search yet.

**Exact evidence**

`E1` · `ver_53da2f78e855c75ec755089c13d44c28` 22695–22875 (180 chars) · Response › `pause_turn` stop reason

```
If Claude calls web search and one of your client tools in the same group of parallel tool calls, the API returns `stop_reason: "tool_use"` instead and does not run the search yet.
```
**critical strings**: `stop_reason`, `tool_use`

**Claim → evidence**

  1. If Claude calls web search and one of your client tools in the same group of parallel tool calls, the API returns `stop_reason: "tool_use"` instead and does not run the search yet. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…ceeded
* `query_too_long`: Query exceeds maximum length
* `request_too_large`: The search request is too large, typically because of a long domain filter list
* `unavailable`: An internal error occurred

### `pause_turn` stop reason

The API can pause a long-running search turn and return `stop_reason: "pause_turn"`. To continue, send the paused assistant message back unchanged in a new request.
  ⟦EVIDENCE⟧
To continue, return the client tool results, and the API runs the search in the next request. See [Mixing server tools and client tools in one turn](https://platform.claude.com/docs/en/agents-and-tools/tool-use/server-tools#mixing-server-tools-and-client-tools-in-one-turn).

For the server-side loop and `pause_turn` handling, see [The server-side loop and pause\_turn](https://platform.claude.com/…
```

</details>

---

## GOLD-B004-03

- **provider**: anthropic
- **document**: Claude API errors
- **section**: Common validation errors › Thinking blocks cannot be modified
- **reasoning type**: `error_behavior` · **evidence shape**: `single_span` · **requires all evidence**: False
- **confidence**: medium · **precheck holdout-ready**: True

**Q.** What happens if the most recent assistant message contains `thinking` or `redacted_thinking` blocks that were edited, reordered, filtered out, or reconstructed before being sent back to the API?

**A.** The request returns a 400 `invalid_request_error`.

**Atomic claims**

  1. If the most recent assistant message contains `thinking` or `redacted_thinking` blocks that were edited, reordered, filtered out, or reconstructed before being sent back to the API, the request returns a 400 `invalid_request_error`.

**Exact evidence**

`E1` · `ver_0774ca0093ff4a846753577c9a4a39d5` 19838–20070 (232 chars) · Common validation errors › Thinking blocks cannot be modified

```
If the most recent assistant message contains `thinking` or `redacted_thinking` blocks that were edited, reordered, filtered out, or reconstructed before being sent back to the API, the request returns a 400 `invalid_request_error`.
```
**critical strings**: `thinking`, `redacted_thinking`, `invalid_request_error`

**Claim → evidence**

  1. If the most recent assistant message contains `thinking` or `redacted_thinking` blocks that were edited, reordered, filtered out, or reconstructed before being sent back to the API, the request returns a 400 `invalid_request_error`. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…tant message prefill. The conversation must end with a user message."
  }
}
```

Use [structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) on models that support it, system prompt instructions, or [`output_config.format`](https://platform.claude.com/docs/en/build-with-claude/structured-outputs#json-outputs) instead.

### Thinking blocks cannot be modified
  ⟦EVIDENCE⟧
The error message starts with the position of the offending block (for example, `messages.1.content.0`) and contains:

```text wrap
`thinking` or `redacted_thinking` blocks in the latest assistant message cannot be modified. These blocks must remain as they were in the original response.
```

With tool use, every `thinking` and `redacted_thinking` block from the assistant turn must be passed back…
```

</details>

---

## GOLD-B004-04

- **provider**: anthropic
- **document**: Thinking
- **section**: Thinking and the context window
- **reasoning type**: `error_behavior` · **evidence shape**: `single_span` · **requires all evidence**: False
- **confidence**: medium · **precheck holdout-ready**: True

**Q.** What happens if generation then reaches the context window limit?

**A.** It stops with `stop_reason: "model_context_window_exceeded"` instead of returning an error.

**Atomic claims**

  1. If generation then reaches the context window limit, it stops with `stop_reason: "model_context_window_exceeded"` instead of returning an error.

**Exact evidence**

`E1` · `ver_012b734775e7edb2649d3a9ddfd93070` 48081–48225 (144 chars) · Thinking and the context window

```
If generation then reaches the context window limit, it stops with `stop_reason: "model_context_window_exceeded"` instead of returning an error.
```
**critical strings**: `stop_reason`, `model_context_window_exceeded`

**Claim → evidence**

  1. If generation then reaches the context window limit, it stops with `stop_reason: "model_context_window_exceeded"` instead of returning an error. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…rompt-caching#1-hour-cache-duration) to maintain cache hits across longer thinking sessions and multistep workflows.
</Tip>

## Thinking and the context window

`max_tokens`, which includes all thinking Claude generates in the current turn, is enforced as a strict limit. On Claude 4.5 models and newer, if input tokens plus `max_tokens` exceeds the context window size, the API accepts the request.
  ⟦EVIDENCE⟧
On earlier models, the API returns a validation error instead. See [Handling stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons).

How thinking counts against the window depends on when it was generated:

* **Current-turn thinking** always counts toward `max_tokens`, is billed as output tokens, and occupies context window space for the turn that generated it…
```

</details>

---

## GOLD-B004-05

- **provider**: anthropic
- **document**: Web search tool
- **section**: Tool definition › Max uses
- **reasoning type**: `error_behavior` · **evidence shape**: `single_span` · **requires all evidence**: False
- **confidence**: medium · **precheck holdout-ready**: True

**Q.** What happens if Claude attempts more searches than allowed?

**A.** The `web_search_tool_result` is an error with the `max_uses_exceeded` error code.

**Atomic claims**

  1. If Claude attempts more searches than allowed, the `web_search_tool_result` is an error with the `max_uses_exceeded` error code.

**Exact evidence**

`E1` · `ver_53da2f78e855c75ec755089c13d44c28` 15475–15603 (128 chars) · Tool definition › Max uses

```
If Claude attempts more searches than allowed, the `web_search_tool_result` is an error with the `max_uses_exceeded` error code.
```
**critical strings**: `web_search_tool_result`, `max_uses_exceeded`

**Claim → evidence**

  1. If Claude attempts more searches than allowed, the `web_search_tool_result` is an error with the `max_uses_exceeded` error code. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…rect"]`. See [Server tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/server-tools#zdr-and-allowed-callers) for how to configure it. `web_search_20260318` and later also accept [`response_inclusion`](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool#response-inclusion).

### Max uses

The `max_uses` parameter limits the number of searches performed.
  ⟦EVIDENCE⟧
Simple factual queries typically use 1–3 searches; comparative or multientity research can use 10 or more. For guidance on choosing a value, see [Server tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/server-tools).

### Domain filtering

Provide `allowed_domains` or `blocked_domains`, not both. If a request includes both, the API returns a 400 error. Entries are bare domain…
```

</details>

---

## GOLD-B004-06

- **provider**: anthropic
- **document**: Web search tool
- **section**: Tool definition › Localization
- **reasoning type**: `exact_lookup` · **evidence shape**: `single_span` · **requires all evidence**: False
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What is the `timezone` option?

**A.** The [IANA timezone ID](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

**Atomic claims**

  1. `timezone`: The [IANA timezone ID](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

**Exact evidence**

`E1` · `ver_53da2f78e855c75ec755089c13d44c28` 16744–16843 (99 chars) · Tool definition › Localization

```
* `timezone`: The [IANA timezone ID](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
```
**critical strings**: `timezone`, `The [IANA timezone ID](https://en.wikipedia.org/wiki/List_of`

**Claim → evidence**

  1. `timezone`: The [IANA timezone ID](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…ize search results based on a user's location. Provide at least one of `city`, `region`, `country`, or `timezone`.

* `type`: The type of location (must be `approximate`)
* `city`: The city name
* `region`: The region or state
* `country`: The two-letter [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country code. The API rejects unsupported country codes with a 400 error.
  ⟦EVIDENCE⟧
### Response inclusion

<Note>
  Requires `web_search_20260318` or later.
</Note>

The `response_inclusion` parameter controls how search result blocks appear in the API response when the result was consumed by a completed [code execution](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool) call in the same turn. Set `"response_inclusion": "excluded"` to drop those…
```

</details>

---

## GOLD-B004-07

- **provider**: anthropic
- **document**: Prompting best practices
- **section**: Thinking and reasoning › Overthinking and excessive thoroughness
- **reasoning type**: `lifecycle_compatibility_migration` · **evidence shape**: `single_span` · **requires all evidence**: False
- **confidence**: medium · **precheck holdout-ready**: True

**Q.** What happens if you need a hard ceiling on thinking costs?

**A.** Extended thinking with a `budget_tokens` cap is still functional on Opus 4.6 and Sonnet 4.6 but is deprecated.

**Atomic claims**

  1. If you need a hard ceiling on thinking costs, extended thinking with a `budget_tokens` cap is still functional on Opus 4.6 and Sonnet 4.6 but is deprecated.

**Exact evidence**

`E1` · `ver_0a5b292d4854b92db0a9e025b4949123` 27270–27426 (156 chars) · Thinking and reasoning › Overthinking and excessive thoroughness

```
If you need a hard ceiling on thinking costs, extended thinking with a `budget_tokens` cap is still functional on Opus 4.6 and Sonnet 4.6 but is deprecated.
```
**critical strings**: `budget_tokens`

**Claim → evidence**

  1. If you need a hard ceiling on thinking costs, extended thinking with a `budget_tokens` cap is still functional on Opus 4.6 and Sonnet 4.6 but is deprecated. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…g to reduce overall thinking and token usage.

```text Sample prompt wrap
When you're deciding how to approach a problem, choose an approach and commit to it.
Avoid revisiting decisions unless you encounter new information that directly
contradicts your reasoning. If you're weighing two approaches, pick one and see it
through. You can always course-correct later if the chosen approach fails.
```
  ⟦EVIDENCE⟧
On Claude 4.7 and later models, setting `budget_tokens` returns a 400 error. Prefer lowering the [effort](https://platform.claude.com/docs/en/build-with-claude/effort) setting or using `max_tokens` as a hard limit with [adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/thinking).

### Leverage thinking & interleaved thinking capabilities

Claude's latest models offer thinki…
```

</details>

---

## GOLD-B004-08

- **provider**: openai
- **document**: Structured Outputs Parsing Helpers
- **section**: Streaming Helpers › Chat Completions API › Chat Completions Events › ContentDeltaEvent
- **reasoning type**: `ambiguity_disambiguation` · **evidence shape**: `multi_span` · **requires all evidence**: True
- **confidence**: medium · **precheck holdout-ready**: True

**Q.** In a `ContentDeltaEvent`, what does the `type` field contain, and how does that differ from `ContentDoneEvent`?

**A.** In `ContentDeltaEvent`, `type` is: `"content.delta"`. In `ContentDoneEvent`, `type` is: `"content.done"`.

**Atomic claims**

  1. In `ContentDeltaEvent`, `type` is: `"content.delta"`.
  2. In `ContentDoneEvent`, `type` is: `"content.done"`.

**Ambiguity**

- **term**: `type`
  - in `ContentDeltaEvent`: `"content.delta"`
  - in `ContentDoneEvent`: `"content.done"`
  - in `FunctionToolCallArgumentsDeltaEvent`: `"tool_calls.function.arguments.delta"`
  - in `FunctionToolCallArgumentsDoneEvent`: `"tool_calls.function.arguments.done"`
  - in `LogprobsContentDeltaEvent`: `"logprobs.content.delta"`
  - in `LogprobsContentDoneEvent`: `"logprobs.content.done"`
  - in `LogprobsRefusalDeltaEvent`: `"logprobs.refusal.delta"`
  - in `LogprobsRefusalDoneEvent`: `"logprobs.refusal.done"`
  - in `RefusalDeltaEvent`: `"refusal.delta"`
  - in `RefusalDoneEvent`: `"refusal.done"`
- **scope needed to answer**: Which parent type the `type` field belongs to. The corpus defines it under ContentDeltaEvent, ContentDoneEvent, FunctionToolCallArgumentsDeltaEvent, FunctionToolCallArgumentsDoneEvent, LogprobsContentDeltaEvent, LogprobsContentDoneEvent, LogprobsRefusalDeltaEvent, LogprobsRefusalDoneEvent, RefusalDeltaEvent, RefusalDoneEvent with different meanings, so the answer is undetermined until the scope is named.

**Exact evidence**

`E1` · `ver_57e26a49b0a3714f3e90376d014d7f52` 5814–5841 (27 chars) (span 1 of 2) · Streaming Helpers › Chat Completions API › Chat Completions Events › ContentDeltaEvent

```
- `type`: `"content.delta"`
```
**critical strings**: `type`, `` `"content.delta"` ``

`E2` · `ver_57e26a49b0a3714f3e90376d014d7f52` 6134–6160 (26 chars) (span 2 of 2) · Streaming Helpers › Chat Completions API › Chat Completions Events › ContentDoneEvent

```
- `type`: `"content.done"`
```
**critical strings**: `type`, `` `"content.done"` ``

**Claim → evidence**

  1. In `ContentDeltaEvent`, `type` is: `"content.delta"`. → `E1`
  2. In `ContentDoneEvent`, `type` is: `"content.done"`. → `E2`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…ent aspects of the stream separately.

Below is a list of the different event types you may encounter:

#### ChunkEvent

Emitted for every chunk received from the API.

- `type`: `"chunk"`
- `chunk`: The raw `ChatCompletionChunk` object received from the API
- `snapshot`: The current accumulated state of the chat completion

#### ContentDeltaEvent

Emitted for every chunk containing new content.
  ⟦EVIDENCE⟧
- `content`: The full generated content
- `parsed`: The fully parsed content (if applicable)

#### RefusalDeltaEvent

Emitted when a chunk contains part of a content refusal.

- `type`: `"refusal.delta"`
- `delta`: The new refusal content string received in this chunk
- `snapshot`: The accumulated refusal content string so far

#### RefusalDoneEvent

Emitted when the refusal content is complete.…
```

</details>

---

## GOLD-B004-09

- **provider**: openai
- **document**: Structured Outputs Parsing Helpers
- **section**: Streaming Helpers › Chat Completions API › Chat Completions Events › FunctionToolCallArgumentsDeltaEvent
- **reasoning type**: `ambiguity_disambiguation` · **evidence shape**: `multi_span` · **requires all evidence**: True
- **confidence**: medium · **precheck holdout-ready**: True

**Q.** In a `FunctionToolCallArgumentsDeltaEvent`, what does the `parsed_arguments` field contain, and how does that differ from `FunctionToolCallArgumentsDoneEvent`?

**A.** In `FunctionToolCallArgumentsDeltaEvent`, `parsed_arguments` is: The partially parsed arguments object. In `FunctionToolCallArgumentsDoneEvent`, `parsed_arguments` is: The fully parsed arguments object. If you used `openai.pydantic_function_tool()` this will be an instance of the given model.

**Atomic claims**

  1. In `FunctionToolCallArgumentsDeltaEvent`, `parsed_arguments` is: The partially parsed arguments object.
  2. In `FunctionToolCallArgumentsDoneEvent`, `parsed_arguments` is: The fully parsed arguments object. If you used `openai.pydantic_function_tool()` this will be an instance of the given model.

**Ambiguity**

- **term**: `parsed_arguments`
  - in `FunctionToolCallArgumentsDeltaEvent`: The partially parsed arguments object
  - in `FunctionToolCallArgumentsDoneEvent`: The fully parsed arguments object. If you used `openai.pydantic_function_tool()` this will be an instance of the given model.
- **scope needed to answer**: Which parent type the `parsed_arguments` field belongs to. The corpus defines it under FunctionToolCallArgumentsDeltaEvent, FunctionToolCallArgumentsDoneEvent with different meanings, so the answer is undetermined until the scope is named.

**Exact evidence**

`E1` · `ver_57e26a49b0a3714f3e90376d014d7f52` 6938–6997 (59 chars) (span 1 of 2) · Streaming Helpers › Chat Completions API › Chat Completions Events › FunctionToolCallArgumentsDeltaEvent

```
- `parsed_arguments`: The partially parsed arguments object
```
**critical strings**: `parsed_arguments`, `The partially parsed arguments object`

`E2` · `ver_57e26a49b0a3714f3e90376d014d7f52` 7362–7509 (147 chars) (span 2 of 2) · Streaming Helpers › Chat Completions API › Chat Completions Events › FunctionToolCallArgumentsDoneEvent

```
- `parsed_arguments`: The fully parsed arguments object. If you used `openai.pydantic_function_tool()` this will be an instance of the given model.
```
**critical strings**: `parsed_arguments`, `` The fully parsed arguments object. If you used `openai.pydan ``

**Claim → evidence**

  1. In `FunctionToolCallArgumentsDeltaEvent`, `parsed_arguments` is: The partially parsed arguments object. → `E1`
  2. In `FunctionToolCallArgumentsDoneEvent`, `parsed_arguments` is: The fully parsed arguments object. If you used `openai.pydantic_function_tool()` this will be an instance of the given model. → `E2`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…content is complete.

- `type`: `"refusal.done"`
- `refusal`: The full refusal content

#### FunctionToolCallArgumentsDeltaEvent

Emitted when a chunk contains part of a function tool call's arguments.

- `type`: `"tool_calls.function.arguments.delta"`
- `name`: The name of the function being called
- `index`: The index of the tool call
- `arguments`: The accumulated raw JSON string of arguments
  ⟦EVIDENCE⟧
#### LogprobsContentDeltaEvent

Emitted when a chunk contains new content [log probabilities](https://cookbook.openai.com/examples/using_logprobs).

- `type`: `"logprobs.content.delta"`
- `content`: A list of the new log probabilities received in this chunk
- `snapshot`: A list of the accumulated log probabilities so far

#### LogprobsContentDoneEvent

Emitted when all content [log probabilities…
```

</details>

---

## GOLD-B004-10

- **provider**: openai
- **document**: Realtime agents guide
- **section**: Realtime agents guide › Session lifecycle
- **reasoning type**: `configuration_interaction` · **evidence shape**: `single_span` · **requires all evidence**: False
- **confidence**: medium · **precheck holdout-ready**: True

**Q.** What happens if you pass a different `RealtimeModel`?

**A.** The same session lifecycle and agent features still apply, while the connection mechanics can change.

**Atomic claims**

  1. If you pass a different `RealtimeModel`, the same session lifecycle and agent features still apply, while the connection mechanics can change.

**Exact evidence**

`E1` · `ver_14a2187cf2216b9d56c213b520a28479` 1979–2121 (142 chars) · Realtime agents guide › Session lifecycle

```
If you pass a different `RealtimeModel`, the same session lifecycle and agent features still apply, while the connection mechanics can change.
```
**critical strings**: `RealtimeModel`

**Claim → evidence**

  1. If you pass a different `RealtimeModel`, the same session lifecycle and agent features still apply, while the connection mechanics can change. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…ext-only runs, `runner.run()` does not produce a final result immediately. It returns a live session object that keeps local history, background tool execution, guardrail state, and the active agent configuration in sync with the transport layer.

By default, `RealtimeRunner` uses `OpenAIRealtimeWebSocketModel`, so the default Python path is a server-side WebSocket connection to the Realtime API.
  ⟦EVIDENCE⟧
When the Realtime API server closes the default WebSocket connection normally, the model transport emits a `disconnected` [`RealtimeModelConnectionStatusEvent`][agents.realtime.model_events.RealtimeModelConnectionStatusEvent] followed by a [`RealtimeModelEndOfStreamEvent`][agents.realtime.model_events.RealtimeModelEndOfStreamEvent]. `RealtimeSession` forwards both inside `raw_model_event`, drain…
```

</details>

---

## GOLD-B004-11

- **provider**: openai
- **document**: Streaming
- **section**: Streaming › Streaming and approvals
- **reasoning type**: `configuration_interaction` · **evidence shape**: `single_span` · **requires all evidence**: False
- **confidence**: medium · **precheck holdout-ready**: True

**Q.** What happens if a tool requires approval?

**A.** `result.stream_events()` finishes and pending approvals are exposed in `RunResultStreaming.interruptions`.

**Atomic claims**

  1. If a tool requires approval, `result.stream_events()` finishes and pending approvals are exposed in [`RunResultStreaming.interruptions`][agents.result.RunResultStreaming.interruptions].

**Exact evidence**

`E1` · `ver_12004469f7a5592cd1e6cab936117fce` 2472–2657 (185 chars) · Streaming › Streaming and approvals

```
If a tool requires approval, `result.stream_events()` finishes and pending approvals are exposed in [`RunResultStreaming.interruptions`][agents.result.RunResultStreaming.interruptions].
```
**critical strings**: `stream_events`, `RunResultStreaming.interruptions`

**Claim → evidence**

  1. If a tool requires approval, `result.stream_events()` finishes and pending approvals are exposed in [`RunResultStreaming.interruptions`][agents.result.RunResultStreaming.interruptions]. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…streamed(agent, input="Please tell me 5 jokes.")
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
```

## Streaming and approvals

Streaming is compatible with runs that pause for tool approval.
  ⟦EVIDENCE⟧
Convert the result to a [`RunState`][agents.run_state.RunState] with `result.to_state()`, approve or reject the interruption, and then resume with `Runner.run_streamed(...)`.

```python
result = Runner.run_streamed(agent, "Delete temporary files if they are no longer needed.")
async for _event in result.stream_events():
    pass

if result.interruptions:
    state = result.to_state()
    for inte…
```

</details>

---

## GOLD-B004-12

- **provider**: openai
- **document**: Streaming
- **section**: Streaming › Cancel streaming after the current turn
- **reasoning type**: `configuration_interaction` · **evidence shape**: `single_span` · **requires all evidence**: False
- **confidence**: medium · **precheck holdout-ready**: True

**Q.** What happens if you are manually continuing from `result.to_input_list(mode="normalized")`, and `cancel(mode="after_turn")` stops after a tool turn?

**A.** Rerun `result.last_agent` with that normalized input to continue the unfinished existing user turn instead of appending a fresh user turn right away.

**Atomic claims**

  1. If you are manually continuing from [`result.to_input_list(mode="normalized")`][agents.result.RunResultBase.to_input_list], and `cancel(mode="after_turn")` stops after a tool turn, rerun `result.last_agent` with that normalized input to continue the unfinished existing user turn instead of appending a fresh user turn right away.

**Exact evidence**

`E1` · `ver_12004469f7a5592cd1e6cab936117fce` 3845–4175 (330 chars) · Streaming › Cancel streaming after the current turn

```
If you are manually continuing from [`result.to_input_list(mode="normalized")`][agents.result.RunResultBase.to_input_list], and `cancel(mode="after_turn")` stops after a tool turn, rerun `result.last_agent` with that normalized input to continue the unfinished existing user turn instead of appending a fresh user turn right away.
```
**critical strings**: `to_input_list`, `after_turn`, `result.last_agent`

**Claim → evidence**

  1. If you are manually continuing from [`result.to_input_list(mode="normalized")`][agents.result.RunResultBase.to_input_list], and `cancel(mode="after_turn")` stops after a tool turn, rerun `result.last_agent` with that normalized input to continue the unfinished existing user turn instead of appending a fresh user turn right away. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…ancel()`][agents.result.RunResultStreaming.cancel]. By default this stops the run immediately. To let the current turn finish cleanly before stopping, call `result.cancel(mode="after_turn")` instead.

A streamed run is not complete until `result.stream_events()` finishes. The SDK may still be persisting session items, finalizing approval state, or compacting history after the last visible token.
  ⟦EVIDENCE⟧
-   If new user input arrives before that unfinished run resumes, convert the drained result with `result.to_state()`, call [`state.add_input(...)`][agents.run_state.RunState.add_input], and resume from the state. The runner admits the staged input immediately before the next model call; see [Add input before resuming](results.md#add-input-before-resuming).
-   If a streamed run stopped for tool…
```

</details>

---

## GOLD-B004-13

- **provider**: openai
- **document**: Handoffs
- **section**: (1)! › Customizing handoffs via the `handoff()` function
- **reasoning type**: `exact_lookup` · **evidence shape**: `single_span` · **requires all evidence**: False
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What is the `input_type` option?

**A.** The schema for the handoff tool-call arguments. When set, the parsed payload is passed to `on_handoff`.

**Atomic claims**

  1. `input_type`: The schema for the handoff tool-call arguments. When set, the parsed payload is passed to `on_handoff`.

**Exact evidence**

`E1` · `ver_1c77f33b04ffffa285ea7e61c2a89653` 2332–2453 (121 chars) · (1)! › Customizing handoffs via the `handoff()` function

```
-   `input_type`: The schema for the handoff tool-call arguments. When set, the parsed payload is passed to `on_handoff`.
```
**critical strings**: `input_type`, `The schema for the handoff tool-call arguments. When set, th`

**Claim → evidence**

  1. `input_type`: The schema for the handoff tool-call arguments. When set, the parsed payload is passed to `on_handoff`. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…ult tool description from `Handoff.default_tool_description()`
-   `on_handoff`: A callback function executed when the handoff is invoked. This is useful for things like kicking off some data fetching as soon as you know a handoff is being invoked. This function receives the agent context, and can optionally also receive LLM generated input. The input data is controlled by the `input_type` param.
  ⟦EVIDENCE⟧
-   `input_filter`: This lets you filter the input received by the next agent. See below for more.
-   `is_enabled`: Whether the handoff is enabled. This can be a boolean or a function that returns a boolean, allowing you to dynamically enable or disable the handoff at runtime.
-   `nest_handoff_history`: Optional per-handoff override for the RunConfig-level `nest_handoff_history` setting. If `No…
```

</details>

---

## GOLD-B004-14

- **provider**: openai
- **document**: Handoffs
- **section**: (1)! › Customizing handoffs via the `handoff()` function
- **reasoning type**: `exact_lookup` · **evidence shape**: `single_span` · **requires all evidence**: False
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What is the `input_filter` option?

**A.** This lets you filter the input received by the next agent.

**Atomic claims**

  1. `input_filter`: This lets you filter the input received by the next agent.

**Exact evidence**

`E1` · `ver_1c77f33b04ffffa285ea7e61c2a89653` 2454–2552 (98 chars) · (1)! › Customizing handoffs via the `handoff()` function

```
-   `input_filter`: This lets you filter the input received by the next agent. See below for more.
```
**critical strings**: `input_filter`, `This lets you filter the input received by the next agent`

**Claim → evidence**

  1. `input_filter`: This lets you filter the input received by the next agent. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…doff is invoked. This is useful for things like kicking off some data fetching as soon as you know a handoff is being invoked. This function receives the agent context, and can optionally also receive LLM generated input. The input data is controlled by the `input_type` param.
-   `input_type`: The schema for the handoff tool-call arguments. When set, the parsed payload is passed to `on_handoff`.
  ⟦EVIDENCE⟧
-   `is_enabled`: Whether the handoff is enabled. This can be a boolean or a function that returns a boolean, allowing you to dynamically enable or disable the handoff at runtime.
-   `nest_handoff_history`: Optional per-handoff override for the RunConfig-level `nest_handoff_history` setting. If `None`, the value defined in the active run configuration is used instead.

The [`handoff()`][agents.h…
```

</details>

---

## GOLD-B004-15

- **provider**: openai
- **document**: Human-in-the-loop
- **section**: Human-in-the-loop › Marking tools that need approval
- **reasoning type**: `genuine_multi_hop` · **evidence shape**: `multi_document` · **requires all evidence**: True
- **confidence**: medium · **precheck holdout-ready**: True

**Q.** If I set `needs_approval` to `True`, what happens?

**A.** Set `needs_approval` to `True` to always require approval or provide an async function that decides per call. SDK tool approval interruptions are not supported: any function tool whose `needs_approval` setting is not `False` is rejected before the request is sent.

**Atomic claims**

  1. Set `needs_approval` to `True` to always require approval or provide an async function that decides per call.
  2. SDK tool approval interruptions are not supported: any function tool whose `needs_approval` setting is not `False` is rejected before the request is sent.

**Composition**

- **bridge entity**: `needs_approval`
- **relationship**: span 1 states a requirement or constraint on the bridge entity; span 2 states the behaviour that follows
- **hop 1**: Set `needs_approval` to `True` to always require approval or provide an async function that decides per call.
- **hop 2**: SDK tool approval interruptions are not supported: any function tool whose `needs_approval` setting is not `False` is rejected before the request is sent.
- **composed**: For `needs_approval`: Set `needs_approval` to `True` to always require approval or provide an async function that decides per call. Consequently, SDK tool approval interruptions are not supported: any function tool whose `needs_approval` setting is not `False` is rejected before the request is sent.
- **span 1 alone is not enough**: Span 1 establishes the condition on needs_approval, but does not state needs_approval.
- **span 2 alone is not enough**: Span 2 states what follows, but does not establish that it applies to needs_approval.
- **composition check**: `PASS` · documents 2 · sections 2

**Exact evidence**

`E1` · `ver_ae3bfcc42c733c5051abda30f0f6db07` 1327–1436 (109 chars) (span 1 of 2) · Human-in-the-loop › Marking tools that need approval

```
Set `needs_approval` to `True` to always require approval or provide an async function that decides per call.
```
**critical strings**: `needs_approval`, `True`

`E2` · `ver_ae909bf8b4bbbe1d1a11119447f7ac94` 16756–16910 (154 chars) (span 2 of 2) · Models › OpenAI models › Hosted multi-agent (experimental) › Local function tools

```
SDK tool approval interruptions are not supported: any function tool whose `needs_approval` setting is not `False` is rejected before the request is sent.
```
**critical strings**: `needs_approval`, `False`

**Claim → evidence**

  1. Set `needs_approval` to `True` to always require approval or provide an async function that decides per call. → `E1`
  2. SDK tool approval interruptions are not supported: any function tool whose `needs_approval` setting is not `False` is rejected before the request is sent. → `E2`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…d tools inside the nested agent can later raise their own approvals after the nested run starts. Both are handled through the same outer-run interruption flow.

This page focuses on the manual approval flow via `interruptions`. If your app can decide in code, some tool types also support programmatic approval callbacks so the run can continue without pausing.

## Marking tools that need approval
  ⟦EVIDENCE⟧
…
```

</details>

---
