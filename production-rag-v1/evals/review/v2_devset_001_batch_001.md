# V2-DEVSET-001 review packet (batch 101)

**50 candidates · corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · generated 2026-09-01T02:20:09Z (2026-08-31 22:20 ET)**

Nothing in this file is ground truth. Every candidate is `candidate_unverified`. The evidence below is quoted verbatim from the frozen corpus and is authoritative for this review — **do not consult live documentation**, which may have changed since the snapshot.

For each candidate, judge the *proposed* question, answer and claims against the evidence and its surrounding context only. Return one record per candidate with verdict `PASS | FAIL | FIX_REQUIRED | UNCERTAIN` and the GOLD review fields in `docs/GOLD-REVIEW-PROCEDURE.md`.

ID prefix `V2D-`. This is a v2 **development** candidate set, not frozen gold, not gold150-v1 holdout, and not gold150-v1 validation.

---

## V2D-01

- **provider**: anthropic
- **document**: Context editing
- **section**: Client-side compaction (SDK) › Configuration options
- **source span**: `ver_1c53b961e1f5da8124a1e7e8eb92c941` chars 82891–83109
- **evidence kind**: `parameter_table_row`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: correct_document_difficult_passage, parameter_error_literal_lookup, identifier_vs_semantic_distractor, same_document_passage_discrimination
- **binding**: structural: parameter is the row's first cell, requiredness is column 2 of the same row
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> Is the `enabled` parameter required?

**Proposed answer**: Yes, it is required.

**Proposed atomic claims**: ``enabled` is required.`

**Critical strings**: enabled, Yes

**Generator notes**: Row-scoped association, so the state cannot belong to a different parameter. Reviewer should confirm the table is a parameter table and that the column header means what it appears to mean.

### Evidence E1 (verbatim, authoritative)

`ver_1c53b961e1f5da8124a1e7e8eb92c941` chars 82891–83109 · hash `58ff96baa79e1a5a…`

```
| `enabled`                 | boolean | Yes      | -                                                                                                                          | Whether to enable automatic compaction   |
```

<details><summary>Context before</summary>

```
nted in report.md...\n\n# Important Discoveries\n- Configuration files use YAML format\n- Found 3 deprecated dependencies\n- Test coverage at 67%\n\n# Next Steps\n1. Analyze remaining files in /src/legacy\n2. Complete final report sections...\n\n# Context to Preserve\nUser prefers markdown format with executive summary first..."
  }
]
```

Claude continues working from this summary as if it were the original conversation history.

### Configuration options

| Parameter                 | Type    | Required | Default                                                                                                                    | Description                              |
| ------------------------- | ------- | -------- | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |

```

</details>

<details><summary>Context after</summary>

```

| `context_token_threshold` | number  | No       | 100,000                                                                                                                    | Token count at which compaction triggers |
| `model`                   | string  | No       | Same as main model                                                                                                         | Model to use for generating summaries    |
| `summary_prompt`          | string  | No       | See [Default summary prompt](https://platform.claude.com/docs/en/build-with-claude/context-editing#default-summary-prompt) | Custom prompt for summary generation     |

#### Choosing a token threshold

The threshold determines when compaction occurs. A lower threshold means more frequent compactions with smaller context windows. A higher threshold allows more context but risks hitting limits.

<Tabs>
  <Tab
```

</details>

---

## V2D-02

- **provider**: anthropic
- **document**: Context editing
- **section**: Client-side compaction (SDK) › Configuration options
- **source span**: `ver_1c53b961e1f5da8124a1e7e8eb92c941` chars 83110–83328
- **evidence kind**: `parameter_table_row`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: correct_document_difficult_passage, parameter_error_literal_lookup, identifier_vs_semantic_distractor, lexical_query_shape, same_document_passage_discrimination
- **binding**: structural: parameter is the row's first cell, requiredness is column 2 of the same row
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> Is the `context_token_threshold` parameter required?

**Proposed answer**: No, it is optional.

**Proposed atomic claims**: ``context_token_threshold` is optional.`

**Critical strings**: context_token_threshold, No

**Generator notes**: Row-scoped association, so the state cannot belong to a different parameter. Reviewer should confirm the table is a parameter table and that the column header means what it appears to mean.

### Evidence E1 (verbatim, authoritative)

`ver_1c53b961e1f5da8124a1e7e8eb92c941` chars 83110–83328 · hash `a8126af82dee9bd1…`

```
| `context_token_threshold` | number  | No       | 100,000                                                                                                                    | Token count at which compaction triggers |
```

<details><summary>Context before</summary>

```
inal report sections...\n\n# Context to Preserve\nUser prefers markdown format with executive summary first..."
  }
]
```

Claude continues working from this summary as if it were the original conversation history.

### Configuration options

| Parameter                 | Type    | Required | Default                                                                                                                    | Description                              |
| ------------------------- | ------- | -------- | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `enabled`                 | boolean | Yes      | -                                                                                                                          | Whether to enable automatic compaction   |

```

</details>

<details><summary>Context after</summary>

```

| `model`                   | string  | No       | Same as main model                                                                                                         | Model to use for generating summaries    |
| `summary_prompt`          | string  | No       | See [Default summary prompt](https://platform.claude.com/docs/en/build-with-claude/context-editing#default-summary-prompt) | Custom prompt for summary generation     |

#### Choosing a token threshold

The threshold determines when compaction occurs. A lower threshold means more frequent compactions with smaller context windows. A higher threshold allows more context but risks hitting limits.

<Tabs>
  <Tab title="cURL">
    <Note>
      Compaction runs client-side in the SDK `tool_runner` helpers, so it has no direct HTTP equivalent. Use [server-side compaction](https://platform.claude.com/docs/en/build-with-claude/compa
```

</details>

---

## V2D-03

- **provider**: anthropic
- **document**: Compliance API
- **section**: Chats › List chats › Query Parameters
- **source span**: `ver_1d58a563501b073d898977de6bc2a823` chars 4640364–4640538
- **evidence kind**: `configuration_interaction`
- **evidence shape**: `single_span`
- **reasoning type**: `configuration_interaction`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, lexical_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does `created_at` require?

**Proposed answer**: For org-wide queries, any time filter must match the sort key: `created_at.*` filters require `order_by=created_at`, and `updated_at.*` filters require `order_by=updated_at`.

**Proposed atomic claims**: For org-wide queries, any time filter must match the sort key: `created_at.*` filters require `order_by=created_at`, and `updated_at.*` filters require `order_by=updated_at`.

**Critical strings**: created_at, order_by, updated_at

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_1d58a563501b073d898977de6bc2a823` chars 4640364–4640538 · hash `c8a02c427ca5f0ee…`

```
For org-wide queries, any time filter must match the sort key: `created_at.*` filters require `order_by=created_at`, and `updated_at.*` filters require `order_by=updated_at`.
```

<details><summary>Context before</summary>

```
e from the most recent response. Clients should treat this value as an opaque string and not attempt to parse or interpret its contents, as the format may change without notice.

- `created_at: optional object { gt, gte, lt, lte }`

  - `gt: optional string`

    Filter chats created after this time (RFC 3339 format)

  - `gte: optional string`

    Filter chats created at or after this time (RFC 3339 format)

  - `lt: optional string`

    Filter chats created before this time (RFC 3339 format)

  - `lte: optional string`

    Filter chats created at or before this time (RFC 3339 format)

- `limit: optional number`

  Maximum results (default: 100, max: 1000)

- `order_by: optional "created_at" or "updated_at"`

  Sort key for results. `created_at` (default) sorts by chat creation time. `updated_at` sorts by last update time and is only supported for org-wide queries (omit user_ids[]). 
```

</details>

<details><summary>Context after</summary>

```


  - `"created_at"`

  - `"updated_at"`

- `organization_ids: optional array of string`

  Filter by organization IDs (accepts `org_...` or organization UUID). Enumerate IDs via `GET /v1/compliance/organizations`.

- `project_ids: optional array of string`

  Filter by project IDs (accepts `claude_proj_...`). Enumerate IDs via `GET /v1/compliance/apps/projects`. Requires user_ids[]; not supported for org-wide queries.

- `updated_at: optional object { gt, gte, lt, lte }`

  - `gt: optional string`

    Filter chats updated after this time (RFC 3339 format)

  - `gte: optional string`

    Filter chats updated at or after this time (RFC 3339 format)

  - `lt: optional string`

    Filter chats updated before this time (RFC 3339 format)

  - `lte: optional string`

    Filter chats updated at or before this time (RFC 3339 format)

- `user_ids: optional array of string`

  Filter to chats 
```

</details>

---

## V2D-04

- **provider**: anthropic
- **document**: Handle streaming refusals
- **section**: Reset context after refusal
- **source span**: `ver_93d1f239133ba85f0e9f7725859fea08` chars 2220–2325
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `configuration_interaction`
- **stress types**: short_evidence_unit, parameter_error_literal_lookup, identifier_vs_semantic_distractor, lexical_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens when you receive **`stop_reason`: `refusal`**?

**Proposed answer**: You must reset the conversation context before continuing.

**Proposed atomic claims**: When you receive **`stop_reason`: `refusal`**, you must reset the conversation context before continuing.

**Critical strings**: stop_reason, refusal

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_93d1f239133ba85f0e9f7725859fea08` chars 2220–2325 · hash `82a5b65ca2cea41f…`

```
When you receive **`stop_reason`: `refusal`**, you must reset the conversation context before continuing.
```

<details><summary>Context before</summary>

```
d because it could enable cyber harm."
  }
}
```

In the event stream, `stop_details` arrives on the `message_delta` event alongside `stop_reason`.

