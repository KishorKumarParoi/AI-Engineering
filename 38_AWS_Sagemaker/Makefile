.PHONY: help install test lint local-sim compile-pipeline api docker-build clean

PYTHON := .venv/bin/python
PIP := .venv/bin/pip
PYTEST := .venv/bin/pytest

help:
	@echo "Available commands:"
	@echo "  make install           Install Python dependencies into .venv"
	@echo "  make test              Run automated pytest test suite"
	@echo "  make local-sim         Run local end-to-end MLOps pipeline simulation"
	@echo "  make compile-pipeline  Compile SageMaker Pipeline DAG into JSON definition"
	@echo "  make api               Start local FastAPI REST serving server (Swagger at :8000/docs)"
	@echo "  make docker-build      Build local Docker container"
	@echo "  make clean             Remove temporary artifacts and caches"

install:
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

test:
	$(PYTEST) -v tests/

local-sim:
	$(PYTHON) src/pipeline/run_pipeline.py --local-simulation

compile-pipeline:
	$(PYTHON) src/pipeline/run_pipeline.py --build-only

api:
	$(PYTHON) src/api/main.py

docker-build:
	docker build -t mobile-price-api:latest -f docker/Dockerfile.local .

clean:
	rm -rf .pytest_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
