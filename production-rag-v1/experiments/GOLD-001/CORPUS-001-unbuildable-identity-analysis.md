# CORPUS-001 — what the 2,482 unbuildable identities are

*2026-08-31T03:56:09Z*

**They are not documents. They are counts of authoring attempts that produced no question, inside batch 006's generator. They are not a corpus-reproduction blocker.**

## Where the number comes from

`scripts/export_batch_006.py`, one statement:

```python
def add(fact, built, confidence): if built is None: removed["unbuildable"] += 1; return
```

It is recorded in `GOLD-001-batch-006-generation-report.json` at `removed.unbuildable` = **2482**, beside its siblings: `excluded_known_failure_case` 1, `dropped_by_semantic_review` 40, `duplicate_question` 26, `duplicate_evidence` 36, `blocking_anaphora` 1, `duplicate_evidence_text` 5, `document_concentration` 1, `short_of_target_before_overflow` 19, `not_selected_diversity` 1.

## What the objects are

**mined facts — (version_id, char_start, char_end) spans of document text, with critical strings, produced by batch 006's miners.**

They are *not* documents, document versions, corpus rows, GOLD candidates, evidence spans of any approved case.

The phrase 'unbuildable identities' reads like missing corpus objects. It is not. Every one of these is a span *inside* the 202 documents, and the documents are what the snapshot is made of. Nothing about them is missing from the corpus; what is missing is the record of which spans they were.

## The count is attempts, not distinct spans

2,482 counts calls to add() where the builder returned None, not distinct facts. The generator iterates conditional_facts twice — once for build_conditional and again for build_predicate_fact — so one fact can be counted more than once.

Corroboration: the same run mined 1361 facts in total and 773 distinct evidence texts. 2482 exceeds both, which is only possible if the counter counts attempts.

**Consequence.** the number of distinct unbuildable spans is unknown and is at most 1361, not 2482.

## What was lost, and what stops it recurring

The counter recorded a number and discarded every identity. rag_v1.gold.provenance.UnbuildableLog exists so this cannot happen again: it records the span's version and offsets alongside the reason, so the set survives the run.

## Can the identities be recovered?

Only by re-running batch 006's miners over the restored corpus — via `scripts/rederive_unbuildable.py, which imports the batch-006 miners and builders unmodified and refuses unless the corpus reproduces the frozen snapshot id first`. Blocked by the same missing corpus — this is downstream of corpus recovery, never a precondition for it.

## Classification

| needed for | verdict |
| --- | --- |
| A. reproducing the corpus snapshot | **False** |
| B. reproducing the GOLD authoring process | **True** |
| C. provenance only | False |

The snapshot digest is stable_id('snap', name, manifest_hash, PARSER_VERSION, chunking_hash) where manifest_hash covers only the 202 (version_id, content_hash) pairs. No unbuildable span appears in any of those inputs. The set is required input for the batch-007 NO_BUILDER calibration pilot, and for nothing else.

## Correction to the project record

Previously: 'the original 2,482 unbuildable identities remain outstanding' was carried in the corpus-reproduction limitation as if it were a corpus gap.

**Corrected:** It is an authoring-pipeline gap. Removing it from the corpus gate does not make the corpus recoverable — the 139 Anthropic documents still do — but it does mean the corpus gate has one blocker, not two.

