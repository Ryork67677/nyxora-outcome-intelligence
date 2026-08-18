"""EXP-009: retrieval using a contextual pretrained transformer encoder.

Why this exists
---------------
EXP-007 could not obtain a transformer. It fell back to mean-pooled static
FastText vectors and said so plainly: an order-insensitive bag of word vectors is
a *weak instrument*, so its negative result was weak evidence rather than a
falsification. EXP-008 then showed that the pooling, not the chunk size, was the
binding constraint — shortening chunks made the static encoder worse.

This module supplies the instrument EXP-007 lacked: ``all-MiniLM-L6-v2``, a
6-layer BERT bi-encoder contrastively trained on ~1B sentence pairs explicitly for
semantic search. It is contextual (token vectors depend on the surrounding
sentence) and it was trained for retrieval, not for language modelling.

See ``experiments/EXP-009/model-preregistration.md``, committed before any EXP-009
retrieval result was observed, for the selection record, the provenance
limitation, and the falsification criteria.

Nothing here is fitted to this corpus:

* Weights are frozen and are never updated.
* Pooling is the reference attention-masked mean, then L2 normalization.
* No query or document prefix is applied — this model is symmetric and defines no
  task instruction. Inventing one would be tuning.

Determinism
-----------
Every sequence is padded to a fixed length rather than to the longest member of
its batch, so a chunk's vector does not depend on which other chunks happened to
share its batch. Combined with a pinned thread count this makes a re-run
reproduce the stored vectors exactly, which is the property EXP-005 and EXP-007
had to retrofit into the two ranking paths.
"""

from __future__ import annotations

import tarfile
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from rag_v1.config import settings
from rag_v1.ids import config_hash

BUNDLE_FILENAME = "onnx.tar.gz"
BUNDLE_SHA256 = "913d7300ceae3b2dbc2c50d1de4baacab4be7b9380491c27fab7418616a16ec3"
MODEL_SHA256 = "4f148ba8ae9c2c7fbee4af2b132db8d06c6a6545b47fc83bbb98c3d22b8393e6"
TOKENIZER_SHA256 = "da0e79933b9ed51798a3ae27893d3c5fa4a201126cef75586296df9b4d2c62a0"

#: Reference maximum sequence length for this model, from its published
#: ``sentence_bert_config.json``. Changing it changes the model's identity.
REFERENCE_MAX_SEQ = 256

#: Recorded identity of the frozen encoder. Any change here is a different model
#: and must invalidate cached embeddings.
MODEL_CARD = {
    "provider": "onnx-sentence-transformers",
    "model_identifier": "sentence-transformers/all-MiniLM-L6-v2",
    "origin": "Microsoft MiniLM-L6 distilled, contrastively fine-tuned by UKPLab "
              "on ~1B sentence pairs for semantic search",
    "distribution": "https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz",
    "revision": f"onnx bundle sha256 {BUNDLE_SHA256}",
    "model_sha256": MODEL_SHA256,
    "tokenizer_sha256": TOKENIZER_SHA256,
    "architecture": "BertModel, 6 layers, hidden 384, 12 heads, intermediate 1536",
    "precision": "fp32 (unquantized)",
    "vocabulary": 30522,
    "dimension": 384,
    "max_seq_length": REFERENCE_MAX_SEQ,
    "tokenizer": "BertTokenizer WordPiece, do_lower_case=true",
    "pooling": "attention-mask-weighted mean over last_hidden_state",
    "normalization": "L2 on the pooled vector",
    "distance_metric": "cosine",
    "query_prefix": None,
    "document_prefix": None,
    "contextual": True,
    "corpus_fitted": False,
    "provenance_verified_against_publisher": False,
}


def model_dir() -> Path:
    return Path(settings.data_dir) / "cache" / "models" / "exp009" / "onnx"


def ensure_extracted(bundle: Path | None = None) -> Path:
    """Unpack the downloaded bundle if it has not been unpacked yet."""
    target = model_dir()
    if (target / "model.onnx").exists():
        return target
    archive = bundle or target.parent / BUNDLE_FILENAME
    if not archive.exists():
        raise RuntimeError(
            f"Transformer bundle not found at {archive}. "
            "Download it first; see experiments/EXP-009/model-preregistration.md."
        )
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(target.parent)
    return target


