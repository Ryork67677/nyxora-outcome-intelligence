from __future__ import annotations

from datetime import date

from nyxora_outcome_intelligence.synthetic import expected_booking_rate, generate_dataset


def test_generator_is_deterministic_and_event_grained() -> None:
    first = generate_dataset(lead_count=500, seed=42, as_of_date=date(2026, 7, 14))
    second = generate_dataset(lead_count=500, seed=42, as_of_date=date(2026, 7, 14))

    assert first.leads.equals(second.leads)
    assert first.events.equals(second.events)
    assert first.leads["lead_id"].is_unique
    assert first.events["event_id"].is_unique
    assert set(first.events["lead_id"]).issubset(set(first.leads["lead_id"]))
    assert len(first.events) > len(first.leads)


def test_generator_produces_nontrivial_booking_outcomes() -> None:
    dataset = generate_dataset(lead_count=1_000, seed=9, as_of_date=date(2026, 7, 14))
    rate = expected_booking_rate(dataset.leads, dataset.events)
    assert 0.10 < rate < 0.75
    assert dataset.leads["response_minutes"].between(0, 1_440).all()
    assert (
        dataset.leads.loc[~dataset.leads["consent_to_contact"], "follow_up_count"] == 0
    ).all()


def test_generator_rejects_invalid_sizes() -> None:
    try:
        generate_dataset(lead_count=99, seed=1, as_of_date=date(2026, 7, 14))
    except ValueError as error:
        assert "at least 100" in str(error)
    else:
        raise AssertionError("Expected a ValueError")