<Note>
  A `refusal` response from streaming classifiers includes a `stop_details` object with a `category` and a human-readable `explanation` that you can surface to the user. See [Refusals and fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback#refusal-response) for the full response shape and the available categories.

  On a refusal the `stop_details` object is always present, but its `category` and `explanation` fields can be `null`, for example when the refusal maps to no named category. Branch on `stop_reason` or `stop_details.type` rather than assuming `category` and `explanation` are populated, and provide your own user-facing messaging when they are `null`.
</Note>

## Reset context after refusal


```

</details>

<details><summary>Context after</summary>

```
 You can remove or rephrase the turn that triggered the refusal, or clear the conversation history entirely. Attempting to continue without resetting will result in continued refusals.

<Note>
  Usage metrics are still provided in the response, even when the response is refused.

  When a refusal arrives before Claude generates any output, you are not billed for the request on the Claude API, and the usage counts in that response are informational only. When Claude generates output before the refusal, you are billed for that request.
</Note>

<Tip>
  Resetting context is not the only way to recover. You can also retry the refused request on a different Claude model, and the [Refusals and fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback) page shows how to set that up with server-side fallback, the SDK middleware, or a manual retry.
</Tip>

## Implement
```

</details>

---

## V2D-05

- **provider**: anthropic
- **document**: Admin
- **section**: Usage Report › Get Messages Usage Report › Query Parameters
- **source span**: `ver_c299b58fe1f5a4d3a081b550334a7df6` chars 145736–145804
- **evidence kind**: `normative_statement`
- **evidence shape**: `single_span`
- **reasoning type**: `configuration_interaction`
- **stress types**: short_evidence_unit, identifier_vs_semantic_distractor
- **binding**: template-captured-groups
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does `speed` require?

**Proposed answer**: The `fast-mode-2026-02-01` beta header.

**Proposed atomic claims**: ``speed` requires the `fast-mode-2026-02-01` beta header.`

**Critical strings**: speed, fast-mode-2026-02-01

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_c299b58fe1f5a4d3a081b550334a7df6` chars 145736–145804 · hash `68696c806a8d4785…`

```
Grouping by `speed` requires the `fast-mode-2026-02-01` beta header.
```

<details><summary>Context before</summary>

```

  Time buckets that start on or after this RFC 3339 timestamp will be returned.
  Each time bucket will be snapped to the start of the minute/hour/day in UTC.

- `account_ids: optional array of string`

  Restrict usage returned to the specified user account ID(s).

- `api_key_ids: optional array of string`

  Restrict usage returned to the specified API key ID(s).

- `bucket_width: optional "1d" or "1h" or "1m"`

  Time granularity of the response data.

  - `"1d"`

  - `"1h"`

  - `"1m"`

- `context_window: optional array of "0-200k" or "200k-1M"`

  Restrict usage returned to the specified context window(s).

  - `"0-200k"`

  - `"200k-1M"`

- `ending_at: optional string`

  Time buckets that end before this RFC 3339 timestamp will be returned.

- `group_by: optional array of "account_id" or "api_key_id" or "context_window" or 6 more`

  Group by any subset of the available options. 
```

</details>

<details><summary>Context after</summary>

```


  - `"account_id"`

  - `"api_key_id"`

  - `"context_window"`

  - `"inference_geo"`

  - `"model"`

  - `"service_account_id"`

  - `"service_tier"`

  - `"speed"`

  - `"workspace_id"`

- `inference_geos: optional array of "global" or "not_available" or "us"`

  Restrict usage returned to the specified inference geo(s). Use `not_available` for models that do not support specifying `inference_geo`.

  - `"global"`

  - `"not_available"`

  - `"us"`

- `limit: optional number`

  Maximum number of time buckets to return in the response.

  The default and max limits depend on `bucket_width`:
  • `"1d"`: Default of 7 days, maximum of 31 days
  • `"1h"`: Default of 24 hours, maximum of 168 hours
  • `"1m"`: Default of 60 minutes, maximum of 1440 minutes

- `models: optional array of string`

  Restrict usage returned to the specified model(s).

- `page: optional string`

  Optionally se
```

</details>

---

## V2D-06

- **provider**: anthropic
- **document**: Fast mode (research preview)
- **section**: Checking which speed was used
- **source span**: `ver_cc7d6ed2a636d74fc7aca7885ba9ce60` chars 9863–9935
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `configuration_interaction`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens when a request with `speed: "fast"` succeeds?

**Proposed answer**: `usage.speed` is `"fast"`.

**Proposed atomic claims**: `When a request with `speed: "fast"` succeeds, `usage.speed` is `"fast"`.`

**Critical strings**: usage.speed

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_cc7d6ed2a636d74fc7aca7885ba9ce60` chars 9863–9935 · hash `2d30e610b6255b61…`

```
When a request with `speed: "fast"` succeeds, `usage.speed` is `"fast"`.
```

<details><summary>Context before</summary>

```
opic-fast-input-tokens-reset`      | Time when the fast mode input token limit resets  |
| `anthropic-fast-output-tokens-limit`     | Maximum fast mode output tokens per minute        |
| `anthropic-fast-output-tokens-remaining` | Remaining fast mode output tokens                 |
| `anthropic-fast-output-tokens-reset`     | Time when the fast mode output token limit resets |

For tier-specific rate limits, see the [Rate limits](https://platform.claude.com/docs/en/api/rate-limits) page.

## Checking which speed was used

The response `usage` object includes a `speed` field that indicates which speed was used, either `"fast"` or `"standard"`. Requesting `speed: "fast"` on a [model that doesn't support fast mode](https://platform.claude.com/docs/en/build-with-claude/fast-mode#supported-models) returns an error, and so does exceeding fast mode's rate limits or capacity (a `429` or `529`). 
```

</details>

<details><summary>Context after</summary>

```
 If you are using Claude Opus 4.6 and request fast mode, its behavior is unique. Instead of returning an error like other models that don't support fast mode, it silently switches to standard speed. Though there is no error with Opus 4.6, the `speed` field accurately shows `"standard"`.

<CodeGroup>
  ```bash cURL
  curl https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "anthropic-beta: fast-mode-2026-02-01" \
    -H "content-type: application/json" \
    -d '{
      "model": "claude-opus-5",
      "max_tokens": 1024,
      "speed": "fast",
      "messages": [{"role": "user", "content": "Hello"}]
    }'
  ```

  ```bash CLI
  ant beta:messages create \
    --beta fast-mode-2026-02-01 \
    --transform usage.speed \
    --raw-output <<'YAML'
  model: claude-opus-5
  max_tokens: 1024
  speed: fast
  messages:
  
```

</details>

---

## V2D-07

- **provider**: anthropic
- **document**: Computer use tool
- **section**: How to implement computer use › Tool parameters
- **source span**: `ver_d9ba3ab0d872dd86047c7ed6dc783235` chars 33274–33442
- **evidence kind**: `parameter_table_row`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, parameter_error_literal_lookup, identifier_vs_semantic_distractor, lexical_query_shape
- **binding**: structural: parameter is the row's first cell, requiredness is column 1 of the same row
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> Is the `display_width_px` parameter required?

**Proposed answer**: Yes, it is required.

**Proposed atomic claims**: ``display_width_px` is required.`

**Critical strings**: display_width_px, Yes

**Generator notes**: Row-scoped association, so the state cannot belong to a different parameter. Reviewer should confirm the table is a parameter table and that the column header means what it appears to mean.

### Evidence E1 (verbatim, authoritative)

`ver_d9ba3ab0d872dd86047c7ed6dc783235` chars 33274–33442 · hash `7906c9aaf36ac236…`

```
| `display_width_px`  | Yes      | Display width in pixels                                                                                                             |
```

<details><summary>Context before</summary>

```
l_amount": 3,
    "text": "shift"
  }
  ```

  The `text` parameter in click/scroll actions accepts modifier keys such as `shift`, `ctrl`, `alt`, and `super` (for the Command/Windows key).
</Accordion>

### Tool parameters

| Parameter           | Required | Description                                                                                                                         |
| ------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `type`              | Yes      | Tool version (`computer_20251124` or `computer_20250124`)                                                                           |
| `name`              | Yes      | Must be "computer"                                                                                                                  |

```

</details>

<details><summary>Context after</summary>

```

| `display_height_px` | Yes      | Display height in pixels                                                                                                            |
| `display_number`    | No       | Display number for X11 environments                                                                                                 |
| `enable_zoom`       | No       | Enable zoom action (`computer_20251124` only). Set to `true` to allow Claude to zoom into specific screen regions. Default: `false` |

<Note>
  **Important:** Your application must explicitly run the computer use tool; Claude cannot run it directly. You are responsible for implementing the screenshot capture, mouse movements, keyboard inputs, and other actions based on Claude's requests.
</Note>

### Combining with thinking

For combining computer use with thinking, see [Thinking](https://platform.claude.com/docs/en/buil
```

</details>

---

## V2D-08

- **provider**: anthropic
- **document**: Beta
- **section**: Models › List Models › Returns
- **source span**: `ver_de7f74230c8f10d30aea5d037a3bd0a5` chars 8860–8937
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does Model IDs this model accept?

**Proposed answer**: Model IDs this model accepts as `fallbacks[i].model` on the Messages API.

**Proposed atomic claims**: `Model IDs this model accepts as `fallbacks[i].model` on the Messages API.`

**Critical strings**: fallbacks[i].model

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_de7f74230c8f10d30aea5d037a3bd0a5` chars 8860–8937 · hash `95982f914e9d0e93…`

```
    Model IDs this model accepts as `fallbacks[i].model` on the Messages API.
```

<details><summary>Context before</summary>

```
ion-2025-05-22"`

    - `"extended-cache-ttl-2025-04-11"`

    - `"context-1m-2025-08-07"`

    - `"context-management-2025-06-27"`

    - `"model-context-window-exceeded-2025-08-26"`

    - `"skills-2025-10-02"`

    - `"fast-mode-2026-02-01"`

    - `"output-300k-2026-03-24"`

    - `"user-profiles-2026-03-24"`

    - `"advisor-tool-2026-03-01"`

    - `"managed-agents-2026-04-01"`

    - `"cache-diagnosis-2026-04-07"`

    - `"dreaming-2026-04-21"`

    - `"thinking-token-count-2026-05-13"`

    - `"server-side-fallback-2026-06-01"`

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


```

</details>

<details><summary>Context after</summary>

```
 An empty list means the `fallbacks` parameter is not supported for this model as primary.

  - `capabilities: BetaModelCapabilities or null`

    Model capability information.

    - `batch: BetaCapabilitySupport`

      Whether the model supports the Batch API.

      - `supported: boolean`

        Whether this capability is supported by the model.

    - `citations: BetaCapabilitySupport`

      Whether the model supports citation generation.

    - `code_execution: BetaCapabilitySupport`

      Whether the model supports code execution tools.

    - `context_management: BetaContextManagementCapability`

      Context management support and available strategies.

      - `clear_thinking_20251015: BetaCapabilitySupport or null`

        Indicates whether a capability is supported.

      - `clear_tool_uses_20250919: BetaCapabilitySupport or null`

        Indicates whether a capabilit
```

</details>

---

## V2D-09

- **provider**: openai
- **document**: Handoffs
- **section**: Handoffs › Creating a handoff
- **source span**: `ver_1c77f33b04ffffa285ea7e61c2a89653` chars 638–800
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `configuration_interaction`
- **stress types**: short_evidence_unit, identifier_vs_semantic_distractor, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens if you pass plain `Agent` instances?

**Proposed answer**: Their `handoff_description` (when set) is appended to the default tool description.

**Proposed atomic claims**: If you pass plain `Agent` instances, their [`handoff_description`][agents.agent.Agent.handoff_description] (when set) is appended to the default tool description.

**Critical strings**: Agent, handoff_description

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_1c77f33b04ffffa285ea7e61c2a89653` chars 638–800 · hash `cb68ebf63dd92026…`

```
If you pass plain `Agent` instances, their [`handoff_description`][agents.agent.Agent.handoff_description] (when set) is appended to the default tool description.
```

<details><summary>Context before</summary>

```
# Handoffs

Handoffs allow an agent to delegate tasks to another agent. This is particularly useful in scenarios where different agents specialize in distinct areas. For example, a customer support app might have agents that each specifically handle tasks like order status, refunds, FAQs, etc.

Handoffs are represented as tools to the LLM. So if there's a handoff to an agent named `Refund Agent`, the tool would be named `transfer_to_refund_agent`.

## Creating a handoff

All agents have a [`handoffs`][agents.agent.Agent.handoffs] param, which can either take an `Agent` directly, or a `Handoff` object that customizes the Handoff.


```

</details>

<details><summary>Context after</summary>

```
 Use it to hint when the model should pick that handoff without writing a full `handoff()` object.

You can create a handoff using the [`handoff()`][agents.handoffs.handoff] function provided by the Agents SDK. This function allows you to specify the agent to hand off to, along with optional overrides and input filters.

### Basic usage

Here's how you can create a simple handoff:

```python
from agents import Agent, handoff

billing_agent = Agent(name="Billing agent")
refund_agent = Agent(name="Refund agent")

# (1)!
triage_agent = Agent(name="Triage agent", handoffs=[billing_agent, handoff(refund_agent)])
```

1. You can use the agent directly (as in `billing_agent`), or you can use the `handoff()` function.

### Customizing handoffs via the `handoff()` function

The [`handoff()`][agents.handoffs.handoff] function lets you customize things.

-   `agent`: This is the agent to which thin
```

