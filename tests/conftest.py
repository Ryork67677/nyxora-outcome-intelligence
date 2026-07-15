from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

import pytest

from nyxora_outcome_intelligence.config import ProjectPaths
from nyxora_outcome_intelligence.dashboard import build_dashboard_artifact
from nyxora_outcome_intelligence.modeling import train_models
from nyxora_outcome_intelligence.monitoring import build_monitoring_report
from nyxora_outcome_intelligence.scoring import score_recent_candidates
from nyxora_outcome_intelligence.synthetic import generate_dataset, write_dataset
from nyxora_outcome_intelligence.warehouse import build_warehouse, validate_warehouse


@pytest.fixture(scope="session")
def built_project(tmp_path_factory: pytest.TempPathFactory) -> ProjectPaths:
    root = tmp_path_factory.mktemp("outcome-intelligence")
    source_root = Path(__file__).resolve().parents[1]
    shutil.copytree(source_root / "sql", root / "sql")
    paths = ProjectPaths(root)
    paths.ensure()
    dataset = generate_dataset(
        lead_count=1_800,
        seed=67677,
        as_of_date=date(2026, 7, 14),
        lookback_days=365,
    )
    write_dataset(dataset, paths.raw_dir)
    build_warehouse(paths, as_of_date=date(2026, 7, 14))
    validate_warehouse(paths)
    train_models(paths, seed=67677, as_of_date="2026-07-14")
    score_recent_candidates(paths)
    build_monitoring_report(paths)
    build_dashboard_artifact(paths, as_of_date="2026-07-14")
    return paths

