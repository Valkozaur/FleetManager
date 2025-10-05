#!/bin/bash
# Setup host-level cron for FleetManager
# Run this script on the Hetzner server after deployment

set -e

echo "🕐 Setting up cron job for FleetManager..."

# Create cron job that runs every 5 minutes
CRON_JOB="*/5 * * * * cd ~/fleetmanager && docker-compose run --rm fleetmanager >> ~/fleetmanager/logs/cron.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "fleetmanager"; then
    echo "⚠️  Cron job already exists. Removing old job..."
    crontab -l | grep -v "fleetmanager" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Cron job installed successfully!"
echo "📋 Current crontab:"
crontab -l | grep fleetmanager

echo ""
echo "💡 To view cron logs: tail -f ~/fleetmanager/logs/cron.log"
echo "💡 To remove cron job: crontab -e (then delete the fleetmanager line)"
