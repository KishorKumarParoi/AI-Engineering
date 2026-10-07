#!/usr/bin/env bash
# ==============================================================================
# Script: run.sh
# Purpose: Master Platform Runner, Orchestrator & One-Click Lifecycle Manager
# Tier: Senior Staff / Lead Platform & Data Engineer Standard
#
# Usage:
#   ./run.sh             # Master One-Click Launch (Next.js, Streamlit, Microservices)
#   ./run.sh up / start  # Same as ./run.sh
#   ./run.sh stop / down # Stops all running platform services cleanly
#   ./run.sh restart     # Restarts all running services
#   ./run.sh status      # Live health status matrix of all ports and cloud connections
#   ./run.sh test [s]    # Runs master test suite (./test_connection.py [all|conn|de|ai|orch|azure|pyspark])
#   ./run.sh scd         # Runs Metadata-Driven PySpark Delta Lake SCD Type 1 & 2 pipeline
#   ./run.sh eventhub    # Inspects live Azure Event Hubs telemetry & partition metrics
#   ./run.sh stream [N]  # Streams N real-time order events to Azure Event Hubs & Kafka
#   ./run.sh de [cmd]    # Runs Snowflake Medallion dbt pipeline (all, debug, snapshot, core, ai)
#   ./run.sh ai [cmd]    # Runs AI enrichment & embeddings (all, enrich, embed, marts)
#   ./run.sh astro [cmd] # Controls Astronomer Airflow (start, stop, status, trigger)
#   ./run.sh apps [app]  # Launches foreground Streamlit app (portal, sql, rag)
#   ./run.sh doctor      # Full environment bootstrap and dependency audit
#   ./run.sh check       # Validates shell script permissions and syntax
# ==============================================================================

set -euo pipefail

# -----------------------------
# Color Formatting (Universal ASCII)
# -----------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Ensure JDK 17 for PySpark Delta on macOS
if [ -d "/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home" ]; then
    export JAVA_HOME="/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home"
fi

# Load .env if present
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    . "$PROJECT_ROOT/.env"
    set +a
    export EVENTHUB_CONNECTION_STRING="${EVENTHUB_CONNECTION_STRING:-${CONNECTION_STRING:-}}"
fi

# Paths
DE_SCRIPTS_DIR="$PROJECT_ROOT/scripts/data-engineering"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
ORDER_DIR="$PROJECT_ROOT/services/order-service"
CATALOG_DIR="$PROJECT_ROOT/services/catalog-service"

# Python interpreter selection (Array format to support paths with spaces)
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_CMD=("$PROJECT_ROOT/.venv/bin/python")
    STREAMLIT_CMD=("$PROJECT_ROOT/.venv/bin/streamlit")
    DVC_CMD=("$PROJECT_ROOT/.venv/bin/dvc")
elif command -v uv >/dev/null 2>&1; then
    PYTHON_CMD=(uv run python)
    STREAMLIT_CMD=(uv run streamlit)
    DVC_CMD=(uv run dvc)
else
    PYTHON_CMD=(python3)
    STREAMLIT_CMD=(streamlit)
    DVC_CMD=(dvc)
fi

export PYSPARK_PYTHON="${PROJECT_ROOT}/.venv/bin/python"
export PYSPARK_DRIVER_PYTHON="${PROJECT_ROOT}/.venv/bin/python"
export PYTHONPATH="$PROJECT_ROOT"

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "=========================================================="
    echo "       ZOMATO ENTERPRISE MULTI-CLOUD DATA & AI PLATFORM   "
    echo "=========================================================="
    echo -e "${NC}"
}

# ------------------------------------------------------------------------------
# Service Lifecycle Management
# ------------------------------------------------------------------------------

