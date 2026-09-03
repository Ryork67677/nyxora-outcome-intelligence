# V2-DEVSET-001 round-1 repair review (16 FIX_REQUIRED only)

**16 repaired candidates · corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · generated 2026-09-01T02:45:03Z (2026-08-31 22:45 ET)**

This packet is **only** the 16 cases ChatGPT marked `FIX_REQUIRED` in round 1. The 34 PASS cases are **not** in this file and must **not** be imported as frozen gold.

Every candidate here is `candidate_unverified_after_fix`. Nothing is ground truth. The evidence is quoted verbatim from the frozen corpus and is authoritative for this review — **do not consult live documentation**, which may have changed since the snapshot.

Judge the *repaired* question, answer and claims against the evidence and its surrounding context only. Return one record per candidate with verdict `PASS | FAIL | FIX_REQUIRED | UNCERTAIN` and the GOLD review fields in `docs/GOLD-REVIEW-PROCEDURE.md`.

Spans were expanded only where round 1 set `evidence_boundary_complete=false`. Hashes were recomputed from the frozen snapshot. `version_id` is unchanged. Old question/span are in each case's repair history.

---

## V2D-03

- **provider**: anthropic
- **document**: Compliance API
- **section**: Chats › List chats › Query Parameters
- **source span**: `ver_1d58a563501b073d898977de6bc2a823` chars 4640364–4640538
- **evidence kind**: `configuration_interaction`
- **reasoning type**: `configuration_interaction`
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **round-1 verdict**: FIX_REQUIRED
- **span expanded this round**: false

**Repaired question** (a suggestion, not gold)

> For org-wide queries, what must any time filter match?

**Repaired answer**: The sort key: `created_at.*` filters require `order_by=created_at`, and `updated_at.*` filters require `order_by=updated_at`.

**Repaired atomic claims**:

1. For org-wide queries, any time filter must match the sort key: `created_at.*` filters require `order_by=created_at`, and `updated_at.*` filters require `order_by=updated_at`.

**Critical strings**: created_at.*, order_by=created_at, updated_at.*, order_by=updated_at

**What changed.** Rewrote around the org-wide time-filter/sort-key rule rather than what `created_at` itself requires. The existing span already stated the full rule (created_at.* and updated_at.*), so the boundary was not expanded.

**Round-1 ChatGPT reason.** The evidence supports the full rule, but the question incorrectly asks what created_at itself requires; specifically created_at.* filters on org-wide queries require order_by=created_at, while the answer also adds the separate updated_at rule.

### Evidence E1 (verbatim, authoritative)

`ver_1d58a563501b073d898977de6bc2a823` chars 4640364–4640538 · hash `c8a02c427ca5f0eeb935c95bc9dc780e1e3d3c86be46519f89d65214de50948f`

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

<details><summary>Repair history (old question / old span)</summary>

**Old question.** What does `created_at` require?

**Old answer.** For org-wide queries, any time filter must match the sort key: `created_at.*` filters require `order_by=created_at`, and `updated_at.*` filters require `order_by=updated_at`.

**Old evidence** — `ver_1d58a563501b073d898977de6bc2a823` 4640364–4640538 · `c8a02c427ca5f0eeb935c95bc9dc780e1e3d3c86be46519f89d65214de50948f`

```
For org-wide queries, any time filter must match the sort key: `created_at.*` filters require `order_by=created_at`, and `updated_at.*` filters require `order_by=updated_at`.
```

</details>

---

## V2D-05

- **provider**: anthropic
- **document**: Admin
- **section**: Usage Report › Get Messages Usage Report › Query Parameters
- **source span**: `ver_c299b58fe1f5a4d3a081b550334a7df6` chars 145736–145804
- **evidence kind**: `normative_statement`
- **reasoning type**: `configuration_interaction`
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **round-1 verdict**: FIX_REQUIRED
- **span expanded this round**: false

**Repaired question** (a suggestion, not gold)

> What does grouping by `speed` require?

**Repaired answer**: The `fast-mode-2026-02-01` beta header.

**Repaired atomic claims**:

1. Grouping by `speed` requires the `fast-mode-2026-02-01` beta header.

**Critical strings**: speed, fast-mode-2026-02-01

**What changed.** Rewrote question and claim so grouping by `speed` (not `speed` generally) requires the `fast-mode-2026-02-01` beta header. Span unchanged.

**Round-1 ChatGPT reason.** The source says grouping by speed requires the beta header; it does not state that speed generally requires it. Rewrite the question and claim to preserve the grouping condition.

### Evidence E1 (verbatim, authoritative)

`ver_c299b58fe1f5a4d3a081b550334a7df6` chars 145736–145804 · hash `68696c806a8d47853c355ddb31e022ccde229994dda89ac214f51755d8b12e59`

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

<details><summary>Repair history (old question / old span)</summary>

**Old question.** What does `speed` require?

**Old answer.** The `fast-mode-2026-02-01` beta header.

