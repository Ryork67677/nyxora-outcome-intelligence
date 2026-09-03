# NATQ-DIAG-001 — POST-VALIDATION MECHANISM DIAGNOSIS

TRACE-ONLY / CORPUS-STRUCTURE. Written 2026-09-03 00:15:58 EDT. SYSTEM-H was not rerun, scores/weights were not changed, NATQ and V1 holdout.json were not opened, NATQ gold was not modified, EXP-020 was not run.

Authoritative EVAL-NATQ-VAL-001 (closed): strict Recall@10 **20/40 = 50.0%**; candidate gold-span case Recall@100 **34/40**; candidate span-level **46/53**; evidence-span Recall@10 **27/53 = 0.5094**; document Recall@10 **35/40**; MRR **0.2952**. Failures: ranking **14**, candidate-generation **6**, document-discovery **0**, gold-ambiguity **0**.

Serialized traces used: `EVAL-NATQ-VAL-001-REPORT.json` and `logs/EVAL-NATQ-VAL-001-pools.jsonl` (C_P, top10 with blend_score, span pool_rank/origin/rank). Corpus metadata/text from frozen postgres snapshot `snap_689e336380a054d8039dc35b2c09cd0a`. Full E-L10 member ids, per-parent local-BM25 ranks, projection ranks, raw CE logits, CE-norm, and retrieval priors were **not** serialized; those fields are marked unavailable rather than recomputed.

---

## 1. Candidate-generation mechanism table

Seven missing gold spans across six candidate-generation cases. **Every** missing span has `gold_in_a_pool_docs=true` and `gold_in_parents=true`.

> Current candidate-generation failures are within-document passage localization failures, not global document-discovery failures.

Nearest-candidate geometry is over the **serialized visible set only** (top10 + C_P + in-pool gold covering chunks). The E-L10 body (~90–110 fused_e rows) was not written to pools.jsonl. Local-BM25 rank within parent and per-document projection rank: **unavailable** (computing them would be a new retrieval run). `chunk_link` is empty; parent/child/sibling is inferred from `section_path`.

| case | provider | gold version | chars | covering chunk | A-pool docs | E-L10 parents | nearest stored same-doc | char dist | same section? | section relation | adjacent chunk retrieved (visible)? | overlapping projection window? | C_P overlapped/neighbored gold? | local-BM25 rank | projection rank | primary mechanism |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| `NATQ-C-004` s0 | openai | `74f8e398` | 21891–22079 | `e5f844c5930c` | yes | yes | `chk_350e78303311766e20` ['top10'] | 6492 | False | distant_same_doc | False | corpus ovl n=2 maps_to_gold=True | ovl=False nb=True | unavailable | unavailable | long-document local ranking miss |
| `NATQ-C-005` s1 | openai | `f0f6db07` | 1919–2104 | `66a236272733` | yes | yes | `chk_15c1a5ddd54293c0cc` ['gold_span_0_covering'] | 2 | True | same | True | corpus ovl n=2 maps_to_gold=True | ovl=False nb=True | unavailable | unavailable | same-section neighborhood miss |
| `NATQ-C-014` s1 | openai | `629b6f1b` | 32058–32393 | `7f61acc4ffb7` | yes | yes | `chk_71217c3103ee1f35f4` ['top10'] | 208 | False | gold_is_parent | True | corpus ovl n=2 maps_to_gold=True | ovl=False nb=True | unavailable | unavailable | same-section neighborhood miss |
| `NATQ-C-179` s0 | anthropic | `3fcf01a7` | 32218–32789 | `3f5a01228cf4` | yes | yes | `chk_d2a54a9b97a72bebb5` ['top10'] | 65036 | False | nearby_shared_prefix | False | corpus ovl n=2 maps_to_gold=True | ovl=False nb=True | unavailable | unavailable | long-document local ranking miss |
| `NATQ-C-044` s0 | anthropic | `bf535dc6` | 8308–8391 | `d6171600a157` | yes | yes | `chk_3b4ca02406fa467c73` ['top10'] | 61608 | False | sibling | False | corpus ovl n=2 maps_to_gold=True | ovl=False nb=False | unavailable | unavailable | long-document local ranking miss |
| `NATQ-C-044` s1 | anthropic | `bf535dc6` | 6308–6435 | `ae6251bc8cf9` | yes | yes | `chk_3b4ca02406fa467c73` ['top10'] | 63564 | False | sibling | False | corpus ovl n=2 maps_to_gold=True | ovl=False nb=False | unavailable | unavailable | long-document local ranking miss |
| `NATQ-C-026` s1 | anthropic | `2f8e802d` | 26711–26743 | `085d1743e592` | yes | yes | `chk_94988b7586392f4fa0` ['C_P'] | 13225 | False | distant_same_doc | False | corpus ovl n=2 maps_to_gold=True | ovl=False nb=True | unavailable | unavailable | long-document local ranking miss |

