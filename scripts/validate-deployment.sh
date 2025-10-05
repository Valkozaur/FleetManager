#!/bin/bash
# Validate deployment prerequisites before deploying
# Run this script on the Hetzner server to check if everything is ready

set -e

echo "🔍 Validating FleetManager deployment prerequisites..."

ERRORS=0
WARNINGS=0

# Check if deployment directory exists
if [ ! -d ~/fleetmanager ]; then
    echo "❌ ERROR: ~/fleetmanager directory does not exist"
    echo "   Run: mkdir -p ~/fleetmanager"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Deployment directory exists"
fi

# Check if credentials directory exists
if [ ! -d ~/fleetmanager/credentials ]; then
    echo "❌ ERROR: ~/fleetmanager/credentials directory does not exist"
    echo "   Run: mkdir -p ~/fleetmanager/credentials"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Credentials directory exists"
fi

# Check if credentials.json exists
if [ ! -f ~/fleetmanager/credentials/credentials.json ]; then
    echo "❌ ERROR: credentials.json not found"
    echo "   Copy your OAuth 2.0 credentials from Google Cloud Console"
    echo "   to ~/fleetmanager/credentials/credentials.json"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ credentials.json found"
    
    # Validate it's valid JSON
    if ! cat ~/fleetmanager/credentials/credentials.json | python3 -m json.tool > /dev/null 2>&1; then
        echo "❌ ERROR: credentials.json is not valid JSON"
        ERRORS=$((ERRORS + 1))
    else
        echo "✅ credentials.json is valid JSON"
    fi
fi

# Check if data directory exists
if [ ! -d ~/fleetmanager/data ]; then
    echo "⚠️  WARNING: data directory does not exist, creating..."
    mkdir -p ~/fleetmanager/data
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ Data directory exists"
fi

# Check for token files
if [ ! -f ~/fleetmanager/data/token.json ]; then
    echo "⚠️  WARNING: Gmail token (token.json) not found"
    echo "   The application will attempt OAuth flow on first run"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ Gmail token found"
fi

if [ ! -f ~/fleetmanager/data/token_sheets.json ]; then
    echo "⚠️  WARNING: Google Sheets token (token_sheets.json) not found"
    echo "   The application will attempt OAuth flow on first run"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ Google Sheets token found"
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ ERROR: Docker is not installed"
    echo "   Run: curl -fsSL https://get.docker.com | sh"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Docker is installed ($(docker --version))"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ ERROR: Docker Compose is not installed"
    echo "   Run setup-server.sh to install Docker Compose"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Docker Compose is installed ($(docker-compose --version))"
fi

# Check if user can run Docker without sudo
if ! docker ps &> /dev/null; then
    echo "⚠️  WARNING: Cannot run Docker commands without sudo"
    echo "   Run: sudo usermod -aG docker $USER && newgrp docker"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ Can run Docker without sudo"
fi

# Check disk space
AVAILABLE_SPACE=$(df -h ~ | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "${AVAILABLE_SPACE%.*}" -lt 5 ]; then
    echo "⚠️  WARNING: Low disk space (${AVAILABLE_SPACE}GB available)"
    echo "   Recommend at least 5GB free space"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ Sufficient disk space (${AVAILABLE_SPACE}GB available)"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ All checks passed! Ready to deploy."
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  Validation completed with $WARNINGS warning(s)"
    echo "You can proceed with deployment, but review the warnings above."
    exit 0
else
    echo "❌ Validation failed with $ERRORS error(s) and $WARNINGS warning(s)"
    echo "Please fix the errors above before deploying."
    exit 1
fi