**Old evidence** — `ver_c299b58fe1f5a4d3a081b550334a7df6` 145736–145804 · `68696c806a8d47853c355ddb31e022ccde229994dda89ac214f51755d8b12e59`

```
Grouping by `speed` requires the `fast-mode-2026-02-01` beta header.
```

</details>

---

## V2D-06

- **provider**: anthropic
- **document**: Fast mode (research preview)
- **section**: Checking which speed was used
- **source span**: `ver_cc7d6ed2a636d74fc7aca7885ba9ce60` chars 9863–10222
- **evidence kind**: `short_normative`
- **reasoning type**: `configuration_interaction`
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **round-1 verdict**: FIX_REQUIRED
- **span expanded this round**: true

**Repaired question** (a suggestion, not gold)

> What is `usage.speed` when a request with `speed: "fast"` succeeds, including on Claude Opus 4.6?

**Repaired answer**: It is `"fast"`. Claude Opus 4.6 is an exception: requesting fast mode can succeed while the `speed` field shows `"standard"`.

**Repaired atomic claims**:

1. When a request with `speed: "fast"` succeeds, `usage.speed` is `"fast"`.
2. If you are using Claude Opus 4.6 and request fast mode, it silently switches to standard speed and the `speed` field accurately shows `"standard"`.

**Critical strings**: usage.speed, Claude Opus 4.6, standard

**What changed.** Included the Claude Opus 4.6 exception in the question, answer, and claims. Expanded the evidence boundary forward to that following exception (speed=fast can succeed while usage.speed is standard).

**Round-1 ChatGPT reason.** The selected sentence is qualified by the immediately following Claude Opus 4.6 exception, where a speed=fast request can succeed while usage.speed is standard. The candidate needs that scope or exception.

### Evidence E1 (verbatim, authoritative)

`ver_cc7d6ed2a636d74fc7aca7885ba9ce60` chars 9863–10222 · hash `1ae25e4479c1961c3ac649534d70309e9fc4f29a776e49115c2c7e0209f536b4`

```
When a request with `speed: "fast"` succeeds, `usage.speed` is `"fast"`. If you are using Claude Opus 4.6 and request fast mode, its behavior is unique. Instead of returning an error like other models that don't support fast mode, it silently switches to standard speed. Though there is no error with Opus 4.6, the `speed` field accurately shows `"standard"`.
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
    - role: user
      content: Hello
  YAML
  ```

  ```python Python
  client = anthropic.Anthropic()

  response = client.beta.messages.create(
      model="claude-opus-5",
      max_tokens=1024,
      speed="fast",
      betas=["fast-mode-2026-02-01"],
      messages=[{"role": "user",
```

</details>

<details><summary>Repair history (old question / old span)</summary>

**Old question.** What happens when a request with `speed: "fast"` succeeds?

**Old answer.** `usage.speed` is `"fast"`.

**Old evidence** — `ver_cc7d6ed2a636d74fc7aca7885ba9ce60` 9863–9935 · `2d30e610b6255b61fbff2e6e3331557eb3fc865d50dcec703c0e859a24c1fb3a`

```
When a request with `speed: "fast"` succeeds, `usage.speed` is `"fast"`.
```

</details>

---

## V2D-08

- **provider**: anthropic
- **document**: Beta
- **section**: Models › List Models › Returns
- **source span**: `ver_de7f74230c8f10d30aea5d037a3bd0a5` chars 8804–8937
- **evidence kind**: `short_normative`
- **reasoning type**: `exact_lookup`
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **round-1 verdict**: FIX_REQUIRED
- **span expanded this round**: true

**Repaired question** (a suggestion, not gold)

> What does `allowed_fallback_models` contain?

**Repaired answer**: Model IDs this model accepts as `fallbacks[i].model` on the Messages API.

**Repaired atomic claims**:

1. `allowed_fallback_models` contains model IDs this model accepts as `fallbacks[i].model` on the Messages API.

**Critical strings**: allowed_fallback_models, fallbacks[i].model

**What changed.** Named the omitted field `allowed_fallback_models` in the question. Expanded the evidence boundary backwards to the field name.

**Round-1 ChatGPT reason.** The factual description is supported, but the question is malformed and omits the field being defined, allowed_fallback_models. The field name is needed to bind the description to the correct return value.

### Evidence E1 (verbatim, authoritative)

`ver_de7f74230c8f10d30aea5d037a3bd0a5` chars 8804–8937 · hash `a71662214aeb083e40ff4eed5dc1eec7fe7cb4ea3925ff888836afefcb19386c`

```
  - `allowed_fallback_models: array of string or null`

    Model IDs this model accepts as `fallbacks[i].model` on the Messages API.
```

<details><summary>Context before</summary>

