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
  → human QC packet                   scripts/export_human_qc_packet.py
  → human decisions                   (you) -> human_decisions_batch_NNN.json
  → import decisions                  scripts/import_human_decisions.py
  → boundary repair (NEEDS_EDIT only) scripts/repair_evidence_boundary.py
  → re-decide the repaired cases      (you)
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

The verifier's output may be a bare JSON list or an object with a `reviews`,
`records` or `results` list; all four shapes are accepted so nobody has to reformat a
review by hand. If the file carries a `source_batch_sha256` it must match the batch's
own `batch_sha256`, otherwise the import aborts — verdicts written against a different
batch would attach to the wrong evidence, and that is not a thing to discover later.

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

## 5. Render the QC packet

```bash
python scripts/export_human_qc_packet.py \\
  evals/review/gold_review_batch_001.json evals/review/human_qc_queue_batch_001.json
```

Writes `gold_batch_NNN_qc.md` (decide from this), `gold_batch_NNN_qc.json` (the same
content plus the full audit trail), and a blank `human_decisions_batch_NNN.json`. It
will not overwrite a decisions file that already carries decisions.

Each candidate leads with the **final** question, answer and claims, so nobody has to
reconstruct the case from revision history, then the exact span, then a marked context
window, then one sentence on why a human is needed. Candidates are grouped so the easy
ones go fast:

| group | meaning |
|---|---|
| A — fast track | every term the case asserts appears in the anchored span |
| B — check the anchor | a claim asserts something the span does not contain |
| C — recommended reject | the independent review recommended rejection |

Group B is computed, not asserted: code identifiers and product names in the answer and
claims are checked against the span, and separately against the document title and
section path. A term the span lacks but the section path supplies is reported as weaker
evidence rather than as a gap. This is the OA-002 defect made mechanical.

**Repairs are repairs to wording, not to anchors.** The verdict importer forbids a
reviewer from moving a span, so a boundary defect can only be addressed by rewriting the
question. Where that leaves a claim resting on a term the anchor does not contain, the
packet says so instead of presenting the case as fixed.

Judge each case against the anchored evidence alone. If you need the context window to
answer the question, the anchor is wrong: `NEEDS_EDIT`.

## 6. Approve

Record `APPROVE`, `REJECT` or `NEEDS_EDIT` per candidate in
`evals/review/human_decisions_batch_NNN.json`, then:

```bash
python scripts/import_human_decisions.py \\
  evals/review/gold_review_batch_001.json evals/review/human_decisions_batch_001.json
```

This is the only script that can produce `human_verified`, and it can only do it from a
decision a person wrote. It refuses a decisions file whose `source_batch_sha256` does not
match, refuses unknown or duplicate candidate ids, refuses an invalid decision value, and
**refuses a reviewer name that is a model** — a decisions file claiming `chatgpt` as its
reviewer is not a human decision whatever it says inside. An absent decision leaves the
candidate out of gold; `NEEDS_EDIT` keeps it out too.

Decisions append to `human_decision_history`; re-reviewing a case adds an entry rather
than erasing the first. Revisions, the original proposal and the anchor are untouched.

It then writes `validation_report_batch_NNN.json`, which re-checks what an approval
cannot vouch for: evidence-hash drift, empty or placeholder questions, missing claims,
missing provenance. An approval says the case is right; the report says its bytes still
match the corpus.

## 6a. Repair a boundary the owner sent back

```bash
python scripts/repair_evidence_boundary.py \\
  evals/review/gold_review_batch_001.json \\
  experiments/GOLD-001/batch-001-boundary-repairs.json
```

An anchor is otherwise immutable — `import_verification.py` refuses to let a reviewer
move one. This is the single authorised exception, and it is deliberately narrow:

* it only touches candidates the owner marked `NEEDS_EDIT`;
* the new span must be a **strict superset** of the old, so an anchor can only grow
  outward to include what its claim already depended on. A span that moves elsewhere is
  a re-anchoring, and is refused;
* the old offsets, text and hash are kept in a numbered `anchor_revisions` entry beside
  the new ones. Nothing is overwritten;
* the repaired case returns to `needs_human_review`. Repairing is not approving, and
  this script cannot produce `human_verified`.

It then projects each repaired candidate into the golden-case schema and runs the real
`validate()` over it — alongside the already-approved candidates and the development set,
so duplicate question and duplicate evidence are checked against everything that exists.

**Known schema gap.** The validator's convention is that a critical claim is a literal
string appearing inside its own span; the batch candidates carry sentence-form atomic
claims instead. Repaired cases are authored with both. Every other candidate will need
its critical strings written before it can enter a validated holdout.

## 7. Validate, then freeze

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
| `human_verified` / `human_rejected` | a person decided, via `import_human_decisions.py` |
| `needs_edit` | a person looked and wants it changed — out of gold until it is |
| `needs_human_review` | also where a repaired case lands: the change is made, the approval is not |

Only `human_verified` may enter a holdout. `needs_edit` and an absent decision are both
out, and that is the same outcome by design: gold requires someone to have said yes.

## Batch outcomes

| batch | verdicts | outcome |
|---|---|---|
| 001 | PASS 2, FIX_REQUIRED 15, FAIL 1 | 17 queued for a person; three miner defects recorded in `experiments/GOLD-001/batch-001-findings.md` and preregistered as changes for batch 002 |
| 001 | owner: APPROVE 12, NEEDS_EDIT 3, REJECT 2 | 12 `human_verified`; 2 `human_rejected` kept as negative audit examples; 3 boundary-repaired and back at `needs_human_review`; `GOLD-B001-01` never reached a human and stays `dual_llm_pass`. Batch 001 is **not closed**. |

## What is deliberately not automated

Nothing here raises a case's status on its own. The models can narrow the queue; they
cannot close it. That safeguard already prevented one real mistake — running a
replication against bad ground truth — and weakening it would cost more than the
time it saves.
