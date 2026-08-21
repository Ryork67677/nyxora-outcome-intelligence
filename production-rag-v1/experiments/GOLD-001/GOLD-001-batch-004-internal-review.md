# GOLD-001 — batch 004 internal source-integrity review

**15 candidates reviewed against the frozen evidence · 10 repaired · reviewed 2026-08-21T16:41:19Z**

This is an internal review by the authoring model. It is not human verification, not an independent second opinion, and it changes no candidate's status: all 15 remain `candidate_unverified`, and the confirmed holdout-eligible count is still 53 from batches 001–003.

## Outcome

| status | candidates |
| --- | --- |
| NEEDS_REPAIR | 10 |
| READY_FOR_OWNER_REVIEW | 4 |
| REJECT_RECOMMENDED | 1 |

All 15 candidates were `precheck_holdout_ready` before this review, and all 15 still are. That is the point worth taking from the table: the structural precheck passed a candidate whose rule applies only on one experimental API surface, three questions broader than their evidence, four anchors whose scope lived in a section heading, and two critical strings that were 60-character truncations of a markdown link. A precheck cannot read.

| candidate | status | repaired | findings |
| --- | --- | --- | --- |
| `GOLD-B004-01` | NEEDS_REPAIR | yes | 2 |
| `GOLD-B004-02` | READY_FOR_OWNER_REVIEW | no | 1 |
| `GOLD-B004-03` | READY_FOR_OWNER_REVIEW | no | 0 |
| `GOLD-B004-04` | NEEDS_REPAIR | yes | 2 |
| `GOLD-B004-05` | READY_FOR_OWNER_REVIEW | no | 1 |
| `GOLD-B004-06` | NEEDS_REPAIR | yes | 3 |
| `GOLD-B004-07` | NEEDS_REPAIR | yes | 1 |
| `GOLD-B004-08` | REJECT_RECOMMENDED | no | 3 |
| `GOLD-B004-09` | NEEDS_REPAIR | yes | 2 |
| `GOLD-B004-10` | NEEDS_REPAIR | yes | 2 |
| `GOLD-B004-11` | NEEDS_REPAIR | yes | 2 |
| `GOLD-B004-12` | READY_FOR_OWNER_REVIEW | no | 1 |
| `GOLD-B004-13` | NEEDS_REPAIR | yes | 2 |
| `GOLD-B004-14` | NEEDS_REPAIR | yes | 2 |
| `GOLD-B004-15` | NEEDS_REPAIR | yes | 4 |

## The multi-hop case, reviewed semantically

§3 of the review brief: the mechanical PASS is not to be trusted on its own. The composition check proves that neither span carries the other hop's critical strings. It says nothing about whether the two documents mean the same thing by `needs_approval`, or whether span 1 establishes the state span 2 tests. Those are the questions below.

**A. Does span 1 establish the exact state tested by span 2?**

*Yes, and only after the repair.*

Span 2 tests `needs_approval` being not `False`. Span 1 sets it to `True`. The state span 1 establishes is a member of the set span 2 tests, so the chain closes. What span 1 does not establish — and what the unrepaired candidate silently assumed — is that span 2's rule applies at all. That scope now sits inside span 2's anchor.

**B. Does setting `needs_approval=True` satisfy '`needs_approval` is not `False`' without unsupported inference?**

*Yes.*

`True` is not `False` is an identity, not an inference about the API. Span 1 also documents a second permitted value — an async callable — and span 2's rule covers that too, since a callable is likewise not `False`. The composed claim is stated for `True` only, which is the narrower and therefore safer reading.

**C. Does span 1 come from the same SDK/tool concept as span 2?**

*Same SDK, different execution surface — and this was the defect.*

Both spans are openai-agents-python. Span 1 is the general human-in-the-loop page; span 2 is the hosted multi-agent (experimental) surface, where the SDK's approval interruption mechanism is not available. The setting is the same setting; the surfaces are not the same surface. As generated, the question was unqualified, which made the composed answer false in the ordinary Runner flow — where `needs_approval = True` does exactly what span 1 says and pauses for approval. The repair puts 'hosted agents' into both the question and the anchor.

**D. Are the two documents referring to compatible meanings of `needs_approval`?**

*Yes.*

Both refer to the per-tool `needs_approval` setting on a function tool, with the same value domain (`True`, `False`, or a callable). Span 2's phrase 'any function tool whose `needs_approval` setting' matches span 1's subject exactly. This is not the `max_tokens` equivocation found among the near-miss pairs, where one span meant a request parameter and the other a stop_reason value.

**E. Is neither span alone sufficient to answer the final question?**

*Yes — and span 1 alone is worse than insufficient.*

A reader holding only span 1 concludes the run pauses for approval, which is the opposite of the outcome on this surface. A reader holding only span 2 knows tools are rejected but not that `True` is the value a person would have set or what they were trying to achieve. This is the property batch 003's four candidates lacked: there, either span answered on its own.

**F. Does the composed answer follow directly?**

*Yes, once the scope is inside the evidence. No, as originally generated.*

