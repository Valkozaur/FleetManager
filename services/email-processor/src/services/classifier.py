from google import genai
from google.genai import types
from shared.models.email import Email, Attachment 
from enum import Enum
from services.email_prompt_construct import construct_prompt_parts
import logging

logger = logging.getLogger(__name__)

class MailClassificationEnum(Enum):
    """Enumeration for mail classification types"""
    ORDER = "Order"
    INVOICE = "Invoice"
    OTHER = "Other"

class MailClassifier:
    """Classifier using Google Gemini Developer API"""
    
    CLASSIFIER_INSTRUCTIONS="""
     You are an email classification assistant used within a truck fleet management system.
     Your task is to classify incoming emails into one of the following categories: Order, Invoice, or Other.
        - Order: The email contains a specific, actionable new order request for transportation services. 
          Do NOT classify as "Order" if the email is a listing, summary, or offer of possible orders or shipments.
        - Invoice: The email contains billing information or an invoice for services rendered.
        - Other: The email does not pertain to orders or invoices, or is a listing/summary/offer of available shipments.

    #Please respond with only one of the following keywords: "Order", "Invoice", or "Other".

    ##BE AWARE:
        - You will be provided with email content including subject, body.
        - You may or may not be provided with attachments depending on the email.
        - You must base your classification on the whole information provided (including attachments if any).
        - If the email is a list, summary, or offer of possible orders/shipments (not a direct request), classify as "Other".
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

    def classify_email(self, email: Email) -> MailClassificationEnum:
        """Clasify email content using Gemini API"""

        parts = construct_prompt_parts(email=email)

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite-preview-09-2025",
                contents=parts,
                config=types.GenerateContentConfig(
                    max_output_tokens=10,
                    temperature=0.1,
                    system_instruction=self.CLASSIFIER_INSTRUCTIONS,
                    response_mime_type="text/x.enum",
                    response_schema=MailClassificationEnum
                )
            )

            return MailClassificationEnum(response.text.strip())
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return MailClassificationEnum.OTHER

