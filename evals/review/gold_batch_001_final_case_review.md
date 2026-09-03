# GOLD-001 — batch 001 final case: GOLD-B001-01

One decision closes batch 001. This candidate passed independent verification without a single rewrite, but the deterministic QC sample drew its sibling `GOLD-B001-02` instead, so no person has ever looked at it. It is `dual_llm_pass` — two models agreeing, which is not gold.

Everything needed to decide is below. Nothing to look up.

---

## The case

**Q.** What is the default value of enable_zoom?

**A.** false

**Atomic claim**
  1. enable_zoom defaults to false

## Exact evidence

`ver_d9ba3ab0d872dd86047c7ed6dc783235` chars 33781–33949 (168 chars) · `cbc58014a9073624…`

```
| `enable_zoom`       | No       | Enable zoom action (`computer_20251124` only). Set to `true` to allow Claude to zoom into specific screen regions. Default: `false` |
```

The row binds structurally, not by proximity: the parameter is the row's first cell and the default is stated in that same row. That is the mechanism the table miner was built on, and it is the one mechanism in batch 001 that produced candidates needing no re-authoring.

<details><summary>the table this row sits in</summary>

```
…|
| `name`              | Yes      | Must be "computer"                                                                                                                  |
| `display_width_px`  | Yes      | Display width in pixels                                                                                                             |
| `display_height_px` | Yes      | Display height in pixels                                                                                                            |
| `display_number`    | No       | Display number for X11 environments                                                                                                 |
  ⟦THE ANCHORED ROW⟧
<Note>
  **Important:** Your application must explicitly run the computer use tool; Claude cannot run it directly. You are responsible for implementing the screenshot capture, mouse movements, keyboard inputs, and other actions based on Claude's requests.
</Note>

### Combining with thinking

For combining computer use with thinking, see [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking).

<Tip>
  For computer use specifically, internal benchmarking suggests these `effort` settings:

  * **Claude Opus 4.7:** use `high` as the default; use `low` for high-throughput or cost-sensitive workloads.
  * **Claude Sonnet 4.6 and Claude Opus 4.6:** use `medium` as the default…
```

</details>

## Source

| field | value |
| --- | --- |
| document | Computer use tool |
| section | How to implement computer use > Tool parameters |
| provider | anthropic |
| url | https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool |
| captured | 2026-08-17 04:46:19+00:00 |
| version | `ver_d9ba3ab0d872dd86047c7ed6dc783235` |
| evidence kind | `parameter_table_row` |
| generator confidence | `high` |

## Independent review

**Verdict: PASS** (reviewer `chatgpt`, 2026-08-19T05:41:57Z)

| check | passed |
| --- | --- |
| `question_supported` | yes |
| `answer_supported` | yes |
| `all_critical_claims_supported` | yes |
| `evidence_boundary_complete` | yes |
| `identifier_value_binding_correct` | yes |
| `natural_question` | yes |

> The row is clearly part of the computer-use tool parameter table. The same row names `enable_zoom` and explicitly states `Default: false`, so the proposed question, answer, and claim are directly supported.

The generator proposed this question and answer directly — there are 0 revisions on this candidate, because the reviewer changed nothing.

## Validator

**PASS — all blocking checks**

Run through the same `validate_golden.py` the golden sets use, on this case projected into the golden-case schema, alongside the 15 already-approved cases so duplicate question and duplicate evidence are checked against them.

Critical claim strings proposed for this case: `enable_zoom`, `` Default: `false` ``. These are the literal strings the validator requires to appear inside the span; they are proposed, not stored, and become real only on approval.

## Decision

`APPROVE` or `REJECT`. Approving closes batch 001 at **16 human_verified, 2 human_rejected**; rejecting closes it at **15 and 3**. Either way it closes.

Record it in a decisions file and import with `scripts/import_human_decisions.py`. Nothing else in batch 001 is outstanding.
