# Gold review batch 002

**18 candidates · corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · generated 2026-08-20T06:32:52Z**

Nothing in this file is ground truth. Every candidate is `candidate_unverified`. The evidence below is quoted verbatim from the frozen corpus and is authoritative for this review — **do not consult live documentation**, which may have changed since the snapshot.

For each candidate, judge the *proposed* question, answer and claims against the evidence and its surrounding context, and return the verdict schema in `docs/GOLD-REVIEW-PROCEDURE.md`.

---

## GOLD-B002-01

- **provider**: anthropic
- **document**: Context editing
- **section**: Client-side compaction (SDK) › Configuration options
- **source span**: `ver_1c53b961e1f5da8124a1e7e8eb92c941` chars 83548–83766
- **evidence kind**: `parameter_table_row`
- **binding**: structural: parameter is the row's first cell, requiredness is column 2 of the same row
- **generator confidence**: high
- **needs human interpretation**: False

**Proposed question** (a suggestion, not gold)

> Is the `summary_prompt` parameter required?

**Proposed answer**: No, it is optional.

**Proposed atomic claims**: `` `summary_prompt` is optional. ``

**Generator notes**: Row-scoped association, so the state cannot belong to a different parameter. Reviewer should confirm the table is a parameter table and that the column header means what it appears to mean.

### Evidence (verbatim, authoritative)

```
| `summary_prompt`          | string  | No       | See [Default summary prompt](https://platform.claude.com/docs/en/build-with-claude/context-editing#default-summary-prompt) | Custom prompt for summary generation     |
```

<details><summary>Context before</summary>

```
                      |
| ------------------------- | ------- | -------- | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `enabled`                 | boolean | Yes      | -                                                                                                                          | Whether to enable automatic compaction   |
| `context_token_threshold` | number  | No       | 100,000                                                                                                                    | Token count at which compaction triggers |
| `model`                   | string  | No       | Same as main model                                                                                                         | Model to use for generating summaries    |

```

</details>

<details><summary>Context after</summary>

```


#### Choosing a token threshold

The threshold determines when compaction occurs. A lower threshold means more frequent compactions with smaller context windows. A higher threshold allows more context but risks hitting limits.

<Tabs>
  <Tab title="cURL">
    <Note>
      Compaction runs client-side in the SDK `tool_runner` helpers, so it has no direct HTTP equivalent. Use [server-side compaction](https://platform.claude.com/docs/en/build-with-claude/compaction) instead, which handles compaction on Anthropic's servers.
    </Note>
  </Tab>

  <Tab title="CLI">
    <Note>
      The CLI does not include a `tool_runner` helper. Use [server-side compaction](https://platform.claude.com/docs/en/build-with-claude/compaction) instead, which handles compaction on Anthropic's servers without SDK-side integration.
    </Note>
  </Tab>

  <Tab title="Python">
    ```python Python
    client = anth
```

</details>

---

## GOLD-B002-02

- **provider**: anthropic
- **document**: MCP connector
- **section**: MCP server configuration › Field descriptions
- **source span**: `ver_279d37a3a0cc4e8a9209e01f16f9df88` chars 11319–11677
- **evidence kind**: `parameter_table_row`
- **binding**: structural: parameter is the row's first cell, requiredness is column 2 of the same row
- **generator confidence**: high
- **needs human interpretation**: False

**Proposed question** (a suggestion, not gold)

> Is the `url` parameter required?

**Proposed answer**: Yes, it is required.

**Proposed atomic claims**: `` `url` is required. ``

**Generator notes**: Row-scoped association, so the state cannot belong to a different parameter. Reviewer should confirm the table is a parameter table and that the column header means what it appears to mean.

### Evidence (verbatim, authoritative)

```
| `url`                 | string | Yes      | The URL of the MCP server. Must start with https\://.                                                                                                                                                                                                                                                                  |
```

<details><summary>Context before</summary>

```
                                                                                                                                                                                    |
| --------------------- | ------ | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `type`                | string | Yes      | Currently only "url" is supported.                                                                                                                                                                                                                                                                                     |

```

</details>

<details><summary>Context after</summary>

```

