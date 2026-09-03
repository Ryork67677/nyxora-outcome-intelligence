# V2-DEVSET-001 review packet (batch 101)

**18 candidates (slice2_of_3: V2D-19–V2D-36 of 50) · corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · generated 2026-09-01T02:20:09Z (2026-08-31 22:20 ET)**

Nothing in this file is ground truth. Every candidate is `candidate_unverified`. The evidence below is quoted verbatim from the frozen corpus and is authoritative for this review — **do not consult live documentation**, which may have changed since the snapshot.

For each candidate, judge the *proposed* question, answer and claims against the evidence and its surrounding context only. Return one record per candidate with verdict `PASS | FAIL | FIX_REQUIRED | UNCERTAIN` and the GOLD review fields in `docs/GOLD-REVIEW-PROCEDURE.md`.

ID prefix `V2D-`. This is a v2 **development** candidate set, not frozen gold, not gold150-v1 holdout, and not gold150-v1 validation.

---

## V2D-19

- **provider**: anthropic
- **document**: Using Agent Skills with the API
- **section**: Managing custom Skills › Creating a Skill
- **source span**: `ver_5a15a8f543d432ef91eb6e2997f51225` chars 72650–72735
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, lexical_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does the Python SDK also provides a `files_from_dir` helper that accept?

**Proposed answer**: The Python SDK also provides a `files_from_dir` helper that accepts a directory path.

**Proposed atomic claims**: The Python SDK also provides a `files_from_dir` helper that accepts a directory path.

**Critical strings**: files_from_dir

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_5a15a8f543d432ef91eb6e2997f51225` chars 72650–72735 · hash `dcf16d18e94cb433…`

```
The Python SDK also provides a `files_from_dir` helper that accepts a directory path.
```

<details><summary>Context before</summary>

```
m",
          skill_id: "skill_01AbCdEfGhIjKlMnOpQrStUv",
          version: "latest"
        }
      ]
    },
    messages: [
      { role: "user", content: "Analyze sales data and create a presentation" }
    ],
    tools: [
      { type: "code_execution_20250825", name: "code_execution" }
    ]
  )
  puts message
  ```
</CodeGroup>

***

## Managing custom Skills

### Creating a Skill

A Skill bundle is a directory containing a `SKILL.md` file at the top level with `name` and `description` YAML frontmatter, plus any supporting scripts or resources. See [Get started with Agent Skills in the API](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/quickstart) to author one, and the **Requirements** list following the examples for the full constraints.

Upload your custom Skill to make it available in your workspace. You can upload a zip archive or individual file objects. 
```

</details>

<details><summary>Context after</summary>

```


Files are identified by the filename you attach. Per-file uploads must keep a common top-level directory in their paths (the `;filename=` suffix in the cURL example and the filename arguments in the SDK examples). A zip archive must contain the skill directory as its single top-level entry. For the walkthrough's skill, create one with `zip -r financial_skill.zip financial_skill/` and substitute it for the `example_skill.zip` placeholder in the zip-upload options.

<CodeGroup defaultLanguage="CLI">
  ```bash cURL
  curl -X POST "https://api.anthropic.com/v1/skills" \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "anthropic-beta: skills-2025-10-02" \
    -F "files[]=@financial_skill/SKILL.md;filename=financial_skill/SKILL.md" \
    -F "files[]=@financial_skill/analyze.py;filename=financial_skill/analyze.py"
  ```

  ```bash CLI
  ant beta:skills
```

</details>

---

## V2D-20

- **provider**: anthropic
- **document**: Claude Platform on AWS
- **section**: Data residency
- **source span**: `ver_5ebdc722f9bedb1e2e8cbd3f29ff6805` chars 47753–47880
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `configuration_interaction`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, lexical_query_shape, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens if you omit `inference_geo`?

**Proposed answer**: The request uses the workspace's `default_inference_geo` if one is configured, otherwise `global`.

**Proposed atomic claims**: If you omit `inference_geo`, the request uses the workspace's `default_inference_geo` if one is configured, otherwise `global`.

**Critical strings**: inference_geo, default_inference_geo, global

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_5ebdc722f9bedb1e2e8cbd3f29ff6805` chars 47753–47880 · hash `44d2362efd094347…`

```
If you omit `inference_geo`, the request uses the workspace's `default_inference_geo` if one is configured, otherwise `global`.
```

<details><summary>Context before</summary>

```
mEnv())
          .build();

      Message message = client.messages().create(
          MessageCreateParams.builder()
              .model(Model.CLAUDE_SONNET_5)
              .maxTokens(1024)
              .inferenceGeo("us")
              .addUserMessage("Hello!")
              .build()
      );

      IO.println(message);
  }
  ```

  ```php PHP
  use Anthropic\Aws\Client;

  $client = new Client();

  $message = $client->messages->create(
      model: 'claude-sonnet-5',
      maxTokens: 1024,
      inferenceGeo: 'us',
      messages: [['role' => 'user', 'content' => 'Hello!']],
  );

  echo $message;
  ```

  ```ruby Ruby
  require "anthropic"

  client = Anthropic::AWSClient.new

  message = client.messages.create(
    model: "claude-sonnet-5",
    max_tokens: 1024,
    inference_geo: "us",
    messages: [{ role: "user", content: "Hello!" }]
  )

  puts message
  ```
</CodeGroup>


```

</details>

<details><summary>Context after</summary>

```


