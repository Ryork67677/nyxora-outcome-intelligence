# V2-DEVSET-001 FREEZE n=50

**FROZEN** `2026-09-01T02:54:52Z` (UTC). n=50. Snapshot `snap_689e336380a054d8039dc35b2c09cd0a`.

New files only. gold150-v1 was not renamed. `holdout.json` was not opened.
SYSTEM-E knobs were not changed. `cs_v1_control` was not mutated.
`SYSTEM-D-GUARD.json` and `SYSTEM-D-RELEASE.json` were not mutated.
Retrieval was **not** run at freeze time.

## Manifest hashes

| artifact | sha256 |
| --- | --- |
| `experiments/RAG-V2/V2-DEVSET-001/V2-DEVSET-001-FREEZE.json` | `97ea6befbb4fd845f53da2aef20ba84cedaaf69c0f09e3ad90833b813fee2ad9` |
| `evals/gold/v2-devset-001.jsonl` | `cb687f3cc88b38d4beed7ad4bc829296a30518aaaf45cce0677ec568b1bf77e5` |
| `evals/splits/v2-devset-001/development.json` | `6b0c49c9040c215fde6134697c35a1f28458ba7d72ef012c0840feb7f9c3eb17` |

## Frozen identities

| identity | value |
| --- | --- |
| n | **50** |
| corpus snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| SYSTEM-D-GUARD-BLEND | `d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a` |
| SYSTEM-E-WITHIN-DOC | `7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe` (unchanged; knobs not retuned) |
| SYSTEM-A-GLOBAL | `9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38` |
| CE ONNX | `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a` |
| chunk set | `cs_v1_control` (immutable) |

## Verification provenance (honest)

- `chatgpt_verified=true` for all 50 after independent ChatGPT review
  (round1 34 PASS + round2 15 PASS + round3 V2D-06 PASS).
- `human_verified=true` because ChatGPT (Build Spec for RAG) instructed:
  after all 16 pass, mark all 50 human-verified, freeze, hash, then D-vs-E.
  Russell's standing order is to follow that loop. This freeze records that
  instruction being executed. **It does not claim Russell personally QC'd**
  each of the 50 cases.
- `frozen=true`. `retrieval_was_not_run=true` until the subsequent D-vs-E step.

## Assembly

- **34 PASS (round 1):** question/answer/span kept from
  `evals/review/v2_devset_001_batch_001.json` first-mined packet.
  IDs: V2D-01, V2D-02, V2D-04, V2D-07, V2D-09, V2D-10, V2D-11, V2D-12, V2D-14, V2D-15, V2D-16, V2D-17, V2D-20, V2D-24, V2D-25, V2D-26, V2D-27, V2D-28, V2D-29, V2D-30, V2D-31, V2D-34, V2D-35, V2D-36, V2D-39, V2D-40, V2D-41, V2D-42, V2D-43, V2D-45, V2D-46, V2D-47, V2D-48, V2D-49
- **16 repairs:** question/answer/span/hash from
  `V2-DEVSET-001-repaired-candidates.jsonl`.
  IDs: V2D-03,05,08,13,18,19,21,22,23,32,33,37,38,44,50 and V2D-06.
- **V2D-06:** ROUND-2 answer after the later python rewrite.
  Answer: `Normally `usage.speed` is `"fast"`. Claude Opus 4.6 is the exception: a successful `speed: "fast"` request can report `"standard"`.`
  Confirmed: normal-case + Opus 4.6 exception; starts with Normally `usage.speed`.

## Gold harness files

EXP-016/018 schema: `case_id`, `category`, `question`, `expected_evidence`
(`version_id` + `section_path` + `char_start`/`char_end`), `expected_abstain`, `notes`.

- split: `evals/splits/v2-devset-001/development.json`
- gold jsonl: `evals/gold/v2-devset-001.jsonl`
- harness copy: `evals/splits/v2-devset-001/development.jsonl` (byte-identical to gold jsonl)

## Next

One comparison of frozen SYSTEM-D vs frozen SYSTEM-E on this set.
Do not retune E after seeing scores. Do not open holdout.json.
