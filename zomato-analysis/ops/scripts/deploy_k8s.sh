#!/usr/bin/env bash
# ==============================================================================
# Script: deploy_k8s.sh
# Purpose: Deploys all Kubernetes manifests for Colorectal Cancer Survival Serving
# Highlights from Material 5: Kubernetes Cluster + Deployments + Services + Ingress
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
K8S_DIR="$OPS_DIR/kubernetes"
NAMESPACE="mlops-system"

echo -e "${BLUE}${BOLD}"
echo "=========================================================="
echo "      KUBERNETES MANIFEST DEPLOYMENT & ROLLOUT ENGINE     "
echo "=========================================================="
echo -e "${NC}"

if ! command -v kubectl >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] kubectl CLI not found.${NC}"
    exit 1
fi

# 1. Apply Manifests in Sequence
echo -e "${BLUE}[INFO] 1/3. Applying Kubernetes Manifests from $K8S_DIR...${NC}"
kubectl apply -f "$K8S_DIR/00-namespace.yaml"
kubectl apply -f "$K8S_DIR/01-configmap.yaml"
kubectl apply -f "$K8S_DIR/02-secret.yaml"
kubectl apply -f "$K8S_DIR/03-pvc.yaml"
kubectl apply -f "$K8S_DIR/04-deployment.yaml"
kubectl apply -f "$K8S_DIR/05-service.yaml"
kubectl apply -f "$K8S_DIR/06-ingress.yaml"
kubectl apply -f "$K8S_DIR/07-hpa.yaml"

echo -e "  [✓] ${GREEN}All manifests successfully submitted to API server!${NC}"

# 2. Wait for deployment rollout
echo -e "\n${BLUE}[INFO] 2/3. Monitoring Deployment Rollout Status...${NC}"
kubectl rollout status deployment/colorectal-cancer-serving -n "$NAMESPACE" --timeout=120s || {
    echo -e "${YELLOW}[!] Rollout in progress or pending image/volume. Inspecting pods...${NC}"
}

# 3. Display Live Cluster Status Matrix
echo -e "\n${BLUE}[INFO] 3/3. Live Cluster Workload Status in Namespace: $NAMESPACE${NC}\n"
kubectl get all,pvc,ingress,hpa -n "$NAMESPACE"

echo -e "\n${GREEN}${BOLD}=========================================================="
echo "          DEPLOYMENT ROLLOUT CYCLE COMPLETE               "
echo "==========================================================${NC}"
echo -e "  To test the service locally via port-forward, run:"
echo -e "  ${BOLD}kubectl port-forward -n $NAMESPACE svc/colorectal-cancer-service 5000:80${NC}"
echo -e "  Then access: ${GREEN}http://localhost:5000${NC}\n"
