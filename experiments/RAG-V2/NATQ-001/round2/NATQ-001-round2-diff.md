# NATQ-001 ROUND 2 diff

Generated 2026-09-02 14:13 EDT (2026-09-02T18:13:16Z). Snapshot `snap_689e336380a054d8039dc35b2c09cd0a`.

Questions preserved byte-for-byte. 0 replacements. 84 PASS packets not in this diff.

## NATQ-C-002

- **action**: `tightened`
- **what changed**: Removed 'Agent holds config; Runner is what actually invokes the model.' Kept the supported Runner-loop-calls-LLM answer. Evidence span unchanged.

### Old answer

The `Runner` agent loop calls the LLM for the current agent. `Agent` holds config; `Runner` is what actually invokes the model.

### New answer

The `Runner` agent loop calls the LLM for the current agent.

### Old claims

- The runner runs a loop after you call a Runner method with a starting agent.
- Step 1 of the loop: We call the LLM for the current agent, with the current input.

### New claims

- The runner runs a loop after you call a Runner method with a starting agent.
- Step 1 of the loop: We call the LLM for the current agent, with the current input.

### Old evidence spans

- `E1` `ver_2c60e99cfd929a738910b893fd6f1a40` chars 1496–1591 hash `a8d6b8fb890056326897a6f4497aadd9b4fbed1ef10e45f0ff655e6bb1ed7de4`

```
The runner then runs a loop:

1. We call the LLM for the current agent, with the current input.
```

### New evidence spans

- `E1` `ver_2c60e99cfd929a738910b893fd6f1a40` chars 1496–1591 hash `a8d6b8fb890056326897a6f4497aadd9b4fbed1ef10e45f0ff655e6bb1ed7de4`

```
The runner then runs a loop:

1. We call the LLM for the current agent, with the current input.
```

---

## NATQ-C-005

- **action**: `evidence-added`
- **what changed**: Kept needs_approval=True. Added E2 showing the exact @tool(needs_approval=True) decorator example.

### Old answer

Mark the tool with `needs_approval=True` (or a per-call callable). The run pauses until a human approves, e.g. `@tool(needs_approval=True)` on delete_user-style tools.

### New answer

Mark the tool with `needs_approval=True` (or a per-call callable). The run pauses until a human approves. Example: `@tool(needs_approval=True)`.

### Old claims

- Set needs_approval to True to always require approval, or provide an async function that decides per call.

### New claims

- Set needs_approval to True to always require approval, or provide an async function that decides per call.
- The decorator example is @tool(needs_approval=True).

### Old evidence spans

- `E1` `ver_ae3bfcc42c733c5051abda30f0f6db07` chars 1327–1436 hash `72cb1e104a68797ed1296cfed17b04ba519cd1890449a2e5542f4ed36ad4e836`

```
Set `needs_approval` to `True` to always require approval or provide an async function that decides per call.
```

### New evidence spans

- `E1` `ver_ae3bfcc42c733c5051abda30f0f6db07` chars 1327–1436 hash `72cb1e104a68797ed1296cfed17b04ba519cd1890449a2e5542f4ed36ad4e836`

```
Set `needs_approval` to `True` to always require approval or provide an async function that decides per call.
```

- `E2` `ver_ae3bfcc42c733c5051abda30f0f6db07` chars 1919–2104 hash `1a51dbf80d3510972c2302163ed180d2b3fa18a4d3b4375bca8a8601cccd68c9`

````
```python
from agents import Agent
from agents.decorators import tool


@tool(needs_approval=True)
async def cancel_order(order_id: int) -> str:
    return f"Cancelled order {order_id}"
````

---

## NATQ-C-014

- **action**: `evidence-added`
- **what changed**: Kept 'agents as tools'. Added E2 with spanish_agent.as_tool(...) / french_agent.as_tool(...).

### Old answer

Yes. Model nested agents as tools (`as_tool`) so one agent calls another as a function instead of a handoff.

### New answer

Yes. Model nested agents as tools via `.as_tool()` so one agent calls another as a function instead of a handoff.

### Old claims

- A central agent can orchestrate specialized agents instead of handing off control.
- You do this by modeling agents as tools.

### New claims

- A central agent can orchestrate specialized agents instead of handing off control.
- You do this by modeling agents as tools.
- The method is Agent.as_tool() (e.g. spanish_agent.as_tool(...)).

### Old evidence spans

- `E1` `ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 31350–31522 hash `46173393ea157969ac221c5be74b31fb7bfcf0b5e994b1ac6ba3f46fbd6e92e3`

```
In some workflows, you may want a central agent to orchestrate a network of specialized agents, instead of handing off control. You can do this by modeling agents as tools.
```

### New evidence spans

