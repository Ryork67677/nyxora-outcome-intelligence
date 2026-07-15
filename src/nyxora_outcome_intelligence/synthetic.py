from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .config import OBSERVATION_HOURS, OUTCOME_WINDOW_DAYS

CHANNELS = np.array(
    ["organic_search", "paid_search", "instagram", "referral", "website_direct", "reactivation"]
)
CHANNEL_PROBABILITIES = np.array([0.22, 0.20, 0.17, 0.16, 0.15, 0.10])
SERVICES = np.array(["injectables", "facial", "laser", "body_contouring", "skincare"])
SERVICE_PROBABILITIES = np.array([0.25, 0.24, 0.19, 0.17, 0.15])
REGIONS = np.array(["northeast", "southeast", "midwest", "west"])
CAMPAIGNS_BY_CHANNEL = {
    "organic_search": ("consultation_guide", "local_search"),
    "paid_search": ("always_on_search", "summer_glow"),
    "instagram": ("summer_glow", "before_after_education"),
    "referral": ("referral_circle",),
    "website_direct": ("direct_visit", "consultation_guide"),
    "reactivation": ("winback_q2",),
}
SERVICE_VALUES = {
    "injectables": 720.0,
    "facial": 260.0,
    "laser": 980.0,
    "body_contouring": 1_850.0,
    "skincare": 190.0,
}


@dataclass(frozen=True)
class SyntheticDataset:
    leads: pd.DataFrame
    events: pd.DataFrame
    as_of_date: date
    seed: int


def _sigmoid(value: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-value))


