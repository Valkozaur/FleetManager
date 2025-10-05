#!/bin/bash
# Backup script for FleetManager data
# Run this periodically to backup important data

set -e

BACKUP_DIR="$HOME/fleetmanager-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="fleetmanager_$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

echo "💾 Creating FleetManager backup..."

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup archive
cd ~/fleetmanager

# Stop container temporarily for consistent backup
echo "⏸️  Stopping container for consistent backup..."
docker-compose stop

# Create backup
tar -czf "$BACKUP_PATH.tar.gz" \
    --exclude='logs/*' \
    --exclude='*.log' \
    data/ \
    credentials/ \
    docker-compose.yml \
    .env \
    2>/dev/null || true

# Start container again
echo "▶️  Starting container..."
docker-compose start

# Verify backup was created
if [ -f "$BACKUP_PATH.tar.gz" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_PATH.tar.gz" | cut -f1)
    echo "✅ Backup created successfully: $BACKUP_PATH.tar.gz ($BACKUP_SIZE)"

    # Clean up old backups (keep last 7)
    echo "🧹 Cleaning up old backups..."
    ls -t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null || true

    echo "📋 Available backups:"
    ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "No backups found"
else
    echo "❌ Backup failed!"
    exit 1
fi

echo ""
echo "💡 To restore from backup:"
echo "  cd ~/fleetmanager"
echo "  docker-compose down"
echo "  tar -xzf $BACKUP_PATH.tar.gz"
echo "  docker-compose up -d"