- `E1` `ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 31350–31522 hash `46173393ea157969ac221c5be74b31fb7bfcf0b5e994b1ac6ba3f46fbd6e92e3`

```
In some workflows, you may want a central agent to orchestrate a network of specialized agents, instead of handing off control. You can do this by modeling agents as tools.
```

- `E2` `ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 32058–32393 hash `c0ca0b574ac24fdf55c409279879cb44dce4555d93a6ce73d71dcc8df790757f`

```
    tools=[
        spanish_agent.as_tool(
            tool_name="translate_to_spanish",
            tool_description="Translate the user's message to Spanish",
        ),
        french_agent.as_tool(
            tool_name="translate_to_french",
            tool_description="Translate the user's message to French",
        ),
    ],
```

---

## NATQ-C-016

- **action**: `tightened`
- **what changed**: Removed the unsupported model-scope qualifier 'On some newer models'. Evidence span unchanged.

### Old answer

Put start-of-conversation instructions in the top-level `system` field, not as the first `messages` item. On some newer models you may also send later `"role": "system"` messages after a user turn.

### New answer

Put start-of-conversation instructions in the top-level `system` field, not as the first `messages` item. Use a mid-conversation system message for instructions that only become relevant later.

### Old claims

- A system message cannot be the first entry in messages; use the top-level system field for instructions from the start.
- Use top-level system for first-turn instructions and a mid-conversation system message for later instructions.

### New claims

- A system message cannot be the first entry in messages; use the top-level system field for instructions from the start.
- Use top-level system for first-turn instructions and a mid-conversation system message for later instructions.

### Old evidence spans

- `E1` `ver_d7be262221efc52378af14916e203df8` chars 10028–10561 hash `2c87e048a56535c6a64d46fad90542c91fe8344e734c7b187d4ad8681573a227`

```
A `system` message cannot be the first entry in `messages`; use the top-level `system` field for instructions that apply from the start.

A mid-conversation system message has the same authority as the top-level `system` field, but because it is appended to the end of the message history, it does not invalidate any cached prefix that came before it. Use the top-level `system` field for instructions that should apply from the very first turn, and a mid-conversation system message for instructions that only become relevant later.
```

### New evidence spans

- `E1` `ver_d7be262221efc52378af14916e203df8` chars 10028–10561 hash `2c87e048a56535c6a64d46fad90542c91fe8344e734c7b187d4ad8681573a227`

```
A `system` message cannot be the first entry in `messages`; use the top-level `system` field for instructions that apply from the start.

A mid-conversation system message has the same authority as the top-level `system` field, but because it is appended to the end of the message history, it does not invalidate any cached prefix that came before it. Use the top-level `system` field for instructions that should apply from the very first turn, and a mid-conversation system message for instructions that only become relevant later.
```

---

## NATQ-C-026

- **action**: `evidence-added`
- **what changed**: Removed 'not a tool'. Added E3: 'When citations are enabled, responses include multiple text blocks with citations.'

### Old answer

A document/response feature, not a tool. Enable with `citations: { enabled: true }` on a `document` block; cited passages come back on the response text blocks.

### New answer

A document/response feature. Enable with `citations: { enabled: true }` on a `document` block; when citations are enabled, responses include multiple text blocks with citations.

### Old claims

- Citations ground responses in source documents and return exact supporting passages.
- Enabled on a document block via citations.enabled true.

### New claims

- Citations ground responses in source documents and return exact supporting passages.
- Enabled on a document block via citations.enabled true.
- When citations are enabled, responses include multiple text blocks with citations.

### Old evidence spans

- `E1` `ver_77dd930ea597c30fc512a8f92f8e802d` chars 103–276 hash `6ac91ad79f18dbbec19d9b779cf16c3a621731cd679f572bfbee678cf2c1360e`

```
Ground Claude's responses in your source documents. Citations return the exact passages that support each claim, so you can verify answers and surface sources to your users.
```

- `E2` `ver_77dd930ea597c30fc512a8f92f8e802d` chars 26711–26743 hash `4267f2e963523ff0e3359002f395268fa725adeeb54935c7defa9e78a2df4bb2`

```
"citations": { "enabled": true }
```

### New evidence spans

- `E1` `ver_77dd930ea597c30fc512a8f92f8e802d` chars 103–276 hash `6ac91ad79f18dbbec19d9b779cf16c3a621731cd679f572bfbee678cf2c1360e`

```
Ground Claude's responses in your source documents. Citations return the exact passages that support each claim, so you can verify answers and surface sources to your users.
```

- `E2` `ver_77dd930ea597c30fc512a8f92f8e802d` chars 26711–26743 hash `4267f2e963523ff0e3359002f395268fa725adeeb54935c7defa9e78a2df4bb2`

```
"citations": { "enabled": true }
```

- `E3` `ver_77dd930ea597c30fc512a8f92f8e802d` chars 72228–72310 hash `0bc602fb9b0f0fedf4d0fb819a561d4cac8d9eefeb926bb054005053fcbd05b4`

```
When citations are enabled, responses include multiple text blocks with citations:
```

