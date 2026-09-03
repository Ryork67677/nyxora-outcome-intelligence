# V2-DEVSET-001 review packet (batch 101)

**15 candidates · corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · generated 2026-09-01T02:02:49Z (2026-08-31 22:02 ET)**

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
