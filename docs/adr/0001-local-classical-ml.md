# ADR-0001: Use a local classical-ML pipeline

## Status

Accepted — July 14, 2026

## Context

The portfolio already demonstrates grounded LLM integration. The missing proof points are SQL,
structured data modeling, temporal evaluation, probability quality, monitoring, and operational
software around a model.

## Decision

Use DuckDB, scikit-learn, and FastAPI. Compare an interpretable logistic baseline with nonlinear
gradient boosting. Select on a chronological validation period and report one final chronological
holdout evaluation. Do not use an LLM in the prediction path.

## Consequences

The repository is inexpensive, deterministic, and explainable. It demonstrates the full applied-ML
lifecycle without claiming distributed scale. A future version can add hosted infrastructure only
after the local contracts are stable.

