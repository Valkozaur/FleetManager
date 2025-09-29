"""
Gemini Integration Package for FleetManager
Provides AI-powered email classification and cargo truck data extraction
"""

from .client import GeminiClient, GeminiConfig
from .classifier import EmailClassifier
from .attachment_processor import AttachmentProcessor
from .cargo_extractor import CargoDataExtractor
from .integration import GeminiEmailProcessor
from .schemas import (
    EmailClassification, CargoTruckData, Location, TimeWindow,
    CargoDetails, Coordinates, CargoType, OrderType, ProcessingResult
)
from .error_handling import (
    ErrorTracker, ErrorHandler, ErrorSeverity, ErrorCategory,
    global_error_tracker, track_error_global, handle_errors,
    categorize_error, determine_severity
)

__version__ = "1.0.0"
__all__ = [
    "GeminiClient",
    "GeminiConfig",
    "EmailClassifier",
    "AttachmentProcessor",
    "CargoDataExtractor",
    "GeminiEmailProcessor",
    "EmailClassification",
    "CargoTruckData",
    "Location",
    "TimeWindow",
    "CargoDetails",
    "Coordinates",
    "CargoType",
    "OrderType",
    "ProcessingResult",
    "ErrorTracker",
    "ErrorHandler",
    "ErrorSeverity",
    "ErrorCategory",
    "global_error_tracker",
    "track_error_global",
    "handle_errors",
    "categorize_error",
    "determine_severity"
]