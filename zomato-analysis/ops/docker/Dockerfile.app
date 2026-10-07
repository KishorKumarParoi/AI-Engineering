# ==============================================================================
# Dockerfile.app: Production Inference Serving Image
# Purpose: Containerizes the Colorectal Cancer Survival Prediction Flask Service
# ==============================================================================

FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final Lean Runtime Stage
FROM python:3.12-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /install /usr/local

# Create non-root application user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/artifacts/models /app/artifacts/processed /app/logs && \
    chown -R appuser:appuser /app

# Copy application code and templates
COPY application.py /app/application.py
COPY templates/ /app/templates/
COPY static/ /app/static/

USER appuser

ENV PYTHONUNBUFFERED=1 \
    PORT=5000 \
    MODEL_PATH=/app/artifacts/models/model.pkl \
    SCALER_PATH=/app/artifacts/processed/scaler.pkl

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

CMD ["python", "application.py"]
