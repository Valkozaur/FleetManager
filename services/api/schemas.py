from uuid import UUID
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

class RouteStatus(str, Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"

class DriverStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    ON_ROUTE = "ON_ROUTE"
    OFF_DUTY = "OFF_DUTY"

class StopActivityType(str, Enum):
    PICKUP = "PICKUP"
    DROP = "DROP"

class StopStatus(str, Enum):
    PENDING = "PENDING"
    ARRIVED = "ARRIVED"
    COMPLETED = "COMPLETED"

class TruckStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    MAINTENANCE = "MAINTENANCE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"
    INACTIVE = "INACTIVE"

class RouteCreate(BaseModel):
    truck_id: UUID
    scheduled_start_at: datetime

class RoutePlanRequest(BaseModel):
    truck_id: UUID
    date: datetime
    order_ids: List[int]

class RouteResponse(BaseModel):
    id: UUID
    name: str
    truck_id: UUID
    status: RouteStatus
    scheduled_start_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class StopCreate(BaseModel):
    order_id: Optional[int] = None
    activity_type: StopActivityType
    location: Dict[str, Any]

class StopResponse(BaseModel):
    id: UUID
    route_id: UUID
    order_id: Optional[int]
    sequence_number: int
    activity_type: StopActivityType
    status: StopStatus
    location: Dict[str, Any]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class RouteStatusUpdate(BaseModel):
    status: RouteStatus

class StopStatusUpdate(BaseModel):
    status: StopStatus

class TruckCreate(BaseModel):
    plate_number: str = Field(..., min_length=1, max_length=50)
    trailer_plate_number: str = Field(..., min_length=1, max_length=50)
    capacity_weight: float = Field(..., gt=0)
    status: TruckStatus = TruckStatus.AVAILABLE

class TruckUpdate(BaseModel):
    plate_number: Optional[str] = Field(None, min_length=1, max_length=50)
    trailer_plate_number: Optional[str] = Field(None, min_length=1, max_length=50)
    capacity_weight: Optional[float] = Field(None, gt=0)
    status: Optional[TruckStatus] = None

class TruckResponse(BaseModel):
    id: UUID
    plate_number: str
    trailer_plate_number: Optional[str]
    capacity_weight: float
    status: TruckStatus
    is_active: bool
    current_location: Optional[str] = None # Mocked for now
    assigned_driver: Optional[str] = None # Derived

    model_config = ConfigDict(from_attributes=True)

class DriverCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=1, max_length=50)
    status: DriverStatus = DriverStatus.AVAILABLE
    truck_id: Optional[UUID] = None

class DriverUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[DriverStatus] = None
    truck_id: Optional[UUID] = None

class DriverResponse(BaseModel):
    id: UUID
    name: str
    phone: str
    status: DriverStatus
    truck_id: Optional[UUID]
    
    # Derived fields
    assigned_truck_plate: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class OrderResponse(BaseModel):
    id: int
    email_id: str
    customer: Optional[str] = None
    loading_address: str
    unloading_address: str
    loading_date: datetime
    unloading_date: datetime
    status: str
    
    model_config = ConfigDict(from_attributes=True)
