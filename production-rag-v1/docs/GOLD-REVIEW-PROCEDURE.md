# Gold review procedure (GOLD-001)

How a candidate becomes a trusted evaluation case. The short version: **the machine
finds evidence, people and an independent model decide what it means.**

## Why the workflow looks like this

EXP-014R tried to have the generator write questions *and* answers. It produced
confident wrong gold — `tool_choice → True`, one parameter given two contradictory
defaults, numbers bound to whichever identifier sat nearest — and only 12 of a
target 100 survived, several still wrong.

Span *discovery* was reliable. Claim *synthesis* was not. So the generator now
discovers and packages evidence, and never declares gold.

An evaluation set is the one artifact you cannot check by running it: a wrong answer
key produces a confident number with nothing behind it. Every gate below exists for
that reason.

## The pipeline

```
frozen corpus
  → candidate evidence discovery      scripts/export_review_batch.py
  → review packet (JSON + Markdown)   evals/review/gold_review_batch_NNN.*
  → independent ChatGPT verification  (you, outside this repo)
  → import verdicts                   scripts/import_verification.py
  → human QC queue                    scripts/select_human_qc.py
  → human approval                    (you)
  → validator                         scripts/validate_golden.py
  → frozen holdout                    → only then, replication
```

Retrieval is **never** run on candidates. Nothing about SYSTEM-A or SYSTEM-B results
may influence question authoring — that is what keeps the holdout meaningful.

## 1. Generate a batch

```bash
python scripts/export_review_batch.py --batch 1 --size 18
```

Writes `gold_review_batch_001.json` and `.md`. Every candidate carries the evidence
verbatim plus ~900 characters of context each side, because a sentence often cannot
be judged alone.

Candidates come in two kinds:

| kind | confidence | what the reviewer does |
|---|---|---|
| `parameter_table_row` | high | Check the row really is a parameter table. The parameter/value binding is **structural** — first cell of the row — not a proximity guess. |
| `explicit_*` prose | medium/low | **Write the question and the atomic claims.** These ship with empty claims and a placeholder prompt on purpose. |

Anything with more than one possible subject is flagged
`needs_human_interpretation` rather than resolved automatically.

## 2. Send the batch for independent verification

Upload the `.md` (or `.json`) to ChatGPT with this instruction:

> The evidence quoted in this file is authoritative. **Do not consult live
> documentation** — the corpus is a frozen snapshot and the live docs may have
> changed. For each candidate, judge the proposed question, answer and claims
> against the evidence and its surrounding context only.

Ask for one record per candidate:

```json
{
  "candidate_id": "GOLD-B001-01",
  "verdict": "PASS | FAIL | FIX_REQUIRED | UNCERTAIN",
  "question_supported": true,
  "answer_supported": true,
  "all_critical_claims_supported": true,
  "evidence_boundary_complete": true,
  "identifier_value_binding_correct": true,
  "natural_question": true,
  "suggested_question": "optional rewrite",
  "suggested_answer": "optional",
  "suggested_claims": ["optional"],
  "suggested_fix": "optional",
  "verification_notes": "brief, grounded in the evidence"
}
```

`evidence_boundary_complete` is the one that catches the OA-002 class of defect: a
span that describes a thing without naming it.

## 3. Import the verdicts

```bash
python scripts/import_verification.py \
  evals/review/gold_review_batch_001.json reviews_001.json
```

The importer refuses the whole file if any candidate id or verdict is invalid —
partial imports would leave the batch in a state nobody could reason about. Every
edit is appended as a numbered revision with author, timestamp and reason; the
original proposal is never destroyed. A reviewer cannot silently move a source
anchor: disagreements are recorded as `anchor_disputes` and the anchor stands.

**A ChatGPT PASS yields `dual_llm_pass`, never `human_verified`.**

## 4. Build the human queue

```bash
python scripts/select_human_qc.py evals/review/gold_review_batch_001.json
```

You see every disagreement, uncertainty and failure, plus a seeded random 15% of the
agreed passes — two models agreeing is correlated evidence, not independent
confirmation, and a shared blind spot would otherwise never surface.

## 5. Approve

Set `verification: "human_approved"` and `human_verified: true` only for cases you
have actually looked at. The validator blocks any holdout case that lacks it.

## 6. Validate, then freeze

```bash
python scripts/validate_golden.py evals/holdout/v1.jsonl --require-human holdout
```

Blocks on: invalid or drifting source spans · hash mismatch · a critical claim absent
from its own evidence · duplicate questions or evidence · missing evidence or claims ·
invalid split, category or provider · missing provenance · missing verification
status · unapproved holdout cases · chunk-id-only ground truth · malformed multi-hop
structure.

Only after the holdout is validated, approved, hashed and frozen may SYSTEM-A and
SYSTEM-B be run against it — **once**.

## Status vocabulary

| status | meaning |
|---|---|
| `candidate_unverified` | freshly mined; not evidence of anything |
| `dual_llm_pass` / `dual_llm_fail` | Claude proposed, ChatGPT reviewed |
| `needs_human_review` | disagreement, uncertainty, or a repair to check |
| `human_approved` / `human_rejected` | a person decided |
| `human_verified` | reserved for the original development set |

Only `human_approved` and `human_verified` may enter a holdout.

## What is deliberately not automated

Nothing here raises a case's status on its own. The models can narrow the queue; they
cannot close it. That safeguard already prevented one real mistake — running a
replication against bad ground truth — and weakening it would cost more than the
time it saves.
