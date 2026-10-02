#!/usr/bin/env bash
# ==============================================================================
# Script: run.sh
# Purpose: Master Platform Scripts Checker & CLI Dispatcher
# Tier: Senior Staff / Lead Engineer Standard
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

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

SCRIPTS_DIR="$PROJECT_ROOT/scripts"

# Expected core platform scripts
EXPECTED_SCRIPTS=(
    "data_engineering.sh"
    "ai_pipeline.sh"
    "orchestration.sh"
    "serve_apps.sh"
    "setup_env.sh"
)

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "=========================================================="
    echo "       ZOMATO AI PLATFORM - SCRIPTS CHECKER & RUNNER      "
    echo "=========================================================="
    echo -e "${NC}"
}

check_all_scripts() {
    print_header
    log_info "Auditing and validating platform automation scripts in scripts/..."
    echo ""

    printf "  %-30s | %-12s | %-10s | %-10s\n" "SCRIPT" "PERMISSIONS" "SYNTAX" "STATUS"
    echo "  -------------------------------+--------------+------------+------------"

    TOTAL=0
    PASSED=0
    FAILED=0

    for script_name in "${EXPECTED_SCRIPTS[@]}"; do
        TOTAL=$((TOTAL + 1))
        script_path="$SCRIPTS_DIR/$script_name"

        if [ ! -f "$script_path" ]; then
            printf "  %-30s | %-12s | %-10s | %-10s\n" "$script_name" "MISSING" "N/A" "[FAIL]"
            FAILED=$((FAILED + 1))
            continue
        fi

        # Check / fix execute permission
        if [ ! -x "$script_path" ]; then
            chmod +x "$script_path"
        fi
        perms="$(ls -l "$script_path" | awk '{print $1}')"

        # Check bash syntax
        if bash -n "$script_path" 2>/dev/null; then
            syntax_status="VALID"
            overall_status="[READY]"
            PASSED=$((PASSED + 1))
        else
            syntax_status="SYNTAX ERR"
            overall_status="[FAIL]"
            FAILED=$((FAILED + 1))
        fi

        printf "  %-30s | %-12s | %-10s | %-10s\n" "scripts/$script_name" "$perms" "$syntax_status" "$overall_status"
    done

    echo "  -------------------------------+--------------+------------+------------"
    echo ""

    if [ "$FAILED" -eq 0 ]; then
        log_success "All $TOTAL scripts validated and operational (100% READY)!"
        return 0
    else
        log_error "$FAILED of $TOTAL scripts failed inspection."
        return 1
    fi
}

show_help() {
    print_header
    echo "Usage: ./run.sh [COMMAND] [ARGS...]"
    echo ""
    echo "Platform Commands:"
    echo "  check                Validate all scripts in scripts/ (default)"
    echo "  de [args...]         Run Data Engineering orchestrator (scripts/data_engineering.sh)"
    echo "  ai [args...]         Run AI/LLM pipeline orchestrator (scripts/ai_pipeline.sh)"
    echo "  astro [args...]      Manage Airflow dev environment (scripts/orchestration.sh)"
    echo "  apps [sql|rag]       Launch Streamlit applications (scripts/serve_apps.sh)"
    echo "  doctor               Run environment doctor & sync deps (scripts/setup_env.sh)"
    echo "  test [args...]       Execute master test suite (./test_conn.py)"
    echo "  help                 Show this help manual"
    echo ""
    echo "Quick Examples:"
    echo "  ./run.sh check       # Check all scripts"
    echo "  ./run.sh de all      # Run complete dbt medallion pipeline"
    echo "  ./run.sh ai enrich   # Run review enrichment"
    echo "  ./run.sh apps sql    # Launch Text-to-SQL app on port 8501"
    echo "  ./run.sh test        # Run comprehensive test scorecard"
    echo ""
}

COMMAND="${1:-check}"
shift || true

case "$COMMAND" in
    check)
        check_all_scripts
        ;;
    de|data-engineering|data_engineering)
        "$SCRIPTS_DIR/data_engineering.sh" "$@"
        ;;
    ai|ai-pipeline|ai_pipeline)
        "$SCRIPTS_DIR/ai_pipeline.sh" "$@"
        ;;
    astro|airflow|orchestration)
        "$SCRIPTS_DIR/orchestration.sh" "$@"
        ;;
    apps|serve|app)
        "$SCRIPTS_DIR/serve_apps.sh" "$@"
        ;;
    doctor|setup)
        "$SCRIPTS_DIR/setup_env.sh" "$@"
        ;;
    test|tests)
        ./test_conn.py "$@"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        echo "Run './run.sh help' for usage instructions."
        exit 1
        ;;
esac
