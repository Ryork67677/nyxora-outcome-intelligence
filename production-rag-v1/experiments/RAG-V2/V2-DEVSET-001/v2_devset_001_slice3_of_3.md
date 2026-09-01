# V2-DEVSET-001 review packet (batch 101)

**14 candidates (slice3_of_3: V2D-37–V2D-50 of 50) · corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · generated 2026-09-01T02:20:09Z (2026-08-31 22:20 ET)**

Nothing in this file is ground truth. Every candidate is `candidate_unverified`. The evidence below is quoted verbatim from the frozen corpus and is authoritative for this review — **do not consult live documentation**, which may have changed since the snapshot.

For each candidate, judge the *proposed* question, answer and claims against the evidence and its surrounding context only. Return one record per candidate with verdict `PASS | FAIL | FIX_REQUIRED | UNCERTAIN` and the GOLD review fields in `docs/GOLD-REVIEW-PROCEDURE.md`.

ID prefix `V2D-`. This is a v2 **development** candidate set, not frozen gold, not gold150-v1 holdout, and not gold150-v1 validation.

---

## V2D-37

- **provider**: openai
- **document**: OpenAI Python API library
- **section**: Remove `await` for non-async usage. › File uploads
- **source span**: `ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` chars 14166–14318
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, paraphrase_query_shape, same_document_passage_discrimination
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens if you pass a `PathLike` instance?

**Proposed answer**: The file contents will be read asynchronously automatically.

