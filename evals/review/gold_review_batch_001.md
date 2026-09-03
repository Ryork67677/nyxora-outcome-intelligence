# Gold review batch 001

**18 candidates · corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · generated 2026-08-19T05:23:00Z**

Nothing in this file is ground truth. Every candidate is `candidate_unverified`. The evidence below is quoted verbatim from the frozen corpus and is authoritative for this review — **do not consult live documentation**, which may have changed since the snapshot.

For each candidate, judge the *proposed* question, answer and claims against the evidence and its surrounding context, and return the verdict schema in `docs/GOLD-REVIEW-PROCEDURE.md`.

---

## GOLD-B001-01

- **provider**: anthropic
- **document**: Computer use tool
- **section**: How to implement computer use › Tool parameters
- **source span**: `ver_d9ba3ab0d872dd86047c7ed6dc783235` chars 33781–33949
- **evidence kind**: `parameter_table_row`
- **binding**: structural: parameter is the row's first cell, default stated in the same row
- **generator confidence**: high
- **needs human interpretation**: False

**Proposed question** (a suggestion, not gold)

> What is the default value of enable_zoom?

**Proposed answer**: false

**Proposed atomic claims**: `enable_zoom defaults to false`

**Generator notes**: Row-scoped association, so the value cannot belong to a different parameter. Reviewer should still confirm the row is a parameter table and not a comparison or pricing table.

### Evidence (verbatim, authoritative)

```
| `enable_zoom`       | No       | Enable zoom action (`computer_20251124` only). Set to `true` to allow Claude to zoom into specific screen regions. Default: `false` |
```

<details><summary>Context before</summary>

```
---------------------------------------------------- |
| `type`              | Yes      | Tool version (`computer_20251124` or `computer_20250124`)                                                                           |
| `name`              | Yes      | Must be "computer"                                                                                                                  |
| `display_width_px`  | Yes      | Display width in pixels                                                                                                             |
| `display_height_px` | Yes      | Display height in pixels                                                                                                            |
| `display_number`    | No       | Display number for X11 environments                                                                                                 |

```

</details>

<details><summary>Context after</summary>

```


<Note>
  **Important:** Your application must explicitly run the computer use tool; Claude cannot run it directly. You are responsible for implementing the screenshot capture, mouse movements, keyboard inputs, and other actions based on Claude's requests.
</Note>

### Combining with thinking

For combining computer use with thinking, see [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking).

<Tip>
  For computer use specifically, internal benchmarking suggests these `effort` settings:

  * **Claude Opus 4.7:** use `high` as the default; use `low` for high-throughput or cost-sensitive workloads.
  * **Claude Sonnet 4.6 and Claude Opus 4.6:** use `medium` as the default (best accuracy-to-cost ratio). Avoid `max`, which adds token cost without improving accuracy on UI tasks. On these models, `low` uses *fewer* output tokens than disabling thinking entirely (fewer mis
```

</details>

---

## GOLD-B001-02

- **provider**: openai
- **document**: Agents
- **section**: Agents › Basic configuration
- **source span**: `ver_35cac5e98c151a17f941a6142d74709f` chars 3571–3725
- **evidence kind**: `parameter_table_row`
- **binding**: structural: parameter is the row's first cell, default stated in the same row
- **generator confidence**: high
- **needs human interpretation**: False

**Proposed question** (a suggestion, not gold)

> What is the default value of reset_tool_choice?

**Proposed answer**: True

**Proposed atomic claims**: `reset_tool_choice defaults to True`

**Generator notes**: Row-scoped association, so the value cannot belong to a different parameter. Reviewer should still confirm the row is a parameter table and not a comparison or pricing table.

### Evidence (verbatim, authoritative)

```
| `reset_tool_choice` | no | Reset `tool_choice` after a tool call (default: `True`) to avoid tool-use loops. See [Forcing tool use](#forcing-tool-use). |
```

<details><summary>Context before</summary>

```
 no | MCP servers that provide MCP-backed tools to the agent. See the [MCP guide](mcp.md). |
| `mcp_config` | no | Fine-tune how MCP tools are prepared, such as converting their schemas to strict mode and formatting MCP failures. See the [MCP guide](mcp.md#agent-level-mcp-configuration). |
| `input_guardrails` | no | Guardrails that run on the first user input for this agent chain. See [Guardrails](guardrails.md). |
| `output_guardrails` | no | Guardrails that run on the final output for this agent. See [Guardrails](guardrails.md). |
| `output_type` | no | Structured output type instead of plain text. See [Output types](#output-types). |
| `hooks` | no | Agent-scoped lifecycle callbacks. See [Lifecycle events (hooks)](#lifecycle-events-hooks). |
| `tool_use_behavior` | no | Control whether tool results loop back to the model or end the run. See [Tool use behavior](#tool-use-behavior). |

```

</details>

<details><summary>Context after</summary>

```


```python
from agents import Agent
from agents.decorators import tool

@tool
def get_weather(city: str) -> str:
    """returns weather info for the specified city."""
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Haiku agent",
    instructions="Always respond in haiku form",
    model="gpt-5-nano",
    tools=[get_weather],
)
```

Everything in this section applies to `Agent`. `SandboxAgent` builds on the same ideas, then adds `default_manifest`, `base_instructions`, `capabilities`, and `run_as` for workspace-scoped runs. See [Sandbox agent concepts](sandbox/guide.md).

## Prompt templates

You can reference a prompt template created in the OpenAI platform by setting `prompt`. This works when OpenAI models are accessed through the Responses API.

To use it, please:

1. Go to https://platform.openai.com/playground/prompts
2. Create a new prompt variable, `poem_st
```

</details>

---

## GOLD-B001-03

- **provider**: anthropic
- **document**: Migration guide
- **section**: Migrating to Claude Mythos 5 and Claude Fable 5
- **source span**: `ver_a7bda3595f2c124605c3228464d4ee52` chars 2410–2519
- **evidence kind**: `explicit_required_optional`
- **binding**: single identifier in the sentence
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question about thinking in Migration guide, answerable from the evidence below (relationship stated: 'required').

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none_

**Generator notes**: Matched explicit marker 'required'. No claim is proposed: the reviewer should write the question and the atomic claims from the evidence. 

### Evidence (verbatim, authoritative)

```
The model determines when and how much to think on each request, and no `thinking` configuration is required.
```

<details><summary>Context before</summary>

```
de/models/introducing-claude-fable-5-and-claude-mythos-5) is Anthropic's most capable widely released model, generally available on the Claude API, [Amazon Bedrock](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock), [Claude Platform on AWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws), [Google Cloud](https://platform.claude.com/docs/en/build-with-claude/claude-on-vertex-ai), and [Microsoft Foundry](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry). [Claude Mythos 5](https://anthropic.com/glasswing) shares the same capabilities and is offered in limited availability to approved customers in Project Glasswing.

The baseline settings shared by `claude-fable-5` and `claude-mythos-5`:

* **Thinking:** [Adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) is always on. 
```

</details>

<details><summary>Context after</summary>

```
 Both `thinking: {type: "disabled"}` and manual extended thinking (`thinking: {type: "enabled", budget_tokens: N}`) return a 400 error.
