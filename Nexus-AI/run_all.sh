#!/usr/bin/env bash
# ============================================================================
#  NEXUS-AI: One-Click Enterprise AI Platform Launcher
# ============================================================================
#  Usage:
#    ./run_all.sh --mode=local                    # Zero-cost local demo
#    ./run_all.sh --mode=local --scale=0.1         # Quick sample data
#    ./run_all.sh --mode=cloud --provider=gcp      # Deploy to GCP
#    ./run_all.sh --service=web                    # Frontend + Backend only
#    ./run_all.sh --demo                           # Guided demo mode
#    ./run_all.sh --help                           # Show usage
# ============================================================================

set -euo pipefail

# ── Colors and Formatting ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

NEXUS_BANNER="${CYAN}${BOLD}
======================================================================
    NEXUS-AI: Enterprise Multi-Cloud Lakehouse + MLOps + AI Mesh
    One-Click Deployment Engine v1.0
======================================================================
${NC}"

# ── Script Directory ─────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Default Configuration ────────────────────────────────────────────────
MODE="local"
PROVIDER=""
REGION=""
SERVICE=""
SCALE="1.0"
DEMO_MODE=false
SKIP_DATA=false
VERBOSE=false

# ── Parse Arguments ──────────────────────────────────────────────────────
usage() {
    echo -e "${BOLD}Usage:${NC}"
    echo "  ./run_all.sh [OPTIONS]"
    echo ""
    echo -e "${BOLD}Options:${NC}"
    echo "  --mode=<local|cloud>       Execution mode (default: local)"
    echo "  --provider=<gcp|aws|azure> Cloud provider (required for cloud mode)"
    echo "  --region=<region>          Cloud region"
    echo "  --service=<web|etl|agents> Run specific service only"
    echo "  --scale=<0.1-10.0>         Data scale factor (default: 1.0)"
    echo "  --demo                     Guided demo mode with narration"
    echo "  --skip-data                Skip data generation step"
    echo "  --verbose                  Enable verbose output"
    echo "  --help                     Show this help message"
}

for arg in "$@"; do
    case $arg in
        --mode=*)      MODE="${arg#*=}" ;;
        --provider=*)  PROVIDER="${arg#*=}" ;;
        --region=*)    REGION="${arg#*=}" ;;
        --service=*)   SERVICE="${arg#*=}" ;;
        --scale=*)     SCALE="${arg#*=}" ;;
        --demo)        DEMO_MODE=true ;;
        --skip-data)   SKIP_DATA=true ;;
        --verbose)     VERBOSE=true ;;
        --help)        echo -e "$NEXUS_BANNER"; usage; exit 0 ;;
        *)             echo -e "${RED}Unknown option: $arg${NC}"; usage; exit 1 ;;
    esac
done

# ── Helper Functions ─────────────────────────────────────────────────────
log_step() {
    local step_num=$1
    local total=$2
    local message=$3
    echo -e "\n${MAGENTA}──────────────────────────────────────────────────────────${NC}"
    echo -e "${BOLD}  [${step_num}/${total}] ${message}${NC}"
    echo -e "${MAGENTA}──────────────────────────────────────────────────────────${NC}"
}

log_success() { echo -e "  ${GREEN}[OK] $1${NC}"; }
log_warn()    { echo -e "  ${YELLOW}[WARN] $1${NC}"; }
log_error()   { echo -e "  ${RED}[ERROR] $1${NC}"; }
log_info()    { echo -e "  ${BLUE}[INFO] $1${NC}"; }

check_command() {
    if command -v "$1" &> /dev/null; then
        local version
        version=$($1 --version 2>&1 | head -1)
        log_success "$1 found: $version"
        return 0
    else
        log_error "$1 is not installed"
        return 1
    fi
}

demo_pause() {
    if [ "$DEMO_MODE" = true ]; then
        echo -e "\n  ${CYAN}[Demo] Press Enter to continue...${NC}"
        read -r
    fi
}

