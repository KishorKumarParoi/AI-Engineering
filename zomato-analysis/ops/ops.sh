#!/usr/bin/env bash
# ==============================================================================
# Script: ops.sh
# Purpose: Master MLOps & DevOps Operational Lifecycle Manager
# Tier: Senior Staff MLOps & Platform Engineer Standard
# Highlights: Minikube + Kubeflow + DockerHub + Kubernetes Manifests + MLflow
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
    echo "=========================================================="
    echo "       ENTERPRISE MLOPS & KUBERNETES OPERATIONS HUB       "
    echo "=========================================================="
    echo -e "${NC}"
}

show_help() {
    print_header
    echo "Usage: ./ops/ops.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  cluster             Initialize local Kubernetes cluster via Minikube"
    echo "  kfp-install         Deploy Kubeflow Pipelines standalone onto the cluster"
    echo "  pipeline [mode]     Compile & run Kubeflow pipeline (modes: local (default), remote)"
    echo "  build [push]        Build container images for App & Pipeline (pass 'push' for DockerHub)"
    echo "  deploy              Apply Kubernetes manifests & monitor rollout status"
    echo "  compose [up|down]   Manage local Docker Compose stack (App + MLflow)"
    echo "  status              Inspect live Kubernetes pods, services, ingress & cluster health"
    echo "  help                Show this help manual"
    echo ""
    echo "Examples:"
    echo "  ./ops/ops.sh cluster           # Launch Minikube cluster"
    echo "  ./ops/ops.sh pipeline          # Run end-to-end Kubeflow pipeline locally"
    echo "  ./ops/ops.sh build push        # Build & push images to DockerHub"
    echo "  ./ops/ops.sh deploy            # Deploy to Kubernetes cluster"
    echo "  ./ops/ops.sh status            # View cluster status"
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
