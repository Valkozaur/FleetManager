from pydantic import BaseModel, Field
from datetime import datetime

class LogisticsDataExtract(BaseModel):
    """
    You are a logistics data extraction assistant used within a truck fleet management system.
    Your task is to extract the following logistics information from the provided email content.

    ##BE AWARE:
        - You will be provided with email content including subject, body, and possibly attachments.
        - You must base your extraction on the whole information provided (including attachments if any).
        - Dates must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS) or similar parseable datetime format.
    """
    # Original logistics fields
    loading_address: str = Field(..., description="The full address for loading the cargo.")
    unloading_address: str = Field(..., description="The full address for unloading the cargo.")
    loading_date: datetime = Field(..., description="The date and time for loading the cargo in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).")
    unloading_date: datetime = Field(..., description="The date and time for unloading the cargo in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).")
    loading_coordinates: str | None = Field(default=None, description="The GPS coordinates for the loading location, if available.")
    unloading_coordinates: str | None = Field(default=None, description="The GPS coordinates for the unloading location, if available.")
    cargo_description: str = Field(..., description="A description of the cargo being transported.")
    weight: str = Field(..., description="The weight of the cargo.")
    vehicle_type: str = Field(..., description="The type of vehicle required for the transport.")
    special_requirements: str | None = Field(default=None, description="Any special requirements for the transport.")
    reference_number: str | None = Field(default=None, description='A unique identifier for the specific transport order or shipment. Look for labels like "Reference Number", "Order ID", "Booking Number", or "Референтен №". This number is used to track the specific cargo and is often found near the cargo description.')

    # Email identifier fields (populated by pipeline, not extracted from email content)
    email_id: str | None = None
    email_subject: str | None = None
    email_sender: str | None = None
    email_date: datetime | None = None
    polled_at: datetime | None = None