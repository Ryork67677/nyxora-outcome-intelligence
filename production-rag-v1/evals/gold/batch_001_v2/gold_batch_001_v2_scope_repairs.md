# GOLD-001 — batch 001 v2 scope repairs

Two cases, proposed and applied to nothing. Batch 001 v1 is unchanged and still hashes to `d6f92e8d1a7e77ea…`; the v2 metadata overlay deliberately excludes both of these because neither can be fixed by adding metadata.

Both were flagged by the mechanical claim audit and both flags are correct: each case asserts a scope its approved anchor does not contain. Neither is holdout-eligible until one of the options below is approved.

---

## GOLD-B001-13

**Current question.** What value must `anthropic_version` be set to when using Claude on Google Cloud's Agent Platform?

**Current answer.** `vertex-2023-10-16`.

**Current claims (as approved in v1)**

  1. On Google Cloud Agent Platform, `anthropic_version` is passed in the request body and must be set to `vertex-2023-10-16`.

**Current exact evidence** — 519–725 · `39c03eda7465a346…`

```
Instead, it is specified in the Google Cloud endpoint URL.
* On Agent Platform, `anthropic_version` is passed in the request body (rather than as a header), and must be set to the value `vertex-2023-10-16`.
```

### Option A: evidence_boundary_expansion — **recommended**

**What changed.** Extended backwards to the sentence that names Google Cloud's Agent Platform as the subject of the two request-format differences. (+271 characters; anchor moved.)

**Why it is necessary.** The approved claim says "On Google Cloud Agent Platform" and the approved span does not contain that scope — the audit's UNSUPPORTED finding is correct. The extension also fixes something the audit did not look for: the approved span opens on "Instead, it is specified in…", an anaphoric reference to the previous bullet. Both defects close with the same extension.

**Proposed claims**

  1. On Google Cloud's Agent Platform, `anthropic_version` is passed in the request body rather than as a header.
  2. `anthropic_version` must be set to the value `vertex-2023-10-16`.

**Proposed exact evidence** — 248–725 · `f9057cf3281d924b…`

```
The API for accessing Claude on Google Cloud's Agent Platform is nearly identical to the [Messages API](https://platform.claude.com/docs/en/api/messages/create), with two key differences in request format:

* On Agent Platform, `model` is not passed in the request body. Instead, it is specified in the Google Cloud endpoint URL.
* On Agent Platform, `anthropic_version` is passed in the request body (rather than as a header), and must be set to the value `vertex-2023-10-16`.
```

**Critical strings.** `Google Cloud's Agent Platform`, `` `anthropic_version` ``, `passed in the request body`, `rather than as a header`, `vertex-2023-10-16`

*All verified inside the proposed span.*

**Validator.** PASS — all blocking checks

**Holdout-eligible if approved.** yes

---

### Option B: claim_narrowing

**What changed.** The anchor does not move. The claim drops "Google Cloud". (+0 characters; anchor unchanged.)

**Why it is necessary.** Smaller, and fully supported by the existing span. It is not recommended: the question still asks about Google Cloud, so a reader checking the anchor alone cannot confirm which Agent Platform is meant, and the span keeps its anaphoric opening. It trades a real fix for a smaller diff.

**Proposed claims**

  1. On Agent Platform, `anthropic_version` is passed in the request body (rather than as a header), and must be set to `vertex-2023-10-16`.

**Exact evidence** — unchanged, hash still `39c03eda7465a346…`

**Critical strings.** `On Agent Platform`, `` `anthropic_version` ``, `passed in the request body`, `rather than as a header`, `vertex-2023-10-16`

*All verified inside the proposed span.*

**Validator.** PASS — all blocking checks

**Holdout-eligible if approved.** yes

---

## GOLD-B001-17

**Current question.** What does a 404 `File not found` error mean in the Anthropic Files API?

**Current answer.** The specified `file_id` does not exist or you do not have access to it.

**Current claims (as approved in v1)**

  1. A Files API `File not found` error uses HTTP 404.
  2. It indicates that the specified `file_id` does not exist or the caller does not have access to it.

**Current exact evidence** — 29836–30171 · `83e5abb14c4495a6…`

```
* **File not found (404):** The specified `file_id` doesn't exist or you don't have access to it
* **Invalid file type (400):** The file type doesn't match the content block type (for example, using an image file in a document block)
* **Not downloadable (400):** Files you upload have `"downloadable": false` and cannot be downloaded.
```

### Option A: evidence_boundary_expansion — **recommended**

**What changed.** Extended backwards to the line that names the Files API as the scope of the error list. The span's end is unchanged. (+49 characters; anchor moved.)

**Why it is necessary.** The approved claim says "Files API", which appears only in the document title and section path. The extension puts the scope inside the anchor. The end is not trimmed: the repair path only ever grows an anchor outward, so that the new span provably contains the approved one. Two unrelated error bullets therefore stay in the span — a cost worth stating rather than hiding.

**Proposed claims**

  1. A Files API `File not found` error uses HTTP 404.
  2. It indicates that the specified `file_id` doesn't exist or the caller doesn't have access to it.

**Proposed exact evidence** — 29787–30171 · `8089c9eb85636cf6…`

```
Common errors when using the Files API include:

* **File not found (404):** The specified `file_id` doesn't exist or you don't have access to it
* **Invalid file type (400):** The file type doesn't match the content block type (for example, using an image file in a document block)
* **Not downloadable (400):** Files you upload have `"downloadable": false` and cannot be downloaded.
```

**Critical strings.** `Common errors when using the Files API`, `File not found (404)`, `` `file_id` ``, `doesn't exist or you don't have access to it`

*All verified inside the proposed span.*

**Validator.** PASS — all blocking checks

**Holdout-eligible if approved.** yes

---

## Decision

Approve one option per case, or reject both. Nothing is applied until you do, and applying it creates a v2 record — batch 001 v1 stays closed and unchanged either way.

Until then the project stands at **14 holdout-eligible** cases, with these two pending.
