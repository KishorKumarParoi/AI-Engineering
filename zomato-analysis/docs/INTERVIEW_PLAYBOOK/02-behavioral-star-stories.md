# Principal Engineer Behavioral Interview: STAR Stories

**Role Target**: Principal Systems Architect / Director of Engineering  
**Focus Areas**: High-Severity Production Incidents, Enterprise Migrations, Cloud Cost Reductions, Cross-Functional Technical Leadership.

---

## Story 1: Production Incident (New Year's Eve 14,800 QPS Order Surge)

### Situation:
On New Year's Eve 2025 at 20:45 IST, nationwide order volume surged to an unprecedented 14,800 orders/sec (3.4x normal peak). The Debezium CDC and Kafka streaming pipeline suffered severe consumer lag on hot partitions, causing order confirmations and kitchen dispatch notifications to stall for over 14,000 customers.

### Task:
As Principal Systems Architect, I was the Incident Commander responsible for stabilizing order throughput, protecting financial transaction consistency, preventing double-debits, and mitigating customer churn.

### Action:
1. **Immediate Triage**: Within 3 minutes of the SEV-1 alert, I identified that the root cause was partition key hot-spotting on `city_id` where Mumbai and Bengaluru saturated two Kafka partitions.
2. **Dynamic Scaling**: I quickly executed a live cluster repartitioning to 64 partitions and scaled Kubernetes consumer pods from 32 to 96 replicas.
3. **Compensating Rollbacks**: For orders where restaurant prep times timed out (>180s), I activated our distributed Saga coordinator (`patterns/order_saga.py`) to trigger backward compensating refunds, ensuring zero double debits.
4. **Permanent Prevention**: Following the incident, I authored the SEV-1 postmortem, instituted compound hash partitioning `murmur3(restaurant_id + order_id)`, and updated the operational runbook.

### Result:
Consumer lag was fully cleared within 28 minutes. All 14,200 delayed orders were reconciled with **100% financial accuracy** thanks to SHA-256 idempotency key deduplication. Zero customer disputes required manual debit reversals.

---

## Story 2: Enterprise Migration (50 TB Zero-Downtime Lakehouse & Feature Store)

### Situation:
Zomato's legacy analytics relied on a sprawling PostgreSQL read-replica cluster and fragmented batch cron jobs. Feature data for delivery ETA models was up to 6 hours stale, resulting in erratic delivery time promises during peak traffic. Additionally, cross-region analytical queries caused lock contention on transactional databases.

### Task:
Lead the technical architecture and zero-downtime migration of over 50 TB of operational telemetry to a Medallion Delta Lake on S3, coupled with a low-latency Feast Feature Store serving <50ms real-time features.

### Action:
1. **Architecture Blueprint**: Designed a dual-path ingestion architecture: Debezium CDC streaming to Delta Lake Bronze layer, while simultaneously writing real-time spatial features to Feast Redis cluster.
2. **Dual-Writing & Reconciliation**: Ran a 3-week parallel dual-run phase. Wrote a Python automated reconciliation script validating 100% data contract parity across 45 million daily records.
3. **Cutover Strategy**: Orchestrated an incremental, zero-downtime cutover by city tiers (Tier 3 -> Tier 2 -> Tier 1 Metro). No downtime was incurred by customer-facing apps.

### Result:
- Feature freshness for real-time ETA models dropped from **6 hours to < 45 seconds**.
- ETA prediction error (MAE) decreased by 22%, saving an estimated ₹3.2 Cr annually in late-delivery compensation vouchers.
- Database read load on primary OLTP PostgreSQL was reduced by 68%.

---

## Story 3: Cost Reduction (Slashing Cloud Infrastructure Spend by 42%)

### Situation:
Following aggressive expansion of our AI dispute resolution and computer vision capabilities, our AWS monthly cloud bill ballooned to over $62,000/month, primarily driven by unoptimized GPU instances (`g5.4xlarge`) running full-precision FP16 models and redundant LLM evaluations.

### Task:
Formulate and execute a technical cost optimization roadmap to reduce monthly compute spend by at least 30% within 90 days without compromising model accuracy or customer resolution SLOs.

### Action:
1. **Model Quantization**: Benchmarked and converted our heavy FP16 Vision Transformer damage classifier into an INT8 ONNX Runtime model with TensorRT execution provider. VRAM footprint shrank by 62%, allowing 2x worker packing per GPU node.
2. **Semantic Caching**: Implemented an in-memory vector cache in Redis with cosine similarity thresholding (0.96) to intercept repetitive customer dispute queries. 61.4% of queries bypassed the external LLM entirely with <15ms response times.
3. **Spot Instance Orchestration**: Migrated non-critical Airflow batch processing and offline evaluation harnesses to AWS Karpenter-managed Spot instances with automatic graceful draining.

### Result:
- Reduced monthly cloud spend from **$62,000 to $35,900 (-42.1% net reduction, saving ~$313,000 annually)**.
- P99 dispute resolution latency decreased from 1,850ms to 1,050ms.
- Model F1-score remained completely flat (94.2% vs 94.1%), proving that intelligent systems architecture beats brute-force compute scaling.
