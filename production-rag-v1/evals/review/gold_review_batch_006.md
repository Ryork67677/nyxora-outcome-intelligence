# Gold review batch 006

**9 candidates · corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · generated 2026-08-24T06:01:08Z**

Nothing in this file is ground truth. Every candidate is `candidate_unverified`. The evidence is quoted verbatim from the frozen corpus and is authoritative for this review — **do not consult live documentation**, which may have changed since the snapshot.

Three things to know before reading. First, `precheck_holdout_ready` is **structural only**: batch 005 shipped 19 of 19 precheck-ready and its review still repaired seven and rejected four. Second, the `internal_semantic_review_status` on each candidate is a **generation** self-review — the author reading its own output — and is not verification. Third, `section_path` is metadata, not evidence: the heading parser audit found headings that are ordinary prose, so a claim's scope has to be inside the span.

Provider {'anthropic': 5, 'openai': 4} · reasoning {'configuration_interaction': 4, 'error_behavior': 1, 'exact_lookup': 4} · 8 distinct documents · median span 181 characters.

| id | provider | reasoning type | shape | chars | question |
| --- | --- | --- | --- | --- | --- |
| `01` | anthropic | configuration_interaction | single_span | 181 | What does Creating an `admin`-role service account require? |
| `02` | anthropic | error_behavior | single_span | 72 | What does Claude Opus 4.7 reject? |
| `03` | anthropic | exact_lookup | single_span | 345 | What does Claude Haiku 4.5 accept? |
| `04` | anthropic | exact_lookup | single_span | 76 | What does Claude Sonnet 5 default to? |
| `05` | anthropic | exact_lookup | single_span | 182 | What does `thinking.display` default to? |
| `06` | openai | configuration_interaction | single_span | 206 | What does `AWS_BEDROCK_BASE_URL` override? |
| `07` | openai | configuration_interaction | single_span | 81 | What does Setting `audio.input.turn_detection` to `None` disable? |
| `08` | openai | configuration_interaction | single_span | 324 | What does the OpenAI Python SDK's temporary legacy-client compati… |
| `09` | openai | exact_lookup | single_span | 62 | What does `RunErrorHandlerResult.include_in_history` default to? |

---

## GOLD-B006-01

- **provider**: anthropic
- **document**: Admin
- **section** (metadata, not scope): Service Accounts › Create Service Account
- **reasoning type**: `configuration_interaction` · **secondary**: `requires`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What does Creating an `admin`-role service account require?

**A.** Creating an `admin`-role service account requires an interactive credential (a user OAuth token or a Console session) — a workload may only create `developer`-role service accounts.

**Atomic claims**

  1. Creating an `admin`-role service account requires an interactive credential (a user OAuth token or a Console session) — a workload may only create `developer`-role service accounts.

**Subject and relation** — check the direction against the evidence below.

| | subject | relation | object |
| --- | --- | --- | --- |
| source | Creating an `admin`-role service account | `requires` | an interactive credential (a user OAuth token or a Console session) — a workload may only create `developer`-role service accounts. |
| question | Creating an `admin`-role service account | `requires` | an interactive credential (a user OAuth token or a Console session) — a workload may only create `developer`-role service accounts |

*Source triple read by: named relation.*

**Exact evidence**

`E1` · `ver_c299b58fe1f5a4d3a081b550334a7df6` 441865–442046 (181 chars)

```
Creating an `admin`-role service account requires
an interactive credential (a user OAuth token or a Console session) — a
workload may only create `developer`-role service accounts.
```
**critical strings**: `admin`, `developer`

**Claim → evidence**

  1. Creating an `admin`-role service account requires an interactive credential (a user OAuth token or a… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…eate a service account.

A service account is a named workload identity that federation rules
target. `organization_role` is `developer` (default) or `admin`; a rule
may only be created or retargeted to grant `org:admin` scope when the
target's `organization_role` is `admin`. Requires an OAuth bearer (user
or WIF-minted service account token) or a Console session; Admin API
keys are not accepted.
  ⟦EVIDENCE⟧
### Header Parameters

- `"anthropic-beta": optional array of string`

  Optional header to specify the beta version(s) you want to use.

  To use multiple betas, use a comma separated list like `beta1,beta2` or specify the header multiple times for each beta.

### Body Parameters

- `name: string`

  Slug identifier (lowercase, digits, hyphens). Unique within the organization; a duplicate name…
