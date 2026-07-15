from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import duckdb
import pandas as pd

from .config import ProjectPaths


class DataQualityError(RuntimeError):
    """Raised when a blocking data contract check fails."""


def _sql_literal(path: Path) -> str:
    return str(path.resolve()).replace("'", "''").replace("\\", "/")


def build_warehouse(paths: ProjectPaths, *, as_of_date: date) -> Path:
    paths.ensure()
    leads_path = paths.raw_dir / "leads.csv"
    events_path = paths.raw_dir / "events.csv"
    if not leads_path.exists() or not events_path.exists():
        raise FileNotFoundError("Raw leads.csv and events.csv must exist before building the warehouse")

    connection = duckdb.connect(str(paths.warehouse_path))
    try:
        connection.execute("SET TimeZone = 'UTC'")
        for sql_path in sorted(paths.sql_dir.glob("*.sql")):
            sql = sql_path.read_text(encoding="utf-8").format(
                leads_path=_sql_literal(leads_path),
                events_path=_sql_literal(events_path),
                as_of_date=as_of_date.isoformat(),
            )
            connection.execute(sql)
    finally:
        connection.close()
    return paths.warehouse_path


def validate_warehouse(paths: ProjectPaths) -> dict[str, object]:
    connection = duckdb.connect(str(paths.warehouse_path), read_only=True)
    connection.execute("SET TimeZone = 'UTC'")
    checks: list[dict[str, object]] = []

    def check(name: str, query: str, expected: int = 0, *, blocking: bool = True) -> None:
        actual = int(connection.execute(query).fetchone()[0])
        checks.append(
            {
                "name": name,
                "expected": expected,
                "actual": actual,
                "passed": actual == expected,
                "blocking": blocking,
            }
        )

    try:
        check(
            "unique lead ids",
            "SELECT COUNT(*) - COUNT(DISTINCT lead_id) FROM stg_leads",
        )
        check(
            "unique event ids",
            "SELECT COUNT(*) - COUNT(DISTINCT event_id) FROM stg_events",
        )
        check(
            "events reference a known lead",
            """
            SELECT COUNT(*)
            FROM stg_events e
            LEFT JOIN stg_leads l USING (lead_id)
            WHERE l.lead_id IS NULL
            """,
        )
        check(
            "required lead fields are present",
            """
            SELECT COUNT(*) FROM stg_leads
            WHERE lead_id IS NULL OR created_at IS NULL OR channel IS NULL
               OR campaign IS NULL OR service_type IS NULL OR region IS NULL
            """,
        )
        check(
            "response minutes stay inside the 24-hour observation window",
            "SELECT COUNT(*) FROM stg_leads WHERE response_minutes < 0 OR response_minutes > 1440",
        )
        check(
            "follow-up count is bounded",
            "SELECT COUNT(*) FROM stg_leads WHERE follow_up_count < 0 OR follow_up_count > 6",
        )
        check(
            "non-consented leads receive no follow-up",
            "SELECT COUNT(*) FROM stg_leads WHERE NOT consent_to_contact AND follow_up_count <> 0",
        )
        check(
            "events never precede lead creation",
            """
            SELECT COUNT(*)
            FROM stg_events e
            JOIN stg_leads l USING (lead_id)
            WHERE e.event_at < l.created_at
            """,
        )
        check(
            "outcome flags preserve funnel order",
            """
            SELECT COUNT(*) FROM fct_lead_outcomes
            WHERE attended > booked OR won > attended
            """,
        )

        summary = connection.execute(
            """
            SELECT
                COUNT(*) AS leads,
                SUM(booked) AS booked,
                ROUND(AVG(booked), 6) AS observed_booking_rate,
                SUM(CASE WHEN is_matured THEN 1 ELSE 0 END) AS matured_leads,
                MIN(created_at) AS first_created_at,
                MAX(created_at) AS last_created_at
            FROM fct_lead_outcomes
            """
        ).fetchdf().iloc[0].to_dict()
    finally:
        connection.close()

    for key, value in list(summary.items()):
        if hasattr(value, "item"):
            summary[key] = value.item()
        if isinstance(summary[key], (pd.Timestamp, datetime)):
            summary[key] = summary[key].isoformat()

    blocking_failures = [item for item in checks if item["blocking"] and not item["passed"]]
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "passed" if not blocking_failures else "failed",
        "summary": summary,
        "checks": checks,
    }
    report_path = paths.artifacts_dir / "data_quality_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if blocking_failures:
        names = ", ".join(str(item["name"]) for item in blocking_failures)
        raise DataQualityError(f"Blocking data-quality checks failed: {names}")
    return report


def read_table(paths: ProjectPaths, table: str) -> pd.DataFrame:
    allowed = {
        "model_training_set",
        "mart_monthly_funnel",
        "mart_channel_performance",
        "mart_campaign_performance",
        "mart_recent_candidates",
        "fct_lead_outcomes",
    }
    if table not in allowed:
        raise ValueError(f"Unsupported table: {table}")
    connection = duckdb.connect(str(paths.warehouse_path), read_only=True)
    try:
        connection.execute("SET TimeZone = 'UTC'")
        return connection.execute(f"SELECT * FROM {table}").fetchdf()
    finally:
        connection.close()
