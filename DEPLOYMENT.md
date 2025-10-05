# FleetManager Deployment Guide

This guide covers deploying FleetManager to a Hetzner server using Docker containers with automated GitHub Actions CI/CD.

## 🚀 Quick Start

**New to FleetManager?** Follow these three simple steps:

1. **[Setup GitHub Secrets](#1-setup-github-secrets)** - 5 minutes
2. **[Prepare Hetzner Server](#2-prepare-hetzner-server)** - 2 minutes  
3. **[Deploy](#3-deploy)** - Automatic via Git push

That's it! The CI/CD pipeline handles everything else.

---

## Overview

FleetManager is a Gmail-based logistics order processing system that:
- Polls Gmail accounts for new emails
- Classifies emails using Google Gemini AI
- Extracts logistics data and geocodes addresses
- Saves data to Google Sheets as a database

**Deployment Architecture:**
- **Docker**: Containerized application
- **GitHub Actions**: Automated CI/CD pipeline
- **GitHub Container Registry**: Docker image storage
- **Hetzner Server**: Production environment (Docker pre-installed)

---

## Prerequisites

### Required Accounts & Resources

- [ ] GitHub account with repository access
- [ ] Google Cloud project with enabled APIs (Gmail, Sheets, Maps, Gemini)
- [ ] Hetzner server with Docker pre-installed
- [ ] SSH access to Hetzner server

### Google Cloud Setup

**Need help?** See detailed guide in [SECRETS_SETUP.md](./SECRETS_SETUP.md)

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create project: `FleetManager`

2. **Enable Required APIs**
   - Gmail API
   - Google Sheets API
   - Google Maps Geocoding API
   - Google Gemini API

3. **Create OAuth 2.0 Credentials**
   - Application type: **Desktop app**
   - Download `credentials.json`

4. **Get API Keys**
   - [Gemini API Key](https://aistudio.google.com/app/apikey)
   - Google Maps API Key from Cloud Console

---

## Deployment Setup

### 1. Setup GitHub Secrets

All sensitive data is stored securely in GitHub Secrets. No manual file uploads needed!

**📚 Complete Guide:** [SECRETS_SETUP.md](./SECRETS_SETUP.md)

**Quick Setup:**

Go to **Your Repository → Settings → Secrets and variables → Actions**

Add these secrets:

#### Server Connection
```
HETZNER_HOST          = Your server IP (e.g., 123.456.789.012)
HETZNER_USER          = root
HETZNER_SSH_KEY       = Your private SSH key (see setup guide)
HETZNER_PORT          = 22 (optional)
```

#### Application Configuration
```
GOOGLE_CREDENTIALS_JSON           = Complete OAuth JSON from Google Cloud
GEMINI_API_KEY                    = Your Gemini API key
GOOGLE_MAPS_API_KEY               = Your Google Maps API key
GOOGLE_SHEETS_SPREADSHEET_ID      = Your spreadsheet ID from URL
GOOGLE_SHEETS_RANGE_NAME          = Sheet1!A:Z (optional)
```

**🔐 Security Note:** GitHub Secrets are encrypted and never exposed in logs.

### 2. Prepare Hetzner Server

**One-time setup** - Run this single command on your server:

```bash
# SSH to your Hetzner server
ssh root@YOUR_SERVER_IP

# Download and run setup script
curl -fsSL https://raw.githubusercontent.com/Valkozaur/FleetManager/main/scripts/setup-server.sh | bash

# That's it! Server is ready for deployment.
```

**What does this script do?**
- ✅ Verifies Docker installation
- ✅ Creates directory structure
- ✅ Downloads deployment scripts
- ✅ Sets up systemd service for auto-restart
- ✅ Configures log rotation
- ✅ Sets up automated backups
- ✅ Configures proper permissions

**The script is idempotent** - Safe to run multiple times and on multiple servers.

### 3. Deploy

**Option A: Automatic Deployment (Recommended)**

Simply push to main branch:

```bash
git add .
git commit -m "Deploy FleetManager"
git push origin main
```

GitHub Actions automatically:
1. ✅ Runs tests
2. ✅ Builds optimized Docker image
3. ✅ Scans for vulnerabilities
4. ✅ Deploys credentials securely
5. ✅ Updates environment variables
6. ✅ Performs blue-green deployment
7. ✅ Runs health checks
8. ✅ Rolls back if issues detected

**Monitor deployment:**
- Go to **Actions** tab in GitHub
- Watch real-time deployment progress
- Review logs if needed

**Option B: Manual Deployment**

For testing or emergency deployments:

```bash
# SSH to server
ssh root@YOUR_SERVER_IP

# Navigate to deployment directory
cd /root/fleetmanager

# Run deployment script
./scripts/deploy-manual.sh
```

---

## What Happens During Deployment

### CI/CD Pipeline Stages

#### 1. **Test Stage** (2-3 minutes)
- Sets up Python environment
- Installs dependencies
- Runs import tests
- Validates code structure

#### 2. **Build Stage** (3-5 minutes)
- Multi-stage Docker build for optimization
- Layer caching for faster builds
- Pushes to GitHub Container Registry
- Security vulnerability scanning
- Tags image with commit SHA and 'latest'

#### 3. **Deploy Stage** (2-3 minutes)
- Securely transfers credentials to server
- Downloads latest docker-compose.yml
- Creates .env file from secrets
- Pulls new Docker image
- Blue-green deployment:
  - Renames old container
  - Starts new container
  - Health checks (6 attempts, 10s intervals)
  - Removes old container on success
  - Automatic rollback on failure
- Cleanup of old images

#### 4. **Health Check Stage** (30 seconds)
- Verifies container is running
- Checks container health status
- Validates credentials accessibility
- Runs comprehensive health script

**Total deployment time: ~8-12 minutes**

---

## Authentication Setup

### OAuth Token Generation

FleetManager needs OAuth tokens for Gmail and Google Sheets access.

**Option 1: Automatic (Headless) - Recommended**

The application will automatically handle OAuth flow on first run if tokens don't exist.

**Option 2: Generate Locally and Upload**

```bash
# Clone repository locally
git clone https://github.com/Valkozaur/FleetManager.git
cd FleetManager

# Add credentials
mkdir -p credentials
cp /path/to/credentials.json credentials/

# Generate tokens (opens browser)
chmod +x scripts/generate-tokens.sh
./scripts/generate-tokens.sh

# Upload to server
scp -r data/token*.json root@YOUR_SERVER_IP:/root/fleetmanager/data/
```

---

## Post-Deployment

### Verify Deployment

```bash
# SSH to server
ssh root@YOUR_SERVER_IP

# Check container status
cd /root/fleetmanager
docker-compose ps

# View logs
docker-compose logs -f

# Run health check
./scripts/health-check.sh
```

### Setup Automated Tasks (Optional)

The setup script already configured these, but you can customize:

```bash
# View current cron jobs
crontab -l

# Edit cron jobs
crontab -e

# Default setup includes:
# - Daily backups at 2 AM
```

### Monitor Application

```bash
# Follow logs in real-time
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# Check container stats
docker stats fleetmanager

# Run health check
./scripts/health-check.sh
```

---

## Configuration

### Environment Variables

Managed automatically via GitHub Secrets. To modify:

1. Update secrets in GitHub repository
2. Push to main branch
3. New deployment uses updated values

**Available variables:**
```bash
GEMINI_API_KEY                    # Required: Gemini API key
GOOGLE_MAPS_API_KEY               # Required: Maps API key
GOOGLE_SHEETS_SPREADSHEET_ID      # Required: Sheet ID
GOOGLE_SHEETS_RANGE_NAME          # Optional: Default Sheet1!A:Z
GMAIL_CREDENTIALS_FILE            # Auto-set: /app/credentials/credentials.json
DATA_DIR                          # Auto-set: /app/data
LOG_LEVEL                         # Auto-set: INFO
TEST_MODE                         # Auto-set: false
```

### Mail (Postfix) guidance

FleetManager uses the Gmail API (OAuth) to read emails and does not send outgoing application email via the local system MTA. Because the app accesses Gmail via the API (`src/orders/poller/clients/gmail_client.py`), you do not need Postfix for the application to function.

Recommended action when the Debian/Ubuntu Postfix configuration dialog appears during package installation:
- Choose "No configuration" to leave the system MTA unchanged (recommended), or skip installing Postfix entirely.

If you want to install Postfix for system-level notifications but avoid interactive prompts, here are non-interactive examples.

Preseed Postfix to select "No configuration" and install non-interactively:

```bash
# Preseed Postfix to select "No configuration"
sudo debconf-set-selections <<'DEB'
postfix postfix/main_mailer_type select No configuration
DEB

# Install without interactive prompts
sudo DEBIAN_FRONTEND=noninteractive apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get -y install postfix
```

Preseed for "Local only":

```bash
sudo debconf-set-selections <<'DEB'
postfix postfix/main_mailer_type select Local only
DEB

sudo DEBIAN_FRONTEND=noninteractive apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get -y install postfix
```

Preseed for "Internet with smarthost" (you'll still need to configure relayhost and authentication afterwards):

```bash
sudo debconf-set-selections <<'DEB'
postfix postfix/main_mailer_type select 'Internet with smarthost'
DEB

sudo DEBIAN_FRONTEND=noninteractive apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get -y install postfix

# Example manual steps after install to set relayhost (replace with your relay):
# sudo postconf -e "relayhost = [smtp.example.com]:587"
# echo "[smtp.example.com]:587    username:password" | sudo tee /etc/postfix/sasl_passwd
# sudo postmap /etc/postfix/sasl_passwd
# sudo chown root:root /etc/postfix/sasl_passwd*
# sudo systemctl reload postfix
```

Change Postfix configuration interactively later with:

```bash
sudo dpkg-reconfigure postfix
```

Or remove Postfix entirely:

```bash
sudo apt-get remove --purge -y postfix
sudo apt-get autoremove -y
```

### Google Sheets Setup

1. Create Google Sheet for logistics data
2. Get spreadsheet ID from URL:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit
   ```
3. Add to GitHub Secrets as `GOOGLE_SHEETS_SPREADSHEET_ID`
4. Share sheet with authenticated Google account

---

## Advanced Topics

### Replicate to Another Server

The streamlined setup makes replication trivial:

```bash
# 1. On new server, run setup script
ssh root@NEW_SERVER_IP
curl -fsSL https://raw.githubusercontent.com/Valkozaur/FleetManager/main/scripts/setup-server.sh | bash

# 2. Update GitHub Secrets with new server IP
# HETZNER_HOST=NEW_SERVER_IP

# 3. Push to trigger deployment
git push origin main

# Done! New server is configured and running.
```

### Blue-Green Deployment

The CI/CD pipeline implements zero-downtime deployments:

1. **Blue (Current)**: Running container serves traffic
2. **Green (New)**: New container starts and passes health checks
3. **Switch**: Old container stops, new container takes over
4. **Rollback**: If health checks fail, old container restores

### Rollback to Previous Version

**Automatic rollback** happens if health checks fail during deployment.

**Manual rollback:**

```bash
# SSH to server
ssh root@YOUR_SERVER_IP
cd /root/fleetmanager

# View deployment history
tail -50 logs/deployments.log

# Pull specific image version
docker pull ghcr.io/valkozaur/fleetmanager:main-abc123

# Update docker-compose.yml to use specific tag
# Change: image: ghcr.io/valkozaur/fleetmanager:latest
# To: image: ghcr.io/valkozaur/fleetmanager:main-abc123

# Deploy
docker-compose down
docker-compose up -d
```

### Multi-Environment Setup

Deploy to multiple environments (staging, production):

1. **Create branches:**
   ```bash
   git checkout -b staging
   git checkout -b production
   ```

2. **Update workflow** to deploy different branches to different servers

3. **Use GitHub Environments** for approval gates

---

## Troubleshooting

### Common Issues

#### 1. **Deployment Fails at SSH Connection**

**Error:** `Permission denied (publickey)`

**Solution:**
```bash
# Verify SSH key is correct
cat ~/.ssh/fleetmanager_deploy.pub | ssh root@YOUR_SERVER_IP "cat >> ~/.ssh/authorized_keys"

# Test connection
ssh -i ~/.ssh/fleetmanager_deploy root@YOUR_SERVER_IP

# Verify GitHub Secret has complete private key (including BEGIN/END lines)
```

**See:** [SECRETS_SETUP.md - SSH Troubleshooting](./SECRETS_SETUP.md#ssh-key-configuration)

#### 2. **Container Fails Health Check**

**Error:** `Container health check failed after 6 attempts`

**Solution:**
```bash
# SSH to server and check logs
ssh root@YOUR_SERVER_IP
cd /root/fleetmanager
docker-compose logs

# Common causes:
# - Missing credentials.json
# - Invalid .env variables
# - API quota exceeded
# - Network connectivity issues

# Verify credentials file
ls -la credentials/credentials.json

# Check environment variables
docker-compose exec fleetmanager env | grep API
```

#### 3. **Authentication Failed**

**Error:** `Invalid credentials` or `Token refresh failed`

**Solution:**
```bash
# Regenerate tokens locally
./scripts/generate-tokens.sh

# Upload to server
scp data/token*.json root@YOUR_SERVER_IP:/root/fleetmanager/data/

# Restart container
ssh root@YOUR_SERVER_IP "cd /root/fleetmanager && docker-compose restart"
```

#### 4. **API Quota Exceeded**

**Error:** `429 Too Many Requests` or `Quota exceeded`

**Solution:**
- Check Google Cloud Console for API quotas
- Upgrade quotas if needed (usually free tier is sufficient)
- Reduce polling frequency in application settings
- Review API usage patterns

#### 5. **Build Stage Fails**

**Error:** `Failed to build Docker image`

**Solution:**
```bash
# Test build locally
docker build -t fleetmanager:test .

# Check for dependency issues
pip install -r requirements.txt

# Verify Python version compatibility (3.13)
```

### Debug Mode

Enable detailed logging:

**In GitHub Secrets, add:**
```
ACTIONS_STEP_DEBUG = true
```

**On server:**
```bash
# Edit .env
echo "LOG_LEVEL=DEBUG" >> /root/fleetmanager/.env

# Restart container
docker-compose restart
```

### Get Help

1. **Check deployment logs:**
   - GitHub Actions → Latest workflow run
   - Server: `docker-compose logs`

2. **Review documentation:**
   - [SECRETS_SETUP.md](./SECRETS_SETUP.md) - Secrets configuration
   - [README.md](./README.md) - Application overview

3. **Validate setup:**
   ```bash
   ssh root@YOUR_SERVER_IP
   cd /root/fleetmanager
   ./scripts/validate-deployment.sh
   ```

4. **Open GitHub Issue** with:
   - Deployment logs
   - Container logs
   - Error messages
   - Steps to reproduce

---

## Monitoring and Maintenance

### Application Health

```bash
# SSH to server
ssh root@YOUR_SERVER_IP
cd /root/fleetmanager

# Check container status
docker-compose ps

# View live logs
docker-compose logs -f

# Run comprehensive health check
./scripts/health-check.sh

# Check resource usage
docker stats fleetmanager
```

### Log Management

Logs are automatically rotated daily (configured during setup).

```bash
# View recent logs
docker-compose logs --tail=100

# View logs from last hour
docker-compose logs --since=1h

# Filter error logs
docker-compose logs | grep -i error

# Check deployment history
cat logs/deployments.log

# Check health check history
cat logs/health.log
```

### Backup and Restore

Automated daily backups run at 2 AM (configured during setup).

**Manual backup:**
```bash
./scripts/backup.sh
```

**List backups:**
```bash
ls -lh ~/fleetmanager-backups/
```

**Restore from backup:**
```bash
cd /root/fleetmanager
docker-compose down

# Extract backup
tar -xzf ~/fleetmanager-backups/fleetmanager_YYYYMMDD_HHMMSS.tar.gz

# Restart
docker-compose up -d
```

### Update Application

Automatic updates via GitHub Actions (just push to main).

**Manual update:**
```bash
cd /root/fleetmanager
./scripts/deploy-manual.sh
```

---