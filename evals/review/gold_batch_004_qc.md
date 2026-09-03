# GOLD-001 — batch 004 owner QC packet

**15 candidates · corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · prepared 2026-08-21T16:40:08Z**

Nothing in this packet is gold and nothing is verified. Every candidate is `candidate_unverified`, and no script in this repository can change that: `human_verified` exists only where the project owner records an approval.

## What the three states mean

| state | who decides | what it means |
| --- | --- | --- |
| `precheck_holdout_ready` | a script | the record is structurally capable — hashes match, critical strings are inside their own spans, no critical anaphora, no oversized anchor |
| `human_verified` | the project owner | a person read the evidence and approved the case |
| `holdout_eligible` | derived | `human_verified` **and** deterministic claim support **and** valid evidence **and** no unresolved blocker |

15 of 15 candidates are `precheck_holdout_ready`. That is not an argument for approving them: the internal review below recommends one for rejection and repaired ten, and every one of those was precheck-ready before the review looked at it. A structural check cannot see that a question is broader than its evidence or that a rule applies only on one API surface.

## Internal review outcome

| status | candidates |
| --- | --- |
| NEEDS_REPAIR | 10 |
| READY_FOR_OWNER_REVIEW | 4 |
| REJECT_RECOMMENDED | 1 |

The review was done by the authoring model against the frozen evidence. It is an internal check, not a second opinion from an independent party, and it is certainly not verification. Where it repaired a candidate the original text and the original anchor are both preserved, so a disagreement is checkable.

| id | provider | reasoning type | shape | internal status | repaired |
| --- | --- | --- | --- | --- | --- |
| `01` | anthropic | `error_behavior` | single_span | NEEDS_REPAIR | yes |
| `02` | anthropic | `configuration_interaction` | single_span | READY_FOR_OWNER_REVIEW | no |
| `03` | anthropic | `error_behavior` | single_span | READY_FOR_OWNER_REVIEW | no |
| `04` | anthropic | `error_behavior` | single_span | NEEDS_REPAIR | yes |
| `05` | anthropic | `error_behavior` | single_span | READY_FOR_OWNER_REVIEW | no |
| `06` | anthropic | `exact_lookup` | single_span | NEEDS_REPAIR | yes |
| `07` | anthropic | `lifecycle_compatibility_migration` | single_span | NEEDS_REPAIR | yes |
| `08` | openai | `ambiguity_disambiguation` | multi_span | REJECT_RECOMMENDED | no |
| `09` | openai | `ambiguity_disambiguation` | multi_span | NEEDS_REPAIR | yes |
| `10` | openai | `configuration_interaction` | single_span | NEEDS_REPAIR | yes |
| `11` | openai | `error_behavior` | single_span | NEEDS_REPAIR | yes |
| `12` | openai | `configuration_interaction` | single_span | READY_FOR_OWNER_REVIEW | no |
| `13` | openai | `exact_lookup` | single_span | NEEDS_REPAIR | yes |
| `14` | openai | `exact_lookup` | multi_span | NEEDS_REPAIR | yes |
| `15` | openai | `genuine_multi_hop` | multi_document | NEEDS_REPAIR | yes |

---

## GOLD-B004-01

- **provider**: anthropic
- **document**: Stop reasons and fallback
- **section**: Best practices for handling stop reasons › Implement retry logic for pause\_turn
- **reasoning type**: `error_behavior` (generated as `configuration_interaction`)
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

When using server tools, what does the API return if the server-side sampling loop reaches its iteration limit?

### Final answer

The API may return `pause_turn`.

### Final atomic claims

1. When using [server tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/server-tools), the API may return `pause_turn` if the server-side sampling loop reaches its iteration limit (default 10).

### Exact evidence

**E1** · `ver_4d14aec24504f4b8f6f28938b84587dc` 80272–80481 (209 chars) · Best practices for handling stop reasons › Implement retry logic for pause\_turn

```
When using [server tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/server-tools), the API may return `pause_turn` if the server-side sampling loop reaches its iteration limit (default 10).
```
**critical strings**: `pause_turn`
**evidence_hash**: `b13da047087150f9eefa746b904f26b9fc06d87cbc58b912916dd6eba0a74231`

### Claim → evidence

