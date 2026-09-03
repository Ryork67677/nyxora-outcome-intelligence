# NATQ-001 review packet (batch 002)

**Corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · generated 2026-09-02T17:53:30Z (2026-09-02 13:53 EDT)**

**Header instruction for ChatGPT (coordinator):** The quoted evidence below is authoritative. **Do not consult live docs.** The corpus is frozen snapshot `snap_689e336380a054d8039dc35b2c09cd0a`. Judge each candidate against the quoted evidence and the short context_before/after only.

Nothing in this file is frozen gold. Every candidate is `PENDING_CHATGPT_REVIEW`. `proposed_split` is **PROPOSED / NOT_FROZEN** metadata — ChatGPT must see **all 100** candidates; the split is not a secrecy boundary yet. Do not create a NATQ holdout lock.

For each candidate, return verdict `PASS | FAIL | FIX_REQUIRED | UNCERTAIN` against the evidence as written. Do not rewrite questions into corpus language unless FIX_REQUIRED.

ID prefix `NATQ-C-`. This is NATQ-001 question-first authoring + evidence-second verification, not gold150-v1 and not V2-DEVSET-001.

---

**This batch:** 50 candidates (`NATQ-C-121` … `NATQ-C-227`). Complements the other batch; together they are the full 100.
## NATQ-C-121

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Models overview
- **version_id**: `ver_819d4aa94d02100b3608627cf2443d58`
- **url**: https://platform.claude.com/docs/en/about-claude/models/overview
- **section**: Choosing a model › Latest models comparison
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> 128k vs 200k vs 1m context, which claude model is which

**Answer**: In the latest-models comparison, context windows are 1M tokens for Claude Fable 5, Claude Opus 5, and Claude Sonnet 5, and 200k tokens for Claude Haiku 4.5. 128k tokens is max output for Fable/Opus/Sonnet 5 (Haiku 4.5 max output is 64k), not a context-window size.

**Atomic claims**:
  - Claude Fable 5, Claude Opus 5, and Claude Sonnet 5 have a 1M-token context window.
  - Claude Haiku 4.5 has a 200k-token context window.
  - 128k tokens is the max output for Fable 5, Opus 5, and Sonnet 5, not their context window.
  - Claude Haiku 4.5 max output is 64k tokens.

**Critical strings**: `1M tokens`, `200k tokens`, `128k tokens`, `64k tokens`, `Context window`, `Max output`

### Evidence E1 (verbatim, authoritative)

`ver_819d4aa94d02100b3608627cf2443d58` chars 9748–11112 · hash `908e5819366168aecf0976742585b046e15ac1ff1723abef64f2d79d5505e6bb`

```
| **Context window**                                                                                                            | <Tooltip tooltipContent="~555k words \ ~2.5M unicode characters. Claude Fable 5 uses the tokenizer introduced with Claude Opus 4.7; compared to models before Claude Opus 4.7, the same text produces roughly 30% more tokens. The exact increase depends on the content.">1M tokens</Tooltip> | <Tooltip tooltipContent="~555k words \ ~2.5M unicode characters">1M tokens</Tooltip> | <Tooltip tooltipContent="~555k words \ ~2.5M unicode characters">1M tokens</Tooltip> | <Tooltip tooltipContent="~150k words \ ~680k unicode characters">200k tokens</Tooltip> |
| **Max output**                                                                                                                | 128k tokens                                                                                                                                                                                                                                                                                    | 128k tokens                                                                          | 128k tokens                                                                          | 64k tokens                                                                             |
```

<details><summary>Context before (short)</summary>

```
                                        | Yes                                                                                  | No                                                                                     |
| **Comparative latency**                                                                                                       | Slower                                              …
```

</details>

<details><summary>Context after (short)</summary>

```
| **Reliable knowledge cutoff**                                                                                                 | Jan 20262                                                                                                                                                                                                                                                                     …
```

</details>

### Evidence E2 (verbatim, authoritative)

`ver_819d4aa94d02100b3608627cf2443d58` chars 2216–3610 · hash `e1cb91c787b39c4018682a138538eeff259c2cfff082e15c193156f507f99281`

```
### Latest models comparison

| Feature                                                                                                                       | Claude Fable 5                                                                                                                                                                                                                                                                                 | Claude Opus 5                                                                        | Claude Sonnet 5                                                                      | Claude Haiku 4.5                                                                       |
| ----------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
```

---
## NATQ-C-123

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Running agents
- **version_id**: `ver_2c60e99cfd929a738910b893fd6f1a40`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/running_agents.md
- **section**: Running agents › State and conversation management › Conversations/chat threads › Server-managed conversations › 1. Using `conversation_id`
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> responses api previous_response_id — is that the new thread

**Answer**: No. previous_response_id is response chaining (each turn links to the previous response ID). The conversation/thread-style server state is conversation_id from the Conversations API. They are two different server-managed options.

**Atomic claims**:
  - OpenAI provides two server-managed ways to track state across turns.
  - conversation_id reuses a Conversations API conversation ID.
  - previous_response_id is response chaining to the previous response ID, not the conversation/thread object.

**Critical strings**: `conversation_id`, `previous_response_id`, `response chaining`

### Evidence E1 (verbatim, authoritative)

`ver_2c60e99cfd929a738910b893fd6f1a40` chars 22876–23744 · hash `f76f75b20869d84ae2effa0ea663fe5b5c8feb3bd7aaab41924ea45744d6743d`

````
OpenAI provides two ways to track state across turns:

##### 1. Using `conversation_id`

You first create a conversation using the OpenAI Conversations API and then reuse its ID for every subsequent call:

```python
from agents import Agent, Runner
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def main():
    agent = Agent(name="Assistant", instructions="Reply very concisely.")

    # Create a server-managed conversation
    conversation = await client.conversations.create()
    conv_id = conversation.id

    while True:
        user_input = input("You: ")
        result = await Runner.run(agent, user_input, conversation_id=conv_id)
        print(f"Assistant: {result.final_output}")
```

##### 2. Using `previous_response_id`

Another option is **response chaining**, where each turn links explicitly to the response ID from the previous turn.
````

<details><summary>Context before (short)</summary>

````
tate is it in?", session=session)
        print(result.final_output)
        # California
```

Sessions automatically:

-   Retrieves conversation history before each run
-   Stores new messages after each run
-   Maintains separate conversations for different session IDs

See the [Sessions documentation](sessions/index.md) for more details.


#### Server-managed conversations

You can also let th…
````

</details>

<details><summary>Context after (short)</summary>

````


```python
from agents import Agent, Runner

async def main():
    agent = Agent(name="Assistant", instructions="Reply very concisely.")

    previous_response_id = None

    while True:
        user_input = input("You: ")

        # Setting auto_previous_response_id=True enables response chaining automatically
        # for the first turn, even when there's no actual previous response ID yet.
  …
````

</details>

---
## NATQ-C-124

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Vision
- **version_id**: `ver_4f8c7b2939ec104f110004dfe05a342b`
- **url**: https://platform.claude.com/docs/en/build-with-claude/vision
- **section**: Image limits and costs › Request limits
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> how many images can I send in one claude message before it errors

**Answer**: On the API: 100 images per request for models with a 200k-token context window, and 600 per request for all other models. On claude.ai it is 20 per message.

**Atomic claims**:
  - claude.ai allows 20 images per message.
  - The API allows 100 images per request for 200k-context models.
  - The API allows 600 images per request for all other models.

**Critical strings**: `20 per message`, `100 per request`, `600 per request`, `200k-token context window`

### Evidence E1 (verbatim, authoritative)

`ver_4f8c7b2939ec104f110004dfe05a342b` chars 34244–34480 · hash `f0d9fff0c0e6fe963ef71bf1fac52c08bcb36002c2c1b74a0186f54e31595e71`

```
The maximum number of images per message or request is:

* 20 per message on [claude.ai](https://claude.ai/).
* 100 per request on the API, for models with a 200k-token context window.
* 600 per request on the API, for all other models.
```

<details><summary>Context before (short)</summary>

```
Image 1:" },
          {
            type: "image",
            source: {
              type: "base64",
              media_type: "image/png",
              data: image1_data
            }
          },
          { type: "text", text: "Image 2:" },
          {
            type: "image",
            source: {
              type: "base64",
              media_type: "image/png",
              data: im…
```

</details>

<details><summary>Context after (short)</summary>

```


The maximum dimensions per image are 8000x8000 px.

If a single API request contains more than 20 images, a stricter per-image dimension limit applies. On Amazon Bedrock and Google Cloud, document blocks such as PDFs also count toward this threshold. Images exceeding the stricter limit are rejected with an `invalid_request_error` whose message references "many-image requests" and states the curr…
```

</details>

---
## NATQ-C-127

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Context editing
- **version_id**: `ver_1c53b961e1f5da8124a1e7e8eb92c941`
- **url**: https://platform.claude.com/docs/en/build-with-claude/context-editing
- **section**: Server-side strategies › Tool result clearing
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> does claude drop old tool results if I turn on context editing / compaction beta

**Answer**: Yes, if you enable context editing (beta header context-management-2025-06-27) with clear_tool_uses_20250919. The API then automatically clears the oldest tool results past the threshold and replaces them with placeholder text. Server-side compaction is a different, primary strategy; this page is fine-grained clearing.

**Atomic claims**:
  - Context editing is beta and requires the context-management-2025-06-27 header.
  - clear_tool_uses_20250919 clears tool results when context grows past the threshold.
  - The oldest tool results are cleared automatically and replaced with placeholder text.

**Critical strings**: `context-management-2025-06-27`, `clear_tool_uses_20250919`, `clears tool results`, `placeholder text`

### Evidence E1 (verbatim, authoritative)

`ver_1c53b961e1f5da8124a1e7e8eb92c941` chars 3947–4766 · hash `cb46b2283398129eefe8d9de46c3c2b45d1ebcf0529d9435f755c094305e6b6c`

```
Context editing is in beta with support for tool result clearing and thinking block clearing. To enable it, use the beta header `context-management-2025-06-27` in your API requests.

  Share feedback on this feature through the [feedback form](https://forms.gle/YXC2EKGMhjN1c4L88).
</Note>

### Tool result clearing

The `clear_tool_uses_20250919` strategy clears tool results when conversation context grows beyond your configured threshold. This is particularly useful for agentic workflows with heavy tool use. Older tool results (like file contents or search results) are no longer needed once Claude has processed them.

When activated, the API automatically clears the oldest tool results in chronological order. The API replaces each cleared result with placeholder text indicating to Claude that it was removed.
```

<details><summary>Context before (short)</summary>

```
. Each strategy can be configured independently.                                                                                                                                                                                                                                                                          |
| **Client-side** | SDK           | Compaction                                      …
```

</details>

<details><summary>Context after (short)</summary>

```
 By default, only tool results are cleared. You can optionally clear both tool results and tool calls (the tool use parameters) by setting `clear_tool_inputs` to true.

### Thinking block clearing

The `clear_thinking_20251015` strategy manages `thinking` blocks in conversations when extended thinking is enabled. This strategy gives you control over thinking preservation: you can choose to keep mo…
```

</details>

---
## NATQ-C-131

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Structured Outputs Parsing Helpers
- **version_id**: `ver_57e26a49b0a3714f3e90376d014d7f52`
- **url**: https://github.com/openai/openai-python/blob/10ee3f0da2ac6f93345c1204bd7bb1a2faa79ff2/helpers.md
- **section**: Structured Outputs Parsing Helpers › Auto-parsing response content with Pydantic models
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> pydantic with openai parse(), what if the model refuses

**Answer**: Check message.parsed from chat.completions.parse(). If it is missing/falsy, the refusal is on message.refusal (the documented else branch prints message.refusal).

**Atomic claims**:
  - chat.completions.parse() returns a completion whose message may have parsed content or a refusal.
  - If message.parsed is missing, read message.refusal.

**Critical strings**: `message.parsed`, `message.refusal`

### Evidence E1 (verbatim, authoritative)

`ver_57e26a49b0a3714f3e90376d014d7f52` chars 1295–1469 · hash `bf03fe42fce09b9ee45ad22a6d7b297f49d77decfe96020884d72d6a8a595e0e`

```
message = completion.choices[0].message
if message.parsed:
    print(message.parsed.steps)
    print("answer: ", message.parsed.final_answer)
else:
    print(message.refusal)
```

<details><summary>Context before (short)</summary>

````
ions with Python specific types & returns a `ParsedChatCompletion` object, which is a subclass of the standard `ChatCompletion` class.

## Auto-parsing response content with Pydantic models

You can pass a pydantic model to the `.parse()` method and the SDK will automatically convert the model
into a JSON schema, send it to the API and parse the response content back into the given model.

```py
f…
````

</details>

<details><summary>Context after (short)</summary>

````

```

## Auto-parsing function tool calls

The `.parse()` method will also automatically parse `function` tool calls if:

- You use the `openai.pydantic_function_tool()` helper method
- You mark your tool schema with `"strict": True`

For example:

```py
from enum import Enum
from typing import List, Union
from pydantic import BaseModel
import openai

class Table(str, Enum):
    orders = "orders"
…
````

</details>

---
## NATQ-C-132

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Structured outputs
- **version_id**: `ver_0865c9612dfe97d8f30dd870dd12e53e`
- **url**: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- **section**: Compatibility
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic structured outputs — still beta, and do I still fake it with a forced tool

**Answer**: No longer required to be beta: output_format moved to output_config.format and beta headers are no longer required (structured-outputs-2025-11-13 still works during a transition). You do not fake structured outputs with a forced tool; JSON outputs use output_config.format, and strict tool use is a separate strict:true option that can be combined in the same request.

**Atomic claims**:
  - JSON structured outputs use output_config.format.
  - Strict tool use is strict: true on tools, not a fake forced tool.
  - Beta headers are no longer required; structured-outputs-2025-11-13 still works for a transition period.

**Critical strings**: `output_config.format`, `strict: true`, `beta headers are no longer required`, `structured-outputs-2025-11-13`

### Evidence E1 (verbatim, authoritative)

`ver_0865c9612dfe97d8f30dd870dd12e53e` chars 1473–2072 · hash `1efbb4e574c62053ef18095d71751342ad00e1e23685fc40609abb34d248ed46`

```
* **JSON outputs** (`output_config.format`): Get Claude's response in a specific JSON format
* **Strict tool use** (`strict: true`): Guarantee schema validation on tool names and inputs