| `name`                | string | Yes      | A unique identifier for this MCP server. Must be referenced by exactly one MCPToolset in the `tools` array.                                                                                                                                                                                                            |
| `authorization_token` | string | No       | OAuth authorization token if required by the MCP server. See [Authentication](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector#authentication) for how to obtain one, or the [MCP specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) for protocol details. |

## MCP toolset configuration

The MCPToolset lives in the `tools` array and configures which tools from the MCP server are enabled and how they should be configured.

### Basic str
```

</details>

---

## GOLD-B002-03

- **provider**: openai
- **document**: Agents
- **section**: Agents › Basic configuration
- **source span**: `ver_35cac5e98c151a17f941a6142d74709f` chars 2057–2208
- **evidence kind**: `parameter_table_row`
- **binding**: structural: parameter is the row's first cell, requiredness is column 1 of the same row
- **generator confidence**: high
- **needs human interpretation**: False

**Proposed question** (a suggestion, not gold)

> Is the `prompt` parameter required?

**Proposed answer**: No, it is optional.

**Proposed atomic claims**: `` `prompt` is optional. ``

**Generator notes**: Row-scoped association, so the state cannot belong to a different parameter. Reviewer should confirm the table is a parameter table and that the column header means what it appears to mean.

### Evidence (verbatim, authoritative)

```
| `prompt` | no | OpenAI Responses API prompt configuration. Accepts a static prompt object or a function. See [Prompt templates](#prompt-templates). |
```

<details><summary>Context before</summary>

```
s to the agent | [Tools](tools.md) |
| Run an agent against a real repo, document bundle, or isolated workspace | [Sandbox agents quickstart](sandbox_agents.md) |
| Decide between manager-style orchestration and handoffs | [Agent orchestration](multi_agent.md) |
| Configure handoff behavior | [Handoffs](handoffs.md) |
| Run turns, stream events, or manage conversation state | [Running agents](running_agents.md) |
| Inspect final output, run items, or resumable state | [Results](results.md) |
| Share local dependencies and runtime state | [Context management](context.md) |

## Basic configuration

The most common properties of an agent are:

| Property | Required | Description |
| --- | --- | --- |
| `name` | yes | Human-readable agent name. |
| `instructions` | no | System prompt or dynamic instructions callback. Strongly recommended. See [Dynamic instructions](#dynamic-instructions). |

```

</details>

<details><summary>Context after</summary>

```

| `handoff_description` | no | Short description exposed when this agent is offered as a handoff target. |
| `handoffs` | no | Delegate the conversation to specialist agents. See [handoffs](handoffs.md). |
| `model` | no | Which LLM to use. See [Models](models/index.md). |
| `model_settings` | no | Model tuning parameters such as `temperature`, `top_p`, and `tool_choice`. |
| `tools` | no | Tools the agent can call. See [Tools](tools.md). |
| `mcp_servers` | no | MCP servers that provide MCP-backed tools to the agent. See the [MCP guide](mcp.md). |
| `mcp_config` | no | Fine-tune how MCP tools are prepared, such as converting their schemas to strict mode and formatting MCP failures. See the [MCP guide](mcp.md#agent-level-mcp-configuration). |
| `input_guardrails` | no | Guardrails that run on the first user input for this agent chain. See [Guardrails](guardrails.md). |
| `output_guardra
```

</details>

---

## GOLD-B002-04

- **provider**: anthropic
- **document**: Search results
- **section**: How it works › Required fields
- **source span**: `ver_42a4f3d941b664a285883aaf6ff90373` chars 2380–2517
- **evidence kind**: `parameter_table_row`
- **binding**: structural: parameter is the row's first cell, type is another cell of the same row
- **generator confidence**: high
- **needs human interpretation**: False

**Proposed question** (a suggestion, not gold)

> What type does the `source` parameter take?

**Proposed answer**: `string`

**Proposed atomic claims**: `` `source` is of type string. ``

**Generator notes**: Row-scoped association. Reviewer should confirm the table is a parameter table and that the column header means the parameter's own type rather than, say, a return type.

### Evidence (verbatim, authoritative)

```
| `source`  | string | The source of the content. Any stable string works: a URL, or an internal identifier such as `kb://article-1234` |
```

<details><summary>Context before</summary>

```
:

```json
{
  "type": "search_result",
  "source": "https://example.com/article", // Required: Source URL or identifier
  "title": "Article Title", // Required: Title of the result
  "content": [
    // Required: Array of text blocks
    {
      "type": "text",
      "text": "The actual content of the search result..."
    }
  ],
  "citations": {
    // Optional: Citation configuration
    "enabled": true // Enable/disable citations for this result
  }
}
```

### Required fields

| Field     | Type   | Description                                                                                                      |
| --------- | ------ | ---------------------------------------------------------------------------------------------------------------- |
| `type`    | string | Must be `"search_result"`                                                                                        |

```

</details>

<details><summary>Context after</summary>

```

| `title`   | string | A descriptive title for the search result                                                                        |
| `content` | array  | An array of text blocks containing the actual content                                                            |

### Optional fields

| Field           | Type   | Description                                                                                                                                                                                                                                                                                                                     |
| --------------- | ------ | -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
```

</details>

---

## GOLD-B002-05

- **provider**: anthropic
- **document**: Bash tool
- **section**: Parameters
- **source span**: `ver_9bf8513721dc2d1ef3e1ec42bf535dc6` chars 7758–7826
- **evidence kind**: `parameter_table_row`
- **binding**: structural: parameter is the row's first cell, requiredness is column 1 of the same row
- **generator confidence**: high
- **needs human interpretation**: False

**Proposed question** (a suggestion, not gold)

> Is the `restart` parameter required?

**Proposed answer**: No, it is optional.

**Proposed atomic claims**: `` `restart` is optional. ``

**Generator notes**: Row-scoped association, so the state cannot belong to a different parameter. Reviewer should confirm the table is a parameter table and that the column header means what it appears to mean.

### Evidence (verbatim, authoritative)

```
| `restart` | No       | Set to `true` to restart the bash session |
```

<details><summary>Context before</summary>

```
s-and-tools/tool-use/parallel-tool-use).

The API is stateless. Nothing about your shell session travels between requests, so your application decides when the session starts, how long it lives, and when to restart it. For the full request and response cycle, see [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls).

## Parameters

A bash tool definition has two required fields, `type` and `name`, and the `name` must be `bash`. The tool is schema-less: you don't provide an `input_schema`, because the schema is built into Claude's model and can't be modified. The following table lists the input fields Claude sets when it calls the tool.

| Parameter | Required | Description                               |
| --------- | -------- | ----------------------------------------- |
| `command` | Yes\*    | The bash command to run                   |

```

</details>

<details><summary>Context after</summary>

```


\*Required unless using `restart`

To handle `restart: true`, kill the shell process, start a new one, and return a `tool_result` that confirms the restart. A restarted session starts clean: the working directory, environment variables, and any running processes are gone.

<Accordion title="Example usage">
  Run a command:

  ```json
  {
    "command": "ls -la *.py"
  }
  ```

  Restart the session:

  ```json
  {
    "restart": true
  }
  ```
</Accordion>

## Tool versions

`bash_20250124` is the current version of the tool, and it requires no beta header. Every model from Claude Sonnet 3.7 ([retired](https://platform.claude.com/docs/en/about-claude/model-deprecations)) onward accepts it, including all current Claude models.

The original `bash_20241022` version is part of the computer use beta, and the October 2024 Claude Sonnet 3.5 release ([retired](https://platform.claude.com/docs
```

</details>

---

## GOLD-B002-06

- **provider**: anthropic
- **document**: Advisor tool
- **section**: Tool parameters
- **source span**: `ver_b8b18cda9b875d51a2ce979a1bf4e909` chars 13205–13710
- **evidence kind**: `parameter_table_row`
- **binding**: structural: parameter is the row's first cell, type is another cell of the same row
- **generator confidence**: high
- **needs human interpretation**: False

**Proposed question** (a suggestion, not gold)

> What type does the `max_tokens` parameter take?

**Proposed answer**: `integer`

**Proposed atomic claims**: `` `max_tokens` is of type integer. ``

**Generator notes**: Row-scoped association. Reviewer should confirm the table is a parameter table and that the column header means the parameter's own type rather than, say, a return type.

### Evidence (verbatim, authoritative)

```
| `max_tokens` | integer        | advisor model's output cap | Caps the advisor's total output (thinking plus text) per call. Minimum 1024. See [Capping advisor output](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool#capping-advisor-output).                                                                                                                                                                                                                                            |
```

<details><summary>Context before</summary>

```
ed at this model's rates for the sub-inference.                                                                                                                                                                                                                                                                                                                                                         |
| `max_uses`   | integer        | unlimited                  | Maximum number of advisor calls allowed in a single request. Once the executor reaches this cap, further advisor calls return an `advisor_tool_result_error` with `error_code: "max_uses_exceeded"` and the executor continues without further advice. This is a per-request cap, not a per-conversation cap. See [Cost control](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool#cost-control) for conversation-level limits. |

```

</details>

<details><summary>Context after</summary>

```

| `caching`    | object \| null | `null` (off)               | Enables [prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) for the advisor's own transcript across calls within a conversation. See [Advisor prompt caching](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool#advisor-prompt-caching).                                                                                                                                                     |

The `caching` object has the shape `{"type": "ephemeral", "ttl": "5m" | "1h"}`. Unlike `cache_control` on content blocks, this is not a breakpoint marker. It is an on/off switch. The server determines where cache boundaries go.

The advisor tool also accepts the generic properties available on any tool definition: `cache_control`, `allowed_callers`, `defer_loading`, and `strict` (covered i
```

</details>

---

## GOLD-B002-07

- **provider**: anthropic
- **document**: Compaction
- **section**: Parameters
- **source span**: `ver_c60f7418b69b6610bd20e974b92cdd8c` chars 9443–9648
- **evidence kind**: `parameter_table_row`
- **binding**: structural: parameter is the row's first cell, type is another cell of the same row
- **generator confidence**: high
- **needs human interpretation**: False

**Proposed question** (a suggestion, not gold)

> What type does the `pause_after_compaction` parameter take?

**Proposed answer**: `boolean`

**Proposed atomic claims**: `` `pause_after_compaction` is of type boolean. ``

**Generator notes**: Row-scoped association. Reviewer should confirm the table is a parameter table and that the column header means the parameter's own type rather than, say, a return type.

### Evidence (verbatim, authoritative)

```
| `pause_after_compaction` | boolean | `false`                                     | Whether to pause after generating the compaction summary                                                               |
```

<details><summary>Context before</summary>

```
ent: response.content }

  puts response
  ```
</CodeGroup>

## Parameters

| Parameter                | Type    | Default                                     | Description                                                                                                            |
| ------------------------ | ------- | ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `type`                   | string  | Required                                    | Must be `"compact_20260112"`                                                                                           |
| `trigger`                | object  | `{"type": "input_tokens", "value": 150000}` | When to trigger compaction. `input_tokens` is the only supported trigger type. `value` must be at least 50,000 tokens. |

```

</details>

<details><summary>Context after</summary>

```

| `instructions`           | string  | `null`                                      | Custom summarization prompt. Completely replaces the default prompt when provided.                                     |

### Trigger configuration

Configure when compaction triggers using the `trigger` parameter:

<CodeGroup>
  ```bash cURL
  curl https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "anthropic-beta: compact-2026-01-12" \
    -H "content-type: application/json" \
    -d '{
      "model": "claude-opus-5",
      "max_tokens": 4096,
      "messages": [
        {
          "role": "user",
          "content": "Hello, Claude"
        }
      ],
      "context_management": {
        "edits": [
          {
            "type": "compact_20260112",
            "trigger": {
              "type": "input_tokens",
          
```

</details>

---

## GOLD-B002-08

- **provider**: anthropic
- **document**: Trigger a routine through the API
- **section**: Trigger a routine › Request body
- **source span**: `ver_d81ee605bd8bbb880deea432e51462ac` chars 8144–8480
- **evidence kind**: `parameter_table_row`
- **binding**: structural: parameter is the row's first cell, requiredness is column 2 of the same row
- **generator confidence**: high
- **needs human interpretation**: False

**Proposed question** (a suggestion, not gold)

> Is the `text` parameter required?

**Proposed answer**: No, it is optional.

**Proposed atomic claims**: `` `text` is optional. ``

**Generator notes**: Row-scoped association, so the state cannot belong to a different parameter. Reviewer should confirm the table is a parameter table and that the column header means what it appears to mean.

### Evidence (verbatim, authoritative)

```
| `text` | string | No       | Initial context for this run, such as an alert body, a failing log line, or a git diff. The value is freeform text and is not parsed; if you send JSON or another structured payload, the routine receives it as a literal string. Passed to the routine alongside its saved prompt. Maximum 65,536 characters. |
```

<details><summary>Context before</summary>

```
 `routine_id` | string | The routine's identifier. Despite the parameter name, the value is prefixed `trig_` rather than `routine_`. Included in the URL the modal window shows when you add an API trigger. |

### Request body

| Field  | Type   | Required | Description                                                                                                                                                                                                                                                                                                     |
| ------ | ------ | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

```

</details>

<details><summary>Context after</summary>

```


The body is optional. Unknown fields in the body are ignored.

### Response

A successful request returns `200 OK` with the new session details:

```json
{
  "type": "routine_fire",
  "claude_code_session_id": "session_01HJKLMNOPQRSTUVWXYZ",
  "claude_code_session_url": "https://claude.ai/code/session_01HJKLMNOPQRSTUVWXYZ"
}
```

| Field                     | Type   | Description                                                                                                              |
| ------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------ |
| `type`                    | string | Always `routine_fire`.                                                                                                   |
| `claude_code_session_id`  | string | The ID of the Claude Code session created
```

</details>

---

## GOLD-B002-09

- **provider**: anthropic
- **document**: Computer use tool
- **section**: How to implement computer use › Tool parameters
- **source span**: `ver_d9ba3ab0d872dd86047c7ed6dc783235` chars 33443–33611
- **evidence kind**: `parameter_table_row`
- **binding**: structural: parameter is the row's first cell, requiredness is column 1 of the same row
- **generator confidence**: high
- **needs human interpretation**: False

**Proposed question** (a suggestion, not gold)

> Is the `display_height_px` parameter required?

**Proposed answer**: Yes, it is required.

**Proposed atomic claims**: `` `display_height_px` is required. ``

**Generator notes**: Row-scoped association, so the state cannot belong to a different parameter. Reviewer should confirm the table is a parameter table and that the column header means what it appears to mean.

### Evidence (verbatim, authoritative)

```
| `display_height_px` | Yes      | Display height in pixels                                                                                                            |
```

<details><summary>Context before</summary>

```
mmand/Windows key).
</Accordion>

### Tool parameters

| Parameter           | Required | Description                                                                                                                         |
| ------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `type`              | Yes      | Tool version (`computer_20251124` or `computer_20250124`)                                                                           |
| `name`              | Yes      | Must be "computer"                                                                                                                  |
| `display_width_px`  | Yes      | Display width in pixels                                                                                                             |

```

</details>

<details><summary>Context after</summary>

```

| `display_number`    | No       | Display number for X11 environments                                                                                                 |
| `enable_zoom`       | No       | Enable zoom action (`computer_20251124` only). Set to `true` to allow Claude to zoom into specific screen regions. Default: `false` |

<Note>
  **Important:** Your application must explicitly run the computer use tool; Claude cannot run it directly. You are responsible for implementing the screenshot capture, mouse movements, keyboard inputs, and other actions based on Claude's requests.
</Note>

### Combining with thinking

For combining computer use with thinking, see [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking).

<Tip>
  For computer use specifically, internal benchmarking suggests these `effort` settings:

  * **Claude Opus 4.7:** use `high` as the defa
```

</details>

---

## GOLD-B002-10

- **provider**: anthropic
- **document**: Structured outputs
- **section**: JSON outputs › Working with JSON outputs in SDKs › SDK-specific methods
- **source span**: `ver_0865c9612dfe97d8f30dd870dd12e53e` chars 24246–24381
- **evidence kind**: `prose_statement`
- **binding**: single identifier in the span
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question answerable from the evidence below, which mentions `parsed_output`.

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none — reviewer to write_

**Generator notes**: The reviewer writes the question and the atomic claims from the evidence; no relation is proposed. The span was checked to resolve its own references and is not drawn from example code. 

### Evidence (verbatim, authoritative)

```
    The `parse()` method automatically transforms your Pydantic model, validates the response, and returns a `parsed_output` attribute.
```

<details><summary>Context before</summary>

```
ring returned in the text content block and project specific fields.

    ```bash
    ant messages create \
      --transform 'content.#(type=="text").text|@fromstr|{name,email}' \
      --format yaml <<'YAML'
    model: claude-opus-5
    max_tokens: 1024
    messages:
      - role: user
        content: >-
          Extract contact info: John Smith, john@example.com,
          interested in the Pro plan
    output_config:
      format:
        type: json_schema
        schema:
          type: object
          properties:
            name: {type: string}
            email: {type: string}
            plan_interest: {type: string}
          required: [name, email, plan_interest]
          additionalProperties: false
    YAML
    ```

    ```yaml Output
    name: John Smith
    email: john@example.com
    ```
  </Tab>

  <Tab title="Python">
    **`client.messages.parse()` (Recommended)**


```

</details>

<details><summary>Context after</summary>

```


    ```python
    from pydantic import BaseModel
    # ...
    class ContactInfo(BaseModel):
        name: str
        email: str
        plan_interest: str
    # ...
    response = client.messages.parse(
        model="claude-opus-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "Extract contact info: John Smith, john@example.com, interested in the Pro plan",
            }
        ],
        output_format=ContactInfo,
    )

    # Access the parsed output directly
    contact = response.parsed_output
    print(contact.name, contact.email)
    ```

    **`transform_schema()` helper**

    For when you need to manually transform schemas before sending, or when you want to modify a Pydantic-generated schema. Unlike `client.messages.parse()`, which transforms provided schemas automatically, this gives you the transfor
```

</details>

---

## GOLD-B002-11

- **provider**: anthropic
- **document**: What's new in Claude Sonnet 5
- **section**: Preamble
- **source span**: `ver_6c0983aad96f198367a0de369b3bb86c` chars 205–656
- **evidence kind**: `prose_statement`
- **binding**: AMBIGUOUS: 3 identifiers present (temperature, top_p, top_k)
- **generator confidence**: low
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question answerable from the evidence below, which mentions `temperature`, `top_p`, `top_k`.

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none — reviewer to write_

**Generator notes**: The reviewer writes the question and the atomic claims from the evidence; no relation is proposed. The span was checked to resolve its own references and is not drawn from example code. More than one identifier appears, so the subject is not machine-determinable.

### Evidence (verbatim, authoritative)

```
Claude Sonnet 5 is the next generation of Anthropic's Sonnet model family. It is a drop-in upgrade for Claude Sonnet 4.6 with three behavior changes: [adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) is on by default, manual extended thinking now returns a 400 error (it was deprecated on Claude Sonnet 4.6), and setting sampling parameters (`temperature`, `top_p`, `top_k`) to non-default values returns a 400 error.
```

<details><summary>Context before</summary>

```
---
title: What's new in Claude Sonnet 5
url: https://platform.claude.com/docs/en/about-claude/models/whats-new-sonnet-5
description: Overview of new features and behavior changes in Claude Sonnet 5.
---


```

</details>

<details><summary>Context after</summary>

```
 This page summarizes everything new at launch, including a new tokenizer.

## New model

| Model           | API model ID      | Description                                    |
| --------------- | ----------------- | ---------------------------------------------- |
| Claude Sonnet 5 | `claude-sonnet-5` | The best combination of speed and intelligence |

Claude Sonnet 5 supports the [1M token context window](https://platform.claude.com/docs/en/build-with-claude/context-windows) by default (1M tokens is both the default and the maximum; there is no smaller context variant), 128k max output tokens, [adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/thinking), and the same set of tools and platform features as Claude Sonnet 4.6, except [Priority Tier](https://platform.claude.com/docs/en/api/service-tiers#supported-models), which is not available on Claude Sonnet 5.


```

</details>

---

## GOLD-B002-12

- **provider**: anthropic
- **document**: Prompt caching
- **section**: Caching strategies and considerations › Cache limitations
- **source span**: `ver_7947433dfde6b3b8eccd0faa597c3c9a` chars 31104–31174
- **evidence kind**: `prose_statement`
- **binding**: single identifier in the span
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question answerable from the evidence below, which mentions `cache_control`.

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none — reviewer to write_

**Generator notes**: The reviewer writes the question and the atomic claims from the evidence; no relation is proposed. The span was checked to resolve its own references and is not drawn from example code. 

### Evidence (verbatim, authoritative)

```
Shorter prompts cannot be cached, even if marked with `cache_control`.
```

<details><summary>Context before</summary>

```
wing)
* 2,048 tokens for [Claude Mythos Preview](https://anthropic.com/glasswing) and Claude Opus 4.7
* 4,096 tokens for Claude Opus 4.6 and Claude Opus 4.5
* 1,024 tokens for Claude Opus 4.8, Claude Sonnet 5, Claude Sonnet 4.6, Claude Sonnet 4.5, Claude Opus 4.1 ([retired, except on Bedrock and Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations)), Claude Opus 4 ([retired, except on Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations)), and Claude Sonnet 4 ([retired, except on Bedrock and Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations))
* 4,096 tokens for Claude Haiku 4.5
* 2,048 tokens for Claude Haiku 3.5 ([retired, except on Bedrock and Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations))

These minimums apply on every platform where each model is available.


```

</details>

<details><summary>Context after</summary>

```
 Any requests to cache fewer than this number of tokens will be processed without caching, and no error is returned. To verify whether a prompt was cached, check the [response usage fields](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#tracking-cache-performance): if both `cache_creation_input_tokens` and `cache_read_input_tokens` are 0, the prompt was not cached (likely because it did not meet the minimum length requirement).

If your prompt falls just short of the minimum for your model and platform, expanding the cached content to reach the threshold is often worthwhile. Cache reads cost significantly less than uncached input tokens, so reaching the minimum can reduce costs for frequently reused prompts.

<Note>
  [Bedrock](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock) is an AWS-operated platform. On Bedrock, see the [Bedrock pr
```

</details>

---

## GOLD-B002-13

- **provider**: anthropic
- **document**: Deploy MCP tunnels with Docker Compose
- **section**: Install
- **source span**: `ver_b05e105d93045aff4c7ce998b198ae79` chars 17854–18006
- **evidence kind**: `prose_statement`
- **binding**: single identifier in the span
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question answerable from the evidence below, which mentions `TUNNEL_TOKEN`.

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none — reviewer to write_

**Generator notes**: The reviewer writes the question and the atomic claims from the evidence; no relation is proposed. The span was checked to resolve its own references and is not drawn from example code. 

### Evidence (verbatim, authoritative)

```
The compose file reads `TUNNEL_TOKEN` from the host environment with no default, so the export must be repeated in every fresh shell and after a reboot.
```

<details><summary>Context before</summary>

```
:
              - ALL
            stop_grace_period: 30s
            logging:
              options:
                max-size: "10m"
                max-file: "3"
        EOF
        ```

        If you're using the [sample MCP server](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/deploy-compose#optional-use-a-sample-mcp-server), append it as a service:

        ```bash
        cat >> docker-compose.yaml <<'EOF'

          hello-mcp:
            image: python:3.13-slim
            working_dir: /app
            volumes:
              - ./hello_server.py:/app/hello_server.py:ro
            command: sh -c "pip install --quiet mcp && python hello_server.py"
            restart: unless-stopped
        EOF
        ```
      </Step>

      <Step title="Start the deployment">
        ```bash
        docker compose up -d
        ```
      </Step>
    </Steps>
  </Tab>
</Tabs>


```

</details>

<details><summary>Context after</summary>

```


For a multi-VM deployment, copy the `mcp-tunnel/` directory to each host, set `TUNNEL_TOKEN`, and run `docker compose up -d`. In the programmatic flow `TUNNEL_TOKEN` is `$(sudo cat data/tunnel-token)`; in the manual flow it's the value you copied from the Console. The same tunnel token and certificates work across all replicas.

## Verify the deployment

Verify end to end by calling an [upstream MCP server](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/concepts#components) from Anthropic's side: see [Use the tunneled MCP servers](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/overview#use-the-tunneled-mcp-servers). With the [sample MCP server](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/deploy-compose#optional-use-a-sample-mcp-server), the routed URL is `https://echo.<your-tunnel-domain>/mcp`. If verification fails, see [Trouble
```

</details>

---

## GOLD-B002-14

- **provider**: anthropic
- **document**: Batch processing
- **section**: Message Batches API › How to use the Message Batches API › Extended output (beta)
- **source span**: `ver_cec813c3bb15b76dcf16e7a0c2231ef1` chars 59581–59790
- **evidence kind**: `prose_statement`
- **binding**: single identifier in the span
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question answerable from the evidence below, which mentions `max_tokens`.

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none — reviewer to write_

**Generator notes**: The reviewer writes the question and the atomic claims from the evidence; no relation is proposed. The span was checked to resolve its own references and is not drawn from example code. 

### Evidence (verbatim, authoritative)

```
The `output-300k-2026-03-24` beta header raises the `max_tokens` cap to 300,000 for batch requests using Claude Opus 5, Claude Opus 4.8, Claude Opus 4.7, Claude Opus 4.6, Claude Sonnet 5, or Claude Sonnet 4.6.
```

<details><summary>Context before</summary>

```
essages API.

Because there is no open connection to maintain, the batch loop runs **more iterations per turn** than a synchronous request before it returns `stop_reason: "pause_turn"`. If a batch result comes back with `pause_turn`, the turn did not finish; you can continue it by submitting the paused assistant content in a follow-up request (batch or synchronous) exactly as shown in the [pause\_turn continuation pattern](https://platform.claude.com/docs/en/agents-and-tools/tool-use/server-tools#the-server-side-loop-and-pause-turn).

The batch worker additionally throttles `web_search` per organization so that highly concurrent batch processing does not exhaust your organization's web-search rate limit. The batch retries throttled requests automatically; you don't need to handle this yourself, but very large web-search batches might take longer to complete.

### Extended output (beta)


```

</details>

<details><summary>Context after</summary>

```
 Include the header to generate outputs far longer than the standard 128k `max_tokens` limit in a single turn.

<Note>
  Extended output is available on the Message Batches API only, not the synchronous Messages API. It is supported on the Claude API and Claude Platform on AWS, and is not currently available on Amazon Bedrock, Google Cloud, or Microsoft Foundry.
</Note>

Use extended output for long-form generation such as book-length drafts and technical documentation, exhaustive structured data extraction, large code-generation scaffolds, and long reasoning chains.

A single 300k-token generation can take over an hour to complete, so plan your batch submissions with the 24-hour processing window in mind. Standard batch pricing (50% of standard API prices) applies.

<CodeGroup>
  ```bash cURL
  curl https://api.anthropic.com/v1/messages/batches \
       --header "x-api-key: $ANTHROPIC_A
```

</details>

---

## GOLD-B002-15

- **provider**: openai
- **document**: Testing
- **section**: Testing › Agent workflow recipes › Inspect model calls
- **source span**: `ver_d2295786320b2815477eb963eb1f5e8a` chars 7031–7112
- **evidence kind**: `prose_statement`
- **binding**: single identifier in the span
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question answerable from the evidence below, which mentions `ScriptedModel`.

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none — reviewer to write_

**Generator notes**: The reviewer writes the question and the atomic claims from the evidence; no relation is proposed. The span was checked to resolve its own references and is not drawn from example code. 

### Evidence (verbatim, authoritative)

```
`ScriptedModel` records each call before it resolves or raises the selected step.
```

<details><summary>Context before</summary>

```
:
    assert call.streamed is False
    assert call.input == [{"content": "Summarize this", "role": "user"}]
    return {"output": [assistant_message("Handled the normalized request.")]}


@pytest.mark.asyncio
async def test_request_aware_response() -> None:
    model = ScriptedModel([ModelStep.respond(respond)])
    agent = Agent(name="Assistant", model=model)

    result = await Runner.run(
        agent,
        "Summarize this",
        run_config=RunConfig(tracing_disabled=True),
    )

    assert result.final_output == "Handled the normalized request."
    model.assert_complete()
```

`ScriptedModel` accepts `ModelStep`, the equivalent dictionary form, `ModelResponse`, a normalized output-item sequence, or an exception. Prefer fixed output sequences when a response does not depend on the call because fixed scripts make unexpected turns easier to diagnose.

### Inspect model calls


```

</details>

<details><summary>Context after</summary>

```


| Member | Contains |
| --- | --- |
| `calls` | Every `ModelCall` in invocation order |
| `first_call` | The first call, or `None` |
| `last_call` | The most recent call, or `None` |
| `remaining_steps` | The number of configured steps not yet consumed |

Common assertions include `call.input`, `call.model_settings`, `call.tools`, `call.handoffs`, and `call.streamed`. Mutable request data is snapshotted at the invocation boundary, and each public history accessor returns detached snapshots. Tool, handoff, output-schema, and tracing objects keep their runtime identity.

Structured `call_index` and `input_index` error fields are zero-based so they directly index `calls[...]` or the supplied step sequence. Human-readable error messages display one-based call or step numbers.

Use `enqueue()` or `extend()` when one test needs to append model steps incrementally. Create a new `ScriptedModel
```

</details>

---

## GOLD-B002-16

- **provider**: anthropic
- **document**: Claude on Google Cloud
- **section**: Preamble
- **source span**: `ver_e312b7f41115cc2b84cd36151efc6dd8` chars 455–725
- **evidence kind**: `prose_statement`
- **binding**: single identifier in the span
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question answerable from the evidence below, which mentions `anthropic_version`.

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none — reviewer to write_

**Generator notes**: The reviewer writes the question and the atomic claims from the evidence; no relation is proposed. The span was checked to resolve its own references and is not drawn from example code. 

### Evidence (verbatim, authoritative)

```
* On Agent Platform, `model` is not passed in the request body. Instead, it is specified in the Google Cloud endpoint URL.
* On Agent Platform, `anthropic_version` is passed in the request body (rather than as a header), and must be set to the value `vertex-2023-10-16`.
```

<details><summary>Context before</summary>

```
---
title: Claude on Google Cloud
url: https://platform.claude.com/docs/en/build-with-claude/claude-on-vertex-ai
description: Anthropic's Claude models are available through [Google Cloud's Agent Platform](https://cloud.google.com/vertex-ai).
---

The API for accessing Claude on Google Cloud's Agent Platform is nearly identical to the [Messages API](https://platform.claude.com/docs/en/api/messages/create), with two key differences in request format:


```

</details>

<details><summary>Context after</summary>

```


Agent Platform is also supported by Anthropic's official [client SDKs](https://platform.claude.com/docs/en/cli-sdks-libraries/overview). This guide walks you through making a request to Claude on Agent Platform using one of Anthropic's client SDKs.

Note that this guide assumes you already have a Google Cloud project that is able to use Agent Platform. See [Anthropic Claude models on Agent Platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/claude) for more information on the setup required and a full walkthrough.

## Install an SDK for accessing Agent Platform

First, install Anthropic's [client SDK](https://platform.claude.com/docs/en/cli-sdks-libraries/overview) for your language of choice.

<Tabs>
  <Tab title="Python">
    ```bash
    pip install -U "anthropic[vertex]"
    ```
  </Tab>

  <Tab title="TypeScript">
    ```bash
    npm insta
```

</details>

---

## GOLD-B002-17

- **provider**: openai
- **document**: Migration guide
- **section**: Migration guide › Breaking changes › Named path parameters
- **source span**: `ver_e8a7b17b5af64679cadea33cd8f6d250` chars 1813–2009
- **evidence kind**: `prose_statement`
- **binding**: AMBIGUOUS: 2 identifiers present (parent_id, child_id)
- **generator confidence**: low
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question answerable from the evidence below, which mentions `parent_id`, `child_id`.

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none — reviewer to write_

**Generator notes**: The reviewer writes the question and the atomic claims from the evidence; no relation is proposed. The span was checked to resolve its own references and is not drawn from example code. More than one identifier appears, so the subject is not machine-determinable.

### Evidence (verbatim, authoritative)

```
For example, for a method that would call an endpoint at `/v1/parents/{parent_id}/children/{child_id}`, only the _last_ path parameter is positional and the rest must be passed as named arguments.
```

<details><summary>Context before</summary>

```
eb/API/ReadableStream) rather than a [node `Readable`](https://nodejs.org/api/stream.html#readable-streams).

```ts
// Before:
const res = await client.example.retrieve('string/with/slash').asResponse();
res.body.pipe(process.stdout);

// After:
import { Readable } from 'node:stream';
const res = await client.example.retrieve('string/with/slash').asResponse();
Readable.fromWeb(res.body).pipe(process.stdout);
```

Additionally, the `headers` property on `APIError` objects is now an instance of the Web [Headers](https://developer.mozilla.org/en-US/docs/Web/API/Headers) class. It was previously defined as `Record<string, string | null | undefined>`.

### Named path parameters

Methods that take multiple path parameters typically now use named instead of positional arguments for better clarity and to prevent a footgun where it was easy to accidentally pass arguments in the incorrect order.


```

</details>

<details><summary>Context after</summary>

```


```ts
// Before
client.parents.children.retrieve('p_123', 'c_456');

// After
client.parents.children.retrieve('c_456', { parent_id: 'p_123' });
```

<details>

<summary>This affects the following methods</summary>

- `client.fineTuning.checkpoints.permissions.delete()`
- `client.vectorStores.files.retrieve()`
- `client.vectorStores.files.update()`
- `client.vectorStores.files.delete()`
- `client.vectorStores.files.content()`
- `client.vectorStores.fileBatches.retrieve()`
- `client.vectorStores.fileBatches.cancel()`
- `client.vectorStores.fileBatches.listFiles()`
- `client.beta.threads.runs.retrieve()`
- `client.beta.threads.runs.update()`
- `client.beta.threads.runs.cancel()`
- `client.beta.threads.runs.submitToolOutputs()`
- `client.beta.threads.runs.steps.retrieve()`
- `client.beta.threads.runs.steps.list()`
- `client.beta.threads.messages.retrieve()`
- `client.beta.threads.messages
```

</details>

---

## GOLD-B002-18

- **provider**: anthropic
- **document**: Refusals and fallback
- **section**: Server-side fallback › Naming your own fallback models
- **source span**: `ver_fa78e1feb6289d6bcb22305e61bbbfc3` chars 25565–25931
- **evidence kind**: `prose_statement`
- **binding**: AMBIGUOUS: 5 identifiers present (allowed_fallback_models, max_tokens, thinking, output_config)
- **generator confidence**: low
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question answerable from the evidence below, which mentions `allowed_fallback_models`, `max_tokens`, `thinking`.

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none — reviewer to write_

**Generator notes**: The reviewer writes the question and the atomic claims from the evidence; no relation is proposed. The span was checked to resolve its own references and is not drawn from example code. More than one identifier appears, so the subject is not machine-determinable.

### Evidence (verbatim, authoritative)

```
With the beta header set, that list is published as `allowed_fallback_models` on the model's entry in the [Models API](https://platform.claude.com/docs/en/api/models/list).
* Each entry names a `model` and can override `max_tokens`, `thinking`, `output_config`, and `speed` for that attempt only.
* The request must be valid as a direct request to every model named.
```

<details><summary>Context before</summary>

```
 $client = new Client();

  $response = $client->beta->messages->create(
      model: 'claude-fable-5',
      maxTokens: 1024,
      messages: [['role' => 'user', 'content' => 'Hello, Claude']],
      fallbacks: [['model' => 'claude-opus-4-8']],
      betas: ['server-side-fallback-2026-07-01'],
  );

  echo $response->model, PHP_EOL;
  ```

  ```ruby Ruby
  client = Anthropic::Client.new

  response = client.beta.messages.create(
    model: "claude-fable-5",
    max_tokens: 1024,
    messages: [{role: "user", content: "Hello, Claude"}],
    fallbacks: [{model: "claude-opus-4-8"}],
    betas: ["server-side-fallback-2026-07-01"]
  )

  puts response.model
  ```
</CodeGroup>

A few rules apply to the `fallbacks` list:

* Entries are tried in order. Each must be distinct from the other entries and from the requested model.
* Each entry must be one of the requested model's permitted targets. 
```

</details>

<details><summary>Context after</summary>

```
 If a fallback model does not support a feature the request uses, the API rejects the request up front.
* As with the default mode, only a safety classifier decline triggers the fallback. A rate limit, overload, or server error on the requested model is returned to you as-is.

The explicit-list form also works under the `server-side-fallback-2026-06-01` beta header; the `"default"` mode does not.

The response has the same shape in both modes: the model that served the turn appears in the top-level `model` field, a `fallback` content block marks the handoff, and `usage.iterations` records each attempt.

### What the response contains

The response looks like any other message, with two additions:

* The top-level `model` field reports the model that produced the returned message, whether that is the requested model or a fallback.

* A `fallback` content block marks each point in `content
```

</details>

---