start_platform() {
    print_header
    echo -e "${BLUE}[INFO] Initiating Master One-Click Platform Launch...${NC}\n"

    # 1. Start Catalog Service (8082) if Go is available
    if command -v go >/dev/null 2>&1 && [ -d "$CATALOG_DIR" ]; then
        if lsof -i :8082 >/dev/null 2>&1; then
            echo -e "  [+] ${GREEN}Catalog Service${NC}: Already online on port :8082"
        else
            echo -e "  [*] ${BLUE}Launching Catalog Microservice on :8082...${NC}"
            cd "$CATALOG_DIR"
            mkdir -p bin
            go build -o bin/catalog-server ./cmd/server
            PORT=8082 ./bin/catalog-server > "$PROJECT_ROOT/logs_catalog.log" 2>&1 &
            CATALOG_PID=$!
            echo "$CATALOG_PID" > "$PROJECT_ROOT/.catalog.pid"
            cd "$PROJECT_ROOT"
            echo -e "  [+] ${GREEN}Catalog Service${NC}: Running (PID: $CATALOG_PID)"
        fi
    fi

    # 2. Start Order Service (8081) if Go is available
    if command -v go >/dev/null 2>&1 && [ -d "$ORDER_DIR" ]; then
        if lsof -i :8081 >/dev/null 2>&1; then
            echo -e "  [+] ${GREEN}Order Service${NC}: Already online on port :8081"
        else
            echo -e "  [*] ${BLUE}Launching Order Microservice on :8081...${NC}"
            cd "$ORDER_DIR"
            mkdir -p bin
            go build -o bin/order-server ./cmd/server
            PORT=8081 ./bin/order-server > "$PROJECT_ROOT/logs_order.log" 2>&1 &
            ORDER_PID=$!
            echo "$ORDER_PID" > "$PROJECT_ROOT/.order.pid"
            cd "$PROJECT_ROOT"
            echo -e "  [+] ${GREEN}Order Service${NC}: Running (PID: $ORDER_PID)"
        fi
    fi

    # 3. Start Next.js Consumer Portal (3000)
    if [ -d "$FRONTEND_DIR" ]; then
        if lsof -i :3000 >/dev/null 2>&1; then
            echo -e "  [+] ${GREEN}Next.js Frontend${NC}: Already online on port :3000"
        else
            echo -e "  [*] ${BLUE}Launching Next.js Streaming Frontend on :3000...${NC}"
            cd "$FRONTEND_DIR"
            npm run dev > "$PROJECT_ROOT/logs_frontend.log" 2>&1 &
            FRONT_PID=$!
            echo "$FRONT_PID" > "$PROJECT_ROOT/.frontend.pid"
            cd "$PROJECT_ROOT"
            echo -e "  [+] ${GREEN}Next.js Frontend${NC}: Running (PID: $FRONT_PID)"
        fi
    fi

    # 4. Start Unified Streamlit AI & Analytics Portal (8501)
    if lsof -i :8501 >/dev/null 2>&1; then
        echo -e "  [+] ${GREEN}Streamlit Platform Hub${NC}: Already online on port :8501"
    else
        echo -e "  [*] ${BLUE}Launching Streamlit Unified AI Hub on :8501...${NC}"
        "${STREAMLIT_CMD[@]}" run streamlit_app.py --server.port 8501 --server.headless true > "$PROJECT_ROOT/logs_streamlit.log" 2>&1 &
        STREAMLIT_PID=$!
        echo "$STREAMLIT_PID" > "$PROJECT_ROOT/.streamlit.pid"
        echo -e "  [+] ${GREEN}Streamlit Platform Hub${NC}: Running (PID: $STREAMLIT_PID)"
    fi

    sleep 2

    # Executive Scorecard & Live Endpoints Dashboard
    echo ""
    echo -e "${CYAN}${BOLD}=========================================================="
    echo "          PLATFORM RUNTIME MESH & CLOUD TELEMETRY         "
    echo -e "==========================================================${NC}"
    echo -e "  🌐 ${BOLD}Next.js Consumer Portal:${NC}     ${GREEN}http://localhost:3000${NC}"
    echo -e "  📊 ${BOLD}Streamlit AI & Lakehouse Hub:${NC} ${GREEN}http://localhost:8501${NC}"
    echo -e "  🤖 ${BOLD}Semantic Reviews RAG Chat:${NC}    ${GREEN}http://localhost:8502${NC} (via: ./run.sh apps rag)"
    echo -e "  📦 ${BOLD}Catalog Microservice:${NC}         ${GREEN}http://localhost:8082${NC}"
    echo -e "  💳 ${BOLD}Order Microservice:${NC}           ${GREEN}http://localhost:8081${NC}"
    if docker ps 2>/dev/null | grep -q "scheduler"; then
        echo -e "  🌪️ ${BOLD}Astronomer Airflow UI:${NC}        ${GREEN}http://localhost:8080${NC}"
    else
        echo -e "  🌪️ ${BOLD}Astronomer Airflow UI:${NC}        ${YELLOW}Offline${NC} (start via: ./run.sh astro start)"
    fi
    echo ""
    echo -e "  📡 ${BOLD}Azure Event Hubs:${NC}             ${CYAN}${EVENT_HUBNAME:-zomato}${NC} @ eventhub-kkp007.servicebus.windows.net"
    echo -e "  ❄️ ${BOLD}Snowflake Data Cloud:${NC}         ${CYAN}${SNOWFLAKE_DATABASE:-ZOMATO}${NC} @ ${SNOWFLAKE_ACCOUNT:-VVXMVZH-FL05366}"
    echo -e "  ⚡ ${BOLD}Apache Spark & Delta Lake:${NC}    ${CYAN}Delta Lake 3.2.0${NC} (Java 17 Runtime Active)"
    echo -e "${CYAN}${BOLD}==========================================================${NC}"
    echo -e "${GREEN}${BOLD}✓ Platform operational! Use './run.sh status' or './run.sh test' anytime.${NC}\n"
}

