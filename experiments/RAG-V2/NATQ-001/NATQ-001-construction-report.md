# NATQ-001 construction report

**Label:** candidate review packets for coordinator ChatGPT  
**Generated:** 2026-09-02 13:53 EDT (2026-09-02T17:53:30Z)  
**Snapshot:** `snap_689e336380a054d8039dc35b2c09cd0a`  
**Repo:** `experiments/RAG-V2/NATQ-001/`

---

## OUTPUT FIRST

| item | value |
|---|---|
| SYSTEM-H `config_hash` (verified) | `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` |
| SYSTEM-H file SHA-256 (verified) | `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475` |
| SYSTEM-H `DEVELOPMENT_ARCHITECTURE_FROZEN` | `True` |
| SYSTEM-H `RELEASE_FROZEN` | `False` |
| n_raw | 230 |
| n_rejected | 118 |
| n_supported | 112 |
| n_selected (review packets) | 100 |
| proposed validation | 40 |
| proposed holdout | 60 |
| proposed split label | **PROPOSED / NOT_FROZEN** |
| retrieval / BM25 / dense / CE | **not run** |
| SYSTEM-H evaluated | **no** |
| V1 `holdout.json` opened | **no** |
| V1 `holdout-access.log.jsonl` | 235 bytes, sha256 `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3` (size/sha only; `holdout.json` not read) |
| frozen gold written | **no** |
| SYSTEM-* identities overwritten | **no** |
| NATQ holdout lock/access log created | **no** |

**STOP:** Do not evaluate SYSTEM-H. Send packets to coordinator ChatGPT first.

---

## SYSTEM-H identity (verified, not evaluated)

- Path: `experiments/RAG-V2/SYSTEM-H-V2-DEV-CANDIDATE/SYSTEM-H-V2-DEV-CANDIDATE.json`
- `name`: `SYSTEM-H-V2-DEV-CANDIDATE`
- `config_hash`: `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` (matches expected `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a`)
- file sha256: `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475` (matches expected `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475`)
- `DEVELOPMENT_ARCHITECTURE_FROZEN`: **True**
- `RELEASE_FROZEN`: **False**
- `NOT_FROZEN`: True
- `independently_validated`: False
- `does_not_overwrite_SYSTEM_G`: True

No SYSTEM-H run, no scoring, no identity rewrite.

---

## Authoring protocol summary

Question-first, isolated; evidence-second.

1. Coordinator ordered **QUESTION-FIRST** authoring: write candidate questions a real developer might type, then stop. No answers, no guessed spans, no retrieval.
2. Domain: OpenAI Agents SDK, Anthropic API, tools, streaming, model configuration, errors, migrations, authentication, context management, structured outputs, realtime, computer use, SDK behavior.
3. Authoring was from general 2026-era product/task knowledge, not from eval items or live docs.
4. 150 questions (NATQ-C-001..150) plus 80 extras (151..230) so a later verifier could reject toward a target of 100 verified cases.
5. Evidence verification (slices A–E) was **isolated from retrieval ranking**: ILIKE / `get_span` on frozen `normalized_text` only. No BM25, dense, or CE.
6. This assembly step selected 100 SUPPORT packets for ChatGPT review and proposed a cluster-safe 40/60 split. It did **not** freeze gold.

Copied protocol: `NATQ-001-authoring-protocol.md` (from `/workspace/natq001-authoring/NATQ-001-authoring-protocol.md`).

---

## Counts

| | n |
|---|---|
| raw authored | 230 (150 + 80 extras) |
| REJECT | 118 |
| SUPPORT (span-verified) | 112 |
| selected for review | 100 |
| SUPPORT held out of the 100 | 12 |
| proposed validation | 40 |
| proposed holdout | 60 |

Slice SUPPORT/REJECT (from disposition files, counted):