</details>

---

## V2D-10

- **provider**: openai
- **document**: Running agents
- **section**: Running agents › Runner lifecycle and configuration › Streaming › Responses WebSocket transport (optional helper) › Pattern 1: No session helper (works)
- **source span**: `ver_2c60e99cfd929a738910b893fd6f1a40` chars 3840–3995
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `configuration_interaction`
- **stress types**: short_evidence_unit, identifier_vs_semantic_distractor, lexical_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens if you call `Runner.run()` / `Runner.run_streamed()` repeatedly?

**Proposed answer**: Each run may reconnect unless you manually reuse the same `RunConfig` / provider instance.

**Proposed atomic claims**: If you call `Runner.run()` / `Runner.run_streamed()` repeatedly, each run may reconnect unless you manually reuse the same `RunConfig` / provider instance.

**Critical strings**: run_streamed, RunConfig

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_2c60e99cfd929a738910b893fd6f1a40` chars 3840–3995 · hash `8f35618b0730452d…`

```
If you call `Runner.run()` / `Runner.run_streamed()` repeatedly, each run may reconnect unless you manually reuse the same `RunConfig` / provider instance.
```

<details><summary>Context before</summary>

```
 transport, not the [Realtime API](realtime/guide.md).

For transport-selection rules and caveats around concrete model objects or custom providers, see [Models](models/index.md#responses-websocket-transport).

##### Pattern 1: No session helper (works)

Use this when you just want websocket transport and do not need the SDK to manage a shared provider/session for you.

```python
import asyncio

from agents import Agent, Runner, set_default_openai_responses_transport


async def main():
    set_default_openai_responses_transport("websocket")

    agent = Agent(name="Assistant", instructions="Be concise.")
    result = Runner.run_streamed(agent, "Summarize recursion in one sentence.")

    async for event in result.stream_events():
        if event.type == "raw_response_event":
            continue
        print(event.type)


asyncio.run(main())
```

This pattern is fine for single runs. 
```

</details>

<details><summary>Context after</summary>

```


##### Pattern 2: Use `responses_websocket_session()` (recommended for multi-turn reuse)

Use [`responses_websocket_session()`][agents.responses_websocket_session] when you want a shared websocket-capable provider and `RunConfig` across multiple runs (including nested agent-as-tool calls that inherit the same `run_config`).

```python
import asyncio

from agents import Agent, responses_websocket_session


async def main():
    agent = Agent(name="Assistant", instructions="Be concise.")

    async with responses_websocket_session(
        responses_websocket_options={"ping_interval": 20.0, "ping_timeout": 60.0},
    ) as ws:
        first = ws.run_streamed(agent, "Say hello in one short sentence.")
        async for _event in first.stream_events():
            pass

        second = ws.run_streamed(
            agent,
            "Now say goodbye.",
            previous_response_id=first
```

</details>

---

## V2D-11

- **provider**: openai
- **document**: Agents
- **section**: Agents › Basic configuration
- **source span**: `ver_35cac5e98c151a17f941a6142d74709f` chars 1910–2056
- **evidence kind**: `parameter_table_row`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, parameter_error_literal_lookup, identifier_vs_semantic_distractor
- **binding**: structural: parameter is the row's first cell, requiredness is column 1 of the same row
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> Is the `instructions` parameter required?

**Proposed answer**: No, it is optional.

**Proposed atomic claims**: ``instructions` is optional.`

**Critical strings**: instructions, no

**Generator notes**: Row-scoped association, so the state cannot belong to a different parameter. Reviewer should confirm the table is a parameter table and that the column header means what it appears to mean.

### Evidence E1 (verbatim, authoritative)

`ver_35cac5e98c151a17f941a6142d74709f` chars 1910–2056 · hash `82cea7b95770ca4b…`

```
| `instructions` | no | System prompt or dynamic instructions callback. Strongly recommended. See [Dynamic instructions](#dynamic-instructions). |
```

<details><summary>Context before</summary>

```
u need to make.

| If you want to... | Read next |
| --- | --- |
| Choose a model or provider setup | [Models](models/index.md) |
| Add capabilities to the agent | [Tools](tools.md) |
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

```

</details>

<details><summary>Context after</summary>

```

| `prompt` | no | OpenAI Responses API prompt configuration. Accepts a static prompt object or a function. See [Prompt templates](#prompt-templates). |
| `handoff_description` | no | Short description exposed when this agent is offered as a handoff target. |
| `handoffs` | no | Delegate the conversation to specialist agents. See [handoffs](handoffs.md). |
| `model` | no | Which LLM to use. See [Models](models/index.md). |
| `model_settings` | no | Model tuning parameters such as `temperature`, `top_p`, and `tool_choice`. |
| `tools` | no | Tools the agent can call. See [Tools](tools.md). |
| `mcp_servers` | no | MCP servers that provide MCP-backed tools to the agent. See the [MCP guide](mcp.md). |
| `mcp_config` | no | Fine-tune how MCP tools are prepared, such as converting their schemas to strict mode and formatting MCP failures. See the [MCP guide](mcp.md#agent-level-mcp-configuratio
```

</details>

---

## V2D-12

- **provider**: openai
- **document**: Sandbox clients
- **section**: Sandbox clients › Supported hosted platforms › Size Modal sandboxes
- **source span**: `ver_3d4b8881962381cbfba18ade50c598e1` chars 11175–11288
- **evidence kind**: `configuration_interaction`
- **evidence shape**: `single_span`
- **reasoning type**: `configuration_interaction`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor
- **binding**: structural-or-subject-window
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does `S3FilesMountPattern` require?

**Proposed answer**: `S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses ambient IAM authority.

**Proposed atomic claims**: `S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses ambient IAM authority.

**Critical strings**: S3FilesMountPattern, mount.s3files

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_3d4b8881962381cbfba18ade50c598e1` chars 11175–11288 · hash `b7cd45d15c27feea…`

```
`S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses ambient IAM authority.
```

<details><summary>Context before</summary>

```
 backend can execute. A check mark does not bypass the credential boundary for a mount helper that runs inside a model-controlled sandbox, and it does not mean that every strategy can operate without credentials. The Agents SDK accepts an in-container mount without an acknowledgement only when the selected helper can operate without protected authority. It rejects a mount that requires protected authority before starting the sandbox or mount helper unless trusted application code explicitly acknowledges the exposure for the exact mount path.

Credentialless `rclone` mounts are limited to S3, GCS, R2, and Azure Blob. An in-container Box mount requires a non-interactive authentication source and the acknowledgement that matches that source. `FuseMountPattern` requires broad acknowledgement because `blobfuse2` discovers ambient Azure authority, even when no inline credential is configured. 
```

</details>

<details><summary>Context after</summary>

```
 These requirements also apply when Docker is the backend; the check marks below indicate that Docker can execute the mount after the applicable authority boundary is satisfied.

For a mount entry named `"data"`, retain the copied `Manifest` returned by the acknowledgement that matches the configured authority:

```python
# Mount-scoped values such as inline access keys.
manifest = manifest.with_in_container_mount_credential_exposure_acknowledged("data")

# Broader authority such as managed or workload identity and external credential files.
manifest = manifest.with_in_container_mount_broad_credential_exposure_acknowledged("data")
```

Pass every exact mount path that needs the acknowledgement. A mount that uses both authority classes requires both acknowledgements. The acknowledgements are runtime-only, are not serialized, and permit the helper to receive credentials without confining c
```

</details>

---

## V2D-13

- **provider**: openai
- **document**: Models
- **section**: Models › OpenAI models › Hosted multi-agent (experimental) › Current limitations
- **source span**: `ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 19331–19456
- **evidence kind**: `configuration_interaction`
- **evidence shape**: `single_span`
- **reasoning type**: `configuration_interaction`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor
- **binding**: structural-or-subject-window
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does `betas` override?

**Proposed answer**: The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.

**Proposed atomic claims**: The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.

**Critical strings**: betas, reasoning.summary, max_tool_calls

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 19331–19456 · hash `540a39028df81849…`

```
The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.
```

<details><summary>Context before</summary>

```
ll is ready, then resumes that same provider response after the Runner produces an output. Use `get_hosted_agent_metadata()` with a raw hosted item or a `ToolContext` to identify the hosted agent to which the item or tool call is attributed.

#### Relationship to SDK orchestration

Hosted multi-agent is separate from SDK handoffs and agents-as-tools:

-   Hosted multi-agent creates subagents on the OpenAI service. Your application does not create or schedule those subagents.
-   SDK handoffs change the active local SDK `Agent`. They are rejected when this experimental model is used because every hosted agent receives the same handoff tools, which would create conflicting ownership.
-   Agents-as-tools remain available, but using them creates nested client-side and server-side orchestration. Evaluate the additional latency, cost, and tool exposure deliberately.

#### Current limitations


```

</details>

<details><summary>Context after</summary>

```
 The Responses `/compact` endpoint is not supported by the beta, although an explicit `context_management.compact_threshold` may be used because the service automatically compacts each hosted agent context independently.

One `OpenAIHostedMultiAgentModel` instance owns at most one active hosted response at a time. If a run is abandoned while waiting for local function output, call `await model.close()` to release its WebSocket. Restoring an in-flight hosted response in a different process or event loop is not currently supported.

See the [OpenAI Multi-agent guide](https://developers.openai.com/api/docs/guides/tools-multi-agent) for the underlying Responses API beta behavior. See [`examples/agent_patterns/hosted_multi_agent_beta.py`](https://github.com/openai/openai-agents-python/tree/main/examples/agent_patterns/hosted_multi_agent_beta.py) for non-streaming and streaming SDK usage.

## 
```

</details>

---

## V2D-14

- **provider**: openai
- **document**: Testing
- **section**: Testing › Agent workflow recipes › Derive a response from the request
- **source span**: `ver_d2295786320b2815477eb963eb1f5e8a` chars 6729–6866
- **evidence kind**: `error_statement`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, parameter_error_literal_lookup, identifier_vs_semantic_distractor
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does `ScriptedModel` accept?

**Proposed answer**: `ScriptedModel` accepts `ModelStep`, the equivalent dictionary form, `ModelResponse`, a normalized output-item sequence, or an exception.

**Proposed atomic claims**: `ScriptedModel` accepts `ModelStep`, the equivalent dictionary form, `ModelResponse`, a normalized output-item sequence, or an exception.

**Critical strings**: ScriptedModel, ModelStep, ModelResponse

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_d2295786320b2815477eb963eb1f5e8a` chars 6729–6866 · hash `ff6b6dac88107bfa…`

```
`ScriptedModel` accepts `ModelStep`, the equivalent dictionary form, `ModelResponse`, a normalized output-item sequence, or an exception.
```

<details><summary>Context before</summary>

```
l boundary. The responder may be synchronous or asynchronous and may return any step shape accepted by `ScriptedModel`.

```python
import pytest

from agents import Agent, RunConfig, Runner
from agents.testing import ModelCall, ModelStep, ScriptedModel, assistant_message


def respond(call: ModelCall):
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


```

</details>

<details><summary>Context after</summary>

```
 Prefer fixed output sequences when a response does not depend on the call because fixed scripts make unexpected turns easier to diagnose.

### Inspect model calls

`ScriptedModel` records each call before it resolves or raises the selected step.

| Member | Contains |
| --- | --- |
| `calls` | Every `ModelCall` in invocation order |
| `first_call` | The first call, or `None` |
| `last_call` | The most recent call, or `None` |
| `remaining_steps` | The number of configured steps not yet consumed |

Common assertions include `call.input`, `call.model_settings`, `call.tools`, `call.handoffs`, and `call.streamed`. Mutable request data is snapshotted at the invocation boundary, and each public history accessor returns detached snapshots. Tool, handoff, output-schema, and tracing objects keep their runtime identity.

Structured `call_index` and `input_index` error fields are zero-based so the
```

</details>

---

## V2D-15

- **provider**: openai
- **document**: OpenAI TypeScript and JavaScript API Library
- **section**: OpenAI TypeScript and JavaScript API Library › Amazon Bedrock
- **source span**: `ver_f30a6447e4df2ab76e4c1475f353109c` chars 17117–17323
- **evidence kind**: `configuration_interaction`
- **evidence shape**: `single_span`
- **reasoning type**: `configuration_interaction`
- **stress types**: correct_document_difficult_passage, identifier_vs_semantic_distractor, lexical_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does `AWS_BEDROCK_BASE_URL` override?

**Proposed answer**: This uses the regional `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint. The region can also come from `AWS_REGION` or `AWS_DEFAULT_REGION`, and `AWS_BEDROCK_BASE_URL` can override the endpoint.

**Proposed atomic claims**: This uses the regional `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint. The region can also come from `AWS_REGION` or `AWS_DEFAULT_REGION`, and `AWS_BEDROCK_BASE_URL` can override the endpoint.

**Critical strings**: AWS_BEDROCK_BASE_URL, AWS_REGION, AWS_DEFAULT_REGION

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_f30a6447e4df2ab76e4c1475f353109c` chars 17117–17323 · hash `ebe19ef32b204e03…`

```
This uses the regional `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint. The region can also come from `AWS_REGION` or `AWS_DEFAULT_REGION`, and `AWS_BEDROCK_BASE_URL` can override the endpoint.
```

<details><summary>Context before</summary>

```
t.choices[0]!.message?.content);
```

For more information on support for the Azure API, see [docs/azure.md](docs/azure.md).

## Amazon Bedrock

To use this library with [Amazon Bedrock's OpenAI-compatible API](https://docs.aws.amazon.com/bedrock/latest/userguide/models-api-compatibility.html), configure the standard `OpenAI` client with the Bedrock provider:

```ts
import OpenAI from 'openai';
import { bedrock } from 'openai/providers/bedrock/aws';

const client = new OpenAI({
  provider: bedrock({ region: 'us-west-2' }),
});

const response = await client.responses.create({
  model: 'openai.gpt-5.4',
  input: 'Say hello!',
});

console.log(response.output_text);
```

Use a model that [supports the Responses API](https://docs.aws.amazon.com/bedrock/latest/userguide/models-api-compatibility.html). A model returned by the Models API may support a different Bedrock inference API instead.


```

</details>

<details><summary>Context after</summary>

```


The AWS entrypoint uses the standard AWS credential chain by default. It also accepts a named profile, static credentials, or a custom credential provider. Install its peer dependencies before importing it:

```bash
npm install @aws-sdk/credential-provider-node @smithy/hash-node @smithy/signature-v4
```

The AWS entrypoint uses normal static imports so bundlers and serverless packagers can trace these dependencies. If one is missing, importing `openai/providers/bedrock/aws` fails immediately with the runtime's normal module-not-found error, for example:

```text
Cannot find module '@aws-sdk/credential-provider-node'
```

For Bedrock API key authentication, import `bedrock` from `openai/providers/bedrock` instead. That entrypoint has no AWS dependencies and works in browser-compatible runtimes when `dangerouslyAllowBrowser` is enabled. SigV4 authentication is supported in Node.js and co
```

</details>

---

## V2D-16

- **provider**: openai
- **document**: Realtime agents guide
- **section**: Realtime agents guide › Agent and session configuration › Input transcription settings
- **source span**: `ver_14a2187cf2216b9d56c213b520a28479` chars 6569–6644
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does the `delay` setting accept?

**Proposed answer**: The `delay` setting accepts `minimal`, `low`, `medium`, `high`, or `xhigh`.

**Proposed atomic claims**: `The `delay` setting accepts `minimal`, `low`, `medium`, `high`, or `xhigh`.`

**Critical strings**: delay, minimal, low

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_14a2187cf2216b9d56c213b520a28479` chars 6569–6644 · hash `710d3803ff9ad91f…`

```
The `delay` setting accepts `minimal`, `low`, `medium`, `high`, or `xhigh`.
```

<details><summary>Context before</summary>

```
            }
            }
        }
    },
)
```

For `gpt-live-transcribe`, `prompt` provides free-form recording context, `keywords` lists literal terms that may occur in the audio, and `languages` lists expected input languages. This model uses plural `languages` instead of singular `language`; do not send both fields.

The OpenAI client version pinned by this SDK supports `delay` only with `gpt-realtime-whisper`. Configure that model's latency and accuracy tradeoff as follows:

```python
runner = RealtimeRunner(
    starting_agent=agent,
    config={
        "model_settings": {
            "audio": {
                "input": {
                    "transcription": {
                        "model": "gpt-realtime-whisper",
                        "delay": "low",
                    },
                    "turn_detection": None,
                }
            }
        }
    },
)
```


```

