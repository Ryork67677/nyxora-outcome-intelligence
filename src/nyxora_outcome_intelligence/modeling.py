from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import OUTCOME_WINDOW_DAYS, ProjectPaths
from .warehouse import read_table

NUMERIC_FEATURES = ["response_minutes", "follow_up_count", "estimated_value", "created_hour"]
CATEGORICAL_FEATURES = [
    "channel",
    "campaign",
    "service_type",
    "region",
    "created_weekday",
]
BOOLEAN_FEATURES = ["consent_to_contact", "is_returning"]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES + BOOLEAN_FEATURES
TARGET_COLUMN = "target_booked"


@dataclass
class ModelBundle:
    estimator: Pipeline
    feature_columns: list[str]
    model_name: str
    threshold: float
    trained_at: str
    training_rows: int
    as_of_date: str
    model_version: str = "0.1.0"

    def predict_probability(self, frame: pd.DataFrame) -> np.ndarray:
        return self.estimator.predict_proba(frame[self.feature_columns])[:, 1]


def _preprocessor(*, scale_numeric: bool) -> ColumnTransformer:
    numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scale", StandardScaler()))
    numeric = Pipeline(numeric_steps)
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
            ("boolean", "passthrough", BOOLEAN_FEATURES),
        ],
        verbose_feature_names_out=False,
    )


def candidate_models(seed: int) -> dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline(
            [
                ("preprocess", _preprocessor(scale_numeric=True)),
                (
                    "classifier",
                    LogisticRegression(max_iter=1_000, random_state=seed),
                ),
            ]
        ),
        "hist_gradient_boosting": Pipeline(
            [
                ("preprocess", _preprocessor(scale_numeric=False)),
                (
                    "classifier",
                    HistGradientBoostingClassifier(
                        max_iter=180,
                        learning_rate=0.06,
                        max_leaf_nodes=20,
                        l2_regularization=0.25,
                        random_state=seed,
                    ),
                ),
            ]
        ),
    }


def _metrics(y_true: pd.Series, probabilities: np.ndarray, threshold: float) -> dict[str, float]:
    predictions = (probabilities >= threshold).astype(int)
    return {
        "roc_auc": round(float(roc_auc_score(y_true, probabilities)), 6),
        "average_precision": round(float(average_precision_score(y_true, probabilities)), 6),
        "brier_score": round(float(brier_score_loss(y_true, probabilities)), 6),
        "accuracy": round(float(accuracy_score(y_true, predictions)), 6),
        "precision": round(float(precision_score(y_true, predictions, zero_division=0)), 6),
        "recall": round(float(recall_score(y_true, predictions, zero_division=0)), 6),
        "f1": round(float(f1_score(y_true, predictions, zero_division=0)), 6),
        "positive_rate": round(float(np.mean(y_true)), 6),
        "predicted_positive_rate": round(float(np.mean(predictions)), 6),
    }


def _best_threshold(y_true: pd.Series, probabilities: np.ndarray) -> float:
    thresholds = np.linspace(0.20, 0.75, 56)
    scores = [f1_score(y_true, probabilities >= threshold, zero_division=0) for threshold in thresholds]
    return round(float(thresholds[int(np.argmax(scores))]), 2)


def _calibration_rows(y_true: pd.Series, probabilities: np.ndarray) -> pd.DataFrame:
    frame = pd.DataFrame({"actual": np.asarray(y_true), "probability": probabilities})
    frame["bin"] = pd.qcut(frame["probability"], q=10, duplicates="drop")
    result = (
        frame.groupby("bin", observed=True)
        .agg(
            predicted_probability=("probability", "mean"),
            observed_booking_rate=("actual", "mean"),
            leads=("actual", "size"),
        )
        .reset_index(drop=True)
    )
    result.insert(0, "decile", np.arange(1, len(result) + 1))
    return result.round(6)


