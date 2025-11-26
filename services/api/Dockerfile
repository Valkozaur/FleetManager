# syntax=docker/dockerfile:1.4

# Use the official uv image as a builder
FROM ghcr.io/astral-sh/uv:0.9.0-python3.13-bookworm as builder

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Copy workspace files for dependency resolution
COPY pyproject.toml uv.lock ./
COPY services/database-models ./services/database-models/
COPY services/api ./services/api/

# Install only api package and its dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package api

# --- #

# Use a slim Python image for the runtime
FROM python:3.13-slim as runtime

WORKDIR /app

# Create a non-root user
RUN groupadd -r appuser --gid=1000 && \
    useradd -r -g appuser --uid=1000 --home-dir=/app --shell=/sbin/nologin appuser

# Create directories with proper ownership
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app/logs /app/data

# Copy the virtual environment from the builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy services
COPY --chown=appuser:appuser services/database-models /app/services/database-models
COPY --chown=appuser:appuser services/api /app/services/api

# Activate the virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

USER appuser

WORKDIR /app

# Expose the port
EXPOSE 8000

# Set the default command
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
