# GOLD-001 — batch 001 claim-support audit

An overlay, not an edit. No batch 001 record was modified, no closure hash was recomputed, and the closed batch still hashes to `d6f92e8d1a7e77ea…`.

**12 SUPPORTED · 3 NEEDS_REVIEW · 1 UNSUPPORTED** across 16 approved cases and 24 atomic claims.

**3 of 16 are holdout-eligible today** — meaning their claims trace to their own span *and* they carry literal critical strings the validator can check. That second condition is what the closure artifact flagged, and it is the binding one.

## Method, and what it cannot tell you

This is a mechanical screen. For each approved claim it checks that every term the claim turns on — code identifiers, numbers, quoted values, product names — appears inside the approved span, and measures how much of the claim's content vocabulary the span carries.

A claim can pass every check here and still be a bad paraphrase; a claim can fail one and still be true. Nothing short of clean is called a verdict — it is called NEEDS_REVIEW and addressed to a person. Retrieval was not run.

## Results

| candidate | status | critical strings | min claim coverage | holdout-eligible |
| --- | --- | --- | --- | --- |
| `GOLD-B001-01` | SUPPORTED | no | 100% | no |
| `GOLD-B001-02` | SUPPORTED | no | 100% | no |
| `GOLD-B001-03` | SUPPORTED | yes | 78% | **yes** |
| `GOLD-B001-04` | SUPPORTED | yes | 75% | **yes** |
| `GOLD-B001-05` | SUPPORTED | no | 60% | no |
| `GOLD-B001-06` | NEEDS_REVIEW | no | 12% | no |
| `GOLD-B001-07` | SUPPORTED | no | 100% | no |
| `GOLD-B001-08` | SUPPORTED | no | 100% | no |
| `GOLD-B001-09` | NEEDS_REVIEW | no | 50% | no |
| `GOLD-B001-10` | SUPPORTED | no | 67% | no |
| `GOLD-B001-11` | SUPPORTED | no | 70% | no |
| `GOLD-B001-12` | SUPPORTED | no | 100% | no |
| `GOLD-B001-13` | UNSUPPORTED | no | 100% | no |
| `GOLD-B001-14` | SUPPORTED | yes | 100% | **yes** |
| `GOLD-B001-17` | NEEDS_REVIEW | no | 50% | no |
| `GOLD-B001-18` | SUPPORTED | no | 80% | no |

## Cases that are not clean

### GOLD-B001-01 — SUPPORTED

- *SUPPORTED* — enable_zoom defaults to false
  - every asserted term is inside the span and 100% of the claim's content words appear there
- no critical claim strings, so `validate_golden.py` does not check this case's claims at all

### GOLD-B001-02 — SUPPORTED

- *SUPPORTED* — reset_tool_choice defaults to True
  - every asserted term is inside the span and 100% of the claim's content words appear there
- no critical claim strings, so `validate_golden.py` does not check this case's claims at all

### GOLD-B001-05 — SUPPORTED

- *SUPPORTED* — If the input alone exceeds the model's context window, the API returns a 400 `invalid_request_error`.
  - every asserted term is inside the span and 100% of the claim's content words appear there
- *SUPPORTED* — The error message is `prompt is too long`.
  - every asserted term is inside the span and 60% of the claim's content words appear there
- no critical claim strings, so `validate_golden.py` does not check this case's claims at all

### GOLD-B001-06 — NEEDS_REVIEW

- *SUPPORTED* — The `body` parameter must be the raw JSON string sent from the server.
  - every asserted term is inside the span and 86% of the claim's content words appear there
- *NEEDS_REVIEW* — The body should not be parsed before being passed to the webhook parsing/verification method.
  - only 12% of the claim's content words appear in the span, and the case carries no critical strings, so nothing else checks it
- no critical claim strings, so `validate_golden.py` does not check this case's claims at all

### GOLD-B001-07 — SUPPORTED

