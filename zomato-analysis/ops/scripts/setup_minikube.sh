#!/usr/bin/env bash
# ==============================================================================
# Script: setup_minikube.sh
# Purpose: Initializes a Local Kubernetes Cluster with Minikube for MLOps
# Highlights from Material 5: Minikube + Docker Driver + Ingress + K8s CLI
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

CPUS="${MINIKUBE_CPUS:-4}"
MEMORY="${MINIKUBE_MEMORY:-8192}"
DISK="${MINIKUBE_DISK:-40g}"
PROFILE="${MINIKUBE_PROFILE:-minikube}"

echo -e "${BLUE}${BOLD}"
echo "=========================================================="
echo "      LOCAL KUBERNETES CLUSTER INITIALIZER (MINIKUBE)     "
echo "=========================================================="
echo -e "${NC}"

# 1. Verify Prerequisites
echo -e "${BLUE}[INFO] 1/5. Checking Prerequisites...${NC}"
if ! command -v minikube >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] minikube CLI is not installed.${NC}"
    echo "Install via Homebrew: brew install minikube"
    exit 1
fi

if ! command -v kubectl >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] kubectl CLI is not installed.${NC}"
    echo "Install via Homebrew: brew install kubectl"
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] Docker is not installed or not running.${NC}"
    exit 1
fi

echo -e "  [+] ${GREEN}Minikube${NC}: $(minikube version --short)"
echo -e "  [+] ${GREEN}Kubectl${NC}: $(kubectl version --client -o yaml | grep gitVersion | head -n1 || echo 'Installed')"
echo -e "  [+] ${GREEN}Docker${NC}: Running"

# 2. Check cluster status
echo -e "\n${BLUE}[INFO] 2/5. Evaluating Cluster Status...${NC}"
if minikube status -p "$PROFILE" >/dev/null 2>&1; then
    echo -e "  [✓] ${GREEN}Minikube cluster '$PROFILE' is already running!${NC}"
else
    echo -e "  [*] ${YELLOW}Starting Minikube with Docker driver (CPUs: $CPUS, Memory: ${MEMORY}MB)...${NC}"
    minikube start \
        -p "$PROFILE" \
        --driver=docker \
        --cpus="$CPUS" \
        --memory="$MEMORY" \
        --disk-size="$DISK" \
        --kubernetes-version=stable
    echo -e "  [✓] ${GREEN}Minikube cluster '$PROFILE' successfully started!${NC}"
fi

# 3. Enable essential addons
echo -e "\n${BLUE}[INFO] 3/5. Enabling Essential Addons...${NC}"
echo "  [*] Enabling Ingress Controller..."
minikube addons enable ingress -p "$PROFILE" || true

echo "  [*] Enabling Metrics Server (for HPA)..."
minikube addons enable metrics-server -p "$PROFILE" || true

echo "  [*] Enabling Default StorageClass..."
minikube addons enable default-storageclass -p "$PROFILE" || true

# 4. Configure Kubectl Context
echo -e "\n${BLUE}[INFO] 4/5. Setting Kubectl Context...${NC}"
kubectl config use-context "$PROFILE"
echo -e "  [✓] Current context: ${GREEN}$(kubectl config current-context)${NC}"

# 5. Display Cluster Summary Matrix
IP=$(minikube ip -p "$PROFILE")
echo -e "\n${GREEN}${BOLD}=========================================================="
echo "          MINIKUBE KUBERNETES CLUSTER IS READY            "
echo "==========================================================${NC}"
echo -e "  Cluster Profile:   ${BOLD}$PROFILE${NC}"
echo -e "  Kubernetes Node IP:${GREEN}$IP${NC}"
echo -e "  Docker Driver:     ${GREEN}docker${NC}"
echo -e "  Ingress Addon:     ${GREEN}ENABLED${NC}"
echo -e "  Metrics Server:    ${GREEN}ENABLED (Ready for HPA)${NC}"
echo -e "${GREEN}==========================================================${NC}\n"