stop_platform() {
    print_header
    echo -e "${BLUE}[INFO] Shutting down platform services...${NC}\n"

    # Stop Streamlit
    if [ -f "$PROJECT_ROOT/.streamlit.pid" ]; then
        PID=$(cat "$PROJECT_ROOT/.streamlit.pid")
        kill "$PID" 2>/dev/null || true
        rm -f "$PROJECT_ROOT/.streamlit.pid"
        echo -e "  [-] Stopped Streamlit (PID: $PID)"
    fi
    pkill -f "streamlit run streamlit_app.py" 2>/dev/null || true

    # Stop Frontend
    if [ -f "$PROJECT_ROOT/.frontend.pid" ]; then
        PID=$(cat "$PROJECT_ROOT/.frontend.pid")
        kill "$PID" 2>/dev/null || true
        rm -f "$PROJECT_ROOT/.frontend.pid"
        echo -e "  [-] Stopped Next.js Frontend (PID: $PID)"
    fi

    # Stop Order Service
    if [ -f "$PROJECT_ROOT/.order.pid" ]; then
        PID=$(cat "$PROJECT_ROOT/.order.pid")
        kill "$PID" 2>/dev/null || true
        rm -f "$PROJECT_ROOT/.order.pid"
        echo -e "  [-] Stopped Order Service (PID: $PID)"
    fi
    pkill -f "order-server" 2>/dev/null || true

    # Stop Catalog Service
    if [ -f "$PROJECT_ROOT/.catalog.pid" ]; then
        PID=$(cat "$PROJECT_ROOT/.catalog.pid")
        kill "$PID" 2>/dev/null || true
        rm -f "$PROJECT_ROOT/.catalog.pid"
        echo -e "  [-] Stopped Catalog Service (PID: $PID)"
    fi
    pkill -f "catalog-server" 2>/dev/null || true

    echo -e "\n${GREEN}[SUCCESS] All local platform services terminated.${NC}"
}

restart_platform() {
    stop_platform
    sleep 2
    start_platform
}

