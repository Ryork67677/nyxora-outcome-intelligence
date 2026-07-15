from __future__ import annotations

import json
from datetime import UTC, datetime

import duckdb
import numpy as np
import pandas as pd

from .config import ProjectPaths
from .modeling import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from .scoring import load_bundle
from .warehouse import read_table


def _psi(expected: pd.Series, actual: pd.Series, *, bins: int = 10) -> float:
    expected_values = pd.to_numeric(expected, errors="coerce").dropna().to_numpy()
    actual_values = pd.to_numeric(actual, errors="coerce").dropna().to_numpy()
    if not len(expected_values) or not len(actual_values):
        return 0.0
    edges = np.unique(np.quantile(expected_values, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    expected_counts, _ = np.histogram(expected_values, bins=edges)
    actual_counts, _ = np.histogram(actual_values, bins=edges)
    expected_rates = np.clip(expected_counts / expected_counts.sum(), 1e-6, None)
    actual_rates = np.clip(actual_counts / actual_counts.sum(), 1e-6, None)
    return float(np.sum((actual_rates - expected_rates) * np.log(actual_rates / expected_rates)))


def _categorical_psi(expected: pd.Series, actual: pd.Series) -> float:
    categories = sorted(set(expected.astype(str)) | set(actual.astype(str)))
    expected_rates = expected.astype(str).value_counts(normalize=True).reindex(categories, fill_value=0)
    actual_rates = actual.astype(str).value_counts(normalize=True).reindex(categories, fill_value=0)
    expected_rates = expected_rates.clip(lower=1e-6)
    actual_rates = actual_rates.clip(lower=1e-6)
    return float(((actual_rates - expected_rates) * np.log(actual_rates / expected_rates)).sum())


def build_monitoring_report(paths: ProjectPaths) -> dict[str, object]:
    training = read_table(paths, "model_training_set").sort_values(["created_at", "lead_id"])
    split = int(len(training) * 0.70)
    reference = training.iloc[:split]
    comparison = training.iloc[split:]
    bundle = load_bundle(paths)
    comparison_probabilities = bundle.predict_probability(comparison)

    drift_rows: list[dict[str, object]] = []
    for feature in NUMERIC_FEATURES:
        value = _psi(reference[feature], comparison[feature])
        drift_rows.append(
            {
                "feature": feature,
                "feature_type": "numeric",
                "psi": round(value, 6),
                "status": "review" if value >= 0.20 else "watch" if value >= 0.10 else "stable",
            }
        )
    for feature in CATEGORICAL_FEATURES:
        value = _categorical_psi(reference[feature], comparison[feature])
        drift_rows.append(
            {
                "feature": feature,
                "feature_type": "categorical",
                "psi": round(value, 6),
                "status": "review" if value >= 0.20 else "watch" if value >= 0.10 else "stable",
            }
        )
    drift = pd.DataFrame(drift_rows).sort_values("psi", ascending=False)

    performance = comparison[["channel", "target_booked"]].copy()
    performance["prediction"] = comparison_probabilities
    slices = (
        performance.groupby("channel")
        .agg(
            leads=("target_booked", "size"),
            observed_booking_rate=("target_booked", "mean"),
            average_prediction=("prediction", "mean"),
        )
        .reset_index()
    )
    slices["calibration_gap"] = slices["average_prediction"] - slices["observed_booking_rate"]
    numeric_columns = ["observed_booking_rate", "average_prediction", "calibration_gap"]
    slices[numeric_columns] = slices[numeric_columns].round(6)

    report: dict[str, object] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "reference_period": {
            "start": pd.Timestamp(reference["created_at"].min()).isoformat(),
            "end": pd.Timestamp(reference["created_at"].max()).isoformat(),
            "rows": len(reference),
        },
        "comparison_period": {
            "start": pd.Timestamp(comparison["created_at"].min()).isoformat(),
            "end": pd.Timestamp(comparison["created_at"].max()).isoformat(),
            "rows": len(comparison),
        },
        "drift_thresholds": {"watch": 0.10, "review": 0.20},
        "maximum_psi": round(float(drift["psi"].max()), 6),
        "features_requiring_review": int((drift["status"] == "review").sum()),
        "drift": drift.to_dict(orient="records"),
        "performance_by_channel": slices.to_dict(orient="records"),
        "caveat": "PSI indicates distribution movement, not model failure or causal change.",
    }
    (paths.artifacts_dir / "monitoring_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    connection = duckdb.connect(str(paths.warehouse_path))
    try:
        connection.register("drift_frame", drift)
        connection.execute("CREATE OR REPLACE TABLE mart_feature_drift AS SELECT * FROM drift_frame")
        connection.unregister("drift_frame")
        connection.register("slice_frame", slices)
        connection.execute(
            "CREATE OR REPLACE TABLE mart_channel_model_performance AS SELECT * FROM slice_frame"
        )
        connection.unregister("slice_frame")
    finally:
        connection.close()
    return report

