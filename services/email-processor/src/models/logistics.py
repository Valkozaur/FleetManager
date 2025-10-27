from pydantic import BaseModel, Field
from datetime import datetime

class LogisticsDataExtract(BaseModel):
    """Extract logistics data from transportation/shipping emails. Dates should be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)."""
    # Original logistics fields
    loading_address: str
    unloading_address: str
    loading_date: datetime = Field(description="Loading date and time in ISO 8601 format")
    unloading_date: datetime = Field(description="Unloading date and time in ISO 8601 format")
    loading_coordinates: str | None = None
    unloading_coordinates: str | None = None
    cargo_description: str
    weight: str
    vehicle_type: str
    special_requirements: str | None = None
    reference_number: str | None = None

    # Email identifier fields
    email_id: str | None = None
    email_subject: str | None = None
    email_sender: str | None = None
    email_date: datetime | None = None
    polled_at: datetime | None = None