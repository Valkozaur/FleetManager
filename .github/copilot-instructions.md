# FleetManager Copilot Instructions

## Project Overview
FleetManager is a UV workspace-based logistics system that automates email processing for truck fleet management. The system uses shared database models across services with automated migrations.

## Architecture Essentials

### Service Structure
- **UV Workspace Monorepo**: Services under `services/` with shared dependencies via `database-models`
- **Active Services**: 
  - `services/email-processor/` - Email processing and AI extraction
  - `services/database-migration/` - Alembic migration runner
  - `services/database-models/` - Shared SQLAlchemy ORM models
- **Entry Point**: `services/email-processor/main.py` wires all clients and pipeline steps
- **Database**: PostgreSQL with SQLAlchemy ORM

### Pipeline Architecture
The processing flow is a strictly ordered pipeline defined by `ProcessingOrder` enum:

1. **CLASSIFICATION** (1) - Critical step; pipeline aborts if it fails
2. **LOGISTICS_EXTRACTION** (2) - Runs only for Order emails
3. **GEOCODING** (3) - Optional; fills missing coordinates
4. **POSTGRES_SAVE** (4) - Saves to PostgreSQL database
5. **GOOGLE_SHEETS_SAVE** (5) - Optional; writes to Google Sheets (legacy)

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

**PostgresSaveStep** (`steps/postgres_save_step.py`)
- Uses `DatabaseClient` to persist orders to PostgreSQL
- Creates `Order` ORM instances from `LogisticsDataExtract` Pydantic models
- Checks for duplicate `email_id` before inserting
- Handles date parsing and type conversions

**GoogleSheetsSaveStep** (`steps/google_sheets_save_step.py`) - Legacy
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

### Google Sheets API (Optional - Legacy)
- Uses **service account authentication** (same key as Gmail)
- Requires `GOOGLE_SHEETS_SPREADSHEET_ID` + service account key at `GOOGLE_SERVICE_ACCOUNT_FILE`
- Headers: `email_id`, `email_subject`, `email_sender`, `email_date`, + 10 logistics fields
- Graceful degradation: if auth fails or env var missing, step is skipped

### Alembic Migrations
- Located in `services/database-models/migrations/`
- Config in `services/database-migration/alembic.ini`
- Imports models via `from database_models import Base`
- Run via `database-migration` service on deployment
- Creates/updates schema idempotently

### PostgreSQL Database
- Uses **SQLAlchemy 2.0** with declarative ORM models
- Shared `database-models` package imported as `from database_models import Base, Order`
- Connection via `DATABASE_URL` environment variable
- Tables auto-created by Alembic migrations, not `create_all()`
- `DatabaseClient` handles connection pooling and session management

## Developer Workflows

### Local Development
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync workspace dependencies
uv sync

# Run migrations
cd services/database-migration
uv run python main.py

# Run email processor
cd services/email-processor
uv run python main.py
```

### Docker Development
```bash
# From repo root - runs migrations then email-processor
docker-compose up

# Run specific service
docker-compose up email-processor

# Rebuild after changes
docker-compose up --build
```

### Testing
```bash
# Run tests with UV
uv run pytest

# Run tests for specific service
cd services/email-processor
uv run pytest
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
- `DATABASE_URL` (PostgreSQL connection string)

**Optional**:
- `GOOGLE_MAPS_API_KEY` (enables geocoding)
- `GOOGLE_SHEETS_SPREADSHEET_ID` (enables legacy Google Sheets saving)
- `GOOGLE_SHEETS_RANGE_NAME` (default: "Sheet1!A:Z")
- `DATA_DIR` (default: "./data")
- `LOG_LEVEL` (default: "INFO")
- `TEST_EMAIL_QUERY` (optional; filters emails with Gmail query syntax)

## Anti-Patterns to Avoid
- ❌ Don't return data dicts from steps; mutate `ProcessingContext` instead
- ❌ Don't add steps without unique `ProcessingOrder` integer
- ❌ Don't modify `MailClassificationEnum` values (breaks Gemini response parsing)
- ❌ Don't create long-lived clients without `close()` method and finally-block cleanup
- ❌ Don't hard-code file paths; use `DATA_DIR` or service-relative paths

## Key Files Reference
- **Pipeline**: `pipeline/pipeline.py`, `pipeline/processing_context.py`, `pipeline/processing_step.py`
- **Steps**: `pipeline/steps/{classification,logistics_extraction,geocoding,postgres_save,google_sheets_save}_step.py`
- **Services**: `services/{classifier,logistics_data_extract,email_prompt_construct}.py`
- **Clients**: `clients/{gmail,gemini,google_maps,google_sheets,database}_client.py`
- **Models**: `models/{email,logistics}.py`
- **Database Models**: `services/database-models/database_models/orm.py`
- **Migrations**: `services/database-models/migrations/`
- **Main**: `services/email-processor/main.py` (wires everything together)


### RULES
- never create markdown (`.md`) files after you're done. NEVER!
- only update existing markdown files.