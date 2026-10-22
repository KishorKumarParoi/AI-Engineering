# 🏛️ Enterprise System Architecture & Design Specification

## 1. Architectural Philosophy & C4 Model

The **Enterprise Autonomous AI Production Chatbot Platform** is designed for high-availability, mission-critical e-commerce operations. It rejects monolithic script designs in favor of **Decoupled Microservices**, **Polyglot Model Context Protocol (MCP)** tool execution, **LangGraph Finite State Machines (FSM)**, and **Zero-Trust Edge Security**.

### C4 Container Model

```mermaid
graph TD
    User([Enterprise Customer / User]) -->|HTTPS / SSE| Cloudflare[Cloudflare CDN & Edge DDoS]
    Cloudflare -->|Port 8501| UIContainer[Streamlit Web UI Container]
    Cloudflare -->|Port 8000| APIContainer[FastAPI Core Orchestrator]

    subgraph Security Boundary [BotShield WAF & Guardrails]
        APIContainer --> WAF[BotShield Middleware: Rate Limiter & Honeypots]
        WAF --> Guardrail[PromptSecurityGuardrail: Anti-Jailbreak & PII Redaction]
    end

    subgraph State & Orchestration [LangGraph Cyclic Engine]
        Guardrail --> IntentNode[Intent Router Agent]
        IntentNode --> QueryExpand[Query Decomposition Node]
        QueryExpand --> AgentNode[Planning & Reasoning Agent]
        AgentNode --> AggregatorNode[Aggregator & Synthesis Node]
    end

    subgraph MCP Microservice Ecosystem [Model Context Protocol]
        AgentNode -->|MCP JSON-RPC / HTTP :8002| MCPCatalog[MCP Server: Product Catalog]
        AgentNode -->|MCP JSON-RPC / HTTP :8003| MCPReviews[MCP Server: Customer Reviews]
    end

    subgraph Data & Persistence Tier
        MCPCatalog -->|Vector & Payload Query| Qdrant[(Qdrant Vector Database: HNSW Index)]
        MCPReviews -->|Filtered Text Search| Qdrant
        APIContainer -->|Session Checkpoint / HITL State| Postgres[(PostgreSQL 16 Checkpointer)]
    end

    subgraph HITL Governance Tier
        AgentNode -.->|High-Stakes Mutation| HITLGate{HITL Checkpoint Gate}
        HITLGate -->|Execution Suspended| Supervisor([Human Supervisor / Tier-2 Agent])
        Supervisor -->|POST /rag/hitl/approve| APIContainer
    end
```

---

## 2. LangGraph Stateful Execution Flow

The core reasoning engine is modeled as a stateful, cyclic directed graph using LangGraph:

```mermaid
stateDiagram-v2
    [*] --> InboundRequest
    InboundRequest --> BotShieldWAF: Validate IP & User-Agent
    BotShieldWAF --> PromptGuardrail: Evaluate Semantic Threat
    
    state PromptGuardrail {
        [*] --> CheckJailbreak
        CheckJailbreak --> ThreatDetected: Match Override Pattern
        CheckJailbreak --> SanitizePII: Clean Input
        SanitizePII --> [*]
    }
    
    PromptGuardrail --> IntentRouter: Clean Query
    ThreatDetected --> TerminateWithAlert: 403 / Security Event

    state IntentRouter {
        [*] --> ClassifyIntent
        ClassifyIntent --> DirectFAQ: General Inquiries
        ClassifyIntent --> TechnicalSearch: Product / Comparison
        ClassifyIntent --> SensitiveMutation: Refund / Discount / Cancel
    }

    DirectFAQ --> DirectSynthesis
    SensitiveMutation --> HITL_Gate: Register Pending Action
    HITL_Gate --> AwaitingSupervisor: Yield SSE hitl_required
    
    TechnicalSearch --> QueryDecomposition: Complex Multi-Product Prompt
    QueryDecomposition --> ParallelMCPRetriever: Fan-Out Sub-Queries
    ParallelMCPRetriever --> AggregatorNode: Reciprocal Rank Fusion
    AggregatorNode --> DirectSynthesis
    
    DirectSynthesis --> StreamSSEToClient: Emit Tokens & Context
    StreamSSEToClient --> [*]
```

---

## 3. Model Context Protocol (MCP) Transport Specification

Tools are not hardcoded inside the orchestrator; they are managed as independent FastMCP microservices adhering to the Anthropic Model Context Protocol standard:

