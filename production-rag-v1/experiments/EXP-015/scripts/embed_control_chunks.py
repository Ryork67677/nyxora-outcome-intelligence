#!/usr/bin/env python3
"""Embed cs_v1_control with the frozen MiniLM ONNX encoder (max_seq=512).

Wraps scripts/build_transformer_embeddings.py so the EXP-015 run is reproducible
from this directory. Refuses to start if the encoder fingerprint would not match
frozen SYSTEM-A.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from rag_v1.embedders_transformer import TransformerEncoder
from rag_v1.ids import stable_id
from rag_v1.systems import MAX_SEQ, TRANSFORMER_FINGERPRINT, TRANSFORMER_MODEL

ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    enc = TransformerEncoder(max_seq=MAX_SEQ)
    model_id = stable_id(
        "emb", enc.provider, enc.model_name, enc.model_version, enc.dimension, length=32
    )
    if enc.model_version != TRANSFORMER_FINGERPRINT or model_id != TRANSFORMER_MODEL:
        print(
            f"STOP: encoder {enc.model_version}/{model_id} != "
            f"{TRANSFORMER_FINGERPRINT}/{TRANSFORMER_MODEL}",
            file=sys.stderr,
        )
        return 2
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "build_transformer_embeddings.py"),
        "--chunk-set",
        "cs_v1_control",
        "--max-seq",
        "512",
        "--batch",
        "64",
        "--out",
        str(ROOT / "experiments" / "EXP-015" / "embedding-build.json"),
    ]
    return subprocess.call(cmd, cwd=str(ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
