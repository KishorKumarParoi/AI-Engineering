#!/usr/bin/env bash
# ==============================================================================
# Script: scripts/data-engineering/orchestration.sh
# Purpose: Astronomer Airflow DAG & Orchestrator Management
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

check_astro() {
    if ! command -v astro &>/dev/null; then
        log_error "Astro CLI is not installed. Please install it using 'brew install astro'."
        exit 1
    fi
}

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "=========================================================="
    echo "       ASTRONOMER AIRFLOW ORCHESTRATION CONTROLLER        "
    echo "=========================================================="
    echo -e "${NC}"
}

start_astro() {
    print_header
    check_astro
    log_info "Starting Astronomer Airflow containers..."
    astro dev start
    log_success "Airflow is running! Access Webserver UI at http://localhost:8080 (admin/admin)"
}

stop_astro() {
    print_header
    check_astro
    log_info "Stopping Astronomer Airflow containers..."
    astro dev stop
    log_success "Airflow services stopped."
}

restart_astro() {
    print_header
    check_astro
    log_info "Restarting Astronomer Airflow containers..."
    astro dev restart
    log_success "Airflow services restarted."
}

status_astro() {
    print_header
    check_astro
    log_info "Checking Astronomer container status..."
    astro dev ps
}

logs_astro() {
    check_astro
    astro dev logs "$@"
}

trigger_dag() {
    print_header
    check_astro
    DAG_ID="${1:-zomato_batch}"
    log_info "Triggering DAG: $DAG_ID..."
    astro dev run dags trigger "$DAG_ID" || astro dev pytest tests/dags/test_dag_example.py
    log_success "Trigger command completed."
}

COMMAND="${1:-status}"
shift || true

case "$COMMAND" in
    start|up)
        start_astro
        ;;
    stop|down)
        stop_astro
        ;;
    restart)
        restart_astro
        ;;
    status|ps)
        status_astro
        ;;
    logs)
        logs_astro "$@"
        ;;
    trigger|run)
        trigger_dag "${1:-zomato_batch}"
        ;;
    help|--help|-h)
        print_header
        echo "Usage: ./scripts/data-engineering/orchestration.sh [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  start     Start local Astronomer Airflow dev environment (astro dev start)"
        echo "  stop      Stop Airflow dev containers (astro dev stop)"
        echo "  restart   Restart Airflow dev containers (astro dev restart)"
        echo "  status    Show status of running containers (astro dev ps) [Default]"
        echo "  logs      View container logs"
        echo "  trigger   Trigger execution of 'zomato_batch' pipeline DAG"
        echo ""
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        echo "Run './scripts/data-engineering/orchestration.sh help' for usage instructions."
        exit 1
        ;;
esac
