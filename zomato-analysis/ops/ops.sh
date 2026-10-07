#!/usr/bin/env bash
# ==============================================================================
# Script: ops.sh
# Purpose: Master MLOps, DevOps & Multi-Cloud SRE Operations Hub
# Tier: Principal Cloud Architect & Senior Staff SRE Standard
# Highlights: Terraform (AWS/GCP), Ansible, K8s, Kubeflow, ArgoCD GitOps, Jenkins CI, Multi-Cloud Failover
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR/scripts"

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "========================================================================"
    echo "       ENTERPRISE MLOPS, DEVOPS & MULTI-CLOUD OPERATIONS HUB           "
    echo "========================================================================"
    echo -e "${NC}"
}

show_help() {
    print_header
    echo "Usage: ./ops/ops.sh [command] [options]"
    echo ""
    echo "Core Operations:"
    echo "  cluster             Initialize local Kubernetes cluster via Minikube"
    echo "  kfp-install         Deploy Kubeflow Pipelines standalone onto the cluster"
    echo "  pipeline [mode]     Compile & run Kubeflow pipeline (local or remote)"
    echo "  build [push]        Build container images (pass 'push' for DockerHub)"
    echo "  deploy              Apply Kubernetes manifests & monitor rollout status"
    echo "  compose [up|down]   Manage local Docker Compose stack (App + MLflow)"
    echo "  status              Inspect live Kubernetes pods, services, ingress & cluster health"
    echo ""
    echo "Multi-Cloud & GitOps Production Commands:"
    echo "  tf [cmd]            Manage Terraform multi-cloud IaC (init, plan, apply, validate)"
    echo "  ansible [playbook]  Run Ansible automation (setup, harden, check)"
    echo "  jenkins [up|down]   Run Jenkins LTS CI controller with Docker socket"
    echo "  argocd [sync|status] Trigger declarative GitOps CD sync via ArgoCD CLI"
    echo "  failover [cmd]      Manage Multi-Cloud DR failover (status, probe, failover, simulate)"
    echo "  help                Show this help manual"
    echo ""
    echo "Examples:"
    echo "  ./ops/ops.sh tf plan                 # Preview AWS + GCP multi-cloud infrastructure"
    echo "  ./ops/ops.sh ansible setup           # Provision CI build agent dependencies"
    echo "  ./ops/ops.sh argocd sync             # GitOps CD synchronization with ArgoCD"
    echo "  ./ops/ops.sh failover simulate       # Test Route 53 < 30s automated cloud failover"
    echo "  ./ops/ops.sh jenkins up              # Launch Jenkins CI controller"
    echo ""
}

COMMAND="${1:-help}"
shift || true

case "$COMMAND" in
    cluster|minikube)
        "$SCRIPTS_DIR/setup_minikube.sh" "$@"
        ;;
    kfp-install|kubeflow-install)
        "$SCRIPTS_DIR/install_kubeflow.sh" "$@"
        ;;
    pipeline|kfp|run-pipeline)
        "$SCRIPTS_DIR/run_kubeflow_pipeline.sh" "$@"
        ;;
    build|docker)
        "$SCRIPTS_DIR/build_and_push_docker.sh" "$@"
        ;;
    deploy|k8s)
        "$SCRIPTS_DIR/deploy_k8s.sh" "$@"
        ;;
    compose)
        SUB_CMD="${1:-up}"
        cd "$SCRIPT_DIR/docker"
        if [ "$SUB_CMD" == "down" ]; then
            docker compose down
        else
            docker compose up -d
        fi
        cd "$SCRIPT_DIR"
        ;;
    tf|terraform)
        SUB_CMD="${1:-plan}"
        shift || true
        cd "$SCRIPT_DIR/terraform"
        case "$SUB_CMD" in
            init)     terraform init "$@" ;;
            validate) terraform validate "$@" ;;
            plan)     terraform plan "$@" ;;
            apply)    terraform apply "$@" ;;
            destroy)  terraform destroy "$@" ;;
            fmt)      terraform fmt -recursive "$@" ;;
            *)        terraform "$SUB_CMD" "$@" ;;
        esac
        cd "$SCRIPT_DIR"
        ;;
    ansible)
        SUB_CMD="${1:-check}"
        cd "$SCRIPT_DIR/ansible"
        case "$SUB_CMD" in
            setup)  ansible-playbook -i inventory/hosts.ini playbooks/setup_ci_cd_nodes.yml ;;
            harden) ansible-playbook -i inventory/hosts.ini playbooks/hardening_security.yml ;;
            check)  ansible-playbook -i inventory/hosts.ini playbooks/setup_ci_cd_nodes.yml --syntax-check && \
                    ansible-playbook -i inventory/hosts.ini playbooks/hardening_security.yml --syntax-check ;;
            *)      ansible-playbook -i inventory/hosts.ini "$@" ;;
        esac
        cd "$SCRIPT_DIR"
        ;;
    jenkins)
        SUB_CMD="${1:-up}"
        cd "$SCRIPT_DIR/jenkins"
        if [ "$SUB_CMD" == "down" ]; then
            docker compose -f docker-compose.jenkins.yml down
        elif [ "$SUB_CMD" == "logs" ]; then
            docker compose -f docker-compose.jenkins.yml logs -f
        else
            docker compose -f docker-compose.jenkins.yml up -d
            echo -e "${GREEN}[INFO] Jenkins LTS running at http://localhost:8080/jenkins${NC}"
        fi
        cd "$SCRIPT_DIR"
        ;;
    argocd|cd)
        SUB_CMD="${1:-sync}"
        shift || true
        case "$SUB_CMD" in
            sync)   "$SCRIPT_DIR/argocd/sync_argocd.sh" "$@" ;;
            status) argocd app list || echo "ArgoCD CLI not connected" ;;
            *)      argocd "$SUB_CMD" "$@" ;;
        esac
        ;;
    failover|dr)
        "$SCRIPT_DIR/failover/failover_manager.sh" "$@"
        ;;
    status|ps)
        print_header
        echo -e "${BLUE}[INFO] Inspecting Kubernetes Cluster Status...${NC}\n"
        if command -v kubectl >/dev/null 2>&1; then
            kubectl get pods,svc,ingress,hpa -n mlops-system 2>/dev/null || echo "No active pods in namespace 'mlops-system'."
        else
            echo "kubectl not found."
        fi
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}[ERROR] Unknown command: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac
