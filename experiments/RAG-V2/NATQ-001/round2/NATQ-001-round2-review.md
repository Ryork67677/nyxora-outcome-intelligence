# NATQ-001 ROUND 2 review packet (16 repaired cases)

**Corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · generated 2026-09-02T18:13:16Z (2026-09-02 14:13 EDT)**

**Header instruction for ChatGPT (coordinator):** The quoted evidence below is authoritative. **Do not consult live docs.** The corpus is frozen snapshot `snap_689e336380a054d8039dc35b2c09cd0a`. Judge each candidate against the quoted evidence and the short context_before/after only.

ROUND 2 repairs only. The other **84 coordinator-PASS** candidates are byte-for-byte unchanged and are **not** repeated here. Do not freeze NATQ-001 yet. Do not run SYSTEM-H. Do not run retrieval. Do not open V1 `holdout.json`.

Questions are preserved byte-for-byte from authoring. Repairs were limited to tightening answers/claims and adding/expanding frozen-snapshot evidence spans. **0 replacements** from the 12 held-out SUPPORT cases.

For each candidate, return verdict `PASS | FAIL | FIX_REQUIRED | UNCERTAIN` against the evidence as written.

---

**This packet:** 16 repaired candidates (`NATQ-C-002` … `NATQ-C-219` as listed).
## NATQ-C-002

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Running agents
- **version_id**: `ver_2c60e99cfd929a738910b893fd6f1a40`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/running_agents.md
- **section**: Running agents › Runner lifecycle and configuration › The agent loop
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`
- **round2_action**: `tightened`

**Question** (byte-for-byte from authoring jsonl)

> runner vs agent in the python agents sdk — which one actually calls the model

**Answer**: The `Runner` agent loop calls the LLM for the current agent.

**Atomic claims**:
  - The runner runs a loop after you call a Runner method with a starting agent.
  - Step 1 of the loop: We call the LLM for the current agent, with the current input.

**Critical strings**: `The runner then runs a loop`, `We call the LLM for the current agent`

### Evidence E1 (verbatim, authoritative)

`ver_2c60e99cfd929a738910b893fd6f1a40` chars 1496–1591 · hash `a8d6b8fb890056326897a6f4497aadd9b4fbed1ef10e45f0ff655e6bb1ed7de4`

```
The runner then runs a loop:

1. We call the LLM for the current agent, with the current input.
```

<details><summary>Context before (short)</summary>

````
s import Agent, Runner

async def main():
    agent = Agent(name="Assistant", instructions="You are a helpful assistant")

    result = await Runner.run(agent, "Write a haiku about recursion in programming.")
    print(result.final_output)
    # Code within the code,
    # Functions calling themselves,
    # Infinite loop's dance
```

Read more in the [results guide](results.md).

## Runner lifecycle and configuratio…
````

</details>

<details><summary>Context after (short)</summary>

```

2. The LLM produces its output.
    1. If the runner classifies the LLM's output as final output, the loop ends and we return the result.
    2. If the LLM requests a handoff, we update the current agent and input, and re-run the loop.
    3. If the LLM produces tool calls, we run those tool calls, append the results, and re-run the loop.
3. If we exceed the `max_turns` passed, we raise a [`MaxTurnsExceeded`][agents…
```

</details>

---
## NATQ-C-005

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Human-in-the-loop
- **version_id**: `ver_ae3bfcc42c733c5051abda30f0f6db07`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/human_in_the_loop.md
- **section**: Human-in-the-loop › Marking tools that need approval
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`
- **round2_action**: `evidence-added`

**Question** (byte-for-byte from authoring jsonl)

> how do I require a human to approve a tool before the agents sdk actually runs it, like delete_user

**Answer**: Mark the tool with `needs_approval=True` (or a per-call callable). The run pauses until a human approves. Example: `@tool(needs_approval=True)`.

**Atomic claims**:
  - Set needs_approval to True to always require approval, or provide an async function that decides per call.
  - The decorator example is @tool(needs_approval=True).

**Critical strings**: `needs_approval`, `True`, `require approval`, `@tool(needs_approval=True)`

### Evidence E1 (verbatim, authoritative)

`ver_ae3bfcc42c733c5051abda30f0f6db07` chars 1327–1436 · hash `72cb1e104a68797ed1296cfed17b04ba519cd1890449a2e5542f4ed36ad4e836`

```
Set `needs_approval` to `True` to always require approval or provide an async function that decides per call.
```

<details><summary>Context before (short)</summary>

```
s when the tool belongs to the current agent, to an agent reached through a handoff, or to a nested [`Agent.as_tool()`][agents.agent.Agent.as_tool] execution. In the nested `Agent.as_tool()` case, the interruption still surfaces on the outer run, so you approve or reject it on the outer `RunState` and resume the original top-level run.

With `Agent.as_tool()`, approvals can happen at two different layers: the agent t…
```

</details>

<details><summary>Context after (short)</summary>

````
 The callable receives the run context, parsed tool parameters, and the tool call ID.

Callable approval rules fail closed when the SDK cannot safely inspect the arguments. If the arguments are malformed JSON, are valid JSON but not an object (for example, `null` or a list), or contain non-standard constants such as `NaN`, `Infinity`, or `-Infinity`, the callable is not invoked and the call requires manual approval.…
````

</details>

### Evidence E2 (verbatim, authoritative)

`ver_ae3bfcc42c733c5051abda30f0f6db07` chars 1919–2104 · hash `1a51dbf80d3510972c2302163ed180d2b3fa18a4d3b4375bca8a8601cccd68c9`

````
```python
from agents import Agent
from agents.decorators import tool


@tool(needs_approval=True)
async def cancel_order(order_id: int) -> str:
    return f"Cancelled order {order_id}"
````

<details><summary>Context before (short)</summary>

