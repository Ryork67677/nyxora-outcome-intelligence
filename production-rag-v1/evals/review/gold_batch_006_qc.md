# GOLD-001 — batch 006 owner QC packet

**9 candidates · corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · prepared 2026-08-24T17:45:58Z**

Nothing in this packet is gold and nothing is verified. Every candidate is `candidate_unverified`, and no script in this repository can change that: `human_verified` exists only where the project owner records an approval.

## Internal authoring review is not independent verification

The statuses below were produced by the authoring model reading its own output against the frozen evidence. That is a self-check. It is not a second opinion from an independent party, it is not verification, and it confers no status on any candidate. A `READY_FOR_OWNER_REVIEW` label means the author found nothing wrong — which is exactly the claim an independent reviewer is there to test.

## What the three states mean

| state | who decides | what it means |
| --- | --- | --- |
| `precheck_holdout_ready` | a script | the record is structurally checkable — hashes, offsets, critical strings inside their own spans, no critical anaphora, no oversized anchor |
| `human_verified` | the project owner | a person read the evidence and approved the case |
| `holdout_eligible` | derived | `human_verified` **and** deterministic claim support **and** valid evidence **and** no unresolved blocker |

9 of 9 candidates are `precheck_holdout_ready`. That is not an argument for approving them: the review below recommends 1 for rejection and repaired 6, and every one of those was precheck-ready before the review looked at it.

## Internal review outcome

| status | candidates |
| --- | --- |
| NEEDS_REPAIR | 6 |
| READY_FOR_OWNER_REVIEW | 2 |
| REJECT_RECOMMENDED | 1 |

| id | provider | reasoning type | shape | internal status | repaired |
| --- | --- | --- | --- | --- | --- |
| `01` | anthropic | `exact_lookup` | single_span | NEEDS_REPAIR | yes |
| `02` | anthropic | `error_behavior` | single_span | NEEDS_REPAIR | yes |
| `03` | anthropic | `lifecycle_compatibility_migration` | single_span | NEEDS_REPAIR | yes |
| `04` | anthropic | `exact_lookup` | single_span | NEEDS_REPAIR | yes |
| `05` | anthropic | `exact_lookup` | single_span | NEEDS_REPAIR | yes |
| `06` | openai | `configuration_interaction` | single_span | REJECT_RECOMMENDED | no |
| `07` | openai | `configuration_interaction` | single_span | READY_FOR_OWNER_REVIEW | no |
| `08` | openai | `lifecycle_compatibility_migration` | single_span | NEEDS_REPAIR | yes |
| `09` | openai | `exact_lookup` | single_span | READY_FOR_OWNER_REVIEW | no |

---

## GOLD-B006-01

- **provider**: anthropic
- **document**: Admin
- **section**: Service Accounts › Create Service Account
- **reasoning type**: `exact_lookup` (generated as `configuration_interaction`)
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

What credential is required to create an `admin`-role service account, and what role may a workload create?

### Final answer

Creating an `admin`-role service account requires an interactive credential, such as a user OAuth token or Console session. A workload may only create `developer`-role service accounts.

### Final atomic claims

1. Creating an `admin`-role service account requires an interactive credential (a user OAuth token or a Console session).
2. A workload may only create `developer`-role service accounts.

### Exact evidence

**E1** · `ver_c299b58fe1f5a4d3a081b550334a7df6` 441865–442046 (181 chars) · Service Accounts › Create Service Account

```
Creating an `admin`-role service account requires
an interactive credential (a user OAuth token or a Console session) — a
workload may only create `developer`-role service accounts.
```
**critical strings**: `admin`, `developer`
**evidence_hash**: `481c22beedb734b9c72fffe1c1646f3f9a3bceb7782aa08f4c8c28a70da5a10c`

### Claim → evidence

