# GOLD-001 — batch 001 human QC packet

**17 decisions.** 10 fast track, 6 need the anchor checked, 1 recommended for rejection.

Nothing in this packet is gold. A candidate becomes `human_verified` only when you record `APPROVE` for it in `evals/review/human_decisions_batch_001.json` and import that file. A ChatGPT `PASS` produces `dual_llm_pass` and stops there — two AI systems agreeing is not human verification.

**Judge each case against the anchored evidence block alone.** The context is there to let you spot a bad anchor, not to answer the question. If you need the context to answer it, the anchor is wrong: `NEEDS_EDIT`.

**The anchors were never moved.** The import path forbids a reviewer from changing a source span, so every repair below is a repair to the *wording*. Where that leaves a claim resting on a term the span does not contain, it is flagged in section B rather than smoothed over.

Queue: 16 mandatory + 1 sampled from the 2 agreed passes (seed 20250819, rate 15%).

| id | verdict | risk | defects | one-line |
| --- | --- | --- | --- | --- |
| `02` | PASS | LOW | — | What is the default value of reset_tool_choice? |
| `05` | FIX_REQUIRED | LOW | — | What does the Claude API return if the input alone already exceeds th… |
| `06` | FIX_REQUIRED | LOW | — | When parsing an OpenAI webhook payload, what must the `body` paramete… |
| `07` | FIX_REQUIRED | LOW | — | What happens if a mid-conversation tool change references a tool name… |
| `08` | FIX_REQUIRED | LOW | D2 | By default, what kind of SDK release is used when `engines.node`, emi… |
| `09` | FIX_REQUIRED | LOW | D2 | When does the Anthropic SDK tool runner stop looping? |
| `10` | FIX_REQUIRED | LOW | — | Why should you avoid filtering `response.output` down to only message… |
| `11` | FIX_REQUIRED | LOW | — | How should a tool-using Claude agent handle an error raised by a tool? |
| `12` | FIX_REQUIRED | LOW | D2 | What does the `nest_handoff_history` option on `handoff()` override? |
| `18` | FIX_REQUIRED | LOW | — | When tool search discovers a deferred tool and returns a `tool_refere… |
| `03` | FIX_REQUIRED | MEDIUM | D1 | For Claude Fable 5 and Claude Mythos 5, is a `thinking` configuration… |
| `04` | FIX_REQUIRED | HIGH | D1 | What exception is raised when an input guardrail's `tripwire_triggere… |
| `13` | FIX_REQUIRED | HIGH | — | What value must `anthropic_version` be set to when using Claude on Go… |
| `14` | FIX_REQUIRED | HIGH | D1 | What error is returned if you send a prefilled last assistant message… |
| `16` | FIX_REQUIRED | HIGH | D3 | What happens if the `embd_normalize` helper encounters a row whose no… |
| `17` | FIX_REQUIRED | MEDIUM | D2 | What does a 404 `File not found` error mean in the Anthropic Files API? |
| `15` | FAIL | HIGH | D3 | In the specific streaming tool-use example, what value is `tool_choic… |

---

## A. Fast track — every asserted term is in the anchored span

Read the question, glance at the span, decide. These carry no detected gap between what the case claims and what its anchor contains.

#### GOLD-B001-02 · PASS · risk LOW

**Q.** What is the default value of reset_tool_choice?

**A.** True

**Claims**
  1. reset_tool_choice defaults to True

**Evidence span** — `ver_35cac5e98c151a17f941a6142d74709f` 3571–3725 · Agents > Basic configuration

```
| `reset_tool_choice` | no | Reset `tool_choice` after a tool call (default: `True`) to avoid tool-use loops. See [Forcing tool use](#forcing-tool-use). |
```

<details><summary>surrounding context</summary>

```
…s). |
| `hooks` | no | Agent-scoped lifecycle callbacks. See [Lifecycle events (hooks)](#lifecycle-events-hooks). |
| `tool_use_behavior` | no | Control whether tool results loop back to the model or end the run. See [Tool use behavior](#tool-use-behavior). |
  ⟦SPAN⟧
```python
from agents import Agent
from agents.decorators import tool

@tool
def get_weather(city: str) -> str:
    """returns weather info for the specified city."""
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Haiku agent",
    in…
```

</details>

**Why you are seeing this.** Both models passed this case. It is here because agreement between two models is correlated evidence, not independent confirmation, and this candidate was drawn as the deterministic QC sample.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-02` in `human_decisions_batch_001.json`.

---

#### GOLD-B001-05 · FIX_REQUIRED · risk LOW

**Q.** What does the Claude API return if the input alone already exceeds the model's context window?

**A.** A 400 `invalid_request_error` with the message `prompt is too long`.

**Claims**
  1. If the input alone exceeds the model's context window, the API returns a 400 `invalid_request_error`.
  2. The error message is `prompt is too long`.

**Evidence span** — `ver_b42814c2d273210095c8e5844612933e` 14083–14230 · Context window overflow behavior

```
If the input alone already exceeds the model's context window, the API returns a 400 `invalid_request_error` ("prompt is too long") on every model.
```

<details><summary>surrounding context</summary>

```
…ended thinking

Cached prompt prefixes still occupy the context window: [prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) changes what you pay for those tokens, not whether they count.

## Context window overflow behavior
  ⟦SPAN⟧
On Claude 4.5 models and newer, if input tokens plus `max_tokens` exceeds the context window size, the API accepts the request. If generation then reaches the context window limit, it stops with `stop_reason: "model_context_window_exceeded"`. On earlier mode…
```

</details>

**Why you are seeing this.** The generator shipped this as evidence with no question; the reviewer wrote the question, answer and claims. Two models are not human verification.

*Note:* the question mentions `Claude API` as framing only; no claim depends on it.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-05` in `human_decisions_batch_001.json`.

---

#### GOLD-B001-06 · FIX_REQUIRED · risk LOW

**Q.** When parsing an OpenAI webhook payload, what must the `body` parameter contain?

**A.** The raw JSON string sent from the server; it should not be parsed first.

**Claims**
  1. The `body` parameter must be the raw JSON string sent from the server.
  2. The body should not be parsed before being passed to the webhook parsing/verification method.

**Evidence span** — `ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` 14847–14951 · Remove `await` for non-async usage. > Webhook Verification > Parsing webhook payloads

```
Note that the `body` parameter must be the raw JSON string sent from the server (do not parse it first).
```

<details><summary>surrounding context</summary>

```
…verify the webhook and parse the payload at the same time. To achieve this, we provide the method `client.webhooks.unwrap()`, which parses a webhook request and verifies that it was sent by OpenAI. This method will raise an error if the signature is invalid.
  ⟦SPAN⟧
The `.unwrap()` method will parse this JSON for you into an event object after verifying the webhook was sent from OpenAI.

```python
from openai import OpenAI
from flask import Flask, request

app = Flask(__name__)
client = OpenAI()  # OPENAI_WEBHOOK_SECRET…
```

</details>

**Why you are seeing this.** The generator shipped this as evidence with no question; the reviewer wrote the question, answer and claims. Two models are not human verification.

*Note:* the question mentions `OpenAI` as framing only; no claim depends on it.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-06` in `human_decisions_batch_001.json`.

---

#### GOLD-B001-07 · FIX_REQUIRED · risk LOW

**Q.** What happens if a mid-conversation tool change references a tool name that was not declared in the request's `tools` array?

**A.** The request returns a 400 error.

**Claims**
  1. Referencing a tool name that is not declared in `tools` returns a 400 error.

**Evidence span** — `ver_77fbe47b4b7db32ee46b972b2f611d0e` 4256–4327 · Mid-conversation tool changes

```
Referencing a name that is not declared in `tools` returns a 400 error.
```

<details><summary>surrounding context</summary>

```
…tools` array, and [MCP connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) tools can be referenced individually with `mcp_tool_reference` (`server_name` and `name`) or as a whole toolset with `mcp_toolset_reference` (`server_name`).
  ⟦SPAN⟧
Every tool declared in `tools` is offered to the model from the start of the conversation unless it is declared with `defer_loading: true`, which keeps it withheld until a `tool_addition` block surfaces it. `tool_addition` also re-offers a tool that an earli…
```

</details>

**Why you are seeing this.** The generator shipped this as evidence with no question; the reviewer wrote the question, answer and claims. Two models are not human verification.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-07` in `human_decisions_batch_001.json`.

---

#### GOLD-B001-08 · FIX_REQUIRED · risk LOW

**Q.** By default, what kind of SDK release is used when `engines.node`, emitted JavaScript syntax, or required runtime APIs are raised?

**A.** An SDK major release.

**Claims**
  1. Raising `engines.node`, emitted JavaScript syntax, or required runtime APIs ships in an SDK major release by default.

**Evidence span** — `ver_0699973a131d91f270d69f81ba7a0da0` 1250–1371 · Node.js Version Support Policy > Release and packaging rules

```
- Raising `engines.node`, emitted JavaScript syntax, or required runtime APIs
  ships in an SDK major release by default.
```

<details><summary>surrounding context</summary>

```
…The exception must be recorded below with its
owner, reason, and end date. It provides only feasible SDK fixes and migration
help; OpenAI cannot provide missing upstream runtime security fixes, and the
exception may end early.

## Release and packaging rules
  ⟦SPAN⟧
An urgent minor-release exception
  requires SDK and Security approval. Never hide a runtime-floor change in a
  patch.
- Adding a newly promoted LTS without raising the minimum is an SDK minor.
- `engines.node` states the technical floor. The README support…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**D2 — what was repaired.** The generator's relation label pointed at the wrong fact; the reviewer re-authored the question and claims around what the span actually states.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-08` in `human_decisions_batch_001.json`.

---

#### GOLD-B001-09 · FIX_REQUIRED · risk LOW

**Q.** When does the Anthropic SDK tool runner stop looping?

**A.** When Claude returns a message without a tool use, or when the runner reaches `max_iterations` if that limit was set.

**Claims**
  1. The tool runner stops when Claude returns a message without a tool use.
  2. If `max_iterations` is set, the tool runner also stops when that limit is reached.

**Evidence span** — `ver_96d5aba3c4e7771cabd4f3d4f5a3fff1` 19885–20004 · Iterating over the tool runner

```
The runner loops until Claude returns a message without a tool use, or until it reaches `max_iterations` if you set it.
```

<details><summary>surrounding context</summary>

```
…the runner checks whether Claude requested a tool use. If so, it runs the tool and sends the result back to Claude automatically, then yields the next message from Claude to continue your loop.

You can end the loop at any iteration with a `break` statement.
  ⟦SPAN⟧
If you don't need intermediate messages, you can get the final message directly:

<Tabs>
  <Tab title="Python">
    Use `runner.until_done()` to get the final message.

    ```python
    client = anthropic.Anthropic()
    # ...
    runner = client.beta.messa…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**D2 — what was repaired.** The generator's relation label pointed at the wrong fact; the reviewer re-authored the question and claims around what the span actually states.

*Note:* the question mentions `Anthropic SDK` as framing only; no claim depends on it.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-09` in `human_decisions_batch_001.json`.

---

#### GOLD-B001-10 · FIX_REQUIRED · risk LOW

**Q.** Why should you avoid filtering `response.output` down to only message items when manually carrying Responses API conversation history forward?

**A.** Because doing so can drop required reasoning or tool-call items and cause the next request to fail.

**Claims**
  1. Filtering `response.output` to message items can remove required reasoning or tool-call items.
  2. Dropping those required items can cause the next request to fail.

**Evidence span** — `ver_f30a6447e4df2ab76e4c1475f353109c` 1631–1753 · OpenAI TypeScript and JavaScript API Library > Usage > Multi-turn conversations

```
Filtering
`response.output` to messages can drop required reasoning or tool-call items and cause the next request to
fail.
```

<details><summary>surrounding context</summary>

```
…ing assistant that talks like a pirate',
  input: 'Are semicolons optional in JavaScript?',
});