```
`"interleaved-thinking-2025-05-14"`

    - `"code-execution-2025-05-22"`

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

<details><summary>Repair history (old question / old span)</summary>

**Old question.** What does Model IDs this model accept?

**Old answer.** Model IDs this model accepts as `fallbacks[i].model` on the Messages API.

**Old evidence** — `ver_de7f74230c8f10d30aea5d037a3bd0a5` 8860–8937 · `95982f914e9d0e93a07148156b3808869ecfaf8c4d28544d5aaee396d016d88b`

```
    Model IDs this model accepts as `fallbacks[i].model` on the Messages API.
```

</details>

---

## V2D-13

- **provider**: openai
- **document**: Models
- **section**: Models › OpenAI models › Hosted multi-agent (experimental) › Current limitations
- **source span**: `ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 19331–19456
- **evidence kind**: `configuration_interaction`
- **reasoning type**: `configuration_interaction`
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **round-1 verdict**: FIX_REQUIRED
- **span expanded this round**: false

**Repaired question** (a suggestion, not gold)

> What does the experimental model reject?

**Repaired answer**: `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.

**Repaired atomic claims**:

1. The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.

**Critical strings**: betas, reasoning.summary, max_tool_calls

**What changed.** RELATION_DIRECTION fix: the question no longer asks what `betas` override. Subject is the experimental model; relation is rejects; object is the listed overrides. Span unchanged.

**Round-1 ChatGPT reason.** The answer is supported, but the question 'What does betas override?' misstates the relation. The source says the model rejects caller-supplied betas overrides along with reasoning.summary and max_tool_calls.

### Evidence E1 (verbatim, authoritative)

`ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 19331–19456 · hash `540a39028df8184945b1d598976982b6092e1c52dbb919d3c009f6d5df2ccad0`

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

<details><summary>Repair history (old question / old span)</summary>

**Old question.** What does `betas` override?

**Old answer.** The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.

**Old evidence** — `ver_ae909bf8b4bbbe1d1a11119447f7ac94` 19331–19456 · `540a39028df8184945b1d598976982b6092e1c52dbb919d3c009f6d5df2ccad0`

```
The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.
```

</details>

---

## V2D-18

- **provider**: openai
- **document**: Testing
- **section**: Testing › Agent workflow recipes › Inject model failures
- **source span**: `ver_d2295786320b2815477eb963eb1f5e8a` chars 9219–9850
- **evidence kind**: `short_normative`
- **reasoning type**: `exact_lookup`
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **round-1 verdict**: FIX_REQUIRED
- **span expanded this round**: true

**Repaired question** (a suggestion, not gold)

> What does `ModelStep.raise_error` accept?

**Repaired answer**: A fixed `ModelRetryAdvice` value; use a custom `Model` when retry advice itself must vary dynamically by attempt.

**Repaired atomic claims**:

1. `ModelStep.raise_error` accepts a fixed `ModelRetryAdvice` value; use a custom `Model` when retry advice itself must vary dynamically by attempt.

**Critical strings**: ModelStep.raise_error, ModelRetryAdvice

**What changed.** Replaced 'the Python helper' with `ModelStep.raise_error`. Expanded the evidence boundary backwards so the helper name is inside the span.

**Round-1 ChatGPT reason.** The factual statement is supported, but 'the Python helper' is not identified in the question or selected evidence. The surrounding section indicates ModelStep.raise_error; name that helper explicitly.

### Evidence E1 (verbatim, authoritative)

`ver_d2295786320b2815477eb963eb1f5e8a` chars 9219–9850 · hash `5eaa435ade77face5566e2a959ab20237247f93384c38b64c1f79cdf4cea24d3`

```
Use `ModelStep.raise_error()` to fail one model call. Optional retry advice belongs to that exact scripted error:

```python
from agents import ModelRetryAdvice
from agents.testing import ModelStep


step = ModelStep.raise_error(
    RuntimeError("temporary failure"),
    retry_advice=ModelRetryAdvice(suggested=True, replay_safety="safe"),
)
```

The runner's retry policy decides whether advice causes another attempt. Each retry is another model call and consumes the next scripted step. The Python helper accepts a fixed `ModelRetryAdvice` value; use a custom `Model` when retry advice itself must vary dynamically by attempt.
```

<details><summary>Context before</summary>

