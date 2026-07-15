# Validation Report

## Overall assessment: Ready to share with synthetic-data caveat

The default deterministic build completed successfully on July 14, 2026 (America/New_York). The
pipeline generated 10,000 synthetic leads and 36,173 lifecycle events, built the DuckDB warehouse,
passed all blocking data contracts, trained both candidate models, scored current candidates, and
produced the dashboard snapshot.

## Methodology review

- Prediction features are fixed at 24 hours after lead creation.
- Labels require a complete 14-day outcome window.
- Model selection uses an older training period and the following chronological validation period.
- Final performance is reported once on the newest 15% holdout period.
- The system compares two model candidates with a constant-prevalence probability baseline.
- Interpretation is explicitly associative; no causal claims are made.

## Calculation spot-checks

- Matured leads: **9,587** in the fact table, monthly mart, channel mart, and dashboard snapshot.
- Matured booked leads: **4,418** in both the fact table and channel mart.
- Open candidates: **217** in both the scoring mart and dashboard snapshot.
- Candidate exclusion: **0** already-booked leads and **0** incomplete observation windows.
- Blocking quality contracts: **9/9 passed**.
- Selected holdout ROC AUC: **0.686** versus **0.500** naive.
- Selected holdout average precision: **0.667** versus **0.481** naive.
- Selected holdout Brier score: **0.221** versus **0.250** naive; lower is better.

## Software verification

- Ruff: passed.
- Pytest: 13 passed.
- Measured core coverage: 96% (CLI shell orchestration excluded from the coverage denominator).
- Live FastAPI smoke: health, model loading, and scoring passed.
- Docker image build: passed on Python 3.12 slim.
- Docker runtime smoke: container healthy with model and warehouse available.
- Portable dashboard: schema validation and structural packaging passed.

## Remaining caveat

The portable dashboard verifier could not run its Chromium desktop/narrow-layout interaction pass
because a compatible Chromium headless-shell was unavailable. The generated file passed exact
payload equality, required runtime-root checks, semantic fallback checks, and structural validation.
No custom browser workaround was substituted for the prescribed verifier.

All records and performance results are synthetic. The project is ready to demonstrate engineering
methodology, but it is not evidence of real clinic conversion performance or production readiness.
