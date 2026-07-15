from __future__ import annotations

from typing import Any

import duckdb
import joblib
import pandas as pd

from .config import ProjectPaths
from .modeling import FEATURE_COLUMNS, ModelBundle
from .warehouse import read_table


def load_bundle(paths: ProjectPaths) -> ModelBundle:
    if not paths.model_path.exists():
        raise FileNotFoundError("Model artifact is missing; run `nyxora-intel build` first")
    bundle = joblib.load(paths.model_path)
    if not isinstance(bundle, ModelBundle):
        raise TypeError("Unexpected model artifact type")
    return bundle


def _driver_explanations(bundle: ModelBundle, frame: pd.DataFrame) -> list[list[dict[str, Any]]]:
    base = bundle.predict_probability(frame)
    all_drivers: list[list[dict[str, Any]]] = [[] for _ in range(len(frame))]
    scenarios = [
        ("response_minutes", 5.0, "Responding within five minutes"),
        ("follow_up_count", 3, "Completing three consented follow-ups"),
        ("consent_to_contact", True, "Having permission to follow up"),
    ]
    for feature, replacement, label in scenarios:
        altered = frame.copy()
        altered[feature] = replacement
        changed = bundle.predict_probability(altered)
        for index, delta in enumerate(changed - base):
            if abs(float(delta)) >= 0.005:
                all_drivers[index].append(
                    {
                        "factor": feature,
                        "scenario": label,
                        "probability_delta": round(float(delta), 4),
                    }
                )
    for items in all_drivers:
        items.sort(key=lambda item: abs(item["probability_delta"]), reverse=True)
        del items[3:]
    return all_drivers


def score_frame(bundle: ModelBundle, frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in FEATURE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing scoring features: {', '.join(missing)}")
    probabilities = bundle.predict_probability(frame)
    drivers = _driver_explanations(bundle, frame)
    scored = frame.copy()
    scored["booking_probability"] = probabilities.round(6)
    scored["risk_band"] = pd.cut(
        probabilities,
        bins=[-0.001, 0.35, 0.65, 1.001],
        labels=["low", "medium", "high"],
    ).astype(str)
    scored["priority_score"] = (
        probabilities
        * scored["estimated_value"].astype(float)
        * (1 + (scored["response_minutes"].astype(float) >= 120) * 0.20)
    ).round(2)
    scored["recommended_action"] = [
        "human_follow_up"
        if bool(consent) and probability >= 0.35
        else "consent_review"
        if not bool(consent)
        else "nurture"
        for consent, probability in zip(scored["consent_to_contact"], probabilities, strict=True)
    ]
    scored["drivers"] = drivers
    return scored


def score_one(bundle: ModelBundle, payload: dict[str, Any]) -> dict[str, Any]:
    scored = score_frame(bundle, pd.DataFrame([payload])).iloc[0]
    return {
        "booking_probability": float(scored["booking_probability"]),
        "risk_band": str(scored["risk_band"]),
        "priority_score": float(scored["priority_score"]),
        "recommended_action": str(scored["recommended_action"]),
        "drivers": scored["drivers"],
        "model": {
            "name": bundle.model_name,
            "version": bundle.model_version,
            "threshold": bundle.threshold,
            "trained_at": bundle.trained_at,
        },
        "caveat": "Synthetic portfolio model; the score is decision support, not causal evidence.",
    }


def score_recent_candidates(paths: ProjectPaths) -> pd.DataFrame:
    bundle = load_bundle(paths)
    candidates = read_table(paths, "mart_recent_candidates")
    if candidates.empty:
        scored = candidates.assign(
            booking_probability=pd.Series(dtype=float),
            risk_band=pd.Series(dtype=str),
            priority_score=pd.Series(dtype=float),
            recommended_action=pd.Series(dtype=str),
            drivers=pd.Series(dtype=object),
        )
    else:
        scored = score_frame(bundle, candidates)
    warehouse_copy = scored.copy()
    warehouse_copy["drivers"] = warehouse_copy["drivers"].map(str)
    connection = duckdb.connect(str(paths.warehouse_path))
    try:
        connection.register("scored_candidates", warehouse_copy)
        connection.execute(
            "CREATE OR REPLACE TABLE mart_scored_candidates AS SELECT * FROM scored_candidates"
        )
        connection.unregister("scored_candidates")
    finally:
        connection.close()
    return scored


def bundle_metadata(bundle: ModelBundle) -> dict[str, Any]:
    return {
        "feature_columns": bundle.feature_columns,
        "model_name": bundle.model_name,
        "threshold": bundle.threshold,
        "trained_at": bundle.trained_at,
        "training_rows": bundle.training_rows,
        "as_of_date": bundle.as_of_date,
        "model_version": bundle.model_version,
    }
