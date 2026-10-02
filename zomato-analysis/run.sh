#!/usr/bin/env bash
# ==============================================================================
# Script: run.sh
# Purpose: Master One-Click Orchestration & Management CLI for Zomato AI Platform
# Supports: macOS, Linux (Debian, Ubuntu)
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
NC='\033[0m' # No Color

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# -----------------------------
# Directory Resolution
# -----------------------------
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# -----------------------------
# Load Environment Variables (.env)
# -----------------------------
ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    source <(grep -v '^[[:space:]]*#' "$ENV_FILE" | grep -v '^[[:space:]]*$')
    set +a
fi

# Fallback defaults
SNOWFLAKE_USER_VAL="${SNOWFLAKE_USER:-${SNOWFLAKE_USERNAME:-kkp007}}"
SNOWFLAKE_ROLE_VAL="${SNOWFLAKE_ROLE:-DBT_ROLE}"
SNOWFLAKE_WH_VAL="${SNOWFLAKE_WAREHOUSE:-ZOMATO_WH}"
SNOWFLAKE_DB_VAL="${SNOWFLAKE_DATABASE:-ZOMATO}"
BUCKET_NAME="${S3_BUCKET_NAME:-zomato-dataset-kkp}"
AWS_REGION="${AWS_REGION:-us-east-1}"

print_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "=========================================================="
    echo "        ZOMATO AI DATA ENGINEERING PLATFORM CLI           "
    echo "  S3 -> Snowflake -> dbt Medallion -> Airflow -> OpenAI   "
    echo "=========================================================="
    echo -e "${NC}"
}

# -----------------------------
# Helper Commands
# -----------------------------
run_health_check() {
    log_info "Running comprehensive Snowflake & platform health check..."
    uv run ./test_con.py
}

run_dbt_pipeline() {
    log_info "Running dbt Medallion pipeline (Silver, Gold, Snapshots)..."
    cd "$PROJECT_ROOT/zomato"
    log_info "1. Verifying dbt connection to Snowflake..."
    uv run dbt debug --profiles-dir .
    log_info "2. Executing SCD Type 2 dimension snapshots..."
    uv run dbt snapshot --profiles-dir .
    log_info "3. Building core staging views, dimensions, and incremental facts..."
    uv run dbt build --exclude tag:ai --profiles-dir .
    log_info "4. Building Gold AI Marts..."
    uv run dbt build --select tag:ai --profiles-dir .
    cd "$PROJECT_ROOT"
    log_success "dbt Medallion transformations completed successfully!"
}

run_ai_enrichment() {
    log_info "Running OpenAI LLM customer review enrichment..."
    if [ -z "${OPENAI_API_KEY:-}" ]; then
        log_warn "OPENAI_API_KEY is not set in environment or .env. Using mock/skip mode."
    fi
    uv run python ai/enrich_reviews.py
    log_success "Review enrichment finished!"
}

start_astro_airflow() {
    log_info "Checking Astronomer Airflow local development environment..."
    if ! command -v astro &>/dev/null; then
        log_error "Astro CLI is not installed. Run 'brew install astro' first."
        return 1
    fi
    if astro dev ps 2>/dev/null | grep -q "running"; then
        log_success "Astro Airflow is already running!"
    else
        log_info "Starting Astro dev environment..."
        astro dev start
    fi
    echo ""
    log_success "Airflow Web UI: http://zomato-analysis.localhost:6563 (or http://localhost:8080)"
}

trigger_dag() {
    log_info "Triggering master batch pipeline DAG (zomato_batch)..."
    astro dev run dags trigger zomato_batch
    log_success "DAG 'zomato_batch' triggered! Monitor progress in Airflow UI."
}

launch_rag_app() {
    log_info "Launching Semantic RAG Review Chat application..."
    echo -e "${GREEN}Opening Streamlit at: http://localhost:8501${NC}"
    uv run streamlit run ai/rag_chat.py
}

launch_sql_app() {
    log_info "Launching Natural Language Text-to-SQL Analytics application..."
    echo -e "${GREEN}Opening Streamlit at: http://localhost:8501${NC}"
    uv run streamlit run ai/text_to_sql.py
}