- *SUPPORTED* — Referencing a tool name that is not declared in `tools` returns a 400 error.
  - every asserted term is inside the span and 100% of the claim's content words appear there
- no critical claim strings, so `validate_golden.py` does not check this case's claims at all

### GOLD-B001-08 — SUPPORTED

- *SUPPORTED* — Raising `engines.node`, emitted JavaScript syntax, or required runtime APIs ships in an SDK major release by default.
  - every asserted term is inside the span and 100% of the claim's content words appear there
- no critical claim strings, so `validate_golden.py` does not check this case's claims at all

### GOLD-B001-09 — NEEDS_REVIEW

- *SUPPORTED* — The tool runner stops when Claude returns a message without a tool use.
  - every asserted term is inside the span and 75% of the claim's content words appear there
- *NEEDS_REVIEW* — If `max_iterations` is set, the tool runner also stops when that limit is reached.
  - only 50% of the claim's content words appear in the span, and the case carries no critical strings, so nothing else checks it
- no critical claim strings, so `validate_golden.py` does not check this case's claims at all

### GOLD-B001-10 — SUPPORTED

- *SUPPORTED* — Filtering `response.output` to message items can remove required reasoning or tool-call items.
  - every asserted term is inside the span and 67% of the claim's content words appear there
- *SUPPORTED* — Dropping those required items can cause the next request to fail.
  - every asserted term is inside the span and 86% of the claim's content words appear there
- no critical claim strings, so `validate_golden.py` does not check this case's claims at all

### GOLD-B001-11 — SUPPORTED

- *SUPPORTED* — When a tool raises an error, the tool result should return the error message with `is_error: true` rather than crashing.
  - every asserted term is inside the span and 70% of the claim's content words appear there
- no critical claim strings, so `validate_golden.py` does not check this case's claims at all

### GOLD-B001-12 — SUPPORTED

- *SUPPORTED* — `nest_handoff_history` is an optional per-handoff override for the RunConfig-level `nest_handoff_history` setting.
  - every asserted term is inside the span and 100% of the claim's content words appear there
- no critical claim strings, so `validate_golden.py` does not check this case's claims at all

### GOLD-B001-13 — UNSUPPORTED

- *UNSUPPORTED* — On Google Cloud Agent Platform, `anthropic_version` is passed in the request body and must be set to `vertex-2023-10-16`.
  - the claim asserts `Google Cloud Agent Platform`, which the approved span does not contain
- no critical claim strings, so `validate_golden.py` does not check this case's claims at all

### GOLD-B001-17 — NEEDS_REVIEW

- *NEEDS_REVIEW* — A Files API `File not found` error uses HTTP 404.
  - the claim asserts `Files API`, which appears in the document title or section path but not in the span itself
- *NEEDS_REVIEW* — It indicates that the specified `file_id` does not exist or the caller does not have access to it.
  - only 57% of the claim's content words appear in the span, and the case carries no critical strings, so nothing else checks it
- no critical claim strings, so `validate_golden.py` does not check this case's claims at all

### GOLD-B001-18 — SUPPORTED

- *SUPPORTED* — When a deferred tool is discovered and returned as a `tool_reference`, its full definition is expanded inline in the conversation body.
  - every asserted term is inside the span and 91% of the claim's content words appear there
- *SUPPORTED* — The full definition is not expanded in the prompt prefix.
  - every asserted term is inside the span and 80% of the claim's content words appear there
- no critical claim strings, so `validate_golden.py` does not check this case's claims at all

## Proposed v2 promotion

`PROPOSED — not applied, and no batch 001 record was modified`. It is returned for explicit approval and has not been written anywhere.

- claim repair needed: 4
- critical strings needed (claims otherwise fine): 9

A case in the second list is not wrong — its claims are traceable to its span. It simply carries no literal critical string, so the validator cannot check it, and a holdout built from it would be gated on nothing.

## Holdout

Not frozen, and this audit does not unblock it. SYSTEM-A and SYSTEM-B remain frozen and unexecuted.
