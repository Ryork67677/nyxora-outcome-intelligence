# V2-DEVSET-001 repair report (ChatGPT round-1, 16 FIX_REQUIRED)

Written 2026-09-01T02:45:03Z (2026-08-31 22:45 ET). **Nothing is gold. Nothing is frozen. Nothing is human_verified.**

Applied ChatGPT round-1 `FIX_REQUIRED` rewrites only. The 34 PASS cases were not changed and were not imported as frozen gold. Holdout.json was not opened. Retrieval was not run. SYSTEM-D / SYSTEM-E were not run. Live docs were not fetched.

Corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a`. Evidence hashes recomputed from frozen `document_version.normalized_text`. `version_id`, provider, and document are unchanged. Spans expanded only where round-1 `evidence_boundary_complete=false`; every expansion is a strict superset of the original packet span.

| | |
| --- | --- |
| PASS (untouched, not gold) | 34 |
| FIX_REQUIRED repaired | **16** |
| FAIL | 0 |
| status after fix | `candidate_unverified_after_fix` |
| human_verified | **false** on every repaired record |

## The 16 new questions

- **V2D-03**: For org-wide queries, what must any time filter match?
- **V2D-05**: What does grouping by `speed` require?
- **V2D-06**: What is `usage.speed` when a request with `speed: "fast"` succeeds, including on Claude Opus 4.6?
- **V2D-08**: What does `allowed_fallback_models` contain?
- **V2D-13**: What does the experimental model reject?
- **V2D-18**: What does `ModelStep.raise_error` accept?
- **V2D-19**: What argument does `files_from_dir` accept?
- **V2D-21**: How should large `view` output be limited, and how can Claude page through the rest with `view_range`?
- **V2D-22**: What has already been appended by the time `next_message` returns?
- **V2D-23**: What are credentialless `rclone` mounts limited to?
- **V2D-32**: What OpenSSL version is required, and what is required of the `openssl` binary on Windows?
- **V2D-33**: What do you pass in when you call `Runner.run`, `Runner.run_sync`, or `Runner.run_streamed`?
- **V2D-37**: What happens if you pass a `PathLike` instance to the async client?
- **V2D-38**: If you previously relied on `temperature` for design variety, what approach should you use?
- **V2D-44**: What setting should you add when a streaming Chat Completions provider requires an explicit usage request?
- **V2D-50**: What happens when you use any GPT-5 model such as `gpt-5.6-sol` as the default model via `OPENAI_DEFAULT_MODEL` or `RunConfig`?

## Before / after

### V2D-03

**Document.** anthropic · Compliance API · `ver_1d58a563501b073d898977de6bc2a823`

**Repair reason (ChatGPT).** The evidence supports the full rule, but the question incorrectly asks what created_at itself requires; specifically created_at.* filters on org-wide queries require order_by=created_at, while the answer also adds the separate updated_at rule.

**Before Q.** What does `created_at` require?

**After Q.** For org-wide queries, what must any time filter match?

**Before A.** For org-wide queries, any time filter must match the sort key: `created_at.*` filters require `order_by=created_at`, and `updated_at.*` filters require `order_by=updated_at`.

**After A.** The sort key: `created_at.*` filters require `order_by=created_at`, and `updated_at.*` filters require `order_by=updated_at`.

**Before span.** `ver_1d58a563501b073d898977de6bc2a823` 4640364–4640538 (174 chars) · `c8a02c427ca5f0eeb935c95bc9dc780e1e3d3c86be46519f89d65214de50948f`

```
For org-wide queries, any time filter must match the sort key: `created_at.*` filters require `order_by=created_at`, and `updated_at.*` filters require `order_by=updated_at`.
```

**After span.** `ver_1d58a563501b073d898977de6bc2a823` 4640364–4640538 (174 chars) · `c8a02c427ca5f0eeb935c95bc9dc780e1e3d3c86be46519f89d65214de50948f`

```
For org-wide queries, any time filter must match the sort key: `created_at.*` filters require `order_by=created_at`, and `updated_at.*` filters require `order_by=updated_at`.
```

**Span.** unchanged (+0 before, +0 after).

**What changed.** Rewrote around the org-wide time-filter/sort-key rule rather than what `created_at` itself requires. The existing span already stated the full rule (created_at.* and updated_at.*), so the boundary was not expanded.

**Status.** `candidate_unverified_after_fix` · human_verified=`false` · frozen=`false`

---

### V2D-05

**Document.** anthropic · Admin · `ver_c299b58fe1f5a4d3a081b550334a7df6`

**Repair reason (ChatGPT).** The source says grouping by speed requires the beta header; it does not state that speed generally requires it. Rewrite the question and claim to preserve the grouping condition.

**Before Q.** What does `speed` require?

**After Q.** What does grouping by `speed` require?

**Before A.** The `fast-mode-2026-02-01` beta header.

**After A.** The `fast-mode-2026-02-01` beta header.

**Before span.** `ver_c299b58fe1f5a4d3a081b550334a7df6` 145736–145804 (68 chars) · `68696c806a8d47853c355ddb31e022ccde229994dda89ac214f51755d8b12e59`

```
Grouping by `speed` requires the `fast-mode-2026-02-01` beta header.
```

**After span.** `ver_c299b58fe1f5a4d3a081b550334a7df6` 145736–145804 (68 chars) · `68696c806a8d47853c355ddb31e022ccde229994dda89ac214f51755d8b12e59`

```
Grouping by `speed` requires the `fast-mode-2026-02-01` beta header.
```

**Span.** unchanged (+0 before, +0 after).

**What changed.** Rewrote question and claim so grouping by `speed` (not `speed` generally) requires the `fast-mode-2026-02-01` beta header. Span unchanged.

**Status.** `candidate_unverified_after_fix` · human_verified=`false` · frozen=`false`

---

### V2D-06

**Document.** anthropic · Fast mode (research preview) · `ver_cc7d6ed2a636d74fc7aca7885ba9ce60`

**Repair reason (ChatGPT).** The selected sentence is qualified by the immediately following Claude Opus 4.6 exception, where a speed=fast request can succeed while usage.speed is standard. The candidate needs that scope or exception.

**Before Q.** What happens when a request with `speed: "fast"` succeeds?

**After Q.** What is `usage.speed` when a request with `speed: "fast"` succeeds, including on Claude Opus 4.6?

**Before A.** `usage.speed` is `"fast"`.

**After A.** It is `"fast"`. Claude Opus 4.6 is an exception: requesting fast mode can succeed while the `speed` field shows `"standard"`.

**Before span.** `ver_cc7d6ed2a636d74fc7aca7885ba9ce60` 9863–9935 (72 chars) · `2d30e610b6255b61fbff2e6e3331557eb3fc865d50dcec703c0e859a24c1fb3a`

```
When a request with `speed: "fast"` succeeds, `usage.speed` is `"fast"`.
```

**After span.** `ver_cc7d6ed2a636d74fc7aca7885ba9ce60` 9863–10222 (359 chars) · `1ae25e4479c1961c3ac649534d70309e9fc4f29a776e49115c2c7e0209f536b4`

```
When a request with `speed: "fast"` succeeds, `usage.speed` is `"fast"`. If you are using Claude Opus 4.6 and request fast mode, its behavior is unique. Instead of returning an error like other models that don't support fast mode, it silently switches to standard speed. Though there is no error with Opus 4.6, the `speed` field accurately shows `"standard"`.
```

**Span.** expanded (+0 before, +287 after).

**What changed.** Included the Claude Opus 4.6 exception in the question, answer, and claims. Expanded the evidence boundary forward to that following exception (speed=fast can succeed while usage.speed is standard).

**Status.** `candidate_unverified_after_fix` · human_verified=`false` · frozen=`false`

---

### V2D-08

**Document.** anthropic · Beta · `ver_de7f74230c8f10d30aea5d037a3bd0a5`

**Repair reason (ChatGPT).** The factual description is supported, but the question is malformed and omits the field being defined, allowed_fallback_models. The field name is needed to bind the description to the correct return value.

**Before Q.** What does Model IDs this model accept?

**After Q.** What does `allowed_fallback_models` contain?

**Before A.** Model IDs this model accepts as `fallbacks[i].model` on the Messages API.

**After A.** Model IDs this model accepts as `fallbacks[i].model` on the Messages API.

**Before span.** `ver_de7f74230c8f10d30aea5d037a3bd0a5` 8860–8937 (77 chars) · `95982f914e9d0e93a07148156b3808869ecfaf8c4d28544d5aaee396d016d88b`

```
    Model IDs this model accepts as `fallbacks[i].model` on the Messages API.
