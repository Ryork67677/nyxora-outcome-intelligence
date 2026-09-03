# GOLD-001 — batch 001 v2 metadata upgrade

A versioned overlay, not an edit. Batch 001 v1 is closed and unchanged; the builder
re-verifies its closure hash (`d6f92e8d1a7e77ea…`) before writing and
refuses if it has drifted.

| | |
| --- | --- |
| cases in the overlay | **14** |
| metadata upgraded | 11 |
| carried forward unchanged | 3 |
| holdout-eligible | **14** |
| pending scope repair | `GOLD-B001-13`, `GOLD-B001-17` |
| validator | **14 cases, 0 failures** (`--require-human validation`) |

## What changed, and what did not

Only validation metadata. Question, answer, atomic claims, evidence span, source version
and evidence hash are copied from the closed v1 case, and the builder compares them field
by field and refuses to write if the spec would alter any of them. There is a test that
holds it to that.

Every critical string was checked against the **raw** approved evidence through the
documented Markdown-escape normalisation. Nothing was normalised into storage: evidence
is still stored raw, hashed raw, and shown raw.

## Critical strings added

| case | v2 | critical strings |
| --- | --- | --- |
| `GOLD-B001-01` | upgraded | `` `enable_zoom` ``, `` Default: `false` `` |
| `GOLD-B001-02` | upgraded | `` `reset_tool_choice` ``, `` default: `True` `` |
| `GOLD-B001-03` | carried forward | `claude-fable-5`, `claude-mythos-5`, `is always on`, `` no `thinking` configuration is required `` |
| `GOLD-B001-04` | carried forward | `input guardrails`, `.tripwire_triggered`, `inputguardrailtripwiretriggered`, `exception is raised` |
| `GOLD-B001-05` | upgraded | `400`, `invalid_request_error`, `prompt is too long` |
| `GOLD-B001-06` | upgraded | `` `body` ``, `raw JSON string sent from the server`, `do not parse it first` |
| `GOLD-B001-07` | upgraded | `` not declared in `tools` ``, `returns a 400 error` |
| `GOLD-B001-08` | upgraded | `` `engines.node` ``, `ships in an SDK major release by default` |
| `GOLD-B001-09` | upgraded | `message without a tool use`, `` `max_iterations` `` |
| `GOLD-B001-10` | upgraded | `` `response.output` ``, `drop required reasoning or tool-call items` |
| `GOLD-B001-11` | upgraded | `When a tool raises an error`, `` `is_error: true` ``, `instead of crashing` |
| `GOLD-B001-12` | upgraded | `` `nest_handoff_history` ``, `Optional per-handoff override for the RunConfig-level` |
| `GOLD-B001-14` | carried forward | `claude 4.6 and later models`, `claude mythos preview`, `do not support prefilling assistant messages`, `` 400 `invalid_request_error` `` |
| `GOLD-B001-18` | upgraded | `` `tool_reference` ``, `expanded inline at that point in the conversation body`, `not in the prefix` |

## Cases the mechanical audit flagged, and what human review found

### GOLD-B001-06

The mechanical audit flagged 11% content-word overlap. Human inspection found the span states both halves outright — the `body` must be the raw JSON string sent from the server, and it must not be parsed first. Lexical overlap does not overrule explicit source meaning. Evidence retained; critical strings added.

### GOLD-B001-09

The mechanical audit flagged 50% content-word overlap on the `max_iterations` claim. The span states both stopping conditions in one sentence. Evidence retained; critical strings added for each condition.

Both were retained on their approved evidence. Lexical overlap is a screen, not a
verdict, and in both cases the span states the substance outright — which is exactly why
the audit reports NEEDS_REVIEW to a person rather than deciding.

## Holdout eligibility

`human_verified` and `holdout_eligible` are now separate states.
Every case here was human_verified in v1 and still is. Eligibility is a separate state; gaining it required no new approval and losing it would not revoke one.

Eligibility requires all five conditions in `rag_v1.gold.eligibility`: human approval,
a deterministic check for every claim, critical strings present in the evidence, a valid
evidence hash, and no unresolved scope defect. A case can gain eligibility through
metadata without a new approval, and lose it to a corpus change without the approval
being called wrong.

## What this does not do

- It does not make batch 001 v1 anything other than closed.
- It does not touch `GOLD-B001-13` or `GOLD-B001-17`; both have genuine scope defects and
  are proposed for repair in `gold_batch_001_v2_scope_repairs.md`, applied to nothing.
- It does not freeze a holdout, and no retrieval was run.
