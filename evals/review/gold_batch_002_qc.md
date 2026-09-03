# GOLD-001 — batch 002 human QC packet

**18 decisions.** 17 fast track, 1 need the anchor checked, 0 recommended for rejection.

Nothing in this packet is gold. A candidate becomes `human_verified` only when you record `APPROVE` for it in `evals/review/human_decisions_batch_002.json` and import that file. An independent-review PASS produces `dual_llm_pass` and stops there — two AI systems agreeing is not human verification.

**Judge each case against the anchored evidence block alone.** The context is there to let you spot a bad anchor, not to answer the question. If you need the context to answer it, the anchor is wrong: `NEEDS_EDIT`.

**The anchors were never moved.** The import path forbids a reviewer from changing a source span, so every repair below is a repair to the *wording*. Where that leaves a claim resting on a term the span does not contain, it is flagged in section B rather than smoothed over.

Queue: 18 mandatory + 0 sampled from the 0 agreed passes (seed 20250819, rate 15%).

| id | verdict | risk | defects | one-line |
| --- | --- | --- | --- | --- |
| `01` | FIX_REQUIRED | LOW | MINER_QUESTION_HEADER_DEPENDENCY | What is the `summary_prompt` parameter used for? |
| `03` | FIX_REQUIRED | LOW | MINER_QUESTION_HEADER_DEPENDENCY | What kinds of values can an agent's `prompt` configuration accept? |
| `04` | FIX_REQUIRED | LOW | MINER_QUESTION_HEADER_DEPENDENCY | What kinds of values can the `source` field of a search result contain? |
| `05` | FIX_REQUIRED | LOW | MINER_QUESTION_HEADER_DEPENDENCY | What does setting `restart` to `true` do for the Bash tool? |
| `06` | FIX_REQUIRED | LOW | MINER_QUESTION_HEADER_DEPENDENCY | What is the minimum allowed `max_tokens` value for the advisor tool? |
| `07` | FIX_REQUIRED | LOW | MINER_QUESTION_HEADER_DEPENDENCY | What does the `pause_after_compaction` parameter control? |
| `08` | FIX_REQUIRED | LOW | MINER_QUESTION_HEADER_DEPENDENCY | What is the maximum length of the `text` field when triggering a rout… |
| `09` | FIX_REQUIRED | LOW | MINER_QUESTION_HEADER_DEPENDENCY | What does `display_height_px` specify for the computer use tool? |
| `10` | FIX_REQUIRED | LOW | QUESTION_AUTHORING_REQUIRED | What attribute does the `parse()` method return after transforming th… |
| `11` | FIX_REQUIRED | LOW | QUESTION_AUTHORING_REQUIRED | What happens in Claude Sonnet 5 if `temperature`, `top_p`, or `top_k`… |
| `12` | FIX_REQUIRED | LOW | MINER_EVIDENCE_DEFECT | Can a prompt below the applicable minimum cacheable length be cached … |
| `13` | FIX_REQUIRED | LOW | QUESTION_AUTHORING_REQUIRED | Why must `TUNNEL_TOKEN` be exported again in every fresh shell and af… |
| `14` | FIX_REQUIRED | LOW | QUESTION_AUTHORING_REQUIRED | What `max_tokens` cap does the `output-300k-2026-03-24` beta header e… |
| `15` | FIX_REQUIRED | LOW | QUESTION_AUTHORING_REQUIRED | When does `ScriptedModel` record a model call relative to resolving o… |
| `16` | FIX_REQUIRED | LOW | QUESTION_AUTHORING_REQUIRED | On Google Cloud Agent Platform, where is `anthropic_version` supplied… |
| `17` | FIX_REQUIRED | LOW | QUESTION_AUTHORING_REQUIRED | For a method calling `/v1/parents/{parent_id}/children/{child_id}`, w… |
| `18` | FIX_REQUIRED | LOW | MINER_EVIDENCE_DEFECT | For an explicit server-side fallback entry, which per-attempt setting… |
| `02` | FIX_REQUIRED | HIGH | MINER_QUESTION_HEADER_DEPENDENCY | What URL scheme must the MCP connector's `url` value start with? |

---

## A. Fast track — every asserted term is in the anchored span

Read the question, glance at the span, decide. These carry no detected gap between what the case claims and what its anchor contains.

#### GOLD-B002-01 · FIX_REQUIRED · risk LOW

