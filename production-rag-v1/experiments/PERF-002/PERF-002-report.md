# PERF-002 — BLOCKED: the V2 cross-encoder path is not in this workspace

**Status: `CE_IMPLEMENTATION_NOT_AVAILABLE`. No audit was performed.**

This is not the audit PERF-002 asked for. It is the report the brief requires
*instead* of one:

> First locate or obtain access to the CURRENT authoritative V2 implementation
> that contains the actual CE path used by EXP-018 / EXP-018B. If the current V2
> implementation is not available in your workspace: **STOP after reporting that
> fact. Do not invent the CE implementation from historical code.**

I searched, did not find it, and stopped. Sections A–H are not answered below,
because answering them would require the code that is missing. What follows is
the evidence that it is missing, and exactly what to supply so PERF-002 can run
in a single pass.

---

## What was searched, and what was found

| Where | Result |
|---|---|
| `git fetch --all` on the working repository | 2 branches only: `claude/rag-v1-build-experiments-5yngul`, `main`. No V2 branch. |
| `origin/main` file tree | No `v2`, no cross-encoder, no reranker, no `SYSTEM-D`/`SYSTEM-E` path. |
| Full history of **all** branches (`git log --all --diff-filter=A`) | The only file ever added matching `cross_encoder\|rerank\|system_e\|within_doc\|devset` is `tests/test_exp015_reranker.py` — my own EXP-015 test, which asserts a reranker does **not** exist. |
| GitHub account (`list_repos`) | 4 repositories. `nyxora-outcome-intelligence` (this one, last push = my own), `nyxora-lead-concierge`, `AI-Engineer-Roadmap`, `Ryork67677`. None is a V2 RAG implementation. |
| Filesystem, all mounts (`find / -name .git`) | One project checkout only. The others are `/opt/rbenv` and `/opt/nvm`. |
| Filesystem, `*.onnx` | One real model plus three ONNX Runtime test fixtures. See below. |
| Directories named `*rag-v2*`, `*rag_v2*`, `*production-rag-v2*` | None. |
| `experiments/` | Ends at `EXP-015`. No EXP-016, EXP-017, **EXP-018**, EXP-018B, EXP-019. |
| `evals/` | No `V2-DEVSET-001`. |

### The one ONNX model on disk is a bi-encoder, not a cross-encoder

`data/cache/models/exp009/onnx/model.onnx` — this is the model SYSTEM-A already
uses for dense retrieval, and it cannot be the CE:

```
config.json  _name_or_path : "sentence-transformers/all-MiniLM-L6-v2"
             architectures : ["BertModel"]

ORT session  inputs  : input_ids, attention_mask, token_type_ids  [batch, seq] int64
             outputs : last_hidden_state  [batch, seq, 384]  float
```

A cross-encoder is `…ForSequenceClassification` and emits
`logits [batch, 1]` — one relevance score per pair. This emits per-token hidden
states for a single text. It is structurally the wrong kind of model, not merely
a different checkpoint.

### The environment could not have run the described CE either

```
onnxruntime  1.29.0     present
tokenizers   0.23.1     present
torch                   ABSENT
transformers            ABSENT
optimum                 ABSENT
flashrank / fastembed   ABSENT
```

This is the same environment EXP-015 surveyed, which concluded
`NO_PRETRAINED_CROSS_ENCODER_AVAILABLE` (huggingface.co and cdn.jsdelivr.net are
proxy CONNECT 403 policy denials). `src/rag_v1/systems.py` still reads
`"reranker": None, "cross_encoder": None`.

**Conclusion:** the EXP-018B results in the brief were produced somewhere this
session cannot see. Nothing here is a stale copy of that code — there is no copy
of it at all.

---

## Why I did not proceed anyway

The brief lists ten inspection targets. Every one of them is a question about
code I do not have:

* *"Is the session created once or repeatedly?"* — there is no session-creating
  CE code to look at.
* *"Current batch size / number of ONNX calls per query"* — not inferable.
* *"intra_op_num_threads, execution mode, provider configuration"* — these are
  arguments in a `SessionOptions` that does not exist here.