### Per-span notes (uniform rules, not named-case patches)

**NATQ-C-004 span 0** (openai, `Sessions`, doc_len=30709, n_chunks=88). Gold `ver_b275f1db2ff0a82e2654391774f8e398` chars 21891–22079 section `['Wrap with encryption and TTL', 'Operational patterns', 'Memory persistence']`. Covering `chk_c2389625f0f7ffc5060037b9b449e5f844c5930c` ordinal 73 chars 21863–23408.

- Identifiers (query / gold / nearest stored): `in-memory SQLite` q=False gold=True near=False; `temporary conversations` q=False gold=True near=False; `file-based SQLite` q=False gold=True near=False; `persistent conversations` q=False gold=True near=False
- Buckets: long-document local ranking miss, semantic/paraphrase mismatch, projection coverage gap.
- Gold Sessions doc is 30709 chars / 88 chunks. Nearest stored same-doc candidate is 6492 chars away in a distant section (custom session / compaction). Adjacent ordinals 72 and 74 were not in serialized top10 or C_P. Query paraphrases RAM vs persistence without the gold identifiers (in-memory SQLite / file-based SQLite). Overlapping projection windows exist and map to the covering chunk, but C_P did not add it.

**NATQ-C-005 span 1** (openai, `Human-in-the-loop`, doc_len=15615, n_chunks=15). Gold `ver_ae3bfcc42c733c5051abda30f0f6db07` chars 1919–2104 section `['Human-in-the-loop', 'Marking tools that need approval']`. Covering `chk_5451da95f9f8e826733d725bcd4366a236272733` ordinal 2 chars 1919–2503.

- Identifiers (query / gold / nearest stored): `needs_approval` q=False gold=True near=True; `True` q=False gold=True near=True; `require approval` q=False gold=False near=True; `@tool(needs_approval=True)` q=False gold=True near=False
- Buckets: same-section neighborhood miss, projection coverage gap.
- Gold covering chunk ordinal 2 sits 2 characters after gold span 0's covering chunk (ordinal 1, same section_path ['Human-in-the-loop','Marking tools that need approval']), which is in the pool at pool_rank 15 / final rank 11. Parent doc has only 15 canonical chunks. Adjacent previous chunk retrieved; gold neighbor not in union. Projection windows overlap and map to gold covering chunk; C_P did not add it (C_P did neighbor).

**NATQ-C-014 span 1** (openai, `Tools`, doc_len=44832, n_chunks=55). Gold `ver_cbeb36b7cf9a5e241940a011629b6f1b` chars 32058–32393 section `['Annotated form', 'Agents as tools']`. Covering `chk_c130edc4e298c4ff4bd3743552957f61acc4ffb7` ordinal 36 chars 31524–32599.

