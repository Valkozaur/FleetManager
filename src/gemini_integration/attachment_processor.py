"""
Attachment processing module for handling email attachments with Gemini
"""

import os
import logging
import tempfile
import mimetypes
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from .client import GeminiClient

logger = logging.getLogger(__name__)


class AttachmentProcessor:
    """Processes email attachments for cargo truck data extraction"""

    SUPPORTED_MIME_TYPES = {
        'application/pdf': 'PDF document',
        'application/msword': 'Word document',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word document',
        'application/vnd.ms-excel': 'Excel spreadsheet',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'Excel spreadsheet',
        'image/jpeg': 'JPEG image',
        'image/jpg': 'JPEG image',
        'image/png': 'PNG image',
        'image/gif': 'GIF image',
        'text/plain': 'Text file',
        'text/csv': 'CSV file',
        'application/json': 'JSON file'
    }

    def __init__(self, gemini_client: GeminiClient):
        """Initialize attachment processor with Gemini client"""
        self.client = gemini_client
        self.temp_dir = tempfile.mkdtemp(prefix='gemini_attachments_')
        logger.info(f"Attachment processor initialized with temp directory: {self.temp_dir}")

    def process_attachments(self, attachments: List[Dict[str, Any]], email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process email attachments for cargo truck data extraction

        Args:
            attachments: List of attachment dictionaries from email
            email_data: Email context data

        Returns:
            Dictionary with processed attachment information
        """
        results = {
            'processed_files': [],
            'failed_files': [],
            'uploaded_files': [],
            'processing_errors': [],
            'total_attachments': len(attachments),
            'successful_processing': 0
        }

        if not attachments:
            logger.info("No attachments to process")
            return results

        logger.info(f"Processing {len(attachments)} attachments")

        for i, attachment in enumerate(attachments):
            try:
                attachment_id = attachment.get('id', f'attachment_{i}')
                filename = attachment.get('filename', f'unknown_{i}')
                mime_type = attachment.get('mime_type', 'application/octet-stream')

                logger.debug(f"Processing attachment {i+1}/{len(attachments)}: {filename}")

                # Check if mime type is supported
                if mime_type not in self.SUPPORTED_MIME_TYPES:
                    logger.warning(f"Unsupported mime type: {mime_type} for file: {filename}")
                    results['failed_files'].append({
                        'filename': filename,
                        'error': f'Unsupported mime type: {mime_type}'
                    })
                    continue

                # Download and process attachment
                file_path, file_obj = self._download_and_process_attachment(attachment, email_data)

                if file_path and file_obj:
                    results['processed_files'].append({
                        'filename': filename,
                        'file_path': file_path,
                        'mime_type': mime_type,
                        'file_obj': file_obj,
                        'processing_timestamp': datetime.now().isoformat()
                    })
                    results['uploaded_files'].append(file_obj)
                    results['successful_processing'] += 1
                else:
                    results['failed_files'].append({
                        'filename': filename,
                        'error': 'Failed to download or process attachment'
                    })

            except Exception as e:
                logger.error(f"Error processing attachment {i}: {e}")
                results['processing_errors'].append(f"Attachment {i}: {str(e)}")
                results['failed_files'].append({
                    'filename': attachment.get('filename', f'unknown_{i}'),
                    'error': str(e)
                })

        logger.info(f"Attachment processing completed: "
                   f"{results['successful_processing']}/{results['total_attachments']} successful")

        return results

    def _download_and_process_attachment(self, attachment: Dict[str, Any], email_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[Any]]:
        """
        Download attachment and upload to Gemini for processing

        Args:
            attachment: Attachment dictionary
            email_data: Email context data

        Returns:
            Tuple of (local_file_path, gemini_file_object)
        """
        try:
            # Extract attachment data
            filename = attachment.get('filename', 'unknown')
            mime_type = attachment.get('mime_type', 'application/octet-stream')
            attachment_data = attachment.get('data')

            if not attachment_data:
                logger.error(f"No data found for attachment: {filename}")
                return None, None

            # Create temporary file
            temp_file_path = os.path.join(self.temp_dir, filename)

            # Write attachment data to file
            if isinstance(attachment_data, bytes):
                with open(temp_file_path, 'wb') as f:
                    f.write(attachment_data)
            elif isinstance(attachment_data, str):
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    f.write(attachment_data)
            else:
                logger.error(f"Unsupported attachment data type: {type(attachment_data)}")
                return None, None

            logger.debug(f"Attachment saved to: {temp_file_path}")

            # Upload file to Gemini
            if self.client.file_operations_available:
                gemini_file_obj = self.client.upload_file(temp_file_path, mime_type)
                if gemini_file_obj:
                    logger.info(f"Successfully uploaded attachment to Gemini: {filename}")
                    return temp_file_path, gemini_file_obj
                else:
                    logger.error(f"Failed to upload attachment to Gemini: {filename}")
                    return temp_file_path, None
            else:
                logger.warning("File operations not available, keeping local file only")
                return temp_file_path, None

        except Exception as e:
            logger.error(f"Failed to download/process attachment {filename}: {e}")
            return None, None

    def extract_text_from_attachment(self, gemini_file_obj: Any, filename: str = None) -> Optional[str]:
        """
        Extract text content from an uploaded attachment

        Args:
            gemini_file_obj: Gemini file object
            filename: Original filename for context

        Returns:
            Extracted text content or None if failed
        """
        try:
            prompt = f"""
Extract and summarize all text content from the uploaded {filename or 'document'}.

Focus on:
1. Loading/unloading information (dates, times, addresses)
2. Cargo details (type, weight, dimensions)
3. Contact information
4. Any scheduling or logistics information
5. Order numbers or references

Provide a comprehensive text extraction that can be used for further analysis.
"""

            response = self.client.generate_content_with_files(prompt, [gemini_file_obj])

            if response and hasattr(response, 'text'):
                extracted_text = response.text
                logger.debug(f"Extracted {len(extracted_text)} characters from {filename or 'file'}")
                return extracted_text
            else:
                logger.error(f"Failed to extract text from {filename or 'file'}")
                return None

        except Exception as e:
            logger.error(f"Error extracting text from attachment: {e}")
            return None

    def analyze_attachment_content(self, gemini_file_obj: Any, email_context: Dict[str, Any], filename: str = None) -> Dict[str, Any]:
        """
        Analyze attachment content for cargo truck information

        Args:
            gemini_file_obj: Gemini file object
            email_context: Email context for additional information
            filename: Original filename

        Returns:
            Dictionary with analysis results
        """
        try:
            # Extract text first
            extracted_text = self.extract_text_from_attachment(gemini_file_obj, filename)

            if not extracted_text:
                return {
                    'analysis_performed': False,
                    'error': 'Failed to extract text from attachment'
                }

            # Analyze content for cargo truck information
            analysis_prompt = f"""
Analyze the following document content for cargo truck and logistics information.

Document content:
---
{extracted_text}
---

Email context:
- Subject: {email_context.get('subject', '')}
- From: {email_context.get('from', '')}

Extract and identify:
1. Loading information (dates, times, addresses, coordinates)
2. Unloading information (dates, times, addresses, coordinates)
3. Cargo details (type, weight, dimensions, special requirements)
4. Contact information
5. Order references or numbers
6. Vehicle requirements
7. Special instructions or requirements

Provide a structured summary of all logistics-related information found.
"""

            response = self.client.generate_content_with_files(analysis_prompt, [gemini_file_obj])

            if response and hasattr(response, 'text'):
                analysis_result = response.text

                return {
                    'analysis_performed': True,
                    'extracted_text': extracted_text,
                    'analysis_result': analysis_result,
                    'filename': filename,
                    'analysis_timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'analysis_performed': False,
                    'error': 'Failed to analyze attachment content',
                    'extracted_text': extracted_text
                }

        except Exception as e:
            logger.error(f"Error analyzing attachment content: {e}")
            return {
                'analysis_performed': False,
                'error': str(e)
            }

    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Failed to clean up temporary files: {e}")

    def get_supported_formats(self) -> Dict[str, str]:
        """Get list of supported file formats"""
        return self.SUPPORTED_MIME_TYPES.copy()

    def is_supported_format(self, mime_type: str) -> bool:
        """Check if mime type is supported"""
        return mime_type in self.SUPPORTED_MIME_TYPES

    def batch_process_attachments(self, attachment_lists: List[Tuple[List[Dict[str, Any]], Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Process attachments from multiple emails in batch

        Args:
            attachment_lists: List of (attachments, email_data) tuples

        Returns:
            List of processing results
        """
        results = []

        for i, (attachments, email_data) in enumerate(attachment_lists):
            logger.info(f"Processing attachments from email {i+1}/{len(attachment_lists)}")

            result = self.process_attachments(attachments, email_data)
            result['email_index'] = i
            result['email_subject'] = email_data.get('subject', 'Unknown')

            results.append(result)

        total_processed = sum(r['successful_processing'] for r in results)
        total_attachments = sum(r['total_attachments'] for r in results)

        logger.info(f"Batch processing completed: {total_processed}/{total_attachments} attachments processed successfully")

        return results

    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.cleanup_temp_files()
        except:
            pass  # Ignore errors during cleanup