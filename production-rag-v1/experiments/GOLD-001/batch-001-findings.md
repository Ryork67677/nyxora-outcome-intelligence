# GOLD-001 — batch 001 verification findings

**Status: no case in batch 001 is gold.** Independent verification is finished; human
review is not. 17 of 18 candidates are queued for a person, and nothing becomes
`human_verified` until the owner records an `APPROVE` decision.

## What was run

| Step | Artifact |
| --- | --- |
| Batch shipped | `evals/review/gold_review_batch_001.json` — `batch_sha256 a3fe9242e33fb2df…` |
| Independent review | `evals/review/reviews_001.json` — reviewer `chatgpt`, `source_batch_sha256` matched exactly, all 18 ids aligned |
| Import | `scripts/import_verification.py` — 18 verdicts, 16 versioned revisions, 0 anchor disputes |
| Human queue | `scripts/select_human_qc.py` — 16 mandatory + 1 QC sample of the 2 agreed passes (seed 20250819) |
| Review packet | `scripts/export_human_qc_packet.py` — 17 candidates with evidence, context and both proposals |

Verdicts: **PASS 2, FIX_REQUIRED 15, FAIL 1, UNCERTAIN 0.**
Statuses after import: `dual_llm_pass` 2, `needs_human_review` 15, `dual_llm_fail` 1.

A PASS produced `dual_llm_pass`, never `human_verified`. That distinction is enforced
in `STATUS_FROM_VERDICT`, not left to discipline, and there is a test for it.

## What the verdict counts do and do not mean

The raw counts overstate the miner's error rate, and saying so is not a defence of the
miner — it is a statement about how the batch was constructed.

All 16 prose candidates shipped with `[REVIEWER TO WRITE]` as their question and an
empty claim list, because GOLD-001 deliberately changed the generator from a
question-answer producer into an evidence-candidate producer. `question_supported`,
`answer_supported`, `all_critical_claims_supported` and `natural_question` were
therefore **false by construction** on every prose candidate. Those four flags carry no
information about the miner. FIX_REQUIRED on a prose candidate means "the reviewer
wrote the question", which is the design, not a defect.

The two checks that do test the miner's own output are `evidence_boundary_complete`
(is the anchored span self-contained?) and `identifier_value_binding_correct` (did the
miner bind the right identifier to the right relation?).

| Signal | Prose candidates (n=16) |
| --- | --- |
| Boundary incomplete | 3 — 03, 04, 14 |
| Identifier/relation binding wrong | 6 — 08, 09, 12, 15, 16, 17 |
| Either defect | 9 |
| No named miner defect (only needed a question written) | 7 — 05, 06, 07, 10, 11, 13, 18 |

Structural candidates: **2 of 2 passed every check with nothing rewritten** (01, 02).
Two observations is not a precision estimate — it is two observations — but they are
the only two candidates in the batch that needed no re-authoring at all.

With n=18, one candidate is 5.6 percentage points. Nothing here supports a significance
claim, and none is made.

## Defect taxonomy

### D1 — anaphoric anchor (3 cases: 03, 04, 14)

The span opens with, or silently depends on, a referent that lives outside it.

- **04**: `"If true, an [InputGuardrailTripwireTriggered] exception is raised…"` — what
  is true is named only in the preceding sentence.
- **14**: `"Sending a request with a prefilled last assistant message to any of these
  models returns a 400 invalid_request_error:"` — "these models" is the whole point of
  the question and is not in the span.
- **03**: `"The model determines when and how much to think… no thinking configuration
  is required."` — which models is outside the anchor.

This is the same failure shape as the OA-002 defect already recorded in
`experiments/EXP-014R/known-data-defects.md`. Finding it three times in sixteen
candidates says the miner reproduces it systematically rather than by accident.

### D2 — wrong relation label (5 cases: 08, 09, 12, 16, 17)

The miner matched a trigger word and labelled the candidate with a relation the
sentence does not express. The evidence is usually fine; the *label* points the
reviewer at the wrong question.

- **17**: `file_id` was linked to wording from a different bullet in the same error list.
- **12**: the span picked up an unrelated anaphoric sentence before the relevant bullet.
- **09**: a two-part stopping condition labelled as a single response relation.

Because the label rode along in the exported candidate, it actively steered the
reviewer's first reading. On the evidence of this batch the label is worse than no
label.

### D3 — identifier matched inside example code (2 cases: 15, 16)

- **15 (the only FAIL)**: the miner matched `"required": ["location"]` inside a JSON
  request body and framed it as a requirement on `tool_choice`. This is exactly the
  false token-to-identifier association that killed the EXP-014R generator and that
  GOLD-001 exists to prevent. It survived into a shipped batch.
- **16**: a `ValueError` raised by an example helper function, framed as embeddings API
  behaviour.

A sample configuration is not a documented rule. The miner currently cannot tell them
apart.

## Changes for batch 002

Preregistered here, before batch 002 is generated, so they cannot be tuned to its
outcome.

1. **Reject or extend anaphoric spans.** A candidate whose span opens with an
   anaphoric construction (`If true`, `these`, `any of these`, `it`, `this`) or whose
   subject is a bare pronoun is either extended to include the antecedent or dropped.
   Targets D1.
2. **Stop exporting the proposed relation label.** Keep it internally for selection;
   remove it from the candidate the reviewer sees. Wrong on 5 of 16 and, per the
   reviewer's own notes, misleading when wrong. Targets D2.
3. **Refuse identifier matches inside fenced code blocks and JSON literals** when the
   candidate would be framed as a documented rule. Targets D3.
4. **Raise the share of structural candidates.** Table-row mining was the only
   mechanism that produced candidates needing no re-authoring. This is a change of mix,
   not evidence that table rows have high precision in general.

None of these changes touch batch 001. Its records stay exactly as verified.

## What is still true and unchanged

- Retrieval was never run over these candidates. `retrieval_was_not_run: true`.
- SYSTEM-A and SYSTEM-B remain frozen at
  `9afcb5b7c58ebacf…` and `304c350940b83733…` and have not been run against any
  candidate in this batch.
- The holdout is not frozen and no A-vs-B replication has been attempted.
- OA-002 remains a recorded defect with a proposed, unapplied correction awaiting the
  owner's decision.

## Next step, and who owns it

The next step is **not** batch 002. It is the human review of the 17 queued candidates,
because that is the only step that can produce a `human_verified` case, and the target
of 30–40 validation plus 70–100 holdout cases is gated entirely on it.

Run `scripts/export_human_qc_packet.py` to regenerate the packet locally, then record
`APPROVE` or `REJECT` per candidate in
`evals/review/human_decisions_batch_001.json`.
