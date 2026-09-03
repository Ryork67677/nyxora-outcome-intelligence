#!/usr/bin/env python3
"""Obtain and verify the frozen SYSTEM-A MiniLM ONNX encoder.

The freeze is the Chroma S3 redistribution of sentence-transformers/all-MiniLM-L6-v2
recorded in experiments/EXP-009/model-preregistration.md. This script downloads that
exact tar if missing, verifies the preregistered checksums, extracts it to the path
``TransformerEncoder`` already reads, and refuses any substitute.
"""

from __future__ import annotations

import argparse
import hashlib
import tarfile
import urllib.request
from pathlib import Path

from rag_v1.embedders_transformer import (
    BUNDLE_FILENAME,
    BUNDLE_SHA256,
    MODEL_SHA256,
    TOKENIZER_SHA256,
    TransformerEncoder,
    model_dir,
)
from rag_v1.ids import stable_id
from rag_v1.systems import MAX_SEQ, TRANSFORMER_FINGERPRINT, TRANSFORMER_MODEL

URL = "https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def bundle_path() -> Path:
    return model_dir().parent / BUNDLE_FILENAME


def obtain(force_download: bool = False) -> dict:
    archive = bundle_path()
    archive.parent.mkdir(parents=True, exist_ok=True)
    downloaded = False
    if force_download or not archive.exists():
        print(f"downloading {URL}")
        urllib.request.urlretrieve(URL, archive)
        downloaded = True
    bundle_hash = sha256_file(archive)
    if bundle_hash != BUNDLE_SHA256:
        raise SystemExit(
            f"STOP: onnx.tar.gz sha256 {bundle_hash} != frozen {BUNDLE_SHA256}. "
            "Refusing a substitute encoder."
        )
    target = model_dir()
    if not (target / "model.onnx").exists():
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(target.parent)
    model_hash = sha256_file(target / "model.onnx")
    tok_hash = sha256_file(target / "tokenizer.json")
    if model_hash != MODEL_SHA256:
        raise SystemExit(f"STOP: model.onnx sha256 {model_hash} != frozen {MODEL_SHA256}")
    if tok_hash != TOKENIZER_SHA256:
        raise SystemExit(
            f"STOP: tokenizer.json sha256 {tok_hash} != frozen {TOKENIZER_SHA256}"
        )
    encoder = TransformerEncoder(max_seq=MAX_SEQ)
    model_id = stable_id(
        "emb", encoder.provider, encoder.model_name, encoder.model_version,
        encoder.dimension, length=32,
    )
    if encoder.model_version != TRANSFORMER_FINGERPRINT:
        raise SystemExit(
            f"STOP: encoder fingerprint {encoder.model_version} != "
            f"frozen {TRANSFORMER_FINGERPRINT}"
        )
    if model_id != TRANSFORMER_MODEL:
        raise SystemExit(f"STOP: model_id {model_id} != frozen {TRANSFORMER_MODEL}")
    encoder.load()
    return {
        "url": URL,
        "downloaded_this_run": downloaded,
        "bundle_path": str(archive),
        "bundle_sha256": bundle_hash,
        "model_onnx_sha256": model_hash,
        "tokenizer_json_sha256": tok_hash,
        "extracted_dir": str(target),
        "encoder_fingerprint": encoder.model_version,
        "model_id": model_id,
        "max_seq": encoder.max_seq,
        "graph_inputs": sorted(encoder._input_names),
        "match_frozen_system_a": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args()
    payload = obtain(force_download=args.force_download)
    import json
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
