from google import genai
from google.genai import types
import logging

logger = logging.getLogger(__name__)


class AddressCleanerService:
    """Service to clean addresses using Gemini for better geocoding accuracy"""
    
    CLEANING_INSTRUCTION = """You are an address cleaning assistant for a logistics geocoding system.

Your task is to extract ONLY the geocodable part of an address suitable for Google Maps API.

RULES:
1. Remove company names, building descriptions, and warehouse details
2. Remove everything after colons (:) or semicolons (;) - these are usually extra descriptions
3. Keep ONLY: country code, postal code, city, street name/number
4. For addresses with company names at the start (like "DLG Fabrik ASA, Saebyvej 3..."), move the street/address before the company name
5. Return ONLY the cleaned address string, nothing else - no explanations, no extra text

EXAMPLES:
Input: "BG 7000 Русе, Индустриалкомплект, АД склад Русе зад ТЕЦ Изток във фуражен завод : Устрем, АД"
Output: "BG 7000 Русе, Индустриалкомплект"

Input: "DLG Fabrik ASA, Saebyvej 3, 9340 Asaa, Denmark"
Output: "Saebyvej 3, 9340 Asaa, Denmark"

Input: "Индустриалкомплект, АД склад Русе зад ТЕЦ Изток във фуражен завод : Устрем, BG 7000 Русе"
Output: "BG 7000 Русе, Индустриалкомплект"

Return only the cleaned address, nothing else."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

    def clean_address(self, address: str) -> str:
        """
        Clean address using Gemini to extract geocodable components
        
        Args:
            address: Raw address string with potential extra information
            
        Returns:
            Cleaned address suitable for geocoding, or original if cleaning fails
        """
        if not address or not address.strip():
            logger.warning("Empty address provided for cleaning")
            return address
        
        try:
            logger.info(f"Cleaning address: {address}")
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite-preview-09-2025",
                contents=address,
                config=types.GenerateContentConfig(
                    temperature=0,
                    system_instruction=self.CLEANING_INSTRUCTION,
                )
            )
            
            cleaned = response.text.strip()
            logger.info(f"Cleaned address: '{address}' -> '{cleaned}'")
            return cleaned
            
        except Exception as e:
            logger.warning(f"Address cleaning failed: {e}, using original address")
            return address

    def close(self):
        """Close the Gemini client"""
        if hasattr(self.client, 'close'):
            self.client.close()

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close()
