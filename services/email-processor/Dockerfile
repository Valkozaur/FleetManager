# syntax=docker/dockerfile:1.4

# Use the official uv image as a builder
FROM ghcr.io/astral-sh/uv:0.7.8-python3.13-bookworm as builder

WORKDIR /app

# Copy project files for the email-processor service
COPY services/email-processor/pyproject.toml ./pyproject.toml
COPY services/email-processor/uv.lock ./uv.lock

# Build a virtual environment
RUN uv venv

# Install dependencies into the virtual environment
RUN . .venv/bin/activate && uv pip install -r uv.lock

# --- #

# Use a slim Python image for the runtime
FROM python:3.13-slim as runtime

WORKDIR /app

# Create a non-root user
RUN groupadd -r appuser --gid=1000 && \
    useradd -r -g appuser --uid=1000 --home-dir=/app --shell=/sbin/nologin appuser

# Copy the virtual environment from the builder
COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv

# Copy application code
COPY --chown=appuser:appuser services/email-processor/src ./src
COPY --chown=appuser:appuser services/email-processor/main.py .
COPY --chown=appuser:appuser services/database-migration ./database

# Activate the virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

USER appuser

# Set the default command
CMD ["python", "main.py"]