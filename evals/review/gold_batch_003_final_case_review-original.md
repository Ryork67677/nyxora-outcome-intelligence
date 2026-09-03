# GOLD-001 — batch 003 final case: GOLD-B003-04

One decision closes batch 003. The other 19 candidates are approved; this one was sent back with `NEEDS_EDIT` and has been rewritten as directed.

**The evidence was never the problem, and it has not been touched.** Both spans are byte-identical to the ones you reviewed, and both hashes were re-verified against their text. What changed is the question.

---

## The case

**Q.** What happens when the executor model and advisor model do not form a valid pair?

**A.** The API returns a `400 invalid_request_error` naming the unsupported combination.

**Atomic claims**
  1. The executor model and advisor model must form a valid pair.
  2. Requesting an invalid pair returns a `400 invalid_request_error` naming the unsupported combination.

`reasoning_type: error_behavior` · `evidence_shape: multi_span` · `requires_all_evidence: True` — a retriever earns credit only by finding both spans.

## Exact evidence

**Span 1** — `ver_b8b18cda9b875d51a2ce979a1bf4e909` 88971–89112 (141 chars) · `a147d3f035dd177a…`

```
The executor model (the top-level `model` field) and the advisor model (the `model` field inside the tool definition) must form a valid pair.
```

**Span 2** — `ver_b8b18cda9b875d51a2ce979a1bf4e909` 92785–92898 (113 chars) · `1591ea4b2fc1d87d…`

```
If you request an invalid pair, the API returns a `400 invalid_request_error` naming the unsupported combination.
```

**Critical strings** (each verified inside the evidence): `executor model`, `advisor model`, `must form a valid pair`, `invalid pair`, `400 invalid_request_error`, `naming the unsupported combination`

## What changed, and what did not

| | |
| --- | --- |
| question, before | What happens when the executor and advisor models requested for the advisor tool do not form a valid pair? |
| question, after | What happens when the executor model and advisor model do not form a valid pair? |
| evidence spans | unchanged — 2 spans, same offsets, same hashes |
| revisions on record | 7, none touching evidence |

The original question named the advisor tool. That framing is what made the phrase "the tool definition" load-bearing, because a reader had to resolve which tool before the question meant anything. Removing it does not weaken the case: the fact under test is the executor/advisor pairing rule and its failure behaviour, and both spans state that outright.

## The detector finding — kept, not erased

| | |
| --- | --- |
| original finding | refers to 'the tool' with no antecedent in the span |
| phrase | `the tool` |
| classification | **NONCRITICAL_ANAPHORA** |
| override | True by `project_owner` |

**Why noncritical.** Nothing scored mentions 'tool': the question, answer, claims and critical strings are all satisfied without resolving it.

The rule is mechanical, not a judgement call: a span that *opens* on a reference is always critical, because the sentence's own subject or condition is what is missing. Otherwise the reference's head noun is looked for in the question, the answer, the claims and the critical strings. If the scored text never mentions it, resolving it cannot change the score.

Two things this deliberately does not do. It does not edit the evidence to silence the detector — the phrase is still there, verbatim, and a test holds it there. And it does not let a model accept its own finding: without a named human override the case stays blocked, which is what it did until you recorded one.

## Validator and eligibility

**Validator.** PASS — all blocking checks

**Precheck.** holdout-ready.

**Holdout eligibility if approved.** yes

Eligibility is not approval. This case is `needs_human_review` and stays there until you decide.

## Batch 003 state

| | |
| --- | --- |
| `human_verified` | 19 |
| `needs_human_review` | 0 |
| `human_rejected` | 0 |
| genuine multi-hop | 0 (target 3–4) |

The multi-hop shortfall is unchanged and is not being quietly refilled. The five multi-span cases remain useful retrieval tests; none of them is multi-hop reasoning.

## Decision

`APPROVE` or `REJECT`. Approving closes batch 003 at **20 human_verified, 0 rejected**; rejecting closes it at **19 and 1**. Either way it closes, and no retrieval has been run against any of it.
