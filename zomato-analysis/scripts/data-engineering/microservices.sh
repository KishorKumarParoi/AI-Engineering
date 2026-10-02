#!/usr/bin/env bash
# ==============================================================================
# Script: scripts/data-engineering/microservices.sh
# Purpose: Microservices & Next.js Mesh Lifecycle Controller
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

ORDER_DIR="$PROJECT_ROOT/services/order-service"
CATALOG_DIR="$PROJECT_ROOT/services/catalog-service"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

start_services() {
    echo -e "${CYAN}${BOLD}"
    echo "=========================================================="
    echo "       STARTING ZOMATO DISTRIBUTED MICROSERVICES MESH     "
    echo "=========================================================="
    echo -e "${NC}"

    # 1. Build and start Catalog Service (Port 8082)
    log_info "1/3. Launching Catalog Service on port 8082..."
    cd "$CATALOG_DIR"
    go build -o bin/catalog-server ./cmd/server
    PORT=8082 ./bin/catalog-server > "$PROJECT_ROOT/logs_catalog.log" 2>&1 &
    CATALOG_PID=$!
    echo $CATALOG_PID > "$PROJECT_ROOT/.catalog.pid"
    log_success "Catalog Service running in background (PID: $CATALOG_PID) -> http://localhost:8082"

    # 2. Build and start Order Service (Port 8081)
    log_info "2/3. Launching Order Service on port 8081..."
    cd "$ORDER_DIR"
    go build -o bin/order-server ./cmd/server
    PORT=8081 ./bin/order-server > "$PROJECT_ROOT/logs_order.log" 2>&1 &
    ORDER_PID=$!
    echo $ORDER_PID > "$PROJECT_ROOT/.order.pid"
    log_success "Order Service running in background (PID: $ORDER_PID) -> http://localhost:8081"

    # 3. Verify Health
    cd "$PROJECT_ROOT"
    sleep 2
    log_info "3/3. Verifying service liveness probes..."
    if curl -s http://localhost:8082/healthz | grep -q "healthy"; then
        log_success "Catalog Service liveness probe PASSED"
    else
        log_warn "Catalog Service still starting up..."
    fi

    if curl -s http://localhost:8081/healthz | grep -q "healthy"; then
        log_success "Order Service liveness probe PASSED"
    else
        log_warn "Order Service still starting up..."
    fi

    echo ""
    log_success "Microservices Mesh is ONLINE!"
    echo "  - Catalog Service: http://localhost:8082"
    echo "  - Order Service:   http://localhost:8081"
    echo "  - Next.js Web:     http://localhost:3000 (run './scripts/data-engineering/microservices.sh web')"
}

stop_services() {
    log_info "Stopping running microservices..."
    if [ -f "$PROJECT_ROOT/.catalog.pid" ]; then
        kill "$(cat "$PROJECT_ROOT/.catalog.pid")" 2>/dev/null || true
        rm -f "$PROJECT_ROOT/.catalog.pid"
        log_success "Catalog Service stopped."
    fi

    if [ -f "$PROJECT_ROOT/.order.pid" ]; then
        kill "$(cat "$PROJECT_ROOT/.order.pid")" 2>/dev/null || true
        rm -f "$PROJECT_ROOT/.order.pid"
        log_success "Order Service stopped."
    fi

    if [ -f "$PROJECT_ROOT/.frontend.pid" ]; then
        kill "$(cat "$PROJECT_ROOT/.frontend.pid")" 2>/dev/null || true
        rm -f "$PROJECT_ROOT/.frontend.pid"
        log_success "Frontend server stopped."
    fi

    # Clean port bindings if lingering
    pkill -f "catalog-server" 2>/dev/null || true
    pkill -f "order-server" 2>/dev/null || true
    log_success "All services stopped."
}

start_web() {
    log_info "Launching Next.js 14+ Consumer Web App on port 3000..."
    cd "$FRONTEND_DIR"
    npm run dev > "$PROJECT_ROOT/logs_frontend.log" 2>&1 &
    FRONT_PID=$!
    echo $FRONT_PID > "$PROJECT_ROOT/.frontend.pid"
    cd "$PROJECT_ROOT"
    sleep 3
    log_success "Next.js Web App running at http://localhost:3000 (PID: $FRONT_PID)"
}

status_services() {
    echo -e "${CYAN}${BOLD}"
    echo "=========================================================="
    echo "           MICROSERVICES RUNTIME STATUS                   "
    echo "=========================================================="
    echo -e "${NC}"

    printf "  %-22s | %-10s | %-12s\n" "SERVICE" "PORT" "STATUS"
    echo "  -----------------------+------------+-------------"

    if curl -s http://localhost:8082/healthz | grep -q "healthy"; then
        printf "  %-22s | %-10s | %-12s\n" "Catalog Service" ":8082" "[ONLINE]"
    else
        printf "  %-22s | %-10s | %-12s\n" "Catalog Service" ":8082" "[OFFLINE]"
    fi

    if curl -s http://localhost:8081/healthz | grep -q "healthy"; then
        printf "  %-22s | %-10s | %-12s\n" "Order Service" ":8081" "[ONLINE]"
    else
        printf "  %-22s | %-10s | %-12s\n" "Order Service" ":8081" "[OFFLINE]"
    fi

    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        printf "  %-22s | %-10s | %-12s\n" "Next.js Web" ":3000" "[ONLINE]"
    else
        printf "  %-22s | %-10s | %-12s\n" "Next.js Web" ":3000" "[OFFLINE]"
    fi

    echo "  -----------------------+------------+-------------"
}

COMMAND="${1:-status}"

case "$COMMAND" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 1
        start_services
        ;;
    web)
        start_web
        ;;
    status)
        status_services
        ;;
    *)
        echo "Usage: ./scripts/data-engineering/microservices.sh [start|stop|restart|web|status]"
        exit 1
        ;;
esac
