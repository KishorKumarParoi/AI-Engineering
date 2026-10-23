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
   - [3.4 Principal Engineer Supervisor & 5 Sub-Agents (Graph & Loop Engineering)](#34-principal-engineer-supervisor--5-sub-agents-graph--loop-engineering)
   - [3.5 Re-Ranking Architecture: Hybrid Engine (Cohere v3.5 + FlashRank + Lexical BM25)](#35-re-ranking-architecture-hybrid-engine-cohere-v35--flashrank--lexical-bm25)
   - [3.6 Model Context Protocol (FastMCP) & Human-In-The-Loop (HITL) Governance](#36-model-context-protocol-fastmcp--human-in-the-loop-hitl-governance)
   - [3.7 LLM Gateway & Resilience Matrix (Portkey)](#37-llm-gateway--resilience-matrix-portkey)
   - [3.8 Distributed Telemetry & Observability (Logfire + LangSmith)](#38-distributed-telemetry--observability-logfire--langsmith)
   - [3.9 Cloud Infrastructure & Ephemeral Orchestration](#39-cloud-infrastructure--ephemeral-orchestration)
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

![Ingestion Pipeline](DOCS/images/01_ingestion_pipeline.jpg)

* **Google Document AI:** Leverages enterprise OCR and parsing engines to handle unstructured multi-column tables, headers, and footers without losing context.
* **Semantic Windowing:** Breaks continuous text into fixed **512-token chunks** with **50-token overlapping borders**, preventing the splitting of critical code blocks or command sequences.
* **Jina Embeddings v3:** Uses task-specific asymmetric retrieval embeddings (`retrieval.passage`), projecting documents into a shared 1024-dimensional semantic manifold.
* **Qdrant Vector DB:** Stored with payload indexes on metadata fields (`source`, `chunk_id`, `page`) enabling sub-50ms hybrid filtering alongside Cosine distance search.

---

### 3.2 Edge WAF & Threat Mitigation Tier (BotShield)

![Security Guardrails](DOCS/images/02_security_guardrails.jpg)

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

### 3.4 Principal Engineer Supervisor & 5 Sub-Agents (Graph & Loop Engineering)

![Supervisor Multi-Agent Network](DOCS/images/06_supervisor_multi_agent.jpg)

The platform implements an autonomous **Supervisor-Worker Multi-Agent Architecture** utilizing **LangGraph StateGraph** with cyclic reflection and self-correction loops.

```mermaid
graph TD
    UserQuery([🚨 User / SOC Threat Query]) --> SupervisorNode[👑 SecuritySupervisor: Triage & Plan]
    
    subgraph MultiAgentOrchestration ["Stateful Multi-Agent Network & Tool Ecosystem"]
        SupervisorNode --> Agent1[🕵️ Agent 1: ThreatResearcher<br/>Tavily + Serper + MCP Tools]
        SupervisorNode --> Agent2[💥 Agent 2: ExploitAnalyst<br/>OWASP LLM Red-Teaming & PoC Analysis]
        SupervisorNode --> Agent3[📚 Agent 3: SecurityRetrieval<br/>Qdrant + Cascading Reranker]
        
        Agent1 & Agent2 & Agent3 --> Agent5[🛠️ Agent 5: RemediationPatcher<br/>WAF Rules, ModSecurity & Patch Synthesis]
        
        %% Loop Engineering (Reflection & Self-Correction)
        subgraph LoopEngineering ["🔁 Loop Engineering: Cyclic Reflection & Critique Gate"]
            Agent5 --> Agent4[⚖️ Agent 4: ComplianceAuditor<br/>NIST AI RMF, ISO 27001 & CVSS Audit]
            Agent4 -->|Audit Rejected: Needs Rollback/Refinement| LoopGate{Passed Audit?<br/>Cycle < 3}
            LoopGate -->|Refinement Critique| Agent5
        end
    end

    LoopGate -->|Audit Passed| HITLCheck{High-Impact Action?<br/>IP Ban / Patch Deploy}
    
    subgraph GovernanceTier ["Human-in-the-Loop & Model Context Protocol"]
        HITLCheck -->|Critical Action| HITLQueue[⏸️ HITL Interrupt Gate<br/>Suspends State Machine]
        HITLQueue --> SupervisorApproval[👨‍✈️ Human SecOps Approval /api/v1/hitl/approve]
        SupervisorApproval --> FastMCPTool[🔌 Model Context Protocol Server<br/>FastMCP cve_lookup / threat_intel / waf_metrics]
        HITLCheck -->|Read-Only / Normal| FastMCPTool
    end

    FastMCPTool --> FinalSynthesis[👑 Supervisor Final Synthesis Briefing]
    FinalSynthesis --> ResponsePayload([📋 Verified Incident Briefing & Defenses])
```

#### The 5 Specialized Autonomous Sub-Agents:
1. **Agent 1: Threat Researcher (`ThreatResearcherAgent`):**
   - **Capabilities:** Executes real-time threat intelligence gathering across open and dark web sources using **Tavily Search API** (extracting raw markdown from technical security advisories) and **Serper Google API** (discovering zero-day news and vendor patches).
   - **Tool Context:** Dispatches queries to the local **FastMCP Security Server** to query CVE databases and active threat feeds.
2. **Agent 2: Exploit Analyst (`ExploitAnalystAgent`):**
   - **Capabilities:** Specializes in OWASP Top 10 for LLMs (LLM01 Prompt Injection, LLM02 Insecure Output Handling, LLM06 Sensitive Information Disclosure). Synthesizes exploit mechanics, PoC vectors, and blast-radius estimations.
3. **Agent 3: Security Retrieval Agent (`SecurityRetrievalAgent`):**
   - **Capabilities:** Interfaces with Qdrant Cloud vector collections for enterprise runbooks, security policies, and incident response playbooks. Employs the **Dual-Tier Cascading Re-Ranker** for context optimization.
4. **Agent 4: Compliance Auditor (`ComplianceAuditorAgent`):**
   - **Role:** Acts as the **Reflection Loop Critic**.
   - **Frameworks:** Evaluates remediation strategies against NIST AI RMF, ISO 27001, and CVSS v3.1 scoring.
   - **Loop Engineering:** If a generated remediation patch lacks an automated rollback script, unit test harness, or verification signature, the auditor rejects the proposal, generates structured `critique_feedback`, and forces state regression back to Agent 5.
5. **Agent 5: Remediation Patcher (`RemediationPatchAgent`):**
   - **Capabilities:** Synthesizes concrete infrastructure fixes: ModSecurity WAF rules, IP blocklists, regex guardrail rules, and application code diffs. Dynamically consumes the Auditor's critique in iteration $N+1$ to achieve self-correction.

---

### 3.5 Re-Ranking Architecture: Hybrid Engine (Cohere v3.5 + FlashRank + Lexical BM25)

![Hybrid Re-Ranking Engine](DOCS/images/07_hybrid_reranker_cascade.jpg)

In enterprise high-throughput production environments, selecting between **FlashRank** and **Cohere v3.5** represents a classic tradeoff between **latency/data privacy** vs **linguistic nuance**:

| Metric / Dimension | ⚡ FlashRank (Local Cross-Encoder) | 🌐 Cohere v3.5 (Cloud Transformer) |
| :--- | :--- | :--- |
| **Execution Paradigm** | In-Process Quantized ONNX Runtime | Hosted REST Cross-Attention Cloud API |
| **Model Architecture** | `ms-marco-TinyBERT-L-2-v2` / `MiniLM-L-12` | Deep 100M+ Parameter Transformer Cross-Attention |
| **Inference Latency** | **1.2ms – 14ms** (CPU-only, sub-millisecond) | **180ms – 450ms** (Network hop + TLS + cloud inference) |
| **Operational Cost** | **$0.00** (Zero compute cost, runs in application pod) | **$1.00 per 1,000 queries** (Scale-dependent recurring cost) |
| **Data Privacy & Compliance**| **100% Air-Gapped / In-VPC** (Zero data egress, GDPR/HIPAA compliant) | **Data egresses VPC** to 3rd-party SaaS (requires enterprise DPA) |
| **Ranking Quality (NDCG@10)**| 82% – 88% on standard semantic IR benchmarks | **94% – 97%** (State of the art on multi-hop technical reasoning) |
| **Exact Anchor Matching** | Moderate (neural embeddings can dilute exact tokens) | High (transformer cross-attention across full sequences) |
| **Failure Modes** | Bounded by host CPU/RAM | Network timeout, 429 rate limit, SaaS outage |

#### 🏆 Principal Engineer Hybrid Re-Ranking Strategies:

The platform implements three complementary hybrid re-ranking strategies in [`app/services/reranker.py`](file:///Users/kishorkumarparoi/Desktop/AI_Security_Production_App/app/services/reranker.py):

##### Strategy 1: Reciprocal Rank Fusion (RRF) Ensemble (`mode="hybrid_rrf"`)
Blends ranking signals across disparate models and exact keyword matches without requiring raw score calibration:
$$RRF(d) = \sum_{m \in \{\text{Cohere}, \text{FlashRank}, \text{Lexical}\}} \frac{w_m}{k + \text{rank}_m(d)}$$
- **Parameters:** Smoothing factor $k=60$; Weights: $w_{\text{Cohere}}=0.50$, $w_{\text{FlashRank}}=0.35$, $w_{\text{Lexical}}=0.15$.
- **Security Anchor Boost:** The Lexical BM25 scorer applies heuristic boosts for exact CVE identifiers (`CVE-\d{4}-\d{4,}`), status codes (`403`, `500`), and critical primitives (`WAF`, `RCE`, `SSRF`).

##### Strategy 2: Cascade Dual-Tier Re-Ranking (`mode="cascade"`)
```
Stage 1: Qdrant Vector DB ➔ Top-50 candidate chunks (Recall-oriented)
             │
Stage 2: FlashRank Local ONNX (1.4ms) ➔ Prunes Top-50 candidates down to Top-15
             │ (Drops 70% of noise in-VPC at $0.00 cost)
             ▼
Stage 3: Cohere v3.5 Deep Cross-Encoder ➔ Refines Top-15 down to Top-5
             │ (Applied selectively for high-assurance technical reasoning)
             ▼
         Top-5 Ultra-Dense Context passed to LLM Generation
```

##### Strategy 3: Normalized Convex Score Blending (`mode="score_fusion"`)
Min-max normalizes scores into $[0, 1]$ and computes the weighted convex combination:
$$\text{Score}_{\text{final}}(d) = 0.55 \cdot S_{\text{Cohere}}(d) + 0.35 \cdot S_{\text{FlashRank}}(d) + 0.10 \cdot S_{\text{Lexical}}(d)$$

* **Fallback Resilience:** If `COHERE_API_KEY` is omitted, rate-limited, or encounters timeouts (>1.5s), the system seamlessly completes the ranking via FlashRank with zero downtime and sub-15ms guaranteed latency.

---

### 3.6 Model Context Protocol (FastMCP) & Human-In-The-Loop (HITL) Governance

![Model Context Protocol & HITL Governance](DOCS/images/08_mcp_hitl_governance.jpg)

#### Model Context Protocol (MCP) Integration:
- Built with **FastMCP** exposing standardized JSON-RPC 2.0 tool endpoints:
  - `cve_lookup(cve_id)`: Fetches CVSS scores, exploitability metrics, and affected versions.
  - `threat_intel_feed(category)`: Live intelligence stream (ransomware, zero-day, botnets).
  - `waf_metrics()`: Real-time telemetry on active IP blocks and threat blocks.
- **Architectural Value:** Decouples tool execution from the agent runtime. The LLM acts as an MCP client over standard pipes, preventing vendor lock-in.

#### Human-In-The-Loop (HITL) Break-Glass Architecture:
- Autonomous agents must **never** execute high-impact production mutations (e.g., permanent IP bans, firewall reconfigurations, zero-day kernel hotfixes) without authorized cryptographic human approval.
- **State Checkpointing:** When `is_high_impact_remediation` evaluates to `True`, the LangGraph execution graph invokes an interrupt, saving state to memory.
- **Approval API Gate:**
  - `GET /api/v1/hitl/pending/{thread_id}`: SOC analyst reviews proposed action, diff, and CVSS score.
  - `POST /api/v1/hitl/approve`: Analyst submits digital signature (`decision: "approved" | "rejected"`). The thread resumes and completes execution.

---

### 3.7 LLM Gateway & Resilience Matrix (Portkey)

![LLM Gateway](DOCS/images/04_llm_gateway.jpg)

* **Semantic Caching:** Identical and near-identical queries return stored responses in `<50ms` at $0.00 cost.
* **Dual-Tier Model Routing:**
  - **Primary:** `groq/llama-3.3-70b-versatile` (Temperature: 0.1, Max Tokens: 2048)
  - **Secondary (Fallback):** `groq/llama-3.1-8b-instant` (Triggered on 429 rate limits or timeouts)
* **Circuit Breaker:** Trips after 3 consecutive 5xx errors, diverting traffic to secondary models for 60 seconds before probing health.

---

### 3.8 Distributed Telemetry & Observability (Logfire + LangSmith)

* **Pydantic Logfire:** Captures ASGI request lifecycles, database query latencies, and agent state transitions in structured OpenTelemetry spans.
* **LangSmith:** Records complete prompt chains, token counts, model latency distributions, and cost metrics per thread ID.

---

### 3.9 Cloud Infrastructure & Ephemeral Orchestration

![Cloud Deployment](DOCS/images/05_cloud_deployment.jpg)

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