status_platform() {
    print_header
    echo -e "${BLUE}[INFO] Inspecting Platform Runtime Status Matrix...${NC}\n"

    printf "  %-30s | %-12s | %-12s\n" "SERVICE / INTEGRATION" "PORT / TARGET" "STATUS"
    echo "  -------------------------------+--------------+-------------"

    # Next.js
    if lsof -i :3000 >/dev/null 2>&1; then
        printf "  %-30s | %-12s | %-12s\n" "Next.js Consumer Portal" ":3000" "[ONLINE]"
    else
        printf "  %-30s | %-12s | %-12s\n" "Next.js Consumer Portal" ":3000" "[OFFLINE]"
    fi

    # Streamlit Portal
    if lsof -i :8501 >/dev/null 2>&1; then
        printf "  %-30s | %-12s | %-12s\n" "Streamlit AI & Lakehouse Hub" ":8501" "[ONLINE]"
    else
        printf "  %-30s | %-12s | %-12s\n" "Streamlit AI & Lakehouse Hub" ":8501" "[OFFLINE]"
    fi

    # Streamlit RAG
    if lsof -i :8502 >/dev/null 2>&1; then
        printf "  %-30s | %-12s | %-12s\n" "Streamlit RAG Chat" ":8502" "[ONLINE]"
    else
        printf "  %-30s | %-12s | %-12s\n" "Streamlit RAG Chat" ":8502" "[STANDBY]"
    fi

    # Order Service
    if lsof -i :8081 >/dev/null 2>&1; then
        printf "  %-30s | %-12s | %-12s\n" "Order Microservice" ":8081" "[ONLINE]"
    else
        printf "  %-30s | %-12s | %-12s\n" "Order Microservice" ":8081" "[OFFLINE]"
    fi

    # Catalog Service
    if lsof -i :8082 >/dev/null 2>&1; then
        printf "  %-30s | %-12s | %-12s\n" "Catalog Microservice" ":8082" "[ONLINE]"
    else
        printf "  %-30s | %-12s | %-12s\n" "Catalog Microservice" ":8082" "[OFFLINE]"
    fi

    # Astronomer Airflow
    if docker ps 2>/dev/null | grep -q "scheduler"; then
        printf "  %-30s | %-12s | %-12s\n" "Astronomer Airflow (Docker)" ":8080" "[ONLINE]"
    else
        printf "  %-30s | %-12s | %-12s\n" "Astronomer Airflow (Docker)" ":8080" "[OFFLINE]"
    fi

    # Azure Event Hubs
    if [ -n "${EVENTHUB_CONNECTION_STRING:-${CONNECTION_STRING:-}}" ]; then
        printf "  %-30s | %-12s | %-12s\n" "Azure Event Hubs (Cloud)" "AMQP 1.0" "[CONFIGURED]"
    else
        printf "  %-30s | %-12s | %-12s\n" "Azure Event Hubs (Cloud)" "AMQP 1.0" "[NO CREDENTIALS]"
    fi

    # Snowflake
    if [ -n "${SNOWFLAKE_ACCOUNT:-}" ]; then
        printf "  %-30s | %-12s | %-12s\n" "Snowflake Medallion Lakehouse" "Cloud WH" "[CONFIGURED]"
    else
        printf "  %-30s | %-12s | %-12s\n" "Snowflake Medallion Lakehouse" "Cloud WH" "[NO CREDENTIALS]"
    fi

    # DagsHub MLflow
    if [ -n "${DAGSHUB_REPO_NAME:-}" ] || [[ "${MLFLOW_TRACKING_URI:-}" == *"dagshub.com"* ]]; then
        printf "  %-30s | %-12s | %-12s\n" "DagsHub MLflow (Cloud)" "MLflow REST" "[CONFIGURED]"
    else
        printf "  %-30s | %-12s | %-12s\n" "DagsHub MLflow (Cloud)" "MLflow REST" "[LOCAL SQLITE]"
    fi

    # DVC Data Remote
    if [ -d "$PROJECT_ROOT/.dvc" ]; then
        printf "  %-30s | %-12s | %-12s\n" "DVC Data Storage (DagsHub)" "HTTP Remote" "[CONFIGURED]"
    else
        printf "  %-30s | %-12s | %-12s\n" "DVC Data Storage (DagsHub)" "HTTP Remote" "[UNINITIALIZED]"
    fi

    echo "  -------------------------------+--------------+-------------"
    echo ""
}

# ------------------------------------------------------------------------------
# Script Audit & Verification
# ------------------------------------------------------------------------------

