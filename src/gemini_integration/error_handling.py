"""
Error handling utilities for Gemini integration
"""

import logging
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization"""
    API_ERROR = "api_error"
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"
    FILE_ERROR = "file_error"
    NETWORK_ERROR = "network_error"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorTracker:
    """Centralized error tracking and management"""

    def __init__(self, max_errors: int = 1000):
        self.max_errors = max_errors
        self.error_history = []
        self.error_counts = {
            'total': 0,
            'by_category': {},
            'by_severity': {},
            'by_type': {}
        }
        self.logger = logging.getLogger(__name__)

    def track_error(self,
                   error: Exception,
                   context: str = "",
                   severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                   category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR,
                   additional_info: Optional[Dict[str, Any]] = None):
        """Track an error with full context"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'severity': severity.value,
            'category': category.value,
            'traceback': traceback.format_exc(),
            'additional_info': additional_info or {}
        }

        # Add to history
        self.error_history.append(error_entry)

        # Maintain history size limit
        if len(self.error_history) > self.max_errors:
            self.error_history = self.error_history[-self.max_errors:]

        # Update counts
        self.error_counts['total'] += 1
        self.error_counts['by_category'][category.value] = self.error_counts['by_category'].get(category.value, 0) + 1
        self.error_counts['by_severity'][severity.value] = self.error_counts['by_severity'].get(severity.value, 0) + 1
        self.error_counts['by_type'][type(error).__name__] = self.error_counts['by_type'].get(type(error).__name__, 0) + 1

        # Log the error
        self._log_error(error_entry)

    def _log_error(self, error_entry: Dict[str, Any]):
        """Log error based on severity"""
        severity = error_entry['severity']
        message = f"{error_entry['category'].upper()} in {error_entry['context']}: {error_entry['error_message']}"

        if severity == ErrorSeverity.CRITICAL.value:
            self.logger.critical(message)
        elif severity == ErrorSeverity.HIGH.value:
            self.logger.error(message)
        elif severity == ErrorSeverity.MEDIUM.value:
            self.logger.warning(message)
        else:
            self.logger.info(message)

        # Log debug info
        self.logger.debug(f"Error details: {error_entry}")

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked errors"""
        return {
            'total_errors': self.error_counts['total'],
            'by_category': self.error_counts['by_category'],
            'by_severity': self.error_counts['by_severity'],
            'by_type': self.error_counts['by_type'],
            'recent_errors': self.error_history[-10:] if self.error_history else []
        }

    def get_errors_by_category(self, category: ErrorCategory) -> List[Dict[str, Any]]:
        """Get all errors of a specific category"""
        return [error for error in self.error_history if error['category'] == category.value]

    def clear_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.error_counts = {
            'total': 0,
            'by_category': {},
            'by_severity': {},
            'by_type': {}
        }
        self.logger.info("Error history cleared")


class ErrorHandler:
    """Context manager for handling errors with automatic tracking"""

    def __init__(self,
                 tracker: ErrorTracker,
                 context: str,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR,
                 reraise: bool = True,
                 return_on_error: Any = None):
        self.tracker = tracker
        self.context = context
        self.severity = severity
        self.category = category
        self.reraise = reraise
        self.return_on_error = return_on_error
        self.error_occurred = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error_occurred = True
            self.tracker.track_error(
                error=exc_val,
                context=self.context,
                severity=self.severity,
                category=self.category,
                additional_info={
                    'reraise': self.reraise,
                    'return_on_error': self.return_on_error
                }
            )

            if self.reraise:
                return False  # Re-raise the exception
            else:
                return True  # Suppress the exception

    def get_result(self, fallback_result=None):
        """Get result with fallback if error occurred"""
        if self.error_occurred:
            return self.return_on_error or fallback_result
        return None


def categorize_error(error: Exception) -> ErrorCategory:
    """Categorize an error based on its type and message"""
    error_message = str(error).lower()
    error_type = type(error).__name__.lower()

    # API errors
    if any(keyword in error_message for keyword in ['api', 'quota', 'rate limit', 'timeout']):
        return ErrorCategory.API_ERROR

    # Network errors
    if any(keyword in error_message for keyword in ['connection', 'network', 'ssl', 'certificate']):
        return ErrorCategory.NETWORK_ERROR

    # Validation errors
    if any(keyword in error_type for keyword in ['validation', 'value', 'type']) or 'invalid' in error_message:
        return ErrorCategory.VALIDATION_ERROR

    # File errors
    if any(keyword in error_message for keyword in ['file', 'directory', 'permission', 'not found']):
        return ErrorCategory.FILE_ERROR

    # Configuration errors
    if any(keyword in error_message for keyword in ['config', 'setting', 'environment', 'missing']):
        return ErrorCategory.CONFIGURATION_ERROR

    # Processing errors
    if any(keyword in error_type for keyword in ['processing', 'extraction', 'parsing']):
        return ErrorCategory.PROCESSING_ERROR

    return ErrorCategory.UNKNOWN_ERROR


def determine_severity(error: Exception) -> ErrorSeverity:
    """Determine error severity based on type and message"""
    error_message = str(error).lower()
    error_type = type(error).__name__.lower()

    # Critical errors
    if any(keyword in error_message for keyword in ['authentication', 'authorization', 'api key', 'quota exceeded']):
        return ErrorSeverity.CRITICAL

    # High severity errors
    if any(keyword in error_type for keyword in ['connection', 'timeout', 'network']):
        return ErrorSeverity.HIGH

    # Medium severity errors
    if any(keyword in error_type for keyword in ['value', 'type', 'validation']):
        return ErrorSeverity.MEDIUM

    # Low severity errors
    return ErrorSeverity.LOW


# Global error tracker instance
global_error_tracker = ErrorTracker()


def track_error_global(error: Exception, context: str = "", additional_info: Optional[Dict[str, Any]] = None):
    """Track error using global tracker"""
    global_error_tracker.track_error(
        error=error,
        context=context,
        severity=determine_severity(error),
        category=categorize_error(error),
        additional_info=additional_info
    )


def handle_errors(context: str,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR,
                 reraise: bool = True,
                 return_on_error: Any = None):
    """Decorator for automatic error handling"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            with ErrorHandler(global_error_tracker, context, severity, category, reraise, return_on_error):
                return func(*args, **kwargs)
        return wrapper
    return decorator