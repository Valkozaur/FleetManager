# FleetManager Copilot Instructions

## Project Overview
FleetManager is a microservice-based logistics system that automates email processing for truck fleet management. Only the email-processor service is production-ready; ui and api-gateway are placeholders.

## Architecture Essentials

### Service Structure
- **Monorepo**: Services under `services/`; only `services/email-processor` is active
- **Entry Point**: `services/email-processor/src/orders/poller/main.py` wires all clients and pipeline steps
- **Shared Code**: Despite `shared/` folder at root, email-processor has its own copies under `services/email-processor/src/orders/poller/`—always edit the service-local versions

### Pipeline Architecture
The processing flow is a strictly ordered pipeline defined by `ProcessingOrder` enum:

1. **CLASSIFICATION** (1) - Critical step; pipeline aborts if it fails
2. **LOGISTICS_EXTRACTION** (2) - Runs only for Order emails
3. **GEOCODING** (3) - Optional; fills missing coordinates
4. **DATABASE_SAVE** (4) - Optional; writes to Google Sheets

**Key Pattern**: Steps communicate through `ProcessingContext`, which passes `email`, `classification`, `logistics_data`, and `custom_data`. Steps mutate the context directly—never return raw dicts.

### Processing Steps Details

**EmailClassificationStep** (`steps/classification_step.py`)
- Wraps `MailClassifier` which uses Gemini `gemini-2.5-flash-lite-preview-09-2025`
- Uses `response_schema=MailClassificationEnum` for structured output
- Enum values MUST remain: `"Order"`, `"Invoice"`, `"Other"` (exact casing matters)

**LogisticsExtractionStep** (`steps/logistics_extraction_step.py`)
- Uses `LogisticsDataExtractor` with model `gemini-2.5-flash-preview-09-2025`
- Returns `LogisticsDataExtract` (Pydantic model) with both logistics fields AND email metadata
- Validates JSON response against schema; returns None on failure

**GeocodingStep** (`steps/geocoding_step.py`)
- Only runs when `should_process` detects missing coordinates but present addresses
- Calls `GoogleMapsClient.geocode_address()` for each missing coordinate pair
- Gracefully degrades on API failures (logs warning, continues)

**DatabaseSaveStep** (`steps/database_save_step.py`)
- Creates headers once via `create_headers_if_not_exist()` on first run
- Mutates `context.logistics_data` to inject `email_id`, `email_subject`, `email_sender`, `email_date` if missing
- Skipped entirely when `GOOGLE_SHEETS_SPREADSHEET_ID` env var not set

## External Integrations

### Gmail API
- Uses **service account authentication** with domain-wide delegation
- Service account acts on behalf of `GMAIL_DELEGATED_USER_EMAIL`
- No tokens needed - authenticates directly with service account key file at `GOOGLE_SERVICE_ACCOUNT_FILE`
- Tracks last check timestamp in `{DATA_DIR}/last_check.txt`
- Fetches emails with query (default: `is:unread`); supports custom queries via `TEST_EMAIL_QUERY`

### Google Gemini API
- **Classification**: `gemini-2.5-flash-lite-preview-09-2025` with `temperature=0.1`, `response_mime_type="text/x.enum"`
- **Extraction**: `gemini-2.5-flash-preview-09-2025` with `temperature=0.1`, `response_mime_type="application/json"`
- Prompt construction in `services/email_prompt_construct.py` handles attachments via `types.Part` with inline data
- Both clients MUST be closed via `.close()` in `main.run()` finally block

### Google Maps API (Optional)
- Only initialized if `GOOGLE_MAPS_API_KEY` is set
- Used exclusively by `GeocodingStep` for address→coordinates conversion
- Returns tuple `(lat, lng)` or None on failure

### Google Sheets API (Optional)
- Uses **service account authentication** (same key as Gmail)
- Requires `GOOGLE_SHEETS_SPREADSHEET_ID` + service account key at `GOOGLE_SERVICE_ACCOUNT_FILE`
- Headers: `email_id`, `email_subject`, `email_sender`, `email_date`, + 10 logistics fields
- Graceful degradation: if auth fails or env var missing, step is skipped

## Developer Workflows