---

## NATQ-C-030

- **action**: `evidence-added`
- **what changed**: Added E2 from handling-stop-reasons: client tool_use is continued with tool_result blocks, not as-is resume.

### Old answer

Resume `pause_turn` by sending the response back as-is. `end_turn` is a natural stop (do not resume). `tool_use` means tools were invoked — continue with `tool_result`s, not a pause resume.

### New answer

Resume `pause_turn` by sending the response back as-is. `end_turn` is a natural stop (do not resume). `tool_use` means Claude stopped to call your tools — continue by sending client `tool_result` blocks, not by re-sending the response.

### Old claims

- end_turn: the model reached a natural stopping point.
- tool_use: the model invoked one or more tools.
- pause_turn: paused a long-running turn; provide the response back as-is in a subsequent request to continue.

### New claims

- end_turn: the model reached a natural stopping point.
- tool_use: the model invoked one or more tools.
- pause_turn: paused a long-running turn; provide the response back as-is in a subsequent request to continue.
- A client tool_use stop is continued by sending client tool_result blocks instead of the response itself.

### Old evidence spans

- `E1` `ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 89070–89496 hash `5ca0f474a72e4e48467b4e7cf30832c0342ebad20d5ad1897311bf3eaf02447c`

```
* `"end_turn"`: the model reached a natural stopping point
    * `"max_tokens"`: we exceeded the requested `max_tokens` or the model's maximum
    * `"stop_sequence"`: one of your provided custom `stop_sequences` was generated
    * `"tool_use"`: the model invoked one or more tools
    * `"pause_turn"`: we paused a long-running turn. You may provide the response back as-is in a subsequent request to let the model continue.
```

### New evidence spans

- `E1` `ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 89070–89496 hash `5ca0f474a72e4e48467b4e7cf30832c0342ebad20d5ad1897311bf3eaf02447c`

```
* `"end_turn"`: the model reached a natural stopping point
    * `"max_tokens"`: we exceeded the requested `max_tokens` or the model's maximum
    * `"stop_sequence"`: one of your provided custom `stop_sequences` was generated
    * `"tool_use"`: the model invoked one or more tools
    * `"pause_turn"`: we paused a long-running turn. You may provide the response back as-is in a subsequent request to let the model continue.
```

- `E2` `ver_4d14aec24504f4b8f6f28938b84587dc` chars 52326–52682 hash `8be5b8fd12ab9bb59b140f264e0a1b5000b7575f9e65401fa32119b14290c750`

```
A response that leaves a client `tool_use` block waiting on you never has a `stop_reason` of `pause_turn`: when Claude stops to call your tools, `stop_reason` is [`tool_use`](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons#tool-use), and you continue it by sending the client `tool_result` blocks instead of the response itself.
```

---

## NATQ-C-044

- **action**: `evidence-added`
- **what changed**: Question asks bash AND text editor. Added frozen text-editor E3 rather than reject/replace.

### Old answer

Built-in tool types you declare (`bash_20250124`, and the sibling text-editor type), but you still implement the client loop: run the command and return `tool_result`.

### New answer

Built-in tool types you declare (`bash_20250124` and `text_editor_20250728`), but you still implement the client loop. For bash, your application runs the command after Claude returns `tool_use`. For text editor, the schema is built into the model (`type: "text_editor_20250728"`) and you implement file operations.

### Old claims

- bash_20250124 is the current built-in bash tool type and requires no beta header.
- Your application runs the command in its bash session after Claude returns tool_use.

### New claims

- bash_20250124 is the current built-in bash tool type and requires no beta header.
- Your application runs the command in its bash session after Claude returns tool_use.
- The text editor tool is a schema-less built-in; type is text_editor_20250728 for Claude 4 and later.
- You implement the text editor by handling file operations / editor tool calls yourself.

### Old evidence spans

- `E1` `ver_9bf8513721dc2d1ef3e1ec42bf535dc6` chars 8308–8391 hash `0fb5b2b6b9540ce984d156f3ac858414d8c391031619c12914705f617e95273b`

```
`bash_20250124` is the current version of the tool, and it requires no beta header.
```

- `E2` `ver_9bf8513721dc2d1ef3e1ec42bf535dc6` chars 6308–6435 hash `b3d65e6e4717b3cef5e087ab1c9dd9708cc2fb1962a23ceeb663c905a0813c3c`

```
1. Claude returns a `tool_use` block containing the `command` to run.
2. Your application runs the command in its bash session.
```

### New evidence spans

- `E1` `ver_9bf8513721dc2d1ef3e1ec42bf535dc6` chars 8308–8391 hash `0fb5b2b6b9540ce984d156f3ac858414d8c391031619c12914705f617e95273b`

```
`bash_20250124` is the current version of the tool, and it requires no beta header.
```

