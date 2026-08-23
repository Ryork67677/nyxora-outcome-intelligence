# GOLD-001 — batch 005 owner QC packet

**19 candidates · corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · prepared 2026-08-23T16:43:37Z**

Nothing in this packet is gold and nothing is verified. Every candidate is `candidate_unverified`, and no script in this repository can change that: `human_verified` exists only where the project owner records an approval.

## Internal authoring review is not independent verification

The statuses below were produced by the authoring model reading its own output against the frozen evidence. That is a self-check. It is not a second opinion from an independent party, it is not verification, and it confers no status on any candidate. A `READY_FOR_OWNER_REVIEW` label means the author found nothing wrong — which is exactly the claim an independent reviewer is there to test.

## What the three states mean

| state | who decides | what it means |
| --- | --- | --- |
| `precheck_holdout_ready` | a script | the record is structurally checkable — hashes, offsets, critical strings inside their own spans, no critical anaphora, no oversized anchor |
| `human_verified` | the project owner | a person read the evidence and approved the case |
| `holdout_eligible` | derived | `human_verified` **and** deterministic claim support **and** valid evidence **and** no unresolved blocker |

19 of 19 candidates are `precheck_holdout_ready`. That is not an argument for approving them: the review below recommends 4 for rejection and repaired 7, and every one of those was precheck-ready before the review looked at it.

## Internal review outcome

| status | candidates |
| --- | --- |
| READY_FOR_OWNER_REVIEW | 8 |
| NEEDS_REPAIR | 7 |
| REJECT_RECOMMENDED | 4 |

| id | provider | reasoning type | shape | internal status | repaired |
| --- | --- | --- | --- | --- | --- |
| `01` | anthropic | `ambiguity_disambiguation` | multi_document | REJECT_RECOMMENDED | no |
| `02` | anthropic | `configuration_interaction` | single_span | READY_FOR_OWNER_REVIEW | no |
| `03` | anthropic | `error_behavior` | single_span | READY_FOR_OWNER_REVIEW | no |
| `04` | anthropic | `error_behavior` | single_span | READY_FOR_OWNER_REVIEW | no |
| `05` | anthropic | `exact_lookup` | single_span | NEEDS_REPAIR | yes |
| `06` | anthropic | `lifecycle_compatibility_migration` | single_span | REJECT_RECOMMENDED | no |
| `07` | anthropic | `lifecycle_compatibility_migration` | single_span | READY_FOR_OWNER_REVIEW | no |
| `08` | anthropic | `lifecycle_compatibility_migration` | single_span | NEEDS_REPAIR | yes |
| `09` | openai | `error_behavior` | single_span | NEEDS_REPAIR | yes |
| `10` | openai | `configuration_interaction` | single_span | REJECT_RECOMMENDED | no |
| `11` | openai | `configuration_interaction` | single_span | NEEDS_REPAIR | yes |
| `12` | openai | `configuration_interaction` | single_span | READY_FOR_OWNER_REVIEW | no |
| `13` | openai | `configuration_interaction` | single_span | REJECT_RECOMMENDED | no |
| `14` | openai | `configuration_interaction` | single_span | READY_FOR_OWNER_REVIEW | no |
| `15` | openai | `configuration_interaction` | single_span | NEEDS_REPAIR | yes |
| `16` | openai | `configuration_interaction` | single_span | NEEDS_REPAIR | yes |
| `17` | openai | `error_behavior` | single_span | READY_FOR_OWNER_REVIEW | no |
| `18` | openai | `exact_lookup` | single_span | NEEDS_REPAIR | yes |
| `19` | openai | `lifecycle_compatibility_migration` | single_span | READY_FOR_OWNER_REVIEW | no |

---

## GOLD-B005-01

- **provider**: anthropic
- **document**: Web fetch tool
- **section**: Response › Errors
- **reasoning type**: `ambiguity_disambiguation`
- **evidence shape**: `multi_document` · **requires all evidence**: True
- **internal review status**: **REJECT_RECOMMENDED**
- **precheck**: holdout-ready = True

### Final question

In Web fetch tool, what does the `invalid_tool_input` field mean, and how does that differ from Tool search tool?

### Final answer

In Web fetch tool, `invalid_tool_input` is: Invalid tool input, such as a malformed URL or a non-HTTP(S) scheme. In Tool search tool, `invalid_tool_input` is: the search input was invalid, for example a malformed regex pattern or a pattern over the 200-character limit.

### Final atomic claims

1. In Web fetch tool, `invalid_tool_input` is: Invalid tool input, such as a malformed URL or a non-HTTP(S) scheme.
2. In Tool search tool, `invalid_tool_input` is: the search input was invalid, for example a malformed regex pattern or a pattern over the 200-character limit.

### Exact evidence

**E1** · `ver_901356d3ffce0f0478ba2d33aefdf98a` 22545–22636 (91 chars) · Response › Errors

```
* `invalid_tool_input`: Invalid tool input, such as a malformed URL or a non-HTTP(S) scheme
```
**critical strings**: `invalid_tool_input`
**evidence_hash**: `ee532724156923f6591fd9e72285493442b2e0e15541ce46c2f879c5ba54458c`

**E2** · `ver_b7ea8359f97ca269418988f78e80b870` 28727–28860 (133 chars) · Error handling › Tool result errors (200 status)

