#!/bin/bash
# FleetManager Manual Deployment Script

set -e

echo "🚀 Manual deployment of FleetManager..."

# Run validation first
if [ -f "scripts/validate-deployment.sh" ]; then
    echo "🔍 Running pre-deployment validation..."
    if ! bash scripts/validate-deployment.sh; then
        echo "❌ Validation failed. Please fix issues before deploying."
        exit 1
    fi
fi

# Check required files
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and configure your settings"
    exit 1
fi

if [ ! -f "credentials/credentials.json" ]; then
    echo "❌ credentials/credentials.json not found!"
    echo "Please download OAuth 2.0 credentials from Google Cloud Console"
    exit 1
fi

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Build and deploy
echo "🐳 Building and deploying Docker containers..."
docker-compose down
docker-compose pull
docker-compose up -d

# Wait for containers to start
echo "⏳ Waiting for containers to start..."
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
echo "💡 Use 'bash scripts/health-check.sh' to check system health"