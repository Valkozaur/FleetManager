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

class StopActivityType(str, Enum):
    PICKUP = "PICKUP"
    DROP = "DROP"

class StopStatus(str, Enum):
    PENDING = "PENDING"
    ARRIVED = "ARRIVED"
    COMPLETED = "COMPLETED"

class RouteCreate(BaseModel):
    driver_id: UUID
    truck_id: UUID
    scheduled_start_at: datetime

class RouteResponse(BaseModel):
    id: UUID
    driver_id: UUID
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