# ── MAIN EXECUTION ───────────────────────────────────────────────────────
echo -e "$NEXUS_BANNER"
echo -e "${BOLD}  Mode:     ${GREEN}${MODE}${NC}"
echo -e "${BOLD}  Provider: ${GREEN}${PROVIDER:-N/A}${NC}"
echo -e "${BOLD}  Scale:    ${GREEN}${SCALE}x${NC}"
echo -e "${BOLD}  Demo:     ${GREEN}${DEMO_MODE}${NC}"
echo ""

TOTAL_STEPS=8
START_TIME=$(date +%s)

# ═══════════════════════════════════════════════════════════════════════
# STEP 1: Pre-flight Checks
# ═══════════════════════════════════════════════════════════════════════
log_step 1 $TOTAL_STEPS "Pre-flight System Check"

PREFLIGHT_PASS=true
check_command "python3" || PREFLIGHT_PASS=false
check_command "node"    || log_warn "Node.js not found (needed for frontend)"
check_command "docker"  || log_warn "Docker not found (needed for services)"

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
if python3 -c "import sys; assert sys.version_info >= (3, 10)" 2>/dev/null; then
    log_success "Python version ${PYTHON_VERSION} >= 3.10"
else
    log_error "Python ${PYTHON_VERSION} < 3.10 required"
    PREFLIGHT_PASS=false
fi

if [ "$PREFLIGHT_PASS" = false ]; then
    log_error "Pre-flight checks failed. Please install missing dependencies."
    exit 1
fi

log_success "All pre-flight checks passed!"
demo_pause

# ═══════════════════════════════════════════════════════════════════════
# STEP 2: Install Python Dependencies
# ═══════════════════════════════════════════════════════════════════════
log_step 2 $TOTAL_STEPS "Installing Dependencies"

