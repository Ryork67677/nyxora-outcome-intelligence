# Gold review batch 005

**19 candidates · corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · generated 2026-08-23T16:29:55Z**

Nothing in this file is ground truth. Every candidate is `candidate_unverified`. The evidence is quoted verbatim from the frozen corpus and is authoritative for this review — **do not consult live documentation**, which may have changed since the snapshot.

Two things to know before reading. First, `precheck_holdout_ready` means the record is structurally checkable and nothing more: batch 004 shipped 15 of 15 precheck-ready and its review still repaired ten and rejected one. Second, the `internal_semantic_review_status` on each candidate is a **generation** self-review — the author reading its own output — and is not verification.

Provider {'anthropic': 8, 'openai': 11} · reasoning {'ambiguity_disambiguation': 1, 'configuration_interaction': 9, 'error_behavior': 3, 'exact_lookup': 2, 'lifecycle_compatibility_migration': 4} · 16 distinct documents · median span 133 characters.

| id | provider | reasoning type | shape | chars | question |
| --- | --- | --- | --- | --- | --- |
| `01` | anthropic | ambiguity_disambiguation | multi_document | 224 | In Web fetch tool, what does the `invalid_tool_input` field mean,… |
| `02` | anthropic | configuration_interaction | single_span | 277 | What happens when `jwks.type` is `discovery` and no `discovery_ba… |
| `03` | anthropic | error_behavior | single_span | 70 | What happens when filtering by a non-existent deployment_id? |
| `04` | anthropic | error_behavior | single_span | 93 | What happens if `encrypted_content` is missing or modified? |
| `05` | anthropic | exact_lookup | single_span | 151 | What must `allowed_domains` be? |
| `06` | anthropic | lifecycle_compatibility_migration | single_span | 163 | Where is `fallbacks` supported? |
| `07` | anthropic | lifecycle_compatibility_migration | single_span | 130 | Is `compaction_control` still supported? |
| `08` | anthropic | lifecycle_compatibility_migration | single_span | 135 | Where is `budget_tokens` supported? |
| `09` | openai | configuration_interaction | single_span | 246 | What happens if the arguments are malformed JSON, are valid JSON … |
| `10` | openai | configuration_interaction | single_span | 125 | What does `betas` override? |
| `11` | openai | configuration_interaction | single_span | 149 | What does `AWS_BEDROCK_BASE_URL` override? |
| `12` | openai | configuration_interaction | single_span | 150 | What does `FuseMountPattern` require? |
| `13` | openai | configuration_interaction | single_span | 113 | What does `S3FilesMountPattern` require? |
| `14` | openai | configuration_interaction | single_span | 90 | What does `ApplyPatchTool` require? |
| `15` | openai | configuration_interaction | single_span | 233 | What happens when a [`ComputerTool`][agents.tool.ComputerTool] is… |
| `16` | openai | configuration_interaction | single_span | 117 | What happens when you use a `Session` (e.g., `SQLiteSession`)? |
| `17` | openai | error_behavior | single_span | 115 | What happens if we exceed the `max_turns` passed? |
| `18` | openai | exact_lookup | single_span | 98 | What must `dispatcher` be? |
| `19` | openai | lifecycle_compatibility_migration | single_span | 158 | What happened to `httpAgent`? |

---

## GOLD-B005-01

- **provider**: anthropic
- **document**: Web fetch tool
- **section**: Response › Errors
- **reasoning type**: `ambiguity_disambiguation` · **secondary**: `cross_component`
- **evidence shape**: `multi_document` · **requires all evidence**: True
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** In Web fetch tool, what does the `invalid_tool_input` field mean, and how does that differ from Tool search tool?

**A.** In Web fetch tool, `invalid_tool_input` is: Invalid tool input, such as a malformed URL or a non-HTTP(S) scheme. In Tool search tool, `invalid_tool_input` is: the search input was invalid, for example a malformed regex pattern or a pattern over the 200-character limit.

**Atomic claims**

  1. In Web fetch tool, `invalid_tool_input` is: Invalid tool input, such as a malformed URL or a non-HTTP(S) scheme.
  2. In Tool search tool, `invalid_tool_input` is: the search input was invalid, for example a malformed regex pattern or a pattern over the 200-character limit.

**Ambiguity**

- **term**: `invalid_tool_input`
  - in `Web fetch tool`: Invalid tool input, such as a malformed URL or a non-HTTP(S) scheme
  - in `Tool search tool`: the search input was invalid, for example a malformed regex pattern or a pattern over the 200-character limit
- **scope needed to answer**: Which component the `invalid_tool_input` field belongs to. It is documented in Web fetch tool and in Tool search tool with different meanings, so the answer is undetermined until the component is named.

**Exact evidence**

`E1` · `ver_901356d3ffce0f0478ba2d33aefdf98a` 22545–22636 (91 chars) · Response › Errors

```
* `invalid_tool_input`: Invalid tool input, such as a malformed URL or a non-HTTP(S) scheme
```
**critical strings**: `invalid_tool_input`

`E2` · `ver_b7ea8359f97ca269418988f78e80b870` 28727–28860 (133 chars) · Error handling › Tool result errors (200 status)

```
* `invalid_tool_input`: the search input was invalid, for example a malformed regex pattern or a pattern over the 200-character limit
```
**critical strings**: `invalid_tool_input`

**Claim → evidence**

  1. In Web fetch tool, `invalid_tool_input` is: Invalid tool input, such as a malformed URL or a non-HTT… → `E1`
  2. In Tool search tool, `invalid_tool_input` is: the search input was invalid, for example a malformed … → `E2`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…r, the Claude API returns a 200 (success) response with the error represented in the response body. Claude sees the error result and continues the turn. For example:

```json Output
{
  "type": "web_fetch_tool_result",
  "tool_use_id": "srvtoolu_a93jad",
  "content": {
    "type": "web_fetch_tool_result_error",
    "error_code": "url_not_accessible"
  }
}
```

These are the possible error codes:
  ⟦EVIDENCE⟧
.build();

      Message response = client.messages().create(params);
      IO.println(response);
  }
  ```

  ```php PHP
  $client = new Client();

  $message = $client->messages->create(
      maxTokens: 4096,
      messages: [
          ['role' => 'user', 'content' => 'Find recent articles about quantum computing and analyze the most relevant one in detail']
      ],
      model: 'claude-…
```

