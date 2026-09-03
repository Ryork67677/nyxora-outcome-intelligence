# GOLD-001 — batch 004 near-miss multi-hop diagnostic

**5 bridge pairs** cleared every check in the composer except the entity-state rule. This document exists to test that rule, not to rescue the pairs.

§5 of the review brief forbids promoting any of these into batch 004, and the reason is worth stating plainly: choosing candidates by re-reading the rejection list is how a benchmark ends up measuring its own generator. If the rule is wrong, the place to fix it is batch 005's design, with the change preregistered before it sees any candidate.

## The rule under test

A pair is a chain only when span 2 makes its outcome conditional on **the bridge entity's own state**. Span 2 mentioning the entity and containing a conditional is not enough: the entity has to sit inside the conditional clause. Formally, for some conditional marker in span 2, the text from that marker to the next `,`/`;`/`:` (or 70 characters, whichever comes first) must contain the entity.

| # | bridge entity | provider | verdict |
| --- | --- | --- | --- |
| 1 | `OpenAIChatCompletionsModel` | openai | **CORRECT_REJECTION** |
| 2 | `allowed_callers` | anthropic | **CORRECT_REJECTION** |
| 3 | `max_tokens` | anthropic | **CORRECT_REJECTION** |
| 4 | `tool_result` | anthropic | **CORRECT_REJECTION** |
| 5 | `view_range` | anthropic | **CORRECT_REJECTION** |

---

## 1. `OpenAIChatCompletionsModel`

- **provider**: openai
- **span 1 document**: Results — Results › Streaming lifecycle and diagnostics › Raw responses
- **span 2 document**: Models — Models › Troubleshooting non-OpenAI providers › Chat Completions compatibility options
- **same document**: False

**Span 1 (proposed hop 1)**

```
The built-in `OpenAIResponsesModel` and `OpenAIChatCompletionsModel` propagate an available server-generated `x-request-id` on their HTTP and SSE transport paths.
```
critical strings: `OpenAIResponsesModel`, `OpenAIChatCompletionsModel`

**Span 2 (proposed hop 2)**

```
The OpenAI Chat Completions API can return audio output, but [`OpenAIChatCompletionsModel`][agents.models.openai_chatcompletions.OpenAIChatCompletionsModel] does not currently convert audio output into Agents SDK run items.
```
critical strings: `OpenAIChatCompletionsModel`, `openai_chatcompletions`

**Why every other check passed**

Both spans are openai documentation; span 1 is a condition statement about `OpenAIChatCompletionsModel` and is not a list enumeration; span 2 is a consequence statement; the entity appears near the front of both; and the composition check returned `PASS` — neither span carries the other hop's critical strings, so on the mechanical test neither span alone answers.

**Why the entity-state rule rejected it**

the span carries no conditional marker at all, so there is no clause that could test the entity's state

**Reviewer verdict: CORRECT_REJECTION**

Span 1 says the built-in models propagate `x-request-id` on their transport paths. Span 2 says the Chat Completions API can return audio output that the model does not convert into run items. These are two unrelated facts that happen to name the same class: request-id propagation has no bearing on audio conversion, and no answer follows from holding both. Span 2 contains no conditional at all, so there was nothing for span 1 to establish. The rejection is right, and it would have been right under any of the rules.

---

## 2. `allowed_callers`

- **provider**: anthropic
- **span 1 document**: Programmatic tool calling — Quick start
- **span 2 document**: Programmatic tool calling — Process results programmatically › Constraints and limitations › Input schema limitations
- **same document**: True

**Span 1 (proposed hop 1)**

```
Adding `allowed_callers: ["code_execution_20260120"]` to a tool definition is what makes that tool callable from within code execution (see [The `allowed_callers` field](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling#the-allowed-callers-field)):
```
critical strings: `allowed_callers`, `code_execution_20260120`

**Span 2 (proposed hop 2)**

```
Including a code execution tool version in `allowed_callers` for such a tool causes the request to fail with a `400 invalid_request_error` whose message contains `Circular $ref detected`.
```
critical strings: `allowed_callers`, `invalid_request_error`

**Why every other check passed**

Both spans are anthropic documentation; span 1 is a condition statement about `allowed_callers` and is not a list enumeration; span 2 is a consequence statement; the entity appears near the front of both; and the composition check returned `PASS` — neither span carries the other hop's critical strings, so on the mechanical test neither span alone answers.

**Why the entity-state rule rejected it**

the span's conditional markers are ['whose'], and none of their clauses contains `allowed_callers` — 'whose' governs 'message contains `Circular $ref detected`.'

**Reviewer verdict: CORRECT_REJECTION**

This is the closest of the five and still a correct rejection, though the rule caught it for a shallower reason than the one that matters. The rule saw that the only conditional marker in span 2 (`whose`) governs the error message rather than `allowed_callers`. The substantive problem is narrower: span 2's failure applies to a tool whose input schema contains a circular `$ref`, a qualification the phrase 'for such a tool' carries from text outside the span. Composing it with span 1 would produce 'adding `allowed_callers` makes the tool callable, and doing so fails with 400', which is false in general and true only for that unstated subcase. That is unsupported inference, which is the composition check's own §9 criterion. Span 1 also ends in a colon introducing a code block, so it is weak evidence on its own terms.

---

## 3. `max_tokens`

- **provider**: anthropic
- **span 1 document**: Extended thinking — Interleaved thinking in manual mode
- **span 2 document**: How tool use works — The agentic loop (client tools)
- **same document**: False

**Span 1 (proposed hop 1)**