console.log(response.output_text);
```

### Multi-turn conversations

When you manage Responses API conversation history manually, preserve output items in order.
  ⟦SPAN⟧
Use the SDK's `toResponseInputItems()` helper to normalize all replayable output items before adding them to
the next request. For simple continuation, you can pass `previous_response_id` instead.

See the [manual conversation state example](examples/respons…
```

</details>

**Why you are seeing this.** The generator shipped this as evidence with no question; the reviewer wrote the question, answer and claims. Two models are not human verification.

*Note:* the question mentions `Responses API` as framing only; no claim depends on it.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-10` in `human_decisions_batch_001.json`.

---

#### GOLD-B001-11 · FIX_REQUIRED · risk LOW

**Q.** How should a tool-using Claude agent handle an error raised by a tool?

**A.** Send the error message back with `is_error: true` instead of crashing.

**Claims**
  1. When a tool raises an error, the tool result should return the error message with `is_error: true` rather than crashing.

**Evidence span** — `ver_fc127d394b32ba1f136356d746c083e5` 103289–103388 · Ring 4: Error handling

```
When a tool raises an error, send the error message back with `is_error: true` instead of crashing.
```

<details><summary>surrounding context</summary>

```
…ordering guarantees, see [Parallel tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use).

## Ring 4: Error handling