</details>

---

## GOLD-B005-02

- **provider**: anthropic
- **document**: Admin
- **section**: Federation Issuers › Create Federation Issuer
- **reasoning type**: `configuration_interaction` · **secondary**: `conditional_behavior`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What happens when `jwks.type` is `discovery` and no `discovery_base` is set?

**A.** The issuer URL must be publicly reachable over HTTPS so Anthropic can fetch the discovery document; for `explicit_url` and `inline` modes the issuer URL is only matched as the JWT's `iss` claim and is not fetched.

**Atomic claims**

  1. When `jwks.type` is `discovery` and no `discovery_base` is set, the issuer URL must be publicly reachable over HTTPS so Anthropic can fetch the discovery document; for `explicit_url` and `inline` modes the issuer URL is only matched as the JWT's `iss` claim and is not fetched.

**Exact evidence**

`E1` · `ver_c299b58fe1f5a4d3a081b550334a7df6` 469462–469739 (277 chars) · Federation Issuers › Create Federation Issuer

```
When `jwks.type` is
`discovery` and no `discovery_base` is set, the issuer URL must be
publicly reachable over HTTPS so Anthropic can fetch the discovery
document; for `explicit_url` and `inline` modes the issuer URL is only
matched as the JWT's `iss` claim and is not fetched.
```
**critical strings**: `jwks.type`, `discovery`, `discovery_base`

**Claim → evidence**

  1. When `jwks.type` is `discovery` and no `discovery_base` is set, the issuer URL must be publicly reac… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…ganizations/federation_issuers`

Register an OIDC issuer that Anthropic will trust for workload identity
federation in your organization.

The `jwks` field controls how the issuer's signing keys are obtained and
takes one of three shapes selected by `type`: `discovery` (resolve keys
through OIDC discovery), `explicit_url` (fetch keys from a fixed JWKS
URL), or `inline` (provide a static key set).
  ⟦EVIDENCE⟧
Requires an OAuth bearer or Console session; Admin API keys are not
accepted.

### Header Parameters

- `"anthropic-beta": optional array of string`

  Optional header to specify the beta version(s) you want to use.

  To use multiple betas, use a comma separated list like `beta1,beta2` or specify the header multiple times for each beta.

### Body Parameters

- `issuer_url: string`

  The `iss`…
```

</details>

---

## GOLD-B005-03

- **provider**: anthropic
- **document**: Beta
- **section**: Deployment Runs › List Deployment Runs › Query Parameters
- **reasoning type**: `error_behavior` · **secondary**: `normative_statement`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What happens when filtering by a non-existent deployment_id?

**A.** It returns 200 with empty data.

**Atomic claims**

  1. Filtering by a non-existent deployment_id returns 200 with empty data.

**Exact evidence**

`E1` · `ver_de7f74230c8f10d30aea5d037a3bd0a5` 2711799–2711869 (70 chars) · Deployment Runs › List Deployment Runs › Query Parameters

```
Filtering by a non-existent deployment_id returns 200 with empty data.
```
**critical strings**: `200 with empty data`