```mermaid
sequenceDiagram
    autonumber
    actor User as User Browser
    participant API as FastAPI Core Orchestrator
    participant MCP_Mgr as MCP Client Manager
    participant MCP_Cat as FastMCP Catalog (:8002)
    participant Qdrant as Qdrant Vector DB

    User->>API: POST /rag (Query: "Best noise canceling headphones")
    API->>API: BotShield WAF & Prompt Validation
    API->>MCP_Mgr: Dispatch Tool Call (get_formatted_context)
    
    alt Remote MCP Microservice Online
        MCP_Mgr->>MCP_Cat: POST /tools/get_formatted_context (JSON-RPC)
        MCP_Cat->>Qdrant: Hybrid Search (Dense Cosine + Payload Filter)
        Qdrant-->>MCP_Cat: Top-5 Matching Point Structs
        MCP_Cat-->>MCP_Mgr: Formatted Inventory Payload
    else Microservice Failure / Network Timeout
        MCP_Mgr->>MCP_Mgr: Trigger Graceful Fallback Mode
        MCP_Mgr->>Qdrant: Direct In-Process Vector Query
        Qdrant-->>MCP_Mgr: Top-5 Matching Chunks
    end

    MCP_Mgr-->>API: Standardized Context Response
    API->>User: SSE Stream (Tokens + Product Metadata Cards)
```

---

## 4. Human-in-the-Loop (HITL) Checkpoint Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Customer as E-commerce Customer
    participant API as FastAPI Orchestrator
    participant Graph as LangGraph Engine
    participant DB as PostgreSQL State Saver
    actor Supervisor as Human Supervisor (Console)

    Customer->>API: "I want a refund of $89.99 for order ORD-9482"
    API->>Graph: Initialize Stream
    Graph->>Graph: Identify Tool: request_refund
    Graph->>Graph: Intercept High-Consequence Action (HITL Trigger)
    Graph->>DB: Checkpoint Thread State (Status: PENDING_APPROVAL)
    Graph-->>API: Emit hitl_required Event
    API-->>Customer: SSE Event: Action Gated for Supervisor Review
    
    Note over Supervisor: Supervisor Console detects pending action
    Supervisor->>API: GET /rag/hitl/pending/{thread_id}
    API-->>Supervisor: Return Pending Action Details ($89.99, Reason)
    
    Supervisor->>API: POST /rag/hitl/approve (decision="approved")
    API->>DB: Retrieve Checkpointed State
    API->>Graph: Resume Thread Execution with Authorized Token
    Graph->>Graph: Execute Transaction & Update Audit Log
    Graph-->>API: Final Synthesis
    API-->>Customer: "Your refund of $89.99 has been authorized."
```

---

## 5. Security & Threat Mitigation Architecture

```
Layer 1: Network & Edge Security (BotShield WAF)
├── Honeypot Endpoint Traps (/.env, /.git, /wp-admin) -> Immediate 600s Ban
├── Automated Scanner Drops (sqlmap, nikto, wpscan, nmap User-Agents)
└── Sliding-Window Rate Limiter (60 req/min per IP, 8 req/sec burst limit)

Layer 2: Pre-Flight Guardrails (PromptSecurityGuardrail)
├── Adversarial Regex Interception (DAN, Jailbreaks, Instruction Overrides)
├── Delimiter Evasion Defense (### System, [INST], <system> tags)
└── PII & Secrets Redaction (Credit Cards, SSNs, API Key Regex)

Layer 3: Application Runtime Governance (HITL)
├── Sensitive Action Detection (Refunds, Discounts > 15%, Order Cancellations)
├── State Checkpoint Serialization (PostgreSQL 16)
└── Authenticated Dual-Key Supervisor Sign-Off
```

---

## 6. Latency Budget & SLA Profile

| Processing Phase | Target Latency | P95 Latency | Architectural Optimization |
| :--- | :--- | :--- | :--- |
| **BotShield WAF Evaluation** | `< 1 ms` | `2 ms` | In-memory hash set lookup & compiled regexes. |
| **Prompt Guardrail & PII Scan** | `< 3 ms` | `5 ms` | Pre-compiled regex patterns before LLM network calls. |
| **Intent Classification Node** | `180 ms` | `320 ms` | Compact `gpt-4.1-mini` with Pydantic structured output. |
| **Qdrant Vector Retrieval** | `15 ms` | `35 ms` | HNSW indexed search with memory payload caching. |
| **MCP Tool Network Round-Trip** | `25 ms` | `45 ms` | Keep-alive HTTP connection pooling via `httpx`. |
| **First Token Latency (TTFT)** | `420 ms` | `750 ms` | Server-Sent Events (SSE) streaming direct to client. |
| **Total Pipeline Completion** | `1200 ms` | `2400 ms` | Parallel sub-query decomposition and fusion. |
