"""
Pydantic schemas for data validation and structured output
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class OrderType(str, Enum):
    """Types of cargo orders"""
    FULL_TRUCK_LOAD = "full_truck_load"
    LESS_THAN_TRUCKLOAD = "less_than_truckload"
    PARTIAL_LOAD = "partial_load"
    EXPRESS = "express"
    STANDARD = "standard"


class CargoType(str, Enum):
    """Types of cargo"""
    GENERAL = "general"
    PERISHABLE = "perishable"
    HAZARDOUS = "hazardous"
    FRAGILE = "fragile"
    OVERSIZED = "oversized"
    TEMPERATURE_CONTROLLED = "temperature_controlled"
    LIQUID = "liquid"
    BULK = "bulk"


class EmailClassification(BaseModel):
    """Schema for email classification results"""
    is_order: bool = Field(..., description="Whether the email contains an order")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in classification")
    order_type: Optional[OrderType] = Field(None, description="Type of order if classified as order")
    reasoning: str = Field(..., description="Reasoning for the classification")
    detected_keywords: List[str] = Field(default_factory=list, description="Keywords that triggered order classification")
    processing_timestamp: datetime = Field(default_factory=datetime.now, description="When classification was performed")


class Coordinates(BaseModel):
    """Geographic coordinates"""
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude coordinate")
    address: Optional[str] = Field(None, description="Human-readable address")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in coordinate accuracy")


class Location(BaseModel):
    """Location information for loading/unloading"""
    address: str = Field(..., description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    postal_code: Optional[str] = Field(None, description="Postal/ZIP code")
    country: Optional[str] = Field(None, description="Country")
    coordinates: Optional[Coordinates] = Field(None, description="GPS coordinates")
    facility_name: Optional[str] = Field(None, description="Name of facility/warehouse")
    contact_info: Optional[str] = Field(None, description="Contact information")


class TimeWindow(BaseModel):
    """Time window for operations"""
    start_date: str = Field(..., description="Start date (YYYY-MM-DD format)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD format)")
    start_time: Optional[str] = Field(None, description="Start time (HH:MM format)")
    end_time: Optional[str] = Field(None, description="End time (HH:MM format)")
    timezone: Optional[str] = Field(None, description="Timezone")
    is_flexible: bool = Field(default=False, description="Whether time window is flexible")


class CargoDetails(BaseModel):
    """Detailed cargo information"""
    cargo_type: CargoType = Field(..., description="Type of cargo")
    description: str = Field(..., description="Description of cargo")
    weight_kg: Optional[float] = Field(None, ge=0.0, description="Weight in kilograms")
    volume_cbm: Optional[float] = Field(None, ge=0.0, description="Volume in cubic meters")
    dimensions: Optional[Dict[str, float]] = Field(None, description="Dimensions in meters (length, width, height)")
    special_requirements: List[str] = Field(default_factory=list, description="Special handling requirements")
    is_dangerous: bool = Field(default=False, description="Whether cargo is dangerous/hazardous")
    temperature_requirements: Optional[str] = Field(None, description="Temperature control requirements")


class CargoTruckData(BaseModel):
    """Complete cargo truck order data"""
    order_id: Optional[str] = Field(None, description="Unique order identifier")
    customer_name: Optional[str] = Field(None, description="Customer company name")
    loading_location: Location = Field(..., description="Loading location details")
    loading_time: TimeWindow = Field(..., description="Loading time window")
    unloading_location: Location = Field(..., description="Unloading location details")
    unloading_time: TimeWindow = Field(..., description="Unloading time window")
    cargo_details: CargoDetails = Field(..., description="Cargo information")
    vehicle_requirements: List[str] = Field(default_factory=list, description="Required vehicle specifications")
    special_instructions: List[str] = Field(default_factory=list, description="Special handling instructions")
    contact_person: Optional[str] = Field(None, description="Primary contact person")
    contact_phone: Optional[str] = Field(None, description="Contact phone number")
    contact_email: Optional[str] = Field(None, description="Contact email")
    priority: Optional[str] = Field(None, description="Order priority (low/medium/high)")
    estimated_duration_hours: Optional[float] = Field(None, ge=0.0, description="Estimated trip duration")
    distance_km: Optional[float] = Field(None, ge=0.0, description="Distance in kilometers")
    extraction_timestamp: datetime = Field(default_factory=datetime.now, description="When data was extracted")
    extraction_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in extracted data")
    source_files: List[str] = Field(default_factory=list, description="Source files used for extraction")

    @validator('loading_time', 'unloading_time')
    def validate_time_window(cls, v):
        """Validate time window format"""
        if v.start_date:
            try:
                datetime.strptime(v.start_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("start_date must be in YYYY-MM-DD format")
        if v.end_date:
            try:
                datetime.strptime(v.end_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("end_date must be in YYYY-MM-DD format")
        return v


class ProcessingResult(BaseModel):
    """Result of email processing"""
    email_id: str = Field(..., description="Email identifier")
    classification: EmailClassification = Field(..., description="Email classification result")
    extracted_data: Optional[CargoTruckData] = Field(None, description="Extracted cargo data if applicable")
    processed_attachments: List[str] = Field(default_factory=list, description="List of processed attachment files")
    processing_errors: List[str] = Field(default_factory=list, description="Errors encountered during processing")
    processing_time_seconds: float = Field(..., description="Time taken to process email")
    success: bool = Field(..., description="Whether processing was successful")