# FleetManager Email Processor Docker Image

Docker image for the FleetManager email processing service that automatically polls Gmail, classifies emails using AI, and extracts logistics data.

## Quick Start

```bash
docker pull ghcr.io/valkozaur/fleetmanager-email-processor:latest

docker run -d \
  --name email-processor \
  -v $(pwd)/credentials:/app/credentials \
  -e GOOGLE_SERVICE_ACCOUNT_FILE=/app/credentials/service-account.json \
  -e GMAIL_DELEGATED_USER_EMAIL=logistics@yourdomain.com \
  -e GEMINI_API_KEY=your_gemini_api_key \
  -e GOOGLE_MAPS_API_KEY=your_maps_api_key \
  -e GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id \
  ghcr.io/valkozaur/fleetmanager-email-processor:latest
```

## What This Image Does

This service continuously:
1. **Polls Gmail** for new emails using Google Service Account authentication
2. **Classifies emails** using Google Gemini AI (Order, Invoice, or Other)
3. **Extracts logistics data** from order emails (pickup/delivery locations, dates, contact info)
4. **Geocodes addresses** to coordinates using Google Maps API (optional)
5. **Saves to Google Sheets** for easy tracking and management (optional)

## Required Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_SERVICE_ACCOUNT_FILE` | **Yes** | Path to service account JSON key (mount as volume) |
| `GMAIL_DELEGATED_USER_EMAIL` | **Yes** | Email address to monitor via domain-wide delegation |
| `GEMINI_API_KEY` | **Yes** | Google Gemini API key for AI processing |
| `GOOGLE_MAPS_API_KEY` | No | Google Maps API key for geocoding addresses |
| `GOOGLE_SHEETS_SPREADSHEET_ID` | No | Spreadsheet ID to save extracted data |
| `GOOGLE_SHEETS_RANGE_NAME` | No | Sheet range (default: "Sheet1!A:Z") |
| `DATA_DIR` | No | Directory for state storage (default: /app/data) |
| `LOG_LEVEL` | No | Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO) |
| `TEST_EMAIL_QUERY` | No | Optional Gmail search query to filter emails (e.g., "subject:test") |

### Volume Mounts

**Required:**
- `/app/credentials` - Mount directory containing `service-account.json`

**Optional but recommended:**
- `/app/data` - Persistent storage for last check timestamps
- `/app/logs` - Application logs

## Setup Guide

### 1. Google Service Account Setup

This service requires a Google Service Account with domain-wide delegation enabled. This allows it to access Gmail on behalf of a user.