```

**After span.** `ver_de7f74230c8f10d30aea5d037a3bd0a5` 8804–8937 (133 chars) · `a71662214aeb083e40ff4eed5dc1eec7fe7cb4ea3925ff888836afefcb19386c`

```
  - `allowed_fallback_models: array of string or null`

    Model IDs this model accepts as `fallbacks[i].model` on the Messages API.
```

**Span.** expanded (+56 before, +0 after).

**What changed.** Named the omitted field `allowed_fallback_models` in the question. Expanded the evidence boundary backwards to the field name.

**Status.** `candidate_unverified_after_fix` · human_verified=`false` · frozen=`false`

---

### V2D-13

**Document.** openai · Models · `ver_ae909bf8b4bbbe1d1a11119447f7ac94`

**Repair reason (ChatGPT).** The answer is supported, but the question 'What does betas override?' misstates the relation. The source says the model rejects caller-supplied betas overrides along with reasoning.summary and max_tool_calls.

**Before Q.** What does `betas` override?

**After Q.** What does the experimental model reject?

**Before A.** The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.

**After A.** `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.

**Before span.** `ver_ae909bf8b4bbbe1d1a11119447f7ac94` 19331–19456 (125 chars) · `540a39028df8184945b1d598976982b6092e1c52dbb919d3c009f6d5df2ccad0`

