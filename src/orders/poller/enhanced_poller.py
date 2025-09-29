#!/usr/bin/env python3
"""
Enhanced Gmail Poller with Gemini Integration for FleetManager
Extends the existing email poller with AI-powered classification and data extraction
"""

import os
import sys
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Add parent directory to path to import existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gmail_client import GmailClient
from ..gemini_integration import (
    GeminiEmailProcessor, GeminiConfig, global_error_tracker,
    ErrorSeverity, ErrorCategory, handle_errors
)

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


class EnhancedGmailPoller:
    """Enhanced Gmail poller with Gemini AI integration"""

    def __init__(self, enable_gemini: bool = True):
        """Initialize the enhanced poller"""
        self.client = None
        self.gemini_processor = None
        self.enable_gemini = enable_gemini
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
            'output_file': os.getenv('OUTPUT_FILE', '/app/data/emails.json'),
            'gemini_output_dir': os.getenv('GEMINI_OUTPUT_DIR', '/app/data/gemini_results'),
            'enable_gemini': os.getenv('ENABLE_GEMINI', 'true').lower() == 'true',
            'gemini_api_key': os.getenv('GEMINI_API_KEY'),
            'gemini_model': os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
            'gemini_temperature': float(os.getenv('GEMINI_TEMPERATURE', '0.1')),
            'min_confidence_threshold': float(os.getenv('MIN_CONFIDENCE_THRESHOLD', '0.5'))
        }

        # Create necessary directories
        os.makedirs(config['data_dir'], exist_ok=True)
        os.makedirs(config['log_dir'], exist_ok=True)
        os.makedirs(config['gemini_output_dir'], exist_ok=True)

        # Validate configuration
        if not os.path.exists(config['credentials_file']):
            logger.error(f"Credentials file not found: {config['credentials_file']}")
            raise FileNotFoundError(f"Credentials file not found: {config['credentials_file']}")

        if config['enable_gemini'] and not config['gemini_api_key']:
            logger.warning("GEMINI_API_KEY not set, disabling Gemini features")
            config['enable_gemini'] = False

        self.enable_gemini = config['enable_gemini']

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
                logging.FileHandler(os.path.join(self.config['log_dir'], 'enhanced_gmail_poller.log'))
            ]
        )

        logger.info(f"Logging level set to {self.config['log_level']}")
        logger.info(f"Log directory: {self.config['log_dir']}")
        logger.info(f"Gemini features enabled: {self.enable_gemini}")

    @handle_errors(
    context="enhanced_poller_initialization",
    severity=ErrorSeverity.CRITICAL,
    category=ErrorCategory.CONFIGURATION_ERROR,
    reraise=True
)
def initialize(self):
        """Initialize the Gmail client and Gemini processor"""
        # Initialize Gmail client
        self.client = GmailClient(
            credentials_file=self.config['credentials_file'],
            data_dir=self.config['data_dir']
        )
        logger.info("Gmail client initialized successfully")

        # Initialize Gemini processor if enabled
        if self.enable_gemini:
            gemini_config = GeminiConfig(
                api_key=self.config['gemini_api_key'],
                model_name=self.config['gemini_model'],
                temperature=self.config['gemini_temperature']
            )
            self.gemini_processor = GeminiEmailProcessor(gemini_config)
            logger.info("Gemini processor initialized successfully")
        else:
            logger.info("Gemini features disabled")

    @handle_errors(
    context="email_polling",
    severity=ErrorSeverity.HIGH,
    category=ErrorCategory.PROCESSING_ERROR,
    reraise=True
)
def poll_emails(self) -> Dict[str, Any]:
        """Poll for new emails with optional Gemini processing"""
        logger.info("Starting enhanced email polling...")

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

        # Process emails with Gemini if enabled
        processing_results = None
        if self.enable_gemini and emails and self.gemini_processor:
            logger.info("Processing emails with Gemini AI...")
            processing_results = self.gemini_processor.process_emails_batch(emails)

            # Filter emails based on confidence threshold
            high_confidence_emails = self._filter_high_confidence_emails(emails, processing_results)
            logger.info(f"High confidence emails: {len(high_confidence_emails)}/{len(emails)}")
        else:
            high_confidence_emails = emails

        # Save results
        if emails:
            self._save_emails(emails, processing_results)

        # Update last check timestamp
        self.client.save_last_check_timestamp()

        return {
            'emails': emails,
            'high_confidence_emails': high_confidence_emails,
            'processing_results': processing_results,
            'total_emails': len(emails),
            'high_confidence_count': len(high_confidence_emails),
            'gemini_enabled': self.enable_gemini
        }

    def _filter_high_confidence_emails(self, emails: List[Dict[str, Any]],
                                    processing_results: List) -> List[Dict[str, Any]]:
        """Filter emails based on confidence threshold"""
        if not processing_results:
            return emails

        high_confidence_emails = []
        threshold = self.config['min_confidence_threshold']

        for i, result in enumerate(processing_results):
            if (result.classification.is_order and
                result.classification.confidence_score >= threshold and
                i < len(emails)):
                high_confidence_emails.append(emails[i])

        return high_confidence_emails

    @handle_errors(
    context="save_emails",
    severity=ErrorSeverity.MEDIUM,
    category=ErrorCategory.FILE_ERROR,
    reraise=False
)
def _save_emails(self, emails: List[Dict[str, Any]],
                    processing_results: Optional[List] = None):
        """Save emails and processing results to output files"""
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config['output_file']), exist_ok=True)

        # Save raw emails
        output_data = {
            'poll_timestamp': datetime.now().isoformat(),
            'gemini_enabled': self.enable_gemini,
            'total_emails': len(emails),
            'emails': emails
        }

        with open(self.config['output_file'], 'w') as f:
            json.dump(output_data, f, indent=2, default=str)

        logger.info(f"Saved {len(emails)} emails to {self.config['output_file']}")

        # Save processing results if available
        if processing_results:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            processing_file = os.path.join(
                self.config['gemini_output_dir'],
                f'processing_results_{timestamp}.json'
            )

            # Convert processing results to serializable format
            serializable_results = []
            for result in processing_results:
                result_dict = {
                    'email_id': result.email_id,
                    'success': result.success,
                    'processing_time_seconds': result.processing_time_seconds,
                    'classification': {
                        'is_order': result.classification.is_order,
                        'confidence_score': result.classification.confidence_score,
                        'order_type': result.classification.order_type.value if result.classification.order_type else None,
                        'reasoning': result.classification.reasoning,
                        'detected_keywords': result.classification.detected_keywords
                    },
                    'processed_attachments': result.processed_attachments,
                    'processing_errors': result.processing_errors
                }

                if result.extracted_data:
                    result_dict['extracted_data'] = {
                        'order_id': result.extracted_data.order_id,
                        'customer_name': result.extracted_data.customer_name,
                        'loading_address': result.extracted_data.loading_location.address,
                        'loading_date': result.extracted_data.loading_time.start_date,
                        'unloading_address': result.extracted_data.unloading_location.address,
                        'unloading_date': result.extracted_data.unloading_time.start_date,
                        'cargo_type': result.extracted_data.cargo_details.cargo_type.value,
                        'weight_kg': result.extracted_data.cargo_details.weight_kg,
                        'extraction_confidence': result.extracted_data.extraction_confidence
                    }

                serializable_results.append(result_dict)

            with open(processing_file, 'w') as f:
                json.dump({
                    'processing_timestamp': timestamp,
                    'total_processed': len(processing_results),
                    'successful': sum(1 for r in processing_results if r.success),
                    'orders_found': sum(1 for r in processing_results if r.classification.is_order),
                    'cargo_data_extracted': sum(1 for r in processing_results if r.extracted_data is not None),
                    'results': serializable_results
                }, f, indent=2, default=str)

            logger.info(f"Saved processing results to {processing_file}")

    @handle_errors(
    context="get_statistics",
    severity=ErrorSeverity.LOW,
    category=ErrorCategory.PROCESSING_ERROR,
    reraise=False
)
def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = {
            'gemini_enabled': self.enable_gemini,
            'configuration': {
                'max_emails': self.config['max_emails'],
                'email_query': self.config['email_query'],
                'min_confidence_threshold': self.config['min_confidence_threshold'],
                'gemini_model': self.config['gemini_model'] if self.enable_gemini else None
            }
        }

        if self.enable_gemini and self.gemini_processor:
            try:
                gemini_stats = self.gemini_processor.get_processing_statistics()
                stats['gemini_statistics'] = gemini_stats
                stats['gemini_performance'] = self.gemini_processor.get_performance_metrics()
            except Exception as e:
                logger.error(f"Failed to get Gemini statistics: {e}")
                stats['gemini_statistics'] = {'error': str(e)}

        # Add global error statistics
        stats['error_statistics'] = global_error_tracker.get_error_summary()

        return stats

    def export_cargo_data(self, output_file: str = None) -> bool:
        """Export extracted cargo data"""
        if not self.enable_gemini or not self.gemini_processor:
            logger.warning("Gemini features not enabled, cannot export cargo data")
            return False

        return self.gemini_processor.export_cargo_data(output_file)

    def run(self) -> bool:
        """Run the enhanced poller (main execution method)"""
        try:
            self._setup_logging()
            self.initialize()
            result = self.poll_emails()

            if result['emails']:
                logger.info(f"Successfully processed {len(result['emails'])} emails")
                if result['gemini_enabled']:
                    orders_found = sum(1 for r in result['processing_results'] or [] if r.classification.is_order)
                    cargo_extracted = sum(1 for r in result['processing_results'] or [] if r.extracted_data)
                    logger.info(f"Found {orders_found} orders, extracted {cargo_extracted} cargo records")
                print(f"Processed {len(result['emails'])} emails")
            else:
                logger.info("No new emails found")
                print("No new emails found")

            return True

        except KeyboardInterrupt:
            logger.info("Enhanced poller interrupted by user")
            return False
        except Exception as e:
            logger.error(f"Enhanced poller failed: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return False

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.gemini_processor:
                self.gemini_processor.cleanup()
        except Exception as e:
            logger.error(f"Failed to cleanup resources: {e}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced Gmail Poller with Gemini AI')
    parser.add_argument('--disable-gemini', action='store_true',
                       help='Disable Gemini AI features')
    parser.add_argument('--stats', action='store_true',
                       help='Show processing statistics')
    parser.add_argument('--export-cargo', metavar='OUTPUT_FILE',
                       help='Export extracted cargo data to file')

    args = parser.parse_args()

    try:
        poller = EnhancedGmailPoller(enable_gemini=not args.disable_gemini)

        if args.stats:
            stats = poller.get_statistics()
            print("Processing Statistics:")
            print(json.dumps(stats, indent=2))
            return

        if args.export_cargo:
            success = poller.export_cargo_data(args.export_cargo)
            if success:
                print(f"Cargo data exported to: {args.export_cargo}")
            else:
                print("Failed to export cargo data")
            return

        success = poller.run()

        # Cleanup
        poller.cleanup()

        # Exit with appropriate code for cron
        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Application failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()