- Identifiers (query / gold / nearest stored): `agents as tools` q=False gold=False near=False; `instead of handing off control` q=False gold=False near=False; `as_tool` q=False gold=True near=True
- Buckets: same-section neighborhood miss, adjacent-section miss, long-document local ranking miss, projection coverage gap.
- Missing covering chunk ordinal 36 (section ['Annotated form','Agents as tools']) sits between retrieved same-section gold span 0 (ordinal 35, in pool) and a child-section top-1 hit (ordinal 37, 'Customizing tool-agents', char distance 208). Tools doc is 44832 chars / 55 chunks. Classic neighborhood hole: same-section previous chunk in pool, next child-section in top10, middle gold chunk absent from union.

**NATQ-C-179 span 0** (anthropic, `Messages`, doc_len=804747, n_chunks=493). Gold `ver_18c692f4d28bd01c0a5cac553fcf01a7` chars 32218–32789 section `['Messages', 'Create a Message', 'Body Parameters']`. Covering `chk_ac9cfe6e72739732251c2d7361b53f5a01228cf4` ordinal 21 chars 31034–34525.

- Identifiers (query / gold / nearest stored): `optional string or array of TextBlockParam` q=False gold=True near=False; `system:` q=False gold=True near=False
- Buckets: long-document local ranking miss, adjacent-section miss, projection coverage gap.
- Messages API doc is 804747 chars / 493 chunks. Gold is the Create-a-Message Body Parameters system-prompt type. Nearest stored same-doc candidate is Count-tokens Body Parameters at char distance 65036 (shared prefix 'Messages' only). Adjacent ordinals 20 and 22 not in serialized top10/C_P. Projection windows overlap and map to covering chunk; C_P did not add it.

**NATQ-C-044 span 0** (anthropic, `Bash tool`, doc_len=71331, n_chunks=109). Gold `ver_9bf8513721dc2d1ef3e1ec42bf535dc6` chars 8308–8391 section `['Tool versions']`. Covering `chk_d6c502d2d4b45c2db0abc29c2c98d6171600a157` ordinal 21 chars 8290–8977.

- Identifiers (query / gold / nearest stored): `bash_20250124` q=False gold=True near=False; `Your application runs the command` q=False gold=False near=False; `tool_use` q=False gold=False near=False; `text_editor_20250728` q=False gold=False near=False; `schema-less tool` q=False gold=False near=False
- Buckets: long-document local ranking miss, projection coverage gap.
- Bash tool doc is 71331 chars / 109 chunks. Gold 'Tool versions' / bash_20250124 at chars 8308-8391. Only visible stored same-doc candidate is top10 rank 2 'Combining with other tools' 61608 chars away. Adjacent ordinals not retrieved. No C_P overlap or neighbor. Complementary gold span 2 from a different document (text editor) is in top10 at rank 3.

**NATQ-C-044 span 1** (anthropic, `Bash tool`, doc_len=71331, n_chunks=109). Gold `ver_9bf8513721dc2d1ef3e1ec42bf535dc6` chars 6308–6435 section `['How it works']`. Covering `chk_e97a0e5a38a3255179e40e2fcd03ae6251bc8cf9` ordinal 15 chars 6220–7223.

- Identifiers (query / gold / nearest stored): `bash_20250124` q=False gold=False near=False; `Your application runs the command` q=False gold=True near=False; `tool_use` q=False gold=True near=False; `text_editor_20250728` q=False gold=False near=False; `schema-less tool` q=False gold=False near=False
- Buckets: long-document local ranking miss, projection coverage gap.
- Same Bash tool parent as span 0. Gold 'How it works' (tool_use / application runs the command) at chars 6308-6435, covering ordinal 15. Nearest stored same-doc still the rank-2 'Combining with other tools' chunk 63564 chars away. Adjacent not retrieved. No C_P overlap/neighbor.

**NATQ-C-026 span 1** (anthropic, `Citations`, doc_len=76202, n_chunks=97). Gold `ver_77dd930ea597c30fc512a8f92f8e802d` chars 26711–26743 section `['Document types', 'Plain text documents']`. Covering `chk_7bc8c51b2fbe42e9142852e5c8c7085d1743e592` ordinal 31 chars 26430–26757.

