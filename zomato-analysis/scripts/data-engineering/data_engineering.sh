#!/usr/bin/env bash
# ==============================================================================
# Script: scripts/data-engineering/data_engineering.sh
# Purpose: Core Data Engineering Pipeline & Medallion Layer Orchestrator
# Tier: Senior Staff / Lead Data Engineer Standard
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    set -a
    source <(grep -v '^[[:space:]]*#' "$ENV_FILE" | grep -v '^[[:space:]]*$')
    set +a
fi

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "=========================================================="
    echo "      ZOMATO DATA ENGINEERING PIPELINE (MEDALLION)       "
    echo "=========================================================="
    echo -e "${NC}"
}

run_dbt_debug() {
    log_info "1/4. Verifying dbt connection to Snowflake warehouse..."
    cd "$PROJECT_ROOT/zomato"
    uv run dbt debug --profiles-dir .
    cd "$PROJECT_ROOT"
    log_success "Snowflake connection and profile verified!"
}

run_dbt_snapshots() {
    log_info "2/4. Executing SCD Type 2 dimension snapshots..."
    cd "$PROJECT_ROOT/zomato"
    uv run dbt snapshot --profiles-dir .
    cd "$PROJECT_ROOT"
    log_success "SCD2 Snapshots executed successfully!"
}

run_dbt_core() {
    log_info "3/4. Building core staging views, conformed dimensions, and incremental facts..."
    cd "$PROJECT_ROOT/zomato"
    uv run dbt build --exclude tag:ai --profiles-dir .
    cd "$PROJECT_ROOT"
    log_success "Core Medallion tables & facts built successfully!"
}

run_dbt_ai_marts() {
    log_info "4/4. Building Gold AI analytical marts..."
    cd "$PROJECT_ROOT/zomato"
    uv run dbt build --select tag:ai --profiles-dir .
    cd "$PROJECT_ROOT"
    log_success "AI analytical marts built successfully!"
}

run_all() {
    print_header
    run_dbt_debug
    echo ""
    run_dbt_snapshots
    echo ""
    run_dbt_core
    echo ""
    run_dbt_ai_marts
    echo ""
    log_success "All Data Engineering Medallion layers built and tested (100% PASS)!"
}

COMMAND="${1:-all}"

case "$COMMAND" in
    all)
        run_all
        ;;
    debug)
        print_header
        run_dbt_debug
        ;;
    snapshot|snapshots)
        print_header
        run_dbt_snapshots
        ;;
    core)
        print_header
        run_dbt_core
        ;;
    ai|marts)
        print_header
        run_dbt_ai_marts
        ;;
    help|--help|-h)
        print_header
        echo "Usage: ./scripts/data-engineering/data_engineering.sh [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  all        Run debug -> snapshot -> core build -> ai marts build [Default]"
        echo "  debug      Test dbt profile and Snowflake warehouse connectivity"
        echo "  snapshot   Run SCD Type 2 dimension snapshots (snap_restaurants)"
        echo "  core       Build Silver views, Gold dimensions, and incremental facts"
        echo "  ai         Build Gold AI review insights mart"
        echo ""
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        echo "Run './scripts/data-engineering/data_engineering.sh help' for usage instructions."
        exit 1
        ;;
esac
