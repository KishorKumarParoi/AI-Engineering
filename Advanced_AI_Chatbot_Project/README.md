# 🛡️ Enterprise Autonomous AI Production Chatbot & Governance Platform

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Stateful%20Agents-FF6F00?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Model Context Protocol](https://img.shields.io/badge/Anthropic-MCP%20Protocol-8A2BE2)](https://modelcontextprotocol.io/)
[![BotShield WAF](https://img.shields.io/badge/BotShield-Enterprise%20WAF-10B981)](https://github.com/KishorKumarParoi/)
[![Qdrant Vector DB](https://img.shields.io/badge/Qdrant-Hybrid%20Dense%2BSparse-DC2626?logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Streamlit UI](https://img.shields.io/badge/Streamlit-1.42-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20Checkpoints-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)

> **A mission-critical, enterprise-grade Conversational AI and Operational Agent platform engineered for high-throughput, fault-tolerant e-commerce environments.** Built on a **Decoupled Microservice Architecture** with **LangGraph state machines**, native **Model Context Protocol (MCP)** tool execution, **Human-in-the-Loop (HITL) financial governance gating**, **BotShield WAF dual-layer security**, and real-time **Server-Sent Events (SSE)** streaming.

---

## 📑 Table of Contents
1. [Executive Architectural Summary](#-executive-architectural-summary)
2. [What Makes This Stand Out from Naive Chatbots](#-what-makes-this-stand-out-from-naive-chatbots)
3. [Step-by-Step Visual Architecture & System Flows](#-step-by-step-visual-architecture--system-flows)
   - [Step 1: Hybrid Vector Ingestion & Multi-Payload Indexing](#step-1-hybrid-vector-ingestion--multi-payload-indexing)
   - [Step 2: BotShield Edge WAF & Adversarial Threat Mitigation](#step-2-botshield-edge-waf--adversarial-threat-mitigation)
   - [Step 3: LangGraph Cyclic Multi-Turn Intent & Reasoning Graph](#step-3-langgraph-cyclic-multi-turn-intent--reasoning-graph)
   - [Step 4: Model Context Protocol (MCP) Dynamic Tool Integration](#step-4-model-context-protocol-mcp-dynamic-tool-integration)
   - [Step 5: Human-in-the-Loop (HITL) Checkpointing & Supervisor Gating](#step-5-human-in-the-loop-hitl-checkpointing--supervisor-gating)
4. [Technology Stack & Architectural Tool Matrix](#-technology-stack--architectural-tool-matrix)
5. [Principal Engineer Design Rationale & Trade-Offs](#-principal-engineer-design-rationale--trade-offs)
6. [Local Development & Production Runbook](#-local-development--production-runbook)
7. [Automated Verification & Test Harness](#-automated-verification--test-harness)
8. [Principal Engineer Interview Defense Guide](#-principal-engineer-interview-defense-guide)

---

## 🏛️ Executive Architectural Summary

Standard tutorial chatbots simply pipe prompts into LLM completion APIs. In enterprise reality, that results in **prompt injection breaches, DDOS token-drain attacks, unauthorized financial transactions (refunds/discounts), hallucinated inventory, and zero session auditability**.

This platform solves these production failure modes with a **Defense-in-Depth, Decoupled Architecture**:

```
[Inbound Client Traffic (Browser / API)]
                │
                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. EDGE SECURITY: BotShield WAF Middleware                              │
│    • Honeypot Traps (/wp-admin, /.env, /.git) -> Proactive 600s IP Ban  │
│    • Scanner Fingerprint Dropping (sqlmap, nikto, wpscan, nmap)        │
│    • Sliding-Window Rate Limiting (60 req/min, 8 req/sec burst)         │
│    • Defensive Headers (X-Content-Type-Options: nosniff, DENY)          │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ Clean HTTP / SSE Request
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. INPUT GUARDRAILS: Prompt Security & PII Sanitizer                     │
│    • Adversarial Jailbreak Interception (DAN, instruction override)     │
│    • System Prompt Exfiltration Blocker                                │
│    • Sensitive PII Redaction (Credit Cards, SSNs, API Keys)             │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ Sanitized Inbound Payload
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. ORCHESTRATION: LangGraph Stateful Cyclic Multi-Agent Engine           │
│    • Intent Router (FAQ / Technical Search / Mutation / Complex Multi)   │
│    • Query Decomposition & Multi-Query Expansion                        │
│    • Session Checkpointing (PostgreSQL / In-Memory State Savers)        │
└──────────────┬────────────────────────────────────────────┬─────────────┘
               │ Operational Mutation                       │ Search / Analytics
               ▼                                            ▼
┌──────────────────────────────────────────┐   ┌──────────────────────────┐
│ 4. HITL GOVERNANCE GATEWAY               │   │ 5. MCP CLIENT BRIDGE     │
│    • High-Stakes Interception:           │   │    • Dynamic Tool Schema │
│      - Refunds > $50                     │   │    • Catalog Server      │
│      - Order Cancellations               │   │      (Port 8002)         │
│      - Promotional Codes > 15%           │   │    • Reviews Analytics   │
│    • Execution Interrupted & Suspended   │   │      (Port 8003)         │
│    • Real-time SSE Supervisor Alert      │   │    • High-Speed Fallback │
│    • Resume past Checkpoint upon Sign-Off│   │    • Qdrant Hybrid HNSW  │
└──────────────────┬───────────────────────┘   └────────────┬─────────────┘
                   │                                        │
                   └──────────────────┬─────────────────────┘
                                      │ Streaming SSE Chunks
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 6. PRESENTATION: Streamlit Real-Time SSE Client UI                      │
│    • Micro-Step Progress Visualizer (Analyzing ➔ MCP Invoking ➔ Fusion)  │
│    • Dynamic Product Cards with Hi-Res Images, Badges, & Star Ratings   │
│    • Live Interactive Supervisor Approval & Rejection Console           │
│    • Distributed Feedback Loop (LangSmith Trace ID Integration)         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 💎 What Makes This Stand Out from Naive Chatbots

| Dimension | Naive Tutorial Chatbots | This Principal-Grade Platform |
| :--- | :--- | :--- |
| **Tool Calling Standard** | Hardcoded python functions tightly coupled in-process | **Model Context Protocol (MCP)**: Microservices communicate via standardized JSON-RPC with dynamic capability negotiation. |
| **High-Stakes Actions** | Autonomous execution risking financial loss | **Human-in-the-Loop (HITL)**: Graph state is paused and checkpointed; sensitive actions require supervisor authorization. |
| **Adversarial Security** | Vulnerable to `"Ignore previous instructions"` | **BotShield WAF**: Honeypots, scanner drops, sliding-window rate limiting, and regex jailbreak interception. |
| **Retrieval Architecture** | Basic dense vector top-k cosine similarity | **Hybrid Search**: Dense vectors (`text-embedding-3-small`) + sparse BM25 payload filters + Reciprocal Rank Fusion. |
| **State Persistence** | Transient memory lost on restart | **Checkpointed State Graph**: PostgreSQL-backed LangGraph state allowing multi-turn paused sessions to resume seamlessly. |
| **Streaming Protocol** | Chunked REST polling or raw blocks | **Industrial SSE**: Low-latency Server-Sent Events yielding step status, tool execution traces, and context cards. |

---

## 📸 Step-by-Step Visual Architecture & System Flows

### Step 1: Hybrid Vector Ingestion & Multi-Payload Indexing

![Ingestion Pipeline](docs/images/01_ingestion_pipeline.jpg)

#### Technical Workflow:
1. **Raw Catalog Ingestion**: High-volume e-commerce catalog (`data/Data_With_Images.jsonl`) parsed with whitespace-stripping generators.
2. **Dense & Sparse Vector Generation**: Products embedded with OpenAI `text-embedding-3-small` (1536 dimensions) paired with lexical keyword indices.
3. **Payload Indexing in Qdrant**: High-performance HNSW vector indices mapped to metadata payloads (`parent_asin`, `brand`, `price`, `ratings`, `images`, `features`).
4. **Resilient Network Bridge**: Dynamic container host resolution (`http://qdrant:6333` in Docker, `http://localhost:6333` locally).

---

### Step 2: BotShield Edge WAF & Adversarial Threat Mitigation

![Security Guardrails Flow](docs/images/02_security_guardrails.jpg)

#### Security Enforcement Pipeline:
1. **Honeypot Trap Defense**: Instant 10-minute IP blacklisting for bots probing `/.env`, `/.git`, `/wp-admin`, or `/phpmyadmin`.
2. **Scanner User-Agent Drops**: Automatic 403 Forbidden rejection for vulnerability scanners (`sqlmap`, `nikto`, `wpscan`, `nmap`).
3. **Sliding-Window Rate Limiter**: 60 requests/minute per client IP with strict 8 req/sec burst protection.
4. **Prompt Injection Guardrail**: Pattern-based interception blocking instruction overrides, DAN roleplay exploits, and system exfiltration.
5. **PII Sanitizer**: Regex redaction scrubbing credit cards, SSNs, and API keys from both input queries and output responses.

---

### Step 3: LangGraph Cyclic Multi-Turn Intent & Reasoning Graph

![Agentic Retrieval Flow](docs/images/03_agentic_retrieval.jpg)

#### State Machine Routing Logic:
1. **Intent Classification Node**: Pre-routes queries to `General QnA`, `Technical Retrieval`, or `Mutation Action`.
2. **Query Decomposition Node**: Deconstructs multi-intent prompts (e.g., *"Laptop for my wife, tablet for my kid, and waterproof speaker for a party"*) into independent search branches.
3. **Parallel Tool Invocation**: Dispatches concurrent retrievals across isolated catalog partitions.
4. **Aggregator & Synthesis Node**: Synthesizes structured markdown bullet points with product references, ratings, and price breakdowns.

---

### Step 4: Model Context Protocol (MCP) Dynamic Tool Integration

![LLM Gateway & MCP Flow](docs/images/04_llm_gateway.jpg)

#### Standardized Protocol Architecture:
1. **Decoupled FastMCP Servers**:
   - `apps/mcp_server` (Port 8002): Product Catalog Inventory & Item Details.
   - `apps/mcp_server_reviews` (Port 8003): Amazon Reviews Sentiment & Qualitative Insights.
2. **MCP Client Manager**:
   - Manages asynchronous connections to external MCP endpoints.
   - Dynamically checks cluster health and discovers tool schemas.
   - **Zero-Downtime Fallback**: If an MCP microservice is cycling or deploying, automatically falls back to in-process execution with zero end-user disruption.

---

### Step 5: Human-in-the-Loop (HITL) Checkpointing & Supervisor Gating

![Cloud Deployment & HITL Flow](docs/images/05_cloud_deployment.jpg)

#### Financial & Operational Governance Workflow:
1. **Sensitive Action Detection**: Identifies sensitive operational intents (`request_refund`, `cancel_order`, `apply_manager_discount`, `escalate_human_agent`).
2. **LangGraph Interruption**: Halts execution, serializes thread state into PostgreSQL checkpointer, and marks action as `pending_approval`.
3. **Real-time SSE Notification**: Emits an SSE event `type: "hitl_required"` containing action ID, severity, and payload parameters.
4. **Streamlit Supervisor Console**: Renders an interactive authorization card with `[✅ Authorize]` and `[❌ Decline]` actions.
5. **Resumption API (`/rag/hitl/approve`)**: Supervisor decision resumes the graph from the exact checkpoint, committing approved transactions or providing alternative paths.

---

## 🛠️ Technology Stack & Architectural Tool Matrix

| Component | Technology | Version | Architectural Justification |
| :--- | :--- | :--- | :--- |
| **Agent Orchestrator** | LangGraph | `^0.2.68` | Cyclic state graph engine with checkpoints, parallel node fan-out, and interruption support. |
| **API Framework** | FastAPI | `^0.115.0` | High-throughput asynchronous ASGI web server with native SSE streaming and Pydantic v2 schemas. |
| **Tool Protocol** | FastMCP / Anthropic MCP | `^0.4.1` | Standardized Model Context Protocol enabling decoupled, polyglot microservice tool calling. |
| **Edge Security** | BotShield WAF | `Custom v2.0` | In-memory sliding-window rate limiter, honeypots, and scanner drop middleware. |
| **Vector Database** | Qdrant Cloud / Local | `^1.13.0` | High-concurrency HNSW vector search with dense & sparse hybrid payload filtering. |
| **State Persistence** | PostgreSQL / MemorySaver | `16-alpine` | Checkpointing engine saving graph snapshots across multi-turn sessions and HITL interruptions. |
| **Conversational UI** | Streamlit | `^1.42.0` | Interactive web frontend with real-time SSE streaming, product card rendering, and supervisor controls. |
| **Distributed Tracing** | LangSmith | Native | Distributed trace correlation, token accounting, latency profiling, and feedback score tracking. |

---

## ⚖️ Principal Engineer Design Rationale & Trade-Offs

### 1. Model Context Protocol (MCP) vs Hardcoded Python Tool Functions
- **Trade-off**: MCP adds a network transport hop (JSON-RPC over HTTP/SSE), adding ~4–8ms of latency compared to direct in-process function invocation.
- **Architectural Rationale**: In enterprise microservices, catalog and review analytics domains are managed by different teams with distinct deployment lifecycles and security boundaries. Decoupling tools into dedicated FastMCP servers prevents monolithic lock-in, allows independent horizontal scaling, and aligns with emerging multi-vendor agent standards. To mitigate network hiccups, our `MCPClientManager` includes **automatic in-process fallback**.

### 2. Human-in-the-Loop (HITL) Checkpointing vs Autonomous Agent Execution
- **Trade-off**: Halting graph execution introduces asynchronous human latency (seconds to minutes) and requires state persistence storage.
- **Architectural Rationale**: Real-world e-commerce LLMs hallucinate discounts, misunderstand return windows, or can be manipulated by social engineering. Gating financial operations (`request_refund`, `apply_discount > 15%`) behind a stateful checkpoint with supervisor sign-off guarantees 100% financial compliance and auditability.

### 3. Server-Sent Events (SSE) vs WebSockets
- **Trade-off**: SSE is unidirectional (Server ➔ Client), while WebSockets provide full-duplex communication.
- **Architectural Rationale**: For conversational RAG with agentic intermediate status steps, user input is discrete (HTTP POST), while agent response is a continuous stream of tokens and status notifications. SSE operates over standard HTTP/1.1 and HTTP/2, traverses enterprise firewalls and CDNs without stateful socket pinning, supports automatic client reconnection, and reduces connection overhead by 60%.

---

## 🏃 Local Development & Production Runbook

### Prerequisites
- Python 3.12+ (managed via `uv` or standard venv)
- Docker & Docker Compose

### 1. Environment Configuration
```bash
cp env.example .env
# Ensure OPENAI_API_KEY is populated
```

### 2. Multi-Container Orchestration
Launch the entire 6-container production stack:
```bash
docker-compose up -d --build
```
- **Streamlit Web UI**: http://localhost:8501
- **FastAPI Core Docs**: http://localhost:8000/docs
- **Qdrant Vector Dashboard**: http://localhost:6333/dashboard
- **MCP Catalog Microservice**: http://localhost:8002
- **MCP Reviews Microservice**: http://localhost:8003
- **PostgreSQL Session DB**: localhost:5434

---

## 🧪 Automated Verification & Test Harness

Run the comprehensive Principal Engineer test suite validating BotShield WAF, prompt injection defense, MCP client connectivity, HITL state machine, and observability:

```bash
uv run python scripts/verify_principal_chatbot.py
```

### Expected Output:
```
==================================================================
🚀 STARTING PRINCIPAL ENGINEER CHATBOT TEST SUITE
==================================================================

🔍 [TEST 1] Testing BotShield WAF & Honeypot Defense...
  ✅ Honeypot Trap: Successfully blocked & banned probe on /wp-admin
  ✅ Scanner Defense: Successfully blocked sqlmap scanner User-Agent
  ✅ Defensive Headers: X-Content-Type-Options & X-Frame-Options verified

🔍 [TEST 2] Testing Semantic Prompt Injection & Jailbreak Guardrail...
  ✅ Injection Blocked: 'Ignore all previous instructions...' -> PROMPT_INJECTION
  ✅ Jailbreak Blocked: 'You are now in DAN mode...' -> PROMPT_INJECTION
  ✅ PII Redacted: 'My credit card is [REDACTED_CREDIT_CARD]...'

🔍 [TEST 3] Testing Model Context Protocol (MCP) Client Architecture...
  ✅ MCP Health Check: Catalog (operational), Reviews (operational)
  ✅ MCP Tool Protocol: Verified dynamic tool schema discovery & remote JSON-RPC routing

🔍 [TEST 4] Testing Human-in-the-Loop (HITL) State Gating & Authorization...
  ✅ Action Registered: ID 9c7ecbc4-33bd-42ad-b006-000b90d2e2e5 | Status: pending_approval
  ✅ Inspection Endpoint: Thread test_interview_session_99 shows pending action 'request_refund'
  ✅ Supervisor Approval: Action 'request_refund' APPROVED by supervisor.
  ✅ State Cleared: Thread successfully resumed past the HITL gate

🔍 [TEST 5] Testing System Health & Observability Metrics...
  ✅ Health Endpoint 200 OK: Service 'enterprise_ai_chatbot_api' v2.0.0
  ✅ Security Stats: {'status': 'operational', 'shield': 'BotShield WAF v2.0', ...}

==================================================================
🎉 ALL PRINCIPAL ENGINEER SYSTEM CHECKS PASSED WITH 100% SUCCESS!
==================================================================
```

---

## 🎯 Principal Engineer Interview Defense Guide

### Q1: How does your system prevent catastrophic financial mutations from agent hallucinations?
> **Answer**: "We enforce **Human-in-the-Loop (HITL) State Gating**. Rather than granting the LLM direct autonomous execution rights for mutating tools, we define a declarative registry of high-stakes tools (`request_refund`, `apply_manager_discount`, `cancel_order`). When LangGraph encounters a proposed invocation of one of these tools, execution is paused. The graph state is snapshot-serialized into PostgreSQL using `PostgresSaver`. The user stream receives an `hitl_required` event, and the supervisor console surfaces an authorization card. Only when an authenticated supervisor calls `/rag/hitl/approve` does the state engine deserialize and resume execution. The model literally cannot execute financial mutations on its own."

### Q2: Why did you decouple tools into Model Context Protocol (MCP) rather than standard in-process LangChain tools?
> **Answer**: "In enterprise architecture, product catalogs and review analytics are managed by separate domain teams with different SLA, scaling, and deployment profiles. Tightly coupling Python functions into the chatbot API creates a monolithic failure domain. By adopting the **Model Context Protocol (MCP)**, tools are exposed as independent HTTP/JSON-RPC microservices. The agent discovers schemas dynamically at runtime. If the reviews service experiences high load, it can be auto-scaled independently without redeploying the core API. Furthermore, our `MCPClientManager` implements **graceful degradation**: if an external MCP microservice is unreachable, it seamlessly switches to an in-process fallback."

### Q3: How do you defend against prompt injection, jailbreaks, and token-draining attacks?
> **Answer**: "We employ a **Defense-in-Depth** model across the OSI and application stack:
> 1. **Network & Edge**: Our `BotShield WAF Middleware` enforces a sliding-window rate limiter (60 req/min, 8 req/sec burst) to prevent token-draining DDOS. Vulnerability scanners (`sqlmap`, `nikto`) and honeypot probes (`/wp-admin`, `/.env`) trigger automatic 10-minute IP bans.
> 2. **Pre-Flight Semantic Guardrail**: Inbound queries are sanitized via `PromptSecurityGuardrail` before any LLM call, blocking instruction overrides (`'Ignore all previous instructions'`), roleplay exploits (`'DAN mode'`), and exfiltration attempts.
> 3. **Output Sanitization**: All outbound LLM responses pass through regex redaction to prevent accidental leakage of PII, API tokens, or internal database identifiers."

---

## 📄 License
This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.