from google import genai
from google.genai import types
from models.logistics import LogisticsDataExtract
from models.email import Email, Attachment
from services.email_prompt_construct import construct_prompt_parts
import logging

logger = logging.getLogger(__name__)

class LogisticsDataExtractor:
    """Service to extract logistics data using Google Gemini Developer API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

    def close(self):
        """Close the Gemini client"""
        if hasattr(self.client, 'close'):
            self.client.close()

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close()

    def extract_logistics_data(self, email: Email) -> LogisticsDataExtract | None:
        """Extract logistics data from email content using Gemini API"""
        try:
            parts = construct_prompt_parts(email=email)

            response = self.client.models.generate_content(
                model="gemini-2.5-flash-preview-09-2025",
                contents=parts,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    system_instruction=LogisticsDataExtract.__doc__,
                    response_mime_type='application/json',
                    response_schema=LogisticsDataExtract
                )
            )

            logistics_data = LogisticsDataExtract.model_validate_json(response.text)
            logistics_data.email_id = email.id
            logistics_data.email_subject = email.subject
            logistics_data.email_sender = email.sender
            logistics_data.email_date = email.received_at
            return logistics_data
        except Exception as e:
            logger.error(f"Logistics data extraction failed: {e}")
            return None
