CREATE OR REPLACE TABLE pipeline_metadata AS
SELECT
    DATE '{as_of_date}' AS as_of_date,
    TIMESTAMPTZ '{as_of_date} 23:59:59+00' AS as_of_timestamp,
    24::INTEGER AS observation_hours,
    14::INTEGER AS outcome_window_days;

CREATE OR REPLACE TABLE stg_leads AS
SELECT
    lead_id::VARCHAR AS lead_id,
    created_at::TIMESTAMPTZ AS created_at,
    observation_complete_at::TIMESTAMPTZ AS observation_complete_at,
    channel::VARCHAR AS channel,
    campaign::VARCHAR AS campaign,
    service_type::VARCHAR AS service_type,
    region::VARCHAR AS region,
    consent_to_contact::BOOLEAN AS consent_to_contact,
    is_returning::BOOLEAN AS is_returning,
    response_minutes::DOUBLE AS response_minutes,
    follow_up_count::INTEGER AS follow_up_count,
    estimated_value::DOUBLE AS estimated_value
FROM read_csv_auto('{leads_path}', header = true, sample_size = -1);

CREATE OR REPLACE TABLE stg_events AS
SELECT
    event_id::VARCHAR AS event_id,
    lead_id::VARCHAR AS lead_id,
    event_type::VARCHAR AS event_type,
    event_at::TIMESTAMPTZ AS event_at,
    event_value::DOUBLE AS event_value
FROM read_csv_auto('{events_path}', header = true, sample_size = -1);

CREATE OR REPLACE TABLE fct_lead_outcomes AS
WITH event_flags AS (
    SELECT
        lead_id,
        MAX((event_type = 'contacted')::INTEGER) AS contacted,
        MAX((event_type = 'qualified')::INTEGER) AS qualified,
        MAX((event_type = 'consultation_booked')::INTEGER) AS booked,
        MAX((event_type = 'consultation_attended')::INTEGER) AS attended,
        MAX((event_type = 'customer_won')::INTEGER) AS won,
        MIN(event_at) FILTER (WHERE event_type = 'consultation_booked') AS booked_at
    FROM stg_events
    GROUP BY lead_id
)
SELECT
    l.*,
    LOWER(STRFTIME(l.created_at, '%A')) AS created_weekday,
    EXTRACT('hour' FROM l.created_at)::INTEGER AS created_hour,
    COALESCE(e.contacted, 0) AS contacted,
    COALESCE(e.qualified, 0) AS qualified,
    COALESCE(e.booked, 0) AS booked,
    COALESCE(e.attended, 0) AS attended,
    COALESCE(e.won, 0) AS won,
    e.booked_at,
    l.created_at <= m.as_of_timestamp - INTERVAL 14 DAYS AS is_matured
FROM stg_leads l
LEFT JOIN event_flags e USING (lead_id)
CROSS JOIN pipeline_metadata m;

CREATE OR REPLACE TABLE model_training_set AS
SELECT
    lead_id,
    created_at,
    channel,
    campaign,
    service_type,
    region,
    consent_to_contact,
    is_returning,
    response_minutes,
    follow_up_count,
    estimated_value,
    created_weekday,
    created_hour,
    booked AS target_booked
FROM fct_lead_outcomes
WHERE is_matured
ORDER BY created_at, lead_id;

