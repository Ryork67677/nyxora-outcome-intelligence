# GOLD-001 — batch 001 evidence-boundary repair review

3 candidates were sent back with `NEEDS_EDIT`. Their anchors have been extended so that each exact span now contains everything its claims depend on. Nothing here is approved.

Every one of these remains `needs_human_review` until you approve the repaired version. This script cannot produce `human_verified`, and did not.

**The original anchors were not overwritten.** Each repair is a numbered `anchor_revisions` entry carrying the old offsets, text and hash beside the new ones. The new span is a strict superset of the old in all three cases — the script refuses anything else, because a span that moves elsewhere is a re-anchoring, not a boundary completion.

Validator: **PASS** (3 cases checked, 0 failures).

---

## GOLD-B001-03

**Q.** For `claude-fable-5` and `claude-mythos-5`, is a `thinking` configuration required?

**A.** No. Adaptive thinking is always on for those models, so no `thinking` configuration is required.

**Atomic claims**
  1. `claude-fable-5` and `claude-mythos-5` share a baseline setting of adaptive thinking, which is always on.
  2. No `thinking` configuration is required for `claude-fable-5` and `claude-mythos-5`.

**Repaired exact evidence** — `ver_a7bda3595f2c124605c3228464d4ee52` 2223–2519 (296 chars) · `54f4b6a0802f04ab…`

```
The baseline settings shared by `claude-fable-5` and `claude-mythos-5`:

* **Thinking:** [Adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) is always on. The model determines when and how much to think on each request, and no `thinking` configuration is required.
```

**Old evidence** — 2410–2519 (109 chars) · `85dd3cb0dd55e21a…`

```
The model determines when and how much to think on each request, and no `thinking` configuration is required.
```

**What changed.** Extended backwards by 187 characters to the sentence that names which models the baseline settings belong to. (187 characters added before the old span, 0 after.) The old span is contained in the new one verbatim.

**Why the new anchor is complete.** The model scope, the adaptive-thinking setting and the no-configuration-required statement are now all inside one contiguous span. The question is worded with the model identifiers the span actually contains rather than the display names, which appear only in the section heading.

**Validator result.** PASS — all checks

**Decision needed:** `APPROVE` or `REJECT` the repaired version.

---

## GOLD-B001-04

**Q.** What happens when an input guardrail's `.tripwire_triggered` value is true?

**A.** An `InputGuardrailTripwireTriggered` exception is raised.

**Atomic claims**
  1. If an input guardrail's `.tripwire_triggered` value is true, an `InputGuardrailTripwireTriggered` exception is raised.

**Repaired exact evidence** — `ver_f22fbd5c504fa28a4e70440337e4a495` 1496–2119 (623 chars) · `f544439786324009…`

```
Input guardrails run in 3 steps:

1. First, the guardrail receives the same input passed to the agent.
2. Next, the guardrail function runs to produce a [`GuardrailFunctionOutput`][agents.guardrail.GuardrailFunctionOutput], which is then wrapped in an [`InputGuardrailResult`][agents.guardrail.InputGuardrailResult]
3. Finally, we check if [`.tripwire_triggered`][agents.guardrail.GuardrailFunctionOutput.tripwire_triggered] is true. If true, an [`InputGuardrailTripwireTriggered`][agents.exceptions.InputGuardrailTripwireTriggered] exception is raised, so you can appropriately respond to the user or handle the exception.
```

**Old evidence** — 1930–2119 (189 chars) · `c700d2b8e7c2cc4e…`

```
If true, an [`InputGuardrailTripwireTriggered`][agents.exceptions.InputGuardrailTripwireTriggered] exception is raised, so you can appropriately respond to the user or handle the exception.
```

**What changed.** Extended backwards by 434 characters to the start of the numbered procedure, so the anchor carries both the subject (input guardrails) and the condition (`.tripwire_triggered` is true). (434 characters added before the old span, 0 after.) The old span is contained in the new one verbatim.

**Why the new anchor is complete.** The original span opened on the bare pronoun `If true`. The repaired span states what is checked, what makes it true, and what is raised, without any reference outside itself.

**Validator result.** PASS — all checks

**Decision needed:** `APPROVE` or `REJECT` the repaired version.

---

## GOLD-B001-14

**Q.** What happens if a request sends a prefilled last assistant message to Claude 4.6 and later models or Claude Mythos Preview?

**A.** The request returns a 400 `invalid_request_error`.

**Atomic claims**
  1. Claude 4.6 and later models and Claude Mythos Preview do not support prefilling assistant messages.
  2. Sending a request with a prefilled last assistant message to those models returns a 400 `invalid_request_error`.

**Repaired exact evidence** — `ver_0774ca0093ff4a846753577c9a4a39d5` 19054–19308 (254 chars) · `9e8be2c9734a4b12…`

```
Claude 4.6 and later models and [Claude Mythos Preview](https://anthropic.com/glasswing) do not support prefilling assistant messages. Sending a request with a prefilled last assistant message to any of these models returns a 400 `invalid_request_error`:
```

**Old evidence** — 19189–19308 (119 chars) · `96a1b300f6116275…`

```
Sending a request with a prefilled last assistant message to any of these models returns a 400 `invalid_request_error`:
```

**What changed.** Extended backwards by 135 characters to the sentence that defines `these models`. (135 characters added before the old span, 0 after.) The old span is contained in the new one verbatim.

**Why the new anchor is complete.** The model scope is now stated inside the anchor instead of being carried by the phrase `any of these models`. The claim asserts exactly the range the frozen source names and no more.

**Validator result.** PASS — all checks

**Decision needed:** `APPROVE` or `REJECT` the repaired version.

---

## What happens next

Record a decision for these three in a decisions file and import it with `scripts/import_human_decisions.py`. Until then batch 001 stands at 12 `human_verified`, 2 `human_rejected`, 3 `needs_human_review`, and is not closed.

`GOLD-B001-01` is not in this packet and never reached a human: it was the second agreed pass, and the deterministic QC sample drew `02`. It remains `dual_llm_pass`, which is not gold.