```
The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.
```

**After span.** `ver_ae909bf8b4bbbe1d1a11119447f7ac94` 19331–19456 (125 chars) · `540a39028df8184945b1d598976982b6092e1c52dbb919d3c009f6d5df2ccad0`

```
The experimental model rejects `reasoning.summary`, `max_tool_calls`, and caller-supplied `multi_agent` or `betas` overrides.
```

**Span.** unchanged (+0 before, +0 after).

**What changed.** RELATION_DIRECTION fix: the question no longer asks what `betas` override. Subject is the experimental model; relation is rejects; object is the listed overrides. Span unchanged.

**Status.** `candidate_unverified_after_fix` · human_verified=`false` · frozen=`false`

---

### V2D-18

**Document.** openai · Testing · `ver_d2295786320b2815477eb963eb1f5e8a`

**Repair reason (ChatGPT).** The factual statement is supported, but 'the Python helper' is not identified in the question or selected evidence. The surrounding section indicates ModelStep.raise_error; name that helper explicitly.

**Before Q.** What does the Python helper accept?

**After Q.** What does `ModelStep.raise_error` accept?

**Before A.** The Python helper accepts a fixed `ModelRetryAdvice` value; use a custom `Model` when retry advice itself must vary dynamically by attempt.

**After A.** A fixed `ModelRetryAdvice` value; use a custom `Model` when retry advice itself must vary dynamically by attempt.

**Before span.** `ver_d2295786320b2815477eb963eb1f5e8a` 9711–9850 (139 chars) · `98f949d187d774cf689478066c3b8933a2327a701129539680d5ae21bd9af9c6`

```
The Python helper accepts a fixed `ModelRetryAdvice` value; use a custom `Model` when retry advice itself must vary dynamically by attempt.
```

**After span.** `ver_d2295786320b2815477eb963eb1f5e8a` 9219–9850 (631 chars) · `5eaa435ade77face5566e2a959ab20237247f93384c38b64c1f79cdf4cea24d3`

```
Use `ModelStep.raise_error()` to fail one model call. Optional retry advice belongs to that exact scripted error:

```python
from agents import ModelRetryAdvice
from agents.testing import ModelStep


