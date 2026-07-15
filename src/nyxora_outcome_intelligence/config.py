from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @property
    def raw_dir(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def warehouse_dir(self) -> Path:
        return self.root / "data" / "warehouse"

    @property
    def warehouse_path(self) -> Path:
        return self.warehouse_dir / "outcome_intelligence.duckdb"

    @property
    def artifacts_dir(self) -> Path:
        return self.root / "artifacts"

    @property
    def sql_dir(self) -> Path:
        return self.root / "sql"

    @property
    def model_path(self) -> Path:
        return self.artifacts_dir / "model.joblib"

    def ensure(self) -> None:
        for directory in (self.raw_dir, self.warehouse_dir, self.artifacts_dir):
            directory.mkdir(parents=True, exist_ok=True)


def default_root() -> Path:
    configured = os.environ.get("NYXORA_PROJECT_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    working_directory = Path.cwd().resolve()
    if (working_directory / "sql").is_dir():
        return working_directory
    return Path(__file__).resolve().parents[2]


DEFAULT_AS_OF_DATE = date(2026, 7, 14)
DEFAULT_SEED = 67677
DEFAULT_LEAD_COUNT = 10_000
OBSERVATION_HOURS = 24
OUTCOME_WINDOW_DAYS = 14
