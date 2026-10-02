# ==============================================================================
# Makefile: Developer Automation & Standard Tooling
# Standard: Senior Staff / Lead Data Engineer Standard
# ==============================================================================

.PHONY: help check test test-conn test-de test-ai test-orch de de-debug de-snapshot de-core de-ai ai ai-enrich ai-embed astro-start astro-stop astro-ps astro-trigger sql rag doctor clean

SHELL := /bin/bash

# Default target
all: help

help:
	@echo ""
	@echo "=========================================================="
	@echo "   ZOMATO AI DATA PLATFORM - DEVELOPER WORKFLOW CLI       "
	@echo "=========================================================="
	@echo ""
	@echo "Quality & Testing:"
	@echo "  make check          Audit and validate all automation scripts in scripts/data-engineering/"
	@echo "  make test           Execute master test runner (Scorecard across all 4 suites)"
	@echo "  make test-conn      Test Snowflake connection, role, and medallion schemas"
	@echo "  make test-de        Test Snowflake Medallion layers (Bronze, Silver, Gold, SCD2)"
	@echo "  make test-ai        Test OpenAI embeddings, RAG search & SQL guardrails"
	@echo "  make test-orch      Test Airflow DAG syntax, tasks, and container health"
	@echo ""
	@echo "Data Engineering:"
	@echo "  make de             Execute complete Medallion pipeline (debug -> snapshot -> core -> ai)"
	@echo "  make de-debug       Test dbt connection to Snowflake warehouse"
	@echo "  make de-snapshot    Run SCD Type 2 dimension snapshots"
	@echo "  make de-core        Build Silver views and Gold dimension/fact tables"
	@echo "  make de-ai          Build Gold AI review insights mart"
	@echo ""
	@echo "AI & Intelligence:"
	@echo "  make ai             Run full AI pipeline (enrichment -> embeddings -> dbt ai marts)"
	@echo "  make ai-enrich      Run OpenAI LLM customer review enrichment"
	@echo "  make ai-embed       Pre-compute/refresh 1536-dim vector embeddings for RAG"
	@echo ""
	@echo "Orchestration (Airflow):"
	@echo "  make astro-start    Start Astronomer Airflow local containers (Webserver on :8080)"
	@echo "  make astro-stop     Stop Astronomer Airflow local containers"
	@echo "  make astro-ps       Check status of running Airflow services"
	@echo "  make astro-trigger  Trigger execution of the 'zomato_batch' DAG"
	@echo ""
	@echo "Application Serving:"
	@echo "  make sql            Launch Text-to-SQL Analytics Assistant (Streamlit on :8501)"
	@echo "  make rag            Launch Semantic Reviews RAG Chat (Streamlit on :8502)"
	@echo ""
	@echo "Environment & Maintenance:"
	@echo "  make doctor         Verify system dependencies, environment variables and sync venv"
	@echo "  make clean          Clean build caches, bytecode, and dbt artifacts"
	@echo ""

check:
	@./run.sh check

test:
	@./test_connection.py

test-conn:
	@./test_connection.py --suite conn

test-de:
	@./test_connection.py --suite de

test-ai:
	@./test_connection.py --suite ai

test-orch:
	@./test_connection.py --suite orch

de:
	@./scripts/data-engineering/data_engineering.sh all

de-debug:
	@./scripts/data-engineering/data_engineering.sh debug

de-snapshot:
	@./scripts/data-engineering/data_engineering.sh snapshot

de-core:
	@./scripts/data-engineering/data_engineering.sh core

de-ai:
	@./scripts/data-engineering/data_engineering.sh ai

ai:
	@./scripts/data-engineering/ai_pipeline.sh all

ai-enrich:
	@./scripts/data-engineering/ai_pipeline.sh enrich

ai-embed:
	@./scripts/data-engineering/ai_pipeline.sh embed

astro-start:
	@./scripts/data-engineering/orchestration.sh start

astro-stop:
	@./scripts/data-engineering/orchestration.sh stop

astro-ps:
	@./scripts/data-engineering/orchestration.sh status

astro-trigger:
	@./scripts/data-engineering/orchestration.sh trigger

sql:
	@./scripts/data-engineering/serve_apps.sh sql

rag:
	@./scripts/data-engineering/serve_apps.sh rag

doctor:
	@./scripts/data-engineering/setup_env.sh

clean:
	@echo "Cleaning cache files and build artifacts..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf zomato/target zomato/dbt_packages 2>/dev/null || true
	@echo "Clean completed!"