```

</details>

---

## GOLD-B006-02

- **provider**: anthropic
- **document**: Migration guide
- **section** (metadata, not scope): Opus migration › What changed
- **reasoning type**: `error_behavior` · **secondary**: `rejects`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What does Claude Opus 4.7 reject?

**A.** Claude Opus 4.7 rejects `role: "system"` in `messages` with a 400 error.

**Atomic claims**

  1. Claude Opus 4.7 rejects `role: "system"` in `messages` with a 400 error.

**Subject and relation** — check the direction against the evidence below.

| | subject | relation | object |
| --- | --- | --- | --- |
| source | Claude Opus 4.7 | `rejects` | `role: "system"` in `messages` with a 400 error. |
| question | Claude Opus 4.7 | `rejects` | `role: "system"` in `messages` with a 400 error |

*Source triple read by: named relation.*

**Exact evidence**

`E1` · `ver_a7bda3595f2c124605c3228464d4ee52` 55306–55378 (72 chars)

```
Claude Opus 4.7 rejects `role: "system"` in `messages` with a 400 error.
```
**critical strings**: `messages`

**Claim → evidence**

  1. Claude Opus 4.7 rejects `role: "system"` in `messages` with a 400 error. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…er models, you can remove it on Claude Opus 5.

5. **Mid-conversation system messages:** Claude Opus 5 accepts `role: "system"` messages immediately after a user turn in the `messages` array (subject to [placement rules](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages#limitations)). Use the top-level `system` field for instructions that apply from the start.
  ⟦EVIDENCE⟧
If you maintain code paths that rebuild the full message history to update instructions, you can simplify them and preserve [prompt cache](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) hits on earlier turns.

6. **Refusal stop details:** The `stop_details` object on refusal responses (available since Claude Opus 4.7) is now publicly documented. When the model declines a re…
```

</details>

---

## GOLD-B006-03

- **provider**: anthropic
- **document**: Code execution tool
- **section** (metadata, not scope): Model compatibility
- **reasoning type**: `exact_lookup` · **secondary**: `accepts`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What does Claude Haiku 4.5 accept?

**A.** Claude Haiku 4.5 accepts the `code_execution_20260120` and `code_execution_20260521` tool types, but programmatic tool calling and the REPL state persistence that depends on it aren't available on it, so the newer versions behave like `code_execution_20250825` there.

**Atomic claims**

  1. Claude Haiku 4.5 accepts the `code_execution_20260120` and `code_execution_20260521` tool types, but programmatic tool calling and the REPL state persistence that depends on it aren't available on it, so the newer versions behave like `code_execution_20250825` there.

**Subject and relation** — check the direction against the evidence below.

| | subject | relation | object |
| --- | --- | --- | --- |
| source | Claude Haiku 4.5 | `accepts` | the `code_execution_20260120` and `code_execution_20260521` tool types, but programmatic tool calling and the REPL state persistence that depends on it aren't available on it, so the newer versions behave like `code_execution_20250825` there |
| question | Claude Haiku 4.5 | `accepts` | the `code_execution_20260120` and `code_execution_20260521` tool types, but programmatic tool calling and the REPL state persistence that depends on it aren't available on it, so the newer versions behave like `code_execution_20250825` there |

*Source triple read by: named relation.*

**Exact evidence**

`E1` · `ver_f65938c74d40ac1e288f169d3d0435b7` 3971–4316 (345 chars)

```
Claude Haiku 4.5 accepts the `code_execution_20260120` and `code_execution_20260521` tool types, but programmatic tool calling and the REPL state persistence that depends on it aren't available on it, so the newer versions behave like `code_execution_20250825` there.
* `code_execution_20260521` is the same runtime as `code_execution_20260120`.
```
**critical strings**: `code_execution_20260120`, `code_execution_20260521`, `code_execution_20250825`

**Claim → evidence**

  1. Claude Haiku 4.5 accepts the `code_execution_20260120` and `code_execution_20260521` tool types, but… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…e_execution_20250825`, `code_execution_20260120`, `code_execution_20260521` |

Each tool version builds on the previous one:

* `code_execution_20250825` supports Bash commands and file operations.
* `code_execution_20260120` adds REPL state persistence and [programmatic tool calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling) from within the sandbox.
  ⟦EVIDENCE⟧
The difference is that the tool description tells Claude about the 90-second wall-clock limit on each Python cell in programmatic tool calling, so Claude can budget long-running cells. A cell that exceeds the limit returns a normal code execution result with a non-zero `return_code` and a `detection_timeout` status message in its output. This is separate from the `execution_time_exceeded` [error…
```

</details>

---

## GOLD-B006-04

- **provider**: anthropic
- **document**: Effort
- **section** (metadata, not scope): How effort works › Recommended effort levels for Claude Sonnet 5
- **reasoning type**: `exact_lookup` · **secondary**: `defaults_to`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What does Claude Sonnet 5 default to?

**A.** Claude Sonnet 5 defaults to `high` effort on the Claude API and Claude Code.

**Atomic claims**

  1. Claude Sonnet 5 defaults to `high` effort on the Claude API and Claude Code.

**Subject and relation** — check the direction against the evidence below.

| | subject | relation | object |
| --- | --- | --- | --- |
| source | Claude Sonnet 5 | `defaults_to` | `high` effort on the Claude API and Claude Code. |
| question | Claude Sonnet 5 | `defaults_to` | `high` effort on the Claude API and Claude Code |

*Source triple read by: named relation.*

**Exact evidence**

`E1` · `ver_238961530ce62a75c61bdeead5ccb10d` 5123–5199 (76 chars)

```
Claude Sonnet 5 defaults to `high` effort on the Claude API and Claude Code.
```
**critical strings**: `high`

**Claim → evidence**

  1. Claude Sonnet 5 defaults to `high` effort on the Claude API and Claude Code. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…gents                 |

`xhigh` is a newer level; some models that support `max` don't support `xhigh`.

<Note>
  Effort is a behavioral signal, not a strict token budget. At lower effort levels, Claude will still think on sufficiently difficult problems, but it will think less than it would at higher effort levels for the same problem.
</Note>

### Recommended effort levels for Claude Sonnet 5
  ⟦EVIDENCE⟧
* **High effort (default):** Suitable for complex reasoning, coding, and agentic tasks where quality matters more than speed or cost.
* **Xhigh effort:** For the hardest coding and agentic tasks. See [Prompting Claude Sonnet 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5#calibrating-effort-and-thinking-depth).
* **Medium effort:** Cost-savin…
```

</details>

---

## GOLD-B006-05

- **provider**: anthropic
- **document**: Migration guide
- **section** (metadata, not scope): Or, for the generally available model with the same capabilities: › Migration checklist
- **reasoning type**: `exact_lookup` · **secondary**: `defaults_to`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What does `thinking.display` default to?

**A.** `thinking.display` defaults to `"omitted"` on `claude-mythos-5` and `claude-fable-5`, the same as on Claude Mythos Preview; set `display: "summarized"` to receive readable summaries.

**Atomic claims**

  1. `thinking.display` defaults to `"omitted"` on `claude-mythos-5` and `claude-fable-5`, the same as on Claude Mythos Preview; set `display: "summarized"` to receive readable summaries.

**Subject and relation** — check the direction against the evidence below.

| | subject | relation | object |
| --- | --- | --- | --- |
| source | `thinking.display` | `defaults_to` | `"omitted"` on `claude-mythos-5` and `claude-fable-5`, the same as on Claude Mythos Preview; set `display: "summarized"` to receive readable summaries. |
| question | `thinking.display` | `defaults_to` | `"omitted"` on `claude-mythos-5` and `claude-fable-5`, the same as on Claude Mythos Preview; set `display: "summarized"` to receive readable summaries |

*Source triple read by: named relation.*

**Exact evidence**

`E1` · `ver_a7bda3595f2c124605c3228464d4ee52` 15155–15337 (182 chars)

```
`thinking.display` defaults to `"omitted"` on `claude-mythos-5` and `claude-fable-5`, the same as on Claude Mythos Preview; set `display: "summarized"` to receive readable summaries.
```
**critical strings**: `thinking.display`

**Claim → evidence**

  1. `thinking.display` defaults to `"omitted"` on `claude-mythos-5` and `claude-fable-5`, the same as on… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…sabling thinking returns an error on `claude-mythos-5` and `claude-fable-5`.
* Remove `budget_tokens`. It has no direct replacement: thinking is adaptive, and the `effort` parameter is a separate output-level control, not a thinking budget.
* Verify any code that parses the `thinking` field treats it as display text only and passes thinking blocks back unchanged when continuing on the same model.
  ⟦EVIDENCE⟧
See [Thinking output on Claude Fable 5 and Claude Mythos 5](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-output-on-claude-fable-5-and-claude-mythos-5).
* If you replay conversation history on another model, strip `thinking` and `redacted_thinking` blocks from prior assistant turns first. Thinking blocks from `claude-mythos-5` and `claude-fable-5` are tied to the model t…
```

</details>

---

## GOLD-B006-06

- **provider**: openai
- **document**: OpenAI TypeScript and JavaScript API Library
- **section** (metadata, not scope): OpenAI TypeScript and JavaScript API Library › Amazon Bedrock
- **reasoning type**: `configuration_interaction` · **secondary**: `overrides`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What does `AWS_BEDROCK_BASE_URL` override?

**A.** This uses the regional `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint. The region can also come from `AWS_REGION` or `AWS_DEFAULT_REGION`, and `AWS_BEDROCK_BASE_URL` can override the endpoint.

**Atomic claims**

  1. This uses the regional `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint. The region can also come from `AWS_REGION` or `AWS_DEFAULT_REGION`, and `AWS_BEDROCK_BASE_URL` can override the endpoint.

**Subject and relation** — check the direction against the evidence below.

| | subject | relation | object |
| --- | --- | --- | --- |
| source | `AWS_BEDROCK_BASE_URL` | `overrides` | the endpoint. |
| question | `AWS_BEDROCK_BASE_URL` | `overrides` | `AWS_REGION` |

*Source triple read by: named relation.*

**Exact evidence**

`E1` · `ver_f30a6447e4df2ab76e4c1475f353109c` 17117–17323 (206 chars)

```
This uses the regional `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint. The region can also come from `AWS_REGION` or `AWS_DEFAULT_REGION`, and `AWS_BEDROCK_BASE_URL` can override the endpoint.
```
**critical strings**: `AWS_BEDROCK_BASE_URL`, `AWS_REGION`, `AWS_DEFAULT_REGION`

**Claim → evidence**

  1. This uses the regional `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint. The region can … → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…ck({ region: 'us-west-2' }),
});