**Claim → evidence**

  1. Filtering by a non-existent deployment_id returns 200 with empty data. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…ptional string`

  Return runs created at or after this time (inclusive).

- `"created_at[lt]": optional string`

  Return runs created strictly before this time (exclusive).

- `"created_at[lte]": optional string`

  Return runs created at or before this time (inclusive).

- `deployment_id: optional string`

  Filter to a specific deployment. Omit to list across all deployments in the workspace.
  ⟦EVIDENCE⟧
- `has_error: optional boolean`

  Filter: true for runs with non-null error, false for runs with non-null session_id. Omit for all.

- `limit: optional number`

  Maximum results per page. Default 20, maximum 1000.

- `page: optional string`

  Opaque pagination cursor. Pass next_page from the previous response. Invalid or expired cursors return 400.

- `trigger_type: optional BetaManagedAgents…
```

</details>

---

## GOLD-B005-04

- **provider**: anthropic
- **document**: Web search tool
- **section**: Response › Search results
- **reasoning type**: `error_behavior` · **secondary**: `conditional_behavior`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What happens if `encrypted_content` is missing or modified?

**A.** The request fails with a 400 validation error.

**Atomic claims**

  1. If `encrypted_content` is missing or modified, the request fails with a 400 validation error.

**Exact evidence**

`E1` · `ver_53da2f78e855c75ec755089c13d44c28` 20614–20707 (93 chars) · Response › Search results

```
If `encrypted_content` is missing or modified, the request fails with a 400 validation error.
```
**critical strings**: `encrypted_content`

**Claim → evidence**

  1. If `encrypted_content` is missing or modified, the request fails with a 400 validation error. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…age`: When the site was last updated
* `encrypted_content`: Encrypted content that you must pass back in multi-turn conversations

To continue a conversation that contains search results, send the assistant's content blocks back exactly as you received them, including each result's `encrypted_content`. The API decrypts that content on later turns to restore the search results in Claude's context.
  ⟦EVIDENCE⟧
### Citations

Citations are always enabled for web search, and each `web_search_result_location` includes:

* `url`: The URL of the cited source
* `title`: The title of the cited source
* `encrypted_index`: A reference that must be passed back for multi-turn conversations
* `cited_text`: Up to 150 characters of the cited content

The web search citation fields `cited_text`, `title`, and `url` d…
```

</details>

---

## GOLD-B005-05

- **provider**: anthropic
- **document**: Server tools
- **section**: Domain filtering
- **reasoning type**: `exact_lookup` · **secondary**: `constraint_required_value`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What must `allowed_domains` be?

**A.** Request-level `allowed_domains` must be a subset of the organization-level allowed list; entries outside it cause the API to return a validation error.

**Atomic claims**

  1. Request-level `allowed_domains` must be a subset of the organization-level allowed list; entries outside it cause the API to return a validation error.

**Exact evidence**

`E1` · `ver_8d2a22e3827c98e0b9d4e1ef411e5353` 40135–40286 (151 chars) · Domain filtering

```
Request-level `allowed_domains` must be a subset of the organization-level allowed list; entries outside it cause the API to return a validation error.
```
**critical strings**: `allowed_domains`

**Claim → evidence**

  1. Request-level `allowed_domains` must be a subset of the organization-level allowed list; entries out… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…*

* Wildcards (`*`) are not allowed in the domain itself, only in the path after it.
* Valid: `example.com/*`, `example.com/*/articles`
* Invalid: `*.example.com`, `ex*.com`

Invalid domain formats are rejected at request time with a 400 `invalid_request_error`.

<Note>
  Request-level domain restrictions work together with any organization-level domain restrictions configured in Claude Console.
  ⟦EVIDENCE⟧
Domains your organization blocks are removed from a request-level allowed list rather than returning an error.
</Note>

<Warning>
  Unicode characters in domain names can bypass domain filters through homograph attacks: `аmazon.com` (with a Cyrillic `а`) looks identical to `amazon.com` but is a different domain. Use ASCII-only domain names in allow and block lists, and audit existing entries for…
```

</details>

---

## GOLD-B005-06

- **provider**: anthropic
- **document**: Beta
- **section**: Models › List Models › Returns
- **reasoning type**: `lifecycle_compatibility_migration` · **secondary**: `compatibility`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** Where is `fallbacks` supported?

**A.** Model IDs this model accepts as `fallbacks[i].model` on the Messages API. An empty list means the `fallbacks` parameter is not supported for this model as primary.

**Atomic claims**

  1. Model IDs this model accepts as `fallbacks[i].model` on the Messages API. An empty list means the `fallbacks` parameter is not supported for this model as primary.

**Exact evidence**

`E1` · `ver_de7f74230c8f10d30aea5d037a3bd0a5` 8864–9027 (163 chars) · Models › List Models › Returns

```
Model IDs this model accepts as `fallbacks[i].model` on the Messages API. An empty list means the `fallbacks` parameter is not supported for this model as primary.
```
**critical strings**: `fallbacks`

