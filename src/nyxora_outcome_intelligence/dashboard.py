from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd

from .config import ProjectPaths

QUERIES = {
    "summary": """
        SELECT
            COUNT(*)::INTEGER AS matured_leads,
            SUM(booked)::INTEGER AS booked_leads,
            ROUND(AVG(booked), 6) AS booking_rate,
            ROUND(MEDIAN(response_minutes), 2) AS median_response_minutes,
            (SELECT test_roc_auc FROM mart_model_summary) AS test_roc_auc,
            (SELECT COUNT(*)::INTEGER FROM mart_scored_candidates) AS open_candidates,
            (SELECT MAX(psi) FROM mart_feature_drift) AS maximum_psi
        FROM fct_lead_outcomes
        WHERE is_matured
    """,
    "monthly": "SELECT * FROM mart_monthly_funnel ORDER BY month",
    "channels": "SELECT * FROM mart_channel_performance ORDER BY booking_rate DESC",
    "campaigns": "SELECT * FROM mart_campaign_performance ORDER BY booking_rate DESC LIMIT 10",
    "calibration": "SELECT * FROM mart_model_calibration ORDER BY decile",
    "importance": "SELECT * FROM mart_feature_importance ORDER BY importance_mean DESC LIMIT 8",
    "drift": "SELECT * FROM mart_feature_drift ORDER BY psi DESC",
    "candidates": """
        SELECT
            lead_id,
            channel,
            service_type,
            ROUND(booking_probability, 4) AS booking_probability,
            ROUND(priority_score, 2) AS priority_score,
            recommended_action,
            ROUND(response_minutes, 1) AS response_minutes,
            ROUND(estimated_value, 2) AS estimated_value
        FROM mart_scored_candidates
        ORDER BY priority_score DESC
        LIMIT 12
    """,
}


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    clean = frame.astype(object).where(pd.notna(frame), None)
    records = clean.to_dict(orient="records")
    return [{key: _json_value(value) for key, value in row.items()} for row in records]


def _json_value(value: Any) -> Any:
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def _source(
    source_id: str,
    label: str,
    sql: str,
    tables: list[str],
    generated_at: str,
    definitions: list[str],
    filters: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": source_id,
        "label": label,
        "query": {
            "sql": sql.strip(),
            "description": label,
            "engine": "DuckDB",
            "language": "sql",
            "executed_at": generated_at,
            "tables_used": tables,
            "filters": filters or [],
            "metric_definitions": definitions,
        },
    }