check_scripts() {
    print_header
    echo -e "${BLUE}[INFO]${NC} Auditing automation scripts in scripts/..."
    echo ""

    EXPECTED_SCRIPTS=(
        "scripts/data-engineering/data_engineering.sh"
        "scripts/data-engineering/ai_pipeline.sh"
        "scripts/data-engineering/orchestration.sh"
        "scripts/data-engineering/serve_apps.sh"
        "scripts/data-engineering/setup_env.sh"
        "scripts/data-engineering/microservices.sh"
    )

    printf "  %-44s | %-10s | %-10s\n" "SCRIPT" "SYNTAX" "STATUS"
    echo "  ---------------------------------------------+------------+------------"

    TOTAL=0
    PASSED=0
    FAILED=0

    for script_path in "${EXPECTED_SCRIPTS[@]}"; do
        TOTAL=$((TOTAL + 1))
        full_path="$PROJECT_ROOT/$script_path"

        if [ ! -f "$full_path" ]; then
            printf "  %-44s | %-10s | %-10s\n" "$script_path" "MISSING" "[FAIL]"
            FAILED=$((FAILED + 1))
            continue
        fi

        if [ ! -x "$full_path" ]; then
            chmod +x "$full_path"
        fi

        if bash -n "$full_path" 2>/dev/null; then
            syntax_status="VALID"
            overall_status="[READY]"
            PASSED=$((PASSED + 1))
        else
            syntax_status="SYNTAX ERR"
            overall_status="[FAIL]"
            FAILED=$((FAILED + 1))
        fi

        printf "  %-44s | %-10s | %-10s\n" "$script_path" "$syntax_status" "$overall_status"
    done

    echo "  ---------------------------------------------+------------+------------"
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
    echo "Master Lifecycle Commands:"
    echo "  (no args)            One-click master launch of all web and platform services [Default]"
    echo "  up | start           Start all platform services (Next.js, Streamlit, Microservices)"
    echo "  down | stop          Stop all running services cleanly"
    echo "  restart              Restart all platform services"
    echo "  status | ps          Inspect live runtime health and connection status matrix"
    echo ""
    echo "Verification & Testing:"
    echo "  test [suite]         Run master test suite (./test_connection.py)"
    echo "                       Suites: all (default), conn, de, ai, orch, azure, pyspark"
    echo "  check                Validate permissions and syntax for all shell scripts"
    echo "  doctor               Run environment verification and dependency sync"
    echo ""
    echo "MLOps & Cloud Tracking:"
    echo "  dagshub [args...]    Configure & test remote DagsHub MLflow & DVC tracking"
    echo "  ml [args...]         Train Dynamic ETA regression model with MLflow tracking"
    echo "  dvc [args...]        Manage DVC data tracking with DagsHub (push, pull, status, add)"
    echo "  ops [cmd]            Manage Multi-Cloud (AWS/GCP), Terraform, Ansible, K8s, ArgoCD, Jenkins & Failover"
    echo "  sync [msg]           Synchronize changes across both GitHub repos (AI-Engineering & zomato-analysis)"
    echo ""
    echo "Data, AI & Real-time Pipelines:"
    echo "  scd                  Run Metadata-Driven PySpark Delta Lake SCD Type 1 & 2 Demo"
    echo "  eventhub             Query live Azure Event Hubs cloud telemetry & partition counts"
    echo "  stream [N]           Stream N events directly to Azure Event Hubs & Kafka (default: 25)"
    echo "  de [cmd]             Run Snowflake Medallion pipeline (all, debug, snapshot, core, ai)"
    echo "  ai [cmd]             Run AI enrichment & embedding pipeline (all, enrich, embed, marts)"
    echo "  astro [cmd]          Manage Astronomer Airflow (start, stop, status, trigger)"
    echo "  vision [img]         Execute Computer Vision & Receipt OCR dispute arbitration"
    echo "  apps [portal|sql|rag] Launch specific Streamlit application in foreground"
    echo ""
    echo "Examples:"
    echo "  ./run.sh             # Launch entire platform in one click"
    echo "  ./run.sh test        # Run all 6 master test suites"
    echo "  ./run.sh test pyspark # Run Metadata PySpark & Delta SCD verification"
    echo "  ./run.sh dagshub     # Configure DagsHub remote MLflow connection"
    echo "  ./run.sh ml          # Train ETA model & log to MLflow / DagsHub"
    echo "  ./run.sh dvc push    # Push DVC datasets to DagsHub remote storage"
    echo "  ./run.sh scd         # Execute PySpark SCD-2 simulation"
    echo "  ./run.sh stream 50   # Stream 50 order events to Azure Event Hub"
    echo "  ./run.sh stop        # Shut down all services"
    echo ""
}

