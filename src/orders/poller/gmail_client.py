import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GmailClient:
    """Gmail API client for email operations"""

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, credentials_file: str = 'credentials.json',
                 token_file: str = 'token.json',
                 data_dir: str = '/app/data'):
        self.credentials_file = credentials_file
        self.token_file = os.path.join(data_dir, token_file)
        self.data_dir = data_dir
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth 2.0"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(self.data_dir, exist_ok=True)

            creds = None

            # Load existing token if available
            if os.path.exists(self.token_file):
                try:
                    creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
                    logger.info("Loaded existing credentials")
                except Exception as e:
                    logger.warning(f"Failed to load existing credentials: {e}")

            # If there are no valid credentials, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        logger.info("Refreshing expired credentials")
                        creds.refresh(Request())
                    except Exception as e:
                        logger.warning(f"Failed to refresh credentials: {e}")
                        creds = None

                if not creds:
                    # Check if credentials file exists
                    if not os.path.exists(self.credentials_file):
                        raise FileNotFoundError(
                            f"Credentials file not found: {self.credentials_file}. "
                            "Please download from Google Cloud Console."
                        )

                    # Try headless authentication first
                    creds = self._headless_auth()
                    if not creds:
                        logger.info("Starting OAuth flow")
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_file, self.SCOPES)
                        creds = flow.run_local_server(port=0)

                # Save the credentials for the next run
                try:
                    with open(self.token_file, 'w') as token:
                        token.write(creds.to_json())
                    logger.info("Saved credentials to token file")
                except Exception as e:
                    logger.error(f"Failed to save credentials: {e}")

            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Successfully authenticated with Gmail API")

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def get_emails(self, max_results: int = 10,
                   query: str = '',
                   after_timestamp: Optional[str] = None) -> list:
        """Fetch emails from Gmail"""
        try:
            # Build query
            if after_timestamp:
                query += f' after:{after_timestamp}'

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

    def _get_email_details(self, msg_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific email"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='metadata'
            ).execute()

            # Extract headers
            headers = {}
            for header in message['payload']['headers']:
                headers[header['name'].lower()] = header['value']

            # Get email body (snippet)
            snippet = message.get('snippet', '')

            # Parse date
            date_str = headers.get('date', '')
            try:
                # Try to parse the date
                date_obj = datetime.strptime(date_str.split(',')[1].strip(),
                                           '%d %b %Y %H:%M:%S %z')
            except:
                date_obj = datetime.now()

            return {
                'id': message['id'],
                'thread_id': message['threadId'],
                'subject': headers.get('subject', 'No Subject'),
                'from': headers.get('from', ''),
                'to': headers.get('to', ''),
                'date': date_obj,
                'date_str': date_str,
                'snippet': snippet,
                'label_ids': message.get('labelIds', []),
                'internal_date': int(message.get('internalDate', 0))
            }

        except Exception as e:
            logger.error(f"Failed to get email details for {msg_id}: {e}")
            raise

    def get_last_check_timestamp(self) -> Optional[str]:
        """Get the timestamp of the last check"""
        timestamp_file = os.path.join(self.data_dir, 'last_check.txt')

        if os.path.exists(timestamp_file):
            try:
                with open(timestamp_file, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"Failed to read last check timestamp: {e}")

        return None

    def save_last_check_timestamp(self, timestamp: str = None):
        """Save the timestamp of the last check"""
        if timestamp is None:
            # Use Gmail's internal date format
            timestamp = datetime.now().strftime('%Y/%m/%d')

        timestamp_file = os.path.join(self.data_dir, 'last_check.txt')

        try:
            with open(timestamp_file, 'w') as f:
                f.write(timestamp)
            logger.info(f"Saved last check timestamp: {timestamp}")
        except Exception as e:
            logger.error(f"Failed to save last check timestamp: {e}")

    def _headless_auth(self):
        """Handle headless OAuth authentication for servers without browsers"""
        try:
            # Check for pre-generated authorization code
            auth_code_file = os.path.join(self.data_dir, 'auth_code.txt')
            if os.path.exists(auth_code_file):
                with open(auth_code_file, 'r') as f:
                    auth_code = f.read().strip()

                logger.info("Using pre-generated authorization code")
                return self._exchange_code_for_token(auth_code)

            # Check for imported token file
            imported_token_file = os.path.join(self.data_dir, 'imported_token.json')
            if os.path.exists(imported_token_file):
                with open(imported_token_file, 'r') as f:
                    token_data = json.load(f)

                logger.info("Using imported token")
                return Credentials.from_authorized_user_info(token_data, self.SCOPES)

            logger.info("No pre-generated auth code or imported token found")
            return None

        except Exception as e:
            logger.error(f"Headless authentication failed: {e}")
            return None

    def _exchange_code_for_token(self, auth_code):
        """Exchange authorization code for access token"""
        try:
            # Create flow instance
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # Out-of-band flow
            )

            # Exchange code for token
            flow.fetch_token(code=auth_code)
            return flow.credentials

        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
            return None

    def export_token(self, output_file=None):
        """Export current token for headless deployment"""
        if not output_file:
            output_file = os.path.join(self.data_dir, 'exported_token.json')

        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)

                with open(output_file, 'w') as f:
                    json.dump(token_data, f, indent=2)

                logger.info(f"Token exported to {output_file}")
                return True
            else:
                logger.error("No token file found to export")
                return False

        except Exception as e:
            logger.error(f"Failed to export token: {e}")
            return False

    def generate_auth_url(self):
        """Generate authorization URL for headless authentication"""
        try:
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )

            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )

            return auth_url

        except Exception as e:
            logger.error(f"Failed to generate auth URL: {e}")
            return None