```
* `invalid_tool_input`: the search input was invalid, for example a malformed regex pattern or a pattern over the 200-character limit
```
**critical strings**: `invalid_tool_input`
**evidence_hash**: `caf2d8758e197a6698a3f58e49adee4ccdf7bd10082018815144c119cc72ffb3`

### Claim → evidence

1. In Web fetch tool, `invalid_tool_input` is: Invalid tool input, such as a malformed URL or… → `E1`
2. In Tool search tool, `invalid_tool_input` is: the search input was invalid, for example a … → `E2`

### Internal review findings

- NOT_A_FIELD: `invalid_tool_input` is a value of the `error_code` field, not a field. The question's noun is wrong before anything else is considered.
- NOT_AMBIGUITY: the two readings are the same concept — 'the input you gave this tool was invalid' — with tool-specific examples (a malformed URL for web fetch, a malformed regex or an over-length pattern for tool search). §12 asks for a term whose semantics differ by scope; an error code whose examples differ by tool is one meaning documented twice.
- SCOPE_IN_HEADING: neither span mentions its tool. E1 reads '* `invalid_tool_input`: Invalid tool input, such as a malformed URL…' and E2 '* `invalid_tool_input`: the search input was invalid…'; 'Web fetch tool' and 'Tool search tool' come from the document titles. This is the bare-definition-bullet defect the generator drops elsewhere — it did not fire here because the rule only inspects single-span records, which is a generator bug recorded below.
- §3 is explicit that ambiguity must not be preserved because the batch has only one such case.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

The review recommends rejecting this candidate. That recommendation is not a decision and does not bind you.

---

## GOLD-B005-02

- **provider**: anthropic
- **document**: Admin
- **section**: Federation Issuers › Create Federation Issuer
- **reasoning type**: `configuration_interaction`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **READY_FOR_OWNER_REVIEW**
- **precheck**: holdout-ready = True

### Final question

What happens when `jwks.type` is `discovery` and no `discovery_base` is set?

### Final answer

The issuer URL must be publicly reachable over HTTPS so Anthropic can fetch the discovery document; for `explicit_url` and `inline` modes the issuer URL is only matched as the JWT's `iss` claim and is not fetched.

### Final atomic claims

1. When `jwks.type` is `discovery` and no `discovery_base` is set, the issuer URL must be publicly reachable over HTTPS so Anthropic can fetch the discovery document; for `explicit_url` and `inline` modes the issuer URL is only matched as the JWT's `iss` claim and is not fetched.

### Interaction recorded

- **A**: `jwks.type` set to `discovery`
- **B**: `discovery_base` absent
- **relation**: with A selected and B unset, the issuer URL must be publicly reachable over HTTPS so the discovery document can be fetched; under `explicit_url` and `inline` the URL is matched as the `iss` claim and never fetched

### Exact evidence

**E1** · `ver_c299b58fe1f5a4d3a081b550334a7df6` 469462–469739 (277 chars) · Federation Issuers › Create Federation Issuer

```
When `jwks.type` is
`discovery` and no `discovery_base` is set, the issuer URL must be
publicly reachable over HTTPS so Anthropic can fetch the discovery
document; for `explicit_url` and `inline` modes the issuer URL is only
matched as the JWT's `iss` claim and is not fetched.
```
**critical strings**: `jwks.type`, `discovery`, `discovery_base`
**evidence_hash**: `a2602d47d43f5d8dd96abef379a50a1cfd6144349d27e7082f1ae8a69862d873`

### Claim → evidence

1. When `jwks.type` is `discovery` and no `discovery_base` is set, the issuer URL must be pub… → `E1`

### Internal review findings

- The anchor carries all three parts §5 asks for: `jwks.type` is `discovery`, no `discovery_base` is set, and the resulting requirement. No boundary repair is needed.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

---

## GOLD-B005-03

- **provider**: anthropic
- **document**: Beta
- **section**: Deployment Runs › List Deployment Runs › Query Parameters
- **reasoning type**: `error_behavior`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **READY_FOR_OWNER_REVIEW**
- **precheck**: holdout-ready = True

### Final question

What happens when filtering by a non-existent deployment_id?

### Final answer

It returns 200 with empty data.

### Final atomic claims

1. Filtering by a non-existent deployment_id returns 200 with empty data.

### Exact evidence

**E1** · `ver_de7f74230c8f10d30aea5d037a3bd0a5` 2711799–2711869 (70 chars) · Deployment Runs › List Deployment Runs › Query Parameters

```
Filtering by a non-existent deployment_id returns 200 with empty data.
```
**critical strings**: `200 with empty data`
**evidence_hash**: `892ee8dfcbdd186e6454dbbed9e5f70ba5c5f353b262c62c1749656a6d93bd63`

### Claim → evidence

1. Filtering by a non-existent deployment_id returns 200 with empty data. → `E1`

### Internal review findings

- Condition and result are both inside the anchor, as §6 requires.
- NONCRITICAL_SCOPE: the span does not name the endpoint whose list behaviour this is. The question is answerable without it, so the anchor stands; an owner who wants the endpoint named should choose NEEDS_EDIT.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

---

## GOLD-B005-04

- **provider**: anthropic
- **document**: Web search tool
- **section**: Response › Search results
- **reasoning type**: `error_behavior`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **READY_FOR_OWNER_REVIEW**
- **precheck**: holdout-ready = True