Tools fail. A calendar API might reject an event with too many attendees, or a date might be malformed.
  ⟦SPAN⟧
Claude reads the error and can retry with corrected input, ask the user for clarification, or explain the limitation.

<CodeGroup>
  ```bash cURL
  #!/bin/bash
  # Ring 4: Error handling.

  TOOLS='[
    {
      "name": "create_calendar_event",
      "descrip…
```

</details>

**Why you are seeing this.** The generator shipped this as evidence with no question; the reviewer wrote the question, answer and claims. Two models are not human verification.

*Note:* the question mentions `Claude` as framing only; no claim depends on it.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-11` in `human_decisions_batch_001.json`.

---

#### GOLD-B001-12 · FIX_REQUIRED · risk LOW

**Q.** What does the `nest_handoff_history` option on `handoff()` override?

**A.** It is an optional per-handoff override for the RunConfig-level `nest_handoff_history` setting.

**Claims**
  1. `nest_handoff_history` is an optional per-handoff override for the RunConfig-level `nest_handoff_history` setting.

**Evidence span** — `ver_1c77f33b04ffffa285ea7e61c2a89653` 2603–2846 · (1)! > Customizing handoffs via the `handoff()` function

```
This can be a boolean or a function that returns a boolean, allowing you to dynamically enable or disable the handoff at runtime.
-   `nest_handoff_history`: Optional per-handoff override for the RunConfig-level `nest_handoff_history` setting.
```

<details><summary>surrounding context</summary>

```
…type`: The schema for the handoff tool-call arguments. When set, the parsed payload is passed to `on_handoff`.
-   `input_filter`: This lets you filter the input received by the next agent. See below for more.
-   `is_enabled`: Whether the handoff is enabled.
  ⟦SPAN⟧
If `None`, the value defined in the active run configuration is used instead.

The [`handoff()`][agents.handoffs.handoff] helper always transfers control to the specific `agent` you passed in. If you have multiple possible destinations, register one handoff p…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**D2 — what was repaired.** The generator's relation label pointed at the wrong fact; the reviewer re-authored the question and claims around what the span actually states.

*Note:* the question mentions `handoff()` as framing only; no claim depends on it.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-12` in `human_decisions_batch_001.json`.

