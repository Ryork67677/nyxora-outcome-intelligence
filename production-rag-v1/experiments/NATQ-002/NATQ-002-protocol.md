# NATQ-002 — authoring protocol and stage-1 result

**Purpose.** A fresh 100-case benchmark whose questions were written *before* any
evidence was looked at, to remove the source-anchored bias in V2-DEVSET-001 and
GOLD-001. Those were mined from the corpus, so their wording echoed the corpus
and made retrieval look easier than it is (see ASSESS-001, concern C3).

**Status: stage 1 of 4 complete.** 150 questions authored blind and triaged
against the frozen snapshot. Evidence packets are NOT yet written. Nothing is
frozen, no split exists, no retrieval has been run.

---

## The contamination problem, and how it was actually solved

The brief requires the question author to have seen none of: source passages,
canonical chunks, evidence spans, retrieval results, previous V2D questions,
previous gold answers, the V1 holdout failures, or exact corpus wording.

**I fail that test.** Earlier in this same session I loaded 400 `cs_v1_control`
chunk texts into context for the PERF-002 cross-encoder microbenchmark, tokenized
53 existing gold questions, and read V2-DEVSET-001 review files. I could not
honestly author these questions, and asserting otherwise would have quietly
destroyed the one property the benchmark exists to have.

**So the authoring was delegated to five isolated agents with cold context**, each
given only a domain slice and style guidance — no repository path, no corpus, no
prior questions — and each instructed explicitly not to read any file, run any
search, or consult the web.

**This is verifiable, not just asserted.** Each agent's run reports its tool-call
count, and all five returned **`tool_uses: 0`**. No agent touched a file, a
database, or a network. Their entire input was the prompt.

| slice | domains | questions | tool uses |
|---|---|---:|---:|
| A | tool use, computer use, structured outputs | 30 | 0 |
| B | streaming, realtime, errors/rate limits/retries | 30 | 0 |
| C | model configuration, context management, migrations | 30 | 0 |
| D | auth/keys/org, SDK behaviour, OpenAI Agents SDK | 30 | 0 |
| E | cross-cutting: batch, vision, embeddings, caching, token counting, billing, moderation | 30 | 0 |
| | **total raw authored** | **150** | **0** |

Residual limitation, stated plainly: the authors share my underlying model, so
its pretraining knowledge of public Anthropic/OpenAI documentation is common to
both. That is inherent to asking an AI to author questions and the brief accepts
it. What has been eliminated is exposure to **this project's** corpus, gold set,
and results — which is the contamination that actually inflates the metric.

## Style discipline given to the authors

Authors were told to write the way developers type, and to vary register
deliberately: incomplete terminology, conversational phrasing, abbreviations,
mistaken-but-resolvable terminology, task- and error-oriented questions,
"what happens if" questions, migration questions, exact-identifier questions, and
configuration-interaction questions. Mixed lengths, typos and lowercase were
explicitly encouraged. Slice E was additionally asked to produce about four
genuinely ambiguous questions; **5 came back flagged**.

They were told *not* to reproduce documentation phrasing, and told that an
unverifiable question is fine because a separate verifier would reject it later.
That instruction matters: it removes the incentive to drift toward corpus
language in order to be "right".

---

## Stage 2 — verification triage (complete; NOT verification itself)

Only after all 150 questions existed did any evidence get inspected.

**Method.** All 14,209 `cs_v1_control` chunks of
`snap_689e336380a054d8039dc35b2c09cd0a` were loaded and aggregated per document
(202 documents). For each question, per-document coverage of its content tokens
was computed by literal substring inspection.

**What this is not.** No BM25, no dense retrieval, no cross-encoder, no ranking,
no candidate set. Nothing that could be used to select easier or harder
questions. It is a reading aid that tells a verifier which document to open
first.

| triage | best-document token coverage | count |
|---|---|---:|
| STRONG | ≥ 0.80 | 134 |
| PROBABLE | 0.65 – 0.80 | 13 |
| REVIEW | 0.50 – 0.65 | 3 |
| LIKELY_UNSUPPORTED | < 0.50 | 0 |

Provider of the best-matching document across STRONG+PROBABLE: **anthropic 121,
openai 26**. Recorded, not forced — the brief asks for balance to be reported
rather than engineered. It is skewed, and the skew is a real property of the
corpus (139 Anthropic vs 63 OpenAI documents), not of the authoring.

**Read this table conservatively.** High token coverage means a document contains
the question's vocabulary. It does **not** mean the document answers the
question. Converting a triage row into a verified case requires reading the
spans, and that has not been done yet.

---

## Stages 3 and 4 — not started

**Stage 3, evidence packets.** For each surviving candidate: confirm the frozen
corpus genuinely answers it; reject unsupported or accidentally-ambiguous cases;
write the supported answer; anchor exact canonical evidence with source offsets;
record atomic claims, critical strings, provider/document/version, evidence
shape, and reasoning/stress types.

The rule that matters most here, from the brief: **a failed question is rejected
and replaced, never rewritten into corpus language to make it answerable.** That
rewrite is exactly how source-anchored bias got into the previous benchmarks, and
150 raw for a target of 100 exists to make rejection affordable.

**Stage 4, split and freeze.** After the coordinator's independent review passes
100 cases: contamination-aware deterministic split into 40 validation / 60
holdout, with fact clusters and near-duplicate intents kept on the same side;
hashes frozen before any retrieval; a NATQ-002 holdout lock and access log
created, separate from the historical V1 holdout log.

## Anti-contamination compliance

No V2D question was paraphrased. No V1 holdout question was touched. No known
retrieval miss was used as a template. No SYSTEM-H output was used — SYSTEM-H has
never been run. No BM25, dense or CE scoring influenced question selection. No
question has been modified after seeing any system result, because no system has
seen any of these questions.
