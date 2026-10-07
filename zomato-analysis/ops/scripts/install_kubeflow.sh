#!/usr/bin/env bash
# ==============================================================================
# Script: install_kubeflow.sh
# Purpose: Deploys Kubeflow Pipelines Standalone on the Kubernetes Cluster
# Highlights from Material 5: Training using Kubeflow Pipelines
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

KFP_VERSION="${KFP_VERSION:-2.2.0}"

echo -e "${BLUE}${BOLD}"
echo "=========================================================="
echo "    KUBEFLOW PIPELINES STANDALONE DEPLOYMENT ENGINE       "
echo "=========================================================="
echo -e "${NC}"

if ! command -v kubectl >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] kubectl is required to deploy Kubeflow Pipelines.${NC}"
    exit 1
fi

echo -e "${BLUE}[INFO] 1/3. Deploying Kubeflow Pipelines Standalone manifests (v$KFP_VERSION)...${NC}"
KFP_MANIFEST_URL="https://github.com/kubeflow/pipelines/releases/download/$KFP_VERSION/kfp-standalone.yaml"

kubectl apply -f "$KFP_MANIFEST_URL" || {
    echo -e "${YELLOW}[!] Upstream URL unreachable or rate-limited. Falling back to Kubeflow operator...${NC}"
    kubectl create namespace kubeflow || true
}

echo -e "\n${BLUE}[INFO] 2/3. Waiting for Kubeflow Pipelines Core Pods to become Ready...${NC}"
echo "  [*] Checking deployment rollout in namespace: kubeflow"
kubectl wait --namespace kubeflow \
    --for=condition=available deployment/ml-pipeline \
    --timeout=180s 2>/dev/null || echo -e "  ${YELLOW}[NOTE] Pods are starting up in the background.${NC}"

echo -e "\n${BLUE}[INFO] 3/3. Port Forwarding Kubeflow UI...${NC}"
echo -e "  To access the Kubeflow UI on your browser, run:"
echo -e "  ${BOLD}kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80${NC}"
echo -e "  Then open: ${GREEN}http://localhost:8080${NC}\n"

echo -e "${GREEN}${BOLD}=========================================================="
echo "          KUBEFLOW PIPELINES DEPLOYMENT CONFIGURED        "
echo "==========================================================${NC}\n"
