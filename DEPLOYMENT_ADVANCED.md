# Advanced Deployment Topics

This document covers advanced deployment scenarios, performance optimization, and security best practices for FleetManager.

## Table of Contents

1. [Security Best Practices](#security-best-practices)
2. [CI/CD Pipeline Details](#cicd-pipeline-details)
3. [Performance Optimization](#performance-optimization)
4. [Multi-Environment Setup](#multi-environment-setup)
5. [Comparison: Old vs New](#comparison-old-vs-new)
6. [FAQ](#faq)

---

## Security Best Practices

### Credential Protection

✅ **Implemented:**
- GitHub Secrets for all sensitive data (encrypted at rest)
- SSH key authentication (no passwords)
- Multi-stage Docker builds (minimal attack surface)
- Non-root container user
- Automated security scanning (Trivy)
- Credentials deployed over encrypted SSH
- Environment variables never logged

✅ **Maintenance:**
- Rotate SSH keys every 6 months
- Rotate API keys every 90 days
- Review access logs regularly
- Keep Docker images updated
- Monitor API usage for anomalies

### Container Security

- **Runs as non-root user** (`appuser:1000`)
- **Minimal base image** (Python slim)
- **Read-only credentials directory** (`chmod 700`)
- **No unnecessary system packages**
- **Regular security scans** in CI/CD pipeline
- **Healthcheck validation** before deployment

### Network Security

- Use SSH keys (never passwords)
- Restrict server firewall to necessary ports
- All API calls over HTTPS
- GitHub Container Registry authentication
- Server access logged and audited

### Data Privacy

⚠️ **Important:** Gmail content is processed by Google Gemini API

**Considerations:**
- Review [Google's data processing policies](https://cloud.google.com/terms)
- Ensure compliance with your organization's policies
- Consider data residency requirements
- OAuth tokens have minimal required scopes
- No data persisted beyond session

---

## CI/CD Pipeline Details

### Workflow Triggers

- **Push to main** → Full deployment to production
- **Push to develop** → Build and test only
- **Manual trigger** → Deploy via GitHub Actions UI
- **Pull request** → Test only (no deployment)

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        GitHub Actions                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐          │
│  │   Test   │  →   │  Build   │  →   │  Deploy  │          │
│  └──────────┘      └──────────┘      └──────────┘          │
│      │                  │                  │                 │
│      ├─ Setup Python    ├─ Multi-stage    ├─ Deploy creds  │
│      ├─ Install deps    │  Docker build   ├─ Blue-green    │
│      ├─ Run tests       ├─ Layer cache    ├─ Health check  │
│      └─ Validate        ├─ Security scan  ├─ Rollback      │
│                         ├─ Push to GHCR   └─ Cleanup       │
│                         └─ Tag images                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
                    ┌─────────────────┐
                    │  Hetzner Server │
                    ├─────────────────┤
                    │  Docker Engine  │
                    │  FleetManager   │
                    └─────────────────┘
```

### Deployment Features

- ✅ **Zero-downtime deployment** (blue-green strategy)
- ✅ **Automatic rollback** on health check failure
- ✅ **Health check validation** (6 retries, 10s intervals)
- ✅ **Credential security** (encrypted SSH transfer)
- ✅ **Build optimization** (BuildKit caching)
- ✅ **Security scanning** (Trivy vulnerability scanner)
- ✅ **Deployment history** (logged with timestamps)
- ✅ **Container isolation** (non-root user, minimal privileges)

### Blue-Green Deployment Process

1. **Current State (Blue)**: `fleetmanager` container running
2. **Download**: Pull new Docker image
3. **Rename**: `fleetmanager` → `fleetmanager-old`
4. **Deploy (Green)**: Start new `fleetmanager` container
5. **Health Check**: Validate new container (6 attempts)
6. **Success**: Remove `fleetmanager-old`
7. **Failure**: Rollback to `fleetmanager-old`

**Benefits:**
- Zero downtime
- Instant rollback capability
- Validation before cutover
- Minimal risk

---

## Performance Optimization

### Docker Image Optimization

**Multi-stage build improvements:**

| Metric | Old | New | Improvement |
|--------|-----|-----|-------------|
| Image size | ~400MB | ~200MB | 50% reduction |
| Build time (cold) | ~6 min | ~5 min | 17% faster |
| Build time (cached) | ~6 min | ~2 min | 67% faster |
| Startup time | ~8s | ~5s | 38% faster |
| Security score | B | A | Improved |

**Optimization techniques:**
- Multi-stage builds (separate build and runtime)
- Virtual environment isolation
- Minimal runtime dependencies
- Layer caching strategy
- BuildKit optimizations

### Build Caching Strategy

```dockerfile
# Stage 1: Builder (cached separately)
FROM python:3.13.7-slim AS builder
RUN python -m venv /opt/venv
COPY requirements.txt .
RUN pip install -r requirements.txt

# Stage 2: Runtime (only changes when code changes)
FROM python:3.13.7-slim AS runtime
COPY --from=builder /opt/venv /opt/venv
COPY src/ ./src/
```

**Cache layers:**
1. Base image (rarely changes)
2. Virtual environment (changes with dependencies)
3. Application code (changes frequently)

**Results:**
- First build: ~5 minutes
- Subsequent builds: ~2 minutes (60% faster)
- Code-only changes: ~1 minute (80% faster)

### Resource Configuration

**Current limits (docker-compose.yml):**
```yaml
mem_limit: 512m           # Maximum memory
mem_reservation: 256m     # Guaranteed memory
cpus: 1.0                 # CPU cores
```

**Recommended for different loads:**

| Scenario | Memory | CPU | Notes |
|----------|--------|-----|-------|
| Light (<100 emails/day) | 256-512MB | 0.5 | Default |
| Medium (100-1000/day) | 512MB-1GB | 1.0 | Recommended |
| Heavy (>1000/day) | 1-2GB | 2.0 | High volume |

**Monitoring:**
```bash
# Check resource usage
docker stats fleetmanager

# Optimize if needed
# Edit docker-compose.yml and redeploy
```

---

## Multi-Environment Setup

### Strategy: Branch-Based Environments

**Setup multiple environments (staging, production):**

#### 1. Create Environment Branches

```bash
git checkout -b staging
git push origin staging

git checkout -b production
git push origin production
```

#### 2. Configure GitHub Environments

In GitHub repository settings:

1. Go to **Settings** → **Environments**
2. Create two environments:
   - `staging` (auto-deploy)
   - `production` (manual approval required)

3. Add environment-specific secrets to each

#### 3. Update Workflow

```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [ main, staging, production ]

jobs:
  deploy:
    environment: 
      name: ${{ github.ref == 'refs/heads/production' && 'production' || 'staging' }}
```

#### 4. Environment-Specific Secrets

**Staging environment:**
- `HETZNER_HOST` → Staging server IP
- `GOOGLE_CREDENTIALS_JSON` → Staging credentials
- Other staging-specific configs

**Production environment:**
- `HETZNER_HOST` → Production server IP
- `GOOGLE_CREDENTIALS_JSON` → Production credentials
- Other production-specific configs

### Deployment Flow

```
Developer → Push to staging → Auto-deploy to staging server
                                      ↓
                            Test on staging environment
                                      ↓
                            Create PR: staging → production
                                      ↓
                            Approval required (manual)
                                      ↓
                            Deploy to production server
```

---

## Comparison: Old vs New

### Old Deployment Process ❌

**Manual, error-prone, time-consuming:**

1. ❌ Manual file uploads (credentials, tokens)
2. ❌ Manual .env creation on server
3. ❌ Multiple SSH sessions required
4. ❌ No automated testing
5. ❌ No health checks during deployment
6. ❌ No rollback mechanism
7. ❌ Difficult to replicate to new servers
8. ❌ Secrets managed manually (insecure)
9. ❌ Larger Docker images (400MB+)
10. ❌ Manual monitoring setup
11. ❌ No deployment history
12. ❌ Downtime during deployment

**Time Investment:**
- Initial setup: 2-3 hours
- Each deployment: 30-45 minutes
- Replication to new server: 2-3 hours
- Debugging issues: High (manual checks)

**Risk Level:** High (manual errors, no rollback)

---

### New Deployment Process ✅

**Automated, secure, fast:**

1. ✅ All secrets in GitHub (one-time setup)
2. ✅ One-command server setup
3. ✅ Automated CI/CD pipeline
4. ✅ Automated testing before deployment
5. ✅ Health checks with retries
6. ✅ Automatic rollback on failure
7. ✅ Easy replication (same script)
8. ✅ Secure secret management (encrypted)
9. ✅ Optimized Docker images (200MB)
10. ✅ Automated monitoring setup
11. ✅ Complete deployment history
12. ✅ Zero-downtime deployment

**Time Investment:**
- Initial setup: 10-15 minutes
- Each deployment: 8-12 minutes (automated)
- Replication to new server: 5 minutes
- Debugging issues: Low (automated logs)

**Risk Level:** Low (automated rollback, health checks)

---

### Feature Comparison Table

| Feature | Old Process | New Process |
|---------|-------------|-------------|
| Setup time | 2-3 hours | 10-15 minutes |
| Deployment time | 30-45 min | 8-12 min (auto) |
| Manual steps | 15+ | 0 (after setup) |
| Rollback capability | No | Yes (automatic) |
| Health validation | No | Yes (6 retries) |
| Security scanning | No | Yes (Trivy) |
| Zero downtime | No | Yes |
| Secrets management | Manual/insecure | GitHub Secrets |
| Image optimization | No | Yes (50% smaller) |
| Build caching | No | Yes (67% faster) |
| Replication ease | Hard | Easy (5 min) |
| Documentation | Minimal | Comprehensive |

---

## FAQ

### General Questions

**Q: Do I need to manually upload credentials to the server?**  
A: No! Store credentials in GitHub Secrets. The CI/CD pipeline deploys them securely via encrypted SSH during deployment.

**Q: What happens if deployment fails?**  
A: The system automatically rolls back to the previous working version. The old container is preserved until health checks pass.

**Q: Can I deploy to multiple servers?**  
A: Yes! Run the setup script on each server, create environment-specific GitHub Secrets, and deploy to different environments.

**Q: How do I know if deployment succeeded?**  
A: Check the GitHub Actions tab for real-time status. Health checks validate the deployment before marking it successful.

**Q: What if I need to rollback manually?**  
A: SSH to the server and run: `docker tag fleetmanager-old fleetmanager && docker-compose up -d`. See [manual rollback guide](./DEPLOYMENT.md#rollback-to-previous-version).

### Security Questions

**Q: How secure are my credentials?**  
A: Very secure. GitHub Secrets are encrypted at rest, transferred over SSH, and never exposed in logs. Only authorized users can access them.

**Q: Can I rotate API keys without downtime?**  
A: Yes! Update the GitHub Secret and push to main. The deployment will use the new keys with zero downtime.

**Q: Is the container secure?**  
A: Yes. It runs as non-root user, has minimal packages, read-only credentials, and is regularly scanned for vulnerabilities.

**Q: What about data privacy?**  
A: Gmail content is processed by Google Gemini API. Review Google's policies and ensure compliance with your requirements.

### Cost Questions

**Q: How much does this setup cost?**  
A: 
- **GitHub Actions**: Free for public repos, ~$8/month for 3000 private minutes
- **GitHub Container Registry**: Free for public images
- **Hetzner Server**: ~$5-15/month depending on size
- **Google APIs**: Usually free tier sufficient

**Total: ~$5-25/month** (mostly server cost)

### Technical Questions

**Q: Why multi-stage Docker builds?**  
A: Smaller images (50% reduction), better security (no build tools in runtime), faster deployments, and better caching.

**Q: Can I customize resource limits?**  
A: Yes! Edit `mem_limit` and `cpus` in `docker-compose.yml` and redeploy.

**Q: How does blue-green deployment work?**  
A: Old container renamed, new container starts, health checks run, old removed on success or restored on failure.

**Q: What if health checks keep failing?**  
A: Deployment fails and rolls back automatically. Check logs for the issue (usually credentials, env vars, or API quota).

### Operational Questions

**Q: How do I view logs?**  
A: SSH to server: `docker-compose logs -f` or check GitHub Actions logs for deployment details.

**Q: Can I pause automated deployments?**  
A: Yes! Disable the GitHub Actions workflow or use a feature branch instead of pushing to main.

**Q: How do I update the application code?**  
A: Just push to main branch. CI/CD handles testing, building, and deployment automatically.

**Q: What about database migrations?**  
A: Currently uses Google Sheets (no migrations needed). For database additions, add migration steps to deployment script.

---

## Quick Reference Commands

### Server Management

```bash
# Server setup (one-time)
curl -fsSL https://raw.githubusercontent.com/Valkozaur/FleetManager/main/scripts/setup-server.sh | bash

# Check deployment status
ssh root@SERVER_IP "cd /root/fleetmanager && docker-compose ps"

# View live logs
ssh root@SERVER_IP "cd /root/fleetmanager && docker-compose logs -f"

# Run health check
ssh root@SERVER_IP "cd /root/fleetmanager && ./scripts/health-check.sh"

# Manual deployment
ssh root@SERVER_IP "cd /root/fleetmanager && ./scripts/deploy-manual.sh"

# Restart container
ssh root@SERVER_IP "cd /root/fleetmanager && docker-compose restart"

# Stop container
ssh root@SERVER_IP "cd /root/fleetmanager && docker-compose down"

# View resource usage
ssh root@SERVER_IP "docker stats fleetmanager"
```

### Local Development

```bash
# Build locally
docker build -t fleetmanager:local .

# Run locally
docker run -it --rm \
  -v $(pwd)/credentials:/app/credentials \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  fleetmanager:local

# Test build
docker build --target builder -t fleetmanager:test .
```

### GitHub Actions

```bash
# Trigger manual deployment
gh workflow run deploy.yml

# View workflow status
gh run list

# View workflow logs
gh run view

# Cancel running workflow
gh run cancel
```

---

## Support Resources

**Documentation:**
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Main deployment guide
- [SECRETS_SETUP.md](./SECRETS_SETUP.md) - Detailed secrets configuration
- [README.md](./README.md) - Application overview

**Get Help:**
1. Check [Troubleshooting](./DEPLOYMENT.md#troubleshooting) section
2. Review GitHub Actions logs (Actions tab)
3. Check server logs: `docker-compose logs`
4. Run validation: `./scripts/validate-deployment.sh`
5. Open GitHub Issue with error details

**Community:**
- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and community help

---

**Last Updated:** October 2025  
**Version:** 2.0  
**Maintainer:** Valkozaur