def _iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def generate_dataset(
    *,
    lead_count: int,
    seed: int,
    as_of_date: date,
    lookback_days: int = 365,
) -> SyntheticDataset:
    if lead_count < 100:
        raise ValueError("lead_count must be at least 100")
    if lookback_days <= OUTCOME_WINDOW_DAYS:
        raise ValueError("lookback_days must exceed the outcome window")

    rng = np.random.default_rng(seed)
    as_of = datetime.combine(as_of_date, datetime.min.time(), tzinfo=UTC) + timedelta(
        hours=23, minutes=59, seconds=59
    )
    offsets = rng.integers(0, lookback_days * 24 * 60, size=lead_count)
    created_at = np.array([as_of - timedelta(minutes=int(value)) for value in offsets])
    order = np.argsort(created_at)
    created_at = created_at[order]

    channels = rng.choice(CHANNELS, size=lead_count, p=CHANNEL_PROBABILITIES)[order]
    services = rng.choice(SERVICES, size=lead_count, p=SERVICE_PROBABILITIES)[order]
    regions = rng.choice(REGIONS, size=lead_count, p=[0.27, 0.28, 0.22, 0.23])[order]
    campaigns = np.array(
        [rng.choice(CAMPAIGNS_BY_CHANNEL[str(channel)]) for channel in channels], dtype=object
    )
    is_returning = (
        rng.random(lead_count)
        < np.where(channels == "reactivation", 0.88, np.where(channels == "referral", 0.28, 0.12))
    )
    consent_to_contact = rng.random(lead_count) < 0.92

    created_hour = np.array([item.hour for item in created_at])
    created_weekday = np.array([item.strftime("%A").lower() for item in created_at])
    business_hours = (created_hour >= 8) & (created_hour <= 18)
    channel_speed = np.select(
        [channels == "referral", channels == "website_direct", channels == "paid_search"],
        [0.72, 0.88, 1.05],
        default=1.18,
    )
    raw_response = rng.lognormal(mean=3.35, sigma=1.25, size=lead_count)
    response_minutes = raw_response * channel_speed * np.where(business_hours, 0.72, 1.48)
    response_minutes = np.clip(response_minutes, 1, OBSERVATION_HOURS * 60)
    response_minutes = np.where(consent_to_contact, response_minutes, OBSERVATION_HOURS * 60)
    contacted_within_24h = consent_to_contact & (response_minutes < OBSERVATION_HOURS * 60)

    follow_up_lambda = np.where(contacted_within_24h, 1.55, 0.25) + np.where(
        response_minutes > 120, 0.35, 0
    )
    follow_up_count = np.minimum(rng.poisson(follow_up_lambda), 6)
    follow_up_count = np.where(consent_to_contact, follow_up_count, 0)

    estimated_value = np.array([SERVICE_VALUES[str(service)] for service in services])
    estimated_value *= rng.lognormal(mean=0.0, sigma=0.28, size=lead_count)
    estimated_value = np.round(np.clip(estimated_value, 90, 4_500), 2)

    logit = np.full(lead_count, -1.48)
    logit += np.select(
        [
            channels == "referral",
            channels == "reactivation",
            channels == "organic_search",
            channels == "website_direct",
            channels == "instagram",
        ],
        [0.95, 0.48, 0.34, 0.18, -0.08],
        default=-0.22,
    )
    logit += np.where(is_returning, 0.55, 0)
    logit += np.where(consent_to_contact, 0.72, -1.35)
    logit += np.select(
        [response_minutes <= 5, response_minutes <= 30, response_minutes <= 120, response_minutes > 720],
        [0.78, 0.46, 0.12, -1.08],
        default=-0.48,
    )
    logit += np.select(
        [follow_up_count == 1, follow_up_count == 2, follow_up_count == 3, follow_up_count >= 5],
        [0.12, 0.31, 0.43, -0.18],
        default=0,
    )
    logit += np.where(services == "injectables", 0.20, 0)
    logit += np.where(services == "body_contouring", -0.12, 0)
    logit += np.where(np.isin(created_weekday, ["saturday", "sunday"]), -0.17, 0)
    logit += np.where((channels == "referral") & (response_minutes <= 30), 0.38, 0)
    logit += rng.normal(0, 0.42, size=lead_count)
    booking_probability = _sigmoid(logit)
    will_book = rng.random(lead_count) < booking_probability

    booking_delay_hours = np.clip(
        rng.gamma(shape=1.8, scale=22.0, size=lead_count) + response_minutes / 60 * 0.18,
        1,
        OUTCOME_WINDOW_DAYS * 24 - 2,
    )
    attended = will_book & (rng.random(lead_count) < np.where(is_returning, 0.91, 0.84))
    won = attended & (rng.random(lead_count) < np.where(services == "body_contouring", 0.50, 0.64))
    qualified = will_book | (rng.random(lead_count) < np.where(consent_to_contact, 0.34, 0.04))

    lead_rows: list[dict[str, object]] = []
    event_rows: list[dict[str, object]] = []
    for index in range(lead_count):
        lead_id = f"lead_{index + 1:06d}"
        created = created_at[index]
        response = float(response_minutes[index])
        lead_rows.append(
            {
                "lead_id": lead_id,
                "created_at": _iso_utc(created),
                "observation_complete_at": _iso_utc(created + timedelta(hours=OBSERVATION_HOURS)),
                "channel": str(channels[index]),
                "campaign": str(campaigns[index]),
                "service_type": str(services[index]),
                "region": str(regions[index]),
                "consent_to_contact": bool(consent_to_contact[index]),
                "is_returning": bool(is_returning[index]),
                "response_minutes": round(response, 2),
                "follow_up_count": int(follow_up_count[index]),
                "estimated_value": float(estimated_value[index]),
            }
        )

        events: list[tuple[str, datetime, float | None]] = [("lead_created", created, None)]
        if contacted_within_24h[index]:
            events.append(("contacted", created + timedelta(minutes=response), response))
        if qualified[index]:
            qualify_delay = min(response + float(rng.uniform(10, 360)), 48 * 60)
            events.append(("qualified", created + timedelta(minutes=qualify_delay), None))
        if will_book[index]:
            booked_at = created + timedelta(hours=float(booking_delay_hours[index]))
            events.append(("consultation_booked", booked_at, None))
            if attended[index]:
                attended_at = booked_at + timedelta(days=float(rng.uniform(2, 12)))
                events.append(("consultation_attended", attended_at, None))
                if won[index]:
                    events.append(("customer_won", attended_at + timedelta(minutes=30), None))
        for sequence, (event_type, event_at, event_value) in enumerate(events, start=1):
            if event_at <= as_of:
                event_rows.append(
                    {
                        "event_id": f"evt_{index + 1:06d}_{sequence:02d}",
                        "lead_id": lead_id,
                        "event_type": event_type,
                        "event_at": _iso_utc(event_at),
                        "event_value": None if event_value is None else round(event_value, 2),
                    }
                )

    leads = pd.DataFrame(lead_rows)
    events = pd.DataFrame(event_rows).sort_values(["event_at", "event_id"]).reset_index(drop=True)
    return SyntheticDataset(leads=leads, events=events, as_of_date=as_of_date, seed=seed)


def write_dataset(dataset: SyntheticDataset, raw_dir: Path) -> tuple[Path, Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    leads_path = raw_dir / "leads.csv"
    events_path = raw_dir / "events.csv"
    dataset.leads.to_csv(leads_path, index=False)
    dataset.events.to_csv(events_path, index=False)
    return leads_path, events_path


def expected_booking_rate(leads: pd.DataFrame, events: pd.DataFrame) -> float:
    booked_ids = set(events.loc[events["event_type"] == "consultation_booked", "lead_id"])
    return len(booked_ids) / len(leads) if len(leads) else math.nan