- Identifiers (query / gold / nearest stored): `Citations` q=True gold=True near=False; `source documents` q=False gold=False near=False; `citations": { "enabled": true }` q=False gold=True near=False; `text blocks with citations` q=False gold=False near=False
- Buckets: long-document local ranking miss, identifier mismatch, projection coverage gap.
- Citations doc is 76202 chars / 97 chunks. Missing span is the 32-char JSON snippet citations enabled:true at chars 26711-26743 (section Document types / Plain text documents). Gold span 0 (Preamble) is in top10 at rank 2; gold span 2 (Response structure) is in pool at rank 77. Nearest stored same-doc is a C_P chunk 13225 chars away (How citations work / Citation indices). Adjacent ordinals not in visible set. Query contains 'citations'; that literal JSON snippet was not localized.

### Mechanism bucket counts (7 missing spans)

| bucket | primary | any-of |
| --- | ---: | ---: |
| same-section neighborhood miss | 2 | 2 |
| adjacent-section miss | 0 | 2 |
| long-document local ranking miss | 5 | 6 |
| identifier mismatch | 0 | 1 |
| semantic/paraphrase mismatch | 0 | 1 |
| projection coverage gap | 0 | 7 |
| other | 0 | 0 |

Projection note: **all 7** missing spans have overlapping `ps_v2_ovl_win448_s224` windows in the snapshot whose `covering_chunk_ids` include the gold covering chunk. None of those covering chunks appear in serialized C_P. That is a projection-*selection* miss inside an already-covered document, not a missing window in the corpus. Per-document projection rank of those windows is unavailable.

---

## 2. Ranking movement table + aggregate

46 gold spans were in the candidate pool. Movement compares serialized `pool_rank` (pre-final union order) to final `exp019a_rank`. Raw CE logit / CE-norm / retrieval prior: **unavailable**. Final blended score is present only for covering chunks that landed in serialized top10 (27/46).

| subset | n | improved | worsened | unchanged | outside→top10 | top10→outside |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| overall (in-pool gold spans) | 46 | 27 | 13 | 6 | 5 | 3 |
| strict PASS cases | 21 | 12 | 3 | 6 | 4 | 0 |
| strict FAIL cases | 25 | 15 | 10 | 0 | 1 | 3 |
| multi-span cases (broad n=12) | 20 | 11 | 8 | 1 | 1 | 2 |
| exact-identifier cases | 18 | 10 | 8 | 0 | 2 | 1 |
| OpenAI | 20 | 14 | 3 | 3 | 5 | 1 |
| Anthropic | 26 | 13 | 10 | 3 | 0 | 2 |

Origins of the 46 in-pool gold spans: A pool **40**, projection **4**, local BM25 **2**.

CE/blend is **not simply broken**: 27 improved vs 13 worsened vs 6 unchanged; 5 outside→top10 vs 3 top10→outside. PASS cases show 4 rescues into top10 and 0 ejections. FAIL cases carry all 3 ejections and 10 of 13 demotions. Anthropic in-pool gold is closer to even (13/10) than OpenAI (14/3).

Ugly demotions (do not retune blend on these): C-017 span0 pool 10 → final 48; C-033 span0 pool 5 → final 14; C-201 span1 local-BM25 pool 2 → final 14. Rescues: C-201 span0 15→3; C-217 15→3; C-203 15→2; C-011 24→8; C-015 11→6.

Full per-span ranking rows (origin, pool_rank, final rank, movement, boundary) are in `NATQ-DIAG-001-REPORT.json` item_2.

---

## 3. Multi-span coverage table

Broad multi-span = `n_gold_spans>1` or tag `multi_span` (same definition as EVAL-NATQ-VAL-001): **n=12, strict 2/12, gold spans in top10 9/25, all-gold-in-pool 8/12**.