Workspace-level inference geography controls (`allowed_inference_geos` and `default_inference_geo`) are also available on Claude Platform on AWS. See [Workspace-level restrictions](https://platform.claude.com/docs/en/manage-claude/data-residency#workspace-level-restrictions).

## Workspaces

Inference and resource requests on Claude Platform on AWS target a workspace. You pass the workspace's ID in the `anthropic-workspace-id` header on these API calls. Workspace IDs use the tagged format `wrkspc_` followed by an alphanumeric identifier (for example, `wrkspc_01AbCdEf23GhIj`). See [Obtain your workspace ID](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws#obtain-your-workspace-id) if you don't have it yet.

### Workspace scoping

Workspaces are bound to a single AWS region. A workspace created in `us-west-2` can only be accessed through the `us-west-2` endpoi
```

</details>

---

## V2D-21

- **provider**: anthropic
- **document**: Memory tool
- **section**: Security considerations › File storage size
- **source span**: `ver_96d1698a3864f79451e8576f87a07004` chars 34903–35023
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `error_behavior`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, version_model_discrimination, identifier_vs_semantic_distractor
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does Consider capping how many characters the `view` command return?

**Proposed answer**: Consider capping how many characters the `view` command returns, and let Claude page through the rest with `view_range`.

**Proposed atomic claims**: Consider capping how many characters the `view` command returns, and let Claude page through the rest with `view_range`.

**Critical strings**: view, view_range

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_96d1698a3864f79451e8576f87a07004` chars 34903–35023 · hash `829b4270435161f7…`

```
Consider capping how many characters the `view` command returns, and let Claude page through the rest with `view_range`.
```

<details><summary>Context before</summary>

```
to repeat that instruction. If Claude still creates cluttered memory files, you can reinforce it in your prompt:

```text wrap
Note: when editing your memory folder, always try to keep its content up-to-date, coherent and organized. You can rename or delete files that are no longer relevant. Do not create new files unless necessary.
```

You can also guide what Claude writes to memory. For example: "Only write down information relevant to \<topic> in your memory system."

## Security considerations

Your application executes every file operation Claude requests, so these safeguards are your responsibility:

### Sensitive information

Claude usually refuses to write sensitive information to memory files. For stronger guarantees, add validation that strips sensitive data before your handler writes the file.

### File storage size

Track memory file sizes and cap how large a file can grow. 
```

</details>

<details><summary>Context after</summary>

```


### Memory expiration

Periodically delete memory files that haven't been accessed in a long time.

### Path traversal protection

<Warning>
  A malicious path such as `/memories/../../secrets.env` can reach files outside the `/memories` directory. Your implementation must validate every path in every command to prevent directory traversal attacks.
</Warning>

Consider these safeguards:

* Validate that all paths start with `/memories`
* Resolve paths to their canonical form and verify they remain within the memory directory
* Reject paths containing sequences such as `../`, `..\\`, or other traversal patterns
* Watch for URL-encoded traversal sequences (`%2e%2e%2f`)
* Use your language's built-in path security utilities (for example, Python's `pathlib.Path.resolve()` and `relative_to()`)

## Error handling

The memory tool uses similar error-handling patterns to the [text editor tool]
```

</details>

---

## V2D-22

- **provider**: anthropic
- **document**: Tool runner (SDK)
- **section**: Advanced usage › Taking over message history
- **source span**: `ver_96d5aba3c4e7771cabd4f3d4f5a3fff1` chars 38316–38425
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `error_behavior`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, lexical_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does By the time `next_message` return?

**Proposed answer**: By the time `next_message` returns, the assistant message and tool result for that turn are already appended.

**Proposed atomic claims**: By the time `next_message` returns, the assistant message and tool result for that turn are already appended.

**Critical strings**: next_message

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_96d5aba3c4e7771cabd4f3d4f5a3fff1` chars 38316–38425 · hash `cc4be65021e4ea3f…`

```
By the time `next_message` returns, the assistant message and tool result for that turn are already appended.
```

<details><summary>Context before</summary>

```
 === BetaStopReason::MAX_TOKENS->value) {
            $current = $runner->getParams()['maxTokens'];

            if ($current >= $maxTokenCeiling) {
                echo "Hit ceiling ({$maxTokenCeiling}), accepting truncated response.\n";
                break;
            }

            $doubled = min($current * 2, $maxTokenCeiling);
            echo "Response truncated at {$current} tokens, retrying with {$doubled}.\n";

            // Calling setMessagesParams() inside the loop tells the runner to skip
            // its automatic append. The truncated message is discarded; the next
            // iteration retries with the larger budget.
            // Keys are camelCase, matching the toolRunner() named parameters.
            $runner->setMessagesParams(['maxTokens' => $doubled]);
        }
    }
    ```
  </Tab>

  <Tab title="Ruby">
    Use `next_message` for step-by-step control. 
```

</details>

<details><summary>Context after</summary>

```
 Use `feed_messages` to inject follow-up messages between turns, and `runner.params.update(...)` to change request parameters in place.

    You take over message history when, from inside an `each_message` or `each_streaming` block, you reassign `runner.params[:messages]` or call `feed_messages`. The following pattern calls `feed_messages` between `next_message` calls, which does not take over.

    ```ruby
    runner = client.beta.messages.tool_runner(
      model: "claude-opus-5",
      max_tokens: 1024,
      max_iterations: 10,
      tools: [GetWeather.new],
      messages: [{role: "user", content: "What's the weather in San Francisco?"}]
    )

    # Step the runner once. The assistant message and tool result are appended
    # to runner.params[:messages] before next_message returns.
    message = runner.next_message
    puts message.content

    # Inject a follow-up before continu
```

</details>

---

## V2D-23

- **provider**: openai
- **document**: Sandbox clients
- **section**: Sandbox clients › Supported hosted platforms › Size Modal sandboxes
- **source span**: `ver_3d4b8881962381cbfba18ade50c598e1` chars 10824–11465
- **evidence kind**: `long_technical_section`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: long_technical_section, correct_document_difficult_passage, identifier_vs_semantic_distractor
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What is Credentialless `rclone` mounts limited to?

**Proposed answer**: Credentialless `rclone` mounts are limited to S3, GCS, R2, and Azure Blob.

**Proposed atomic claims**: `Credentialless `rclone` mounts are limited to S3, GCS, R2, and Azure Blob.`

**Critical strings**: rclone, FuseMountPattern, blobfuse2

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_3d4b8881962381cbfba18ade50c598e1` chars 10824–11465 · hash `b970148442409480…`

```
Credentialless `rclone` mounts are limited to S3, GCS, R2, and Azure Blob. An in-container Box mount requires a non-interactive authentication source and the acknowledgement that matches that source. `FuseMountPattern` requires broad acknowledgement because `blobfuse2` discovers ambient Azure authority, even when no inline credential is configured. `S3FilesMountPattern` likewise requires broad acknowledgement because `mount.s3files` uses ambient IAM authority. These requirements also apply when Docker is the backend; the check marks below indicate that Docker can execute the mount after the applicable authority boundary is satisfied.
```

<details><summary>Context before</summary>

