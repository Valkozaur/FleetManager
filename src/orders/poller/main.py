#!/usr/bin/env python3
"""
Gmail Poller for FleetManager
A cron-friendly email polling application that fetches emails from Gmail API
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from src.orders.poller.services.classifier import MailClassifier, MailClassificationEnum
from src.orders.poller.services.logistics_data_extract import LogisticsDataExtractor
from src.orders.poller.clients.gmail_client import GmailClient

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

    try:
        gmail_client = GmailClient(
            credentials_file=os.getenv('GMAIL_CREDENTIALS_FILE', './credentials.json'),
            token_file='token.json',
            data_dir=os.getenv('DATA_DIR', './data')
        )
        classifier = MailClassifier(api_key=os.getenv('GEMINI_API_KEY'))
        extractor = LogisticsDataExtractor(api_key=os.getenv('GEMINI_API_KEY'))

        # Fetch unread emails
        emails = gmail_client.get_emails(query='is:unread')
        logger.info(f"Fetched {len(emails)} unread emails.")

        for email in emails:
            logger.info(f"Processing email with subject: {email.subject}")

            # Classify email
            classification = classifier.classify_email(email)
            logger.info(f"Email classified as: {classification}")

            if classification == MailClassificationEnum.ORDER:
                # Extract logistics data
                logistics_data = extractor.extract_logistics_data(email)
                if logistics_data:
                    logger.info(f"Extracted logistics data: {logistics_data}")
                else:
                    logger.warning("Failed to extract logistics data.")
            else:
                logger.info("Email is not related to order. Skipping extraction.")

        return True

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return False


def main():
    """Main entry point"""
    success = run()
    # Exit with appropriate code for cron
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()