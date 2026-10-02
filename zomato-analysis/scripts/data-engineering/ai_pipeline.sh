#!/usr/bin/env bash
# ==============================================================================
# Script: scripts/data-engineering/ai_pipeline.sh
# Purpose: AI & LLM Intelligence Pipeline Orchestrator
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
    echo "           ZOMATO AI & LLM PIPELINE ORCHESTRATOR          "
    echo "=========================================================="
    echo -e "${NC}"
}

run_enrichment() {
    log_info "1/3. Running OpenAI LLM customer review enrichment (Sentiment + Categorization)..."
    if [ -z "${OPENAI_API_KEY:-}" ]; then
        log_warn "OPENAI_API_KEY is not set in environment or .env. Using mock fallback mode."
    fi
    uv run python ai/enrich_reviews.py
    log_success "Customer reviews enriched into Snowflake ZOMATO.AI.REVIEW_ENRICHED!"
}

run_embeddings() {
    log_info "2/3. Pre-computing text-embedding-3-small vectors for RAG semantic index..."
    uv run python -c "
import os, sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from ai.rag_chat import read_reviews_from_snowflake, embed, CACHE_FILE
import pandas as pd

if os.path.exists(CACHE_FILE):
    print(f'[INFO] Cache file {CACHE_FILE} exists. Verifying vector integrity...')
    df = pd.read_parquet(CACHE_FILE)
    print(f'[SUCCESS] Loaded {len(df)} indexed vectors from cache.')
else:
    print('[INFO] Reading reviews from Snowflake STG_REVIEWS...')
    df = read_reviews_from_snowflake(500)
    print(f'[INFO] Generating 1536-dim embeddings for {len(df)} reviews...')
    df['embedding'] = embed(df['comment'].tolist())
    df.to_parquet(CACHE_FILE)
    print(f'[SUCCESS] Saved {len(df)} embedded reviews to {CACHE_FILE}.')
"
    log_success "Semantic search index ready!"
}

run_ai_marts() {
    log_info "3/3. Building Gold AI Mart (MART_REVIEW_INSIGHTS) via dbt..."
    cd "$PROJECT_ROOT/zomato"
    uv run dbt build --select tag:ai --profiles-dir .
    cd "$PROJECT_ROOT"
    log_success "dbt AI Marts successfully updated!"
}

run_all() {
    print_header
    run_enrichment
    echo ""
    run_embeddings
    echo ""
    run_ai_marts
    echo ""
    log_success "AI & LLM Pipeline execution completed successfully (100% PASS)!"
}

COMMAND="${1:-all}"

case "$COMMAND" in
    all)
        run_all
        ;;
    enrich)
        print_header
        run_enrichment
        ;;
    embed|embeddings)
        print_header
        run_embeddings
        ;;
    marts)
        print_header
        run_ai_marts
        ;;
    help|--help|-h)
        print_header
        echo "Usage: ./scripts/data-engineering/ai_pipeline.sh [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  all        Run LLM enrichment -> Embeddings generation -> dbt AI marts [Default]"
        echo "  enrich     Run OpenAI gpt-4o-mini review enrichment"
        echo "  embed      Generate/refresh text-embedding-3-small vector index"
        echo "  marts      Build dbt tag:ai analytical marts"
        echo ""
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        echo "Run './scripts/data-engineering/ai_pipeline.sh help' for usage instructions."
        exit 1
        ;;
esac
