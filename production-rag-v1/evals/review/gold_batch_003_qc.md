# GOLD-001 — batch 003 human QC packet

**20 decisions.** 19 fast track, 1 need the anchor checked, 0 recommended for rejection.

Nothing in this packet is gold. A candidate becomes `human_verified` only when you record `APPROVE` for it in `evals/review/human_decisions_batch_003.json` and import that file. An independent-review PASS produces `dual_llm_pass` and stops there — two AI systems agreeing is not human verification.

**Judge each case against the anchored evidence block alone.** The context is there to let you spot a bad anchor, not to answer the question. If you need the context to answer it, the anchor is wrong: `NEEDS_EDIT`.

**The anchors were never moved.** The import path forbids a reviewer from changing a source span, so every repair below is a repair to the *wording*. Where that leaves a claim resting on a term the span does not contain, it is flagged in section B rather than smoothed over.

Queue: 20 mandatory + 0 sampled from the 0 agreed passes (seed 20250819, rate 15%).

| id | verdict | risk | defects | one-line |
| --- | --- | --- | --- | --- |
| `01` | PASS | LOW | — | What happens when `citations.enabled` is set to `true`? |
| `02` | FIX_REQUIRED | LOW | QUESTION_SCOPE, CLAIM_SCOPE | In a Skill definition, what does the `description` field enable and w… |
| `03` | PASS | LOW | — | What happens when setting `max_tokens` above the advisor model's own … |
| `05` | PASS | LOW | — | What happens if your tool result doesn't arrive within about 4 minutes? |
| `06` | FIX_REQUIRED | LOW | EVIDENCE_BOUNDARY, QUESTION_SCOPE, CLAIM_SCOPE | On Claude Sonnet 5, what happens if `temperature`, `top_p`, or `top_k… |
| `07` | PASS | LOW | — | What does the `clear_tool_inputs` parameter do? |
| `08` | PASS | LOW | — | What is the `old_str` option? |
| `09` | PASS | LOW | — | What is the `new_str` option? |
| `10` | FIX_REQUIRED | LOW | CLAIM_SCOPE | What is the documented status of `budget_tokens` on Claude Opus 4.6 a… |
| `11` | FIX_REQUIRED | LOW | CLAIM_SCOPE | What happens if manual extended thinking `thinking: {type: "enabled",… |
| `12` | FIX_REQUIRED | LOW | CATEGORY_MISCLASSIFICATION | What do the `type` and `country` options specify in Localization? |
| `13` | FIX_REQUIRED | LOW | QUESTION_SCOPE, CLAIM_SCOPE | If both a per-call `rejection_message` and the run-wide formatter are… |
| `14` | FIX_REQUIRED | LOW | QUESTION_SCOPE, CLAIM_SCOPE | Without explicit authentication, what does `AWS_BEARER_TOKEN_BEDROCK`… |
| `15` | PASS | LOW | — | What is the `ToolsToFinalOutputFunction` option? |
| `16` | FIX_REQUIRED | LOW | EVIDENCE_BOUNDARY, QUESTION_SCOPE | In a Chat Completions `ChunkEvent`, what does the `chunk` field contain? |
| `17` | FIX_REQUIRED | LOW | EVIDENCE_BOUNDARY, QUESTION_SCOPE | In a Chat Completions `ContentDeltaEvent`, what does the `parsed` fie… |
| `18` | FIX_REQUIRED | LOW | CATEGORY_MISCLASSIFICATION | What do the `tool_name_override` and `tool_description_override` opti… |
| `19` | FIX_REQUIRED | LOW | EVIDENCE_BOUNDARY, CATEGORY_MISCLASSIFICATION | What do the `kind` and `tool_type` options specify in `tool_error_for… |
| `20` | FIX_REQUIRED | LOW | CATEGORY_MISCLASSIFICATION | What do the `workflow_name` and `trace_id` options specify in Traces … |
| `04` | FIX_REQUIRED | HIGH | EVIDENCE_BOUNDARY, QUESTION_SCOPE | What happens when the executor and advisor models requested for the a… |

---

## A. Fast track — every asserted term is in the anchored span

Read the question, glance at the span, decide. These carry no detected gap between what the case claims and what its anchor contains.

#### GOLD-B003-01 · PASS · risk LOW

`reasoning_type: configuration_interaction` · `evidence_shape: single_span` · `requires_all_evidence: False`

**Q.** What happens when `citations.enabled` is set to `true`?

**A.** Claude attaches citation references to the text blocks that draw on the search result.

**Claims**
  1. When `citations.enabled` is set to `true`, Claude attaches citation references to the text blocks that draw on the search result.

**Evidence span** — `ver_42a4f3d941b664a285883aaf6ff90373` 80381–80510 · Advanced usage > Citation control

```
When `citations.enabled` is set to `true`, Claude attaches citation references to the text blocks that draw on the search result.
```

<details><summary>surrounding context</summary>

```
…on
{
  "type": "search_result",
  "source": "https://docs.company.com/guide",
  "title": "User Guide",
  "content": [{ "type": "text", "text": "Important documentation..." }],
  "citations": {
    "enabled": true // Enable citations for this result
  }
}
```
  ⟦SPAN⟧
<Warning>
  Citations are all-or-nothing: either all search results in a request must have citations enabled, or all must have them disabled. Mixing search results with different citation settings results in an error.
</Warning>

## Best practices

### For t…
```

</details>

**Why you are seeing this.** Both models passed this case. It is here because agreement between two models is correlated evidence, not independent confirmation, and this candidate was drawn as the deterministic QC sample.

**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `citations.enabled`, `true`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-01` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-02 · FIX_REQUIRED · risk LOW

`reasoning_type: configuration_interaction` · `evidence_shape: single_span` · `requires_all_evidence: False`

**Q.** In a Skill definition, what does the `description` field enable and what should it include?

**A.** It enables Skill discovery and should include both what the Skill does and when to use it.

**Claims**
  1. The Skill `description` field enables Skill discovery and should include both what the Skill does and when to use it.

**Evidence span** — `ver_90de89ac7da393e4d9056cf12204d046` 6496–6607 · Skill structure > Writing effective descriptions

```
The `description` field enables Skill discovery and should include both what the Skill does and when to use it.
```

<details><summary>surrounding context</summary>

```
…t naming makes it easier to:

* Reference Skills in documentation and conversations
* Understand what a Skill does at a glance
* Organize and search through multiple Skills
* Maintain a professional, cohesive skill library

### Writing effective descriptions
  ⟦SPAN⟧
<Warning>
  **Always write in third person**. The description is injected into the system prompt, and inconsistent point-of-view can cause discovery problems.

  * **Good:** "Processes Excel files and generates reports"
  * **Avoid:** "I can help you process…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**QUESTION_SCOPE — what was repaired.** The question was ambiguous or broader than the evidence supports; it was re-scoped to what the anchor states.

**CLAIM_SCOPE — what was repaired.** The claim asserted more, or less, than the anchored evidence states; it was brought back to the source's own scope.

**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `description`, `Skill discovery`, `what the Skill does`, `when to use it`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-02` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-03 · PASS · risk LOW

`reasoning_type: error_behavior` · `evidence_shape: single_span` · `requires_all_evidence: False`

**Q.** What happens when setting `max_tokens` above the advisor model's own output cap?

**A.** It returns a 400 error.

**Claims**
  1. Setting `max_tokens` above the advisor model's own output cap returns a 400 error.

**Evidence span** — `ver_b8b18cda9b875d51a2ce979a1bf4e909` 85181–85263 · Best practices > Capping advisor output

```
Setting `max_tokens` above the advisor model's own output cap returns a 400 error.
```

<details><summary>surrounding context</summary>

```
…opus-5',
          'max_tokens' => 2048,
      ],
  ];
  ```

  ```ruby Ruby
  tools = [
    {
      type: "advisor_20260301",
      name: "advisor",
      model: "claude-opus-5",
      max_tokens: 2048
    }
  ]
  ```
</CodeGroup>

The minimum value is 1024.
  ⟦SPAN⟧
The cap applies to each advisor call independently and is not shared across calls in the same request.

This is not a hard truncation alone. The server also passes the advisor its remaining-token budget, so the advisor shapes its response to fit.

**Recommend…
```

