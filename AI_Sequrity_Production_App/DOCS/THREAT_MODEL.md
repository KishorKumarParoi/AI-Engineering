# 🛡️ Enterprise AI Security & Threat Model (STRIDE + OWASP Top 10 for LLMs)

## 1. System Scope & Architecture Overview
The Enterprise AI Security Production Application operates an autonomous multi-agent SecOps system utilizing FastAPI, NVIDIA NeMo Guardrails, BotShield ASGI WAF, Qdrant Vector Store, Dual-Tier FlashRank/Cohere Re-Ranking, and LangGraph Supervisor.

### Trust Boundaries
1. **TB-1: Public Internet / User Ingestion Boundary**: Gated by BotShield WAF, Cloudflare/AWS SG, and PII Tokenizer.
2. **TB-2: Application / Guardrail Runtime**: Gated by NVIDIA NeMo Guardrails and Prompt Injection Shield.
3. **TB-3: Orchestration / Agent Execution Core**: Isolated LangGraph state machine and thread session memory.
4. **TB-4: External Integrations / Microservices**: Model Context Protocol (FastMCP) and encrypted HTTPS outbound tools (Tavily, Cohere, Groq).

---

## 2. Threat Modeling Matrix (OWASP Top 10 for LLMs 2025)

| Threat ID | Threat Vector | STRIDE Category | Threat Description | Architectural Mitigation | Residual Risk |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **LLM01** | **Direct & Indirect Prompt Injection** | Tampering / Elevation of Privilege | Adversary supplies input designed to override system instructions or hijack agent tools. | Delimiter stripping, heuristic signatures, and NVIDIA NeMo Guardrails Colang rails. | **LOW** |
| **LLM02** | **Insecure Output Handling** | Tampering | Agent response contains unescaped malicious JavaScript, SQL injection, or shell script. | Output sanitization, strict Pydantic JSON schemas, and BotShield injection filters. | **LOW** |
| **LLM03** | **Training Data Poisoning / Knowledge Corruption** | Tampering | Adversary manipulates retrieved enterprise policies or web search feeds. | Dual-Tier Re-Ranking (FlashRank ONNX + Cohere cross-attention) and strict score cutoffs. | **LOW** |
| **LLM04** | **Model Denial of Service (DoS)** | Denial of Service | Adversary floods endpoints with expensive, resource-heavy recursive queries. | Sliding-window IP rate limiter (60 rpm, 5 burst/s) and Portkey semantic cache (<50ms). | **LOW** |
| **LLM05** | **Supply Chain Vulnerabilities** | Tampering | Compromised third-party Python packages or external model endpoints. | Pinned dependency locks (`uv.lock`), minimal base images (`python:3.12-slim`), non-root container users. | **LOW** |
| **LLM06** | **Excessive Agency** | Elevation of Privilege | Autonomous agent executes unauthorized destructive infrastructure mutations. | Cryptographic Human-in-the-Loop (HITL) break-glass approval gates on all mutating actions. | **NEGLIGIBLE** |
| **LLM07** | **System Prompt & Secret Leakage** | Information Disclosure | Inbound prompt tricks model into echoing initial system prompt or API credentials. | Colang policy rails forbidding prompt disclosure; PII filter detecting API key patterns. | **LOW** |
| **LLM08** | **Vector & Embedding Inversion** | Information Disclosure | Adversary reconstructs raw policy documents from vector distance queries. | Strict tenant isolation via Qdrant collection payloads and session thread IDs. | **LOW** |
| **LLM09** | **Misinformation & Hallucination** | Repudiation | Model invents non-existent security CVEs or generates invalid compliance advice. | G-Eval Faithfulness CoT scoring and loop engineering self-correction cycles. | **LOW** |
| **LLM10** | **Unbounded Consumption & Token Spikes** | Denial of Service | Token generation loops exhausting API budget or crashing memory. | Hard token generation caps (`max_tokens=2000`) and loop max iterations ($N=3$). | **NEGLIGIBLE** |

---

## 3. STRIDE Threat Analysis

### 1. Spoofing
- **Threat**: Malicious actor impersonates authorized security supervisor.
- **Mitigation**: Bearer token authorization, thread ID cryptographic validation, and admin signing for HITL approvals.

### 2. Tampering
- **Threat**: In-flight modification of retrieved security policies or agent state.
- **Mitigation**: End-to-end TLS 1.3 encryption, immutable LangGraph state transitions, SHA-256 payload checksums.

### 3. Repudiation
- **Threat**: User denies submitting an adversarial prompt or an admin denies approving a critical patch.
- **Mitigation**: Immutable Logfire OpenTelemetry audit logs, structured JSON access logs, and persistent HITL approval state.

### 4. Information Disclosure
- **Threat**: Accidental output echo of client PII (SSNs, credit cards) or backend API keys (`sk-...`, `AKIA...`).
- **Mitigation**: Bidirectional PII filter engine with Luhn verification, secret regex scanners, and automated output detokenization.

### 5. Denial of Service
- **Threat**: Scrapers and botnets overwhelming backend inference capacity.
- **Mitigation**: BotShield ASGI WAF with honeypot traps (`/.env`, `/wp-admin`) triggering automated 10-minute IP bans.

### 6. Elevation of Privilege
- **Threat**: Agent sub-process attempting shell breakout or host filesystem read.
- **Mitigation**: Docker container runs as unprivileged user `appuser` (UID 1000); read-only root filesystems where applicable.
