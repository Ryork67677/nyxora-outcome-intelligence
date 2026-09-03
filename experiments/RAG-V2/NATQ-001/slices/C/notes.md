# NATQ-001 slice C notes

- Slice: NATQ-C-101 through NATQ-C-150 (50 candidates)
- Snapshot: `snap_689e336380a054d8039dc35b2c09cd0a`
- Schema: natq-001-v1
- Verifier: evidence-verifier slice C
- Timestamp (America/New_York): 2026-09-02 1:23 PM EDT (write-up completed same afternoon)

## Counts

- n_support: 17
- n_reject: 33
- n_total: 50

## SUPPORT ids

NATQ-C-105, NATQ-C-106, NATQ-C-112, NATQ-C-119, NATQ-C-120, NATQ-C-121, NATQ-C-122, NATQ-C-123, NATQ-C-124, NATQ-C-127, NATQ-C-131, NATQ-C-132, NATQ-C-134, NATQ-C-143, NATQ-C-147, NATQ-C-148, NATQ-C-150

## Process

1. Loaded questions unchanged from `/workspace/natq001-authoring/NATQ-001-raw-questions.jsonl`.
2. Inspected precomputed ILIKE hits in `/tmp/natq001/hits.json` (not BM25/dense/CE).
3. If a snippet answered the question as written, expanded a tight contiguous span via `get_span`/`find_offset` on `document_version.normalized_text`.
4. If n==0 or snippets did not answer: **at most one** extra `search_chunks` (ILIKE) with better terms from the question. Still no → REJECT.
5. Verified `evidence_text == normalized_text[char_start:char_end]` and sha256.
6. Did not rewrite questions into corpus language.
7. Rejected unsupported, stretched, or conflicting items. `genuine_ambiguity` was kept only when the corpus itself presents that ambiguity (NATQ-C-148).

## Isolation

- Did **not** run BM25, dense retrieval, or cross-encoder.
- Did **not** open `evals/gold`, `evals/splits`, `evals/review`, or `holdout.json`.
- Did **not** evaluate SYSTEM-H or touch SYSTEM-* files.
- Did **not** pick the final 100 or write gold.
- `retrieval_was_not_run` is true on every SUPPORT packet.

## Decision notes (selected)

- C-121: 128k in the latest-models table is **max output**, not context. Answer states that discrimination; header row is E2 so columns bind to models.
- C-123: previous_response_id is response chaining, not the Conversations API thread (`conversation_id`).
- C-132: structured outputs are no longer beta-header-required; not a forced-tool fake.
- C-148: tagged genuine_ambiguity — recommended human confirm + classifier-triggered confirm, not a required pre-click gate.

## Extra-search used (one per unclear id; not a second search)

Used for ids whose original hits were empty or non-answering. Extra n=0 still REJECT. Did not chain additional queries.

## Example SUPPORT (3)

- NATQ-C-105: "is the openai agents sdk replacing swarm"
- NATQ-C-124: "how many images can I send in one claude message before it errors"
- NATQ-C-134: "agents sdk output_type as a list vs a single object, allowed?"

## Example REJECT reasons (3)

- NATQ-C-101: no Chat Completions function_call→tool_calls field-rename evidence (harmony hits; extra n=0)
- NATQ-C-110: OpenAI-Organization / OpenAI-Project header requiredness not found (n=0 + extra n=0)
- NATQ-C-142: semantic_vad vs server_vad — original AND extra ILIKE n=0