step = ModelStep.raise_error(
    RuntimeError("temporary failure"),
    retry_advice=ModelRetryAdvice(suggested=True, replay_safety="safe"),
)
```

The runner's retry policy decides whether advice causes another attempt. Each retry is another model call and consumes the next scripted step. The Python helper accepts a fixed `ModelRetryAdvice` value; use a custom `Model` when retry advice itself must vary dynamically by attempt.
```

**Span.** expanded (+492 before, +0 after).

**What changed.** Replaced 'the Python helper' with `ModelStep.raise_error`. Expanded the evidence boundary backwards so the helper name is inside the span.

**Status.** `candidate_unverified_after_fix` · human_verified=`false` · frozen=`false`

---

### V2D-19

**Document.** anthropic · Using Agent Skills with the API · `ver_5a15a8f543d432ef91eb6e2997f51225`

**Repair reason (ChatGPT).** The underlying files_from_dir fact is supported, but the proposed question is grammatically malformed. Rewrite it as what argument files_from_dir accepts.

**Before Q.** What does the Python SDK also provides a `files_from_dir` helper that accept?

**After Q.** What argument does `files_from_dir` accept?

**Before A.** The Python SDK also provides a `files_from_dir` helper that accepts a directory path.

**After A.** A directory path.

**Before span.** `ver_5a15a8f543d432ef91eb6e2997f51225` 72650–72735 (85 chars) · `dcf16d18e94cb433a7aa16e08368cde0eaafaf15f6738dc5db9363ca67bf9f3a`

```
The Python SDK also provides a `files_from_dir` helper that accepts a directory path.
```

**After span.** `ver_5a15a8f543d432ef91eb6e2997f51225` 72650–72735 (85 chars) · `dcf16d18e94cb433a7aa16e08368cde0eaafaf15f6738dc5db9363ca67bf9f3a`

```
The Python SDK also provides a `files_from_dir` helper that accepts a directory path.
```

**Span.** unchanged (+0 before, +0 after).

**What changed.** Grammatical rewrite: the question now asks what argument `files_from_dir` accepts. Span unchanged.

**Status.** `candidate_unverified_after_fix` · human_verified=`false` · frozen=`false`

---

### V2D-21

**Document.** anthropic · Memory tool · `ver_96d1698a3864f79451e8576f87a07004`

**Repair reason (ChatGPT).** The recommendation is supported, but the proposed question is malformed. Ask how to handle large view output or what safeguard is recommended for the view command.

**Before Q.** What does Consider capping how many characters the `view` command return?

**After Q.** How should large `view` output be limited, and how can Claude page through the rest with `view_range`?

**Before A.** Consider capping how many characters the `view` command returns, and let Claude page through the rest with `view_range`.

**After A.** Cap how many characters the `view` command returns, and let Claude page through the rest with `view_range`.

**Before span.** `ver_96d1698a3864f79451e8576f87a07004` 34903–35023 (120 chars) · `829b4270435161f75e29c18c666d040ecac6c5820aeea5bc33c8c65c9b51092b`

```
Consider capping how many characters the `view` command returns, and let Claude page through the rest with `view_range`.
```

**After span.** `ver_96d1698a3864f79451e8576f87a07004` 34903–35023 (120 chars) · `829b4270435161f75e29c18c666d040ecac6c5820aeea5bc33c8c65c9b51092b`

```
Consider capping how many characters the `view` command returns, and let Claude page through the rest with `view_range`.
```

**Span.** unchanged (+0 before, +0 after).

**What changed.** Rewrote the malformed question as the recommended safeguard: limit `view` output and page through the rest with `view_range`. Span unchanged.

**Status.** `candidate_unverified_after_fix` · human_verified=`false` · frozen=`false`

---

### V2D-22

**Document.** anthropic · Tool runner (SDK) · `ver_96d5aba3c4e7771cabd4f3d4f5a3fff1`

**Repair reason (ChatGPT).** The statement about next_message is supported, but the question is malformed. Rewrite as 'What has already been appended by the time next_message returns?'