```
rts. Both are handled through the same outer-run interruption flow.

This page focuses on the manual approval flow via `interruptions`. If your app can decide in code, some tool types also support programmatic approval callbacks so the run can continue without pausing.

## Marking tools that need approval

Set `needs_approval` to `True` to always require approval or provide an async function that decides per call. Th…
```

</details>

<details><summary>Context after (short)</summary>

````



async def requires_review(_ctx, params, _call_id) -> bool:
    return "refund" in params.get("subject", "").lower()


@tool(needs_approval=requires_review)
async def send_email(subject: str, body: str) -> str:
    return f"Sent '{subject}'"


agent = Agent(
    name="Support agent",
    instructions="Handle tickets and ask for approval when needed.",
    tools=[cancel_order, send_email],
)
```

`needs_approval` is…
````

</details>

---
## NATQ-C-014

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Tools
- **version_id**: `ver_cbeb36b7cf9a5e241940a011629b6f1b`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/tools.md
- **section**: Annotated form › Agents as tools
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`
- **round2_action**: `evidence-added`

**Question** (byte-for-byte from authoring jsonl)

> can I nest an agent as a tool, like one agent calling another as a function

**Answer**: Yes. Model nested agents as tools via `.as_tool()` so one agent calls another as a function instead of a handoff.

**Atomic claims**:
  - A central agent can orchestrate specialized agents instead of handing off control.
  - You do this by modeling agents as tools.
  - The method is Agent.as_tool() (e.g. spanish_agent.as_tool(...)).

**Critical strings**: `agents as tools`, `instead of handing off control`, `as_tool`

### Evidence E1 (verbatim, authoritative)

`ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 31350–31522 · hash `46173393ea157969ac221c5be74b31fb7bfcf0b5e994b1ac6ba3f46fbd6e92e3`

```
In some workflows, you may want a central agent to orchestrate a network of specialized agents, instead of handing off control. You can do this by modeling agents as tools.
```

<details><summary>Context before (short)</summary>

````
tool
from typing import Any

def my_custom_error_function(context: RunContextWrapper[Any], error: Exception) -> str:
    """A custom function to provide a user-friendly error message."""
    print(f"A tool call failed with the following error: {error}")
    return "An internal server error occurred. Please try again later."

@tool(failure_error_function=my_custom_error_function)
def get_user_profile(user_id: str) ->…
````

</details>

<details><summary>Context after (short)</summary>

````


```python
import asyncio

from agents import Agent, Runner

spanish_agent = Agent(
    name="Spanish agent",
    instructions="You translate the user's message to Spanish",
)

french_agent = Agent(
    name="French agent",
    instructions="You translate the user's message to French",
)

orchestrator_agent = Agent(
    name="orchestrator_agent",
    instructions=(
        "You are a translation agent. You use the t…
````

</details>

### Evidence E2 (verbatim, authoritative)

`ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 32058–32393 · hash `c0ca0b574ac24fdf55c409279879cb44dce4555d93a6ce73d71dcc8df790757f`

```
    tools=[
        spanish_agent.as_tool(
            tool_name="translate_to_spanish",
            tool_description="Translate the user's message to Spanish",
        ),
        french_agent.as_tool(
            tool_name="translate_to_french",
            tool_description="Translate the user's message to French",
        ),
    ],
```

<details><summary>Context before (short)</summary>

````
user_id: {user_id}. API returned an error.")

```

If you are manually creating a `FunctionTool` object, then you must handle errors inside the `on_invoke_tool` function.

## Agents as tools

In some workflows, you may want a central agent to orchestrate a network of specialized agents, instead of handing off control. You can do this by modeling agents as tools.

```python
import asyncio

from agents import Agent, Ru…
````

</details>

<details><summary>Context after (short)</summary>

````

)

async def main():
    result = await Runner.run(orchestrator_agent, input="Say 'Hello, how are you?' in Spanish.")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
```

### Customizing tool-agents

`agent.as_tool` is a convenience method for turning an agent into a tool. It supports common runtime options such as `max_turns`, `run_config`, `hooks`, `previous_response_id`, `conve…
````

</details>

---
## NATQ-C-016

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Using the Messages API
- **version_id**: `ver_d7be262221efc52378af14916e203df8`
- **url**: https://platform.claude.com/docs/en/build-with-claude/working-with-messages
- **section**: Multiple conversational turns › System role in messages
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`
- **round2_action**: `tightened`

**Question** (byte-for-byte from authoring jsonl)

> claude messages api, do I still send system as a role in messages or is it the top-level system field

**Answer**: Put start-of-conversation instructions in the top-level `system` field, not as the first `messages` item. Use a mid-conversation system message for instructions that only become relevant later.

**Atomic claims**:
  - A system message cannot be the first entry in messages; use the top-level system field for instructions from the start.
  - Use top-level system for first-turn instructions and a mid-conversation system message for later instructions.

**Critical strings**: `top-level `system` field`, `role": "system"`, `cannot be the first entry`

### Evidence E1 (verbatim, authoritative)

`ver_d7be262221efc52378af14916e203df8` chars 10028–10561 · hash `2c87e048a56535c6a64d46fad90542c91fe8344e734c7b187d4ad8681573a227`

```
A `system` message cannot be the first entry in `messages`; use the top-level `system` field for instructions that apply from the start.

A mid-conversation system message has the same authority as the top-level `system` field, but because it is appended to the end of the message history, it does not invalidate any cached prefix that came before it. Use the top-level `system` field for instructions that should apply from the very first turn, and a mid-conversation system message for instructions that only become relevant later.
```

<details><summary>Context before (short)</summary>

````
"assistant", content: "Hello!" },
      { role: "user", content: "Can you describe LLMs to me?" }
    ]
  )
  puts message
  ```
</CodeGroup>

```json Output
{
  "id": "msg_018gCsTGsXkYJVqYPxTgDHBU",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Sure, I'd be happy to provide..."
    }
  ],
  "model": "claude-opus-5",
  "stop_reason": "end_turn",
  "stop_sequence…
