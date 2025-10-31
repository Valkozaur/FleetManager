# syntax=docker/dockerfile:1.4

# Stage 1: Builder
FROM python:3.13.7-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.7.8 /uv /uvx /bin/


# Stage 2: Runtime
FROM python:3.13.7-slim AS runtime

# Install uv
COPY --from=builder /bin/uv /bin/uv
COPY --from=builder /bin/uvx /bin/uvx

# Create a non-root user
RUN groupadd -r appuser --gid=1000 && \
    useradd -r -g appuser --uid=1000 --home-dir=/app --shell=/sbin/nologin appuser

WORKDIR /app

# Create a virtual environment in the project root
RUN python -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"
ENV UV_LINK_MODE=copy

# Copy project definition
COPY pyproject.toml uv.lock ./

# Install dependencies with cache mount
# This requires BuildKit to be enabled.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-cache-dir --all-extras --no-install-project

# Copy application code
COPY --chown=appuser:appuser services/email-processor/src ./src
COPY --chown=appuser:appuser services/email-processor/main.py .
COPY --chown=appuser:appuser database ./database

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-cache-dir --all-extras

# Set environment variables
ENV PYTHONPATH=/app

RUN mkdir /app/data && chown appuser:appuser /app/data

USER appuser

# Set the default command
CMD ["python", "main.py"]