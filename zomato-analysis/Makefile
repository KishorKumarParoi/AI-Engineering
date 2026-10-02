# ==============================================================================
# Makefile: Developer Automation & Standard Tooling
# Standard: Senior Staff / Lead Data Engineer Standard
# ==============================================================================

.PHONY: help check test test-de test-ai test-orch de de-debug de-snapshot de-core de-ai ai ai-enrich ai-embed astro-start astro-stop astro-ps astro-trigger sql rag doctor clean

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
	@echo "  make check          Audit and validate all automation scripts in scripts/"
	@echo "  make test           Execute master test runner (Scorecard across all 3 suites)"
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
	@./test_conn.py

test-de:
	@./test_conn.py --suite de

test-ai:
	@./test_conn.py --suite ai

test-orch:
	@./test_conn.py --suite orch

de:
	@./scripts/data_engineering.sh all

de-debug:
	@./scripts/data_engineering.sh debug

de-snapshot:
	@./scripts/data_engineering.sh snapshot

de-core:
	@./scripts/data_engineering.sh core

de-ai:
	@./scripts/data_engineering.sh ai

ai:
	@./scripts/ai_pipeline.sh all

ai-enrich:
	@./scripts/ai_pipeline.sh enrich

ai-embed:
	@./scripts/ai_pipeline.sh embed

astro-start:
	@./scripts/orchestration.sh start

astro-stop:
	@./scripts/orchestration.sh stop

astro-ps:
	@./scripts/orchestration.sh status

astro-trigger:
	@./scripts/orchestration.sh trigger

sql:
	@./scripts/serve_apps.sh sql

rag:
	@./scripts/serve_apps.sh rag

doctor:
	@./scripts/setup_env.sh

clean:
	@echo "Cleaning cache files and build artifacts..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf zomato/target zomato/dbt_packages 2>/dev/null || true
	@echo "Clean completed!"