**Claim → evidence**

  1. Model IDs this model accepts as `fallbacks[i].model` on the Messages API. An empty list means the `f… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…- `"server-side-fallback-2026-06-01"`

    - `"server-side-fallback-2026-07-01"`

    - `"fallback-credit-2026-06-01"`

    - `"fallback-credit-2026-07-01"`

    - `"agent-memory-2026-07-22"`

    - `"mid-conversation-tool-changes-2026-07-01"`

### Returns

- `data: array of BetaModelInfo`

  - `id: string`

    Unique model identifier.

  - `allowed_fallback_models: array of string or null`
  ⟦EVIDENCE⟧
- `capabilities: BetaModelCapabilities or null`

    Model capability information.

    - `batch: BetaCapabilitySupport`

      Whether the model supports the Batch API.

      - `supported: boolean`

        Whether this capability is supported by the model.

    - `citations: BetaCapabilitySupport`

      Whether the model supports citation generation.

    - `code_execution: BetaCapabilityS…
```

</details>

---

## GOLD-B005-07

- **provider**: anthropic
- **document**: Context editing
- **section**: Client-side compaction (SDK)
- **reasoning type**: `lifecycle_compatibility_migration` · **secondary**: `deprecation`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** Is `compaction_control` still supported?

**A.** The `compaction_control` parameter is deprecated in the Python, TypeScript, and Ruby SDKs and will be removed in a future version.

**Atomic claims**

  1. The `compaction_control` parameter is deprecated in the Python, TypeScript, and Ruby SDKs and will be removed in a future version.

**Exact evidence**

`E1` · `ver_1c53b961e1f5da8124a1e7e8eb92c941` 75250–75380 (130 chars) · Client-side compaction (SDK)

```
The `compaction_control` parameter is deprecated in the Python, TypeScript, and Ruby SDKs and will be removed in a future version.
```
**critical strings**: `compaction_control`

**Claim → evidence**

  1. The `compaction_control` parameter is deprecated in the Python, TypeScript, and Ruby SDKs and will b… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…nthropic recommends server-side compaction over SDK compaction.** [Server-side compaction](https://platform.claude.com/docs/en/build-with-claude/compaction) handles context management automatically with less integration complexity, better token usage calculation, and no client-side limitations. Use SDK compaction only if you specifically need client-side control over the summarization process.
  ⟦EVIDENCE⟧
The SDKs emit a deprecation warning when it is enabled. To use server-side compaction with a tool runner, pass the `compact_20260112` edit in the request's `context_management` parameter.
</Warning>

<Note>
  Compaction is available in the [Python, TypeScript, and Ruby SDKs](https://platform.claude.com/docs/en/cli-sdks-libraries/overview) when using the [`tool_runner` method](https://platform.cla…
```

</details>

---

## GOLD-B005-08

- **provider**: anthropic
- **document**: Prompting Claude Sonnet 5
- **section**: Calibrating effort and thinking depth
- **reasoning type**: `lifecycle_compatibility_migration` · **secondary**: `compatibility`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** Where is `budget_tokens` supported?

**A.** Manual extended thinking (`thinking: {type: "enabled", budget_tokens: N}`) is not supported on Claude Sonnet 5 and returns a 400 error.

**Atomic claims**

  1. Manual extended thinking (`thinking: {type: "enabled", budget_tokens: N}`) is not supported on Claude Sonnet 5 and returns a 400 error.

**Exact evidence**

`E1` · `ver_9c5166b670bf43589ee63d0dbe8b93d2` 5356–5491 (135 chars) · Calibrating effort and thinking depth

```
Manual extended thinking (`thinking: {type: "enabled", budget_tokens: N}`) is not supported on Claude Sonnet 5 and returns a 400 error.
```
**critical strings**: `budget_tokens`

**Claim → evidence**

  1. Manual extended thinking (`thinking: {type: "enabled", budget_tokens: N}`) is not supported on Claud… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…performance. Example:

```text wrap
Thinking adds latency and should only be used when it will meaningfully improve answer quality, typically for problems that require multistep reasoning. When in doubt, respond directly.
```

Conversely, if you're running hard workloads at `medium` and seeing under-thinking, the first lever is to raise effort. If you need finer control, prompt for it directly.
  ⟦EVIDENCE⟧
It was deprecated on Claude Sonnet 4.6 and is now removed. Use adaptive thinking with the effort parameter instead.

<Note>
  If you are running Claude Sonnet 5 at `high`, `xhigh`, or `max` effort, leave headroom in `max_tokens` so the model has room for thinking and tool calls. On long tasks, adaptive thinking can use a large share of the budget; if the budget is tight, you may see a response th…