```
rmalized start, delta, item-completion, and terminal response events. The terminal response carries the complete output and usage.

Use `ModelStep.stream()` only when the exact normalized `TResponseStreamEvent` sequence is part of the behavior under test:

```python
step = ModelStep.stream(
    events,
    output=[assistant_message("The terminal output used by the runner.")],
)
```

`events` may be a fixed sequence or an async factory that receives the recorded `ModelCall`. The optional `output` is the response returned if the same step is used in a non-streaming call. Exact stream events are SDK-normalized events, not Responses API or Chat Completions wire chunks.

Automatic streaming rejects normalized output-item kinds whose incremental lifecycle is not implemented. Use `ModelStep.stream(...)` for those items instead of relying on a partial event sequence.

### Inject model failures


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

<details><summary>Repair history (old question / old span)</summary>

**Old question.** What does the Python helper accept?

**Old answer.** The Python helper accepts a fixed `ModelRetryAdvice` value; use a custom `Model` when retry advice itself must vary dynamically by attempt.

**Old evidence** — `ver_d2295786320b2815477eb963eb1f5e8a` 9711–9850 · `98f949d187d774cf689478066c3b8933a2327a701129539680d5ae21bd9af9c6`

```
The Python helper accepts a fixed `ModelRetryAdvice` value; use a custom `Model` when retry advice itself must vary dynamically by attempt.
```

</details>

---

## V2D-19

- **provider**: anthropic
- **document**: Using Agent Skills with the API
- **section**: Managing custom Skills › Creating a Skill
- **source span**: `ver_5a15a8f543d432ef91eb6e2997f51225` chars 72650–72735
- **evidence kind**: `short_normative`
- **reasoning type**: `exact_lookup`
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **round-1 verdict**: FIX_REQUIRED
- **span expanded this round**: false

**Repaired question** (a suggestion, not gold)

> What argument does `files_from_dir` accept?

**Repaired answer**: A directory path.

**Repaired atomic claims**:

1. The Python SDK `files_from_dir` helper accepts a directory path.

**Critical strings**: files_from_dir

**What changed.** Grammatical rewrite: the question now asks what argument `files_from_dir` accepts. Span unchanged.

**Round-1 ChatGPT reason.** The underlying files_from_dir fact is supported, but the proposed question is grammatically malformed. Rewrite it as what argument files_from_dir accepts.

### Evidence E1 (verbatim, authoritative)

`ver_5a15a8f543d432ef91eb6e2997f51225` chars 72650–72735 · hash `dcf16d18e94cb433a7aa16e08368cde0eaafaf15f6738dc5db9363ca67bf9f3a`

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

<details><summary>Repair history (old question / old span)</summary>

**Old question.** What does the Python SDK also provides a `files_from_dir` helper that accept?

**Old answer.** The Python SDK also provides a `files_from_dir` helper that accepts a directory path.

**Old evidence** — `ver_5a15a8f543d432ef91eb6e2997f51225` 72650–72735 · `dcf16d18e94cb433a7aa16e08368cde0eaafaf15f6738dc5db9363ca67bf9f3a`

```
The Python SDK also provides a `files_from_dir` helper that accepts a directory path.
```

</details>

---

## V2D-21

- **provider**: anthropic
- **document**: Memory tool
- **section**: Security considerations › File storage size
- **source span**: `ver_96d1698a3864f79451e8576f87a07004` chars 34903–35023
- **evidence kind**: `short_normative`
- **reasoning type**: `error_behavior`
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **round-1 verdict**: FIX_REQUIRED
- **span expanded this round**: false

**Repaired question** (a suggestion, not gold)

> How should large `view` output be limited, and how can Claude page through the rest with `view_range`?

**Repaired answer**: Cap how many characters the `view` command returns, and let Claude page through the rest with `view_range`.

**Repaired atomic claims**:

1. Consider capping how many characters the `view` command returns, and let Claude page through the rest with `view_range`.

**Critical strings**: view, view_range

**What changed.** Rewrote the malformed question as the recommended safeguard: limit `view` output and page through the rest with `view_range`. Span unchanged.

**Round-1 ChatGPT reason.** The recommendation is supported, but the proposed question is malformed. Ask how to handle large view output or what safeguard is recommended for the view command.

### Evidence E1 (verbatim, authoritative)

`ver_96d1698a3864f79451e8576f87a07004` chars 34903–35023 · hash `829b4270435161f75e29c18c666d040ecac6c5820aeea5bc33c8c65c9b51092b`

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

<details><summary>Repair history (old question / old span)</summary>

**Old question.** What does Consider capping how many characters the `view` command return?

**Old answer.** Consider capping how many characters the `view` command returns, and let Claude page through the rest with `view_range`.

**Old evidence** — `ver_96d1698a3864f79451e8576f87a07004` 34903–35023 · `829b4270435161f75e29c18c666d040ecac6c5820aeea5bc33c8c65c9b51092b`

```
Consider capping how many characters the `view` command returns, and let Claude page through the rest with `view_range`.
```

</details>

---

## V2D-22

- **provider**: anthropic
- **document**: Tool runner (SDK)
- **section**: Advanced usage › Taking over message history
- **source span**: `ver_96d5aba3c4e7771cabd4f3d4f5a3fff1` chars 38316–38425
- **evidence kind**: `short_normative`
- **reasoning type**: `error_behavior`
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **round-1 verdict**: FIX_REQUIRED
- **span expanded this round**: false

**Repaired question** (a suggestion, not gold)

> What has already been appended by the time `next_message` returns?

**Repaired answer**: The assistant message and tool result for that turn.

**Repaired atomic claims**:

1. By the time `next_message` returns, the assistant message and tool result for that turn are already appended.

**Critical strings**: next_message

**What changed.** Rewrote the malformed question to 'What has already been appended by the time `next_message` returns?'. Span unchanged.

**Round-1 ChatGPT reason.** The statement about next_message is supported, but the question is malformed. Rewrite as 'What has already been appended by the time next_message returns?'

### Evidence E1 (verbatim, authoritative)

`ver_96d5aba3c4e7771cabd4f3d4f5a3fff1` chars 38316–38425 · hash `cc4be65021e4ea3f13b4ad9ce60d23942d2d0ec76c0c46663fd82d8025ee4224`

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

<details><summary>Repair history (old question / old span)</summary>

**Old question.** What does By the time `next_message` return?

**Old answer.** By the time `next_message` returns, the assistant message and tool result for that turn are already appended.

**Old evidence** — `ver_96d5aba3c4e7771cabd4f3d4f5a3fff1` 38316–38425 · `cc4be65021e4ea3f13b4ad9ce60d23942d2d0ec76c0c46663fd82d8025ee4224`

```
By the time `next_message` returns, the assistant message and tool result for that turn are already appended.
```

</details>

---

## V2D-23

- **provider**: openai
- **document**: Sandbox clients
- **section**: Sandbox clients › Supported hosted platforms › Size Modal sandboxes
- **source span**: `ver_3d4b8881962381cbfba18ade50c598e1` chars 10824–11465
- **evidence kind**: `long_technical_section`
- **reasoning type**: `exact_lookup`
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **round-1 verdict**: FIX_REQUIRED
- **span expanded this round**: false

**Repaired question** (a suggestion, not gold)

> What are credentialless `rclone` mounts limited to?

**Repaired answer**: S3, GCS, R2, and Azure Blob.

**Repaired atomic claims**:

1. Credentialless `rclone` mounts are limited to S3, GCS, R2, and Azure Blob.

**Critical strings**: rclone, FuseMountPattern, blobfuse2

**What changed.** Grammar only: 'What are credentialless `rclone` mounts limited to?'. No factual change. Span unchanged.

**Round-1 ChatGPT reason.** The answer is exactly supported, but the question should be grammatically corrected to 'What are credentialless rclone mounts limited to?' No factual change is needed.

### Evidence E1 (verbatim, authoritative)

`ver_3d4b8881962381cbfba18ade50c598e1` chars 10824–11465 · hash `b97014844240948026e9df02c8b13569c24b56a95ddfab31721fb318fdd150a1`

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

<details><summary>Repair history (old question / old span)</summary>

**Old question.** What is Credentialless `rclone` mounts limited to?

**Old answer.** Credentialless `rclone` mounts are limited to S3, GCS, R2, and Azure Blob.

**Old evidence** — `ver_3d4b8881962381cbfba18ade50c598e1` 10824–11465 · `b97014844240948026e9df02c8b13569c24b56a95ddfab31721fb318fdd150a1`

```
Credentialless `rclone` mounts are limited to S3, GCS, R2, and Azure Blob. An in-container Box mount requires a non-interactive authentication source and the acknowledgement that matches that source. `FuseMountPattern` requires broad acknowledgement because `blobfuse2` discovers ambient Azure authority, even when no inline credential is configured. `S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses ambient IAM authority. These requirements also apply when Docker is the backend; the check marks below indicate that Docker can execute the mount after the applicable authority boundary is satisfied.
```

