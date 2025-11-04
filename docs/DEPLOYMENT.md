# FleetManager Deployment Guide

Complete guide for deploying FleetManager services to Hetzner Cloud with full observability stack.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [GitHub Repository Setup](#github-repository-setup)
- [Hetzner Server Setup](#hetzner-server-setup)
- [Deployment Process](#deployment-process)
- [Observability Stack](#observability-stack)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Rollback Procedure](#rollback-procedure)

## Prerequisites

### Local Requirements
- GitHub account with repository access
- SSH key pair for Hetzner server access
- Docker CLI (for manual deployments)

### Hetzner Cloud Requirements
- Hetzner Cloud server (minimum 2 CPU, 4GB RAM recommended)
- Docker and Docker Compose installed on server
- SSH access configured
- Firewall rules configured (see [Firewall Configuration](#firewall-configuration))

### API Keys & Credentials
- **Google Service Account**: JSON key file with Gmail and Maps API access
- **Gmail Delegated User Email**: Email address for domain-wide delegation
- **Gemini API Key**: For AI classification and extraction
- **Google Maps API Key**: For geocoding (optional)
- **Google Sheets Spreadsheet ID**: For legacy Sheets integration (optional)

## GitHub Repository Setup

### 1. Configure GitHub Secrets

Navigate to your repository → Settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `HETZNER_HOST` | Hetzner server IP or hostname | `49.12.34.56` or `fleet.example.com` |
| `HETZNER_PORT` | SSH port (usually 22) | `22` |
| `HETZNER_USER` | SSH username | `root` or `deploy` |
| `HETZNER_SSH_KEY` | Private SSH key for authentication | `-----BEGIN OPENSSH PRIVATE KEY-----...` |

**Note**: `GITHUB_TOKEN` is automatically provided by GitHub Actions.

### 2. Verify Workflow Configuration

The deployment workflow (`.github/workflows/deploy-email-processor.yml`) will:
1. Build `email-processor` Docker image
2. Build `database-migration` Docker image
3. Push both images to GitHub Container Registry (GHCR)
4. SSH to Hetzner server and deploy via Docker Compose

**Trigger**: Automatic on push to `main` branch

## Hetzner Server Setup

### 1. Initial Server Configuration

SSH into your Hetzner server:

```bash
ssh root@<HETZNER_HOST>
```

### 2. Install Docker & Docker Compose

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Verify installation
docker --version
docker compose version
```

### 3. Create Deployment Directory

```bash
# Create deployment directory
mkdir -p ~/fleetmanager
cd ~/fleetmanager

# Create credentials directory
mkdir -p .credentials
```

### 4. Upload Required Files

From your **local machine**, copy required files to the server:

```bash
# Copy production compose file
scp docker-compose.prod.yml <user>@<HETZNER_HOST>:~/fleetmanager/

# Copy observability configuration files
scp otel-collector-config.yml <user>@<HETZNER_HOST>:~/fleetmanager/
scp prometheus.yml <user>@<HETZNER_HOST>:~/fleetmanager/

# Copy service account credentials
scp .credentials/service-account.json <user>@<HETZNER_HOST>:~/fleetmanager/.credentials/
```

### 5. Create Environment File

On the Hetzner server, create `~/fleetmanager/.env`:

```bash
cd ~/fleetmanager
nano .env
```

**Required environment variables:**

```env
# Database Configuration
POSTGRES_USER=fleetmanager
POSTGRES_PASSWORD=<STRONG_PASSWORD_HERE>
POSTGRES_DB=fleetmanager

# Google Service Account
GOOGLE_SERVICE_ACCOUNT_FILE=/app/credentials/service-account.json
GMAIL_DELEGATED_USER_EMAIL=<your-email@domain.com>

# Google Gemini AI
GEMINI_API_KEY=<your-gemini-api-key>

# Optional: Google Maps Geocoding
GOOGLE_MAPS_API_KEY=<your-maps-api-key>

# Optional: Google Sheets (Legacy)
GOOGLE_SHEETS_SPREADSHEET_ID=<spreadsheet-id>
GOOGLE_SHEETS_RANGE_NAME=Sheet1!A:Z

# Application Configuration
DATA_DIR=/app/data
LOG_LEVEL=INFO

# OpenTelemetry (configured by docker-compose)
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_SERVICE_NAME=email-processor
```

**Security**: Set proper file permissions:

```bash
chmod 600 .env
chmod 600 .credentials/service-account.json
```

### 6. Firewall Configuration

Configure Hetzner firewall to allow access to observability services:

```bash
# If using UFW
ufw allow 22/tcp      # SSH
ufw allow 3000/tcp    # Grafana UI
ufw allow 9090/tcp    # Prometheus UI
ufw allow 16686/tcp   # Jaeger UI
ufw enable
```

**Production recommendation**: Use Hetzner Cloud Firewall for better control:
- Allow inbound: `22` (SSH), `3000` (Grafana), `9090` (Prometheus), `16686` (Jaeger)
- Source: Your IP address or VPN range
- Default: Deny all other inbound traffic

### 7. Docker Registry Authentication

Authenticate Docker to pull images from GitHub Container Registry:

```bash
# Create personal access token at https://github.com/settings/tokens
# with 'read:packages' permission

echo "<YOUR_GITHUB_TOKEN>" | docker login ghcr.io -u <YOUR_GITHUB_USERNAME> --password-stdin
```

**Alternative**: Use GitHub Actions to deploy without manual authentication (recommended).

## Deployment Process

### Automatic Deployment (Recommended)

**Trigger**: Push to `main` branch

```bash
# On your local machine
git add .
git commit -m "Deploy to production"
git push origin main
```

GitHub Actions will:
1. ✅ Build both Docker images
2. ✅ Push to GHCR (`ghcr.io/valkozaur/email-processor:main` and `ghcr.io/valkozaur/database-migration:main`)
3. ✅ SSH to Hetzner server
4. ✅ Pull latest images
5. ✅ Restart services with `docker compose up -d`

**Monitor deployment**: Check GitHub Actions workflow at `https://github.com/Valkozaur/FleetManager/actions`

### Manual Deployment

If automatic deployment fails or you need to deploy manually:

```bash
# SSH to Hetzner server
ssh <user>@<HETZNER_HOST>

# Navigate to deployment directory
cd ~/fleetmanager

# Pull latest images
docker compose -f docker-compose.prod.yml pull

# Start/restart services
docker compose -f docker-compose.prod.yml up -d

# Check service status
docker compose -f docker-compose.prod.yml ps
```

### Service Startup Order

Docker Compose ensures proper startup sequence:

1. **PostgreSQL Database** (`db`)
   - Starts with health check
   - Waits for `pg_isready` confirmation

2. **Database Migration** (`database-migration`)
   - Depends on: `db` (healthy)
   - Runs Alembic migrations
   - Exits after completion (restart policy: `no`)

3. **Email Processor** (`email-processor`)
   - Depends on: `database-migration` (completed successfully) and `otel-collector` (started)
   - Continuously polls Gmail for emails
   - Restart policy: `unless-stopped`

4. **Observability Stack** (parallel startup)
   - **Jaeger** (`jaeger`) - Distributed tracing backend
   - **Prometheus** (`prometheus`) - Metrics collection and storage
   - **OTEL Collector** (`otel-collector`) - Telemetry aggregation
   - **Grafana** (`grafana`) - Visualization and dashboards

## Observability Stack

### Exposed Services

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **Jaeger UI** | 16686 | `http://<HETZNER_HOST>:16686` | Distributed tracing visualization |
| **Prometheus UI** | 9090 | `http://<HETZNER_HOST>:9090` | Metrics query interface |
| **Grafana** | 3000 | `http://<HETZNER_HOST>:3000` | Unified observability dashboards |
| **OTEL Collector** | 4317, 4318 | Internal only | Telemetry ingestion endpoint |

### Accessing Observability UIs

#### Grafana
- **URL**: `http://<HETZNER_HOST>:3000`
- **Default credentials**: 
  - Username: `admin`
  - Password: `admin` (change on first login!)
- **Features**: 
  - Pre-configured Prometheus data source
  - Custom dashboards for email-processor metrics
  - Alerting and notification support

#### Jaeger
- **URL**: `http://<HETZNER_HOST>:16686`
- **Features**:
  - Trace search and visualization
  - Service dependency graph
  - Performance analysis
  - Email processing pipeline tracing

#### Prometheus
- **URL**: `http://<HETZNER_HOST>:9090`
- **Features**:
  - PromQL query interface
  - Target health monitoring
  - Metrics exploration
  - Alert rule management

### Configuration Files

**OpenTelemetry Collector** (`otel-collector-config.yml`):
- Receives traces and metrics from email-processor
- Exports traces to Jaeger
- Exports metrics to Prometheus
- Must be present in `~/fleetmanager/` on Hetzner server

**Prometheus** (`prometheus.yml`):
- Scrapes metrics from OTEL Collector (`http://otel-collector:8889/metrics`)
- 15-second scrape interval
- Must be present in `~/fleetmanager/` on Hetzner server

### Data Persistence

Observability data is persisted in Docker volumes:
- `prometheus_data`: Metrics storage (15-day retention by default)
- `grafana_data`: Dashboards, users, and settings

**Backup recommendation**: Regularly backup volumes for disaster recovery.

## Verification

### 1. Check Service Status

```bash
# On Hetzner server
cd ~/fleetmanager
docker compose -f docker-compose.prod.yml ps
```

Expected output:
```
NAME                   STATUS              PORTS
database-migration     Exited (0)          
email-processor        Up (healthy)        
fleetmanager-db        Up (healthy)        5432/tcp
grafana                Up                  0.0.0.0:3000->3000/tcp
jaeger                 Up                  0.0.0.0:14268->14268/tcp, 0.0.0.0:16686->16686/tcp
otel-collector         Up                  0.0.0.0:4317-4318->4317-4318/tcp, 0.0.0.0:8889->8889/tcp
prometheus             Up                  0.0.0.0:9090->9090/tcp
```

### 2. Check Service Logs

```bash
# Email processor logs
docker compose -f docker-compose.prod.yml logs -f email-processor

# Migration logs (should show successful migration)
docker compose -f docker-compose.prod.yml logs database-migration

# Database logs
docker compose -f docker-compose.prod.yml logs db

# OTEL Collector logs
docker compose -f docker-compose.prod.yml logs otel-collector
```

### 3. Verify Database Connection

```bash
# Access PostgreSQL
docker compose -f docker-compose.prod.yml exec db psql -U fleetmanager -d fleetmanager

# Check tables
\dt

# Expected tables:
# - alembic_version
# - orders

# Exit
\q
```

### 4. Test Email Processing

Monitor logs while email-processor runs:

```bash
docker compose -f docker-compose.prod.yml logs -f email-processor
```

Look for:
- ✅ Gmail authentication successful
- ✅ Polling for new emails
- ✅ Email classification (if emails found)
- ✅ Logistics data extraction
- ✅ Database save operations
- ✅ OTEL spans exported successfully

### 5. Check Observability Stack

**Grafana**:
1. Open `http://<HETZNER_HOST>:3000`
2. Login with `admin` / `admin`
3. Navigate to Data Sources → Prometheus (should be connected)

**Jaeger**:
1. Open `http://<HETZNER_HOST>:16686`
2. Select "email-processor" service
3. Search for recent traces

**Prometheus**:
1. Open `http://<HETZNER_HOST>:9090`
2. Check targets: Status → Targets (should show `otel-collector` as UP)
3. Query metrics: `up{job="otel-collector"}`

## Troubleshooting

### Image Pull Failures

**Problem**: `Error response from daemon: pull access denied`

**Solution**:
```bash
# Re-authenticate to GHCR
echo "<YOUR_GITHUB_TOKEN>" | docker login ghcr.io -u <YOUR_GITHUB_USERNAME> --password-stdin

# Retry deployment
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Migration Failures

**Problem**: `database-migration` container exits with error

**Solution**:
```bash
# Check migration logs
docker compose -f docker-compose.prod.yml logs database-migration

# Common issues:
# 1. DATABASE_URL incorrect - verify .env file
# 2. Database not ready - check db health: docker compose ps
# 3. Schema conflicts - manually downgrade: docker compose run --rm database-migration alembic downgrade -1

# Retry migration
docker compose -f docker-compose.prod.yml up database-migration
```

### Email Processor Crashes

**Problem**: `email-processor` container repeatedly restarts

**Solution**:
```bash
# Check logs for error details
docker compose -f docker-compose.prod.yml logs email-processor

# Common issues:
# 1. Missing credentials - verify .credentials/service-account.json exists
# 2. Invalid API keys - check GEMINI_API_KEY in .env
# 3. Gmail delegation not configured - verify GMAIL_DELEGATED_USER_EMAIL

# Restart after fixing
docker compose -f docker-compose.prod.yml restart email-processor
```

### OTEL Collector Not Receiving Data

**Problem**: No traces in Jaeger, no metrics in Prometheus

**Solution**:
```bash
# Check OTEL Collector logs
docker compose -f docker-compose.prod.yml logs otel-collector

# Verify configuration file exists
ls -la ~/fleetmanager/otel-collector-config.yml

# Check email-processor environment
docker compose -f docker-compose.prod.yml exec email-processor env | grep OTEL

# Expected:
# OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
# OTEL_SERVICE_NAME=email-processor

# Restart services
docker compose -f docker-compose.prod.yml restart otel-collector email-processor
```

### Observability UI Not Accessible

**Problem**: Cannot access Grafana/Jaeger/Prometheus from browser

**Solution**:
```bash
# Check if services are running
docker compose -f docker-compose.prod.yml ps

# Check firewall rules
ufw status

# Verify ports are exposed
netstat -tuln | grep -E '(3000|9090|16686)'

# If using Hetzner Cloud Firewall, verify rules in Cloud Console
```

### Disk Space Issues

**Problem**: Server running out of disk space

**Solution**:
```bash
# Check disk usage
df -h

# Remove unused Docker resources
docker system prune -a --volumes

# Check largest volumes
docker system df -v

# Consider reducing Prometheus retention or adding more storage
```

## Rollback Procedure

### Quick Rollback (Last Known Good)

```bash
# SSH to Hetzner server
ssh <user>@<HETZNER_HOST>
cd ~/fleetmanager

# Pull previous tag (replace with specific tag)
docker pull ghcr.io/valkozaur/email-processor:sha-<commit-hash>
docker pull ghcr.io/valkozaur/database-migration:sha-<commit-hash>

# Update docker-compose.prod.yml to use specific tag
# Then restart
docker compose -f docker-compose.prod.yml up -d
```

### Database Rollback

```bash
# If migration caused issues
docker compose -f docker-compose.prod.yml run --rm database-migration bash

# Inside container
alembic downgrade -1  # Go back one migration
alembic downgrade <revision>  # Go to specific revision

exit

# Restart services
docker compose -f docker-compose.prod.yml up -d
```

### Complete Environment Reset

```bash
# WARNING: This will delete all data!
cd ~/fleetmanager

# Stop and remove everything
docker compose -f docker-compose.prod.yml down -v

# Remove volumes (careful - data loss!)
docker volume rm fleetmanager_postgres_data
docker volume rm fleetmanager_email_poller_data
docker volume rm fleetmanager_email_poller_logs
docker volume rm fleetmanager_prometheus_data
docker volume rm fleetmanager_grafana_data

# Redeploy from scratch
docker compose -f docker-compose.prod.yml up -d
```

## Maintenance Tasks

### Update Images

```bash
# Pull latest images
cd ~/fleetmanager
docker compose -f docker-compose.prod.yml pull

# Restart services
docker compose -f docker-compose.prod.yml up -d
```

### Backup Database

```bash
# Create backup
docker compose -f docker-compose.prod.yml exec db pg_dump -U fleetmanager fleetmanager > backup_$(date +%Y%m%d).sql

# Restore from backup
docker compose -f docker-compose.prod.yml exec -T db psql -U fleetmanager fleetmanager < backup_YYYYMMDD.sql
```

### Rotate Logs

Docker handles log rotation automatically, but you can configure limits:

```yaml
# Add to each service in docker-compose.prod.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Monitor Resource Usage

```bash
# Real-time resource usage
docker stats

# Check container logs size
du -sh /var/lib/docker/containers/*/*-json.log
```

## Security Recommendations

1. **Change default passwords**: Update Grafana admin password immediately
2. **Use firewall**: Restrict access to observability ports (3000, 9090, 16686)
3. **Secure credentials**: Never commit `.env` or service account JSON to git
4. **Regular updates**: Keep Docker images and base OS updated
5. **SSH hardening**: Disable password authentication, use key-based only
6. **TLS/SSL**: Add reverse proxy (nginx/traefik) with Let's Encrypt for HTTPS
7. **Backup strategy**: Automate database and volume backups
8. **Monitoring alerts**: Configure Grafana alerts for service health

## Support

- **Issues**: https://github.com/Valkozaur/FleetManager/issues
- **Workflow Logs**: https://github.com/Valkozaur/FleetManager/actions
- **Service Documentation**: See individual service README files

---

**Last Updated**: November 2025  
**Deployment Version**: 4.0 (OpenTelemetry Production)
