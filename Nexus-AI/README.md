<div align="center">

# ⚡ Nexus-AI

### Enterprise Multi-Cloud Lakehouse + MLOps + AI Agent Mesh

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=next.js&logoColor=white)](https://nextjs.org)
[![Go](https://img.shields.io/badge/Go-1.22-00ADD8?logo=go&logoColor=white)](https://go.dev)
[![Terraform](https://img.shields.io/badge/Terraform-Multi--Cloud-7B42BC?logo=terraform&logoColor=white)](https://terraform.io)
[![K8s](https://img.shields.io/badge/Kubernetes-GPU-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**One-click deployment** of a production-grade AI platform spanning ETL pipelines, ML training, autonomous agent mesh, multi-cloud infrastructure, and a premium dashboard — all from a single `./run_all.sh` command.

</div>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        NEXUS-AI PLATFORM                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │  📊 Data     │  │  💡 Analyst │  │  🤖 MLOps   │  │  🛡️ Security │  │
│  │  Agent       │  │  Agent      │  │  Agent       │  │  Agent       │  │
│  │  (NL2SQL)    │  │  (BI/KPIs)  │  │  (Health)    │  │  (OWASP)     │  │
│  └──────┬───────┘  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  │
│         └────────────────┬┴────────────────┴─────────────────┘          │
│                    ┌─────▼──────┐                                        │
│                    │ Orchestrator│  ← Security-First Pipeline            │
│                    └─────┬──────┘                                        │
│         ┌────────────────┼────────────────┐                              │
│    ┌────▼─────┐   ┌──────▼──────┐   ┌─────▼────┐                       │
│    │ Go GW    │   │  FastAPI    │   │  Express  │                       │
│    │ :3000    │   │  :8081      │   │  BFF :3003│                       │
│    └────┬─────┘   └─────────────┘   └──────────┘                       │
│         │                                                                │
│    ┌────▼────────────────────────────────────────┐                      │
│    │           Next.js 16 Dashboard :3001        │                      │
│    │  [Overview] [Agents] [MLOps] [Data] [Security]                    │
│    └─────────────────────────────────────────────┘                      │
├─────────────────────────────────────────────────────────────────────────┤
│  Infra: Terraform (GCP/AWS/Azure) │ K8s + Helm │ GPU │ Multi-Region   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

```bash
# Clone and run — one command does everything
git clone https://github.com/nexus-ai/nexus-ai.git
cd nexus-ai

# One-click: Generate data → ETL → Train ML → Start Agents → Launch Dashboard
./run_all.sh --demo
```

### What happens:
| Step | Phase | Description | Time |
|:---:|:---|:---|:---:|
| 1 | Pre-flight | Check Python 3.12, Node.js, Docker | ~2s |
| 2 | Dependencies | Create venv, install packages | ~15s |
| 3 | Data Gen | 10,000 orders, 100 restaurants, 200 riders | ~5s |
| 4 | ETL Pipeline | Bronze → Silver → Gold (Medallion) | ~8s |
| 5 | ML Training | GradientBoosting, R²=0.954, Prometheus export | ~12s |
| 6 | Observability | Prometheus + Grafana + MLflow (Docker) | ~10s |
| 7 | Agent Mesh | 5-agent demo with 12 queries | ~5s |
| 8 | Web Stack | FastAPI :8081 + Next.js :3001 | ~5s |

**Total boot time: ~60 seconds**

---

## 📁 Project Structure

```
Nexus-AI/
├── run_all.sh                    # One-click master launcher
├── Dockerfile                    # Multi-stage production build
├── docker-compose.yml            # 11-service local stack
│
├── data/
│   ├── generators/               # Synthetic data (Zomato-inspired)
│   │   └── seed_all.py           # 5-table generator
│   ├── schemas/                  # JSON schemas
│   ├── raw/                      # CSVs (generated)
│   ├── bronze/                   # Raw Parquet (ingested)
│   ├── silver/                   # Cleaned + validated
│   └── gold/                     # Analytics-ready + feature store
│
├── etl/
│   ├── pipeline.py               # Medallion orchestrator
│   ├── bronze/ingest.py          # CSV → Parquet ingestion
│   ├── silver/quality_checks.py  # 32-point DQ validation
│   ├── gold/dimensions.py        # Star schema dimensions
│   ├── gold/facts.py             # Fact tables + marts
│   ├── gold/features.py          # ML feature engineering
│   └── storage/__init__.py       # Multi-cloud storage adapter
│
├── mlops/
│   ├── train.py                  # Automated training pipeline
│   ├── predict.py                # FastAPI inference server
│   ├── drift.py                  # PSI drift detector
│   └── metrics_exporter.py       # 12 Prometheus metrics
│
├── agents/
│   ├── orchestrator.py           # Security-first mesh router
│   ├── agent_1_data/agent.py     # NL2SQL + DuckDB
│   ├── agent_2_analyst/agent.py  # BI + KPIs + strategy
│   ├── agent_3_mlops/agent.py    # Model health supervisor
│   ├── agent_4_security/agent.py # OWASP LLM firewall
│   └── agent_5_voice/agent.py    # Multi-channel notifications
│
├── backend/
│   ├── gateway/main.go           # Go API gateway (JWT, rate limit)
│   └── services/express-bff/     # Node.js BFF
│
├── frontend/                     # Next.js 16 (TypeScript)
│   └── src/app/
│       ├── page.tsx              # 5-tab glassmorphism dashboard
│       ├── layout.tsx            # Root layout + SEO
│       └── globals.css           # Design system
│
├── terraform/
│   ├── main.tf                   # Multi-cloud orchestrator
│   ├── environments/prod.tfvars  # Production config
│   └── modules/
│       ├── gcp/main.tf           # GCS + BigQuery + GKE + GPU
│       ├── aws/main.tf           # S3 + Glue + EKS + GPU
│       ├── azure/main.tf         # ADLS + Synapse + AKS + GPU
│       └── monitoring/main.tf    # kube-prometheus-stack
│
├── k8s/
│   ├── deployments/              # Inference + CronJobs
│   ├── gpu/                      # T4 GPU deployment
│   ├── helm/nexus-ai/            # Helm chart
│   ├── failover/                 # Multi-region GCP↔AWS
│   └── base/network-policies/    # Zero-trust policies
│
├── infra/
│   ├── prometheus/               # Scrape config + alert rules
│   └── grafana/                  # Auto-provisioned datasources
│
├── scripts/
│   └── smoke_test.sh             # 35+ E2E tests
│
└── docs/
    └── SECURITY_COMPLIANCE.md    # OWASP + SOC2 + GDPR
```

---

## 🧪 Key Features

### 📊 Medallion ETL Pipeline
- **Bronze**: CSV → Parquet ingestion with schema validation
- **Silver**: 32-point data quality checks (null rates, type casts, dedup)
- **Gold**: Star schema (dims + facts + marts) + ML feature store
- **Multi-cloud**: Pluggable storage adapter (Local / GCS / S3 / ADLS)

### 🤖 MLOps Pipeline
- **Training**: GradientBoostingRegressor with hyperparameter tuning
- **Metrics**: R²=0.954, MAE=2.6 min, 86.5% within 5-minute accuracy
- **Monitoring**: 12 Prometheus metrics + 9-panel Grafana dashboard
- **Drift**: PSI-based feature drift detection with auto-alert thresholds

### 🧠 5-Agent AI Mesh
| Agent | Purpose | Key Capability |
|:---|:---|:---|
| Data Agent | NL2SQL queries | Schema-aware, read-only, keyword routing |
| Analyst Agent | Business intelligence | Executive briefs, KPIs, recommendations |
| MLOps Agent | Model health | R²/RMSE/PSI monitoring, retrain advisor |
| Security Agent | OWASP LLM firewall | 12+ injection sigs, 8 PII types |
| Voice Agent | Notifications | Email, Slack, WhatsApp, n8n webhooks |

### 🛡️ Security
- OWASP LLM Top 10: 8/10 covered
- PII Detection: Email, Phone, Aadhaar, PAN, SSN, Credit Card
- Zero-trust K8s network policies
- JWT authentication + rate limiting

### ☁️ Multi-Cloud Infrastructure
| Cloud | Storage | Analytics | Compute | Registry |
|:---|:---|:---|:---|:---|
| **GCP** | GCS | BigQuery | GKE + T4 GPU | Artifact Registry |
| **AWS** | S3 | Glue + Athena | EKS + g4dn GPU | ECR |
| **Azure** | ADLS Gen2 | Synapse | AKS + NC T4 GPU | ACR |

---

## 🛠️ Commands

```bash
# Full demo with narration
./run_all.sh --demo

# Quick local run (small data)
./run_all.sh --mode=local --scale=0.1

# Cloud deployment
./run_all.sh --mode=cloud --provider=gcp

# Run smoke tests
./scripts/smoke_test.sh

# Docker Compose
docker compose up -d                    # All services
docker compose --profile gpu up -d      # With GPU inference

# Terraform
cd terraform
terraform plan -var-file=environments/prod.tfvars
terraform apply -auto-approve

# Helm
helm install nexus-ai ./k8s/helm/nexus-ai -n nexus-ai --create-namespace
```

---

## 📊 Tech Stack

| Layer | Technologies |
|:---|:---|
| **Data** | Python, Pandas, DuckDB, PyArrow, Parquet |
| **ML** | scikit-learn, joblib, Prometheus, Grafana |
| **Agents** | Custom mesh (no LangChain), regex NLP, DuckDB |
| **Backend** | Go (net/http), Express.js, FastAPI, Uvicorn |
| **Frontend** | Next.js 16, TypeScript, CSS (glassmorphism) |
| **Infra** | Terraform, Docker, Kubernetes, Helm |
| **Cloud** | GCP, AWS, Azure (pluggable) |
| **Security** | OWASP, JWT, RBAC, Network Policies |

---

## 📈 Metrics

| Metric | Value |
|:---|:---|
| Lines of Code | 10,855+ |
| Python Files | 55 |
| Terraform Files | 7 |
| K8s/Docker Files | 21 |
| Test Coverage | 35+ E2E tests |
| Model R² Score | 0.9542 |
| Prediction Accuracy | 86.5% within 5 min |
| Agent Mesh Queries | 12/12 pass |
| OWASP Coverage | 8/10 |
| Boot Time | ~60 seconds |

---

<div align="center">

**Built with ⚡ by the Nexus-AI Team**

*One-click. Multi-cloud. Enterprise-grade.*

</div>
