# 🛡️ Threat Model: Zomato Streaming Lakehouse & Delivery AI Platform

## 1. System Overview & Trust Boundaries
The Zomato platform handles high-velocity order events, rider telemetry, customer payment tokens, and automated dispute resolution across 500+ cities.
- **TB-1: Public Edge**: Mobile apps, rider GPS streams, restaurant partner portals (Gated by CloudFront, AWS WAF, and BotShield).
- **TB-2: Event Ingestion Boundary**: Kafka Ingress Broker cluster and Debezium CDC connectors.
- **TB-3: Storage & Processing Core**: AWS EKS cluster, Delta Lake Medallion S3 buckets encrypted with KMS CMK.
- **TB-4: Automated Decisioning Engine**: Autonomous refund RAG service with financial bound gating.

---

## 2. STRIDE Threat Analysis Matrix

| Threat Category | Specific Threat Vector | Architectural Mitigation | Residual Risk |
| :--- | :--- | :--- | :---: |
| **Spoofing** | Compromised Delivery Partner reporting fake GPS arrival | Cell tower triangulation + cryptographically signed MQTT payloads | **LOW** |
| **Tampering** | Man-in-the-middle modification of order pricing or cart subtotal | Strict Pydantic Data Contracts with checksum validation on subtotal | **NEGLIGIBLE** |
| **Repudiation** | Customer denies receiving meal; claims full refund fraudulently | Multimodal photo upload + delivery partner OTP confirmation | **LOW** |
| **Information Disclosure** | Customer mobile number or address leaked in analytical logs | PII tokenization engine masking phone numbers before lakehouse ingestion | **LOW** |
| **Denial of Service** | Botnet flooding flash sale or New Year's Eve order streams | Inbound sliding-window rate limiting (60 rpm, 5 burst/s) + HPA auto-scaling | **LOW** |
| **Elevation of Privilege** | Autonomous dispute agent tricked into issuing arbitrary refunds | Prompt injection defense + hard financial refund caps (₹1,500 INR max) | **LOW** |