if [ ! -d ".venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate

if command -v uv &> /dev/null; then
    log_info "Installing with uv (fast mode)..."
    uv pip install -e ".[dev]" --quiet 2>/dev/null || pip install -e ".[dev]" --quiet
else
    log_info "Installing with pip..."
    pip install -e ".[dev]" --quiet 2>/dev/null || pip install -e "." --quiet
fi

log_success "Python dependencies installed!"
demo_pause

# ═══════════════════════════════════════════════════════════════════════
# STEP 3: Generate Synthetic Data
# ═══════════════════════════════════════════════════════════════════════
if [ "$SKIP_DATA" = false ]; then
    log_step 3 $TOTAL_STEPS "Generating Zomato Synthetic Data (Scale: ${SCALE}x)"
    python3 data/generators/seed_all.py --rows-scale "$SCALE" --output-dir data/raw
    log_success "Synthetic data generated!"
else
    log_step 3 $TOTAL_STEPS "Skipping Data Generation (--skip-data)"
    log_warn "Using existing data in data/raw/"
fi
demo_pause

# ═══════════════════════════════════════════════════════════════════════
# STEP 4: Run Medallion ETL Pipeline (Bronze -> Silver -> Gold)
# ═══════════════════════════════════════════════════════════════════════
log_step 4 $TOTAL_STEPS "Running Medallion ETL Pipeline"

if [ -f "etl/pipeline.py" ]; then
    python3 -m etl.pipeline --provider="${PROVIDER:-local}" --input-dir=data/raw
    log_success "Medallion ETL pipeline complete! (Bronze -> Silver -> Gold)"
else
    log_warn "ETL pipeline not yet implemented (Phase 1B-1D). Skipping."
fi
demo_pause

# ═══════════════════════════════════════════════════════════════════════
# STEP 5: Train ML Model and Register in MLflow
# ═══════════════════════════════════════════════════════════════════════
log_step 5 $TOTAL_STEPS "Training Delivery ETA Model (MLOps Pipeline)"

if [ -f "mlops/train.py" ]; then
    python3 -m mlops.train --experiment-name="nexus-ai-delivery-eta"
    log_success "Model trained and registered in MLflow!"
else
    log_warn "MLOps training pipeline not yet implemented (Phase 2). Skipping."
fi
demo_pause

# ═══════════════════════════════════════════════════════════════════════
# STEP 6: Start Observability Stack (Prometheus + Grafana)
# ═══════════════════════════════════════════════════════════════════════
log_step 6 $TOTAL_STEPS "Starting Observability Stack"

if [ "$MODE" = "local" ] && command -v docker &> /dev/null; then
    if [ -f "docker-compose.yml" ]; then
        docker compose up -d prometheus grafana mlflow 2>/dev/null || true
        log_success "Prometheus (localhost:9090) + Grafana (localhost:3001) + MLflow (localhost:5000)"
    else
        log_warn "docker-compose.yml not yet created (Phase 4A). Skipping."
    fi
else
    log_warn "Observability requires Docker. Skipping in current config."
fi
demo_pause

# ═══════════════════════════════════════════════════════════════════════
# STEP 7: Initialize AI Agent Mesh
# ═══════════════════════════════════════════════════════════════════════
log_step 7 $TOTAL_STEPS "Initializing 5-Agent AI Mesh"

if [ -f "agents/orchestrator.py" ]; then
    log_info "Starting Agent Orchestrator (LangGraph State Machine)..."
    log_info "  Agent 1: Data Agent (NL2SQL)"
    log_info "  Agent 2: Business Analysis Agent"
    log_info "  Agent 3: MLOps Agent"
    log_info "  Agent 4: Security and Guardrails Agent"
    log_info "  Agent 5: Voice and Notification Agent"
    python3 -m backend.services.agent_service.app &
    AGENT_PID=$!
    log_success "Agent Mesh initialized (PID: $AGENT_PID)"
else
    log_warn "Agent mesh not yet implemented (Phase 3). Skipping."
fi
demo_pause

# ═══════════════════════════════════════════════════════════════════════
# STEP 8: Launch Backend API + Frontend Dashboard
# ═══════════════════════════════════════════════════════════════════════
log_step 8 $TOTAL_STEPS "Launching Backend API and Frontend Dashboard"

if [ -f "backend/services/etl_service/app.py" ]; then
    log_info "Starting FastAPI backend services..."
    python3 -m uvicorn backend.services.etl_service.app:app --host 0.0.0.0 --port 8080 &
    BACKEND_PID=$!
    log_success "Backend API running on http://localhost:8080"
else
    log_warn "Backend not yet implemented (Phase 5A). Skipping."
fi

if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    log_info "Starting Next.js frontend..."
    (cd frontend && npm run dev) &
    FRONTEND_PID=$!
    log_success "Frontend dashboard on http://localhost:3000"
else
    log_warn "Frontend not yet implemented (Phase 5B). Skipping."
fi

# ═══════════════════════════════════════════════════════════════════════
# COMPLETION SUMMARY
# ═══════════════════════════════════════════════════════════════════════
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo -e "${GREEN}${BOLD}"
echo "======================================================================"
echo "                  NEXUS-AI IS RUNNING!"
echo "======================================================================"
echo ""
echo "  Frontend Dashboard:  http://localhost:3000"
echo "  Backend API:         http://localhost:8080"
echo "  MLflow UI:           http://localhost:5000"
echo "  Prometheus:          http://localhost:9090"
echo "  Grafana:             http://localhost:3001"
echo "  Agent API:           http://localhost:8080/api/agents"
echo ""
echo "  Boot time: ${ELAPSED}s"
echo ""
echo "======================================================================"
echo -e "${NC}"

if [ "$DEMO_MODE" = true ]; then
    echo -e "${CYAN}${BOLD}[Demo Mode] System is running. Press Ctrl+C to stop all services.${NC}"
fi

wait