**Q.** What is the `summary_prompt` parameter used for?

**A.** It specifies a custom prompt for summary generation.

**Claims**
  1. `summary_prompt` is used to provide a custom prompt for summary generation.

**Evidence span** — `ver_1c53b961e1f5da8124a1e7e8eb92c941` 83548–83766 · Client-side compaction (SDK) > Configuration options

```
| `summary_prompt`          | string  | No       | See [Default summary prompt](https://platform.claude.com/docs/en/build-with-claude/context-editing#default-summary-prompt) | Custom prompt for summary generation     |
```

<details><summary>surrounding context</summary>

```
…ken count at which compaction triggers |
| `model`                   | string  | No       | Same as main model                                                                                                         | Model to use for generating summaries    |
  ⟦SPAN⟧
#### Choosing a token threshold

The threshold determines when compaction occurs. A lower threshold means more frequent compactions with smaller context windows. A higher threshold allows more context but risks hitting limits.

<Tabs>
  <Tab title="cURL">…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**MINER_QUESTION_HEADER_DEPENDENCY — what was repaired.** The anchored row is sound evidence; the miner's exported question asked about a column whose meaning lives in a table header outside the row. The question was re-authored around a fact stated inside the row, and the anchor did not move.

*Critical claim strings, each verified inside the span above:* `summary_prompt`, `Custom prompt for summary generation`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-01` in `human_decisions_batch_002.json`.

---

#### GOLD-B002-03 · FIX_REQUIRED · risk LOW

**Q.** What kinds of values can an agent's `prompt` configuration accept?

**A.** A static prompt object or a function.

**Claims**
  1. The agent `prompt` configuration accepts either a static prompt object or a function.

**Evidence span** — `ver_35cac5e98c151a17f941a6142d74709f` 2057–2208 · Agents > Basic configuration

```
| `prompt` | no | OpenAI Responses API prompt configuration. Accepts a static prompt object or a function. See [Prompt templates](#prompt-templates). |
```

<details><summary>surrounding context</summary>

```
…nt are:

| Property | Required | Description |
| --- | --- | --- |
| `name` | yes | Human-readable agent name. |
| `instructions` | no | System prompt or dynamic instructions callback. Strongly recommended. See [Dynamic instructions](#dynamic-instructions). |
  ⟦SPAN⟧
| `handoff_description` | no | Short description exposed when this agent is offered as a handoff target. |
| `handoffs` | no | Delegate the conversation to specialist agents. See [handoffs](handoffs.md). |
| `model` | no | Which LLM to use. See [Models](model…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**MINER_QUESTION_HEADER_DEPENDENCY — what was repaired.** The anchored row is sound evidence; the miner's exported question asked about a column whose meaning lives in a table header outside the row. The question was re-authored around a fact stated inside the row, and the anchor did not move.

*Critical claim strings, each verified inside the span above:* `prompt`, `Accepts a static prompt object or a function`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-03` in `human_decisions_batch_002.json`.

---

#### GOLD-B002-04 · FIX_REQUIRED · risk LOW

**Q.** What kinds of values can the `source` field of a search result contain?

**A.** Any stable string, such as a URL or an internal identifier.

**Claims**
  1. The search-result `source` field can be any stable string, including a URL or internal identifier.

**Evidence span** — `ver_42a4f3d941b664a285883aaf6ff90373` 2380–2517 · How it works > Required fields

```
| `source`  | string | The source of the content. Any stable string works: a URL, or an internal identifier such as `kb://article-1234` |
```

<details><summary>surrounding context</summary>

```
…---- | ---------------------------------------------------------------------------------------------------------------- |
| `type`    | string | Must be `"search_result"`                                                                                        |
  ⟦SPAN⟧
| `title`   | string | A descriptive title for the search result                                                                        |
| `content` | array  | An array of text blocks containing the actual content…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**MINER_QUESTION_HEADER_DEPENDENCY — what was repaired.** The anchored row is sound evidence; the miner's exported question asked about a column whose meaning lives in a table header outside the row. The question was re-authored around a fact stated inside the row, and the anchor did not move.

