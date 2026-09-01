# V2-DEVSET-001 status

Written 2026-09-01T02:20:09Z (2026-08-31 22:20 ET). Construction + review packet only. **Nothing is gold. Nothing is frozen.**

## Outcome

| | |
| --- | --- |
| candidates exported | **50** (`V2D-01` … `V2D-50`) |
| status of every record | `candidate_unverified` |
| target | n≈50 (preregistered) |
| owner decision | **Russell asked for 50 after 46**. Final n=**50**. V2D-01..V2D-46 kept unchanged; V2D-47..V2D-50 appended. |
| split role | v2 **development** candidate set, not holdout, not gold150-v1 validation |

## Pass history

| pass | gated unique | notes |
| --- | --- | --- |
| 1 | 15 | per-doc miner limits too tight; GOLD gates + overlap collision; Advisor tool `skipped_timeout` at 45s |
| 2 | 46 | GOLD-ish miner limits restored; collision = exact question or exact `version_id`+char span only; Advisor tool re-included as `advisor_narrow` (tables + short/error only); Russell accepted this packet |
| plus-4 | 50 | Russell asked for 50 after 46. Original 46 unchanged. Recovered leftover extras: 0. Mined first 4 unique newcomers; early-stop. |

A later unapproved pass that grew past 46 (to 54) was **reverted**. Those extras were not left in JSON dumps; plus-4 re-mined 4 unique non-colliding records rather than restoring the reverted 8.

## Provider mix (n=50)

| provider | n |
| --- | --- |
| anthropic | 30 |
| openai | 20 |

## Stress-type mix (a case may carry several tags)

| stress type | n |
| --- | --- |
| identifier_vs_semantic_distractor | 43 |
| short_evidence_unit | 38 |
| correct_document_difficult_passage | 29 |
| lexical_query_shape | 17 |
| parameter_error_literal_lookup | 16 |
| paraphrase_query_shape | 16 |
| same_document_passage_discrimination | 10 |
| version_model_discrimination | 7 |
| long_technical_section | 4 |

## Evidence-kind mix

parameter_table_row 8 · configuration_interaction 4 · short_normative 26 · normative_statement 3 · error_statement 1 · long_technical_section 4 · definition_bullet 1 · lifecycle_statement 1 · constraint_statement 2

## GOLD-001 collision checks (exact only)

Admitted GOLD-001 loaded from `evals/gold`, `evals/golden`, review batches, and `evals/development/v1.jsonl`, filtered by the 150-ID list. `holdout.json` was not opened.

plus-4 dropped: `{'exact_question': 34, 'interaction_relabelled_exact_lookup': 10, 'exact_span': 16, 'subject_mismatch_flagged': 7, 'bare_definition_scope': 19, 'generic_identifier': 9, 'critical_anaphora': 1, 'low_value_flagged': 9, 'unauthorable': 1, 'dangling_reference': 2, 'markdown_junk': 2}`

## The four appended candidates

| id | provider | document | question |
| --- | --- | --- | --- |
| V2D-47 | anthropic | Structured outputs | What happens if you use `@JsonProperty(required = false)`? |
| V2D-48 | anthropic | Messages | What happens if the final message uses the `assistant` role? |
| V2D-49 | openai | How to run gpt-oss with Hugging Face Transformers | What happens if you use `bfloat16` instead of MXFP4? |
| V2D-50 | openai | Models | What happens when you use any GPT-5 model such as `gpt-5.6-sol` in this way? |

Original 46 id/question/span unchanged vs pre-plus-4 snapshot: **True** (`experiments/RAG-V2/V2-DEVSET-001/v2d-01-46-identity-before-plus4.json`).

## Attestations

| | |
| --- | --- |
| `holdout_json_opened` | **false** |
| holdout miss IDs used as authoring templates | **false** |
| `retrieval_was_not_run` | **true** |
| systems executed | none (no SYSTEM-A / D / E) |
| live OpenAI/Anthropic docs fetched | **false** |
| cases declared frozen gold | **false** |
| verdicts imported | **false** |
| gold150-v1 split files renamed/moved | **false** |
| SYSTEM-E config hash | `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe` (unchanged) |
| corpus snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| ChatGPT posting | **not done** |