### Final question

What happens if `encrypted_content` is missing or modified?

### Final answer

The request fails with a 400 validation error.

### Final atomic claims

1. If `encrypted_content` is missing or modified, the request fails with a 400 validation error.

### Exact evidence

**E1** · `ver_53da2f78e855c75ec755089c13d44c28` 20614–20707 (93 chars) · Response › Search results

```
If `encrypted_content` is missing or modified, the request fails with a 400 validation error.
```
**critical strings**: `encrypted_content`
**evidence_hash**: `bf645608c00bf09471aa9890464ff50f4ed0500135209a9ceab88a6e0b9d29db`

### Claim → evidence

1. If `encrypted_content` is missing or modified, the request fails with a 400 validation err… → `E1`

### Internal review findings

- Condition and result are both inside the anchor.
- NONCRITICAL_SCOPE: the span does not say that `encrypted_content` belongs to the web search tool's results. The fact is answerable as asked.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

---

## GOLD-B005-05

- **provider**: anthropic
- **document**: Server tools
- **section**: Domain filtering
- **reasoning type**: `exact_lookup`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

What constraint does a request-level `allowed_domains` list have to satisfy?

### Final answer

Request-level `allowed_domains` must be a subset of the organization-level allowed list; entries outside it cause the API to return a validation error.

### Final atomic claims

1. Request-level `allowed_domains` must be a subset of the organization-level allowed list; entries outside it cause the API to return a validation error.

### Exact evidence

**E1** · `ver_8d2a22e3827c98e0b9d4e1ef411e5353` 40135–40286 (151 chars) · Domain filtering

```
Request-level `allowed_domains` must be a subset of the organization-level allowed list; entries outside it cause the API to return a validation error.
```
**critical strings**: `allowed_domains`
**evidence_hash**: `e46486f298067b5585bf926b4dffbf606adc0fabe989a04f569377183b1da3a5`

### Claim → evidence

1. Request-level `allowed_domains` must be a subset of the organization-level allowed list; e… → `E1`

### Internal review findings

- QUESTION_SCOPE: 'What must `allowed_domains` be?' drops the qualifier the evidence itself supplies. The span constrains a *request-level* `allowed_domains` list relative to the organization-level list; asked unscoped, the question implies a rule about the parameter in general.
- The scope word is inside the anchor, so this is a question repair and the evidence does not move.

### Repairs made

