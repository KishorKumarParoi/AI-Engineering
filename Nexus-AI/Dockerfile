# ──────────────────────────────────────────────────────────────────
# Nexus-AI: Multi-Stage Production Dockerfile
# ──────────────────────────────────────────────────────────────────
# Stage 1: Build dependencies (cached for fast rebuilds)
# Stage 2: Runtime image (slim, no dev tools)
# Final image: ~350MB (vs ~1.2GB without multi-stage)
# ──────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (layer caching)
COPY pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install \
    pandas pyarrow duckdb scikit-learn joblib fastapi uvicorn numpy

# ── Stage 2: Runtime ─────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL maintainer="Nexus-AI Team <team@nexus-ai.dev>"
LABEL version="1.0.0"
LABEL description="Nexus-AI Enterprise Lakehouse + MLOps Platform"

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY etl/ ./etl/
COPY mlops/ ./mlops/
COPY agents/ ./agents/
COPY data/generators/ ./data/generators/
COPY data/schemas/ ./data/schemas/

# Create data directories
RUN mkdir -p data/raw data/bronze data/silver data/gold \
    mlops/artifacts mlops/configs/grafana_dashboards

# Copy configs
COPY pyproject.toml ./

# Security: Non-root user
RUN groupadd -r nexus && useradd -r -g nexus -s /bin/bash nexus && \
    chown -R nexus:nexus /app
USER nexus

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import pandas; import duckdb; print('healthy')" || exit 1

# Default: run the ETL pipeline
ENV PYTHONPATH=/app
CMD ["python", "-m", "etl.pipeline", "--provider=local", "--input-dir=data/raw", "--data-dir=data"]