````

</details>

<details><summary>Context after (short)</summary>

```


See [Mid-conversation system messages](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages) for the complete guide, including how to combine it with [prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).

## Prefilling Claude's response

You can pre-fill part of Claude's response in the last position of the input messages list. Use this technique t…
```

</details>

---
## NATQ-C-026

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Citations
- **version_id**: `ver_77dd930ea597c30fc512a8f92f8e802d`
- **url**: https://platform.claude.com/docs/en/build-with-claude/citations
- **section**: Preamble
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`
- **round2_action**: `evidence-added`

**Question** (byte-for-byte from authoring jsonl)

> claude citations / grounded answers — is that a tool or a response format

**Answer**: A document/response feature. Enable with `citations: { enabled: true }` on a `document` block; when citations are enabled, responses include multiple text blocks with citations.

**Atomic claims**:
  - Citations ground responses in source documents and return exact supporting passages.
  - Enabled on a document block via citations.enabled true.
  - When citations are enabled, responses include multiple text blocks with citations.

**Critical strings**: `Citations`, `source documents`, `citations": { "enabled": true }`, `text blocks with citations`

### Evidence E1 (verbatim, authoritative)

`ver_77dd930ea597c30fc512a8f92f8e802d` chars 103–276 · hash `6ac91ad79f18dbbec19d9b779cf16c3a621731cd679f572bfbee678cf2c1360e`

```
Ground Claude's responses in your source documents. Citations return the exact passages that support each claim, so you can verify answers and surface sources to your users.
```

<details><summary>Context before (short)</summary>

```
---
title: Citations
url: https://platform.claude.com/docs/en/build-with-claude/citations
description: 
```

</details>

<details><summary>Context after (short)</summary>

````

---