</details>

**Why you are seeing this.** Both models passed this case. It is here because agreement between two models is correlated evidence, not independent confirmation, and this candidate was drawn as the deterministic QC sample.

**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `max_tokens`, `a 400 error`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-03` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-05 · PASS · risk LOW

`reasoning_type: error_behavior` · `evidence_shape: single_span` · `requires_all_evidence: False`

**Q.** What happens if your tool result doesn't arrive within about 4 minutes?

**A.** The pending call raises a `TimeoutError` inside Claude's running code.

**Claims**
  1. If your tool result doesn't arrive within about 4 minutes, the pending call raises a `TimeoutError` inside Claude's running code.

**Evidence span** — `ver_7cd600e1124f25cfedc3f1f6d5c297e5` 48472–48601 · Process results programmatically > Error handling > Container expiration during tool call

```
If your tool result doesn't arrive within about 4 minutes, the pending call raises a `TimeoutError` inside Claude's running code.
```

<details><summary>surrounding context</summary>

```
…| `tool_choice` names a tool whose `allowed_callers` does not include `"direct"` | Either add `"direct"` to that tool's `allowed_callers`, or remove the tool from `tool_choice` and let Claude invoke it from code |

### Container expiration during tool call
  ⟦SPAN⟧
Claude sees the error in `stderr` and typically retries the call:

```json
{
  "type": "code_execution_tool_result",
  "tool_use_id": "srvtoolu_abc123",
  "content": {
    "type": "code_execution_result",
    "stdout": "",
    "stderr": "TimeoutError: Calling…
```

</details>

**Why you are seeing this.** Both models passed this case. It is here because agreement between two models is correlated evidence, not independent confirmation, and this candidate was drawn as the deterministic QC sample.

