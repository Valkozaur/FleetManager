# Use Python 3.11 slim image for efficiency
FROM python:3.11-slim

# Set metadata
LABEL maintainer="FleetManager"
LABEL description="Gmail Poller for FleetManager"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs && \
    chmod 755 /app/data /app/logs

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Set default configuration
ENV GMAIL_CREDENTIALS_FILE=/app/credentials.json
ENV DATA_DIR=/app/data
ENV LOG_DIR=/app/logs
ENV MAX_EMAILS=10
ENV EMAIL_QUERY=""
ENV LOG_LEVEL=INFO
ENV OUTPUT_FILE=/app/data/emails.json

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app /app/data /app/logs
USER appuser

# Expose health check port (if needed)
EXPOSE 8080

# Health check (simple HTTP server for monitoring)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import http.server; import socketserver; s = socketserver.TCPServer(('', 8080), http.server.SimpleHTTPRequestHandler); s.server_close()" || exit 1

# Default command (can be overridden)
CMD ["python", "src/orders/poller/main.py"]