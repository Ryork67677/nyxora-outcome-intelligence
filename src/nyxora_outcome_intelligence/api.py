from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Literal

import duckdb
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from . import __version__
from .config import ProjectPaths, default_root
from .scoring import bundle_metadata, load_bundle, score_one


class ScoreRequest(BaseModel):
    channel: Literal[
        "organic_search", "paid_search", "instagram", "referral", "website_direct", "reactivation"
    ]
    campaign: str = Field(min_length=2, max_length=80)
    service_type: Literal["injectables", "facial", "laser", "body_contouring", "skincare"]
    region: Literal["northeast", "southeast", "midwest", "west"]
    consent_to_contact: bool
    is_returning: bool
    response_minutes: float = Field(ge=0, le=1_440)
    follow_up_count: int = Field(ge=0, le=6)
    estimated_value: float = Field(ge=0, le=25_000)
    created_weekday: Literal[
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
    ]
    created_hour: int = Field(ge=0, le=23)


def create_app(paths: ProjectPaths | None = None) -> FastAPI:
    configured_paths = paths or ProjectPaths(default_root())

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.paths = configured_paths
        app.state.bundle = load_bundle(configured_paths) if configured_paths.model_path.exists() else None
        yield

    app = FastAPI(
        title="Nyxora Outcome Intelligence API",
        version=__version__,
        description=(
            "Scores synthetic lead snapshots after a 24-hour observation window. "
            "This educational API does not automate outreach or use real customer data."
        ),
        lifespan=lifespan,
    )

    @app.get("/", include_in_schema=False)
    def dashboard():
        dashboard_path = configured_paths.artifacts_dir / "dashboard.html"
        if dashboard_path.exists():
            return FileResponse(dashboard_path, media_type="text/html")
        return JSONResponse(
            {
                "name": "Nyxora Outcome Intelligence",
                "status": "dashboard_not_packaged",
                "docs": "/docs",
                "message": "Run `nyxora-intel build` to generate the analytical artifacts.",
            }
        )

    @app.get("/health")
    def health():
        return {
            "status": "ok" if configured_paths.model_path.exists() else "not_ready",
            "version": __version__,
            "model_available": configured_paths.model_path.exists(),
            "warehouse_available": configured_paths.warehouse_path.exists(),
            "checked_at": datetime.now(UTC).isoformat(),
        }

    @app.get("/v1/model")
    def model_metadata():
        if app.state.bundle is None:
            raise HTTPException(status_code=503, detail="Model is not built")
        metrics_path = configured_paths.artifacts_dir / "model_metrics.json"
        return {
            "model": bundle_metadata(app.state.bundle),
            "evaluation": json.loads(metrics_path.read_text(encoding="utf-8"))
            if metrics_path.exists()
            else None,
        }

    @app.get("/v1/metrics")
    def operating_metrics():
        if not configured_paths.warehouse_path.exists():
            raise HTTPException(status_code=503, detail="Warehouse is not built")
        connection = duckdb.connect(str(configured_paths.warehouse_path), read_only=True)
        try:
            channels = connection.execute(
                "SELECT * FROM mart_channel_performance ORDER BY booking_rate DESC"
            ).fetchdf()
            summary = connection.execute(
                """
                SELECT COUNT(*) AS matured_leads, SUM(booked) AS booked,
                       ROUND(AVG(booked), 6) AS booking_rate
                FROM fct_lead_outcomes WHERE is_matured
                """
            ).fetchdf().iloc[0]
        finally:
            connection.close()
        return {
            "as_of": json.loads(
                (configured_paths.artifacts_dir / "model_metrics.json").read_text(encoding="utf-8")
            )["as_of_date"],
            "synthetic": True,
            "summary": {
                "matured_leads": int(summary["matured_leads"]),
                "booked": int(summary["booked"]),
                "booking_rate": float(summary["booking_rate"]),
            },
            "channels": channels.to_dict(orient="records"),
        }

    @app.post("/v1/score")
    def score(request: ScoreRequest):
        if app.state.bundle is None:
            raise HTTPException(status_code=503, detail="Model is not built")
        if not request.consent_to_contact and request.follow_up_count > 0:
            raise HTTPException(
                status_code=422,
                detail="follow_up_count must be zero when consent_to_contact is false",
            )
        return score_one(app.state.bundle, request.model_dump())

    return app


app = create_app()