```
* `budget_tokens` can exceed `max_tokens` here; the [budget rules](https://platform.claude.com/docs/en/build-with-claude/extended-thinking#budget-rules-and-tuning) explain this exception.
* Interleaved thinking is only supported for [tools used through the Messages API](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview).
```
critical strings: `budget_tokens`, `max_tokens`

**Span 2 (proposed hop 2)**

```
The loop exits on any other stop reason (`"end_turn"`, `"max_tokens"`, `"stop_sequence"`, or `"refusal"`), which means Claude has either produced a final answer or stopped for another reason that your application should handle.
```
critical strings: `end_turn`, `max_tokens`, `stop_sequence`

**Why every other check passed**

Both spans are anthropic documentation; span 1 is a condition statement about `max_tokens` and is not a list enumeration; span 2 is a consequence statement; the entity appears near the front of both; and the composition check returned `PASS` — neither span carries the other hop's critical strings, so on the mechanical test neither span alone answers.

**Why the entity-state rule rejected it**

the span carries no conditional marker at all, so there is no clause that could test the entity's state

**Reviewer verdict: CORRECT_REJECTION**

The most instructive of the five. Span 1 uses `max_tokens` as a request parameter that `budget_tokens` may exceed during interleaved thinking. Span 2 uses `"max_tokens"` as one of the stop_reason values on which the agentic loop exits. The bridge test matched a string that names two different things in the two spans, so there was never an entity to chain through. This is equivocation, not a hop, and it is worth recording that the bridge-entity requirement — the entity must appear in both spans — cannot detect it.

---

## 4. `tool_result`

- **provider**: anthropic
- **span 1 document**: Programmatic tool calling — Process results programmatically › Constraints and limitations › Message formatting restrictions
- **span 2 document**: Stop reasons and fallback — Stop reason values › tool\_use
- **same document**: False

**Span 1 (proposed hop 1)**

```
**Text-only tool result content:** The `content` of each `tool_result` that answers a programmatic call must be a string or `text` blocks.
```
critical strings: `content`, `tool_result`, `text`

**Span 2 (proposed hop 2)**

```
Adding anything after the `tool_result` blocks in that user message, such as text, ends the assistant turn; for a server tool Claude called directly, the request then fails with a 400 `invalid_request_error` that names the unresolved server tool:
```
critical strings: `tool_result`, `invalid_request_error`

**Why every other check passed**

Both spans are anthropic documentation; span 1 is a condition statement about `tool_result` and is not a list enumeration; span 2 is a consequence statement; the entity appears near the front of both; and the composition check returned `PASS` — neither span carries the other hop's critical strings, so on the mechanical test neither span alone answers.

**Why the entity-state rule rejected it**

the span carries no conditional marker at all, so there is no clause that could test the entity's state

**Reviewer verdict: CORRECT_REJECTION**

Span 1 requires the `content` of a `tool_result` answering a programmatic call to be a string or text blocks. Span 2 says that adding anything after the `tool_result` blocks in a user message ends the assistant turn, and fails with 400 for a server tool Claude called directly. Both are formatting rules about `tool_result` and neither depends on the other: satisfying span 1 tells a reader nothing about span 2's outcome. Two rules in one subject area are still two lookups. Span 2 also ends in a colon, and its condition is about message structure rather than about the entity's configured state.

---

## 5. `view_range`

- **provider**: anthropic
- **span 1 document**: Text editor tool — Use the text editor tool › Text editor tool commands › view
- **span 2 document**: Memory tool — Tool commands › view
- **same document**: False

**Span 1 (proposed hop 1)**

```
* `command`: Must be "view"
* `path`: The path to the file or directory to view
* `view_range` (optional): An array of two integers specifying the start and end line numbers to view.
```
critical strings: `command`, `path`, `view_range`

**Span 2 (proposed hop 2)**

```
`view_range` is optional and applies to text-file views: `[start_line, end_line]` returns those lines, and `[start_line, -1]` returns everything from `start_line` to the end of the file.
```
critical strings: `view_range`, `start_line`, `end_line`

**Why every other check passed**

Both spans are anthropic documentation; span 1 is a condition statement about `view_range` and is not a list enumeration; span 2 is a condition_and_consequence statement; the entity appears near the front of both; and the composition check returned `PASS` — neither span carries the other hop's critical strings, so on the mechanical test neither span alone answers.

**Why the entity-state rule rejected it**

the span carries no conditional marker at all, so there is no clause that could test the entity's state

**Reviewer verdict: CORRECT_REJECTION**

Span 1 is a bullet list describing `view_range` in the text editor tool; span 2 describes `view_range` in the memory tool. They are two parallel definitions of a parameter in two different tools, which is the plainest possible case of multi-span-is-not-multi-hop. Span 1 is also a list fragment whose stem sits outside the span, so it would have failed the evidence-scope check even if the pair had been a chain.

---

## What this says about the rule

Every pair here is a correct rejection, and each fails in the same way: the two spans are about the same identifier and about different questions. That is the shape batch 003 shipped four times. On this evidence the rule is not too strict — it is the only check that caught them, since all four cleared the composition check that is supposed to be the hostile one.

The composition check's blind spot is worth recording for batch 005: it asks whether either span carries the *other hop's critical strings*, which is a test of textual overlap, not of whether the two facts bear on one another. Two unrelated facts share no strings, so they pass. The entity-state rule is a crude proxy for the missing test, and a better one would ask whether span 1 establishes the state span 2's condition tests — which is the judgement `GOLD-B004-15` is flagged for.

## Scope

Diagnostic only. No pair here is a batch-004 candidate, none was added, and batch 004 was not regenerated. No retrieval system was run; SYSTEM-A and SYSTEM-B remain frozen and unexecuted.