</details>

---

## V2D-32

- **provider**: anthropic
- **document**: MCP tunnels quickstart
- **section**: What you need
- **source span**: `ver_067b3bfdc28f24500ea19b97bf3e80b1` chars 1792–1989
- **evidence kind**: `constraint_statement`
- **reasoning type**: `exact_lookup`
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **round-1 verdict**: FIX_REQUIRED
- **span expanded this round**: true

**Repaired question** (a suggestion, not gold)

> What OpenSSL version is required, and what is required of the `openssl` binary on Windows?

**Repaired answer**: OpenSSL 1.1.1 or later. On Windows, install it separately (the `openssl` binary must be on your `PATH`).

**Repaired atomic claims**:

1. OpenSSL 1.1.1 or later is required.
2. On Windows, install OpenSSL separately (the `openssl` binary must be on your `PATH`).

**Critical strings**: OpenSSL, 1.1.1, openssl, PATH

**What changed.** Included the adjacent OpenSSL 1.1.1 or later version requirement and narrowed the Windows part to install/PATH. Expanded the evidence boundary backwards to the start of that bullet.

**Round-1 ChatGPT reason.** The proposed answer is supported as an installation/PATH statement, but the broad question 'What must openssl be?' omits the adjacent requirement that OpenSSL be version 1.1.1 or later. Narrow the question to Windows installation/PATH or include the version requirement.

### Evidence E1 (verbatim, authoritative)