def train_models(paths: ProjectPaths, *, seed: int, as_of_date: str) -> dict[str, object]:
    training = read_table(paths, "model_training_set").sort_values(["created_at", "lead_id"])
    if len(training) < 500:
        raise ValueError("At least 500 matured leads are required for chronological model training")

    train_end = int(len(training) * 0.70)
    validation_end = int(len(training) * 0.85)
    train = training.iloc[:train_end]
    validation = training.iloc[train_end:validation_end]
    test = training.iloc[validation_end:]

    candidate_results: dict[str, dict[str, float]] = {}
    fitted: dict[str, Pipeline] = {}
    candidate_thresholds: dict[str, float] = {}
    for name, model in candidate_models(seed).items():
        model.fit(train[FEATURE_COLUMNS], train[TARGET_COLUMN])
        probabilities = model.predict_proba(validation[FEATURE_COLUMNS])[:, 1]
        threshold = _best_threshold(validation[TARGET_COLUMN], probabilities)
        candidate_thresholds[name] = threshold
        candidate_results[name] = _metrics(validation[TARGET_COLUMN], probabilities, threshold)
        fitted[name] = model

    selected_name = max(
        candidate_results,
        key=lambda name: (
            candidate_results[name]["roc_auc"],
            -candidate_results[name]["brier_score"],
        ),
    )
    selected_threshold = candidate_thresholds[selected_name]
    evaluation_model = fitted[selected_name]
    test_probabilities = evaluation_model.predict_proba(test[FEATURE_COLUMNS])[:, 1]
    test_metrics = _metrics(test[TARGET_COLUMN], test_probabilities, selected_threshold)

    naive_probability = float(train[TARGET_COLUMN].mean())
    naive_probabilities = np.full(len(test), naive_probability)
    naive_metrics = _metrics(test[TARGET_COLUMN], naive_probabilities, 0.5)

    importance = permutation_importance(
        evaluation_model,
        test[FEATURE_COLUMNS],
        test[TARGET_COLUMN],
        scoring="roc_auc",
        n_repeats=8,
        random_state=seed,
        n_jobs=1,
    )
    importance_frame = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "importance_mean": importance.importances_mean,
            "importance_std": importance.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)
    importance_frame[["importance_mean", "importance_std"]] = importance_frame[
        ["importance_mean", "importance_std"]
    ].round(6)

    calibration = _calibration_rows(test[TARGET_COLUMN], test_probabilities)
    deployment = candidate_models(seed)[selected_name]
    development = training.iloc[:validation_end]
    deployment.fit(development[FEATURE_COLUMNS], development[TARGET_COLUMN])
    trained_at = datetime.now(UTC).isoformat()
    bundle = ModelBundle(
        estimator=deployment,
        feature_columns=FEATURE_COLUMNS,
        model_name=selected_name,
        threshold=selected_threshold,
        trained_at=trained_at,
        training_rows=len(development),
        as_of_date=as_of_date,
    )
    joblib.dump(bundle, paths.model_path)

    metrics: dict[str, object] = {
        "generated_at": trained_at,
        "as_of_date": as_of_date,
        "prediction_point": "24 hours after lead creation",
        "outcome": f"consultation booked within {OUTCOME_WINDOW_DAYS} days",
        "split_strategy": "chronological 70% train / 15% validation / 15% test",
        "rows": {
            "total_matured": len(training),
            "train": len(train),
            "validation": len(validation),
            "test": len(test),
            "deployment_train": len(development),
        },
        "candidate_validation_metrics": candidate_results,
        "selected_model": selected_name,
        "decision_threshold": selected_threshold,
        "selected_test_metrics": test_metrics,
        "naive_test_metrics": naive_metrics,
        "test_date_range": {
            "start": pd.Timestamp(test["created_at"].min()).isoformat(),
            "end": pd.Timestamp(test["created_at"].max()).isoformat(),
        },
    }
    (paths.artifacts_dir / "model_metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )

    connection = duckdb.connect(str(paths.warehouse_path))
    try:
        connection.register("calibration_frame", calibration)
        connection.execute("CREATE OR REPLACE TABLE mart_model_calibration AS SELECT * FROM calibration_frame")
        connection.unregister("calibration_frame")
        connection.register("importance_frame", importance_frame)
        connection.execute(
            "CREATE OR REPLACE TABLE mart_feature_importance AS SELECT * FROM importance_frame"
        )
        connection.unregister("importance_frame")
        model_summary = pd.DataFrame(
            [
                {
                    "selected_model": selected_name,
                    "decision_threshold": selected_threshold,
                    "test_roc_auc": test_metrics["roc_auc"],
                    "test_average_precision": test_metrics["average_precision"],
                    "test_brier_score": test_metrics["brier_score"],
                    "naive_brier_score": naive_metrics["brier_score"],
                    "test_rows": len(test),
                    "trained_at": trained_at,
                }
            ]
        )
        connection.register("model_summary_frame", model_summary)
        connection.execute(
            "CREATE OR REPLACE TABLE mart_model_summary AS SELECT * FROM model_summary_frame"
        )
        connection.unregister("model_summary_frame")
    finally:
        connection.close()

    _write_model_card(paths, metrics, importance_frame)
    return metrics


def _write_model_card(
    paths: ProjectPaths, metrics: dict[str, object], importance: pd.DataFrame
) -> Path:
    test_metrics = metrics["selected_test_metrics"]
    naive_metrics = metrics["naive_test_metrics"]
    rows = metrics["rows"]
    top_features = "\n".join(
        f"- `{row.feature}`: permutation importance {row.importance_mean:.4f} ± {row.importance_std:.4f}"
        for row in importance.head(6).itertuples()
    )
    body = f"""# Model Card: Nyxora Booking Propensity v0.1.0

## Intended use

Rank synthetic leads for human review after the first 24 hours of follow-up activity. The score
estimates whether a consultation will be booked within 14 days. It does not automate outreach,
make eligibility decisions, or represent real clinic performance.

## Training data

- Source: reproducibly generated synthetic lead and event records
- As-of date: {metrics['as_of_date']}
- Matured observations: {rows['total_matured']:,}
- Development rows: {rows['deployment_train']:,}
- Holdout rows: {rows['test']:,}
- Split: chronological, with the newest 15% reserved as an untouched test set

## Selected model

- Algorithm: `{metrics['selected_model']}`
- Decision threshold: {metrics['decision_threshold']:.2f}, selected on the validation period for F1
- Holdout ROC AUC: {test_metrics['roc_auc']:.3f}
- Holdout average precision: {test_metrics['average_precision']:.3f}
- Holdout Brier score: {test_metrics['brier_score']:.3f}
- Naive Brier score: {naive_metrics['brier_score']:.3f}

## Most useful global features

{top_features}

Permutation importance measures predictive association on the synthetic holdout set. It does not
establish that changing a feature will cause conversion to change.

## Limitations and risks

- All records are synthetic. Performance cannot be generalized to real customers or clinics.
- The generator intentionally embeds learnable patterns; real acquisition channels may behave differently.
- Response time and follow-up count can reflect operational processes and are not causal estimates.
- The score must be reviewed alongside consent, availability, and human judgment.
- Protected attributes are not generated or used. A real deployment would still require fairness,
  privacy, retention, security, and legal review.

## Monitoring

The build produces population-stability checks for numeric and categorical inputs, calibration
deciles, performance slices by channel, and a data-quality report. Retraining is not automatic.
"""
    path = paths.artifacts_dir / "model_card.md"
    path.write_text(body, encoding="utf-8")
    return path