| slice | SUPPORT | REJECT | selected in 100 |
|---|---|---|---|
| A (001–050) | 34 | 16 | 29 |
| B (051–100) | 18 | 32 | 16 |
| C (101–150) | 17 | 33 | 16 |
| D (151–190) | 27 | 13 | 24 |
| E (191–230) | 16 | 24 | 15 |

---

## Span re-verification

Every SUPPORT packet (all 112, including the 12 not selected) was re-checked against Postgres `document_version.normalized_text` (DSN `postgresql://rag:rag@localhost:5432/corpus002_restore`):

- `evidence_text == normalized_text[char_start:char_end]` for every `expected_evidence` span
- `evidence_hash == sha256(evidence_text utf-8)`

Result: **112/112 packets OK, 127/127 spans OK, 0 dropped**. No replacement from leftover SUPPORT was required.

Questions in packets match authoring jsonl **byte-for-byte** (0 mismatches).

---

## Selection of 100

`n_supported = 112 ≥ 100`, so 100 were selected for review. Selection did **not** use retrieval scores.

Preferences applied:

- diversity of `intended_provider` / packet `provider`
- diversity of `topics` / `coverage_tags`
- well-bounded evidence (prefer intact contiguous spans over truncated/hedged leftovers)
- hold out near-duplicate intents (keep one per cluster in the 100)

### SUPPORT not selected (n=12)

- `NATQ-C-003`: weaker truncated span (evidence_text cuts mid-word); MCP coverage retained via NATQ-C-043 and NATQ-C-218
- `NATQ-C-007`: near-duplicate of NATQ-C-060 (Agents SDK stream events for messages vs tools)
- `NATQ-C-024`: near-duplicate of NATQ-C-057 (Message Batches + streaming; 057 is the stream:true validation-error bound)
- `NATQ-C-038`: near-duplicate of NATQ-C-225 (defining Agents SDK function tools / JSON schema)
- `NATQ-C-045`: near-duplicate of NATQ-C-029 (forcing a named tool is a subset of tool_choice auto/any/tool/none)
- `NATQ-C-076`: near-duplicate of NATQ-C-132 (native structured outputs vs tool-hack / beta header)
- `NATQ-C-093`: near-duplicate of NATQ-C-080 (HTTP 529 overloaded_error retry vs rate_limit_error)
- `NATQ-C-122`: near-duplicate of NATQ-C-017 (prompt-cache tools→system→messages hierarchy / invalidation)
- `NATQ-C-175`: near-duplicate of NATQ-C-026 (enable citations with citations.enabled on a document block)
- `NATQ-C-181`: near-duplicate of NATQ-C-023 (5-minute vs 1-hour prompt-cache write/TTL pricing)
- `NATQ-C-185`: near-duplicate of NATQ-C-023 (cache_read_input_tokens vs cache_creation_input_tokens is the cheap-reread field of the same pricing story)
- `NATQ-C-224`: near-duplicate of NATQ-C-150 (ComputerTool is a local harness you provide; OpenAI does not host the machine)

### Provider mix of the 100

Packet `provider`:

| provider | n |
|---|---|
| anthropic | 60 |
| openai | 40 |

Authoring `intended_provider`:

| intended_provider | n |
|---|---|
| anthropic | 57 |
| openai | 39 |
| either | 4 |

### Topics of the 100 (multi-label)

| topic | n |
|---|---|
| Anthropic API | 57 |
| OpenAI Agents SDK | 29 |
| context management | 27 |
| tool use / tools | 27 |
| errors | 25 |
| SDK behavior | 22 |
| model configuration | 19 |
| computer use | 10 |
| structured outputs | 8 |
| authentication | 8 |
| streaming | 8 |
| migrations | 5 |
| realtime | 2 |

### Coverage tags of the 100 (multi-label)

