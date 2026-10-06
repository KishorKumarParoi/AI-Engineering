#!/usr/bin/env bash
# ==============================================================================
# Script: scripts/data-engineering/serve_apps.sh
# Purpose: AI Streamlit Application Server Launcher
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

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "=========================================================="
    echo "         ZOMATO AI STREAMLIT APPLICATIONS LAUNCHER        "
    echo "=========================================================="
    echo -e "${NC}"
}

run_streamlit() {
    local script="$1"
    local port="$2"
    local headless="${HEADLESS:-true}"
    if [ -f "$PROJECT_ROOT/.venv/bin/streamlit" ]; then
        "$PROJECT_ROOT/.venv/bin/streamlit" run "$script" --server.port "$port" --server.headless "$headless"
    elif command -v uv >/dev/null 2>&1; then
        uv run streamlit run "$script" --server.port "$port" --server.headless "$headless"
    else
        streamlit run "$script" --server.port "$port" --server.headless "$headless"
    fi
}

run_portal_app() {
    print_header
    PORT="${1:-8501}"
    log_info "Launching Unified Zomato AI & Analytics Portal on port $PORT..."
    log_info "URL: http://localhost:$PORT"
    run_streamlit streamlit_app.py "$PORT"
}

run_sql_app() {
    print_header
    PORT="${1:-8501}"
    log_info "Launching Text-to-SQL Analytics Assistant on port $PORT..."
    log_info "URL: http://localhost:$PORT"
    run_streamlit ai/text_to_sql.py "$PORT"
}

run_rag_app() {
    print_header
    PORT="${1:-8502}"
    log_info "Launching Semantic Reviews RAG Chat on port $PORT..."
    log_info "URL: http://localhost:$PORT"
    run_streamlit ai/rag_chat.py "$PORT"
}

COMMAND="${1:-portal}"
PORT="${2:-}"

case "$COMMAND" in
    portal|all|app)
        run_portal_app "${PORT:-8501}"
        ;;
    sql|text_to_sql)
        run_sql_app "${PORT:-8501}"
        ;;
    rag|rag_chat)
        run_rag_app "${PORT:-8502}"
        ;;
    help|--help|-h)
        print_header
        echo "Usage: ./scripts/data-engineering/serve_apps.sh [APP] [PORT]"
        echo ""
        echo "Applications:"
        echo "  portal     Start Unified AI & Analytics Portal (Default port: 8501)"
        echo "  sql        Start Text-to-SQL Analytics Assistant (Default port: 8501)"
        echo "  rag        Start Semantic Reviews RAG Chat (Default port: 8502)"
        echo ""
        echo "Examples:"
        echo "  ./scripts/data-engineering/serve_apps.sh portal"
        echo "  ./scripts/data-engineering/serve_apps.sh sql 8501"
        echo "  ./scripts/data-engineering/serve_apps.sh rag 8502"
        echo ""
        ;;
    *)
        log_error "Unknown application: $COMMAND"
        echo "Run './scripts/data-engineering/serve_apps.sh help' for usage instructions."
        exit 1
        ;;
esac
