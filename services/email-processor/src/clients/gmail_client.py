import os
import logging
import base64
from datetime import datetime
from typing import Optional, Dict, Any, List
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from models.email import Email, Attachment

logger = logging.getLogger(__name__)

class GmailClient:
    """Gmail API client for email operations"""

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, service_account_file: str, delegated_user_email: str, data_dir: str = '/app/data'):
        """
        Initialize Gmail client with service account authentication
        
        Args:
            service_account_file: Path to service account JSON key file
            delegated_user_email: Email address to impersonate (domain-wide delegation)
            data_dir: Directory for storing last check timestamp
        """
        self.service_account_file = service_account_file
        self.delegated_user_email = delegated_user_email
        self.data_dir = data_dir
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using service account"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(self.data_dir, exist_ok=True)

            # Check if service account file exists
            if not os.path.exists(self.service_account_file):
                raise FileNotFoundError(
                    f"Service account file not found: {self.service_account_file}. "
                    "Please download from Google Cloud Console."
                )

            # Load service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=self.SCOPES
            )

            # Create delegated credentials for the specified user
            delegated_credentials = credentials.with_subject(self.delegated_user_email)

            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=delegated_credentials)
            logger.info(f"Successfully authenticated with Gmail API as {self.delegated_user_email}")

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def get_emails(self, max_results: int = 100,
                   query: str = '',
                   after_timestamp: Optional[int] = None) -> List[Email]:
        """Fetch emails from Gmail
        
        Args:
            max_results: Maximum number of emails to fetch (default 100 for 5-min polling)
            query: Gmail search query
            after_timestamp: Unix timestamp (seconds) to fetch emails after.
                           Uses a 2-second buffer to avoid missing emails at same second.
        """
        try:
            # Build query with buffer to handle same-second arrivals
            if after_timestamp:
                # Subtract 2 seconds as buffer to catch emails at same timestamp
                buffer_timestamp = after_timestamp - 2
                query += f' after:{buffer_timestamp}'

            # Get messages
            result = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=query.strip()
            ).execute()

            messages = result.get('messages', [])
            emails = []

            for msg in messages:
                try:
                    email_data = self._get_email_details(msg['id'])
                    emails.append(email_data)
                except Exception as e:
                    logger.error(f"Failed to fetch email {msg['id']}: {e}")
                    continue

            logger.info(f"Successfully fetched {len(emails)} emails")
            return emails

        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            raise

    def _get_email_details(self, msg_id: str) -> Email:
        """Get detailed information about a specific email"""
        try:
            # Get full message with payload
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()

            # Extract headers
            headers = {}
            for header in message['payload']['headers']:
                headers[header['name'].lower()] = header['value']

            # Extract body content
            body = self._extract_body(message['payload'])

            # Extract attachments
            attachments = self._extract_attachments(message)

            # Parse date
            date_str = headers.get('date', '')
            try:
                # Try to parse the date
                date_obj = datetime.strptime(date_str.split(',')[1].strip(),
                                           '%d %b %Y %H:%M:%S %z')
            except:
                date_obj = datetime.now()

            return Email(
                id=message['id'],
                subject=headers.get('subject', 'No Subject'),
                sender=headers.get('from', ''),
                body=body,
                received_at=date_obj,
                attachments=attachments
            )

        except Exception as e:
            logger.error(f"Failed to get email details for {msg_id}: {e}")
            raise

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract the email body from the message payload"""
        try:
            if 'parts' in payload:
                # Multipart message
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    elif part.get('mimeType') == 'text/html' and 'data' in part.get('body', {}):
                        # For HTML, we could convert to text, but for now return as-is
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            else:
                # Single part message
                if 'data' in payload.get('body', {}):
                    return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

            return ""  # No body found

        except Exception as e:
            logger.error(f"Failed to extract body: {e}")
            return ""

    def _extract_attachments(self, message: Dict[str, Any]) -> List[Attachment]:
        """Extract attachments from the message"""
        attachments = []
        try:
            def process_parts(parts):
                for part in parts:
                    if 'filename' in part and part['filename']:
                        # This is an attachment
                        attachment_id = part['body'].get('attachmentId')
                        if attachment_id:
                            try:
                                attachment_data = self._download_attachment(message['id'], attachment_id)
                                if attachment_data:
                                    attachments.append(Attachment(
                                        filename=part['filename'],
                                        mime_type=part.get('mimeType', 'application/octet-stream'),
                                        size=part['body'].get('size', 0),
                                        data=attachment_data
                                    ))
                            except Exception as e:
                                logger.error(f"Failed to download attachment {part['filename']}: {e}")

                    # Recursively process nested parts
                    if 'parts' in part:
                        process_parts(part['parts'])

            if 'parts' in message.get('payload', {}):
                process_parts(message['payload']['parts'])

        except Exception as e:
            logger.error(f"Failed to extract attachments: {e}")

        return attachments

    def _download_attachment(self, message_id: str, attachment_id: str) -> Optional[bytes]:
        """Download attachment data from Gmail"""
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()

            data = attachment.get('data', '')
            if data:
                return base64.urlsafe_b64decode(data)
            return None

        except Exception as e:
            logger.error(f"Failed to download attachment {attachment_id}: {e}")
            return None

    def get_last_check_timestamp(self) -> Optional[int]:
        """Get the Unix timestamp of the last check"""
        timestamp_file = os.path.join(self.data_dir, 'last_check.txt')

        if os.path.exists(timestamp_file):
            try:
                with open(timestamp_file, 'r') as f:
                    return int(f.read().strip())
            except Exception as e:
                logger.error(f"Failed to read last check timestamp: {e}")

        return None

    def save_last_check_timestamp(self, timestamp: int = None):
        """Save the Unix timestamp of the last check
        
        Args:
            timestamp: Unix timestamp (seconds). If None, uses current time.
                      Should be the maximum internalDate from successfully processed emails.
        """
        if timestamp is None:
            # Use current Unix timestamp (seconds since epoch)
            timestamp = int(datetime.now().timestamp())

        timestamp_file = os.path.join(self.data_dir, 'last_check.txt')

        try:
            with open(timestamp_file, 'w') as f:
                f.write(str(timestamp))
            # Convert to readable format for logging
            readable_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"Saved last check timestamp: {timestamp} ({readable_time})")
        except Exception as e:
            logger.error(f"Failed to save last check timestamp: {e}")

