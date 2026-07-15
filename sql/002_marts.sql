CREATE OR REPLACE TABLE mart_monthly_funnel AS
SELECT
    STRFTIME(DATE_TRUNC('month', created_at), '%Y-%m') AS month,
    COUNT(*)::INTEGER AS leads,
    SUM(consent_to_contact::INTEGER)::INTEGER AS consented,
    SUM(contacted)::INTEGER AS contacted,
    SUM(qualified)::INTEGER AS qualified,
    SUM(booked)::INTEGER AS booked,
    SUM(attended)::INTEGER AS attended,
    SUM(won)::INTEGER AS won,
    ROUND(AVG(booked), 6) AS booking_rate,
    ROUND(AVG(attended), 6) AS attendance_rate,
    ROUND(AVG(won), 6) AS win_rate,
    ROUND(AVG(response_minutes), 2) AS average_response_minutes,
    ROUND(MEDIAN(response_minutes), 2) AS median_response_minutes
FROM fct_lead_outcomes
WHERE is_matured
GROUP BY 1
ORDER BY 1;

CREATE OR REPLACE TABLE mart_channel_performance AS
SELECT
    channel,
    COUNT(*)::INTEGER AS leads,
    SUM(booked)::INTEGER AS booked,
    ROUND(AVG(booked), 6) AS booking_rate,
    ROUND(AVG(attended), 6) AS attendance_rate,
    ROUND(AVG(won), 6) AS win_rate,
    ROUND(MEDIAN(response_minutes), 2) AS median_response_minutes,
    ROUND(AVG(follow_up_count), 2) AS average_follow_ups,
    ROUND(SUM(estimated_value), 2) AS pipeline_value
FROM fct_lead_outcomes
WHERE is_matured
GROUP BY channel
ORDER BY booking_rate DESC, leads DESC;

CREATE OR REPLACE TABLE mart_campaign_performance AS
SELECT
    campaign,
    channel,
    COUNT(*)::INTEGER AS leads,
    SUM(booked)::INTEGER AS booked,
    ROUND(AVG(booked), 6) AS booking_rate,
    ROUND(MEDIAN(response_minutes), 2) AS median_response_minutes,
    ROUND(SUM(estimated_value), 2) AS pipeline_value
FROM fct_lead_outcomes
WHERE is_matured
GROUP BY campaign, channel
HAVING COUNT(*) >= 50
ORDER BY booking_rate DESC, leads DESC;

CREATE OR REPLACE TABLE mart_recent_candidates AS
SELECT
    f.lead_id,
    f.created_at,
    f.channel,
    f.campaign,
    f.service_type,
    f.region,
    f.consent_to_contact,
    f.is_returning,
    f.response_minutes,
    f.follow_up_count,
    f.estimated_value,
    f.created_weekday,
    f.created_hour
FROM fct_lead_outcomes f
CROSS JOIN pipeline_metadata m
WHERE f.created_at > m.as_of_timestamp - INTERVAL 14 DAYS
  AND f.observation_complete_at <= m.as_of_timestamp
  AND f.booked = 0
ORDER BY f.created_at DESC;

