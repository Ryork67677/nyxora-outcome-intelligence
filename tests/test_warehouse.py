from __future__ import annotations

import duckdb

from nyxora_outcome_intelligence.config import ProjectPaths
from nyxora_outcome_intelligence.warehouse import read_table, validate_warehouse


def test_data_contracts_and_mart_reconciliation(built_project: ProjectPaths) -> None:
    report = validate_warehouse(built_project)
    assert report["status"] == "passed"
    assert all(check["passed"] for check in report["checks"])

    connection = duckdb.connect(str(built_project.warehouse_path), read_only=True)
    try:
        matured = connection.execute(
            "SELECT COUNT(*) FROM fct_lead_outcomes WHERE is_matured"
        ).fetchone()[0]
        channel_total = connection.execute(
            "SELECT SUM(leads) FROM mart_channel_performance"
        ).fetchone()[0]
        training = connection.execute("SELECT COUNT(*) FROM model_training_set").fetchone()[0]
    finally:
        connection.close()

    assert matured == channel_total == training


def test_read_table_allowlist(built_project: ProjectPaths) -> None:
    frame = read_table(built_project, "mart_monthly_funnel")
    assert not frame.empty
    assert {"month", "leads", "booking_rate"}.issubset(frame.columns)

    try:
        read_table(built_project, "pipeline_metadata")
    except ValueError as error:
        assert "Unsupported table" in str(error)
    else:
        raise AssertionError("Expected a ValueError")