```

</details>

---

## GOLD-B005-09

- **provider**: openai
- **document**: Human-in-the-loop
- **section**: Human-in-the-loop › Marking tools that need approval
- **reasoning type**: `configuration_interaction` · **secondary**: `conditional_behavior`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What happens if the arguments are malformed JSON, are valid JSON but not an object (for example, `null` or a list), or contain non-standard constants such as `NaN`, `Infinity`, or `-Infinity`?

**A.** The callable is not invoked and the call requires manual approval.

**Atomic claims**

  1. If the arguments are malformed JSON, are valid JSON but not an object (for example, `null` or a list), or contain non-standard constants such as `NaN`, `Infinity`, or `-Infinity`, the callable is not invoked and the call requires manual approval.

**Exact evidence**

`E1` · `ver_ae3bfcc42c733c5051abda30f0f6db07` 1609–1855 (246 chars) · Human-in-the-loop › Marking tools that need approval

```
If the arguments are malformed JSON, are valid JSON but not an object (for example, `null` or a list), or contain non-standard constants such as `NaN`, `Infinity`, or `-Infinity`, the callable is not invoked and the call requires manual approval.
```
**critical strings**: `null`, `NaN`, `Infinity`

**Claim → evidence**

  1. If the arguments are malformed JSON, are valid JSON but not an object (for example, `null` or a list… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…upport programmatic approval callbacks so the run can continue without pausing.

## Marking tools that need approval

Set `needs_approval` to `True` to always require approval or provide an async function that decides per call. The callable receives the run context, parsed tool parameters, and the tool call ID.

Callable approval rules fail closed when the SDK cannot safely inspect the arguments.
  ⟦EVIDENCE⟧
This behavior is the same for Runner and Realtime tool calls.

```python
from agents import Agent
from agents.decorators import tool


@tool(needs_approval=True)
async def cancel_order(order_id: int) -> str:
    return f"Cancelled order {order_id}"


async def requires_review(_ctx, params, _call_id) -> bool:
    return "refund" in params.get("subject", "").lower()


