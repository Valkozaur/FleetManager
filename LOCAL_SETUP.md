# Local Testing Setup for Gmail Poller

## Prerequisites

1. **Python 3.8+** installed on your system
2. **pip** package manager
3. **Google Cloud Project** with Gmail API enabled
4. **OAuth 2.0 Credentials** from Google Cloud Console

## Step 1: Gmail API Setup

### 1.1 Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing one)
3. Enable the **Gmail API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

### 1.2 Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "+ CREATE CREDENTIALS" > "OAuth client ID"
3. Select "Desktop app" as application type
4. Give it a name (e.g., "Gmail Poller Local")
5. Click "Create"
6. Download the JSON file and save it as `credentials.json` in the project root

## Step 2: Local Environment Setup

### 2.1 Install Dependencies
```bash
pip install -r requirements.txt
```

### 2.2 Create Local Configuration
```bash
cp .env.example .env
```

### 2.3 Update .env for Local Testing
```bash
# Local paths
GMAIL_CREDENTIALS_FILE=./credentials.json
DATA_DIR=./data
LOG_LEVEL=DEBUG
OUTPUT_FILE=./data/emails.json
```

## Step 3: Run Locally

### 3.1 Create Required Directories
```bash
mkdir -p data logs
```

### 3.2 First Run (Authentication)
The first time you run the poller, it will open a browser window for OAuth authentication:

```bash
python src/orders/poller/main.py
```

1. A browser window will open
2. Sign in with your Google account
3. Grant permissions to the application
4. The application will save the token for future runs

### 3.3 Subsequent Runs
After the initial authentication, you can run the poller without the browser prompt:

```bash
python src/orders/poller/main.py
```

## Step 4: Testing

### 4.1 Check Output
The poller saves emails to `./data/emails.json`:

```bash
cat ./data/emails.json
```

### 4.2 View Logs
```bash
cat ./logs/gmail_poller.log
```

### 4.3 Test Different Queries
Modify the `EMAIL_QUERY` in `.env` to test different filters:

```bash
# Get unread emails
EMAIL_QUERY=is:unread

# Get emails from specific sender
EMAIL_QUERY=from:specific@domain.com

# Get emails with specific subject
EMAIL_QUERY=subject:"Order Confirmation"
```

## Step 5: Headless Server Setup (Hetzner)

For servers without browsers, use the headless authentication method:

### 5.1 Generate Authorization URL
```bash
python scripts/setup_auth.py --generate-url
```

### 5.2 Complete Authentication
1. Copy the generated URL
2. Open it in a browser on your local machine
3. Complete the OAuth flow
4. Copy the authorization code
5. Setup on the server:
```bash
python scripts/setup_auth.py --code 'your_auth_code_here'
```

### 5.3 Import/Export Tokens
```bash
# Export token from local machine
python scripts/setup_auth.py --export-token

# Copy exported_token.json to server
# Import on server
python scripts/setup_auth.py --import-token ./exported_token.json
```

### 5.4 Check Setup
```bash
python scripts/setup_auth.py --check
```

## Step 6: Common Issues

### 6.1 Authentication Issues
If you get authentication errors:
1. Check authentication setup: `python scripts/setup_auth.py --check`
2. Delete authentication files and re-run setup
3. Ensure you have the correct scopes in Google Cloud Console

### 6.2 Missing Credentials
If you get "credentials file not found":
1. Ensure `credentials.json` is in the project root
2. Check the path in `.env` file
3. Verify the file is valid JSON

### 6.3 API Quota Issues
If you hit rate limits:
1. Wait a few minutes before running again
2. Reduce `MAX_EMAILS` in `.env`
3. Check Google Cloud Console for quota limits

### 6.4 Headless Server Issues
For servers without browsers:
1. Use the `setup_auth.py` script
2. Complete OAuth flow on a machine with browser
3. Import the authorization code or token to the server

## Step 6: Development Tips

### 6.1 Run in Debug Mode
Set `LOG_LEVEL=DEBUG` in `.env` for detailed logging:

```bash
LOG_LEVEL=DEBUG
```

### 6.2 Test with Specific Date Range
To test emails from a specific date:

```bash
EMAIL_QUERY=after:2024/01/01 before:2024/01/31
```

### 6.3 Monitor API Usage
Check your Google Cloud Console for API usage and quotas.

## Next Steps

Once local testing is complete, you can proceed with:
1. Docker container testing
2. Hetzner deployment
3. Production configuration