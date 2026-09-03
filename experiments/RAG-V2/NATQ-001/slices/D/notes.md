# NATQ-001 slice D notes (extras NATQ-C-151 .. NATQ-C-190)

**Verifier:** evidence verifier slice D  
**Snapshot:** `snap_689e336380a054d8039dc35b2c09cd0a`  
**Schema:** natq-001-v1  
**Written:** 2026-09-02 1:45 PM EDT (America/New_York)

## Counts

- n_total: 40
- n_support: 27
- n_reject: 13

## SUPPORT IDs

NATQ-C-151, NATQ-C-152, NATQ-C-153, NATQ-C-154, NATQ-C-155, NATQ-C-159, NATQ-C-160, NATQ-C-161, NATQ-C-162, NATQ-C-163, NATQ-C-164, NATQ-C-165, NATQ-C-166, NATQ-C-167, NATQ-C-170, NATQ-C-172, NATQ-C-175, NATQ-C-176, NATQ-C-177, NATQ-C-179, NATQ-C-181, NATQ-C-182, NATQ-C-185, NATQ-C-186, NATQ-C-187, NATQ-C-188, NATQ-C-189

## REJECT IDs

NATQ-C-156, NATQ-C-157, NATQ-C-158, NATQ-C-168, NATQ-C-169, NATQ-C-171, NATQ-C-173, NATQ-C-174, NATQ-C-178, NATQ-C-180, NATQ-C-183, NATQ-C-184, NATQ-C-190

## Process

1. Loaded questions **unchanged** from `/workspace/natq001-authoring/NATQ-001-raw-questions-extra.jsonl` (ids 151–190).
2. No precomputed hits.json for extras. First wrote a batch ILIKE AND search for all 40 ids to `/tmp/natq001/hits-extra-D.json` (terms from the question; provider from `intended_provider` when openai/anthropic).
3. If a hit snippet answered as written, expanded a tight contiguous span via `get_span`/`find_offset` on `document_version.normalized_text`.
4. If n==0 or snippets did not answer: **at most one** extra `search_chunks` (ILIKE). Still no → REJECT. Did not rewrite questions into corpus language.
5. Verified `evidence_text == normalized_text[char_start:char_end]` and sha256.
6. Rejected unsupported/stretched/conflicting items. No `genuine_ambiguity` keep in this slice.

## Isolation

- Did **not** evaluate SYSTEM-H or touch SYSTEM-* files.
- Did **not** run BM25, dense retrieval, or cross-encoder.
- Did **not** open `evals/gold`, `evals/splits`, `evals/review`, or `holdout.json`.
- Did **not** pick the final 100 or write gold.
- Did **not** modify slices A/B/C.
- `retrieval_was_not_run=true` on every SUPPORT packet.
- `verification_status=PENDING_CHATGPT_REVIEW`, `chatgpt_verified=null`.
- Answers quoted from contiguous normalized_text spans only.

## Extra search_chunks (one per unclear id)

Used when original batch hits were empty or non-answering: 153, 154, 155, 156, 157, 158, 161, 162, 164, 167, 168, 169, 171, 173, 174, 176, 178, 179, 180, 181, 182, 183, 184, 185, 188, 189, 190.

Original batch hits were sufficient (no extra needed to locate the answering span) for SUPPORT of: 151, 152, 159, 160, 163, 165, 166, 170, 172, 175, 177, 186, 187.

Extra search located the answering passage for SUPPORT of: 154, 155, 161, 162, 164, 176, 179, 181, 182, 185, 189. 153 and 188 extra n=0; SUPPORT from original-batch schema/error hits.

## Example SUPPORT (3)

- NATQ-C-151: "if claude sends back a thinking block do I have to echo the whole thing plus the signature on the next request or can I strip it"
- NATQ-C-161: "pdf page limit for claude, when does it start rejecting"
- NATQ-C-187: "how do I cancel an in-flight anthropic message batch"

## Example REJECT reasons (3)

- NATQ-C-156: last-tool `cache_control` prefix-caching not in original hits; extra Prompt-caching `tools array` n=0.
- NATQ-C-178: Anthropic consecutive user turns are combined, but extra OpenAI consecutive+messages n=0; question asks both providers.
- NATQ-C-190: corpus forbids dropping/modifying thinking blocks; no recovery path for an already-invalid signature (new thread vs drop).
