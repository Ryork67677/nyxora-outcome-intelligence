"""The only supported way to load a split, and the guard on the frozen holdout.

Development and validation load freely. The holdout does not: it is frozen, and every
time it is read the reading is deliberate and recorded. The guard is not security — any
script can read the JSON directly — it is a tripwire against the accident that actually
happens, which is a convenience helper that enumerates "all cases" and quietly pulls the
holdout into a tuning loop.

``load("holdout")`` raises. Reading it requires ``allow_frozen_holdout=True``, which
prints a warning and appends to an access log.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

SPLIT_DIR = Path("evals/splits/gold150-v1")
ACCESS_LOG = SPLIT_DIR / "holdout-access.log.jsonl"
DEVELOPMENT = "development"
VALIDATION = "validation"
HOLDOUT = "holdout"
OPEN_SPLITS = (DEVELOPMENT, VALIDATION)
#: The flag a final holdout runner must pass on the command line.
CLI_FLAG = "--allow-frozen-holdout"


class FrozenHoldoutError(RuntimeError):
    """Raised when the holdout is read without an explicit, recorded intent."""


def split_path(split: str) -> Path:
    return SPLIT_DIR / f"{split}.json"


def is_frozen() -> bool:
    lock = SPLIT_DIR / "holdout.lock.json"
    if not lock.exists():
        return False
    return bool(json.loads(lock.read_text()).get("holdout_frozen"))


def load(split: str, *, allow_frozen_holdout: bool = False,
         reason: str | None = None) -> dict:
    """Load one split. The holdout needs ``allow_frozen_holdout=True`` and a reason."""
    if split not in (DEVELOPMENT, VALIDATION, HOLDOUT):
        raise ValueError(f"unknown split {split!r}")
    if split == HOLDOUT and is_frozen() and not allow_frozen_holdout:
        raise FrozenHoldoutError(
            "the holdout is frozen and was not explicitly requested. A development or "
            "validation run must not read it. If this really is the final holdout "
            f"evaluation, pass {CLI_FLAG} (allow_frozen_holdout=True) and a reason; the "
            "access will be printed and logged.")
    payload = json.loads(split_path(split).read_text())
    if split == HOLDOUT and allow_frozen_holdout:
        record = {
            "accessed_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "reason": reason or "(no reason given)",
            "count": payload["count"],
            "pid": os.getpid(),
        }
        print("WARNING: reading the FROZEN HOLDOUT "
              f"({payload['count']} cases). Reason: {record['reason']}. "
              "This access is logged. Holdout membership must not change because of "
              "what a system scores on it.")
        with ACCESS_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return payload


def case_ids(split: str, **kwargs) -> list[str]:
    return load(split, **kwargs)["case_ids"]


def load_development() -> dict:
    return load(DEVELOPMENT)


def load_validation() -> dict:
    return load(VALIDATION)


def all_evaluable_case_ids() -> list[str]:
    """Every case an ordinary script may enumerate. The holdout is not in it.

    This exists so that "give me all the cases" has an answer that is safe to call. A
    helper that returned all 150 is how a frozen holdout leaks into a tuning loop.
    """
    return sorted(case_ids(DEVELOPMENT) + case_ids(VALIDATION))


__all__ = ["ACCESS_LOG", "CLI_FLAG", "DEVELOPMENT", "HOLDOUT", "OPEN_SPLITS",
           "SPLIT_DIR", "VALIDATION", "FrozenHoldoutError", "all_evaluable_case_ids",
           "case_ids", "is_frozen", "load", "load_development", "load_validation",
           "split_path"]
