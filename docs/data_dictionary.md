# Data Dictionary

All timestamps are UTC. All records are synthetic.

## `stg_leads`

One row per lead at the 24-hour observation point.

| Field | Type | Meaning |
|---|---|---|
| `lead_id` | text | Synthetic stable identifier |
| `created_at` | timestamp | Lead arrival time |
| `observation_complete_at` | timestamp | Prediction point, 24 hours after creation |
| `channel` | text | Acquisition source |
| `campaign` | text | Synthetic campaign identifier |
| `service_type` | text | Requested service category |
| `region` | text | Broad synthetic operating region |
| `consent_to_contact` | boolean | Whether follow-up is permitted in the scenario |
| `is_returning` | boolean | Whether the lead represents a returning client |
| `response_minutes` | double | Minutes to first contact; 1,440 means none in 24 hours |
| `follow_up_count` | integer | Consented follow-ups completed in the first 24 hours |
| `estimated_value` | double | Synthetic opportunity estimate, not revenue |

## `stg_events`

One row per lead lifecycle event. Allowed event types are `lead_created`, `contacted`, `qualified`,
`consultation_booked`, `consultation_attended`, and `customer_won`.

## `fct_lead_outcomes`

One row per lead. Event flags are derived from `stg_events`; `is_matured` identifies records whose
14-day label window is complete at the synthetic as-of timestamp.

## Analytical marts

- `model_training_set`: matured feature snapshot and binary target at lead grain
- `mart_monthly_funnel`: matured lead counts and rates by creation month
- `mart_channel_performance`: matured outcomes and synthetic value by acquisition channel
- `mart_campaign_performance`: campaign/channel metrics with at least 50 matured leads
- `mart_recent_candidates`: unbooked recent leads whose 24-hour observation window is complete
- `mart_scored_candidates`: recent candidates plus model probability and priority fields
- `mart_model_calibration`: chronological holdout prediction deciles
- `mart_feature_importance`: holdout permutation importance
- `mart_feature_drift`: PSI by feature
- `mart_channel_model_performance`: prediction and outcome summaries by channel

