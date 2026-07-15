from __future__ import annotations

import json

from nyxora_outcome_intelligence.config import ProjectPaths
from nyxora_outcome_intelligence.scoring import load_bundle, score_one


def sample_payload() -> dict[str, object]:
    return {
        "channel": "referral",
        "campaign": "referral_circle",
        "service_type": "injectables",
        "region": "northeast",
        "consent_to_contact": True,
        "is_returning": False,
        "response_minutes": 42.0,
        "follow_up_count": 2,
        "estimated_value": 850.0,
        "created_weekday": "tuesday",
        "created_hour": 14,
    }


def test_model_beats_probability_baseline(built_project: ProjectPaths) -> None:
    metrics = json.loads(
        (built_project.artifacts_dir / "model_metrics.json").read_text(encoding="utf-8")
    )
    selected = metrics["selected_test_metrics"]
    naive = metrics["naive_test_metrics"]
    assert selected["roc_auc"] > 0.62
    assert selected["average_precision"] > naive["average_precision"]
    assert selected["brier_score"] < naive["brier_score"]
    assert metrics["split_strategy"].startswith("chronological")


def test_scoring_is_bounded_and_explained(built_project: ProjectPaths) -> None:
    result = score_one(load_bundle(built_project), sample_payload())
    assert 0 <= result["booking_probability"] <= 1
    assert result["risk_band"] in {"low", "medium", "high"}
    assert result["priority_score"] >= 0
    assert result["recommended_action"] in {"human_follow_up", "nurture", "consent_review"}
    assert len(result["drivers"]) <= 3
    assert "causal" in result["caveat"]


def test_consent_boundary_changes_action(built_project: ProjectPaths) -> None:
    payload = sample_payload()
    payload["consent_to_contact"] = False
    payload["follow_up_count"] = 0
    result = score_one(load_bundle(built_project), payload)
    assert result["recommended_action"] == "consent_review"