| coverage_tag | n |
|---|---|
| exact_identifier_lookup | 45 |
| configuration_interaction | 32 |
| short_evidence | 30 |
| error_behavior | 23 |
| same_document_passage_discrimination | 19 |
| lifecycle_migration | 13 |
| long_document_localization | 10 |
| realistic_paraphrase | 8 |
| multi_span | 8 |
| version_model_discrimination | 7 |
| genuine_ambiguity | 3 |
| multi_hop | 2 |

### Evidence shape of the 100

| evidence_shape | n |
|---|---|
| short_contiguous | 58 |
| single_span | 15 |
| multi_span_same_doc | 6 |
| multi_span | 4 |
| short_normative_paragraph | 2 |
| parameter_definition | 2 |
| http_error_list_item | 2 |
| short_event_flow_list | 1 |
| parameter_table_row | 1 |
| event_name_list | 1 |
| short_normative_sentence | 1 |
| parameter_constraint | 1 |
| http_error_list | 1 |
| enum_value_with_gloss | 1 |
| error_table_row | 1 |
| exception_list | 1 |
| api_endpoint_heading | 1 |
| two_span | 1 |

---

## Proposed split (NOT FROZEN)

PROPOSED / NOT_FROZEN. Cluster near-duplicate intents so a cluster does not straddle val/holdout. Assign clusters greedily after sorting by cluster_id then candidate_id: if the whole cluster fits in remaining validation slots (target 40), assign it to validation; otherwise assign it to holdout (target 60). cluster_id = 'cluster-{NNN}' where NNN is the zero-padded minimum candidate number in the cluster (singletons use their own id). No RNG seed (fully deterministic given the cluster membership list).

- validation: **40** — NATQ-C-001, NATQ-C-201, NATQ-C-002, NATQ-C-004, NATQ-C-217, NATQ-C-005, NATQ-C-006, NATQ-C-008, NATQ-C-009, NATQ-C-203, NATQ-C-010, NATQ-C-134, NATQ-C-011, NATQ-C-012, NATQ-C-013, NATQ-C-014, NATQ-C-015, NATQ-C-016, NATQ-C-179, NATQ-C-017, NATQ-C-023, NATQ-C-155, NATQ-C-019, NATQ-C-071, NATQ-C-021, NATQ-C-044, NATQ-C-147, NATQ-C-022, NATQ-C-160, NATQ-C-161, NATQ-C-025, NATQ-C-026, NATQ-C-199, NATQ-C-027, NATQ-C-170, NATQ-C-029, NATQ-C-191, NATQ-C-030, NATQ-C-032, NATQ-C-033
- holdout: **60** — NATQ-C-043, NATQ-C-218, NATQ-C-047, NATQ-C-053, NATQ-C-061, NATQ-C-163, NATQ-C-186, NATQ-C-200, NATQ-C-056, NATQ-C-151, NATQ-C-152, NATQ-C-057, NATQ-C-058, NATQ-C-143, NATQ-C-060, NATQ-C-065, NATQ-C-069, NATQ-C-080, NATQ-C-083, NATQ-C-088, NATQ-C-087, NATQ-C-090, NATQ-C-092, NATQ-C-100, NATQ-C-162, NATQ-C-182, NATQ-C-187, NATQ-C-105, NATQ-C-106, NATQ-C-112, NATQ-C-119, NATQ-C-120, NATQ-C-121, NATQ-C-123, NATQ-C-207, NATQ-C-212, NATQ-C-124, NATQ-C-159, NATQ-C-188, NATQ-C-127, NATQ-C-131, NATQ-C-132, NATQ-C-153, NATQ-C-148, NATQ-C-150, NATQ-C-177, NATQ-C-189, NATQ-C-154, NATQ-C-164, NATQ-C-165, NATQ-C-166, NATQ-C-167, NATQ-C-172, NATQ-C-176, NATQ-C-193, NATQ-C-205, NATQ-C-209, NATQ-C-219, NATQ-C-225, NATQ-C-227

### Cluster membership

