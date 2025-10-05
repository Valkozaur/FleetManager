# FleetManager

Gmail-based logistics order processing system with automated email classification, data extraction, and Google Sheets integration.

## 🚀 Features

- **Automated Email Processing**: Polls Gmail for new emails automatically
- **AI-Powered Classification**: Uses Google Gemini AI to classify emails
- **Logistics Data Extraction**: Extracts order details, addresses, and contact info
- **Geocoding**: Converts addresses to coordinates using Google Maps API
- **Google Sheets Integration**: Stores processed data in Google Sheets
- **Dockerized**: Fully containerized for easy deployment
- **CI/CD Pipeline**: Automated testing and deployment via GitHub Actions

## 📚 Documentation

### Quick Start
- **[Deployment Guide](./DEPLOYMENT.md)** - Complete setup and deployment instructions (start here!)
- **[Quick Reference](./QUICK_REFERENCE.md)** - One-page command reference
- **[Deployment Checklist](./DEPLOYMENT_CHECKLIST.md)** - Step-by-step checklist

### Configuration
- **[Secrets Setup](./SECRETS_SETUP.md)** - Detailed guide for GitHub Secrets and credentials
- **[Advanced Topics](./DEPLOYMENT_ADVANCED.md)** - Security, performance, and multi-environment setup
- **[Deployment Summary](./DEPLOYMENT_SUMMARY.md)** - Overview of improvements and architecture

## 🎯 Quick Deployment (3 Steps)

1. **Setup GitHub Secrets** (5 minutes)
   - Add server credentials, API keys, and OAuth credentials
   - See [SECRETS_SETUP.md](./SECRETS_SETUP.md)

2. **Prepare Server** (2 minutes)
   ```bash
   ssh root@YOUR_SERVER_IP
   curl -fsSL https://raw.githubusercontent.com/Valkozaur/FleetManager/main/scripts/setup-server.sh | bash
   ```

3. **Deploy** (automatic - 8-12 minutes)
   ```bash
   git push origin main
   ```

That's it! GitHub Actions handles the rest.

## 🏗️ Architecture

```
Gmail → FleetManager → Gemini AI → Geocoding → Google Sheets
         (Docker)        ↓
                    Classification
                    Data Extraction
```

**Deployment:**
- Automated CI/CD via GitHub Actions
- Blue-green deployment (zero downtime)
- Automatic health checks and rollback
- Deployed to Hetzner server with Docker

## 🔧 Technology Stack

- **Language**: Python 3.13
- **Container**: Docker (multi-stage build)
- **CI/CD**: GitHub Actions
- **Registry**: GitHub Container Registry
- **Server**: Hetzner (Docker-enabled image)
- **APIs**: Gmail, Google Sheets, Google Maps, Google Gemini

## 📦 Project Structure

```
FleetManager/
├── src/orders/poller/           # Main application code
│   ├── clients/                 # API clients (Gmail, Sheets, Maps, Gemini)
│   ├── models/                  # Data models
│   ├── pipeline/                # Processing pipeline
│   ├── services/                # Business logic
│   └── main.py                  # Entry point
├── scripts/                     # Deployment and utility scripts
├── .github/workflows/           # CI/CD pipeline
├── Dockerfile                   # Multi-stage Docker build
├── docker-compose.yml           # Container orchestration
└── docs/                        # Comprehensive documentation
```

## 🚀 Key Features

### Deployment (v2.0)
- ✅ **Zero-touch deployment** - All secrets via GitHub
- ✅ **One-command setup** - Single script configures server
- ✅ **Blue-green deployment** - Zero downtime
- ✅ **Automatic rollback** - Fails safe
- ✅ **Health checks** - Validates deployment
- ✅ **Security scanning** - Automated vulnerability checks
- ✅ **50% smaller images** - Multi-stage builds
- ✅ **67% faster builds** - Layer caching

### Security
- ✅ Non-root container execution
- ✅ Encrypted credential storage
- ✅ SSH key authentication
- ✅ Automated security scanning
- ✅ Read-only credential directory
- ✅ Minimal attack surface

## 🔄 Workflow

1. **Email Polling**: Checks Gmail for new emails
2. **Classification**: AI determines if email is logistics-related
3. **Extraction**: Extracts sender, receiver, addresses, contacts
4. **Geocoding**: Converts addresses to lat/long coordinates
5. **Storage**: Saves structured data to Google Sheets
6. **Logging**: Records all operations for monitoring

## 🛠️ Development

### Local Development

```bash
# Clone repository
git clone https://github.com/Valkozaur/FleetManager.git
cd FleetManager

# Install dependencies
pip install -r requirements.txt

# Add credentials
mkdir -p credentials
cp /path/to/credentials.json credentials/

# Run locally
python src/orders/poller/main.py
```

### Docker Build

```bash
# Build image
docker build -t fleetmanager:local .

# Run container
docker run -it --rm \
  -v $(pwd)/credentials:/app/credentials \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  fleetmanager:local
```

## 📊 Monitoring

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Run health check
./scripts/health-check.sh

# Resource usage
docker stats fleetmanager
```

## 🆘 Support

- **Documentation**: See [DEPLOYMENT.md](./DEPLOYMENT.md) and other guides above
- **Troubleshooting**: Check [DEPLOYMENT.md#troubleshooting](./DEPLOYMENT.md#troubleshooting)
- **Issues**: Open a GitHub Issue
- **Questions**: Use GitHub Discussions

## 📝 License

MIT License - See LICENSE file for details

## 👤 Maintainer

**Valkozaur**
- GitHub: [@Valkozaur](https://github.com/Valkozaur)

---

**Version**: 2.0  
**Last Updated**: October 2025  
**Status**: Production Ready ✅
