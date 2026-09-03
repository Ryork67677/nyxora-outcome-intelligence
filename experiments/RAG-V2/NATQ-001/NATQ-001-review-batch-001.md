# NATQ-001 review packet (batch 001)

**Corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · generated 2026-09-02T17:53:30Z (2026-09-02 13:53 EDT)**

**Header instruction for ChatGPT (coordinator):** The quoted evidence below is authoritative. **Do not consult live docs.** The corpus is frozen snapshot `snap_689e336380a054d8039dc35b2c09cd0a`. Judge each candidate against the quoted evidence and the short context_before/after only.

Nothing in this file is frozen gold. Every candidate is `PENDING_CHATGPT_REVIEW`. `proposed_split` is **PROPOSED / NOT_FROZEN** metadata — ChatGPT must see **all 100** candidates; the split is not a secrecy boundary yet. Do not create a NATQ holdout lock.

For each candidate, return verdict `PASS | FAIL | FIX_REQUIRED | UNCERTAIN` against the evidence as written. Do not rewrite questions into corpus language unless FIX_REQUIRED.

ID prefix `NATQ-C-`. This is NATQ-001 question-first authoring + evidence-second verification, not gold150-v1 and not V2-DEVSET-001.

---

**This batch:** 50 candidates (`NATQ-C-001` … `NATQ-C-120`). Complements the other batch; together they are the full 100.
## NATQ-C-001

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Handoffs
- **version_id**: `ver_1c77f33b04ffffa285ea7e61c2a89653`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/handoffs.md
- **section**: Handoffs › Creating a handoff
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> how do i hand off between agents in the openai agents sdk

**Answer**: Put target agents on the current agent's `handoffs` list (plain `Agent` or `handoff(...)`). Handoffs are tools the LLM can call (e.g. `transfer_to_refund_agent`).

**Atomic claims**:
  - Handoffs allow an agent to delegate tasks to another agent.
  - Handoffs are represented as tools to the LLM (e.g. transfer_to_refund_agent).
  - All agents have a handoffs param that can take an Agent directly or a Handoff object.
  - Example: triage_agent = Agent(..., handoffs=[billing_agent, handoff(refund_agent)]).

**Critical strings**: `handoffs`, `handoff()`, `transfer_to_refund_agent`

### Evidence E1 (verbatim, authoritative)

`ver_1c77f33b04ffffa285ea7e61c2a89653` chars 12–1519 · hash `bd42fa2ceb82a8f722811c5de7221a882b67f4f6793246ac34ebe55f935cb544`

````
Handoffs allow an agent to delegate tasks to another agent. This is particularly useful in scenarios where different agents specialize in distinct areas. For example, a customer support app might have agents that each specifically handle tasks like order status, refunds, FAQs, etc.

Handoffs are represented as tools to the LLM. So if there's a handoff to an agent named `Refund Agent`, the tool would be named `transfer_to_refund_agent`.

## Creating a handoff

All agents have a [`handoffs`][agents.agent.Agent.handoffs] param, which can either take an `Agent` directly, or a `Handoff` object that customizes the Handoff.

If you pass plain `Agent` instances, their [`handoff_description`][agents.agent.Agent.handoff_description] (when set) is appended to the default tool description. Use it to hint when the model should pick that handoff without writing a full `handoff()` object.

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
````

<details><summary>Context before (short)</summary>

```
# Handoffs

```

</details>

<details><summary>Context after (short)</summary>

```


### Customizing handoffs via the `handoff()` function

The [`handoff()`][agents.handoffs.handoff] function lets you customize things.

-   `agent`: This is the agent to which things will be handed off.
-   `tool_name_override`: By default, the `Handoff.default_tool_name()` function is used, which resolves to `transfer_to_<agent_name>`. You can override this.
-   `tool_description_override`: Over…
```

</details>

---
## NATQ-C-002

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Running agents
- **version_id**: `ver_2c60e99cfd929a738910b893fd6f1a40`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/running_agents.md
- **section**: Running agents › Runner lifecycle and configuration › The agent loop
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> runner vs agent in the python agents sdk — which one actually calls the model

**Answer**: The `Runner` agent loop calls the LLM for the current agent. `Agent` holds config; `Runner` is what actually invokes the model.

**Atomic claims**:
  - The runner runs a loop after you call a Runner method with a starting agent.
  - Step 1 of the loop: We call the LLM for the current agent, with the current input.

**Critical strings**: `The runner then runs a loop`, `We call the LLM for the current agent`

### Evidence E1 (verbatim, authoritative)

`ver_2c60e99cfd929a738910b893fd6f1a40` chars 1496–1591 · hash `a8d6b8fb890056326897a6f4497aadd9b4fbed1ef10e45f0ff655e6bb1ed7de4`

```
The runner then runs a loop:

1. We call the LLM for the current agent, with the current input.
```

<details><summary>Context before (short)</summary>

````
s import Agent, Runner

async def main():
    agent = Agent(name="Assistant", instructions="You are a helpful assistant")

    result = await Runner.run(agent, "Write a haiku about recursion in programming.")
    print(result.final_output)
    # Code within the code,
    # Functions calling themselves,
    # Infinite loop's dance
```

Read more in the [results guide](results.md).

## Runner lifecy…
````

</details>

<details><summary>Context after (short)</summary>

```

2. The LLM produces its output.
    1. If the runner classifies the LLM's output as final output, the loop ends and we return the result.
    2. If the LLM requests a handoff, we update the current agent and input, and re-run the loop.
    3. If the LLM produces tool calls, we run those tool calls, append the results, and re-run the loop.
