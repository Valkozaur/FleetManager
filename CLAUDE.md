# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FleetManager is a truck fleet management system that processes emails to extract logistics orders and data. The system automatically polls Gmail accounts, classifies emails using AI, and extracts structured logistics information.

## Architecture

### Core Components

- **Gmail Client** (`src/orders/poller/clients/gmail_client.py`): Handles OAuth 2.0 authentication with Gmail API and fetches emails with attachments
- **Google Maps Client** (`src/orders/poller/clients/google_maps_client.py`): Provides geocoding services to convert addresses to coordinates
- **Google Sheets Client** (`src/orders/poller/clients/google_sheets_client.py`): Saves extracted logistics data to Google Sheets as a database
- **Email Classifier** (`src/orders/poller/services/classifier.py`): Uses Google Gemini API to classify emails as Order, Invoice, or Other
- **Logistics Extractor** (`src/orders/poller/services/logistics_data_extract.py`): Extracts structured logistics data from order emails using Gemini API and fills missing coordinates with geocoding
- **Email Models** (`src/orders/poller/models/email.py`, `src/orders/poller/models/logistics.py`): Pydantic models for email and logistics data structures

### Data Flow

1. Gmail client fetches unread emails using `is:unread` query
2. Each email is classified using Gemini API (`gemini-2.5-flash-lite-preview-09-2025`)
3. For emails classified as "Order", logistics data is extracted (addresses, dates, cargo details, etc.)
4. If coordinates are missing from extracted data, Google Maps Geocoding API is used to convert addresses to coordinates
5. Complete logistics data with email identifiers is saved to Google Sheets database
6. All data including email metadata (subject, sender, date) and logistics details are stored as rows

## Environment Setup

### Required Environment Variables
- `GEMINI_API_KEY`: Google Gemini API key for AI classification and extraction
- `GOOGLE_MAPS_API_KEY`: Google Maps API key for address geocoding
- `GOOGLE_SHEETS_SPREADSHEET_ID`: Google Sheets spreadsheet ID for database storage
- `GOOGLE_SHEETS_RANGE_NAME`: Sheet name and range (default: "Sheet1!A:Z")
- `LOG_LEVEL`: Logging level (default: INFO)

### Required Files
- `credentials.json`: Google Cloud OAuth 2.0 client credentials file
- `token.json`: OAuth token file for Gmail API (auto-generated after first authentication)
- `token_sheets.json`: OAuth token file for Google Sheets API (auto-generated after first authentication)

### Python Dependencies
Key dependencies include Google APIs, Gemini AI client, and Pydantic for data validation.

## Running the Application

### Main Entry Point
```bash
python src/orders/poller/main.py
```

The application is designed to be cron-friendly and exits with appropriate status codes:
- Exit code 0: Success
- Exit code 1: Error occurred

### Authentication
The Gmail client supports multiple authentication methods:
1. **Interactive OAuth**: Opens browser for user authentication
2. **Headless Authentication**: Uses pre-generated auth codes or imported tokens for server deployment

## Key Implementation Details

### AI Integration
- Uses Google Gemini Developer API with structured response schemas
- Low temperature (0.1) for consistent classification and extraction
- Enum-based classification for reliable type safety

### Email Processing
- Supports both plain text and HTML email bodies
- Handles file attachments and includes them in AI processing
- Tracks last check timestamp to avoid processing duplicates

### Google Sheets Database Integration
- Automatically creates headers in the target Google Sheet if they don't exist
- Stores both email identifiers and extracted logistics data in structured rows
- Columns include: email_id, subject, sender, date, loading_address, unloading_address, loading_date, unloading_date, coordinates, cargo_description, weight, vehicle_type, special_requirements
- Uses OAuth 2.0 authentication with separate token file for Sheets API
- Graceful degradation if Google Sheets authentication or saving fails

### Error Handling
- Graceful degradation when AI extraction fails
- Comprehensive logging for debugging email processing issues
- Individual email failures don't stop batch processing

## Development Notes

- The system uses relative imports within the `src/orders/poller/` package
- All AI clients are properly closed after use to prevent resource leaks
- Logging is configured dynamically based on environment variables
- The application maintains state across runs using timestamp files