* *"actual tokenized pair lengths for candidates"* — requires the CE tokenizer
  and V2-DEVSET-001, neither present.

I could have written a plausible audit of a generic ONNX cross-encoder. It would
have been fluent, roughly right in outline, and worthless — worse than worthless,
because §F asks for patch-style changes and someone would have tried to apply
them to real code they do not describe. This is the same call as EXP-015, where
refusing to substitute a hand-rolled scorer was the finding.

**Nothing in this repository was modified.** No source file, no experiment, no
system. This report is the only file written, at the path the brief named.

---

## What the brief's own numbers already imply — hypotheses, not findings

Derived only from figures supplied in the brief. **These are predictions to test
against the real code, not conclusions.** They are recorded so the audit, when
it can run, starts from a sharp question.

CE share of E-L10: `5903.9 / 6454.8` = **91.5%** of total runtime. Confirmed as
the dominant component; that part needs no code.

Per-candidate CE cost at the reported mean union of 104.1:

```
5903.9 ms / 104.1 candidates = 56.7 ms per candidate
```

For context, a 6-layer / 384-hidden MiniLM-class cross-encoder on CPU costs
roughly 10–30 ms for a *single* unbatched 512-token pair, and typically **under
5 ms per pair** once batched. 56.7 ms/candidate is high enough that it is
probably not explained by tokenization or tensor shuffling at all. Three
hypotheses fit:

| # | Hypothesis | Predicted signature in the code | Predicted ceiling if true |
|---|---|---|---|
| H1 | Candidates scored **one at a time** — one `session.run()` per pair | a `for` loop over candidates containing `session.run` | batching alone: **5–15×** |
| H2 | **Session or tokenizer constructed inside** the per-query (or per-candidate) path | `InferenceSession(...)` / tokenizer load not at module or object scope | hoisting alone: often **>10×**, and it would dwarf everything else |
| H3 | The CE is a **much larger model** than MiniLM-class | `num_hidden_layers` / `hidden_size` in the CE's `config.json` | batching helps, but the floor is set by model size |

**The single check that discriminates all three** is to count `session.run`
invocations and `InferenceSession` constructions for one query — a counter or an
`ORT` profile, no scoring, no metric. If H2 holds, it is likely the whole finding
and the fix is a two-line hoist, exactly as PERF-001's `snapshot_chunk_set`
nested-connection defect turned out to be.

One thing I can state now with confidence, because it is arithmetic and not
architecture: **§H cannot be answered honestly before the profile in "PROFILE
FIRST" is run.** A latency range quoted before knowing which of H1–H3 holds
would span two orders of magnitude.

---

## What to supply so PERF-002 runs in one pass

In rough order of how much each unblocks:

1. **The V2 source tree containing the CE path** — ideally pushed to a branch of
   `Ryork67677/nyxora-outcome-intelligence`, which this session can already
   reach. A branch name is enough; I will fetch it. Failing that, any repo I can
   be granted via `add_repo`.
2. **The CE model directory**: the ONNX file, `config.json`, and the tokenizer
   files. `config.json` alone settles H3 immediately.
3. **The call site** — where the CE is invoked in the E-L10 path, and the
   `SessionOptions` / provider configuration it is constructed with.
4. **The stored EXP-018B latency instrumentation**, if the 358.5 / 192.4 /
   5903.9 split came from timers already in the code. Reusing the existing
   decomposition avoids adding new measurement to a frozen path.
5. **V2-DEVSET-001** and its frozen split hashes — needed only for §6
   (sequence-length distribution and padding waste) and for the equivalence
   plan's metric-identity check. §§1–5 and 7–10 can be audited without it.

With items 1–3 the audit is straightforwardly completable; items 4–5 raise its
precision.

---

## Constraints observed

No V2 implementation located, so: no CE audited, no patch proposed, no patch
applied. No holdout opened. SYSTEM-D untouched. CE model, scoring semantics,
blend weights and RRF untouched — trivially, since none of them are present.
EXP-017 and EXP-019 not run. E-L10 not validated and not frozen. No benchmark
variant scored. The PERF-001 checkout's source is unmodified.
