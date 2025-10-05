#!/bin/bash
# FleetManager Gmail API Token Generation Script

set -e

echo "🔑 Generating Gmail API tokens for FleetManager..."

# Check if credentials.json exists
if [ ! -f "credentials/credentials.json" ]; then
    echo "❌ credentials/credentials.json not found!"
    echo "Please download OAuth 2.0 credentials from Google Cloud Console"
    echo "and place them in credentials/credentials.json"
    exit 1
fi

# Create data directory
mkdir -p data

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "🐳 Using Docker for token generation..."

    # Build temporary container for authentication
    docker build -t fleetmanager-auth .

    # Run container with interactive authentication
    docker run -it --rm \
        -v "$(pwd)/credentials":/app/credentials \
        -v "$(pwd)/data":/app/data \
        fleetmanager-auth \
        python -c "
from src.orders.poller.clients.gmail_client import GmailClient
import os

try:
    gmail_client = GmailClient(
        credentials_file='/app/credentials/credentials.json',
        token_file='token.json',
        data_dir='/app/data'
    )
    print('✅ Gmail authentication successful!')
    print('Token saved to data/token.json')

    # Also generate Google Sheets token
    from src.orders.poller.clients.google_sheets_client import GoogleSheetsClient
    sheets_client = GoogleSheetsClient(
        credentials_file='/app/credentials/credentials.json',
        token_file='token_sheets.json'
    )
    if sheets_client.authenticate():
        print('✅ Google Sheets authentication successful!')
        print('Token saved to data/token_sheets.json')
    else:
        print('⚠️ Google Sheets authentication failed (optional)')

except Exception as e:
    print(f'❌ Authentication failed: {e}')
    exit(1)
"
else
    echo "🐍 Using local Python for token generation..."

    # Set up Python environment
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    # Generate Gmail token
    python3 -c "
from src.orders.poller.clients.gmail_client import GmailClient
import os

try:
    gmail_client = GmailClient(
        credentials_file='credentials/credentials.json',
        token_file='token.json',
        data_dir='data'
    )
    print('✅ Gmail authentication successful!')
    print('Token saved to data/token.json')

    # Also generate Google Sheets token
    from src.orders.poller.clients.google_sheets_client import GoogleSheetsClient
    sheets_client = GoogleSheetsClient(
        credentials_file='credentials/credentials.json',
        token_file='token_sheets.json'
    )
    if sheets_client.authenticate():
        print('✅ Google Sheets authentication successful!')
        print('Token saved to data/token_sheets.json')
    else:
        print('⚠️ Google Sheets authentication failed (optional)')

except Exception as e:
    print(f'❌ Authentication failed: {e}')
    exit(1)
"

    # Clean up
    deactivate
    rm -rf venv
fi

echo ""
echo "✅ Token generation completed!"
echo "📁 Generated files:"
echo "   - data/token.json (Gmail API token)"
echo "   - data/token_sheets.json (Google Sheets API token)"
echo ""
echo "🚀 You can now deploy FleetManager using GitHub Actions or docker-compose"