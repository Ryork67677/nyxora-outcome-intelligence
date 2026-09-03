"""V2 SYSTEM-G development-path CE constructor (PERF-003 D1).

Does not edit CrossEncoderReranker default kwargs. V1 / validation / holdout
callers that construct CrossEncoderReranker() keep pad='fixed', threads=4,
bucket_by_length=False, fast=False.

D1: pad each batch to that batch's max seq length, deterministic length
bucketing, ORT threads UNCHANGED (intra_op=4, inter_op=1). No fast=True.
"""
from __future__ import annotations

from cross_encoder import CrossEncoderReranker


def make_v2_system_g_d1_reranker() -> CrossEncoderReranker:
    """SYSTEM-G V2 development path: D1 only. threads left at class default 4."""
    return CrossEncoderReranker(pad="batch", bucket_by_length=True)
