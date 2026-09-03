# CORPUS-001 — expected 202-document manifest

*2026-08-31T03:55:16Z*

The recovery checklist for `snap_689e336380a054d8039dc35b2c09cd0a`.

## Two snapshot parameters recovered

Both were previously recorded as unknown. They are confirmed together, by arithmetic:

| parameter | value | how |
| --- | --- | --- |
| `name` | `v1-openai-anthropic` | searched; confirmed by the reproduction below |
| `manifest_hash` | `452479294cbbbe702b15d2df3f5a268023247dcd630782aaad5e17690cee7b17` | read from `experiments/EXP-007/results.json` |
| `parser_version` | `v1.0` | `rag_v1.parsing` |
| `chunking_config_hash` | `bbc874e4f27a7e6826d5106e33510942fd76cb28cf55b5c3333f014e2a6fd916` | `rag_v1.config.settings` |

```
stable_id("snap", "v1-openai-anthropic", manifest_hash, "v1.0", chunking_hash)
  = snap_689e336380a054d8039dc35b2c09cd0a
```

Any other name gives a different 128-bit value, so the match confirms the name **and** the manifest hash at once. The manifest hash is the better recovery target of the two: it covers only the 202 `(version_id, content_hash)` pairs, so it isolates the corpus content from the parser and chunking parameters.

## Expected-identity coverage

| | documents |
| --- | --- |
| expected entries | 202 |
| with a recovered expected `version_id` | **89** |
| &nbsp;&nbsp;from a GOLD record (url + version paired) | 63 |
| &nbsp;&nbsp;from a retrieval experiment artifact | 26 |
| with no recorded identity anywhere | 113 |
| Anthropic documents with a recovered expected `version_id` | **40** |

A further **62** expected `version_id` values survive in experiment artifacts without a url attached. They are still an oracle: a candidate historical capture either hashes into that set or it does not, so no trust is required to test one.

`expected_raw_content_hash` is `UNKNOWN` for all 202 — the raw pre-normalization hash was never written to any surviving artifact. `ordinal` is `UNKNOWN` and is not needed: `corpus_snapshot_version` has no ordinal column and `create_snapshot` orders by `version_id`.

