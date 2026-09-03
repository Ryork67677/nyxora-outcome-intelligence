# EXP-014R — DOC-C Replication and Golden Set Expansion

**Status: the replication could not be performed. The reason is the finding.**

The systems were frozen and hashed, the evaluation infrastructure was built and
works, and the harness reproduces EXP-014 exactly. But the expanded golden set that
the replication depends on **could not be built to a usable standard**, and running
a replication on the set that *was* generated would have produced a confident number
with nothing behind it.

Two things were learned that are worth more than the replication would have been:

1. **The EXP-014 result is not statistically distinguishable from zero on its own
   data.** Bootstrap 95% CI on the macro-recall delta: **[+0.000, +0.250]**.
   McNemar exact p = **0.5** on 2 discordant pairs.
2. **The original human-verified development set contains a real defect**, found by
   the new validator: OA-002's critical claim does not appear in its own evidence
   span.

## 1. What was delivered

| deliverable | status |
|---|---|
| SYSTEM-A and SYSTEM-B frozen and hashed | **done** |
| Golden-set schema, splits, provenance fields | **done** |
| `validate_golden.py` with 16 blocking checks | **done** |
| Source-anchored candidate generator | **done** — and it demonstrates why this approach fails |
| Development split, verbatim, hashed | **done** (22 cases) |
| Replication harness with bootstrap + McNemar | **done**, verified against EXP-014 |
| Expanded validation/holdout splits (100–150 cases) | **NOT delivered** |
| Holdout replication of DOC-C | **NOT run** |

## 2. Frozen systems

```
SYSTEM-A-GLOBAL  9afcb5b7c58ebacf…   global BM25 + transformer RRF
SYSTEM-B-DOC-C   304c350940b83733…   DOC-C-SECTION routing -> frozen Stage 2
```

Both were frozen **before** any new evaluation data existed, exactly as the brief
requires. `rag_v1.systems` states each configuration as data and hashes everything
that could change a result. Recorded metrics are excluded from the hash (an outcome
is not a setting) and a test proves that changing `top_documents` *does* change the
hash.

The secondary 19/20 router is recorded as explicitly **not under test**, with its
reason: it routes better and retrieves worse.

## 3. Why the golden set could not be expanded

The brief permits automated candidate generation with human verification
(§17–18). **There is no human in this session**, so the honest ceiling on any
question I generate is `source_anchored_automatic`, never `human_verified`.

That alone would have been survivable. What was not survivable is quality.

### Three generations, each tightened, each still wrong

| pass | yield | representative failure |
|---|---|---|
| 1. broad patterns | 123 | "Which HTTP status code corresponds to **the ptimized condition**?" → claim `512`. A truncated word, and a status code invented by pairing an unrelated number with a nearby token. |
| 2. + identifier shape, + soundness check | 45 | "What is the maximum value allowed for **resold**?" — a word fragment treated as a parameter. `rbac_group_id → 100`, where the 100 governed something else in the sentence. |
| 3. + literal-value filter, limit pattern removed | 20 | `tool_choice → True` (wrong — it is not a boolean). `effort` given **two contradictory answers** in two cases. `max_concurrent_subagents → used`. |

Each tightening cut yield without eliminating false facts. The third pass produced
**12 supported questions**, several still wrong — against a stated minimum of 100.

The failure is structural, not a bug. Extracting "X defaults to Y" from prose
requires knowing which `X` a sentence is *about*; regexes bind to the nearest
plausible token, which is right often enough to look fine in aggregate and wrong
often enough to poison an answer key. **An evaluation set is the one artifact that
cannot be checked by running it** — a wrong key produces a confident number with
nothing behind it.

### What was NOT done

No replication was computed on those 12 questions. Reporting "DOC-C replicated on
n=12" would have been worse than reporting nothing, because it would have carried
the authority of a number while resting on claims the corpus does not support.

## 4. The validator works — it blocked the run

`scripts/validate_golden.py` performs 16 checks, and validation failure blocks
evaluation. Run against the generated candidates it correctly refused them:

```
20 cases, 13 failures
  human_verified_required            12
  duplicate_question                  1
```

The duplicate it caught is the contradictory `effort` pair. The human-verification
gate is what stops machine-generated ground truth from silently becoming gold.

Checks implemented: unique ids · valid split/category/provider/verification ·
supported cases have evidence and claims · abstention cases carry neither ·
source version exists in the snapshot · char spans in range · section path present ·
**evidence span hash matches** · **every critical claim appears in its own evidence
span** · no duplicate questions · no duplicate evidence · no chunk-id ground truth ·
human verification required for holdout.

## 5. A real defect in the original golden set

The claim-supported-by-evidence check found this on the *human-verified*
development set:

**OA-002** — "Which exception does the OpenAI Agents SDK raise when a run exceeds
the `max_turns` limit?", critical claim `MaxTurnsExceeded`. Its cited span reads:

