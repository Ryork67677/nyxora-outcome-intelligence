# Architecture

## Decision

Nyxora Outcome Intelligence is a local-first modular monolith. Python owns generation, validation,
modeling, monitoring, and serving; DuckDB owns durable analytical transformations; SQL files remain
independently reviewable; FastAPI exposes read-only metrics and synchronous scoring.

## Prediction contract

Every feature is defined at a fixed observation point 24 hours after lead creation. The label is a
`consultation_booked` event occurring within 14 days of creation. Training excludes leads without
the complete label window. This prevents the most common temporal leakage: training on incomplete
recent outcomes or on activity recorded after the prediction should have occurred.

## Components

1. `synthetic.py` produces deterministic lead and event CSVs from a fixed seed.
2. `001_foundation.sql` types raw records, builds event-derived outcomes, and creates the matured
   model training set.
3. `002_marts.sql` builds reconciled monthly, channel, campaign, and recent-candidate marts.
4. `warehouse.py` executes transformations and enforces blocking relational/data contracts.
5. `modeling.py` performs chronological candidate selection and holdout evaluation.
6. `scoring.py` ranks recent candidates and computes bounded counterfactual scenario deltas.
7. `monitoring.py` produces PSI drift signals and performance slices.
8. `dashboard.py` writes a bounded, provenance-rich dashboard artifact.
9. `api.py` serves the packaged dashboard, metadata, aggregate metrics, and validated scoring.

## Deliberate trade-offs

- **DuckDB over a hosted warehouse:** makes the complete workflow free and reproducible while
  preserving real SQL modeling. It does not demonstrate distributed query operations.
- **CSV source over Parquet:** keeps generated evidence human-readable. A larger system should use
  typed columnar storage and partitioning.
- **Custom model registry artifact over MLflow:** keeps the first release understandable and small.
  The joblib bundle is paired with machine-readable metrics and a model card.
- **Batch retraining over automatic retraining:** a drift flag requires human review. Automatic
  retraining could silently reinforce bad or biased outcomes.
- **No LLM:** the problem is structured probability estimation. A generative model would add cost,
  nondeterminism, and evaluation surface without improving the core decision.

## Production path

A real pilot would replace synthetic CSVs with consented, governed event ingestion; add a feature
store or point-in-time feature query; authenticate every endpoint; encrypt storage; define data
retention; add lineage and alert ownership; run fairness and privacy reviews; shadow-score before
use; and record human decisions and downstream outcomes for prospective monitoring.

