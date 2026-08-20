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

## 6b. Approving a repaired case

Once an anchor has been extended, the candidate id has two spans with two hashes, and a
bare `APPROVE` is ambiguous. An approval of a repaired case must pin the version it
applies to:

```json
{
  "candidate_id": "GOLD-B001-03",
  "decision": "APPROVE",
  "approves_anchor_revision": 1,
  "approves_evidence_hash": "54f4b6a0802f04ab…"
}
```

The importer refuses an approval that omits the pin, one that names a hash other than
the current anchor, and — specifically — one that names the anchor *as it was before the
repair*, since that version was sent back rather than approved. The pin is stored on the
decision, so a later reader can tell which span the owner actually saw.

## 6c. Project and validate

```bash
python scripts/export_golden_projection.py evals/review/gold_review_batch_001.json
python scripts/validate_golden.py \\
  evals/review/batch_001_approved_projection.jsonl --require-human validation
```

A review batch and a golden set are different shapes, so the approved candidates are
projected into the golden-case schema and run through the real validator. The projection
asserts a **placeholder** split; assigning cases to validation or holdout is a separate
decision and is not made there.

The projection prints how many cases are genuinely claim-checked. For batch 001 that is
3 of 15 — see the schema gap in §6a. A validator pass over the other 12 says nothing
about claim support, and the script says so rather than letting the green tick imply it.

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

## Two states, not one

`human_verified` and `holdout_eligible` are separate, and conflating them is the defect
the batch 001 claim audit found.

| state | means |
|---|---|
| `human_verified` | a person read the case and said yes — historical, permanent, never revoked by tooling |
| `holdout_eligible` | all five conditions in `rag_v1.gold.eligibility` hold **right now** |

The conditions: human approval · a deterministic check for every claim · critical strings
present in the evidence · a valid evidence hash · no unresolved scope defect.

A case can gain eligibility through added metadata without being re-approved, and lose it
to a corpus change without the approval being called wrong. **Only `holdout_eligible`
cases may enter a frozen holdout.**

## Comparing a claim to its evidence

Claims are checked as literal strings inside the anchored span, with one documented
transformation: **Markdown backslash escapes are undone on both sides, and nothing else.**
`GOLD-B002-02`'s row writes the URL scheme as `https\://` so the renderer does not
linkify it, while the claim writes `https://`; failing on a backslash the renderer would
drop is a defect in the checker, not the evidence.

No case folding beyond the existing case-insensitive match, no whitespace collapsing, no
quote or dash substitution — each would let a claim match evidence that does not say it.
Normalisation lives only inside a comparison: evidence is stored raw, hashed raw and
displayed raw, so the exact source form survives for audit. See
`src/rag_v1/gold/normalisation.py`.

## Versioned promotion overlays

When later work shows an approved case is missing something a machine needs, the answer
is a new version layered on top, never an edit underneath:

```bash
python scripts/build_batch_v2_overlay.py evals/review/gold_review_batch_001.json
python scripts/validate_golden.py evals/gold/batch_001_v2/projection.jsonl \\
  --require-human validation
```

The builder re-verifies the v1 closure hash first and refuses to layer on drifted
records. It copies question, answer, claims, span, version and hash from the closed case
and refuses to write if the spec would change any of them — an overlay of this kind adds
validation metadata and nothing else.

A defect metadata cannot fix goes to `scripts/propose_scope_repairs.py`, which writes a
packet and applies nothing.

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
| 001 | owner: APPROVE 12, NEEDS_EDIT 3, REJECT 2 | 12 `human_verified`; 2 `human_rejected` kept as negative audit examples; 3 boundary-repaired and back at `needs_human_review` |
| 001 | owner: APPROVE the 3 repairs | 15 `human_verified`, 2 `human_rejected`, 1 `dual_llm_pass` |
| 001 | **CLOSED** | 16 `human_verified`, 2 `human_rejected`, 88.9% acceptance. `validate_golden.py` passes on all 16 with `--require-human validation`. Closure hash `d6f92e8d1a7e77ea…`; the test suite re-checks it, so an edit after closure fails the tests. See `experiments/GOLD-001/GOLD-001-batch-001-closure.md`. |
| 002 | generated | 18 candidates, 50% structural, 9 complete proposals. Built with the four preregistered rules and nothing else. |
| 002 | independently reviewed | 0 rejects, all 18 FIX_REQUIRED. A new defect class found: 9 structural candidates whose miner-written question depended on table-header semantics outside the row. 2 anchor extensions (`12`, `18`). |
| 002 | **CLOSED** | 17 `human_verified`, 1 `human_rejected` (`12`, OVERSIZED_EVIDENCE_ANCHOR — a 1,430-character anchor for one fact), 94.4% acceptance. **17 of 17 carry critical strings**, against batch 001's 3 of 16. Closure hash `69364f672e233fb3…`. |

## Auditing a closed batch

```bash
python scripts/audit_claim_support.py evals/review/gold_review_batch_001.json
```

A passing `validate_golden.py` run is weaker than it looks: the claim-in-evidence gate
only fires on claims marked *critical*, and a case with none passes it vacuously. This
audits the approved claims of a closed batch without touching it — no record is modified
and the closure hash is not recomputed — and writes an overlay keyed by candidate id and
approved evidence hash.

It is a mechanical screen, not a semantic proof: it checks that the terms a claim turns
on appear inside the approved span, and measures content-word coverage. Anything short of
clean is `NEEDS_REVIEW` addressed to a person, never a verdict. Findings that would
change a closed case become a **proposed** v2 promotion, returned for approval and
applied to nothing.

## Closing a batch

```bash
python scripts/close_batch.py evals/review/gold_review_batch_001.json
```

Closure is a statement that every candidate reached a human decision, so the script
refuses to write one while anything is outstanding, and refuses if the validator did not
pass. It records a `closure_sha256` over the candidate records; the test suite re-checks
it, which is the difference between saying a closed batch does not change and being able
to tell when it has.

## What is deliberately not automated

Nothing here raises a case's status on its own. The models can narrow the queue; they
cannot close it. That safeguard already prevented one real mistake — running a
replication against bad ground truth — and weakening it would cost more than the
time it saves.
