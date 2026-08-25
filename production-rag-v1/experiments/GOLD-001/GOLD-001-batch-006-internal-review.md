# GOLD-001 — batch 006 internal source-integrity review

**9 candidates reviewed against the frozen evidence · 6 repaired · reviewed 2026-08-24T17:45:45Z**

This is an internal review by the authoring model. It is not independent verification, not a second opinion from another party, and it changes no candidate's status: all of them remain `candidate_unverified`.

## Outcome

| status | candidates |
| --- | --- |
| NEEDS_REPAIR | 6 |
| READY_FOR_OWNER_REVIEW | 2 |
| REJECT_RECOMMENDED | 1 |

| candidate | status | repaired | findings |
| --- | --- | --- | --- |
| `GOLD-B006-01` | NEEDS_REPAIR | yes | 3 |
| `GOLD-B006-02` | NEEDS_REPAIR | yes | 2 |
| `GOLD-B006-03` | NEEDS_REPAIR | yes | 3 |
| `GOLD-B006-04` | NEEDS_REPAIR | yes | 2 |
| `GOLD-B006-05` | NEEDS_REPAIR | yes | 3 |
| `GOLD-B006-06` | REJECT_RECOMMENDED | no | 4 |
| `GOLD-B006-07` | READY_FOR_OWNER_REVIEW | no | 2 |
| `GOLD-B006-08` | NEEDS_REPAIR | yes | 3 |
| `GOLD-B006-09` | READY_FOR_OWNER_REVIEW | no | 2 |

## Findings by candidate

### GOLD-B006-01 — NEEDS_REPAIR

- TAXONOMY: relabelled from `configuration_interaction` to `exact_lookup` / `requirement_constraint`. The span states one requirement and one restriction; nothing in it describes two settings bearing on each other.
- QUESTION_SCOPE: the generated question asked only what the action requires. The owner's question also asks what a workload may create, which is the second half of the same sentence and was previously carried by the answer without being asked.
- Two atomic claims, both from the same span. This is a compound fact stated in one place — it is NOT multi-hop and is not labelled as such.

**Repairs**

- `question` rewritten
- `answer` rewritten
- `atomic_claims` rewritten
- `reasoning_type` rewritten
- `secondary_category` rewritten

### GOLD-B006-02 — NEEDS_REPAIR

- QUESTION_SCOPE: 'What does Claude Opus 4.7 reject?' invites a list. The evidence supports exactly one rejection, so the question is rewritten to ask about that condition and its outcome.
- CRITICAL_STRINGS: extended to the four the owner named. All four are literally present in the anchor; the generated record carried only `messages`, which anchored the weakest part of the claim.

**Repairs**

- `question` rewritten
- `answer` rewritten

### GOLD-B006-03 — NEEDS_REPAIR

- TAXONOMY: relabelled to `lifecycle_compatibility_migration` / `compatibility`. The span states what is accepted, what is unavailable, and what the newer versions therefore behave like — a compatibility statement, not a lookup.
- QUESTION_SCOPE: 'What does Claude Haiku 4.5 accept?' asks for half of it. The owner's question asks how the newer versions behave there, which is what the sentence is about.
- This is a compound fact stated explicitly in ONE span. It is NOT genuine multi-hop and is not labelled as such.

**Repairs**

- `question` rewritten
- `answer` rewritten
- `atomic_claims` rewritten
- `reasoning_type` rewritten
- `secondary_category` rewritten

### GOLD-B006-04 — NEEDS_REPAIR

- The owner approved this as currently supported and offered a scoped wording 'if desired for naturalness'. It is applied, because it fixes the same breadth defect the owner REQUIRED fixing on GOLD-B006-05, and leaving the two inconsistent would be arbitrary. The fact is unchanged; only the question names the surfaces the source names.
- CRITICAL_STRINGS: `Claude Sonnet 5` added so the model scope the question now asserts is machine-checkable against the anchor. The generated record anchored only `high`.

**Repairs**

- `question` rewritten
- `answer` rewritten

### GOLD-B006-05 — NEEDS_REPAIR

- QUESTION_SCOPE: `thinking.display` does not have one default. The source gives the default for two named models, so the question names them.
- The owner offered a second atomic claim about `display: "summarized"` and said to include it only if the question is meant to test it. It is NOT included: the question asks about the default, and a claim nothing asks about is an unscored assertion sitting in a benchmark record. The sentence stays in the evidence, where it is context.
- CRITICAL_STRINGS: the two model names added, so the scope the question now asserts is anchored.

**Repairs**

- `question` rewritten
- `answer` rewritten
- `atomic_claims` rewritten

### GOLD-B006-06 — REJECT_RECOMMENDED

