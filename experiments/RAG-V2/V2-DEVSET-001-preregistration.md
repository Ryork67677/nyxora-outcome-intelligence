# V2-DEVSET-001 preregistration

**PREREGISTERED — written 2026-09-01T01:44:00Z (2026-08-31 21:44 ET), before any V2-DEVSET-001 candidate was mined.**

This document fixes the construction contract for a new v2 development set **before any candidate exists**. A rule written after seeing the output is a rule fitted to the output. Nothing below is gold. Nothing below freezes a case.

Construction + review packet only. Independent ChatGPT verification is a later gate. Human QC is Russell York. This generator discovers evidence and never declares gold (GOLD-REVIEW-PROCEDURE.md; EXP-014R failed by writing questions AND answers).

## 1. Hypothesis

gold150-v1 **development** is at ceiling for the metric that was being used to compare systems:

- SYSTEM-D-GUARD-BLEND: 20/20 strict Recall@10, 23/23 spans@10
- SYSTEM-E-WITHIN-DOC (config hash frozen below): 20/20 strict Recall@10, 23/23 spans@10, 23/23 candidate evidence recall

ChatGPT (Build Spec for RAG, after EXP-018) reclassified EXP-018 as `INCONCLUSIVE_DUE_TO_DEV_CEILING`. A tied 20/20 on that split is not a retrieval win and cannot measure whether E's larger additive pool helps.

**V2-DEVSET-001 exists so v2 systems can be compared on a discriminative development set.** New human-verified cases, authored from the frozen corpus, frozen before any retrieval is run, then D vs E. This packet is construction only: candidates leave as `candidate_unverified`.

## 2. Conceptual label — do not mutate files

gold150-v1 **validation** (n=40) is conceptually **`V1-EXPOSED-REGRESSION-40`**.

- It is exposed development-adjacent material. It is **not** independent validation for SYSTEM-E.
- Do **not** run SYSTEM-E on gold150-v1 validation as independent validation.
- Do **not** rename, move, re-hash, or edit `evals/splits/gold150-v1/validation.json`, `validation.jsonl`, or any other gold150-v1 split file.
- The conceptual label lives in this preregistration and in `V2-DEVSET-001-status.md` only.

gold150-v1 **development** remains the v1 ceiling split. gold150-v1 **holdout** remains frozen and unopened for this task (`holdout.lock.json` hash recorded below; `holdout.json` is not loaded).

## 3. Frozen identities

| identity | value |
| --- | --- |
| corpus snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| SYSTEM-E-WITHIN-DOC config hash | `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe` |
| SYSTEM-D-GUARD-BLEND config hash | `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a` |
| SYSTEM-A-GLOBAL config hash | `9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38` |
| gold150-v1 holdout lock sha256 | `756a3a9bc74ce3e2dd3a7924c4048984a0ae5e74237bc8053e18b6fec202d914` (from `holdout.lock.json` only) |
| GOLD-001 150-case closure hash | `32b59f774d3efa31` |
| chunk set | `cs_v1_control` (immutable; this task does not chunk) |

**SYSTEM-E hash is unchanged.** This task does not retune E, does not start EXP-017, and does not optimize E latency.

## 4. Target

| | |
| --- | --- |
| target surviving review | **n ≈ 50** human-verified development cases |
| mine / export now | **~60–80** `candidate_unverified` records so ~50 can survive ChatGPT + human QC |
| ID prefix | **`V2D-`** (zero-padded, `V2D-01` …). One prefix; do not mix with `GOLD-V2B001-` |
| batch number | **101** (cannot collide with GOLD-001 batches 001–007) |
| output stem | `evals/review/v2_devset_001_batch_001.*` plus a copy under `experiments/RAG-V2/V2-DEVSET-001/` |
| split role | **v2 development** — not holdout, not gold150-v1 validation, not frozen gold |
| status of every exported record | `candidate_unverified` |

Primary **later** metric candidate (not computed in this task): **gold-span Recall@100** (candidate evidence recall at pool 100). Strict Recall@10 on gold150-v1/dev cannot move. D vs E on this set happens **only after** freeze + ChatGPT independent verification + Russell human QC.

## 5. Exclusions (fixed before mining)

Exclude **all 150 GOLD-001 admitted IDs** and **their evidence spans**. ID sources (no `holdout.json`):

- `experiments/GOLD-001/GOLD-001-150-case-closure.json` / eligibility `holdout_eligible_ids`
- `evals/splits/gold150-v1/development.json` (20 IDs)
- `evals/splits/gold150-v1/validation.json` (40 IDs)

Admitted questions and spans are loaded from `evals/gold`, `evals/golden`, GOLD-001 review batches, and `evals/development/v1.jsonl`, **filtered by the 150-ID list** when a file mixes splits. GOLD dedupe: same `version_id` + char span is a duplicate; normalised question text (whitespace/lowercase) is a duplicate.

**Do not** copy or lightly rewrite questions from `evals/development`, `evals/gold`, or review batches already admitted. New IDs, new questions, new evidence spans.

**Do not** derive cases from the 11 v1 holdout miss IDs, do not open those case records as authoring templates, and do not paraphrase their questions:

`GOLD-B001-02`, `GOLD-B001-09`, `GOLD-B002-06`, `GOLD-B003-04`, `GOLD-B005-07`, `GOLD-B006-02`, `HA-20`, `HA-21`, `HA-37`, `HA-43`, `HA-58`.

Those IDs are in the 150-ID exclusion list. Their questions/spans, if loaded at all, are loaded **only as exclusion keys** from admitted GOLD-001 sources — never as templates.

## 6. Stress coverage — document / query properties, never retrieval outcomes

Target mix is a property of the **document and the authored question**, not of what SYSTEM-D misses. **Do not run a retriever to see what D misses.** Do not mine from holdout residuals.

| stress type | what it means here |
| --- | --- |
| `correct_document_difficult_passage` | gold document is long; the evidence is not the opening; passage selection inside an already-correct document is the hard part |
| `identifier_vs_semantic_distractor` | exact technical identifier in the question (`snake_case`, error codes, API names) where the page also discusses related concepts in prose |
| `same_document_passage_discrimination` | two distinct facts from the same `version_id` (different spans / sections) so the right passage inside one document must be chosen |
| `long_technical_section` | evidence unit 400–1500 characters (hard cap 1500) |
| `short_evidence_unit` | leftover-like 60–180 character units |
| `version_model_discrimination` | span names a model, version, or API surface that must appear in the question |
| `parameter_error_literal_lookup` | parameter table row, definition bullet, numeric/literal constraint, or named error/exception |
| `multi_span_same_document` | two independently anchored spans in one `version_id`; `requires_all_evidence` |
| `lexical_query_shape` | identifier-heavy question (backticked tokens / error codes) — the *shape* that historically disagrees with dense retrieval |
| `paraphrase_query_shape` | prose-heavy "what happens if/when" question with at most one identifier — the *shape* that historically disagrees with lexical retrieval |

A candidate may carry more than one stress tag. Tags are assigned from span length, section offset, identifier count, model/version tokens, evidence kind, and span count. **Never** from a retrieval run.

## 7. Authoring contract (GOLD claim rules)

Order, unchanged:

1. frozen source evidence selected
2. literal source fact extracted
3. subject / relation / object recorded where the builder can state them
4. atomic claims anchored to the span
5. only then the question is written from captured groups / frames

**Never:** invent question → hunt for supporting evidence.

Standing GOLD rules that still apply:

- subject–relation direction (`rag_v1.gold.relations`) — REVERSED and SUBJECT_MISMATCH drop
- no live docs; corpus snapshot is authoritative
- no markdown link junk in questions (`has_markdown_link`)
- no bare-definition-bullet without heading scope in the span itself (`rag_v1.gold.scoping`); `section_path` is never claim scope
- identifiers bound structurally (table first cell, definition-bullet name, or subject window) — not proximity
- critical strings literally inside their own span
- anaphoric spans resolve their antecedent or drop; critical anaphora blocks export
- question form matches evidence form (`rag_v1.gold.questionform`)
- evidence size: <500 preferred, 1000 soft cap, 1500 hard cap; long-section stress uses the 400–1500 band on purpose
- fenced code / JSON literals / sample configuration are not rules
- generator never sets `human_verified`

Every exported record: verbatim evidence, ~900 characters of context each side, `version_id`, char offsets, `section_path`, evidence hash, critical strings, proposed question, proposed atomic claims. Status remains `candidate_unverified`.

## 8. Workflow gates (this task stops before them)

```
frozen corpus
  → this packet (candidate_unverified)
  → independent ChatGPT verification     (parent / outside this repo)
  → Russell human QC
  → freeze V2-DEVSET-001                 (not this task)
  → SYSTEM-D vs SYSTEM-E                 (not this task)
```

ChatGPT independent verification, then Russell human QC, **before freeze**. D vs E **only after freeze**.

Retrieval is **never** run on candidates. SYSTEM-A, SYSTEM-D, and SYSTEM-E are not executed in this task.

## 9. Do-nots

1. Do not declare any case frozen gold.
2. Do not import ChatGPT verdicts in this task.
3. Do not freeze V2-DEVSET-001 in this task.
4. Do not run SYSTEM-A, SYSTEM-D, or SYSTEM-E.
5. Do not run retrieval of any kind to choose, rank, or filter candidates.
6. Do not open `evals/splits/gold150-v1/holdout.json` or holdout question text.
7. Do not open the 11 v1 holdout miss case records as authoring templates.
8. Do not fetch live OpenAI or Anthropic documentation.
9. Do not start EXP-017.
10. Do not optimize E latency.
11. Do not retune or change SYSTEM-E hash `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe`.
12. Do not rename/move gold150-v1 split files; validation is conceptually `V1-EXPOSED-REGRESSION-40` only.
13. Do not skip ChatGPT verification or Russell human QC.
14. Do not reuse GOLD-001 IDs, admitted questions, or admitted spans.

## 10. Attestations required at export

The status file must record:

- holdout files not opened (yes)
- retrieval was not run (yes)
- collision count vs GOLD-001 (questions and spans dropped)
- candidate count, provider mix, stress-type mix
- next step = independent ChatGPT verification

## 11. Not done in this document

- No V2-DEVSET-001 candidate was generated at the time this file was written.
- No retrieval was run.
- Nothing was frozen.
- No verdicts were imported.