const response = await client.responses.create({
  model: 'openai.gpt-5.4',
  input: 'Say hello!',
});

console.log(response.output_text);
```

Use a model that [supports the Responses API](https://docs.aws.amazon.com/bedrock/latest/userguide/models-api-compatibility.html). A model returned by the Models API may support a different Bedrock inference API instead.
  ⟦EVIDENCE⟧
The AWS entrypoint uses the standard AWS credential chain by default. It also accepts a named profile, static credentials, or a custom credential provider. Install its peer dependencies before importing it:

```bash
npm install @aws-sdk/credential-provider-node @smithy/hash-node @smithy/signature-v4
```

The AWS entrypoint uses normal static imports so bundlers and serverless packagers can trace…
```

</details>

---

## GOLD-B006-07

- **provider**: openai
- **document**: Realtime agents guide
- **section** (metadata, not scope): Realtime agents guide › Agent and session configuration › Input transcription settings
- **reasoning type**: `configuration_interaction` · **secondary**: `disables`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What does Setting `audio.input.turn_detection` to `None` disable?

**A.** Setting `audio.input.turn_detection` to `None` disables automatic turn detection.

**Atomic claims**

  1. Setting `audio.input.turn_detection` to `None` disables automatic turn detection.

**Subject and relation** — check the direction against the evidence below.

| | subject | relation | object |
| --- | --- | --- | --- |
| source | Setting `audio.input.turn_detection` to `None` | `disables` | automatic turn detection. |
| question | Setting `audio.input.turn_detection` to `None` | `disables` | automatic turn detection |

*Source triple read by: named relation.*

**Exact evidence**

`E1` · `ver_14a2187cf2216b9d56c213b520a28479` 7318–7399 (81 chars)

```
Setting `audio.input.turn_detection` to `None` disables automatic turn detection.
```
**critical strings**: `audio.input.turn_detection`, `None`

**Claim → evidence**

  1. Setting `audio.input.turn_detection` to `None` disables automatic turn detection. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…on over WebSocket only when transcription should begin after a committed audio turn or the application needs detected-language output. The model automatically uses earlier transcribed turns as context. The `gpt-transcribe` completion event reports detected languages in its `languages` output field. This output field is different from the `gpt-live-transcribe` expected-language input shown above.
  ⟦EVIDENCE⟧