gold150-v1 validation remains conceptually **`V1-EXPOSED-REGRESSION-40`**. Files were not renamed or moved.

## Packet paths

| | |
| --- | --- |
| preregistration | `experiments/RAG-V2/V2-DEVSET-001-preregistration.md` (+ `.json`) |
| packet json | `evals/review/v2_devset_001_batch_001.json` |
| packet md | `evals/review/v2_devset_001_batch_001.md` (168506 bytes) |
| copies | `experiments/RAG-V2/V2-DEVSET-001/v2_devset_001_batch_001.{json,md}` |
| slices | `evals/review/v2_devset_001_slice{1,2,3}_of_3.{json,md}` plus copies |
| this status | `experiments/RAG-V2/V2-DEVSET-001-status.md` |

## Next step

**Independent ChatGPT verification**, then Russell human QC, **then** freeze. Do not import verdicts in this construction task. Do not freeze. Do not run SYSTEM-D or SYSTEM-E. Do not start EXP-017. Do not optimize E latency.

The generator discovered evidence and proposed questions. It does not declare gold.

## Round-1 ChatGPT verdicts applied (not a freeze)

Written 2026-09-01T02:45:03Z (2026-08-31 22:45 ET).

| | |
| --- | --- |
| round-1 PASS | **34** — **not** imported as frozen gold; **not** changed |
| round-1 FIX_REQUIRED | **16** — repaired; status `candidate_unverified_after_fix`; human_verified=`false` |
| round-1 FAIL | **0** |
| frozen | **false** |
| retrieval run | **false** |
| holdout.json opened | **false** |
| SYSTEM-D / SYSTEM-E | **not run** |
| live docs fetched | **false** |

Canonical outputs:

- `experiments/RAG-V2/V2-DEVSET-001/V2-DEVSET-001-repair-report.md`
- `experiments/RAG-V2/V2-DEVSET-001/V2-DEVSET-001-repaired-candidates.jsonl`
- `evals/review/v2_devset_001_repairs_round1.md` (ChatGPT-ready, 16 only; copied to `/home/box/Downloads/v2_devset_001_repairs_round1.md`)

Copies of earlier names: `experiments/RAG-V2/V2-DEVSET-001/v2_devset_001_repairs_round1.json` + `.md`. Original 50-case packet `evals/review/v2_devset_001_batch_001.json` is unchanged.

The 16 new questions:

- `V2D-03` For org-wide queries, what must any time filter match?
- `V2D-05` What does grouping by `speed` require?
- `V2D-06` What is `usage.speed` when a request with `speed: "fast"` succeeds, including on Claude Opus 4.6?
- `V2D-08` What does `allowed_fallback_models` contain?
- `V2D-13` What does the experimental model reject?
- `V2D-18` What does `ModelStep.raise_error` accept?
- `V2D-19` What argument does `files_from_dir` accept?
- `V2D-21` How should large `view` output be limited, and how can Claude page through the rest with `view_range`?
- `V2D-22` What has already been appended by the time `next_message` returns?
- `V2D-23` What are credentialless `rclone` mounts limited to?
- `V2D-32` What OpenSSL version is required, and what is required of the `openssl` binary on Windows?
- `V2D-33` What do you pass in when you call `Runner.run`, `Runner.run_sync`, or `Runner.run_streamed`?
- `V2D-37` What happens if you pass a `PathLike` instance to the async client?
- `V2D-38` If you previously relied on `temperature` for design variety, what approach should you use?
- `V2D-44` What setting should you add when a streaming Chat Completions provider requires an explicit usage request?
- `V2D-50` What happens when you use any GPT-5 model such as `gpt-5.6-sol` as the default model via `OPENAI_DEFAULT_MODEL` or `RunConfig`?

Next step: independent ChatGPT review of the **16 repairs**, then Russell human QC, **then** freeze. Do not run SYSTEM-D or SYSTEM-E. Do not start EXP-017.
