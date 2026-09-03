# V2-DEVSET-001 V2D-06 round-2 wording repair

**1 repaired candidate · corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` · generated 2026-09-01T02:49:44Z (2026-08-31 22:49 ET)**

Only V2D-06. Round-2 ChatGPT: 15 PASS, this one FIX_REQUIRED. Evidence boundary is sufficient; rewrite the answer/claim as a normal-case rule plus explicit Opus 4.6 exception. Span/hash unchanged. Not gold. Do not consult live docs.

## V2D-06

- **provider**: anthropic
- **document**: Fast mode (research preview)
- **section**: Checking which speed was used
- **source span**: `ver_cc7d6ed2a636d74fc7aca7885ba9ce60` chars 9863–10222
- **verification status**: `candidate_unverified_after_fix`
- **human_verified**: false
- **span expanded this round**: false

**Question**

> What is `usage.speed` when a request with `speed: "fast"` succeeds, including on Claude Opus 4.6?

**Repaired answer**: Normally `usage.speed` is `"fast"`. Claude Opus 4.6 is the exception: a successful `speed: "fast"` request can report `"standard"`.

**Repaired atomic claims**:

1. In the normal case, when a request with `speed: "fast"` succeeds, `usage.speed` is `"fast"`.
2. Claude Opus 4.6 is an exception: requesting fast mode can succeed while the `speed` field shows `"standard"`.

**Critical strings**: usage.speed, Claude Opus 4.6, standard

**What changed.** Answer no longer leads with an unqualified `It is "fast"`. It states the normal-case rule, then the Opus 4.6 exception. Evidence span `1ae25e4479c1961c3ac649534d70309e9fc4f29a776e49115c2c7e0209f536b4` unchanged.

### Evidence E1 (verbatim, authoritative)

`ver_cc7d6ed2a636d74fc7aca7885ba9ce60` chars 9863–10222 · hash `1ae25e4479c1961c3ac649534d70309e9fc4f29a776e49115c2c7e0209f536b4`

```
When a request with `speed: "fast"` succeeds, `usage.speed` is `"fast"`. If you are using Claude Opus 4.6 and request fast mode, its behavior is unique. Instead of returning an error like other models that don't support fast mode, it silently switches to standard speed. Though there is no error with Opus 4.6, the `speed` field accurately shows `"standard"`.
```

<details><summary>Context before</summary>

```
opic-fast-input-tokens-reset`      | Time when the fast mode input token limit resets  |
| `anthropic-fast-output-tokens-limit`     | Maximum fast mode output tokens per minute        |
| `anthropic-fast-output-tokens-remaining` | Remaining fast mode output tokens                 |
| `anthropic-fast-output-tokens-reset`     | Time when the fast mode output token limit resets |

For tier-specific rate limits, see the [Rate limits](https://platform.claude.com/docs/en/api/rate-limits) page.

## Checking which speed was used

The response `usage` object includes a `speed` field that indicates which speed was used, either `"fast"` or `"standard"`. Requesting `speed: "fast"` on a [model that doesn't support fast mode](https://platform.claude.com/docs/en/build-with-claude/fast-mode#supported-models) returns an error, and so does exceeding fast mode's rate limits or capacity (a `429` or `529`). 
```

</details>

<details><summary>Context after</summary>

```


<CodeGroup>
  ```bash cURL
  curl https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "anthropic-beta: fast-mode-2026-02-01" \
    -H "content-type: application/json" \
    -d '{
      "model": "claude-opus-5",
      "max_tokens": 1024,
      "speed": "fast",
      "messages": [{"role": "user", "content": "Hello"}]
    }'
  ```

  ```bash CLI
  ant beta:messages create \
    --beta fast-mode-2026-02-01 \
    --transform usage.speed \
    --raw-output <<'YAML'
  model: claude-opus-5
  max_tokens: 1024
  speed: fast
  messages:
    - role: user
      content: Hello
  YAML
  ```

  ```python Python
  client = anthropic.Anthropic()

  response = client.beta.messages.create(
      model="claude-opus-5",
      max_tokens=1024,
      speed="fast",
      betas=["fast-mode-2026-02-01"],
      messages=[{"role": "user",
```

</details>
