#!/bin/bash
# Health monitoring script for FleetManager
# Run this periodically to check system and application health

set -e

# Configuration
DEPLOY_DIR="$HOME/fleetmanager"
LOG_FILE="$DEPLOY_DIR/logs/health.log"
ALERT_EMAIL=""  # Set this to receive alerts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

# Alert function
alert() {
    local message="$1"
    log "🚨 ALERT: $message"

    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "FleetManager Alert" "$ALERT_EMAIL" 2>/dev/null || true
    fi
}

# Check function
check() {
    local name="$1"
    local command="$2"
    local critical="${3:-false}"

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name: OK${NC}"
        return 0
    else
        if [ "$critical" = "true" ]; then
            echo -e "${RED}❌ $name: FAILED${NC}"
            alert "$name check failed"
            return 1
        else
            echo -e "${YELLOW}⚠️  $name: WARNING${NC}"
            return 0
        fi
    fi
}

log "🏥 Starting FleetManager health check..."

# Change to deployment directory
cd "$DEPLOY_DIR" || {
    alert "Cannot access deployment directory $DEPLOY_DIR"
    exit 1
}

# System health checks
echo "🔍 System Health Checks:"
check "Disk space (>1GB free)" "df / | awk 'NR==2 {exit(\$4>1048576)}'" true
check "Memory usage (<90%)" "free | awk 'NR==2 {exit(\$3/\$2*100<90)}'" true
check "Docker daemon" "docker info" true

# Application health checks
echo ""
echo "🔍 Application Health Checks:"
check "Container running" "docker-compose ps | grep -q 'Up'" true
check "Container healthy" "docker-compose ps | grep -q 'healthy'" false

# Check container logs for errors in last hour
if docker-compose logs --since=1h 2>&1 | grep -qi "error\|exception\|failed"; then
    echo -e "${YELLOW}⚠️  Recent errors found in logs${NC}"
    log "Recent errors found in container logs"
else
    echo -e "${GREEN}✅ No recent errors in logs${NC}"
fi

# Check if application processed emails recently
if [ -f "data/last_check.txt" ]; then
    LAST_CHECK=$(cat data/last_check.txt)
    LAST_CHECK_TIME=$(date -d "$LAST_CHECK" +%s 2>/dev/null || echo 0)
    CURRENT_TIME=$(date +%s)
    HOURS_SINCE_CHECK=$(( (CURRENT_TIME - LAST_CHECK_TIME) / 3600 ))

    if [ $HOURS_SINCE_CHECK -gt 2 ]; then
        echo -e "${YELLOW}⚠️  No email processing in ${HOURS_SINCE_CHECK} hours${NC}"
        log "No email processing activity in ${HOURS_SINCE_CHECK} hours"
    else
        echo -e "${GREEN}✅ Email processing active (last: $LAST_CHECK)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No last_check.txt file found${NC}"
fi

# Check token files exist and are recent
echo ""
echo "🔍 Authentication Health Checks:"
check "Gmail token exists" "[ -f data/token.json ]" false
check "Sheets token exists" "[ -f data/token_sheets.json ]" false

# Check token file ages (should be updated regularly)
if [ -f "data/token.json" ]; then
    TOKEN_AGE=$(($(date +%s) - $(stat -c %Y data/token.json 2>/dev/null || date +%s)))
    DAYS_OLD=$((TOKEN_AGE / 86400))
    if [ $DAYS_OLD -gt 30 ]; then
        echo -e "${YELLOW}⚠️  Gmail token is ${DAYS_OLD} days old${NC}"
    fi
fi

# Network connectivity check
echo ""
echo "🔍 Network Health Checks:"
check "Internet connectivity" "ping -c 1 8.8.8.8" true
check "Gmail connectivity" "ping -c 1 gmail.com" false
check "Google APIs" "curl -s --max-time 5 https://www.googleapis.com > /dev/null" false

# Performance metrics
echo ""
echo "📊 Performance Metrics:"
CONTAINER_STATS=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" fleetmanager 2>/dev/null | tail -1)
if [ -n "$CONTAINER_STATS" ]; then
    echo "Container stats: $CONTAINER_STATS"
    log "Container stats: $CONTAINER_STATS"
fi

# Check for zombie processes
ZOMBIE_COUNT=$(ps aux | awk '{print $8}' | grep -c 'Z' || echo 0)
if [ "$ZOMBIE_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $ZOMBIE_COUNT zombie processes found${NC}"
    log "$ZOMBIE_COUNT zombie processes found"
fi

log "🏥 Health check completed"
echo ""
echo "📋 Full log available at: $LOG_FILE"