# production-rag-v1

An evaluation-first RAG baseline. The retrieval work is finished and frozen; the live
work is GOLD-001, the human-verified evaluation set.

## Every completed phase ends with a PDF

When a phase of work completes — a batch generated, reviewed, closed, an experiment
analysed — build a shareable PDF into `docs/reports/` and hand the user the file. This
is not optional and does not need asking for. A phase is not finished until the PDF
exists.

Build it with a `scripts/build_*_pdf.py` script rather than by hand, following the
existing ones (`build_batch_005_pdf.py` is the current model):

- **read every figure from the artifacts at build time.** No number is retyped into the
  document. A PDF that restates counts from memory is how batch 003's reports came to
  disagree with their own records, twice.
- **gate the build.** Refuse to render when the report disagrees with the batch, when a
  hash no longer covers the records it claims to, when a candidate claims a verification
  it does not have, or when the document would describe a state the project has left.
  A build that cannot be honest should fail, not warn.
- **lead with the finding, not the count.** If a batch came back short, the shortfall is
  the headline and the reasons are the document. If a result is unflattering — 1 chain in
  559, 27 drops from 46 — it goes in the summary, not a footnote.
- Render with headless Chromium; the house CSS is in any of the existing builders.

## Standing constraints for GOLD-001

- Closed batches are historical artifacts. Never edit one; issue an erratum, an audit, or
  a versioned overlay instead.
- `precheck_holdout_ready` (structural) · `human_verified` (owner approval only) ·
  `holdout_eligible` (derived) are three different states and must never collapse.
- No script may produce `human_verified`. Only an explicit owner decision can.
- Retrieval is never run against a GOLD candidate: `retrieval_was_not_run` stays true and
  SYSTEM-A / SYSTEM-B stay frozen and unexecuted, until a holdout is deliberately frozen.
- Report what the records support. Do not force an expected number.

## Running things

`.venv/bin/python` is the interpreter. PostgreSQL sometimes needs
`pg_ctlcluster 16 main start` after the container idles. `pytest` and `ruff check .`
should both be clean before a commit.