```
BlobMount`, and `BoxMount`. |
| `VercelSandboxClient` | Supports create-time-only S3 and S3-compatible bucket mounts by pairing `VercelCloudBucketMountStrategy` with an `S3Mount` entry; mounted sessions cannot be resumed, and inline credentials require `allow_s3_credential_exposure=True`. |

</div>

The mount tables describe which storage types each backend can execute. A check mark does not bypass the credential boundary for a mount helper that runs inside a model-controlled sandbox, and it does not mean that every strategy can operate without credentials. The Agents SDK accepts an in-container mount without an acknowledgement only when the selected helper can operate without protected authority. It rejects a mount that requires protected authority before starting the sandbox or mount helper unless trusted application code explicitly acknowledges the exposure for the exact mount path.


```

</details>

<details><summary>Context after</summary>

```


For a mount entry named `"data"`, retain the copied `Manifest` returned by the acknowledgement that matches the configured authority:

```python
# Mount-scoped values such as inline access keys.
manifest = manifest.with_in_container_mount_credential_exposure_acknowledged("data")

# Broader authority such as managed or workload identity and external credential files.
manifest = manifest.with_in_container_mount_broad_credential_exposure_acknowledged("data")
```

Pass every exact mount path that needs the acknowledgement. A mount that uses both authority classes requires both acknowledgements. The acknowledgements are runtime-only, are not serialized, and permit the helper to receive credentials without confining credential use to the mounted path. Prefer an external or provider-native strategy when available, and otherwise use sandbox-scoped, short-lived, least-privilege credentials.

`V
```

</details>

---

## V2D-24

- **provider**: anthropic
- **document**: Migration guide
- **section**: Opus migration › What changed
- **source span**: `ver_a7bda3595f2c124605c3228464d4ee52` chars 54954–55610
- **evidence kind**: `long_technical_section`
- **evidence shape**: `single_span`
- **reasoning type**: `error_behavior`
- **stress types**: long_technical_section, correct_document_difficult_passage, version_model_discrimination, parameter_error_literal_lookup, same_document_passage_discrimination
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does Claude Opus 4.7 reject?

**Proposed answer**: Claude Opus 4.7 rejects `role: "system"` in `messages` with a 400 error.

**Proposed atomic claims**: `Claude Opus 4.7 rejects `role: "system"` in `messages` with a 400 error.`

