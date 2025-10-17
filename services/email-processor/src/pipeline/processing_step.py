from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ProcessingOrder(IntEnum):
    """Define the order of processing steps"""
    CLASSIFICATION = 1
    LOGISTICS_EXTRACTION = 2
    ADDRESS_CLEANING = 3
    GEOCODING = 4
    DATABASE_SAVE = 5


class ProcessingResult:
    """Result of a processing step"""
    def __init__(self, success: bool, data: Optional[dict] = None, error: Optional[str] = None):
        self.success = success
        self.data = data or {}
        self.error = error

    def __bool__(self) -> bool:
        return self.success


class ProcessingStep(ABC):
    """Abstract base class for all processing steps in the pipeline"""

    def __init__(self, order: ProcessingOrder):
        self.order = order
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def process(self, context: 'ProcessingContext') -> ProcessingResult:
        """
        Process the given context and return a result

        Args:
            context: The processing context containing email and any previously extracted data

        Returns:
            ProcessingResult with success status and any extracted data
        """
        pass

    def should_process(self, context: 'ProcessingContext') -> bool:
        """
        Determine if this step should be executed for the given context

        Args:
            context: The processing context

        Returns:
            True if this step should be executed, False otherwise
        """
        return True

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(order={self.order})"

    def __repr__(self) -> str:
        return self.__str__()