* **Prefill:** Prefilling the assistant message returns a 400 error. Use system prompt instructions instead.
* **Context window and output:** A [1M token context window](https://platform.claude.com/docs/en/build-with-claude/context-windows) by default, and up to 128k output tokens per request.
* **Pricing:** $10 USD per million input tokens and $50 USD per million output tokens. See [Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing).
* **Data retention:** Both models require 30-day data retention and are not available under zero data retention (ZDR) arrangements; both are designated Covered Models. On the Claude API, a request to Claude Fable 5 from an organization whose data retention configuration does not meet this requirement 
```

</details>

---

## GOLD-B001-04

- **provider**: openai
- **document**: Guardrails
- **section**: Guardrails › Input guardrails
- **source span**: `ver_f22fbd5c504fa28a4e70440337e4a495` chars 1930–2119
- **evidence kind**: `explicit_exception`
- **binding**: single identifier in the sentence
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question about InputGuardrailTripwireTriggered in Guardrails, answerable from the evidence below (relationship stated: 'is raised').

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none_

**Generator notes**: Matched explicit marker 'is raised'. No claim is proposed: the reviewer should write the question and the atomic claims from the evidence. 

### Evidence (verbatim, authoritative)

```
If true, an [`InputGuardrailTripwireTriggered`][agents.exceptions.InputGuardrailTripwireTriggered] exception is raised, so you can appropriately respond to the user or handle the exception.
```

<details><summary>Context before</summary>

```
uardrails** run only for the agent that produces the final output.
-   **Tool guardrails** run on every custom function-tool invocation, with input guardrails before execution and output guardrails after execution.

If you need checks before and/or after each custom function-tool call in a workflow that includes managers, handoffs, or delegated specialists, use tool guardrails instead of relying only on agent-level input/output guardrails.

## Input guardrails

Input guardrails run in 3 steps:

1. First, the guardrail receives the same input passed to the agent.
2. Next, the guardrail function runs to produce a [`GuardrailFunctionOutput`][agents.guardrail.GuardrailFunctionOutput], which is then wrapped in an [`InputGuardrailResult`][agents.guardrail.InputGuardrailResult]
3. Finally, we check if [`.tripwire_triggered`][agents.guardrail.GuardrailFunctionOutput.tripwire_triggered] is true. 
```

</details>

<details><summary>Context after</summary>

```


!!! Note

    Input guardrails are intended to run on user input, so an agent's guardrails only run if the agent is the *first* agent. You might wonder, why is the `guardrails` property on the agent instead of passed to `Runner.run`? It's because guardrails tend to be related to the actual Agent - you'd run different guardrails for different agents, so colocating the code is useful for readability.

### Execution modes

Input guardrails support two execution modes:

- **Parallel execution** (default, `run_in_parallel=True`): The guardrail runs concurrently with the agent's execution. This provides the best latency since both start at the same time. However, if the guardrail's tripwire is triggered, the agent may have already consumed tokens and executed tools before being cancelled.

- **Blocking execution** (`run_in_parallel=False`): The guardrail runs and completes *before* the agent
```

</details>

---

## GOLD-B001-05

- **provider**: anthropic
- **document**: Context windows
- **section**: Context window overflow behavior
- **source span**: `ver_b42814c2d273210095c8e5844612933e` chars 14083–14230
- **evidence kind**: `explicit_response`
- **binding**: single identifier in the sentence
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question about invalid_request_error in Context windows, answerable from the evidence below (relationship stated: 'returns a').

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none_

**Generator notes**: Matched explicit marker 'returns a'. No claim is proposed: the reviewer should write the question and the atomic claims from the evidence. 

### Evidence (verbatim, authoritative)

```
If the input alone already exceeds the model's context window, the API returns a 400 `invalid_request_error` ("prompt is too long") on every model.
```

<details><summary>Context before</summary>

```
de compaction](https://platform.claude.com/docs/en/build-with-claude/compaction). Compaction automatically summarizes earlier parts of the conversation on the server, so the conversation can continue past the context window limit. It is available in beta for Claude 4.6 and later models and [Claude Mythos Preview](https://anthropic.com/glasswing).

For more specialized needs, [context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing) offers additional strategies:

* **Tool result clearing:** Clear old tool results in agentic workflows
* **Thinking block clearing:** Manage thinking blocks when you use extended thinking

Cached prompt prefixes still occupy the context window: [prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) changes what you pay for those tokens, not whether they count.

## Context window overflow behavior


```

</details>

<details><summary>Context after</summary>

```


On Claude 4.5 models and newer, if input tokens plus `max_tokens` exceeds the context window size, the API accepts the request. If generation then reaches the context window limit, it stops with `stop_reason: "model_context_window_exceeded"`. On earlier models, the API returns a [validation error](https://platform.claude.com/docs/en/api/errors) instead. To opt in to the `model_context_window_exceeded` behavior on those models, use the `model-context-window-exceeded-2025-08-26` beta header. See [Stop reasons and fallback](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons) for details.

To stay within context window limits, use the [token counting API](https://platform.claude.com/docs/en/build-with-claude/token-counting) to estimate token usage before sending messages to Claude.

## Next steps

<CardGroup cols={2}>
  <Card title="Compaction" icon="stack" href="h
```

</details>

---

## GOLD-B001-06

- **provider**: openai
- **document**: OpenAI Python API library
- **section**: Remove `await` for non-async usage. › Webhook Verification › Parsing webhook payloads
- **source span**: `ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` chars 14847–14951
- **evidence kind**: `explicit_constraint`
- **binding**: single identifier in the sentence
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question about body in OpenAI Python API library, answerable from the evidence below (relationship stated: 'must be').

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none_

**Generator notes**: Matched explicit marker 'must be'. No claim is proposed: the reviewer should write the question and the atomic claims from the evidence. 

### Evidence (verbatim, authoritative)

```
Note that the `body` parameter must be the raw JSON string sent from the server (do not parse it first).
```

<details><summary>Context before</summary>

```
pe)`.

```python
from pathlib import Path
from openai import OpenAI

client = OpenAI()

client.files.create(
    file=Path("input.jsonl"),
    purpose="fine-tune",
)
```

The async client uses the exact same interface. If you pass a [`PathLike`](https://docs.python.org/3/library/os.html#os.PathLike) instance, the file contents will be read asynchronously automatically.

## Webhook Verification

Verifying webhook signatures is _optional but encouraged_.

For more information about webhooks, see [the API docs](https://platform.openai.com/docs/guides/webhooks).

### Parsing webhook payloads

For most use cases, you will likely want to verify the webhook and parse the payload at the same time. To achieve this, we provide the method `client.webhooks.unwrap()`, which parses a webhook request and verifies that it was sent by OpenAI. This method will raise an error if the signature is invalid.


```

</details>

<details><summary>Context after</summary>

```
 The `.unwrap()` method will parse this JSON for you into an event object after verifying the webhook was sent from OpenAI.

```python
from openai import OpenAI
from flask import Flask, request

app = Flask(__name__)
client = OpenAI()  # OPENAI_WEBHOOK_SECRET environment variable is used by default


@app.route("/webhook", methods=["POST"])
def webhook():
    request_body = request.get_data(as_text=True)

    try:
        event = client.webhooks.unwrap(request_body, request.headers)

        if event.type == "response.completed":
            print("Response completed:", event.data)
        elif event.type == "response.failed":
            print("Response failed:", event.data)
        else:
            print("Unhandled event type:", event.type)

        return "ok"
    except Exception as e:
        print("Invalid signature:", e)
        return "Invalid signature", 400


if __name__ == "_
```

</details>

---

## GOLD-B001-07

- **provider**: anthropic
- **document**: Mid-conversation system messages and tool changes
- **section**: Mid-conversation tool changes
- **source span**: `ver_77fbe47b4b7db32ee46b972b2f611d0e` chars 4256–4327
- **evidence kind**: `explicit_response`
- **binding**: single identifier in the sentence
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question about tools in Mid-conversation system messages and tool changes, answerable from the evidence below (relationship stated: 'returns a').

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none_

**Generator notes**: Matched explicit marker 'returns a'. No claim is proposed: the reviewer should write the question and the atomic claims from the evidence. 

### Evidence (verbatim, authoritative)

```
Referencing a name that is not declared in `tools` returns a 400 error.
```

<details><summary>Context before</summary>

```
hanges, so the cached prefix stays intact.

`tool_addition` and `tool_removal` are content blocks in the `content` array of a `role: "system"` message, and they can be mixed with `text` blocks in the same message. The message follows the same placement rules as any mid-conversation system message (see [Limitations](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages#limitations)), and the change applies from that point in the conversation onward. Each block's `tool` field references a tool rather than defining one: `{"type": "tool_reference", "name": "..."}` names a tool declared in the request's `tools` array, and [MCP connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) tools can be referenced individually with `mcp_tool_reference` (`server_name` and `name`) or as a whole toolset with `mcp_toolset_reference` (`server_name`). 
```

</details>

<details><summary>Context after</summary>

```


Every tool declared in `tools` is offered to the model from the start of the conversation unless it is declared with `defer_loading: true`, which keeps it withheld until a `tool_addition` block surfaces it. `tool_addition` also re-offers a tool that an earlier `tool_removal` withdrew.

<CodeGroup>
  ```bash cURL
  curl https://api.anthropic.com/v1/messages \
    -H "content-type: application/json" \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "anthropic-beta: mid-conversation-tool-changes-2026-07-01" \
    -d '{
      "model": "claude-opus-5",
      "max_tokens": 1024,
      "tools": [
        {
          "name": "get_weather",
          "description": "Get the current weather for a location.",
          "input_schema": {
            "type": "object",
            "properties": {
              "location": {"type": "string", "description": "Ci
```

</details>

---

## GOLD-B001-08

- **provider**: openai
- **document**: Node.js Version Support Policy
- **section**: Node.js Version Support Policy › Release and packaging rules
- **source span**: `ver_0699973a131d91f270d69f81ba7a0da0` chars 1250–1371
- **evidence kind**: `explicit_required_optional`
- **binding**: single identifier in the sentence
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question about engines.node in Node.js Version Support Policy, answerable from the evidence below (relationship stated: 'required').

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none_

**Generator notes**: Matched explicit marker 'required'. No claim is proposed: the reviewer should write the question and the atomic claims from the evidence. 

### Evidence (verbatim, authoritative)

```
- Raising `engines.node`, emitted JavaScript syntax, or required runtime APIs
  ships in an SDK major release by default.
```

<details><summary>Context before</summary>

```
nd Alpha releases are forward-compatibility targets,
not production support promises. This policy follows lifecycle state rather
than even or odd version numbers because every annual Node.js release beginning
with Node.js 27 is planned to become LTS.

OpenAI publishes a retirement notice at least six months before removing a
supported Node.js line. The notice belongs in the README or support matrix,
release notes, and a pinned GitHub issue. Social-media announcements are not
required. Support ends at upstream EOL by default.

The SDK and Security teams may approve up to six months of post-EOL grace when
migration risk justifies it. The exception must be recorded below with its
owner, reason, and end date. It provides only feasible SDK fixes and migration
help; OpenAI cannot provide missing upstream runtime security fixes, and the
exception may end early.

## Release and packaging rules


```

</details>

<details><summary>Context after</summary>

```
 An urgent minor-release exception
  requires SDK and Security approval. Never hide a runtime-floor change in a
  patch.
- Adding a newly promoted LTS without raising the minimum is an SDK minor.
- `engines.node` states the technical floor. The README support matrix is
  authoritative for lifecycle status because npm engine ranges cannot express
  only the currently supported LTS lines.
- Repository tooling may use a newer Node.js version than SDK consumers.
- Node.js lifecycle changes do not silently redefine TypeScript, Deno, Bun,
  browser, Workers, edge-runtime, Jest, or Nitro support.
- Required CI runs the SDK test suite on every supported Node.js line.
- Required CI builds and installs the packed npm artifact on supported lines,
  exercising CommonJS, ESM, and published engine metadata.

## Current compatibility

| Node.js line | Upstream status on 2026-07-27      | OpenAI status 
```

</details>

---

## GOLD-B001-09

- **provider**: anthropic
- **document**: Tool runner (SDK)
- **section**: Iterating over the tool runner
- **source span**: `ver_96d5aba3c4e7771cabd4f3d4f5a3fff1` chars 19885–20004
- **evidence kind**: `explicit_response`
- **binding**: single identifier in the sentence
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question about max_iterations in Tool runner (SDK), answerable from the evidence below (relationship stated: 'returns a').

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none_

**Generator notes**: Matched explicit marker 'returns a'. No claim is proposed: the reviewer should write the question and the atomic claims from the evidence. 

### Evidence (verbatim, authoritative)

```
The runner loops until Claude returns a message without a tool use, or until it reaches `max_iterations` if you set it.
```

<details><summary>Context before</summary>

```
CalculateSum.new],
      messages: [
        {role: "user", content: "What's the weather like in Paris? Also, what's 15 + 27?"}
      ]
    )

    runner.each_message do |message|
      message.content.each do |block|
        puts block.text if block.type == :text
      end
    end
    ```

    The `Anthropic::BaseTool` class uses the `doc` method for the tool description and `input_schema` to define the expected parameters. The SDK automatically converts this to the appropriate JSON schema format.
  </Tab>
</Tabs>

## Iterating over the tool runner

The tool runner is an iterable that yields messages from Claude. On each iteration, the runner checks whether Claude requested a tool use. If so, it runs the tool and sends the result back to Claude automatically, then yields the next message from Claude to continue your loop.

You can end the loop at any iteration with a `break` statement. 
```

</details>

<details><summary>Context after</summary>

```


If you don't need intermediate messages, you can get the final message directly:

<Tabs>
  <Tab title="Python">
    Use `runner.until_done()` to get the final message.

    ```python
    client = anthropic.Anthropic()
    # ...
    runner = client.beta.messages.tool_runner(
        model="claude-opus-5",
        max_tokens=1024,
        tools=[get_weather, calculate_sum],
        messages=[
            {
                "role": "user",
                "content": "What's the weather like in Paris? Also, what's 15 + 27?",
            }
        ],
    )
    final_message = runner.until_done()
    for block in final_message.content:
        if block.type == "text":
            print(block.text)
    ```
  </Tab>

  <Tab title="TypeScript">
    `await` the runner to get the final message.

    ```typescript
    const client = new Anthropic();
    // ...
    const runner = client.beta.message
```

</details>

---

## GOLD-B001-10

- **provider**: openai
- **document**: OpenAI TypeScript and JavaScript API Library
- **section**: OpenAI TypeScript and JavaScript API Library › Usage › Multi-turn conversations
- **source span**: `ver_f30a6447e4df2ab76e4c1475f353109c` chars 1631–1753
- **evidence kind**: `explicit_required_optional`
- **binding**: single identifier in the sentence
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question about response.output in OpenAI TypeScript and JavaScript API Library, answerable from the evidence below (relationship stated: 'required').

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none_

**Generator notes**: Matched explicit marker 'required'. No claim is proposed: the reviewer should write the question and the atomic claims from the evidence. 

### Evidence (verbatim, authoritative)

```
Filtering
`response.output` to messages can drop required reasoning or tool-call items and cause the next request to
fail.
```

<details><summary>Context before</summary>

```
nAI from 'npm:openai';
```

## Usage

The full API of this library can be found in [api.md file](api.md) along with many [code examples](https://github.com/openai/openai-node/tree/main/examples).

The primary API for interacting with OpenAI models is the [Responses API](https://platform.openai.com/docs/api-reference/responses). You can generate text from the model with the code below.

```ts
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: process.env['OPENAI_API_KEY'], // This is the default and can be omitted
});

const response = await client.responses.create({
  model: 'gpt-5.5',
  instructions: 'You are a coding assistant that talks like a pirate',
  input: 'Are semicolons optional in JavaScript?',
});

console.log(response.output_text);
```

### Multi-turn conversations

When you manage Responses API conversation history manually, preserve output items in order. 
```

</details>

<details><summary>Context after</summary>

```


Use the SDK's `toResponseInputItems()` helper to normalize all replayable output items before adding them to
the next request. For simple continuation, you can pass `previous_response_id` instead.

See the [manual conversation state example](examples/responses/manual-conversation-state.ts) and
[conversation state guide](https://developers.openai.com/api/docs/guides/conversation-state).

The previous standard (supported indefinitely) for generating text is the [Chat Completions API](https://platform.openai.com/docs/api-reference/chat). You can use that API to generate text from the model with the code below.

```ts
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: process.env['OPENAI_API_KEY'], // This is the default and can be omitted
});

const completion = await client.chat.completions.create({
  model: 'gpt-5.5',
  messages: [
    { role: 'developer', content: 'Tal
```

</details>

---

## GOLD-B001-11

- **provider**: anthropic
- **document**: Tutorial: Build a tool-using agent
- **section**: Ring 4: Error handling
- **source span**: `ver_fc127d394b32ba1f136356d746c083e5` chars 103289–103388
- **evidence kind**: `explicit_exception`
- **binding**: single identifier in the sentence
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question about is_error in Tutorial: Build a tool-using agent, answerable from the evidence below (relationship stated: 'raises').

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none_

**Generator notes**: Matched explicit marker 'raises'. No claim is proposed: the reviewer should write the question and the atomic claims from the evidence. 

### Evidence (verbatim, authoritative)

```
When a tool raises an error, send the error message back with `is_error: true` instead of crashing.
```

<details><summary>Context before</summary>

```
nput)
      }
    end

    messages << {role: "assistant", content: response.content}
    messages << {role: "user", content: tool_results}

    response = client.messages.create(
      model: "claude-opus-5",
      max_tokens: 1024,
      tools: tools,
      messages: messages
    )
  end

  response.content.each do |block|
    puts block.text if block.type == :text
  end
  ```
</CodeGroup>

**What to expect**

```text Output wrap
I checked your calendar for next Monday and found an existing meeting from 2pm to 3pm. I've scheduled the planning session for 10am to 11am to avoid the conflict.
```

For more on concurrent execution and ordering guarantees, see [Parallel tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use).

## Ring 4: Error handling

Tools fail. A calendar API might reject an event with too many attendees, or a date might be malformed. 
```

</details>

<details><summary>Context after</summary>

```
 Claude reads the error and can retry with corrected input, ask the user for clarification, or explain the limitation.

<CodeGroup>
  ```bash cURL
  #!/bin/bash
  # Ring 4: Error handling.

  TOOLS='[
    {
      "name": "create_calendar_event",
      "description": "Create a calendar event with attendees and optional recurrence.",
      "input_schema": {
        "type": "object",
        "properties": {
          "title": {"type": "string"},
          "start": {"type": "string", "format": "date-time"},
          "end": {"type": "string", "format": "date-time"},
          "attendees": {"type": "array", "items": {"type": "string", "format": "email"}},
          "recurrence": {
            "type": "object",
            "properties": {
              "frequency": {"enum": ["daily", "weekly", "monthly"]},
              "count": {"type": "integer", "minimum": 1}
            }
          }
     
```

</details>

---

## GOLD-B001-12

- **provider**: openai
- **document**: Handoffs
- **section**: (1)! › Customizing handoffs via the `handoff()` function
- **source span**: `ver_1c77f33b04ffffa285ea7e61c2a89653` chars 2603–2846
- **evidence kind**: `explicit_response`
- **binding**: single identifier in the sentence
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question about nest_handoff_history in Handoffs, answerable from the evidence below (relationship stated: 'returns a').

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none_

**Generator notes**: Matched explicit marker 'returns a'. No claim is proposed: the reviewer should write the question and the atomic claims from the evidence. 

### Evidence (verbatim, authoritative)

```
This can be a boolean or a function that returns a boolean, allowing you to dynamically enable or disable the handoff at runtime.
-   `nest_handoff_history`: Optional per-handoff override for the RunConfig-level `nest_handoff_history` setting.
```

<details><summary>Context before</summary>

```
will be handed off.
-   `tool_name_override`: By default, the `Handoff.default_tool_name()` function is used, which resolves to `transfer_to_<agent_name>`. You can override this.
-   `tool_description_override`: Override the default tool description from `Handoff.default_tool_description()`
-   `on_handoff`: A callback function executed when the handoff is invoked. This is useful for things like kicking off some data fetching as soon as you know a handoff is being invoked. This function receives the agent context, and can optionally also receive LLM generated input. The input data is controlled by the `input_type` param.
-   `input_type`: The schema for the handoff tool-call arguments. When set, the parsed payload is passed to `on_handoff`.
-   `input_filter`: This lets you filter the input received by the next agent. See below for more.
-   `is_enabled`: Whether the handoff is enabled. 
```

</details>

<details><summary>Context after</summary>

```
 If `None`, the value defined in the active run configuration is used instead.

The [`handoff()`][agents.handoffs.handoff] helper always transfers control to the specific `agent` you passed in. If you have multiple possible destinations, register one handoff per destination and let the model choose among them. Use a custom [`Handoff`][agents.handoffs.Handoff] only when your own handoff code must decide which agent to return at invocation time.

```python
from agents import Agent, handoff, RunContextWrapper

def on_handoff(ctx: RunContextWrapper[None]):
    print("Handoff called")

agent = Agent(name="My agent")

handoff_obj = handoff(
    agent=agent,
    on_handoff=on_handoff,
    tool_name_override="custom_handoff_tool",
    tool_description_override="Custom description",
)
```

## Handoff inputs

In certain situations, you want the LLM to provide some data when it calls a handoff. For
```

</details>

---

## GOLD-B001-13

- **provider**: anthropic
- **document**: Claude on Google Cloud
- **section**: Preamble
- **source span**: `ver_e312b7f41115cc2b84cd36151efc6dd8` chars 519–725
- **evidence kind**: `explicit_constraint`
- **binding**: single identifier in the sentence
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question about anthropic_version in Claude on Google Cloud, answerable from the evidence below (relationship stated: 'must be').

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none_

**Generator notes**: Matched explicit marker 'must be'. No claim is proposed: the reviewer should write the question and the atomic claims from the evidence. 

### Evidence (verbatim, authoritative)

```
Instead, it is specified in the Google Cloud endpoint URL.
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

* On Agent Platform, `model` is not passed in the request body. 
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

## GOLD-B001-14

- **provider**: anthropic
- **document**: Claude API errors
- **section**: Common validation errors › Prefill not supported
- **source span**: `ver_0774ca0093ff4a846753577c9a4a39d5` chars 19189–19308
- **evidence kind**: `explicit_response`
- **binding**: single identifier in the sentence
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question about invalid_request_error in Claude API errors, answerable from the evidence below (relationship stated: 'returns a').

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none_

**Generator notes**: Matched explicit marker 'returns a'. No claim is proposed: the reviewer should write the question and the atomic claims from the evidence. 

### Evidence (verbatim, authoritative)

```
Sending a request with a prefilled last assistant message to any of these models returns a 400 `invalid_request_error`:
```

<details><summary>Context before</summary>

```
umulator = MessageAccumulator::forMessages();
  foreach ($stream as $event) {
      $accumulator->accumulate($event);
  }

  echo array_find($accumulator->message()->content, static fn ($block): bool => $block->type === 'text')->text;
  ```

  ```ruby Ruby
  client = Anthropic::Client.new

  message = client.messages.stream(
    model: "claude-sonnet-5",
    max_tokens: 128000,
    messages: [{ role: "user", content: "Write a detailed analysis..." }]
  ).accumulated_message

  puts message.content.find { it.type == :text }.text
  ```
</CodeGroup>

See [Streaming Messages](https://platform.claude.com/docs/en/build-with-claude/streaming#get-the-final-message-without-handling-events) for more details.

## Common validation errors

### Prefill not supported

Claude 4.6 and later models and [Claude Mythos Preview](https://anthropic.com/glasswing) do not support prefilling assistant messages. 
```

</details>

<details><summary>Context after</summary>

```


```json
{
  "type": "error",
  "error": {
    "type": "invalid_request_error",
    "message": "This model does not support assistant message prefill. The conversation must end with a user message."
  }
}
```

Use [structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) on models that support it, system prompt instructions, or [`output_config.format`](https://platform.claude.com/docs/en/build-with-claude/structured-outputs#json-outputs) instead.

### Thinking blocks cannot be modified

If the most recent assistant message contains `thinking` or `redacted_thinking` blocks that were edited, reordered, filtered out, or reconstructed before being sent back to the API, the request returns a 400 `invalid_request_error`. The error message starts with the position of the offending block (for example, `messages.1.content.0`) and contains:

```text wrap
`thin
```

</details>

---

## GOLD-B001-15

- **provider**: anthropic
- **document**: Streaming messages
- **section**: Full HTTP stream response › Streaming request with tool use
- **source span**: `ver_1261879c16f641270789647ac9c63c96` chars 19561–19921
- **evidence kind**: `explicit_required_optional`
- **binding**: single identifier in the sentence
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question about tool_choice in Streaming messages, answerable from the evidence below (relationship stated: 'required').

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none_

**Generator notes**: Matched explicit marker 'required'. No claim is proposed: the reviewer should write the question and the atomic claims from the evidence. 

### Evidence (verbatim, authoritative)

```
San Francisco, CA"
                }
              },
              "required": ["location"]
            }
          }
        ],
        "tool_choice": {"type": "any"},
        "messages": [
          {
            "role": "user",
            "content": "What is the weather like in San Francisco?"
          }
        ],
        "stream": true
      }'
  ```
```

<details><summary>Context before</summary>

```
orts [fine-grained streaming](https://platform.claude.com/docs/en/agents-and-tools/tool-use/fine-grained-tool-streaming) for parameter values. Enable it per tool with `eager_input_streaming`.
</Tip>

This request asks Claude to use a tool to report the weather.

<CodeGroup>
  ```bash cURL
    curl https://api.anthropic.com/v1/messages \
      -H "content-type: application/json" \
      -H "x-api-key: $ANTHROPIC_API_KEY" \
      -H "anthropic-version: 2023-06-01" \
      -d '{
        "model": "claude-opus-5",
        "max_tokens": 1024,
        "tools": [
          {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "input_schema": {
              "type": "object",
              "properties": {
                "location": {
                  "type": "string",
                  "description": "The city and state, e.g. 
```

</details>

<details><summary>Context after</summary>

```


  ```bash CLI
  ant messages create --stream --format jsonl <<'YAML'
  model: claude-opus-5
  max_tokens: 1024
  tools:
    - name: get_weather
      description: Get the current weather in a given location
      input_schema:
        type: object
        properties:
          location:
            type: string
            description: The city and state, e.g. San Francisco, CA
        required:
          - location
  tool_choice:
    type: any
  messages:
    - role: user
      content: What is the weather like in San Francisco?
  YAML
  ```

  ```python Python
  client = anthropic.Anthropic()

  tools = [
      {
          "name": "get_weather",
          "description": "Get the current weather in a given location",
          "input_schema": {
              "type": "object",
              "properties": {
                  "location": {
                      "type": "string",
        
```

</details>

---

## GOLD-B001-16

- **provider**: anthropic
- **document**: Embeddings
- **section**: and cosine similarity are the same. › FAQ
- **source span**: `ver_26f61f56d6ff7124cfa38152f7baef3d` chars 22027–22317
- **evidence kind**: `explicit_exception`
- **binding**: single identifier in the sentence
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question about row_norms in Embeddings, answerable from the evidence below (relationship stated: 'raises').

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none_

**Generator notes**: Matched explicit marker 'raises'. No claim is proposed: the reviewer should write the question and the atomic claims from the evidence. 

### Evidence (verbatim, authoritative)

```
Raises a ValueError if any row has a norm of zero to prevent division by zero.
        """
        row_norms = np.linalg.norm(v, axis=1, keepdims=True)
        if np.any(row_norms == 0):
            raise ValueError("Cannot normalize rows with a norm of zero.")
        return v / row_norms
```

<details><summary>Context before</summary>

```
 integer (`uint8`) 77.
    > * `binary`: The binary sequence is represented as the signed integer (`int8`) -51, calculated using the offset binary method (77 - 128 = -51).
  </Accordion>

  <Accordion title="How can I truncate Matryoshka embeddings?">
    Matryoshka learning creates embeddings with coarse-to-fine representations within a single vector. Voyage models, such as `voyage-code-3`, that support multiple output dimensions generate such Matryoshka embeddings. You can truncate these vectors by keeping the leading subset of dimensions. For example, the following Python code demonstrates how to truncate 1024-dimensional vectors to 256 dimensions:

    ```python
    import voyageai
    import numpy as np


    def embd_normalize(v: np.ndarray) -> np.ndarray:
        """
        Normalize the rows of a 2D numpy array to unit vectors by dividing each row by its Euclidean
        norm. 
```

</details>

<details><summary>Context after</summary>

```



    vo = voyageai.Client()

    # Generate voyage-code-3 vectors, which by default are 1024-dimensional floating-point numbers
    embd = vo.embed(["Sample text 1", "Sample text 2"], model="voyage-code-3").embeddings

    # Set shorter dimension
    short_dim = 256

    # Resize and normalize vectors to shorter dimension
    resized_embd = embd_normalize(np.array(embd)[:, :short_dim]).tolist()
    ```
  </Accordion>
</AccordionGroup>

## Pricing

Visit Voyage's [pricing page](https://docs.voyageai.com/docs/pricing?ref=anthropic) for the most up to date pricing details.

```

</details>

---

## GOLD-B001-17

- **provider**: anthropic
- **document**: Files API
- **section**: Error handling
- **source span**: `ver_ab9e2c2bf4c17bf70ce1b94355d01729` chars 29836–30171
- **evidence kind**: `explicit_constraint`
- **binding**: single identifier in the sentence
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question about file_id in Files API, answerable from the evidence below (relationship stated: 'cannot be').

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none_

**Generator notes**: Matched explicit marker 'cannot be'. No claim is proposed: the reviewer should write the question and the atomic claims from the evidence. 

### Evidence (verbatim, authoritative)

```
* **File not found (404):** The specified `file_id` doesn't exist or you don't have access to it
* **Invalid file type (400):** The file type doesn't match the content block type (for example, using an image file in a document block)
* **Not downloadable (400):** Files you upload have `"downloadable": false` and cannot be downloaded.
```

<details><summary>Context before</summary>

```
 [workspace access warning](https://platform.claude.com/docs/en/build-with-claude/files#workspace-scoped-access))
* Files cannot be modified or renamed after upload. To change a file's content, upload a new file and delete the old one
* Files persist until you delete them with the `DELETE /v1/files/{file_id}` endpoint
* Deleted files cannot be recovered
* Files are inaccessible through the API shortly after deletion, but they may persist in active Messages API calls and associated tool uses
* Files that users delete will be deleted in accordance with Anthropic's [data retention policy](https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data). For ZDR eligibility across all features, see [API and data retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)

## Error handling

Common errors when using the Files API include:


```

</details>

<details><summary>Context after</summary>

```
 Only files created by skills or the code execution tool can be downloaded
* **Exceeds context window size (400):** The file is larger than the context window size (for example, using a 500 MB plain text file in a `/v1/messages` request)
* **Invalid filename (400):** The file name doesn't meet the length requirements (1-255 characters) or contains forbidden characters (`<`, `>`, `:`, `"`, `|`, `?`, `*`, `\`, `/`, or Unicode characters 0-31)
* **File too large (413):** File exceeds the 500 MB limit
* **Storage limit exceeded (400):** Your organization has reached the 500 GB storage limit

```json Output
{
  "type": "error",
  "error": {
    "type": "not_found_error",
    "message": "File `file_011CNha8iCJcU1wXNR6q4V8w` not found."
  },
  "request_id": "req_011CQFYcrRp7mCHLDsAYT8Qt"
}
```

## Usage and billing

Files API operations are free:

* Uploading files
* Downloading files
* Listing
```

</details>

---

## GOLD-B001-18

- **provider**: anthropic
- **document**: Tool reference
- **section**: Tool definition properties › `defer_loading` and prompt caching
- **source span**: `ver_5f5df502fc725ffcca9d893fef90fe3f` chars 11593–11779
- **evidence kind**: `explicit_response`
- **binding**: single identifier in the sentence
- **generator confidence**: medium
- **needs human interpretation**: True

**Proposed question** (a suggestion, not gold)

> [REVIEWER TO WRITE] A question about tool_reference in Tool reference, answerable from the evidence below (relationship stated: 'returns a').

**Proposed answer**: _none — reviewer to write_

**Proposed atomic claims**: _none_

**Generator notes**: Matched explicit marker 'returns a'. No claim is proposed: the reviewer should write the question and the atomic claims from the evidence. 

### Evidence (verbatim, authoritative)

```
When tool search discovers a deferred tool and returns a `tool_reference` for it, the tool's full definition is expanded inline at that point in the conversation body, not in the prefix.
```

<details><summary>Context before</summary>

```
ng either code-execution tool version satisfies tools that list either caller. Response blocks always tag the caller as `code_execution_20260120` regardless of which version the request declared.

Omitting `"direct"` from the array (for example, `"allowed_callers": ["code_execution_20260120"]`) guides Claude to call the tool only from within code execution. The response's `tool_use` block includes a `caller` field that identifies which caller called the tool. See [Programmatic tool calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling#the-allowed-callers-field) for the full treatment, including the `caller` response shape and error behavior.

### `defer_loading` and prompt caching

Tools with `defer_loading: true` are stripped from the rendered tools section before the cache key is computed. They don't appear in the system-prompt prefix at all. 
```

</details>

<details><summary>Context after</summary>

```


This means `defer_loading: true` preserves your prompt cache. You can add deferred tools to a request without invalidating an existing cache entry, and the cache remains valid across the turn where the tool is discovered and the turn where it's called.

For how to combine `defer_loading` with `cache_control` breakpoints, see the [Tool search tool prompt caching guidance](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool#prompt-caching).

```

</details>

---
