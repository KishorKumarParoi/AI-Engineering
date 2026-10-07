# Enterprise Multi-Cloud, GitOps & MLOps Operations Hub

Welcome to the **Operations (Ops)** platform architecture. This production infrastructure unifies the GitOps microservices automation from **Material 9 (Smart Manufacturing / ArgoCD & Jenkins GitOps)** and the MLOps pipeline orchestration from **Material 5 (Kubeflow & DagsHub MLflow)** into an enterprise-grade:

1. **Multi-Cloud High Availability**: AWS EKS (Primary, `us-east-1`) + GCP GKE (Standby DR, `us-central1`).
2. **Automated Multi-Failover Region DNS**: AWS Route 53 active-passive health check routing with sub-30-second RTO.
3. **Continuous Integration (CI)**: Declarative multi-stage Jenkins pipeline (lint, test, multi-arch buildx, Trivy vulnerability scanning, git commit, ArgoCD trigger).
4. **Continuous Delivery (CD)**: Declarative GitOps engine using ArgoCD with the App-of-Apps architectural pattern.
5. **Configuration Management & Hardening**: Ansible playbooks for CI agent provisioning and CIS-benchmark Linux security hardening.
6. **Infrastructure as Code (IaC)**: Modular Terraform for AWS VPC/EKS, GCP VPC/GKE, and Route 53 global routing.
7. **Disaster Recovery (DR) Controller**: Automated health probing, DNS swing, and workload scaling.

---

## 1. Global Multi-Cloud Architecture Topology

```
+-------------------------------------------------------------------------------------------------------+
|                                    GLOBAL INTERNET TRAFFIC                                            |
+-------------------------------------------------------------------------------------------------------+
                                                   |
                                                   v
                         +----------------------------------------------------+
                         |          AWS Route 53 Global Failover DNS          |
                         |            api.zomato-ai.production.internal       |
                         |            Health Checks: 10s Probe / 3 Failures   |
                         +----------------------------------------------------+
                                    |                                  |
               ACTIVE ROUTE (99.99%)|                                  | PASSIVE / FAILOVER (<30s RTO)
                                    v                                  v
+---------------------------------------------+    +---------------------------------------------+
|          PRIMARY CLOUD: AWS (us-east-1)     |    |         FAILOVER CLOUD: GCP (us-central1)   |
+---------------------------------------------+    +---------------------------------------------+
| * Multi-AZ VPC (10.0.0.0/16)                |    | * Custom VPC (10.10.0.0/20)                 |
| * NAT Gateways & Private Subnets            |    | * Secondary Pod CIDR (10.48.0.0/14)         |
| * Application Load Balancer (ALB)           |    | * Secondary Svc CIDR (10.52.0.0/20)         |
|   IP: 52.204.110.82                         |    | * Google Cloud HTTPS Load Balancer          |
| * AWS EKS v1.30 Cluster                     |    |   IP: 34.102.215.19                         |
|   - Managed Node Group (2 - 6 Nodes)        |    | * GCP GKE Failover Cluster                  |
|   - In-Cluster ArgoCD Instance              |    |   - Auto-scaling Node Pool (1 - 5 Nodes)    |
|   - Active Pod Workloads (HPA: 2 - 10 Pods) |    |   - Warm Standby Workloads (2 Pods)         |
+---------------------------------------------+    +---------------------------------------------+
                         ^                                                     ^
                         |                                                     |
                         +--------------------------+--------------------------+
                                                    |
                                    +--------------------------------+
                                    |       ArgoCD GitOps Engine     |
                                    |       (App-of-Apps Pattern)    |
                                    +--------------------------------+
                                                    ^
                                                    | Syncs manifests
                                    +--------------------------------+
                                    |     GitOps Manifest Repo       |
                                    |   (ops/kubernetes/*.yaml)      |
                                    +--------------------------------+
                                                    ^
                                                    | Commits new tags
                                    +--------------------------------+
                                    |     Jenkins CI Pipeline        |
                                    | (Lint, Test, Trivy, Buildx)    |
                                    +--------------------------------+
```

---

## 2. Directory Layout

