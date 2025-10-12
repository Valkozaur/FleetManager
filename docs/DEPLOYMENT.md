# Deployment Guide - Hetzner Server

This guide covers the complete deployment process for FleetManager to a Hetzner server using GitHub Actions CI/CD.

## Architecture Overview

The deployment pipeline consists of:

1. **GitHub Actions** - Builds Docker images and pushes to GitHub Container Registry (GHCR)
2. **Deployment Script** - Manages Hetzner firewall access and deploys via SSH
3. **Docker Compose** - Orchestrates services on the Hetzner server

## Prerequisites

### 1. Hetzner Server Setup

Your Hetzner server needs:

- Docker and Docker Compose installed
- Project directory created at `/opt/fleetmanager`
- Credentials directory at `/opt/fleetmanager/credentials` with Gmail credentials
- Environment file at `/opt/fleetmanager/.env.production`

#### Initial Server Setup

```bash
# SSH into your Hetzner server
ssh root@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt-get update
apt-get install -y docker-compose-plugin

# Create project structure
mkdir -p /opt/fleetmanager/credentials
cd /opt/fleetmanager

# Clone repository (first time only)
git clone https://github.com/Valkozaur/FleetManager.git .

# Create production environment file
cp .env.example .env.production
nano .env.production  # Edit with production values
```

### 2. GitHub Repository Secrets

Add the following secrets to your GitHub repository (Settings → Secrets and variables → Actions):

| Secret Name | Description | Example |
|------------|-------------|---------|
| `HETZNER_HOST` | Your Hetzner server IP or hostname | `123.456.789.10` |
| `HETZNER_USER` | SSH user (typically `root`) | `root` |
| `HETZNER_SSH_KEY` | Private SSH key for server access | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `HETZNER_FIREWALL_TOKEN` | Hetzner Cloud API token | `abc123...` |
| `HETZNER_FIREWALL_ID` | Hetzner firewall ID | `123456` |

#### Generating SSH Key

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions@fleetmanager" -f ~/.ssh/fleetmanager_deploy

# Copy public key to server
ssh-copy-id -i ~/.ssh/fleetmanager_deploy.pub root@your-server-ip

# Add private key to GitHub secrets
cat ~/.ssh/fleetmanager_deploy
```

#### Getting Hetzner API Token and Firewall ID

1. Go to [Hetzner Cloud Console](https://console.hetzner.cloud/)
2. Select your project
3. Navigate to **Security → API Tokens**
4. Create a new token with **Read & Write** permissions
5. Navigate to **Firewalls** to find your firewall ID (in the URL or details)

### 3. Hetzner Firewall Configuration

Your firewall needs these permanent rules:

- **SSH (22/tcp)** - From your management IPs (permanent access)
- **HTTP (80/tcp)** - From anywhere (if using nginx)
- **HTTPS (443/tcp)** - From anywhere (if using nginx)

The deployment script will temporarily add the GitHub Actions runner IP for SSH access.

## Deployment Process

### Automatic Deployment (via GitHub Actions)

The workflow automatically triggers on:

- Push to `main` or `develop` branches
- Changes to `services/email-processor/**`
- Manual workflow dispatch

#### Workflow Steps:

1. **Build Stage**
   - Checks out code
   - Builds Docker image with multi-stage optimization
   - Pushes image to GHCR with tags: `latest`, `branch-name`, `branch-sha`
   - Generates build attestation

2. **Deploy Stage**
   - Gets GitHub Actions runner IP
   - Adds IP to Hetzner firewall temporarily
   - SSHs into server
   - Logs into GHCR
   - Pulls new image
   - Stops old container
   - Starts new container
   - Removes temporary firewall rule
   - Verifies deployment

### Manual Deployment

To deploy manually from your local machine:

```bash
# Set environment variables
export HETZNER_HOST="your-server-ip"
export HETZNER_USER="root"
export HETZNER_FIREWALL_TOKEN="your-api-token"
export HETZNER_FIREWALL_ID="your-firewall-id"
export IMAGE_TAG="latest"
export GITHUB_TOKEN="your-github-pat"
export GITHUB_ACTOR="your-github-username"

# Run deployment script
./scripts/deploy-to-hetzner.sh
```

## Monitoring and Maintenance

### View Logs

```bash
# SSH into server
ssh root@your-server-ip

# View email processor logs
cd /opt/fleetmanager
docker-compose -f infrastructure/docker/docker-compose.prod.yml logs -f email-processor

# View specific time range
docker-compose -f infrastructure/docker/docker-compose.prod.yml logs --since 1h email-processor
```

### Check Service Status

```bash
# List running services
docker-compose -f infrastructure/docker/docker-compose.prod.yml ps

# Check health status
docker inspect fleetmanager-email-processor --format='{{.State.Health.Status}}'

# View resource usage
docker stats fleetmanager-email-processor
```

### Update Credentials

```bash
# SSH into server
ssh root@your-server-ip

# Update Gmail credentials
nano /opt/fleetmanager/credentials/credentials.json

# Restart service
cd /opt/fleetmanager
docker-compose -f infrastructure/docker/docker-compose.prod.yml restart email-processor
```

### Rollback to Previous Version

```bash
# Find previous image versions
docker images | grep fleetmanager-email-processor

# Update docker-compose to use specific tag
nano infrastructure/docker/docker-compose.prod.yml
# Change: ghcr.io/valkozaur/fleetmanager-email-processor:latest
# To:     ghcr.io/valkozaur/fleetmanager-email-processor:develop-abc1234

# Pull and restart
docker-compose -f infrastructure/docker/docker-compose.prod.yml pull email-processor
docker-compose -f infrastructure/docker/docker-compose.prod.yml up -d email-processor
```

## Troubleshooting

### Deployment Fails - SSH Connection Timeout

**Issue**: Firewall rule not propagating fast enough.

**Solution**: The script includes a 5-second wait. If needed, increase it in `scripts/deploy-to-hetzner.sh`:

```bash
# Change from:
sleep 5
# To:
sleep 10
```

### Container Fails to Start - Credentials Error

**Issue**: Missing or invalid Gmail credentials.

**Solution**: Ensure credentials are mounted correctly:

```bash
# Check if file exists
ssh root@your-server-ip "ls -la /opt/fleetmanager/credentials/"

# Verify file content (should be valid JSON)
ssh root@your-server-ip "cat /opt/fleetmanager/credentials/credentials.json"
```

### Image Pull Authentication Failed

**Issue**: GitHub Container Registry authentication failure.

**Solution**: Create a Personal Access Token (PAT) with `read:packages` scope:

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate token with `read:packages` scope
3. Add to server:

```bash
ssh root@your-server-ip
echo "YOUR_PAT" | docker login ghcr.io -u YOUR_USERNAME --password-stdin
```

### High Memory Usage

**Issue**: Container exceeding memory limits.

**Solution**: Adjust limits in `infrastructure/docker/docker-compose.prod.yml`:

```yaml
mem_limit: 1024m      # Increase from 512m
mem_reservation: 512m  # Increase from 256m
```

## Security Best Practices

1. **SSH Keys**: Use dedicated SSH keys for deployment, not your personal keys
2. **API Tokens**: Rotate Hetzner API tokens regularly
3. **Firewall Rules**: Keep permanent SSH access limited to known IPs
4. **Credentials**: Store credentials in secure volume, never in Git
5. **Environment Variables**: Use `.env.production` for sensitive data
6. **Container Isolation**: Run containers as non-root user (already configured)
7. **Log Rotation**: Logs are limited to 3 files × 10MB each

## Environment Variables

Production environment file (`.env.production`) should contain:

```bash
# Gmail Configuration
GMAIL_CREDENTIALS_FILE=/app/credentials/credentials.json
GMAIL_CHECK_INTERVAL=300

# Gemini AI Configuration
GOOGLE_GEMINI_API_KEY=your-gemini-api-key

# Google Sheets Configuration
GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id

# Google Maps Configuration (optional)
GOOGLE_MAPS_API_KEY=your-maps-api-key

# Application Configuration
LOG_LEVEL=INFO
TEST_MODE=false
DATA_DIR=/app/data

# Email Query Configuration (optional)
TEST_EMAIL_QUERY=is:unread category:primary newer_than:7d
```

## CI/CD Pipeline Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  Developer Push (main/develop)                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  GitHub Actions: Build & Push                                   │
│  ├─ Build Docker image                                          │
│  ├─ Run tests                                                   │
│  ├─ Push to GHCR                                                │
│  └─ Generate attestation                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  GitHub Actions: Deploy                                         │
│  ├─ Get runner IP                                               │
│  ├─ Add IP to Hetzner firewall (temporary)                      │
│  ├─ SSH to server                                               │
│  ├─ Pull new image from GHCR                                    │
│  ├─ Stop old container                                          │
│  ├─ Start new container                                         │
│  ├─ Remove IP from firewall                                     │
│  └─ Verify deployment                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Hetzner Server: Running Service                                │
│  └─ Docker Compose with new image                               │
└─────────────────────────────────────────────────────────────────┘
```

## Additional Resources

- [Hetzner Cloud Documentation](https://docs.hetzner.com/cloud/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [GitHub Container Registry Guide](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

## Support

For issues or questions:

1. Check GitHub Actions logs for build/deploy errors
2. Check server logs: `docker-compose logs -f email-processor`
3. Review firewall rules in Hetzner Console
4. Verify all secrets are correctly set in GitHub repository
