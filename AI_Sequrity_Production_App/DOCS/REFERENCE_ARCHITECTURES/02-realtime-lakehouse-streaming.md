# Reference Architecture 02: Real-Time Event-Driven Lakehouse & Multimodal Dispute Resolution

## 1. Executive Architecture Overview
Designed for high-throughput consumer platforms (e.g. food delivery, logistics, e-commerce). Ingests millions of streaming events per minute via **Apache Kafka**, executes **Spark Structured Streaming** into a **Delta Medallion Lakehouse (Bronze -> Silver -> Gold)** with **Slowly Changing Dimensions (SCD Type 2)**, and leverages a **Multimodal Vision LLM** to resolve customer refund disputes autonomously.

```mermaid
graph TD
    UserApp[Mobile / Web Client] --> Gateway[API Gateway / Kafka Ingress]
    Gateway --> Kafka[Kafka Cluster: Topic 'order_events']
    
    subgraph MedallionLakehouse [Delta Lake Medallion Architecture]
        Kafka --> Spark[Spark Structured Streaming]
        Spark --> Bronze[(Bronze Layer: Raw Append Parquet)]
        Bronze --> Cleanse[Deduplication + Schema Validation]
        Cleanse --> Silver[(Silver Layer: Cleaned Events & SCD-2 Dimensions)]
        Silver --> Agg[Batch Feature Aggregator]
        Agg --> Gold[(Gold Layer: Feature Store & Business KPIs)]
    end
    
    subgraph DisputeResolution [Multimodal AI Dispute Pipeline]
        CustomerPhoto[Dispute Upload: Meal Photo] --> S3[Secure GCS / S3 Bucket]
        S3 --> VisionAgent[Multimodal Vision LLM Agent]
        Gold --> FeatureVector[Customer Trust & Fraud Features]
        FeatureVector --> VisionAgent
        VisionAgent --> Decision{Automated Refund Decision}
        Decision -- "Approved (< $25)" --> PaymentOutbox[Transactional Outbox: Refund Event]
        Decision -- "Flagged / High Value" --> HITLQueue[Human Fraud Ops Review]
    end
```

---

## 2. Quantitative Service Level Objectives (SLOs)
| Metric | SLO Target | Production Measured | Verification Method |
| :--- | :---: | :---: | :--- |
| **Streaming Ingestion Lag** | < 2.0s | **850ms** | Kafka Consumer Lag Offset Monitoring |
| **Silver Freshness SLA** | < 60s | **38s** | Delta micro-batch checkpoint interval |
| **Online Feature Freshness**| < 50ms | **12ms** | Feast Redis online store P99 |
| **Vision Dispute Settlement**| < 4.0s | **2.8s** | End-to-end multimodal inference pipeline |
| **Dispute Fraud Precision** | > 92% | **94.8%** | Manual spot-check audit vs Ground Truth |

---

## 3. Financial Cost Breakdown (Per 1 Million Orders)
| Component | Unit Cost Basis | Monthly / 1M Cost | Optimization Architecture |
| :--- | :--- | :---: | :--- |
| **Kafka Ingestion (MSK / Confluent)**| $0.11 / GB Ingress | $145.00 | Snappy compression + batch coalescing |
| **Dataproc / EMR Spark Workers** | Spot Instance Cluster | $220.00 | Auto-terminating autoscaling clusters |
| **Delta Lake Storage (S3 / GCS)** | $0.023 / GB-month | $46.00 | S3 Intelligent-Tiering to Glacier Deep Archive |
| **Vision LLM (Qwen-2.5-VL / Gemini)**| $0.002 / image analysis | $400.00 | Heuristic filter drops trivial disputes (<$2) |
| **Total Monthly Cost** | — | **$811.00** | **$0.00081 per processed order event** |

---

## 4. Key Architectural Patterns
- **Transactional Outbox & Idempotency**: Refund commands use idempotency keys preventing double-refunds during network retries.
- **SCD Type 2 Historical Tracking**: Restaurant pricing and driver locations maintain `valid_from`, `valid_to`, and `is_current` flags.
- **Feast Shared Feature Store**: Syncs customer lifetime value, historical dispute frequency, and fraud flags in real-time.
