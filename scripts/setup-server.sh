#!/bin/bash
# FleetManager Server Setup Script
# Run this once on a fresh Hetzner server with Docker pre-installed
# This script is idempotent - safe to run multiple times

set -e

# Configuration
DEPLOY_DIR="$HOME/fleetmanager"
REPO_URL="https://github.com/Valkozaur/FleetManager"
BACKUP_DIR="$HOME/fleetmanager-backups"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🚀 FleetManager Server Setup"
echo "=============================="
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC}  $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    print_warning "Running as root. It's recommended to run as a regular user."
fi

# Preseed Postfix to avoid interactive config prompts during package installs
# This sets the default to "No configuration" so apt installs won't block on Postfix.
if command -v debconf-set-selections &> /dev/null; then
    echo "Preseeding Postfix to 'No configuration' to avoid interactive prompts..."
    sudo debconf-set-selections <<'DEB'
postfix postfix/main_mailer_type select No configuration
DEB
    print_status "Preseeded Postfix debconf (No configuration)"
fi

# 1. Verify Docker is installed
echo "📦 Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    echo "Since you're using a Hetzner image with Docker, this shouldn't happen."
    echo "If Docker is missing, run: curl -fsSL https://get.docker.com | sh"
    exit 1
fi
print_status "Docker is installed: $(docker --version)"

# 2. Verify Docker Compose is available
echo "📦 Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_warning "Docker Compose not found. Installing..."
    # Install Docker Compose
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_status "Docker Compose installed"
else
    print_status "Docker Compose is available"
fi

# 3. Ensure user can run Docker without sudo
echo "🔐 Checking Docker permissions..."
if ! docker ps &> /dev/null 2>&1; then
    print_warning "Cannot run Docker without sudo. Adding user to docker group..."
    sudo usermod -aG docker $USER
    print_status "Added $USER to docker group"
    print_warning "You'll need to log out and back in for this to take effect"
    print_warning "Or run: newgrp docker"
fi

# 4. Create directory structure
echo "📁 Creating directory structure..."
mkdir -p "$DEPLOY_DIR"/{credentials,data,logs,scripts,backups}
mkdir -p "$BACKUP_DIR"
print_status "Directory structure created at $DEPLOY_DIR"

# 5. Download deployment scripts
echo "📥 Downloading deployment scripts..."
cd "$DEPLOY_DIR"

# Download docker-compose.yml
if [ ! -f "docker-compose.yml" ] || [ "$1" = "--force" ]; then
    curl -fsSL -o docker-compose.yml "$REPO_URL/raw/main/docker-compose.yml"
    print_status "Downloaded docker-compose.yml"
else
    print_warning "docker-compose.yml already exists (use --force to overwrite)"
fi

# Download scripts
SCRIPTS=("health-check.sh" "backup.sh" "deploy-manual.sh" "validate-deployment.sh")
for script in "${SCRIPTS[@]}"; do
    if [ ! -f "scripts/$script" ] || [ "$1" = "--force" ]; then
        curl -fsSL -o "scripts/$script" "$REPO_URL/raw/main/scripts/$script"
        chmod +x "scripts/$script"
        print_status "Downloaded scripts/$script"
    else
        print_warning "scripts/$script already exists (use --force to overwrite)"
    fi
done

# 6. Create systemd service for auto-restart (optional)
echo "🔧 Setting up systemd service..."
SYSTEMD_SERVICE="/etc/systemd/system/fleetmanager.service"

# Choose the appropriate docker-compose command (binary or plugin)
DOCKER_COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD=$(command -v docker-compose)
elif docker compose version &> /dev/null; then
    # Use docker CLI with compose subcommand
    DOCKER_COMPOSE_CMD="$(command -v docker) compose"
else
    # Fallback to expected install location
    DOCKER_COMPOSE_CMD="/usr/local/bin/docker-compose"
fi

if [ ! -f "$SYSTEMD_SERVICE" ]; then
    sudo tee "$SYSTEMD_SERVICE" > /dev/null <<EOF
[Unit]
Description=FleetManager Container
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$DEPLOY_DIR
ExecStart=$DOCKER_COMPOSE_CMD up -d
ExecStop=$DOCKER_COMPOSE_CMD down
User=$USER

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable fleetmanager.service
    print_status "Systemd service created and enabled"
else
    print_warning "Systemd service already exists"
fi

# 7. Setup log rotation
echo "📋 Setting up log rotation..."
LOGROTATE_CONF="/etc/logrotate.d/fleetmanager"

if [ ! -f "$LOGROTATE_CONF" ]; then
    sudo tee "$LOGROTATE_CONF" > /dev/null <<EOF
$DEPLOY_DIR/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 $USER $USER
    sharedscripts
    postrotate
        docker-compose -f $DEPLOY_DIR/docker-compose.yml restart 2>/dev/null || true
    endscript
}
EOF
    print_status "Log rotation configured"
else
    print_warning "Log rotation already configured"
fi

# 8. Setup automated backups (optional)
echo "🔄 Setting up automated backups..."
CRON_BACKUP="0 2 * * * $DEPLOY_DIR/scripts/backup.sh >> $DEPLOY_DIR/logs/backup.log 2>&1"

if ! crontab -l 2>/dev/null | grep -q "backup.sh"; then
    (crontab -l 2>/dev/null; echo "$CRON_BACKUP") | crontab -
    print_status "Daily backup cron job added (runs at 2 AM)"
else
    print_warning "Backup cron job already exists"
fi

# 9. Create .env template
echo "📝 Creating .env template..."
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    cat > "$DEPLOY_DIR/.env.template" <<'EOF'
# FleetManager Environment Variables
# Copy this to .env and fill in your values

# Required: API Keys
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here

# Optional: Configuration
GOOGLE_SHEETS_RANGE_NAME=Sheet1!A:Z
GMAIL_CREDENTIALS_FILE=/app/credentials/credentials.json
DATA_DIR=/app/data
LOG_LEVEL=INFO
TEST_MODE=false
EOF
    print_status "Created .env.template"
    print_warning "You need to create .env file with your actual values"
else
    print_status ".env file already exists"
fi

# 10. Set proper permissions
echo "🔒 Setting permissions..."
chmod 700 "$DEPLOY_DIR/credentials"
chmod 755 "$DEPLOY_DIR/data"
chmod 755 "$DEPLOY_DIR/logs"
chmod +x "$DEPLOY_DIR"/scripts/*.sh
print_status "Permissions set correctly"

# 11. Setup firewall (if UFW is available)
if command -v ufw &> /dev/null; then
    echo "🔥 Checking firewall..."
    if sudo ufw status | grep -q "Status: active"; then
        print_warning "UFW firewall is active. Ensure SSH port is allowed."
    fi
fi

# 12. Verify setup
echo ""
echo "🔍 Verifying setup..."
echo ""

CHECKS_PASSED=0
CHECKS_TOTAL=0

# Check Docker
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if docker ps &> /dev/null; then
    print_status "Docker is working"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    print_error "Docker is not working"
fi

# Check directory structure
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if [ -d "$DEPLOY_DIR/credentials" ] && [ -d "$DEPLOY_DIR/data" ] && [ -d "$DEPLOY_DIR/logs" ]; then
    print_status "Directory structure is correct"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    print_error "Directory structure is incomplete"
fi

# Check scripts
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if [ -x "$DEPLOY_DIR/scripts/health-check.sh" ] && [ -x "$DEPLOY_DIR/scripts/backup.sh" ]; then
    print_status "Scripts are executable"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    print_error "Scripts are not properly installed"
fi

# Check docker-compose.yml
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if [ -f "$DEPLOY_DIR/docker-compose.yml" ]; then
    print_status "docker-compose.yml is present"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    print_error "docker-compose.yml is missing"
fi

echo ""
echo "=============================="
echo "📊 Setup Results: $CHECKS_PASSED/$CHECKS_TOTAL checks passed"
echo ""

if [ $CHECKS_PASSED -eq $CHECKS_TOTAL ]; then
    echo -e "${GREEN}✅ Server setup completed successfully!${NC}"
    echo ""
    echo "📋 Next Steps:"
    echo ""
    echo "1. Add your Google OAuth credentials:"
    echo "   - Copy credentials.json to: $DEPLOY_DIR/credentials/"
    echo "   - Ensure file permissions: chmod 600 $DEPLOY_DIR/credentials/credentials.json"
    echo ""
    echo "2. Create .env file with your API keys:"
    echo "   - Copy template: cp $DEPLOY_DIR/.env.template $DEPLOY_DIR/.env"
    echo "   - Edit: nano $DEPLOY_DIR/.env"
    echo "   - Add your API keys and configuration"
    echo ""
    echo "3. (Optional) Generate OAuth tokens locally and upload:"
    echo "   - Run locally: ./scripts/generate-tokens.sh"
    echo "   - Upload: scp -r data/*.json $USER@$(hostname -I | awk '{print $1}'):$DEPLOY_DIR/data/"
    echo ""
    echo "4. Deploy FleetManager:"
    echo "   - Manual: cd $DEPLOY_DIR && ./scripts/deploy-manual.sh"
    echo "   - Or setup GitHub Actions for automatic deployment"
    echo ""
    echo "5. Monitor the application:"
    echo "   - Logs: docker-compose -f $DEPLOY_DIR/docker-compose.yml logs -f"
    echo "   - Health: $DEPLOY_DIR/scripts/health-check.sh"
    echo "   - Status: docker-compose -f $DEPLOY_DIR/docker-compose.yml ps"
    echo ""
    echo "📚 Documentation: See DEPLOYMENT.md in the repository"
    echo ""
else
    print_error "Setup completed with errors. Please review the output above."
    exit 1
fi