</details>

<details><summary>Context after</summary>

```
 Lower values can produce earlier partial text, while higher values give the transcription model more audio context and can improve recognition accuracy. Benchmark representative audio instead of assuming fixed timing for any level.

Use `gpt-transcribe` in a Realtime session over WebSocket only when transcription should begin after a committed audio turn or the application needs detected-language output. The model automatically uses earlier transcribed turns as context. The `gpt-transcribe` completion event reports detected languages in its `languages` output field. This output field is different from the `gpt-live-transcribe` expected-language input shown above.

Setting `audio.input.turn_detection` to `None` disables automatic turn detection. The application must then commit audio turns and control response creation as described in [Manual response control](#manual-response-control). 
```

</details>

---

## V2D-17

- **provider**: anthropic
- **document**: Thinking
- **section**: Reading thinking output › Summarized thinking
- **source span**: `ver_012b734775e7edb2649d3a9ddfd93070` chars 19697–19845
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `configuration_interaction`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, lexical_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens when `display` is `"summarized"`?

**Proposed answer**: The thinking text you receive is a summary of Claude's full thinking process rather than the raw chain of thought.

**Proposed atomic claims**: When `display` is `"summarized"`, the thinking text you receive is a summary of Claude's full thinking process rather than the raw chain of thought.

**Critical strings**: display

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_012b734775e7edb2649d3a9ddfd93070` chars 19697–19845 · hash `8542afab39ec13b2…`

```
When `display` is `"summarized"`, the thinking text you receive is a summary of Claude's full thinking process rather than the raw chain of thought.
```

<details><summary>Context before</summary>

```
y` is invalid with `thinking.type: "disabled"` (there is nothing to display).
* When using `thinking.type: "adaptive"` and the model skips thinking for a simple request, no thinking block is produced regardless of `display`.
* When streaming with `display: "omitted"`, no `thinking_delta` events are emitted. See [Streaming thinking](https://platform.claude.com/docs/en/build-with-claude/thinking#streaming-thinking) for the event sequence.

<Note>
  The `signature` field is identical whether `display` is `"summarized"` or `"omitted"`. Switching `display` values between turns in a conversation is supported.
</Note>

In the Ruby SDK, plain hashes take `display:` as the examples show. The typed `ThinkingConfigAdaptive` class names the parameter `display_` (trailing underscore, to avoid shadowing Ruby's `Kernel#display`). Either way, the wire field is still `display`.

### Summarized thinking


```

</details>

<details><summary>Context after</summary>

```
 Summarized thinking provides the full intelligence benefits of thinking while preventing misuse. No `display` setting returns the raw chain of thought.

Keep the following in mind when working with summarized thinking:

* You're charged for the full thinking tokens generated by the original request, not the summary tokens. The billed output token count does not match the count of tokens you see in the response.
* On Claude Opus 4.6, Claude Sonnet 4.6, and earlier models, the first few lines of thinking output are more verbose, providing detailed reasoning that's particularly helpful for prompt engineering purposes. [Claude Mythos Preview](https://anthropic.com/glasswing) summarizes from the first token, so its thinking blocks do not show this verbose preamble.
* Summarization preserves the key ideas of Claude's thinking process with minimal added latency, so summaries can stream as they
```

</details>

---

## V2D-18

- **provider**: openai
- **document**: Testing
- **section**: Testing › Agent workflow recipes › Inject model failures
- **source span**: `ver_d2295786320b2815477eb963eb1f5e8a` chars 9711–9850
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, correct_document_difficult_passage
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does the Python helper accept?

**Proposed answer**: The Python helper accepts a fixed `ModelRetryAdvice` value; use a custom `Model` when retry advice itself must vary dynamically by attempt.

**Proposed atomic claims**: The Python helper accepts a fixed `ModelRetryAdvice` value; use a custom `Model` when retry advice itself must vary dynamically by attempt.

**Critical strings**: ModelRetryAdvice

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_d2295786320b2815477eb963eb1f5e8a` chars 9711–9850 · hash `98f949d187d774cf…`

```
The Python helper accepts a fixed `ModelRetryAdvice` value; use a custom `Model` when retry advice itself must vary dynamically by attempt.
```

<details><summary>Context before</summary>

```
`output` is the response returned if the same step is used in a non-streaming call. Exact stream events are SDK-normalized events, not Responses API or Chat Completions wire chunks.

Automatic streaming rejects normalized output-item kinds whose incremental lifecycle is not implemented. Use `ModelStep.stream(...)` for those items instead of relying on a partial event sequence.

### Inject model failures

Use `ModelStep.raise_error()` to fail one model call. Optional retry advice belongs to that exact scripted error:

```python
from agents import ModelRetryAdvice
from agents.testing import ModelStep


step = ModelStep.raise_error(
    RuntimeError("temporary failure"),
    retry_advice=ModelRetryAdvice(suggested=True, replay_safety="safe"),
)
```

The runner's retry policy decides whether advice causes another attempt. Each retry is another model call and consumes the next scripted step. 
```

</details>

<details><summary>Context after</summary>

```


### Detect workflow drift

Treat the scripted calls as the expected workflow shape. An extra model request raises `UnexpectedModelCall`; an early exit leaves steps for `assert_complete()` to report.

When your test framework supports teardown or finalizers, place `assert_complete()` there if you also want unconsumed steps reported after another assertion fails. Do not catch mismatch errors in a normal regression test.

| Error | Structured fields | Meaning |
| --- | --- | --- |
| `InvalidModelStep` | `reason`, `input_index` | A step is malformed and is rejected before entering the queue |
| `UnexpectedModelCall` | `call`, `call_index` | The workflow made another model call after the script ended |
| `UnconsumedModelSteps` | `remaining_steps` | The workflow ended before using every step |

## Sandbox Agent recipes

### Test a Sandbox Agent workflow

Combine `ScriptedModel` with `scripte
```

</details>

---

## V2D-19

- **provider**: anthropic
- **document**: Using Agent Skills with the API
- **section**: Managing custom Skills › Creating a Skill
- **source span**: `ver_5a15a8f543d432ef91eb6e2997f51225` chars 72650–72735
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, lexical_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does the Python SDK also provides a `files_from_dir` helper that accept?

**Proposed answer**: The Python SDK also provides a `files_from_dir` helper that accepts a directory path.

**Proposed atomic claims**: The Python SDK also provides a `files_from_dir` helper that accepts a directory path.

**Critical strings**: files_from_dir

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_5a15a8f543d432ef91eb6e2997f51225` chars 72650–72735 · hash `dcf16d18e94cb433…`