1. When using [server tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/se… → `E1`

### Internal review

- QUESTION_SCOPE: 'What happens when using server tools?' is far broader than its evidence. The span answers one conditional fact — what the API may return when the server-side sampling loop reaches its iteration limit — and a reader could give a dozen true answers to the question as asked.
- CATEGORY: the source states one direct conditional fact, not an interaction between two settings. §8 says relabel rather than inflate reasoning complexity.

### Repairs made

- **question rewritten** (question_scope_completion; taxonomy correction to a named stop behaviour)
  - was: What happens when using server tools?
  - now: When using server tools, what does the API return if the server-side sampling loop reaches its iteration limit?
- **answer rewritten** (question_scope_completion; taxonomy correction to a named stop behaviour)
  - was: The API may return `pause_turn` if the server-side sampling loop reaches its iteration limit (default 10).
  - now: The API may return `pause_turn`.
- **reasoning_type rewritten** (question_scope_completion; taxonomy correction to a named stop behaviour)
  - was: configuration_interaction
  - now: error_behavior

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `b13da047087150f9eefa746b904f26b9fc06d87cbc58b912916dd6eba0a74231`.

---

## GOLD-B004-02

- **provider**: anthropic
- **document**: Web search tool
- **section**: Response › `pause_turn` stop reason
- **reasoning type**: `configuration_interaction`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **READY_FOR_OWNER_REVIEW**
- **precheck**: holdout-ready = True

### Final question

What happens if Claude calls web search and one of your client tools in the same group of parallel tool calls?

### Final answer

The API returns `stop_reason: "tool_use"` instead and does not run the search yet.

### Final atomic claims

1. If Claude calls web search and one of your client tools in the same group of parallel tool calls, the API returns `stop_reason: "tool_use"` instead and does not run the search yet.

### Exact evidence

**E1** · `ver_53da2f78e855c75ec755089c13d44c28` 22695–22875 (180 chars) · Response › `pause_turn` stop reason

```
If Claude calls web search and one of your client tools in the same group of parallel tool calls, the API returns `stop_reason: "tool_use"` instead and does not run the search yet.
```
**critical strings**: `stop_reason`, `tool_use`
**evidence_hash**: `0f83094654abd858b9e46cff62a781ffc8b0bb12c679beb91ed3498045109e06`

### Claim → evidence

1. If Claude calls web search and one of your client tools in the same group of parallel tool… → `E1`

### Internal review

- NONCRITICAL_ANAPHORA: the span says the API returns tool_use 'instead', and what it is instead of — the pause_turn behaviour — sits in the preceding paragraph, outside the span. The fact is answerable without resolving it, so this is noncritical, but §2B requires an explicit human override rather than a silent pass.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

---

## GOLD-B004-03

- **provider**: anthropic
- **document**: Claude API errors
- **section**: Common validation errors › Thinking blocks cannot be modified
- **reasoning type**: `error_behavior`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **READY_FOR_OWNER_REVIEW**
- **precheck**: holdout-ready = True

### Final question

What happens if the most recent assistant message contains `thinking` or `redacted_thinking` blocks that were edited, reordered, filtered out, or reconstructed before being sent back to the API?

### Final answer

The request returns a 400 `invalid_request_error`.

### Final atomic claims

1. If the most recent assistant message contains `thinking` or `redacted_thinking` blocks that were edited, reordered, filtered out, or reconstructed before being sent back to the API, the request returns a 400 `invalid_request_error`.

### Exact evidence

**E1** · `ver_0774ca0093ff4a846753577c9a4a39d5` 19838–20070 (232 chars) · Common validation errors › Thinking blocks cannot be modified

```
If the most recent assistant message contains `thinking` or `redacted_thinking` blocks that were edited, reordered, filtered out, or reconstructed before being sent back to the API, the request returns a 400 `invalid_request_error`.
```
**critical strings**: `thinking`, `redacted_thinking`, `invalid_request_error`
**evidence_hash**: `1f1dbc851bb4029f1d827d1c11462573659eaa43a6e23acae8e9b1e0a916cdff`

### Claim → evidence

1. If the most recent assistant message contains `thinking` or `redacted_thinking` blocks tha… → `E1`

### Internal review

- No finding. The candidate is as generated.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

---

## GOLD-B004-04

- **provider**: anthropic
- **document**: Thinking
- **section**: Thinking and the context window
- **reasoning type**: `error_behavior`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

On Claude 4.5 models and newer, if input tokens plus `max_tokens` exceed the context window size, what happens when generation reaches the context window limit?

### Final answer

The API accepts the request, and generation stops with `stop_reason: "model_context_window_exceeded"` instead of returning an error.

### Final atomic claims

1. On Claude 4.5 models and newer, if input tokens plus `max_tokens` exceeds the context window size, the API accepts the request.
2. If generation then reaches the context window limit, it stops with `stop_reason: "model_context_window_exceeded"` instead of returning an error.

### Exact evidence

**E1** · `ver_012b734775e7edb2649d3a9ddfd93070` 47953–48225 (272 chars) · Thinking and the context window

```
On Claude 4.5 models and newer, if input tokens plus `max_tokens` exceeds the context window size, the API accepts the request. If generation then reaches the context window limit, it stops with `stop_reason: "model_context_window_exceeded"` instead of returning an error.
```
**critical strings**: `Claude 4.5 models and newer`, `max_tokens`, `stop_reason`, `model_context_window_exceeded`
**evidence_hash**: `8eb88b1c77cc0a04bd7ffe36232db6fb450a7bf9b650087984be147984df7753`

### Claim → evidence

1. On Claude 4.5 models and newer, if input tokens plus `max_tokens` exceeds the context wind… → `E1`
2. If generation then reaches the context window limit, it stops with `stop_reason: "model_co… → `E1`

### Internal review

- CRITICAL_ANAPHORA: 'If generation then reaches the context window limit' — 'then' refers to the preceding sentence, which is outside the span.
- MODEL_SCOPE: the antecedent is 'On Claude 4.5 models and newer, if input tokens plus max_tokens exceeds the context window size, the API accepts the request.' The very next sentence in the source says earlier models return a validation error instead, so the claim as anchored over-generalises across models.

### Repairs made

- **E1 anchor extended** (evidence_boundary_completion)
  - was 48081–48225, hash `13f22cd01eeaeaad…`
  - now 47953–48225, hash `8eb88b1c77cc0a04…`
- **question rewritten** (evidence_boundary_completion; the antecedent of 'then' also carries the model scope)
  - was: What happens if generation then reaches the context window limit?
  - now: On Claude 4.5 models and newer, if input tokens plus `max_tokens` exceed the context window size, what happens when generation reaches the context window limit?
- **answer rewritten** (evidence_boundary_completion; the antecedent of 'then' also carries the model scope)
  - was: It stops with `stop_reason: "model_context_window_exceeded"` instead of returning an error.
  - now: The API accepts the request, and generation stops with `stop_reason: "model_context_window_exceeded"` instead of returning an error.
- **atomic_claims rewritten** (evidence_boundary_completion; the antecedent of 'then' also carries the model scope)
  - was: ['If generation then reaches the context window limit, it stops with `stop_reason: "model_context_window_exceeded"` instead of returning an error.']
  - now: ['On Claude 4.5 models and newer, if input tokens plus `max_tokens` exceeds the context window size, the API accepts the request.', 'If generation then reaches the context window limit, it stops with `stop_reason: "model_context_window_exceeded"` instead of returning an error.']

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `8eb88b1c77cc0a04bd7ffe36232db6fb450a7bf9b650087984be147984df7753`.

---

## GOLD-B004-05

- **provider**: anthropic
- **document**: Web search tool
- **section**: Tool definition › Max uses
- **reasoning type**: `error_behavior`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **READY_FOR_OWNER_REVIEW**
- **precheck**: holdout-ready = True

### Final question

What happens if Claude attempts more searches than allowed?

### Final answer

The `web_search_tool_result` is an error with the `max_uses_exceeded` error code.

### Final atomic claims

1. If Claude attempts more searches than allowed, the `web_search_tool_result` is an error with the `max_uses_exceeded` error code.

### Exact evidence

**E1** · `ver_53da2f78e855c75ec755089c13d44c28` 15475–15603 (128 chars) · Tool definition › Max uses

```
If Claude attempts more searches than allowed, the `web_search_tool_result` is an error with the `max_uses_exceeded` error code.
```
**critical strings**: `web_search_tool_result`, `max_uses_exceeded`
**evidence_hash**: `9d881c94127cc6d29cf87e6cce6611ee77ac7b4fdbfb19477653a4f5b0a8fa08`

### Claim → evidence

1. If Claude attempts more searches than allowed, the `web_search_tool_result` is an error wi… → `E1`

### Internal review

- NONCRITICAL_DEPENDENCY: 'more searches than allowed' does not name the parameter that sets the limit (`max_uses`), which is defined in the preceding sentence. The question is answerable without it, so the anchor stands; an owner who wants the parameter named should choose NEEDS_EDIT and the span can be extended backwards by 60 characters.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

---

## GOLD-B004-06

- **provider**: anthropic
- **document**: Web search tool
- **section**: Tool definition › Localization
- **reasoning type**: `exact_lookup`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

Within the `user_location` parameter, what value does the `timezone` field take?

### Final answer

The IANA timezone ID.

### Final atomic claims

1. The `user_location` parameter allows you to localize search results based on a user's location.
2. `timezone`: The [IANA timezone ID](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

### Exact evidence

**E1** · `ver_53da2f78e855c75ec755089c13d44c28` 16295–16843 (548 chars) · Tool definition › Localization

```
The `user_location` parameter allows you to localize search results based on a user's location. Provide at least one of `city`, `region`, `country`, or `timezone`.

* `type`: The type of location (must be `approximate`)
* `city`: The city name
* `region`: The region or state
* `country`: The two-letter [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country code. The API rejects unsupported country codes with a 400 error.
* `timezone`: The [IANA timezone ID](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
```
**critical strings**: `user_location`, `timezone`, `IANA timezone ID`
**evidence_hash**: `b38e23b266e3c424991cafafdc60be26959220d2a50a395e7ae813d5fba08c7c`

### Claim → evidence

1. The `user_location` parameter allows you to localize search results based on a user's loca… → `E1`
2. `timezone`: The [IANA timezone ID](https://en.wikipedia.org/wiki/List_of_tz_database_time_… → `E1`

### Internal review

- CLAIM_SCOPE: the span is a bare definition bullet. The parent that gives `timezone` its meaning — the `user_location` parameter — is in the section heading and the list stem, both outside the span. §2D forbids relying on a header outside the exact evidence.
- GENERIC_IDENTIFIER: 'What is the `timezone` option?' names an identifier that exists in many APIs (§6).
- CRITICAL_STRING: one critical string was a 60-character truncation of a markdown link — 'The [IANA timezone ID](https://en.wikipedia.org/wiki/List_of' — which is not a meaningful checkable string.

### Repairs made

- **E1 anchor extended** (evidence_scope_completion)
  - was 16744–16843, hash `0bd723f53fa5e63b…`
  - now 16295–16843, hash `b38e23b266e3c424…`
- **question rewritten** (evidence_scope_completion; the parent parameter must be inside the anchor, not in the heading)
  - was: What is the `timezone` option?
  - now: Within the `user_location` parameter, what value does the `timezone` field take?
- **answer rewritten** (evidence_scope_completion; the parent parameter must be inside the anchor, not in the heading)
  - was: The [IANA timezone ID](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
  - now: The IANA timezone ID.
- **atomic_claims rewritten** (evidence_scope_completion; the parent parameter must be inside the anchor, not in the heading)
  - was: ['`timezone`: The [IANA timezone ID](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).']
  - now: ["The `user_location` parameter allows you to localize search results based on a user's location.", '`timezone`: The [IANA timezone ID](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).']

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `b38e23b266e3c424991cafafdc60be26959220d2a50a395e7ae813d5fba08c7c`.

---

## GOLD-B004-07

- **provider**: anthropic
- **document**: Prompting best practices
- **section**: Thinking and reasoning › Overthinking and excessive thoroughness
- **reasoning type**: `lifecycle_compatibility_migration`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

If I need a hard ceiling on thinking costs, what is the support status of extended thinking with a `budget_tokens` cap on Opus 4.6 and Sonnet 4.6?

### Final answer

It is still functional but deprecated.

### Final atomic claims

1. If you need a hard ceiling on thinking costs, extended thinking with a `budget_tokens` cap is still functional on Opus 4.6 and Sonnet 4.6 but is deprecated.

### Exact evidence

**E1** · `ver_0a5b292d4854b92db0a9e025b4949123` 27270–27426 (156 chars) · Thinking and reasoning › Overthinking and excessive thoroughness

```
If you need a hard ceiling on thinking costs, extended thinking with a `budget_tokens` cap is still functional on Opus 4.6 and Sonnet 4.6 but is deprecated.
```
**critical strings**: `budget_tokens`, `Opus 4.6`, `deprecated`
**evidence_hash**: `6defce92772b6eefb4f7e6e8c08c6c7107cc017e934290819360eb5bfd38c874`

### Claim → evidence

1. If you need a hard ceiling on thinking costs, extended thinking with a `budget_tokens` cap… → `E1`

### Internal review

- QUESTION_FORM: 'What happens if you need a hard ceiling on thinking costs?' asks what happens when a person has a requirement, which is not a behaviour the documentation can answer. The evidence states a support status, so the question should ask for one.

### Repairs made

- **question rewritten** (question_form_correction)
  - was: What happens if you need a hard ceiling on thinking costs?
  - now: If I need a hard ceiling on thinking costs, what is the support status of extended thinking with a `budget_tokens` cap on Opus 4.6 and Sonnet 4.6?
- **answer rewritten** (question_form_correction)
  - was: Extended thinking with a `budget_tokens` cap is still functional on Opus 4.6 and Sonnet 4.6 but is deprecated.
  - now: It is still functional but deprecated.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `6defce92772b6eefb4f7e6e8c08c6c7107cc017e934290819360eb5bfd38c874`.

---

## GOLD-B004-08

- **provider**: openai
- **document**: Structured Outputs Parsing Helpers
- **section**: Streaming Helpers › Chat Completions API › Chat Completions Events › ContentDeltaEvent
- **reasoning type**: `ambiguity_disambiguation`
- **evidence shape**: `multi_span` · **requires all evidence**: True
- **internal review status**: **REJECT_RECOMMENDED**
- **precheck**: holdout-ready = True

### Final question

In a `ContentDeltaEvent`, what does the `type` field contain, and how does that differ from `ContentDoneEvent`?

### Final answer

In `ContentDeltaEvent`, `type` is: `"content.delta"`. In `ContentDoneEvent`, `type` is: `"content.done"`.

### Final atomic claims

1. In `ContentDeltaEvent`, `type` is: `"content.delta"`.
2. In `ContentDoneEvent`, `type` is: `"content.done"`.

### Exact evidence

**E1** · `ver_57e26a49b0a3714f3e90376d014d7f52` 5814–5841 (27 chars) · Streaming Helpers › Chat Completions API › Chat Completions Events › ContentDeltaEvent

```
- `type`: `"content.delta"`
```
**critical strings**: `type`, `` `"content.delta"` ``
**evidence_hash**: `9d90d13b5ef5041ad8d20a4c0acf1a56b5845947c2b74462a46d2700c7fa393d`

**E2** · `ver_57e26a49b0a3714f3e90376d014d7f52` 6134–6160 (26 chars) · Streaming Helpers › Chat Completions API › Chat Completions Events › ContentDoneEvent

```
- `type`: `"content.done"`
```
**critical strings**: `type`, `` `"content.done"` ``
**evidence_hash**: `c4e5d438b90d3496919b5293c18370f6d3ed060409e90fce345e3b8ac4a76b12`

### Claim → evidence

1. In `ContentDeltaEvent`, `type` is: `"content.delta"`. → `E1`
2. In `ContentDoneEvent`, `type` is: `"content.done"`. → `E2`

### Internal review

- NOT_AMBIGUITY: `type` on `ContentDeltaEvent` and `ContentDoneEvent` is a discriminator constant. A tagged union whose tag differs per member is not a case where a developer must select a scope to resolve a meaning — it is two literal lookups, and §7 says to relabel rather than keep the label to hit a category target.
- CLAIM_SCOPE: both spans are 27 and 26 characters and contain neither event-type name, so the question's scope lives entirely in headings outside the evidence (§2D). This part is repairable — expanding each span to its `#### EventName` heading costs only ~100 characters — but repairing the scope does not make the case a disambiguation.
- CEILING: relabelling to `exact_lookup` would take that category to 4 against the §5 maximum of 3.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

The review recommends rejecting this candidate. That recommendation is not a decision and does not bind you.

---

## GOLD-B004-09

- **provider**: openai
- **document**: Structured Outputs Parsing Helpers
- **section**: Streaming Helpers › Chat Completions API › Chat Completions Events › FunctionToolCallArgumentsDeltaEvent
- **reasoning type**: `ambiguity_disambiguation`
- **evidence shape**: `multi_span` · **requires all evidence**: True
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

In a `FunctionToolCallArgumentsDeltaEvent`, what does the `parsed_arguments` field contain, and how does that differ from `FunctionToolCallArgumentsDoneEvent`?

### Final answer

In `FunctionToolCallArgumentsDeltaEvent`, `parsed_arguments` is: The partially parsed arguments object. In `FunctionToolCallArgumentsDoneEvent`, `parsed_arguments` is: The fully parsed arguments object. If you used `openai.pydantic_function_tool()` this will be an instance of the given model.

### Final atomic claims

1. In `FunctionToolCallArgumentsDeltaEvent`, `parsed_arguments` is: The partially parsed arguments object.
2. In `FunctionToolCallArgumentsDoneEvent`, `parsed_arguments` is: The fully parsed arguments object. If you used `openai.pydantic_function_tool()` this will be an instance of the given model.

### Exact evidence

**E1** · `ver_57e26a49b0a3714f3e90376d014d7f52` 6627–6997 (370 chars) · Streaming Helpers › Chat Completions API › Chat Completions Events › FunctionToolCallArgumentsDeltaEvent

```
#### FunctionToolCallArgumentsDeltaEvent

Emitted when a chunk contains part of a function tool call's arguments.

- `type`: `"tool_calls.function.arguments.delta"`
- `name`: The name of the function being called
- `index`: The index of the tool call
- `arguments`: The accumulated raw JSON string of arguments
- `parsed_arguments`: The partially parsed arguments object
```
**critical strings**: `FunctionToolCallArgumentsDeltaEvent`, `parsed_arguments`, `The partially parsed arguments object`
**evidence_hash**: `53b4b866ce9f1066a9bbe80d16dacdd21318dd256b8564216256943b8adec57e`

**E2** · `ver_57e26a49b0a3714f3e90376d014d7f52` 7072–7509 (437 chars) · Streaming Helpers › Chat Completions API › Chat Completions Events › FunctionToolCallArgumentsDoneEvent

```
#### FunctionToolCallArgumentsDoneEvent

Emitted when a function tool call's arguments are complete.

- `type`: `"tool_calls.function.arguments.done"`
- `name`: The name of the function being called
- `index`: The index of the tool call
- `arguments`: The full raw JSON string of arguments
- `parsed_arguments`: The fully parsed arguments object. If you used `openai.pydantic_function_tool()` this will be an instance of the given model.
```
**critical strings**: `FunctionToolCallArgumentsDoneEvent`, `parsed_arguments`, `The fully parsed arguments object`
**evidence_hash**: `2c4842349ec2c5fd3374e46a6cd2378745ff41ad0f8ac74ce9b24f259dd8aa26`

### Claim → evidence

1. In `FunctionToolCallArgumentsDeltaEvent`, `parsed_arguments` is: The partially parsed argu… → `E1`
2. In `FunctionToolCallArgumentsDoneEvent`, `parsed_arguments` is: The fully parsed arguments… → `E2`

### Internal review

- AMBIGUITY_CONFIRMED: `parsed_arguments` genuinely means different things on the two events — a partially parsed object mid-stream, a fully parsed object (a pydantic model instance where `openai.pydantic_function_tool()` was used) when complete. A developer holding one event and reading the other's documentation would be wrong, which is the realistic confusion §11 asks for.
- CLAIM_SCOPE: as anchored, neither span contains its event-type name, so the scope the question names is in a heading outside the evidence (§2D).

### Repairs made

- **E1 anchor extended** (evidence_scope_completion)
  - was 6938–6997, hash `a3608232ce720258…`
  - now 6627–6997, hash `53b4b866ce9f1066…`
- **E2 anchor extended** (evidence_scope_completion)
  - was 7362–7509, hash `24e776c42e7a5e4c…`
  - now 7072–7509, hash `2c4842349ec2c5fd…`

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `53b4b866ce9f1066a9bbe80d16dacdd21318dd256b8564216256943b8adec57e` (and the other spans' hashes above).

---

## GOLD-B004-10

- **provider**: openai
- **document**: Realtime agents guide
- **section**: Realtime agents guide › Session lifecycle
- **reasoning type**: `configuration_interaction`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

`RealtimeRunner` uses `OpenAIRealtimeWebSocketModel` by default. What happens if I pass a different `RealtimeModel`?

### Final answer

The same session lifecycle and agent features still apply, while the connection mechanics can change.

### Final atomic claims

1. By default, `RealtimeRunner` uses `OpenAIRealtimeWebSocketModel`, so the default Python path is a server-side WebSocket connection to the Realtime API.
2. If you pass a different `RealtimeModel`, the same session lifecycle and agent features still apply, while the connection mechanics can change.

### Exact evidence

**E1** · `ver_14a2187cf2216b9d56c213b520a28479` 1827–2121 (294 chars) · Realtime agents guide › Session lifecycle

```
By default, `RealtimeRunner` uses `OpenAIRealtimeWebSocketModel`, so the default Python path is a server-side WebSocket connection to the Realtime API. If you pass a different `RealtimeModel`, the same session lifecycle and agent features still apply, while the connection mechanics can change.
```
**critical strings**: `RealtimeRunner`, `OpenAIRealtimeWebSocketModel`, `RealtimeModel`
**evidence_hash**: `352fcab03e4bb99e38aeb11550323d6e3efe49a101b144bd2ea2a2f28ac35d9d`

### Claim → evidence

1. By default, `RealtimeRunner` uses `OpenAIRealtimeWebSocketModel`, so the default Python pa… → `E1`
2. If you pass a different `RealtimeModel`, the same session lifecycle and agent features sti… → `E1`

### Internal review

- COMPARATIVE_ANAPHORA: 'a different `RealtimeModel`' is different from a default the span does not name. The default — `OpenAIRealtimeWebSocketModel` — is established in the preceding sentence, outside the anchor.
- CATEGORY: with the default inside the anchor this is a real configuration interaction (which transport model is used changes connection mechanics while leaving the session lifecycle alone), so the label stands once the scope does.

### Repairs made

- **E1 anchor extended** (evidence_boundary_completion)
  - was 1979–2121, hash `ad1950090760f8b3…`
  - now 1827–2121, hash `352fcab03e4bb99e…`
- **question rewritten** (evidence_boundary_completion; 'a different model' needs the default it differs from)
  - was: What happens if you pass a different `RealtimeModel`?
  - now: `RealtimeRunner` uses `OpenAIRealtimeWebSocketModel` by default. What happens if I pass a different `RealtimeModel`?
- **atomic_claims rewritten** (evidence_boundary_completion; 'a different model' needs the default it differs from)
  - was: ['If you pass a different `RealtimeModel`, the same session lifecycle and agent features still apply, while the connection mechanics can change.']
  - now: ['By default, `RealtimeRunner` uses `OpenAIRealtimeWebSocketModel`, so the default Python path is a server-side WebSocket connection to the Realtime API.', 'If you pass a different `RealtimeModel`, the same session lifecycle and agent features still apply, while the connection mechanics can change.']

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `352fcab03e4bb99e38aeb11550323d6e3efe49a101b144bd2ea2a2f28ac35d9d`.

---

## GOLD-B004-11

- **provider**: openai
- **document**: Streaming
- **section**: Streaming › Streaming and approvals
- **reasoning type**: `error_behavior` (generated as `configuration_interaction`)
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

In a streamed run, what happens if a tool requires approval?

### Final answer

`result.stream_events()` finishes and pending approvals are exposed in `RunResultStreaming.interruptions`.

### Final atomic claims

1. If a tool requires approval, `result.stream_events()` finishes and pending approvals are exposed in [`RunResultStreaming.interruptions`][agents.result.RunResultStreaming.interruptions].

### Exact evidence

**E1** · `ver_12004469f7a5592cd1e6cab936117fce` 2472–2657 (185 chars) · Streaming › Streaming and approvals

```
If a tool requires approval, `result.stream_events()` finishes and pending approvals are exposed in [`RunResultStreaming.interruptions`][agents.result.RunResultStreaming.interruptions].
```
**critical strings**: `stream_events`, `RunResultStreaming.interruptions`
**evidence_hash**: `fd6ec23ac1830d0625b7509d4ef3572a6ec90090565db15c3d8402acbc147908`

### Claim → evidence

1. If a tool requires approval, `result.stream_events()` finishes and pending approvals are e… → `E1`

### Internal review

- QUESTION_SCOPE: 'What happens if a tool requires approval?' is generic across SDKs and run modes. The evidence is about a streamed run — it names `result.stream_events()` — so the question can carry that scope without adding anything the span does not say.
- CATEGORY: one direct conditional fact about run behaviour, not an interaction between two settings (§8).

### Repairs made

- **question rewritten** (question_scope_completion; taxonomy correction to a named stop behaviour)
  - was: What happens if a tool requires approval?
  - now: In a streamed run, what happens if a tool requires approval?
- **reasoning_type rewritten** (question_scope_completion; taxonomy correction to a named stop behaviour)
  - was: configuration_interaction
  - now: error_behavior

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `fd6ec23ac1830d0625b7509d4ef3572a6ec90090565db15c3d8402acbc147908`.

---

## GOLD-B004-12

- **provider**: openai
- **document**: Streaming
- **section**: Streaming › Cancel streaming after the current turn
- **reasoning type**: `configuration_interaction`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **READY_FOR_OWNER_REVIEW**
- **precheck**: holdout-ready = True

### Final question

What happens if you are manually continuing from `result.to_input_list(mode="normalized")`, and `cancel(mode="after_turn")` stops after a tool turn?

### Final answer

Rerun `result.last_agent` with that normalized input to continue the unfinished existing user turn instead of appending a fresh user turn right away.

### Final atomic claims

1. If you are manually continuing from [`result.to_input_list(mode="normalized")`][agents.result.RunResultBase.to_input_list], and `cancel(mode="after_turn")` stops after a tool turn, rerun `result.last_agent` with that normalized input to continue the unfinished existing user turn instead of appending a fresh user turn right away.

### Exact evidence

**E1** · `ver_12004469f7a5592cd1e6cab936117fce` 3845–4175 (330 chars) · Streaming › Cancel streaming after the current turn

```
If you are manually continuing from [`result.to_input_list(mode="normalized")`][agents.result.RunResultBase.to_input_list], and `cancel(mode="after_turn")` stops after a tool turn, rerun `result.last_agent` with that normalized input to continue the unfinished existing user turn instead of appending a fresh user turn right away.
```
**critical strings**: `to_input_list`, `after_turn`, `result.last_agent`
**evidence_hash**: `cfb7414fc8aeb9482635a45eede6ce305286f8df5f58cf54cc0818e14e954232`

### Claim → evidence

1. If you are manually continuing from [`result.to_input_list(mode="normalized")`][agents.res… → `E1`

### Internal review

- The question is long, because the source's condition has two parts and both matter. Shortening it would drop a condition the answer depends on, so it stands as written.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

---

## GOLD-B004-13

- **provider**: openai
- **document**: Handoffs
- **section**: (1)! › Customizing handoffs via the `handoff()` function
- **reasoning type**: `exact_lookup`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

For a handoff, what does the `input_type` option specify?

### Final answer

The schema for the handoff tool-call arguments. When set, the parsed payload is passed to `on_handoff`.

### Final atomic claims

1. `input_type`: The schema for the handoff tool-call arguments. When set, the parsed payload is passed to `on_handoff`.

### Exact evidence

**E1** · `ver_1c77f33b04ffffa285ea7e61c2a89653` 2332–2453 (121 chars) · (1)! › Customizing handoffs via the `handoff()` function

```
-   `input_type`: The schema for the handoff tool-call arguments. When set, the parsed payload is passed to `on_handoff`.
```
**critical strings**: `input_type`, `The schema for the handoff tool-call arguments`, `on_handoff`
**evidence_hash**: `3b8a83ecd785ac37429a82c6060abc61a4f6d4ac14a89586830b25a4ec75f25e`

### Claim → evidence

1. `input_type`: The schema for the handoff tool-call arguments. When set, the parsed payload… → `E1`

### Internal review

- GENERIC_IDENTIFIER: 'What is the `input_type` option?' does not say what it is an option of (§6). Unlike B004-06 and B004-14 the span itself says 'the handoff tool-call arguments', so the scope can be added to the question without touching the evidence.
- CRITICAL_STRING: one critical string was a 60-character truncation — 'The schema for the handoff tool-call arguments. When set, th'.

### Repairs made

- **question rewritten** (question_scope_completion; critical string repaired to a whole phrase)
  - was: What is the `input_type` option?
  - now: For a handoff, what does the `input_type` option specify?

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `3b8a83ecd785ac37429a82c6060abc61a4f6d4ac14a89586830b25a4ec75f25e`.

---

## GOLD-B004-14

- **provider**: openai
- **document**: Handoffs
- **section**: (1)! › Customizing handoffs via the `handoff()` function
- **reasoning type**: `exact_lookup`
- **evidence shape**: `multi_span` · **requires all evidence**: True
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

In the `handoff()` function, what does the `input_filter` option do?

### Final answer

It filters the input received by the next agent.

### Final atomic claims

1. The [`handoff()`][agents.handoffs.handoff] function lets you customize things.
2. `input_filter`: This lets you filter the input received by the next agent.

### Exact evidence

**E1** · `ver_1c77f33b04ffffa285ea7e61c2a89653` 1576–1654 (78 chars) · (1)! › Customizing handoffs via the `handoff()` function

```
The [`handoff()`][agents.handoffs.handoff] function lets you customize things.
```
**critical strings**: `handoff()`
**evidence_hash**: `6ed28e39bdd7b060856374798eb975198a88cf4e9866ee4f8ccd25450138caba`

**E2** · `ver_1c77f33b04ffffa285ea7e61c2a89653` 2454–2552 (98 chars) · (1)! › Customizing handoffs via the `handoff()` function

```
-   `input_filter`: This lets you filter the input received by the next agent. See below for more.
```
**critical strings**: `input_filter`, `This lets you filter the input received by the next agent`
**evidence_hash**: `1c50ad6eeed23afe1fd9cb3c931d490f140d744f683d5f95de266846dae0364a`

### Claim → evidence

1. The [`handoff()`][agents.handoffs.handoff] function lets you customize things. → `E1`
2. `input_filter`: This lets you filter the input received by the next agent. → `E2`

### Internal review

- CLAIM_SCOPE: the span reads '`input_filter`: This lets you filter the input received by the next agent.' and contains no mention of handoffs. The scope is entirely in the section heading and the list stem, both outside the evidence (§2D).
- REPAIR_SHAPE: a contiguous expansion back to the list stem would swallow five unrelated field definitions and produce a 976-character anchor. §16 asks for precise spans, so the stem is added as its own span instead.

### Repairs made

- **E0 scope span added** (evidence_scope_completion)
  - 1576–1654, hash `6ed28e39bdd7b060…`
- **question rewritten** (evidence_scope_completion; the stem naming handoff() is added as a second precise span)
  - was: What is the `input_filter` option?
  - now: In the `handoff()` function, what does the `input_filter` option do?
- **answer rewritten** (evidence_scope_completion; the stem naming handoff() is added as a second precise span)
  - was: This lets you filter the input received by the next agent.
  - now: It filters the input received by the next agent.
- **atomic_claims rewritten** (evidence_scope_completion; the stem naming handoff() is added as a second precise span)
  - was: ['`input_filter`: This lets you filter the input received by the next agent.']
  - now: ['The [`handoff()`][agents.handoffs.handoff] function lets you customize things.', '`input_filter`: This lets you filter the input received by the next agent.']

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `6ed28e39bdd7b060856374798eb975198a88cf4e9866ee4f8ccd25450138caba` (and the other spans' hashes above).

---

## GOLD-B004-15

- **provider**: openai
- **document**: Human-in-the-loop
- **section**: Human-in-the-loop › Marking tools that need approval
- **reasoning type**: `genuine_multi_hop`
- **evidence shape**: `multi_document` · **requires all evidence**: True
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

If I set `needs_approval` to `True` on a function tool used with hosted agents, what happens?

### Final answer

The tool requires approval, but SDK tool-approval interruptions are not supported there, so a function tool whose `needs_approval` is not `False` is rejected before the request is sent.

### Final atomic claims

1. Set `needs_approval` to `True` to always require approval or provide an async function that decides per call.
2. SDK tool approval interruptions are not supported: any function tool whose `needs_approval` setting is not `False` is rejected before the request is sent.

**Composed claim.** For hosted agents, a function tool with `needs_approval` set to `True` has a value that is not `False`, so it is rejected before the request is sent rather than pausing for approval.

### Exact evidence

**E1** · `ver_ae3bfcc42c733c5051abda30f0f6db07` 1327–1436 (109 chars) · Human-in-the-loop › Marking tools that need approval

```
Set `needs_approval` to `True` to always require approval or provide an async function that decides per call.
```
**critical strings**: `needs_approval`, `True`
**evidence_hash**: `72cb1e104a68797ed1296cfed17b04ba519cd1890449a2e5542f4ed36ad4e836`

**E2** · `ver_ae909bf8b4bbbe1d1a11119447f7ac94` 16313–16910 (597 chars) · Models › OpenAI models › Hosted multi-agent (experimental) › Local function tools

```
All hosted agents share the model and tools configured for the request. The Responses API decides which hosted agent calls a function. The normal SDK Runner executes the function locally and injects a `function_call_output` with the same call ID into the active WebSocket response, which lets the service resume the original hosted caller. Function execution still passes through the Runner's normal guardrails, hooks, and failure conversion. SDK tool approval interruptions are not supported: any function tool whose `needs_approval` setting is not `False` is rejected before the request is sent.
```
**critical strings**: `hosted agents`, `needs_approval`, `False`
**evidence_hash**: `b0ef211a15b2f158ac09382986237d5050567eaf25439c000f7fc76a3415bafd`

### Claim → evidence

1. Set `needs_approval` to `True` to always require approval or provide an async function tha… → `E1`
2. SDK tool approval interruptions are not supported: any function tool whose `needs_approval… → `E2`

### Internal review

- UNSUPPORTED_GENERALIZATION: span 2 comes from 'Models > OpenAI models > Hosted multi-agent (experimental) > Local function tools'. Its rejection rule holds on that surface, not in the ordinary Runner flow, where `needs_approval = True` correctly pauses for approval. The question as written is unqualified, so the composed answer is false in the default path.
- SCOPE_IN_HEADING: the qualification lives in the section heading, which §2D forbids relying on. It has to be inside the anchor or the case cannot carry it.
- MULTI_HOP_STANDS: with the scope inside span 2 the chain is real — see the semantic review in the internal review document.
- CLAIM_SET: the scope sentence 'All hosted agents share the model and tools configured for the request.' is inside the repaired span but is deliberately NOT an atomic claim. Quoting it would put 'the model' — whose antecedent is outside the span — into scored text, which turns a noncritical anaphora into a critical one. The span establishes the hosted-agent scope; the claims do not need to restate it.

### Repairs made

- **E2 anchor extended** (evidence_scope_completion)
  - was 16756–16910, hash `2f49ae6be39cdc33…`
  - now 16313–16910, hash `b0ef211a15b2f158…`
- **question rewritten** (evidence_scope_completion; the composed claim holds only on the hosted-agent surface and must say so)
  - was: If I set `needs_approval` to `True`, what happens?
  - now: If I set `needs_approval` to `True` on a function tool used with hosted agents, what happens?
- **answer rewritten** (evidence_scope_completion; the composed claim holds only on the hosted-agent surface and must say so)
  - was: Set `needs_approval` to `True` to always require approval or provide an async function that decides per call. SDK tool approval interruptions are not supported: any function tool whose `needs_approval` setting is not `False` is rejected before the request is sent.
  - now: The tool requires approval, but SDK tool-approval interruptions are not supported there, so a function tool whose `needs_approval` is not `False` is rejected before the request is sent.
- **composed_claim rewritten** (evidence_scope_completion; the composed claim holds only on the hosted-agent surface and must say so)
  - was: For `needs_approval`: Set `needs_approval` to `True` to always require approval or provide an async function that decides per call. Consequently, SDK tool approval interruptions are not supported: any function tool whose `needs_approval` setting is not `False` is rejected before the request is sent.
  - now: For hosted agents, a function tool with `needs_approval` set to `True` has a value that is not `False`, so it is rejected before the request is sent rather than pausing for approval.
- **composed_answer rewritten** (evidence_scope_completion; the composed claim holds only on the hosted-agent surface and must say so)
  - was: For `needs_approval`: Set `needs_approval` to `True` to always require approval or provide an async function that decides per call. Consequently, SDK tool approval interruptions are not supported: any function tool whose `needs_approval` setting is not `False` is rejected before the request is sent.
  - now: For hosted agents, a function tool with `needs_approval` set to `True` has a value that is not `False`, so it is rejected before the request is sent rather than pausing for approval.
- **bridge_relationship rewritten** (evidence_scope_completion; the composed claim holds only on the hosted-agent surface and must say so)
  - was: span 1 states a requirement or constraint on the bridge entity; span 2 states the behaviour that follows
  - now: Span 1 sets `needs_approval` to `True`; span 2 makes rejection conditional on `needs_approval` not being `False`. The chain runs through the value: `True` is not `False`, so the tool span 1 configures is the tool span 2 rejects.
- **why_span_1_alone_is_insufficient rewritten** (evidence_scope_completion; the composed claim holds only on the hosted-agent surface and must say so)
  - was: Span 1 establishes the condition on needs_approval, but does not state needs_approval.
  - now: Span 1 says a tool set to `True` always requires approval, and read alone it implies the run pauses for that approval — the opposite of what happens. It mentions neither hosted agents nor rejection, so a reader holding only span 1 answers the question wrongly rather than incompletely.
- **why_span_2_alone_is_insufficient rewritten** (evidence_scope_completion; the composed claim holds only on the hosted-agent surface and must say so)
  - was: Span 2 states what follows, but does not establish that it applies to needs_approval.
  - now: Span 2 says a function tool whose `needs_approval` is not `False` is rejected before the request is sent, but never says that `True` is a value anyone would set or what setting it is meant to achieve. A reader holding only span 2 knows an outcome without knowing the configuration that triggers it.

### Flags for your judgement

- E2: noncritical anaphora — refers to 'the model' with no antecedent in the span. Nothing scored mentions 'model': the question, answer, claims and critical strings are all satisfied without resolving it.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `72cb1e104a68797ed1296cfed17b04ba519cd1890449a2e5542f4ed36ad4e836` (and the other spans' hashes above).

---