## Compatibility
- [ZDR](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention): eligible (excludes [Covered Models](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention#model-specific-data-retention-requirements))
- Platforms: Claude API, Claude Platform on AWS, Amazon Bedrock, Google Cloud, Microsoft Foundry

Claude can provide detailed citations when answering questions…
````

</details>

### Evidence E2 (verbatim, authoritative)

`ver_77dd930ea597c30fc512a8f92f8e802d` chars 26711–26743 · hash `4267f2e963523ff0e3359002f395268fa725adeeb54935c7defa9e78a2df4bb2`

```
"citations": { "enabled": true }
```

<details><summary>Context before (short)</summary>

````
message content. Files that are already plain text, such as .csv and .md files, can also be uploaded with an explicit `text/plain` content type. See [Working with other file formats](https://platform.claude.com/docs/en/build-with-claude/files#working-with-other-file-formats).
</Note>

### Plain text documents

Plain text documents are automatically chunked into sentences. You can provide them inline or by reference w…
````

</details>

<details><summary>Context after (short)</summary>

````

    }
    ```
  </Tab>

  <Tab title="Files API">
    <Note>
      Files API document sources are in beta. These examples use the beta client path; see [Files API](https://platform.claude.com/docs/en/build-with-claude/files) for upload details.
    </Note>

    <CodeGroup>
      ```bash cURL
      curl -X POST https://api.anthropic.com/v1/messages \
        -H "x-api-key: $ANTHROPIC_API_KEY" \
        -H "anthropic-…
````

</details>

### Evidence E3 (verbatim, authoritative)

`ver_77dd930ea597c30fc512a8f92f8e802d` chars 72228–72310 · hash `0bc602fb9b0f0fedf4d0fb819a561d4cac8d9eefeb926bb054005053fcbd05b4`

```
When citations are enabled, responses include multiple text blocks with citations:
```

<details><summary>Context before (short)</summary>

````
: {
              type: "content",
              content: [
                { type: "text", text: "First chunk" },
                { type: "text", text: "Second chunk" }
              ]
            },
            title: "Document Title",
            context: "Context about the document that will not be cited from",
            citations: { enabled: true }
          },
          {
            type: "text",…
````

</details>

<details><summary>Context after (short)</summary>

````


```json
{
  "content": [
    { "type": "text", "text": "According to the document, " },
    {
      "type": "text",
      "text": "the grass is green",
      "citations": [
        {
          "type": "char_location",
          "cited_text": "The grass is green.",
          "document_index": 0,
          "document_title": "Example Document",
          "start_char_index": 0,
          "end_char_index": 20
        }…
````

</details>

---
## NATQ-C-030

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Create a Message › Returns
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`
- **round2_action**: `evidence-added`

**Question** (byte-for-byte from authoring jsonl)

> claude stop_reason pause_turn vs end_turn vs tool_use — when do I send the next request to resume

**Answer**: Resume `pause_turn` by sending the response back as-is. `end_turn` is a natural stop (do not resume). `tool_use` means Claude stopped to call your tools — continue by sending client `tool_result` blocks, not by re-sending the response.

**Atomic claims**:
  - end_turn: the model reached a natural stopping point.
  - tool_use: the model invoked one or more tools.
  - pause_turn: paused a long-running turn; provide the response back as-is in a subsequent request to continue.
  - A client tool_use stop is continued by sending client tool_result blocks instead of the response itself.

**Critical strings**: `end_turn`, `tool_use`, `pause_turn`, `as-is`, `tool_result`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 89070–89496 · hash `5ca0f474a72e4e48467b4e7cf30832c0342ebad20d5ad1897311bf3eaf02447c`

```
* `"end_turn"`: the model reached a natural stopping point
    * `"max_tokens"`: we exceeded the requested `max_tokens` or the model's maximum
    * `"stop_sequence"`: one of your provided custom `stop_sequences` was generated
    * `"tool_use"`: the model invoked one or more tools
    * `"pause_turn"`: we paused a long-running turn. You may provide the response back as-is in a subsequent request to let the model continue.
```

<details><summary>Context before (short)</summary>

```
s://www.anthropic.com/legal/commercial-terms). Benign machine learning work can also trigger this category.

      - `"reasoning_extraction"`

        The request asks the model to reproduce its internal reasoning in the response text. To get reasoning in a structured form instead, use [adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking).

      - `"general_harms"`

        The…
```

</details>

<details><summary>Context after (short)</summary>

```

    * `"refusal"`: when streaming classifiers intervene to handle potential policy violations
    * `"model_context_window_exceeded"`: we exceeded the model's context window

    In non-streaming mode this value is always non-null. In streaming mode, it is null in the `message_start` event and non-null otherwise.

    - `"end_turn"`

    - `"max_tokens"`

    - `"stop_sequence"`

    - `"tool_use"`

    - `"pause_tu…
```

</details>

### Evidence E2 (verbatim, authoritative)

**source document**: Stop reasons and fallback  ·  https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons

`ver_4d14aec24504f4b8f6f28938b84587dc` chars 52326–52682 · hash `8be5b8fd12ab9bb59b140f264e0a1b5000b7575f9e65401fa32119b14290c750`

```
A response that leaves a client `tool_use` block waiting on you never has a `stop_reason` of `pause_turn`: when Claude stops to call your tools, `stop_reason` is [`tool_use`](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons#tool-use), and you continue it by sending the client `tool_result` blocks instead of the response itself.
```

<details><summary>Context before (short)</summary>

````
ver tool:

```text wrap
`web_search` tool use with id `srvtoolu_01HxbWnMRmbWyMfUtJKC45rA` was found without a corresponding `web_search_tool_result` block
```

Leaving out a `tool_result`, or putting one after other content, fails earlier with the standard `tool_use ids were found without tool_result blocks immediately after` error instead. To give Claude more input, send it as a separate user message after the turn…
````

</details>

<details><summary>Context after (short)</summary>

````


<CodeGroup>
  ```bash cURL
  # The SDKs handle continuation directly. With cURL, inspect stop_reason
  # on the response and re-POST with the assistant content appended.
  curl https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d '{
      "model": "claude-opus-5",
      "max_tokens": 4096,
      "to…
````

</details>

---
## NATQ-C-044

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Bash tool
- **version_id**: `ver_9bf8513721dc2d1ef3e1ec42bf535dc6`
- **url**: https://platform.claude.com/docs/en/agents-and-tools/tool-use/bash-tool
- **section**: Tool versions
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`
- **round2_action**: `evidence-added`

**Question** (byte-for-byte from authoring jsonl)

> anthropic bash tool and text editor tool — are those built-in types or do I implement them

**Answer**: Built-in tool types you declare (`bash_20250124` and `text_editor_20250728`), but you still implement the client loop. For bash, your application runs the command after Claude returns `tool_use`. For text editor, the schema is built into the model (`type: "text_editor_20250728"`) and you implement file operations.

**Atomic claims**:
  - bash_20250124 is the current built-in bash tool type and requires no beta header.
  - Your application runs the command in its bash session after Claude returns tool_use.
  - The text editor tool is a schema-less built-in; type is text_editor_20250728 for Claude 4 and later.
  - You implement the text editor by handling file operations / editor tool calls yourself.

**Critical strings**: `bash_20250124`, `Your application runs the command`, `tool_use`, `text_editor_20250728`, `schema-less tool`

### Evidence E1 (verbatim, authoritative)

`ver_9bf8513721dc2d1ef3e1ec42bf535dc6` chars 8308–8391 · hash `0fb5b2b6b9540ce984d156f3ac858414d8c391031619c12914705f617e95273b`

```
`bash_20250124` is the current version of the tool, and it requires no beta header.
```

<details><summary>Context before (short)</summary>

````
the schema is built into Claude's model and can't be modified. The following table lists the input fields Claude sets when it calls the tool.

| Parameter | Required | Description                               |
| --------- | -------- | ----------------------------------------- |
| `command` | Yes\*    | The bash command to run                   |
| `restart` | No       | Set to `true` to restart the bash session |…
````

</details>

<details><summary>Context after (short)</summary>

````
 Every model from Claude Sonnet 3.7 ([retired](https://platform.claude.com/docs/en/about-claude/model-deprecations)) onward accepts it, including all current Claude models.

The original `bash_20241022` version is part of the computer use beta, and the October 2024 Claude Sonnet 3.5 release ([retired](https://platform.claude.com/docs/en/about-claude/model-deprecations)) is the only model that accepts it. Requests tha…
````

</details>

### Evidence E2 (verbatim, authoritative)

`ver_9bf8513721dc2d1ef3e1ec42bf535dc6` chars 6308–6435 · hash `b3d65e6e4717b3cef5e087ab1c9dd9708cc2fb1962a23ceeb663c905a0813c3c`

```
1. Claude returns a `tool_use` block containing the `command` to run.
2. Your application runs the command in its bash session.
```

<details><summary>Context before (short)</summary>

````
```
</CodeGroup>

Claude responds with `stop_reason: "tool_use"` and a `tool_use` block that contains the command for your application to run:

```json Output
{
  "id": "msg_01XAbCDeFgHiJkLmNoPQrStU",
  "model": "claude-opus-5",
  "stop_reason": "tool_use",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I'll list all Python files in the current directory for you."
    },
    {…
````

</details>

<details><summary>Context after (short)</summary>

```

3. Your application returns the command's output, stdout and stderr together, to Claude in a `tool_result` block.
4. Claude either requests another command in the same session or responds with text.

Claude can also return several `tool_use` blocks in one response. Run them in order in the same session and return all of the results in one `user` message. See [Parallel tool use](https://platform.claude.com/docs/en/ag…
```

</details>

### Evidence E3 (verbatim, authoritative)

**source document**: Text editor tool  ·  https://platform.claude.com/docs/en/agents-and-tools/tool-use/text-editor-tool

`ver_72833144cee232446fa450e9e040995a` chars 53515–53836 · hash `abc0fd6f5e0087734ce8b2eb42a90f2b99ac261dd391391ba55dd2e845dfa293`

```
## Implement the text editor tool

The text editor tool is implemented as a schema-less tool. When using this tool, you don't need to provide an input schema as with other tools; the schema is built into Claude's model and can't be modified.

The tool type is `type: "text_editor_20250728"` for Claude 4 and later models.
```

<details><summary>Context before (short)</summary>

````


````json Output
{
  "id": "msg_01IjKlMnOpQrStUvWxYzAb",
  "model": "claude-opus-5",
  "stop_reason": "end_turn",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I've fixed the syntax error in your primes.py file. The issue was in the `get_primes` function at line 19. There was a missing colon (:) at the end of the for loop line.\n\nHere's what I changed:\n\nFrom:\n```python\nfor num…
````

</details>

<details><summary>Context after (short)</summary>

````


<Steps>
  <Step title="Initialize your editor implementation">
    Create helper functions to handle file operations like reading, writing, and modifying files. Consider implementing backup functionality to recover from mistakes.
  </Step>

  <Step title="Handle editor tool calls">
    Create a function that processes tool calls from Claude based on the command type:

    <CodeGroup exclude="shell">
      ```python…
````

</details>

---
## NATQ-C-047

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Tools
- **version_id**: `ver_cbeb36b7cf9a5e241940a011629b6f1b`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/tools.md
- **section**: Tools › Hosted tools
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`
- **round2_action**: `evidence-added`

**Question** (byte-for-byte from authoring jsonl)

> agents sdk hosted tools like web search, do I still implement an on_invoke callback

**Answer**: No. Hosted tools like `WebSearchTool` are OpenAI-managed built-ins that execute for the model on OpenAI servers. `on_invoke_tool` is the async callback you provide when creating a custom `FunctionTool`.

**Atomic claims**:
  - OpenAI offers built-in hosted tools when using OpenAIResponsesModel.
  - WebSearchTool lets an agent search the web.
  - Hosted OpenAI tools execute for the model on OpenAI servers.
  - When you create a FunctionTool you must provide on_invoke_tool.

**Critical strings**: `built-in tools`, `WebSearchTool`, `OpenAI servers`, `on_invoke_tool`, `FunctionTool`

### Evidence E1 (verbatim, authoritative)

`ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 1524–1736 · hash `e09902a49d7762d5f509b1ee1cff7803a0491c191aa770b30c572688d38f0934`

```
OpenAI offers a few built-in tools when using the [`OpenAIResponsesModel`][agents.models.openai_responses.OpenAIResponsesModel]:

-   The [`WebSearchTool`][agents.tool.WebSearchTool] lets an agent search the web.
```

<details><summary>Context before (short)</summary>

```
# Choosing a tool type

Use this page as a catalog, then jump to the section that matches the runtime you control.

| If you want to... | Start here |
| --- | --- |
| Use OpenAI-managed tools (web search, file search, code interpreter, hosted MCP, image generation) | [Hosted tools](#hosted-tools) |
| Defer large tool surfaces until runtime with tool search | [Hosted tool search](#hosted-tool-search) |
| Coordinate se…
```

</details>

<details><summary>Context after (short)</summary>

```

-   The [`FileSearchTool`][agents.tool.FileSearchTool] allows retrieving information from your OpenAI Vector Stores.
-   The [`CodeInterpreterTool`][agents.tool.CodeInterpreterTool] lets the LLM execute code in a sandboxed environment.
-   The [`HostedMCPTool`][agents.tool.HostedMCPTool] exposes a remote MCP server's tools to the model.
-   The [`ImageGenerationTool`][agents.tool.ImageGenerationTool] generates image…
```

</details>

### Evidence E2 (verbatim, authoritative)

`ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 170–231 · hash `6081c6c824a23a2130f34634e7d8a16e4679f983115bdc47dfdb14ccf9ffa725`

```
Hosted OpenAI tools: execute for the model on OpenAI servers.
```

<details><summary>Context before (short)</summary>

```
# Tools

Tools let agents take actions: things like fetching data, running code, calling external APIs, and even using a computer. The SDK supports five categories:

-   
```

</details>

<details><summary>Context after (short)</summary>

```

-   Local/runtime execution tools: `ComputerTool` and `ApplyPatchTool` always run in your environment, while `ShellTool` can run locally or in a hosted container.
-   `FunctionTool` instances: wrap any Python function as a tool.
-   Agents as tools: expose an agent as a callable tool without a full handoff.
-   Experimental: Codex tool: run workspace-scoped Codex tasks from a tool call.

## Choosing a tool type

Use…
```

</details>

### Evidence E3 (verbatim, authoritative)

`ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 24918–25462 · hash `e7504a65ab00badf914ebc7a1739f903aa9300c1e5e93a1e7d899e9775d4bc12`

```
### Custom function tools

Sometimes, you don't want to use a Python function as a tool. You can directly create a [`FunctionTool`][agents.tool.FunctionTool] if you prefer. You'll need to provide:

-   `name`
-   `description`
-   `params_json_schema`, which is the JSON schema for the arguments
-   `on_invoke_tool`, which is an async function that receives a [`ToolContext`][agents.tool_context.ToolContext] and the arguments as a JSON string, and returns tool output (for example, text, structured tool output objects, or a list of outputs).
```

<details><summary>Context before (short)</summary>

````
cription": "The directory to read the file from.",
        "title": "Directory"
      }
    },
    "required": [
      "path"
    ],
    "title": "fetch_data_args",
    "type": "object"
    }
    ```

### Returning images or files from function tools

In addition to returning text outputs, you can return one or many images or files as the output of a function tool. To do so, you can return any of:

-   Images: [`Tool…
````

</details>

<details><summary>Context after (short)</summary>

````


```python
from typing import Any

from pydantic import BaseModel

from agents import RunContextWrapper, FunctionTool



def do_some_work(data: str) -> str:
    return "done"


class FunctionArgs(BaseModel):
    username: str
    age: int


async def run_function(ctx: RunContextWrapper[Any], args: str) -> str:
    parsed = FunctionArgs.model_validate_json(args)
    return do_some_work(data=f"{parsed.username} is {pa…
````

</details>

---
## NATQ-C-120

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Models
- **version_id**: `ver_ae909bf8b4bbbe1d1a11119447f7ac94`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/models/index.md
- **section**: Models › Advanced OpenAI Responses settings › Common advanced `ModelSettings` options
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`
- **round2_action**: `tightened`

**Question** (byte-for-byte from authoring jsonl)

> prompt caching on openai — automatic prefix cache or do I mark breakpoints like claude

**Answer**: On the OpenAI Responses path you choose via `prompt_cache_options`: implicit or explicit prompt caching, and for GPT-5.6 you can configure a `"30m"` cache TTL.

**Atomic claims**:
  - prompt_cache_options selects implicit or explicit prompt caching.
  - For GPT-5.6 you can also configure a 30m cache TTL.

**Critical strings**: `prompt_cache_options`, `implicit or explicit prompt caching`, `30m`

### Evidence E1 (verbatim, authoritative)

`ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 26913–27028 · hash `ba08ea5675f68fc543ecd4405c245ed545e5820638a4c93ce3a0cc898c71cdd4`

```
`prompt_cache_options`: Select implicit or explicit prompt caching and, for GPT-5.6, configure a `"30m"` cache TTL.
```

<details><summary>Context before (short)</summary>

```
## Common advanced `ModelSettings` options

When you are using the OpenAI Responses API, several request fields already have direct `ModelSettings` fields, so you do not need `extra_args` for them.

- `parallel_tool_calls`: Allow or forbid multiple tool calls in the same turn.
- `truncation`: Set `"auto"` to let the Responses API drop the oldest conversation items instead of failing when context would overflow.
- `st…
```

</details>

<details><summary>Context after (short)</summary>

````

- `response_include`: Request richer response payloads such as `web_search_call.action.sources`, `file_search_call.results`, or `reasoning.encrypted_content`.
- `top_logprobs`: Request top-token logprobs for output text. The SDK also adds `message.output_text.logprobs` automatically.
- `retry`: Opt in to runner-managed retry settings for model calls. See [Runner-managed retries](#runner-managed-retries).

```python…
````

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
- **round2_action**: `tightened`

**Question** (byte-for-byte from authoring jsonl)

> does claude drop old tool results if I turn on context editing / compaction beta

**Answer**: Yes, if you enable context editing (beta header `context-management-2025-06-27`) with `clear_tool_uses_20250919`. The API then automatically clears the oldest tool results past the threshold and replaces them with placeholder text.

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
| **Client-side** | SDK           | Compaction…
```

</details>

<details><summary>Context after (short)</summary>

```
 By default, only tool results are cleared. You can optionally clear both tool results and tool calls (the tool use parameters) by setting `clear_tool_inputs` to true.

### Thinking block clearing

The `clear_thinking_20251015` strategy manages `thinking` blocks in conversations when extended thinking is enabled. This strategy gives you control over thinking preservation: you can choose to keep more thinking blocks t…
```

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
- **round2_action**: `evidence-added`

**Question** (byte-for-byte from authoring jsonl)

> anthropic web search, what type string goes in the tools array

**Answer**: Put a versioned web-search tool in `tools` with `name` `web_search` and `type` `web_search_20260209` (the same schema also documents `web_search_20250305`).

**Atomic claims**:
  - The web search tool name is web_search.
  - The tools-array type string for the current schema is web_search_20260209.
  - The same Messages schema also documents type web_search_20250305.

**Critical strings**: `web_search`, `web_search_20260209`, `web_search_20250305`

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

    Parameters for the user's location. Used to provide more r…
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

    If provided, only these domains will be included in results. Cannot be used alongside `blocked_d…
```

</details>

### Evidence E2 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 571471–571790 · hash `bffee40a6f1596816b97f8ec4b39801e30c695ce432d7650971bc872bbda8254`

```
### Web Search Tool 20250305

- `WebSearchTool20250305 object { name, type, allowed_callers, 7 more }`

  - `name: "web_search"`

    Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks.

    - `"web_search"`

  - `type: "web_search_20250305"`

    - `"web_search_20250305"`
```

<details><summary>Context before (short)</summary>

```
ltErrorCode = "invalid_tool_input" or "url_too_long" or "url_not_allowed" or 6 more`

  - `"invalid_tool_input"`

  - `"url_too_long"`

  - `"url_not_allowed"`

  - `"url_not_in_prior_context"`

  - `"url_not_accessible"`

  - `"unsupported_content_type"`

  - `"too_many_requests"`

  - `"max_uses_exceeded"`

  - `"unavailable"`

### Web Search Result Block

- `WebSearchResultBlock object { encrypted_content, page_ag…
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

    If provided, only these domains will be included in results. Cannot be used alongside `blocked_d…
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
- **round2_action**: `evidence-added`

**Question** (byte-for-byte from authoring jsonl)

> anthropic files api — do I reference a file_id in the document block or still inline the pdf

**Answer**: In the Files API, a `document` block references a previously uploaded file via `source: { "type": "file", "file_id": ... }` rather than inlining PDF bytes. The beta schema names that shape `BetaFileDocumentSource` (`file_id`, `type: "file"`).

**Atomic claims**:
  - Files API document blocks use source type file plus file_id for PDFs and text files.
  - BetaFileDocumentSource has file_id and type file.

**Critical strings**: `file_id`, `"file"`, `Beta File Document Source`, `"type": "document"`

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

      - `BetaThinkingConfigAdaptive object { type, display…
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

      - `media_type…
```

</details>

### Evidence E2 (verbatim, authoritative)

**source document**: Files API  ·  https://platform.claude.com/docs/en/build-with-claude/files

`ver_ab9e2c2bf4c17bf70ce1b94355d01729` chars 14340–14707 · hash `0c9916ccfecc120a473943fe5d31f01b78e2f86da93b9a052f77382b7f08e785`

````
#### Document blocks

For PDFs and text files, use the `document` content block:

```json
{
  "type": "document",
  "source": {
    "type": "file",
    "file_id": "file_011CNha8iCJcU1wXNR6q4V8w"
  },
  "title": "Document Title", // Optional
  "context": "Context about the document", // Optional
  "citations": { "enabled": true } // Optional, enables citations
}
```
````

<details><summary>Context before (short)</summary>

```
                     | `application/pdf`                                    | `document`         | Text analysis, document processing  |
| Plain text                                                                                                                              | `text/plain`                                         | `document`         | Text analysis, processing           |
| Images…
```

</details>

<details><summary>Context after (short)</summary>

````


#### Image blocks

For images, use the `image` content block:

```json
{
  "type": "image",
  "source": {
    "type": "file",
    "file_id": "file_011CPMxVD3fHLUhvTqtsQA5w"
  }
}
```

#### Container upload blocks

To send a file to the [code execution tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool#upload-and-analyze-your-own-files), use the `container_upload` content block:…
````

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
- **round2_action**: `evidence-added`

**Question** (byte-for-byte from authoring jsonl)

> streaming tool args on claude, is it input_json_delta or a content_block_delta with partial_json

**Answer**: Tool-argument streaming is a `content_block_delta` (`RawContentBlockDeltaEvent`) whose `delta` is `InputJSONDelta` with `type: "input_json_delta"` and a `partial_json` string — not a separate top-level `input_json_delta` SSE event name.

**Atomic claims**:
  - RawContentBlockDeltaEvent carries a delta that can be InputJSONDelta.
  - InputJSONDelta has partial_json and type input_json_delta.
  - The outer SSE event name is content_block_delta (event: content_block_delta).

**Critical strings**: `Raw Content Block Delta Event`, `input_json_delta`, `partial_json`, `event: content_block_delta`

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

      The incremental `thinking` text for this content block. Concatenate the `thinking` values of successive `thinking_delta` events to assembl…
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

          - `end_char_index: number`…
```

</details>

### Evidence E2 (verbatim, authoritative)

**source document**: Streaming messages  ·  https://platform.claude.com/docs/en/build-with-claude/streaming

`ver_1261879c16f641270789647ac9c63c96` chars 10893–11760 · hash `d08e64bde91aa1cb1865fea87dfc9a76c8411ba41d875e56f67fba77642016ae`

````
### Input JSON delta

The deltas for `tool_use` content blocks correspond to updates for the `input` field of the block. To support maximum granularity, the deltas are *partial JSON strings*, whereas the final `tool_use.input` is always an *object*.

You can accumulate the string deltas and parse the JSON once you receive a `content_block_stop` event, by using a library like [Pydantic](https://docs.pydantic.dev/latest/concepts/json/#partial-json-parsing) to do partial JSON parsing, or by using the [SDKs](https://platform.claude.com/docs/en/cli-sdks-libraries/overview), which provide helpers to access parsed incremental values.

A `tool_use` content block delta looks like:

```sse Input JSON delta
event: content_block_delta
data: {"type": "content_block_delta","index": 1,"delta": {"type": "input_json_delta","partial_json": "{\"location\": \"San Fra"}}}
```
````

<details><summary>Context before (short)</summary>

````
.claude.com/docs/en/api/errors) in the event stream. For example, during periods of high usage, you may receive an `overloaded_error`, which would normally correspond to an HTTP 529 in a non-streaming context:

```sse Example error
event: error
data: {"type": "error", "error": {"type": "overloaded_error", "message": "Overloaded"}}
```

### Other events

In accordance with the [versioning policy](https://platform.clau…
````

</details>

<details><summary>Context after (short)</summary>

```


Note: Current models only support emitting one complete key and value property from `input` at a time. As such, when using tools, there may be delays between streaming events while the model is working. Once an `input` key and value are accumulated, they are emitted as multiple `content_block_delta` events with chunked partial JSON so that the format can automatically support finer granularity in future models.

##…
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
- **round2_action**: `tightened`

**Question** (byte-for-byte from authoring jsonl)

> anthropic-organization or anthropic-workspace header, does that exist

**Answer**: The documented header names here are `anthropic-organization-id` and `anthropic-workspace-id`. `anthropic-organization-id` is a response header (organization of the API key or access token); `anthropic-workspace-id` is a request header used to target a workspace on Claude Platform on AWS.

**Atomic claims**:
  - anthropic-organization-id is a documented response header identifying the organization of the API key or token.
  - anthropic-workspace-id is a request header used to target a workspace on Claude Platform on AWS.
  - The documented header names here are anthropic-organization-id and anthropic-workspace-id.

**Critical strings**: `anthropic-organization-id`, `anthropic-workspace-id`

### Evidence E1 (verbatim, authoritative)

`ver_6cbca1c2343b84b7d5cf99029456cfa2` chars 12322–12443 · hash `023ee059d163c56697c87ca32d5e7326d8ae8e7b3f3f15eadd221a3a84b78f5c`

```
`anthropic-organization-id` | The ID of the organization that the API key or access token used in the request belongs to.
```

<details><summary>Context before (short)</summary>

```
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `request-id`                | A globally unique identifier for the request, such as `req_018EeWyXxfu5pfWkrYcMdjWG`. Includ…
```

</details>

<details><summary>Context after (short)</summary>

```
…
```

</details>

### Evidence E2 (verbatim, authoritative)

**source document**: Claude Platform on AWS  ·  https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws

`ver_5ebdc722f9bedb1e2e8cbd3f29ff6805` chars 48160–48339 · hash `1824b8420b2c3c818c721edf04ed2bd3b1a012e81d18b4da21807690e3b08c65`

```
## Workspaces

Inference and resource requests on Claude Platform on AWS target a workspace. You pass the workspace's ID in the `anthropic-workspace-id` header on these API calls.
```

<details><summary>Context before (short)</summary>

````

  $message = $client->messages->create(
      model: 'claude-sonnet-5',
      maxTokens: 1024,
      inferenceGeo: 'us',
      messages: [['role' => 'user', 'content' => 'Hello!']],
  );

  echo $message;
  ```

  ```ruby Ruby
  require "anthropic"

  client = Anthropic::AWSClient.new

  message = client.messages.create(
    model: "claude-sonnet-5",
    max_tokens: 1024,
    inference_geo: "us",
    messages: [{ ro…
````

</details>

<details><summary>Context after (short)</summary>

````
 Workspace IDs use the tagged format `wrkspc_` followed by an alphanumeric identifier (for example, `wrkspc_01AbCdEf23GhIj`). See [Obtain your workspace ID](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws#obtain-your-workspace-id) if you don't have it yet.

### Workspace scoping

Workspaces are bound to a single AWS region. A workspace created in `us-west-2` can only be accessed through t…
````

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
- **round2_action**: `tightened`

**Question** (byte-for-byte from authoring jsonl)

> can I pass my own OpenAI() client into the agents Runner so our wrapper/base_url is used

**Answer**: Yes, via `set_default_openai_client`. Build an `AsyncOpenAI` (`base_url` / `api_key` / wrapper) and pass it in; the SDK uses that client instead of constructing its own.

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

By default, the SDK uses the `OP…
````

</details>

<details><summary>Context after (short)</summary>

````

```

### Custom HTTP clients with `openai` v3

Version 0.21.0 requires `openai>=3.0.0,<4`. The default OpenAI provider uses HTTPX2, so most applications do not need to configure an HTTP client directly. If your application passes `http_client=` to `AsyncOpenAI`, use HTTPX2 types for the custom client and its transport-facing options:

```python
import httpx2
from openai import AsyncOpenAI, DefaultAsyncHttpx2Client…
````

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
- **round2_action**: `evidence-added`

**Question** (byte-for-byte from authoring jsonl)

> does haiku even support computer use or is that sonnet/opus only

**Answer**: Haiku 4.5 does support computer use. The current `computer-use-2025-11-24` supported-models list is opus/sonnet IDs (`claude-opus-5`, `claude-sonnet-5`, `claude-opus-4-8`, `claude-opus-4-7`, `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-opus-4-5-20251101`). A note on the same page says Claude Haiku 4.5 (with Claude Sonnet 4.5, Claude Opus 4.1, Claude Sonnet 4, and Claude Opus 4) uses the earlier `computer-use-2025-01-24` beta header instead of `computer-use-2025-11-24`.

**Atomic claims**:
  - Computer use is beta; the current beta header is computer-use-2025-11-24.
  - The supported-models list for that header is opus/sonnet IDs (no haiku id in that list).
  - On Claude Sonnet 4.5, Claude Haiku 4.5, Claude Opus 4.1, Claude Sonnet 4, and Claude Opus 4, use the earlier computer-use-2025-01-24 beta header instead.

**Critical strings**: `Supported models:`, `claude-sonnet-5`, `claude-opus-5`, `Claude Haiku 4.5`, `computer-use-2025-01-24`

### Evidence E1 (verbatim, authoritative)

`ver_d9ba3ab0d872dd86047c7ed6dc783235` chars 237–1792 · hash `28ffa05ae6d5e2832f83c7ea9f3f5fd17955593bcdfb6f1ce0828ed85c227bde`

```
## Compatibility
- Status: Beta
- [Beta header](https://platform.claude.com/docs/en/api/beta-headers): `computer-use-2025-11-24`
- [ZDR](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention): eligible (excludes [Covered Models](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention#model-specific-data-retention-requirements))
- Supported models: `claude-opus-5`, `claude-sonnet-5`, `claude-opus-4-8`, `claude-opus-4-7`, `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-opus-4-5-20251101`
- Platforms: Claude API (beta), Claude Platform on AWS (beta), Amazon Bedrock (beta), Google Cloud (beta), Microsoft Foundry (beta)

Claude can interact with computer environments through the computer use tool, which provides screenshot capabilities and mouse/keyboard control for autonomous desktop interaction.

<Note>
  On Claude Sonnet 4.5, Claude Haiku 4.5, Claude Opus 4.1 ([retired, except on Bedrock and Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations)), Claude Sonnet 4 ([retired, except on Bedrock and Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations)), and Claude Opus 4 ([retired, except on Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations)), use the earlier `computer-use-2025-01-24` [beta header](https://platform.claude.com/docs/en/api/beta-headers) instead of `computer-use-2025-11-24`.

  Reach out through the [feedback form](https://forms.gle/H6UFuXaaLywri9hz6) to share your feedback on this feature.
</Note>
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


## Overview

Computer use is a beta feature that enables Claude to interact with desktop environments. This tool provides:

* **Screenshot capture:** See what's currently displayed on screen
* **Mouse control:** Click, drag, and move the cursor
* **Keyboard input:** Type text and use keyboard shortcuts
* **Desktop automation:** Interact with any application or interface

While computer use can be augmented with oth…
```

</details>

---

**STOP:** Do not freeze. Do not evaluate SYSTEM-H. Coordinator review of these 16 only.
