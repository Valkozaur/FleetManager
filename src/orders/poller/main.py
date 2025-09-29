#!/usr/bin/env python3
"""
Gmail Poller for FleetManager
A cron-friendly email polling application that fetches emails from Gmail API
"""

import os
import sys
import logging
import json
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add parent directory to path to import gmail_client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orders.poller.clients.gmail_client import GmailClient
from orders.poller.models.email import Email

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

class GmailPoller:
    """Main poller class for Gmail email fetching"""

    def __init__(self):
        self.client = None
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        config = {
            'credentials_file': os.getenv('GMAIL_CREDENTIALS_FILE', 'credentials.json'),
            'data_dir': os.getenv('DATA_DIR', '/app/data'),
            'log_dir': os.getenv('LOG_DIR', '/app/logs'),
            'max_emails': int(os.getenv('MAX_EMAILS', '10')),
            'email_query': os.getenv('EMAIL_QUERY', ''),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'output_file': os.getenv('OUTPUT_FILE', '/app/data/emails.json')
        }

        # Create necessary directories
        os.makedirs(config['data_dir'], exist_ok=True)
        os.makedirs(config['log_dir'], exist_ok=True)

        # Validate configuration
        if not os.path.exists(config['credentials_file']):
            logger.error(f"Credentials file not found: {config['credentials_file']}")
            raise FileNotFoundError(f"Credentials file not found: {config['credentials_file']}")

        return config

    def _setup_logging(self):
        """Setup logging based on configuration"""
        log_level = getattr(logging, self.config['log_level'].upper())

        # Configure logging with file handler
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(os.path.join(self.config['log_dir'], 'gmail_poller.log'))
            ]
        )

        logger.info(f"Logging level set to {self.config['log_level']}")
        logger.info(f"Log directory: {self.config['log_dir']}")

    def initialize(self):
        """Initialize the Gmail client"""
        try:
            self.client = GmailClient(
                credentials_file=self.config['credentials_file'],
                data_dir=self.config['data_dir']
            )
            logger.info("Gmail client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gmail client: {e}")
            raise

    def poll_emails(self) -> List[Email]:
        """Poll for new emails"""
        try:
            logger.info("Starting email polling...")

            # Get last check timestamp
            last_check = self.client.get_last_check_timestamp()
            if last_check:
                logger.info(f"Checking for emails after: {last_check}")

            # Fetch emails
            emails = self.client.get_emails(
                max_results=self.config['max_emails'],
                query=self.config['email_query'],
                after_timestamp=last_check
            )

            logger.info(f"Found {len(emails)} new emails")

            # Save results
            if emails:
                self._save_emails(emails)

            # Update last check timestamp
            self.client.save_last_check_timestamp()

            return emails

        except Exception as e:
            logger.error(f"Failed to poll emails: {e}")
            raise

    def _save_emails(self, emails: List[Email]):
        """Save emails to output file"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config['output_file']), exist_ok=True)

            # Convert emails to dictionaries for JSON serialization
            # Handle attachments specially since they contain bytes
            email_dicts = []
            for email in emails:
                email_dict = email.model_dump()
                # Convert attachment bytes to base64 for JSON serialization
                email_dict['attachments'] = [
                    {
                        'filename': att.filename,
                        'mime_type': att.mime_type,
                        'size': att.size,
                        'data_b64': att.data.decode('latin-1') if isinstance(att.data, bytes) else att.data
                    }
                    for att in email.attachments
                ]
                email_dicts.append(email_dict)

            # Prepare data for saving
            output_data = {
                'poll_timestamp': datetime.now().isoformat(),
                'total_emails': len(emails),
                'emails': email_dicts
            }

            # Save to file
            with open(self.config['output_file'], 'w') as f:
                json.dump(output_data, f, indent=2, default=str)

            logger.info(f"Saved {len(emails)} emails to {self.config['output_file']}")

        except Exception as e:
            logger.error(f"Failed to save emails: {e}")
            raise

    def run(self) -> bool:
        """Run the poller (main execution method)"""
        try:
            self._setup_logging()
            self.initialize()
            emails = self.poll_emails()

            if emails:
                logger.info(f"Successfully processed {len(emails)} emails")
                print(f"Processed {len(emails)} emails")
            else:
                logger.info("No new emails found")
                print("No new emails found")

            return True

        except KeyboardInterrupt:
            logger.info("Poller interrupted by user")
            return False
        except Exception as e:
            logger.error(f"Poller failed: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return False

def main():
    """Main entry point"""
    poller = GmailPoller()
    success = poller.run()

    # Exit with appropriate code for cron
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()