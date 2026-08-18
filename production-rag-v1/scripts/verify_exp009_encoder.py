#!/usr/bin/env python3
"""Verify the EXP-009 encoder before it is allowed to produce any result.

Hugging Face is unreachable from this environment, so the bundle's checksum cannot
be verified against the upstream publisher. Two independent checks are recorded in
its place, and both are run before the golden set is touched:

1. **Structural** — architecture, precision, graph shape, tokenizer vocabulary.
2. **Behavioural** — held-out sentence pairs, none of them from this corpus. A
   trained sentence-similarity encoder separates paraphrases from unrelated
   sentences; an untrained or plain-MLM BERT scores everything alike. The decisive
   pair has *no content-word overlap at all*, which is precisely the vocabulary
   mismatch EXP-009 exists to test.

A third check covers reproducibility: a chunk's vector must not depend on which
other chunks shared its batch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from rag_v1.embedders_transformer import (
    MODEL_CARD,
    MODEL_SHA256,
    TOKENIZER_SHA256,
    TransformerEncoder,
    model_dir,
)

# Held out from this corpus on purpose: none of these sentences are documentation.
PARAPHRASES = [
    ("A man is eating food.", "A man is eating a meal."),
    ("A man is playing a guitar.", "Someone is performing on a musical instrument."),
    # Zero content-word overlap. Lexical retrieval scores this pair at nothing.
    ("How do I reset my password?",
     "What are the steps to change my login credentials?"),
]
UNRELATED = [
    ("A man is eating food.", "The train arrives at nine o'clock."),
    ("A man is playing a guitar.", "The stock market closed lower today."),
    ("How do I reset my password?", "The cat slept on the windowsill all afternoon."),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="experiments/EXP-009/encoder-verification.json")
    parser.add_argument("--max-seq", type=int, default=256)
    args = parser.parse_args()

    encoder = TransformerEncoder(max_seq=args.max_seq).load()
    path = model_dir()
    failures: list[str] = []

    structural = {
        "model_sha256": sha256(path / "model.onnx"),
        "model_sha256_expected": MODEL_SHA256,
        "tokenizer_sha256": sha256(path / "tokenizer.json"),
        "tokenizer_sha256_expected": TOKENIZER_SHA256,
        "config": json.loads((path / "config.json").read_text()),
        "graph_inputs": sorted(encoder._input_names),
        "output_dimension": encoder.dimension,
        "tokenizer_vocab_size": encoder._tokenizer.get_vocab_size(),
    }
    if structural["model_sha256"] != MODEL_SHA256:
        failures.append("model.onnx checksum does not match the preregistered value")
    if structural["tokenizer_sha256"] != TOKENIZER_SHA256:
        failures.append("tokenizer.json checksum does not match the preregistered value")
    cfg = structural["config"]
    for key, expected in (("num_hidden_layers", 6), ("hidden_size", 384),
                          ("num_attention_heads", 12), ("intermediate_size", 1536),
                          ("vocab_size", 30522), ("model_type", "bert")):
        if cfg.get(key) != expected:
            failures.append(f"config.{key}={cfg.get(key)!r}, expected {expected!r}")

    # -- behavioural -----------------------------------------------------------
    pairs = PARAPHRASES + UNRELATED
    texts = [t for pair in pairs for t in pair]
    vectors = encoder.embed_array(texts, batch_size=len(texts))
    sims = [float(vectors[2 * i] @ vectors[2 * i + 1]) for i in range(len(pairs))]
    paraphrase_sims = sims[:len(PARAPHRASES)]
    unrelated_sims = sims[len(PARAPHRASES):]

    behavioural = {
        "paraphrase_pairs": [
            {"a": a, "b": b, "cosine": round(s, 4)}
            for (a, b), s in zip(PARAPHRASES, paraphrase_sims, strict=True)
        ],
        "unrelated_pairs": [
            {"a": a, "b": b, "cosine": round(s, 4)}
            for (a, b), s in zip(UNRELATED, unrelated_sims, strict=True)
        ],
        "min_paraphrase": round(min(paraphrase_sims), 4),
        "max_unrelated": round(max(unrelated_sims), 4),
        "separation": round(min(paraphrase_sims) - max(unrelated_sims), 4),
        "zero_overlap_pair_cosine": round(paraphrase_sims[2], 4),
    }
    if behavioural["separation"] <= 0:
        failures.append(
            "encoder does not separate paraphrases from unrelated sentences; "
            "these weights do not behave like a trained similarity encoder"
        )
    if behavioural["zero_overlap_pair_cosine"] < 0.4:
        failures.append(
            "encoder scores the zero-lexical-overlap paraphrase below 0.4; it cannot "
            "bridge vocabulary mismatch and is not a valid instrument for EXP-009"
        )

    # -- reproducibility -------------------------------------------------------
    probe = "The rate limit error returns a 429 status code."
    alone = encoder.embed_array([probe], batch_size=1)[0]
    padded = encoder.embed_array(["unrelated filler sentence", probe, "x"], batch_size=8)[1]
    twice = encoder.embed_array([probe], batch_size=1)[0]
    reproducibility = {
        "batch_composition_max_abs_delta": float(np.abs(alone - padded).max()),
        "repeat_call_max_abs_delta": float(np.abs(alone - twice).max()),
        "bitwise_identical_across_batches": bool(np.array_equal(alone, padded)),
        "bitwise_identical_across_calls": bool(np.array_equal(alone, twice)),
    }
    if not reproducibility["bitwise_identical_across_calls"]:
        failures.append("encoder is not deterministic across repeated calls")
    if reproducibility["batch_composition_max_abs_delta"] > 1e-5:
        failures.append("a vector depends on which texts shared its batch")

    payload = {
        "experiment_id": "EXP-009",
        "model_card": MODEL_CARD,
        "model_fingerprint": encoder.model_version,
        "provenance_note": (
            "huggingface.co is blocked by egress policy, so the bundle cannot be "
            "checksummed against the upstream publisher. Structural and behavioural "
            "checks are recorded instead."
        ),
        "structural": structural,
        "behavioural": behavioural,
        "reproducibility": reproducibility,
        "failures": failures,
        "passed": not failures,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({k: v for k, v in payload.items()
                      if k not in ("model_card", "structural")}, indent=2))
    print(f"\nwrote {out}")
    if failures:
        print("\nENCODER VERIFICATION FAILED — EXP-009 must not proceed.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
