from google import genai
from google.genai import types
import logging

logger = logging.getLogger(__name__)

class MailClassificationEnum:
    """Enumeration for mail classification types"""
    ORDER = "Order"
    INVOICE = "Invoice"
    OTHER = "Other"

class GeminiClassifier:
    """Classifier using Google Gemini Developer API"""
    
    CLASIFIER_INSTRUCTIONS="""
     You are an email classification assistant used within a truck fleet management system.
     Your task is to classify incoming emails into one of the following categories: Order, Invoice, or Other.
        - Order: The email contains a new order request for transportation services.
        - Invoice: The email contains billing information or an invoice for services rendered.
        - Other: The email does not pertain to orders or invoices.

    #BE AWARE:
        - You will be provided with email content including subject, body.
        - You may or may not be provided with attachments depending on the email.
        - You must base your classification on the whole information provided (including attachments if any). 
     """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

    def classify_email(self, email_content: str, attachments: list = None) -> str: