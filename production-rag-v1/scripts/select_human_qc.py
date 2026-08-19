#!/usr/bin/env python3
"""GOLD-001: choose which candidates a person must actually look at.

The point is to keep human oversight real while keeping the queue small. A person
sees everything the two models disagreed about or were unsure of, plus a fixed
random sample of the cases they agreed on — because agreement between two models is
correlated, not independent, and a shared blind spot would otherwise pass unseen.

The sample is drawn with a recorded seed so the same batch always produces the same
queue.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

QC_SEED = 20250819


def build_queue(records: list[dict], sample_rate: float, seed: int) -> dict:
    must_review, passed = [], []
    for record in records:
        status = record.get("verification_status")
        if status == "dual_llm_pass":
            passed.append(record)
        elif status in ("dual_llm_fail", "needs_human_review", "candidate_unverified"):
            must_review.append(record)

    rng = random.Random(seed)
    ordered = sorted(passed, key=lambda r: r["candidate_id"])
    sample_size = max(1, round(len(ordered) * sample_rate)) if ordered else 0
    sampled = sorted(rng.sample(ordered, min(sample_size, len(ordered))),
                     key=lambda r: r["candidate_id"]) if ordered else []

    return {
        "seed": seed,
        "sample_rate": sample_rate,
        "must_review": [r["candidate_id"] for r in must_review],
        "qc_sample_of_dual_llm_pass": [r["candidate_id"] for r in sampled],
        "dual_llm_pass_total": len(ordered),
        "human_queue_size": len(must_review) + len(sampled),
        "rationale": (
            "Disagreements, uncertainty and failures always reach a person. Agreed "
            "passes are sampled because two models agreeing is correlated evidence, "
            "not independent confirmation."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch")
    parser.add_argument("--sample-rate", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=QC_SEED)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    batch = json.loads(Path(args.batch).read_text())
    queue = build_queue(batch["records"], args.sample_rate, args.seed)
    queue["batch"] = batch.get("batch")

    out = Path(args.out) if args.out else Path(args.batch).with_name(
        f"human_qc_queue_batch_{batch.get('batch', 0):03d}.json")
    out.write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")

    print(f"human queue: {queue['human_queue_size']} of {len(batch['records'])} candidates")
    print(f"  must review ({len(queue['must_review'])}): {', '.join(queue['must_review']) or '—'}")
    print(f"  QC sample ({len(queue['qc_sample_of_dual_llm_pass'])} of "
          f"{queue['dual_llm_pass_total']} passes, seed {queue['seed']}): "
          f"{', '.join(queue['qc_sample_of_dual_llm_pass']) or '—'}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
