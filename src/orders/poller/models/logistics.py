from pydantic import BaseModel

class LogisticsDataExtract(BaseModel):
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