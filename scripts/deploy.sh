#!/bin/bash

# Gmail Poller Deployment Script for Hetzner
# This script sets up the Gmail poller on a Hetzner server

set -e

# Configuration
PROJECT_NAME="fleetmanager-gmail-poller"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on supported system
check_system() {
    log_info "Checking system compatibility..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    log_info "System compatibility check passed"
}

# Create necessary directories
setup_directories() {
    log_info "Setting up directories..."

    mkdir -p data logs

    # Set proper permissions
    chmod 755 data logs
    chmod 644 .env 2>/dev/null || true

    log_info "Directories created successfully"
}

# Check required files
check_files() {
    log_info "Checking required files..."

    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file not found. Please create .env from .env.example"
        exit 1
    fi

    if [ ! -f "credentials.json" ]; then
        log_error "Gmail credentials file not found. Please place credentials.json in the project root"
        exit 1
    fi

    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        log_error "Docker Compose file not found: $DOCKER_COMPOSE_FILE"
        exit 1
    fi

    log_info "All required files found"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."

    docker-compose build --no-cache

    log_info "Docker image built successfully"
}

# Setup cron job
setup_cron() {
    log_info "Setting up cron job..."

    # Remove existing cron job if any
    (crontab -l 2>/dev/null | grep -v "$PROJECT_NAME" | crontab -) 2>/dev/null || true

    # Add new cron job (run every 5 minutes)
    (crontab -l 2>/dev/null; echo "*/5 * * * * cd $(pwd) && docker-compose run --rm gmail-poller") | crontab -

    log_info "Cron job set up successfully (runs every 5 minutes)"
    log_warn "To verify: crontab -l"
}

# Show status
show_status() {
    log_info "Deployment status:"
    echo "Project: $PROJECT_NAME"
    echo "Location: $(pwd)"
    echo "Cron jobs:"
    crontab -l | grep "$PROJECT_NAME" || echo "No cron jobs found"
}

# Main deployment function
deploy() {
    log_info "Starting deployment of $PROJECT_NAME..."

    check_system
    check_files
    setup_directories
    build_image
    setup_cron
    show_status

    log_info "Deployment completed successfully!"
    log_info "The poller will run every 5 minutes via cron"
    log_info "Check logs in: $(pwd)/logs/"
    log_info "Check output in: $(pwd)/data/emails.json"
}

# Handle command line arguments
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    check)
        check_system
        check_files
        log_info "All checks passed"
        ;;
    build)
        build_image
        ;;
    cron)
        setup_cron
        ;;
    status)
        show_status
        ;;
    test-run)
        log_info "Running poller once for testing..."
        docker-compose run --rm gmail-poller
        ;;
    *)
        echo "Usage: $0 {deploy|check|build|cron|status|test-run}"
        echo "  deploy  - Full deployment (default)"
        echo "  check   - Check system and files"
        echo "  build   - Build Docker image only"
        echo "  cron    - Setup cron job only"
        echo "  status  - Show deployment status"
        echo "  test-run - Run poller once for testing"
        exit 1
        ;;
esac