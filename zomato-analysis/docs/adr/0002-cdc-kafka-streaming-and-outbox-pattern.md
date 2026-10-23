# ADR 0002: Change Data Capture (CDC), Kafka Streaming, and Transactional Outbox Pattern

## Status: ACCEPTED (Production Standard)

## Context & Problem Statement
Microservices updating local databases (e.g. order placement in PostgreSQL) and simultaneously attempting to publish to Kafka risk dual-write inconsistencies during network partitions or crashes (e.g. order committed to DB but message fails to reach Kafka).

## Decision
We enforce the **Transactional Outbox Pattern** combined with **Debezium Change Data Capture (CDC)**:
1. Microservices commit state changes and an outbox event in the same atomic database transaction.
2. Inbound event consumers enforce **Idempotency Keys** to guarantee exactly-once processing even during Kafka consumer group rebalances.
3. CDC connectors read PostgreSQL write-ahead logs (WAL) to push change streams with zero application performance degradation.

## Consequences
- **Positive**: 100% elimination of dual-write discrepancies; zero duplicate order charges or duplicate refunds.
- **Negative**: Adds an asynchronous outbox polling dispatcher latency (~200ms).