---

#### GOLD-B001-18 · FIX_REQUIRED · risk LOW

**Q.** When tool search discovers a deferred tool and returns a `tool_reference`, where is the tool's full definition expanded?

**A.** Inline at that point in the conversation body, not in the prompt prefix.

**Claims**
  1. When a deferred tool is discovered and returned as a `tool_reference`, its full definition is expanded inline in the conversation body.
  2. The full definition is not expanded in the prompt prefix.

**Evidence span** — `ver_5f5df502fc725ffcca9d893fef90fe3f` 11593–11779 · Tool definition properties > `defer_loading` and prompt caching

```
When tool search discovers a deferred tool and returns a `tool_reference` for it, the tool's full definition is expanded inline at that point in the conversation body, not in the prefix.
```

<details><summary>surrounding context</summary>

```
…ding the `caller` response shape and error behavior.

### `defer_loading` and prompt caching

Tools with `defer_loading: true` are stripped from the rendered tools section before the cache key is computed. They don't appear in the system-prompt prefix at all.
  ⟦SPAN⟧
This means `defer_loading: true` preserves your prompt cache. You can add deferred tools to a request without invalidating an existing cache entry, and the cache remains valid across the turn where the tool is discovered and the turn where it's called.

For…
```

</details>

**Why you are seeing this.** The generator shipped this as evidence with no question; the reviewer wrote the question, answer and claims. Two models are not human verification.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-18` in `human_decisions_batch_001.json`.

---

---

## B. Check the anchor before approving

Each of these asserts something the anchored span does not contain. This is the OA-002 defect class, and it is the reason the whole batch exists — do not skim these.

#### GOLD-B001-03 · FIX_REQUIRED · risk MEDIUM

**Q.** For Claude Fable 5 and Claude Mythos 5, is a `thinking` configuration required?

**A.** No. Adaptive thinking is always on, the model decides when and how much to think, and no `thinking` configuration is required.

**Claims**
  1. For Claude Fable 5 and Claude Mythos 5, no `thinking` configuration is required.

**Evidence span** — `ver_a7bda3595f2c124605c3228464d4ee52` 2410–2519 · Migrating to Claude Mythos 5 and Claude Fable 5

```
The model determines when and how much to think on each request, and no `thinking` configuration is required.
```

<details><summary>surrounding context</summary>

```
…red in limited availability to approved customers in Project Glasswing.