**Critical strings**: messages, system

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_a7bda3595f2c124605c3228464d4ee52` chars 54954–55610 · hash `47f0ae4b3a03eda2…`

```
5. **Mid-conversation system messages:** Claude Opus 5 accepts `role: "system"` messages immediately after a user turn in the `messages` array (subject to [placement rules](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages#limitations)). Use the top-level `system` field for instructions that apply from the start. Claude Opus 4.7 rejects `role: "system"` in `messages` with a 400 error. If you maintain code paths that rebuild the full message history to update instructions, you can simplify them and preserve [prompt cache](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) hits on earlier turns.
```

<details><summary>Context before</summary>

```
ll set of effort levels (`low`, `medium`, `high`, `xhigh`, `max`). Run a fresh effort sweep on your own evals rather than carrying over a setting tuned for Claude Opus 4.7. `low` and `medium` effort are worth testing as cost and latency controls, and test `max` effort where maximum capability matters more than token spend. If you run at `xhigh` or `max` effort, set a large `max_tokens` so the model has room to think and act; start at 64k tokens and tune from there. See [Effort](https://platform.claude.com/docs/en/build-with-claude/effort).

4. **1M context window is the default:** Claude Opus 5 serves the full 1M token [context window](https://platform.claude.com/docs/en/build-with-claude/context-windows) by default with no beta header and no long-context premium. If your client passes a context-window beta header for compatibility with older models, you can remove it on Claude Opus 5.


```

</details>

<details><summary>Context after</summary>

```


6. **Refusal stop details:** The `stop_details` object on refusal responses (available since Claude Opus 4.7) is now publicly documented. When the model declines a request, it identifies the category of refusal, in addition to the existing `refusal` stop reason. No beta header is required, and there is no opt-out. See [Handling stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons).

7. **Lower prompt caching minimum:** The minimum cacheable prompt length on Claude Opus 5 is 512 tokens, lower than on Claude Opus 4.7. Prompts that were too short to cache on Claude Opus 4.7 can now create cache entries, with no code changes required. See [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#cache-limitations) for per-model minimums.

8. **Fast mode:** Claude Opus 5 supports [fast mode](https://platform.claude.com/docs/en
```

</details>

---

## V2D-25

- **provider**: anthropic
- **document**: Admin
- **section**: Service Accounts › Create Service Account
- **source span**: `ver_c299b58fe1f5a4d3a081b550334a7df6` chars 441490–442046
- **evidence kind**: `long_technical_section`
- **evidence shape**: `single_span`
- **reasoning type**: `configuration_interaction`
- **stress types**: long_technical_section, correct_document_difficult_passage, identifier_vs_semantic_distractor
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does Creating an `admin`-role service account require?

**Proposed answer**: Creating an `admin`-role service account requires an interactive credential (a user OAuth token or a Console session) — a workload may only create `developer`-role service accounts.

**Proposed atomic claims**: Creating an `admin`-role service account requires an interactive credential (a user OAuth token or a Console session) — a workload may only create `developer`-role service accounts.

**Critical strings**: organization_role, developer, admin

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_c299b58fe1f5a4d3a081b550334a7df6` chars 441490–442046 · hash `81389e37ebfd6524…`

```
A service account is a named workload identity that federation rules
target. `organization_role` is `developer` (default) or `admin`; a rule
may only be created or retargeted to grant `org:admin` scope when the
target's `organization_role` is `admin`. Requires an OAuth bearer (user
or WIF-minted service account token) or a Console session; Admin API
keys are not accepted. Creating an `admin`-role service account requires
an interactive credential (a user OAuth token or a Console session) — a
workload may only create `developer`-role service accounts.
```

<details><summary>Context before</summary>

```
`"skills"`

      - `"token_count"`

      - `"web_search"`

    - `limits: array of object { type, value }`

      The limiter values that apply to this group.

      - `type: string`

        The limiter type (for example, `requests_per_minute` or `input_tokens_per_minute`).

      - `value: number`

        The configured limit value for this limiter type.

    - `models: array of string or null`

      Model names this entry's limits apply to, including aliases. `null` when `group_type` is not `"model_group"`.

    - `type: "rate_limit"`

      Object type. Always `rate_limit` for organization rate-limit entries.

      - `"rate_limit"`

  - `next_page: string or null`

    Token to provide in as `page` in the subsequent request to retrieve the next page of data.

# Service Accounts

## Create Service Account

**post** `/v1/organizations/service_accounts`

Create a service account.


```

</details>

<details><summary>Context after</summary>

```


### Header Parameters

- `"anthropic-beta": optional array of string`

  Optional header to specify the beta version(s) you want to use.

  To use multiple betas, use a comma separated list like `beta1,beta2` or specify the header multiple times for each beta.

### Body Parameters

- `name: string`

  Slug identifier (lowercase, digits, hyphens). Unique within the organization; a duplicate name returns 409.

- `description: optional string or null`

  Optional free-text description.

- `organization_role: optional "admin" or "developer"`

  Org-level role. Defaults to `developer`.

  - `"admin"`

  - `"developer"`

### Returns

- `ServiceAccount object { id, archived_at, archived_by_actor_id, 8 more }`

  Named non-human identity within the caller's organization.

  A service account is a pure identity: name + org. Authorization lives on
  whatever references it (federation rules).

  
```

</details>

---

## V2D-26

- **provider**: anthropic
- **document**: Code execution tool
- **section**: Model compatibility
- **source span**: `ver_f65938c74d40ac1e288f169d3d0435b7` chars 3697–4899
- **evidence kind**: `long_technical_section`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: long_technical_section, version_model_discrimination, parameter_error_literal_lookup
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does Claude Haiku 4.5 accept?

**Proposed answer**: Claude Haiku 4.5 accepts the `code_execution_20260120` and `code_execution_20260521` tool types, but programmatic tool calling and the REPL state persistence that depends on it aren't available on it, so the newer versions behave like `code_execution_20250825` there.

**Proposed atomic claims**: Claude Haiku 4.5 accepts the `code_execution_20260120` and `code_execution_20260521` tool types, but programmatic tool calling and the REPL state persistence that depends on it aren't available on it, so the newer versions behave like `code_execution_20250825` there.

**Critical strings**: code_execution_20250825, code_execution_20260120, code_execution_20260521

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_f65938c74d40ac1e288f169d3d0435b7` chars 3697–4899 · hash `9cea4902ecd5c887…`

```
* `code_execution_20250825` supports Bash commands and file operations.
* `code_execution_20260120` adds REPL state persistence and [programmatic tool calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling) from within the sandbox. Claude Haiku 4.5 accepts the `code_execution_20260120` and `code_execution_20260521` tool types, but programmatic tool calling and the REPL state persistence that depends on it aren't available on it, so the newer versions behave like `code_execution_20250825` there.
* `code_execution_20260521` is the same runtime as `code_execution_20260120`. The difference is that the tool description tells Claude about the 90-second wall-clock limit on each Python cell in programmatic tool calling, so Claude can budget long-running cells. A cell that exceeds the limit returns a normal code execution result with a non-zero `return_code` and a `detection_timeout` status message in its output. This is separate from the `execution_time_exceeded` [error code](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool#errors), which the API returns when a whole tool invocation exceeds the maximum execution time.
```

<details><summary>Context before</summary>

```
code_execution_20260120`, `code_execution_20260521` |
| Claude Opus 4.7 (claude-opus-4-7)              | `code_execution_20250825`, `code_execution_20260120`, `code_execution_20260521` |
| Claude Opus 4.6 (claude-opus-4-6)              | `code_execution_20250825`, `code_execution_20260120`, `code_execution_20260521` |
| Claude Sonnet 4.6 (claude-sonnet-4-6)          | `code_execution_20250825`, `code_execution_20260120`, `code_execution_20260521` |
| Claude Opus 4.5 (claude-opus-4-5-20251101)     | `code_execution_20250825`, `code_execution_20260120`, `code_execution_20260521` |
| Claude Sonnet 4.5 (claude-sonnet-4-5-20250929) | `code_execution_20250825`, `code_execution_20260120`, `code_execution_20260521` |
| Claude Haiku 4.5 (claude-haiku-4-5-20251001)   | `code_execution_20250825`, `code_execution_20260120`, `code_execution_20260521` |

Each tool version builds on the previous one:


```

</details>

<details><summary>Context after</summary>

```


All three tool versions are generally available and don't require an `anthropic-beta` header. The legacy code execution beta headers remain valid opt-ins.

The examples on this page use `code_execution_20250825`, which covers the Bash and file operations they demonstrate and behaves the same way on every model in the table; use `code_execution_20260120` or later when you need programmatic tool calling or REPL state persistence. The current [web search](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool) and [web fetch](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool) tools (`web_search_20260209`, `web_fetch_20260209`, and later) require `code_execution_20260120` or later as their code execution version.

<Note>
  If you're still using the legacy `code_execution_20250522` (Python only), see [Upgrade to latest tool version](https://
```

</details>

---

## V2D-27

- **provider**: openai
- **document**: Handoffs
- **section**: (1)! › Customizing handoffs via the `handoff()` function
- **source span**: `ver_1c77f33b04ffffa285ea7e61c2a89653` chars 2733–2924
- **evidence kind**: `definition_bullet`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: parameter_error_literal_lookup, identifier_vs_semantic_distractor, lexical_query_shape
- **binding**: template-captured-groups
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What is the `nest_handoff_history` option?

**Proposed answer**: Optional per-handoff override for the RunConfig-level `nest_handoff_history` setting. If `None`, the value defined in the active run configuration is used instead.

**Proposed atomic claims**: `nest_handoff_history`: Optional per-handoff override for the RunConfig-level `nest_handoff_history` setting. If `None`, the value defined in the active run configuration is used instead.

**Critical strings**: nest_handoff_history, Optional per-handoff override for the RunConfig-level `nest

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_1c77f33b04ffffa285ea7e61c2a89653` chars 2733–2924 · hash `dc3876a7a33fdb1b…`

```
-   `nest_handoff_history`: Optional per-handoff override for the RunConfig-level `nest_handoff_history` setting. If `None`, the value defined in the active run configuration is used instead.
```

<details><summary>Context before</summary>

```
ransfer_to_<agent_name>`. You can override this.
-   `tool_description_override`: Override the default tool description from `Handoff.default_tool_description()`
-   `on_handoff`: A callback function executed when the handoff is invoked. This is useful for things like kicking off some data fetching as soon as you know a handoff is being invoked. This function receives the agent context, and can optionally also receive LLM generated input. The input data is controlled by the `input_type` param.
-   `input_type`: The schema for the handoff tool-call arguments. When set, the parsed payload is passed to `on_handoff`.
-   `input_filter`: This lets you filter the input received by the next agent. See below for more.
-   `is_enabled`: Whether the handoff is enabled. This can be a boolean or a function that returns a boolean, allowing you to dynamically enable or disable the handoff at runtime.

```

</details>

<details><summary>Context after</summary>

```


The [`handoff()`][agents.handoffs.handoff] helper always transfers control to the specific `agent` you passed in. If you have multiple possible destinations, register one handoff per destination and let the model choose among them. Use a custom [`Handoff`][agents.handoffs.Handoff] only when your own handoff code must decide which agent to return at invocation time.

```python
from agents import Agent, handoff, RunContextWrapper

def on_handoff(ctx: RunContextWrapper[None]):
    print("Handoff called")

agent = Agent(name="My agent")

handoff_obj = handoff(
    agent=agent,
    on_handoff=on_handoff,
    tool_name_override="custom_handoff_tool",
    tool_description_override="Custom description",
)
```

## Handoff inputs

In certain situations, you want the LLM to provide some data when it calls a handoff. For example, imagine a handoff to an "Escalation agent". You might want the model
```

</details>

---

## V2D-28

- **provider**: anthropic
- **document**: MCP connector
- **section**: MCP server configuration › Field descriptions
- **source span**: `ver_279d37a3a0cc4e8a9209e01f16f9df88` chars 12037–12395
- **evidence kind**: `parameter_table_row`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: parameter_error_literal_lookup, identifier_vs_semantic_distractor, lexical_query_shape
- **binding**: structural: parameter is the row's first cell, requiredness is column 2 of the same row
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> Is the `authorization_token` parameter required?

**Proposed answer**: No, it is optional.

**Proposed atomic claims**: ``authorization_token` is optional.`

**Critical strings**: authorization_token, No

**Generator notes**: Row-scoped association, so the state cannot belong to a different parameter. Reviewer should confirm the table is a parameter table and that the column header means what it appears to mean.

### Evidence E1 (verbatim, authoritative)

`ver_279d37a3a0cc4e8a9209e01f16f9df88` chars 12037–12395 · hash `f9e6a94fee46649f…`

```
| `authorization_token` | string | No       | OAuth authorization token if required by the MCP server. See [Authentication](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector#authentication) for how to obtain one, or the [MCP specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) for protocol details. |
```

<details><summary>Context before</summary>

```
                                                                                                                                                                                    |
| `url`                 | string | Yes      | The URL of the MCP server. Must start with https\://.                                                                                                                                                                                                                                                                  |
| `name`                | string | Yes      | A unique identifier for this MCP server. Must be referenced by exactly one MCPToolset in the `tools` array.                                                                                                                                                                                                            |

```

</details>

<details><summary>Context after</summary>

```


## MCP toolset configuration

The MCPToolset lives in the `tools` array and configures which tools from the MCP server are enabled and how they should be configured.

### Basic structure

```json
{
  "type": "mcp_toolset",
  "mcp_server_name": "example-mcp",
  "default_config": {
    "enabled": true,
    "defer_loading": false
  },
  "configs": {
    "specific_tool_name": {
      "enabled": true,
      "defer_loading": true
    }
  }
}
```

### Field descriptions

| Property          | Type   | Required | Description                                                                                                                             |
| ----------------- | ------ | -------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `type`            | string | Yes      | Must be "mcp\_toolset".    
```

</details>

---

## V2D-29

- **provider**: anthropic
- **document**: Migration guide
- **section**: Sonnet migration › Migrating to Claude Sonnet 5 from Claude Sonnet 4.5 and earlier Sonnet models › Breaking changes › When migrating from Sonnet 4.5
- **source span**: `ver_a7bda3595f2c124605c3228464d4ee52` chars 145238–145433
- **evidence kind**: `lifecycle_statement`
- **evidence shape**: `single_span`
- **reasoning type**: `lifecycle_compatibility_migration`
- **stress types**: correct_document_difficult_passage, version_model_discrimination, parameter_error_literal_lookup, identifier_vs_semantic_distractor, lexical_query_shape, same_document_passage_discrimination
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> Is `budget_tokens` supported on Claude Sonnet 5?

**Proposed answer**: **Extended thinking changes:** `budget_tokens` configurations from Claude Sonnet 4.5 (`thinking: {type: "enabled", budget_tokens: N}`) are not supported on Claude Sonnet 5 and return a 400 error.

**Proposed atomic claims**: **Extended thinking changes:** `budget_tokens` configurations from Claude Sonnet 4.5 (`thinking: {type: "enabled", budget_tokens: N}`) are not supported on Claude Sonnet 5 and return a 400 error.

**Critical strings**: budget_tokens

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_a7bda3595f2c124605c3228464d4ee52` chars 145238–145433 · hash `de9ec2b850012612…`

```
**Extended thinking changes:** `budget_tokens` configurations from Claude Sonnet 4.5 (`thinking: {type: "enabled", budget_tokens: N}`) are not supported on Claude Sonnet 5 and return a 400 error.
```

<details><summary>Context before</summary>

```
', 'Based on...', etc."

   * **Avoiding bad refusals:** Claude is much better at appropriate refusals now. Clear prompting in the user message without prefill should be sufficient.

   * **Continuations** (resuming interrupted responses): Move the continuation to the user message: "Your previous response was interrupted and ended with `[previous_response]`. Continue from where you left off."

   * **Context hydration / role consistency** (refreshing context in long conversations): Inject what were previously prefilled-assistant reminders into the user turn instead.

2. **Tool parameter JSON escaping may differ**

   <Warning>
     This is a breaking change when migrating from Sonnet 4.5 or earlier.
   </Warning>

   JSON string escaping in tool parameters may differ from previous models. Standard JSON parsers handle this automatically, but custom string-based parsing may need updates.


```

</details>

<details><summary>Context after</summary>

```
 Adaptive thinking is on by default, so most workloads need no `thinking` configuration at all; use the [effort parameter](https://platform.claude.com/docs/en/build-with-claude/effort) to control thinking depth. If you ran Claude Sonnet 4.5 without extended thinking, pass `thinking: {type: "disabled"}` to preserve that behavior.

##### When migrating from Claude 3.x

3. **Remove sampling parameters**

   <Warning>
     This is a breaking change when migrating from Claude 3.x models.
   </Warning>

   Sampling parameters (`temperature`, `top_p`, `top_k`) set to a non-default value return a 400 error on Claude Sonnet 5. Remove them from requests, and use prompting to guide the model's behavior instead.

4. **Update tool versions**

   <Warning>
     This is a breaking change when migrating from Claude 3.x models.
   </Warning>

   Update to the latest tool versions (`text_editor_20250728`,
```

</details>

---

## V2D-30

- **provider**: anthropic
- **document**: Structured outputs
- **section**: JSON outputs › Working with JSON outputs in SDKs › SDK-specific methods
- **source span**: `ver_0865c9612dfe97d8f30dd870dd12e53e` chars 29387–29591
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: correct_document_difficult_passage
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What does the C# SDK accept?

**Proposed answer**: The C# SDK accepts raw JSON schemas built programmatically with `JsonSerializer.SerializeToElement`, as shown here, or derives the schema from a plain C# class with the generic `Create<T>()` overload.

**Proposed atomic claims**: The C# SDK accepts raw JSON schemas built programmatically with `JsonSerializer.SerializeToElement`, as shown here, or derives the schema from a plain C# class with the generic `Create<T>()` overload.

**Critical strings**: JsonSerializer.SerializeToElement

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_0865c9612dfe97d8f30dd870dd12e53e` chars 29387–29591 · hash `ae1c3cc2f4fbd61f…`

```
    The C# SDK accepts raw JSON schemas built programmatically with `JsonSerializer.SerializeToElement`, as shown here, or derives the schema from a plain C# class with the generic `Create<T>()` overload.
```

<details><summary>Context before</summary>

```
nse.parsed_output is typed as { name: string; email: string; planInterest: string } | null
    console.log(response.parsed_output!.email);
    ```

    **Type inference requires `as const`.** Use a literal object expression with a `const` assertion so TypeScript can narrow the property types. Without `as const`, the inferred type collapses to `unknown`.

    **Schema transformation.** By default, the helper transforms the schema the same way `zodOutputFormat()` does: removing unsupported constraints, adding `additionalProperties: false` to objects, and filtering string formats. Pass `jsonSchemaOutputFormat(schema, { transform: false })` to send your schema to the API unchanged. See [How SDK transformation works](https://platform.claude.com/docs/en/build-with-claude/structured-outputs#how-sdk-transformation-works).
  </Tab>

  <Tab title="C#">
    **JSON schemas through `OutputConfig`**


```

</details>

<details><summary>Context after</summary>

```
 Deserialize the response JSON with `JsonSerializer.Deserialize`.

    ```csharp
    using System.Text.Json;
    using Anthropic;
    using Anthropic.Models.Messages;

    var client = new AnthropicClient();

    var response = await client.Messages.Create(new MessageCreateParams
    {
        Model = Model.ClaudeOpus5,
        MaxTokens = 1024,
        Messages = [new() {
            Role = Role.User,
            Content = "Extract the key information from this email: John Smith (john@example.com) is interested in our Enterprise plan."
        }],
        OutputConfig = new OutputConfig
        {
            Format = new JsonOutputFormat
            {
                Schema = new Dictionary<string, JsonElement>
                {
                    ["type"] = JsonSerializer.SerializeToElement("object"),
                    ["properties"] = JsonSerializer.SerializeToElement(new
         
```

</details>

---

## V2D-31

- **provider**: openai
- **document**: Agent memory
- **section**: Agent memory › Generate memory
- **source span**: `ver_20a999d310bdb42a2eaa743e061ba109` chars 6111–6278
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, lexical_query_shape, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens if recent raw memories exceed `max_raw_memories_for_consolidation` (defaults to 256)?

**Proposed answer**: Phase 2 keeps only memories from the newest conversations and removes older ones.

**Proposed atomic claims**: If recent raw memories exceed `max_raw_memories_for_consolidation` (defaults to 256), Phase 2 keeps only memories from the newest conversations and removes older ones.

**Critical strings**: max_raw_memories_for_consolidation

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_20a999d310bdb42a2eaa743e061ba109` chars 6111–6278 · hash `0b2654299175c579…`

```
If recent raw memories exceed `max_raw_memories_for_consolidation` (defaults to 256), Phase 2 keeps only memories from the newest conversations and removes older ones.
```

<details><summary>Context before</summary>

```
pace layout is:

```text
workspace/
├── sessions/
│   └── <rollout-id>.jsonl
└── memories/
    ├── memory_summary.md
    ├── MEMORY.md
    ├── raw_memories.md (intermediate)
    ├── phase_two_selection.json (intermediate)
    ├── raw_memories/ (intermediate)
    │   └── <rollout-id>.md
    ├── rollout_summaries/
    │   └── <rollout-id>_<slug>.md
    └── skills/
```

You can configure memory generation with `MemoryGenerateConfig`:

```python
from agents.sandbox import MemoryGenerateConfig
from agents.sandbox.capabilities import Memory

memory = Memory(
    generate=MemoryGenerateConfig(
        max_raw_memories_for_consolidation=128,
        extra_prompt="Pay extra attention to what made the customer more satisfied or annoyed",
    ),
)
```

Use `extra_prompt` to tell the memory generator which signals matter most for your use case, such as customer and company details for a GTM agent.


```

</details>

<details><summary>Context after</summary>

```
 Recency is based on the last time the conversation is updated. This forgetting mechanism helps memories reflect the newest environment.

## Multi-turn conversations

For multi-turn sandbox chats, use the normal SDK `Session` together with the same live sandbox session:

```python
from agents import Runner, SQLiteSession
from agents.run import RunConfig
from agents.sandbox import SandboxRunConfig

conversation_session = SQLiteSession("gtm-q2-pipeline-review")
sandbox = await client.create(manifest=agent.default_manifest)

async with sandbox:
    run_config = RunConfig(
        sandbox=SandboxRunConfig(session=sandbox),
        workflow_name="GTM memory example",
    )
    await Runner.run(
        agent,
        "Analyze data/leads.csv and identify one promising GTM segment.",
        session=conversation_session,
        run_config=run_config,
    )
    await Runner.run(
        agent,

```

</details>

---

## V2D-32

- **provider**: anthropic
- **document**: MCP tunnels quickstart
- **section**: What you need
- **source span**: `ver_067b3bfdc28f24500ea19b97bf3e80b1` chars 1857–1989
- **evidence kind**: `constraint_statement`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, parameter_error_literal_lookup, identifier_vs_semantic_distractor
- **binding**: structural-or-subject-window
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What must `openssl` be?

**Proposed answer**: Preinstalled on macOS and most Linux distributions; on Windows, install it separately (the `openssl` binary must be on your `PATH`).

**Proposed atomic claims**: Preinstalled on macOS and most Linux distributions; on Windows, install it separately (the `openssl` binary must be on your `PATH`).

**Critical strings**: openssl, PATH

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_067b3bfdc28f24500ea19b97bf3e80b1` chars 1857–1989 · hash `a73bb959f95532e9…`

```
Preinstalled on macOS and most Linux distributions; on Windows, install it separately (the `openssl` binary must be on your `PATH`).
```

<details><summary>Context before</summary>

```
m.claude.com/docs/en/agents-and-tools/mcp-tunnels/concepts#components) (the [proxy](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/concepts#components) and [cloudflared](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/concepts#components)) plus a sample MCP server running alongside it. When everything is running, the sample server is reachable from Claude at `https://echo.<your-tunnel-domain>/mcp` even though nothing is listening on a public port.

## What you need

* [Docker and Docker Compose](https://docs.docker.com/get-docker/) on a machine with outbound internet access.
* A role in the [Claude Console](https://platform.claude.com) that can manage MCP tunnels. See the [Console guide prerequisites](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/console#prerequisites).
* [OpenSSL](https://openssl-library.org/source/) 1.1.1 or later. 
```

</details>

<details><summary>Context after</summary>

```


<Steps>
  <Step title="Create a tunnel">
    In the Claude Console sidebar, go to **Manage > MCP tunnels** and click **New tunnel**. Give it a name. Leave **Set up programmatic access** off; this quickstart uses manual credential provisioning.

    After it's created, open the tunnel. Copy two values from the **Connection** section:

    * **Domain** (looks like `abcd1234.tunnel.anthropic.com`)
    * **Token** (click the eye icon, then copy)
  </Step>

  <Step title="Set up the deployment directory">
    <Tabs>
      <Tab title="macOS / Linux">
        ```bash
        mkdir -p mcp-tunnel/{config,data}
        cd mcp-tunnel
        export TUNNEL_DOMAIN=YOUR_TUNNEL_DOMAIN_HERE   # from step 1
        export TUNNEL_TOKEN='eyJ...'            # from step 1
        ```
      </Tab>

      <Tab title="Windows (PowerShell)">
        ```powershell
        New-Item -ItemType Directory -Force -Pa
```

</details>

---

## V2D-33

- **provider**: openai
- **document**: Running agents
- **section**: Running agents › Runner lifecycle and configuration › The agent loop
- **source span**: `ver_2c60e99cfd929a738910b893fd6f1a40` chars 1039–1133
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, identifier_vs_semantic_distractor, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens when you call any of the three `Runner` methods above?

**Proposed answer**: You pass in a starting agent and input.

**Proposed atomic claims**: When you call any of the three `Runner` methods above, you pass in a starting agent and input.

**Critical strings**: Runner

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_2c60e99cfd929a738910b893fd6f1a40` chars 1039–1133 · hash `81aad2cf94487959…`

```
When you call any of the three `Runner` methods above, you pass in a starting agent and input.
```

<details><summary>Context before</summary>

```
r.run], which runs async and returns a [`RunResult`][agents.result.RunResult].
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


```

</details>

<details><summary>Context after</summary>

```
 The input can be:

-   a string (treated as a user message),
-   a list of input items in the OpenAI Responses API format, or
-   a [`RunState`][agents.run_state.RunState] when resuming a paused run or a run stopped with `cancel(mode="after_turn")`. The state can also carry [input staged for the next resumed model call](results.md#add-input-before-resuming).

The runner then runs a loop:

1. We call the LLM for the current agent, with the current input.
2. The LLM produces its output.
    1. If the runner classifies the LLM's output as final output, the loop ends and we return the result.
    2. If the LLM requests a handoff, we update the current agent and input, and re-run the loop.
    3. If the LLM produces tool calls, we run those tool calls, append the results, and re-run the loop.
3. If we exceed the `max_turns` passed, we raise a [`MaxTurnsExceeded`][agents.exceptions.MaxTurnsEx
```

</details>

---

## V2D-34

- **provider**: anthropic
- **document**: Embeddings
- **section**: and cosine similarity are the same. › FAQ
- **source span**: `ver_26f61f56d6ff7124cfa38152f7baef3d` chars 17895–18001
- **evidence kind**: `short_normative`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, identifier_vs_semantic_distractor, lexical_query_shape, paraphrase_query_shape
- **binding**: structural-or-subject-window
- **generator confidence**: medium
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What happens when using the `input_type` parameter?

**Proposed answer**: Special prompts are prepended to the input text prior to embedding.

**Proposed atomic claims**: When using the `input_type` parameter, special prompts are prepended to the input text prior to embedding.

**Critical strings**: input_type

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_26f61f56d6ff7124cfa38152f7baef3d` chars 17895–18001 · hash `0977226e832171ae…`

```
When using the `input_type` parameter, special prompts are prepended to the input text prior to embedding.
```

<details><summary>Context before</summary>

```
dings are normalized to length 1, which means that:

    * Cosine similarity is equivalent to dot-product similarity, while the latter can be computed more quickly.
    * Cosine similarity and Euclidean distance result in identical rankings.
  </Accordion>

  <Accordion title="What is the relationship between characters, words, and tokens?">
    See the [Voyage tokenization guide](https://docs.voyageai.com/docs/tokenization?ref=anthropic).
  </Accordion>

  <Accordion title="When and how should I use the input_type parameter?">
    For all retrieval tasks and use cases (for example, RAG), use the `input_type` parameter to specify whether the input text is a query or document. Do not omit `input_type` or set `input_type=None`. Specifying whether input text is a query or document can create better dense vector representations for retrieval, which can lead to better retrieval quality.

    
```

</details>

<details><summary>Context after</summary>

```
 Specifically:

    > 📘 **Prompts associated with `input_type`**
    >
    > * For a query, the prompt is “Represent the query for retrieving supporting documents: “.
    >
    > * For a document, the prompt is “Represent the document for retrieval: “.
    >
    > * Example
    >
    >   * When `input_type="query"`, a query like "When is Apple's conference call scheduled?" will become "**Represent the query for retrieving supporting documents:** When is Apple's conference call scheduled?"
    >
    >   * When `input_type="document"`, a query like "Apple's conference call to discuss fourth fiscal quarter results and business updates is scheduled for Thursday, November 2, 2023 at 2p.m. PT / 5p.m. ET." will become "**Represent the document for retrieval:** Apple's conference call to discuss fourth fiscal quarter results and business updates is scheduled for Thursday, November 2, 2023 at 2p.
```

</details>

---

## V2D-35

- **provider**: openai
- **document**: OpenAI Python API library
- **section**: Remove `await` for non-async usage. › Webhook Verification › Verifying webhook payloads directly
- **source span**: `ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` chars 16257–16361
- **evidence kind**: `constraint_statement`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, correct_document_difficult_passage, parameter_error_literal_lookup, identifier_vs_semantic_distractor, same_document_passage_discrimination
- **binding**: structural-or-subject-window
- **generator confidence**: high
- **needs human interpretation**: False
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What must `body` be?

**Proposed answer**: Note that the `body` parameter must be the raw JSON string sent from the server (do not parse it first).

**Proposed atomic claims**: Note that the `body` parameter must be the raw JSON string sent from the server (do not parse it first).

**Critical strings**: body

**Generator notes**: _none_

### Evidence E1 (verbatim, authoritative)

`ver_9247e3ce4df6f79d9cadc44e1a3bbd0c` chars 16257–16361 · hash `b41d372109411e73…`

```
Note that the `body` parameter must be the raw JSON string sent from the server (do not parse it first).
```

<details><summary>Context before</summary>

```
)

    try:
        event = client.webhooks.unwrap(request_body, request.headers)

        if event.type == "response.completed":
            print("Response completed:", event.data)
        elif event.type == "response.failed":
            print("Response failed:", event.data)
        else:
            print("Unhandled event type:", event.type)

        return "ok"
    except Exception as e:
        print("Invalid signature:", e)
        return "Invalid signature", 400


if __name__ == "__main__":
    app.run(port=8000)
```

### Verifying webhook payloads directly

In some cases, you may want to verify the webhook separately from parsing the payload. If you prefer to handle these steps separately, we provide the method `client.webhooks.verify_signature()` to _only verify_ the signature of a webhook request. Like `.unwrap()`, this method will raise an error if the signature is invalid.


```

</details>

<details><summary>Context after</summary>

```
 You will then need to parse the body after verifying the signature.

```python
import json
from openai import OpenAI
from flask import Flask, request

app = Flask(__name__)
client = OpenAI()  # OPENAI_WEBHOOK_SECRET environment variable is used by default


@app.route("/webhook", methods=["POST"])
def webhook():
    request_body = request.get_data(as_text=True)

    try:
        client.webhooks.verify_signature(request_body, request.headers)

        # Parse the body after verification
        event = json.loads(request_body)
        print("Verified event:", event)

        return "ok"
    except Exception as e:
        print("Invalid signature:", e)
        return "Invalid signature", 400


if __name__ == "__main__":
    app.run(port=8000)
```

## Handling errors

When the library is unable to connect to the API (for example, due to network connection problems or a timeout), a subclass
```

</details>

---

## V2D-36

- **provider**: anthropic
- **document**: Search results
- **section**: How it works › Required fields
- **source span**: `ver_42a4f3d941b664a285883aaf6ff90373` chars 2518–2655
- **evidence kind**: `parameter_table_row`
- **evidence shape**: `single_span`
- **reasoning type**: `exact_lookup`
- **stress types**: short_evidence_unit, parameter_error_literal_lookup, identifier_vs_semantic_distractor
- **binding**: structural: parameter is the row's first cell, type is another cell of the same row
- **generator confidence**: high
- **needs human interpretation**: True
- **verification status**: `candidate_unverified`

**Proposed question** (a suggestion, not gold)

> What type does the `title` parameter take?

**Proposed answer**: `string`

**Proposed atomic claims**: ``title` is of type string.`

**Critical strings**: title, string

**Generator notes**: Row-scoped association. Reviewer should confirm the table is a parameter table and that the column header means the parameter's own type rather than, say, a return type. FLAG_LOW_VALUE

### Evidence E1 (verbatim, authoritative)

`ver_42a4f3d941b664a285883aaf6ff90373` chars 2518–2655 · hash `2f4dc41ed17b240c…`

```
| `title`   | string | A descriptive title for the search result                                                                        |
```

<details><summary>Context before</summary>

```
le Title", // Required: Title of the result
  "content": [
    // Required: Array of text blocks
    {
      "type": "text",
      "text": "The actual content of the search result..."
    }
  ],
  "citations": {
    // Optional: Citation configuration
    "enabled": true // Enable/disable citations for this result
  }
}
```

### Required fields

| Field     | Type   | Description                                                                                                      |
| --------- | ------ | ---------------------------------------------------------------------------------------------------------------- |
| `type`    | string | Must be `"search_result"`                                                                                        |
| `source`  | string | The source of the content. Any stable string works: a URL, or an internal identifier such as `kb://article-1234` |

```

</details>

<details><summary>Context after</summary>

```

| `content` | array  | An array of text blocks containing the actual content                                                            |

### Optional fields

| Field           | Type   | Description                                                                                                                                                                                                                                                                                                                     |
| --------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `citations`     | object | Citation
```

</details>

---