- `cluster-001` → **validation** (2): NATQ-C-001, NATQ-C-201
- `cluster-002` → **validation** (1): NATQ-C-002
- `cluster-004` → **validation** (2): NATQ-C-004, NATQ-C-217
- `cluster-005` → **validation** (1): NATQ-C-005
- `cluster-006` → **validation** (1): NATQ-C-006
- `cluster-008` → **validation** (1): NATQ-C-008
- `cluster-009` → **validation** (2): NATQ-C-009, NATQ-C-203
- `cluster-010` → **validation** (2): NATQ-C-010, NATQ-C-134
- `cluster-011` → **validation** (1): NATQ-C-011
- `cluster-012` → **validation** (1): NATQ-C-012
- `cluster-013` → **validation** (1): NATQ-C-013
- `cluster-014` → **validation** (1): NATQ-C-014
- `cluster-015` → **validation** (1): NATQ-C-015
- `cluster-016` → **validation** (2): NATQ-C-016, NATQ-C-179
- `cluster-017` → **validation** (3): NATQ-C-017, NATQ-C-023, NATQ-C-155
- `cluster-019` → **validation** (2): NATQ-C-019, NATQ-C-071
- `cluster-021` → **validation** (3): NATQ-C-021, NATQ-C-044, NATQ-C-147
- `cluster-022` → **validation** (3): NATQ-C-022, NATQ-C-160, NATQ-C-161
- `cluster-025` → **validation** (1): NATQ-C-025
- `cluster-026` → **validation** (2): NATQ-C-026, NATQ-C-199
- `cluster-027` → **validation** (2): NATQ-C-027, NATQ-C-170
- `cluster-029` → **validation** (2): NATQ-C-029, NATQ-C-191
- `cluster-030` → **validation** (1): NATQ-C-030
- `cluster-032` → **validation** (2): NATQ-C-032, NATQ-C-033
- `cluster-043` → **holdout** (2): NATQ-C-043, NATQ-C-218
- `cluster-047` → **holdout** (1): NATQ-C-047
- `cluster-053` → **holdout** (5): NATQ-C-053, NATQ-C-061, NATQ-C-163, NATQ-C-186, NATQ-C-200
- `cluster-056` → **holdout** (3): NATQ-C-056, NATQ-C-151, NATQ-C-152
- `cluster-057` → **holdout** (1): NATQ-C-057
- `cluster-058` → **holdout** (2): NATQ-C-058, NATQ-C-143
- `cluster-060` → **holdout** (1): NATQ-C-060
- `cluster-065` → **holdout** (2): NATQ-C-065, NATQ-C-069
- `cluster-080` → **holdout** (3): NATQ-C-080, NATQ-C-083, NATQ-C-088
- `cluster-087` → **holdout** (1): NATQ-C-087
- `cluster-090` → **holdout** (1): NATQ-C-090
- `cluster-092` → **holdout** (1): NATQ-C-092
- `cluster-100` → **holdout** (4): NATQ-C-100, NATQ-C-162, NATQ-C-182, NATQ-C-187
- `cluster-105` → **holdout** (1): NATQ-C-105
- `cluster-106` → **holdout** (1): NATQ-C-106
- `cluster-112` → **holdout** (1): NATQ-C-112
- `cluster-119` → **holdout** (1): NATQ-C-119
- `cluster-120` → **holdout** (1): NATQ-C-120
- `cluster-121` → **holdout** (1): NATQ-C-121
- `cluster-123` → **holdout** (3): NATQ-C-123, NATQ-C-207, NATQ-C-212
- `cluster-124` → **holdout** (3): NATQ-C-124, NATQ-C-159, NATQ-C-188
- `cluster-127` → **holdout** (1): NATQ-C-127
- `cluster-131` → **holdout** (1): NATQ-C-131
- `cluster-132` → **holdout** (2): NATQ-C-132, NATQ-C-153
- `cluster-148` → **holdout** (1): NATQ-C-148
- `cluster-150` → **holdout** (3): NATQ-C-150, NATQ-C-177, NATQ-C-189
- `cluster-154` → **holdout** (1): NATQ-C-154
- `cluster-164` → **holdout** (1): NATQ-C-164
- `cluster-165` → **holdout** (1): NATQ-C-165
- `cluster-166` → **holdout** (1): NATQ-C-166
- `cluster-167` → **holdout** (1): NATQ-C-167
- `cluster-172` → **holdout** (1): NATQ-C-172
- `cluster-176` → **holdout** (1): NATQ-C-176
- `cluster-193` → **holdout** (1): NATQ-C-193
- `cluster-205` → **holdout** (1): NATQ-C-205
- `cluster-209` → **holdout** (1): NATQ-C-209
- `cluster-219` → **holdout** (1): NATQ-C-219
- `cluster-225` → **holdout** (1): NATQ-C-225
- `cluster-227` → **holdout** (1): NATQ-C-227

