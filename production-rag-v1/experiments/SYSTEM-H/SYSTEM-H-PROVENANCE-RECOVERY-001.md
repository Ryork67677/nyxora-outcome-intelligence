# SYSTEM-H provenance recovery — RECOVERED

The EXP-019A lineage was **found**, complete, as original git blobs. `PROVENANCE-GAP-001` is superseded
but not rewritten: it remains an accurate record of what was known at commit `9dc0899`.

## Where it was, and why two of my searches missed it

Everything is on **`origin/grok/v2-natq-20260903`**.

`PROVENANCE-GAP-001` recorded four refs checked — the claude branch, `grok/v2-dev`,
`grok/ce-latency-handoff`, `main`. It did not check `grok/v2-natq-20260903`. My later claim that *"no
SYSTEM-H runner exists on any branch"* repeated the same omission: I searched three refs and wrote "any".

Both statements were wrong because the **search space** was wrong, not because the artifacts were absent.
The lineage has been reachable from `origin` this whole time, and a second copy has been sitting checked
out in a detached worktree at `37adc2c` since earlier in this session.

## What is recovered

26 artifacts, each a git blob with a verified SHA256. Spot-checked against the detached worktree —
identical hashes from two independent copies.

| Lineage | Key artifacts |
|---|---|
| **EXP-019A** | preregistration, results, report, pool-identity, closure, `SYSTEM-G-PROJECTION-PRIOR.json`, recovered-union (3.6 MB), `run_exp019a.py` |
| **EXP-019B** | preregistration, results, report, `run_exp019b.py` |
| **PERF-003** | preregistration, results, closure, `SYSTEM-G-CE-D1.json`, `run_perf003.py`, `v2_system_g_ce.py`, logit logs |
| **EXP-017** | projection build record, `SYSTEM-F-PROJECTION.json`, `run_exp017.py` |
| **SYSTEM-H** | upstream `SYSTEM-H-V2-DEV-CANDIDATE.json` |
| **EVAL-NATQ-VAL-001** | preregistration, REPORT, `run_eval_natq_val_001.py` |

### Identity cross-checks — all pass

- `EXP-019A-preregistration.json` → `f14001ef…`, **exactly** the value relayed in `PROVENANCE-GAP-001`,
  and matching its own `.sha256` sidecar. Independent confirmation this is the original.
- SYSTEM-G config hash `563a7b79…` — matches the coordinator's value.
- PERF-003 CE-D1 config hash `6d108568…` — matches the coordinator's value.
- PERF-003 preregistration `dc01713e…` — matches the value cited *inside* the upstream SYSTEM-H record.
- Projection config hash `7fd5034c…` — matches the SYSTEM-H record.

## Two findings that block the run anyway

**1. The identity in my preregistration is wrong.**

The authoritative SYSTEM-H is `config_hash = 7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a`
— that is what the upstream record carries and what `EVAL-NATQ-VAL-001` recomputed and verified.

My local record carries `026a302b…` and `score_determining_hash = 3fade96a…`. **`3fade96a` appears only on
my own branch.** It is a hash I minted over my own SYSTEM-H record during the earlier freeze; it is not the
upstream identity and never was. The NATQ-002 preregistration pins it.

So recovering the artifacts does **not** by itself unblock the run. Executing against the current
preregistration would verify against the wrong hash.

**2. SYSTEM-H has already been scored, and my preregistration says it hasn't.**

`EVAL-NATQ-VAL-001` ran SYSTEM-H on the frozen NATQ-001 validation set — n=40, 53 gold spans, config hash
verified, holdout not opened:

| Metric | Result |
|---|---|
| PRIMARY strict_recall@10 | **20/40** |
| evidence_span_recall@10 | 0.5094 (27/53) |
| document_recall@10 | 35/40 |
| candidate_gold_span_recall@100 | 34/40 |

My preregistration justified its paired design on the grounds that no prior anchor existed. One does. The
paired design is still sound, but its rationale was wrong — and the consequence matters more than the
rationale: **the approved `case_hit@10` PASS floor of 0.80 sits far above SYSTEM-H's known ~0.50
case-level result on a comparable natural-query validation set.** On that evidence SYSTEM-H would likely
fail the approved floor. That is something to see before authorising a run, not after.

*Caveat:* `strict_recall_at_10` and my `case_hit@10` are similar but not proven identical in definition.
The comparison is indicative, not exact.

## Still not recovered

- **Projection index rows** for `ps_v2_ovl_win448_s224`. The build record survives (config hash, 18,057
  projections, 27 MB, fingerprint `bd95feaeacf98559`), but the rows are database state and this host has no
  projection table. `run_exp017.py` can rebuild it — but a rebuild is reproduction, not recovery.
- **Cross-encoder weights** at revision `233902d2…`. Not in git; `huggingface.co` is unreachable from here;
  the local `model.onnx` is unverified against `artifact_sha256 5d3e70fd…`.

## Search scope

7 refs, 0 tags, 0 stashes, 2 worktrees, 313 reflog entries, 6 unreachable objects (5 trees and one
GOLD-001 PDF commit — zero matches). Filesystem swept across `/home/user`, `/root`, `/tmp`, `/workspace`,
`/opt`, `/mnt`, `/media`; two archives listed read-only, neither containing matches. Windows paths do not
exist on this Linux container. Database inspected read-only; nothing written.

Repository state unchanged. Nothing restored or checked out.

## Recommendation

**STOP for coordinator approval**, as instructed. SYSTEM-H should not move to `UNEVALUABLE_PROVENANCE_LOSS`
— the provenance is not lost. But it is not runnable against the current NATQ-002 preregistration either,
because that preregistration names the wrong system identity and rests on a false premise about prior
scoring. Both need a ruling before any run.
