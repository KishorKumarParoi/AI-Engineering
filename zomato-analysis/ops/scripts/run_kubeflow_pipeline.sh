#!/usr/bin/env bash
# ==============================================================================
# Script: run_kubeflow_pipeline.sh
# Purpose: Compiles & executes the Colorectal Cancer Survival Kubeflow Pipeline
# Highlights from Material 5: Kubeflow Pipelines + DagsHub MLflow Tracking
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

PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

echo -e "${BLUE}${BOLD}"
echo "=========================================================="
echo "      KUBEFLOW PIPELINE COMPILER & EXECUTION RUNNER       "
echo "=========================================================="
echo -e "${NC}"

export PYTHONPATH="$PROJECT_ROOT"

# 1. Compile Pipeline to YAML
echo -e "${BLUE}[INFO] 1/2. Compiling Kubeflow Pipeline to YAML specification...${NC}"
"$PYTHON_BIN" "$OPS_DIR/kubeflow/compile_pipeline.py"

# 2. Execute or Submit Pipeline Run
MODE="${1:-local}"
if [ "$MODE" == "remote" ]; then
    echo -e "\n${BLUE}[INFO] 2/2. Submitting pipeline to remote Kubeflow cluster...${NC}"
    "$PYTHON_BIN" "$OPS_DIR/kubeflow/run_pipeline.py" --remote
else
    echo -e "\n${BLUE}[INFO] 2/2. Executing pipeline DAG locally with full component logging...${NC}"
    "$PYTHON_BIN" "$OPS_DIR/kubeflow/run_pipeline.py"
fi

echo -e "\n${GREEN}${BOLD}=========================================================="
echo "          PIPELINE EXECUTION CYCLE FINISHED              "
echo "==========================================================${NC}\n"
