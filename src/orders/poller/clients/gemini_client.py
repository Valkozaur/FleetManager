from google import genai
from google.genai import types
import logging

logger = logging.getLogger(__name__)

class GeminiClient:
    """Client to interact with Google Gemini Developer API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

    def generate_text(self, prompt: str, system_instructions: str = "You are a helpful assistant.", model: str = "gemini-2.5-flash", max_tokens: int = 256) -> str:
        """Generate text using Gemini model"""
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config = types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.1,
                    system_instruction=system_instructions
                )
            )

            self.client.close()

            return response.text
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise

    def generate_text_with_files(self, prompt: str, files: list, system_instructions: str = "You are a helpful assistant.", model: str = "gemini-2.5-flash", max_tokens: int = 256) -> str:
        """Generate text using Gemini model with file inputs"""
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.1,
                    system_instruction=system_instructions
                )
            )
            
            self.client.close()

            return response.text
        except Exception as e:
            logger.error(f"Error generating text with files: {e}")
            raise
