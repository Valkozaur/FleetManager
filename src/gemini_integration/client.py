"""
Gemini API client configuration and management
"""

import os
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from dotenv import load_dotenv

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class GeminiConfig:
    """Configuration for Gemini API client"""
    api_key: str
    model_name: str = "gemini-2.5-flash"
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 30
    temperature: float = 0.1
    max_tokens: int = 8192


class GeminiClient:
    """Enhanced Gemini API client with error handling and retries"""

    def __init__(self, config: Optional[GeminiConfig] = None):
        """Initialize Gemini client with configuration"""
        self.config = config or self._load_config_from_env()
        self._setup_client()
        self._setup_file_handling()

        # Initialize error tracking
        self.error_count = 0
        self.last_error = None
        self.consecutive_errors = 0
        self.request_count = 0
        self.total_request_time = 0

    def _load_config_from_env(self) -> GeminiConfig:
        """Load configuration from environment variables"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        return GeminiConfig(
            api_key=api_key,
            model_name=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
            max_retries=int(os.getenv('GEMINI_MAX_RETRIES', '3')),
            retry_delay=float(os.getenv('GEMINI_RETRY_DELAY', '1.0')),
            timeout=int(os.getenv('GEMINI_TIMEOUT', '30')),
            temperature=float(os.getenv('GEMINI_TEMPERATURE', '0.1')),
            max_tokens=int(os.getenv('GEMINI_MAX_TOKENS', '8192'))
        )

    def _setup_client(self):
        """Setup the Gemini client"""
        try:
            genai.configure(api_key=self.config.api_key)
            self.client = genai.GenerativeModel(
                model_name=self.config.model_name,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_tokens,
                )
            )
            logger.info(f"Initialized Gemini client with model: {self.config.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise

    def _setup_file_handling(self):
        """Setup file handling capabilities"""
        try:
            # Check if file operations are available
            if hasattr(genai, 'upload_file'):
                self.file_operations_available = True
                logger.info("File operations are available")
            else:
                self.file_operations_available = False
                logger.warning("File operations not available in current genai version")
        except Exception as e:
            logger.warning(f"Could not check file operations: {e}")
            self.file_operations_available = False

    def generate_content(self, prompt: str, **kwargs) -> GenerateContentResponse:
        """Generate content with retry logic"""
        import time
        start_time = time.time()
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1} to generate content (prompt length: {len(prompt)})")
                response = self.client.generate_content(prompt, **kwargs)

                if response and hasattr(response, 'text'):
                    duration = time.time() - start_time
                    self._track_request(duration)
                    self._reset_error_tracking()
                    logger.debug(f"Generated content successfully (length: {len(response.text)}, duration: {duration:.2f}s)")
                    return response
                else:
                    logger.warning(f"Empty or invalid response on attempt {attempt + 1}")

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")

                # Check if we should abort on certain errors
                if self._should_abort_on_error(e):
                    logger.error(f"Critical error encountered, aborting: {e}")
                    self._log_error(e, context="generate_content_critical", attempt=attempt+1, prompt_length=len(prompt))
                    raise

                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.debug(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {self.config.max_retries} attempts failed")

        # All attempts failed
        error_msg = f"Failed to generate content after {self.config.max_retries} attempts. Last error: {last_error}"
        self._log_error(last_error or Exception("Unknown error"), context="generate_content_final", prompt_length=len(prompt))
        raise Exception(error_msg)

    def generate_structured_content(self, prompt: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured content using JSON schema"""
        import time
        start_time = time.time()

        try:
            logger.debug(f"Generating structured content (schema size: {len(str(response_schema))})")

            response = self.client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_tokens,
                )
            )

            if response and hasattr(response, 'text'):
                import json
                result = json.loads(response.text)
                duration = time.time() - start_time
                self._track_request(duration)
                self._reset_error_tracking()
                logger.debug(f"Structured content generated successfully (duration: {duration:.2f}s)")
                return result
            else:
                raise Exception("Empty response from structured content generation")

        except Exception as e:
            duration = time.time() - start_time
            self._log_error(e, context="generate_structured_content", prompt_length=len(prompt), duration=duration)
            logger.error(f"Failed to generate structured content: {e}")
            raise

    def upload_file(self, file_path: str, mime_type: str = None) -> Optional[Any]:
        """Upload file to Gemini for processing"""
        if not self.file_operations_available:
            logger.warning("File operations not available")
            return None

        try:
            import pathlib

            file_path_obj = pathlib.Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Determine MIME type if not provided
            if not mime_type:
                import mimetypes
                mime_type, _ = mimetypes.guess_type(str(file_path_obj))
                if not mime_type:
                    mime_type = "application/octet-stream"

            logger.info(f"Uploading file: {file_path} with MIME type: {mime_type}")

            # Upload file
            file_obj = genai.upload_file(file_path_obj, mime_type=mime_type)

            # Wait for file processing
            file_obj = self._wait_for_file_processing(file_obj)

            logger.info(f"File uploaded successfully: {file_obj.name}")
            return file_obj

        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    def _wait_for_file_processing(self, file_obj, max_wait_time: int = 300, check_interval: int = 5) -> Any:
        """Wait for file to finish processing"""
        import time

        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            try:
                file_obj = genai.get_file(file_obj.name)

                if file_obj.state.name == "ACTIVE":
                    logger.info("File processing completed")
                    return file_obj
                elif file_obj.state.name == "FAILED":
                    raise Exception(f"File processing failed: {file_obj.state.name}")
                else:
                    logger.debug(f"File processing state: {file_obj.state.name}")

            except Exception as e:
                logger.warning(f"Error checking file status: {e}")

            time.sleep(check_interval)

        raise Exception(f"File processing timed out after {max_wait_time} seconds")

    def generate_content_with_files(self, prompt: str, files: List[Any]) -> GenerateContentResponse:
        """Generate content with uploaded files"""
        try:
            # Create content parts
            content_parts = [prompt]

            for file_obj in files:
                if hasattr(file_obj, 'uri') and hasattr(file_obj, 'mime_type'):
                    content_parts.append({
                        "mime_type": file_obj.mime_type,
                        "data": file_obj.uri
                    })

            logger.debug(f"Generating content with {len(files)} files")

            response = self.client.generate_content(content_parts)

            if response and hasattr(response, 'text'):
                logger.info(f"Generated content with files successfully (length: {len(response.text)})")
                return response
            else:
                raise Exception("Empty response from file-based content generation")

        except Exception as e:
            logger.error(f"Failed to generate content with files: {e}")
            raise

    def delete_file(self, file_obj):
        """Delete uploaded file to clean up"""
        try:
            if hasattr(file_obj, 'name'):
                genai.delete_file(file_obj.name)
                logger.info(f"Deleted file: {file_obj.name}")
        except Exception as e:
            logger.warning(f"Failed to delete file {getattr(file_obj, 'name', 'unknown')}: {e}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        try:
            return {
                "model_name": self.config.model_name,
                "api_key_configured": bool(self.config.api_key),
                "file_operations_available": self.file_operations_available,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "max_retries": self.config.max_retries
            }
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {}

    def is_ready(self) -> bool:
        """Check if the client is ready to use"""
        try:
            # Test with a simple prompt
            test_response = self.generate_content("Hello")
            return bool(test_response and hasattr(test_response, 'text'))
        except Exception as e:
            logger.error(f"Client not ready: {e}")
            self._log_error(e, context="readiness_check")
            return False

    def _log_error(self, error: Exception, context: str = "", **kwargs):
        """Log error with context information"""
        self.error_count += 1
        self.last_error = error
        self.consecutive_errors += 1

        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "error_count": self.error_count,
            "consecutive_errors": self.consecutive_errors,
            "request_count": self.request_count,
            **kwargs
        }

        logger.error(f"Gemini client error in {context}: {error}")
        logger.debug(f"Error context: {error_context}")

    def _should_abort_on_error(self, error: Exception) -> bool:
        """Determine if we should abort retries based on error type"""
        error_message = str(error).lower()

        # Critical errors that should not be retried
        critical_errors = [
            "api key invalid",
            "quota exceeded",
            "billing not enabled",
            "permission denied",
            "access denied",
            "authentication failed",
            "invalid api key"
        ]

        return any(critical in error_message for critical in critical_errors)

    def _reset_error_tracking(self):
        """Reset consecutive error counter after successful operation"""
        self.consecutive_errors = 0

    def _track_request(self, duration: float):
        """Track request performance metrics"""
        self.request_count += 1
        self.total_request_time += duration
        if self.request_count % 10 == 0:
            avg_time = self.total_request_time / self.request_count
            logger.debug(f"Request performance: {self.request_count} requests, avg time: {avg_time:.2f}s")

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "total_errors": self.error_count,
            "consecutive_errors": self.consecutive_errors,
            "last_error": str(self.last_error) if self.last_error else None,
            "error_rate": self.error_count / max(self.request_count, 1),
            "client_ready": self.is_ready()
        }