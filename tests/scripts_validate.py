"""Import shim so the validator's logic is testable without running the CLI."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "_validate_golden", Path(__file__).resolve().parents[1] / "scripts" / "validate_golden.py")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

validate_cases = _module.validate

__all__ = ["validate_cases"]
