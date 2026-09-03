# Known data defects in the development set — found, recorded, NOT fixed

## OA-002 — evidence span does not contain its own critical claim

Found by `scripts/validate_golden.py` during EXP-014R, on the *original
human-verified* development set.

**Question:** "Which exception does the OpenAI Agents SDK raise when a run exceeds
the `max_turns` limit?"

**Critical claim:** `MaxTurnsExceeded`

**Cited evidence** — `ver_…`, section `["Running agents", "Exceptions"]`,
chars 33598–33793:

> "This exception is raised when the agent's run exceeds the `max_turns` limit
> passed to the `Runner.run`, `Runner.run_sync`, or `Runner.run_streamed` methods.
> It indicates that the agent could not …"

The span *describes* the exception without ever naming it. The string
`MaxTurnsExceeded` occurs at character 1986 of the same document, and presumably in
the sub-heading immediately above the cited span — the anchor's start boundary
excludes it.

**Consequence.** A retrieval system that returns exactly this span is scored as
having found the evidence, although the span alone cannot support the claim. One of
22 spans is affected, so any single experiment's span-level metric could be off by
up to 1/22 ≈ 4.5 percentage points — about one case.

**Why it has not been fixed.** The EXP-014R brief is explicit that the development
set must not be rewritten: every experiment from EXP-000 onward was measured against
these exact anchors, and correcting one now would silently change the meaning of
every historical number without re-running any of them. The defect is recorded here
instead.

**What should happen.** If the anchor is ever corrected it must produce
`development/v2` alongside the untouched v1, and any comparison across the two must
re-run both systems rather than mixing figures.

## Schema note (not a defect)

Two development cases use category `normal`, which the EXP-014R category vocabulary
did not list. The vocabulary was extended to accept it; no case was changed.