3. If we exceed the `max_turns` passed, we raise a [`MaxTu…
```

</details>

---
## NATQ-C-004

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Sessions
- **version_id**: `ver_b275f1db2ff0a82e2654391774f8e398`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/sessions/index.md
- **section**: Wrap with encryption and TTL › Operational patterns › Memory persistence
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> does agents sdk session memory survive a process restart or is it just in ram

**Answer**: In-memory `SQLiteSession("id")` is temporary (does not survive process restart). Pass a SQLite file path (or Redis/SQLAlchemy) for persistence.

**Atomic claims**:
  - In-memory SQLiteSession("session_id") is for temporary conversations.
  - File-based SQLiteSession("session_id", "path/to/db.sqlite") is for persistent conversations.

**Critical strings**: `in-memory SQLite`, `temporary conversations`, `file-based SQLite`, `persistent conversations`

### Evidence E1 (verbatim, authoritative)

`ver_b275f1db2ff0a82e2654391774f8e398` chars 21891–22079 · hash `01f834cf0e14f6755bb7719077cbcc104703898961a1276badaa2a1b5f090ba6`

```
Use in-memory SQLite (`SQLiteSession("session_id")`) for temporary conversations
-   Use file-based SQLite (`SQLiteSession("session_id", "path/to/db.sqlite")`) for persistent conversations
```

<details><summary>Context before (short)</summary>

```

# Create underlying session
underlying_session = SQLAlchemySession.from_url(
    "user_123",
    url="sqlite+aiosqlite:///conversations.db",
    create_tables=True
)

# Wrap with encryption and TTL
session = EncryptedSession(
    session_id="user_123",
    underlying_session=underlying_session,
    encryption_key="your-secret-key",
    ttl=600  # 10 minutes
)

result = await Runner.run(agent, "He…
```

</details>

<details><summary>Context after (short)</summary>

```

-   Use async SQLite (`AsyncSQLiteSession("session_id", db_path="...")`) when you need an `aiosqlite`-based implementation
-   Use Redis-backed sessions (`RedisSession.from_url("session_id", url="redis://...")`) for shared, low-latency session memory
-   Use SQLAlchemy-powered sessions (`SQLAlchemySession("session_id", engine=engine, create_tables=True)`) for production systems with existing data…
```

</details>

---
## NATQ-C-005

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Human-in-the-loop
- **version_id**: `ver_ae3bfcc42c733c5051abda30f0f6db07`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/human_in_the_loop.md
- **section**: Human-in-the-loop › Marking tools that need approval
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> how do I require a human to approve a tool before the agents sdk actually runs it, like delete_user

**Answer**: Mark the tool with `needs_approval=True` (or a per-call callable). The run pauses until a human approves, e.g. `@tool(needs_approval=True)` on delete_user-style tools.

**Atomic claims**:
  - Set needs_approval to True to always require approval, or provide an async function that decides per call.

**Critical strings**: `needs_approval`, `True`, `require approval`

### Evidence E1 (verbatim, authoritative)

`ver_ae3bfcc42c733c5051abda30f0f6db07` chars 1327–1436 · hash `72cb1e104a68797ed1296cfed17b04ba519cd1890449a2e5542f4ed36ad4e836`

```
Set `needs_approval` to `True` to always require approval or provide an async function that decides per call.
```

<details><summary>Context before (short)</summary>

```
s when the tool belongs to the current agent, to an agent reached through a handoff, or to a nested [`Agent.as_tool()`][agents.agent.Agent.as_tool] execution. In the nested `Agent.as_tool()` case, the interruption still surfaces on the outer run, so you approve or reject it on the outer `RunState` and resume the original top-level run.

With `Agent.as_tool()`, approvals can happen at two different…
```

</details>

<details><summary>Context after (short)</summary>

```
 The callable receives the run context, parsed tool parameters, and the tool call ID.

Callable approval rules fail closed when the SDK cannot safely inspect the arguments. If the arguments are malformed JSON, are valid JSON but not an object (for example, `null` or a list), or contain non-standard constants such as `NaN`, `Infinity`, or `-Infinity`, the callable is not invoked and the call requir…
```

</details>

---
## NATQ-C-006

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Tracing
- **version_id**: `ver_6b90217721b841b1329f51ec1caab139`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/tracing.md
- **section**: Tracing
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> agents sdk tracing default on or off?

**Answer**: On by default. Disable with `OPENAI_AGENTS_DISABLE_TRACING=1`, `set_tracing_disabled(True)`, or `RunConfig.tracing_disabled=True`.

**Atomic claims**:
  - Tracing is enabled by default.
  - Disable globally via OPENAI_AGENTS_DISABLE_TRACING=1 or set_tracing_disabled(True).
  - Disable per run via RunConfig.tracing_disabled=True.

**Critical strings**: `enabled by default`, `OPENAI_AGENTS_DISABLE_TRACING=1`, `set_tracing_disabled`

### Evidence E1 (verbatim, authoritative)

`ver_6b90217721b841b1329f51ec1caab139` chars 375–770 · hash `93d581b123a25258305ebb18e567abccd6fcd642f18d7af62fec8aaf11002c9b`

```
Tracing is enabled by default. You can disable it in three common ways:

    1. You can globally disable tracing by setting the env var `OPENAI_AGENTS_DISABLE_TRACING=1`
    2. You can globally disable tracing in code with [`set_tracing_disabled(True)`][agents.set_tracing_disabled]
    3. You can disable tracing for a single run by setting [`agents.run.RunConfig.tracing_disabled`][] to `True`
```

<details><summary>Context before (short)</summary>

```
# Tracing

The Agents SDK includes built-in tracing, collecting a comprehensive record of events during an agent run: LLM generations, tool calls, handoffs, guardrails, and even custom events that occur. Using the [Traces dashboard](https://platform.openai.com/traces), you can debug, visualize, and monitor your workflows during development and in production.

!!!note

    
```

</details>

<details><summary>Context after (short)</summary>

```


***Tracing is unavailable for organizations that use OpenAI's APIs under a Zero Data Retention (ZDR) policy.***

## Traces and spans

-   **Traces** represent a single end-to-end operation of a "workflow". They're composed of Spans. Traces have the following properties:
    -   `workflow_name`: This is the name of the logical workflow or app. For example "Code generation" or "Customer service".
…
```

</details>

---
## NATQ-C-008

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Tools
- **version_id**: `ver_cbeb36b7cf9a5e241940a011629b6f1b`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/tools.md
- **section**: Annotated form › Handling errors in function tools
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> if a tool function raises, does the agent run die or get the traceback as a tool result

**Answer**: By default the run does not die: `default_tool_error_function` sends an error string to the LLM as the tool result. Pass `failure_error_function=None` to re-raise.

**Atomic claims**:
  - Default failure_error_function runs default_tool_error_function which tells the LLM an error occurred.
  - If you explicitly pass None, tool call errors are re-raised.

**Critical strings**: `default_tool_error_function`, `tells the LLM an error occurred`, `re-raised`

### Evidence E1 (verbatim, authoritative)

`ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 29934–30254 · hash `ba8d1c433ee1e7b6bd16d62f746153c3d755fdb3d6a2296e9b81105bb6b10768`

```
By default (i.e. if you don't pass anything), it runs a `default_tool_error_function` which tells the LLM an error occurred.
-   If you pass your own error function, it runs that instead, and sends the response to the LLM.
-   If you explicitly pass `None`, then any tool call errors will be re-raised for you to handle.
```

<details><summary>Context before (short)</summary>

````
ror] and fail the run.
-   `timeout_error_function=...`: customize the timeout message when using `error_as_result`.

```python
import asyncio
from agents import Agent, Runner, ToolTimeoutError
from agents.decorators import tool


@tool(timeout=1.5, timeout_behavior="raise_exception")
async def slow_tool() -> str:
    await asyncio.sleep(5)
    return "done"


agent = Agent(name="Timeout hard-fail…
````

</details>

<details><summary>Context after (short)</summary>

````
 This could be a `ModelBehaviorError` if the model produced invalid JSON, or a `UserError` if your code crashed, etc.

```python
from agents import RunContextWrapper
from agents.decorators import tool
from typing import Any

def my_custom_error_function(context: RunContextWrapper[Any], error: Exception) -> str:
    """A custom function to provide a user-friendly error message."""
    print(f"A too…
````

</details>

---
## NATQ-C-009

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Models
- **version_id**: `ver_ae909bf8b4bbbe1d1a11119447f7ac94`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/models/index.md
- **section**: Models › Mixing models in one workflow
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> can two agents in one workflow use different models, like 4.1 for planning and a mini for extraction

**Answer**: Yes. Each `Agent` can take its own `model`; a workflow can use a smaller/faster model for one agent and a larger model for another.

**Atomic claims**:
  - Within a single workflow, you may want to use different models for each agent.
  - Example: smaller/faster model for triage and a larger, more capable model for complex tasks.

**Critical strings**: `single workflow`, `different models for each agent`, `triage`

### Evidence E1 (verbatim, authoritative)

`ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 23469–23670 · hash `165645db45dee8d706321754b7e51e378bbd076427b69e916b49da2b11388356`

```
Within a single workflow, you may want to use different models for each agent. For example, you could use a smaller, faster model for triage, while using a larger, more capable model for complex tasks.
```

<details><summary>Context before (short)</summary>

````
openai-agents-python/tree/main/examples/model_providers/custom_example_agent.py).

In cases where you do not have an API key from `platform.openai.com`, we recommend disabling tracing via `set_tracing_disabled()`, or setting up a [different tracing processor](../tracing.md).

``` python
from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled

set_tracing_disabled(di…
````

</details>

<details><summary>Context after (short)</summary>

```
 When configuring an [`Agent`][agents.Agent], you can select a specific model by either:

1. Passing the name of a model.
2. Passing any model name + a [`ModelProvider`][agents.models.interface.ModelProvider] that can map that name to a Model instance.
3. Directly providing a [`Model`][agents.models.interface.Model] implementation.

!!! note

    While our SDK supports both the [`OpenAIResponsesMo…
```

</details>

---
## NATQ-C-010

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Agents
- **version_id**: `ver_35cac5e98c151a17f941a6142d74709f`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/agents.md
- **section**: Agents › Output types
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> where do I hang the pydantic model for an agent's final output — Agent or Runner

**Answer**: Hang the Pydantic model on `Agent(..., output_type=...)`, not on `Runner`.

**Atomic claims**:
  - Use the output_type parameter on the agent to produce a particular output type.
  - Example Agent(..., output_type=CalendarEvent) where CalendarEvent is a Pydantic model.

**Critical strings**: `output_type`, `CalendarEvent`, `Agent`

### Evidence E1 (verbatim, authoritative)

`ver_35cac5e98c151a17f941a6142d74709f` chars 6517–7144 · hash `8825853a3b6c2be644311fbbb4f1cbd583f34016d268002d5a51c0a0da9a6984`

````
If you want the agent to produce a particular type of output, you can use the `output_type` parameter. A common choice is to use [Pydantic](https://docs.pydantic.dev/) objects, but we support any type that can be wrapped in a Pydantic [TypeAdapter](https://docs.pydantic.dev/latest/api/type_adapter/) - dataclasses, lists, TypedDict, etc.

```python
from pydantic import BaseModel
from agents import Agent


class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

agent = Agent(
    name="Calendar extractor",
    instructions="Extract calendar events from text",
    output_type=CalendarEvent,
````

<details><summary>Context before (short)</summary>

````
em_style="limerick"),
)
```

## Context

Agents are generic on their `context` type. Context is a dependency-injection tool: it's an object you create and pass to `Runner.run()`, that is passed to every agent, tool, handoff etc, and it serves as a grab bag of dependencies and state for the agent run. You can provide any Python object as the context.

Read the [context guide](context.md) for the fu…
````

</details>

<details><summary>Context after (short)</summary>

````

)
```

!!! note

    When you pass an `output_type`, that tells the model to use [structured outputs](https://platform.openai.com/docs/guides/structured-outputs) instead of regular plain text responses.

## Multi-agent system design patterns

There are many ways to design multi‑agent systems, but we commonly see two broadly applicable patterns:

1. Manager (agents as tools): A central manager/orc…
````

</details>

---
## NATQ-C-011

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Guardrails
- **version_id**: `ver_f22fbd5c504fa28a4e70440337e4a495`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/guardrails.md
- **section**: Guardrails › Tripwires
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> agents sdk guardrails: do input and output guardrails both halt the run

**Answer**: Yes for both: an input or output tripwire makes the runner raise `InputGuardrailTripwireTriggered` or `OutputGuardrailTripwireTriggered` and halt the run.

**Atomic claims**:
  - Input or output guardrail failure can signal a tripwire.
  - The runner immediately raises InputGuardrailTripwireTriggered or OutputGuardrailTripwireTriggered and halts agent execution.

**Critical strings**: `tripwire`, `InputGuardrailTripwireTriggered`, `OutputGuardrailTripwireTriggered`, `halts agent execution`

### Evidence E1 (verbatim, authoritative)

`ver_f22fbd5c504fa28a4e70440337e4a495` chars 7131–7366 · hash `47e0c4494efe526c5de31381bfddcfdf6a22c01cdb915e9b66daf6434e25d300`

```
If an agent input or output fails a guardrail, the guardrail can signal this with a tripwire. The runner immediately raises an `InputGuardrailTripwireTriggered` or `OutputGuardrailTripwireTriggered` exception and halts agent execution.
```

<details><summary>Context before (short)</summary>

```
.run.ToolExecutionConfig] when you want those input checks to run before the pending approval interruption is emitted. Calls that pass this pre-approval check are still checked again after approval before the tool executes.
- Tool guardrails apply only to function tools created with [`function_tool`][agents.tool.function_tool]. Handoffs run through the SDK's handoff pipeline rather than the normal…
```

</details>

<details><summary>Context after (short)</summary>

```
 Tool guardrails use the corresponding `ToolInputGuardrailTripwireTriggered` and `ToolOutputGuardrailTripwireTriggered` exceptions.

For agent-level tripwires, the exception's `guardrail_result` identifies the guardrail that triggered the tripwire. For an input tripwire raised by the runner, `exception.run_data.input_guardrail_results` contains every input guardrail result completed before the run…
```

</details>

---
## NATQ-C-012

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Context management
- **version_id**: `ver_fef74b4dda29e84a533c3e83f753effd`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/context.md
- **section**: Context management
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> how do I pass extra context into a tool without stuffing it into the LLM prompt

**Answer**: Pass a Python object as `Runner.run(..., context=...)`. Tools get it via `RunContextWrapper`. That local context is for your code, not automatically stuffed into the LLM prompt (LLM context is a separate class: what the model sees).

**Atomic claims**:
  - Local context is data/dependencies for tool functions, not the LLM-visible class of context.
  - Pass the object to Runner.run(..., context=whatever); tools receive RunContextWrapper[T].

**Critical strings**: `locally to your code`, `tool functions`, `Runner.run(..., context=whatever)`, `RunContextWrapper`

### Evidence E1 (verbatim, authoritative)

`ver_fef74b4dda29e84a533c3e83f753effd` chars 114–371 · hash `66b85e901f8cb00964dd68378b0d5fe889e0be3cf200d568f72a8c290947718f`

```
1. Context available locally to your code: this is data and dependencies you might need when tool functions run, during callbacks like `on_handoff`, in lifecycle hooks, etc.
2. Context available to LLMs: this is data the LLM sees when generating a response.
```

<details><summary>Context before (short)</summary>

```
# Context management

Context is an overloaded term. There are two main classes of context you might care about:

```

</details>

<details><summary>Context after (short)</summary>

```


## Local context

This is represented via the [`RunContextWrapper`][agents.run_context.RunContextWrapper] class and the [`context`][agents.run_context.RunContextWrapper.context] property within it. The way this works is:

1. You create any Python object you want. A common pattern is to use a dataclass or a Pydantic object.
2. You pass that object to the various run methods (e.g. `Runner.run(...,…
```

</details>

### Evidence E2 (verbatim, authoritative)

`ver_fef74b4dda29e84a533c3e83f753effd` chars 701–946 · hash `a2f35a5204bd7fb38bb6d7b685cfe3a1d2882f45ba177fb0b01f2f9fbb4db652`

```
You pass that object to the various run methods (e.g. `Runner.run(..., context=whatever)`).
3. All your tool calls, lifecycle hooks etc will be passed a wrapper object, `RunContextWrapper[T]`, where `T` represents the type of your context object
```

---
## NATQ-C-013

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Models
- **version_id**: `ver_ae909bf8b4bbbe1d1a11119447f7ac94`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/models/index.md
- **section**: Models › OpenAI models › Hosted multi-agent (experimental)
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> is there a hosted runner for openai agents or is the sdk local-only

**Answer**: Not purely local-only: experimental hosted multi-agent runs server-hosted subagents. The SDK still uses its normal local `Runner`; hosted orchestration stays on the service and your function tools run in your app.

**Atomic claims**:
  - Hosted multi-agent beta coordinates server-hosted subagents.
  - The Agents SDK keeps using its normal Runner; hosted orchestration stays on the service; function tools execute in your application.

**Critical strings**: `server-hosted subagents`, `normal `Runner``, `hosted orchestration`

### Evidence E1 (verbatim, authoritative)

`ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 14876–15159 · hash `f8297d9f08ee41ffb0a4c14a5c22bcaa9799c966bcbb055c98c08da2fa85086e`

```
The OpenAI Responses API hosted multi-agent beta lets a GPT-5.6 root model create and coordinate server-hosted subagents. The Agents SDK can keep using its normal `Runner`: hosted orchestration stays on the service, while developer-defined function tools execute in your application.
```

<details><summary>Context before (short)</summary>

```
rs, set `responses_websocket_options={"max_size": 8 * 1024 * 1024}` to bound per-message memory usage.
-   The [Responses API WebSocket service](https://developers.openai.com/api/docs/guides/websocket-mode) processes one response at a time on each connection and limits each connection to 60 minutes. Open a new connection after that limit; use multiple connections when you need parallel runs.
-   T…
```

</details>

<details><summary>Context after (short)</summary>

```


This integration is experimental and uses the Responses WebSocket transport so local function outputs can be returned to an active hosted agent with `response.inject`. It requires a build of `openai[realtime]` version 2.45.0 or later that exposes `client.beta.responses.connect`. The interface and beta item schemas may change before general availability.

#### Configure the model

Import the mode…
```

</details>

---
## NATQ-C-014

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Tools
- **version_id**: `ver_cbeb36b7cf9a5e241940a011629b6f1b`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/tools.md
- **section**: Annotated form › Agents as tools
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> can I nest an agent as a tool, like one agent calling another as a function

**Answer**: Yes. Model nested agents as tools (`as_tool`) so one agent calls another as a function instead of a handoff.

**Atomic claims**:
  - A central agent can orchestrate specialized agents instead of handing off control.
  - You do this by modeling agents as tools.

**Critical strings**: `agents as tools`, `instead of handing off control`

### Evidence E1 (verbatim, authoritative)

`ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 31350–31522 · hash `46173393ea157969ac221c5be74b31fb7bfcf0b5e994b1ac6ba3f46fbd6e92e3`

```
In some workflows, you may want a central agent to orchestrate a network of specialized agents, instead of handing off control. You can do this by modeling agents as tools.
```

<details><summary>Context before (short)</summary>

```
tool
from typing import Any

def my_custom_error_function(context: RunContextWrapper[Any], error: Exception) -> str:
    """A custom function to provide a user-friendly error message."""
    print(f"A tool call failed with the following error: {error}")
    return "An internal server error occurred. Please try again later."

@tool(failure_error_function=my_custom_error_function)
def get_user_profi…
```

</details>

<details><summary>Context after (short)</summary>

````


```python
import asyncio

from agents import Agent, Runner

spanish_agent = Agent(
    name="Spanish agent",
    instructions="You translate the user's message to Spanish",
)

french_agent = Agent(
    name="French agent",
    instructions="You translate the user's message to French",
)

orchestrator_agent = Agent(
    name="orchestrator_agent",
    instructions=(
        "You are a translation …
````

</details>

---
## NATQ-C-015

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Running agents
- **version_id**: `ver_2c60e99cfd929a738910b893fd6f1a40`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/running_agents.md
- **section**: Running agents › Exceptions
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> max turns on Runner.run, what error do I get when it hits the cap

**Answer**: You get `MaxTurnsExceeded` when the run exceeds `max_turns` on `Runner.run` / `run_sync` / `run_streamed`.

**Atomic claims**:
  - MaxTurnsExceeded is raised when the agent's run exceeds the max_turns limit passed to Runner.run, Runner.run_sync, or Runner.run_streamed.

**Critical strings**: `MaxTurnsExceeded`, `max_turns`, `Runner.run`

### Evidence E1 (verbatim, authoritative)

`ver_2c60e99cfd929a738910b893fd6f1a40` chars 33540–33754 · hash `a377941d599d150a1dd268d2926ab6459940a247142d0f0af1bd799de8c95d1d`

```
[`MaxTurnsExceeded`][agents.exceptions.MaxTurnsExceeded]: This exception is raised when the agent's run exceeds the `max_turns` limit passed to the `Runner.run`, `Runner.run_sync`, or `Runner.run_streamed` methods.
```

<details><summary>Context before (short)</summary>

```
d-openai-sdk) or view the [docs](https://docs.restate.dev/ai) for more details.

### DBOS

You can use the Agents SDK [DBOS](https://dbos.dev/) integration to run reliable agents that preserve progress across failures and restarts. It supports long-running agents, human-in-the-loop workflows, and handoffs. It supports both sync and async methods. The integration requires only a SQLite or Postgres …
```

</details>

<details><summary>Context after (short)</summary>

```
 It indicates that the agent could not complete its task within the specified number of agent-loop turns (LLM calls). Set `max_turns=None` to disable the limit.
-   [`ModelTimeoutError`][agents.exceptions.ModelTimeoutError]: This exception is raised when a model-call attempt exceeds [`ModelSettings.timeout`][agents.model_settings.ModelSettings.timeout]. See [Model-call timeouts](models/index.md#mo…
```

</details>

---
## NATQ-C-016

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Using the Messages API
- **version_id**: `ver_d7be262221efc52378af14916e203df8`
- **url**: https://platform.claude.com/docs/en/build-with-claude/working-with-messages
- **section**: Multiple conversational turns › System role in messages
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> claude messages api, do I still send system as a role in messages or is it the top-level system field

**Answer**: Put start-of-conversation instructions in the top-level `system` field, not as the first `messages` item. On some newer models you may also send later `"role": "system"` messages after a user turn.

**Atomic claims**:
  - A system message cannot be the first entry in messages; use the top-level system field for instructions from the start.
  - Use top-level system for first-turn instructions and a mid-conversation system message for later instructions.

**Critical strings**: `top-level `system` field`, `role": "system"`, `cannot be the first entry`

### Evidence E1 (verbatim, authoritative)

`ver_d7be262221efc52378af14916e203df8` chars 10028–10561 · hash `2c87e048a56535c6a64d46fad90542c91fe8344e734c7b187d4ad8681573a227`

```
A `system` message cannot be the first entry in `messages`; use the top-level `system` field for instructions that apply from the start.

A mid-conversation system message has the same authority as the top-level `system` field, but because it is appended to the end of the message history, it does not invalidate any cached prefix that came before it. Use the top-level `system` field for instructions that should apply from the very first turn, and a mid-conversation system message for instructions that only become relevant later.
```

<details><summary>Context before (short)</summary>

````
"assistant", content: "Hello!" },
      { role: "user", content: "Can you describe LLMs to me?" }
    ]
  )
  puts message
  ```
</CodeGroup>

```json Output
{
  "id": "msg_018gCsTGsXkYJVqYPxTgDHBU",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Sure, I'd be happy to provide..."
    }
  ],
  "model": "claude-opus-5",
  "stop_reason": "end_tur…
````

</details>

<details><summary>Context after (short)</summary>

```


See [Mid-conversation system messages](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages) for the complete guide, including how to combine it with [prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).

## Prefilling Claude's response

You can pre-fill part of Claude's response in the last position of the input messages list. …
```

</details>

---
## NATQ-C-017

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Prompt caching
- **version_id**: `ver_7947433dfde6b3b8eccd0faa597c3c9a`
- **url**: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- **section**: Caching strategies and considerations › What can be cached
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic prompt caching — do I mark the system prompt, the tools, or both

**Answer**: Both. Tool definitions and system blocks can be cached. Prefixes are created in order `tools`, then `system`, then `messages`; mark breakpoints with `cache_control`.

**Atomic claims**:
  - Tools (tool definitions in the tools array) can be cached.
  - System messages (content blocks in the system array) can be cached.
  - Cache prefixes are created in the order tools, system, then messages.

**Critical strings**: `tools array`, `system array`, `tools`, `system`, then `messages``

### Evidence E1 (verbatim, authoritative)

`ver_7947433dfde6b3b8eccd0faa597c3c9a` chars 32663–32765 · hash `5dda6be920e7e2fa10f267c2cf3d5e21dcbff2f12a57a7048be922583b568277`

```
* Tools: Tool definitions in the `tools` array
* System messages: Content blocks in the `system` array
```

<details><summary>Context before (short)</summary>

```
en worthwhile. Cache reads cost significantly less than uncached input tokens, so reaching the minimum can reduce costs for frequently reused prompts.

<Note>
  [Bedrock](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock) is an AWS-operated platform. On Bedrock, see the [Bedrock prompt caching documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-c…
```

</details>

<details><summary>Context after (short)</summary>

```

* Text messages: Content blocks in the `messages.content` array, for both user and assistant turns
* Images & Documents: Content blocks in the `messages.content` array, in user turns
* Tool use and tool results: Content blocks in the `messages.content` array, in both user and assistant turns

Each of these elements can be cached, either automatically or by marking them with `cache_control`.

### …
```

</details>

### Evidence E2 (verbatim, authoritative)

`ver_7947433dfde6b3b8eccd0faa597c3c9a` chars 24246–24409 · hash `4e8612ae8853426308d73e681ca9aa67c22e10200823e2cc22a3810b185be863`

```
Cache prefixes are created in the following order: `tools`, `system`, then `messages`. This order forms a hierarchy where each level builds upon the previous ones.
```

---
## NATQ-C-019

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Thinking
- **version_id**: `ver_012b734775e7edb2649d3a9ddfd93070`
- **url**: https://platform.claude.com/docs/en/build-with-claude/thinking
- **section**: Configuring thinking
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> extended thinking on claude — do thinking tokens count against max_tokens

**Answer**: Yes. Thinking tokens count toward `max_tokens`; raise `max_tokens` to cover thinking plus the visible response.

**Atomic claims**:
  - Thinking tokens count toward max_tokens.
  - Set max_tokens high enough for both thinking and response text.

**Critical strings**: `Thinking tokens count toward `max_tokens``

### Evidence E1 (verbatim, authoritative)

`ver_012b734775e7edb2649d3a9ddfd93070` chars 11240–11363 · hash `ec3cf91f5001e176eab2aff4ea05bf0947303e7b893aa2e62ecdd5d78bd3f087`

```
Thinking tokens count toward `max_tokens`, so set it high enough to leave room for both the thinking and the response text.
```

<details><summary>Context before (short)</summary>

```
ock->text;
      }
  }
  ```

  ```ruby Ruby
  client = Anthropic::Client.new

  message = client.messages.create(
    model: "claude-opus-4-8",
    max_tokens: 16000,
    thinking: {
      type: "adaptive",
      display: "summarized"
    },
    messages: [
      {
        role: "user",
        content: "What is the greatest common divisor of 1071 and 462?"
      }
    ]
  )

  message.content.ea…
```

</details>

<details><summary>Context after (short)</summary>

```
 See [Cost control](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost#cost-control) on the steering page and [Thinking and the context window](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-and-the-context-window).

### Turning thinking off

On Claude Sonnet 5, where thinking is on by default, you can turn it off:

<CodeGroup>
  ```bash cURL
…
```

</details>

---
## NATQ-C-021

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Computer use tool
- **version_id**: `ver_d9ba3ab0d872dd86047c7ed6dc783235`
- **url**: https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool
- **section**: Quick start
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic computer use, which tool type name do I actually send in the tools array

**Answer**: Send `type: "computer_20251124"` (versioned computer-use type) with `name: "computer"` in the tools array.

**Atomic claims**:
  - The tools array uses type computer_20251124.
  - The name is computer.

**Critical strings**: `computer_20251124`, `"name": "computer"`

### Evidence E1 (verbatim, authoritative)

`ver_d9ba3ab0d872dd86047c7ed6dc783235` chars 5301–5358 · hash `08ba75c134aa4b28ae7e00db4a2e1097a3cf6ccb4aa77a3e15b8d2f89c77ef35`

```
"type": "computer_20251124",
          "name": "computer"
```

<details><summary>Context before (short)</summary>

```
 with the classifier defense layer in place.

Inform end users of relevant risks and obtain their consent prior to enabling computer use in your own products.

<Card title="Computer use reference implementation" icon="computer" href="https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo">
  Get started with the computer use reference implementation that includes a web int…
```

</details>

<details><summary>Context after (short)</summary>

```
,
          "display_width_px": 1024,
          "display_height_px": 768,
          "display_number": 1
        },
        {
          "type": "text_editor_20250728",
          "name": "str_replace_based_edit_tool"
        },
        {
          "type": "bash_20250124",
          "name": "bash"
        }
      ],
      "messages": [
        {
          "role": "user",
          "content": "Save a …
```

</details>

---
## NATQ-C-022

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: PDF support
- **version_id**: `ver_31cd12f6d13c8ac47666eb1a55874e5d`
- **url**: https://platform.claude.com/docs/en/build-with-claude/pdf-support
- **section**: Process PDFs with Claude › Send your first PDF request
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> claude pdfs — is that a document content block or do I still stuff base64 in an image

**Answer**: Use a `document` content block (URL, base64 PDF, or `file_id`), not an image block.

**Atomic claims**:
  - PDFs are provided as a URL, as a base64-encoded PDF in document content blocks, or by file_id.

**Critical strings**: `document content blocks`, `base64-encoded PDF`

### Evidence E1 (verbatim, authoritative)

`ver_31cd12f6d13c8ac47666eb1a55874e5d` chars 5452–5599 · hash `61c25c0f9fdbad9598b74aaf97b1d475b846b8d15d61f11ae099a9398933d6aa`

```
You can provide PDFs to Claude in three ways:

1. As a URL reference to a PDF hosted online
2. As a base64-encoded PDF in `document` content blocks
```

<details><summary>Context before (short)</summary>

```
r charts in your PDFs when using the Converse API, you likely need to enable the citations flag. Without it, Converse falls back to basic text extraction only.

<Note>
  This is a known constraint with the Converse API. For applications that require visual PDF analysis without citations, consider using the InvokeModel API instead.
</Note>

<Note>
  Plain text files such as .txt, .csv, or .md can b…
```

</details>

<details><summary>Context after (short)</summary>

```

3. By a `file_id` from the [Files API](https://platform.claude.com/docs/en/build-with-claude/files)

<Note>
  On Amazon Bedrock and Google Cloud, only base64-encoded sources are currently available. On Microsoft Foundry, the Files API is not supported for deployments hosted on Azure.
</Note>

#### Option 1: URL-based PDF document

The simplest approach is to reference a PDF directly from a URL:

…
```

</details>

---
## NATQ-C-023

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Prompt caching
- **version_id**: `ver_7947433dfde6b3b8eccd0faa597c3c9a`
- **url**: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- **section**: Automatic caching › TTL support
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> does anthropic cache input cheaper on the second request, and is there a 5 min vs 1 hr ttl

**Answer**: Yes: cache reads are 0.1× base input. Default TTL is 5 minutes (writes 1.25×); optional 1-hour TTL writes at 2×.

**Atomic claims**:
  - Default automatic caching TTL is 5 minutes.
  - A 1-hour TTL is available at 2x base input token price.
  - Cache read tokens are 0.1 times the base input tokens price.
  - 5-minute cache write tokens are 1.25 times the base input tokens price.

**Critical strings**: `5-minute TTL`, `1-hour TTL`, `0.1 times`, `1.25 times`

### Evidence E1 (verbatim, authoritative)

`ver_7947433dfde6b3b8eccd0faa597c3c9a` chars 21514–21627 · hash `028b0951e455d3264104c13c96e8d4aa542e805597c55c551142777e2df11283`

```
By default, automatic caching uses a 5-minute TTL. You can specify a 1-hour TTL at 2x the base input token price:
```

<details><summary>Context before (short)</summary>

```
-------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Request 1 | System + User(1) + Asst(1) + **User(2)** ◀ cache                                         | Everything written to cache                                                |
| Request 2 | System + User(1) + Asst(1) + User(2) +…
```

</details>

<details><summary>Context after (short)</summary>

````


```json
{ "cache_control": { "type": "ephemeral", "ttl": "1h" } }
```

### Combining with block-level caching

Automatic caching is compatible with [explicit cache breakpoints](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#explicit-cache-breakpoints). When used together, the automatic cache breakpoint uses one of the 4 available breakpoint slots.

This lets you combine bot…
````

</details>

### Evidence E2 (verbatim, authoritative)

`ver_7947433dfde6b3b8eccd0faa597c3c9a` chars 12929–13135 · hash `81ca6ba945a645dc792909ab6b0294db093a02bc0dd33ddb38e80f5aad6817a6`

```
* 5-minute cache write tokens are 1.25 times the base input tokens price
  * 1-hour cache write tokens are 2 times the base input tokens price
  * Cache read tokens are 0.1 times the base input tokens price
```

---
## NATQ-C-025

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Models
- **version_id**: `ver_ffe1fe20eccb89591ccddc867fa1ed65`
- **url**: https://platform.claude.com/docs/en/api/models
- **section**: Models › List Models › Example
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic-version header still 2023-06-01??

**Answer**: Yes — current API-reference examples in this snapshot still send `anthropic-version: 2023-06-01`.

**Atomic claims**:
  - List Models curl example uses anthropic-version: 2023-06-01.

**Critical strings**: `anthropic-version: 2023-06-01`

### Evidence E1 (verbatim, authoritative)

`ver_ffe1fe20eccb89591ccddc867fa1ed65` chars 5742–5776 · hash `59e99ce31eccb98a7e219e3f7d05b32b1b5b14dd1d908eae323334554460bc72`

```
-H 'anthropic-version: 2023-06-01'
```

<details><summary>Context before (short)</summary>

```
tetime string representing the time at which the model was released. May be set to an epoch value if the release date is unknown.

  - `display_name: string`

    A human-readable name for the model.

  - `max_input_tokens: number or null`

    Maximum input context window size in tokens for this model.

  - `max_tokens: number or null`

    Maximum value for the `max_tokens` parameter when using …
```

</details>

<details><summary>Context after (short)</summary>

````
 \
    -H "X-Api-Key: $ANTHROPIC_API_KEY"
```

#### Response

```json
{
  "data": [
    {
      "id": "claude-opus-4-6",
      "capabilities": {
        "batch": {
          "supported": true
        },
        "citations": {
          "supported": true
        },
        "code_execution": {
          "supported": true
        },
        "context_management": {
          "clear_thinking_20251015":…
````

</details>

---
## NATQ-C-026

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Citations
- **version_id**: `ver_77dd930ea597c30fc512a8f92f8e802d`
- **url**: https://platform.claude.com/docs/en/build-with-claude/citations
- **section**: Preamble
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> claude citations / grounded answers — is that a tool or a response format

**Answer**: A document/response feature, not a tool. Enable with `citations: { enabled: true }` on a `document` block; cited passages come back on the response text blocks.

**Atomic claims**:
  - Citations ground responses in source documents and return exact supporting passages.
  - Enabled on a document block via citations.enabled true.

**Critical strings**: `Citations`, `source documents`, `citations": { "enabled": true }`

### Evidence E1 (verbatim, authoritative)

`ver_77dd930ea597c30fc512a8f92f8e802d` chars 103–276 · hash `6ac91ad79f18dbbec19d9b779cf16c3a621731cd679f572bfbee678cf2c1360e`

```
Ground Claude's responses in your source documents. Citations return the exact passages that support each claim, so you can verify answers and surface sources to your users.
```

<details><summary>Context before (short)</summary>

```
---
title: Citations
url: https://platform.claude.com/docs/en/build-with-claude/citations
description: 
```

</details>

<details><summary>Context after (short)</summary>

```

---

## Compatibility
- [ZDR](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention): eligible (excludes [Covered Models](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention#model-specific-data-retention-requirements))
- Platforms: Claude API, Claude Platform on AWS, Amazon Bedrock, Google Cloud, Microsoft Foundry

Claude can provide detailed citations when…
```

</details>

### Evidence E2 (verbatim, authoritative)

`ver_77dd930ea597c30fc512a8f92f8e802d` chars 26711–26743 · hash `4267f2e963523ff0e3359002f395268fa725adeeb54935c7defa9e78a2df4bb2`

```
"citations": { "enabled": true }
```

---
## NATQ-C-027

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Token counting
- **version_id**: `ver_76c80d3d80b12ae7870092b39f1832f1`
- **url**: https://platform.claude.com/docs/en/build-with-claude/token-counting
- **section**: How to count message tokens › Count tokens in basic messages
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> token counting for anthropic, is it count_tokens or messages/count_tokens

**Answer**: The HTTP path is `POST /v1/messages/count_tokens` (SDK: `client.messages.count_tokens`), not a bare `count_tokens` root.

**Atomic claims**:
  - Token counting HTTP path is /v1/messages/count_tokens.
  - Python SDK method is client.messages.count_tokens(.

**Critical strings**: `/v1/messages/count_tokens`, `client.messages.count_tokens`

### Evidence E1 (verbatim, authoritative)

`ver_76c80d3d80b12ae7870092b39f1832f1` chars 2431–3063 · hash `3602e6819b2d9d31328be683981559dceaca6e6a583f950837bc51a47fb67ef5`

```
curl https://api.anthropic.com/v1/messages/count_tokens \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "content-type: application/json" \
    -H "anthropic-version: 2023-06-01" \
    -d '{
      "model": "claude-opus-5",
      "system": "You are a scientist",
      "messages": [{
        "role": "user",
        "content": "Hello, Claude"
      }]
    }'
  ```

  ```bash CLI
  ant messages count-tokens \
    --model claude-opus-5 \
    --system "You are a scientist" \
    --message '{role: user, content: "Hello, Claude"}'
  ```

  ```python Python
  client = anthropic.Anthropic()

  response = client.messages.count_tokens(
```

<details><summary>Context before (short)</summary>

```
*. In some cases, the actual number of input tokens used when creating a message might differ by a small amount.

  Token counts may include tokens added automatically by Anthropic for system optimizations. **You are not billed for system-added tokens**. Billing reflects only your content.
</Note>

### Supported models

All [active models](https://platform.claude.com/docs/en/about-claude/models/ov…
```

</details>

<details><summary>Context after (short)</summary>

```

      model="claude-opus-5",
      system="You are a scientist",
      messages=[{"role": "user", "content": "Hello, Claude"}],
  )

  print(response.json())
  ```

  ```typescript TypeScript
  const client = new Anthropic();

  const response = await client.messages.countTokens({
    model: "claude-opus-5",
    system: "You are a scientist",
    messages: [
      {
        role: "user",
        …
```

</details>

---
## NATQ-C-029

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Domain Types › Tool Choice Any
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic tool_choice — auto vs any vs tool vs none, what does any actually force

**Answer**: `tool_choice: {"type": "any"}` forces the model to use tools — specifically, it will use any available tool rather than answering without tools.

**Atomic claims**:
  - Tool Choice Any is ToolChoiceAny with type any.
  - The model will use any available tools.

**Critical strings**: `Tool Choice Any`, `ToolChoiceAny`, `any available tools`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 483099–483439 · hash `d6c428bb005c4b15cac7d4bf67394084592dc95c682bea3224bc082d1d0759ed`

```
### Tool Choice Any

- `ToolChoiceAny object { type, disable_parallel_tool_use }`

  The model will use any available tools.

  - `type: "any"`

    - `"any"`

  - `disable_parallel_tool_use: optional boolean`

    Whether to disable parallel tool use.

    Defaults to `false`. If set to `true`, the model will output exactly one tool use.
```

<details><summary>Context before (short)</summary>

```
e tool use.

  - `ToolChoiceAny object { type, disable_parallel_tool_use }`

    The model will use any available tools.

    - `type: "any"`

      - `"any"`

    - `disable_parallel_tool_use: optional boolean`

      Whether to disable parallel tool use.

      Defaults to `false`. If set to `true`, the model will output exactly one tool use.

  - `ToolChoiceTool object { name, type, disable_par…
```

</details>

<details><summary>Context after (short)</summary>

```


### Tool Choice Auto

- `ToolChoiceAuto object { type, disable_parallel_tool_use }`

  The model will automatically decide whether to use tools.

  - `type: "auto"`

    - `"auto"`

  - `disable_parallel_tool_use: optional boolean`

    Whether to disable parallel tool use.

    Defaults to `false`. If set to `true`, the model will output at most one tool use.

### Tool Choice None

- `ToolChoic…
```

</details>

---
## NATQ-C-030

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Create a Message › Returns
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> claude stop_reason pause_turn vs end_turn vs tool_use — when do I send the next request to resume

**Answer**: Resume `pause_turn` by sending the response back as-is. `end_turn` is a natural stop (do not resume). `tool_use` means tools were invoked — continue with `tool_result`s, not a pause resume.

**Atomic claims**:
  - end_turn: the model reached a natural stopping point.
  - tool_use: the model invoked one or more tools.
  - pause_turn: paused a long-running turn; provide the response back as-is in a subsequent request to continue.

**Critical strings**: `end_turn`, `tool_use`, `pause_turn`, `as-is`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 89070–89496 · hash `5ca0f474a72e4e48467b4e7cf30832c0342ebad20d5ad1897311bf3eaf02447c`

```
* `"end_turn"`: the model reached a natural stopping point
    * `"max_tokens"`: we exceeded the requested `max_tokens` or the model's maximum
    * `"stop_sequence"`: one of your provided custom `stop_sequences` was generated
    * `"tool_use"`: the model invoked one or more tools
    * `"pause_turn"`: we paused a long-running turn. You may provide the response back as-is in a subsequent request to let the model continue.
```

<details><summary>Context before (short)</summary>

```
s://www.anthropic.com/legal/commercial-terms). Benign machine learning work can also trigger this category.

      - `"reasoning_extraction"`

        The request asks the model to reproduce its internal reasoning in the response text. To get reasoning in a structured form instead, use [adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking).

      - `"general_…
```

</details>

<details><summary>Context after (short)</summary>

```

    * `"refusal"`: when streaming classifiers intervene to handle potential policy violations
    * `"model_context_window_exceeded"`: we exceeded the model's context window

    In non-streaming mode this value is always non-null. In streaming mode, it is null in the `message_start` event and non-null otherwise.

    - `"end_turn"`

    - `"max_tokens"`

    - `"stop_sequence"`

    - `"tool_use…
```

</details>

---
## NATQ-C-032

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Models
- **version_id**: `ver_ae909bf8b4bbbe1d1a11119447f7ac94`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/models/index.md
- **section**: Models › Advanced OpenAI Responses settings › Common advanced `ModelSettings` options
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> parallel_tool_calls off how — openai

**Answer**: Set `ModelSettings(parallel_tool_calls=False)` to forbid multiple tool calls in the same turn.

**Atomic claims**:
  - parallel_tool_calls allows or forbids multiple tool calls in the same turn.
  - Example sets parallel_tool_calls=False on ModelSettings.

**Critical strings**: `parallel_tool_calls`, `False`, `same turn`

### Evidence E1 (verbatim, authoritative)

`ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 26214–26290 · hash `a757f84a5fcf8a5b06f2de0a764d202e8b22b5f2f364b521f0101f7efd10132b`

```
`parallel_tool_calls`: Allow or forbid multiple tool calls in the same turn.
```

<details><summary>Context before (short)</summary>

````
main())
```

1.  Sets the name of an OpenAI model directly.
2.  Provides a [`Model`][agents.models.interface.Model] implementation.

When you want to further configure the model used for an agent, you can pass [`ModelSettings`][agents.model_settings.ModelSettings], which provides optional model configuration parameters such as temperature.

```python
from agents import Agent, ModelSettings

englis…
````

</details>

<details><summary>Context after (short)</summary>

```

- `truncation`: Set `"auto"` to let the Responses API drop the oldest conversation items instead of failing when context would overflow.
- `store`: Control whether the generated response is stored server-side for later retrieval. This matters for follow-up workflows that rely on response IDs, and for session compaction flows that may need to fall back to local input when `store=False`.
- `context…
```

</details>

### Evidence E2 (verbatim, authoritative)

`ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 27607–27633 · hash `e407d12789dd1ccc5d1b4c1dcc43a58c673ac94ff51c58ae41ed210e33996323`

```
parallel_tool_calls=False,
```

---
## NATQ-C-033

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Domain Types › Tool Choice Auto
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> claude disable parallel tools — I keep sending parallel_tool_calls=false like openai, what's the actual param

**Answer**: Use `tool_choice.disable_parallel_tool_use=true` (not OpenAI's `parallel_tool_calls`). That limits the model to at most one tool use.

**Atomic claims**:
  - ToolChoiceAuto includes disable_parallel_tool_use.
  - If disable_parallel_tool_use is true, the model will output at most one tool use.

**Critical strings**: `disable_parallel_tool_use`, `at most one tool use`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 483441–483803 · hash `46fac64529bde39968d9f6dd190828dc98fb8b866b0e1e93618da18987274d16`

```
### Tool Choice Auto

- `ToolChoiceAuto object { type, disable_parallel_tool_use }`

  The model will automatically decide whether to use tools.

  - `type: "auto"`

    - `"auto"`

  - `disable_parallel_tool_use: optional boolean`

    Whether to disable parallel tool use.

    Defaults to `false`. If set to `true`, the model will output at most one tool use.
```

<details><summary>Context before (short)</summary>

```
use.

  - `ToolChoiceTool object { name, type, disable_parallel_tool_use }`

    The model will use the specified tool with `tool_choice.name`.

    - `name: string`

      The name of the tool to use.

    - `type: "tool"`

      - `"tool"`

    - `disable_parallel_tool_use: optional boolean`

      Whether to disable parallel tool use.

      Defaults to `false`. If set to `true`, the model will…
```

</details>

<details><summary>Context after (short)</summary>

```


### Tool Choice None

- `ToolChoiceNone object { type }`

  The model will not be allowed to use tools.

  - `type: "none"`

    - `"none"`

### Tool Choice Tool

- `ToolChoiceTool object { name, type, disable_parallel_tool_use }`

  The model will use the specified tool with `tool_choice.name`.

  - `name: string`

    The name of the tool to use.

  - `type: "tool"`

    - `"tool"`

  - `disab…
```

</details>

---
## NATQ-C-043

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Concepts
- **version_id**: `ver_46f8ac47ff4cd52c9382f986727e0672`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/sandbox/guide.md
- **section**: Concepts › Common patterns › Combine with local tools and MCP
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> mcp tool vs native function tool on openai, can I mix them on one request

**Answer**: Yes. Ordinary/function tools and MCP servers can be on the same agent (`tools=[...]` plus `mcp_servers=[server]`).

**Atomic claims**:
  - You can use ordinary tools on the same agent as MCP.
  - Example sets tools=[get_discount_approval_path] and mcp_servers=[server].

**Critical strings**: `ordinary tools on the same agent`, `mcp_servers=[server]`

### Evidence E1 (verbatim, authoritative)

`ver_46f8ac47ff4cd52c9382f986727e0672` chars 48743–49113 · hash `14effe8e54a248a997bb17c1c3f2f4e8ac953d7d1414b1683c240b7b52be89e3`

````
Keep the sandbox workspace while still using ordinary tools on the same agent:

```python
from agents.sandbox import SandboxAgent
from agents.sandbox.capabilities import Shell

agent = SandboxAgent(
    name="Workspace reviewer",
    instructions="Inspect the workspace and call host tools when needed.",
    tools=[get_discount_approval_path],
    mcp_servers=[server],
````

<details><summary>Context before (short)</summary>

```
box.sandboxes.docker import DockerSandboxClient, DockerSandboxClientOptions

rollout_agent = SandboxAgent(
    name="Rollout Reviewer",
    instructions="Inspect the rollout packet and summarize implementation risk.",
)

rollout_agent.as_tool(
    tool_name="review_rollout_risk",
    tool_description="Inspect the rollout packet and summarize implementation risk.",
    run_config=RunConfig(
       …
```

</details>

<details><summary>Context after (short)</summary>

````

    capabilities=[Shell()],
)
```

Use this when workspace inspection is only one part of the agent's job. See [examples/sandbox/sandbox_agent_with_tools.py](https://github.com/openai/openai-agents-python/blob/main/examples/sandbox/sandbox_agent_with_tools.py).

## Memory

Use the `Memory` capability when future sandbox-agent runs should learn from prior runs. Memory is separate from the SDK's co…
````

</details>

---
## NATQ-C-044

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Bash tool
- **version_id**: `ver_9bf8513721dc2d1ef3e1ec42bf535dc6`
- **url**: https://platform.claude.com/docs/en/agents-and-tools/tool-use/bash-tool
- **section**: Tool versions
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic bash tool and text editor tool — are those built-in types or do I implement them

**Answer**: Built-in tool types you declare (`bash_20250124`, and the sibling text-editor type), but you still implement the client loop: run the command and return `tool_result`.

**Atomic claims**:
  - bash_20250124 is the current built-in bash tool type and requires no beta header.
  - Your application runs the command in its bash session after Claude returns tool_use.

**Critical strings**: `bash_20250124`, `Your application runs the command`, `tool_use`

### Evidence E1 (verbatim, authoritative)

`ver_9bf8513721dc2d1ef3e1ec42bf535dc6` chars 8308–8391 · hash `0fb5b2b6b9540ce984d156f3ac858414d8c391031619c12914705f617e95273b`

```
`bash_20250124` is the current version of the tool, and it requires no beta header.
```

<details><summary>Context before (short)</summary>

```
the schema is built into Claude's model and can't be modified. The following table lists the input fields Claude sets when it calls the tool.

| Parameter | Required | Description                               |
| --------- | -------- | ----------------------------------------- |
| `command` | Yes\*    | The bash command to run                   |
| `restart` | No       | Set to `true` to restart …
```

</details>

<details><summary>Context after (short)</summary>

```
 Every model from Claude Sonnet 3.7 ([retired](https://platform.claude.com/docs/en/about-claude/model-deprecations)) onward accepts it, including all current Claude models.

The original `bash_20241022` version is part of the computer use beta, and the October 2024 Claude Sonnet 3.5 release ([retired](https://platform.claude.com/docs/en/about-claude/model-deprecations)) is the only model that acce…
```

</details>

### Evidence E2 (verbatim, authoritative)

`ver_9bf8513721dc2d1ef3e1ec42bf535dc6` chars 6308–6435 · hash `b3d65e6e4717b3cef5e087ab1c9dd9708cc2fb1962a23ceeb663c905a0813c3c`

```
1. Claude returns a `tool_use` block containing the `command` to run.
2. Your application runs the command in its bash session.
```

---
## NATQ-C-047

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Tools
- **version_id**: `ver_cbeb36b7cf9a5e241940a011629b6f1b`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/tools.md
- **section**: Tools › Hosted tools
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> agents sdk hosted tools like web search, do I still implement an on_invoke callback

**Answer**: No. Hosted tools like `WebSearchTool` are OpenAI-managed built-ins you attach on the agent. `on_invoke_tool` is for custom `FunctionTool`s, not hosted web search.

**Atomic claims**:
  - OpenAI offers built-in hosted tools when using OpenAIResponsesModel.
  - WebSearchTool lets an agent search the web.

**Critical strings**: `built-in tools`, `WebSearchTool`

### Evidence E1 (verbatim, authoritative)

`ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 1524–1736 · hash `e09902a49d7762d5f509b1ee1cff7803a0491c191aa770b30c572688d38f0934`

```
OpenAI offers a few built-in tools when using the [`OpenAIResponsesModel`][agents.models.openai_responses.OpenAIResponsesModel]:

-   The [`WebSearchTool`][agents.tool.WebSearchTool] lets an agent search the web.
```

<details><summary>Context before (short)</summary>

```
# Choosing a tool type

Use this page as a catalog, then jump to the section that matches the runtime you control.

| If you want to... | Start here |
| --- | --- |
| Use OpenAI-managed tools (web search, file search, code interpreter, hosted MCP, image generation) | [Hosted tools](#hosted-tools) |
| Defer large tool surfaces until runtime with tool search | [Hosted tool search](#hosted-tool-searc…
```

</details>

<details><summary>Context after (short)</summary>

```

-   The [`FileSearchTool`][agents.tool.FileSearchTool] allows retrieving information from your OpenAI Vector Stores.
-   The [`CodeInterpreterTool`][agents.tool.CodeInterpreterTool] lets the LLM execute code in a sandboxed environment.
-   The [`HostedMCPTool`][agents.tool.HostedMCPTool] exposes a remote MCP server's tools to the model.
-   The [`ImageGenerationTool`][agents.tool.ImageGenerationT…
```

</details>

---
## NATQ-C-053

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Streaming messages
- **version_id**: `ver_1261879c16f641270789647ac9c63c96`
- **url**: https://platform.claude.com/docs/en/build-with-claude/streaming
- **section**: Event types
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic streaming event names, content_block_delta or just delta

**Answer**: The SSE event name is `content_block_delta`, not a bare `delta`. Each content block streams as `content_block_start`, then one or more `content_block_delta` events, then `content_block_stop`.

**Atomic claims**:
  - Anthropic streaming uses the event name `content_block_delta`.
  - A content block is streamed as `content_block_start`, one or more `content_block_delta` events, and `content_block_stop`.

**Critical strings**: `content_block_delta`, `content_block_start`, `content_block_stop`

### Evidence E1 (verbatim, authoritative)

`ver_1261879c16f641270789647ac9c63c96` chars 8932–9195 · hash `cc462499cc65e4aeb676924c0a81decae2d7f275ab6ee64fadf011f69bdd44f1`

```
Each stream uses the following event flow:

1. `message_start`: contains a `Message` object with empty `content`.
2. A series of content blocks, each of which has a `content_block_start`, one or more `content_block_delta` events, and a `content_block_stop` event.
```

<details><summary>Context before (short)</summary>

```
 server-sent events, then `.get_final_message()` (Python) or `.finalMessage()` (TypeScript) accumulates all events and returns the complete `Message` object. In Go, you call `message.Accumulate(event)` inside the stream loop to build the same complete `Message`. In Java, use `MessageAccumulator.create()` and call `accumulator.accumulate(event)` on each event. In C#, await the stream's `.Aggregate(…
```

</details>

<details><summary>Context after (short)</summary>

```
 Each content block has an `index` that corresponds to its index in the final Message `content` array. One exception: during [server-side fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback#server-side-fallback) responses, a `fallback` content block arrives at each model boundary as a `content_block_start` and `content_block_stop` pair with no deltas in between.
3…
```

</details>

---
## NATQ-C-056

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Streaming messages
- **version_id**: `ver_1261879c16f641270789647ac9c63c96`
- **url**: https://platform.claude.com/docs/en/build-with-claude/streaming
- **section**: Content block delta types › Thinking delta
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> can I stream anthropic thinking tokens separately from the visible answer

**Answer**: Yes. With thinking and streaming enabled, thinking text arrives as `thinking_delta` events on the `thinking` field of `thinking` content blocks, separate from visible answer text.

**Atomic claims**:
  - Streaming thinking content is delivered via `thinking_delta` events.
  - `thinking_delta` events correspond to the `thinking` field of `thinking` content blocks, not the visible text block.

**Critical strings**: `thinking_delta`, `thinking content blocks`, `streaming enabled`

### Evidence E1 (verbatim, authoritative)

`ver_1261879c16f641270789647ac9c63c96` chars 12178–12473 · hash `a2cde4f8e87ca7cccb3c629bad2be4d167bf236157a58d39bd3b28f71104cb13`

```
### Thinking delta

When using [thinking](https://platform.claude.com/docs/en/build-with-claude/thinking#streaming-thinking) with streaming enabled, you'll receive thinking content through `thinking_delta` events. These deltas correspond to the `thinking` field of the `thinking` content blocks.
```

<details><summary>Context before (short)</summary>

````
ic](https://docs.pydantic.dev/latest/concepts/json/#partial-json-parsing) to do partial JSON parsing, or by using the [SDKs](https://platform.claude.com/docs/en/cli-sdks-libraries/overview), which provide helpers to access parsed incremental values.

A `tool_use` content block delta looks like:

```sse Input JSON delta
event: content_block_delta
data: {"type": "content_block_delta","index": 1,"del…
````

</details>

<details><summary>Context after (short)</summary>

```


For thinking content, a special `signature_delta` event is sent just before the `content_block_stop` event. This signature is used to verify the integrity of the thinking block.

When `display: "omitted"` is set on the thinking configuration, no `thinking_delta` events are sent. The thinking block opens, receives a single `signature_delta`, and closes. See [Controlling thinking display](https://…
```

</details>

---
## NATQ-C-057

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): either
- **document**: Batch processing
- **version_id**: `ver_cec813c3bb15b76dcf16e7a0c2231ef1`
- **url**: https://platform.claude.com/docs/en/build-with-claude/batch-processing
- **section**: Message Batches API › How the Message Batches API works › What can be batched
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> what happens if I set stream true and also submit via the batch api

**Answer**: `stream: true` is not supported on the Message Batches API. Including it returns a validation error because batch results come back as a single file, not a stream.

**Atomic claims**:
  - `stream: true` is not supported in batch requests.
  - Including `stream: true` on a batch request returns a validation error.
  - Batch results come back as a single file, not a stream.

**Critical strings**: `stream: true`, `validation error`, `single file, not a stream`

### Evidence E1 (verbatim, authoritative)

`ver_cec813c3bb15b76dcf16e7a0c2231ef1` chars 4783–5397 · hash `d1db2fce79fa00f232fda34905671f8971dac1470b0e30b4a87bc307911867fd`

```
Including any of these returns a validation error:

| Parameter                                                                              | Why                                                                                                                |
| -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `stream: true`                                                                         | Batch results come back as a single file, not a stream.
```

<details><summary>Context before (short)</summary>

```
de a batch, because an ephemeral cache entry written during batch processing would likely expire before the follow-up request runs.

### Supported models

All [active models](https://platform.claude.com/docs/en/about-claude/models/overview) support the Message Batches API.

### What can be batched

Almost any request you can make to the Messages API can be included in a batch. This includes:

* Vi…
```

</details>

<details><summary>Context after (short)</summary>

```
                                                            |
| `speed` ([Fast mode](https://platform.claude.com/docs/en/build-with-claude/fast-mode)) | Fast mode tunes synchronous latency, which doesn't apply to asynchronous batch processing.                         |
| `store` / `previous_thread_event_id` (Threads)                                         | Threads are stateful; batch requests ar…
```

</details>

---
## NATQ-C-058

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Realtime transport
- **version_id**: `ver_e818e78755f8e2a71b458c743ce52db1`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/realtime/transport.md
- **section**: Realtime transport
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> openai realtime, ws from a python backend or webrtc from the browser

**Answer**: For the Python Agents SDK, use server-side WebSockets (and SIP). The Python SDK does not include browser WebRTC; WebRTC is a separate platform/browser topic.

**Atomic claims**:
  - The Python SDK does not include a browser WebRTC transport.
  - Python SDK realtime transport choices are server-side WebSockets and SIP attach flows.
  - Browser WebRTC is documented separately from the Python SDK.

**Critical strings**: `WebRTC`, `server-side WebSockets`, `Python SDK`

### Evidence E1 (verbatim, authoritative)

`ver_e818e78755f8e2a71b458c743ce52db1` chars 137–371 · hash `b0fc6199c42ccaf885a21d806cd87198a063bbdb505861a5ac321438f548bf80`

```
The Python SDK does **not** include a browser WebRTC transport. This page is only about Python SDK transport choices: server-side WebSockets and SIP attach flows. Browser WebRTC is a separate platform topic, documented in the official
```

<details><summary>Context before (short)</summary>

```
# Realtime transport

Use this page to decide how realtime agents fit into your Python application.

!!! note "Python SDK boundary"

    
```

</details>

<details><summary>Context after (short)</summary>

```
 [Realtime API with WebRTC](https://developers.openai.com/api/docs/guides/realtime-webrtc/) guide.

## Decision guide

| Goal | Start with | Why |
| --- | --- | --- |
| Build a server-managed realtime app | [Quickstart](quickstart.md) | The default Python path is a server-side WebSocket session managed by `RealtimeRunner`. |
| Understand which transport and deployment shape to choose | This page |…
```

</details>

---
## NATQ-C-060

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Streaming
- **version_id**: `ver_12004469f7a5592cd1e6cab936117fce`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/streaming.md
- **section**: Streaming › Run item events and agent events
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> agents sdk stream events — is there a RunItemStreamEvent for messages vs tools

**Answer**: Yes. `RunItemStreamEvent` is the higher-level stream event fired when an item is fully generated. Its `name` values include `message_output_created` for messages and `tool_called` / `tool_output` for tools.

**Atomic claims**:
  - `RunItemStreamEvent`s are higher-level events fired when an item has been fully generated.
  - `RunItemStreamEvent.name` includes `message_output_created`.
  - `RunItemStreamEvent.name` includes `tool_called` and `tool_output`.

**Critical strings**: `RunItemStreamEvent`, `message_output_created`, `tool_called`, `tool_output`

### Evidence E1 (verbatim, authoritative)

`ver_12004469f7a5592cd1e6cab936117fce` chars 5054–5750 · hash `90e4df8c8527df880eecf9c85870578e6fa62ccdc33234037ded7737c0ee7ee3`

```
[`RunItemStreamEvent`][agents.stream_events.RunItemStreamEvent]s are higher level events. They inform you when an item has been fully generated. This allows you to push progress updates at the level of "message generated", "tool ran", etc, instead of each token. Similarly, [`AgentUpdatedStreamEvent`][agents.stream_events.AgentUpdatedStreamEvent] gives you updates when the current agent changes (e.g. as the result of a handoff).

### Run item event names

`RunItemStreamEvent.name` uses a fixed set of semantic event names:

-   `message_output_created`
-   `handoff_requested`
-   `handoff_occured`
-   `tool_called`
-   `tool_search_called`
-   `tool_search_output_created`
-   `tool_output`
```

<details><summary>Context before (short)</summary>

```
user turn right away.

-   If new user input arrives before that unfinished run resumes, convert the drained result with `result.to_state()`, call [`state.add_input(...)`][agents.run_state.RunState.add_input], and resume from the state. The runner admits the staged input immediately before the next model call; see [Add input before resuming](results.md#add-input-before-resuming).
-   If a streamed…
```

</details>

<details><summary>Context after (short)</summary>

```

-   `reasoning_item_created`
-   `mcp_approval_requested`
-   `mcp_approval_response`
-   `mcp_list_tools`

`handoff_occured` is intentionally misspelled for backward compatibility.

A handoff call is emitted only as `handoff_requested`; it is not also emitted as `tool_called`. Ordinary function tool calls in the same turn still emit `tool_called`.

When you use hosted tool search, `tool_search_c…
```

</details>

---
## NATQ-C-061

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Streaming messages
- **version_id**: `ver_1261879c16f641270789647ac9c63c96`
- **url**: https://platform.claude.com/docs/en/build-with-claude/streaming
- **section**: Event types › Ping events
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> claude streaming, do I still need to handle ping events

**Answer**: Yes. Claude event streams may include any number of `ping` events, so a streaming client should handle them (typically as keepalives) rather than treating them as unknown/error events.

**Atomic claims**:
  - Anthropic event streams may include `ping` events.
  - There may be any number of `ping` events in a stream.

**Critical strings**: `Ping events`, `ping`

### Evidence E1 (verbatim, authoritative)

`ver_1261879c16f641270789647ac9c63c96` chars 9842–9918 · hash `cd4bb473a7357326cfae247a068eaafaf5024cc088bb2a574bd54433f2c41b55`

```
### Ping events

Event streams may also include any number of `ping` events.
```

<details><summary>Context before (short)</summary>

```
m uses the following event flow:

1. `message_start`: contains a `Message` object with empty `content`.
2. A series of content blocks, each of which has a `content_block_start`, one or more `content_block_delta` events, and a `content_block_stop` event. Each content block has an `index` that corresponds to its index in the final Message `content` array. One exception: during [server-side fallback]…
```

</details>

<details><summary>Context after (short)</summary>

````


### Error events

The API may occasionally send [errors](https://platform.claude.com/docs/en/api/errors) in the event stream. For example, during periods of high usage, you may receive an `overloaded_error`, which would normally correspond to an HTTP 529 in a non-streaming context:

```sse Example error
event: error
data: {"type": "error", "error": {"type": "overloaded_error", "message": "Overlo…
````

</details>

---
## NATQ-C-065

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Create a Message
- **version_id**: `ver_26ab39f5dede18e6cf62900e8b84f38b`
- **url**: https://platform.claude.com/docs/en/api/messages/create
- **section**: Create a Message › Body Parameters
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic temperature default, 1 or 0

**Answer**: Anthropic `temperature` defaults to `1.0` (not 0). Range is `0.0` to `1.0`.

**Atomic claims**:
  - `temperature` is an optional number on Create a Message.
  - The default temperature is `1.0`.
  - Temperature ranges from `0.0` to `1.0`.

**Critical strings**: `temperature`, `Defaults to `1.0``

### Evidence E1 (verbatim, authoritative)

`ver_26ab39f5dede18e6cf62900e8b84f38b` chars 32858–32992 · hash `a37463fe1be5c85186cf9fc0855805e68ea2600c75095dc17cf5a19f5ca7a487`

```
- `temperature: optional number`

  Amount of randomness injected into the response.

  Defaults to `1.0`. Ranges from `0.0` to `1.0`.
```

<details><summary>Context before (short)</summary>

```
stop_sequence` value will contain the matched stop sequence.

- `stream: optional boolean`

  Whether to incrementally stream the response using server-sent events.

  See [streaming](https://platform.claude.com/docs/en/build-with-claude/streaming) for details.

- `system: optional string or array of TextBlockParam`

  System prompt.

  A system prompt is a way of providing context and instruction…
```

</details>

<details><summary>Context after (short)</summary>

```
 Use `temperature` closer to `0.0` for analytical / multiple choice, and closer to `1.0` for creative and generative tasks.

  Note that even with `temperature` of `0.0`, the results will not be fully deterministic.

- `thinking: optional ThinkingConfigParam`

  Configuration for enabling Claude's extended thinking.

  When enabled, responses include `thinking` content blocks showing Claude's thin…
```

</details>

---
## NATQ-C-069

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Create a Message
- **version_id**: `ver_26ab39f5dede18e6cf62900e8b84f38b`
- **url**: https://platform.claude.com/docs/en/api/messages/create
- **section**: Create a Message › Body Parameters
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> claude top_k, still supported or only top_p now

**Answer**: `top_k` is still supported on the Messages API as an optional number (alongside `top_p`). It is recommended for advanced use cases only.

**Atomic claims**:
  - `top_k` is an optional number on Create a Message.
  - `top_k` samples only from the top K options for each subsequent token.
  - `top_k` is recommended for advanced use cases only, not removed in favor of `top_p` only.

**Critical strings**: `top_k: optional number`, `top K options`

### Evidence E1 (verbatim, authoritative)

`ver_26ab39f5dede18e6cf62900e8b84f38b` chars 66361–66670 · hash `2ad5996f9782fddfd7c31ed470dc1bdf3cb13fe00cdc13c865af2015be9da7f6`

```
- `top_k: optional number`

  Only sample from the top K options for each subsequent token.

  Used to remove "long tail" low probability responses. [Learn more technical details here](https://towardsdatascience.com/how-to-sample-from-language-models-682bceb97277).

  Recommended for advanced use cases only.
```

<details><summary>Context before (short)</summary>

```
el and in `tool_use` blocks.

      - `"tool_search_tool_regex"`

    - `type: "tool_search_tool_regex_20251119" or "tool_search_tool_regex"`

      - `"tool_search_tool_regex_20251119"`

      - `"tool_search_tool_regex"`

    - `allowed_callers: optional array of "direct" or "code_execution_20250825" or "code_execution_20260120" or "code_execution_20260521"`

      - `"direct"`

      - `"code_e…
```

</details>

<details><summary>Context after (short)</summary>

```


- `top_p: optional number`

  Use nucleus sampling.

  In nucleus sampling, we compute the cumulative distribution over all the options for each subsequent token in decreasing probability order and cut it off once it reaches a particular probability specified by `top_p`.

  Recommended for advanced use cases only.

### Returns

- `Message object { id, container, content, 7 more }`

  - `id: stri…
```

</details>

---
## NATQ-C-071

- **proposed_split**: `validation`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Create a Message
- **version_id**: `ver_26ab39f5dede18e6cf62900e8b84f38b`
- **url**: https://platform.claude.com/docs/en/api/messages/create
- **section**: Create a Message › Body Parameters
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic thinking budget_tokens vs max_tokens, can the budget be larger than max

**Answer**: No. `budget_tokens` must be ≥1024 and less than `max_tokens`, so the thinking budget cannot be larger than `max_tokens`.

**Atomic claims**:
  - `budget_tokens` determines how many tokens Claude can use for internal reasoning.
  - `budget_tokens` must be ≥1024.
  - `budget_tokens` must be less than `max_tokens`.

**Critical strings**: `budget_tokens`, `less than `max_tokens``, `≥1024`

### Evidence E1 (verbatim, authoritative)

`ver_26ab39f5dede18e6cf62900e8b84f38b` chars 33703–33961 · hash `c944d3bb39d5754dac54a1ea381685c06f8b01727577c10c6a6b13294cd3da3e`

```
- `budget_tokens: number`

      Determines how many tokens Claude can use for its internal reasoning process. Larger budgets can enable more thorough analysis for complex problems, improving response quality.

      Must be ≥1024 and less than `max_tokens`.
```

<details><summary>Context before (short)</summary>

```
tations: optional array of TextCitationParam or null`

- `temperature: optional number`

  Amount of randomness injected into the response.

  Defaults to `1.0`. Ranges from `0.0` to `1.0`. Use `temperature` closer to `0.0` for analytical / multiple choice, and closer to `1.0` for creative and generative tasks.

  Note that even with `temperature` of `0.0`, the results will not be fully determinis…
```

</details>

<details><summary>Context after (short)</summary>

```


      See [extended thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) for details.

    - `type: "enabled"`

      - `"enabled"`

    - `display: optional "summarized" or "omitted" or null`

      Controls how thinking content appears in the response. When set to `summarized`, thinking is returned normally. When set to `omitted`, thinking content is redacted but …
```

</details>

---
## NATQ-C-080

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Claude API errors
- **version_id**: `ver_0774ca0093ff4a846753577c9a4a39d5`
- **url**: https://platform.claude.com/docs/en/api/errors
- **section**: HTTP errors
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic overloaded_error vs rate_limit_error, same backoff?

**Answer**: They are different errors: 429 is `rate_limit_error` (account hit a rate limit); 529 is `overloaded_error` (API temporarily overloaded). Official SDKs retry transient failures such as rate limits and 5xx with the same exponential backoff (twice by default, honoring `retry-after`). A sharp usage spike can surface as 429 acceleration limits rather than 529.

**Atomic claims**:
  - 429 maps to `rate_limit_error` when the account hits a rate limit.
  - 529 maps to `overloaded_error` when the API is temporarily overloaded.
  - Official SDKs retry rate limits and 5xx server errors with exponential backoff, twice by default.

**Critical strings**: `429`, `rate_limit_error`, `529`, `overloaded_error`, `exponential backoff`

### Evidence E1 (verbatim, authoritative)

`ver_0774ca0093ff4a846753577c9a4a39d5` chars 1838–1900 · hash `5fbd183c0434345113813cb429db137c0def9957f350c399a4763f34b7704e8a`

```
* 429 - `rate_limit_error`: Your account has hit a rate limit.
```

<details><summary>Context before (short)</summary>

```
ils in the [Claude Console](https://platform.claude.com), or in AWS Marketplace if you're using Claude Platform on AWS.

* 403 - `permission_error`: Your API key does not have permission to use the specified resource. Check your organization's access and workspace settings in the [Claude Console](https://platform.claude.com).

* 404 - `not_found_error`: The requested resource was not found. Check …
```

</details>

<details><summary>Context after (short)</summary>

```


* 500 - `api_error`: An unexpected error has occurred internal to Anthropic's systems. Retry the request with exponential backoff; if the error persists, contact support with the [request ID](https://platform.claude.com/docs/en/api/errors#request-id).

* 504 - `timeout_error`: The request timed out while processing. Consider using the [streaming Messages API](https://platform.claude.com/docs/en/…
```

</details>

### Evidence E2 (verbatim, authoritative)

`ver_0774ca0093ff4a846753577c9a4a39d5` chars 2457–3089 · hash `79ae0877d46972cacc0fafaab7534d6104e6aa53221b729381ac87788a33aff9`

```
* 529 - `overloaded_error`: The API is temporarily overloaded.

  <Warning>
    529 errors can occur when the API experiences high traffic across all users.

    In rare cases, if your organization has a sharp increase in usage, you might see 429 errors because of acceleration limits on the API. To avoid hitting acceleration limits, ramp up your traffic gradually and maintain consistent usage patterns.
  </Warning>

The official SDKs automatically retry transient failures (such as connection errors, rate limits, and 5xx server errors) with exponential backoff, twice by default, honoring the `retry-after` header when present.
```

---
## NATQ-C-083

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Claude API errors
- **version_id**: `ver_0774ca0093ff4a846753577c9a4a39d5`
- **url**: https://platform.claude.com/docs/en/api/errors
- **section**: HTTP errors
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic request too large, is it 413 or a 400

**Answer**: It is HTTP 413 (`request_too_large`), not a 400. The request exceeded the maximum allowed number of bytes.

**Atomic claims**:
  - Oversized requests return HTTP 413.
  - The error type is `request_too_large`.

**Critical strings**: `413`, `request_too_large`

### Evidence E1 (verbatim, authoritative)

`ver_0774ca0093ff4a846753577c9a4a39d5` chars 1634–1836 · hash `e2e1e599e16edb051fa02df8bd5789eb510c8ba7bcad868c47eb556bf97d301b`

```
* 413 - `request_too_large`: Request exceeds the maximum allowed number of bytes. See [Request size limits](https://platform.claude.com/docs/en/api/errors#request-size-limits) for per-endpoint maximums.
```

<details><summary>Context before (short)</summary>

```
Platform on AWS, this can also indicate a problem with your AWS credentials or SigV4 signature.

* 402 - `billing_error`: There's an issue with your billing or payment information. Check your payment details in the [Claude Console](https://platform.claude.com), or in AWS Marketplace if you're using Claude Platform on AWS.

* 403 - `permission_error`: Your API key does not have permission to use th…
```

</details>

<details><summary>Context after (short)</summary>

```


* 429 - `rate_limit_error`: Your account has hit a rate limit.

* 500 - `api_error`: An unexpected error has occurred internal to Anthropic's systems. Retry the request with exponential backoff; if the error persists, contact support with the [request ID](https://platform.claude.com/docs/en/api/errors#request-id).

* 504 - `timeout_error`: The request timed out while processing. Consider using t…
```

</details>

---
## NATQ-C-087

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Messages
- **version_id**: `ver_18c692f4d28bd01c0a5cac553fcf01a7`
- **url**: https://platform.claude.com/docs/en/api/messages
- **section**: Messages › Create a Message › Returns
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> claude refusal, is stop_reason refusal or just end_turn with a decline

**Answer**: Claude uses `stop_reason` value `"refusal"` when streaming classifiers intervene for potential policy violations, not merely `end_turn` with a decline.

**Atomic claims**:
  - `stop_reason` can be `"refusal"`.
  - `refusal` is used when streaming classifiers intervene to handle potential policy violations.

**Critical strings**: `"refusal"`, `streaming classifiers`

### Evidence E1 (verbatim, authoritative)

`ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 89501–89590 · hash `93ee2036d4be7e80e3805a08ffda396d6b6d50130e3aff653281254adea02990`

```
* `"refusal"`: when streaming classifiers intervene to handle potential policy violations
```

<details><summary>Context before (short)</summary>

```
uld be related to an area that was determined as harmful. Benign work might sometimes trigger this category.

    - `explanation: string or null`

      Human-readable explanation of the refusal.

      This text is not guaranteed to be stable. `null` when no explanation is available for the category.

    - `type: "refusal"`

      - `"refusal"`

  - `stop_reason: StopReason or null`

    The rea…
```

</details>

<details><summary>Context after (short)</summary>

```

    * `"model_context_window_exceeded"`: we exceeded the model's context window

    In non-streaming mode this value is always non-null. In streaming mode, it is null in the `message_start` event and non-null otherwise.

    - `"end_turn"`

    - `"max_tokens"`

    - `"stop_sequence"`

    - `"tool_use"`

    - `"pause_turn"`

    - `"refusal"`

    - `"model_context_window_exceeded"`

  - `sto…
```

</details>

---
## NATQ-C-088

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): either
- **document**: Claude API errors
- **version_id**: `ver_0774ca0093ff4a846753577c9a4a39d5`
- **url**: https://platform.claude.com/docs/en/api/errors
- **section**: HTTP errors
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> expired api key vs invalid, both 401?

**Answer**: On the Claude API, both an invalid/malformed key and an expired key are HTTP 401 `authentication_error`. The docs give malformed, revoked, or expired as examples of the same status/type, so those cases are not distinguished by HTTP code.

**Atomic claims**:
  - API key problems return HTTP 401 `authentication_error`.
  - Examples of 401 include a malformed, revoked, or expired API key.

**Critical strings**: `401`, `authentication_error`, `malformed, revoked, or expired`

### Evidence E1 (verbatim, authoritative)

`ver_0774ca0093ff4a846753577c9a4a39d5` chars 502–723 · hash `b15703e4182e6884c343b3827f7a4fa4041b63b6ec3aa37f0df9cce34a25a9ce`

```
* 401 - `authentication_error`: There's an issue with your API key (for example, it's malformed, revoked, or expired; see [Key expiration](https://platform.claude.com/docs/en/manage-claude/authentication#key-expiration)).
```

<details><summary>Context before (short)</summary>

```
---
title: Claude API errors
url: https://platform.claude.com/docs/en/api/errors
description: Understand the HTTP status codes, error response shape, and request IDs the Claude API returns, and handle errors with the SDKs' typed exceptions.
---

## HTTP errors

The API follows a predictable HTTP error code format:

* 400 - `invalid_request_error`: There was an issue with the format or content of y…
```

</details>

<details><summary>Context after (short)</summary>

```
 On Claude Platform on AWS, this can also indicate a problem with your AWS credentials or SigV4 signature.

* 402 - `billing_error`: There's an issue with your billing or payment information. Check your payment details in the [Claude Console](https://platform.claude.com), or in AWS Marketplace if you're using Claude Platform on AWS.

* 403 - `permission_error`: Your API key does not have permissio…
```

</details>

---
## NATQ-C-090

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Troubleshooting tool use
- **version_id**: `ver_30f4e54dabb3ed9754d4075a41cc2531`
- **url**: https://platform.claude.com/docs/en/agents-and-tools/tool-use/troubleshooting-tool-use
- **section**: Errors at request time
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> tool_use_id mismatch when I return a tool_result, what error does claude give

**Answer**: Claude rejects the request with error `tool_use ids were found without tool_result blocks immediately after` when `tool_use` ids are missing a matching immediately-following `tool_result` (or the result is not the first content block). Return one `tool_result` for every `tool_use` id.

**Atomic claims**:
  - The request-time error is `tool_use ids were found without tool_result blocks immediately after`.
  - Cause is a missing `tool_result` for some `tool_use` ids, or `tool_result` not first in the user message.
  - Fix is one `tool_result` for every `tool_use` block, with `tool_result` blocks before any text.

**Critical strings**: `tool_use ids were found without tool_result blocks immediately after`, `tool_result`, `tool_use`

### Evidence E1 (verbatim, authoritative)

`ver_30f4e54dabb3ed9754d4075a41cc2531` chars 7909–8479 · hash `de6fa6bd3c26f62dac81dc906d9b58919d7ca9057e12380121b00625884b9c0e`

```
`tool_use ids were found without tool_result blocks immediately after`               | Missing `tool_result` for some `tool_use` ids, or `tool_result` is not the first content block in the user message                                                                                                                                                                                                                                                       | Return one `tool_result` for every `tool_use` block in the assistant response. Put `tool_result` blocks before any text.
```

<details><summary>Context before (short)</summary>

```
                                                                                                              |
| ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------…
```

</details>

<details><summary>Context after (short)</summary>

```
 See [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) and [Parallel tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use). |
| `was found without a corresponding <name>_tool_result block`                         | The previous assistant turn has a `server_tool_use` block with no result block (most often, Claud…
```

</details>

---
## NATQ-C-092

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Running agents
- **version_id**: `ver_2c60e99cfd929a738910b893fd6f1a40`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/running_agents.md
- **section**: Running agents › Exceptions
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> agents sdk ModelBehaviorError vs UserError, when do I see each

**Answer**: `ModelBehaviorError` is raised when the underlying model produces unexpected or invalid outputs (e.g. malformed JSON for tool calls/output_type, or unexpected tool-related failures). `UserError` is raised when you misuse the SDK (incorrect code, invalid configuration, or API misuse).

**Atomic claims**:
  - `ModelBehaviorError` occurs when the LLM produces unexpected or invalid outputs.
  - ModelBehaviorError examples include malformed JSON for tool calls or a defined `output_type`, and unexpected tool-related failures.
  - `UserError` is raised when the SDK user makes an error (incorrect implementation, invalid configuration, or API misuse).

**Critical strings**: `ModelBehaviorError`, `UserError`, `unexpected or invalid outputs`

### Evidence E1 (verbatim, authoritative)

`ver_2c60e99cfd929a738910b893fd6f1a40` chars 34203–35111 · hash `b58ebcf34eaa3052a07ce03b6178db5e36d6a48fde32717d3fea92d3af9fd28b`

```
-   [`ModelBehaviorError`][agents.exceptions.ModelBehaviorError]: This exception occurs when the underlying model (LLM) produces unexpected or invalid outputs. This can include:
    -   Malformed JSON: When the model provides a malformed JSON structure for tool calls or in its direct output, especially if a specific `output_type` is defined.
    -   Unexpected tool-related failures: When the model fails to use tools in an expected manner
-   [`ToolTimeoutError`][agents.exceptions.ToolTimeoutError]: This exception is raised when a function tool call exceeds its configured timeout and the tool uses `timeout_behavior="raise_exception"`.
-   [`UserError`][agents.exceptions.UserError]: This exception is raised when you (the person writing code using the SDK) make an error while using the SDK. This typically results from incorrect code implementation, invalid configuration, or misuse of the SDK's API.
```

<details><summary>Context before (short)</summary>

```
tions`][]. As an overview:

-   [`AgentsException`][agents.exceptions.AgentsException]: This is the base class for all exceptions that the SDK raises. It serves as a generic type from which all other specific exceptions are derived.
-   [`MaxTurnsExceeded`][agents.exceptions.MaxTurnsExceeded]: This exception is raised when the agent's run exceeds the `max_turns` limit passed to the `Runner.run`, `…
```

</details>

<details><summary>Context after (short)</summary>

```

-   [`InputGuardrailTripwireTriggered`][agents.exceptions.InputGuardrailTripwireTriggered], [`OutputGuardrailTripwireTriggered`][agents.exceptions.OutputGuardrailTripwireTriggered]: `InputGuardrailTripwireTriggered` is raised when an input guardrail's conditions are met, and `OutputGuardrailTripwireTriggered` is raised when an output guardrail's conditions are met. Input guardrails check incoming…
```

</details>

---
## NATQ-C-100

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: anthropic
- **intended_provider** (authoring): anthropic
- **document**: Batches
- **version_id**: `ver_ef5f9dacc17f99c298faf449e756ae90`
- **url**: https://platform.claude.com/docs/en/api/messages/batches
- **section**: Batches › Create a Message Batch
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> anthropic messages batches, did the path change from /v1/messages/batches

**Answer**: No. Creating a message batch is still `POST /v1/messages/batches`.

**Atomic claims**:
  - Create a Message Batch is POST `/v1/messages/batches`.

**Critical strings**: `/v1/messages/batches`, `post`

### Evidence E1 (verbatim, authoritative)

`ver_ef5f9dacc17f99c298faf449e756ae90` chars 97–155 · hash `32064282a56d1461aa66d45d0bb04cb9ea7bd51654eafd19612723e5ad902e9d`

```
## Create a Message Batch

**post** `/v1/messages/batches`
```

<details><summary>Context before (short)</summary>

```
---
title: Batches
url: https://platform.claude.com/docs/en/api/messages/batches
---

# Batches

```

</details>

<details><summary>Context after (short)</summary>

```


Send a batch of Message creation requests.

The Message Batches API can be used to process multiple Messages API requests at once. Once a Message Batch is created, it begins processing immediately. Batches can take up to 24 hours to complete.

Learn more about the Message Batches API in our [user guide](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

### Header Parameter…
```

</details>

---
## NATQ-C-105

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: OpenAI Agents SDK
- **version_id**: `ver_02c06cea4a4bbffd4d01ee202f124a75`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/index.md
- **section**: OpenAI Agents SDK
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> is the openai agents sdk replacing swarm

**Answer**: Yes. The OpenAI Agents SDK is described as a production-ready upgrade of OpenAI's previous agents experiment, Swarm.

**Atomic claims**:
  - The OpenAI Agents SDK is a production-ready upgrade of Swarm.
  - Swarm was OpenAI's previous experimentation for agents.

**Critical strings**: `production-ready upgrade`, `Swarm`

### Evidence E1 (verbatim, authoritative)

`ver_02c06cea4a4bbffd4d01ee202f124a75` chars 196–323 · hash `7b7ad75a93842ab9a27ab130888f4b7ab223d7cc79316a9790b3429bbfac980f`

```
It's a production-ready upgrade of our previous experimentation for agents, [Swarm](https://github.com/openai/swarm/tree/main).
```

<details><summary>Context before (short)</summary>

```
# OpenAI Agents SDK

The [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) enables you to build agentic AI apps in a lightweight, easy-to-use package with very few abstractions. 
```

</details>

<details><summary>Context after (short)</summary>

```
 The Agents SDK has a very small set of primitives:

-   **Agents**, which are LLMs equipped with instructions and tools
-   **Agents as tools / Handoffs**, which allow agents to delegate to other agents for specific tasks
-   **Guardrails**, which enable validation of agent inputs and outputs

In combination with Python, these primitives are powerful enough to express complex relationships betwee…
```

</details>

---
## NATQ-C-106

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Quickstart
- **version_id**: `ver_7c087a260ac830f2b4fa1396300b3fcc`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/realtime/quickstart.md
- **section**: Quickstart › Connection options
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> azure openai vs api.openai.com, does the agents sdk talk to azure

**Answer**: Yes, at least on the realtime path: the Agents SDK can talk to Azure OpenAI by setting model_config url to a GA Realtime endpoint URL and passing headers explicitly. Avoid the legacy beta path `/openai/realtime?api-version=...`.

**Atomic claims**:
  - Realtime agents can connect to Azure OpenAI.
  - Set model_config url to a GA Realtime endpoint URL and pass headers explicitly.
  - The legacy beta path `/openai/realtime?api-version=...` should be avoided with realtime agents.

**Critical strings**: `Azure OpenAI`, `model_config["url"]`, `GA Realtime endpoint`, `/openai/realtime?api-version=`

### Evidence E1 (verbatim, authoritative)

`ver_7c087a260ac830f2b4fa1396300b3fcc` chars 4907–5110 · hash `bf224d13c469bea9987ec82e5653105b432148e1f6002eda94f12c20794687f3`

```
When connecting to Azure OpenAI, set `model_config["url"]` to a GA Realtime endpoint URL and pass headers explicitly. Avoid the legacy beta path (`/openai/realtime?api-version=...`) with realtime agents.
```

<details><summary>Context before (short)</summary>

````
.create` flow described in the [Realtime agents guide](guide.md#manual-response-control).

For the full schema, see [`RealtimeRunConfig`][agents.realtime.config.RealtimeRunConfig] and [`RealtimeSessionModelSettings`][agents.realtime.config.RealtimeSessionModelSettings].

## Connection options

Set your API key in the environment:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or pass it d…
````

</details>

<details><summary>Context after (short)</summary>

```
 See the [Realtime agents guide](guide.md#low-level-access-and-custom-endpoints) for details.

## Next steps

-   Read [Realtime transport](transport.md) to choose between server-side WebSocket and SIP.
-   Read the [Realtime agents guide](guide.md) for lifecycle, structured input, approvals, handoffs, guardrails, and low-level control.
-   Browse the examples in [`examples/realtime`](https://gith…
```

</details>

---
## NATQ-C-112

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: OpenAI Agents SDK
- **version_id**: `ver_02c06cea4a4bbffd4d01ee202f124a75`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/index.md
- **section**: Infinite loop's dance.
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> where do I put the api key for openai agents sdk, still OPENAI_API_KEY?

**Answer**: Yes. Put it in the OPENAI_API_KEY environment variable (`export OPENAI_API_KEY=sk-...`).

**Atomic claims**:
  - The Agents SDK hello-world path expects the OPENAI_API_KEY environment variable.
  - The documented export is `export OPENAI_API_KEY=sk-...`.

**Critical strings**: `OPENAI_API_KEY`, `export OPENAI_API_KEY`

### Evidence E1 (verbatim, authoritative)

`ver_02c06cea4a4bbffd4d01ee202f124a75` chars 4044–4163 · hash `5dd07a1d9b8dc8657a431443d26b312bc3b66926a09697e2377a1adfe03e3c93`

````
(_If running this, ensure you set the `OPENAI_API_KEY` environment variable_)

```bash
export OPENAI_API_KEY=sk-...
```
````

<details><summary>Context before (short)</summary>

```
d and mainly about returning the model's response

Use the Agents SDK when:

-   you want the runtime to manage turns, tool execution, guardrails, handoffs, or sessions
-   your agent should produce artifacts or operate across multiple coordinated steps
-   you need a real workspace or resumable execution through [Sandbox agents](sandbox_agents.md)

You do not need to choose one globally. Many app…
```

</details>

<details><summary>Context after (short)</summary>

```


## Start here

-   Build your first text-based agent with the [Quickstart](quickstart.md).
-   Then decide how you want to carry state across turns in [Running agents](running_agents.md#choose-a-memory-strategy).
-   If the task depends on real files, repos, or isolated per-agent workspace state, read the [Sandbox agents quickstart](sandbox_agents.md).
-   If you are deciding between handoffs an…
```

</details>

---
## NATQ-C-119

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Sessions
- **version_id**: `ver_b275f1db2ff0a82e2654391774f8e398`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/sessions/index.md
- **section**: Continue the conversation › OpenAI Responses compaction sessions › Typical usage (auto-compaction)
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> openai compaction / context management in responses, automatic or do I have to call something

**Answer**: Both: compaction is an explicit Responses API call (`responses.compact`), but OpenAIResponsesCompactionSession can run it automatically after each turn when the threshold is met. You wrap an underlying session; you do not have to call compact yourself on that path.

**Atomic claims**:
  - OpenAIResponsesCompactionSession compacts stored history with the Responses API responses.compact.
  - It can automatically compact after each turn based on should_trigger_compaction.
  - By default the SDK checks the threshold after each turn and compacts only if it is met.

**Critical strings**: `OpenAIResponsesCompactionSession`, `responses.compact`, `automatically compact`, `should_trigger_compaction`

### Evidence E1 (verbatim, authoritative)

`ver_b275f1db2ff0a82e2654391774f8e398` chars 10000–10954 · hash `fa67f6266564b1d41d5c1a3d29b84bb6dd6ca4a177037f38c19156bbf48d054b`

````
### OpenAI Responses compaction sessions

Use `OpenAIResponsesCompactionSession` to compact stored conversation history with the Responses API (`responses.compact`). It wraps an underlying session and can automatically compact after each turn based on `should_trigger_compaction`. Do not wrap `OpenAIConversationsSession` with it; those two features manage history in different ways.

#### Typical usage (auto-compaction)

```python
from agents import Agent, Runner, SQLiteSession
from agents.memory import OpenAIResponsesCompactionSession

underlying = SQLiteSession("conversation_123")
session = OpenAIResponsesCompactionSession(
    session_id="conversation_123",
    underlying_session=underlying,
)

agent = Agent(name="Assistant")
result = await Runner.run(agent, "Hello", session=session)
print(result.final_output)
```

By default, after each turn, the SDK checks whether the compaction candidate meets the threshold and compacts only if it does.
````

<details><summary>Context before (short)</summary>

````
-store).

### OpenAI Conversations API sessions

Use [OpenAI's Conversations API](https://platform.openai.com/docs/api-reference/conversations) through `OpenAIConversationsSession`.

```python
from agents import Agent, Runner, OpenAIConversationsSession

# Create agent
agent = Agent(
    name="Assistant",
    instructions="Reply very concisely.",
)

# Create a new conversation
session = OpenAIConv…
````

</details>

<details><summary>Context after (short)</summary>

```


When automatic compaction runs, the SDK waits for it before `Runner.run(...)` returns or the streamed event iterator closes. Usage reported by the compaction request contributes to that run's [`Usage`](../usage.md) totals. By default, a manual `run_compaction()` call made later has no enclosing run context and does not update the completed run's usage object.

`compaction_mode="previous_response…
```

</details>

---
## NATQ-C-120

- **proposed_split**: `holdout`  *(PROPOSED / NOT_FROZEN metadata; not a secrecy boundary)*
- **provider**: openai
- **intended_provider** (authoring): openai
- **document**: Models
- **version_id**: `ver_ae909bf8b4bbbe1d1a11119447f7ac94`
- **url**: https://github.com/openai/openai-agents-python/blob/39327d7c5d04c120bf47f1ee9696c078e1f55441/docs/models/index.md
- **section**: Models › Advanced OpenAI Responses settings › Common advanced `ModelSettings` options
- **snapshot**: `snap_689e336380a054d8039dc35b2c09cd0a`
- **verification_status**: `PENDING_CHATGPT_REVIEW`

**Question** (byte-for-byte from authoring jsonl)

> prompt caching on openai — automatic prefix cache or do I mark breakpoints like claude

**Answer**: On the OpenAI Responses path you choose via prompt_cache_options: implicit (automatic) or explicit prompt caching. That is not Claude-style cache_control breakpoints; the SDK setting is mode implicit vs explicit (plus a 30m TTL option on GPT-5.6).

**Atomic claims**:
  - prompt_cache_options selects implicit or explicit prompt caching.
  - For GPT-5.6 you can also configure a 30m cache TTL.

**Critical strings**: `prompt_cache_options`, `implicit or explicit prompt caching`, `30m`

### Evidence E1 (verbatim, authoritative)

`ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 26913–27028 · hash `ba08ea5675f68fc543ecd4405c245ed545e5820638a4c93ce3a0cc898c71cdd4`

```
`prompt_cache_options`: Select implicit or explicit prompt caching and, for GPT-5.6, configure a `"30m"` cache TTL.
```

<details><summary>Context before (short)</summary>

```
## Common advanced `ModelSettings` options

When you are using the OpenAI Responses API, several request fields already have direct `ModelSettings` fields, so you do not need `extra_args` for them.

- `parallel_tool_calls`: Allow or forbid multiple tool calls in the same turn.
- `truncation`: Set `"auto"` to let the Responses API drop the oldest conversation items instead of failing when context w…
```

</details>

<details><summary>Context after (short)</summary>

```

- `response_include`: Request richer response payloads such as `web_search_call.action.sources`, `file_search_call.results`, or `reasoning.encrypted_content`.
- `top_logprobs`: Request top-token logprobs for output text. The SDK also adds `message.output_text.logprobs` automatically.
- `retry`: Opt in to runner-managed retry settings for model calls. See [Runner-managed retries](#runner-managed-r…
```

</details>

---
