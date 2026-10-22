FROM python:3.12-slim-bookworm

# Pull uv binary from the official image — no pip install needed.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Patch OS-level CVEs, then install system deps required by torch and native packages.
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Layer: install production dependencies only (cached until requirements-prod.txt changes).
COPY requirements-prod.txt .
RUN uv pip install --system --no-cache -r requirements-prod.txt

# Layer: copy source — only invalidates on code changes, not dep changes.
COPY app/ ./app/
COPY ui/ ./ui/

# Expose the port documented in the task definitions and health checks.
EXPOSE 8080

# Run as a non-root user for production hardening.
RUN useradd -m appuser && chown -R appuser /app
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-graceful-shutdown", "5"]