def build_dashboard_artifact(paths: ProjectPaths, *, as_of_date: str) -> Path:
    generated_at = datetime.now(UTC).isoformat()
    connection = duckdb.connect(str(paths.warehouse_path), read_only=True)
    try:
        datasets = {
            dataset_id: _records(connection.execute(sql).fetchdf())
            for dataset_id, sql in QUERIES.items()
        }
    finally:
        connection.close()

    definitions = {
        "summary": [
            "Matured leads: leads created at least 14 days before the synthetic as-of timestamp.",
            "Booking rate: matured leads with a consultation_booked event divided by matured leads.",
            "Median response: median minutes to first contact inside the 24-hour observation window; 1,440 represents no contact.",
            "Test ROC AUC: discrimination on the newest chronological 15% holdout set.",
            "Open candidates: unbooked leads created in the latest 14 days with a completed 24-hour observation window.",
        ],
        "monthly": [
            "Monthly booking rate: booked matured leads divided by matured leads created in the month.",
            "Only fully observed leads are included; timestamps use UTC.",
        ],
        "channels": [
            "Channel booking rate: booked matured leads divided by matured leads for the acquisition channel.",
            "Pipeline value: sum of synthetic estimated lead value, not realized revenue.",
        ],
        "calibration": [
            "Predictions are grouped into equal-frequency deciles on the chronological holdout set.",
            "Observed booking rate is the booked share within each decile.",
        ],
        "importance": [
            "Permutation importance: mean change in holdout ROC AUC after shuffling one input feature.",
            "Importance describes predictive association, not causality.",
        ],
        "drift": [
            "Population Stability Index compares the oldest 70% reference period with the newest 30% comparison period.",
            "PSI below 0.10 is stable, 0.10-0.20 is watch, and 0.20 or above requires review.",
        ],
        "candidates": [
            "Priority score: predicted booking probability × estimated value × a 1.2 delayed-response multiplier when response is at least 120 minutes.",
            "Candidates exclude already-booked leads and leads without a completed 24-hour observation window.",
        ],
    }
    sources = [
        _source(
            "source_summary",
            "Synthetic portfolio overview and model summary",
            QUERIES["summary"],
            [
                "fct_lead_outcomes",
                "mart_model_summary",
                "mart_scored_candidates",
                "mart_feature_drift",
            ],
            generated_at,
            definitions["summary"],
            ["is_matured = true"],
        ),
        _source(
            "source_monthly",
            "Monthly matured-lead funnel",
            QUERIES["monthly"],
            ["mart_monthly_funnel"],
            generated_at,
            definitions["monthly"],
        ),
        _source(
            "source_channels",
            "Acquisition channel performance",
            QUERIES["channels"],
            ["mart_channel_performance"],
            generated_at,
            definitions["channels"],
        ),
        _source(
            "source_campaigns",
            "Campaign performance",
            QUERIES["campaigns"],
            ["mart_campaign_performance"],
            generated_at,
            definitions["channels"],
            ["minimum 50 matured leads", "top 10 by booking rate"],
        ),
        _source(
            "source_calibration",
            "Chronological holdout calibration",
            QUERIES["calibration"],
            ["mart_model_calibration"],
            generated_at,
            definitions["calibration"],
        ),
        _source(
            "source_importance",
            "Holdout permutation importance",
            QUERIES["importance"],
            ["mart_feature_importance"],
            generated_at,
            definitions["importance"],
            ["top 8 features by mean importance"],
        ),
        _source(
            "source_drift",
            "Feature distribution monitoring",
            QUERIES["drift"],
            ["mart_feature_drift"],
            generated_at,
            definitions["drift"],
        ),
        _source(
            "source_candidates",
            "Highest-priority open synthetic leads",
            QUERIES["candidates"],
            ["mart_scored_candidates"],
            generated_at,
            definitions["candidates"],
            ["top 12 by priority score"],
        ),
    ]

    manifest: dict[str, Any] = {
        "version": 1,
        "surface": "dashboard",
        "title": "Nyxora Outcome Intelligence",
        "description": "Synthetic lead funnel, booking propensity, and model monitoring dashboard.",
        "generatedAt": generated_at,
        "sources": sources,
        "cards": [
            {
                "id": "card_leads",
                "dataset": "summary",
                "sourceId": "source_summary",
                "description": "Leads with the complete 14-day booking window.",
                "metrics": [{"label": "Matured leads", "field": "matured_leads", "format": "compact"}],
            },
            {
                "id": "card_booking",
                "dataset": "summary",
                "sourceId": "source_summary",
                "description": "Booked consultations divided by matured leads.",
                "metrics": [{"label": "Booking rate", "field": "booking_rate", "format": "percent"}],
            },
            {
                "id": "card_response",
                "dataset": "summary",
                "sourceId": "source_summary",
                "description": "Median first-response minutes; 1,440 means no response in 24 hours.",
                "metrics": [
                    {"label": "Median response", "field": "median_response_minutes", "format": "number"}
                ],
            },
            {
                "id": "card_auc",
                "dataset": "summary",
                "sourceId": "source_summary",
                "description": "ROC AUC on the newest chronological holdout period.",
                "metrics": [{"label": "Holdout ROC AUC", "field": "test_roc_auc", "format": "number"}],
            },
            {
                "id": "card_candidates",
                "dataset": "summary",
                "sourceId": "source_summary",
                "description": "Recent unbooked leads ready for human review.",
                "metrics": [{"label": "Open candidates", "field": "open_candidates", "format": "compact"}],
            },
        ],
        "charts": [
            {
                "id": "chart_monthly",
                "title": "Monthly booking rate",
                "type": "line",
                "intent": "trend",
                "question": "How does matured-lead booking rate move over time?",
                "rationale": "A chronological line makes direction and stability visible without mixing differently scaled funnel counts.",
                "dataset": "monthly",
                "sourceId": "source_monthly",
                "encodings": {
                    "x": {"field": "month", "type": "temporal", "label": "Month"},
                    "y": {"field": "booking_rate", "type": "quantitative", "format": "percent", "label": "Booking rate"},
                },
                "valueFormat": "percent",
                "layout": "full",
            },
            {
                "id": "chart_channels",
                "title": "Booking rate by acquisition channel",
                "type": "horizontalBar",
                "intent": "comparison",
                "question": "Which acquisition channels have the highest matured-lead booking rates?",
                "rationale": "Sorted horizontal bars support accurate category comparison while preserving readable channel labels.",
                "dataset": "channels",
                "sourceId": "source_channels",
                "encodings": {
                    "x": {"field": "channel", "type": "nominal", "label": "Channel"},
                    "y": {"field": "booking_rate", "type": "quantitative", "format": "percent", "label": "Booking rate"},
                },
                "valueFormat": "percent",
                "layout": "half",
            },
            {
                "id": "chart_calibration",
                "title": "Predicted versus observed booking rate",
                "type": "scatter",
                "intent": "relationship",
                "question": "Do holdout probabilities align with observed booking rates across prediction deciles?",
                "rationale": "A scatter plot directly compares average predicted and observed probability on the same rate scale.",
                "dataset": "calibration",
                "sourceId": "source_calibration",
                "encodings": {
                    "x": {"field": "predicted_probability", "type": "quantitative", "format": "percent", "label": "Predicted probability"},
                    "y": {"field": "observed_booking_rate", "type": "quantitative", "format": "percent", "label": "Observed booking rate"},
                    "size": {"field": "leads", "type": "quantitative", "label": "Leads"},
                    "label": {"field": "decile", "type": "ordinal", "label": "Decile"},
                },
                "valueFormat": "percent",
                "layout": "half",
            },
            {
                "id": "chart_importance",
                "title": "Predictive feature importance",
                "type": "horizontalBar",
                "intent": "comparison",
                "question": "Which inputs contribute most to holdout discrimination?",
                "rationale": "A sorted bar chart makes model-agnostic permutation importance easy to compare across inputs.",
                "dataset": "importance",
                "sourceId": "source_importance",
                "encodings": {
                    "x": {"field": "feature", "type": "nominal", "label": "Feature"},
                    "y": {"field": "importance_mean", "type": "quantitative", "format": "number", "label": "ROC AUC decrease"},
                },
                "valueFormat": "number",
                "layout": "half",
            },
            {
                "id": "chart_drift",
                "title": "Population Stability Index by feature",
                "type": "horizontalBar",
                "intent": "comparison",
                "question": "Which model inputs changed most between the reference and comparison periods?",
                "rationale": "Sorted bars expose the largest distribution shifts and make the 0.10 watch threshold interpretable.",
                "dataset": "drift",
                "sourceId": "source_drift",
                "encodings": {
                    "x": {"field": "feature", "type": "nominal", "label": "Feature"},
                    "y": {"field": "psi", "type": "quantitative", "format": "number", "label": "PSI"},
                },
                "referenceLines": [
                    {"axis": "y", "value": 0.10, "label": "Watch", "color": "orange", "lineStyle": "dashed"},
                    {"axis": "y", "value": 0.20, "label": "Review", "color": "red", "lineStyle": "dashed"},
                ],
                "valueFormat": "number",
                "layout": "half",
            },
        ],
        "tables": [
            {
                "id": "table_channels",
                "title": "Channel operating metrics",
                "dataset": "channels",
                "sourceId": "source_channels",
                "defaultSort": {"field": "booking_rate", "direction": "desc"},
                "density": "dense",
                "layout": "full",
                "columns": [
                    {"field": "channel", "label": "Channel", "type": "text"},
                    {"field": "leads", "label": "Matured leads", "format": "compact"},
                    {"field": "booking_rate", "label": "Booking rate", "format": "percent"},
                    {"field": "attendance_rate", "label": "Attendance rate", "format": "percent"},
                    {"field": "median_response_minutes", "label": "Median response", "format": "number"},
                    {"field": "pipeline_value", "label": "Pipeline value", "format": "currency"},
                ],
            },
            {
                "id": "table_candidates",
                "title": "Highest-priority synthetic leads",
                "subtitle": "For human review; no outreach is automated.",
                "dataset": "candidates",
                "sourceId": "source_candidates",
                "defaultSort": {"field": "priority_score", "direction": "desc"},
                "density": "dense",
                "layout": "full",
                "columns": [
                    {"field": "lead_id", "label": "Lead", "type": "text"},
                    {"field": "channel", "label": "Channel", "type": "text"},
                    {"field": "service_type", "label": "Service", "type": "text"},
                    {"field": "booking_probability", "label": "Booking probability", "format": "percent"},
                    {"field": "priority_score", "label": "Priority score", "format": "currency"},
                    {"field": "recommended_action", "label": "Action", "type": "text"},
                    {"field": "response_minutes", "label": "Response min", "format": "number"},
                ],
            },
        ],
        "blocks": [
            {"id": "block_metrics", "type": "metric-strip", "cardIds": ["card_leads", "card_booking", "card_response", "card_auc", "card_candidates"]},
            {"id": "block_monthly", "type": "chart", "chartId": "chart_monthly", "layout": "full"},
            {"id": "block_channels_chart", "type": "chart", "chartId": "chart_channels", "layout": "half"},
            {"id": "block_calibration", "type": "chart", "chartId": "chart_calibration", "layout": "half"},
            {"id": "block_channel_table", "type": "table", "tableId": "table_channels", "layout": "full"},
            {"id": "block_importance", "type": "chart", "chartId": "chart_importance", "layout": "half"},
            {"id": "block_drift", "type": "chart", "chartId": "chart_drift", "layout": "half"},
            {"id": "block_candidates", "type": "table", "tableId": "table_candidates", "layout": "full"},
            {
                "id": "block_caveats",
                "type": "markdown",
                "body": "## Scope and interpretation\n\nAll records are synthetic and reproducible. Model scores are decision-support signals, not causal estimates or evidence of real clinic performance. The newest leads without a complete observation window are excluded, and no outreach action is automated.",
                "layout": "full",
            },
        ],
    }
    artifact = {
        "surface": "dashboard",
        "manifest": manifest,
        "snapshot": {
            "version": 1,
            "generatedAt": generated_at,
            "status": "ready",
            "datasets": datasets,
            "accessIssues": [],
        },
        "sources": sources,
        "package_info": {
            "name": "nyxora-outcome-intelligence",
            "snapshot_as_of": as_of_date,
            "synthetic": True,
        },
    }
    output = paths.artifacts_dir / "artifact.json"
    output.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return output

