# GOLD-001 — heading parser audit

**44 of 5857 parsed headings (0.75%) read as prose rather than as a label**, across 15 of 202 documents in the frozen snapshot.

44 of 5857 parsed headings (0.75%), in 15 of 202 documents. That is isolated. It does not justify a parser experiment on its own, and the batch-006 rule — never trust section_path for scope — is the cheaper fix.

## What was counted

| | |
| --- | --- |
| snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| parser | `rag_v1.parsing._HEADING_RE` |
| documents | 202 |
| headings parsed | 5857 |
| suspicious on any rule | 82 |
| **likely prose** | **44** |
| documents affected | 15 |

A heading is a label. *Suspicious* means it broke one of the rules below; *likely prose* is the strong subset — it ends in a sentence-final period or begins in lower case, which a label does not do. A merely long heading is common and harmless, and is counted separately for that reason.

| why it was flagged | headings |
| --- | --- |
| starts lowercase | 30 |
| ends in a sentence-final period | 21 |
| contains a comma-separated 'or'/'and' list | 16 |
| longer than 12 words | 14 |
| ends in a comma, semicolon or colon | 13 |

## Examples

| version | level | heading | why |
| --- | --- | --- | --- |
| `ver_b275f1db…` | 1 | Decide when to compact (e.g., on idle, every N turns, or size thresholds). | ends in a sentence-final period; longer than 12 words; contains a comma-separated 'or'/'and' list |
| `ver_9247e3ce…` | 1 | configured through AWS_REGION, AWS_DEFAULT_REGION, or your AWS profile. | ends in a sentence-final period; starts lowercase; contains a comma-separated 'or'/'and' list |
| `ver_4c8080eb…` | 1 | 'entries' is a sequence of structured conversation entries (assistant messages, tool calls, etc. | ends in a sentence-final period; longer than 12 words |
| `ver_aeebd84b…` | 1 | Define a function that can be called by the model and provide them as tools to the model. | ends in a sentence-final period; longer than 12 words |
| `ver_9247e3ce…` | 1 | operating system's normal trusted certificate authorities. | ends in a sentence-final period; starts lowercase |
| `ver_57e26a49…` | 1 | how we want to handle the events in the response stream. | ends in a sentence-final period; starts lowercase |
| `ver_b05e105d…` | 1 | environment (it will have expired since install). | ends in a sentence-final period; starts lowercase |
| `ver_26f61f56…` | 1 | and cosine similarity are the same. | ends in a sentence-final period; starts lowercase |
| `ver_57e26a49…` | 1 | and stream the response. | ends in a sentence-final period; starts lowercase |
| `ver_b05e105d…` | 1 | hasn't changed. | ends in a sentence-final period; starts lowercase |
| `ver_a183af1c…` | 1 | Valid channels: analysis, commentary, final. Channel must be included for every message. | ends in a sentence-final period |
| `ver_a183af1c…` | 1 | Valid channels: analysis, commentary, final. Channel must be included for every message. | ends in a sentence-final period |
| `ver_a183af1c…` | 1 | Valid channels: analysis, commentary, final. Channel must be included for every message. | ends in a sentence-final period |
| `ver_3d4b8881…` | 1 | Broader authority such as managed or workload identity and external credential files. | ends in a sentence-final period |
| `ver_b05e105d…` | 1 | export ANTHROPIC_WORKSPACE_ID=wrkspc_...   # if your rule is workspace-scoped | starts lowercase |
| `ver_aeebd84b…` | 1 | Tools are just regular Python functions. They can be anything at all. | ends in a sentence-final period |
| `ver_b05e105d…` | 1 | export TUNNEL_ID=tnl_...   # set only if you set it during install | starts lowercase |
| `ver_b275f1db…` | 1 | session = OpenAIConversationsSession(conversation_id="conv_123") | starts lowercase |
| `ver_9247e3ce…` | 1 | gets the API Key from environment variable AZURE_OPENAI_API_KEY | starts lowercase |
| `ver_de67d790…` | 1 | This is an absolute host path outside the SDK process base_dir. | ends in a sentence-final period |
| `ver_e3b7dcb3…` | 1 | change the provider config in providers.ts to add your provider | starts lowercase |
| `ver_3d4b8881…` | 1 | Mount-scoped values such as inline access keys. | ends in a sentence-final period |
| `ver_57e26a49…` | 1 | with the `EventHandler` class to create the Run | starts lowercase |
| `ver_9247e3ce…` | 1 | Automatically fetches more pages as needed. | ends in a sentence-final period |
| `ver_e3b7dcb3…` | 1 | go into the compatibility test directory | starts lowercase |

## What this changes

**For batch 006.** section_path is not trusted for claim scope. A candidate's exact evidence must contain the scope its claim needs, and a candidate whose scope would depend on a suspicious heading is repaired or dropped.

**Later.** A parser experiment AFTER GOLD-001 is complete. Not now: changing the parser changes section_path for every stored document, and the corpus snapshot is frozen for the duration of this evaluation.

## What was not done

- No heading was rewritten and no document was reparsed into storage.
- No existing evidence anchor moved; closed batches are unchanged.
- GOLD-B005-11 keeps its recorded section_path — it is a closed record.