| case | req | in pool | in top10 | gold final ranks | one doc? | unique version_ids in top10 | unique section_paths in top10 | redundant top10? | missing-gold relation | strict |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- |
| `NATQ-C-201` | 2 | 2 | 1 | [3, 14] | True | 4 | 10 | True | s1:same section as another retrieved gold (in_pool=True) | False |
| `NATQ-C-005` | 2 | 1 | 0 | [11, None] | True | 5 | 9 | True | s0:no_other_gold_in_top10 (in_pool=True); s1:no_other_gold_in_top10 (in_pool=False) | False |
| `NATQ-C-012` | 2 | 2 | 2 | [7, 3] | True | 4 | 10 | True | — | True |
| `NATQ-C-014` | 2 | 1 | 0 | [27, None] | True | 5 | 10 | True | s0:no_other_gold_in_top10 (in_pool=True); s1:no_other_gold_in_top10 (in_pool=False) | False |
| `NATQ-C-017` | 2 | 2 | 1 | [48, 2] | True | 6 | 10 | True | s0:distant section (in_pool=True) | False |
| `NATQ-C-023` | 2 | 2 | 0 | [17, 43] | True | 4 | 9 | True | s0:no_other_gold_in_top10 (in_pool=True); s1:no_other_gold_in_top10 (in_pool=True) | False |
| `NATQ-C-044` | 3 | 1 | 1 | [None, None, 3] | False | 6 | 10 | True | s0:different document (in_pool=False); s1:different document (in_pool=False) | False |
| `NATQ-C-160` | 2 | 2 | 0 | [98, 23] | False | 3 | 6 | True | s0:different document (no other gold in top10; gold doc may still be in top10 via non-gold chunks) (in_pool=True); s1:no_other_gold_in_top10 (in_pool=True) | False |
| `NATQ-C-026` | 3 | 2 | 1 | [2, None, 77] | True | 4 | 10 | True | s1:distant section (in_pool=False); s2:nearby section (in_pool=True) | False |
| `NATQ-C-170` | 1 | 1 | 1 | [2] | True | 5 | 9 | True | — | True |
| `NATQ-C-030` | 2 | 2 | 1 | [51, 6] | False | 8 | 9 | True | s0:different document (in_pool=True) | False |
| `NATQ-C-032` | 2 | 2 | 1 | [1, 15] | True | 4 | 9 | True | s1:same section as another retrieved gold (in_pool=True) | False |

Every one of the 12 multi-span top10s contains redundant same-version or same-section chunks. Complementary gold is often same-document (10/12 cases are one-doc evidence) but a different or distant section.

---

## 4. Oracle candidate-pool ceiling (diagnostic only, not a system)

**ORACLE-COVERAGE-A.** If any 10 items may be selected from the existing candidate pool with gold knowledge: **34/40** cases contain all required evidence. This equals recorded candidate gold-span case Recall@100. Max required spans on this split is 3, so the pool-size-10 cap does not bind. The 6 misses are exactly the candidate-generation cases.

**ORACLE-COVERAGE-B.** Keep existing final scores. A non-gold top10 item is a redundant slot if another top10 item shares its `version_id` or `section_path`. Replace those slots with gold covering chunks already in the pool but outside top10. **14 strict cases theoretically rescued** (all 14 ranking-primary failures). The 6 candidate-generation cases are not fully rescueable because at least one required gold span is absent from the pool.

Neither oracle is a deployable system. They bound what within-pool set selection vs neighborhood expansion can theoretically do.

---

## 5. Dominant failure mechanisms, ranked

1. **Independent-passage ranking / missing set-aware complementary selection.** 14/20 strict failures are ranking. Multi-span 2/12 strict, 9/25 gold spans in top10. Oracle-B rescues all 14 ranking failures. Top10 is repeatedly packed with same-version duplicates while complementary gold sits at ranks 11–98.
2. **Within-document passage localization.** All 7 missing gold spans already have their documents in SYSTEM-A and in the E-L10 parent set. Zero document-discovery failures. Current candidate-generation failures are within-document passage localization failures, not global document-discovery failures.
3. **Same-section / ordinal-neighborhood expansion gap.** C-005 and C-014: the immediately adjacent same-section chunk was retrieved and the gold covering chunk was not.
4. **Long-document local ranking miss.** C-004, C-179, C-044 (×2), C-026: 30k–805k char parents; nearest serialized same-doc candidate 6.5k–65k chars away.
5. **CE/blend robustness (secondary).** Helps 27 vs hurts 13. Do **not** change the frozen 0.7/0.3 blend on this evidence.
6. **Global document retrieval — not the main issue.** 0 discovery failures; document Recall@10 35/40; every CG miss is already inside the parent machinery.