*Critical claim strings, each verified inside the span above:* `source`, `Any stable string works`, `a URL, or an internal identifier`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-04` in `human_decisions_batch_002.json`.

---

#### GOLD-B002-05 · FIX_REQUIRED · risk LOW

**Q.** What does setting `restart` to `true` do for the Bash tool?

**A.** It restarts the bash session.

**Claims**
  1. Setting `restart` to `true` restarts the bash session.

**Evidence span** — `ver_9bf8513721dc2d1ef3e1ec42bf535dc6` 7758–7826 · Parameters

```
| `restart` | No       | Set to `true` to restart the bash session |
```

<details><summary>surrounding context</summary>

```
…he input fields Claude sets when it calls the tool.

| Parameter | Required | Description                               |
| --------- | -------- | ----------------------------------------- |
| `command` | Yes\*    | The bash command to run                   |
  ⟦SPAN⟧
\*Required unless using `restart`

To handle `restart: true`, kill the shell process, start a new one, and return a `tool_result` that confirms the restart. A restarted session starts clean: the working directory, environment variables, and any running proce…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**MINER_QUESTION_HEADER_DEPENDENCY — what was repaired.** The anchored row is sound evidence; the miner's exported question asked about a column whose meaning lives in a table header outside the row. The question was re-authored around a fact stated inside the row, and the anchor did not move.

