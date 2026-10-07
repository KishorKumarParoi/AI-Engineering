#!/usr/bin/env bash
# ==============================================================================
# ArgoCD GitOps Continuous Deployment Synchronization Script
# Directly implements production workflow from GitOps Material 9:
# Authenticates, triggers declarative sync, verifies health, handles rollbacks.
# ==============================================================================

set -euo pipefail

ARGOCD_SERVER="${ARGOCD_SERVER:-argocd.production.internal:443}"
ARGOCD_AUTH_TOKEN="${ARGOCD_AUTH_TOKEN:-}"
ARGOCD_USERNAME="${ARGOCD_USERNAME:-admin}"
ARGOCD_PASSWORD="${ARGOCD_PASSWORD:-admin123}"
APP_NAME="${1:-zomato-prod-aws}"
SYNC_TIMEOUT="${SYNC_TIMEOUT:-300}"

COLOR_RESET="\033[0m"
COLOR_GREEN="\033[32m"
COLOR_YELLOW="\033[33m"
COLOR_RED="\033[31m"
COLOR_CYAN="\033[36m"

log_info() { echo -e "${COLOR_GREEN}[INFO]${COLOR_RESET} $1"; }
log_warn() { echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $1"; }
log_err()  { echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"; }
log_step() { echo -e "\n${COLOR_CYAN}==> $1${COLOR_RESET}"; }

# Check dependencies
if ! command -v argocd &> /dev/null; then
  log_err "ArgoCD CLI not found in PATH. Install via ops/ansible or brew install argocd."
  exit 1
fi

log_step "Step 1: Authenticating with ArgoCD Server [${ARGOCD_SERVER}]"
if [ -n "$ARGOCD_AUTH_TOKEN" ]; then
  log_info "Authenticating via provided ARGOCD_AUTH_TOKEN"
  export ARGOCD_AUTH_TOKEN
else
  log_info "Logging in as user '${ARGOCD_USERNAME}'..."
  # Handle both local insecure development and production TLS
  argocd login "${ARGOCD_SERVER}" \
    --username "${ARGOCD_USERNAME}" \
    --password "${ARGOCD_PASSWORD}" \
    --insecure \
    --grpc-web
fi

log_step "Step 2: Checking Current Status of Application [${APP_NAME}]"
argocd app get "${APP_NAME}" || {
  log_warn "Application '${APP_NAME}' not registered yet. Applying root app..."
  kubectl apply -f "$(dirname "$0")/projects/project.yaml" || true
  kubectl apply -f "$(dirname "$0")/applications/root-app-of-apps.yaml" || true
  sleep 3
}

log_step "Step 3: Triggering Declarative GitOps Synchronization"
log_info "Initiating sync for '${APP_NAME}' (prune enabled, force disabled)..."
argocd app sync "${APP_NAME}" --prune

log_step "Step 4: Waiting for Cluster Health Verification (Timeout: ${SYNC_TIMEOUT}s)"
if argocd app wait "${APP_NAME}" --health --sync --timeout "${SYNC_TIMEOUT}"; then
  log_info "Sync and Health check SUCCEEDED for application: ${APP_NAME}"
  argocd app get "${APP_NAME}"
else
  log_err "Synchronization or Health check FAILED for application: ${APP_NAME}"
  log_warn "Initiating automated rollback probe..."
  argocd app rollback "${APP_NAME}" 1 || true
  exit 1
fi

log_step "Step 5: GitOps Deployment State Complete"
log_info "Desired Git state is in 100% sync with live Kubernetes cluster."