ChatGPT sees **all 100** in the two review batches. The split is metadata only.

---

## Isolation confirmations

- Did **not** run BM25, dense retrieval, or cross-encoder.
- Did **not** evaluate SYSTEM-H or score candidates with SYSTEM-H.
- Did **not** open `evals/splits/gold150-v1/holdout.json`.
- Did inspect `holdout-access.log.jsonl` **size and sha256 only** (235 bytes, `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`). Log was not used as a NATQ lock; no NATQ holdout lock/access log was created.
- Did **not** write frozen gold (`evals/gold/natq*` not written).
- Did **not** copy review markdown into `evals/review`.
- Did **not** overwrite SYSTEM-* identities.
- `retrieval_was_not_run` remains true on every candidate packet.

---

## Outputs

All under `experiments/RAG-V2/NATQ-001/`:

1. `NATQ-001-authoring-protocol.md`
2. `NATQ-001-raw-questions.jsonl` (001–230 in id order; provenance copy of authoring lines)
3. `NATQ-001-disposition.jsonl` (all 230)
4. `NATQ-001-candidates.jsonl` (100 packets; `selected=true`, `proposed_split=validation|holdout`)
5. `NATQ-001-review-batch-001.md` (50) and `NATQ-001-review-batch-002.md` (50)
6. `NATQ-001-proposed-split.json`
7. `NATQ-001-construction-report.md` (this file)
8. `NATQ-001-hashes.json`

## File SHA-256

| file | sha256 |
|---|---|
| `NATQ-001-authoring-protocol.md` | `631ea1f1122005510df55e15b6688f12e59ad897ce7d851799d4c4ad4cad4854` |
| `NATQ-001-raw-questions.jsonl` | `3662a2e4bdac732cb0c9f45d6e2c83fadb18a3b3e25f4cd3ff314f624190f4a1` |
| `NATQ-001-disposition.jsonl` | `aaac7f87e304dedb79a7059b66b76ac084958e92bf7621cb12673041e03de1d1` |
| `NATQ-001-candidates.jsonl` | `4fc870d2ab82f4f4c5ce8b235e8c8a0f4086fe37a9ae704d0564f7b8c2b1a9fa` |
| `NATQ-001-review-batch-001.md` | `a3e5bcce100f7cec5f072fb4ee564364931c1a70eaf15951b9d6dd8909f2d18e` |
| `NATQ-001-review-batch-002.md` | `f30b09c1fb18e81a24b25f3888e51e53b69a8b7301a4442884d59c6559cd76ff` |
| `NATQ-001-proposed-split.json` | `e55ccf40139499438e4a32ef1217ec7d0af5e8302b8cf64efec5aee931e9efbe` |
| `NATQ-001-construction-report.md` | see `NATQ-001-hashes.json` (self-hash omitted here to avoid circularity) |

---

## STOP

Do **not** evaluate SYSTEM-H. Send the 100 packets to coordinator ChatGPT first.
