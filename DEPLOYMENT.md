# FleetManager Deployment Guide

This guide covers deploying FleetManager to a Hetzner server using Docker containers with GitHub Actions CI/CD.

## Overview

FleetManager is a Gmail-based logistics order processing system that:
- Polls Gmail accounts for new emails
- Classifies emails using Google Gemini AI
- Extracts logistics data and geocodes addresses
- Saves data to Google Sheets as a database

## Prerequisites

### Google Cloud Setup

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable APIs**
   Enable these APIs in your Google Cloud project:
   - Gmail API
   - Google Sheets API
   - Google Maps Geocoding API
   - Google Gemini API

3. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Select "Desktop app" as application type
   - Download the credentials as `credentials.json`

### API Keys Setup

1. **Google Gemini API Key**
   - Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a new API key
   - Store securely as environment variable

2. **Google Maps API Key**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable "Geocoding API"
   - Create API key with restrictions
   - Store securely as environment variable

### Hetzner Server Setup

1. **Create Hetzner Server**
   - Choose Ubuntu 22.04 or later
   - Minimum 2GB RAM, 20GB storage
   - Note the server IP address

2. **Initial Server Setup**
   ```bash
   # Connect to server
   ssh root@your-server-ip

   # Run setup script
   curl -O https://raw.githubusercontent.com/your-username/FleetManager/main/scripts/setup-server.sh
   chmod +x setup-server.sh
   ./setup-server.sh
   ```

## Authentication Setup

### Option 1: Local Token Generation (Recommended)

Generate OAuth tokens locally and deploy them to the server:

1. **Clone Repository Locally**
   ```bash
   git clone https://github.com/your-username/FleetManager.git
   cd FleetManager
   ```

2. **Set Up Credentials**
   ```bash
   mkdir -p credentials
   # Copy your downloaded credentials.json to credentials/
   cp /path/to/credentials.json credentials/
   ```

3. **Generate Tokens**
   ```bash
   chmod +x scripts/generate-tokens.sh
   ./scripts/generate-tokens.sh
   ```
   This will:
   - Open a browser for Gmail authentication
   - Generate `data/token.json` for Gmail API
   - Generate `data/token_sheets.json` for Google Sheets API

4. **Deploy Tokens to Server**
   ```bash
   # Copy generated tokens to server
   scp -r data/ root@your-server-ip:~/fleetmanager/
   scp -r credentials/ root@your-server-ip:~/fleetmanager/
   ```

### Option 2: Headless Authentication

For server environments without browsers:

1. **Generate Authorization URL**
   ```bash
   python3 -c "
from src.orders.poller.clients.gmail_client import GmailClient
client = GmailClient(credentials_file='credentials/credentials.json')
url = client.generate_auth_url()
print(f'Visit this URL: {url}')
print('Copy the authorization code and save it to data/auth_code.txt')
"
   ```

2. **Save Authorization Code**
   ```bash
   mkdir -p data
   echo "YOUR_AUTH_CODE_HERE" > data/auth_code.txt
   ```

3. **Deploy and Run**
   ```bash
   # Deploy to server
   scp -r data/ root@your-server-ip:~/fleetmanager/
   scp -r credentials/ root@your-server-ip:~/fleetmanager/

   # Container will automatically exchange code for tokens
   ```

## GitHub Actions CI/CD Setup

### Repository Secrets

Set these secrets in your GitHub repository (Settings → Secrets and variables → Actions):

```bash
# Required Secrets
GITHUB_TOKEN=                    # Automatically provided by GitHub
HETZNER_HOST=your-server-ip
HETZNER_USER=root
HETZNER_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----
... your private SSH key ...
-----END OPENSSH PRIVATE KEY-----

# API Keys
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_SHEETS_RANGE_NAME=Sheet1!A:Z

# Optional Secrets
HETZNER_PORT=22                  # SSH port (default: 22)
```

### SSH Key Setup

1. **Generate SSH Key Pair**
   ```bash
   ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/fleetmanager_deploy
   ```

2. **Add Public Key to Server**
   ```bash
   cat ~/.ssh/fleetmanager_deploy.pub | ssh root@your-server-ip "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
   ```

3. **Add Private Key to GitHub Secrets**
   ```bash
   cat ~/.ssh/fleetmanager_deploy
   # Copy output and add as HETZNER_SSH_KEY secret
   ```

