# NATQ-001 slice A notes (NATQ-C-001 .. NATQ-C-050)

**Verifier:** evidence verifier slice A  
**Snapshot:** `snap_689e336380a054d8039dc35b2c09cd0a`  
**Method:** ILIKE hits.json inspection + at most one extra `search_chunks` per ID. No BM25, dense, or CE. No evals/gold, evals/splits, evals/review, or holdout.json. No SYSTEM-H. Questions copied unchanged.

## Counts

- n_total: 50
- n_support: 34
- n_reject: 16

## SUPPORT IDs

NATQ-C-001, NATQ-C-002, NATQ-C-003, NATQ-C-004, NATQ-C-005, NATQ-C-006, NATQ-C-007, NATQ-C-008, NATQ-C-009, NATQ-C-010, NATQ-C-011, NATQ-C-012, NATQ-C-013, NATQ-C-014, NATQ-C-015, NATQ-C-016, NATQ-C-017, NATQ-C-019, NATQ-C-021, NATQ-C-022, NATQ-C-023, NATQ-C-024, NATQ-C-025, NATQ-C-026, NATQ-C-027, NATQ-C-029, NATQ-C-030, NATQ-C-032, NATQ-C-033, NATQ-C-038, NATQ-C-043, NATQ-C-044, NATQ-C-045, NATQ-C-047

## REJECT IDs

NATQ-C-018, NATQ-C-020, NATQ-C-028, NATQ-C-031, NATQ-C-034, NATQ-C-035, NATQ-C-036, NATQ-C-037, NATQ-C-039, NATQ-C-040, NATQ-C-041, NATQ-C-042, NATQ-C-046, NATQ-C-048, NATQ-C-049, NATQ-C-050

## Isolation

- retrieval_was_not_run: true on every SUPPORT packet
- Did not run BM25 / dense / cross-encoder
- Did not open evals/gold, evals/splits, evals/review, or holdout.json
- Did not evaluate SYSTEM-H or write gold / pick the final 100
- Answers quoted from contiguous normalized_text spans with sha256 verified against evidence_text == normalized_text[char_start:char_end]

## Extra search_chunks used (one per ID, only when n=0 or hits did not answer)

- NATQ-C-002: `The agent loop` → SUPPORT
- NATQ-C-005: `needs_approval` → SUPPORT
- NATQ-C-008: `failure_error_function` → SUPPORT
- NATQ-C-018: `prompt caching` + `beta` → REJECT (conflict)
- NATQ-C-020: `sonnet 4` + `thinking` → REJECT (wrong model for disable recipe)
- NATQ-C-028: `system` + `array` → REJECT
- NATQ-C-031: `functions` + `deprecated` → REJECT
- NATQ-C-034: `tool_choice` + `Chat Completions` → REJECT
- NATQ-C-035: `additionalProperties` → n=0 REJECT
- NATQ-C-036: `tool result` + `image` → REJECT
- NATQ-C-037: `screenshot` + `action` (anthropic) → REJECT (no which-loop discrimination)
- NATQ-C-039: `collision` + `tool` → REJECT (collision policy ≠ two-agent who-wins)
- NATQ-C-040: `call_id` → REJECT
- NATQ-C-041: `must include` + `tools` → n=0 REJECT
- NATQ-C-042: `strict mode` → REJECT
- NATQ-C-048: `unknown tool` → n=0 REJECT
- NATQ-C-049: `timeout` + `default` → REJECT (timeout_behavior default, not duration)
- NATQ-C-050: `interrupted` + `tool_use` → REJECT
