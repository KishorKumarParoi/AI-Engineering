#!/usr/bin/env bash
# ==============================================================================
# Script: run.sh
# Purpose: Master Platform Runner & Orchestrator
# Tier: Senior Staff / Lead Engineer Standard
#
# Usage:
#   ./run.sh             # Executes Data Engineering pipeline & streams full logs
#   ./run.sh check       # Audits all scripts in scripts/data-engineering/
#   ./run.sh de [cmd]    # Runs data_engineering.sh (all, debug, snapshot, core, ai)
#   ./run.sh ai [cmd]    # Runs ai_pipeline.sh (all, enrich, embed, marts)
#   ./run.sh astro [cmd] # Controls Airflow (start, stop, status, trigger)
#   ./run.sh apps [app]  # Launches Streamlit app (sql or rag)
#   ./run.sh doctor      # Runs environment setup and dependency verification
#   ./run.sh test        # Runs master test suite (./test_connection.py)
# ==============================================================================

set -euo pipefail

# -----------------------------
# Color Formatting (Universal ASCII)
# -----------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

DE_SCRIPTS_DIR="$PROJECT_ROOT/scripts/data-engineering"

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "=========================================================="
    echo "      ZOMATO AI DATA PLATFORM - MASTER SCRIPT RUNNER      "
    echo "=========================================================="
    echo -e "${NC}"
}

check_scripts() {
    print_header
    echo -e "${BLUE}[INFO]${NC} Auditing automation scripts in scripts/data-engineering/..."
    echo ""

    EXPECTED_SCRIPTS=(
        "data_engineering.sh"
        "ai_pipeline.sh"
        "orchestration.sh"
        "serve_apps.sh"
        "setup_env.sh"
    )

    printf "  %-32s | %-12s | %-10s | %-10s\n" "SCRIPT" "PERMISSIONS" "SYNTAX" "STATUS"
    echo "  ---------------------------------+--------------+------------+------------"

    TOTAL=0
    PASSED=0
    FAILED=0

    for script_name in "${EXPECTED_SCRIPTS[@]}"; do
        TOTAL=$((TOTAL + 1))
        script_path="$DE_SCRIPTS_DIR/$script_name"

        if [ ! -f "$script_path" ]; then
            printf "  %-32s | %-12s | %-10s | %-10s\n" "$script_name" "MISSING" "N/A" "[FAIL]"
            FAILED=$((FAILED + 1))
            continue
        fi

        if [ ! -x "$script_path" ]; then
            chmod +x "$script_path"
        fi
        perms="$(ls -l "$script_path" | awk '{print $1}')"

        if bash -n "$script_path" 2>/dev/null; then
            syntax_status="VALID"
            overall_status="[READY]"
            PASSED=$((PASSED + 1))
        else
            syntax_status="SYNTAX ERR"
            overall_status="[FAIL]"
            FAILED=$((FAILED + 1))
        fi

        printf "  %-32s | %-12s | %-10s | %-10s\n" "scripts/data-engineering/$script_name" "$perms" "$syntax_status" "$overall_status"
    done

    echo "  ---------------------------------+--------------+------------+------------"
    echo ""

    if [ "$FAILED" -eq 0 ]; then
        echo -e "${GREEN}[SUCCESS] All $TOTAL scripts validated and operational (100% READY)!${NC}"
        return 0
    else
        echo -e "${RED}[ERROR] $FAILED of $TOTAL scripts failed inspection.${NC}"
        return 1
    fi
}

show_help() {
    print_header
    echo "Usage: ./run.sh [COMMAND] [ARGS...]"
    echo ""
    echo "Commands:"
    echo "  (no args)            Run Data Engineering pipeline and stream full logs [Default]"
    echo "  de [args...]         Run scripts/data-engineering/data_engineering.sh"
    echo "  ai [args...]         Run scripts/data-engineering/ai_pipeline.sh"
    echo "  astro [args...]      Run scripts/data-engineering/orchestration.sh"
    echo "  apps [sql|rag]       Run scripts/data-engineering/serve_apps.sh"
    echo "  doctor               Run scripts/data-engineering/setup_env.sh"
    echo "  check                Validate script permissions and syntax in scripts/data-engineering/"
    echo "  test [args...]       Execute master verification suite (./test_connection.py)"
    echo "  help                 Show this help manual"
    echo ""
    echo "Examples:"
    echo "  ./run.sh             # Run full data engineering build with logs"
    echo "  ./run.sh check       # Audit all scripts"
    echo "  ./run.sh de debug    # Run dbt debug connectivity test"
    echo "  ./run.sh ai enrich   # Run customer review LLM enrichment"
    echo "  ./run.sh apps sql    # Launch Text-to-SQL Streamlit app"
    echo ""
}

# If no argument provided, default to running data engineering with live logs
COMMAND="${1:-de}"
if [ $# -gt 0 ]; then
    shift
fi

case "$COMMAND" in
    de|data-engineering|data_engineering)
        TARGET="${1:-all}"
        shift || true
        "$DE_SCRIPTS_DIR/data_engineering.sh" "$TARGET" "$@"
        ;;
    ai|ai-pipeline|ai_pipeline)
        TARGET="${1:-all}"
        shift || true
        "$DE_SCRIPTS_DIR/ai_pipeline.sh" "$TARGET" "$@"
        ;;
    astro|airflow|orchestration)
        "$DE_SCRIPTS_DIR/orchestration.sh" "$@"
        ;;
    apps|serve|app)
        "$DE_SCRIPTS_DIR/serve_apps.sh" "$@"
        ;;
    doctor|setup)
        "$DE_SCRIPTS_DIR/setup_env.sh" "$@"
        ;;
    check)
        check_scripts
        ;;
    test|tests)
        ./test_connection.py "$@"
        ;;
    all)
        print_header
        echo -e "${BLUE}[INFO] Running end-to-end platform workflow...${NC}"
        "$DE_SCRIPTS_DIR/setup_env.sh"
        echo ""
        "$DE_SCRIPTS_DIR/data_engineering.sh" all
        echo ""
        "$DE_SCRIPTS_DIR/ai_pipeline.sh" all
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}[ERROR] Unknown command: $COMMAND${NC}"
        echo "Run './run.sh help' for usage instructions."
        exit 1
        ;;
esac