```
ops/
├── README.md                      # Production architecture & SRE runbook
├── ops.sh                         # Unified Operations Hub CLI
│
├── terraform/                     # Multi-Cloud Infrastructure as Code
│   ├── main.tf                    # Root multi-cloud orchestrator
│   ├── variables.tf               # Input parameter definitions
│   ├── outputs.tf                 # Cluster endpoints, IPs, DNS records
│   ├── terraform.tfvars.example   # Sample credentials configuration
│   └── modules/
│       ├── aws_eks/               # AWS Multi-AZ VPC, EKS Cluster, Node Groups
│       ├── gcp_gke/               # GCP Custom VPC, GKE Cluster, Workload Identity
│       └── global_failover_dns/   # Route 53 Health Checks & Active-Passive DNS
│
├── ansible/                       # Configuration Management & OS Hardening
│   ├── ansible.cfg                # Optimized execution, pipelining, SSH multiplexing
│   ├── inventory/
│   │   └── hosts.ini              # CI masters, build agents, and k8s bastions
│   └── playbooks/
│       ├── setup_ci_cd_nodes.yml  # Docker, containerd, OpenJDK 17, kubectl, argocd, trivy
│       └── hardening_security.yml # Sysctl tuning, UFW firewall, Fail2ban, SSH lock-down
│
├── argocd/                        # Declarative GitOps Continuous Delivery
│   ├── projects/
│   │   └── project.yaml           # AppProject with RBAC and multi-cluster perimeters
│   ├── applications/
│   │   ├── root-app-of-apps.yaml  # ArgoCD Root App-of-Apps orchestrator
│   │   ├── zomato-prod-aws.yaml   # AWS EKS Primary deployment application
│   │   └── zomato-dr-gcp.yaml     # GCP GKE Standby DR application
│   └── sync_argocd.sh             # Production CLI synchronization & rollback runner
│
├── jenkins/                       # Enterprise Continuous Integration (CI)
│   ├── Jenkinsfile                # 8-stage declarative pipeline (lint, test, buildx, Trivy, gitops)
│   └── docker-compose.jenkins.yml # Jenkins LTS controller with Docker-out-of-Docker socket
│
├── failover/                      # Disaster Recovery & Traffic Orchestration
│   └── failover_manager.sh        # Health probe, Route 53 DNS swing, workload scaler (<30s RTO)
│
├── kubernetes/                    # Multi-Cluster Production Manifests
│   ├── 00-namespace.yaml          # Dedicated workload namespace
│   ├── 01-configmap.yaml          # Environmental configuration
│   ├── 02-secret.yaml             # Credentials and registry tokens
│   ├── 03-pvc.yaml                # Persistent volume claims
│   ├── 04-deployment.yaml         # Multi-replica deployment with rolling updates
│   ├── 05-service.yaml            # LoadBalancer & ClusterIP definitions
│   ├── 06-ingress.yaml            # Ingress rules with TLS termination
│   └── 07-hpa.yaml                # Horizontal Pod Autoscaler (CPU/Memory thresholds)
│
├── kubeflow/                      # MLOps Pipeline Orchestration
│   ├── components.py              # Modular KFP components
│   ├── pipeline.py                # Kubeflow DSL DAG definition
│   ├── compile_pipeline.py        # Compiles pipeline YAML
│   ├── run_pipeline.py            # Local & remote KFP runner
│   └── colorectal_cancer_pipeline.yaml # Compiled Kubeflow workflow
│
├── docker/                        # Containerization Runtimes
│   ├── Dockerfile.app             # Inference runtime
│   ├── Dockerfile.pipeline        # Kubeflow execution image
│   └── docker-compose.yml         # Local stack (Serving App + MLflow tracking)
│
└── scripts/                       # Local Kubernetes & Kubeflow bootstrap utilities
    ├── setup_minikube.sh          # Minikube cluster bootstrapper
    ├── install_kubeflow.sh        # Standalone Kubeflow Pipelines installer
    ├── build_and_push_docker.sh   # Container build & registry push
    ├── deploy_k8s.sh              # Manifest rollout applicator
    └── run_kubeflow_pipeline.sh   # Local KFP execution client
```

---

## 3. Production Operational Runbook

All workflows can be executed directly via `./ops/ops.sh` or through the root `./run.sh ops`:

### A. Infrastructure as Code (Terraform)
```bash
# 1. Preview multi-cloud resources:
./ops/ops.sh tf plan

# 2. Validate HCL syntax and provider configurations:
./ops/ops.sh tf validate

# 3. Provision AWS EKS, GCP GKE, and Route 53:
./ops/ops.sh tf apply -auto-approve
```

### B. Configuration Management & OS Hardening (Ansible)
```bash
# 1. Verify syntax of all Ansible playbooks:
./ops/ops.sh ansible check

# 2. Provision build agents (Docker, Java 17, kubectl, Helm, ArgoCD, Trivy):
./ops/ops.sh ansible setup

# 3. Apply Linux security hardening (Sysctl, UFW, Fail2ban, SSH limits):
./ops/ops.sh ansible harden
```

### C. Continuous Delivery (ArgoCD GitOps)
```bash
# 1. Trigger GitOps sync for AWS Primary:
./ops/ops.sh argocd sync zomato-prod-aws

# 2. Trigger GitOps sync for GCP Standby DR:
./ops/ops.sh argocd sync zomato-dr-gcp

# 3. View live application sync and health status:
./ops/ops.sh argocd status
```

### D. Continuous Integration (Jenkins CI)
```bash
# 1. Launch local Jenkins LTS controller:
./ops/ops.sh jenkins up

# 2. Stream controller logs:
./ops/ops.sh jenkins logs

# 3. Stop Jenkins controller:
./ops/ops.sh jenkins down
```

### E. Multi-Cloud Disaster Recovery & Failover Controller
```bash
# 1. Inspect live health across AWS and GCP:
./ops/ops.sh failover status

# 2. Probe HTTP status and response latency:
./ops/ops.sh failover probe

# 3. Simulate regional outage (< 30s automated DNS failover):
./ops/ops.sh failover simulate

# 4. Execute manual emergency failover to GCP GKE:
./ops/ops.sh failover failover

# 5. Restore primary routing once AWS recovers:
./ops/ops.sh failover failback
```

### F. MLOps & Local Kubernetes Workloads
```bash
# 1. Launch local Minikube cluster:
./ops/ops.sh cluster

# 2. Run Kubeflow pipeline locally:
./ops/ops.sh pipeline local

# 3. Deploy Kubernetes manifests:
./ops/ops.sh deploy

# 4. View Kubernetes pods and HPA:
./ops/ops.sh status
```

---

## 4. Key Performance Indicators & SRE Metrics

- **Recovery Time Objective (RTO)**: < 30 seconds via Route 53 health check TTL and automated failover routing.
- **Recovery Point Objective (RPO)**: Near-Zero (< 1 second) via GitOps source of truth and distributed multi-region state.
- **Vulnerability SLA**: Trivy gate blocks container images containing any CRITICAL CVEs with known vendor fixes.
- **Autoscaling Response**: AWS HPA scales pods between 2 and 10 replicas when average CPU utilization exceeds 75%.