*Critical claim strings, each verified inside the span above:* `restart`, `` Set to `true` to restart the bash session ``

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-05` in `human_decisions_batch_002.json`.

---

#### GOLD-B002-06 · FIX_REQUIRED · risk LOW

**Q.** What is the minimum allowed `max_tokens` value for the advisor tool?

**A.** 1024.

**Claims**
  1. The advisor tool's `max_tokens` value has a minimum of 1024.

**Evidence span** — `ver_b8b18cda9b875d51a2ce979a1bf4e909` 13205–13710 · Tool parameters

```
| `max_tokens` | integer        | advisor model's output cap | Caps the advisor's total output (thinking plus text) per call. Minimum 1024. See [Capping advisor output](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool#capping-advisor-output).                                                                                                                                                                                                                                            |
```

<details><summary>surrounding context</summary>

```
…s_exceeded"` and the executor continues without further advice. This is a per-request cap, not a per-conversation cap. See [Cost control](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool#cost-control) for conversation-level limits. |
  ⟦SPAN⟧
| `caching`    | object \| null | `null` (off)               | Enables [prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) for the advisor's own transcript across calls within a conversation. See [Advisor prompt caching](htt…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**MINER_QUESTION_HEADER_DEPENDENCY — what was repaired.** The anchored row is sound evidence; the miner's exported question asked about a column whose meaning lives in a table header outside the row. The question was re-authored around a fact stated inside the row, and the anchor did not move.

*Critical claim strings, each verified inside the span above:* `max_tokens`, `Minimum 1024`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-06` in `human_decisions_batch_002.json`.

---

#### GOLD-B002-07 · FIX_REQUIRED · risk LOW

**Q.** What does the `pause_after_compaction` parameter control?

**A.** Whether to pause after generating the compaction summary.

**Claims**
  1. `pause_after_compaction` controls whether execution pauses after the compaction summary is generated.

**Evidence span** — `ver_c60f7418b69b6610bd20e974b92cdd8c` 9443–9648 · Parameters

```
| `pause_after_compaction` | boolean | `false`                                     | Whether to pause after generating the compaction summary                                                               |
```

<details><summary>surrounding context</summary>

```
…|
| `trigger`                | object  | `{"type": "input_tokens", "value": 150000}` | When to trigger compaction. `input_tokens` is the only supported trigger type. `value` must be at least 50,000 tokens. |
  ⟦SPAN⟧
| `instructions`           | string  | `null`                                      | Custom summarization prompt. Completely replaces the default prompt when provided.                                     |

### Trigger configuration

Configure when compaction…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**MINER_QUESTION_HEADER_DEPENDENCY — what was repaired.** The anchored row is sound evidence; the miner's exported question asked about a column whose meaning lives in a table header outside the row. The question was re-authored around a fact stated inside the row, and the anchor did not move.

*Critical claim strings, each verified inside the span above:* `pause_after_compaction`, `Whether to pause after generating the compaction summary`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-07` in `human_decisions_batch_002.json`.

---

#### GOLD-B002-08 · FIX_REQUIRED · risk LOW

**Q.** What is the maximum length of the `text` field when triggering a routine through the API?

**A.** 65,536 characters.

**Claims**
  1. The routine-trigger `text` field has a maximum length of 65,536 characters.

**Evidence span** — `ver_d81ee605bd8bbb880deea432e51462ac` 8144–8480 · Trigger a routine > Request body

```
| `text` | string | No       | Initial context for this run, such as an alert body, a failing log line, or a git diff. The value is freeform text and is not parsed; if you send JSON or another structured payload, the routine receives it as a literal string. Passed to the routine alongside its saved prompt. Maximum 65,536 characters. |
```

<details><summary>surrounding context</summary>

```
…----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  ⟦SPAN⟧
The body is optional. Unknown fields in the body are ignored.

### Response

A successful request returns `200 OK` with the new session details:

```json
{
  "type": "routine_fire",
  "claude_code_session_id": "session_01HJKLMNOPQRSTUVWXYZ",
  "claude_code_s…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**MINER_QUESTION_HEADER_DEPENDENCY — what was repaired.** The anchored row is sound evidence; the miner's exported question asked about a column whose meaning lives in a table header outside the row. The question was re-authored around a fact stated inside the row, and the anchor did not move.

*Critical claim strings, each verified inside the span above:* `text`, `Maximum 65,536 characters`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-08` in `human_decisions_batch_002.json`.

---

#### GOLD-B002-09 · FIX_REQUIRED · risk LOW

**Q.** What does `display_height_px` specify for the computer use tool?

**A.** The display height in pixels.

**Claims**
  1. `display_height_px` specifies the display height in pixels.

**Evidence span** — `ver_d9ba3ab0d872dd86047c7ed6dc783235` 33443–33611 · How to implement computer use > Tool parameters

```
| `display_height_px` | Yes      | Display height in pixels                                                                                                            |
```

<details><summary>surrounding context</summary>

```
…|
| `display_width_px`  | Yes      | Display width in pixels                                                                                                             |
  ⟦SPAN⟧
| `display_number`    | No       | Display number for X11 environments                                                                                                 |
| `enable_zoom`       | No       | Enable zoom action (`computer_20251124` only). Set to `…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**MINER_QUESTION_HEADER_DEPENDENCY — what was repaired.** The anchored row is sound evidence; the miner's exported question asked about a column whose meaning lives in a table header outside the row. The question was re-authored around a fact stated inside the row, and the anchor did not move.

*Critical claim strings, each verified inside the span above:* `display_height_px`, `Display height in pixels`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-09` in `human_decisions_batch_002.json`.

---

#### GOLD-B002-10 · FIX_REQUIRED · risk LOW

**Q.** What attribute does the `parse()` method return after transforming the Pydantic model and validating the response?

**A.** `parsed_output`

**Claims**
  1. The `parse()` method transforms the Pydantic model, validates the response, and returns a `parsed_output` attribute.

**Evidence span** — `ver_0865c9612dfe97d8f30dd870dd12e53e` 24246–24381 · JSON outputs > Working with JSON outputs in SDKs > SDK-specific methods

```
    The `parse()` method automatically transforms your Pydantic model, validates the response, and returns a `parsed_output` attribute.
```

<details><summary>surrounding context</summary>

```
…required: [name, email, plan_interest]
          additionalProperties: false
    YAML
    ```

    ```yaml Output
    name: John Smith
    email: john@example.com
    ```
  </Tab>

  <Tab title="Python">
    **`client.messages.parse()` (Recommended)**
  ⟦SPAN⟧
```python
    from pydantic import BaseModel
    # ...
    class ContactInfo(BaseModel):
        name: str
        email: str
        plan_interest: str
    # ...
    response = client.messages.parse(
        model="claude-opus-5",
        max_tokens=102…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**QUESTION_AUTHORING_REQUIRED — what was repaired.** No defect. The span is self-contained and the reviewer authored the question, answer and claims, which is how the prose miner is designed to work.

*Critical claim strings, each verified inside the span above:* `parse()`, `validates the response`, `parsed_output`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-10` in `human_decisions_batch_002.json`.

---

#### GOLD-B002-11 · FIX_REQUIRED · risk LOW

**Q.** What happens in Claude Sonnet 5 if `temperature`, `top_p`, or `top_k` is set to a non-default value?

**A.** The request returns a 400 error.

**Claims**
  1. Claude Sonnet 5 returns a 400 error when `temperature`, `top_p`, or `top_k` is set to a non-default value.

**Evidence span** — `ver_6c0983aad96f198367a0de369b3bb86c` 205–656 · Preamble

```
Claude Sonnet 5 is the next generation of Anthropic's Sonnet model family. It is a drop-in upgrade for Claude Sonnet 4.6 with three behavior changes: [adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) is on by default, manual extended thinking now returns a 400 error (it was deprecated on Claude Sonnet 4.6), and setting sampling parameters (`temperature`, `top_p`, `top_k`) to non-default values returns a 400 error.
```

<details><summary>surrounding context</summary>

```
…---
title: What's new in Claude Sonnet 5
url: https://platform.claude.com/docs/en/about-claude/models/whats-new-sonnet-5
description: Overview of new features and behavior changes in Claude Sonnet 5.
---
  ⟦SPAN⟧
This page summarizes everything new at launch, including a new tokenizer.

## New model

| Model           | API model ID      | Description                                    |
| --------------- | ----------------- | -----------------------------------------…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**QUESTION_AUTHORING_REQUIRED — what was repaired.** No defect. The span is self-contained and the reviewer authored the question, answer and claims, which is how the prose miner is designed to work.

*Critical claim strings, each verified inside the span above:* `Claude Sonnet 5`, `temperature`, `top_p`, `top_k`, `non-default values returns a 400 error`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-11` in `human_decisions_batch_002.json`.

---

#### GOLD-B002-12 · FIX_REQUIRED · risk LOW

**Q.** Can a prompt below the applicable minimum cacheable length be cached simply by marking it with `cache_control`?

**A.** No.

**Claims**
  1. A prompt below the applicable minimum cacheable length cannot be cached even when marked with `cache_control`.

**Evidence span** — `ver_7947433dfde6b3b8eccd0faa597c3c9a` 29744–31174 · Caching strategies and considerations > Cache limitations

```
On the Claude API, [Claude Platform on AWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws), [Google Cloud](https://platform.claude.com/docs/en/build-with-claude/claude-on-vertex-ai), and [Microsoft Foundry](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry), the minimum cacheable prompt length is:

* 512 tokens for Claude Opus 5, Claude Fable 5, and [Claude Mythos 5](https://anthropic.com/glasswing)
* 2,048 tokens for [Claude Mythos Preview](https://anthropic.com/glasswing) and Claude Opus 4.7
* 4,096 tokens for Claude Opus 4.6 and Claude Opus 4.5
* 1,024 tokens for Claude Opus 4.8, Claude Sonnet 5, Claude Sonnet 4.6, Claude Sonnet 4.5, Claude Opus 4.1 ([retired, except on Bedrock and Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations)), Claude Opus 4 ([retired, except on Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations)), and Claude Sonnet 4 ([retired, except on Bedrock and Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations))
* 4,096 tokens for Claude Haiku 4.5
* 2,048 tokens for Claude Haiku 3.5 ([retired, except on Bedrock and Google Cloud](https://platform.claude.com/docs/en/about-claude/model-deprecations))

These minimums apply on every platform where each model is available.

Shorter prompts cannot be cached, even if marked with `cache_control`.
```

<details><summary>surrounding context</summary>

```
…sn't increase your costs - you still pay the same amount based on what content is actually cached and read. The breakpoints give you control over what sections can be cached independently.

***

## Caching strategies and considerations

### Cache limitations
  ⟦SPAN⟧
Any requests to cache fewer than this number of tokens will be processed without caching, and no error is returned. To verify whether a prompt was cached, check the [response usage fields](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#t…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**MINER_EVIDENCE_DEFECT — what was repaired.** The anchor did not contain what its claim depends on, and was extended. Both spans and both hashes are retained below.

**Anchor extended** — 31104–31174 → 29744–31174 (+1360 before, +0 after). Extended backwards 1,360 characters to the sentence that introduces the per-model minimum cacheable prompt length, and the list of those minimums.

*Why complete:* The claim turns on "the applicable minimum cacheable length", and that phrase appears nowhere in the original span. A smaller extension is available and was rejected: starting at "These minimums apply on every platform…" costs only 71 extra characters but leaves the anchor opening on "These minimums", which is the same anaphoric defect one sentence further up. See the size warning below.

*Size warning:* 1,430 characters is a large anchor and does make the case easier to retrieve. The alternative 141-character anchor is recorded in the packet; choosing it means also weakening the claim to something the smaller span can support.

<details><summary>the span before the extension</summary>

```
Shorter prompts cannot be cached, even if marked with `cache_control`.
```

</details>

*Critical claim strings, each verified inside the span above:* `minimum cacheable prompt length`, `Shorter prompts cannot be cached`, `cache_control`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-12` in `human_decisions_batch_002.json`.

---

#### GOLD-B002-13 · FIX_REQUIRED · risk LOW

**Q.** Why must `TUNNEL_TOKEN` be exported again in every fresh shell and after a reboot for this Docker Compose deployment?

**A.** Because the compose file reads it from the host environment and has no default.

**Claims**
  1. The compose file reads `TUNNEL_TOKEN` from the host environment with no default, so the export must be repeated in every fresh shell and after a reboot.

**Evidence span** — `ver_b05e105d93045aff4c7ce998b198ae79` 17854–18006 · Install

```
The compose file reads `TUNNEL_TOKEN` from the host environment with no default, so the export must be repeated in every fresh shell and after a reboot.
```

<details><summary>surrounding context</summary>

```
…l --quiet mcp && python hello_server.py"
            restart: unless-stopped
        EOF
        ```
      </Step>

      <Step title="Start the deployment">
        ```bash
        docker compose up -d
        ```
      </Step>
    </Steps>
  </Tab>
</Tabs>
  ⟦SPAN⟧
For a multi-VM deployment, copy the `mcp-tunnel/` directory to each host, set `TUNNEL_TOKEN`, and run `docker compose up -d`. In the programmatic flow `TUNNEL_TOKEN` is `$(sudo cat data/tunnel-token)`; in the manual flow it's the value you copied from the Co…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**QUESTION_AUTHORING_REQUIRED — what was repaired.** No defect. The span is self-contained and the reviewer authored the question, answer and claims, which is how the prose miner is designed to work.

*Critical claim strings, each verified inside the span above:* `TUNNEL_TOKEN`, `from the host environment with no default`, `every fresh shell and after a reboot`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-13` in `human_decisions_batch_002.json`.

---

#### GOLD-B002-14 · FIX_REQUIRED · risk LOW

**Q.** What `max_tokens` cap does the `output-300k-2026-03-24` beta header enable for supported Message Batch requests?

**A.** 300,000 tokens.

**Claims**
  1. The `output-300k-2026-03-24` beta header raises the `max_tokens` cap to 300,000 for the supported Message Batch models listed in the evidence.

**Evidence span** — `ver_cec813c3bb15b76dcf16e7a0c2231ef1` 59581–59790 · Message Batches API > How to use the Message Batches API > Extended output (beta)

```
The `output-300k-2026-03-24` beta header raises the `max_tokens` cap to 300,000 for batch requests using Claude Opus 5, Claude Opus 4.8, Claude Opus 4.7, Claude Opus 4.6, Claude Sonnet 5, or Claude Sonnet 4.6.
```

<details><summary>surrounding context</summary>

```
…ch processing does not exhaust your organization's web-search rate limit. The batch retries throttled requests automatically; you don't need to handle this yourself, but very large web-search batches might take longer to complete.

### Extended output (beta)
  ⟦SPAN⟧
Include the header to generate outputs far longer than the standard 128k `max_tokens` limit in a single turn.

<Note>
  Extended output is available on the Message Batches API only, not the synchronous Messages API. It is supported on the Claude API and Claud…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**QUESTION_AUTHORING_REQUIRED — what was repaired.** No defect. The span is self-contained and the reviewer authored the question, answer and claims, which is how the prose miner is designed to work.

*Critical claim strings, each verified inside the span above:* `output-300k-2026-03-24`, `max_tokens`, `300,000`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-14` in `human_decisions_batch_002.json`.

---

#### GOLD-B002-15 · FIX_REQUIRED · risk LOW

**Q.** When does `ScriptedModel` record a model call relative to resolving or raising the selected step?

**A.** Before resolving or raising the selected step.

**Claims**
  1. `ScriptedModel` records each call before it resolves or raises the selected step.

**Evidence span** — `ver_d2295786320b2815477eb963eb1f5e8a` 7031–7112 · Testing > Agent workflow recipes > Inspect model calls

```
`ScriptedModel` records each call before it resolves or raises the selected step.
```

<details><summary>surrounding context</summary>

```
…quivalent dictionary form, `ModelResponse`, a normalized output-item sequence, or an exception. Prefer fixed output sequences when a response does not depend on the call because fixed scripts make unexpected turns easier to diagnose.

### Inspect model calls
  ⟦SPAN⟧
| Member | Contains |
| --- | --- |
| `calls` | Every `ModelCall` in invocation order |
| `first_call` | The first call, or `None` |
| `last_call` | The most recent call, or `None` |
| `remaining_steps` | The number of configured steps not yet consumed |

Co…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**QUESTION_AUTHORING_REQUIRED — what was repaired.** No defect. The span is self-contained and the reviewer authored the question, answer and claims, which is how the prose miner is designed to work.

*Critical claim strings, each verified inside the span above:* `ScriptedModel`, `records each call before it resolves or raises the selected step`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-15` in `human_decisions_batch_002.json`.

---

#### GOLD-B002-16 · FIX_REQUIRED · risk LOW

**Q.** On Google Cloud Agent Platform, where is `anthropic_version` supplied and what value must it have?

**A.** It is passed in the request body and must be `vertex-2023-10-16`.

**Claims**
  1. On Agent Platform, `anthropic_version` is passed in the request body rather than as a header.
  2. It must be set to `vertex-2023-10-16`.

**Evidence span** — `ver_e312b7f41115cc2b84cd36151efc6dd8` 455–725 · Preamble

```
* On Agent Platform, `model` is not passed in the request body. Instead, it is specified in the Google Cloud endpoint URL.
* On Agent Platform, `anthropic_version` is passed in the request body (rather than as a header), and must be set to the value `vertex-2023-10-16`.
```

<details><summary>surrounding context</summary>

```
…Platform](https://cloud.google.com/vertex-ai).
---

The API for accessing Claude on Google Cloud's Agent Platform is nearly identical to the [Messages API](https://platform.claude.com/docs/en/api/messages/create), with two key differences in request format:
  ⟦SPAN⟧
Agent Platform is also supported by Anthropic's official [client SDKs](https://platform.claude.com/docs/en/cli-sdks-libraries/overview). This guide walks you through making a request to Claude on Agent Platform using one of Anthropic's client SDKs.

Note tha…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**QUESTION_AUTHORING_REQUIRED — what was repaired.** No defect. The span is self-contained and the reviewer authored the question, answer and claims, which is how the prose miner is designed to work.

*Note:* the question mentions `Google Cloud Agent Platform` as framing only; no claim depends on it.

*Critical claim strings, each verified inside the span above:* `anthropic_version`, `passed in the request body`, `rather than as a header`, `vertex-2023-10-16`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-16` in `human_decisions_batch_002.json`.

---

#### GOLD-B002-17 · FIX_REQUIRED · risk LOW

**Q.** For a method calling `/v1/parents/{parent_id}/children/{child_id}`, which path parameter remains positional and how must the other be passed?

**A.** `child_id` remains positional; `parent_id` must be passed as a named argument.

**Claims**
  1. The last path parameter, `child_id`, is positional in the example.
  2. `parent_id` must be passed as a named argument.

**Evidence span** — `ver_e8a7b17b5af64679cadea33cd8f6d250` 1813–2009 · Migration guide > Breaking changes > Named path parameters

```
For example, for a method that would call an endpoint at `/v1/parents/{parent_id}/children/{child_id}`, only the _last_ path parameter is positional and the rest must be passed as named arguments.
```

<details><summary>surrounding context</summary>

```
…| undefined>`.

### Named path parameters

Methods that take multiple path parameters typically now use named instead of positional arguments for better clarity and to prevent a footgun where it was easy to accidentally pass arguments in the incorrect order.
  ⟦SPAN⟧
```ts
// Before
client.parents.children.retrieve('p_123', 'c_456');

// After
client.parents.children.retrieve('c_456', { parent_id: 'p_123' });
```

<details>

<summary>This affects the following methods</summary>

- `client.fineTuning.checkpoints.permissio…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**QUESTION_AUTHORING_REQUIRED — what was repaired.** No defect. The span is self-contained and the reviewer authored the question, answer and claims, which is how the prose miner is designed to work.

*Critical claim strings, each verified inside the span above:* `parent_id`, `child_id`, `only the _last_ path parameter is positional`, `must be passed as named arguments`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-17` in `human_decisions_batch_002.json`.

---

#### GOLD-B002-18 · FIX_REQUIRED · risk LOW

**Q.** For an explicit server-side fallback entry, which per-attempt settings can be overridden?

**A.** `max_tokens`, `thinking`, `output_config`, and `speed`.

**Claims**
  1. Each explicit fallback entry can override `max_tokens`, `thinking`, `output_config`, and `speed` for that attempt only.

**Evidence span** — `ver_fa78e1feb6289d6bcb22305e61bbbfc3` 25347–25931 · Server-side fallback > Naming your own fallback models

```
A few rules apply to the `fallbacks` list:

* Entries are tried in order. Each must be distinct from the other entries and from the requested model.
* Each entry must be one of the requested model's permitted targets. With the beta header set, that list is published as `allowed_fallback_models` on the model's entry in the [Models API](https://platform.claude.com/docs/en/api/models/list).
* Each entry names a `model` and can override `max_tokens`, `thinking`, `output_config`, and `speed` for that attempt only.
* The request must be valid as a direct request to every model named.
```

<details><summary>surrounding context</summary>

```
…ges.create(
    model: "claude-fable-5",
    max_tokens: 1024,
    messages: [{role: "user", content: "Hello, Claude"}],
    fallbacks: [{model: "claude-opus-4-8"}],
    betas: ["server-side-fallback-2026-07-01"]
  )

  puts response.model
  ```
</CodeGroup>
  ⟦SPAN⟧
If a fallback model does not support a feature the request uses, the API rejects the request up front.
* As with the default mode, only a safety classifier decline triggers the fallback. A rate limit, overload, or server error on the requested model is return…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**MINER_EVIDENCE_DEFECT — what was repaired.** The anchor did not contain what its claim depends on, and was extended. Both spans and both hashes are retained below.

**Anchor extended** — 25565–25931 → 25347–25931 (+218 before, +0 after). Extended backwards 218 characters to the line that names the `fallbacks` list, so "Each entry" has something to refer to.

*Why complete:* The original span opened on "With the beta header set, that list…" and then said "Each entry…" — both referring to the `fallbacks` list, which was outside the anchor. The repaired span states what the list is before making rules about its entries.

<details><summary>the span before the extension</summary>

```
With the beta header set, that list is published as `allowed_fallback_models` on the model's entry in the [Models API](https://platform.claude.com/docs/en/api/models/list).
* Each entry names a `model` and can override `max_tokens`, `thinking`, `output_config`, and `speed` for that attempt only.
* The request must be valid as a direct request to every model named.
```

</details>

*Critical claim strings, each verified inside the span above:* `fallbacks`, `max_tokens`, `thinking`, `output_config`, `speed`, `for that attempt only`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-18` in `human_decisions_batch_002.json`.

---

---

## B. Check the anchor before approving

Each of these asserts something the anchored span does not contain. This is the OA-002 defect class, and it is the reason the whole batch exists — do not skim these.

#### GOLD-B002-02 · FIX_REQUIRED · risk HIGH

**Q.** What URL scheme must the MCP connector's `url` value start with?

**A.** `https://`

**Claims**
  1. The MCP server `url` must start with `https://`.

**Evidence span** — `ver_279d37a3a0cc4e8a9209e01f16f9df88` 11319–11677 · MCP server configuration > Field descriptions

```
| `url`                 | string | Yes      | The URL of the MCP server. Must start with https\://.                                                                                                                                                                                                                                                                  |
```

<details><summary>surrounding context</summary>

```
…|
  ⟦SPAN⟧
| `name`                | string | Yes      | A unique identifier for this MCP server. Must be referenced by exactly one MCPToolset in the `tools` array.…
```

</details>

**Why you are seeing this.** A claim asserts `https://`, which the anchored span does not contain and the document title and section path do not supply either. Approving accepts a claim the anchor cannot support on its own.

**MINER_QUESTION_HEADER_DEPENDENCY — what was repaired.** The anchored row is sound evidence; the miner's exported question asked about a column whose meaning lives in a table header outside the row. The question was re-authored around a fact stated inside the row, and the anchor did not move.

*Critical claim strings, each verified inside the span above:* `url`, `The URL of the MCP server`, `Must start with https`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B002-02` in `human_decisions_batch_002.json`.

---

## Audit

The full history — the generator's original proposal, the reviewer's verdict and boolean checks, every numbered revision, and the anchor as first mined — is retained per candidate in `gold_batch_001_qc.json` under `audit`. Nothing was overwritten, and no anchor was changed (0 disputes recorded).

OA-002 is a defect in the original development set and is deliberately not part of this batch. Its `development/v2` correction remains proposed and unapplied.