**Before Q.** What does By the time `next_message` return?

**After Q.** What has already been appended by the time `next_message` returns?

**Before A.** By the time `next_message` returns, the assistant message and tool result for that turn are already appended.

**After A.** The assistant message and tool result for that turn.

**Before span.** `ver_96d5aba3c4e7771cabd4f3d4f5a3fff1` 38316–38425 (109 chars) · `cc4be65021e4ea3f13b4ad9ce60d23942d2d0ec76c0c46663fd82d8025ee4224`

```
By the time `next_message` returns, the assistant message and tool result for that turn are already appended.
```

**After span.** `ver_96d5aba3c4e7771cabd4f3d4f5a3fff1` 38316–38425 (109 chars) · `cc4be65021e4ea3f13b4ad9ce60d23942d2d0ec76c0c46663fd82d8025ee4224`

```
By the time `next_message` returns, the assistant message and tool result for that turn are already appended.
```

**Span.** unchanged (+0 before, +0 after).

**What changed.** Rewrote the malformed question to 'What has already been appended by the time `next_message` returns?'. Span unchanged.

**Status.** `candidate_unverified_after_fix` · human_verified=`false` · frozen=`false`

---

### V2D-23

**Document.** openai · Sandbox clients · `ver_3d4b8881962381cbfba18ade50c598e1`

**Repair reason (ChatGPT).** The answer is exactly supported, but the question should be grammatically corrected to 'What are credentialless rclone mounts limited to?' No factual change is needed.

**Before Q.** What is Credentialless `rclone` mounts limited to?

**After Q.** What are credentialless `rclone` mounts limited to?

**Before A.** Credentialless `rclone` mounts are limited to S3, GCS, R2, and Azure Blob.

**After A.** S3, GCS, R2, and Azure Blob.

**Before span.** `ver_3d4b8881962381cbfba18ade50c598e1` 10824–11465 (641 chars) · `b97014844240948026e9df02c8b13569c24b56a95ddfab31721fb318fdd150a1`

```
Credentialless `rclone` mounts are limited to S3, GCS, R2, and Azure Blob. An in-container Box mount requires a non-interactive authentication source and the acknowledgement that matches that source. `FuseMountPattern` requires broad acknowledgement because `blobfuse2` discovers ambient Azure authority, even when no inline credential is configured. `S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses ambient IAM authority. These requirements also apply when Docker is the backend; the check marks below indicate that Docker can execute the mount after the applicable authority boundary is satisfied.
```

**After span.** `ver_3d4b8881962381cbfba18ade50c598e1` 10824–11465 (641 chars) · `b97014844240948026e9df02c8b13569c24b56a95ddfab31721fb318fdd150a1`

```
Credentialless `rclone` mounts are limited to S3, GCS, R2, and Azure Blob. An in-container Box mount requires a non-interactive authentication source and the acknowledgement that matches that source. `FuseMountPattern` requires broad acknowledgement because `blobfuse2` discovers ambient Azure authority, even when no inline credential is configured. `S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses ambient IAM authority. These requirements also apply when Docker is the backend; the check marks below indicate that Docker can execute the mount after the applicable authority boundary is satisfied.
```

**Span.** unchanged (+0 before, +0 after).

**What changed.** Grammar only: 'What are credentialless `rclone` mounts limited to?'. No factual change. Span unchanged.

**Status.** `candidate_unverified_after_fix` · human_verified=`false` · frozen=`false`

---

### V2D-32

**Document.** anthropic · MCP tunnels quickstart · `ver_067b3bfdc28f24500ea19b97bf3e80b1`

**Repair reason (ChatGPT).** The proposed answer is supported as an installation/PATH statement, but the broad question 'What must openssl be?' omits the adjacent requirement that OpenSSL be version 1.1.1 or later. Narrow the question to Windows installation/PATH or include the version requirement.

**Before Q.** What must `openssl` be?

**After Q.** What OpenSSL version is required, and what is required of the `openssl` binary on Windows?

