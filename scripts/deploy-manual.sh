#!/bin/bash
# FleetManager Manual Deployment Script
# Deploys pre-built image from GitHub Container Registry

set -e

echo "🚀 Deploying FleetManager from GitHub Container Registry..."

# Check if we're in the right directory
if [ ! -d "credentials" ]; then
    echo "❌ ERROR: credentials directory not found!"
    echo "Please run this script from the fleetmanager directory"
    echo "or create the credentials directory and add your credentials.json"
    exit 1
fi

# Check required files
if [ ! -f "credentials/credentials.json" ]; then
    echo "❌ ERROR: credentials/credentials.json not found!"
    echo "Please add your OAuth 2.0 credentials to credentials/credentials.json"
    exit 1
fi

# Download latest docker-compose.yml if it doesn't exist
if [ ! -f "docker-compose.yml" ]; then
    echo "📥 Downloading docker-compose.yml..."
    curl -o docker-compose.yml https://raw.githubusercontent.com/Valkozaur/FleetManager/main/docker-compose.yml
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Please create .env file with your API keys, or this deployment will fail"
    echo "See DEPLOYMENT.md for required environment variables"
    exit 1
fi

# Pull and deploy
echo "� Pulling latest image from GitHub Container Registry..."
docker-compose pull

echo "� Starting FleetManager..."
docker-compose down
docker-compose up -d

# Wait for containers to start
echo "⏳ Waiting for container to start..."
sleep 10

# Check deployment status
echo "🔍 Checking deployment status..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ FleetManager is running successfully!"

    # Show logs
    echo ""
    echo "📋 Recent logs:"
    docker-compose logs --tail=20

    # Show container status
    echo ""
    echo "📊 Container status:"
    docker-compose ps

    # Run health check
    echo ""
    echo "🏥 Running health check..."
    if [ -f "scripts/health-check.sh" ]; then
        bash scripts/health-check.sh | head -20
    fi
else
    echo "❌ FleetManager failed to start!"
    echo "📋 Error logs:"
    docker-compose logs --tail=50
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo "💡 Use 'docker-compose logs -f' to follow logs"
echo "💡 Use 'docker-compose down' to stop the application"