The baseline settings shared by `claude-fable-5` and `claude-mythos-5`:

* **Thinking:** [Adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) is always on.
  ⟦SPAN⟧
Both `thinking: {type: "disabled"}` and manual extended thinking (`thinking: {type: "enabled", budget_tokens: N}`) return a 400 error.
* **Prefill:** Prefilling the assistant message returns a 400 error. Use system prompt instructions instead.
* **Context win…
```

</details>

**Why you are seeing this.** A claim asserts `Claude Fable 5`, `Claude Mythos 5`, which appears in the section path but not in the anchored span. Confirm the section scope is genuinely part of the claim before approving.

**D1 — what was repaired.** The anchor still opens on a referent it does not contain; the reviewer repaired this by rewriting the question to name the scope explicitly, and the span itself is unchanged.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-03` in `human_decisions_batch_001.json`.

---

#### GOLD-B001-04 · FIX_REQUIRED · risk HIGH

**Q.** What exception is raised when an input guardrail's `tripwire_triggered` value is true?

**A.** `InputGuardrailTripwireTriggered`.

**Claims**
  1. When an input guardrail's `tripwire_triggered` value is true, an `InputGuardrailTripwireTriggered` exception is raised.

**Evidence span** — `ver_f22fbd5c504fa28a4e70440337e4a495` 1930–2119 · Guardrails > Input guardrails

```
If true, an [`InputGuardrailTripwireTriggered`][agents.exceptions.InputGuardrailTripwireTriggered] exception is raised, so you can appropriately respond to the user or handle the exception.
```

<details><summary>surrounding context</summary>

```
…tput`][agents.guardrail.GuardrailFunctionOutput], which is then wrapped in an [`InputGuardrailResult`][agents.guardrail.InputGuardrailResult]
3. Finally, we check if [`.tripwire_triggered`][agents.guardrail.GuardrailFunctionOutput.tripwire_triggered] is true.
  ⟦SPAN⟧
!!! Note

    Input guardrails are intended to run on user input, so an agent's guardrails only run if the agent is the *first* agent. You might wonder, why is the `guardrails` property on the agent instead of passed to `Runner.run`? It's because guardrails…
```

</details>

**Why you are seeing this.** A claim asserts `tripwire_triggered`, which the anchored span does not contain and the document title and section path do not supply either. Approving accepts a claim the anchor cannot support on its own.

**D1 — what was repaired.** The anchor still opens on a referent it does not contain; the reviewer repaired this by rewriting the question to name the scope explicitly, and the span itself is unchanged.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-04` in `human_decisions_batch_001.json`.

---

#### GOLD-B001-13 · FIX_REQUIRED · risk HIGH

**Q.** What value must `anthropic_version` be set to when using Claude on Google Cloud's Agent Platform?

