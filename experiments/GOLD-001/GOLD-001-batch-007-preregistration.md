# GOLD-001 — batch 007 preregistration

**Controlled evidence-grounded question paraphrasing.**

*PREREGISTERED — no batch-007 candidate has been generated. Written 2026-08-25T06:50:29Z against corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a`.*

This document fixes the authoring contract for batch 007 **before any candidate exists**. That is the point of preregistering: a rule written after seeing the output is a rule fitted to the output. Every figure below is read from the closed record.

## Why the method is changing

Batch 006 was commissioned at **28** candidates and exported **9**. Its census is why:

| | |
| --- | --- |
| facts mined | 1361 |
| distinct evidence spans the miners reach | 773 |
| **unspent by any closed batch** | **699** |
| mined facts that reached no builder | None |

**The corpus is not exhausted. The authoring is.** 699 distinct spans have never been used, and deterministic templates cannot express them: what remains in this snapshot is long, multi-clause prose, and a template that fits it is a template that invents wording. Refusing all paraphrase is precisely what keeps those facts out of the benchmark.

## The line this batch draws

> The authoring model may change WORDING. It may not change MEANING. It authors the QUESTION; it never invents the FACT.

This is an **authoring** change. The evidence stays frozen and exact, the ground truth is still read out of the source, and every existing gate still runs. What changes is that a model may write the question when a template cannot.

### The order is the safeguard

1. frozen source evidence selected
2. literal source fact extracted
3. subject / relation / object recorded
4. atomic claims anchored
5. only then the natural question is paraphrased

**Never:** invent question → search for supporting evidence. Inventing a question and then hunting for evidence to support it is how a benchmark ends up testing what its author imagined rather than what the documentation says.

### Recorded on every paraphrased candidate

- `source_fact_literal`
- `source_subject`
- `source_relation`
- `source_object`
- `generated_question`
- `generated_answer`
- `generated_atomic_claims`
- `paraphrase_used`

The literal source fact sits on the record beside the authored question, so a reviewer can see the gap between them and disagree with it.

## The entailment self-check

| | check | it fails when |
| --- | --- | --- |
| **A** | Does the exact evidence support the complete answer? | any part of the answer is not derivable from the anchored spans |
| **B** | Does every atomic claim map to literal evidence? | a claim has no span whose text supports it |
| **C** | Did the question introduce any new condition? | the question adds an 'if', 'when' or 'unless' the source lacks |
| **D** | Did it broaden model/provider/platform scope? | the source names a model, provider, platform or surface and the question drops or generalises it |
| **E** | Did it reverse the relation? | the question's subject is the source's object and vice versa, and the relation is not symmetric |
| **F** | Did it introduce a causal claim absent from the source? | the answer explains why, and the source only says what |
| **G** | Could the answer be verified using only the exact evidence? | verifying it needs the surrounding document, a heading, or outside knowledge |

**Any failure: DROP.** There is no flag-and-continue branch, deliberately — a caveat in a benchmark is a defect with an excuse.

## Answer conservatism

The question may be naturalised more aggressively than the answer. Prefer answers close to the source wording.

Source says *A overrides B* →️ answer *A overrides B*, **not** *A overrides B because this improves reliability*. The reason is not in the source. An answer that explains is an answer that asserts something the evidence cannot check.

## Calibration pilot — required before the lane scales

**10 spans**, selected as: 10 evidence spans that failed batch 006 ONLY because no builder could express them — NO_BUILDER / UNBUILDABLE. Not spans that failed a semantic gate: those failed for reasons paraphrasing does not fix.

| criterion | threshold |
| --- | --- |
| independently judged factually sound | ≥ 8 of 10 |
| unsupported claims | 0 |
| relation-direction reversals | 0 |
| scope broadening | 0 |
| wording cleanup needed | acceptable, does not count against the criterion |

**If it fails:** Do not scale the paraphrasing lane. Revise the authoring contract first and re-pilot.

The pilot is independently reviewed before the lane may scale, and no retrieval is run on the pilot.

## Every existing gate still runs

| gate | implemented in | behaviour |
| --- | --- | --- |
| bare definition scope | `rag_v1.gold.scoping` | every span, independently |
| critical anaphora | `rag_v1.gold.anaphora` | blocks; noncritical flags |
| subject / relation direction | `rag_v1.gold.relations` | REVERSED and SUBJECT_MISMATCH both drop |
| question form matches evidence form | `rag_v1.gold.questionform` | negative-as-positive and truncated predicates drop |
| duplicate detection | `scripts/export_batch_007.py` | question text, span offsets, span text — and now the relation triple |
| critical strings | `rag_v1.gold.normalisation` | every one must be literally inside its own span |
| evidence hashes | `scripts/export_batch_007.py` | each span hashes to its own text |
| scope self-containment | `rag_v1.gold.scoping` | section_path is never claim scope |
| example-code restriction | `scripts/export_batch_007.py` | a sample configuration is not a rule |
| evidence size | `scripts/export_batch_007.py` | <500 preferred, 1000 soft cap, 1500 hard cap |
| provider / model scope | `scripts/export_batch_007.py` | a scoped source needs a scoped question |
| holdout eligibility | `rag_v1.gold.eligibility` | deterministic, run after owner approval |

Controlled paraphrasing is an **additional authoring method, not a weaker pipeline**.

## Generator defects to fix before batch 007 authors anything

| | defect | seen in |
| --- | --- | --- |
| **E** | cross-library duplicate facts are invisible to duplicate control | `GOLD-B006-06` |
| **F** | compound single-span facts are labelled by their first verb | `GOLD-B006-01, GOLD-B006-03, GOLD-B006-08` |
| **G** | questions inherit the breadth of their frame, not of their evidence | `GOLD-B006-02, GOLD-B006-04, GOLD-B006-05` |

**E. cross-library duplicate facts are invisible to duplicate control** — Duplicate control compares normalised question text, span offsets and span text. Two provider libraries documenting the same operational behaviour share none of those, so the same fact can enter the benchmark twice from two SDKs. GOLD-B005-11 and GOLD-B006-06 both state that a base-URL environment variable overrides the region-derived Bedrock endpoint.

*Proposed fix:* Compare candidates on their (subject, relation, object) triple, normalised, in addition to text and offsets. Batch 006 records that triple on every candidate, so the material for the check now exists. Flag rather than auto-drop: two libraries genuinely differing in behaviour is a real case, and only a reviewer can tell the two apart.

**F. compound single-span facts are labelled by their first verb** — The predicate lane picks a frame from the first matching verb and takes the reasoning type from that frame. Three of the nine exported candidates were relabelled by the owner: a requirement read as a configuration interaction, a compatibility statement read as an exact lookup, and a migration note read as a configuration interaction. The evidence was right in every case; the taxonomy was not.

*Proposed fix:* Classify from the whole sentence rather than from the matched verb: a span naming a support status, a version or a migration is a lifecycle case whatever its verb, and `configuration_interaction` should require two settings that bear on each other rather than one requirement with two identifiers in it.

**G. questions inherit the breadth of their frame, not of their evidence** — 'What does X reject?' and 'What does X default to?' ask for a complete list. The evidence gives one item, usually scoped to named models or surfaces. Three candidates needed rescoping, and in two of them the scope qualifier was not even in the critical strings, so nothing checked it.

*Proposed fix:* When the source sentence carries a model, platform or surface qualifier, the question must carry it too and it must appear in the critical strings. Add a generation gate: a question whose evidence is scoped and whose wording is not, does not export.

## Where the project stands

| | |
| --- | --- |
| human_verified | **90** |
| holdout_eligible | **90** |
| rejected | 9 |
| genuine multi-hop | 1 |
| project target | **150** |
| still needed | **60** |

Batch 007 targets **35-40** candidates. At the observed acceptance rates (001 89% · 002 94% · 003 100% · 004 93% · 005 79% · 006 89%), that lands between **117** and **130** eligible cases — short of 150, so more than one batch will be needed.

*A projection, not a plan. It is recorded so nobody has to compute it during review, and it must not influence any individual approval. If controlled paraphrasing yields only 25 strong cases, batch 007 returns 25.*

## Who may set `human_verified`

Only the project owner. No AI may set human_verified, and controlled paraphrasing does not make Claude authoritative about anything.

Workflow, unchanged: **frozen evidence** → **Claude authoring** → **Claude internal semantic self-review** → **ChatGPT independent verification** → **project-owner approval** → **holdout eligibility**.

## Not done in this document

- No batch-007 candidate was generated.
- No pilot was run.
- No paraphraser was implemented.
- No retrieval was run.
- Nothing was frozen.
