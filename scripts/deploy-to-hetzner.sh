#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# FleetManager - Hetzner Deployment Script
#
# This script handles secure deployment to Hetzner servers by:
# 1. Temporarily adding GitHub Actions runner IP to Hetzner firewall
# 2. Creating .env.production from GitHub Secrets
# 3. SSHing into the server to pull and deploy new Docker images
# 4. Removing the IP from the firewall after deployment
#
# Required environment variables:
#   HETZNER_HOST              - Server hostname or IP
#   HETZNER_USER              - SSH user (default: root)
#   HETZNER_FIREWALL_TOKEN    - Hetzner Cloud API token
#   HETZNER_FIREWALL_ID       - Hetzner firewall ID
#   IMAGE_TAG                 - Docker image tag to deploy (optional)
#   GOOGLE_GEMINI_API_KEY     - Gemini API key
#   GOOGLE_SHEETS_SPREADSHEET_ID - Google Sheets spreadsheet ID
#   GOOGLE_MAPS_API_KEY       - Google Maps API key (optional)
#   GMAIL_CHECK_INTERVAL      - Gmail check interval (default: 300)
#   LOG_LEVEL                 - Log level (default: INFO)
###############################################################################

# Color output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Configuration
readonly HETZNER_HOST="${HETZNER_HOST:?Error: HETZNER_HOST is required}"
readonly HETZNER_USER="${HETZNER_USER:-root}"
readonly HETZNER_FIREWALL_TOKEN="${HETZNER_FIREWALL_TOKEN:?Error: HETZNER_FIREWALL_TOKEN is required}"
readonly HETZNER_FIREWALL_ID="${HETZNER_FIREWALL_ID:?Error: HETZNER_FIREWALL_ID is required}"
readonly IMAGE_TAG="${IMAGE_TAG:-latest}"
readonly DEPLOYMENT_DIR="/opt/fleetmanager"
readonly API_BASE="https://api.hetzner.cloud/v1"

# Application configuration
readonly GOOGLE_GEMINI_API_KEY="${GOOGLE_GEMINI_API_KEY:?Error: GOOGLE_GEMINI_API_KEY is required}"
readonly GOOGLE_SHEETS_SPREADSHEET_ID="${GOOGLE_SHEETS_SPREADSHEET_ID:?Error: GOOGLE_SHEETS_SPREADSHEET_ID is required}"
readonly GOOGLE_MAPS_API_KEY="${GOOGLE_MAPS_API_KEY:-}"
readonly GMAIL_CHECK_INTERVAL="${GMAIL_CHECK_INTERVAL:-300}"
readonly LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Track whether we added a rule (for cleanup)
FIREWALL_RULE_ADDED=false
CURRENT_IP=""

###############################################################################
# Helper Functions
###############################################################################

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Get current public IP of the GitHub Actions runner
get_current_ip() {
    local ip
    ip=$(curl -s https://api.ipify.org || curl -s https://ifconfig.me || curl -s https://icanhazip.com)
    
    if [[ -z "$ip" ]]; then
        log_error "Failed to determine public IP address"
        return 1
    fi
    
    echo "$ip"
}

# Add IP to Hetzner firewall
add_firewall_rule() {
    local ip="$1"
    log_info "Adding IP $ip to Hetzner firewall (ID: $HETZNER_FIREWALL_ID)"
    
    local response
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Authorization: Bearer $HETZNER_FIREWALL_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"rules\": [
                {
                    \"direction\": \"in\",
                    \"port\": \"22\",
                    \"protocol\": \"tcp\",
                    \"source_ips\": [\"${ip}/32\"],
                    \"description\": \"GitHub Actions - $(date -u +%Y-%m-%dT%H:%M:%SZ)\"
                }
            ]
        }" \
        "$API_BASE/firewalls/$HETZNER_FIREWALL_ID/actions/set_rules")
    
    local http_code
    http_code=$(echo "$response" | tail -n1)
    local body
    body=$(echo "$response" | sed '$d')
    
    if [[ "$http_code" -ge 200 && "$http_code" -lt 300 ]]; then
        log_info "Firewall rule added successfully"
        FIREWALL_RULE_ADDED=true
        # Wait for firewall rule to propagate
        sleep 5
        return 0
    else
        log_error "Failed to add firewall rule (HTTP $http_code)"
        log_error "Response: $body"
        return 1
    fi
}

# Remove IP from Hetzner firewall
remove_firewall_rule() {
    local ip="$1"
    log_info "Removing IP $ip from Hetzner firewall"
    
    # First, get current firewall rules
    local current_rules
    current_rules=$(curl -s -H "Authorization: Bearer $HETZNER_FIREWALL_TOKEN" \
        "$API_BASE/firewalls/$HETZNER_FIREWALL_ID" | \
        jq -r '.firewall.rules[] | select(.source_ips[] | contains("'$ip'/32") | not)')
    
    # Set rules without the GitHub Actions IP
    local response
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Authorization: Bearer $HETZNER_FIREWALL_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"rules\": $(curl -s -H "Authorization: Bearer $HETZNER_FIREWALL_TOKEN" \
            "$API_BASE/firewalls/$HETZNER_FIREWALL_ID" | \
            jq '[.firewall.rules[] | select(.source_ips[] | contains("'$ip'/32") | not)]')}" \
        "$API_BASE/firewalls/$HETZNER_FIREWALL_ID/actions/set_rules")
    
    local http_code
    http_code=$(echo "$response" | tail -n1)
    
    if [[ "$http_code" -ge 200 && "$http_code" -lt 300 ]]; then
        log_info "Firewall rule removed successfully"
    else
        log_warn "Failed to remove firewall rule (HTTP $http_code) - manual cleanup may be needed"
    fi
}

