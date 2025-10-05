# FleetManager Deployment Checklist

Use this checklist to ensure a successful deployment. Check off items as you complete them.

## 📋 Pre-Deployment Checklist

### Google Cloud Setup
- [ ] Created Google Cloud project
- [ ] Enabled Gmail API
- [ ] Enabled Google Sheets API
- [ ] Enabled Google Maps Geocoding API
- [ ] Enabled Google Gemini API
- [ ] Created OAuth 2.0 credentials (Desktop app)
- [ ] Downloaded credentials.json
- [ ] Created Gemini API key
- [ ] Created Google Maps API key
- [ ] Created Google Sheet for data storage
- [ ] Noted Spreadsheet ID from URL

### GitHub Repository Setup
- [ ] Forked/cloned FleetManager repository
- [ ] Have admin access to repository
- [ ] Confirmed Actions tab is enabled

### Hetzner Server Setup
- [ ] Provisioned Hetzner server
- [ ] Selected Docker-enabled image
- [ ] Noted server IP address
- [ ] Can SSH to server as root
- [ ] Server has at least 2GB RAM
- [ ] Server has at least 20GB storage

---

## 🔐 GitHub Secrets Configuration

### Server Connection Secrets
- [ ] Added `HETZNER_HOST` (server IP address)
- [ ] Added `HETZNER_USER` (typically `root`)
- [ ] Generated SSH key pair locally
- [ ] Added public key to server's `~/.ssh/authorized_keys`
- [ ] Added `HETZNER_SSH_KEY` (complete private key with BEGIN/END)
- [ ] (Optional) Added `HETZNER_PORT` if not using default 22

### Application Secrets
- [ ] Added `GOOGLE_CREDENTIALS_JSON` (complete OAuth JSON)
- [ ] Added `GEMINI_API_KEY` (starts with `AIza`)
- [ ] Added `GOOGLE_MAPS_API_KEY`
- [ ] Added `GOOGLE_SHEETS_SPREADSHEET_ID`
- [ ] (Optional) Added `GOOGLE_SHEETS_RANGE_NAME`

### Verification
- [ ] All required secrets show in GitHub Settings → Secrets → Actions
- [ ] No typos in secret names (case-sensitive)
- [ ] Secrets contain complete values (no truncation)

**📚 Detailed Guide:** [SECRETS_SETUP.md](./SECRETS_SETUP.md)

---

## 🖥️ Server Setup

### One-Time Setup Script
- [ ] SSH to server: `ssh root@YOUR_SERVER_IP`
- [ ] Downloaded setup script
- [ ] Executed: `curl -fsSL https://raw.githubusercontent.com/Valkozaur/FleetManager/main/scripts/setup-server.sh | bash`
- [ ] Script completed successfully (all checks passed)
- [ ] Directory structure created at `/root/fleetmanager`
- [ ] Scripts downloaded and made executable
- [ ] Systemd service created
- [ ] Log rotation configured
- [ ] Automated backups configured

### Post-Setup Verification
- [ ] Docker is running: `docker ps`
- [ ] Directory exists: `ls -la /root/fleetmanager`
- [ ] Scripts are executable: `ls -la /root/fleetmanager/scripts`
- [ ] Can run Docker without sudo

---

## 🚀 Initial Deployment

### Trigger Deployment
- [ ] Made a commit to main branch
- [ ] Pushed to GitHub: `git push origin main`
- [ ] GitHub Actions workflow started
- [ ] Monitored deployment in Actions tab

### Deployment Stages
- [ ] **Test Stage** - Passed
- [ ] **Build Stage** - Passed
- [ ] **Deploy Stage** - Passed
- [ ] **Health Check Stage** - Passed

### Post-Deployment Verification
- [ ] Container is running: `docker-compose ps`
- [ ] Logs show no errors: `docker-compose logs`
- [ ] Health check passes: `./scripts/health-check.sh`
- [ ] Credentials file accessible in container
- [ ] Can authenticate with Gmail (check logs)
- [ ] Can authenticate with Google Sheets (check logs)

---

## 🔍 Testing & Validation

### Functional Testing
- [ ] Application polls Gmail successfully
- [ ] Emails are classified correctly
- [ ] Logistics data is extracted
- [ ] Addresses are geocoded
- [ ] Data is written to Google Sheets
- [ ] No errors in application logs

### Performance Testing
- [ ] Container memory usage is normal (<512MB)
- [ ] Container CPU usage is normal (<100%)
- [ ] Response times are acceptable
- [ ] No memory leaks observed

### Security Testing
- [ ] Container runs as non-root user
- [ ] Credentials directory has correct permissions (700)
- [ ] No secrets in logs
- [ ] SSH key authentication works
- [ ] No vulnerabilities in security scan

---