**A.** `vertex-2023-10-16`.

**Claims**
  1. On Google Cloud Agent Platform, `anthropic_version` is passed in the request body and must be set to `vertex-2023-10-16`.

**Evidence span** — `ver_e312b7f41115cc2b84cd36151efc6dd8` 519–725 · Preamble

```
Instead, it is specified in the Google Cloud endpoint URL.
* On Agent Platform, `anthropic_version` is passed in the request body (rather than as a header), and must be set to the value `vertex-2023-10-16`.
```

<details><summary>surrounding context</summary>

```
…accessing Claude on Google Cloud's Agent Platform is nearly identical to the [Messages API](https://platform.claude.com/docs/en/api/messages/create), with two key differences in request format:

* On Agent Platform, `model` is not passed in the request body.
  ⟦SPAN⟧
Agent Platform is also supported by Anthropic's official [client SDKs](https://platform.claude.com/docs/en/cli-sdks-libraries/overview). This guide walks you through making a request to Claude on Agent Platform using one of Anthropic's client SDKs.

Note tha…
```

</details>

**Why you are seeing this.** A claim asserts `Google Cloud Agent Platform`, which the anchored span does not contain and the document title and section path do not supply either. Approving accepts a claim the anchor cannot support on its own.

*Note:* the question mentions `Claude` as framing only; no claim depends on it.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-13` in `human_decisions_batch_001.json`.

---

#### GOLD-B001-14 · FIX_REQUIRED · risk HIGH

**Q.** What error is returned if you send a prefilled last assistant message to Claude 4.6-and-later models or Claude Mythos Preview?

**A.** A 400 `invalid_request_error`.

**Claims**
  1. Claude 4.6-and-later models and Claude Mythos Preview do not support prefilling assistant messages.
  2. Sending a request with a prefilled last assistant message to those models returns a 400 `invalid_request_error`.

**Evidence span** — `ver_0774ca0093ff4a846753577c9a4a39d5` 19189–19308 · Common validation errors > Prefill not supported

```
Sending a request with a prefilled last assistant message to any of these models returns a 400 `invalid_request_error`:
```

<details><summary>surrounding context</summary>

```
…ng#get-the-final-message-without-handling-events) for more details.

## Common validation errors

### Prefill not supported