Repaired, the chain is: on the hosted-agent surface (span 2), a function tool whose `needs_approval` is not `False` is rejected before the request is sent; `True` is such a value (span 1); therefore a tool set to `True` is rejected there. Every step is stated in the evidence and nothing is assumed. Unrepaired, step one required the unstated assumption that the reader was on the hosted-agent surface, which is precisely the 'unstated compatibility assumption' §3 says to mark NEEDS_REPAIR for.

**Verdict: NEEDS_REPAIR, repaired; genuine_multi_hop preserved.** Preserved: `reasoning_type` = `genuine_multi_hop`, `evidence_shape` = `multi_document`, `requires_all_evidence` = `True`.

### What the mechanical check still cannot see

The composition check tests textual overlap between each hop's critical strings and the other span. It cannot detect equivocation (one string naming two things), it cannot detect a scope carried by a heading, and it cannot tell whether span 1's state is the state span 2 tests. All three had to be judged by reading. A reviewer who disagrees with any of them should reject this candidate rather than trusting the PASS.

## Findings by candidate

### GOLD-B004-01 — NEEDS_REPAIR

- QUESTION_SCOPE: 'What happens when using server tools?' is far broader than its evidence. The span answers one conditional fact — what the API may return when the server-side sampling loop reaches its iteration limit — and a reader could give a dozen true answers to the question as asked.
- CATEGORY: the source states one direct conditional fact, not an interaction between two settings. §8 says relabel rather than inflate reasoning complexity.

**Repairs**

- `question` rewritten
- `answer` rewritten
- `reasoning_type` rewritten

### GOLD-B004-02 — READY_FOR_OWNER_REVIEW

- NONCRITICAL_ANAPHORA: the span says the API returns tool_use 'instead', and what it is instead of — the pause_turn behaviour — sits in the preceding paragraph, outside the span. The fact is answerable without resolving it, so this is noncritical, but §2B requires an explicit human override rather than a silent pass.

### GOLD-B004-03 — READY_FOR_OWNER_REVIEW

- No finding.

### GOLD-B004-04 — NEEDS_REPAIR

- CRITICAL_ANAPHORA: 'If generation then reaches the context window limit' — 'then' refers to the preceding sentence, which is outside the span.
- MODEL_SCOPE: the antecedent is 'On Claude 4.5 models and newer, if input tokens plus max_tokens exceeds the context window size, the API accepts the request.' The very next sentence in the source says earlier models return a validation error instead, so the claim as anchored over-generalises across models.

**Repairs**

- `E1` 48081–48225 → 47953–48225 (evidence_boundary_completion); hash `13f22cd01eea…` → `8eb88b1c77cc…`
- `question` rewritten
- `answer` rewritten
- `atomic_claims` rewritten

### GOLD-B004-05 — READY_FOR_OWNER_REVIEW

- NONCRITICAL_DEPENDENCY: 'more searches than allowed' does not name the parameter that sets the limit (`max_uses`), which is defined in the preceding sentence. The question is answerable without it, so the anchor stands; an owner who wants the parameter named should choose NEEDS_EDIT and the span can be extended backwards by 60 characters.

### GOLD-B004-06 — NEEDS_REPAIR

- CLAIM_SCOPE: the span is a bare definition bullet. The parent that gives `timezone` its meaning — the `user_location` parameter — is in the section heading and the list stem, both outside the span. §2D forbids relying on a header outside the exact evidence.
- GENERIC_IDENTIFIER: 'What is the `timezone` option?' names an identifier that exists in many APIs (§6).
- CRITICAL_STRING: one critical string was a 60-character truncation of a markdown link — 'The [IANA timezone ID](https://en.wikipedia.org/wiki/List_of' — which is not a meaningful checkable string.

**Repairs**

- `E1` 16744–16843 → 16295–16843 (evidence_scope_completion); hash `0bd723f53fa5…` → `b38e23b266e3…`
- `question` rewritten
- `answer` rewritten
- `atomic_claims` rewritten

### GOLD-B004-07 — NEEDS_REPAIR

- QUESTION_FORM: 'What happens if you need a hard ceiling on thinking costs?' asks what happens when a person has a requirement, which is not a behaviour the documentation can answer. The evidence states a support status, so the question should ask for one.

**Repairs**

- `question` rewritten
- `answer` rewritten

### GOLD-B004-08 — REJECT_RECOMMENDED

- NOT_AMBIGUITY: `type` on `ContentDeltaEvent` and `ContentDoneEvent` is a discriminator constant. A tagged union whose tag differs per member is not a case where a developer must select a scope to resolve a meaning — it is two literal lookups, and §7 says to relabel rather than keep the label to hit a category target.
- CLAIM_SCOPE: both spans are 27 and 26 characters and contain neither event-type name, so the question's scope lives entirely in headings outside the evidence (§2D). This part is repairable — expanding each span to its `#### EventName` heading costs only ~100 characters — but repairing the scope does not make the case a disambiguation.
- CEILING: relabelling to `exact_lookup` would take that category to 4 against the §5 maximum of 3.

### GOLD-B004-09 — NEEDS_REPAIR

