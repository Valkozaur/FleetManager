# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FleetManager is a Python-based application that processes fleet management orders through email polling and AI-powered document analysis. The system integrates with Gmail API to fetch emails and uses Google's Gemini AI for order processing and cargo extraction from email attachments.

## Architecture

### Core Components

1. **Gmail Poller** (`src/orders/poller/`)
   - `main.py`: Main entry point for the Gmail polling service
   - `gmail_client.py`: Handles Gmail API authentication and email fetching
   - `enhanced_poller.py`: Advanced polling with additional features

2. **Gemini Integration** (`src/gemini_integration/`)
   - `client.py`: Main Gemini AI client wrapper
   - `classifier.py`: Document classification using AI
   - `cargo_extractor.py`: Extracts cargo information from documents
   - `attachment_processor.py`: Processes email attachments
   - `schemas.py`: Data models and validation schemas
   - `error_handling.py`: Centralized error handling

### Data Flow

1. Gmail Poller fetches emails from Gmail API
2. Emails are processed and attachments extracted
3. Gemini AI analyzes documents and extracts order information
4. Processed data is saved to JSON files in the `data/` directory

## Development Commands

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Gmail poller
python src/orders/poller/main.py

# Test the complete setup locally
python test_local.py

# Check authentication setup
python scripts/setup_auth.py --check
```

### Docker Commands

```bash
# Build the Docker image
docker-compose build

# Run the Gmail poller container
docker-compose up gmail-poller

# Run with monitoring profile
docker-compose --profile monitoring up

# Stop all services
docker-compose down
```

### Authentication Setup

```bash
# Generate authorization URL for headless servers
python scripts/setup_auth.py --generate-url

# Complete authentication with code
python scripts/setup_auth.py --code 'your_auth_code_here'

# Export token from local machine
python scripts/setup_auth.py --export-token

# Import token on server
python scripts/setup_auth.py --import-token ./exported_token.json
```

## Configuration

### Environment Variables

The application uses environment variables configured in `.env`:

- `GMAIL_CREDENTIALS_FILE`: Path to Gmail API credentials JSON
- `DATA_DIR`: Directory for storing processed data
- `LOG_DIR`: Directory for log files
- `MAX_EMAILS`: Maximum number of emails to fetch per run
- `EMAIL_QUERY`: Gmail search query for filtering emails
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `OUTPUT_FILE`: Path for output JSON file

### Gmail API Setup

1. Create Google Cloud Project with Gmail API enabled
2. Create OAuth 2.0 credentials (Desktop app type)
3. Download credentials as `credentials.json`
4. Complete OAuth flow using `setup_auth.py` script

## File Structure

```
src/
├── orders/poller/          # Gmail polling functionality
│   ├── main.py            # Main poller entry point
│   ├── gmail_client.py    # Gmail API client
│   └── enhanced_poller.py # Enhanced polling features
├── gemini_integration/    # AI-powered document processing
│   ├── client.py          # Gemini AI client
│   ├── classifier.py      # Document classification
│   ├── cargo_extractor.py # Cargo information extraction
│   ├── attachment_processor.py # Attachment handling
│   ├── schemas.py         # Data models
│   └── error_handling.py  # Error handling
data/                      # Processed data storage
logs/                      # Application logs
scripts/                   # Utility scripts
├── setup_auth.py         # Authentication setup
└── deploy.sh            # Deployment script
```

## Important Notes

- The application requires Gmail API OAuth 2.0 credentials
- First run requires browser-based authentication
- Subsequent runs use saved authentication tokens
- The system is designed for headless server deployment
- Docker configuration includes resource limits for production use
- Use `test_local.py` for comprehensive local testing
- Authentication tokens can be exported/imported for server deployment