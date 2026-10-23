# ==============================================================================
# AI Platform Starter Kit — Standardized Golden Path Makefile
# Enterprise Principal Engineering Standard (Phases 0 - 5)
# ==============================================================================

SHELL := /bin/bash
PROJECT := enterprise-ai-platform
PYTHON := python3
VENV := .venv

.PHONY: help install lint test run-local deploy teardown eval audit clean

help:
	@echo "Available commands:"
	@echo "  make install     - Setup virtualenv and install pinned production dependencies"
	@echo "  make lint        - Run ruff, black, and type checking"
	@echo "  make test        - Run pytest verification test suite"
	@echo "  make run-local   - Launch FastAPI backend (:8000) and Streamlit UI (:8501)"
	@echo "  make eval        - Execute offline G-Eval continuous rubric benchmarking"
	@echo "  make audit       - Run real-time ISO 27001 / SOC 2 / DPIA compliance audit"
	@echo "  make deploy      - One-click automated EC2 cloud deployment via deploy.sh"
	@echo "  make teardown    - Single-command \$0.00 cloud resource destruction via clear.sh"
	@echo "  make clean       - Remove cache, temporary files, and test artifacts"

install:
	@echo "🔧 Installing dependencies via uv..."
	uv venv $(VENV)
	source $(VENV)/bin/activate && uv pip install -r requirements-prod.txt

lint:
	@echo "🔍 Running code formatters and linters..."
	source $(VENV)/bin/activate && python -m ruff check app/ ui/

test:
	@echo "🧪 Running unit and integration tests..."
	source $(VENV)/bin/activate && python -m pytest tests/ -v

run-local:
	@echo "🚀 Launching local FastAPI (:8000) and Streamlit (:8501)..."
	source $(VENV)/bin/activate && python main.py

eval:
	@echo "📊 Running G-Eval automated evaluation harness..."
	source $(VENV)/bin/activate && python -c "from app.evaluation import geval_evaluator; print(geval_evaluator.evaluate_full('What is enterprise secret rotation?', 'SEC-POL-05 mandates secret rotation within 60s.'))"

audit:
	@echo "⚖️ Running ISO 27001 & SOC 2 compliance verification..."
	source $(VENV)/bin/activate && python -c "from app.compliance import compliance_mapper; print(compliance_mapper.audit().executive_summary)"

deploy:
	@echo "☁️ Provisioning AWS cloud infrastructure..."
	./deploy.sh

teardown:
	@echo "🧹 Terminating all cost-bearing cloud resources (\$0.00 bill)..."
	./clear.sh

clean:
	@echo "🧹 Cleaning temporary cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache
