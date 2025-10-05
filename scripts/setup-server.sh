#!/bin/bash
# FleetManager Hetzner Server Setup Script

set -e

echo "🚀 Setting up FleetManager on Hetzner server..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "📦 Installing required packages..."
sudo apt install -y curl wget git htop iotop ncdu mailutils

# Install Docker and Docker Compose
echo "🐳 Installing Docker and Docker Compose..."
if ! command -v docker &> /dev/null; then
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
else
    echo "Docker already installed"
fi

if ! command -v docker-compose &> /dev/null; then
    # Install Docker Compose standalone binary (v2)
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose v2 installed at /usr/local/bin/docker-compose"
else
    echo "Docker Compose already installed"
fi

# Create FleetManager directory
echo "📁 Creating FleetManager directory..."
mkdir -p ~/fleetmanager
cd ~/fleetmanager

# Create credentials directory
echo "🔐 Creating credentials directory..."
mkdir -p credentials

# Set up basic firewall (optional)
echo "🔥 Setting up basic firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# Set up logrotate for FleetManager
echo "📝 Setting up log rotation..."
if [ -f "scripts/setup-logrotate.sh" ]; then
    bash scripts/setup-logrotate.sh
fi

echo "✅ Server setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Copy your Google OAuth credentials.json to ~/fleetmanager/credentials/"
echo "2. Generate Gmail API tokens (see authentication docs)"
echo "3. Set up GitHub Secrets for CI/CD deployment"
echo "4. Run 'bash scripts/validate-deployment.sh' to check setup"
echo "5. Run 'docker-compose up -d' to start the application"
echo "6. Run 'bash scripts/setup-cron.sh' to set up automated execution"