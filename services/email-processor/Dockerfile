# Multi-stage build for optimized production image
# Stage 1: Builder - Install dependencies and compile
FROM python:3.13.7-slim AS builder

# Set build-time environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime - Minimal production image
FROM python:3.13.7-slim AS runtime

# Set runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

# Install runtime dependencies only (if any needed)
# Currently no runtime deps needed beyond Python

# Create non-root user for security
RUN groupadd -r appuser --gid=1000 && \
    useradd -r -g appuser --uid=1000 --home-dir=/app --shell=/sbin/nologin appuser

# Set work directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code with proper ownership
# Copying the whole build context. If `.env.example` is present in the context
# it will be included by the previous COPY; if it's not present (e.g. when
# building with the service folder as the context) create an empty example
# file so the subsequent steps don't fail.
COPY --chown=appuser:appuser . .

# Ensure an example env file exists inside the image. This avoids failing the
# build when the source `.env.example` is outside the build context.
RUN if [ ! -f /app/.env.example ]; then touch /app/.env.example; fi

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs /app/credentials && \
    chown -R appuser:appuser /app && \
    chmod 755 /app/data /app/logs && \
    chmod 700 /app/credentials

# Switch to non-root user
USER appuser

# Add labels for metadata
LABEL org.opencontainers.image.source="https://github.com/Valkozaur/FleetManager"
LABEL org.opencontainers.image.description="FleetManager - Gmail-based logistics order processing"
LABEL org.opencontainers.image.licenses="MIT"

# Health check - verify Python environment and credentials directory
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" && test -d /app/credentials || exit 1

# Default command
CMD ["python", "-u", "src/orders/poller/main.py"]