# Cleanup function (called on exit)
cleanup() {
    local exit_code=$?
    
    if [[ "$FIREWALL_RULE_ADDED" == "true" && -n "$CURRENT_IP" ]]; then
        log_info "Performing cleanup..."
        remove_firewall_rule "$CURRENT_IP" || true
    fi
    
    if [[ $exit_code -eq 0 ]]; then
        log_info "Deployment completed successfully!"
    else
        log_error "Deployment failed with exit code $exit_code"
    fi
    
    exit $exit_code
}

# Create .env.production file on server
create_env_file() {
    log_info "Creating .env.production from GitHub Secrets"
    
    # Create environment file content
    local env_content
    env_content=$(cat <<EOF
# Production Environment Configuration
# Auto-generated from GitHub Secrets on $(date -u +%Y-%m-%dT%H:%M:%SZ)
# DO NOT EDIT MANUALLY - Changes will be overwritten on next deployment

# =============================================================================
# Gmail Configuration
# =============================================================================
GMAIL_CREDENTIALS_FILE=/app/credentials/credentials.json
GMAIL_CHECK_INTERVAL=${GMAIL_CHECK_INTERVAL}

# =============================================================================
# Google Gemini AI Configuration
# =============================================================================
GOOGLE_GEMINI_API_KEY=${GOOGLE_GEMINI_API_KEY}

# =============================================================================
# Google Sheets Configuration
# =============================================================================
GOOGLE_SHEETS_SPREADSHEET_ID=${GOOGLE_SHEETS_SPREADSHEET_ID}

# =============================================================================
# Google Maps Configuration
# =============================================================================
GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}

# =============================================================================
# Application Configuration
# =============================================================================
LOG_LEVEL=${LOG_LEVEL}
TEST_MODE=false
DATA_DIR=/app/data

# =============================================================================
# Docker Configuration
# =============================================================================
COMPOSE_PROJECT_NAME=fleetmanager
EOF
)
    
    # Write to server
    ssh -o StrictHostKeyChecking=no \
        -o ConnectTimeout=10 \
        "$HETZNER_USER@$HETZNER_HOST" \
        "cat > ${DEPLOYMENT_DIR}/.env.production && chmod 600 ${DEPLOYMENT_DIR}/.env.production" <<< "$env_content"
    
    log_info "Environment file created successfully"
}

# Deploy to server via SSH
deploy_to_server() {
    log_info "Connecting to $HETZNER_USER@$HETZNER_HOST"
    
    # Create deployment commands
    local deploy_commands
    deploy_commands=$(cat <<'EOF'
set -euo pipefail

cd /opt/fleetmanager || exit 1

echo "Logging in to GitHub Container Registry..."
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_ACTOR" --password-stdin

echo "Pulling latest images..."
docker-compose -f infrastructure/docker/docker-compose.prod.yml pull email-processor

echo "Stopping services..."
docker-compose -f infrastructure/docker/docker-compose.prod.yml stop email-processor

echo "Starting services with new image..."
docker-compose -f infrastructure/docker/docker-compose.prod.yml up -d email-processor

echo "Removing old images..."
docker image prune -f

echo "Checking service status..."
docker-compose -f infrastructure/docker/docker-compose.prod.yml ps email-processor

echo "Deployment completed!"
EOF
)
    
    # Execute deployment over SSH
    ssh -o StrictHostKeyChecking=no \
        -o ConnectTimeout=10 \
        -o ServerAliveInterval=60 \
        "$HETZNER_USER@$HETZNER_HOST" \
        "GITHUB_TOKEN=$GITHUB_TOKEN GITHUB_ACTOR=$GITHUB_ACTOR bash -s" <<< "$deploy_commands"
}

###############################################################################
# Main Execution
###############################################################################

main() {
    log_info "Starting deployment to Hetzner server..."
    log_info "Target: $HETZNER_USER@$HETZNER_HOST"
    log_info "Image: $IMAGE_TAG"
    
    # Set up cleanup trap
    trap cleanup EXIT INT TERM
    
    # Get current IP
    CURRENT_IP=$(get_current_ip)
    log_info "Current runner IP: $CURRENT_IP"
    
    # Add firewall rule
    add_firewall_rule "$CURRENT_IP"
    
    # Create environment file
    create_env_file
    
    # Deploy to server
    deploy_to_server
    
    log_info "Deployment process completed!"
}

# Run main function
main "$@"