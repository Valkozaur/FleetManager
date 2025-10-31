# Use a slim Python image
FROM python:3.13-slim

# Set the working directory
WORKDIR /app/database

# Install uv for package management
COPY --from=ghcr.io/astral-sh/uv:0.7.8 /uv /usr/local/bin/

# Copy the project files
COPY . /app

# Install dependencies
RUN uv pip install --no-cache-dir --system /app/database

# Set the python path
ENV PYTHONPATH=/app

# Set the entrypoint to alembic
ENTRYPOINT ["alembic"]