**Proposed atomic claims**: If you pass a [`PathLike`](https://docs.python.org/3/library/os.html#os.PathLike) instance, the file contents will be read asynchronously automatically.

**Critical strings**: PathLike

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` chars 14166–14318 · hash `c7de0d42f68c2ceb…`

```
If you pass a [`PathLike`](https://docs.python.org/3/library/os.html#os.PathLike) instance, the file contents will be read asynchronously automatically.
```

<details><summary>Context before</summary>

```
r: ..."
for job in first_page.data:
    print(job.id)

# Remove `await` for non-async usage.
```

## Nested params

Nested parameters are dictionaries, typed using `TypedDict`, for example:

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    input=[
        {
            "role": "user",
            "content": "How much ?",
        }
    ],
    model="gpt-5.5",
    text={"format": {"type": "json_object"}},
)
```

## File uploads

Request parameters that correspond to file uploads can be passed as `bytes`, or a [`PathLike`](https://docs.python.org/3/library/os.html#os.PathLike) instance or a tuple of `(filename, contents, media type)`.

```python
from pathlib import Path
from openai import OpenAI

client = OpenAI()

client.files.create(
    file=Path("input.jsonl"),
    purpose="fine-tune",
)
```

The async client uses the exact same interface. 
```

</details>

<details><summary>Context after</summary>

```


## Webhook Verification

Verifying webhook signatures is _optional but encouraged_.

For more information about webhooks, see [the API docs](https://platform.openai.com/docs/guides/webhooks).

### Parsing webhook payloads

For most use cases, you will likely want to verify the webhook and parse the payload at the same time. To achieve this, we provide the method `client.webhooks.unwrap()`, which parses a webhook request and verifies that it was sent by OpenAI. This method will raise an error if the signature is invalid.

Note that the `body` parameter must be the raw JSON string sent from the server (do not parse it first). The `.unwrap()` method will parse this JSON for you into an event object after verifying the webhook was sent from OpenAI.

```python
from openai import OpenAI
from flask import Flask, request

app = Flask(__name__)
client = OpenAI()  # OPENAI_WEBHOOK_SECRET environ
```

</details>

---

## V2D-38

- **provider**: anthropic
- **document**: Prompting Claude Opus 4.8
- **section**: Design and frontend defaults
- **source span**: `ver_997f51c850a46243a541d4f4ec4175ce` chars 10771–10910
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens if you previously relied on `temperature` for design variety?

**Proposed answer**: Use this approach; it produces meaningfully different directions across runs.

**Proposed atomic claims**: If you previously relied on `temperature` for design variety, use this approach; it produces meaningfully different directions across runs.

**Critical strings**: temperature

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_997f51c850a46243a541d4f4ec4175ce` chars 10771–10910 · hash `7c2fd69c00251dc1…`

```
If you previously relied on `temperature` for design variety, use this approach; it produces meaningfully different directions across runs.
```

<details><summary>Context before</summary>

```
ss compressed. Headline text can be large and uppercase, while supporting copy remains short and sparse. The sub texts should be written with Alumni Sans SC in 4-6px like tiny little texts on corners bottom centre like that.

For the structure, start with a hero section containing a strong product statement, one short supporting paragraph, and a clean product placeholder or packshot frame. Below that, add a benefit grid with three or four blocks, then a formulation or ingredients section, and finally a cta.

Buttons should be flat and precise, with subtle hover changes using transition: all 160ms ease out where brightness and border contrast shift slightly rather than using dramatic motion.

Color palette should stay within this range:
#E9ECEC, #C9D2D4, #8C9A9E, #44545B, #11171B.
```

**2. Have the model propose options before building.** This breaks the default and gives users control. 
```

</details>

<details><summary>Context after</summary>

```
 Example prompt:

```text wrap
Before building, propose 4 distinct visual directions tailored to this brief (each as: bg hex / accent hex / typeface — one-line rationale). Ask the user to pick one, then implement only that direction.
```

Additionally, Claude Opus 4.8 requires less frontend design prompting than previous models to avoid generic patterns that users call the "AI slop" aesthetic. With earlier models, Anthropic recommended a lengthier prompt snippet in the [frontend-design skill](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md). However, Claude Opus 4.8 generates distinctive, creative frontends with more minimal prompting guidance. This prompt snippet works well with the preceding prompting advice for variety:

```text wrap
<frontend_aesthetics>
NEVER use generic AI-generated aesthetics like overused font families (
```

</details>

---

## V2D-39

- **provider**: anthropic
- **document**: Compaction
- **section**: Parameters
- **source span**: `ver_c60f7418b69b6610bd20e974b92cdd8c` chars 9649–9854
- **evidence kind**: `parameter_table_row`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: parameter_error_literal_lookup, identifier_vs_semantic_distractor, same_document_passage_discrimination
- **binding**: structural: parameter is the row's first cell, type is another cell of the same row
- **generator confidence**: high
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What type does the `instructions` parameter take?

**Proposed answer**: `string`

**Proposed atomic claims**: ``instructions` is of type string.`

**Critical strings**: instructions, string

**Generator notes**: Row-scoped association. Reviewer should confirm the table is a parameter table and that the column header means the parameter's own type rather than, say, a return type. FLAG_LOW_VALUE

### Evidence E1 (verbatim, authoritative)

`ver_c60f7418b69b6610bd20e974b92cdd8c` chars 9649–9854 · hash `9f9b8324df15d3af…`

```
| `instructions`           | string  | `null`                                      | Custom summarization prompt. Completely replaces the default prompt when provided.                                     |
```

<details><summary>Context before</summary>

```
                                                                          |
| ------------------------ | ------- | ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `type`                   | string  | Required                                    | Must be `"compact_20260112"`                                                                                           |
| `trigger`                | object  | `{"type": "input_tokens", "value": 150000}` | When to trigger compaction. `input_tokens` is the only supported trigger type. `value` must be at least 50,000 tokens. |
| `pause_after_compaction` | boolean | `false`                                     | Whether to pause after generating the compaction summary                                                               |

```

</details>

<details><summary>Context after</summary>

```


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
              "value": 150000
            }
          }
        ]
      }
    }'
  ```

  ```bash CLI
  ant beta:messages create --beta compact-2026-01-12 <<'YAML'
  model: claude-opus-5
  max_tokens: 4096
  messages
```

</details>

---

## V2D-40

- **provider**: anthropic
- **document**: Trigger a routine through the API
- **section**: Trigger a routine › Response
- **source span**: `ver_d81ee605bd8bbb880deea432e51462ac` chars 9300–9461
- **evidence kind**: `parameter_table_row`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, version_model_discrimination, parameter_error_literal_lookup, identifier_vs_semantic_distractor, lexical_query_shape
- **binding**: structural: parameter is the row's first cell, type is another cell of the same row
- **generator confidence**: high
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What type does the `claude_code_session_id` parameter take?

**Proposed answer**: `string`

**Proposed atomic claims**: ``claude_code_session_id` is of type string.`

**Critical strings**: claude_code_session_id, string

**Generator notes**: Row-scoped association. Reviewer should confirm the table is a parameter table and that the column header means the parameter's own type rather than, say, a return type. FLAG_LOW_VALUE

### Evidence E1 (verbatim, authoritative)

`ver_d81ee605bd8bbb880deea432e51462ac` chars 9300–9461 · hash `6fc84fb57bf1faad…`

```
| `claude_code_session_id`  | string | The ID of the Claude Code session created for this run.                                                                  |
```

<details><summary>Context before</summary>

```
. Passed to the routine alongside its saved prompt. Maximum 65,536 characters. |

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

```

</details>

<details><summary>Context after</summary>

```

| `claude_code_session_url` | string | A link to the session on claude.ai. Open it in a browser to watch the run, review changes, or continue the conversation. |

### Errors

Errors use the standard Anthropic [error envelope](https://platform.claude.com/docs/en/api/errors):

```json
{
  "type": "error",
  "error": {
    "type": "not_found_error",
    "message": "<string>"
  }
}
```

| HTTP status | Error type              | Cause                                                                                                                                                                                                         |
| ----------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 400        
```

</details>

---

## V2D-41

- **provider**: openai
- **document**: Release process/changelog
- **section**: Release process/changelog › Breaking change changelog › 0.21.0
- **source span**: `ver_de67d790db9792b2f6c5c7418a507764` chars 745–843
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, version_model_discrimination, same_document_passage_discrimination
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does Version 0.21.0 require?

**Proposed answer**: Version 0.21.0 requires `openai` v3 and moves the Agents SDK's OpenAI HTTP integrations to HTTPX2.

**Proposed atomic claims**: Version 0.21.0 requires `openai` v3 and moves the Agents SDK's OpenAI HTTP integrations to HTTPX2.

**Critical strings**: openai

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_de67d790db9792b2f6c5c7418a507764` chars 745–843 · hash `3fd0bfd40ca4fc70…`

```
Version 0.21.0 requires `openai` v3 and moves the Agents SDK's OpenAI HTTP integrations to HTTPX2.
```

<details><summary>Context before</summary>

```
# Release process/changelog

The project follows a slightly modified version of semantic versioning using the form `0.Y.Z`. The leading `0` indicates the SDK is still evolving rapidly. Increment the components as follows:

## Minor (`Y`) versions

We will increase minor versions `Y` for **breaking changes** to any public interfaces that are not marked as beta. For example, going from `0.0.x` to `0.1.x` might include breaking changes.

If you don't want breaking changes, we recommend pinning to `0.0.x` versions in your project.

## Patch (`Z`) versions

We will increment `Z` for non-breaking changes:

-   Bug fixes
-   New features
-   Changes to private interfaces
-   Updates to beta features

## Breaking change changelog

### 0.21.0


```

</details>

<details><summary>Context after</summary>

```
 Applications that use the default OpenAI client do not need to change their client setup, but applications that customize the OpenAI HTTP layer may need to migrate transport-facing code.

Highlights:

-   The required OpenAI dependency is now `openai>=3.0.0,<4`. A clean core installation uses HTTPX2 and no longer installs legacy `httpx` as a direct dependency.
-   The default OpenAI provider, Voice provider, Responses WebSocket support, tracing exporter, and provider retry normalization now use HTTPX2. Their existing Agents SDK public configuration and runtime behavior remain unchanged.
-   Applications that pass `http_client=` to `AsyncOpenAI` should migrate custom clients, transports, authentication, event hooks, mock transports, timeout values, URLs, requests, responses, and transport exception handling from `httpx` to `httpx2`. Prefer the OpenAI Python SDK's `DefaultAsyncHttpx2Clien
```

</details>

---

## V2D-42

- **provider**: anthropic
- **document**: Get started with Claude
- **section**: Call the API
- **source span**: `ver_e207dcf70119ccde7d6f7f9b9ab55676` chars 2866–2964
- **evidence kind**: `normative_statement`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, identifier_vs_semantic_distractor, lexical_query_shape, paraphrase_query_shape
- **binding**: template-captured-groups
- **generator confidence**: high
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens when `ANTHROPIC_API_KEY` is set in your environment?

**Proposed answer**: It takes precedence over the login credentials.

**Proposed atomic claims**: When `ANTHROPIC_API_KEY` is set in your environment, it takes precedence over the login credentials.

**Critical strings**: ANTHROPIC_API_KEY

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_e207dcf70119ccde7d6f7f9b9ab55676` chars 2866–2964 · hash `29fce2c334b8a4ec…`

```
If `ANTHROPIC_API_KEY` is set in your environment, it takes precedence over the login credentials.
```

<details><summary>Context before</summary>

```
put_tokens": 305
          }
        }
        ```
      </Step>
    </Steps>
  </Tab>

  <Tab title="CLI">
    <Steps>
      <Step title="Install the CLI">
        Install the Anthropic CLI with Homebrew:

        ```bash
        brew install anthropics/tap/ant
        ```

        For other installation methods, see [Installation](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart#installation) in the CLI quickstart.
      </Step>

      <Step title="Authenticate">
        Log in with your Anthropic account:

        ```bash
        ant auth login
        ```

        This opens a browser-based OAuth flow. After authorizing, confirm your credential with:

        ```bash
        ant auth status
        ```

        On a remote host without a browser, pass `--no-browser` to get a URL you can open on another device, then paste the returned code back into the terminal. 
```

</details>

<details><summary>Context after</summary>

```
 For non-interactive environments such as CI, see [CLI authentication options](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/authentication).
      </Step>

      <Step title="Make your first API call">
        Run `ant messages create` from your terminal:

        ```bash CLI
        ant messages create \
          --model claude-opus-5 \
          --max-tokens 1000 \
          --message '{
            role: user,
            content: "What should I search for to find the latest developments in renewable energy?"
          }'
        ```

        The CLI prints the JSON response:

        ```json Output
        {
          "model": "claude-opus-5",
          "id": "msg_01N1ycuCkM5Mzd7WhTU4fwST",
          "type": "message",
          "role": "assistant",
          "content": [
            {
              "type": "text",
              "text": "Here are some effective search 
```

</details>

---

## V2D-43

- **provider**: openai
- **document**: Release process/changelog
- **section**: Release process/changelog › Breaking change changelog › 0.20.0
- **source span**: `ver_de67d790db9792b2f6c5c7418a507764` chars 3830–3917
- **evidence kind**: `normative_statement`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, identifier_vs_semantic_distractor, same_document_passage_discrimination
- **binding**: template-captured-groups
- **generator confidence**: high
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does `audio.input.turn_detection=None` disable?

**Proposed answer**: Automatic turn detection.

**Proposed atomic claims**: ``audio.input.turn_detection=None` disables automatic turn detection.`

**Critical strings**: audio.input.turn_detection=None

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_de67d790db9792b2f6c5c7418a507764` chars 3830–3917 · hash `c6cb7a177bf11adf…`

```
Setting `audio.input.turn_detection=None` explicitly disables automatic turn detection.
```

<details><summary>Context before</summary>

```
n agent or run does not explicitly select one.

Highlights:

-   The SDK default model is now `gpt-5.6-luna` instead of `gpt-5.4-mini`. The default `reasoning.effort="none"` and `verbosity="low"` settings are unchanged.
-   Explicit agent models, run-level model overrides, and the `OPENAI_DEFAULT_MODEL` environment variable continue to take precedence over the SDK default.
-   Realtime input transcription settings now recognize `gpt-transcribe`, `gpt-live-transcribe`, and `gpt-realtime-whisper`. For low-latency `gpt-live-transcribe` sessions, nested `audio.input.transcription` settings can supply `prompt`, `keywords`, and multiple expected `languages`. The OpenAI client version pinned by this SDK supports the `delay` latency/accuracy level only with `gpt-realtime-whisper`. Use `gpt-transcribe` over WebSocket for transcription after a committed audio turn or for detected-language output. 
```

</details>

<details><summary>Context after</summary>

```
 See [Input transcription settings](realtime/guide.md#input-transcription-settings).
-   Local MCP connections created by the Agents SDK now support MCP Python SDK v2 while retaining v1 compatibility through `mcp>=1.19.0,<3`. The Agents SDK adapts ordinary stdio, SSE, and Streamable HTTP connections automatically. With MCP v2 installed, these connections use `mcp.Client(mode="auto")` to probe the newest supported protocol and fall back to the legacy `initialize` handshake for older servers. If dependency resolution selects MCP v2, applications that supply custom `httpx.Auth` objects or `httpx.AsyncClient` factories must migrate those values to `httpx2`, or pin `mcp<2` to retain the v1 HTTP stack. `MCPServerStreamableHttp`'s `params["ignore_initialized_notification_failure"] = True` option also remains v1-only. See [MCP Python SDK v1 and v2](mcp.md#mcp-python-sdk-v1-and-v2) for migration 
```

</details>

---

## V2D-44

- **provider**: openai
- **document**: Usage
- **section**: Usage › Preserving provider usage payloads
- **source span**: `ver_f8002fe268b970eaea8d640f9dd91fb3` chars 4145–4269
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does When a streaming Chat Completions provider require?

**Proposed answer**: When a streaming Chat Completions provider requires an explicit usage request, also set `ModelSettings(include_usage=True)`.

**Proposed atomic claims**: When a streaming Chat Completions provider requires an explicit usage request, also set `ModelSettings(include_usage=True)`.

**Critical strings**: include_usage

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_f8002fe268b970eaea8d640f9dd91fb3` chars 4145–4269 · hash `aa1600091e56a6fb…`

```
When a streaming Chat Completions provider requires an explicit usage request, also set `ModelSettings(include_usage=True)`.
```

<details><summary>Context before</summary>

```
field from a provider-reported zero:

```python
from agents import Agent, ModelSettings, Runner

agent = Agent(
    name="Assistant",
    model_settings=ModelSettings(preserve_raw_usage=True),
)
result = await Runner.run(agent, "What's the weather in Tokyo?")

for response in result.raw_responses:
    print(response.raw_usage)
```

The Agents SDK stores each [`ModelResponse.raw_usage`][agents.items.ModelResponse.raw_usage] value as a detached, JSON-compatible snapshot of the provider payload for that model call. The Agents SDK does not aggregate `raw_usage` across the run. The value remains `None` when preservation is disabled, the provider returns no usage payload, or an upstream adapter has already discarded the original field-presence information.

`preserve_raw_usage` preserves only a usage payload that reaches the model adapter; the setting does not request usage from the provider. 
```

</details>

<details><summary>Context after</summary>

```


`LitellmModel` does not currently populate `ModelResponse.raw_usage` in either streaming or non-streaming runs, so `preserve_raw_usage=True` has no effect with that adapter. Continue to use the normalized [`Usage`][agents.usage.Usage] fields when using `LitellmModel`, or choose an adapter that supports raw usage preservation when provider-specific field presence is required.

## Accessing usage with sessions

When you use a `Session` (e.g., `SQLiteSession`), each call to `Runner.run(...)` returns usage for that specific run. Sessions maintain conversation history for context, but each run's usage is independent.

```python
session = SQLiteSession("my_conversation")

first = await Runner.run(agent, "Hi!", session=session)
print(first.context_wrapper.usage.total_tokens)  # Usage for first run

second = await Runner.run(agent, "Can you elaborate?", session=session)
print(second.context_wr
```

</details>

---

## V2D-45

- **provider**: anthropic
- **document**: Advisor tool
- **section**: How it works
- **source span**: `ver_b8b18cda9b875d51a2ce979a1bf4e909` chars 8738–8858
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, identifier_vs_semantic_distractor, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens when you add the advisor tool to your `tools` array?

**Proposed answer**: The executor model determines when to call it, like any other tool.

**Proposed atomic claims**: When you add the advisor tool to your `tools` array, the executor model determines when to call it, like any other tool.

**Critical strings**: tools

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_b8b18cda9b875d51a2ce979a1bf4e909` chars 8738–8858 · hash `cc704171126b00b0…`

```
When you add the advisor tool to your `tools` array, the executor model determines when to call it, like any other tool.
```

<details><summary>Context before</summary>

```
}
    ],
    betas: ["advisor-tool-2026-03-01"]
  )

  puts response
  ```
</CodeGroup>

The response `content` includes an `advisor_tool_result` block carrying the advisor's guidance. With `claude-opus-5` as the advisor, as in this quick start, the block's `content` field is an `advisor_redacted_result` variant (encrypted; the executor reads it server-side, but your client does not). To see the advice text directly in your response, use `claude-opus-4-8` as the advisor model instead, which returns the plaintext `advisor_result` variant. See [Result variants](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool#result-variants) for both shapes side by side and which advisor models return which, and [Model compatibility](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool#model-compatibility) for the full list of valid pairs.

## How it works


```

</details>

<details><summary>Context after</summary>

```
 When the executor calls the advisor:

1. The executor emits a [`server_tool_use`](https://platform.claude.com/docs/en/agents-and-tools/tool-use/server-tools) block with `name: "advisor"` and an empty `input`. The executor signals timing, and the server supplies context.
2. Anthropic runs a separate inference pass on the advisor model server-side. The advisor runs under its own Anthropic-supplied system prompt and receives the executor's full transcript as quoted context in its input. That transcript includes your system prompt, the tool definitions, the prior turns and tool results, and the text the executor has produced so far in this turn.
3. The advisor's response returns to the executor as an `advisor_tool_result` block.
4. The executor continues generating, informed by the advice.

All of this occurs inside a single `/v1/messages` request, with no extra round trips on your side. Th
```

</details>

---

## V2D-46

- **provider**: anthropic
- **document**: Compaction
- **section**: Working with compaction blocks › Passing compaction blocks back
- **source span**: `ver_c60f7418b69b6610bd20e974b92cdd8c` chars 53108–53193
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, paraphrase_query_shape, same_document_passage_discrimination
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens when the API receives a `compaction` block?

**Proposed answer**: All content blocks before it are ignored.

**Proposed atomic claims**: When the API receives a `compaction` block, all content blocks before it are ignored.

**Critical strings**: compaction

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_c60f7418b69b6610bd20e974b92cdd8c` chars 53108–53193 · hash `d7a977f61bc823a0…`

```
When the API receives a `compaction` block, all content blocks before it are ignored.
```

<details><summary>Context before</summary>

```
 => [['type' => 'compact_20260112']]
      ]
  );

  echo json_encode($nextResponse, JSON_PRETTY_PRINT), PHP_EOL;
  ```

  ```ruby Ruby
  client = Anthropic::Client.new

  messages = [
    { role: "user", content: "Help me build a web scraper" }
  ]

  response = client.beta.messages.create(
    betas: ["compact-2026-01-12"],
    model: "claude-opus-5",
    max_tokens: 4096,
    messages: messages,
    context_management: {
      edits: [{ type: "compact_20260112" }]
    }
  )

  messages << { role: "assistant", content: response.content }

  messages << { role: "user", content: "Now add error handling" }

  next_response = client.beta.messages.create(
    betas: ["compact-2026-01-12"],
    model: "claude-opus-5",
    max_tokens: 4096,
    messages: messages,
    context_management: {
      edits: [{ type: "compact_20260112" }]
    }
  )

  puts next_response.content
  ```
</CodeGroup>


```

</details>

<details><summary>Context after</summary>

```
 You can either:

* Keep the original messages in your list and let the API handle removing the compacted content
* Manually drop the compacted messages and only include the compaction block onwards

### Streaming

The compaction block streams differently from text blocks. You receive a `content_block_start` event, followed by a single `content_block_delta` with the complete summary content (no intermediate streaming), and then a `content_block_stop` event.

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
      "stream": true,
      "messages": [
        {
          "role": "user",
          "content": "Hello, Claude"
        }

```

</details>

---

## V2D-47

- **provider**: anthropic
- **document**: Structured outputs
- **section**: JSON outputs › Working with JSON outputs in SDKs › SDK-specific methods
- **source span**: `ver_0865c9612dfe97d8f30dd870dd12e53e` chars 41479–41565
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `configuration_interaction`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens if you use `@JsonProperty(required = false)`?

**Proposed answer**: The SDK ignores the `false` value.

**Proposed atomic claims**: If you use `@JsonProperty(required = false)`, the SDK ignores the `false` value.

**Critical strings**: false

**Generator notes**: FLAG_SUBJECT_MISMATCH

### Evidence E1 (verbatim, authoritative)

`ver_0865c9612dfe97d8f30dd870dd12e53e` chars 41479–41565 · hash `a6a6b4e7bcf0674b…`

```
      If you use `@JsonProperty(required = false)`, the SDK ignores the `false` value.
```

<details><summary>Context before</summary>

```
blic int birthYear;

        @JsonPropertyDescription("The year the person died, or 'present' if the person is living.")
        public String deathYear;
      }

      @JsonClassDescription("The details of one published book")
      static class Book {

        public String title;
        public Person author;

        @JsonPropertyDescription("The year in which the book was first published.")
        public int publicationYear;

        @JsonIgnore
        public String genre;
      }

      static class BookList {
        public List<Book> books;
      }
      ```

      Annotation summary:

      * `@JsonClassDescription`: Add a description to a class
      * `@JsonPropertyDescription`: Add a description to a field or getter method
      * `@JsonIgnore`: Exclude a `public` field or getter from the schema
      * `@JsonProperty`: Include a non-`public` field or getter in the schema


```

</details>

<details><summary>Context after</summary>

```
 Class-derived schemas always mark all properties as required.

      You can also use Swagger Core (OpenAPI 3) `@Schema` and `@ArraySchema` annotations for type-specific constraints:

      ```java
      import io.swagger.v3.oas.annotations.media.ArraySchema;
      import io.swagger.v3.oas.annotations.media.Schema;

      static class Article {

        @ArraySchema(minItems = 1)
        public List<String> authors;

        public String title;

        @Schema(format = "date")
        public String publicationDate;

        public int pageCount;
      }
      ```

      Local validation checks that you haven't used any unsupported constraint keywords, but constraint values aren't validated locally. For example, an unsupported `"format"` value may pass local validation but cause a remote error.

      If you use both Jackson and Swagger annotations to set the same schema field, the Jac
```

</details>

---

## V2D-48

- **provider**: anthropic
- **document**: Messages
- **section**: Messages › Create a Message › Body Parameters
- **source span**: `ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 1892–2020
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, identifier_vs_semantic_distractor, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens if the final message uses the `assistant` role?

**Proposed answer**: The response content will continue immediately from the content in that message.

**Proposed atomic claims**: If the final message uses the `assistant` role, the response content will continue immediately from the content in that message.

**Critical strings**: assistant

**Generator notes**: FLAG_SUBJECT_MISMATCH

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 1892–2020 · hash `5b76cb0087e5e2af…`

```
If the final message uses the `assistant` role, the response content will continue immediately from the content in that message.
```

<details><summary>Context before</summary>

```
[prompt cache](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#pre-warming-the-cache) without generating a response.

  Different models have different maximum values for this parameter.  See [models](https://platform.claude.com/docs/en/about-claude/models/overview) for details.

- `messages: array of MessageParam`

  Input messages.

  Our models are trained to operate on alternating `user` and `assistant` conversational turns. When creating a new `Message`, you specify the prior conversational turns with the `messages` parameter, and the model then generates the next `Message` in the conversation. Consecutive `user` or `assistant` turns in your request will be combined into a single turn.

  Each input message must be an object with a `role` and `content`. You can specify a single `user`-role message, or you can include multiple `user` and `assistant` messages.

  
```

</details>

<details><summary>Context after</summary>

```
 This can be used to constrain part of the model's response.

  Example with a single `user` message:

  ```json
  [{"role": "user", "content": "Hello, Claude"}]
  ```

  Example with multiple conversational turns:

  ```json
  [
    {"role": "user", "content": "Hello there."},
    {"role": "assistant", "content": "Hi, I'm Claude. How can I help you?"},
    {"role": "user", "content": "Can you explain LLMs in plain English?"},
  ]
  ```

  Example with a partially-filled response from Claude:

  ```json
  [
    {"role": "user", "content": "What's the Greek name for Sun? (A) Sol (B) Helios (C) Sun"},
    {"role": "assistant", "content": "The best answer is ("},
  ]
  ```

  Each input message `content` may be either a single `string` or an array of content blocks, where each block has a specific `type`. Using a `string` for `content` is shorthand for an array of one content block of type 
```

</details>

---

## V2D-49

- **provider**: openai
- **document**: How to run gpt-oss with Hugging Face Transformers
- **section**: How to run gpt-oss with Hugging Face Transformers › Pick your model
- **source span**: `ver_6b3ff8e63de5417e301da5fa5adf415e` chars 1588–1700
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, identifier_vs_semantic_distractor, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens if you use `bfloat16` instead of MXFP4?

**Proposed answer**: Memory consumption will be larger (\~48 GB for the 20b parameter model).

**Proposed atomic claims**: If you use `bfloat16` instead of MXFP4, memory consumption will be larger (\~48 GB for the 20b parameter model).

**Critical strings**: bfloat16

**Generator notes**: FLAG_SUBJECT_MISMATCH

### Evidence E1 (verbatim, authoritative)

`ver_6b3ff8e63de5417e301da5fa5adf415e` chars 1588–1700 · hash `b4c6edf26e0150a2…`

```
If you use `bfloat16` instead of MXFP4, memory consumption will be larger (\~48 GB for the 20b parameter model).
```

<details><summary>Context before</summary>

```
s, and serving models locally with \`transformers serve\`, with in a way compatible with the Responses API.

In this guide we’ll run through various optimised ways to run the **gpt-oss models via Transformers.**

Bonus: You can also fine-tune models via transformers, [check out our fine-tuning guide here](https://cookbook.openai.com/articles/gpt-oss/fine-tune-transformers).

## Pick your model

Both **gpt-oss** models are available on Hugging Face:

- **`openai/gpt-oss-20b`**
  - \~16GB VRAM requirement when using MXFP4
  - Great for single high-end consumer GPUs
- **`openai/gpt-oss-120b`**
  - Requires ≥60GB VRAM or multi-GPU setup
  - Ideal for H100-class hardware

Both are **MXFP4 quantized** by default. Please, note that MXFP4 is supported in Hopper or later architectures. This includes data center GPUs such as H100 or GB200, as well as the latest RTX 50xx family of consumer cards.


```

</details>

<details><summary>Context after</summary>

```


## Quick setup

1. **Install dependencies**  
   It’s recommended to create a fresh Python environment. Install transformers, accelerate, as well as the Triton kernels for MXFP4 compatibility:

```bash
pip install -U transformers accelerate torch triton==3.4 kernels
```

2. **(Optional) Enable multi-GPU**  
   If you’re running large models, use Accelerate or torchrun to handle device mapping automatically.

## Create an Open AI Responses / Chat Completions endpoint

To launch a server, simply use the `transformers serve` CLI command:

```bash
transformers serve
```

The simplest way to interact with the server is through the transformers chat CLI

```bash
transformers chat localhost:8000 --model-name-or-path openai/gpt-oss-20b
```

or by sending an HTTP request with cURL, e.g.

```bash
curl -X POST http://localhost:8000/v1/responses -H "Content-Type: application/json" -d '{"messages":
```

</details>

---

## V2D-50

- **provider**: openai
- **document**: Models
- **section**: Models › OpenAI models › Default model › GPT-5 models
- **source span**: `ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 3271–3375
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `configuration_interaction`
- **stress types**: short_evidence_unit, version_model_discrimination, identifier_vs_semantic_distractor, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens when you use any GPT-5 model such as `gpt-5.6-sol` in this way?

**Proposed answer**: The SDK applies default `ModelSettings`.

**Proposed atomic claims**: When you use any GPT-5 model such as `gpt-5.6-sol` in this way, the SDK applies default `ModelSettings`.

**Critical strings**: ModelSettings

**Generator notes**: FLAG_SUBJECT_MISMATCH

### Evidence E1 (verbatim, authoritative)

`ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 3271–3375 · hash `90191bc8cb471837…`

```
When you use any GPT-5 model such as `gpt-5.6-sol` in this way, the SDK applies default `ModelSettings`.
```

<details><summary>Context before</summary>

```
ility can explicitly set `model="gpt-5.6-sol"` and choose `model_settings` that are appropriate for the workload.

If you want to switch to other models like `gpt-5.6-sol`, there are two ways to configure your agents.

### Default model

First, if you want to consistently use a specific model for all agents that do not set a custom model, set the `OPENAI_DEFAULT_MODEL` environment variable before running your agents.

```bash
export OPENAI_DEFAULT_MODEL=gpt-5.6-sol
python3 my_awesome_agent.py
```

Second, you can set a default model for a run via `RunConfig`. If you don't set a model for an agent, this run's model will be used.

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


```

</details>

<details><summary>Context after</summary>

```
 It sets the ones that work the best for most use cases. To adjust the reasoning effort for the default model, pass your own `ModelSettings`:

```python
from openai.types.shared import Reasoning
from agents import Agent, ModelSettings

my_agent = Agent(
    name="My Agent",
    instructions="You're a helpful agent.",
    # If OPENAI_DEFAULT_MODEL=gpt-5.6-sol is set, passing only model_settings works.
    # It's also fine to pass a GPT-5 model name explicitly:
    model="gpt-5.6-sol",
    model_settings=ModelSettings(reasoning=Reasoning(effort="high"), verbosity="low")
)
```

For lower latency, using `reasoning.effort="none"` with GPT-5 models is recommended.

GPT-5.6 also supports reasoning mode, reasoning context carried across conversation turns, and the `"max"` effort level through the existing `reasoning` setting. These controls are available on the Responses API path:

```python
fro
```

</details>

---
