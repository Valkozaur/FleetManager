from google import genai
from google.genai import types
from models.logistics import LogisticsDataExtract
from models.email import Email, Attachment
from services.email_prompt_construct import construct_prompt_parts
import logging

logger = logging.getLogger(__name__)

class LogisticsDataExtractor:
    """Service to extract logistics data using Google Gemini Developer API"""
    
    EXTRACTION_INSTRUCTIONS = """
     You are a logistics data extraction assistant used within a truck fleet management system.
     Your task is to extract the following logistics information from the provided email content:
        - Loading Address
        - Unloading Address
        - Loading Date
        - Unloading Date
        - Loading Coordinates (if available)
        - Unloading Coordinates (if available)
        - Cargo Description
        - Weight
        - Vehicle Type
        - Special Requirements (if any)

    ##BE AWARE:
        - You will be provided with email content including subject, body, and possibly attachments.
        - You must base your extraction on the whole information provided (including attachments if any). 
     """

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
                    system_instruction=self.EXTRACTION_INSTRUCTIONS,
                    response_mime_type='application/json',
                    response_schema=LogisticsDataExtract
                )
            )

            return LogisticsDataExtract.model_validate_json(response.text)
        except Exception as e:
            logger.error(f"Logistics data extraction failed: {e}")
            return None
