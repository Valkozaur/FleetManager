#!/usr/bin/env python3
"""
Gmail Poller for FleetManager
A cron-friendly email polling application that fetches emails from Gmail API
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add src directory to Python path for absolute imports
main_root = os.path.dirname(os.path.abspath(__file__))
src_root = os.path.join(main_root, 'src')
sys.path.insert(0, src_root)

from services.classifier import MailClassifier, MailClassificationEnum
from services.logistics_data_extract import LogisticsDataExtractor
from services.address_cleaner import AddressCleanerService
from clients.gmail_client import GmailClient

from clients.google_maps_client import GoogleMapsClient
from clients.google_sheets_client import GoogleSheetsClient
from pipeline.pipeline import ProcessingPipeline, PipelineExecutionError
from pipeline.processing_context import ProcessingContext
from pipeline.steps.classification_step import EmailClassificationStep
from pipeline.steps.logistics_extraction_step import LogisticsExtractionStep
from pipeline.steps.address_cleaning_step import AddressCleaningStep
from pipeline.steps.geocoding_step import GeocodingStep
from pipeline.steps.database_save_step import DatabaseSaveStep

# Load environment variables
load_dotenv()

# Configure basic logging first (will be reconfigured later)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def _create_processing_pipeline(classifier: MailClassifier, extractor: LogisticsDataExtractor, address_cleaner: AddressCleanerService, google_maps_client: GoogleMapsClient | None, sheets_client: GoogleSheetsClient | None) -> ProcessingPipeline:
    """Create and configure the processing pipeline with all steps"""

    # Create processing steps
    steps = [
        EmailClassificationStep(classifier),
        LogisticsExtractionStep(extractor),
        AddressCleaningStep(address_cleaner)
    ]

    # Add geocoding step only if Google Maps client is available
    if google_maps_client:
        steps.append(GeocodingStep(google_maps_client))

    # Add database save step only if Sheets client is available
    if sheets_client:
        steps.append(DatabaseSaveStep(sheets_client))

    return ProcessingPipeline(steps)

def run():
    """Run pipeline"""
    # Reconfigure logging based on environment variables
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logger.setLevel(log_level)

    # Clear existing handlers
    logger.handlers = []

    # Create handlers based on environment variables
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Get data directory
    data_dir = os.getenv('DATA_DIR', './data')

    try:
        # Get service account configuration
        service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
        if not service_account_file:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_FILE environment variable is required")
        
        delegated_user_email = os.getenv('GMAIL_DELEGATED_USER_EMAIL')
        if not delegated_user_email:
            raise ValueError("GMAIL_DELEGATED_USER_EMAIL environment variable is required")
        
        gmail_client = GmailClient(
            service_account_file=service_account_file,
            delegated_user_email=delegated_user_email,
            data_dir=data_dir
        )

        classifier = MailClassifier(api_key=os.getenv('GEMINI_API_KEY'))
        extractor = LogisticsDataExtractor(api_key=os.getenv('GEMINI_API_KEY'))
        address_cleaner = AddressCleanerService(api_key=os.getenv('GEMINI_API_KEY'))

        # Initialize Google Maps client for geocoding
        google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        google_maps_client = GoogleMapsClient(api_key=google_maps_api_key) if google_maps_api_key else None

        # Initialize Google Sheets client for database operations
        sheets_client = None
        if os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID'):
            try:
                sheets_client = GoogleSheetsClient(
                    service_account_file=service_account_file
                )
                if not sheets_client.authenticate():
                    logger.warning("Failed to authenticate with Google Sheets API. Database saving will be disabled.")
                    sheets_client = None
                else:
                    logger.info("Successfully authenticated with Google Sheets API")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Sheets client: {e}")
                sheets_client = None
        else:
            logger.info("GOOGLE_SHEETS_SPREADSHEET_ID not set. Database saving will be disabled.")


        # Create processing pipeline
        pipeline = _create_processing_pipeline(classifier, extractor, address_cleaner, google_maps_client, sheets_client)
        logger.info(f"Created processing pipeline with {len(pipeline.steps)} steps")



        # Optional: Custom query for debugging/testing (used for initial scan)
        custom_query = os.getenv('TEST_EMAIL_QUERY', '').strip()
        if custom_query:
            logger.info(f"Using custom Gmail query filter for initial scan: '{custom_query}'")
        
        # Fetch emails using the new history-based mechanism
        # The GmailClient now handles historyId and deduplication internally.
        emails = gmail_client.get_emails(query=custom_query)
        logger.info(f"Fetched {len(emails)} emails")

        # Process each email through the pipeline
        successful_processing = 0
        failed_processing = 0

        for email in emails:
            try:
                logger.info(f"Processing email with subject: {email.subject}")

                # Create processing context for this email
                context = ProcessingContext(email=email)

                # Execute the pipeline
                processed_context = pipeline.execute(context)

                # Log results
                if processed_context.is_order_email() and processed_context.has_logistics_data():
                    logger.info(f"Successfully processed order email. Logistics data: {processed_context.logistics_data}")
                    successful_processing += 1
                elif processed_context.is_order_email():
                    logger.warning(f"Email classified as order but failed to extract logistics data. Errors: {processed_context.errors}")
                    failed_processing += 1
                else:
                    logger.info(f"Email classified as {processed_context.classification}. Skipping logistics extraction.")

            except PipelineExecutionError as e:
                logger.error(f"Pipeline execution failed for email '{email.subject}': {e}")
                failed_processing += 1
            except Exception as e:
                logger.error(f"Unexpected error processing email '{email.subject}': {e}", exc_info=True)
                failed_processing += 1

        logger.info(f"Email processing completed. Successful: {successful_processing}, Failed: {failed_processing}")
        
        return failed_processing == 0

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return False
    finally:
        # Cleanup clients
        if 'google_maps_client' in locals() and google_maps_client:
            google_maps_client.close()
        if 'sheets_client' in locals() and sheets_client:
            sheets_client.close()
        if 'address_cleaner' in locals() and address_cleaner:
            address_cleaner.close()
        if 'extractor' in locals() and extractor:
            extractor.close()
        if 'classifier' in locals() and classifier:
            classifier.close()


def main():
    """Main entry point"""
    success = run()
    # Exit with appropriate code for cron
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()