You can use these features independently or together in the same request.

<Tip>
  **Migrating from beta?** The `output_format` parameter has moved to `output_config.format`, and beta headers are no longer required. The old beta header (`structured-outputs-2025-11-13`) and `output_format` parameter will continue working for a transition period. See the following code examples for the updated API shape.
</Tip>
```

<details><summary>Context before (short)</summary>

```
opus-4-6`, `claude-sonnet-5`, `claude-sonnet-4-6`, `claude-sonnet-4-5-20250929`, `claude-opus-4-5-20251101`, `claude-haiku-4-5-20251001`
- Platforms: Claude API, Claude Platform on AWS, Amazon Bedrock [1], Google Cloud, Microsoft Foundry [2]
1. On Amazon Bedrock, structured outputs are available for Claude Opus 4.6, Claude Sonnet 4.6, Claude Sonnet 4.5, Claude Opus 4.5, and Claude Haiku 4.5.
2. On…
```

</details>

<details><summary>Context after (short)</summary>

```


## Why use structured outputs

Without structured outputs, Claude can generate malformed JSON responses or invalid tool inputs that break your applications. Even with careful prompting, you may encounter:

* Parsing errors from invalid JSON syntax
* Missing required fields
* Inconsistent data types
* Schema violations requiring error handling and retries

Structured outputs guarantee schema-comp…
```

</details>

---
## NATQ-C-134

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Agents
- **version_id**: `ver_35cac5e98c151a17f941a6142d74709f`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/agents.md
- **section**: Agents › Output types
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> agents sdk output_type as a list vs a single object, allowed?

**Answer**: Yes. output_type can be any type wrappable in a Pydantic TypeAdapter, including lists (also dataclasses and TypedDict), not only a single Pydantic object.

**Atomic claims**:
  - output_type is how you ask an agent for a particular output type.
  - Supported types include anything TypeAdapter can wrap: dataclasses, lists, TypedDict, etc.

**Critical strings**: `output_type`, `TypeAdapter`, `lists`

### Evidence E1 (verbatim, authoritative)

`ver_35cac5e98c151a17f941a6142d74709f` chars 6440–6855 · hash `cfa34250dddd7d26d595f5ee4ee4a93e5a82c9d7f0a18e8ddc1edd48d2e9b48d`

```
## Output types

By default, agents produce plain text (i.e. `str`) outputs. If you want the agent to produce a particular type of output, you can use the `output_type` parameter. A common choice is to use [Pydantic](https://docs.pydantic.dev/) objects, but we support any type that can be wrapped in a Pydantic [TypeAdapter](https://docs.pydantic.dev/latest/api/type_adapter/) - dataclasses, lists, TypedDict, etc.
```

<details><summary>Context before (short)</summary>

````
   agent,
    "Say hello",
    context=PromptContext(prompt_id="pmpt_123", poem_style="limerick"),
)
```

## Context

Agents are generic on their `context` type. Context is a dependency-injection tool: it's an object you create and pass to `Runner.run()`, that is passed to every agent, tool, handoff etc, and it serves as a grab bag of dependencies and state for the agent run. You can provide any P…
````

</details>

<details><summary>Context after (short)</summary>

````


```python
from pydantic import BaseModel
from agents import Agent


class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

agent = Agent(
    name="Calendar extractor",
    instructions="Extract calendar events from text",
    output_type=CalendarEvent,
)
```

!!! note

    When you pass an `output_type`, that tells the model to use [structured outputs](https://…
````

</details>

---
## NATQ-C-143

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Realtime agents guide
- **version_id**: `ver_14a2187cf2216b9d56c213b520a28479`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/realtime/guide.md
- **section**: Realtime agents guide › Agent and session configuration
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> realtime transcription model vs conversation model, are those two separate models

**Answer**: Yes, they are separate. The conversation/realtime model is session-level model_name (example: gpt-realtime-2.1). Input transcription is a different setting under audio.input.transcription.model (examples: gpt-4o-mini-transcribe, gpt-live-transcribe, gpt-transcribe).

**Atomic claims**:
  - Realtime model choice is configured at the session level (model_name), not per agent.
  - Input transcription is configured under audio.input.transcription with its own model.
  - Example pairs gpt-realtime-2.1 as the session model with a separate transcription model.

**Critical strings**: `model_name`, `audio.input.transcription`, `gpt-realtime-2.1`, `gpt-live-transcribe`

### Evidence E1 (verbatim, authoritative)

`ver_14a2187cf2216b9d56c213b520a28479` chars 2956–5041 · hash `b12c992b60cf3656b63bed8d054cf92b57b09e8cb727326c5abf5b1414df11b0`

````
Model choice is configured at the session level, not per agent.
-   Structured outputs are not supported.
-   Voice can be configured, but it cannot change after the session has already produced spoken audio.
-   Instructions, function tools, handoffs, hooks, and output guardrails all still work.

`RealtimeSessionModelSettings` supports both a newer nested `audio` config and older flat aliases. Prefer the nested shape for new code, and start with `gpt-realtime-2.1` for new realtime agents:

```python
runner = RealtimeRunner(
    starting_agent=agent,
    config={
        "model_settings": {
            "model_name": "gpt-realtime-2.1",
            "audio": {
                "input": {
                    "format": "pcm16",
                    "transcription": {"model": "gpt-4o-mini-transcribe"},
                    "turn_detection": {"type": "semantic_vad", "interrupt_response": True},
                },
                "output": {"format": "pcm16", "voice": "ash"},
            },
            "tool_choice": "auto",
        }
    },
)
```

Useful session-level settings include:

-   `audio.input.format`, `audio.output.format`
-   `audio.input.transcription`
-   `audio.input.noise_reduction`
-   `audio.input.turn_detection`
-   `audio.output.voice`, `audio.output.speed`
-   `output_modalities`
-   `tool_choice`
-   `prompt`
-   `tracing`

Useful run-level settings on `RealtimeRunner(config=...)` include:

-   `async_tool_calls`
-   `output_guardrails`
-   `guardrails_settings.debounce_text_length`
-   `tool_error_formatter`
-   `tracing_disabled`

See [`RealtimeRunConfig`][agents.realtime.config.RealtimeRunConfig] and [`RealtimeSessionModelSettings`][agents.realtime.config.RealtimeSessionModelSettings] for the full typed surface.

### Input transcription settings

Configure input transcription under `audio.input.transcription`. Use `gpt-live-transcribe` for low-latency incremental transcripts, or use `gpt-transcribe` over WebSocket when transcription should begin after an audio turn is committed or when your application needs detected-language output.
````

<details><summary>Context before (short)</summary>

```
 features still apply, while the connection mechanics can change.

