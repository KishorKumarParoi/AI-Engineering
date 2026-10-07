# Enterprise MLOps & Kubernetes Operations Hub

Welcome to the **Operations (Ops)** hub of the platform. This module translates the operational blueprints from **Material 5 (Colorectal Cancer Patient Survival Prediction)** into an enterprise-grade, containerized, and orchestrated production infrastructure.

---

## 1. Architectural Highlights

As established in the Material 5 blueprint, this operational framework standardizes four key pillars:
1. **Local Kubernetes Cluster (Minikube)**: Production-identical local Kubernetes orchestration with Docker driver, Ingress controller, and Metrics Server.
2. **Kubeflow Pipelines (KFP)**: Declarative, component-driven DAG orchestrating data preprocessing, Chi-Square feature selection, stratified scaling, GradientBoosting training, and quality gate validation.
3. **Experiment Tracking (DagsHub MLflow)**: Remote experiment logging, parameter tracking, metrics visualization, and model registry on DagsHub.
4. **Production Containerization (DockerHub)**: Multi-stage, lean Docker images for high-throughput model serving and reproducible pipeline execution.

```
+-----------------------------------------------------------------------------------+
|                           MLOPS ORCHESTRATION PIPELINE                            |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [Raw Data (CSV)]                                                                 |
|         |                                                                         |
|         v                                                                         |
|  [KFP Step 1: Preprocessing & Chi2 Selection]                                     |
|         |                                                                         |
|         v                                                                         |
|  [KFP Step 2: Stratified Split & StandardScaler]                                  |
|         |                                                                         |
|         v                                                                         |
|  [KFP Step 3: GradientBoosting Classifier] ----> [DagsHub MLflow (Metrics/Params)]|
|         |                                                                         |
|         v                                                                         |
|  [KFP Step 4: Production Quality Gate]                                            |
|         |                                                                         |
|         +---> [Artifacts (model.pkl / scaler.pkl)]                                |
|                     |                                                             |
|                     v                                                             |
|        [Docker Multi-Stage Build]                                                 |
|                     |                                                             |
|                     v                                                             |
|   [Kubernetes Cluster: Deployment (2 Replicas) + Service + Ingress + HPA]        |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Directory Structure

```
ops/
├── README.md                      # Operational architecture and runbook
├── ops.sh                         # Unified master operations manager CLI
├── docker/
│   ├── Dockerfile.app             # Lean multi-stage runtime for Flask inference app
│   ├── Dockerfile.pipeline        # Container image for Kubeflow pipeline steps
│   ├── .dockerignore
│   └── docker-compose.yml         # Local stack (Serving App + MLflow tracking)
├── kubernetes/
│   ├── 00-namespace.yaml          # Dedicated mlops-system namespace
│   ├── 01-configmap.yaml          # Application and MLflow environment variables
│   ├── 02-secret.yaml             # DagsHub and registry credentials
│   ├── 03-pvc.yaml                # Persistent volume claim for model artifacts
│   ├── 04-deployment.yaml         # Production deployment (2 replicas, rolling updates)
│   ├── 05-service.yaml            # LoadBalancer & ClusterIP definitions
│   ├── 06-ingress.yaml            # NGINX Ingress rules
│   └── 07-hpa.yaml                # Horizontal Pod Autoscaler (CPU/Memory thresholds)
├── kubeflow/
│   ├── __init__.py
│   ├── components.py              # Modular KFP component functions
│   ├── pipeline.py                # Kubeflow DSL pipeline DAG definition
│   ├── compile_pipeline.py        # KFP compiler generating pipeline YAML
│   ├── run_pipeline.py            # Local & remote pipeline executor client
│   └── colorectal_cancer_pipeline.yaml # Compiled Kubeflow workflow specification
└── scripts/
    ├── setup_minikube.sh          # One-click Minikube cluster bootstrapper
    ├── install_kubeflow.sh        # Standalone Kubeflow Pipelines deployer
    ├── build_and_push_docker.sh   # Container build, cache & DockerHub pusher
    ├── deploy_k8s.sh              # Kubernetes manifest applicator and rollout checker
    └── run_kubeflow_pipeline.sh   # Pipeline compiler and executor
```

---

## 3. Operational Commands & Runbook

All lifecycle actions are accessible via `./ops/ops.sh` or the root `./run.sh ops`:

### A. Initialize Local Kubernetes Cluster (Minikube)
```bash
./ops/ops.sh cluster
```
- Provisions Minikube with the Docker driver (4 CPUs, 8GB RAM).
- Automatically enables the `ingress`, `metrics-server`, and `default-storageclass` addons.

### B. Compile and Run the Kubeflow Pipeline
```bash
# Local Execution (Simulates full KFP DAG with real metrics & MLflow logging):
./ops/ops.sh pipeline local

# Remote Cluster Submission (Direct to KFP endpoint):
./ops/ops.sh pipeline remote
```
- Compiles the workflow into `ops/kubeflow/colorectal_cancer_pipeline.yaml`.
- Executes data ingestion, Chi2 selection, standard scaling, and model training.
- Evaluates against the Production Quality Gate (Min Accuracy: 70%, Min F1: 65%).

### C. Build and Push Container Images
```bash
# Build locally and cache into Minikube:
./ops/ops.sh build

# Build and push to DockerHub registry:
./ops/ops.sh build push
```

### D. Deploy to Kubernetes
```bash
./ops/ops.sh deploy
```
- Applies manifests in sequence (`00` through `07`).
- Monitors rolling deployment status.
- Sets up readiness/liveness probes and Horizontal Pod Autoscaler.

### E. Run with Docker Compose
```bash
# Start Flask app and MLflow tracking server locally:
./ops/ops.sh compose up

# Stop services:
./ops/ops.sh compose down
```

### F. Check Cluster Workloads
```bash
./ops/ops.sh status
```

---

## 4. Feature Selection & Model Contract

From the `1. ALL MATERIAL - 5 - NEW` empirical analysis:
- **Target Variable**: `Survival_Prediction` ("Yes" / "No")
- **Top 5 Chi-Square Features Selected**:
  1. `Healthcare_Costs` (Numeric: Total annual medical expenditure)
  2. `Tumor_Size_mm` (Numeric: Primary tumor diameter in millimeters)
  3. `Treatment_Type` (Categorical: 0=Chemotherapy, 1=Combination, 2=Radiotherapy, 3=Surgery)
  4. `Diabetes` (Binary: 0=No, 1=Yes)
  5. `Mortality_Rate_per_100K` (Numeric: Regional mortality metric)
- **Model**: `GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)`
- **Evaluation Gate**: Accuracy >= 0.70, F1 >= 0.65
