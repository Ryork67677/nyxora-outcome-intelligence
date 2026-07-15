# Metric Definitions

## Population anchors

- **As-of timestamp:** end of the configured UTC as-of date.
- **Observation-complete lead:** at least 24 hours have elapsed since creation.
- **Matured lead:** at least 14 days have elapsed since creation.
- **Open candidate:** created during the latest 14 days, observation complete, and no booking event
  has occurred by the as-of timestamp.

## Funnel metrics

- **Booking rate:** matured leads with `consultation_booked` ÷ matured leads.
- **Attendance rate:** matured leads with `consultation_attended` ÷ matured leads. This is not the
  appointment show rate; the denominator intentionally stays at lead grain for funnel consistency.
- **Win rate:** matured leads with `customer_won` ÷ matured leads.
- **Median response minutes:** median first-response time at lead grain. No contact inside the
  observation window is represented as 1,440 minutes and remains in the metric.
- **Pipeline value:** sum of synthetic estimated lead values. It is neither booked nor recognized revenue.

## Model metrics

- **ROC AUC:** ranking discrimination across all classification thresholds.
- **Average precision:** precision-recall summary appropriate to the positive booking outcome.
- **Brier score:** mean squared error of predicted probabilities; lower is better.
- **Calibration gap:** average predicted probability minus observed booking rate.
- **Permutation importance:** decrease in holdout ROC AUC after shuffling one feature.
- **PSI:** Population Stability Index comparing feature distributions. Below 0.10 is stable,
  0.10–0.20 is watch, and 0.20 or above requires review.

## Operational ranking

`priority_score = booking_probability × estimated_value × delay_multiplier`

The delay multiplier is 1.2 when first response is at least 120 minutes, otherwise 1.0. This is an
explicit queue-ordering policy, not an expected-revenue forecast.

