# NATQ-001 authoring protocol

**Timestamp:** Tuesday, September 1, 2026, 1:49 AM America/New_York (EDT, UTC-4)

**Role:** QUESTION AUTHOR for NATQ-001 (question-first, no evidence).

## Isolation rules (restated)

The author must **not** see, open, grep, search, or otherwise load:

- any source passages, canonical chunks, evidence spans, or corpus snapshot files
- `/workspace/rag-v1` (the whole repo — do not list it, do not read it)
- Postgres, retrieval, BM25, embeddings, cross-encoder (CE)
- previous V2D / V2-DEVSET questions or gold answers
- V1 holdout questions or the historical 11 holdout failures
- exact corpus wording, docs HTML, or captured pages

Work product is written **only** under `/workspace/natq001-authoring/`.

Public knowledge of OpenAI and Anthropic APIs/products (as a developer in 2026 would know them) is allowed. Documentation phrases must not be copied on purpose. Docs must not be looked up on the web — a fetch would pull exact current wording. Authoring is from general product/task knowledge only.

## Isolation attestation

The author:

- did **not** open, list, read, or search `/workspace/rag-v1`
- did **not** open corpus snapshots, canonical chunks, evidence spans, or captured docs HTML
- did **not** open V2D / V2-DEVSET questions or gold answers
- did **not** open V1 holdout questions or historical holdout-failure lists
- did **not** connect to Postgres or run retrieval / BM25 / embeddings / CE
- did **not** fetch OpenAI or Anthropic documentation (or any other web pages) while authoring
- did **not** write answers, evidence spans, or guessed supporting passages

## Process

1. ChatGPT (coordinator) ordered **QUESTION-FIRST** authoring: write candidate questions a real developer might type, then stop.
2. Domain limited to: OpenAI Agents SDK, Anthropic API, tool use / tools, streaming, model configuration, errors, migrations, authentication, context management, structured outputs, realtime, computer use, SDK behavior.
3. Questions were drafted from general 2026-era product/task knowledge (model families, API shapes, SDK patterns, common failure modes) — not from remembered eval items and not by paraphrasing documentation.
4. Wording was deliberately mixed: incomplete terminology, conversational phrasing, abbreviations, mistaken-but-resolvable product names, task-oriented asks, error-oriented asks, what-if, migration, exact identifiers, and configuration interactions.
5. Each candidate is independent. Near-duplicates (same intent, tiny rephrase) were avoided.
6. Coverage tags were applied where they fit; quotas were not forced. Provider mix is recorded, not balanced to 50/50.
7. **No answers** were written. **No evidence** was guessed. **No retrieval** was run.
8. Extras were authored (150) so a later verifier can reject unsupported or ambiguous items toward a target of 100 verified cases.

## Output

- `NATQ-001-authoring-protocol.md` (this file)
- `NATQ-001-raw-questions.jsonl` (150 lines)
- `NATQ-001-raw-summary.md`