```
The Python SDK also provides a `files_from_dir` helper that accepts a directory path.
```

<details><summary>Context before</summary>

```
m",
          skill_id: "skill_01AbCdEfGhIjKlMnOpQrStUv",
          version: "latest"
        }
      ]
    },
    messages: [
      { role: "user", content: "Analyze sales data and create a presentation" }
    ],
    tools: [
      { type: "code_execution_20250825", name: "code_execution" }
    ]
  )
  puts message
  ```
</CodeGroup>

***

## Managing custom Skills

### Creating a Skill

A Skill bundle is a directory containing a `SKILL.md` file at the top level with `name` and `description` YAML frontmatter, plus any supporting scripts or resources. See [Get started with Agent Skills in the API](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/quickstart) to author one, and the **Requirements** list following the examples for the full constraints.

Upload your custom Skill to make it available in your workspace. You can upload a zip archive or individual file objects. 
```

</details>

<details><summary>Context after</summary>

```


Files are identified by the filename you attach. Per-file uploads must keep a common top-level directory in their paths (the `;filename=` suffix in the cURL example and the filename arguments in the SDK examples). A zip archive must contain the skill directory as its single top-level entry. For the walkthrough's skill, create one with `zip -r financial_skill.zip financial_skill/` and substitute it for the `example_skill.zip` placeholder in the zip-upload options.

<CodeGroup defaultLanguage="CLI">
  ```bash cURL
  curl -X POST "https://api.anthropic.com/v1/skills" \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "anthropic-beta: skills-2025-10-02" \
    -F "files[]=@financial_skill/SKILL.md;filename=financial_skill/SKILL.md" \
    -F "files[]=@financial_skill/analyze.py;filename=financial_skill/analyze.py"
  ```

  ```bash CLI
  ant beta:skills
```

</details>

---

## V2D-20

- **provider**: anthropic
- **document**: Claude Platform on AWS
- **section**: Data residency
- **source span**: `ver_5ebdc722f9bedb1e2e8cbd3f29ff6805` chars 47753–47880
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `configuration_interaction`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, lexical_query_shape, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens if you omit `inference_geo`?

**Proposed answer**: The request uses the workspace's `default_inference_geo` if one is configured, otherwise `global`.

**Proposed atomic claims**: If you omit `inference_geo`, the request uses the workspace's `default_inference_geo` if one is configured, otherwise `global`.

**Critical strings**: inference_geo, default_inference_geo, global

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_5ebdc722f9bedb1e2e8cbd3f29ff6805` chars 47753–47880 · hash `44d2362efd094347…`

```
If you omit `inference_geo`, the request uses the workspace's `default_inference_geo` if one is configured, otherwise `global`.
```

<details><summary>Context before</summary>

```
mEnv())
          .build();

      Message message = client.messages().create(
          MessageCreateParams.builder()
              .model(Model.CLAUDE_SONNET_5)
              .maxTokens(1024)
              .inferenceGeo("us")
              .addUserMessage("Hello!")
              .build()
      );

      IO.println(message);
  }
  ```

  ```php PHP
  use Anthropic\Aws\Client;

  $client = new Client();

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
    messages: [{ role: "user", content: "Hello!" }]
  )

  puts message
  ```
</CodeGroup>


```

</details>

<details><summary>Context after</summary>

```


Workspace-level inference geography controls (`allowed_inference_geos` and `default_inference_geo`) are also available on Claude Platform on AWS. See [Workspace-level restrictions](https://platform.claude.com/docs/en/manage-claude/data-residency#workspace-level-restrictions).

## Workspaces

Inference and resource requests on Claude Platform on AWS target a workspace. You pass the workspace's ID in the `anthropic-workspace-id` header on these API calls. Workspace IDs use the tagged format `wrkspc_` followed by an alphanumeric identifier (for example, `wrkspc_01AbCdEf23GhIj`). See [Obtain your workspace ID](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws#obtain-your-workspace-id) if you don't have it yet.

### Workspace scoping

Workspaces are bound to a single AWS region. A workspace created in `us-west-2` can only be accessed through the `us-west-2` endpoi
```

</details>

---

## V2D-21

- **provider**: anthropic
- **document**: Memory tool
- **section**: Security considerations › File storage size
- **source span**: `ver_96d1698a3864f79451e8576f87a07004` chars 34903–35023
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `error_behavior`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, version_model_discrimination, identifier_vs_semantic_distractor
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does Consider capping how many characters the `view` command return?

**Proposed answer**: Consider capping how many characters the `view` command returns, and let Claude page through the rest with `view_range`.

**Proposed atomic claims**: Consider capping how many characters the `view` command returns, and let Claude page through the rest with `view_range`.

**Critical strings**: view, view_range

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_96d1698a3864f79451e8576f87a07004` chars 34903–35023 · hash `829b4270435161f7…`

```
Consider capping how many characters the `view` command returns, and let Claude page through the rest with `view_range`.
```

<details><summary>Context before</summary>

```
to repeat that instruction. If Claude still creates cluttered memory files, you can reinforce it in your prompt:

```text wrap
Note: when editing your memory folder, always try to keep its content up-to-date, coherent and organized. You can rename or delete files that are no longer relevant. Do not create new files unless necessary.
```

You can also guide what Claude writes to memory. For example: "Only write down information relevant to \<topic> in your memory system."

## Security considerations

Your application executes every file operation Claude requests, so these safeguards are your responsibility:

### Sensitive information

Claude usually refuses to write sensitive information to memory files. For stronger guarantees, add validation that strips sensitive data before your handler writes the file.

### File storage size

Track memory file sizes and cap how large a file can grow. 
```

</details>

<details><summary>Context after</summary>

```


### Memory expiration

Periodically delete memory files that haven't been accessed in a long time.

### Path traversal protection

<Warning>
  A malicious path such as `/memories/../../secrets.env` can reach files outside the `/memories` directory. Your implementation must validate every path in every command to prevent directory traversal attacks.
</Warning>

Consider these safeguards:

* Validate that all paths start with `/memories`
* Resolve paths to their canonical form and verify they remain within the memory directory
* Reject paths containing sequences such as `../`, `..\\`, or other traversal patterns
* Watch for URL-encoded traversal sequences (`%2e%2e%2f`)
* Use your language's built-in path security utilities (for example, Python's `pathlib.Path.resolve()` and `relative_to()`)

## Error handling

The memory tool uses similar error-handling patterns to the [text editor tool]
```

</details>

---

## V2D-22

- **provider**: anthropic
- **document**: Tool runner (SDK)
- **section**: Advanced usage › Taking over message history
- **source span**: `ver_96d5aba3c4e7771cabd4f3d4f5a3fff1` chars 38316–38425
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `error_behavior`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, lexical_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does By the time `next_message` return?

**Proposed answer**: By the time `next_message` returns, the assistant message and tool result for that turn are already appended.

**Proposed atomic claims**: By the time `next_message` returns, the assistant message and tool result for that turn are already appended.

**Critical strings**: next_message

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_96d5aba3c4e7771cabd4f3d4f5a3fff1` chars 38316–38425 · hash `cc4be65021e4ea3f…`

```
By the time `next_message` returns, the assistant message and tool result for that turn are already appended.
```

<details><summary>Context before</summary>

```
 === BetaStopReason::MAX_TOKENS->value) {
            $current = $runner->getParams()['maxTokens'];

            if ($current >= $maxTokenCeiling) {
                echo "Hit ceiling ({$maxTokenCeiling}), accepting truncated response.\n";
                break;
            }

            $doubled = min($current * 2, $maxTokenCeiling);
            echo "Response truncated at {$current} tokens, retrying with {$doubled}.\n";

            // Calling setMessagesParams() inside the loop tells the runner to skip
            // its automatic append. The truncated message is discarded; the next
            // iteration retries with the larger budget.
            // Keys are camelCase, matching the toolRunner() named parameters.
            $runner->setMessagesParams(['maxTokens' => $doubled]);
        }
    }
    ```
  </Tab>

  <Tab title="Ruby">
    Use `next_message` for step-by-step control. 
```

</details>

<details><summary>Context after</summary>

```
 Use `feed_messages` to inject follow-up messages between turns, and `runner.params.update(...)` to change request parameters in place.

    You take over message history when, from inside an `each_message` or `each_streaming` block, you reassign `runner.params[:messages]` or call `feed_messages`. The following pattern calls `feed_messages` between `next_message` calls, which does not take over.

    ```ruby
    runner = client.beta.messages.tool_runner(
      model: "claude-opus-5",
      max_tokens: 1024,
      max_iterations: 10,
      tools: [GetWeather.new],
      messages: [{role: "user", content: "What's the weather in San Francisco?"}]
    )

    # Step the runner once. The assistant message and tool result are appended
    # to runner.params[:messages] before next_message returns.
    message = runner.next_message
    puts message.content

    # Inject a follow-up before continu
```

</details>

---

## V2D-23

- **provider**: openai
- **document**: Sandbox clients
- **section**: Sandbox clients › Supported hosted platforms › Size Modal sandboxes
- **source span**: `ver_3d4b8881962381cbfba18ade50c598e1` chars 10824–11465
- **evidence kind**: `long_technical_section`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: long_technical_section, correct_document_difficult_passage, identifier_vs_semantic_distractor
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What is Credentialless `rclone` mounts limited to?

**Proposed answer**: Credentialless `rclone` mounts are limited to S3, GCS, R2, and Azure Blob.

**Proposed atomic claims**: `Credentialless `rclone` mounts are limited to S3, GCS, R2, and Azure Blob.`

**Critical strings**: rclone, FuseMountPattern, blobfuse2

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_3d4b8881962381cbfba18ade50c598e1` chars 10824–11465 · hash `b970148442409480…`

```
Credentialless `rclone` mounts are limited to S3, GCS, R2, and Azure Blob. An in-container Box mount requires a non-interactive authentication source and the acknowledgement that matches that source. `FuseMountPattern` requires broad acknowledgement because `blobfuse2` discovers ambient Azure authority, even when no inline credential is configured. `S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses ambient IAM authority. These requirements also apply when Docker is the backend; the check marks below indicate that Docker can execute the mount after the applicable authority boundary is satisfied.
```

<details><summary>Context before</summary>

```
BlobMount`, and `BoxMount`. |
| `VercelSandboxClient` | Supports create-time-only S3 and S3-compatible bucket mounts by pairing `VercelCloudBucketMountStrategy` with an `S3Mount` entry; mounted sessions cannot be resumed, and inline credentials require `allow_s3_credential_exposure=True`. |

</div>

The mount tables describe which storage types each backend can execute. A check mark does not bypass the credential boundary for a mount helper that runs inside a model-controlled sandbox, and it does not mean that every strategy can operate without credentials. The Agents SDK accepts an in-container mount without an acknowledgement only when the selected helper can operate without protected authority. It rejects a mount that requires protected authority before starting the sandbox or mount helper unless trusted application code explicitly acknowledges the exposure for the exact mount path.


```

</details>

<details><summary>Context after</summary>

```


For a mount entry named `"data"`, retain the copied `Manifest` returned by the acknowledgement that matches the configured authority:

```python
# Mount-scoped values such as inline access keys.
manifest = manifest.with_in_container_mount_credential_exposure_acknowledged("data")

# Broader authority such as managed or workload identity and external credential files.
manifest = manifest.with_in_container_mount_broad_credential_exposure_acknowledged("data")
```