### Local Development
```bash
cd services/email-processor
# Loads .env or .env.local automatically
python src/orders/poller/main.py
```

### Docker Development
```bash
# From repo root
docker-compose up email-processor
# Mounts ./credentials as /app/credentials and uses service Dockerfile
```

### Testing
```bash
cd services/email-processor
pytest
# Note: root pyproject.toml testpaths=["tests/"] won't find service tests
```

### Debugging Mode
Set in `.env`:
```
TEST_EMAIL_QUERY=subject:"test order"
LOG_LEVEL=DEBUG
```
- `TEST_EMAIL_QUERY`: Custom Gmail search query to filter emails (supplements timestamp-based filtering)
- Examples: `subject:test`, `from:user@example.com`, `subject:"test order"`

### Deployment (CI/CD)
- **Trigger**: Push to `main`/`develop` or manual dispatch
- **Process**: GitHub Actions → Build image → Push to GHCR → Deploy to Hetzner via SSH
- **Hetzner Setup**: Server at `/opt/fleetmanager` runs `docker-compose.prod.yml`
- **Secrets Required**: `HETZNER_HOST`, `HETZNER_SSH_KEY`, `HETZNER_FIREWALL_TOKEN`, `HETZNER_FIREWALL_ID`
- See `docs/DEPLOYMENT.md` for complete setup

## Critical Conventions

### New Pipeline Steps
1. Subclass `ProcessingStep` with unique `ProcessingOrder` integer
2. Implement `process(context) → ProcessingResult`
3. Implement `should_process(context) → bool` to enable conditional execution
4. Critical steps (currently only CLASSIFICATION) abort pipeline on failure; others log errors and continue

### Client Lifecycle
- All clients with persistent connections (Gemini, Maps, Sheets) MUST expose `close()` method
- Main script calls `close()` in finally block after processing completes
- Add new clients to finally block in `main.run()`

### Logging
- **Format**: ASCII only (no Unicode in log messages, even for international data)
- **Level**: Configured via `LOG_LEVEL` env var, reconfigured in `main.run()`
- **Style**: Use `logger.info(f"Processing email: {email.subject}")` with context

### State Management
- Service account authentication requires no token storage
- Last check timestamp stored in `{DATA_DIR}/last_check.txt`
- Never commit `service-account.json` or `last_check.txt`

### Environment Variables
**Required**:
- `GEMINI_API_KEY`
- `GOOGLE_SERVICE_ACCOUNT_FILE` (path to service account JSON key)
- `GMAIL_DELEGATED_USER_EMAIL` (email to impersonate via domain-wide delegation)

**Optional**:
- `GOOGLE_MAPS_API_KEY` (enables geocoding)
- `GOOGLE_SHEETS_SPREADSHEET_ID` (enables database saving)
- `GOOGLE_SHEETS_RANGE_NAME` (default: "Sheet1!A:Z")
- `DATA_DIR` (default: "./data")
- `LOG_LEVEL` (default: "INFO")
- `TEST_EMAIL_QUERY` (optional; filters emails with Gmail query syntax)

## Anti-Patterns to Avoid
- ❌ Don't edit files in root `shared/` folder (duplicates are for future services)
- ❌ Don't return data dicts from steps; mutate `ProcessingContext` instead
- ❌ Don't add steps without unique `ProcessingOrder` integer
- ❌ Don't modify `MailClassificationEnum` values (breaks Gemini response parsing)
- ❌ Don't create long-lived clients without `close()` method and finally-block cleanup
- ❌ Don't hard-code file paths; use `DATA_DIR` or service-relative paths

## Key Files Reference
- **Pipeline**: `pipeline/pipeline.py`, `pipeline/processing_context.py`, `pipeline/processing_step.py`
- **Steps**: `pipeline/steps/{classification,logistics_extraction,geocoding,database_save}_step.py`
- **Services**: `services/{classifier,logistics_data_extract,email_prompt_construct}.py`
- **Clients**: `clients/{gmail,gemini,google_maps,google_sheets}_client.py`
- **Models**: `models/{email,logistics}.py`
- **Main**: `main.py` (wires everything together)


### RULES
- never create markdown (`.md`) files after you're done. NEVER!
- only update existing markdown files.