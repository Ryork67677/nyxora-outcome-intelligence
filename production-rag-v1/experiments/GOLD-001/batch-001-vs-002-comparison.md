# GOLD-001 — batch 001 vs batch 002 candidate quality

Batch 002 was generated with the four rules preregistered from batch 001's verified
results, and with nothing else changed about what counts as a good candidate.

**Nothing below is a precision measurement.** Batch 001's numbers are outcomes — a
person decided every one of them. Batch 002's are generator-side properties, checked by
the same code that produced them. Whether batch 002 is actually better is a question
only independent review and a human can answer, and it has not been asked yet.

## What changed in the candidates

| | batch 001 (as generated) | batch 002 |
| --- | --- | --- |
| candidates | 18 | 18 |
| pool drawn from | 85 | 70 |
| structural (table row) | 2 (11%) | **9 (50%)** |
| complete question + answer + claims | 2 | **9** |
| reviewer must author the question | 16 | 9 |
| candidates carrying critical claim strings | 0 | **9** |
| high generator confidence | 2 | 9 |
| OpenAI candidates | 6 | **3** |
| distinct source documents | 18 | 18 |

## The four rules, and what they did

**Rule 1 — anaphoric spans extended or dropped.** The check is mechanical: a span that
opens on a reference (`If true`, `Otherwise`), or that says `these models` without
naming them, is grown backwards up to three sentences until it contains its own
antecedent, and dropped if it cannot. Both batch-001 shapes are covered by tests that
name the candidate they come from — `GOLD-B001-04` and `GOLD-B001-14`. Applying the
detector to batch 002's prose spans finds **0 unresolved references**.

**Rule 2 — no relation label exported.** Batch 001 shipped `explicit_exception`,
`explicit_response` and so on; the label was wrong on 5 of 16 and, per the reviewer's own
notes, steered the first reading. Prose candidates now carry one neutral kind,
`prose_statement`, and the marker phrase that selected the sentence is not written to the
file at all. The defect is not reduced in batch 002; it is **structurally impossible**,
because there is no longer a label to be wrong.

**Rule 3 — no rules from example code.** Spans overlapping a fenced block are refused, as
are spans shaped like code (assignments, JSON keys, bare closing brackets). This is the
`GOLD-B001-15` failure — `required: ["location"]` read out of a request body — and the
one that made the EXP-014R generator unusable. Batch 002 contains **0 code-shaped
spans**.

**Rule 4 — more structural candidates.** From 11% to 50%, enforced: the exporter refuses
to write a batch below the required share rather than quietly shipping fewer. Batch 001's
two structural candidates were the only two that passed independent review with nothing
rewritten, which is the whole argument for the change — and two observations is what that
argument rests on.

## One defect the rules exposed, fixed here

Extending spans backwards made a pre-existing sentence-splitter defect visible: it cuts
numbered lists mid-clause and strands the next item's marker on the end. The first batch
002 run produced spans like ``[`Runner.run()`][…], which runs async and returns a
[`RunResult`][…]\n2.`` and ``See [Route matching](https://…).`` — fragments, and in the
second case a span that cleared a 60-character minimum on URL alone.

Candidates must now end a sentence, start one, survive having link URLs discounted, and
not be a list item whose stem lives outside the span. **This is not a change to the four
rules** — it is a fix to a defect they surfaced, and it is recorded here rather than
folded in silently.

## What got worse

**Provider balance: 6 OpenAI candidates to 3.** Rule 4 and provider balance pull against
each other, and rule 4 now wins. The corpus holds far fewer OpenAI parameter tables that
state requiredness or type, so demanding a structural half necessarily skews the batch
toward Anthropic. This is a real cost of the change, not a rounding artifact, and if
cross-provider coverage matters more than structural share, rule 4 is the thing to
revisit — after batch 002 is reviewed, not before.

**Structural questions are template-shaped.** Nine structural candidates come from three
templates: "Is the `X` parameter required?" (6), "What type does the `X` parameter
take?" (3). A retrieval benchmark built mostly from one phrasing tests one phrasing. The
type miner exists specifically to keep this from being a single template, but three
shapes is still narrow, and it is the thing most likely to limit what batch 002 can
tell you.

**The pool shrank from 85 to 70.** Rules 1 and 3 reject candidates, which is what they
are for. A smaller pool means less room for selection to be choosy.

## What is unchanged

- `retrieval_was_not_run: true`. No retrieval ran against any candidate.
- Every candidate is `candidate_unverified`. Nothing is gold, nothing is
  `human_verified`, and no script here can make it so.
- No span or question overlaps batch 001, including the pre-repair spans.
- SYSTEM-A and SYSTEM-B are frozen and were not executed.
- `development/v1` is untouched; OA-002 is still a recorded defect with an unapplied
  correction proposal.