Pass every exact mount path that needs the acknowledgement. A mount that uses both authority classes requires both acknowledgements. The acknowledgements are runtime-only, are not serialized, and permit the helper to receive credentials without confining credential use to the mounted path. Prefer an external or provider-native strategy when available, and otherwise use sandbox-scoped, short-lived, least-privilege credentials.

`V
```

</details>

---

## V2D-24

- **provider**: anthropic
- **document**: Migration guide
- **section**: Opus migration › What changed
- **source span**: `ver_a7bda3595f2c124605c3228464d4ee52` chars 54954–55610
- **evidence kind**: `long_technical_section`
- **evidence shape**: `single_span`
- **reasoning type**: `error_behavior`
- **stress types**: long_technical_section, correct_document_difficult_passage, version_model_discrimination, parameter_error_literal_lookup, same_document_passage_discrimination
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does Claude Opus 4.7 reject?

**Proposed answer**: Claude Opus 4.7 rejects `role: "system"` in `messages` with a 400 error.

**Proposed atomic claims**: `Claude Opus 4.7 rejects `role: "system"` in `messages` with a 400 error.`

**Critical strings**: messages, system

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_a7bda3595f2c124605c3228464d4ee52` chars 54954–55610 · hash `47f0ae4b3a03eda2…`

```
5. **Mid-conversation system messages:** Claude Opus 5 accepts `role: "system"` messages immediately after a user turn in the `messages` array (subject to [placement rules](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages#limitations)). Use the top-level `system` field for instructions that apply from the start. Claude Opus 4.7 rejects `role: "system"` in `messages` with a 400 error. If you maintain code paths that rebuild the full message history to update instructions, you can simplify them and preserve [prompt cache](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) hits on earlier turns.
```

<details><summary>Context before</summary>

```
ll set of effort levels (`low`, `medium`, `high`, `xhigh`, `max`). Run a fresh effort sweep on your own evals rather than carrying over a setting tuned for Claude Opus 4.7. `low` and `medium` effort are worth testing as cost and latency controls, and test `max` effort where maximum capability matters more than token spend. If you run at `xhigh` or `max` effort, set a large `max_tokens` so the model has room to think and act; start at 64k tokens and tune from there. See [Effort](https://platform.claude.com/docs/en/build-with-claude/effort).

4. **1M context window is the default:** Claude Opus 5 serves the full 1M token [context window](https://platform.claude.com/docs/en/build-with-claude/context-windows) by default with no beta header and no long-context premium. If your client passes a context-window beta header for compatibility with older models, you can remove it on Claude Opus 5.


```

</details>

<details><summary>Context after</summary>

```


6. **Refusal stop details:** The `stop_details` object on refusal responses (available since Claude Opus 4.7) is now publicly documented. When the model declines a request, it identifies the category of refusal, in addition to the existing `refusal` stop reason. No beta header is required, and there is no opt-out. See [Handling stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons).

7. **Lower prompt caching minimum:** The minimum cacheable prompt length on Claude Opus 5 is 512 tokens, lower than on Claude Opus 4.7. Prompts that were too short to cache on Claude Opus 4.7 can now create cache entries, with no code changes required. See [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#cache-limitations) for per-model minimums.

8. **Fast mode:** Claude Opus 5 supports [fast mode](https://platform.claude.com/docs/en
```

</details>

---

## V2D-25

- **provider**: anthropic
- **document**: Admin
- **section**: Service Accounts › Create Service Account
- **source span**: `ver_c299b58fe1f5a4d3a081b550334a7df6` chars 441490–442046
- **evidence kind**: `long_technical_section`
- **evidence shape**: `single_span`
- **reasoning type**: `configuration_interaction`
- **stress types**: long_technical_section, correct_document_difficult_passage, identifier_vs_semantic_distractor
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does Creating an `admin`-role service account require?

**Proposed answer**: Creating an `admin`-role service account requires an interactive credential (a user OAuth token or a Console session) — a workload may only create `developer`-role service accounts.

**Proposed atomic claims**: Creating an `admin`-role service account requires an interactive credential (a user OAuth token or a Console session) — a workload may only create `developer`-role service accounts.

**Critical strings**: organization_role, developer, admin

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_c299b58fe1f5a4d3a081b550334a7df6` chars 441490–442046 · hash `81389e37ebfd6524…`

```
A service account is a named workload identity that federation rules
target. `organization_role` is `developer` (default) or `admin`; a rule
may only be created or retargeted to grant `org:admin` scope when the
target's `organization_role` is `admin`. Requires an OAuth bearer (user
or WIF-minted service account token) or a Console session; Admin API
keys are not accepted. Creating an `admin`-role service account requires
an interactive credential (a user OAuth token or a Console session) — a
workload may only create `developer`-role service accounts.
```

<details><summary>Context before</summary>

```
`"skills"`

      - `"token_count"`

      - `"web_search"`

    - `limits: array of object { type, value }`

      The limiter values that apply to this group.

      - `type: string`

        The limiter type (for example, `requests_per_minute` or `input_tokens_per_minute`).

      - `value: number`

        The configured limit value for this limiter type.

    - `models: array of string or null`

      Model names this entry's limits apply to, including aliases. `null` when `group_type` is not `"model_group"`.

    - `type: "rate_limit"`

      Object type. Always `rate_limit` for organization rate-limit entries.

      - `"rate_limit"`

  - `next_page: string or null`

    Token to provide in as `page` in the subsequent request to retrieve the next page of data.

# Service Accounts

## Create Service Account

**post** `/v1/organizations/service_accounts`

Create a service account.


```

</details>

<details><summary>Context after</summary>

```


### Header Parameters

- `"anthropic-beta": optional array of string`

  Optional header to specify the beta version(s) you want to use.

  To use multiple betas, use a comma separated list like `beta1,beta2` or specify the header multiple times for each beta.

### Body Parameters

- `name: string`

  Slug identifier (lowercase, digits, hyphens). Unique within the organization; a duplicate name returns 409.

- `description: optional string or null`

  Optional free-text description.

- `organization_role: optional "admin" or "developer"`

  Org-level role. Defaults to `developer`.

  - `"admin"`

  - `"developer"`

### Returns

- `ServiceAccount object { id, archived_at, archived_by_actor_id, 8 more }`

  Named non-human identity within the caller's organization.

  A service account is a pure identity: name + org. Authorization lives on
  whatever references it (federation rules).

  
```

</details>

---

## V2D-26

- **provider**: anthropic
- **document**: Code execution tool
- **section**: Model compatibility
- **source span**: `ver_f65938c74d40ac1e288f169d3d0435b7` chars 3697–4899
- **evidence kind**: `long_technical_section`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: long_technical_section, version_model_discrimination, parameter_error_literal_lookup
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does Claude Haiku 4.5 accept?

**Proposed answer**: Claude Haiku 4.5 accepts the `code_execution_20260120` and `code_execution_20260521` tool types, but programmatic tool calling and the REPL state persistence that depends on it aren't available on it, so the newer versions behave like `code_execution_20250825` there.

**Proposed atomic claims**: Claude Haiku 4.5 accepts the `code_execution_20260120` and `code_execution_20260521` tool types, but programmatic tool calling and the REPL state persistence that depends on it aren't available on it, so the newer versions behave like `code_execution_20250825` there.

**Critical strings**: code_execution_20250825, code_execution_20260120, code_execution_20260521

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_f65938c74d40ac1e288f169d3d0435b7` chars 3697–4899 · hash `9cea4902ecd5c887…`

```
* `code_execution_20250825` supports Bash commands and file operations.
* `code_execution_20260120` adds REPL state persistence and [programmatic tool calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling) from within the sandbox. Claude Haiku 4.5 accepts the `code_execution_20260120` and `code_execution_20260521` tool types, but programmatic tool calling and the REPL state persistence that depends on it aren't available on it, so the newer versions behave like `code_execution_20250825` there.
* `code_execution_20260521` is the same runtime as `code_execution_20260120`. The difference is that the tool description tells Claude about the 90-second wall-clock limit on each Python cell in programmatic tool calling, so Claude can budget long-running cells. A cell that exceeds the limit returns a normal code execution result with a non-zero `return_code` and a `detection_timeout` status message in its output. This is separate from the `execution_time_exceeded` [error code](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool#errors), which the API returns when a whole tool invocation exceeds the maximum execution time.
```

<details><summary>Context before</summary>

```
code_execution_20260120`, `code_execution_20260521` |
| Claude Opus 4.7 (claude-opus-4-7)              | `code_execution_20250825`, `code_execution_20260120`, `code_execution_20260521` |
| Claude Opus 4.6 (claude-opus-4-6)              | `code_execution_20250825`, `code_execution_20260120`, `code_execution_20260521` |
| Claude Sonnet 4.6 (claude-sonnet-4-6)          | `code_execution_20250825`, `code_execution_20260120`, `code_execution_20260521` |
| Claude Opus 4.5 (claude-opus-4-5-20251101)     | `code_execution_20250825`, `code_execution_20260120`, `code_execution_20260521` |
| Claude Sonnet 4.5 (claude-sonnet-4-5-20250929) | `code_execution_20250825`, `code_execution_20260120`, `code_execution_20260521` |
| Claude Haiku 4.5 (claude-haiku-4-5-20251001)   | `code_execution_20250825`, `code_execution_20260120`, `code_execution_20260521` |

Each tool version builds on the previous one:


```

</details>

<details><summary>Context after</summary>

```


All three tool versions are generally available and don't require an `anthropic-beta` header. The legacy code execution beta headers remain valid opt-ins.

The examples on this page use `code_execution_20250825`, which covers the Bash and file operations they demonstrate and behaves the same way on every model in the table; use `code_execution_20260120` or later when you need programmatic tool calling or REPL state persistence. The current [web search](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool) and [web fetch](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool) tools (`web_search_20260209`, `web_fetch_20260209`, and later) require `code_execution_20260120` or later as their code execution version.

<Note>
  If you're still using the legacy `code_execution_20250522` (Python only), see [Upgrade to latest tool version](https://
```

</details>

---

## V2D-27

- **provider**: openai
- **document**: Handoffs
- **section**: (1)! › Customizing handoffs via the `handoff()` function
- **source span**: `ver_1c77f33b04ffffa285ea7e61c2a89653` chars 2733–2924
- **evidence kind**: `definition_bullet`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: parameter_error_literal_lookup, identifier_vs_semantic_distractor, lexical_query_shape
- **binding**: template-captured-groups
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What is the `nest_handoff_history` option?

**Proposed answer**: Optional per-handoff override for the RunConfig-level `nest_handoff_history` setting. If `None`, the value defined in the active run configuration is used instead.

**Proposed atomic claims**: `nest_handoff_history`: Optional per-handoff override for the RunConfig-level `nest_handoff_history` setting. If `None`, the value defined in the active run configuration is used instead.

**Critical strings**: nest_handoff_history, Optional per-handoff override for the RunConfig-level `nest

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_1c77f33b04ffffa285ea7e61c2a89653` chars 2733–2924 · hash `dc3876a7a33fdb1b…`

```
-   `nest_handoff_history`: Optional per-handoff override for the RunConfig-level `nest_handoff_history` setting. If `None`, the value defined in the active run configuration is used instead.
```

<details><summary>Context before</summary>

```
ransfer_to_<agent_name>`. You can override this.
-   `tool_description_override`: Override the default tool description from `Handoff.default_tool_description()`
-   `on_handoff`: A callback function executed when the handoff is invoked. This is useful for things like kicking off some data fetching as soon as you know a handoff is being invoked. This function receives the agent context, and can optionally also receive LLM generated input. The input data is controlled by the `input_type` param.
-   `input_type`: The schema for the handoff tool-call arguments. When set, the parsed payload is passed to `on_handoff`.
-   `input_filter`: This lets you filter the input received by the next agent. See below for more.
-   `is_enabled`: Whether the handoff is enabled. This can be a boolean or a function that returns a boolean, allowing you to dynamically enable or disable the handoff at runtime.

```

</details>

<details><summary>Context after</summary>

```


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

In certain situations, you want the LLM to provide some data when it calls a handoff. For example, imagine a handoff to an "Escalation agent". You might want the model
```

</details>

---

## V2D-28

- **provider**: anthropic
- **document**: MCP connector
- **section**: MCP server configuration › Field descriptions
- **source span**: `ver_279d37a3a0cc4e8a9209e01f16f9df88` chars 12037–12395
- **evidence kind**: `parameter_table_row`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: parameter_error_literal_lookup, identifier_vs_semantic_distractor, lexical_query_shape
- **binding**: structural: parameter is the row's first cell, requiredness is column 2 of the same row
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> Is the `authorization_token` parameter required?

**Proposed answer**: No, it is optional.

**Proposed atomic claims**: ``authorization_token` is optional.`

**Critical strings**: authorization_token, No

**Generator notes**: Row-scoped association, so the state cannot belong to a different parameter. Reviewer should confirm the table is a parameter table and that the column header means what it appears to mean.

### Evidence E1 (verbatim, authoritative)

`ver_279d37a3a0cc4e8a9209e01f16f9df88` chars 12037–12395 · hash `f9e6a94fee46649f…`

```
| `authorization_token` | string | No       | OAuth authorization token if required by the MCP server. See [Authentication](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector#authentication) for how to obtain one, or the [MCP specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) for protocol details. |
```

<details><summary>Context before</summary>

```
                                                                                                                                                                                    |
| `url`                 | string | Yes      | The URL of the MCP server. Must start with https\://.                                                                                                                                                                                                                                                                  |
| `name`                | string | Yes      | A unique identifier for this MCP server. Must be referenced by exactly one MCPToolset in the `tools` array.                                                                                                                                                                                                            |

```

</details>

<details><summary>Context after</summary>

```


## MCP toolset configuration

The MCPToolset lives in the `tools` array and configures which tools from the MCP server are enabled and how they should be configured.

### Basic structure

```json
{
  "type": "mcp_toolset",
  "mcp_server_name": "example-mcp",
  "default_config": {
    "enabled": true,
    "defer_loading": false
  },
  "configs": {
    "specific_tool_name": {
      "enabled": true,
      "defer_loading": true
    }
  }
}
```

### Field descriptions

| Property          | Type   | Required | Description                                                                                                                             |
| ----------------- | ------ | -------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `type`            | string | Yes      | Must be "mcp\_toolset".    
```

</details>

---

## V2D-29

- **provider**: anthropic
- **document**: Migration guide
- **section**: Sonnet migration › Migrating to Claude Sonnet 5 from Claude Sonnet 4.5 and earlier Sonnet models › Breaking changes › When migrating from Sonnet 4.5
- **source span**: `ver_a7bda3595f2c124605c3228464d4ee52` chars 145238–145433
- **evidence kind**: `lifecycle_statement`
- **evidence shape**: `single_span`
- **reasoning type**: `lifecycle_compatibility_migration`
- **stress types**: correct_document_difficult_passage, version_model_discrimination, parameter_error_literal_lookup, identifier_vs_semantic_distractor, lexical_query_shape, same_document_passage_discrimination
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> Is `budget_tokens` supported on Claude Sonnet 5?

**Proposed answer**: **Extended thinking changes:** `budget_tokens` configurations from Claude Sonnet 4.5 (`thinking: {type: "enabled", budget_tokens: N}`) are not supported on Claude Sonnet 5 and return a 400 error.

**Proposed atomic claims**: **Extended thinking changes:** `budget_tokens` configurations from Claude Sonnet 4.5 (`thinking: {type: "enabled", budget_tokens: N}`) are not supported on Claude Sonnet 5 and return a 400 error.

**Critical strings**: budget_tokens

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_a7bda3595f2c124605c3228464d4ee52` chars 145238–145433 · hash `de9ec2b850012612…`

```
**Extended thinking changes:** `budget_tokens` configurations from Claude Sonnet 4.5 (`thinking: {type: "enabled", budget_tokens: N}`) are not supported on Claude Sonnet 5 and return a 400 error.
```

<details><summary>Context before</summary>

```
', 'Based on...', etc."

   * **Avoiding bad refusals:** Claude is much better at appropriate refusals now. Clear prompting in the user message without prefill should be sufficient.

   * **Continuations** (resuming interrupted responses): Move the continuation to the user message: "Your previous response was interrupted and ended with `[previous_response]`. Continue from where you left off."

   * **Context hydration / role consistency** (refreshing context in long conversations): Inject what were previously prefilled-assistant reminders into the user turn instead.

2. **Tool parameter JSON escaping may differ**

   <Warning>
     This is a breaking change when migrating from Sonnet 4.5 or earlier.
   </Warning>

   JSON string escaping in tool parameters may differ from previous models. Standard JSON parsers handle this automatically, but custom string-based parsing may need updates.


```

</details>

<details><summary>Context after</summary>

```
 Adaptive thinking is on by default, so most workloads need no `thinking` configuration at all; use the [effort parameter](https://platform.claude.com/docs/en/build-with-claude/effort) to control thinking depth. If you ran Claude Sonnet 4.5 without extended thinking, pass `thinking: {type: "disabled"}` to preserve that behavior.

##### When migrating from Claude 3.x

3. **Remove sampling parameters**

   <Warning>
     This is a breaking change when migrating from Claude 3.x models.
   </Warning>

   Sampling parameters (`temperature`, `top_p`, `top_k`) set to a non-default value return a 400 error on Claude Sonnet 5. Remove them from requests, and use prompting to guide the model's behavior instead.

4. **Update tool versions**

   <Warning>
     This is a breaking change when migrating from Claude 3.x models.
   </Warning>

   Update to the latest tool versions (`text_editor_20250728`,
```

</details>

---

## V2D-30

- **provider**: anthropic
- **document**: Structured outputs
- **section**: JSON outputs › Working with JSON outputs in SDKs › SDK-specific methods
- **source span**: `ver_0865c9612dfe97d8f30dd870dd12e53e` chars 29387–29591
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: correct_document_difficult_passage
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does the C# SDK accept?

**Proposed answer**: The C# SDK accepts raw JSON schemas built programmatically with `JsonSerializer.SerializeToElement`, as shown here, or derives the schema from a plain C# class with the generic `Create<T>()` overload.

**Proposed atomic claims**: The C# SDK accepts raw JSON schemas built programmatically with `JsonSerializer.SerializeToElement`, as shown here, or derives the schema from a plain C# class with the generic `Create<T>()` overload.

**Critical strings**: JsonSerializer.SerializeToElement

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_0865c9612dfe97d8f30dd870dd12e53e` chars 29387–29591 · hash `ae1c3cc2f4fbd61f…`

```
    The C# SDK accepts raw JSON schemas built programmatically with `JsonSerializer.SerializeToElement`, as shown here, or derives the schema from a plain C# class with the generic `Create<T>()` overload.
```

<details><summary>Context before</summary>

```
nse.parsed_output is typed as { name: string; email: string; planInterest: string } | null
    console.log(response.parsed_output!.email);
    ```

    **Type inference requires `as const`.** Use a literal object expression with a `const` assertion so TypeScript can narrow the property types. Without `as const`, the inferred type collapses to `unknown`.

    **Schema transformation.** By default, the helper transforms the schema the same way `zodOutputFormat()` does: removing unsupported constraints, adding `additionalProperties: false` to objects, and filtering string formats. Pass `jsonSchemaOutputFormat(schema, { transform: false })` to send your schema to the API unchanged. See [How SDK transformation works](https://platform.claude.com/docs/en/build-with-claude/structured-outputs#how-sdk-transformation-works).
  </Tab>

  <Tab title="C#">
    **JSON schemas through `OutputConfig`**


```

</details>

<details><summary>Context after</summary>

```
 Deserialize the response JSON with `JsonSerializer.Deserialize`.

    ```csharp
    using System.Text.Json;
    using Anthropic;
    using Anthropic.Models.Messages;

    var client = new AnthropicClient();

    var response = await client.Messages.Create(new MessageCreateParams
    {
        Model = Model.ClaudeOpus5,
        MaxTokens = 1024,
        Messages = [new() {
            Role = Role.User,
            Content = "Extract the key information from this email: John Smith (john@example.com) is interested in our Enterprise plan."
        }],
        OutputConfig = new OutputConfig
        {
            Format = new JsonOutputFormat
            {
                Schema = new Dictionary<string, JsonElement>
                {
                    ["type"] = JsonSerializer.SerializeToElement("object"),
                    ["properties"] = JsonSerializer.SerializeToElement(new
         
```

</details>

---

## V2D-31

- **provider**: openai
- **document**: Agent memory
- **section**: Agent memory › Generate memory
- **source span**: `ver_20a999d310bdb42a2eaa743e061ba109` chars 6111–6278
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, lexical_query_shape, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens if recent raw memories exceed `max_raw_memories_for_consolidation` (defaults to 256)?

**Proposed answer**: Phase 2 keeps only memories from the newest conversations and removes older ones.

**Proposed atomic claims**: If recent raw memories exceed `max_raw_memories_for_consolidation` (defaults to 256), Phase 2 keeps only memories from the newest conversations and removes older ones.

**Critical strings**: max_raw_memories_for_consolidation

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_20a999d310bdb42a2eaa743e061ba109` chars 6111–6278 · hash `0b2654299175c579…`

```
If recent raw memories exceed `max_raw_memories_for_consolidation` (defaults to 256), Phase 2 keeps only memories from the newest conversations and removes older ones.
```

<details><summary>Context before</summary>

```
pace layout is:

```text
workspace/
├── sessions/
│   └── <rollout-id>.jsonl
└── memories/
    ├── memory_summary.md
    ├── MEMORY.md
    ├── raw_memories.md (intermediate)
    ├── phase_two_selection.json (intermediate)
    ├── raw_memories/ (intermediate)
    │   └── <rollout-id>.md
    ├── rollout_summaries/
    │   └── <rollout-id>_<slug>.md
    └── skills/
```

You can configure memory generation with `MemoryGenerateConfig`:

```python
from agents.sandbox import MemoryGenerateConfig
from agents.sandbox.capabilities import Memory

memory = Memory(
    generate=MemoryGenerateConfig(
        max_raw_memories_for_consolidation=128,
        extra_prompt="Pay extra attention to what made the customer more satisfied or annoyed",
    ),
)
```

Use `extra_prompt` to tell the memory generator which signals matter most for your use case, such as customer and company details for a GTM agent.


```

</details>

<details><summary>Context after</summary>

```
 Recency is based on the last time the conversation is updated. This forgetting mechanism helps memories reflect the newest environment.

## Multi-turn conversations

For multi-turn sandbox chats, use the normal SDK `Session` together with the same live sandbox session:

```python
from agents import Runner, SQLiteSession
from agents.run import RunConfig
from agents.sandbox import SandboxRunConfig

conversation_session = SQLiteSession("gtm-q2-pipeline-review")
sandbox = await client.create(manifest=agent.default_manifest)

async with sandbox:
    run_config = RunConfig(
        sandbox=SandboxRunConfig(session=sandbox),
        workflow_name="GTM memory example",
    )
    await Runner.run(
        agent,
        "Analyze data/leads.csv and identify one promising GTM segment.",
        session=conversation_session,
        run_config=run_config,
    )
    await Runner.run(
        agent,

```

</details>

---

## V2D-32

- **provider**: anthropic
- **document**: MCP tunnels quickstart
- **section**: What you need
- **source span**: `ver_067b3bfdc28f24500ea19b97bf3e80b1` chars 1857–1989
- **evidence kind**: `constraint_statement`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, parameter_error_literal_lookup, identifier_vs_semantic_distractor
- **binding**: structural-or-subject-window
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What must `openssl` be?

**Proposed answer**: Preinstalled on macOS and most Linux distributions; on Windows, install it separately (the `openssl` binary must be on your `PATH`).

**Proposed atomic claims**: Preinstalled on macOS and most Linux distributions; on Windows, install it separately (the `openssl` binary must be on your `PATH`).

**Critical strings**: openssl, PATH

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_067b3bfdc28f24500ea19b97bf3e80b1` chars 1857–1989 · hash `a73bb959f95532e9…`

```
Preinstalled on macOS and most Linux distributions; on Windows, install it separately (the `openssl` binary must be on your `PATH`).
```

<details><summary>Context before</summary>

```
m.claude.com/docs/en/agents-and-tools/mcp-tunnels/concepts#components) (the [proxy](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/concepts#components) and [cloudflared](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/concepts#components)) plus a sample MCP server running alongside it. When everything is running, the sample server is reachable from Claude at `https://echo.<your-tunnel-domain>/mcp` even though nothing is listening on a public port.

## What you need

* [Docker and Docker Compose](https://docs.docker.com/get-docker/) on a machine with outbound internet access.
* A role in the [Claude Console](https://platform.claude.com) that can manage MCP tunnels. See the [Console guide prerequisites](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/console#prerequisites).
* [OpenSSL](https://openssl-library.org/source/) 1.1.1 or later. 
```

</details>

<details><summary>Context after</summary>

```


<Steps>
  <Step title="Create a tunnel">
    In the Claude Console sidebar, go to **Manage > MCP tunnels** and click **New tunnel**. Give it a name. Leave **Set up programmatic access** off; this quickstart uses manual credential provisioning.

    After it's created, open the tunnel. Copy two values from the **Connection** section:

    * **Domain** (looks like `abcd1234.tunnel.anthropic.com`)
    * **Token** (click the eye icon, then copy)
  </Step>

  <Step title="Set up the deployment directory">
    <Tabs>
      <Tab title="macOS / Linux">
        ```bash
        mkdir -p mcp-tunnel/{config,data}
        cd mcp-tunnel
        export TUNNEL_DOMAIN=YOUR_TUNNEL_DOMAIN_HERE   # from step 1
        export TUNNEL_TOKEN='eyJ...'            # from step 1
        ```
      </Tab>

      <Tab title="Windows (PowerShell)">
        ```powershell
        New-Item -ItemType Directory -Force -Pa
```

</details>

---

## V2D-33

- **provider**: openai
- **document**: Running agents
- **section**: Running agents › Runner lifecycle and configuration › The agent loop
- **source span**: `ver_2c60e99cfd929a738910b893fd6f1a40` chars 1039–1133
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, identifier_vs_semantic_distractor, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens when you call any of the three `Runner` methods above?

**Proposed answer**: You pass in a starting agent and input.

**Proposed atomic claims**: When you call any of the three `Runner` methods above, you pass in a starting agent and input.

**Critical strings**: Runner

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_2c60e99cfd929a738910b893fd6f1a40` chars 1039–1133 · hash `81aad2cf94487959…`

```
When you call any of the three `Runner` methods above, you pass in a starting agent and input.
```

<details><summary>Context before</summary>

```
r.run], which runs async and returns a [`RunResult`][agents.result.RunResult].
2. [`Runner.run_sync()`][agents.run.Runner.run_sync], which is a sync method and just runs `.run()` under the hood.
3. [`Runner.run_streamed()`][agents.run.Runner.run_streamed], which runs async and returns a [`RunResultStreaming`][agents.result.RunResultStreaming]. It calls the LLM in streaming mode, and streams those events to you as they are received.

```python
from agents import Agent, Runner

async def main():
    agent = Agent(name="Assistant", instructions="You are a helpful assistant")

    result = await Runner.run(agent, "Write a haiku about recursion in programming.")
    print(result.final_output)
    # Code within the code,
    # Functions calling themselves,
    # Infinite loop's dance
```

Read more in the [results guide](results.md).

## Runner lifecycle and configuration

### The agent loop


```

</details>

<details><summary>Context after</summary>

```
 The input can be:

-   a string (treated as a user message),
-   a list of input items in the OpenAI Responses API format, or
-   a [`RunState`][agents.run_state.RunState] when resuming a paused run or a run stopped with `cancel(mode="after_turn")`. The state can also carry [input staged for the next resumed model call](results.md#add-input-before-resuming).

The runner then runs a loop:

1. We call the LLM for the current agent, with the current input.
2. The LLM produces its output.
    1. If the runner classifies the LLM's output as final output, the loop ends and we return the result.
    2. If the LLM requests a handoff, we update the current agent and input, and re-run the loop.
    3. If the LLM produces tool calls, we run those tool calls, append the results, and re-run the loop.
3. If we exceed the `max_turns` passed, we raise a [`MaxTurnsExceeded`][agents.exceptions.MaxTurnsEx
```

</details>

---

## V2D-34

- **provider**: anthropic
- **document**: Embeddings
- **section**: and cosine similarity are the same. › FAQ
- **source span**: `ver_26f61f56d6ff7124cfa38152f7baef3d` chars 17895–18001
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, lexical_query_shape, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens when using the `input_type` parameter?

**Proposed answer**: Special prompts are prepended to the input text prior to embedding.

**Proposed atomic claims**: When using the `input_type` parameter, special prompts are prepended to the input text prior to embedding.

**Critical strings**: input_type

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_26f61f56d6ff7124cfa38152f7baef3d` chars 17895–18001 · hash `0977226e832171ae…`

```
When using the `input_type` parameter, special prompts are prepended to the input text prior to embedding.
```

<details><summary>Context before</summary>

```
dings are normalized to length 1, which means that:

    * Cosine similarity is equivalent to dot-product similarity, while the latter can be computed more quickly.
    * Cosine similarity and Euclidean distance result in identical rankings.
  </Accordion>

  <Accordion title="What is the relationship between characters, words, and tokens?">
    See the [Voyage tokenization guide](https://docs.voyageai.com/docs/tokenization?ref=anthropic).
  </Accordion>

  <Accordion title="When and how should I use the input_type parameter?">
    For all retrieval tasks and use cases (for example, RAG), use the `input_type` parameter to specify whether the input text is a query or document. Do not omit `input_type` or set `input_type=None`. Specifying whether input text is a query or document can create better dense vector representations for retrieval, which can lead to better retrieval quality.

    
```

</details>

<details><summary>Context after</summary>

```
 Specifically:

    > 📘 **Prompts associated with `input_type`**
    >
    > * For a query, the prompt is “Represent the query for retrieving supporting documents: “.
    >
    > * For a document, the prompt is “Represent the document for retrieval: “.
    >
    > * Example
    >
    >   * When `input_type="query"`, a query like "When is Apple's conference call scheduled?" will become "**Represent the query for retrieving supporting documents:** When is Apple's conference call scheduled?"
    >
    >   * When `input_type="document"`, a query like "Apple's conference call to discuss fourth fiscal quarter results and business updates is scheduled for Thursday, November 2, 2023 at 2p.m. PT / 5p.m. ET." will become "**Represent the document for retrieval:** Apple's conference call to discuss fourth fiscal quarter results and business updates is scheduled for Thursday, November 2, 2023 at 2p.
```

</details>

---

## V2D-35

- **provider**: openai
- **document**: OpenAI Python API library
- **section**: Remove `await` for non-async usage. › Webhook Verification › Verifying webhook payloads directly
- **source span**: `ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` chars 16257–16361
- **evidence kind**: `constraint_statement`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, parameter_error_literal_lookup, identifier_vs_semantic_distractor, same_document_passage_discrimination
- **binding**: structural-or-subject-window
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What must `body` be?

**Proposed answer**: Note that the `body` parameter must be the raw JSON string sent from the server (do not parse it first).

**Proposed atomic claims**: Note that the `body` parameter must be the raw JSON string sent from the server (do not parse it first).

**Critical strings**: body

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` chars 16257–16361 · hash `b41d372109411e73…`

```
Note that the `body` parameter must be the raw JSON string sent from the server (do not parse it first).
```

<details><summary>Context before</summary>

```
)

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


if __name__ == "__main__":
    app.run(port=8000)
```

### Verifying webhook payloads directly

In some cases, you may want to verify the webhook separately from parsing the payload. If you prefer to handle these steps separately, we provide the method `client.webhooks.verify_signature()` to _only verify_ the signature of a webhook request. Like `.unwrap()`, this method will raise an error if the signature is invalid.


```

</details>

<details><summary>Context after</summary>

```
 You will then need to parse the body after verifying the signature.

```python
import json
from openai import OpenAI
from flask import Flask, request

app = Flask(__name__)
client = OpenAI()  # OPENAI_WEBHOOK_SECRET environment variable is used by default


@app.route("/webhook", methods=["POST"])
def webhook():
    request_body = request.get_data(as_text=True)

    try:
        client.webhooks.verify_signature(request_body, request.headers)

        # Parse the body after verification
        event = json.loads(request_body)
        print("Verified event:", event)

        return "ok"
    except Exception as e:
        print("Invalid signature:", e)
        return "Invalid signature", 400


if __name__ == "__main__":
    app.run(port=8000)
```

## Handling errors

When the library is unable to connect to the API (for example, due to network connection problems or a timeout), a subclass
```

</details>

---

## V2D-36

- **provider**: anthropic
- **document**: Search results
- **section**: How it works › Required fields
- **source span**: `ver_42a4f3d941b664a285883aaf6ff90373` chars 2518–2655
- **evidence kind**: `parameter_table_row`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, parameter_error_literal_lookup, identifier_vs_semantic_distractor
- **binding**: structural: parameter is the row's first cell, type is another cell of the same row
- **generator confidence**: high
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What type does the `title` parameter take?

**Proposed answer**: `string`

**Proposed atomic claims**: ``title` is of type string.`

**Critical strings**: title, string

**Generator notes**: Row-scoped association. Reviewer should confirm the table is a parameter table and that the column header means the parameter's own type rather than, say, a return type. FLAG_LOW_VALUE

### Evidence E1 (verbatim, authoritative)

`ver_42a4f3d941b664a285883aaf6ff90373` chars 2518–2655 · hash `2f4dc41ed17b240c…`

```
| `title`   | string | A descriptive title for the search result                                                                        |
```

<details><summary>Context before</summary>

```
le Title", // Required: Title of the result
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
| `source`  | string | The source of the content. Any stable string works: a URL, or an internal identifier such as `kb://article-1234` |

```

</details>

<details><summary>Context after</summary>

```

| `content` | array  | An array of text blocks containing the actual content                                                            |

### Optional fields

| Field           | Type   | Description                                                                                                                                                                                                                                                                                                                     |
| --------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `citations`     | object | Citation
```

</details>

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