class TransformerEncoder:
    """Mean-pooled contextual transformer encoder. Deterministic and frozen."""

    def __init__(self, max_seq: int = REFERENCE_MAX_SEQ, threads: int = 4):
        self.provider = MODEL_CARD["provider"]
        self.model_name = MODEL_CARD["model_identifier"]
        self.dimension = MODEL_CARD["dimension"]
        self.max_seq = max_seq
        self.threads = threads
        # The model's identity decides embedding validity. max_seq is part of that
        # identity: the same weights truncating at 256 and at 512 are two encoders.
        self.model_version = config_hash(
            {**{k: v for k, v in MODEL_CARD.items() if k not in ("origin", "distribution")},
             "max_seq_length": max_seq}
        )[:16]
        self._session = None
        self._tokenizer = None
        self._raw_tokenizer = None
        self._input_names: set[str] = set()
        self.texts_seen = 0
        self.texts_truncated = 0
        self.tokens_seen = 0
        self.tokens_kept = 0

    # -- loading ---------------------------------------------------------------

    def load(self) -> TransformerEncoder:
        if self._session is not None:
            return self
        import onnxruntime as ort
        from tokenizers import Tokenizer

        path = ensure_extracted()
        options = ort.SessionOptions()
        # Pinned so a re-run reproduces the stored vectors bit for bit.
        options.intra_op_num_threads = self.threads
        options.inter_op_num_threads = 1
        self._session = ort.InferenceSession(
            str(path / "model.onnx"), options, providers=["CPUExecutionProvider"]
        )
        self._input_names = {i.name for i in self._session.get_inputs()}
        self._tokenizer = Tokenizer.from_file(str(path / "tokenizer.json"))
        # Fixed-width padding: a chunk's vector must not depend on its batch mates.
        self._tokenizer.enable_truncation(max_length=self.max_seq)
        self._tokenizer.enable_padding(length=self.max_seq, pad_id=0, pad_token="[PAD]")
        return self

    # -- encoding --------------------------------------------------------------

    def embed(self, texts: Sequence[str], batch_size: int = 32) -> list[list[float]]:
        return [v.tolist() for v in self.embed_array(texts, batch_size=batch_size)]

    def embed_array(self, texts: Sequence[str], batch_size: int = 32) -> np.ndarray:
        if self._session is None:
            self.load()
        out: list[np.ndarray] = []
        for start in range(0, len(texts), batch_size):
            out.append(self._encode_batch(list(texts[start:start + batch_size])))
        if not out:
            return np.zeros((0, self.dimension), dtype=np.float32)
        return np.vstack(out)

    def _encode_batch(self, texts: list[str]) -> np.ndarray:
        encodings = self._tokenizer.encode_batch(texts)
        ids = np.array([e.ids for e in encodings], dtype=np.int64)
        mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
        types = np.array([e.type_ids for e in encodings], dtype=np.int64)

        for text, enc in zip(texts, encodings, strict=True):
            kept = int(sum(enc.attention_mask))
            self.texts_seen += 1
            self.tokens_kept += kept
            # Padding fills every sequence to max_seq, so length cannot reveal
            # truncation; a full attention mask can mean "exactly fits" or "was
            # cut short". Only those are re-tokenized without truncation, which
            # is what makes the coverage figure exact rather than a lower bound.
            if kept >= self.max_seq:
                total = self._untruncated_length(text)
                if total > self.max_seq:
                    self.texts_truncated += 1
                self.tokens_seen += total
            else:
                self.tokens_seen += kept

        feeds = {"input_ids": ids, "attention_mask": mask}
        if "token_type_ids" in self._input_names:
            feeds["token_type_ids"] = types

        hidden = self._session.run(None, feeds)[0]  # [batch, seq, dim]
        weights = mask.astype(np.float32)[:, :, None]
        summed = (hidden * weights).sum(axis=1)
        counts = np.clip(weights.sum(axis=1), 1e-9, None)
        pooled = summed / counts
        norms = np.linalg.norm(pooled, axis=1, keepdims=True)
        return (pooled / np.clip(norms, 1e-12, None)).astype(np.float32)

    def _untruncated_length(self, text: str) -> int:
        """Token count with truncation disabled, for truncation accounting only."""
        from tokenizers import Tokenizer

        if self._raw_tokenizer is None:
            raw = Tokenizer.from_file(str(model_dir() / "tokenizer.json"))
            # tokenizer.json ships its own saved truncation (128 for this model) and
            # from_file restores it. Without clearing that, this "untruncated" count
            # is itself truncated, which silently under-reports how much of a long
            # chunk the encoder never saw — it reported zero truncation on a corpus
            # whose largest chunk is 16,096 characters.
            raw.no_truncation()
            raw.no_padding()
            self._raw_tokenizer = raw
        return len(self._raw_tokenizer.encode(text, add_special_tokens=True).ids)

    def truncation_stats(self) -> dict:
        return {
            "texts_seen": self.texts_seen,
            "texts_truncated": self.texts_truncated,
            "truncation_rate": round(self.texts_truncated / self.texts_seen, 4) if self.texts_seen else None,
            "tokens_seen": self.tokens_seen,
            "tokens_kept": self.tokens_kept,
            "token_coverage": round(self.tokens_kept / self.tokens_seen, 4) if self.tokens_seen else None,
            "max_seq_length": self.max_seq,
        }


_INSTANCE: TransformerEncoder | None = None


def get_transformer_embedder(max_seq: int | None = None) -> TransformerEncoder:
    """Return the shared transformer encoder, loading it at most once per process."""
    global _INSTANCE
    wanted = max_seq if max_seq is not None else settings.transformer_max_seq
    if _INSTANCE is not None and _INSTANCE.max_seq == wanted:
        return _INSTANCE
    _INSTANCE = TransformerEncoder(max_seq=wanted).load()
    return _INSTANCE


def reset_transformer_embedder() -> None:
    global _INSTANCE
    _INSTANCE = None
