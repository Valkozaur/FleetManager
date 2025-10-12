# FleetManager Copilot Instructions

## Architecture in a hurry
- Monorepo with services under `services/`; only `services/email-processor` is production-ready, `services/ui` and `services/api-gateway` are stubs.
- Email processor entrypoint is `services/email-processor/src/orders/poller/main.py`; it wires Gmail, Gemini, Google Maps, and Google Sheets clients into a step-based pipeline.
- Shared code for this service lives entirely inside the service folder (despite `shared/` duplicates); prefer editing `services/email-processor/src/...` unless told otherwise.

## Email processor flow
- Pipeline definition (`pipeline/pipeline.py`) orders steps via the `ProcessingOrder` enum; new steps must keep integer ordering unique and respect that CLASSIFICATION is the only critical step (pipeline aborts on its failure).
- Each step receives a `ProcessingContext` with `email`, `classification`, `logistics_data`, and shared `custom_data`; set fields on the context instead of returning raw dicts.
- `EmailClassificationStep` wraps `MailClassifier`, which calls Gemini `gemini-2.5-flash-lite-preview-09-2025` with `response_schema=MailClassificationEnum`; the enum values must remain exactly `"Order"|"Invoice"|"Other"`.
- `LogisticsExtractionStep` relies on `LogisticsDataExtractor` to return `LogisticsDataExtract` (Pydantic); this model already includes email metadata fields and is JSON-validated from the Gemini response.
- `GeocodingStep` fills missing coordinates via `GoogleMapsClient.geocode_address`; it only runs when coordinates are blank but addresses exist.
- `DatabaseSaveStep` uses `GoogleSheetsClient` to create headers once and append rows; it mutates the context logistics object to inject email identifiers before saving.

## External integration quirks
- Gmail tokens and timestamps are stored under the service `data/` directory (see `GmailClient`); avoid hard-coding other paths and keep generated `token*.json` files out of commits.
- Sheets access requires `GOOGLE_SHEETS_SPREADSHEET_ID`; without it `DatabaseSaveStep` is skipped. Maps geocoding is optional and only enabled when `GOOGLE_MAPS_API_KEY` is set.
- Prompt construction for Gemini lives in `services/email-processor/src/orders/poller/services/email_prompt_construct.py`; reuse helpers to ensure attachments are passed correctly.
- Both Gemini clients expose `close()` and are cleaned up in `main.run()`. If you add new long-lived clients, mirror that pattern so the finally block can close them.

## Developer workflows
- Local run: `cd services/email-processor && python src/orders/poller/main.py` (dotenv loads `.env` or `.env.local` if present).
- Dockerized run: `docker-compose up email-processor` from repo root mounts `./credentials` and uses service Dockerfile.
- Tests: service-specific tests live in `services/email-processor/tests`; run with `cd services/email-processor && pytest` (root `pyproject.toml` only discovers `tests/` by default).
- Logging level is controlled via `LOG_LEVEL` (.env) and reconfigured at runtime; when debugging, set `TEST_MODE=true` and optionally `TEST_EMAIL_QUERY` to scope Gmail fetches.

## Conventions to keep
- Use ASCII logging messages; existing code sticks to ASCII even when handling international data.
- New pipeline steps should subclass `ProcessingStep`, honor `should_process`, and return `ProcessingResult` objects.
- Keep Google client constructors lightweight and authenticate lazily if a feature can be optional; the main script already skips Sheets/Maps when env vars are missing.
- Avoid touching `shared/` duplicates unless aligning cross-service models—email processor expects its local versions.