**Before A.** Preinstalled on macOS and most Linux distributions; on Windows, install it separately (the `openssl` binary must be on your `PATH`).

**After A.** OpenSSL 1.1.1 or later. On Windows, install it separately (the `openssl` binary must be on your `PATH`).

**Before span.** `ver_067b3bfdc28f24500ea19b97bf3e80b1` 1857–1989 (132 chars) · `a73bb959f95532e95f81c5b7ca24d8e14fa3a92af229fc7e0305755d80dedd37`

```
Preinstalled on macOS and most Linux distributions; on Windows, install it separately (the `openssl` binary must be on your `PATH`).
```

**After span.** `ver_067b3bfdc28f24500ea19b97bf3e80b1` 1792–1989 (197 chars) · `64a21c31843c3819f9bbf9e1f235df92d9bd00f21a0df635c4c8c8bf9814082e`

```
* [OpenSSL](https://openssl-library.org/source/) 1.1.1 or later. Preinstalled on macOS and most Linux distributions; on Windows, install it separately (the `openssl` binary must be on your `PATH`).
```

**Span.** expanded (+65 before, +0 after).

**What changed.** Included the adjacent OpenSSL 1.1.1 or later version requirement and narrowed the Windows part to install/PATH. Expanded the evidence boundary backwards to the start of that bullet.

**Status.** `candidate_unverified_after_fix` · human_verified=`false` · frozen=`false`

---

### V2D-33

**Document.** openai · Running agents · `ver_2c60e99cfd929a738910b893fd6f1a40`

**Repair reason (ChatGPT).** The fact is supported, but 'the three Runner methods above' is a deictic dependency on preceding text. Name Runner.run, Runner.run_sync, and Runner.run_streamed or otherwise make the question self-contained.

**Before Q.** What happens when you call any of the three `Runner` methods above?

**After Q.** What do you pass in when you call `Runner.run`, `Runner.run_sync`, or `Runner.run_streamed`?

**Before A.** You pass in a starting agent and input.

**After A.** A starting agent and input.

**Before span.** `ver_2c60e99cfd929a738910b893fd6f1a40` 1039–1133 (94 chars) · `81aad2cf94487959520dc00de693cf7bfe8d949944ce1ca33ff88e899bc7d926`

```
When you call any of the three `Runner` methods above, you pass in a starting agent and input.
```

**After span.** `ver_2c60e99cfd929a738910b893fd6f1a40` 82–1133 (1051 chars) · `8dcd14030925dca2775dd03788cf65e7c62691ba478dcbf4bfffcd9fb8555efe`

```
You have 3 options:

1. [`Runner.run()`][agents.run.Runner.run], which runs async and returns a [`RunResult`][agents.result.RunResult].
2. [`Runner.run_sync()`][agents.run.Runner.run_sync], which is a sync method and just runs `.run()` under the hood.
3. [`Runner.run_streamed()`][agents.run.Runner.run_streamed], which runs async and returns a [`RunResultStreaming`][agents.result.RunResultStreaming]. It calls the LLM in streaming mode, and streams those events to you as they are received.

```python
from agents import Agent, Runner

async def main():
    agent = Agent(name="Assistant", instructions="You are a helpful assistant")

    result = await Runner.run(agent, "Write a haiku about recursion in programming.")
    print(result.final_output)
    # Code within the code,
    # Functions calling themselves,
    # Infinite loop's dance
```

Read more in the [results guide](results.md).

## Runner lifecycle and configuration

### The agent loop

When you call any of the three `Runner` methods above, you pass in a starting agent and input.
```

**Span.** expanded (+957 before, +0 after).

**What changed.** Replaced 'the three Runner methods above' with `Runner.run`, `Runner.run_sync`, and `Runner.run_streamed`. Expanded the evidence boundary backwards to the list that names those methods.

**Status.** `candidate_unverified_after_fix` · human_verified=`false` · frozen=`false`

---

### V2D-37

**Document.** openai · OpenAI Python API library · `ver_9247e3ce4df6f79d9cadc44e1a3bbd0c`

