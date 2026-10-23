# Principal AI Systems Design Interview Framework & Whiteboard Drill

## 1. The Principal Engineer 6-Step Whiteboard Framework

```
[ Step 1: Clarify Scope & SLAs ] ──▶ Functional & Non-Functional Requirements
               │
               ▼
[ Step 2: Quantitative Capacity Estimation ] ──▶ QPS, IOPS, Token Bandwidth, Storage/day
               │
               ▼
[ Step 3: High-Level Architecture ] ──▶ Decouple Data Plane vs Control Plane
               │
               ▼
[ Step 4: Deep-Dive Component Design ] ──▶ RAG, Hybrid Re-ranking, Cache, Vector DB
               │
               ▼
[ Step 5: Trade-Off Analysis Matrix ] ──▶ Latency vs Cost vs Accuracy vs VPC Privacy
               │
               ▼
[ Step 6: Failure Modes & Self-Healing ] ──▶ Breached SLOs, Rate Limits, Partitioning
```

---

## 2. Step 1: Clarifying Requirements & Boundaries
Always split into **Functional (FR)** and **Non-Functional Requirements (NFR)**:
- **FR**: Multi-tenant RAG querying, prompt injection interception, autonomous multi-agent task execution, compliance auditing.
- **NFR**:
  - P95 Latency < 1,500ms; Availability: 99.99%.
  - Zero raw PII exposure to external third-party models (GDPR Art. 32).
  - Disaster Recovery: RTO < 30s, RPO < 5s.

---

## 3. Step 2: Capacity & Scale Math (Back-of-the-Envelope)
- **Traffic**: 100M queries / month ≈ 40 queries / sec (QPS) average, 200 QPS peak.
- **Payload & Context Size**:
  - Inbound prompt: ~300 tokens ≈ 1.2 KB.
  - Retrieved context: 5 chunks x 500 tokens = 2,500 tokens ≈ 10 KB.
  - Outbound answer: ~500 tokens ≈ 2 KB.
- **Compute & Token Bandwidth**:
  - Peak Inbound: 200 QPS x 2,800 tokens = **560,000 tokens / sec**.
  - Without semantic caching: Requires ~14 dedicated 70B inference nodes.
  - With 25% semantic caching (<50ms): Drops peak load to 420k tokens/sec, saving 4 nodes ($3,800/mo).

---

## 4. Step 3: Data Plane vs Control Plane Whiteboard

### Data Plane (Hot Path — Sub-Second Ingress)
`Client -> CDN -> BotShield WAF -> PII Tokenizer -> Semantic Cache -> FlashRank ONNX -> Cohere Cross-Attention -> LLM Inference -> Detokenizer -> Client`

### Control Plane (Cold Path — Asynchronous Governance)
`Telemetry -> Transactional Outbox -> Kafka -> Spark Structured Streaming -> Delta Lake (Silver/Gold) -> G-Eval Offline Drift Audit -> Prometheus AlertManager`

---

## 5. Step 4: The 4-Way Trade-Off Matrix (Principal Level)

| Dimension | Option A: Pure SaaS (OpenAI/Cohere) | Option B: Self-Hosted OSS (vLLM / A100) | Option C: Hybrid Edge Cascade (Our Design) |
| :--- | :--- | :--- | :--- |
| **Latency** | Medium (350-600ms network hop) | Very Low (40-120ms in-VPC) | **Optimized (Local ONNX 15ms + Cloud 180ms)** |
| **Cost / Query** | High ($0.015 - $0.030) | High Fixed ($8k/GPU-mo idle) | **Low Variable ($0.00113 with cache)** |
| **Data Privacy** | Sensitive tokens leave VPC | 100% In-VPC isolation | **Pre-filtered PII tokens leave VPC** |
| **Operational Burden**| Zero infrastructure management | High (CUDA, drivers, K8s OOMs) | **Low (Docker, serverless scale-to-zero)** |

---

## 6. Step 5: Failure Modes & Mitigations
1. **Third-Party Rate Limit (HTTP 429)**: Portkey circuit breaker routes traffic to secondary cloud fallback in <140ms.
2. **Adversarial Poisoning of Vector DB**: Cryptographic signature validation on all ingested chunks + hybrid lexical BM25 fallback.
3. **High Latency Drift**: Automated HPA scaling triggered by external P95 latency metrics, not merely CPU.
