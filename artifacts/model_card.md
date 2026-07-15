# Model Card: Nyxora Booking Propensity v0.1.0

## Intended use

Rank synthetic leads for human review after the first 24 hours of follow-up activity. The score
estimates whether a consultation will be booked within 14 days. It does not automate outreach,
make eligibility decisions, or represent real clinic performance.

## Training data

- Source: reproducibly generated synthetic lead and event records
- As-of date: 2026-07-14
- Matured observations: 9,587
- Development rows: 8,148
- Holdout rows: 1,439
- Split: chronological, with the newest 15% reserved as an untouched test set

## Selected model

- Algorithm: `logistic_regression`
- Decision threshold: 0.30, selected on the validation period for F1
- Holdout ROC AUC: 0.686
- Holdout average precision: 0.667
- Holdout Brier score: 0.221
- Naive Brier score: 0.250

## Most useful global features

- `response_minutes`: permutation importance 0.1031 ± 0.0104
- `is_returning`: permutation importance 0.0167 ± 0.0042
- `channel`: permutation importance 0.0111 ± 0.0077
- `campaign`: permutation importance 0.0073 ± 0.0048
- `created_weekday`: permutation importance 0.0043 ± 0.0031
- `service_type`: permutation importance 0.0023 ± 0.0018

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
