from pydantic import BaseModel
from datetime import datetime

class LogisticsDataExtract(BaseModel):
    # Original logistics fields
    loading_address: str
    unloading_address: str
    loading_date: str
    unloading_date: str
    loading_coordinates: str | None = None
    unloading_coordinates: str | None = None
    cargo_description: str
    weight: str
    vehicle_type: str
    special_requirements: str | None = None
    reference_number: str | None = None

    # Email identifier fields
    email_id: str
    email_subject: str
    email_sender: str
    email_date: datetime