## 📊 Monitoring Setup

### Automated Monitoring
- [ ] Cron jobs configured (check with `crontab -l`)
- [ ] Daily backups scheduled (2 AM)
- [ ] Log rotation configured
- [ ] Health check logs being written

### Manual Monitoring
- [ ] Can view logs: `docker-compose logs -f`
- [ ] Can check status: `docker-compose ps`
- [ ] Can run health check: `./scripts/health-check.sh`
- [ ] Can check resource usage: `docker stats`

---

## 🔄 Operational Readiness

### Documentation Review
- [ ] Read [DEPLOYMENT.md](./DEPLOYMENT.md)
- [ ] Reviewed [SECRETS_SETUP.md](./SECRETS_SETUP.md)
- [ ] Bookmarked [DEPLOYMENT_ADVANCED.md](./DEPLOYMENT_ADVANCED.md)
- [ ] Know where to find troubleshooting info

### Runbooks
- [ ] Know how to check deployment status
- [ ] Know how to view logs
- [ ] Know how to restart container
- [ ] Know how to perform manual deployment
- [ ] Know how to rollback if needed
- [ ] Know how to restore from backup

### Emergency Procedures
- [ ] Have backup of credentials.json
- [ ] Have backup of OAuth tokens
- [ ] Know server admin credentials
- [ ] Have GitHub access for secret updates
- [ ] Know who to contact for help

---

## ✅ Go-Live Checklist

### Final Verification
- [ ] All above checklists completed
- [ ] Deployment is stable (running 24+ hours)
- [ ] No errors in logs
- [ ] Emails are being processed correctly
- [ ] Data appearing in Google Sheets
- [ ] Backups are working
- [ ] Monitoring is functional

### Documentation
- [ ] Documented server IP and access details
- [ ] Documented Google Cloud project details
- [ ] Documented spreadsheet URLs
- [ ] Documented deployment schedule
- [ ] Created team runbook (if applicable)

### Communication
- [ ] Notified team of deployment
- [ ] Shared access credentials (securely)
- [ ] Scheduled review meeting
- [ ] Set up alerting (if applicable)

---

## 🔁 Ongoing Maintenance

### Weekly
- [ ] Review application logs
- [ ] Check container health
- [ ] Verify backups are running
- [ ] Check resource usage trends

### Monthly
- [ ] Review API usage and quotas
- [ ] Check for security updates
- [ ] Review deployment logs
- [ ] Test rollback procedure

### Quarterly
- [ ] Rotate API keys
- [ ] Review and update documentation
- [ ] Test disaster recovery
- [ ] Review costs and optimize

### Semi-Annually
- [ ] Rotate SSH keys
- [ ] Review OAuth credentials
- [ ] Security audit
- [ ] Performance optimization

---

## 🆘 Troubleshooting Quick Reference

### Container Won't Start
1. Check logs: `docker-compose logs`
2. Verify credentials exist: `ls -la credentials/credentials.json`
3. Check .env file: `cat .env`
4. Verify secrets in GitHub

### Deployment Fails
1. Check GitHub Actions logs
2. Verify SSH connection: `ssh root@SERVER_IP`
3. Check server disk space: `df -h`
4. Verify all secrets are set

### Authentication Errors
1. Check credentials.json is valid JSON
2. Verify OAuth tokens exist: `ls -la data/token*.json`
3. Regenerate tokens if needed
4. Check Google Cloud API status

### Performance Issues
1. Check resource usage: `docker stats`
2. Review logs for errors
3. Check API quotas in Google Cloud
4. Verify network connectivity

**📚 Full Troubleshooting:** [DEPLOYMENT.md#troubleshooting](./DEPLOYMENT.md#troubleshooting)

---

## 📞 Getting Help

**Resources:**
- 📖 [Deployment Guide](./DEPLOYMENT.md)
- 🔐 [Secrets Setup](./SECRETS_SETUP.md)
- 🚀 [Advanced Topics](./DEPLOYMENT_ADVANCED.md)
- 📋 [Quick Summary](./DEPLOYMENT_SUMMARY.md)

**Support:**
- GitHub Issues for bug reports
- GitHub Discussions for questions
- Review logs first: `docker-compose logs`
- Check GitHub Actions for CI/CD issues

---

## ✨ Success Criteria

Your deployment is successful when:

✅ Container is running without errors  
✅ Emails are being processed automatically  
✅ Data appears in Google Sheets  
✅ Health checks pass consistently  
✅ Backups are created daily  
✅ No security vulnerabilities  
✅ Resource usage is within limits  
✅ Logs show no errors  

**Congratulations! 🎉 Your FleetManager is now production-ready!**

---

**Version:** 2.0  
**Last Updated:** October 2025  
**Maintainer:** Valkozaur