@tool(needs_approval=requires_…
```

</details>

---

## GOLD-B005-10

- **provider**: openai
- **document**: Models
- **section**: Models › OpenAI models › Hosted multi-agent (experimental) › Current limitations
- **reasoning type**: `configuration_interaction` · **secondary**: `overrides`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What does `betas` override?

**A.** The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.

**Atomic claims**

  1. The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.

**Exact evidence**

`E1` · `ver_ae909bf8b4bbbe1d1a11119447f7ac94` 19331–19456 (125 chars) · Models › OpenAI models › Hosted multi-agent (experimental) › Current limitations

```
The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.
```
**critical strings**: `betas`, `reasoning.summary`, `max_tool_calls`

**Claim → evidence**

  1. The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_age… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…nge the active local SDK `Agent`. They are rejected when this experimental model is used because every hosted agent receives the same handoff tools, which would create conflicting ownership.
-   Agents-as-tools remain available, but using them creates nested client-side and server-side orchestration. Evaluate the additional latency, cost, and tool exposure deliberately.

#### Current limitations
  ⟦EVIDENCE⟧
The Responses `/compact` endpoint is not supported by the beta, although an explicit `context_management.compact_threshold` may be used because the service automatically compacts each hosted agent context independently.

One `OpenAIHostedMultiAgentModel` instance owns at most one active hosted response at a time. If a run is abandoned while waiting for local function output, call `await model.clo…
```

</details>

---

## GOLD-B005-11

- **provider**: openai
- **document**: OpenAI Python API library
- **section**: configured through AWS_REGION, AWS_DEFAULT_REGION, or your AWS profile.
- **reasoning type**: `configuration_interaction` · **secondary**: `overrides`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What does `AWS_BEDROCK_BASE_URL` override?

**A.** Pass `base_url` to `bedrock(...)` or set `AWS_BEDROCK_BASE_URL` to override the derived `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint.

**Atomic claims**

  1. Pass `base_url` to `bedrock(...)` or set `AWS_BEDROCK_BASE_URL` to override the derived `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint.

**Exact evidence**

`E1` · `ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` 33783–33932 (149 chars) · configured through AWS_REGION, AWS_DEFAULT_REGION, or your AWS profile.

```
Pass `base_url` to `bedrock(...)` or set `AWS_BEDROCK_BASE_URL` to override the derived `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint.
```
**critical strings**: `AWS_BEDROCK_BASE_URL`, `base_url`

**Claim → evidence**

  1. Pass `base_url` to `bedrock(...)` or set `AWS_BEDROCK_BASE_URL` to override the derived `https://bed… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…s such as ECS, EKS, and EC2 metadata. To select a named profile:

```py
client = OpenAI(
    provider=bedrock(
        profile="my-profile",
    )
)
```

You can also pass `access_key_id` and `secret_access_key`, with an optional `session_token`, or a refreshable `credential_provider` that returns botocore-compatible credentials. Explicit bearer and AWS credential options are mutually exclusive.
  ⟦EVIDENCE⟧
SigV4 requests require replayable, fully serialized request bodies. Standard JSON requests already meet this requirement, and response streaming is unaffected. Low-level one-shot request streams must be buffered before sending, or sent with bearer authentication and retries disabled.

Bearer tokens remain available as a compatibility or manual authentication mode. Set `AWS_BEARER_TOKEN_BEDROCK`…
```

</details>

---

## GOLD-B005-12

- **provider**: openai
- **document**: Sandbox clients
- **section**: Sandbox clients › Supported hosted platforms › Size Modal sandboxes
- **reasoning type**: `configuration_interaction` · **secondary**: `requires`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What does `FuseMountPattern` require?

**A.** `FuseMountPattern` requires broad acknowledgement because `blobfuse2` discovers ambient Azure authority, even when no inline credential is configured.

**Atomic claims**

  1. `FuseMountPattern` requires broad acknowledgement because `blobfuse2` discovers ambient Azure authority, even when no inline credential is configured.

**Exact evidence**

`E1` · `ver_3d4b8881962381cbfba18ade50c598e1` 11024–11174 (150 chars) · Sandbox clients › Supported hosted platforms › Size Modal sandboxes

```
`FuseMountPattern` requires broad acknowledgement because `blobfuse2` discovers ambient Azure authority, even when no inline credential is configured.
```
**critical strings**: `FuseMountPattern`, `blobfuse2`

**Claim → evidence**

  1. `FuseMountPattern` requires broad acknowledgement because `blobfuse2` discovers ambient Azure author… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…ority. It rejects a mount that requires protected authority before starting the sandbox or mount helper unless trusted application code explicitly acknowledges the exposure for the exact mount path.

Credentialless `rclone` mounts are limited to S3, GCS, R2, and Azure Blob. An in-container Box mount requires a non-interactive authentication source and the acknowledgement that matches that source.
  ⟦EVIDENCE⟧
`S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses ambient IAM authority. These requirements also apply when Docker is the backend; the check marks below indicate that Docker can execute the mount after the applicable authority boundary is satisfied.

For a mount entry named `"data"`, retain the copied `Manifest` returned by the acknowledgement that matches…
```

</details>

---

## GOLD-B005-13

- **provider**: openai
- **document**: Sandbox clients
- **section**: Sandbox clients › Supported hosted platforms › Size Modal sandboxes
- **reasoning type**: `configuration_interaction` · **secondary**: `requires`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What does `S3FilesMountPattern` require?

**A.** `S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses ambient IAM authority.

**Atomic claims**

  1. `S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses ambient IAM authority.

**Exact evidence**

`E1` · `ver_3d4b8881962381cbfba18ade50c598e1` 11175–11288 (113 chars) · Sandbox clients › Supported hosted platforms › Size Modal sandboxes

```
`S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses ambient IAM authority.
```
**critical strings**: `S3FilesMountPattern`, `mount.s3files`

**Claim → evidence**

  1. `S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses ambient I… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…owledges the exposure for the exact mount path.

Credentialless `rclone` mounts are limited to S3, GCS, R2, and Azure Blob. An in-container Box mount requires a non-interactive authentication source and the acknowledgement that matches that source. `FuseMountPattern` requires broad acknowledgement because `blobfuse2` discovers ambient Azure authority, even when no inline credential is configured.
  ⟦EVIDENCE⟧
These requirements also apply when Docker is the backend; the check marks below indicate that Docker can execute the mount after the applicable authority boundary is satisfied.

For a mount entry named `"data"`, retain the copied `Manifest` returned by the acknowledgement that matches the configured authority:

```python
# Mount-scoped values such as inline access keys.
manifest = manifest.with_i…
```

</details>

---

## GOLD-B005-14

- **provider**: openai
- **document**: Tools
- **section**: Tools › Local runtime tools
- **reasoning type**: `configuration_interaction` · **secondary**: `requires`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What does `ApplyPatchTool` require?

**A.** `ComputerTool` and `ApplyPatchTool` always require local implementations that you provide.

**Atomic claims**

  1. `ComputerTool` and `ApplyPatchTool` always require local implementations that you provide.

**Exact evidence**

`E1` · `ver_cbeb36b7cf9a5e241940a011629b6f1b` 14491–14581 (90 chars) · Tools › Local runtime tools

```
`ComputerTool` and `ApplyPatchTool` always require local implementations that you provide.
```
**critical strings**: `ApplyPatchTool`, `ComputerTool`

**Claim → evidence**

  1. `ComputerTool` and `ApplyPatchTool` always require local implementations that you provide. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
….py` for complete examples.
-   OpenAI platform guides: [Shell](https://platform.openai.com/docs/guides/tools-shell) and [Skills](https://platform.openai.com/docs/guides/tools-skills).

## Local runtime tools

Local runtime tools execute outside the model response itself. The model still decides when to call them, but your application or configured execution environment performs the actual work.
  ⟦EVIDENCE⟧
`ShellTool` spans both modes: use the hosted-container configuration above when you want managed execution, or the local runtime configuration below when you want commands to run in your own process.

Local runtime tools require you to supply implementations:

-   [`ComputerTool`][agents.tool.ComputerTool]: implement the [`Computer`][agents.computer.Computer] or [`AsyncComputer`][agents.computer.…
```

</details>

---

## GOLD-B005-15

- **provider**: openai
- **document**: Tools
- **section**: Tools › Local runtime tools › ComputerTool and the Responses computer tool
- **reasoning type**: `configuration_interaction` · **secondary**: `normative_statement`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What happens when a [`ComputerTool`][agents.tool.ComputerTool] is present?

**A.** `tool_choice="computer"`, `"computer_use"`, and `"computer_use_preview"` are all accepted and normalized to the built-in selector that matches the effective request model.

**Atomic claims**

  1. When a [`ComputerTool`][agents.tool.ComputerTool] is present, `tool_choice="computer"`, `"computer_use"`, and `"computer_use_preview"` are all accepted and normalized to the built-in selector that matches the effective request model.

**Exact evidence**

`E1` · `ver_cbeb36b7cf9a5e241940a011629b6f1b` 17432–17665 (233 chars) · Tools › Local runtime tools › ComputerTool and the Responses computer tool

```
When a [`ComputerTool`][agents.tool.ComputerTool] is present, `tool_choice="computer"`, `"computer_use"`, and `"computer_use_preview"` are all accepted and normalized to the built-in selector that matches the effective request model.
```
**critical strings**: `ComputerTool`, `tool_choice="computer"`, `"computer_use"`, `"computer_use_preview"`

**Claim → evidence**

  1. When a [`ComputerTool`][agents.tool.ComputerTool] is present, `tool_choice="computer"`, `"computer_u… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…The SDK chooses that wire shape from the effective model on the actual Responses request. If you use a prompt template and the request omits `model` because the prompt owns it, the SDK keeps the preview-compatible computer payload unless you either keep `model="gpt-5.5"` explicit or force the GA selector with `ModelSettings(tool_choice="computer")` or `ModelSettings(tool_choice="computer_use")`.
  ⟦EVIDENCE⟧
Without a `ComputerTool`, those strings still behave like ordinary function names.

This distinction matters when `ComputerTool` is backed by a [`ComputerProvider`][agents.tool.ComputerProvider] factory. The GA `computer` payload does not need `environment` or dimensions at serialization time, so serialization can occur before a factory has produced a `Computer` or `AsyncComputer` instance. Previ…
```

</details>

---

## GOLD-B005-16

- **provider**: openai
- **document**: Usage
- **section**: Usage › Accessing usage with sessions
- **reasoning type**: `configuration_interaction` · **secondary**: `conditional_behavior`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What happens when you use a `Session` (e.g., `SQLiteSession`)?

**A.** Each call to `Runner.run(...)` returns usage for that specific run.

**Atomic claims**

  1. When you use a `Session` (e.g., `SQLiteSession`), each call to `Runner.run(...)` returns usage for that specific run.

**Exact evidence**

`E1` · `ver_f8002fe268b970eaea8d640f9dd91fb3` 4684–4801 (117 chars) · Usage › Accessing usage with sessions

```
When you use a `Session` (e.g., `SQLiteSession`), each call to `Runner.run(...)` returns usage for that specific run.
```
**critical strings**: `Session`, `SQLiteSession`

**Claim → evidence**

  1. When you use a `Session` (e.g., `SQLiteSession`), each call to `Runner.run(...)` returns usage for t… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…` does not currently populate `ModelResponse.raw_usage` in either streaming or non-streaming runs, so `preserve_raw_usage=True` has no effect with that adapter. Continue to use the normalized [`Usage`][agents.usage.Usage] fields when using `LitellmModel`, or choose an adapter that supports raw usage preservation when provider-specific field presence is required.

## Accessing usage with sessions
  ⟦EVIDENCE⟧
Sessions maintain conversation history for context, but each run's usage is independent.

```python
session = SQLiteSession("my_conversation")

first = await Runner.run(agent, "Hi!", session=session)
print(first.context_wrapper.usage.total_tokens)  # Usage for first run

second = await Runner.run(agent, "Can you elaborate?", session=session)
print(second.context_wrapper.usage.total_tokens)  # Usa…
```

</details>

---

## GOLD-B005-17

- **provider**: openai
- **document**: Running agents
- **section**: Running agents › Runner lifecycle and configuration › The agent loop
- **reasoning type**: `error_behavior` · **secondary**: `conditional_behavior`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What happens if we exceed the `max_turns` passed?

**A.** We raise a `MaxTurnsExceeded` exception.

**Atomic claims**

  1. If we exceed the `max_turns` passed, we raise a [`MaxTurnsExceeded`][agents.exceptions.MaxTurnsExceeded] exception.

**Exact evidence**

`E1` · `ver_2c60e99cfd929a738910b893fd6f1a40` 1936–2051 (115 chars) · Running agents › Runner lifecycle and configuration › The agent loop

```
If we exceed the `max_turns` passed, we raise a [`MaxTurnsExceeded`][agents.exceptions.MaxTurnsExceeded] exception.
```
**critical strings**: `max_turns`, `MaxTurnsExceeded`

**Claim → evidence**

  1. If we exceed the `max_turns` passed, we raise a [`MaxTurnsExceeded`][agents.exceptions.MaxTurnsExcee… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…the LLM for the current agent, with the current input.
2. The LLM produces its output.
    1. If the runner classifies the LLM's output as final output, the loop ends and we return the result.
    2. If the LLM requests a handoff, we update the current agent and input, and re-run the loop.
    3. If the LLM produces tool calls, we run those tool calls, append the results, and re-run the loop.
3.
  ⟦EVIDENCE⟧
Pass `max_turns=None` to disable this turn limit.

!!! note

    The rule for whether the LLM output is considered as a "final output" is that it produces text output with the desired type, and there are no tool calls.

### Streaming

Streaming allows you to additionally receive streaming events as the LLM runs. Once the stream is done, the [`RunResultStreaming`][agents.result.RunResultStreaming]…
```

</details>

---

## GOLD-B005-18

- **provider**: openai
- **document**: OpenAI TypeScript and JavaScript API Library
- **section**: OpenAI TypeScript and JavaScript API Library › Advanced Usage › Fetch options › Configuring proxies
- **reasoning type**: `exact_lookup` · **secondary**: `constraint_required_value`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What must `dispatcher` be?

**A.** Undici-specific options like `dispatcher` must be paired with the matching `fetch` implementation.

**Atomic claims**

  1. Undici-specific options like `dispatcher` must be paired with the matching `fetch` implementation.

**Exact evidence**

`E1` · `ver_f30a6447e4df2ab76e4c1475f353109c` 24178–24276 (98 chars) · OpenAI TypeScript and JavaScript API Library › Advanced Usage › Fetch options › Configuring proxies

```
Undici-specific options like `dispatcher` must be paired with the matching `fetch` implementation.
```
**critical strings**: `dispatcher`, `fetch`

**Claim → evidence**

  1. Undici-specific options like `dispatcher` must be paired with the matching `fetch` implementation. → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
…proxy
options to requests:

**Node** <sup>[[docs](https://github.com/nodejs/undici/blob/main/docs/docs/api/ProxyAgent.md#example---proxyagent-with-fetch)]</sup>

```ts
import OpenAI from 'openai';
import { fetch, ProxyAgent } from 'undici';

const proxyAgent = new ProxyAgent('http://localhost:8888');
const client = new OpenAI({
  fetch,
  fetchOptions: {
    dispatcher: proxyAgent,
  },
});
```
  ⟦EVIDENCE⟧
**Bun** <sup>[[docs](https://bun.sh/guides/http/proxy)]</sup>

```ts
import OpenAI from 'openai';

const client = new OpenAI({
  fetchOptions: {
    proxy: 'http://localhost:8888',
  },
});
```

**Deno** <sup>[[docs](https://docs.deno.com/api/deno/~/Deno.createHttpClient)]</sup>

```ts
import OpenAI from 'npm:openai';

const httpClient = Deno.createHttpClient({ proxy: { url: 'http://localhost:88…
```

</details>

---

## GOLD-B005-19

- **provider**: openai
- **document**: Migration guide
- **section**: Migration guide › Breaking changes › Removed `httpAgent` in favor of `fetchOptions`
- **reasoning type**: `lifecycle_compatibility_migration` · **secondary**: `removal`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **generation self-review**: READY_FOR_INDEPENDENT_REVIEW · **precheck holdout-ready**: True

**Q.** What happened to `httpAgent`?

**A.** The `httpAgent` client option has been removed in favor of a platform-specific `fetchOptions` property.

**Atomic claims**

  1. The `httpAgent` client option has been removed in favor of a [platform-specific `fetchOptions` property](https://github.com/openai/openai-node#fetch-options).

**Exact evidence**

`E1` · `ver_e8a7b17b5af64679cadea33cd8f6d250` 10081–10239 (158 chars) · Migration guide › Breaking changes › Removed `httpAgent` in favor of `fetchOptions`

```
The `httpAgent` client option has been removed in favor of a [platform-specific `fetchOptions` property](https://github.com/openai/openai-node#fetch-options).
```
**critical strings**: `httpAgent`, `fetchOptions`

**Claim → evidence**

  1. The `httpAgent` client option has been removed in favor of a [platform-specific `fetchOptions` prope… → `E1`

<details><summary>surrounding context (review only — not part of the gold evidence)</summary>

```
….checkpoints.permissions.delete();
client.vectorStores.delete();
client.vectorStores.files.delete();
client.beta.assistants.delete();
client.beta.threads.delete();
client.beta.threads.messages.delete();
client.responses.delete();
client.evals.delete();
client.evals.runs.delete();
client.containers.delete();
client.containers.files.delete();
```

### Removed `httpAgent` in favor of `fetchOptions`
  ⟦EVIDENCE⟧
This change was made as `httpAgent` relied on `node:http` agents which are not supported by any runtime's builtin fetch implementation.

If you were using `httpAgent` for proxy support, check out the [new proxy documentation](https://github.com/openai/openai-node#configuring-proxies).

Before:

```ts
import OpenAI from 'openai';
import http from 'http';
import { HttpsProxyAgent } from 'https-prox…
```

</details>

---
