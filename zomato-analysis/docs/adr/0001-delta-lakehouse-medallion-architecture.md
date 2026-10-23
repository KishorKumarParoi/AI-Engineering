# ADR 0001: Medallion Lakehouse Architecture (Delta Lake & Apache Iceberg)

## Status: ACCEPTED (Production Standard)

## Context & Problem Statement
Legacy relational databases and plain S3 CSV/JSON data lakes suffered from lack of ACID transactions, slow analytical scans, high query costs, and inability to track historical state changes (e.g. restaurant menu changes or rider relocations) over time.

## Decision
We implement a **3-Tier Medallion Data Architecture using Delta Lake and Apache Iceberg**:
1. **Bronze (Raw Ingest)**: Append-only streaming ingestion from Kafka (`raw_agent_events_bronze`), maintaining exact source fidelity.
2. **Silver (Cleaned & SCD Type 2)**: Deduplicated, PII-sanitized, and schema-validated tables with Slowly Changing Dimensions (SCD Type 2: `valid_from`, `valid_to`, `is_current`). Freshness SLA < 60s.
3. **Gold (Aggregated Features & Business KPIs)**: Feature stores and compliance metrics stored as optimized Parquet with Delta Time Travel enabled. Retention: 7 years.

## Consequences
- **Positive**: ACID transactions, schema enforcement, 4.2x faster query scans, and sub-minute freshness SLAs.
- **Negative**: Requires periodic Delta `OPTIMIZE` and `VACUUM` maintenance jobs to prevent small file accumulation.