## Deployment Methods

### Method 1: Automatic CI/CD (Recommended)

1. **Push to Main Branch**
   ```bash
   git add .
   git commit -m "Deploy FleetManager to production"
   git push origin main
   ```

2. **Monitor Deployment**
   - Go to "Actions" tab in GitHub
   - Watch the deployment workflow
   - Check logs for any issues

### Method 2: Manual Deployment

1. **Connect to Server**
   ```bash
   ssh root@your-server-ip
   cd ~/fleetmanager
   ```

2. **Deploy Manually**
   ```bash
   # Download latest docker-compose.yml
   curl -o docker-compose.yml https://raw.githubusercontent.com/your-username/FleetManager/main/docker-compose.yml

   # Create .env file
   cp .env.example .env
   # Edit .env with your API keys

   # Deploy
   chmod +x scripts/deploy-manual.sh
   ./scripts/deploy-manual.sh
   ```

## Configuration

### Environment Variables

Edit `.env` file on the server:

```bash
# Required API Keys
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id

# Gmail API Configuration
GMAIL_CREDENTIALS_FILE=/app/credentials/credentials.json

# Application Settings
DATA_DIR=/app/data
LOG_LEVEL=INFO

# Testing (optional)
TEST_MODE=false
TEST_EMAIL_QUERY=
```

### Google Sheets Setup

1. **Create Google Sheet**
   - Create a new Google Sheet
   - Note the spreadsheet ID from the URL

2. **Share with Service Account**
   - The OAuth tokens will automatically handle access
   - Ensure the sheet is accessible to the authenticated account

## Monitoring and Maintenance

### Check Application Status

```bash
# Check if containers are running
docker-compose ps

# View logs
docker-compose logs -f

# Check container health
docker inspect fleetmanager | grep Health -A 10
```

### Log Management

```bash
# View logs from last hour
docker-compose logs --since=1h

# View error logs only
docker-compose logs | grep ERROR

# Rotate logs (setup logrotate)
sudo nano /etc/logrotate.d/fleetmanager
```

### Backup Strategy

```bash
# Backup data directory
tar -czf fleetmanager-backup-$(date +%Y%m%d).tar.gz data/

# Backup Google Sheets (manual export)
# Use Google Sheets export feature periodically
```

### Update Application

```bash
# Pull latest version
cd ~/fleetmanager
git pull origin main

# Redeploy
./scripts/deploy-manual.sh
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   ```bash
   # Check token files exist
   ls -la data/token*.json

   # Check credentials file
   ls -la credentials/credentials.json

   # Regenerate tokens if needed
   ./scripts/generate-tokens.sh
   ```

2. **Container Won't Start**
   ```bash
   # Check container logs
   docker-compose logs fleetmanager

   # Check environment variables
   docker-compose exec fleetmanager env | grep -E "(API_KEY|SPREADSHEET)"
   ```

3. **API Quota Exceeded**
   - Check Google Cloud Console quotas
   - Upgrade API quotas if needed
   - Reduce polling frequency

4. **Gmail/Google Sheets Permissions**
   - Ensure OAuth tokens have correct scopes
   - Re-authenticate if permissions changed
   - Check Google account security settings

### Debug Mode

Enable debug logging:

```bash
# Edit .env
echo "LOG_LEVEL=DEBUG" >> .env

# Restart container
docker-compose restart fleetmanager
```

### Performance Monitoring

```bash
# Monitor resource usage
docker stats fleetmanager

# Check disk space
df -h

# Monitor network connectivity
ping gmail.com
```

## Security Considerations

1. **Credential Security**
   - Never commit API keys to version control
   - Use GitHub Secrets for production
   - Regularly rotate API keys

2. **Container Security**
   - Run as non-root user (configured in Dockerfile)
   - Use read-only filesystem where possible
   - Keep base images updated

3. **Network Security**
   - Use SSH keys for authentication
   - Configure firewall rules
   - Use HTTPS for all API calls

4. **Data Privacy**
   - Gmail content is processed by Google Gemini API
   - Review Google's data processing policies
   - Consider privacy implications for your organization

## Support

For issues and questions:
- Check GitHub Issues
- Review application logs
- Verify API configurations
- Test authentication setup