# Secrets Management Guide

This guide explains how to securely set up and manage secrets for FleetManager deployment with GitHub Actions.

## Overview

FleetManager requires several secrets for automated deployment:
- **Google OAuth Credentials** - For Gmail and Sheets API access
- **API Keys** - For Gemini AI and Google Maps
- **SSH Keys** - For server deployment
- **Configuration** - Spreadsheet IDs and other settings

## Table of Contents

1. [GitHub Secrets Setup](#github-secrets-setup)
2. [Google Cloud Credentials](#google-cloud-credentials)
3. [SSH Key Configuration](#ssh-key-configuration)
4. [API Keys Setup](#api-keys-setup)
5. [Verification](#verification)
6. [Security Best Practices](#security-best-practices)
7. [Troubleshooting](#troubleshooting)

---

## GitHub Secrets Setup

### Access GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each secret below

### Required Secrets Checklist

#### Server Connection Secrets

| Secret Name | Description | Example/Format |
|------------|-------------|----------------|
| `HETZNER_HOST` | Your server IP address | `123.456.789.012` |
| `HETZNER_USER` | SSH username (usually `root`) | `root` |
| `HETZNER_SSH_KEY` | Private SSH key for authentication | See [SSH Key Setup](#ssh-key-configuration) |
| `HETZNER_PORT` | SSH port (optional, defaults to 22) | `22` |

#### Application Secrets

| Secret Name | Description | Where to Get It |
|------------|-------------|-----------------|
| `GOOGLE_CREDENTIALS_JSON` | Google OAuth 2.0 credentials | [Google Cloud Console](#google-cloud-credentials) |
| `GEMINI_API_KEY` | Google Gemini API key | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `GOOGLE_MAPS_API_KEY` | Google Maps Geocoding API key | [Google Cloud Console](https://console.cloud.google.com/) |
| `GOOGLE_SHEETS_SPREADSHEET_ID` | Your Google Sheet ID | From Sheet URL (see below) |
| `GOOGLE_SHEETS_RANGE_NAME` | Sheet range (optional) | Default: `Sheet1!A:Z` |

---

## Google Cloud Credentials

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Enter project name: `FleetManager`
4. Click **Create**

### Step 2: Enable Required APIs

Enable these APIs in your project:

1. **Gmail API**
   - Search for "Gmail API" in the API Library
   - Click **Enable**

2. **Google Sheets API**
   - Search for "Google Sheets API"
   - Click **Enable**

3. **Google Maps Geocoding API**
   - Search for "Geocoding API"
   - Click **Enable**

4. **Google Gemini API**
   - Go to [Google AI Studio](https://aistudio.google.com/)
   - Enable the API and create an API key

### Step 3: Create OAuth 2.0 Credentials

1. In Google Cloud Console, go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. If prompted, configure OAuth consent screen:
   - User Type: **External**
   - App name: `FleetManager`
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: Add `gmail.readonly` and `spreadsheets`
   - Test users: Add your Gmail address

4. Create OAuth Client ID:
   - Application type: **Desktop app**
   - Name: `FleetManager Desktop Client`
   - Click **Create**

5. **Download the JSON file**
   - Click the download icon next to your OAuth client
   - This downloads `client_secret_xxx.json`

### Step 4: Add Credentials to GitHub Secrets

The credentials JSON file looks like this:

```json
{
  "installed": {
    "client_id": "xxxxx.apps.googleusercontent.com",
    "project_id": "fleetmanager-xxxxx",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "GOCSPX-xxxxx",
    "redirect_uris": ["http://localhost"]
  }
}
```

**Add to GitHub:**
1. Copy the **entire contents** of the JSON file
2. In GitHub Secrets, create new secret:
   - Name: `GOOGLE_CREDENTIALS_JSON`
   - Value: Paste the entire JSON content
3. Click **Add secret**

---

## SSH Key Configuration

### Step 1: Generate SSH Key Pair

On your local machine:

```bash
# Generate a new SSH key specifically for GitHub Actions
ssh-keygen -t ed25519 -C "github-actions-fleetmanager" -f ~/.ssh/fleetmanager_deploy

# This creates two files:
# - ~/.ssh/fleetmanager_deploy (private key)
# - ~/.ssh/fleetmanager_deploy.pub (public key)
```

### Step 2: Add Public Key to Hetzner Server

```bash
# Copy the public key
cat ~/.ssh/fleetmanager_deploy.pub

# SSH to your Hetzner server
ssh root@YOUR_SERVER_IP

# Add the public key to authorized_keys
mkdir -p ~/.ssh
echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### Step 3: Add Private Key to GitHub Secrets

```bash
# Display the private key
cat ~/.ssh/fleetmanager_deploy
```

Copy the **entire output** including the `-----BEGIN` and `-----END` lines:

```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
...
-----END OPENSSH PRIVATE KEY-----
```

**Add to GitHub:**
1. Create new secret: `HETZNER_SSH_KEY`
2. Paste the entire private key (including BEGIN/END lines)
3. Click **Add secret**

### Step 4: Verify SSH Access

Test the SSH connection:

```bash
ssh -i ~/.ssh/fleetmanager_deploy root@YOUR_SERVER_IP

# If successful, you should connect without password
```

---

## API Keys Setup

### Google Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **Create API key**
3. Select your Google Cloud project (FleetManager)
4. Copy the API key

**Add to GitHub:**
- Secret Name: `GEMINI_API_KEY`
- Value: Your API key (starts with `AIza...`)

### Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Click **Create Credentials** → **API Key**
4. Click **Restrict Key** (recommended):
   - API restrictions: Select **Geocoding API**
   - Save

**Add to GitHub:**
- Secret Name: `GOOGLE_MAPS_API_KEY`
- Value: Your API key

### Google Sheets Configuration

#### Get Spreadsheet ID

1. Open your Google Sheet
2. Look at the URL: 
   ```
   https://docs.google.com/spreadsheets/d/1ABC123xyz456DEF789/edit
   ```
3. The Spreadsheet ID is: `1ABC123xyz456DEF789`

**Add to GitHub:**
- Secret Name: `GOOGLE_SHEETS_SPREADSHEET_ID`
- Value: Your spreadsheet ID

#### Set Range Name (Optional)

**Add to GitHub:**
- Secret Name: `GOOGLE_SHEETS_RANGE_NAME`
- Value: `Sheet1!A:Z` (or your preferred range)

---

## Verification

### Verify All Secrets Are Set

Run this checklist in your GitHub repository:

**Go to Settings → Secrets → Actions and verify:**

- [ ] `HETZNER_HOST` - Server IP address
- [ ] `HETZNER_USER` - SSH username (root)
- [ ] `HETZNER_SSH_KEY` - Private SSH key (includes BEGIN/END lines)
- [ ] `GOOGLE_CREDENTIALS_JSON` - Complete OAuth JSON
- [ ] `GEMINI_API_KEY` - Starts with `AIza`
- [ ] `GOOGLE_MAPS_API_KEY` - Google Maps API key
- [ ] `GOOGLE_SHEETS_SPREADSHEET_ID` - Sheet ID from URL
- [ ] `GOOGLE_SHEETS_RANGE_NAME` - Sheet range (optional)

### Test SSH Connection

Create a test workflow to verify SSH:

```yaml
# .github/workflows/test-ssh.yml
name: Test SSH Connection
on: workflow_dispatch

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - name: Test SSH
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.HETZNER_HOST }}
        username: ${{ secrets.HETZNER_USER }}
        key: ${{ secrets.HETZNER_SSH_KEY }}
        script: |
          echo "✅ SSH connection successful!"
          docker --version
          whoami
          pwd
```

Run it manually from the Actions tab.

### Test Deployment

Once all secrets are set:

1. Push to `main` branch
2. Check **Actions** tab
3. Watch the deployment workflow
4. Verify each step completes successfully

---

## Security Best Practices

### Protect Your Secrets

✅ **DO:**
- Use GitHub Secrets for all sensitive data
- Rotate API keys regularly (every 90 days)
- Use SSH keys instead of passwords
- Restrict API keys to specific APIs
- Use separate credentials for development and production
- Enable 2FA on all Google accounts
- Review GitHub Actions logs for exposed secrets

❌ **DON'T:**
- Commit secrets to git (use `.gitignore`)
- Share secrets in chat or email
- Use production credentials for testing
- Give secrets overly broad permissions
- Store secrets in code comments
- Use weak SSH keys (use ed25519 or RSA 4096)

### Credential Rotation

**Regular rotation schedule:**
- SSH keys: Every 6 months
- API keys: Every 90 days
- OAuth tokens: Regenerate if compromised

**How to rotate:**

1. **API Keys:**
   - Create new key in Google Cloud Console
   - Update GitHub Secret
   - Test deployment
   - Revoke old key

2. **SSH Keys:**
   - Generate new key pair
   - Add new public key to server
   - Update GitHub Secret with new private key
   - Test deployment
   - Remove old public key from server

3. **OAuth Credentials:**
   - Create new OAuth client in Google Cloud
   - Update GitHub Secret
   - Test deployment
   - Delete old OAuth client

### Monitor Access

- Check GitHub Actions logs regularly
- Review Google Cloud audit logs
- Monitor API usage in Google Cloud Console
- Set up billing alerts for unexpected API usage

---

## Troubleshooting

### Common Issues

#### "Permission denied (publickey)" Error

**Cause:** SSH key not properly configured

**Solution:**
```bash
# Verify private key format
cat ~/.ssh/fleetmanager_deploy
# Should start with: -----BEGIN OPENSSH PRIVATE KEY-----

# Verify public key is on server
ssh root@YOUR_SERVER_IP "cat ~/.ssh/authorized_keys"
```

#### "Invalid credentials" Error

**Cause:** `GOOGLE_CREDENTIALS_JSON` is malformed

**Solution:**
```bash
# Validate JSON locally
cat credentials.json | python3 -m json.tool

# Ensure entire JSON is copied to GitHub Secret
# Including opening and closing braces
```

#### "API key not found" Error

**Cause:** API key secret name mismatch or empty value

**Solution:**
- Verify secret name exactly matches: `GEMINI_API_KEY`
- Ensure no extra spaces in the key value
- Regenerate key if necessary

#### "Spreadsheet not found" Error

**Cause:** Incorrect spreadsheet ID or insufficient permissions

**Solution:**
```bash
# Verify spreadsheet ID format (no spaces)
# Correct: 1ABC123xyz456DEF789
# Wrong: https://docs.google.com/spreadsheets/d/1ABC123xyz456DEF789/

# Ensure authenticated Google account has access to the sheet
```

#### Container Fails Health Check

**Cause:** Credentials not accessible in container

**Solution:**
```bash
# SSH to server and check
ssh root@YOUR_SERVER_IP
cd ~/fleetmanager

# Verify credentials file
ls -la credentials/credentials.json

# Check container logs
docker-compose logs
```

### Debug Mode

Enable debug logging in GitHub Actions:

1. Go to Settings → Secrets → Actions
2. Add new secret:
   - Name: `ACTIONS_STEP_DEBUG`
   - Value: `true`
3. Re-run workflow

---

## Quick Reference

### Complete Setup Commands

```bash
# 1. Generate SSH key
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/fleetmanager_deploy

# 2. Copy public key to server
ssh-copy-id -i ~/.ssh/fleetmanager_deploy.pub root@YOUR_SERVER_IP

# 3. Test SSH connection
ssh -i ~/.ssh/fleetmanager_deploy root@YOUR_SERVER_IP

# 4. Display private key for GitHub Secret
cat ~/.ssh/fleetmanager_deploy
```

### GitHub Secrets Summary

```bash
# Server Connection
HETZNER_HOST=123.456.789.012
HETZNER_USER=root
HETZNER_SSH_KEY=<private key with BEGIN/END lines>
HETZNER_PORT=22

# Google OAuth
GOOGLE_CREDENTIALS_JSON=<entire credentials JSON>

# API Keys
GEMINI_API_KEY=AIza...
GOOGLE_MAPS_API_KEY=AIza...

# Configuration
GOOGLE_SHEETS_SPREADSHEET_ID=1ABC123xyz456DEF789
GOOGLE_SHEETS_RANGE_NAME=Sheet1!A:Z
```

---

## Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review GitHub Actions logs
3. Verify all secrets are correctly set
4. Check server logs: `docker-compose logs`
5. Open a GitHub issue with error details

---

**Last Updated:** October 2025  
**Version:** 1.0
