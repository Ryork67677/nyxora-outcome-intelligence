# GOLD-001 — batch 001 review summary

17 decisions are waiting. This is the one-page version; the packet itself is
`evals/review/gold_batch_001_qc.md`.

| candidate | group | risk | verdict | defects | term asserted but absent from the span |
| --- | --- | --- | --- | --- | --- |
| `GOLD-B001-02` | fast track | LOW | PASS | — | — |
| `GOLD-B001-05` | fast track | LOW | FIX_REQUIRED | — | — |
| `GOLD-B001-06` | fast track | LOW | FIX_REQUIRED | — | — |
| `GOLD-B001-07` | fast track | LOW | FIX_REQUIRED | — | — |
| `GOLD-B001-08` | fast track | LOW | FIX_REQUIRED | D2 | — |
| `GOLD-B001-09` | fast track | LOW | FIX_REQUIRED | D2 | — |
| `GOLD-B001-10` | fast track | LOW | FIX_REQUIRED | — | — |
| `GOLD-B001-11` | fast track | LOW | FIX_REQUIRED | — | — |
| `GOLD-B001-12` | fast track | LOW | FIX_REQUIRED | D2 | — |
| `GOLD-B001-18` | fast track | LOW | FIX_REQUIRED | — | — |
| `GOLD-B001-03` | check anchor | MEDIUM | FIX_REQUIRED | D1 | `Claude Fable 5` (section path), `Claude Mythos 5` (section path) |
| `GOLD-B001-04` | check anchor | HIGH | FIX_REQUIRED | D1 | `tripwire_triggered` |
| `GOLD-B001-13` | check anchor | HIGH | FIX_REQUIRED | — | `Google Cloud Agent Platform` |
| `GOLD-B001-14` | check anchor | HIGH | FIX_REQUIRED | D1 | `Claude 4.6`, `Claude Mythos Preview` |
| `GOLD-B001-16` | check anchor | HIGH | FIX_REQUIRED | D3 | `embd_normalize` |
| `GOLD-B001-17` | check anchor | MEDIUM | FIX_REQUIRED | D2 | `Files API` (section path) |
| `GOLD-B001-15` | recommended reject | HIGH | FAIL | D3 | `tool_choice.type` |

## How to read it

**Group A (10) — fast track.** Every code identifier and product name the case asserts
appears inside the anchored span. Read the question, glance at the span, decide.

**Group B (6) — check the anchor.** Each asserts something the span does not contain.
Four are genuine gaps; two (`03`, `13`) are supplied by the section path instead, which
is weaker evidence rather than none. These are the OA-002 defect class and are the whole
reason this batch exists.

**Group C (1) — recommended reject.** `GOLD-B001-15`, the only FAIL. The span is a JSON
request body, so any question over it tests a sample configuration rather than a
documented rule. It was not repaired a second time to preserve it.

## The thing worth knowing before you start

The verdict importer forbids a reviewer from moving a source anchor, so **every repair in
this batch is a repair to the wording, not to the span**. Where ChatGPT addressed a
boundary defect by rewriting the question to name the missing scope, the anchor is still
the same anchor and still does not contain that scope. Group B is exactly the set where
that matters. Approving one of those accepts a claim its anchor cannot support alone;
`NEEDS_EDIT` is the honest choice if you want the span extended instead.

The group assignment is computed, not asserted: identifiers and product names in the
answer and claims are matched against the span text, then against the document title and
section path. It is a mechanical check for one specific defect, not a judgement about
whether the case is any good.

## What produces gold

Only `APPROVE` recorded in `evals/review/human_decisions_batch_001.json` and imported by
`scripts/import_human_decisions.py`. A ChatGPT PASS is `dual_llm_pass` and stops there.
`NEEDS_EDIT` and an undecided candidate both stay out of gold. The importer refuses a
decisions file that names a model as its reviewer.

## Not done, deliberately

Batch 002 is not generated. The preregistered miner changes — drop or extend anaphoric
spans, stop exporting relation labels, reject normative claims drawn from example code,
raise the structural share — are unchanged and stay unchanged until decisions are in.
OA-002 remains separate: `development/v1` is untouched and the `development/v2`
correction is still a proposal.
