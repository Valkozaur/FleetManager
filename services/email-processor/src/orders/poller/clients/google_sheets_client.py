import os
import logging
from typing import List, Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GoogleSheetsClient:
    """Client for interacting with Google Sheets API"""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token_sheets.json'):
        """
        Initialize Google Sheets client

        Args:
            credentials_file: Path to OAuth 2.0 credentials file
            token_file: Path to store/load user token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
        self.range_name = os.getenv('GOOGLE_SHEETS_RANGE_NAME', 'Sheet1!A:Z')

        if not self.spreadsheet_id:
            raise ValueError("GOOGLE_SHEETS_SPREADSHEET_ID environment variable is required")

    def authenticate(self) -> bool:
        """
        Authenticate with Google Sheets API using OAuth 2.0

        Returns:
            bool: True if authentication successful
        """
        try:
            creds = None

            # Load existing token if available
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
                logger.info("Loaded existing Sheets token")

            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    logger.info("Refreshed expired Sheets token")
                else:
                    if not os.path.exists(self.credentials_file):
                        raise FileNotFoundError(f"Credentials file not found: {self.credentials_file}")

                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                    logger.info("Completed OAuth flow for Sheets")

                # Save credentials for next run
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
                logger.info(f"Saved Sheets token to {self.token_file}")

            # Build the service object
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("Successfully authenticated with Google Sheets API")
            return True

        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets API: {e}")
            return False

    def create_headers_if_not_exist(self, headers: List[str]) -> bool:
        """
        Create headers in the spreadsheet if they don't exist

        Args:
            headers: List of column headers

        Returns:
            bool: True if successful
        """
        try:
            # Check if headers already exist by reading first row
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.range_name.split('!')[0]}!1:1"
            ).execute()

            existing_headers = result.get('values', [[]])[0] if result.get('values') else []

            if not existing_headers or existing_headers[0] == '':
                # Create headers
                body = {
                    'values': [headers]
                }
                result = self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{self.range_name.split('!')[0]}!A1",
                    valueInputOption='RAW',
                    body=body
                ).execute()
                logger.info(f"Created headers: {headers}")
            else:
                logger.info(f"Headers already exist: {existing_headers}")

            return True

        except HttpError as e:
            logger.error(f"HTTP error creating headers: {e}")
            return False
        except Exception as e:
            logger.error(f"Error creating headers: {e}")
            return False

    def append_row(self, data: Dict[str, Any], headers: List[str]) -> bool:
        """
        Append a new row to the spreadsheet

        Args:
            data: Dictionary of data to append
            headers: List of column headers in order

        Returns:
            bool: True if successful
        """
        try:
            # Convert data to list in the same order as headers
            row_data = [data.get(header, '') for header in headers]

            body = {
                'values': [row_data]
            }

            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=self.range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()

            logger.info(f"Successfully appended row to spreadsheet. Updated rows: {result.get('updates').get('updatedRows')}")
            return True

        except HttpError as e:
            logger.error(f"HTTP error appending row: {e}")
            return False
        except Exception as e:
            logger.error(f"Error appending row: {e}")
            return False

    def close(self):
        """Clean up resources"""
        if self.service:
            self.service = None
            logger.info("Google Sheets client closed")