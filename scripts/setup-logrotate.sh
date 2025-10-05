#!/bin/bash
# Log rotation script for FleetManager
# Run this on the Hetzner server to set up log rotation

set -e

echo "📝 Setting up log rotation for FleetManager..."

# Create logrotate configuration
sudo tee /etc/logrotate.d/fleetmanager > /dev/null << EOF
/app/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 appuser appuser
    postrotate
        docker-compose logs -f fleetmanager > /dev/null 2>&1 || true
    endscript
}

/home/*/fleetmanager/logs/cron.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 $USER $USER
}
EOF

echo "✅ Log rotation configured"
echo "📋 Configuration created at /etc/logrotate.d/fleetmanager"
echo "💡 Logs will be rotated daily, kept for 7 days, and compressed"

# Test logrotate configuration
echo "🔍 Testing logrotate configuration..."
if sudo logrotate -d /etc/logrotate.d/fleetmanager 2>/dev/null; then
    echo "✅ Logrotate configuration is valid"
else
    echo "❌ Logrotate configuration has errors"
    exit 1
fi

echo ""
echo "💡 To manually rotate logs: sudo logrotate -f /etc/logrotate.d/fleetmanager"
echo "💡 To check logrotate status: sudo logrotate -s /var/lib/logrotate/logrotate.status /etc/logrotate.d/fleetmanager"