- AMBIGUITY_CONFIRMED: `parsed_arguments` genuinely means different things on the two events — a partially parsed object mid-stream, a fully parsed object (a pydantic model instance where `openai.pydantic_function_tool()` was used) when complete. A developer holding one event and reading the other's documentation would be wrong, which is the realistic confusion §11 asks for.
- CLAIM_SCOPE: as anchored, neither span contains its event-type name, so the scope the question names is in a heading outside the evidence (§2D).

**Repairs**

- `E1` 6938–6997 → 6627–6997 (evidence_scope_completion); hash `a3608232ce72…` → `53b4b866ce9f…`
- `E2` 7362–7509 → 7072–7509 (evidence_scope_completion); hash `24e776c42e7a…` → `2c4842349ec2…`

### GOLD-B004-10 — NEEDS_REPAIR

- COMPARATIVE_ANAPHORA: 'a different `RealtimeModel`' is different from a default the span does not name. The default — `OpenAIRealtimeWebSocketModel` — is established in the preceding sentence, outside the anchor.
- CATEGORY: with the default inside the anchor this is a real configuration interaction (which transport model is used changes connection mechanics while leaving the session lifecycle alone), so the label stands once the scope does.

**Repairs**

- `E1` 1979–2121 → 1827–2121 (evidence_boundary_completion); hash `ad1950090760…` → `352fcab03e4b…`
- `question` rewritten
- `atomic_claims` rewritten

### GOLD-B004-11 — NEEDS_REPAIR

- QUESTION_SCOPE: 'What happens if a tool requires approval?' is generic across SDKs and run modes. The evidence is about a streamed run — it names `result.stream_events()` — so the question can carry that scope without adding anything the span does not say.
- CATEGORY: one direct conditional fact about run behaviour, not an interaction between two settings (§8).

**Repairs**

- `question` rewritten
- `reasoning_type` rewritten

### GOLD-B004-12 — READY_FOR_OWNER_REVIEW

- The question is long, because the source's condition has two parts and both matter. Shortening it would drop a condition the answer depends on, so it stands as written.

### GOLD-B004-13 — NEEDS_REPAIR

- GENERIC_IDENTIFIER: 'What is the `input_type` option?' does not say what it is an option of (§6). Unlike B004-06 and B004-14 the span itself says 'the handoff tool-call arguments', so the scope can be added to the question without touching the evidence.
- CRITICAL_STRING: one critical string was a 60-character truncation — 'The schema for the handoff tool-call arguments. When set, th'.

**Repairs**

- `question` rewritten

### GOLD-B004-14 — NEEDS_REPAIR

- CLAIM_SCOPE: the span reads '`input_filter`: This lets you filter the input received by the next agent.' and contains no mention of handoffs. The scope is entirely in the section heading and the list stem, both outside the evidence (§2D).
- REPAIR_SHAPE: a contiguous expansion back to the list stem would swallow five unrelated field definitions and produce a 976-character anchor. §16 asks for precise spans, so the stem is added as its own span instead.

**Repairs**

- `E0` scope span added at 1576–1654 (evidence_scope_completion); hash `6ed28e39bdd7…`
- `question` rewritten
- `answer` rewritten
- `atomic_claims` rewritten

### GOLD-B004-15 — NEEDS_REPAIR

- UNSUPPORTED_GENERALIZATION: span 2 comes from 'Models > OpenAI models > Hosted multi-agent (experimental) > Local function tools'. Its rejection rule holds on that surface, not in the ordinary Runner flow, where `needs_approval = True` correctly pauses for approval. The question as written is unqualified, so the composed answer is false in the default path.
- SCOPE_IN_HEADING: the qualification lives in the section heading, which §2D forbids relying on. It has to be inside the anchor or the case cannot carry it.
- MULTI_HOP_STANDS: with the scope inside span 2 the chain is real — see the semantic review in the internal review document.
- CLAIM_SET: the scope sentence 'All hosted agents share the model and tools configured for the request.' is inside the repaired span but is deliberately NOT an atomic claim. Quoting it would put 'the model' — whose antecedent is outside the span — into scored text, which turns a noncritical anaphora into a critical one. The span establishes the hosted-agent scope; the claims do not need to restate it.

**Repairs**

- `E2` 16756–16910 → 16313–16910 (evidence_scope_completion); hash `2f49ae6be39c…` → `b0ef211a15b2…`
- `question` rewritten
- `answer` rewritten
- `composed_claim` rewritten
- `composed_answer` rewritten
- `bridge_relationship` rewritten
- `why_span_1_alone_is_insufficient` rewritten
- `why_span_2_alone_is_insufficient` rewritten

## What this review did not do

- It did not approve anything. `human_verified` requires an owner decision, and the decisions file ships with every decision `null`.
- It did not rewrite the generation artifact. `gold_review_batch_004.json` is unchanged; repairs live in `gold_review_batch_004_repairs.json` with the original text and offsets preserved.
- It did not regenerate the batch, add a candidate, or promote a near-miss bridge pair.
- It did not run retrieval. SYSTEM-A and SYSTEM-B remain frozen and unexecuted, and the holdout is not frozen.