Claude 4.6 and later models and [Claude Mythos Preview](https://anthropic.com/glasswing) do not support prefilling assistant messages.
  ⟦SPAN⟧
```json
{
  "type": "error",
  "error": {
    "type": "invalid_request_error",
    "message": "This model does not support assistant message prefill. The conversation must end with a user message."
  }
}
```

Use [structured outputs](https://platform.claude.…
```

</details>

**Why you are seeing this.** A claim asserts `Claude 4.6`, `Claude Mythos Preview`, which the anchored span does not contain and the document title and section path do not supply either. Approving accepts a claim the anchor cannot support on its own.

**D1 — what was repaired.** The anchor still opens on a referent it does not contain; the reviewer repaired this by rewriting the question to name the scope explicitly, and the span itself is unchanged.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-14` in `human_decisions_batch_001.json`.

---

#### GOLD-B001-16 · FIX_REQUIRED · risk HIGH

**Q.** What happens if the `embd_normalize` helper encounters a row whose norm is zero?

**A.** It raises a `ValueError` to prevent division by zero.

**Claims**
  1. The example `embd_normalize` helper raises a `ValueError` if any row has a norm of zero.
  2. The zero-norm check prevents division by zero.

**Evidence span** — `ver_26f61f56d6ff7124cfa38152f7baef3d` 22027–22317 · and cosine similarity are the same. > FAQ

```
Raises a ValueError if any row has a norm of zero to prevent division by zero.
        """
        row_norms = np.linalg.norm(v, axis=1, keepdims=True)
        if np.any(row_norms == 0):
            raise ValueError("Cannot normalize rows with a norm of zero.")
        return v / row_norms
```

<details><summary>surrounding context</summary>

```
…to 256 dimensions:

    ```python
    import voyageai
    import numpy as np


    def embd_normalize(v: np.ndarray) -> np.ndarray:
        """
        Normalize the rows of a 2D numpy array to unit vectors by dividing each row by its Euclidean
        norm.
  ⟦SPAN⟧
vo = voyageai.Client()

    # Generate voyage-code-3 vectors, which by default are 1024-dimensional floating-point numbers
    embd = vo.embed(["Sample text 1", "Sample text 2"], model="voyage-code-3").embeddings

    # Set shorter dimension
    short_d…
```

</details>

**Why you are seeing this.** A claim asserts `embd_normalize`, which the anchored span does not contain and the document title and section path do not supply either. Approving accepts a claim the anchor cannot support on its own.

**D3 — what was repaired.** The span is example code, and the generator framed it as a documented rule; the reviewer narrowed the question to be about the example itself.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-16` in `human_decisions_batch_001.json`.

---

#### GOLD-B001-17 · FIX_REQUIRED · risk MEDIUM

**Q.** What does a 404 `File not found` error mean in the Anthropic Files API?

**A.** The specified `file_id` does not exist or you do not have access to it.

**Claims**
  1. A Files API `File not found` error uses HTTP 404.
  2. It indicates that the specified `file_id` does not exist or the caller does not have access to it.

**Evidence span** — `ver_ab9e2c2bf4c17bf70ce1b94355d01729` 29836–30171 · Error handling

```
* **File not found (404):** The specified `file_id` doesn't exist or you don't have access to it
* **Invalid file type (400):** The file type doesn't match the content block type (for example, using an image file in a document block)
* **Not downloadable (400):** Files you upload have `"downloadable": false` and cannot be downloaded.
```

<details><summary>surrounding context</summary>

```
…how-long-do-you-store-my-organization-s-data). For ZDR eligibility across all features, see [API and data retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)

## Error handling

Common errors when using the Files API include:
  ⟦SPAN⟧
Only files created by skills or the code execution tool can be downloaded
* **Exceeds context window size (400):** The file is larger than the context window size (for example, using a 500 MB plain text file in a `/v1/messages` request)
* **Invalid filename (…
```

</details>

**Why you are seeing this.** A claim asserts `Files API`, which appears in the section path but not in the anchored span. Confirm the section scope is genuinely part of the claim before approving.

**D2 — what was repaired.** The generator's relation label pointed at the wrong fact; the reviewer re-authored the question and claims around what the span actually states.

*Note:* the question mentions `Anthropic Files API` as framing only; no claim depends on it.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-17` in `human_decisions_batch_001.json`.

---

---

## C. Independent review recommends rejection

Included for your decision and the audit trail, not for rescue. No second automatic repair was attempted.

#### GOLD-B001-15 · FAIL · risk HIGH

**Q.** In the specific streaming tool-use example, what value is `tool_choice.type` set to?

**A.** `any`.

**Claims**
  1. In this example request, `tool_choice.type` is set to `any`.

**Evidence span** — `ver_1261879c16f641270789647ac9c63c96` 19561–19921 · Full HTTP stream response > Streaming request with tool use

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

<details><summary>surrounding context</summary>

```
…the current weather in a given location",
            "input_schema": {
              "type": "object",
              "properties": {
                "location": {
                  "type": "string",
                  "description": "The city and state, e.g.
  ⟦SPAN⟧
```bash CLI
  ant messages create --stream --format jsonl <<'YAML'
  model: claude-opus-5
  max_tokens: 1024
  tools:
    - name: get_weather
      description: Get the current weather in a given location
      input_schema:
        type: object
        pr…
```

</details>

**Why you are seeing this.** The independent review recommends rejection: the span is a sample configuration, so any question over it tests an example rather than a documented rule.

**D3 — what was repaired.** The span is example code, and the generator framed it as a documented rule; the reviewer narrowed the question to be about the example itself.

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B001-15` in `human_decisions_batch_001.json`.

---

## Audit

The full history — the generator's original proposal, the reviewer's verdict and boolean checks, every numbered revision, and the anchor as first mined — is retained per candidate in `gold_batch_001_qc.json` under `audit`. Nothing was overwritten, and no anchor was changed (0 disputes recorded).

OA-002 is a defect in the original development set and is deliberately not part of this batch. Its `development/v2` correction remains proposed and unapplied.
