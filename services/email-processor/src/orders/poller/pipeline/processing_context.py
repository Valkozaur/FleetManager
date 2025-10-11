from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..models.email import Email
from ..models.logistics import LogisticsDataExtract
from ..services.classifier import MailClassificationEnum


@dataclass
class ProcessingContext:
    """Context object that passes data between processing steps"""

    # Input data
    email: Email

    # Processing results (filled by steps)
    classification: Optional[MailClassificationEnum] = None
    logistics_data: Optional[LogisticsDataExtract] = None

    # Metadata
    start_time: datetime = field(default_factory=datetime.now)
    completed_steps: list[str] = field(default_factory=list)
    failed_steps: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    # Custom data for steps to share
    custom_data: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, error: str, step_name: Optional[str] = None):
        """Add an error to the context"""
        self.errors.append(error)
        if step_name:
            self.failed_steps.append(step_name)

    def mark_step_completed(self, step_name: str):
        """Mark a step as completed"""
        self.completed_steps.append(step_name)

    def has_logistics_data(self) -> bool:
        """Check if logistics data has been extracted"""
        return self.logistics_data is not None

    def is_order_email(self) -> bool:
        """Check if email is classified as an order"""
        return self.classification == MailClassificationEnum.ORDER

    def set_custom_data(self, key: str, value: Any):
        """Set custom data for sharing between steps"""
        self.custom_data[key] = value

    def get_custom_data(self, key: str, default: Any = None) -> Any:
        """Get custom data shared between steps"""
        return self.custom_data.get(key, default)

    def __str__(self) -> str:
        return f"ProcessingContext(email_subject='{self.email.subject}', classification={self.classification}, has_logistics={self.has_logistics_data()})"