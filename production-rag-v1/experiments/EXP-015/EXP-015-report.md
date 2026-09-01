# EXP-015 — cross-encoder reranking of SYSTEM-A

## Status: BLOCKED at model acquisition

The experiment is preregistered and its headroom is measured. It cannot proceed past reranker selection: **no pretrained cross-encoder is obtainable in this environment**, and no substitute was used.

## 1. Validation decision (recorded)

**`SYSTEM_B_PROMOTION = REJECTED`** · **`SYSTEM_A_CONTROL = RETAINED`**

DOC-C did not replicate on independent validation. Its Stage-1 routing discarded a required document in 12 of 40 cases, and every one of the 11 regressions has the same signature: SYSTEM-A found the span at rank 1-9 and SYSTEM-B did not retrieve it at all.

SYSTEM-B is preserved, not deleted: A rejected intervention with a clean causal explanation is a result. Deleting it would leave the project unable to say why routing was tried and what it cost. Its config hash `304c350940b83733…` and every run artifact remain in the repository.

## 2. Why reranking is the justified next intervention

SYSTEM-A's validation gap is between documents and passages, not between documents and nothing: document recall **0.975** against span recall **0.750**. The dominant failure class is `WITHIN_DOCUMENT_PASSAGE_FAILURE`. That is a ranking problem, which is what a reranker addresses.

## 3. Reranker ceiling — computed before any model was considered

A perfect reranker over a pool of P can only promote a span already inside the top P. These are arithmetic bounds over SYSTEM-A's stored candidate ranks; no retrieval was re-run and no model was involved.

| pool | max strict recall | headroom over 30/40 | max span recall | cases unreachable | spans unreachable |
| --- | --- | --- | --- | --- | --- |
| 30 | 35/40 (87.5%) | +5 | 0.8723 | 5 | 6 |
| 50 | 36/40 (90.0%) | +6 | 0.8936 | 4 | 5 |
| 100 | 37/40 (92.5%) | +7 | 0.9149 | 3 | 4 |

**There is real headroom.** At pool 100 a perfect reranker could reach 37/40 against SYSTEM-A's 30/40 — **+7 cases**. The experiment is worth running as soon as a model can be obtained.

**The ceiling is not 40.** 4 spans are never retrieved at any depth. These spans are outside every pool. No reranker can reach them; they are a candidate-generation problem, not a ranking one. Those cases need better candidate generation, and no reranker will reach them.

## 4. Model acquisition — what was actually tried

| host | response | verdict |
| --- | --- | --- |
| `huggingface.co` | CONNECT 403 | BLOCKED by egress policy |
| `cdn.jsdelivr.net` | CONNECT 403 | BLOCKED by egress policy |
| `github.com / objects.githubusercontent.com` | 400 / 403 | release assets not retrievable |
| `chroma-onnx-models.s3.amazonaws.com` | 200 for the EXP-009 bi-encoder bundle; 403 for every cross-encoder key tried | REACHABLE but hosts no cross-encoder |
| `storage.googleapis.com/qdrant-fastembed` | 403 for concrete reranker objects | not retrievable |
| `pypi.org / files.pythonhosted.org` | 200 | REACHABLE — but no PyPI wheel bundles cross-encoder weights; flashrank and fastembed both resolve their weights from huggingface.co, which is blocked |

Local inventory: the only cached model is the **all-MiniLM-L6-v2 bi-encoder** SYSTEM-A already uses. `onnxruntime` is available; `torch` and `transformers` are not installed and their weights would still resolve through huggingface.co.

**Conclusion: `NO_PRETRAINED_CROSS_ENCODER_AVAILABLE`.** The 403s from huggingface.co and cdn.jsdelivr.net are explicit proxy policy denials recorded at CONNECT. The S3 and GCS 403s are bucket responses, not blocks — the same S3 host returns 200 for the EXP-009 bi-encoder bundle, so it is reachable and simply hosts no cross-encoder.

## 5. What was deliberately not done

**No substitute was used. A hand-written lexical or heuristic rescorer is not a pretrained cross-encoder, and tuning one against the development set would be the GOLD fitting section 12 forbids. Reporting the blocker is the correct outcome, not a workaround.**

Substituting a hand-written scorer would have produced a number for every section of this brief, and the number would have measured a heuristic invented this afternoon rather than the hypothesis under test. Tuning that heuristic on the development set to make it competitive is precisely the GOLD fitting §12 forbids.

## 6. Not executed

EXP-015 cannot proceed past model selection. Sections 13 through 20 — development qualification, the SYSTEM-C freeze, the one-shot validation, the regression audit and the promotion classification — are not executable and were not attempted.

No `RERANKER_SUPPORTED` / `NEUTRAL` / `REJECTED` classification is returned, because no reranker was run. Returning one would be inventing a result.

## 7. How to unblock

1. Allow huggingface.co through the egress policy for this environment.
2. Side-load a cross-encoder ONNX bundle (for example cross-encoder/ms-marco-MiniLM-L-6-v2) into data/cache/models/ the way the EXP-009 bi-encoder bundle was supplied.
3. Publish the bundle to a reachable object store; chroma-onnx-models.s3.amazonaws.com is reachable and already serves the project's bi-encoder.

The preregistration in `EXP-015-preregistration.json` is complete and fixed: candidate pool 100, development-only qualification, freeze before validation, one scored validation run, promotion criteria. None of it depends on which model arrives, so it stays valid and unedited when one does.

## 8. Invariants

- SYSTEM-A unchanged and hash-verified; SYSTEM-B unchanged and preserved.
- Corpus snapshot `snap_689e336380a054d8039dc35b2c09cd0a` and manifest hash unchanged.
- No retrieval was run in this task; the ceiling used stored ranks only.
- No answer generation.
- **Holdout: 90 cases, `holdout_runs = 0`, frozen, not loaded or enumerated.**
