# GOLD-001 — batch 005 internal source-integrity review

**19 candidates reviewed against the frozen evidence · 7 repaired · reviewed 2026-08-23T16:42:37Z**

This is an internal review by the authoring model. It is not independent verification, not a second opinion from another party, and it changes no candidate's status: all of them remain `candidate_unverified`.

## Outcome

| status | candidates |
| --- | --- |
| READY_FOR_OWNER_REVIEW | 8 |
| NEEDS_REPAIR | 7 |
| REJECT_RECOMMENDED | 4 |

| candidate | status | repaired | findings |
| --- | --- | --- | --- |
| `GOLD-B005-01` | REJECT_RECOMMENDED | no | 4 |
| `GOLD-B005-02` | READY_FOR_OWNER_REVIEW | no | 1 |
| `GOLD-B005-03` | READY_FOR_OWNER_REVIEW | no | 2 |
| `GOLD-B005-04` | READY_FOR_OWNER_REVIEW | no | 2 |
| `GOLD-B005-05` | NEEDS_REPAIR | yes | 2 |
| `GOLD-B005-06` | REJECT_RECOMMENDED | no | 3 |
| `GOLD-B005-07` | READY_FOR_OWNER_REVIEW | no | 1 |
| `GOLD-B005-08` | NEEDS_REPAIR | yes | 2 |
| `GOLD-B005-09` | NEEDS_REPAIR | yes | 3 |
| `GOLD-B005-10` | REJECT_RECOMMENDED | no | 3 |
| `GOLD-B005-11` | NEEDS_REPAIR | yes | 3 |
| `GOLD-B005-12` | READY_FOR_OWNER_REVIEW | no | 1 |
| `GOLD-B005-13` | REJECT_RECOMMENDED | no | 3 |
| `GOLD-B005-14` | READY_FOR_OWNER_REVIEW | no | 1 |
| `GOLD-B005-15` | NEEDS_REPAIR | yes | 2 |
| `GOLD-B005-16` | NEEDS_REPAIR | yes | 2 |
| `GOLD-B005-17` | READY_FOR_OWNER_REVIEW | no | 1 |
| `GOLD-B005-18` | NEEDS_REPAIR | yes | 2 |
| `GOLD-B005-19` | READY_FOR_OWNER_REVIEW | no | 1 |

## Findings by candidate

### GOLD-B005-01 — REJECT_RECOMMENDED

- NOT_A_FIELD: `invalid_tool_input` is a value of the `error_code` field, not a field. The question's noun is wrong before anything else is considered.
- NOT_AMBIGUITY: the two readings are the same concept — 'the input you gave this tool was invalid' — with tool-specific examples (a malformed URL for web fetch, a malformed regex or an over-length pattern for tool search). §12 asks for a term whose semantics differ by scope; an error code whose examples differ by tool is one meaning documented twice.
- SCOPE_IN_HEADING: neither span mentions its tool. E1 reads '* `invalid_tool_input`: Invalid tool input, such as a malformed URL…' and E2 '* `invalid_tool_input`: the search input was invalid…'; 'Web fetch tool' and 'Tool search tool' come from the document titles. This is the bare-definition-bullet defect the generator drops elsewhere — it did not fire here because the rule only inspects single-span records, which is a generator bug recorded below.
- §3 is explicit that ambiguity must not be preserved because the batch has only one such case.

### GOLD-B005-02 — READY_FOR_OWNER_REVIEW

- The anchor carries all three parts §5 asks for: `jwks.type` is `discovery`, no `discovery_base` is set, and the resulting requirement. No boundary repair is needed.

**Interaction recorded**

- A: `jwks.type` set to `discovery`
- B: `discovery_base` absent
- relation: with A selected and B unset, the issuer URL must be publicly reachable over HTTPS so the discovery document can be fetched; under `explicit_url` and `inline` the URL is matched as the `iss` claim and never fetched

### GOLD-B005-03 — READY_FOR_OWNER_REVIEW

- Condition and result are both inside the anchor, as §6 requires.
- NONCRITICAL_SCOPE: the span does not name the endpoint whose list behaviour this is. The question is answerable without it, so the anchor stands; an owner who wants the endpoint named should choose NEEDS_EDIT.

### GOLD-B005-04 — READY_FOR_OWNER_REVIEW

- Condition and result are both inside the anchor.
- NONCRITICAL_SCOPE: the span does not say that `encrypted_content` belongs to the web search tool's results. The fact is answerable as asked.

### GOLD-B005-05 — NEEDS_REPAIR