The application must then commit audio turns and control response creation as described in [Manual response control](#manual-response-control). See the OpenAI API [Realtime transcription guide](https://developers.openai.com/api/docs/guides/realtime-transcription) for model behavior, validation rules, and latency guidance.

## Inputs and outputs

### Text and structured user messages

Use [`sessio…
```

</details>

---

## GOLD-B006-08

- **provider**: openai
- **document**: Release process/changelog
- **section** (metadata, not scope): Release process/changelog › Breaking change changelog › 0.21.0
- **reasoning type**: `configuration_interaction` · **secondary**: `requires`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What does the OpenAI Python SDK's temporary legacy-client compatibility path require?

**A.** The OpenAI Python SDK's temporary legacy-client compatibility path requires an explicit `httpx` installation and should be treated as a migration bridge.

**Atomic claims**

  1. The OpenAI Python SDK's temporary legacy-client compatibility path requires an explicit `httpx` installation and should be treated as a migration bridge.

**Subject and relation** — check the direction against the evidence below.

| | subject | relation | object |
| --- | --- | --- | --- |
| source | The OpenAI Python SDK's temporary legacy-client compatibility path | `requires` | an explicit `httpx` installation and should be treated as a migration bridge |
| question | The OpenAI Python SDK's temporary legacy-client compatibility path | `requires` | an explicit `httpx` installation and should be treated as a migration bridge |

*Source triple read by: named relation.*

**Exact evidence**

`E1` · `ver_de67d790db9792b2f6c5c7418a507764` 1996–2320 (324 chars)

```
The OpenAI Python SDK's temporary legacy-client compatibility path requires an explicit `httpx` installation and should be treated as a migration bridge.
-   Local MCP HTTP customization continues to follow the installed MCP package: MCP Python SDK v1 supplies and uses legacy `httpx`, while MCP Python SDK v2 uses `httpx2`.
```
**critical strings**: `httpx`, `httpx2`

**Claim → evidence**

  1. The OpenAI Python SDK's temporary legacy-client compatibility path requires an explicit `httpx` inst… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…lues, URLs, requests, responses, and transport exception handling from `httpx` to `httpx2`. Prefer the OpenAI Python SDK's `DefaultAsyncHttpx2Client` when the application needs the OpenAI client's defaults plus custom HTTP options. See [Custom HTTP clients with `openai` v3](config.md#custom-http-clients-with-openai-v3).
-   The Agents SDK does not convert arbitrary legacy HTTPX objects to HTTPX2.
  ⟦EVIDENCE⟧
Ordinary MCP connections do not need application changes. See [MCP Python SDK v1 and v2](mcp.md#mcp-python-sdk-v1-and-v2).
-   Public provider-neutral testing utilities now cover Agent model, Sandbox session, Realtime session, and Voice pipeline workflows without provider or process dependencies. See [Testing](testing.md) for recipes and guidance on when to keep the real provider adapter or integ…
```

</details>

---

## GOLD-B006-09

- **provider**: openai
- **document**: Running agents
- **section** (metadata, not scope): Running agents › Errors and recovery › Error handlers
- **reasoning type**: `exact_lookup` · **secondary**: `defaults_to`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What does `RunErrorHandlerResult.include_in_history` default to?

**A.** `RunErrorHandlerResult.include_in_history` defaults to `True`.

**Atomic claims**

  1. `RunErrorHandlerResult.include_in_history` defaults to `True`.

**Subject and relation** — check the direction against the evidence below.

| | subject | relation | object |
| --- | --- | --- | --- |
| source | `RunErrorHandlerResult.include_in_history` | `defaults_to` | `True`. |
| question | `RunErrorHandlerResult.include_in_history` | `defaults_to` | `True` |

*Source triple read by: named relation.*

**Exact evidence**

`E1` · `ver_2c60e99cfd929a738910b893fd6f1a40` 29933–29995 (62 chars)

```
`RunErrorHandlerResult.include_in_history` defaults to `True`.
```
**critical strings**: `RunErrorHandlerResult.include_in_history`, `True`

**Claim → evidence**

  1. `RunErrorHandlerResult.include_in_history` defaults to `True`. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…tance(data.error, ModelBehaviorError)
    return Recipe(ingredients=[], recovered_from_invalid_output=True)


agent = Agent(
    name="Recipe assistant",
    instructions="Return a structured recipe.",
    output_type=Recipe,
)

result = Runner.run_sync(
    agent,
    "Plan tonight's dinner.",
    error_handlers={"invalid_final_output": on_invalid_final_output},
)
print(result.final_output)
```
  ⟦EVIDENCE⟧
For a max-turns handler, this appends the synthesized fallback output to conversation history and persists it to the configured session. Set `include_in_history=False` when you want the fallback returned to the caller without adding it to result history or session storage.

Use `"model_refusal"` when a model refusal should produce an application-specific fallback instead of ending the run with `M…
```

</details>

---