Natural paraphrase (tag) was 4/5 strict in EVAL-NATQ-VAL-001 and is not a dominant mechanism here.

---

## 6. Evidence for / against interventions

| intervention | verdict | for | against |
| --- | --- | --- | --- |
| more global retrieval | **against as next primary** | 5 cases still lack a gold-doc chunk in final top10 (ranking, not discovery) | 0 document-discovery failures; all 7 missing spans already have gold in A-pool docs and parents; forbids testing larger L/P now |
| stronger within-doc expansion | **for** | all 6 CG failures are localization inside found parents; C-005/C-014 are ordinal-adjacent holes; projection windows already cover every missing gold span | local-BM25 rank of missing chunks not stored (unavailable); cannot blame W vs L extras specifically |
| better reranking (CE/blend retune) | **mixed; do not retune 0.7/0.3** | 13 demotions, 3 top10→outside, Anthropic 13/10 improved/worsened | overall 27 improved vs 13 worsened; PASS cases 4 rescues and 0 ejections |
| set-aware / coverage-aware top10 selection | **strongly for (diagnostic ceiling)** | Oracle-B +14 ranking cases; multi-span 2/12; ranks 11–19 crowded out by same-doc duplicates | cannot rescue the 6 CG misses; gold-aware oracle is not a deployable ranker |

---

## 7. ONE recommended next experiment (DO NOT RUN)

**EXP-020 — Within-document neighborhood expansion + coverage-aware top-10 selection.** Design only. Not run.

- Keep frozen SYSTEM-H identity: do not change L, P, W, BLEND_CE=0.7, BLEND_A=0.3, CE model, or SYSTEM-A.
- Change 1: after the existing union pool is materialized, add canonical chunks that are ordinal-adjacent and/or same-`section_path` siblings of already-retrieved chunks whose `version_id` is in the E-L10 parent set (within-doc expansion on already-found parents, not new global retrieval).
- Change 2: replace independent top-10 truncation with one pre-registered coverage-aware selector over the already-blended ranking (keep the next chunk that adds a new `(version_id, section_path)` or that is ordinal-adjacent to an already-kept parent-doc section; drop near-duplicate same-section extras). No MMR weight search.
- Evaluate once on NATQ-001 validation n=40 with the same gates as EVAL-NATQ-VAL-001. Log whether the 7 currently missing covering chunks enter the expanded pool, unique version_id/section_path in top10, and ranking movement of the 46 in-pool gold spans.
- Hypothesis: neighborhood expansion converts some CG misses into ranking cases; coverage-aware top10 converts some of the 14 ranking misses into strict hits. Upper bounds: ORACLE-A = 34/40, ORACLE-B = +14 ranking cases.
- STOP after that one run. Do not open holdout unless ChatGPT authorizes.

This diagnosis did **not** run EXP-020, did not test larger L/P, did not alter W, did not change CE blend, did not add MMR/diversity penalties/section bonuses/adjacency expansion to SYSTEM-H, and did not run SYSTEM-I.

---

## 8. NATQ holdout access log

- bytes: **0**
- sha256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- still 0 bytes with empty-file sha: **true**
- `holdout.json` opened: **false**

## 9. V1 holdout untouched

- access log bytes: **235**
- sha256: `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`
- matches frozen 235-byte sha `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`: **true**
- `evals/splits/gold150-v1/holdout.json` opened: **false**

---

## STOP

Stop. Do not run EXP-020. SYSTEM-H unchanged. Holdout unopened.