`ver_067b3bfdc28f24500ea19b97bf3e80b1` chars 1792–1989 · hash `64a21c31843c3819f9bbf9e1f235df92d9bd00f21a0df635c4c8c8bf9814082e`

```
* [OpenSSL](https://openssl-library.org/source/) 1.1.1 or later. Preinstalled on macOS and most Linux distributions; on Windows, install it separately (the `openssl` binary must be on your `PATH`).
```

<details><summary>Context before</summary>

```
What you'll build

A two-container [tunnel stack](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/concepts#components) (the [proxy](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/concepts#components) and [cloudflared](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/concepts#components)) plus a sample MCP server running alongside it. When everything is running, the sample server is reachable from Claude at `https://echo.<your-tunnel-domain>/mcp` even though nothing is listening on a public port.

## What you need

* [Docker and Docker Compose](https://docs.docker.com/get-docker/) on a machine with outbound internet access.
* A role in the [Claude Console](https://platform.claude.com) that can manage MCP tunnels. See the [Console guide prerequisites](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/console#prerequisites).

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

<details><summary>Repair history (old question / old span)</summary>

**Old question.** What must `openssl` be?

**Old answer.** Preinstalled on macOS and most Linux distributions; on Windows, install it separately (the `openssl` binary must be on your `PATH`).

**Old evidence** — `ver_067b3bfdc28f24500ea19b97bf3e80b1` 1857–1989 · `a73bb959f95532e95f81c5b7ca24d8e14fa3a92af229fc7e0305755d80dedd37`

```
Preinstalled on macOS and most Linux distributions; on Windows, install it separately (the `openssl` binary must be on your `PATH`).
```

</details>

---

## V2D-33

- **provider**: openai
- **document**: Running agents
- **section**: Running agents › Runner lifecycle and configuration › The agent loop
- **source span**: `ver_2c60e99cfd929a738910b893fd6f1a40` chars 82–1133
- **evidence kind**: `short_normative`
- **reasoning type**: `exact_lookup`
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **round-1 verdict**: FIX_REQUIRED
- **span expanded this round**: true

**Repaired question** (a suggestion, not gold)

> What do you pass in when you call `Runner.run`, `Runner.run_sync`, or `Runner.run_streamed`?

**Repaired answer**: A starting agent and input.

**Repaired atomic claims**:

1. When you call `Runner.run`, `Runner.run_sync`, or `Runner.run_streamed`, you pass in a starting agent and input.

**Critical strings**: Runner.run, Runner.run_sync, Runner.run_streamed, Runner

**What changed.** Replaced 'the three Runner methods above' with `Runner.run`, `Runner.run_sync`, and `Runner.run_streamed`. Expanded the evidence boundary backwards to the list that names those methods.

**Round-1 ChatGPT reason.** The fact is supported, but 'the three Runner methods above' is a deictic dependency on preceding text. Name Runner.run, Runner.run_sync, and Runner.run_streamed or otherwise make the question self-contained.

### Evidence E1 (verbatim, authoritative)

`ver_2c60e99cfd929a738910b893fd6f1a40` chars 82–1133 · hash `8dcd14030925dca2775dd03788cf65e7c62691ba478dcbf4bfffcd9fb8555efe`

```
You have 3 options:

1. [`Runner.run()`][agents.run.Runner.run], which runs async and returns a [`RunResult`][agents.result.RunResult].
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

When you call any of the three `Runner` methods above, you pass in a starting agent and input.
```

<details><summary>Context before</summary>

```
# Running agents

You can run agents via the [`Runner`][agents.run.Runner] class. 
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

<details><summary>Repair history (old question / old span)</summary>

**Old question.** What happens when you call any of the three `Runner` methods above?

**Old answer.** You pass in a starting agent and input.

**Old evidence** — `ver_2c60e99cfd929a738910b893fd6f1a40` 1039–1133 · `81aad2cf94487959520dc00de693cf7bfe8d949944ce1ca33ff88e899bc7d926`

```
When you call any of the three `Runner` methods above, you pass in a starting agent and input.
```

</details>

---

## V2D-37

- **provider**: openai
- **document**: OpenAI Python API library
- **section**: Remove `await` for non-async usage. › File uploads
- **source span**: `ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` chars 14118–14318
- **evidence kind**: `short_normative`
- **reasoning type**: `exact_lookup`
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **round-1 verdict**: FIX_REQUIRED
- **span expanded this round**: true

**Repaired question** (a suggestion, not gold)

> What happens if you pass a `PathLike` instance to the async client?

**Repaired answer**: The file contents will be read asynchronously automatically.

**Repaired atomic claims**:

1. If you pass a PathLike instance to the async client, the file contents will be read asynchronously automatically.

**Critical strings**: PathLike, async client

**What changed.** Scoped PathLike async file-reading to the async client. Expanded the evidence boundary backwards to the sentence that names the async client.

**Round-1 ChatGPT reason.** The surrounding sentence establishes that this asynchronous file-reading behavior is for the async client. The proposed question omits that scope and therefore overgeneralizes PathLike behavior.

### Evidence E1 (verbatim, authoritative)

`ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` chars 14118–14318 · hash `21ffcc2671568c84ca6000e864412e9b44513168e97b389e665b6d7d266660c4`

```
The async client uses the exact same interface. If you pass a [`PathLike`](https://docs.python.org/3/library/os.html#os.PathLike) instance, the file contents will be read asynchronously automatically.
```

<details><summary>Context before</summary>

```
sor: {first_page.after}")  # => "next page cursor: ..."
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

<details><summary>Repair history (old question / old span)</summary>

**Old question.** What happens if you pass a `PathLike` instance?

**Old answer.** The file contents will be read asynchronously automatically.

**Old evidence** — `ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` 14166–14318 · `c7de0d42f68c2ceb6a1330b77e0017d9ab086e08594d5fa83b86ffb3dcd8f616`

```
If you pass a [`PathLike`](https://docs.python.org/3/library/os.html#os.PathLike) instance, the file contents will be read asynchronously automatically.
```

</details>

---

## V2D-38

- **provider**: anthropic
- **document**: Prompting Claude Opus 4.8
- **section**: Design and frontend defaults
- **source span**: `ver_997f51c850a46243a541d4f4ec4175ce` chars 10667–11143
- **evidence kind**: `short_normative`
- **reasoning type**: `exact_lookup`
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **round-1 verdict**: FIX_REQUIRED
- **span expanded this round**: true

**Repaired question** (a suggestion, not gold)

> If you previously relied on `temperature` for design variety, what approach should you use?

**Repaired answer**: Have the model propose distinct visual directions before building; it produces meaningfully different directions across runs.

**Repaired atomic claims**:

1. If you previously relied on `temperature` for design variety, have the model propose distinct visual directions before building; it produces meaningfully different directions across runs.

**Critical strings**: temperature, distinct visual directions

**What changed.** Replaced 'this approach' with the explicit approach: having the model propose distinct visual directions before building. Expanded the evidence boundary to the heading that names the approach and the following example prompt that states 'distinct visual directions'.

**Round-1 ChatGPT reason.** The claim is supported in context, but both evidence and answer rely on the unresolved phrase 'this approach,' which refers to having the model propose visual options before building. State that approach explicitly.

### Evidence E1 (verbatim, authoritative)

`ver_997f51c850a46243a541d4f4ec4175ce` chars 10667–11143 · hash `09f3c3638c60eeec22566369ef433f2115e9129d79ba3f009561c626dea03d0e`

```
**2. Have the model propose options before building.** This breaks the default and gives users control. If you previously relied on `temperature` for design variety, use this approach; it produces meaningfully different directions across runs. Example prompt:

```text wrap
Before building, propose 4 distinct visual directions tailored to this brief (each as: bg hex / accent hex / typeface — one-line rationale). Ask the user to pick one, then implement only that direction.
```

<details><summary>Context before</summary>

```
tter spacing than usual, especially in headings and navigation, so the text feels more engineered and less compressed. Headline text can be large and uppercase, while supporting copy remains short and sparse. The sub texts should be written with Alumni Sans SC in 4-6px like tiny little texts on corners bottom centre like that.

For the structure, start with a hero section containing a strong product statement, one short supporting paragraph, and a clean product placeholder or packshot frame. Below that, add a benefit grid with three or four blocks, then a formulation or ingredients section, and finally a cta.

Buttons should be flat and precise, with subtle hover changes using transition: all 160ms ease out where brightness and border contrast shift slightly rather than using dramatic motion.

Color palette should stay within this range:
#E9ECEC, #C9D2D4, #8C9A9E, #44545B, #11171B.
```


```

</details>

<details><summary>Context after</summary>

```

```

Additionally, Claude Opus 4.8 requires less frontend design prompting than previous models to avoid generic patterns that users call the "AI slop" aesthetic. With earlier models, Anthropic recommended a lengthier prompt snippet in the [frontend-design skill](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md). However, Claude Opus 4.8 generates distinctive, creative frontends with more minimal prompting guidance. This prompt snippet works well with the preceding prompting advice for variety:

```text wrap
<frontend_aesthetics>
NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white or dark backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character. Use 
```

</details>

<details><summary>Repair history (old question / old span)</summary>

**Old question.** What happens if you previously relied on `temperature` for design variety?

**Old answer.** Use this approach; it produces meaningfully different directions across runs.

**Old evidence** — `ver_997f51c850a46243a541d4f4ec4175ce` 10771–10910 · `7c2fd69c00251dc123c3e60ad91560edb0c223b0bc9b752fea3a71656310c284`

```
If you previously relied on `temperature` for design variety, use this approach; it produces meaningfully different directions across runs.
```

</details>

---

## V2D-44

- **provider**: openai
- **document**: Usage
- **section**: Usage › Preserving provider usage payloads
- **source span**: `ver_f8002fe268b970eaea8d640f9dd91fb3` chars 4145–4269
- **evidence kind**: `short_normative`
- **reasoning type**: `exact_lookup`
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **round-1 verdict**: FIX_REQUIRED
- **span expanded this round**: false

**Repaired question** (a suggestion, not gold)

> What setting should you add when a streaming Chat Completions provider requires an explicit usage request?

**Repaired answer**: `ModelSettings(include_usage=True)`.

**Repaired atomic claims**:

1. When a streaming Chat Completions provider requires an explicit usage request, also set `ModelSettings(include_usage=True)`.

**Critical strings**: include_usage

**What changed.** Rewrote the malformed question to ask what setting to add when a streaming Chat Completions provider requires an explicit usage request. Span unchanged.

**Round-1 ChatGPT reason.** The include_usage requirement is supported, but the proposed question is grammatically malformed. Rewrite it to ask what setting to add when a streaming Chat Completions provider requires an explicit usage request.

### Evidence E1 (verbatim, authoritative)

`ver_f8002fe268b970eaea8d640f9dd91fb3` chars 4145–4269 · hash `aa1600091e56a6fb15309b79c17b992e67cc4085d7646a6efee636dcd1233185`

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

<details><summary>Repair history (old question / old span)</summary>

**Old question.** What does When a streaming Chat Completions provider require?

**Old answer.** When a streaming Chat Completions provider requires an explicit usage request, also set `ModelSettings(include_usage=True)`.

**Old evidence** — `ver_f8002fe268b970eaea8d640f9dd91fb3` 4145–4269 · `aa1600091e56a6fb15309b79c17b992e67cc4085d7646a6efee636dcd1233185`

```
When a streaming Chat Completions provider requires an explicit usage request, also set `ModelSettings(include_usage=True)`.
```

</details>

---

## V2D-50

- **provider**: openai
- **document**: Models
- **section**: Models › OpenAI models › Default model › GPT-5 models
- **source span**: `ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 2486–3375
- **evidence kind**: `short_normative`
- **reasoning type**: `configuration_interaction`
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **round-1 verdict**: FIX_REQUIRED
- **span expanded this round**: true

**Repaired question** (a suggestion, not gold)

> What happens when you use any GPT-5 model such as `gpt-5.6-sol` as the default model via `OPENAI_DEFAULT_MODEL` or `RunConfig`?

**Repaired answer**: The SDK applies default `ModelSettings`.

**Repaired atomic claims**:

1. When you use any GPT-5 model such as `gpt-5.6-sol` as the default model via `OPENAI_DEFAULT_MODEL` or `RunConfig`, the SDK applies default `ModelSettings`.

**Critical strings**: gpt-5.6-sol, OPENAI_DEFAULT_MODEL, RunConfig, ModelSettings

**What changed.** Replaced 'in this way' with the explicit default-model / `RunConfig` configuration path. Expanded the evidence boundary backwards to that path.

**Round-1 ChatGPT reason.** The claim is supported in its section, but 'in this way' is not self-contained and depends on the preceding default-model/RunConfig setup. Rewrite the question to state the configuration path explicitly.

### Evidence E1 (verbatim, authoritative)

`ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 2486–3375 · hash `3e90577101dbe3584f6f6f92526744d5e3647d579b627f00d30006d04cd7db81`

```
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

When you use any GPT-5 model such as `gpt-5.6-sol` in this way, the SDK applies default `ModelSettings`.
```

<details><summary>Context before</summary>

```
 OpenAI Responses path | [Advanced OpenAI Responses settings](#advanced-openai-responses-settings) |
| Use a third-party adapter for non-OpenAI or mixed-provider routing | Compare the supported beta adapters and validate the provider path you plan to ship | [Third-party adapters](#third-party-adapters) |

## OpenAI models

For most OpenAI-only apps, the recommended path is to use string model names with the default OpenAI provider and stay on the Responses model path.

When an [`Agent`][agents.agent.Agent] does not specify a model, the Agents SDK uses [`gpt-5.6-luna`](https://developers.openai.com/api/docs/models/gpt-5.6-luna) with `reasoning.effort="none"` and `verbosity="low"` by default for cost-sensitive, high-volume agent workflows. Applications that need frontier capability can explicitly set `model="gpt-5.6-sol"` and choose `model_settings` that are appropriate for the workload.


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

<details><summary>Repair history (old question / old span)</summary>

**Old question.** What happens when you use any GPT-5 model such as `gpt-5.6-sol` in this way?

**Old answer.** The SDK applies default `ModelSettings`.

**Old evidence** — `ver_ae909bf8b4bbbe1d1a11119447f7ac94` 3271–3375 · `90191bc8cb47183770e60952c57e4dd9b388d30ff0fdebb418a7942a8a17ba2b`

```
When you use any GPT-5 model such as `gpt-5.6-sol` in this way, the SDK applies default `ModelSettings`.
```

</details>

---
