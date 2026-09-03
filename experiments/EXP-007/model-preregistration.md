# EXP-007 model selection — recorded BEFORE running the experiment

Written and committed before any EXP-007 retrieval result was observed, so the
choice cannot be a post-hoc selection of whichever model happened to win.

## Environment constraint (measured, not assumed)

| host | result |
|---|---|
| `huggingface.co` | **blocked** — `CONNECT tunnel failed, response 403` |
| `hf-mirror.com` | blocked |
| `api.openai.com` | blocked |
| `api.voyageai.com` | blocked |
| `api.cohere.com` | blocked |
| `github.com` / `raw.githubusercontent.com` / release assets | **reachable** |
| `pypi.org` | reachable |

No embedding or generation credential is present in the environment. Therefore no
transformer-based retrieval embedding model (BGE, E5, GTE, `text-embedding-3`,
Voyage) can be obtained. Per the EXP-007 brief, falling back to corpus-fitted
TF-IDF+SVD is **not** acceptable, so the question became whether *any* genuinely
pretrained model is reachable. One class is: pretrained static word-embedding
models published as versioned release assets on GitHub via `gensim-data`.

## Selected model

| field | value |
|---|---|
| provider | `gensim-data` (RaRe-Technologies / piskvorky), GitHub release asset |
| model identifier | `fasttext-wiki-news-subwords-300` |
| origin | Facebook Research fastText, "wiki-news-300d-1M-subword" |
| training corpus | Wikipedia 2017 + UMBC webbase + statmt.org news (~16B tokens) |
| vocabulary | 1,000,000 word vectors |
| dimensions | 300 |
| pooling | mean of L2-normalized in-vocabulary token vectors |
| normalization | L2 on the pooled vector |
| distance metric | cosine |
| query prefix | none — this model defines no task instruction |
| document prefix | none |

## Why this model, a priori

1. **It is trained with subword information.** The brief names plural/singular
   mismatch (`requests` ↔ `request`) as a concrete failure mode of the unstemmed
   lexical retriever. Subword-informed training places morphological variants near
   each other, so this model is the best available instrument for the specific
   hypothesis under test.
2. **Its pretraining corpus is entirely independent of this project.** Wikipedia and
   news text, fixed long before this corpus was assembled; it cannot have seen the
   20 evaluation questions.
3. **Largest reachable vocabulary** (1M vs GloVe's 400k), which matters for technical
   documentation vocabulary.
4. **Fixed, versioned, addressable artifact**, so the run is reproducible.

Alternatives considered and rejected before running: `glove-wiki-gigaword-300`
(smaller vocabulary, no subword information — strictly worse for the morphology
question), `word2vec-google-news-300` (1.7 GB, no subword information).

## Pooling decision, and why it is corpus-independent

Documents and queries are encoded as the **plain mean of L2-normalized word
vectors**, then L2-normalized. IDF or SIF weighting was rejected deliberately: both
derive weights from *this* corpus, which would reintroduce exactly the
corpus-fitted component that disqualified the earlier LSA substitute. Nothing in
the encoder is fitted to the corpus or to the evaluation questions.

## Honest statement of instrument strength — read before interpreting any result

This is a **genuinely pretrained model, but a static word-embedding one**. It is
*not* a modern transformer retrieval encoder. Mean-pooled static vectors are a
weak sentence representation: they are order-insensitive and they wash out over
long chunks.

The asymmetry this creates must be respected when reading the results:

* A **positive** result (dense rescues cases lexical cannot reach) is strong
  evidence for the vocabulary-mismatch hypothesis — a weak instrument that still
  finds signal is convincing.
* A **negative** result is **weak** evidence against it. It would show that *this
  class* of pretrained embedding cannot bridge the gap, not that a transformer
  retrieval model could not. The hypothesis would remain open, not falsified.

EXP-007 is therefore a partial test. The report states this wherever a conclusion
is drawn.