- The fact is supported: `AWS_BEDROCK_BASE_URL` can override the region-derived Bedrock endpoint.
- DUPLICATE_FACT: GOLD-B005-11, approved in batch 005, carries the same operational relation from the OpenAI Python library. This candidate obtains it from the TypeScript/JavaScript library. Source corroboration is useful; a second benchmark case for the same relation is not.
- The duplicate-control gate did not catch this. It compares question text, span offsets and span text, and two libraries documenting the same behaviour share none of those. Recorded as a generator defect for batch 007 rather than patched here.
- Preserved as an audit example. NOT replaced with a new candidate — the owner was explicit about that.

### GOLD-B006-07 — READY_FOR_OWNER_REVIEW

- The anchor is one self-contained sentence: the condition (setting `audio.input.turn_detection` to `None`) and the outcome (automatic turn detection is disabled) are both inside it.
- Relation direction is correct — the setting is the subject of `disables`, and the question asks it that way round.

### GOLD-B006-08 — NEEDS_REPAIR

- TAXONOMY: relabelled to `lifecycle_compatibility_migration` / `migration`. The sentence is about a compatibility path being a migration bridge, not about two settings interacting.
- QUESTION_SCOPE: the question now also asks how the path should be treated, which is the half of the sentence the answer already carried.
- The owner said to keep the MCP/`httpx2` sentence 'only if it is needed by the final claims'. It is not: no claim uses it. It is dropped from the CRITICAL STRINGS, which is what makes it scored. The sentence stays inside the anchor, because shrinking an anchor is not a repair this project permits — every anchor revision must be a strict outward growth. If the owner meant the span itself, that is a separate instruction and this note is the place to correct it.

**Repairs**

- `question` rewritten
- `answer` rewritten
- `atomic_claims` rewritten
- `reasoning_type` rewritten
- `secondary_category` rewritten

### GOLD-B006-09 — READY_FOR_OWNER_REVIEW

- The fully-qualified identifier `RunErrorHandlerResult.include_in_history` scopes the question by itself — there is no other `include_in_history` this could mean.
- The anchor is the whole fact in one sentence.

## Generator defects found during review

Recorded rather than patched. The generation artifact is not being regenerated, so a fix belongs in the next batch's preregistration where it can be declared before it sees a candidate.

- **E. cross-library duplicate facts are invisible to duplicate control** (seen in GOLD-B006-06). Duplicate control compares normalised question text, span offsets and span text. Two provider libraries documenting the same operational behaviour share none of those, so the same fact can enter the benchmark twice from two SDKs. GOLD-B005-11 and GOLD-B006-06 both state that a base-URL environment variable overrides the region-derived Bedrock endpoint.
  - *Proposed fix, preregistered for batch 007:* Compare candidates on their (subject, relation, object) triple, normalised, in addition to text and offsets. Batch 006 records that triple on every candidate, so the material for the check now exists. Flag rather than auto-drop: two libraries genuinely differing in behaviour is a real case, and only a reviewer can tell the two apart.
- **F. compound single-span facts are labelled by their first verb** (seen in GOLD-B006-01, GOLD-B006-03, GOLD-B006-08). The predicate lane picks a frame from the first matching verb and takes the reasoning type from that frame. Three of the nine exported candidates were relabelled by the owner: a requirement read as a configuration interaction, a compatibility statement read as an exact lookup, and a migration note read as a configuration interaction. The evidence was right in every case; the taxonomy was not.
  - *Proposed fix, preregistered for batch 007:* Classify from the whole sentence rather than from the matched verb: a span naming a support status, a version or a migration is a lifecycle case whatever its verb, and `configuration_interaction` should require two settings that bear on each other rather than one requirement with two identifiers in it.
- **G. questions inherit the breadth of their frame, not of their evidence** (seen in GOLD-B006-02, GOLD-B006-04, GOLD-B006-05). 'What does X reject?' and 'What does X default to?' ask for a complete list. The evidence gives one item, usually scoped to named models or surfaces. Three candidates needed rescoping, and in two of them the scope qualifier was not even in the critical strings, so nothing checked it.
  - *Proposed fix, preregistered for batch 007:* When the source sentence carries a model, platform or surface qualifier, the question must carry it too and it must appear in the critical strings. Add a generation gate: a question whose evidence is scoped and whose wording is not, does not export.

## What this review did not do

- It did not approve anything. `human_verified` requires an owner decision.
- It did not rewrite the generation artifact; repairs live beside it with the original text and offsets preserved.
- It did not regenerate the batch, add a candidate, or search for new multi-hop chains.
- It did not run retrieval. SYSTEM-A and SYSTEM-B remain frozen and unexecuted, and the holdout is not frozen.
