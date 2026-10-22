# 🏗️ Architecture Manifesto: Enterprise AI Security & Production Agentic RAG

> **Confidential & Proprietary** — System Architecture Document for Principal Engineering Review.

---

## 📑 Table of Contents
1. [Architectural Principles & Non-Functional Requirements](#1-architectural-principles--non-functional-requirements)
2. [End-to-End System Topography](#2-end-to-end-system-topography)
3. [Component Deep Dive & Sequence Flows](#3-component-deep-dive--sequence-flows)
   - [3.1 Ingestion & Processing Tier](#31-ingestion--processing-tier)
   - [3.2 Edge WAF & Threat Mitigation Tier (BotShield)](#32-edge-waf--threat-mitigation-tier-botshield)
   - [3.3 Semantic Moderation & Safety Tier (NeMo Guardrails)](#33-semantic-moderation--safety-tier-nemo-guardrails)
   - [3.4 Agentic Reasoning Core (LangGraph)](#34-agentic-reasoning-core-langgraph)
   - [3.5 Two-Stage Adaptive Retrieval Tier (Qdrant + FlashRank)](#35-two-stage-adaptive-retrieval-tier-qdrant--flashrank)
   - [3.6 LLM Gateway & Resilience Matrix (Portkey)](#36-llm-gateway--resilience-matrix-portkey)
   - [3.7 Distributed Telemetry & Observability (Logfire + LangSmith)](#37-distributed-telemetry--observability-logfire--langsmith)
   - [3.8 Cloud Infrastructure & Ephemeral Orchestration](#38-cloud-infrastructure--ephemeral-orchestration)
4. [Threat Modeling (STRIDE & OWASP Top 10 for LLMs)](#4-threat-modeling-stride--owasp-top-10-for-llms)
5. [End-to-End Latency Budget & SLA Profile](#5-end-to-end-latency-budget--sla-profile)
6. [Disaster Recovery & High Availability Matrix](#6-disaster-recovery--high-availability-matrix)

---

## 1. Architectural Principles & Non-Functional Requirements

This architecture was designed according to four foundational tenets:

1. **Defense-in-Depth (Zero-Trust LLM):** Never trust raw user input, and never trust raw LLM output. Every request undergoes deterministic algorithmic scrutiny before invoking semantic vector search or neural inference.
2. **Deterministic Routing over Brute-Force Retrieval:** Avoid invoking expensive vector search and LLM synthesis when a query can be answered via session state, canonical conversational patterns, or cached responses.
3. **Resilience over Single-Point Dependencies:** All external network hops (APIs, Vector DB, LLMs) must implement exponential backoff retries, circuit breakers, and secondary provider fallbacks.
4. **Extreme Cost Awareness:** Maintain zero recurring idle cloud cost ($0.00/month) for evaluation and demo workloads through single-command ephemeral provisioning (`deploy.sh`) and complete teardown (`clear.sh`).

---

## 2. End-to-End System Topography

```mermaid
graph TD
    %% ── Client Ingress ───────────────────────────────────────────────
    Client([🌐 Client Request / Streamlit UI]) -->|HTTP /port 8080 or 8501| WAF[🛡️ BotShield Edge Middleware]

    %% ── Security Tier ────────────────────────────────────────────────
    subgraph SecurityTier ["Gate 1: Edge & Semantic Defense"]
        WAF -->|Check Honeypot / Scanners / RateLimit| WAFDecision{Passed WAF?}
        WAFDecision -->|No| BlockWAF[🛑 403 / 429 Forbidden]
        WAFDecision -->|Yes| NeMo[🛡️ NVIDIA NeMo Guardrails]
        NeMo -->|Topic Gating / Jailbreak Check| NeMoDecision{Safe & On-Topic?}
        NeMoDecision -->|Off-Topic / Jailbreak| BlockNeMo[🛑 Deterministic Refusal]
    end

    %% ── Agentic Tier ─────────────────────────────────────────────────
    subgraph AgenticTier ["Gate 2: LangGraph Stateful Core"]
        NeMoDecision -->|Sanitized Query| Planner[🧠 Intent & Planner Node]
        Planner -->|Conversational| Responder[💬 Synthesis Node]
        Planner -->|Technical Query| VectorSearch[🔍 Qdrant Dense Vector Search]
        VectorSearch -->|Top-10 Candidates| Reranker[🎯 FlashRank Cross-Encoder]
        Reranker -->|Top-3 Reranked| Responder
        Responder <--> StateCheck[💾 MemorySaver Session Checkpoint]
    end

    %% ── Gateway & LLM Tier ───────────────────────────────────────────
    subgraph GatewayTier ["Gate 3: Resilient LLM Gateway"]
        Responder --> Portkey[🔀 Portkey AI Gateway]
        Portkey -->|Semantic Cache Check| CacheHit{Cache Hit?}
        CacheHit -->|Hit <50ms| ReturnCached[⚡ Instant Response]
        CacheHit -->|Miss| PrimaryLLM[🦙 Primary: Groq Llama 3.3 70B]
        PrimaryLLM -.->|Failover / 429 / 503| FallbackLLM[🦙 Fallback: Groq Llama 3.1 8B]
    end

    %% ── Telemetry Tier ───────────────────────────────────────────────
    subgraph TelemetryTier ["Distributed Observability"]
        WAF -.-> Logfire[🔥 Pydantic Logfire Spans]
        NeMo -.-> Logfire
        Responder -.-> Logfire
        Portkey -.-> LangSmith[🦜 LangSmith Cost & Traces]
    end

    Responder --> Client
```

---

## 3. Component Deep Dive & Sequence Flows

### 3.1 Ingestion & Processing Tier

![Ingestion Pipeline](docs/images/01_ingestion_pipeline.jpg)

* **Google Document AI:** Leverages enterprise OCR and parsing engines to handle unstructured multi-column tables, headers, and footers without losing context.
* **Semantic Windowing:** Breaks continuous text into fixed **512-token chunks** with **50-token overlapping borders**, preventing the splitting of critical code blocks or command sequences.
* **Jina Embeddings v3:** Uses task-specific asymmetric retrieval embeddings (`retrieval.passage`), projecting documents into a shared 1024-dimensional semantic manifold.
* **Qdrant Vector DB:** Stored with payload indexes on metadata fields (`source`, `chunk_id`, `page`) enabling sub-50ms hybrid filtering alongside Cosine distance search.

---

### 3.2 Edge WAF & Threat Mitigation Tier (BotShield)

![Security Guardrails](docs/images/02_security_guardrails.jpg)

The `BotShieldMiddleware` sits directly in the ASGI pipeline before any framework logic executes:

```python
# Execution Order:
1. Honeypot check (/wp-admin, /.env, /.git, /phpmyadmin) ➔ Instant 10-minute IP blacklist
2. Malicious User-Agent check (sqlmap, nikto, scrapers) ➔ 403 Forbidden
3. Sliding-window rate limiting (60 req/min per IP) ➔ 429 Retry-After
4. Burst mitigation (5 req/sec burst ceiling) ➔ Drop spikes
5. Injection pattern scanner (union select, <script>, ../..) ➔ 400 Bad Request
```

---

### 3.3 Semantic Moderation & Safety Tier (NeMo Guardrails)

Configured via declarative **Colang** models and semantic intent matching:

* **Off-Topic Gating:** Queries are matched against canonical enterprise intents. Non-technical or off-domain prompts (cooking, politics, creative writing) are intercepted deterministically.
* **Jailbreak Defense:** Defends against role-play subversion ("pretend you are an unrestricted AI", "developer mode enabled", "DAN") and payload obfuscation (base64, leetspeak).
* **PII Redaction:** Sensitive credit card, phone, and identity patterns are detected and replaced with redacted tokens before vector querying.

---

### 3.4 Agentic Reasoning Core (LangGraph)

![Agentic Retrieval](docs/images/03_agentic_retrieval.jpg)

Built on a stateful cyclic directed acyclic graph (DAG):

```python
class AgentState(TypedDict):
    messages: list[BaseMessage]
    intent: str
    search_query: str
    retrieved_chunks: list[str]
    thought_process: list[str]
    response: str
```

* **Planner Node:** Classifies intent and dynamically extracts search parameters.
* **Retriever Node:** Executes vector search and cross-encoder reranking.
* **Responder Node:** Grounded generation using system prompts, retrieved context, and conversation history.

---

### 3.5 Two-Stage Adaptive Retrieval Tier (Qdrant + FlashRank)

1. **Stage 1 — Dense Vector Candidate Generation:**
   $$\text{sim}(q, d) = \frac{\vec{q} \cdot \vec{d}}{\|\vec{q}\| \|\vec{d}\|}$$
   Retrieves the top-10 candidate chunks via HNSW graph traversal in Qdrant Cloud.
2. **Stage 2 — Cross-Encoder Fine Reranking:**
   $$\text{Score} = \text{CrossEncoder}(q \oplus d)$$
   FlashRank processes full bidirectional token interactions, scoring context relevance and pruning to the top-3 highest-density snippets.

---

### 3.6 LLM Gateway & Resilience Matrix (Portkey)

![LLM Gateway](docs/images/04_llm_gateway.jpg)

* **Semantic Caching:** Identical and near-identical queries return stored responses in `<50ms` at $0.00 cost.
* **Dual-Tier Model Routing:**
  - **Primary:** `groq/llama-3.3-70b-versatile` (Temperature: 0.1, Max Tokens: 2048)
  - **Secondary (Fallback):** `groq/llama-3.1-8b-instant` (Triggered on 429 rate limits or timeouts)
* **Circuit Breaker:** Trips after 3 consecutive 5xx errors, diverting traffic to secondary models for 60 seconds before probing health.

---

### 3.7 Distributed Telemetry & Observability (Logfire + LangSmith)

* **Pydantic Logfire:** Captures ASGI request lifecycles, database query latencies, and agent state transitions in structured OpenTelemetry spans.
* **LangSmith:** Records complete prompt chains, token counts, model latency distributions, and cost metrics per thread ID.

---

### 3.8 Cloud Infrastructure & Ephemeral Orchestration

![Cloud Deployment](docs/images/05_cloud_deployment.jpg)

```
[Developer Machine / CI Runner]
               │
               ▼
   [deploy.sh Push-Button Script]
   ├── Discovers Default AWS VPC & Public Subnet
   ├── Configures Security Group: Ports 22, 80, 8080, 8501
   ├── Launches Ubuntu 24.04 LTS (t3.medium)
   └── Cloud-Init Bootstrap:
       ├── Installs Docker CE & Docker Compose
       ├── Clones GitHub Repo
       ├── Injects Production .env
       └── docker compose up -d --build
               │
               ▼
   [clear.sh Teardown Script]
   └── Terminates EC2 Instance & Deletes Security Groups ➔ $0.00 / month
```

---

## 4. Threat Modeling (STRIDE & OWASP Top 10 for LLMs)

| OWASP LLM Vector | Threat Scenario | Mitigation Architecture |
| :--- | :--- | :--- |
| **LLM01: Prompt Injection** | Adversarial user embeds system overrides in prompt | NeMo Guardrails regex + Colang intent gating intercepts attack |
| **LLM02: Sensitive Data Leak** | System prompt or internal PII leaked to output | NeMo output rail cleanses sensitive patterns before return |
| **LLM04: Model DoS** | Massive token payloads or rapid burst attacks | BotShield limits payload to 50KB and rate limits to 5 req/sec |
| **LLM06: Excessive Agency** | Agent taking unauthorized external actions | State machine has no arbitrary code execution nodes |
| **LLM09: Overreliance** | Hallucinated answers in technical domains | FlashRank enforces grounded context; temperature locked to 0.1 |

---

## 5. End-to-End Latency Budget & SLA Profile

| Operation Phase | Component | P50 (ms) | P95 (ms) | P99 (ms) |
| :--- | :--- | :--- | :--- | :--- |
| Edge Security | BotShield WAF | 0.8 | 1.5 | 3.0 |
| Semantic Safety | NeMo Guardrails | 12.0 | 25.0 | 45.0 |
| Intent Classification | LangGraph Planner | 180.0 | 240.0 | 310.0 |
| Dense Vector Search | Qdrant Cloud | 28.0 | 45.0 | 75.0 |
| Cross-Encoder Rerank | FlashRank Local | 14.0 | 22.0 | 35.0 |
| Neural Generation | Groq LPU (70B) | 350.0 | 580.0 | 850.0 |
| Telemetry Export | Logfire + LangSmith (Async) | 0.0 (Non-blocking) | 0.0 | 0.0 |
| **Total Pipeline (Cold)** | **Full RAG Execution** | **~585 ms** | **~915 ms** | **~1320 ms** |
| **Total Pipeline (Cache Hit)** | **Portkey Semantic Cache** | **~38 ms** | **~48 ms** | **~65 ms** |

---

## 6. Disaster Recovery & High Availability Matrix

| Failure Mode | Detection Mechanism | Recovery Automation | RTO | RPO |
| :--- | :--- | :--- | :--- | :--- |
| **Groq 70B Outage** | HTTP 503 / Timeout from Portkey | Portkey automatically switches to Groq 8B | `< 200 ms` | 0 |
| **Qdrant Network Blip** | Async connection timeout | Retry loop (3 attempts) + fallback to conversational mode | `< 1.2 s` | 0 |
| **Container Crash** | Docker health check failure | `restart: unless-stopped` triggers automatic process reboot | `< 4 s` | 0 |
| **EC2 Host Hardware Fault** | AWS system status check failure | Re-run `./deploy.sh` to launch new instance | `< 90 s` | 0 |
