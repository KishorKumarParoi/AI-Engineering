# ADR 0003: Shared Feast Feature Store and Population Stability Index (PSI) Drift Monitoring

## Status: ACCEPTED (Production Standard)

## Context & Problem Statement
Machine learning models (such as ETA prediction and fraud scoring) suffered from training-serving skew: spatial and temporal features calculated during batch training differed slightly from real-time features extracted in production microservices. Furthermore, sudden shifts in city traffic (e.g. monsoon storms) degraded model accuracy silently.

## Decision
1. **Feast Shared Feature Store**: Standardize feature extraction across batch and streaming through Feast feature views (`restaurant_hourly_stats`, `customer_risk_profile`).
   - Online Store: Redis (< 10ms P99 retrieval).
   - Offline Store: Delta Lake Gold Parquet.
2. **Automated Drift Detection**: Real-time evaluation of Population Stability Index (PSI) and Kolmogorov-Smirnov (KS-test) on delivery features.
   - Triggers automated alerting and model retraining when PSI >= 0.25.

## Consequences
- **Positive**: Zero training-serving skew; automated detection of real-world environmental drift.
- **Negative**: Redis cluster memory sizing must accommodate high-cardinality entities.