run_all_end_to_end() {
    print_banner
    log_info "STARTING ONE-CLICK COMPLETE END-TO-END EXECUTION..."
    echo ""

    # 1. Health & Connection check
    run_health_check
    echo ""

    # 2. dbt build
    run_dbt_pipeline
    echo ""

    # 3. AI Enrichment
    run_ai_enrichment
    echo ""

    # 4. Airflow check/start
    start_astro_airflow || true
    echo ""

    # 5. Final summary
    log_success "=========================================================="
    log_success "  ALL SYSTEMS OPERATIONAL & PIPELINE EXECUTED CLEANLY!    "
    log_success "=========================================================="
    echo ""
    echo -e "  - ${BOLD}Airflow UI:${NC}    http://zomato-analysis.localhost:6563"
    echo -e "  - ${BOLD}RAG Chat App:${NC}  ./run.sh rag"
    echo -e "  - ${BOLD}Text-to-SQL:${NC}   ./run.sh sql"
    echo -e "  - ${BOLD}Health Check:${NC}  ./run.sh health"
    echo ""
}

# -----------------------------
# CLI Dispatcher
# -----------------------------
COMMAND="${1:-}"

case "$COMMAND" in
    all|"")
        if [ -t 0 ] && [ -z "$COMMAND" ]; then
            print_banner
            echo -e "${BOLD}Select an action to run:${NC}"
            echo "  1) Run Complete Pipeline End-to-End (Health + dbt + AI + Airflow) [Default]"
            echo "  2) Run Snowflake Database Health Check (test_con.py)"
            echo "  3) Run dbt Build & Snapshots (Medallion Layers)"
            echo "  4) Run OpenAI Review Enrichment (ai/enrich_reviews.py)"
            echo "  5) Start Astronomer Airflow dev server"
            echo "  6) Trigger 'zomato_batch' DAG in Airflow"
            echo "  7) Launch Semantic RAG Review Chat (Streamlit)"
            echo "  8) Launch Text-to-SQL Analytics (Streamlit)"
            echo "  q) Quit"
            echo ""
            read -rp "Enter choice [1-8 or q, default=1]: " choice
            choice="${choice:-1}"
            case "$choice" in
                1) run_all_end_to_end ;;
                2) run_health_check ;;
                3) run_dbt_pipeline ;;
                4) run_ai_enrichment ;;
                5) start_astro_airflow ;;
                6) trigger_dag ;;
                7) launch_rag_app ;;
                8) launch_sql_app ;;
                [qQ]) exit 0 ;;
                *) log_error "Invalid choice: $choice"; exit 1 ;;
            esac
        else
            run_all_end_to_end
        fi
        ;;
    health|check)
        print_banner
        run_health_check
        ;;
    dbt)
        print_banner
        run_dbt_pipeline
        ;;
    enrich|ai)
        print_banner
        run_ai_enrichment
        ;;
    astro|airflow)
        print_banner
        start_astro_airflow
        ;;
    trigger)
        print_banner
        trigger_dag
        ;;
    rag)
        print_banner
        launch_rag_app
        ;;
    sql)
        print_banner
        launch_sql_app
        ;;
    help|--help|-h)
        print_banner
        echo "Usage: ./run.sh [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  all         Execute full pipeline (Health Check -> dbt Build -> AI Enrichment -> Airflow)"
        echo "  health      Run Snowflake & platform health check (test_con.py)"
        echo "  dbt         Run dbt debug, snapshots, and full build (Core + AI marts)"
        echo "  enrich      Run OpenAI LLM customer review enrichment"
        echo "  airflow     Check and start Astronomer Airflow local server"
        echo "  trigger     Trigger zomato_batch DAG execution in Airflow"
        echo "  rag         Launch Streamlit Semantic RAG Review Chat"
        echo "  sql         Launch Streamlit Natural Language Text-to-SQL"
        echo ""
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        echo "Run './run.sh help' for usage instructions."
        exit 1
        ;;
esac