**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `TimeoutError`, `` a `TimeoutError` inside Claude's running code ``

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-05` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-06 · FIX_REQUIRED · risk LOW

`reasoning_type: error_behavior` · `evidence_shape: single_span` · `requires_all_evidence: False`

**Q.** On Claude Sonnet 5, what happens if `temperature`, `top_p`, or `top_k` is set to a non-default value?

**A.** The request returns a 400 error.

**Claims**
  1. On Claude Sonnet 5, setting `temperature`, `top_p`, or `top_k` to a non-default value returns a 400 error.

**Evidence span** — `ver_6c0983aad96f198367a0de369b3bb86c` 1820–2293 · Behavior changes > Sampling parameters not accepted

```
On Claude Sonnet 5, the same requests run with [adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/thinking). To turn thinking off, pass `thinking: {type: "disabled"}`. Because `max_tokens` is a hard limit on total output (thinking plus response text), revisit it for workloads that ran without thinking on Claude Sonnet 4.6.

### Sampling parameters not accepted

Setting `temperature`, `top_p`, or `top_k` to a non-default value returns a 400 error.
```

<details><summary>surrounding context</summary>

```
…complete pricing and specs, see the [models overview](https://platform.claude.com/docs/en/about-claude/models/overview).

## Behavior changes

### Adaptive thinking on by default

On Claude Sonnet 4.6, requests without a `thinking` field run without thinking.
  ⟦SPAN⟧
Remove these parameters when migrating; the default value (or omitting the parameter) is accepted. Use system-prompt instructions to guide model behavior. This is new for Sonnet-class models; the same constraint was previously introduced on Claude Opus 4.7.…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**EVIDENCE_BOUNDARY — what was repaired.** The anchor did not carry the scope its claim depends on, and was extended or split into precise spans. Both old and new spans are retained.

**QUESTION_SCOPE — what was repaired.** The question was ambiguous or broader than the evidence supports; it was re-scoped to what the anchor states.

**CLAIM_SCOPE — what was repaired.** The claim asserted more, or less, than the anchored evidence states; it was brought back to the source's own scope.

**Anchor changed** (MODEL_SCOPE_COMPLETION) — 2207–2293 → 1820–2293

*Why:* The nearest occurrence of "Claude Sonnet 5" is 384 characters earlier, in the adjacent "Adaptive thinking on by default" subsection. The extension is 470 characters and under the soft cap, but it drags in a subsection about thinking that the claim does not use. This is a real trade and the owner should confirm it rather than have it made quietly.

**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `Claude Sonnet 5`, `temperature`, `top_p`, `top_k`, `400 error`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-06` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-07 · PASS · risk LOW

`reasoning_type: exact_lookup` · `evidence_shape: single_span` · `requires_all_evidence: False`

**Q.** What does the `clear_tool_inputs` parameter do?

**A.** Controls whether the tool call parameters are cleared along with the tool results. By default, only the tool results are cleared while keeping Claude's original tool calls visible.

**Claims**
  1. The `clear_tool_inputs` parameter controls whether the tool call parameters are cleared along with the tool results. By default, only the tool results are cleared while keeping Claude's original tool calls visible.

**Evidence span** — `ver_1c53b961e1f5da8124a1e7e8eb92c941` 56502–56797 · Configuration options for tool result clearing

```
| `clear_tool_inputs`  | `false`              | Controls whether the tool call parameters are cleared along with the tool results. By default, only the tool results are cleared while keeping Claude's original tool calls visible.                                                                  |
```

<details><summary>surrounding context</summary>

```
…| List of tool names whose tool uses and results should never be cleared. Useful for preserving important context.                                                                                                                                      |
  ⟦SPAN⟧
## Context editing response

You can see which context edits were applied to your request using the `context_management` response field, along with helpful statistics about the content and input tokens cleared.

```json Output
{
  "id": "msg_013Zva2CMHLNnXjN…
```

</details>

**Why you are seeing this.** Both models passed this case. It is here because agreement between two models is correlated evidence, not independent confirmation, and this candidate was drawn as the deterministic QC sample.

**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `clear_tool_inputs`, `Controls whether the tool call parameters are cleared along`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-07` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-08 · PASS · risk LOW

`reasoning_type: exact_lookup` · `evidence_shape: single_span` · `requires_all_evidence: False`

**Q.** What is the `old_str` option?

**A.** The text to replace (must match exactly, including whitespace and indentation).

**Claims**
  1. `old_str`: The text to replace (must match exactly, including whitespace and indentation).

**Evidence span** — `ver_72833144cee232446fa450e9e040995a` 9719–9810 · Use the text editor tool > Text editor tool commands > str\_replace

```
* `old_str`: The text to replace (must match exactly, including whitespace and indentation)
```

<details><summary>surrounding context</summary>

```
…/Accordion>

#### str\_replace

The `str_replace` command allows Claude to replace a specific string in a file with a new string. This is used for making precise edits.

Parameters:

* `command`: Must be "str\_replace"
* `path`: The path to the file to modify
  ⟦SPAN⟧
* `new_str`: The new text to insert in place of the old text

<Accordion title="Example str_replace command">
  ```json
  {
    "type": "tool_use",
    "id": "toolu_01A09q90qw90lq917835lq9",
    "name": "str_replace_based_edit_tool",
    "input": {
      "com…
```

</details>

**Why you are seeing this.** Both models passed this case. It is here because agreement between two models is correlated evidence, not independent confirmation, and this candidate was drawn as the deterministic QC sample.

**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `old_str`, `The text to replace (must match exactly, including whitespac`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-08` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-09 · PASS · risk LOW

`reasoning_type: exact_lookup` · `evidence_shape: single_span` · `requires_all_evidence: False`

**Q.** What is the `new_str` option?

**A.** The new text to insert in place of the old text.

**Claims**
  1. `new_str`: The new text to insert in place of the old text.

**Evidence span** — `ver_72833144cee232446fa450e9e040995a` 9811–9871 · Use the text editor tool > Text editor tool commands > str\_replace

```
* `new_str`: The new text to insert in place of the old text
```

<details><summary>surrounding context</summary>

```
…c string in a file with a new string. This is used for making precise edits.

Parameters:

* `command`: Must be "str\_replace"
* `path`: The path to the file to modify
* `old_str`: The text to replace (must match exactly, including whitespace and indentation)
  ⟦SPAN⟧
<Accordion title="Example str_replace command">
  ```json
  {
    "type": "tool_use",
    "id": "toolu_01A09q90qw90lq917835lq9",
    "name": "str_replace_based_edit_tool",
    "input": {
      "command": "str_replace",
      "path": "primes.py",
      "old_s…
```

</details>

**Why you are seeing this.** Both models passed this case. It is here because agreement between two models is correlated evidence, not independent confirmation, and this candidate was drawn as the deterministic QC sample.

**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `new_str`, `The new text to insert in place of the old text`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-09` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-10 · FIX_REQUIRED · risk LOW

`reasoning_type: lifecycle` · `evidence_shape: single_span` · `requires_all_evidence: False`

**Q.** What is the documented status of `budget_tokens` on Claude Opus 4.6 and Claude Sonnet 4.6?

**A.** It is deprecated.

**Claims**
  1. `budget_tokens` is deprecated on Claude Opus 4.6 and Claude Sonnet 4.6.

**Evidence span** — `ver_3acba29982fd40528ac6498dd0d5fe18` 19000–19251 · Migrating to adaptive thinking

```
* You use Claude Opus 4.6 or Claude Sonnet 4.6, where `budget_tokens` is deprecated.
* You are moving to Claude Opus 4.7, Claude Opus 4.8, Claude Opus 5, Claude Sonnet 5, Claude Fable 5, or Claude Mythos 5, where `type: "enabled"` returns a 400 error.
```

<details><summary>surrounding context</summary>

```
…m.claude.com/docs/en/build-with-claude/thinking-troubleshooting#error-thinking-type-adaptive). Keep `budget_tokens` until you move to a model that supports adaptive thinking, then apply the mapping that follows.

You need to migrate off `type: "enabled"` if:
  ⟦SPAN⟧
The mapping is small: remove `budget_tokens`, set `thinking: {type: "adaptive"}`, and control reasoning depth with `output_config: {effort: ...}` instead of a token budget.

```json
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 16000,
  "thinking": {…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**CLAIM_SCOPE — what was repaired.** The claim asserted more, or less, than the anchored evidence states; it was brought back to the source's own scope.

**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `budget_tokens`, `deprecated`, `Claude Opus 4.6`, `Claude Sonnet 4.6`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-10` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-11 · FIX_REQUIRED · risk LOW

`reasoning_type: lifecycle` · `evidence_shape: single_span` · `requires_all_evidence: False`

**Q.** What happens if manual extended thinking `thinking: {type: "enabled", budget_tokens: N}` is used on Claude Opus 4.7 or later models?

**A.** It is no longer supported and returns a 400 error.

**Claims**
  1. `thinking: {type: "enabled", budget_tokens: N}` is no longer supported on Claude Opus 4.7 or later models.
  2. Using it on those models returns a 400 error.

**Evidence span** — `ver_a7bda3595f2c124605c3228464d4ee52` 65023–65187 · Opus migration > Breaking changes

```
1. **Extended thinking removed:** `thinking: {type: "enabled", budget_tokens: N}` is no longer supported on Claude Opus 4.7 or later models and returns a 400 error.
```

<details><summary>surrounding context</summary>

```
…ttps://platform.claude.com/docs/en/api/service-tiers#supported-models) is not supported on Claude Opus 5.

#### Update your model name

```python
# Opus migration
model = "claude-opus-4-6"  # Before
model = "claude-opus-5"  # After
```

#### Breaking changes
  ⟦SPAN⟧
Switch to [adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) (`thinking: {type: "adaptive"}`) and use the [effort parameter](https://platform.claude.com/docs/en/build-with-claude/effort) to control thinking depth. On Claude Op…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**CLAIM_SCOPE — what was repaired.** The claim asserted more, or less, than the anchored evidence states; it was brought back to the source's own scope.

**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `Claude Opus 4.7 or later models`, `no longer supported`, `400 error`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-11` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-12 · FIX_REQUIRED · risk LOW

`reasoning_type: exact_lookup` · `evidence_shape: multi_span` · `requires_all_evidence: True`

**Q.** What do the `type` and `country` options specify in Localization?

**A.** The type of location (must be `approximate`). The two-letter [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country code. The API rejects unsupported country codes with a 400 error.

**Claims**
  1. `type`: The type of location (must be `approximate`).
  2. `country`: The two-letter [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country code. The API rejects unsupported country codes with a 400 error.

**Evidence span** — `ver_53da2f78e855c75ec755089c13d44c28` 16460–16514 · Tool definition > Localization

```
* `type`: The type of location (must be `approximate`)
```

<details><summary>surrounding context</summary>

```
…nd-tools/tool-use/server-tools#domain-filtering) in the Server tools guide.

### Localization

The `user_location` parameter allows you to localize search results based on a user's location. Provide at least one of `city`, `region`, `country`, or `timezone`.
  ⟦SPAN⟧
* `city`: The city name
* `region`: The region or state
* `country`: The two-letter [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country code. The API rejects unsupported country codes with a 400 error.
* `timezone`: The [IANA timezo…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**CATEGORY_MISCLASSIFICATION — what was repaired.** The recorded reasoning type was wrong. Two facts from two spans is a multi-span retrieval test, not multi-hop reasoning.

**Evidence span 2** — 16571–16743 (172 chars)

```
* `country`: The two-letter [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country code. The API rejects unsupported country codes with a 400 error.
```

*Both spans are required: a retriever earns credit only by finding all of them.*


**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `type`, `` The type of location (must be `approximate ``, `country`, `The two-letter [ISO 3166-1 alpha-2](https://en.wikipedia.org`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-12` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-13 · FIX_REQUIRED · risk LOW

`reasoning_type: configuration_interaction` · `evidence_shape: single_span` · `requires_all_evidence: False`

**Q.** If both a per-call `rejection_message` and the run-wide formatter are provided, which one takes precedence?

**A.** The per-call `rejection_message`.

**Claims**
  1. If both are provided, the per-call `rejection_message` takes precedence over the run-wide formatter.

**Evidence span** — `ver_ae3bfcc42c733c5051abda30f0f6db07` 6226–6326 · Human-in-the-loop > Custom rejection messages

```
If both are provided, the per-call `rejection_message` takes precedence over the run-wide formatter.
```

<details><summary>surrounding context</summary>

```
…ror_formatter] to control the default model-visible message for approval rejections across the whole run.
-   Per-call override: pass `rejection_message=...` to `state.reject(...)` when you want one specific rejected tool call to surface a different message.
  ⟦SPAN⟧
```python
from agents import RunConfig, ToolErrorFormatterArgs


def format_rejection(args: ToolErrorFormatterArgs[None]) -> str | None:
    if args.kind != "approval_rejected":
        return None
    return "Publish action was canceled because approval was…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**QUESTION_SCOPE — what was repaired.** The question was ambiguous or broader than the evidence supports; it was re-scoped to what the anchor states.

**CLAIM_SCOPE — what was repaired.** The claim asserted more, or less, than the anchored evidence states; it was brought back to the source's own scope.

**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `If both are provided`, `rejection_message`, `run-wide formatter`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-13` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-14 · FIX_REQUIRED · risk LOW

`reasoning_type: configuration_interaction` · `evidence_shape: single_span` · `requires_all_evidence: False`

**Q.** Without explicit authentication, what does `AWS_BEARER_TOKEN_BEDROCK` take precedence over?

**A.** The default AWS credential chain.

**Claims**
  1. Without explicit authentication, `AWS_BEARER_TOKEN_BEDROCK` takes precedence over the default AWS credential chain.

**Evidence span** — `ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` 34622–34765 · configured through AWS_REGION, AWS_DEFAULT_REGION, or your AWS profile.

```
Without explicit authentication, `AWS_BEARER_TOKEN_BEDROCK` takes precedence over the default AWS credential chain for backwards compatibility.
```

<details><summary>surrounding context</summary>

```
…(https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html), pass `api_key`, or provide a refresh callback:

```py
client = OpenAI(
    provider=bedrock(
        region="us-west-2",
        token_provider=lambda: refresh_bedrock_token(),
    )
)
```
  ⟦SPAN⟧
### Legacy `BedrockOpenAI` client

`BedrockOpenAI` and `AsyncBedrockOpenAI` remain available for existing applications and delegate to the same provider implementation. New applications should prefer `OpenAI(provider=bedrock(...))`.

```py
from openai import…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**QUESTION_SCOPE — what was repaired.** The question was ambiguous or broader than the evidence supports; it was re-scoped to what the anchor states.

**CLAIM_SCOPE — what was repaired.** The claim asserted more, or less, than the anchored evidence states; it was brought back to the source's own scope.

**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `Without explicit authentication`, `AWS_BEARER_TOKEN_BEDROCK`, `default AWS credential chain`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-14` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-15 · PASS · risk LOW

`reasoning_type: exact_lookup` · `evidence_shape: single_span` · `requires_all_evidence: False`

**Q.** What is the `ToolsToFinalOutputFunction` option?

**A.** A custom function that processes tool results and decides whether to end the run with a final output or continue processing with the LLM.

**Claims**
  1. `ToolsToFinalOutputFunction`: A custom function that processes tool results and decides whether to end the run with a final output or continue processing with the LLM.

**Evidence span** — `ver_35cac5e98c151a17f941a6142d74709f` 15672–15841 · Agents > Tool use behavior

```
- `ToolsToFinalOutputFunction`: A custom function that processes tool results and decides whether to end the run with a final output or continue processing with the LLM.
```

<details><summary>surrounding context</summary>

```
…nt:
    """Adds two numbers."""
    return a + b

agent = Agent(
    name="Stop At Stock Agent",
    instructions="Get weather or sum numbers.",
    tools=[get_weather, sum_numbers],
    tool_use_behavior=StopAtTools(stop_at_tool_names=["get_weather"])
)
```
  ⟦SPAN⟧
```python
from agents import Agent, FunctionToolResult, RunContextWrapper
from agents.agent import ToolsToFinalOutputResult
from agents.decorators import tool
from typing import List, Any

@tool
def get_weather(city: str) -> str:
    """Returns weather info…
```

</details>

**Why you are seeing this.** Both models passed this case. It is here because agreement between two models is correlated evidence, not independent confirmation, and this candidate was drawn as the deterministic QC sample.

**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `ToolsToFinalOutputFunction`, `A custom function that processes tool results and decides wh`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-15` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-16 · FIX_REQUIRED · risk LOW

`reasoning_type: exact_lookup` · `evidence_shape: single_span` · `requires_all_evidence: False`

**Q.** In a Chat Completions `ChunkEvent`, what does the `chunk` field contain?

**A.** The raw `ChatCompletionChunk` object received from the API.

**Claims**
  1. The `chunk` field of a Chat Completions `ChunkEvent` contains the raw `ChatCompletionChunk` object received from the API.

**Evidence span** — `ver_57e26a49b0a3714f3e90376d014d7f52` 5518–5672 · Streaming Helpers > Chat Completions API > Chat Completions Events > ChunkEvent

```
#### ChunkEvent

Emitted for every chunk received from the API.

- `type`: `"chunk"`
- `chunk`: The raw `ChatCompletionChunk` object received from the API
```

<details><summary>surrounding context</summary>

```
…ger.

### Chat Completions Events

These events allow you to track the progress of the chat completion generation, access partial results, and handle different aspects of the stream separately.

Below is a list of the different event types you may encounter:
  ⟦SPAN⟧
- `snapshot`: The current accumulated state of the chat completion

#### ContentDeltaEvent

Emitted for every chunk containing new content.

- `type`: `"content.delta"`
- `delta`: The new content string received in this chunk
- `snapshot`: The accumulated con…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**EVIDENCE_BOUNDARY — what was repaired.** The anchor did not carry the scope its claim depends on, and was extended or split into precise spans. Both old and new spans are retained.

**QUESTION_SCOPE — what was repaired.** The question was ambiguous or broader than the evidence supports; it was re-scoped to what the anchor states.

**Anchor changed** (EVENT_TYPE_SCOPE_COMPLETION) — 5603–5672 → 5518–5672

*Why:* Adds the event-type heading that scopes the field, 85 characters.

**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `ChunkEvent`, `chunk`, `ChatCompletionChunk`, `received from the API`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-16` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-17 · FIX_REQUIRED · risk LOW

`reasoning_type: exact_lookup` · `evidence_shape: single_span` · `requires_all_evidence: False`

**Q.** In a Chat Completions `ContentDeltaEvent`, what does the `parsed` field contain?

**A.** The partially parsed content, if applicable.

**Claims**
  1. In `ContentDeltaEvent`, the `parsed` field contains the partially parsed content, if applicable.

**Evidence span** — `ver_57e26a49b0a3714f3e90376d014d7f52` 5741–6000 · Streaming Helpers > Chat Completions API > Chat Completions Events > ContentDeltaEvent

```
#### ContentDeltaEvent

Emitted for every chunk containing new content.

- `type`: `"content.delta"`
- `delta`: The new content string received in this chunk
- `snapshot`: The accumulated content so far
- `parsed`: The partially parsed content (if applicable)
```

<details><summary>surrounding context</summary>

```
…rent event types you may encounter:

#### ChunkEvent

Emitted for every chunk received from the API.

- `type`: `"chunk"`
- `chunk`: The raw `ChatCompletionChunk` object received from the API
- `snapshot`: The current accumulated state of the chat completion
  ⟦SPAN⟧
#### ContentDoneEvent

Emitted when the content generation is complete. May be fired multiple times if there are multiple choices.

- `type`: `"content.done"`
- `content`: The full generated content
- `parsed`: The fully parsed content (if applicable)

####…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**EVIDENCE_BOUNDARY — what was repaired.** The anchor did not carry the scope its claim depends on, and was extended or split into precise spans. Both old and new spans are retained.

**QUESTION_SCOPE — what was repaired.** The question was ambiguous or broader than the evidence supports; it was re-scoped to what the anchor states.

**Anchor changed** (EVENT_TYPE_SCOPE_COMPLETION) — 5944–6000 → 5741–6000

*Why:* Adds the event-type heading and the sibling fields, 259 characters. `parsed` appears on several event types with different meanings, so the event type is the claim.

**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `ContentDeltaEvent`, `parsed`, `The partially parsed content (if applicable)`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-17` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-18 · FIX_REQUIRED · risk LOW

`reasoning_type: exact_lookup` · `evidence_shape: multi_span` · `requires_all_evidence: True`

**Q.** What do the `tool_name_override` and `tool_description_override` options specify in Customizing handoffs via the `handoff()` function?

**A.** By default, the `Handoff.default_tool_name()` function is used, which resolves to `transfer_to_<agent_name>`. You can override this. Override the default tool description from `Handoff.default_tool_description()`.

**Claims**
  1. `tool_name_override`: By default, the `Handoff.default_tool_name()` function is used, which resolves to `transfer_to_<agent_name>`. You can override this.
  2. `tool_description_override`: Override the default tool description from `Handoff.default_tool_description()`.

**Evidence span** — `ver_1c77f33b04ffffa285ea7e61c2a89653` 1723–1881 · (1)! > Customizing handoffs via the `handoff()` function

```
-   `tool_name_override`: By default, the `Handoff.default_tool_name()` function is used, which resolves to `transfer_to_<agent_name>`. You can override this.
```

<details><summary>surrounding context</summary>

```
…illing_agent`), or you can use the `handoff()` function.

### Customizing handoffs via the `handoff()` function

The [`handoff()`][agents.handoffs.handoff] function lets you customize things.

-   `agent`: This is the agent to which things will be handed off.
  ⟦SPAN⟧
-   `tool_description_override`: Override the default tool description from `Handoff.default_tool_description()`
-   `on_handoff`: A callback function executed when the handoff is invoked. This is useful for things like kicking off some data fetching as soon…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**CATEGORY_MISCLASSIFICATION — what was repaired.** The recorded reasoning type was wrong. Two facts from two spans is a multi-span retrieval test, not multi-hop reasoning.

*Note:* the question mentions `handoff()` as framing only; no claim depends on it.

**Evidence span 2** — 1882–1994 (112 chars)

```
-   `tool_description_override`: Override the default tool description from `Handoff.default_tool_description()`
```

*Both spans are required: a retriever earns credit only by finding all of them.*


**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `tool_name_override`, `` By default, the `Handoff.default_tool_name()` function is us ``, `tool_description_override`, `` Override the default tool description from `Handoff.default ``

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-18` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-19 · FIX_REQUIRED · risk LOW

`reasoning_type: exact_lookup` · `evidence_shape: multi_span` · `requires_all_evidence: True`

**Q.** What do the `kind` and `tool_type` options specify in `tool_error_formatter`?

**A.** The error category, such as `"approval_rejected"` or `"tool_not_found"`. The tool runtime (`"function"`, `"computer"`, `"shell"`, `"apply_patch"`, or `"custom"`).

**Claims**
  1. `kind`: The error category, such as `"approval_rejected"` or `"tool_not_found"`.
  2. `tool_type`: The tool runtime (`"function"`, `"computer"`, `"shell"`, `"apply_patch"`, or `"custom"`).

**Evidence span** — `ver_2c60e99cfd929a738910b893fd6f1a40` 15267–15450 · Running agents > Runner lifecycle and configuration > Run config > Run config details > `tool_error_formatter`

```
The formatter receives [`ToolErrorFormatterArgs`][agents.run_config.ToolErrorFormatterArgs] with:

-   `kind`: The error category, such as `"approval_rejected"` or `"tool_not_found"`.
```

<details><summary>surrounding context</summary>

```
…l-name lookup. Other invalid tool payloads continue to use their existing error behavior.

##### `tool_error_formatter`

Use `tool_error_formatter` to customize the message that is returned to the model when the SDK creates a model-visible tool error output.
  ⟦SPAN⟧
-   `tool_name`: The tool name.
-   `call_id`: The tool call ID.
-   `default_message`: The SDK's default model-visible message.
-   `run_context`: The active run context wrapper.

Return a string to replace the message, or `None` to use the SDK default.

```…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**EVIDENCE_BOUNDARY — what was repaired.** The anchor did not carry the scope its claim depends on, and was extended or split into precise spans. Both old and new spans are retained.

**CATEGORY_MISCLASSIFICATION — what was repaired.** The recorded reasoning type was wrong. Two facts from two spans is a multi-span retrieval test, not multi-hop reasoning.

*Note:* the question mentions `tool_error_formatter` as framing only; no claim depends on it.

**Anchor changed** (OWNER_TYPE_SCOPE_COMPLETION) — 15366–15450, 15451–15557 → 15267–15450, 15451–15557

*Why:* The first span grows 99 characters upward to the line naming `ToolErrorFormatterArgs`, so the fields have an owner inside the evidence. The second field span is unchanged.

**Evidence span 2** — 15451–15557 (106 chars)

```
-   `tool_type`: The tool runtime (`"function"`, `"computer"`, `"shell"`, `"apply_patch"`, or `"custom"`).
```

*Both spans are required: a retriever earns credit only by finding all of them.*


**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `kind`, `` The error category, such as `"approval_rejected"` or `"tool ``, `tool_type`, `` The tool runtime (`"function"`, `"computer"`, `"shell"`, `"a ``

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-19` in `human_decisions_batch_003.json`.

---

#### GOLD-B003-20 · FIX_REQUIRED · risk LOW

`reasoning_type: exact_lookup` · `evidence_shape: multi_span` · `requires_all_evidence: True`

**Q.** What do the `workflow_name` and `trace_id` options specify in Traces and spans?

**A.** This is the name of the logical workflow or app. For example "Code generation" or "Customer service". A unique ID for the trace. Automatically generated if you don't pass one. Must have the format `trace_<32_alphanumeric>`.

**Claims**
  1. `workflow_name`: This is the name of the logical workflow or app. For example "Code generation" or "Customer service".
  2. `trace_id`: A unique ID for the trace. Automatically generated if you don't pass one. Must have the format `trace_<32_alphanumeric>`.

**Evidence span** — `ver_6b90217721b841b1329f51ec1caab139` 1043–1169 · Tracing > Traces and spans

```
    -   `workflow_name`: This is the name of the logical workflow or app. For example "Code generation" or "Customer service".
```

<details><summary>surrounding context</summary>

```
…is unavailable for organizations that use OpenAI's APIs under a Zero Data Retention (ZDR) policy.***

## Traces and spans

-   **Traces** represent a single end-to-end operation of a "workflow". They're composed of Spans. Traces have the following properties:
  ⟦SPAN⟧
-   `trace_id`: A unique ID for the trace. Automatically generated if you don't pass one. Must have the format `trace_<32_alphanumeric>`.
    -   `group_id`: Optional group ID, to link multiple traces from the same conversation. For example, you might use…
```

</details>

**Why you are seeing this.** The reviewer rewrote the question and claims. Every term they assert is present in the anchored span, but a model authored the wording and a model verified it, so the case is not gold until you agree.

**CATEGORY_MISCLASSIFICATION — what was repaired.** The recorded reasoning type was wrong. Two facts from two spans is a multi-span retrieval test, not multi-hop reasoning.

**Evidence span 2** — 1170–1311 (141 chars)

```
    -   `trace_id`: A unique ID for the trace. Automatically generated if you don't pass one. Must have the format `trace_<32_alphanumeric>`.
```

*Both spans are required: a retriever earns credit only by finding all of them.*


**Precheck holdout-ready.** Structurally capable of becoming eligible; not an approval.

*Critical claim strings, each verified inside the span above:* `workflow_name`, `This is the name of the logical workflow or app. For example`, `trace_id`, `A unique ID for the trace. Automatically generated if you do`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-20` in `human_decisions_batch_003.json`.

---

---

## B. Check the anchor before approving

Each of these asserts something the anchored span does not contain. This is the OA-002 defect class, and it is the reason the whole batch exists — do not skim these.

#### GOLD-B003-04 · FIX_REQUIRED · risk HIGH

`reasoning_type: error_behavior` · `evidence_shape: multi_span` · `requires_all_evidence: True`

**Q.** What happens when the executor and advisor models requested for the advisor tool do not form a valid pair?

**A.** The API returns a `400 invalid_request_error` naming the unsupported combination.

**Claims**
  1. The executor model and the advisor model must form a valid pair.
  2. Requesting an invalid pair returns a `400 invalid_request_error` naming the unsupported combination.

**Evidence span** — `ver_b8b18cda9b875d51a2ce979a1bf4e909` 88971–89112 · Model compatibility

```
The executor model (the top-level `model` field) and the advisor model (the `model` field inside the tool definition) must form a valid pair.
```

<details><summary>surrounding context</summary>

```
…(see the note in [Multi-turn conversations](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool#multi-turn-conversations)).
* Enable `caching` only for conversations where you expect three or more advisor calls.

## Model compatibility
  ⟦SPAN⟧
### Platform availability

The advisor tool is available in beta on the Claude API and on [Claude Platform on AWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws). It is not currently available on Amazon Bedrock, Google Cloud, o…
```

</details>

**Why you are seeing this.** The deterministic precheck blocks this case: unresolved anaphora: refers to 'the tool' with no antecedent in the span. It cannot become holdout-eligible until that is resolved, so it needs a decision on the evidence rather than a quick approval.

**EVIDENCE_BOUNDARY — what was repaired.** The anchor did not carry the scope its claim depends on, and was extended or split into precise spans. Both old and new spans are retained.

**QUESTION_SCOPE — what was repaired.** The question was ambiguous or broader than the evidence supports; it was re-scoped to what the anchor states.

**Anchor changed** (ANAPHORIC_SCOPE_COMPLETION) — 92785–92898 → 88971–89112, 92785–92898

*Why:* "pair" is defined 3,838 characters earlier, with a model-compatibility table in between, so a contiguous extension would pull in the whole table. Two precise spans are the sanctioned alternative to one giant one: the definition of a valid pair, and the failure behaviour.

**Evidence span 2** — 92785–92898 (113 chars)

```
If you request an invalid pair, the API returns a `400 invalid_request_error` naming the unsupported combination.
```

*Both spans are required: a retriever earns credit only by finding all of them.*


**Precheck blocked** — unresolved anaphora: refers to 'the tool' with no antecedent in the span

*Critical claim strings, each verified inside the span above:* `executor model`, `advisor model`, `must form a valid pair`, `400 invalid_request_error`, `naming the unsupported combination`

**Decision:** `APPROVE` · `REJECT` · `NEEDS_EDIT` → record for `GOLD-B003-04` in `human_decisions_batch_003.json`.

---

## Audit

The full history — the generator's original proposal, the reviewer's verdict and boolean checks, every numbered revision, and the anchor as first mined — is retained per candidate in `gold_batch_001_qc.json` under `audit`. Nothing was overwritten, and no anchor was changed (0 disputes recorded).

OA-002 is a defect in the original development set and is deliberately not part of this batch. Its `development/v2` correction remains proposed and unapplied.
