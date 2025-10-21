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

    def get_emails(self, query: str = '', max_results_initial_scan: int = 100) -> List[Email]:
        """
        Fetch new emails since the last check using history API.
        If it's the first run, it performs a full scan.

        Args:
            query: Gmail search query for the initial scan.
            max_results_initial_scan: Maximum number of emails to fetch for the initial scan.
        """
        last_history_id = self.get_last_history_id()

        if last_history_id:
            # Subsequent run: use history.list
            return self._sync_new_emails(last_history_id)
        else:
            # First run: do a full scan
            return self._initial_email_scan(query, max_results=max_results_initial_scan)

    def _initial_email_scan(self, query: str, max_results: int = 100) -> List[Email]:
        """
        Performs an initial scan of all emails, saves the current historyId,
        and returns the emails.
        """
        logger.info("No last history ID found. Performing initial email scan.")
        try:
            # Get the current historyId
            profile = self.service.users().getProfile(userId='me').execute()
            history_id = profile.get('historyId')

            if not history_id:
                logger.error("Could not retrieve start historyId. Aborting initial scan.")
                return []

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
                    logger.error(f"Failed to fetch email {msg['id']} during initial scan: {e}")
                    continue
            
            self.save_last_history_id(history_id)

            logger.info(f"Initial scan fetched {len(emails)} emails. History ID {history_id} saved.")
            return emails

        except HttpError as e:
            logger.error(f"Gmail API error during initial scan: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to perform initial email scan: {e}")
            raise

    def _sync_new_emails(self, start_history_id: str) -> List[Email]:
        """
        Fetches new emails using history.list since the last known historyId.
        """
        logger.info(f"Syncing new emails since history ID: {start_history_id}")
        try:
            history_request = self.service.users().history().list(
                userId='me',
                startHistoryId=start_history_id,
                historyTypes=['messageAdded']
            )
            
            emails = []
            new_history_id = start_history_id
            all_new_message_ids = []

            while history_request is not None:
                history = history_request.execute()
                changes = history.get('history', [])
                
                current_page_message_ids = []
                if changes:
                    for change in changes:
                        if 'messagesAdded' in change:
                            for msg_added in change['messagesAdded']:
                                msg_id = msg_added['message']['id']
                                if msg_id not in all_new_message_ids:
                                    current_page_message_ids.append(msg_id)
                                    all_new_message_ids.append(msg_id)

                for msg_id in current_page_message_ids:
                    try:
                        email_data = self._get_email_details(msg_id)
                        emails.append(email_data)
                    except Exception as e:
                        logger.error(f"Failed to fetch new email {msg_id} from history: {e}")
                        continue
                
                next_page_token = history.get('nextPageToken')
                if next_page_token:
                    history_request = self.service.users().history().list_next(
                        previous_request=history_request,
                        previous_response=history
                    )
                else:
                    history_request = None

                if 'historyId' in history:
                    new_history_id = history['historyId']

            if new_history_id != start_history_id:
                self.save_last_history_id(new_history_id)
                logger.info(f"Synced and fetched {len(emails)} new emails. New history ID {new_history_id} saved.")
            else:
                logger.info("No new emails since last sync.")

            return emails

        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"History ID {start_history_id} not found. It might be too old. "
                               "Performing a full rescan.")
                return self._initial_email_scan(query='')
            else:
                logger.error(f"Gmail API error during history sync: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to sync new emails: {e}")
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

    def get_last_history_id(self) -> Optional[str]:
        """Get the history ID of the last check."""
        history_id_file = os.path.join(self.data_dir, 'last_history_id.txt')

        if os.path.exists(history_id_file):
            try:
                with open(history_id_file, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"Failed to read last history ID: {e}")

        return None

    def save_last_history_id(self, history_id: str):
        """Save the history ID of the last check."""
        history_id_file = os.path.join(self.data_dir, 'last_history_id.txt')

        try:
            with open(history_id_file, 'w') as f:
                f.write(str(history_id))
            logger.info(f"Saved last history ID: {history_id}")
        except Exception as e:
            logger.error(f"Failed to save last history ID: {e}")