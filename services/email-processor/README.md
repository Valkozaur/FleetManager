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

- `GEMINI_API_KEY`: Google Gemini API key for AI classification and extraction
- `GOOGLE_MAPS_API_KEY`: Google Maps API key for address geocoding
- `GOOGLE_SHEETS_SPREADSHEET_ID`: Google Sheets spreadsheet ID
- `GOOGLE_SHEETS_RANGE_NAME`: Sheet name and range (default: "Sheet1!A:Z")
- `LOG_LEVEL`: Logging level (default: INFO)

## Required Files

- `credentials.json`: Google Cloud OAuth 2.0 client credentials
- `token.json`: OAuth token for Gmail API
- `token_sheets.json`: OAuth token for Google Sheets API

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