1. Creating an `admin`-role service account requires an interactive credential (a user OAuth … → `E1`
2. A workload may only create `developer`-role service accounts. → `E1`

### Internal review findings

- TAXONOMY: relabelled from `configuration_interaction` to `exact_lookup` / `requirement_constraint`. The span states one requirement and one restriction; nothing in it describes two settings bearing on each other.
- QUESTION_SCOPE: the generated question asked only what the action requires. The owner's question also asks what a workload may create, which is the second half of the same sentence and was previously carried by the answer without being asked.
- Two atomic claims, both from the same span. This is a compound fact stated in one place — it is NOT multi-hop and is not labelled as such.

### Repairs made

- **question rewritten** (owner: the fact is good but the reasoning label is inflated — a requirement stated in one sentence is not a configuration interaction)
  - was: What does Creating an `admin`-role service account require?
  - now: What credential is required to create an `admin`-role service account, and what role may a workload create?
- **answer rewritten** (owner: the fact is good but the reasoning label is inflated — a requirement stated in one sentence is not a configuration interaction)
  - was: Creating an `admin`-role service account requires an interactive credential (a user OAuth token or a Console session) — a workload may only create `developer`-role service accounts.
  - now: Creating an `admin`-role service account requires an interactive credential, such as a user OAuth token or Console session. A workload may only create `developer`-role service accounts.
- **atomic_claims rewritten** (owner: the fact is good but the reasoning label is inflated — a requirement stated in one sentence is not a configuration interaction)
  - was: ['Creating an `admin`-role service account requires an interactive credential (a user OAuth token or a Console session) — a workload may only create `developer`-role service accounts.']
  - now: ['Creating an `admin`-role service account requires an interactive credential (a user OAuth token or a Console session).', 'A workload may only create `developer`-role service accounts.']
- **reasoning_type rewritten** (owner: the fact is good but the reasoning label is inflated — a requirement stated in one sentence is not a configuration interaction)
  - was: configuration_interaction
  - now: exact_lookup
- **secondary_category rewritten** (owner: the fact is good but the reasoning label is inflated — a requirement stated in one sentence is not a configuration interaction)
  - was: requires
  - now: requirement_constraint

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `481c22beedb734b9c72fffe1c1646f3f9a3bceb7782aa08f4c8c28a70da5a10c`.

---

## GOLD-B006-02

- **provider**: anthropic
- **document**: Migration guide
- **section**: Opus migration › What changed
- **reasoning type**: `error_behavior`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

What happens if `role: "system"` is used in `messages` with Claude Opus 4.7?

### Final answer

Claude Opus 4.7 rejects it with a 400 error.

### Final atomic claims

1. Claude Opus 4.7 rejects `role: "system"` in `messages` with a 400 error.

### Exact evidence

**E1** · `ver_a7bda3595f2c124605c3228464d4ee52` 55306–55378 (72 chars) · Opus migration › What changed

```
Claude Opus 4.7 rejects `role: "system"` in `messages` with a 400 error.
```
**critical strings**: `Claude Opus 4.7`, `role: "system"`, `messages`, `400`
**evidence_hash**: `d5fd68caa4e7d689da55ce58f7b6befd6e94d1b3ba2645ccfd3bf0144ffcb366`

### Claim → evidence

1. Claude Opus 4.7 rejects `role: "system"` in `messages` with a 400 error. → `E1`

### Internal review findings

- QUESTION_SCOPE: 'What does Claude Opus 4.7 reject?' invites a list. The evidence supports exactly one rejection, so the question is rewritten to ask about that condition and its outcome.
- CRITICAL_STRINGS: extended to the four the owner named. All four are literally present in the anchor; the generated record carried only `messages`, which anchored the weakest part of the claim.

### Repairs made

- **question rewritten** (owner: the question is broader than the exact fact — the span names one rejected thing, not everything the model rejects)
  - was: What does Claude Opus 4.7 reject?
  - now: What happens if `role: "system"` is used in `messages` with Claude Opus 4.7?
- **answer rewritten** (owner: the question is broader than the exact fact — the span names one rejected thing, not everything the model rejects)
  - was: Claude Opus 4.7 rejects `role: "system"` in `messages` with a 400 error.
  - now: Claude Opus 4.7 rejects it with a 400 error.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `d5fd68caa4e7d689da55ce58f7b6befd6e94d1b3ba2645ccfd3bf0144ffcb366`.

---

## GOLD-B006-03

- **provider**: anthropic
- **document**: Code execution tool
- **section**: Model compatibility
- **reasoning type**: `lifecycle_compatibility_migration` (generated as `exact_lookup`)
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

How do the newer code-execution tool versions behave on Claude Haiku 4.5?

### Final answer

Claude Haiku 4.5 accepts `code_execution_20260120` and `code_execution_20260521`, but programmatic tool calling and the REPL state persistence that depends on it are unavailable, so the newer versions behave like `code_execution_20250825` there.

### Final atomic claims

1. Claude Haiku 4.5 accepts the `code_execution_20260120` and `code_execution_20260521` tool types.
2. Programmatic tool calling and the REPL state persistence that depends on it are not available on Claude Haiku 4.5, so the newer versions behave like `code_execution_20250825` there.

### Exact evidence

**E1** · `ver_f65938c74d40ac1e288f169d3d0435b7` 3971–4316 (345 chars) · Model compatibility

```
Claude Haiku 4.5 accepts the `code_execution_20260120` and `code_execution_20260521` tool types, but programmatic tool calling and the REPL state persistence that depends on it aren't available on it, so the newer versions behave like `code_execution_20250825` there.
* `code_execution_20260521` is the same runtime as `code_execution_20260120`.
```
**critical strings**: `Claude Haiku 4.5`, `code_execution_20260120`, `code_execution_20260521`, `code_execution_20250825`
**evidence_hash**: `8832424c5f41dd8f1c3801845a9f0fcfa7a6fcb08e8a803cc4cdc30b97b2cccb`

### Claim → evidence

1. Claude Haiku 4.5 accepts the `code_execution_20260120` and `code_execution_20260521` tool … → `E1`
2. Programmatic tool calling and the REPL state persistence that depends on it are not availa… → `E1`

### Internal review findings

- TAXONOMY: relabelled to `lifecycle_compatibility_migration` / `compatibility`. The span states what is accepted, what is unavailable, and what the newer versions therefore behave like — a compatibility statement, not a lookup.
- QUESTION_SCOPE: 'What does Claude Haiku 4.5 accept?' asks for half of it. The owner's question asks how the newer versions behave there, which is what the sentence is about.
- This is a compound fact stated explicitly in ONE span. It is NOT genuine multi-hop and is not labelled as such.

### Repairs made

- **question rewritten** (owner: `exact_lookup` understates a compound compatibility fact)
  - was: What does Claude Haiku 4.5 accept?
  - now: How do the newer code-execution tool versions behave on Claude Haiku 4.5?
- **answer rewritten** (owner: `exact_lookup` understates a compound compatibility fact)
  - was: Claude Haiku 4.5 accepts the `code_execution_20260120` and `code_execution_20260521` tool types, but programmatic tool calling and the REPL state persistence that depends on it aren't available on it, so the newer versions behave like `code_execution_20250825` there.
  - now: Claude Haiku 4.5 accepts `code_execution_20260120` and `code_execution_20260521`, but programmatic tool calling and the REPL state persistence that depends on it are unavailable, so the newer versions behave like `code_execution_20250825` there.
- **atomic_claims rewritten** (owner: `exact_lookup` understates a compound compatibility fact)
  - was: ["Claude Haiku 4.5 accepts the `code_execution_20260120` and `code_execution_20260521` tool types, but programmatic tool calling and the REPL state persistence that depends on it aren't available on it, so the newer versions behave like `code_execution_20250825` there."]
  - now: ['Claude Haiku 4.5 accepts the `code_execution_20260120` and `code_execution_20260521` tool types.', 'Programmatic tool calling and the REPL state persistence that depends on it are not available on Claude Haiku 4.5, so the newer versions behave like `code_execution_20250825` there.']
- **reasoning_type rewritten** (owner: `exact_lookup` understates a compound compatibility fact)
  - was: exact_lookup
  - now: lifecycle_compatibility_migration
- **secondary_category rewritten** (owner: `exact_lookup` understates a compound compatibility fact)
  - was: accepts
  - now: compatibility

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `8832424c5f41dd8f1c3801845a9f0fcfa7a6fcb08e8a803cc4cdc30b97b2cccb`.

---

## GOLD-B006-04

- **provider**: anthropic
- **document**: Effort
- **section**: How effort works › Recommended effort levels for Claude Sonnet 5
- **reasoning type**: `exact_lookup`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

What effort level does Claude Sonnet 5 default to on the Claude API and Claude Code?

### Final answer

High effort, on both the Claude API and Claude Code.

### Final atomic claims

1. Claude Sonnet 5 defaults to `high` effort on the Claude API and Claude Code.

### Exact evidence

**E1** · `ver_238961530ce62a75c61bdeead5ccb10d` 5123–5199 (76 chars) · How effort works › Recommended effort levels for Claude Sonnet 5

```
Claude Sonnet 5 defaults to `high` effort on the Claude API and Claude Code.
```
**critical strings**: `Claude Sonnet 5`, `high`, `Claude API`, `Claude Code`
**evidence_hash**: `712a1a0780ade57f504d68707890cf5dea3b05f3f7c32b98cb7f1d704c0ac55b`

### Claim → evidence

1. Claude Sonnet 5 defaults to `high` effort on the Claude API and Claude Code. → `E1`

### Internal review findings

- The owner approved this as currently supported and offered a scoped wording 'if desired for naturalness'. It is applied, because it fixes the same breadth defect the owner REQUIRED fixing on GOLD-B006-05, and leaving the two inconsistent would be arbitrary. The fact is unchanged; only the question names the surfaces the source names.
- CRITICAL_STRINGS: `Claude Sonnet 5` added so the model scope the question now asserts is machine-checkable against the anchor. The generated record anchored only `high`.

### Repairs made

- **question rewritten** (owner: optional rescoping accepted — the source scopes the default to two surfaces and the question should say so)
  - was: What does Claude Sonnet 5 default to?
  - now: What effort level does Claude Sonnet 5 default to on the Claude API and Claude Code?
- **answer rewritten** (owner: optional rescoping accepted — the source scopes the default to two surfaces and the question should say so)
  - was: Claude Sonnet 5 defaults to `high` effort on the Claude API and Claude Code.
  - now: High effort, on both the Claude API and Claude Code.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `712a1a0780ade57f504d68707890cf5dea3b05f3f7c32b98cb7f1d704c0ac55b`.

---

## GOLD-B006-05

- **provider**: anthropic
- **document**: Migration guide
- **section**: Or, for the generally available model with the same capabilities: › Migration checklist
- **reasoning type**: `exact_lookup`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

What does `thinking.display` default to on `claude-mythos-5` and `claude-fable-5`?

### Final answer

`"omitted"`, the same default as Claude Mythos Preview.

### Final atomic claims

1. `thinking.display` defaults to `"omitted"` on `claude-mythos-5` and `claude-fable-5`, the same as on Claude Mythos Preview.

### Exact evidence

**E1** · `ver_a7bda3595f2c124605c3228464d4ee52` 15155–15337 (182 chars) · Or, for the generally available model with the same capabilities: › Migration checklist

```
`thinking.display` defaults to `"omitted"` on `claude-mythos-5` and `claude-fable-5`, the same as on Claude Mythos Preview; set `display: "summarized"` to receive readable summaries.
```
**critical strings**: `thinking.display`, `omitted`, `claude-mythos-5`, `claude-fable-5`
**evidence_hash**: `7fa16f3bd72441cb82aeca4783f2642ce67e3cfa78da3dca956bb6d2ea672e6c`

### Claim → evidence

1. `thinking.display` defaults to `"omitted"` on `claude-mythos-5` and `claude-fable-5`, the … → `E1`

### Internal review findings

- QUESTION_SCOPE: `thinking.display` does not have one default. The source gives the default for two named models, so the question names them.
- The owner offered a second atomic claim about `display: "summarized"` and said to include it only if the question is meant to test it. It is NOT included: the question asks about the default, and a claim nothing asks about is an unscored assertion sitting in a benchmark record. The sentence stays in the evidence, where it is context.
- CRITICAL_STRINGS: the two model names added, so the scope the question now asserts is anchored.

### Repairs made

- **question rewritten** (owner: the question is too broad because the source explicitly scopes the behaviour to models)
  - was: What does `thinking.display` default to?
  - now: What does `thinking.display` default to on `claude-mythos-5` and `claude-fable-5`?
- **answer rewritten** (owner: the question is too broad because the source explicitly scopes the behaviour to models)
  - was: `thinking.display` defaults to `"omitted"` on `claude-mythos-5` and `claude-fable-5`, the same as on Claude Mythos Preview; set `display: "summarized"` to receive readable summaries.
  - now: `"omitted"`, the same default as Claude Mythos Preview.
- **atomic_claims rewritten** (owner: the question is too broad because the source explicitly scopes the behaviour to models)
  - was: ['`thinking.display` defaults to `"omitted"` on `claude-mythos-5` and `claude-fable-5`, the same as on Claude Mythos Preview; set `display: "summarized"` to receive readable summaries.']
  - now: ['`thinking.display` defaults to `"omitted"` on `claude-mythos-5` and `claude-fable-5`, the same as on Claude Mythos Preview.']

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `7fa16f3bd72441cb82aeca4783f2642ce67e3cfa78da3dca956bb6d2ea672e6c`.

---

## GOLD-B006-06

- **provider**: openai
- **document**: OpenAI TypeScript and JavaScript API Library
- **section**: OpenAI TypeScript and JavaScript API Library › Amazon Bedrock
- **reasoning type**: `configuration_interaction`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **REJECT_RECOMMENDED**
- **precheck**: holdout-ready = True

### Final question

What does `AWS_BEDROCK_BASE_URL` override?

### Final answer

This uses the regional `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint. The region can also come from `AWS_REGION` or `AWS_DEFAULT_REGION`, and `AWS_BEDROCK_BASE_URL` can override the endpoint.

### Final atomic claims

1. This uses the regional `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint. The region can also come from `AWS_REGION` or `AWS_DEFAULT_REGION`, and `AWS_BEDROCK_BASE_URL` can override the endpoint.

### Exact evidence

**E1** · `ver_f30a6447e4df2ab76e4c1475f353109c` 17117–17323 (206 chars) · OpenAI TypeScript and JavaScript API Library › Amazon Bedrock

```
This uses the regional `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint. The region can also come from `AWS_REGION` or `AWS_DEFAULT_REGION`, and `AWS_BEDROCK_BASE_URL` can override the endpoint.
```
**critical strings**: `AWS_BEDROCK_BASE_URL`, `AWS_REGION`, `AWS_DEFAULT_REGION`
**evidence_hash**: `ebe19ef32b204e03ada1970d7b6266188f378ce00152fd3bc0a2fdd385371dc4`

### Claim → evidence

1. This uses the regional `https://bedrock-mantle.<region>.api.aws/openai/v1` endpoint. The r… → `E1`

### Internal review findings

- The fact is supported: `AWS_BEDROCK_BASE_URL` can override the region-derived Bedrock endpoint.
- DUPLICATE_FACT: GOLD-B005-11, approved in batch 005, carries the same operational relation from the OpenAI Python library. This candidate obtains it from the TypeScript/JavaScript library. Source corroboration is useful; a second benchmark case for the same relation is not.
- The duplicate-control gate did not catch this. It compares question text, span offsets and span text, and two libraries documenting the same behaviour share none of those. Recorded as a generator defect for batch 007 rather than patched here.
- Preserved as an audit example. NOT replaced with a new candidate — the owner was explicit about that.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

The review recommends rejecting this candidate. That recommendation is not a decision and does not bind you.

---

## GOLD-B006-07

- **provider**: openai
- **document**: Realtime agents guide
- **section**: Realtime agents guide › Agent and session configuration › Input transcription settings
- **reasoning type**: `configuration_interaction`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **READY_FOR_OWNER_REVIEW**
- **precheck**: holdout-ready = True

### Final question

What does Setting `audio.input.turn_detection` to `None` disable?

### Final answer

Setting `audio.input.turn_detection` to `None` disables automatic turn detection.

### Final atomic claims

1. Setting `audio.input.turn_detection` to `None` disables automatic turn detection.

### Exact evidence

**E1** · `ver_14a2187cf2216b9d56c213b520a28479` 7318–7399 (81 chars) · Realtime agents guide › Agent and session configuration › Input transcription settings

```
Setting `audio.input.turn_detection` to `None` disables automatic turn detection.
```
**critical strings**: `audio.input.turn_detection`, `None`
**evidence_hash**: `38635aabfe1d74a3c43fa3a4724d6953e94ae26cd373b55e576f27cf497fc07b`

### Claim → evidence

1. Setting `audio.input.turn_detection` to `None` disables automatic turn detection. → `E1`

### Internal review findings

- The anchor is one self-contained sentence: the condition (setting `audio.input.turn_detection` to `None`) and the outcome (automatic turn detection is disabled) are both inside it.
- Relation direction is correct — the setting is the subject of `disables`, and the question asks it that way round.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

---

## GOLD-B006-08

- **provider**: openai
- **document**: Release process/changelog
- **section**: Release process/changelog › Breaking change changelog › 0.21.0
- **reasoning type**: `lifecycle_compatibility_migration` (generated as `configuration_interaction`)
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **NEEDS_REPAIR**
- **precheck**: holdout-ready = True

### Final question

What does the OpenAI Python SDK's temporary legacy-client compatibility path require, and how should that path be treated?

### Final answer

It requires an explicit `httpx` installation and should be treated as a migration bridge.

### Final atomic claims

1. The OpenAI Python SDK's temporary legacy-client compatibility path requires an explicit `httpx` installation.
2. That path should be treated as a migration bridge.

### Exact evidence

**E1** · `ver_de67d790db9792b2f6c5c7418a507764` 1996–2320 (324 chars) · Release process/changelog › Breaking change changelog › 0.21.0

```
The OpenAI Python SDK's temporary legacy-client compatibility path requires an explicit `httpx` installation and should be treated as a migration bridge.
-   Local MCP HTTP customization continues to follow the installed MCP package: MCP Python SDK v1 supplies and uses legacy `httpx`, while MCP Python SDK v2 uses `httpx2`.
```
**critical strings**: `httpx`
**evidence_hash**: `ca119ba8c06e5c6b054c06540e3bda4ced4fe15e0478460fa687fe581aec303d`

### Claim → evidence

1. The OpenAI Python SDK's temporary legacy-client compatibility path requires an explicit `h… → `E1`
2. That path should be treated as a migration bridge. → `E1`

### Internal review findings

- TAXONOMY: relabelled to `lifecycle_compatibility_migration` / `migration`. The sentence is about a compatibility path being a migration bridge, not about two settings interacting.
- QUESTION_SCOPE: the question now also asks how the path should be treated, which is the half of the sentence the answer already carried.
- The owner said to keep the MCP/`httpx2` sentence 'only if it is needed by the final claims'. It is not: no claim uses it. It is dropped from the CRITICAL STRINGS, which is what makes it scored. The sentence stays inside the anchor, because shrinking an anchor is not a repair this project permits — every anchor revision must be a strict outward growth. If the owner meant the span itself, that is a separate instruction and this note is the place to correct it.

### Repairs made

- **question rewritten** (owner: the fact is good but the primary label should not be configuration_interaction)
  - was: What does the OpenAI Python SDK's temporary legacy-client compatibility path require?
  - now: What does the OpenAI Python SDK's temporary legacy-client compatibility path require, and how should that path be treated?
- **answer rewritten** (owner: the fact is good but the primary label should not be configuration_interaction)
  - was: The OpenAI Python SDK's temporary legacy-client compatibility path requires an explicit `httpx` installation and should be treated as a migration bridge.
  - now: It requires an explicit `httpx` installation and should be treated as a migration bridge.
- **atomic_claims rewritten** (owner: the fact is good but the primary label should not be configuration_interaction)
  - was: ["The OpenAI Python SDK's temporary legacy-client compatibility path requires an explicit `httpx` installation and should be treated as a migration bridge."]
  - now: ["The OpenAI Python SDK's temporary legacy-client compatibility path requires an explicit `httpx` installation.", 'That path should be treated as a migration bridge.']
- **reasoning_type rewritten** (owner: the fact is good but the primary label should not be configuration_interaction)
  - was: configuration_interaction
  - now: lifecycle_compatibility_migration
- **secondary_category rewritten** (owner: the fact is good but the primary label should not be configuration_interaction)
  - was: requires
  - now: migration

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

This candidate was repaired. Approving it means approving the repaired evidence: record `approves_evidence_hash` = `ca119ba8c06e5c6b054c06540e3bda4ced4fe15e0478460fa687fe581aec303d`.

---

## GOLD-B006-09

- **provider**: openai
- **document**: Running agents
- **section**: Running agents › Errors and recovery › Error handlers
- **reasoning type**: `exact_lookup`
- **evidence shape**: `single_span` · **requires all evidence**: False
- **internal review status**: **READY_FOR_OWNER_REVIEW**
- **precheck**: holdout-ready = True

### Final question

What does `RunErrorHandlerResult.include_in_history` default to?

### Final answer

`RunErrorHandlerResult.include_in_history` defaults to `True`.

### Final atomic claims

1. `RunErrorHandlerResult.include_in_history` defaults to `True`.

### Exact evidence

**E1** · `ver_2c60e99cfd929a738910b893fd6f1a40` 29933–29995 (62 chars) · Running agents › Errors and recovery › Error handlers

```
`RunErrorHandlerResult.include_in_history` defaults to `True`.
```
**critical strings**: `RunErrorHandlerResult.include_in_history`, `True`
**evidence_hash**: `35af2508c1e224460838e49c3faa5dcd8894bae3b8d76bc91438cd362d9d33a2`

### Claim → evidence

1. `RunErrorHandlerResult.include_in_history` defaults to `True`. → `E1`

### Internal review findings

- The fully-qualified identifier `RunErrorHandlerResult.include_in_history` scopes the question by itself — there is no other `include_in_history` this could mean.
- The anchor is the whole fact in one sentence.

### Your decision

`APPROVE` · `REJECT` · `NEEDS_EDIT`

---

## Generator defects found during this review

Recorded, not patched: the generation artifact is not being regenerated, and a fix belongs in the next batch's preregistration.

- **E. cross-library duplicate facts are invisible to duplicate control** (seen in GOLD-B006-06). Duplicate control compares normalised question text, span offsets and span text. Two provider libraries documenting the same operational behaviour share none of those, so the same fact can enter the benchmark twice from two SDKs. GOLD-B005-11 and GOLD-B006-06 both state that a base-URL environment variable overrides the region-derived Bedrock endpoint.
  - *Proposed fix, preregistered for batch 007:* Compare candidates on their (subject, relation, object) triple, normalised, in addition to text and offsets. Batch 006 records that triple on every candidate, so the material for the check now exists. Flag rather than auto-drop: two libraries genuinely differing in behaviour is a real case, and only a reviewer can tell the two apart.
- **F. compound single-span facts are labelled by their first verb** (seen in GOLD-B006-01, GOLD-B006-03, GOLD-B006-08). The predicate lane picks a frame from the first matching verb and takes the reasoning type from that frame. Three of the nine exported candidates were relabelled by the owner: a requirement read as a configuration interaction, a compatibility statement read as an exact lookup, and a migration note read as a configuration interaction. The evidence was right in every case; the taxonomy was not.
  - *Proposed fix, preregistered for batch 007:* Classify from the whole sentence rather than from the matched verb: a span naming a support status, a version or a migration is a lifecycle case whatever its verb, and `configuration_interaction` should require two settings that bear on each other rather than one requirement with two identifiers in it.
- **G. questions inherit the breadth of their frame, not of their evidence** (seen in GOLD-B006-02, GOLD-B006-04, GOLD-B006-05). 'What does X reject?' and 'What does X default to?' ask for a complete list. The evidence gives one item, usually scoped to named models or surfaces. Three candidates needed rescoping, and in two of them the scope qualifier was not even in the critical strings, so nothing checked it.
  - *Proposed fix, preregistered for batch 007:* When the source sentence carries a model, platform or surface qualifier, the question must carry it too and it must appear in the critical strings. Add a generation gate: a question whose evidence is scoped and whose wording is not, does not export.