- QUESTION_SCOPE: 'What must `allowed_domains` be?' drops the qualifier the evidence itself supplies. The span constrains a *request-level* `allowed_domains` list relative to the organization-level list; asked unscoped, the question implies a rule about the parameter in general.
- The scope word is inside the anchor, so this is a question repair and the evidence does not move.

**Repairs**

- `question` rewritten

### GOLD-B005-06 — REJECT_RECOMMENDED

- NOT_A_LIFECYCLE_STATEMENT: the span is a schema field description from a List Models response — 'Model IDs this model accepts as `fallbacks[i].model` on the Messages API' — not a statement about support status. It was mined as lifecycle because its second sentence contains 'not supported'.
- UNANSWERABLE_AS_ASKED: 'Where is `fallbacks` supported?' asks for a set of models. The span says only that an empty list means the parameter is unsupported for that model as primary, which does not answer it.
- A repair would have to rewrite the question into a different fact; the honest outcome is rejection.

### GOLD-B005-07 — READY_FOR_OWNER_REVIEW

- Self-contained: names the parameter, the three SDKs, the deprecation, and the future removal. Narrowest accurate type is deprecation, which is what the secondary category records.

### GOLD-B005-08 — NEEDS_REPAIR

- QUESTION_FORM: 'Where is `budget_tokens` supported?' asks for the set of places it works. The evidence states one place it does not — manual extended thinking is not supported on Claude Sonnet 5 and returns a 400. A question asking for the positive set cannot be answered from a single negative.
- The model scope is inside the anchor, so only the question changes.

**Repairs**

- `question` rewritten

### GOLD-B005-09 — NEEDS_REPAIR

- §9 satisfied on the conditions: all three — malformed JSON, valid JSON that is not an object, and non-standard constants — are disjuncts of a single conditional with one stated result, so nothing needs splitting or narrowing.
- CATEGORY: labelled configuration_interaction, but §4's three fields cannot be filled. The critical strings are `null`, `NaN` and `Infinity`, which are values rather than settings, and no second setting interacts with a first. Relabelled to error_behavior.
- CRITICAL_ANAPHORA: the answer's subject is 'the callable', whose antecedent — 'Callable approval rules fail closed when the SDK cannot safely inspect the arguments' — sits immediately before the anchor. Without it a reader cannot tell which callable is not invoked.

**Repairs**

- `E1` 1609–1855 → 1523–1855 (evidence_boundary_completion); hash `25ef4cc6cccc…` → `d4a15c400fe1…`
- `atomic_claims` rewritten
- `reasoning_type` rewritten
- `secondary_category` rewritten

### GOLD-B005-10 — REJECT_RECOMMENDED

- RELATION_DIRECTION: §10's suspicion is confirmed. The source says 'The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.' `betas` is the object of the rejection, not the subject of an override. The question asks what `betas` overrides, which the source never says.
- SCOPE_IN_HEADING: rewriting around the true subject would make the question about 'the experimental model', which the span identifies only by that phrase. The model's name sits in the section heading and, further down, after the span. There is no minimal outward expansion that brings the identity inside the anchor.
- Both defects would have to be repaired at once, and the second has no honest repair, so the candidate is recommended for rejection rather than rewritten.

### GOLD-B005-11 — NEEDS_REPAIR

- DIRECTION_CORRECT: unlike B005-10 the source does put the environment variable on the acting side — 'set `AWS_BEDROCK_BASE_URL` to override the derived … endpoint'.
- MISSING_CONDITION: §11's warning applies. What is overridden is the endpoint *derived* from the region configuration, and the span says so; the question as asked implies an unconditional override. The provider that derives it, `bedrock(...)`, is named in the span.
- SECTION_PATH_ARTEFACT: the record's section_path is 'configured through AWS_REGION, AWS_DEFAULT_REGION, or your AWS profile.', which is prose the parser mistook for a heading. It is metadata only — no claim rests on it — but a reviewer should not read it as a real section.

**Interaction recorded**

- A: `AWS_BEDROCK_BASE_URL`, or `base_url` passed to `bedrock(...)`
- B: the endpoint derived from the configured AWS region
- relation: A overrides B

**Repairs**

- `question` rewritten

### GOLD-B005-12 — READY_FOR_OWNER_REVIEW

- §12 satisfied: `FuseMountPattern` is the grammatical subject of the requirement, the span states a requirement rather than a definition, and the reason — `blobfuse2` discovering ambient Azure authority — is inside the anchor.

**Interaction recorded**

- A: `FuseMountPattern`
- B: broad acknowledgement of the authority exposure
- relation: A requires B, because `blobfuse2` discovers ambient Azure authority even with no inline credential

### GOLD-B005-13 — REJECT_RECOMMENDED