- `E2` `ver_9bf8513721dc2d1ef3e1ec42bf535dc6` chars 6308–6435 hash `b3d65e6e4717b3cef5e087ab1c9dd9708cc2fb1962a23ceeb663c905a0813c3c`

```
1. Claude returns a `tool_use` block containing the `command` to run.
2. Your application runs the command in its bash session.
```

- `E3` `ver_72833144cee232446fa450e9e040995a` chars 53515–53836 hash `abc0fd6f5e0087734ce8b2eb42a90f2b99ac261dd391391ba55dd2e845dfa293`

```
## Implement the text editor tool

The text editor tool is implemented as a schema-less tool. When using this tool, you don't need to provide an input schema as with other tools; the schema is built into Claude's model and can't be modified.

The tool type is `type: "text_editor_20250728"` for Claude 4 and later models.
```

---

## NATQ-C-047

- **action**: `evidence-added`
- **what changed**: Added direct hosted-vs-FunctionTool evidence. Did not infer; did not replace.

### Old answer

No. Hosted tools like `WebSearchTool` are OpenAI-managed built-ins you attach on the agent. `on_invoke_tool` is for custom `FunctionTool`s, not hosted web search.

### New answer

No. Hosted tools like `WebSearchTool` are OpenAI-managed built-ins that execute for the model on OpenAI servers. `on_invoke_tool` is the async callback you provide when creating a custom `FunctionTool`.

### Old claims

- OpenAI offers built-in hosted tools when using OpenAIResponsesModel.
- WebSearchTool lets an agent search the web.

### New claims

- OpenAI offers built-in hosted tools when using OpenAIResponsesModel.
- WebSearchTool lets an agent search the web.
- Hosted OpenAI tools execute for the model on OpenAI servers.
- When you create a FunctionTool you must provide on_invoke_tool.

### Old evidence spans

- `E1` `ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 1524–1736 hash `e09902a49d7762d5f509b1ee1cff7803a0491c191aa770b30c572688d38f0934`

```
OpenAI offers a few built-in tools when using the [`OpenAIResponsesModel`][agents.models.openai_responses.OpenAIResponsesModel]:

-   The [`WebSearchTool`][agents.tool.WebSearchTool] lets an agent search the web.
```

### New evidence spans

- `E1` `ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 1524–1736 hash `e09902a49d7762d5f509b1ee1cff7803a0491c191aa770b30c572688d38f0934`

```
OpenAI offers a few built-in tools when using the [`OpenAIResponsesModel`][agents.models.openai_responses.OpenAIResponsesModel]:

-   The [`WebSearchTool`][agents.tool.WebSearchTool] lets an agent search the web.
```

- `E2` `ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 170–231 hash `6081c6c824a23a2130f34634e7d8a16e4679f983115bdc47dfdb14ccf9ffa725`

```
Hosted OpenAI tools: execute for the model on OpenAI servers.
```

- `E3` `ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 24918–25462 hash `e7504a65ab00badf914ebc7a1739f903aa9300c1e5e93a1e7d899e9775d4bc12`

```
### Custom function tools

Sometimes, you don't want to use a Python function as a tool. You can directly create a [`FunctionTool`][agents.tool.FunctionTool] if you prefer. You'll need to provide:

-   `name`
-   `description`
-   `params_json_schema`, which is the JSON schema for the arguments
-   `on_invoke_tool`, which is an async function that receives a [`ToolContext`][agents.tool_context.ToolContext] and the arguments as a JSON string, and returns tool output (for example, text, structured tool output objects, or a list of outputs).
```

---

## NATQ-C-120

- **action**: `tightened`
- **what changed**: Dropped Claude-style cache_control absence claim. Kept prompt_cache_options implicit/explicit and 30m TTL.

### Old answer

On the OpenAI Responses path you choose via prompt_cache_options: implicit (automatic) or explicit prompt caching. That is not Claude-style cache_control breakpoints; the SDK setting is mode implicit vs explicit (plus a 30m TTL option on GPT-5.6).

### New answer

On the OpenAI Responses path you choose via `prompt_cache_options`: implicit or explicit prompt caching, and for GPT-5.6 you can configure a `"30m"` cache TTL.

### Old claims

- prompt_cache_options selects implicit or explicit prompt caching.
- For GPT-5.6 you can also configure a 30m cache TTL.

### New claims

- prompt_cache_options selects implicit or explicit prompt caching.
- For GPT-5.6 you can also configure a 30m cache TTL.

### Old evidence spans