- **question rewritten** (question_scope_completion using the source's own term 'request-level')
  - was: What must `allowed_domains` be?
  - now: What constraint does a request-level `allowed_domains` list have to satisfy?

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `e46486f298067b5585bf926b4dffbf606adc0fabe989a04f569377183b1da3a5`.

---

## GOLD-B005-06

- **provider**: anthropic
- **document**: Beta
- **section**: Models › List Models › Returns
- **reasoning type**: `lifecycle_compatibility_migration`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **REJECT_RECOMMENDED**
- **precheck**: holdout-ready = True

### Final question

Where is `fallbacks` supported?

### Final answer

Model IDs this model accepts as `fallbacks[i].model` on the Messages API. An empty list means the `fallbacks` parameter is not supported for this model as primary.

### Final atomic claims

1. Model IDs this model accepts as `fallbacks[i].model` on the Messages API. An empty list means the `fallbacks` parameter is not supported for this model as primary.

### Exact evidence

**E1** · `ver_de7f74230c8f10d30aea5d037a3bd0a5` 8864–9027 (163 chars) · Models › List Models › Returns

```
Model IDs this model accepts as `fallbacks[i].model` on the Messages API. An empty list means the `fallbacks` parameter is not supported for this model as primary.
```
**critical strings**: `fallbacks`
**evidence_hash**: `0233ca0ebe16c41bd827639d7138b79a98ca3cc5b357e7d6d75bd908bbe774ca`

### Claim → evidence

1. Model IDs this model accepts as `fallbacks[i].model` on the Messages API. An empty list me… → `E1`

### Internal review findings

- NOT_A_LIFECYCLE_STATEMENT: the span is a schema field description from a List Models response — 'Model IDs this model accepts as `fallbacks[i].model` on the Messages API' — not a statement about support status. It was mined as lifecycle because its second sentence contains 'not supported'.
- UNANSWERABLE_AS_ASKED: 'Where is `fallbacks` supported?' asks for a set of models. The span says only that an empty list means the parameter is unsupported for that model as primary, which does not answer it.
- A repair would have to rewrite the question into a different fact; the honest outcome is rejection.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

The review recommends rejecting this candidate. That recommendation is not a decision and does not bind you.

---

## GOLD-B005-07

- **provider**: anthropic
- **document**: Context editing
- **section**: Client-side compaction (SDK)
- **reasoning type**: `lifecycle_compatibility_migration`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **READY_FOR_OWNER_REVIEW**
- **precheck**: holdout-ready = True

### Final question

Is `compaction_control` still supported?

### Final answer

The `compaction_control` parameter is deprecated in the Python, TypeScript, and Ruby SDKs and will be removed in a future version.

### Final atomic claims

1. The `compaction_control` parameter is deprecated in the Python, TypeScript, and Ruby SDKs and will be removed in a future version.

### Exact evidence

**E1** · `ver_1c53b961e1f5da8124a1e7e8eb92c941` 75250–75380 (130 chars) · Client-side compaction (SDK)

```
The `compaction_control` parameter is deprecated in the Python, TypeScript, and Ruby SDKs and will be removed in a future version.
```
**critical strings**: `compaction_control`
**evidence_hash**: `b2f29d24dba4045e411f87f438b77bc9271fe24588f500c999d148195d44736a`

### Claim → evidence

1. The `compaction_control` parameter is deprecated in the Python, TypeScript, and Ruby SDKs … → `E1`

### Internal review findings

- Self-contained: names the parameter, the three SDKs, the deprecation, and the future removal. Narrowest accurate type is deprecation, which is what the secondary category records.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

---

## GOLD-B005-08

- **provider**: anthropic
- **document**: Prompting Claude Sonnet 5
- **section**: Calibrating effort and thinking depth
- **reasoning type**: `lifecycle_compatibility_migration`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

Is manual extended thinking with `budget_tokens` supported on Claude Sonnet 5?

### Final answer

Manual extended thinking (`thinking: {type: "enabled", budget_tokens: N}`) is not supported on Claude Sonnet 5 and returns a 400 error.

### Final atomic claims

1. Manual extended thinking (`thinking: {type: "enabled", budget_tokens: N}`) is not supported on Claude Sonnet 5 and returns a 400 error.

### Exact evidence

**E1** · `ver_9c5166b670bf43589ee63d0dbe8b93d2` 5356–5491 (135 chars) · Calibrating effort and thinking depth

```
Manual extended thinking (`thinking: {type: "enabled", budget_tokens: N}`) is not supported on Claude Sonnet 5 and returns a 400 error.
```
**critical strings**: `budget_tokens`
**evidence_hash**: `58fbedd718a3c5c6487312de617ed46995249883d398207176d61663dda9dbbe`

### Claim → evidence

1. Manual extended thinking (`thinking: {type: "enabled", budget_tokens: N}`) is not supporte… → `E1`

### Internal review findings

- QUESTION_FORM: 'Where is `budget_tokens` supported?' asks for the set of places it works. The evidence states one place it does not — manual extended thinking is not supported on Claude Sonnet 5 and returns a 400. A question asking for the positive set cannot be answered from a single negative.
- The model scope is inside the anchor, so only the question changes.

### Repairs made

- **question rewritten** (question_form_correction: ask what the evidence answers)
  - was: Where is `budget_tokens` supported?
  - now: Is manual extended thinking with `budget_tokens` supported on Claude Sonnet 5?

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `58fbedd718a3c5c6487312de617ed46995249883d398207176d61663dda9dbbe`.

---

## GOLD-B005-09

- **provider**: openai
- **document**: Human-in-the-loop
- **section**: Human-in-the-loop › Marking tools that need approval
- **reasoning type**: `error_behavior` (generated as `configuration_interaction`)
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

What happens if the arguments are malformed JSON, are valid JSON but not an object (for example, `null` or a list), or contain non-standard constants such as `NaN`, `Infinity`, or `-Infinity`?

### Final answer

The callable is not invoked and the call requires manual approval.

### Final atomic claims

1. Callable approval rules fail closed when the SDK cannot safely inspect the arguments.
2. If the arguments are malformed JSON, are valid JSON but not an object (for example, `null` or a list), or contain non-standard constants such as `NaN`, `Infinity`, or `-Infinity`, the callable is not invoked and the call requires manual approval.

### Exact evidence

**E1** · `ver_ae3bfcc42c733c5051abda30f0f6db07` 1523–1855 (332 chars) · Human-in-the-loop › Marking tools that need approval

```
Callable approval rules fail closed when the SDK cannot safely inspect the arguments. If the arguments are malformed JSON, are valid JSON but not an object (for example, `null` or a list), or contain non-standard constants such as `NaN`, `Infinity`, or `-Infinity`, the callable is not invoked and the call requires manual approval.
```
**critical strings**: `Callable approval rules fail closed`, `NaN`, `manual approval`
**evidence_hash**: `d4a15c400fe14c77b39eb20fda908baeb1827d2ae89d4610af0994eee5b6fe7d`

### Claim → evidence

1. Callable approval rules fail closed when the SDK cannot safely inspect the arguments. → `E1`
2. If the arguments are malformed JSON, are valid JSON but not an object (for example, `null`… → `E1`

### Internal review findings

- §9 satisfied on the conditions: all three — malformed JSON, valid JSON that is not an object, and non-standard constants — are disjuncts of a single conditional with one stated result, so nothing needs splitting or narrowing.
- CATEGORY: labelled configuration_interaction, but §4's three fields cannot be filled. The critical strings are `null`, `NaN` and `Infinity`, which are values rather than settings, and no second setting interacts with a first. Relabelled to error_behavior.
- CRITICAL_ANAPHORA: the answer's subject is 'the callable', whose antecedent — 'Callable approval rules fail closed when the SDK cannot safely inspect the arguments' — sits immediately before the anchor. Without it a reader cannot tell which callable is not invoked.

### Repairs made

- **E1 anchor extended** (evidence_boundary_completion)
  - was 1609–1855, hash `25ef4cc6cccc83ff…`
  - now 1523–1855, hash `d4a15c400fe14c77…`
- **atomic_claims rewritten** (evidence_boundary_completion and taxonomy correction; the antecedent of 'the callable' must be inside the anchor)
  - was: ['If the arguments are malformed JSON, are valid JSON but not an object (for example, `null` or a list), or contain non-standard constants such as `NaN`, `Infinity`, or `-Infinity`, the callable is not invoked and the call requires manual approval.']
  - now: ['Callable approval rules fail closed when the SDK cannot safely inspect the arguments.', 'If the arguments are malformed JSON, are valid JSON but not an object (for example, `null` or a list), or contain non-standard constants such as `NaN`, `Infinity`, or `-Infinity`, the callable is not invoked and the call requires manual approval.']
- **reasoning_type rewritten** (evidence_boundary_completion and taxonomy correction; the antecedent of 'the callable' must be inside the anchor)
  - was: configuration_interaction
  - now: error_behavior
- **secondary_category rewritten** (evidence_boundary_completion and taxonomy correction; the antecedent of 'the callable' must be inside the anchor)
  - was: conditional_behavior
  - now: fail_closed_behavior

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `d4a15c400fe14c77b39eb20fda908baeb1827d2ae89d4610af0994eee5b6fe7d`.

---

## GOLD-B005-10

- **provider**: openai
- **document**: Models
- **section**: Models › OpenAI models › Hosted multi-agent (experimental) › Current limitations
- **reasoning type**: `configuration_interaction`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **REJECT_RECOMMENDED**
- **precheck**: holdout-ready = True

### Final question

What does `betas` override?

### Final answer

The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.

### Final atomic claims

1. The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.

### Exact evidence

**E1** · `ver_ae909bf8b4bbbe1d1a11119447f7ac94` 19331–19456 (125 chars) · Models › OpenAI models › Hosted multi-agent (experimental) › Current limitations

```
The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.
```
**critical strings**: `betas`, `reasoning.summary`, `max_tool_calls`
**evidence_hash**: `540a39028df8184945b1d598976982b6092e1c52dbb919d3c009f6d5df2ccad0`

### Claim → evidence

1. The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied … → `E1`

### Internal review findings

- RELATION_DIRECTION: §10's suspicion is confirmed. The source says 'The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.' `betas` is the object of the rejection, not the subject of an override. The question asks what `betas` overrides, which the source never says.
- SCOPE_IN_HEADING: rewriting around the true subject would make the question about 'the experimental model', which the span identifies only by that phrase. The model's name sits in the section heading and, further down, after the span. There is no minimal outward expansion that brings the identity inside the anchor.
- Both defects would have to be repaired at once, and the second has no honest repair, so the candidate is recommended for rejection rather than rewritten.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

The review recommends rejecting this candidate. That recommendation is not a decision and does not bind you.

---

## GOLD-B005-11

- **provider**: openai
- **document**: OpenAI Python API library
- **section**: configured through AWS_REGION, AWS_DEFAULT_REGION, or your AWS profile.
- **reasoning type**: `configuration_interaction`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

When using the `bedrock(...)` provider, what does setting `AWS_BEDROCK_BASE_URL` change?

### Final answer

Pass `base_url` to `bedrock(...)` or set `AWS_BEDROCK_BASE_URL` to override the derived `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint.

### Final atomic claims

1. Pass `base_url` to `bedrock(...)` or set `AWS_BEDROCK_BASE_URL` to override the derived `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint.

### Interaction recorded

- **A**: `AWS_BEDROCK_BASE_URL`, or `base_url` passed to `bedrock(...)`
- **B**: the endpoint derived from the configured AWS region
- **relation**: A overrides B

### Exact evidence

**E1** · `ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` 33783–33932 (149 chars) · configured through AWS_REGION, AWS_DEFAULT_REGION, or your AWS profile.

```
Pass `base_url` to `bedrock(...)` or set `AWS_BEDROCK_BASE_URL` to override the derived `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint.
```
**critical strings**: `AWS_BEDROCK_BASE_URL`, `base_url`
**evidence_hash**: `d48685e50739421736a63a780d66187b87e069d5b77514a0efa840fb92b35f55`

### Claim → evidence

1. Pass `base_url` to `bedrock(...)` or set `AWS_BEDROCK_BASE_URL` to override the derived `h… → `E1`

### Internal review findings

- DIRECTION_CORRECT: unlike B005-10 the source does put the environment variable on the acting side — 'set `AWS_BEDROCK_BASE_URL` to override the derived … endpoint'.
- MISSING_CONDITION: §11's warning applies. What is overridden is the endpoint *derived* from the region configuration, and the span says so; the question as asked implies an unconditional override. The provider that derives it, `bedrock(...)`, is named in the span.
- SECTION_PATH_ARTEFACT: the record's section_path is 'configured through AWS_REGION, AWS_DEFAULT_REGION, or your AWS profile.', which is prose the parser mistook for a heading. It is metadata only — no claim rests on it — but a reviewer should not read it as a real section.

### Repairs made

- **question rewritten** (question_scope_completion: name the provider and the derived endpoint the override replaces)
  - was: What does `AWS_BEDROCK_BASE_URL` override?
  - now: When using the `bedrock(...)` provider, what does setting `AWS_BEDROCK_BASE_URL` change?

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `d48685e50739421736a63a780d66187b87e069d5b77514a0efa840fb92b35f55`.

---

## GOLD-B005-12

- **provider**: openai
- **document**: Sandbox clients
- **section**: Sandbox clients › Supported hosted platforms › Size Modal sandboxes
- **reasoning type**: `configuration_interaction`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **READY_FOR_OWNER_REVIEW**
- **precheck**: holdout-ready = True

### Final question

What does `FuseMountPattern` require?

### Final answer

`FuseMountPattern` requires broad acknowledgement because `blobfuse2` discovers ambient Azure authority, even when no inline credential is configured.

### Final atomic claims

1. `FuseMountPattern` requires broad acknowledgement because `blobfuse2` discovers ambient Azure authority, even when no inline credential is configured.

### Interaction recorded

- **A**: `FuseMountPattern`
- **B**: broad acknowledgement of the authority exposure
- **relation**: A requires B, because `blobfuse2` discovers ambient Azure authority even with no inline credential

### Exact evidence

**E1** · `ver_3d4b8881962381cbfba18ade50c598e1` 11024–11174 (150 chars) · Sandbox clients › Supported hosted platforms › Size Modal sandboxes

```
`FuseMountPattern` requires broad acknowledgement because `blobfuse2` discovers ambient Azure authority, even when no inline credential is configured.
```
**critical strings**: `FuseMountPattern`, `blobfuse2`
**evidence_hash**: `6d34d63eb16fc99d04e20f8b9f024eff75fe086315cadca54dc94b3b88878a73`

### Claim → evidence

1. `FuseMountPattern` requires broad acknowledgement because `blobfuse2` discovers ambient Az… → `E1`

### Internal review findings

- §12 satisfied: `FuseMountPattern` is the grammatical subject of the requirement, the span states a requirement rather than a definition, and the reason — `blobfuse2` discovering ambient Azure authority — is inside the anchor.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

---

## GOLD-B005-13

- **provider**: openai
- **document**: Sandbox clients
- **section**: Sandbox clients › Supported hosted platforms › Size Modal sandboxes
- **reasoning type**: `configuration_interaction`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **REJECT_RECOMMENDED**
- **precheck**: holdout-ready = True

### Final question

What does `S3FilesMountPattern` require?

### Final answer

`S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses ambient IAM authority.

### Final atomic claims

1. `S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses ambient IAM authority.

### Exact evidence

**E1** · `ver_3d4b8881962381cbfba18ade50c598e1` 11175–11288 (113 chars) · Sandbox clients › Supported hosted platforms › Size Modal sandboxes

```
`S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses ambient IAM authority.
```
**critical strings**: `S3FilesMountPattern`, `mount.s3files`
**evidence_hash**: `b7cd45d15c27feeafd00ab13cda6f7664f164f3864fb5a9e0cb377e4f5f58c95`

### Claim → evidence

1. `S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses… → `E1`

### Internal review findings

- DUPLICATE_RELATION: this is the sentence immediately after B005-12's, stating the same relation about a sibling mount pattern. §26 rejects 'the same configuration relation reworded', and two adjacent sentences from one paragraph are not two facts worth two benchmark cases.
- ANAPHORA: the span opens '`S3FilesMountPattern` likewise requires…', and 'likewise' refers to the FuseMountPattern sentence outside the anchor. The requirement is stated in full regardless, so this is noncritical — but combined with the duplication there is no reason to keep it.
- Keeping B005-12 and dropping this one is the choice; they are interchangeable.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

The review recommends rejecting this candidate. That recommendation is not a decision and does not bind you.

---

## GOLD-B005-14

- **provider**: openai
- **document**: Tools
- **section**: Tools › Local runtime tools
- **reasoning type**: `configuration_interaction`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **READY_FOR_OWNER_REVIEW**
- **precheck**: holdout-ready = True

### Final question

What does `ApplyPatchTool` require?

### Final answer

`ComputerTool` and `ApplyPatchTool` always require local implementations that you provide.

### Final atomic claims

1. `ComputerTool` and `ApplyPatchTool` always require local implementations that you provide.

### Interaction recorded

- **A**: `ComputerTool` and `ApplyPatchTool`
- **B**: a local implementation supplied by the application
- **relation**: A always requires B

### Exact evidence

**E1** · `ver_cbeb36b7cf9a5e241940a011629b6f1b` 14491–14581 (90 chars) · Tools › Local runtime tools

```
`ComputerTool` and `ApplyPatchTool` always require local implementations that you provide.
```
**critical strings**: `ApplyPatchTool`, `ComputerTool`
**evidence_hash**: `b99555629d4f3bc24af3d059ad3a0b08f1eb616106369557e8228d4a115359fc`

### Claim → evidence

1. `ComputerTool` and `ApplyPatchTool` always require local implementations that you provide. → `E1`

### Internal review findings

- §12 satisfied: `ApplyPatchTool` is a subject of the requirement (compound with `ComputerTool`), the span states a requirement, and 'local implementations that you provide' is operationally meaningful.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

---

## GOLD-B005-15

- **provider**: openai
- **document**: Tools
- **section**: Tools › Local runtime tools › ComputerTool and the Responses computer tool
- **reasoning type**: `configuration_interaction`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

When a `ComputerTool` is present, how are `tool_choice="computer"`, `"computer_use"` and `"computer_use_preview"` treated?

### Final answer

All three are accepted and normalized to the built-in selector that matches the effective request model.

### Final atomic claims

1. When a [`ComputerTool`][agents.tool.ComputerTool] is present, `tool_choice="computer"`, `"computer_use"`, and `"computer_use_preview"` are all accepted and normalized to the built-in selector that matches the effective request model.

### Interaction recorded

- **A**: the presence of a `ComputerTool`
- **B**: the `tool_choice` value
- **relation**: A changes how B is interpreted: three otherwise-distinct strings are normalised to one built-in selector

### Exact evidence

**E1** · `ver_cbeb36b7cf9a5e241940a011629b6f1b` 17432–17665 (233 chars) · Tools › Local runtime tools › ComputerTool and the Responses computer tool

```
When a [`ComputerTool`][agents.tool.ComputerTool] is present, `tool_choice="computer"`, `"computer_use"`, and `"computer_use_preview"` are all accepted and normalized to the built-in selector that matches the effective request model.
```
**critical strings**: `ComputerTool`, `tool_choice="computer"`, `"computer_use"`, `"computer_use_preview"`
**evidence_hash**: `821cedbcd91b12d3dda4b832920ad3cc5756f02525eb06a621776aa1d97b85c7`

### Claim → evidence

1. When a [`ComputerTool`][agents.tool.ComputerTool] is present, `tool_choice="computer"`, `"… → `E1`

### Internal review findings

- QUESTION_BREADTH: §13's concern. 'What happens when a `ComputerTool` is present?' invites any consequence; the span supports exactly one — three `tool_choice` strings are accepted and normalised to the selector matching the effective model.
- LINK_MARKUP: the question carries a raw markdown reference, '[`ComputerTool`][agents.tool.ComputerTool]', which the generator's link stripper did not reach. A question is not a place for documentation plumbing.

### Repairs made

- **question rewritten** (question_narrowing to the single documented consequence, and link markup removed)
  - was: What happens when a [`ComputerTool`][agents.tool.ComputerTool] is present?
  - now: When a `ComputerTool` is present, how are `tool_choice="computer"`, `"computer_use"` and `"computer_use_preview"` treated?
- **answer rewritten** (question_narrowing to the single documented consequence, and link markup removed)
  - was: `tool_choice="computer"`, `"computer_use"`, and `"computer_use_preview"` are all accepted and normalized to the built-in selector that matches the effective request model.
  - now: All three are accepted and normalized to the built-in selector that matches the effective request model.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `821cedbcd91b12d3dda4b832920ad3cc5756f02525eb06a621776aa1d97b85c7`.

---

## GOLD-B005-16

- **provider**: openai
- **document**: Usage
- **section**: Usage › Accessing usage with sessions
- **reasoning type**: `configuration_interaction`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

When you use a `Session` such as `SQLiteSession`, what usage does each call to `Runner.run(...)` return?

### Final answer

Usage for that specific run.

### Final atomic claims

1. When you use a `Session` (e.g., `SQLiteSession`), each call to `Runner.run(...)` returns usage for that specific run.

### Interaction recorded

- **A**: using a `Session` (for example `SQLiteSession`)
- **B**: the usage returned by each `Runner.run(...)` call
- **relation**: A scopes B to the individual run rather than to the accumulated session

### Exact evidence

**E1** · `ver_f8002fe268b970eaea8d640f9dd91fb3` 4684–4801 (117 chars) · Usage › Accessing usage with sessions

```
When you use a `Session` (e.g., `SQLiteSession`), each call to `Runner.run(...)` returns usage for that specific run.
```
**critical strings**: `Session`, `SQLiteSession`
**evidence_hash**: `40b53a39a3051bb1c73d88719255085ef89a539e53d19db5f6c5e7303eb61dcb`

### Claim → evidence

1. When you use a `Session` (e.g., `SQLiteSession`), each call to `Runner.run(...)` returns u… → `E1`

### Internal review findings

- QUESTION_BREADTH: §14's concern. 'What happens when you use a `Session`?' is broader than the span, which establishes one specific effect on usage accounting.
- The condition is preserved in the rewrite; only the consequence being asked about is named.

### Repairs made

- **question rewritten** (question_narrowing to the documented effect)
  - was: What happens when you use a `Session` (e.g., `SQLiteSession`)?
  - now: When you use a `Session` such as `SQLiteSession`, what usage does each call to `Runner.run(...)` return?
- **answer rewritten** (question_narrowing to the documented effect)
  - was: Each call to `Runner.run(...)` returns usage for that specific run.
  - now: Usage for that specific run.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `40b53a39a3051bb1c73d88719255085ef89a539e53d19db5f6c5e7303eb61dcb`.

---

## GOLD-B005-17

- **provider**: openai
- **document**: Running agents
- **section**: Running agents › Runner lifecycle and configuration › The agent loop
- **reasoning type**: `error_behavior`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **READY_FOR_OWNER_REVIEW**
- **precheck**: holdout-ready = True

### Final question

What happens if we exceed the `max_turns` passed?

### Final answer

We raise a `MaxTurnsExceeded` exception.

### Final atomic claims

1. If we exceed the `max_turns` passed, we raise a [`MaxTurnsExceeded`][agents.exceptions.MaxTurnsExceeded] exception.

### Exact evidence

**E1** · `ver_2c60e99cfd929a738910b893fd6f1a40` 1936–2051 (115 chars) · Running agents › Runner lifecycle and configuration › The agent loop

```
If we exceed the `max_turns` passed, we raise a [`MaxTurnsExceeded`][agents.exceptions.MaxTurnsExceeded] exception.
```
**critical strings**: `max_turns`, `MaxTurnsExceeded`
**evidence_hash**: `f1011d934522b2fe05de267455898faddd037e2ef0af581c5d11a7dd7571ea38`

### Claim → evidence

1. If we exceed the `max_turns` passed, we raise a [`MaxTurnsExceeded`][agents.exceptions.Max… → `E1`

### Internal review findings

- §6 satisfied: the condition (exceeding the `max_turns` passed) and the result (a `MaxTurnsExceeded` exception) are both inside the anchor, with no antecedent outside it.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

---

## GOLD-B005-18

- **provider**: openai
- **document**: OpenAI TypeScript and JavaScript API Library
- **section**: OpenAI TypeScript and JavaScript API Library › Advanced Usage › Fetch options › Configuring proxies
- **reasoning type**: `exact_lookup`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

What must an Undici-specific option like `dispatcher` be paired with?

### Final answer

The matching `fetch` implementation.

### Final atomic claims

1. Undici-specific options like `dispatcher` must be paired with the matching `fetch` implementation.

### Exact evidence

**E1** · `ver_f30a6447e4df2ab76e4c1475f353109c` 24178–24276 (98 chars) · OpenAI TypeScript and JavaScript API Library › Advanced Usage › Fetch options › Configuring proxies

```
Undici-specific options like `dispatcher` must be paired with the matching `fetch` implementation.
```
**critical strings**: `dispatcher`, `fetch`
**evidence_hash**: `36d9e40ac1ce3cc82a00c5db4d11c8c00c3758313df7d54a8485e5759ad9f73c`

### Claim → evidence

1. Undici-specific options like `dispatcher` must be paired with the matching `fetch` impleme… → `E1`

### Internal review findings

- QUESTION_FORM: 'What must `dispatcher` be?' asks for a value. The span states a pairing requirement — an Undici-specific option must accompany the matching `fetch` implementation — so the question asks for something the evidence does not give.
- SCOPE: 'Undici-specific' is inside the anchor and belongs in the question; the section heading is not needed.

### Repairs made

- **question rewritten** (question_form_correction: ask for the pairing the evidence states)
  - was: What must `dispatcher` be?
  - now: What must an Undici-specific option like `dispatcher` be paired with?
- **answer rewritten** (question_form_correction: ask for the pairing the evidence states)
  - was: Undici-specific options like `dispatcher` must be paired with the matching `fetch` implementation.
  - now: The matching `fetch` implementation.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `36d9e40ac1ce3cc82a00c5db4d11c8c00c3758313df7d54a8485e5759ad9f73c`.

---

## GOLD-B005-19

- **provider**: openai
- **document**: Migration guide
- **section**: Migration guide › Breaking changes › Removed `httpAgent` in favor of `fetchOptions`
- **reasoning type**: `lifecycle_compatibility_migration`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **READY_FOR_OWNER_REVIEW**
- **precheck**: holdout-ready = True

### Final question

What happened to `httpAgent`?

### Final answer

The `httpAgent` client option has been removed in favor of a platform-specific `fetchOptions` property.

### Final atomic claims

1. The `httpAgent` client option has been removed in favor of a [platform-specific `fetchOptions` property](https://github.com/openai/openai-node#fetch-options).

### Exact evidence

**E1** · `ver_e8a7b17b5af64679cadea33cd8f6d250` 10081–10239 (158 chars) · Migration guide › Breaking changes › Removed `httpAgent` in favor of `fetchOptions`

```
The `httpAgent` client option has been removed in favor of a [platform-specific `fetchOptions` property](https://github.com/openai/openai-node#fetch-options).
```
**critical strings**: `httpAgent`, `fetchOptions`
**evidence_hash**: `50dce494bcf32c01963ddfabd2ddf4eecbe4659b793fcf5a7c5f5dbc95543201`

### Claim → evidence

1. The `httpAgent` client option has been removed in favor of a [platform-specific `fetchOpti… → `E1`

### Internal review findings

- Self-contained removal statement naming both the removed option and its replacement. Narrowest accurate type is removal, which the secondary category records.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

---

## Generator defects found during this review

Recorded, not patched: the generation artifact is not being regenerated, and a fix belongs in the next batch's preregistration.

- **the bare-definition-bullet rule only inspects single-span records** (seen in GOLD-B005-01). The generation self-review drops a candidate whose single span is a bare '- `field`: description' bullet, because its scope lives in the heading. B005-01 is two such bullets in a multi-span record, and the rule's `len(spans) == 1` guard let it through. Recorded rather than patched: batch 005's generation artifact is not being regenerated, and a fix belongs in batch 006's preregistration.
- **markdown reference links survive into questions built from conditional sentences** (seen in GOLD-B005-15). The link stripper runs on the composed question, but a reference-style link whose label is itself backticked was not matched. Repaired here by hand; the pattern should be fixed before batch 006.
- **prose mistaken for a section heading by the parser** (seen in GOLD-B005-11). section_path reads 'configured through AWS_REGION, AWS_DEFAULT_REGION, or your AWS profile.' No claim depends on it, and closed batches must not be touched, so this is recorded as a parser observation for a future audit.