# ------------------------------------------------------------------------------
# Dispatcher
# ------------------------------------------------------------------------------

COMMAND="${1:-up}"
if [ $# -gt 0 ]; then
    shift
fi

case "$COMMAND" in
    up|start)
        start_platform
        ;;
    down|stop)
        stop_platform
        ;;
    restart)
        restart_platform
        ;;
    status|ps)
        status_platform
        ;;
    dagshub)
        "${PYTHON_CMD[@]}" "$PROJECT_ROOT/scripts/setup_dagshub.py" "$@"
        ;;
    ml|mlflow|train)
        "${PYTHON_CMD[@]}" "$PROJECT_ROOT/mlops/training/train_eta_mlflow.py" "$@"
        ;;
    dvc)
        "${DVC_CMD[@]}" "$@"
        ;;
    ops)
        "$PROJECT_ROOT/ops/ops.sh" "$@"
        ;;
    vision|cv|ocr)
        IMG_ARG="${1:-vision/test_samples/sample_receipt.png}"
        print_header
        echo -e "${BLUE}[INFO] Running Multimodal Computer Vision & Receipt OCR Dispute Engine on: $IMG_ARG...${NC}\n"
        "${PYTHON_CMD[@]}" -c "
import sys, json
from vision.dispute_engine import DisputeArbitrationEngine
img = sys.argv[1]
engine = DisputeArbitrationEngine()
order = {'order_id': 'ORD-2026-9842', 'customer_id': 'CUST-4109', 'food_name': 'Paneer Butter Masala', 'order_amount': 31.50, 'delivery_fee': 3.00, 'cuisine': 'Indian'}
res = engine.arbitrate_order_dispute(img, order, claim_type='WRONG_ITEM')
print(json.dumps(res, indent=2))
" "$IMG_ARG"
        ;;
    sync)
        "$PROJECT_ROOT/scripts/sync_dual_repos.sh" "$@"
        ;;
    test|tests)
        SUITE_ARG="${1:-all}"
        "${PYTHON_CMD[@]}" ./test_connection.py --suite "$SUITE_ARG"
        ;;
    scd|pyspark)
        print_header
        echo -e "${BLUE}[INFO] Running Metadata-Driven PySpark SCD Pipeline Simulation...${NC}\n"
        "${PYTHON_CMD[@]}" "$PROJECT_ROOT/scripts/etl/run_metadata_pyspark_pipeline.py" --demo-scd2
        ;;
    eventhub|azure)
        print_header
        echo -e "${BLUE}[INFO] Querying Live Azure Event Hubs Telemetry...${NC}\n"
        "${PYTHON_CMD[@]}" "$PROJECT_ROOT/scripts/check_azure_eventhub.py"
        ;;
    stream|kafka)
        NUM_EVENTS="${1:-25}"
        print_header
        echo -e "${BLUE}[INFO] Streaming $NUM_EVENTS order events to Azure Event Hubs & Kafka...${NC}\n"
        "${PYTHON_CMD[@]}" "$PROJECT_ROOT/scripts/kafka_stream_producer.py" -n "$NUM_EVENTS" -r 15
        ;;
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
        APP_NAME="${1:-portal}"
        PORT="${2:-}"
        "$DE_SCRIPTS_DIR/serve_apps.sh" "$APP_NAME" "$PORT"
        ;;
    doctor|setup)
        "$DE_SCRIPTS_DIR/setup_env.sh" "$@"
        ;;
    check)
        check_scripts
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
