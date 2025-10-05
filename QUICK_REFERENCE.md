# FleetManager Quick Reference Card

One-page reference for common operations. Print or bookmark for quick access.

## 🚀 Setup Commands

```bash
# Server Setup (one-time)
curl -fsSL https://raw.githubusercontent.com/Valkozaur/FleetManager/main/scripts/setup-server.sh | bash

# Deploy (automated)
git push origin main
```

## 📊 Monitoring Commands

```bash
# Container status
docker-compose ps

# Live logs
docker-compose logs -f

# Recent logs
docker-compose logs --tail=100

# Health check
./scripts/health-check.sh

# Resource usage
docker stats fleetmanager
```

## 🔧 Management Commands

```bash
# Restart
docker-compose restart

# Stop
docker-compose down

# Start
docker-compose up -d

# Manual deploy
./scripts/deploy-manual.sh

# Backup
./scripts/backup.sh
```

## 🔍 Debugging Commands

```bash
# Check credentials
ls -la credentials/credentials.json

# Check tokens
ls -la data/token*.json

# Check environment
docker-compose exec fleetmanager env | grep API

# Enter container
docker-compose exec fleetmanager sh

# View config
cat docker-compose.yml
```

## 📁 Important Paths

```
/root/fleetmanager/
├── credentials/credentials.json    # OAuth credentials
├── data/token*.json               # OAuth tokens
├── logs/                          # Application logs
├── scripts/                       # Utility scripts
├── docker-compose.yml             # Container config
└── .env                          # Environment variables
```

## 🔐 GitHub Secrets

```
HETZNER_HOST                       # Server IP
HETZNER_USER                       # SSH user (root)
HETZNER_SSH_KEY                    # Private SSH key
GOOGLE_CREDENTIALS_JSON            # OAuth JSON
GEMINI_API_KEY                     # AI API key
GOOGLE_MAPS_API_KEY                # Maps API key
GOOGLE_SHEETS_SPREADSHEET_ID       # Sheet ID
```

## ⚡ Emergency Procedures

### Rollback
```bash
docker tag fleetmanager-old fleetmanager
docker-compose up -d
```

### Restore Backup
```bash
cd /root/fleetmanager
docker-compose down
tar -xzf ~/fleetmanager-backups/fleetmanager_YYYYMMDD_HHMMSS.tar.gz
docker-compose up -d
```

### Force Redeploy
```bash
docker-compose pull
docker-compose down
docker-compose up -d
```

## 🔄 Common Tasks

### Update API Key
1. Update secret in GitHub
2. `git push origin main`

### View Deployment History
```bash
cat logs/deployments.log
```

### Check Disk Space
```bash
df -h
docker system df
```

### Clean Up Old Images
```bash
docker image prune -f
```

## 📞 Quick Links

- **Deployment Guide:** [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Secrets Setup:** [SECRETS_SETUP.md](./SECRETS_SETUP.md)
- **Advanced Topics:** [DEPLOYMENT_ADVANCED.md](./DEPLOYMENT_ADVANCED.md)
- **Checklist:** [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)
- **GitHub Actions:** `https://github.com/Valkozaur/FleetManager/actions`

## ⚠️ Troubleshooting

| Issue | Quick Fix |
|-------|-----------|
| Container won't start | Check logs: `docker-compose logs` |
| Auth failed | Verify credentials.json exists |
| API quota exceeded | Check Google Cloud Console |
| Deployment failed | Check GitHub Actions logs |
| Out of disk space | Clean up: `docker system prune -a` |

## 📊 Health Check Indicators

✅ **Healthy:**
- Container status: `Up`
- Health status: `healthy`
- Logs: No errors
- CPU: <80%
- Memory: <80%

❌ **Unhealthy:**
- Container status: `Exited`
- Health status: `unhealthy`
- Logs: Errors present
- CPU: >90%
- Memory: >90%

## 🎯 Success Metrics

- ✅ Uptime: >99%
- ✅ Response time: <5s
- ✅ Memory usage: <512MB
- ✅ Error rate: <1%
- ✅ Backups: Daily
- ✅ Deployment time: 8-12 min

---

**Version:** 2.0 | **Last Updated:** October 2025 | **Maintainer:** Valkozaur