**Repair reason (ChatGPT).** The surrounding sentence establishes that this asynchronous file-reading behavior is for the async client. The proposed question omits that scope and therefore overgeneralizes PathLike behavior.

**Before Q.** What happens if you pass a `PathLike` instance?

**After Q.** What happens if you pass a `PathLike` instance to the async client?

**Before A.** The file contents will be read asynchronously automatically.

**After A.** The file contents will be read asynchronously automatically.

**Before span.** `ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` 14166–14318 (152 chars) · `c7de0d42f68c2ceb6a1330b77e0017d9ab086e08594d5fa83b86ffb3dcd8f616`

```
If you pass a [`PathLike`](https://docs.python.org/3/library/os.html#os.PathLike) instance, the file contents will be read asynchronously automatically.
```

**After span.** `ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` 14118–14318 (200 chars) · `21ffcc2671568c84ca6000e864412e9b44513168e97b389e665b6d7d266660c4`

```
The async client uses the exact same interface. If you pass a [`PathLike`](https://docs.python.org/3/library/os.html#os.PathLike) instance, the file contents will be read asynchronously automatically.
```

**Span.** expanded (+48 before, +0 after).

**What changed.** Scoped PathLike async file-reading to the async client. Expanded the evidence boundary backwards to the sentence that names the async client.

**Status.** `candidate_unverified_after_fix` · human_verified=`false` · frozen=`false`

---

### V2D-38

**Document.** anthropic · Prompting Claude Opus 4.8 · `ver_997f51c850a46243a541d4f4ec4175ce`

**Repair reason (ChatGPT).** The claim is supported in context, but both evidence and answer rely on the unresolved phrase 'this approach,' which refers to having the model propose visual options before building. State that approach explicitly.

**Before Q.** What happens if you previously relied on `temperature` for design variety?

**After Q.** If you previously relied on `temperature` for design variety, what approach should you use?

**Before A.** Use this approach; it produces meaningfully different directions across runs.

**After A.** Have the model propose distinct visual directions before building; it produces meaningfully different directions across runs.

**Before span.** `ver_997f51c850a46243a541d4f4ec4175ce` 10771–10910 (139 chars) · `7c2fd69c00251dc123c3e60ad91560edb0c223b0bc9b752fea3a71656310c284`

```
If you previously relied on `temperature` for design variety, use this approach; it produces meaningfully different directions across runs.
```

**After span.** `ver_997f51c850a46243a541d4f4ec4175ce` 10667–11143 (476 chars) · `09f3c3638c60eeec22566369ef433f2115e9129d79ba3f009561c626dea03d0e`