#### Prerequisites
- Google Workspace account (domain-wide delegation doesn't work with personal Gmail)
- Google Workspace admin access
- Google Cloud Project

#### Steps

1. **Create Service Account in Google Cloud Console:**
   ```
   1. Go to https://console.cloud.google.com
   2. Navigate to "IAM & Admin" → "Service Accounts"
   3. Click "Create Service Account"
   4. Name it (e.g., "fleetmanager-email-processor")
   5. Create and download JSON key file
   ```

2. **Enable Required APIs:**
   - Gmail API
   - Google Sheets API (if using Sheets integration)
   - Google Maps API (if using geocoding)

3. **Configure Domain-Wide Delegation:**
   ```
   1. Copy the service account's Client ID
   2. Go to https://admin.google.com
   3. Navigate to Security → Access and data control → API Controls
   4. Click "Manage Domain Wide Delegation"
   5. Add new with these scopes:
      - https://www.googleapis.com/auth/gmail.readonly
      - https://www.googleapis.com/auth/spreadsheets
   ```

### 2. Get API Keys

- **Gemini API**: Get from [Google AI Studio](https://aistudio.google.com/apikey)
- **Google Maps API**: Get from [Google Cloud Console](https://console.cloud.google.com/google/maps-apis)

### 3. Prepare Credentials Directory

```bash
mkdir -p ./credentials
# Place your service-account.json file here
cp /path/to/your/service-account.json ./credentials/
chmod 600 ./credentials/service-account.json
```

## Running the Container

### Using Docker Run

```bash
docker run -d \
  --name email-processor \
  --restart unless-stopped \
  -v $(pwd)/credentials:/app/credentials \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -e GOOGLE_SERVICE_ACCOUNT_FILE=/app/credentials/service-account.json \
  -e GMAIL_DELEGATED_USER_EMAIL=logistics@yourdomain.com \
  -e GEMINI_API_KEY=your_gemini_api_key \
  -e GOOGLE_MAPS_API_KEY=your_maps_api_key \
  -e GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id \
  -e LOG_LEVEL=INFO \
  ghcr.io/valkozaur/fleetmanager-email-processor:latest
```

### Using Docker Compose

```yaml
version: '3.8'

services:
  email-processor:
    image: ghcr.io/valkozaur/fleetmanager-email-processor:latest
    container_name: email-processor
    restart: unless-stopped
    volumes:
      - ./credentials:/app/credentials:ro
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - GOOGLE_SERVICE_ACCOUNT_FILE=/app/credentials/service-account.json
      - GMAIL_DELEGATED_USER_EMAIL=logistics@yourdomain.com
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}
      - GOOGLE_SHEETS_SPREADSHEET_ID=${GOOGLE_SHEETS_SPREADSHEET_ID}
      - LOG_LEVEL=INFO
```

Run with:
```bash
docker-compose up -d
```

## Debugging

### Enable Debug Logging

```bash
docker run -d \
  --name email-processor \
  -v $(pwd)/credentials:/app/credentials \
  -e LOG_LEVEL=DEBUG \
  # ... other env vars ...
  ghcr.io/valkozaur/fleetmanager-email-processor:latest
```

### Custom Email Filtering

You can filter emails using Gmail search syntax with `TEST_EMAIL_QUERY`. This supplements the timestamp-based filtering:

```bash
docker run -d \
  --name email-processor \
  -v $(pwd)/credentials:/app/credentials \
  -e TEST_EMAIL_QUERY="subject:test order" \
  # ... other env vars ...
  ghcr.io/valkozaur/fleetmanager-email-processor:latest
```

Useful query examples:
- `subject:"test order"` - Only emails with "test order" in subject
- `from:sender@example.com` - Only emails from specific sender
- `subject:test` - Simple keyword match
- Queries are combined with timestamp filter (fetches emails after last check)

### View Logs

```bash
docker logs -f email-processor
```

### Access Container

```bash
docker exec -it email-processor /bin/bash
```

## Health Check

The image includes a built-in health check that verifies:
- Python environment is working
- Credentials directory exists

Check container health:
```bash
docker inspect --format='{{.State.Health.Status}}' email-processor
```

## Security Notes

- **Never commit** your `service-account.json` to version control
- Mount credentials directory as **read-only** (`:ro`) when possible
- Use **secrets management** in production (Docker secrets, Kubernetes secrets, etc.)
- The container runs as **non-root user** (appuser, UID 1000)
- Credentials directory has **restrictive permissions** (700)

## Troubleshooting

### "Permission denied" on credentials
```bash
# Fix file permissions
chmod 600 ./credentials/service-account.json
```

### "Domain-wide delegation required"
Ensure you've configured domain-wide delegation in Google Workspace Admin Console with the correct scopes.

### "Invalid credentials"
Verify that:
- Service account JSON file is valid
- File path in `GOOGLE_SERVICE_ACCOUNT_FILE` matches mounted location
- Service account has domain-wide delegation enabled

### No emails being processed
Check:
- Gmail account has new emails since last check timestamp
- Service account has proper Gmail API access
- Use `TEST_EMAIL_QUERY="subject:test"` with specific query to debug
- Check `/app/data/last_check.txt` for watermark timestamp

## Image Tags

- `latest` - Latest stable release from main branch
- `develop` - Latest development build
- `vX.Y.Z` - Specific version tags

## Source Code

- Repository: [github.com/Valkozaur/FleetManager](https://github.com/Valkozaur/FleetManager)
- Service Directory: `services/email-processor/`

## Support

For issues and questions:
- GitHub Issues: [github.com/Valkozaur/FleetManager/issues](https://github.com/Valkozaur/FleetManager/issues)
- Documentation: See `services/email-processor/README.md` in repository

## License

MIT License - See repository for details
