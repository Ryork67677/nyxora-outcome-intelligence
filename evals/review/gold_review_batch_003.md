# Gold review batch 003

**20 candidates · corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · generated 2026-08-20T18:55:07Z**

Nothing in this file is ground truth. Every candidate is `candidate_unverified`. The evidence is quoted verbatim from the frozen corpus and is authoritative for this review — **do not consult live documentation**, which may have changed since the snapshot.

Unlike batches 001 and 002, these ship complete: question, answer, atomic claims and the critical strings that make each claim machine-checkable. Judge the proposal against the evidence; where you disagree, say what the evidence does support.

Provider {'anthropic': 12, 'openai': 8} · 17 distinct documents · median evidence 129 characters.

| id | provider | category | chars | question |
| --- | --- | --- | --- | --- |
| `01` | anthropic | configuration_interaction | 129 | What happens when `citations.enabled` is set to `true`? |
| `02` | anthropic | configuration_interaction | 111 | What does `description` enable? |
| `03` | anthropic | error_behavior | 82 | What happens when setting `max_tokens` above the advisor model's own output… |
| `04` | anthropic | error_behavior | 113 | What happens if you request an invalid pair? |
| `05` | anthropic | error_behavior | 129 | What happens if your tool result doesn't arrive within about 4 minutes? |
| `06` | anthropic | error_behavior | 86 | What happens when setting `temperature`, `top_p`, or `top_k` to a non-defau… |
| `07` | anthropic | exact_constraint | 295 | What does the `clear_tool_inputs` parameter do? |
| `08` | anthropic | exact_constraint | 91 | What is the `old_str` option? |
| `09` | anthropic | exact_constraint | 60 | What is the `new_str` option? |
| `10` | anthropic | lifecycle | 251 | What is the documented status of `budget_tokens`? |
| `11` | anthropic | lifecycle | 164 | What is the documented status of `thinking: {type: "enabled", budget_tokens… |
| `12` | anthropic | multi_hop | 226 | What do the `type` and `country` options specify in Localization? |
| `13` | openai | configuration_interaction | 100 | What does `rejection_message` take precedence over? |
| `14` | openai | configuration_interaction | 143 | What does `AWS_BEARER_TOKEN_BEDROCK` take precedence over? |
| `15` | openai | exact_constraint | 169 | What is the `ToolsToFinalOutputFunction` option? |
| `16` | openai | exact_constraint | 69 | What is the `chunk` option? |
| `17` | openai | exact_constraint | 56 | What is the `parsed` option? |
| `18` | openai | multi_hop | 270 | What do the `tool_name_override` and `tool_description_override` options sp… |
| `19` | openai | multi_hop | 190 | What do the `kind` and `tool_type` options specify in `tool_error_formatter`? |
| `20` | openai | multi_hop | 267 | What do the `workflow_name` and `trace_id` options specify in Traces and sp… |

---

## GOLD-B003-01

- **provider**: anthropic
- **document**: Search results
- **section**: Advanced usage › Citation control
- **category**: `configuration_interaction` · **evidence kind**: `normative_statement`
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What happens when `citations.enabled` is set to `true`?

**A.** Claude attaches citation references to the text blocks that draw on the search result.

**Atomic claims**

  1. When `citations.enabled` is set to `true`, Claude attaches citation references to the text blocks that draw on the search result.

**Exact evidence**

`ver_42a4f3d941b664a285883aaf6ff90373` 80381–80510 (129 chars)

```
When `citations.enabled` is set to `true`, Claude attaches citation references to the text blocks that draw on the search result.
```

**Critical strings** (each verified inside the evidence): `citations.enabled`, `true`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…By default, citations are disabled for search results. You can enable citations by explicitly setting the `citations` configuration:

```json
{
  "type": "search_result",
  "source": "https://docs.company.com/guide",
  "title": "User Guide",
  "content": [{ "type": "text", "text": "Important documentation..." }],
  "citations": {
    "enabled": true // Enable citations for this result
  }
}
```
  ⟦EVIDENCE⟧
<Warning>
  Citations are all-or-nothing: either all search results in a request must have citations enabled, or all must have them disabled. Mixing search results with different citation settings results in an error.
</Warning>

## Best practices

### For tool-based search (Method 1)

* **Dynamic content:** Use for real-time searches and dynamic RAG applications
* **Error handling:** Return app…
```

</details>

---

## GOLD-B003-02

- **provider**: anthropic
- **document**: Skill authoring best practices
- **section**: Skill structure › Writing effective descriptions
- **category**: `configuration_interaction` · **evidence kind**: `normative_statement`
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What does `description` enable?

**A.** Skill discovery and should include both what the Skill does and when to use it.

**Atomic claims**

  1. `description` enables Skill discovery and should include both what the Skill does and when to use it.

