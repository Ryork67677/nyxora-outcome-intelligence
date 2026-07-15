from __future__ import annotations

import json

from nyxora_outcome_intelligence.config import ProjectPaths


def test_dashboard_artifact_is_bounded_and_source_backed(built_project: ProjectPaths) -> None:
    artifact = json.loads(
        (built_project.artifacts_dir / "artifact.json").read_text(encoding="utf-8")
    )
    assert artifact["surface"] == "dashboard"
    assert artifact["snapshot"]["status"] == "ready"
    assert artifact["manifest"]["blocks"][0]["type"] == "metric-strip"
    assert len(artifact["snapshot"]["datasets"]["candidates"]) <= 12
    assert all(source["query"]["sql"] for source in artifact["sources"])
    assert all(card["sourceId"] for card in artifact["manifest"]["cards"])
    assert all(chart["sourceId"] for chart in artifact["manifest"]["charts"])


def test_monitoring_report_has_explicit_periods(built_project: ProjectPaths) -> None:
    report = json.loads(
        (built_project.artifacts_dir / "monitoring_report.json").read_text(encoding="utf-8")
    )
    assert report["reference_period"]["rows"] > report["comparison_period"]["rows"]
    assert report["maximum_psi"] >= 0
    assert report["drift_thresholds"] == {"watch": 0.1, "review": 0.2}
    assert "causal" in report["caveat"]

