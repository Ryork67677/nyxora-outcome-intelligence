# GOLD-001 — batch 003 generation report erratum

The original report is preserved unchanged at `GOLD-001-batch-003-generation-report-original.{md,json}`. This document corrects it rather than replacing it.

**No candidate record was affected.** Both defects were in report generation. The records did change afterwards, but only because of the independent review, and that is documented separately in the revision report.

---

### E1 — REPORT_GATE_BUG

**The report said, in two places:**

- Composition table: precheck holdout-ready = 20 of 20
- Comparison table: anaphoric spans = 1

**Authoritative:** 19 of 20 are precheck holdout-ready after the fix

**Cause.** The precheck checked hashes, spans, claims, critical strings, size, chunk-id leakage and the retrieval flag — but never ran the anaphora detector. The anaphoric-span count came from the comparison table, which did run it, so the two numbers were computed by different code and never compared.

**Fixed by.** The precheck now runs the anaphora detector over every evidence span of every candidate, with no exemption by evidence kind, and an unresolved anaphora sets precheck_holdout_ready to false. A report that counts an anaphoric span while claiming every candidate is precheck-ready is now refused at write time.

**Which candidate.** Not the one the original metric counted. The original anaphoric span was GOLD-B003-19's `kind` bullet, which the review's own anchor repair resolved. The candidate blocked now is GOLD-B003-04, whose repaired first span contains "the tool definition" — a definite noun phrase the detector reads as an unresolved reference. It is reported as blocking rather than waved through; see the QC packet.

### E2 — REPORT_GATE_BUG

**The report said, in two places:**

- Composition table: complete proposals = 16 of 20
- Comparison table: complete question+answer+claims = 20
- Comparison table: needing reviewer authoring = 4

**Authoritative:** 20 of 20 candidates have a populated question, answer and claim list. 4 of 20 are flagged needs_human_interpretation — the composed multi-span cases, whose joint phrasing a reviewer should check.

**Cause.** Two different quantities were both labelled "complete". The composition table printed total minus needs_human_interpretation; the comparison table counted records with a non-empty answer. Neither number was wrong; the shared label was.

**Fixed by.** The metric is now named complete_question_answer_claims and computed one way, and needs_human_interpretation is reported as its own row. The consistency gate fails the build if the two tables disagree.

## Verification

The new consistency gate was run against the original report's own numbers and refused them. A gate that has never been shown to fail is not evidence of anything.

## Batch state after the review

| | |
| --- | --- |
| candidates | 20 |
| precheck holdout-ready | 19 |
| precheck blocked | GOLD-B003-04 |
| genuine multi-hop | 0 (target 3–4) |
| reasoning types | {'configuration_interaction': 4, 'error_behavior': 4, 'exact_lookup': 10, 'lifecycle': 2} |
| evidence shapes | {'single_span': 15, 'multi_span': 5} |