- DUPLICATE_RELATION: this is the sentence immediately after B005-12's, stating the same relation about a sibling mount pattern. §26 rejects 'the same configuration relation reworded', and two adjacent sentences from one paragraph are not two facts worth two benchmark cases.
- ANAPHORA: the span opens '`S3FilesMountPattern` likewise requires…', and 'likewise' refers to the FuseMountPattern sentence outside the anchor. The requirement is stated in full regardless, so this is noncritical — but combined with the duplication there is no reason to keep it.
- Keeping B005-12 and dropping this one is the choice; they are interchangeable.

### GOLD-B005-14 — READY_FOR_OWNER_REVIEW

- §12 satisfied: `ApplyPatchTool` is a subject of the requirement (compound with `ComputerTool`), the span states a requirement, and 'local implementations that you provide' is operationally meaningful.

**Interaction recorded**

- A: `ComputerTool` and `ApplyPatchTool`
- B: a local implementation supplied by the application
- relation: A always requires B

### GOLD-B005-15 — NEEDS_REPAIR

- QUESTION_BREADTH: §13's concern. 'What happens when a `ComputerTool` is present?' invites any consequence; the span supports exactly one — three `tool_choice` strings are accepted and normalised to the selector matching the effective model.
- LINK_MARKUP: the question carries a raw markdown reference, '[`ComputerTool`][agents.tool.ComputerTool]', which the generator's link stripper did not reach. A question is not a place for documentation plumbing.

**Interaction recorded**

- A: the presence of a `ComputerTool`
- B: the `tool_choice` value
- relation: A changes how B is interpreted: three otherwise-distinct strings are normalised to one built-in selector

**Repairs**

- `question` rewritten
- `answer` rewritten

### GOLD-B005-16 — NEEDS_REPAIR

- QUESTION_BREADTH: §14's concern. 'What happens when you use a `Session`?' is broader than the span, which establishes one specific effect on usage accounting.
- The condition is preserved in the rewrite; only the consequence being asked about is named.

**Interaction recorded**

- A: using a `Session` (for example `SQLiteSession`)
- B: the usage returned by each `Runner.run(...)` call
- relation: A scopes B to the individual run rather than to the accumulated session

**Repairs**

- `question` rewritten
- `answer` rewritten

### GOLD-B005-17 — READY_FOR_OWNER_REVIEW

- §6 satisfied: the condition (exceeding the `max_turns` passed) and the result (a `MaxTurnsExceeded` exception) are both inside the anchor, with no antecedent outside it.

### GOLD-B005-18 — NEEDS_REPAIR

- QUESTION_FORM: 'What must `dispatcher` be?' asks for a value. The span states a pairing requirement — an Undici-specific option must accompany the matching `fetch` implementation — so the question asks for something the evidence does not give.
- SCOPE: 'Undici-specific' is inside the anchor and belongs in the question; the section heading is not needed.

**Repairs**

- `question` rewritten
- `answer` rewritten

### GOLD-B005-19 — READY_FOR_OWNER_REVIEW

- Self-contained removal statement naming both the removed option and its replacement. Narrowest accurate type is removal, which the secondary category records.

## Generator defects found during review

Recorded rather than patched. The generation artifact is not being regenerated, so a fix belongs in the next batch's preregistration where it can be declared before it sees a candidate.

- **the bare-definition-bullet rule only inspects single-span records** (seen in GOLD-B005-01). The generation self-review drops a candidate whose single span is a bare '- `field`: description' bullet, because its scope lives in the heading. B005-01 is two such bullets in a multi-span record, and the rule's `len(spans) == 1` guard let it through. Recorded rather than patched: batch 005's generation artifact is not being regenerated, and a fix belongs in batch 006's preregistration.
- **markdown reference links survive into questions built from conditional sentences** (seen in GOLD-B005-15). The link stripper runs on the composed question, but a reference-style link whose label is itself backticked was not matched. Repaired here by hand; the pattern should be fixed before batch 006.
- **prose mistaken for a section heading by the parser** (seen in GOLD-B005-11). section_path reads 'configured through AWS_REGION, AWS_DEFAULT_REGION, or your AWS profile.' No claim depends on it, and closed batches must not be touched, so this is recorded as a parser observation for a future audit.

## What this review did not do

- It did not approve anything. `human_verified` requires an owner decision.
- It did not rewrite the generation artifact; repairs live beside it with the original text and offsets preserved.
- It did not regenerate the batch, add a candidate, or search for new multi-hop chains.
- It did not run retrieval. SYSTEM-A and SYSTEM-B remain frozen and unexecuted, and the holdout is not frozen.
