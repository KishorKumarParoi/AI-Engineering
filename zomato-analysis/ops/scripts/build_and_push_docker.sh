#!/usr/bin/env bash
# ==============================================================================
# Script: build_and_push_docker.sh
# Purpose: Builds and pushes MLOps Container Images (DockerHub & Minikube)
# Highlights from Material 5: Dockerization + Use of DockerHub + Local Cluster
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
PROJECT_ROOT="$(cd "$OPS_DIR/.." && pwd)"
CODE_DIR="$PROJECT_ROOT/1. ALL MATERIAL - 5 - NEW/CODE"

DOCKER_USER="${DOCKER_USERNAME:-kishorkumarparoi}"
TAG="${IMAGE_TAG:-latest}"
APP_IMAGE="$DOCKER_USER/colorectal-cancer-app:$TAG"
PIPELINE_IMAGE="$DOCKER_USER/colorectal-cancer-pipeline:$TAG"

PUSH_FLAG="${1:-build-only}"

echo -e "${BLUE}${BOLD}"
echo "=========================================================="
echo "         DOCKER CONTAINER BUILD & REGISTRY ENGINE         "
echo "=========================================================="
echo -e "${NC}"

if ! command -v docker >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] Docker CLI not found.${NC}"
    exit 1
fi

# 1. Build Inference Serving App Image
echo -e "${BLUE}[INFO] 1/4. Building Serving App Docker Image: ${BOLD}$APP_IMAGE${NC}..."
docker build \
    -t "$APP_IMAGE" \
    -f "$OPS_DIR/docker/Dockerfile.app" \
    "$CODE_DIR"
echo -e "  [✓] ${GREEN}App image built successfully!${NC}"

# 2. Build Pipeline Runner Image
echo -e "\n${BLUE}[INFO] 2/4. Building Pipeline Runner Docker Image: ${BOLD}$PIPELINE_IMAGE${NC}..."
docker build \
    -t "$PIPELINE_IMAGE" \
    -f "$OPS_DIR/docker/Dockerfile.pipeline" \
    "$OPS_DIR"
echo -e "  [✓] ${GREEN}Pipeline image built successfully!${NC}"

# 3. Load into Minikube if cluster is active
if command -v minikube >/dev/null 2>&1 && minikube status >/dev/null 2>&1; then
    echo -e "\n${BLUE}[INFO] 3/4. Loading images directly into Minikube Docker Daemon...${NC}"
    minikube image load "$APP_IMAGE" || true
    minikube image load "$PIPELINE_IMAGE" || true
    echo -e "  [✓] ${GREEN}Images cached inside Minikube cluster!${NC}"
else
    echo -e "\n${YELLOW}[INFO] 3/4. Minikube not active; skipping local cluster image cache.${NC}"
fi

# 4. Push to DockerHub if requested
if [ "$PUSH_FLAG" == "push" ]; then
    echo -e "\n${BLUE}[INFO] 4/4. Pushing images to DockerHub registry...${NC}"
    docker push "$APP_IMAGE"
    docker push "$PIPELINE_IMAGE"
    echo -e "  [✓] ${GREEN}Images pushed to DockerHub: $APP_IMAGE, $PIPELINE_IMAGE${NC}"
else
    echo -e "\n${YELLOW}[INFO] 4/4. Build complete without push. Run './ops/scripts/build_and_push_docker.sh push' to push to DockerHub.${NC}"
fi

echo -e "\n${GREEN}${BOLD}=========================================================="
echo "          CONTAINER BUILD PIPELINE SUCCESSFUL             "
echo "==========================================================${NC}\n"
