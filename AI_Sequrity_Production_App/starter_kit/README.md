# 🚀 Enterprise AI Platform Starter Kit

## Overview
The **Enterprise AI Platform Starter Kit** provides a standardized, battle-tested golden path for engineering, deploying, and governing production AI microservices. Aligned with the **Enterprise AI Architect Roadmap (Phases 0 - 5)**, this repository equips engineering teams with zero-configuration security, distributed event patterns, evaluation harnesses, and cloud automation.

---

## 🏗️ Architecture Blueprint
- **Phase 0 (Setup)**: FastAPI, Uvicorn, Docker, CI/CD, Makefile, non-root container user, strict P95 latency SLOs (<2,000ms).
- **Phase 1 (Core ML)**: Algorithmic foundations, experiment tracking, fast inference packaging.
- **Phase 2 (Data & MLOps)**: Delta Medallion Lakehouse (Bronze/Silver/Gold), Feast shared feature store, streaming SLAs (<50ms online, <60s silver).
- **Phase 3 (GenAI & LLMOps)**: Dual-Tier Hybrid Re-ranking (FlashRank ONNX + Cohere v3.5 RRF), NVIDIA NeMo Guardrails, BotShield ASGI WAF, G-Eval Chain-of-Thought evaluation harness.
- **Phase 4 (Distributed Patterns)**: Transactional Outbox pattern with idempotency keys, CQRS Command/Query separation, Saga distributed compensations.
- **Phase 5 (Governance & Platform)**: ISO 27001 / SOC 2 control mappings, GDPR Article 35 DPIA generator, Model Cards, and single-command AWS EC2 deploy (`./deploy.sh`) and teardown (`./clear.sh`).

---

## ⚡ Quickstart

### 1. Local Development
```bash
# Setup dependencies
make install

# Run local backend (:8000) and Streamlit dashboard (:8501)
make run-local
```

### 2. Run G-Eval Automated Quality Audit
```bash
make eval
```

### 3. Verify ISO 27001 & SOC 2 Compliance
```bash
make audit
```

### 4. Single-Command Cloud Deployment
```bash
make deploy
```

### 5. Zero-Cost Cloud Teardown ($0.00 AWS Bill)
```bash
make teardown
```
