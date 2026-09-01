#!/usr/bin/env python3
"""Preregistered EXP-015 cross-encoder: ONNX MiniLM, raw logit, pair truncation 512.

Not the sentence-transformers CrossEncoder class. Pair format is BERT
``[CLS] query [SEP] passage [SEP]``, longest_first at 512, Identity activation.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

CE_ROOT = Path(
    "experiments/EXP-015/models/cross-encoder-ms-marco-MiniLM-L6-v2/"
    "233902d25c440f23af6f7d6e94d2946bac0bee0a"
)
CE_ONNX = CE_ROOT / "onnx" / "model.onnx"
CE_TOKENIZER = CE_ROOT / "tokenizer.json"
CE_SHA256 = "5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a"
CE_REVISION = "233902d25c440f23af6f7d6e94d2946bac0bee0a"
CE_NAME = "cross-encoder/ms-marco-MiniLM-L6-v2"
MAX_LENGTH = 512


class CrossEncoderReranker:
    """ONNX MiniLM cross-encoder. Default path is EXP-015/E-L10 identical.

    Optional kwargs do not change callers that construct ``CrossEncoderReranker()``.
    ``pad="fixed"`` (default) pads every pair to 512. ``pad="batch"`` pads to the
    longest sequence in the current encode_batch (still truncated longest_first
    at 512). ``bucket_by_length`` sorts pairs by unpadded length before batching
    so short pairs are not dragged to 512 by a long batch-mate. ``fast=True``
    selects threads=8, pad=batch, bucket_by_length=True. E-L10 must keep defaults.
    """

    def __init__(
        self,
        threads: int = 4,
        *,
        pad: str = "fixed",
        pad_to_multiple_of: int | None = None,
        bucket_by_length: bool = False,
        fast: bool = False,
    ):
        import hashlib
        import onnxruntime as ort
        from tokenizers import Tokenizer

        if fast:
            threads = 8
            pad = "batch"
            bucket_by_length = True
        if pad not in ("fixed", "batch"):
            raise ValueError(f"pad must be 'fixed' or 'batch', got {pad!r}")
        if not CE_ONNX.exists():
            raise RuntimeError(f"cross-encoder ONNX missing at {CE_ONNX}")
        digest = hashlib.sha256(CE_ONNX.read_bytes()).hexdigest()
        if digest != CE_SHA256:
            raise RuntimeError(
                f"cross-encoder sha256 {digest} != preregistered {CE_SHA256}"
            )
        self.artifact_sha256 = digest
        self.threads = threads
        self.pad = pad
        self.pad_to_multiple_of = pad_to_multiple_of
        self.bucket_by_length = bucket_by_length
        self.fast = fast
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        options.inter_op_num_threads = 1
        self._session = ort.InferenceSession(
            str(CE_ONNX), options, providers=["CPUExecutionProvider"]
        )
        self._input_names = {i.name for i in self._session.get_inputs()}
        self._tokenizer = Tokenizer.from_file(str(CE_TOKENIZER))
        self._tokenizer.enable_truncation(max_length=MAX_LENGTH, strategy="longest_first")
        pad_kwargs = {"pad_id": 0, "pad_token": "[PAD]"}
        if pad_to_multiple_of:
            pad_kwargs["pad_to_multiple_of"] = pad_to_multiple_of
        if pad == "fixed":
            self._tokenizer.enable_padding(length=MAX_LENGTH, **pad_kwargs)
        else:
            self._tokenizer.enable_padding(**pad_kwargs)
        self._raw_tokenizer = None
        if bucket_by_length:
            raw = Tokenizer.from_file(str(CE_TOKENIZER))
            raw.enable_truncation(max_length=MAX_LENGTH, strategy="longest_first")
            self._raw_tokenizer = raw

    def score_pairs(self, query: str, passages: list[str], batch_size: int = 16) -> list[float]:
        if not passages:
            return []
        if self.bucket_by_length:
            return self._score_bucketed(query, passages, batch_size)
        return self._score_in_order(query, passages, batch_size)

    def _score_bucketed(self, query: str, passages: list[str], batch_size: int) -> list[float]:
        raw = self._raw_tokenizer.encode_batch([(query, p) for p in passages])
        order = sorted(range(len(passages)), key=lambda i: (len(raw[i].ids), i))
        sorted_ps = [passages[i] for i in order]
        scores_sorted = self._score_in_order(query, sorted_ps, batch_size)
        out = [0.0] * len(passages)
        for new_i, orig_i in enumerate(order):
            out[orig_i] = scores_sorted[new_i]
        return out

    def _score_in_order(self, query: str, passages: list[str], batch_size: int) -> list[float]:
        out: list[float] = []
        for start in range(0, len(passages), batch_size):
            batch = passages[start:start + batch_size]
            encodings = self._tokenizer.encode_batch([(query, p) for p in batch])
            ids = np.array([e.ids for e in encodings], dtype=np.int64)
            mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
            types = np.array([e.type_ids for e in encodings], dtype=np.int64)
            feeds = {"input_ids": ids, "attention_mask": mask}
            if "token_type_ids" in self._input_names:
                feeds["token_type_ids"] = types
            logits = self._session.run(None, feeds)[0]
            out.extend(float(v) for v in logits.reshape(-1))
        return out


def rerank(hits, query: str, encoder: CrossEncoderReranker, top_k: int = 10) -> list:
    """Reorder SYSTEM-A fused hits. Tie-break: score desc, A-rank asc, chunk_id asc."""
    scores = encoder.score_pairs(query, [h.text for h in hits])
    decorated = list(zip(hits, scores, strict=True))
    decorated.sort(key=lambda row: (-row[1], row[0].rank, row[0].chunk_id))
    out = []
    for new_rank, (hit, score) in enumerate(decorated[:top_k], start=1):
        copied = hit.model_copy(deep=True)
        copied.rank = new_rank
        copied.score = score
        copied.retriever = "cross_encoder"
        copied.metadata = {
            **copied.metadata,
            "ce_score": score,
            "system_a_rank": hit.rank,
        }
        out.append(copied)
    return out, scores
