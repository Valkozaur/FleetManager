"""
Integration module for connecting Gemini features with existing email poller
"""

import logging
import time
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from .client import GeminiClient, GeminiConfig
from .classifier import EmailClassifier
from .cargo_extractor import CargoDataExtractor
from .schemas import ProcessingResult, EmailClassification, CargoTruckData

logger = logging.getLogger(__name__)


class GeminiEmailProcessor:
    """Main integration class for Gemini-powered email processing"""

    def __init__(self, config: Optional[GeminiConfig] = None):
        """Initialize the Gemini email processor"""
        try:
            # Initialize Gemini client
            self.client = GeminiClient(config)

            # Check if client is ready
            if not self.client.is_ready():
                raise Exception("Gemini client is not ready")

            # Initialize components
            self.classifier = EmailClassifier(self.client)
            self.extractor = CargoDataExtractor(self.client)

            # Configuration
            self.output_dir = os.getenv('GEMINI_OUTPUT_DIR', '/app/data/gemini_results')
            self.processing_log_file = os.path.join(self.output_dir, 'processing_log.json')

            # Create output directory
            os.makedirs(self.output_dir, exist_ok=True)

            # Performance tracking
            self.total_emails_processed = 0
            self.successful_extractions = 0
            self.total_processing_time = 0

            logger.info("Gemini email processor initialized successfully")
            logger.info(f"Output directory: {self.output_dir}")

        except Exception as e:
            logger.error(f"Failed to initialize Gemini email processor: {e}")
            raise

    def process_email(self, email_data: Dict[str, Any]) -> ProcessingResult:
        """
        Process a single email for classification and cargo data extraction

        Args:
            email_data: Email data dictionary from Gmail API

        Returns:
            ProcessingResult with classification and extracted data
        """
        start_time = time.time()
        processing_errors = []
        email_id = email_data.get('id', 'unknown')

        try:
            logger.info(f"Processing email: {email_id} - {email_data.get('subject', 'No Subject')}")

            # Validate email data
            if not self._validate_email_data(email_data):
                raise ValueError("Invalid email data provided")

            # Step 1: Classify email
            logger.debug("Step 1: Classifying email")
            classification = self.classifier.classify_email(email_data)

            # Step 2: Extract cargo data if it's an order
            extracted_data = None
            processed_attachments = []

            if classification.is_order:
                logger.debug("Step 2: Email classified as order, extracting cargo data")
                try:
                    extracted_data = self.extractor.extract_cargo_data(email_data, classification)

                    if extracted_data:
                        # Track processed attachments
                        if extracted_data.source_files:
                            processed_attachments = extracted_data.source_files.copy()

                        self.successful_extractions += 1
                        logger.info(f"Successfully extracted cargo data from email {email_id}")
                    else:
                        logger.warning(f"Failed to extract cargo data from order email {email_id}")
                        processing_errors.append("Cargo data extraction failed")

                except Exception as e:
                    logger.error(f"Error extracting cargo data: {e}")
                    processing_errors.append(f"Cargo extraction error: {str(e)}")
            else:
                logger.debug(f"Email {email_id} not classified as order, skipping cargo extraction")

            # Step 3: Calculate processing time
            processing_time = time.time() - start_time

            # Update performance metrics
            self.total_emails_processed += 1
            self.total_processing_time += processing_time

            # Step 4: Create processing result
            result = ProcessingResult(
                email_id=email_id,
                classification=classification,
                extracted_data=extracted_data,
                processed_attachments=processed_attachments,
                processing_errors=processing_errors,
                processing_time_seconds=processing_time,
                success=len(processing_errors) == 0
            )

            # Step 5: Log the result
            self._log_processing_result(result)

            logger.info(f"Email processing completed: "
                       f"success={result.success}, "
                       f"is_order={classification.is_order}, "
                       f"confidence={classification.confidence_score:.2f}, "
                       f"time={processing_time:.2f}s")

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Failed to process email {email_id}: {e}")

            # Log detailed error information
            self._log_processing_error(email_id, e, email_data, processing_time)

            return ProcessingResult(
                email_id=email_id,
                classification=EmailClassification(
                    is_order=False,
                    confidence_score=0.0,
                    reasoning=f"Processing failed: {str(e)}",
                    processing_timestamp=datetime.now()
                ),
                extracted_data=None,
                processed_attachments=[],
                processing_errors=[f"Email processing failed: {str(e)}"],
                processing_time_seconds=processing_time,
                success=False
            )

    def process_emails_batch(self, emails: List[Dict[str, Any]]) -> List[ProcessingResult]:
        """
        Process multiple emails in batch

        Args:
            emails: List of email data dictionaries

        Returns:
            List of ProcessingResult objects
        """
        results = []
        total_emails = len(emails)

        logger.info(f"Starting batch processing of {total_emails} emails")

        for i, email in enumerate(emails, 1):
            try:
                logger.debug(f"Processing email {i}/{total_emails}")

                result = self.process_email(email)
                results.append(result)

                # Add small delay to avoid rate limiting
                if i < total_emails:
                    time.sleep(0.5)

            except Exception as e:
                logger.error(f"Failed to process email {i}: {e}")
                error_result = ProcessingResult(
                    email_id=email.get('id', f'unknown_{i}'),
                    classification=EmailClassification(
                        is_order=False,
                        confidence_score=0.0,
                        reasoning=f"Batch processing failed: {str(e)}",
                        processing_timestamp=datetime.now()
                    ),
                    extracted_data=None,
                    processed_attachments=[],
                    processing_errors=[f"Batch processing error: {str(e)}"],
                    processing_time_seconds=0.0,
                    success=False
                )
                results.append(error_result)

        # Save batch results
        self._save_batch_results(results)

        # Calculate summary statistics
        total_processed = len(results)
        successful = sum(1 for r in results if r.success)
        orders_found = sum(1 for r in results if r.classification.is_order)
        cargo_data_extracted = sum(1 for r in results if r.extracted_data is not None)

        logger.info(f"Batch processing completed: "
                   f"{successful}/{total_processed} successful, "
                   f"{orders_found} orders found, "
                   f"{cargo_data_extracted} cargo data extracted")

        return results

    def _log_processing_result(self, result: ProcessingResult):
        """Log individual processing result"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'email_id': result.email_id,
                'success': result.success,
                'is_order': result.classification.is_order,
                'confidence_score': result.classification.confidence_score,
                'processing_time_seconds': result.processing_time_seconds,
                'has_cargo_data': result.extracted_data is not None,
                'processed_attachments_count': len(result.processed_attachments),
                'errors_count': len(result.processing_errors),
                'classification_reasoning': result.classification.reasoning,
                'errors': result.processing_errors
            }

            # Load existing log
            existing_log = []
            if os.path.exists(self.processing_log_file):
                try:
                    with open(self.processing_log_file, 'r') as f:
                        existing_log = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load existing processing log: {e}")

            # Add new entry
            existing_log.append(log_entry)

            # Keep only last 1000 entries
            if len(existing_log) > 1000:
                existing_log = existing_log[-1000:]

            # Save log
            with open(self.processing_log_file, 'w') as f:
                json.dump(existing_log, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to log processing result: {e}")

    def _save_batch_results(self, results: List[ProcessingResult]):
        """Save batch processing results"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            batch_file = os.path.join(self.output_dir, f'batch_results_{timestamp}.json')

            # Convert results to serializable format
            serializable_results = []
            for result in results:
                result_dict = {
                    'email_id': result.email_id,
                    'success': result.success,
                    'processing_time_seconds': result.processing_time_seconds,
                    'processed_attachments': result.processed_attachments,
                    'processing_errors': result.processing_errors,
                    'classification': {
                        'is_order': result.classification.is_order,
                        'confidence_score': result.classification.confidence_score,
                        'order_type': result.classification.order_type.value if result.classification.order_type else None,
                        'reasoning': result.classification.reasoning,
                        'detected_keywords': result.classification.detected_keywords
                    }
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
                        'extraction_confidence': result.extracted_data.extraction_confidence
                    }

                serializable_results.append(result_dict)

            # Save to file
            with open(batch_file, 'w') as f:
                json.dump({
                    'batch_timestamp': timestamp,
                    'total_emails': len(results),
                    'successful': sum(1 for r in results if r.success),
                    'orders_found': sum(1 for r in results if r.classification.is_order),
                    'cargo_data_extracted': sum(1 for r in results if r.extracted_data is not None),
                    'results': serializable_results
                }, f, indent=2, default=str)

            logger.info(f"Batch results saved to: {batch_file}")

        except Exception as e:
            logger.error(f"Failed to save batch results: {e}")

    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics from logs"""
        try:
            if not os.path.exists(self.processing_log_file):
                return {'total_processed': 0, 'statistics': 'No processing log found'}

            with open(self.processing_log_file, 'r') as f:
                logs = json.load(f)

            total_processed = len(logs)
            successful = sum(1 for log in logs if log['success'])
            orders_found = sum(1 for log in logs if log['is_order'])
            avg_confidence = sum(log['confidence_score'] for log in logs) / total_processed if total_processed > 0 else 0
            avg_processing_time = sum(log['processing_time_seconds'] for log in logs) / total_processed if total_processed > 0 else 0

            return {
                'total_processed': total_processed,
                'successful': successful,
                'orders_found': orders_found,
                'success_rate': successful / total_processed if total_processed > 0 else 0,
                'order_rate': orders_found / total_processed if total_processed > 0 else 0,
                'average_confidence': avg_confidence,
                'average_processing_time': avg_processing_time,
                'last_processed': logs[-1]['timestamp'] if logs else None
            }

        except Exception as e:
            logger.error(f"Failed to get processing statistics: {e}")
            return {'error': str(e)}

    def export_cargo_data(self, output_file: str = None) -> bool:
        """Export all extracted cargo data to JSON file"""
        try:
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = os.path.join(self.output_dir, f'cargo_data_export_{timestamp}.json')

            # Load all batch result files
            cargo_data_list = []
            result_files = [f for f in os.listdir(self.output_dir) if f.startswith('batch_results_') and f.endswith('.json')]

            for result_file in result_files:
                try:
                    with open(os.path.join(self.output_dir, result_file), 'r') as f:
                        batch_data = json.load(f)

                    for result in batch_data.get('results', []):
                        if result.get('extracted_data'):
                            cargo_data_list.append(result['extracted_data'])

                except Exception as e:
                    logger.warning(f"Failed to process result file {result_file}: {e}")

            # Export cargo data
            with open(output_file, 'w') as f:
                json.dump({
                    'export_timestamp': datetime.now().isoformat(),
                    'total_records': len(cargo_data_list),
                    'cargo_data': cargo_data_list
                }, f, indent=2, default=str)

            logger.info(f"Exported {len(cargo_data_list)} cargo records to: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export cargo data: {e}")
            return False

    def cleanup(self):
        """Clean up resources"""
        try:
            self.extractor.cleanup()
        except Exception as e:
            logger.error(f"Failed to cleanup resources: {e}")

    def _validate_email_data(self, email_data: Dict[str, Any]) -> bool:
        """Validate email data structure"""
        if not isinstance(email_data, dict):
            return False

        # Check required fields
        required_fields = ['id']
        for field in required_fields:
            if field not in email_data:
                logger.warning(f"Missing required field in email data: {field}")
                return False

        # Check for useful content
        content_fields = ['subject', 'body', 'snippet']
        has_content = any(field in email_data and email_data[field] for field in content_fields)
        if not has_content:
            logger.warning("Email data has no readable content")
            return False

        return True

    def _log_processing_error(self, email_id: str, error: Exception, email_data: Dict[str, Any], processing_time: float):
        """Log detailed error information"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'email_id': email_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'processing_time': processing_time,
            'email_subject': email_data.get('subject', ''),
            'email_from': email_data.get('from', ''),
            'has_attachments': len(email_data.get('attachments', [])) > 0
        }

        logger.error(f"Processing error details: {error_info}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the processor"""
        if self.total_emails_processed == 0:
            return {
                'total_emails_processed': 0,
                'successful_extractions': 0,
                'success_rate': 0,
                'average_processing_time': 0
            }

        return {
            'total_emails_processed': self.total_emails_processed,
            'successful_extractions': self.successful_extractions,
            'success_rate': self.successful_extractions / self.total_emails_processed,
            'average_processing_time': self.total_processing_time / self.total_emails_processed,
            'client_error_stats': self.client.get_error_statistics()
        }