> "This exception is raised when the agent's run exceeds the `max_turns` limit
> passed to the `Runner.run`, `Runner.run_sync`, or `Runner.run_streamed` methods…"

The span *describes* the exception without naming it. `MaxTurnsExceeded` occurs
elsewhere in the document; the anchor's start boundary excludes it.

A system returning exactly this span is scored as having found the evidence though
the span alone cannot support the claim. One of 22 spans is affected — up to ~4.5
percentage points, about one case, on every experiment since EXP-000.

**It has not been fixed**, per §7. Correcting it now would silently change the
meaning of every historical number without re-running anything. It is recorded in
`experiments/EXP-014R/known-data-defects.md`, and a test asserts the record stays.

## 6. Harness verification on the development set

The replication harness was run end to end on the development split. It reproduces
EXP-014 exactly:

| system | macro recall | full | spans@10 | doc R | MRR |
|---|---|---|---|---|---|
| SYSTEM-A-GLOBAL | 0.775 | 15/20 | 17/22 | 0.925 | 0.449 |
| SYSTEM-B-DOC-C | 0.875 | 17/20 | 19/22 | 0.925 | 0.474 |

Paired: B rescues **AN-006, AN-011**; **zero regressions**; net **+2**;
delta **+0.100**. Routing: all expected documents in the top 5 for **18/20** cases.

This is the *development* set — the same data EXP-014 used, and no longer an
unbiased holdout. It is a reproduction, not a replication.

## 7. The statistics that motivated this phase

Applying the new machinery to the development result:

| statistic | value |
|---|---|
| macro-recall delta | **+0.100** |
| bootstrap 95% CI (10,000 paired resamples of questions, seed 20250818) | **[+0.000, +0.250]** |
| fully-recalled delta per case | +0.100, CI [+0.000, +0.250] |
| McNemar discordant pairs | 2 (both favouring B) |
| McNemar exact p | **0.5** |

**The lower bound touches zero.** Two rescues out of twenty questions is exactly the
evidence you would expect from a real +0.100 effect and also from a coin landing
twice — the data cannot separate them. The bootstrap resamples *questions*, not
spans, because spans within a question are not independent; resampling spans would
have produced a falsely narrow interval.

This is the strongest available argument that the replication was the right next
step, and that it remains outstanding.

## 8. Provider and category coverage — a further constraint

The corpus is 139 Anthropic / 63 OpenAI documents, and the extraction yield was
worse still for OpenAI. Two requested categories are **not buildable from this
corpus at all**:

* **version_conflict** — the snapshot contains **zero** superseded versions
  (`supersedes_version_id` is null everywhere), so "current vs superseded" questions
  cannot be anchored. 52 documents discuss deprecation *within* one version, which
  is a weaker and different thing.
* **routing_heavy / passage_heavy** — these are properties of how the *systems*
  behave, not of the corpus. Labelling them would require running the systems first,
  which is precisely the leakage the split design exists to prevent.

## 9. Limitations

* No holdout exists, so **DOC-C remains unreplicated**. Nothing here changes its
  status.
* The 12 generated questions are retained as `evals/golden/candidates.jsonl` for
  reference only. They are **not** an evaluation set and the validator rejects them.
* Even a correct auto-generated set would carry an authorship problem: I know how
  both systems work, so questions I write are not neutral instruments.
* **EXP-NULL remains BLOCKED** — no project generation credential.

## 10. Promotion decision

**DOC-C is not promoted.** The frozen production baseline remains SYSTEM-A-GLOBAL
(BM25 + transformer RRF, control chunks, `top_k=10`).

EXP-014's +2/0 result stands as recorded, on the development set, with a confidence
interval whose lower bound is zero. That is a promising candidate, not a validated
improvement, and it was never eligible for promotion without replication.

## 11. What the measurements justify next

1. **The blocker is human question authoring, and it cannot be automated away.**
   Roughly 100–150 source-anchored questions need a person to write or verify them.
   Everything else needed to consume them now exists: schema, splits, manifests,
   validator, harness, bootstrap, McNemar, frozen hashed systems.
2. **Fix the generator's role.** It should propose *candidate evidence spans* for a
   human to write questions against — the span extraction was reliable; the
   question and claim synthesis was not.
3. **Decide about OA-002 explicitly.** Either accept a known ~4.5-percentage-point
   defect in all historical numbers, or create `development/v2` and re-run the
   affected experiments. Do not fix it silently.
4. **Do not run more retrieval experiments against n=20.** Six of the last seven
   turned on one or two cases, and this phase shows the interval on such a result
   includes zero.
5. **If the corpus is ever re-fetched, capture version chains.** Without superseded
   versions the project cannot test the temporal-conflict behaviour it was designed
   to handle.
