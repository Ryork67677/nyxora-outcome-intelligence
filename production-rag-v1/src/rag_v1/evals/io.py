from __future__ import annotations

import json
from pathlib import Path

from rag_v1.types import EvalCase


def load_cases(path: Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            cases.append(EvalCase.model_validate_json(line))
        except Exception as exc:
            raise ValueError(f"Invalid JSONL at {path}:{lineno}: {exc}") from exc
    return cases


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