When the Realtime API server closes the default WebSocket connection normally, the model transport emits a `disconnected` [`RealtimeModelConnectionStatusEvent`][agents.realtime.model_events.RealtimeModelConnectionStatusEvent] followed by a [`RealtimeModelEndOfStreamEvent`][agents.realtime.model_events.RealtimeModelEndOfStreamEvent]…
```

</details>

<details><summary>Context after (short)</summary>

````
 The Agents SDK forwards the model-specific GA transcription settings in the nested session configuration:

```python
runner = RealtimeRunner(
    starting_agent=agent,
    config={
        "model_settings": {
            "audio": {
                "input": {
                    "transcription": {
                        "model": "gpt-live-transcribe",
                        "prompt": "A support …
````

</details>

---
## NATQ-C-147

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Beta
- **version_id**: `ver_de7f74230c8f10d30aea5d037a3bd0a5`
- **url**: https://platform.claude.com/docs/en/api/beta
- **section**: Messages › Domain Types › Beta Tool Computer Use 20241022
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic computer use, is display_width_px required

**Answer**: Yes. On BetaToolComputerUse20241022, display_width_px is typed as number and is not marked optional (unlike later fields such as display_number / cache_control, which are optional).

**Atomic claims**:
  - BetaToolComputerUse20241022 includes display_width_px: number.
  - display_width_px is not labeled optional in this schema listing.

**Critical strings**: `display_width_px: number`, `The width of the display in pixels.`

### Evidence E1 (verbatim, authoritative)

`ver_de7f74230c8f10d30aea5d037a3bd0a5` chars 805575–805852 · hash `eb44f05b562af587c76f490a5b4656ec8bb5e081894bc8c2e0d87ed889d6ab7d`

```
### Beta Tool Computer Use 20241022

- `BetaToolComputerUse20241022 object { display_height_px, display_width_px, name, 7 more }`

  - `display_height_px: number`

    The height of the display in pixels.

  - `display_width_px: number`

    The width of the display in pixels.
```

<details><summary>Context before (short)</summary>

```
e, disable_parallel_tool_use }`

  The model will automatically decide whether to use tools.

  - `type: "auto"`

    - `"auto"`

  - `disable_parallel_tool_use: optional boolean`

    Whether to disable parallel tool use.

    Defaults to `false`. If set to `true`, the model will output at most one tool use.

### Beta Tool Choice None

- `BetaToolChoiceNone object { type }`

  The model will not …
```

</details>

<details><summary>Context after (short)</summary>

```


  - `name: "computer"`

    Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks.

    - `"computer"`

  - `type: "computer_20241022"`

    - `"computer_20241022"`

  - `allowed_callers: optional array of "direct" or "code_execution_20250825" or "code_execution_20260120" or "code_execution_20260521"`

    - `"direct"`

    - `"code_execution_20250825"`…
```

</details>

---
## NATQ-C-148

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): either
- **document**: Computer use tool
- **version_id**: `ver_d9ba3ab0d872dd86047c7ed6dc783235`
- **url**: https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool
- **section**: Security considerations
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> computer use safety — is there a required confirmation before click or type

**Answer**: Not a required confirmation before every click or type. Human confirmation is listed as a recommended precaution for meaningful/consent actions. Separately, prompt-injection classifiers on screenshots steer the model to ask for user confirmation before the next action, and that classifier layer can be opted out via support. Tagged genuine_ambiguity: the corpus presents recommended vs classifier-triggered confirmation, not a hard click/type gate.

**Atomic claims**:
  - Asking a human to confirm meaningful real-world or consent tasks is a recommended precaution, not a stated hard requirement for every click or type.
  - Classifiers may steer the model to ask for confirmation when they flag prompt injections in screenshots.
  - The classifier confirmation layer can be opted out by contacting support.

**Critical strings**: `Asking a human to confirm`, `ask for user confirmation before proceeding with the next action`, `opt out`

### Evidence E1 (verbatim, authoritative)

`ver_d9ba3ab0d872dd86047c7ed6dc783235` chars 3124–4360 · hash `9c85043067aed6e1637d4175ec953e66f67a723eac1069f9c406ccd54a8dc62f`

```
4. Asking a human to confirm decisions that might result in meaningful real-world consequences and any tasks requiring affirmative consent, such as accepting cookies, completing financial transactions, or agreeing to terms of service.
</Warning>

In some circumstances, Claude will follow commands found in content even when they conflict with your instructions. For example, instructions on webpages or contained in images might override your instructions or cause Claude to make mistakes. Take precautions to isolate Claude from sensitive data and actions to avoid risks related to prompt injection.

Anthropic has trained the model to resist these prompt injections and has added an extra layer of defense. If you use the computer use tools, classifiers will automatically run on your prompts to flag potential instances of prompt injections. When these classifiers identify potential prompt injections in screenshots, they will automatically steer the model to ask for user confirmation before proceeding with the next action. This extra protection won't be ideal for every use case (for example, use cases without a human in the loop), so if you'd like to opt out and turn it off, [contact support](https://support.claude.com/en/).
```

<details><summary>Context before (short)</summary>

```
h as bash and text editor for more comprehensive automation workflows, computer use specifically refers to the computer use tool's capability to see and control desktop environments.

For model support, see the [Tool reference](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-reference).

## Security considerations

Computer use is a beta feature with unique risks distinct from s…
```

</details>

<details><summary>Context after (short)</summary>

```


These precautions remain important even with the classifier defense layer in place.

Inform end users of relevant risks and obtain their consent prior to enabling computer use in your own products.

<Card title="Computer use reference implementation" icon="computer" href="https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo">
  Get started with the computer use referen…
```

</details>

---
## NATQ-C-150

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Tools
- **version_id**: `ver_cbeb36b7cf9a5e241940a011629b6f1b`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/tools.md
- **section**: Tools › Local runtime tools › ComputerTool and the Responses computer tool
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> agents sdk computer tool vs the responses computer_use_preview tool, same thing?

**Answer**: Not the same thing. ComputerTool is a local harness the SDK maps onto the Responses computer surface. Explicit gpt-5.5 requests send GA `{"type": "computer"}`; the older computer-use-preview model still gets `{"type": "computer_use_preview", ...}`.

**Atomic claims**:
  - ComputerTool is a local harness mapped onto the OpenAI Responses computer surface.
  - gpt-5.5 requests send the GA payload type computer.
  - computer-use-preview requests send type computer_use_preview with environment and display fields.

**Critical strings**: `ComputerTool`, `{"type": "computer"}`, `computer_use_preview`, `local harness`

### Evidence E1 (verbatim, authoritative)

`ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 15918–16568 · hash `0cc647fdcadecec1e06a10621db6d0f196cbd02c30e6e6b3c6d61c3fe69bc257`

```
### ComputerTool and the Responses computer tool

`ComputerTool` is still a local harness: you provide a [`Computer`][agents.computer.Computer] or [`AsyncComputer`][agents.computer.AsyncComputer] implementation, and the SDK maps that harness onto the OpenAI Responses API computer surface.

For explicit [`gpt-5.5`](https://developers.openai.com/api/docs/models/gpt-5.5) requests, the SDK sends the GA built-in tool payload `{"type": "computer"}`. For requests to the older `computer-use-preview` model, the SDK continues to send the preview payload `{"type": "computer_use_preview", "environment": ..., "display_width": ..., "display_height": ...}`.
```

<details><summary>Context before (short)</summary>

```
I/browser automation.
-   [`ShellTool`][agents.tool.ShellTool]: the latest shell tool for both local execution and hosted container execution.
-   [`LocalShellTool`][agents.tool.LocalShellTool]: legacy local-shell integration.
-   [`ApplyPatchTool`][agents.tool.ApplyPatchTool]: implement [`ApplyPatchEditor`][agents.editor.ApplyPatchEditor] to apply diffs locally.
-   Local shell skills are availab…
```

</details>

<details><summary>Context after (short)</summary>

```
 This mirrors the platform migration described in OpenAI's [Computer use guide](https://developers.openai.com/api/docs/guides/tools-computer-use/):

-   Model: `computer-use-preview` -> `gpt-5.5`
-   Tool selector: `computer_use_preview` -> `computer`
-   Computer call shape: one `action` per `computer_call` -> batched `actions[]` on `computer_call`
-   Truncation: `ModelSettings(truncation="auto"…
```

</details>

---
## NATQ-C-151

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Domain Types › Thinking Block Param
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> if claude sends back a thinking block do I have to echo the whole thing plus the signature on the next request or can I strip it

**Answer**: You must echo the thinking block unmodified, including the `signature`. Passing a modified block (stripped or altered) returns 400 `invalid_request_error`.

**Atomic claims**:
  - Thinking blocks must be passed back unmodified and in their original order.
  - The signature is the value returned by the API and is used to verify the block was generated by Claude.
  - A modified thinking block results in a 400 invalid_request_error.

**Critical strings**: `Thinking blocks must be passed back unmodified`, `signature`, `invalid_request_error`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 473421–473964 · hash `40f52ad69d59eced8e8171750083667b65c170f8262e358f9afd10cbe2e33548`

```
### Thinking Block Param

- `ThinkingBlockParam object { signature, thinking, type }`

  - `signature: string`

    The `signature` value of this thinking block, exactly as returned by the API in a previous response. Used to verify that the block was generated by Claude.

    Thinking blocks must be passed back unmodified and in their original order; a modified block results in a 400 `invalid_request_error`.

  - `thinking: string`

    The `thinking` text of this block as returned by the API.

  - `type: "thinking"`

    - `"thinking"`
```

<details><summary>Context before (short)</summary>

```
t_editor_code_execution_view_result"`

    - `"text_editor_code_execution_view_result"`

  - `num_lines: optional number or null`

  - `start_line: optional number or null`

  - `total_lines: optional number or null`

### Thinking Block

- `ThinkingBlock object { signature, thinking, type }`

  - `signature: string`

    A value used to verify that this thinking block was generated by Claude when …
```

</details>

<details><summary>Context after (short)</summary>

```

### Thinking Config Adaptive

- `ThinkingConfigAdaptive object { type, display }`

  - `type: "adaptive"`

    - `"adaptive"`

  - `display: optional "summarized" or "omitted" or null`

    Controls how thinking content appears in the response. When set to `summarized`, thinking is returned normally. When set to `omitted`, thinking content is redacted but a signature is returned for multi-turn co…
```

</details>

---
## NATQ-C-152

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Domain Types › Redacted Thinking Block
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> redacted_thinking blocks — keep them in the transcript or delete them

**Answer**: Keep them. Pass `redacted_thinking` blocks back to the API unchanged when continuing a multi-turn conversation. The `data` field is opaque/encrypted.

**Atomic claims**:
  - redacted_thinking is returned when portions of thinking were safety-redacted.
  - Pass redacted_thinking blocks back unchanged in multi-turn conversations.
  - The data field is opaque and encrypted with no readable content.

**Critical strings**: `redacted_thinking`, `Pass `redacted_thinking` blocks back to the API unchanged`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 438322–438909 · hash `4edca6804133f060b40a9e3535dc0804d89a2b3dfb59e15bdee82d95328a3c60`

```
### Redacted Thinking Block

- `RedactedThinkingBlock object { data, type }`

  - `data: string`

    The contents of this redacted thinking block, returned when portions of the model's thinking were safety-redacted. This field is opaque and encrypted, with no readable content.

    Pass `redacted_thinking` blocks back to the API unchanged when continuing a multi-turn conversation.

    See [extended thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking#redacted-thinking-blocks) for details.

  - `type: "redacted_thinking"`

    - `"redacted_thinking"`
```

<details><summary>Context before (short)</summary>

```
ng`

          The incremental `thinking` text for this content block. Concatenate the `thinking` values of successive `thinking_delta` events to assemble the block's full `thinking` value.

        - `type: "thinking_delta"`

          - `"thinking_delta"`

      - `SignatureDelta object { signature, type }`

        - `signature: string`

          The `signature` for this thinking block: an opa…
```

</details>

<details><summary>Context after (short)</summary>

```

### Redacted Thinking Block Param

- `RedactedThinkingBlockParam object { data, type }`

  - `data: string`

    The `data` value of this redacted thinking block, exactly as returned by the API in a previous response. Opaque and encrypted; pass it back unchanged.

  - `type: "redacted_thinking"`

    - `"redacted_thinking"`

### Refusal Stop Details

- `RefusalStopDetails object { category, expla…
```

</details>

---
## NATQ-C-153

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Claude API errors
- **version_id**: `ver_0774ca0093ff4a846753577c9a4a39d5`
- **url**: https://platform.claude.com/docs/en/api/errors
- **section**: Common validation errors › Prefill not supported
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> can I prefill the assistant message on claude so it starts with `{` and stays json

**Answer**: Not on Claude 4.6 and later (or Claude Mythos Preview): assistant prefill is unsupported and returns 400 `invalid_request_error` with message that the conversation must end with a user message. You cannot prefill `{` on those models.

**Atomic claims**:
  - Claude 4.6 and later models and Claude Mythos Preview do not support prefilling assistant messages.
  - A prefilled last assistant message returns 400 invalid_request_error.
  - Error message: This model does not support assistant message prefill. The conversation must end with a user message.

**Critical strings**: `Prefill not supported`, `Claude 4.6`, `invalid_request_error`

### Evidence E1 (verbatim, authoritative)

`ver_0774ca0093ff4a846753577c9a4a39d5` chars 19027–19507 · hash `e702f904afdb91d4390ae32125cb7d2e0212abf5e0ee47a9ebca44bcbae73999`

````
### Prefill not supported

Claude 4.6 and later models and [Claude Mythos Preview](https://anthropic.com/glasswing) do not support prefilling assistant messages. Sending a request with a prefilled last assistant message to any of these models returns a 400 `invalid_request_error`:

```json
{
  "type": "error",
  "error": {
    "type": "invalid_request_error",
    "message": "This model does not support assistant message prefill. The conversation must end with a user message."
````

<details><summary>Context before (short)</summary>

```
teStream(
      model: 'claude-sonnet-5',
      maxTokens: 128000,
      messages: [['role' => 'user', 'content' => 'Write a detailed analysis...']],
  );

  $accumulator = MessageAccumulator::forMessages();
  foreach ($stream as $event) {
      $accumulator->accumulate($event);
  }

  echo array_find($accumulator->message()->content, static fn ($block): bool => $block->type === 'text')->text;
  `…
```

</details>

<details><summary>Context after (short)</summary>

````

  }
}
```

Use [structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) on models that support it, system prompt instructions, or [`output_config.format`](https://platform.claude.com/docs/en/build-with-claude/structured-outputs#json-outputs) instead.

### Thinking blocks cannot be modified

If the most recent assistant message contains `thinking` or `redacted…
````

</details>

---
## NATQ-C-154

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Domain Types › Web Search Tool 20260209
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic web search, what type string goes in the tools array

**Answer**: Put a versioned web-search tool in `tools` with `name` `web_search` and `type` `web_search_20260209` (older schema also has `web_search_20250305`).

**Atomic claims**:
  - The web search tool name is web_search.
  - The tools-array type string for the current schema is web_search_20260209.

**Critical strings**: `web_search`, `web_search_20260209`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 573885–574204 · hash `b6c2bc149b7856621900880bc50917feff4ea5774d2ddf04665285b5cabf3e09`

```
### Web Search Tool 20260209

- `WebSearchTool20260209 object { name, type, allowed_callers, 7 more }`

  - `name: "web_search"`

    Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks.

    - `"web_search"`

  - `type: "web_search_20260209"`

    - `"web_search_20260209"`
```

<details><summary>Context before (short)</summary>

```
ed in initial system prompt. Only loaded when returned via tool_reference from tool search.

  - `max_uses: optional number or null`

    Maximum number of times the tool can be used in the API request.

  - `strict: optional boolean`

    When true, guarantees schema validation on tool names and inputs

  - `user_location: optional UserLocation or null`

    Parameters for the user's location. Us…
```

</details>

<details><summary>Context after (short)</summary>

```


  - `allowed_callers: optional array of "direct" or "code_execution_20250825" or "code_execution_20260120" or "code_execution_20260521"`

    - `"direct"`

    - `"code_execution_20250825"`

    - `"code_execution_20260120"`

    - `"code_execution_20260521"`

  - `allowed_domains: optional array of string or null`

    If provided, only these domains will be included in results. Cannot be used …
```

</details>

---
## NATQ-C-155

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Prompt caching
- **version_id**: `ver_7947433dfde6b3b8eccd0faa597c3c9a`
- **url**: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- **section**: Caching strategies and considerations › Cache limitations
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> prompt cache never hits, is there a min token count before anthropic will actually cache

**Answer**: Yes. There is a minimum cacheable prompt length (model-dependent: 512 / 1,024 / 2,048 / 4,096 tokens). Shorter prompts are processed without caching and no error is returned.

**Atomic claims**:
  - Minimum cacheable prompt length is 512 tokens for Opus 5 / Fable 5 / Mythos 5.
  - Other models have 1,024, 2,048, or 4,096 token floors (Haiku 4.5 is 4,096).
  - Shorter prompts cannot be cached even with cache_control; they are processed without caching and no error is returned.

**Critical strings**: `minimum cacheable prompt length`, `Shorter prompts cannot be cached`

### Evidence E1 (verbatim, authoritative)

`ver_7947433dfde6b3b8eccd0faa597c3c9a` chars 30066–31174 · hash `549d888d480ee4e8f7dbad2d12eef2d36e8d9f8505618330b1518693a46342b7`

```
the minimum cacheable prompt length is:

* 512 tokens for Claude Opus 5, Claude Fable 5, and [Claude Mythos 5](https://anthropic.com/glasswing)
* 2,048 tokens for [Claude Mythos Preview](https://anthropic.com/glasswing) and Claude Opus 4.7
* 4,096 tokens for Claude Opus 4.6 and Claude Opus 4.5
* 1,024 tokens for Claude Opus 4.8, Claude Sonnet 5, Claude Sonnet 4.6, Claude Sonnet 4.5, Claude Opus 4.1 ([retired, except on Bedrock and Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations)), Claude Opus 4 ([retired, except on Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations)), and Claude Sonnet 4 ([retired, except on Bedrock and Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations))
* 4,096 tokens for Claude Haiku 4.5
* 2,048 tokens for Claude Haiku 3.5 ([retired, except on Bedrock and Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations))

These minimums apply on every platform where each model is available.

Shorter prompts cannot be cached, even if marked with `cache_control`.
```

<details><summary>Context before (short)</summary>

```
** You are only charged for:

* **Cache writes:** When new content is written to the cache (25% more than base input tokens for 5-minute TTL)
* **Cache reads:** When cached content is used (10% of base input token price)
* **Regular input tokens:** For any uncached content

Adding more `cache_control` breakpoints doesn't increase your costs - you still pay the same amount based on what content is …
```

</details>

<details><summary>Context after (short)</summary>

```
 Any requests to cache fewer than this number of tokens will be processed without caching, and no error is returned. To verify whether a prompt was cached, check the [response usage fields](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#tracking-cache-performance): if both `cache_creation_input_tokens` and `cache_read_input_tokens` are 0, the prompt was not cached (likely bec…
```

</details>

---
## NATQ-C-159

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Domain Types › Image Block Param
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> can I give claude an image url like openai or is it still base64 only

**Answer**: You can send an image URL. `ImageBlockParam.source` is `Base64ImageSource` or `URLImageSource` (`type: "url"` plus `url`). It is not base64-only.

**Atomic claims**:
  - Image source may be Base64ImageSource or URLImageSource.
  - URLImageSource has type url and a url string.
  - Base64 remains available with media_type image/jpeg|png|gif|webp.

**Critical strings**: `URLImageSource`, `Base64ImageSource`, `"url"`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 252577–253702 · hash `953ea0efd34277bcaa907b18309adee5d8b4d6ad00a4489508a8a5955d8b35b7`

```
### Image Block Param

- `ImageBlockParam object { source, type, cache_control }`

  - `source: Base64ImageSource or URLImageSource`

    - `Base64ImageSource object { data, media_type, type }`

      - `data: string`

      - `media_type: "image/jpeg" or "image/png" or "image/gif" or "image/webp"`

        - `"image/jpeg"`

        - `"image/png"`

        - `"image/gif"`

        - `"image/webp"`

      - `type: "base64"`

        - `"base64"`

    - `URLImageSource object { type, url }`

      - `type: "url"`

        - `"url"`

      - `url: string`

  - `type: "image"`

    - `"image"`

  - `cache_control: optional CacheControlEphemeral or null`

    Create a cache control breakpoint at this content block.

    - `type: "ephemeral"`

      - `"ephemeral"`

    - `ttl: optional "5m" or "1h"`

      The time-to-live for the cache control breakpoint.

      This may be one the following values:

      - `5m`: 5 minutes
      - `1h`: 1 hour

      Defaults to `5m`. See [prompt caching pricing](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) for details.

      - `"5m"`

      - `"1h"`
```

<details><summary>Context before (short)</summary>

```
PFC + web_search results.

  - `content: array of CodeExecutionOutputBlock`

    - `file_id: string`

    - `type: "code_execution_output"`

      - `"code_execution_output"`

  - `encrypted_stdout: string`

  - `return_code: number`

  - `stderr: string`

  - `type: "encrypted_code_execution_result"`

    - `"encrypted_code_execution_result"`

### Encrypted Code Execution Result Block Param

- `E…
```

</details>

<details><summary>Context after (short)</summary>

```

### Input JSON Delta

- `InputJSONDelta object { partial_json, type }`

  - `partial_json: string`

  - `type: "input_json_delta"`

    - `"input_json_delta"`

### JSON Output Format

- `JSONOutputFormat object { schema, type }`

  - `schema: map[unknown]`

    The JSON schema of the format

  - `type: "json_schema"`

    - `"json_schema"`

### Memory Tool 20250818

- `MemoryTool20250818 object {…
```

</details>

---
## NATQ-C-160

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Beta
- **version_id**: `ver_de7f74230c8f10d30aea5d037a3bd0a5`
- **url**: https://platform.claude.com/docs/en/api/beta
- **section**: Messages › Domain Types › Beta File Document Source
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic files api — do I reference a file_id in the document block or still inline the pdf

**Answer**: Reference a previously uploaded file with a document source `{ file_id, type: "file" }` (`BetaFileDocumentSource`), rather than inlining the PDF bytes.

**Atomic claims**:
  - BetaFileDocumentSource has file_id and type file.
  - This is the document-block source shape for a Files API id.

**Critical strings**: `file_id`, `"file"`, `Beta File Document Source`

### Evidence E1 (verbatim, authoritative)

`ver_de7f74230c8f10d30aea5d037a3bd0a5` chars 438428–438570 · hash `5d3597596859e25527dd845b49f59b58d3dca6680ee3d44ff51072572248c22d`

```
### Beta File Document Source

- `BetaFileDocumentSource object { file_id, type }`

  - `file_id: string`

  - `type: "file"`

    - `"file"`
```

<details><summary>Context before (short)</summary>

```
ponse. When set to `summarized`, thinking is returned normally. When set to `omitted`, thinking content is redacted but a signature is returned for multi-turn continuity. Defaults to `summarized`.

          - `"summarized"`

          - `"omitted"`

      - `BetaThinkingConfigDisabled object { type }`

        - `type: "disabled"`

          - `"disabled"`

      - `BetaThinkingConfigAdaptive obj…
```

</details>

<details><summary>Context after (short)</summary>

```

### Beta File Image Source

- `BetaFileImageSource object { file_id, type }`

  - `file_id: string`

  - `type: "file"`

    - `"file"`

### Beta Image Block Param

- `BetaImageBlockParam object { source, type, cache_control }`

  - `source: BetaBase64ImageSource or BetaURLImageSource or BetaFileImageSource`

    - `BetaBase64ImageSource object { data, media_type, type }`

      - `data: string`
…
```

</details>

---
## NATQ-C-161

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: PDF support
- **version_id**: `ver_31cd12f6d13c8ac47666eb1a55874e5d`
- **url**: https://platform.claude.com/docs/en/build-with-claude/pdf-support
- **section**: Before you begin › Check PDF requirements
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> pdf page limit for claude, when does it start rejecting

**Answer**: Maximum pages per request is 600, or 100 when the request's context window is under 1M tokens. Also 32 MB request size and standard (unencrypted) PDF.

**Atomic claims**:
  - Maximum pages per request is 600.
  - The page cap is 100 when the request context window is under 1M tokens.
  - Maximum request size is 32 MB.

**Critical strings**: `Maximum pages per request`, `600`, `100`

### Evidence E1 (verbatim, authoritative)

`ver_31cd12f6d13c8ac47666eb1a55874e5d` chars 912–1513 · hash `87062fe80de77985b1676b211a4b5630c6cd95498c857f6d5cae991cf7c60827`

```
### Check PDF requirements

Claude works with any standard PDF. Ensure your request size meets these requirements:

| Requirement               | Limit                                                                                              |
| ------------------------- | -------------------------------------------------------------------------------------------------- |
| Maximum request size      | 32 MB ([varies by platform](https://platform.claude.com/docs/en/api/overview#request-size-limits)) |
| Maximum pages per request | 600 (100 when the request's context window is under 1M tokens)
```

<details><summary>Context before (short)</summary>

```
DF support
url: https://platform.claude.com/docs/en/build-with-claude/pdf-support
description: "Process PDFs with Claude: extract text, analyze charts, and understand visual content from your documents."
---

## Compatibility
- [ZDR](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention): eligible (excludes [Covered Models](https://platform.claude.com/docs/en/manage-claude/api-a…
```

</details>

<details><summary>Context after (short)</summary>

```
                                     |
| Format                    | Standard PDF (no passwords/encryption)                                                             |

Both limits are on the entire request payload, including any other content sent alongside PDFs. For large PDFs, consider uploading with the [Files API](https://platform.claude.com/docs/en/build-with-claude/files) and referencing …
```

</details>

---
## NATQ-C-162

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Batch processing
- **version_id**: `ver_cec813c3bb15b76dcf16e7a0c2231ef1`
- **url**: https://platform.claude.com/docs/en/build-with-claude/batch-processing
- **section**: Message Batches API › How the Message Batches API works › Batch limitations
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic batch results, how long do they stick around before I have to download

**Answer**: Batch results remain available for 29 days after creation; after that you can still view the Batch but cannot download results.

**Atomic claims**:
  - Batch results are available for 29 days after creation.
  - After that the Batch may still be viewed but results are no longer downloadable.

**Critical strings**: `29 days`, `results will no longer be available for download`

### Evidence E1 (verbatim, authoritative)

`ver_cec813c3bb15b76dcf16e7a0c2231ef1` chars 2746–2901 · hash `9a78c2bd0f4d84be1dd48704370cd3f5b5ea639c85117039fd30d5d15620a094`

```
Batch results are available for 29 days after creation. After that, you may still view the Batch, but its results will no longer be available for download.
```

<details><summary>Context before (short)</summary>

```
en processing has ended for all requests.

This is especially useful for bulk operations that don't require immediate results, such as:

* Large-scale evaluations: Process thousands of test cases efficiently.
* Content moderation: Analyze large volumes of user-generated content asynchronously.
* Data analysis: Generate insights or summaries for large datasets.
* Bulk content generation: Create lar…
```

</details>

<details><summary>Context after (short)</summary>

```

* Batches are scoped to a [Workspace](https://platform.claude.com/settings/workspaces). You may view all batches (and their results) that were created within the Workspace that your API key belongs to.
* Rate limits apply to both Batches API HTTP requests and the number of requests within a batch waiting to be processed. See [Message Batches API rate limits](https://platform.claude.com/docs/en/ap…
```

</details>

---
## NATQ-C-163

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Domain Types › Raw Content Block Delta Event
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> streaming tool args on claude, is it input_json_delta or a content_block_delta with partial_json

**Answer**: Tool-argument streaming is a `content_block_delta` (`RawContentBlockDeltaEvent`) whose `delta` is `InputJSONDelta` with `type: "input_json_delta"` and a `partial_json` string — not a separate top-level `input_json_delta` SSE event name.

**Atomic claims**:
  - RawContentBlockDeltaEvent carries a delta that can be InputJSONDelta.
  - InputJSONDelta has partial_json and type input_json_delta.

**Critical strings**: `Raw Content Block Delta Event`, `input_json_delta`, `partial_json`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 349245–349649 · hash `320274240a25c455710144022ec141d32e1dd399e9b5d4f91fc93911db1dfd77`

```
### Raw Content Block Delta Event

- `RawContentBlockDeltaEvent object { delta, index, type }`

  - `delta: RawContentBlockDelta`

    - `TextDelta object { text, type }`

      - `text: string`

      - `type: "text_delta"`

        - `"text_delta"`

    - `InputJSONDelta object { partial_json, type }`

      - `partial_json: string`

      - `type: "input_json_delta"`

        - `"input_json_delta"`
```

<details><summary>Context before (short)</summary>

```
e's `content` array.

        - `title: string or null`

        - `type: "search_result_location"`

          - `"search_result_location"`

    - `type: "citations_delta"`

      - `"citations_delta"`

  - `ThinkingDelta object { thinking, type }`

    - `thinking: string`

      The incremental `thinking` text for this content block. Concatenate the `thinking` values of successive `thinking_delt…
```

</details>

<details><summary>Context after (short)</summary>

```


    - `CitationsDelta object { citation, type }`

      - `citation: CitationCharLocation or CitationPageLocation or CitationContentBlockLocation or 2 more`

        - `CitationCharLocation object { cited_text, document_index, document_title, 4 more }`

          - `cited_text: string`

          - `document_index: number`

          - `document_title: string or null`

          - `end_char_inde…
```

</details>

---
## NATQ-C-164

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Rate limits
- **version_id**: `ver_c8b2c7130cb18508fed4f864d4c3d7a3`
- **url**: https://platform.claude.com/docs/en/api/rate-limits
- **section**: Rate limits
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic-ratelimit-requests-remaining vs retry-after, which headers actually come back on 429

**Answer**: On 429 the docs explicitly return `retry-after`. The same rate-limit response header set also includes `anthropic-ratelimit-requests-remaining` (requests remaining before being rate limited).

**Atomic claims**:
  - Exceeding a rate limit returns 429 along with a retry-after header.
  - API responses include anthropic-ratelimit-requests-remaining as a returned header.

**Critical strings**: `429`, `retry-after`, `anthropic-ratelimit-requests-remaining`

### Evidence E1 (verbatim, authoritative)

`ver_c8b2c7130cb18508fed4f864d4c3d7a3` chars 5134–5350 · hash `8b29b0a91ed229be9b2fa37fc58bf4401f852d6b854247319ecee512b5ffcaf9`

```
If you exceed any of the rate limits you will get a [429 error](https://platform.claude.com/docs/en/api/errors) describing which rate limit was exceeded, along with a `retry-after` header indicating how long to wait.
```

<details><summary>Context before (short)</summary>

```
 | $1,000 USD        |
| Scale      | $200,000 USD      |

Organizations on the Custom tier have no monthly spend cap; limits are arranged with their account team.

You can also set your own spend limit below your tier's cap to control costs:

<Steps>
  <Step title="Navigate to the Billing page">
    Go to [Settings > Billing](https://platform.claude.com/settings/billing) in the Claude Console.
  …
```

</details>

<details><summary>Context after (short)</summary>

```


<Note>
  You might also encounter 429 errors because of acceleration limits on the API if your organization has a sharp increase in usage. To avoid hitting acceleration limits, ramp up your traffic gradually and maintain consistent usage patterns.
</Note>

### Cache-aware ITPM

Many API providers use a combined "tokens per minute" (TPM) limit that may include all tokens, both cached and uncached…
```

</details>

### Evidence E2 (verbatim, authoritative)

`ver_c8b2c7130cb18508fed4f864d4c3d7a3` chars 23823–24857 · hash `85b8f31ba00e44687ca64a91b158359a036b83a2c0a97f01abbcedc4d14d0ab2`

```
## Response headers

The API response includes headers that show you the rate limit enforced, current usage, and when the limit will be reset.

The following headers are returned:

| Header                                        | Description                                                                                                                           |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `retry-after`                                 | The number of seconds to wait until you can retry the request. Earlier retries will fail.                                             |
| `anthropic-ratelimit-requests-limit`          | The maximum number of requests allowed within any rate limit period.                                                                  |
| `anthropic-ratelimit-requests-remaining`      | The number of requests remaining before being rate limited.
```

---
## NATQ-C-165

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Claude API errors
- **version_id**: `ver_0774ca0093ff4a846753577c9a4a39d5`
- **url**: https://platform.claude.com/docs/en/api/errors
- **section**: Request ID
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> which response header do I paste into an anthropic support ticket, request-id or x-request-id

**Answer**: Paste the `request-id` response header (example `req_018EeWyXxfu5pfWkrYcMdjWG`). The same value appears as `request_id` in error bodies. It is not `x-request-id` (AWS additionally has `x-amzn-requestid`).

**Atomic claims**:
  - Every API response includes a unique request-id header.
  - Include this ID when contacting support.
  - The same identifier appears as request_id in error response bodies.

**Critical strings**: `request-id`, `contacting support`

### Evidence E1 (verbatim, authoritative)

`ver_0774ca0093ff4a846753577c9a4a39d5` chars 6333–6719 · hash `7f9831406fa530fca10b05cb90bafc1c03f6c8a75f11254c6fa412eb52ad8508`

```
## Request ID

Every API response includes a unique `request-id` header. This header contains a value such as `req_018EeWyXxfu5pfWkrYcMdjWG`. The same identifier appears as the `request_id` field in [error response bodies](https://platform.claude.com/docs/en/api/errors#error-shapes). When contacting support about a specific request, include this ID to help quickly resolve your issue.
```

<details><summary>Context before (short)</summary>

```
n` in Java, and as a single `*anthropic.Error` value (branch on `StatusCode`) in Go. Catch the SDK's typed classes rather than string-matching error messages, handling the most specific classes first. Each SDK page documents its full exception hierarchy:

* [Python](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python#handling-errors) · [TypeScript](https://platform.claude.com/docs/e…
```

</details>

<details><summary>Context after (short)</summary>

```


On [Claude Platform on AWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws), responses include two request IDs: the AWS request ID (`x-amzn-requestid`, primary, indexed in CloudTrail) and the Anthropic request ID (`request-id`, secondary). Use the AWS request ID for CloudTrail lookups and the Anthropic request ID for Anthropic support tickets.

The Python and TypeSc…
```

</details>

---
## NATQ-C-166

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Domain Types › Metadata
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> metadata.user_id on /v1/messages, required now or still optional

**Answer**: Still optional. `metadata.user_id` is `optional string or null` — an opaque external identifier, not required.

**Atomic claims**:
  - Metadata.user_id is optional string or null.
  - It should be a uuid, hash, or other opaque identifier.
  - Do not include name, email, or phone number.

**Critical strings**: `user_id: optional string or null`, `Metadata`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 336100–336467 · hash `a8434f8b1e4e4270b96f2416a59a66e2d95772bc9111db498185bb68ab1e357b`

```
### Metadata

- `Metadata object { user_id }`

  - `user_id: optional string or null`

    An external identifier for the user who is associated with the request.

    This should be a uuid, hash value, or other opaque identifier. Anthropic may use this id to help detect abuse. Do not include any identifying information such as name, email address, or phone number.
```

<details><summary>Context before (short)</summary>

```
y via the top-level `system` parameter.

        - `content: array of TextBlockParam`

          System instruction text blocks.

          - `text: string`

          - `type: "text"`

          - `cache_control: optional CacheControlEphemeral or null`

            Create a cache control breakpoint at this content block.

          - `citations: optional array of TextCitationParam or null`

     …
```

</details>

<details><summary>Context after (short)</summary>

```


### Mid Conversation System Block Param

- `MidConversationSystemBlockParam object { content, type, cache_control }`

  System instructions that appear mid-conversation.

  Use this block to provide or update system-level instructions at a specific
  point in the conversation, rather than only via the top-level `system` parameter.

  - `content: array of TextBlockParam`

    System instruction t…
```

</details>

---
## NATQ-C-167

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Create a Message › Body Parameters
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> claude tool_result, can the content be a mix of text and image blocks or only a string

**Answer**: Either a string or an array of blocks. The array may include `TextBlockParam` and `ImageBlockParam`, so a mix of text and image is allowed (not string-only).

**Atomic claims**:
  - tool_result content is optional string or array of TextBlockParam or ImageBlockParam (and others).
  - Image blocks are a legal content array member.

**Critical strings**: `TextBlockParam or ImageBlockParam`, `content: optional string or array`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 13567–13795 · hash `72864f0c019eb55a9b97ab91fbcae1fa4aee027155d2b53b2ffde3e4dc6f18b1`

```
  - `content: optional string or array of TextBlockParam or ImageBlockParam or SearchResultBlockParam or 2 more`

          - `string`

          - `array of TextBlockParam or ImageBlockParam or SearchResultBlockParam or 2 more`
```

<details><summary>Context before (short)</summary>

```
ectCaller object { type }`

            Tool invocation directly from the model.

            - `type: "direct"`

              - `"direct"`

          - `ServerToolCaller object { tool_id, type }`

            Tool invocation generated by a server-side tool.

            - `tool_id: string`

            - `type: "code_execution_20250825"`

              - `"code_execution_20250825"`

          - …
```

</details>

<details><summary>Context after (short)</summary>

```


            - `TextBlockParam object { text, type, cache_control, citations }`

            - `ImageBlockParam object { source, type, cache_control }`

            - `SearchResultBlockParam object { content, source, title, 3 more }`

            - `DocumentBlockParam object { source, type, cache_control, 3 more }`

            - `ToolReferenceBlockParam object { tool_name, type, cache_control }`…
```

</details>

---
## NATQ-C-170

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Count tokens in a Message
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> messages.count_tokens, does it include images and the tools array or just the text

**Answer**: It includes tools, images, and documents — not just text. `POST /v1/messages/count_tokens` counts tokens in a Message including those fields without creating it.

**Atomic claims**:
  - Endpoint is POST /v1/messages/count_tokens.
  - Token Count API counts tokens including tools, images, and documents.

**Critical strings**: `count_tokens`, `including tools, images, and documents`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 95790–96036 · hash `e01134ab384b9285b5c4e43f6b84f5cc1817a76219876cc815a68872fe0bd672`

```
## Count tokens in a Message

**post** `/v1/messages/count_tokens`

Count the number of tokens in a Message.

The Token Count API can be used to count the number of tokens in a Message, including tools, images, and documents, without creating it.
```

<details><summary>Context before (short)</summary>

```
    "type": "char_location"
        }
      ],
      "text": "Hi! My name is Claude.",
      "type": "text"
    }
  ],
  "model": "claude-opus-4-6",
  "role": "assistant",
  "stop_details": {
    "category": "cyber",
    "explanation": "This request was declined because it conflicts with Anthropic's Usage Policy.",
    "type": "refusal"
  },
  "stop_reason": "end_turn",
  "stop_sequence": null,
  …
```

</details>

<details><summary>Context after (short)</summary>

```


Learn more about token counting in our [user guide](https://platform.claude.com/docs/en/build-with-claude/token-counting)

### Header Parameters

- `"anthropic-user-profile-id": optional string`

  The user profile ID to attribute this request to. Use when acting on behalf of a party other than your organization. Requires the `user-profiles` beta header.

### Body Parameters

- `messages: array …
```

</details>

---
## NATQ-C-172

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Computer use tool
- **version_id**: `ver_d9ba3ab0d872dd86047c7ed6dc783235`
- **url**: https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool
- **section**: Compatibility
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> does haiku even support computer use or is that sonnet/opus only

**Answer**: Computer use supported models listed are opus/sonnet families (`claude-opus-5`, `claude-sonnet-5`, `claude-opus-4-8`, `claude-opus-4-7`, `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-opus-4-5-20251101`). Haiku is not in that list.

**Atomic claims**:
  - Computer use is beta with header computer-use-2025-11-24.
  - Supported models listed are opus and sonnet IDs; haiku is absent from the list.

**Critical strings**: `Supported models:`, `claude-sonnet-5`, `claude-opus-5`

### Evidence E1 (verbatim, authoritative)

`ver_d9ba3ab0d872dd86047c7ed6dc783235` chars 237–762 · hash `682cfec786f4ed77493144d950012dd0626fbe864bb6fd754301eacedbe2618e`

```
## Compatibility
- Status: Beta
- [Beta header](https://platform.claude.com/docs/en/api/beta-headers): `computer-use-2025-11-24`
- [ZDR](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention): eligible (excludes [Covered Models](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention#model-specific-data-retention-requirements))
- Supported models: `claude-opus-5`, `claude-sonnet-5`, `claude-opus-4-8`, `claude-opus-4-7`, `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-opus-4-5-20251101
```

<details><summary>Context before (short)</summary>

```
---
title: Computer use tool
url: https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool
description: Give Claude screenshot, mouse, and keyboard control of a desktop environment with the computer use tool.
---

```

</details>

<details><summary>Context after (short)</summary>

```
`
- Platforms: Claude API (beta), Claude Platform on AWS (beta), Amazon Bedrock (beta), Google Cloud (beta), Microsoft Foundry (beta)

Claude can interact with computer environments through the computer use tool, which provides screenshot capabilities and mouse/keyboard control for autonomous desktop interaction.

<Note>
  On Claude Sonnet 4.5, Claude Haiku 4.5, Claude Opus 4.1 ([retired, except o…
```

</details>

---
## NATQ-C-176

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Code execution tool
- **version_id**: `ver_f65938c74d40ac1e288f169d3d0435b7`
- **url**: https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool
- **section**: Container reuse
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> code execution / bash container, if I send back a container_id does the sandbox persist to the next turn

**Answer**: Yes. Reuse the container by sending the previous response's container ID; created files persist across requests. Containers expire 30 days after creation (checkpointed after ~5 minutes idle).

**Atomic claims**:
  - Reuse an existing container by providing the container ID from a previous response.
  - This maintains created files between requests.
  - Containers expire 30 days after creation.

**Critical strings**: `Container reuse`, `container ID`, `30 days`

### Evidence E1 (verbatim, authoritative)

`ver_f65938c74d40ac1e288f169d3d0435b7` chars 43209–43661 · hash `4e51e55687b0dfa55918585f872c98150db524a45208a63d6a26b626eb9d4981`

```
## Container reuse

You can reuse an existing container across multiple API requests by providing the container ID from a previous response. This allows you to maintain created files between requests. With `code_execution_20260120` or later and [programmatic tool calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling), the Python interpreter state persists as well.

Containers expire 30 days after creation.
```

<details><summary>Context before (short)</summary>

```
cs/en/build-with-claude/files), containers are scoped to the workspace of the API key
* **Expiration:** Containers expire 30 days after creation

### Pre-installed libraries

The sandboxed Python environment includes these commonly used libraries:

* **Data science:** pandas, numpy, scipy, scikit-learn, statsmodels
* **Visualization:** matplotlib, seaborn
* **File processing:** pyarrow, openpyxl, …
```

</details>

<details><summary>Context after (short)</summary>

```
 After about 5 minutes of inactivity a container is checkpointed, and sending a request with its ID inside the 30-day window restores it. The `expires_at` timestamp in the response's `container` object is a shorter rolling value and doesn't report the 30-day limit. A container that has expired can't be reused. Send the request again without the `container` parameter to get a new container.

### Ex…
```

</details>

---
## NATQ-C-177

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Computer use tool
- **version_id**: `ver_d9ba3ab0d872dd86047c7ed6dc783235`
- **url**: https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool
- **section**: How to implement computer use › Build a custom computer use environment › Size screenshots to fit image limits
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> computer use click coordinates — if I downscale the screenshot do I have to scale the x/y back

**Answer**: Yes. If the screenshot is downscaled (or Retina 2x), you must scale coordinates back: either downscale the screenshot before sending, or scale/halve the x/y Claude returns before clicking.

**Atomic claims**:
  - Retina screenshots are 2x logical coordinates.
  - Either downscale the screenshot 2x before sending, or halve the coordinates Claude returns before clicking.

**Critical strings**: `downscale the screenshot`, `halve the coordinates`

### Evidence E1 (verbatim, authoritative)

`ver_d9ba3ab0d872dd86047c7ed6dc783235` chars 66148–66415 · hash `784700e2a8801a9af6828defc1e4531e1e5637b0264eb776c66d8385621b86c7`

```
**macOS Retina displays** capture screenshots at a device pixel ratio of 2, so the image is twice the resolution of the logical screen coordinates. Either downscale the screenshot by 2x before sending, or halve the coordinates Claude returns before issuing the click.
```

<details><summary>Context before (short)</summary>

```
$scale);

  // Resize image to scaled dimensions before sending to Claude
  $screenshot = captureAndResize($scaledWidth, $scaledHeight);

  // When handling Claude's coordinates, scale them back up
  $executeClick = fn(int $x, int $y) => performClick($x / $scale, $y / $scale);
  ```

  ```ruby Ruby
  def get_scale_factor(width, height)
    [1.0, 1568.0 / [width, height].max, Math.sqrt(1_150_000.0 …
```

</details>

<details><summary>Context after (short)</summary>

```

</Note>

#### Diagnose click issues

If clicks miss their targets, the cause is usually one of the following:

| Symptom                                           | Likely cause                                                                                  | Try                                                                                                               |
| --------------------…
```

</details>

---
## NATQ-C-179

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Create a Message › Body Parameters
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> claude system prompt, string vs array of text blocks, both valid?

**Answer**: Both are valid. `system` is `optional string or array of TextBlockParam`.

**Atomic claims**:
  - system is optional string or array of TextBlockParam.
  - The array form is TextBlockParam blocks (text/type, optional cache_control).

**Critical strings**: `optional string or array of TextBlockParam`, `system:`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 32218–32618 · hash `ef1c71ae6a34cdbb0470a42f6d8bf59953583b71ae7c7af6a6fa194d17a20cd4`

```
- `system: optional string or array of TextBlockParam`

  System prompt.

  A system prompt is a way of providing context and instructions to Claude, such as specifying a particular goal or role. See our [guide to system prompts](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#give-claude-a-role).

  - `string`

  - `array of TextBlockParam`
```

<details><summary>Context before (short)</summary>

```
ice-tiers](https://platform.claude.com/docs/en/api/service-tiers) for details.

  - `"auto"`

  - `"standard_only"`

- `stop_sequences: optional array of string`

  Custom text sequences that will cause the model to stop generating.

  Our models will normally stop when they have naturally completed their turn, which will result in a response `stop_reason` of `"end_turn"`.

  If you want the model…
```

</details>

<details><summary>Context after (short)</summary>

```


    - `text: string`

    - `type: "text"`

    - `cache_control: optional CacheControlEphemeral or null`

      Create a cache control breakpoint at this content block.

    - `citations: optional array of TextCitationParam or null`

- `temperature: optional number`

  Amount of randomness injected into the response.

  Defaults to `1.0`. Ranges from `0.0` to `1.0`. Use `temperature` closer to …
```

</details>

---
## NATQ-C-182

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Batches
- **version_id**: `ver_ef5f9dacc17f99c298faf449e756ae90`
- **url**: https://platform.claude.com/docs/en/api/messages/batches
- **section**: Batches › Create a Message Batch › Body Parameters
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> batch custom_id uniqueness, unique inside that batch or unique forever

**Answer**: Unique inside that batch: `custom_id` must be unique for each request within the Message Batch (used to match results; order is not guaranteed).

**Atomic claims**:
  - custom_id is a developer-provided ID per request in a Message Batch.
  - It must be unique for each request within the Message Batch.

**Critical strings**: `custom_id`, `unique for each request within the Message Batch`

### Evidence E1 (verbatim, authoritative)

`ver_ef5f9dacc17f99c298faf449e756ae90` chars 1087–1332 · hash `f7641a15a370674546d36c867e1edb801593640bd7340579b625dddb55d55218`

```
  - `custom_id: string`

    Developer-provided ID created for each request in a Message Batch. Useful for matching results to requests, as results may be given out of request order.

    Must be unique for each request within the Message Batch.
```

<details><summary>Context before (short)</summary>

```
on requests.

The Message Batches API can be used to process multiple Messages API requests at once. Once a Message Batch is created, it begins processing immediately. Batches can take up to 24 hours to complete.

Learn more about the Message Batches API in our [user guide](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

### Header Parameters

- `"anthropic-user-profile-id…
```

</details>

<details><summary>Context after (short)</summary>

```


  - `params: object { max_tokens, messages, model, 15 more }`

    Messages API creation parameters for the individual request.

    See the [Messages API reference](https://platform.claude.com/docs/en/api/messages) for full documentation on available parameters.

    - `max_tokens: number`

      The maximum number of tokens to generate before stopping.

      Note that our models may stop _bef…
```

</details>

---
## NATQ-C-186

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Domain Types › Message Delta Usage
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> claude stream message_delta.usage, running total or just the last chunk

**Answer**: Running total. `message_delta.usage` fields are described as cumulative (input, cache, and `output_tokens` are 'the cumulative number ... which were used'), not last-chunk deltas.

**Atomic claims**:
  - cache_creation_input_tokens / cache_read_input_tokens / input_tokens on MessageDeltaUsage are cumulative.
  - output_tokens is the cumulative number of output tokens used.

**Critical strings**: `cumulative number of output tokens`, `Message Delta Usage`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 309826–310381 · hash `735b368401e8de2c84e4020b9cd00e09acc616fc881499f5328f8c31401e7ee8`

```
### Message Delta Usage

- `MessageDeltaUsage object { cache_creation_input_tokens, cache_read_input_tokens, input_tokens, 3 more }`

  - `cache_creation_input_tokens: number or null`

    The cumulative number of input tokens used to create the cache entry.

  - `cache_read_input_tokens: number or null`

    The cumulative number of input tokens read from the cache.

  - `input_tokens: number or null`

    The cumulative number of input tokens which were used.

  - `output_tokens: number`

    The cumulative number of output tokens which were used.
```

<details><summary>Context before (short)</summary>

```
el and in `tool_use` blocks.

      - `"tool_search_tool_regex"`

    - `type: "tool_search_tool_regex_20251119" or "tool_search_tool_regex"`

      - `"tool_search_tool_regex_20251119"`

      - `"tool_search_tool_regex"`

    - `allowed_callers: optional array of "direct" or "code_execution_20250825" or "code_execution_20260120" or "code_execution_20260521"`

      - `"direct"`

      - `"code_e…
```

</details>

<details><summary>Context after (short)</summary>

```


  - `output_tokens_details: OutputTokensDetails or null`

    Breakdown of output tokens by category.

    `output_tokens` remains the inclusive, authoritative total used for billing.
    This object provides a read-only decomposition for observability — for example,
    how many of the billed output tokens were spent on internal reasoning that may
    have been summarized before being returned …
```

</details>

---
## NATQ-C-187

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Cancel a Message Batch
- **version_id**: `ver_61b47461370755f2d32a2e0e77ab18e3`
- **url**: https://platform.claude.com/docs/en/api/messages/batches/cancel
- **section**: Cancel a Message Batch
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> how do I cancel an in-flight anthropic message batch

**Answer**: POST `/v1/messages/batches/{message_batch_id}/cancel`. Batches may be canceled any time before processing ends (then `canceling`; in-progress non-interruptible requests may still finish).

**Atomic claims**:
  - Cancel path is POST /v1/messages/batches/{message_batch_id}/cancel.
  - Batches may be canceled any time before processing ends.

**Critical strings**: `/v1/messages/batches/{message_batch_id}/cancel`, `canceled any time before processing ends`

### Evidence E1 (verbatim, authoritative)

`ver_61b47461370755f2d32a2e0e77ab18e3` chars 108–250 · hash `65d18a6b96daa9a165f2cb996af30657b85c9427a8b5efa366cb484dfbb8a77a`

```
## Cancel a Message Batch

**post** `/v1/messages/batches/{message_batch_id}/cancel`

Batches may be canceled any time before processing ends.
```

<details><summary>Context before (short)</summary>

```
---
title: Cancel a Message Batch
url: https://platform.claude.com/docs/en/api/messages/batches/cancel
---

```

</details>

<details><summary>Context after (short)</summary>

```
 Once cancellation is initiated, the batch enters a `canceling` state, at which time the system may complete any in-progress, non-interruptible requests before finalizing cancellation.

The number of canceled requests is specified in `request_counts`. To determine which requests were canceled, check the individual results within the batch. Note that cancellation may not result in any canceled requ…
```

</details>

---
## NATQ-C-188

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Domain Types › Base64 Image Source
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> image source.media_type, do I have to send image/png or will claude sniff it

**Answer**: You have to send `media_type`. Base64 image source requires `media_type` as one of `image/jpeg`, `image/png`, `image/gif`, or `image/webp` — there is no sniff-it-for-me field.

**Atomic claims**:
  - Base64ImageSource includes required media_type enum image/jpeg, image/png, image/gif, image/webp.
  - type is base64.

**Critical strings**: `media_type`, `image/png`, `image/jpeg`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 160584–160889 · hash `efa725149fb2991519c1815ce5d86f65f6b74da85ad5525086a16d0f27b72491`

```
### Base64 Image Source

- `Base64ImageSource object { data, media_type, type }`

  - `data: string`

  - `media_type: "image/jpeg" or "image/png" or "image/gif" or "image/webp"`

    - `"image/jpeg"`

    - `"image/png"`

    - `"image/gif"`

    - `"image/webp"`

  - `type: "base64"`

    - `"base64"`
```

<details><summary>Context before (short)</summary>

```
\
    -H "X-Api-Key: $ANTHROPIC_API_KEY" \
    -d '{
          "messages": [
            {
              "content": "Hello, world",
              "role": "user"
            }
          ],
          "model": "claude-opus-4-6",
          "system": [
            {
              "text": "Today'\''s date is 2024-06-01.",
              "type": "text"
            }
          ],
          "thinking": {
  …
```

</details>

<details><summary>Context after (short)</summary>

```

### Base64 PDF Source

- `Base64PDFSource object { data, media_type, type }`

  - `data: string`

  - `media_type: "application/pdf"`

    - `"application/pdf"`

  - `type: "base64"`

    - `"base64"`

### Bash Code Execution Output Block

- `BashCodeExecutionOutputBlock object { file_id, type }`

  - `file_id: string`

  - `type: "bash_code_execution_output"`

    - `"bash_code_execution_output"…
```

</details>

---
## NATQ-C-189

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Computer use tool
- **version_id**: `ver_d9ba3ab0d872dd86047c7ed6dc783235`
- **url**: https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool
- **section**: How to implement computer use › Available actions
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> computer use actions — screenshot, mouse_move, left_click, type, is key its own action or part of type

**Answer**: `key` is its own action, not part of `type`. Basic actions include screenshot, left_click, type (text string), key (key or combo such as ctrl+s), and mouse_move.

**Atomic claims**:
  - Basic actions include screenshot, left_click, type, key, and mouse_move.
  - key presses a key or key combination (e.g. ctrl+s), separate from type which types a text string.

**Critical strings**: `left_click`, `**key:**`, `**type:**`

### Evidence E1 (verbatim, authoritative)

`ver_d9ba3ab0d872dd86047c7ed6dc783235` chars 29420–29711 · hash `4f7a1c02f12accdfd147b9dcc17ed75eb68ab7b18bbc12dadcd638524a5da58a`

```
### Available actions

The computer use tool supports these actions:

**Basic actions (all versions)**

* **screenshot:** Capture the current display
* **left\_click:** Click at coordinates `[x, y]`
* **type:** Type text string
* **key:** Press key or key combination (for example, "ctrl+s")
```

<details><summary>Context before (short)</summary>

```
iew alone misses. See [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) for details.
</Tip>

### System prompts

When one of the Anthropic-schema tools is requested through the Claude API, a computer use-specific system prompt is generated. It's similar to the [tool use system prompt](https://platform.claude.com/docs/en…
```

</details>

<details><summary>Context after (short)</summary>

```

* **mouse\_move:** Move cursor to coordinates

**Enhanced actions (`computer_20250124` and later)** Available in `computer_20250124` and `computer_20251124`:

* **scroll:** Scroll in any direction with amount control
* **left\_click\_drag:** Click and drag between coordinates
* **right\_click**, **middle\_click:** Additional mouse buttons
* **double\_click**, **triple\_click:** Multiple clicks
* …
```

</details>

---
## NATQ-C-191

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Thinking
- **version_id**: `ver_012b734775e7edb2649d3a9ddfd93070`
- **url**: https://platform.claude.com/docs/en/build-with-claude/thinking
- **section**: Thinking with tool use
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> tool_choice none with thinking enabled, allowed or 400

**Answer**: Allowed (not a 400) for `tool_choice: {"type": "none"}` with manual extended thinking (`thinking: {type: "enabled"}`). Manual thinking only supports `auto` (default) or `none`; `any` or a named `tool` force tool use and error. Adaptive thinking does support forced tool use.

**Atomic claims**:
  - Manual extended thinking only supports tool_choice auto or none.
  - tool_choice any or a named tool results in an error with manual extended thinking.
  - Adaptive thinking supports forced tool use.

**Critical strings**: `tool_choice`, `none`, `thinking`, `results in an error`

### Evidence E1 (verbatim, authoritative)

`ver_012b734775e7edb2649d3a9ddfd93070` chars 34322–35060 · hash `7c1e176d598061d4c7f578f15c47bbd335c308637e8565d784665fe71f113f6a`

```
## Thinking with tool use

Thinking works alongside [tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview), letting Claude reason through tool selection and process tool results. Two constraints apply:

1. **Tool choice limitation (manual mode):** tool use with manual extended thinking (`thinking: {type: "enabled"}`) only supports `tool_choice: {"type": "auto"}` (the default) or `tool_choice: {"type": "none"}`. Using `tool_choice: {"type": "any"}` or `tool_choice: {"type": "tool", "name": "..."}` results in an error because these options force tool use, which is incompatible with manual extended thinking. Adaptive thinking, including on models where thinking is on by default, supports forced tool use.
```

<details><summary>Context before (short)</summary>

```
//platform.claude.com/docs/en/build-with-claude/extended-thinking#budget-rules-and-tuning).

With the two controls separated this way, pick the one that matches your goal:

* **Lower cost or latency on a thinking-enabled workload:** lower `effort` first. It scales the whole response down, thinking included.
* **Claude is thinking too rarely or too shallowly:** raise `effort`, or see [Steering how …
```

</details>

<details><summary>Context after (short)</summary>

```

2. **Preserving thinking blocks:** when you return tool results, you must pass the thinking blocks from the assistant message back to the API, complete and unmodified. See [Preserving thinking blocks](https://platform.claude.com/docs/en/build-with-claude/thinking#preserving-thinking-blocks).

**A tool-use loop is one assistant turn.** From the model's perspective, an assistant turn doesn't comple…
```

</details>

---
## NATQ-C-193

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: API overview
- **version_id**: `ver_6cbca1c2343b84b7d5cf99029456cfa2`
- **url**: https://platform.claude.com/docs/en/api/overview
- **section**: Request and response format › Response headers
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic-organization or anthropic-workspace header, does that exist

**Answer**: Not under those exact names. The corpus documents `anthropic-organization-id` as a response header (org of the API key/token) and `anthropic-workspace-id` as a request header required on Claude Platform on AWS. There is no `anthropic-organization` or `anthropic-workspace` header as guessed.

**Atomic claims**:
  - anthropic-organization-id is a documented response header identifying the organization of the API key or token.
  - anthropic-workspace-id is a request header used to target a workspace on Claude Platform on AWS.
  - The guessed names without the -id suffix are not the documented headers.

**Critical strings**: `anthropic-organization-id`, `anthropic-workspace-id`

### Evidence E1 (verbatim, authoritative)

`ver_6cbca1c2343b84b7d5cf99029456cfa2` chars 12322–12443 · hash `023ee059d163c56697c87ca32d5e7326d8ae8e7b3f3f15eadd221a3a84b78f5c`

```
`anthropic-organization-id` | The ID of the organization that the API key or access token used in the request belongs to.
```

<details><summary>Context before (short)</summary>

```
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `request-id`                | A globally unique identifier for the request, such as `req_018EeWyXxfu5p…
```

</details>

<details><summary>Context after (short)</summary>

```
                                                                                                                                                                                                                                                                                                                                                                                                                …
```

</details>

### Evidence E2 (verbatim, authoritative)

`ver_5ebdc722f9bedb1e2e8cbd3f29ff6805` chars 48160–48339 · hash `1824b8420b2c3c818c721edf04ed2bd3b1a012e81d18b4da21807690e3b08c65`

```
## Workspaces

Inference and resource requests on Claude Platform on AWS target a workspace. You pass the workspace's ID in the `anthropic-workspace-id` header on these API calls.
```

---
## NATQ-C-199

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Domain Types › Citation Page Location
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> claude citation objects, is the span in cited_text or document_index plus start_page_number

**Answer**: Both. A page_location citation object includes `cited_text` (the quoted span) plus location fields `document_index` and `start_page_number` (and `end_page_number`). The span text is not instead-of the location fields.

**Atomic claims**:
  - CitationPageLocation includes cited_text.
  - CitationPageLocation includes document_index.
  - CitationPageLocation includes start_page_number and end_page_number.
  - type is page_location.

**Critical strings**: `cited_text`, `document_index`, `start_page_number`, `page_location`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 169975–170332 · hash `aaed5065ef62745568ebf0af07d11ce2c481a1df2feb29c5163d258964ff212f`

```
### Citation Page Location

- `CitationPageLocation object { cited_text, document_index, document_title, 4 more }`

  - `cited_text: string`

  - `document_index: number`

  - `document_title: string or null`

  - `end_page_number: number`

  - `file_id: string or null`

  - `start_page_number: number`

  - `type: "page_location"`

    - `"page_location"`
```

<details><summary>Context before (short)</summary>

```
 document_title, 3 more }`

  - `cited_text: string`

    The full text of the cited block range, concatenated.

    Always equals the contents of `content[start_block_index:end_block_index]` joined together. The text block is the minimal citable unit; this field is never a substring of a single block. Not counted toward output tokens, and not counted toward input tokens when sent back in subseque…
```

</details>

<details><summary>Context after (short)</summary>

```


### Citation Page Location Param

- `CitationPageLocationParam object { cited_text, document_index, document_title, 3 more }`

  - `cited_text: string`

  - `document_index: number`

  - `document_title: string or null`

  - `end_page_number: number`

  - `start_page_number: number`

  - `type: "page_location"`

    - `"page_location"`

### Citation Search Result Location Param

- `CitationSearc…
```

</details>

---
## NATQ-C-200

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Streaming messages
- **version_id**: `ver_1261879c16f641270789647ac9c63c96`
- **url**: https://platform.claude.com/docs/en/build-with-claude/streaming
- **section**: Event types › Error events
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic sse error event, is type just error and where is the nested error.type

**Answer**: SSE uses `event: error`. The JSON payload has `type` `error` at the top level and the nested code in `error.type` (example: `overloaded_error`).

**Atomic claims**:
  - Streaming error events are sent as event: error.
  - The data object has type error.
  - The nested error.type holds the error class such as overloaded_error.

**Critical strings**: `event: error`, `"type": "error"`, `error.type`, `overloaded_error`

### Evidence E1 (verbatim, authoritative)

`ver_1261879c16f641270789647ac9c63c96` chars 9920–10325 · hash `2465d93c6d9acb205496b2c109fc8295c9860051b1439bb0adcabd4cf0f16828`

````
### Error events

The API may occasionally send [errors](https://platform.claude.com/docs/en/api/errors) in the event stream. For example, during periods of high usage, you may receive an `overloaded_error`, which would normally correspond to an HTTP 529 in a non-streaming context:

```sse Example error
event: error
data: {"type": "error", "error": {"type": "overloaded_error", "message": "Overloaded"}}
````

<details><summary>Context before (short)</summary>

```
ect with empty `content`.
2. A series of content blocks, each of which has a `content_block_start`, one or more `content_block_delta` events, and a `content_block_stop` event. Each content block has an `index` that corresponds to its index in the final Message `content` array. One exception: during [server-side fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback#s…
```

</details>

<details><summary>Context after (short)</summary>

````

```

### Other events

In accordance with the [versioning policy](https://platform.claude.com/docs/en/api/versioning), new event types may be added, and your code should handle unknown event types gracefully.

## Content block delta types

Each `content_block_delta` event contains a `delta` of a type that updates the `content` block at a given `index`.

### Text delta

A `text` content block delt…
````

</details>

---
## NATQ-C-201

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Handoffs
- **version_id**: `ver_1c77f33b04ffffa285ea7e61c2a89653`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/handoffs.md
- **section**: (1)! › Input filters
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> agents sdk handoff input_filter — can I strip prior tool calls from the history I pass the next agent

**Answer**: Yes. Set `input_filter` on the handoff. Built-in `handoff_filters.remove_all_tools` strips tool-related items from the history the next agent sees.

**Atomic claims**:
  - By default the receiving agent sees the entire previous conversation history.
  - input_filter can change that history.
  - handoff_filters.remove_all_tools removes all tool-related items from the history.

**Critical strings**: `input_filter`, `remove_all_tools`, `tool-related items`

### Evidence E1 (verbatim, authoritative)

`ver_1c77f33b04ffffa285ea7e61c2a89653` chars 6481–6885 · hash `00cdd52c2129c68b65e1cc546da8f220c2e54a432b4d7e23066907153283d815`

```
When a handoff occurs, it's as though the new agent takes over the conversation, and gets to see the entire previous conversation history. If you want to change this, you can set an [`input_filter`][agents.handoffs.Handoff.input_filter]. An input filter is a function that receives the existing input via a [`HandoffInputData`][agents.handoffs.HandoffInputData], and must return a new `HandoffInputData`.
```

<details><summary>Context before (short)</summary>

```
 is different:

-   Put existing application state and dependencies in [`RunContextWrapper.context`][agents.run_context.RunContextWrapper.context]. See the [context guide](context.md).
-   Use [`input_filter`][agents.handoffs.Handoff.input_filter], [`RunConfig.nest_handoff_history`][agents.run.RunConfig.nest_handoff_history], or [`RunConfig.handoff_history_mapper`][agents.run.RunConfig.handoff_his…
```

</details>

<details><summary>Context after (short)</summary>

```


[`HandoffInputData`][agents.handoffs.HandoffInputData] includes:

-   `input_history`: the input history before `Runner.run(...)` started.
-   `pre_handoff_items`: items generated before the agent turn where the handoff was invoked.
-   `new_items`: items generated during the current turn, including the handoff call and handoff output items.
-   `input_items`: optional items to forward to the ne…
```

</details>

### Evidence E2 (verbatim, authoritative)

`ver_1c77f33b04ffffa285ea7e61c2a89653` chars 9915–10406 · hash `a49f4c137aff1cdb74ec66aab1db720af73333a09b2df4f1dc5008d0207ac94e`

````
There are some common patterns (for example removing all tool calls from the history), which are implemented for you in [`agents.extensions.handoff_filters`][]

```python
from agents import Agent, handoff
from agents.extensions import handoff_filters

agent = Agent(name="FAQ agent")

handoff_obj = handoff(
    agent=agent,
    input_filter=handoff_filters.remove_all_tools, # (1)!
)
```

1. This will automatically remove all tool-related items from the history when `FAQ agent` is called.
````

---
## NATQ-C-203

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Models
- **version_id**: `ver_ae909bf8b4bbbe1d1a11119447f7ac94`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/models/index.md
- **section**: Models › OpenAI models › Default model
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> Agent.model is 4.1 and RunConfig.model is mini, which one actually gets called

**Answer**: Agent.model wins. `RunConfig.model` is only the run default for agents that do not set a model. If Agent.model is 4.1, that is what is called, not RunConfig's mini.

**Atomic claims**:
  - RunConfig.model is a default model for the run.
  - That run model is used if the agent does not set a model.

**Critical strings**: `RunConfig`, `If you don't set a model for an agent`

### Evidence E1 (verbatim, authoritative)

`ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 2874–3006 · hash `7d9cb6ba1babf4327840158a1f6be21283db7d8d907be4a59d309596a0271e41`

```
Second, you can set a default model for a run via `RunConfig`. If you don't set a model for an agent, this run's model will be used.
```

<details><summary>Context before (short)</summary>

```
g model names with the default OpenAI provider and stay on the Responses model path.

When an [`Agent`][agents.agent.Agent] does not specify a model, the Agents SDK uses [`gpt-5.6-luna`](https://developers.openai.com/api/docs/models/gpt-5.6-luna) with `reasoning.effort="none"` and `verbosity="low"` by default for cost-sensitive, high-volume agent workflows. Applications that need frontier capabili…
```

</details>

<details><summary>Context after (short)</summary>

````


```python
from agents import Agent, RunConfig, Runner

agent = Agent(
    name="Assistant",
    instructions="You're a helpful agent.",
)

result = await Runner.run(
    agent,
    "Hello",
    run_config=RunConfig(model="gpt-5.6-sol"),
)
```

#### GPT-5 models

When you use any GPT-5 model such as `gpt-5.6-sol` in this way, the SDK applies default `ModelSettings`. It sets the ones that work the…
````

</details>

---
## NATQ-C-205

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Agents
- **version_id**: `ver_35cac5e98c151a17f941a6142d74709f`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/agents.md
- **section**: Agents › Dynamic instructions
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> dynamic instructions, can Agent(instructions=) take a callable or do I rebuild the agent every request

**Answer**: Yes. `Agent(instructions=)` can take a callable (sync or async). The function receives the agent and context and must return the prompt; you do not have to rebuild the agent every request.

**Atomic claims**:
  - Instructions can be provided as a function (dynamic instructions).
  - The function receives the agent and context and must return the prompt.
  - Both regular and async functions are accepted.
  - Example passes instructions=dynamic_instructions into Agent.

**Critical strings**: `Dynamic instructions`, `function`, `instructions=dynamic_instructions`

### Evidence E1 (verbatim, authoritative)

`ver_35cac5e98c151a17f941a6142d74709f` chars 9488–10122 · hash `dc6a7a92dd360938380ae965a0bde5a21aab8f9892b31f2ee460499269c39d02`

````
## Dynamic instructions

In most cases, you can provide instructions when you create the agent. However, you can also provide dynamic instructions via a function. The function will receive the agent and context, and must return the prompt. Both regular and `async` functions are accepted.

```python
from agents import Agent, RunContextWrapper

def dynamic_instructions(
    context: RunContextWrapper[UserContext], agent: Agent[UserContext]
) -> str:
    return f"The user's name is {context.context.name}. Help them with their questions."


agent = Agent[UserContext](
    name="Triage agent",
    instructions=dynamic_instructions,
````

<details><summary>Context before (short)</summary>

````
  ),
        refund_agent.as_tool(
            tool_name="refund_expert",
            tool_description="Handles refund questions and requests.",
        )
    ],
)
```

### Handoffs

Configured handoff targets are sub‑agents to which the agent can delegate. When a handoff occurs, the delegated agent receives the conversation history and takes over the conversation. This pattern enables modular, sp…
````

</details>

<details><summary>Context after (short)</summary>

````

)
```

## Lifecycle events (hooks)

Sometimes, you want to observe the lifecycle of an agent. For example, you may want to log events, pre-fetch data, or record usage when certain events occur.

There are two hook scopes:

-   [`RunHooks`][agents.lifecycle.RunHooks] observe the entire `Runner.run(...)` invocation, including handoffs to other agents.
-   [`AgentHooks`][agents.lifecycle.AgentHooks]…
````

</details>

---
## NATQ-C-207

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Models
- **version_id**: `ver_ae909bf8b4bbbe1d1a11119447f7ac94`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/models/index.md
- **section**: Models › Advanced OpenAI Responses settings › Common advanced `ModelSettings` options
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> responses store=false, can I still chain previous_response_id

**Answer**: Not as a server-side chain. `store=False` means the response is not kept for later server-side retrieval, so features that reuse response IDs must use locally managed state instead of chaining `previous_response_id` against a stored response.

**Atomic claims**:
  - store=False does not keep the response available for later server-side retrieval.
  - Features that reuse response IDs need locally managed state instead.

**Critical strings**: `store=False`, `server-side retrieval`, `response IDs`

### Evidence E1 (verbatim, authoritative)

`ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 28977–29517 · hash `4a70be911130af9868d740ae77b4dd3b5194ab016cd0426126be986f6d05aa77`

```
When you set `store=False`, the Responses API does not keep that response available for later server-side retrieval. This is useful for stateless or zero-data-retention style flows, but it also means features that would otherwise reuse response IDs need to rely on locally managed state instead. For example, [`OpenAIResponsesCompactionSession`][agents.memory.openai_responses_compaction_session.OpenAIResponsesCompactionSession] switches its default `"auto"` compaction path to input-based compaction when the last response was not stored.
```

<details><summary>Context before (short)</summary>

````
is passed through on Responses and Chat Completions requests, and the Chat Completions converter preserves breakpoints on text, image, audio, and file content parts.

```python
from agents import Runner

result = await Runner.run(
    research_agent,
    [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    …
````

</details>

<details><summary>Context after (short)</summary>

```
 See the [Sessions guide](../sessions/index.md#openai-responses-compaction-sessions).

Server-side compaction is different from [`OpenAIResponsesCompactionSession`][agents.memory.openai_responses_compaction_session.OpenAIResponsesCompactionSession]. `context_management=[{"type": "compaction", "compact_threshold": ...}]` is sent with each Responses API request, and the API can emit compaction items…
```

</details>

---
## NATQ-C-209

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Models
- **version_id**: `ver_ae909bf8b4bbbe1d1a11119447f7ac94`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/models/index.md
- **section**: Models › Advanced OpenAI Responses settings › Common advanced `ModelSettings` options
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> include array on responses, exact string to get file_search_call.results back

**Answer**: The exact include string is `file_search_call.results` (Agents SDK exposes it as `ModelSettings.response_include`).

**Atomic claims**:
  - response_include requests richer response payloads.
  - file_search_call.results is a documented include string.

**Critical strings**: `response_include`, `file_search_call.results`

### Evidence E1 (verbatim, authoritative)

`ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 27031–27152 · hash `e807bb49d64479f7b9c238438aef707a360cbf98b7d844e532af5facfa886542`

```
`response_include`: Request richer response payloads such as `web_search_call.action.sources`, `file_search_call.results`
```

<details><summary>Context before (short)</summary>

```
y have direct `ModelSettings` fields, so you do not need `extra_args` for them.

- `parallel_tool_calls`: Allow or forbid multiple tool calls in the same turn.
- `truncation`: Set `"auto"` to let the Responses API drop the oldest conversation items instead of failing when context would overflow.
- `store`: Control whether the generated response is stored server-side for later retrieval. This matte…
```

</details>

<details><summary>Context after (short)</summary>

````
, or `reasoning.encrypted_content`.
- `top_logprobs`: Request top-token logprobs for output text. The SDK also adds `message.output_text.logprobs` automatically.
- `retry`: Opt in to runner-managed retry settings for model calls. See [Runner-managed retries](#runner-managed-retries).

```python
from agents import Agent, ModelSettings

research_agent = Agent(
    name="Research agent",
    model="g…
````

</details>

---
## NATQ-C-212

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Models
- **version_id**: `ver_ae909bf8b4bbbe1d1a11119447f7ac94`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/models/index.md
- **section**: Models › OpenAI models › Default model › GPT-5 models
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> reasoning encrypted_content on responses, do I have to roundtrip it like anthropic thinking signatures

**Answer**: Yes for stateless `store=False` calls: request `reasoning.encrypted_content` and send those reasoning items back as input on the next request (round-trip, analogous to keeping Anthropic thinking blocks).

**Atomic claims**:
  - For store=False calls, request reasoning.encrypted_content in the response.
  - Include those reasoning items as input in the next request.

**Critical strings**: `encrypted_content`, `store=False`, `next request`

### Evidence E1 (verbatim, authoritative)

`ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 5194–5348 · hash `27b4dd17e33e4dd6c5e485b79531617e2b77e83959a69bf6c476420134b8919f`

```
For stateless `store=False` calls, request `reasoning.encrypted_content` in the response, then include those reasoning items as input in the next request.
```

<details><summary>Context before (short)</summary>

````
ed import Reasoning
from agents import Agent, ModelSettings

agent = Agent(
    name="Deep research agent",
    model="gpt-5.6-sol",
    model_settings=ModelSettings(
        reasoning=Reasoning(
            mode="pro",
            effort="max",
            context="all_turns",
        ),
    ),
)
```

`reasoning.mode` and `reasoning.context` are Responses-only settings. Chat Completions uses only…
````

</details>

<details><summary>Context after (short)</summary>

```


#### ComputerTool model selection

If an agent includes [`ComputerTool`][agents.tool.ComputerTool], the effective model on the actual Responses request determines which computer-tool payload the SDK sends. Explicit `gpt-5.5` requests use the GA built-in `computer` tool, while explicit `computer-use-preview` requests keep the older `computer_use_preview` payload.

Prompt-managed calls are the mai…
```

</details>

---
## NATQ-C-217

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Running agents
- **version_id**: `ver_2c60e99cfd929a738910b893fd6f1a40`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/running_agents.md
- **section**: Running agents › State and conversation management › Conversations/chat threads › Manual conversation management
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> RunResult.to_input_list — is that the supported way to send a follow-up user message on the same agent

**Answer**: Yes. Manual follow-up is `result.to_input_list()` plus the next user message, passed back into `Runner.run`. Sessions exist as a simpler alternative that avoids calling it yourself.

**Atomic claims**:
  - RunResultBase.to_input_list() produces the inputs for the next turn.
  - Example concatenates to_input_list() with a new user message and calls Runner.run.

**Critical strings**: `to_input_list()`, `Manual conversation management`

### Evidence E1 (verbatim, authoritative)

`ver_2c60e99cfd929a738910b893fd6f1a40` chars 20237–20996 · hash `214f7553a7f42f8058f3ce44460b5df350b9a63e86cf772e429b452c13d3a3b8`

````
#### Manual conversation management

You can manually manage conversation history using the [`RunResultBase.to_input_list()`][agents.result.RunResultBase.to_input_list] method to get the inputs for the next turn:

```python
from agents import Agent, Runner, trace

async def main():
    agent = Agent(name="Assistant", instructions="Reply very concisely.")

    thread_id = "thread_123"  # Example thread ID
    with trace(workflow_name="Conversation", group_id=thread_id):
        # First turn
        result = await Runner.run(agent, "What city is the Golden Gate Bridge in?")
        print(result.final_output)
        # San Francisco

        # Second turn
        new_input = result.to_input_list() + [{"role": "user", "content": "What state is it in?"}]
````

<details><summary>Context before (short)</summary>

```

!!! note

    Session persistence cannot be combined with server-managed conversation settings
    (`conversation_id`, `previous_response_id`, or `auto_previous_response_id`) in the
    same run. Choose one approach per call.

### Conversations/chat threads

Calling any of the run methods can result in one or more agents running (and hence one or more LLM calls), but it represents a single logica…
```

</details>

<details><summary>Context after (short)</summary>

````

        result = await Runner.run(agent, new_input)
        print(result.final_output)
        # California
```

#### Automatic conversation management with sessions

For a simpler approach, you can use [Sessions](sessions/index.md) to automatically handle conversation history without manually calling `.to_input_list()`:

```python
from agents import Agent, Runner, SQLiteSession, trace

async def…
````

</details>

---
## NATQ-C-218

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Model context protocol (MCP)
- **version_id**: `ver_f4be547b9adbe8f607eae8c2422c6985`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/mcp.md
- **section**: Model context protocol (MCP) › Choosing an MCP integration
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> agents sdk MCP, MCPServerStdio vs the streamable http one, which do I use for a remote server

**Answer**: Use `MCPServerStreamableHttp` for a Streamable HTTP server you run locally or remotely. `MCPServerStdio` is for launching a local subprocess over stdin/stdout, not a remote HTTP server.

**Atomic claims**:
  - Streamable HTTP servers run locally or remotely use MCPServerStreamableHttp.
  - stdio / MCPServerStdio is for launching a local process over stdin/stdout.

**Critical strings**: `MCPServerStreamableHttp`, `MCPServerStdio`, `remotely`

### Evidence E1 (verbatim, authoritative)

`ver_f4be547b9adbe8f607eae8c2422c6985` chars 1218–2441 · hash `ec41075b64dd7793bddf73b29d3aa6babb81cc8d4af9fb4818370975ff844de4`

```
## Choosing an MCP integration

Before wiring an MCP server into an agent decide where the tool calls should execute and which transports you can reach. The matrix below summarises the options that the Python SDK supports.

| What you need                                                                        | Recommended option                                    |
| ------------------------------------------------------------------------------------ | ----------------------------------------------------- |
| Let OpenAI's Responses API call a publicly reachable MCP server on the model's behalf| **Hosted MCP server tools** via [`HostedMCPTool`][agents.tool.HostedMCPTool] |
| Connect to Streamable HTTP servers that you run locally or remotely                  | **Streamable HTTP MCP servers** via [`MCPServerStreamableHttp`][agents.mcp.server.MCPServerStreamableHttp] |
| Talk to servers that implement HTTP with Server-Sent Events                          | **HTTP with SSE MCP servers** via [`MCPServerSse`][agents.mcp.server.MCPServerSse] |
| Launch a local process and communicate over stdin/stdout                             | **stdio MCP servers** via [`MCPServerStdio`][agents.mcp.server.MCPServerStdio] |
```

<details><summary>Context before (short)</summary>

```
CP like a USB-C port for AI
> applications. Just as USB-C provides a standardized way to connect your devices to various peripherals and accessories, MCP
> provides a standardized way to connect AI models to different data sources and tools.

The Agents Python SDK understands multiple MCP transports. This lets you reuse existing MCP servers or build your own to expose filesystem, HTTP, or connecto…
```

</details>

<details><summary>Context after (short)</summary>

```


The sections below walk through each option, how to configure it, and when to prefer one transport over another.

## MCP Python SDK v1 and v2

The Agents SDK supports both major versions of the `mcp` Python package through the dependency range `mcp>=1.19.0,<3`. The installed `mcp` package version is separate from the MCP protocol version negotiated with a server. The Agents SDK detects the insta…
```

</details>

---
## NATQ-C-219

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Configuration
- **version_id**: `ver_f15e1a531d680bb98179238f80355058`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/config.md
- **section**: Configuration › API keys and clients
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> can I pass my own OpenAI() client into the agents Runner so our wrapper/base_url is used

**Answer**: Yes, via `set_default_openai_client`. Build an `AsyncOpenAI` (base_url/api_key/wrapper) and pass it in; the SDK uses that client instead of constructing its own. It is a process default, not a per-Runner constructor argument.

**Atomic claims**:
  - By default the SDK creates an AsyncOpenAI instance.
  - set_default_openai_client lets you replace that client.
  - Example constructs AsyncOpenAI(base_url=..., api_key=...) and calls set_default_openai_client.

**Critical strings**: `set_default_openai_client`, `AsyncOpenAI`, `base_url`

### Evidence E1 (verbatim, authoritative)

`ver_f15e1a531d680bb98179238f80355058` chars 2401–2895 · hash `29cb0cd9697430f885bb9971d6ef6b1a427eea8a5eca759a7702f983dfc84a05`

````
Alternatively, you can also configure an OpenAI client to be used. By default, the SDK creates an `AsyncOpenAI` instance, using the API key from the environment variable or the default key set above. You can change this by using the [set_default_openai_client()][agents.set_default_openai_client] function.

```python
from openai import AsyncOpenAI
from agents import set_default_openai_client

custom_client = AsyncOpenAI(base_url="...", api_key="...")
set_default_openai_client(custom_client)
````

<details><summary>Context before (short)</summary>

````
erbosity": "low",
    },
)
```

The SDK normalizes these dictionaries into the corresponding settings objects. Unknown fields in dataclass configuration types defined by the SDK raise `TypeError`, which helps catch misspelled option names early. Check the parameter's type annotation or API reference to confirm whether a specific boundary accepts a dictionary.

## API keys and clients

By default, …
````

</details>

<details><summary>Context after (short)</summary>

````

```

### Custom HTTP clients with `openai` v3

Version 0.21.0 requires `openai>=3.0.0,<4`. The default OpenAI provider uses HTTPX2, so most applications do not need to configure an HTTP client directly. If your application passes `http_client=` to `AsyncOpenAI`, use HTTPX2 types for the custom client and its transport-facing options:

```python
import httpx2
from openai import AsyncOpenAI, Defaul…
````

</details>

---
## NATQ-C-225

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Tools
- **version_id**: `ver_cbeb36b7cf9a5e241940a011629b6f1b`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/tools.md
- **section**: Tools › Function tools
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> @function_tool vs FunctionTool(...) — do I still hand-write the json schema

**Answer**: No for a Python function tool: the SDK builds the JSON schema from the function arguments. Yes if you construct `FunctionTool(...)` yourself — you must supply `params_json_schema`.

**Atomic claims**:
  - For a Python function used as a tool, the schema is automatically created from the function's arguments.
  - Direct FunctionTool construction requires params_json_schema, the JSON schema for the arguments.

**Critical strings**: `schema for the function inputs is automatically created`, `FunctionTool`, `params_json_schema`

### Evidence E1 (verbatim, authoritative)

`ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 19873–20278 · hash `69901301dd7f004a68468d6d48b91505cc0e69e4fd6c87d405760e1a83b4fb29`

```
## Function tools

You can use any Python function as a tool. The Agents SDK will set up the tool automatically:

-   The name of the tool will be the name of the Python function (or you can provide a name)
-   Tool description will be taken from the docstring of the function (or you can provide a description)
-   The schema for the function inputs is automatically created from the function's arguments
```

<details><summary>Context before (short)</summary>

```
): ...
    async def scroll(self, x, y, scroll_x, scroll_y): ...
    async def type(self, text): ...
    async def wait(self): ...
    async def move(self, x, y): ...
    async def keypress(self, keys): ...
    async def drag(self, path): ...


class NoopEditor(ApplyPatchEditor):
    async def create_file(self, op: ApplyPatchOperation): return ApplyPatchResult(status="completed")
    async def upd…
```

</details>

<details><summary>Context after (short)</summary>

```

-   Descriptions for each input are taken from the docstring of the function, unless disabled

Tools created by `@tool` expose the original Python callable through the read-only `__wrapped__` attribute. This is useful for inspection and testing, but calling it directly bypasses the tool runtime pipeline, including schema validation, context injection, guardrails, timeouts, failure handling, and t…
```

</details>

### Evidence E2 (verbatim, authoritative)

`ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 24918–25213 · hash `f25485c3c9570a0aeefd2c70f5c1e126ae1637797ffbe4e4c39f5c98d3745481`

```
### Custom function tools

Sometimes, you don't want to use a Python function as a tool. You can directly create a [`FunctionTool`][agents.tool.FunctionTool] if you prefer. You'll need to provide:

-   `name`
-   `description`
-   `params_json_schema`, which is the JSON schema for the arguments
```

---
## NATQ-C-227

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): either
- **document**: OpenAI Python API library
- **version_id**: `ver_9247e3ce4df6f79d9cadc44e1a3bbd0c`
- **url**: https://github.com/openai/openai-python/blob/10ee3f0da2ac6f93345c1204bd7bb1a2faa79ff2/README.md
- **section**: Or, configure per-request: › Timeouts
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> python sdk timeout default, like 10 minutes? and is that the whole agent/tool loop or just one http call

**Answer**: OpenAI Python SDK: yes, requests time out after 10 minutes by default. That timeout is per HTTP request, not an agent/tool loop spanning multiple calls.

**Atomic claims**:
  - Default request timeout is 10 minutes.
  - The timeout applies to requests (HTTP calls).

**Critical strings**: `10 minutes`, `requests time out`

### Evidence E1 (verbatim, authoritative)

`ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` chars 20462–20521 · hash `640fda9110e335ce2304ebbef6c06cc169dc627eda15aae7b294dc4bb441ba41`

```
## Timeouts

By default requests time out after 10 minutes.
```

<details><summary>Context before (short)</summary>

````
 is a test"}], model="gpt-5.5"
    )
except openai.APIStatusError as exc:
    print(exc.request_id)  # req_123
    raise exc
```

## Retries

Certain errors are automatically retried 2 times by default, with a short exponential backoff.
Connection errors (for example, due to a network connectivity problem), 408 Request Timeout, 409 Conflict,
429 Rate Limit, and >=500 Internal errors are all retrie…
````

</details>

<details><summary>Context after (short)</summary>

````
 You can configure this with a `timeout` option,
which accepts a float or an [`httpx2.Timeout`](https://httpx2.pydantic.dev/) object:

```python
import httpx2
from openai import OpenAI

# Configure the default for all requests:
client = OpenAI(
    # 20 seconds (default is 10 minutes)
    timeout=20.0,
)

# More granular control:
client = OpenAI(
    timeout=httpx2.Timeout(60.0, read=5.0, write=10…
````

</details>

---