- `E1` `ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 26913–27028 hash `ba08ea5675f68fc543ecd4405c245ed545e5820638a4c93ce3a0cc898c71cdd4`

```
`prompt_cache_options`: Select implicit or explicit prompt caching and, for GPT-5.6, configure a `"30m"` cache TTL.
```

### New evidence spans

- `E1` `ver_ae909bf8b4bbbe1d1a11119447f7ac94` chars 26913–27028 hash `ba08ea5675f68fc543ecd4405c245ed545e5820638a4c93ce3a0cc898c71cdd4`

```
`prompt_cache_options`: Select implicit or explicit prompt caching and, for GPT-5.6, configure a `"30m"` cache TTL.
```

---

## NATQ-C-127

- **action**: `tightened`
- **what changed**: Removed 'Server-side compaction is a different, primary strategy; this page is fine-grained clearing.' Claims already matched the tool-result-clearing evidence.

### Old answer

Yes, if you enable context editing (beta header context-management-2025-06-27) with clear_tool_uses_20250919. The API then automatically clears the oldest tool results past the threshold and replaces them with placeholder text. Server-side compaction is a different, primary strategy; this page is fine-grained clearing.

### New answer

Yes, if you enable context editing (beta header `context-management-2025-06-27`) with `clear_tool_uses_20250919`. The API then automatically clears the oldest tool results past the threshold and replaces them with placeholder text.

### Old claims

- Context editing is beta and requires the context-management-2025-06-27 header.
- clear_tool_uses_20250919 clears tool results when context grows past the threshold.
- The oldest tool results are cleared automatically and replaced with placeholder text.

### New claims

- Context editing is beta and requires the context-management-2025-06-27 header.
- clear_tool_uses_20250919 clears tool results when context grows past the threshold.
- The oldest tool results are cleared automatically and replaced with placeholder text.

### Old evidence spans

- `E1` `ver_1c53b961e1f5da8124a1e7e8eb92c941` chars 3947–4766 hash `cb46b2283398129eefe8d9de46c3c2b45d1ebcf0529d9435f755c094305e6b6c`

```
Context editing is in beta with support for tool result clearing and thinking block clearing. To enable it, use the beta header `context-management-2025-06-27` in your API requests.

  Share feedback on this feature through the [feedback form](https://forms.gle/YXC2EKGMhjN1c4L88).
</Note>

### Tool result clearing

The `clear_tool_uses_20250919` strategy clears tool results when conversation context grows beyond your configured threshold. This is particularly useful for agentic workflows with heavy tool use. Older tool results (like file contents or search results) are no longer needed once Claude has processed them.

When activated, the API automatically clears the oldest tool results in chronological order. The API replaces each cleared result with placeholder text indicating to Claude that it was removed.
```

### New evidence spans

- `E1` `ver_1c53b961e1f5da8124a1e7e8eb92c941` chars 3947–4766 hash `cb46b2283398129eefe8d9de46c3c2b45d1ebcf0529d9435f755c094305e6b6c`

```
Context editing is in beta with support for tool result clearing and thinking block clearing. To enable it, use the beta header `context-management-2025-06-27` in your API requests.

  Share feedback on this feature through the [feedback form](https://forms.gle/YXC2EKGMhjN1c4L88).
</Note>

### Tool result clearing

The `clear_tool_uses_20250919` strategy clears tool results when conversation context grows beyond your configured threshold. This is particularly useful for agentic workflows with heavy tool use. Older tool results (like file contents or search results) are no longer needed once Claude has processed them.

When activated, the API automatically clears the oldest tool results in chronological order. The API replaces each cleared result with placeholder text indicating to Claude that it was removed.
```

---

## NATQ-C-154

- **action**: `evidence-added`
- **what changed**: Kept web_search_20260209 as current type. Added E2 anchoring web_search_20250305 in the same Messages schema.

### Old answer

Put a versioned web-search tool in `tools` with `name` `web_search` and `type` `web_search_20260209` (older schema also has `web_search_20250305`).

### New answer

Put a versioned web-search tool in `tools` with `name` `web_search` and `type` `web_search_20260209` (the same schema also documents `web_search_20250305`).

### Old claims

- The web search tool name is web_search.
- The tools-array type string for the current schema is web_search_20260209.

### New claims

- The web search tool name is web_search.
- The tools-array type string for the current schema is web_search_20260209.
- The same Messages schema also documents type web_search_20250305.

### Old evidence spans

- `E1` `ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 573885–574204 hash `b6c2bc149b7856621900880bc50917feff4ea5774d2ddf04665285b5cabf3e09`

```
### Web Search Tool 20260209

- `WebSearchTool20260209 object { name, type, allowed_callers, 7 more }`

  - `name: "web_search"`

    Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks.

    - `"web_search"`

  - `type: "web_search_20260209"`

    - `"web_search_20260209"`
```

### New evidence spans

- `E1` `ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 573885–574204 hash `b6c2bc149b7856621900880bc50917feff4ea5774d2ddf04665285b5cabf3e09`

```
### Web Search Tool 20260209

- `WebSearchTool20260209 object { name, type, allowed_callers, 7 more }`

  - `name: "web_search"`

    Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks.

    - `"web_search"`

  - `type: "web_search_20260209"`

    - `"web_search_20260209"`
```

- `E2` `ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 571471–571790 hash `bffee40a6f1596816b97f8ec4b39801e30c695ce432d7650971bc872bbda8254`

```
### Web Search Tool 20250305

- `WebSearchTool20250305 object { name, type, allowed_callers, 7 more }`

  - `name: "web_search"`

    Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks.

    - `"web_search"`

  - `type: "web_search_20250305"`

    - `"web_search_20250305"`
```

---

## NATQ-C-160

- **action**: `evidence-added`
- **what changed**: Added general Files API document-source evidence (E2) rather than scoping the answer to beta-only.

### Old answer

Reference a previously uploaded file with a document source `{ file_id, type: "file" }` (`BetaFileDocumentSource`), rather than inlining the PDF bytes.

### New answer

In the Files API, a `document` block references a previously uploaded file via `source: { "type": "file", "file_id": ... }` rather than inlining PDF bytes. The beta schema names that shape `BetaFileDocumentSource` (`file_id`, `type: "file"`).

### Old claims

- BetaFileDocumentSource has file_id and type file.
- This is the document-block source shape for a Files API id.

### New claims

- Files API document blocks use source type file plus file_id for PDFs and text files.
- BetaFileDocumentSource has file_id and type file.

### Old evidence spans

- `E1` `ver_de7f74230c8f10d30aea5d037a3bd0a5` chars 438428–438570 hash `5d3597596859e25527dd845b49f59b58d3dca6680ee3d44ff51072572248c22d`

```
### Beta File Document Source

- `BetaFileDocumentSource object { file_id, type }`

  - `file_id: string`

  - `type: "file"`

    - `"file"`

```

### New evidence spans

- `E1` `ver_de7f74230c8f10d30aea5d037a3bd0a5` chars 438428–438570 hash `5d3597596859e25527dd845b49f59b58d3dca6680ee3d44ff51072572248c22d`

```
### Beta File Document Source

- `BetaFileDocumentSource object { file_id, type }`

  - `file_id: string`

  - `type: "file"`

    - `"file"`

```

- `E2` `ver_ab9e2c2bf4c17bf70ce1b94355d01729` chars 14340–14707 hash `0c9916ccfecc120a473943fe5d31f01b78e2f86da93b9a052f77382b7f08e785`

````
#### Document blocks

For PDFs and text files, use the `document` content block:

```json
{
  "type": "document",
  "source": {
    "type": "file",
    "file_id": "file_011CNha8iCJcU1wXNR6q4V8w"
  },
  "title": "Document Title", // Optional
  "context": "Context about the document", // Optional
  "citations": { "enabled": true } // Optional, enables citations
}
```
````

---

## NATQ-C-163

- **action**: `evidence-added`
- **what changed**: Added frozen SSE span with event: content_block_delta plus input_json_delta/partial_json.

### Old answer

Tool-argument streaming is a `content_block_delta` (`RawContentBlockDeltaEvent`) whose `delta` is `InputJSONDelta` with `type: "input_json_delta"` and a `partial_json` string — not a separate top-level `input_json_delta` SSE event name.

### New answer

Tool-argument streaming is a `content_block_delta` (`RawContentBlockDeltaEvent`) whose `delta` is `InputJSONDelta` with `type: "input_json_delta"` and a `partial_json` string — not a separate top-level `input_json_delta` SSE event name.

### Old claims

- RawContentBlockDeltaEvent carries a delta that can be InputJSONDelta.
- InputJSONDelta has partial_json and type input_json_delta.

### New claims

- RawContentBlockDeltaEvent carries a delta that can be InputJSONDelta.
- InputJSONDelta has partial_json and type input_json_delta.
- The outer SSE event name is content_block_delta (event: content_block_delta).

### Old evidence spans

- `E1` `ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 349245–349649 hash `320274240a25c455710144022ec141d32e1dd399e9b5d4f91fc93911db1dfd77`

```
### Raw Content Block Delta Event

- `RawContentBlockDeltaEvent object { delta, index, type }`

  - `delta: RawContentBlockDelta`

    - `TextDelta object { text, type }`

      - `text: string`

      - `type: "text_delta"`

        - `"text_delta"`

    - `InputJSONDelta object { partial_json, type }`

      - `partial_json: string`

      - `type: "input_json_delta"`

        - `"input_json_delta"`
```

### New evidence spans

- `E1` `ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 349245–349649 hash `320274240a25c455710144022ec141d32e1dd399e9b5d4f91fc93911db1dfd77`

```
### Raw Content Block Delta Event

- `RawContentBlockDeltaEvent object { delta, index, type }`

  - `delta: RawContentBlockDelta`

    - `TextDelta object { text, type }`

      - `text: string`

      - `type: "text_delta"`

        - `"text_delta"`

    - `InputJSONDelta object { partial_json, type }`

      - `partial_json: string`

      - `type: "input_json_delta"`

        - `"input_json_delta"`
```

- `E2` `ver_1261879c16f641270789647ac9c63c96` chars 10893–11760 hash `d08e64bde91aa1cb1865fea87dfc9a76c8411ba41d875e56f67fba77642016ae`

````
### Input JSON delta

The deltas for `tool_use` content blocks correspond to updates for the `input` field of the block. To support maximum granularity, the deltas are *partial JSON strings*, whereas the final `tool_use.input` is always an *object*.

You can accumulate the string deltas and parse the JSON once you receive a `content_block_stop` event, by using a library like [Pydantic](https://docs.pydantic.dev/latest/concepts/json/#partial-json-parsing) to do partial JSON parsing, or by using the [SDKs](https://platform.claude.com/docs/en/cli-sdks-libraries/overview), which provide helpers to access parsed incremental values.

A `tool_use` content block delta looks like:

```sse Input JSON delta
event: content_block_delta
data: {"type": "content_block_delta","index": 1,"delta": {"type": "input_json_delta","partial_json": "{\"location\": \"San Fra"}}}
```
````

---

## NATQ-C-193

- **action**: `tightened`
- **what changed**: Removed 'there is no unsuffixed anthropic-organization / anthropic-workspace'. Evidence spans unchanged.

### Old answer

Not under those exact names. The corpus documents `anthropic-organization-id` as a response header (org of the API key/token) and `anthropic-workspace-id` as a request header required on Claude Platform on AWS. There is no `anthropic-organization` or `anthropic-workspace` header as guessed.

### New answer

The documented header names here are `anthropic-organization-id` and `anthropic-workspace-id`. `anthropic-organization-id` is a response header (organization of the API key or access token); `anthropic-workspace-id` is a request header used to target a workspace on Claude Platform on AWS.

### Old claims

- anthropic-organization-id is a documented response header identifying the organization of the API key or token.
- anthropic-workspace-id is a request header used to target a workspace on Claude Platform on AWS.
- The guessed names without the -id suffix are not the documented headers.

### New claims

- anthropic-organization-id is a documented response header identifying the organization of the API key or token.
- anthropic-workspace-id is a request header used to target a workspace on Claude Platform on AWS.
- The documented header names here are anthropic-organization-id and anthropic-workspace-id.

### Old evidence spans

- `E1` `ver_6cbca1c2343b84b7d5cf99029456cfa2` chars 12322–12443 hash `023ee059d163c56697c87ca32d5e7326d8ae8e7b3f3f15eadd221a3a84b78f5c`

```
`anthropic-organization-id` | The ID of the organization that the API key or access token used in the request belongs to.
```

- `E2` `ver_5ebdc722f9bedb1e2e8cbd3f29ff6805` chars 48160–48339 hash `1824b8420b2c3c818c721edf04ed2bd3b1a012e81d18b4da21807690e3b08c65`

```
## Workspaces

Inference and resource requests on Claude Platform on AWS target a workspace. You pass the workspace's ID in the `anthropic-workspace-id` header on these API calls.
```

### New evidence spans

- `E1` `ver_6cbca1c2343b84b7d5cf99029456cfa2` chars 12322–12443 hash `023ee059d163c56697c87ca32d5e7326d8ae8e7b3f3f15eadd221a3a84b78f5c`

```
`anthropic-organization-id` | The ID of the organization that the API key or access token used in the request belongs to.
```

- `E2` `ver_5ebdc722f9bedb1e2e8cbd3f29ff6805` chars 48160–48339 hash `1824b8420b2c3c818c721edf04ed2bd3b1a012e81d18b4da21807690e3b08c65`

```
## Workspaces

Inference and resource requests on Claude Platform on AWS target a workspace. You pass the workspace's ID in the `anthropic-workspace-id` header on these API calls.
```

---

## NATQ-C-219

- **action**: `tightened`
- **what changed**: Removed process-default / per-Runner-constructor claim. Evidence span unchanged.

### Old answer

Yes, via `set_default_openai_client`. Build an `AsyncOpenAI` (base_url/api_key/wrapper) and pass it in; the SDK uses that client instead of constructing its own. It is a process default, not a per-Runner constructor argument.

### New answer

Yes, via `set_default_openai_client`. Build an `AsyncOpenAI` (`base_url` / `api_key` / wrapper) and pass it in; the SDK uses that client instead of constructing its own.

### Old claims

- By default the SDK creates an AsyncOpenAI instance.
- set_default_openai_client lets you replace that client.
- Example constructs AsyncOpenAI(base_url=..., api_key=...) and calls set_default_openai_client.

### New claims

- By default the SDK creates an AsyncOpenAI instance.
- set_default_openai_client lets you replace that client.
- Example constructs AsyncOpenAI(base_url=..., api_key=...) and calls set_default_openai_client.

### Old evidence spans

- `E1` `ver_f15e1a531d680bb98179238f80355058` chars 2401–2895 hash `29cb0cd9697430f885bb9971d6ef6b1a427eea8a5eca759a7702f983dfc84a05`

````
Alternatively, you can also configure an OpenAI client to be used. By default, the SDK creates an `AsyncOpenAI` instance, using the API key from the environment variable or the default key set above. You can change this by using the [set_default_openai_client()][agents.set_default_openai_client] function.

```python
from openai import AsyncOpenAI
from agents import set_default_openai_client

custom_client = AsyncOpenAI(base_url="...", api_key="...")
set_default_openai_client(custom_client)
````

### New evidence spans

- `E1` `ver_f15e1a531d680bb98179238f80355058` chars 2401–2895 hash `29cb0cd9697430f885bb9971d6ef6b1a427eea8a5eca759a7702f983dfc84a05`

````
Alternatively, you can also configure an OpenAI client to be used. By default, the SDK creates an `AsyncOpenAI` instance, using the API key from the environment variable or the default key set above. You can change this by using the [set_default_openai_client()][agents.set_default_openai_client] function.

```python
from openai import AsyncOpenAI
from agents import set_default_openai_client

custom_client = AsyncOpenAI(base_url="...", api_key="...")
set_default_openai_client(custom_client)
````

---

## NATQ-C-172

- **action**: `evidence-added`
- **what changed**: Expanded E1 through the Note that names Claude Haiku 4.5. Corrected answer: Haiku 4.5 supports computer use with computer-use-2025-01-24, not 'haiku is absent'.

### Old answer

Computer use supported models listed are opus/sonnet families (`claude-opus-5`, `claude-sonnet-5`, `claude-opus-4-8`, `claude-opus-4-7`, `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-opus-4-5-20251101`). Haiku is not in that list.

### New answer

Haiku 4.5 does support computer use. The current `computer-use-2025-11-24` supported-models list is opus/sonnet IDs (`claude-opus-5`, `claude-sonnet-5`, `claude-opus-4-8`, `claude-opus-4-7`, `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-opus-4-5-20251101`). A note on the same page says Claude Haiku 4.5 (with Claude Sonnet 4.5, Claude Opus 4.1, Claude Sonnet 4, and Claude Opus 4) uses the earlier `computer-use-2025-01-24` beta header instead of `computer-use-2025-11-24`.

### Old claims

- Computer use is beta with header computer-use-2025-11-24.
- Supported models listed are opus and sonnet IDs; haiku is absent from the list.

### New claims

- Computer use is beta; the current beta header is computer-use-2025-11-24.
- The supported-models list for that header is opus/sonnet IDs (no haiku id in that list).
- On Claude Sonnet 4.5, Claude Haiku 4.5, Claude Opus 4.1, Claude Sonnet 4, and Claude Opus 4, use the earlier computer-use-2025-01-24 beta header instead.

### Old evidence spans

- `E1` `ver_d9ba3ab0d872dd86047c7ed6dc783235` chars 237–762 hash `682cfec786f4ed77493144d950012dd0626fbe864bb6fd754301eacedbe2618e`

```
## Compatibility
- Status: Beta
- [Beta header](https://platform.claude.com/docs/en/api/beta-headers): `computer-use-2025-11-24`
- [ZDR](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention): eligible (excludes [Covered Models](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention#model-specific-data-retention-requirements))
- Supported models: `claude-opus-5`, `claude-sonnet-5`, `claude-opus-4-8`, `claude-opus-4-7`, `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-opus-4-5-20251101
```

### New evidence spans

- `E1` `ver_d9ba3ab0d872dd86047c7ed6dc783235` chars 237–1792 hash `28ffa05ae6d5e2832f83c7ea9f3f5fd17955593bcdfb6f1ce0828ed85c227bde`

```
## Compatibility
- Status: Beta
- [Beta header](https://platform.claude.com/docs/en/api/beta-headers): `computer-use-2025-11-24`
- [ZDR](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention): eligible (excludes [Covered Models](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention#model-specific-data-retention-requirements))
- Supported models: `claude-opus-5`, `claude-sonnet-5`, `claude-opus-4-8`, `claude-opus-4-7`, `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-opus-4-5-20251101`
- Platforms: Claude API (beta), Claude Platform on AWS (beta), Amazon Bedrock (beta), Google Cloud (beta), Microsoft Foundry (beta)

Claude can interact with computer environments through the computer use tool, which provides screenshot capabilities and mouse/keyboard control for autonomous desktop interaction.

<Note>
  On Claude Sonnet 4.5, Claude Haiku 4.5, Claude Opus 4.1 ([retired, except on Bedrock and Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations)), Claude Sonnet 4 ([retired, except on Bedrock and Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations)), and Claude Opus 4 ([retired, except on Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations)), use the earlier `computer-use-2025-01-24` [beta header](https://platform.claude.com/docs/en/api/beta-headers) instead of `computer-use-2025-11-24`.

  Reach out through the [feedback form](https://forms.gle/H6UFuXaaLywri9hz6) to share your feedback on this feature.
</Note>
```

---
