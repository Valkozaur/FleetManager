# Email Processor Service

Email processing microservice for FleetManager that handles Gmail polling, AI classification, and logistics data extraction.

## Description

This service:
- Polls Gmail accounts for new emails
- Classifies emails using Google Gemini AI
- Extracts logistics data from order emails
- Performs geocoding using Google Maps API
- Saves data to Google Sheets

## Environment Variables

- `GOOGLE_SERVICE_ACCOUNT_FILE`: Path to Google service account JSON key file
- `GMAIL_DELEGATED_USER_EMAIL`: Email address to access via domain-wide delegation
- `GEMINI_API_KEY`: Google Gemini API key for AI classification and extraction
- `GOOGLE_MAPS_API_KEY`: Google Maps API key for address geocoding
- `GOOGLE_SHEETS_SPREADSHEET_ID`: Google Sheets spreadsheet ID
- `GOOGLE_SHEETS_RANGE_NAME`: Sheet name and range (default: "Sheet1!A:Z")
- `DATA_DIR`: Directory for storing last check timestamp (default: /app/data)
- `LOG_LEVEL`: Logging level (default: INFO)
- `TEST_MODE`: Enable test mode with custom queries (default: false)
- `TEST_EMAIL_QUERY`: Custom Gmail search query when TEST_MODE is enabled

## Service Account Setup

This service uses Google Service Account authentication with domain-wide delegation.

### Prerequisites

1. **Google Workspace Admin Access** - You need admin rights to enable domain-wide delegation
2. **Google Cloud Project** - Create or use existing project at [Google Cloud Console](https://console.cloud.google.com)

### Setup Steps

1. **Create Service Account**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Navigate to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Give it a name (e.g., "fleetmanager-email-processor")
   - Click "Create and Continue"
   - Skip granting roles (not needed for domain-wide delegation)
   - Click "Done"

2. **Create Service Account Key**:
   - Click on your newly created service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose JSON format
   - Download the key file (this is your `service-account.json`)

3. **Enable Required APIs**:
   - In Google Cloud Console, go to "APIs & Services" → "Library"
   - Enable these APIs:
     - Gmail API
     - Google Sheets API
     - Google Maps API (if using geocoding)

4. **Configure Domain-Wide Delegation**:
   - In your service account details, copy the "Unique ID" (Client ID)
   - Go to [Google Workspace Admin Console](https://admin.google.com)
   - Navigate to "Security" → "Access and data control" → "API Controls"
   - Click "Manage Domain Wide Delegation"
   - Click "Add new"
   - Paste the Client ID
   - Add these OAuth scopes:
     ```
     https://www.googleapis.com/auth/gmail.readonly
     https://www.googleapis.com/auth/spreadsheets
     ```
   - Click "Authorize"

5. **Configure Environment**:
   ```bash
   # Set in your .env file
   GOOGLE_SERVICE_ACCOUNT_FILE=./service-account.json
   GMAIL_DELEGATED_USER_EMAIL=logistics@yourdomain.com
   ```

### Important Notes

- The service account will act on behalf of `GMAIL_DELEGATED_USER_EMAIL`
- This email must be a Google Workspace account in your domain
- Personal Gmail accounts (@gmail.com) cannot use domain-wide delegation
- Keep your service account key file secure and never commit it to version control

## Required Files

- `service-account.json`: Google service account key file with domain-wide delegation

## Running

### Development
```bash
python src/orders/poller/main.py
```

### Docker
```bash
docker build -t email-processor:local .
docker run -v $(pwd)/credentials:/app/credentials --env-file .env email-processor:local
```

## Dependencies

See `requirements.txt` for Python dependencies.