```
**2. Have the model propose options before building.** This breaks the default and gives users control. If you previously relied on `temperature` for design variety, use this approach; it produces meaningfully different directions across runs. Example prompt:

```text wrap
Before building, propose 4 distinct visual directions tailored to this brief (each as: bg hex / accent hex / typeface — one-line rationale). Ask the user to pick one, then implement only that direction.
```

**Span.** expanded (+104 before, +233 after).

**What changed.** Replaced 'this approach' with the explicit approach: having the model propose distinct visual directions before building. Expanded the evidence boundary to the heading that names the approach and the following example prompt that states 'distinct visual directions'.

**Status.** `candidate_unverified_after_fix` · human_verified=`false` · frozen=`false`

---

### V2D-44

**Document.** openai · Usage · `ver_f8002fe268b970eaea8d640f9dd91fb3`

**Repair reason (ChatGPT).** The include_usage requirement is supported, but the proposed question is grammatically malformed. Rewrite it to ask what setting to add when a streaming Chat Completions provider requires an explicit usage request.

**Before Q.** What does When a streaming Chat Completions provider require?

**After Q.** What setting should you add when a streaming Chat Completions provider requires an explicit usage request?

**Before A.** When a streaming Chat Completions provider requires an explicit usage request, also set `ModelSettings(include_usage=True)`.

**After A.** `ModelSettings(include_usage=True)`.

**Before span.** `ver_f8002fe268b970eaea8d640f9dd91fb3` 4145–4269 (124 chars) · `aa1600091e56a6fb15309b79c17b992e67cc4085d7646a6efee636dcd1233185`

```
When a streaming Chat Completions provider requires an explicit usage request, also set `ModelSettings(include_usage=True)`.
```

**After span.** `ver_f8002fe268b970eaea8d640f9dd91fb3` 4145–4269 (124 chars) · `aa1600091e56a6fb15309b79c17b992e67cc4085d7646a6efee636dcd1233185`

```
When a streaming Chat Completions provider requires an explicit usage request, also set `ModelSettings(include_usage=True)`.
```

**Span.** unchanged (+0 before, +0 after).

**What changed.** Rewrote the malformed question to ask what setting to add when a streaming Chat Completions provider requires an explicit usage request. Span unchanged.

**Status.** `candidate_unverified_after_fix` · human_verified=`false` · frozen=`false`

---

### V2D-50

**Document.** openai · Models · `ver_ae909bf8b4bbbe1d1a11119447f7ac94`

**Repair reason (ChatGPT).** The claim is supported in its section, but 'in this way' is not self-contained and depends on the preceding default-model/RunConfig setup. Rewrite the question to state the configuration path explicitly.

**Before Q.** What happens when you use any GPT-5 model such as `gpt-5.6-sol` in this way?

**After Q.** What happens when you use any GPT-5 model such as `gpt-5.6-sol` as the default model via `OPENAI_DEFAULT_MODEL` or `RunConfig`?

**Before A.** The SDK applies default `ModelSettings`.

**After A.** The SDK applies default `ModelSettings`.

**Before span.** `ver_ae909bf8b4bbbe1d1a11119447f7ac94` 3271–3375 (104 chars) · `90191bc8cb47183770e60952c57e4dd9b388d30ff0fdebb418a7942a8a17ba2b`

```
When you use any GPT-5 model such as `gpt-5.6-sol` in this way, the SDK applies default `ModelSettings`.
```

**After span.** `ver_ae909bf8b4bbbe1d1a11119447f7ac94` 2486–3375 (889 chars) · `3e90577101dbe3584f6f6f92526744d5e3647d579b627f00d30006d04cd7db81`

```
If you want to switch to other models like `gpt-5.6-sol`, there are two ways to configure your agents.

### Default model

First, if you want to consistently use a specific model for all agents that do not set a custom model, set the `OPENAI_DEFAULT_MODEL` environment variable before running your agents.

```bash
export OPENAI_DEFAULT_MODEL=gpt-5.6-sol
python3 my_awesome_agent.py
```

Second, you can set a default model for a run via `RunConfig`. If you don't set a model for an agent, this run's model will be used.

```python
from agents import Agent, RunConfig, Runner

agent = Agent(
    name="Assistant",
    instructions="You're a helpful agent.",
)

result = await Runner.run(
    agent,
    "Hello",
    run_config=RunConfig(model="gpt-5.6-sol"),
)
```

#### GPT-5 models

When you use any GPT-5 model such as `gpt-5.6-sol` in this way, the SDK applies default `ModelSettings`.
```

**Span.** expanded (+785 before, +0 after).

**What changed.** Replaced 'in this way' with the explicit default-model / `RunConfig` configuration path. Expanded the evidence boundary backwards to that path.

**Status.** `candidate_unverified_after_fix` · human_verified=`false` · frozen=`false`

---

## Files

- `experiments/RAG-V2/V2-DEVSET-001/V2-DEVSET-001-repair-report.md` (this file)
- `experiments/RAG-V2/V2-DEVSET-001/V2-DEVSET-001-repaired-candidates.jsonl`
- `evals/review/v2_devset_001_repairs_round1.md` (ChatGPT-ready review of the 16 only)
- `/home/box/Downloads/v2_devset_001_repairs_round1.md` (copy of the ChatGPT-ready md)
- copies: `experiments/RAG-V2/V2-DEVSET-001/v2_devset_001_repairs_round1.json` and `.md`

Original 50-case packet `evals/review/v2_devset_001_batch_001.json` was not mutated.
