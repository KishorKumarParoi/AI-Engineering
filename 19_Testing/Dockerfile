FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Enable bytecode compilation and python optimization for consistent hashing
ENV UV_COMPILE_BYTECODE=1
ENV PYTHONOPTIMIZE=2
ENV UV_LINK_MODE=copy

# Set Python Path to include the src directory for imports
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Copy only dependencies first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies with uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Copy the rest of the application code
COPY src ./src
COPY app.py ./
COPY templates ./templates
COPY config ./config

# Set Path to use the virtual environment's Python and pip
ENV PATH="/app/.venv/bin:$PATH"

# Create non-root user and switch to it with secure permissions
RUN addgroup --system app && \
    adduser --system --ingroup app app && \
    chown -R app:app /app && \
    mkdir -p /home/app && \
    chown -R app:app /home/app && \
    mkdir -p /home/app/.streamlit && \
    mkdir -p /home/app/.streamlit/data && \
    mkdir -p /home/app/.streamlit/cache && \
    chown -R app:app /home/app/.streamlit

# Set home directory for the app user and switch to it
ENV HOME=/home/app
# WORKDIR /home/app
USER app

# Expose the port Streamlit runs on
EXPOSE 8501

# Run the Streamlit app with the virtual environment's Python
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]