**Exact evidence**

`ver_90de89ac7da393e4d9056cf12204d046` 6496–6607 (111 chars)

```
The `description` field enables Skill discovery and should include both what the Skill does and when to use it.
```

**Critical strings** (each verified inside the evidence): `description`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…ments`, `data`, `files`
* Reserved words: `anthropic-helper`, `claude-tools`
* Inconsistent patterns within your skill collection

Consistent naming makes it easier to:

* Reference Skills in documentation and conversations
* Understand what a Skill does at a glance
* Organize and search through multiple Skills
* Maintain a professional, cohesive skill library

### Writing effective descriptions
  ⟦EVIDENCE⟧
<Warning>
  **Always write in third person**. The description is injected into the system prompt, and inconsistent point-of-view can cause discovery problems.

  * **Good:** "Processes Excel files and generates reports"
  * **Avoid:** "I can help you process Excel files"
  * **Avoid:** "You can use this to process Excel files"
</Warning>

**Be specific and include key terms**. Include both what…
```

</details>

---

## GOLD-B003-03

- **provider**: anthropic
- **document**: Advisor tool
- **section**: Best practices › Capping advisor output
- **category**: `error_behavior` · **evidence kind**: `normative_statement`
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What happens when setting `max_tokens` above the advisor model's own output cap?

**A.** It returns a 400 error.

**Atomic claims**

  1. Setting `max_tokens` above the advisor model's own output cap returns a 400 error.

**Exact evidence**

`ver_b8b18cda9b875d51a2ce979a1bf4e909` 85181–85263 (82 chars)

```
Setting `max_tokens` above the advisor model's own output cap returns a 400 error.
```

**Critical strings** (each verified inside the evidence): `max_tokens`, `a 400 error`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…```

  ```php PHP
  $tools = [
      [
          'type' => 'advisor_20260301',
          'name' => 'advisor',
          'model' => 'claude-opus-5',
          'max_tokens' => 2048,
      ],
  ];
  ```

  ```ruby Ruby
  tools = [
    {
      type: "advisor_20260301",
      name: "advisor",
      model: "claude-opus-5",
      max_tokens: 2048
    }
  ]
  ```
</CodeGroup>

The minimum value is 1024.
  ⟦EVIDENCE⟧
The cap applies to each advisor call independently and is not shared across calls in the same request.

This is not a hard truncation alone. The server also passes the advisor its remaining-token budget, so the advisor shapes its response to fit.

**Recommended starting point:** `max_tokens: 2048`. In Anthropic's testing on a hard reasoning benchmark (n = 40 per configuration), this reduced mean…
```

</details>

---

## GOLD-B003-04

- **provider**: anthropic
- **document**: Advisor tool
- **section**: Model compatibility
- **category**: `error_behavior` · **evidence kind**: `normative_statement`
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What happens if you request an invalid pair?

**A.** The api returns a `400 invalid_request_error` naming the unsupported combination.

**Atomic claims**

  1. If you request an invalid pair, the API returns a `400 invalid_request_error` naming the unsupported combination.

**Exact evidence**

`ver_b8b18cda9b875d51a2ce979a1bf4e909` 92785–92898 (113 chars)

```
If you request an invalid pair, the API returns a `400 invalid_request_error` naming the unsupported combination.
```

**Critical strings** (each verified inside the evidence): `400 invalid_request_error`, `` a `400 invalid_request_error` naming the unsupported combination ``

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…|
| Claude Mythos 5 (claude-mythos-5)     | Claude Mythos 5 (claude-mythos-5) Claude Fable 5 (claude-fable-5) Claude Opus 5 (claude-opus-5)                                                                                                                                                                               |
  ⟦EVIDENCE⟧
### Platform availability

The advisor tool is available in beta on the Claude API and on [Claude Platform on AWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws). It is not currently available on Amazon Bedrock, Google Cloud, or Microsoft Foundry.

## Advisor on Claude Managed Agents

[Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overvi…
```

</details>

---

## GOLD-B003-05

- **provider**: anthropic
- **document**: Programmatic tool calling
- **section**: Process results programmatically › Error handling › Container expiration during tool call
- **category**: `error_behavior` · **evidence kind**: `normative_statement`
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What happens if your tool result doesn't arrive within about 4 minutes?

**A.** The pending call raises a `TimeoutError` inside Claude's running code.

**Atomic claims**

  1. If your tool result doesn't arrive within about 4 minutes, the pending call raises a `TimeoutError` inside Claude's running code.

**Exact evidence**

`ver_7cd600e1124f25cfedc3f1f6d5c297e5` 48472–48601 (129 chars)

```
If your tool result doesn't arrive within about 4 minutes, the pending call raises a `TimeoutError` inside Claude's running code.
```

**Critical strings** (each verified inside the evidence): `TimeoutError`, `` a `TimeoutError` inside Claude's running code ``

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…-tool#errors)   |
| `invalid_request_error` (on `tool_choice`) | HTTP 400 error response                                                      | `tool_choice` names a tool whose `allowed_callers` does not include `"direct"` | Either add `"direct"` to that tool's `allowed_callers`, or remove the tool from `tool_choice` and let Claude invoke it from code |

### Container expiration during tool call
  ⟦EVIDENCE⟧
Claude sees the error in `stderr` and typically retries the call:

```json
{
  "type": "code_execution_tool_result",
  "tool_use_id": "srvtoolu_abc123",
  "content": {
    "type": "code_execution_result",
    "stdout": "",
    "stderr": "TimeoutError: Calling tool ['query_database'] timed out (no response after 270s).",
    "return_code": 0,
    "content": []
  }
}
```

To prevent timeouts:

* Mo…
```

</details>

---

## GOLD-B003-06

- **provider**: anthropic
- **document**: What's new in Claude Sonnet 5
- **section**: Behavior changes › Sampling parameters not accepted
- **category**: `error_behavior` · **evidence kind**: `normative_statement`
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What happens when setting `temperature`, `top_p`, or `top_k` to a non-default value?

**A.** It returns a 400 error.

**Atomic claims**

  1. Setting `temperature`, `top_p`, or `top_k` to a non-default value returns a 400 error.

**Exact evidence**

`ver_6c0983aad96f198367a0de369b3bb86c` 2207–2293 (86 chars)

```
Setting `temperature`, `top_p`, or `top_k` to a non-default value returns a 400 error.
```

**Critical strings** (each verified inside the evidence): `temperature`, `top_p`, `top_k`, `a 400 error`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…ut thinking. On Claude Sonnet 5, the same requests run with [adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/thinking). To turn thinking off, pass `thinking: {type: "disabled"}`. Because `max_tokens` is a hard limit on total output (thinking plus response text), revisit it for workloads that ran without thinking on Claude Sonnet 4.6.

### Sampling parameters not accepted
  ⟦EVIDENCE⟧
Remove these parameters when migrating; the default value (or omitting the parameter) is accepted. Use system-prompt instructions to guide model behavior. This is new for Sonnet-class models; the same constraint was previously introduced on Claude Opus 4.7.

### Manual extended thinking removed

Manual extended thinking (`thinking: {type: "enabled", budget_tokens: N}`) was deprecated on Claude So…
```

</details>

---

## GOLD-B003-07

- **provider**: anthropic
- **document**: Context editing
- **section**: Configuration options for tool result clearing
- **category**: `exact_constraint` · **evidence kind**: `parameter_table_row`
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What does the `clear_tool_inputs` parameter do?

**A.** Controls whether the tool call parameters are cleared along with the tool results. By default, only the tool results are cleared while keeping Claude's original tool calls visible.

**Atomic claims**

  1. The `clear_tool_inputs` parameter controls whether the tool call parameters are cleared along with the tool results. By default, only the tool results are cleared while keeping Claude's original tool calls visible.

**Exact evidence**

`ver_1c53b961e1f5da8124a1e7e8eb92c941` 56502–56797 (295 chars)

```
| `clear_tool_inputs`  | `false`              | Controls whether the tool call parameters are cleared along with the tool results. By default, only the tool results are cleared while keeping Claude's original tool calls visible.                                                                  |
```

**Critical strings** (each verified inside the evidence): `clear_tool_inputs`, `Controls whether the tool call parameters are cleared along`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…gy will not be applied. This helps determine if context clearing is worth breaking your prompt cache. |
| `exclude_tools`      | None                 | List of tool names whose tool uses and results should never be cleared. Useful for preserving important context.                                                                                                                                      |
  ⟦EVIDENCE⟧
## Context editing response

You can see which context edits were applied to your request using the `context_management` response field, along with helpful statistics about the content and input tokens cleared.

```json Output
{
  "id": "msg_013Zva2CMHLNnXjNJJKqJ2EF",
  "type": "message",
  "role": "assistant",
  "content": [
    // ...
  ],
  "usage": {
    // ...
  },
  "context_management": {…
```

</details>

---

## GOLD-B003-08

- **provider**: anthropic
- **document**: Text editor tool
- **section**: Use the text editor tool › Text editor tool commands › str\_replace
- **category**: `exact_constraint` · **evidence kind**: `definition_bullet`
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What is the `old_str` option?

**A.** The text to replace (must match exactly, including whitespace and indentation).

**Atomic claims**

  1. `old_str`: The text to replace (must match exactly, including whitespace and indentation).

**Exact evidence**

`ver_72833144cee232446fa450e9e040995a` 9719–9810 (91 chars)

```
* `old_str`: The text to replace (must match exactly, including whitespace and indentation)
```

**Critical strings** (each verified inside the evidence): `old_str`, `The text to replace (must match exactly, including whitespac`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…1rw91mr917835mr9",
    "name": "str_replace_based_edit_tool",
    "input": {
      "command": "view",
      "path": "src/"
    }
  }
  ```
</Accordion>

#### str\_replace

The `str_replace` command allows Claude to replace a specific string in a file with a new string. This is used for making precise edits.

Parameters:

* `command`: Must be "str\_replace"
* `path`: The path to the file to modify
  ⟦EVIDENCE⟧
* `new_str`: The new text to insert in place of the old text

<Accordion title="Example str_replace command">
  ```json
  {
    "type": "tool_use",
    "id": "toolu_01A09q90qw90lq917835lq9",
    "name": "str_replace_based_edit_tool",
    "input": {
      "command": "str_replace",
      "path": "primes.py",
      "old_str": "for num in range(2, limit + 1)",
      "new_str": "for num in range(2, li…
```

</details>

---

## GOLD-B003-09

- **provider**: anthropic
- **document**: Text editor tool
- **section**: Use the text editor tool › Text editor tool commands › str\_replace
- **category**: `exact_constraint` · **evidence kind**: `definition_bullet`
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What is the `new_str` option?

**A.** The new text to insert in place of the old text.

**Atomic claims**

  1. `new_str`: The new text to insert in place of the old text.

**Exact evidence**

`ver_72833144cee232446fa450e9e040995a` 9811–9871 (60 chars)

```
* `new_str`: The new text to insert in place of the old text
```

**Critical strings** (each verified inside the evidence): `new_str`, `The new text to insert in place of the old text`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…: "view",
      "path": "src/"
    }
  }
  ```
</Accordion>

#### str\_replace

The `str_replace` command allows Claude to replace a specific string in a file with a new string. This is used for making precise edits.

Parameters:

* `command`: Must be "str\_replace"
* `path`: The path to the file to modify
* `old_str`: The text to replace (must match exactly, including whitespace and indentation)
  ⟦EVIDENCE⟧
<Accordion title="Example str_replace command">
  ```json
  {
    "type": "tool_use",
    "id": "toolu_01A09q90qw90lq917835lq9",
    "name": "str_replace_based_edit_tool",
    "input": {
      "command": "str_replace",
      "path": "primes.py",
      "old_str": "for num in range(2, limit + 1)",
      "new_str": "for num in range(2, limit + 1):"
    }
  }
  ```
</Accordion>

#### create

The `cr…
```

</details>

---

## GOLD-B003-10

- **provider**: anthropic
- **document**: Extended thinking
- **section**: Migrating to adaptive thinking
- **category**: `lifecycle` · **evidence kind**: `normative_statement`
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What is the documented status of `budget_tokens`?

**A.** It is deprecated.

**Atomic claims**

  1. `budget_tokens` is deprecated.

**Exact evidence**

`ver_3acba29982fd40528ac6498dd0d5fe18` 19000–19251 (251 chars)

```
* You use Claude Opus 4.6 or Claude Sonnet 4.6, where `budget_tokens` is deprecated.
* You are moving to Claude Opus 4.7, Claude Opus 4.8, Claude Opus 5, Claude Sonnet 5, Claude Fable 5, or Claude Mythos 5, where `type: "enabled"` returns a 400 error.
```

**Critical strings** (each verified inside the evidence): `budget_tokens`, `deprecated`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…e 4 models), no action is needed now: adaptive thinking is not available there, and `type: "adaptive"` [returns a 400 error](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting#error-thinking-type-adaptive). Keep `budget_tokens` until you move to a model that supports adaptive thinking, then apply the mapping that follows.

You need to migrate off `type: "enabled"` if:
  ⟦EVIDENCE⟧
The mapping is small: remove `budget_tokens`, set `thinking: {type: "adaptive"}`, and control reasoning depth with `output_config: {effort: ...}` instead of a token budget.

```json
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 16000,
  "thinking": {
    "type": "enabled",
    "budget_tokens": 10000
  }
}
```

becomes:

```json
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 16000,
  "thin…
```

</details>

---

## GOLD-B003-11

- **provider**: anthropic
- **document**: Migration guide
- **section**: Opus migration › Breaking changes
- **category**: `lifecycle` · **evidence kind**: `normative_statement`
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What is the documented status of `thinking: {type: "enabled", budget_tokens: N}`?

**A.** It is no longer supported on Claude Opus 4.

**Atomic claims**

  1. `thinking: {type: "enabled", budget_tokens: N}` is no longer supported on Claude Opus 4.

**Exact evidence**

`ver_a7bda3595f2c124605c3228464d4ee52` 65023–65187 (164 chars)

```
1. **Extended thinking removed:** `thinking: {type: "enabled", budget_tokens: N}` is no longer supported on Claude Opus 4.7 or later models and returns a 400 error.
```

**Critical strings** (each verified inside the evidence): `thinking: {type: "enabled", budget_tokens: N}`, `no longer supported`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…etch](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool) is not available on Claude Opus 5, and [Priority Tier](https://platform.claude.com/docs/en/api/service-tiers#supported-models) is not supported on Claude Opus 5.

#### Update your model name

```python
# Opus migration
model = "claude-opus-4-6"  # Before
model = "claude-opus-5"  # After
```

#### Breaking changes
  ⟦EVIDENCE⟧
Switch to [adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) (`thinking: {type: "adaptive"}`) and use the [effort parameter](https://platform.claude.com/docs/en/build-with-claude/effort) to control thinking depth. On Claude Opus 5, adaptive thinking is **on by default**: `thinking: {type: "adaptive"}` is valid and equivalent to omitting the `thinking` field entire…
```

</details>

---

## GOLD-B003-12

- **provider**: anthropic
- **document**: Web search tool
- **section**: Tool definition › Localization
- **category**: `multi_hop` · **evidence kind**: `multi_span`
- **confidence**: medium · **precheck holdout-ready**: True

**Q.** What do the `type` and `country` options specify in Localization?

**A.** The type of location (must be `approximate`). The two-letter [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country code. The API rejects unsupported country codes with a 400 error.

**Atomic claims**

  1. `type`: The type of location (must be `approximate`).
  2. `country`: The two-letter [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country code. The API rejects unsupported country codes with a 400 error.

**Exact evidence**

`ver_53da2f78e855c75ec755089c13d44c28` 16460–16514 (54 chars) (span 1 of 2)

```
* `type`: The type of location (must be `approximate`)
```

`ver_53da2f78e855c75ec755089c13d44c28` 16571–16743 (172 chars) (span 2 of 2)

```
* `country`: The two-letter [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country code. The API rejects unsupported country codes with a 400 error.
```

**Critical strings** (each verified inside the evidence): `type`, `` The type of location (must be `approximate ``, `country`, `The two-letter [ISO 3166-1 alpha-2](https://en.wikipedia.org`

*Two independently anchored spans. A retriever earns credit only by finding both, and each claim is checked against the span it came from. The question asks for both facts; it does not ask the reader to derive a third, because the source does not state one.*

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…ample.com/blog`, without a scheme.

For the full domain filtering rules, see [Domain filtering](https://platform.claude.com/docs/en/agents-and-tools/tool-use/server-tools#domain-filtering) in the Server tools guide.

### Localization

The `user_location` parameter allows you to localize search results based on a user's location. Provide at least one of `city`, `region`, `country`, or `timezone`.
  ⟦EVIDENCE⟧
* `city`: The city name
* `region`: The region or state
* `country`: The two-letter [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country code. The API rejects unsupported country codes with a 400 error.
* `timezone`: The [IANA timezone ID](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

### Response inclusion

<Note>
  Requires `web_search_20260318` or la…
```

</details>

---

## GOLD-B003-13

- **provider**: openai
- **document**: Human-in-the-loop
- **section**: Human-in-the-loop › Custom rejection messages
- **category**: `configuration_interaction` · **evidence kind**: `normative_statement`
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What does `rejection_message` take precedence over?

**A.** The run-wide formatter.

**Atomic claims**

  1. `rejection_message` takes precedence over the run-wide formatter.

**Exact evidence**

`ver_ae3bfcc42c733c5051abda30f0f6db07` 6226–6326 (100 chars)

```
If both are provided, the per-call `rejection_message` takes precedence over the run-wide formatter.
```

**Critical strings** (each verified inside the evidence): `rejection_message`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…n. You can customize that message in two layers:

-   Run-wide fallback: set [`RunConfig.tool_error_formatter`][agents.run.RunConfig.tool_error_formatter] to control the default model-visible message for approval rejections across the whole run.
-   Per-call override: pass `rejection_message=...` to `state.reject(...)` when you want one specific rejected tool call to surface a different message.
  ⟦EVIDENCE⟧
```python
from agents import RunConfig, ToolErrorFormatterArgs


def format_rejection(args: ToolErrorFormatterArgs[None]) -> str | None:
    if args.kind != "approval_rejected":
        return None
    return "Publish action was canceled because approval was rejected."


run_config = RunConfig(tool_error_formatter=format_rejection)

# Later, while resolving a specific interruption:
state.reject(…
```

</details>

---

## GOLD-B003-14

- **provider**: openai
- **document**: OpenAI Python API library
- **section**: configured through AWS_REGION, AWS_DEFAULT_REGION, or your AWS profile.
- **category**: `configuration_interaction` · **evidence kind**: `normative_statement`
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What does `AWS_BEARER_TOKEN_BEDROCK` take precedence over?

**A.** The default AWS credential chain for backwards compatibility.

**Atomic claims**

  1. `AWS_BEARER_TOKEN_BEDROCK` takes precedence over the default AWS credential chain for backwards compatibility.

**Exact evidence**

`ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` 34622–34765 (143 chars)

```
Without explicit authentication, `AWS_BEARER_TOKEN_BEDROCK` takes precedence over the default AWS credential chain for backwards compatibility.
```

**Critical strings** (each verified inside the evidence): `AWS_BEARER_TOKEN_BEDROCK`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…arer tokens remain available as a compatibility or manual authentication mode. Set `AWS_BEARER_TOKEN_BEDROCK` to an [Amazon Bedrock API key](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html), pass `api_key`, or provide a refresh callback:

```py
client = OpenAI(
    provider=bedrock(
        region="us-west-2",
        token_provider=lambda: refresh_bedrock_token(),
    )
)
```
  ⟦EVIDENCE⟧
### Legacy `BedrockOpenAI` client

`BedrockOpenAI` and `AsyncBedrockOpenAI` remain available for existing applications and delegate to the same provider implementation. New applications should prefer `OpenAI(provider=bedrock(...))`.

```py
from openai import BedrockOpenAI

client = BedrockOpenAI(
    aws_region="us-west-2",
    aws_profile="my-profile",
)
```

The legacy module client also conti…
```

</details>

---

## GOLD-B003-15

- **provider**: openai
- **document**: Agents
- **section**: Agents › Tool use behavior
- **category**: `exact_constraint` · **evidence kind**: `definition_bullet`
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What is the `ToolsToFinalOutputFunction` option?

**A.** A custom function that processes tool results and decides whether to end the run with a final output or continue processing with the LLM.

**Atomic claims**

  1. `ToolsToFinalOutputFunction`: A custom function that processes tool results and decides whether to end the run with a final output or continue processing with the LLM.

**Exact evidence**

`ver_35cac5e98c151a17f941a6142d74709f` 15672–15841 (169 chars)

```
- `ToolsToFinalOutputFunction`: A custom function that processes tool results and decides whether to end the run with a final output or continue processing with the LLM.
```

**Critical strings** (each verified inside the evidence): `ToolsToFinalOutputFunction`, `A custom function that processes tool results and decides wh`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…"""Returns weather info for the specified city."""
    return f"The weather in {city} is sunny"

@tool
def sum_numbers(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b

agent = Agent(
    name="Stop At Stock Agent",
    instructions="Get weather or sum numbers.",
    tools=[get_weather, sum_numbers],
    tool_use_behavior=StopAtTools(stop_at_tool_names=["get_weather"])
)
```
  ⟦EVIDENCE⟧
```python
from agents import Agent, FunctionToolResult, RunContextWrapper
from agents.agent import ToolsToFinalOutputResult
from agents.decorators import tool
from typing import List, Any

@tool
def get_weather(city: str) -> str:
    """Returns weather info for the specified city."""
    return f"The weather in {city} is sunny"

def custom_tool_handler(
    context: RunContextWrapper[Any],
    t…
```

</details>

---

## GOLD-B003-16

- **provider**: openai
- **document**: Structured Outputs Parsing Helpers
- **section**: Streaming Helpers › Chat Completions API › Chat Completions Events › ChunkEvent
- **category**: `exact_constraint` · **evidence kind**: `definition_bullet`
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What is the `chunk` option?

**A.** The raw `ChatCompletionChunk` object received from the API.

**Atomic claims**

  1. `chunk`: The raw `ChatCompletionChunk` object received from the API.

**Exact evidence**

`ver_57e26a49b0a3714f3e90376d014d7f52` 5603–5672 (69 chars)

```
- `chunk`: The raw `ChatCompletionChunk` object received from the API
```

**Critical strings** (each verified inside the evidence): `chunk`, `` The raw `ChatCompletionChunk` object received from the API ``

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…m` instance is still available outside
the context manager.

### Chat Completions Events

These events allow you to track the progress of the chat completion generation, access partial results, and handle different aspects of the stream separately.

Below is a list of the different event types you may encounter:

#### ChunkEvent

Emitted for every chunk received from the API.

- `type`: `"chunk"`
  ⟦EVIDENCE⟧
- `snapshot`: The current accumulated state of the chat completion

#### ContentDeltaEvent

Emitted for every chunk containing new content.

- `type`: `"content.delta"`
- `delta`: The new content string received in this chunk
- `snapshot`: The accumulated content so far
- `parsed`: The partially parsed content (if applicable)

#### ContentDoneEvent

Emitted when the content generation is complete…
```

</details>

---

## GOLD-B003-17

- **provider**: openai
- **document**: Structured Outputs Parsing Helpers
- **section**: Streaming Helpers › Chat Completions API › Chat Completions Events › ContentDeltaEvent
- **category**: `exact_constraint` · **evidence kind**: `definition_bullet`
- **confidence**: high · **precheck holdout-ready**: True

**Q.** What is the `parsed` option?

**A.** The partially parsed content (if applicable).

**Atomic claims**

  1. `parsed`: The partially parsed content (if applicable).

**Exact evidence**

`ver_57e26a49b0a3714f3e90376d014d7f52` 5944–6000 (56 chars)

```
- `parsed`: The partially parsed content (if applicable)
```

**Critical strings** (each verified inside the evidence): `parsed`, `The partially parsed content (if applicable`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…or every chunk received from the API.

- `type`: `"chunk"`
- `chunk`: The raw `ChatCompletionChunk` object received from the API
- `snapshot`: The current accumulated state of the chat completion

#### ContentDeltaEvent

Emitted for every chunk containing new content.

- `type`: `"content.delta"`
- `delta`: The new content string received in this chunk
- `snapshot`: The accumulated content so far
  ⟦EVIDENCE⟧
#### ContentDoneEvent

Emitted when the content generation is complete. May be fired multiple times if there are multiple choices.

- `type`: `"content.done"`
- `content`: The full generated content
- `parsed`: The fully parsed content (if applicable)

#### RefusalDeltaEvent

Emitted when a chunk contains part of a content refusal.

- `type`: `"refusal.delta"`
- `delta`: The new refusal content…
```

</details>

---

## GOLD-B003-18

- **provider**: openai
- **document**: Handoffs
- **section**: (1)! › Customizing handoffs via the `handoff()` function
- **category**: `multi_hop` · **evidence kind**: `multi_span`
- **confidence**: medium · **precheck holdout-ready**: True

**Q.** What do the `tool_name_override` and `tool_description_override` options specify in Customizing handoffs via the `handoff()` function?

**A.** By default, the `Handoff.default_tool_name()` function is used, which resolves to `transfer_to_<agent_name>`. You can override this. Override the default tool description from `Handoff.default_tool_description()`.

**Atomic claims**

  1. `tool_name_override`: By default, the `Handoff.default_tool_name()` function is used, which resolves to `transfer_to_<agent_name>`. You can override this.
  2. `tool_description_override`: Override the default tool description from `Handoff.default_tool_description()`.

**Exact evidence**

`ver_1c77f33b04ffffa285ea7e61c2a89653` 1723–1881 (158 chars) (span 1 of 2)

```
-   `tool_name_override`: By default, the `Handoff.default_tool_name()` function is used, which resolves to `transfer_to_<agent_name>`. You can override this.
```

`ver_1c77f33b04ffffa285ea7e61c2a89653` 1882–1994 (112 chars) (span 2 of 2)

```
-   `tool_description_override`: Override the default tool description from `Handoff.default_tool_description()`
```

**Critical strings** (each verified inside the evidence): `tool_name_override`, `` By default, the `Handoff.default_tool_name()` function is us ``, `tool_description_override`, `` Override the default tool description from `Handoff.default ``

*Two independently anchored spans. A retriever earns credit only by finding both, and each claim is checked against the span it came from. The question asks for both facts; it does not ask the reader to derive a third, because the source does not state one.*

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…triage_agent = Agent(name="Triage agent", handoffs=[billing_agent, handoff(refund_agent)])
```

1. You can use the agent directly (as in `billing_agent`), or you can use the `handoff()` function.

### Customizing handoffs via the `handoff()` function

The [`handoff()`][agents.handoffs.handoff] function lets you customize things.

-   `agent`: This is the agent to which things will be handed off.
  ⟦EVIDENCE⟧
-   `tool_description_override`: Override the default tool description from `Handoff.default_tool_description()`
-   `on_handoff`: A callback function executed when the handoff is invoked. This is useful for things like kicking off some data fetching as soon as you know a handoff is being invoked. This function receives the agent context, and can optionally also receive LLM generated input. The i…
```

</details>

---

## GOLD-B003-19

- **provider**: openai
- **document**: Running agents
- **section**: Running agents › Runner lifecycle and configuration › Run config › Run config details › `tool_error_formatter`
- **category**: `multi_hop` · **evidence kind**: `multi_span`
- **confidence**: medium · **precheck holdout-ready**: True

**Q.** What do the `kind` and `tool_type` options specify in `tool_error_formatter`?

**A.** The error category, such as `"approval_rejected"` or `"tool_not_found"`. The tool runtime (`"function"`, `"computer"`, `"shell"`, `"apply_patch"`, or `"custom"`).

**Atomic claims**

  1. `kind`: The error category, such as `"approval_rejected"` or `"tool_not_found"`.
  2. `tool_type`: The tool runtime (`"function"`, `"computer"`, `"shell"`, `"apply_patch"`, or `"custom"`).

**Exact evidence**

`ver_2c60e99cfd929a738910b893fd6f1a40` 15366–15450 (84 chars) (span 1 of 2)

```
-   `kind`: The error category, such as `"approval_rejected"` or `"tool_not_found"`.
```

`ver_2c60e99cfd929a738910b893fd6f1a40` 15451–15557 (106 chars) (span 2 of 2)

```
-   `tool_type`: The tool runtime (`"function"`, `"computer"`, `"shell"`, `"apply_patch"`, or `"custom"`).
```

**Critical strings** (each verified inside the evidence): `kind`, `` The error category, such as `"approval_rejected"` or `"tool ``, `tool_type`, `` The tool runtime (`"function"`, `"computer"`, `"shell"`, `"a ``

*Two independently anchored spans. A retriever earns credit only by finding both, and each claim is checked against the span it came from. The question asks for both facts; it does not ask the reader to derive a third, because the source does not state one.*

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…only to function tool calls that fail tool-name lookup. Other invalid tool payloads continue to use their existing error behavior.

##### `tool_error_formatter`

Use `tool_error_formatter` to customize the message that is returned to the model when the SDK creates a model-visible tool error output.

The formatter receives [`ToolErrorFormatterArgs`][agents.run_config.ToolErrorFormatterArgs] with:
  ⟦EVIDENCE⟧
-   `tool_type`: The tool runtime (`"function"`, `"computer"`, `"shell"`, `"apply_patch"`, or `"custom"`).
-   `tool_name`: The tool name.
-   `call_id`: The tool call ID.
-   `default_message`: The SDK's default model-visible message.
-   `run_context`: The active run context wrapper.

Return a string to replace the message, or `None` to use the SDK default.

```python
from agents import Agent,…
```

</details>

---

## GOLD-B003-20

- **provider**: openai
- **document**: Tracing
- **section**: Tracing › Traces and spans
- **category**: `multi_hop` · **evidence kind**: `multi_span`
- **confidence**: medium · **precheck holdout-ready**: True

**Q.** What do the `workflow_name` and `trace_id` options specify in Traces and spans?

**A.** This is the name of the logical workflow or app. For example "Code generation" or "Customer service". A unique ID for the trace. Automatically generated if you don't pass one. Must have the format `trace_<32_alphanumeric>`.

**Atomic claims**

  1. `workflow_name`: This is the name of the logical workflow or app. For example "Code generation" or "Customer service".
  2. `trace_id`: A unique ID for the trace. Automatically generated if you don't pass one. Must have the format `trace_<32_alphanumeric>`.

**Exact evidence**

`ver_6b90217721b841b1329f51ec1caab139` 1043–1169 (126 chars) (span 1 of 2)

```
    -   `workflow_name`: This is the name of the logical workflow or app. For example "Code generation" or "Customer service".
```

`ver_6b90217721b841b1329f51ec1caab139` 1170–1311 (141 chars) (span 2 of 2)

```
    -   `trace_id`: A unique ID for the trace. Automatically generated if you don't pass one. Must have the format `trace_<32_alphanumeric>`.
```

**Critical strings** (each verified inside the evidence): `workflow_name`, `This is the name of the logical workflow or app. For example`, `trace_id`, `A unique ID for the trace. Automatically generated if you do`

*Two independently anchored spans. A retriever earns credit only by finding both, and each claim is checked against the span it came from. The question asks for both facts; it does not ask the reader to derive a third, because the source does not state one.*

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…cing_disabled]
    3. You can disable tracing for a single run by setting [`agents.run.RunConfig.tracing_disabled`][] to `True`

***Tracing is unavailable for organizations that use OpenAI's APIs under a Zero Data Retention (ZDR) policy.***

## Traces and spans

-   **Traces** represent a single end-to-end operation of a "workflow". They're composed of Spans. Traces have the following properties:
  ⟦EVIDENCE⟧
-   `trace_id`: A unique ID for the trace. Automatically generated if you don't pass one. Must have the format `trace_<32_alphanumeric>`.
    -   `group_id`: Optional group ID, to link multiple traces from the same conversation. For example, you might use a chat thread ID.
    -   `disabled`: If True, the trace will not be recorded.
    -   `metadata`: Optional metadata for the trace.
-   **S…
```

</details>

---
