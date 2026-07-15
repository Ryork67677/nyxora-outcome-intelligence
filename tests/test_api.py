from __future__ import annotations

from fastapi.testclient import TestClient

from nyxora_outcome_intelligence.api import create_app
from nyxora_outcome_intelligence.config import ProjectPaths

PAYLOAD = {
    "channel": "referral",
    "campaign": "referral_circle",
    "service_type": "injectables",
    "region": "northeast",
    "consent_to_contact": True,
    "is_returning": False,
    "response_minutes": 42,
    "follow_up_count": 2,
    "estimated_value": 850,
    "created_weekday": "tuesday",
    "created_hour": 14,
}


def test_health_metrics_and_score_endpoints(built_project: ProjectPaths) -> None:
    with TestClient(create_app(built_project)) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        metrics = client.get("/v1/metrics")
        assert metrics.status_code == 200
        assert metrics.json()["summary"]["matured_leads"] > 1_000

        response = client.post("/v1/score", json=PAYLOAD)
        assert response.status_code == 200
        assert 0 <= response.json()["booking_probability"] <= 1

        metadata = client.get("/v1/model")
        assert metadata.status_code == 200
        assert metadata.json()["evaluation"]["selected_model"]


def test_api_rejects_invalid_consent_state(built_project: ProjectPaths) -> None:
    payload = dict(PAYLOAD, consent_to_contact=False, follow_up_count=2)
    with TestClient(create_app(built_project)) as client:
        response = client.post("/v1/score", json=payload)
    assert response.status_code == 422
    assert "follow_up_count" in response.json()["detail"]


def test_root_reports_unpacked_snapshot(built_project: ProjectPaths) -> None:
    with TestClient(create_app(built_project)) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "dashboard_not_packaged"

